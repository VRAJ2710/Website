// Offline tests for the insiders part of deploy/patch_bb8h.py: the real bb7 and bb8 blocks plus bb8h, with a stub
// SEC (globalThis.bb7Fetch); no network, no live files.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const cut = (src, a, b) => { const i = src.indexOf(a), j = src.indexOf(b); assert.ok(i > 0 && j > i, a); return src.slice(i, j + b.length); };
const B7 = cut(read("patch_bb7.py"), "// BB7_JS\n", "// BB7_JS_END");
const B8 = cut(read("patch_bb8.py"), "// \u2500\u2500 bb8 \u2500\u2500", "// BB8_JS_END");
const B8H = cut(read("patch_bb8h.py"), "// \u2500\u2500 bb8h \u2500\u2500", "// BB8H_JS_END");
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env"]) assert.equal(B8H.includes(bad), false, bad);

const T0 = Date.parse("2026-10-19T08:00:00Z");
const day = n => new Date(T0 - n * 86400000).toISOString().slice(0, 10);
// 60 Form 4 filings, one every 5 days; each holds one open-market sale, so a free scan stops after 5 filings.
const N = 60;
const form = i => `<ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>Insider ${i}</rptOwnerName></reportingOwnerId></reportingOwner><nonDerivativeTable><nonDerivativeTransaction><transactionDate><value>${day(i * 5)}</value></transactionDate><transactionCoding><transactionCode>S</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>100</value></transactionShares><transactionPricePerShare><value>10</value></transactionPricePerShare><transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode></transactionAmounts></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>`;
function load() {
  const ctx = { console: { warn() {} }, Date, Intl, Number, String, isFinite, Object, Array, Math, RegExp, JSON, Error, process, Buffer, require, AbortSignal, URL, encodeURIComponent, setTimeout, clearTimeout, Promise, Map, Set };
  ctx.globalThis = ctx;
  ctx.hasPremiumAccess = u => !!(u && u.admin === true);
  vm.createContext(ctx);
  const sec = ctx.sec = { lat: 0, slow: {}, fail: {}, gone: {}, calls: 0, inflight: 0, maxInflight: 0 };
  ctx.bb7SleepHook = ms => { ctx.clock += ms; }; // the old bb7 10/s bucket (bb8f is not loaded here) waits on the test clock
  ctx.bb7Fetch = async function (url) {
    sec.calls++; sec.inflight++; sec.maxInflight = Math.max(sec.maxInflight, sec.inflight);
    try {
      const m = /\/000104581026(\d{6})\//.exec(url), i = m ? Number(m[1]) : -1;
      await new Promise(r => setTimeout(r, (sec.slow[i] || 0) + sec.lat));
      if (sec.fail[i]) return { ok: false, status: 503 };
      if (sec.gone[i]) return { ok: false, status: 404 };
      let body;
      if (/company_tickers/.test(url)) body = JSON.stringify({ 0: { ticker: "NVDA", cik_str: 1045810, title: "NVIDIA" } });
      else if (/submissions/.test(url)) body = JSON.stringify({ name: "NVIDIA", filings: { recent: { form: Array(N).fill("4"), filingDate: Array.from({ length: N }, (_, k) => day(k * 5)), accessionNumber: Array.from({ length: N }, (_, k) => "0001045810-26-" + String(k).padStart(6, "0")), primaryDocument: Array(N).fill("xslF345X05/form4.xml") } } });
      else body = form(i);
      return { ok: true, status: 200, text: async () => body };
    } finally { sec.inflight--; }
  };
  vm.runInContext(B7, ctx, { filename: "bb7.js" });
  vm.runInContext(B8, ctx, { filename: "bb8.js" });
  vm.runInContext(B8H, ctx, { filename: "bb8h.js" });
  ctx.clock = T0; ctx.bb7Clock = () => ctx.clock + (Date.now() - ctx.real0); ctx.real0 = Date.now();
  ctx.bb7Reset();
  return ctx;
}
const PREM = { premium: true }, FREE = { premium: false };
const settle = async (c, ms) => { const end = Date.now() + ms; while (Date.now() < end && vm.runInContext("bb7Inflight.size", c)) await new Promise(r => setTimeout(r, 20)); };

test("5) root cause: a free scan no longer stands in for the premium window, and never overwrites the complete entry", async () => {
  const c = load();
  c.bb8InsidersBudgetMs = 20000;
  let r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "fresh");
  assert.equal(r.body.meta.window.filings, 40);
  const full = r.body.meta.window.label;
  assert.equal(full, "Last 6 months");
  c.clock += 7 * 3600e3; // past the 6 h TTL
  r = await c.bb7Load("NVDA", FREE);
  assert.equal(r.body.insider.length, 5);
  const mem = vm.runInContext("bb7Mem", c);
  assert.equal(mem.get("f4:NVDA").body.scanned, 40, "complete premium entry kept");
  assert.equal(mem.get("f4:NVDA").body.complete, true);
  assert.equal(mem.get("f4:NVDA:free").body.scope, "free");
  // Cold premium scan that misses the cap: answered from the complete (stale) premium entry, not the 5-filing free scan.
  c.sec.lat = 200; c.bb8InsidersBudgetMs = 300;
  r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(r.body.meta.window.label, full);
  assert.equal(r.body.meta.window.filings, 40);
  await settle(c, 8000);
  assert.equal(mem.get("f4:NVDA").body.scanned, 40);
});

test("5) before-bb8h entries holding a free scan under the premium key are dropped, never served as a premium window", async () => {
  const c = load();
  vm.runInContext("bb7Remember('f4:NVDA', { ticker: 'NVDA', rows: [], complete: false, filings: 60, scanned: 4, newestFiling: '2026-10-19', oldestFiling: '2026-10-04' }, bb7FormTtl, bb7Now())", c);
  c.sec.lat = 100; c.bb8InsidersBudgetMs = 250;
  const r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.notEqual(r.body.meta.window.label, "Last 2 weeks");
  await settle(c, 8000);
});

test("5) a filing that fails twice ends the scan as partial; it is not cached and does not replace a complete entry", async () => {
  const c = load();
  c.bb8InsidersBudgetMs = 20000;
  let r = await c.bb7Load("NVDA", PREM);
  const mem = vm.runInContext("bb7Mem", c);
  const at = mem.get("f4:NVDA").at;
  c.clock += 7 * 3600e3;
  c.sec.fail[12] = true;
  r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.headers["Cache-Control"], "no-store");
  assert.equal(r.body.meta.partial, true);
  assert.equal(r.body.meta.more, "retry");
  assert.equal(r.body.meta.window.partial, true);
  assert.equal(r.body.meta.window.filings, 12, "window covers the 12 filings before the failed one");
  assert.equal(r.body.meta.window.from, day(55));
  assert.equal(r.body.insider.length, 12);
  assert.equal(mem.get("f4:NVDA").at, at, "complete entry untouched");
  assert.equal(mem.get("f4:NVDA").body.scanned, 40);
  // A transient failure is retried once; SEC 404 for one filing is a real answer and the scan completes.
  const d = load(); d.bb8InsidersBudgetMs = 20000; d.sec.gone[3] = true;
  r = await d.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "fresh");
  assert.equal(r.body.meta.window.filings, 40);
  assert.equal(r.body.insider.length, 39);
});

test("4) cap: answer within the cap with what is ready, flagged partial, while the same scan fills the cache", async () => {
  const c = load();
  assert.equal(vm.runInContext("bb8hCap()", c), 6500);
  c.bb8InsidersBudgetMs = 600;
  c.sec.lat = 60;
  const t0 = Date.now();
  let r = await c.bb7Load("NVDA", PREM);
  const ms = Date.now() - t0;
  assert.ok(ms >= 580 && ms < 900, "answered at the cap: " + ms);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.headers["X-Dispatch-As-Of"], undefined);
  assert.equal(r.body.meta.partial, true);
  assert.equal(r.body.meta.more, "loading");
  assert.equal(r.body.note, "More filings loading \u2014 refresh shortly");
  const w = r.body.meta.window;
  assert.equal(w.partial, true);
  assert.ok(w.filings > 0 && w.filings < 40);
  assert.equal(r.body.insider.length, w.filings);
  assert.equal(w.from, day((w.filings - 1) * 5), "window is the loaded filings");
  assert.equal(vm.runInContext("bb7Recall('f4:NVDA')", c), null, "partial never cached");
  await settle(c, 10000);
  r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "fresh");
  assert.equal(r.body.meta.partial, undefined);
  assert.equal(r.body.meta.window.filings, 40);
  assert.ok(c.sec.maxInflight > 1 && c.sec.maxInflight <= 4, "filings load 4 at a time: " + c.sec.maxInflight);
});

test("4/5) out-of-order loads: the window and rows only cover the unbroken run from the newest filing", async () => {
  const c = load();
  c.bb8InsidersBudgetMs = 400;
  c.sec.slow[0] = 1500; // newest filing is slow; later ones arrive first
  const r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.body.insider.length, 0);
  assert.equal(r.body.meta.window.label, "Loading filings");
  assert.equal(r.body.meta.window.filings, 0);
  assert.equal(r.body.note, "More filings loading \u2014 refresh shortly");
  await settle(c, 10000);
  assert.equal(vm.runInContext("bb7Recall('f4:NVDA').body.complete", c), true);
});

test("5) older pages: a scan with a failed filing is partial and not cached as complete", async () => {
  const c = load();
  c.sec.fail[45] = true;
  const r = await c.bb8Older("NVDA", day(100), { codes: "PS" });
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.body.meta.partial, true);
  assert.equal(r.body.meta.window.filings, 24, "filings 21..44 load, 45 fails");
  const key = "f4:NVDA<" + day(100) + ":PS";
  assert.equal(vm.runInContext("bb7Recall(" + JSON.stringify(key) + ")", c), null);
});
