// Offline tests for deploy/patch_bb8c.py. Loads the bb8c block with stubs (real timers,
// abort-honouring fake fetch); no network, no live files. Run: node --test test/bb8c.test.js
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8c.py"), "utf8");
const block = patch.slice(patch.indexOf("// \u2500\u2500 bb8c \u2500\u2500"), patch.indexOf("// BB8C_JS_END") + "// BB8C_JS_END".length);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env"]) assert.equal(block.includes(bad), false, bad);
assert.match(patch, /5683b5b2720ee7ced93b95f69690b81e/);
for (const m of block.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8c/, m[1]);

// Minimal stand-ins for the rt32/rt33s/bb8b pieces the block hooks into.
const STUBS = `
var RT32 = { cache: new Map(), crumb: "", ck: "", crumbAt: 0 };
var RT32_BUA = "ua", RT32_UA = "ua";
var RT33S_CRYPTO = new Set(["BTC"]);
var fundCalls = 0;
function bb8bForeign(s) { return /\\.[A-Z]{1,2}$/.test(s) && !/^[A-Z]+\\.[AB]$/.test(s); }
function bb8bYahooSym(s) { return bb8bForeign(s) ? s : s.replace(/\\./g, "-"); }
async function rt32CikMap() { var r = await fetch("https://www.sec.gov/files/company_tickers.json", {}); var j = await r.json(); return new Map(Object.values(j).map(function (x) { return [x.ticker, { cik: String(x.cik_str).padStart(10, "0"), name: x.title }]; })); }
function rt32Get(url, headers) { return fetch(url, { headers: headers, signal: AbortSignal.timeout(8000) }); }
function rt32Sec(f) { return { annual: [{ period: "FY2026", revenue: f.rev }], quarterly: [] }; }
async function rt32Crumb() { throw new Error("old crumb chain must not run"); }
async function rt32Yahoo() { throw new Error("old yahoo chain must not run"); }
async function rt32Build(sym, snap) { throw new Error("replaced"); }
function bb8bBuild0(key, snap) {
  var s = snap.settled[0], y = snap.settled[1];
  var d = { symbol: key, asOf: "now", sources: { sec: s.status === "fulfilled" ? "ok" : String(s.reason && s.reason.message), yahoo: y.status === "fulfilled" ? "ok" : String(y.reason && y.reason.message) } };
  if (s.status === "fulfilled" && s.value) d.financials = s.value;
  if (y.status === "fulfilled") d.valuation = { pe: y.value.pe };
  return Promise.resolve(d);
}
async function rt33sFund(req, res, p, url) { fundCalls++; var sym = url.searchParams.get("symbol"); var h = RT32.cache.get(sym); json(res, 200, h ? h.data : { symbol: sym, unavailable: true }, { "Cache-Control": "public, max-age=600" }); }
`;

function harness() {
  const cfg = { yahooMs: 50, secMs: 20, expired: false, yahooDown: false };
  const calls = {};
  const R = (o, st = 200) => ({ ok: st < 300, status: st, headers: { getSetCookie: () => ["A3=new"], get: () => "" }, json: async () => o, text: async () => (typeof o === "string" ? o : JSON.stringify(o)) });
  const wait = (ms, signal) => new Promise((res, rej) => { const t = setTimeout(res, ms); if (signal) signal.addEventListener("abort", () => { clearTimeout(t); rej(Object.assign(new Error("timeout"), { name: "TimeoutError" })); }); });
  const fetch = async (u, o) => {
    const k = /companyfacts/.test(u) ? "facts" : /company_tickers/.test(u) ? "map" : /fc\.yahoo/.test(u) ? "fc" : /getcrumb/.test(u) ? "getcrumb" : /quoteSummary/.test(u) ? "qs" : "other";
    calls[k] = (calls[k] || 0) + 1;
    const yahoo = /yahoo/.test(u);
    await wait(yahoo ? cfg.yahooMs : cfg.secMs, o && o.signal);
    if (yahoo && cfg.yahooDown) return R({}, 503);
    if (k === "map") return R({ 0: { ticker: "NVDA", cik_str: 1045810, title: "NVIDIA" }, 1: { ticker: "AAPL", cik_str: 320193, title: "Apple" } });
    if (k === "facts") return R({ facts: { rev: 1.3e11 } });
    if (k === "fc") return R("", 404);
    if (k === "getcrumb") return R(cfg.badCrumbOnce ? (cfg.badCrumbOnce = false, "<html>") : "crumbNEW", 200);
    if (k === "qs") { if (cfg.expired && !/crumb=crumbNEW/.test(u)) return R({}, 401); return R({ quoteSummary: { result: [{ pe: 27.07 }] } }); }
    return R({}, 404);
  };
  const ctx = { console: { warn() {} }, URL, AbortSignal, setTimeout, clearTimeout, Promise, Map, Set, Date, JSON, Math, Object, String, Number, Error, fetch };
  ctx.globalThis = ctx;
  ctx.json = (res, status, body, headers) => { res.status = status; res.body = body; res.headers = Object.assign({}, headers || {}); };
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(block, ctx, { filename: "bb8c.js" });
  const V = (s) => vm.runInContext(s, ctx);
  V("RT32.crumb='crumbOLD'; RT32.ck='A3=old'; RT32.crumbAt=Date.now()-3600e3;");
  const call = async (sym, p = "/api/financials") => { const res = {}; const t = Date.now(); await ctx.rt33sFund({ headers: {} }, res, p, new URL("http://x" + p + "?symbol=" + encodeURIComponent(sym))); res.ms = Date.now() - t; return res; };
  const until = async (fn, ms) => { const t = Date.now(); while (!fn()) { if (Date.now() - t > ms) throw new Error("timed out"); await new Promise((r) => setTimeout(r, 100)); } };
  return { cfg, calls, ctx, V, call, until };
}

test("slow Yahoo (6s per call) with an expired crumb: partial in <=8s, next call complete", { timeout: 40000 }, async () => {
  const h = harness();
  Object.assign(h.cfg, { yahooMs: 6000, secMs: 20, expired: true });
  let r = await h.call("NVDA");
  assert.ok(r.ms <= 8000, "took " + r.ms + "ms");
  assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.headers["Cache-Control"], "no-store");
  assert.equal(r.body.meta.partial, true);
  assert.deepEqual([...r.body.meta.pending], ["yahoo"]);
  assert.equal(r.body.sources.yahoo, "pending");
  assert.ok(r.body.financials, "SEC part returned");
  assert.equal(h.V("RT32.cache.has('NVDA')"), false, "partial is never cached");
  await h.until(() => h.V("RT32.cache.has('NVDA')"), 30000);
  r = await h.call("NVDA");
  assert.equal(r.body.meta, undefined);
  assert.equal(r.body.valuation.pe, 27.07);
  assert.equal(h.V("bb8cAuthCount"), 1, "single re-auth");
  assert.equal(h.calls.getcrumb, 1);
  assert.equal(h.calls.qs, 2, "one retry");
});

test("expired crumb: one re-auth and one retry, shared by concurrent requests", async () => {
  const h = harness();
  Object.assign(h.cfg, { yahooMs: 100, expired: true });
  const rs = await Promise.all([h.call("NVDA"), h.call("AAPL"), h.call("NVDA", "/api/earnings")]);
  assert.ok(rs.every((r) => r.headers["X-Dispatch-Data-Status"] === "fresh"));
  assert.equal(h.V("bb8cAuthCount"), 1);
  assert.equal(h.calls.getcrumb, 1);
  assert.equal(h.calls.fc || 0, 0);
  assert.equal(h.calls.qs, 4, "2 symbols x (expired + retry)");
});

test("dead cookie: still one re-auth (getcrumb, then fc + getcrumb)", async () => {
  const h = harness();
  Object.assign(h.cfg, { yahooMs: 30, expired: true, badCrumbOnce: true });
  const r = await h.call("AAPL");
  assert.equal(r.body.valuation.pe, 27.07);
  assert.equal(h.V("bb8cAuthCount"), 1);
  assert.equal(h.calls.fc, 1);
  assert.equal(h.calls.getcrumb, 2);
});

test("concurrent cold requests share one build, Ask peer lookups get the full result", async () => {
  const h = harness();
  Object.assign(h.cfg, { yahooMs: 300, secMs: 300 });
  const rs = await Promise.all([h.call("AAPL"), h.call("AAPL"), h.call("AAPL", "/api/earnings"), h.call("AAPL", "/api/holders"), h.ctx.rt32Build("AAPL")]);
  assert.equal(h.calls.facts, 1);
  assert.equal(h.calls.qs, 1);
  assert.ok(rs[4].valuation && !rs[4].meta);
  h.V("RT32.cache.clear(); globalThis.bb8cBudgetMs = 300");
  Object.assign(h.cfg, { yahooMs: 1200 });
  const [route, ask] = await Promise.all([h.call("NVDA"), h.ctx.rt32Build("NVDA")]);
  assert.equal(route.body.meta.partial, true);
  assert.ok(ask.valuation && !ask.meta, "Ask waits for the full build");
});

test("partial with a stale cache entry serves the stale entry; fresh hits use the old path", async () => {
  const h = harness();
  h.V("RT32.cache.set('NVDA', { at: Date.now() - 13 * 3600e3, data: { symbol: 'NVDA', valuation: { pe: 1 } } }); globalThis.bb8cBudgetMs = 200");
  Object.assign(h.cfg, { yahooMs: 1000 });
  let r = await h.call("NVDA");
  assert.equal(r.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(r.body.valuation.pe, 1);
  await h.until(() => h.V("Date.now() - RT32.cache.get('NVDA').at < 60e3"), 5000);
  r = await h.call("NVDA");
  assert.equal(h.V("fundCalls"), 1);
  assert.equal(r.headers["Cache-Control"], "public, max-age=600");
});

test("Yahoo down: SEC-only answer cached for 10 minutes, not 12 hours; foreign listings skip SEC", async () => {
  const h = harness();
  Object.assign(h.cfg, { yahooDown: true });
  let r = await h.call("NVDA");
  assert.ok(r.body.financials && !r.body.meta);
  assert.ok(h.V("Date.now() - RT32.cache.get('NVDA').at") > 11.8 * 3600e3);
  Object.assign(h.cfg, { yahooDown: false });
  for (const k in h.calls) delete h.calls[k];
  r = await h.call("BP.L");
  assert.equal(h.calls.map || 0, 0);
  assert.equal(h.calls.facts || 0, 0);
  assert.equal(r.body.valuation.pe, 27.07);
});
