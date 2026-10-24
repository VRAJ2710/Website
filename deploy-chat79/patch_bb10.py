#!/usr/bin/env python3
"""bb10: QA chat78 server fixes (a)-(h) + NVDA fundamentals. Server-only, anchor-based, no timers/tables/secrets.
Usage: python3 patch_bb10.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
BASE_MD5 = "d595fee7031ef3458b20fea7efbdb378"
MARK = "// ── bb10:"
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''// ── bb10: QA chat78 fixes. One crypto 24h basis (Coinbase), non-USD market-cap currency, null-safe gold change, energy asset tags,
// US 10-year value+unit, ONE regime object (no thin flips), honest Ask quote chip, ONE session summary, sourced NVDA fundamentals.
// New routes: GET /api/regime, /api/session-summary, /api/desk-quotes. No timers, no tables, no secrets. Server-only.
// BB10_JS
// ── bb10: QA chat78 data fixes. One 24h basis for crypto change, market-cap currency, gold change never 0 when missing, asset tags that
// follow the headline subject, US 10-year as a number plus a unit, one regime object, honest Ask gold chip, one session summary,
// NVDA fundamentals that reconcile or are hidden. Server-only. Free sources only (Coinbase Exchange public stats, Yahoo chart, SEC
// via the existing financials route). In-request caching only: no setInterval/setTimeout/cron, no tables, no secrets, no Stripe.
// Every new top-level name starts with bb10. Internal desk numbers are never presented as market figures.
// BB10_JS
var BB10_CB_MS = 30 * 1000;
var BB10_CB_STALE_MS = 15 * 60 * 1000;
var BB10_REG_KEEP_MS = 12 * 3600 * 1000;
var BB10_REG_RETRY_MS = 60 * 1000;
var BB10_SESS_MS = 60 * 1000;
var BB10_DIV_MS = 6 * 3600 * 1000;
var BB10_CB_COINS = { BTC: 1, ETH: 1, SOL: 1, XRP: 1, DOGE: 1, ADA: 1, AVAX: 1, LINK: 1, LTC: 1, DOT: 1, BCH: 1, ATOM: 1, UNI: 1, XLM: 1, NEAR: 1, SHIB: 1, ETC: 1, FIL: 1, AAVE: 1, ARB: 1, OP: 1, APT: 1, SUI: 1, HBAR: 1, ALGO: 1, MATIC: 1, POL: 1, TRX: 1, TON: 1, PEPE: 1 };
var BB10_CG_ID = { bitcoin: "BTC", ethereum: "ETH", solana: "SOL", ripple: "XRP", dogecoin: "DOGE", cardano: "ADA", "avalanche-2": "AVAX", chainlink: "LINK", litecoin: "LTC", polkadot: "DOT", "bitcoin-cash": "BCH", cosmos: "ATOM", uniswap: "UNI", stellar: "XLM", near: "NEAR", "shiba-inu": "SHIB", "ethereum-classic": "ETC", filecoin: "FIL", aave: "AAVE", arbitrum: "ARB", optimism: "OP", aptos: "APT", sui: "SUI", "hedera-hashgraph": "HBAR", algorand: "ALGO", "matic-network": "MATIC", "polygon-ecosystem-token": "POL", tron: "TRX", "the-open-network": "TON", pepe: "PEPE" };
var bb10Cb = new Map();
var bb10CbFly = new Map();
var bb10SessMem = { at: 0, ms: 0, out: null };
var bb10DivMem = new Map();
function bb10Has(v) { return v !== null && v !== undefined && v !== "" && typeof v !== "boolean" && typeof v !== "object" && isFinite(Number(v)); }
function bb10N(v) { return bb10Has(v) ? Number(v) : null; }
function bb10R(n, d) { var k = Math.pow(10, d == null ? 2 : d); return Math.round(Number(n) * k) / k; }
function bb10Iso(ms) { try { return new Date(ms).toISOString(); } catch (e) { return null; } }
function bb10Uk(ms) {
  try {
    var d = new Date(ms), p = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).forEach(function (x) { p[x.type] = x.value; });
    return p.weekday + " " + p.day + " " + p.month + ", " + p.hour + ":" + p.minute + " UK";
  } catch (e) { return ""; }
}
function bb10Money(n, ccy) {
  n = Number(n);
  if (!(n > 0)) return "";
  var c = String(ccy || "").toUpperCase();
  if (c === "GBX" || c === "GBP") c = "GBP";
  var sym = c === "USD" ? "$" : c === "GBP" ? "\u00a3" : c === "EUR" ? "\u20ac" : (c ? c + " " : "");
  var u = n >= 1e12 ? [1e12, "tn"] : n >= 1e9 ? [1e9, "bn"] : n >= 1e6 ? [1e6, "m"] : [1, ""];
  return sym + (n / u[0]).toFixed(1) + u[1];
}
function bb10Clone(o) { try { return JSON.parse(JSON.stringify(o)); } catch (e) { return o; } }
function bb10Addr(req) { var fwd = String((req && req.headers && req.headers["x-forwarded-for"]) || "").split(",")[0].trim(); return fwd || (req && req.socket && req.socket.remoteAddress) || "unknown"; }

// ── (a) crypto 24h change: ONE basis for every endpoint ──
// Basis: Coinbase Exchange public /products/<COIN>-USD/stats. `open` is the price 24 hours before the call, `last` the latest
// trade. This is the same open_24h the live ticker's websocket (ws-feed.exchange.coinbase.com) reports, so the table, the API and
// the market page now read one number. Yahoo previous close and CoinGecko's rolling figure are only used (and labelled) when
// Coinbase is unreachable.
async function bb10CbOne(coin) {
  var key = String(coin || "").toUpperCase();
  if (!BB10_CB_COINS[key]) return null;
  var hit = bb10Cb.get(key), now = Date.now();
  if (hit && now - hit.at < BB10_CB_MS) return hit;
  if (bb10CbFly.has(key)) return bb10CbFly.get(key);
  var job = (async function () {
    try {
      var r = await fetch("https://api.exchange.coinbase.com/products/" + key + "-USD/stats", { signal: AbortSignal.timeout(3500), headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" } });
      if (!r.ok) throw new Error("coinbase " + r.status);
      var j = await r.json();
      var open = Number(j && j.open), last = Number(j && j.last);
      if (!(open > 0) || !(last > 0)) throw new Error("coinbase empty");
      var row = { coin: key, open: open, last: last, high: bb10N(j.high), low: bb10N(j.low), at: Date.now() };
      bb10Cb.set(key, row);
      if (bb10Cb.size > 64) bb10Cb.delete(bb10Cb.keys().next().value);
      return row;
    } catch (e) { return null; } finally { bb10CbFly.delete(key); }
  })();
  bb10CbFly.set(key, job);
  return job;
}
async function bb10CryptoLoad(coins) {
  var list = Array.from(new Set((coins || []).map(function (c) { return String(c).toUpperCase(); }))).filter(function (c) { return BB10_CB_COINS[c]; }).slice(0, 12);
  await Promise.all(list.map(function (c) { return bb10CbOne(c).catch(function () { return null; }); }));
}
function bb10CbRow(coin) {
  var h = bb10Cb.get(String(coin || "").toUpperCase());
  return h && Date.now() - h.at < BB10_CB_STALE_MS ? h : null;
}
function bb10CryptoPct(coin) {
  var h = bb10CbRow(coin);
  return h ? bb10R((h.last / h.open - 1) * 100, 4) : null;
}
function bb10CoinOf(sym) {
  var m = /^([A-Z0-9]{2,6})(?:-USD|\/USD)$/i.exec(String(sym || "").trim());
  return m && BB10_CB_COINS[m[1].toUpperCase()] ? m[1].toUpperCase() : "";
}
function bb10CoinsIn(text) {
  var out = [], re = /\b([A-Za-z0-9]{2,6})[-\/]USD\b/g, m, s = String(text || "");
  while ((m = re.exec(s))) { var c = m[1].toUpperCase(); if (BB10_CB_COINS[c] && out.indexOf(c) < 0) out.push(c); }
  return out;
}
function bb10CryptoFields(o, h) {
  var pct = bb10R((h.last / h.open - 1) * 100, 4), at = h.at;
  o.changeBasis = "rolling 24h";
  o.changeBasisLabel = "Rolling 24 hours: latest trade against the price 24 hours earlier (Coinbase Exchange)";
  o.baselinePrice = h.open;
  o.baselineAt = bb10Iso(at - 24 * 3600 * 1000);
  o.baselineAtUk = bb10Uk(at - 24 * 3600 * 1000);
  o.changeSource = "Coinbase Exchange public stats (api.exchange.coinbase.com/products/" + h.coin + "-USD/stats)";
  o.changeAsOf = bb10Iso(at);
  o.changeAsOfUk = bb10Uk(at);
  o.lastTrade = h.last;
  return pct;
}
function bb10CryptoRow(v, sym) {
  var coin = bb10CoinOf(sym);
  if (!coin || !v || typeof v !== "object") return v;
  var h = bb10CbRow(coin);
  var o = Object.assign({}, v);
  if (h) {
    var pct = bb10CryptoFields(o, h);
    o.c = pct; o.changePct = pct; o.prev = h.open; o.prevClose = h.open; o.change = bb10R(h.last - h.open, 6);
    o.basis = "rolling_24h"; o.baselineSource = "Coinbase Exchange 24h open"; o.baselineAsOf = o.baselineAt;
    o.changeAvailable = true;
    return o;
  }
  // Coinbase not reachable: keep the figure we have but say plainly which basis it is
  var p = bb10N(v.p != null ? v.p : v.price), pv = bb10N(v.prev != null ? v.prev : v.prevClose);
  o.changeBasis = v.basis === "rolling_24h" ? "rolling 24h" : "previous close";
  o.changeBasisLabel = v.basis === "rolling_24h" ? "Rolling 24 hours (" + String(v.baselineSource || "CoinGecko") + ")" : "Previous close (" + String(v.exchange || v.source || "Yahoo Finance") + "); Coinbase 24h basis unavailable right now";
  o.baselinePrice = pv != null && pv > 0 ? pv : null;
  o.baselineAt = v.baselineAsOf || null;
  o.baselineAtUk = v.baselineAsOf ? bb10Uk(Date.parse(v.baselineAsOf)) : null;
  o.changeSource = String(v.baselineSource || v.source || v.exchange || "Yahoo Finance");
  if (p == null) o.baselinePrice = null;
  return o;
}
// CoinGecko proxy bodies: /coins/markets rows and /simple/price maps. Only when Coinbase has the coin.
function bb10CgBody(body) {
  if (Array.isArray(body)) {
    var any = false;
    var rows = body.map(function (r) {
      var coin = r && typeof r === "object" ? BB10_CG_ID[String(r.id || "")] : "", h = coin ? bb10CbRow(coin) : null;
      if (!h) return r;
      any = true;
      var o = Object.assign({}, r), pct = bb10CryptoFields(o, h);
      o.coingecko_price_change_percentage_24h = r.price_change_percentage_24h == null ? null : r.price_change_percentage_24h;
      o.price_change_percentage_24h = pct;
      o.price_change_24h = bb10R(h.last - h.open, 6);
      return o;
    });
    return any ? rows : body;
  }
  if (body && typeof body === "object") {
    var out = null;
    Object.keys(body).forEach(function (id) {
      var coin = BB10_CG_ID[id], h = coin ? bb10CbRow(coin) : null, row = body[id];
      if (!h || !row || typeof row !== "object" || !("usd_24h_change" in row)) return;
      out = out || Object.assign({}, body);
      var o = Object.assign({}, row), pct = bb10CryptoFields(o, h);
      o.coingecko_usd_24h_change = row.usd_24h_change == null ? null : row.usd_24h_change;
      o.usd_24h_change = pct;
      out[id] = o;
    });
    return out || body;
  }
  return body;
}

// ── (c)/(d)/(e) per-row shaping: gold display change, US 10-year value + unit ──
function bb10IsGoldKey(k) { return /^(?:XAU|XAUUSD|XAU\/USD|GOLD)$/i.test(String(k || "")); }
function bb10GoldRow(v) {
  var o = Object.assign({}, v);
  var c = bb10N(v.c != null ? v.c : v.changePct);
  if (c != null && v.changeAvailable !== false && v.noPrevClose !== true) {
    o.displayChange = { pct: bb10R(c, 4), instrument: "spot", symbol: "XAU", label: "Gold spot", basis: v.basis || "previous_close", source: v.source || null, asOf: v.asOf || null, asOfUk: v.asOfUk || null, text: null };
    o.changeDisplayPct = o.displayChange.pct;
    return o;
  }
  var f = v.futuresChange && typeof v.futuresChange === "object" ? v.futuresChange : null, fp = f ? bb10N(f.changePct) : null;
  if (f && fp != null) {
    o.displayChange = {
      pct: bb10R(fp, 4), instrument: "futures", symbol: f.symbol || "GC=F", label: f.label || "Gold futures (GC=F, delayed 10 min)", basis: "previous_close",
      price: bb10N(f.price), prevClose: bb10N(f.prevClose), change: bb10N(f.change), source: f.source || "Yahoo Finance", asOf: f.asOf || null, asOfUk: f.asOfUk || null,
      text: f.text || ("gold futures (GC=F) " + (fp > 0 ? "+" : fp < 0 ? "\u2212" : "") + Math.abs(fp).toFixed(2) + "% today"),
      note: "Gold spot has no previous close in the free feed, so this is the change in gold futures (GC=F). It is not spot's change."
    };
    o.changeDisplayPct = o.displayChange.pct;
    return o;
  }
  o.displayChange = null;
  o.changeDisplayPct = null;
  o.changeNote = o.changeNote || "No gold change figure is available right now. Show a dash, not 0.00%.";
  return o;
}
function bb10YieldRow(v) {
  var p = bb10N(v.p != null ? v.p : v.price);
  if (p == null) return v;
  var o = Object.assign({}, v);
  o.unit = "percent";
  o.value = bb10R(p, 3);
  var ch = bb10N(v.change);
  if (ch != null) { o.changePp = bb10R(ch, 3); o.changeBp = bb10R(ch * 100, 1); o.changeUnit = "percentage points"; }
  o.valueNote = "p is the 10-year yield in percent (4.99 means 4.99%). The server never appends a % sign to it; add the unit once in the UI.";
  return o;
}
function bb10RowKey(v, k) { return String((v && (v.symbol || v.feedSymbol)) || k || ""); }
function bb10Rows(map) {
  if (!map || typeof map !== "object" || Array.isArray(map)) return map;
  var out = null;
  Object.keys(map).forEach(function (k) {
    var v = map[k];
    if (!bb8oIsRow(v) && !(v && typeof v === "object" && ("futuresChange" in v || "changeAvailable" in v))) return;
    var n = v;
    var ks = String(k);
    if (bb10CoinOf(ks) || bb10CoinOf(v.symbol)) n = bb10CryptoRow(v, bb10CoinOf(ks) ? ks : v.symbol);
    else if (bb10IsGoldKey(ks)) n = bb10GoldRow(v);
    else if (/^\^TNX$/i.test(ks) || /^\^TNX$/i.test(String(v.symbol || ""))) n = bb10YieldRow(v);
    if (bb10N(n.marketCap) > 0) n = bb10CapFields(n, n.marketCapCurrency || n.currency);
    if (n !== v) { out = out || Object.assign({}, map); out[k] = n; }
  });
  return out || map;
}
// non-USD listings: market cap with its own currency, never "$" by default
function bb10CapFields(v, ccy) {
  var mc = bb10N(v && v.marketCap);
  if (!(mc > 0)) return v;
  var c = String(ccy || (v && (v.marketCapCurrency || v.priceCurrency || v.currency)) || "").trim();
  if (!c) return v;
  if (c === "GBp" || c === "GBX") c = "GBP";
  var o = Object.assign({}, v);
  o.marketCapCurrency = c.toUpperCase();
  o.marketCapText = typeof bb8rCapText === "function" ? bb8rCapText(mc, o.marketCapCurrency) : bb10Money(mc, o.marketCapCurrency);
  o.marketCapSource = "Yahoo Finance (" + (o.marketCapCurrency === "USD" ? "USD" : "quoted in " + o.marketCapCurrency) + ")";
  return o;
}

// ── (f) ONE regime object ──
// The only place a regime is computed is bb3Mood (bb3Compute for card scores, bb8q for Ask, /api/market-reference-quotes, /api/regime,
// meta.regime). bb8r already keeps one row for 10 minutes. bb10 adds: (1) the Bitcoin input uses the same 24h basis as the tape;
// (2) a thin recompute (fewer than 4 of the 5 inputs, or VIX / S&P 500 missing) never replaces a good row: the previous regime is
// kept for up to 12 hours and marked stale + thin; (3) one public object with computedAt/asOf in UK time for every endpoint.
var bb10RegPub0 = typeof bb8rRegimePublic === "function" ? bb8rRegimePublic : null;
var bb10Good = null;
function bb10MoodView(m) {
  m = m || {};
  var keys = ["vix", "spx", "dxy", "oil", "btc"], used = 0, view = {};
  keys.forEach(function (k) { var n = bb10N(m[k]); view[k] = n; if (n != null) used++; });
  var thin = used < 4 || view.vix == null || view.spx == null;
  return { view: view, used: used, of: 5, thin: thin };
}
function bb10MoodArgs(m) {
  if (!m || typeof m !== "object") return { m: m, info: bb10MoodView(m), btcBasis: null };
  var cb = bb10CryptoPct("BTC"), m2 = Object.assign({}, m);
  if (cb != null) m2.btc = cb;
  var info = bb10MoodView(m2);
  info.btcBasis = cb != null ? "Coinbase Exchange rolling 24h" : "feed previous close";
  return { m: m2, info: info };
}
function bb10RegimeNote(row) {
  if (!row) return "";
  if (row.bb10Thin && row.bb10Stale) return "Kept from the last full reading (" + row.asOfUk + "). The latest check had too few market inputs (" + (row.bb10Inputs ? row.bb10Inputs.used : "?") + " of 5), so the regime was not recomputed.";
  if (row.bb10Thin) return "Computed from " + (row.bb10Inputs ? row.bb10Inputs.used : "?") + " of 5 inputs; treat as provisional.";
  return "";
}
function bb10RegimePublic(row) {
  row = row || (typeof bb8rRegimeRow === "function" ? bb8rRegimeRow() : null) || (bb8rReg && bb8rReg.row) || null;
  if (!row || !row.mood) return null;
  if (row.bb10Inputs && row.bb10Inputs.used < 3 && row.bb10Stale !== true) return null; // no previous good reading and almost no inputs: publish no regime rather than a default 50
  var base = bb10RegPub0 ? bb10RegPub0(row) : { regime: row.mood.regime, score: row.mood.score, asOf: row.asOfIso, asOfUk: row.asOfUk };
  var chk = row.bb10CheckedAt || row.asOf;
  var o = Object.assign({}, base);
  o.label = row.mood.regime;
  o.computedAt = row.asOfIso;
  o.computedAtUk = row.asOfUk;
  o.checkedAt = bb10Iso(chk);
  o.checkedAtUk = bb10Uk(chk);
  o.thin = row.bb10Thin === true;
  o.stale = row.bb10Stale === true;
  o.inputs = row.bb10Inputs ? { vix: row.bb10Inputs.view.vix, spx: row.bb10Inputs.view.spx, dxy: row.bb10Inputs.view.dxy, oil: row.bb10Inputs.view.oil, btc: row.bb10Inputs.view.btc, used: row.bb10Inputs.used, of: 5, btcBasis: row.bb10Inputs.btcBasis || null } : null;
  o.source = "Dispatch regime model (ours): VIX, S&P 500 move, dollar index, oil and Bitcoin move from Yahoo Finance and Coinbase Exchange";
  o.method = "Same score for every visitor, brief, dashboard, intel strip, pill and Ask: computed once, kept 10 minutes, and never replaced by a reading built from too few inputs.";
  o.note = bb10RegimeNote(row) || null;
  return o;
}
function bb10RegimeText(row) {
  var p = bb10RegimePublic(row);
  if (!p) return "";
  var t = "Dispatch regime model (ours): market mood " + p.regime + ", score " + p.score + "/100, computed " + p.computedAtUk + ".";
  if (p.stale) t += " Kept from the last full reading; the latest check had too few inputs.";
  return t;
}
async function bb10RegimeEnsure() {
  var now = Date.now();
  try { await bb10CryptoLoad(["BTC"]); } catch (e) {}
  var row = typeof bb8rRegimeRow === "function" ? bb8rRegimeRow() : null;
  if (row) return row;
  try {
    var pack = await bb3Pack(now), Q = (pack && pack.quotes) || {};
    var ip = bb3QuotePct(Q["^GSPC"]), sp = bb3QuotePct(Q["SPY"]);
    var dq = pack && pack.dxy && Number(pack.dxy.p) > 0 ? pack.dxy : Q["DX-Y.NYB"];
    bb3Mood({ vix: bb3QuotePx(Q["^VIX"]), spx: ip != null ? ip : sp, dxy: bb3QuotePx(dq), oil: bb3QuotePx(Q["CL=F"]), btc: bb3QuotePct(Q["BTC-USD"]) });
  } catch (e) {}
  return (typeof bb8rRegimeRow === "function" ? bb8rRegimeRow() : null) || (bb8rReg && bb8rReg.row) || null;
}
async function bb10RegimeRoute(req, res) {
  var row = await bb10RegimeEnsure();
  var p = bb10RegimePublic(row);
  if (!p) return json(res, 200, { available: false, reason: "Regime inputs are not available right now. No regime is shown rather than a guessed one.", asOfUk: bb10Uk(Date.now()), asOf: bb10Iso(Date.now()) });
  return json(res, 200, Object.assign({ available: true }, p));
}
// text rewrite used for /api/brief context and answers: any "Regime: Risk-On (score 55/100)" style mention becomes the server's
function bb10RegimeRewrite(s, row) {
  var p = bb10RegimePublic(row);
  if (typeof s !== "string" || !p) return s;
  var lab = "(?:Risk-On|Risk-Off|Transition)";
  var t = s.replace(new RegExp("(Regime:\\s*)" + lab + "(?:\\s*\\((?:score\\s*)?\\d{1,3}(?:\\.\\d+)?(?:\\/100)?\\))?", "g"), "$1" + p.regime + " (score " + p.score + "/100)");
  t = t.replace(new RegExp("\\b" + lab + "(\\s*(?:\\u00b7|,|-|\\u2013)?\\s*)\\d{1,3}\\/100", "g"), p.regime + "$1" + p.score + "/100");
  return t;
}
function bb10RegimeWalk(o, row, depth) {
  if (depth > 5 || !o || typeof o !== "object") return;
  Object.keys(o).forEach(function (k) {
    var v = o[k];
    if (typeof v === "string") { var n = bb10RegimeRewrite(v, row); if (n !== v) o[k] = n; }
    else if (v && typeof v === "object") bb10RegimeWalk(v, row, depth + 1);
  });
}

// ── (c) null-safe change wording: a missing change is "no figure", never "unchanged" / "+0.00%" ──
var BB10_NOCHG = "has no change figure available";
// ── (d) Academy: energy stories are tagged to energy, not gold ──
var BB10_ENERGY = /\b(lng|natural gas|liquefied natural gas|gas (?:pipelines?|fields?|plants?|terminals?|exports?|supply|supplies|flows?|storage)|oil|crude|brent|wti|opec|refiner(?:y|ies)|tankers?|pipelines?|energy (?:sites|facilities|infrastructure|prices?|crisis|supply))\b/i;
var BB10_GOLD_OK = /\b(gold|bullion|safe[- ]havens?|flight to safety|risk[- ]off|fed|federal reserve|fomc|powell|dollar|greenback|dxy|yields?|treasur(?:y|ies)|inflation|rate (?:cut|hike)s?)\b/i;
function bb10AcademySetup() {
  if (typeof RT48B_ASSETS !== "object" || RT48B_ASSETS.natgas) return false;
  // plain "gas prices" is left out on purpose: it is petrol in UK/US headlines
  RT48B_ASSETS.natgas = ["natural gas prices", /\b(lng|liquefied natural gas|natural gas|nat gas|natgas)\b/i];
  RT48B_NM.natgas = "lng|liquefied natural gas|natural gas|natgas";
  RT48B_ALIAS["natural gas"] = "natgas"; RT48B_ALIAS["nat gas"] = "natgas"; RT48B_ALIAS["natgas"] = "natgas"; RT48B_ALIAS["lng"] = "natgas"; RT48B_ALIAS["gas"] = "natgas"; RT48B_ALIAS["natural gas prices"] = "natgas";
  var sup = /\b(?:lng|liquefied natural gas|natural gas|gas (?:pipelines?|fields?|plants?|terminals?|exports?|supply|supplies|flows?))\b/i;
  RT48B_RULES.push([new RegExp("(?:" + sup.source + ").*\\b(?:outage|disrupt\\w*|halt\\w*|shut\\w*|attack\\w*|strikes?|struck|explosion|force majeure|blockade|sanction\\w*|cut off)\\b|\\b(?:outage|disrupt\\w*|halt\\w*|shut\\w*|attack\\w*|strikes?|struck|explosion|force majeure|blockade|sanction\\w*)\\b.*(?:" + sup.source + ")", "i"), { natgas: ["up", "A disruption to LNG or natural gas supply usually lifts gas prices first, because fewer cargoes or less pipeline gas are expected to reach buyers."] }]);
  RT48B_RULES.push([new RegExp("(?:" + sup.source + ").*\\b(?:glut|surplus|oversuppl\\w*|storage (?:build|surplus))\\b", "i"), { natgas: ["down", "Signs of too much LNG or natural gas supply usually push gas prices lower first, as more cargoes compete for buyers."] }]);
  return true;
}
function bb10GoldGuard(x) {
  if (!x || x.asset !== "gold") return "";
  var h = String(x.h || "");
  if (BB10_ENERGY.test(h) && !BB10_GOLD_OK.test(h)) return "gold-not-headline-subject";
  return "";
}
function bb10Fallback() {
  // The stock example no longer defaults to gold: a Fed cut is about rates, so the first asset named is the US dollar.
  try {
    var H = { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" };
    var r = _rt48bRule(H.h, "usd");
    if (r) { var it = _rt48bItem(H, "usd", r[0], r[1], "template"); if (_rt48bValid(it)) return [it]; }
  } catch (e) {}
  return null;
}
// the plain US 10-year object: a number and a separate unit. Nothing here ends in "%".
function bb10Us10y(q, ts) {
  var row = q && typeof q === "object" ? q : null, p = row ? bb10N(row.p != null ? row.p : row.price) : null;
  if (!(p > 0)) return null;
  var ms = row.ts != null && isFinite(Number(row.ts)) ? (Number(row.ts) < 1e12 ? Number(row.ts) * 1000 : Number(row.ts)) : (ts || Date.now());
  var ch = bb10N(row.change), prev = bb10N(row.prev != null ? row.prev : row.prevClose);
  if (ch == null && prev != null) ch = p - prev;
  return {
    symbol: "^TNX", label: "US 10-year yield", value: bb10R(p, 3), unit: "percent", unitSymbol: "%",
    prevClose: prev != null ? bb10R(prev, 3) : null, change: ch != null ? bb10R(ch, 3) : null, changeUnit: "percentage points", changeBp: ch != null ? bb10R(ch * 100, 1) : null,
    asOf: bb10Iso(ms), asOfUk: bb10Uk(ms), source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)",
    note: "value is in percent (4.99 = 4.99%). Show the % once, in the UI."
  };
}
function bb10Dedupe(o, depth) {
  if (!o || typeof o !== "object" || (depth || 0) > 6) return o;
  Object.keys(o).forEach(function (k) {
    var v = o[k];
    if (typeof v === "string") { if (/%{2,}/.test(v)) o[k] = v.replace(/%{2,}/g, "%"); }
    else if (v && typeof v === "object") bb10Dedupe(v, (depth || 0) + 1);
  });
  return o;
}

// ── (h) ONE session summary ──
var BB10_VENUES = [
  { id: "us", cls: "equities", label: "US stocks (NYSE/Nasdaq)", sym: "SPY" },
  { id: "lse", cls: "equities", label: "London (LSE)", sym: "VOD.L" },
  { id: "frankfurt", cls: "equities", label: "Frankfurt (Xetra)", sym: "SAP.DE" },
  { id: "paris", cls: "equities", label: "Paris (Euronext)", sym: "MC.PA" },
  { id: "tokyo", cls: "equities", label: "Tokyo (TSE)", sym: "7203.T" },
  { id: "hk", cls: "equities", label: "Hong Kong (HKEX)", sym: "0700.HK" },
  { id: "korea", cls: "equities", label: "Seoul (KRX)", sym: "005930.KS" },
  { id: "sydney", cls: "equities", label: "Sydney (ASX)", sym: "BHP.AX" },
  { id: "india", cls: "equities", label: "India (NSE)", sym: "RELIANCE.NS" },
  { id: "gold", cls: "commodities", label: "Gold (COMEX futures)", sym: "GC=F" },
  { id: "oil", cls: "commodities", label: "Oil (NYMEX futures)", sym: "CL=F" },
  { id: "fx", cls: "fx", label: "Foreign exchange", sym: "EURUSD=X" },
  { id: "crypto", cls: "crypto", label: "Crypto", sym: "BTC-USD" }
];
function bb10CalendarThrough() {
  var best = "";
  try { Object.keys(bb6Full || {}).forEach(function (b) { Object.keys(bb6Full[b] || {}).forEach(function (d) { if (d > best) best = d; }); }); } catch (e) {}
  return best;
}
function bb10Venue(v, now) {
  var o = { id: v.id, label: v.label, class: v.cls, symbol: v.sym, open: false, status: "closed" };
  try {
    var spec = typeof bb5gSpec === "function" ? bb5gSpec(v.sym) : bb5eSpec(v.sym);
    var q = bb5eApply({ ts: Math.floor(now / 1000) }, v.sym, null, now);
    var st = String(q.status || "closed");
    o.status = st === "closed" ? "closed" : st === "quiet" ? "quiet" : "open";
    o.open = o.status === "open";
    var book = null, hit = null;
    try { spec.bb6Sym = v.sym; book = bb6Book(spec); hit = bb6Hit(spec, new Date(now)); } catch (e) {}
    o.calendar = book ? "holiday-aware" : (spec && (spec.mode === "always") ? "24/7" : "hours-based");
    o.hoursBased = o.calendar === "hours-based";
    if (hit && hit.name) o.holiday = hit.name + (hit.early ? " (early close)" : "");
    if (q.nextOpen) { o.nextOpen = q.nextOpen; o.nextOpenUk = bb10Uk(Date.parse(q.nextOpen)); }
    if (o.open && spec && spec.mode === "cash" && typeof bb5eParts === "function") {
      var p = bb5eParts(spec.tz, new Date(now)), end = hit && hit.early ? hit.early : (spec.lo != null && p.m < spec.lo ? spec.lo : spec.c);
      if (isFinite(Number(end)) && isFinite(Number(p.m)) && end > p.m) { var cl = now + (end - p.m) * 60000; o.nextClose = bb10Iso(cl); o.nextCloseUk = bb10Uk(cl); }
    }
    if (o.status === "quiet") o.note = "Thin hours: the local market is shut, only the global desk is quoting";
    else if (o.status === "closed" && q.note) o.note = String(q.note);
  } catch (e) { o.status = "unknown"; o.open = false; o.calendar = "unknown"; }
  return o;
}
function bb10Sessions(now) {
  now = now == null ? Date.now() : now;
  if (bb10SessMem.out && Math.abs(now - bb10SessMem.at) < BB10_SESS_MS) return bb10SessMem.out;
  var ven = BB10_VENUES.map(function (v) { return bb10Venue(v, now); });
  var by = {}, nOpen = 0, nClosed = 0, nQuiet = 0, unk = 0;
  ven.forEach(function (v) {
    var c = by[v.class] = by[v.class] || { open: 0, closed: 0, quiet: 0, total: 0, openIds: [], closedIds: [] };
    c.total++;
    if (v.status === "open") { c.open++; c.openIds.push(v.id); nOpen++; }
    else if (v.status === "quiet") { c.quiet++; nQuiet++; c.closedIds.push(v.id); }
    else if (v.status === "closed") { c.closed++; nClosed++; c.closedIds.push(v.id); }
    else unk++;
  });
  var nexts = ven.filter(function (v) { return !v.open && v.nextOpen; }).sort(function (a, b) { return Date.parse(a.nextOpen) - Date.parse(b.nextOpen); })[0];
  var closes = ven.filter(function (v) { return v.open && v.nextClose; }).sort(function (a, b) { return Date.parse(a.nextClose) - Date.parse(b.nextClose); })[0];
  var through = bb10CalendarThrough();
  var out = {
    asOf: bb10Iso(now), asOfUk: bb10Uk(now), timezone: "Europe/London",
    tradingNow: nOpen, closed: nClosed + nQuiet, quiet: nQuiet, total: ven.length, unknown: unk,
    text: nOpen + " of " + ven.length + " markets trading now, " + (nClosed + nQuiet) + " closed (" + bb10Uk(now) + ")",
    byClass: by, markets: ven,
    nextOpen: nexts ? { id: nexts.id, label: nexts.label, at: nexts.nextOpen, atUk: nexts.nextOpenUk } : null,
    nextClose: closes ? { id: closes.id, label: closes.label, at: closes.nextClose, atUk: closes.nextCloseUk } : null,
    basis: "Dispatch session table: published exchange hours, plus a built-in exchange holiday calendar for US, London, Tokyo, Hong Kong, Seoul, Sydney and India" + (through ? " (entries to " + through + ")" : "") + ". Frankfurt and Paris are hours-based: their holidays are not in the calendar. Crypto trades 24/7; FX runs from Sunday evening to Friday evening.",
    source: "Dispatch session calendar (ours)", cacheSec: BB10_SESS_MS / 1000
  };
  bb10SessMem = { at: now, ms: BB10_SESS_MS, out: out };
  return out;
}
async function bb10SessionRoute(req, res) { return json(res, 200, bb10Sessions(Date.now())); }

// ── P2: fundamentals (NVDA etc): reconcile or hide, and label every figure with its source ──
function bb10DayMs(s) { var t = Date.parse(String(s || "").slice(0, 10) + "T00:00:00Z"); return isFinite(t) ? t : null; }
function bb10EvParse(j, sym) {
  var r = j && j.chart && j.chart.result && j.chart.result[0];
  if (!r || !r.meta) return null;
  var ev = r.events || {}, divs = [], splits = [];
  Object.keys(ev.dividends || {}).forEach(function (k) { var d = ev.dividends[k]; if (d && bb10N(d.amount) != null) divs.push({ t: Number(d.date || k) * 1000, amount: Number(d.amount) }); });
  Object.keys(ev.splits || {}).forEach(function (k) { var s = ev.splits[k]; if (s && bb10N(s.numerator) > 0 && bb10N(s.denominator) > 0) splits.push({ t: Number(s.date || k) * 1000, num: Number(s.numerator), den: Number(s.denominator), text: String(s.splitRatio || (s.numerator + ":" + s.denominator)) }); });
  divs.sort(function (a, b) { return a.t - b.t; }); splits.sort(function (a, b) { return a.t - b.t; });
  return { symbol: sym, currency: String(r.meta.currency || ""), price: bb10N(r.meta.regularMarketPrice), priceAt: r.meta.regularMarketTime ? Number(r.meta.regularMarketTime) * 1000 : null, divs: divs, splits: splits, at: Date.now() };
}
async function bb10EventsLoad(sym) {
  sym = String(sym || "").toUpperCase();
  if (!/^[A-Z0-9^][A-Z0-9.^=-]{0,14}$/.test(sym)) return null;
  var hit = bb10DivMem.get(sym), now = Date.now();
  if (hit && hit.ev && now - hit.at < BB10_DIV_MS) return hit.ev;
  if (hit && hit.fail && now - hit.at < 5 * 60000) return null;
  if (hit && hit.pr) return hit.pr;
  var pr = (async function () {
    try {
      var r = await upstream("https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sym) + "?range=max&interval=1mo&events=div%2Csplits", { headers: { "user-agent": "Mozilla/5.0 (compatible; DispatchBot/1.0)", accept: "application/json" }, timeoutMs: 6000 });
      var j = JSON.parse(await readTextCapped(r, 3000000)), ev = bb10EvParse(j, sym);
      if (!ev) throw new Error("no chart");
      bb10DivMem.set(sym, { at: Date.now(), ev: ev });
      return ev;
    } catch (e) { bb10DivMem.set(sym, { at: Date.now(), fail: true }); return null; }
    finally { while (bb10DivMem.size > 64) bb10DivMem.delete(bb10DivMem.keys().next().value); }
  })();
  bb10DivMem.set(sym, { at: now, pr: pr });
  return pr;
}
function bb10EvFresh(sym) { var h = bb10DivMem.get(String(sym || "").toUpperCase()); return h && h.ev && Date.now() - h.at < BB10_DIV_MS ? h.ev : null; }
function bb10SplitFactor(ev, endMs) {
  var f = 1;
  if (ev && endMs != null) ev.splits.forEach(function (s) { if (s.t > endMs) f *= s.num / s.den; });
  return f;
}
function bb10Within(x, ref, lo, hi) { return x > 0 && ref > 0 && x / ref >= lo && x / ref <= hi; }
// split-adjust (or hide) every EPS figure. Share count implied by net income / EPS must match the latest quarter.
function bb10EpsRows(fin, ev, notes) {
  var q = Array.isArray(fin.quarterly) ? fin.quarterly : [], a = Array.isArray(fin.annual) ? fin.annual : [];
  var refRow = q.find(function (r) { return bb10N(r.eps) > 0 && bb10N(r.netIncome) > 0; }) || a.find(function (r) { return bb10N(r.eps) > 0 && bb10N(r.netIncome) > 0; });
  var ref = refRow ? refRow.netIncome / refRow.eps : null;
  function fix(r) {
    var o = Object.assign({}, r);
    if (bb10N(o.eps) == null) return o;
    var endMs = bb10DayMs(o.end), F = bb10SplitFactor(ev, endMs);
    var sh = bb10N(o.netIncome) != null && o.eps !== 0 ? o.netIncome / o.eps : null;
    if (ref && sh && sh > 0) {
      if (bb10Within(sh, ref, 0.5, 1.5)) return o;
      if (F > 1.0001 && bb10Within(sh * F, ref, 0.5, 1.5)) {
        o.epsReported = o.eps; o.eps = bb10R(o.eps / F, 3);
        o.epsAdjusted = { factor: bb10R(F, 4), reportedEps: o.epsReported, note: "Restated for later stock splits (divided by " + bb10R(F, 4) + ") so it is comparable with current EPS", source: "SEC EDGAR EPS as filed; split dates from Yahoo Finance" };
        notes.push(o.period + " EPS restated for splits");
        return o;
      }
      var why = ev ? "share count implied by net income / EPS does not match the current basis" : "share count basis changed (split) and split dates were unavailable";
      o.epsReported = o.eps; delete o.eps; o.epsHidden = why; notes.push(o.period + " EPS hidden: " + why);
      return o;
    }
    return o;
  }
  fin.annual = a.map(fix); fin.quarterly = q.map(fix);
  return ref;
}
function bb10TtmEps(fin) {
  var q = Array.isArray(fin && fin.quarterly) ? fin.quarterly.filter(function (r) { return bb10N(r.eps) != null && bb10DayMs(r.end) != null; }) : [];
  if (q.length < 4) return null;
  q.sort(function (x, y) { return bb10DayMs(y.end) - bb10DayMs(x.end); });
  var four = q.slice(0, 4), ok = true;
  for (var i = 0; i < 3; i++) { var gap = (bb10DayMs(four[i].end) - bb10DayMs(four[i + 1].end)) / 864e5; if (gap < 75 || gap > 110) ok = false; }
  if (!ok || Date.now() - bb10DayMs(four[0].end) > 200 * 864e5) return null;
  var sum = four.reduce(function (s, r) { return s + Number(r.eps); }, 0);
  return { value: bb10R(sum, 2), ends: four.map(function (r) { return r.end; }), through: four[0].end, quarters: four.map(function (r) { return r.eps; }) };
}
function bb10DayUk(s) { var t = bb10DayMs(s); if (t == null) return String(s || ""); return new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }); }
function bb10Dividend(ev, val, hidden) {
  var now = Date.now(), px = ev && ev.price > 0 ? ev.price : null;
  if (!ev || !(px > 0)) return null;
  var yr = ev.divs.filter(function (d) { return d.t > now - 365 * 864e5; });
  if (!ev.divs.length || !yr.length) return { paysDividend: false, source: "Yahoo Finance dividend history", note: "No dividend paid in the last 12 months" };
  var last = ev.divs[ev.divs.length - 1], prev = ev.divs.length > 1 ? ev.divs[ev.divs.length - 2] : null;
  var trailing = yr.reduce(function (s, d) { return s + d.amount; }, 0), fwd = last.amount * yr.length;
  var o = {
    paysDividend: true, currency: ev.currency, payments12m: yr.length,
    forwardAnnual: bb10R(fwd, 4), forwardYield: bb10R(fwd / px, 5), forwardYieldPct: bb10R(100 * fwd / px, 3),
    trailingAnnual: bb10R(trailing, 4), trailingYield: bb10R(trailing / px, 5), trailingYieldPct: bb10R(100 * trailing / px, 3),
    last: { amount: bb10R(last.amount, 4), exDate: bb10Iso(last.t).slice(0, 10) },
    price: bb10R(px, 2), priceSource: "Yahoo Finance chart",
    basis: "forward = latest payment x payments in the last 12 months; trailing = sum of the last 12 months of payments",
    source: "Yahoo Finance dividend history (chart events)"
  };
  if (prev && prev.amount > 0 && last.amount >= 3 * prev.amount) o.note = "The dividend was raised from " + bb10R(prev.amount, 4) + " to " + bb10R(last.amount, 4) + " per payment (ex-date " + o.last.exDate + "). Forward yield uses the new rate; trailing yield still includes the earlier smaller payments.";
  return o;
}
function bb10Financials(body) {
  if (!body || typeof body !== "object" || body.bb10Done) return body;
  var out = Object.assign({}, body), hidden = [], notes = [], src = {};
  var sym = String(out.symbol || "").toUpperCase(), ev = bb10EvFresh(sym);
  var val = out.valuation && typeof out.valuation === "object" ? Object.assign({}, out.valuation) : null;
  var met = out.metrics && typeof out.metrics === "object" ? Object.assign({}, out.metrics) : null;
  var fin = out.financials && typeof out.financials === "object" ? Object.assign({}, out.financials) : null;
  if (fin) { bb10EpsRows(fin, ev, notes); fin.epsBasis = "GAAP diluted EPS as filed with the SEC (EDGAR XBRL); rows restated or hidden where a stock split changes the share count"; if (notes.length) fin.epsNotes = notes.slice(0, 12); out.financials = fin; }
  var ttm = bb10TtmEps(fin);
  if (val) {
    var px = bb10N(val.price), ccyOk = !val.financialCurrency || !val.priceCurrency || val.financialCurrency === val.priceCurrency;
    var yahooPe = bb10N(val.pe);
    if (ttm && px > 0 && ccyOk) {
      val.epsTtm = { value: ttm.value, basis: "GAAP diluted EPS, sum of the last 4 reported quarters", source: "SEC EDGAR (XBRL company facts)", through: ttm.through, quarters: ttm.quarters, currency: val.financialCurrency || val.currency || "USD" };
      if (ttm.value > 0) {
        var pe = px / ttm.value;
        if (yahooPe != null && Math.abs(yahooPe / pe - 1) > 0.03) val.yahooPe = yahooPe;
        val.pe = bb10R(pe, 2);
        val.peBasis = "Price " + bb10R(px, 2) + " (Yahoo Finance) / trailing 12-month GAAP EPS " + ttm.value + " (SEC EDGAR, 4 quarters to " + bb10DayUk(ttm.through) + ")";
      } else { delete val.pe; hidden.push({ field: "pe", reason: "Trailing 12-month GAAP EPS is not positive, so P/E is not meaningful" }); }
    } else if (yahooPe != null) {
      val.peBasis = "Yahoo Finance trailing P/E (EPS basis is Yahoo's; SEC quarterly EPS not available for this listing" + (ccyOk ? "" : " or reported in a different currency") + ")";
    }
    // adjusted (non-GAAP) EPS actuals, kept separate and labelled
    var eh = out.earnings && Array.isArray(out.earnings.history) ? out.earnings.history.filter(function (r) { return bb10N(r.actual) != null; }) : [];
    if (eh.length >= 4) {
      var adj = eh.slice(0, 4).reduce(function (s, r) { return s + Number(r.actual); }, 0);
      val.epsTtmAdjusted = { value: bb10R(adj, 2), basis: "Adjusted (non-GAAP) EPS actuals, last 4 quarters", source: "Yahoo Finance (earnings history)", note: "Differs from GAAP EPS; both are shown with their basis" };
      if (px > 0 && adj > 0 && ccyOk) val.peAdjusted = { value: bb10R(px / adj, 2), basis: "Price / adjusted trailing EPS", source: "Yahoo Finance" };
    }
    // forward P/E: kept only when it reconciles with the sourced next-quarter estimate
    var fpe = bb10N(val.forwardPe), nxt = out.earnings && out.earnings.next ? bb10N(out.earnings.next.estimate) : null;
    if (fpe > 0 && px > 0) {
      var ok = false, why = "";
      if (nxt > 0) {
        var rate = 1, fx = val.fx;
        if (!ccyOk) { rate = fx && bb10N(fx.rate) > 0 && String(fx.pair || "") === String(val.priceCurrency) + String(val.financialCurrency) ? Number(fx.rate) : null; }
        if (rate) {
          var impl = px / fpe, ann = 4 * nxt / rate;
          ok = bb10Within(impl, ann, 0.75, 1.25);
          if (!ok) why = "Yahoo's forward P/E implies forward EPS of " + bb10R(impl, 2) + ", but the next-quarter consensus EPS of " + bb10R(nxt, 3) + " annualises to " + bb10R(ann, 2) + ". The two bases do not match, so the forward P/E is not shown.";
        } else why = "Forward EPS currency cannot be matched to the price currency, so the forward P/E is not shown.";
      } else why = "No sourced forward EPS estimate to check it against, so the forward P/E is not shown.";
      if (!ok) { delete val.forwardPe; delete val.forwardBasis; hidden.push({ field: "forwardPe", reason: why }); }
      else val.forwardCheck = "Consistent (within 25%) with 4 x next-quarter consensus EPS " + bb10R(nxt, 3) + " (Yahoo Finance)";
    }
    // dividends
    var dv = bb10Dividend(ev, val, hidden), yy = bb10N(val.divYield);
    if (dv) {
      val.dividend = dv;
      if (dv.paysDividend) {
        if (yy != null && Math.abs(yy / dv.forwardYield - 1) <= 0.12) val.divYieldBasis = "Forward yield: latest dividend x " + dv.payments12m + " payments a year / price";
        else if (yy != null && Math.abs(yy / dv.trailingYield - 1) <= 0.12) val.divYieldBasis = "Trailing 12-month yield (sum of dividends paid / price)";
        else { if (yy != null) val.yahooDivYield = yy; val.divYield = dv.forwardYield; val.divYieldBasis = "Forward yield: latest dividend x " + dv.payments12m + " payments a year / price (computed from Yahoo Finance dividend history)"; }
      } else if (yy != null) { delete val.divYield; hidden.push({ field: "divYield", reason: "Yahoo reports a yield but no dividend was paid in the last 12 months" }); }
    } else if (yy != null) val.divYieldBasis = "Yahoo Finance dividend yield (basis not itemised)";
    // market cap with the right currency symbol
    var mcc = val.marketCapCurrency || val.currency || val.priceCurrency || "USD";
    if (bb10N(val.marketCap) > 0) val = bb10CapFields(val, mcc);
    var S = { price: "Yahoo Finance (chart)", pe: val.peBasis ? val.peBasis : "Yahoo Finance", forwardPe: "Yahoo Finance forward P/E, checked against consensus EPS", ps: "Yahoo Finance", pb: "Yahoo Finance", evEbitda: "Yahoo Finance", marketCap: "Yahoo Finance", divYield: val.divYieldBasis || "Yahoo Finance", beta: "Yahoo Finance (5-year monthly beta vs the S&P 500)", profitMargin: "Yahoo Finance (financialData)", revenueGrowth: "Yahoo Finance (financialData, year on year)", epsTtm: "SEC EDGAR", epsTtmAdjusted: "Yahoo Finance (earnings history)" };
    Object.keys(S).forEach(function (k) { if (val[k] != null && typeof val[k] !== "object" || (k === "epsTtm" || k === "epsTtmAdjusted") && val[k]) src[k] = S[k]; });
    val.sources = src;
    if (hidden.length) val.hidden = hidden;
    out.valuation = val;
  }
  if (met) {
    if (val) {
      if (val.pe != null) met.peRatio = val.pe; else delete met.peRatio;
      if (val.forwardPe != null) met.forwardPE = val.forwardPe; else delete met.forwardPE;
      if (val.divYield != null) met.dividendYield = val.divYield; else delete met.dividendYield;
      if (val.marketCapText) { met.marketCapText = val.marketCapText; met.marketCapCurrency = val.marketCapCurrency; }
      met.sources = src;
    }
    out.metrics = met;
  }
  if (out.earnings && typeof out.earnings === "object") {
    out.earnings = Object.assign({}, out.earnings, { basis: "Adjusted (non-GAAP) EPS actuals and consensus estimates, Yahoo Finance. These differ from GAAP EPS in the SEC filings." });
  }
  if (out.history && Array.isArray(out.history) && out.earnings) out.historyBasis = "Adjusted (non-GAAP) EPS, Yahoo Finance";
  try {
    var pr = bb8oProfiles.get(sym), ab = pr && pr.value && pr.value.about ? String(pr.value.about).trim() : "";
    if (ab) { out.about = bb10About(ab); out.aboutSource = "Yahoo Finance (company profile)"; }
  } catch (e) {}
  if (hidden.length) out.hidden = hidden;
  out.bb10Done = true;
  out.fieldSources = src;
  return out;
}
function bb10About(t) {
  t = String(t || "").replace(/\s+/g, " ").trim();
  if (t.length <= 320) return t;
  var cut = t.slice(0, 320), i = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("; "));
  return i > 80 ? cut.slice(0, i + 1) : cut.replace(/\s+\S*$/, "") + "\u2026";
}

// ── /api/desk-quotes: sourced desk quotes, never "no price" / "null" strings ──
var BB10_DESK_MAP = { TNX: "^TNX", US10Y: "^TNX", DXY: "DX-Y.NYB", VIX: "^VIX", XAU: "GC=F", GOLD: "GC=F", WTI: "CL=F", BRENT: "BZ=F", SPX: "^GSPC", NDX: "^NDX", DJIA: "^DJI", FTSE: "^FTSE", DAX: "^GDAXI", N225: "^N225", HSI: "^HSI" };
var BB10_DESK_LABEL = { "^TNX": "US 10-year yield (^TNX)", "DX-Y.NYB": "US Dollar Index (ICE, Yahoo DX-Y.NYB)", "GC=F": "Gold futures (GC=F, delayed 10 min)", "^VIX": "VIX (CBOE)" };
function bb10DeskSym(tk) {
  var t = String(tk || "").trim().toUpperCase();
  if (!/^[A-Z0-9^][A-Z0-9.^=\/-]{0,14}$/.test(t)) return "";
  if (BB10_DESK_MAP[t]) return BB10_DESK_MAP[t];
  if (BB10_CB_COINS[t]) return t + "-USD";
  return t.replace("/", "-");
}
function bb10DeskOne(tk, sym, row) {
  if (!row || typeof row !== "object" || !(bb10N(row.p) > 0)) return null;
  var r = row, coin = bb10CoinOf(sym);
  if (coin) r = bb10CryptoRow(row, sym);
  else if (sym === "^TNX") r = bb10YieldRow(row);
  var c = bb10N(r.c != null ? r.c : r.changePct), ts = bb10N(row.ts) != null ? (Number(row.ts) < 1e12 ? Number(row.ts) * 1000 : Number(row.ts)) : null;
  var o = {
    ticker: tk, symbol: sym, label: BB10_DESK_LABEL[sym] || row.name || tk,
    price: bb10R(row.p, Number(row.p) < 10 ? 4 : 2), currency: row.currency || null,
    changePct: c != null ? bb10R(c, 4) : null,
    changeBasis: r.changeBasis || (row.basis === "previous_close" ? "previous close" : (row.basis || null)),
    baselinePrice: bb10N(r.baselinePrice != null ? r.baselinePrice : (r.prev != null ? r.prev : r.prevClose)),
    source: r.changeSource || "Yahoo Finance (" + sym + ")", asOf: ts ? bb10Iso(ts) : null, asOfUk: ts ? bb10Uk(ts) : null,
    status: row.status || null, delayMin: bb10N(row.delayMin)
  };
  if (sym === "^TNX") { o.unit = "percent"; o.value = r.value; o.changePp = r.changePp != null ? r.changePp : null; o.currency = null; }
  else if (/^\^/.test(sym) || sym === "DX-Y.NYB") { o.unit = "index points"; }
  else o.unit = o.currency || null;
  if (sym === "GC=F") { o.instrument = "futures"; o.note = "Gold futures (COMEX), not spot. Spot has no previous close in the free feed."; }
  if (coin && r.changeBasisLabel) o.changeBasisLabel = r.changeBasisLabel;
  if (row.note) o.note = o.note ? o.note + " " + row.note : row.note;
  return o;
}
async function bb10DeskRoute(req, res, url) {
  var addr = bb10Addr(req);
  if (typeof yahooRateLimiter === "object" && yahooRateLimiter && !yahooRateLimiter.allow(addr)) return json(res, 429, { error: "Too many requests." });
  var raw = String(url.searchParams.get("symbols") || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean).slice(0, 20);
  if (!raw.length) return json(res, 400, { error: "Pass symbols=TNX,DXY,XAU,BTC (up to 20)." });
  var pairs = [], bad = [];
  raw.forEach(function (tk) { var s = bb10DeskSym(tk); if (s) pairs.push([tk.toUpperCase(), s]); else bad.push({ ticker: tk.slice(0, 20), reason: "invalid symbol" }); });
  var syms = Array.from(new Set(pairs.map(function (p) { return p[1]; })));
  var rows = {}, down = false;
  try { await bb10CryptoLoad(syms.map(bb10CoinOf).filter(Boolean)); } catch (e) {}
  try { rows = (await yahooQuote(syms)) || {}; } catch (e) { rows = {}; down = true; }
  var quotes = {}, missing = bad.slice(), wantBeta = url.searchParams.get("beta") === "1", now = Date.now();
  for (var i = 0; i < pairs.length; i++) {
    var tk = pairs[i][0], sym = pairs[i][1], q = bb10DeskOne(tk, sym, rows[sym]);
    if (!q) { missing.push({ ticker: tk, symbol: sym, reason: down ? "Yahoo Finance quote feed unavailable" : "no quote returned by Yahoo Finance" }); continue; }
    if (wantBeta && /^[A-Z0-9]{1,6}(?:\.[A-Z]{1,2})?$/.test(sym) && typeof bb5LoadBeta === "function") {
      try {
        var b = await Promise.race([bb5LoadBeta(sym), new Promise(function (ok) { setTimeout(function () { ok(null); }, 3500); })]);
        if (b && bb10N(b.beta) != null) q.beta = { value: bb10R(b.beta, 3), source: "Yahoo Finance (published beta)", asOf: b.asOf || null };
      } catch (e) {}
    }
    quotes[tk] = q;
  }
  return json(res, 200, { asOf: bb10Iso(now), asOfUk: bb10Uk(now), timezone: "Europe/London", quotes: quotes, missing: missing, note: "Missing symbols are listed in missing[]; no quote is ever returned as 'no price' or 'null'. beta appears only when Yahoo publishes one (pass beta=1)." });
}

// ── hook helpers ──
function bb10Profile(p) {
  if (!p || typeof p !== "object" || !p.asset || typeof p.asset !== "object") return p;
  var th = String(p.asset.th || "");
  if (th && !/Prices stream from Yahoo|Source: the desk instrument table|\bis an? (?:Stock|ETF|FX|Crypto|Index|Commodity|Future)s? listed on\b/i.test(th)) return p;
  var ab = p.about ? bb10About(p.about) : "";
  var a = Object.assign({}, p.asset, { th: ab });
  if (ab) a.thSource = "Yahoo Finance (company profile)"; else delete a.thSource;
  return Object.assign({}, p, { asset: a });
}
function bb10GoldQuoteMeta(st, o) {
  try {
    if (!o || typeof o !== "object") return o;
    if (!bb8rGoldSym(bb8rSubjectSym(st))) return o;
    if (bb8rSpotQuote(st)) return o;
    if (!/gold spot/i.test(String(o.label || "")) && !/gold spot/i.test(String(o.name || ""))) return o;
    var f = Object.assign({}, o);
    f.symbol = "GC=F"; f.label = "Gold futures (GC=F, delayed 10 min)"; f.name = f.label;
    f.instrument = "futures"; f.spotAvailable = false;
    f.source = "Yahoo Finance"; f.feed = "Yahoo Finance GC=F (COMEX gold futures, delayed 10 min)";
    f.note = "Gold spot was not available for this answer, so the futures price is shown and labelled as futures.";
    f.quoteLine = bb8rQuoteLine(f);
    return f;
  } catch (e) { return o; }
}
function bb10Shape(res, status, body) {
  var path = res && res.bb8oPath;
  if (!path || !body || typeof body !== "object" || status !== 200) return body;
  if (BB10_ROW_ROUTES[path]) {
    if (Array.isArray(body)) return body;
    var out = bb10Rows(body);
    if (out && typeof out === "object" && out.quotes && typeof out.quotes === "object") { var q2 = bb10Rows(out.quotes); if (q2 !== out.quotes) out = Object.assign({}, out, { quotes: q2 }); }
    if (path === "/api/market-reference-quotes") {
      out = Object.assign({}, out);
      var us = bb10Us10y(res.bb10Tnx, Date.now());
      if (us) out.US10Y = us;
      try { out.sessionSummary = bb10Clone(bb10Sessions(Date.now())); } catch (e) {}
    }
    return bb10Dedupe(bb10Clone(out), 0);
  }
  if (path === "/api/coingecko") return bb10CgBody(body);
  if (path === "/api/financials") return bb10Financials(body);
  if (path === "/api/brief") {
    var row = bb8rRegimeRow();
    if (!row) return body;
    var b = Object.assign({}, body);
    try { b = bb10Clone(b); bb10RegimeWalk(b, row, 0); } catch (e) {}
    b.regime = bb10RegimePublic(row);
    return b;
  }
  return body;
}
var BB10_ROW_ROUTES = { "/api/yahoo-quote": 1, "/api/market-reference-quotes": 1, "/api/ext-hours": 1, "/api/spot-energy": 1, "/api/twelve-data-quote": 1, "/api/finnhub": 1 };
var BB10_REG_PATHS = { "/api/brief": 1, "/api/chat": 1, "/api/lenses": 1, "/api/intelligence": 1, "/api/regime-fit": 1, "/api/market-reference-quotes": 1 };
async function bb10Withtimeout(p, ms) { return Promise.race([p, new Promise(function (ok) { setTimeout(function () { ok(null); }, ms); })]); }

// ── bb10 hooks: rebinding wrappers. Each wrapper falls back to the previous function on any error. ──
function bb10Preamble(req, res) {
  try {
    if (typeof bb5bEarly === "function" && bb5bEarly(req, res)) return true;
    if (typeof writeCanonicalRedirect === "function" && writeCanonicalRedirect(req, res)) return true;
    if (typeof attachSecurityHeaders === "function") attachSecurityHeaders(res);
    if (typeof writeCanonicalHostRedirect === "function" && writeCanonicalHostRedirect(req, res)) return true;
    if (typeof rt20sWrapResponse === "function") rt20sWrapResponse(req, res);
  } catch (e) {}
  return false;
}
async function bb10Prefetch(path, url, req, res) {
  var sp = url.searchParams;
  if (path === "/api/yahoo-quote") {
    var coins = bb10CoinsIn(sp.get("symbols") || "");
    if (coins.length) await bb10CryptoLoad(coins);
    if (/(^|,)\s*\^TNX\s*(,|$)/i.test(sp.get("symbols") || "")) { /* row shaping needs no extra data */ }
  } else if (path === "/api/coingecko") {
    var cp = String(sp.get("path") || ""), list = ["BTC"];
    if (/coins\/markets/.test(cp)) list = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "LTC", "DOT", "BCH", "ATOM"];
    else {
      var ids = /[?&]ids=([^&]+)/.exec(cp);
      if (ids) { list = decodeURIComponent(ids[1]).split(",").map(function (i) { return BB10_CG_ID[i.trim().toLowerCase()]; }).filter(Boolean); }
      var cid = /\/coins\/([a-z0-9-]+)/.exec(cp);
      if (cid && BB10_CG_ID[cid[1]]) list.push(BB10_CG_ID[cid[1]]);
    }
    await bb10CryptoLoad(list);
  } else if (path === "/api/market-reference-quotes") {
    await bb10CryptoLoad(["BTC"]);
    try { var t = await bb10Withtimeout(yahooQuote(["^TNX"]), 4000); res.bb10Tnx = t && t["^TNX"] ? t["^TNX"] : null; } catch (e) { res.bb10Tnx = null; }
  } else if (path === "/api/financials") {
    var sym = String(sp.get("symbol") || sp.get("ticker") || "").trim().toUpperCase();
    if (/^[A-Z0-9^][A-Z0-9.^=-]{0,14}$/.test(sym)) {
      await bb10Withtimeout(bb10EventsLoad(sym).catch(function () { return null; }), 6000);
      if (typeof bb8oProfile === "function") await bb10Withtimeout(Promise.resolve(bb8oProfile(sym)).catch(function () { return null; }), 4000);
    }
  }
  if (BB10_REG_PATHS[path]) await bb10Withtimeout(bb10RegimeEnsure().catch(function () { return null; }), 8000);
}
try {
  bb10AcademySetup();

  // (f) one regime: computed once, never flipped by a thin recompute, enriched public object everywhere
  var bb10Mood0 = bb3Mood;
  bb3Mood = function (m) {
    try {
      if (bb8rRegimeRow()) return bb10Mood0.apply(this, arguments);
      var now = Date.now(), a = bb10MoodArgs(m);
      if (a.info.thin && bb10Good && bb10Good.row && now - bb10Good.row.asOf < BB10_REG_KEEP_MS) {
        bb8rReg = { at: now - BB8R_REGIME_MS + BB10_REG_RETRY_MS, row: Object.assign({}, bb10Good.row, { bb10Thin: true, bb10Stale: true, bb10CheckedAt: now, bb10Inputs: a.info }) };
        return bb8rReg.row.mood;
      }
      var mood = bb10Mood0.call(this, a.m), row = bb8rReg && bb8rReg.row;
      if (row && row.mood && mood && row.mood.score === Number(mood.score) && row.asOf >= now - 5000) {
        row.bb10Inputs = a.info; row.bb10Thin = a.info.thin; row.bb10Stale = false; row.bb10CheckedAt = now;
        if (!a.info.thin) bb10Good = { row: Object.assign({}, row) };
      }
      return mood;
    } catch (e) { return bb10Mood0.apply(this, arguments); }
  };
  bb8rRegimePublic = function (row) { try { return bb10RegimePublic(row); } catch (e) { return bb10RegPub0 ? bb10RegPub0(row) : null; } };
  var bb10Stamp0 = bb8rStampRegime;
  bb8rStampRegime = function (ctx) {
    var r = bb10Stamp0.apply(this, arguments);
    try {
      var row = bb8rRegimeRow();
      if (ctx && row) {
        ctx.regime = bb10RegimePublic(row);
        if (row.bb10Stale) (ctx.facts || []).forEach(function (f) { if (f && f.id === "regime") f.text = bb10RegimeText(row); });
      }
    } catch (e) {}
    return r;
  };

  // (c) a missing change figure is null, never 0 / "unchanged"
  var bb10Pack0 = bb8eMovePack;
  bb8eMovePack = async function (base) {
    var p = await bb10Pack0.apply(this, arguments);
    try {
      if (!p || !p.q) return p;
      if (!bb10Has(p.q.c)) return null;
      if (p.bench && !bb10Has(p.bench.q && p.bench.q.c)) p.bench = null;
      if (p.sector && !bb10Has(p.sector.q && p.sector.q.c)) p.sector = null;
    } catch (e) {}
    return p;
  };
  var bb10Verb0 = bb8eVerb;
  bb8eVerb = function (c, closed) { if (!bb10Has(c)) return BB10_NOCHG; return bb10Verb0.apply(this, arguments); };
  var bb10QVerb0 = bb8qVerb;
  bb8qVerb = function (pct) { if (!bb10Has(pct)) return BB10_NOCHG; return bb10QVerb0.apply(this, arguments); };
  var bb10UpDown0 = bb8oUpDown;
  bb8oUpDown = function (n) { if (!bb10Has(n)) return "has no change figure available"; return bb10UpDown0.apply(this, arguments); };

  // (g) the Ask footer chip says what it is
  var bb10QM0 = bb8rQuoteMeta;
  bb8rQuoteMeta = function (st, prior) { var o = bb10QM0.apply(this, arguments); return bb10GoldQuoteMeta(st, o); };

  // (d) asset tags follow the headline subject
  var bb10Why0 = _rt48bWhy;
  _rt48bWhy = function (x) { var g = bb10GoldGuard(x); return g ? g : bb10Why0.apply(this, arguments); };
  var bb10Fb0 = _bb4dFallback;
  _bb4dFallback = function () { var f = bb10Fallback(); return f || bb10Fb0.apply(this, arguments); };

  // profile text: sourced company description or nothing
  var bb10PF0 = bb8oProfileFrom;
  bb8oProfileFrom = function () { var p = bb10PF0.apply(this, arguments); try { return bb10Profile(p); } catch (e) { return p; } };

  // response shaping runs last
  var bb10Shape0 = bb8oShape;
  bb8oShape = function (res, status, body) {
    var out = bb10Shape0.apply(this, arguments);
    try { return bb10Shape(res, status, out); } catch (e) { return out; }
  };

  // regime strings echoed back from the client (brief context, chat history) are rewritten to the server's
  var bb10Read0 = readBody;
  readBody = async function (req) {
    var b = await bb10Read0.apply(this, arguments);
    try {
      if (b && typeof b === "object" && /^\/api\/(?:brief|chat|lenses|intelligence)(?:[?\/]|$)/.test(String(req && req.url || ""))) {
        var row = bb8rRegimeRow();
        if (row) bb10RegimeWalk(b, row, 0);
      }
    } catch (e) {}
    return b;
  };

  var bb10Handle0 = handle;
  handle = async function (req, res) {
    var url = null;
    try { url = new URL(req.url || "/", "http://localhost"); } catch (e) { return bb10Handle0.apply(this, arguments); }
    var path = url.pathname, get = req.method === "GET";
    try {
      if (get && (path === "/api/regime" || path === "/api/session-summary" || path === "/api/desk-quotes")) {
        if (bb10Preamble(req, res)) return;
        res.setHeader("Cache-Control", "no-store");
        if (path === "/api/regime") return await bb10RegimeRoute(req, res);
        if (path === "/api/session-summary") return await bb10SessionRoute(req, res);
        return await bb10DeskRoute(req, res, url);
      }
      if (get || req.method === "POST") await bb10Prefetch(path, url, req, res);
    } catch (e) { console.warn("bb10 prefetch", e && e.message); }
    return bb10Handle0.apply(this, arguments);
  };
} catch (e) { console.warn("bb10 hooks skipped", e && e.message); }
'''

ANCHOR = "// BB8R_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb9a live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10 already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
