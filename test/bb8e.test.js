// Offline tests for deploy/patch_bb8e.py (stacked on bb8d). Loads the bb8d and bb8e blocks with stubs; no network.
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
const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8e.py"), "utf8");
assert.match(PATCH, /e0a1e5ea2ba975298bd9a2177abd5a6f/);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env", "require("]) assert.equal(B8E.includes(bad), false, bad);
for (const m of B8E.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8e/, m[1]);

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
function load() {
  const ctx = { console: { warn() {} }, Promise, Map, Set, Date, JSON, Math, Intl, Object, String, Number, Array, RegExp, Error, URL, setTimeout, clearTimeout };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8D, ctx, { filename: "bb8d.js" });
  vm.runInContext(B8E, ctx, { filename: "bb8e.js" });
  return ctx;
}
const NOTE = "\n\n[Answer this question as asked, about MU. Quote valuation only from the live figures supplied, including the PEER VALUATIONS block when comparing.]";
const CARD_Q = "What matters most about MU — Headwind?" + NOTE;
const NEWS = [
  { title: "INTC, AMD, MU, SNDK: US Chip Stocks Rebound After Worst Week Since March", link: "https://stocktwits.com/a", ts: FRI + 9 * 3600e3 },
  { title: "Micron shares slide as chipmakers retreat", link: "https://www.reuters.com/b", ts: FRI - 2 * 3600e3 },
  { title: "Why Micron's Latest Long-Term Deals Are a Game-Changer for Investors", link: "https://www.fool.com/c", ts: FRI + 3600e3 },
  { title: "Does Micron (MU) Have an Economic Moat at All?", link: "https://finance.yahoo.com/d", ts: FRI + 3600e3 },
  { title: "Micron Stock Alert: Elon Musk Just Made The Bull Case Even Stronger", link: "https://example.com/e", ts: FRI + 3600e3 },
  { title: "Micron results date set", link: "https://example.com/old", ts: FRI - 5 * 86400e3 }
];
const MODEL_CARD = [
  "Micron (MU) faces a significant headwind: its trailing P/E (TTM) of 11.8x, which indicates a relatively low valuation compared with peers.",
  "The stock fell sharply on Friday as chip stocks sold off after a strong run [7]. Memory makers are sensitive to swings in AI spending expectations, so a high-beta name like MU tends to fall further than the market on risk-off days.",
  "A high forward P/E would be a tailwind for sentiment.",
  "Investors will watch upcoming chip earnings for signs that memory pricing (DRAM and NAND) is holding up.",
  "In short, MU looks like an opportunity after the drop.",
  "Sources: [7] Yahoo Finance quote"
].join("\n");
const CLIENT = ["Reuters", "Bloomberg", "Reuters", "BBC", "CoinDesk", "Reuters"].map((n, i) => ({ name: n, detail: "general headline " + i })).concat([{ name: "Yahoo Finance quote", detail: "MU price" }]);

test("intent is deterministic: card label/flag and non-valuation questions are move questions", () => {
  const ctx = load();
  const it = q => ctx.bb8eIntent(q, null);
  assert.deepEqual([it(CARD_Q).mode, it(CARD_Q).card], ["move", true]);
  assert.equal(it("What matters most about MU — Tailwind?").mode, "move");
  assert.equal(it("How does Micron (MU) compare with its peers on valuation?" + NOTE).mode, "valuation");
  assert.equal(it("Is MU cheap versus NVDA?").mode, "valuation");
  assert.equal(it("How did MU perform versus SPY this week?").mode, "move");
  assert.equal(it("What is driving MU today?" + NOTE).mode, "move");
  assert.equal(ctx.bb8eIntent("Tell me about MU", { card: true }).card, true);
  ctx.__store = { chat: true };
  assert.equal(ctx.bb2PeerAsk(CARD_Q), false, "the client note's 'valuation'/'PEER' words no longer make a card question a peer question");
  assert.equal(ctx.bb2PeerAsk("How does Micron (MU) compare with its peers on valuation?" + NOTE), true);
});

test("move lead: move, SPY, sector, card score, neutral headlines; cites numbered after the prompt's sources", () => {
  const ctx = load();
  const pack = { base: "MU", ysym: "MU", q: { p: 878.84, c: -5.6269, prev: 931.24, currency: "USD", status: "closed" }, ms: FRI,
    bench: { sym: "SPY", label: "SPY (S&P 500 ETF)", q: { c: -1.1065 } }, sector: { sym: "SOXX", label: "SOXX (semiconductor ETF)", q: { c: -4.1421 } },
    fit: { label: "Headwind", score: 28, reason: "Headwind, 28 out of 100, while the market mood is Risk-Off. The score starts at 50. Today's fall is past 2 percent, which takes off 10." },
    news: ctx.bb8ePickNews(NEWS, "MU", "Micron Technology, Inc.", FRI) };
  assert.deepEqual(pack.news.map(n => n.link), ["https://stocktwits.com/a", "https://www.reuters.com/b"], "opinion hosts, question and promo titles, and stale items are skipped");
  const lead = ctx.bb8eLead(pack, true, 7);
  assert.equal(lead.text, [
    "Why MU reads Headwind (card score 28/100), as of Fri 16 Oct, 21:00 UK:",
    "MU fell 5.63% to $878.84 in its last session (previous close $931.24). [8]",
    "SPY (S&P 500 ETF) fell 1.11% in the same session, so MU lagged the market by 4.52 percentage points. [8]",
    "SOXX (semiconductor ETF) fell 4.14% in the same session, so MU lagged its sector by 1.48 percentage points. [8]",
    "Card score (Dispatch regime fit): Headwind, 28 out of 100, while the market mood is Risk-Off. Today's fall is past 2 percent, which takes off 10.",
    "In the news (Sat 17 Oct, 06:00 UK), not confirmed as the cause: \"INTC, AMD, MU, SNDK: US Chip Stocks Rebound After Worst Week Since March\" [9]",
    "In the news (Fri 16 Oct, 19:00 UK), not confirmed as the cause: \"Micron shares slide as chipmakers retreat\" [10]"
  ].join("\n"));
  assert.doesNotMatch(lead.paint, /\[\d+\]/);
  assert.match(lead.prompt, /^CARD AND MOVE FACTS/);
  assert.match(lead.prompt, /Do not discuss valuation multiples/);
  assert.equal(lead.sources.length, 3);
  assert.equal(ctx.bb8eRel("MU", 1.2, 1.21, "the market"), "MU moved in line with the market");
  assert.equal(ctx.bb8eRel("MU", 2, 1, "its sector"), "MU outperformed its sector by 1.00 percentage points");
  const gmt = ctx.bb8eLead(Object.assign({}, pack, { ms: Date.parse("2026-11-20T21:00:00Z"), news: [] }), false, 0);
  assert.match(gmt.text, /^MU's latest move, as of Fri 20 Nov, 21:00 UK:/);
});

async function streamRun(chunk) {
  const ctx = load();
  ctx.__news = NEWS;
  const st = { chat: true, facts: [], clientSources: CLIENT.slice(), peerSource: null };
  ctx.__store = st;
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  ctx.__model = MODEL_CARD; ctx.__chunk = chunk;
  let acc = "";
  // Mimic the stream pump: every delta is passed through bb5gJoinStream after trimming edge newlines.
  await ctx.bb2Complete("BASE SYSTEM\n\nDo not write a concluding or summary sentence; the server adds it.", [], d => { const j = ctx.bb5gJoinStream(acc, d.replace(/^\n+|\n+$/g, ""), !acc); acc = j.acc; });
  const reply = ctx.bb3bCompose(acc, { facts: [] }, 0);
  const foot = st.clientSources.slice();
  const footer = ctx.bb2Footer(foot);
  return { ctx, st, painted: acc, reply, footer, foot };
}

test("stream path, card question, awkward chunks: move lead first, no peer block or In short, contradictions dropped", async () => {
  for (const chunk of [1, 3, 7, 11, 29]) {
    const { ctx, painted, reply, footer, foot } = await streamRun(chunk);
    assert.match(ctx.__system, /^CARD AND MOVE FACTS/, "the move facts lead the prompt");
    assert.match(ctx.__system, /Do not write a concluding or summary sentence\.(?! the server)/);
    assert.match(painted, /^Why MU reads Headwind \(card score 28\/100\), as of Fri 16 Oct, 21:00 UK:\nMU fell 5\.63%/);
    assert.match(painted, /chipmakers retreat"\n\nThe stock fell sharply on Friday as chip stocks sold off after a strong run\. Memory makers/, "chunk " + chunk + ": " + painted);
    assert.match(painted, /risk-off days\.\nInvestors will watch/);
    assert.doesNotMatch(painted, /headwind: its|tailwind for|In short|opportunit|\[\d+\]|Sources:/i);
    assert.match(reply, /^Why MU reads Headwind/);
    assert.doesNotMatch(reply, /Peer comparisons|In short|P\/E|opportunit/);
    assert.match(reply, /after a strong run \[1\]\./);
    const cited = [...new Set(reply.match(/\[(\d+)\]/g).map(x => +x.slice(1, -1)))].sort();
    assert.deepEqual(cited, [1, 2, 3, 4]);
    assert.deepEqual(foot.map(s => s.name), ["Yahoo Finance quote", "Yahoo Finance quote", "Yahoo Finance news", "Yahoo Finance news"]);
    assert.equal(foot[0].detail, "MU price");
    assert.match(footer, /^\n\nSources:\n\[1\] Yahoo Finance quote \| MU price\n\[2\] Yahoo Finance quote \| MU, SPY, SOXX last price and session change\n\[3\] Yahoo Finance news/);
  }
});

test("JSON path: move facts and the rule lead the system prompt; rt41s peer block left out for move, kept for valuation", async () => {
  const ctx = load();
  ctx.__news = [];
  ctx.__store = { chat: true, facts: [], clientSources: [], peerSource: null };
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  assert.equal(await ctx.rt41sPeerBlock("MU"), "");
  await ctx.generateAi({ system: "ORIGINAL {\"reply\":\"string\"}", messages: [] });
  assert.match(ctx.__genSystem, /^CARD AND MOVE FACTS[\s\S]*MU fell 5\.63% to \$878\.84[\s\S]*\[1\][\s\S]*Never describe a valuation figure[\s\S]*ORIGINAL/);
  const out = ctx.bb3bCompose(MODEL_CARD, { facts: [] }, 0);
  assert.match(out, /^Why MU reads Headwind/);
  assert.doesNotMatch(out, /headwind: its|tailwind for|In short/i);
  const v = load();
  v.__store = { chat: true, facts: [], clientSources: [], peerSource: null };
  await v.bb2Read0({ body: { messages: [{ role: "user", content: "How does Micron (MU) compare with its peers on valuation?" + NOTE }] } });
  assert.equal(await v.rt41sPeerBlock("MU"), "PEER VALUATIONS block for MU");
  assert.equal(v.__store.bb8eMoveP, undefined, "valuation questions fetch no move pack");
});

test("contradiction filter: valuation figures labelled headwind/tailwind are dropped whole; other head/tailwind lines stay", () => {
  const ctx = load();
  for (const s of [
    "A significant headwind is its trailing P/E 11.8x, which indicates a relatively low valuation.",
    "Micron (MU) faces a significant headwind: its trailing P/E (TTM) of 11.8x.",
    "A high forward P/E would be a tailwind for sentiment.",
    "Its cheap valuation is a tailwind.",
    "The 4.9x multiple is a headwind for the shares."
  ]) assert.equal(ctx.bb8eContra(s), true, s);
  for (const s of ["The Headwind label reflects Friday's 5.63% fall.", "Rising rates are a headwind for chip stocks.", "MU trades at a forward P/E of 4.9x."]) assert.equal(ctx.bb8eContra(s), false, s);
  assert.equal(ctx.bb8dDrop("A significant headwind is its trailing P/E 11.8x, which indicates a relatively low valuation.", { "11.8": 1 }, []), true);
});

test("valuation answers keep the peer block and In short; the peer cite moves off the header; uncited sources pruned and renumbered", () => {
  const ctx = load();
  const facts = [
    { a: "MU", b: "NVDA", basis: "forward", dir: "lower", va: 4.9, vb: 15.3, sentence: "MU forward P/E (next 12 months) 4.9x is lower than NVDA forward P/E (next 12 months) 15.3x by 10.4x (68.0%)." },
    { a: "MU", b: "NVDA", basis: "trailing", dir: "lower", va: 11.8, vb: 27.1, sentence: "MU trailing P/E (TTM) 11.8x is lower than NVDA trailing P/E (TTM) 27.1x by 15.3x (56.5%)." }
  ];
  const peer = { name: "Yahoo Finance", detail: "trailing P/E (TTM) and forward P/E" };
  const client = [{ name: "Yahoo Finance quote", detail: "MU price" }];
  ctx.__store = { chat: true, facts, clientSources: client, peerSource: peer, bb8eMode: "valuation" };
  const out = ctx.bb3bCompose("Memory pricing has improved this year, which has lifted margins.\nA significant headwind is its trailing P/E 11.8x, which indicates a relatively low valuation.", { facts, asOf: "2026-10-16 20:00 UTC" }, 2);
  assert.match(out, /^Peer comparisons as of Fri 16 Oct, 21:00 UK:\n/);
  assert.match(out, /by 15\.3x \(56\.5%\)\. \[1\]\n/);
  assert.match(out, /\nIn short: on next-12-month earnings MU is the cheapest of its peers at 4\.9x, against 15\.3x; on trailing earnings \(TTM\) MU is the cheapest of its peers at 11\.8x, against 27\.1x\. \[1\]$/);
  assert.doesNotMatch(out, /headwind/i);
  const foot = client.concat([peer]);
  assert.match(ctx.bb2Footer(foot), /^\n\nSources:\n\[1\] Yahoo Finance \| trailing P\/E/);
  assert.deepEqual(foot.map(s => s.name), ["Yahoo Finance"], "the done/JSON sources array matches the footer");
});

test("citation renumbering: list order kept, [a, b] form, unknown numbers removed, nothing cited leaves the list alone", () => {
  const ctx = load();
  const full = ["a", "b", "c", "d"].map(n => ({ name: n }));
  const r = ctx.bb8eCites("X [4]. Y [2, 4]. Z [9].", full);
  assert.equal(r.text, "X [2]. Y [1][2]. Z.");
  assert.deepEqual([...r.keep], [1, 3]);
  assert.equal(ctx.bb8eCites("No markers.", full).keep, null);
});

test("House note is plain English", () => {
  const ctx = load();
  assert.equal(ctx.bb7HouseView({}).note, "Each filing links to the official House disclosure (PDF).");
});

const UK = iso => Date.parse(iso);
function series(ctx, sym, delay, lastTsMs, startIso, mins, printsFromIso) {
  const rows = [];
  for (let m = 0; m <= mins; m += 5) {
    const t = UK(startIso) + m * 60000;
    const ts = printsFromIso && t >= UK(printsFromIso) ? Math.floor((t - delay * 60000) / 1000) : Math.floor(lastTsMs / 1000);
    const r = ctx.bb5gApply({ p: 100, c: 0.1, delayMin: delay, ts }, sym, t, 60000);
    rows.push([m, r.status, r.stale, r.phase || "", r.note || ""]);
  }
  return rows;
}
test("opening window: LSE 08:00-08:40 UK, 15-min delay, no print yet -> opening until 08:35, then stale (before: stale from 08:00)", () => {
  const ctx = load();
  const rows = series(ctx, "HSBA.L", 15, UK("2026-10-16T15:30:00Z"), "2026-10-19T07:00:00Z", 40, null);
  for (const [m, status, stale, phase, note] of rows) {
    if (m < 35) assert.deepEqual([status, stale, phase, note], ["delayed", false, "opening", "opening · first prices due 08:15 UK"], "08:" + m);
    else assert.deepEqual([status, stale, phase], ["stale", true, ""], "08:" + m);
  }
  const r = ctx.bb5gApply({ p: 1, delayMin: 15, ts: UK("2026-10-16T15:30:00Z") / 1000 }, "HSBA.L", UK("2026-10-19T07:10:00Z"), 60000);
  assert.equal(r.firstPriceAt, "2026-10-19T07:15:00.000Z");
});
test("opening window: delayed prints from 08:15 UK end the opening phase at once; Xetra 09:00 CET = 08:00 UK", () => {
  const ctx = load();
  const rows = series(ctx, "AZN.L", 15, UK("2026-10-16T15:30:00Z"), "2026-10-19T07:00:00Z", 40, "2026-10-19T07:15:00Z");
  assert.deepEqual(rows.map(r => r[1] + "/" + r[3]), ["delayed/opening", "delayed/opening", "delayed/opening", "delayed/", "delayed/", "delayed/", "delayed/", "delayed/", "delayed/"]);
  const x = series(ctx, "SAP.DE", 15, UK("2026-10-16T15:30:00Z"), "2026-10-19T07:00:00Z", 40, null);
  assert.deepEqual(x.map(r => r[3] || r[1]), ["opening", "opening", "opening", "opening", "opening", "opening", "opening", "stale", "stale"]);
  const lag = ctx.bb5eApply({ p: 1, delayMin: 15, ts: (UK("2026-10-19T07:20:00Z") - 15 * 60000) / 1000 }, "AZN.L", null, UK("2026-10-19T07:20:00Z"));
  assert.equal(lag.lagMs, 0, "lag is measured against the delayed clock");
});
test("opening window: GMT date, US open (delay 0 and 15), Tokyo after lunch, holiday stays closed, crypto untouched", () => {
  const ctx = load();
  const gmt = ctx.bb5gApply({ p: 1, delayMin: 15, ts: UK("2026-10-30T16:30:00Z") / 1000 }, "SHEL.L", UK("2026-11-02T08:05:00Z"), 60000);
  assert.equal(gmt.note, "opening · first prices due 08:15 UK");
  const spy = series(ctx, "SPY", 0, UK("2026-10-16T20:00:00Z"), "2026-10-19T13:30:00Z", 25, null);
  assert.deepEqual(spy.map(r => r[3] || r[1]), ["opening", "opening", "opening", "opening", "stale", "stale"]);
  assert.equal(ctx.bb5gApply({ p: 1, delayMin: 15, ts: UK("2026-10-16T20:00:00Z") / 1000 }, "MU", UK("2026-10-19T13:40:00Z"), 60000).note, "opening · first prices due 14:45 UK");
  const tok = ctx.bb5gApply({ p: 1, delayMin: 20, ts: UK("2026-10-19T02:30:00Z") / 1000 }, "7203.T", UK("2026-10-19T03:35:00Z"), 60000);
  assert.equal(tok.note, "opening · first prices due 04:50 UK", "the 12:30 JST reopen after lunch counts as an open");
  ctx.__holiday = (spec, d) => spec.tz === "America/New_York";
  assert.equal(ctx.bb5gApply({ p: 1, delayMin: 15, ts: 1 }, "MU", UK("2026-11-26T14:40:00Z"), 60000).status, "closed");
  ctx.__holiday = null;
  const btc = ctx.bb5gApply({ p: 1, delayMin: 0, ts: Math.floor(UK("2026-10-19T07:00:00Z") / 1000) }, "BTC-USD", UK("2026-10-19T07:01:00Z"), 60000);
  assert.equal(btc.phase, undefined);
});
test("/api/brief carries generatedAt and generatedAtUk stamped at generation", () => {
  const ctx = load();
  const before = Date.now();
  const b = ctx.rt33sBriefDate({ headline: "x" });
  assert.ok(Date.parse(b.generatedAt) >= before - 1000);
  assert.match(b.generatedAtUk, /^[A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2}, \d{2}:\d{2} UK$/);
  const res = {};
  ctx.json(res, 200, { brief: b, cached: false });
  assert.equal(res.body.generatedAt, b.generatedAt);
  assert.equal(res.body.generatedAtUk, b.generatedAtUk);
  const keep = ctx.rt33sBriefDate({ generatedAt: "2026-10-19T06:05:00.000Z" });
  assert.equal(keep.generatedAt, "2026-10-19T06:05:00.000Z", "an existing stamp is kept");
});
