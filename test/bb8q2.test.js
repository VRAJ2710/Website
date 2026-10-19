// Offline tests for deploy/patch_bb8q2.py (P0 follow-up to bb8q, Jack's calls): Yahoo DX-Y.NYB is the dollar index
// on every server output (the FX-computed index labelled "Dispatch FX basket"), UK CPI / gilt no-data wording, and a
// cited, labelled gold futures move whenever gold spot has no previous close (cold start). Loads the bb8m, bb8p, bb8q
// and bb8q2 blocks with stubs; no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const cut = (src, a, b) => src.slice(src.indexOf(a), src.indexOf(b) + b.length);
const B8M = cut(read("patch_bb8m.py"), "// \u2500\u2500 bb8m \u2500\u2500", "// BB8M_JS_END");
const B8P = cut(read("patch_bb8p.py"), "// \u2500\u2500 bb8p \u2500\u2500", "// BB8P_JS_END");
const B8Q = cut(read("patch_bb8q.py"), "// \u2500\u2500 bb8q \u2500\u2500", "// BB8Q_JS_END");
const PATCH = read("patch_bb8q2.py");
const B8Q2 = cut(PATCH, "// \u2500\u2500 bb8q2 \u2500\u2500", "// BB8Q2_JS_END");
assert.match(B8Q2, /function bb8q2GoldFill/);
const plain = x => JSON.parse(JSON.stringify(x));

const NOW = Date.parse("2026-10-19T11:50:00Z");   // Mon 19 Oct 2026, 12:50 BST
const STUBS = `
var RT17_ENUMS = { askLength: ["brief", "detailed"], askFocus: ["gold", "macro", "crypto", "em"] };
var BB2_PEERS = { MU: ["NVDA", "AVGO"] };
var __st = null;
function bb8dStore() { return __st; }
function bb8dUk(ms) { var d = new Date(ms); return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }).format(d).replace(/,? (\\d\\d:\\d\\d)$/, ", $1") + " UK"; }
function bb2Question(body) { var m = body && body.messages || []; for (var i = m.length - 1; i >= 0; i--) if (m[i].role === "user") return String(m[i].content || ""); return ""; }
function bb2Footer(sources) { if (!sources || !sources.length) return ""; return "\\n\\nSources:\\n" + sources.map(function (s, i) { return "[" + (i + 1) + "] " + s.name + " | " + (s.link || "") + " | " + (s.detail || ""); }).join("\\n"); }
function bb8eIsCard(q) { return false; }
function bb8eStrip(q) { return q; }
function bb8eMs(q) { return Number(q.ts) * 1000; }
function bb8iCiteNums(s) { var o = []; String(s).replace(/\\[(\\d+)\\]/g, function (m, g) { o.push(Number(g)); return m; }); return o; }
function bb8iIsNews(src) { return !!(src && !src.bb8q && src.detail && src.detail.length >= 12); }
function bb8iNewsMatch(sent, src) { return false; }
function bb8dSplit(t) { return String(t).split(/(?<=[.!?](?:\\s*\\[\\d+\\])*)\\s+(?=[A-Z])/); }
function isAdminUser(u) { return !!(u && u.email === "admin@box.local"); }
async function currentUser() { return null; }
var lastChatLiveSnapshot = {};
// free-data stubs (the shapes the server's own helpers return)
var __quotes = {
  "^GSPC": { p: 7659.44, prev: 7744.06, c: -1.09, ts: 1792183320, status: "closed" },
  "^VIX": { p: 18.91, prev: 17.2, ts: 1792183320, status: "closed" },
  "DX-Y.NYB": { p: 101.807, prev: 101.837, c: -0.0295, ts: 1792410000 },
  "^TNX": { p: 5.098, prev: 5.089, ts: 1792173540, status: "closed" },
  "USDCNH=X": { p: 6.6800, prev: 6.6853, ts: 1792410000 },
  "^HSI": { p: 24186.83, prev: 24061.7, ts: 1792139280, status: "closed" },
  "HG=F": { p: 6.579, prev: 6.574, currency: "USD", ts: 1792410000 },
  "GBPUSD=X": { p: 1.3337, prev: 1.3330, ts: 1792410000 },
  "^FTSE": { p: 10754.8, prev: 10882.1, ts: 1792410000 },
  "GC=F": { p: 4189.6, prev: 4181.1, currency: "USD", ts: 1792410000 }
};
var __calls = 0;
async function bb3Pack(t) { __calls++; return { at: ${NOW}, quotes: { "^GSPC": __quotes["^GSPC"], "^VIX": __quotes["^VIX"], "DX-Y.NYB": __quotes["DX-Y.NYB"], "SPY": { p: 763.25, prev: 771.8 }, "CL=F": { p: 71 }, "BTC-USD": { p: 100000, prev: 99000 } }, dxy: { p: 101.806, prev: 101.747 } }; }
async function bb3OneQuote(pack, sym) { return __quotes[sym] ? Object.assign({}, __quotes[sym]) : null; }
function bb3QuotePx(q) { return q && Number(q.p) > 0 ? Number(q.p) : null; }
function bb3QuotePct(q) { return q && q.prev > 0 ? (q.p / q.prev - 1) * 100 : null; }
function bb3Mood(x) { return { regime: "Risk-Off", score: 37 }; }
var __spot = { p: 4170.3, ts: ${Math.floor(NOW / 1000)}, source: "gold-api-spot-proxy", c: 0, prev: 4170.3 };
async function fetchGoldProxy() { return Object.assign({}, __spot); }
async function buildChatLiveMarketBlock() { lastChatLiveSnapshot = { goldLast: 4189.6, goldTs: 1792410000, dayHigh: 4211.2, dayLow: 4176, windows: [] }; return "LIVE"; }
function __bars(closes) { var t0 = Date.parse("2026-09-28T12:00:00Z") / 1000, ts = [], c = []; closes.forEach(function (v, i) { ts.push(t0 + i * 86400); c.push(v); }); return { data: { chart: { result: [{ meta: { exchangeTimezoneName: "America/New_York", regularMarketPrice: 4189.6, regularMarketTime: 1792410000 }, timestamp: ts, indicators: { quote: [{ close: c }] } }] } } }; }
// Mon 28 Sep .. Mon 19 Oct (daily; weekend closes are null like Yahoo's)
var __closes = [4180, 4185, 4186.7, 4190, 4192, null, null, 4195, 4200, 4199, 4198, 4197, null, null, 4196, 4190, 4185, 4183, 4181.1, null, null, 4189.6];
async function fetchYahooChart(sym, range, interval) { return __bars(__closes); }
function bb8pQuestion(body) { return bb2Question(body); }

function bb8Late(ms) { return new Promise(function () {}); }
async function yahooQuote(syms) { var o = {}; syms.forEach(function (s) { if (__quotes[s] && !__noYahoo[s]) o[s] = Object.assign({}, __quotes[s]); }); return o; }
var __noYahoo = {};
async function fetchSyntheticDxy() { return { p: 101.806, prev: 101.747, c: 0.058, change: 0.059, currency: "USD", exchange: "SYNTHETIC", name: "US Dollar Index (computed from live FX)", ts: ${Math.floor(NOW / 1000)}, source: "dxy-fx-computed", proxy: true }; }
async function marketReferenceQuotes() { var g = await fetchGoldProxy(), d = await fetchSyntheticDxy(); return { XAU: g, DXY: d, fetchedAt: ${NOW} }; }
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, Map, WeakMap, Intl, isFinite, Buffer, encodeURIComponent };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8M, ctx, { filename: "bb8m.js" });
  vm.runInContext(B8P, ctx, { filename: "bb8p.js" });
  vm.runInContext("async function bb2Read0(req) { return req.body; }", ctx);
  vm.runInContext(B8Q, ctx, { filename: "bb8q.js" });
  vm.runInContext(B8Q2, ctx, { filename: "bb8q2.js" });
  return ctx;
}
function body(q, context) { return { context: context || "Page: Markets", messages: [{ role: "user", content: q }] }; }
async function read0(c, q) { c.__st = { chat: true, clientSources: [] }; const b = body(q); c.__st.body = b; await c.bb2Read0({ body: b }); return c.__st; }

test("protocol: bb8q2 names only, no forbidden code, stacked on bb8q (b4f66c89)", () => {
  assert.match(PATCH, /b4f66c896a13a73fb03656386c4ae802/);
  assert.match(PATCH, /REFUSE: bb8q2 already applied/);
  const code = B8Q2.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "process.env", "require(", ".tier", "cookie", "x-api-key"]) assert.equal(code.indexOf(bad), -1, bad);
  for (const m of B8Q2.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8q2/, m[1]);
  for (const m of B8Q2.matchAll(/^var ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^(?:bb8q2|BB8Q2)/, m[1]);
});

test("reference route: DXY is Yahoo DX-Y.NYB with its own previous close; the FX index is DXY_FX, labelled", async () => {
  const c = load();
  const r = await c.marketReferenceQuotes();
  const d = r.DXY;
  assert.equal(d.symbol, "DX-Y.NYB"); assert.equal(d.label, "US Dollar Index (ICE, Yahoo DX-Y.NYB)"); assert.equal(d.source, "Yahoo Finance (DX-Y.NYB)");
  assert.equal(d.price, 101.807); assert.equal(d.prevClose, 101.837);
  assert.ok(Math.abs(d.changePct - (101.807 / 101.837 - 1) * 100) < 1e-9); assert.ok(d.changePct < 0 && d.change < 0 && d.c === d.changePct);
  assert.match(d.asOf, /Z$/); assert.match(d.asOfUk, / UK$/);
  assert.equal(r.DXY_FX.label, "Dispatch FX basket"); assert.equal(r.DXY_FX.name, "Dispatch FX basket");
});

test("reference route: Yahoo DX-Y.NYB missing -> DXY is the labelled FX basket with a fallback flag", async () => {
  const c = load(); c.__noYahoo["DX-Y.NYB"] = true;
  const r = await c.marketReferenceQuotes();
  assert.equal(r.DXY.label, "Dispatch FX basket"); assert.equal(r.DXY.fallback, true);
});

test("cold start: XAU keeps spot's fields null and adds a labelled futuresChange; warm start has none", async () => {
  const c = load();
  const x = (await c.marketReferenceQuotes()).XAU;
  assert.equal(x.changeAvailable, false); assert.equal(x.change, null); assert.equal(x.changePct, null);
  assert.equal(x.futuresChange.symbol, "GC=F"); assert.equal(x.futuresChange.label, "Gold futures (GC=F, delayed 10 min)");
  assert.equal(x.futuresChange.prevClose, 4181.1); assert.match(x.futuresChange.text, /^gold futures \(GC=F\) \+0\.20% today$/);
  const w = load(); vm.runInContext("bb8qSpotMem.day = '2026-10-16'; bb8qSpotMem.last = 4150.5;", w);
  const y = (await w.marketReferenceQuotes()).XAU;
  assert.equal(y.changeAvailable, true); assert.equal(y.prevClose, 4150.5); assert.equal(y.futuresChange, null);
});

test("regime and Ask context name the ICE index; the pack keeps the FX basket only as dxyFx", async () => {
  const c = load();
  const pk = await c.bb3Pack(NOW);
  assert.equal(pk.dxy.symbol, "DX-Y.NYB"); assert.equal(pk.dxySrc, "ice"); assert.equal(pk.dxyFx.label, "Dispatch FX basket"); assert.equal((await c.fetchSyntheticDxy()).name, "Dispatch FX basket");
  const st = await read0(c, "How is the dollar doing?");
  const ids = st.bb8qCtx.facts.map(f => f.id + "|" + f.text);
  assert.ok(ids.some(t => /^regime\|.*US Dollar Index \(ICE, Yahoo DX-Y\.NYB\)/.test(t)));
  assert.ok(ids.some(t => /^DX-Y\.NYB\|US Dollar Index \(ICE, Yahoo DX-Y\.NYB\) is down 0\.03%/.test(t)));
  assert.ok(!ids.some(t => /101\.75|computed from live FX/.test(t)));
});

test("cold start, both paths: identical context; spot line carries the futures move and cites both sources", async () => {
  const c = load();
  const shape = st => plain({ facts: st.bb8qCtx.facts.map(f => f.id + "|" + f.text), sources: st.bb8qCtx.sources.map(s => s.name + "|" + s.link + "|" + s.detail), spot: st.bb8qCtx.spot.text });
  const a = shape(await read0(c, "What's the outlook for gold this week?"));
  const st = await read0(c, "What's the outlook for gold this week?");
  assert.deepStrictEqual(a, shape(st));
  assert.doesNotMatch(JSON.stringify(a), /no change is given/);
  assert.match(st.bb8qCtx.spot.text, /spot has no previous close in our feed yet, so today's move comes from gold futures \(GC=F, delayed 10 min\), up 0\.20% today\.$/);
  const doc = c.bb8qParse({ reply: st.bb8qCtx.spot.text + " [1]\n\nIn short: gold.", sources: [st.bb8qCtx.spot.src] });
  const out = c.bb8qRender(doc);
  assert.match(out.reply, /up 0\.20% today\. \[1\]\[2\]/);
  assert.equal(out.sources[1], st.bb8qCtx.fut.src);
});

test("warm start: spot's own change, one bracket, no futures fallback", async () => {
  const c = load(); vm.runInContext("bb8qSpotMem.day = '2026-10-16'; bb8qSpotMem.last = 4150.5;", c);
  const st = await read0(c, "Where is gold now?");
  assert.match(st.bb8qCtx.spot.text, /^Gold spot is up 0\.48% at \$4,170\.30 \(previous close \$4,150\.50; gold-api\.com, as of /);
  assert.equal(st.bb8qCtx.spot.futMove, undefined);
});

test("UK: CPI and gilt wording, proxies named as proxies, a related yield for gilt questions, no duplicates", async () => {
  const c = load();
  const lab = q => c.bb8pTopicLabel(c.bb8pTopic(body(q)));
  assert.equal(lab("What's the UK inflation rate?"), "UK CPI");
  assert.equal(lab("What are UK gilt yields doing?"), "UK gilt yields");
  assert.equal(lab("UK inflation and the Bank of England rate path?"), "UK CPI or UK gilt yields");
  const st = await read0(c, "What's the UK inflation rate, and where are gilt yields?");
  const doc = c.bb8qParse({ reply: "Sterling is little changed.\n\nIn short: steady.", sources: [] });
  c.bb8qNoData(doc, st, st.bb8qCtx); c.bb8qNoData(doc, st, st.bb8qCtx);
  const out = c.bb8qRender(doc).reply;
  assert.match(out, /^We don't carry UK CPI or UK gilt yields in our data feed right now/);
  assert.match(out, /as market proxies \(not CPI or gilt data\): GBP\/USD is up 0\.05% at 1\.3337 \[1\]; the FTSE 100 is down 1\.17% at 10,754\.80 \[2\]; the US 10-year Treasury yield \(\^TNX\), a related yield but not a gilt yield, is 5\.10% \[3\]\./);
  assert.equal(out.split("We don't carry").length, 2); assert.equal(out.split("as market proxies").length, 2);
  assert.match(out, /In short: no UK CPI or UK gilt yields in our feed/);
});

test("Ask meta.quote for gold: futuresChange on a cold start", async () => {
  const c = load();
  const st = await read0(c, "What's the outlook for gold this week?");
  vm.runInContext("function __qm(st) { return { symbol: 'XAU', changeAvailable: false, futures: { prevClose: null } }; }", c);
  c.bb8q2Qm0 = c.__qm;
  const q = vm.runInContext("bb8pQuoteMeta", c)(st);
  assert.equal(q.symbol, "XAU");
  assert.equal(q.futuresChange.label, "Gold futures (GC=F, delayed 10 min)"); assert.match(q.futuresChange.text, /\+0\.20% today/);
});
