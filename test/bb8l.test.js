// Offline tests for deploy/patch_bb8l.py: UK time (Europe/London, BST and GMT) in user-visible text and model prompts.
// Loads the bb8d UK formatter and the bb8l block with stubs; no network, no live files.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const D = read("patch_bb8d.py");
const FMT = D.slice(D.indexOf('var BB8D_TZ = "Europe/London";'), D.indexOf("// Bracket-aware sentence split"));
const PATCH = read("patch_bb8l.py");
const B8L = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8l \u2500\u2500"), PATCH.indexOf("// BB8L_JS_END") + 14);
assert.match(FMT, /function bb8dUkText/);

const STUBS = `
var calls = [];
function bb2BuildFacts(base, vals) { return { block: "AUTHORITATIVE PEER COMPARISONS as of 2026-10-16 20:00 UTC (Yahoo Finance).\\n- MU | as of 2026-10-16 20:00 UTC", asOf: "2026-10-16 20:00 UTC", facts: [] }; }
async function bb3bGenerateAi(options) { calls.push(options); return { text: "{}" }; }
async function bb2Complete(system, messages, onDelta) { calls.push({ system: system, messages: messages }); return {}; }
function bb8jFix(sent, st) { return sent; }
function bb8iGeneral(st) { return !!(st && st.general); }
function bb8iLine(line, resolve, st) { return line; }
function bb8jAssemble(reply, store) { return { reply: String(reply), sources: [{ name: "Reuters", asOf: "2026-10-19T06:10:00.000Z" }] }; }
function rt33sBriefDate(b) { b.date = "2026-10-19"; return b; }
function institutionalResponse(type, status, source, asOf, items, note) { return { type: type, status: status, source: source, asOf: asOf, items: items, note: note }; }
`;
function load() {
  const ctx = { console: { warn() {} }, Date, Intl, JSON, Math, Object, String, Number, Array, RegExp, Promise };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(FMT + STUBS, ctx);
  vm.runInContext(B8L, ctx, { filename: "bb8l.js" });
  return ctx;
}

test("protocol: bb8l names, no forbidden code, no Stripe/auth/webhook, stacked on bb8k", () => {
  assert.match(PATCH, /0510fe845e43ec1e865dbc4257b00418/);
  const code = B8L.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "currentUser", "hasPremiumAccess", "process.env", "require(", ".tier", "cookie"]) assert.equal(code.includes(bad), false, bad);
  for (const m of B8L.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8l/, m[1]);
  assert.match(PATCH, /bb8lGoldHm\(d\) \? bb8lGoldHm\(d\) : d\.toISOString\(\)\.slice\(11, 16\) \+ " UTC"/);
});

test("BST and GMT: full timestamps through the bb8d formatter, Europe/London", () => {
  const c = load();
  const cases = [
    ["2026-10-19T06:10:00Z", "Mon 19 Oct, 07:10 UK"],          // BST (UTC+1)
    ["2026-10-19T06:10:00.000Z", "Mon 19 Oct, 07:10 UK"],
    ["2026-11-16T06:10:00Z", "Mon 16 Nov, 06:10 UK"],          // GMT (UTC+0)
    ["2026-10-16 20:00 UTC", "Fri 16 Oct, 21:00 UK"],          // bb2AsOf form
    ["2026-01-05 09:30 GMT", "Mon 5 Jan, 09:30 UK"],
    ["2026-10-19T08:10:00+02:00", "Mon 19 Oct, 07:10 UK"],
    ["2026-10-25T00:30:00Z", "Sun 25 Oct, 01:30 UK"],          // last BST half hour (clocks go back at 01:00 UTC)
    ["2026-10-25T01:30:00Z", "Sun 25 Oct, 01:30 UK"],          // first GMT half hour, same wall time
    ["2027-03-28T00:30:00Z", "Sun 28 Mar, 00:30 UK"],          // GMT before clocks go forward at 01:00 UTC
    ["2027-03-28T01:30:00Z", "Sun 28 Mar, 02:30 UK"]           // BST
  ];
  for (const [i, o] of cases) assert.equal(c.bb8lUkText("as of " + i + "."), "as of " + o + ".", i);
});

test("BST and GMT: time-only UTC stamps convert on the request's UTC date", () => {
  const c = load();
  const bst = Date.parse("2026-10-19T09:00:00Z"), gmt = Date.parse("2026-12-01T09:00:00Z");
  assert.equal(c.bb8lUkText("Gold as of 08:49 UTC", bst), "Gold as of 09:49 UK");
  assert.equal(c.bb8lUkText("Gold as of 08:49 UTC", gmt), "Gold as of 08:49 UK");
  assert.equal(c.bb8lUkText("at 06:30 GMT and 23:30Z", bst), "at 07:30 UK and 00:30 UK");
  assert.equal(c.bb8lUkText("at 13:30:00 UTC", gmt), "at 13:30 UK");
});

test("text that is not a timestamp is left alone", () => {
  const c = load();
  for (const s of ["Q3 2026 results", "earnings on 18 Dec", "session 2026-10-19", "filed 2026-03-20", "US 10y 4.12%", "P/E 11.8x", "as of Mon 19 Oct, 07:10 UK", "07:15 UK", "the UTC calendar", "1:2 ratio", "SPX 6612.4 (-1.10%)"]) assert.equal(c.bb8lUkText(s), s, s);
});

test("prompts: generateAi and the stream's bb2Complete get UK text; callers' objects are not mutated", async () => {
  const c = load();
  const msgs = [{ role: "user", content: "Context: news at 2026-10-19T06:14:00Z" }];
  const opts = { system: "Tape as of 2026-10-19 07:15 UTC", messages: msgs, maxTokens: 10 };
  await c.bb3bGenerateAi(opts);
  assert.equal(c.calls[0].system, "Tape as of Mon 19 Oct, 08:15 UK");
  assert.equal(c.calls[0].messages[0].content, "Context: news at Mon 19 Oct, 07:14 UK");
  assert.equal(c.calls[0].maxTokens, 10);
  assert.equal(opts.system, "Tape as of 2026-10-19 07:15 UTC");
  assert.equal(msgs[0].content, "Context: news at 2026-10-19T06:14:00Z");
  await c.bb2Complete("FACT as of 2026-11-16T06:10:00Z", msgs, () => {});
  assert.equal(c.calls[1].system, "FACT as of Mon 16 Nov, 06:10 UK");
});

test("item 1: the peer block (JSON valuation prompt) is UK; built.asOf stays the machine value", () => {
  const c = load();
  const built = c.bb2BuildFacts("MU", {});
  assert.equal(built.block, "AUTHORITATIVE PEER COMPARISONS as of Fri 16 Oct, 21:00 UK (Yahoo Finance).\n- MU | as of Fri 16 Oct, 21:00 UK");
  assert.equal(built.asOf, "2026-10-16 20:00 UTC");
});

test("replies, brief text and notes are UK; machine fields stay ISO", () => {
  const c = load();
  const r = c.bb8jAssemble("Gold traded near 4012 as of 2026-10-19T06:30:00Z.", {});
  assert.equal(r.reply, "Gold traded near 4012 as of Mon 19 Oct, 07:30 UK.");
  assert.equal(r.sources[0].asOf, "2026-10-19T06:10:00.000Z");
  assert.equal(c.bb8jFix("Yield 4.12% at 2026-10-19 06:30 UTC [1].", {}), "Yield 4.12% at Mon 19 Oct, 07:30 UK [1].");
  assert.equal(c.bb8iLine("as of 2026-10-19T06:30:00Z", null, { general: true }), "as of Mon 19 Oct, 07:30 UK");
  assert.equal(c.bb8iLine("as of 2026-10-19T06:30:00Z", null, { general: false }), "as of 2026-10-19T06:30:00Z", "card/valuation lines are bb8d's");
  const b = c.rt33sBriefDate({ headline: "Lift as of 2026-10-19T06:10:00Z", risks: ["CPI at 2026-11-12 13:30 UTC"], generatedAt: "2026-10-19T08:59:48.959Z", focusTickers: ["SPY"] });
  assert.equal(b.headline, "Lift as of Mon 19 Oct, 07:10 UK");
  assert.deepEqual(Array.from(b.risks), ["CPI at Thu 12 Nov, 13:30 UK"]);
  assert.equal(b.generatedAt, "2026-10-19T08:59:48.959Z");
  assert.equal(b.date, "2026-10-19");
  const ir = c.institutionalResponse("congress", "partial", "Kadoa", "2026-10-12T14:00:00.000Z", [], "Showing the last verified snapshot from 2026-10-12T14:00:00.000Z.");
  assert.equal(ir.note, "Showing the last verified snapshot from Mon 12 Oct, 15:00 UK.");
  assert.equal(ir.asOf, "2026-10-12T14:00:00.000Z");
  assert.equal(c.bb8lGoldHm(new Date(Date.parse("2026-10-19T08:49:00Z"))), "Mon 19 Oct, 09:49 UK");
  assert.equal(c.bb8lGoldHm(new Date(Date.parse("2026-12-01T08:49:00Z"))), "Tue 1 Dec, 08:49 UK");
});

// ── chat73 items (next-earnings line; insiders span and UK dates) ──
const B8 = read("patch_bb8.py"), B8I = read("patch_bb8i.py");
const WIN = B8.slice(B8.indexOf("function bb8Day(s)"), B8.indexOf("function bb8Window(pack, premium)"));
const SPEC = B8I.slice(B8I.indexOf("var BB8I_SPEC = ["), B8I.indexOf("var BB8I_STOP"));
assert.match(WIN, /function bb8WindowLabel/); assert.match(SPEC, /BB8I_SPEC/);
const STUBS2 = `
var store = { chat: true };
var yahooCalls = 0, yahooNext = { date: "2026-12-23", est: true };
var RT32 = { cache: new Map() };
function bb8dStore() { return store; }
async function generateAi(options) { return bb3bGenerateAi(options); }
function bb8Late(ms) { return new Promise(function () {}); }
function bb8bYahooSym(s) { return s; }
async function rt32Yahoo(sym) { yahooCalls++; await null; return { calendarEvents: { earnings: { earningsDate: yahooNext.date ? [{ fmt: yahooNext.date }] : [], isEarningsDateEstimate: yahooNext.est } } }; }
function bb2Question(b) { return b.q; }
function bb8eStrip(q) { return String(q || "").replace(/\\s*\\[Answer[^\\]]*\\]\\s*$/, ""); }
function bb8eBaseOf(q, b) { return "MU"; }
async function bb2Read0(req) { return req; }
async function bb8eMovePack(base) { return { base: base, ysym: base }; }
function bb8eLead(pack, card, n0) {
  var text = "Why MU reads Headwind:\\nMU fell 5.63% to $878.84. [" + (n0 + 1) + "]\\nIn the news, not confirmed as the cause: \\"Chip stocks rebound\\" [" + (n0 + 2) + "]";
  return { text: text, paint: text, prompt: "CARD AND MOVE FACTS:\\n" + text.split("\\n").slice(1).join("\\n") + "\\n\\nAnswer.", sources: [{ name: "Yahoo Finance quote" }, { name: "Stocktwits", detail: "Chip stocks rebound after worst week" }] };
}
function bb8eFull(st) { var f = (st.clientSources || []).slice(); if (st.peerSource) f.push(st.peerSource); if (st.bb8eMove) f.push.apply(f, st.bb8eMove.sources); return f; }
function bb8eCites(text, full) { return { text: text, keep: null }; }
function bb8dIsFact(line) { return /^MU .*x/.test(line); }
function bb8hIndex(st, facts) { return { n: bb8eFull(st).length, text: {}, fact: {}, factFigs: {}, known: {} }; }
function bb8hFigs(t) { var o = {}; String(t).replace(/\\[\\d+\\]/g, "").replace(/\\$(\\d+(?:\\.\\d+)?)|(\\d+(?:\\.\\d+)?)\\s*(?:%|x\\b)/g, function (m, a, b) { o[Number(a || b).toFixed(2)] = 1; return m; }); return o; }
function bb8hFixSentence(sent, idx) { return "ORIG:" + sent; }
function bb8iCiteNums(s) { var o = []; String(s).replace(/\\[(\\d{1,2}(?:\\s*,\\s*\\d{1,2})*)\\]/g, function (m, g) { g.split(/\\s*,\\s*/).forEach(function (x) { o.push(Number(x)); }); return m; }); return o; }
function bb8iKeep(sent, resolve, st) { for (var i = 0; i < BB8I_SPEC.length; i++) if (BB8I_SPEC[i].test(sent)) return false; return true; }
var mem = new Map();
function bb7TickerKeys(t) { return [String(t || "").toUpperCase()]; }
function bb7Recall(k) { return mem.get(k) || null; }
function bb8hKey(t, mode) { return "f4:" + t + (mode === "full" ? "" : ":free"); }
function bb7FormList(sub) { return sub.list; }
function bb7IsoDate(v) { var m = /^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})$/.exec(String(v)); return m ? m[3] + "-" + ("0" + m[1]).slice(-2) + "-" + ("0" + m[2]).slice(-2) : String(v); }
var shapeOut = null;
function bb7Shape(pack, opts) { return JSON.parse(JSON.stringify(shapeOut)); }
async function bb8Older(ticker, before, opts) { return { status: 200, body: bb7Shape() }; }
`;
function load2() {
  const ctx = { console: { warn() {} }, Date, Intl, JSON, Math, Object, String, Number, Array, RegExp, Promise, Map, WeakSet };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(FMT + STUBS + SPEC + WIN + STUBS2, ctx);
  vm.runInContext(B8L, ctx, { filename: "bb8l.js" });
  return ctx;
}
const NOW = Date.parse("2026-10-19T09:20:00Z");

test("earnings line: UK calendar date, (estimated) only when isEstimate, none when missing or past", () => {
  const c = load2();
  assert.equal(c.bb8lDay("2026-12-23", true), "Wed 23 Dec 2026");
  assert.equal(c.bb8lDay("2025-10-15"), "15 Oct 2025");
  assert.equal(c.bb8lDay("9/21/2026"), "21 Sep 2026");
  assert.equal(c.bb8lDay(""), "");
  assert.equal(c.bb8lDay("n/a"), "");
  const est = c.bb8lEarnFrom({ date: "2026-12-23", isEstimate: true }, "2026-10-19T09:20:00.000Z", "MU", NOW);
  assert.equal(c.bb8lEarnLine(est), "Next earnings: Wed 23 Dec 2026 (estimated)");
  assert.equal(c.bb8lEarnLine(c.bb8lEarnFrom({ date: "2026-12-23", isEstimate: false }, "", "MU", NOW)), "Next earnings: Wed 23 Dec 2026");
  assert.equal(c.bb8lEarnFrom({ date: "2026-10-18", isEstimate: false }, "", "MU", NOW), null);          // yesterday (UK)
  assert.ok(c.bb8lEarnFrom({ date: "2026-10-19", isEstimate: false }, "", "MU", NOW));                    // today still shown
  assert.equal(c.bb8lEarnFrom({ date: "", isEstimate: true }, "", "MU", NOW), null);
  assert.equal(c.bb8lEarnFrom(null, "", "MU", NOW), null);
  // UK "today" at 00:30 BST on 20 Oct is still 19 Oct in UTC: a 19 Oct date is past for UK readers.
  assert.equal(c.bb8lEarnFrom({ date: "2026-10-19" }, "", "MU", Date.parse("2026-10-19T23:30:00Z")), null);
  const src = c.bb8lEarnSrc(est, "MU", "MU");
  assert.equal(src.link, "https://finance.yahoo.com/quote/MU/");
  assert.equal(src.asOf, "2026-10-19T09:20:00.000Z");
  assert.match(src.detail, /calendarEvents, estimated/);
});

test("earnings source: /api/financials nextEarnings (RT32 cache) first, else Yahoo calendarEvents; one shared Yahoo call", async () => {
  const c = load2();
  c.RT32.cache.set("MU", { at: Date.now(), data: { earnings: { source: "Yahoo Finance", asOf: "2026-10-19T08:00:00.000Z", next: { date: "2026-12-23", isEstimate: true } }, nextEarnings: { date: "2026-12-23", estimate: 1.2, isEstimate: true } } });
  const a = await c.bb8lEarnGet("MU");
  assert.equal(a.date, "2026-12-23"); assert.equal(a.isEstimate, true); assert.equal(a.asOf, "2026-10-19T08:00:00.000Z"); assert.equal(c.yahooCalls, 0);
  const b = await c.bb8lEarnGet("NVDA");
  assert.equal(b.date, "2026-12-23"); assert.equal(c.yahooCalls, 1);
  await Promise.all([c.rt32Yahoo("AMD"), c.rt32Yahoo("AMD")]);
  assert.equal(c.yahooCalls, 2, "concurrent quoteSummary calls for one symbol share one request");
  c.yahooNext.date = "2026-01-20";
  assert.equal(await c.bb8lEarnGet("AVGO"), null, "past date: no line");
  c.yahooNext.date = "";
  assert.equal(await c.bb8lEarnGet("WDC"), null, "no date: no line");
});

test("card lead: Next earnings line with its own [n], Yahoo source, prompt updated; none without a date", async () => {
  const c = load2();
  c.store.bb8eCard = true; c.store.bb8eBody = { q: "What matters most about MU — Headwind?" };
  const pack = await c.bb8eMovePack("MU");
  assert.equal(pack.bb8lEarn.date, "2026-12-23");
  const out = c.bb8eLead(pack, true, 7);
  const lines = out.text.split("\n");
  assert.equal(lines[2], "Next earnings: Wed 23 Dec 2026 (estimated) [10]");
  assert.match(lines[3], /^In the news/);
  assert.equal(out.sources[2].name, "Yahoo Finance"); assert.equal(out.sources[2].link, "https://finance.yahoo.com/quote/MU/");
  assert.match(out.prompt, /Next earnings: Wed 23 Dec 2026 \(estimated\) \[10\]/);
  assert.match(out.prompt, /say it is estimated when the line says so/);
  assert.equal(out.paint.includes("[10]"), false);
  const none = c.bb8eLead({ base: "MU", ysym: "MU", bb8lEarn: null }, true, 7);
  assert.equal(none.text.includes("Next earnings"), false);
  // Non-card move question that does not ask about earnings: no lookup.
  const c2 = load2(); c2.store.bb8eCard = false; c2.store.bb8eBody = { q: "Why is MU down today?" };
  assert.equal((await c2.bb8eMovePack("MU")).bb8lEarn, undefined);
  c2.store.bb8eBody = { q: "When does MU report earnings?" };
  assert.equal((await c2.bb8eMovePack("MU")).bb8lEarn.date, "2026-12-23");
});

test("filters: a cited earnings-date sentence stays (bb8h and bb8i); wrong dates, 'confirmed' and attributed views go", async () => {
  const c = load2();
  c.store.bb8eCard = true; c.store.bb8eBody = { q: "x" };
  const pack = await c.bb8eMovePack("MU");
  c.store.bb8eMove = c.bb8eLead(pack, true, 0);
  const idx = c.bb8hIndex(c.store, []);
  assert.equal(idx.bb8lEarnN, 3);
  assert.equal(c.bb8hFixSentence("Micron is set to report its next quarterly results on 23 Dec [3].", idx), "Micron is set to report its next quarterly results on 23 Dec [3].");
  assert.equal(c.bb8hFixSentence("Its next earnings date is 23 December [2].", idx), "Its next earnings date is 23 December [3].");
  assert.equal(c.bb8hFixSentence("MU's next earnings date is 23 Dec.", idx), "MU's next earnings date is 23 Dec [3].");
  assert.equal(c.bb8hFixSentence("MU reports earnings on 18 Nov [3].", idx), "");
  assert.equal(c.bb8hFixSentence("MU has confirmed it reports results on 23 Dec [3].", idx), "");
  assert.equal(c.bb8hFixSentence("MU has not confirmed the results date of 23 Dec [3].", idx), "MU has not confirmed the results date of 23 Dec [3].");
  assert.equal(c.bb8hFixSentence("MU shares fell 5.63% [3].", idx), "ORIG:MU shares fell 5.63% [99].", "not about earnings: may not cite the line");
  assert.equal(c.bb8hFixSentence("Results are due on 23 Dec with EPS of $2.10 [3].", idx), "ORIG:Results are due on 23 Dec with EPS of $2.10 [3].", "a figure the line does not carry is bb8h's call");
  const R = n => c.bb8eFull(c.store)[n - 1] || null;
  assert.equal(c.bb8iKeep("Micron is set to report its next quarterly results on 23 Dec [3].", R, c.store), true);
  assert.equal(c.bb8iKeep("Micron is set to report its next quarterly results on 23 Dec [2].", R, c.store), false, "cites the news line, not the earnings line");
  assert.equal(c.bb8iKeep("Analysts expect strong results when MU reports on 23 Dec [3].", R, c.store), false);
  assert.equal(c.bb8iKeep("MU could see a rally when it reports results on 23 Dec [3].", R, c.store), false);
});

test("valuation answers: line goes before In short with the final [n]; prompt numbered like the source list", async () => {
  const c = load2();
  c.store.bb8eMode = "valuation"; c.store.bb8eBody = { q: "Is MU expensive versus peers ahead of earnings?" };
  await c.bb2Read0({ q: "Is MU expensive versus peers ahead of earnings?" });
  c.store.clientSources = [{ name: "Reuters" }]; c.store.peerSource = { name: "Yahoo Finance" };
  await c.generateAi({ system: "SYS", messages: [{ role: "user", content: "q" }] });
  const sys = c.calls[c.calls.length - 1].system;
  assert.match(sys, /NEXT EARNINGS[^\n]*\[3\][^\n]*\nNext earnings: Wed 23 Dec 2026 \(estimated\) \[3\]/);
  assert.equal(c.bb8eFull(c.store).length, 3);
  const text = "Peer comparisons:\nMU forward P/E 4.9x is lower than NVDA 15.3x. [2]\n\nIn short: MU is the cheapest. [2]";
  const seen = c.bb8eCites(text, c.bb8eFull(c.store)).text;
  assert.match(seen, /\[2\]\n\nNext earnings: Wed 23 Dec 2026 \(estimated\) \[3\]\n\nIn short:/);
  assert.equal(c.bb8eCites(seen, c.bb8eFull(c.store)).text.split("Next earnings").length, 2, "inserted once");
  const c2 = load2(); c2.store.bb8eMode = "valuation"; c2.store.bb8eBody = { q: "How does MU compare with peers on valuation?" };
  await c2.bb2Read0({}); assert.equal(c2.store.bb8lEarnP, undefined, "valuation question without earnings: no line");
});

test("insiders: meta.window stays the page window; meta.span is the whole loaded span; UK display dates everywhere", async () => {
  const c = load2();
  c.shapeOut = { cik: "0001045810", insider: [{ insiderName: "A", transactionDate: "2026-09-21", filingDate: "2026-09-23" }, { insiderName: "B", transactionDate: "", filingDate: "2025-10-15" }],
    house: { items: [{ member: "M", filingDate: "2026-10-15", trades: [{ date: "2026-09-30" }] }] },
    meta: { window: { label: "Last 7 months", from: "2026-03-20", to: "2026-10-13", filings: 40, more: true, next: "before=2026-03-20" } } };
  const p1 = c.bb7Shape();
  assert.deepEqual(JSON.parse(JSON.stringify(p1.insider[0])), { insiderName: "A", transactionDate: "2026-09-21", filingDate: "2026-09-23", transactionDateUk: "21 Sep 2026", filingDateUk: "23 Sep 2026" });
  assert.equal(p1.insider[1].transactionDateUk, ""); assert.equal(p1.insider[1].filingDateUk, "15 Oct 2025");
  assert.equal(p1.house.items[0].filingDateUk, "15 Oct 2026"); assert.equal(p1.house.items[0].trades[0].dateUk, "30 Sep 2026");
  assert.equal(p1.meta.window.fromUk, "20 Mar 2026"); assert.equal(p1.meta.window.toUk, "13 Oct 2026");
  assert.deepEqual(JSON.parse(JSON.stringify(p1.meta.span)), { from: "2026-03-20", to: "2026-10-13", label: "Last 7 months", fromUk: "20 Mar 2026", toUk: "13 Oct 2026", before: null, toSource: "page" });
  // The first page's full scan is cached (bb8h key); the older page's window covers only that page.
  c.mem.set("f4:NVDA", { at: Date.now(), body: { newestFiling: "2026-10-13", complete: true } });
  c.shapeOut.meta.window = { label: "Last 5 months", from: "2025-10-15", to: "2026-03-19", filings: 40, more: true, next: "before=2025-10-15" };
  const p2 = await c.bb8Older("NVDA", "2026-03-20", { codes: "PS" });
  assert.equal(p2.body.meta.window.label, "Last 5 months", "meta.window unchanged (compat)");
  assert.equal(p2.body.meta.window.from, "2025-10-15");
  assert.deepEqual(JSON.parse(JSON.stringify(p2.body.meta.span)), { from: "2025-10-15", to: "2026-10-13", label: "Last 1 year", fromUk: "15 Oct 2025", toUk: "13 Oct 2026", before: "2026-03-20", toSource: "newest-filing" });
  // Without the cached first page, the newest filing recorded from the SEC submissions list is used.
  c.mem.clear();
  c.bb7FormList({ cik: "1045810", tickers: ["NVDA"], list: [{ filingDate: "2026-10-13" }, { filingDate: "2026-03-20" }] });
  assert.equal((await c.bb8Older("NVDA", "2026-03-20", {})).body.meta.span.to, "2026-10-13");
  // Nothing known: the span falls back to the page.
  const c3 = load2(); c3.shapeOut = c.shapeOut;
  const p3 = await c3.bb8Older("NVDA", "2026-03-20", {});
  assert.equal(p3.body.meta.span.to, "2026-03-19"); assert.equal(p3.body.meta.span.toSource, "page");
});
