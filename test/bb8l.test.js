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
