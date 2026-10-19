#!/usr/bin/env python3
"""patch_bb8k.py — Ask/Expert reader hints on both /api/chat paths; the JSON body gets a top-level sources array.
Server.js only. Stacked on bb8k (server md5 ccab2b5891c284d7d68aeb84c19291c6). Does not rewrite app.js or index.html.
1) The client sends hints { length, focus } (the reader's Ask settings) in the same body on the stream and JSON
   requests. Only the JSON route applied them (rt17ApplyChatHints); the stream path ignored them. One builder,
   bb8kHintNote / bb8kApplyHints, now serves both (rt17ApplyChatHints delegates to it; bb3bStreamInner calls it
   right after reading the body, as the JSON route does). There is no separate Expert mode flag: every /api/chat
   answer is Dispatch Expert, premium-gated on both paths by currentUser + hasPremiumAccess, unchanged.
2) JSON body: top-level sources = the list the final Sources footer printed (same objects, order and numbering as
   the stream's done-event sources). structured.sources is unchanged.
3) The JSON prompt's CITABLE SOURCES list (bb8j) now prints UK times, as the stream prompt does.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8k.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "ccab2b5891c284d7d68aeb84c19291c6",
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
    print("bb8k %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8k before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8k %s untouched" % label)

if "// \u2500\u2500 bb8k \u2500\u2500" in v:
    print("REFUSE: bb8k already applied")
    sys.exit(0)

REPLACE = [
    ("    var body = typeof bb2Read0 === \"function\" ? await bb2Read0(req) : {};\n",
     "    var body = typeof bb2Read0 === \"function\" ? await bb2Read0(req) : {};\n    if (typeof bb8kApplyHints === \"function\") bb8kApplyHints(body);\n"),
    ("                  body.reply = bb2Finish(body.reply, st);\n",
     "                  body.reply = bb2Finish(body.reply, st);\n                  if (typeof bb8kSources === \"function\") body.sources = bb8kSources(st);\n"),
]
REQUIRED = [
    ("bb8j end", "// BB8J_JS_END"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb8jCiteList", "function bb8jCiteList(sources) {"),
    ("bb8dUkText", "function bb8dUkText(text) {"),
    ("rt17ApplyChatHints", "function rt17ApplyChatHints(body) {"),
    ("RT17_ENUMS", "const RT17_ENUMS = {"),
    ("bb3bStreamInner", "async function bb3bStreamInner(req, res) {"),
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
print("bb8k anchors ok x%d" % len(REQUIRED))

BLOCK = r"""

// ── bb8k ── Ask/Expert reader hints on both /api/chat paths; JSON body carries the footer's sources.
// BB8K_JS
// The client sends the same body to both paths: { messages, context, tickers, knownTickers, hints, sources }, where
// hints = the reader's Ask settings { length, focus } (app.js _rt37Hints; focus is dropped for non-gold tickers).
// There is no separate Expert mode flag: every /api/chat answer is Dispatch Expert and premium-gated on both paths
// (currentUser + hasPremiumAccess, unchanged). Before bb8k only the JSON route applied the hints
// (rt17ApplyChatHints); the stream path ignored them. Both now use bb8kHintNote / bb8kApplyHints.
// One builder for the reader-preference note (validated enums only, never free text).
function bb8kHintNote(hints) {
  var h = hints && typeof hints === "object" ? hints : null;
  if (!h) return "";
  var length = RT17_ENUMS.askLength.indexOf(h.length) >= 0 ? h.length : null;
  var focus = RT17_ENUMS.askFocus.indexOf(h.focus) >= 0 ? h.focus : null;
  if (!length && !focus) return "";
  var focusTxt = { gold: "gold", macro: "macro and rates", crypto: "crypto", em: "emerging markets" }[focus];
  return "\n\n[Reader preferences: " + (length === "brief" ? "keep the answer brief (3-5 sentences)" : length === "detailed" ? "a detailed answer is welcome" : "") +
    (length && focus ? "; " : "") + (focus ? "where relevant, frame it for a reader focused on " + focusTxt : "") + ".]";
}
// Appends the note to the latest user turn once per request body (same place and clip as rt17ApplyChatHints).
function bb8kApplyHints(body) {
  if (!body || typeof body !== "object" || body.__bb8kHinted) return body;
  try { Object.defineProperty(body, "__bb8kHinted", { value: true, enumerable: false }); } catch (e) {}
  var note = bb8kHintNote(body.hints);
  if (!note || !Array.isArray(body.messages) || !body.messages.length) return body;
  for (var i = body.messages.length - 1; i >= 0; i--) {
    var m = body.messages[i];
    if (m && m.role === "user" && typeof m.content === "string") { m.content = m.content.slice(0, 7800) + note; break; }
  }
  return body;
}
// Sources for the JSON body: the list the final Sources footer printed (bb8jAssemble), same objects and order.
function bb8kSources(st) {
  return st && Array.isArray(st.bb8jSources) ? st.bb8jSources.slice() : [];
}
try {
  // bb8j's JSON CITABLE SOURCES list printed ISO times; the stream prompt (bb2System) prints UK times.
  if (typeof bb8jCiteList === "function" && typeof bb8dUkText === "function") {
    var bb8kCite0 = bb8jCiteList;
    bb8jCiteList = function () { return bb8dUkText(bb8kCite0.apply(this, arguments)); };
  }
  if (typeof rt17ApplyChatHints === "function") rt17ApplyChatHints = function (body) { bb8kApplyHints(body); };
} catch (e) { console.warn("bb8k hooks skipped", e && e.message); }
// BB8K_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8k")]
if bad:
    die("bb8k block declares a non-bb8k function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8k block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8k function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8k block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8k replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8k setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8kbak"
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
print("APPLY bb8k reader hints on both /api/chat paths + JSON top-level sources")
