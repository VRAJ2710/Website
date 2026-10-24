#!/usr/bin/env python3
"""bb10b: QA chat79 server fixes (regime available:false + arrays, one gold displayChange, one-snapshot crypto + Pulse text,
academy non-US bond guard). Server-only, anchor-based, no timers/tables/secrets.
Usage: python3 patch_bb10b.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
BASE_MD5 = "56ebb9729fc8866d1be6488f244f550e"
MARK = "// ── bb10b:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''// ── bb10b: QA chat79 retest fixes. (2) /api/regime never serves a loading or placeholder reading and always carries overweight[] /
// underweight[]; (3) ONE gold displayChange with its basis label; (4) crypto price + change + text from one Coinbase snapshot;
// (5) asset tags follow the headline subject (India / non-US bond guard, null asset for untagged items). Server-only, in-request
// only: no timers, no tables, no secrets, no paid feeds. Every new top-level name starts with bb10b.
// BB10B_JS
var BB10B_REG_RETRY_MS = 20 * 1000;
var BB10B_GOLD_KEEP_MS = 90 * 1000;
var BB10B_DEMOTE_MS = 36 * 3600 * 1000;
var BB10B_GOLD_LABEL = "Gold futures (GC=F, delayed 10 min)";
var bb10bRegTry = 0;
var bb10bGoldMem = { dc: null, at: 0 };
var bb10bDemoted = new Map();

// ── (2) regime: a real reading with arrays, or available:false with empty arrays ──
// The three score bands are the ones the dashboard already uses (>=60, >=45, below). They are our own display themes, not advice.
function bb10bThemes(score) {
  var s = Number(score);
  if (!isFinite(s)) return { ow: [], uw: [], neu: [] };
  if (s >= 60) return { ow: ["Cyclicals", "Tech / AI", "Crypto"], uw: ["Long-duration bonds", "Defensive staples"], neu: [] };
  if (s >= 45) return { ow: ["Quality compounders", "Energy", "Gold"], uw: ["High-beta growth", "Unprofitable tech"], neu: ["Healthcare", "Financials"] };
  return { ow: ["Gold", "Cash / T-bills", "Defensive sectors"], uw: ["Small caps", "Crypto", "High-beta"], neu: [] };
}
function bb10bRegimeFull(p) {
  if (!p || typeof p !== "object") return p;
  var o = Object.assign({}, p), score = Number(o.score), lab = String(o.label || o.regime || "");
  var t = bb10bThemes(score);
  o.available = true;
  o.overweight = Array.isArray(o.overweight) ? o.overweight : t.ow.slice();
  o.underweight = Array.isArray(o.underweight) ? o.underweight : t.uw.slice();
  o.neutral = Array.isArray(o.neutral) ? o.neutral : t.neu.slice();
  o.narrative = typeof o.narrative === "string" && o.narrative ? o.narrative : (lab + " \u00b7 Regime score " + (isFinite(score) ? score : "") + "/100.");
  o.themeBasis = "Themes follow the score band (60 and above, 45 to 59, below 45). They describe the regime and are our own display rule, not advice.";
  return o;
}
function bb10bUnavailable(why) {
  var now = Date.now();
  return {
    available: false, regime: null, label: null, score: null, overweight: [], underweight: [], neutral: [], narrative: "",
    reason: why || "No full regime reading yet.",
    note: "The market mood needs the volatility index and the S&P 500 move. Until both are in, no regime is shown instead of a placeholder. Try again in a minute.",
    retryAfterSec: 30, asOf: bb10Iso(now), asOfUk: bb10Uk(now), source: "Dispatch regime model (ours)"
  };
}
// A provisional reading (thin inputs, no previous full reading) is not a reading: it is not served anywhere.
var bb10bRegPub0 = bb10RegimePublic;
function bb10bRegimePublicV(row) {
  var p = bb10bRegPub0.apply(this, arguments);
  if (!p) return null;
  if (p.thin === true && p.stale !== true) return null;
  var s = Number(p.score), lab = String(p.label || p.regime || "");
  if (!isFinite(s) || !lab || /load|placeholder|cautious/i.test(lab)) return null;
  return bb10bRegimeFull(p);
}
var bb10bEns0 = bb10RegimeEnsure;
async function bb10bRegimeEnsureV() {
  var row = await bb10bEns0.apply(this, arguments);
  try {
    if (!bb10RegimePublic(row) && Date.now() - bb10bRegTry > BB10B_REG_RETRY_MS) {
      bb10bRegTry = Date.now();
      bb8rReg = null;
      row = (await bb10Withtimeout(bb10bEns0().catch(function () { return null; }), 6000)) || row;
    }
  } catch (e) {}
  return row;
}
async function bb10bRegimeRouteV(req, res) {
  var row = await bb10RegimeEnsure();
  var p = bb10RegimePublic(row);
  if (!p) return json(res, 200, bb10bUnavailable("Regime inputs are not all in yet."));
  return json(res, 200, Object.assign({ available: true }, p));
}
var BB10B_LOAD_RE = /[^.!?\n]*\b(?:inputs?|regime|data)\b[^.!?\n]*\bstill loading\b[^.!?\n]*[.!?]?[ \t]*/gi;
function bb10bStripLoading(o, depth) {
  if (depth > 6 || !o || typeof o !== "object") return;
  Object.keys(o).forEach(function (k) {
    var v = o[k];
    if (typeof v === "string") { if (/still loading/i.test(v)) o[k] = v.replace(BB10B_LOAD_RE, "").trim(); }
    else if (Array.isArray(v)) {
      for (var i = v.length - 1; i >= 0; i--) {
        if (typeof v[i] === "string" && /still loading/i.test(v[i])) { var n = v[i].replace(BB10B_LOAD_RE, "").trim(); if (n) v[i] = n; else v.splice(i, 1); }
        else if (v[i] && typeof v[i] === "object") bb10bStripLoading(v[i], depth + 1);
      }
    } else if (v && typeof v === "object") bb10bStripLoading(v, depth + 1);
  });
}
var BB10B_REG_SHAPE = { "/api/brief": 1, "/api/market-reference-quotes": 1, "/api/lenses": 1, "/api/intelligence": 1, "/api/regime-fit": 1 };
function bb10bShape(res, status, body) {
  var path = res && res.bb8oPath;
  if (!path || !body || typeof body !== "object" || Array.isArray(body)) return body;
  if (path === "/api/academy-daily") return bb10bAcademyShape(body);
  if (!BB10B_REG_SHAPE[path]) return body;
  var out = body, r = body.regime, real = null;
  try { real = bb10RegimePublic(); } catch (e) { real = null; }
  if (r && typeof r === "object" && !Array.isArray(r.overweight)) {
    out = Object.assign({}, body); out.regime = real || bb10bUnavailable("No full regime reading yet.");
  } else if (!r && (path === "/api/brief" || path === "/api/market-reference-quotes")) {
    out = Object.assign({}, body); out.regime = real || bb10bUnavailable("No full regime reading yet.");
  }
  if (path === "/api/brief") {
    try { out = bb10Clone(out); bb10bStripLoading(out, 0); } catch (e) {}
  }
  return out;
}

// ── (3) gold: ONE displayChange, with its basis label, from ONE function ──
// Gold spot has no previous close in the free feed, so the only change we can source is the COMEX futures one (GC=F, Yahoo).
// Every route that carries a gold change (yahoo-quote, market-reference-quotes, ext-hours, twelve-data-quote, finnhub, desk-quotes,
// the Ask quote chip) is routed through bb10bGoldRow, so a stale spot change can never replace it. A futures change read in the
// last 90 seconds beats a row's own spot change.
function bb10bSign(n) { return n > 0 ? "+" : n < 0 ? "\u2212" : ""; }
function bb10bFutFrom(v, k) {
  if (!v || typeof v !== "object") return null;
  var sym = String(v.symbol || v.feedSymbol || k || "").toUpperCase();
  var f = v.futuresChange && typeof v.futuresChange === "object" ? v.futuresChange : null, pct = f ? bb10N(f.changePct) : null;
  if (f && pct != null) {
    return { pct: pct, symbol: f.symbol || "GC=F", label: f.label || BB10B_GOLD_LABEL, price: bb10N(f.price), prevClose: bb10N(f.prevClose), change: bb10N(f.change), source: f.source || "Yahoo Finance", asOf: f.asOf || null, asOfUk: f.asOfUk || null, text: f.text || null };
  }
  if (sym === "GC=F" || /futures/i.test(String(v.instrument || ""))) {
    var c = bb10N(v.c != null ? v.c : (v.changePct != null ? v.changePct : v.changeDisplayPct));
    if (c == null || v.changeAvailable === false) return null;
    var ts = bb10N(v.ts), ms = ts != null ? (ts < 1e12 ? ts * 1000 : ts) : null;
    return { pct: c, symbol: "GC=F", label: BB10B_GOLD_LABEL, price: bb10N(v.p != null ? v.p : v.price), prevClose: bb10N(v.prev != null ? v.prev : v.prevClose), change: bb10N(v.change), source: "Yahoo Finance", asOf: v.asOf || (ms ? bb10Iso(ms) : null), asOfUk: v.asOfUk || (ms ? bb10Uk(ms) : null), text: null };
  }
  return null;
}
function bb10bGoldDC(f) {
  var pct = bb10R(f.pct, 2);
  return {
    pct: pct, instrument: "futures", symbol: f.symbol, label: f.label, basis: "previous_close", price: f.price, prevClose: f.prevClose, change: f.change,
    source: f.source, asOf: f.asOf, asOfUk: f.asOfUk,
    text: f.text || ("gold futures (GC=F) " + bb10bSign(pct) + Math.abs(pct).toFixed(2) + "% today"),
    note: "Gold spot has no previous close in the free feed, so the change shown is the change in gold futures (GC=F). It is not spot's change."
  };
}
function bb10bGoldChange(v, k) {
  var f = bb10bFutFrom(v, k), now = Date.now(), m = bb10bGoldMem;
  if (f) {
    var dc = bb10bGoldDC(f);
    // a futures change fetched in this request window and not older than this row's is the one everybody shows
    if (m.dc && now - m.at < 60 * 1000 && dc.asOf && m.dc.asOf && String(m.dc.asOf) > String(dc.asOf)) return Object.assign({}, m.dc);
    bb10bGoldMem = { dc: dc, at: now };
    return dc;
  }
  var own = bb10N(v && (v.c != null ? v.c : v.changePct));
  // the row's own spot change (no futures on this row) never overrides a futures change read within the last 90 seconds
  if (own != null && bb10bGoldMem.dc && now - bb10bGoldMem.at < BB10B_GOLD_KEEP_MS) return Object.assign({}, bb10bGoldMem.dc);
  var c = bb10N(v && (v.c != null ? v.c : v.changePct));
  var sym = String((v && (v.symbol || v.feedSymbol)) || k || "").toUpperCase();
  if (c != null && v.changeAvailable !== false && v.noPrevClose !== true && sym !== "GC=F") {
    return { pct: bb10R(c, 4), instrument: "spot", symbol: "XAU", label: "Gold spot", basis: v.basis || "previous_close", source: v.source || null, asOf: v.asOf || null, asOfUk: v.asOfUk || null, text: null, note: null };
  }
  return null;
}
function bb10bGoldRow(v, k) {
  var o = Object.assign({}, v), dc = bb10bGoldChange(v, k);
  var sym = String(v.symbol || v.feedSymbol || k || "").toUpperCase();
  var spotC = bb10N(v.c != null ? v.c : v.changePct);
  o.displayChange = dc;
  o.changeDisplayPct = dc ? dc.pct : null;
  o.displayChangeBasis = dc ? dc.instrument : null;
  o.displayChangeLabel = dc ? dc.label : null;
  if (dc && dc.instrument === "futures" && sym !== "GC=F") {
    if (spotC != null && spotC !== dc.pct) o.spotChangePct = spotC;
    if (spotC != null) { o.c = dc.pct; o.changePct = dc.pct; o.changeBasis = "futures"; }
  }
  if (!dc) { o.changeNote = o.changeNote || "No gold change figure is available right now. Show a dash."; }
  return o;
}
function bb10bIsGoldKey(k) { return /^(?:XAU|XAUUSD|XAU\/USD|GOLD|GC=F)$/i.test(String(k || "")); }
// one futures read per request window, shared by every gold row on every route (yahooQuote has its own short cache)
async function bb10bGoldLoad() {
  try {
    var t = await bb10Withtimeout(yahooQuote(["GC=F"]), 4000), r = t && t["GC=F"];
    if (r && bb10N(r.p) > 0) bb10bGoldChange(Object.assign({ symbol: "GC=F" }, r), "GC=F");
  } catch (e) {}
}
function bb10bDeskOne(tk, sym, row) {
  var o = bb10bDesk0(tk, sym, row);
  try {
    if (o && sym === "GC=F") {
      var g = bb10bGoldRow(Object.assign({ symbol: "GC=F" }, row), "GC=F");
      o.displayChange = g.displayChange; o.displayChangeBasis = g.displayChangeBasis; o.displayChangeLabel = g.displayChangeLabel; o.changeDisplayPct = g.changeDisplayPct;
    }
  } catch (e) {}
  return o;
}
var bb10bDesk0 = bb10DeskOne;

// ── (4) crypto: price, change, range and the Pulse text from ONE Coinbase snapshot ──
// bb10 already moved the 24h change to Coinbase but left CoinGecko's current_price / high / low / last_updated in the same row, so
// a row mixed two snapshots. Now every CoinGecko-proxy row for a coin Coinbase covers takes price, change, range and timestamp
// from the one Coinbase stats read. Coins Coinbase does not cover keep CoinGecko's own row, labelled as such.
var BB10B_CB_SRC = "Coinbase Exchange public stats";
function bb10bFmtUsd(n) {
  n = Number(n);
  if (!isFinite(n)) return "";
  var d = n >= 100 ? 2 : n >= 1 ? 2 : n >= 0.01 ? 4 : 6;
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: d > 2 ? d : 2, maximumFractionDigits: d });
}
function bb10bSnapRow(h) {
  var pct = bb10R((h.last / h.open - 1) * 100, 4);
  var hi = h.high != null ? Math.max(h.high, h.last) : null, lo = h.low != null ? Math.min(h.low, h.last) : null;
  return { coin: h.coin, symbol: h.coin + "-USD", price: h.last, changePct: pct, change: bb10R(h.last - h.open, 6), open24h: h.open, high24h: hi, low24h: lo, at: h.at, asOf: bb10Iso(h.at), asOfUk: bb10Uk(h.at) };
}
function bb10bCgFix(o, h) {
  var s = bb10bSnapRow(h);
  if (o.current_price != null) o.coingecko_current_price = o.current_price;
  o.current_price = s.price;
  if ("high_24h" in o) { o.coingecko_high_24h = o.high_24h; o.high_24h = s.high24h != null ? s.high24h : o.high_24h; }
  if ("low_24h" in o) { o.coingecko_low_24h = o.low_24h; o.low_24h = s.low24h != null ? s.low24h : o.low_24h; }
  if (o.last_updated != null) o.coingecko_last_updated = o.last_updated;
  o.last_updated = s.asOf;
  o.snapshotAt = s.asOf; o.snapshotAtUk = s.asOfUk;
  o.priceSource = BB10B_CB_SRC + " (" + h.coin + "-USD)";
  o.priceBasis = "last trade";
  return o;
}
var bb10bCg0 = bb10CgBody;
function bb10bCgBodyV(body) {
  var out = bb10bCg0.apply(this, arguments);
  try {
    if (Array.isArray(out)) {
      return out.map(function (r) {
        if (!r || typeof r !== "object") return r;
        var coin = BB10_CG_ID[String(r.id || "")], h = coin ? bb10CbRow(coin) : null;
        if (h && r.changeSource != null) return bb10bCgFix(Object.assign({}, r), h);
        return "current_price" in r ? Object.assign({}, r, { priceSource: "CoinGecko", snapshotAt: r.last_updated || null }) : r;
      });
    }
    if (out && typeof out === "object") {
      var res = null;
      Object.keys(out).forEach(function (id) {
        var coin = BB10_CG_ID[id], h = coin ? bb10CbRow(coin) : null, row = out[id];
        if (!h || !row || typeof row !== "object" || row.changeSource == null) return;
        res = res || Object.assign({}, out);
        var o = Object.assign({}, row);
        if (o.usd != null) o.coingecko_usd = o.usd;
        o.usd = h.last; o.last_updated_at = Math.floor(h.at / 1000);
        o.snapshotAt = bb10Iso(h.at); o.snapshotAtUk = bb10Uk(h.at); o.priceSource = BB10B_CB_SRC + " (" + h.coin + "-USD)";
        res[id] = o;
      });
      return res || out;
    }
  } catch (e) {}
  return out;
}
// Yahoo-style crypto rows (BTC-USD in /api/yahoo-quote etc.): the price comes from the same snapshot as the change
var bb10bCRow0 = bb10CryptoRow;
function bb10bCryptoRowV(v, sym) {
  var o = bb10bCRow0.apply(this, arguments);
  try {
    if (!o || o === v || o.lastTrade == null) return o;
    var coin = bb10CoinOf(sym), h = coin ? bb10CbRow(coin) : null;
    if (!h) return o;
    var n = Object.assign({}, o);
    if ("p" in n) { n.yahooP = n.p; n.p = h.last; }
    if ("price" in n) n.price = h.last;
    n.priceSource = BB10B_CB_SRC + " (" + h.coin + "-USD)"; n.snapshotAt = bb10Iso(h.at); n.snapshotAtUk = bb10Uk(h.at);
    return n;
  } catch (e) { return o; }
}
// GET /api/crypto-snapshot?coins=BTC,ETH,SOL&limit=3 : the rows AND the Pulse sentence, built from the same rows
var BB10B_PULSE_DEFAULT = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA"];
function bb10bPulse(rows, limit) {
  var ok = rows.filter(function (r) { return r.available; });
  if (!ok.length) return { text: "", leaders: [], best: null, worst: null, basis: "24h change, Coinbase Exchange" };
  var lead = ok.slice(0, Math.max(1, Math.min(limit || 3, 6)));
  var bit = function (r) { return r.coin + " " + bb10bFmtUsd(r.price) + " " + bb10bSign(r.changePct) + Math.abs(r.changePct).toFixed(2) + "%"; };
  var sorted = ok.slice().sort(function (a, b) { return b.changePct - a.changePct; });
  var best = sorted[0], worst = sorted[sorted.length - 1];
  var t = "Crypto, 24h on Coinbase: " + lead.map(bit).join(", ") + ".";
  if (ok.length > 1) t += " Strongest " + best.coin + " " + bb10bSign(best.changePct) + Math.abs(best.changePct).toFixed(2) + "%, weakest " + worst.coin + " " + bb10bSign(worst.changePct) + Math.abs(worst.changePct).toFixed(2) + "%.";
  var at = Math.min.apply(null, ok.map(function (r) { return r.at; }));
  t += " As of " + bb10bHm(at) + " UK.";
  return { text: t, leaders: lead.map(function (r) { return r.coin; }), best: best.coin, worst: worst.coin, basis: "24h change, Coinbase Exchange" };
}
function bb10bHm(ms) {
  try { return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms)); } catch (e) { return ""; }
}
async function bb10bCryptoRoute(req, res, url) {
  var addr = bb10Addr(req);
  if (typeof yahooRateLimiter === "object" && yahooRateLimiter && !yahooRateLimiter.allow(addr)) return json(res, 429, { error: "Too many requests." });
  var sp = url.searchParams, raw = String(sp.get("coins") || sp.get("ids") || "");
  var list = raw.split(",").map(function (c) { c = c.trim(); return BB10_CG_ID[c.toLowerCase()] || c.toUpperCase(); }).filter(function (c) { return BB10_CB_COINS[c]; });
  list = Array.from(new Set(list.length ? list : BB10B_PULSE_DEFAULT)).slice(0, 12);
  var limit = Math.max(1, Math.min(parseInt(sp.get("limit") || "3", 10) || 3, 6));
  await bb10CryptoLoad(list);
  var rows = list.map(function (c) {
    var h = bb10CbRow(c);
    if (!h) return { coin: c, symbol: c + "-USD", available: false, price: null, changePct: null, note: "No Coinbase reading for " + c + " right now." };
    var s = bb10bSnapRow(h);
    return Object.assign({ available: true, changeBasis: "rolling 24h", changeBasisLabel: "Rolling 24 hours: latest trade against the price 24 hours earlier (Coinbase Exchange)", source: BB10B_CB_SRC + " (api.exchange.coinbase.com/products/" + c + "-USD/stats)" }, s);
  });
  var ok = rows.filter(function (r) { return r.available; });
  var oldest = ok.length ? Math.min.apply(null, ok.map(function (r) { return r.at; })) : null;
  return json(res, 200, { available: ok.length > 0, rows: rows, pulse: bb10bPulse(rows, limit), snapshotAt: oldest ? bb10Iso(oldest) : null, snapshotAtUk: oldest ? bb10Uk(oldest) : null, note: "Price, change and the Pulse text come from the same rows. The snapshot time is the oldest row's." });
}

// ── (5) Academy: an asset question only when the headline is about that asset ──
// bb9a / bb10 already check that the tagged asset is the headline's own subject. They did not know that "India 40-year bond yield"
// is not a US Treasury story, because the yields pattern matches any "bond yield". This guard rejects a yields tag when the
// headline is about another country's bonds and never names US Treasuries. Rejected items are shown as plain headlines with
// asset:null and no question, so the client contract (all fields present, null) stays safe.
var BB10B_NONUS_RE = /\b(?:india(?:n|'s)?|rbi|reserve bank of india|rupees?|g-?secs?|sensex|nifty|japan(?:ese)?|jgbs?|boj|bank of japan|china|chinese|pboc|yuan|gilts?|u\.?k\.?|britain|british|bank of england|boe|germany|german|bunds?|france|french|oats|italy|italian|btps?|spain|spanish|greece|greek|euro ?zone|euro area|ecb|australia(?:n)?|canada|canadian|brazil(?:ian)?|mexic\w+|turk\w+|south africa\w*|indonesia\w*|korea\w*|russia\w*|ukrain\w*|argentin\w*|pakistan\w*|nigeria\w*|egypt\w*|saudi|emirat\w*|uae)\b/i;
var BB10B_US_TSY_RE = /\b(?:u\.?s\.?|american|united states)\s+(?:\d+-?year\s+|government\s+|sovereign\s+)?(?:treasur|bonds?\b|yields?\b)|\btreasuries\b/i;
function bb10bYieldWhy(x) {
  if (!x || typeof x !== "object" || x.asset !== "yields") return "";
  var h = String(x.h || "");
  var m = BB10B_NONUS_RE.exec(h);
  if (m && !BB10B_US_TSY_RE.test(h)) return "non-us-bond-headline";
  return "";
}
var bb10bWhyPrev = null;
function bb10bWhyV(x) {
  var g = "";
  try { g = bb10bYieldWhy(x); } catch (e) { g = ""; }
  if (g) {
    try {
      var h = String(x.h || "").trim();
      if (h && x.link && x.src) { bb10bDemoted.set(h, { h: h, src: x.src, link: x.link, why: g, at: Date.now() }); if (bb10bDemoted.size > 40) bb10bDemoted.delete(bb10bDemoted.keys().next().value); }
    } catch (e) {}
    return g;
  }
  return bb10bWhyPrev.apply(this, arguments);
}
function bb10bUntagged(h, why) {
  return { h: h.h, src: h.src, link: h.link, asset: null, dir: null, q: null, o: null, a: null, e: null, kind: "news", untagged: true, untaggedReason: why || "The headline is not about one of the assets we ask about, so no asset question is asked." };
}
function bb10bAcademyShape(body) {
  if (!body || !Array.isArray(body.items)) return body;
  var out = Object.assign({}, body), seen = {}, now = Date.now();
  out.items = body.items.map(function (it) {
    if (!it || typeof it !== "object") return it;
    var n = Object.assign({}, it), g = "";
    try { g = bb10bYieldWhy(n); } catch (e) { g = ""; }
    if (g) n = bb10bUntagged(n, "The headline is about another country's bonds, not US Treasury yields, so no asset question is asked.");
    else if (!n.asset) { n.asset = null; n.dir = n.dir == null ? null : n.dir; n.q = null; n.o = null; n.a = null; n.e = null; n.untagged = true; }
    ["asset", "dir", "q", "o", "a", "e"].forEach(function (k) { if (!(k in n) || n[k] === undefined || n[k] === "") n[k] = null; });
    seen[String(n.h || "").trim()] = 1;
    return n;
  });
  // the validity gate dropped a mis-tagged cached item: show its headline untagged so the set keeps its size
  if (out.items.length < 3 && bb10bDemoted.size) {
    var add = [];
    bb10bDemoted.forEach(function (d, k) { if (now - d.at > BB10B_DEMOTE_MS) bb10bDemoted.delete(k); else if (!seen[k]) add.push(d); });
    add.sort(function (a, b) { return b.at - a.at; });
    for (var i = 0; i < add.length && out.items.length < 3; i++) out.items.push(bb10bUntagged(add[i], "The headline is about another country's bonds, not US Treasury yields, so no asset question is asked."));
  }
  return out;
}

// ── bb10b hooks: rebinding wrappers. Each falls back to the previous function on any error. ──
try {
  bb10bWhyPrev = _rt48bWhy;
  // (2) regime
  bb10RegimePublic = bb10bRegimePublicV;
  bb10RegimeEnsure = bb10bRegimeEnsureV;
  bb10RegimeRoute = bb10bRegimeRouteV;
  // (3) gold
  bb10IsGoldKey = bb10bIsGoldKey;
  bb10GoldRow = function (v, k) { try { return bb10bGoldRow(v, k); } catch (e) { return v; } };
  bb10DeskOne = bb10bDeskOne;
  var bb10bQM0 = bb8rQuoteMeta;
  bb8rQuoteMeta = function (st, prior) {
    var o = bb10bQM0.apply(this, arguments);
    try {
      if (o && typeof o === "object" && /^(?:XAU|XAUUSD|XAU\/USD|GOLD|GC=F)$/i.test(String(o.symbol || "")) && (o.c != null || o.changePct != null || o.futuresChange)) {
        var g = bb10bGoldRow(o, o.symbol);
        o.displayChange = g.displayChange; o.displayChangeBasis = g.displayChangeBasis; o.displayChangeLabel = g.displayChangeLabel;
      }
    } catch (e) {}
    return o;
  };
  // (4) crypto
  bb10CgBody = bb10bCgBodyV;
  bb10CryptoRow = bb10bCryptoRowV;
  // (5) academy
  _rt48bWhy = bb10bWhyV;
  // response shaping runs after bb10's
  var bb10bShape0 = bb8oShape;
  bb8oShape = function (res, status, body) {
    var out = bb10bShape0.apply(this, arguments);
    try { return bb10bShape(res, status, out); } catch (e) { return out; }
  };
  var bb10bHandle0 = handle;
  handle = async function (req, res) {
    var url = null;
    try { url = new URL(req.url || "/", "http://localhost"); } catch (e) { return bb10bHandle0.apply(this, arguments); }
    var path = url.pathname;
    try {
      if (req.method === "GET" && path === "/api/crypto-snapshot") {
        if (bb10Preamble(req, res)) return;
        res.setHeader("Cache-Control", "no-store");
        return await bb10bCryptoRoute(req, res, url);
      }
      if ((req.method === "GET" || req.method === "POST") && (BB10_ROW_ROUTES[path] || path === "/api/desk-quotes" || path === "/api/gold-desk")) {
        if (path === "/api/market-reference-quotes" || path === "/api/desk-quotes" || path === "/api/gold-desk" || /XAU|GOLD|GC=F/i.test(url.search)) await bb10bGoldLoad();
      }
    } catch (e) { console.warn("bb10b prefetch", e && e.message); }
    return bb10bHandle0.apply(this, arguments);
  };
} catch (e) { console.warn("bb10b hooks skipped", e && e.message); }
'''

ANCHOR = "// BB10_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10B_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10b.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10b: {f} md5 {m0} lines {raw.count(b'\n')}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10 live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10b already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10b.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
    os.replace(tmp, f); print(f"bb10b: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
sys.exit(main())
