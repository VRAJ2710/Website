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
      if (entry.expiresAt <= now) this.delete(key);
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

  set(key, value, ttlMs, now = Date.now()) {
    const bytes = Buffer.byteLength(JSON.stringify(value), "utf8");
    if (bytes > this.maxBytes) return false;
    this.prune(now);
    this.delete(key);
    while (this.entries.size >= this.maxEntries || this.bytes + bytes > this.maxBytes) {
      const oldestKey = this.entries.keys().next().value;
      if (oldestKey === undefined) break;
      this.delete(oldestKey);
    }
    this.entries.set(key, { value, bytes, expiresAt: now + ttlMs });
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

function hasOnly(params, allowed) {
  for (const key of params.keys()) {
    if (!allowed.has(key) || params.getAll(key).length !== 1) return false;
  }
  return true;
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

const TWELVE_DATA_ALLOWED_SYMBOLS = Object.freeze([
  "AAPL", "NVDA", "MSFT", "TSLA", "AMZN",
  "EUR/USD", "GBP/USD", "USD/JPY",
]);

function normalizeTwelveDataSymbols(symbols) {
  if (!Array.isArray(symbols)) return [];
  const requested = new Set(symbols.map(symbol => String(symbol || "").trim()));
  return TWELVE_DATA_ALLOWED_SYMBOLS.filter(symbol => requested.has(symbol));
}

function normalizeTwelveDataQuotes(payload) {
  const rows = payload && typeof payload === "object" && typeof payload.symbol === "string"
    ? { [payload.symbol]: payload }
    : payload;
  if (!rows || typeof rows !== "object" || Array.isArray(rows)) return {};

  const allowed = new Set(TWELVE_DATA_ALLOWED_SYMBOLS);
  const quotes = {};
  for (const [symbol, row] of Object.entries(rows)) {
    if (!allowed.has(symbol) || !row || typeof row !== "object") continue;
    const price = Number(row.close);
    if (!Number.isFinite(price) || price <= 0) continue;
    const previousClose = Number(row.previous_close);
    const changePercent = Number(row.percent_change);
    const change = Number(row.change);
    const timestamp = Number(row.last_quote_at || row.timestamp);
    quotes[symbol] = {
      p: price,
      c: Number.isFinite(changePercent) ? changePercent : 0,
      prev: Number.isFinite(previousClose) && previousClose > 0 ? previousClose : price,
      change: Number.isFinite(change) ? change : 0,
      currency: typeof row.currency === "string" ? row.currency : null,
      exchange: typeof row.exchange === "string" ? row.exchange : null,
      name: typeof row.name === "string" ? row.name : symbol,
      ts: Number.isFinite(timestamp) && timestamp > 0 ? timestamp : null,
    };
  }
  return quotes;
}

module.exports = {
  BoundedTtlCache,
  FixedWindowRateLimiter,
  normalizeCoinGeckoPath,
  TWELVE_DATA_ALLOWED_SYMBOLS,
  normalizeTwelveDataSymbols,
  normalizeTwelveDataQuotes,
};