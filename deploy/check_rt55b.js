#!/usr/bin/env node
"use strict";
/* Closed venue chart copy uses the status note, then nextOpen, then the calendar.
   An open venue keeps the plain history sentence. The chunk join is untouched. */
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt55b/out/app.js";
const src = fs.readFileSync(appPath, "utf8");
const at = src.indexOf("function fe65b_openHm");
const end = src.indexOf("function fe65b_css");
if (at < 0 || end < 0) throw new Error("missing fe65b chart helpers");
const ctx = {
  A: [{ tk: "0700.HK", ex: "HKEX", cat: "Stock" }, { tk: "MU", ex: "NASDAQ", cat: "Stock" }],
  _rt39Ex: a => a.ex,
  fe64_yqBag: () => null,
  fe64_closedWords: bag => (bag && bag.note) || "",
  fe64_ukHm: ms => (ms === 1 ? "08:00" : ms ? "07:15" : ""),
  _rt51Next: () => 1,
  _rt18MarketOpen: tk => tk !== "COFFEE",
  fp: tk => Object.prototype.hasOwnProperty.call(ctx.QUOTES, tk) ? ctx.QUOTES[tk] : { status: "delayed" }
};
ctx.QUOTES = {};
vm.createContext(ctx);
vm.runInContext(src.slice(at, end), ctx);
let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("ok", msg);
  else { failed++; console.error("FAIL", msg); }
}
ctx.QUOTES["0700.HK"] = { status: "closed", fe64Note: "opens 06:00 UK" };
ok(ctx.fe65b_chartNote("0700.HK") === "Chart fills in when HKEX opens (06:00 UK).", "closed HK uses the status note");
ctx.QUOTES.MU = { status: "closed", fe64Note: "" };
ctx.fe64_yqBag = tk => tk === "MU" ? { status: "closed", note: "", nextOpen: 2 } : null;
ok(ctx.fe65b_chartNote("MU") === "Chart fills in when NASDAQ opens (07:15 UK).", "closed quote with no note uses nextOpen");
ctx.QUOTES.COFFEE = null;
ctx.fe64_yqBag = () => null;
ok(ctx.fe65b_chartNote("COFFEE") === "Chart fills in when the market opens (08:00 UK).", "missing status uses the venue calendar");
ctx.QUOTES.AAPL = { status: "delayed", fe64Note: "" };
ok(ctx.fe65b_chartNote("AAPL") === "Not enough price history yet for this chart. The latest price above is still live.", "open venue keeps the history sentence");
ok(src.indexOf("Dispatch and fallback market feeds returned insufficient history.") < 0, "old chart sentence is gone");
ok(src.indexOf(" · ETF proxy") < 0 && src.indexOf(" · tracked via an ETF") >= 0, "etf wording");
ok(src.indexOf("acc = fe64_joinChunk(acc, chunk)") >= 0, "chunk join call stays");
ok(src.indexOf("function fe64_joinChunk(acc, chunk)") >= 0 && src.indexOf("return String(acc == null ? \"\" : acc) + String(chunk == null ? \"\" : chunk);") >= 0, "join stays identity");
ok(/app\.js\?v=chat66/.test(fs.readFileSync(appPath.replace(/app\.js$/, "index.html"), "utf8")), "cache bust chat66");
["Dispatch and fallback", " · ETF proxy", "STALE·PROXY", "gold-api.com spot proxy", "Spot Gold proxy", "Synthetic DXY proxy", "Proxy reference price", "Proxy value", "Free Yahoo/proxy", "Finnhub free/proxy", "Yahoo/proxy can lag", "range-distributed proxy", "Proxy levels", "Insufficient sector", "TRADINGVIEW FALLBACK", "'Spot proxy'"].forEach(bit => {
  ok(src.indexOf(bit) < 0, "gone: " + bit);
});
ok(src.split("SPOT PROXY").length === 2, "SPOT PROXY remains only as the old-label matcher");
if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("rt55b fixture passed");
