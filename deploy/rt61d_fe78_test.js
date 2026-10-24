#!/usr/bin/env node
"use strict";
var fs = require("fs");
var vm = require("vm");
var src = fs.readFileSync(process.argv[2], "utf8");
var a = src.indexOf("// FE78_PURE_START");
var b = src.indexOf("// FE78_PURE_END");
if (a < 0 || b < 0) throw new Error("pure block missing");
var ctx = {};
vm.createContext(ctx);
vm.runInContext(src.slice(a, b), ctx);
function eq(got, want, label) {
  if (got !== want) throw new Error(label + " got " + JSON.stringify(got) + " want " + JSON.stringify(want));
}
var NVDA = "AI infrastructure spend accelerating. Data center revenue dominant. TSMC Q1 confirms demand strength. Elevated valuation justified by 90%+ growth.";
if (src.indexOf(NVDA) >= 0) throw new Error("old NVDA thesis still in output");
if (src.indexOf("// ── rt61d ──") < 0) throw new Error("marker missing");

eq(ctx.fe78_about({ th: NVDA }), "", "opinion dropped");
eq(ctx.fe78_about({ th: "" }), "", "empty th");
eq(ctx.fe78_about({}), "", "missing th");
eq(ctx.fe78_about({ th: undefined }), "", "undefined th");
eq(ctx.fe78_about({ th: "NVIDIA (NVDA) is a Stock listed on NASDAQ. Source: the desk instrument table." }),
  "NVIDIA (NVDA) is a Stock listed on NASDAQ. Source: the desk instrument table.", "factual kept");

var srv = ctx.fe78_cryptoBasis({ baseline: "24h", changePct: 1.21, prev: 80000, p: 90000, c: 99 }, { prev: 1, at: 0, kind: "cg", c: 5 }, 1000);
eq(srv.mode, "srv", "server baseline mode");
eq(srv.c, 1.21, "server change kept");
eq(srv.kind, "srv24", "srv24 kind");
var client = ctx.fe78_cryptoBasis({ c: 2, p: 10, basis: "rolling_24h", prev: 9 }, null, 1000);
eq(client.mode, "client", "no server baseline");
var keep = ctx.fe78_cryptoBasis({ c: 4.5, p: 10, source: "coingecko" }, { kind: "srv24", c: 1.21, prev: 80000, at: 1000 }, 2000);
eq(keep.mode, "keep", "client quote does not replace srv24");
eq(keep.c, 1.21, "kept server change");

ctx.fe78_meta.BTC = { baseline: "24h" };
eq(ctx.fe78_chgText("BTC", "+1.21%"), "+1.21% 24h", "btc 24h");
eq(ctx.fe78_chgText("ETH", "+0.50%"), "+0.50% 24h", "eth 24h without bag");
eq(ctx.fe78_chgText("BTC", "+0.00%"), "—", "no zero");
eq(ctx.fe78_chgText("BTC", "+1.21% 24h"), "+1.21% 24h", "no double 24h");
delete ctx.fe78_meta.AAPL;
eq(ctx.fe78_chgText("AAPL", "+0.40%"), "+0.40%", "stock without fields");
ctx.fe78_take("AAPL", { changeDay: "Fri", prevNote: "vs Fri close" });
eq(ctx.fe78_chgText("AAPL", "+0.40%"), "+0.40% Fri · vs Fri close", "changeDay and prevNote");
eq(ctx.fe78_chgHtml("AAPL", "+0.40%").indexOf('class="fe78-note"') > 0, true, "muted note");
ctx.fe78_take("MSFT", {});
eq(ctx.fe78_chgText("MSFT", "+0.10%"), "+0.10%", "take without fields");
ctx.fe78_take("NVDA", { changeDay: "Fri", prevNote: "vs Fri close", feedLabel: "Yahoo Finance" });
eq(ctx.fe78_bag("NVDA").feedLabel, "Yahoo Finance", "feedLabel stored");
eq(ctx.fe78_badgeText("Yahoo Finance", null), "Yahoo Finance", "badge with feedLabel");
eq(ctx.fe78_badgeText("", { status: "live" }), "", "badge without feedLabel");
eq(ctx.fe78_badgeText(null, null), "", "badge absent");

eq(ctx.fe78_quoteLabel({ symbol: "NVDA", label: "NVIDIA" }, "NVIDIA"), "NVIDIA", "quote label");
eq(ctx.fe78_quoteLabel({ symbol: "EURUSD", label: "EUR/USD" }, "EURUSD"), "EUR/USD", "fx label");
eq(ctx.fe78_quoteLabel({ symbol: "NVDA", label: "Gold spot" }, "NVIDIA"), "NVIDIA", "stale gold ignored");
eq(ctx.fe78_quoteLabel({ symbol: "NVDA" }, "NVIDIA"), "NVIDIA", "display name fallback");
eq(ctx.fe78_quoteLabel({ symbol: "XAU", label: "Gold spot" }, ""), "Gold spot", "gold keeps its label");
eq(ctx.fe78_quoteLabel({ symbol: "AAPL" }, ""), "AAPL", "symbol fallback");
var line = ctx.fe78_quoteLine({ quote: { symbol: "NVDA", label: "NVIDIA", price: 131.4, changePct: 0.8, changeDay: "Fri", prevNote: "vs Fri close" } }, "NVIDIA");
if (line.indexOf("NVIDIA") < 0 || line.indexOf("Gold spot") >= 0) throw new Error("quote line " + line);
if (line.indexOf("Fri") < 0 || line.indexOf("vs Fri close") < 0) throw new Error("quote note " + line);

var full = ctx.fe78_briefBits({ label: "Mon 19 Oct · Afternoon edition", dayLabel: "Mon 19 Oct", name: "Afternoon" });
eq(full.text, "Mon 19 Oct · Afternoon edition", "brief label");
eq(full.dayLabel, "Mon 19 Oct", "brief day");
eq(full.name, "Afternoon", "brief name");
var parts = ctx.fe78_briefBits({ dayLabel: "Mon 19 Oct", name: "Evening" });
eq(parts.text, "Mon 19 Oct · Evening", "brief day and name");
eq(ctx.fe78_briefBits({}).text, "", "brief absent");
eq(ctx.fe78_briefBits(null).text, "", "brief null");

eq(ctx.fe78_sourceTitle({ title: "Dispatch regime model · Regime model (The Dispatch)", label: "Regime model", name: "regime" }),
  "Dispatch regime model · Regime model (The Dispatch)", "source title");
eq(ctx.fe78_sourceTitle({ label: "Yahoo Finance", name: "Yahoo" }), "Yahoo Finance", "source label");
eq(ctx.fe78_sourceTitle({ name: "Yahoo Finance" }), "Yahoo Finance", "source name");
eq(ctx.fe78_sourceTitle(null), "", "source absent");
eq(ctx.fe78_sourceTitle("SEC EDGAR"), "SEC EDGAR", "source string");

ctx.fe78_take("0700.HK", { changeDay: "Fri", prevNote: "vs Fri close" });
eq(ctx.fe78_chgText("0700.HK", "+0.40% Mon"), "+0.40% Fri · vs Fri close", "change day replaces Mon");
eq(ctx.fe78_chgText("0700.HK", "+0.40% Fri"), "+0.40% Fri · vs Fri close", "server day kept");
eq(ctx.fe78_chgText("0700.HK", "+0.40% Fri 16 Oct"), "+0.40% Fri · vs Fri close", "date fragment dropped");
eq(ctx.fe78_chgText("0700.HK", "\u2191 +HK$5.20 (+1.26%) Mon \u00b7 Hong Kong market closed"), "\u2191 +HK$5.20 (+1.26%) Fri \u00b7 vs Fri close", "status not glued to change");
eq(ctx.fe78_tidyStatus("STOCK \u00b7 HKEX \u00b7 Last close", "0700.HK", "2026-10-20T01:30:00Z"), "Hong Kong market closed \u00b7 opens Tue 20 Oct, 02:30 UK", "closed status replaces category");
ctx.fe78_take("BTC", { baseline: "24h", changePct: 1.21, c: 1.21 });
eq(ctx.fe78_cryptoLine("BTC", 82477.55).indexOf("(+1.21%) 24h") > 0, true, "server 24h change");
eq(ctx.fe78_closedLine("0700.HK", "2026-10-20T01:30:00Z"), "Hong Kong market closed · opens Tue 20 Oct, 02:30 UK", "hk closed line");
eq(ctx.fe78_closedLine("7203.T", "2026-10-20T00:00:00Z").indexOf("Tokyo market closed · opens") === 0, true, "tokyo closed");
eq(ctx.fe78_closedLine("600519.SS", "").indexOf("Shanghai market closed") === 0, true, "shanghai closed");
eq(ctx.fe78_tidyStatus("opens 02:30 UK Fri 16 Oct", "0700.HK", "2026-10-20T01:30:00Z"), "Hong Kong market closed · opens Tue 20 Oct, 02:30 UK", "dangling date replaced");
eq(ctx.fe78_tidyStatus("Last session · Fri 16 Oct", "", ""), "Last session · Fri 16 Oct", "open status left alone");
eq(ctx.fe78_askPrefill("MU — Neutral"), "What matters most for MU right now?", "prefill drops stance");
eq(ctx.fe78_askPrefill("Micron Technology — Neutral fit"), "What matters most for Micron Technology right now?", "prefill name");
eq(ctx.fe78_askPrefill("Bullish"), "What matters most in markets right now?", "stance only");
eq(ctx.fe78_askPrefill(""), "What matters most in markets right now?", "empty prefill");
eq(ctx.fe78_dxyLabel("US Dollar Index (ICE, Yahoo DX-Y.NYB)", true, false), "US Dollar Index (ICE)", "long dxy dropped");
eq(ctx.fe78_dxyLabel("US Dollar Index (computed from live FX)", true, false), "US Dollar Index (ICE)", "computed dxy dropped");
eq(ctx.fe78_dxyLabel("US Dollar Index (ICE)", true, false), "US Dollar Index (ICE)", "matching server label");
eq(ctx.fe78_dxyLabel("US Dollar Index (ICE)", false, true), "Dispatch FX basket", "dxy fallback");
eq(ctx.fe78_deskScore(78), "Desk score 78/100", "desk score");
eq(ctx.fe78_deskScore(null), "", "desk score missing");
eq(ctx.fe78_zeroish("$0.00"), true, "zero price");
eq(ctx.fe78_zeroish("+$1.21 (1.21%)"), false, "real change");
eq(ctx.fe78_zeroish("+0.00%"), true, "zero percent");
eq(ctx.fe78_zeroish("$0.00 (+0.00%)"), true, "zero pair");
eq(ctx.fe78_skel().indexOf("fe78-skel") > 0, true, "skeleton");
if (src.indexOf("HIGH DESK SCORE") >= 0) throw new Error("high desk score remains");
if (src.indexOf("US Dollar Index (computed from live FX)") >= 0) throw new Error("computed dxy remains");
if (src.indexOf("US Dollar Index (ICE, Yahoo DX-Y.NYB)") >= 0) throw new Error("long dxy remains");
if (src.indexOf('baseline === "24h"') < 0 && src.indexOf("q.baseline === \"24h\"") < 0) throw new Error("baseline hook missing");
if (src.indexOf("fe78_cryptoBasis") < 0) throw new Error("basis helper missing");
if (src.indexOf("Platform thesis: ${a.th || \"None\"}") >= 0) throw new Error("empty thesis heading remains");

eq(ctx.fe78_quoteLine({ quote: { quoteLine: "Micron Technology $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK" } }),
  "Micron Technology $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK", "verbatim quote line");
eq(ctx.fe78_quoteLine({ quote: { symbol: "MU", label: "Micron Technology", price: 909.09, change: 30.25, changePct: 3.44, asOfUk: "Mon 19 Oct, 14:40 UK" } }, "MU"),
  "Micron Technology $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK", "built MU quote");
eq(ctx.fe78_quoteLine({ quote: { symbol: "XAU", label: "Gold spot", price: 4171.7, change: 11.6, changePct: 0.28, asOfUk: "Mon 19 Oct, 11:57 UK" } }),
  "Gold spot $4,171.70 +11.60 (+0.28%) · Mon 19 Oct, 11:57 UK", "gold quote built");
eq(ctx.fe78_quoteLine({}), "", "no quote");
eq(ctx.fe78_quoteLine({ provider: "mock" }), "", "meta without quote");
var todayNote = ctx.fe78_academyNote({ edition: "today", label: "Today's practice set", dateLabel: "Mon 19 Oct", nextRunUk: "07:00 UK", stale: false }, "2026-10-19");
eq(todayNote.amber, false, "today note neutral");
if (todayNote.text.indexOf("Today's practice set") < 0 || todayNote.text.indexOf("Mon 19 Oct") < 0 || todayNote.text.indexOf("Next set due 07:00 UK") < 0) throw new Error("today note " + todayNote.text);
var yest = ctx.fe78_academyNote({ edition: "yesterday", label: "Yesterday's practice set", dateLabel: "Sun 18 Oct", nextRunUk: "07:00", stale: false }, "2026-10-19");
eq(yest.amber, false, "yesterday neutral");
if (yest.text.indexOf("Yesterday's practice set") < 0 || yest.text.indexOf("Next set due 07:00 UK") < 0) throw new Error("yesterday note " + yest.text);
var older = ctx.fe78_academyNote({ edition: "older", label: "An earlier practice set", dateLabel: "Fri 16 Oct", nextRunUk: "Tue 07:00 UK", stale: true }, "2026-10-19");
eq(older.amber, true, "older stale amber");
if (older.text.indexOf("An earlier practice set") < 0 || older.text.indexOf("Fri 16 Oct") < 0) throw new Error("older note " + older.text);
eq(ctx.fe78_academyNote({ date: "2026-10-19", items: [] }, "2026-10-19"), null, "old server today has no note");
eq(ctx.fe78_academyNote({ date: "2026-10-16", items: [{}] }, "2026-10-19").text, "From 2026-10-16", "old server from date");
eq(ctx.fe78_academyKeep({ items: [{}] }), true, "keep a valid set");
eq(ctx.fe78_academyKeep({ date: "2026-10-16" }), false, "no items");
var srv = ctx.fe78_regimeFrom({ regime: "Risk-On (Fragile)", score: 61, asOf: "2026-10-19T13:40:00Z", asOfUk: "Mon 19 Oct, 14:40 UK" }, { label: "Transition", score: 48, loading: false });
eq(srv.label, "Risk-On (Fragile)", "server regime label");
eq(srv.score, 61, "server regime score");
eq(srv.localEstimate, false, "server not local");
if (ctx.fe78_regimeTitle(srv).indexOf("Mon 19 Oct, 14:40 UK") < 0) throw new Error("regime title " + ctx.fe78_regimeTitle(srv));
var local = ctx.fe78_regimeFrom(null, { label: "Transition", score: 48, loading: false });
eq(local.localEstimate, true, "local estimate flag");
if (local.label.indexOf("Dispatch local estimate") < 0) throw new Error("local label " + local.label);
var loading = ctx.fe78_regimeFrom(null, { label: "Regime: loading…", score: 50, loading: true });
eq(loading.loading, true, "loading stays");
eq(loading.localEstimate, undefined, "loading is not an estimate");
if (ctx.fe78_regimeSub(srv).indexOf("Mon 19 Oct, 14:40 UK") < 0) throw new Error("regime sub " + ctx.fe78_regimeSub(srv));

console.log("fe78 tests passed");
