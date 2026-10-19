#!/usr/bin/env python3
"""patch_bb8b.py — Ask cold-cache facts and replayed-answer cleanup; fundamentals symbol fixes. Server.js only.
Stacked on bb8 (server md5 c5cdaf0eb4cdee4daed380e57d2a1522). Does not rewrite app.js or index.html.
P1: a cold /api/chat peer question (Pulse "Ask ->") raced the peer refresh against an 800ms timer and built
the system prompt before the refresh finished, so the model got no FACT lines, no bb8 conclusion fix and no
NTM forward P/E; it copied the client context (old Yahoo +1y forward P/E) and the replayed earlier answer.
bb8b waits up to 3s for the peer facts before prompting, builds them late if still missing, rewrites old
forward P/E figures in the client context and earlier assistant turns, drops "cannot compare" sentences from
replayed turns, drops generic metric filler, strips a model-written Sources line, and tags valuation cache
entries "bb8b" so untagged ones are ignored.
Fundamentals: non-US listings (BP.L) were sent to Yahoo as BP-L (404) and to the SEC ticker map; now BP.L and
no SEC. Concurrent rt32Build calls for one symbol share one in-flight build.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8b.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "c5cdaf0eb4cdee4daed380e57d2a1522",
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
    print("bb8b %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8b before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8b %s untouched" % label)

if "// \u2500\u2500 bb8b \u2500\u2500" in v:
    print("REFUSE: bb8b already applied")
    sys.exit(0)

# (old, new, expected count)
EDITS = [
    ("lead wait", '            new Promise(function (r) { setTimeout(function () { r("slow"); }, 800); })',
     '            new Promise(function (r) { setTimeout(function () { r("slow"); }, bb8bLeadWait()); })', 1),
    ("facts before prompt", '    var buf = "";\n    function emitModel(text) {\n',
     '    if (pendingLead) { try { await pendingLead; } catch (e9) {} pendingLead = null; }\n    var buf = "";\n    function emitModel(text) {\n', 1),
    ("late facts", '    if (store) store.facts = facts;\n    var clientSources = bb3bArr(store && store.clientSources);\n',
     '    if (store) store.facts = facts;\n    if (store && !facts.length && base && job && typeof job.then === "function") { try { await Promise.race([job, new Promise(function (r) { setTimeout(r, bb8bLeadWait() + 1000); })]); } catch (e10) {} }\n    if (store && !facts.length && base && typeof bb8bLateFacts === "function") { facts = bb8bLateFacts(store, base, syms, sources) || facts; }\n    var clientSources = bb3bArr(store && store.clientSources);\n', 1),
    ("rt32 yahoo symbol", '  const ySym = sym.replace(/\\./g, "-");', '  const ySym = bb8bYahooSym(sym);', 1),
    ("rt32 sec skip", '      const m = await rt32CikMap(); const e = m.get(sym) || m.get(ySym); if (!e) return null;',
     '      if (bb8bForeign(sym)) return null;\n      const m = await rt32CikMap(); const e = m.get(sym) || m.get(sym.replace(/\\./g, "-")); if (!e) return null;', 1),
    ("beta yahoo symbol", 'quote = await rt32Yahoo(key.replace(/\\./g, "-"));', 'quote = await rt32Yahoo(bb8bYahooSym(key));', 1),
]

miss = []
if "// \u2500\u2500 bb8 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // \u2500\u2500 bb8 \u2500\u2500")
for name, old, new, want in EDITS:
    n = v.count(old)
    if n != want:
        miss.append("anchor %s matched %d times (want %d)" % (name, n, want))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)
for name, old, new, want in EDITS:
    v = v.replace(old, new)
    print("bb8b edit %s x%d" % (name, want))

BLOCK = r"""
// ── bb8b ── Ask cold-cache facts, replayed-answer cleanup, filler drop, tagged valuation cache; fundamentals symbol fixes.
// BB8B_JS
// Cold /api/chat (Pulse "Ask ->"): the peer refresh raced an 800ms timer and the system prompt was built
// before it finished, so the model saw no FACT lines and copied the client's context and replayed history.
var BB8B_TAG = "bb8b";
var bb8bBuildFlight = new Map();
var BB8B_FOREIGN = { L: 1, IL: 1, HK: 1, T: 1, DE: 1, F: 1, PA: 1, AS: 1, BR: 1, MI: 1, MC: 1, LS: 1, SW: 1, VX: 1, ST: 1, OL: 1, CO: 1, HE: 1, IR: 1, VI: 1, WA: 1, PR: 1, AT: 1, IS: 1, TO: 1, V: 1, CN: 1, NE: 1, AX: 1, NZ: 1, NS: 1, BO: 1, KS: 1, KQ: 1, TW: 1, TWO: 1, SS: 1, SZ: 1, SI: 1, JK: 1, BK: 1, KL: 1, SA: 1, MX: 1, BA: 1, SN: 1, JO: 1, TA: 1, SR: 1, QA: 1 };
function bb8bLeadWait() {
  try { var n = Number(globalThis.bb8bLeadWaitMs); if (isFinite(n) && n > 0) return n; } catch (e) {}
  return 3000;
}
function bb8bForeign(sym) {
  var m = /\.([A-Z]{1,3})$/.exec(String(sym || "").toUpperCase());
  return !!(m && BB8B_FOREIGN[m[1]]);
}
function bb8bYahooSym(sym) {
  var s = String(sym || "").toUpperCase();
  return bb8bForeign(s) ? s : s.replace(/\./g, "-");
}
function bb8bFwdFor(tk) {
  var key = String(tk || "").toUpperCase();
  if (!key) return null;
  try {
    var hit = bb2Mem && bb2Mem.vals && bb2Mem.vals.get(key);
    if (hit && hit.v && hit.v.bb8b === BB8B_TAG && hit.v.forward > 0) return hit.v.forward;
  } catch (e) {}
  try {
    var r = typeof RT32 === "object" && RT32 && RT32.cache && RT32.cache.get(key);
    var v = r && r.data && r.data.valuation;
    if (v && v.forwardBasis && v.forwardPe > 0) return v.forwardPe;
  } catch (e2) {}
  return null;
}
function bb8bFwdLine(line, fallbackTk) {
  var s = String(line || "");
  if (!/forward\s+P\/E/i.test(s)) return s;
  var lead = /^\s*\$?([A-Z][A-Z0-9.\-]{0,9})\s*:/.exec(s);
  var tk = lead ? lead[1] : fallbackTk;
  var fwd = bb8bFwdFor(tk);
  return s.replace(/(forward\s+P\/E)(?:\s*\(next 12 months\))?(?:\s*(?:of|is|at|:))?\s*~?(\d+(?:\.\d+)?|n\/a|—)\s*[x×]?/gi, function (_m, word) {
    var w = /^F/.test(word) ? "Forward P/E" : "forward P/E";
    return fwd > 0 ? w + " (next 12 months) " + Number(fwd).toFixed(1) + "x" : w + " not available";
  });
}
function bb8bFwdText(text, fallbackTk) {
  return String(text == null ? "" : text).split("\n").map(function (line) { return bb8bFwdLine(line, fallbackTk); }).join("\n");
}
function bb8bFillerRe() {
  return /[^.!?\n]*\b(?:this (?:valuation )?(?:metric|ratio|multiple|measure|figure) (?:provides|gives|offers|helps)|(?:the )?(?:p\/e|price[- ]to[- ]earnings)(?: ratio)? (?:is|measures|reflects) (?:a |the )?(?:common|widely used|popular|key|useful|how)|investors (?:often|typically|commonly|generally) (?:use|look at) (?:this|these|the p\/e|valuation)|it(?:'s| is) (?:important|worth noting|essential) to (?:note|remember|consider) that (?:valuation|p\/e|multiples))[^.!?\n]*[.!?]?/gi;
}
function bb8bDropFiller(text) {
  return String(text == null ? "" : text).replace(bb8bFillerRe(), function (m) {
    if (/\d/.test(m) || /\b[A-Z]{2,5}\b/.test(m.replace(/\bP\/E\b/gi, ""))) return m;
    return "";
  }).replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/ {2,}/g, " ");
}
function bb8bCleanReplay(text, tk) {
  var s = bb8bFwdText(text, tk);
  if (typeof bb8DeadEndRe === "function") s = s.replace(new RegExp(bb8DeadEndRe().source, "gi"), "");
  return bb8bDropFiller(s).trim();
}
function bb8bStripModelSources(text) {
  return String(text == null ? "" : text).replace(/\s*\bSources:\s*\[\d+\][^\n]*(?:\n(?!\n)[^\n]*)*\s*$/i, "");
}
function bb8bLateFacts(store, base, syms, sources) {
  if (!store || !base || typeof bb3bReadCache !== "function" || typeof bb2BuildFacts !== "function") return null;
  var vals = bb3bReadCache(syms);
  if (!vals) return null;
  var built;
  try { built = bb2BuildFacts(base, vals); } catch (e) { return null; }
  var facts = (built && built.facts) || [];
  if (!facts.length) return null;
  store.facts = facts;
  store.bb3Built = built;
  if (!store.peerSource && typeof bb2PeerSource === "function") store.peerSource = bb2PeerSource(base, built);
  return facts;
}
try {
  if (typeof bb3bReadCache === "function") {
    var bb8bRead0 = bb3bReadCache;
    bb3bReadCache = function (syms) {
      var out = bb8bRead0.call(this, syms);
      if (!out) return out;
      var kept = {}, any = false;
      Object.keys(out).forEach(function (k) { if (out[k] && out[k].bb8b === BB8B_TAG) { kept[k] = out[k]; any = true; } });
      return any ? kept : null;
    };
  }
  if (typeof bb2Refresh === "function") {
    var bb8bRefresh0 = bb2Refresh;
    bb2Refresh = async function (syms) {
      await bb8bRefresh0.call(this, syms);
      (syms || []).forEach(function (s) {
        var hit = bb2Mem.vals.get(String(s || "").toUpperCase());
        if (hit && hit.v && typeof bb8ApplyNtm === "function") { bb8ApplyNtm(String(s).toUpperCase(), hit.v); hit.v.bb8b = BB8B_TAG; }
      });
    };
  }
  if (typeof bb3bTrimBody === "function") {
    var bb8bTrim0 = bb3bTrimBody;
    bb3bTrimBody = function (body) {
      var out = bb8bTrim0.call(this, body);
      if (!out || typeof out !== "object") return out;
      var tk = Array.isArray(out.tickers) && out.tickers[0] ? out.tickers[0] : (typeof bb2Base === "function" ? bb2Base(typeof bb2Question === "function" ? bb2Question(out) : "") : "");
      var copy = Object.assign({}, out);
      if (typeof copy.context === "string") copy.context = bb8bFwdText(copy.context, tk);
      if (Array.isArray(copy.messages)) {
        var lastUser = -1;
        copy.messages.forEach(function (m, i) { if (m && m.role === "user") lastUser = i; });
        copy.messages = copy.messages.map(function (m, i) {
          if (!m || m.role !== "assistant" || i > lastUser) return m;
          return Object.assign({}, m, { content: bb8bCleanReplay(m.content, tk) || "(earlier answer omitted)" });
        });
      }
      return copy;
    };
  }
  if (typeof bb3bRewrite === "function") {
    var bb8bRewrite0 = bb3bRewrite;
    bb3bRewrite = function (text, facts, drop) { return bb8bDropFiller(bb8bRewrite0.call(this, text, facts, drop)); };
  }
  if (typeof bb3bHold === "function") {
    var bb8bHold0 = bb3bHold;
    bb3bHold = function (text, facts) { return bb8bHold0.call(this, text, facts) || /\b(this|investors|it(?:'s| is)|the p\/e|price[- ]to)\b/i.test(String(text || "")); };
  }
  if (typeof bb3bCompose === "function") {
    var bb8bCompose0 = bb3bCompose;
    bb3bCompose = function (reply, built, cite) { return bb8bCompose0.call(this, bb8bStripModelSources(reply), built, cite); };
  }
  if (typeof bb2Footer === "function") {
    var bb8bFooter0 = bb2Footer;
    bb2Footer = function (sources) { return "\n\n" + String(bb8bFooter0.call(this, sources) || "").replace(/^\s+/, ""); };
  }
  if (typeof bb2System === "function") {
    var bb8bSystem0 = bb2System;
    bb2System = function (body, built, sources) {
      return bb8bSystem0.call(this, body, built, sources) + "\n\nDo not add generic sentences explaining what a valuation metric is or what it provides insight into. Earlier assistant answers in this chat may be out of date; use only the figures in this prompt.";
    };
  }
  if (typeof rt32Build === "function") {
    var bb8bBuild0 = rt32Build;
    rt32Build = function (sym) {
      var key = String(sym || "").toUpperCase();
      if (bb8bBuildFlight.has(key)) return bb8bBuildFlight.get(key);
      var job = bb8bBuild0.call(this, sym).finally(function () { bb8bBuildFlight.delete(key); });
      bb8bBuildFlight.set(key, job);
      return job;
    };
  }
} catch (e) { console.warn("bb8b hooks skipped", e && e.message); }
// BB8B_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8b")]
if bad:
    die("bb8b block declares a non-bb8b function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8b block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8b function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8b block has a forbidden declaration")

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
print("bb8b setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8bbak"
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
print("APPLY bb8b ask cold facts + fundamentals")
