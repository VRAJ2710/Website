"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockG = fs.readFileSync(path.join(dir, "server_block_c102r6g.js"), "utf8");
const blockD = fs.readFileSync(path.join(dir, "..", "deploy-chat102r6d", "server_block_c102r6d.js"), "utf8");
const oldBlock = fs.readFileSync(path.join(dir, "server_block_c102r6f.js"), "utf8");

function proseKey(key) {
  const k = String(key || "");
  return /^(note|cacheNote|statusNote|text|label|detail|message|caption|description)$/.test(k) || /(?:Note|Text|Label)$/.test(k);
}
function nonProse(value) {
  if (Array.isArray(value)) return value.map(nonProse);
  if (!value || typeof value !== "object") return value;
  const out = {};
  Object.keys(value).forEach(function (k) {
    if (k === "sourceLabel" || proseKey(k)) return;
    out[k] = nonProse(value[k]);
  });
  return out;
}
function send(block, body) {
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function () {} },
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
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  context.json(res, 200, body);
  return JSON.parse(res.written);
}

function fixture() {
  return {
    fetchedAt: 1794325077671,
    generatedAtUtc: "2026-11-10T18:04:00.000Z",
    XAU: {
      p: 4050.1,
      source: "gold-api-spot-proxy",
      asOf: "2026-11-10T17:51:40.665Z",
      ts: 1794324700,
      displayChangeLabel: "Gold futures (GC=F, delayed 10 min)",
      displayChange: { symbol: "GC=F", text: "gold futures (GC=F) −1.43% today", asOf: "2026-11-10T17:51:40.665Z" },
      futuresChange: { symbol: "GC=F", text: "gold futures (gold futures) -2.18% today", ts: 1794324700 },
      bars: [{ timeUtc: "2026-11-10T05:00:00.000Z", c: 4050.1 }]
    },
    DXY: { p: 102.1, symbol: "DX-Y.NYB", source: "Yahoo Finance (DX-Y.NYB)", name: "US Dollar Index (ICE, Yahoo the ICE dollar index)", detail: "Yahoo Finance (the ICE dollar index)", asOf: "2026-11-10T17:27:55.000Z" },
    US10Y: { symbol: "^TNX", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)", note: "value is in percent (4.99 = 4.99%). Show the % once, in the UI.", asOf: "2026-11-10T17:26:14.000Z" },
    cacheNote: "Stored reading from 2026-11-10T17:51:40.665Z, 3 minutes ago. It was not refreshed for this response. It is not a new print.",
    spot: { price: 4100.25, asOfUtc: "2026-11-10T17:51:40.665Z", source: "gold-api.com", timeUtc: "2026-11-10T05:00:00.000Z" }
  };
}

test("non-prose fields stay equal to the r6d scrub and prose is reader-safe", () => {
  const raw = fixture();
  const d = send(blockD, JSON.parse(JSON.stringify(raw)));
  const g = send(blockG, JSON.parse(JSON.stringify(raw)));
  assert.deepEqual(nonProse(g), nonProse(d));
  assert.equal(g.generatedAtUtc, "2026-11-10T18:04:00.000Z");
  assert.equal(g.XAU.asOf, "2026-11-10T17:51:40.665Z");
  assert.equal(g.XAU.ts, 1794324700);
  assert.equal(g.fetchedAt, 1794325077671);
  assert.equal(g.XAU.bars[0].timeUtc, "2026-11-10T05:00:00.000Z");
  assert.equal(g.spot.asOfUtc, "2026-11-10T17:51:40.665Z");
  assert.equal(g.XAU.source, d.XAU.source);
  assert.equal(g.DXY.source, d.DXY.source);
  assert.equal(g.XAU.futuresChange.text, "gold futures (COMEX, front month) −2.18% today");
  assert.equal(g.DXY.detail, "Yahoo Finance (ICE US Dollar Index)");
  assert.equal(g.DXY.sourceLabel, "Yahoo Finance, ICE US Dollar Index");
  assert.equal(g.US10Y.sourceLabel, "Yahoo Finance, CBOE 10-year Treasury yield index");
  assert.equal(g.US10Y.note, "Yield in percent.");
  assert.equal(g.cacheNote, "Stored reading from Tue 10 Nov, 17:51 UK, 3 minutes ago. It was not refreshed for this response. It is not a new print.");
  assert.equal(g.XAU.sourceLabel, "gold-api.com spot price");
});

test("the terminal client parses machine times and only prints prose", () => {
  const client = fs.readFileSync(path.join(dir, "..", "deploy-chat102", "client_c102.js"), "utf8");
  assert.match(client, /uk\(row\.asOfUtc\)/);
  assert.match(client, /uk\(model\.generatedAtUtc\)/);
  assert.match(client, /bar\.timeUtc/);
  assert.match(client, /esc\(model\.cacheNote\)/);
  assert.equal(/Date\.parse\([^)]*cacheNote/.test(client), false);
  assert.equal(/new Date\([^)]*cacheNote/.test(client), false);
  assert.equal(/new Date\([^)]*\.note/.test(client), false);
  assert.equal(/new Date\([^)]*\.label/.test(client), false);
  assert.equal(/new Date\([^)]*\.message/.test(client), false);
  const app = "/tmp/c102hash/app.js";
  if (fs.existsSync(app)) {
    const src = fs.readFileSync(app, "utf8");
    const fn = src.slice(src.indexOf("function fe64_plainNote"), src.indexOf("var fe84_ukHmFmt"));
    assert.equal(/Date\.parse|new Date/.test(fn), false);
    assert.match(fn, /return s/);
  }
});

test("replacing the scrub block leaves the CPI prefix byte-identical and keeps the block last", () => {
  const work = fs.mkdtempSync("/tmp/c102r6g-patch-");
  const server = path.join(work, "server.js");
  const cpi = "/* CPI y/y wording. Do not edit. */\nfunction cpiNote(){ return \"year on year\"; }\n";
  fs.writeFileSync(server, cpi + oldBlock);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6g.py"),
    server,
    path.join(dir, "server_block_c102r6f.js"),
    path.join(dir, "server_block_c102r6g.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  const fresh = blockG.endsWith("\n") ? blockG : blockG + "\n";
  assert.equal(after.slice(0, cpi.length), cpi);
  assert.equal(after.endsWith(fresh), true);
  assert.equal(after.slice(0, after.length - fresh.length), cpi);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
});
