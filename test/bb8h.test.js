// Offline tests for deploy/patch_bb8h.py (stacked on bb8d/bb8e/bb8g). Loads the bb8d, bb8e, bb8g and bb8h blocks with stubs; no network.
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
const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8h.py"), "utf8");
assert.match(PATCH, /7d10de541da933783afa032a90a4e57c/);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env", "require("]) assert.equal(B8H.includes(bad), false, bad);
for (const m of B8H.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8h/, m[1]);

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

async function streamRun(chunk, yahoo, model) {
  const ctx = load();
  ctx.__news = NEWS;
  ctx.__yahoo = yahoo === undefined ? YQ({ raw: 2.226, fmt: "2.23" }, { raw: 2.226, fmt: "2.23" }) : yahoo;
  const st = { chat: true, facts: [], clientSources: CLIENT.map(s => Object.assign({}, s)), peerSource: null };
  ctx.__store = st;
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
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

test("1) beta: Yahoo's published beta replaces the card line, cited Yahoo Finance key-statistics; no desk wording anywhere", async () => {
  const { ctx, reply, foot } = await streamRun(7);
  assert.match(reply, /\nMU's published beta is 2\.23 \(Yahoo Finance, 5-year monthly\), so it has tended to move about 2\.23 times as much as the market\. \[\d+\]\n/);
  assert.doesNotMatch(reply, /Dispatch desk reference|desk beta/);
  assert.doesNotMatch(ctx.__system, /Dispatch desk reference|desk beta/);
  assert.match(ctx.__system, /Only the Yahoo Finance line may be called beta/);
  const y = foot.find(s => /key-statistics/.test(s.link));
  assert.equal(y.name, "Yahoo Finance");
  assert.equal(y.link, "https://finance.yahoo.com/quote/MU/key-statistics/");
  assert.ok(Date.parse(y.asOf) > 0);
  const d = foot.find(s => s.name === "The Dispatch");
  assert.equal(d.detail, "Pulse card score (regime fit)");
  const n = numOf(foot, /key-statistics/);
  assert.match(reply, new RegExp("published beta is 2\\.23[^\\n]*\\[" + n + "\\]"));
});

test("1) beta: defaultKeyStatistics when summaryDetail has none; no Yahoo beta means no beta line and beta sentences dropped", async () => {
  const a = await streamRun(7, YQ({}, { raw: 1.9, fmt: "1.90" }), "MU's beta of 1.90 is high [1].\nSources:");
  assert.match(a.reply, /published beta is 1\.90 \(Yahoo Finance/);
  assert.doesNotMatch(a.reply, /MU's beta of 1\.90 is high/, "restates the bullet beta, so item 3 drops it");
  const b = await streamRun(7, YQ({}, {}), "MU's beta of 2.23 means it tends to amplify market moves [9].\nMU lagged its sector by 1.48 percentage points [2].\nSources:");
  assert.doesNotMatch(b.reply, /beta/i);
  assert.ok(!b.foot.some(s => /key-statistics/.test(s.link || "")));
  assert.doesNotMatch(b.reply, /MU lagged its sector by 1\.48 percentage points \[/, "restates a bullet figure");
  const c = await streamRun(7, undefined, "MU's beta of 1.62 makes it volatile [8].\nThe card's 1.62 beta reading is high.\nSources:");
  assert.doesNotMatch(c.reply, /1\.62/, "a number other than Yahoo's is never called beta");
});

const MODEL_PROSE = [
  "MU fell 5.63% to $878.84 in its last session, a sharper drop than SPY's 1.11% decline, leaving it 4.52 percentage points behind the market [8]. It also trailed SOXX, which fell 4.14%, by 1.48 percentage points [8]. With a beta of 2.23, MU tends to amplify market moves, and its card score of 28/100 reflects increased investor caution towards MU [11]. This reflects increased investor caution towards MU.",
  "Chip stocks including MU rebounded on Monday after their worst week since March [2].",
  "Chip stocks have fallen 12% this month [8]."
].join("\n");
test("2+3) stream at chunks 1, 3, 7, 13 plus JSON: mis-cites re-pointed or dropped, bullet restatements and uncited claims dropped, Sources renumbered", async () => {
  for (const chunk of [1, 3, 7, 13]) {
    for (const model of [MODEL_CARD, MODEL_PROSE]) {
      const { reply, foot, painted } = await streamRun(chunk, undefined, model);
      const parts = reply.split("\n\n");
      assert.match(parts[parts.length - 1], /^In short: /);
      const prose = parts.slice(1, -1).join("\n\n");
      for (const re of [/5\.63%|1\.11%|4\.52|4\.14%|1\.48|2\.23 means|beta of 2\.23|28\/100/, /investor caution/, /12% this month/, /Memory makers/]) assert.doesNotMatch(prose, re, "chunk " + chunk + "\n" + reply);
      if (model === MODEL_PROSE) {
        const st = numOf(foot, /stocktwits|Rebound/i);
        assert.equal(prose, "Chip stocks including MU rebounded on Monday after their worst week since March [" + st + "].", "cite re-pointed to the matching headline");
      } else assert.equal(parts.length, 2, "nothing left: bullets plus In short\n" + reply);
      assert.doesNotMatch(painted, /investor caution|12% this month/);
      assert.deepEqual(cites(reply), foot.map((_, i) => i + 1));
      assert.ok(!foot.some(s => s.name === "Reuters"), "client headlines no longer cited");
    }
  }
  const ctx = load();
  ctx.__news = NEWS; ctx.__yahoo = YQ({ raw: 2.226 }, null);
  ctx.__store = { chat: true, facts: [], clientSources: [], peerSource: null };
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  await ctx.generateAi({ system: "ORIGINAL", messages: [] });
  assert.match(ctx.__genSystem, /MU's published beta is 2\.23 \(Yahoo Finance/);
  assert.match(ctx.__genSystem, /Do not restate any figure from the lines above/);
  const out = ctx.bb3bCompose(MODEL_PROSE.replace(/\[8\]/g, "[1]").replace(/\[11\]/g, "[4]").replace("[2].\n", "[2].\n"), { facts: [] }, 0);
  const keep = ctx.__store.bb8eCites.keep.map(i => ctx.__store.bb8eCites.full[i]);
  const st = keep.findIndex(s => /stocktwits|Rebound/i.test((s.link || "") + (s.detail || ""))) + 1;
  assert.ok(st > 0);
  assert.match(out, new RegExp("\\n\\nChip stocks including MU rebounded on Monday after their worst week since March \\[" + st + "\\]\\.\\n\\nIn short: "));
  assert.doesNotMatch(out, /investor caution|12% this month|beta of 2\.23/);
  assert.deepEqual(cites(out), keep.map((_, i) => i + 1));
});

test("2) sentence rules: figure match keeps, wrong source re-points, no match strips, unknown figure drops, ticker needed without a figure", () => {
  const ctx = load();
  const idx = { n: 4, known: { MU: 1, SPY: 1, NVDA: 1 }, yBeta: 2.23, yN: 4,
    text: { 1: "\nReuters general headline", 2: "\nMU fell 5.63% to $878.84 [2]\nSPY fell 1.11% [2]", 3: "\nNVDA forward P/E 15.3x", 4: "\nMU's published beta is 2.23 [4]" },
    fact: { 2: "\nMU fell 5.63% to $878.84 [2]\nSPY fell 1.11% [2]", 3: "\nNVDA forward P/E 15.3x", 4: "\nMU's published beta is 2.23 [4]" }, factFigs: {} };
  ["5.63", "878.84", "1.11", "15.30", "2.23"].forEach(k => { idx.factFigs[k] = 1; });
  const F = s => ctx.bb8hFixSentence(s, idx);
  assert.equal(F("MU dropped 5.63% on Friday [2]."), "MU dropped 5.63% on Friday [2].");
  assert.equal(F("MU dropped 5.63% on Friday [1]."), "MU dropped 5.63% on Friday [2].");
  assert.equal(F("MU dropped 5.63% on Friday [9]."), "MU dropped 5.63% on Friday [2].", "out-of-range cites are re-pointed too");
  assert.equal(F("Chips fell 12% this month [2]."), "");
  assert.equal(F("NVDA keeps its lead in accelerators [1]."), "NVDA keeps its lead in accelerators [3].");
  assert.equal(F("Memory makers are sensitive to AI spending [2]."), "Memory makers are sensitive to AI spending.");
  assert.equal(F("A beta of 2.23 is high [1]."), "A beta of 2.23 is high [4].");
  assert.equal(F("A beta of 1.62 is high [4]."), "");
  assert.equal(F("MU is volatile [2]."), "MU is volatile [2].");
  assert.equal(ctx.bb8hFigs("fell 5.63% to $878.84, 2.5x, 28/100, beta of 2.23, 12 pts, in 2026")["2026.00"], undefined);
  assert.deepEqual(Object.keys(ctx.bb8hFigs("fell 5.63% to $878.84, 2.5x, 28/100, beta of 2.23, 12 pts")).sort(), ["12.00", "2.23", "2.50", "28.00", "5.63", "878.84"].sort());
});

test("2) valuation answers: ticker sentence re-pointed to the peer source, unsourced figure and non-Yahoo beta dropped", () => {
  const ctx = load();
  const facts = [
    { a: "MU", b: "NVDA", sentence: "MU forward P/E (next 12 months) 4.9x is lower than NVDA forward P/E (next 12 months) 15.3x by 10.4x (68.0%)." }
  ];
  const peer = { name: "Yahoo Finance", detail: "trailing P/E (TTM) and forward P/E" };
  ctx.__store = { chat: true, facts, clientSources: [{ name: "Yahoo Finance quote", detail: "MU price" }], peerSource: peer, bb8eMode: "valuation" };
  const body = ctx.bb8dBody([
    "Micron (MU) has the lowest forward P/E in the group, which reflects expectations for strong memory pricing [1].",
    "Memory prices rose 20% last quarter, which supports that view [2].",
    "Analysts see NVDA's dominance in AI accelerators continuing [1].",
    "MU's beta of 1.62 makes it one of the more volatile names in the group [2].",
    "The market appears to price in a sharp earnings cycle for memory makers [1]."
  ].join("\n"), facts);
  assert.equal(body, [
    "Micron (MU) has the lowest forward P/E in the group, which reflects expectations for strong memory pricing [1].",
    "Analysts see NVDA's dominance in AI accelerators continuing [2].",
    "The market appears to price in a sharp earnings cycle for memory makers."
  ].join("\n"));
});
