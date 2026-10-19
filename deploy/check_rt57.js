#!/usr/bin/env node
"use strict";
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt57/in/app.js";
const src = fs.readFileSync(appPath, "utf8");
const a = src.indexOf("// fe68-pure-begin");
const b = src.indexOf("// fe68-pure-end");
if (a < 0 || b < a) {
  console.error("pure slice missing");
  process.exit(1);
}
const pure = src.slice(a, b);
const sandbox = { console, Date, Intl, Object, String, Number, RegExp, Math, isFinite, Array };
vm.createContext(sandbox);
vm.runInContext(pure, sandbox);

const rows = [
  ["Starboard takes an activist stake in Skyworks and the shares hit a record", "Crypto", "Stocks"],
  ["CoreWeave bond rout deepens after a weak sale", "Crypto", "Stocks"],
  ["Hang Seng slides as Asian stocks slip on the open", "Crypto", "Stocks"],
  ["Senator Rubio speaks at a technology conference", "Geopolitics", "Other"],
  ["Rubio backs new sanctions on chip exports", "Geopolitics", "Geopolitics"],
  ["SEC sets out a tokenized stock framework", "Crypto", "Crypto"],
  ["NewPeak starts gold drilling in Western Australia", "Stocks", "Commodities"],
  ["Cindy Crawford launches a new skincare line", "Geopolitics", "Other"],
  ["Andy Burnham calls headphone dodgers selfish", "Geopolitics", "Other"],
  ["Kylie Minogue says AI could write her next single", "Stocks", "Other"],
  ["Council issues a fine over loud bus music", "Macro", "Other"],
  ["Dollar firmer as FX traders cut euro longs", "FX", "Forex"],
  ["Ampol lifts fuel sales outlook", "Crypto", "Commodities"],
  ["New Hope raises coal output guidance", "Crypto", "Commodities"],
  ["New Hope says coal prices held up last quarter", "Crypto", "Commodities"],
  ["FleetPartners shares climb after a fleet contract", "Crypto", "Stocks"],
  ["An AI-picked stock list names three US winners", "Crypto", "Stocks"],
  ["Asian stocks slip on a weaker open", "Crypto", "Stocks"],
  ["Deutsche Bank plans crypto custody for institutions", "Crypto", "Crypto"],
  ["Bitcoin, Kospi and Nasdaq futures rally together", "Stocks", "Crypto"],
  ["Weekly market briefing", "Macro", "Macro"]
];

let fail = 0;
function check(ok, msg) {
  if (!ok) { fail++; console.log("FAIL " + msg); }
  else console.log("ok   " + msg);
}

console.log("headline | feed | got | want");
const cryptoShown = [];
rows.forEach(function (r) {
  const got = sandbox.fe68_storyTag(r[0], "", null, r[1]);
  const ok = got === r[2];
  if (!ok) fail++;
  if (got === "Crypto") cryptoShown.push(r[0]);
  console.log((ok ? "ok  " : "FAIL") + " | " + got + " | " + r[2] + " | " + r[1] + " | " + r[0]);
});
const cryptoWant = [
  "SEC sets out a tokenized stock framework",
  "Deutsche Bank plans crypto custody for institutions",
  "Bitcoin, Kospi and Nasdaq futures rally together"
];
check(cryptoShown.length === cryptoWant.length && cryptoWant.every(function (t) { return cryptoShown.indexOf(t) >= 0; }),
  "crypto filter only real crypto (" + cryptoShown.length + ")");

const now = Date.parse("2026-10-19T12:00:00Z");
function badge(meta, tk) {
  return sandbox.fe68_badge(meta, tk, now);
}
const recent = now - 2 * 60 * 1000;
const old = now - 20 * 60 * 1000;
const c1 = badge({ status: "cached", label: "CACHED", src: "coingecko", asOf: recent, cached: true }, "SHIB");
check(c1.label.indexOf("as of ") === 0 && /UK$/.test(c1.label) && !/cached/i.test(c1.label + c1.detail), "cached recent -> as of UK, no CACHED (" + c1.label + ")");
const c2 = badge({ status: "cached", label: "CACHED", src: "coingecko", asOf: old, cached: true }, "BCH");
check(c2.label === "delayed" && c2.status === "delayed" && !/cached/i.test(c2.label), "cached older than threshold -> delayed");
const live = badge({ status: "live", label: "LIVE·CB", src: "coinbase-ws", asOf: recent, detail: "Coinbase Exchange stream" }, "ETH");
check(live.label === "LIVE" && live.title === "Coinbase" && /Coinbase/.test(live.detail), "LIVE·CB -> LIVE, source in title");
const ys = badge({ status: "live", label: "LIVE·YS", src: "yahoo-stream", asOf: recent, detail: "" }, "EURUSD");
check(ys.label === "LIVE" && ys.title === "Yahoo", "LIVE·YS -> LIVE");
const note = sandbox.fe68_words("delayed 20m by exchange");
check(note === "delayed 20 min by exchange", "delayed 20m -> delayed 20 min (" + note + ")");
const note15 = sandbox.fe68_words("delayed 15m by exchange");
check(note15 === "delayed 15 min by exchange", "delayed 15m -> min");
const xau = badge({ status: "stale", label: "STALE", src: "gold-api-spot-proxy-browser", asOf: now - 30 * 1000, detail: "Gold · free market feed", fe64Note: "free gold feed" }, "XAU");
check(xau.status === "live" && xau.detail === "Spot gold" && !/stale|free gold|cached/i.test(xau.label + " " + xau.detail + " " + xau.fe64Note), "XAU fresh gold-api is LIVE Spot gold (" + xau.status + " " + xau.detail + ")");
const xauLag = badge({ status: "stale", label: "STALE·SPOT", src: "gold-api-spot-proxy-browser", asOf: now - 8 * 60 * 1000, detail: "free gold feed", checkedAge: 2000 }, "XAU");
check(xauLag.status === "live" && xauLag.detail === "Spot gold", "XAU checked recently stays LIVE (" + xauLag.status + ")");
const slv = badge({ status: "proxy", label: "free feed", src: "gold-api-spot-metal", asOf: recent, detail: "Gold · free market feed" }, "SLV");
check(slv.detail === "SLV · silver ETF" && !/gold|free gold|cached/i.test(slv.detail), "SLV is the silver ETF (" + slv.detail + ")");
const pall = badge({ status: "stale", label: "STALE·SPOT", src: "gold-api-spot-metal", asOf: now - 6 * 60 * 1000, detail: "This price is not current." }, "PALLADIUM");
check(pall.status !== "stale" && !/stale|cached/i.test(pall.label), "PALLADIUM within window is not STALE (" + pall.status + " " + pall.label + ")");
const eur = badge({ status: "stale", label: "STALE", src: "yahoo-last-good", asOf: recent, cached: true, detail: "CACHED" }, "EURUSD");
check(/as of /.test(eur.label) && eur.status !== "stale" && !/cached/i.test(eur.label), "EURUSD last-good within threshold is as of (" + eur.label + ")");
const wordsFree = sandbox.fe68_words("free gold feed");
check(wordsFree === "Spot gold" && !/cached/i.test(wordsFree), "words strip free gold feed");

check(src.indexOf('SSE: ["Asia/Shanghai", 570, 900, 690, 780]') >= 0, "SSE calendar row");
check(src.indexOf('SZSE: ["Asia/Shanghai", 570, 900, 690, 780]') >= 0, "SZSE calendar row");
check(src.indexOf("Fit score covers US-listed stocks for now.") < 0, "regime clause removed");
check(src.indexOf("We couldn't load a price for ${shown} just now. Try again in a minute.") >= 0, "BP.L desktop sentence");
check(src.indexOf("We couldn't load a price for ${_dynTk} just now. Try again in a minute.") >= 0, "BP.L mobile sentence");
check(src.indexOf("See full history with Premium") >= 0, "premium insider row");
check(src.indexOf("/api/insiders?t=") >= 0, "insiders endpoint");
check(src.indexOf("Unknown ticker.") >= 0, "unknown ticker copy");
check(src.indexOf("No Form 4 filings for this ticker.") >= 0, "empty filings copy");
check(src.indexOf("Insider filings unavailable right now") >= 0, "unavailable copy");
check(/\.SZ\|TW/.test(src) || src.indexOf("SS|SZ|TW") >= 0, ".SZ treated as non-US");

const olderStart = src.indexOf("function fe68_older");
const olderEnd = src.indexOf("function fe68_dayHl");
vm.runInContext(src.slice(olderStart, olderEnd), sandbox);
sandbox.liveQuoteSrc = { ETH: "coinbase-ws", EURUSD: "yahoo-stream" };
sandbox.liveQuoteTs = { ETH: now, EURUSD: now };
sandbox._rt = { lastRecv: { ETH: now - 1000, EURUSD: now - 1000 } };
check(sandbox.fe68_older("ETH", { stale: true, ts: now, source: "coingecko-last-good", p: 1 }) === true, "ETH last-good does not cover a fresh stream");
check(sandbox.fe68_older("EURUSD", { cached: true, ts: now, source: "yahoo", p: 1 }) === true, "EURUSD cached poll does not cover a fresh stream");
check(sandbox.fe68_older("ETH", { ts: now - 5000, source: "coinbase-ws", p: 1 }) === true, "older stream tick is skipped");

const b0 = src.indexOf("// fe66b-pure-begin");
const b1 = src.indexOf("// fe66b-pure-end");
check(b0 >= 0 && b1 > b0, "lunch slice present");
if (b0 >= 0 && b1 > b0) {
  const lunch = {};
  vm.createContext(lunch);
  lunch.fe66b_cal = {
    SSE: ["Asia/Shanghai", 570, 900, 690, 780],
    SZSE: ["Asia/Shanghai", 570, 900, 690, 780]
  };
  lunch._rt18Parts = function (tz, d) {
    const o = {};
    new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).forEach(function (x) { o[x.type] = x.value; });
    return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };
  };
  vm.runInContext(src.slice(b0, b1), lunch);
  const noon = Date.parse("2026-10-19T04:00:00Z");
  const morning = Date.parse("2026-10-19T02:00:00Z");
  lunch.fe66b_now.pin = noon;
  const sse = lunch.fe66b_text("600519.SS", null, noon);
  const sz = lunch.fe66b_text("000001.SZ", null, noon);
  lunch.fe66b_now.pin = morning;
  const open = lunch.fe66b_text("600519.SS", null, morning);
  check(/Lunch break/.test(sse), "SSE lunch at 12:00 CST (" + sse + ")");
  check(/Lunch break/.test(sz), "SZSE lunch at 12:00 CST (" + sz + ")");
  check(!open, "SSE morning is not lunch (" + open + ")");
}

if (fail) {
  console.error("FAILED " + fail);
  process.exit(1);
}
console.log("ALL PASS");
