"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const block = fs.readFileSync(path.join(dir, "server_block_c102r6f.js"), "utf8");
const oldBlock = fs.readFileSync(path.join(dir, "server_block_c102r6d.js"), "utf8");
const TICKER = /GC=F|DX-Y|\^TNX|=X\b|\^VIX|\^GSPC|CL=F|BTC-USD|\^[A-Z]{2,8}\b|\b[A-Z]{1,4}=F\b/;
const ISO = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;
const MACHINE = /\b(?:gold-api-spot-proxy(?:-browser)?|dxy-fx-computed)\b/;
const DOUBLED = /\b([A-Za-z]+(?: [A-Za-z]+){0,3}) \(\1\)|Yahoo the\b/i;

function skipKey(key) {
  return key === "symbol" || key === "symbols" || key === "source" || key === "sourceId" || /(?:Id|Url|Key|Code)$/.test(String(key || ""));
}
function walk(value, key, acc) {
  if (typeof value === "string") {
    if (!skipKey(key)) acc.push(value);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(function (item) { walk(item, key, acc); });
    return;
  }
  if (value && typeof value === "object") Object.keys(value).forEach(function (k) { walk(value[k], k, acc); });
}
function audit(body) {
  const rows = [];
  walk(body, "", rows);
  return rows.filter(function (s) { return TICKER.test(s) || ISO.test(s) || MACHINE.test(s) || DOUBLED.test(s); });
}

function boot() {
  const logs = [];
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function (line) { logs.push(String(line)); } },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer: Buffer,
    JSON: JSON,
    Object: Object,
    Array: Array,
    String: String,
    Intl: Intl,
    Date: Date,
    isFinite: isFinite
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext("function json(res, status, body) { res.end(JSON.stringify(body)); }", context);
  vm.runInContext(block, context);
  context.logs = logs;
  context.send = function (body) {
    const Ctor = context.require("http").ServerResponse;
    const res = new Ctor();
    context.json(res, 200, body);
    return JSON.parse(res.written);
  };
  return context;
}

test("wording is plained and source stays the r6d machine id", () => {
  const ctx = boot();
  const quotes = ctx.send({
    XAU: {
      p: 4050.1,
      source: "gold-api-spot-proxy",
      asOf: "2026-11-10T17:51:40.665Z",
      displayChangeLabel: "Gold futures (gold futures, delayed 10 min)",
      displayChange: {
        symbol: "GC=F",
        label: "Gold futures (GC=F, delayed 10 min)",
        text: "gold futures (GC=F) −1.43% today",
        note: "the change shown is the change in gold futures (GC=F).",
        sourceUrl: "https://finance.yahoo.com/quote/GC=F"
      },
      futuresChange: {
        symbol: "GC=F",
        text: "gold futures (gold futures) -2.18% today",
        source: "Yahoo Finance (the ICE dollar index)",
        label: "Yahoo Finance (the ICE dollar index)"
      }
    },
    DXY: {
      p: 102.1,
      symbol: "DX-Y.NYB",
      name: "US Dollar Index (ICE, Yahoo the ICE dollar index)",
      source: "dxy-fx-computed",
      fallbackReason: "Yahoo DX-Y.NYB unavailable; this is the Dispatch FX basket"
    },
    US10Y: { symbol: "^TNX", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)" }
  });
  const terminal = ctx.send({
    cacheState: "stale",
    cacheNote: "Stored reading from 2026-11-10T17:51:40.665Z, 3 minutes ago. It was not refreshed for this response. It is not a new print.",
    spot: { price: 4100.25, source: "gold-api.com", asOfUtc: "2026-11-10T17:51:40.665Z" },
    dollar: { price: 102.1, source: "Yahoo Finance (DX-Y.NYB)", symbol: "DX-Y.NYB" }
  });
  assert.equal(quotes.XAU.source, "gold-api-spot-proxy");
  assert.equal(quotes.DXY.source, "dxy-fx-computed");
  assert.equal(quotes.XAU.futuresChange.source, "Yahoo Finance (the ICE dollar index)");
  assert.equal(quotes.US10Y.source, "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)");
  assert.equal(quotes.XAU.sourceLabel, "gold-api.com spot price");
  assert.equal(quotes.DXY.sourceLabel, "Dispatch FX basket (our calculation from Yahoo Finance FX rates)");
  assert.equal(quotes.XAU.futuresChange.text, "gold futures (COMEX, front month) −2.18% today");
  assert.equal(quotes.XAU.futuresChange.label, "Yahoo Finance (ICE US Dollar Index)");
  assert.equal(quotes.XAU.displayChange.symbol, "GC=F");
  assert.equal(terminal.cacheNote, "Stored reading from Tue 10 Nov, 17:51 UK, 3 minutes ago. It was not refreshed for this response. It is not a new print.");
  assert.equal(terminal.spot.source, "gold-api.com");
  assert.deepEqual(audit(quotes), []);
  assert.deepEqual(audit(terminal), []);
  assert.ok(ctx.logs.some(function (line) { return line === "[c102r6c] scrub attached"; }));
});

test("replacing the scrub block leaves the CPI prefix byte-identical and keeps the block last", () => {
  const work = fs.mkdtempSync("/tmp/c102r6f-patch-");
  const server = path.join(work, "server.js");
  const cpi = "/* CPI y/y wording. Do not edit. */\nfunction cpiNote(){ return \"year on year\"; }\n";
  fs.writeFileSync(server, cpi + oldBlock);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6f.py"),
    server,
    path.join(dir, "server_block_c102r6d.js"),
    path.join(dir, "server_block_c102r6f.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  const fresh = block.endsWith("\n") ? block : block + "\n";
  assert.equal(after.slice(0, cpi.length), cpi);
  assert.equal(after.endsWith(fresh), true);
  assert.equal(after.slice(0, after.length - fresh.length), cpi);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
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
  const root = fs.mkdtempSync("/tmp/c102r6f-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + oldBlock);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6f\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6f.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /d0a74a6c26e3a8dd7dcbf8ad0939f926/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6f")), false);
});
