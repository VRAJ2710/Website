#!/usr/bin/env python3
"""patch_bb5f.py — thin FX is quiet while the onshore desk is shut.

Chat63 plus bb5b through bb5e. Server.js only. Does not rewrite app.js or
index.html and does not bump the client cache token.

USDINR is INR=X and USDBRL is BRL=X (BB3_ALIAS and the client map). They are
not renamed to USDINR=X. Twelve Data's basket is the majors and does not
serve these pairs. /api/yahoo-quote fetches them on the v7 batch, then the
chart pool when that row has no print time.

Yahoo's chart meta puts INR=X and BRL=X inside one currentTradingPeriod that
covers the London day, and stamps both with the same regularMarketTime. bb5e
trusted that period, so an onshore-closed pair was classified stale and the
note was dropped. A last-good refill returned that object unchanged.

Thin pairs now follow the onshore table during the New York FX week, on the
fresh row and on every refill. The Yahoo print time is kept. No timestamp is
invented. Majors stay on the 24/5 rule.

Usage: python3 patch_bb5f.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "4b094d30cc5070c2ca44d7979452d648",
    "index.html": "0e595097e68bcf2f8c0c90395add2880",
    "server.js": "f612d9fbd5155b5218665a4e4b16c1d4",
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
    print("bb5f %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb5f before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5f %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5f \u2500\u2500" in v:
    print("REFUSE: bb5f already applied")
    sys.exit(0)

WIRE_OLD = """function bb5dWire(symbol) {
  var raw = String(symbol || "").trim();
  if (!raw) return null;
  var wire = raw;
  try {
    if (typeof BB3_ALIAS === "object" && BB3_ALIAS && BB3_ALIAS[raw.toUpperCase()]) wire = String(BB3_ALIAS[raw.toUpperCase()]);
  } catch (e) {}
  return { req: raw, wire: wire };
}"""
WIRE_NEW = """function bb5dWire(symbol) {
  return bb5fWire(symbol);
}"""

MISS_OLD = """  var missing = wires.filter(function (wire) { return !merged[wire]; });"""
MISS_NEW = """  var missing = wires.filter(function (wire) {
    var hit = merged[wire];
    if (!hit) return true;
    return typeof bb5fNeedsChart === "function" && bb5fNeedsChart(wire, hit);
  });"""

OPEN_OLD = """  var open = yahoo.known ? yahoo.open : tableOpen;"""
OPEN_NEW = """  var open = typeof bb5fOpen === "function" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);"""

STATUS_OLD = """  var status = spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed";"""
STATUS_NEW = """  var status = typeof bb5fStatus === "function" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed");"""

ROUTE_OLD = """    const _fromLastGood = () => { const out = {}; for (const sym of symbols) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000) out[sym] = e.q; } return out; };
    if (!yahooRateLimiter.allow(clientAddress)) {
      return json(res, 200, _fromLastGood(), { "X-Dispatch-Data-Status": "cached" });
    }
    let _data;
    try { _data = await yahooQuote(symbols); } catch (e) { return json(res, 200, _fromLastGood(), { "X-Dispatch-Data-Status": "stale" }); }
    try { if (_data && typeof _data === "object") { for (const [k, v] of Object.entries(_data)) { if (v && typeof v === "object") _lg.set(k, { q: v, t: Date.now() }); } if (_lg.size > 2000) { const first = _lg.keys().next().value; _lg.delete(first); } for (const sym of symbols) { if (!(_data && _data[sym])) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000) _data[sym] = e.q; } } } } catch (e) {}
    return json(res, 200, _data);"""
ROUTE_NEW = """    const _fromLastGood = () => { const out = {}; for (const sym of symbols) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000 && e.q) out[sym] = bb5fRefill(e.q, sym); } return out; };
    if (!yahooRateLimiter.allow(clientAddress)) {
      return json(res, 200, bb5fPublish(_fromLastGood()), { "X-Dispatch-Data-Status": "cached" });
    }
    let _data;
    try { _data = await yahooQuote(symbols); } catch (e) { return json(res, 200, bb5fPublish(_fromLastGood()), { "X-Dispatch-Data-Status": "stale" }); }
    try { if (_data && typeof _data === "object") { for (const [k, v] of Object.entries(_data)) { if (v && typeof v === "object") _lg.set(k, { q: v, t: Date.now() }); } if (_lg.size > 2000) { const first = _lg.keys().next().value; _lg.delete(first); } for (const sym of symbols) { if (!(_data && _data[sym])) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000 && e.q) _data[sym] = bb5fRefill(e.q, sym); } } } } catch (e) {}
    return json(res, 200, bb5fPublish(_data));"""

miss = []
if "// \u2500\u2500 bb5e \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5e ──")
for name, old in (
    ("bb5dWire", WIRE_OLD),
    ("chart miss", MISS_OLD),
    ("bb5e open", OPEN_OLD),
    ("bb5e status", STATUS_OLD),
    ("yahoo-quote route", ROUTE_OLD),
):
    n = v.count(old)
    if n != 1:
        miss.append("server.js anchor %s matched %d times" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(WIRE_OLD, WIRE_NEW, 1)
v = v.replace(MISS_OLD, MISS_NEW, 1)
v = v.replace(OPEN_OLD, OPEN_NEW, 1)
v = v.replace(STATUS_OLD, STATUS_NEW, 1)
v = v.replace(ROUTE_OLD, ROUTE_NEW, 1)

BLOCK = r'''
// ── bb5f ── Thin FX follows the onshore desk. Refills are classified too.
// BB5F_JS
var bb5fAlias = { USDINR: "INR=X", USDBRL: "BRL=X" };
function bb5fWire(symbol) {
  var raw = String(symbol || "").trim();
  if (!raw) return null;
  var key = raw.toUpperCase();
  var wire = raw;
  try {
    if (typeof BB3_ALIAS === "object" && BB3_ALIAS && BB3_ALIAS[key]) wire = String(BB3_ALIAS[key]);
  } catch (e) {}
  if (wire === raw && bb5fAlias[key]) wire = bb5fAlias[key];
  var upper = wire.toUpperCase();
  if (upper === "USDINR=X") wire = "INR=X";
  if (upper === "USDBRL=X") wire = "BRL=X";
  return { req: raw, wire: wire };
}
function bb5fOpen(spec, yahoo, tableOpen) {
  if (spec && spec.quiet) return !!tableOpen;
  if (yahoo && yahoo.known) return !!yahoo.open;
  return !!tableOpen;
}
function bb5fStatus(spec, d) {
  if (!spec || !spec.quiet) return "closed";
  try {
    if (typeof bb5eFxOpen === "function" && !bb5eFxOpen(d)) return "closed";
  } catch (e) {
    try { if (typeof bb5eOffday === "function" && bb5eOffday(spec, d)) return "closed"; } catch (e2) {}
  }
  return "quiet";
}
function bb5fNeedsChart(symbol, q) {
  var spec = typeof bb5eSpec === "function" ? bb5eSpec(symbol) : null;
  if (!spec || !spec.quiet) return false;
  var ts = Number(q && q.ts);
  return !(isFinite(ts) && ts > 0);
}
function bb5fRefill(q, symbol) {
  if (!q || typeof q !== "object") return q;
  var out = {};
  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];
  out.cached = true;
  return out;
}
function bb5fPublish(data, now) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return data;
  var t = now == null ? Date.now() : Number(now);
  if (!isFinite(t)) t = Date.now();
  var out = {};
  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {
    var q = data[k];
    if (!q || typeof q !== "object" || typeof bb5eApply !== "function" || typeof bb5eSpec !== "function") { out[k] = q; continue; }
    var spec = bb5eSpec(k);
    if ((spec && spec.quiet) || q.cached) out[k] = bb5eApply(q, k, null, t);
    else out[k] = q;
  }
  return out;
}
// BB5F_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5f")]
if bad:
    die("bb5f block declares a non-bb5f function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5f block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb5f block has a forbidden declaration")

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
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
    print("bb5f app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5f index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5fbak"
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
print("APPLY bb5f thin fx")
