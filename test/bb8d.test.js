// Offline tests for deploy/patch_bb8d.py. Loads the bb8d block with stubs; no network, no live files.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8d.py"), "utf8");
const block = patch.slice(patch.indexOf("// \u2500\u2500 bb8d \u2500\u2500"), patch.indexOf("// BB8D_JS_END") + "// BB8D_JS_END".length);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe", ".tier", "process.env"]) assert.equal(block.includes(bad), false, bad);
assert.match(patch, /2d807112acf22009af0fa09da742f94c/);
for (const m of block.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8d/, m[1]);

const STUBS = `
var bb2Als = { getStore: function () { return globalThis.__store || null; } };
var bb2Mem = { vals: new Map() };
function bb8cAllowed(facts) { var set = {}; (facts || []).forEach(function (f) { (String(f.sentence).match(/\\d+(?:\\.\\d+)?(?=x)/g) || []).forEach(function (n) { set[Number(n).toFixed(1)] = 1; }); }); return set; }
function bb8bFillerRe() { return /[^.!?\\n]*\\bthis (?:valuation )?(?:metric|ratio) (?:provides|gives)[^.!?\\n]*[.!?]?/gi; }
function bb3LeadText(built, cite) { return (built.asOf ? "Peer comparisons as of " + built.asOf + ":" : "Peer comparisons:") + (cite ? " [" + cite + "]" : "") + "\\n" + built.facts.map(function (f) { return f.sentence; }).join("\\n") + "\\n\\n"; }
function bb3bCompose(reply, built, cite) { return "INNER:" + reply; }
async function bb2Complete(system, messages, onDelta) {
  var text = globalThis.__model, n = globalThis.__chunk || 7;
  for (var i = 0; i < text.length; i += n) { onDelta(text.slice(i, i + n)); await new Promise(function (r) { setTimeout(r, 0); }); }
  return { provider: "stub" };
}
function bb2Footer(sources) { return "\\n\\nSources:\\n" + sources.map(function (s, i) { return "[" + (i + 1) + "] " + s.name + (s.asOf ? " | as of " + s.asOf : ""); }).join("\\n"); }
function bb2System() { return "AUTHORITATIVE PEER COMPARISONS as of 2026-10-16 20:00 UTC"; }
async function buildChatLiveMarketBlock() { return "Gold last 4000 (as of 2026-10-16T20:00:00.000Z)"; }
function bb2FixSentence(s, facts) { return /trailing|ttm/i.test(s) && /forward/i.test(s) && /lower|higher|cheaper/i.test(s) ? "Trailing P/E (TTM) and forward P/E are different bases and are not compared." : s; }
function bb5eLondon(ms, now) { return "old"; }
function bb5hHm(ms) { return "old"; }
`;
function load() {
  const ctx = { console: { warn() {} }, Promise, Map, Set, Date, JSON, Math, Intl, Object, String, Number, Array, RegExp, Error, setTimeout, clearTimeout };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(block, ctx, { filename: "bb8d.js" });
  return ctx;
}
const one = (a, b, basis, va, vb) => {
  const label = basis === "trailing" ? "trailing P/E (TTM)" : "forward P/E (next 12 months)";
  if (va == null || vb == null) {
    const who = va == null ? a : b;
    return { a, b, basis, dir: "missing", sentence: `${who} ${label} was not reported, so ${a} and ${b} are not compared on ${label}.` };
  }
  const dir = Math.abs(va - vb) < 0.05 ? "in line" : va < vb ? "lower" : "higher";
  return { a, b, basis, dir, va, vb, sentence: dir === "in line" ? `${a} ${label} ${va.toFixed(1)}x is in line with ${b} ${label} ${vb.toFixed(1)}x.` : `${a} ${label} ${va.toFixed(1)}x is ${dir} than ${b} ${label} ${vb.toFixed(1)}x by ${Math.abs(va - vb).toFixed(1)}x (1.0%).` };
};
function build(base, rows) {
  const facts = [];
  Object.keys(rows).filter(s => s !== base).forEach(s => ["trailing", "forward"].forEach(basis => {
    const k = basis === "trailing" ? 0 : 1, va = rows[base][k], vb = rows[s][k];
    if (va == null && vb == null) return;
    facts.push(one(base, s, basis, va, vb));
  }));
  return { base, facts, asOf: "2026-10-16 20:00 UTC" };
}
const MU = build("MU", { MU: [11.8, 4.9], NVDA: [27.1, 15.3], AVGO: [42.0, 17.2], AMD: [134.9, 37.5], WDC: [12.3, 13.6], INTC: [null, 45.2] });
const MODEL = [
  "Micron (MU) has a forward P/E of 4.9x (versus NVDA at 15.3x), the lowest in the group.",
  "Trailing P/E (TTM) and forward P/E are different bases and are not compared with each other.",
  "Memory pricing (DRAM and NAND) has improved, which has lifted margins.",
  "This valuation metric provides insight into how the market values earnings.",
  "In conclusion, while we know MU's valuation, we cannot directly compare it to its peers at this time.",
  "In short, MU looks undervalued and is an opportunity versus its peers.",
  "Sources: [1] Yahoo Finance"
].join("\n");
const VERDICT = "In short: on next-12-month earnings MU is the cheapest of its peers at 4.9x, against 13.6–45.2x; on trailing earnings (TTM) MU is the cheapest of its peers at 11.8x, against 12.3–134.9x; INTC's trailing P/E (TTM) isn't reported.";
const BAD = /different bases|cannot|undervalued|opportunit|provides insight|In conclusion|In short, MU looks/;

test("stream path: awkward chunks, model conclusion and dead ends removed, server verdict appended last", async () => {
  for (const chunk of [3, 7, 11, 29]) {
    const ctx = load();
    ctx.__store = { facts: MU.facts };
    ctx.__model = MODEL; ctx.__chunk = chunk;
    let painted = "";
    await ctx.bb2Complete("sys", [], d => { painted += d; });
    for (const s of ctx.bb8dSplit(painted.replace(/\n/g, " "))) assert.ok(ctx.bb8dBalanced(s), "chunk " + chunk + " painted fragment: " + s);
    assert.doesNotMatch(painted, BAD, "chunk " + chunk + ": " + painted);
    assert.doesNotMatch(painted, /Sources:/);
    assert.match(painted, /Memory pricing \(DRAM and NAND\) has improved, which has lifted margins\./);
    const acc = "Peer comparisons as of x:\n" + MU.facts.map(f => f.sentence).join("\n") + "\n\n" + painted;
    const reply = ctx.bb3bCompose(acc, MU, 2) + ctx.bb2Footer([{ name: "Yahoo Finance", asOf: "2026-10-16T20:00:00.000Z" }]);
    assert.doesNotMatch(reply, BAD);
    assert.match(reply, /^Peer comparisons as of Fri 16 Oct, 21:00 UK: \[2\]\n/);
    assert.match(reply, /Micron \(MU\) has a forward P\/E of 4\.9x \(versus NVDA at 15\.3x\), the lowest in the group\./);
    const v = reply.indexOf(VERDICT);
    assert.ok(v > 0, reply);
    assert.equal(reply.slice(v + VERDICT.length, v + VERDICT.length + 11), "\n\nSources:\n");
    assert.match(reply, /\[1\] Yahoo Finance \| as of Fri 16 Oct, 21:00 UK/);
    assert.equal((reply.match(/In short/g) || []).length, 1);
  }
});

test("stream paint never glues words across chunk boundaries (sentences on one line, chunk sizes 1-15)", async () => {
  const para = "Micron trades at a trailing P/E of 11.8x and a forward P/E of 4.2x, while NVDA trades at 13.5x forward. This valuation metric provides insight into how the company's earnings are being valued by the market. Memory pricing has improved this year for the sector. In conclusion, while we know MU's valuation, we cannot directly compare it to its peers at this time.\nSources: [1] Yahoo Finance";
  const words = new Set(para.split(/\s+/));
  for (let chunk = 1; chunk <= 15; chunk++) {
    const ctx = load();
    ctx.__store = { facts: MU.facts };
    ctx.__model = para; ctx.__chunk = chunk;
    let painted = "";
    await ctx.bb2Complete("sys", [], d => { painted += d; });
    for (const w of painted.split(/\s+/).filter(Boolean)) assert.ok(words.has(w), "chunk " + chunk + " glued word: " + w);
    assert.equal(painted.trim(), "Memory pricing has improved this year for the sector.", "chunk " + chunk);
  }
});

test("JSON path: no raw stream text, the reply itself is cleaned and gets the same verdict", () => {
  const ctx = load();
  ctx.__store = { facts: MU.facts };
  const out = ctx.bb3bCompose(MODEL, MU, 1);
  assert.doesNotMatch(out, BAD);
  assert.ok(out.endsWith(VERDICT), out);
});

test("garbled stream text from the old pipeline never reaches the final reply", () => {
  const ctx = load();
  ctx.__store = null;
  const garbled = "Micron (Trailing P/E (TTM) and forward P/E are different bases and are not compared.\nIn In short, on the figures shown, MU's\nMemory demand is strong.";
  const out = ctx.bb3bCompose(garbled, MU, 1);
  assert.doesNotMatch(out, /Micron \(|In In|different bases|MU's$/m);
  assert.match(out, /Memory demand is strong\./);
  assert.ok(out.endsWith(VERDICT));
});

test("verdict cases: cheapest, most expensive, middle, in line, missing peer, missing base, neutral wording", () => {
  const ctx = load();
  const v = rows => ctx.bb8dConclusion(build("X", rows));
  assert.equal(v({ X: [10, 5], A: [20, 8], B: [30, 9] }), "In short: on next-12-month earnings X is the cheapest of its peers at 5.0x, against 8.0–9.0x; on trailing earnings (TTM) X is the cheapest of its peers at 10.0x, against 20.0–30.0x.");
  assert.equal(v({ X: [50, 40], A: [20, 8] }), "In short: on next-12-month earnings X is the most expensive of its peers at 40.0x, against 8.0x; on trailing earnings (TTM) X is the most expensive of its peers at 50.0x, against 20.0x.");
  assert.equal(v({ X: [null, 12], A: [20, 8], B: [30, 15], C: [9, 12] }), "In short: on next-12-month earnings X sits in the middle of its peers at 12.0x: below B (15.0x), above A (8.0x), in line with C; X's trailing P/E (TTM) isn't reported.");
  assert.equal(v({ X: [10, 5], A: [10, 5] }), "In short: on next-12-month earnings X is in line with its peers at 5.0x; on trailing earnings (TTM) X is in line with its peers at 10.0x.");
  assert.equal(v({ X: [10, 5], A: [null, 8], B: [null, 9] }), "In short: on next-12-month earnings X is the cheapest of its peers at 5.0x, against 8.0–9.0x; trailing P/E (TTM) isn't reported for A and B.");
  assert.equal(v({ X: [10, null], A: [20, 8] }), "In short: on trailing earnings (TTM) X is the cheapest of its peers at 10.0x, against 20.0x; X's forward P/E isn't reported.");
  assert.equal(ctx.bb8dConclusion({ facts: [] }), "");
  for (const rows of [{ X: [10, 5], A: [20, 8] }, { X: [50, 40], A: [20, 8] }, { X: [null, 12], A: [20, 8], B: [30, 15] }]) {
    const s = v(rows);
    assert.doesNotMatch(s, /\b(buy|sell|undervalued|overvalued|opportunit|target|upside)\b/i);
    assert.ok(ctx.bb8dBalanced(s));
  }
});

test("bracket-aware sentence split", () => {
  const ctx = load();
  assert.deepEqual([...ctx.bb8dSplit("Micron (MU) trades at 4.9x (vs. NVDA 15.3x). Next one!")], ["Micron (MU) trades at 4.9x (vs. NVDA 15.3x).", "Next one!"]);
  assert.deepEqual([...ctx.bb8dSplit("U.S. demand rose 3.5% today. Fine.")], ["U.S. demand rose 3.5% today.", "Fine."]);
  assert.deepEqual([...ctx.bb8dSplit("forward 4.9x (NVDA 15.3x).Trailing basis differs.")], ["forward 4.9x (NVDA 15.3x).", "Trailing basis differs."]);
  assert.equal(ctx.bb8dBalanced("Micron (Trailing P/E (TTM) is 4.9x."), false);
});

test("UK time everywhere in text: BST and GMT, lead/footer/prompt/live block/quote notes; machine fields unchanged", async () => {
  const ctx = load();
  assert.equal(ctx.bb8dUk(Date.parse("2026-10-16T20:00:00Z")), "Fri 16 Oct, 21:00 UK");
  assert.equal(ctx.bb8dUk(Date.parse("2026-11-20T20:00:00Z")), "Fri 20 Nov, 20:00 UK");
  assert.equal(ctx.bb8dUkText("as of 2026-10-16 20:00 UTC: [2]"), "as of Fri 16 Oct, 21:00 UK: [2]");
  assert.equal(ctx.bb8dUkText("as of 2026-10-16T20:00:00.000Z | MU"), "as of Fri 16 Oct, 21:00 UK | MU");
  assert.equal(ctx.bb8dUkText("2026-10-16T21:00:00+01:00"), "Fri 16 Oct, 21:00 UK");
  assert.equal(ctx.bb8dUkText("date 2026-10-16 only"), "date 2026-10-16 only");
  assert.match(ctx.bb2System(), /as of Fri 16 Oct, 21:00 UK/);
  assert.match(await ctx.buildChatLiveMarketBlock(), /as of Fri 16 Oct, 21:00 UK/);
  assert.equal(ctx.bb5eLondon(Date.parse("2026-10-19T13:30:00Z"), Date.now()), "Mon 19 Oct, 14:30");
  assert.equal(ctx.bb5hHm(Date.parse("2026-12-01T09:05:00Z")), "Tue 1 Dec, 09:05");
  const src = { name: "Yahoo Finance", asOf: "2026-10-16T20:00:00.000Z" };
  ctx.bb2Footer([src]);
  assert.equal(src.asOf, "2026-10-16T20:00:00.000Z", "source objects (JSON fields) are not modified");
});

test("no peer facts: other answers keep the existing path, only timestamps change", () => {
  const ctx = load();
  assert.equal(ctx.bb3bCompose("Gold rose (as of 2026-10-16T20:00:00Z).", { facts: [] }, 0), "INNER:Gold rose (as of Fri 16 Oct, 21:00 UK).");
});
