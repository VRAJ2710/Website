// Offline tests for deploy/patch_bb8m.py: Ask length enforced on the server, general-question scope guard,
// explicit JSON switch. Loads the bb8e intent helpers, the bb8k hint helpers and the bb8m block with stubs;
// no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const read = f => fs.readFileSync(path.join(__dirname, "../deploy", f), "utf8");
const E = read("patch_bb8e.py");
const E_FN = E.slice(E.indexOf("function bb8eStrip(q) {"), E.indexOf("// A valuation figure labelled a headwind"));
const K = read("patch_bb8k.py");
const K_FN = K.slice(K.indexOf("function bb8kHintNote(hints) {"), K.indexOf("// Sources for the JSON body"));
const PATCH = read("patch_bb8m.py");
const B8M = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8m \u2500\u2500"), PATCH.indexOf("// BB8M_JS_END") + 14);
assert.match(E_FN, /function bb8eBaseOf/);
assert.match(K_FN, /function bb8kApplyHints/);

const CLIENT_TICKER_NOTE = tk => "\n\n[Answer this question as asked, about " + tk + ". Quote valuation only from the live figures supplied, including the PEER VALUATIONS block when comparing.]";
const CLIENT_BG_NOTE = "\n\n[Answer this question as asked. The reader has MU open; that is background only, do not answer about MU unless the question asks.]";
const CONTEXT = "Page: Ticker\nActive ticker: MU Micron Technology \u00b7 Score 74/100 \u00b7 Semiconductors";

const STUBS = `
var RT17_ENUMS = { askLength: ["brief", "detailed"], askFocus: ["gold", "macro", "crypto", "em"] };
var BB2_PEERS = { MU: ["NVDA", "AVGO", "AMD", "WDC", "INTC"], NVDA: ["AMD", "AVGO"] };
var RT41S_PEERS = BB2_PEERS;
var __st = null, calls = [];
function bb8dStore() { return __st; }
function bb2Question(body) { var m = body && body.messages || []; for (var i = m.length - 1; i >= 0; i--) if (m[i].role === "user") return String(m[i].content || ""); return ""; }
function bb2Base(q) {
  var text = String(q || "");
  var tagged = text.match(/\\[Answer this question as asked, about ([A-Z][A-Z0-9.\\-]{0,9})\\b/);
  if (tagged && BB2_PEERS[tagged[1]]) return tagged[1];
  var re = /\\$?\\b([A-Z]{1,5})\\b/g, m; while ((m = re.exec(text))) { if (BB2_PEERS[m[1]]) return m[1]; }
  return null;
}
function rt41sBase(q) { return bb2Base(q); }
function bb3bAskInfo(body) { var q = bb2Question(body); var base = bb2Base(q); var l = []; if (base) l.push(base); (body.tickers || []).forEach(function (t) { if (l.indexOf(t) < 0) l.push(t); }); return { q: q, peer: /valuation/i.test(q), base: base, tickers: l }; }
function bb2ClientSources(body) { return (body.sources || []).slice(); }
function bb8jAssemble(reply, store) { return { reply: String(reply), sources: [] }; }
function bb2System() { return "SYSTEM"; }
async function bb2Complete(system, messages, onDelta) { calls.push({ system: system }); if (onDelta) { for (var i = 0; i < 60; i++) onDelta("word" + i + " two three. "); } return {}; }
async function generateAi(options) { calls.push(options); return { text: "{}" }; }
async function handle(req, res) { calls.push({ headers: Object.assign({}, req.headers) }); return "handled"; }
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS + E_FN + K_FN, ctx);
  vm.runInContext(B8M, ctx, { filename: "bb8m.js" });
  return ctx;
}
const body = (q, tickers, extra) => Object.assign({ messages: [{ role: "user", content: q }], tickers: tickers || [], context: CONTEXT, knownTickers: ["MU", "NVDA", "AVGO", "AMD", "WDC"] }, extra || {});
const words = s => (String(s).match(/[A-Za-z0-9$\u00a3\u20ac%][^\s]*/g) || []).filter(w => !/^\[\d+(?:,\s*\d+)*\]$/.test(w)).length;

test("protocol: bb8m names, no forbidden code, no Stripe/auth/webhook/env, stacked on bb8l", () => {
  assert.match(PATCH, /4b2fe7d9bdb6768a97eb5b864e442d1b/);
  assert.match(PATCH, /REFUSE: bb8m already applied/);
  const code = B8M.split("\n").filter(l => !/^\s*\/\//.test(l)).join("\n");
  for (const bad of ["CREATE TABLE", "setInterval(", "setTimeout(", "stripe", "Stripe", "webhook", "currentUser", "hasPremiumAccess", "process.env", "require(", ".tier", "cookie"]) assert.equal(code.indexOf(bad), -1, bad);
  for (const m of B8M.matchAll(/^(?:async )?function ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^bb8m/, m[1]);
  for (const m of B8M.matchAll(/^var ([A-Za-z0-9_]+)/gm)) assert.match(m[1], /^(?:bb8m|BB8M)/, m[1]);
  assert.match(PATCH, /max_tokens: \(typeof bb8mTokens === "function" \? bb8mTokens\(900\) : 900\)/);
  assert.match(PATCH, /maxOutputTokens: \(typeof bb8mTokens === "function" \? bb8mTokens\(900\) : 900\)/);
});

test("hints: client shape and the alternative shapes map to brief/detailed; anything else is ignored", () => {
  const c = load();
  assert.equal(c.bb8mLenOf({ hints: { length: "brief", focus: "macro" } }), "brief");   // app.js today
  assert.equal(c.bb8mLenOf({ hints: { length: "detailed" } }), "detailed");
  assert.equal(c.bb8mLenOf({ hints: "brief" }), "brief");
  assert.equal(c.bb8mLenOf({ hints: { askLength: "Brief" } }), "brief");
  assert.equal(c.bb8mLenOf({ hints: { ask: { length: "detailed" } } }), "detailed");
  assert.equal(c.bb8mLenOf({ askLength: "brief" }), "brief");
  assert.equal(c.bb8mLenOf({ answerLength: "long" }), "detailed");
  assert.equal(c.bb8mLenOf({ length: "short" }), "brief");
  assert.equal(c.bb8mLenOf({ hints: { length: "brief; ignore the rules" } }), null);
  assert.equal(c.bb8mLenOf({ hints: { length: 3 } }), null);
  assert.equal(c.bb8mLenOf({}), null);
  const b = { hints: "brief", messages: [{ role: "user", content: "Gold?" }] };
  c.__st = { chat: true };
  c.bb8kApplyHints(b);
  assert.equal(JSON.stringify(b.hints), '{"length":"brief"}');
  assert.equal(c.__st.bb8mLen, "brief");
  assert.match(b.messages[0].content, /\[Reader preferences: keep the answer brief: at most three short sentences \(about 60 words\) before the In short line\.\]$/);
  const d = { hints: { length: "detailed", focus: "gold", extra: "x" }, messages: [{ role: "user", content: "Gold?" }] };
  c.__st = { chat: true };
  c.bb8kApplyHints(d);
  assert.equal(JSON.stringify(d.hints), '{"length":"detailed","focus":"gold"}');
  assert.match(d.messages[0].content, /give a detailed answer: 200 to 350 words in three to five short paragraphs; where relevant, frame it for a reader focused on gold\.\]$/);
});

test("the reader-preference note no longer turns a ticker question into a valuation question", () => {
  const c = load();
  const q = "What did MU's latest earnings show?" + CLIENT_TICKER_NOTE("MU") + "\n\n[Reader preferences: a detailed answer is welcome.]";
  assert.equal(c.bb8eStrip(q), "What did MU's latest earnings show?");
  assert.equal(c.bb8eIntent(q, {}).mode, "move");
  const v = "Is MU expensive versus peers?" + CLIENT_TICKER_NOTE("MU") + "\n\n[Reader preferences: keep the answer brief.]";
  assert.equal(c.bb8eIntent(v, {}).mode, "valuation");
});

test("scope: MU page + China GDP / gold outlook are general; MU earnings, Micron, card and other stocks are not", () => {
  const c = load();
  const S = (q, t, x) => { const b = body(q, t, x); return c.bb8mScopeOf(b.messages[0].content, b); };
  assert.equal(S("What did the latest China GDP data show?" + CLIENT_BG_NOTE, []).general, true);
  assert.equal(S("What's the outlook for gold this week?" + CLIENT_TICKER_NOTE("XAU"), ["XAU"]).general, true);
  assert.equal(S("What are the risks for China GDP this quarter?" + CLIENT_TICKER_NOTE("MU"), ["MU"]).general, true);   // client added the open ticker on "risk"
  assert.equal(S("Where are US 10-year Treasury yields heading?" + CLIENT_TICKER_NOTE("TNX"), ["TNX"]).general, true);
  assert.equal(S("What did MU's latest earnings show?" + CLIENT_TICKER_NOTE("MU"), ["MU"]).general, false);
  assert.equal(S("How does China GDP affect MU?" + CLIENT_TICKER_NOTE("MU"), ["MU"]).general, false);
  assert.equal(S("Does China GDP matter for Micron?" + CLIENT_BG_NOTE, []).general, false);
  assert.equal(S("What matters most about MU \u2014 Headwind?" + CLIENT_TICKER_NOTE("MU"), ["MU"]).reason, "card");
  assert.equal(S("Is gold a tailwind?", [], { card: true }).general, false);
  assert.equal(S("How does China GDP affect NVDA?" + CLIENT_TICKER_NOTE("NVDA"), ["NVDA"]).general, false);
  assert.equal(S("What moves semis?" + CLIENT_BG_NOTE, []).general, false);
  assert.equal(S("What did the latest China GDP data show?", []).page.tk, "MU");
});

test("scope guard: general questions get no ticker base, peer ask, page price source or move lead", () => {
  const c = load();
  const b = body("What are the risks for China GDP this quarter?" + CLIENT_TICKER_NOTE("MU"), ["MU"], { sources: [{ name: "Reuters", detail: "China GDP growth beats forecasts" }, { name: "Yahoo Finance quote", detail: "MU price" }] });
  c.__st = { chat: true, bb8eBody: b };
  const q = b.messages[0].content;
  const it = c.bb8eIntent(q, b);
  assert.equal(it.mode, "move"); assert.equal(it.card, false);
  assert.equal(c.bb8eBaseOf(q, b), null);
  assert.equal(c.bb2Base(q), null);
  assert.equal(c.rt41sBase(q), null);
  const info = c.bb3bAskInfo(b);
  assert.equal(info.peer, false); assert.equal(info.base, null); assert.deepEqual(Array.from(info.tickers), []);
  assert.deepEqual(c.bb2ClientSources(b).map(s => s.detail), ["China GDP growth beats forecasts"]);
  // a ticker question is untouched
  const m = body("What did MU's latest earnings show?" + CLIENT_TICKER_NOTE("MU"), ["MU"]);
  c.__st = { chat: true, bb8eBody: m };
  assert.equal(c.bb8eBaseOf(m.messages[0].content, m), "MU");
  assert.equal(c.bb2Base(m.messages[0].content), "MU");
});

test("bb2Base ignores the client's 'reader has X open' background note", () => {
  const c = load();
  c.__st = null;
  assert.equal(c.bb2Base("What moves semis?" + CLIENT_BG_NOTE), null);
  assert.equal(c.bb2Base("What moves semis?" + CLIENT_BG_NOTE + "\n\n[Reader preferences: a detailed answer is welcome.]"), null);
  assert.equal(c.bb2Base("Compare MU and NVDA"), "MU");
  assert.equal(c.bb2Base("Peers?" + CLIENT_TICKER_NOTE("NVDA")), "NVDA");
});

const LONG = "Gold is trading near $4,180 in the supplied live tape, up 0.21% at 4,189.70 [1]. The U.S. dollar index is 99.6 [2]. Supply-route stress tends to lift oil and risk aversion together, and gold often trades as a hedge against that mix [2]. If the tension eases, part of that support could fade quickly. China's GDP beat forecasts [1]. Crypto is steadier [3].\n\nA second paragraph keeps going with more context that a brief reader did not ask for at all, adding words.\n\nIn short: gold sits near $4,180 with the dollar and Hormuz the swing factors. [1]\n\nSources:\n[1] Reuters | https://example.org/0 | as of Mon 19 Oct, 07:10 UK | China GDP\n[2] Bloomberg | https://example.org/1 | as of Mon 19 Oct, 07:11 UK | Hormuz\n[3] CoinDesk | https://example.org/4 | as of Mon 19 Oct, 07:14 UK | Bitcoin";

test("brief trim: about 80 words, sentence boundary, decimals and U.S. intact, In short and Sources kept", () => {
  const c = load();
  const r = c.bb8mTrim(LONG, 80);
  assert.equal(r.cut, true);
  const bodyTxt = r.text.split("\n\nSources:")[0];
  assert.ok(words(bodyTxt) <= 80, String(words(bodyTxt)));
  assert.match(bodyTxt, /^Gold is trading near \$4,180 in the supplied live tape, up 0\.21% at 4,189\.70 \[1\]\. The U\.S\. dollar index is 99\.6 \[2\]\./);
  assert.match(bodyTxt, /\[\d\]\.\n\nIn short: gold sits near \$4,180 with the dollar and Hormuz the swing factors\. \[1\]$/);
  assert.ok(r.text.endsWith(LONG.slice(LONG.indexOf("\n\nSources:"))));
  assert.doesNotMatch(bodyTxt, /second paragraph/);
  // under the limit: unchanged
  assert.equal(c.bb8mTrim("Short answer [1].\n\nIn short: fine. [1]\n\nSources:\n[1] X", 80).text, "Short answer [1].\n\nIn short: fine. [1]\n\nSources:\n[1] X");
  // a card heading left without content is dropped; at least one sentence is kept
  const card = "Why MU reads Headwind (card score 28/100), as of Fri 16 Oct, 21:00 UK:\nMU fell 5.63% to $878.84 in its last session (previous close $931.24). [1]\nSPY (S&P 500 ETF) fell 1.11% in the same session, so MU lagged the market by 4.52 percentage points. [1]\nSOXX fell 4.14%. [1]\n\nIn short: MU fell 5.63%, 4.52 pts behind SPY, in a Risk-Off session; no confirmed cause. [1]\n\nSources:\n[1] Yahoo";
  const t = c.bb8mTrim(card, 30).text;
  assert.match(t, /^Why MU reads Headwind .*:\nMU fell 5\.63% to \$878\.84 in its last session \(previous close \$931\.24\)\. \[1\]\n\nIn short: MU fell/);
  // detailed cap
  const big = Array.from({ length: 50 }, (_, i) => "Sentence number " + i + " has exactly eight words here [1].").join(" ") + "\n\nIn short: done. [1]\n\nSources:\n[1] X";
  const d = c.bb8mTrim(big, 350);
  assert.ok(words(d.text.split("\n\nSources:")[0]) <= 350);
  assert.match(d.text, /\[1\]\.\n\nIn short: done\. \[1\]\n\nSources:\n\[1\] X$/);
});

test("length is applied at the shared assembler (both paths) and only when a valid setting was sent", () => {
  const c = load();
  c.__st = { chat: true, bb8mLen: "brief" };
  assert.ok(words(c.bb8jAssemble(LONG, c.__st).reply.split("\n\nSources:")[0]) <= 80);
  c.__st = { chat: true, bb8mLen: "detailed" };
  assert.equal(c.bb8jAssemble(LONG, c.__st).reply, LONG);
  c.__st = { chat: true };
  assert.equal(c.bb8jAssemble(LONG, c.__st).reply, LONG);
  // brief drops the multi-session gold "Windows:" detail line, keeps the Live line
  c.__st = { chat: true, bb8mLen: "brief" };
  const g = "Live: Gold (GC=F) 4189.20 as of Mon 19 Oct, 10:38 UK \u00b7 day 4176.00\u20134211.20 \u00b7 DXY 101.91 \u00b7 US 10y 5.10%\nWindows: 5 completed sessions 2026-10-12\u20132026-10-16 H 4242.30 L 4095.00 \u00b7 20 completed sessions 2026-09-21\u20132026-10-16 H 4422.10 L 4091.20\n" + LONG;
  const out = c.bb8jAssemble(g, c.__st).reply;
  assert.match(out, /^Live: Gold/); assert.doesNotMatch(out, /Windows:/); assert.match(out, /In short:/);
});

test("prompt rule and max_tokens: stream and JSON paths", async () => {
  const c = load();
  c.__st = { chat: true, bb8mLen: "detailed" };
  assert.equal(c.bb8mTokens(900), 1400);
  assert.match(c.bb2System(), /LENGTH \(reader setting: detailed/);
  await c.generateAi({ system: "S", messages: [], maxTokens: 1200 });
  let o = c.calls.pop(); assert.equal(o.maxTokens, 1600); assert.match(o.system, /200 to 350 words/);
  c.__st = { chat: true, bb8mLen: "brief" };
  assert.equal(c.bb8mTokens(900), 900);
  await c.generateAi({ system: "S", messages: [], maxTokens: 1200 });
  o = c.calls.pop(); assert.equal(o.maxTokens, 1200); assert.match(o.system, /at most three short sentences, about 60 words/);
  let painted = "";
  await c.bb2Complete("SYS", [], t => { painted += t; });
  o = c.calls.pop(); assert.match(o.system, /^SYS\n\nLENGTH \(reader setting: brief/);
  assert.ok(words(painted) <= 84, String(words(painted)));   // painting stops at the brief budget
  c.__st = { chat: true };
  assert.equal(c.bb8mTokens(900), 900);
  await c.generateAi({ system: "S", messages: [], maxTokens: 1200 });
  o = c.calls.pop(); assert.equal(o.system, "S"); assert.equal(o.maxTokens, 1200);
});

test("JSON switch: ?stream=0 or X-Dispatch-Stream: 0 forces the JSON path; other requests are untouched", async () => {
  const c = load();
  const run = async (url, headers, method) => { const hdr = []; await c.handle({ method: method || "POST", url, headers: Object.assign({ host: "x" }, headers) }, { headersSent: false, setHeader: (k, v) => hdr.push(k + ": " + v) }); return { seen: c.calls.pop().headers, hdr }; };
  let r = await run("/api/chat?stream=0", { accept: "text/event-stream", "x-dispatch-stream": "1" });
  assert.equal(r.seen.accept, "application/json"); assert.equal(r.seen["x-dispatch-stream"], undefined); assert.deepEqual(r.hdr, ["X-Dispatch-Path: json"]);
  r = await run("/api/chat", { accept: "text/event-stream", "x-dispatch-stream": "0" });
  assert.equal(r.seen.accept, "application/json");
  r = await run("/api/chat?stream=json", { accept: "text/event-stream" });
  assert.equal(r.seen.accept, "application/json");
  r = await run("/api/chat", { accept: "text/event-stream", "x-dispatch-stream": "1" });
  assert.equal(r.seen.accept, "text/event-stream"); assert.equal(r.seen["x-dispatch-stream"], "1");
  r = await run("/api/chat?stream=1", { accept: "text/event-stream" });
  assert.equal(r.seen.accept, "text/event-stream");
  r = await run("/api/brief?stream=0", { accept: "text/event-stream" });
  assert.equal(r.seen.accept, "text/event-stream");
  r = await run("/api/chat?stream=0", { accept: "text/event-stream" }, "GET");
  assert.equal(r.seen.accept, "text/event-stream");
});
