#!/usr/bin/env python3
"""patch_bb8c.py — /api/financials 8s cap with partial results; Yahoo re-auth once. Server.js only.
Stacked on bb8b (server md5 5683b5b2720ee7ced93b95f69690b81e). Does not rewrite app.js or index.html.
1) /api/financials, /api/earnings, /api/statements, /api/holders answer within about 7.5s. If SEC or Yahoo is
   still running, the response is built from what is ready, with meta.partial and pending sources and the
   header X-Dispatch-Data-Status: partial. The shared in-flight build keeps running and fills the cache.
   Partial results are never cached; a build with a failed source is cached for 10 minutes, not 12 hours.
   Ask's peer lookups (rt32Build) get the full build as before.
2) Yahoo crumb: an expired crumb triggers one shared re-auth (getcrumb with the existing cookie first, then
   fc.yahoo + getcrumb), one retry, per-call timeouts of 6.5s (auth) and 7s (quote) and a 20s chain budget.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8c.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "5683b5b2720ee7ced93b95f69690b81e",
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
    print("bb8c %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8c before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8c %s untouched" % label)

if "// \u2500\u2500 bb8c \u2500\u2500" in v:
    print("REFUSE: bb8c already applied")
    sys.exit(0)

# (old, new, expected count)
EDITS = [
    ("rt32Build signature", 'async function rt32Build(sym) {', 'async function rt32Build(sym, bb8cSnap) {', 1),
    ("rt32Build settled", '  const [secR, yR] = await Promise.allSettled([', '  const [secR, yR] = bb8cSnap ? bb8cSnap.settled : await Promise.allSettled([', 1),
    ("rt32Build price fallback", '    const px = await rt32Price(ySym);', '    const px = bb8cSnap && bb8cSnap.snap ? null : await rt32Price(ySym);', 1),
]

miss = []
if "// \u2500\u2500 bb8b \u2500\u2500" not in v:
    miss.append("server.js marker missing: // \u2500\u2500 bb8b \u2500\u2500")
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
    print("bb8c edit %s x%d" % (name, want))

BLOCK = r"""
// ── bb8c ── /api/financials 8s cap with partial results; Yahoo re-auth once with tight timeouts.
// BB8C_JS
var bb8cFlight = new Map();
var bb8cAuthP = null;
var bb8cAuthCount = 0;
var BB8C_PATHS = { "/api/financials": 1, "/api/earnings": 1, "/api/statements": 1, "/api/holders": 1 };
function bb8cNum(name, dflt) {
  try { var n = Number(globalThis[name]); if (isFinite(n) && n > 0) return n; } catch (e) {}
  return dflt;
}
function bb8cBudget() { return bb8cNum("bb8cBudgetMs", 7500); }
function bb8cAuthMs() { return bb8cNum("bb8cAuthMs", 6500); }
function bb8cQuoteMs() { return bb8cNum("bb8cQuoteMs", 7000); }
function bb8cYahooBudget() { return bb8cNum("bb8cYahooBudgetMs", 20000); }
function bb8cGet(url, headers, ms) {
  return fetch(url, { headers: headers || {}, signal: AbortSignal.timeout(Math.max(1, Math.round(ms))), redirect: "follow" });
}
function bb8cCrumbOk(c, t) { return !!(c && c.ok && t && t.length <= 40 && !/[<{\s]/.test(t)); }
async function bb8cCrumb(force) {
  if (!force && RT32.crumb && Date.now() - RT32.crumbAt < 6 * 3600e3) return RT32.crumb;
  if (force && RT32.crumb && Date.now() - RT32.crumbAt < 15000) return RT32.crumb;
  if (bb8cAuthP) return bb8cAuthP;
  bb8cAuthP = (async function () {
    bb8cAuthCount++;
    if (force && RT32.ck) {
      try {
        var c0 = await bb8cGet("https://query2.finance.yahoo.com/v1/test/getcrumb", { "User-Agent": RT32_BUA, Cookie: RT32.ck }, bb8cAuthMs());
        var t0 = String(await c0.text()).trim();
        if (bb8cCrumbOk(c0, t0)) { RT32.crumb = t0; RT32.crumbAt = Date.now(); return t0; }
      } catch (e) {}
    }
    var r = await bb8cGet("https://fc.yahoo.com/", { "User-Agent": RT32_BUA }, bb8cAuthMs());
    var sc = (typeof r.headers.getSetCookie === "function" ? r.headers.getSetCookie() : [r.headers.get("set-cookie") || ""]).map(function (x) { return String(x).split(";")[0]; }).filter(Boolean).join("; ");
    var c = await bb8cGet("https://query2.finance.yahoo.com/v1/test/getcrumb", { "User-Agent": RT32_BUA, Cookie: sc }, bb8cAuthMs());
    var t = String(await c.text()).trim();
    if (!bb8cCrumbOk(c, t)) throw new Error("crumb " + c.status);
    RT32.ck = sc; RT32.crumb = t; RT32.crumbAt = Date.now();
    return t;
  })().finally(function () { bb8cAuthP = null; });
  return bb8cAuthP;
}
async function bb8cYahoo(sym) {
  var mods = "summaryDetail,defaultKeyStatistics,financialData,earnings,earningsHistory,calendarEvents,institutionOwnership,majorHoldersBreakdown,price,earningsTrend";
  var end = Date.now() + bb8cYahooBudget();
  var left = function (cap) { var ms = Math.min(cap, end - Date.now()); if (ms <= 0) throw new Error("yahoo budget"); return ms; };
  for (var i = 0; i < 2; i++) {
    var crumb = await rt32Crumb(i > 0);
    var r = await bb8cGet("https://query2.finance.yahoo.com/v10/finance/quoteSummary/" + encodeURIComponent(sym) + "?modules=" + mods + "&crumb=" + encodeURIComponent(crumb), { "User-Agent": RT32_BUA, Cookie: RT32.ck }, left(bb8cQuoteMs()));
    if (r.status === 401 || r.status === 403) { if (RT32.crumb === crumb) RT32.crumbAt = 0; continue; }
    if (!r.ok) throw new Error("yahoo " + r.status);
    var j = await r.json();
    var res = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
    if (!res) throw new Error("yahoo empty");
    return res;
  }
  throw new Error("yahoo auth");
}
async function bb8cSec(sym) {
  if (typeof bb8bForeign === "function" && bb8bForeign(sym)) return null;
  var m = await rt32CikMap();
  var e = m.get(sym) || m.get(String(sym).replace(/\./g, "-"));
  if (!e) return null;
  var r = await rt32Get("https://data.sec.gov/api/xbrl/companyfacts/CIK" + e.cik + ".json", { "User-Agent": RT32_UA, Accept: "application/json" });
  if (!r.ok) throw new Error("sec facts " + r.status);
  var j = await r.json();
  var s = rt32Sec(j.facts);
  s.name = e.name;
  return s;
}
function bb8cTrack(p) {
  var box = { state: null, p: p };
  p.then(function (v) { box.state = { status: "fulfilled", value: v }; }, function (e) { box.state = { status: "rejected", reason: e }; });
  return box;
}
function bb8cAny(d) { return !!(d && (d.financials || d.valuation || d.earnings || d.institutions)); }
function bb8cEnsure(sym, build0) {
  var key = String(sym || "").toUpperCase();
  var hit = bb8cFlight.get(key);
  if (hit) return hit;
  var ySym = typeof bb8bYahooSym === "function" ? bb8bYahooSym(key) : key.replace(/\./g, "-");
  var sec = bb8cTrack(bb8cSec(key));
  var yah = bb8cTrack(rt32Yahoo(ySym));
  var entry = { sym: key, sec: sec, yah: yah, t0: Date.now() };
  var failed = false;
  entry.full = Promise.allSettled([sec.p, yah.p]).then(function (settled) {
    failed = settled[1].status === "rejected" || (settled[0].status === "rejected");
    return build0(key, { settled: settled });
  }).then(function (data) {
    if (bb8cAny(data)) {
      // A build with a failed source is kept for 10 minutes, not 12 hours.
      RT32.cache.set(key, { at: failed ? Date.now() - 12 * 3600e3 + 10 * 60e3 : Date.now(), data: data });
      if (RT32.cache.size > 300) RT32.cache.delete(RT32.cache.keys().next().value);
    }
    return data;
  }).finally(function () { bb8cFlight.delete(key); });
  entry.full.catch(function () {});
  entry.snapshot = async function () {
    var pend = new Error("pending");
    var settled = [sec.state || { status: "rejected", reason: pend }, yah.state || { status: "rejected", reason: pend }];
    var data = await build0(key, { settled: settled, snap: true });
    var pending = [];
    if (!sec.state) { pending.push("sec"); if (data.sources) data.sources.sec = "pending"; }
    if (!yah.state) { pending.push("yahoo"); if (data.sources) data.sources.yahoo = "pending"; }
    data.meta = Object.assign({}, data.meta || {}, { partial: true, pending: pending });
    return data;
  };
  bb8cFlight.set(key, entry);
  return entry;
}
function bb8cLate(ms) {
  return new Promise(function (r) { var t = setTimeout(function () { r("bb8c-late"); }, Math.max(0, ms)); if (t && t.unref) t.unref(); });
}
async function bb8cLoad(sym, build0) {
  var entry = bb8cEnsure(sym, build0);
  var out = await Promise.race([entry.full.then(function (d) { return { d: d }; }, function (e) { return { e: e }; }), bb8cLate(bb8cBudget() - (Date.now() - entry.t0))]);
  if (out !== "bb8c-late") { if (out.e) throw out.e; return { data: out.d, partial: false }; }
  return { data: await entry.snapshot(), partial: true };
}
try {
  if (typeof rt32Crumb === "function") rt32Crumb = bb8cCrumb;
  if (typeof rt32Yahoo === "function") rt32Yahoo = bb8cYahoo;
  if (typeof rt32Build === "function" && typeof rt33sFund === "function") {
    var bb8cBuild0 = bb8bBuild0;
    var bb8cAssemble = function (key, snap) { return bb8cBuild0(key, snap); };
    rt32Build = function (sym) { return bb8cEnsure(sym, bb8cAssemble).full; };
    var bb8cFund0 = rt33sFund;
    rt33sFund = async function (req, res, p, url) {
      var sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
      var empty = function (reason) { return { symbol: sym, unavailable: true, reason: reason, data: [], earnings: [], holders: [], history: [] }; };
      if (!BB8C_PATHS[p] || RT33S_CRYPTO.has(sym) || /-USD$/.test(sym) || !/^[A-Z0-9][A-Z0-9.\-]{0,9}$/.test(sym)) return bb8cFund0.apply(this, arguments);
      var hit = RT32.cache.get(sym);
      var fresh = hit && Date.now() - hit.at < 12 * 3600e3;
      if (fresh) return bb8cFund0.apply(this, arguments);
      var data = null, partial = false, status = "";
      try {
        var got = await bb8cLoad(sym, bb8cAssemble);
        data = got.data; partial = got.partial;
        if (partial && hit && hit.data) { data = hit.data; partial = false; status = "stale"; }
        else if (!partial && !bb8cAny(data) && hit) { data = hit.data; status = "stale"; }
      } catch (e) {
        console.warn("[bb8c] fundamentals", sym, e && e.message);
        if (hit) { data = hit.data; status = "stale"; }
      }
      var headers = { "Cache-Control": "no-store", "X-Dispatch-Data-Status": partial ? "partial" : (status || "fresh") };
      if (!data) return json(res, 200, empty("source error"), headers);
      var any = bb8cAny(data);
      var base = { symbol: sym, asOf: data.asOf, sources: data.sources };
      if (data.meta) base.meta = data.meta;
      if (p === "/api/financials") return json(res, 200, any ? data : Object.assign({}, data, { unavailable: true }), headers);
      if (p === "/api/earnings") return json(res, 200, Object.assign(base, { earnings: data.earnings, history: data.history || [], nextEarnings: data.nextEarnings || null, beatRate: data.beatRate, avgSurprise: data.avgSurprise }), headers);
      if (p === "/api/holders") return json(res, 200, Object.assign(base, { institutions: data.institutions, holders: data.holders || [] }), headers);
      return json(res, 200, Object.assign(base, { financials: data.financials, data: [] }), headers);
    };
  }
} catch (e) { console.warn("bb8c hooks skipped", e && e.message); }
// BB8C_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8c")]
if bad:
    die("bb8c block declares a non-bb8c function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8c block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8c function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8c block has a forbidden declaration")

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
print("bb8c setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8cbak"
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
print("APPLY bb8c financials cap + yahoo re-auth")
