// Offline tests for deploy/patch_bb8p.py (P0, QA chat75): grounding rule, numeric guard, topic-relevant sources,
// admin-only provider/model, meta.quote, honest no-data answer, timeframe kept by the brief trim. Loads the bb8m
// block (trim, scope) and the bb8p block with stubs; no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const M = read("patch_bb8m.py");
const B8M = M.slice(M.indexOf("// \u2500\u2500 bb8m \u2500\u2500"), M.indexOf("// BB8M_JS_END") + 14);
const PATCH = read("patch_bb8p.py");
const B8P = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8p \u2500\u2500"), PATCH.indexOf("// BB8P_JS_END") + 14);
assert.match(B8P, /function bb8pFigs/);

const STUBS = `
var RT17_ENUMS = { askLength: ["brief", "detailed"], askFocus: ["gold", "macro", "crypto", "em"] };
var BB2_PEERS = { MU: ["NVDA", "AVGO"] };
var __st = null;
function bb8dStore() { return __st; }
function bb8dUk(ms) { return "Mon 19 Oct, 12:00 UK"; }
function bb2Question(body) { var m = body && body.messages || []; for (var i = m.length - 1; i >= 0; i--) if (m[i].role === "user") return String(m[i].content || ""); return ""; }
function bb2Footer(sources) { if (!sources || !sources.length) return "\\n\\nSources: No news or price sources were supplied for this answer."; return "\\n\\nSources:\\n" + sources.map(function (s, i) { return "[" + (i + 1) + "] " + s.name + " | " + (s.detail || ""); }).join("\\n"); }
function bb8eIsCard(q) { return /\\s[\u2014-]\\s*Headwind/.test(q); }
function bb8eStrip(q) { return q; }
function bb8eMs(q) { return Number(q.ts) * 1000; }
function bb8iCiteNums(s) { var o = []; String(s).replace(/\\[(\\d+)\\]/g, function (m, g) { o.push(Number(g)); return m; }); return o; }
function bb8iIsNews(src) { return !!(src && src.detail && src.detail.length >= 12); }
function bb8iNewsMatch(sent, src) { return /china/i.test(sent) && /china/i.test(src.detail || ""); }
function isAdminUser(u) { return !!(u && u.email === "admin@box.local"); }
async function currentUser() { return null; }
var lastChatLiveSnapshot = {};
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, isFinite, Buffer };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8M, ctx, { filename: "bb8m.js" });
  vm.runInContext(B8P, ctx, { filename: "bb8p.js" });
  return ctx;
}
const CTX = "Page: Ticker\nLive tape: SPY $763.25 (-1.11%) \u00b7 VIX 24.1 \u00b7 DXY 99.6 \u00b7 Gold $4,180 \u00b7 prices as of 19/10/2026, 07:40\nActive ticker: MU Micron Technology \u00b7 Score 74/100 \u00b7 Semiconductors \u00b7 Memory \u00b7 $878.84 (-5.63%) \u00b7 Beta 1.62 \u00b7 11.8x";
function st(sys, q) {
  return { chat: true, bb8pSys: sys, bb8pMsgs: [{ role: "user", content: q || "" }], bb8pHayVer: 1, body: { context: CTX, messages: [{ role: "user", content: q || "" }] } };
}

test("protocol: bb8p names only, no forbidden code, stacked on bb8n (9b48a917)", () => {
  assert.match(PATCH, /9b48a917c654891a50e7c7c6bd8c9a49/);
  assert.match(PATCH, /REFUSE: bb8p already applied/);
  const code = B8P.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "process.env", "require(", ".tier", "cookie", "hasPremiumAccess"]) assert.equal(code.indexOf(bad), -1, bad);
  for (const m of B8P.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8p/, m[1]);
  for (const m of B8P.matchAll(/^var ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^(?:bb8p|BB8P)/, m[1]);
  // the admin check reuses isAdminUser(currentUser(req)), as /api/ai-status does
  assert.match(code, /currentUser\(req\)[\s\S]*isAdminUser\(u\)/);
});

test("numeric guard: invented China GDP figures are unsupported; context values, rounding and forms are supported", () => {
  const c = load();
  const s = st(CTX + "\nGC=F last 4188.60 USD/oz (as of Mon 19 Oct, 11:39 UK)\nUS 10y Treasury yield 5.10%\nMU's published beta is 2.23 (Yahoo Finance)\nNext earnings: Wed 23 Dec 2026 (estimated)", "What did the latest China GDP data show? Is 4% growth good?");
  const bad = t => c.bb8pFigs(t, s);
  assert.deepEqual(bad("China's Q3 2026 GDP grew 4.5% year-on-year, up from 4.2%."), ["4.5%", "4.2%"]);
  assert.deepEqual(bad("The PBoC held its loan prime rate at 3.10% and the yuan traded near 7.12."), ["3.10%", "7.12"]);
  assert.deepEqual(bad("Gold futures are at $4,188.60, near $4,200 and 4188.6."), []);
  assert.deepEqual(bad("SPY fell 1.1% and the 10-year yield is 5.1%; DXY is 99.6."), []);
  assert.deepEqual(bad("MU's beta is 2.23 and it trades at 11.8x."), []);
  assert.deepEqual(bad("Its beta implies a 2% move."), ["2%"]);              // no rounding across classes
  assert.deepEqual(bad("Earnings are due on 23 Dec 2026."), []);
  assert.deepEqual(bad("Earnings are due on 18 Nov."), ["18-11"]);
  assert.deepEqual(bad("Is 4% growth good? It depends."), []);                 // the question's own number
  assert.deepEqual(bad("Over the past 5 years the S&P 500 rose [1]."), []);    // tenor, index name, cite marker
  assert.deepEqual(bad("Markets price a 25bp cut."), ["25bp"]);
  assert.deepEqual(bad("Growth was 3.8% in 2025."), ["3.8%", "2025"]);
});

test("keep: drops unsupported figures, follow-on 'This ...' sentences and uncited causes; records why", () => {
  const c = load();
  const s = st(CTX, "What did the latest China GDP data show?");
  const R = n => ({ 1: { name: "Reuters", detail: "China GDP growth beats forecasts in third quarter" } })[n];
  assert.equal(c.bb8pKeep("China's GDP grew 4.5% in Q3.", R, s), false);
  assert.equal(c.bb8pKeep("This uptick reflects stronger exports.", R, s), false);
  assert.equal(c.bb8pKeep("Exports were boosted by a rebound in consumer spending.", R, s), false);
  assert.equal(c.bb8pKeep("China's third-quarter growth beat forecasts, driven by exports, Reuters reported [1].", R, s), true);
  assert.equal(c.bb8pKeep("Gold is near $4,180 in the live tape.", R, s), true);
  assert.equal(s.bb8pDrops.length, 3);
  assert.match(s.bb8pDrops[0].why, /unsupported figure 4\.5%/);
});

test("relevance: China GDP keeps only China + GDP headlines; ticker mode uses ticker, company and sector words", () => {
  const c = load();
  const body = { context: CTX, messages: [{ role: "user", content: "What did the latest China GDP data show?\n\n[Answer this question as asked. The reader has MU open; that is background only, do not answer about MU unless the question asks.]" }], knownTickers: ["MU"] };
  const t = c.bb8pTopic(body);
  assert.equal(t.mode, "topic"); assert.deepEqual(t.entities.map(x => x.id), ["china"]); assert.deepEqual(t.series.map(x => x.id), ["gdp"]);
  const S = ["France bond yields jump as budget talks stall", "Putin and Trump to meet for summit", "West Bank settlers attack village", "Kenya pastor charged", "Haiti gangs tighten grip", "France's far right gains", "China GDP growth beats forecasts in third quarter", "China stocks fall in Shanghai", "UK GDP edges up"].map((d, i) => ({ name: "N" + i, detail: d }));
  assert.deepEqual(S.filter(s => c.bb8pRelevant(s, t)).map(s => s.detail), ["China GDP growth beats forecasts in third quarter"]);
  const tk = c.bb8pTopic({ context: CTX, messages: [{ role: "user", content: "What is Micron's beta?" }] });
  assert.equal(tk.mode, "ticker");
  assert.equal(c.bb8pRelevant({ detail: "US Chip Stocks Rebound After Worst Week" }, tk), true);
  assert.equal(c.bb8pRelevant({ detail: "Haiti gangs tighten grip on capital" }, tk), false);
  assert.equal(c.bb8pTopic({ context: "Page: Home", messages: [{ role: "user", content: "What's moving markets?" }] }).mode, "none");
  assert.equal(c.bb8pIsServerSrc({ name: "Yahoo Finance quote", link: "https://finance.yahoo.com/quote/MU/" }), true);
});

test("honest fallback: no-data opener, related Yahoo quotes and topic news, all cited 1..n", () => {
  const c = load();
  const s = st(CTX, "What did the latest China GDP data show?");
  s.bb8pTopic = c.bb8pTopic(s.body);
  s.clientSources = [{ name: "Reuters", detail: "China GDP growth beats forecasts in third quarter", asOf: "2026-10-19T06:10:00.000Z" }];
  s.bb8pRel = [{ sym: "CNH=X", label: "USD/CNH (offshore yuan)", dp: 4, q: { p: 6.6799, c: -0.08, ts: 1792407424, currency: "CNH", status: "fresh" } }, { sym: "^HSI", label: "the Hang Seng", dp: 2, q: { p: 24186.83, c: 0.52, ts: 1792138118, currency: "HKD", status: "closed" } }];
  const out = c.bb8pFallback({ reply: "\n\nSources: No news or price sources were supplied for this answer.", sources: [] }, s);
  assert.match(out.reply, /^We don't have China GDP figures in our data feed right now/);
  assert.match(out.reply, /In the news \(Reuters, Mon 19 Oct, 12:00 UK\): "China GDP growth beats forecasts in third quarter" \[1\]/);
  assert.match(out.reply, /USD\/CNH \(offshore yuan\) is down 0\.08% at 6\.6799; the Hang Seng rose 0\.52% in its last session, to 24,186\.83\. \[2\]/);
  assert.equal(out.sources.length, 2); assert.equal(s.bb8jSources.length, 2); assert.equal(s.bb8pNoData, true);
  assert.equal(c.bb8pHasFigure("UK CPI inflation was 3.8% in September. [1]"), true);
  assert.equal(c.bb8pHasFigure("Gold is a hedge in 2026."), false);
});

test("timeframe: the brief trim keeps the 'this week' sentence", () => {
  const c = load();
  c.__st = st(CTX, "What's the outlook for gold this week?");
  const long = "Gold is trading near $4,180 in the supplied live tape. The dollar index is at 99.6. Shipping through Hormuz is slowing. China's growth beat forecasts. The context lists Gold and Treasuries as overweight themes, which fits the defensive rotation it describes. Crypto is steadier after weekend swings, and European trading opened with pharma stocks in the lead. For this week, the things to watch are the Hormuz headlines and the dollar index around 99.6.\n\nIn short: gold sits near $4,180.";
  const r = c.bb8mTrim(long, 40);
  assert.equal(r.cut, true);
  assert.match(r.text, /For this week, the things to watch/);
  assert.match(r.text, /In short: gold sits near \$4,180\./);
  assert.ok(c.bb8mWords(r.text.replace(/In short:.*$/m, "")) <= 40);
});

test("meta: provider/model only for admins; quote and grounding added", () => {
  const c = load();
  const s = st(CTX, "gold this week?");
  s.bb8pTopic = c.bb8pTopic({ context: CTX, messages: [{ role: "user", content: "What's the outlook for gold this week?" }] });
  s.bb8pGold = { goldLast: 4188.6, goldTs: 1792406818, dayHigh: 4211.2, dayLow: 4176, sessionDate: "2026-10-19" };
  const pub = c.bb8pMetaFix({ provider: "OpenAI", model: "gpt-4o-mini", streamed: true }, false, s);
  assert.equal(pub.provider, undefined); assert.equal(pub.model, undefined); assert.equal(pub.streamed, true);
  assert.equal(pub.quote.feedSymbol, "GC=F"); assert.equal(pub.quote.price, 4188.6); assert.equal(pub.quote.asOf, "2026-10-19T10:46:58.000Z");
  assert.deepEqual(Object.keys(pub.grounding), ["dropped", "noData", "sourcesDropped"]);
  const adm = c.bb8pMetaFix({ provider: "OpenAI", model: "gpt-4o-mini" }, true, s);
  assert.equal(adm.provider, "OpenAI"); assert.equal(adm.model, "gpt-4o-mini");
  s.bb8pGold = null; s.bb8eMove = { text: "lead" }; s.bb8eMoveR = { base: "MU", ysym: "MU", ms: 1792094400000, q: { p: 878.84, c: -5.63, prev: 931.24, currency: "USD", status: "closed", name: "Micron" } };
  const q = c.bb8pMetaFix({}, false, s).quote;
  assert.equal(q.symbol, "MU"); assert.equal(q.price, 878.84); assert.equal(q.session, "closed");
});

test("grounding rule goes first and the chat prompt clip is the same on both paths", () => {
  const c = load();
  assert.match(c.BB8P_GROUND, /^GROUNDING \(both answer paths/);
  assert.match(c.BB8P_GROUND, /Never state a figure/);
  assert.equal(c.BB8P_CLIP, 14000);
});
