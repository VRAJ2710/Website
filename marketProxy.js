"use strict";

class BoundedTtlCache {
  constructor({ maxEntries, maxBytes }) {
    this.maxEntries = maxEntries;
    this.maxBytes = maxBytes;
    this.entries = new Map();
    this.bytes = 0;
  }

  delete(key) {
    const entry = this.entries.get(key);
    if (!entry) return false;
    this.entries.delete(key);
    this.bytes -= entry.bytes;
    return true;
  }

  prune(now = Date.now()) {
    for (const [key, entry] of this.entries) {
      const staleUntil = entry.staleUntil ?? entry.expiresAt;
      if (staleUntil <= now) this.delete(key);
    }
  }

  get(key, now = Date.now()) {
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    if (entry.expiresAt <= now) {
      this.delete(key);
      return undefined;
    }
    // Refresh insertion order so the oldest entry is always the LRU candidate.
    this.entries.delete(key);
    this.entries.set(key, entry);
    return entry.value;
  }

  peek(key, now = Date.now()) {
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    const staleUntil = entry.staleUntil ?? entry.expiresAt;
    if (staleUntil <= now) {
      this.delete(key);
      return undefined;
    }
    return { value: entry.value, fresh: entry.expiresAt > now };
  }

  set(key, value, ttlMs, now = Date.now(), options = {}) {
    const bytes = Buffer.byteLength(JSON.stringify(value), "utf8");
    if (bytes > this.maxBytes) return false;
    this.prune(now);
    this.delete(key);
    while (this.entries.size >= this.maxEntries || this.bytes + bytes > this.maxBytes) {
      const oldestKey = this.entries.keys().next().value;
      if (oldestKey === undefined) break;
      this.delete(oldestKey);
    }
    const staleMs = Number(options?.staleMs) || 0;
    this.entries.set(key, {
      value,
      bytes,
      expiresAt: now + ttlMs,
      staleUntil: now + ttlMs + Math.max(0, staleMs),
    });
    this.bytes += bytes;
    return true;
  }
}

class FixedWindowRateLimiter {
  constructor({ limit, windowMs, maxKeys }) {
    this.limit = limit;
    this.windowMs = windowMs;
    this.maxKeys = maxKeys;
    this.windows = new Map();
  }

  allow(key, now = Date.now()) {
    for (const [candidate, window] of this.windows) {
      if (window.startedAt + this.windowMs <= now) this.windows.delete(candidate);
    }
    let window = this.windows.get(key);
    if (!window) {
      if (this.windows.size >= this.maxKeys) this.windows.delete(this.windows.keys().next().value);
      window = { startedAt: now, count: 0 };
      this.windows.set(key, window);
    }
    if (window.count >= this.limit) return false;
    window.count += 1;
    return true;
  }
}

class FixedWindowCreditLimiter {
  constructor({ limit, windowMs, maxKeys }) {
    this.limit = limit;
    this.windowMs = windowMs;
    this.maxKeys = maxKeys;
    this.windows = new Map();
  }

  allow(key, cost, now = Date.now()) {
    if (!Number.isInteger(cost) || cost <= 0 || cost > this.limit) return false;
    for (const [candidate, window] of this.windows) {
      if (window.startedAt + this.windowMs <= now) this.windows.delete(candidate);
    }
    let window = this.windows.get(key);
    if (!window) {
      if (this.windows.size >= this.maxKeys) this.windows.delete(this.windows.keys().next().value);
      window = { startedAt: now, credits: 0 };
      this.windows.set(key, window);
    }
    if (window.credits + cost > this.limit) return false;
    window.credits += cost;
    return true;
  }
}

function hasOnly(params, allowed) {
  for (const key of params.keys()) {
    if (!allowed.has(key) || params.getAll(key).length !== 1) return false;
  }
  return true;
}

function composeCoinGeckoPath(rawPath, searchParams) {
  if (typeof rawPath !== "string") return null;
  let path = rawPath.trim();
  if (path.startsWith("/api/v3/")) path = path.slice("/api/v3".length);
  else if (path === "/api/v3") path = "/";
  if (path && !path.startsWith("/")) path = `/${path}`;

  const extra = new URLSearchParams();
  if (searchParams && typeof searchParams.entries === "function") {
    for (const [key, value] of searchParams.entries()) {
      if (key === "path") continue;
      extra.append(key, value);
    }
  }
  const extraQuery = extra.toString();
  if (extraQuery) path += (path.includes("?") ? "&" : "?") + extraQuery;
  return normalizeCoinGeckoPath(path);
}

function normalizeCoinGeckoPath(rawPath) {
  if (typeof rawPath !== "string" || !rawPath.startsWith("/") || rawPath.length > 600) return null;
  let input;
  try {
    input = new URL(rawPath, "https://api.coingecko.com");
  } catch {
    return null;
  }

  const { pathname, searchParams } = input;
  if (pathname === "/simple/price") {
    if (!hasOnly(searchParams, new Set(["ids", "vs_currencies", "include_24hr_change"]))) return null;
    const ids = searchParams.get("ids");
    if (!ids || !/^[a-z0-9-]+(?:,[a-z0-9-]+){0,29}$/.test(ids)) return null;
    if (searchParams.get("vs_currencies") !== "usd" || searchParams.get("include_24hr_change") !== "true") return null;
    return `/simple/price?ids=${encodeURIComponent(ids)}&vs_currencies=usd&include_24hr_change=true`;
  }

  const chart = pathname.match(/^\/coins\/([a-z0-9-]{1,80})\/market_chart$/);
  if (chart) {
    if (!hasOnly(searchParams, new Set(["vs_currency", "days"]))) return null;
    const days = searchParams.get("days");
    if (searchParams.get("vs_currency") !== "usd" || !/^(?:[1-9]|[1-9]\d|[12]\d\d|3[0-6][0-5])$/.test(days || "")) return null;
    return `/coins/${chart[1]}/market_chart?vs_currency=usd&days=${days}`;
  }

  if (pathname === "/coins/markets") {
    if (!hasOnly(searchParams, new Set(["vs_currency", "order", "per_page", "page", "sparkline", "price_change_percentage"]))) return null;
    if (
      searchParams.get("vs_currency") !== "usd" ||
      searchParams.get("order") !== "market_cap_desc" ||
      searchParams.get("per_page") !== "50" ||
      searchParams.get("page") !== "1" ||
      searchParams.get("sparkline") !== "false" ||
      searchParams.get("price_change_percentage") !== "1h,24h,7d"
    ) return null;
    return "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=1h%2C24h%2C7d";
  }

  return pathname === "/global" && !searchParams.toString() ? "/global" : null;
}

const USGS_SOURCE = "USGS Earthquake Hazards Program";
const GEO_CACHE_CONTROL = "public, max-age=60";
const SECURITY_HEADERS = Object.freeze({
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Frame-Options": "DENY",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
});
const LONG_CACHE_EXTENSIONS = new Set([".js", ".css", ".svg", ".woff", ".woff2"]);

function normalizeGeoQuery(searchParams) {
  const read = key => {
    if (!searchParams) return null;
    if (typeof searchParams.get === "function") return searchParams.get(key);
    return searchParams[key];
  };
  const mag = Number(read("minmag"));
  const days = Number(read("days"));
  const minmag = Number.isFinite(mag) ? Math.min(8, Math.max(0, mag)) : 4.5;
  const windowDays = Number.isFinite(days) ? Math.min(30, Math.max(1, Math.round(days))) : 7;
  const magBucket = minmag >= 4.5 ? "4.5" : minmag >= 2.5 ? "2.5" : minmag >= 1 ? "1.0" : "all";
  const period = windowDays <= 1 ? "day" : windowDays <= 7 ? "week" : "month";
  return {
    minmag,
    days: windowDays,
    cacheKey: `geo:${magBucket}:${period}:${minmag}:${windowDays}`,
    feedUrl: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/${magBucket}_${period}.geojson`,
  };
}

function normalizeUsgsEarthquakes(payload, { minmag = 4.5, days = 7 } = {}, now = Date.now()) {
  const cutoff = now - days * 24 * 60 * 60 * 1000;
  const features = Array.isArray(payload?.features) ? payload.features : [];
  const events = [];
  for (const feature of features) {
    const props = feature?.properties || {};
    const mag = Number(props.mag);
    const time = Number(props.time);
    if (!Number.isFinite(mag) || mag < minmag) continue;
    if (!Number.isFinite(time) || time < cutoff) continue;
    const coords = Array.isArray(feature?.geometry?.coordinates) ? feature.geometry.coordinates : [];
    events.push({
      id: typeof feature.id === "string" ? feature.id : null,
      mag,
      place: typeof props.place === "string" ? props.place : "",
      time: new Date(time).toISOString(),
      url: typeof props.url === "string" ? props.url : null,
      coordinates: {
        longitude: Number(coords[0]),
        latitude: Number(coords[1]),
        depthKm: Number(coords[2]),
      },
    });
  }
  events.sort((a, b) => Date.parse(b.time) - Date.parse(a.time));
  return {
    events,
    source: USGS_SOURCE,
    asOf: new Date(now).toISOString(),
    status: "available",
  };
}

function staticCacheControl(pathname, searchParams) {
  const ext = pathExtension(pathname);
  const versioned = Boolean(
    searchParams && (typeof searchParams.get === "function" ? searchParams.get("v") : searchParams.v),
  );
  if (ext === ".html" || pathname === "/" || pathname === "/index.html") return "no-store";
  if (versioned && LONG_CACHE_EXTENSIONS.has(ext)) return "public, max-age=31536000, immutable";
  if (ext === ".js" || ext === ".css") return "public, max-age=300";
  return "no-store";
}

function pathExtension(pathname) {
  const base = String(pathname || "").split("?")[0];
  const slash = base.lastIndexOf("/");
  const name = slash >= 0 ? base.slice(slash + 1) : base;
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot).toLowerCase() : "";
}

function attachSecurityHeaders(res) {
  const original = res.writeHead;
  if (typeof original !== "function" || res.__dispatchSecurityHeaders) return res;
  res.__dispatchSecurityHeaders = true;
  res.writeHead = function writeHeadWithSecurity(statusCode, ...rest) {
    let reason;
    let headers = {};
    if (typeof rest[0] === "string") {
      reason = rest[0];
      headers = rest[1] || {};
    } else if (rest[0] && typeof rest[0] === "object") {
      headers = rest[0];
    }
    const merged = { ...SECURITY_HEADERS, ...headers };
    return reason === undefined
      ? original.call(this, statusCode, merged)
      : original.call(this, statusCode, reason, merged);
  };
  return res;
}

// One shared Basic-plan tape. Twelve Data bills one credit per symbol, with
// 8 credits/minute and 800/day. Eight symbols × a 15-minute shared cache
// stays at 768 credits/day. Adding MSFT/TSLA/AMZN/GBPUSD/USDJPY on top of
// gold/crypto/ETFs would exceed the per-minute ceiling in a single request.
const TWELVE_DATA_ALLOWED_SYMBOLS = Object.freeze([
  "AAPL", "NVDA",
  "SPY", "QQQ",
  "XAU/USD", "EUR/USD",
  "BTC/USD", "ETH/USD",
]);
const TWELVE_DATA_MAX_SYMBOLS = TWELVE_DATA_ALLOWED_SYMBOLS.length;
const TWELVE_DATA_DAILY_CREDIT_LIMIT = 800;
const TWELVE_DATA_MARKET_CLOSED_STATUSES = new Set(["closed", "market_closed", "not_open"]);
const TWELVE_DATA_PROVIDER = Object.freeze({
  id: "twelve-data",
  name: "Twelve Data",
  url: "https://twelvedata.com/",
});
const DXY_CONSTANT = 50.14348112;
const DXY_WEIGHTS = Object.freeze({
  EUR: -0.576,
  JPY: 0.136,
  GBP: -0.119,
  CAD: 0.091,
  SEK: 0.042,
  CHF: 0.036,
});

function canonicalTwelveDataSymbols() {
  return [...TWELVE_DATA_ALLOWED_SYMBOLS];
}

function normalizeTwelveDataSymbols(symbols, allowedSymbols = TWELVE_DATA_ALLOWED_SYMBOLS) {
  if (!Array.isArray(symbols)) return [];
  const requested = new Set(symbols.map(symbol => String(symbol || "").trim()));
  return allowedSymbols.slice(0, TWELVE_DATA_MAX_SYMBOLS).filter(symbol => requested.has(symbol));
}

function twelveDataPayloadRows(payload) {
  return payload && typeof payload === "object" && typeof payload.symbol === "string"
    ? { [payload.symbol]: payload }
    : payload;
}

function twelveDataMarketClosed(row) {
  if (!row || typeof row !== "object") return false;
  const marketOpen = row.is_market_open ?? row.market_open;
  if (marketOpen === false || String(marketOpen || "").trim().toLowerCase() === "false") return true;
  return TWELVE_DATA_MARKET_CLOSED_STATUSES.has(
    String(row.status ?? row.market_status ?? "").trim().toLowerCase(),
  );
}

function normalizeTwelveDataQuotes(payload, allowedSymbols = TWELVE_DATA_ALLOWED_SYMBOLS, now = Date.now()) {
  const rows = twelveDataPayloadRows(payload);
  if (!rows || typeof rows !== "object" || Array.isArray(rows)) return {};

  const allowed = new Set(allowedSymbols.slice(0, TWELVE_DATA_MAX_SYMBOLS));
  const quotes = {};
  for (const [symbol, row] of Object.entries(rows)) {
    if (!allowed.has(symbol) || !row || typeof row !== "object") continue;
    const price = Number(row.close);
    if (!Number.isFinite(price) || price <= 0) continue;
    const previousClose = Number(row.previous_close);
    const changePercent = Number(row.percent_change);
    const change = Number(row.change);
    const timestamp = Number(row.last_quote_at || row.timestamp);
    if (!Number.isFinite(timestamp) || timestamp <= 0 || timestamp * 1000 > now + 60_000) continue;
    const marketClosed = twelveDataMarketClosed(row);
    quotes[symbol] = {
      p: price,
      c: Number.isFinite(changePercent) ? changePercent : 0,
      prev: Number.isFinite(previousClose) && previousClose > 0 ? previousClose : price,
      change: Number.isFinite(change) ? change : 0,
      currency: typeof row.currency === "string" ? row.currency : null,
      exchange: typeof row.exchange === "string" ? row.exchange : null,
      name: typeof row.name === "string" ? row.name : symbol,
      ts: timestamp,
      ...(marketClosed ? { marketClosed: true } : {}),
    };
  }
  return quotes;
}

function twelveDataQuoteCoverage(payload, allowedSymbols = TWELVE_DATA_ALLOWED_SYMBOLS, now = Date.now()) {
  const requestedSymbols = normalizeTwelveDataSymbols(allowedSymbols, allowedSymbols);
  const quotes = normalizeTwelveDataQuotes(payload, allowedSymbols, now);
  const returnedSymbols = requestedSymbols.filter(symbol => quotes[symbol]);
  const missingSymbols = requestedSymbols.filter(symbol => !quotes[symbol]);
  const rows = twelveDataPayloadRows(payload);
  const marketClosedSymbols = missingSymbols.filter(symbol => twelveDataMarketClosed(rows?.[symbol]));
  const alertableMissingSymbols = missingSymbols.filter(symbol => !marketClosedSymbols.includes(symbol));
  return {
    requestedSymbols,
    returnedSymbols,
    missingSymbols,
    marketClosedSymbols,
    alertableMissingSymbols,
  };
}

function normalizeGoldApiQuote(payload, now = Date.now()) {
  const price = Number(payload?.price);
  if (!Number.isFinite(price) || price <= 0) return null;
  const updated = Date.parse(payload?.updatedAt || "");
  const ts = Number.isFinite(updated) ? Math.floor(updated / 1000) : Math.floor(now / 1000);
  return {
    p: price,
    c: 0,
    prev: price,
    change: 0,
    currency: typeof payload.currency === "string" ? payload.currency : "USD",
    exchange: "FREE REFERENCE",
    name: "Spot Gold (proxy)",
    ts,
    source: "gold-api-spot-proxy",
    proxy: true,
  };
}

function synthesizeDxyFromUsdRates(rates, date, now = Date.now()) {
  if (!rates || typeof rates !== "object") return null;
  const usdPerForeign = {
    EUR: 1 / Number(rates.EUR),
    GBP: 1 / Number(rates.GBP),
    JPY: Number(rates.JPY),
    CAD: Number(rates.CAD),
    SEK: Number(rates.SEK),
    CHF: Number(rates.CHF),
  };
  if (Object.values(usdPerForeign).some(value => !Number.isFinite(value) || value <= 0)) return null;

  const price = DXY_CONSTANT
    * (usdPerForeign.EUR ** DXY_WEIGHTS.EUR)
    * (usdPerForeign.JPY ** DXY_WEIGHTS.JPY)
    * (usdPerForeign.GBP ** DXY_WEIGHTS.GBP)
    * (usdPerForeign.CAD ** DXY_WEIGHTS.CAD)
    * (usdPerForeign.SEK ** DXY_WEIGHTS.SEK)
    * (usdPerForeign.CHF ** DXY_WEIGHTS.CHF);
  if (!Number.isFinite(price) || price <= 0) return null;

  const parsedDate = date ? Date.parse(`${date}T00:00:00Z`) : NaN;
  const ts = Number.isFinite(parsedDate) ? Math.floor(parsedDate / 1000) : Math.floor(now / 1000);
  return {
    p: price,
    c: 0,
    prev: price,
    change: 0,
    currency: "USD",
    exchange: "SYNTHETIC",
    name: "Synthetic Dollar Index (proxy)",
    ts,
    source: "frankfurter-ecb",
    proxy: true,
  };
}

function canReplaceLiveQuote({ ticker, currentSrc, currentTs, incomingSrc, now = Date.now(), windowMs = 16 * 60 * 1000 }) {
  const current = String(currentSrc || "");
  const incoming = String(incomingSrc || "");
  const freshTwelveData = current === "twelve-data" && now - (currentTs || 0) <= windowMs;
  if (freshTwelveData && incoming !== "twelve-data") return false;
  if (ticker === "XAU" && incoming === "yahoo" && current.startsWith("gold-api")) {
    return false;
  }
  if (ticker === "DXY" && incoming === "frankfurter-ecb" && current === "yahoo") return false;
  return true;
}

function providerTimestampMs(value, now = Date.now()) {
  const raw = Number(value);
  if (!Number.isFinite(raw) || raw <= 0) return null;
  const ms = raw < 10_000_000_000 ? raw * 1000 : raw;
  if (ms > now + 60_000) return null;
  return ms;
}

module.exports = {
  BoundedTtlCache,
  FixedWindowRateLimiter,
  FixedWindowCreditLimiter,
  composeCoinGeckoPath,
  normalizeCoinGeckoPath,
  normalizeGeoQuery,
  normalizeUsgsEarthquakes,
  staticCacheControl,
  attachSecurityHeaders,
  SECURITY_HEADERS,
  GEO_CACHE_CONTROL,
  USGS_SOURCE,
  TWELVE_DATA_ALLOWED_SYMBOLS,
  TWELVE_DATA_MAX_SYMBOLS,
  TWELVE_DATA_DAILY_CREDIT_LIMIT,
  TWELVE_DATA_PROVIDER,
  canonicalTwelveDataSymbols,
  normalizeTwelveDataSymbols,
  normalizeTwelveDataQuotes,
  twelveDataQuoteCoverage,
  normalizeGoldApiQuote,
  synthesizeDxyFromUsdRates,
  canReplaceLiveQuote,
  providerTimestampMs,
};
