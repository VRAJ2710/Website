// Offline tests for deploy/patch_bb8n.py: no beta or card score for non-equities; Sources list only what the
// answer cites, renumbered by first appearance. Loads the bb8e/bb8k helpers, the bb8m block and the bb8n block
// with stubs; no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const E = read("patch_bb8e.py");
const E_FN = E.slice(E.indexOf("function bb8eStrip(q) {"), E.indexOf("// A valuation figure labelled a headwind"));
const K = read("patch_bb8k.py");
const K_FN = K.slice(K.indexOf("function bb8kHintNote(hints) {"), K.indexOf("// Sources for the JSON body"));
const M = read("patch_bb8m.py");
const B8M = M.slice(M.indexOf("// \u2500\u2500 bb8m \u2500\u2500"), M.indexOf("// BB8M_JS_END") + 14);
const PATCH = read("patch_bb8n.py");
const B8N = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8n \u2500\u2500"), PATCH.indexOf("// BB8N_JS_END") + 14);
assert.match(B8N, /function bb8nPrune/);

const STUBS = `
var RT17_ENUMS = { askLength: ["brief", "detailed"], askFocus: ["gold", "macro", "crypto", "em"] };
var BB2_PEERS = { MU: ["NVDA", "AVGO"] }; var RT41S_PEERS = BB2_PEERS;
var BB3_ALIAS = { XAU: "GC=F", XAG: "SI=F", SPX: "^GSPC", FTSE: "^FTSE", WTI: "CL=F", BRENT: "BZ=F", EURUSD: "EURUSD=X", GBPUSD: "GBPUSD=X", BTC: "BTC-USD", ETH: "ETH-USD", DXY: "DX-Y.NYB", US10Y: "^TNX" };
var BB3_MAP = { SOL: { cat: "crypto" }, NATGAS: { cat: "commodity" }, SPY: { cat: "other" }, MU: { cat: "other" } };
function bb3Yahoo(t) { return BB3_ALIAS[t] || t; }
function bb8bYahooSym(t) { return bb3Yahoo(t); }
var QT = { MU: "EQUITY", SPY: "ETF", VWRL: "ETF", ABCD: null, VFIAX: "MUTUALFUND" }, yahooCalls = [];
async function rt32Yahoo(sym) { yahooCalls.push(sym); if (sym === "SLOW") return new Promise(function () {}); var q = QT[sym]; return q ? { price: { quoteType: q } } : {}; }
var LATE = [];
function bb8Late(ms) { return new Promise(function (r) { LATE.push(r); }); }
var __st = null;
function bb8dStore() { return __st; }
function bb2Question(body) { var m = body && body.messages || []; for (var i = m.length - 1; i >= 0; i--) if (m[i].role === "user") return String(m[i].content || ""); return ""; }
function bb2Base(q) { return null; } function rt41sBase(q) { return null; }
function bb3bAskInfo(body) { return { q: bb2Question(body), tickers: body.tickers || [] }; }
function bb2ClientSources(body) { return (body.sources || []).slice(); }
var ASM = null;
function bb8jAssemble(reply, store) { return { reply: String(reply), sources: ASM ? ASM.slice() : [] }; }
function bb2System() { return "SYSTEM"; }
var PACK = null;
async function bb8eMovePack(base) { return PACK ? JSON.parse(JSON.stringify(PACK)) : null; }
function bb8eLead(pack) { return { text: "lead", prompt: "FACTS. Only the Yahoo Finance line may be called beta; never call the card score or its inputs a beta." }; }
function bb8dDrop(sent) { return /buy now/i.test(sent); }
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, isFinite };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS + E_FN + K_FN, ctx);
  vm.runInContext(B8M, ctx, { filename: "bb8m.js" });
  vm.runInContext(B8N, ctx, { filename: "bb8n.js" });
  return ctx;
}
const S = (n) => Array.from({ length: n }, (_, i) => ({ name: "Src" + (i + 1), link: "https://example.org/" + (i + 1) }));
const foot = (n) => "\n\nSources:\n" + Array.from({ length: n }, (_, i) => "[" + (i + 1) + "] Src" + (i + 1) + " | https://example.org/" + (i + 1) + " | as of Mon 19 Oct, 07:1" + i + " UK | headline " + (i + 1)).join("\n");
function check(reply, list) {   // every listed source cited, every [n] resolves, numbered 1..n by first appearance
  const at = reply.lastIndexOf("\nSources:\n"); const body = reply.slice(0, at), f = reply.slice(at);
  const listed = [...f.matchAll(/^\[(\d+)\]/gm)].map(m => +m[1]);
  const order = []; for (const m of body.matchAll(/\[(\d+(?:\s*,\s*\d+)*)\]/g)) for (const x of m[1].split(/\s*,\s*/)) if (!order.includes(+x)) order.push(+x);
  assert.deepEqual(order, listed.slice(0, order.length).length ? order.map((_, i) => i + 1) : []);
  assert.deepEqual(listed, order.map((_, i) => i + 1));
  if (list) assert.equal(list.length, listed.length);
}

test("protocol: bb8n names, no forbidden code, stacked on bb8m (464c5b95)", () => {
  assert.match(PATCH, /464c5b95c3079b067a840b5b0a8fde25/);
  assert.match(PATCH, /REFUSE: bb8n already applied/);
  const code = B8N.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "currentUser", "hasPremiumAccess", "process.env", "require(", ".tier", "cookie"]) assert.equal(code.indexOf(bad), -1, bad);
  for (const m of B8N.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8n/, m[1]);
  for (const m of B8N.matchAll(/^var ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^(?:bb8n|BB8N)/, m[1]);
});

test("equity check by symbol: metals, FX, crypto, indices, rates and futures are not equities", () => {
  const c = load();
  const k = s => c.bb8nKindBySymbol(s);
  assert.equal(k("XAU"), "metal"); assert.equal(k("XAG"), "metal"); assert.equal(k("XAUUSD"), "metal"); assert.equal(k("GC=F"), "metal");
  assert.equal(k("EURUSD"), "fx"); assert.equal(k("GBPUSD=X"), "fx"); assert.equal(k("USDJPY"), "fx");
  assert.equal(k("BTC"), "crypto"); assert.equal(k("ETH-USD"), "crypto"); assert.equal(k("SOL"), "crypto");
  assert.equal(k("SPX"), "index"); assert.equal(k("^GSPC"), "index"); assert.equal(k("FTSE"), "index"); assert.equal(k("^FTSE"), "index"); assert.equal(k("DXY"), "index");
  assert.equal(k("US10Y"), "rates"); assert.equal(k("^TNX"), "rates"); assert.equal(k("ZN=F"), "rates");
  assert.equal(k("WTI"), "future"); assert.equal(k("CL=F"), "future"); assert.equal(k("NATGAS"), "commodity");
  for (const s of ["MU", "NVDA", "AAPL", "SPY", "BRK-B", "VOD.L"]) assert.equal(k(s), null, s);
});

test("equity check by Yahoo quoteType when the pattern cannot tell; assumed equity when nothing answers", async () => {
  const c = load();
  assert.deepEqual(JSON.parse(JSON.stringify(await c.bb8nKind("MU"))), { equity: true, kind: "equity", via: "yahoo quoteType EQUITY" });
  assert.equal((await c.bb8nKind("SPY")).equity, true);   // ETF counts as an equity
  assert.deepEqual(JSON.parse(JSON.stringify(await c.bb8nKind("VFIAX"))), { equity: false, kind: "fund", via: "yahoo quoteType MUTUALFUND" });
  assert.equal((await c.bb8nKind("XAU")).via, "symbol");
  assert.equal((await c.bb8nKind("ABCD")).via, "assumed (no pattern, no quoteType)");
  const slow = c.bb8nKind("SLOW"); c.LATE.forEach(f => f("bb8-late"));   // Yahoo never answers: bb8Late wins, no hang
  assert.equal((await slow).via, "assumed (no pattern, no quoteType)");
  assert.equal(c.bb8nKindByQuoteType("CURRENCY"), "fx"); assert.equal(c.bb8nKindByQuoteType("INDEX"), "index");
  assert.equal(c.bb8nKindByQuoteType("FUTURE"), "future"); assert.equal(c.bb8nKindByQuoteType("CRYPTOCURRENCY"), "crypto");
  assert.equal(c.bb8nKindByQuoteType("WEIRD"), "other"); assert.equal(c.bb8nKindByQuoteType(""), null);
});

test("move pack: non-equity loses card fit and beta; MU keeps beta 2.23; zero / non-finite beta dropped", async () => {
  const c = load();
  for (const t of ["XAU", "EURUSD", "BTC", "SPX", "FTSE", "WTI"]) {
    c.PACK = { base: t, fit: { label: "Neutral", score: 65 }, bb8hBeta: { beta: 0 } };
    c.__st = { chat: true };
    const p = await c.bb8eMovePack(t);
    assert.equal(p.fit, null, t); assert.equal(p.bb8hBeta, null, t); assert.equal(p.bb8nKind.equity, false, t);
    assert.equal(c.__st.bb8nNonEq, true, t);
    const lead = c.bb8eLead(p);
    assert.doesNotMatch(lead.prompt, /may be called beta/); assert.match(lead.prompt, /not an equity/);
  }
  c.PACK = { base: "MU", fit: { label: "Headwind", score: 28 }, bb8hBeta: { beta: 2.23 } }; c.__st = { chat: true };
  const mu = await c.bb8eMovePack("MU");
  assert.equal(mu.bb8hBeta.beta, 2.23); assert.equal(mu.fit.score, 28); assert.equal(c.__st.bb8nNonEq, false);
  assert.match(c.bb8eLead(mu).prompt, /Only the Yahoo Finance line may be called beta/);
  for (const b of [0, NaN, Infinity, null, "x"]) {
    c.PACK = { base: "MU", fit: { score: 28 }, bb8hBeta: { beta: b } };
    assert.equal((await c.bb8eMovePack("MU")).bb8hBeta, null, String(b));
  }
  c.PACK = null; assert.equal(await c.bb8eMovePack("MU"), null);
});

test("client context: Score and Beta removed for a non-equity active ticker; zero beta removed for any", () => {
  const c = load();
  const ctx = t => "Page: Ticker\nActive ticker: " + t + " \u00b7 Score 65/100 \u00b7 Neutral \u00b7 Beta 0.00 \u00b7 Sector X\nRegime: Risk-Off (score 32/100)";
  for (const t of ["XAU Gold", "EURUSD Euro", "BTC Bitcoin", "^FTSE FTSE 100", "WTI Crude"]) {
    const o = c.bb8nContext(ctx(t));
    assert.doesNotMatch(o, /Score 65|Beta/, t); assert.match(o, /Regime: Risk-Off \(score 32\/100\)/); assert.match(o, /Neutral \u00b7 Sector X/);
  }
  const mu = c.bb8nContext("Active ticker: MU Micron \u00b7 Score 28/100 \u00b7 Beta 1.62 \u00b7 Semis");
  assert.match(mu, /Score 28\/100/); assert.match(mu, /Beta 1\.62/);
  assert.doesNotMatch(c.bb8nContext("Active ticker: MU Micron \u00b7 Score 28/100 \u00b7 Beta 0.00 \u00b7 Semis"), /Beta/);
  assert.doesNotMatch(c.bb8nContext("Active ticker: MU Micron \u00b7 Score 28/100 \u00b7 Beta \u2014 \u00b7 Semis"), /Beta/);
  assert.equal(c.bb8nContext("no ticker"), "no ticker");
});

test("restatement filter: beta / card-score sentences dropped for non-equities only; regime and Fear/Greed kept", () => {
  const c = load();
  const beta = "The move came with a published beta of 0.00 for this asset [1].", score = "The card score is 65 out of 100, a Neutral regime fit [2].";
  const keep = ["Regime reading Risk-Off at 32/100 and Fear/Greed at Fear (31/100).", "Underweight: high-beta tech.", "Traders pointed to risk-off headlines [3]."];
  c.__st = { chat: true, bb8nNonEq: true };
  assert.equal(c.bb8dDrop(beta), true); assert.equal(c.bb8dDrop(score), true);
  for (const s of keep) assert.equal(c.bb8dDrop(s), false, s);
  c.__st = { chat: false, bb8nNonEqSym: true };   // flag from the hints hook, no move pack needed
  assert.equal(c.bb8dDrop(beta), true);
  c.__st = { chat: true, bb8nNonEq: false };       // MU: untouched
  assert.equal(c.bb8dDrop("MU's published beta is 2.23 [3]."), false);
  assert.equal(c.bb8dDrop("buy now"), true);       // earlier filter still runs
  c.__st = {}; c.bb8kApplyHints({ messages: [{ role: "user", content: "q" }], tickers: ["XAU"], context: "" });
  assert.equal(c.__st.bb8nNonEqSym, true);
  c.__st = {}; c.bb8kApplyHints({ messages: [{ role: "user", content: "q" }], tickers: ["MU"], context: "" });
  assert.equal(c.__st.bb8nNonEqSym, undefined);
});

test("prune: uncited sources removed, renumbered by first appearance, multi-cite groups and In short rewritten", () => {
  const c = load();
  const src = S(5);
  const r = "Hormuz slows [2]. China beat [1, 4]. Crypto steady [4].\n\nIn short: watch Hormuz [2] and China [1]." + foot(5);
  const p = c.bb8nPrune(r, src);
  assert.match(p.reply, /^Hormuz slows \[1\]\. China beat \[2, 3\]\. Crypto steady \[3\]\.\n\nIn short: watch Hormuz \[1\] and China \[2\]\./);
  assert.match(p.reply, /\[1\] Src2 \|[^\n]*\n\[2\] Src1 \|[^\n]*\n\[3\] Src4 \|/);
  assert.doesNotMatch(p.reply, /Src3|Src5/);
  assert.deepEqual(p.sources.map(s => s.name), ["Src2", "Src1", "Src4"]);
  check(p.reply, p.sources);
});

test("prune: invalid markers removed; zero cites keep the list; misaligned list skipped; no change returns null", () => {
  const c = load();
  const p = c.bb8nPrune("A [1]. B [9]. C [2, 9]." + foot(3), S(3));
  assert.match(p.reply, /^A \[1\]\. B\. C \[2\]\./); check(p.reply, p.sources);
  const z = c.bb8nPrune("No cites here [13]." + foot(3), S(3));
  assert.match(z.reply, /^No cites here\.\n\nSources:\n\[1\] Src1[\s\S]*\[3\] Src3/); assert.equal(z.sources.length, 3);
  assert.equal(c.bb8nPrune("No cites." + foot(3), S(3)), null);
  assert.equal(c.bb8nPrune("A [1]. B [2]." + foot(3), S(2)), null);   // footer 3, list 2: left alone
  assert.equal(c.bb8nPrune("A [1]. B [2]." + foot(2), S(2)), null);
  assert.equal(c.bb8nPrune("A [1].", S(1)), null);
});

test("assembler (stream done + JSON): reply, returned sources and st.bb8jSources are the same pruned list", () => {
  const c = load();
  c.ASM = S(4);
  const st = { chat: true, bb8jSources: S(4) };
  const out = c.bb8jAssemble("Gold near 4,180 [3]. Hormuz [2].\n\nIn short: Hormuz [2]." + foot(4), st);
  assert.match(out.reply, /^Gold near 4,180 \[1\]\. Hormuz \[2\]\.\n\nIn short: Hormuz \[2\]\./);
  assert.deepEqual(out.sources.map(s => s.name), ["Src3", "Src2"]);
  assert.deepEqual(st.bb8jSources.map(s => s.name), ["Src3", "Src2"]);
  check(out.reply, out.sources);
});

test("brief trim keeps a cited sentence when the plain trim would cut every cite", () => {
  const c = load();
  const long = Array.from({ length: 10 }, (_, i) => "Context sentence number " + i + " runs on with eight more plain words here.").join(" ");
  const r = long + "\nHormuz shipping slows as tensions rise [2].\n\nIn short: Hormuz and the dollar matter [2]." + foot(4);
  const t = c.bb8mTrim(r, 80);
  assert.ok(t.cut);
  assert.match(t.text, /Hormuz shipping slows as tensions rise \[2\]\./);
  assert.match(t.text, /In short: Hormuz and the dollar matter \[2\]\./);
  const p = c.bb8nPrune(t.text, S(4)); check(p.reply, p.sources); assert.equal(p.sources.length, 1);
});
