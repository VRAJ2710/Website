const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb3_fit.py");
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
const NOW = Date.parse("2026-10-17T21:15:00.000Z");
const QUOTE_TS = Date.parse("2026-10-17T20:00:00.000Z") / 1000;

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB3_FIT_JS\n([\s\S]*?)\n\/\/ BB3_FIT_JS_END/);
  assert.ok(m, "BB3_FIT_JS block missing from patch");
  const js = m[1];
  assert.equal(js.includes("/api/chat"), false);
  assert.equal(js.includes("sendChatMessage"), false);
  assert.equal(js.includes("user.tier"), false);
  assert.equal(js.includes("currentUser"), false);
  assert.equal(js.includes("hasPremiumAccess"), false);
  assert.equal(/CREATE TABLE|node-cron|\bcron\b/.test(js), false);
  return js;
}

function loadFit(extra) {
  const sandbox = Object.assign({
    console,
    URL,
    Map,
    Date,
    Math,
    JSON,
    Object,
    Number,
    String,
    isFinite,
    Promise,
    setTimeout,
    clearTimeout,
    handle: async function () { return "next"; },
    json(res, status, body, extraHeaders) {
      res.statusCode = status;
      res.body = body;
      res.headers = extraHeaders || {};
    },
    currentUser() { throw new Error("regime fit must not read the session"); },
  }, extra || {});
  sandbox.global = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(extractJs(), sandbox, { filename: "bb3fit.js" });
  sandbox.bb3Reset();
  return sandbox;
}

function moodRiskOff() {
  return { vix: 22.5, spx: -1.09, dxy: 101.81, oil: 93, btc: 0.4 };
}

function quote(price, change, ts) {
  return { p: price, c: change, prev: price, basis: "previous_close", ts: ts == null ? QUOTE_TS : ts, currency: "USD" };
}

function sumToScore(fit) {
  assert.equal(typeof fit.score, "number");
  const total = 50 + fit.inputs.reduce((sum, row) => sum + row.contribution, 0);
  assert.equal(total, fit.score);
}

function assertContract(fit) {
  assert.deepEqual(Object.keys(fit), ["ticker", "score", "reason", "label", "regime", "asOf", "method", "version", "inputs", "benchmark"]);
  assert.equal(fit.version, "bb3");
  assert.match(fit.asOf, ISO);
  assert.match(fit.method, /starts at 50/);
  assert.equal(/\b(buy|sell|accumulate)\b/i.test(JSON.stringify(fit)), false);
  assert.deepEqual(Object.keys(fit.benchmark), ["symbol", "value", "asOf"]);
  assert.equal(fit.benchmark.symbol, "SPY");
  assert.match(fit.benchmark.asOf, ISO);
  if (fit.score == null) {
    assert.equal(fit.label, null);
    assert.equal(fit.regime, null);
    assert.equal(fit.inputs.length, 0);
    assert.equal(typeof fit.reason, "string");
    assert.ok(fit.reason.length > 0);
    return;
  }
  assert.equal(fit.score, Math.round(fit.score));
  assert.ok(fit.score >= 0 && fit.score <= 100);
  assert.ok(["Tailwind", "Neutral", "Headwind"].includes(fit.label));
  assert.ok(["Risk-On", "Transition", "Risk-Off"].includes(fit.regime));
  assert.ok(fit.inputs.length >= 1);
  fit.inputs.forEach(row => {
    assert.deepEqual(Object.keys(row), ["key", "label", "value", "unit", "source", "asOf", "weight", "contribution"]);
    assert.match(row.asOf, ISO);
    assert.equal(typeof row.label, "string");
    assert.equal(/\b(beta|wtiC|liveChg|re\.score)\b/.test(row.label), false);
    assert.equal(typeof row.contribution, "number");
    assert.equal(typeof row.weight, "number");
  });
  sumToScore(fit);
}

test("the same inputs always produce the same MU score", () => {
  const s = loadFit();
  const mood = s.bb3Mood(moodRiskOff());
  assert.equal(mood.score, 22);
  assert.equal(mood.regime, "Risk-Off");
  const profile = s.bb3Profile("MU");
  assert.equal(profile.stance, "positive");
  assert.equal(profile.beta, 1.62);
  const a = s.bb3Assemble("MU", profile, mood, -2.4, -1.05, NOW, NOW, NOW);
  const b = s.bb3Assemble("MU", profile, mood, -2.4, -1.05, NOW, NOW, NOW);
  assert.deepEqual(a, b);
  assert.equal(a.score, 28);
  assert.equal(a.label, "Headwind");
  assert.equal(a.ticker, "MU");
  assert.equal(a.benchmark.value, -1.05);
  assertContract(a);
  const later = s.bb3Assemble("MU", profile, mood, -2.4, -1.05, NOW + 60000, NOW, NOW);
  assert.equal(later.score, a.score);
  assert.equal(later.label, a.label);
});

test("a missing price still scores, and adds nothing", () => {
  const s = loadFit();
  const mood = s.bb3Mood(moodRiskOff());
  const profile = s.bb3Profile("MU");
  const fit = s.bb3Assemble("MU", profile, mood, null, null, NOW, NOW, NOW);
  const again = s.bb3Assemble("MU", profile, mood, null, null, NOW, NOW, NOW);
  assert.deepEqual(fit, again);
  assert.equal(fit.score, 38);
  assert.equal(fit.label, "Headwind");
  const session = fit.inputs.find(row => row.key === "session");
  assert.equal(session.value, null);
  assert.equal(session.contribution, 0);
  assert.match(fit.reason, /not available/);
  assertContract(fit);
  const unknown = s.bb3Assemble("ZZZZ", s.bb3Profile("ZZZZ"), mood, null, null, NOW, NOW, NOW);
  const sensitivity = unknown.inputs.find(row => row.key === "sensitivity");
  assert.equal(sensitivity.value, null);
  assert.equal(sensitivity.contribution, 0);
  assert.equal(typeof unknown.score, "number");
  assert.deepEqual(unknown, s.bb3Assemble("ZZZZ", s.bb3Profile("ZZZZ"), mood, null, null, NOW, NOW, NOW));
});

test("falling WTI does not add Hormuz supply risk, and rising WTI does", () => {
  const s = loadFit();
  assert.equal(s.bb3OilPoints(-0.6), -1.2);
  assert.ok(s.bb3OilPoints(-0.6) <= 0);
  assert.equal(s.bb3OilPoints(-0.64), -1.3);
  assert.ok(s.bb3OilPoints(-0.64) < 0);
  assert.equal(s.bb3OilPoints(0.6), 1.2);
  assert.equal(s.bb3OilPoints(20), 12);
  assert.equal(s.bb3OilPoints(-20), -12);
  assert.equal(s.bb3OilPoints(null), null);
  const flat = s.bb3ChokeScore(82, 0, 19);
  const down = s.bb3ChokeScore(82, -0.6, 19);
  const up = s.bb3ChokeScore(82, 0.6, 19);
  assert.equal(flat, 82);
  assert.ok(down < flat);
  assert.ok(up > flat);
  assert.equal(down, 81);
  assert.equal(up, 83);
  const py = fs.readFileSync(PATCH, "utf8");
  assert.match(py, /Math\.round\(Math\.max\(-12, Math\.min\(12, wtiC \* 2\)\) \* 10\) \/ 10/);
  assert.match(py, /Math\.round\(Math\.max\(-12, Math\.min\(12, oilC \* 2\)\) \* 10\) \/ 10/);
  assert.match(py, /A rise in oil raises this supply-risk score; a fall lowers it/);
});

test("guests and admins receive the same cached payload", async () => {
  let calls = 0;
  const s = loadFit({
    yahooQuote: async (symbols) => {
      calls += 1;
      await new Promise(r => setTimeout(r, 20));
      const out = {};
      symbols.forEach(sym => {
        if (sym === "^VIX") out[sym] = quote(22.5, -1);
        else if (sym === "^GSPC") out[sym] = quote(5600, -1.09);
        else if (sym === "CL=F") out[sym] = quote(93, -0.6);
        else if (sym === "BTC-USD") out[sym] = quote(80000, 0.4);
        else if (sym === "SPY") out[sym] = quote(560, -1.05);
        else if (sym === "DX-Y.NYB") out[sym] = quote(101.5, -0.1);
        else if (sym === "MU") out[sym] = quote(180, -2.4);
      });
      return out;
    },
    fetchSyntheticDxy: async () => ({ p: 101.81, c: -0.19, ts: QUOTE_TS, source: "frankfurter-ecb" }),
  });
  const guest = { method: "GET", url: "/api/regime-fit?ticker=mu", headers: {} };
  const admin = { method: "GET", url: "/api/regime-fit?t=MU", headers: { cookie: "dispatch_session=admin", host: "thedispatch.uk" } };
  const rg = {}, ra = {};
  await Promise.all([s.bb3RegimeFit(guest, rg), s.bb3RegimeFit(admin, ra)]);
  assert.equal(rg.statusCode, 200);
  assert.equal(ra.statusCode, 200);
  assert.deepEqual(rg.body, ra.body);
  assert.equal(rg.body.regimeFit.ticker, "MU");
  assert.equal(rg.body.regimeFit.score, 28);
  assert.equal(rg.headers["Cache-Control"], "public, max-age=60");
  assert.equal(calls, 2);
  const again = {};
  const before = calls;
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: {} }, again);
  assert.deepEqual(again.body, rg.body);
  assert.equal(calls, before);
  assertContract(rg.body.regimeFit);
});

test("a missing session quote is identical for every caller", async () => {
  const s = loadFit({
    yahooQuote: async (symbols) => {
      const out = {};
      symbols.forEach(sym => {
        if (sym === "^VIX") out[sym] = quote(22.5, 0);
        else if (sym === "^GSPC") out[sym] = quote(5600, -1.09);
        else if (sym === "CL=F") out[sym] = quote(93, -0.6);
        else if (sym === "BTC-USD") out[sym] = quote(80000, 0.4);
        else if (sym === "SPY") out[sym] = quote(560, -1.05);
      });
      return out;
    },
    fetchSyntheticDxy: async () => ({ p: 101.81, ts: QUOTE_TS }),
  });
  const a = {}, b = {};
  await Promise.all([
    s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: {} }, a),
    s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: { cookie: "admin" } }, b),
  ]);
  assert.deepEqual(a.body, b.body);
  assert.equal(a.body.regimeFit.score, 38);
  const session = a.body.regimeFit.inputs.find(row => row.key === "session");
  assert.equal(session.value, null);
  assert.equal(session.contribution, 0);
  assertContract(a.body.regimeFit);
});

test("an unusable symbol returns one null score and does not guess", async () => {
  const s = loadFit({ yahooQuote: async () => { throw new Error("should not fetch"); } });
  const a = {}, b = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=not%20a%20symbol", headers: {} }, a);
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=", headers: { cookie: "admin" } }, b);
  assert.equal(a.body.regimeFit.score, null);
  assert.equal(b.body.regimeFit.score, null);
  assert.equal(a.body.regimeFit.inputs.length, 0);
  assert.equal(b.body.regimeFit.inputs.length, 0);
  assertContract(a.body.regimeFit);
  assertContract(b.body.regimeFit);
  const posted = {};
  await s.handle({ method: "POST", url: "/api/regime-fit?ticker=MU", headers: {} }, posted);
  assert.equal(posted.statusCode, 405);
  const passed = {};
  await s.handle({ method: "GET", url: "/api/yahoo-quote?symbols=MU", headers: {} }, passed);
  assert.equal(passed.statusCode, undefined);
});

test("the range row keeps the arithmetic identity", () => {
  const s = loadFit();
  assert.equal(s.bb3Finish(130).score, 100);
  assert.equal(s.bb3Finish(130).bounds, -30);
  assert.equal(s.bb3Finish(-4).score, 0);
  assert.equal(s.bb3Finish(-4).bounds, 4);
  assert.equal(s.bb3Finish(28).score, 28);
  assert.equal(s.bb3Finish(28).bounds, 0);
  const mood = s.bb3Mood({ vix: 22, spx: 0, dxy: 100, oil: 80, btc: 0 });
  assert.equal(mood.score, 50);
  assert.equal(s.bb3Mood({ vix: 22.01, spx: 0, dxy: 100, oil: 80, btc: 0 }).score, 38);
  const flat = s.bb3Assemble("MU", s.bb3Profile("MU"), s.bb3Mood(moodRiskOff()), -2, null, NOW, NOW, NOW);
  assert.equal(flat.score, 38);
  const down = s.bb3Assemble("MU", s.bb3Profile("MU"), s.bb3Mood(moodRiskOff()), -2.01, null, NOW, NOW, NOW);
  assert.equal(down.score, 28);
});

test("curl against the fit route returns one public JSON body", async () => {
  const s = loadFit({
    yahooQuote: async (symbols) => {
      const out = {};
      symbols.forEach(sym => {
        if (sym === "^VIX") out[sym] = quote(22.5, 0);
        else if (sym === "^GSPC") out[sym] = quote(5600, -1.09);
        else if (sym === "CL=F") out[sym] = quote(93, -0.6);
        else if (sym === "BTC-USD") out[sym] = quote(80000, 0.4);
        else if (sym === "SPY") out[sym] = quote(560, -1.05);
        else if (sym === "MU") out[sym] = quote(180, -2.4);
      });
      return out;
    },
    fetchSyntheticDxy: async () => ({ p: 101.81, ts: QUOTE_TS }),
  });
  const server = http.createServer((req, res) => {
    const fake = { statusCode: 200, headers: {}, setHeader(k, v) { this.headers[k] = v; } };
    s.json = function (out, status, body, extra) {
      out.statusCode = status;
      out.body = body;
      out.headers = Object.assign({}, extra || {});
    };
    s.bb3RegimeFit({ method: req.method, url: req.url, headers: req.headers }, fake).then(() => {
      res.writeHead(fake.statusCode, Object.assign({ "Content-Type": "application/json; charset=utf-8" }, fake.headers));
      res.end(JSON.stringify(fake.body));
    }).catch(err => {
      res.writeHead(500);
      res.end(String(err && err.message));
    });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  try {
    const urls = [
      "http://127.0.0.1:" + port + "/api/regime-fit?ticker=MU",
      "http://127.0.0.1:" + port + "/api/regime-fit?ticker=MU",
    ];
    const bodies = [];
    for (const url of urls) {
      const res = await fetch(url, { headers: url.endsWith("MU") ? {} : { cookie: "dispatch_session=admin" } });
      assert.equal(res.status, 200);
      assert.match(res.headers.get("cache-control") || "", /public, max-age=60/);
      bodies.push(await res.json());
    }
    const admin = await fetch("http://127.0.0.1:" + port + "/api/regime-fit?ticker=MU", { headers: { cookie: "dispatch_session=admin" } });
    bodies.push(await admin.json());
    assert.deepEqual(bodies[0], bodies[1]);
    assert.deepEqual(bodies[0], bodies[2]);
    assert.equal(bodies[0].regimeFit.score, 28);
    assert.equal(bodies[0].regimeFit.benchmark.symbol, "SPY");
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});

function macroQuote(symbols) {
  const out = {};
  symbols.forEach(sym => {
    if (sym === "^VIX") out[sym] = quote(22.5, 0);
    else if (sym === "^GSPC") out[sym] = quote(5600, -1.09);
    else if (sym === "CL=F") out[sym] = quote(93, -0.6);
    else if (sym === "BTC-USD") out[sym] = quote(80000, 0.4);
    else if (sym === "SPY") out[sym] = quote(560, -1.05);
    else if (sym === "MU") out[sym] = quote(180, -2.4);
    else out[sym] = quote(100, -0.2);
  });
  return out;
}

test("an unknown ticker returns a null score and does not fetch", async () => {
  let quotes = 0;
  let dollars = 0;
  const s = loadFit({
    yahooQuote: async () => { quotes += 1; throw new Error("unknown ticker must not fetch"); },
    fetchSyntheticDxy: async () => { dollars += 1; throw new Error("unknown ticker must not fetch"); },
  });
  const names = ["ZZZZ", "BTC-USD", "^GSPC", "NOTREAL1", "MU;DROP"];
  const bodies = [];
  for (const tk of names) {
    const out = {};
    await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=" + encodeURIComponent(tk), headers: { "x-forwarded-for": "198.51.100.10" } }, out);
    assert.equal(out.statusCode, 200);
    assert.equal(out.body.regimeFit.score, null);
    assert.equal(out.body.regimeFit.inputs.length, 0);
    bodies.push(out.body);
  }
  const again = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=ZZZZ", headers: { cookie: "dispatch_session=admin", "x-forwarded-for": "198.51.100.11" } }, again);
  assert.equal(again.body.regimeFit.score, null);
  assert.equal(again.body.regimeFit.inputs.length, 0);
  assert.equal(quotes, 0);
  assert.equal(dollars, 0);
  assert.equal(s.bb3CacheSize(), 0);
  assert.equal(s.bb3Known("MU"), true);
  assert.equal(s.bb3Known("ZZZZ"), false);
  assert.equal(s.bb3Known("BTC-USD"), false);
});

test("the per-ticker cache stays inside its LRU bound and the market pack is fetched once", async () => {
  const fetched = [];
  const s = loadFit({
    yahooQuote: async (symbols) => {
      fetched.push(symbols.slice());
      return macroQuote(symbols);
    },
    fetchSyntheticDxy: async () => ({ p: 101.81, ts: QUOTE_TS }),
    yahooRateLimiter: { allow() { return true; } },
  });
  const names = s.bb3Tickers();
  assert.ok(names.length > s.bb3FitMax());
  assert.equal(s.bb3FitMax(), 64);
  for (let i = 0; i < s.bb3FitMax() + 1; i++) {
    const out = {};
    await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=" + names[i], headers: {} }, out);
    assert.equal(out.statusCode, 200);
    assert.equal(typeof out.body.regimeFit.score, "number");
    assert.ok(s.bb3CacheSize() <= s.bb3FitMax());
  }
  assert.equal(s.bb3CacheSize(), s.bb3FitMax());
  assert.equal(s.bb3Hot(names[0]), false);
  assert.equal(s.bb3Hot(names[s.bb3FitMax()]), true);
  const packs = fetched.filter(symbols => symbols.indexOf("^VIX") !== -1);
  assert.equal(packs.length, 1);
  const before = fetched.length;
  const evicted = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=" + names[0], headers: {} }, evicted);
  assert.equal(typeof evicted.body.regimeFit.score, "number");
  assert.equal(fetched.length, before);
  assert.equal(fetched.filter(symbols => symbols.indexOf("^VIX") !== -1).length, 1);
  assert.equal(s.bb3CacheSize(), s.bb3FitMax());
  assert.equal(s.bb3Hot(names[0]), true);
  const hot = {};
  const mid = fetched.length;
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=" + names[s.bb3FitMax()], headers: { cookie: "dispatch_session=admin" } }, hot);
  assert.equal(fetched.length, mid);
  assert.equal(hot.body.regimeFit.ticker, names[s.bb3FitMax()]);
});

test("a limited miss returns the last score or a null score and does not fetch", async () => {
  let quotes = 0;
  let allows = 0;
  let open = true;
  const s = loadFit({
    yahooQuote: async (symbols) => {
      quotes += 1;
      return macroQuote(symbols);
    },
    fetchSyntheticDxy: async () => ({ p: 101.81, ts: QUOTE_TS }),
    yahooRateLimiter: {
      allow() { allows += 1; return open; },
    },
  });
  const first = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: { "x-forwarded-for": "203.0.113.8" } }, first);
  assert.equal(first.body.regimeFit.score, 28);
  const afterScore = quotes;
  const allowsAfterScore = allows;
  open = false;
  const guest = {};
  const admin = {};
  await Promise.all([
    s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: {} }, guest),
    s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: { cookie: "dispatch_session=admin", "x-forwarded-for": "203.0.113.9" } }, admin),
  ]);
  assert.deepEqual(guest.body, first.body);
  assert.deepEqual(admin.body, first.body);
  assert.equal(quotes, afterScore);
  assert.equal(allows, allowsAfterScore);
  const unseen = {};
  const unseenAdmin = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=AAPL", headers: { "x-forwarded-for": "203.0.113.8" } }, unseen);
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=AAPL", headers: { cookie: "dispatch_session=admin", "x-forwarded-for": "198.51.100.4" } }, unseenAdmin);
  assert.equal(unseen.body.regimeFit.score, null);
  assert.equal(unseen.body.regimeFit.inputs.length, 0);
  assert.deepEqual(unseen.body, unseenAdmin.body);
  assert.equal(unseen.headers["Cache-Control"], "no-store");
  assert.equal(quotes, afterScore);
  s.bb3DropHot();
  const stale = {};
  await s.bb3RegimeFit({ method: "GET", url: "/api/regime-fit?ticker=MU", headers: { "x-forwarded-for": "203.0.113.8" } }, stale);
  assert.equal(stale.body.regimeFit.score, 28);
  assert.deepEqual(stale.body.regimeFit, first.body.regimeFit);
  assert.equal(quotes, afterScore);
});
