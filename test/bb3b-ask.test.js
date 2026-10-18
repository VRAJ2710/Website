const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb3b.py");

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB3B_JS\n([\s\S]*?)\n\/\/ BB3B_JS_END/);
  assert.ok(m, "BB3B_JS block missing");
  const js = m[1];
  assert.equal(js.includes("setInterval("), false);
  assert.equal(/node-cron|CREATE TABLE|\bcron\b/.test(js), false);
  assert.equal(js.includes("bb3Tickers("), false);
  assert.equal(js.includes("_bb4d"), false);
  assert.equal(js.includes("BB4D_AI"), false);
  assert.equal(js.includes("academy-daily"), false);
  assert.ok(js.includes("!hasPremiumAccess(user)"));
  assert.ok(js.includes("bb3b stream error"));
  assert.ok(js.includes("model_ttft_ms"));
  return js;
}

function chatMdSource() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/NEW_MD = """([\s\S]*?)"""/);
  assert.ok(m, "NEW_MD missing");
  return m[1].replace(/\\\\/g, "\\");
}

const PEERS = ["NVDA", "AVGO", "AMD", "WDC", "INTC"];
const LIVE_LIST = [
  "we can see significant differences:",
  "1. MU trailing P/E (TTM) 11.8x is lower than NVDA trailing P/E (TTM) 27.1x.",
  "2. MU trailing P/E (TTM) 11.8x is lower than AVGO trailing P/E (TTM) 42.0x.",
  "3. MU trailing P/E (TTM) 11.8x is lower than WDC trailing P/E (TTM) 12.3x.",
  "4. INTC trailing P/E (TTM) was not reported, so MU and INTC are not compared on trailing P/E (TTM).",
  "5. MU forward P/E 4.2x is lower than INTC forward P/E 42.7x.",
  "Summary"
].join("\n");

function sampleFacts() {
  return [
    { a: "MU", b: "NVDA", basis: "trailing", dir: "lower", sentence: "MU trailing P/E (TTM) 11.8x is lower than NVDA trailing P/E (TTM) 27.1x." },
    { a: "MU", b: "AVGO", basis: "trailing", dir: "lower", sentence: "MU trailing P/E (TTM) 11.8x is lower than AVGO trailing P/E (TTM) 42.0x." },
    { a: "MU", b: "WDC", basis: "trailing", dir: "lower", sentence: "MU trailing P/E (TTM) 11.8x is lower than WDC trailing P/E (TTM) 12.3x." },
    { a: "MU", b: "INTC", basis: "trailing", dir: "missing", sentence: "INTC trailing P/E (TTM) was not reported, so MU and INTC are not compared on trailing P/E (TTM)." },
    { a: "MU", b: "INTC", basis: "forward", dir: "lower", sentence: "MU forward P/E 4.2x is lower than INTC forward P/E 42.7x by 38.5x (90.2%)." }
  ];
}

function buildFacts(base, vals) {
  vals = vals || {};
  const peers = [base].concat(PEERS);
  const facts = [];
  peers.slice(1).forEach(sym => {
    const a = vals[base] || {};
    const b = vals[sym];
    ["trailing", "forward"].forEach(basis => {
      const av = a[basis];
      const bv = b && b[basis];
      const label = basis === "trailing" ? "trailing P/E (TTM)" : "forward P/E";
      if (!(av > 0) || !(bv > 0)) {
        if ((av > 0) || (bv > 0)) {
          const who = av > 0 ? sym : base;
          facts.push({ a: base, b: sym, basis, dir: "missing", sentence: who + " " + label + " was not reported, so " + base + " and " + sym + " are not compared on " + label + "." });
        }
        return;
      }
      facts.push({ a: base, b: sym, basis, dir: "lower", va: av, vb: bv, sentence: base + " " + label + " " + av + "x is lower than " + sym + " " + label + " " + bv + "x." });
    });
  });
  return { base, peers, facts, asOf: "2026-10-16 20:00 UTC", block: "AUTHORITATIVE" };
}

function load(opts) {
  opts = opts || {};
  const logs = [];
  const sandbox = {
    console: { warn(...a) { logs.push(a.map(x => String(x)).join(" ")); }, log() {}, error() {} },
    require, Buffer, URL, URLSearchParams, TextDecoder, TextEncoder, Intl,
    setTimeout, clearTimeout, AbortSignal, AbortController, Map, Set, Promise, Date, Math, JSON, RegExp, Error, Object, Array,
    encodeURIComponent, decodeURIComponent,
    process: { env: Object.assign({}, opts.env || {}) },
    globalThis: null,
    BB2_PEERS: { MU: PEERS.slice() },
    bb2Mem: { vals: new Map() },
    currentUser: async () => ({ id: "u", tier: "premium", isAdmin: false }),
    isAdminUser(user) { return Boolean(user && user.isAdmin === true); },
    hasPremiumAccess(user) { return Boolean(user && (user.tier === "premium" || sandbox.isAdminUser(user))); },
    json(res, status, body) { res.statusCode = status; res._json = body; if (res.end) res.end(JSON.stringify(body)); return res; },
    bb2Question(body) {
      const msgs = bb3bArrSafe(body && body.messages);
      for (let i = msgs.length - 1; i >= 0; i--) if (msgs[i] && msgs[i].role === "user") return String(msgs[i].content || "");
      return "";
    },
    bb2PeerAsk(q) { return /peer|compar|valuation|p\/e/i.test(String(q || "")); },
    bb2Base(q) { return /\bMU\b/.test(String(q || "")) ? "MU" : null; },
    bb2FixSentence(s) { return s; },
    bb2Scrub(s) { return s; },
    bb3Fix(s) { return s; },
    bb2BuildFacts: buildFacts,
    bb3LeadText(built, cite) {
      const facts = (built && built.facts) || [];
      const lines = facts.map(f => f && f.sentence).filter(Boolean);
      if (!lines.length) return "";
      return "Peer comparisons as of " + (built.asOf || "") + ":" + (cite ? " [" + cite + "]" : "") + "\n" + lines.join("\n") + "\n\n";
    },
    bb2PeerSource(base, built) {
      return { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/" + base + "/key-statistics/", asOf: built.asOf || "", detail: "trailing and forward" };
    },
    bb2Footer(sources) {
      if (opts.footerBoom) throw new Error("footer boom Bearer sk-testsecret123456");
      if (!sources || !sources.length) return "\n\nSources: No news or price sources were supplied for this answer.";
      return "\n\nSources:\n" + sources.map((src, i) => "[" + (i + 1) + "] " + src.name).join("\n");
    },
    bb2System(body) { sandbox._seenContext = body && body.context; return "system"; },
    bb2Complete: opts.complete || (async (_s, _m, onDelta) => {
      onDelta("Demand is firm.\n");
      onDelta(LIVE_LIST + "\n");
      return { provider: "OpenAI", model: "gpt-4o-mini" };
    }),
    bb2Refresh: opts.refresh || (async () => {}),
    bb2Read0: async () => sandbox._body,
    bb2Als: { _s: null, getStore() { return this._s; }, run(store, fn) { this._s = store; return fn(); } },
    bb3Tickers() { throw new Error("called clobbered bb3Tickers"); },
    AiRequestError: class AiRequestError extends Error { constructor(status, message, code) { super(message); this.status = status; this.code = code; } },
    aiProviderStatus() { return { fallbackOrder: ["xai", "anthropic", "google", "mistral", "openai"] }; },
    openAiOwnerOptIn() { return String(sandbox.process.env.OPENAI_MANUAL_OPT_IN || "").toLowerCase() === "true"; },
    aiProviderError(provider, status) {
      const code = status === 402 || status === 403 ? "PROVIDER_CREDITS" : "UPSTREAM_ERROR";
      return new sandbox.AiRequestError(status || 502, provider, code);
    },
    isAiTimeoutError(error) { return error && error.code === "TIMEOUT"; },
    asAiMessages(messages) { return bb3bArrSafe(messages).map(m => ({ role: "user", content: String(m && m.content || "") })); },
    clipped(v) { return String(v || ""); },
    withTimeout(p) { return p; },
    discoverAiModel: async () => "gemini",
    generateWithAiProvider: async (provider) => ({ text: "from " + provider, provider, model: "m" }),
    AI_TIMEOUT_MS: 25000,
    fetch: opts.fetch || (async () => ({ ok: true, status: 200, json: async () => ({ choices: [{ message: { content: "ok" } }] }) })),
    logs
  };
  sandbox.globalThis = sandbox;
  sandbox.global = sandbox;
  sandbox._body = opts.body || {
    messages: [{ role: "user", content: "How does MU compare with peers on valuation, especially INTC trailing P/E versus forward P/E?" }],
    sources: [],
    tickers: ["MU"],
    context: "Latest headlines:\n- Canada wildfire\nActive ticker: MU\n"
  };
  vm.createContext(sandbox);
  vm.runInContext(extractJs() + "\nthis.bb3bAskInfo = bb3bAskInfo; this.bb3bRewrite = bb3bRewrite; this.bb3bMentions = bb3bMentions; this.bb3bFilterSources = bb3bFilterSources; this.bb3bGenerateAi = bb3bGenerateAi; this.bb3bAttempts = bb3bAttempts;", sandbox, { filename: "bb3b.js" });
  sandbox.logs = logs;
  return sandbox;
}

function bb3bArrSafe(x) { return Array.isArray(x) ? x : []; }

function streamRes() {
  const writes = [];
  let flushed = false;
  return {
    writes,
    statusCode: 0,
    headers: null,
    headersSent: false,
    writableEnded: false,
    get flushed() { return flushed; },
    writeHead(code, headers) { this.statusCode = code; this.headers = headers; this.headersSent = true; },
    flushHeaders() { flushed = true; this.headersSent = true; },
    write(chunk) { writes.push(String(chunk)); return true; },
    end() { this.writableEnded = true; },
    flush() {},
    socket: { setNoDelay() {} }
  };
}

function events(res) {
  return res.writes.filter(w => w.indexOf("data: ") === 0).map(w => JSON.parse(w.replace(/^data: /, "").trim()));
}

const VALS = {
  MU: { trailing: 11.8, forward: 4.2, price: 100 },
  NVDA: { trailing: 27.1, forward: 13.5, price: 180 },
  AVGO: { trailing: 42.0, forward: 16.9, price: 170 },
  WDC: { trailing: 12.3, forward: 10.0, price: 60 },
  INTC: { trailing: null, forward: 42.7, price: 22 }
};

test("unpatched shape throws on tickers.length", () => {
  // chat61 server.js:8895 (filter :8901; fit bb3Tickers :9155 overwrites :8874).
  // chat59 server.js:8546 (filter :8552; fit bb3Tickers :8806 overwrites :8525).
  // Fit's function bb3Tickers() returns an array, so info.tickers is undefined.
  function bb3Tickers() { return ["AAPL", "MU"]; }
  function bb3Mentions(source, tickers) {
    for (var i = 0; i < tickers.length; i++) return true;
    return false;
  }
  function bb3FilterSources(sources, body) {
    var info = bb3Tickers(body);
    (sources || []).forEach(function (src) { bb3Mentions(src, info.tickers); });
  }
  assert.throws(() => bb3FilterSources([{ name: "Reuters", detail: "oil" }], {}), /reading 'length'/);
});

test("guards undefined arrays and missing numbers", () => {
  const s = load();
  assert.equal(s.bb3bMentions({ name: "MU filing" }, undefined), false);
  assert.equal(JSON.stringify(s.bb3bFilterSources(undefined, s._body)), "[]");
  assert.doesNotThrow(() => s.bb3bRewrite(LIVE_LIST, undefined, true));
  const built = buildFacts("MU", VALS);
  assert.ok(built.facts.some(f => f.b === "INTC" && f.dir === "missing"));
  assert.ok(built.facts.some(f => f.b === "INTC" && f.basis === "forward"));
  assert.ok(built.facts.some(f => f.b === "AMD" && f.dir === "missing"));
});

test("drops the whole restated list and keeps a real item", () => {
  const s = load();
  const dropped = s.bb3bRewrite("Demand is firm.\n" + LIVE_LIST + "\n", sampleFacts(), true);
  assert.equal(/differences:/.test(dropped), false);
  assert.equal(/^\s*\d+\.\s*$/m.test(dropped), false);
  assert.equal(/\bSummary\b/.test(dropped), false);
  assert.match(dropped, /Demand is firm/);
  const keptLine = "6. Demand for HBM is the other point in this cycle.";
  const mixed = s.bb3bRewrite(LIVE_LIST + "\n" + keptLine + "\nSummary\nThe cycle still matters.\n", sampleFacts(), true);
  assert.ok(mixed.indexOf(keptLine) >= 0);
  assert.match(mixed, /Summary/);
  assert.match(mixed, /The cycle still matters/);
  assert.equal(/^\s*1\.\s*$/m.test(mixed), false);
});

test("cold MU/INTC stream sends done and does not throw", async () => {
  let started = false;
  let releaseRefresh;
  const refreshGate = new Promise(r => { releaseRefresh = r; });
  const s = load({
    refresh: () => refreshGate.then(() => {
      ["MU", "NVDA", "AVGO", "WDC", "INTC"].forEach(sym => {
        if (VALS[sym]) s.bb2Mem.vals.set(sym, { at: Date.now(), v: VALS[sym] });
      });
    }),
    complete: async (_sys, _msgs, onDelta) => {
      started = true;
      onDelta("Demand is firm.\n");
      onDelta(LIVE_LIST + "\n");
      return { provider: "OpenAI", model: "gpt-4o-mini" };
    }
  });
  const res = streamRes();
  const req = { method: "POST", url: "/api/chat", headers: { accept: "text/event-stream", "x-dispatch-stream": "1", host: "localhost" } };
  const pending = s.bb2Als.run({ chat: true }, () => s.bb2StreamInner(req, res));
  await new Promise(r => setTimeout(r, 30));
  assert.equal(started, true);
  assert.equal(res.flushed, true);
  assert.equal(res.headers["X-Accel-Buffering"], "no");
  assert.match(res.headers["Cache-Control"], /no-cache, no-transform/);
  assert.equal(res.headers.Connection, "keep-alive");
  const pad = res.writes.find(w => w.charAt(0) === ":");
  assert.ok(pad && pad.length >= 2048);
  const early = events(res);
  assert.ok(early.some(ev => ev.t && /Fetching latest valuations/.test(ev.t)));
  assert.equal(early.some(ev => ev.done), false);
  releaseRefresh();
  await pending;
  assert.equal(res.writableEnded, true);
  const ev = events(res);
  const done = ev.filter(e => e.done);
  assert.equal(done.length, 1);
  const reply = done[0].reply;
  assert.match(reply, /INTC trailing P\/E \(TTM\) was not reported/);
  assert.match(reply, /forward P\/E 4\.2x is lower than INTC forward P\/E 42\.7x/);
  assert.equal(/differences:/.test(reply), false);
  assert.equal(/^\s*\d+\.\s*$/m.test(reply), false);
  assert.match(reply, /Demand is firm/);
  const success = s.logs.filter(l => l.indexOf("model_ttft_ms") >= 0);
  assert.equal(success.length, 1);
  assert.match(success[0], /total_ms/);
  assert.match(success[0], /provider OpenAI/);
  const leadAt = ev.findIndex(e => e.t && /Peer comparisons/.test(e.t));
  const demandAt = ev.findIndex(e => e.t && /Demand is firm/.test(e.t));
  assert.ok(leadAt >= 0 && demandAt >= 0);
});

test("warm cache paints the peer block before model text", async () => {
  const s = load();
  Object.keys(VALS).forEach(sym => s.bb2Mem.vals.set(sym, { at: Date.now(), v: VALS[sym] }));
  const res = streamRes();
  await s.bb2Als.run({ chat: true }, () => s.bb2StreamInner({ method: "POST", url: "/api/chat", headers: { host: "h" } }, res));
  const ev = events(res);
  const firstText = ev.find(e => e.t);
  assert.match(firstText.t, /Peer comparisons/);
  assert.match(firstText.t, /INTC trailing P\/E \(TTM\) was not reported/);
  const model = ev.find(e => e.t && /Demand is firm/.test(e.t));
  assert.ok(ev.indexOf(firstText) < ev.indexOf(model));
});

test("stream failure after headers sends error and done", async () => {
  const s = load({ footerBoom: true });
  Object.keys(VALS).forEach(sym => s.bb2Mem.vals.set(sym, { at: Date.now(), v: VALS[sym] }));
  const res = streamRes();
  await s.bb2StreamInner({ method: "POST", url: "/api/chat", headers: { host: "h" } }, res);
  const ev = events(res);
  assert.ok(ev.some(e => e.error === "unavailable"));
  assert.ok(ev.some(e => e.done));
  const err = s.logs.filter(l => l.indexOf("bb3b stream error") === 0);
  assert.equal(err.length, 1);
  assert.match(err[0], /footer boom/);
  assert.match(err[0], /Bearer \[redacted\]/);
  assert.equal(err[0].includes("sk-testsecret123456"), false);
  assert.equal(s.logs.some(l => l.indexOf("model_ttft_ms") >= 0), false);
});

test("openai1 is tried before openai, then xAI cools down", async () => {
  const calls = [];
  let xaiHits = 0;
  const env = {
    XAI_API_KEY: "xai-secret-value",
    AI_INTEGRATIONS_OPENAI_API_KEY: "integration-secret-value",
    AI_INTEGRATIONS_OPENAI_BASE_URL: "https://integration.example/v1",
    OPENAI_API_KEY: "manual-secret-value",
    OPENAI_MANUAL_OPT_IN: "true"
  };
  const s = load({
    env,
    fetch: async (url, opts) => {
      const auth = String(opts && opts.headers && opts.headers.Authorization || "");
      const id = auth.endsWith(env.AI_INTEGRATIONS_OPENAI_API_KEY) ? "openai1" : auth.endsWith(env.OPENAI_API_KEY) ? "openai" : "other";
      calls.push(id);
      if (id === "openai1") return { ok: true, status: 200, json: async () => { throw new Error("bad json"); } };
      if (id === "openai") return { ok: true, status: 200, json: async () => ({ choices: [{ message: { content: "legacy answer" } }] }) };
      return { ok: false, status: 500, json: async () => ({}) };
    }
  });
  s.bb3bXaiTest = () => ({
    completeWithXaiKey: async () => { xaiHits += 1; const e = new s.AiRequestError(402, "no credits", "PROVIDER_CREDITS"); throw e; },
    xaiBaseUrl: () => "https://api.x.ai",
    xaiModel: () => "grok"
  });
  const first = await s.bb3bGenerateAi({ system: "sys", messages: [{ role: "user", content: "MU peers" }], maxTokens: 400 });
  assert.equal(first.text, "legacy answer");
  assert.deepEqual(calls, ["openai1", "openai"]);
  assert.equal(xaiHits, 1);
  assert.match(s.logs.join("\n"), /AI provider attempt failed: xai-key PROVIDER_CREDITS/);
  assert.match(s.logs.join("\n"), /AI provider attempt failed: openai1 INVALID_RESPONSE/);
  assert.match(s.logs.join("\n"), /AI provider answered: openai/);
  const blob = s.logs.join("\n");
  assert.equal(blob.includes(env.XAI_API_KEY), false);
  assert.equal(blob.includes(env.OPENAI_API_KEY), false);
  assert.equal(blob.includes(env.AI_INTEGRATIONS_OPENAI_API_KEY), false);
  calls.length = 0;
  const second = await s.bb3bGenerateAi({ system: "sys", messages: [{ role: "user", content: "again" }] });
  assert.equal(second.text, "legacy answer");
  assert.equal(xaiHits, 1);
  assert.deepEqual(calls, ["openai1", "openai"]);
});

test("client markdown skips marker-only lines", () => {
  const src = chatMdSource();
  const sandbox = { String, RegExp };
  vm.createContext(sandbox);
  vm.runInContext(src + "\nthis._chatMd = _chatMd;", sandbox);
  const html = sandbox._chatMd("we can see significant differences:\n1.\n2.\n3.\nSummary\n1. Demand for HBM stayed firm.\n");
  assert.equal(/<li>\s*<\/li>/.test(html), false);
  assert.equal(/chat-li-dot">▸<\/span>\s*<\/div>/.test(html), false);
  assert.equal(/>\s*1\.\s*</.test(html), false);
  assert.match(html, /1\. Demand for HBM stayed firm/);
});
