#!/usr/bin/env node
"use strict";
/* Mocked quotes for a closed previous-close print.
   0700.HK is the live holiday payload. BP.L is GBp (pence). 7203.T is JPY.
   A zero change is a last close, never NO SYNC. Regime fit is not the AI score. */
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt56/in/app.js";
const src = fs.readFileSync(appPath, "utf8");
const at = src.indexOf("// fe66-pure-begin");
const end = src.indexOf("// fe66-pure-end");
if (at < 0 || end < 0) throw new Error("missing fe66 helpers");

const HK_NOTE = "Hong Kong market closed (day after Chung Yeung) · opens Tue 02:30 UK";
const BP_NOTE = "London market closed · opens 08:00 UK";
const T_NOTE = "Tokyo market closed · opens 04:30 UK";
const HK = { p: 417.8, prev: 417.8, c: 0, currency: "HKD", basis: "previous_close", status: "closed", stale: false, nextOpen: "2026-10-20T01:30Z", note: HK_NOTE, ts: 1792138094 };
const BP = { p: 614.1, prev: 610.5, c: 0.5896805896805934, currency: "GBp", basis: "previous_close", status: "closed", stale: false, nextOpen: "2026-10-19T07:00:00.000Z", note: BP_NOTE, ts: 1792167300 };
const T = { p: 3089, prev: 3094, c: -0.16160310277957335, currency: "JPY", basis: "previous_close", status: "closed", stale: false, nextOpen: "2026-10-19T03:30:00.000Z", note: T_NOTE, ts: 1792377000 };

const ctx = {
  A: [
    { tk: "0700.HK", ex: "HKEX", cat: "Stock", _rt43: true },
    { tk: "BP.L", ex: "LSE", cat: "Stock", _rt43: true },
    { tk: "7203.T", ex: "TSE", cat: "Stock", _rt43: true },
    { tk: "MU", ex: "NASDAQ", cat: "Stock" }
  ],
  P: {},
  BASE: {},
  liveQuoteTs: {},
  bags: {},
  RT43_CUR: { "0700.HK": "HKD", "BP.L": "GBp", "7203.T": "JPY" },
  fe64_yqBag: tk => ctx.bags[tk] || null,
  hasSyncedQuote: () => true,
  liveChg: tk => (ctx.P[tk] ? ctx.P[tk].c : null),
  _rt18MarketOpen: tk => tk === "0700.HK",
  _rt18MarketOpenAt: (tk, d) => {
    const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Hong_Kong", weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d);
    const wd = parts.find(p => p.type === "weekday").value;
    const hh = Number(parts.find(p => p.type === "hour").value);
    const mm = Number(parts.find(p => p.type === "minute").value);
    const m = hh * 60 + mm;
    if (wd === "Sat" || wd === "Sun") return false;
    if (m >= 720 && m < 780) return false;
    return m >= 570 && m < 960;
  },
  _rt22NoSync: () => "Syncing…",
  _rt26Day: () => "today",
  fe65_feedLbl: d => (!d || d.status === "unavailable" ? "NO SYNC" : d.status || "")
};
vm.createContext(ctx);
vm.runInContext(src.slice(at, end), ctx);

let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("ok", msg);
  else { failed++; console.error("FAIL", msg); }
}

ok(ctx.fe66_pick({ "0700.HK": HK }, "0700.HK", "0700.HK").p === 417.8, "keyed payload");
ok(ctx.fe66_pick(HK, "0700.HK", "0700.HK").note === HK_NOTE, "flat payload keeps the note");
ok(ctx.fe66_pick(HK, "0700.HK", "0700.HK").c === 0, "zero change is kept");
ok(ctx.fe66_pick(HK, "0700.HK", "0700.HK").basis === "previous_close", "previous_close basis is kept");

ctx.fe66_setCcy("0700.HK", HK.currency);
ctx.fe66_setCcy("BP.L", BP.currency);
ctx.fe66_setCcy("7203.T", T.currency);
ctx.fe66_setBasis("0700.HK", HK.basis);
ok(ctx.fe66_money("0700.HK", 417.8) === "HK$417.80", "HKD");
ok(ctx.fe66_money("0700.HK", 420.8) === "HK$420.80" && ctx.fe66_money("0700.HK", 415.8) === "HK$415.80", "chart high low in HK$");
ok(ctx.fe66_money("BP.L", 614.1) === "614.10p", "LSE pence, not pounds");
ok(ctx.fe66_money("7203.T", 3089) === "¥3,089", "yen");
ok(!ctx.fe66_money("BP.L", 614.1).includes("£") && !ctx.fe66_money("BP.L", 614.1).includes("$"), "pence has no dollar or pound sign");

ok(ctx.fe66_pct(0) === "+0.00 (0.00%)", "zero change text");
ok(ctx.fe66_pct(BP.c).startsWith("+0.59"), "BP change");
ok(ctx.fe66_pct(T.c) === "-0.16 (-0.16%)", "Toyota change");

ctx.P["0700.HK"] = { p: 417.8, c: 0 };
ctx.bags["0700.HK"] = { status: "closed", note: HK_NOTE, nextOpen: HK.nextOpen };
ctx.liveQuoteTs["0700.HK"] = HK.ts;
const hkLine = ctx.fe66_chgLine("0700.HK", { status: "closed" }, false);
ok(ctx.fe66_priceLine("0700.HK", { status: "closed" }, false) === "HK$417.80", "headline price");
ok(hkLine.startsWith("Last close · +0.00 (0.00%)"), "labelled last close with a zero change: " + hkLine);
ok(hkLine.endsWith(HK_NOTE), "server note verbatim");
ok(hkLine.indexOf("NO SYNC") < 0 && hkLine.indexOf("awaiting feed") < 0 && hkLine.indexOf("Syncing") < 0, "closed quote is not NO SYNC");
ok(ctx.fe66_feedLbl({ status: "unavailable" }, "0700.HK") === HK_NOTE, "header uses the note, not NO SYNC");
ok(ctx.fe66_chartBit("0700.HK", "1d", { status: "closed" }, "", "Syncing…") === "Last session · Fri", "holiday chart label is Friday");

ctx.P["BP.L"] = { p: 614.1, c: +BP.c.toFixed(2) };
ctx.bags["BP.L"] = { status: "closed", note: BP_NOTE };
ctx.liveQuoteTs["BP.L"] = BP.ts;
ctx._rt18MarketOpen = () => false;
ok(ctx.fe66_priceLine("BP.L", { status: "closed" }, false) === "614.10p", "BP price in pence");
ok(ctx.fe66_chgLine("BP.L", { status: "closed" }, false).indexOf(BP_NOTE) > 0, "BP note");
ok(ctx.fe66_chartBit("BP.L", "1d", { status: "closed" }, "", "Syncing…") === "Last session · Fri", "LSE last session Friday");
ok(ctx.fe66_dynHead("BP.L") === "Last session · Fri", "dynamic lookup chart label");
ok(ctx.fe66_money("BP.L", 610.5) === "610.50p", "previous close stays in pence");

ctx.P["7203.T"] = { p: 3089, c: +T.c.toFixed(2) };
ctx.bags["7203.T"] = { status: "closed", note: T_NOTE };
ctx.liveQuoteTs["7203.T"] = T.ts;
ok(ctx.fe66_priceLine("7203.T", { status: "closed" }, false) === "¥3,089", "Toyota price");
ok(ctx.fe66_chgLine("7203.T", { status: "closed" }, true).indexOf("Last close") === 0, "closed even when the caller said unavailable");
ok(ctx.fe66_chgLine("7203.T", { status: "closed" }, true).indexOf(T_NOTE) > 0, "Tokyo note");
ok(ctx.fe66_chartBit("7203.T", "1d", { status: "closed" }, "", "Syncing…") === "Last session · Mon", "Tokyo last session Monday");
ctx._rt18MarketOpen = () => true;
ok(ctx.fe66_chartBit("7203.T", "1d", { status: "closed" }, "", "Syncing…") === "Last session · Mon", "lunch print stays Monday while the afternoon session is open");
ok(ctx.fe66_chartBit("0700.HK", "1d", { status: "closed" }, "", "Syncing…") === "Last session · Fri", "holiday print stays Friday while the calendar says open");

const ask = "Enter a market symbol such as MU. No score is shown rather than a guessed one.";
ok(ctx.fe66_fitSub("0700.HK", { state: "null", reason: ask }) === "Fit score covers US-listed stocks for now.", "HK regime empty state");
ok(ctx.fe66_fitSub("BP.L", { state: "null", reason: ask }) === "Fit score covers US-listed stocks for now.", "LSE regime empty state");
ok(ctx.fe66_fitSub("7203.T", { state: "null", reason: ask }) === "Fit score covers US-listed stocks for now.", "TSE regime empty state");
ok(ctx.fe66_fitSub("0700.HK", { state: "null", reason: "Listed outside the US coverage set." }) === "Listed outside the US coverage set.", "plain server reason is kept");
ok(ctx.fe66_fitSub("MU", { state: "score", reason: "Headwind, 28 out of 100, while the market mood is Risk-Off." }).indexOf("Headwind") === 0, "US reason stays");
ok(ctx.fe66_fitSub("0700.HK", { state: "null", reason: ask }).indexOf("No score") < 0, "empty state does not say no score");

ok(src.indexOf('app.js?v=chat67"') >= 0 || /app\.js\?v=chat67/.test(fs.readFileSync(appPath.replace(/app\.js$/, "index.html"), "utf8")), "cache bust chat67");
ok(src.indexOf(">AI score <") >= 0 && src.indexOf(">Regime fit<") >= 0, "the two scores are labelled differently");
ok(src.indexOf("fe66_money(tk, v)") >= 0, "chart footer uses the quote currency");
ok(src.indexOf('fe66_pick(data, yhSym, tk)') >= 0, "yahoo chunk uses the flat-or-keyed pick");
ok(src.indexOf("fe66_money(_dynTk, d.prev)") >= 0, "dynamic previous close uses the quote currency");
ok(src.indexOf("fe66_chgLine(_dynTk") >= 0, "dynamic change line uses last close");
ok(src.indexOf("Object.assign({}, priceInfo") >= 0, "lookup keeps currency and basis");

if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("rt56 fixture passed");
