// Offline tests for deploy/patch_bb8j.py: the JSON /api/chat path gets the stream path's sources and both call one
// final assembler. Loads the bb8d, bb8e, bb8g, bb8h, bb8i and bb8j blocks with stubs; no network, no live files.
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
const B8J = blockOf("patch_bb8j.py", "// \u2500\u2500 bb8j \u2500\u2500", "// BB8J_JS_END");
const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8j.py"), "utf8");

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
function bb2Footer(sources) { if (!sources || !sources.length) return "\\n\\nSources: No news or price sources were supplied for this answer."; return "\\n\\nSources:\\n" + sources.map(function (s, i) { return "[" + (i + 1) + "] " + s.name + " | " + (s.detail || ""); }).join("\\n"); }
function bb3bRawSources(body) { return (body && body.sources) || []; }
function bb3bFilterSources(sources, body) { return sources.filter(function (s) { return s && s.name; }).map(function (s) { return { name: s.name, link: s.link || "", asOf: s.asOf || "", detail: s.detail || "" }; }); }
function bb2Finish(reply, store) { return "pre-bb8j finish"; }
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
function load(withJ) {
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
  if (withJ !== false) vm.runInContext(B8J, ctx, { filename: "bb8j.js" });
  return ctx;
}

assert.match(PATCH, /eb6937c7284919ed1a86f7e9d8b87d9c/);
const GEN_Q = "What's moving markets this morning?";
const HEAD = ["China GDP growth beats forecasts in third quarter", "Shipping through Hormuz slows as tensions rise", "Pharma stocks lead European open", "UK house prices edge higher in October", "Bitcoin steadies after weekend swings", "SK Hynix shares climb in Seoul"];
const SRC = ["Reuters", "Bloomberg", "Reuters", "BBC", "CoinDesk", "Reuters"].map((n, i) => ({ name: n, link: "https://example.org/" + i, asOf: "Mon 19 Oct, 07:1" + i + " UK", detail: HEAD[i] }));
const MODEL_GEN = [
  "China's third-quarter GDP growth beat forecasts [1].",
  "Analysts expect the China GDP beat to support commodity demand [1].",
  "Investors expect oil prices to rise as Hormuz shipping slows [3].",
  "Traders expect the Bank of England to cut rates in November.",
  "Bitcoin is likely to stay range-bound this week [5].",
  "SK Hynix shares climbed in Seoul, and memory makers could see further gains [6].",
  "UK house prices edged higher in October [4]."
].join("\n");
const MODEL_FIG = [
  "China's economy grew 4.8% in the third quarter, ahead of forecasts [1].",
  "Brent crude rose 2.1% in early trade [4].",
  "Bitcoin traded near $67,000 after weekend swings [5].",
  "The Bank of England is likely to cut rates in November [2].",
  "UK house prices rose 0.3% in October [4]."
].join("\n");
const body = (sources) => ({ messages: [{ role: "user", content: GEN_Q }], tickers: [], sources: sources.map(s => Object.assign({}, s)) });
function check(reply) {
  const [text, foot] = reply.split("\n\nSources:");
  assert.ok(foot !== undefined, "blank line before Sources");
  const cited = [...new Set((text.match(/\[(\d+)\]/g) || []).map(x => +x.slice(1, -1)))].sort((a, b) => a - b);
  const listed = (foot.match(/^\[(\d+)\]/gm) || []).map(x => +x.slice(1, -1));
  assert.deepEqual(cited, listed, "cites match Sources");
  listed.forEach((n, i) => assert.equal(n, i + 1, "contiguous"));
  return { text, foot };
}
async function jsonRun(model, sources, withJ) {
  const ctx = load(withJ);
  ctx.__news = []; ctx.__yahoo = null;
  const st = { chat: true, facts: [], clientSources: [], peerSource: null };
  ctx.__store = st;
  const b = body(sources);
  await ctx.bb2Read0({ body: b });
  st.body = b; // bb2's readBody hook does this on the JSON path
  await ctx.generateAi({ system: "JSON SYSTEM", messages: [] });
  return { ctx, st, reply: ctx.bb2Finish(model, st) };
}
async function streamRun(model, sources, chunk) {
  const ctx = load();
  ctx.__news = []; ctx.__yahoo = null;
  const b = body(sources);
  const st = { chat: true, facts: [], clientSources: [], peerSource: null };
  ctx.__store = st;
  await ctx.bb2Read0({ body: b });
  st.clientSources = ctx.bb8jClient(ctx.bb8jSources(b)); // as bb3bStreamInner now does
  ctx.__model = model; ctx.__chunk = chunk;
  let painted = "";
  await ctx.bb2Complete(ctx.bb2System(), [], d => { painted += d; });
  const out = ctx.bb8jAssemble("glued text the pump produced", st);
  return { ctx, st, painted, out };
}

test("protocol: bb8j names, no forbidden code, both final paths call the shared assembler", () => {
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", ".tier", "process.env", "require("]) assert.equal(B8J.includes(bad), false, bad);
  for (const m of B8J.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8j/, m[1]);
  assert.match(PATCH, /var sources = bb8jSources\(body\);/);
  assert.match(PATCH, /var bb8jOut = bb8jAssemble\(acc, store\);/);
  assert.match(B8J, /bb2Finish = function \(reply, store\) \{ return bb8jAssemble\(reply, store\)\.reply; \};/);
});

test("JSON general answer: sources gathered as on the stream, prompt lists them, footer pruned and renumbered", async () => {
  const before = await jsonRun(MODEL_GEN, SRC, false);
  assert.equal(before.st.clientSources.length, 0, "pre-bb8j: JSON store never got the client sources");
  const { ctx, st, reply } = await jsonRun(MODEL_GEN, SRC);
  assert.equal(st.clientSources.length, 6);
  assert.match(ctx.__genSystem, /CITABLE SOURCES \(use these \[n\] markers only; do not invent sources\):\n\[1\] Reuters as of Mon 19 Oct, 07:10 UK https:\/\/example\.org\/0 - China GDP/);
  assert.match(ctx.__genSystem, /\[6\] Reuters .* SK Hynix shares climb in Seoul/);
  const { text, foot } = check(reply);
  assert.equal(text, [
    "China's third-quarter GDP growth beat forecasts [1].",
    "Analysts expect the China GDP beat to support commodity demand [1].",
    "Bitcoin is likely to stay range-bound this week [3].",
    "SK Hynix shares climbed in Seoul, and memory makers could see further gains [4].",
    "UK house prices edged higher in October [2]."
  ].join("\n"));
  assert.deepEqual(foot.trim().split("\n").map(l => l.split(" | ")[1]), [HEAD[0], HEAD[3], HEAD[4], HEAD[5]]);
  assert.deepEqual(st.bb8jSources.map(s => s.detail), [HEAD[0], HEAD[3], HEAD[4], HEAD[5]]);
});

test("stream at chunks 1, 3, 7, 13: final reply equals the JSON reply (one assembler)", async () => {
  for (const model of [MODEL_GEN, MODEL_FIG]) {
    const json = (await jsonRun(model, SRC)).reply;
    for (const chunk of [1, 3, 7, 13]) {
      const { out, painted } = await streamRun(model, SRC, chunk);
      assert.equal(out.reply, json, "chunk " + chunk);
      check(out.reply);
      assert.doesNotMatch(painted, /oil prices|Brent|Bank of England/, "dropped while streaming, chunk " + chunk);
    }
  }
});

test("general answers get bb8h citation matching: an unsupported figure goes, matching news cites stay", async () => {
  const { reply } = await jsonRun(MODEL_FIG, SRC);
  const { text } = check(reply);
  assert.equal(text, [
    "China's economy grew 4.8% in the third quarter, ahead of forecasts [1].",
    "Bitcoin traded near $67,000 after weekend swings [3].",
    "UK house prices rose 0.3% in October [2]."
  ].join("\n"));
});

test("no sources at all: [n] stripped as the last resort, footer says none were supplied", async () => {
  const { reply } = await jsonRun(MODEL_GEN, []);
  assert.doesNotMatch(reply, /\[\d+\]/);
  assert.match(reply, /\n\nSources: No news or price sources were supplied for this answer\.$/);
  assert.match(reply, /^China's third-quarter GDP growth beat forecasts\.\n/);
  for (const chunk of [3, 13]) assert.equal((await streamRun(MODEL_GEN, [], chunk)).out.reply, reply);
});
