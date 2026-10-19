#!/usr/bin/env python3
"""patch_bb5h.py — stale follows each route's refresh cadence. Server.js only.

Chat64 plus bb5b through bb5g. Does not rewrite app.js or index.html and does
not bump the client cache token.

Twelve Data, the reference desk, spot energy and Finnhub were classified with
the Yahoo window (bb5dCadenceMs 60s + bb5dMarginMs 2m, server.js:10535-10536).
A Twelve Data print about 200s old was therefore stale, even though
dispatch_market_data_coordination serves that payload for TWELVE_DATA_CACHE_MS
(server.js:431, written to cache_expires_at at server.js:4961). The 30s
TWELVE_DATA_REFRESH_LEASE_MS (server.js:449) is only the in-flight claim.

Inside the route window a print stays fresh, or delayed with "updated HH:MM UK"
once it is older than 60s. Past cadence + 2m it is stale. Yahoo is unchanged.
Closed and quiet are unchanged.

Usage: python3 patch_bb5h.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "b45b28623e1c8368140406558df95b90",
    "index.html": "b2271ff3debbf8790a4cdeb5a42b8297",
    "server.js": "5867c44014b5ac8855786b719b2cbe59",
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
    print("bb5h %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb5h before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5h %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5h \u2500\u2500" in v:
    print("REFUSE: bb5h already applied")
    sys.exit(0)

REF_OLD = """    return json(res, 200, bb5gPublish(await marketReferenceQuotesSWR()));"""
REF_NEW = """    return json(res, 200, bb5gPublish(await marketReferenceQuotesSWR(), null, null, "reference"));"""

TD_OLD = """    return json(res, 200, bb5gPublish(await twelveDataQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean))));"""
TD_NEW = """    return json(res, 200, bb5gPublish(await twelveDataQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean)), null, null, "twelve"));"""

FH_OLD = """      return json(res, 200, bb5gPublish(quotes[symbol] || {}, null, symbol));"""
FH_NEW = """      return json(res, 200, bb5gPublish(quotes[symbol] || {}, null, symbol, "finnhub"));"""

EN_OLD = """    return json(res, 200, bb5gPublish({ available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }), { "Cache-Control": "public, max-age=30" });"""
EN_NEW = """    return json(res, 200, bb5gPublish({ available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }, null, null, "energy"), { "Cache-Control": "public, max-age=30" });"""

PUB_OLD = """function bb5gApply(q, symbol, now) {
  if (!bb5gIsQuote(q) || typeof bb5eApply !== "function") return q;
  var wasStale = q.stale === true;
  var next = bb5eApply(q, symbol, null, now);
  if (!next || typeof next !== "object") return q;
  if (wasStale && next.status !== "closed" && next.status !== "quiet") next.stale = true;
  return next;
}
function bb5gMap(map, now) {
  if (!map || typeof map !== "object" || Array.isArray(map)) return map;
  var out = {};
  for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k)) out[k] = bb5gApply(map[k], k, now);
  return out;
}
function bb5gPublish(data, now, symbol) {
  if (!data || typeof data !== "object") return data;
  if (Array.isArray(data)) return data;
  var t = now == null ? Date.now() : Number(now);
  if (!isFinite(t)) t = Date.now();
  if (bb5gIsQuote(data)) return bb5gApply(data, symbol || data.symbol || data.name || "", t);
  var out = {};
  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {
    if (k === "quotes" || k === "directIndices") out[k] = bb5gMap(data[k], t);
    else out[k] = bb5gApply(data[k], k, t);
  }
  return out;
}"""
PUB_NEW = """function bb5gApply(q, symbol, now, cadence) {
  if (!bb5gIsQuote(q) || typeof bb5eApply !== "function") return q;
  var wasStale = q.stale === true;
  var next = bb5eApply(q, symbol, null, now);
  if (!next || typeof next !== "object") return q;
  if (cadence > 0 && typeof bb5hRetouch === "function") return bb5hRetouch(next, now, cadence);
  if (wasStale && next.status !== "closed" && next.status !== "quiet") next.stale = true;
  return next;
}
function bb5gMap(map, now, cadence) {
  if (!map || typeof map !== "object" || Array.isArray(map)) return map;
  var out = {};
  for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k)) out[k] = bb5gApply(map[k], k, now, cadence);
  return out;
}
function bb5gPublish(data, now, symbol, route) {
  if (!data || typeof data !== "object") return data;
  if (Array.isArray(data)) return data;
  var t = now == null ? Date.now() : Number(now);
  if (!isFinite(t)) t = Date.now();
  var cadence = typeof bb5hRouteMs === "function" ? bb5hRouteMs(route, data, t) : 0;
  if (bb5gIsQuote(data)) return bb5gApply(data, symbol || data.symbol || data.name || "", t, cadence);
  var out = {};
  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {
    if (k === "quotes" || k === "directIndices") out[k] = bb5gMap(data[k], t, cadence);
    else out[k] = bb5gApply(data[k], k, t, cadence);
  }
  return out;
}"""

miss = []
if "// \u2500\u2500 bb5g \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5g ──")
for name, old in (
    ("reference route", REF_OLD),
    ("twelve-data route", TD_OLD),
    ("finnhub quote", FH_OLD),
    ("spot energy", EN_OLD),
    ("bb5g publish", PUB_OLD),
):
    n = v.count(old)
    if n != 1:
        miss.append("server.js anchor %s matched %d times" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(REF_OLD, REF_NEW, 1)
v = v.replace(TD_OLD, TD_NEW, 1)
v = v.replace(FH_OLD, FH_NEW, 1)
v = v.replace(EN_OLD, EN_NEW, 1)
v = v.replace(PUB_OLD, PUB_NEW, 1)

BLOCK = r'''
// ── bb5h ── Stale follows the route cache, not the Yahoo 60s window.
// BB5H_JS
function bb5hEnergyMs(now) {
  var t = now == null ? Date.now() : Number(now);
  if (!isFinite(t)) t = Date.now();
  var day = new Date(t).toISOString().slice(0, 10);
  var budget = 300;
  try {
    if (typeof process !== "undefined" && process.env && process.env.RT43_TD_ENERGY_DAILY != null) budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));
  } catch (e) {}
  var used = 0;
  try {
    if (typeof RT43S_EN === "object" && RT43S_EN && RT43S_EN.day === day) used = Number(RT43S_EN.used) || 0;
  } catch (e2) {}
  var left = budget - used;
  var msLeft = Date.parse(day + "T24:00:00Z") - t;
  if (!(left >= 2) || !(msLeft > 0)) return 60000;
  return Math.max(60000, Math.floor(msLeft / (left / 2)));
}
function bb5hRouteMs(route, data, now) {
  // twelve: TWELVE_DATA_CACHE_MS server.js:431, cache_expires_at server.js:4961.
  // The 30s TWELVE_DATA_REFRESH_LEASE_MS at server.js:449 is the in-flight claim.
  if (route === "twelve") return typeof TWELVE_DATA_CACHE_MS === "number" ? TWELVE_DATA_CACHE_MS : 15 * 60 * 1000;
  // reference: REFERENCE_QUOTE_CACHE_MS server.js:575.
  if (route === "reference") return typeof REFERENCE_QUOTE_CACHE_MS === "number" ? REFERENCE_QUOTE_CACHE_MS : 5 * 60 * 1000;
  // energy: refreshSec is the interval at server.js:7934, echoed at server.js:7947.
  if (route === "energy") {
    var sec = data && Number(data.refreshSec);
    if (isFinite(sec) && sec > 0) return Math.round(sec * 1000);
    return bb5hEnergyMs(now);
  }
  // finnhub: no cache TTL. Live fetch at server.js:4339. Window is bb5dCadenceMs server.js:10535.
  if (route === "finnhub") return typeof bb5dCadenceMs === "number" ? bb5dCadenceMs : 60000;
  return 0;
}
function bb5hHm(ms) {
  try {
    return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms));
  } catch (e) { return ""; }
}
function bb5hClass(q, now, cadence) {
  var delay = Number(q && q.delayMin);
  if (!isFinite(delay) || delay < 0) delay = 0;
  delay = Math.round(delay);
  var ts = Number(q && q.ts);
  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;
  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;
  var margin = typeof bb5dMarginMs === "number" ? bb5dMarginMs : 120000;
  var fresh = typeof bb5dCadenceMs === "number" ? bb5dCadenceMs : 60000;
  var windowMs = Number(cadence) + delay * 60000 + margin;
  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? "delayed" : "fresh", stale: false, note: delay > 0 ? "delayed " + delay + "m by exchange" : "" };
  if (Number(age) > windowMs) return { delayMin: delay, status: "stale", stale: true, note: "" };
  if (Number(age) > fresh) {
    var hm = bb5hHm(tsMs);
    return { delayMin: delay, status: "delayed", stale: false, note: hm ? "updated " + hm + " UK" : "updated UK" };
  }
  if (delay > 0) return { delayMin: delay, status: "delayed", stale: false, note: "delayed " + delay + "m by exchange" };
  return { delayMin: 0, status: "fresh", stale: false, note: "" };
}
function bb5hRetouch(q, now, cadence) {
  if (!q || typeof q !== "object") return q;
  if (q.status === "closed" || q.status === "quiet") return q;
  var cls = bb5hClass(q, now, cadence);
  q.delayMin = cls.delayMin;
  q.status = cls.status;
  q.stale = cls.stale;
  if (cls.note) q.note = cls.note;
  else delete q.note;
  delete q.nextOpen;
  return q;
}
// BB5H_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5h")]
if bad:
    die("bb5h block declares a non-bb5h function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5h block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb5h block has a forbidden declaration")

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
    print("bb5h app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5h index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5hbak"
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
print("APPLY bb5h route cadence")
