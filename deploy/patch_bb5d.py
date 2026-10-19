#!/usr/bin/env python3
"""patch_bb5d.py — CoinGecko stale bodies, and the same Yahoo cadence for Asia/FX.

Chat63 plus bb5b plus bb5c. Server.js only. Does not rewrite app.js or
index.html and does not bump the client cache token.

CoinGecko. bb5bRemember ignored arrays, so /coins/markets never had a last
good body, and a cooldown that started before the first success answered
{error, unavailable}. Last-good bodies (including arrays) are kept per
normalised path. The existing coingecko-lastgood.json store is reused.
There is no new table. A cooldown timestamp saved in that store does not
block the first request after boot. A stale body keeps its original shape.
Headers carry x-dispatch-data-status: stale and the as-of time. A cold
cache still returns unavailable: there is no price to replay.

Yahoo. yahooQuote fired every symbol in one Promise.all, so a 40-symbol
chart burst dropped the names that Yahoo did not answer. Those misses sat
on an old print. Quotes now share one v7 batch when the existing crumb
helper is available, and the chart fallback runs six at a time so the tail
is fetched. exchangeDataDelayedBy becomes delayMin. A delayed print stays
status "delayed" until it is older than the 60s cadence plus that delay
plus a 2 minute margin. No price is invented.

Usage: python3 patch_bb5d.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "4b094d30cc5070c2ca44d7979452d648",
    "index.html": "0e595097e68bcf2f8c0c90395add2880",
    "server.js": "dc2ef95b2dce0439d1ec455cd1147d6c",
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
    print("bb5d %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb5d before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5d %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5d \u2500\u2500" in v:
    print("REFUSE: bb5d already applied")
    sys.exit(0)

OLD = """async function yahooQuote(symbols) {
  const out = {};
  await Promise.all((symbols || []).slice(0, 60).map(async symbol => {
    try {
      const d = await (await upstream(
        `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?${_yahooQuoteRange(symbol)}`,
      )).json();
      const meta = d?.chart?.result?.[0]?.meta;
      const price = Number(meta?.regularMarketPrice);
      if (!Number.isFinite(price) || price <= 0) return;
      const _ybL = _yahooPrevClose(meta, d?.chart?.result?.[0], symbol); const parsedPrev = Number(_ybL ? _ybL.prev : price);
      const prev = Number.isFinite(parsedPrev) && parsedPrev > 0 ? parsedPrev : price;
      out[symbol] = {
        p: price,
        c: prev ? ((price - prev) / prev) * 100 : 0,
        prev,
        change: price - prev,
        currency: meta.currency, basis: _ybL ? _ybL.basis : "none",
        exchange: meta.exchangeName,
        name: meta.longName || meta.shortName || symbol,
        ts: meta.regularMarketTime,
      };
    } catch {}
  }));
  return out;
}"""
NEW = """async function yahooQuote(symbols) {
  return bb5dYahooQuote(symbols);
}"""

miss = []
if "// \u2500\u2500 bb5c \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5c ──")
if v.count(OLD) != 1:
    miss.append("server.js anchor yahooQuote matched %d times" % v.count(OLD))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(OLD, NEW, 1)

BLOCK = r'''
// ── bb5d ── CoinGecko last-good bodies, Yahoo tail and exchange delay.
// BB5D_JS
var bb5dStore = new Map();
var bb5dMeta = null;
var bb5dCarry = { until: 0, boot: false };
var bb5dCadenceMs = 60000;
var bb5dMarginMs = 120000;
var bb5dCoolKey = "bb5d:cool";
function bb5dNow() {
  try {
    if (typeof globalThis.bb5dClock === "function") {
      var n = Number(globalThis.bb5dClock());
      if (isFinite(n)) return n;
    }
  } catch (e) {}
  return Date.now();
}
function bb5dKey(url) {
  try {
    var u = new URL(String(url || ""), "https://api.coingecko.com");
    var path = u.pathname || "";
    if (path.indexOf("/api/v3") === 0) path = path.slice("/api/v3".length);
    var parts = [];
    u.searchParams.forEach(function (val, name) { parts.push([name, val]); });
    parts.sort(function (a, b) {
      if (a[0] < b[0]) return -1;
      if (a[0] > b[0]) return 1;
      if (a[1] < b[1]) return -1;
      if (a[1] > b[1]) return 1;
      return 0;
    });
    var q = parts.map(function (p) { return encodeURIComponent(p[0]) + "=" + encodeURIComponent(p[1]); }).join("&");
    return path + (q ? "?" + q : "");
  } catch (e) { return String(url || ""); }
}
function bb5dCopy(body) {
  if (body == null || typeof body !== "object") return null;
  try { return JSON.parse(JSON.stringify(body)); } catch (e) { return null; }
}
function bb5dPut(key, body, asOf) {
  if (!key || key === bb5dCoolKey) return;
  var copy = bb5dCopy(body);
  if (!copy) return;
  bb5dStore.set(key, { body: copy, asOf: asOf || new Date(bb5dNow()).toISOString() });
  if (bb5dStore.size > 64) {
    var first = bb5dStore.keys().next().value;
    if (first === bb5dCoolKey) { bb5dStore.delete(first); first = bb5dStore.keys().next().value; }
    if (first) bb5dStore.delete(first);
  }
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.set === "function") {
      coinGeckoLastGood.set(key, copy);
      if (typeof coinGeckoLastGoodAt !== "undefined" && coinGeckoLastGoodAt) coinGeckoLastGoodAt.set(key, bb5dStore.get(key).asOf);
      if (typeof persistCoinGeckoLastGood === "function") persistCoinGeckoLastGood();
    }
  } catch (e2) {}
}
function bb5dParams(key) {
  var q = String(key || "");
  var i = q.indexOf("?");
  var path = i < 0 ? q : q.slice(0, i);
  var out = {};
  if (i >= 0) {
    q.slice(i + 1).split("&").forEach(function (pair) {
      if (!pair) return;
      var eq = pair.indexOf("=");
      var name = decodeURIComponent(eq < 0 ? pair : pair.slice(0, eq));
      var val = decodeURIComponent(eq < 0 ? "" : pair.slice(eq + 1));
      out[name] = val;
    });
  }
  return { path: path, q: out };
}
function bb5dList(raw) {
  return String(raw || "").split(",").map(function (s) { return s.trim().toLowerCase(); }).filter(Boolean);
}
function bb5dSibling(key) {
  var want = bb5dParams(key);
  if (want.path === "/simple/price") {
    var ids = bb5dList(want.q.ids), vs = bb5dList(want.q.vs_currencies);
    if (!ids.length || !vs.length) return null;
    var fields = [];
    vs.forEach(function (v) {
      fields.push(v);
      if (want.q.include_24hr_change === "true") fields.push(v + "_24h_change");
      if (want.q.include_market_cap === "true") fields.push(v + "_market_cap");
      if (want.q.include_24hr_vol === "true") fields.push(v + "_24h_vol");
    });
    if (want.q.include_last_updated_at === "true") fields.push("last_updated_at");
    var hit = null;
    bb5dStore.forEach(function (row, rowKey) {
      if (hit || rowKey === bb5dCoolKey) return;
      var got = bb5dParams(rowKey);
      if (got.path !== "/simple/price" || !row || !row.body || Array.isArray(row.body)) return;
      var ok = ids.every(function (id) {
        return row.body[id] && fields.every(function (fl) { return row.body[id][fl] != null; });
      });
      if (!ok) return;
      var out = {};
      ids.forEach(function (id) {
        out[id] = {};
        fields.forEach(function (fl) { out[id][fl] = row.body[id][fl]; });
      });
      hit = { body: out, asOf: row.asOf };
    });
    return hit;
  }
  if (want.path === "/coins/markets") {
    var ids2 = bb5dList(want.q.ids);
    if (!ids2.length) return null;
    var vs2 = String(want.q.vs_currency || "");
    var hit2 = null;
    bb5dStore.forEach(function (row, rowKey) {
      if (hit2 || rowKey === bb5dCoolKey) return;
      var got2 = bb5dParams(rowKey);
      if (got2.path !== "/coins/markets" || !row || !Array.isArray(row.body)) return;
      if (String(got2.q.vs_currency || "") !== vs2) return;
      var byId = {};
      row.body.forEach(function (coin) { if (coin && coin.id) byId[String(coin.id).toLowerCase()] = coin; });
      if (!ids2.every(function (id) { return byId[id]; })) return;
      hit2 = { body: ids2.map(function (id) { return byId[id]; }), asOf: row.asOf };
    });
    return hit2;
  }
  return null;
}
function bb5dFind(key) {
  var hit = bb5dStore.get(key);
  if (hit && hit.body != null && key !== bb5dCoolKey) return hit;
  var sib = bb5dSibling(key);
  if (sib) return sib;
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.get === "function") {
      var body = coinGeckoLastGood.get(key);
      if (body && typeof body === "object" && key !== bb5dCoolKey) {
        var asOf = null;
        if (typeof coinGeckoLastGoodAt !== "undefined" && coinGeckoLastGoodAt) asOf = coinGeckoLastGoodAt.get(key) || null;
        return { body: body, asOf: asOf };
      }
    }
  } catch (e) {}
  return null;
}
function bb5dStaleHeaders(asOf) {
  var headers = { "X-Dispatch-Data-Status": "stale" };
  if (asOf) {
    headers["X-Dispatch-Data-As-Of"] = String(asOf);
    headers["X-Dispatch-As-Of"] = String(asOf);
  }
  return headers;
}
function bb5dAnswer(key, cooling) {
  var hit = bb5dFind(key);
  if (hit) return { body: hit.body, headers: bb5dStaleHeaders(hit.asOf) };
  var err = cooling ? { error: "CoinGecko cooling down", unavailable: true } : { error: "CoinGecko unavailable", unavailable: true };
  return { body: err, headers: { "X-Dispatch-Data-Status": "unavailable" } };
}
function bb5dGate(now) {
  if (bb5dCarry.boot) { bb5dCarry.boot = false; return false; }
  return Number(bb5dCarry.until) > (now == null ? bb5dNow() : now);
}
function bb5dNoteCool(until) {
  bb5dCarry.until = Number(until) || 0;
  bb5dCarry.boot = false;
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.set === "function") {
      coinGeckoLastGood.set(bb5dCoolKey, { until: bb5dCarry.until });
      if (typeof persistCoinGeckoLastGood === "function") persistCoinGeckoLastGood();
    }
  } catch (e) {}
}
function bb5dLoadCarry() {
  var until = 0;
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.get === "function") {
      var row = coinGeckoLastGood.get(bb5dCoolKey);
      if (row && isFinite(Number(row.until))) until = Number(row.until);
    }
  } catch (e) {}
  bb5dStore.forEach(function (row, key) {
    if (key === bb5dCoolKey) return;
    if (row && row.body != null) bb5dStore.set(key, row);
  });
  try {
    if (typeof coinGeckoLastGood !== "undefined" && coinGeckoLastGood && typeof coinGeckoLastGood.forEach === "function") {
      coinGeckoLastGood.forEach(function (body, key) {
        if (!key || key === bb5dCoolKey || bb5dStore.has(key)) return;
        var asOf = null;
        try { if (typeof coinGeckoLastGoodAt !== "undefined" && coinGeckoLastGoodAt) asOf = coinGeckoLastGoodAt.get(key) || null; } catch (e2) {}
        if (body && typeof body === "object") bb5dStore.set(key, { body: body, asOf: asOf });
      });
    }
  } catch (e3) {}
  bb5dCarry.until = until;
  bb5dCarry.boot = until > bb5dNow();
}
function bb5dClass(ageMs, delayMin) {
  var delay = Number(delayMin);
  if (!isFinite(delay) || delay < 0) delay = 0;
  delay = Math.round(delay);
  var note = delay > 0 ? "delayed " + delay + "m by exchange" : "";
  if (ageMs == null || !isFinite(Number(ageMs))) return { delayMin: delay, status: delay > 0 ? "delayed" : "fresh", stale: false, note: note };
  var allowance = bb5dCadenceMs + delay * 60000 + bb5dMarginMs;
  if (Number(ageMs) > allowance) return { delayMin: delay, status: "stale", stale: true, note: "" };
  if (delay > 0) return { delayMin: delay, status: "delayed", stale: false, note: note };
  return { delayMin: 0, status: "fresh", stale: false, note: "" };
}
function bb5dAnnotate(q, delayMin) {
  if (!q || typeof q !== "object") return q;
  var out = {};
  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];
  var delay = delayMin != null ? delayMin : out.delayMin;
  var ts = Number(out.ts);
  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;
  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, bb5dNow() - tsMs) : null;
  var cls = bb5dClass(age, delay);
  out.delayMin = cls.delayMin;
  out.status = cls.status;
  out.stale = cls.stale;
  if (cls.note) out.note = cls.note;
  return out;
}
function bb5dFromRow(row) {
  if (!row || typeof row !== "object") return null;
  var price = Number(row.regularMarketPrice);
  if (!isFinite(price) || price <= 0) return null;
  var prevRaw = Number(row.regularMarketPreviousClose);
  var prev = isFinite(prevRaw) && prevRaw > 0 ? prevRaw : price;
  return bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: row.currency,
    basis: isFinite(prevRaw) && prevRaw > 0 ? "previous_close" : "none",
    exchange: row.fullExchangeName || row.exchange || "",
    name: row.longName || row.shortName || row.symbol || "",
    ts: row.regularMarketTime,
    delayMin: Number(row.exchangeDataDelayedBy) > 0 ? Number(row.exchangeDataDelayedBy) : 0
  }, Number(row.exchangeDataDelayedBy));
}
function bb5dWire(symbol) {
  var raw = String(symbol || "").trim();
  if (!raw) return null;
  var wire = raw;
  try {
    if (typeof BB3_ALIAS === "object" && BB3_ALIAS && BB3_ALIAS[raw.toUpperCase()]) wire = String(BB3_ALIAS[raw.toUpperCase()]);
  } catch (e) {}
  return { req: raw, wire: wire };
}
async function bb5dPool(items, limit, fn) {
  var out = new Array(items.length);
  var next = 0;
  var n = Math.max(1, Math.min(limit || 1, items.length || 1));
  async function bb5dWorker() {
    while (next < items.length) {
      var i = next++;
      try { out[i] = await fn(items[i], i); } catch (e) { out[i] = null; }
    }
  }
  var jobs = [];
  for (var w = 0; w < n; w++) jobs.push(bb5dWorker());
  await Promise.all(jobs);
  return out;
}
async function bb5dChartOne(symbol) {
  if (typeof upstream !== "function" || typeof _yahooQuoteRange !== "function" || typeof _yahooPrevClose !== "function") return null;
  var d = await (await upstream(
    "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(symbol) + "?" + _yahooQuoteRange(symbol)
  )).json();
  var meta = d && d.chart && d.chart.result && d.chart.result[0] && d.chart.result[0].meta;
  var price = Number(meta && meta.regularMarketPrice);
  if (!isFinite(price) || price <= 0) return null;
  var basis = _yahooPrevClose(meta, d.chart.result[0], symbol);
  var parsedPrev = Number(basis ? basis.prev : price);
  var prev = isFinite(parsedPrev) && parsedPrev > 0 ? parsedPrev : price;
  var delay = Number(meta && meta.exchangeDataDelayedBy);
  return bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: meta.currency,
    basis: basis ? basis.basis : "none",
    exchange: meta.exchangeName,
    name: meta.longName || meta.shortName || symbol,
    ts: meta.regularMarketTime,
    delayMin: isFinite(delay) && delay > 0 ? delay : 0
  }, delay);
}
async function bb5dBatch(wires) {
  if (!wires.length || typeof rt32Crumb !== "function" || typeof rt32Get !== "function") return null;
  try {
    var crumb = await rt32Crumb(false);
    if (!crumb) return null;
    var headers = { "User-Agent": "Mozilla/5.0" };
    try { if (typeof RT32 === "object" && RT32 && RT32.ck) headers.Cookie = RT32.ck; } catch (e) {}
    var r = await rt32Get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + encodeURIComponent(wires.join(",")) + "&crumb=" + encodeURIComponent(crumb), headers);
    if (!r || !r.ok) return null;
    var j = await r.json();
    var rows = (j && j.quoteResponse && j.quoteResponse.result) || [];
    if (!rows.length) return null;
    var out = {};
    rows.forEach(function (row) {
      if (!row || !row.symbol) return;
      var q = bb5dFromRow(row);
      if (q) out[String(row.symbol)] = q;
    });
    return out;
  } catch (e2) { return null; }
}
async function bb5dYahooQuote(symbols) {
  var pairs = [];
  (symbols || []).forEach(function (symbol) {
    if (pairs.length >= 60) return;
    var pair = bb5dWire(symbol);
    if (pair) pairs.push(pair);
  });
  var seen = {};
  var wires = [];
  pairs.forEach(function (pair) {
    if (seen[pair.wire]) return;
    seen[pair.wire] = 1;
    wires.push(pair.wire);
  });
  var merged = {};
  var batched = await bb5dBatch(wires);
  if (batched) {
    for (var k in batched) if (Object.prototype.hasOwnProperty.call(batched, k)) merged[k] = batched[k];
  }
  var missing = wires.filter(function (wire) { return !merged[wire]; });
  if (missing.length) {
    await bb5dPool(missing, 6, async function (wire) {
      try {
        var q = await bb5dChartOne(wire);
        if (q) merged[wire] = q;
      } catch (e) {}
    });
  }
  var out = {};
  pairs.forEach(function (pair) {
    var row = merged[pair.wire] || merged[pair.req];
    if (!row) return;
    out[pair.req] = row;
    if (pair.wire !== pair.req) out[pair.wire] = row;
  });
  return out;
}
function bb5dInstall() {
  bb5dLoadCarry();
  if (typeof bb5bRemember === "function") {
    bb5bRemember = function (url, data) { bb5dPut(bb5dKey(url), data); };
  }
  if (typeof bb5bStamp === "function") {
    bb5bStamp = function (body) { return body; };
  }
  if (typeof bb5bCachedOrError === "function") {
    bb5bCachedOrError = function (url) {
      var answer = bb5dAnswer(bb5dKey(url), typeof bb5bCooling === "function" ? bb5bCooling("api.coingecko.com") : false);
      bb5dMeta = answer.headers;
      return answer.body;
    };
  }
  if (typeof bb5bServe === "function") {
    bb5bServe = function (res, body) {
      var headers = bb5dMeta || {};
      bb5dMeta = null;
      if (!headers["X-Dispatch-Data-Status"]) {
        if (body && body.unavailable) headers = { "X-Dispatch-Data-Status": "unavailable" };
        else headers = { "X-Dispatch-Data-Status": "fresh" };
      }
      if (typeof json === "function") return json(res, 200, body, headers);
      return body;
    };
  }
  if (typeof bb5bCooling === "function" && !bb5bCooling.bb5d) {
    var prevCooling = bb5bCooling;
    var wrappedCooling = function bb5dCooling(host) {
      if (bb5dCarry.boot) {
        bb5dCarry.boot = false;
        try { if (typeof bb5bCool !== "undefined" && bb5bCool && typeof bb5bCool.set === "function") bb5bCool.set(host || "api.coingecko.com", 0); } catch (e) {}
        return false;
      }
      return prevCooling(host);
    };
    wrappedCooling.bb5d = true;
    bb5bCooling = wrappedCooling;
  }
  if (typeof bb5bArm === "function" && !bb5bArm.bb5d) {
    var prevArm = bb5bArm;
    var wrappedArm = function bb5dArm(host, ms) {
      var out = prevArm.apply(this, arguments);
      try {
        var until = (typeof bb5bCool !== "undefined" && bb5bCool && bb5bCool.get) ? bb5bCool.get(host || "api.coingecko.com") : 0;
        bb5dNoteCool(until);
      } catch (e) {}
      return out;
    };
    wrappedArm.bb5d = true;
    bb5bArm = wrappedArm;
  }
}
try { bb5dInstall(); } catch (e) { console.warn("bb5d install skipped"); }
// BB5D_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5d")]
if bad:
    die("bb5d block declares a non-bb5d function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5d block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb5d block has a forbidden declaration")

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
    print("bb5d app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5d index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5dbak"
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
print("APPLY bb5d coingecko last-good and yahoo delay")
