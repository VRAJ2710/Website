#!/usr/bin/env python3
"""patch_bb8m.py — Ask length setting enforced on the server, general-question scope guard, explicit JSON switch.
Server.js only. Stacked on bb8l (server md5 4b2fe7d9bdb6768a97eb5b864e442d1b). Does not rewrite app.js or index.html.
(1) Brief/Detailed: a LENGTH rule in the system prompt on both /api/chat paths; brief replies cut at a sentence
boundary to about 80 words (In short line and Sources list kept); detailed capped at 350 words, max_tokens raised
(stream 1400, JSON 1600); bb8eStrip also strips the reader-preference note (it was turning ticker questions into
P/E peer tables); alternative hint shapes are mapped onto { length, focus }.
(2) Clearly general questions (a country, macro series or asset; no page ticker or company named) keep the page
ticker as context only on both paths; card prompts and ticker questions are unchanged.
(3) POST /api/chat?stream=0 or X-Dispatch-Stream: 0 forces the JSON path. See docs/bb8m.md.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8m.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "4b2fe7d9bdb6768a97eb5b864e442d1b",
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
    print("bb8m %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8m before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8m %s untouched" % label)

if "// \u2500\u2500 bb8m \u2500\u2500" in v:
    print("REFUSE: bb8m already applied")
    sys.exit(0)

REPLACE = [
    ('stream: true, temperature: 0.2, max_tokens: 900, messages:',
     'stream: true, temperature: 0.2, max_tokens: (typeof bb8mTokens === "function" ? bb8mTokens(900) : 900), messages:'),
    ('generationConfig: { temperature: 0.2, maxOutputTokens: 900 }',
     'generationConfig: { temperature: 0.2, maxOutputTokens: (typeof bb8mTokens === "function" ? bb8mTokens(900) : 900) }'),
]
REQUIRED = [
    ("bb8l end", "// BB8L_JS_END"),
    ("bb8kHintNote", "function bb8kHintNote(hints) {"),
    ("bb8kApplyHints", "function bb8kApplyHints(body) {"),
    ("bb8eStrip", "function bb8eStrip(q) {"),
    ("bb8eIsCard", "function bb8eIsCard(q, body) {"),
    ("bb8eIntent", "function bb8eIntent(q, body) {"),
    ("bb8eBaseOf", "function bb8eBaseOf(q, body) {"),
    ("bb2Base", "function bb2Base(q) {"),
    ("rt41sBase", "function rt41sBase(q) {"),
    ("bb3bAskInfo", "function bb3bAskInfo(body) {"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
    ("bb2WantsStream", "function bb2WantsStream(req) {"),
    ("bb8dStore", "function bb8dStore() {"),
    ("handle", "async function handle(req, res) {"),
    ("RT17_ENUMS askLength", "askLength:"),
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
print("bb8m anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8m ── Ask length hint enforced on the server, general-question scope guard, explicit JSON switch.
// BB8M_JS
// (1) Length. The client already sends hints = { length: "brief"|"detailed", focus? } (app.js _rt37Hints), which is
// what bb8kHintNote reads. The setting had no effect because (a) the note was a weak bracketed line on the user turn,
// (b) nothing on the server enforced it, and (c) the note, appended after the client's "[Answer this question as
// asked, about X. ... PEER VALUATIONS ...]" note, stopped bb8eStrip from removing that note, so later intent checks
// read "VALUATIONS" and switched ticker questions to the P/E peer table. bb8m: bb8eStrip also strips reader-preference
// notes; a LENGTH rule goes into the system prompt on both paths; brief replies are cut at a sentence boundary to
// about 80 words (the "In short:" line and the Sources list are kept as they are); detailed replies are capped at
// 350 words the same way and get a larger max_tokens (stream 1400, JSON 1600).
// (2) Scope. A clearly general question (names a country, a macro series or an asset, and names neither the page
// ticker nor its company) keeps the page ticker as context only: no ticker base, no move/card lead, no peer or
// earnings facts, no page-ticker price source. Card prompts and questions that name the ticker are unchanged.
// bb2Base also ignores the client's "The reader has X open; that is background only" note on every question.
// (3) JSON switch. POST /api/chat?stream=0 (or header X-Dispatch-Stream: 0) is answered on the JSON path even when
// Accept: text/event-stream is sent. Without either, nothing changes.
var BB8M_BRIEF_MAX = 80, BB8M_DETAILED_MIN = 200, BB8M_DETAILED_MAX = 350;
var BB8M_RULE = {
  brief: "LENGTH (reader setting: brief; this overrides every other length or sentence-count instruction above): at most three short sentences, about 60 words, before the In short line. Keep the [n] citations. No headings, no lists, no background the question did not ask for.",
  detailed: "LENGTH (reader setting: detailed; this overrides every other length or sentence-count instruction above, including any 'two to four sentences'): the whole answer, counting any lines already shown, should run 200 to 350 words before the Sources list, in three to five short paragraphs: what the supplied data shows, the drivers the supplied sources name, and what to watch next. Cite [n] wherever a supplied source supports a sentence. Do not pad with definitions or generic statements, and do not invent figures to fill the length."
};
var BB8M_NOTE = {
  brief: "keep the answer brief: at most three short sentences (about 60 words) before the In short line",
  detailed: "give a detailed answer: 200 to 350 words in three to five short paragraphs"
};
// Reader-preference and background notes the client or bb8k add to the user turn (never part of the question).
var BB8M_NOTE_RE = /\s*\[Reader preferences:[^\]]*\]/g;
var BB8M_BG_RE = /\s*\[Answer this question as asked\.\s*(?:The reader has [^\]]*)?\]/g;
var BB8M_SYN = { brief: "brief", short: "brief", concise: "brief", detailed: "detailed", long: "detailed", full: "detailed" };
function bb8mEnum(v) {
  if (typeof v !== "string") return null;
  var k = v.trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(BB8M_SYN, k) ? BB8M_SYN[k] : null;
}
// Accepted shapes, first match wins: hints.length (client today), hints.askLength, hints.ask.length, hints as a
// string, body.askLength, body.answerLength, body.length. Values are enum-mapped; anything else is ignored.
function bb8mLenOf(body) {
  if (!body || typeof body !== "object") return null;
  var h = body.hints;
  var c = [];
  if (h && typeof h === "object") { c.push(h.length, h.askLength); if (h.ask && typeof h.ask === "object") c.push(h.ask.length); }
  if (typeof h === "string") c.push(h);
  c.push(body.askLength, body.answerLength, body.length);
  for (var i = 0; i < c.length; i++) { var e = bb8mEnum(c[i]); if (e) return e; }
  return null;
}
// Rewrites the body's hints to the one shape bb8kHintNote reads ({ length, focus }), keeping a valid focus.
function bb8mNormHints(body) {
  var len = bb8mLenOf(body);
  if (!body || typeof body !== "object") return len;
  var h = body.hints && typeof body.hints === "object" ? body.hints : {};
  var focus = typeof h.focus === "string" && typeof RT17_ENUMS !== "undefined" && RT17_ENUMS.askFocus.indexOf(h.focus) >= 0 ? h.focus : undefined;
  if (len || focus) { body.hints = { length: len || undefined, focus: focus }; if (!len) delete body.hints.length; if (!focus) delete body.hints.focus; }
  return len;
}
// Question text without client and reader notes.
function bb8mClean(q) {
  var s = String(q == null ? "" : q).replace(BB8M_NOTE_RE, "").replace(BB8M_BG_RE, "");
  s = s.replace(/\s*\[Answer this question as asked, about [^\]]*\]/g, "");
  return s.trim();
}
// The reader's open ticker and company name: context "Active ticker: MU Micron Technology · ...", else the note.
function bb8mPage(body, q) {
  var ctx = body && typeof body.context === "string" ? body.context : (body && body.context ? JSON.stringify(body.context) : "");
  var m = ctx.match(/Active ticker:\s*\$?([A-Z][A-Z0-9.\-]{0,9})\s+([^\u00b7\n|]{2,80})/);
  if (m) return { tk: m[1], name: m[2].trim() };
  var n = String(q || "").match(/The reader has ([A-Z][A-Z0-9.\-]{0,9}) open/);
  return n ? { tk: n[1], name: "" } : null;
}
var BB8M_MACRO_CS = /\b(?:US|U\.S\.|USA|UK|U\.K\.|EU|GDP|CPI|PPI|PCE|PMI|ISM|FOMC|Fed|ECB|BoE|BoJ|PBoC|SNB|RBA|RBI|OPEC|DXY|XAU|WTI|BTC|ETH|VIX|FTSE|DAX|CAC|Nikkei|Nasdaq|Dow|S&P(?:\s*500)?)(?![A-Za-z])/;
var BB8M_MACRO_CI = /\b(?:china|chinese|japan(?:ese)?|german[y]?|france|french|britain|british|united kingdom|united states|america[n]?|euro ?zone|euro area|europe(?:an)?|india[n]?|brazil(?:ian)?|canad(?:a|ian)|australia[n]?|russia[n]?|korea[n]?|mexic(?:o|an)|ital(?:y|ian)|spain|spanish|turk(?:ey|ish)|saudi|switzerland|swiss|taiwan(?:ese)?|hong kong|asia[n]?|emerging markets?|gdp|inflation|deflation|payrolls?|non-?farm|jobs report|unemployment|jobless|retail sales|industrial production|trade (?:balance|deficit|surplus)|interest rates?|rate (?:cuts?|hikes?|decision)|central banks?|federal reserve|bank of england|monetary policy|fiscal (?:policy|deficit|stimulus)|recession|yield curve|bond yields?|treasur(?:y|ies)|gilts?|tariffs?|housing (?:starts|market)|consumer (?:confidence|prices)|wages?|gold|bullion|silver|oil|crude|brent|natural gas|copper|bitcoin|ethereum|ether|crypto(?:currenc(?:y|ies))?|dollar|sterling|the pound|yen|yuan|renminbi|the euro|commodit(?:y|ies)|bonds?|forex|currenc(?:y|ies))\b/i;
// Decides scope for one question. general: names a country / macro series / asset, and neither the page ticker nor
// its company name nor any other stock ticker; card prompts are never general.
function bb8mScopeOf(q, body) {
  var clean = bb8mClean(q);
  var out = { general: false, page: null, reason: "" };
  try { if (typeof bb8eIsCard === "function" && bb8eIsCard(typeof bb8eStrip === "function" ? bb8eStrip(clean) : clean, body)) { out.reason = "card"; return out; } } catch (e) {}
  var page = bb8mPage(body, q);
  out.page = page;
  if (!(BB8M_MACRO_CS.test(clean) || BB8M_MACRO_CI.test(clean))) { out.reason = "no macro, country or asset named"; return out; }
  if (page) {
    var tkRe = new RegExp("(?:^|[^A-Za-z0-9])\\$?" + page.tk.replace(/[.\-]/g, "\\$&") + "(?![A-Za-z0-9])");
    if (tkRe.test(clean)) { out.reason = "names the page ticker"; return out; }
    var stem = String(page.name || "").replace(/[,.]?\s+(?:Inc|Corp(?:oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd|Platforms|Class [A-Z])\b.*$/i, "").trim();
    if (stem.length >= 3 && new RegExp("\\b" + stem.replace(/[^A-Za-z0-9 ]/g, "") + "\\b", "i").test(clean)) { out.reason = "names the page company"; return out; }
  }
  var known = {};
  try { (typeof BB2_PEERS !== "undefined" && BB2_PEERS ? Object.keys(BB2_PEERS) : []).forEach(function (k) { known[k] = 1; }); } catch (e) {}
  try { (Array.isArray(body && body.knownTickers) ? body.knownTickers : []).forEach(function (k) { known[String(k)] = 1; }); } catch (e) {}
  var toks = clean.match(/\$?\b[A-Z]{1,5}\b/g) || [];
  for (var i = 0; i < toks.length; i++) { var t = toks[i].replace("$", ""); if (known[t]) { out.reason = "names stock " + t; return out; } }
  out.general = true; out.reason = "general";
  return out;
}
function bb8mScopeSt(st) {
  if (!st || !st.chat) return null;
  if (st.bb8mScope) return st.bb8mScope;
  var body = st.bb8eBody || st.body;
  if (!body) return null;
  var q = typeof bb2Question === "function" ? bb2Question(body) : "";
  st.bb8mScope = bb8mScopeOf(q, body);
  return st.bb8mScope;
}
function bb8mGeneral() {
  try { var sc = bb8mScopeSt(bb8dStore()); return !!(sc && sc.general); } catch (e) { return false; }
}
function bb8mLenSt() {
  try { var st = bb8dStore(); return st && st.chat ? st.bb8mLen || null : null; } catch (e) { return null; }
}
function bb8mTokens(def) {
  var len = bb8mLenSt();
  return len === "detailed" ? Math.max(def, 1400) : def;
}
function bb8mWords(text) {
  return (String(text || "").match(/[A-Za-z0-9$\u00a3\u20ac%][^\s]*/g) || []).filter(function (w) { return !/^\[\d+(?:,\s*\d+)*\]$/.test(w); }).length;
}
// End offsets of the sentence units in a body: a sentence ends at . ! or ? (not a decimal point, not "U.S."-style
// abbreviations followed by lower case), plus closing quotes/brackets and any [n] cites; a line break ends a unit too.
function bb8mUnits(text) {
  var s = String(text || ""), ends = [], i = 0, n = s.length;
  while (i < n) {
    var ch = s[i];
    if (ch === "\n") { if (i > 0 && s[i - 1] !== "\n") ends.push(i); i++; continue; }
    if (ch === "." || ch === "!" || ch === "?") {
      if (ch === "." && /[0-9]/.test(s[i + 1] || "")) { i++; continue; }
      var j = i + 1;
      while (j < n && /[)"\u201d\u2019']/.test(s[j])) j++;
      var k = j;
      while (true) { var mm = s.slice(k).match(/^\s*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/); if (!mm) break; k += mm[0].length; }
      if (k >= n || /\s/.test(s[k])) {
        var nx = s.slice(k).match(/^\s*(\S)/);
        if (!nx || /[A-Z0-9"\u201c$\u00a3(\[]/.test(nx[1]) || /\n/.test(s.slice(k, k + 2))) { ends.push(k); i = k; continue; }
      }
      i = j; continue;
    }
    i++;
  }
  if (!ends.length || ends[ends.length - 1] < s.replace(/\s+$/, "").length) ends.push(s.replace(/\s+$/, "").length);
  return ends;
}
// Cuts a reply to max words at a sentence boundary. The "In short:" line and the Sources list stay as they are; a
// heading line left with nothing under it is dropped; at least one sentence of the body is kept.
function bb8mTrim(reply, max) {
  var text = String(reply || "");
  var at = text.search(/\n+Sources:\n/);
  var body = at >= 0 ? text.slice(0, at) : text, tail = at >= 0 ? text.slice(at) : "";
  var shortM = body.match(/(?:^|\n)(In short:[^\n]*)\s*$/) || body.match(/(?:^|\n)(In short:[^\n]*)/);
  var inShort = shortM ? shortM[1] : "";
  var rest = shortM ? (body.slice(0, shortM.index) + body.slice(shortM.index + shortM[0].length)) : body;
  rest = rest.replace(/\s+$/, "");
  if (bb8mWords(rest) + bb8mWords(inShort) <= max) return { text: text, cut: false, words: bb8mWords(rest) + bb8mWords(inShort) };
  var budget = max - bb8mWords(inShort), ends = bb8mUnits(rest), keep = 0, contentKept = 0;
  for (var i = 0; i < ends.length; i++) {
    var piece = rest.slice(0, ends[i]);
    var unit = rest.slice(i ? ends[i - 1] : 0, ends[i]).trim();
    var isHead = /:\s*$/.test(unit) && !/[.!?](?:\s*\[\d+\])*\s*$/.test(unit);
    if (bb8mWords(piece) > budget && contentKept > 0) break;
    keep = ends[i];
    if (!isHead && unit) contentKept++;
    if (bb8mWords(piece) > budget && contentKept > 0) break;
  }
  var cutBody = rest.slice(0, keep).replace(/\s+$/, "");
  var lines = cutBody.split("\n");
  while (lines.length > 1 && /:\s*$/.test(lines[lines.length - 1].trim()) && !/[.!?](?:\s*\[\d+\])*\s*$/.test(lines[lines.length - 1].trim())) lines.pop();
  cutBody = lines.join("\n").replace(/\s+$/, "");
  var out = cutBody + (inShort ? "\n\n" + inShort : "") + tail;
  return { text: out, cut: true, words: bb8mWords(cutBody) + bb8mWords(inShort) };
}
function bb8mApplyLen(reply) {
  var len = bb8mLenSt();
  if (len === "brief") {
    var r = String(reply || "");
    // Brief keeps the one-line live gold quote (rt39s "Live: ...") but not its multi-session "Windows: ..." detail line.
    if (bb8mWords(r.split(/\n+Sources:\n/)[0]) > BB8M_BRIEF_MAX) r = r.replace(/(^|\n)Windows: [^\n]*(?=\n)/, "");
    return bb8mTrim(r, BB8M_BRIEF_MAX).text;
  }
  if (len === "detailed") return bb8mTrim(reply, BB8M_DETAILED_MAX).text;
  return reply;
}
// The explicit JSON switch: ?stream=0|false|off|json, or X-Dispatch-Stream: 0|false|off|json.
function bb8mWantsJson(req, url) {
  var q = url && url.searchParams ? String(url.searchParams.get("stream") || "").toLowerCase() : "";
  var h = req && req.headers ? String(req.headers["x-dispatch-stream"] || "").toLowerCase() : "";
  return /^(?:0|false|off|json)$/.test(q) || /^(?:0|false|off|json)$/.test(h);
}
function bb8mPagePriceSource(src, page) {
  if (!src || !page || !page.tk) return false;
  return String(src.detail || "").trim().toUpperCase() === page.tk.toUpperCase() + " PRICE";
}
try {
  if (typeof bb8eStrip === "function") {
    var bb8mStrip0 = bb8eStrip;
    bb8eStrip = function (q) { return bb8mStrip0.call(this, String(q == null ? "" : q).replace(BB8M_NOTE_RE, "")); };
  }
  if (typeof bb8kHintNote === "function") {
    var bb8mNote0 = bb8kHintNote;
    bb8kHintNote = function (hints) {
      var note = bb8mNote0.apply(this, arguments);
      var len = hints && typeof hints === "object" ? bb8mEnum(hints.length) : null;
      if (!note || !len) return note;
      return note.replace(len === "brief" ? "keep the answer brief (3-5 sentences)" : "a detailed answer is welcome", BB8M_NOTE[len]);
    };
  }
  if (typeof bb8kApplyHints === "function") {
    var bb8mApply0 = bb8kApplyHints;
    bb8kApplyHints = function (body) {
      try {
        var len = bb8mNormHints(body);
        var st = bb8dStore();
        if (st && st.chat && len) st.bb8mLen = len;
      } catch (e) {}
      return bb8mApply0.apply(this, arguments);
    };
  }
  if (typeof bb2Base === "function") {
    var bb8mBase0 = bb2Base;
    bb2Base = function (q) {
      if (bb8mGeneral()) return null;
      return bb8mBase0.call(this, String(q == null ? "" : q).replace(BB8M_NOTE_RE, "").replace(BB8M_BG_RE, ""));
    };
  }
  if (typeof rt41sBase === "function") {
    var bb8mRt41Base0 = rt41sBase;
    rt41sBase = function (q) {
      if (bb8mGeneral()) return null;
      return bb8mRt41Base0.call(this, String(q == null ? "" : q).replace(BB8M_NOTE_RE, "").replace(BB8M_BG_RE, ""));
    };
  }
  if (typeof bb8eIntent === "function") {
    var bb8mIntent0 = bb8eIntent;
    bb8eIntent = function (q, body) {
      var it = bb8mIntent0.apply(this, arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && body && body === st.bb8eBody && !st.bb8mScope) st.bb8mScope = bb8mScopeOf(q, body);
        var sc = st && st.chat && body ? bb8mScopeOf(q, body) : null;
        if (sc && sc.general && !it.card) return { mode: "move", card: false, q: it.q, bb8mGeneral: true };
      } catch (e) {}
      return it;
    };
  }
  if (typeof bb8eBaseOf === "function") {
    var bb8mBaseOf0 = bb8eBaseOf;
    bb8eBaseOf = function (q, body) {
      try { if (body && bb8mScopeOf(q, body).general) return null; } catch (e) {}
      if (bb8mGeneral()) return null;
      return bb8mBaseOf0.apply(this, arguments);
    };
  }
  if (typeof bb3bAskInfo === "function") {
    var bb8mAsk0 = bb3bAskInfo;
    bb3bAskInfo = function (body) {
      var info = bb8mAsk0.apply(this, arguments);
      try {
        var sc = body ? bb8mScopeOf(typeof bb2Question === "function" ? bb2Question(body) : "", body) : null;
        if (info && sc && sc.general) {
          var pg = sc.page && sc.page.tk;
          return { q: info.q, peer: false, base: null, tickers: (info.tickers || []).filter(function (t) { return t !== pg; }) };
        }
      } catch (e) {}
      return info;
    };
  }
  if (typeof bb2ClientSources === "function") {
    var bb8mClient0 = bb2ClientSources;
    bb2ClientSources = function (body) {
      var list = bb8mClient0.apply(this, arguments);
      try {
        var sc = body ? bb8mScopeOf(typeof bb2Question === "function" ? bb2Question(body) : "", body) : null;
        if (sc && sc.general && Array.isArray(list)) list = list.filter(function (s) { return !bb8mPagePriceSource(s, sc.page); });
      } catch (e) {}
      return list;
    };
  }
  if (typeof bb8jAssemble === "function") {
    var bb8mAssemble0 = bb8jAssemble;
    bb8jAssemble = function () {
      var out = bb8mAssemble0.apply(this, arguments);
      try { if (out && typeof out.reply === "string") out.reply = bb8mApplyLen(out.reply); } catch (e) {}
      return out;
    };
  }
  if (typeof bb2System === "function") {
    var bb8mSystem0 = bb2System;
    bb2System = function () {
      var s = bb8mSystem0.apply(this, arguments), len = bb8mLenSt();
      return len && typeof s === "string" && s.indexOf("LENGTH (reader setting") < 0 ? s + "\n\n" + BB8M_RULE[len] : s;
    };
  }
  if (typeof bb2Complete === "function") {
    var bb8mComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var args = Array.prototype.slice.call(arguments), len = bb8mLenSt();
      try {
        if (len && typeof system === "string" && system.indexOf("LENGTH (reader setting") < 0) args[0] = system + "\n\n" + BB8M_RULE[len];
        if (len === "brief" && typeof onDelta === "function") {
          var painted = "";
          args[2] = function (t) {
            if (bb8mWords(painted) >= BB8M_BRIEF_MAX) return;
            painted += String(t || "");
            return onDelta.apply(this, arguments);
          };
        }
      } catch (e) {}
      return bb8mComplete0.apply(this, args);
    };
  }
  if (typeof generateAi === "function") {
    var bb8mGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore(), len = bb8mLenSt();
        if (st && st.chat && len && options && typeof options.system === "string") {
          var next = Object.assign({}, options);
          if (next.system.indexOf("LENGTH (reader setting") < 0) next.system = next.system + "\n\n" + BB8M_RULE[len];
          if (len === "detailed") next.maxTokens = Math.max(Number(next.maxTokens) || 0, 1600);
          args[0] = next;
        }
      } catch (e) {}
      return bb8mGen0.apply(this, args);
    };
  }
  if (typeof handle === "function") {
    var bb8mHandle0 = handle;
    handle = async function (req, res) {
      try {
        if (req && req.method === "POST" && req.headers) {
          var host = req.headers.host || "localhost";
          var url = new URL(req.url || "/", "http://" + host);
          if (url.pathname === "/api/chat" && bb8mWantsJson(req, url)) {
            req.headers.accept = "application/json";
            delete req.headers["x-dispatch-stream"];
            if (res && typeof res.setHeader === "function" && !res.headersSent) res.setHeader("X-Dispatch-Path", "json");
          }
        }
      } catch (e) {}
      return bb8mHandle0.apply(this, arguments);
    };
  }
} catch (e) { console.warn("bb8m hooks skipped", e && e.message); }
// BB8M_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8m")]
if bad:
    die("bb8m block declares a non-bb8m function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8m block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8m function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8m block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8m replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8m setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8mbak"
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
print("APPLY bb8m Ask length enforced (brief/detailed), general-question scope guard, ?stream=0 JSON switch")
