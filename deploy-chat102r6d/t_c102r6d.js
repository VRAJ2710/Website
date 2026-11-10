"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const block = fs.readFileSync(path.join(dir, "server_block_c102r6d.js"), "utf8");
const oldBlock = fs.readFileSync(path.join(dir, "server_block_c102r6c.js"), "utf8");
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
  if (value && typeof value === "object") Object.keys(value).forEach(function (k) { readerStrings(value[k], k, acc); });
}

test("doubled phrases and fallback reasons are plained at the last write", () => {
  const logs = [];
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function (line) { logs.push(String(line)); } },
    require: function (name) {
      if (name !== "http") throw new Error(name);
      return { ServerResponse: Res };
    },
    Buffer: Buffer,
    JSON: JSON,
    Object: Object,
    Array: Array,
    String: String
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(`
    function addRaw(body) { return body; }
    function json(res, status, body) {
      res.end(JSON.stringify(body));
    }
  `, context);
  vm.runInContext(block, context);
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  context.json(res, 200, {
    XAU: {
      p: 4050.1,
      label: "Gold spot",
      displayChangeLabel: "Gold futures (gold futures, delayed 10 min)",
      displayChange: {
        symbol: "GC=F",
        label: "Gold futures (GC=F, delayed 10 min)",
        text: "gold futures (GC=F) −1.43% today",
        note: "the change shown is the change in gold futures (GC=F)."
      }
    },
    DXY: {
      p: 102.1,
      symbol: "DX-Y.NYB",
      name: "US Dollar Index (ICE, Yahoo the ICE dollar index)",
      label: "US Dollar Index (ICE, Yahoo DX-Y.NYB)",
      fallbackReason: "Yahoo DX-Y.NYB unavailable; this is the Dispatch FX basket"
    },
    US10Y: { symbol: "^TNX", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)" }
  });
  const body = JSON.parse(res.written);
  assert.equal(body.XAU.displayChangeLabel, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChange.label, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChange.text, "gold futures (COMEX, front month) −1.43% today");
  assert.equal(body.DXY.name, "US Dollar Index (ICE), Yahoo Finance");
  assert.equal(body.DXY.label, "US Dollar Index (ICE), Yahoo Finance");
  assert.equal(body.DXY.fallbackReason, "Yahoo's ICE dollar index was unavailable; this is the Dispatch FX basket");
  assert.equal(body.DXY.symbol, "DX-Y.NYB");
  assert.equal(body.XAU.displayChange.symbol, "GC=F");
  assert.equal(body.US10Y.source, "Yahoo Finance (CBOE 10-year Treasury yield index)");
  const readers = [];
  readerStrings(body, "", readers);
  const bad = readers.filter(function (s) { return RX.test(s) || /Gold futures \(gold futures/i.test(s) || /Yahoo the/.test(s); });
  assert.deepEqual(bad, []);
  assert.ok(logs.some(function (line) { return line === "[c102r6c] scrub attached"; }));
});

test("replacing the scrub block leaves the CPI prefix byte-identical and keeps the block last", () => {
  const work = fs.mkdtempSync("/tmp/c102r6d-patch-");
  const server = path.join(work, "server.js");
  const cpi = "/* CPI y/y wording. Do not edit. */\nfunction cpiNote(){ return \"year on year\"; }\n";
  fs.writeFileSync(server, cpi + oldBlock);
  const before = fs.readFileSync(server);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6d.py"),
    server,
    path.join(dir, "server_block_c102r6c.js"),
    path.join(dir, "server_block_c102r6d.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  assert.equal(after.startsWith(cpi), true);
  assert.equal(after.endsWith(block.endsWith("\n") ? block : block + "\n"), true);
  const outside = before.toString("utf8").replace(oldBlock, "");
  const newBlock = block.endsWith("\n") ? block : block + "\n";
  assert.equal(after.slice(0, after.length - newBlock.length), outside);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  const again = spawnSync("python3", [
    path.join(dir, "patch_c102r6d.py"),
    server,
    path.join(dir, "server_block_c102r6c.js"),
    path.join(dir, "server_block_c102r6d.js")
  ], { encoding: "utf8" });
  assert.notEqual(again.status, 0);
  assert.match(again.stderr + again.stdout, /matched 0 times/);
});
