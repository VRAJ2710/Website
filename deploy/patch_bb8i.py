#!/usr/bin/env python3
"""patch_bb8i.py — Ask: speculative / attributed claims need a matching cited news headline; insiders (premium):
a failed refresh serves the older complete entry as stale, with a request-driven backoff. Server.js only.
Stacked on bb8i (server md5 dabd441e6cd87c6ce828601861142798). Does not rewrite app.js or index.html.
a) A model sentence that attributes a view ("analysts see/expect/believe", "investors expect/are favoring",
   "the market believes/is pricing", "traders expect", "many expect") or speculates ("is likely to", "could see",
   "poised to", "reflects ... expectations") is kept only when one of its [n] points at a NEWS source whose
   headline shares a ticker or two topic words with it; otherwise the whole sentence is dropped (bb8d splitter).
   Card, valuation and general answers, stream and JSON; after the bb8i citation matching, before 'In short'.
   Plain facts that say "expected" ("earnings are expected on 18 Nov [n]") are not matched. The prompt says so.
b) Insiders, premium only: when a refresh of an expired complete entry fails mid-scan (or errors), the complete
   entry is served instead: meta.stale true, X-Dispatch-Data-Status: stale, meta.statusLabel and
   meta.window.note "Updated <UK time> · refreshing" (bb8d formatter); the entry stays in place. Request-driven
   backoff: 60 s, doubling, capped at 15 min; during it requests get the complete entry at once, the first request
   after it starts the refresh, and concurrent requests share one scan. No timers, no background job.
   Free tier unchanged; with no complete entry, bb8i's partial / retry behaviour is unchanged.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8i.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "dabd441e6cd87c6ce828601861142798",
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
    print("bb8i %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8i before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8i %s untouched" % label)

if "// \u2500\u2500 bb8i \u2500\u2500" in v:
    print("REFUSE: bb8i already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8h end", "// BB8H_JS_END"),
    ("bb8hKey", "function bb8hKey(ticker, mode) {"),
    ("bb8hServes", "function bb8hServes(body, mode) {"),
    ("bb8hForm4", "async function bb8hForm4(ticker, mode, now) {"),
    ("bb8hFixSentence", "function bb8hFixSentence(sent, idx) {"),
    ("bb8hFigs", "function bb8hFigs(text) {"),
    ("bb8hForm4 hook", "if (typeof bb7Form4 === \"function\") bb7Form4 = bb8hForm4;"),
    ("BB8H_NOT_TICKERS", "var BB8H_NOT_TICKERS = {"),
    ("bb7Shape", "function bb7Shape(pack, opts) {"),
    ("bb7Inflight", "var bb7Inflight = new Map();"),
    ("bb8dCleanLine", "function bb8dCleanLine(line, ok, facts) {"),
    ("bb8dSplit", "function bb8dSplit(line) {"),
    ("bb8dStore", "function bb8dStore() {"),
    ("bb8dUk", "function bb8dUk(ms) {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb8eCites", "function bb8eCites(text, full) {"),
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
print("bb8i anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8i ── Ask: speculative or attributed claims stay only with a matching cited news headline; insiders
// (premium): a failed refresh serves the older complete entry as stale, with a request-driven backoff.
// BB8I_JS
// (a) Speculative / attributed claims: "analysts see", "investors expect", "the market is pricing", "is likely to",
// "could see", "poised to" ... A sentence like that is kept only when one of its [n] is a NEWS source whose
// headline shares a ticker or two topic words with it. Plain facts ("earnings are expected on 18 Nov") do not match.
var BB8I_SPEC = [
  /\b(?:analysts?|investors?|traders?|economists?|strategists?|observers?|(?:market )?participants|wall street|the street|the market|markets|many|some|most|bulls|bears|money managers|fund managers)\s+(?:[\w’'-]+\s+){0,3}?(?:see|sees|expect|expects|believe|believes|think|thinks|anticipate|anticipates|predict|predicts|forecast|forecasts|bet|bets|betting|fear|fears|worry|worries|hope|hopes|view|views|favou?r|favou?rs|favou?ring|are favou?ring|is pricing|are pricing|pricing in|price in|prices in|is priced for|remain (?:bullish|bearish|cautious|optimistic)|(?:are|is|remain|stay|turn|turned|grow|grew) (?:bullish|bearish|optimistic|pessimistic|confident|cautious|nervous|wary))\b/i,
  /\b(?:is|are|was|were|seems?|appears?|looks?)\s+(?:\w+\s+)?(?:likely|unlikely|poised|set|well[- ]placed|positioned)\s+to\b/i,
  /\b(?:likely|unlikely|poised)\s+to\b/i,
  /\b(?:could|may|might)\s+(?:see|benefit|face|gain|rally|rebound|struggle|suffer|outperform|underperform|continue|extend|lead|drive|boost|weigh)\b/i,
  /\bstands? to (?:benefit|gain|lose)\b/i,
  /\breflect(?:s|ing)?\s+(?:\w+\s+){0,3}?(?:expectations?|optimism|pessimism|caution|confidence|concerns?|fears?|sentiment|hopes?|bets?)\b/i,
  /\b(?:sentiment|expectations?)\s+(?:is|are|remain|remains|has|have)\b/i
];
var BB8I_STOP = { this: 1, that: 1, with: 1, from: 1, have: 1, been: 1, were: 1, will: 1, would: 1, could: 1, should: 1, their: 1, there: 1, which: 1, about: 1, after: 1, before: 1, into: 1, over: 1, more: 1, most: 1, than: 1, then: 1, they: 1, them: 1, also: 1, said: 1, says: 1, week: 1, today: 1, share: 1, stock: 1, market: 1, analyst: 1, investor: 1, trader: 1, expect: 1, expected: 1, expecting: 1, expectation: 1, believe: 1, likely: 1, unlikely: 1, poised: 1, pricing: 1, price: 1, favor: 1, favour: 1, favoring: 1, favouring: 1, continue: 1, continuing: 1, many: 1, some: 1, what: 1, when: 1, while: 1, where: 1, being: 1, other: 1, these: 1, those: 1, still: 1, even: 1, just: 1, only: 1, very: 1, such: 1, much: 1, year: 1, month: 1, session: 1, reflect: 1, reflects: 1, since: 1, week: 1, weeks: 1, months: 1, quarter: 1, prices: 1, growth: 1, earnings: 1, earning: 1, demand: 1, sector: 1, names: 1, group: 1, further: 1, again: 1, strong: 1, higher: 1, lower: 1, rising: 1, falling: 1, gains: 1, gain: 1, investo: 1, analys: 1, expect: 1, believ: 1, contin: 1, favour: 1, favori: 1, favour: 1 };
var BB8I_RULE = "Do not attribute views to analysts, investors, traders or the market, and do not speculate (for example 'likely to', 'could see', 'poised to') unless a news headline listed above says so; then cite that headline's [n]. Otherwise leave the sentence out.";
function bb8iSpec(sent) {
  var s = String(sent || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ");
  for (var i = 0; i < BB8I_SPEC.length; i++) if (BB8I_SPEC[i].test(s)) return true;
  return false;
}
function bb8iWords(text) {
  var out = {};
  String(text || "").toLowerCase().replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/[a-z][a-z’'-]{3,}/g, function (w) {
    w = w.replace(/[’'-].*$/, "");
    if (w.length > 4 && /s$/.test(w) && !/ss$/.test(w)) w = w.slice(0, -1);
    if (w.length >= 4 && !BB8I_STOP[w]) out[w.length > 6 ? w.slice(0, 6) : w] = 1;
    return w;
  });
  return out;
}
function bb8iTicks(text) {
  var out = {}, skip = typeof BB8H_NOT_TICKERS !== "undefined" ? BB8H_NOT_TICKERS : {};
  String(text || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/\$?\b[A-Z][A-Z0-9]{0,4}(?:\.[A-Z]{1,2})?\b/g, function (m) {
    var t = m.replace(/^\$/, "");
    if (t.length >= 2 && !skip[t]) out[t] = 1;
    return m;
  });
  return out;
}
// Server fact sources (quote, peer valuations, card score, Yahoo beta) are not news.
function bb8iIsNews(src, st) {
  if (!src || typeof src !== "object") return false;
  if (st && src === st.peerSource) return false;
  var name = String(src.name || ""), link = String(src.link || ""), detail = String(src.detail || src.title || "");
  if (name === "The Dispatch" || /\bquote\b/i.test(name)) return false;
  if (/\/quote\/[^/]+\/?(?:key-statistics\/?)?$/i.test(link) || /key-statistics/i.test(link)) return false;
  if (/P\/E|last price|session change|card score|\bbeta\b|refreshed on request/i.test(detail)) return false;
  return detail.trim().length >= 12;
}
function bb8iNewsMatch(sent, src) {
  var head = String(src.detail || "") + " " + String(src.title || "");
  var a = bb8iTicks(sent), b = bb8iTicks(head), k;
  for (k in a) if (b[k]) return true;
  // Topic words: one shared distinctive word (5+ letters, not a generic market word) or two shorter ones.
  var w = bb8iWords(sent), h = bb8iWords(head), n = 0;
  for (k in w) if (h[k]) { if (k.length >= 5) return true; n++; }
  return n >= 2;
}
function bb8iCiteNums(sent) {
  var out = [];
  String(sent || "").replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) { g.split(/\s*,\s*/).forEach(function (x) { out.push(Number(x)); }); return m; });
  return out;
}
// resolve(n) -> the source record [n] points at in this text's numbering.
function bb8iKeep(sent, resolve, st) {
  if (!bb8iSpec(sent)) return true;
  var ns = bb8iCiteNums(sent);
  for (var i = 0; i < ns.length; i++) {
    var src = resolve(ns[i]);
    if (src && bb8iIsNews(src, st) && bb8iNewsMatch(sent, src)) return true;
  }
  return false;
}
function bb8iLine(line, resolve, st) {
  var t = String(line || "");
  if (!t.trim() || /^\s*(?:\*\*)?Sources?:/i.test(t) || /^\s*In short:/.test(t)) return t;
  var pre = (/^\s*(?:[-*•]|\d+[.)]|#{1,6})\s+/.exec(t) || [""])[0];
  var parts = bb8dSplit(t.slice(pre.length));
  var kept = parts.filter(function (x) { return bb8iKeep(x, resolve, st); });
  if (kept.length === parts.length) return t;
  if (!kept.length) return "";
  return pre + kept.join(" ");
}
function bb8iText(text, resolve, st) {
  var lines = String(text == null ? "" : text).split("\n"), out = [];
  lines.forEach(function (l) { var c = bb8iLine(l, resolve, st); if (c || !l.trim()) out.push(c); });
  return out.join("\n").replace(/\n{3,}/g, "\n\n");
}
function bb8iFullResolve(st) {
  var full = typeof bb8eFull === "function" ? bb8eFull(st) : [];
  return function (n) { return full[n - 1] || null; };
}
// General answers: no peer facts and no card / move lead.
function bb8iGeneral(st) {
  if (!st || !st.chat) return false;
  if (Array.isArray(st.facts) && st.facts.length) return false;
  return !(st.bb8eMode === "move" && st.bb8eBase);
}
// (b) Insiders, premium: request-driven backoff after a failed refresh. No timers: the first request after the
// backoff starts the refresh, and concurrent requests share one scan (bb8h flight).
var BB8I_BACKOFF_MS = 60000;
var BB8I_BACKOFF_MAX_MS = 15 * 60000;
var bb8iBack = new Map();
var bb8iFlight = new Map();
function bb8iBackoffMs(fails) { return Math.min(BB8I_BACKOFF_MAX_MS, BB8I_BACKOFF_MS * Math.pow(2, Math.max(0, fails - 1))); }
function bb8iFail(key, now) {
  var b = bb8iBack.get(key) || { fails: 0, until: 0 };
  b.fails++;
  b.until = now + bb8iBackoffMs(b.fails);
  bb8iBack.set(key, b);
  if (bb8iBack.size > 200) bb8iBack.delete(bb8iBack.keys().next().value);
  return b;
}
function bb8iLabel(at) { return "Updated " + bb8dUk(at) + " \u00b7 refreshing"; }
function bb8iStale(row) {
  return Object.assign({}, row.body, { stale: true, asOf: new Date(row.at).toISOString(), bb8iAt: row.at });
}
try {
  if (typeof bb8hFixSentence === "function") {
    // bb8h's no-figure rule needs a shared ticker; a cited news headline that shares the sentence's topic words
    // ("Micron shares rise") is a match too, so that cite is kept for the claim check below.
    var bb8iFix0 = bb8hFixSentence;
    bb8hFixSentence = function (sent, idx) {
      try {
        var st = bb8dStore();
        if (st && st.chat && typeof bb8hFigs === "function" && !Object.keys(bb8hFigs(sent)).length) {
          var ns = bb8iCiteNums(sent), R = bb8iFullResolve(st);
          if (ns.length && ns.every(function (n) { var src = R(n); return src && bb8iIsNews(src, st) && bb8iNewsMatch(sent, src); })) return String(sent);
        }
      } catch (e) {}
      return bb8iFix0.apply(this, arguments);
    };
  }
  if (typeof bb8dCleanLine === "function") {
    var bb8iClean0 = bb8dCleanLine;
    bb8dCleanLine = function (line, ok, facts) {
      var out = bb8iClean0.apply(this, arguments);
      try {
        var st = bb8dStore();
        if (out && st && st.chat) out = bb8iLine(out, bb8iFullResolve(st), st);
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb2Complete === "function") {
    // General answers stream raw from bb8d; hold them to whole sentences and filter, like bb8d does with facts.
    var bb8iComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var st = bb8dStore();
      if (!bb8iGeneral(st) || typeof onDelta !== "function") return bb8iComplete0.apply(this, arguments);
      var pend = "", stop = false, resolve = null;
      // The filtered text is also kept whole: bb3b's line pump drops a newline that ends a delta, which glued
      // general answers into one line ("forecasts [1].Analysts"); the final reply is composed from this copy.
      st.bb8iGen = "";
      var emit = function (s) { if (s) { st.bb8iGen += s; onDelta(s); } };
      var paint = function (force) {
        if (!resolve) resolve = bb8iFullResolve(st);
        var out = "", nl = pend.lastIndexOf("\n");
        if (nl >= 0) {
          pend.slice(0, nl + 1).split("\n").slice(0, -1).forEach(function (line) {
            if (stop) return;
            if (/^\s*(?:\*\*)?Sources?:/i.test(line)) { stop = true; out += line + "\n"; return; }
            var c = bb8iLine(line, resolve, st);
            out += c || !line.trim() ? c + "\n" : "";
          });
          pend = pend.slice(nl + 1);
        }
        if (stop) { out += pend; pend = ""; emit(out); return; }
        if (pend) {
          var parts = bb8dSplit(pend);
          var done = force ? parts : parts.slice(0, -1);
          if (done.length) {
            var keepd = done.filter(function (x) { return bb8iKeep(x, resolve, st); });
            if (keepd.length) out += keepd.join(" ") + (force ? "" : " ");
            if (force) pend = "";
            else { var last = parts[parts.length - 1] || "", at = last ? pend.lastIndexOf(last) : -1; pend = at >= 0 ? pend.slice(at) : last; }
          }
          if (force && pend) { if (bb8iKeep(pend, resolve, st)) out += pend; pend = ""; }
        }
        emit(out);
      };
      var p = bb8iComplete0.call(this, system, messages, function (d) {
        if (typeof d !== "string") return onDelta.apply(this, arguments);
        try { pend += d; paint(false); } catch (e) { onDelta(d); }
      });
      return Promise.resolve(p).then(function (r) { try { paint(true); } catch (e) {} return r; });
    };
  }
  if (typeof bb3bCompose === "function") {
    // General answers (final / JSON): the text arrives renumbered by bb8e; map back, filter, renumber again.
    var bb8iCompose0 = bb3bCompose;
    bb3bCompose = function (reply, built, cite) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st0 = bb8dStore();
        var f0 = built && Array.isArray(built.facts) ? built.facts : [];
        if (!f0.length && bb8iGeneral(st0) && typeof st0.bb8iGen === "string" && st0.bb8iGen.trim()) args[0] = st0.bb8iGen;
      } catch (e0) {}
      var out = bb8iCompose0.apply(this, args);
      try {
        var st = bb8dStore();
        var facts = built && Array.isArray(built.facts) ? built.facts : [];
        if (!facts.length && bb8iGeneral(st)) {
          var full = typeof bb8eFull === "function" ? bb8eFull(st) : [];
          var keep = st.bb8eCites && st.bb8eCites.keep;
          var back = function (n) { return keep ? keep[n - 1] + 1 : n; };
          var text = keep ? String(out).replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) { return "[" + g.split(/\s*,\s*/).map(function (x) { return back(Number(x)); }).join(", ") + "]"; }) : String(out);
          var f2 = bb8iText(text, function (n) { return full[n - 1] || null; }, st).trim();
          if (f2 !== text.trim()) {
            var r = bb8eCites(f2, full);
            st.bb8eCites = r.keep ? { full: full, keep: r.keep } : null;
            out = r.text;
          }
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb2System === "function") {
    var bb8iSystem0 = bb2System;
    bb2System = function () { return bb8iSystem0.apply(this, arguments) + "\n\n" + BB8I_RULE; };
  }
  if (typeof generateAi === "function") {
    var bb8iGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && options && typeof options.system === "string" && options.system.indexOf(BB8I_RULE) < 0) args[0] = Object.assign({}, options, { system: options.system + "\n\n" + BB8I_RULE });
      } catch (e) {}
      return bb8iGen0.apply(this, args);
    };
  }
  if (typeof bb7Form4 === "function") {
    var bb8iForm40 = bb7Form4;
    bb7Form4 = async function (ticker, mode, now) {
      if (mode !== "full") return bb8iForm40.apply(this, arguments);
      var key = bb8hKey(ticker, "full");
      var row = bb7Recall(key);
      var good = row && bb8hServes(row.body, "full") ? row : null;
      if (!good || now - good.at <= good.ttl) return bb8iForm40.apply(this, arguments);
      var b = bb8iBack.get(key);
      if (b && now < b.until && !bb7Inflight.has("f4-flight:" + key + ":full")) return bb8iStale(good);
      // One shared refresh per ticker; each failure is counted once.
      var job = bb8iFlight.get(key);
      if (!job) {
        var self = this, args = arguments;
        job = (async function () {
          try {
            var pack = await bb8iForm40.apply(self, args);
            if (pack && !pack.unknown && pack.complete === true) bb8iBack.delete(key);
            else if (pack && !pack.unknown && pack.failed) bb8iFail(key, bb7Now());
            return { pack: pack };
          } catch (e) { bb8iFail(key, bb7Now()); return { err: e }; }
          finally { bb8iFlight.delete(key); }
        })();
        bb8iFlight.set(key, job);
      }
      var res = await job;
      var cur = bb7Recall(key);
      var keepRow = cur && bb8hServes(cur.body, "full") ? cur : good;
      if (res.err) return bb8iStale(keepRow);
      if (res.pack && !res.pack.unknown && res.pack.complete !== true && res.pack.failed) return bb8iStale(keepRow);
      return res.pack;
    };
  }
  if (typeof bb7Shape === "function") {
    var bb8iShape0 = bb7Shape;
    bb7Shape = function (pack, opts) {
      var body = bb8iShape0.apply(this, arguments);
      try {
        // Premium answers from an older complete entry say when it was updated.
        if (opts && opts.premium && pack && pack.stale && pack.complete === true && body && body.meta) {
          var at = pack.bb8iAt || Date.parse(pack.asOf);
          if (isFinite(at)) {
            body.meta.stale = true;
            body.meta.statusLabel = bb8iLabel(at);
            if (body.meta.window && typeof body.meta.window === "object") body.meta.window.note = body.meta.statusLabel;
          }
        }
      } catch (e) {}
      return body;
    };
  }
} catch (e) { console.warn("bb8i hooks skipped", e && e.message); }
// BB8I_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8i")]
if bad:
    die("bb8i block declares a non-bb8i function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8i block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8i function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8i block has a forbidden declaration")

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
print("bb8i setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8ibak"
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
print("APPLY bb8i speculative-claim filter + insiders stale-on-failed-refresh with request-driven backoff")
