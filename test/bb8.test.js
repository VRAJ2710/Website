// Offline tests for deploy/patch_bb8.py. Loads the bb8 block with stubs; no network, no live files.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8.py"), "utf8");
const start = patch.indexOf("// \u2500\u2500 bb8 \u2500\u2500");
const end = patch.indexOf("// BB8_JS_END");
assert.ok(start > 0 && end > start);
const block = patch.slice(start, end + "// BB8_JS_END".length);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe.webhooks", ".tier"]) assert.equal(block.includes(bad), false, bad);
assert.match(patch, /e10bf8fdeb7f9c7f3265ab2a0e0ec549/);
assert.match(patch, /" min by exchange"/);

function load(extra) {
  const ctx = { console: { warn() {} }, Buffer, require, process, URL, AbortSignal, setTimeout, clearTimeout, Promise, Map, Set, Date, JSON, Math };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(extra || "", ctx);
  vm.runInContext(block, ctx, { filename: "bb8.js" });
  return ctx;
}
const STUBS = `
var bb2Mem = { vals: new Map() };
function bb2Num(x) { if (x == null) return null; var n = Number(x && x.raw != null ? x.raw : x); return isFinite(n) ? n : null; }
function bb3bRewrite(text) { return String(text); }
function bb3bHold() { return false; }
function bb2System() { return "BASE"; }
function bb2StoreQuote(row) { bb2Mem.vals.set(row.symbol, { at: Date.now(), v: { trailing: row.trailingPE, forward: row.forwardPE, price: row.regularMarketPrice } }); }
function bb7TickerKeys(s) { return [String(s || "").toUpperCase()]; }
var bb7Store = new Map();
function bb7Recall(k) { return bb7Store.get(k) || null; }
function bb7Now() { return Date.now(); }
function bb7Shape(pack, opts) { return { ticker: pack.ticker, insider: (pack.rows || []).slice(0, opts && opts.premium ? 999 : 5), house: opts && opts.house ? opts.houseBody : null, meta: { limited: !(opts && opts.premium) } }; }
function bb7StaleResult(pack, opts) { return { status: 200, body: bb7Shape(pack, opts), headers: { "X-Dispatch-Data-Status": "stale" } }; }
function bb7Unavailable() { return { status: 200, body: { unavailable: true, message: "Insider filings unavailable right now" }, headers: { "X-Dispatch-Data-Status": "unavailable" } }; }
function bb7HouseView(index) { return { items: (index && index.items) || [], asOf: "", note: "n" }; }
var loadDelay = 0, loadCalls = 0, loadFail = 0;
async function bb7Load(ticker, opts) {
  loadCalls++;
  if (loadFail > 0) { loadFail--; return bb7Unavailable(); }
  var rows = [];
  bb8Track(ticker, opts && opts.premium ? "full" : "free", { rows: rows, cik: "1", company: "Co", list: [{ filingDate: "2026-10-13" }, { filingDate: "2026-10-01" }], scanned: function () { return rows.length; } });
  rows.push({ filingDate: "2026-10-13", transactionCode: "S" });
  await new Promise(function (r) { setTimeout(r, loadDelay); });
  rows.push({ filingDate: "2026-10-01", transactionCode: "S" });
  return { status: 200, body: bb7Shape({ ticker: ticker, rows: rows, oldestFiling: "2026-04-02", newestFiling: "2026-10-13", filings: 600, scanned: 40 }, opts), headers: { "X-Dispatch-Data-Status": "fresh" } };
}
`;

const FACTS = [
  { a: "MU", b: "NVDA", basis: "trailing", dir: "lower", label: "trailing P/E (TTM)", sentence: "MU ... lower than NVDA" },
  { a: "MU", b: "NVDA", basis: "forward", dir: "lower", label: "forward P/E (next 12 months)", sentence: "MU ... lower" },
  { a: "MU", b: "WDC", basis: "trailing", dir: "higher", label: "trailing P/E (TTM)", sentence: "MU ... higher" },
  { a: "MU", b: "INTC", basis: "trailing", dir: "missing", sentence: "INTC trailing P/E (TTM) was not reported, so MU and INTC are not compared on trailing P/E (TTM)." },
];

test("1 Ask: cannot-compare dead end becomes a fact-based conclusion", () => {
  const c = load(STUBS);
  const out = c.bb3bRewrite("Margins improved. In conclusion, while we know MU's valuation, we cannot directly compare it to its peers at this time.", FACTS, true);
  assert.ok(!/cannot/.test(out));
  assert.match(out, /^Margins improved\.\n\nIn short, on the figures shown, MU's trailing P\/E \(TTM\) is lower than NVDA and higher than WDC, and its forward P\/E \(next 12 months\) is lower than NVDA\. INTC trailing P\/E \(TTM\) was not reported/);
  assert.equal(c.bb3bRewrite(out, FACTS, true), out);
  assert.equal(c.bb3bRewrite("We cannot compare MU to peers.", [], true), "We cannot compare MU to peers.");
  assert.equal(c.bb3bRewrite("MU trades lower than NVDA.", FACTS, true), "MU trades lower than NVDA.");
  assert.equal(c.bb3bHold("In conclusion, while", FACTS), true);
  assert.match(c.bb2System({}, { facts: FACTS }, []), /Never say the company cannot be compared/);
  assert.equal(c.bb2System({}, null, []), "BASE");
});

test("2 forward P/E: NTM consensus EPS instead of Yahoo +1y forwardPE", () => {
  const c = load(STUBS);
  const now = Date.parse("2026-10-19T05:00:00Z");
  const info = c.bb8NtmFromTrend([{ period: "0y", endDate: "2027-01-31", earningsEstimate: { avg: { raw: 9.31242 } } }, { period: "+1y", endDate: "2028-01-31", earningsEstimate: { avg: { raw: 15.9146 } } }], now);
  assert.ok(Math.abs(info.epsNtm - 14.02) < 0.01);
  assert.equal(c.bb8ForwardFrom(214.13, info), 15.27);
  assert.equal(c.bb8NtmFromTrend([{ period: "0y" }], now), null);
  assert.equal(c.bb8ForwardFrom(100, { epsNtm: -1 }), null);
  c.bb8NtmRemember("NVDA", Object.assign({}, info, { at: Date.now() }));
  c.bb2StoreQuote({ symbol: "NVDA", trailingPE: 27.07, forwardPE: 13.45, regularMarketPrice: 214.13, epsTrailingTwelveMonths: 7.91 });
  const v = vm.runInContext("bb2Mem.vals.get('NVDA').v", c);
  assert.equal(v.forward, 15.27);
  c.bb2StoreQuote({ symbol: "XYZ", trailingPE: 20, forwardPE: 9.9, regularMarketPrice: 50 });
  assert.equal(vm.runInContext("bb2Mem.vals.get('XYZ').v", c).forward, null);
  assert.match(c.bb8EpsNote(v), /EPS TTM \$7\.91, next-12-month consensus EPS \$14\.02/);
});

test("4 insiders window label and raw Form 4 path", () => {
  const c = load(STUBS);
  assert.equal(c.bb8WindowLabel("2026-04-02", "2026-10-13"), "Last 6 months");
  assert.equal(c.bb8WindowLabel("2026-09-20", "2026-10-13"), "Last 3 weeks");
  assert.equal(c.bb8WindowLabel("2025-10-13", "2026-10-13"), "Last 1 year");
  const w = c.bb8Window({ rows: [], oldestFiling: "2026-04-02", newestFiling: "2026-10-13", filings: 600, scanned: 40 }, true);
  assert.equal(w.label, "Last 6 months"); assert.equal(w.more, true); assert.equal(w.next, "before=2026-04-02");
  assert.equal(c.bb8Window({}, false).label, "Latest 5 open-market trades");
  assert.equal(c.bb8RawPrimary("xslF345X06/form4.xml"), "form4.xml");
  assert.equal(c.bb8RawPrimary("doc4.xml"), "doc4.xml");
});

test("5 insiders cold cache: wait up to the budget, then partial rows, then unavailable", async () => {
  const c = load(STUBS);
  c.bb8InsidersBudgetMs = 300;
  vm.runInContext("loadDelay = 50", c);
  let r = await c.bb7Load("AAPL", { premium: true });
  assert.equal(r.body.insider.length, 2); assert.equal(r.body.meta.window.label, "Last 6 months");
  vm.runInContext("loadDelay = 1000", c);
  const t0 = Date.now();
  r = await c.bb7Load("MSFT", { premium: true, house: true });
  assert.ok(Date.now() - t0 >= 280 && Date.now() - t0 < 700);
  assert.equal(r.body.meta.partial, true); assert.equal(r.headers["X-Dispatch-Data-Status"], "partial");
  assert.equal(r.body.insider.length, 1);
  assert.equal(r.body.house.label, "Latest House trade filings (all members)");
  vm.runInContext("loadDelay = 0; loadFail = 1; loadCalls = 0", c);
  c.bb8InsidersBudgetMs = 4000;
  r = await c.bb7Load("AAPL", { premium: true });
  assert.ok(!r.body.unavailable); assert.equal(vm.runInContext("loadCalls", c), 2);
});

test("6 House label", () => {
  const c = load(STUBS);
  const h = c.bb7HouseView({ items: [] });
  assert.equal(h.label, "Latest House trade filings (all members)"); assert.equal(h.scope, "all-members"); assert.equal(h.tickerFiltered, false);
});
