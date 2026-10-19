#!/usr/bin/env python3
"""patch_bb8j.py — /api/chat JSON answers get the stream path's sources and one shared final assembler.
Server.js only. Stacked on bb8j (server md5 eb6937c7284919ed1a86f7e9d8b87d9c). Does not rewrite app.js or index.html.
Root cause: the JSON request store starts with clientSources [] (bb2 handle), so the "fill if missing" checks
never ran: general JSON answers listed no Sources and kept dangling [n]; card JSON numbered its move sources from
[1] instead of after the client sources as the stream does.
- bb8jSources: the stream's source gathering (bb3bFilterSources(bb3bRawSources(body))), now also used by the JSON
  path, which also lists the same CITABLE SOURCES in its prompt.
- bb8jAssemble: one final assembler (compose -> bb8h citation matching, bb8j claim filter, bb8e pruning and
  contiguous renumbering -> Sources footer with a blank line and UK times). The stream tail in bb3bStreamInner and
  the JSON finish (bb2Finish) both call it. [n] are stripped only when there are no sources at all.
- General answers (stream and JSON) now get bb8h citation matching; a cite to a news headline that shares the
  sentence's topic words counts as a match.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8j.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "eb6937c7284919ed1a86f7e9d8b87d9c",
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
    print("bb8j %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8j before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8j %s untouched" % label)

if "// \u2500\u2500 bb8j \u2500\u2500" in v:
    print("REFUSE: bb8j already applied")
    sys.exit(0)

REPLACE = [
    ("    var sources = bb3bFilterSources(bb3bRawSources(body), body);\n",
     "    var sources = bb8jSources(body);\n"),
    ("    var clientSources = bb3bArr(store && store.clientSources);\n    var citeN = store && store.peerSource ? (clientSources.length + 1) : 0;\n    var reply = bb3bCompose(acc, store && store.bb3Built, citeN);\n    var footSources = clientSources.slice();\n    if (store && store.peerSource) footSources.push(store.peerSource);\n    reply += typeof bb2Footer === \"function\" ? bb2Footer(footSources) : \"\";\n",
     "    var bb8jOut = bb8jAssemble(acc, store);\n    var reply = bb8jOut.reply;\n    var footSources = bb8jOut.sources;\n"),
    ("            var keepd = done.filter(function (x) { return bb8iKeep(x, resolve, st); });\n",
     "            var keepd = done.map(function (x) { return bb8jFix(x, st); }).filter(function (x) { return x && x.trim() && bb8iKeep(x, resolve, st); });\n"),
    ("          if (force && pend) { if (bb8iKeep(pend, resolve, st)) out += pend; pend = \"\"; }\n",
     "          if (force && pend) { var bb8jP = bb8jFix(pend, st); if (bb8jP && bb8jP.trim() && bb8iKeep(bb8jP, resolve, st)) out += bb8jP; pend = \"\"; }\n"),
]
REQUIRED = [
    ("bb8i end", "// BB8I_JS_END"),
    ("bb8iLine", "function bb8iLine(line, resolve, st) {"),
    ("bb8iGeneral", "function bb8iGeneral(st) {"),
    ("bb8hIndex", "function bb8hIndex(st, facts) {"),
    ("bb8hFixSentence", "function bb8hFixSentence(sent, idx) {"),
    ("bb8dSplit", "function bb8dSplit(line) {"),
    ("bb8dStore", "function bb8dStore() {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb3bRawSources", "function bb3bRawSources("),
    ("bb3bFilterSources", "function bb3bFilterSources("),
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
print("bb8j anchors ok x%d" % len(REQUIRED))

BLOCK = r"""

// ── bb8j ── /api/chat JSON answers get the stream path's sources and one shared final assembler.
// BB8J_JS
// Root cause: the JSON path's request store starts with clientSources [] (bb2 handle), so the bb2 and bb8e
// "fill if missing" checks never ran. General JSON answers then listed no Sources ("No news or price sources
// were supplied") and kept dangling [n] markers. Card JSON also numbered its move sources from 1, not after the
// client sources the way the stream does. Now both paths gather sources with bb8jSources, the JSON prompt lists
// the same CITABLE SOURCES, and both build the final reply with bb8jAssemble: compose (bb8h matching, bb8i
// claim filter, bb8e pruning and contiguous renumbering), then the Sources footer. [n] markers are stripped
// only when there are no sources at all.
var BB8J_CITE_HEAD = "CITABLE SOURCES (use these [n] markers only; do not invent sources):";
// The stream path's source gathering (bb3bStreamInner), shared with JSON.
function bb8jSources(body) {
  if (typeof bb3bFilterSources === "function" && typeof bb3bRawSources === "function") return bb3bFilterSources(bb3bRawSources(body), body);
  return typeof bb2ClientSources === "function" ? bb2ClientSources(body) : [];
}
function bb8jClient(sources) {
  return (Array.isArray(sources) ? sources : []).filter(function (src) { return !(src && src.name === "Yahoo Finance"); });
}
function bb8jCiteList(sources) {
  return (sources || []).map(function (s, i) { return "[" + (i + 1) + "] " + s.name + (s.asOf ? " as of " + s.asOf : "") + (s.link ? " " + s.link : "") + (s.detail ? " - " + s.detail : ""); }).join("\n");
}
// Last resort only: nothing to cite at all.
function bb8jStrip(text) {
  return String(text == null ? "" : text).replace(/[ \t]*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, "").replace(/[ \t]+([.!?,;:])/g, "$1");
}
// One final assembler for the stream tail and the JSON finish. Returns the reply and the listed sources.
function bb8jAssemble(reply, store) {
  var st = store || null;
  var facts = Array.isArray(st && st.facts) ? st.facts : [];
  var built = (st && st.bb3Built) || { facts: facts, asOf: "" };
  if (!Array.isArray(built.facts)) built = { facts: facts, asOf: built.asOf || "" };
  var client = Array.isArray(st && st.clientSources) ? st.clientSources : [];
  var cite = st && st.peerSource ? client.length + 1 : 0;
  var text = typeof bb3bCompose === "function" ? bb3bCompose(reply, built, cite) : String(reply || "");
  var foot = client.slice();
  if (st && st.peerSource) foot.push(st.peerSource);
  var full = typeof bb8eFull === "function" && st ? bb8eFull(st) : foot;
  if (!foot.length && !full.length) text = bb8jStrip(text);
  var footer = typeof bb2Footer === "function" ? bb2Footer(foot) : "";
  if (st) st.bb8jSources = foot;
  return { reply: String(text).replace(/\s+$/, "") + footer, sources: foot };
}
// bb8h citation matching for general answers (no card, no peer facts); bb8h covered only card and valuation.
// A cite to a news headline that shares the sentence's topic words is a match, so is one bb8h matches; others are
// re-pointed or stripped, and a figure no source carries goes with its sentence (bb8h rule).
function bb8jFix(sent, st) {
  var s = String(sent || "");
  if (!st || typeof bb8hIndex !== "function" || typeof bb8hFixSentence !== "function") return s;
  if (!/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/.test(s)) return s;
  var idx = bb8hIndex(st, []);
  if (!idx.n) return s;
  try {
    var ns = bb8iCiteNums(s), R = bb8iFullResolve(st);
    if (ns.length && ns.every(function (n) { var src = R(n); return src && bb8iIsNews(src, st) && bb8iNewsMatch(s, src); })) return s;
  } catch (e) {}
  return bb8hFixSentence(s, idx);
}
function bb8jFixLine(line, st) {
  var t = String(line || "");
  if (!t.trim() || /^\s*(?:\*\*)?Sources?:/i.test(t) || /^\s*In short:/.test(t) || /^\s*\[\d{1,2}\]\s/.test(t)) return t;
  var pre = (/^\s*(?:[-*•]|\d+[.)]|#{1,6})\s+/.exec(t) || [""])[0];
  var parts = bb8dSplit(t.slice(pre.length));
  var fixed = parts.map(function (x) { return bb8jFix(x, st); });
  var same = fixed.every(function (x, i) { return x === parts[i]; });
  if (same) return t;
  fixed = fixed.filter(function (x) { return x && x.trim(); });
  return fixed.length ? pre + fixed.join(" ") : "";
}
try {
  if (typeof bb8iLine === "function") {
    var bb8jLine0 = bb8iLine;
    bb8iLine = function (line, resolve, st) {
      var t = line;
      try { if (bb8iGeneral(st)) t = bb8jFixLine(line, st); } catch (e) {}
      if (line && String(line).trim() && !String(t).trim()) return "";
      return bb8jLine0.call(this, t, resolve, st);
    };
  }
  bb2Finish = function (reply, store) { return bb8jAssemble(reply, store).reply; };
  if (typeof generateAi === "function") {
    // JSON path (the stream fills these before prompting): same sources, same CITABLE SOURCES list.
    var bb8jGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && st.body && options && typeof options.system === "string" && Array.isArray(st.clientSources) && !st.clientSources.length && !st.bb8jFilled) {
          st.bb8jFilled = true;
          var client = bb8jClient(bb8jSources(st.body));
          st.clientSources = client;
          if (client.length && options.system.indexOf(BB8J_CITE_HEAD) < 0) {
            args[0] = Object.assign({}, options, { system: options.system + "\n\n" + BB8J_CITE_HEAD + "\n" + bb8jCiteList(client) + "\nCite a source only for what its line says; leave a sentence uncited rather than cite a source that does not say it." });
          }
        }
      } catch (e) {}
      return bb8jGen0.apply(this, args);
    };
  }
} catch (e) { console.warn("bb8j hooks skipped", e && e.message); }
// BB8J_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8j")]
if bad:
    die("bb8j block declares a non-bb8j function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8j block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8j function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8j block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8j replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8j setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8jbak"
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
print("APPLY bb8j shared source assembly and final assembler for /api/chat JSON and stream")
