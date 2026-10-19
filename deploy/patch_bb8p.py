#!/usr/bin/env python3
"""patch_bb8p.py — P0 hotfix (QA chat75): one grounding rule on both /api/chat paths, a hard numeric guard (a figure
that is not in the prompt the model received is dropped with its sentence, before the bb8m trim and bb8n pruning;
nothing left -> an honest "not in our feed" answer with related live Yahoo quotes and topic news), topic-relevant
news sources only, meta.provider/meta.model for admins only (isAdminUser), meta.quote (the quote the answer used)
and meta.grounding, and brief answers keep the question's timeframe sentence.
Server.js only. Stacked on bb8n (live server md5 9b48a917c654891a50e7c7c6bd8c9a49). Does not rewrite app.js or index.html.
No tables, intervals, timers, dependencies, secrets or Stripe changes. See docs/bb8p.md.
Usage: python3 patch_bb8p.py [--check] <dir with server.js>
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
    print("bb8p %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8p before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8p %s untouched" % label)

if "// \u2500\u2500 bb8p \u2500\u2500" in v:
    print("REFUSE: bb8p already applied")
    sys.exit(0)

REPLACE = [
]
REQUIRED = [
    ("bb8n end", "// BB8N_JS_END"),
    ("bb8iKeep", "function bb8iKeep(sent, resolve, st) {"),
    ("bb8iLine", "function bb8iLine(line, resolve, st) {"),
    ("bb8iGeneral", "function bb8iGeneral(st) {"),
    ("bb8iNewsMatch", "function bb8iNewsMatch(sent, src) {"),
    ("bb8iIsNews", "function bb8iIsNews(src, st) {"),
    ("bb8jSources", "function bb8jSources(body) {"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb8mTrim", "function bb8mTrim(reply, max) {"),
    ("bb8mScopeOf", "function bb8mScopeOf(q, body) {"),
    ("bb8mClean", "function bb8mClean(q) {"),
    ("bb8mUnits", "function bb8mUnits(text) {"),
    ("bb2System", "function bb2System(body, built, sources) {"),
    ("bb2OpenAi", "async function bb2OpenAi(cfg, system, messages, onDelta) {"),
    ("bb2Gemini", "async function bb2Gemini(cfg, system, messages, onDelta) {"),
    ("bb3bGenerateAi", "async function bb3bGenerateAi(options) {"),
    ("bb3bGenerateAi call", "  return bb3bGenerateAi(options);"),
    ("openai-slot clip", "  var system = typeof clipped === \"function\" ? clipped(options && options.system, 5000) : String((options && options.system) || \"\");"),
    ("buildChatLiveMarketBlock", "async function buildChatLiveMarketBlock() {"),
    ("lastChatLiveSnapshot", "let lastChatLiveSnapshot = {};"),
    ("bb3OneQuote", "async function bb3OneQuote(pack, yahooSym) {"),
    ("isAdminUser", "function isAdminUser(user) {"),
    ("/api/ai-status admin check", "    if (!isAdminUser(rt17AiUser)) return json(res, rt17AiUser ? 403 : 401, { error: \"Administrator access required.\" });"),
    ("stream done meta", "    send({ done: true, reply: reply, meta: { provider: meta.provider, model: meta.model, streamed: true }, sources: footSources });"),
    ("bb8m handle hook", "    var bb8mHandle0 = handle;"),
    ("bb8dStore", "function bb8dStore() {"),
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
print("bb8p anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8p ── One grounding rule on both /api/chat paths; hard numeric guard; topic-relevant news only;
// provider/model for admins only; the answer's quote in meta; brief answers keep the question's timeframe.
// BB8P_JS
// Root cause (QA chat75, China GDP from the MU page): the stream prompt is built by bb2System, written for the
// bb2 peer-valuation stream. It never carried the JSON route's grounding text (MARKET_SYSTEM "Use only the supplied
// market context ... Do not claim real-time facts that were not provided" and "Answer using ONLY the supplied
// terminal context ... say plainly when a figure is unavailable"). bb8j/bb8k/bb8m harmonised sources, hints, length
// and scope, never grounding, and bb8m's detailed LENGTH rule ("200 to 350 words ... three to five paragraphs")
// pushed the stream model to fill space with figures it did not have. The JSON route also clips its system prompt
// at 5000 characters (openai-slot / provider calls), so on long contexts its tail (CITABLE SOURCES, bb8i rule) was cut.
// bb8p: (1) one rule, BB8P_GROUND, is put first in the final system prompt of both paths at the provider call
// (stream bb2OpenAi/bb2Gemini, JSON bb3bGenerateAi), and a chat system prompt is clipped at 14000 on both paths;
// (2) every model sentence goes through bb8pFigs at the same place bb8i drops speculative claims (bb8iKeep; painted
// and final text, both paths): a figure that is not in the prompt the model received is dropped with its sentence,
// before the bb8m trim and bb8n pruning; if nothing substantive is left, the answer says the data is not in our feed
// and gives related live Yahoo quotes and topic news instead; (3) client news sources must match the question's
// topic (bb8pTopic); (4) meta.provider/meta.model only for admins (isAdminUser, as /api/ai-status); (5) meta.quote;
// (6) timeframe kept by the brief trim. No tables, intervals, timers, secrets or billing changes.
var BB8P_GROUND = "GROUNDING (both answer paths; overrides any length target): use only the facts, figures and headlines supplied in this prompt. Never state a figure (percentage, price, currency amount, rate, growth figure, basis points, multiple, date or quarterly result) that is not written in the supplied text: the server deletes every sentence with an unsupported figure. Do not name causes or drivers unless a supplied headline names them, and cite it. If the data the question asks for is not supplied, say plainly that it is not in our feed and give what is supplied that relates to it, with its [n]. If the question names a timeframe (today, this week, this month), answer for that timeframe in the first sentence.";
var BB8P_CLIP = 14000;
var BB8P_REL_MS = 2500;
var BB8P_GOLD_MS = 3000;
var BB8P_MIN_WORDS = 25;
var BB8P_MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12 };
var BB8P_MON_RE = "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)";
// Topic groups. kind: entity (country/region/asset) or series (macro data). rel: related free Yahoo symbols.
var BB8P_TOPICS = [
  { id: "china", kind: "entity", label: "China", re: /\b(?:china|chinese|beijing|pboc|yuan|renminbi|cnh|cny|shanghai|shenzhen|hang seng|hong kong)\b/i, rel: [["CNH=X", "USD/CNH (offshore yuan)", 4], ["^HSI", "the Hang Seng", 2], ["HG=F", "copper (HG=F futures)", 3]] },
  { id: "japan", kind: "entity", label: "Japan", re: /\b(?:japan|japanese|boj|bank of japan|yen|nikkei|tokyo)\b/i, rel: [["^N225", "the Nikkei 225", 2], ["JPY=X", "USD/JPY", 2]] },
  { id: "uk", kind: "entity", label: "UK", re: /\b(?:UK|U\.K\.|britain|british|united kingdom|england|bank of england|BoE|gilts?|sterling|the pound|FTSE|ONS)\b/, rel: [["GBPUSD=X", "GBP/USD", 4], ["^FTSE", "the FTSE 100", 2]] },
  { id: "us", kind: "entity", label: "US", re: /\b(?:US|U\.S\.|USA|united states|america|american|Fed|federal reserve|FOMC|Powell|Treasur(?:y|ies)|wall street|S&P|Nasdaq|Dow)\b/, rel: [["^GSPC", "the S&P 500", 2], ["^TNX", "the US 10-year Treasury yield", 2], ["DX-Y.NYB", "the dollar index (DXY)", 2]] },
  { id: "euro", kind: "entity", label: "euro area", re: /\b(?:euro ?zone|euro area|ECB|Lagarde|european union|EU)\b/, rel: [["EURUSD=X", "EUR/USD", 4], ["^STOXX50E", "the Euro Stoxx 50", 2]] },
  { id: "germany", kind: "entity", label: "Germany", re: /\b(?:germany|german|bunds?|DAX|bundesbank)\b/i, rel: [["^GDAXI", "the DAX", 2], ["EURUSD=X", "EUR/USD", 4]] },
  { id: "france", kind: "entity", label: "France", re: /\b(?:france|french|CAC)\b/i, rel: [["^FCHI", "the CAC 40", 2], ["EURUSD=X", "EUR/USD", 4]] },
  { id: "india", kind: "entity", label: "India", re: /\b(?:india|indian|rbi|rupee|sensex|nifty)\b/i, rel: [["^NSEI", "the Nifty 50", 2], ["INR=X", "USD/INR", 3]] },
  { id: "korea", kind: "entity", label: "South Korea", re: /\b(?:korea|korean|kospi|won)\b/i, rel: [["^KS11", "the KOSPI", 2]] },
  { id: "asia", kind: "entity", label: "Asia", re: /\b(?:asia|asian)\b/i, rel: [["^HSI", "the Hang Seng", 2], ["^N225", "the Nikkei 225", 2], ["^KS11", "the KOSPI", 2]] },
  { id: "gold", kind: "entity", label: "gold", re: /\b(?:gold|bullion|XAU|precious metals?)\b/i, rel: [["GC=F", "gold (GC=F, COMEX futures)", 2]] },
  { id: "silver", kind: "entity", label: "silver", re: /\b(?:silver|XAG)\b/i, rel: [["SI=F", "silver (SI=F futures)", 2]] },
  { id: "oil", kind: "entity", label: "oil", re: /\b(?:oil|crude|brent|WTI|OPEC)\b/i, rel: [["CL=F", "WTI crude (CL=F)", 2], ["BZ=F", "Brent crude (BZ=F)", 2]] },
  { id: "copper", kind: "entity", label: "copper", re: /\bcopper\b/i, rel: [["HG=F", "copper (HG=F futures)", 3]] },
  { id: "crypto", kind: "entity", label: "crypto", re: /\b(?:bitcoin|BTC|ether(?:eum)?|ETH|crypto(?:currenc(?:y|ies))?)\b/i, rel: [["BTC-USD", "bitcoin", 2], ["ETH-USD", "ether", 2]] },
  { id: "dollar", kind: "entity", label: "the dollar", re: /\b(?:dollar|DXY|greenback)\b/i, rel: [["DX-Y.NYB", "the dollar index (DXY)", 2]] },
  { id: "gdp", kind: "series", label: "GDP", re: /\b(?:GDP|gross domestic product|economic growth|economy grew|economy shrank|recession)\b/i },
  { id: "inflation", kind: "series", label: "inflation", re: /\b(?:inflation|CPI|PPI|PCE|consumer prices|deflation)\b/i },
  { id: "jobs", kind: "series", label: "jobs", re: /\b(?:jobs|payrolls?|non-?farm|unemployment|jobless|employment|labou?r market|wages?)\b/i },
  { id: "rates", kind: "series", label: "interest rate", re: /\b(?:interest rates?|rate (?:cuts?|hikes?|decision)|central bank|monetary policy|bond yields?|yield curve)\b/i },
  { id: "pmi", kind: "series", label: "PMI", re: /\b(?:PMI|ISM|purchasing managers)\b/i },
  { id: "retail", kind: "series", label: "retail sales", re: /\b(?:retail sales|consumer spending)\b/i },
  { id: "trade", kind: "series", label: "trade", re: /\b(?:exports?|imports?|trade (?:balance|deficit|surplus|data)|tariffs?)\b/i },
  { id: "housing", kind: "series", label: "housing", re: /\b(?:house prices|housing|home sales|mortgages?)\b/i }
];
var BB8P_SECTOR_SYN = { semiconductors: "semiconductor|chip|chips|chipmaker|semis", memory: "memory|dram|nand|hbm" };
function bb8pSt() { try { var st = typeof bb8dStore === "function" ? bb8dStore() : null; return st && st.chat ? st : null; } catch (e) { return null; } }
function bb8pQuestion(body) {
  var q = typeof bb2Question === "function" ? bb2Question(body) : "";
  return typeof bb8mClean === "function" ? bb8mClean(q) : String(q || "");
}
// ── (3) Topic and source relevance ──
// Topic of one question: entity groups (country, region, asset) and series groups (GDP, inflation, ...) it names;
// for a ticker question (bb8m scope not general: card prompt, or names the ticker/company, or no macro word at all
// with a page ticker open), the ticker, its company stem and its sector words from the Active ticker line.
function bb8pTopic(body) {
  var q = bb8pQuestion(body), out = { q: q, entities: [], series: [], ticker: null, terms: null, mode: "none" };
  var sc = null;
  try { sc = typeof bb8mScopeOf === "function" ? bb8mScopeOf(typeof bb2Question === "function" ? bb2Question(body) : q, body) : null; } catch (e) { sc = null; }
  BB8P_TOPICS.forEach(function (t) { if (t.re.test(q)) (t.kind === "entity" ? out.entities : out.series).push(t); });
  var page = sc && sc.page ? sc.page : (typeof bb8mPage === "function" ? bb8mPage(body, typeof bb2Question === "function" ? bb2Question(body) : q) : null);
  if (sc && !sc.general && page && page.tk) {
    var ctx = body && typeof body.context === "string" ? body.context : "";
    var line = (ctx.match(/^Active ticker:[^\n]*$/m) || [""])[0];
    var terms = [page.tk.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")];
    var stem = String(page.name || "").replace(/[,.]?\s+(?:Inc|Corp(?:oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd|Platforms|Class [A-Z])\b.*$/i, "").trim();
    if (stem.length >= 3) terms.push(stem.replace(/[^A-Za-z0-9 ]/g, ""));
    line.split("\u00b7").slice(1).forEach(function (bit) { var w = bit.trim().toLowerCase(); if (BB8P_SECTOR_SYN[w]) terms.push(BB8P_SECTOR_SYN[w]); });
    out.ticker = page.tk; out.terms = new RegExp("\\b(?:" + terms.join("|") + ")\\b", "i"); out.mode = "ticker";
  } else if (out.entities.length || out.series.length) out.mode = "topic";
  return out;
}
// Relevance rule (documented in docs/bb8p.md): topic mode with entities and series -> a headline must match one
// named entity AND one named series ("China GDP" keeps "China GDP growth beats forecasts", drops "China stocks
// fall" and "UK GDP"); entities only -> one entity; series only -> one series; ticker mode -> the ticker, company
// stem or a sector word; no topic at all (home page, "what's moving markets?") -> the client list is unchanged.
// Server sources (Yahoo quote, peer valuations, Dispatch card, key statistics) are never filtered here.
function bb8pRelevant(src, topic) {
  if (!topic || topic.mode === "none") return true;
  var blob = String((src && src.detail) || "") + " " + String((src && src.title) || "");
  if (topic.mode === "ticker") return topic.terms.test(blob) || topic.terms.test(String((src && src.link) || "").replace(/[-_/]/g, " "));
  var hit = function (list) { return list.some(function (t) { return t.re.test(blob); }); };
  if (topic.entities.length && topic.series.length) return hit(topic.entities) && hit(topic.series);
  if (topic.entities.length) return hit(topic.entities);
  return hit(topic.series);
}
function bb8pIsServerSrc(src) {
  var name = String((src && src.name) || ""), link = String((src && src.link) || "");
  return name === "The Dispatch" || /^price feed$/i.test(name) || /quote|key statistics/i.test(name) || /\/quote\/|key-statistics/i.test(link) || (name === "Yahoo Finance" && !/\/news\//.test(link));
}
function bb8pFilter(list, body) {
  if (!Array.isArray(list)) return list;
  var st = bb8pSt();
  var topic = st && st.bb8pTopic ? st.bb8pTopic : bb8pTopic(body);
  if (st && !st.bb8pTopic) st.bb8pTopic = topic;
  var kept = list.filter(function (s) { return s && (bb8pIsServerSrc(s) || bb8pRelevant(s, topic)); });
  if (st) st.bb8pSrcDropped = (st.bb8pSrcDropped || 0) + (list.length - kept.length);
  return kept;
}
// ── (2) Numeric guard ──
function bb8pDec(s) { var m = String(s).match(/\.(\d+)/); return m ? m[1].length : 0; }
function bb8pMult(u) {
  u = String(u || "").toLowerCase();
  if (u === "k") return 1e3;
  if (u === "m" || u === "mn" || u === "million") return 1e6;
  if (u === "bn" || u === "billion") return 1e9;
  if (u === "tn" || u === "trillion") return 1e12;
  return 1;
}
function bb8pCls(cur, unit) {
  var u = String(unit || "").toLowerCase();
  if (/^(?:%|per ?cent|percent|percentage points?|pts?|pp)$/.test(u)) return "pct";
  if (/^(?:bps?|basis points?)$/.test(u)) return "bp";
  if (u === "x" || u === "\u00d7") return "x";
  if (cur) return "money";
  return "plain";
}
var BB8P_NUM = /(US\$|HK\$|C\$|A\$|[$\u00a3\u20ac\u00a5])?\s?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?:\s?(%|per ?cent\b|percent\b|percentage points?\b|pts?\b|pp\b|bps?\b|basis points?\b|x(?![A-Za-z])|\u00d7|k\b|mn\b|m\b|bn\b|tn\b|million\b|billion\b|trillion\b))?/g;
// Figures in one text: [{ v, d, cls, mult, raw, year }]. Masks [n] cites, times, tenors and index names first.
function bb8pMask(t) {
  return String(t || "")
    .replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ")
    .replace(/\b\d{1,2}:\d{2}(?::\d{2})?\b/g, " ")
    .replace(/\b(?:S&P|FTSE|Nikkei|DAX|CAC|Stoxx|STOXX|Euro Stoxx|Russell|ASX|Nasdaq|NASDAQ|Dow|KOSPI|Nifty|MSCI|G|SSE|CSI|Top)\s?\d{1,4}\b/g, " ")
    .replace(/\b\d{1,3}(?:-|\s)?(?:years?|yrs?|y|months?|mos?|weeks?|wks?|days?|sessions?|hours?|minutes?|mins?|quarters?)\b(?!\s*(?:high|low)s?\b)/gi, " ")
    .replace(/\b(?:Q[1-4]|H[12]|FY\s?\d{2,4})\b/g, " ");
}
function bb8pDates(t) {
  var out = [], s = String(t || "");
  var re1 = new RegExp("\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(" + BB8P_MON_RE + ")\\b", "gi");
  var re2 = new RegExp("\\b(" + BB8P_MON_RE + ")\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b", "gi");
  var m;
  while ((m = re1.exec(s))) out.push({ k: Number(m[1]) + "-" + BB8P_MONTHS[m[2].slice(0, 3).toLowerCase()], at: m.index, len: m[0].length });
  while ((m = re2.exec(s))) out.push({ k: Number(m[2]) + "-" + BB8P_MONTHS[m[1].slice(0, 3).toLowerCase()], at: m.index, len: m[0].length });
  var re3 = /\b(\d{4})-(\d{2})-(\d{2})\b/g;
  while ((m = re3.exec(s))) out.push({ k: Number(m[3]) + "-" + Number(m[2]), y: m[1], at: m.index, len: m[0].length });
  var re4 = /\b(\d{1,2})\/(\d{1,2})\/(\d{2,4})\b/g;
  while ((m = re4.exec(s))) out.push({ k: Number(m[1]) + "-" + Number(m[2]), y: m[3].length === 4 ? m[3] : "20" + m[3], at: m.index, len: m[0].length });
  return out;
}
function bb8pNums(t) {
  var s = bb8pMask(t), dates = bb8pDates(s), out = [];
  // Blank the date spans so their day numbers are not read as figures.
  dates.slice().sort(function (a, b) { return b.at - a.at; }).forEach(function (d) { s = s.slice(0, d.at) + new Array(d.len + 1).join(" ") + s.slice(d.at + d.len); });
  var m; BB8P_NUM.lastIndex = 0;
  while ((m = BB8P_NUM.exec(s))) {
    var pre = s.charAt(m.index - 1), post = s.charAt(m.index + m[0].length);
    var lead = m[1] ? 0 : (m[0].length - m[0].replace(/^\s+/, "").length);
    var p0 = s.charAt(m.index + lead - 1);
    if (!m[1] && /[A-Za-z0-9.^=_\/-]/.test(p0) && !/[-]/.test(p0)) continue;   // part of a symbol (0700.HK, GC=F, X1)
    if (/[A-Za-z]/.test(post) && !m[4] && /^(?:st|nd|rd|th|[A-Za-z])(?![A-Za-z])/.test(s.slice(m.index + m[0].length))) continue;   // 3rd, 10y, 5Y
    var int = m[2].replace(/,/g, ""), dec = m[3] || "";
    var v = Number(int + dec);
    if (!isFinite(v)) continue;
    var cls = bb8pCls(m[1], m[4]);
    var year = !m[1] && !dec && !m[4] && /^(?:19|20)\d{2}$/.test(int);
    out.push({ v: v, d: dec ? dec.length - 1 : 0, z: dec ? 0 : (int.match(/0+$/) || [""])[0].length, n: int.replace(/^0+/, "").length, cls: cls, mult: bb8pMult(m[4]), raw: m[0].trim(), year: year });
    void pre;
  }
  return { nums: out, dates: dates };
}
// Everything the model was given: final system prompt + user turns (never earlier assistant answers) + the server
// facts and sources of this request.
function bb8pHayOf(st) {
  if (!st) return null;
  if (st.bb8pHay && st.bb8pHay.ver === st.bb8pHayVer) return st.bb8pHay;
  var txt = [String(st.bb8pSys || "")];
  (Array.isArray(st.bb8pMsgs) ? st.bb8pMsgs : []).forEach(function (m) { if (m && m.role !== "assistant") txt.push(String(m.content || "")); });
  try { if (st.body && st.body.messages) st.body.messages.forEach(function (m) { if (m && m.role === "user") txt.push(String(m.content || "")); }); } catch (e) {}
  try { (typeof bb8eFull === "function" ? bb8eFull(st) : []).forEach(function (s) { txt.push(String((s && s.detail) || "")); }); } catch (e) {}
  try { if (st.bb8eMove && st.bb8eMove.text) txt.push(st.bb8eMove.text); } catch (e) {}
  try { if (st.bb3Built && st.bb3Built.block) txt.push(st.bb3Built.block); } catch (e) {}
  // Move pack / quote facts (the card lead's quotes, benchmark and sector; bb8o fallback quotes included): their
  // prices, previous closes and changes are context values for the guard.
  try {
    var pk = st.bb8eMoveR;
    if (pk && pk.q) [pk.q, pk.bench && pk.bench.q, pk.sector && pk.sector.q].forEach(function (q) {
      if (!q) return;
      ["p", "prev", "c", "change", "open", "high", "low", "dayHigh", "dayLow"].forEach(function (k) { var n = Number(q[k]); if (isFinite(n) && n !== 0) { txt.push(String(n)); txt.push(String(Math.abs(n))); txt.push(Math.abs(n).toFixed(2)); } });
    });
  } catch (e) {}
  try { if (Array.isArray(st.bb8pRel)) st.bb8pRel.forEach(function (r) { if (r && r.q) txt.push(String(r.q.p), String(Math.abs(Number(r.q.c)).toFixed(2))); }); } catch (e) {}
  try { if (Array.isArray(st.facts)) st.facts.forEach(function (f) { txt.push(f && f.sentence ? String(f.sentence) : ""); txt.push(JSON.stringify(f || {})); }); } catch (e) {}
  var all = txt.join("\n"), parsed = bb8pNums(all), years = {}, days = {};
  parsed.dates.forEach(function (d) { days[d.k] = 1; if (d.y) years[d.y] = 1; });
  (all.match(/\b(?:19|20)\d{2}\b/g) || []).forEach(function (y) { years[y] = 1; });
  st.bb8pHay = { ver: st.bb8pHayVer, nums: parsed.nums, years: years, days: days, n: all.length };
  return st.bb8pHay;
}
function bb8pTol(f) {
  if (f.d > 0) return 0.5 * Math.pow(10, -f.d) + 1e-9;
  var z = Math.max(0, Math.min(f.z, f.n - 2));
  return 0.5 * Math.pow(10, z) + 1e-9;
}
function bb8pMatch(f, hay) {
  if (f.year) return !!hay.years[String(f.v)];
  var tol = bb8pTol(f), cands = [f.v];
  if (f.mult !== 1) cands.push(f.v * f.mult);
  if (f.cls === "bp") cands.push(f.v / 100);
  for (var i = 0; i < hay.nums.length; i++) {
    var h = hay.nums[i];
    if (f.cls !== "plain" && h.cls !== "plain" && h.cls !== f.cls && !(f.cls === "bp" && h.cls === "pct") && !(f.cls === "pct" && h.cls === "bp")) continue;
    var hv = [h.v];
    if (h.mult !== 1) hv.push(h.v * h.mult);
    if (h.cls === "bp") hv.push(h.v / 100);
    for (var a = 0; a < cands.length; a++) for (var b = 0; b < hv.length; b++) {
      var t = cands[a] === f.v ? tol : tol * (cands[a] / f.v || 1);
      // Rounding is allowed within one class (and money <-> a bare price); across classes (a % against a bare
      // number such as a beta) only an exact value counts.
      var same = f.cls === h.cls || (f.cls === "money" && h.cls === "plain") || (f.cls === "plain" && h.cls === "money") || (f.cls === "plain" && h.cls === "plain") || (f.cls === "bp" && h.cls === "pct") || (f.cls === "pct" && h.cls === "bp");
      if (!same) {
        if (!(h.d > 0 || h.v >= 10)) continue;              // a bare small count never supports a %, bp or x figure
        if (f.d < (h.d || 0)) continue;                     // no rounding across classes (2% is not beta 2.23)
      }
      if (Math.abs(cands[a] - hv[b]) <= t) return true;
    }
  }
  return false;
}
// Unsupported figures in one sentence ([] when every figure is in the prompt). Small bare counts (< 10) are words.
function bb8pFigs(sent, st) {
  var hay = bb8pHayOf(st);
  if (!hay || !hay.n) return [];
  var p = bb8pNums(sent), bad = [];
  p.nums.forEach(function (f) {
    if (f.cls === "plain" && !f.year && f.d === 0 && f.v < 10) return;
    if (!bb8pMatch(f, hay)) bad.push(f.raw);
  });
  p.dates.forEach(function (d) { if (!hay.days[d.k]) bad.push(d.k); });
  return bad;
}
var BB8P_ANAPH = /^(?:\*\*)?\s*(?:This|These|That|Those|Such|It|The (?:rise|fall|uptick|increase|decrease|decline|drop|gain|growth|figure|reading|print|data|improvement|slowdown|acceleration|beat|miss|move|rebound|expansion|contraction))\b/;
var BB8P_CAUSE = /\b(?:attributed to|driven (?:largely |mainly |primarily |partly )?by|fuel(?:l)?ed by|thanks to|on the back of|boosted by|weighed (?:down )?(?:on )?by|due to|because of|as a result of|underpinned by|spurred by|a rebound in|a boost in|a pickup in)\b/i;
// bb8p keep test for one model sentence (st = request store); records drops for the honest fallback.
function bb8pKeep(sent, resolve, st) {
  var s = String(sent || "");
  if (!st || !st.chat || !s.trim() || !st.bb8pSys) return true;
  var bad = bb8pFigs(s, st), why = "";
  if (bad.length) why = "unsupported figure " + bad.slice(0, 3).join(", ");
  else if (st.bb8pPrevDrop && BB8P_ANAPH.test(s)) why = "refers to a dropped sentence";
  else if (BB8P_CAUSE.test(s)) {
    var ok = false;
    try {
      var ns = typeof bb8iCiteNums === "function" ? bb8iCiteNums(s) : [];
      for (var i = 0; i < ns.length && !ok; i++) { var src = resolve ? resolve(ns[i]) : null; ok = !!(src && bb8iIsNews(src, st) && bb8iNewsMatch(s, src)); }
    } catch (e) { ok = false; }
    if (!ok) why = "cause not named by a cited headline";
  }
  st.bb8pPrevDrop = !!why;
  if (why) {
    st.bb8pDrops = st.bb8pDrops || [];
    var key = s.trim().slice(0, 120);
    if (!st.bb8pDrops.some(function (d) { return d.s === key; })) st.bb8pDrops.push({ s: key, why: why });
  }
  return !why;
}
// ── Honest fallback (nothing substantive left) ──
function bb8pTopicLabel(topic) {
  if (!topic) return "the figures this question asks about";
  var e = topic.entities.map(function (t) { return t.label; }), s = topic.series.map(function (t) { return t.label; });
  if (topic.mode === "ticker" && topic.ticker) return topic.ticker + " figures for this question";
  if (e.length && s.length) return e[0] + " " + s[0] + " figures";
  if (s.length) return s[0] + " figures";
  if (e.length) return "the " + e[0] + " figures this question asks about";
  return "the figures this question asks about";
}
function bb8pRelSyms(topic) {
  var out = [], seen = {};
  (topic && topic.entities ? topic.entities : []).forEach(function (t) { (t.rel || []).forEach(function (r) { if (!seen[r[0]] && out.length < 3) { seen[r[0]] = 1; out.push(r); } }); });
  return out;
}
function bb8pRelFetch(st) {
  if (!st || st.bb8pRelP || typeof bb3Pack !== "function" || typeof bb3OneQuote !== "function") return st && st.bb8pRelP;
  var syms = bb8pRelSyms(st.bb8pTopic);
  if (!syms.length) return null;
  st.bb8pRelP = (async function () {
    var pack = await bb3Pack(Date.now());
    var rows = await Promise.all(syms.map(function (r) { return bb3OneQuote(pack, r[0]).catch(function () { return null; }); }));
    var out = [];
    rows.forEach(function (q, i) { if (q && Number(q.p) > 0 && isFinite(Number(q.c)) && q.basis !== "none") out.push({ sym: syms[i][0], label: syms[i][1], dp: syms[i][2], q: q }); });
    st.bb8pRel = out;
    return out;
  })().catch(function () { st.bb8pRel = []; return []; });
  return st.bb8pRelP;
}
async function bb8pRelWait(st) {
  if (!st || !st.bb8pRelP) return;
  try { await Promise.race([st.bb8pRelP, typeof bb8Late === "function" ? bb8Late(BB8P_REL_MS) : st.bb8pRelP]); } catch (e) {}
}
function bb8pFmt(q, dp) {
  var n = Number(q.p), s = n.toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });
  return q.currency === "USD" && !/=X$/.test(String(q.sym || "")) ? "$" + s : s;
}
function bb8pRelLine(rel, n) {
  if (!rel || !rel.length) return "";
  var bits = rel.map(function (r) {
    var c = Number(r.q.c), closed = String(r.q.status || "") === "closed";
    var verb = Math.abs(c) < 0.005 ? (closed ? "was unchanged" : "is unchanged") : (closed ? (c < 0 ? "fell " : "rose ") : (c < 0 ? "is down " : "is up ")) + Math.abs(c).toFixed(2) + "%";
    var px = /\^TNX/.test(r.sym) ? Number(r.q.p).toFixed(2) + "%" : bb8pFmt(Object.assign({ sym: r.sym }, r.q), r.dp);
    return r.label + " " + verb + (closed ? " in its last session, to " : " at ") + px;
  });
  var ms = Math.max.apply(null, rel.map(function (r) { return typeof bb8eMs === "function" ? bb8eMs(r.q) : 0; }));
  var uk = ms && typeof bb8dUk === "function" ? bb8dUk(ms) : "";
  var txt = bits.join("; ");
  return "What we do have, from Yahoo Finance" + (uk ? " as of " + uk : "") + ": " + txt.charAt(0).toUpperCase() + txt.slice(1) + ". [" + n + "]";
}
// A short answer that still quotes a supported figure is a real answer, not a no-data one.
function bb8pHasFigure(reply) {
  var t = String(reply || ""), at = t.search(/\n+Sources:/);
  var b = (at >= 0 ? t.slice(0, at) : t).replace(/(?:^|\n)In short:[^\n]*/g, "");
  return bb8pNums(b).nums.some(function (f) { return !f.year && (f.cls !== "plain" || f.d > 0 || f.v >= 10); });
}
function bb8pBodyWords(reply) {
  var t = String(reply || ""), at = t.search(/\n+Sources:/);
  var b = (at >= 0 ? t.slice(0, at) : t).replace(/(?:^|\n)In short:[^\n]*/g, "");
  return typeof bb8mWords === "function" ? bb8mWords(b) : b.split(/\s+/).filter(Boolean).length;
}
function bb8pFallback(out, st) {
  var topic = st.bb8pTopic || null, label = bb8pTopicLabel(topic);
  var t = String(out.reply || ""), at = t.search(/\n+Sources:/);
  var kept = (at >= 0 ? t.slice(0, at) : t).replace(/(?:^|\n)In short:[^\n]*/g, "").trim();
  var all = Array.isArray(out.sources) ? out.sources : [], sources = [];
  // Kept model text keeps only the sources it cites, renumbered 1..n.
  if (kept) {
    kept = kept.replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) {
      var got = [];
      g.split(/\s*,\s*/).forEach(function (x) { var src = all[Number(x) - 1]; if (!src) return; var k = sources.indexOf(src); if (k < 0) { sources.push(src); k = sources.length - 1; } if (got.indexOf(k + 1) < 0) got.push(k + 1); });
      return got.length ? "[" + got.join(", ") + "]" : "";
    }).replace(/[ \t]+([.!?,;:])/g, "$1").trim();
  }
  var lines = ["We don't have " + label + " in our data feed right now, so this answer does not quote any."];
  if (kept) lines.push(kept);
  var news = (Array.isArray(st.clientSources) ? st.clientSources : []).filter(function (s) { return s && !bb8pIsServerSrc(s) && sources.indexOf(s) < 0 && (typeof bb8iIsNews !== "function" || bb8iIsNews(s, st)); }).slice(0, 2);
  news.forEach(function (s) {
    sources.push(s);
    var when = "";
    try { var ms = Date.parse(s.asOf || ""); when = isFinite(ms) && typeof bb8dUk === "function" ? ", " + bb8dUk(ms) : ""; } catch (e) {}
    lines.push("In the news (" + s.name + when + "): \"" + String(s.detail || s.title || "").replace(/"/g, "'") + "\" [" + sources.length + "]");
  });
  var rel = Array.isArray(st.bb8pRel) ? st.bb8pRel : [];
  if (rel.length) {
    var iso = ""; try { iso = new Date(Math.max.apply(null, rel.map(function (r) { return bb8eMs(r.q) || 0; })) || Date.now()).toISOString(); } catch (e) {}
    sources.push({ name: "Yahoo Finance quote", link: "https://finance.yahoo.com/quote/" + encodeURIComponent(rel[0].sym) + "/", asOf: iso, detail: rel.map(function (r) { return r.sym; }).join(", ") + " last price and session change" });
    lines.push(bb8pRelLine(rel, sources.length));
  } else if (!news.length) lines.push("Our feed has no related live market data or news for this question either.");
  var shortTxt = "In short: no " + label.replace(/^the /, "") + " in our feed" + (rel.length ? "; related live markets are above." : news.length ? "; the related headline is above." : ".");
  var footer = typeof bb2Footer === "function" ? bb2Footer(sources) : "";
  st.bb8jSources = sources.slice();
  st.bb8pNoData = true;
  return { reply: lines.join("\n\n") + "\n\n" + shortTxt + footer, sources: sources };
}
// ── (6) Timeframe ──
var BB8P_TF = /\b(?:this week|next week|this month|next month|today|tonight|tomorrow|this year|this quarter|this session|week ahead|coming week|this weekend)\b/i;
function bb8pTimeframe(q) { var m = String(q || "").match(BB8P_TF); return m ? m[0].toLowerCase() : ""; }
function bb8pKeepTf(orig, r, max) {
  try {
    if (!r || !r.cut || typeof bb8mUnits !== "function") return r;
    var st = bb8pSt(), tf = st && st.body ? bb8pTimeframe(bb8pQuestion(st.body)) : "";
    if (!tf) return r;
    var tfRe = new RegExp("\\b" + tf.replace(/\s+/g, "\\s+") + "\\b|\\b(?:week|weekly|today|month)\\b", "i");
    var split = function (text) {
      var s = String(text || ""), at = s.search(/\n+Sources:\n/);
      var body = at >= 0 ? s.slice(0, at) : s, tail = at >= 0 ? s.slice(at) : "";
      var sm = body.match(/(?:^|\n)(In short:[^\n]*)/), inShort = sm ? sm[1] : "";
      var rest = (sm ? body.slice(0, sm.index) + body.slice(sm.index + sm[0].length) : body).replace(/\s+$/, "");
      var ends = bb8mUnits(rest), units = [];
      for (var i = 0; i < ends.length; i++) { var u = rest.slice(i ? ends[i - 1] : 0, ends[i]).trim(); if (u) units.push(u); }
      return { units: units, inShort: inShort, tail: tail };
    };
    var a = split(r.text);
    if (a.units.some(function (u) { return tfRe.test(u); })) return r;
    var o = split(orig), pick = o.units.filter(function (u) { return tfRe.test(u) && !/:\s*$/.test(u); })[0];
    if (!pick) return r;
    var w = function (x) { return bb8mWords(x); };
    var units = a.units.slice();
    while (units.length > 1 && w(units.join(" ") + " " + pick) + w(a.inShort) > max) units.pop();
    units.push(pick);
    var body = units.join(" ");
    return { text: body + (a.inShort ? "\n\n" + a.inShort : "") + a.tail, cut: true, words: w(body) + w(a.inShort), bb8pTf: tf };
  } catch (e) { return r; }
}
// ── (5) The quote the answer used ──
function bb8pIso(ms) { try { return ms ? new Date(ms).toISOString() : null; } catch (e) { return null; } }
function bb8pQuoteMeta(st) {
  if (!st) return null;
  try {
    var pack = st.bb8eMoveR;
    if (pack && pack.q && st.bb8eMove) {
      var ms = pack.ms || (typeof bb8eMs === "function" ? bb8eMs(pack.q) : 0);
      return { symbol: pack.base, feedSymbol: pack.ysym, name: pack.q.name || null, price: Number(pack.q.p), change: isFinite(Number(pack.q.c)) ? Number(Number(pack.q.c).toFixed(4)) : null, prevClose: isFinite(Number(pack.q.prev)) ? Number(pack.q.prev) : null, currency: pack.q.currency || null, asOf: bb8pIso(ms), asOfUk: typeof bb8dUk === "function" && ms ? bb8dUk(ms) : null, source: "Yahoo Finance", feed: "server yahooQuote (Yahoo v7/v8 quote) via bb3Quotes, card/move lead", session: pack.q.session || pack.q.status || null, fallback: pack.q.fallback === true ? true : undefined, fallbackReason: pack.q.fallbackReason || undefined, delayMin: isFinite(Number(pack.q.delayMin)) ? Number(pack.q.delayMin) : null };
    }
    var g = st.bb8pGold;
    if (g && isFinite(Number(g.goldLast))) {
      var gms = Number(g.goldTs) * 1000;
      return { symbol: "XAU", feedSymbol: "GC=F", name: "Gold futures (COMEX, front month)", price: Number(g.goldLast), dayHigh: isFinite(Number(g.dayHigh)) ? Number(g.dayHigh) : null, dayLow: isFinite(Number(g.dayLow)) ? Number(g.dayLow) : null, currency: "USD", asOf: bb8pIso(gms), asOfUk: typeof bb8dUk === "function" && gms ? bb8dUk(gms) : null, source: "Yahoo Finance", feed: "server buildChatLiveMarketBlock (Yahoo v8 chart GC=F 3mo/1d)", session: g.sessionDate ? "in-progress " + g.sessionDate : "last completed session" };
    }
    var ctx = st.body && typeof st.body.context === "string" ? st.body.context : "";
    var topic = st.bb8pTopic;
    if (topic && topic.entities.some(function (t) { return t.id === "gold"; })) {
      var m = ctx.match(/Gold \$([\d,]+(?:\.\d+)?)/), a = ctx.match(/prices as of ([^\u00b7\n]+)/);
      if (m) return { symbol: "XAU", feedSymbol: "client tape P.XAU", name: "Gold (client live tape)", price: Number(m[1].replace(/,/g, "")), currency: "USD", asOf: null, asOfUk: a ? a[1].trim() : null, source: "client context", feed: "browser live tape (gold-api.com spot proxy, % change from GC=F)", session: null };
    }
  } catch (e) {}
  return null;
}
function bb8pMetaFix(meta, admin, st) {
  if (!meta || typeof meta !== "object") return meta;
  var m = Object.assign({}, meta);
  if (!admin) { delete m.provider; delete m.model; }
  if (st) {
    var q = bb8pQuoteMeta(st);
    if (q) m.quote = q;
    m.grounding = { dropped: (st.bb8pDrops || []).length, noData: !!st.bb8pNoData, sourcesDropped: st.bb8pSrcDropped || 0 };
    if (admin && st.bb8pDrops && st.bb8pDrops.length) m.grounding.drops = st.bb8pDrops.slice(0, 8);
  }
  return m;
}
try {
  // (1) one grounding rule, first in the final system prompt of both paths; the prompt is recorded for the guard.
  var bb8pRecord = function (system, messages) {
    var st = bb8pSt();
    if (!st) return system;
    var s = String(system || "");
    if (s.indexOf("GROUNDING (both answer paths") < 0) s = BB8P_GROUND + "\n\n" + s;
    st.bb8pSys = s; st.bb8pMsgs = Array.isArray(messages) ? messages.slice() : []; st.bb8pHayVer = (st.bb8pHayVer || 0) + 1;
    return s;
  };
  if (typeof bb2OpenAi === "function") {
    var bb8pOai0 = bb2OpenAi;
    bb2OpenAi = function (cfg, system, messages, onDelta) { return bb8pOai0.call(this, cfg, bb8pRecord(system, messages), messages, onDelta); };
  }
  if (typeof bb2Gemini === "function") {
    var bb8pGem0 = bb2Gemini;
    bb2Gemini = function (cfg, system, messages, onDelta) { return bb8pGem0.call(this, cfg, bb8pRecord(system, messages), messages, onDelta); };
  }
  if (typeof bb3bGenerateAi === "function") {
    var bb8pB3g0 = bb3bGenerateAi;
    bb3bGenerateAi = function (options) {
      var args = Array.prototype.slice.call(arguments);
      try { if (bb8pSt() && options && typeof options.system === "string") args[0] = Object.assign({}, options, { system: bb8pRecord(options.system, options.messages) }); } catch (e) {}
      return bb8pB3g0.apply(this, args);
    };
  }
  // JSON chat prompts were clipped at 5000 characters (stream: 14000); one limit for chat on both paths.
  if (typeof clipped === "function") {
    var bb8pClip0 = clipped;
    clipped = function (value, max) {
      try { if (max === 5000 && typeof value === "string" && value.length > 5000 && value.indexOf("GROUNDING (both answer paths") === 0 && bb8pSt()) return bb8pClip0.call(this, value, BB8P_CLIP); } catch (e) {}
      return bb8pClip0.apply(this, arguments);
    };
  }
  // (2) the guard sits where bb8i drops speculative claims: painted general text, card/move/valuation lines and the
  // final compose on both paths all pass bb8iKeep.
  if (typeof bb8iKeep === "function") {
    var bb8pKeep0 = bb8iKeep;
    bb8iKeep = function (sent, resolve, st) {
      if (!bb8pKeep0.apply(this, arguments)) return false;
      try { return bb8pKeep(sent, resolve, st || bb8pSt()); } catch (e) { return true; }
    };
  }
  // bb8i leaves "In short:" lines alone; a model-written one (general answers) is checked for figures too.
  if (typeof bb8iLine === "function") {
    var bb8pLine0 = bb8iLine;
    bb8iLine = function (line, resolve, st) {
      try {
        var s0 = st || bb8pSt();
        if (s0 && s0.bb8pSys && /^\s*In short:/.test(String(line || "")) && typeof bb8iGeneral === "function" && bb8iGeneral(s0) && bb8pFigs(line, s0).length) {
          s0.bb8pDrops = s0.bb8pDrops || []; s0.bb8pDrops.push({ s: String(line).trim().slice(0, 120), why: "unsupported figure in In short" });
          return "";
        }
      } catch (e) {}
      return bb8pLine0.apply(this, arguments);
    };
  }
  // (3) topic-relevant client news only, both paths (bb8jSources feeds the stream and the JSON prompt alike).
  if (typeof bb8jSources === "function") {
    var bb8pSrc0 = bb8jSources;
    bb8jSources = function (body) {
      var list = bb8pSrc0.apply(this, arguments);
      try {
        var st = bb8pSt();
        if (st && body && !st.bb8pTopic) st.bb8pTopic = bb8pTopic(body);
        list = bb8pFilter(list, body);
        if (st && st.bb8pTopic && st.bb8pTopic.mode === "topic") bb8pRelFetch(st);
        if (st && st.bb8pTopic && st.bb8pTopic.entities.some(function (t) { return t.id === "gold"; }) && typeof buildChatLiveMarketBlock === "function" && !st.bb8pGoldP) {
          st.bb8pGoldP = buildChatLiveMarketBlock().then(function (blk) { st.bb8pGoldBlk = blk || ""; try { st.bb8pGold = Object.assign({}, lastChatLiveSnapshot); } catch (e) {} return blk; }).catch(function () { st.bb8pGoldBlk = ""; return ""; });
        }
      } catch (e) {}
      return list;
    };
  }
  if (typeof bb2ClientSources === "function") {
    var bb8pCs0 = bb2ClientSources;
    bb2ClientSources = function (body) { var l = bb8pCs0.apply(this, arguments); try { if (bb8pSt()) l = bb8pFilter(l, body); } catch (e) {} return l; };
  }
  // JSON path: the live gold block is built by the route itself; keep its snapshot for meta.quote.
  if (typeof buildChatLiveMarketBlock === "function") {
    var bb8pBlk0 = buildChatLiveMarketBlock;
    buildChatLiveMarketBlock = async function () {
      var r = await bb8pBlk0.apply(this, arguments);
      try { var st = bb8pSt(); if (st && st.bb8pTopic && st.bb8pTopic.entities.some(function (t) { return t.id === "gold"; })) st.bb8pGold = Object.assign({}, lastChatLiveSnapshot); } catch (e) {}
      return r;
    };
  }
  // Stream: a gold question gets the same LIVE MARKET DATA block the JSON route sends (bounded wait), and the
  // related-quotes fetch is awaited (bounded) after the model so the fallback can use it.
  if (typeof bb2Complete === "function") {
    var bb8pComplete0 = bb2Complete;
    bb2Complete = async function (system, messages, onDelta) {
      var st = bb8pSt(), sys = system;
      try {
        if (st && st.bb8pGoldP) {
          await Promise.race([st.bb8pGoldP, typeof bb8Late === "function" ? bb8Late(BB8P_GOLD_MS) : st.bb8pGoldP]);
          if (st.bb8pGoldBlk && String(sys).indexOf("LIVE MARKET DATA") < 0) sys = st.bb8pGoldBlk + "\n" + sys;
        }
      } catch (e) {}
      // Painting: a whole sentence with a figure that is not in the prompt is never painted (the done event's
      // guarded reply replaces the painted text anyway; this keeps it off the screen meanwhile).
      var cb = onDelta, pend = "";
      if (st && typeof onDelta === "function") {
        var flush = function (force) {
          if (!pend || typeof bb8mUnits !== "function") return;
          var ends = bb8mUnits(pend), upto = force ? pend.length : (ends.length > 1 ? ends[ends.length - 2] : 0);
          if (!upto) return;
          var out = "", from = 0;
          for (var i = 0; i < ends.length && ends[i] <= upto; i++) {
            var piece = pend.slice(from, ends[i]); from = ends[i];
            out += st.bb8pSys && /\d/.test(piece) && bb8pFigs(piece, st).length ? piece.replace(/[^\n]+/g, "") : piece;
          }
          if (force && from < pend.length) { var last = pend.slice(from); out += /\d/.test(last) && (!/[.!?:)\]"']\s*$/.test(last) || (st.bb8pSys && bb8pFigs(last, st).length)) ? "" : last; from = pend.length; }
          pend = pend.slice(from);
          if (out) onDelta(out);
        };
        cb = function (d) {
          if (typeof d !== "string") return onDelta.apply(this, arguments);
          try { pend += d; flush(false); } catch (e) { var p0 = pend; pend = ""; onDelta(p0); }
        };
      }
      var r = await bb8pComplete0.call(this, sys, messages, cb);
      try { flush && pend && flush(true); } catch (e) { if (pend) onDelta(pend); }
      try { if (st && st.bb8pDrops && st.bb8pDrops.length) await bb8pRelWait(st); } catch (e) {}
      return r;
    };
  }
  if (typeof generateAi === "function") {
    var bb8pGen0 = generateAi;
    generateAi = async function (options) {
      var r = await bb8pGen0.apply(this, arguments);
      try { var st = bb8pSt(); if (st && st.bb8pRelP) await bb8pRelWait(st); } catch (e) {}
      return r;
    };
  }
  // A new compose pass starts with no "previous sentence dropped" state.
  if (typeof bb3bCompose === "function") {
    var bb8pCompose0 = bb3bCompose;
    bb3bCompose = function () { try { var st = bb8pSt(); if (st) st.bb8pPrevDrop = false; } catch (e) {} return bb8pCompose0.apply(this, arguments); };
  }
  // (6) the brief trim keeps a sentence that answers the question's timeframe.
  if (typeof bb8mTrim === "function") {
    var bb8pTrim0 = bb8mTrim;
    bb8mTrim = function (reply, max) { return bb8pKeepTf(reply, bb8pTrim0.apply(this, arguments), max); };
  }
  // Honest fallback after every filter, the trim and the pruning (one assembler: stream done and JSON reply).
  if (typeof bb8jAssemble === "function") {
    var bb8pAssemble0 = bb8jAssemble;
    bb8jAssemble = function (reply, store) {
      var out = bb8pAssemble0.apply(this, arguments);
      try {
        var st = store || bb8pSt();
        // Last check on every mode: an "In short:" line (model-written or rebuilt from model text) with a figure
        // that is not in the prompt is removed.
        if (st && st.chat && st.bb8pSys && out && typeof out.reply === "string") {
          out.reply = out.reply.replace(/(^|\n)(In short:[^\n]*)(?=\n|$)/g, function (m, pre, line) {
            var bad = bb8pFigs(line, st);
            if (!bad.length) return m;
            st.bb8pDrops = st.bb8pDrops || []; st.bb8pDrops.push({ s: line.slice(0, 120), why: "unsupported figure " + bad.slice(0, 3).join(", ") + " in In short" });
            return pre;
          }).replace(/\n{3,}/g, "\n\n");
        }
        if (st && st.chat && out && typeof out.reply === "string" && st.bb8pDrops && st.bb8pDrops.length && !(st.facts && st.facts.length) && !st.bb8eMove && bb8pBodyWords(out.reply) < BB8P_MIN_WORDS && !bb8pHasFigure(out.reply)) {
          var fb = bb8pFallback(out, st);
          out.reply = fb.reply; out.sources = fb.sources;
        }
      } catch (e) {}
      return out;
    };
  }
  // (4) meta.provider / meta.model for admins only (isAdminUser, the /api/ai-status check), on every JSON body and
  // every SSE event of /api/chat; meta.quote and meta.grounding added. Unknown admin state = stripped.
  if (typeof handle === "function") {
    var bb8pHandle0 = handle;
    handle = async function (req, res) {
      try {
        var host = (req && req.headers && req.headers.host) || "localhost";
        var url = new URL((req && req.url) || "/", "http://" + host);
        if (req && req.method === "POST" && url.pathname === "/api/chat" && res && !res.__bb8p) {
          res.__bb8p = true;
          var admin = null;
          Promise.resolve().then(function () { return currentUser(req); }).then(function (u) { admin = !!(u && isAdminUser(u)); }).catch(function () { admin = false; });
          var fix = function (text) {
            var s = String(text);
            if (s.indexOf('"meta"') < 0) return null;
            var st = bb8pSt();
            if (s.charCodeAt(0) === 123) { var j = JSON.parse(s); if (j && j.meta) { j.meta = bb8pMetaFix(j.meta, admin === true, st); return JSON.stringify(j); } return null; }
            if (/^data: /.test(s)) {
              var changed = false;
              var outS = s.split("\n").map(function (ln) {
                if (!/^data: \{/.test(ln) || ln.indexOf('"meta"') < 0) return ln;
                try { var e = JSON.parse(ln.slice(6)); if (e && e.meta) { e.meta = bb8pMetaFix(e.meta, admin === true, e.done ? st : null); changed = true; return "data: " + JSON.stringify(e); } } catch (er) {}
                return ln;
              }).join("\n");
              return changed ? outS : null;
            }
            return null;
          };
          var w0 = res.write, e0 = res.end;
          res.write = function (chunk) {
            try { if (chunk && typeof chunk !== "function") { var t = Buffer.isBuffer(chunk) ? chunk.toString("utf8") : typeof chunk === "string" ? chunk : ""; var n = t ? fix(t) : null; if (n != null) { var a = Array.prototype.slice.call(arguments); a[0] = n; return w0.apply(this, a); } } } catch (e) {}
            return w0.apply(this, arguments);
          };
          res.end = function (chunk) {
            try {
              if (chunk && typeof chunk !== "function") {
                var t = Buffer.isBuffer(chunk) ? chunk.toString("utf8") : typeof chunk === "string" ? chunk : "";
                var n = t ? fix(t) : null;
                if (n != null) {
                  if (!res.headersSent && typeof res.setHeader === "function") { try { res.setHeader("Content-Length", Buffer.byteLength(n)); } catch (e1) {} }
                  var a = Array.prototype.slice.call(arguments); a[0] = n; return e0.apply(this, a);
                }
              }
            } catch (e) {}
            return e0.apply(this, arguments);
          };
        }
      } catch (e) {}
      return bb8pHandle0.apply(this, arguments);
    };
  }
} catch (e) { console.warn("bb8p hooks skipped", e && e.message); }
// BB8P_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8p")]
if bad:
    die("bb8p block declares a non-bb8p function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8p block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8p function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "setTimeout(" in BLOCK or "stripe" in BLOCK.lower() or ".tier" in BLOCK or "process.env" in BLOCK:
    die("bb8p block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8p replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8p setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8pbak"
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
print("APPLY bb8p grounding rule on both paths, numeric guard, topic-relevant sources, admin-only provider/model, meta.quote, timeframe kept")
