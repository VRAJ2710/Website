#!/usr/bin/env python3
"""patch_bb8o.py — (1) no zero, null or non-finite price on any quote path: last valid close with its real
timestamp and session, flagged fallback; Taiwan listings get the Taipei session. (2) Form 4 trade date falls back
to deemedExecutionDate then periodOfReport (same XML, no extra SEC request); never the filing date. (3) /api/search
returns result[] in the client's shape plus an LSE listing profile (GBp handled); GET /api/listing-profile.
(4) One canonical feed object {v,status,ageSec,asOf,...} on every quote row of every quote route.
(5) GET /api/brief/edition and brief.edition: a stable, request-driven edition, memory only.
Server.js only. Stacked on bb8n (server md5 9b48a917c654891a50e7c7c6bd8c9a49). Appended at the end of the file;
anchors are long-standing declarations only. See docs/bb8o.md.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8o.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "9b48a917c654891a50e7c7c6bd8c9a49",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def show(phase, name, raw):
    digest = hashlib.md5(raw).hexdigest()
    print("bb8o %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def read_bytes(path):
    if not os.path.isfile(path):
        return None
    return open(path, "rb").read()

raw = read_bytes(SRV)
if raw is None:
    die("server.js missing in %s" % D)
v = raw.decode("utf-8").replace("\r\n", "\n")
vcrlf = b"\r\n" in raw
app_before = read_bytes(APP)
idx_before = read_bytes(IDX)

digest = show("before", "server.js", raw)
if digest != EXPECTED_MD5["server.js"]:
    print("WARN md5 server.js: have %s expected %s (anchors still decide)" % (digest, EXPECTED_MD5["server.js"]))
for label, blob in (("app.js", app_before), ("index.html", idx_before)):
    if blob is None:
        print("bb8o before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8o %s untouched" % label)

if "// BB8O_JS" in v:
    print("REFUSE: bb8o already applied")
    sys.exit(0)

REPLACE = [
]
REQUIRED = [
    ("bb8n end marker", "// BB8N_JS_END"),
    ("crypto", 'const crypto = require("crypto");'),
    ("json", "function json(res, status, body, extraHeaders = {}) {"),
    ("handle", "async function handle(req, res) {"),
    ("yahooQuote", "async function yahooQuote(symbols) {"),
    ("fetchYahooQuote", "async function fetchYahooQuote(symbol) {"),
    ("yahooRateLimiter", "const yahooRateLimiter = new FixedWindowRateLimiter("),
    ("rt32Get", "function rt32Get(u, headers) {"),
    ("rt32Crumb", "async function rt32Crumb(force) {"),
    ("RT32_BUA", "const RT32_BUA = "),
    ("_rt48sHeads", "async function _rt48sHeads() {"),
    ("bb5eCanon", "function bb5eCanon(symbol) {"),
    ("bb5eCash", "function bb5eCash(tz, o, c, label, lo, lc) {"),
    ("bb5eSpec", "function bb5eSpec(symbol) {"),
    ("bb5eApply", "function bb5eApply(q, symbol, hints, now) {"),
    ("bb5gSpec", "function bb5gSpec(symbol) {"),
    ("bb7Tag", "function bb7Tag(xml, tag) {"),
    ("bb7Blocks", "function bb7Blocks(xml, tag) {"),
    ("bb7IsoDate", "function bb7IsoDate(value) {"),
    ("bb7ParseForm4", "function bb7ParseForm4(xml, meta) {"),
    ("parseForm4", "function parseForm4(xml, ticker, sourceUrl) {"),
    ("bb8lDay", "function bb8lDay(s, weekday) {"),
    ("bb8lRowDates", "function bb8lRowDates(body) {"),
    ("bb8cUnit", "function bb8cUnit(ccy) {"),
    ("bb8dUk", "function bb8dUk(ms) {"),
]
for a, _b in REPLACE:
    REQUIRED.append(("replace: " + a.strip()[:60], a))
miss = []
for name, anchor in REQUIRED:
    n = v.count(anchor)
    if n != 1:
        miss.append("anchor %s matched %d times (want 1)" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)
print("bb8o anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8o ── No zero or non-finite price on any quote route; insider trade dates never borrow the filing date;
// LSE listing profile on /api/search and /api/listing-profile; one canonical per-symbol feed status; a stable,
// request-driven brief edition. See docs/bb8o.md.
// BB8O_JS
var BB8O_GOOD_MAX = 3000;
var BB8O_HEADS_MS = 5 * 60 * 1000;
var BB8O_DWELL_MS = 30 * 60 * 1000;
var BB8O_AGED_MS = 12 * 3600 * 1000;
var BB8O_PROFILE_MS = 30 * 60 * 1000;
var BB8O_LIVE_SEC = 180;
var BB8O_DELAYED_SEC = 1200;
var bb8oGood = new Map();
var bb8oProfiles = new Map();
var bb8oEd = { cur: null, heads: null, headsAt: 0, pending: null };
var BB8O_ROUTES = { "/api/yahoo-quote": "yahoo", "/api/market-reference-quotes": "reference", "/api/twelve-data-quote": "twelve-data", "/api/finnhub": "finnhub", "/api/spot-energy": "energy" };
var BB8O_TZ = { "Asia/Hong_Kong": "HKT", "Asia/Tokyo": "JST", "Asia/Seoul": "KST", "Asia/Taipei": "Taipei time", "Asia/Kolkata": "IST", "America/New_York": "ET", "America/Chicago": "CT" };
var BB8O_CCY = { GBP: "£", USD: "$", EUR: "€", JPY: "¥", HKD: "HK$", KRW: "₩", INR: "₹", AUD: "A$", TWD: "NT$", CAD: "C$", CHF: "CHF " };
var BB8O_STOP = { with: 1, from: "1", that: 1, this: 1, will: 1, after: 1, over: 1, into: 1, says: 1, said: 1, amid: 1, their: 1, have: 1, more: 1, than: 1, what: 1, when: 1, were: 1, been: 1, about: 1, news: 1, live: 1, could: 1, would: 1, year: 1 };
function bb8oNum(v) { if (v && typeof v === "object" && "raw" in v) v = v.raw; var n = Number(v); return v === null || v === "" || v === undefined || !isFinite(n) ? null : n; }
function bb8oKey(sym) {
  var s = String(sym || "").trim().toUpperCase();
  if (/^[A-Z]{3}\/[A-Z]{3}$/.test(s)) s = s.replace("/", "") + "=X";
  return s;
}
function bb8oTsMs(ts) { var n = Number(ts); if (!isFinite(n) || n <= 0) return null; return n < 1e12 ? n * 1000 : n; }
function bb8oIsRow(q) { return !!q && typeof q === "object" && !Array.isArray(q) && Object.prototype.hasOwnProperty.call(q, "p"); }
function bb8oValid(q) { if (!bb8oIsRow(q) || q.p === null || typeof q.p === "boolean" || q.p === "") return false; var p = Number(q.p); return isFinite(p) && p > 0; }
function bb8oSpec(sym) { try { return typeof bb5gSpec === "function" ? bb5gSpec(sym) : (typeof bb5eSpec === "function" ? bb5eSpec(sym) : null); } catch (e) { return null; } }
function bb8oHm(ms, tz) {
  try { return new Intl.DateTimeFormat("en-GB", { timeZone: tz || "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms)); } catch (e) { return ""; }
}
function bb8oYmd(ms, tz) {
  try { return new Intl.DateTimeFormat("en-CA", { timeZone: tz || "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms)); } catch (e) { return ""; }
}
function bb8oDayLabel(ms, tz) {
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: tz || "Europe/London", weekday: "short", day: "numeric", month: "short" }).formatToParts(new Date(ms)).forEach(function (p) { parts[p.type] = p.value; });
    return parts.weekday + " " + parts.day + " " + parts.month;
  } catch (e) { return ""; }
}
function bb8oOffsetMin(ms, tz) {
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-US", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms)).forEach(function (p) { parts[p.type] = p.value; });
    var asUtc = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour) % 24, Number(parts.minute));
    return Math.round((asUtc - Math.floor(ms / 60000) * 60000) / 60000);
  } catch (e) { return null; }
}
function bb8oTzLabel(ms, tz) {
  if (!tz) return "";
  if (BB8O_TZ[tz]) return BB8O_TZ[tz];
  var off = bb8oOffsetMin(ms, tz);
  if (tz === "Australia/Sydney") return off === 660 ? "AEDT" : "AEST";
  if (tz === "Europe/Berlin" || tz === "Europe/Paris") return off === 120 ? "CEST" : "CET";
  if (off == null) return tz;
  var h = off / 60;
  return "UTC" + (h >= 0 ? "+" : "") + h;
}
function bb8oUk(ms) { return typeof bb8dUk === "function" ? bb8dUk(ms) : bb8oDayLabel(ms) + ", " + bb8oHm(ms) + " UK"; }
// Where a price came from: the venue-local session date and the time in venue time and UK time.
function bb8oSession(sym, tsMs, kind) {
  if (!tsMs) return null;
  var spec = bb8oSpec(sym) || {};
  var tz = spec.tz && spec.tz !== "Europe/London" ? spec.tz : null;
  var local = tz ? bb8oHm(tsMs, tz) + " " + bb8oTzLabel(tsMs, tz) : "";
  var day = bb8oDayLabel(tsMs, tz || "Europe/London");
  var uk = bb8oHm(tsMs) + " UK";
  return {
    kind: kind || "regular close",
    date: bb8oYmd(tsMs, tz || "Europe/London"),
    dayUk: day,
    asOf: new Date(tsMs).toISOString(),
    asOfUk: bb8oUk(tsMs),
    local: local,
    label: (kind || "regular close") + ", " + day + ", " + (local ? local + " (" + uk + ")" : uk)
  };
}
function bb8oRemember(sym, q, src) {
  if (!bb8oValid(q)) return;
  var key = bb8oKey(sym);
  if (!key) return;
  var ms = bb8oTsMs(q.ts);
  var old = bb8oGood.get(key);
  if (old && old.tsMs && ms && ms < old.tsMs) return;
  var prev = bb8oNum(q.prev);
  if (old) bb8oGood.delete(key);
  bb8oGood.set(key, { p: Number(q.p), prev: prev != null && prev > 0 ? prev : null, ts: q.ts, tsMs: ms, currency: q.currency || null, src: src || q.source || "", seen: Date.now() });
  while (bb8oGood.size > BB8O_GOOD_MAX) bb8oGood.delete(bb8oGood.keys().next().value);
}
// Valid price: keep it, but never let a non-finite change or previous close through.
function bb8oTidy(q) {
  var p = Number(q.p), prev = bb8oNum(q.prev), c = bb8oNum(q.c), ch = bb8oNum(q.change), out = q, copy = function () { if (out === q) out = Object.assign({}, q); return out; };
  if (prev == null || prev <= 0) {
    if (q.prev !== null || c !== 0 || ch !== 0 || q.basis !== "none") { copy(); out.prev = null; out.c = 0; out.change = 0; out.basis = "none"; out.changeAvailable = false; }
    return out;
  }
  if (c == null) { copy(); out.c = ((p - prev) / prev) * 100; }
  if (ch == null) { copy(); out.change = p - prev; }
  return out;
}
function bb8oOpen(sym, now) {
  try {
    var spec = bb8oSpec(sym);
    if (!spec || typeof bb5eOpenAt !== "function") return null;
    return !!bb5eOpenAt(spec, new Date(now || Date.now()));
  } catch (e) { return null; }
}
// Zero, null, missing or non-finite price: the last valid close we saw, with its real timestamp, flagged.
function bb8oFromLast(q, sym, last, reason) {
  var out = Object.assign({}, q || {});
  var tsMs = last.tsMs;
  out.p = last.p;
  out.ts = last.ts != null ? last.ts : (tsMs ? Math.floor(tsMs / 1000) : null);
  if (last.prev) { out.prev = last.prev; out.change = last.p - last.prev; out.c = (out.change / last.prev) * 100; out.basis = "previous_close"; }
  else { out.prev = null; out.c = 0; out.change = 0; out.basis = "none"; out.changeAvailable = false; }
  if (!out.currency && last.currency) out.currency = last.currency;
  out.fallback = true;
  out.fallbackReason = reason;
  out.fallbackSource = last.src || "";
  var spec = bb8oSpec(sym) || {};
  var kind = spec.mode === "cash" || spec.mode === "thin" ? "regular close" : "last valid price";
  out.session = bb8oSession(sym, tsMs, kind);
  var open = bb8oOpen(sym);
  if (open) { out.status = "stale"; out.stale = true; }
  out.note = "Last valid " + (kind === "regular close" ? "close" : "price") + (out.session ? " · " + out.session.label : "") + " (live price unavailable)";
  delete out.nextOpen;
  if (!open) { try { if (typeof bb5eApply === "function") { var re = bb5eApply(out, sym); if (re && re.nextOpen) out.nextOpen = re.nextOpen; if (re && re.status) out.status = re.status; } } catch (e) {} out.note = "Last valid " + (kind === "regular close" ? "close" : "price") + (out.session ? " · " + out.session.label : ""); }
  return out;
}
function bb8oReason(q) {
  if (!bb8oIsRow(q) || q.p === null || q.p === undefined) return "missing-price";
  var n = Number(q.p);
  if (!isFinite(n)) return "non-finite-price";
  return n === 0 ? "zero-price" : "invalid-price";
}
// Sync guard for one row: tidy a valid row, fall back from memory, else null (the caller drops the row).
function bb8oFix(q, sym, src) {
  if (bb8oValid(q)) { var t = bb8oTidy(q); bb8oRemember(sym, t, src); return t; }
  var last = bb8oGood.get(bb8oKey(sym));
  return last ? bb8oFromLast(q, sym, last, bb8oReason(q)) : null;
}
// Async guard with one free Yahoo daily chart read when memory has nothing.
async function bb8oChartLast(sym) {
  if (typeof upstream !== "function") return null;
  var d = await (await upstream("https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sym) + "?range=1mo&interval=1d")).json();
  var r = d && d.chart && d.chart.result && d.chart.result[0];
  if (!r) return null;
  var ts = r.timestamp || [], cl = (r.indicators && r.indicators.quote && r.indicators.quote[0] && r.indicators.quote[0].close) || [];
  var i = cl.length - 1;
  while (i >= 0 && !(Number(cl[i]) > 0)) i--;
  if (i < 0) return null;
  var meta = r.meta || {}, spec = bb8oSpec(sym) || {}, tz = spec.tz || meta.exchangeTimezoneName || "Europe/London";
  var barMs = Number(ts[i]) * 1000, rmt = Number(meta.regularMarketTime) * 1000, day = bb8oYmd(barMs, tz);
  var j = i - 1;
  while (j >= 0 && (!(Number(cl[j]) > 0) || bb8oYmd(Number(ts[j]) * 1000, tz) === day)) j--;
  var tsMs = rmt > 0 && bb8oYmd(rmt, tz) === day ? rmt : barMs;
  var r4 = function (x) { return Math.round(Number(x) * 10000) / 10000; };
  return { p: r4(cl[i]), prev: j >= 0 ? r4(cl[j]) : null, ts: Math.floor(tsMs / 1000), tsMs: tsMs, currency: meta.currency || null, src: "yahoo-daily-close", seen: Date.now() };
}
async function bb8oGuardMap(map, src) {
  if (!map || typeof map !== "object" || Array.isArray(map)) return map;
  for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k)) {
    var q = map[k];
    if (!bb8oIsRow(q)) continue;
    var fixed = bb8oFix(q, k, src);
    if (!fixed) {
      try { var last = await bb8oChartLast(k); if (last) { bb8oGood.set(bb8oKey(k), last); fixed = bb8oFromLast(q, k, last, bb8oReason(q)); } } catch (e) {}
    }
    if (fixed) map[k] = fixed; else delete map[k];
  }
  return map;
}
// One status vocabulary for every quote route: live | delayed | stale | closed.
function bb8oFeed(q, sym, src, now) {
  var t = now || Date.now(), tsMs = bb8oTsMs(q.ts), age = tsMs ? Math.max(0, Math.round((t - tsMs) / 1000)) : null;
  var delay = Math.max(0, Math.round(Number(q.delayMin) || 0)), legacy = String(q.status || ""), status, reason;
  var spec = bb8oSpec(bb8oKey(sym)) || {};
  if (legacy === "closed") { status = "closed"; reason = "session-closed"; }
  else if (q.fallback) { status = "stale"; reason = "fallback"; }
  else if (legacy === "quiet") { status = "delayed"; reason = "thin-market"; }
  else if (age == null) { status = "delayed"; reason = "no-timestamp"; }
  else if (age <= delay * 60 + BB8O_LIVE_SEC) { status = delay > 0 ? "delayed" : "live"; reason = delay > 0 ? "exchange-delay" : "fresh"; }
  else if (age <= delay * 60 + BB8O_DELAYED_SEC) { status = "delayed"; reason = "age"; }
  else { status = "stale"; reason = "age"; }
  var sess = tsMs ? bb8oSession(bb8oKey(sym), tsMs, status === "closed" || q.fallback ? (spec.mode === "cash" || spec.mode === "thin" ? "regular close" : "last price") : "live session") : null;
  return {
    v: 1, symbol: bb8oKey(sym), status: status, reason: reason, ageSec: age,
    asOf: tsMs ? new Date(tsMs).toISOString() : null, asOfUk: tsMs ? bb8oUk(tsMs) : null,
    delayMin: delay, source: String(q.source || src || ""), market: spec.label || "",
    sessionDate: sess ? sess.date : null, sessionDayUk: sess ? sess.dayUk : null, sessionLabel: sess && (status === "closed" || q.fallback) ? sess.label : null,
    fallback: !!q.fallback
  };
}
function bb8oQuoteBody(body, path, query) {
  var src = BB8O_ROUTES[path], now = Date.now();
  var one = function (q, sym) { var f = bb8oFix(q, sym, src); if (f) f.feed = bb8oFeed(f, sym, src, now); return f; };
  var map = function (m) {
    if (!m || typeof m !== "object" || Array.isArray(m)) return m;
    var out = {};
    for (var k in m) if (Object.prototype.hasOwnProperty.call(m, k)) {
      var q = m[k];
      if (!bb8oIsRow(q)) { out[k] = q; continue; }
      var f = one(q, k);
      if (f) out[k] = f;
    }
    return out;
  };
  if (path === "/api/finnhub") {
    if (!bb8oIsRow(body)) return body;
    var sym = query && query.get ? String(query.get("symbol") || "").trim().toUpperCase() : "";
    return one(body, sym || body.name || "") || {};
  }
  if (path === "/api/twelve-data-quote") {
    var tb = Object.assign({}, body);
    if (tb.quotes) tb.quotes = map(tb.quotes);
    if (tb.directIndices) tb.directIndices = map(tb.directIndices);
    return tb;
  }
  return map(body);
}
// ── LSE (and any Yahoo) listing profile ──
function bb8oMoney(v, ccy) {
  var n = Number(v);
  if (!isFinite(n) || n <= 0) return "";
  var sym = BB8O_CCY[ccy] || (ccy ? ccy + " " : "");
  var u = n >= 1e12 ? [1e12, "tn"] : n >= 1e9 ? [1e9, "bn"] : n >= 1e6 ? [1e6, "m"] : [1, ""];
  return sym + (n / u[0]).toFixed(1) + u[1];
}
function bb8oSymOk(s) { return /^[A-Z0-9^][A-Z0-9.\-=^]{0,14}$/.test(String(s || "")); }
function bb8oAbout(text) {
  var s = String(text || "").replace(/\s+/g, " ").trim();
  if (s.length <= 600) return s;
  var cut = s.slice(0, 600), dot = cut.lastIndexOf(". ");
  return dot > 200 ? cut.slice(0, dot + 1) : cut.replace(/\s+\S*$/, "") + "…";
}
function bb8oProfileFrom(sym, r) {
  var pr = r.price || {}, sd = r.summaryDetail || {}, ks = r.defaultKeyStatistics || {}, ap = r.assetProfile || {};
  var cur = String(pr.currency || "");
  var u = typeof bb8cUnit === "function" ? bb8cUnit(cur) : (cur === "GBp" || cur === "GBX" ? { major: "GBP", div: 100 } : { major: cur.toUpperCase(), div: 1 });
  var px = bb8oNum(pr.regularMarketPrice), shares = bb8oNum(ks.sharesOutstanding) || bb8oNum(ks.impliedSharesOutstanding);
  var mcRaw = bb8oNum(sd.marketCap) || bb8oNum(pr.marketCap);
  var implied = shares && px ? shares * px / (u.div || 1) : null;
  var ratio = mcRaw && implied ? mcRaw / implied : null, mc = mcRaw, check;
  if (ratio != null && ratio >= 0.5 && ratio <= 2) check = "ok";
  else if (ratio != null && ratio >= 50 && ratio <= 200) { mc = mcRaw / 100; check = "corrected-minor-units"; }
  else if (mcRaw && !implied) check = "unverified";
  else if (!mcRaw && implied) { mc = implied; check = "computed"; }
  else if (mcRaw) check = "mismatch";
  else check = "missing";
  var lse = /\.L$/.test(sym), ex = lse ? "LSE" : String(pr.exchangeName || pr.exchange || "");
  var name = String(pr.longName || pr.shortName || sym);
  var region = lse ? "UK" : String(ap.country || "");
  var pe = bb8oNum(sd.trailingPE);
  var unitNote = u.div === 100 ? "Quoted in pence (" + cur + "); 100p = £1. Market cap is in pounds." : "";
  var mcText = bb8oMoney(mc, u.major);
  var t = Date.now();
  return {
    symbol: sym, name: name, exchange: ex, exchangeName: String(pr.exchangeName || ""), region: region,
    type: String(pr.quoteType || "").toUpperCase() === "EQUITY" ? "Stock" : String(pr.quoteType || ""),
    priceCurrency: cur || null, currency: u.major || null, unitNote: unitNote,
    price: px, priceMajor: px != null ? Math.round(px / (u.div || 1) * 10000) / 10000 : null,
    marketCap: mc != null ? Math.round(mc) : null, marketCapCurrency: u.major || null, marketCapText: mcText,
    marketCapCheck: { status: check, sharesOutstanding: shares, impliedMarketCap: implied != null ? Math.round(implied) : null, ratio: ratio != null ? Math.round(ratio * 1000) / 1000 : null },
    pe: pe != null ? Math.round(pe * 100) / 100 : null, sector: ap.sector || null, industry: ap.industry || null,
    about: bb8oAbout(ap.longBusinessSummary),
    asset: {
      tk: sym, nm: name + (ex ? " (" + ex + ")" : ""), cat: "Stock", ex: ex, rg: region,
      pe: pe != null ? pe.toFixed(1) : "", mc: mcText,
      th: name + ", " + (lse ? "home listing on LSE" : "listed on " + (ex || "its home exchange")) + ", quoted in " + (u.div === 100 ? "pence (GBp)" : (cur || "local currency")) + ". Prices stream from Yahoo during the " + (ex || "exchange") + " session; outside it the last close is shown."
    },
    source: "Yahoo Finance", sourceUrl: "https://finance.yahoo.com/quote/" + encodeURIComponent(sym) + "/profile/",
    asOf: new Date(t).toISOString(), asOfUk: bb8oUk(t)
  };
}
async function bb8oProfile(sym) {
  sym = String(sym || "").trim().toUpperCase();
  if (!bb8oSymOk(sym) || typeof rt32Crumb !== "function" || typeof rt32Get !== "function") return null;
  var hit = bb8oProfiles.get(sym);
  if (hit && Date.now() - hit.at < BB8O_PROFILE_MS) return hit.pending || hit.value;
  var job = (async function () {
    for (var i = 0; i < 2; i++) {
      var crumb = await rt32Crumb(i > 0);
      var headers = { "User-Agent": typeof RT32_BUA === "string" ? RT32_BUA : "Mozilla/5.0" };
      try { if (typeof RT32 === "object" && RT32 && RT32.ck) headers.Cookie = RT32.ck; } catch (e) {}
      var r = await rt32Get("https://query2.finance.yahoo.com/v10/finance/quoteSummary/" + encodeURIComponent(sym) + "?modules=price,summaryDetail,defaultKeyStatistics,assetProfile&crumb=" + encodeURIComponent(crumb || ""), headers);
      if (r.status === 401 || r.status === 403) continue;
      if (!r.ok) return null;
      var j = await r.json();
      var res0 = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
      return res0 && res0.price ? bb8oProfileFrom(sym, res0) : null;
    }
    return null;
  })();
  var entry = { at: Date.now(), pending: job, value: null };
  bb8oProfiles.set(sym, entry);
  while (bb8oProfiles.size > 500) bb8oProfiles.delete(bb8oProfiles.keys().next().value);
  try { entry.value = await job; } catch (e) { entry.value = null; }
  entry.pending = null;
  if (!entry.value) bb8oProfiles.delete(sym);
  return entry.value;
}
function bb8oSearchBody(body, prof) {
  if (!body || typeof body !== "object" || !Array.isArray(body.quotes)) return body;
  var out = Object.assign({}, body);
  out.result = body.quotes.filter(function (q) { return q && q.symbol; }).map(function (q) {
    var row = { symbol: String(q.symbol), name: String(q.longname || q.shortname || q.symbol), exchange: String(q.exchDisp || q.exchange || ""), exchangeCode: String(q.exchange || ""), type: String(q.typeDisp || q.quoteType || ""), quoteType: String(q.quoteType || ""), sector: q.sector || q.sectorDisp || null, industry: q.industry || q.industryDisp || null };
    if (prof && prof.symbol === row.symbol) row.profile = prof;
    return row;
  });
  if (prof) out.profile = prof;
  return out;
}
// ── Brief edition: request-driven, memory only ──
function bb8oTokens(h) {
  var set = {};
  String(h || "").toLowerCase().replace(/[^a-z0-9$%.\s-]/g, " ").split(/\s+/).forEach(function (w) { w = w.replace(/^[.-]+|[.-]+$/g, ""); if (w.length >= 4 && !BB8O_STOP[w]) set[w] = 1; });
  return Object.keys(set);
}
function bb8oSame(a, b) {
  if (!a.length || !b.length) return false;
  var n = 0, m = {};
  a.forEach(function (w) { m[w] = 1; });
  b.forEach(function (w) { if (m[w]) n++; });
  return n >= 2 && n / Math.min(a.length, b.length) >= 0.5;
}
function bb8oHash(s) { try { return crypto.createHash("md5").update(String(s)).digest("hex").slice(0, 6); } catch (e) { return "000000"; } }
function bb8oRank(heads) {
  var list = (heads || []).filter(function (x) { return x && x.h; }).map(function (x) { return { h: String(x.h), src: String(x.src || ""), link: String(x.link || ""), t: Number(x.t) || 0, as: Array.isArray(x.as) ? x.as : [], tok: bb8oTokens(x.h) }; });
  list.forEach(function (x) {
    var srcs = {};
    srcs[x.src] = 1;
    list.forEach(function (y) { if (y !== x && y.src !== x.src && bb8oSame(x.tok, y.tok)) srcs[y.src] = 1; });
    x.sources = Object.keys(srcs).sort();
    x.coverage = x.sources.length;
    x.score = x.coverage * 10 + Math.min(x.as.length, 3);
    x.key = x.tok.slice().sort().join(" ") || x.h.toLowerCase();
  });
  return list.sort(function (a, b) { return b.score - a.score || b.t - a.t || (a.h < b.h ? -1 : a.h > b.h ? 1 : 0); });
}
function bb8oStory(x) {
  return { headline: x.h, source: x.src, link: x.link, publishedAt: x.t ? new Date(x.t).toISOString() : null, publishedAtUk: x.t ? bb8oUk(x.t) : null, coverage: x.coverage, sources: x.sources, assets: x.as };
}
function bb8oPick(ranked, now, reason, prev) {
  var lead = ranked[0], also = [];
  ranked.slice(1).forEach(function (x) { if (also.length < 3 && !bb8oSame(x.tok, lead.tok) && !also.some(function (y) { return bb8oSame(x.tok, y.tok); })) also.push(x); });
  var day = bb8oYmd(now), seq = prev && prev.day === day ? prev.seq + 1 : 1;
  return { day: day, seq: seq, id: day + "." + seq + "-" + bb8oHash(lead.key), lead: lead, also: also, startedAt: now, reason: reason };
}
// The rule (deterministic, evaluated on each request):
// 1. No edition in memory, or a new London day: elect the top-ranked story (coverage x10 + assets, then newer, then A-Z).
// 2. Otherwise keep the lead unless, at least 30 minutes into the edition, a story published after the lead
//    is covered by at least one more outlet (score >= lead score + 10), or the lead is over 12 hours old and a
//    newer story scores at least as well.
function bb8oDecide(cur, ranked, now) {
  if (!ranked.length) return { ed: cur, changed: false };
  var day = bb8oYmd(now);
  if (!cur) return { ed: bb8oPick(ranked, now, "cold-start", null), changed: true };
  if (cur.day !== day) return { ed: bb8oPick(ranked, now, "new-day", cur), changed: true };
  if (now - cur.startedAt < BB8O_DWELL_MS) return { ed: cur, changed: false };
  var lead = cur.lead;
  var newer = ranked.filter(function (x) { return x.t > lead.t && !bb8oSame(x.tok, lead.tok); });
  var best = newer[0];
  if (!best) return { ed: cur, changed: false };
  if (best.score >= lead.score + 10) return { ed: bb8oPick([best].concat(ranked.filter(function (x) { return x !== best; })), now, "broader-coverage", cur), changed: true };
  if (lead.t && now - lead.t > BB8O_AGED_MS && best.score >= lead.score) return { ed: bb8oPick([best].concat(ranked.filter(function (x) { return x !== best; })), now, "lead-aged", cur), changed: true };
  return { ed: cur, changed: false };
}
function bb8oEditionOut(ed, now) {
  if (!ed) return { editionId: null, status: "unavailable", lead: null, also: [], updatedAt: null, updatedAtUk: null, checkedAt: bb8oEd.headsAt ? new Date(bb8oEd.headsAt).toISOString() : null };
  return {
    editionId: ed.id, day: ed.day, seq: ed.seq, status: "ok", reason: ed.reason,
    lead: bb8oStory(ed.lead), also: ed.also.map(bb8oStory),
    updatedAt: new Date(ed.startedAt).toISOString(), updatedAtUk: "Updated " + bb8oHm(ed.startedAt) + " UK",
    checkedAt: bb8oEd.headsAt ? new Date(bb8oEd.headsAt).toISOString() : null, checkedAtUk: bb8oEd.headsAt ? bb8oUk(bb8oEd.headsAt) : null,
    rule: "Lead holds for the edition. A new edition starts on a new UK day, or (after 30 minutes) when a newer story is carried by at least one more outlet, or when the lead is over 12 hours old and a newer story ranks as high.",
    memory: "process"
  };
}
async function bb8oHeads(now) {
  if (bb8oEd.heads && now - bb8oEd.headsAt < BB8O_HEADS_MS) return bb8oEd.heads;
  if (bb8oEd.pending) return bb8oEd.pending;
  if (typeof _rt48sHeads !== "function") return bb8oEd.heads || [];
  bb8oEd.pending = (async function () {
    try {
      var got = await _rt48sHeads();
      if (Array.isArray(got) && got.length) { bb8oEd.heads = got; bb8oEd.headsAt = Date.now(); }
    } catch (e) {}
    return bb8oEd.heads || [];
  })();
  try { return await bb8oEd.pending; } finally { bb8oEd.pending = null; }
}
async function bb8oEdition(now) {
  var t = now || Date.now();
  var heads = await bb8oHeads(t);
  var d = bb8oDecide(bb8oEd.cur, bb8oRank(heads), t);
  bb8oEd.cur = d.ed;
  return bb8oEditionOut(bb8oEd.cur, t);
}
// ── Insider trade dates ──
function bb8oTxDate(block, xml) {
  var get = function (src, tag) { try { return typeof bb7Tag === "function" ? bb7Tag(src, tag) : ""; } catch (e) { return ""; } };
  var iso = function (s) { var v = typeof bb7IsoDate === "function" ? bb7IsoDate(s) : String(s || ""); return /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : ""; };
  var tx = iso(get(block, "transactionDate"));
  if (tx) return { date: tx, source: "transactionDate" };
  var de = iso(get(block, "deemedExecutionDate"));
  if (de) return { date: de, source: "deemedExecutionDate" };
  var pr = iso(get(xml, "periodOfReport"));
  if (pr) return { date: pr, source: "periodOfReport" };
  return { date: null, source: null };
}
function bb8oForm4Rows(xml, rows) {
  if (!Array.isArray(rows) || typeof bb7Blocks !== "function") return rows;
  var blocks = bb7Blocks(xml, "nonDerivativeTransaction").concat(bb7Blocks(xml, "derivativeTransaction"));
  return rows.map(function (r, i) {
    if (!r || typeof r !== "object") return r;
    var d = bb8oTxDate(blocks[i] || "", xml);
    return Object.assign({}, r, { transactionDate: d.date, transactionDateSource: d.source });
  });
}
function bb8oLegacyRows(xml, rows) {
  if (!Array.isArray(rows)) return rows;
  var blocks = (String(xml || "").match(/<(nonDerivativeTransaction|derivativeTransaction)>[\s\S]*?<\/\1>/gi) || []).slice(0, 20);
  return rows.map(function (r, i) {
    if (!r || typeof r !== "object") return r;
    var d = bb8oTxDate(blocks[i] || "", xml);
    return Object.assign({}, r, { date: d.date, dateSource: d.source, dateMissing: !d.date });
  });
}
function bb8oDayUk(s) { var v = typeof bb8lDay === "function" ? bb8lDay(s) : String(s || ""); return v || null; }
function bb8oInsiderRow(r) {
  if (!r || typeof r !== "object") return r;
  var tx = /^\d{4}-\d{2}-\d{2}$/.test(String(r.transactionDate || "")) ? String(r.transactionDate) : null;
  var fl = /^\d{4}-\d{2}-\d{2}$/.test(String(r.filingDate || "")) ? String(r.filingDate) : null;
  var txUk = tx ? bb8oDayUk(tx) : null, flUk = fl ? bb8oDayUk(fl) : null;
  var o = Object.assign({}, r, {
    transactionDate: tx, transactionDateUk: txUk, tradeDate: tx, tradeDateUk: txUk,
    transactionDateMissing: !tx, transactionDateSource: r.transactionDateSource || (tx ? "transactionDate" : null),
    filingDateUk: flUk, sameDayFiling: !!(tx && fl && tx === fl)
  });
  o.whenUk = tx ? (fl && fl !== tx ? txUk + " · filed " + flUk : txUk + (fl ? " · filed same day" : "")) : "Trade date not reported" + (flUk ? " · filed " + flUk : "");
  return o;
}
function bb8oInsiderBody(body) {
  if (!body || typeof body !== "object" || !Array.isArray(body.insider)) return body;
  var rows = body.insider.map(bb8oInsiderRow).map(function (r, i) { return { r: r, i: i }; });
  rows.sort(function (a, b) {
    var ta = a.r && a.r.tradeDate || "", tb = b.r && b.r.tradeDate || "";
    if (ta !== tb) return ta < tb ? 1 : -1;
    var fa = a.r && a.r.filingDate || "", fb = b.r && b.r.filingDate || "";
    if (fa !== fb) return fa < fb ? 1 : -1;
    return a.i - b.i;
  });
  body.insider = rows.map(function (x) { return x.r; });
  return body;
}
function bb8oValuation(body) {
  var v = body && body.valuation;
  if (!v || typeof v !== "object" || !("price" in v)) return body;
  var n = Number(v.price);
  if (v.price !== null && isFinite(n) && n > 0) return body;
  var last = bb8oGood.get(bb8oKey(body.symbol));
  if (last) { v.price = last.p; v.priceFallback = true; v.priceAsOf = last.tsMs ? new Date(last.tsMs).toISOString() : null; v.priceAsOfUk = last.tsMs ? bb8oUk(last.tsMs) : null; }
  else { v.price = null; v.priceMissing = true; }
  return body;
}
function bb8oShape(res, status, body) {
  var path = res && res.bb8oPath;
  if (!path || !body || typeof body !== "object") return body;
  if (BB8O_ROUTES[path]) return bb8oQuoteBody(body, path, res.bb8oQuery);
  if (path === "/api/search") return bb8oSearchBody(body, res.bb8oProfile || null);
  if (path === "/api/brief" && res.bb8oEdition && status === 200 && body.brief) { var b = Object.assign({}, body); b.edition = res.bb8oEdition; return b; }
  if (path === "/api/financials") return bb8oValuation(body);
  return body;
}
async function bb8oEditionRoute(req, res) {
  var ed = null;
  try { ed = await bb8oEdition(Date.now()); } catch (e) { ed = bb8oEditionOut(null, Date.now()); }
  return json(res, 200, ed);
}
async function bb8oProfileRoute(req, res, url) {
  var sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!bb8oSymOk(sym)) return json(res, 400, { error: "Invalid symbol." });
  var fwd = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim(), addr = fwd || (req.socket && req.socket.remoteAddress) || "unknown";
  var hit = bb8oProfiles.get(sym);
  if (!(hit && hit.value && Date.now() - hit.at < BB8O_PROFILE_MS) && typeof yahooRateLimiter === "object" && yahooRateLimiter && !yahooRateLimiter.allow(addr)) return json(res, 429, { error: "Too many requests.", symbol: sym });
  var p = null;
  try { p = await bb8oProfile(sym); } catch (e) { p = null; }
  if (!p) return json(res, 200, { symbol: sym, status: "unavailable" }, { "X-Dispatch-Data-Status": "unavailable" });
  return json(res, 200, Object.assign({ status: "available" }, p));
}
try {
  if (typeof bb5eSpec === "function" && typeof bb5eCash === "function") {
    // Taiwan listings fell through to the US session table (2330.TW read "US market closed").
    var bb8oSpec0 = bb5eSpec;
    bb5eSpec = function (symbol) {
      var s = typeof bb5eCanon === "function" ? bb5eCanon(symbol) : String(symbol || "").trim().toUpperCase();
      if (/\.TWO?$/.test(s)) return bb5eCash("Asia/Taipei", 540, 810, "Taiwan");
      return bb8oSpec0.apply(this, arguments);
    };
  }
  if (typeof yahooQuote === "function") {
    var bb8oYq0 = yahooQuote;
    yahooQuote = async function () {
      var out = await bb8oYq0.apply(this, arguments);
      try { out = await bb8oGuardMap(out, "yahoo"); } catch (e) {}
      return out;
    };
  }
  if (typeof fetchYahooQuote === "function") {
    var bb8oFyq0 = fetchYahooQuote;
    fetchYahooQuote = async function (symbol) {
      var q = await bb8oFyq0.apply(this, arguments);
      try { if (bb8oIsRow(q)) return bb8oFix(q, symbol, "yahoo"); } catch (e) {}
      return q;
    };
  }
  if (typeof bb7ParseForm4 === "function") {
    var bb8oForm40 = bb7ParseForm4;
    bb7ParseForm4 = function (xml) {
      var rows = bb8oForm40.apply(this, arguments);
      try { return bb8oForm4Rows(xml, rows); } catch (e) { return rows; }
    };
  }
  if (typeof parseForm4 === "function") {
    var bb8oLegacy0 = parseForm4;
    parseForm4 = function (xml) {
      var rows = bb8oLegacy0.apply(this, arguments);
      try { return bb8oLegacyRows(xml, rows); } catch (e) { return rows; }
    };
  }
  if (typeof bb8lRowDates === "function") {
    var bb8oRowDates0 = bb8lRowDates;
    bb8lRowDates = function (body) {
      var out = bb8oRowDates0.apply(this, arguments);
      try { return bb8oInsiderBody(out); } catch (e) { return out; }
    };
  }
  if (typeof json === "function") {
    var bb8oJson0 = json;
    json = function (res, status, body) {
      var args = Array.prototype.slice.call(arguments);
      try { args[2] = bb8oShape(res, status, body); } catch (e) {}
      return bb8oJson0.apply(this, args);
    };
  }
  if (typeof handle === "function") {
    var bb8oHandle0 = handle;
    handle = async function (req, res) {
      try {
        var url = new URL((req && req.url) || "/", "http://localhost");
        var path = url.pathname;
        if (res) { res.bb8oPath = path; res.bb8oQuery = url.searchParams; }
        var m = req && req.method;
        if (m === "GET" || m === "HEAD") {
          if (path === "/api/brief/edition") return await bb8oEditionRoute(req, res);
          if (path === "/api/listing-profile") return await bb8oProfileRoute(req, res, url);
          if (path === "/api/search") {
            var q = String(url.searchParams.get("q") || "").trim().toUpperCase();
            if (/^[A-Z0-9]{1,6}\.L$/.test(q)) { try { res.bb8oProfile = await bb8oProfile(q); } catch (e) {} }
          }
        }
        if (m === "POST" && path === "/api/brief") { try { res.bb8oEdition = await bb8oEdition(Date.now()); } catch (e) {} }
      } catch (e) {}
      return bb8oHandle0.apply(this, arguments);
    };
  }
} catch (e) { console.warn("bb8o hooks skipped", e && e.message); }
// BB8O_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8o")]
if bad:
    die("bb8o block declares a non-bb8o function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8o block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8o function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK or "setTimeout(" in BLOCK or "stripe" in BLOCK.lower():
    die("bb8o block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8o replaced in place: %s" % a.strip().splitlines()[0][:70])
v = v.rstrip("\n") + "\n" + BLOCK
print("server-only: app.js and index.html are not modified")

def nodecheck(src, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(src)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, r.stderr[:500]))

nodecheck(v, "server.js")
print("node --check passed" + (" (dry run)" if CHECK else ""))
print("bb8o setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8obak"
try:
    open(bak, "wb").write(raw)
    open(SRV, "wb").write(after_srv)
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("node --check failed after write: " + r.stderr[:400])
    if read_bytes(APP) != app_before or read_bytes(IDX) != idx_before:
        raise RuntimeError("app.js or index.html changed")
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("APPLY bb8o zero-price fallback, insider trade dates, LSE profile, canonical feed status, brief edition")
