// Offline tests for the Ask part of deploy/patch_bb8i.py. Loads the bb8d, bb8e, bb8g, bb8h and bb8i blocks with stubs; no network.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

function blockOf(file, start, end) {
  const s = fs.readFileSync(path.join(__dirname, "../deploy", file), "utf8");
  return s.slice(s.indexOf(start), s.indexOf(end) + end.length);
}
const B8D = blockOf("patch_bb8d.py", "// \u2500\u2500 bb8d \u2500\u2500", "// BB8D_JS_END");
const B8E = blockOf("patch_bb8e.py", "// \u2500\u2500 bb8e \u2500\u2500", "// BB8E_JS_END");
const B8G = blockOf("patch_bb8g.py", "// \u2500\u2500 bb8g \u2500\u2500", "// BB8G_JS_END");
const B8H = blockOf("patch_bb8h.py", "// \u2500\u2500 bb8h \u2500\u2500", "// BB8H_JS_END");
const B8I = blockOf("patch_bb8i.py", "// \u2500\u2500 bb8i \u2500\u2500", "// BB8I_JS_END");
const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8i.py"), "utf8");
assert.match(PATCH, /dabd441e6cd87c6ce828601861142798/);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env", "require("]) assert.equal(B8I.includes(bad), false, bad);
for (const m of B8I.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8i/, m[1]);

const FRI = Date.parse("2026-10-16T20:00:00Z");
const STUBS = `
var bb2Als = { getStore: function () { return globalThis.__store || null; } };
var bb2Mem = { vals: new Map() };
var BB2_PEERS = { MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"] };
function bb8cAllowed(facts) { var set = {}; (facts || []).forEach(function (f) { (String(f.sentence).match(/\\d+(?:\\.\\d+)?(?=x)/g) || []).forEach(function (n) { set[Number(n).toFixed(1)] = 1; }); }); return set; }
function bb8bFillerRe() { return /[^.!?\\n]*\\bthis (?:valuation )?(?:metric|ratio) (?:provides|gives)[^.!?\\n]*[.!?]?/gi; }
function bb2Question(body) { var m = (body && body.messages) || []; for (var i = m.length - 1; i >= 0; i--) if (m[i].role === "user") return String(m[i].content || ""); return ""; }
function bb2Base(q) { var t = /\\[Answer this question as asked, about ([A-Z]{1,5})\\b/.exec(q); if (t && BB2_PEERS[t[1]]) return t[1]; var m = /\\b(MU)\\b/.exec(q); return m ? m[1] : null; }
function bb2PeerAsk(q) { return /peer|compar|versus|\\bvs\\.?\\b|valuation|p\\/e|multiple|cheap|expensive|premium|discount/i.test(String(q || "")); }
var bb2Read0 = async function (req) { return req.body; };
function bb3LeadText(built, cite) { return (built.asOf ? "Peer comparisons as of " + built.asOf + ":" : "Peer comparisons:") + (cite ? " [" + cite + "]" : "") + "\\n" + built.facts.map(function (f) { return f.sentence; }).join("\\n") + "\\n\\n"; }
function bb3bCompose(reply, built, cite) { return String(reply); }
async function bb2Complete(system, messages, onDelta) {
  globalThis.__system = system;
  var text = globalThis.__model, n = globalThis.__chunk || 7;
  for (var i = 0; i < text.length; i += n) { onDelta(text.slice(i, i + n)); await new Promise(function (r) { setTimeout(r, 0); }); }
  return { provider: "stub" };
}
async function generateAi(options) { globalThis.__genSystem = options.system; return { text: "{}" }; }
function bb2Footer(sources) { return "\\n\\nSources:\\n" + sources.map(function (s, i) { return "[" + (i + 1) + "] " + s.name + " | " + (s.detail || ""); }).join("\\n"); }
function bb2System() { return "BASE SYSTEM"; }
async function buildChatLiveMarketBlock() { return ""; }
function bb2FixSentence(s) { return s; }
function bb5eLondon(ms) { return ""; }
function bb5hHm(ms) { return ""; }
function bb5gJoinStream(acc, piece, firstModel) { return { acc: acc + piece, piece: piece }; }
function bb7HouseView(index) { return { items: [], asOf: "", note: "No PDF text library is installed, so each Periodic Transaction Report is listed with its link and marked See filing." }; }
async function rt41sPeerBlock(base) { return "PEER VALUATIONS block for " + base; }
var rt37sNewsCache = new Map();
async function rt37sNews(res) { res.end(JSON.stringify({ items: globalThis.__news || [] })); }
function bb5eParts(tz, d) { var o = {}; new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d).forEach(function (x) { o[x.type] = x.value; }); return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) }; }
function bb5eNow() { return Date.now(); }
function bb6Shut(spec, d) { return !!(globalThis.__holiday && globalThis.__holiday(spec, d)); }
function bb5gSpec(sym) {
  if (/\\.L$/.test(sym)) return { mode: "cash", tz: "Europe/London", o: 480, c: 990, label: "London" };
  if (/\\.DE$/.test(sym)) return { mode: "cash", tz: "Europe/Berlin", o: 540, c: 1050, label: "Frankfurt" };
  if (/\\.T$/.test(sym)) return { mode: "cash", tz: "Asia/Tokyo", o: 540, c: 930, lo: 690, lc: 750, label: "Tokyo" };
  if (/-USD$/.test(sym)) return { mode: "always", label: "Crypto" };
  return { mode: "cash", tz: "America/New_York", o: 570, c: 960, label: "US" };
}
function bb5eOpenAt(spec, d) {
  if (spec.mode === "always") return true;
  if (bb6Shut(spec, d)) return false;
  var p = bb5eParts(spec.tz, d);
  if (p.wd === "Sat" || p.wd === "Sun") return false;
  if (spec.lo != null && p.m >= spec.lo && p.m < spec.lc) return false;
  return p.m >= spec.o && p.m < spec.c;
}
// Pre-bb8e behaviour of the chain: an open venue whose last print is older than cadence + delay + margin is stale.
function bb5eApply(q, symbol, hints, now) {
  var out = Object.assign({}, q), spec = bb5gSpec(symbol), t = now == null ? Date.now() : now;
  if (!bb5eOpenAt(spec, new Date(t))) { out.status = "closed"; out.stale = false; out.note = "closed"; return out; }
  var age = t - out.ts * 1000;
  if (age > 60000 + out.delayMin * 60000 + 120000) { out.status = "stale"; out.stale = true; delete out.note; }
  else { out.status = "delayed"; out.stale = false; out.note = "delayed " + out.delayMin + " min by exchange"; }
  return out;
}
function bb5hRetouch(q, now, cadence) { var age = now - q.ts * 1000; if (q.status !== "closed" && age > cadence + q.delayMin * 60000 + 120000) { q.status = "stale"; q.stale = true; delete q.note; } return q; }
function bb5gApply(q, symbol, now, cadence) { var next = bb5eApply(q, symbol, null, now); return cadence > 0 ? bb5hRetouch(next, now, cadence) : next; }
function rt33sBriefDate(b) { b.date = "2026-10-19"; return b; }
function json(res, status, body) { res.body = body; return body; }
var __Q = {
  MU: { p: 878.84, c: -5.6269060607362205, prev: 931.24, currency: "USD", basis: "previous_close", name: "Micron Technology, Inc.", ts: ${FRI / 1000}, status: "closed" },
  SPY: { p: 763.25, c: -1.1065186125759552, prev: 771.79, currency: "USD", ts: ${FRI / 1000}, status: "closed" },
  SOXX: { p: 493.39, c: -4.142138291465106, prev: 514.71, currency: "USD", ts: ${FRI / 1000}, status: "closed" }
};
async function bb3Pack(now) { return { quotes: { SPY: __Q.SPY }, extra: {}, at: now }; }
async function bb3OneQuote(pack, sym) { return __Q[sym] || null; }
function bb3Yahoo(t) { return t; }
function bb3Known(t) { return t === "MU"; }
function bb3Hit() { return null; }
async function bb3Compute(t) { return { label: "Headwind", score: 28, reason: "Headwind, 28 out of 100, while the market mood is Risk-Off. The score starts at 50. Today's fall is past 2 percent, which takes off 10. This name moves more sharply than the market, and the mood is wary of that, which takes off 12." }; }
`;
const EXTRA = `
var bb5BetaMem = {};
async function rt32Yahoo(sym) { globalThis.__yahooCalls = (globalThis.__yahooCalls || 0) + 1; return globalThis.__yahoo || null; }
function bb8bYahooSym(s) { return s; }
function bb2ClientSources(body) { return (body.sources || []).filter(function (s) { return s && s.name; }).map(function (s) { return { name: s.name, link: s.link || "", asOf: s.asOf || "", detail: s.detail || "" }; }); }
bb3Compute = async function (t) { return { label: "Headwind", score: 28, regime: "Risk-Off", asOf: "2026-10-19T07:40:00.000Z",
  reason: "Headwind, 28 out of 100, while the market mood is Risk-Off. The score starts at 50. Today's fall is past 2 percent, which takes off 10. This name moves more sharply than the market, and the mood is wary of that, which takes off 12.",
  inputs: [{ key: "session", value: -5.63 }, { key: "sensitivity", value: 2.23, unit: "times the market", source: "Dispatch desk reference" }] }; };
`;
function load() {
  const ctx = { console: { warn() {} }, Promise, Map, Set, Date, JSON, Math, Intl, Object, String, Number, Array, RegExp, Error, URL, setTimeout, clearTimeout };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8D, ctx, { filename: "bb8d.js" });
  vm.runInContext(EXTRA, ctx);
  vm.runInContext(B8E, ctx, { filename: "bb8e.js" });
  vm.runInContext(B8G, ctx, { filename: "bb8g.js" });
  vm.runInContext(B8H, ctx, { filename: "bb8h.js" });
  vm.runInContext(B8I, ctx, { filename: "bb8i.js" });
  return ctx;
}
const NOTE = "\n\n[Answer this question as asked, about MU. Quote valuation only from the live figures supplied, including the PEER VALUATIONS block when comparing.]";
const CARD_Q = "What matters most about MU — Headwind?" + NOTE;
const NEWS = [
  { title: "INTC, AMD, MU, SNDK: US Chip Stocks Rebound After Worst Week Since March", link: "https://stocktwits.com/news-articles/a", ts: FRI + 9 * 3600e3, source: "Yahoo Finance" },
  { title: "Micron shares slide as chipmakers retreat", link: "https://finance.yahoo.com/news/b", ts: FRI - 2 * 3600e3, source: "Yahoo Finance" }
];
// Client numbering (stream): 1-7 client, 8 quote, 9 Stocktwits, 10 Yahoo news, 11 The Dispatch, 12 Yahoo beta.
const MODEL_CARD = [
  "MU's beta of 2.23 means it tends to amplify market moves [9].",
  "SPY fell 1.11% in the same session, a much smaller drop [3].",
  "Chip stocks have fallen 12% this month, extending the slide [8].",
  "Memory makers are sensitive to swings in AI spending expectations [9].",
  "MU lagged its sector by 1.48 percentage points [2].",
  "Sources: [9] Yahoo Finance news"
].join("\n");
const CLIENT = ["Reuters", "Bloomberg", "Reuters", "BBC", "CoinDesk", "Reuters"].map((n, i) => ({ name: n, link: "https://www." + n.toLowerCase() + ".com/" + i, detail: "general headline " + i })).concat([{ name: "Yahoo Finance quote", detail: "MU price" }]);
const YQ = (sd, ks) => ({ summaryDetail: { beta: sd }, defaultKeyStatistics: { beta: ks } });

async function streamRun(chunk, yahoo, model, q, tickers) {
  const ctx = load();
  ctx.__news = NEWS;
  ctx.__yahoo = yahoo === undefined ? YQ({ raw: 2.226, fmt: "2.23" }, { raw: 2.226, fmt: "2.23" }) : yahoo;
  const st = { chat: true, facts: [], clientSources: CLIENT.map(s => Object.assign({}, s)), peerSource: null };
  ctx.__store = st;
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: q || CARD_Q }], tickers: tickers || ["MU"] } });
  ctx.__model = model || MODEL_CARD; ctx.__chunk = chunk;
  let acc = "";
  await ctx.bb2Complete("BASE SYSTEM\n\nDo not write a concluding or summary sentence; the server adds it.", [], d => { const j = ctx.bb5gJoinStream(acc, d.replace(/^\n+|\n+$/g, ""), !acc); acc = j.acc; });
  const reply = ctx.bb3bCompose(acc, { facts: [] }, 0);
  const foot = st.clientSources.slice();
  const footer = ctx.bb2Footer(foot);
  return { ctx, st, painted: acc, reply, footer, foot };
}
const cites = (s) => [...new Set((s.split("\n\nSources:")[0].match(/\[(\d+)\]/g) || []).map(x => +x.slice(1, -1)))].sort((a, b) => a - b);
const numOf = (foot, re) => foot.findIndex(s => re.test(s.name + " " + (s.detail || "") + " " + (s.link || ""))) + 1;
const bodyOf = (reply) => reply.split("\n\n")[1] || "";


const SPEC_YES = [
  "Analysts see MU's margins widening next year.", "Analysts expect a strong quarter.", "Analysts believe the cycle has turned.",
  "Investors expect further rate cuts.", "Investors are favoring defensive names.", "The market believes the Fed will cut.",
  "The market is pricing two cuts this year.", "Traders expect volatility to stay high.", "Many expect a rebound.",
  "MU is likely to stay volatile.", "Memory makers could see further gains.", "Micron is poised to benefit from AI demand.",
  "The low P/E reflects expectations for strong memory pricing."
];
const SPEC_NO = [
  "Earnings are expected on 18 Nov.", "MU's next earnings are expected on 18 Dec.", "MU is expected to report on 18 Dec.",
  "MU fell 5.63% in its last session.", "The company expects revenue of $8.7bn, according to its guidance.", "Shares climbed in Seoul."
];
test("a) speculative / attributed claim detection; plain 'expected' facts are not matched", () => {
  const ctx = load();
  for (const s of SPEC_YES) assert.equal(ctx.bb8iSpec(s), true, s);
  for (const s of SPEC_NO) assert.equal(ctx.bb8iSpec(s), false, s);
  assert.match(ctx.BB8I_RULE, /analysts, investors, traders or the market/);
});

test("a) kept only with a cited NEWS line that shares a ticker or topic words", () => {
  const ctx = load();
  const quote = { name: "Yahoo Finance quote", link: "https://finance.yahoo.com/quote/MU/", detail: "MU, SPY, SOXX last price and session change" };
  const peer = { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/MU/key-statistics/", detail: "trailing P/E (TTM) and forward P/E, refreshed on request" };
  const st = { peerSource: peer };
  const news = [
    { name: "Stocktwits", link: "https://stocktwits.com/a", detail: "INTC, AMD, MU, SNDK: US Chip Stocks Rebound After Worst Week Since March" },
    { name: "Reuters", link: "https://example.org/2", detail: "Pharma stocks lead European open" },
    { name: "CoinDesk", link: "https://example.org/4", detail: "Bitcoin steadies after weekend swings" }
  ];
  const all = [quote, peer, { name: "The Dispatch", link: "https://thedispatch.uk/", detail: "Pulse card score (regime fit)" }].concat(news);
  const R = n => all[n - 1] || null;
  const K = s => ctx.bb8iKeep(s, R, st);
  assert.equal(K("Analysts see MU rebounding after its worst week since March [4]."), true, "ticker match on a news line");
  assert.equal(K("Analysts see chip stocks rebounding after a rough week [4]."), true, "topic words (chip, rebound)");
  assert.equal(K("Investors expect memory prices to keep rising [5]."), false, "news line on another topic");
  assert.equal(K("Investors are favoring MU over NVDA [1]."), false, "a quote line is not news");
  assert.equal(K("Investors are favoring MU over NVDA [2]."), false, "the peer valuation line is not news");
  assert.equal(K("MU is likely to stay volatile [3]."), false, "the card score line is not news");
  assert.equal(K("Traders expect the Bank of England to cut rates."), false, "uncited");
  assert.equal(K("Bitcoin is likely to stay range-bound [6]."), true);
  assert.equal(K("Earnings are expected on 18 Nov [1]."), true, "plain fact with a fact cite");
  assert.equal(K("MU fell 5.63% [1]."), true);
  assert.equal(ctx.bb8iLine("- Analysts expect more gains [5]. MU fell 5.63% [1].", R, st), "- MU fell 5.63% [1].");
  assert.equal(ctx.bb8iLine("Analysts expect more gains [5].", R, st), "");
});

// Stream numbering: 1-7 client, 8 quote, 9 Stocktwits (chip-stock rebound headline), 10 Yahoo news (Micron slide), 11 The Dispatch, 12 Yahoo beta.
const MODEL_SPEC = [
  "Analysts see chip stocks including MU rebounding after their worst week since March [9].",
  "Investors expect memory prices to keep rising [3].",
  "Some investors believe Micron (MU) shares slid as chipmakers retreat [10].",
  "MU is likely to stay volatile [8].",
  "Traders expect the selling to continue."
].join("\n");
test("a) card answers, stream at chunks 1, 3, 7, 13 plus JSON: speculation kept only with a matching news cite, before In short", async () => {
  for (const chunk of [1, 3, 7, 13]) {
    const { reply, foot } = await streamRun(chunk, undefined, MODEL_SPEC);
    const parts = reply.split("\n\n");
    assert.match(parts[parts.length - 1], /^In short: /);
    const prose = parts.slice(1, -1).join("\n\n");
    const st = numOf(foot, /stocktwits/i), yn = numOf(foot, /finance\.yahoo\.com\/news/);
    assert.equal(prose, "Analysts see chip stocks including MU rebounding after their worst week since March [" + st + "].\nSome investors believe Micron (MU) shares slid as chipmakers retreat [" + yn + "].", "chunk " + chunk + "\n" + reply);
    assert.deepEqual(cites(reply), foot.map((_, i) => i + 1));
  }
  const ctx = load();
  ctx.__news = NEWS; ctx.__yahoo = YQ({ raw: 2.226 }, null);
  ctx.__store = { chat: true, facts: [], clientSources: [], peerSource: null };
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  await ctx.generateAi({ system: "ORIGINAL", messages: [] });
  assert.ok(ctx.__genSystem.indexOf(ctx.BB8I_RULE) >= 0, "JSON prompt carries the rule");
  const out = ctx.bb3bCompose(MODEL_SPEC.replace(/\[9\]/, "[2]").replace(/\[10\]/, "[3]").replace(/\[8\]/, "[1]").replace(/\[3\]\./, "[4]."), { facts: [] }, 0);
  assert.match(out, /\n\nAnalysts see chip stocks including MU rebounding after their worst week since March \[2\]\.\nSome investors believe Micron \(MU\) shares slid as chipmakers retreat \[3\]\.\n\nIn short: /);
  assert.doesNotMatch(out, /memory prices|likely to stay|Traders expect/);
});

test("a) valuation answers: attributed claims need a news cite; the factual 'expected on 18 Dec' sentence stays", () => {
  const ctx = load();
  const facts = [{ a: "MU", b: "NVDA", sentence: "MU forward P/E (next 12 months) 4.9x is lower than NVDA forward P/E (next 12 months) 15.3x by 10.4x (68.0%)." }];
  const peer = { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/MU/key-statistics/", detail: "trailing P/E (TTM) and forward P/E" };
  ctx.__store = { chat: true, facts, clientSources: [{ name: "Reuters", link: "https://example.org/r", detail: "Micron shares rise" }, { name: "Yahoo Finance quote", detail: "MU price" }], peerSource: peer, bb8eMode: "valuation" };
  const body = ctx.bb8dBody([
    "Micron (MU) has the lowest forward P/E in the group [3].",
    "Analysts expect Micron shares to rise further on memory pricing [1].",
    "Investors are favoring NVDA over memory names [3].",
    "The market is pricing a sharp earnings cycle for memory makers.",
    "MU's next earnings are expected on 18 Dec [2]."
  ].join("\n"), facts);
  assert.equal(body, [
    "Micron (MU) has the lowest forward P/E in the group [3].",
    "Analysts expect Micron shares to rise further on memory pricing [1].",
    "MU's next earnings are expected on 18 Dec [2]."
  ].join("\n"));
});

const GEN_Q = "What's moving markets this morning?";
const GEN_CLIENT = [["Reuters", "China GDP growth beats forecasts in third quarter"], ["Reuters", "Pharma stocks lead European open"], ["CoinDesk", "Bitcoin steadies after weekend swings"], ["Reuters", "SK Hynix shares climb in Seoul"]].map(([n, d], i) => ({ name: n, link: "https://example.org/" + i, detail: d }));
const MODEL_GEN = [
  "China's third-quarter GDP growth beat forecasts [1].",
  "Analysts expect the China GDP beat to support commodity demand [1].",
  "Investors expect oil prices to rise as Hormuz shipping slows [2].",
  "Traders expect the Bank of England to cut rates in November.",
  "SK Hynix shares climbed in Seoul, and memory makers could see further gains [4].",
  "Earnings season is expected to start next week."
].join("\n");
test("a) general answers, stream at chunks 1, 3, 7, 13 plus final: filtered whole sentences, lines kept apart, Sources renumbered", async () => {
  for (const chunk of [1, 3, 7, 13]) {
    const ctx = load();
    ctx.__news = []; ctx.__yahoo = null;
    const st = { chat: true, facts: [], clientSources: GEN_CLIENT.map(s => Object.assign({}, s)), peerSource: null };
    ctx.__store = st;
    await ctx.bb2Read0({ body: { messages: [{ role: "user", content: GEN_Q }], tickers: [] } });
    ctx.__model = MODEL_GEN; ctx.__chunk = chunk;
    let painted = "";
    await ctx.bb2Complete(ctx.bb2System(), [], d => { painted += d; });
    assert.ok(ctx.__system.indexOf(ctx.BB8I_RULE) >= 0);
    assert.doesNotMatch(painted, /oil prices|Bank of England/, "dropped while streaming, chunk " + chunk);
    const reply = ctx.bb3bCompose("glued text the pump produced", { facts: [] }, 0);
    assert.equal(reply, [
      "China's third-quarter GDP growth beat forecasts [1].",
      "Analysts expect the China GDP beat to support commodity demand [1].",
      "SK Hynix shares climbed in Seoul, and memory makers could see further gains [2].",
      "Earnings season is expected to start next week."
    ].join("\n"), "chunk " + chunk);
    const keep = st.bb8eCites.keep.map(i => st.bb8eCites.full[i]);
    assert.deepEqual(keep.map(s => s.detail), ["China GDP growth beats forecasts in third quarter", "SK Hynix shares climb in Seoul"]);
  }
});
