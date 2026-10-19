#!/usr/bin/env python3
"""patch_bb8q.py — P0 hotfix (QA bb8q retest): one shared grounding context for both /api/chat paths (macro grid,
our regime model, gold spot + futures, macro proxies, timeframe changes), each a citable source with a real URL;
every kept figure needs a valid [n] to a source that carries it (else the sentence goes, or the one source that
carries it is cited); honest no-data sentence first with server-fetched proxies; card answers follow the length
hint and answer this week / today / this month / YTD; gold spot is the headline everywhere on the server (own
previous close or nulls with a flag, futures labelled); one meta event on the stream; brief keeps the answer line;
paragraph breaks kept; last cached move pack when the budget is missed.
Server.js only. Stacked on bb8q (live server md5 92cdce800208671ab32ded68d15e24d1). Does not rewrite app.js or index.html.
No tables, intervals, timers, dependencies, secrets or billing changes. See docs/bb8q.md.
Usage: python3 patch_bb8q.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "92cdce800208671ab32ded68d15e24d1",
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
    print("bb8q %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8q before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8q %s untouched" % label)

if "// \u2500\u2500 bb8q \u2500\u2500" in v:
    print("REFUSE: bb8q already applied")
    sys.exit(0)

REPLACE = [
]
REQUIRED = [
    ("bb8p end", "// BB8P_JS_END"),
    ("bb8pFigs", "function bb8pFigs(sent, st) {"),
    ("bb8pKeep", "function bb8pKeep(sent, resolve, st) {"),
    ("bb8pQuoteMeta", "function bb8pQuoteMeta(st) {"),
    ("bb8pMetaFix", "function bb8pMetaFix(meta, admin, st) {"),
    ("bb8pFallback", "function bb8pFallback(out, st) {"),
    ("bb8pRelFetch", "function bb8pRelFetch(st) {"),
    ("bb8pTopic", "function bb8pTopic(body) {"),
    ("bb8pTopicLabel", "function bb8pTopicLabel(topic) {"),
    ("bb8p handle hook", "    var bb8pHandle0 = handle;"),
    ("bb8iLine", "function bb8iLine(line, resolve, st) {"),
    ("bb8iIsNews", "function bb8iIsNews(src, st) {"),
    ("bb8iFullResolve", "function bb8iFullResolve(st) {"),
    ("bb8jSources", "function bb8jSources(body) {"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb8eMovePack", "async function bb8eMovePack(base) {"),
    ("bb8eWait", "async function bb8eWait(st) {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb8mTrim", "function bb8mTrim(reply, max) {"),
    ("bb8mUnits", "function bb8mUnits(text) {"),
    ("bb8mLenSt", "function bb8mLenSt() {"),
    ("bb8dSplit", "function bb8dSplit(line) {"),
    ("bb2System", "function bb2System(body, built, sources) {"),
    ("bb2Read0", "var bb2Read0 = typeof readBody === \"function\" ? readBody : async function () { return {}; };"),
    ("bb2Footer", "function bb2Footer(sources) {"),
    ("buildChatLiveMarketBlock", "async function buildChatLiveMarketBlock() {"),
    ("JSON route gold rule", "In the reply: always quote the gold last price"),
    ("fetchGoldProxy", "async function fetchGoldProxy() {"),
    ("bb3Mood", "function bb3Mood(m) {"),
    ("bb3Pack", "async function bb3Pack(now) {"),
    ("fetchYahooChart", "async function fetchYahooChart(symbol, range, interval) {"),
    ("bb8Late", "function bb8Late(ms) {"),
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
print("bb8q anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8q ── one shared grounding context for both /api/chat paths; every figure cited; gold spot headline (P0, QA bb8p retest)
// BB8Q_JS
// Root causes (QA retest of bb8p, Mon 19 Oct 2026):
// * The two paths still saw different data. JSON: the route's buildChatLiveMarketBlock (GC=F, DX-Y.NYB, ^TNX), no
//   numbered source for any of it. Stream: only the browser's context (regime, SPY/VIX tape). Neither block was a
//   citable source, so figures were quoted with "No news or price sources were supplied".
// * DXY: two different instruments were both called "DXY". The browser tape and /api/market-reference-quotes use the
//   FX-computed index (rt43s: six Yahoo FX pairs, change vs each pair's own previous close, e.g. 101.806, +0.06%); the
//   JSON live block used Yahoo DX-Y.NYB (ICE, delayed 10 min, own previous close 101.837, so -0.03%). The model mixed
//   them. Fix: the shared context quotes one DXY, Yahoo DX-Y.NYB, and its change is recomputed from that symbol's own
//   price and previous close (sign and size from p/prev, never from another feed).
// * 10Y: ^TNX is quoted by Yahoo in yield percent (5.098 = 5.10%), not x10; 5.10% matched Yahoo at 12:5x UK. Not a
//   scale bug: it is Friday's close (status closed). It is now labelled with its own as-of time and cited.
// * Gold: the header used gold-api.com spot with c:0 and prev = price (flat), so the browser borrowed GC=F's change;
//   answers and cards used GC=F futures. Now spot is the headline everywhere on the server, its change comes from spot's
//   own previous close (request-driven, in-memory last spot before the UK day roll) or is null with a flag, and GC=F is
//   labelled "Gold futures (GC=F, delayed 10 min)".
// No timers (bb8Late is the existing bounded wait), no tables, no secrets, no billing changes; free data only
// (Yahoo Finance quotes/charts, gold-api.com spot). UK 10-year gilt: no free Yahoo symbol answers (GB10Y=RR, GB10YT=RR,
// ^GUKG10, TMBMKGB-10Y, GBGB10YR=X, UK10Y=RR, ^UK10Y, GB10Y=X, ^GB10Y), so none is quoted.
var BB8Q_CTX_MS = 2500;
var BB8Q_SITE = "https://thedispatch.uk/markets/";
var BB8Q_MACRO = [
  { sym: "^GSPC", label: "S&P 500", key: /\bS&P(?: 500)?\b|\bSPX\b|\bGSPC\b/i, dp: 2 },
  { sym: "^VIX", label: "VIX (CBOE volatility index)", key: /\bVIX\b|volatility/i, dp: 2 },
  { sym: "DX-Y.NYB", label: "US Dollar Index (DXY)", key: /\bDXY\b|dollar/i, dp: 2 },
  { sym: "^TNX", label: "US 10-year Treasury yield", key: /10[- ]?(?:year|yr|y)\b|treasury|yield|\bTNX\b/i, dp: 2, yield: true }
];
var BB8Q_PROXY = {
  china: [["USDCNH=X", "USD/CNH (offshore yuan)", 4, /yuan|CNH|renminbi/i], ["^HSI", "the Hang Seng", 2, /hang seng|HSI/i], ["HG=F", "copper futures (HG=F)", 3, /copper/i]],
  uk: [["GBPUSD=X", "GBP/USD", 4, /sterling|pound|GBP/i], ["^FTSE", "the FTSE 100", 2, /FTSE/i]]
};
var BB8Q_STOP = /^(?:what|whats|is|are|was|were|the|a|an|of|for|in|on|to|and|or|how|does|do|did|why|about|this|that|it|its|me|tell|much|many|be|with|at|by|from|as|has|have|any|right|now|latest|current|currently|today|week|month|year|outlook|answer|question|asked|reader|open|background|only|unless|asks|show|data|s)$/i;
var bb8qSpotMem = { day: null, last: null, lastMs: 0, prevClose: null, prevDay: null };
var bb8qPackMem = new Map();
var bb8qSrcText = new WeakMap();

function bb8qSt() { return typeof bb8pSt === "function" ? bb8pSt() : null; }
function bb8qUkDay(ms) { try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date(ms)); } catch (e) { return null; } }
function bb8qMs(q) { var t = Number(q && q.ts); return isFinite(t) && t > 0 ? (t < 1e12 ? t * 1000 : t) : 0; }
function bb8qUk(ms) { return ms && typeof bb8dUk === "function" ? bb8dUk(ms) : ""; }
function bb8qIso(ms) { try { return ms ? new Date(ms).toISOString() : null; } catch (e) { return null; } }
function bb8qNum(v, dp) { return Number(v).toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp }); }
function bb8qLink(sym) { return "https://finance.yahoo.com/quote/" + encodeURIComponent(sym) + "/"; }
// Change from the symbol's own price and previous close (never another feed's change).
function bb8qChg(q) {
  var p = Number(q && q.p), prev = Number(q && q.prev);
  if (!(p > 0) || !(prev > 0)) return null;
  return { pct: (p / prev - 1) * 100, abs: p - prev, prev: prev };
}
function bb8qVerb(pct, closed, dp) {
  if (Math.abs(pct) < 0.005) return closed ? "was unchanged" : "is unchanged";
  return (closed ? (pct < 0 ? "fell " : "rose ") : (pct < 0 ? "is down " : "is up ")) + Math.abs(pct).toFixed(dp == null ? 2 : dp) + "%";
}
function bb8qSrc(name, link, ms, detail, key) {
  var s = { name: name, link: link, asOf: bb8qIso(ms || Date.now()), detail: String(detail || "").slice(0, 400), bb8q: true, bb8qKey: key || null };
  bb8qSrcText.set(s, String(detail || ""));
  return s;
}

// ── gold spot: own previous close (request-driven, in-memory) ──
function bb8qSpotSeen(p, ms) {
  var m = bb8qSpotMem, d = bb8qUkDay(ms || Date.now());
  if (!(p > 0) || !d) return;
  if (m.day && d > m.day && m.last > 0) { m.prevClose = m.last; m.prevDay = m.day; }
  if (!m.day || d >= m.day) { m.day = d; m.last = p; m.lastMs = ms || Date.now(); }
}
function bb8qSpotPrev(ms) {
  var m = bb8qSpotMem, d = bb8qUkDay(ms || Date.now());
  if (!(m.prevClose > 0) || !m.prevDay || m.prevDay >= d) return null;
  if (Date.parse(d + "T12:00:00Z") - Date.parse(m.prevDay + "T12:00:00Z") > 4 * 86400000) return null;   // weekend at most
  return { p: m.prevClose, day: m.prevDay };
}
function bb8qSpotQuote(q) {
  if (!q || !(Number(q.p) > 0)) return q;
  var ms = bb8qMs(q) || Date.now();
  if (!q.stale && !q.cached) bb8qSpotSeen(Number(q.p), ms);
  var pv = bb8qSpotPrev(ms), p = Number(q.p);
  var o = Object.assign({}, q, { name: "Gold spot", label: "Gold spot", feed: "gold-api.com spot (api.gold-api.com/price/XAU)" });
  if (pv) { o.prev = pv.p; o.change = p - pv.p; o.c = (p / pv.p - 1) * 100; o.changePct = o.c; o.prevClose = pv.p; o.prevCloseSource = "last gold-api spot seen before the UK day roll (" + pv.day + ")"; o.changeAvailable = true; }
  else { o.prev = null; o.change = null; o.c = null; o.changePct = null; o.prevClose = null; o.prevCloseSource = null; o.changeAvailable = false; o.noPrevClose = true; }
  o.dayHigh = null; o.dayLow = null; o.dayRangeAvailable = false;
  try {
    var sn = typeof lastChatLiveSnapshot !== "undefined" && lastChatLiveSnapshot ? lastChatLiveSnapshot : null;
    if (sn && isFinite(Number(sn.goldLast)) && Date.now() - Number(sn.goldTs) * 1000 < 6 * 3600000) o.futures = { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", price: Number(sn.goldLast), dayHigh: isFinite(Number(sn.dayHigh)) ? Number(sn.dayHigh) : null, dayLow: isFinite(Number(sn.dayLow)) ? Number(sn.dayLow) : null, asOf: bb8qIso(Number(sn.goldTs) * 1000), source: "Yahoo Finance" };
  } catch (e) {}
  return o;
}

// ── timeframe changes from free Yahoo daily bars ──
var BB8Q_TF = [
  { id: "week", re: /\b(?:this week|week to date|wtd|so far this week|week ahead|coming week|next week|weekly)\b/i, label: "This week", base: "last Friday's close" },
  { id: "today", re: /\b(?:today|this session|tonight|right now)\b/i, label: "Today", base: "the previous close" },
  { id: "month", re: /\b(?:this month|month to date|mtd|monthly)\b/i, label: "This month", base: "last month's final close" },
  { id: "ytd", re: /\b(?:ytd|year to date|this year|so far in \d{4}|since january)\b/i, label: "Year to date", base: "last year's final close" }
];
function bb8qTf(q) { var s = String(q || ""); for (var i = 0; i < BB8Q_TF.length; i++) if (BB8Q_TF[i].re.test(s)) return BB8Q_TF[i]; return null; }
function bb8qBars(chart) {
  var r = chart && !chart.unavailable ? (chart.data && chart.data.chart && chart.data.chart.result && chart.data.chart.result[0]) : null;
  if (!r) return null;
  var m = r.meta || {}, tz = m.exchangeTimezoneName || "America/New_York", ts = r.timestamp || [], cl = (r.indicators && r.indicators.quote && r.indicators.quote[0] && r.indicators.quote[0].close) || [];
  var fmt = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" });
  var bars = [];
  for (var i = 0; i < ts.length; i++) { var c = cl[i]; if (c == null || !isFinite(c)) continue; bars.push({ t: ts[i], date: fmt.format(new Date(ts[i] * 1000)), close: c }); }
  var now = Number(m.regularMarketPrice), nowMs = Number(m.regularMarketTime) * 1000;
  if (!(now > 0) || !bars.length) return null;
  return { bars: bars, now: now, nowMs: nowMs, today: fmt.format(new Date(nowMs || Date.now())), tz: tz };
}
function bb8qTfChange(b, tf, prevClose) {
  if (!b || !tf) return null;
  var today = b.today, y = Number(today.slice(0, 4)), mo = today.slice(5, 7), boundary;
  if (tf.id === "today") {
    if (!(prevClose > 0)) return null;
    return { from: prevClose, fromDate: null, to: b.now, pct: (b.now / prevClose - 1) * 100 };
  }
  if (tf.id === "week") {
    var d = new Date(today + "T12:00:00Z"), dow = d.getUTCDay(), back = dow === 0 ? 6 : dow - 1;
    boundary = new Date(d.getTime() - back * 86400000).toISOString().slice(0, 10);   // this week's Monday
  } else if (tf.id === "month") boundary = y + "-" + mo + "-01";
  else boundary = y + "-01-01";
  var base = null;
  for (var i = b.bars.length - 1; i >= 0; i--) if (b.bars[i].date < boundary) { base = b.bars[i]; break; }
  if (!base || !(base.close > 0)) return null;
  return { from: base.close, fromDate: base.date, fromMs: base.t * 1000, to: b.now, pct: (b.now / base.close - 1) * 100 };
}
function bb8qDayName(dateStr) { try { var d = new Date(dateStr + "T12:00:00Z"); return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }); } catch (e) { return dateStr; } }

// ── the shared context ──
function bb8qIsGold(st, topic) {
  if (st && /^(?:XAU|GC=F|GOLD)$/i.test(String(st.bb8eBase || ""))) return true;
  return !!(topic && topic.entities && topic.entities.some(function (t) { return t.id === "gold"; }));
}
function bb8qProxies(topic) {
  var out = [], seen = {};
  if (!topic || topic.mode !== "topic") return out;
  topic.entities.forEach(function (e) {
    var rel = BB8Q_PROXY[e.id] || (e.rel || []).map(function (r) { return [r[0] === "CNH=X" ? "USDCNH=X" : r[0], r[1], r[2], null]; });
    rel.forEach(function (r) { if (!seen[r[0]] && r[0] !== "GC=F" && !BB8Q_MACRO.some(function (m) { return m.sym === r[0]; })) { seen[r[0]] = 1; out.push(r); } });
  });
  return out.slice(0, 4);
}
function bb8qTfSym(st, topic, gold) {
  if (gold) return "GC=F";
  if (st && st.bb8eBase) return typeof bb3Yahoo === "function" ? bb3Yahoo(st.bb8eBase) : st.bb8eBase;
  var px = bb8qProxies(topic);
  if (px.length) return px[0][0];
  return "^GSPC";
}
async function bb8qBuild(st, body) {
  var t0 = Date.now(), dl = typeof bb8Late === "function" ? bb8Late(BB8Q_CTX_MS) : null;
  var race = function (p) { return dl ? Promise.race([Promise.resolve(p).catch(function () { return null; }), dl.then(function () { return null; })]) : Promise.resolve(p).catch(function () { return null; }); };
  var topic = st.bb8pTopic || (typeof bb8pTopic === "function" ? bb8pTopic(body) : null);
  if (topic) st.bb8pTopic = topic;
  var q = typeof bb8pQuestion === "function" ? bb8pQuestion(body) : "";
  var tf = bb8qTf(q), gold = bb8qIsGold(st, topic);
  var pack = await race(bb3Pack(t0));
  var one = function (sym) { return pack ? race(bb3OneQuote(pack, sym)) : Promise.resolve(null); };
  var proxies = bb8qProxies(topic), tfSym = tf ? bb8qTfSym(st, topic, gold) : null;
  var jobs = BB8Q_MACRO.map(function (m) { return one(m.sym); });
  var pj = proxies.map(function (r) { return one(r[0]); });
  var spotJ = gold && typeof fetchGoldProxy === "function" ? race(fetchGoldProxy()) : Promise.resolve(null);
  var futJ = gold && bb8qBlk0 ? race(bb8qBlk0().then(function (blk) { var sn = {}; try { sn = Object.assign({}, lastChatLiveSnapshot); } catch (e) {} return { blk: blk, sn: sn }; })) : Promise.resolve(null);
  var tfJ = tfSym && typeof fetchYahooChart === "function" ? race(fetchYahooChart(tfSym, "1y", "1d")) : Promise.resolve(null);
  var tfQ = tfSym ? one(tfSym) : Promise.resolve(null);
  var got = await Promise.all([Promise.all(jobs), Promise.all(pj), spotJ, futJ, tfJ, tfQ]);
  var ctx = { facts: [], sources: [], gold: gold, tf: null, at: Date.now(), ms: Date.now() - t0, topic: topic, q: q, tfReq: tf ? tf.id : null };
  var add = function (id, text, src) { ctx.facts.push({ id: id, text: text, src: src }); ctx.sources.push(src); return src; };
  // regime (ours), from the same pack and inputs the card score uses
  try {
    if (pack && pack.quotes && typeof bb3Mood === "function") {
      var Q = pack.quotes, ip = bb3QuotePct(Q["^GSPC"]), sp = bb3QuotePct(Q["SPY"]);
      var dq = pack.dxy && Number(pack.dxy.p) > 0 ? pack.dxy : Q["DX-Y.NYB"];
      var mood = bb3Mood({ vix: bb3QuotePx(Q["^VIX"]), spx: ip != null ? ip : sp, dxy: bb3QuotePx(dq), oil: bb3QuotePx(Q["CL=F"]), btc: bb3QuotePct(Q["BTC-USD"]) });
      if (mood && isFinite(Number(mood.score))) {
        var rt = "Dispatch regime model (ours): market mood " + mood.regime + ", score " + mood.score + "/100, computed from VIX, the S&P 500's move, the dollar index, oil and Bitcoin, as of " + bb8qUk(pack.at) + ".";
        ctx.regime = { regime: mood.regime, score: mood.score };
        add("regime", rt, bb8qSrc("Dispatch regime model", BB8Q_SITE, pack.at, "Our regime model (The Dispatch): " + mood.regime + ", score " + mood.score + "/100, from VIX, S&P 500 move, dollar index, oil and Bitcoin", "regime"));
      }
    }
  } catch (e) {}
  BB8Q_MACRO.forEach(function (m, i) {
    var x = got[0][i];
    if (!x || !(Number(x.p) > 0)) return;
    var ms = bb8qMs(x), closed = String(x.status || "") === "closed", ch = bb8qChg(x), uk = bb8qUk(ms);
    var t;
    if (m.yield) {
      t = m.label + " (^TNX) is " + Number(x.p).toFixed(2) + "%" + (ch ? ", " + (Math.abs(ch.abs) < 0.0005 ? "unchanged" : (ch.abs < 0 ? "down " : "up ") + Math.abs(ch.abs * 100).toFixed(1) + " bp") + " from its previous close of " + ch.prev.toFixed(2) + "%" : "") + (closed ? " (last session close)" : "") + ", as of " + uk + ".";
    } else {
      t = m.label + (m.label.indexOf(m.sym) >= 0 ? " " : " (" + m.sym + ") ") + (ch ? bb8qVerb(ch.pct, closed) + (closed ? " in its last session, to " : " at ") : (closed ? "closed at " : "is at ")) + bb8qNum(x.p, m.dp) + (ch ? " (previous close " + bb8qNum(ch.prev, m.dp) + ")" : "") + ", as of " + uk + ".";
    }
    add(m.sym, t, bb8qSrc("Yahoo Finance quote", bb8qLink(m.sym), ms, t.replace(/\.$/, ""), m.sym));
  });
  // gold: spot headline, futures context
  if (gold) {
    var spot = got[2] ? bb8qSpotQuote(got[2]) : null, fut = got[3];
    if (fut && fut.sn) st.bb8pGold = fut.sn;
    if (spot && Number(spot.p) > 0) {
      var sms = bb8qMs(spot) || Date.now(), suk = bb8qUk(sms);
      var stx = "Gold spot " + (spot.changeAvailable ? bb8qVerb(spot.c, false) + " at $" + bb8qNum(spot.p, 2) + " (previous close $" + bb8qNum(spot.prev, 2) + ")" : "is at $" + bb8qNum(spot.p, 2) + "; no spot previous close is available yet, so no change is given") + " (gold-api.com, as of " + suk + ").";
      ctx.spot = { q: spot, ms: sms, text: stx };
      ctx.spot.src = add("spot", stx, bb8qSrc("gold-api.com", "https://gold-api.com/", sms, stx.replace(/\.$/, ""), "spot"));
    }
    var sn = fut && fut.sn ? fut.sn : null;
    if (sn && isFinite(Number(sn.goldLast))) {
      var fms = Number(sn.goldTs) * 1000, fq = pack && pack.quotes ? (pack.extra && pack.extra["GC=F"]) || pack.quotes["GC=F"] : null;
      if (!fq) { try { fq = await race(bb3OneQuote(pack, "GC=F")); } catch (e) { fq = null; } }
      var fch = fq ? bb8qChg({ p: sn.goldLast, prev: fq.prev }) : null;
      var ftx = "Gold futures (GC=F, delayed 10 min) " + (fch ? bb8qVerb(fch.pct, false).replace(/^is /, "are ") + " at $" + bb8qNum(sn.goldLast, 2) + " (previous close $" + bb8qNum(fch.prev, 2) + ")" : "are at $" + bb8qNum(sn.goldLast, 2)) +
        (isFinite(Number(sn.dayHigh)) && isFinite(Number(sn.dayLow)) ? ", futures day range $" + bb8qNum(sn.dayLow, 2) + " to $" + bb8qNum(sn.dayHigh, 2) : "") + ", as of " + bb8qUk(fms) + ".";
      var w = (Array.isArray(sn.windows) ? sn.windows : []).map(function (x) { return x.n + " completed sessions (" + x.start + " to " + x.end + ") high $" + bb8qNum(x.high, 2) + ", low $" + bb8qNum(x.low, 2); });
      ctx.fut = { sn: sn, text: ftx, windows: w.length ? "Gold futures (GC=F) " + w.join("; ") + "." : "" };
      ctx.fut.src = add("futures", ftx, bb8qSrc("Yahoo Finance quote", bb8qLink("GC=F"), fms, ftx.replace(/\.$/, "") + (w.length ? "; " + w.join("; ") : ""), "futures"));
    }
  }
  proxies.forEach(function (r, i) {
    var x = got[1][i];
    if (!x || !(Number(x.p) > 0)) return;
    var ms = bb8qMs(x), closed = String(x.status || "") === "closed", ch = bb8qChg(x);
    var px = (x.currency === "USD" && !/=X$/.test(r[0]) ? "$" : "") + bb8qNum(x.p, r[2]);
    var pl = function (x) { return /futures/i.test(r[1]) ? x.replace(/^is /, "are ").replace(/^was /, "were ") : x; };
    var mv = pl(ch ? bb8qVerb(ch.pct, closed) : "is at");
    var t = r[1].charAt(0).toUpperCase() + r[1].slice(1) + (r[1].indexOf(r[0]) >= 0 ? "" : " (" + r[0] + ")") + " " + (ch ? mv + (closed ? " in its last session, to " : " at ") : mv + " ") + px + ", as of " + bb8qUk(ms) + ".";
    var s = add("proxy:" + r[0], t, bb8qSrc("Yahoo Finance quote", bb8qLink(r[0]), ms, t.replace(/\.$/, ""), r[0]));
    s.bb8qProxy = { sym: r[0], label: r[1], bit: r[1] + " " + (ch ? mv + (closed ? " in its last session, to " : " at ") : mv + " ") + px };
  });
  if (tf && got[4]) {
    var b = bb8qBars(got[4]), tq = got[5], ch2 = bb8qTfChange(b, tf, tq && Number(tq.prev));
    if (ch2) {
      var lbl = tfSym === "GC=F" ? "gold futures (GC=F)" : tfSym === "^GSPC" ? "the S&P 500" : (st.bb8eBase || tfSym);
      var from = tf.id === "today" ? "the previous close" : bb8qDayName(ch2.fromDate) + " close";
      var money = tfSym === "GC=F" || (tq && tq.currency === "USD" && !/^\^/.test(tfSym));
      var f2 = function (v) { return (money ? "$" : "") + bb8qNum(v, 2); };
      var be = /futures/.test(lbl) ? "are" : "is";
      var since = tf.id === "today" ? "from the previous close of " + f2(ch2.from) : "from " + tf.base + " of " + f2(ch2.from) + " (" + bb8qDayName(ch2.fromDate) + ")";
      var ttx = tf.label + ", " + since + " to " + f2(ch2.to) + " now, " + lbl + " " + be + " " + (Math.abs(ch2.pct) < 0.005 ? "unchanged" : (ch2.pct < 0 ? "down " : "up ") + Math.abs(ch2.pct).toFixed(2) + "%") + " (Yahoo Finance daily closes, as of " + bb8qUk(b.nowMs) + ").";
      ctx.tf = { id: tf.id, text: ttx, sym: tfSym };
      ctx.tf.src = add("tf:" + tf.id, ttx, bb8qSrc("Yahoo Finance chart", "https://finance.yahoo.com/quote/" + encodeURIComponent(tfSym) + "/history/", b.nowMs, ttx.replace(/\.$/, ""), "tf"));
      // Context for detailed answers: the other windows too.
      ctx.tfMore = BB8Q_TF.filter(function (t) { return t.id !== tf.id && t.id !== "today"; }).map(function (t) {
        var c3 = bb8qTfChange(b, t, null);
        return c3 ? t.label + " (from the " + bb8qDayName(c3.fromDate) + " close of " + f2(c3.from) + "), " + lbl + " " + be + " " + (c3.pct < 0 ? "down " : "up ") + Math.abs(c3.pct).toFixed(2) + "%." : "";
      }).filter(Boolean);
      if (ctx.tfMore.length) ctx.tf.src.detail = (ctx.tf.src.detail + "; " + ctx.tfMore.join(" ")).slice(0, 400), bb8qSrcText.set(ctx.tf.src, ctx.tf.src.detail);
    }
  }
  return ctx;
}
// The prompt block, numbered as the final source list numbers them (list = the CITABLE SOURCES list of this path).
function bb8qBlock(st, list) {
  var ctx = st && st.bb8qCtx;
  if (!ctx || !ctx.facts.length) return "";
  var L = Array.isArray(list) ? list : [];
  var lines = ctx.facts.map(function (f) { var n = L.indexOf(f.src) + 1; return "- " + f.text + (n > 0 ? " [" + n + "]" : ""); });
  if (ctx.fut && ctx.fut.windows) { var n2 = L.indexOf(ctx.fut.src) + 1; lines.push("- " + ctx.fut.windows + (n2 > 0 ? " [" + n2 + "]" : "")); }
  if (ctx.tfMore && ctx.tfMore.length && ctx.tf) { var n3 = L.indexOf(ctx.tf.src) + 1; ctx.tfMore.forEach(function (t) { lines.push("- " + t + (n3 > 0 ? " [" + n3 + "]" : "")); }); }
  return "SERVER DATA (LIVE MARKET DATA, the same on both answer paths; every figure you use must carry the [n] of its line; the server deletes a figure with no valid [n]; " +
    "the page's own tape figures are not citable, use these; gold spot is the headline gold price, gold futures (GC=F) are context; the regime is our own model):\n" + lines.join("\n") + "\n";
}

// ── citations: every kept figure needs a valid [n] to a source that carries it ──
function bb8qHay(txt) {
  var p = bb8pNums(txt), years = {}, days = {};
  p.dates.forEach(function (d) { days[d.k] = 1; if (d.y) years[d.y] = 1; });
  (String(txt).match(/\b(?:19|20)\d{2}\b/g) || []).forEach(function (y) { years[y] = 1; });
  return { nums: p.nums, years: years, days: days, n: String(txt).length };
}
function bb8qNorm(s) { return String(s || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/\*\*/g, "").replace(/\s+/g, " ").trim().toLowerCase(); }
function bb8qServerText(st) {
  var t = [];
  try { if (st.bb8eMove && st.bb8eMove.text) t.push(st.bb8eMove.text); } catch (e) {}
  try { if (st.bb3Built && st.bb3Built.block) t.push(st.bb3Built.block); } catch (e) {}
  try { if (Array.isArray(st.facts)) st.facts.forEach(function (f) { if (f && f.sentence) t.push(String(f.sentence)); }); } catch (e) {}
  try { if (st.bb8lEarn && st.bb8lEarn.line) t.push(String(st.bb8lEarn.line)); } catch (e) {}
  try { if (st.bb8qCtx) st.bb8qCtx.facts.forEach(function (f) { t.push(f.text); }); } catch (e) {}
  return t;
}
function bb8qIsServer(s, st) {
  var n = bb8qNorm(s).replace(/[.!?]+$/, "");
  if (n.length < 12) return false;
  var key = st.bb8qSrvKey = st.bb8qSrvKey || {};
  var all = bb8qServerText(st).join("\n");
  if (key.len !== all.length) { key.len = all.length; key.txt = bb8qNorm(all.replace(/\n/g, " \u2029 ")); }
  return key.txt.indexOf(n) >= 0;
}
function bb8qSrcHay(src, st) {
  if (!src) return null;
  st.bb8qHays = st.bb8qHays || new Map();
  var full = typeof bb8eFull === "function" ? bb8eFull(st) : [];
  var ver = full.length + ":" + (st.bb8eMove ? 1 : 0);
  var c = st.bb8qHays.get(src);
  if (c && c.ver === ver) return c.hay;
  var txt = [String(src.name || ""), String(src.detail || ""), String(src.title || ""), bb8qSrcText.get(src) || ""];
  try {
    var idx = full.indexOf(src) + 1;
    if (idx > 0) bb8qServerText(st).join("\n").split("\n").forEach(function (l) { if (bb8iCiteNums(l).indexOf(idx) >= 0) txt.push(l); });
    if (st.peerSource === src && Array.isArray(st.facts)) st.facts.forEach(function (f) { txt.push(JSON.stringify(f || {})); });
  } catch (e) {}
  var hay = bb8qHay(txt.join("\n"));
  st.bb8qHays.set(src, { ver: ver, hay: hay });
  return hay;
}
function bb8qNeed(s, st) {
  var p = bb8pNums(s), out = [];
  if (!st.bb8qQHay) st.bb8qQHay = bb8qHay(typeof bb8pQuestion === "function" && st.body ? bb8pQuestion(st.body) : "");
  p.nums.forEach(function (f) {
    if (f.year) return;                                                   // years: bb8p checks they are in context
    if (f.cls === "plain" && f.d === 0 && f.v < 10) return;               // small counts are words
    if (bb8pMatch(f, st.bb8qQHay)) return;                                // the question's own numbers
    out.push(f);
  });
  return out;
}
function bb8qPick(hits, s) {
  if (hits.length <= 1) return hits;
  var named = hits.filter(function (src) {
    var k = src && src.bb8qKey, m = BB8Q_MACRO.filter(function (x) { return x.sym === k; })[0];
    if (m) return m.key.test(s);
    if (k === "spot") return /\bspot\b/i.test(s);
    if (k === "futures") return /futures|GC=F/i.test(s);
    if (k === "regime") return /regime|mood|risk-?(?:on|off)|transition/i.test(s);
    if (src && src.bb8qProxy) return new RegExp(src.bb8qProxy.sym.replace(/[^A-Za-z0-9]/g, "."), "i").test(s) || /[A-Za-z]{4,}/.test(src.bb8qProxy.label) && new RegExp(src.bb8qProxy.label.replace(/^the /, "").replace(/[^A-Za-z0-9 ]/g, ".").split(" ")[0], "i").test(s);
    return false;
  });
  return named.length ? named : hits;
}
function bb8qCite(s, st, resolve) {
  var need = bb8qNeed(s, st);
  if (!need.length) return { ok: true, add: [], bad: [] };
  var full = typeof bb8eFull === "function" ? bb8eFull(st) : [];
  var R = resolve || function (n) { return full[n - 1] || null; };
  var cited = bb8iCiteNums(s).map(function (n) { return R(n); }).filter(Boolean);
  var add = [], bad = [];
  need.forEach(function (f) {
    if (cited.some(function (src) { var h = bb8qSrcHay(src, st); return h && bb8pMatch(f, h); })) return;
    var hits = bb8qPick(full.filter(function (src) { var h = bb8qSrcHay(src, st); return h && bb8pMatch(f, h); }), s);
    if (hits.length === 1) { if (add.indexOf(hits[0]) < 0) add.push(hits[0]); return; }
    bad.push(f.raw + (hits.length ? " (" + hits.length + " sources carry it)" : " (no source carries it)"));
  });
  return { ok: !bad.length, add: add, bad: bad, full: full };
}
function bb8qAttach(x, nums) {
  var t = String(x).replace(/\s+$/, "");
  var have = bb8iCiteNums(t), tags = nums.filter(function (n, i, a) { return n > 0 && have.indexOf(n) < 0 && a.indexOf(n) === i; }).map(function (n) { return "[" + n + "]"; }).join("");
  return tags ? t + " " + tags : t;
}
function bb8qSkipLine(t) { return !t.trim() || /^\s*(?:\*\*)?Sources?:/i.test(t) || /^\s*In short:/.test(t) || /^\s*\[\d{1,2}\]\s/.test(t) || /^\s*(?:Live|Windows):/.test(t); }
function bb8qCiteLine(t, st, resolve) {
  if (bb8qSkipLine(t)) return t;
  var pre = (/^\s*(?:[-*\u2022]|\d+[.)]|#{1,6})\s+/.exec(t) || [""])[0];
  var parts0 = typeof bb8dSplit === "function" ? bb8dSplit(t.slice(pre.length)) : [t.slice(pre.length)], parts = [];
  parts0.forEach(function (x) {
    var lead = /^\s*((?:\[\d{1,2}\]\s*)+)/.exec(x);
    if (parts.length && lead) { parts[parts.length - 1] = parts[parts.length - 1].replace(/\s+$/, "") + " " + lead[1].trim(); x = x.slice(lead[0].length); if (!x.trim()) return; }
    parts.push(x);
  });
  var out = [], changed = false;
  parts.forEach(function (x) {
    if (!x || !x.trim() || bb8qIsServer(x, st)) { out.push(x); return; }
    var r = bb8qCite(x, st, resolve);
    if (!r.ok) {
      changed = true;
      st.bb8pDrops = st.bb8pDrops || []; st.bb8qUncited = (st.bb8qUncited || 0) + 1;
      var key = String(x).trim().slice(0, 120);
      if (!st.bb8pDrops.some(function (d) { return d.s === key; })) st.bb8pDrops.push({ s: key, why: "figure without a valid [n]: " + r.bad.slice(0, 3).join(", ") });
      return;
    }
    if (r.add.length) {
      var nums = r.add.map(function (src) {
        if (resolve) { for (var n = 1; n <= 40; n++) { var g = resolve(n); if (g === src) return n; if (!g && n > r.full.length + 2) break; } }
        return r.full.indexOf(src) + 1;
      });
      x = bb8qAttach(x, nums); changed = true; st.bb8qAttached = (st.bb8qAttached || 0) + 1;
    }
    out.push(x);
  });
  if (!changed) return t;
  out = out.filter(function (x) { return x && x.trim(); });
  return out.length ? pre + out.join(" ") : "";
}

// ── final document: tokens instead of numbers, so lines can be added and the list renumbered ──
function bb8qParse(out) {
  var t = String(out.reply || ""), at = t.search(/\n+Sources:/);
  var body = at >= 0 ? t.slice(0, at) : t, srcs = Array.isArray(out.sources) ? out.sources.slice() : [];
  body = body.replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) {
    return g.split(/\s*,\s*/).map(function (x) { var i = Number(x) - 1; return srcs[i] ? "\u27e6" + i + "\u27e7" : ""; }).join("");
  });
  return { body: body, srcs: srcs, tail: at >= 0 ? t.slice(at) : "" };
}
function bb8qTok(doc, src) { var i = doc.srcs.indexOf(src); if (i < 0) { doc.srcs.push(src); i = doc.srcs.length - 1; } return "\u27e6" + i + "\u27e7"; }
function bb8qRender(doc) {
  var order = [], map = {};
  var body = String(doc.body).replace(/\u27e6(\d+)\u27e7/g, function (m, k) { if (!(k in map)) { order.push(Number(k)); map[k] = order.length; } return "[" + map[k] + "]"; });
  body = body.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/^\s+|\s+$/g, "");
  var sources = order.map(function (k) { return doc.srcs[k]; });
  return { reply: body + (typeof bb2Footer === "function" ? bb2Footer(sources) : ""), sources: sources };
}
function bb8qHasTok(l) { return /\u27e6\d+\u27e7/.test(l); }
function bb8qToks(l) { var o = []; String(l).replace(/\u27e6(\d+)\u27e7/g, function (m, k) { o.push(Number(k)); return m; }); return o; }
function bb8qWords(s) { return typeof bb8mWords === "function" ? bb8mWords(String(s).replace(/\u27e6\d+\u27e7/g, "")) : String(s).split(/\s+/).length; }
function bb8qQWords(q) {
  var w = {};
  String(q || "").replace(/\[[^\]]*\]/g, " ").toLowerCase().replace(/'s\b/g, "").split(/[^a-z0-9]+/).forEach(function (x) { if (x.length >= 3 && !BB8Q_STOP.test(x)) w[x] = 1; });
  return w;
}
function bb8qScore(line, qw) {
  var n = 0, seen = {};
  String(line).toLowerCase().replace(/'s\b/g, "").split(/[^a-z0-9]+/).forEach(function (x) { if (qw[x] && !seen[x]) { seen[x] = 1; n++; } });
  return n;
}
// In-short line: a figure needs a cite token to a source that carries it (attach the one source, or drop the line).
function bb8qShortCite(line, doc, st) {
  if (!/\d/.test(line)) return line;
  var plain = line.replace(/\u27e6\d+\u27e7/g, "");
  var need = bb8qNeed(plain, st);
  if (!need.length) return line;
  var toks = bb8qToks(line).map(function (k) { return doc.srcs[k]; });
  var addI = [], bad = false;
  need.forEach(function (f) {
    if (toks.some(function (s) { var h = bb8qSrcHay(s, st); return h && bb8pMatch(f, h); })) return;
    var hits = bb8qPick(doc.srcs.filter(function (s) { var h = bb8qSrcHay(s, st); return h && bb8pMatch(f, h); }), plain);
    if (hits.length === 1) { if (addI.indexOf(hits[0]) < 0) addI.push(hits[0]); } else bad = true;
  });
  if (bad) { st.bb8qUncited = (st.bb8qUncited || 0) + 1; return ""; }
  return addI.length ? line.replace(/\s+$/, "") + " " + addI.map(function (s) { return bb8qTok(doc, s); }).join("") : line;
}
var BB8Q_OWN_NODATA = /\b(?:not|isn'?t|aren'?t|no)\b[^.\n]{0,80}\b(?:in (?:our|the) (?:data )?feed|in the (?:supplied|provided) (?:data|context)|available|provided|included|supplied)\b/i;
function bb8qHeld(doc, st, topic) {
  if (!topic || !topic.series || !topic.series.length) return true;
  var lines = doc.body.split("\n");
  return lines.some(function (l) {
    if (!/\d/.test(l.replace(/\u27e6\d+\u27e7/g, "")) || /^\s*In short:/.test(l)) return false;
    return bb8qToks(l).some(function (k) { var s = doc.srcs[k]; return s && !s.bb8q && topic.series.some(function (t) { return t.re.test(String(s.detail || "") + " " + String(s.title || "")); }); });
  });
}
function bb8qNoData(doc, st, ctx) {
  var topic = ctx.topic, label = typeof bb8pTopicLabel === "function" ? bb8pTopicLabel(topic) : "these figures";
  var lines = doc.body.split("\n").filter(function (l) { return !/^\s*We don't have /.test(l) && !/^\s*What we do have, from Yahoo Finance/.test(l) && !/^\s*Our feed has no related live market data/.test(l); });
  // the model's own "not in our feed" sentences give way to the server's one
  lines = lines.map(function (l) {
    if (/^\s*In short:/.test(l)) return l;
    var parts = typeof bb8dSplit === "function" ? bb8dSplit(l) : [l];
    var k = parts.filter(function (x) { return !BB8Q_OWN_NODATA.test(x); });
    return k.length === parts.length ? l : k.join(" ");
  });
  var px = ctx.sources.filter(function (s) { return s.bb8qProxy; });
  var head = ["We don't have " + label + " in our data feed right now, so this answer does not quote any."];
  if (px.length) {
    var ms = Math.max.apply(null, px.map(function (s) { return Date.parse(s.asOf) || 0; }));
    var bits = px.map(function (s) { return s.bb8qProxy.bit + " " + bb8qTok(doc, s); });
    var txt = bits.join("; ");
    head.push("What we do have, from Yahoo Finance as of " + bb8qUk(ms) + ": " + txt.charAt(0).toUpperCase() + txt.slice(1) + ".");
  }
  try {
    var used = {}; doc.body.replace(/\u27e6(\d+)\u27e7/g, function (m, k) { used[doc.srcs[k] && (doc.srcs[k].link || doc.srcs[k].detail)] = 1; return m; });
    var news = (Array.isArray(st.clientSources) ? st.clientSources : []).filter(function (s) {
      return s && !s.bb8q && typeof bb8iIsNews === "function" && bb8iIsNews(s, st) && typeof bb8pRelevant === "function" && bb8pRelevant(s, topic) && !used[s.link || s.detail];
    }).slice(0, 2);
    news.forEach(function (s) { head.push("In the news (" + s.name + (s.asOf ? ", " + bb8qUk(Date.parse(s.asOf)) : "") + "), a headline, not our data: \"" + String(s.detail || s.title || "").replace(/"/g, "'").trim() + "\" " + bb8qTok(doc, s)); });
  } catch (e) {}
  var sm = -1;
  for (var i = 0; i < lines.length; i++) if (/^\s*In short:/.test(lines[i])) sm = i;
  var shortL = "In short: no " + label.replace(/^the /, "") + " in our feed" + (px.length ? "; related live markets are above." : ".");
  if (sm >= 0) lines.splice(sm, 1);
  var rest = lines.join("\n").replace(/^\s+|\s+$/g, "");
  doc.body = head.join("\n\n") + (rest ? "\n\n" + rest : "") + "\n\n" + shortL;
  st.bb8pNoData = true; st.bb8qNoData = true;
}
function bb8qFinish(out, st) {
  var ctx = st.bb8qCtx;
  var doc = bb8qParse(out);
  var len = typeof bb8mLenSt === "function" ? bb8mLenSt() : null;
  var q = ctx.q || "", tf = ctx.tf, move = !!(st.bb8eMove && st.bb8eMoveR), gold = ctx.gold;
  var lines = doc.body.split("\n");
  // (5) one gold price line for general gold answers on both paths (the JSON route's "Live:" line had GC=F as the
  // headline, no cite and no full stop; the stream had none)
  // lines left holding only a citation (their sentence was dropped earlier) go too
  lines = lines.filter(function (l) { return !/^\s*(?:Live|Windows): /.test(l) && !/^\s*(?:\u27e6\d+\u27e7\s*)+$/.test(l); });
  if (move && gold) lines = lines.map(function (l) { return /^\s*In short:/.test(l) ? l.replace(/\bXAU is (up|down|unchanged)/, "gold futures are $1").replace(/\bXAU (rose|fell)/, "gold futures $1").replace(/\bXAU\b(?! spot)/g, "gold futures") : l; });
  var own = [];
  if (!move && gold && (ctx.spot || ctx.fut)) {
    var lv = [];
    if (ctx.spot) lv.push(ctx.spot.text.replace(/\.$/, "") + " " + bb8qTok(doc, ctx.spot.src));
    if (ctx.fut) lv.push(ctx.fut.text.replace(/^Gold futures/, "gold futures").replace(/\.$/, "") + " " + bb8qTok(doc, ctx.fut.src));
    lv = lv.map(function (x) { return x.replace(/(gold futures \(GC=F, delayed 10 min\)) is /i, "$1 are "); });
    own.push("Live: " + lv.join("; ") + ".");
  }
  // (4) timeframe sentence from daily bars, cited
  var tfAt = -1;
  if (tf && ctx.tf) {
    var tline = ctx.tf.text + " " + bb8qTok(doc, ctx.tf.src);
    if (move) {
      var pi = -1;
      for (var i = 0; i < lines.length; i++) { if (bb8qHasTok(lines[i]) && !/^\s*In short:/.test(lines[i])) { pi = i; if (!/^\s*Gold spot\b/.test(lines[i])) break; } }
      if (pi >= 0 && /^\s*Gold spot\b/.test(lines[pi]) && /^\s*Gold futures\b/.test(lines[pi + 1] || "")) pi++;
      lines.splice(pi + 1, 0, tline); tfAt = pi + 1;
    } else own.push(tline);
  }
  if (own.length) lines = own.concat(lines.length && lines[0].trim() ? [""] : []).concat(lines);
  doc.body = lines.join("\n");
  // (3) honest no-data first, with the server's own proxy quotes
  var topic = ctx.topic;
  // a gold question is held when the shared context has gold spot or futures
  var goldHeld = !!(gold && (ctx.spot || ctx.fut));
  if (!move && topic && topic.mode === "topic" && topic.series && topic.series.length && !goldHeld && !bb8qHeld(doc, st, topic)) bb8qNoData(doc, st, ctx);
  lines = doc.body.split("\n");
  if (goldHeld) { lines = lines.filter(function (l) { return !/^\s*We don't have /.test(l) && !/^\s*In the news \([^)]*\), a headline, not our data:/.test(l) && !/^\s*In short: no .* in our feed/.test(l); }); st.bb8pNoData = false; st.bb8qNoData = false; }
  // brief general answers: server lines stay, model lines are cut from the end to the brief budget
  if (!move && len === "brief" && typeof BB8M_BRIEF_MAX !== "undefined") {
    var srvRe = /^\s*(?:We don't have |What we do have, from Yahoo Finance|In the news \(|In short:|Live: )/;
    var tot = function (a) { return a.reduce(function (n, l) { return n + bb8qWords(l.replace(/\u27e6\d+\u27e7/g, "")); }, 0); };
    for (var z = lines.length - 1; z >= 0 && tot(lines) > BB8M_BRIEF_MAX; z--) {
      if (!lines[z].trim() || srvRe.test(lines[z]) || (ctx.tf && lines[z].indexOf(ctx.tf.text.slice(0, 30)) >= 0)) continue;
      lines.splice(z, 1);
    }
    lines = lines.filter(function (l, i, a) { return !(l === "" && a[i - 1] === ""); });
  }
  // (4) the card template follows the length hint
  if (move && len === "brief") {
    var qw = bb8qQWords(q), keep = [], best = -1, bestS = 0;
    for (var j = 0; j < lines.length; j++) {
      var l = lines[j];
      if (!l.trim() || /^\s*In short:/.test(l)) continue;
      var sc = bb8qScore(l, qw);
      if (j > 1 && j !== tfAt && !(gold && tfAt >= 0) && sc > bestS) { bestS = sc; best = j; }
    }
    var firstPrice = -1;
    for (var k2 = 0; k2 < lines.length; k2++) if (bb8qHasTok(lines[k2]) && !/^\s*In short:/.test(lines[k2])) { firstPrice = k2; break; }
    for (var j2 = 0; j2 < lines.length; j2++) {
      var l2 = lines[j2];
      if (/^\s*In short:/.test(l2)) { keep.push(l2); continue; }
      if (j2 === 0 && /:\s*$/.test(l2)) { keep.push(l2); continue; }
      if (j2 === firstPrice || j2 === tfAt || j2 === best || (gold && /^\s*Gold spot\b/.test(l2) && j2 <= firstPrice + 1) || (gold && tfAt < 0 && /^\s*Gold futures\b/.test(l2) && j2 <= firstPrice + 1)) keep.push(l2);
    }
    lines = keep;
  } else if (move && len === "detailed") {
    var extra = [];
    if (ctx.tfMore && ctx.tf) ctx.tfMore.forEach(function (t) { extra.push(t + " " + bb8qTok(doc, ctx.tf.src)); });
    if (gold && ctx.fut && ctx.fut.windows) extra.push(ctx.fut.windows + " " + bb8qTok(doc, ctx.fut.src));
    ctx.facts.forEach(function (f) { if (/^(?:regime|DX-Y\.NYB|\^TNX)$/.test(f.id)) extra.push(f.text + " " + bb8qTok(doc, f.src)); });
    var have = bb8qNorm(lines.join(" "));
    extra = extra.filter(function (e) { return have.indexOf(bb8qNorm(e.replace(/\u27e6\d+\u27e7/g, "")).replace(/\.$/, "")) < 0; });
    if (extra.length) {
      var si = -1;
      for (var m2 = lines.length - 1; m2 >= 0; m2--) if (/^\s*In short:/.test(lines[m2])) { si = m2; break; }
      var block = ["", "For context:"].concat(extra);
      if (si >= 0) lines.splice.apply(lines, [si, 0].concat(block.concat([""]))); else lines = lines.concat(block);
    }
  }
  // In-short cites; (B2) detailed answers keep their paragraph breaks
  lines = lines.map(function (l) { return /^\s*In short:/.test(l) ? bb8qShortCite(l, doc, st) : l; }).filter(function (l, i, a) { return !(l === "" && a[i - 1] === ""); });
  var body = lines.join("\n");
  if (len === "detailed" && !move) body = body.replace(/([^\n:])\n(?=[^\n\-*\u2022\d\s])/g, "$1\n\n");
  body = body.replace(/(^|\n)(In short:)/, function (m, a, b) { return (a ? "\n\n" : "") + b; });
  doc.body = body;
  return bb8qRender(doc);
}

// ── B1: the brief trim keeps the sentence that answers the question ──
function bb8qKeepAns(orig, r, max) {
  try {
    if (!r || !r.cut || typeof bb8mUnits !== "function") return r;
    var st = bb8qSt(); if (!st || !st.body) return r;
    var qw = bb8qQWords(bb8pQuestion(st.body));
    if (!Object.keys(qw).length) return r;
    var split = function (text) {
      var s = String(text || ""), at = s.search(/\n+Sources:\n/);
      var body = at >= 0 ? s.slice(0, at) : s, tail = at >= 0 ? s.slice(at) : "";
      var sm = body.match(/(?:^|\n)(In short:[^\n]*)/), inShort = sm ? sm[1] : "";
      var rest = (sm ? body.slice(0, sm.index) + body.slice(sm.index + sm[0].length) : body).replace(/\s+$/, "");
      var ends = bb8mUnits(rest), units = [];
      for (var i = 0; i < ends.length; i++) { var u = rest.slice(i ? ends[i - 1] : 0, ends[i]).trim(); if (u) units.push(u); }
      return { units: units, inShort: inShort, tail: tail };
    };
    var o = split(orig), best = null, bs = 0;
    o.units.forEach(function (u) { if (/:\s*$/.test(u)) return; var sc = bb8qScore(u, qw); if (sc > bs) { bs = sc; best = u; } });
    if (!best) return r;
    var a = split(r.text);
    if (a.units.some(function (u) { return bb8qNorm(u) === bb8qNorm(best); })) return r;
    var w = function (x) { return bb8mWords(x); };
    var units = a.units.slice();
    while (units.length > 1 && w(units.join(" ") + " " + best) + w(a.inShort) > max) units.pop();
    // keep the original order
    var pos = o.units.indexOf(best), ins = units.length;
    for (var k = 0; k < units.length; k++) if (o.units.indexOf(units[k]) > pos) { ins = k; break; }
    units.splice(ins, 0, best);
    var body = units.join("\n");
    return { text: body + (a.inShort ? "\n\n" + a.inShort : "") + a.tail, cut: true, words: w(body) + w(a.inShort), bb8qAns: true };
  } catch (e) { return r; }
}

var bb8qBlk0 = null;
try {
  // Shared context, built once per /api/chat request where both paths read the body (bb2Read0), bounded wait.
  if (typeof bb2Read0 === "function") {
    var bb8qRead0 = bb2Read0;
    bb2Read0 = async function () {
      var body = await bb8qRead0.apply(this, arguments);
      try {
        var st = bb8qSt();
        if (st && body && typeof body === "object" && !st.bb8qP) {
          st.bb8qP = bb8qBuild(st, body).then(function (c) { st.bb8qCtx = c; return c; }).catch(function (e) { console.warn("bb8q ctx", e && e.message); st.bb8qCtx = null; return null; });
          await st.bb8qP;
        }
      } catch (e) {}
      return body;
    };
  }
  // The shared sources join the client list everywhere it is built (stream CITABLE SOURCES, JSON fill, final list).
  if (typeof bb8jSources === "function") {
    var bb8qSrc0 = bb8jSources;
    bb8jSources = function (body) {
      var list = bb8qSrc0.apply(this, arguments);
      try { var st = bb8qSt(); if (st && st.bb8qCtx && Array.isArray(list)) { list = list.slice(); st.bb8qCtx.sources.forEach(function (s) { if (list.indexOf(s) < 0) list.push(s); }); } } catch (e) {}
      return list;
    };
  }
  if (typeof bb2ClientSources === "function") {
    var bb8qCs0 = bb2ClientSources;
    bb2ClientSources = function (body) {
      var l = bb8qCs0.apply(this, arguments);
      try { var st = bb8qSt(); if (st && st.bb8qCtx && Array.isArray(l)) { l = l.slice(); st.bb8qCtx.sources.forEach(function (s) { if (l.indexOf(s) < 0) l.push(s); }); } } catch (e) {}
      return l;
    };
  }
  if (typeof bb8iIsNews === "function") {
    var bb8qNews0 = bb8iIsNews;
    bb8iIsNews = function (src) { if (src && src.bb8q) return false; return bb8qNews0.apply(this, arguments); };
  }
  // JSON path: the route's live block becomes the shared block (same facts and numbering as the stream).
  if (typeof buildChatLiveMarketBlock === "function") {
    bb8qBlk0 = buildChatLiveMarketBlock;
    buildChatLiveMarketBlock = async function () {
      try {
        var st = bb8qSt();
        if (st && st.chat && st.bb8qP) {
          await st.bb8qP;
          if (st.bb8qCtx) {
            var list = typeof bb8jClient === "function" && typeof bb8jSources === "function" && st.body ? bb8jClient(bb8jSources(st.body)) : st.bb8qCtx.sources;
            return bb8qBlock(st, list);
          }
        }
      } catch (e) {}
      return bb8qBlk0.apply(this, arguments);
    };
  }
  // Stream: the same block, numbered by the list this prompt cites.
  if (typeof bb2System === "function") {
    var bb8qSys0 = bb2System;
    bb2System = function (body, built, sources) {
      var s = bb8qSys0.apply(this, arguments);
      try { var st = bb8qSt(); if (st && st.bb8qCtx) { var blk = bb8qBlock(st, sources); if (blk) s = blk + "\n" + s; } } catch (e) {}
      return s;
    };
  }
  // JSON route rules that asked for gold/10y/DXY in every answer give way to the cite rule.
  if (typeof generateAi === "function") {
    var bb8qGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8qSt();
        if (st && st.chat && options && typeof options.system === "string" && options.system.indexOf("In the reply: always quote the gold last price") >= 0) {
          var s = options.system, a = s.indexOf("In the reply: always quote the gold last price"), b = s.indexOf("say plainly when a figure is unavailable.", a);
          if (b > a) s = s.slice(0, a) + "In the reply: cite every figure with the [n] of the SERVER DATA line it comes from; say plainly when a figure is unavailable." + s.slice(b + "say plainly when a figure is unavailable.".length);
          s = s.replace("the LIVE MARKET DATA block", "the SERVER DATA block");
          args[0] = Object.assign({}, options, { system: s });
        }
      } catch (e) {}
      return bb8qGen0.apply(this, args);
    };
  }
  // (1) every kept model figure needs a valid [n]: no unique source -> not painted, dropped by bb8pKeep.
  if (typeof bb8pFigs === "function") {
    var bb8qFigs0 = bb8pFigs;
    bb8pFigs = function (sent, st) {
      var bad = bb8qFigs0.apply(this, arguments);
      try {
        if (st && st.chat && st.bb8qCtx && !bad.length && !/^\s*(?:In short|Live|Windows):/.test(String(sent)) && !bb8qIsServer(sent, st)) {
          var r = bb8qCite(String(sent), st, null);
          if (!r.ok) bad = bad.concat(r.bad.map(function (x) { return "uncited " + x; }));
        }
      } catch (e) {}
      return bad;
    };
  }
  // ... and a figure exactly one source carries gets that source's [n].
  if (typeof bb8iLine === "function") {
    var bb8qLine0 = bb8iLine;
    bb8iLine = function (line, resolve, st) {
      var t = bb8qLine0.apply(this, arguments);
      try { var s0 = st || bb8qSt(); if (s0 && s0.chat && s0.bb8qCtx && typeof t === "string") t = bb8qCiteLine(t, s0, resolve); } catch (e) {}
      return t;
    };
  }
  // bb8p's related-quotes fetch and fallback now come from the shared context.
  if (typeof bb8pRelFetch === "function") bb8pRelFetch = function () {};
  if (typeof bb8pFallback === "function") {
    bb8pFallback = function (out, st) {
      if (!st || !st.bb8qCtx) return out;
      if (st.bb8qCtx.gold && (st.bb8qCtx.spot || st.bb8qCtx.fut)) return out;
      var doc = bb8qParse(out);
      bb8qNoData(doc, st, st.bb8qCtx);
      return bb8qRender(doc);
    };
  }
  // (5) gold card lead: spot is the headline, futures are labelled.
  if (typeof bb8eLead === "function") {
    var bb8qLead0 = bb8eLead;
    bb8eLead = function (pack, card, n0) {
      var r = bb8qLead0.apply(this, arguments);
      try {
        var st = bb8qSt(), ctx = st && st.bb8qCtx;
        if (!r || !pack || pack.ysym !== "GC=F" || !ctx || !ctx.spot) return r;
        var list = Array.isArray(st.clientSources) ? st.clientSources : [];
        var sn = list.indexOf(ctx.spot.src) + 1;
        if (sn <= 0) { r.sources.push(ctx.spot.src); sn = n0 + r.sources.length; }
        var L = r.text.split("\n");
        for (var i = 1; i < L.length; i++) {
          if (/^XAU (?:is|rose|fell|was)\b/.test(L[i])) {
            L[i] = L[i].replace(/^XAU /, "Gold futures (GC=F, delayed 10 min) ").replace(/^Gold futures \(GC=F, delayed 10 min\) is /, "Gold futures (GC=F, delayed 10 min) are ").replace(/^Gold futures \(GC=F, delayed 10 min\) was /, "Gold futures (GC=F, delayed 10 min) were ");
            L.splice(i, 0, ctx.spot.text + " [" + sn + "]");
            break;
          }
        }
        L = L.map(function (l, k) { return k === 0 ? l.replace(/^XAU's latest move/, "Gold's latest move").replace(/^Why XAU reads/, "Why gold (XAU) reads") : l.replace(/\bso XAU\b/g, "so gold futures"); });
        r.text = L.join("\n"); r.paint = r.text.replace(/\s*\[\d+\]/g, "");
        r.prompt = r.prompt.replace(/^(CARD AND MOVE FACTS[^\n]*\n)[\s\S]*?\n\n/, function (m, h) { return h + L.slice(1).join("\n") + "\n\n"; });
      } catch (e) {}
      return r;
    };
  }
  // B4: a move pack that misses its budget falls back to the last pack for that name (its own as-of time).
  if (typeof bb8eMovePack === "function") {
    var bb8qPack0 = bb8eMovePack;
    bb8eMovePack = async function (base) {
      var p = await bb8qPack0.apply(this, arguments);
      try { if (p && base) bb8qPackMem.set(String(base), { pack: p, at: Date.now() }); if (bb8qPackMem.size > 300) bb8qPackMem.delete(bb8qPackMem.keys().next().value); } catch (e) {}
      return p;
    };
  }
  if (typeof bb8eWait === "function") {
    var bb8qWait0 = bb8eWait;
    bb8eWait = async function (st) {
      var r = await bb8qWait0.apply(this, arguments);
      try {
        if (!r && st && st.bb8eBase) {
          var m = bb8qPackMem.get(String(st.bb8eBase));
          if (m && Date.now() - m.at < 24 * 3600000) { r = Object.assign({}, m.pack, { bb8qCached: true, bb8qCachedAt: m.at }); st.bb8eMoveR = r; st.bb8qPackCached = true; }
        }
      } catch (e) {}
      return r;
    };
  }
  // B1
  if (typeof bb8mTrim === "function") {
    var bb8qTrim0 = bb8mTrim;
    bb8mTrim = function (reply, max) { return bb8qKeepAns(reply, bb8qTrim0.apply(this, arguments), max); };
  }
  // (5) the header's quote route and every server spot read: spot's own previous close or nulls with a flag.
  if (typeof fetchGoldProxy === "function") {
    var bb8qGold0 = fetchGoldProxy;
    fetchGoldProxy = async function () { var q = await bb8qGold0.apply(this, arguments); try { return bb8qSpotQuote(q); } catch (e) { return q; } };
  }
  // meta.quote for gold = spot (with futures labelled); grounding counts cites.
  if (typeof bb8pQuoteMeta === "function") {
    var bb8qQm0 = bb8pQuoteMeta;
    bb8pQuoteMeta = function (st) {
      try {
        var c = st && st.bb8qCtx;
        if (c && c.gold && c.spot) {
          var s = c.spot.q, sn = c.fut ? c.fut.sn : null, fq = st.bb8eMoveR && st.bb8eMoveR.ysym === "GC=F" ? st.bb8eMoveR.q : null;
          return {
            symbol: "XAU", label: "Gold spot", name: "Gold spot", price: Number(s.p), currency: "USD",
            change: s.changeAvailable ? Number(Number(s.change).toFixed(2)) : null, changePct: s.changeAvailable ? Number(Number(s.c).toFixed(4)) : null,
            prevClose: s.changeAvailable ? Number(s.prev) : null, changeAvailable: !!s.changeAvailable, prevCloseSource: s.prevCloseSource || null,
            dayHigh: null, dayLow: null, dayRangeAvailable: false,
            asOf: bb8qIso(c.spot.ms), asOfUk: bb8qUk(c.spot.ms), source: "gold-api.com", feed: "gold-api.com spot (api.gold-api.com/price/XAU)", session: null,
            futures: sn ? { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", price: Number(sn.goldLast), prevClose: fq && Number(fq.prev) > 0 ? Number(fq.prev) : null,
              changePct: fq && Number(fq.prev) > 0 ? Number(((Number(sn.goldLast) / Number(fq.prev) - 1) * 100).toFixed(4)) : null,
              dayHigh: isFinite(Number(sn.dayHigh)) ? Number(sn.dayHigh) : null, dayLow: isFinite(Number(sn.dayLow)) ? Number(sn.dayLow) : null,
              asOf: bb8qIso(Number(sn.goldTs) * 1000), asOfUk: bb8qUk(Number(sn.goldTs) * 1000), source: "Yahoo Finance", delayMin: 10 } : null
          };
        }
      } catch (e) {}
      var q = bb8qQm0.apply(this, arguments);
      try { if (q && st && st.bb8qPackCached && st.bb8eMoveR) { q.cached = true; q.cachedAtUk = bb8qUk(st.bb8eMoveR.bb8qCachedAt); } } catch (e) {}
      return q;
    };
  }
  if (typeof bb8pMetaFix === "function") {
    var bb8qMeta0 = bb8pMetaFix;
    bb8pMetaFix = function (meta, admin, st) {
      var m = bb8qMeta0.apply(this, arguments);
      try { if (st && m && m.grounding) { m.grounding.uncitedDropped = st.bb8qUncited || 0; m.grounding.citesAdded = st.bb8qAttached || 0; m.grounding.sharedFacts = st.bb8qCtx ? st.bb8qCtx.facts.map(function (f) { return f.id; }) : []; } } catch (e) {}
      return m;
    };
  }
  // B2: general answers on the stream are painted from the raw model text, whole sentences that pass every line rule,
  // with the model's paragraph breaks; the done event's reply still replaces the painted text.
  var bb8qRawWrap = function (fn0) {
    return function (cfg, system, messages, onDelta) {
      var st = bb8qSt();
      if (st && st.chat && typeof onDelta === "function") {
        st.bb8qRaw = "";
        var od = onDelta;
        onDelta = function (d) { if (typeof d === "string") { st.bb8qRaw += d; try { if (st.bb8qPump) st.bb8qPump(false); } catch (e) {} } return od.apply(this, arguments); };
      }
      return fn0.call(this, cfg, system, messages, onDelta);
    };
  };
  if (typeof bb2OpenAi === "function") bb2OpenAi = bb8qRawWrap(bb2OpenAi);
  if (typeof bb2Gemini === "function") bb2Gemini = bb8qRawWrap(bb2Gemini);
  if (typeof bb2Complete === "function") {
    var bb8qComplete0 = bb2Complete;
    bb2Complete = async function (system, messages, onDelta) {
      var st = bb8qSt();
      var general = st && st.chat && typeof onDelta === "function" && !(st.bb8eMode === "move" && st.bb8eBase) && typeof bb8iGeneral === "function" && bb8iGeneral(st);
      if (!general) return bb8qComplete0.apply(this, arguments);
      var used = 0, painted = 0, first = true, len = typeof bb8mLenSt === "function" ? bb8mLenSt() : null;
      var cap = len === "brief" && typeof BB8M_BRIEF_MAX !== "undefined" ? BB8M_BRIEF_MAX : 1e9;
      var R = typeof bb8iFullResolve === "function" ? bb8iFullResolve(st) : null;
      // the no-data sentence is painted first too when no client source can hold the series (the done event's reply is authoritative)
      try {
        var tp = st.bb8qCtx && st.bb8qCtx.topic;
        if (tp && tp.mode === "topic" && tp.series && tp.series.length) {
          var cs = (Array.isArray(st.clientSources) ? st.clientSources : []).filter(function (x) { return x && !x.bb8q; });
          var heldMaybe = cs.some(function (x) { return tp.series.some(function (t) { return t.re.test(String(x.detail || "") + " " + String(x.title || "")); }); });
          if (!heldMaybe) {
            onDelta("We don't have " + (typeof bb8pTopicLabel === "function" ? bb8pTopicLabel(tp) : "these figures") + " in our data feed right now, so this answer does not quote any.\n");
            first = false; st.bb8qGap = "\n\n";
          }
        }
      } catch (e) {}
      st.bb8qPump = function (force) {
        var raw = String(st.bb8qRaw || ""), rest = raw.slice(used);
        if (!rest) return;
        var ends = bb8mUnits(rest), upto = force ? rest.length : (ends.length > 1 ? ends[ends.length - 2] : 0);
        if (!upto) return;
        var from = 0;
        for (var i = 0; i < ends.length && ends[i] <= upto; i++) {
          var piece = rest.slice(from, ends[i]); from = ends[i];
          var gap = (piece.match(/^\s*/) || [""])[0], unit = piece.slice(gap.length);
          st.bb8qGap = (st.bb8qGap || "") + gap;
          if (!unit.trim() || /^\s*(?:\*\*)?Sources?:/i.test(unit) || /^\s*In short:/.test(unit) || /^\s*\[\d{1,2}\]\s/.test(unit)) continue;
          if (!force || i < ends.length - 1 || /[.!?:)\]"']\s*$/.test(unit)) {
            var kept = bb8iLine(unit, R, st);
            if (kept && kept.trim() && painted < cap) {
              kept = String(kept).replace(/[ \t]*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, "");
              var g2 = st.bb8qGap || "";
              var sep = first ? "" : (/\n\s*\n/.test(g2) ? "\n\n" : /\n/.test(g2) ? "\n" : " ");
              // the stream's line rewrite trims bare whitespace, so the gap travels as bb8e's next-piece separator
              st.bb8eNextSep = sep || null;
              try { onDelta(kept.replace(/\s+$/, "") + "\n"); } finally { st.bb8eNextSep = null; }
              first = false; painted += bb8qWords(kept); st.bb8qGap = "";
            }
          }
        }
        used += from;
      };
      var r;
      try { r = await bb8qComplete0.call(this, system, messages, function () {}); }
      finally { try { st.bb8qPump(true); } catch (e) {} st.bb8qPump = null; st.bb8eNextSep = null; }
      return r;
    };
  }
  // Final document on both paths (after bb8p): one gold line, timeframe, no-data first, card length, In short cites.
  if (typeof bb8jAssemble === "function") {
    var bb8qAssemble0 = bb8jAssemble;
    bb8jAssemble = function (reply, store) {
      var out = bb8qAssemble0.apply(this, arguments);
      try {
        var st = store || bb8qSt();
        if (st && st.chat && st.bb8qCtx && out && typeof out.reply === "string") { out = bb8qFinish(out, st); st.bb8jSources = out.sources; }
      } catch (e) { console.warn("bb8q finish", e && e.message); }
      return out;
    };
  }
  // (6) the stream sends one meta event (quote, grounding; provider/model for admins only) before the done event.
  if (typeof handle === "function") {
    var bb8qHandle0 = handle;
    handle = async function (req, res) {
      try {
        var host = (req && req.headers && req.headers.host) || "localhost";
        var url = new URL((req && req.url) || "/", "http://" + host);
        if (req && req.method === "POST" && url.pathname === "/api/chat" && res && !res.__bb8q) {
          res.__bb8q = true;
          var w0 = res.write, sent = false;
          res.write = function (chunk) {
            try {
              if (!sent && chunk && typeof chunk !== "function") {
                var t = Buffer.isBuffer(chunk) ? chunk.toString("utf8") : typeof chunk === "string" ? chunk : "";
                if (/^data: \{/.test(t) && t.indexOf('"done":true') >= 0) {
                  var ln = t.split("\n").filter(function (l) { return /^data: \{/.test(l) && l.indexOf('"done":true') >= 0; })[0];
                  var e = JSON.parse(ln.slice(6));
                  if (e && e.meta) { sent = true; w0.call(this, "data: " + JSON.stringify({ meta: Object.assign({ quote: null, grounding: null }, e.meta) }) + "\n\n"); }
                }
              }
            } catch (er) {}
            return w0.apply(this, arguments);
          };
        }
      } catch (e) {}
      return bb8qHandle0.apply(this, arguments);
    };
  }
} catch (e) { console.warn("bb8q hooks skipped", e && e.message); }
// BB8Q_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8q")]
if bad:
    die("bb8q block declares a non-bb8q function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8q block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8q function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "setTimeout(" in BLOCK or "stripe" in BLOCK.lower() or ".tier" in BLOCK or "process.env" in BLOCK:
    die("bb8q block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8q replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8q setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8qbak"
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
print("APPLY bb8q shared grounding context on both paths, cited figures, no-data first with proxies, card length/timeframe, gold spot headline, stream meta event")
