#!/usr/bin/env python3
"""patch_bb5g.py — classify every quote route, and keep HK and softs on the desk clock.

Chat64 plus bb5b through bb5f. Server.js only. Does not rewrite app.js or
index.html and does not bump the client cache token.

Twelve Data, the reference quotes and Finnhub returned prices with no
status. Yahoo's currentTradingPeriod kept 0700.HK, HSI and the ICE softs
open after the onshore desk had shut, so a Friday print was stale. HSI was
also a continuous 09:30–16:00 session with no lunch. The Ask stream inserted
a newline between model chunks, which the client then flattened inside words.

Thin FX and the majors stay on the bb5f rules.

Usage: python3 patch_bb5g.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "b45b28623e1c8368140406558df95b90",
    "index.html": "b2271ff3debbf8790a4cdeb5a42b8297",
    "server.js": "c689b794b90bbd88fd00b12139842fbe",
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
    print("bb5g %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb5g before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5g %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5g \u2500\u2500" in v:
    print("REFUSE: bb5g already applied")
    sys.exit(0)

OPEN_OLD = """function bb5fOpen(spec, yahoo, tableOpen) {
  if (spec && spec.quiet) return !!tableOpen;
  if (yahoo && yahoo.known) return !!yahoo.open;
  return !!tableOpen;
}"""
OPEN_NEW = """function bb5fOpen(spec, yahoo, tableOpen) {
  return typeof bb5gOpen === "function" ? bb5gOpen(spec, yahoo, tableOpen) : (!!(spec && spec.quiet) ? !!tableOpen : (yahoo && yahoo.known ? !!yahoo.open : !!tableOpen));
}"""

SPEC_OLD = """  var spec = bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);"""
SPEC_NEW = """  var spec = typeof bb5gSpec === "function" ? bb5gSpec(symbol) : bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);"""

PUB_OLD = """    var spec = bb5eSpec(k);
    if ((spec && spec.quiet) || q.cached) out[k] = bb5eApply(q, k, null, t);"""
PUB_NEW = """    var spec = typeof bb5gSpec === "function" ? bb5gSpec(k) : bb5eSpec(k);
    if (!q.status || q.cached || (spec && spec.quiet)) out[k] = bb5eApply(q, k, null, t);"""

TD_OLD = """  if (p === "/api/twelve-data-quote") {
    return json(res, 200, await twelveDataQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean)));
  }"""
TD_NEW = """  if (p === "/api/twelve-data-quote") {
    return json(res, 200, bb5gPublish(await twelveDataQuote((url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean))));
  }"""

REF_OLD = """    return json(res, 200, await marketReferenceQuotesSWR());"""
REF_NEW = """    return json(res, 200, bb5gPublish(await marketReferenceQuotesSWR()));"""

FH_OLD = """      const quotes = await finnhubQuote([symbol]);
      return json(res, 200, quotes[symbol] || {});"""
FH_NEW = """      const quotes = await finnhubQuote([symbol]);
      return json(res, 200, bb5gPublish(quotes[symbol] || {}, null, symbol));"""

EN_OLD = """    return json(res, 200, { available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }, { "Cache-Control": "public, max-age=30" });"""
EN_NEW = """    return json(res, 200, bb5gPublish({ available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }), { "Cache-Control": "public, max-age=30" });"""

EMIT_OLD = """      if (acc && !/\\n$/.test(acc) && !/^\\n/.test(s)) s = "\\n" + s;
      acc += s;
      send({ t: s }, "model");"""
EMIT_NEW = """      var joined = typeof bb5gJoinStream === "function" ? bb5gJoinStream(acc, s, !modelAt) : { acc: acc + s, piece: s };
      s = joined.piece;
      acc = joined.acc;
      send({ t: s }, "model");"""

miss = []
if "// \u2500\u2500 bb5f \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5f ──")
for name, old in (
    ("bb5fOpen", OPEN_OLD),
    ("bb5e spec", SPEC_OLD),
    ("bb5fPublish", PUB_OLD),
    ("twelve-data route", TD_OLD),
    ("reference route", REF_OLD),
    ("finnhub quote", FH_OLD),
    ("spot energy", EN_OLD),
    ("ask stream join", EMIT_OLD),
):
    n = v.count(old)
    if n != 1:
        miss.append("server.js anchor %s matched %d times" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(OPEN_OLD, OPEN_NEW, 1)
v = v.replace(SPEC_OLD, SPEC_NEW, 1)
v = v.replace(PUB_OLD, PUB_NEW, 1)
v = v.replace(TD_OLD, TD_NEW, 1)
v = v.replace(REF_OLD, REF_NEW, 1)
v = v.replace(FH_OLD, FH_NEW, 1)
v = v.replace(EN_OLD, EN_NEW, 1)
v = v.replace(EMIT_OLD, EMIT_NEW, 1)

BLOCK = r'''
// ── bb5g ── Every quote route is classified. HK lunch and the softs use the desk clock.
// BB5G_JS
function bb5gSpec(symbol) {
  var s = typeof bb5eCanon === "function" ? bb5eCanon(symbol) : String(symbol || "").trim().toUpperCase();
  if (s === "HSI" || s === "^HSI") return { mode: "cash", tz: "Asia/Hong_Kong", o: 570, c: 960, lo: 720, lc: 780, label: "Hong Kong" };
  if (s === "WTI" || s === "BRENT" || s === "CL=F" || s === "BZ=F" || s === "XAU" || s === "GC=F" || s === "XAU/USD") return { mode: "fut", label: "US" };
  if (s === "DXY" || s === "DX-Y.NYB") return { mode: "fx", label: "FX" };
  if (s === "BTC/USD" || s === "ETH/USD") return { mode: "always", label: "Crypto" };
  var slash = s.indexOf("/") >= 0 ? s.replace(/\//g, "") : "";
  if (slash && typeof bb5eSpec === "function") {
    if (typeof bb5eFx === "object" && bb5eFx && bb5eFx[slash]) return bb5eSpec(slash);
    if (typeof bb5eThin === "object" && bb5eThin && bb5eThin[slash]) return bb5eSpec(slash);
    return { mode: "fx", label: "FX" };
  }
  return typeof bb5eSpec === "function" ? bb5eSpec(s) : null;
}
function bb5gOpen(spec, yahoo, tableOpen) {
  var scheduled = spec && (spec.quiet || spec.mode === "cash" || spec.mode === "soft" || spec.mode === "lumber" || spec.mode === "cbot" || spec.mode === "thin");
  if (scheduled) {
    if (!tableOpen) return false;
    if (yahoo && yahoo.known && !yahoo.open) return false;
    return true;
  }
  if (yahoo && yahoo.known) return !!yahoo.open;
  return !!tableOpen;
}
function bb5gIsQuote(q) {
  if (!q || typeof q !== "object" || Array.isArray(q)) return false;
  var p = Number(q.p);
  return isFinite(p) && p > 0;
}
function bb5gApply(q, symbol, now) {
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
}
function bb5gJoinStream(acc, piece, firstModel) {
  var s = String(piece || "");
  acc = String(acc || "");
  if (firstModel && acc && !/\n$/.test(acc) && !/^\n/.test(s)) s = "\n" + s;
  return { acc: acc + s, piece: s };
}
// BB5G_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5g")]
if bad:
    die("bb5g block declares a non-bb5g function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5g block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb5g block has a forbidden declaration")

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
    print("bb5g app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5g index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5gbak"
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
print("APPLY bb5g all quotes")
