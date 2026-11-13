"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockO = fs.readFileSync(path.join(dir, "server_block_c102r6o.js"), "utf8");
const blockP = fs.readFileSync(path.join(dir, "server_block_c102r6p.js"), "utf8");

function buggyYahooQuote(payload, expect) {
  const result = payload && payload.chart && Array.isArray(payload.chart.result) ? payload.chart.result[0] : null;
  const meta = result && result.meta;
  if (!meta || (expect && expect.symbol && meta.symbol !== expect.symbol)) {
    return { status: "malformed" };
  }
  const price = meta.regularMarketPrice;
  const prevRaw = typeof meta.previousClose === "number" ? meta.previousClose : (typeof meta.chartPreviousClose === "number" ? meta.chartPreviousClose : null);
  const prev = prevRaw != null && isFinite(prevRaw) ? prevRaw : null;
  const change = prev == null ? null : Math.round((price - prev) * 1e6) / 1e6;
  return {
    status: change == null ? "partial" : "ok",
    message: change == null ? "no previous close" : "",
    name: expect && expect.label || meta.symbol,
    price: price,
    previousClose: prev,
    change: change,
    asOfUtc: typeof meta.regularMarketTime === "number" ? new Date(meta.regularMarketTime * 1000).toISOString() : null,
    exchange: meta.fullExchangeName || meta.exchangeName || "",
    timezone: meta.exchangeTimezoneName || "",
    instrumentType: meta.instrumentType || "",
    source: expect && expect.source || "yahoo"
  };
}

function loadQuote() {
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: function () {} }; },
    Buffer, JSON, Object, Array, String, Intl, Date, Promise, isFinite, URL,
    c102YahooQuote: buggyYahooQuote,
    c97Transform: function (html) { return html; }
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(blockP, context);
  return context;
}

function bar(iso, close) {
  // midnight America/New_York on that date, as Yahoo daily bars do
  const ms = Date.parse(iso + "T00:00:00-05:00");
  return { t: Math.floor(ms / 1000), c: close };
}

function dailyChart(symbol, bars, opts) {
  opts = opts || {};
  const last = bars[bars.length - 1];
  const ts = bars.map((b) => b.t);
  const close = bars.map((b) => b.c);
  const firstClose = bars[0].c;
  const meta = {
    symbol: symbol,
    instrumentType: "INDEX",
    regularMarketPrice: opts.price != null ? opts.price : last.c,
    regularMarketTime: opts.regularMarketTime != null ? opts.regularMarketTime : last.t + (opts.timeOffset || 0),
    regularMarketPreviousClose: opts.regularMarketPreviousClose != null ? opts.regularMarketPreviousClose : null,
    previousClose: Object.prototype.hasOwnProperty.call(opts, "previousClose") ? opts.previousClose : null,
    chartPreviousClose: opts.chartPreviousClose != null ? opts.chartPreviousClose : firstClose,
    exchangeName: opts.exchangeName || "NYB",
    fullExchangeName: opts.fullExchangeName || "ICE Futures",
    exchangeTimezoneName: opts.tz || "America/New_York",
    timezone: "EST",
    dataGranularity: opts.granularity || "1d",
    currency: "USD",
    shortName: opts.shortName || symbol
  };
  return { chart: { result: [{ meta: meta, timestamp: ts, indicators: { quote: [{ close: close, open: close, high: close, low: close, volume: close.map(() => 0) }] } }], error: null } };
}

function minuteChart(symbol, prev, price, sessionDay, tz) {
  const open = Date.parse(sessionDay + "T00:00:00-05:00") / 1000;
  const ts = [open + 3600, open + 3660, open + 3720];
  const close = [price - 0.002, price - 0.001, price];
  return { chart: { result: [{
    meta: {
      symbol: symbol, instrumentType: "INDEX",
      regularMarketPrice: price,
      regularMarketTime: ts[ts.length - 1],
      previousClose: prev,
      chartPreviousClose: prev,
      exchangeTimezoneName: tz || "America/New_York",
      timezone: "EST",
      dataGranularity: "1m",
      fullExchangeName: "ICE Futures"
    },
    timestamp: ts,
    indicators: { quote: [{ close: close }] }
  }] } };
}

test("DX-Y.NYB 5d/1d uses Thursday's close, not chartPreviousClose 101.65", () => {
  const ctx = loadQuote();
  const payload = dailyChart("DX-Y.NYB", [
    bar("2026-11-09", 101.65),
    bar("2026-11-10", 102.23),
    bar("2026-11-11", 102.91),
    bar("2026-11-12", 103.17),
    bar("2026-11-13", 103.16)
  ], { chartPreviousClose: 101.65, previousClose: null, price: 103.16, timeOffset: 2 * 3600, shortName: "US Dollar Index", fullExchangeName: "ICE Futures" });
  assert.equal(payload.chart.result[0].meta.chartPreviousClose, 101.65);
  const buggy = buggyYahooQuote(payload, { symbol: "DX-Y.NYB", label: "US dollar index" });
  assert.equal(buggy.previousClose, 101.65);
  const row = ctx.c102YahooQuote(payload, { symbol: "DX-Y.NYB", label: "US dollar index" });
  assert.equal(row.previousClose, 103.17);
  assert.equal(row.prevAsOf, "2026-11-12");
  assert.match(row.prevAsOfUk, /Thu 12 Nov/);
  assert.equal(row.price, 103.16);
  assert.ok(Math.abs(row.change - (103.16 - 103.17)) < 1e-9);
  const pct = (row.price - row.previousClose) / row.previousClose * 100;
  assert.ok(Math.abs(pct - (-0.01)) < 0.005, "pct " + pct);
  assert.equal(row.status, "ok");
  assert.equal(JSON.stringify(row).includes("101.65"), false);
  assert.equal(JSON.stringify(row).toLowerCase().includes("dxy_fx"), false);
  assert.equal(JSON.stringify(row).includes("DISPATCH-FX"), false);
});

test("VIX after the cash close: last bar is the completed session, prev is the bar before it", () => {
  const ctx = loadQuote();
  const payload = dailyChart("^VIX", [
    bar("2026-11-06", 25.64),
    bar("2026-11-09", 20.1),
    bar("2026-11-10", 19.2),
    bar("2026-11-11", 17.49),
    bar("2026-11-12", 18.7)
  ], { chartPreviousClose: 25.64, previousClose: null, price: 18.7, shortName: "CBOE Volatility Index", fullExchangeName: "Cboe Options Exchange", exchangeName: "CXI", timeOffset: 16 * 3600 + 15 * 60 });
  const buggy = buggyYahooQuote(payload, { symbol: "^VIX" });
  assert.equal(buggy.previousClose, 25.64);
  const row = ctx.c102YahooQuote(payload, { symbol: "^VIX" });
  assert.equal(row.previousClose, 17.49);
  assert.equal(row.prevAsOf, "2026-11-11");
  assert.match(row.prevAsOfUk, /Wed 11 Nov/);
  assert.ok(Math.abs(row.change - (18.7 - 17.49)) < 1e-9);
});

test("TNX after the cash close, same last-completed-bar shape", () => {
  const ctx = loadQuote();
  const payload = dailyChart("^TNX", [
    bar("2026-11-06", 4.859),
    bar("2026-11-09", 4.9),
    bar("2026-11-10", 4.95),
    bar("2026-11-11", 4.998),
    bar("2026-11-12", 5.103)
  ], { chartPreviousClose: 4.859, previousClose: null, price: 5.103, shortName: "CBOE Interest Rate 10 Year T Note", timeOffset: 15 * 3600 });
  const buggy = buggyYahooQuote(payload, { symbol: "^TNX" });
  assert.equal(buggy.previousClose, 4.859);
  const row = ctx.c102YahooQuote(payload, { symbol: "^TNX" });
  assert.equal(row.previousClose, 4.998);
  assert.equal(row.prevAsOf, "2026-11-11");
  assert.ok(Math.abs(row.change - (5.103 - 4.998)) < 1e-9);
});

test("1d/1m path is unchanged (previousClose already the session close)", () => {
  const ctx = loadQuote();
  const payload = minuteChart("DX-Y.NYB", 103.173, 103.156, "2026-11-13");
  const buggy = buggyYahooQuote(payload, { symbol: "DX-Y.NYB" });
  const row = ctx.c102YahooQuote(payload, { symbol: "DX-Y.NYB" });
  assert.equal(buggy.previousClose, 103.173);
  assert.equal(row.previousClose, 103.173);
  assert.ok(Math.abs(row.change - buggy.change) < 1e-12);
  assert.equal(row.prevAsOf, undefined);
});

test("1d/1d path is unchanged when only today's bar is present", () => {
  const ctx = loadQuote();
  const payload = dailyChart("DX-Y.NYB", [bar("2026-11-13", 103.164)], { chartPreviousClose: 103.173, previousClose: null, price: 103.164 });
  const buggy = buggyYahooQuote(payload, { symbol: "DX-Y.NYB" });
  const row = ctx.c102YahooQuote(payload, { symbol: "DX-Y.NYB" });
  assert.equal(buggy.previousClose, 103.173);
  assert.equal(row.previousClose, 103.173);
  assert.ok(Math.abs(row.change - buggy.change) < 1e-12);
  assert.equal(row.prevAsOf, undefined);
});

test("c102r6pSessionPrev never reads chartPreviousClose and skips a null daily hole", () => {
  const ctx = loadQuote();
  const bars = [
    bar("2026-11-09", 101.65),
    bar("2026-11-10", 102.23),
    { t: bar("2026-11-11", 0).t, c: null },
    bar("2026-11-12", 103.17),
    bar("2026-11-13", 103.16)
  ];
  const payload = dailyChart("DX-Y.NYB", bars, { chartPreviousClose: 101.65, price: 103.16 });
  payload.chart.result[0].indicators.quote[0].close[2] = null;
  const fix = ctx.c102r6pSessionPrev(payload);
  assert.equal(fix.prev, 103.17);
  assert.equal(fix.prevAsOf, "2026-11-12");
  const src = fs.readFileSync(path.join(dir, "server_block_c102r6p.js"), "utf8");
  const sessionFn = src.split("function c102r6pSessionPrev")[1].split("function c102r6pYahooQuote")[0];
  assert.equal(sessionFn.includes("chartPreviousClose"), false);
});

test("install bar still ends with </html> and Content-Length stays exact", () => {
  function Res() { this.headers = {}; this.headersSent = false; }
  Res.prototype.setHeader = function (k, v) { this.headers[String(k).toLowerCase()] = v; };
  Res.prototype.getHeader = function (k) { return this.headers[String(k).toLowerCase()]; };
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  Res.prototype.write = function () { return true; };
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer, JSON, Object, Array, String, Intl, Date, isFinite, URL,
    c102YahooQuote: buggyYahooQuote,
    c97Transform: function (html) { return html; }
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(blockP, context);
  const html = "<!doctype html><html><head></head><body><footer>Prices last refreshed 19:08 UK UK time. Every time is UK time.</footer></body></html>";
  const res = new Res();
  res.req = { url: "/" };
  const out = context.c97Transform(html, res.req);
  const len = Buffer.byteLength(out);
  res.setHeader("Content-Length", len);
  res.headersSent = true;
  res.end(out);
  const body = Buffer.isBuffer(res.written) ? res.written.toString("utf8") : String(res.written);
  assert.equal(Buffer.byteLength(body), len);
  assert.ok(body.endsWith("</html>"));
  assert.equal(body.includes("UK UK time"), false);
  assert.match(body, /19:08 UK time/);
});

test("patch.py keeps the prefix bytes and leaves one r6p attach log", () => {
  const work = fs.mkdtempSync("/tmp/c102r6p-patch-");
  const prefix = "\"use strict\";\nfunction c102Ymd(ms, tz) { return new Intl.DateTimeFormat(\"en-CA\", { timeZone: tz, year: \"numeric\", month: \"2-digit\", day: \"2-digit\" }).format(new Date(ms)); }\nfunction c102YahooQuote(payload, expect) { return payload; }\n";
  const server = path.join(work, "server.js");
  fs.writeFileSync(server, prefix + blockO + (blockO.endsWith("\n") ? "" : "\n"));
  const before = crypto.createHash("sha256").update(prefix).digest("hex");
  const run = spawnSync("python3", [path.join(dir, "patch_c102r6p.py"), server, path.join(dir, "server_block_c102r6o.js"), path.join(dir, "server_block_c102r6p.js")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const out = fs.readFileSync(server, "utf8");
  assert.ok(out.startsWith(prefix));
  assert.ok(out.endsWith(blockP.endsWith("\n") ? blockP : blockP + "\n") || out.endsWith(blockP));
  const marker = "// chat102r6c last-write scrub.";
  const at = out.indexOf(marker);
  assert.equal(crypto.createHash("sha256").update(out.slice(0, at)).digest("hex"), before);
  assert.equal((out.match(/\[c102r6p\] scrub attached/g) || []).length, 1);
  assert.equal(out.includes("[c102r6o] scrub attached"), false);
  const names = [...out.matchAll(/^(?:async )?function ([A-Za-z0-9_$]+)/gm)].map((m) => m[1]);
  const dup = names.filter((n, i) => names.indexOf(n) !== i);
  assert.deepEqual(dup, [], "duplicate top-level functions: " + dup.join(","));
  const check = spawnSync("node", ["--check", server], { encoding: "utf8" });
  assert.equal(check.status, 0, check.stderr);
});

test("deploy.sh bytes match EXPECTED_SHA256 and the current dev (b0e7cd7) root md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(crypto.createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /261655cc8637949842b6536322696748ecc466a3f9d04684d97e683e6dcce66b/);
  assert.match(text, /3e6730cede4c0368d1dcbdc543c81d27/);
  assert.match(text, /f2d33993e4092477ac4f77a23769f650/);
  assert.match(text, /b5a35a7887f1ca8e5fbbcf87de03c866/);
  assert.match(text, /PREFIX_BYTES=2326795/);
  assert.match(text, /bak-chat102r6p/);
  assert.match(text, /\[c102r6p\] scrub attached|chat102r6p/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6p-root-");
  fs.writeFileSync(path.join(root, "server.js"), blockO);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6p\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6p.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
