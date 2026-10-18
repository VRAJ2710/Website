const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb3_ask.py");

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB3_JS\n([\s\S]*?)\n\/\/ BB3_JS_END/);
  assert.ok(m, "BB3_JS block missing");
  const js = m[1];
  assert.equal(js.includes("setInterval("), false);
  assert.equal(/node-cron|CREATE TABLE|\bcron\b/.test(js), false);
  assert.equal(js.includes("user.tier"), false);
  assert.ok(js.includes("!hasPremiumAccess(user)"));
  return js;
}

const PEERS = ["NVDA", "AVGO", "AMD", "WDC", "INTC"];
function sampleFacts() {
  const facts = PEERS.map(b => ({
    a: "MU",
    b,
    basis: "trailing",
    dir: b === "INTC" ? "missing" : "lower",
    sentence: b === "INTC"
      ? "INTC trailing P/E (TTM) was not reported, so MU and INTC are not compared on trailing P/E (TTM)."
      : "MU trailing P/E (TTM) 11.8x is lower than " + b + " trailing P/E (TTM) 12.3x by 0.5x (4.1%)."
  }));
  facts.push({ a: "MU", b: "WDC", basis: "forward", dir: "lower", sentence: "MU forward P/E 4.2x is lower than WDC forward P/E 10.0x by 5.8x (58.0%)." });
  facts.push({ a: "MU", b: "INTC", basis: "forward", dir: "lower", sentence: "MU forward P/E 4.2x is lower than INTC forward P/E 42.7x by 38.5x (90.2%)." });
  return facts;
}

function load(opts) {
  const sandbox = {
    console, require, Buffer, URL, URLSearchParams, TextDecoder, TextEncoder, Intl,
    setTimeout, clearTimeout, AbortSignal, Map, Set, Promise, Date, Math, JSON, RegExp, Error,
    encodeURIComponent, decodeURIComponent,
    process: { env: {} },
    BB2_PEERS: { MU: PEERS.slice() },
    bb2Mem: { vals: new Map() },
    currentUser: async () => ({ id: "u", tier: "premium", isAdmin: false }),
    isAdminUser(user) { return Boolean(user && user.isAdmin === true); },
    hasPremiumAccess(user) { return Boolean(user && (user.tier === "premium" || sandbox.isAdminUser(user))); },
    json(res, status, body) { res.statusCode = status; res._json = body; return res; },
    bb2Question(body) {
      const msgs = (body && body.messages) || [];
      for (let i = msgs.length - 1; i >= 0; i--) if (msgs[i] && msgs[i].role === "user") return String(msgs[i].content || "");
      return "";
    },
    bb2PeerAsk(q) { return /peer|compar|valuation|p\/e/i.test(String(q || "")); },
    bb2Base(q) { return /\bMU\b/.test(String(q || "")) ? "MU" : null; },
    bb2FixSentence(s) {
      if (/trailing|\bttm\b/i.test(s) && /forward/i.test(s) && !/not compared|different bases/i.test(s)) {
        return "Trailing P/E (TTM) and forward P/E are different bases and are not compared.";
      }
      return s;
    },
    bb2Scrub(s) { return s; },
    bb2ClientSources(body) { return (body && body.sources) || []; },
    bb2BuildFacts(base, vals) {
      return { base, facts: sampleFacts(), asOf: (vals.MU && vals.MU.asOf) || "2026-10-16 20:00 UTC" };
    },
    bb2PeerSource(base, built) {
      return { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/" + base + "/key-statistics/", asOf: built.asOf || "", detail: "trailing P/E (TTM) and forward P/E, refreshed on request" };
    },
    bb2Footer(sources) {
      if (!sources || !sources.length) return "\n\nSources: No news or price sources were supplied for this answer.";
      return "\n\nSources:\n" + sources.map((s, i) => "[" + (i + 1) + "] " + s.name + " | " + (s.detail || "")).join("\n");
    },
    bb2System(body) { sandbox._seenContext = body && body.context; return "system"; },
    bb2Complete: async (_s, _m, onDelta) => {
      onDelta("Demand is the driver.\n");
      onDelta("- MU trailing P/E (TTM) 11.8x is lower than WDC trailing P/E (TTM) 12.3x by 0.5x (4.1%).\n");
      onDelta("- MU forward P/E 4.2x is lower than WDC forward P/E 10.0x by 5.8x (58.0%).\n");
      return { provider: "OpenAI", model: "gpt-4o-mini" };
    },
    bb2Refresh: opts && opts.refresh ? opts.refresh : async () => {},
    bb2Read0: async () => sandbox._body,
    bb2Als: {
      _s: null,
      getStore() { return this._s; },
      run(store, fn) { this._s = store; return fn(); }
    }
  };
  sandbox.global = sandbox;
  sandbox.globalThis = sandbox;
  sandbox._body = opts && opts.body ? opts.body : { messages: [{ role: "user", content: "How does MU's valuation compare with its peers?" }], sources: [], tickers: ["MU"] };
  vm.createContext(sandbox);
  vm.runInContext(extractJs(), sandbox, { filename: "bb3.js" });
  return sandbox;
}

function streamRes() {
  const writes = [];
  const t0 = Date.now();
  return {
    writes,
    statusCode: 0,
    headers: null,
    headersSent: false,
    writableEnded: false,
    writeHead(code, headers) { this.statusCode = code; this.headers = headers; this.headersSent = true; },
    flushHeaders() {},
    write(chunk) { writes.push({ at: Date.now() - t0, chunk: String(chunk) }); return true; },
    end() { this.writableEnded = true; },
    flush() {},
    socket: { setNoDelay() {} }
  };
}

const SPLICE = "MU forward P/E 4.2x is lower than INTC forward P/E 42.7x by 38.5x (90.2%).\nMU trailing P/E (TTM) 11.8x is higher than its forward P/E 4.2x.\nDemand is firm.\n";
const BARE = "INTC at 42.7x by 38.5x (90.2%)\nMU trailing P/E (TTM) 11.8x is higher than its forward P/E 4.2x.\nDemand is firm.\n";

function pumped(s, text, sizes) {
  let buf = "", out = "";
  function pump(force) {
    while (buf) {
      const part = s.bb3Next(buf, false);
      if (!part) break;
      out += part.prefix + s.bb3Fix(part.sentence, []) + part.sep;
      buf = part.rest;
    }
    if (force && buf) {
      const last = s.bb3Next(buf, true);
      out += last.prefix + s.bb3Fix(last.sentence, []) + last.sep;
      buf = "";
    }
  }
  let i = 0, n = 0;
  while (i < text.length) {
    const sz = sizes[n++ % sizes.length];
    buf += text.slice(i, i + sz);
    i += sz;
    pump(false);
  }
  pump(true);
  return out;
}

test("sentence splice keeps punctuation and newlines across random chunks", () => {
  const s = load();
  const whole = s.bb3Rewrite(SPLICE, [], false);
  const bare = s.bb3Rewrite(BARE, [], false);
  assert.match(whole, /\(90\.2%\)\.\nTrailing P\/E \(TTM\) and forward P\/E are different bases and are not compared\.\n/);
  assert.equal(whole.includes(").Trailing"), false);
  assert.equal(whole.includes("%Trailing"), false);
  assert.match(bare, /\(90\.2%\)\nTrailing P\/E \(TTM\) and forward P\/E are different bases and are not compared\.\n/);
  assert.equal(bare.includes("%Trailing"), false);
  for (let trial = 0; trial < 30; trial++) {
    const sizes = [1, 2, 3, 4, 5, 7, 8, 11].map(() => 1 + Math.floor(Math.random() * 12));
    assert.equal(pumped(s, SPLICE, sizes), whole, "sizes " + sizes.join(","));
    assert.equal(pumped(s, BARE, sizes), bare, "bare " + sizes.join(","));
  }
});

test("comparisons are shown once and every peer is present, including INTC", async () => {
  const s = load();
  s.bb2Mem.vals.set("MU", { v: { asOf: "2026-10-16 20:00 UTC" } });
  s.bb2Mem.vals.set("INTC", { v: { asOf: "2026-10-16 20:00 UTC" } });
  const res = streamRes();
  await s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost", accept: "text/event-stream", "x-dispatch-stream": "1" }
  }, res));
  const done = res.writes.map(w => JSON.parse(w.chunk.replace(/^data: /, "").trim())).filter(e => e.done).pop();
  const reply = done.reply;
  for (const b of PEERS) assert.match(reply, new RegExp("\\b" + b + "\\b"), b);
  assert.equal(reply.split("INTC trailing P/E (TTM) was not reported").length - 1, 1);
  assert.equal(reply.split("lower than WDC trailing P/E (TTM)").length - 1, 1);
  assert.equal(reply.split("lower than WDC forward P/E").length - 1, 1);
  assert.match(reply, /Demand is the driver/);
  assert.equal(reply.includes("- MU trailing"), false);
  assert.match(reply, /as of 2026-10-16 20:00 UTC/);
});

test("MU peer question drops irrelevant news and renumbers", async () => {
  const sources = [
    { name: "Reuters", detail: "Canada base fire spreads", link: "https://www.reuters.com/world/canada-fire" },
    { name: "Reuters", detail: "MU lifts its data-center outlook", link: "https://www.reuters.com/tech/mu" },
    { name: "AFP", detail: "French town hall fire", link: "https://example.com/fr" },
    { name: "MarketWatch", detail: "oil prices jump on supply", link: "https://example.com/oil" },
    { name: "Price feed", detail: "MU price", link: "" }
  ];
  const s = load({ body: { messages: [{ role: "user", content: "How does MU's valuation compare with its peers?" }], sources, tickers: ["MU"] } });
  s.bb2Mem.vals.set("MU", { v: { asOf: "2026-10-16 20:00 UTC" } });
  const res = streamRes();
  await s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost" }
  }, res));
  const done = res.writes.map(w => JSON.parse(w.chunk.replace(/^data: /, "").trim())).filter(e => e.done).pop();
  const reply = done.reply;
  assert.equal(/Canada base fire|town hall fire|oil prices/i.test(reply), false);
  assert.match(reply, /MU lifts its data-center outlook/);
  assert.match(reply, /MU price/);
  assert.match(reply, /Yahoo Finance/);
  const nums = [...reply.matchAll(/^\[(\d+)\] /gm)].map(m => Number(m[1]));
  assert.deepEqual(nums, [1, 2, 3]);
});

test("cold cache first event is under 1s while Yahoo is slow", async () => {
  let yahooDone = false;
  const s = load({
    refresh() {
      return new Promise(resolve => {
        const t = setTimeout(() => { yahooDone = true; resolve(); }, 2500);
        if (t.unref) t.unref();
      });
    }
  });
  const res = streamRes();
  const started = Date.now();
  const pending = s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost" }
  }, res));
  await new Promise(r => setTimeout(r, 50));
  assert.ok(res.writes.length >= 1, "no first event");
  const first = JSON.parse(res.writes[0].chunk.replace(/^data: /, "").trim());
  assert.match(first.t, /Fetching latest valuations/);
  assert.ok(res.writes[0].at < 1000, "ttft " + res.writes[0].at);
  assert.equal(yahooDone, false);
  assert.match(res.headers["Content-Type"], /text\/event-stream/);
  assert.equal(res.headers["X-Accel-Buffering"], "no");
  await pending;
  assert.ok(Date.now() - started < 2000, "stream waited for the slow Yahoo fetch");
});

test("a fast cold Yahoo still delivers the comparison block within 1s", async () => {
  const s = load({
    refresh() {
      return new Promise(resolve => setTimeout(() => {
        s.bb2Mem.vals.set("MU", { v: { asOf: "2026-10-16 20:00 UTC" } });
        resolve();
      }, 200));
    }
  });
  const res = streamRes();
  await s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost" }
  }, res));
  const events = res.writes.map(w => ({ at: w.at, ev: JSON.parse(w.chunk.replace(/^data: /, "").trim()) })).filter(w => w.ev.t);
  assert.match(events[0].ev.t, /Fetching latest valuations/);
  assert.ok(events[0].at < 1000);
  const block = events.find(w => /INTC trailing P\/E \(TTM\) was not reported/.test(w.ev.t));
  assert.ok(block, "comparison block missing");
  assert.ok(block.at < 1000, "block at " + block.at);
});

test("cached snapshot is the first event and does not wait for Yahoo", async () => {
  let started = false;
  const s = load({
    refresh() {
      started = true;
      return new Promise(resolve => {
        const t = setTimeout(resolve, 2500);
        if (t.unref) t.unref();
      });
    }
  });
  s.bb2Mem.vals.set("MU", { v: { asOf: "2026-10-16 20:00 UTC" } });
  const res = streamRes();
  const pending = s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost" }
  }, res));
  await new Promise(r => setTimeout(r, 30));
  const first = JSON.parse(res.writes[0].chunk.replace(/^data: /, "").trim());
  assert.match(first.t, /Peer comparisons as of 2026-10-16 20:00 UTC/);
  assert.match(first.t, /INTC trailing P\/E \(TTM\) was not reported/);
  assert.ok(res.writes[0].at < 1000);
  await pending;
  assert.equal(started, true);
});

test("cold cache streams the first model token without waiting for Yahoo or the full completion", async () => {
  let yahooDone = false;
  const s = load({
    refresh() {
      return new Promise(resolve => {
        const t = setTimeout(() => { yahooDone = true; resolve(); }, 2500);
        if (t.unref) t.unref();
      });
    },
    body: {
      messages: [{ role: "user", content: "How does MU's valuation compare with its peers?" }],
      tickers: ["MU"],
      context: [
        "Peer valuations (live):",
        "MU: trailing P/E (TTM) 11.8x",
        "Regime: Risk-On and a long essay about the dollar.",
        "Latest headlines:",
        "• Canada base fire spreads overnight",
        "• MU lifts its data-center outlook",
        "• oil prices jump on supply",
        "Portfolio:",
        "AAPL ×1 @ $100",
        "Active ticker: MU Micron · $185"
      ].join("\n") + "\n" + "unrelated ".repeat(2000)
    }
  });
  s.bb2Complete = async (_sys, _msgs, onDelta) => {
    await new Promise(r => setTimeout(r, 600));
    onDelta("Demand ");
    await new Promise(r => setTimeout(r, 40));
    onDelta("is firm.\n");
    const bad = "MU trailing P/E (TTM) 11.8x is higher than its forward P/E 4.2x.\n";
    for (const ch of bad) onDelta(ch);
    return { provider: "OpenAI", model: "gpt-4o-mini" };
  };
  const res = streamRes();
  await s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
    method: "POST", url: "/api/chat", headers: { host: "localhost" }
  }, res));
  const events = res.writes.map(w => ({ at: w.at, ev: JSON.parse(w.chunk.replace(/^data: /, "").trim()) }));
  assert.match(events[0].ev.t, /Fetching latest valuations/);
  assert.ok(events[0].at < 1000);
  const model = events.find(w => w.ev.t && /Demand/.test(w.ev.t));
  assert.ok(model, "no model token");
  assert.ok(model.at >= 500 && model.at < 2000, "model ttft " + model.at);
  assert.ok(model.at > events[0].at);
  assert.equal(yahooDone, false);
  const done = events.filter(w => w.ev.done).pop();
  assert.match(done.ev.reply, /Demand is firm/);
  assert.match(done.ev.reply, /different bases and are not compared/);
  assert.equal(done.ev.reply.includes("%Trailing"), false);
  assert.equal(done.ev.reply.includes(").Trailing"), false);
  assert.equal(/higher than its forward/.test(done.ev.reply), false);
  assert.equal(/^Fetching latest valuations/.test(done.ev.reply), false);
  assert.equal(/Canada base fire|oil prices|Portfolio:|Regime:/.test(s._seenContext || ""), false);
  assert.match(s._seenContext, /MU lifts its data-center outlook/);
  assert.match(s._seenContext, /Active ticker: MU/);
  assert.ok(s._seenContext.length < 1600, "context " + s._seenContext.length);
});

test("a non-peer question keeps its context", () => {
  const s = load({ body: { messages: [{ role: "user", content: "What moved gold today?" }], context: "Latest headlines:\n• Canada base fire spreads\n", tickers: [] } });
  const out = s.bb3TrimBody(s._body);
  assert.match(out.context, /Canada base fire/);
});

test("admin and premium can stream; free and logged-out get the JSON 401", async () => {
  const roles = [
    { name: "admin", user: { id: "a", tier: "free", isAdmin: true }, allow: true },
    { name: "premium", user: { id: "p", tier: "premium", isAdmin: false }, allow: true },
    { name: "free", user: { id: "f", tier: "free", isAdmin: false }, allow: false },
    { name: "logged-out", user: null, allow: false }
  ];
  for (const role of roles) {
    const s = load();
    s.currentUser = async () => role.user;
    s.bb2Mem.vals.set("MU", { v: { asOf: "2026-10-16 20:00 UTC" } });
    const res = streamRes();
    await s.bb2Als.run({ facts: [], clientSources: [], peerSource: null }, () => s.bb2StreamInner({
      method: "POST", url: "/api/chat", headers: { host: "localhost" }
    }, res));
    if (role.allow) {
      assert.equal(res.statusCode, 200, role.name);
      assert.match(res.headers["Content-Type"], /text\/event-stream/, role.name);
    } else {
      assert.equal(res.statusCode, 401, role.name);
      assert.equal(res.headersSent, false, role.name);
      assert.equal(res._json && res._json.error, "Premium membership required", role.name);
    }
  }
});
