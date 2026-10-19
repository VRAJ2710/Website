#!/usr/bin/env python3
"""patch_bb8f.py — one shared SEC limiter: at most 10 sec.gov request starts in any rolling 1000 ms. Server.js only.
Stacked on bb8f (server md5 3fb9d02cb61081cec1d58484b1aef905). Does not rewrite app.js or index.html.
Every request to sec.gov / data.sec.gov (bb7/bb8 insiders: ticker map, submissions, Form 4 documents and their
retries; rt32 company_tickers and companyfacts; bb8c companyfacts; secText / rt52SecBig Form 4 and 13F paths) now
starts through one FIFO queue that keeps the start times of the last 10 requests. The start is stamped in the same
synchronous step that calls fetch. Waiters are woken by one setTimeout at a time (no setInterval). Interactive
requests are served before bulk insider fills. A waiter whose own AbortSignal fires (rt32Get 8 s, secText timeout)
or that waits over 30 s leaves the queue with an error, so the 8 s insiders and 7.5 s financials caps still return
partial results. User-Agent headers are unchanged. The old bb7Pace bucket is no longer used for sec.gov.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8f.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "3fb9d02cb61081cec1d58484b1aef905",
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
    print("bb8f %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8f before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8f %s untouched" % label)

if "// \u2500\u2500 bb8f \u2500\u2500" in v:
    print("REFUSE: bb8f already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8e marker", "// \u2500\u2500 bb8e \u2500\u2500"),
    ("bb8e end", "// BB8E_JS_END"),
    ("bb7FetchBuf", "async function bb7FetchBuf(url, pace) {"),
    ("bb7FetchImpl", "function bb7FetchImpl() {"),
    ("bb7Pace", "async function bb7Pace() {"),
    ("rt32Get", "function rt32Get(u, headers) { return fetch(u,"),
    ("rt32CikMap", "async function rt32CikMap() {"),
    ("secText", "async function secText(url, maxBytes = SEC_MAX_RESPONSE_BYTES) {"),
    ("rt52SecBig", "async function rt52SecBig(url) {"),
    ("bb8cSec", "async function bb8cSec(sym) {"),
    ("rt32 companyfacts", "https://data.sec.gov/api/xbrl/companyfacts/CIK${e.cik}.json"),
    ("bb8c companyfacts", "\"https://data.sec.gov/api/xbrl/companyfacts/CIK\" + e.cik"),
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
print("bb8f anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8f ── One shared SEC limiter: at most 10 sec.gov request starts in any rolling 1000 ms, for every path.
// BB8F_JS
// Every sec.gov / data.sec.gov request (bb7/bb8 insiders, rt32 company_tickers + companyfacts, bb8c companyfacts,
// secText/rt52SecBig 13F and Form 4 paths, retries) starts through bb8fRun. The start time is stamped in the same
// synchronous step that calls fetch, so the stamps are the real request starts. Waiters queue FIFO (interactive
// lane first, bulk insider fills second) and are woken by one setTimeout at a time; no interval. A queued request
// whose own AbortSignal fires (rt32Get 8 s, secText timeout) or that waits past BB8F_MAX_WAIT_MS leaves the queue
// with an error, so the 8 s insiders and 7.5 s financials races still return partial results on time.
// User-Agent headers are untouched: each caller keeps its own.
var BB8F_LIMIT = 10;
var BB8F_WINDOW_MS = 1000;
var BB8F_MAX_WAIT_MS = 30000;
// A start is stamped a hair before the fetch call itself; a 2 ms guard keeps the true starts inside the cap too.
var BB8F_GUARD_MS = 2;
var bb8fStarts = [];
var bb8fQueue = { high: [], low: [] };
var bb8fTimer = null;
var bb8fLane = "";
var bb8fStats = { started: 0, queued: 0, expired: 0, aborted: 0, maxWaitMs: 0, log: null };
function bb8fUrl(input) {
  try {
    if (typeof input === "string") return input;
    if (input && typeof input.href === "string") return input.href;
    if (input && typeof input.url === "string") return input.url;
    return String(input || "");
  } catch (e) { return ""; }
}
function bb8fIsSec(input) {
  return /^https?:\/\/(?:[a-z0-9-]+\.)*sec\.gov(?:[:\/?#]|$)/i.test(bb8fUrl(input));
}
function bb8fPrune(t) {
  while (bb8fStarts.length && t - bb8fStarts[0] >= BB8F_WINDOW_MS + BB8F_GUARD_MS) bb8fStarts.shift();
}
function bb8fPending() { return bb8fQueue.high.length + bb8fQueue.low.length; }
function bb8fNext() { return bb8fQueue.high.length ? bb8fQueue.high : bb8fQueue.low; }
function bb8fDrop(w, err, kind) {
  var list = bb8fQueue[w.lane];
  var i = list.indexOf(w);
  if (i >= 0) list.splice(i, 1);
  if (w.done) return;
  w.done = true;
  bb8fStats[kind]++;
  if (w.signal && w.onAbort) { try { w.signal.removeEventListener("abort", w.onAbort); } catch (e) {} }
  w.reject(err);
}
function bb8fBegin(w) {
  var t = Date.now();
  bb8fStarts.push(t);
  bb8fStats.started++;
  if (t - w.at > bb8fStats.maxWaitMs) bb8fStats.maxWaitMs = t - w.at;
  if (bb8fStats.log) bb8fStats.log.push(t);
  w.done = true;
  if (w.signal && w.onAbort) { try { w.signal.removeEventListener("abort", w.onAbort); } catch (e) {} }
  var p;
  try { p = w.fn(); } catch (e) { p = Promise.reject(e); }
  w.resolve(p);
}
function bb8fArm() {
  if (bb8fTimer || !bb8fPending()) return;
  var t = Date.now();
  bb8fPrune(t);
  var wait = bb8fStarts.length >= BB8F_LIMIT ? bb8fStarts[0] + BB8F_WINDOW_MS + BB8F_GUARD_MS - t : 0;
  var soonest = Infinity;
  ["high", "low"].forEach(function (k) { bb8fQueue[k].forEach(function (w) { if (w.deadline < soonest) soonest = w.deadline; }); });
  wait = Math.max(1, Math.min(wait, soonest - t));
  bb8fTimer = setTimeout(function () { bb8fTimer = null; bb8fPump(); }, wait);
}
function bb8fPump() {
  for (;;) {
    var t = Date.now();
    bb8fPrune(t);
    ["high", "low"].forEach(function (k) {
      bb8fQueue[k].slice().forEach(function (w) {
        if (w.deadline <= t) { var e = new Error("SEC queue wait over " + BB8F_MAX_WAIT_MS + " ms"); e.bb8fQueue = true; bb8fDrop(w, e, "expired"); }
      });
    });
    if (!bb8fPending()) return;
    if (bb8fStarts.length >= BB8F_LIMIT) { bb8fArm(); return; }
    bb8fBegin(bb8fNext().shift());
  }
}
// Run fn (which must start its request synchronously) once a slot in the rolling window is free.
function bb8fRun(fn, opts) {
  opts = opts || {};
  return new Promise(function (resolve, reject) {
    var t = Date.now();
    var lane = opts.lane === "low" ? "low" : "high";
    var w = { fn: fn, resolve: resolve, reject: reject, at: t, lane: lane, deadline: t + (Number(opts.maxWaitMs) > 0 ? Number(opts.maxWaitMs) : BB8F_MAX_WAIT_MS), signal: opts.signal || null, done: false };
    if (w.signal && w.signal.aborted) { bb8fStats.aborted++; reject(w.signal.reason || new Error("aborted")); return; }
    bb8fPrune(t);
    if (!bb8fPending() && bb8fStarts.length < BB8F_LIMIT) { bb8fBegin(w); return; }
    bb8fQueue[lane].push(w);
    bb8fStats.queued++;
    if (w.signal && typeof w.signal.addEventListener === "function") {
      w.onAbort = function () { bb8fDrop(w, w.signal.reason || new Error("aborted"), "aborted"); };
      w.signal.addEventListener("abort", w.onAbort, { once: true });
    }
    bb8fArm();
  });
}
function bb8fSnapshot() {
  return { limit: BB8F_LIMIT, windowMs: BB8F_WINDOW_MS, inWindow: bb8fStarts.length, queued: bb8fPending(), started: bb8fStats.started, expired: bb8fStats.expired, aborted: bb8fStats.aborted, maxWaitMs: bb8fStats.maxWaitMs };
}
try {
  // Process-wide: every sec.gov fetch (whatever helper built it) goes through the one queue.
  if (typeof globalThis.fetch === "function" && !globalThis.fetch.bb8fSec) {
    var bb8fFetch0 = globalThis.fetch;
    var bb8fFetch = function (input, init) {
      var self = this;
      if (!bb8fIsSec(input)) return bb8fFetch0.call(self, input, init);
      var lane = bb8fLane || "high";
      return bb8fRun(function () { return bb8fFetch0.call(self, input, init); }, { signal: init && init.signal, lane: lane });
    };
    bb8fFetch.bb8fSec = true;
    globalThis.fetch = bb8fFetch;
  }
  // bb7/bb8 insiders: the old bb7Pace bucket is retired for sec.gov; the shared queue paces instead.
  if (typeof bb7FetchBuf === "function") {
    var bb8fBuf0 = bb7FetchBuf;
    bb7FetchBuf = function (url, pace) {
      if (pace === false || !bb8fIsSec(url)) return bb8fBuf0.call(this, url, pace);
      var self = this;
      var impl = typeof bb7FetchImpl === "function" ? bb7FetchImpl() : null;
      if (impl && impl === globalThis.fetch && impl.bb8fSec) {
        bb8fLane = "low";
        try { return bb8fBuf0.call(self, url, false); } finally { bb8fLane = ""; }
      }
      return bb8fRun(function () { return bb8fBuf0.call(self, url, false); }, { lane: "low" });
    };
  }
} catch (e) { console.warn("bb8f hooks skipped", e && e.message); }
// BB8F_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8f")]
if bad:
    die("bb8f block declares a non-bb8f function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8f block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8f function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8f block has a forbidden declaration")

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
print("bb8f setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8fbak"
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
print("APPLY bb8f shared SEC limiter (10 request starts per rolling 1000 ms, all sec.gov paths)")
