"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const block = fs.readFileSync(path.join(dir, "server_block_c102r6b.js"), "utf8");
const RX = /GC=F|DX-Y|\^TNX|=X\b|\^VIX|\^GSPC|CL=F|BTC-USD/;
const SKIP = new Set(["symbol", "symbols", "id", "wire"]);

function readerStrings(value, key, acc) {
  if (typeof value === "string") {
    if (!key || !SKIP.has(key)) acc.push(value);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(function (item) { readerStrings(item, key, acc); });
    return;
  }
  if (value && typeof value === "object") {
    Object.keys(value).forEach(function (k) { readerStrings(value[k], k, acc); });
  }
}

function liveShape() {
  return {
    XAU: {
      p: 4050.1,
      label: "Gold spot",
      name: "Gold spot",
      source: "gold-api-spot-proxy",
      displayChangeLabel: "Gold futures (GC=F, delayed 10 min)",
      displayChange: {
        symbol: "GC=F",
        label: "Gold futures (GC=F, delayed 10 min)",
        text: "gold futures (GC=F) −1.43% today",
        note: "Gold spot has no previous close in the free feed, so the change shown is the change in gold futures (GC=F). It is not spot's change.",
        source: "Yahoo Finance"
      },
      futures: { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", price: 4056.9, source: "Yahoo Finance" },
      futuresChange: { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", text: "gold futures (GC=F) −1.43% today", source: "Yahoo Finance" }
    },
    DXY: { p: 102.12, symbol: "DX-Y.NYB", label: "US Dollar Index (ICE, Yahoo DX-Y.NYB)", name: "US Dollar Index (ICE, Yahoo DX-Y.NYB)", source: "Yahoo Finance (DX-Y.NYB)" },
    US10Y: { symbol: "^TNX", label: "US 10-year yield", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)" },
    regime: { label: "Transition", source: "Dispatch regime model", note: "VIX and ^GSPC are inputs" },
    fetchedAt: 1
  };
}

function boot(raw) {
  const sent = [];
  const context = {
    console: console,
    Promise: Promise,
    Object: Object,
    Array: Array,
    String: String,
    marketReferenceQuotesSWR: function () { return Promise.resolve(raw); },
    bb5gPublish: function (data) { return data; },
    json: function (_res, _status, body) { sent.push(body); return body; },
    c95Plain: function (s) { return s; }
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(block, context, { filename: "server_block_c102r6b.js" });
  context.sent = sent;
  return context;
}

test("every reader-facing quotes string loses raw tickers and symbol fields stay", async () => {
  const ctx = boot(liveShape());
  const body = await ctx.marketReferenceQuotesSWR();
  assert.equal(body.XAU.displayChange.label, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChangeLabel, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChange.text, "gold futures (COMEX, front month) −1.43% today");
  assert.match(body.XAU.displayChange.note, /gold futures \(COMEX, front month\)/);
  assert.equal(body.XAU.displayChange.note.includes("GC=F"), false);
  assert.equal(body.US10Y.source, "Yahoo Finance (CBOE 10-year Treasury yield index)");
  assert.equal(body.XAU.displayChange.symbol, "GC=F");
  assert.equal(body.XAU.futures.symbol, "GC=F");
  assert.equal(body.US10Y.symbol, "^TNX");
  assert.equal(body.DXY.symbol, "DX-Y.NYB");
  const readers = [];
  readerStrings(body, "", readers);
  const bad = readers.filter(function (s) { return RX.test(s); });
  assert.deepEqual(bad, []);
  const published = ctx.bb5gPublish(liveShape());
  const viaJson = ctx.json(null, 200, liveShape());
  [published, viaJson].forEach(function (out) {
    const found = [];
    readerStrings(out, "", found);
    assert.deepEqual(found.filter(function (s) { return RX.test(s); }), []);
  });
  assert.equal(ctx.sent[0].US10Y.symbol, "^TNX");
});

test("a later writer cannot put a ticker back into a label", async () => {
  const ctx = boot({ XAU: { p: 1, label: "Gold spot" }, US10Y: { symbol: "^TNX", value: 4, source: "Yahoo Finance" } });
  ctx.bb5gPublish = function (data) {
    const out = Object.assign({}, data);
    out.XAU = Object.assign({}, data.XAU, { displayChangeLabel: "Gold futures (GC=F, delayed 10 min)" });
    return out;
  };
  vm.runInContext(block, ctx);
  const out = ctx.bb5gPublish({ XAU: { p: 1, label: "Gold spot", displayChange: { symbol: "GC=F", text: "gold futures (GC=F) −1.43% today" } }, US10Y: { symbol: "^TNX", source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)" } });
  const found = [];
  readerStrings(out, "", found);
  assert.deepEqual(found.filter(function (s) { return RX.test(s); }), []);
  assert.equal(out.XAU.displayChange.symbol, "GC=F");
});

test("terminal copy does not put raw tickers in reader-facing strings", () => {
  const client = fs.readFileSync(path.join(dir, "..", "deploy-chat102", "client_c102.js"), "utf8");
  const lib = fs.readFileSync(path.join(dir, "..", "deploy-chat102", "lib_c102.js"), "utf8");
  const shown = [];
  const re = /(?:label|source|note|text|name)\s*:\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g;
  [client, lib].join("\n").replace(re, function (_m, lit) {
    if (RX.test(lit)) shown.push(lit);
    return _m;
  });
  assert.deepEqual(shown, []);
  assert.equal(RX.test(client), false);
});

test("the patch appends only server.js onto an r6 file", () => {
  const work = fs.mkdtempSync("/tmp/c102r6b-patch-");
  const server = path.join(work, "server.js");
  fs.writeFileSync(server, "// chat102r6 market-reference cache.\nasync function marketReferenceQuotesSWR(){ return {}; }\n");
  fs.writeFileSync(path.join(work, "app.js"), "app-bytes");
  fs.writeFileSync(path.join(work, "index.html"), "index-bytes");
  const run = spawnSync("python3", [path.join(dir, "patch_c102r6b.py"), server, path.join(dir, "server_block_c102r6b.js")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr);
  const next = fs.readFileSync(server, "utf8");
  assert.match(next, /chat102r6b reader-facing scrub/);
  assert.equal(fs.readFileSync(path.join(work, "app.js"), "utf8"), "app-bytes");
  const check = spawnSync(process.execPath, ["--check", server], { encoding: "utf8" });
  assert.equal(check.status, 0, check.stderr);
  const again = spawnSync("python3", [path.join(dir, "patch_c102r6b.py"), server, path.join(dir, "server_block_c102r6b.js")], { encoding: "utf8" });
  assert.notEqual(again.status, 0);
  assert.match(again.stderr + again.stdout, /already chat102r6b/);
});

test("deploy.sh bytes match EXPECTED_SHA256 on their own", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6b-root-");
  fs.writeFileSync(path.join(root, "server.js"), "// chat102r6 market-reference cache.\nasync function marketReferenceQuotesSWR(){ return {}; }\n");
  fs.writeFileSync(path.join(root, "app.js"), "nope");
  fs.writeFileSync(path.join(root, "index.html"), "nope");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6b\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6b.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /a53eb7ebc9030ed0d1656354b9b8ef78/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6b")), false);
});
