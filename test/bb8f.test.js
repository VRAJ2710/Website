// Offline tests for deploy/patch_bb8f.py: one shared SEC limiter, at most 10 request starts in any rolling 1000 ms.
// Loads the bb7 block (patch_bb7.py), the server's rt32/bb8c companyfacts code (verbatim) and the bb8f block, with a
// stub fetch. No network.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const p7 = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb7.py"), "utf8");
const bb7 = p7.slice(p7.indexOf("// BB7_JS\n"), p7.indexOf("// BB7_JS_END") + 13);
const pf = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8f.py"), "utf8");
const bb8f = pf.slice(pf.indexOf("// \u2500\u2500 bb8f \u2500\u2500"), pf.indexOf("// BB8F_JS_END") + 14);
assert.ok(bb7.length > 1000 && bb8f.length > 1000);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe.webhooks", ".tier", "\"User-Agent\":"]) assert.equal(bb8f.includes(bad), false, bad);
assert.match(pf, /3fb9d02cb61081cec1d58484b1aef905/);

// Verbatim from server.js (rt32s fundamentals + bb8c companyfacts).
const FIN = `const RT32 = { cache: new Map(), inflight: new Map(), cik: null, cikAt: 0, cikP: null, ck: "", crumb: "", crumbAt: 0, crumbP: null };
const RT32_UA = "TheDispatch support@thedispatch.uk";
const RT32_BUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
function rt32Get(u, headers) { return fetch(u, { headers: headers || {}, signal: AbortSignal.timeout(8000), redirect: "follow" }); }
async function rt32CikMap() {
  if (RT32.cik && Date.now() - RT32.cikAt < 7 * 864e5) return RT32.cik;
  if (!RT32.cikP) RT32.cikP = (async () => {
    const r = await rt32Get("https://www.sec.gov/files/company_tickers.json", { "User-Agent": RT32_UA, Accept: "application/json" });
    if (!r.ok) throw new Error("sec tickers " + r.status);
    const j = await r.json(), m = new Map();
    for (const v of Object.values(j)) if (v && v.ticker) m.set(String(v.ticker).toUpperCase(), { cik: String(v.cik_str).padStart(10, "0"), name: v.title });
    RT32.cik = m; RT32.cikAt = Date.now(); return m;
  })().finally(() => { RT32.cikP = null; });
  return RT32.cikP;
}
async function bb8cSec(sym) {
  if (typeof bb8bForeign === "function" && bb8bForeign(sym)) return null;
  var m = await rt32CikMap();
  var e = m.get(sym) || m.get(String(sym).replace(/\./g, "-"));
  if (!e) return null;
  var r = await rt32Get("https://data.sec.gov/api/xbrl/companyfacts/CIK" + e.cik + ".json", { "User-Agent": RT32_UA, Accept: "application/json" });
  if (!r.ok) throw new Error("sec facts " + r.status);
  var j = await r.json();
  var s = rt32Sec(j.facts);
  s.name = e.name;
  return s;
}
function rt32Sec(f) { return { facts: !!f }; }
`;

const TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "META"];
const CIKS = { AAPL: 320193, MSFT: 789019, NVDA: 1045810, AMZN: 1018724, META: 1326801 };
const FORMS = 12;
function sub(t) {
  const d = Array.from({ length: FORMS }, (_, i) => new Date(Date.parse("2026-10-13") - i * 6 * 86400000).toISOString().slice(0, 10));
  return { name: t + " Inc.", filings: { recent: { form: d.map(() => "4"), filingDate: d, accessionNumber: d.map((_, i) => "0000" + CIKS[t] + "-26-" + String(i).padStart(6, "0")), primaryDocument: d.map(() => "xslF345X05/form4.xml") } } };
}
const XML = (i) => `<ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>Insider ${i}</rptOwnerName></reportingOwnerId></reportingOwner><nonDerivativeTable><nonDerivativeTransaction><transactionDate><value>2026-10-01</value></transactionDate><transactionCoding><transactionCode>${i % 2 ? "P" : "S"}</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>10</value></transactionShares><transactionPricePerShare><value>5</value></transactionPricePerShare><transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode></transactionAmounts></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>`;

function load(opts) {
  opts = opts || {};
  const log = [];
  const ctx = { console: { warn() {}, log() {}, error() {} }, Date, Intl, Number, String, isFinite, Object, Array, Math, RegExp, JSON, Error, process, Buffer, require, AbortSignal, AbortController, URL, encodeURIComponent, setTimeout, clearTimeout, Promise, Map, Set };
  ctx.globalThis = ctx;
  ctx.hasPremiumAccess = (u) => !!(u && u.admin === true);
  let fail = opts.fail || 0;
  ctx.fetch = function (input, init) {
    const url = typeof input === "string" ? input : input.url;
    const ua = init && init.headers && init.headers["User-Agent"];
    log.push({ t: Date.now(), url, ua });
    const sec = /sec\.gov/.test(url);
    return new Promise((resolve, reject) => {
      const ms = opts.delay != null ? opts.delay : 5 + Math.floor(Math.random() * 40);
      const timer = setTimeout(() => {
        if (sec && fail > 0) { fail--; return resolve({ ok: false, status: 503, text: async () => "", json: async () => ({}) }); }
        let body = "x";
        if (/company_tickers/.test(url)) body = JSON.stringify(Object.fromEntries(TICKERS.map((t, i) => [i, { ticker: t, cik_str: CIKS[t], title: t + " Inc." }])));
        else if (/submissions\/CIK(\d+)/.test(url)) { const cik = Number(/CIK(\d+)/.exec(url)[1]); body = JSON.stringify(sub(TICKERS.find((t) => CIKS[t] === cik))); }
        else if (/companyfacts/.test(url)) body = JSON.stringify({ facts: { "us-gaap": {} } });
        else { const m = url.match(/26(\d{6})\/form4\.xml$/); body = m ? XML(Number(m[1])) : "<html></html>"; }
        resolve({ ok: true, status: 200, text: async () => body, json: async () => JSON.parse(body) });
      }, ms);
      if (init && init.signal) init.signal.addEventListener("abort", () => { clearTimeout(timer); reject(init.signal.reason); }, { once: true });
    });
  };
  vm.createContext(ctx);
  vm.runInContext(bb7, ctx, { filename: "bb7.js" });
  vm.runInContext(FIN, ctx, { filename: "rt32.js" });
  vm.runInContext(bb8f, ctx, { filename: "bb8f.js" });
  ctx.bb7Reset();
  return { ctx, log };
}
function maxWindow(ts) {
  ts = ts.slice().sort((a, b) => a - b);
  let best = 0;
  for (let i = 0; i < ts.length; i++) { let n = 0; for (let j = i; j < ts.length && ts[j] - ts[i] < 1000; j++) n++; best = Math.max(best, n); }
  return best;
}
const secStarts = (log) => log.filter((x) => /sec\.gov/.test(x.url)).map((x) => x.t);

test("mixed concurrent load: insiders cold for 5 tickers + financials for 5 US tickers stays <= 10 per rolling second", async () => {
  const { ctx, log } = load();
  const t0 = Date.now();
  const fin = [];
  const ins = TICKERS.map((t) => ctx.bb7Load(t, { premium: true, codes: "all" }));
  for (const t of TICKERS) fin.push(ctx.bb8cSec(t).then((v) => ({ t, v, ms: Date.now() - t0 })));
  const [a, b] = await Promise.all([Promise.all(ins), Promise.all(fin)]);
  const starts = secStarts(log);
  assert.ok(starts.length >= 5 * (FORMS + 1) + 5, "requests " + starts.length);
  assert.ok(maxWindow(starts) <= 10, "max " + maxWindow(starts));
  for (const r of a) { assert.equal(r.status, 200); assert.ok(!r.body.unavailable, JSON.stringify(r.body).slice(0, 200)); }
  for (const r of b) assert.ok(r.v && r.v.facts, r.t);
  // Interactive lane: companyfacts is not stuck behind the bulk Form 4 fill.
  assert.ok(Math.max(...b.map((r) => r.ms)) < 3000, "financials " + b.map((r) => r.ms));
  // User-Agent unchanged per path.
  const uas = new Set(log.filter((x) => /sec\.gov/.test(x.url)).map((x) => (/companyfacts|company_tickers/.test(x.url) && x.ua === "TheDispatch support@thedispatch.uk") || x.ua === "TheDispatchMarkets admin@thedispatch.uk"));
  assert.deepEqual([...uas], [true]);
  assert.equal(ctx.bb8fSnapshot().inWindow <= 10, true);
});

test("burst of 40 through both entry points (global fetch and the bb7 test hook) plus retries stays <= 10 per rolling second", async () => {
  const { ctx, log } = load({ delay: 0, fail: 15 });
  const hook = [];
  ctx.bb7Fetch = (u, o) => { hook.push(Date.now()); return Promise.resolve({ ok: true, status: 200, text: async () => "ok" }); };
  async function retrying(u) { for (let i = 0; i < 4; i++) { const r = await ctx.fetch(u, {}); if (r.ok) return r; } throw new Error("gave up"); }
  const jobs = [];
  for (let i = 0; i < 20; i++) jobs.push(retrying("https://data.sec.gov/submissions/CIK000000" + i + ".json"));
  for (let i = 0; i < 20; i++) jobs.push(ctx.bb7FetchBuf("https://www.sec.gov/Archives/edgar/data/1/" + i + "/a.xml"));
  await Promise.all(jobs);
  const all = secStarts(log).concat(hook);
  assert.equal(all.length, 55, "20 + 15 retries + 20");
  assert.ok(maxWindow(all) <= 10, "max " + maxWindow(all));
});

test("queued waits respect the caller's own timeout and the queue cap; non-SEC hosts are never queued", async () => {
  const { ctx, log } = load({ delay: 0 });
  for (let i = 0; i < 10; i++) await ctx.fetch("https://data.sec.gov/x" + i, {});
  const t0 = Date.now();
  await assert.rejects(ctx.fetch("https://data.sec.gov/late", { signal: AbortSignal.timeout(60) }));
  const waited = Date.now() - t0;
  assert.ok(waited >= 50 && waited < 400, "aborted after " + waited);
  ctx.BB8F_MAX_WAIT_MS = 1;
  for (let i = 0; i < 10; i++) ctx.fetch("https://data.sec.gov/y" + i, {}).catch(() => {});
  await assert.rejects(ctx.fetch("https://data.sec.gov/expire", {}), /SEC queue wait/);
  ctx.BB8F_MAX_WAIT_MS = 30000;
  const y0 = Date.now();
  await Promise.all(Array.from({ length: 30 }, (_, i) => ctx.fetch("https://query1.finance.yahoo.com/v8/finance/chart/X" + i, {})));
  await ctx.fetch("https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2026FD.zip", {});
  assert.ok(Date.now() - y0 < 300, "non-SEC not paced");
  assert.equal(log.filter((x) => /late|expire/.test(x.url)).length, 0, "dropped waiters never hit SEC");
  assert.equal(ctx.bb8fIsSec("https://efts.sec.gov/LATEST/search-index?q=x"), true);
  assert.equal(ctx.bb8fIsSec("https://notsec.gov.example.com/"), false);
  assert.equal(ctx.bb8fIsSec("https://example.com/?u=https://www.sec.gov/"), false);
});
