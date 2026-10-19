// Offline tests for deploy/patch_bb8b.py. Loads the bb8b block with stubs; no network, no live files.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8b.py"), "utf8");
const block = patch.slice(patch.indexOf("// \u2500\u2500 bb8b \u2500\u2500"), patch.indexOf("// BB8B_JS_END") + "// BB8B_JS_END".length);
for (const bad of ["CREATE TABLE", "setInterval(", "stripe.webhooks", ".tier"]) assert.equal(block.includes(bad), false, bad);
assert.match(patch, /c5cdaf0eb4cdee4daed380e57d2a1522/);
assert.match(patch, /bb8bLeadWait\(\)/);
assert.match(patch, /await pendingLead/);

const STUBS = `
var bb2Mem = { vals: new Map() };
var RT32 = { cache: new Map() };
function bb8DeadEndRe() { return /[^.!?\\n]*?\\bcannot\\b[^.!?\\n]{0,60}?\\bcompar\\w*[^.!?\\n]*[.!?]?/i; }
function bb8ApplyNtm(sym, v) { v.forward = 15.27; return v; }
function bb3bReadCache(syms) { var o = {}, any = false; syms.forEach(function (s) { var h = bb2Mem.vals.get(s); if (h) { o[s] = h.v; any = true; } }); return any ? o : null; }
async function bb2Refresh(syms) { syms.forEach(function (s) { bb2Mem.vals.set(s, { at: Date.now(), v: { trailing: 20, forward: 13.45, price: 100 } }); }); }
function bb3bTrimBody(body) { return body; }
function bb3bRewrite(text) { return String(text); }
function bb3bHold() { return false; }
function bb3bCompose(reply) { return String(reply).trim(); }
function bb2Footer(sources) { return "\\n\\nSources:\\n[1] x"; }
function bb2System() { return "BASE"; }
var builds = 0;
async function rt32Build(sym) { builds++; await new Promise(function (r) { setTimeout(r, 30); }); return { symbol: sym }; }
`;
function load() {
  const ctx = { console: { warn() {} }, Promise, Map, Set, Date, JSON, Math, setTimeout, clearTimeout };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(block, ctx, { filename: "bb8b.js" });
  return ctx;
}

test("valuation cache entries must carry the bb8b tag", async () => {
  const c = load();
  vm.runInContext("bb2Mem.vals.set('MU', { at: Date.now(), v: { trailing: 11.8, forward: 4.25 } })", c);
  assert.equal(c.bb3bReadCache(["MU"]), null);
  await c.bb2Refresh(["MU", "NVDA"]);
  const vals = c.bb3bReadCache(["MU", "NVDA"]);
  assert.equal(vals.MU.bb8b, "bb8b"); assert.equal(vals.MU.forward, 15.27);
});

test("client context and replayed answers lose old forward P/E and dead ends", async () => {
  const c = load();
  await c.bb2Refresh(["MU"]);
  const OLD = "MU forward P/E of 4.2x. This valuation metric provides insight into how the company's earnings are being valued. In conclusion, we cannot directly compare it to its peers at this time.";
  const body = { tickers: ["MU"], context: "Live valuation (Yahoo Finance): P/E 11.8x | Forward P/E 4.2x\nMU: trailing P/E (TTM) 11.8x · forward P/E 4.2x\nNVDA: trailing P/E (TTM) 27.1x · forward P/E 13.5x",
    messages: [{ role: "user", content: "q" }, { role: "assistant", content: OLD }, { role: "user", content: "q" }] };
  const out = c.bb3bTrimBody(body);
  assert.match(out.context, /Forward P\/E \(next 12 months\) 15\.3x/);
  assert.match(out.context, /MU: trailing P\/E \(TTM\) 11\.8x · forward P\/E \(next 12 months\) 15\.3x/);
  assert.match(out.context, /NVDA: trailing P\/E \(TTM\) 27\.1x · forward P\/E not available/);
  assert.ok(!/cannot directly compare|provides insight|4\.2x/.test(out.messages[1].content), out.messages[1].content);
  assert.equal(body.messages[1].content, OLD, "input body not mutated");
});

test("filler dropped, real content protected", () => {
  const c = load();
  assert.equal(c.bb3bRewrite("Margins rose. This valuation metric provides insight into how earnings are valued. Done."), "Margins rose. Done.");
  const keep = "This ratio gives MU a discount to NVDA at 11.8x.";
  assert.equal(c.bb3bRewrite(keep), keep);
  assert.equal(c.bb3bRewrite("Investors often use this to judge value."), "");
  assert.equal(c.bb3bRewrite("The P/E ratio is a common way to value shares."), "");
  assert.equal(c.bb3bRewrite("Revenue grew 40% year on year."), "Revenue grew 40% year on year.");
  assert.match(c.bb2System({}, null, []), /Do not add generic sentences/);
});

test("model-written Sources line stripped; footer starts with a blank line", () => {
  const c = load();
  assert.equal(c.bb3bCompose("Answer text.Sources: [1] Yahoo", null, 0), "Answer text.");
  assert.equal(c.bb3bCompose("Answer text.\n\nSources: [1] Yahoo\n[2] SEC", null, 0), "Answer text.");
  assert.equal(c.bb3bCompose("Talks about Sources: of revenue growth.", null, 0), "Talks about Sources: of revenue growth.");
  assert.ok(c.bb2Footer([]).startsWith("\n\nSources:"));
});

test("fundamentals symbols: non-US listings keep the dot and skip SEC", () => {
  const c = load();
  assert.equal(c.bb8bYahooSym("BP.L"), "BP.L"); assert.equal(c.bb8bYahooSym("0700.HK"), "0700.HK"); assert.equal(c.bb8bYahooSym("7203.T"), "7203.T");
  assert.equal(c.bb8bYahooSym("BRK.B"), "BRK-B"); assert.equal(c.bb8bYahooSym("BF.B"), "BF-B"); assert.equal(c.bb8bYahooSym("NVDA"), "NVDA");
  assert.equal(c.bb8bForeign("BP.L"), true); assert.equal(c.bb8bForeign("BRK.B"), false);
});

test("concurrent rt32Build calls for one symbol share one build", async () => {
  const c = load();
  const [a, b] = await Promise.all([c.rt32Build("NVDA"), c.rt32Build("nvda")]);
  assert.equal(a, b); assert.equal(vm.runInContext("builds", c), 1);
  await c.rt32Build("NVDA"); assert.equal(vm.runInContext("builds", c), 2);
});
