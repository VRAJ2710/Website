#!/usr/bin/env node
"use strict";
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt58/in/app.js";
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

const c0 = src.indexOf("// fe69-pure-begin");
const c1 = src.indexOf("// fe69-pure-end");
if (c0 < 0 || c1 < c0) {
  console.error("fe69 slice missing");
  process.exit(1);
}
vm.runInContext(src.slice(c0, c1), sandbox);

// The original 21. Chips are single-membership, so a regulator word wins:
// "SEC sets out a tokenized stock framework" is Regulation, not Crypto.
const rows = [
  ["Starboard takes an activist stake in Skyworks and the shares hit a record", "Crypto", "Stocks"],
  ["CoreWeave bond rout deepens after a weak sale", "Crypto", "Stocks"],
  ["Hang Seng slides as Asian stocks slip on the open", "Crypto", "Stocks"],
  ["Senator Rubio speaks at a technology conference", "Geopolitics", "Other"],
  ["Rubio backs new sanctions on chip exports", "Geopolitics", "Geopolitics"],
  ["SEC sets out a tokenized stock framework", "Crypto", "Regulation"],
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

const extra = [
  ["People playing loud music on buses could face £100 fine. Passengers should share the carriage, not the noise.", "Macro", "Other"],
  ["EU tariffs aimed at China hitting Ukraine, steel boss says", "Macro", "Geopolitics"],
  ["What is the Budget and what could be in it?", "Macro", "Macro"],
  ["Ship attack reports near Hormuz reach record high as oil exports slow", "Commodities", "Geopolitics"],
  ["China's growth accelerates as AI export boom outweighs domestic weakness", "Macro", "Macro"],
  ["China's third-quarter economic growth quickens to 4.5% as exports surge, beating estimates", "Stocks", "Macro"],
  ["France hit by worst unrest in years as attempts to rein in government spending meet citizen ire", "Geopolitics", "Macro"],
  ["Strong Exports Stabilize China’s Economic Growth in Official Statistics", "Macro", "Macro"],
  ["China’s new home prices fall again in September as recovery stays elusive", "Commodities", "Macro"],
  ["China’s economic growth accelerates to 4.5% in third quarter", "Macro", "Macro"],
  ["China’s economic growth picks up in third quarter, beating expectations", "Macro", "Macro"],
  ["China’s Q3 GDP growth accelerates to 4.5%, beating forecast", "Macro", "Macro"],
  ["Gift Nifty 50 faces bull trap risk at 23,036 VWAP: Live levels", "Crypto", "Stocks"],
  ["Stocktwits Pharma Pulse: Moderna-Merck Cancer Vaccine Grabs Spotlight As Kidney-Cancer And MS Data Pour In", "Stocks", "Stocks"],
  ["SEC tokenized stock framework faces issuer pushback as Broadcom, Verizon object to OKX-ICE listing", "Crypto", "Regulation"],
  ["Bitcoin, Korea’s Kospi and Nasdaq futures rally as China GDP beats estimates", "Crypto", "Crypto"],
  ["Major fire at Canada military base leaves four dead, dozens injured", "Geopolitics", "Other"],
  ["What we know so far about deadly fire at Canadian military base", "Geopolitics", "Other"],
  ["Four people killed in ‘violent, fast-moving’ fire at Canadian military base", "Geopolitics", "Other"],
  ["Container ship hit by projectile sinks in Strait of Hormuz, Singapore says", "Geopolitics", "Geopolitics"],
  ["livestock prices stay flat", "Commodities", "Other"],
  ["stocktwits chatter only", "Crypto", "Stocks"],
  ["Exchange listing framework updated", "Other", "Regulation"]
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
  "Deutsche Bank plans crypto custody for institutions",
  "Bitcoin, Kospi and Nasdaq futures rally together"
];
check(cryptoShown.length === cryptoWant.length && cryptoWant.every(function (t) { return cryptoShown.indexOf(t) >= 0; }),
  "original crypto filter drops the SEC headline (" + cryptoShown.length + ")");

extra.forEach(function (r) {
  const got = sandbox.fe68_storyTag(r[0], "", null, r[1]);
  const ok = got === r[2];
  if (!ok) fail++;
  console.log((ok ? "ok  " : "FAIL") + " | " + got + " | " + r[2] + " | " + r[1] + " | " + r[0]);
});

const now = Date.parse("2026-10-19T12:00:00Z");
function badge(meta, tk) {
  return sandbox.fe68_badge(meta, tk, now);
}
const recent = now - 2 * 60 * 1000;
const old = now - 20 * 60 * 1000;
const c1b = badge({ status: "cached", label: "CACHED", src: "coingecko", asOf: recent, cached: true }, "SHIB");
check(c1b.label.indexOf("as of ") === 0 && /UK$/.test(c1b.label) && !/cached/i.test(c1b.label + c1b.detail), "cached recent -> as of UK, no CACHED (" + c1b.label + ")");
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

const brent = sandbox.fe69_reconcile({ status: "stale", label: "STALE", detail: "Yahoo Finance" }, { status: "stale", delayMin: 10 });
check(brent.status === "delayed" && brent.label === "delayed 10 min" && brent.detail === "delayed 10 min by exchange", "BRENT delayMin 10 replaces STALE (" + brent.label + ")");
const toyota = sandbox.fe69_reconcile({ status: "delayed", label: "DELAYED 15m" }, { status: "delayed", delayMin: 20 });
check(toyota.label === "delayed 20 min" && toyota.detail === "delayed 20 min by exchange", "7203.T uses delayMin 20 (" + toyota.label + ")");
const closed = sandbox.fe69_reconcile({ status: "closed", label: "London market closed" }, { status: "closed", delayMin: 15 });
check(closed.status === "closed" && closed.label.indexOf("delayed") < 0, "closed market is not rewritten (" + closed.label + ")");
check(sandbox.fe69_words("DELAYED·CG") === "delayed", "DELAYED·CG becomes delayed");
check(sandbox.fe69_words("free gold feed") === "Spot gold", "fe69 words strip free gold feed");
check(sandbox.fe69_insSpan(2399, 827655) === " \u00b7 2,399 shares \u00b7 $828k at $345.00", "insider span (" + sandbox.fe69_insSpan(2399, 827655) + ")");
check(sandbox.fe69_beforeDate({ next: "before=2026-04-16", from: "2026-02-01" }) === "2026-04-16", "before date from next");
check(sandbox.fe69_beforeDate({ from: "2026-02-01" }) === "2026-02-01", "before date falls back to from");
check(sandbox.fe69_hasNext({ next: "before=2026-04-16" }) === true, "has next");
check(sandbox.fe69_hasNext({ from: "2026-02-01" }) === false && sandbox.fe69_hasNext(null) === false, "no next hides Load older");
const gap = sandbox.fe69_srcGap("The move is the point. Sources: ICE, Yahoo Finance");
check(gap.indexOf("\n\nSources:") >= 0, "Sources gets a break (" + JSON.stringify(gap) + ")");
check(sandbox.fe69_srcHtml("The move is the point. Sources: ICE").indexOf("<br><br>Sources:") >= 0, "brief Sources html break");
check(sandbox.fe69_keepPrice({ price: 614.1, name: "BP" }, { price: 0 }).price === 614.1, "keep a painted price");
check(sandbox.fe69_keepPrice({ price: 1 }, { price: 2 }).price === 2, "a real next price replaces");
check(sandbox.fe69_chatFresh("chat37") === true && sandbox.fe69_chatFresh("") === true && sandbox.fe69_chatFresh("bb8") === true, "older chat keys are cleared");
check(sandbox.fe69_chatFresh("chat70") === false, "chat70 is left in place");
check(sandbox.fe69_finPartial({ meta: { partial: true } }, "") === true, "meta.partial is partial");
check(sandbox.fe69_finPartial({ meta: { partial: 0 } }, "partial") === true, "header partial is partial");
check(sandbox.fe69_finPartial({ meta: {} }, "Partial") === true, "header partial ignores case");
check(sandbox.fe69_finPartial({ valuation: { pe: 8.4 } }, "complete") === false, "complete financials are not partial");
const bp = sandbox.fe69_finView({ valuation: { pe: 8.4, price: 614.1, marketCap: 8e10 }, financials: { annual: [{ revenue: 2e11 }] }, priceCurrency: "GBp", financialCurrency: "GBP", fx: 0.01 });
check(bp.pe === 8.4 && bp.peText === "8.4×", "BP.L P/E stays 8.4× (" + bp.peText + ")");
check(bp.price === 614.1 && bp.priceText === "614.10p", "BP.L price stays 614.10p (" + bp.priceText + ")");
check(bp.revenue === 2e11 && bp.revenueText === "£200.00B", "BP.L revenue stays £200.00B (" + bp.revenueText + ")");
check(bp.marketCap === 8e10 && bp.marketCapText === "£80.00B", "BP.L market cap uses GBP (" + bp.marketCapText + ")");
check(bp.price !== 6.141 && bp.revenue !== 2e9, "BP.L is not divided by 100 or multiplied by fx");
const mu = sandbox.fe69_finView({ valuation: { pe: 22.5, price: 104.2, marketCap: 1.2e11 }, financials: { annual: [{ revenue: 3.2e10 }] }, priceCurrency: "USD", financialCurrency: "USD", fx: 1 });
check(mu.pe === 22.5 && mu.peText === "22.5×" && mu.priceText === "$104.20", "MU P/E and price stay USD (" + mu.peText + " " + mu.priceText + ")");
check(mu.revenueText === "$32.00B" && mu.price === 104.2, "MU revenue stays in dollars (" + mu.revenueText + ")");
const bare = sandbox.fe69_finView({ valuation: { pe: 11, price: 20 }, financials: { annual: [{ revenue: 1e9 }] } });
check(bare.tagged === false && bare.priceText === "$20.00" && bare.pe === 11, "missing currency fields stay on the dollar path");
check(src.indexOf('!== "chat70"') >= 0 && src.indexOf('setItem("td_chat_v", "chat70")') >= 0 && src.indexOf("chat37") < 0, "td_chat version is chat70");
check(src.indexOf('sessionStorage.removeItem("td_chat")') >= 0 && src.indexOf('localStorage.removeItem("td_chat")') >= 0, "only td_chat entries are cleared");
check(src.indexOf("function fe69_finPut") >= 0 && src.indexOf("fe69_finOnce") >= 0, "partial financials refetch once");
check(src.indexOf("X-Dispatch-Data-Status") >= 0 && src.indexOf("fe69_finRefetch(tk); }, 5000)") >= 0, "partial refetch waits about 5s");
const putAt = src.indexOf("function fe69_finPut");
const putBody = src.slice(putAt, src.indexOf("function fe69_finPaint"));
check(putBody.indexOf("fe69_finPartial") < putBody.indexOf("_finCache[tk] = data"), "complete results are the only cache write");

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
check(src.indexOf('return "free gold feed"') < 0, "no free gold feed return");
check(!/label\s*=\s*["']DELAYED·CG["']/.test(src), "no DELAYED·CG label assignment");
check(src.indexOf("BP-L") < 0, "no BP-L client rewrite");
check(src.indexOf("Load older") >= 0, "Load older button");
check(src.indexOf("Still loading older filings, refresh in a moment") >= 0, "partial notice");
check(src.indexOf("data.house.label") >= 0 && src.indexOf("data.meta.window") >= 0, "window and house labels");
check(src.indexOf("delayMin") >= 0, "delayMin used");
check(src.indexOf("Loading insider filings…") >= 0, "insider loading copy");
check(src.indexOf("Looking up the listing…") >= 0, "search placeholder");
check(src.indexOf("Loading chart…") >= 0, "chart placeholder");
check(src.indexOf("function fe69_takeChart") >= 0, "chart fills in later");
check(src.indexOf("data-fe69-ask") >= 0 && src.indexOf("function fe69_placeAsk") >= 0, "Ask button is moved above the expanded panel");
check(src.indexOf('_dynTk === want') >= 0, "dynamic lookup stays open");
check(src.indexOf("fe69_paintLookup") >= 0, "price paints from the quote");
check(src.indexOf('onclick="fe69_askCard(this)"') >= 0, "Ask sends from the intel card");
const askAt = src.indexOf("function fe69_askCard");
const askBody = src.slice(askAt, src.indexOf("function fe69_regimeAi"));
check(askAt >= 0 && askBody.indexOf("td_chat") < 0, "auto-send does not read saved chat");
check(askBody.indexOf("fe69_asked[key] = 1") >= 0 && askBody.indexOf("if (fe69_asked[key]) return;") >= 0, "auto-send fires once per ticker");
check(src.indexOf("return x.replace(m[0], m[1]);") < 0, "local Headwind label is kept without a fit score");
check(!/else r\.headline = r\.headline\.replace/.test(src), "a loading fit does not strip the stock label");
check(src.indexOf("function fe69_intelTk") >= 0 && src.indexOf('surface = "ticker"') >= 0, "an open stock pins the intel card");

const olderStart = src.indexOf("function fe68_older");
const olderEnd = src.indexOf("function fe68_dayHl");
vm.runInContext(src.slice(olderStart, olderEnd), sandbox);
sandbox.liveQuoteSrc = { ETH: "coinbase-ws", EURUSD: "yahoo-stream" };
sandbox.liveQuoteTs = { ETH: now, EURUSD: now };
sandbox._rt = { lastRecv: { ETH: now - 1000, EURUSD: now - 1000 } };
check(sandbox.fe68_older("ETH", { stale: true, ts: now, source: "coingecko-last-good", p: 1 }) === true, "ETH last-good does not cover a fresh stream");
check(sandbox.fe68_older("EURUSD", { cached: true, ts: now, source: "yahoo", p: 1 }) === true, "EURUSD cached poll does not cover a fresh stream");
check(sandbox.fe68_older("ETH", { ts: now - 5000, source: "coinbase-ws", p: 1 }) === true, "older stream tick is skipped");

const o0 = src.indexOf("function fe69_older");
const o1 = src.indexOf("function fe69_noteQuote");
vm.runInContext(src.slice(o0, o1), sandbox);
sandbox.liveQuoteSrc.BZ = "session-cache";
sandbox.liveQuoteCached = { BZ: true };
sandbox.liveQuoteTs.BZ = now;
check(sandbox.fe69_older("BZ", { ts: now - 60000, source: "yahoo", p: 108, status: "delayed" }) === false, "wire quote replaces a session-cache snapshot");
check(sandbox.fe69_older("BZ", { ts: now - 60000, source: "session-cache", cached: true, p: 107 }) === true, "older snapshot is still skipped");

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
