#!/usr/bin/env node
"use strict";
const fs = require("fs");
const vm = require("vm");

const appPath = process.argv[2];
if (!appPath) {
  console.error("usage: node deploy/rt61b_fe77_test.js app.js");
  process.exit(1);
}
const app = fs.readFileSync(appPath, "utf8");
const a = app.indexOf("// FE77_PURE_START");
const b = app.indexOf("// FE77_PURE_END");
if (a < 0 || b < a) {
  console.error("pure markers missing");
  process.exit(1);
}
const ctx = { console };
vm.createContext(ctx);
vm.runInContext(app.slice(a, b), ctx, { filename: "fe77-pure.js" });

function assert(cond, msg) {
  if (!cond) {
    console.error("FAIL " + msg);
    process.exit(1);
  }
  console.log("ok " + msg);
}

const desk = ctx.fe77_deskLine("XOM", 84);
assert(desk === "Top desk score: XOM 84/100 (Dispatch desk score).", "desk line");
const scrubbed = ctx.fe77_scrubDesk("Highest conviction on desk: XOM (84/100, Bullish).");
assert(scrubbed === desk, "scrub old conviction sentence");
assert(ctx.fe77_pct(3.21) === "+3.21%", "pct up");
assert(ctx.fe77_pct(-0.77).indexOf("0.77%") > 0, "pct down");
assert(ctx.fe77_pct(0.08) === "+0.08%", "pct futures");

const bb8o = {
  overweightLabel: "Leading themes",
  leadingThemesLabel: "Leading themes",
  leadingThemes: [{
    theme: "Gold",
    proxy: "GLD",
    proxyName: "SPDR Gold",
    changePct: 3.21,
    benchmark: { symbol: "SPY", name: "S&P 500", changePct: -0.77 },
    asOfUk: "Fri 16 Oct, 21:00 UK",
    source: { name: "Yahoo Finance", url: "https://finance.yahoo.com/quote/GLD/history/" }
  }],
  themesExcluded: [{ list: "overweight", theme: "Cash", reason: "no figure" }]
};
const view = ctx.fe77_themesView(bb8o, "leading");
assert(view.label === "Leading themes", "bb8o label");
assert(view.items.length === 1, "bb8o one theme");
assert(view.items[0].changeText === "+3.21%", "proxy change");
assert(view.items[0].spyText.indexOf("SPY") === 0 && view.items[0].spyText.indexOf("0.77%") > 0, "spy change");
assert(view.items[0].source === "Yahoo Finance", "source");
assert(view.items[0].asOf === "as of 21:00 UK", "as of");
assert(view.items[0].line.indexOf("Gold (GLD)") === 0, "theme name");
assert(view.excluded.indexOf("Cash") >= 0, "excluded");
const html = ctx.fe77_briefThemes(bb8o);
assert(html.indexOf("Leading themes") >= 0 && html.indexOf("+3.21%") >= 0 && html.indexOf("Yahoo Finance") >= 0 && html.indexOf("as of 21:00 UK") >= 0 && html.indexOf("Cash") >= 0, "brief html");

const alias = ctx.fe77_themesView({
  leadingThemes: [{ theme: "Treasuries", proxy: "IEF", change: 1.5, spyChange: -0.2, asOfUk: "09:05 UK", source: "Yahoo Finance" }]
}, "leading");
assert(alias.items[0].changeText === "+1.50%", "alias change");
assert(alias.items[0].spyText.indexOf("0.20%") > 0, "alias spy");
assert(alias.items[0].asOf === "as of 09:05 UK", "alias as of");

const old = ctx.fe77_themesView({ overweight: ["Gold", "Treasuries"] }, "leading");
assert(old.label === "Leading themes", "fallback label");
assert(old.items.map(function (it) { return it.name; }).join(",") === "Gold,Treasuries", "fallback names");
assert(old.items.every(function (it) { return !it.changeText; }), "fallback has no invented change");
assert(!ctx.fe77_themesView({ overweight: ["Gold"] }, "leading").excluded, "no excluded note");

function play(events) {
  const st = { early: null, done: null };
  let final = null;
  events.forEach(function (ev) {
    ctx.fe77_takeStreamMeta(ev, st);
    if (ev.done) final = ev;
  });
  return ctx.fe77_streamMeta(final, st);
}
const quote = { price: 4171.7, asOfUk: "11:57:00 UK", symbol: "XAU", source: "gold-api" };
const early = play([{ meta: { quote: quote } }, { done: true, reply: "answer" }]);
assert(early && early.quote && early.quote.price === 4171.7, "meta before done");
const preview = ctx.fe77_quotePreview(early);
assert(preview.indexOf("4,171.70") >= 0, "thousands");
assert(preview.indexOf("11:57:00 UK") >= 0, "as of on quote line");
const doneOnly = play([{ done: true, reply: "answer", meta: { quote: { price: 10, asOfUk: "12:01:00 UK" } } }]);
assert(doneOnly.quote.price === 10, "done only meta");
const none = play([{ t: "hello" }, { done: true, reply: "answer" }]);
assert(none == null, "no meta");
const both = play([
  { meta: { quote: { price: 1 } } },
  { done: true, meta: { quote: { price: 2 } } }
]);
assert(both.quote.price === 2, "done meta wins");

assert(ctx.fe77_freshWord(0, "live") === "LIVE", "fresh live");
assert(ctx.fe77_freshWord(1, "live") === "delayed 1 min", "fresh delay");
assert(ctx.fe77_freshWord(1, "closed") === "", "fresh closed stays");
assert(ctx.fe77_fxKey("USDJPY=X") === "USDJPY", "usdjpy yahoo");
assert(ctx.fe77_fxKey("JPY=X") === "USDJPY", "jpy yahoo");
assert(ctx.fe77_fxKey("EURUSD=X") === "EURUSD", "eur yahoo");
assert(ctx.fe77_fxKey("USDJPY") === "USDJPY", "usdjpy bare");
assert(ctx.fe77_dayPart(15) === "Afternoon", "afternoon");
assert(ctx.fe77_dayPart(9) === "Morning", "morning");
assert(ctx.fe77_briefTitle(null, 15) === "Afternoon brief", "brief fallback");
assert(ctx.fe77_briefTitle({ label: "London close" }, 15) === "London close", "brief label");
assert(ctx.fe77_futText({ futuresChange: { text: "gold futures (GC=F) +0.14% today" } }) === "gold futures (GC=F) +0.14% today", "futures text");
assert(ctx.fe77_futText({ futures: { changePct: 0.08 } }).indexOf("+0.08%") > 0, "futures pct");
assert(ctx.fe77_dxyTitle(true, false, "US Dollar Index (ICE, Yahoo DX-Y.NYB)") === "US Dollar Index (ICE, Yahoo DX-Y.NYB)", "dxy ice");
assert(ctx.fe77_dxyTitle(false, true, "") === "Dispatch FX basket", "dxy fallback");
assert(ctx.fe77_dxyTitle(false, false, "") === "Dispatch FX basket", "dxy computed");

assert(app.indexOf('_openResearchAssistant("What matters most in markets right now?")') < 0, "no canned prefill");
assert(app.indexOf("fe69_askCard") > 0, "pulse helper remains");
var pulse = app.slice(app.indexOf("function fe69_askCard"), app.indexOf("function fe69_regimeAi"));
assert(pulse.indexOf("sendChatMessage") < 0, "pulse does not send");
var chip = app.slice(app.indexOf("function _chatChipIdx"), app.indexOf("async function sendChatMessage"));
assert(chip.indexOf("sendChatMessage()") < 0, "chips do not send");
var follow = app.slice(app.indexOf("function _chatAskFollowUp"), app.indexOf("function _renderBotMsg"));
assert(follow.indexOf("sendChatMessage()") < 0, "follow-ups do not send");
assert(app.indexOf('if (t === "chat") { toggleChat(); const inp = document.getElementById("chatInp"); if (inp && v) { inp.value = v; sendChatMessage();') < 0, "chat action does not send");
assert(app.indexOf("function fe77_chatWipeAll(") === app.lastIndexOf("function fe77_chatWipeAll("), "one wipe");

assert(ctx.fe77_fxPair("TNX") === "", "tnx is not fx");
assert(ctx.fe77_fxPair("DXY") === "", "dxy is not fx");
assert(ctx.fe77_fxPair("EURUSD") === "EURUSD", "eur pair");
assert(ctx.fe77_fxPair("USDJPY") === "USDJPY", "jpy pair");
assert(ctx.fe77_pxText("TNX", 5.1) === "5.10%", "us10 2dp");
assert(ctx.fe77_pxText("^TYX", 4.5) === "4.50%", "us30 2dp");
assert(ctx.fe77_pxText("US2Y", 4.25) === "4.25%", "us2 2dp");
assert(ctx.fe77_pxText("DFII10", 1.8) === "1.80%", "real yield 2dp");
assert(ctx.fe77_pxText("GILT", 4.2) === "4.20%", "gilt 2dp");
assert(ctx.fe77_pxText("BUND", 2.4) === "2.40%", "bund 2dp");
assert(ctx.fe77_pxText("JGB", 0.85) === "0.85%", "jgb 2dp");
assert(ctx.fe77_pxText("SONIA", 4) === "4.00%", "policy 2dp");
assert(ctx.fe77_pxText("EURUSD", 1.1212) === "1.1212", "fx 4dp");
assert(ctx.fe77_pxText("USDJPY", 154.32) === "154.32", "jpy 2dp");
assert(ctx.fe77_pxText("GBPJPY", 190.5) === "190.50", "gbpjpy 2dp");
assert(ctx.fe77_pxText("DXY", 104.25) === "104.25", "dxy 2dp");
assert(ctx.fe77_pxText("AAPL", 227.4) === "227.40", "stock 2dp");
assert(ctx.fe77_pxText("VIX", 18.4) === "18.40", "vix 2dp");
assert(ctx.fe77_kicker("Afternoon stance: Defensive (brief for 2026-10-19) · Mon 19 Oct") === "Afternoon stance: Defensive · Mon 19 Oct", "kicker iso");
assert(ctx.fe77_kicker("AFTERNOON STANCE: DEFENSIVE (BRIEF FOR 2026-10-19) · MON 19 OCT") === "AFTERNOON STANCE: DEFENSIVE · MON 19 OCT", "kicker upper");
assert(app.indexOf("(brief for ${b.date})") < 0, "brief for source gone");
assert(app.indexOf('TICKER_CATS[tk]==="fx"') < 0, "old fx4 gate gone");

const cats = app.match(/const TICKER_CATS=\{[\s\S]*?\};/);
assert(cats, "ticker cats present");
const table = [];
const bad = [];
vm.runInContext("var TICKER_CATS=" + cats[0].replace(/^const TICKER_CATS=/, "").replace(/;$/, ""), ctx);
Object.keys(ctx.TICKER_CATS).forEach(function (tk) {
  const cat = ctx.TICKER_CATS[tk];
  const yieldTk = ctx.fe77_isYield(tk);
  const pair = ctx.fe77_fxPair(tk);
  const sample = yieldTk ? 5.1 : (pair ? (pair.indexOf("JPY") >= 0 ? 154.32 : 1.1212) : 100.5);
  const text = ctx.fe77_pxText(tk, sample);
  const dp = yieldTk ? 2 : pair ? (pair.indexOf("JPY") >= 0 ? 2 : 4) : 2;
  const frac = (String(text).match(/\.(\d+)/) || ["", ""])[1];
  table.push(tk + " " + cat + " " + text + " dp" + frac.length);
  if (frac.length !== dp) bad.push(tk + " got " + text + " want " + dp);
  if (yieldTk && text.slice(-1) !== "%") bad.push(tk + " missing %");
  if (!yieldTk && !pair && /\d\.\d{4}/.test(text)) bad.push(tk + " leaked 4dp " + text);
});
assert(!bad.length, "built-in dp " + bad.join("; "));
console.log("dp table " + table.length + " instruments");

console.log("fe77 tests passed");
