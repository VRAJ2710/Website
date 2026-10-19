#!/usr/bin/env python3
"""patch_bb8e.py — Ask relevance for card and move questions; no valuation headwind/tailwind; cited-only Sources; House note. Server.js only.
Stacked on bb8e (server md5 e0a1e5ea2ba975298bd9a2177abd5a6f). Does not rewrite app.js or index.html.
1) /api/chat intent is decided deterministically from the question (client notes in [..] are ignored): a Pulse card
   question ("What matters most about MU — Headwind?", or body.card) or any question without valuation/peer keywords
   is a move question. Move questions get no peer valuation block and no "In short" line; the server leads with the
   card's reason from data it already has: the last-session move (Yahoo quote), the move against SPY (or the home
   index) and the sector ETF, the regime-fit card score, and up to two neutral Yahoo ticker-news headlines marked
   "not confirmed as the cause". The same facts lead the model prompt. Valuation/peer questions are unchanged (bb8e).
2) Sentences that call a valuation figure a headwind or a tailwind are dropped whole (bb8e splitter), on the
   streamed text and the final reply; the prompt tells the model not to do it.
3) Sources list only what the final text cites, renumbered 1..n with the [n] markers rewritten to match (the
   done/JSON sources array is pruned the same way). The peer source is cited on the last comparison line and on
   the "In short" line instead of the header; move answers cite the quote source on the price lines.
4) House filings note: "Each filing links to the official House disclosure (PDF)."
5) Opening window: a cash venue (London, Xetra, Paris, US, Tokyo, Hong Kong, ...) that has opened (bb6 holidays
   respected; after a lunch break the reopen counts) but has no price from this session yet reads, until
   open + delayMin + 20 min: status "delayed", phase "opening", stale false, firstPriceAt (ISO, open + delayMin) and
   note "opening · first prices due HH:MM UK". bb5h stale thresholds do not fire in the window. Open quotes also
   carry lagMs = now - delayMin - quote ts (the delayed clock) for a 20-minute quiet rule.
6) POST /api/brief returns generatedAt (ISO) and generatedAtUk ("Mon 19 Oct, 07:05 UK") at the top level and
   inside brief, stamped when the brief was generated.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8e.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "e0a1e5ea2ba975298bd9a2177abd5a6f",
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
    print("bb8e %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8e before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8e %s untouched" % label)

if "// \u2500\u2500 bb8e \u2500\u2500" in v:
    print("REFUSE: bb8e already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8d marker", "// \u2500\u2500 bb8d \u2500\u2500"),
    ("bb8dDrop", "function bb8dDrop(sent, ok, facts) {"),
    ("bb8dCleanLine", "function bb8dCleanLine(line, ok, facts) {"),
    ("bb2PeerAsk", "function bb2PeerAsk(q) {"),
    ("bb2Read0", "var bb2Read0 = typeof readBody"),
    ("bb2System", "function bb2System(body, built, sources) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
    ("generateAi", "async function generateAi("),
    ("bb3bCompose", "function bb3bCompose(reply, built, cite) {"),
    ("bb2Footer", "function bb2Footer(sources) {"),
    ("bb7HouseView", "function bb7HouseView(index) {"),
    ("bb3Pack", "async function bb3Pack(now) {"),
    ("bb3OneQuote", "async function bb3OneQuote(pack, yahooSym) {"),
    ("bb3Compute", "async function bb3Compute(ticker, now) {"),
    ("bb3Known", "function bb3Known("),
    ("rt37sNews", "async function rt37sNews(res, url) {"),
    ("rt37sNewsCache", "const rt37sNewsCache = new Map();"),
    ("rt41sPeerBlock", "async function rt41sPeerBlock(base) {"),
    ("bb5eApply", "function bb5eApply(q, symbol, hints, now) {"),
    ("bb5hRetouch", "function bb5hRetouch(q, now, cadence) {"),
    ("bb5gApply", "function bb5gApply(q, symbol, now, cadence) {"),
    ("bb5eParts", "function bb5eParts(tz, d) {"),
    ("bb5eOpenAt", "function bb5eOpenAt(spec, d) {"),
    ("bb6Shut", "function bb6Shut(spec, d) {"),
    ("rt33sBriefDate", "function rt33sBriefDate(b) {"),
    ("json", "function json(res, status, body, extraHeaders = {}) {"),
    ("bb5gJoinStream", "function bb5gJoinStream(acc, piece, firstModel) {"),
]
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
print("bb8e anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8e ── Ask relevance: card and non-valuation questions lead with the card's reason (move, SPY and sector, headlines);
// the peer valuation block and "In short" stay for valuation or peer questions only. Valuation figures are never called
// headwinds or tailwinds. Sources list only what the final text cites, renumbered 1..n. Plain-English House note.
// Quotes in a venue's first open + delay + 20 minutes read status "delayed", phase "opening" instead of stale.
// /api/brief carries generatedAt (ISO) and generatedAtUk ("Mon 19 Oct, 07:05 UK").
// BB8E_JS
var BB8E_WAIT_MS = 3000;
var BB8E_NEWS_MS = 1500;
// Opinion and promotional outlets are not used as "in the news" lines.
var BB8E_OPINION_HOSTS = /^https?:\/\/(?:[a-z0-9-]+\.)*(?:fool\.com|investorplace\.com|247wallst\.com|zacks\.com|seekingalpha\.com|barchart\.com|benzinga\.com|insidermonkey\.com|gurufocus\.com|simplywall\.st)\//i;
var BB8E_HOUSE_NOTE = "Each filing links to the official House disclosure (PDF).";
var BB8E_SECTOR = {
  SOXX: ["MU", "NVDA", "AMD", "AVGO", "INTC", "TSM", "QCOM", "MRVL", "TXN", "AMAT", "LRCX", "ARM", "ASML", "SMCI", "WDC"],
  XLK: ["AAPL", "MSFT", "ORCL", "CRM", "ADBE", "NOW", "INTU", "CSCO", "ACN", "PLTR", "PANW", "CRWD", "SNOW", "NET", "DDOG", "ZS", "SHOP"],
  XLC: ["GOOGL", "META", "NFLX", "DIS", "T", "VZ", "TMUS", "CMCSA", "SNAP", "PINS", "SPOT"],
  XLY: ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "GM", "F", "RIVN", "ABNB", "DASH", "UBER", "TM"],
  XLF: ["JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "V", "MA", "PYPL", "COIN", "HOOD"],
  XLE: ["XOM", "CVX", "COP", "EOG", "SLB", "SHEL", "BP"],
  XLV: ["UNH", "LLY", "JNJ", "PFE", "MRK", "ABBV", "ABT", "TMO", "AMGN", "GILD", "BMY", "ISRG", "REGN", "VRTX", "CVS", "CI", "ELV", "HUM"],
  XLP: ["WMT", "COST", "KO", "PEP", "PG", "PM"],
  XLI: ["CAT", "DE", "HON", "BA", "LMT", "RTX", "UPS"]
};
var BB8E_SECTOR_NAME = { SOXX: "SOXX (semiconductor ETF)", XLK: "XLK (technology ETF)", XLC: "XLC (communication services ETF)", XLY: "XLY (consumer discretionary ETF)", XLF: "XLF (financials ETF)", XLE: "XLE (energy ETF)", XLV: "XLV (health care ETF)", XLP: "XLP (consumer staples ETF)", XLI: "XLI (industrials ETF)" };
var BB8E_BENCH = { L: ["^FTSE", "The FTSE 100"], T: ["^N225", "The Nikkei 225"], HK: ["^HSI", "The Hang Seng"], DE: ["^GDAXI", "The DAX"], PA: ["^FCHI", "The CAC 40"] };
// Client notes appended to the question ("[Answer this question as asked, about MU. Quote valuation only ...]") are not the question.
function bb8eStrip(q) {
  return String(q == null ? "" : q).replace(/\s*\[(?:Answer|Quote|Leave)[^\]]*\]\s*$/g, "").replace(/\s*\[(?:Answer|Quote|Leave)[^\]]*\]\s*$/g, "").trim();
}
function bb8eIsCard(q, body) {
  try { if (body && (body.card === true || /^(?:card|pulse)$/i.test(String(body.card || body.intent || body.origin || "")))) return true; } catch (e) {}
  return /\s[—–-]\s*(?:Headwind|Tailwind|Neutral fit|Regime-aligned|Neutral)\b/.test(String(q || ""));
}
function bb8eIsValuation(q) {
  var s = String(q || "");
  if (/\b(?:valuations?|valued|p\/e|pe ratio|price[- ]to[- ](?:earnings|sales|book)|ev\/ebitda|p\/s|p\/b|multiples?|cheap(?:er|est)?|expensive|premium|discount|earnings yield|peers?)\b/i.test(s)) return true;
  if (/\b(?:compar\w*|versus|vs\.?|relative to|against)\b/i.test(s) && !/\b(?:perform\w*|move[ds]?|moving|returns?|fell|fall(?:ing|en)?|rose|rise|rising|drop\w*|gain\w*|rall\w*|slump\w*|today|this week|session)\b/i.test(s)) return true;
  return false;
}
// Deterministic intent: card flag or card label wins, then valuation/peer keywords, otherwise the move.
function bb8eIntent(q, body) {
  var clean = bb8eStrip(q);
  if (bb8eIsCard(clean, body)) return { mode: "move", card: true, q: clean };
  if (bb8eIsValuation(clean)) return { mode: "valuation", card: false, q: clean };
  return { mode: "move", card: false, q: clean };
}
function bb8eBaseOf(q, body) {
  var b = null;
  try { b = typeof bb2Base === "function" ? bb2Base(q) : null; } catch (e) { b = null; }
  if (b) return b;
  var list = body && Array.isArray(body.tickers) ? body.tickers : [];
  for (var i = 0; i < list.length; i++) {
    var t = String(list[i] || "").toUpperCase();
    if (/^[A-Z][A-Z0-9.\-]{0,9}$/.test(t)) return t;
  }
  return null;
}
// A valuation figure labelled a headwind or tailwind (e.g. "a headwind is its trailing P/E 11.8x").
function bb8eContra(sentence) {
  var s = String(sentence || "");
  if (!/\b(?:head|tail)[- ]?winds?\b/i.test(s)) return false;
  return /\bP\/E\b|\bPE\b|price[- ]to[- ](?:earnings|sales|book)|\bvaluations?\b|\bvalued\b|\bmultiples?\b|\bP\/S\b|\bP\/B\b|EV\/EBITDA|\bcheap\w*|\bexpensive\b|earnings yield|\d(?:\.\d+)?\s*[x×](?!\w)/i.test(s);
}
function bb8eMs(q) {
  var n = Number(q && q.ts);
  if (!isFinite(n) || n <= 0) return 0;
  return n < 1e12 ? n * 1000 : n;
}
function bb8ePx(v, ccy) {
  var n = Number(v);
  if (!isFinite(n)) return "";
  var s = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return !ccy || ccy === "USD" ? "$" + s : s + " " + ccy;
}
function bb8ePct(c) { return Math.abs(Number(c)).toFixed(2) + "%"; }
function bb8eVerb(c, closed) {
  var n = Number(c);
  if (Math.abs(n) < 0.005) return closed ? "was unchanged" : "is unchanged";
  return closed ? (n < 0 ? "fell " : "rose ") + bb8ePct(n) : (n < 0 ? "is down " : "is up ") + bb8ePct(n);
}
function bb8eRel(base, c, other, target) {
  var d = Number(c) - Number(other);
  if (!isFinite(d)) return "";
  if (Math.abs(d) < 0.05) return base + " moved in line with " + target;
  return base + (d < 0 ? " lagged " : " outperformed ") + target + " by " + Math.abs(d).toFixed(2) + " percentage points";
}
function bb8eBench(base) {
  var m = /\.([A-Z]{1,2})$/.exec(String(base || ""));
  if (m) { var b = BB8E_BENCH[m[1]]; return b ? { sym: b[0], label: b[1] } : null; }
  return { sym: "SPY", label: "SPY (S&P 500 ETF)" };
}
function bb8eSector(base) {
  var keys = Object.keys(BB8E_SECTOR);
  for (var i = 0; i < keys.length; i++) if (BB8E_SECTOR[keys[i]].indexOf(base) >= 0) return { sym: keys[i], label: BB8E_SECTOR_NAME[keys[i]] };
  return null;
}
function bb8eNeutralTitle(t) {
  var s = String(t || "");
  if (!s || s.length < 12) return false;
  return !/\b(?:buy|buying|sell|selling|undervalued|overvalued|opportunit\w*|bargain|price targets?|upside|downside|could be worth|should you|is it time|if i could|millionaire|forever|to own|to watch|top (?:stock|pick)s?|stocks? to|game[- ]changer|here'?s why|reasons? to|prediction|soar\w*|skyrocket\w*|no[- ]brainer|investors should|bull case|bear case|stock alert|retire\w*|passive income)\b/i.test(s) && !/\bbetter\b[^:]*\bstocks?\b/i.test(s) && !/\?\s*$/.test(s);
}
async function bb8eNewsItems(sym) {
  try {
    var hit = typeof rt37sNewsCache !== "undefined" && rt37sNewsCache ? rt37sNewsCache.get(sym) : null;
    if (hit && Date.now() - hit.at < 15 * 60000) return hit.items || [];
    if (typeof rt37sNews !== "function") return hit ? hit.items || [] : [];
    var got = null;
    var res = { writeHead: function () { return res; }, setHeader: function () {}, end: function (b) { try { got = JSON.parse(String(b)); } catch (e) { got = null; } } };
    var job = rt37sNews(res, new URL("http://local/api/ticker-news?symbol=" + encodeURIComponent(sym)));
    await Promise.race([job, new Promise(function (r) { setTimeout(r, BB8E_NEWS_MS); })]);
    return got && Array.isArray(got.items) ? got.items : [];
  } catch (e) { return []; }
}
function bb8ePickNews(items, base, name, quoteMs) {
  var stem = String(name || "").replace(/[,.]?\s+(?:Inc|Corp(?:oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd)\b[\s\S]*$/i, "").trim();
  var from = (quoteMs || Date.now()) - 72 * 3600000;
  var re = new RegExp("\\b(?:" + String(base).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + (stem.length >= 3 ? "|" + stem.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") : "") + ")\\b", "i");
  return (items || []).filter(function (it) {
    return it && it.title && /^https?:\/\//.test(String(it.link || "")) && !BB8E_OPINION_HOSTS.test(String(it.link)) && Number(it.ts) >= from && Number(it.ts) <= Date.now() + 3600000 && re.test(it.title) && bb8eNeutralTitle(it.title);
  }).sort(function (a, b) { return Number(b.ts) - Number(a.ts); }).slice(0, 2);
}
async function bb8eMovePack(base) {
  if (!base || typeof bb3Pack !== "function" || typeof bb3OneQuote !== "function") return null;
  var now = Date.now();
  var pack = await bb3Pack(now);
  var ysym = typeof bb3Yahoo === "function" ? bb3Yahoo(base) : base;
  var q = await bb3OneQuote(pack, ysym);
  if (!q || !(Number(q.p) > 0) || !isFinite(Number(q.c)) || q.basis === "none") return null;
  var bench = bb8eBench(base), sector = bb8eSector(base);
  var jobs = [
    bench ? bb3OneQuote(pack, bench.sym).catch(function () { return null; }) : null,
    sector && sector.sym !== base ? bb3OneQuote(pack, sector.sym).catch(function () { return null; }) : null,
    bb8eNewsItems(ysym)
  ];
  var fit = null;
  try { if (typeof bb3Known === "function" && bb3Known(base)) fit = (typeof bb3Hit === "function" && bb3Hit(base, now)) || (typeof bb3Compute === "function" ? await bb3Compute(base, now) : null); } catch (e) { fit = null; }
  var got = await Promise.all(jobs);
  var qMs = bb8eMs(q);
  return {
    base: base, ysym: ysym, q: q, ms: qMs,
    bench: bench && got[0] && isFinite(Number(got[0].c)) ? { sym: bench.sym, label: bench.label, q: got[0] } : null,
    sector: sector && got[1] && isFinite(Number(got[1].c)) ? { sym: sector.sym, label: sector.label, q: got[1] } : null,
    fit: fit && fit.label ? fit : null,
    news: bb8ePickNews(got[2], base, q.name, qMs)
  };
}
// Server-built lead for card / move questions. n0 = how many sources the prompt already numbered.
function bb8eLead(pack, card, n0) {
  var base = pack.base, q = pack.q, closed = String(q.status || "") === "closed" || /closed/i.test(String(q.note || ""));
  var uk = typeof bb8dUk === "function" ? bb8dUk(pack.ms || Date.now()) : "";
  var qn = n0 + 1, sources = [], lines = [];
  var iso = function (ms) { try { return new Date(ms).toISOString(); } catch (e) { return ""; } };
  sources.push({ name: "Yahoo Finance quote", link: "https://finance.yahoo.com/quote/" + encodeURIComponent(pack.ysym) + "/", asOf: iso(pack.ms || Date.now()), detail: [base, pack.bench && pack.bench.sym, pack.sector && pack.sector.sym].filter(Boolean).join(", ") + " last price and session change" });
  var head = card && pack.fit ? "Why " + base + " reads " + pack.fit.label + " (card score " + pack.fit.score + "/100), as of " + uk + ":" : base + "'s latest move, as of " + uk + ":";
  var prev = isFinite(Number(q.prev)) && Number(q.prev) > 0 ? " (previous close " + bb8ePx(q.prev, q.currency) + ")" : "";
  lines.push(base + " " + bb8eVerb(q.c, closed) + (closed ? " to " : " at ") + bb8ePx(q.p, q.currency) + (closed ? " in its last session" : "") + prev + ". [" + qn + "]");
  [pack.bench, pack.sector].forEach(function (o, k) {
    if (!o) return;
    lines.push(o.label + " " + bb8eVerb(o.q.c, closed) + " in the same session, so " + bb8eRel(base, q.c, o.q.c, k ? "its sector" : "the market") + ". [" + qn + "]");
  });
  if (pack.fit && pack.fit.reason) lines.push("Card score (Dispatch regime fit): " + String(pack.fit.reason).replace(/\s*The score starts at 50\.\s*/, " ").trim());
  pack.news.forEach(function (it, k) {
    var n = qn + 1 + k;
    sources.push({ name: "Yahoo Finance news", link: String(it.link).slice(0, 300), asOf: iso(Number(it.ts)), detail: String(it.title).slice(0, 140) });
    var when = typeof bb8dUk === "function" ? bb8dUk(Number(it.ts)) : "";
    lines.push("In the news" + (when ? " (" + when + ")" : "") + ", not confirmed as the cause: \"" + String(it.title).replace(/"/g, "'").trim() + "\" [" + n + "]");
  });
  var text = head + "\n" + lines.join("\n");
  var prompt = "CARD AND MOVE FACTS (server-computed, already shown to the reader; cite with these [n] markers):\n" + lines.join("\n") +
    "\n\nThis question is about " + (card ? "the Pulse card's reason" : "this name's latest move") + ": the price move and how it compares with " + (pack.bench ? pack.bench.sym.replace(/^\^/, "") : "the market") + (pack.sector ? " and its sector (" + pack.sector.sym + ")" : "") +
    ". Answer that first, in two to four sentences of extra context. Do not repeat the lines above. Do not discuss valuation multiples (P/E or similar) unless the question asks for them. Headlines are not confirmed causes: say they were reported and do not invent a catalyst.";
  return { text: text, paint: text.replace(/\s*\[\d+\]/g, ""), prompt: prompt, sources: sources };
}
async function bb8eWait(st) {
  if (!st || !st.bb8eMoveP) return null;
  if (st.bb8eMoveDone) return st.bb8eMoveR;
  var r = null;
  try { r = await Promise.race([st.bb8eMoveP, new Promise(function (res) { setTimeout(function () { res(null); }, BB8E_WAIT_MS); })]); } catch (e) { r = null; }
  st.bb8eMoveDone = true; st.bb8eMoveR = r;
  return r;
}
function bb8eSetLead(st, pack, n0) {
  if (!st || !pack || st.bb8eMove) return st && st.bb8eMove;
  try { st.bb8eMove = bb8eLead(pack, !!st.bb8eCard, n0); } catch (e) { st.bb8eMove = null; }
  return st.bb8eMove;
}
// Keep only cited sources, renumber 1..n in list order, and rewrite every [n] marker to match.
function bb8eCites(text, full) {
  var s = String(text || ""), n = (full || []).length, used = {};
  var re = /\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g;
  s.replace(re, function (m, g) { g.split(/\s*,\s*/).forEach(function (x) { var k = Number(x); if (k >= 1 && k <= n) used[k] = 1; }); return m; });
  var keep = Object.keys(used).map(Number).sort(function (a, b) { return a - b; });
  if (!keep.length) return { text: s, keep: null };
  var map = {}; keep.forEach(function (k, i) { map[k] = i + 1; });
  s = s.replace(/[ \t]*\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) {
    var out = [];
    g.split(/\s*,\s*/).forEach(function (x) { var k = map[Number(x)]; if (k && out.indexOf(k) < 0) out.push(k); });
    if (!out.length) return "";
    return (/^[ \t]/.test(m) ? " " : "") + out.map(function (k) { return "[" + k + "]"; }).join("");
  });
  return { text: s, keep: keep.map(function (k) { return k - 1; }) };
}
// Valuation answers: the peer source is cited on the lines that use it, not on the header.
function bb8eValCite(text, cite) {
  if (!cite) return text;
  var lines = String(text || "").split("\n"), mark = " [" + cite + "]", lastFact = -1, hit = false;
  for (var i = 0; i < lines.length; i++) {
    if (/^Peer comparisons\b[^\n]*:\s*\[\d+\]\s*$/.test(lines[i])) { lines[i] = lines[i].replace(/\s*\[\d+\]\s*$/, ""); hit = true; }
    if (typeof bb8dIsFact === "function" && bb8dIsFact(lines[i])) lastFact = i;
  }
  if (lastFact >= 0 && lines[lastFact].indexOf(mark) < 0) lines[lastFact] += mark;
  for (var j = lines.length - 1; j >= 0; j--) { if (/^In short:/.test(lines[j])) { if (lines[j].indexOf(mark) < 0) lines[j] += mark; break; } }
  return hit || lastFact >= 0 ? lines.join("\n") : text;
}
function bb8eFull(st) {
  var full = [];
  if (st && Array.isArray(st.clientSources)) full.push.apply(full, st.clientSources);
  if (st && st.peerSource) full.push(st.peerSource);
  if (st && st.bb8eMove && Array.isArray(st.bb8eMove.sources)) full.push.apply(full, st.bb8eMove.sources);
  return full;
}
// Streams the move-mode answer as whole cleaned sentences (same rules as the final reply).
function bb8ePainter(emit, sep0) {
  var pend = "", stop = false, sep = sep0 || "";
  function clean(line) { return typeof bb8dCleanLine === "function" ? bb8dCleanLine(line, {}, []) : line; }
  // emit(separator, text): the stream pump drops blank lines and edge newlines, so the separator travels separately.
  function paint(force) {
    if (stop) { pend = ""; return; }
    var nl = pend.lastIndexOf("\n");
    if (nl >= 0) {
      pend.slice(0, nl).split("\n").forEach(function (line) {
        if (stop) return;
        if (/^\s*(?:\*\*)?Sources?:/i.test(line)) { stop = true; return; }
        if (!line.trim()) { if (sep) sep = "\n\n"; return; }
        var c = clean(line);
        if (c) { emit(sep, c); sep = "\n"; }
        else if (sep === " ") sep = "\n";
      });
      pend = pend.slice(nl + 1);
    }
    if (!stop && pend) {
      if (/^\s*(?:\*\*)?Sources?:/i.test(pend)) { if (force) stop = true; }
      else {
        var parts = bb8dSplit(pend), done = force ? parts : parts.slice(0, -1);
        if (done.length) {
          var c2 = clean(done.join(" "));
          if (c2) { emit(sep, c2); sep = " "; }
          if (force) pend = "";
          else { var last = parts[parts.length - 1] || "", at = last ? pend.lastIndexOf(last) : -1; pend = at >= 0 ? pend.slice(at) : last; }
        }
        if (force) pend = "";
      }
    }
  }
  return { push: function (d) { if (typeof d === "string") { pend += d; paint(false); } }, flush: function () { paint(true); } };
}
var BB8E_QUIET_MS = 20 * 60000;
// Today's session start for a cash venue (after the lunch break when one applies), in ms; 0 when not open now.
function bb8eOpenMs(spec, t) {
  if (!spec || spec.mode !== "cash" || typeof bb5eParts !== "function") return 0;
  var d = new Date(t);
  try { if (typeof bb6Shut === "function" && bb6Shut(spec, d)) return 0; } catch (e) {}
  if (typeof bb5eOpenAt === "function" && !bb5eOpenAt(spec, d)) return 0;
  var p = bb5eParts(spec.tz, d);
  var start = spec.lo != null && p.m >= spec.lc ? spec.lc : spec.o;
  if (!(p.m >= start)) return 0;
  return Math.floor(t / 60000) * 60000 - (p.m - start) * 60000;
}
function bb8eTsMs(q) {
  var ts = Number(q && q.ts);
  return ts > 0 && ts < 1e12 ? ts * 1000 : (ts > 0 ? ts : 0);
}
// Opening window: open..open+delay+20 min with no price from this session yet. Returns null outside it.
function bb8eOpening(q, symbol, t) {
  var spec = null;
  try { spec = typeof bb5gSpec === "function" ? bb5gSpec(symbol) : (typeof bb5eSpec === "function" ? bb5eSpec(symbol) : null); } catch (e) { spec = null; }
  if (spec && symbol) spec.bb6Sym = symbol;
  var openMs = bb8eOpenMs(spec, t);
  if (!openMs) return null;
  var delay = Math.round(Number(q && q.delayMin));
  if (!isFinite(delay) || delay < 0) delay = 0;
  var firstMs = openMs + delay * 60000, untilMs = firstMs + BB8E_QUIET_MS;
  if (t >= untilMs) return null;
  var tsMs = bb8eTsMs(q);
  if (tsMs && tsMs >= openMs) return null;
  return { openMs: openMs, firstMs: firstMs, untilMs: untilMs, delay: delay };
}
function bb8eHm(ms) {
  var s = typeof bb8dUkMs === "function" ? bb8dUkMs(ms) : "";
  var m = /(\d{2}:\d{2})$/.exec(s);
  return m ? m[1] : "";
}
function bb8eMarkOpening(out, w) {
  out.status = "delayed";
  out.phase = "opening";
  out.stale = false;
  out.delayMin = w.delay;
  out.firstPriceAt = new Date(w.firstMs).toISOString();
  var hm = bb8eHm(w.firstMs);
  out.note = hm ? "opening · first prices due " + hm + " UK" : "opening";
  delete out.nextOpen;
  return out;
}
var BB8E_RULE = "Never describe a valuation figure (P/E, P/S, P/B, EV/EBITDA or any multiple) as a headwind or a tailwind.";
try {
  if (typeof bb8dDrop === "function") {
    var bb8eDrop0 = bb8dDrop;
    bb8dDrop = function (sent) { if (bb8eContra(sent)) return true; return bb8eDrop0.apply(this, arguments); };
  }
  if (typeof bb2PeerAsk === "function") {
    var bb8ePeer0 = bb2PeerAsk;
    bb2PeerAsk = function (q) {
      var st = bb8dStore();
      var it = bb8eIntent(q, st && st.bb8eBody);
      if (it.mode !== "valuation") return false;
      return bb8ePeer0.call(this, it.q) || true;
    };
  }
  if (typeof bb2Read0 === "function") {
    var bb8eRead0 = bb2Read0;
    bb2Read0 = async function () {
      var body = await bb8eRead0.apply(this, arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && body && typeof body === "object" && !st.bb8eSeen) {
          st.bb8eSeen = true;
          st.bb8eBody = body;
          var q = typeof bb2Question === "function" ? bb2Question(body) : "";
          var it = bb8eIntent(q, body);
          st.bb8eMode = it.mode; st.bb8eCard = it.card;
          st.bb8eBase = it.mode === "move" ? bb8eBaseOf(q, body) : null;
          if (st.bb8eBase) { st.bb8eMoveP = bb8eMovePack(st.bb8eBase); st.bb8eMoveP.catch(function () {}); }
        }
      } catch (e) {}
      return body;
    };
  }
  if (typeof bb2System === "function") {
    var bb8eSystem0 = bb2System;
    bb2System = function () { return bb8eSystem0.apply(this, arguments) + "\n\n" + BB8E_RULE; };
  }
  if (typeof bb2Complete === "function") {
    var bb8eComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var self = this, st = bb8dStore();
      if (!st || st.bb8eMode !== "move" || !st.bb8eBase) return bb8eComplete0.apply(self, arguments);
      return (async function () {
        var pack = await bb8eWait(st);
        var n0 = (Array.isArray(st.clientSources) ? st.clientSources.length : 0) + (st.peerSource ? 1 : 0);
        var lead = pack ? bb8eSetLead(st, pack, n0) : null;
        var sys = String(system || "").replace("Do not write a concluding or summary sentence; the server adds it.", "Do not write a concluding or summary sentence.");
        if (lead) { sys = lead.prompt + "\n\n" + sys; try { if (typeof onDelta === "function") onDelta(lead.paint + "\n"); } catch (e) {} }
        var painter = bb8ePainter(function (sep, t) {
          if (typeof onDelta !== "function") return;
          st.bb8eNextSep = sep;
          try { onDelta(String(t).replace(/[ \t]*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, "") + "\n"); } finally { st.bb8eNextSep = null; }
        }, lead ? "\n\n" : "");
        var r = await bb8eComplete0.call(self, sys, messages, function (d) { painter.push(d); });
        painter.flush();
        return r;
      })();
    };
  }
  if (typeof generateAi === "function") {
    var bb8eGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && options && typeof options.system === "string") {
          var extra = BB8E_RULE;
          if (st.bb8eMode === "move" && st.bb8eBase) {
            var pack = await bb8eWait(st);
            if (!Array.isArray(st.clientSources) && st.body && typeof bb2ClientSources === "function") st.clientSources = bb2ClientSources(st.body);
            var lead = pack ? bb8eSetLead(st, pack, (Array.isArray(st.clientSources) ? st.clientSources.length : 0) + (st.peerSource ? 1 : 0)) : null;
            if (lead) extra = lead.prompt + "\n\n" + extra + " Do not write a concluding or summary sentence.";
          }
          args[0] = Object.assign({}, options, { system: extra + "\n\n" + options.system });
        }
      } catch (e) {}
      return bb8eGen0.apply(this, args);
    };
  }
  if (typeof bb3bCompose === "function") {
    var bb8eCompose0 = bb3bCompose;
    bb3bCompose = function (reply, built, cite) {
      var st = bb8dStore();
      var facts = built && Array.isArray(built.facts) ? built.facts : [];
      var out;
      if (!facts.length && st && st.bb8eMode === "move" && st.bb8eBase) {
        var raw = typeof st.bb8dRaw === "string" && st.bb8dRaw ? st.bb8dRaw : String(reply == null ? "" : reply);
        var body = bb8dUkText(bb8dBody(raw, []));
        var lead = st.bb8eMove ? st.bb8eMove.text : "";
        out = [lead, body].filter(function (x) { return x && x.trim(); }).join("\n\n");
        if (!out) out = bb8eCompose0.apply(this, arguments);
      } else {
        out = bb8eCompose0.apply(this, arguments);
        if (facts.length && cite) out = bb8eValCite(out, cite);
      }
      if (st) {
        var full = bb8eFull(st), r = bb8eCites(out, full);
        st.bb8eCites = r.keep ? { full: full, keep: r.keep } : null;
        out = r.text;
      }
      return out;
    };
  }
  if (typeof bb2Footer === "function") {
    var bb8eFooter0 = bb2Footer;
    bb2Footer = function (sources) {
      try {
        var st = bb8dStore(), c = st && st.bb8eCites;
        if (c && Array.isArray(sources) && c.keep && c.keep.length) {
          var same = sources.every(function (s, i) { return s === c.full[i]; });
          if (same) { var next = c.keep.map(function (i) { return c.full[i]; }); sources.length = 0; next.forEach(function (x) { sources.push(x); }); }
        }
      } catch (e) {}
      return bb8eFooter0.apply(this, arguments);
    };
  }
  if (typeof bb5gJoinStream === "function") {
    var bb8eJoin0 = bb5gJoinStream;
    bb5gJoinStream = function (acc, piece, firstModel) {
      try {
        var st = bb8dStore();
        if (st && st.bb8eNextSep != null && typeof piece === "string" && piece.trim()) {
          var sep = st.bb8eNextSep;
          st.bb8eNextSep = null;
          if (sep && !/\s$/.test(String(acc || ""))) piece = sep + piece.replace(/^\s+/, "");
        }
      } catch (e) {}
      return bb8eJoin0.call(this, acc, piece, firstModel);
    };
  }
  // The JSON handler's own peer block (rt41s) is left out of move answers; valuation answers keep it.
  if (typeof rt41sPeerBlock === "function") {
    var bb8ePb0 = rt41sPeerBlock;
    rt41sPeerBlock = async function () {
      var st = bb8dStore();
      if (st && st.chat && st.bb8eMode === "move") return "";
      return bb8ePb0.apply(this, arguments);
    };
  }
  if (typeof bb5eApply === "function") {
    var bb8eApply0 = bb5eApply;
    bb5eApply = function (q, symbol, hints, now) {
      var out = bb8eApply0.apply(this, arguments);
      try {
        if (!out || typeof out !== "object" || out === q) return out;
        var t = now == null ? (typeof bb5eNow === "function" ? bb5eNow() : Date.now()) : Number(now);
        if (!isFinite(t)) t = Date.now();
        var open = out.status !== "closed" && out.status !== "quiet";
        var w = open ? bb8eOpening(out, symbol, t) : null;
        if (w) return bb8eMarkOpening(out, w);
        if (out.phase === "opening") { delete out.phase; delete out.firstPriceAt; }
        if (open) {
          var tsMs = bb8eTsMs(out), delay = Math.max(0, Math.round(Number(out.delayMin)) || 0);
          // Age of the newest print against the delayed clock (now minus the exchange delay), for a 20-minute quiet rule.
          if (tsMs) out.lagMs = Math.max(0, t - delay * 60000 - tsMs);
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb5hRetouch === "function") {
    var bb8eRetouch0 = bb5hRetouch;
    bb5hRetouch = function (q, now) {
      try {
        if (q && q.phase === "opening" && q.firstPriceAt) {
          var t = Number(now);
          if (!isFinite(t)) t = Date.now();
          if (t < Date.parse(q.firstPriceAt) + BB8E_QUIET_MS) return q;
        }
      } catch (e) {}
      return bb8eRetouch0.apply(this, arguments);
    };
  }
  if (typeof bb5gApply === "function") {
    var bb8eGApply0 = bb5gApply;
    bb5gApply = function () {
      var out = bb8eGApply0.apply(this, arguments);
      try { if (out && out.phase === "opening") out.stale = false; } catch (e) {}
      return out;
    };
  }
  // /api/brief: the time the brief was written (generation finished), not a later read.
  if (typeof rt33sBriefDate === "function") {
    var bb8eBrief0 = rt33sBriefDate;
    rt33sBriefDate = function (b) {
      var out = bb8eBrief0.apply(this, arguments);
      try {
        if (out && typeof out === "object" && !out.generatedAt) {
          var ms = Date.now();
          out.generatedAt = new Date(ms).toISOString();
          out.generatedAtUk = typeof bb8dUk === "function" ? bb8dUk(ms) : "";
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof json === "function") {
    var bb8eJson0 = json;
    json = function (res, status, body) {
      try {
        if (body && typeof body === "object" && body.brief && typeof body.brief === "object" && body.brief.generatedAt && body.generatedAt == null) {
          body.generatedAt = body.brief.generatedAt;
          body.generatedAtUk = body.brief.generatedAtUk || "";
        }
      } catch (e) {}
      return bb8eJson0.apply(this, arguments);
    };
  }
  if (typeof bb7HouseView === "function") {
    var bb8eHouse0 = bb7HouseView;
    bb7HouseView = function () {
      var out = bb8eHouse0.apply(this, arguments);
      if (out && /No PDF text library/.test(String(out.note || ""))) out.note = BB8E_HOUSE_NOTE;
      return out;
    };
  }
} catch (e) { console.warn("bb8e hooks skipped", e && e.message); }
// BB8E_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8e")]
if bad:
    die("bb8e block declares a non-bb8e function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8e block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8e function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8e block has a forbidden declaration")

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
print("bb8e setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8ebak"
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
print("APPLY bb8e card/move Ask relevance + cited-only sources + House note + opening window + brief generatedAt")
