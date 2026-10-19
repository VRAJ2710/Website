#!/usr/bin/env python3
"""patch_bb8l.py — UK time (Europe/London, BST and GMT) in every user-visible text and model prompt. Server.js only.
Stacked on bb8l (server md5 0510fe845e43ec1e865dbc4257b00418). Does not rewrite app.js or index.html.
Converted: the JSON valuation peer block ("as of 2026-10-16 20:00 UTC"), the JSON gold reply prefix ("as of 08:49
UTC"), the Congressional snapshot note, every model prompt (generateAi and the stream's bb2Complete: system and
message text, including the client context and brief context), streamed and final Ask replies, and brief text
fields. Time-only "HH:MM UTC" stamps convert on the UTC date of the request. Machine JSON fields (asOf, ts,
generatedAt, firstPriceAt, sources[].asOf), HTTP headers, sitemap and JSON-LD dates stay ISO; date-only values
stay as they are. Stripe, auth and webhook code paths are not touched. See docs/bb8l.md for the inventory.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8l.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "0510fe845e43ec1e865dbc4257b00418",
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
    print("bb8l %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8l before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8l %s untouched" % label)

if "// \u2500\u2500 bb8l \u2500\u2500" in v:
    print("REFUSE: bb8l already applied")
    sys.exit(0)

REPLACE = [
    ('d.toISOString().slice(11, 16) + " UTC"',
     '(typeof bb8lGoldHm === "function" && bb8lGoldHm(d) ? bb8lGoldHm(d) : d.toISOString().slice(11, 16) + " UTC")'),
]
REQUIRED = [
    ("bb8k end", "// BB8K_JS_END"),
    ("bb8dUk", "function bb8dUk(ms) {"),
    ("bb8dUkText", "function bb8dUkText(text) {"),
    ("bb2BuildFacts", "function bb2BuildFacts(base, vals) {"),
    ("bb3bGenerateAi", "async function bb3bGenerateAi(options) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
    ("bb8jFix", "function bb8jFix(sent, st) {"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb8iLine", "function bb8iLine(line, resolve, st) {"),
    ("rt33sBriefDate", "function rt33sBriefDate(b) {"),
    ("institutionalResponse", "function institutionalResponse(type, status, source, asOf, items, note) {"),
    ("rt32Yahoo", "async function rt32Yahoo(sym) {"),
    ("bb8eMovePack", "async function bb8eMovePack(base) {"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb8eCites", "function bb8eCites(text, full) {"),
    ("bb8eStrip", "function bb8eStrip(q) {"),
    ("bb2Read0", "var bb2Read0 = typeof readBody"),
    ("bb2Question", "function bb2Question(body) {"),
    ("bb8hIndex", "function bb8hIndex(st, facts) {"),
    ("bb8hFixSentence", "function bb8hFixSentence(sent, idx) {"),
    ("bb8iKeep", "function bb8iKeep(sent, resolve, st) {"),
    ("BB8I_SPEC", "var BB8I_SPEC = ["),
    ("bb7FormList", "function bb7FormList(submission) {"),
    ("bb7Shape", "function bb7Shape(pack, opts) {"),
    ("bb8Older", "async function bb8Older(ticker, before, opts) {"),
    ("bb8hOlder", "async function bb8hOlder(ticker, before, opts) {"),
    ("bb8hKey", "function bb8hKey(ticker, mode) {"),
    ("bb8WindowLabel", "function bb8WindowLabel(from, to) {"),
    ("bb8Late", "function bb8Late(ms) {"),
    ("nextEarnings in rt32Build", "out.nextEarnings = out.earnings && out.earnings.next;"),
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
print("bb8l anchors ok x%d" % len(REQUIRED))

BLOCK = r"""

// ── bb8l ── UK time (Europe/London, BST/GMT) in every user-visible text and model prompt; machine fields unchanged.
// Also (chat73): a cited "Next earnings" fact line; insiders meta.span (whole loaded span) and UK display dates.
// BB8L_JS
// Sites converted (see docs/bb8l.md for the full inventory):
//   - JSON valuation peer block: bb2BuildFacts().block said "as of 2026-10-16 20:00 UTC" (bb2AsOf) -> bb8d UK.
//   - JSON gold reply prefix (rt39s-gold): "as of 08:49 UTC" -> "as of Mon 19 Oct, 09:49 UK" (in place).
//   - Congressional snapshot note: "...snapshot from <ISO>" -> UK.
//   - Every model prompt (generateAi -> bb3bGenerateAi, and the stream's bb2Complete): system text and message text.
//   - Ask replies: the streamed general-answer sentences and the final reply (both paths, via bb8jAssemble).
//   - Brief text fields (headline, houseView, summary, risks, ...).
// Machine fields (asOf, ts, generatedAt, firstPriceAt, sources[].asOf, headers, sitemap lastmod, JSON-LD dates) stay
// ISO. Date-only values (session dates, filing dates, brief.date) are dates, not timestamps, and stay as they are.
var BB8L_TIME_ONLY = /\b([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?\s?(?:UTC|GMT)\b|\b([01]\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?Z\b/g;
// "HH:MM" in Europe/London for a UTC time of day on the UTC date of refMs (time-only stamps carry no date).
function bb8lTimeOnly(h, m, refMs) {
  var d = new Date(Number(refMs) || Date.now());
  var ms = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), Number(h), Number(m));
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms)).forEach(function (p) { parts[p.type] = p.value; });
    return parts.hour + ":" + parts.minute + " UK";
  } catch (e) { return ""; }
}
// Full timestamps (ISO / "YYYY-MM-DD HH:MM UTC") via bb8d's formatter, then time-only "HH:MM UTC|GMT" / "HH:MMZ".
function bb8lUkText(text, refMs) {
  var s = String(text == null ? "" : text);
  if (typeof bb8dUkText === "function") s = bb8dUkText(s);
  return s.replace(BB8L_TIME_ONLY, function (all, h1, m1, h2, m2) { return bb8lTimeOnly(h1 != null ? h1 : h2, m1 != null ? m1 : m2, refMs) || all; });
}
function bb8lMsgs(messages) {
  if (!Array.isArray(messages)) return messages;
  return messages.map(function (m) { return m && typeof m.content === "string" ? Object.assign({}, m, { content: bb8lUkText(m.content) }) : m; });
}
function bb8lOptions(options) {
  if (!options || typeof options !== "object") return options;
  var next = Object.assign({}, options);
  if (typeof next.system === "string") next.system = bb8lUkText(next.system);
  if (Array.isArray(next.messages)) next.messages = bb8lMsgs(next.messages);
  return next;
}
// Brief: text fields only; date (YYYY-MM-DD, London) and generatedAt (ISO) are machine fields.
function bb8lBrief(b) {
  if (!b || typeof b !== "object") return b;
  Object.keys(b).forEach(function (k) {
    if (k === "date" || /At$/.test(k) || k === "generatedAtUk") return;
    if (typeof b[k] === "string") b[k] = bb8lUkText(b[k]);
    else if (Array.isArray(b[k])) b[k] = b[k].map(function (x) { return typeof x === "string" ? bb8lUkText(x) : x; });
  });
  return b;
}
// The rt39s-gold reply prefix: UTC "HH:MM" of the gold print -> bb8d UK stamp.
function bb8lGoldHm(d) {
  var ms = d && typeof d.getTime === "function" ? d.getTime() : NaN;
  return isFinite(ms) && typeof bb8dUk === "function" ? bb8dUk(ms) : "";
}
try {
  if (typeof bb2BuildFacts === "function") {
    // Item 1: the peer block reaches the JSON prompt unconverted; built.asOf stays the machine value.
    var bb8lFacts0 = bb2BuildFacts;
    bb2BuildFacts = function () {
      var built = bb8lFacts0.apply(this, arguments);
      try { if (built && typeof built.block === "string") built.block = bb8lUkText(built.block); } catch (e) {}
      return built;
    };
  }
  if (typeof bb3bGenerateAi === "function") {
    // Every generateAi call (Ask JSON, brief, lenses, intelligence, committee, news scores) reaches the provider here.
    var bb8lGen0 = bb3bGenerateAi;
    bb3bGenerateAi = function (options) {
      var args = Array.prototype.slice.call(arguments);
      try { args[0] = bb8lOptions(options); } catch (e) {}
      return bb8lGen0.apply(this, args);
    };
  }
  if (typeof bb2Complete === "function") {
    // Stream path prompt.
    var bb8lComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var args = Array.prototype.slice.call(arguments);
      try { args[0] = typeof system === "string" ? bb8lUkText(system) : system; args[1] = bb8lMsgs(messages); } catch (e) {}
      return bb8lComplete0.apply(this, args);
    };
  }
  if (typeof bb8jFix === "function") {
    // Streamed general-answer sentences (bb8i painter) and the final general compose.
    var bb8lFix0 = bb8jFix;
    bb8jFix = function () { return bb8lUkText(bb8lFix0.apply(this, arguments)); };
  }
  if (typeof bb8iLine === "function") {
    var bb8lLine0 = bb8iLine;
    bb8iLine = function (line, resolve, st) {
      var out = bb8lLine0.apply(this, arguments);
      try { if (bb8iGeneral(st)) out = bb8lUkText(out); } catch (e) {}
      return out;
    };
  }
  if (typeof bb8jAssemble === "function") {
    var bb8lAssemble0 = bb8jAssemble;
    bb8jAssemble = function () {
      var out = bb8lAssemble0.apply(this, arguments);
      try { if (out && typeof out.reply === "string") out.reply = bb8lUkText(out.reply); } catch (e) {}
      return out;
    };
  }
  if (typeof rt33sBriefDate === "function") {
    var bb8lBrief0 = rt33sBriefDate;
    rt33sBriefDate = function () { return bb8lBrief(bb8lBrief0.apply(this, arguments)); };
  }
  if (typeof institutionalResponse === "function") {
    // Notes shown on the disclosures panel ("...snapshot from <ISO>"); asOf stays ISO.
    var bb8lInst0 = institutionalResponse;
    institutionalResponse = function (type, status, source, asOf, items, note) {
      var args = Array.prototype.slice.call(arguments);
      try { if (typeof note === "string") args[5] = bb8lUkText(note); } catch (e) {}
      return bb8lInst0.apply(this, args);
    };
  }
} catch (e) { console.warn("bb8l hooks skipped", e && e.message); }
// bb8l (chat73 1): "Next earnings" server fact line. Source: Yahoo Finance quoteSummary calendarEvents, the same
// field /api/financials returns as nextEarnings (its 12 h cache is used first). Card answers always; move and
// valuation answers when the question asks about earnings or results. No line when there is no date or it is past.
var BB8L_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var BB8L_WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var BB8L_EARN_MS = 2500; // per-request wait, through bb8's existing bb8Late timer (no new timer code)
var BB8L_ASKS = /\b(?:earnings|results|report(?:s|ed|ing)?|quarter(?:ly)?|eps|guidance)\b/i;
var BB8L_EARN_WORD = /\b(?:earnings|results|reports?|reporting|quarterly|quarter|Q[1-4])\b/i;
var BB8L_EARN_RULE = "If you mention the next earnings date, use only the Next earnings line, cite its [n], and say it is estimated when the line says so. Do not give an earnings estimate or a forecast.";
var bb8lEarnMem = new Map();
var bb8lNewestMem = new Map();
var bb8lYahooFlight = new Map();
var bb8lEarnSrcs = new WeakSet();
function bb8lYmd(s) {
  var t = String(s == null ? "" : s).trim();
  try { if (!/^\d{4}-\d{2}-\d{2}/.test(t) && typeof bb7IsoDate === "function") t = bb7IsoDate(t); } catch (e) {}
  var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(t);
  if (!m) return null;
  var y = Number(m[1]), mo = Number(m[2]), d = Number(m[3]);
  if (!(mo >= 1 && mo <= 12 && d >= 1 && d <= 31)) return null;
  return { y: y, m: mo, d: d, iso: m[1] + "-" + m[2] + "-" + m[3] };
}
// "15 Oct 2025" (calendar date, no time zone involved); "" when the value is not a date.
function bb8lDay(s, weekday) {
  var p = bb8lYmd(s);
  if (!p) return "";
  var wd = BB8L_WD[new Date(Date.UTC(p.y, p.m - 1, p.d)).getUTCDay()];
  return (weekday ? wd + " " : "") + p.d + " " + BB8L_MON[p.m - 1] + " " + p.y;
}
function bb8lToday(now) {
  try { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(now == null ? Date.now() : now)); }
  catch (e) { return new Date(now == null ? Date.now() : now).toISOString().slice(0, 10); }
}
// next = /api/financials nextEarnings ({ date, isEstimate }); null when no date or the date is before today (UK).
function bb8lEarnFrom(next, asOf, sym, now) {
  var p = next && bb8lYmd(next.date);
  if (!p || p.iso < bb8lToday(now)) return null;
  return { sym: sym, date: p.iso, isEstimate: !!next.isEstimate, asOf: asOf || new Date(now == null ? Date.now() : now).toISOString() };
}
function bb8lEarnLine(e) { return "Next earnings: " + bb8lDay(e.date, true) + (e.isEstimate ? " (estimated)" : ""); }
function bb8lEarnSrc(e, ysym, base) {
  var src = { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/" + encodeURIComponent(ysym || base) + "/", asOf: e.asOf, detail: base + " next earnings date (Yahoo Finance calendarEvents" + (e.isEstimate ? ", estimated" : "") + ")" };
  bb8lEarnSrcs.add(src);
  return src;
}
// Shared while pending and for 30 s after a success, so the card's beta and earnings lookups make one request.
function bb8lYahooShared(sym) {
  var now = Date.now(), hit = bb8lYahooFlight.get(sym);
  if (hit && (hit.pending || now - hit.at < 30000)) return hit.job;
  var row = { at: now, pending: true, job: null };
  row.job = Promise.resolve().then(function () { return bb8lYahoo0(sym); });
  bb8lYahooFlight.set(sym, row);
  while (bb8lYahooFlight.size > 100) bb8lYahooFlight.delete(bb8lYahooFlight.keys().next().value);
  row.job.then(function () { row.pending = false; row.at = Date.now(); }, function () { if (bb8lYahooFlight.get(sym) === row) bb8lYahooFlight.delete(sym); });
  return row.job;
}
async function bb8lEarnGet(base, now) {
  var key = String(base || "").toUpperCase();
  if (!key) return null;
  var t = now == null ? Date.now() : now;
  try {
    var hit = typeof RT32 === "object" && RT32 && RT32.cache ? RT32.cache.get(key) : null;
    if (hit && hit.data && t - hit.at < 12 * 3600e3 && hit.data.earnings && /yahoo/i.test(String(hit.data.earnings.source || ""))) {
      return bb8lEarnFrom(hit.data.nextEarnings || hit.data.earnings.next, hit.data.earnings.asOf, key, t);
    }
  } catch (e) {}
  var mem = bb8lEarnMem.get(key);
  if (mem && t - mem.at < 3600e3) return mem.v ? bb8lEarnFrom(mem.v, mem.asOf, key, t) : null;
  if (typeof rt32Yahoo !== "function") return null;
  try {
    var ysym = typeof bb8bYahooSym === "function" ? bb8bYahooSym(key) : key;
    var y = await Promise.race([rt32Yahoo(ysym), bb8Late(BB8L_EARN_MS)]);
    if (y === "bb8-late" || !y) return null;
    var ce = (y.calendarEvents || {}).earnings || {};
    var nd = (ce.earningsDate || [])[0];
    var next = nd ? { date: nd.fmt || (nd.raw ? new Date(nd.raw * 1000).toISOString().slice(0, 10) : ""), isEstimate: !!ce.isEarningsDateEstimate } : null;
    var asOf = new Date(t).toISOString();
    bb8lEarnMem.set(key, { at: t, v: next, asOf: asOf });
    if (bb8lEarnMem.size > 200) bb8lEarnMem.delete(bb8lEarnMem.keys().next().value);
    return next ? bb8lEarnFrom(next, asOf, key, t) : null;
  } catch (e) { return null; }
}
function bb8lQuestion(st) {
  try {
    var q = st && st.bb8eBody && typeof bb2Question === "function" ? bb2Question(st.bb8eBody) : "";
    return typeof bb8eStrip === "function" ? bb8eStrip(q) : String(q || "");
  } catch (e) { return ""; }
}
function bb8lAsks(q) { return BB8L_ASKS.test(String(q || "")); }
function bb8lEarnOf(st) {
  if (!st) return null;
  if (st.bb8eMove && st.bb8eMove.bb8lEarn) return st.bb8eMove.bb8lEarn;
  return st.bb8eMode === "valuation" && st.bb8lEarn ? st.bb8lEarn : null;
}
// Dates a sentence names: "23 Dec", "December 23", "Dec. 23rd", "2026-12-23" -> ["12-23", ...].
function bb8lDates(sent) {
  var s = String(sent || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " "), out = [];
  var mon = "(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\\.?";
  var pad = function (m, d) { return ("0" + m).slice(-2) + "-" + ("0" + d).slice(-2); };
  var idx = function (w) { return ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].indexOf(String(w).slice(0, 3).toLowerCase()) + 1; };
  s.replace(new RegExp("\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(?:of\\s+)?" + mon, "gi"), function (m, d, w) { out.push(pad(idx(w), d)); return m; });
  s.replace(new RegExp("\\b" + mon + "\\s+(\\d{1,2})(?:st|nd|rd|th)?\\b", "gi"), function (m, w, d) { out.push(pad(idx(w), d)); return m; });
  s.replace(/\b\d{4}-(\d{2})-(\d{2})\b/g, function (m, a, b) { out.push(a + "-" + b); return m; });
  return out;
}
function bb8lEarnSent(sent, e) {
  var s = String(sent || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ");
  if (!e || !BB8L_EARN_WORD.test(s)) return false;
  return bb8lDates(s).length > 0 || /\b(?:next|upcoming|scheduled|due|date)\b/i.test(s);
}
function bb8lDateOk(sent, e) {
  var d = bb8lDates(sent);
  return !d.length || d.indexOf(String(e.date).slice(5)) >= 0;
}
// Views attributed to analysts or investors, or "could / may" speculation, are still bb8i's call.
function bb8lAttributed(sent) {
  if (typeof BB8I_SPEC === "undefined" || !BB8I_SPEC) return false;
  var s = String(sent || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ");
  for (var i = 0; i < BB8I_SPEC.length; i++) if (i !== 1 && i !== 2 && BB8I_SPEC[i].test(s)) return true;
  return false;
}
function bb8lPoint(sent, n) {
  var s = String(sent || ""), first = true;
  var had = /\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/.test(s);
  if (had) {
    s = s.replace(/[ \t]*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, function (m) { if (!first) return ""; first = false; return (/^[ \t]/.test(m) ? " " : "") + "[" + n + "]"; });
    return s.replace(/\s+([.!?])/g, "$1");
  }
  var m = /([.!?]["')\]]*)\s*$/.exec(s);
  return m ? s.slice(0, m.index).replace(/\s+$/, "") + " [" + n + "]" + m[1] : s.replace(/\s+$/, "") + " [" + n + "]";
}
// Answers without the lead (valuation, or peer facts): the line goes before "In short:", else after the last fact line, else at the end.
function bb8lInsert(text, line) {
  var lines = String(text || "").split("\n"), at = -1, lastFact = -1;
  for (var i = 0; i < lines.length; i++) {
    if (at < 0 && /^In short:/.test(lines[i])) at = i;
    if (typeof bb8dIsFact === "function" && bb8dIsFact(lines[i])) lastFact = i;
  }
  if (at >= 0) { lines.splice(at, 0, line, ""); return lines.join("\n").replace(/\n{3,}/g, "\n\n"); }
  if (lastFact >= 0) { lines.splice(lastFact + 1, 0, line); return lines.join("\n"); }
  return String(text || "").replace(/\s+$/, "") + "\n\n" + line;
}
async function bb8lValEarn(st) {
  if (!st || !st.chat || st.bb8eMode !== "valuation" || !st.bb8lEarnP) return null;
  if (!st.bb8lEarnDone) {
    var e = null;
    try { e = await Promise.race([st.bb8lEarnP, bb8Late(BB8L_EARN_MS)]); } catch (x) { e = null; }
    if (e === "bb8-late") e = null;
    st.bb8lEarnDone = true;
    if (e) {
      // Number it as the final source list will: client sources (bb8j fills them on the JSON path after this
      // wrapper runs, so the same builder is used here), the peer source, then this line.
      var client = Array.isArray(st.clientSources) && st.clientSources.length ? st.clientSources
        : (st.body && typeof bb8jClient === "function" && typeof bb8jSources === "function" ? bb8jClient(bb8jSources(st.body)) : (st.clientSources || []));
      var n = client.length + (st.peerSource || (Array.isArray(st.facts) && st.facts.length) || st.bb8eMode === "valuation" ? 1 : 0) + 1;
      var base = e.sym;
      var src = bb8lEarnSrc(e, typeof bb8bYahooSym === "function" ? bb8bYahooSym(base) : base, base);
      st.bb8lEarn = Object.assign({}, e, { src: src, line: bb8lEarnLine(e), n: n });
    }
  }
  return st.bb8lEarn || null;
}
function bb8lValPrompt(e) {
  return "NEXT EARNINGS (server fact from Yahoo Finance, shown to the reader; cite it with [" + e.n + "] if you mention the date):\n" + e.line + " [" + e.n + "]\n" + BB8L_EARN_RULE;
}
// bb8l (chat73 2, 3): insiders. meta.window stays the page window; meta.span is the whole loaded span (the newest
// filing the first page showed through this page's from). Display-ready UK dates sit next to the ISO fields.
function bb8lNewestFor(ticker, cik) {
  var best = "";
  var take = function (d) { var p = bb8lYmd(d); if (p && p.iso > best) best = p.iso; };
  try {
    if (typeof bb8hKey === "function" && typeof bb7Recall === "function") {
      var row = bb7Recall(bb8hKey(ticker, "full"));
      if (row && row.body && row.body.newestFiling) take(row.body.newestFiling);
    }
  } catch (e) {}
  take(bb8lNewestMem.get("t:" + String(ticker || "").toUpperCase()));
  if (cik) take(bb8lNewestMem.get("c:" + String(Number(cik))));
  return best;
}
function bb8lSpan(from, to, label) {
  var lab = from && to && typeof bb8WindowLabel === "function" ? bb8WindowLabel(from, to) : "";
  return { from: from || "", to: to || "", label: lab || label || "", fromUk: bb8lDay(from), toUk: bb8lDay(to) };
}
function bb8lRowDates(body) {
  if (!body || typeof body !== "object") return body;
  if (Array.isArray(body.insider)) body.insider = body.insider.map(function (r) {
    if (!r || typeof r !== "object") return r;
    return Object.assign({}, r, { transactionDateUk: bb8lDay(r.transactionDate), filingDateUk: bb8lDay(r.filingDate) });
  });
  if (body.house && typeof body.house === "object" && Array.isArray(body.house.items)) {
    body.house = Object.assign({}, body.house, { items: body.house.items.map(function (it) {
      if (!it || typeof it !== "object") return it;
      var o = Object.assign({}, it, { filingDateUk: bb8lDay(it.filingDate) });
      if (Array.isArray(it.trades)) o.trades = it.trades.map(function (t) { return t && typeof t === "object" ? Object.assign({}, t, { dateUk: bb8lDay(t.date) }) : t; });
      return o;
    }) });
  }
  var w = body.meta && body.meta.window;
  if (w && typeof w === "object") {
    if (w.from != null) w.fromUk = bb8lDay(w.from);
    if (w.to != null) w.toUk = bb8lDay(w.to);
    var sp = bb8lSpan(w.from, w.to, w.label);
    sp.label = w.label || sp.label;
    sp.before = null;
    sp.toSource = "page";
    if (w.partial) sp.partial = true;
    body.meta.span = sp;
  }
  return body;
}
try {
  if (typeof rt32Yahoo === "function") {
    // One Yahoo quoteSummary per symbol at a time: the card's beta and earnings lookups share it (pending only).
    var bb8lYahoo0 = rt32Yahoo;
    rt32Yahoo = function (sym) { return bb8lYahooShared(String(sym || "")); };
  }
  if (typeof bb8eMovePack === "function") {
    var bb8lPack0 = bb8eMovePack;
    bb8eMovePack = async function (base) {
      var st = bb8dStore();
      var ep = null;
      try { if (st && st.chat && (st.bb8eCard || bb8lAsks(bb8lQuestion(st)))) { ep = bb8lEarnGet(base); ep.catch(function () {}); } } catch (e) { ep = null; }
      var pack = await bb8lPack0.apply(this, arguments);
      if (pack && ep) { try { pack.bb8lEarn = await ep; } catch (e) { pack.bb8lEarn = null; } }
      return pack;
    };
  }
  if (typeof bb8eLead === "function") {
    var bb8lLead0 = bb8eLead;
    bb8eLead = function (pack, card, n0) {
      var out = bb8lLead0.apply(this, arguments);
      try {
        var e = pack && pack.bb8lEarn;
        if (e && out && typeof out.text === "string") {
          var lines = out.text.split("\n"), oldFacts = lines.slice(1).join("\n");
          var k = n0 + out.sources.length + 1;
          var src = bb8lEarnSrc(e, pack.ysym, pack.base);
          out.sources.push(src);
          var line = bb8lEarnLine(e) + " [" + k + "]", at = lines.length;
          for (var i = 1; i < lines.length; i++) if (/^In the news/.test(lines[i])) { at = i; break; }
          lines.splice(at, 0, line);
          var text = lines.join("\n");
          out.prompt = out.prompt.replace(oldFacts, lines.slice(1).join("\n")) + " " + BB8L_EARN_RULE;
          out.text = text;
          out.paint = text.replace(/\s*\[\d+\]/g, "");
          out.bb8gNums = typeof bb8gNums === "function" ? bb8gNums(text) : out.bb8gNums;
          out.bb8hFigs = null;
          out.bb8lEarn = Object.assign({}, e, { src: src, line: bb8lEarnLine(e), n: k });
        }
      } catch (x) {}
      return out;
    };
  }
  if (typeof bb2Read0 === "function") {
    var bb8lRead0 = bb2Read0;
    bb2Read0 = async function () {
      var body = await bb8lRead0.apply(this, arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && st.bb8eMode === "valuation" && !st.bb8lEarnP && bb8lAsks(bb8lQuestion(st))) {
          var base = typeof bb8eBaseOf === "function" ? bb8eBaseOf(bb8lQuestion(st), body) : null;
          if (base) { st.bb8lEarnP = bb8lEarnGet(base); st.bb8lEarnP.catch(function () {}); }
        }
      } catch (e) {}
      return body;
    };
  }
  if (typeof bb2Complete === "function") {
    var bb8lEarnComplete0 = bb2Complete;
    bb2Complete = async function (system, messages, onDelta) {
      var args = Array.prototype.slice.call(arguments);
      try { var e = await bb8lValEarn(bb8dStore()); if (e) args[0] = String(system || "") + "\n\n" + bb8lValPrompt(e); } catch (x) {}
      return bb8lEarnComplete0.apply(this, args);
    };
  }
  if (typeof generateAi === "function") {
    var bb8lEarnGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && options && typeof options.system === "string") {
          var e = await bb8lValEarn(st);
          if (e) args[0] = Object.assign({}, options, { system: options.system + "\n\n" + bb8lValPrompt(e) });
        }
      } catch (x) {}
      return bb8lEarnGen0.apply(this, args);
    };
  }
  if (typeof bb8eFull === "function") {
    var bb8lFull0 = bb8eFull;
    bb8eFull = function (st) {
      var full = bb8lFull0.apply(this, arguments);
      try { if (st && st.bb8eMode === "valuation" && st.bb8lEarn && st.bb8lEarn.src && full.indexOf(st.bb8lEarn.src) < 0) full.push(st.bb8lEarn.src); } catch (e) {}
      return full;
    };
  }
  if (typeof bb8eCites === "function") {
    var bb8lCites0 = bb8eCites;
    bb8eCites = function (text, full) {
      var args = Array.prototype.slice.call(arguments);
      try {
        // Valuation answers, and move answers composed from peer facts (no lead): the line is added once.
        var st = bb8dStore(), e = bb8lEarnOf(st);
        var at = e && Array.isArray(full) ? full.indexOf(e.src) : -1;
        if (at >= 0 && String(text || "").indexOf("Next earnings:") < 0) args[0] = bb8lInsert(text, e.line + " [" + (at + 1) + "]");
      } catch (x) {}
      return bb8lCites0.apply(this, args);
    };
  }
  if (typeof bb8hIndex === "function") {
    var bb8lIndex0 = bb8hIndex;
    bb8hIndex = function (st, facts) {
      var idx = bb8lIndex0.apply(this, arguments);
      try {
        var e = bb8lEarnOf(st);
        if (e && e.src && idx) {
          var n = (typeof bb8eFull === "function" ? bb8eFull(st) : []).indexOf(e.src) + 1;
          if (n >= 1) {
            var t = e.line + " [" + n + "]";
            idx.text[n] = (idx.text[n] || "") + "\n" + t;
            idx.fact[n] = (idx.fact[n] || "") + "\n" + t;
            idx.bb8lEarn = e; idx.bb8lEarnN = n;
          }
        }
      } catch (x) {}
      return idx;
    };
  }
  if (typeof bb8hFixSentence === "function") {
    // A sentence about the next earnings date keeps (or is pointed at) the Next earnings line's [n]; a sentence that
    // names a different date, or calls an estimated date confirmed, goes.
    var bb8lFix0 = bb8hFixSentence;
    bb8hFixSentence = function (sent, idx) {
      try {
        var e = idx && idx.bb8lEarn, n = idx && idx.bb8lEarnN;
        var s = String(sent || "");
        if (e && n && bb8lEarnSent(s, e)) {
          if (!bb8lDateOk(s, e)) return "";
          if (e.isEstimate && /\bconfirm\w*\b|\bofficial\w*\b/i.test(s) && !/\b(?:not|un)\s*-?confirm/i.test(s)) return "";
          var cites = typeof bb8iCiteNums === "function" ? bb8iCiteNums(s) : [];
          if (cites.indexOf(n) >= 0 || bb8lDates(s).length) {
            var figs = typeof bb8hFigs === "function" ? bb8hFigs(s) : {}, foreign = false;
            for (var k in figs) if (!(idx.factFigs && idx.factFigs[k])) foreign = true;
            if (!foreign) return bb8lPoint(s, n);
          }
        }
        // A sentence that is not about the earnings date may not lean on that line: its [n] is re-pointed by bb8h.
        if (e && n && !bb8lEarnSent(s, e) && (typeof bb8iCiteNums === "function" ? bb8iCiteNums(s) : []).indexOf(n) >= 0) {
          var s2 = s.replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) {
            var keep = g.split(/\s*,\s*/).filter(function (x) { return Number(x) !== n; });
            return "[" + (keep.length ? keep.join(", ") : "99") + "]";
          });
          return bb8lFix0.call(this, s2, idx);
        }
      } catch (x) {}
      return bb8lFix0.apply(this, arguments);
    };
  }
  if (typeof bb8iKeep === "function") {
    var bb8lKeep0 = bb8iKeep;
    bb8iKeep = function (sent, resolve, st) {
      if (bb8lKeep0.apply(this, arguments)) return true;
      try {
        var e = bb8lEarnOf(st);
        if (e && e.src && typeof resolve === "function" && bb8lEarnSent(sent, e) && bb8lDateOk(sent, e) && !bb8lAttributed(sent)) {
          var ns = bb8iCiteNums(sent);
          for (var i = 0; i < ns.length; i++) if (resolve(ns[i]) === e.src) return true;
        }
      } catch (x) {}
      return false;
    };
  }
  if (typeof bb7FormList === "function") {
    var bb8lForms0 = bb7FormList;
    bb7FormList = function (submission) {
      var list = bb8lForms0.apply(this, arguments);
      try {
        var newest = "";
        (list || []).forEach(function (f) { var p = f && bb8lYmd(f.filingDate); if (p && p.iso > newest) newest = p.iso; });
        if (newest && submission) {
          (Array.isArray(submission.tickers) ? submission.tickers : []).forEach(function (t) { bb8lNewestMem.set("t:" + String(t).toUpperCase(), newest); });
          if (submission.cik) bb8lNewestMem.set("c:" + String(Number(submission.cik)), newest);
          while (bb8lNewestMem.size > 400) bb8lNewestMem.delete(bb8lNewestMem.keys().next().value);
        }
      } catch (e) {}
      return list;
    };
  }
  if (typeof bb7Shape === "function") {
    var bb8lShape0 = bb7Shape;
    bb7Shape = function () {
      var body = bb8lShape0.apply(this, arguments);
      try { bb8lRowDates(body); } catch (e) {}
      return body;
    };
  }
  if (typeof bb8Older === "function") {
    var bb8lOlder0 = bb8Older;
    bb8Older = async function (ticker, before, opts) {
      var out = await bb8lOlder0.apply(this, arguments);
      try {
        var m = out && out.body && out.body.meta, w = m && m.window;
        if (w && typeof w === "object") {
          var newest = bb8lNewestFor(bb7TickerKeys(ticker)[0], out.body.cik);
          var to = newest && newest >= String(w.to || "") ? newest : String(w.to || "");
          var sp = bb8lSpan(w.from, to, w.label);
          sp.before = before;
          sp.toSource = newest && newest >= String(w.to || "") ? "newest-filing" : "page";
          if (w.partial) sp.partial = true;
          m.span = sp;
        }
      } catch (e) {}
      return out;
    };
  }
} catch (e) { console.warn("bb8l earnings/insiders hooks skipped", e && e.message); }
// BB8L_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8l")]
if bad:
    die("bb8l block declares a non-bb8l function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8l block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8l function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8l block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8l replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8l setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8lbak"
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
print("APPLY bb8l UK time in user-visible text and model prompts; next-earnings fact line; insiders span and UK dates")
