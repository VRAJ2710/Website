const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5b.py");

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB5B_JS\n([\s\S]*?)\n\/\/ BB5B_JS_END/);
  assert.ok(m, "BB5B_JS block missing");
  const js = m[1];
  assert.equal(/CREATE TABLE|setInterval\(|node-cron|stripe\.webhooks|findOrCreateManagedWebhook/.test(js), false);
  assert.equal(src.includes('app.js?v=chat'), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.ok(names.length > 0);
  names.forEach(name => assert.equal(name.startsWith("bb5b"), true, name));
  const seen = new Set();
  names.forEach(name => {
    assert.equal(seen.has(name), false, name);
    seen.add(name);
  });
  return js;
}

function load(extra) {
  const context = {
    console,
    Date,
    Math,
    Number,
    String,
    Object,
    Array,
    JSON,
    Promise,
    Map,
    URL,
    Response,
    Uint8Array,
    isFinite,
    setImmediate,
    setTimeout,
    clearTimeout,
    process: { env: {} },
    ...(extra || {})
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(extractJs(), context, { filename: "bb5b.js" });
  return context;
}

function cgFetch(state) {
  return async function (url) {
    const u = String(url);
    if (u.indexOf("api.coingecko.com") < 0) {
      state.other += 1;
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
    }
    state.calls += 1;
    const headers = { "content-type": "application/json" };
    if (state.retryAfter != null) headers["retry-after"] = String(state.retryAfter);
    if (state.mode === "throw") throw new Error("CoinGecko 429");
    if (state.mode === "ok") {
      return new Response(JSON.stringify({ bitcoin: { usd: state.price == null ? 1 : state.price } }), { status: 200, headers });
    }
    return new Response(JSON.stringify({ status: { error_code: 429 } }), { status: 429, headers });
  };
}

test("a 429 burst is one upstream call, then stale data, with no unhandledRejection", async () => {
  const seen = [];
  const on = reason => seen.push(reason);
  process.on("unhandledRejection", on);
  const warns = [];
  const state = { calls: 0, other: 0, mode: "429", retryAfter: null };
  try {
    const s = load({
      console: { log() {}, error() {}, warn(...a) { warns.push(a.join(" ")); } },
      fetch: cgFetch(state)
    });
    const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";
    s.bb5bRemember(url, { bitcoin: { usd: 64000 } });
    const rows = await Promise.all([0, 1, 2, 3, 4, 5, 6, 7].map(() => s.bb5bQuote(url)));
    assert.equal(state.calls, 1);
    rows.forEach(row => {
      assert.equal(row.stale, true);
      assert.equal(row.bitcoin.usd, 64000);
      assert.equal(typeof row.asOf, "string");
      assert.ok(row.asOf);
    });
    const again = await s.bb5bQuote(url);
    assert.equal(state.calls, 1);
    assert.equal(again.stale, true);
    const miss = await s.bb5bQuote("https://api.coingecko.com/api/v3/simple/price?ids=missing&vs_currencies=usd");
    assert.equal(state.calls, 1);
    assert.equal(JSON.stringify(miss), JSON.stringify({ error: "CoinGecko cooling down", unavailable: true }));
    assert.equal(warns.length, 1);
    assert.match(warns[0], /^bb5b coingecko cooldown ms /);
    assert.equal(/coingecko\.com|api_key|secret|token/i.test(warns[0]), false);
    await s.fetch("https://example.com/quote");
    await s.fetch("https://example.com/quote");
    assert.equal(state.other, 2);
    assert.equal(state.calls, 1);
    await new Promise(r => setTimeout(r, 30));
    assert.equal(seen.length, 0);
  } finally {
    process.removeListener("unhandledRejection", on);
  }
});

test("a rejected CoinGecko fetch does not emit unhandledRejection", async () => {
  const seen = [];
  const on = reason => seen.push(reason);
  process.on("unhandledRejection", on);
  try {
    const state = { calls: 0, other: 0, mode: "throw", retryAfter: null };
    const s = load({
      console: { log() {}, error() {}, warn() {} },
      fetch: cgFetch(state)
    });
    const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";
    s.bb5bRemember(url, { bitcoin: { usd: 10 } });
    const row = await s.bb5bQuote(url);
    assert.equal(row.stale, true);
    assert.equal(row.bitcoin.usd, 10);
    await new Promise(r => setTimeout(r, 30));
    assert.equal(seen.length, 0);
  } finally {
    process.removeListener("unhandledRejection", on);
  }
});

test("Retry-After is honoured, then a later 429 backs off from 60s to 10 minutes", async () => {
  let clock = 1000000;
  const warns = [];
  const state = { calls: 0, other: 0, mode: "429", retryAfter: "5" };
  const s = load({
    console: { log() {}, error() {}, warn(...a) { warns.push(a.join(" ")); } },
    fetch: cgFetch(state)
  });
  s.bb5bNow = () => clock;
  const url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";
  s.bb5bRemember(url, { bitcoin: { usd: 64000 } });
  const first = await s.bb5bQuote(url);
  assert.equal(state.calls, 1);
  assert.equal(first.stale, true);
  assert.equal(s.bb5bCooldownRemaining(), 5000);
  assert.match(warns[0], /cooldown ms 5000$/);
  clock += 4999;
  const held = await s.bb5bQuote(url);
  assert.equal(state.calls, 1);
  assert.equal(held.stale, true);
  clock += 1;
  state.mode = "ok";
  state.retryAfter = null;
  state.price = 65000;
  const fresh = await s.bb5bQuote(url);
  assert.equal(state.calls, 2);
  assert.equal(fresh.stale, undefined);
  assert.equal(fresh.bitcoin.usd, 65000);
  assert.equal(s.bb5bCooldownRemaining(), 0);

  state.mode = "429";
  let prev = 0;
  for (let i = 0; i < 6; i++) {
    clock += prev + 1;
    await s.bb5bQuote(url);
    const left = s.bb5bCooldownRemaining();
    assert.equal(left, Math.min(600000, 60000 * 2 ** i));
    prev = left;
  }
  assert.equal(prev, 600000);
  assert.equal(state.calls, 8);
  clock += 600000;
  state.mode = "ok";
  const recovered = await s.bb5bQuote(url);
  assert.equal(recovered.bitcoin.usd, 65000);
  assert.equal(recovered.stale, undefined);
  assert.equal(state.calls, 9);
});

test("listen is logged before Stripe and /health is 200 while warmup is still running", async () => {
  const s = load({ fetch: async () => new Response("{}", { status: 200 }) });
  const order = [];
  const t0 = Date.now();
  await new Promise(r => setTimeout(r, 20));
  order.push("db +" + (Date.now() - t0));
  const res = { writeHead(code, headers) { this.status = code; this.headers = headers; }, end(body) { this.body = body; } };
  assert.equal(s.bb5bEarly({ method: "GET", url: "/" }, res), false);
  assert.equal(s.bb5bEarly({ method: "GET", url: "/health" }, res), true);
  assert.equal(res.status, 200);
  assert.deepEqual(JSON.parse(res.body), { ok: true, ready: true });
  const api = { writeHead(code) { this.status = code; }, end(body) { this.body = body; } };
  assert.equal(s.bb5bEarly({ method: "HEAD", url: "/api/health" }, api), true);
  assert.equal(api.status, 200);
  order.push("listen +" + (Date.now() - t0));
  let stripeStarted = false;
  s.bb5bScheduleAfterListen({
    initializeStripe() {
      stripeStarted = true;
      order.push("stripe-start +" + (Date.now() - t0));
      return new Promise(resolve => setTimeout(() => {
        order.push("stripe-end +" + (Date.now() - t0));
        resolve();
      }, 40));
    },
    refreshMarketReferenceSwr() {
      order.push("refresh +" + (Date.now() - t0));
      return Promise.resolve();
    },
    startAiReadinessMonitor() { order.push("ai +" + (Date.now() - t0)); },
    startOpenBbHealthMonitor() { order.push("openbb +" + (Date.now() - t0)); }
  });
  assert.equal(stripeStarted, false);
  const during = { writeHead(code) { this.status = code; }, end(body) { this.body = body; } };
  assert.equal(s.bb5bEarly({ method: "GET", url: "/healthz" }, during), true);
  assert.equal(during.status, 200);
  await new Promise(r => setImmediate(r));
  assert.equal(stripeStarted, true);
  assert.equal(order.some(line => line.startsWith("stripe-end")), false);
  await new Promise(r => setTimeout(r, 60));
  assert.equal(order.some(line => line.startsWith("stripe-end")), true);
  const beforeListen = Date.now();
  await new Promise(r => setTimeout(r, 20));
  await new Promise(r => setTimeout(r, 40));
  const beforeMs = Date.now() - beforeListen;
  console.log("startup before (stub delays, Stripe not started): db awaited, then Stripe awaited (" + beforeMs + "ms) , then listen. The listening line cannot print until both finish.");
  console.log("startup after: " + order.join(" | "));
  assert.ok(order[0].startsWith("db"));
  assert.ok(order[1].startsWith("listen"));
  assert.ok(order.some(line => line.startsWith("stripe-start")));
});

function fitWorld(fail) {
  const mem = {};
  return {
    bb5LoadBeta: async ticker => {
      if (fail) return null;
      const hit = { beta: 2.23, asOf: "2026-10-19T00:00:00.000Z", at: Date.now() };
      mem[String(ticker || "").toUpperCase()] = hit;
      return hit;
    },
    bb3Profile: ticker => {
      const key = String(ticker || "").toUpperCase();
      const desk = { stance: "positive", cat: "other", beta: 1.62, known: true };
      const hit = mem[key];
      if (hit && hit.beta != null) return { stance: desk.stance, cat: desk.cat, beta: hit.beta, known: true, bb5Yahoo: true, bb5AsOf: hit.asOf };
      return desk;
    },
    bb3Assemble: (ticker, profile) => {
      const beta = profile && profile.beta != null && Number.isFinite(Number(profile.beta)) ? Number(profile.beta) : null;
      const sensC = beta != null && beta > 1.5 ? -12 : 0;
      return {
        ticker,
        score: 50 + sensC,
        inputs: [
          { key: "desk", value: "Positive", contribution: 0, source: "Dispatch desk reference", asOf: "2026-10-01T00:00:00.000Z" },
          { key: "sensitivity", value: beta, contribution: sensC, source: "Dispatch desk reference", asOf: "2026-10-01T00:00:00.000Z", unit: "times the market" }
        ]
      };
    }
  };
}

async function fitOf(fail, ticker) {
  const s = load(Object.assign({ fetch: async () => new Response("{}", { status: 200 }), console: { log() {}, error() {}, warn() {} } }, fitWorld(fail)));
  await s.bb5LoadBeta(ticker);
  const profile = s.bb3Profile(ticker);
  return { profile, fit: s.bb3Assemble(ticker, profile) };
}

test("a failed Yahoo beta does not keep the desk beta on sensitivity", async () => {
  const missed = await fitOf(true, "MU");
  assert.equal(missed.profile.beta, null);
  assert.equal(missed.profile.bb5bYahooMiss, true);
  const row = missed.fit.inputs.find(item => item.key === "sensitivity");
  assert.equal(row.value, null);
  assert.equal(row.contribution, 0);
  assert.equal(row.source, "5y monthly beta, Yahoo");
  assert.equal(row.asOf, null);
  assert.equal(missed.fit.score, 50);
  assert.equal(JSON.stringify(row).includes("1.62"), false);
  const desk = missed.fit.inputs.find(item => item.key === "desk");
  assert.equal(desk.value, "Positive");
  assert.equal(desk.source, "Dispatch desk reference");

  const hit = await fitOf(false, "MU");
  const good = hit.fit.inputs.find(item => item.key === "sensitivity");
  assert.equal(good.value, 2.23);
  assert.equal(good.contribution, -12);
  assert.equal(hit.fit.score, 38);
  assert.equal(good.asOf, "2026-10-01T00:00:00.000Z");
});
