// Offline tests for deploy/patch_bb8q.py (P0, QA retest of bb8p): one shared grounding context on both answer paths,
// cited figures, DXY/10Y baselines, gold spot headline with its own previous close, timeframe changes from daily
// bars, honest no-data opener with proxies, brief trim keeps the answer. Loads the bb8m, bb8p and bb8q blocks with
// stubs; no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const cut = (src, a, b) => src.slice(src.indexOf(a), src.indexOf(b) + b.length);
const B8M = cut(read("patch_bb8m.py"), "// \u2500\u2500 bb8m \u2500\u2500", "// BB8M_JS_END");
const B8P = cut(read("patch_bb8p.py"), "// \u2500\u2500 bb8p \u2500\u2500", "// BB8P_JS_END");
const PATCH = read("patch_bb8q.py");
const B8Q = cut(PATCH, "// \u2500\u2500 bb8q \u2500\u2500", "// BB8Q_JS_END");
assert.match(B8Q, /async function bb8qBuild/);

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
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, Map, WeakMap, Intl, isFinite, Buffer, encodeURIComponent };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8M, ctx, { filename: "bb8m.js" });
  vm.runInContext(B8P, ctx, { filename: "bb8p.js" });
  // the shared body read of both paths, wrapped by bb8q
  vm.runInContext("async function bb2Read0(req) { return req.body; }", ctx);
  vm.runInContext(B8Q, ctx, { filename: "bb8q.js" });
  return ctx;
}
const plain = x => JSON.parse(JSON.stringify(x));
function body(q, context) { return { context: context || "Page: Markets", messages: [{ role: "user", content: q }] }; }

test("protocol: bb8q names only, no forbidden code, stacked on bb8p (92cdce80)", () => {
  assert.match(PATCH, /92cdce800208671ab32ded68d15e24d1/);
  assert.match(PATCH, /REFUSE: bb8q already applied/);
  const code = B8Q.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "process.env", "require(", ".tier", "cookie"]) assert.equal(code.indexOf(bad), -1, bad);
  for (const m of B8Q.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8q/, m[1]);
  for (const m of B8Q.matchAll(/^var ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^(?:bb8q|BB8Q)/, m[1]);
});

test("both paths: the same request builds identical facts and sources (stream body read == JSON body read)", async () => {
  const c = load();
  const run = async () => { c.__st = { chat: true }; const b = body("What's the outlook for gold this week?"); c.__st.body = b; await c.bb2Read0({ body: b }); return c.__st; };
  const a = await run(), j = await run();
  const shape = st => ({ facts: st.bb8qCtx.facts.map(f => f.id + "|" + f.text), sources: st.bb8qCtx.sources.map(s => s.name + "|" + s.link + "|" + s.detail) });
  assert.deepStrictEqual(plain(shape(a)), plain(shape(j)));
  assert.ok(a.bb8qCtx.facts.length >= 6);
  assert.equal(c.bb8qBlock(a, a.bb8qCtx.sources), c.bb8qBlock(j, j.bb8qCtx.sources));
  // every source is citable: a real URL and a label
  a.bb8qCtx.sources.forEach(s => { assert.match(s.link, /^https:\/\//); assert.ok(s.name && s.detail); });
  const reg = a.bb8qCtx.sources.find(s => s.bb8qKey === "regime");
  assert.equal(reg.name, "Dispatch regime model"); assert.match(reg.link, /thedispatch\.uk/);
});

test("DXY and 10Y: Yahoo DX-Y.NYB with its own previous close (sign consistent); ^TNX not rescaled", async () => {
  const c = load(); c.__st = { chat: true }; const b = body("How is the dollar doing?"); c.__st.body = b;
  const ctx = await c.bb8qBuild(c.__st, b);
  const dxy = ctx.facts.find(f => f.id === "DX-Y.NYB").text, tnx = ctx.facts.find(f => f.id === "^TNX").text;
  assert.match(dxy, /\(DX-Y\.NYB\) is down 0\.03% at 101\.81 \(previous close 101\.84\)/);
  assert.doesNotMatch(dxy, /101\.75|\+0\.06/);                       // never the FX-computed index's baseline
  assert.match(tnx, /is 5\.10%, up 0\.9 bp from its previous close of 5\.09%/);
  assert.equal(c.bb8qChg({ p: 101.807, prev: 101.837 }).pct < 0, true);
});

test("gold spot: headline with null change and a flag when it has no own previous close; never GC=F's change", () => {
  const c = load();
  const q = c.bb8qSpotQuote({ p: 4170.3, prev: 4170.3, c: 0, ts: NOW / 1000 });
  assert.equal(q.label, "Gold spot"); assert.equal(q.change, null); assert.equal(q.changePct, null); assert.equal(q.prevClose, null);
  assert.equal(q.changeAvailable, false); assert.equal(q.noPrevClose, true);
  assert.equal(q.dayHigh, null); assert.equal(q.dayLow, null); assert.equal(q.dayRangeAvailable, false);
  // after the UK day rolls, the last spot seen on the previous UK day is the previous close
  const next = NOW + 86400000;
  const q2 = c.bb8qSpotQuote({ p: 4180.0, ts: next / 1000 });
  assert.equal(q2.prevClose, 4170.3); assert.equal(q2.changeAvailable, true);
  assert.ok(Math.abs(q2.changePct - (4180 / 4170.3 - 1) * 100) < 1e-9);
  assert.match(q2.prevCloseSource, /2026-10-19/);
});

test("timeframes: week-to-date runs from last Friday's close; month and YTD from the prior period's last close", () => {
  const c = load();
  const b = c.bb8qBars(vm.runInContext("__bars(__closes)", c));
  const wk = c.bb8qTfChange(b, c.bb8qTf("gold this week"), null);
  assert.equal(wk.fromDate, "2026-10-16"); assert.equal(wk.from, 4181.1);
  assert.ok(Math.abs(wk.pct - (4189.6 / 4181.1 - 1) * 100) < 1e-9);
  const mo = c.bb8qTfChange(b, c.bb8qTf("this month"), null);
  assert.equal(mo.fromDate, "2026-09-30"); assert.equal(mo.from, 4186.7);
  assert.equal(c.bb8qTf("today").id, "today"); assert.equal(c.bb8qTf("YTD").id, "ytd");
});

test("citations: a figure with no source carrying it is dropped; one carried by exactly one source gets its [n]", async () => {
  const c = load(); c.__st = { chat: true }; const b = body("What is the latest China GDP data?"); c.__st.body = b;
  c.__st.bb8qCtx = await c.bb8qBuild(c.__st, b);
  const full = c.__st.bb8qCtx.sources; c.bb8eFull = () => full;
  const R = n => full[n - 1] || null;
  assert.equal(c.bb8qCiteLine("China's GDP grew 4.5% in the third quarter.", c.__st, R), "");
  assert.equal(c.bb8qCiteLine("The VIX is at 18.65.", c.__st, R), "");
  const reg = c.bb8qCiteLine("The regime is Risk-Off with a score of 37/100.", c.__st, R);
  assert.match(reg, /37\/100\. \[(\d+)\]$/);
  assert.equal(full[Number(/\[(\d+)\]$/.exec(reg)[1]) - 1].bb8qKey, "regime");
  // an existing tag is kept once, never duplicated
  const n = full.findIndex(s => s.bb8qKey === "^TNX") + 1;
  assert.equal(c.bb8qCiteLine("The 10-year yield is 5.10%. [" + n + "]", c.__st, R), "The 10-year yield is 5.10%. [" + n + "]");
});

test("no-data: the server's sentence comes first, with the proxies it fetched itself, cited", async () => {
  const c = load(); c.__st = { chat: true, clientSources: [] }; const b = body("What is the latest China GDP data?"); c.__st.body = b;
  const ctx = c.__st.bb8qCtx = await c.bb8qBuild(c.__st, b);
  assert.deepStrictEqual(plain(ctx.sources.filter(s => s.bb8qProxy).map(s => s.bb8qProxy.sym)), ["USDCNH=X", "^HSI", "HG=F"]);
  const doc = c.bb8qParse({ reply: "Markets were mixed.\n\nIn short: mixed.", sources: [] });
  c.bb8qNoData(doc, c.__st, ctx);
  const out = c.bb8qRender(doc).reply;
  assert.match(out, /^We don't have China GDP figures in our data feed right now/);
  assert.match(out, /USD\/CNH \(offshore yuan\) is down 0\.08% at 6\.6800 \[1\]; the Hang Seng rose 0\.52% in its last session, to 24,186\.83 \[2\]; copper futures \(HG=F\) are up 0\.08% at \$6\.579 \[3\]/);
  const uk = c.bb8qProxies(c.bb8pTopic(body("What is UK inflation doing?"))).map(r => r[0]);
  assert.deepStrictEqual(plain(uk.slice(0, 2)), ["GBPUSD=X", "^FTSE"]);
});

test("render: tokens renumber by first appearance and the source list follows", () => {
  const c = load();
  const A = { name: "A", link: "https://a/", detail: "a" }, B = { name: "B", link: "https://b/", detail: "b" };
  const doc = c.bb8qParse({ reply: "x [2] y [1]\n\nSources:\n[1] A\n[2] B", sources: [A, B] });
  const r = c.bb8qRender(doc);
  assert.match(r.reply, /^x \[1\] y \[2\]/); assert.equal(r.sources[0], B);
});

test("B1: the brief trim keeps the sentence that answers the question", () => {
  const c = load();
  c.__st = { chat: true, body: body("What is Micron's beta?") };
  const orig = "MU fell 5.63% to $878.84.\nSPY fell 1.11%.\nSOXX fell 4.14%.\nMU's published beta is 2.23 (Yahoo Finance).\n\nIn short: MU fell.";
  const r = c.bb8qKeepAns(orig, { text: "MU fell 5.63% to $878.84.\nSPY fell 1.11%.\n\nIn short: MU fell.", cut: true }, 80);
  assert.match(r.text, /published beta is 2\.23/);
});
