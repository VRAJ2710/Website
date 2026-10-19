#!/usr/bin/env node
"use strict";
/* Feed category is the default. Commodity subject runs before equity.
   Stocks needs a ticker, an exchange:ticker, or a company plus a stock word.
   No market words is Other. n.tg, the chip, and the filter use one word. */
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt55/out/app.js";
const src = fs.readFileSync(appPath, "utf8");

function grab(name) {
  const at = src.indexOf("function " + name);
  if (at < 0) throw new Error("missing " + name);
  let i = src.indexOf("{", at), n = 0, q = "";
  for (; i < src.length; i++) {
    const c = src[i];
    if (q) { if (c === "\\") { i++; continue; } if (c === q) q = ""; continue; }
    if (c === "'" || c === '"' || c === "`") { q = c; continue; }
    if (c === "{") n++;
    else if (c === "}" && --n === 0) return src.slice(at, i + 1);
  }
  throw new Error("unclosed " + name);
}
function between(a, b) {
  const i = src.indexOf(a), j = src.indexOf(b);
  if (i < 0 || j < 0) throw new Error("missing markers");
  return src.slice(i + a.length, j);
}
const rulesAt = src.indexOf("const TAG_RULES = {");
const rulesEnd = src.indexOf("};", rulesAt);
const tagRules = src.slice(rulesAt, rulesEnd + 2);
const ctx = {
  A: [
    { tk: "MU", nm: "Micron", cat: "Stock" },
    { tk: "NVDA", nm: "NVIDIA", cat: "Stock" },
    { tk: "NOW", nm: "ServiceNow", cat: "Stock" },
    { tk: "AAPL", nm: "Apple", cat: "Stock" },
    { tk: "BP", nm: "BP", cat: "Stock" },
    { tk: "SEC", nm: "not a ticker we should use", cat: "Index" }
  ]
};
vm.createContext(ctx);
vm.runInContext(
  tagRules + "\n" +
  grab("fe64_chip") + "\n" +
  grab("fe64_equityStory") + "\n" +
  grab("fe64_cryptoStory") + "\n" +
  between("// fe65-tag-begin", "// fe65-tag-end") + "\n" +
  grab("_rt53bTag") + "\n" +
  "this.detectTag=_rt53bTag; this.fe64_chip=fe64_chip;",
  ctx
);

const FILTER = { stocks: "Stocks", commodities: "Commodities", crypto: "Crypto", forex: "Forex", macro: "Macro", geopolitics: "Geopolitics", regulation: "Regulation", other: "Other" };
function filterHit(tg, id) { return ctx.fe64_chip(tg) === FILTER[id]; }

let failed = 0;
function check(text, feedCat, srcName, want, filterId) {
  const tg = ctx.detectTag(text, feedCat, srcName);
  const chip = ctx.fe64_chip(tg);
  const pass = tg === want && chip === want && filterHit(tg, filterId);
  if (pass) console.log("ok", want, text.slice(0, 48));
  else { failed++; console.error("FAIL", JSON.stringify({ text, feedCat, srcName, tg, chip, want })); }
}

check("SEC tokenized stock framework", "Crypto", "CoinDesk", "Crypto", "crypto");
check("SEC tokenized stock framework", "Crypto", "Investing Crypto", "Crypto", "crypto");
check("Gold rises as Warsh remarks curb Fed hike bets", "Markets", "Reuters", "Commodities", "commodities");
check("Gold rises as Warsh remarks curb Fed hike bets. NVDA was flat.", "Stocks", "Reuters", "Commodities", "commodities");
check("Kylie Minogue songs used to train AI", "Markets", "BBC", "Other", "other");
check("Andy Burnham headphone dodgers", "World", "Guardian", "Other", "other");
check("BP (LSE:BP.) shares rise after results", "Markets", "Reuters", "Stocks", "stocks");
check("Micron (MU) shares rise", "Stocks", "Reuters", "Stocks", "stocks");
check("Apple stock climbs", "Stocks", "Reuters", "Stocks", "stocks");
check("The committee met on Thursday", "World", "BBC", "Other", "other");

if (src.indexOf("function _rt52Retag") < 0 || src.indexOf("n.tg = t") < 0) {
  failed++; console.error("FAIL retag does not write n.tg");
} else console.log("ok retag writes n.tg");

if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("tag fixture passed");
