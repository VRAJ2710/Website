#!/usr/bin/env python3
"""bb10e: QA chat83b P0 hardening on top of bb10d live.
(1) Regime cold-start bug: bb10bRegimeEnsureV set bb8rReg = null, which made bb8rRegimeRow() throw and GET /api/regime fall through to 404.
    The reset keeps its state object and bb8rRegimeRow() heals a missing one.
(2) A per-route deadline (BB10E_DEADLINE_MS = 8000) on /api/regime, /api/desk-quotes, /api/market-reference-quotes, /api/yahoo-quote,
    /api/ext-hours and /api/gold-desk only: HTTP 200 with the last good body for that path+query (stale:true) or the route's own
    empty shape, X-Dispatch-Deadline: 1, no-store; the late original handler is silently discarded. Reuses the in-repo withTimeout()
    helper (one per-request setTimeout cleared on end/close). No interval timers, no scheduled jobs, no tables, no secrets. Server-only.
Usage: python3 patch_bb10e.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
BASE_MD5 = "6a359cecb836848284c2264d13122482"
MARK = "// ── bb10e:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
// ── bb10e: QA chat83b P0 hardening, on top of bb10d live. Server-only; no secrets, tables or background timers. ──
// (1) Regime cold-start bug: bb10bRegimeEnsureV set bb8rReg = null, so every later bb8rRegimeRow() threw ("reading 'row'"), the route
//     errored inside the bb10 prefetch guard and GET /api/regime fell through to 404. The reset now keeps the state object, and
//     bb8rRegimeRow() heals a missing state object itself.
// (2) Per-route deadline (BB10E_DEADLINE_MS, default 8000) on exactly six GET/HEAD routes. If the handler has not ended the response by
//     the deadline the client gets HTTP 200 with the last good body for that exact path+query (stale:true + servedFromCacheAt) or the
//     route's own empty shape. The late original handler is then silently discarded (every write/end/setHeader becomes a no-op).
//     TIMER: this reuses the in-repo withTimeout() helper (the AI request deadline helper). That is one per-request setTimeout,
//     cleared in .finally() as soon as the response ends, the socket closes or the handler rejects. No interval timer, no scheduled job, no module-level timer.
var BB10E_DEADLINE_MS = 8000;
var BB10E_ROUTES = { "/api/regime": "regime", "/api/desk-quotes": "desk", "/api/market-reference-quotes": "ref", "/api/yahoo-quote": "yahoo", "/api/ext-hours": "ext", "/api/gold-desk": "gold" };
var BB10E_CACHE_MAX = 200, BB10E_BODY_MAX = 512 * 1024, BB10E_CACHE_AGE_MS = 24 * 3600 * 1000;
var bb10eLast = new Map(); // key (path+query, gold-desk also the session hash) -> { at, text }
var BB10E_STALE_NOTE = "This is the last good reading from a few minutes ago; the live feed did not answer in time.";
function bb10eKey(req, route) {
  var k = String(req.url || "");
  if (k.length > 400) return "";
  if (route === "gold") {
    var ck = String((req.headers && req.headers.cookie) || "");
    k += "|" + crypto.createHash("sha256").update(ck).digest("hex").slice(0, 24); // premium-only body: only the same session gets it back
  }
  return k;
}
function bb10eStore(key, status, ct, chunks, bytes) {
  try {
    if (!key || status !== 200 || bytes <= 0 || bytes > BB10E_BODY_MAX || !/json/i.test(String(ct || ""))) return;
    var text = Buffer.concat(chunks).toString("utf8"), o = JSON.parse(text);
    if (!o || typeof o !== "object" || Array.isArray(o) || o.available === false || o.error) return;
    bb10eLast.delete(key);
    bb10eLast.set(key, { at: Date.now(), text: text });
    while (bb10eLast.size > BB10E_CACHE_MAX) bb10eLast.delete(bb10eLast.keys().next().value);
  } catch (e) {}
}
function bb10eEmpty(route, url) {
  var now = Date.now(), iso = bb10Iso(now), uk = bb10Uk(now);
  if (route === "regime") {
    var r = typeof bb10bUnavailable === "function" ? bb10bUnavailable("The regime reading did not come back in time.") : { available: false, regime: null, label: null, score: null, overweight: [], underweight: [], neutral: [], narrative: "", note: "Try again in a minute.", retryAfterSec: 30, asOf: iso, asOfUk: uk };
    r.available = false;
    ["overweight", "underweight", "neutral"].forEach(function (k) { if (!Array.isArray(r[k])) r[k] = []; });
    if (!r.retryAfterSec) r.retryAfterSec = 30;
    return r;
  }
  if (route === "desk") {
    var raw = String(url.searchParams.get("symbols") || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean).slice(0, 20), missing = [];
    raw.forEach(function (tk) {
      var s = ""; try { s = bb10DeskSym(tk) || ""; } catch (e) {}
      var m = { ticker: tk.toUpperCase().slice(0, 20), reason: "The quote feed did not answer in time" };
      if (s) m.symbol = s;
      missing.push(m);
    });
    return { available: false, asOf: iso, asOfUk: uk, timezone: "Europe/London", quotes: {}, missing: missing, note: "The quote feed did not answer in time. Every requested symbol is listed in missing[]; try again in a minute.", retryAfterSec: 30 };
  }
  if (route === "ref") return { available: false, fetchedAt: now, asOf: iso, asOfUk: uk, note: "The reference quote feed did not answer in time. Try again in a minute.", retryAfterSec: 30 };
  if (route === "ext") return { available: false, quotes: {}, reason: "deadline" };
  if (route === "gold") return { available: false, error: "The gold desk is taking longer than usual. Try again in a minute.", note: "The gold desk did not finish in time.", retryAfterSec: 60, asOf: iso, asOfUk: uk };
  return {}; // yahoo-quote: the client reads a symbol-keyed map, so the empty shape is {}
}
function bb10eFallback(req, res, st, route) {
  var hdr = Object.assign({}, typeof SECURITY_HEADERS === "object" && SECURITY_HEADERS ? SECURITY_HEADERS : {}, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Dispatch-Deadline": "1" });
  var out = null, body = null, now = Date.now(), url = new URL(req.url || "/", "http://localhost");
  var hit = st.key ? bb10eLast.get(st.key) : null;
  if (hit && now - hit.at <= BB10E_CACHE_AGE_MS && req.method === "GET") {
    try {
      var o = JSON.parse(hit.text);
      if (route === "yahoo") { body = hit.text; } // a symbol-keyed map: the stale marker rides in headers so no row is added
      else { o.stale = true; o.servedFromCacheAt = bb10Iso(now); body = JSON.stringify(o); }
      hdr["X-Dispatch-Data-Status"] = "stale"; hdr["X-Dispatch-Stale"] = "1";
    } catch (e) { body = null; }
  }
  if (body == null) { body = JSON.stringify(bb10eEmpty(route, url)); hdr["X-Dispatch-Data-Status"] = "unavailable"; }
  hdr["Content-Length"] = Buffer.byteLength(body);
  ["ETag", "Content-Encoding", "Content-Range", "Last-Modified", "Content-Length"].forEach(function (h) { try { st.o.removeHeader.call(res, h); } catch (e) {} });
  st.fired = true; st.own = true; // from here every write/end/setHeader of the late original handler is a silent no-op
  try { st.o.writeHead.call(res, 200, hdr); st.o.end.call(res, req.method === "HEAD" ? undefined : body); } finally { st.own = false; } // node merges writeHead(headers) through res.setHeader, so our own call must pass the guard
  return true;
}
function bb10eWrap(req, res, st) {
  var o = st.o = { writeHead: res.writeHead, write: res.write, end: res.end, setHeader: res.setHeader, removeHeader: res.removeHeader };
  res.setHeader = function () { if (st.fired && !st.own) return res; return o.setHeader.apply(res, arguments); };
  res.writeHead = function (status, a, b) {
    if (st.fired) return res;
    try {
      st.status = Number(status);
      var h = a && typeof a === "object" && !Array.isArray(a) ? a : b && typeof b === "object" && !Array.isArray(b) ? b : null, ct = "";
      if (h) Object.keys(h).forEach(function (k) { if (k.toLowerCase() === "content-type") ct = String(h[k]); });
      st.ct = ct || String((typeof res.getHeader === "function" && res.getHeader("content-type")) || "");
    } catch (e) {}
    return o.writeHead.apply(res, arguments);
  };
  var grab = function (c, enc) {
    try {
      if (c == null || typeof c === "function") return;
      var b = Buffer.isBuffer(c) ? c : Buffer.from(String(c), typeof enc === "string" ? enc : "utf8");
      st.bytes += b.length;
      if (st.bytes <= BB10E_BODY_MAX) st.chunks.push(b);
    } catch (e) { st.bytes = BB10E_BODY_MAX + 1; }
  };
  res.write = function (c, enc) { if (st.fired) return true; grab(c, enc); return o.write.apply(res, arguments); };
  res.end = function (c, enc) {
    if (st.fired) return res;
    grab(c, enc);
    var r = o.end.apply(res, arguments);
    try {
      if (!st.ended) {
        st.ended = true;
        if (req.method === "GET") bb10eStore(st.key, st.status || Number(res.statusCode) || 200, st.ct || String((typeof res.getHeader === "function" && res.getHeader("content-type")) || ""), st.chunks, st.bytes);
        if (st.done) st.done();
      }
    } catch (e) {}
    return r;
  };
}
var bb10eHandle0 = handle;
handle = async function (req, res) {
  var route = "", self = this, args = arguments;
  try {
    if ((req.method === "GET" || req.method === "HEAD") && typeof withTimeout === "function" && Number(BB10E_DEADLINE_MS) > 0) route = BB10E_ROUTES[new URL(req.url || "/", "http://localhost").pathname] || "";
  } catch (e) { route = ""; }
  if (!route) return bb10eHandle0.apply(self, args);
  var st = { fired: false, ended: false, chunks: [], bytes: 0, status: 0, ct: "", key: bb10eKey(req, route), done: null, fail: null, o: null };
  try { bb10eWrap(req, res, st); } catch (e) { return bb10eHandle0.apply(self, args); }
  var gate = new Promise(function (ok, bad) { st.done = ok; st.fail = bad; });
  try { if (typeof res.once === "function") res.once("close", function () { try { st.done(); } catch (e) {} }); } catch (e) {}
  var hp;
  try { hp = Promise.resolve(bb10eHandle0.apply(self, args)); } catch (e) { hp = Promise.reject(e); }
  hp.then(function () { if (st.ended || res.writableEnded) st.done(); }, function (e) { if (st.fired) console.warn("bb10e: late handler error after the deadline", e && e.message); else st.fail(e); });
  try {
    await withTimeout(gate, Number(BB10E_DEADLINE_MS), "bb10e route deadline", function () { st.timedOut = true; });
  } catch (e) {
    if (!st.timedOut) throw e;
    if (st.ended || res.headersSent || res.writableEnded || res.destroyed) return; // already answering (or the client left): let it finish
    try { bb10eFallback(req, res, st, route); console.warn("bb10e: deadline " + BB10E_DEADLINE_MS + "ms hit on " + route + (st.key && bb10eLast.has(st.key) ? " (served last good)" : " (served empty shape)")); }
    catch (e2) { st.fired = false; console.warn("bb10e: fallback failed", e2 && e2.message); }
  }
};
// the reset that caused the regime 404 keeps its state object; the reader also heals a missing one
try {
  var bb10eRow0 = bb8rRegimeRow;
  bb8rRegimeRow = function () {
    if (!bb8rReg || typeof bb8rReg !== "object") bb8rReg = { at: 0, row: null };
    return bb10eRow0.apply(this, arguments);
  };
  if (!bb8rReg || typeof bb8rReg !== "object") bb8rReg = { at: 0, row: null };
} catch (e) { console.warn("bb10e regime guard skipped", e && e.message); }
'''

ANCHOR = "// BB10D_JS_END"
FIX_OLD = "      bb8rReg = null;\n      row = (await bb10Withtimeout(bb10bEns0()"
FIX_NEW = "      bb8rReg = { at: 0, row: null }; // bb10e: keep the state object (null made bb8rRegimeRow() throw)\n      row = (await bb10Withtimeout(bb10bEns0()"
EDITS = [(FIX_OLD, FIX_NEW), (ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10E_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10e.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10e: {f} md5 {m0} lines {raw.count(b'\n')}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10d live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10e already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10e.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
    os.replace(tmp, f); print(f"bb10e: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
sys.exit(main())
