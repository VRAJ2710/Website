#!/usr/bin/env python3
"""patch_bb5b.py — CoinGecko 429 cooldown, listen before Stripe, regime-fit beta miss.

Chat63 is chat62 plus bb5. This patch is server.js only. It does not rewrite
app.js or index.html and it does not bump the client cache token. A chat64
client patch is shipping in parallel.

CoinGecko 429. The repeating log line is
"Unhandled rejection (kept alive): CoinGecko 429". coinGecko() throws
`new Error("CoinGecko " + status)` and calls pending.finally(...) without
catching the promise .finally() returns, so every 429 (including rt25s's
synthetic backoff response) is an unhandled rejection. rt29s is the live
proxy and already dedupes its own pull, then falls through to that original
function. There is no server interval polling CoinGecko. This patch wraps
fetch for api.coingecko.com: one in-flight promise per identical request,
and on 429 an in-memory host cooldown. Retry-After is used when it is
present (delta-seconds or HTTP-date), capped at 10 minutes. Otherwise the
wait doubles from 60s up to 10 minutes. During the cooldown the wrapper
does not call upstream. Callers receive the last good body with stale:true
and asOf, or {"error":"CoinGecko cooling down","unavailable":true} when
nothing is cached. One warn is printed when a cooldown starts, not once
per request. The .finally() promise is caught. No new interval is added.

Startup. .replit waits on TCP port 5000 (waitForPort) and does not name an
HTTP health path. The only health route in code was GET /api/health, and it
sits after redirects. server.listen ran only after initializeAuthDatabase()
and initializeStripe(). Connection refused is that gap: nothing is listening.
initializeStripe() (runMigrations, findOrCreateManagedWebhook, syncBackfill,
ensureDispatchPremiumPrice) is awaited before listen and logs
"Stripe membership billing unavailable:" plus the Stripe error — those errors
carry an HTTP status, often 500 — before the listen callback prints
"Dispatch Markets preview listening on PORT". This patch does not change
that function. The call moves into setImmediate after the listening line.
initializeAuthDatabase() stays awaited before listen: currentUser and the
editorial queries need databaseReady, and this patch does not change DB
schema code. Once the port is open, handle().catch writes
{"error":"Server error"} with status 500. GET / renders the public homepage
through publishedPageRoute, which awaits publishedEditorialRecord when the
database is ready; a SQL throw became that 500. The homepage now keeps the
static route if that read throws. GET/HEAD /health, /healthz and /api/health
answer 200 {"ok":true,"ready":true} before redirects and before warmups
finish. "/" stays the homepage.

Regime fit. When bb5LoadBeta returns null, the sensitivity row must not keep
the BB3_ROWS desk beta (MU is 1.62). The profile beta is cleared before
bb3Assemble, so the existing rule (beta above 1.5 while the mood is wary
takes 12 points) contributes 0. The row is then value null, contribution 0,
source "5y monthly beta, Yahoo", asOf null. The client already prints an
em dash for a null value (_rt53FitInputLine) and skips a null asOf, so no
client change is required.

Every new function name starts with bb5b. No new tables, no cron, no new
interval, no Stripe webhook edits, no secrets in log lines.

Usage: python3 patch_bb5b.py [--check] <dir with server.js>
"""
import hashlib, os, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "4b094d30cc5070c2ca44d7979452d648",
    "index.html": "0e595097e68bcf2f8c0c90395add2880",
    "server.js": "6b622ce0101aa9d7ca1e2846acd80f71",
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
    print("bb5b %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def read_bytes(path):
    if not os.path.isfile(path):
        return None
    return open(path, "rb").read()

def load_server():
    raw = read_bytes(SRV)
    if raw is None:
        die("server.js missing in %s" % D)
    return raw.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in raw, raw

v, vcrlf, srv_before = load_server()
app_before = read_bytes(APP)
idx_before = read_bytes(IDX)

digest = show("before", "server.js", srv_before)
expect = EXPECTED_MD5["server.js"]
if digest != expect:
    print("WARN md5 server.js: have %s expected %s (anchors still decide)" % (digest, expect))
for label, raw in (("app.js", app_before), ("index.html", idx_before)):
    if raw is None:
        print("bb5b before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, raw)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5b %s untouched" % label)

chat_n = None
if idx_before is not None:
    text = idx_before.decode("utf-8", "replace")
    import re
    hits = re.findall(r'app\.js\?v=chat(\d+)"', text)
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5b \u2500\u2500" in v:
    print("REFUSE: bb5b already applied")
    sys.exit(0)

miss = []
if "// \u2500\u2500 bb5 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5 ──")
if "async function bb5LoadBeta(ticker)" not in v:
    miss.append("server.js marker missing: async function bb5LoadBeta(ticker)")

anchors = [
    ("finally", """      pending.finally(() => {
        if (coinGeckoInflight.get(normalizedPath) === pending) coinGeckoInflight.delete(normalizedPath);
      });"""),
    ("stale-body", """    if (stale) { const asOf = coinGeckoLastGoodAt.get(normalizedPath) || stale.__asOf; return json(res, 200, stale, Object.assign({ "X-Dispatch-Data-Status": "stale" }, asOf ? { "X-Dispatch-Data-As-Of": asOf } : {})); }"""),
    ("rt29s-stale", """      if (g && Date.now() - g.at < MAXSTALE) return json(res, 200, g.data, hdr("stale", g.at));"""),
    ("published-page", """async function publishedPageRoute(route) {
  const record = databaseReady ? await publishedEditorialRecord("page", route.key) : null;"""),
    ("handle", """async function handle(req, res) {
  if (writeCanonicalRedirect(req, res)) return;"""),
    ("listen", """  await initializeAuthDatabase();
  await initializeStripe();
  server.listen(PORT, "0.0.0.0", () => {
    refreshMarketReferenceSwr().catch(() => {});
    console.log(`Dispatch Markets preview listening on ${PORT}`);
    void openBbRuntimePromise.then(openBbRuntime => {
      if (openBbRuntime.mode === "local" && !openBbRuntime.available) {
        console.error(`OpenBB local runtime unavailable: ${openBbRuntime.code || "UNAVAILABLE"}`);
      }
      if (process.env.DISPATCH_OPENBB_ENABLED !== "1") return;
      return openbbHealthCheck().then(health => {
        console.log(`OpenBB startup health: ${JSON.stringify({
          available: health.available === true,
          status: health.status,
          code: health.code,
        })}`);
      }).catch(() => {
        console.error("OpenBB startup health: unavailable");
      });
    });
    startAiReadinessMonitor();
    startOpenBbHealthMonitor();
  });"""),
]
for name, anchor in anchors:
    n = v.count(anchor)
    if n != 1:
        miss.append("server.js anchor %s matched %d times" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(anchors[0][1], """      pending.finally(() => {
        if (coinGeckoInflight.get(normalizedPath) === pending) coinGeckoInflight.delete(normalizedPath);
      }).catch(() => {});""", 1)
v = v.replace(anchors[1][1], """    if (stale) { const asOf = coinGeckoLastGoodAt.get(normalizedPath) || stale.__asOf; return json(res, 200, bb5bStamp(stale, asOf), Object.assign({ "X-Dispatch-Data-Status": "stale" }, asOf ? { "X-Dispatch-Data-As-Of": asOf } : {})); }""", 1)
v = v.replace(anchors[2][1], """      if (g && Date.now() - g.at < MAXSTALE) return json(res, 200, bb5bStamp(g.data, new Date(g.at).toISOString()), hdr("stale", g.at));""", 1)
v = v.replace(anchors[3][1], """async function publishedPageRoute(route) {
  let record = null;
  try { record = databaseReady ? await publishedEditorialRecord("page", route.key) : null; }
  catch (bb5bEditorialErr) { record = null; }""", 1)
v = v.replace(anchors[4][1], """async function handle(req, res) {
  if (bb5bEarly(req, res)) return;
  if (writeCanonicalRedirect(req, res)) return;""", 1)
v = v.replace(anchors[5][1], """  await initializeAuthDatabase();
  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Dispatch Markets preview listening on ${PORT}`);
    bb5bScheduleAfterListen({
      initializeStripe: initializeStripe,
      refreshMarketReferenceSwr: refreshMarketReferenceSwr,
      openBbRuntimePromise: openBbRuntimePromise,
      openbbHealthCheck: typeof openbbHealthCheck === "function" ? openbbHealthCheck : null,
      startAiReadinessMonitor: startAiReadinessMonitor,
      startOpenBbHealthMonitor: startOpenBbHealthMonitor
    });
  });""", 1)

BLOCK = r'''
// ── bb5b ── CoinGecko host cooldown, listen before Stripe, no desk beta when Yahoo misses.
// BB5B_JS
var bb5bCool = new Map();
var bb5bStep = 0;
var bb5bLastGood = new Map();
var bb5bCgInflight = new Map();
var bb5bBetaMiss = {};
function bb5bClock() {
  try {
    if (typeof globalThis.bb5bNow === "function") {
      var n = Number(globalThis.bb5bNow());
      if (isFinite(n)) return n;
    }
  } catch (e) {}
  return Date.now();
}
function bb5bHeader(headers, name) {
  if (!headers) return "";
  try {
    if (typeof headers.get === "function") return String(headers.get(name) || "");
  } catch (e) {}
  var want = String(name || "").toLowerCase();
  for (var k in headers) {
    if (Object.prototype.hasOwnProperty.call(headers, k) && String(k).toLowerCase() === want) return String(headers[k] == null ? "" : headers[k]);
  }
  return "";
}
function bb5bIsDelta(raw) {
  if (!raw) return false;
  var dot = false;
  for (var i = 0; i < raw.length; i++) {
    var c = raw.charAt(i);
    if (c === "." && !dot) { dot = true; continue; }
    if (c < "0" || c > "9") return false;
  }
  return true;
}
function bb5bRetryAfterMs(headers) {
  var raw = String(bb5bHeader(headers, "retry-after") || "").trim();
  if (!raw) return null;
  if (bb5bIsDelta(raw)) {
    var sec = Number(raw);
    if (!isFinite(sec) || sec < 0) return null;
    return Math.round(sec * 1000);
  }
  var when = Date.parse(raw);
  if (!isFinite(when)) return null;
  return Math.max(0, when - bb5bClock());
}
function bb5bCooldownMs(headers) {
  var ra = bb5bRetryAfterMs(headers);
  if (ra != null) return Math.min(600000, ra);
  var ms = Math.min(600000, 60000 * Math.pow(2, bb5bStep));
  if (bb5bStep < 8) bb5bStep += 1;
  return ms;
}
function bb5bCooling(host) {
  return bb5bClock() < (bb5bCool.get(host) || 0);
}
function bb5bCooldownRemaining(host) {
  return Math.max(0, (bb5bCool.get(host || "api.coingecko.com") || 0) - bb5bClock());
}
function bb5bArm(host, ms) {
  var now = bb5bClock();
  var prev = bb5bCool.get(host) || 0;
  var fresh = now >= prev;
  var until = now + ms;
  if (until > prev) bb5bCool.set(host, until);
  if (fresh) console.warn("bb5b coingecko cooldown ms " + ms);
}
function bb5bUrl(input) {
  try {
    if (typeof input === "string") return input;
    if (input && typeof input.url === "string") return input.url;
  } catch (e) {}
  return "";
}
function bb5bHost(url) {
  try { return new URL(String(url)).host; } catch (e) { return ""; }
}
function bb5bPathKey(url) {
  try {
    var u = new URL(String(url), "https://api.coingecko.com");
    var path = u.pathname || "";
    if (path.indexOf("/api/v3") === 0) path = path.slice("/api/v3".length);
    return path + (u.search || "");
  } catch (e) { return String(url || ""); }
}
function bb5bRemember(url, data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return;
  var copy = {};
  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) copy[k] = data[k];
  bb5bLastGood.set(bb5bPathKey(url), { data: copy, asOf: new Date(bb5bClock()).toISOString() });
  if (bb5bLastGood.size > 64) bb5bLastGood.delete(bb5bLastGood.keys().next().value);
}
function bb5bLookup(url) {
  var key = bb5bPathKey(url);
  var hit = bb5bLastGood.get(key);
  if (hit && hit.data) return hit;
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.get === "function") {
      var keys = [key, String(url || "")];
      for (var i = 0; i < keys.length; i++) {
        var body = coinGeckoLastGood.get(keys[i]);
        if (body && typeof body === "object") {
          var asOf = null;
          if (typeof coinGeckoLastGoodAt !== "undefined" && coinGeckoLastGoodAt && typeof coinGeckoLastGoodAt.get === "function") asOf = coinGeckoLastGoodAt.get(keys[i]) || null;
          return { data: body, asOf: asOf };
        }
      }
    }
  } catch (e) {}
  return null;
}
function bb5bStamp(body, asOf) {
  var when = asOf || null;
  if (!body || typeof body !== "object" || Array.isArray(body)) return { stale: true, asOf: when, data: body == null ? null : body };
  var out = {};
  for (var k in body) {
    if (Object.prototype.hasOwnProperty.call(body, k) && k !== "stale" && k !== "asOf") out[k] = body[k];
  }
  out.stale = true;
  out.asOf = when;
  return out;
}
function bb5bCachedOrError(url) {
  var hit = bb5bLookup(url);
  if (hit) return bb5bStamp(hit.data, hit.asOf);
  if (bb5bCooling("api.coingecko.com")) return { error: "CoinGecko cooling down", unavailable: true };
  return { error: "CoinGecko unavailable", unavailable: true };
}
function bb5bServe(res, body) {
  var headers = {};
  if (body && body.stale === true) {
    headers["X-Dispatch-Data-Status"] = "stale";
    if (body.asOf) headers["X-Dispatch-Data-As-Of"] = String(body.asOf);
  } else if (body && body.unavailable) headers["X-Dispatch-Data-Status"] = "unavailable";
  else headers["X-Dispatch-Data-Status"] = "fresh";
  if (typeof json === "function") return json(res, 200, body, headers);
  if (res && typeof res.writeHead === "function") {
    res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
    if (typeof res.end === "function") res.end(JSON.stringify(body));
  }
  return body;
}
function bb5bPathFromArgs(rawPath) {
  var path = String(rawPath || "");
  if (path.indexOf("http://") === 0 || path.indexOf("https://") === 0) return path;
  if (path.charAt(0) !== "/") path = "/" + path;
  return "https://api.coingecko.com/api/v3" + path;
}
async function bb5bQuote(url) {
  var host = bb5bHost(url);
  if (host === "api.coingecko.com" && bb5bCooling(host)) return bb5bCachedOrError(url);
  try {
    var res = await globalThis.fetch(url);
    if (!res || res.status === 429 || !res.ok) return bb5bCachedOrError(url);
    var data = await res.json();
    if (!data || typeof data !== "object") return bb5bCachedOrError(url);
    return data;
  } catch (e) {
    return bb5bCachedOrError(url);
  }
}
function bb5bFlightKey(input, init) {
  var method = "GET";
  try {
    if (init && init.method) method = String(init.method).toUpperCase();
    else if (input && input.method) method = String(input.method).toUpperCase();
  } catch (e) {}
  return method + " " + bb5bUrl(input);
}
function bb5bRelay(shared) {
  var relay = shared.then(function (snap) {
    return new Response(snap.text, { status: snap.status, headers: snap.headers });
  });
  relay.catch(function () {});
  return relay;
}
function bb5bInstall() {
  var orig = globalThis.fetch;
  if (typeof orig !== "function" || orig.bb5bCg) return;
  async function bb5bFetch(input, init) {
    var url = bb5bUrl(input);
    var host = bb5bHost(url);
    if (host !== "api.coingecko.com") return orig.call(orig, input, init);
    if (bb5bCooling(host)) {
      return new Response(JSON.stringify({ error: "CoinGecko cooling down", unavailable: true }), {
        status: 429,
        headers: { "content-type": "application/json", "x-bb5b-cooldown": "1" }
      });
    }
    var key = bb5bFlightKey(input, init);
    var existing = bb5bCgInflight.get(key);
    if (existing) return bb5bRelay(existing);
    var gate = {};
    var shared = new Promise(function (resolve, reject) { gate.resolve = resolve; gate.reject = reject; });
    bb5bCgInflight.set(key, shared);
    shared.then(function () {
      if (bb5bCgInflight.get(key) === shared) bb5bCgInflight.delete(key);
    }, function () {
      if (bb5bCgInflight.get(key) === shared) bb5bCgInflight.delete(key);
    });
    (async function bb5bPull() {
      try {
        var r = await orig.call(orig, input, init);
        var text = "";
        try { text = await r.text(); } catch (e) { text = ""; }
        var headers = {};
        try {
          if (r && r.headers && typeof r.headers.forEach === "function") r.headers.forEach(function (val, name) { headers[String(name).toLowerCase()] = val; });
        } catch (e2) {}
        var status = Number(r && r.status) || 0;
        if (status === 429) bb5bArm(host, bb5bCooldownMs(headers));
        else if (status >= 200 && status < 300) {
          bb5bStep = 0;
          bb5bCool.set(host, 0);
          try { bb5bRemember(url, JSON.parse(text)); } catch (e3) {}
        }
        gate.resolve({ status: status, headers: headers, text: text });
      } catch (err) {
        try { gate.reject(err); } catch (e4) {}
      }
    })().catch(function () {});
    return bb5bRelay(shared);
  }
  bb5bFetch.bb5bCg = true;
  globalThis.fetch = bb5bFetch;
}
function bb5bEarly(req, res) {
  if (!req || (req.method !== "GET" && req.method !== "HEAD")) return false;
  var path = "/";
  try { path = new URL(req.url || "/", "http://127.0.0.1").pathname; } catch (e) { return false; }
  if (path.length > 1 && path.charAt(path.length - 1) === "/") path = path.slice(0, -1);
  if (path !== "/health" && path !== "/healthz" && path !== "/api/health") return false;
  var payload = '{"ok":true,"ready":true}';
  try {
    res.writeHead(200, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Dispatch-Ready": "1"
    });
    res.end(req.method === "HEAD" ? undefined : payload);
  } catch (e) {}
  return true;
}
function bb5bScheduleAfterListen(deps) {
  deps = deps || {};
  setImmediate(function bb5bAfterListen() {
    Promise.resolve().then(function () {
      if (typeof deps.initializeStripe === "function") return deps.initializeStripe();
    }).catch(function () {});
    try {
      if (typeof deps.refreshMarketReferenceSwr === "function") {
        var refreshed = deps.refreshMarketReferenceSwr();
        if (refreshed && typeof refreshed.catch === "function") refreshed.catch(function () {});
      }
    } catch (e) {}
    try {
      var pending = deps.openBbRuntimePromise;
      if (pending && typeof pending.then === "function") {
        void pending.then(function (openBbRuntime) {
          if (openBbRuntime && openBbRuntime.mode === "local" && !openBbRuntime.available) {
            console.error("OpenBB local runtime unavailable: " + (openBbRuntime.code || "UNAVAILABLE"));
          }
          var openbbOn = false;
          try { openbbOn = typeof process !== "undefined" && process.env && process.env.DISPATCH_OPENBB_ENABLED === "1"; } catch (e2) { openbbOn = false; }
          if (!openbbOn || typeof deps.openbbHealthCheck !== "function") return;
          return deps.openbbHealthCheck().then(function (health) {
            console.log("OpenBB startup health: " + JSON.stringify({
              available: !!(health && health.available === true),
              status: health && health.status,
              code: health && health.code
            }));
          }).catch(function () { console.error("OpenBB startup health: unavailable"); });
        }).catch(function () {});
      }
    } catch (e3) {}
    try { if (typeof deps.startAiReadinessMonitor === "function") deps.startAiReadinessMonitor(); } catch (e4) {}
    try { if (typeof deps.startOpenBbHealthMonitor === "function") deps.startOpenBbHealthMonitor(); } catch (e5) {}
  });
}
function bb5bNoteBeta(ticker, hit) {
  var key = String(ticker || "").toUpperCase();
  if (!key) return;
  bb5bBetaMiss[key] = !(hit && hit.beta != null && isFinite(Number(hit.beta)));
}
function bb5bMissProfile(row) {
  row = row || { stance: "none", cat: "other", beta: null, known: false };
  return {
    stance: row.stance || "none",
    cat: row.cat || "other",
    beta: null,
    known: row.known === true,
    bb5bYahooMiss: true
  };
}
function bb5bBlankSensitivity(fit) {
  if (!fit || !Array.isArray(fit.inputs)) return fit;
  for (var i = 0; i < fit.inputs.length; i++) {
    var row = fit.inputs[i];
    if (!row || row.key !== "sensitivity") continue;
    row.value = null;
    row.contribution = 0;
    row.source = "5y monthly beta, Yahoo";
    row.asOf = null;
  }
  return fit;
}
function bb5bInstallFit() {
  if (typeof bb5LoadBeta === "function" && !bb5LoadBeta.bb5b) {
    var prevLoad = bb5LoadBeta;
    var wrappedLoad = async function bb5bLoadBeta(ticker) {
      var hit = null;
      try { hit = await prevLoad.apply(this, arguments); } catch (e) { hit = null; }
      bb5bNoteBeta(ticker, hit);
      return hit;
    };
    wrappedLoad.bb5b = true;
    bb5LoadBeta = wrappedLoad;
  }
  if (typeof bb3Profile === "function" && !bb3Profile.bb5b) {
    var prevProfile = bb3Profile;
    var wrappedProfile = function bb5bProfile(ticker) {
      var row = prevProfile.apply(this, arguments);
      var key = String(ticker || "").toUpperCase();
      if (bb5bBetaMiss[key] === true) return bb5bMissProfile(row);
      return row;
    };
    wrappedProfile.bb5b = true;
    bb3Profile = wrappedProfile;
  }
  if (typeof bb3Assemble === "function" && !bb3Assemble.bb5b) {
    var prevAssemble = bb3Assemble;
    var wrappedAssemble = function bb5bAssemble(ticker, profile) {
      var fit = prevAssemble.apply(this, arguments);
      if (profile && profile.bb5bYahooMiss === true) return bb5bBlankSensitivity(fit);
      return fit;
    };
    wrappedAssemble.bb5b = true;
    bb3Assemble = wrappedAssemble;
  }
}
try { bb5bInstall(); } catch (e) { console.warn("bb5b fetch hook skipped"); }
try { bb5bInstallFit(); } catch (e) { console.warn("bb5b fit hook skipped"); }
try {
  if (typeof coinGecko === "function" && !coinGecko.bb5b) {
    var bb5bCoinGeckoPrev = coinGecko;
    var bb5bCoinGeckoWrapped = async function bb5bCoinGecko(req, res, rawPath) {
      try {
        if (bb5bCooling("api.coingecko.com")) return bb5bServe(res, bb5bCachedOrError(bb5bPathFromArgs(rawPath)));
      } catch (e) {}
      return bb5bCoinGeckoPrev.apply(this, arguments);
    };
    bb5bCoinGeckoWrapped.bb5b = true;
    coinGecko = bb5bCoinGeckoWrapped;
  }
} catch (e) { console.warn("bb5b coingecko hook skipped"); }
// BB5B_JS_END
'''

import re
declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5b")]
if bad:
    die("bb5b block declares a non-bb5b function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5b block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or "findOrCreateManagedWebhook" in BLOCK:
    die("bb5b block has a forbidden declaration")

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
    print("bb5b app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5b index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5bbak"
try:
    open(bak, "wb").write(srv_before)
    open(SRV, "wb").write(after_srv)
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("node --check failed after write: " + r.stderr[:400])
    now_app, now_idx = read_bytes(APP), read_bytes(IDX)
    if app_before != now_app or idx_before != now_idx:
        raise RuntimeError("app.js or index.html changed")
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("APPLY bb5b coingecko cooldown, early listen, regime-fit beta miss")
