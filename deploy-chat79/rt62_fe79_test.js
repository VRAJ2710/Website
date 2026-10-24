#!/usr/bin/env node
"use strict";
var fs = require("fs");
var vm = require("vm");
var src = fs.readFileSync(process.argv[2], "utf8");
var a = src.indexOf("// FE79_PURE_START");
var b = src.indexOf("// FE79_PURE_END");
if (a < 0 || b < 0) throw new Error("pure block missing");
var ctx = {};
vm.createContext(ctx);
vm.runInContext(src.slice(a, b), ctx);
function eq(got, want, label) {
  if (got !== want) throw new Error(label + " got " + JSON.stringify(got) + " want " + JSON.stringify(want));
}
if (src.indexOf("// ── rt62 ──") < 0) throw new Error("marker missing");

var up = ctx.fe79_surfaces(82000, 80000, -9);
["home", "crypto", "tape", "market", "phone", "list", "lens", "signal", "ask"].forEach(function (k) {
  eq(up[k], "2.50", "surface " + k + " up");
});
var dn = ctx.fe79_surfaces(79000, 80000, 4);
["home", "crypto", "tape", "market", "phone", "list", "lens", "signal", "ask"].forEach(function (k) {
  eq(dn[k], "-1.25", "surface " + k + " down");
});
eq(ctx.fe79_cryptoPct(100, null, -0.58), -0.58, "missing baseline uses server percent");
eq(ctx.fe79_cryptoPct(100, null, null), null, "missing baseline and server stays blank");
eq(ctx.fe79_cryptoPct(100, 100, -1.2), null, "flat baseline is not 0.00");
eq(ctx.fe79_pctHtml("BTC", 2.5), "+2.50% 24h", "24h label");
eq(ctx.fe79_pctHtml("BTC", 0), "—", "no zero percent");

eq(ctx.fe79_goldPct(null, null, false), null, "gold missing");
eq(ctx.fe79_goldPct(0, null, false), null, "gold fake zero");
eq(ctx.fe79_goldPct(-1.29, 0, true), -1.29, "gold uses ticker spot");
eq(ctx.fe79_moveText(null, false), "", "signal omits missing");
eq(ctx.fe79_moveText(0, false), "", "signal omits fake zero");
eq(ctx.fe79_moveText(0, true), "unchanged", "signal real zero");
eq(ctx.fe79_moveText(-1.29, true), "−1.29%", "signal real move");
eq(ctx.fe79_onePct("4.99%%"), "4.99%", "double percent");
eq(ctx.fe79_onePct("4.99%"), "4.99%", "single percent");

var rows = [
  { quote: true, crypto: true, open: false, fresh: false },
  { quote: true, crypto: false, open: true, fresh: true },
  { quote: true, crypto: false, open: false, fresh: false },
  { quote: false, crypto: true, open: true, fresh: true }
];
var box = ctx.fe79_count(rows);
eq(box.live, 2, "trading live includes 24/7");
eq(box.closed, 1, "trading closed");
eq(ctx.fe79_tradeLabel(box), ctx.fe79_tradeLabel(box), "label stable");
eq(ctx.fe79_tradeLabel(box), "2 trading now · 1 closed", "shared label");

var on = ctx.fe79_setRegime(null, { label: "Risk-On", score: 55, asOfUk: "Sat 24 Oct, 14:00 UK" });
var off = ctx.fe79_setRegime(on, { label: "Risk-Off", score: 37, asOfUk: "Sat 24 Oct, 14:05 UK" });
eq(off.label, "Risk-Off", "regime label");
eq(off.score, 37, "regime score");
eq(off.asOfUk, "Sat 24 Oct, 14:05 UK", "one as-of");

eq(ctx.fe79_goldChip({ symbol: "GC=F", source: "yahoo" }), "Gold futures (GC=F, delayed 10 min)", "futures chip");
eq(ctx.fe79_goldChip({ symbol: "XAU", source: "gold-api-spot-proxy" }), "Gold spot", "spot chip");
eq(ctx.fe79_goldChip({ symbol: "GOLD", name: "Gold" }), "Gold", "neutral gold");
if (ctx.fe79_goldChip({ symbol: "GC=F" }).indexOf("spot") >= 0) throw new Error("futures labelled spot");

var yest = ctx.fe79_academyNote({ edition: "yesterday", label: "Today's set", dateLabel: "Fri 23 Oct" }, "2026-10-24");
eq(yest.text, "Yesterday (Fri 23 Oct)", "yesterday set");
var today = ctx.fe79_academyNote({ edition: "today", label: "Today's set (Sat 24 Oct).", nextRunUk: "04:00 UK" }, "2026-10-24");
eq(today.text, "Today's set (Sat 24 Oct) · Next set due 04:00 UK", "no stray dot");
eq(ctx.fe79_academyNote({ date: "2026-10-22" }, "2026-10-24").text, "From Thu 22 Oct", "legacy date");
eq(ctx.fe79_stripUkDay("Hong Kong market closed · opens 01:30 UK Fri"), "Hong Kong market closed · opens 01:30 UK", "strip UK Fri");
eq(ctx.fe79_deskPhrase("Focus NVDA. Score 73"), "Focus NVDA. Desk score 73/100", "desk score");
eq(ctx.fe79_deskPhrase('<span class="desk-letter-tag">Score 55/100</span>'), '<span class="desk-letter-tag">Score 55/100</span>', "regime score kept");
eq(ctx.fe79_dxyPx("$104.20"), "104.20", "dxy dollar");
eq(ctx.fe79_catLabel("Index"), "Index", "index label");
eq(ctx.fe79_catLabel("Yield"), "Yield", "yield label");
eq(ctx.fe79_titleCaseIndex("US dollar index"), "US Dollar Index", "learn name");
eq(ctx.fe79_missing("null"), "Not available for this instrument", "null");
eq(ctx.fe79_missing("no price"), "Not available for this instrument", "no price");
eq(ctx.fe79_metricOk("Mkt Cap", "-"), false, "hide dash cap");
eq(ctx.fe79_metricOk("Mkt Cap", "$1.43T"), true, "show cap");
eq(ctx.fe79_metricOk("Beta", null), false, "hide null beta");
var hid = ctx.fe79_domCard("ETH", { a: "Bitcoin", tk: "BTC", cf: 68, tg: "Crypto" });
eq(hid, null, "hide btc card on eth");
var shown = ctx.fe79_domCard("BTC", { a: "Bitcoin", tk: "BTC", cf: 68, tg: "Crypto", dom: "68.0", asOf: "Sat 14:00 UK" });
eq(shown.a, "BTC dominance", "relabel dominance");
if (shown.x.indexOf("CoinGecko") < 0 || shown.x.indexOf("68.0") < 0) throw new Error("dominance source");

var coin = ctx.fe79_cryptoView({ px: 64200, baselinePrice: 64575, c: -0.58, changePct: -0.58, changeBasis: "rolling 24h", changeBasisLabel: "24h", price_change_percentage_24h: -1.55, changeSource: "coinbase" });
eq(coin.pct, -0.58, "server baseline not coingecko");
eq(coin.label, "24h", "server 24h label");
eq(coin.source, "server", "crypto server");
eq(coin.text, "-0.58% 24h", "crypto text");
var prev = ctx.fe79_cryptoView({ px: 100, baselinePrice: 101, c: -0.99, changeBasis: "previous close", changeBasisLabel: "previous close", price_change_percentage_24h: -4 });
eq(prev.label, "previous close", "previous close label");
eq(prev.text, "-0.99% previous close", "do not mix 24h");
var miss = ctx.fe79_cryptoView({ px: 100 });
eq(miss.source, "fallback", "crypto fallback");

var gNull = ctx.fe79_goldView({ displayChange: null, changeNote: "Change not published" });
eq(gNull.pct, null, "gold null pct");
eq(gNull.text, "Change not published", "gold note");
eq(gNull.unchanged, false, "missing gold is not unchanged");
if (/0\.00%|unchanged/.test(gNull.text)) throw new Error("null gold printed a zero");
var gFut = ctx.fe79_goldView({ displayChange: { pct: 0.4, instrument: "futures", symbol: "GC=F", label: "Gold futures (GC=F)", text: "+0.40%" } });
eq(gFut.label, "Gold futures (GC=F)", "futures label");
eq(gFut.text, "+0.40%", "futures text");
var gSpot = ctx.fe79_goldView({ displayChange: { pct: -1.29, instrument: "spot", symbol: "XAU", label: "Gold spot", text: "−1.29%" } });
eq(gSpot.pct, -1.29, "spot pct");
var gZero = ctx.fe79_goldView({ displayChange: { pct: 0, instrument: "spot", symbol: "XAU", label: "Gold spot" } });
eq(gZero.text, "unchanged", "real zero gold");
var gFall = ctx.fe79_goldView({ spot: -1.29, hasPrev: true });
eq(gFall.source, "fallback", "gold fallback");

var y = ctx.fe79_yieldView({ value: 4.99, unit: "percent", changePp: -0.02, changeBp: -2, source: "treasury" });
eq(y.text, "4.99%", "yield one percent");
eq(y.change, "-0.02 pp", "yield pp");
eq(y.source, "server", "yield server");
if (y.text.indexOf("%%") >= 0) throw new Error("yield double percent");
eq(ctx.fe79_yieldView({ fallback: "4.99%%" }).text, "4.99%", "yield fallback collapse");

var reg = ctx.fe79_regimeView({ regime: "Risk-On", label: "Risk-On", score: 55, computedAtUk: "Sat 24 Oct, 14:00 UK", thin: false, stale: true, inputs: { btcBasis: "rolling 24h" } });
eq(reg.source, "server", "regime server");
eq(reg.score, 55, "regime score field");
eq(reg.asOfUk, "Sat 24 Oct, 14:00 UK", "regime as-of");
if (reg.text.indexOf("stale") < 0) throw new Error("stale flag");
eq(ctx.fe79_regimeView({ available: false }).useLocal, true, "regime unavailable");
eq(ctx.fe79_regimeView(null).source, "fallback", "regime absent");

eq(ctx.fe79_mcapView({ marketCapText: "HKD 3.5tn" }).text, "HKD 3.5tn", "mcap text");
eq(ctx.fe79_mcapView({ marketCapText: "-" }).text, "", "mcap dash hidden");
eq(ctx.fe79_mcapView({}).source, "hidden", "mcap missing");

var sess = ctx.fe79_sessionView({ tradingNow: 1, closed: 12, total: 13, text: "1 of 13 markets trading now" }, { live: 9, closed: 1, priced: 1 });
eq(sess.text, "1 of 13 markets trading now", "session text");
eq(sess.source, "server", "session server");
eq(ctx.fe79_sessionView(null, box).source, "fallback", "session fallback");

var chip = ctx.fe79_askChip({ quote: { label: "Gold futures (GC=F, delayed 10 min)", price: "4007.90", time: "Sat 14:02 UK", instrument: "futures" } });
eq(chip.label, "Gold futures (GC=F, delayed 10 min)", "ask label exact");
eq(chip.source, "server", "ask server");
if (chip.line.indexOf("4007.90") < 0 || chip.line.indexOf("Sat 14:02 UK") < 0) throw new Error("ask price time");
eq(ctx.fe79_askChip({ quote: { symbol: "XAU", source: "gold-api-spot-proxy" } }).source, "fallback", "ask fallback");

var missRow = ctx.fe79_deskRow({ ticker: "TNX" }, [{ ticker: "TNX", reason: "Not available for this instrument" }]);
eq(missRow.text, "Not available for this instrument", "missing reason");
var noBeta = ctx.fe79_deskRow({ ticker: "DXY", price: 104.25 }, []);
eq(noBeta.showBeta, false, "beta omitted");
var withBeta = ctx.fe79_deskRow({ ticker: "BTC", price: 64200, beta: 1.85 }, []);
eq(withBeta.showBeta, true, "sourced beta");

var fin = ctx.fe79_finView({ valuation: { dividend: { forwardYieldPct: 0.03, trailingYieldPct: 0.02, basis: "forward annual" }, hidden: [{ field: "pb", reason: "not sourced" }] }, epsTtm: 2.54, peBasis: "TTM", epsNotes: ["EPS is GAAP trailing twelve months."] });
eq(fin.source, "server", "fin server");
eq(fin.hidden.pb, "not sourced", "hidden field");
eq(fin.peBasis, "TTM", "pe basis");
eq(fin.notes[0], "EPS is GAAP trailing twelve months.", "eps note");
eq(ctx.fe79_finView({}).source, "fallback", "fin fallback");

eq(ctx.fe79_aboutText({ about: "NVIDIA designs GPUs.", th: "NVIDIA (NVDA) is a Stock listed on NASDAQ. Source: the desk instrument table." }).text, "NVIDIA designs GPUs.", "about wins");
eq(ctx.fe79_aboutText({ th: "NVIDIA (NVDA) is a Stock listed on NASDAQ. Source: the desk instrument table." }).text, "", "placeholder hidden");
eq(ctx.fe79_aboutText({ th: "Yahoo description of the company." }).source, "fallback", "th fallback");
eq(ctx.fe79_natgas().id, "natgas", "natgas id");
eq(ctx.fe79_natgas().phrase, "natural gas prices", "natgas phrase");

if (src.indexOf('cat:"Yield"') < 0 && src.indexOf("cat: \"Index\"") < 0) throw new Error("category anchors missing");
if (src.indexOf("natgas: 'natural gas prices'") < 0) throw new Error("natgas missing");
console.log("fe79 tests ok");
