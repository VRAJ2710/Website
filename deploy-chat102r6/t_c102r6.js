"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const block = fs.readFileSync(path.join(dir, "server_block_c102r6.js"), "utf8");

function boot(swr, fetchImpl, publish) {
  const context = {
    console: console,
    Date: Date,
    Intl: Intl,
    Promise: Promise,
    Object: Object,
    Array: Array,
    String: String,
    Number: Number,
    RegExp: RegExp,
    Error: Error,
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    AbortController: AbortController,
    fetch: fetchImpl || (async () => { throw new Error("unexpected fetch"); }),
    marketReferenceQuotesSWR: swr,
    bb5gPublish: publish || function (data) {
      if (!data || typeof data !== "object") return data;
      const out = Object.assign({}, data);
      if (out.XAU && typeof out.XAU.p === "number") out.XAU = Object.assign({}, out.XAU, { note: "classifier replaced the note" });
      return out;
    },
    C102R6_NO_WARM: true,
    C102R6_TTL: 0
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(block, context, { filename: "server_block_c102r6.js" });
  return context;
}

function goodGold() {
  return {
    XAU: {
      p: 4100.25,
      label: "Gold futures (GC=F, delayed 10 min)",
      name: "Gold spot",
      source: "gold-api.com",
      asOf: "2026-11-10T15:37:32.000Z",
      asOfUk: "Tue 10 Nov, 15:37 UK",
      futures: { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", price: 4056.9, asOfUk: "Tue 10 Nov, 15:27 UK" }
    },
    DXY: { p: 102.124, label: "US Dollar Index (ICE, Yahoo DX-Y.NYB)", name: "US Dollar Index (ICE, Yahoo DX-Y.NYB)", source: "Yahoo Finance (DX-Y.NYB)", asOfUk: "Tue 10 Nov, 15:27 UK", symbol: "DX-Y.NYB" },
    DXY_FX: { p: 102.17, label: "Dispatch FX basket", asOfUk: "Tue 10 Nov, 15:37 UK" },
    US10Y: { symbol: "^TNX", label: "US 10-year yield", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)", asOfUk: "Tue 10 Nov, 15:26 UK" },
    regime: { available: true, regime: "Transition", score: 44, label: "Transition", asOfUk: "Tue 10 Nov, 15:31 UK" },
    sessionSummary: { text: "8 of 13 markets trading now", tradingNow: 8, asOfUk: "Tue 10 Nov, 15:41 UK" },
    fetchedAt: 1
  };
}

test("a hung upstream does not delay the reference quotes response", async () => {
  let calls = 0;
  const ctx = boot(function () {
    calls += 1;
    return new Promise(function () {});
  });
  const t0 = Date.now();
  const first = await ctx.marketReferenceQuotesSWR();
  const second = await ctx.marketReferenceQuotesSWR();
  const dt = Date.now() - t0;
  assert.ok(dt < 250, "response took " + dt);
  assert.equal(first.XAU.p, null);
  assert.equal(first.US10Y.value, null);
  assert.equal(first.regime.score, null);
  assert.match(first.XAU.note, /No stored reading yet/);
  assert.match(first.XAU.note, /No number was filled in/);
  assert.equal(second.XAU.p, null);
  assert.equal(calls, 1);
  assert.equal(JSON.stringify(first).includes("4100"), false);
});

test("a timed-out refresh keeps the last good feed and its UK time", async () => {
  let mode = "ok";
  const ctx = boot(async function () {
    if (mode === "ok") return goodGold();
    return {
      XAU: { p: null, status: "timeout", note: "No number was filled in." },
      DXY: { p: 99.5, label: "US dollar index", asOfUk: "Tue 10 Nov, 15:40 UK", source: "Yahoo Finance" },
      US10Y: { value: null, note: "No number was filled in." }
    };
  });
  await ctx.marketReferenceQuotesSWR();
  await new Promise((r) => setTimeout(r, 30));
  const t0 = Date.now();
  mode = "bad";
  const during = await ctx.marketReferenceQuotesSWR();
  assert.ok(Date.now() - t0 < 250, "stale read took " + (Date.now() - t0));
  assert.equal(during.XAU.p, 4100.25);
  assert.equal(during.DXY.symbol, "DX-Y.NYB");
  assert.equal(during.DXY.label.includes("DX-Y.NYB"), false);
  assert.equal(during.XAU.label.includes("GC=F"), false);
  assert.equal(during.US10Y.source.includes("^TNX"), false);
  await new Promise((r) => setTimeout(r, 30));
  const after = await ctx.marketReferenceQuotesSWR();
  assert.equal(after.XAU.p, 4100.25);
  assert.equal(after.XAU.asOfUk, "Tue 10 Nov, 15:37 UK");
  assert.equal(after.XAU.source, "gold-api.com");
  assert.match(after.XAU.note, /Stored reading from Tue 10 Nov, 15:37 UK/);
  assert.match(after.XAU.note, /It is not a new print/);
  assert.equal(after.DXY.p, 99.5);
  assert.equal(String(after.DXY.note || "").includes("not a new print"), false);
  assert.equal(after.US10Y.value, 4.99);
  assert.match(after.US10Y.note, /Stored reading from Tue 10 Nov, 15:26 UK/);
  assert.equal(JSON.stringify(after.XAU).includes("No number was filled in"), false);
  const published = ctx.bb5gPublish(after);
  assert.match(published.XAU.note, /It is not a new print/);
});

test("a cold start that fails stays empty", async () => {
  const ctx = boot(async function () {
    return { XAU: { p: null, status: "timeout" }, DXY: { p: null }, US10Y: { value: null }, regime: { available: false }, sessionSummary: { text: "" } };
  });
  const t0 = Date.now();
  const first = await ctx.marketReferenceQuotesSWR();
  assert.ok(Date.now() - t0 < 250);
  await new Promise((r) => setTimeout(r, 20));
  const second = await ctx.marketReferenceQuotesSWR();
  assert.equal(second.XAU.p, null);
  assert.equal(second.DXY.p, null);
  assert.equal(second.US10Y.value, null);
  assert.match(second.XAU.note, /No number was filled in/);
  assert.equal(JSON.stringify(second).includes("4100"), false);
  assert.equal(first.fetchedAt > 0, true);
});

test("the background refresh aborts gold-api at 3s and other feeds at 2s", async () => {
  const seen = {};
  const ctx = boot(async function () { return { XAU: { p: null } }; }, function (url, opts) {
    return new Promise(function (_resolve, reject) {
      const t0 = Date.now();
      const signal = opts && opts.signal;
      if (!signal) throw new Error("missing abort signal");
      signal.addEventListener("abort", function () {
        seen[String(url)] = Date.now() - t0;
        reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
      });
    });
  });
  vm.runInContext("marketReferenceQuotesSWR = async function () { await Promise.all([fetch('https://api.gold-api.com/price/XAU'), fetch('https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX')]); return { XAU: { p: null } }; };", ctx);
  vm.runInContext(block, ctx);
  const t0 = Date.now();
  const body = await ctx.marketReferenceQuotesSWR();
  assert.ok(Date.now() - t0 < 250, "cold read took " + (Date.now() - t0));
  assert.equal(body.XAU.p, null);
  await new Promise((r) => setTimeout(r, 3400));
  const yahoo = seen["https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX"];
  const gold = seen["https://api.gold-api.com/price/XAU"];
  assert.ok(yahoo > 1500 && yahoo < 2500, "yahoo abort " + yahoo);
  assert.ok(gold > 2500 && gold < 3500, "gold abort " + gold);
});

test("the patch appends only server.js and a second run refuses", () => {
  const work = fs.mkdtempSync("/tmp/c102r6-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  fs.writeFileSync(server, "async function marketReferenceQuotesSWR(){ return { XAU: { p: 1 } }; }\n");
  fs.writeFileSync(app, "app-bytes");
  fs.writeFileSync(index, "index-bytes");
  const run = spawnSync("python3", [path.join(dir, "patch_c102r6.py"), server, path.join(dir, "server_block_c102r6.js")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr);
  const next = fs.readFileSync(server, "utf8");
  assert.match(next, /chat102r6 market-reference cache/);
  assert.equal(fs.readFileSync(app, "utf8"), "app-bytes");
  assert.equal(fs.readFileSync(index, "utf8"), "index-bytes");
  const check = spawnSync(process.execPath, ["--check", server], { encoding: "utf8" });
  assert.equal(check.status, 0, check.stderr);
  const again = spawnSync("python3", [path.join(dir, "patch_c102r6.py"), server, path.join(dir, "server_block_c102r6.js")], { encoding: "utf8" });
  assert.notEqual(again.status, 0);
  assert.match(again.stderr + again.stdout, /already chat102r6/);
  assert.equal(/create table|drop table/i.test(block), false);
});
