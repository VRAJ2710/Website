const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb2.py");

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB2_JS\n([\s\S]*?)\n\/\/ BB2_JS_END/);
  assert.ok(m, "BB2_JS block missing from patch");
  const js = m[1];
  assert.equal(js.includes("setInterval("), false);
  assert.equal(/node-cron|CREATE TABLE|\bcron\b/.test(js), false);
  return js;
}

function loadBb2(env, fetchImpl) {
  const sandbox = {
    console,
    require,
    Buffer,
    URL,
    URLSearchParams,
    TextDecoder,
    TextEncoder,
    Intl,
    setTimeout,
    clearTimeout,
    AbortSignal,
    Map,
    Set,
    Promise,
    Date,
    Math,
    JSON,
    RegExp,
    Error,
    encodeURIComponent,
    decodeURIComponent,
    process: { env: Object.assign({}, env || {}) },
    currentUser: async () => ({ id: "u", tier: "premium" }),
    json(res, status, body) { res.statusCode = status; res._json = body; },
    handle: async () => {},
    generateAi: async () => ({ text: "", model: "stub" }),
    fetch: fetchImpl || (async () => { throw new Error("unexpected fetch"); }),
  };
  sandbox.global = sandbox;
  sandbox.globalThis = sandbox;
  sandbox.readBody = async () => sandbox._body || {};
  sandbox._body = { messages: [], sources: [] };
  vm.createContext(sandbox);
  vm.runInContext(extractJs(), sandbox, { filename: "bb2.js" });
  return sandbox;
}

const MARKET_MS = Date.parse("2026-10-16T20:00:00.000Z");
const ASOF = "2026-10-16 20:00 UTC";
function sampleVals() {
  return {
    MU: { trailing: 11.82349, forward: 4.247783, price: 878.84, marketMs: MARKET_MS, asOf: ASOF },
    WDC: { trailing: 12.332838, forward: 9.97343, price: 332, marketMs: MARKET_MS, asOf: ASOF },
    AVGO: { trailing: 41.98595, forward: 16.948542, price: 328.75, marketMs: MARKET_MS, asOf: ASOF },
    AMD: { trailing: 134.88521, forward: 33.560158, price: 528.75, marketMs: MARKET_MS, asOf: ASOF },
    NVDA: { trailing: 27.070797, forward: 13.454941, price: 214.13, marketMs: MARKET_MS, asOf: ASOF },
    INTC: { trailing: null, forward: 42.685913, price: 89.85, marketMs: MARKET_MS, asOf: ASOF },
  };
}
function seed(sandbox, at) {
  const when = at || Date.now();
  Object.entries(sampleVals()).forEach(([sym, v]) => sandbox.bb2Mem.vals.set(sym, { at: when, v }));
}

test("MU 11.8x is lower than WDC 12.3x, and trailing is not compared with forward", () => {
  const s = loadBb2();
  const built = s.bb2BuildFacts("MU", sampleVals());
  const trailing = built.facts.find(f => f.a === "MU" && f.b === "WDC" && f.basis === "trailing");
  const forward = built.facts.find(f => f.a === "MU" && f.b === "WDC" && f.basis === "forward");
  assert.equal(trailing.dir, "lower");
  assert.equal(trailing.va, 11.8);
  assert.equal(trailing.vb, 12.3);
  assert.equal(trailing.abs, 0.5);
  assert.equal(trailing.pct, 4.1);
  assert.match(trailing.sentence, /trailing P\/E \(TTM\) 11\.8x is lower than WDC trailing P\/E \(TTM\) 12\.3x by 0\.5x \(4\.1%\)/);
  assert.equal(/higher/.test(trailing.sentence), false);
  assert.match(forward.sentence, /forward P\/E/);
  assert.equal(/trailing/.test(forward.sentence), false);
  assert.match(forward.label, /^forward P\/E$/);
  const avgo = built.rows.find(r => r.startsWith("AVGO:"));
  const amd = built.rows.find(r => r.startsWith("AMD:"));
  assert.match(avgo, /trailing P\/E \(TTM\) 42\.0x \| forward P\/E 16\.9x/);
  assert.match(amd, /trailing P\/E \(TTM\) 134\.9x \| forward P\/E 33\.6x/);
  const missing = built.facts.find(f => f.b === "INTC" && f.basis === "trailing");
  assert.equal(missing.dir, "missing");
  assert.match(missing.sentence, /INTC trailing P\/E \(TTM\) was not reported/);
  const bad = "MU's trailing P/E (TTM) 11.8x is slightly higher than WDC's trailing P/E (TTM) 12.3x.";
  const fixed = s.bb2FixSentence(bad, built.facts);
  assert.match(fixed, /lower than WDC/);
  assert.equal(/higher/.test(fixed), false);
  assert.match(fixed, /trailing P\/E \(TTM\)/);
  const cross = s.bb2FixSentence("MU trailing P/E (TTM) 11.8x is higher than its forward P/E 4.2x.", built.facts);
  assert.match(cross, /different bases and are not compared/);
  assert.equal(/higher/.test(cross), false);
  const sunday = Date.parse("2026-10-18T21:00:00.000Z");
  assert.equal(s.bb2LastCloseMs(sunday), MARKET_MS);
  assert.equal(s.bb2Fresh({ at: sunday - 60e3, v: sampleVals().MU }, sunday), true);
  assert.equal(s.bb2Fresh({ at: sunday - 30 * 3600e3, v: sampleVals().MU }, sunday), false);
});

test("streamed answer leads with the corrected comparison in well under 3s and cites Yahoo", async () => {
  const calls = [];
  const s = loadBb2({
    AI_INTEGRATIONS_OPENAI_BASE_URL: "http://openai.test/v1",
    AI_INTEGRATIONS_OPENAI_API_KEY: "test-key",
  }, async (url) => {
    const href = String(url);
    calls.push(href);
    if (/x\.ai|grok/i.test(href)) throw new Error("xAI must not be called");
    await new Promise(r => setTimeout(r, 200));
    const payload = 'data: {"choices":[{"delta":{"content":"MU\'s trailing P/E (TTM) 11.8x is slightly higher than WDC\'s trailing P/E (TTM) 12.3x. Demand is the driver."}}]}\n\ndata: [DONE]\n\n';
    let sent = false;
    return {
      ok: true,
      status: 200,
      body: { getReader: () => ({ read: async () => (sent ? { done: true } : (sent = true, { done: false, value: Buffer.from(payload) })) }) },
    };
  });
  seed(s);
  s._body = {
    messages: [{ role: "user", content: "How do MU's peers compare on P/E?" }],
    sources: [{ name: "Reuters", link: "https://www.reuters.com/markets/mu", asOf: "2026-10-18T12:00:00Z", detail: "MU headline" }],
  };
  const writes = [];
  const t0 = Date.now();
  const res = {
    writeHead(status, headers) { this.statusCode = status; this.headers = headers; },
    write(chunk) { writes.push({ at: Date.now() - t0, chunk: String(chunk) }); return true; },
    end() { this.ended = true; },
    socket: { setNoDelay() {} },
  };
  await s.bb2StreamChat({ method: "POST", url: "/api/chat", headers: { host: "localhost", accept: "text/event-stream", "x-dispatch-stream": "1" } }, res);
  assert.equal(res.statusCode, 200);
  assert.match(res.headers["Content-Type"], /text\/event-stream/);
  assert.ok(writes.length > 1);
  const first = JSON.parse(writes[0].chunk.replace(/^data: /, "").trim());
  assert.ok(writes[0].at < 3000, "ttft " + writes[0].at);
  assert.ok(writes[0].at < 150, "comparison block should flush before the delayed model, ttft " + writes[0].at);
  assert.match(first.t, /trailing P\/E \(TTM\) 11\.8x is lower than WDC trailing P\/E \(TTM\) 12\.3x/);
  assert.equal(/higher than WDC/.test(first.t), false);
  const all = writes.map(w => w.chunk).join("\n");
  assert.equal(/higher than WDC/.test(all), false);
  assert.match(all, /Demand is the driver/);
  assert.match(all, /Yahoo Finance/);
  assert.match(all, /https:\/\/finance\.yahoo\.com\/quote\/MU\/key-statistics\//);
  assert.match(all, /as of 2026-10-16 20:00 UTC/);
  assert.match(all, /trailing P\/E \(TTM\) and forward P\/E/);
  assert.match(all, /Reuters/);
  assert.equal(calls.some(u => /x\.ai|grok/i.test(u)), false);
  assert.ok(calls.some(u => /openai\.test\/v1\/chat\/completions/.test(u)));
  const done = writes.map(w => JSON.parse(w.chunk.replace(/^data: /, "").trim())).filter(e => e.done).pop();
  assert.match(done.reply, /lower than WDC/);
  assert.equal(/higher than WDC/.test(done.reply), false);
  assert.equal(done.meta.provider, "OpenAI");
  assert.equal(done.meta.model, "gpt-4o-mini");
});

test("non-stream JSON reply is corrected and an answer with no sources says so", async () => {
  const bad = "MU's trailing P/E (TTM) 11.8x is slightly higher than WDC's trailing P/E (TTM) 12.3x.";
  const fresh = loadWithStubs(bad);
  seed(fresh);
  const res = { end(chunk) { this.chunk = String(chunk); }, setHeader() {}, headersSent: false };
  await fresh.handle({ method: "POST", url: "/api/chat", headers: { host: "localhost", accept: "application/json" } }, res);
  const body = JSON.parse(res.chunk);
  assert.match(body.reply, /trailing P\/E \(TTM\) 11\.8x is lower than WDC/);
  assert.equal(/higher/.test(body.reply), false);
  assert.match(body.reply, /Yahoo Finance/);
  assert.match(body.reply, /as of 2026-10-16 20:00 UTC/);
  const plain = fresh.bb2Finish("The regime is mixed.", { facts: [], clientSources: [], peerSource: null });
  assert.match(plain, /No news or price sources were supplied for this answer/);
  const priced = fresh.bb2Footer([{ name: "Yahoo Finance stream", link: "", asOf: "2026-10-18T15:04:00Z", detail: "MU price" }]);
  assert.match(priced, /\[1\] Yahoo Finance stream \| as of 2026-10-18T15:04:00Z \| MU price/);
});

function loadWithStubs(bad) {
  const sandbox = {
    console, require, Buffer, URL, URLSearchParams, TextDecoder, TextEncoder, Intl,
    setTimeout, clearTimeout, AbortSignal, Map, Set, Promise, Date, Math, JSON, RegExp, Error,
    encodeURIComponent, decodeURIComponent,
    process: { env: {} },
    currentUser: async () => ({ id: "u", tier: "premium" }),
    json(res, status, body) { res.statusCode = status; res._json = body; },
    fetch: async () => { throw new Error("unexpected fetch"); },
  };
  sandbox.global = sandbox;
  sandbox.globalThis = sandbox;
  sandbox._body = { messages: [{ role: "user", content: "How do MU's peers compare on P/E?" }], sources: [] };
  sandbox.readBody = async () => sandbox._body;
  sandbox.generateAi = async () => ({ text: bad, model: "grok" });
  sandbox.handle = async function (req, res) {
    const result = await sandbox.generateAi({ system: '{"reply":"string"}', messages: sandbox._body.messages });
    res.end(JSON.stringify({ reply: result.text, meta: { provider: "xAI", model: result.model } }));
  };
  vm.createContext(sandbox);
  vm.runInContext(extractJs(), sandbox, { filename: "bb2.js" });
  return sandbox;
}

test("a stale snapshot refreshes from Yahoo's keyless quote and a free user is not streamed", async () => {
  const calls = [];
  const s = loadBb2({
    AI_INTEGRATIONS_OPENAI_BASE_URL: "http://openai.test/v1",
    AI_INTEGRATIONS_OPENAI_API_KEY: "test-key",
  }, async (url) => {
    const href = String(url);
    calls.push(href);
    if (href.startsWith("https://fc.yahoo.com")) {
      return { ok: true, status: 200, headers: { getSetCookie: () => ["A3=abc; Path=/"], get: () => "A3=abc" } };
    }
    if (href.includes("/v1/test/getcrumb")) return { ok: true, status: 200, text: async () => "crumb123" };
    if (href.includes("/v7/finance/quote")) {
      return { ok: true, status: 200, json: async () => ({ quoteResponse: { result: [
        { symbol: "MU", trailingPE: 11.82349, forwardPE: 4.247783, regularMarketPrice: 878.84, regularMarketTime: 1792180800 },
        { symbol: "WDC", trailingPE: 12.332838, forwardPE: 9.97343, regularMarketPrice: 332, regularMarketTime: 1792180800 },
      ] } }) };
    }
    throw new Error("unexpected " + href);
  });
  const old = Date.now() - 48 * 3600e3;
  s.bb2Mem.vals.set("MU", { at: old, v: sampleVals().MU });
  const got = await s.bb2EnsureVals(["MU", "WDC"]);
  assert.ok(calls.some(u => u.includes("query1.finance.yahoo.com/v7/finance/quote")));
  assert.equal(calls.some(u => /api\.openai\.com|api\.x\.ai|polygon|finnhub/i.test(u)), false);
  assert.equal(s.bb2Rnd(got.MU.trailing), 11.8);
  assert.equal(s.bb2Rnd(got.WDC.trailing), 12.3);
  const fact = s.bb2BuildFacts("MU", { MU: got.MU, WDC: got.WDC }).facts.find(f => f.b === "WDC" && f.basis === "trailing");
  assert.equal(fact.dir, "lower");
  let status = 0;
  s.currentUser = async () => null;
  const res = { writeHead() { throw new Error("should not stream"); }, write() {}, end() {} };
  await s.bb2StreamChat({ method: "POST", url: "/api/chat", headers: { accept: "text/event-stream", "x-dispatch-stream": "1", host: "localhost" } }, res);
  status = res.statusCode;
  assert.equal(status, 401);
  assert.equal(res._json && res._json.error, "Premium membership required");
});
