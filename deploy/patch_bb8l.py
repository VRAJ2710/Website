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
print("APPLY bb8l UK time in user-visible text and model prompts")
