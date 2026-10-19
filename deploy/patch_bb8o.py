#!/usr/bin/env python3
"""patch_bb8o.py — (1) no zero, null or non-finite price on any quote path: last valid close with its real
timestamp and session, flagged fallback; Taiwan listings get the Taipei session. (2) Form 4 trade date falls back
to deemedExecutionDate then periodOfReport (same XML, no extra SEC request); never the filing date. (3) /api/search
returns result[] in the client's shape plus an LSE listing profile (GBp handled); GET /api/listing-profile.
(4) One canonical feed object {v,status,ageSec,asOf,...} on every quote row of every quote route.
(5) GET /api/brief/edition and brief.edition: a stable, request-driven edition, memory only.
(6) Analyst ratings and price targets: one sanitizer (bb8oStripRatings) removes target / analyst keys from every JSON
response and AI body; generic keys (rating, ra, recommendation...) only on the BB8O_MARKET_ROUTES allowlist, the Yahoo
quoteSummary source, the fundamentals cache and AI context / fact fields. User questions and messages pass untouched.
(7) AI committee, lenses, intelligence and brief: explicit no-advice rule in those prompts; every prose field of their
output drops buy/sell/hold calls, ratings, price targets, fair values and position sizes (sentence level); "takeaway"
added next to recommendation / verdict; "Recommendation" / "Verdict" headings become "Takeaway".
(8) Brief: "Highest conviction" / "top pick" become "Top desk score: TICKER NN/100 (Dispatch desk score)"; overweight /
underweight become measured Leading / Lagging themes (Yahoo ETF proxies vs SPY over 5 sessions, cited, as-of UK), also
registered as a numbered source in bb8q's shared context. Upstream null changes (bb8q / bb8q2 gold spot) stay null.
Server.js only. Stacked on bb8q2 (server md5 af877dde4d73f4c19eeff011a0e98f89; apply order bb8q b4f66c89 -> bb8q2 -> bb8o).
Appended after // BB8Q2_JS_END;
anchors are long-standing declarations only (no in-place edits). See docs/bb8o.md.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8o.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "af877dde4d73f4c19eeff011a0e98f89",
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

REPLACE = []

REQUIRED = [
    ("bb8n end marker", "// BB8N_JS_END"),
    ("bb8p end marker", "// BB8P_JS_END"),
    ("bb8q end marker", "// BB8Q_JS_END"),
    ("bb8q2 end marker (bb8o is appended after it)", "// BB8Q2_JS_END"),
    ("bb8qBuild", "async function bb8qBuild(st, body) {"),
    ("bb8qSrc", "function bb8qSrc(name, link, ms, detail, key) {"),
    ("bb8qSrcText", "var bb8qSrcText = new WeakMap();"),
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
    ("rt32Yahoo", "async function rt32Yahoo(sym) {"),
    ("RT32", "const RT32 = { cache: new Map(),"),
    ("readBody", "async function readBody(req) {"),
    ("bb2Read0", 'var bb2Read0 = typeof readBody === "function" ? readBody : async function () { return {}; };'),
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
// The upstream row deliberately carries no change: null change / changePct / prevClose, or changeAvailable:false.
function bb8oNullChg(q) {
  if (!q || typeof q !== "object") return false;
  if (q.changeAvailable === false) return true;
  var nul = function (k) { return Object.prototype.hasOwnProperty.call(q, k) && q[k] === null; };
  return nul("c") || nul("change") || nul("changePct");
}
// Valid price: keep it, but never let a non-finite change or previous close through.
function bb8oTidy(q) {
  var p = Number(q.p), prev = bb8oNum(q.prev), c = bb8oNum(q.c), ch = bb8oNum(q.change), out = q, copy = function () { if (out === q) out = Object.assign({}, q); return out; };
  if (prev == null || prev <= 0) {
    // An upstream that already says "no change" (explicit nulls or changeAvailable:false, e.g. bb8q / bb8q2 gold spot on a
    // cold start) keeps its nulls, futuresChange and changeNote. Only junk values (NaN, Infinity, strings) become 0 as before.
    if (bb8oNullChg(q)) {
      if (q.prev !== null || q.c !== null || q.change !== null || q.changeAvailable !== false) { copy(); out.prev = null; out.c = null; out.change = null; out.changeAvailable = false; }
      return out;
    }
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
  else if (bb8oNullChg(q)) { out.prev = null; out.c = null; out.change = null; out.basis = "none"; out.changeAvailable = false; }
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
  var tsMs = rmt > 0 && bb8oYmd(rmt, tz) === day ? rmt : barMs;
  var r4 = function (x) { return Math.round(Number(x) * 10000) / 10000; };
  var pv = bb8oDistinctPrev(r, tz);
  return { p: r4(cl[i]), prev: pv && pv.prev ? r4(pv.prev) : null, prevFix: pv ? pv.fix : null, prevDay: pv ? pv.prevDay : null, ts: Math.floor(tsMs / 1000), tsMs: tsMs, currency: meta.currency || null, src: "yahoo-daily-close", seen: Date.now() };
}
// Previous close from Yahoo daily bars, guarding against duplicate bars (0700.HK: Thu 15 and Fri 16 both "closed"
// at 417.80). Bars on the same session date or timestamp collapse to the last one. When the prior bar's close equals the
// last close and either bar's high/low range does not contain that close, the prior bar is a copy: the previous distinct
// session's close is used, else the chart meta previousClose / chartPreviousClose. Normal series are unchanged.
// (QA 1:38 rule: two consecutive identical daily closes are treated as a duplicate bar; prevDay says which close is used.)
function bb8oDistinctPrev(r, tz) {
  if (!r) return null;
  var ts = r.timestamp || [], q0 = (r.indicators && r.indicators.quote && r.indicators.quote[0]) || {}, cl = q0.close || [], hi = q0.high || [], lo = q0.low || [], meta = r.meta || {};
  var bars = [];
  for (var i = 0; i < ts.length; i++) {
    if (!(Number(cl[i]) > 0)) continue;
    var b = { t: Number(ts[i]), d: bb8oYmd(Number(ts[i]) * 1000, tz), c: Number(cl[i]), h: Number(hi[i]), l: Number(lo[i]) };
    var last = bars[bars.length - 1];
    if (last && (last.d === b.d || last.t === b.t)) { bars[bars.length - 1] = b; continue; }
    bars.push(b);
  }
  if (!bars.length) return null;
  var L = bars[bars.length - 1], fix = null, k = bars.length - 2;
  while (k >= 0 && Math.abs(bars[k].c - L.c) < 1e-9) { fix = "duplicate-bar"; k--; }
  var mp = [meta.previousClose, meta.chartPreviousClose, meta.regularMarketPreviousClose].map(Number).filter(function (x) { return x > 0 && Math.abs(x - L.c) > 1e-9; })[0];
  if (k >= 0 && !(fix && Math.abs(bars[k].c - L.c) < 1e-9)) return { prev: bars[k].c, fix: fix, prevDay: bars[k].d, lastDay: L.d };
  if (mp) return { prev: mp, fix: fix || "meta-previous-close", prevDay: null, lastDay: L.d };
  return { prev: k >= 0 ? bars[k].c : null, fix: fix, prevDay: k >= 0 ? bars[k].d : null, lastDay: L.d };
}
// A valid row with exactly zero change against its previous close: check the daily bars once (duplicate-bar guard).
var BB8O_PREVCHK_MS = 10 * 60 * 1000;
var bb8oPrevChk = new Map();
async function bb8oPrevCheck(map) {
  if (!map || typeof map !== "object" || Array.isArray(map)) return map;
  var keys = Object.keys(map).filter(function (k) {
    var q = map[k], p = Number(q && q.p), pv = Number(q && q.prev);
    return bb8oIsRow(q) && p > 0 && pv > 0 && Math.abs(p - pv) < 1e-9 && !/-USD$|=X$|^\^/.test(k) && !q.prevFix;
  }).slice(0, 6);
  await Promise.all(keys.map(async function (k) {
    try {
      var hit = bb8oPrevChk.get(k), last;
      if (hit && Date.now() - hit.at < BB8O_PREVCHK_MS) last = hit.v; else { last = await bb8oChartLast(k); bb8oPrevChk.set(k, { at: Date.now(), v: last }); if (bb8oPrevChk.size > 128) bb8oPrevChk.delete(bb8oPrevChk.keys().next().value); }
      var q = map[k];
      if (!last || !last.prevFix || !(last.prev > 0) || Math.abs(last.p - Number(q.p)) > 1e-6) return;
      var o = Object.assign({}, q);
      o.prev = last.prev; o.change = Number(q.p) - last.prev; o.c = (o.change / last.prev) * 100; if ("changePct" in o) o.changePct = o.c;
      o.basis = "previous_close"; o.changeAvailable = true; o.prevFix = last.prevFix;
      if (last.prevDay) { o.prevDay = last.prevDay; o.prevNote = "Previous close is the " + bb8oDayLabel(Date.parse(last.prevDay + "T12:00:00Z"), "UTC") + " close (the prior daily bar repeated the last close)."; }
      map[k] = o;
    } catch (e) {}
  }));
  return map;
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
  // bb8q's gold spot row already carries a descriptive feed string: it is kept as feedLabel and feed.label, never lost.
  var one = function (q, sym) {
    var f = bb8oFix(q, sym, src);
    if (f) {
      f = bb8oCrypto24h(f, sym);
      var lbl = typeof f.feed === "string" && f.feed ? f.feed : null;
      f.feed = bb8oFeed(f, sym, src, now);
      if (lbl) { f.feedLabel = lbl; f.feed.label = lbl; }
      bb8oChangeDay(f, sym);
    }
    return f;
  };
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
    editionId: ed.id, day: ed.day, dayLabel: bb8oDayLabel(ed.startedAt), name: bb8oEditionName(now || Date.now()) + " edition",
    label: bb8oDayLabel(ed.startedAt) + " \u00b7 " + bb8oEditionName(now || Date.now()) + " edition", nameBasis: "UK time now: Morning before 12:00, Afternoon 12:00 to 16:59, Evening from 17:00",
    seq: ed.seq, status: "ok", reason: ed.reason,
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
// ── Analyst ratings and price targets ──
// Target / analyst keys are unambiguous and are stripped from every JSON response and every AI request body.
var BB8O_TARGET_KEYS = {
  targethighprice: 1, targetlowprice: 1, targetmeanprice: 1, targetmedianprice: 1, targethigh: 1, targetlow: 1, targetmean: 1, targetmedian: 1,
  pricetarget: 1, pricetargets: 1, targetprice: 1, analysttarget: 1, analysttargets: 1, consensustarget: 1,
  recommendationkey: 1, recommendationmean: 1, recommendationtrend: 1, upgradedowngradehistory: 1, numberofanalystopinions: 1,
  analystrating: 1, analystratings: 1, averageanalystrating: 1, consensusrating: 1
};
// Generic keys mean something else outside market data (a quiz rating, an editorial "recommendation"), so they are
// stripped only inside market / security payloads: the routes in BB8O_MARKET_ROUTES, the fundamentals source and cache,
// and the client-supplied context / fact fields of AI request bodies (BB8O_CTX_FIELDS).
var BB8O_GENERIC_KEYS = { rating: 1, ratings: 1, ra: 1, recommendation: 1, recommendations: 1, upgrades: 1, downgrades: 1 };
var BB8O_MARKET_ROUTES = {
  "/api/financials": 1, "/api/earnings": 1, "/api/holders": 1, "/api/insiders": 1, "/api/institutional-data": 1,
  "/api/openbb/fundamentals": 1, "/api/openbb/summary": 1, "/api/openbb/historical": 1,
  "/api/yahoo-quote": 1, "/api/yahoo-chart": 1, "/api/market-reference-quotes": 1, "/api/twelve-data-quote": 1, "/api/finnhub": 1,
  "/api/ext-hours": 1, "/api/coingecko": 1, "/api/spot-energy": 1, "/api/eia-spot": 1, "/api/gold-desk": 1, "/api/real-yield": 1,
  "/api/search": 1, "/api/listing-profile": 1, "/api/screener": 1, "/api/regime-fit": 1, "/api/ticker-news": 1, "/api/news-scores": 1,
  "/api/brief": 1, "/api/brief/edition": 1
};
// Client-supplied context / fact fields of AI request bodies. Never messages, question, userThesis or any other user-typed field.
var BB8O_CTX_FIELDS = { context: 1, terminalcontext: 1, contextnotes: 1, notes: 1, facts: 1, fact: 1, tickers: 1, assets: 1, asset: 1, sources: 1, marketdata: 1, quotes: 1, portfolio: 1, watchlist: 1 };
var BB8O_RATING_WORDS = "Strong Buy|Strong Sell|Moderate Buy|Moderate Sell|Buy|Sell|Hold|Accumulate|Avoid|Reduce|Outperform|Underperform|Market Perform|Overweight|Underweight|Equal[- ]Weight";
var BB8O_RATING_SEP_RE = new RegExp("\\s[·|]\\s(?:" + BB8O_RATING_WORDS + ")(?=\\s[·|]|\\s*$)", "gim");
var BB8O_RATING_LABEL_RE = /\s*[|·]?\s*\b(?:Analyst\s+)?(?:Rating|Recommendation|Consensus rating)s?:\s*[^|·\n]*/gi;
var BB8O_TARGET_RE = /[^.\n|·]*\b(?:price targets?|target prices?|analyst(?:s'?)? (?:price )?targets?|consensus targets?|mean targets?|target (?:mean|median|high|low)(?: price)?)\b(?:[^.\n|·]|\.(?=\d))*\d(?:[^.\n|·]|\.(?=\d))*\.?/gi;
var BB8O_CONSENSUS_RE = new RegExp(",?\\s*\\b(?:consensus|average analyst|analyst|street)\\s+(?:rating|recommendation)s?\\s*(?:of|is|was|:)?\\s*(?:" + BB8O_RATING_WORDS + ")\\b\\.?", "gi");
var BB8O_TALLY_RE = /\s*\|?\s*\bAnalyst:\s*\d+\s*buy\s*\/\s*\d+\s*hold\s*\/\s*\d+\s*sell\b/gi;
var BB8O_PT_RE = /\s*\|?\s*\bPT\s+(?:mean|median|high|low)\s*\$?\d[\d,]*(?:\.\d+)?/gi;
var bb8oStripStats = { keys: 0, text: 0 };
function bb8oHas(o, k) { return Object.prototype.hasOwnProperty.call(o, String(k).toLowerCase()); }
function bb8oRatingKey(k, generic) { return bb8oHas(BB8O_TARGET_KEYS, k) || (!!generic && bb8oHas(BB8O_GENERIC_KEYS, k)); }
function bb8oMarketRoute(path) { return !!path && bb8oHas(BB8O_MARKET_ROUTES, path); }
// The single sanitizer: removes target / analyst keys everywhere, plus the generic keys when generic is true (market payloads only).
function bb8oStripRatings(x, generic, seen, depth) {
  if (!x || typeof x !== "object") return x;
  depth = depth || 0;
  if (depth > 14) return x;
  seen = seen || new WeakSet();
  if (seen.has(x)) return x;
  seen.add(x);
  if (Array.isArray(x)) { for (var i = 0; i < x.length; i++) bb8oStripRatings(x[i], generic, seen, depth + 1); return x; }
  if (x instanceof Map) { x.forEach(function (v) { bb8oStripRatings(v, generic, seen, depth + 1); }); return x; }
  if (typeof Buffer !== "undefined" && Buffer.isBuffer && Buffer.isBuffer(x)) return x;
  Object.keys(x).forEach(function (k) {
    if (bb8oRatingKey(k, generic)) { try { delete x[k]; bb8oStripStats.keys++; } catch (e) {} return; }
    bb8oStripRatings(x[k], generic, seen, depth + 1);
  });
  return x;
}
function bb8oScrubText(s) {
  if (typeof s !== "string" || !s) return s;
  s = bb8oDeskScore(s);
  s = bb8oCtxOpinion(s);
  var out = s.replace(BB8O_RATING_LABEL_RE, "").replace(BB8O_RATING_SEP_RE, "").replace(BB8O_TARGET_RE, "").replace(BB8O_CONSENSUS_RE, "").replace(BB8O_TALLY_RE, "").replace(BB8O_PT_RE, "");
  if (out !== s) bb8oStripStats.text++;
  return out;
}
// Context / fact values: every rating key (target and generic) removed and rating / target text scrubbed.
function bb8oScrubCtx(v, seen, depth) {
  if (typeof v === "string") return bb8oScrubText(v);
  if (!v || typeof v !== "object") return v;
  depth = depth || 0;
  if (depth > 14) return v;
  seen = seen || new WeakSet();
  if (seen.has(v)) return v;
  seen.add(v);
  if (Array.isArray(v)) { for (var i = 0; i < v.length; i++) v[i] = bb8oScrubCtx(v[i], seen, depth + 1); return v; }
  Object.keys(v).forEach(function (k) {
    if (bb8oRatingKey(k, true)) { try { delete v[k]; bb8oStripStats.keys++; } catch (e) {} return; }
    v[k] = bb8oScrubCtx(v[k], seen, depth + 1);
  });
  return v;
}
// AI request bodies: messages and every other user-typed field pass through byte-identical (only target / analyst keys
// are removed from non-message objects); the client-supplied context / fact fields are sanitized in full.
function bb8oScrubBody(b) {
  if (!b || typeof b !== "object" || Array.isArray(b)) return b;
  Object.keys(b).forEach(function (k) {
    var lk = String(k).toLowerCase();
    if (lk === "messages") return;
    if (bb8oRatingKey(k, false)) { try { delete b[k]; bb8oStripStats.keys++; } catch (e) {} return; }
    if (bb8oHas(BB8O_CTX_FIELDS, lk)) { b[k] = bb8oScrubCtx(b[k]); return; }
    if (b[k] && typeof b[k] === "object") bb8oStripRatings(b[k], false);
  });
  return b;
}
// ── AI committee, lenses, intelligence and brief prose: no buy / sell / hold calls, ratings or price targets ──
// The same rule as Ask is added to those prompts, and every prose field of their outputs goes through one
// sentence-level advice filter (an advice sentence is dropped whole; factual uses such as "insiders sold",
// "buybacks" or "sell-off" are not matched). The "recommendation" / "verdict" section is relabelled "takeaway".
var BB8O_NEUTRAL = "No takeaway beyond the facts above.";
var BB8O_NO_ADVICE = "NO ADVICE (applies to every field): never give a buy, sell, hold, accumulate, trim, add, reduce, avoid, overweight, underweight, outperform, strong buy, go long or go short call, a rating, a price target, a fair value, an upside or downside level, entry / exit / stop levels or a position size, for any asset or portfolio. Describe the facts, the risks and what to watch. Any verdict, recommendation, rating or action field is a neutral takeaway (a lens verdict is MONITOR).";
var BB8O_ADVICE_ROUTES = { "/api/committee": 1, "/api/lenses": 1, "/api/intelligence": 1, "/api/brief": 1 };
var BB8O_ACT = "buy|sell|hold|accumulate|trim|reduce|avoid|add|short|own|exit|enter|rotate|hedge|increase|decrease|scale|load";
var BB8O_ADVICE_RES = [
  // Imperative calls at the start of a sentence, bullet or "Label:" line.
  new RegExp("^(?:[\\-*•]\\s*|\\d+[.)]\\s*)?(?:[*_]{0,2}[A-Za-z][\\w /&-]{0,30}:[*_]{0,2}\\s*)?[*_]{0,2}(?:strong\\s+)?(?:buy|sell|hold|accumulate|trim|reduce|avoid|overweight|underweight|take profits?|book profits?|lock in|stay (?:long|short|invested)|go (?:long|short)|get (?:long|short)|add(?!\\s+to\\s+(?:that|this|the (?:list|mix|picture)))|rotate|rebalance|diversify|hedge(?!\\s+funds?)|increase (?:exposure|the position|your)|decrease (?:exposure|the position|your)|exit (?:the |your |all )?(?:position|trade|longs?|shorts?)|consider (?:buying|selling|holding|trimming|adding|accumulating|reducing|shorting|exiting|taking profits))(?![\\w-])", "i"),
  // Modal advice: "you / investors / we ... should buy".
  new RegExp("\\b(?:you|investors|traders|holders|shareholders|clients|readers|we|i|one|users)\\s+(?:should|could|might|may|must|ought to|would|need to|want to|might want to|may want to|are advised to|would do well to|can)\\s+(?:also\\s+|now\\s+|still\\s+)?(?:consider\\s+|look to\\s+|think about\\s+)?(?:" + BB8O_ACT + "|take profits?|lock in|go long|go short|stay long|stay short|initiate|establish|build)(?:ing|ed|s)?\\b", "i"),
  /\b(?:we|i)\s+(?:recommend|suggest|advise|favou?r|prefer|rate|would (?:buy|sell|hold|avoid))\b/i,
  /\brecommend(?:ed|s|ing)?\s+(?:buying|selling|holding|accumulating|trimming|adding|reducing|avoiding|shorting|an?\s+(?:strong\s+)?(?:buy|sell|hold))\b/i,
  /\b(?:rating|verdict|call|stance|recommendation|view|takeaway|action)\s*(?:is|:|of|remains|stays|=|-)?[*_]{0,2}\s*(?:an?\s+)?(?:strong\s+)?(?:buy|sell|hold|accumulate|trim|outperform|underperform|overweight|underweight|equal[- ]weight)\b/i,
  /\b(?:is|as|remains|looks like|stays|rated(?: as)?|rate it(?: as)?|rating of|upgraded? (?:\w+ ){0,3}to|downgraded? (?:\w+ ){0,3}to)\s+an?\s+(?:strong\s+)?(?:buy|sell|hold)\b/i,
  /\b(?:upgrade|downgrade)[sd]?\s+(?:\w+\s+){0,4}to\s+(?:strong\s+)?(?:buy|sell|hold|outperform|underperform|overweight|underweight|equal[- ]weight|neutral|market perform)\b/i,
  /\b(?:strong[- ](?:buy|sell)|conviction buy|top pick|best idea|(?:highest|top|strongest|best|high)[- ]conviction|market perform|sector perform)\b/i,
  /(?:^|[|·]\s*)(?:\**\s*)(?:overweight|underweight)s?\s*\**\s*:/i,
  /\b(?:go|move|stay|be|turn|remain|recommend|rated?|to|an?)\s+(?:overweight|underweight|equal[- ]weight)\b/i,
  /\b(?:overweight|underweight|equal[- ]weight)\s+(?:rating|position|stance|call|recommendation)\b/i,
  /\b(?:buy|sell|accumulate|trim|add|short)(?:ing)?\s+(?:on|into|the)\s+(?:dips?|weakness|strength|rall(?:y|ies)|pullbacks?|breakouts?|bounces?)\b/i,
  /\b(?:time to (?:buy|sell)|buying opportunity|(?:good|great|attractive|compelling|ideal) (?:entry|time to buy|point to (?:buy|sell)|buy)|worth (?:buying|owning|selling)|entry (?:point|level|zone|price)s?\b)/i,
  /\b(?:(?:initiate|open|establish|build|take|start)(?:ing)?\s+(?:an?\s+|the\s+)?(?:new\s+)?(?:long|short|starter|full|half|core)\s+position|position siz(?:e|ing) (?:of|at|to)|size (?:the|your|a) position|(?:allocat(?:e|ing)|invest(?:ing)?|cap(?:ping)?|limit(?:ing)?|keep(?:ing)?)\s+(?:\w+\s+){0,3}?(?:at\s+)?(?:no more than\s+|up to\s+|about\s+|around\s+|roughly\s+|under\s+|below\s+)?\d+(?:\.\d+)?%|(?:keep|cap|limit) (?:the |your )?position)/i,
  // Targets and valuation levels.
  /\b(?:price[- ]targets?|target prices?|fair[- ]value (?:of|at|is|estimate)|intrinsic value (?:of|at|is)|PT\s+(?:of\s+)?[$£€]?\d)/i,
  /\b(?:target|objective|upside|downside|stop[- ]loss|stop|take[- ]profit|fair[- ]value)\s+(?:of|to|at|near|around|is|:|=|toward|towards)\s*(?:about|around|roughly|approximately|~)?\s*[$£€¥]?\s?\d/i,
  /[$£€¥]\s?\d[\d,]*(?:\.\d+)?\s*(?:[kKmM]\b)?\s*(?:price\s+)?(?:target|objective|fair value)\b/i,
  /\btargets?\s+(?:of\s+)?[$£€¥]\s?\d/i,
  /\b\d+(?:\.\d+)?%\s+(?:upside|downside)\b/i
];
function bb8oIsAdvice(s) { s = String(s || "").trim(); if (!s) return false; for (var i = 0; i < BB8O_ADVICE_RES.length; i++) if (BB8O_ADVICE_RES[i].test(s)) return true; return false; }
var BB8O_LABEL_RE = /^\s*(?:strong\s+)?(?:buy|sell|hold|accumulate|trim|reduce|avoid|add|short|long|outperform|underperform|overweight|underweight|equal[- ]weight|implement|buy the dip|take profits?)\s*[.!]?\s*$/i;
// "Recommendation:" / "## Verdict" headings become "Takeaway".
function bb8oHeadings(s) { return String(s).replace(/^(\s*(?:#{1,6}\s*|\*\*|__)?\s*)(?:final\s+|overall\s+|investment\s+|our\s+)?(?:recommendations?|verdicts?)(?=\s*(?:\*\*|__)?\s*(?::|$|\n))/gim, "$1Takeaway"); }
function bb8oSentences(line) { return String(line).match(/(?:[^.!?]|[.!?](?![\s"')\]]|$))+(?:[.!?]+["')\]]*|$)\s*/g) || [line]; }
// Drops every advice sentence; keeps line breaks and the rest of the text exactly.
function bb8oAdviceText(s) {
  if (typeof s !== "string" || !s) return s;
  var out = bb8oHeadings(bb8oDeskScore(s)).split("\n").map(function (line) {
    if (!line.trim()) return line;
    var head = (line.match(/^\s*(?:[-*•]\s+|\d+[.)]\s+|#{1,6}\s+)?/) || [""])[0];
    var kept = bb8oSentences(line.slice(head.length)).filter(function (x) { return !bb8oIsAdvice(x) && !(head && bb8oIsAdvice(head + x)); }).join("").replace(/\s+$/, "");
    if (!kept.trim()) { bb8oStripStats.text++; return null; }
    if (kept !== line.slice(head.length).replace(/\s+$/, "")) bb8oStripStats.text++;
    return head + kept;
  });
  // A heading whose whole section was advice keeps the heading with the neutral line under it.
  var isHead = function (l) { return typeof l === "string" && /^\s*(?:#{1,6}\s+\S|\*\*[^*]+\*\*:?\s*$|__[^_]+__:?\s*$)/.test(l); };
  for (var i = 0; i < out.length; i++) {
    if (!isHead(out[i])) continue;
    var j = i + 1, any = false, gone = false;
    for (; j < out.length && !isHead(out[j]); j++) { if (out[j] === null) gone = true; else if (out[j].trim()) any = true; }
    if (gone && !any) { for (var k = i + 1; k < j; k++) if (out[k] === null) { out[k] = BB8O_NEUTRAL; break; } }
  }
  out = out.filter(function (l) { return l !== null; }).join("\n");
  return out.replace(/\n{3,}/g, "\n\n").replace(/^\s+$/, "");
}
var BB8O_LABEL_KEYS = { verdict: 1, recommendation: 1, rating: 1, houseview: 1, action: 1, stance: 1, call: 1, decision: 1, takeaway: 1 };
var BB8O_SKIP_KEYS = { ticker: 1, tk: 1, symbol: 1, type: 1, id: 1, priority: 1, severity: 1, sentiment: 1, documenttype: 1, company: 1, date: 1, unit: 1, metric: 1, value_raw: 1, usedsearch: 1, focustickers: 1 };
// One field: a bare rating label becomes MONITOR (the schema's own neutral value); prose loses its advice sentences;
// a field emptied by the filter gets the neutral line.
function bb8oAdviceField(v, key) {
  var lk = String(key || "").toLowerCase();
  if (typeof v !== "string" || !v.trim() || bb8oHas(BB8O_SKIP_KEYS, lk)) return v;
  if (BB8O_LABEL_RE.test(v)) { bb8oStripStats.text++; return bb8oHas(BB8O_LABEL_KEYS, lk) || v.trim().length <= 12 ? "MONITOR" : BB8O_NEUTRAL; }
  var t = bb8oAdviceText(v);
  return t && t.trim() ? t : BB8O_NEUTRAL;
}
// Every prose field of an AI output, recursively. Objects with a recommendation or verdict also get "takeaway".
function bb8oAdviceTree(x, key, depth) {
  depth = depth || 0;
  if (depth > 12 || x == null) return x;
  if (typeof x === "string") return bb8oAdviceField(x, key);
  if (Array.isArray(x)) {
    var arr = [], had = x.length > 0, firstDrop = null;
    x.forEach(function (v) {
      if (typeof v === "string") { if (!v.trim()) { arr.push(v); return; } if (BB8O_LABEL_RE.test(v)) { bb8oStripStats.text++; return; } var t = bb8oAdviceText(v); if (t && t.trim()) arr.push(t); else bb8oStripStats.text++; }
      else {
        var o2 = bb8oAdviceTree(v, key, depth + 1);
        // An action / chip whose label or action was advice is dropped whole (its value would point at the advice).
        if (o2 && typeof o2 === "object" && !Array.isArray(o2) && ["label", "action", "point"].some(function (k) { return typeof v[k] === "string" && v[k].trim() && o2[k] === BB8O_NEUTRAL; })) { bb8oStripStats.text++; if (!firstDrop) firstDrop = o2; return; }
        arr.push(o2);
      }
    });
    // Emptied by the filter: strings get the neutral line; objects keep one item with its neutral fields.
    if (had && !arr.length) { if (x.every(function (v) { return typeof v === "string"; })) arr.push(BB8O_NEUTRAL); else if (firstDrop) arr.push(firstDrop); }
    return arr;
  }
  if (typeof x !== "object") return x;
  var o = {};
  Object.keys(x).forEach(function (k) { o[k] = bb8oHas(BB8O_SKIP_KEYS, String(k).toLowerCase()) ? x[k] : bb8oAdviceTree(x[k], k, depth + 1); });
  var rk = Object.keys(o).filter(function (k) { return /^(?:recommendation|verdict)$/i.test(k) && typeof o[k] === "string"; });
  if (rk.length && !("takeaway" in o)) { var pick = rk.filter(function (k) { return /^recommendation$/i.test(k); })[0] || rk[0]; o.takeaway = o[pick]; }
  return o;
}
// Committee content is the model's text: JSON (filtered as a tree, re-serialised) or plain prose.
function bb8oAdviceCommittee(text) {
  var s = String(text == null ? "" : text), t = s.trim();
  if (/^(?:```(?:json)?\s*)?[\[{]/i.test(t)) {
    try { var j = JSON.parse(t.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "")); return JSON.stringify(bb8oAdviceTree(j, "", 0)); } catch (e) {}
  }
  var p = bb8oAdviceText(s);
  return p && p.trim() ? p : BB8O_NEUTRAL;
}
function bb8oAdviceBody(path, body) {
  if (!body || typeof body !== "object" || body.error) return body;
  var b = Object.assign({}, body);
  if (path === "/api/committee" && Array.isArray(b.content)) b.content = b.content.map(function (c) { return c && c.type === "text" && typeof c.text === "string" ? Object.assign({}, c, { text: bb8oAdviceCommittee(c.text) }) : c; });
  else if (path === "/api/lenses") { if (Array.isArray(b.lenses)) b.lenses = bb8oAdviceTree(b.lenses, "lenses", 1); if (b.intelligence && typeof b.intelligence === "object") b.intelligence = bb8oAdviceTree(b.intelligence, "intelligence", 1); }
  else if (path === "/api/intelligence" && b.intel && typeof b.intel === "object") b.intel = bb8oAdviceTree(b.intel, "intel", 1);
  else if (path === "/api/brief" && b.brief && typeof b.brief === "object") {
    var br = Object.assign({}, b.brief);
    ["headline", "summary", "houseView"].forEach(function (k) { if (typeof br[k] === "string") br[k] = bb8oAdviceField(br[k], k); });
    if (Array.isArray(br.risks)) br.risks = bb8oAdviceTree(br.risks, "risks", 1);
    bb8oBriefThemesSync(br);
    b.brief = br;
  }
  return b;
}
// ── Leading / lagging themes: measured, cited, never a positioning call ──
// An "overweight" / "underweight" theme list becomes "Leading themes" / "Lagging themes": each theme is measured on a
// free Yahoo ETF / index proxy over the last 5 sessions against the S&P 500 (SPY). It is kept only if the figure
// exists and it actually led (or lagged) SPY over that window. Themes with no proxy or no figure are left out.
var BB8O_THEME_WIN = 5;
var BB8O_THEME_MS = 10 * 60 * 1000;
var BB8O_LEAD_LABEL = "Leading themes";
var BB8O_LAG_LABEL = "Lagging themes";
var bb8oThemeCache = new Map();
var BB8O_THEMES = [
  [/\b(?:gold|bullion|xau)\b/i, "GLD", "SPDR Gold Shares"], [/\bsilver\b/i, "SLV", "iShares Silver Trust"],
  [/\b(?:cash|t-?bills?|money markets?)\b/i, "BIL", "SPDR 1-3 Month T-Bill ETF"],
  [/\b(?:long[- ]dated |long |)(?:treasur(?:y|ies)|bonds?|gilts?|duration|fixed income)\b/i, "IEF", "iShares 7-10 Year Treasury Bond ETF"],
  [/\b(?:semis?|semiconductors?|chips?|memory)\b/i, "SOXX", "iShares Semiconductor ETF"],
  [/\b(?:high[- ]beta tech|tech(?:nology)?|software)\b/i, "XLK", "Technology Select Sector SPDR"],
  [/\b(?:energy|oil|crude)\b/i, "XLE", "Energy Select Sector SPDR"], [/\b(?:financials?|banks?)\b/i, "XLF", "Financial Select Sector SPDR"],
  [/\b(?:health ?care|pharma\w*|biotech)\b/i, "XLV", "Health Care Select Sector SPDR"], [/\butilities\b/i, "XLU", "Utilities Select Sector SPDR"],
  [/\b(?:consumer )?staples\b/i, "XLP", "Consumer Staples Select Sector SPDR"], [/\b(?:consumer )?discretionary\b/i, "XLY", "Consumer Discretionary Select Sector SPDR"],
  [/\bindustrials?\b/i, "XLI", "Industrial Select Sector SPDR"], [/\bmaterials\b/i, "XLB", "Materials Select Sector SPDR"],
  [/\breal estate|\breits?\b/i, "XLRE", "Real Estate Select Sector SPDR"], [/\bcommunication/i, "XLC", "Communication Services Select Sector SPDR"],
  [/\bsmall[- ]?caps?\b/i, "IWM", "iShares Russell 2000 ETF"], [/\bnasdaq\b/i, "QQQ", "Invesco QQQ Trust"],
  [/\bemerging markets?\b/i, "EEM", "iShares MSCI Emerging Markets ETF"], [/\beurope(?:an)?\b/i, "VGK", "Vanguard FTSE Europe ETF"],
  [/\bjapan\b/i, "EWJ", "iShares MSCI Japan ETF"], [/\bchina\b/i, "MCHI", "iShares MSCI China ETF"], [/\b(?:uk|ftse)\b/i, "^FTSE", "FTSE 100"],
  [/\b(?:bitcoin|btc|crypto)\b/i, "BTC-USD", "Bitcoin (USD)"], [/\b(?:ether|ethereum)\b/i, "ETH-USD", "Ether (USD)"],
  [/\b(?:dollar|usd|greenback)\b/i, "DX-Y.NYB", "US Dollar Index (ICE, Yahoo DX-Y.NYB)"], [/\bcopper\b/i, "HG=F", "Copper futures"],
  [/\bdefensives?\b/i, "XLP", "Consumer Staples Select Sector SPDR (defensives proxy)"]
];
function bb8oThemeProxy(theme) {
  var s = String(theme || "").trim();
  if (/^[A-Z]{1,5}(?:\.[A-Z]{1,2})?$/.test(s)) return { sym: s, name: s };
  for (var i = 0; i < BB8O_THEMES.length; i++) if (BB8O_THEMES[i][0].test(s)) return { sym: BB8O_THEMES[i][1], name: BB8O_THEMES[i][2] };
  return null;
}
// Change over the last BB8O_THEME_WIN sessions from one free Yahoo daily chart (shared chart cache, then 10 min here).
async function bb8oThemeMove(sym) {
  var hit = bb8oThemeCache.get(sym), now = Date.now();
  if (hit && now - hit.at < BB8O_THEME_MS) return hit.v;
  var v = null;
  try {
    var body = null;
    if (typeof fetchYahooChart === "function") { var r0 = await fetchYahooChart(sym, "1mo", "1d"); body = r0 && !r0.unavailable ? r0.data : null; }
    var r = body && body.chart && body.chart.result && body.chart.result[0];
    var ts = (r && r.timestamp) || [], cl = (r && r.indicators && r.indicators.quote && r.indicators.quote[0] && r.indicators.quote[0].close) || [];
    var pts = [];
    for (var i = 0; i < ts.length; i++) if (Number(cl[i]) > 0) pts.push([Number(ts[i]) * 1000, Number(cl[i])]);
    if (pts.length > BB8O_THEME_WIN) {
      var a = pts[pts.length - 1 - BB8O_THEME_WIN], b = pts[pts.length - 1], meta = (r && r.meta) || {};
      var asOf = Number(meta.regularMarketTime) * 1000; if (!(asOf >= b[0])) asOf = b[0];
      v = { sym: sym, from: a[0], to: b[0], asOf: asOf, chg: Math.round((b[1] / a[1] - 1) * 10000) / 100 };
    }
  } catch (e) { v = null; }
  if (v) { bb8oThemeCache.set(sym, { at: now, v: v }); if (bb8oThemeCache.size > 64) bb8oThemeCache.delete(bb8oThemeCache.keys().next().value); }
  return v;
}
function bb8oSignPct(n) { return (n >= 0 ? "+" : "\u2212") + Math.abs(n).toFixed(2) + "%"; }
// lead: true for an overweight list (kept if it beat SPY), false for an underweight list (kept if it trailed SPY).
async function bb8oThemes(list, lead) {
  var items = [], excluded = [], seen = {};
  var names = (Array.isArray(list) ? list : String(list || "").split(/\s*[,;]\s*|\s+and\s+/)).map(function (x) { return String(typeof x === "object" && x ? (x.theme || x.name || "") : x || "").replace(/\s*\(.*$/, "").trim(); }).filter(Boolean);
  var spy = await bb8oThemeMove("SPY");
  await Promise.all(names.map(async function (theme) {
    var px = bb8oThemeProxy(theme);
    if (!px) { excluded.push({ theme: theme, reason: "no free price proxy" }); return; }
    if (seen[px.sym]) { excluded.push({ theme: theme, reason: "same proxy as " + seen[px.sym] }); return; }
    seen[px.sym] = theme;
    var m = await bb8oThemeMove(px.sym);
    if (!m || !spy) { excluded.push({ theme: theme, reason: "no measured figure" }); return; }
    var rel = Math.round((m.chg - spy.chg) * 100) / 100;
    if (lead ? !(rel > 0) : !(rel < 0)) { excluded.push({ theme: theme, reason: (lead ? "did not lead" : "did not lag") + " the S&P 500 (SPY) over the window", changePct: m.chg, benchmarkChangePct: spy.chg }); return; }
    var toLbl = bb8oDayLabel(m.to, "America/New_York");
    items.push({ theme: theme, proxy: px.sym, proxyName: px.name, window: BB8O_THEME_WIN + " sessions", from: new Date(m.from).toISOString().slice(0, 10), to: new Date(m.to).toISOString().slice(0, 10),
      changePct: m.chg, benchmark: { symbol: "SPY", name: "S&P 500 (SPY)", changePct: spy.chg }, relativePct: rel, asOf: new Date(m.asOf).toISOString(), asOfUk: bb8oUk(m.asOf),
      source: { name: "Yahoo Finance", url: "https://finance.yahoo.com/quote/" + encodeURIComponent(px.sym) + "/history/" },
      text: theme + " (" + px.sym + ") " + bb8oSignPct(m.chg) + " vs S&P 500 (SPY) " + bb8oSignPct(spy.chg) + " over the " + BB8O_THEME_WIN + " sessions to " + toLbl + " (Yahoo Finance, as of " + bb8oUk(m.asOf) + ")" });
  }));
  items.sort(function (a, b) { return lead ? b.relativePct - a.relativePct : a.relativePct - b.relativePct; });
  return { label: lead ? BB8O_LEAD_LABEL : BB8O_LAG_LABEL, items: items, excluded: excluded };
}
// Brief: overweight / underweight keep their keys (same neutral text), plus leadingThemes / laggingThemes and labels.
async function bb8oBriefThemes(br) {
  if (!br || typeof br !== "object" || Array.isArray(br.leadingThemes)) return br;
  var L = await bb8oThemes(br.overweight || [], true);
  br.leadingThemes = L.items; br.leadingThemesLabel = L.label; br.overweight = L.items.map(function (x) { return x.text; }); br.overweightLabel = L.label;
  var ex = L.excluded.map(function (x) { return Object.assign({ list: "leading" }, x); });
  if (Array.isArray(br.underweight)) {
    var G = await bb8oThemes(br.underweight, false);
    br.laggingThemes = G.items; br.laggingThemesLabel = G.label; br.underweight = G.items.map(function (x) { return x.text; }); br.underweightLabel = G.label;
    ex = ex.concat(G.excluded.map(function (x) { return Object.assign({ list: "lagging" }, x); }));
  }
  br.themesExcluded = ex;
  return br;
}
// Sync fallback (response layer): an unmeasured overweight / underweight list is never sent as a positioning call.
function bb8oBriefThemesSync(br) {
  if (!br || typeof br !== "object" || Array.isArray(br.leadingThemes)) return br;
  if (Array.isArray(br.overweight)) { br.themesExcluded = br.overweight.map(function (t) { return { list: "leading", theme: String(t), reason: "no measured figure" }; }); br.overweight = []; br.leadingThemes = []; br.leadingThemesLabel = br.overweightLabel = BB8O_LEAD_LABEL; }
  if (Array.isArray(br.underweight)) { br.themesExcluded = (br.themesExcluded || []).concat(br.underweight.map(function (t) { return { list: "lagging", theme: String(t), reason: "no measured figure" }; })); br.underweight = []; br.laggingThemes = []; br.laggingThemesLabel = br.underweightLabel = BB8O_LAG_LABEL; }
  return br;
}
// AI context text: "Overweight: Gold, Cash" / "Underweight: …" segments become measured "Leading themes" / "Lagging themes"
// segments (or are removed when nothing is measured). Only strings that contain such a segment are touched.
var BB8O_OWUW_RE = /(^|\n|\|\s*|·\s*)\**\s*(?:overweight|underweight)s?\s*\**\s*:\s*\**\s*[^|\n·]*/gi;
async function bb8oThemeLine(s) {
  if (typeof s !== "string" || !/(?:^|\n|\|\s*|·\s*)\**\s*(?:overweight|underweight)s?\s*\**\s*:/i.test(s)) return s;
  var segs = [], m; BB8O_OWUW_RE.lastIndex = 0;
  while ((m = BB8O_OWUW_RE.exec(s))) segs.push(m);
  var outs = await Promise.all(segs.map(async function (mm) {
    var lead = /^[\s*]*overweight/i.test(mm[0].slice(mm[1].length)), list = mm[0].slice(mm[1].length).replace(/^[^:]*:[\s*]*/, "");
    var T = await bb8oThemes(list, lead);
    if (!T.items.length) return "";
    var w = T.items[0];
    return T.label + " (measured, " + w.window + " to " + bb8oDayLabel(Date.parse(w.to + "T20:00:00Z"), "America/New_York") + ", vs S&P 500 (SPY) " + bb8oSignPct(w.benchmark.changePct) + "; Yahoo Finance, as of " + w.asOfUk + "): " +
      T.items.map(function (x) { return x.theme + " (" + x.proxy + ") " + bb8oSignPct(x.changePct); }).join(", ");
  }));
  var out = "", last = 0;
  segs.forEach(function (mm, i) {
    out += s.slice(last, mm.index);
    var rep = outs[i];
    if (rep) out += mm[1] + rep + (/\s*$/.exec(mm[0])[0]);
    else if (!/\|/.test(mm[1])) out += mm[1]; // a removed "| Overweight: …" segment takes its separator with it
    last = mm.index + mm[0].length;
  });
  out += s.slice(last);
  return out.replace(/\s*\|\s*(?=\||$)/g, "").replace(/^\s*\|\s*/, "").replace(/\|\s*\n/g, "\n");
}
async function bb8oThemeCtx(b) {
  if (!b || typeof b !== "object" || Array.isArray(b)) return b;
  var jobs = [];
  var walk = function (o, depth) {
    if (!o || typeof o !== "object" || depth > 8) return;
    Object.keys(o).forEach(function (k) {
      if (depth === 0 && String(k).toLowerCase() === "messages") return;
      if (depth === 0 && !bb8oHas(BB8O_CTX_FIELDS, k)) return;
      var v = o[k];
      if (typeof v === "string") { if (/(?:overweight|underweight)s?\s*\**\s*:/i.test(v)) jobs.push(bb8oThemeLine(v).then(function (t) { o[k] = t; })); }
      else walk(v, depth + 1);
    });
  };
  walk(b, 0);
  if (jobs.length) await Promise.all(jobs);
  return b;
}
// "Highest conviction on desk: XOM (84/100, Bullish)" and its variants become the plain desk-score statement.
var BB8O_DESK_RE = /\b(?:(?:[Hh]ighest|[Tt]op|[Ss]trongest|[Bb]est|[Hh]igh)[- ](?:[Cc]onviction|CONVICTION)(?:\s+(?:[Nn]ame|[Ii]dea|[Pp]ick|[Cc]all))?|[Tt]op (?:[Pp]ick|[Ii]dea)|[Bb]est [Ii]dea|[Cc]onviction (?:[Bb]uy|[Pp]ick|[Ll]ong))(?:\s+(?:on|at|across|for)\s+(?:the\s+)?[Dd]esk)?\s*(?:is|[:\-\u2013])?\s*\**\s*([A-Z][A-Z0-9.\-=^]{0,9})\**\s*\(\s*(\d{1,3})\s*\/\s*100\b[^)]*\)/g;
var BB8O_DESK_RE2 = /\b([A-Z][A-Z0-9.\-=^]{0,9})\**\s+(?:is\s+(?:the\s+|our\s+)?)?(?:(?:[Hh]ighest|[Tt]op|[Ss]trongest|[Bb]est)[- ][Cc]onviction|[Tt]op [Pp]ick|[Bb]est [Ii]dea)\s*\(\s*(\d{1,3})\s*\/\s*100\b[^)]*\)/g;
function bb8oDeskScore(s) {
  if (typeof s !== "string" || !/conviction|top pick|top idea|best idea/i.test(s)) return s;
  return s.replace(BB8O_DESK_RE, function (_m, tk, sc) { return "Top desk score: " + tk + " " + sc + "/100 (Dispatch desk score)"; })
    .replace(BB8O_DESK_RE2, function (_m, tk, sc) { return "Top desk score: " + tk + " " + sc + "/100 (Dispatch desk score)"; });
}
// Leading / Lagging themes as a numbered, citable source in bb8q's shared context (both /api/chat paths read it).
var BB8O_THEME_ASK = /\b(?:themes?|leading|lagging|leaders?|laggards?|lead(?:s|ing)?|lag(?:s|ging)?|outperform\w*|underperform\w*|over-?weight|under-?weight|brief|sectors?|rotation|relative)\b/i;
function bb8oThemeSegs(body) {
  var segs = [];
  var walk = function (o, depth) {
    if (!o || typeof o !== "object" || depth > 8) return;
    Object.keys(o).forEach(function (k) {
      if (depth === 0 && (String(k).toLowerCase() === "messages" || !bb8oHas(BB8O_CTX_FIELDS, k))) return;
      var v = o[k];
      if (typeof v === "string") { var m; BB8O_OWUW_RE.lastIndex = 0; while ((m = BB8O_OWUW_RE.exec(v))) { var seg = m[0].slice(m[1].length); segs.push({ lead: /^[\s*]*overweight/i.test(seg), list: seg.replace(/^[^:]*:[\s*]*/, "").trim() }); } }
      else walk(v, depth + 1);
    });
  };
  walk(body, 0);
  return segs;
}
function bb8oUpDown(n) { return Math.abs(n) < 0.005 ? "unchanged" : (n < 0 ? "down " : "up ") + Math.abs(n).toFixed(2) + "%"; }
async function bb8oThemeFacts(ctx, body) {
  if (!ctx || !Array.isArray(ctx.facts) || !Array.isArray(ctx.sources) || typeof bb8qSrc !== "function") return ctx;
  if (ctx.facts.some(function (f) { return f.id === "themes"; })) return ctx;
  var segs = bb8oThemeSegs(body);
  if (!segs.length) return ctx;
  var q = String(ctx.q || (typeof bb8pQuestion === "function" ? bb8pQuestion(body) : "") || "");
  var named = segs.some(function (s) { return s.list.split(/\s*[,;]\s*|\s+and\s+/).some(function (n) { n = n.trim(); return n.length > 2 && q.toLowerCase().indexOf(n.toLowerCase()) >= 0; }); });
  if (!BB8O_THEME_ASK.test(q) && !named) return ctx;
  var race = function (p) { return typeof bb8q2Race === "function" ? bb8q2Race(p) : p; };
  var res = await race(Promise.all(segs.map(function (s) { return bb8oThemes(s.list, s.lead); })));
  // One source for both lists, so the shared S&P 500 (SPY) benchmark figure is carried by exactly one citable source.
  var parts = [], items = [], seen = {}, first = null;
  (res || []).forEach(function (T, i) {
    var kind = segs[i].lead ? "leading" : "lagging";
    if (!T || !T.items.length || seen[kind]) return;
    seen[kind] = 1;
    if (!first) first = T.items[0];
    parts.push(T.label + ": " + T.items.map(function (x) { return x.theme + " (" + x.proxy + ", " + x.proxyName + ") " + bb8oUpDown(x.changePct); }).join("; "));
    T.items.forEach(function (x) { items.push({ list: kind, theme: x.theme, proxy: x.proxy, changePct: x.changePct, spyChangePct: x.benchmark.changePct, asOfUk: x.asOfUk, source: x.source.url }); });
  });
  if (!first) return ctx;
  var toLbl = bb8oDayLabel(Date.parse(first.to + "T20:00:00Z"), "America/New_York");
  var label = parts.length > 1 ? "Leading and lagging themes" : parts[0].split(":")[0];
  var text = label + " (Dispatch measurement from Yahoo Finance daily closes over the " + first.window + " to " + toLbl + ", against the S&P 500 (SPY), which is " + bb8oUpDown(first.benchmark.changePct) + " over the same window). " +
    parts.join(". ") + ". As of " + first.asOfUk + ".";
  var src = bb8qSrc("Yahoo Finance chart (" + label + ")", first.source.url, Date.parse(first.asOf) || Date.now(), text.replace(/\.$/, ""), "themes");
  src.bb8oThemes = items;
  ctx.facts.push({ id: "themes", text: text, src: src });
  ctx.sources.push(src);
  return ctx;
}
// The change tag names the last session's day ("Fri"), in the listing's own time zone, never today's.
function bb8oChangeDay(f, sym) {
  try {
    var ms = bb8oTsMs(f.ts); if (!ms) return f;
    var spec = bb8oSpec(sym) || {}, tz = spec.tz || (/-USD$|^BTC$|^ETH$/i.test(String(sym)) ? "Europe/London" : "America/New_York");
    var full = bb8oDayLabel(ms, tz);
    f.changeDay = full.split(" ")[0]; f.changeDayLabel = full;
    if (f.feed && typeof f.feed === "object") { f.feed.changeDay = f.changeDay; f.feed.changeDayLabel = full; }
  } catch (e) {}
  return f;
}
// BTC / crypto: one canonical change baseline, rolling 24h. CoinGecko's 24h change when a fresh (10 min) CoinGecko
// simple-price body is already in the server's last-good cache, else the Yahoo rolling-24h basis. Labelled "24h".
var BB8O_CG_IDS = { BTC: "bitcoin", ETH: "ethereum", SOL: "solana", XRP: "ripple", BNB: "binancecoin", DOGE: "dogecoin", ADA: "cardano" };
function bb8oCg24(id) {
  try {
    if (typeof coinGeckoLastGood === "undefined" || !coinGeckoLastGood || typeof coinGeckoLastGood.forEach !== "function") return null;
    var best = null;
    coinGeckoLastGood.forEach(function (body, key) {
      if (!/^\/simple\/price\?/.test(String(key)) || !body || !body[id]) return;
      var r = body[id], pct = Number(r.usd_24h_change), at = Number(r.last_updated_at) * 1000 || (typeof coinGeckoLastGoodAt !== "undefined" ? Number(coinGeckoLastGoodAt.get(key)) : 0) || 0;
      if (!isFinite(pct) || !(Number(r.usd) > 0)) return;
      if (!best || at > best.at) best = { pct: pct, usd: Number(r.usd), at: at };
    });
    return best && Date.now() - best.at < 10 * 60 * 1000 ? best : null;
  } catch (e) { return null; }
}
function bb8oCrypto24h(f, sym) {
  var s = String(sym || "").toUpperCase().replace(/-USD$|USDT?$/, "");
  if (!BB8O_CG_IDS[s] || !/^(?:BTC|ETH|SOL|XRP|BNB|DOGE|ADA)(?:-USD)?$/.test(String(sym || "").toUpperCase())) return f;
  var p = Number(f.p); if (!(p > 0)) return f;
  var cg = bb8oCg24(BB8O_CG_IDS[s]), o = Object.assign({}, f);
  if (cg) {
    var prev = p / (1 + cg.pct / 100);
    o.prev = prev; o.change = p - prev; o.c = cg.pct; o.changePct = cg.pct; o.basis = "rolling_24h"; o.changeAvailable = true;
    o.baseline = "24h"; o.baselineSource = "CoinGecko 24h change"; o.baselineAsOf = new Date(cg.at).toISOString(); o.asOfUk = o.asOfUk || bb8oUk(cg.at); o.baselineAsOfUk = bb8oUk(cg.at);
  } else if (Number(f.prev) > 0) {
    o.change = p - Number(f.prev); o.c = (o.change / Number(f.prev)) * 100; o.changePct = o.c;
    o.baseline = "24h"; o.baselineSource = f.basis === "rolling_24h" ? "Yahoo 15-minute bars, rolling 24h" : "previous print 24h basis"; o.baselineAsOfUk = bb8oUk(bb8oTsMs(f.ts) || Date.now());
  } else return f;
  if (!o.asOfUk) o.asOfUk = bb8oUk(bb8oTsMs(f.ts) || Date.now());
  return o;
}
// "Gold spot" may only ever carry XAU data. A reply line or meta.quote that labels a non-XAU price as gold spot is
// relabelled with the subject's own symbol / name when the figure is the subject's price, else the clause is dropped.
var BB8O_SPOT_RE = /\b(Gold spot)(\s*(?:\(reference\)\s*)?(?:is\s+(?:at|trading\s+(?:at|near))\s+|at\s+|:\s*)?)\$\s?([\d,]+(?:\.\d+)?)/gi;
function bb8oXauRef(st) {
  try { var c = st && st.bb8qCtx; if (c && c.spot && c.spot.q && Number(c.spot.q.p) > 0) return Number(c.spot.q.p); } catch (e) {}
  var g = bb8oGood.get("XAU") || bb8oGood.get("XAUUSD=X");
  return g && Number(g.p) > 0 ? Number(g.p) : null;
}
function bb8oSubject(st) {
  try { var m = st && st.bb8eMoveR; if (m && m.q && Number(m.q.p) > 0 && !/^(?:XAU|GC=F|GOLD)$/i.test(String(m.base || ""))) return { sym: m.base || m.ysym, name: m.q.name || m.base, p: Number(m.q.p) }; } catch (e) {}
  return null;
}
function bb8oGoldSpotGuard(text, st) {
  if (typeof text !== "string" || !/gold spot/i.test(text)) return text;
  var xau = bb8oXauRef(st), subj = bb8oSubject(st);
  var near = function (a, b, tol) { return a > 0 && b > 0 && Math.abs(a / b - 1) <= tol; };
  var bad = false;
  var out = text.replace(BB8O_SPOT_RE, function (m, lab, mid, num) {
    var v = Number(String(num).replace(/,/g, ""));
    if (xau ? near(v, xau, 0.03) : v > 1000) return m;
    if (subj && near(v, subj.p, 0.005)) return subj.sym + (subj.name && subj.name !== subj.sym ? " (" + subj.name + ")" : "") + mid + "$" + num;
    bad = true; return m;
  });
  if (!bad) return out;
  return out.split("\n").map(function (line) {
    if (!/gold spot/i.test(line)) return line;
    return bb8oSentences(line).filter(function (s) {
      var m2; BB8O_SPOT_RE.lastIndex = 0;
      while ((m2 = BB8O_SPOT_RE.exec(s))) { var v = Number(String(m2[3]).replace(/,/g, "")); if (!(xau ? near(v, xau, 0.03) : v > 1000)) return false; }
      return true;
    }).join(" ").replace(/\s+$/, "");
  }).filter(function (l, i, a) { return l.trim() || (a[i - 1] && a[i - 1].trim()); }).join("\n");
}
// ── bb8o answer post-pass (QA 1:44): one document pass on BOTH /api/chat paths, inside bb8qFinish (bb8jAssemble),
// so stream and JSON apply exactly the same numeric and sentence drops. Works on bb8q's token form (⟦i⟧ = doc.srcs[i]).
var BB8O_TOK = /\u27e6(\d+)\u27e7/g;
var BB8O_UP = /\b(up|rose|risen|gained|higher|climbed|advanced|increased|rallied)\b/i;
var BB8O_DN = /\b(down|fell|fallen|lost|lower|dropped|declined|decreased|slid|slipped)\b/i;
var BB8O_DIRW = /\b(up|down|rose|risen|fell|fallen|gained|lost|higher|lower|climbed|dropped|declined|advanced|increased|decreased|rallied|slid|slipped)\b/i;
var BB8O_FLIP = { up: "down", down: "up", rose: "fell", fell: "rose", risen: "fallen", fallen: "risen", gained: "lost", lost: "gained", higher: "lower", lower: "higher", climbed: "dropped", dropped: "climbed", declined: "advanced", advanced: "declined", increased: "decreased", decreased: "increased", rallied: "slid", slid: "rallied", slipped: "rallied" };
var BB8O_FILLER = /geopolitic|defensive (?:sectors?|assets?|names|stocks)|central bank (?:statements?|communications?|commentary)|keep an eye|closely monitor|(?:it will be|remains?) (?:important|crucial|key) to|investors (?:will|may|should|are advised|might)|will likely remain|could significantly impact|preference for safety|seeking safety|amid uncertainty|market (?:sentiment|dynamics) (?:towards|moving forward)|it would be beneficial|shed light on|navigate these conditions|forthcoming economic data|interplay with/i;
var BB8O_TAIL = /,\s*(?:indicating|suggesting|reflecting|signalling|signaling|which (?:may|could|might|suggests?|indicates?|reflects?))\b[^\u27e6\d]*?(?=[.!?]?\s*(?:\u27e6|$))/gi;
var BB8O_METRIC = [
  { id: "beta", q: /\bbeta\b/i, s: /\bbeta\b/i },
  { id: "pe", q: /\b(?:p\s*\/\s*e|pe ratio|price[- ]to[- ]earnings|earnings multiple|valuation multiple)\b/i, s: /\bP\s*\/\s*E\b|price[- ]to[- ]earnings|\bPE\b/i },
  { id: "dividend", q: /\bdividends?\b|\bpayout\b/i, s: /\bdividend|\bpayout\b/i },
  { id: "mcap", q: /market (?:cap|capitali[sz]ation)|\bmcap\b/i, s: /market (?:cap|capitali[sz]ation)|\bvalued at\b/i },
  { id: "eps", q: /\bEPS\b|earnings per share/i, s: /\bEPS\b|earnings per share/i },
  { id: "yield", q: /\byield\b/i, s: /\byield\b/i }
];
var BB8O_WEEK_Q = /\b(?:this|the coming|next|the) week\b|\bweek ahead\b|\bweekly outlook\b/i;
function bb8oN(s) { var v = Number(String(s).replace(/[$,\s]/g, "")); return isFinite(v) ? v : NaN; }
function bb8oPct2(v) { return Math.abs(v).toFixed(2) + "%"; }
// Sentences with their trailing citation tokens attached (bb8q writes "… 1.97%. ⟦2⟧ Next sentence").
var BB8O_ABBR = /(?:\b(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|Inc|Co|Corp|Ltd|vs|No|St|Mr|Ms|Dr|approx|est|e\.g|i\.e|U\.S|U\.K)|\b[A-Z])$/;
function bb8oSplit(line) {
  var s = String(line), out = [], cur = "", inQ = false;
  for (var i = 0; i < s.length; i++) {
    var ch = s.charAt(i); cur += ch;
    if (ch === '"' || ch === "\u201c" || ch === "\u201d") inQ = ch === "\u201c" ? true : ch === "\u201d" ? false : !inQ;
    if (inQ || !/[.!?]/.test(ch)) continue;
    var nx = s.charAt(i + 1);
    if (nx && !/\s/.test(nx)) continue;
    if (ch === "." && BB8O_ABBR.test(cur.slice(0, -1))) continue;
    while (i + 1 < s.length && /\s/.test(s.charAt(i + 1))) { cur += s.charAt(++i); }
    out.push(cur); cur = "";
  }
  if (cur) out.push(cur);
  var res = [];
  out.forEach(function (x) {
    var m = /^(\s*(?:\u27e6\d+\u27e7\s*)+)/.exec(x);
    if (m && res.length) { res[res.length - 1] += m[1]; x = x.slice(m[1].length); }
    if (x) res.push(x);
  });
  return res.length ? res : [s];
}
function bb8oToks(s) { var o = []; String(s).replace(BB8O_TOK, function (m, k) { o.push(Number(k)); return m; }); return o; }
function bb8oNums(s) { return (String(s).replace(BB8O_TOK, " ").replace(/\/\s*100\b/g, " ").replace(/\b(?:19|20)\d{2}\b/g, " ").replace(/\b\d{1,2}:\d{2}\b/g, " ").match(/\d[\d,]*(?:\.\d+)?%?/g) || []).filter(function (x) { return /[.,%]/.test(x); }); }
// P0 (a): direction and % from the two cited numbers, in code. dirs: [{from, to, pct}] (ctx.bb8oDir).
function bb8oDirFix(s, dirs) {
  var t = String(s), S = null, E = null, m;
  if ((m = /\bfrom\s+\$?([\d,]+(?:\.\d+)?)(?:\s*\([^)]*\))?\s+to\s+\$?([\d,]+(?:\.\d+)?)/i.exec(t))) { S = bb8oN(m[1]); E = bb8oN(m[2]); }
  else if ((m = /\bclose of\s+\$?([\d,]+(?:\.\d+)?)/i.exec(t)) || (m = /\bfrom\s+\$?([\d,]+(?:\.\d+)?)/i.exec(t))) {
    S = bb8oN(m[1]);
    var to = /\b(?:to|at|now)\s+\$?([\d,]+(?:\.\d+)?)/i.exec(t.slice(m.index + m[0].length));
    if (to && bb8oN(to[1]) > 0 && Math.abs(bb8oN(to[1]) / S - 1) < 0.9) E = bb8oN(to[1]);
    else (dirs || []).some(function (d) { if (Math.abs(d.from - S) < 0.006) { E = d.to; return true; } return false; });
  } else if ((m = /\bprevious close (?:of )?\$?([\d,]+(?:\.\d+)?)/i.exec(t))) {
    S = bb8oN(m[1]);
    var at = /\b(?:to|at)\s+\$?([\d,]+(?:\.\d+)?)/i.exec(t);
    if (at) E = bb8oN(at[1]);
  }
  if (!(S > 0) || !(E > 0) || S === E) return { s: t, fixed: false };
  var pct = (E / S - 1) * 100;
  if (Math.abs(pct) < 0.005) return { s: t, fixed: false };
  var w = BB8O_DIRW.exec(t);
  if (!w) return { s: t, fixed: false };
  var saysUp = BB8O_UP.test(w[1]), right = pct > 0;
  var after = t.slice(w.index + w[0].length), pm = /^(\s*(?:by\s+)?)(-?\d+(?:\.\d+)?)%/.exec(after);
  var pctOk = !pm || Math.abs(Math.abs(Number(pm[2])) - Math.abs(pct)) < 0.06;
  if (saysUp === right && pctOk) return { s: t, fixed: false };
  var word = saysUp === right ? w[1] : (BB8O_FLIP[w[1].toLowerCase()] || (right ? "up" : "down"));
  if (/^[A-Z]/.test(w[1])) word = word.charAt(0).toUpperCase() + word.slice(1);
  var rest = pm ? pm[1] + bb8oPct2(pct) + after.slice(pm[0].length) : after;
  return { s: t.slice(0, w.index) + word + rest, fixed: true, from: S, to: E, pct: pct };
}
// hay(s) -> the cited source text for sentence s. A contradicting claim is corrected only when both numbers are
// cited figures (in the sentence's sources, or a code-computed timeframe pair); otherwise the sentence is dropped.
function bb8oInHay(v, hay) { return (String(hay || "").replace(/,/g, "").match(/\d+(?:\.\d+)?/g) || []).some(function (x) { return Math.abs(Number(x) - v) < 0.006; }); }
function bb8oDirGuard(text, dirs, hay) {
  var n = 0, dropped = [];
  var out = String(text).split("\n").map(function (line) {
    return bb8oSplit(line).map(function (s) {
      var r = bb8oDirFix(s, dirs); if (!r.fixed) return s;
      var h = typeof hay === "function" ? hay(s) : null;
      var pair = (dirs || []).some(function (d) { return Math.abs(d.from - r.from) < 0.006 && Math.abs(d.to - r.to) < 0.006; });
      if (h != null && !pair && !(bb8oInHay(r.from, h) && bb8oInHay(r.to, h))) { dropped.push(s.replace(BB8O_TOK, "").trim()); return ""; }
      n++; return r.s;
    }).join("");
  }).join("\n");
  return { text: out, fixed: n, dropped: dropped };
}
function bb8oSrcLabel(s) {
  if (!s || typeof s !== "object") return s;
  var p = s.bb8qProxy, d = String(s.detail || "");
  var lab = p && p.label ? p.label + " (" + p.sym + ")" : (d.split(/\s(?:is|are|was|were|has|had)\s|[,;:]\s/)[0] || "").replace(/^Our /, "").slice(0, 80);
  if (!lab || lab.length < 3) lab = s.name || "Source";
  lab = lab.charAt(0).toUpperCase() + lab.slice(1);
  if (!s.label) s.label = lab + (p ? " (proxy)" : "");
  if (!s.title) s.title = (s.name || "Source") + (s.label && s.label !== s.name ? " · " + s.label : "");
  return s;
}
// An uncited sentence gets the [n] of the one source that carries all of its figures (same line first), else none.
function bb8oFigs(s) { return (String(s).replace(BB8O_TOK, " ").replace(/\b(?:19|20)\d{2}\b/g, " ").replace(/\b\d{1,2}:\d{2}\b/g, " ").replace(/,/g, "").match(/\d+(?:\.\d+)?/g) || []).map(Number); }
function bb8oReCite(body, lineToks, doc, after) {
  var figs = bb8oFigs(body).filter(function (v) { return v !== 0; });
  var hayOf = function (src) { return (typeof bb8qSrcText !== "undefined" && bb8qSrcText.get(src)) || (src && src.detail) || ""; };
  var words = (String(body).toLowerCase().match(/[a-z]{5,}/g) || []);
  var fits = function (k) {
    var src = doc.srcs[k]; if (!src) return false; var h = hayOf(src);
    if (figs.length) return figs.every(function (v) { return bb8oInHay(v, h); });
    if (words.length < 3) return false;
    var hl = h.toLowerCase(), hit = words.filter(function (w) { return hl.indexOf(w) >= 0; }).length;
    return hit / words.length >= 0.6;
  };
  var seen = {}, cand = lineToks.filter(function (k) { if (seen[k]) return false; seen[k] = 1; return true; });
  var same = cand.filter(fits); if (same.length === 1 || (same.length && !figs.length)) return same[0];
  // bb8q's line-level cite: a figure sentence before the line's one source takes that source's [n]
  if (figs.length && cand.length === 1 && after) return cand[0];
  if (!figs.length) return null;
  var best = null, bh = 0, tie = false;
  for (var k = 0; k < doc.srcs.length; k++) {
    var src = doc.srcs[k]; if (!src) continue; var h = hayOf(src);
    var hit = figs.filter(function (v) { return bb8oInHay(v, h); }).length;
    if (hit > bh) { best = k; bh = hit; tie = false; } else if (hit && hit === bh) tie = true;
  }
  if (best != null && !tie && bh >= Math.max(1, Math.ceil(figs.length / 2))) return best;
  // a descriptive source (bb8's server lines: "trailing P/E (TTM) and forward P/E, refreshed on request") whose
  // words the sentence carries: the one such source is cited
  var low = String(body).toLowerCase(), desc = [];
  for (var j = 0; j < doc.srcs.length; j++) {
    var hj = hayOf(doc.srcs[j]); if (!hj || /\d\.\d|\d%/.test(hj)) continue;
    var ws = (hj.toLowerCase().match(/[a-z\/]{4,}/g) || []).filter(function (w) { return !/^(?:from|with|that|this|refreshed|request|last|price|change|session)$/.test(w); });
    if (ws.length && ws.filter(function (w) { return low.indexOf(w) >= 0; }).length >= Math.min(2, Math.max(1, ws.length - 1))) desc.push(j);
  }
  return desc.length === 1 ? desc[0] : null;
}
function bb8oUkHm(ms) { try { return typeof bb8qUk === "function" ? bb8qUk(ms) : bb8oUk(ms); } catch (e) { return ""; } }
function bb8oPost(doc, st) {
  var ctx = (st && st.bb8qCtx) || {}, q = String(ctx.q || ""), stat = { dir: 0, dropped: [], moved: null, outlook: false, sp: null, proxied: 0, stamps: 0 };
  var srcOf = function (i) { return doc.srcs[i] || null; };
  var lines = String(doc.body).split("\n");
  var firstDone = false, seenNums = {};
  var isFixed = function (l) { return /^\s*(?:In short:|For context:|Sources:|#|\|)/.test(l) || /:\s*$/.test(l.trim()); };
  // (a) numeric direction guard
  var hayOf = function (s) { var ks = bb8oToks(s), L = ks.length ? ks.map(srcOf) : doc.srcs; return L.filter(Boolean).map(function (x) { return (typeof bb8qSrcText !== "undefined" && bb8qSrcText.get(x)) || x.detail || ""; }).join(" "); };
  var dg = bb8oDirGuard(lines.join("\n"), ctx.bb8oDir || [], hayOf); stat.dir = dg.fixed; dg.dropped.forEach(function (s) { stat.dropped.push({ why: "direction claim on an uncited start or end figure", s: s }); }); lines = dg.text.split("\n");
  // (e) citation hygiene, sentence by sentence
  lines = lines.map(function (line) {
    if (!line.trim() || /^\s*(?:In short:|Sources:|\|)/.test(line)) return line;
    var keepAll = isFixed(line), lineToks = bb8oToks(line);
    var sents = bb8oSplit(line).map(function (s) {
      var toks = bb8oToks(s);
      // the regime source is citable only for the regime score
      toks.forEach(function (k) { var src = srcOf(k); if (src && src.bb8qKey === "regime" && !/regime|risk-?(?:on|off)|score|\/100|mood/i.test(s.replace(BB8O_TOK, ""))) s = s.replace(new RegExp("\\s*\\u27e6" + k + "\\u27e7", "g"), ""); });
      s = s.replace(BB8O_TAIL, "");
      return s;
    });
    var lastTokAt = -1; sents.forEach(function (s, i) { if (bb8oToks(s).length) lastTokAt = i; });
    sents = sents.map(function (s, idx) {
      var body = s.replace(BB8O_TOK, "").trim(), cited = bb8oToks(s).length > 0, nums = bb8oNums(s);
      if (!body) return null;
      var first = !firstDone; firstDone = true;
      if (BB8O_FILLER.test(body) && !nums.length) { stat.dropped.push({ why: "filler", s: body }); return null; }
      if (!cited && !first && !/\b(?:don't|do not|doesn't|not (?:in|available|have|quote|reported|compared))\b|\bno (?:[A-Za-z\- ]{0,30})(?:figures?|data|dates?|catalysts?|cause)\b/i.test(body)) {
        var k2 = bb8oReCite(body, lineToks, doc, idx < lastTokAt);
        if (k2 != null) { s = s.replace(/(\s*)$/, " \u27e6" + k2 + "\u27e7$1"); cited = true; stat.recited = (stat.recited || 0) + 1; }
        else if (!keepAll) { stat.dropped.push({ why: "uncited", s: body }); return null; }
      }
      // de-duplicate a repeated proxy / figure line: every figure already given earlier, same source
      if (nums.length && cited && !first) {
        var all = nums.every(function (x) { return seenNums[x.replace(/[,%]/g, "")]; });
        if (all) { stat.dropped.push({ why: "repeat", s: body }); return null; }
      }
      nums.forEach(function (x) { seenNums[x.replace(/[,%]/g, "")] = 1; });
      return s;
    }).filter(function (s) { return s != null; });
    return sents.join("").replace(/\s+$/, "");
  });
  // (h) one S&P figure per answer: SPY or ^GSPC, never both
  var SPFIG = "[^.;:]{0,60}?(?:-?\\d[\\d,]*\\.\\d+%?|\\d+(?:\\.\\d+)?%)";
  var kind = function (s) { var b = s.replace(BB8O_TOK, ""); if (new RegExp("\\bSPY\\b" + SPFIG).test(b) || new RegExp("-?\\d[\\d,.]*%[^.;]{0,40}\\bSPY\\b").test(b)) return "SPY"; if (new RegExp("(?:\\^GSPC|S&P\\s*500)(?!'s move)" + SPFIG).test(b)) return "GSPC"; return null; };
  var OTHER = /\((?!SPY\b|\^GSPC\b|S&P)[A-Z^][A-Z0-9.=^\-]{1,9}\b|\b(?:lagged|ahead of|behind|outperform\w*|underperform\w*)\b/;
  var kinds = {}, firstKind = null, rich = {};
  lines.forEach(function (l) { bb8oSplit(l).forEach(function (s) { var k = kind(s); if (!k) return; kinds[k] = 1; if (!firstKind) firstKind = k; if (OTHER.test(s.replace(BB8O_TOK, "")) || /^\s*In short:/.test(l)) rich[k] = 1; }); });
  if (kinds.SPY && kinds.GSPC) {
    var keep = rich.SPY && !rich.GSPC ? "SPY" : rich.GSPC && !rich.SPY ? "GSPC" : firstKind;
    stat.sp = keep;
    lines = lines.map(function (l) {
      if (/^\s*In short:/.test(l)) return l;
      return bb8oSplit(l).filter(function (s) { var k = kind(s); if (k && k !== keep && !OTHER.test(s.replace(BB8O_TOK, ""))) { stat.dropped.push({ why: "second S&P figure", s: s.replace(BB8O_TOK, "").trim() }); return false; } return true; }).join("").replace(/\s+$/, "");
    });
  } else stat.sp = kinds.SPY ? "SPY" : kinds.GSPC ? "GSPC" : null;
  // (f) proxies are labelled as proxies in the text
  lines = lines.map(function (l) {
    return bb8oSplit(l).map(function (s) {
      var toks = bb8oToks(s); if (!toks.length || /\bproxy|proxies\b/i.test(s)) return s;
      var px = toks.map(srcOf).filter(function (x) { return x && x.bb8qProxy; });
      if (!px.length || px.length !== toks.map(srcOf).filter(Boolean).length) return s;
      stat.proxied++;
      if (/^(\s*)What we do have, from/i.test(s)) return s.replace(/What we do have, from/i, "What we do have, as proxies, from");
      var lead = /^(\s*)(?:The |the )?/.exec(s)[1];
      var rest = s.slice(lead.length).replace(/^The /, "the ");
      return lead + "As a proxy, " + rest;
    }).join("");
  });
  // (g) a headline as-of is never earlier than the cited source's own as-of: use the source time
  lines = lines.map(function (l, li) {
    return l.replace(/^(.*?(?:latest move|What we do have[^:]*?)\b[^:]*?\bas of )([A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4}, \d{2}:\d{2} UK)(:)/, function (m, a, hm, c) {
      var scope = l; if (!bb8oToks(l).length) { for (var j = li + 1; j < lines.length; j++) if (lines[j].trim()) { scope = lines[j]; break; } }
      var best = 0; bb8oToks(scope).forEach(function (k) { var src = srcOf(k), t = src && Date.parse(src.asOf); if (t > best) best = t; });
      if (!best) return m;
      var txt = bb8oUkHm(best); if (!txt || txt === hm) return m;
      stat.stamps++; return a + txt + c;
    });
  });
  // (c) intent beats template: a direct factual question is answered first, with its cited value
  var met = BB8O_METRIC.filter(function (x) { return x.q.test(q); })[0];
  if (met && !(met.id === "yield" && /dividend/i.test(q))) {
    var hit = null;
    lines.some(function (l, li) { var ss = bb8oSplit(l); return ss.some(function (s, si) { if (met.s.test(s) && bb8oToks(s).length && (/\d/.test(s.replace(BB8O_TOK, "")) || /\bno\b|\bdoes not\b|\bdoesn't\b/i.test(s))) { hit = { li: li, si: si, s: s }; return true; } return false; }); });
    if (!hit && ctx.bb8oMetric && ctx.bb8oMetric.id === met.id && ctx.bb8oMetric.src) {
      lines.unshift(ctx.bb8oMetric.text + " " + bb8qTok(doc, ctx.bb8oMetric.src), "");
      stat.moved = met.id + " (server fact)";
    } else if (hit && !(hit.si === 0 && lines.slice(0, hit.li).every(function (l) { return !l.trim() || /:\s*$/.test(l) && !/\d\.\d|%/.test(l.replace(/\d{2}:\d{2}/g, "")); }))) {
      var ss = bb8oSplit(lines[hit.li]); ss.splice(hit.si, 1); lines[hit.li] = ss.join("").replace(/\s+$/, "");
      lines.unshift(hit.s.replace(/^\s+|\s+$/g, ""), "");
      stat.moved = met.id;
    }
  }
  // (d) "this week" questions: an outlook built only from citable facts, never a forecast
  if (BB8O_WEEK_Q.test(q) && !lines.some(function (l) { return /^\s*Outlook for this week/i.test(l); })) {
    var parts = [], lv = ctx.bb8oLevels, ev = ctx.bb8oEvents || [];
    if (lv && lv.src && /\^GSPC|S&P/.test(lv.label) && stat.sp === "SPY") { stat.levelsSkipped = "one S&P figure per answer (SPY kept)"; lv = null; }
    if (lv && lv.src) parts.push("the " + lv.n + "-session range for " + lv.label + " is " + lv.fmt(lv.low) + " (low) to " + lv.fmt(lv.high) + " (high), " + lv.span + " " + bb8qTok(doc, lv.src));
    ev.forEach(function (e) { parts.push(e.text + " " + bb8qTok(doc, e.src)); });
    var line;
    if (parts.length) line = "Outlook for this week (from our data, not a forecast): " + parts.join("; ") + "." + (ev.length ? "" : " No scheduled Fed, economic-data or earnings dates for this week are in our feed.");
    else line = "Outlook for this week: nothing in our feed is citable for the week ahead (no scheduled Fed, data or earnings dates and no measured range), so we give no outlook.";
    var si2 = -1; for (var z = lines.length - 1; z >= 0; z--) if (/^\s*In short:/.test(lines[z])) { si2 = z; break; }
    if (si2 >= 0) lines.splice(si2, 0, line, ""); else lines.push("", line);
    stat.outlook = true;
  }
  // a header line ("For context:", "Peer comparisons as of …:") left with nothing under it goes too
  lines = lines.filter(function (l, i, a) {
    if (!/:\s*$/.test(l) || /^\s*In short:/.test(l)) return true;
    var nx = a[i + 1]; return !!(nx && nx.trim() && !/:\s*$/.test(nx));
  });
  doc.body = lines.filter(function (l, i, a) { return !(l.trim() === "" && (i === 0 || a[i - 1].trim() === "")); }).join("\n");
  return stat;
}
// P0 (a) in the context: every timeframe line carries both cited numbers and a code-computed direction and %.
function bb8oDirCtx(ctx) {
  if (!ctx || !ctx.tf || !ctx.tf.text) return;
  var m = /\bto\s+\$?([\d,]+(?:\.\d+)?)\s+now\b/.exec(ctx.tf.text), E = m ? bb8oN(m[1]) : NaN;
  if (!(E > 0)) return;
  var dirs = [], money = /\bto \$/.test(ctx.tf.text), f2 = function (v) { return (money ? "$" : "") + bb8qNum(v, 2); };
  var fix = function (t) {
    var s = /close of\s+\$?([\d,]+(?:\.\d+)?)/.exec(t) || /\bfrom [^$\d]*\$?([\d,]+(?:\.\d+)?)/.exec(t), S = s ? bb8oN(s[1]) : NaN;
    if (!(S > 0)) return t;
    var pct = (E / S - 1) * 100, word = Math.abs(pct) < 0.005 ? "unchanged" : (pct < 0 ? "down " : "up ") + bb8oPct2(pct);
    dirs.push({ from: S, to: E, pct: pct });
    var u = t.replace(/\b(?:down|up) \d+(?:\.\d+)?%|\bunchanged\b/, word);
    if (!/\bto\s+\$?[\d,]+(?:\.\d+)?\s+now\b/.test(u)) u = u.replace(/(close of\s+\$?[\d,]+(?:\.\d+)?)/, "$1 to " + f2(E) + " now");
    return u;
  };
  ctx.tf.text = fix(ctx.tf.text);
  if (Array.isArray(ctx.tfMore)) ctx.tfMore = ctx.tfMore.map(fix);
  (ctx.facts || []).forEach(function (f) { if (f.src === ctx.tf.src) f.text = ctx.tf.text; });
  if (ctx.tf.src) { var d = ctx.tf.text.replace(/\.$/, "") + (ctx.tfMore && ctx.tfMore.length ? "; " + ctx.tfMore.join(" ") : ""); ctx.tf.src.detail = d.slice(0, 600); bb8qSrcText.set(ctx.tf.src, d); }
  ctx.bb8oDir = dirs;
}
// P1 (c): direct factual questions about an equity get the cited value as a server fact (Yahoo Finance quoteSummary,
// through bb8l's shared 30 s lookup, so the card's beta / earnings requests are reused; no new fetch path).
async function bb8oMetricCtx(ctx, st) {
  var q = String((ctx && ctx.q) || ""), met = BB8O_METRIC.filter(function (x) { return x.q.test(q); })[0];
  var base = st && st.bb8eBase;
  if (!met || !base || /^(?:XAU|GC=F|GOLD|BTC|ETH)/i.test(base) || /^\^|=/.test(base) || met.id === "beta" || met.id === "pe") return;
  if (met.id === "yield" && !/dividend/i.test(q) && !/\b(?:stock|share|shares|dividend)\b/i.test(q)) return;
  if (typeof bb8lYahooShared !== "function") return;
  var race = function (p) { return typeof bb8q2Race === "function" ? bb8q2Race(p) : p; };
  var ysym = typeof bb8bYahooSym === "function" ? bb8bYahooSym(base) : base;
  var y = await race(bb8lYahooShared(ysym));
  if (!y || typeof y !== "object" || typeof rt32R !== "function") return;
  var sd = y.summaryDetail || {}, ks = y.defaultKeyStatistics || {}, pr = y.price || {}, ccy = sd.currency || pr.currency || "USD";
  var cs = ccy === "USD" ? "$" : ccy === "GBP" ? "\u00a3" : ccy === "EUR" ? "\u20ac" : ccy + " ";
  var text = null, label = "key statistics";
  if (met.id === "dividend" || met.id === "yield") {
    var rate = rt32R(sd.dividendRate), dy = rt32R(sd.dividendYield), ex = sd.exDividendDate && sd.exDividendDate.fmt;
    if (rate > 0) text = base + " pays a dividend of " + cs + Number(rate).toFixed(2) + " a share a year" + (dy > 0 ? ", a yield of " + (dy * 100).toFixed(2) + "%" : "") + (ex ? " (last ex-dividend date " + ex + ")" : "") + " (Yahoo Finance, summary detail).";
    else text = base + " has no dividend in Yahoo Finance's summary detail (no dividend rate is listed).";
  } else if (met.id === "mcap") {
    var mc = rt32R(sd.marketCap) || rt32R(pr.marketCap);
    if (mc > 0) text = base + "'s market capitalisation is " + cs + (mc >= 1e12 ? (mc / 1e12).toFixed(2) + " trillion" : (mc / 1e9).toFixed(1) + " billion") + " (Yahoo Finance, summary detail).";
  } else if (met.id === "eps") {
    var eps = rt32R(ks.trailingEps);
    if (eps != null) text = base + "'s trailing twelve-month EPS is " + cs + Number(eps).toFixed(2) + " (Yahoo Finance, key statistics).";
  }
  if (!text) return;
  var src = bb8qSrc("Yahoo Finance " + label, "https://finance.yahoo.com/quote/" + encodeURIComponent(ysym) + "/key-statistics/", Date.now(), text.replace(/\.$/, ""), "bb8o:metric");
  ctx.facts.push({ id: "bb8o:metric", text: text, src: src }); ctx.sources.push(src);
  ctx.bb8oMetric = { id: met.id, text: text, src: src };
}
// P1 (d): week levels (5-session high / low from daily bars, or gold's futures windows) and scheduled earnings in the next 7 days.
async function bb8oWeekCtx(ctx, st) {
  if (!ctx || !BB8O_WEEK_Q.test(String(ctx.q || ""))) return;
  var race = function (p) { return typeof bb8q2Race === "function" ? bb8q2Race(p) : p; };
  if (ctx.gold && ctx.fut && ctx.fut.sn && Array.isArray(ctx.fut.sn.windows)) {
    var w = ctx.fut.sn.windows.filter(function (x) { return Number(x.n) === 5; })[0];
    if (w && ctx.fut.src) ctx.bb8oLevels = { n: 5, label: "gold futures (GC=F)", low: Number(w.low), high: Number(w.high), span: "sessions " + bb8qDayName(w.start) + " to " + bb8qDayName(w.end), src: ctx.fut.src, fmt: function (v) { return "$" + bb8qNum(v, 2); } };
  } else {
    var sym = (ctx.tf && ctx.tf.sym) || (st && st.bb8eMoveR && st.bb8eMoveR.ysym) || (st && st.bb8eBase) || null;
    if (sym && typeof fetchYahooChart === "function") {
      var c = await race(fetchYahooChart(sym, "1y", "1d"));
      var r = c && c.data && c.data.chart && c.data.chart.result && c.data.chart.result[0];
      var qd = r && r.indicators && r.indicators.quote && r.indicators.quote[0];
      if (r && qd && Array.isArray(r.timestamp)) {
        var tz = (r.meta && r.meta.exchangeTimezoneName) || "America/New_York", fmt = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" });
        var rows = [];
        r.timestamp.forEach(function (t, i) { var h = Number(qd.high && qd.high[i]), l = Number(qd.low && qd.low[i]); if (h > 0 && l > 0) rows.push({ d: fmt.format(new Date(t * 1000)), h: h, l: l }); });
        rows = rows.filter(function (x, i, a) { return !a[i + 1] || a[i + 1].d !== x.d; }).slice(-5);
        if (rows.length === 5) {
          var hi = Math.max.apply(null, rows.map(function (x) { return x.h; })), lo = Math.min.apply(null, rows.map(function (x) { return x.l; }));
          var money = (r.meta && r.meta.currency === "USD" && !/^\^/.test(sym)) || sym === "GC=F";
          var lab = sym === "^GSPC" ? "the S&P 500 (^GSPC)" : sym;
          var span = "sessions " + bb8qDayName(rows[0].d) + " to " + bb8qDayName(rows[4].d);
          var f = function (v) { return (money ? "$" : "") + bb8qNum(v, 2); };
          var tx = "Week levels: " + lab + " 5-session high " + f(hi) + " and low " + f(lo) + " (" + span + ", Yahoo Finance daily bars), as of " + bb8qUk(Number(r.meta && r.meta.regularMarketTime) * 1000 || Date.now()) + ".";
          var src = bb8qSrc("Yahoo Finance chart", "https://finance.yahoo.com/quote/" + encodeURIComponent(sym) + "/history/", Number(r.meta && r.meta.regularMarketTime) * 1000 || Date.now(), tx.replace(/\.$/, ""), "bb8o:levels");
          ctx.facts.push({ id: "bb8o:levels", text: tx, src: src }); ctx.sources.push(src);
          ctx.bb8oLevels = { n: 5, label: lab, low: lo, high: hi, span: span, src: src, fmt: f };
        }
      }
    }
  }
  var base = st && st.bb8eBase;
  if (base && !/^(?:XAU|GC=F|GOLD|BTC|ETH)/i.test(base) && !/^\^/.test(base) && typeof bb8lEarnGet === "function") {
    var e = await race(bb8lEarnGet(base));
    if (e && e.date) {
      var days = (Date.parse(e.date + "T12:00:00Z") - Date.now()) / 86400000;
      if (days >= -0.5 && days <= 7) {
        var es = bb8lEarnSrc(e, typeof bb8bYahooSym === "function" ? bb8bYahooSym(base) : base, base);
        var et = base + " next earnings: " + bb8lDay(e.date, true) + (e.isEstimate ? " (estimated)" : "");
        ctx.facts.push({ id: "bb8o:event", text: "Scheduled this week: " + et + ".", src: es }); ctx.sources.push(es);
        ctx.bb8oEvents = [{ text: et, src: es }];
      }
    }
  }
}
function bb8oQuoteLabel(q) {
  if (!q || typeof q !== "object") return q;
  var sym = String(q.symbol || "");
  if (/^(?:XAU|XAUUSD=X)$/i.test(sym)) return q;
  var o = Object.assign({}, q), own = (q.name && !/gold spot/i.test(q.name) ? q.name : null) || sym || null;
  if (/gold spot/i.test(String(q.label || "")) || /gold spot/i.test(String(q.name || ""))) { o.name = own; o.label = own; }
  if (!o.label && own) o.label = own;
  return o;
}
// Edition naming from UK time: Morning before 12:00, Afternoon 12:00 to 16:59, Evening from 17:00. Dated label, not ISO.
function bb8oEditionName(ms) {
  var hm = bb8oHm(ms), h = Number(String(hm).split(":")[0]);
  return h < 12 ? "Morning" : h < 17 ? "Afternoon" : "Evening";
}
// Static desk thesis and rating / sentiment words sent from the page context are uncited opinion: not passed to the model.
function bb8oCtxOpinion(s) {
  if (typeof s !== "string" || !s) return s;
  if (!/Platform thesis:|Active ticker:/.test(s)) return s;
  return s.split("\n").filter(function (l) { return !/^\s*Platform thesis:/.test(l); }).map(function (l) {
    if (!/^\s*Active ticker:/.test(l)) return l;
    return l.replace(/\s*·\s*(?:Strong[- ]Buy|Strong[- ]Sell|Buy|Sell|Hold|Accumulate|Reduce|Outperform|Underperform|Overweight|Underweight)(?=\s*·)/gi, "")
      .replace(/\s*·\s*(?:Neutral-Bull|Neutral-Bear|Bullish|Bearish|Neutral|Very Bullish|Very Bearish)(?=\s*·)/gi, "");
  }).join("\n");
}
function bb8oShape(res, status, body) {
  var path = res && res.bb8oPath;
  try { bb8oStripRatings(body, bb8oMarketRoute(path)); } catch (e) {}
  if (!path || !body || typeof body !== "object") return body;
  if (BB8O_ROUTES[path]) return bb8oQuoteBody(body, path, res.bb8oQuery);
  if (path === "/api/search") return bb8oSearchBody(body, res.bb8oProfile || null);
  if (BB8O_ADVICE_ROUTES[path] && status === 200) { try { body = bb8oAdviceBody(path, body); } catch (e) {} }
  if (path === "/api/brief" && res.bb8oEdition && status === 200 && body.brief) { var b = Object.assign({}, body); b.edition = res.bb8oEdition; try { b.brief = Object.assign({}, b.brief); var dms = Date.parse(String(b.brief.date || "") + "T12:00:00Z"); b.brief.dateLabel = isFinite(dms) ? bb8oDayLabel(dms) : res.bb8oEdition.dayLabel; b.brief.editionLabel = res.bb8oEdition.label || null; } catch (e) {} return b; }
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
      try { out = await bb8oPrevCheck(out); } catch (e) {}
      return out;
    };
  }
  if (typeof fetchYahooQuote === "function") {
    var bb8oFyq0 = fetchYahooQuote;
    fetchYahooQuote = async function (symbol) {
      var q = await bb8oFyq0.apply(this, arguments);
      try { if (bb8oIsRow(q)) { var m = {}; m[symbol] = bb8oFix(q, symbol, "yahoo"); if (!m[symbol]) return m[symbol]; await bb8oPrevCheck(m); return m[symbol]; } } catch (e) {}
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
  if (typeof rt32Yahoo === "function") {
    var bb8oRt32Y0 = rt32Yahoo;
    rt32Yahoo = function () {
      return Promise.resolve(bb8oRt32Y0.apply(this, arguments)).then(function (r) { try { return bb8oStripRatings(r, true); } catch (e) { return r; } });
    };
  }
  if (typeof RT32 === "object" && RT32 && RT32.cache && typeof RT32.cache.set === "function") {
    var bb8oCacheSet0 = RT32.cache.set;
    RT32.cache.set = function (k, v) { try { bb8oStripRatings(v, true); } catch (e) {} return bb8oCacheSet0.apply(this, arguments); };
    try { RT32.cache.forEach(function (v) { bb8oStripRatings(v, true); }); } catch (e) {}
  }
  if (typeof readBody === "function") {
    var bb8oReadBody0 = readBody;
    readBody = async function () { var b = await bb8oReadBody0.apply(this, arguments); try { b = bb8oScrubBody(b); } catch (e) { return b; } try { return await bb8oThemeCtx(b); } catch (e) { return b; } };
  }
  if (typeof bb2Read0 === "function") {
    var bb8oRead0 = bb2Read0;
    bb2Read0 = async function () { var b = await bb8oRead0.apply(this, arguments); try { b = bb8oScrubBody(b); } catch (e) { return b; } try { return await bb8oThemeCtx(b); } catch (e) { return b; } };
  }
  // P1 (e) stream == JSON: the stream path's final document is assembled from the model's own text (as the JSON path's is),
  // not from the painted text that the per-line stream guards trimmed (acc, bb8i's st.bb8iGen); done.reply stays
  // authoritative on the client, so both paths apply exactly the same numeric and sentence drops.
  var bb8oRawWrap = function (fn) {
    return async function (cfg, system, messages, onDelta) {
      var st = null; try { st = typeof bb8qSt === "function" ? bb8qSt() : null; } catch (e) {}
      if (!st || !st.chat || typeof onDelta !== "function") return fn.apply(this, arguments);
      st.bb8oRaw = "";
      var args = Array.prototype.slice.call(arguments);
      args[3] = function (d) { try { st.bb8oRaw += String(d == null ? "" : d); } catch (e) {} return onDelta.apply(this, arguments); };
      return fn.apply(this, args);
    };
  };
  if (typeof bb2OpenAi === "function") bb2OpenAi = bb8oRawWrap(bb2OpenAi);
  if (typeof bb2Gemini === "function") bb2Gemini = bb8oRawWrap(bb2Gemini);
  if (typeof bb2Finish === "function") {
    var bb8oFin0 = bb2Finish;
    bb2Finish = function (reply, store) { try { if (store && typeof store === "object") store.bb8oJsonFinish = true; } catch (e) {} return bb8oFin0.apply(this, arguments); };
  }
  if (typeof bb8jAssemble === "function") {
    var bb8oAsm0 = bb8jAssemble;
    bb8jAssemble = function (reply, store) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = store || (typeof bb8qSt === "function" ? bb8qSt() : null);
        if (st && st.chat && st.bb8qCtx && !st.bb8oJsonFinish && typeof st.bb8oRaw === "string" && st.bb8oRaw.trim()) { args[0] = st.bb8oRaw; st.bb8oRawUsed = true; if (typeof st.bb8iGen === "string") st.bb8iGen = null; }
      } catch (e) {}
      return bb8oAsm0.apply(this, args);
    };
  }
  // "Gold spot" only ever carries XAU data: reply text (both paths, via bb8qFinish), meta.quote, and the spot stamp.
  if (typeof bb8qFinish === "function") {
    var bb8oFinish0 = bb8qFinish;
    bb8qFinish = function (out, st) {
      var r = bb8oFinish0.apply(this, arguments);
      try {
        if (r && typeof r === "object" && typeof r.reply === "string" && typeof bb8qParse === "function" && typeof bb8qRender === "function") {
          var doc = bb8qParse(r), g = bb8oGoldSpotGuard(doc.body, st);
          if (g !== doc.body) { doc.body = g; st.bb8oSpotFixed = (st.bb8oSpotFixed || 0) + 1; }
          var stat = bb8oPost(doc, st);
          if (st) st.bb8oPost = stat;
          var r2 = bb8qRender(doc);
          (r2.sources || []).forEach(bb8oSrcLabel);
          r = Object.assign({}, r, { reply: r2.reply, sources: r2.sources });
        } else if (typeof r === "string") r = bb8oGoldSpotGuard(r, st);
      } catch (e) { console.warn("bb8o post", e && e.message); }
      return r;
    };
  }
  if (typeof bb8pQuoteMeta === "function") {
    var bb8oQm0 = bb8pQuoteMeta;
    bb8pQuoteMeta = function (st) { var q = bb8oQm0.apply(this, arguments); try { return bb8oQuoteLabel(q); } catch (e) { return q; } };
  }
  if (typeof bb8qSpotQuote === "function") {
    var bb8oSpotQ0 = bb8qSpotQuote;
    bb8qSpotQuote = function (q) { if (q && typeof q === "object" && q.symbol && !/^(?:XAU|XAUUSD=X|GOLD|GC=F)$/i.test(String(q.symbol))) return q; return bb8oSpotQ0.apply(this, arguments); };
  }
  // bb8q shared context: measured Leading / Lagging themes become a numbered, citable source on both /api/chat paths.
  if (typeof bb8qBuild === "function") {
    var bb8oBuild0 = bb8qBuild;
    bb8qBuild = async function (st, body) {
      var ctx = await bb8oBuild0.apply(this, arguments);
      try { await bb8oThemeFacts(ctx, body); } catch (e) {}
      try { bb8oDirCtx(ctx); } catch (e) {}
      try { await bb8oWeekCtx(ctx, st); } catch (e) {}
      try { await bb8oMetricCtx(ctx, st); } catch (e) {}
      try { (ctx.sources || []).forEach(bb8oSrcLabel); } catch (e) {}
      return ctx;
    };
  }
  // Committee, lenses, intelligence and brief prompts get the explicit no-advice rule (identified by their validators).
  if (typeof generateAi === "function") {
    var bb8oGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var v = options && options.validate;
        var mine = v && ((typeof validateCommitteeResponse === "function" && v === validateCommitteeResponse) || (typeof validateLensesResponse === "function" && v === validateLensesResponse) || (typeof validateIntelligenceResponse === "function" && v === validateIntelligenceResponse) || (typeof validateBriefResponse === "function" && v === validateBriefResponse));
        if (mine && typeof options.system === "string" && options.system.indexOf(BB8O_NO_ADVICE) < 0) {
          var o = Object.assign({}, options);
          o.system = options.system + "\n" + BB8O_NO_ADVICE;
          args[0] = o;
        }
      } catch (e) {}
      var res = await bb8oGen0.apply(this, args);
      try { if (options && typeof validateBriefResponse === "function" && options.validate === validateBriefResponse && res && res.validated && typeof res.validated === "object") await bb8oBriefThemes(res.validated); } catch (e) {}
      return res;
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
_after_q2 = v[v.index("// BB8Q2_JS_END") + len("// BB8Q2_JS_END"):]
if re.search(r"// (?:BB|RT)[A-Z0-9]*_JS_END", _after_q2):
    die("bb8o must be stacked directly on bb8q2 (another patch block follows // BB8Q2_JS_END)")
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
