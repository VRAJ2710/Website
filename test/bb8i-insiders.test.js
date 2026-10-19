// Offline tests for the insiders part of deploy/patch_bb8i.py: the real bb7, bb8, bb8d (UK time formatter), bb8h and bb8i
// blocks with a stub SEC (globalThis.bb7Fetch); no network, no live files.
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
const B8D = cut(read("patch_bb8d.py"), "// \u2500\u2500 bb8d \u2500\u2500", "// BB8D_JS_END");
const B8I = cut(read("patch_bb8i.py"), "// \u2500\u2500 bb8i \u2500\u2500", "// BB8I_JS_END");
// No timers at all in bb8i: the retry is request-driven.
for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", ".tier", "process.env"]) assert.equal(B8I.includes(bad), false, bad);

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
      if (sec.down || sec.fail[i]) return { ok: false, status: 503 };
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
  vm.runInContext(B8D, ctx, { filename: "bb8d.js" });
  vm.runInContext(B8H, ctx, { filename: "bb8h.js" });
  vm.runInContext(B8I, ctx, { filename: "bb8i.js" });
  ctx.clock = T0; ctx.bb7Clock = () => ctx.clock + (Date.now() - ctx.real0); ctx.real0 = Date.now();
  ctx.bb7Reset();
  return ctx;
}
const PREM = { premium: true }, FREE = { premium: false };
const settle = async (c, ms) => { const end = Date.now() + ms; while (Date.now() < end && vm.runInContext("bb7Inflight.size", c)) await new Promise(r => setTimeout(r, 20)); };
async function primed() {
  const c = load();
  c.bb8InsidersBudgetMs = 20000;
  const r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "fresh");
  c.clock += 7 * 3600e3; // past the 6 h TTL
  return c;
}
const subs = c => c.sec.subs || 0;

test("b) premium: a failed refresh serves the older complete entry as stale, labelled with its UK time; the entry stays", async () => {
  const c = await primed();
  const mem = vm.runInContext("bb7Mem", c), before = mem.get("f4:NVDA");
  c.sec.fail[12] = true;
  const r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  assert.ok(r.headers["X-Dispatch-As-Of"]);
  assert.equal(r.body.stale, true);
  assert.equal(r.body.meta.stale, true);
  assert.equal(r.body.meta.partial, undefined);
  assert.equal(r.body.meta.window.filings, 40);
  const label = "Updated " + c.bb8dUk(before.at) + " \u00b7 refreshing";
  assert.match(label, /^Updated \w{3} \d{1,2} \w{3}, \d{2}:\d{2} UK \u00b7 refreshing$/);
  assert.equal(r.body.meta.statusLabel, label);
  assert.equal(r.body.meta.window.note, label);
  assert.equal(r.body.insider.length, 40);
  assert.equal(mem.get("f4:NVDA"), before, "complete entry kept in place");
});

test("b) request-driven backoff: 60 s, then doubling; no scan inside it; success clears it", async () => {
  const c = await primed();
  c.sec.fail[12] = true;
  await c.bb7Load("NVDA", PREM);
  assert.equal(vm.runInContext("bb8iBack.get('f4:NVDA').fails", c), 1);
  let n = c.sec.calls, r = await c.bb7Load("NVDA", PREM);
  assert.equal(c.sec.calls, n, "inside 60 s: no SEC request");
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  c.clock += 61e3; n = c.sec.calls; r = await c.bb7Load("NVDA", PREM);
  assert.ok(c.sec.calls > n, "after 60 s the next request starts the refresh");
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(vm.runInContext("bb8iBack.get('f4:NVDA').fails", c), 2);
  c.clock += 61e3; n = c.sec.calls; await c.bb7Load("NVDA", PREM);
  assert.equal(c.sec.calls, n, "inside the doubled 120 s: no SEC request");
  c.clock += 60e3; c.sec.fail = {}; r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "fresh");
  assert.equal(r.body.meta.stale, undefined);
  assert.equal(vm.runInContext("bb8iBack.has('f4:NVDA')", c), false);
  assert.deepEqual([1, 2, 3, 4, 5, 9].map(k => c.bb8iBackoffMs(k) / 1000), [60, 120, 240, 480, 900, 900]);
});

test("b) concurrent premium requests share one refresh and count one failure", async () => {
  const c = await primed();
  c.sec.fail[12] = true;
  const n = c.sec.calls;
  const rs = await Promise.all([1, 2, 3].map(() => c.bb7Load("NVDA", PREM)));
  rs.forEach(r => assert.equal(r.headers["X-Dispatch-Data-Status"], "stale"));
  assert.ok(c.sec.calls - n <= 30, "one scan's worth of requests: " + (c.sec.calls - n));
  assert.equal(vm.runInContext("bb8iBack.get('f4:NVDA').fails", c), 1);
});

test("b) free tier unchanged during a premium backoff; no complete entry keeps bb8h's partial / retry", async () => {
  const c = await primed();
  c.sec.fail[12] = true;
  await c.bb7Load("NVDA", PREM);
  const n = c.sec.calls;
  const f = await c.bb7Load("NVDA", FREE);
  assert.ok(c.sec.calls > n, "free scan runs as before");
  assert.equal(f.headers["X-Dispatch-Data-Status"], "fresh");
  assert.equal(f.body.meta.stale, undefined);
  assert.equal(f.body.insider.length, 5);
  const d = load(); d.bb8InsidersBudgetMs = 20000; d.sec.fail[12] = true;
  const r = await d.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.body.meta.more, "retry");
  assert.equal(r.body.meta.window.filings, 12);
  const m = d.sec.calls; await d.bb7Load("NVDA", PREM);
  assert.ok(d.sec.calls > m, "no backoff without a complete entry: the next request rescans");
});

test("b) a refresh that throws (SEC down) also falls back to the complete entry", async () => {
  const c = await primed();
  c.sec.down = true;
  const r = await c.bb7Load("NVDA", PREM);
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(r.body.meta.stale, true);
  assert.match(r.body.meta.statusLabel, /\u00b7 refreshing$/);
  assert.equal(vm.runInContext("bb8iBack.get('f4:NVDA').fails", c), 1);
});
