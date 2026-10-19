// Offline tests for deploy/patch_bb8g.py (stacked on bb8d/bb8e). Loads the bb8d, bb8e and bb8g blocks with stubs; no network.
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
const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8g.py"), "utf8");
assert.match(PATCH, /b9f30e995bc43d97738b839abf9cf3e3/);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env", "require("]) assert.equal(B8G.includes(bad), false, bad);
for (const m of B8G.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8g/, m[1]);

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
  return ctx;
}
const NOTE = "\n\n[Answer this question as asked, about MU. Quote valuation only from the live figures supplied, including the PEER VALUATIONS block when comparing.]";
const CARD_Q = "What matters most about MU — Headwind?" + NOTE;
const NEWS = [
  { title: "INTC, AMD, MU, SNDK: US Chip Stocks Rebound After Worst Week Since March", link: "https://stocktwits.com/news-articles/a", ts: FRI + 9 * 3600e3, source: "Yahoo Finance" },
  { title: "Micron shares slide as chipmakers retreat", link: "https://finance.yahoo.com/news/b", ts: FRI - 2 * 3600e3, source: "Yahoo Finance" }
];
const MODEL_CARD = [
  "MU's beta of 2.23 means it tends to amplify market moves, which matters on a Risk-Off day.",
  "The stock fell sharply on Friday as chip stocks sold off after a strong run [8]. Investors are favoring defensive assets over cyclicals right now.",
  "The broader semiconductor group also dropped 4.14%, so the move was partly sector-wide.",
  "Many traders expect further volatility as funds rotate out of high-momentum names.",
  "In short, MU looks weak.",
  "Sources: [8] Yahoo Finance quote"
].join("\n");
const CLIENT = ["Reuters", "Bloomberg", "Reuters", "BBC", "CoinDesk", "Reuters"].map((n, i) => ({ name: n, link: "https://www." + n.toLowerCase() + ".com/" + i, detail: "general headline " + i })).concat([{ name: "Yahoo Finance quote", detail: "MU price" }]);
const BAD = /Investors are favoring|Many traders|MU looks weak/;

async function streamRun(chunk) {
  const ctx = load();
  ctx.__news = NEWS;
  const st = { chat: true, facts: [], clientSources: CLIENT.map(s => Object.assign({}, s)), peerSource: null };
  ctx.__store = st;
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  ctx.__model = MODEL_CARD; ctx.__chunk = chunk;
  let acc = "";
  await ctx.bb2Complete("BASE SYSTEM\n\nDo not write a concluding or summary sentence; the server adds it.", [], d => { const j = ctx.bb5gJoinStream(acc, d.replace(/^\n+|\n+$/g, ""), !acc); acc = j.acc; });
  const reply = ctx.bb3bCompose(acc, { facts: [] }, 0);
  const foot = st.clientSources.slice();
  const footer = ctx.bb2Footer(foot);
  return { ctx, st, painted: acc, reply, footer, foot };
}
const cites = (s) => [...new Set((s.split("\n\nSources:")[0].match(/\[(\d+)\]/g) || []).map(x => +x.slice(1, -1)))].sort((a, b) => a - b);

test("(a) labels: publisher field first, then the link's host; never a Yahoo label on a non-Yahoo link", () => {
  const ctx = load();
  const L = (s) => ctx.bb8gLabel(s);
  assert.equal(L({ name: "Yahoo Finance news", link: "https://stocktwits.com/x" }), "Stocktwits");
  assert.equal(L({ name: "Yahoo Finance", link: "https://www.reuters.com/x" }), "Reuters");
  assert.equal(L({ name: "News", link: "https://uk.finance.yahoo.com/x" }), "Yahoo Finance");
  assert.equal(L({ name: "Yahoo Finance news", link: "https://news.unknown-site.io/a" }), "news.unknown-site.io");
  assert.equal(L({ name: "Yahoo Finance quote", link: "https://finance.yahoo.com/quote/MU/" }), "Yahoo Finance quote");
  assert.equal(L({ name: "Yahoo Finance news", link: "https://stocktwits.com/x", publisher: "Benzinga" }), "Benzinga");
  assert.equal(L({ name: "Reuters", link: "https://www.reuters.com/x" }), "Reuters");
  assert.equal(L({ name: "Yahoo Finance quote", link: "" }), "Yahoo Finance quote");
  assert.equal(ctx.bb8gHostLabel("https://www.ft.com/content/1"), "Financial Times");
  assert.equal(ctx.bb8gHostLabel("https://notreuters.com/a"), "notreuters.com");
  // /api/ticker-news items
  const res = {};
  ctx.json(res, 200, { symbol: "MU", items: [{ title: "a", link: "https://stocktwits.com/a", source: "Yahoo Finance" }, { title: "b", link: "https://finance.yahoo.com/b", source: "Yahoo Finance" }] });
  assert.deepEqual(res.body.items.map(i => i.source), ["Stocktwits", "Yahoo Finance"]);
  assert.equal(res.body.items[0].via, "Yahoo Finance RSS");
});

test("(b) card stream at chunks 1, 3, 7, 13, 29: beta fact line cited, uncited speculation dropped, server In short last, cites consistent", async () => {
  for (const chunk of [1, 3, 7, 13, 29]) {
    const { ctx, painted, reply, footer, foot } = await streamRun(chunk);
    assert.match(ctx.__system, /Cite every claim with the \[n\]/);
    assert.match(reply, /\nCard score \(Dispatch regime fit\): [^\n]*\[\d+\]\nBeta \(Dispatch desk reference\): 2\.23, so MU tends to move about 2\.23 times as much as the market\. \[\d+\]\n/);
    assert.doesNotMatch(painted, BAD, "chunk " + chunk);
    assert.doesNotMatch(reply, BAD);
    assert.match(reply, /MU's beta of 2\.23 means/);
    assert.match(reply, /dropped 4\.14%, so the move was partly sector-wide\./);
    assert.match(painted, /\n\nIn short: MU fell 5\.63%, 4\.52 pts behind SPY, in a Risk-Off session; no confirmed cause\.$/m);
    const last = reply.trim().split("\n").pop();
    assert.match(last, /^In short: MU fell 5\.63%, 4\.52 pts behind SPY, in a Risk-Off session; no confirmed cause\. \[\d+\]$/);
    assert.equal((reply.match(/In short/g) || []).length, 1);
    const c = cites(reply);
    assert.deepEqual(c, foot.map((_, i) => i + 1), "chunk " + chunk);
    const names = foot.map(s => s.name);
    assert.ok(names.includes("Stocktwits") && names.includes("The Dispatch") && !names.includes("Yahoo Finance news"), names.join(","));
    assert.match(footer, /\] Stocktwits \|/);
    const quoteN = foot.findIndex(x => /last price and session change/.test(x.detail)) + 1;
    assert.ok(quoteN > 0);
    assert.ok(last.endsWith("[" + quoteN + "]"), "In short cites the quote source");
  }
});

test("(b) JSON path: same lead, filter and In short; rule in the prompt", async () => {
  const ctx = load();
  ctx.__news = NEWS;
  ctx.__store = { chat: true, facts: [], clientSources: [], peerSource: null };
  await ctx.bb2Read0({ body: { messages: [{ role: "user", content: CARD_Q }], tickers: ["MU"] } });
  await ctx.generateAi({ system: "ORIGINAL", messages: [] });
  assert.match(ctx.__genSystem, /^CARD AND MOVE FACTS[\s\S]*Beta \(Dispatch desk reference\): 2\.23[\s\S]*Cite every claim/);
  const out = ctx.bb3bCompose(MODEL_CARD, { facts: [] }, 0);
  assert.doesNotMatch(out, BAD);
  assert.match(out, /\n\nIn short: MU fell 5\.63%, 4\.52 pts behind SPY, in a Risk-Off session; no confirmed cause\. \[1\]$/);
  const keep = ctx.__store.bb8eCites.keep.length;
  assert.deepEqual(cites(out), Array.from({ length: keep }, (_, i) => i + 1));
});

test("(b) In short: rises, ahead/in line/behind, missing benchmark, open session, no mood; neutral wording", () => {
  const ctx = load();
  const P = (c, bc, extra) => Object.assign({ base: "MU", q: { c, status: "closed" }, bench: bc == null ? null : { sym: "SPY", q: { c: bc } }, fit: { regime: "Risk-Off" } }, extra || {});
  assert.equal(ctx.bb8gShort(P(-5.6269, -1.1065)), "In short: MU fell 5.63%, 4.52 pts behind SPY, in a Risk-Off session; no confirmed cause.");
  assert.equal(ctx.bb8gShort(P(2.5, 0.5, { fit: { regime: "Risk-On" } })), "In short: MU rose 2.50%, 2.00 pts ahead of SPY, in a Risk-On session; no confirmed cause.");
  assert.equal(ctx.bb8gShort(P(1.2, 1.2)), "In short: MU rose 1.20%, in line with SPY, in a Risk-Off session; no confirmed cause.");
  assert.equal(ctx.bb8gShort(P(-1, null, { fit: null })), "In short: MU fell 1.00%, with no market comparison available; no confirmed cause.");
  assert.equal(ctx.bb8gShort(P(0, 0.3)), "In short: MU was unchanged, 0.30 pts behind SPY, in a Risk-Off session; no confirmed cause.");
  assert.match(ctx.bb8gShort(Object.assign(P(-0.8, -0.2), { q: { c: -0.8, status: "open" } })), /^In short: MU is down 0\.80%, 0\.60 pts behind SPY/);
  assert.equal(ctx.bb8gShort(Object.assign(P(-1, -0.5), { base: "HSBA.L", bench: { sym: "^FTSE", q: { c: -0.5 } } })), "In short: HSBA.L fell 1.00%, 0.50 pts behind the FTSE 100, in a Risk-Off session; no confirmed cause.");
  for (const s of [ctx.bb8gShort(P(3, 1)), ctx.bb8gShort(P(-3, 1))]) assert.doesNotMatch(s, /\b(buy|sell|target|undervalued|opportunit|upside|downside)\b/i);
});

test("(c) valuation: sentences restating peer lines are dropped; interpretation stays", () => {
  const ctx = load();
  const facts = [
    { a: "MU", b: "NVDA", sentence: "MU forward P/E (next 12 months) 4.9x is lower than NVDA forward P/E (next 12 months) 15.3x by 10.4x (68.0%)." },
    { a: "MU", b: "WDC", sentence: "MU forward P/E (next 12 months) 4.9x is lower than WDC forward P/E (next 12 months) 13.6x by 8.7x (64.0%)." },
    { a: "MU", b: "AMD", sentence: "MU trailing P/E (TTM) 11.8x is lower than AMD trailing P/E (TTM) 134.9x by 123.1x (91.3%)." },
    { a: "MU", b: "INTC", sentence: "INTC trailing P/E (TTM) was not reported, so MU and INTC are not compared on trailing P/E (TTM)." }
  ];
  const R = (s) => ctx.bb8gRestates(s, facts);
  assert.equal(R("MU's forward P/E of 4.9x is well below NVDA's 15.3x."), true);
  assert.equal(R("It is also significantly lower than WDC's 13.6x on a forward basis."), true);
  assert.equal(R("MU's trailing P/E is lower than AMD's by a wide margin."), true);
  assert.equal(R("INTC's trailing P/E (TTM) is not reported, so that comparison is missing."), true);
  assert.equal(R("Micron (MU) has the lowest forward P/E in the group, which reflects expectations for strong memory pricing [1]."), false);
  assert.equal(R("The market appears to price in a sharp earnings cycle for memory makers."), false);
  const ok = ctx.bb8cAllowed(facts);
  const body = ctx.bb8dBody([
    "Micron (MU) has the lowest forward P/E in the group, which reflects expectations for strong memory pricing [1].",
    "MU's forward P/E of 4.9x is well below NVDA's 15.3x. It is also significantly lower than WDC's 13.6x on a forward basis.",
    "The market appears to price in a sharp earnings cycle for memory makers, which tends to compress multiples near peak profits."
  ].join("\n"), facts);
  assert.equal(body, "Micron (MU) has the lowest forward P/E in the group, which reflects expectations for strong memory pricing [1].\nThe market appears to price in a sharp earnings cycle for memory makers, which tends to compress multiples near peak profits.");
  assert.ok(ok);
  assert.match(ctx.bb2System({}, { facts }, []), /Do not restate the peer comparison lines/);
});
