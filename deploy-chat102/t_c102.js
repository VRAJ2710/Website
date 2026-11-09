"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");
const lib = require("./lib_c102.js");

const NOW = Date.parse("2026-11-06T15:30:00.000Z");
const dir = __dirname;

function yahoo(symbol, name, price, prev, timeSec, extra) {
  return {
    chart: {
      result: [{
        meta: Object.assign({
          symbol: symbol,
          shortName: name,
          longName: name,
          instrumentType: "INDEX",
          regularMarketPrice: price,
          previousClose: prev,
          regularMarketTime: timeSec,
          exchangeTimezoneName: "America/New_York",
          currency: "USD",
          fullExchangeName: "Cboe Indices",
          exchangeName: "CXI"
        }, extra || {}),
        timestamp: [timeSec],
        indicators: { quote: [{ open: [price], high: [price], low: [price], close: [price], volume: [0] }] }
      }]
    }
  };
}

test("B1 gold and silver ratio uses same source and rejects a time gap", () => {
  const gold = lib.c102ParseMetal({ symbol: "XAU", currency: "USD", price: 4053.5, name: "Gold", updatedAt: "2026-11-06T15:23:00Z" }, "XAU");
  const silver = lib.c102ParseMetal({ symbol: "XAG", currency: "USD", price: 52.2, name: "Silver", updatedAt: "2026-11-06T15:23:00Z" }, "XAG");
  const ratio = lib.c102Ratio(gold, silver);
  assert.equal(ratio.status, "ok");
  assert.equal(ratio.value, Math.round((4053.5 / 52.2) * 1000) / 1000);
  assert.equal(ratio.numerator.unit, "USD per troy ounce");
  assert.equal(ratio.denominator.name, "Silver spot");
  const drifted = lib.c102Ratio(gold, Object.assign({}, silver, { asOfUtc: "2026-11-06T16:00:00.000Z" }));
  assert.equal(drifted.status, "unavailable");
  assert.equal(drifted.value, undefined);
});

test("B1 one-second metal gap is partial and still shows both times", () => {
  const gold = lib.c102ParseMetal({ symbol: "XAU", currency: "USD", price: 4053.5, updatedAt: "2026-11-06T15:28:05Z" }, "XAU");
  const silver = lib.c102ParseMetal({ symbol: "XAG", currency: "USD", price: 52.202, updatedAt: "2026-11-06T15:28:04Z" }, "XAG");
  const ratio = lib.c102Ratio(gold, silver);
  assert.equal(ratio.status, "partial");
  assert.equal(typeof ratio.value, "number");
  assert.match(ratio.message, /seconds apart/);
});

test("B1 spot change does not borrow a futures percentage", () => {
  const borrowed = lib.c102SnapshotChange({ rows: { gold_usd: { source: "Yahoo Finance futures GC=F", changePct: -1.15 } } });
  assert.equal(borrowed.status, "unavailable");
  assert.equal(borrowed.changePct, undefined);
  const missing = lib.c102SnapshotChange({ rows: { gold_usd: { source: "gold-api.com spot", changePct: null } } });
  assert.equal(missing.status, "unavailable");
  const zero = lib.c102SnapshotChange({ rows: { gold_usd: { source: "gold-api.com spot snapshot", changePct: 0, changeBasis: "since yesterday's close" } } });
  assert.equal(zero.status, "ok");
  assert.equal(zero.changePct, 0);
});

test("B1 dollar index must be the ICE quote, not a synthetic basket", () => {
  const ice = lib.c102YahooQuote(yahoo("DX-Y.NYB", "US Dollar Index", 102.13, 101.55, 1793978328, { fullExchangeName: "ICE Futures", exchangeName: "NYB" }), {
    symbol: "DX-Y.NYB", instrument: "INDEX", nameTest: /dollar index/i, rejectName: /synthetic|basket/i, wantIce: true, range: [40, 200],
    label: "US dollar index", source: "ICE US Dollar Index via Yahoo Finance, delayed"
  });
  assert.equal(ice.status, "ok");
  assert.equal(ice.ice, true);
  assert.match(ice.source, /ICE/);
  const basket = lib.c102YahooQuote(yahoo("DX-Y.NYB", "Dispatch FX basket", 102, 101, 1793978328, { fullExchangeName: "SYNTHETIC", exchangeName: "SYNTHETIC" }), {
    symbol: "DX-Y.NYB", instrument: "INDEX", nameTest: /dollar index/i, rejectName: /synthetic|basket/i, wantIce: true, range: [40, 200], label: "US dollar index", source: "x"
  });
  assert.notEqual(basket.status, "ok");
});

test("B1 VIX is the index and VXX is rejected", () => {
  const vix = lib.c102YahooQuote(yahoo("^VIX", "CBOE Volatility Index", 24.53, 24.53, 1793977801, { exchangeDataDelayedBy: 15 }), {
    symbol: "^VIX", instrument: "INDEX", nameTest: /volatility index/i, rejectName: /VXX/i, range: [1, 150],
    label: "Cboe volatility index", source: "Cboe Volatility Index via Yahoo Finance, delayed"
  });
  assert.equal(vix.status, "ok");
  assert.equal(vix.change, 0);
  assert.equal(vix.delayedByMin, 15);
  const bad = lib.c102YahooQuote(yahoo("VXX", "VXX", 40, 39, 1793977801), {
    symbol: "^VIX", instrument: "INDEX", nameTest: /volatility index/i, rejectName: /VXX/i, range: [1, 150], label: "x", source: "x"
  });
  assert.notEqual(bad.status, "ok");
});

test("B1 yields keep separate dates and a zero official change stays a number", () => {
  const fred = lib.c102FredCsv("DATE,DGS10\n2026-11-03,4.95\n2026-11-04,4.90\n", "DGS10");
  assert.equal(fred.date, "2026-11-04");
  assert.equal(fred.change, -0.05);
  assert.match(fred.message, /2026-11-04/);
  assert.doesNotMatch(fred.message, /today/i);
  const flat = lib.c102FredCsv("DATE,DFII10\n2026-11-03,2.64\n2026-11-04,2.64\n", "DFII10");
  assert.equal(flat.change, 0);
  assert.equal(flat.status, "ok");
  const model = lib.c102Assemble({
    nominal: { status: "ok", price: 4.87, change: 0.033, asOfUtc: "2026-11-06T15:13:46.000Z", source: "Cboe 10-year Treasury yield index via Yahoo Finance, delayed", unit: "percent" },
    dgs10: fred,
    dfii10: flat
  }, NOW);
  assert.notEqual(model.nominal.asOfUtc, model.nominalOfficial.date);
  assert.equal(model.nominalOfficial.date, "2026-11-04");
  assert.equal(model.realOfficial.change, 0);
});

test("B1 chart uses the returned contract name, drops today's bar, and does not invent a 50-session average", () => {
  const tz = "America/New_York";
  const day = (iso, close, vol) => {
    const sec = Math.floor(Date.parse(iso) / 1000);
    return { sec: sec, close: close, vol: vol };
  };
  const days = [];
  for (let i = 0; i < 30; i++) days.push(day("2026-10-" + String(i + 1).padStart(2, "0") + "T21:00:00Z", 4000 + i, i === 3 ? 0 : 1000 + i));
  days.push(day("2026-11-06T15:00:00Z", 4066, 50));
  const payload = {
    chart: {
      result: [{
        meta: { symbol: "GC=F", shortName: "Gold Dec 26", instrumentType: "FUTURE", fullExchangeName: "COMEX", exchangeTimezoneName: tz, currency: "USD", exchangeDataDelayedBy: 10 },
        timestamp: days.map((d) => d.sec),
        indicators: { quote: [{ open: days.map((d) => d.close - 1), high: days.map((d) => d.close + 1), low: days.map((d) => d.close - 2), close: days.map((d) => d.close), volume: days.map((d) => d.vol) }] }
      }]
    }
  };
  const chart = lib.c102Chart(payload, NOW);
  assert.equal(chart.status, "ok");
  assert.equal(chart.label, "Gold Dec 26 future \u00b7 delayed");
  assert.equal(chart.historyKind, "continuous-rolling-proxy");
  assert.equal(chart.excludedIncompleteSessions, 1);
  assert.ok(!chart.sessionDates.includes("2026-11-06"));
  assert.equal(chart.ma20.status, "ok");
  assert.equal(chart.ma50.status, "unavailable");
  assert.match(chart.ma50.message, /50/);
  const zeroVol = chart.bars.find((b) => b.sessionDate === "2026-10-04");
  assert.equal(zeroVol.volume, null);
  assert.equal(typeof zeroVol.c, "number");
  assert.equal(JSON.stringify(chart).includes("GC=F"), false);
});

test("B1 CFTC keeps COMEX gold and drops micro gold", () => {
  const good = lib.c102Cot([
    { report_date_as_yyyy_mm_dd: "2026-10-27T00:00:00.000", commodity_name: "GOLD", cftc_contract_market_code: "088691", market_and_exchange_names: "GOLD - COMMODITY EXCHANGE INC.", m_money_positions_long_all: "122508", m_money_positions_short_all: "16946", open_interest_all: "396810" },
    { report_date_as_yyyy_mm_dd: "2026-10-20T00:00:00.000", commodity_name: "GOLD", cftc_contract_market_code: "088691", market_and_exchange_names: "GOLD - COMMODITY EXCHANGE INC.", m_money_positions_long_all: "121000", m_money_positions_short_all: "16794", open_interest_all: "390000" }
  ]);
  assert.equal(good.status, "ok");
  assert.equal(good.net, 122508 - 16946);
  assert.equal(good.frequency, "weekly");
  assert.equal(good.reportDate, "2026-10-27");
  const micro = lib.c102Cot([
    { report_date_as_yyyy_mm_dd: "2026-10-27T00:00:00.000", commodity_name: "MICRO GOLD", cftc_contract_market_code: "088691", market_and_exchange_names: "MICRO GOLD - COMMODITY EXCHANGE INC.", m_money_positions_long_all: "10", m_money_positions_short_all: "1", open_interest_all: "20" }
  ]);
  assert.equal(micro.status, "malformed");
  assert.equal(micro.net, undefined);
});

test("B1 calendar drops consensus and keeps a real release", () => {
  const ev = lib.c102Events({
    rows: [
      { past: false, agency: "BLS", name: "US jobs report", when: "Fri 6 Nov, 13:30 UK", dayIso: "2026-11-06", source: "US Bureau of Labor Statistics", consensus: "200000" },
      { past: false, agency: "Other", name: "A private survey", when: "Mon", source: "A vendor" }
    ]
  });
  assert.equal(ev.items.length, 1);
  assert.equal(ev.items[0].name, "US jobs report");
  assert.equal(JSON.stringify(ev.items).includes("200000"), false);
  assert.equal(ev.consensus, "not shown");
});

test("B2 panel states stay specific and a zero change is not unavailable", () => {
  const model = lib.c102Assemble({
    gold: { status: "timeout", message: "This source did not answer in time. No number was filled in." },
    silver: { status: "ok", price: 52, currency: "USD", asOfUtc: "2026-11-06T15:23:00.000Z", source: "gold-api.com" },
    dollar: { status: "malformed", message: "This source returned something we could not use. No number was filled in." },
    vix: { status: "ok", price: 20, change: 0, asOfUtc: "2026-11-06T15:20:00.000Z", source: "Cboe Volatility Index via Yahoo Finance, delayed" },
    nominal: { status: "unavailable", message: "The delayed 10-year yield did not answer." },
    positioning: null,
    events: { status: "partial", items: [], message: "No upcoming release from these agencies was in the calendar." }
  }, NOW);
  assert.equal(model.ok, true);
  assert.equal(model.title, "Terminal");
  assert.equal(model.spot.status, "timeout");
  assert.equal(model.spot.price, undefined);
  assert.equal(model.ratio.status, "unavailable");
  assert.equal(model.dollar.status, "malformed");
  assert.equal(model.vix.change, 0);
  assert.equal(model.vix.status, "ok");
  assert.equal(model.nominal.status, "unavailable");
  assert.equal(model.positioning.status, "unavailable");
  assert.equal(model.events.status, "partial");
});

test("B2 a stale quote keeps its date and lag", () => {
  const model = lib.c102Assemble({
    vix: { status: "ok", price: 18, change: -0.2, asOfUtc: "2026-10-01T15:00:00.000Z", source: "Cboe Volatility Index via Yahoo Finance, delayed" }
  }, NOW);
  assert.equal(model.vix.status, "stale");
  assert.equal(model.vix.price, 18);
  assert.ok(model.vix.lagSeconds > 20 * 86400);
  assert.match(model.vix.message, /ago/);
  assert.ok(model.vix.asOfUk);
});

test("UK time is an English 24-hour reading of the UTC stamp", () => {
  const text = lib.c102Uk("2026-11-06T15:23:00.000Z");
  assert.match(text, /6 November 2026/);
  assert.match(text, /15:23/);
});

test("client render has the sections, no raw ticker, and no fabricated zero", () => {
  const context = { console: console, Intl: Intl, Date: Date, URL: URL };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c102.js"), "utf8"), context);
  const model = lib.c102Assemble({
    gold: lib.c102ParseMetal({ symbol: "XAU", currency: "USD", price: 4053.5, updatedAt: "2026-11-06T15:23:00Z" }, "XAU"),
    spotChange: { status: "unavailable", message: "The spot feed did not include a daily change. The futures percentage was not used." },
    vix: { status: "ok", price: 24.5, change: 0, asOfUtc: "2026-11-06T15:20:00.000Z", source: "Cboe Volatility Index via Yahoo Finance, delayed" }
  }, NOW);
  const html = context.c102ui.render(model, { status: "unavailable", message: "The futures chart did not answer." });
  assert.match(html, /id="c102-macro"/);
  assert.match(html, /id="c102-pos"/);
  assert.match(html, /id="c102-ev"/);
  assert.match(html, /id="c102-risk"/);
  assert.match(html, /Gold dashboard/);
  assert.match(html, /href="\/dashboard\/"/);
  assert.match(html, /href="\/gold\/"/);
  assert.match(html, /the feed returned zero/);
  assert.match(html, /Daily change|spot feed did not include a daily change/);
  assert.equal(html.includes("GC=F"), false);
  assert.equal(html.includes("^VIX"), false);
  assert.equal(html.includes("DX-Y.NYB"), false);
  assert.equal(html.includes("^TNX"), false);
  assert.equal(html.includes("VXX"), false);
  assert.equal(html.includes("DXY_FX"), false);
  for (const bad of ["<script", "function(", "const "]) assert.equal(html.includes(bad), false);
});

test("collect ignores a client symbol and keeps a timeout off the other panels", async () => {
  const calls = [];
  const fetch = async (url) => {
    calls.push(String(url));
    if (String(url).includes("symbol=") || String(url).includes("evil")) throw new Error("client symbol");
    if (String(url).includes("XAU")) return { ok: true, json: async () => ({ symbol: "XAU", currency: "USD", price: 4000, updatedAt: "2026-11-06T15:23:00Z" }) };
    if (String(url).includes("XAG")) return { ok: true, json: async () => ({ symbol: "XAG", currency: "USD", price: 50, updatedAt: "2026-11-06T15:23:00Z" }) };
    if (String(url).includes("DX-Y.NYB")) return { ok: true, json: async () => yahoo("DX-Y.NYB", "US Dollar Index", 102, 101, 1793978328, { fullExchangeName: "ICE Futures", exchangeName: "NYB" }) };
    if (String(url).includes("%5EVIX") || String(url).includes("^VIX")) return { ok: true, json: async () => yahoo("^VIX", "CBOE Volatility Index", 22, 21, 1793977800, { exchangeDataDelayedBy: 15 }) };
    if (String(url).includes("TNX")) return new Promise(() => {});
    if (String(url).includes("DGS10")) return { ok: true, text: async () => "DATE,DGS10\n2026-11-04,4.90\n" };
    if (String(url).includes("DFII10")) return { ok: true, text: async () => "DATE,DFII10\n2026-11-04,2.64\n" };
    if (String(url).includes("cftc")) return { ok: true, json: async () => [] };
    throw new Error("unexpected " + url);
  };
  const model = await lib.c102Collect({
    fetch: fetch,
    timeoutMs: 40,
    fred: null,
    calendar: async () => { throw new Error("timeout"); },
    goldDash: async () => ({ rows: { gold_usd: { source: "gold-api.com spot", changePct: null } } }),
    cnbc: null
  }, NOW);
  assert.equal(calls.some((u) => u.includes("evil")), false);
  assert.equal(model.spot.status, "ok");
  assert.equal(model.spot.price, 4000);
  assert.equal(model.ratio.status, "ok");
  assert.equal(model.dollar.ice, true);
  assert.equal(model.vix.delayedByMin, 15);
  assert.ok(model.nominal.status === "timeout" || model.nominal.status === "unavailable");
  assert.equal(model.events.status, "timeout");
  assert.equal(model.nominalOfficial.status, "ok");
  assert.equal(model.nominalOfficial.date, "2026-11-04");
});

test("chart fetch is allowlisted and a client query cannot change the symbol", async () => {
  let seen = "";
  const chart = await lib.c102ChartFetch({
    fetch: async (url) => {
      seen = String(url);
      assert.equal(url.includes("evil.example"), false);
      assert.match(url, /GC%3DF|GC=F/);
      return { ok: true, json: async () => ({ chart: { result: [] } }) };
    }
  }, NOW);
  assert.match(seen, /range=1y/);
  assert.equal(chart.status, "unavailable");
});

test("built server block matches the sources and has no DDL or gold-desk call", () => {
  const built = spawnSync(process.execPath, ["build_block.js"], { cwd: dir, encoding: "utf8" });
  assert.equal(built.status, 0, built.stderr);
  const block = fs.readFileSync(path.join(dir, "server_block_c102.js"), "utf8");
  assert.match(block, /chat102 terminal/);
  assert.equal(/create table|alter table|drop table/i.test(block), false);
  assert.equal(block.includes("/api/gold-desk"), false);
  assert.equal(block.includes("DXY_FX"), false);
  const context = { console: console, globalThis: {}, URL: URL, Date: Date, Map: Map, Promise: Promise, Intl: Intl, setTimeout: setTimeout, clearTimeout: clearTimeout, fetch: async () => ({ ok: false, status: 503 }) };
  context.globalThis = context;
  context.C102_NO_INSTALL = false;
  context.handle = async function () { return "pass"; };
  context.C93_NAV = [["/gold/", "Gold"], ["/calendar/", "Calendar"]];
  context.C101B_GROUPS = [["Gold and macro", [["/gold/dashboard/", "Gold dashboard"], ["/calendar/", "Calendar"]]]];
  context.renderPublicSitemap = async () => "<urlset></urlset>";
  context.BB10I_MAINTENANCE_ON = false;
  vm.createContext(context);
  vm.runInContext(block, context);
  assert.ok(context.C93_NAV.some((x) => x[0] === "/terminal/"));
  assert.ok(context.C101B_GROUPS[0][1].some((x) => x[0] === "/terminal/"));
  const headers = {};
  let body = "";
  const res = { writeHead: (code, h) => { res.code = code; Object.assign(headers, h); }, end: (b) => { body = b || ""; } };
  return context.handle({ method: "GET", url: "/api/c102/chart?symbol=https://evil.example" }, res).then(() => {
    assert.equal(res.code, 200);
    assert.equal(headers["Cache-Control"], "no-store");
    assert.equal(headers["X-Content-Type-Options"], "nosniff");
    assert.equal(headers["X-Frame-Options"], "DENY");
    const json = JSON.parse(body);
    assert.notEqual(json.status, undefined);
    assert.equal(JSON.stringify(json).includes("evil.example"), false);
  });
});

test("app.js boot guard keeps Dashboard and Gold and passes node --check", () => {
  const src = "/tmp/prod101h/app.js";
  if (!fs.existsSync(src)) return;
  const work = fs.mkdtempSync("/tmp/c102-app-");
  fs.copyFileSync(src, path.join(work, "app.js"));
  fs.writeFileSync(path.join(work, "server.js"), "const BB10I_MAINTENANCE_ON = false;\nfunction handle(){}\n");
  fs.writeFileSync(path.join(work, "index.html"), "<script src=\"/app.js?v=chat101h\"></script>\n");
  const patched = spawnSync("python3", [path.join(dir, "patch_c102.py"), path.join(work, "server.js"), path.join(work, "app.js"), path.join(work, "index.html"), path.join(dir, "server_block_c102.js"), path.join(dir, "app_block_c102.js")], { encoding: "utf8" });
  assert.equal(patched.status, 0, patched.stderr);
  const app = fs.readFileSync(path.join(work, "app.js"), "utf8");
  assert.match(app, /c102Path === "\/terminal"/);
  assert.match(app, /Dashboard/);
  assert.match(app, /\["gold","Gold"\]/);
  assert.match(fs.readFileSync(path.join(work, "index.html"), "utf8"), /app\.js\?v=chat102"/);
  const check = spawnSync(process.execPath, ["--check", path.join(work, "app.js")], { encoding: "utf8" });
  assert.equal(check.status, 0, check.stderr);
  const serverCheck = spawnSync(process.execPath, ["--check", path.join(work, "server.js")], { encoding: "utf8" });
  assert.equal(serverCheck.status, 0, serverCheck.stderr);
});

test("repeated futures volume is left blank on the earlier session only", () => {
  const day = (iso, close, vol) => ({ sec: Math.floor(Date.parse(iso) / 1000), close: close, vol: vol });
  const days = [day("2026-11-04T05:00:00Z", 4073, 232561), day("2026-11-05T05:00:00Z", 4113.5, 232561), day("2026-11-06T05:00:00Z", 4073.5, 160887)];
  const chart = lib.c102Chart({
    chart: { result: [{
      meta: { symbol: "GC=F", shortName: "Gold Dec 26", instrumentType: "FUTURE", exchangeTimezoneName: "America/New_York", currency: "USD", fullExchangeName: "COMEX" },
      timestamp: days.map((d) => d.sec),
      indicators: { quote: [{ open: days.map((d) => d.close - 2), high: days.map((d) => d.close + 2), low: days.map((d) => d.close - 3), close: days.map((d) => d.close), volume: days.map((d) => d.vol) }] }
    }] }
  }, Date.parse("2026-11-06T16:00:00Z"));
  assert.equal(chart.excludedIncompleteSessions, 1);
  assert.equal(chart.bars.length, 2);
  assert.equal(chart.bars[0].sessionDate, "2026-11-04");
  assert.equal(chart.bars[0].volume, null);
  assert.equal(chart.bars[1].volume, 232561);
  assert.equal(chart.volumeRepeatsCleared, 1);
  assert.match(chart.barTimeNote, /not a settlement time/);
  assert.match(chart.barTimeNote, /04:00/);
  assert.match(chart.barTimeNote, /05:00/);
});

test("six-month window does not keep the older year on screen", () => {
  const context = { console: console, Intl: Intl, Date: Date };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c102.js"), "utf8"), context);
  const bars = [];
  for (let i = 0; i < 500; i++) {
    const d = new Date(Date.UTC(2024, 0, 1 + i));
    bars.push({ sessionDate: d.toISOString().slice(0, 10), c: 100 + i });
  }
  const six = context.c102ui.windowBars(bars, 6);
  const year = context.c102ui.windowBars(bars, 12);
  assert.ok(six[0].sessionDate > bars[0].sessionDate);
  assert.ok(six[0].sessionDate >= "2024-11-01");
  assert.equal(six[six.length - 1].sessionDate, bars[bars.length - 1].sessionDate);
  assert.ok(year.length > six.length);
  assert.ok(year[0].sessionDate < six[0].sessionDate);
});

test("dark theme uses the site hook and the live readout is not a second visible line", () => {
  const built = spawnSync(process.execPath, ["build_block.js"], { cwd: dir, encoding: "utf8" });
  assert.equal(built.status, 0, built.stderr);
  const css = require("./lib_c102.js").C102_CSS;
  assert.match(css, /\.c102-live\{position:absolute/);
  assert.equal(/\.c102-live\{[^}]*display:\s*none/.test(css), false);
  const ui = {};
  const context = { console: console, Intl: Intl, Date: Date, URL: URL };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c102.js"), "utf8"), context);
  const html = context.c102ui.render({ title: "Terminal", note: "A note." }, null);
  assert.equal((html.match(/id="c102-readout"/g) || []).length, 1);
  assert.equal((html.match(/id="c102-live"/g) || []).length, 1);
  assert.match(html, /id="c102-live" class="c102-live" aria-live="polite"/);
  assert.match(html, /data-c102-months="6" aria-pressed="true"/);
  assert.match(html, /href="\/dashboard\/"/);
  assert.match(html, /href="\/gold\/"/);
  const hooked = [];
  const box = {
    console: console, globalThis: {}, URL: URL, Date: Date, Map: Map, Promise: Promise, Intl: Intl,
    setTimeout: setTimeout, clearTimeout: clearTimeout,
    fetch: async () => ({ ok: false, status: 503 }),
    handle: async function () { return "pass"; },
    c97Hook: function (req) { hooked.push(req.url); },
    c93Shell: function (s) { return "<!doctype html><html><head></head><body><header class=\"site\"><nav><a href=\"/gold/\">Gold</a><a href=\"/dashboard/\">Dashboard</a><a href=\"/brief/\">Brief</a></nav></header><main>" + s.body + "</main></body></html>"; },
    c93Html: function (req, res, html) { res.end(html); }
  };
  box.globalThis = box;
  vm.createContext(box);
  vm.runInContext(fs.readFileSync(path.join(dir, "server_block_c102.js"), "utf8"), box);
  const res = { writeHead: function () {}, end: function (b) { res.body = b; } };
  return box.handle({ method: "GET", url: "/terminal/", headers: {} }, res).then(function () {
    assert.deepEqual(hooked, ["/terminal/"]);
    assert.match(res.body, />Gold</);
    assert.match(res.body, />Dashboard</);
    assert.match(res.body, />Brief</);
    assert.match(res.body, /c102-live/);
    assert.match(res.body, /aria-live/);
  });
});

test("session history is a labelled table and uses the UTC bar timestamp", () => {
  const context = { console: console, Intl: Intl, Date: Date };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c102.js"), "utf8"), context);
  const bars = [];
  for (let i = 0; i < 15; i++) {
    const day = String(i + 1).padStart(2, "0");
    bars.push({ sessionDate: "2026-10-" + day, timeUtc: "2026-10-" + day + "T05:00:00.000Z", o: 1, h: 2, l: 0.5, c: 1.5, volume: 100 + i });
  }
  bars[10].timeUtc = "2026-10-26T04:00:00.000Z";
  bars[10].sessionDate = "2026-10-26";
  const html = context.c102ui.tableHtml(bars, { exchangeTimezone: "America/New_York" });
  assert.match(html, /<table class="c102-ohlc">/);
  assert.match(html, /<caption>Latest 12 completed sessions/);
  assert.match(html, /<th scope="col">Open<\/th><th scope="col">High<\/th><th scope="col">Low<\/th><th scope="col">Close<\/th>/);
  assert.match(html, /Futures volume/);
  assert.match(html, /Not a settlement time/);
  assert.match(html, /05:00 UTC/);
  assert.match(html, /04:00 UTC/);
  assert.match(html, /America\/New_York/);
  assert.equal((html.match(/<tr>/g) || []).length, 13);
  assert.equal(html.includes("<article"), false);
  assert.equal(html.includes("October"), false);
  const one = context.c102ui.barStamp({ sessionDate: "2026-10-21", timeUtc: "2026-10-21T05:00:00.000Z" }, { exchangeTimezone: "America/New_York" });
  const read = context.c102ui.readout({ exchangeTimezone: "America/New_York" }, bars[0]);
  assert.match(one, /05:00 UTC/);
  assert.match(read, /05:00 UTC/);
  assert.match(read, /Not a settlement time/);
  const css = require("./lib_c102.js").C102_CSS;
  assert.match(css, /\.c102-table-scroll\{[^}]*overflow-x:auto/);
  assert.equal(css.includes("c101-inst"), false);
});

test("no stored theme preference stays on system and dark follows the OS media query", () => {
  const src = fs.readFileSync(path.join(dir, "..", "deploy-chat97", "server_block97.js"), "utf8");
  assert.match(src, /function c97SchemeOf\(req\) \{[\s\S]*return m \? m\[1\] : "system"/);
  assert.match(src, /@media \(prefers-color-scheme:dark\)\{" \+ block\("html\.c97-system"\)/);
  assert.match(src, /paper: "#151b23"/);
  const css = src.slice(src.indexOf("const C97_SITE_CSS"), src.indexOf("const C97_AUTH_CSS"));
  assert.match(css, /--paper:\$\{C97D\.paper\}/);
  const hook = fs.readFileSync(path.join(dir, "lib_c102.js"), "utf8");
  assert.match(hook, /if \(typeof c97Hook === "function"\) c97Hook\(req, res\)/);
  function schemeOf(cookie) {
    const m = /(?:^|;\s*)dispatch_theme=(light|dark|system)(?:;|$)/.exec(String(cookie || ""));
    return m ? m[1] : "system";
  }
  assert.equal(schemeOf(""), "system");
  assert.equal(schemeOf("dispatch_theme=dark"), "dark");
  assert.equal(schemeOf("other=1"), "system");
});

test("a hung feed is bounded and does not invent the readings that never answered", async () => {
  const t0 = Date.now();
  const model = await lib.c102Collect({
    fetch: async (url) => {
      const u = String(url);
      if (u.includes("XAU")) return { ok: true, json: async () => ({ symbol: "XAU", currency: "USD", price: 4100.25, updatedAt: "2026-11-06T15:23:00Z" }) };
      if (u.includes("XAG")) return { ok: true, json: async () => ({ symbol: "XAG", currency: "USD", price: 50, updatedAt: "2026-11-06T15:23:00Z" }) };
      return new Promise(() => {});
    },
    timeoutMs: 80,
    fred: () => new Promise(() => {}),
    calendar: () => new Promise(() => {}),
    goldDash: () => new Promise(() => {}),
    cnbc: () => new Promise(() => {})
  }, NOW);
  const dt = Date.now() - t0;
  assert.ok(dt < 500, "collect took " + dt);
  assert.equal(model.spot.status, "ok");
  assert.equal(model.spot.price, 4100.25);
  assert.match(model.spot.source, /gold-api/);
  assert.equal(model.nominalOfficial.status, "timeout");
  assert.equal(model.events.status, "timeout");
  assert.equal(model.nominalOfficial.value, undefined);
  assert.equal(model.dollar.price, undefined);
});

test("stored reading is served stale while one hung refresh is in flight", async () => {
  const store = new Map();
  let started = 0;
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  const producer = () => {
    started += 1;
    return gate.then(() => ({ status: "ok", spot: { status: "ok", price: 9999, source: "should-not-replace" } }));
  };
  store.set("snap-stale", { ok: true, at: Date.now() - 120000, body: { status: "ok", spot: { status: "ok", price: 4100.25, source: "gold-api.com", asOfUk: "Fri, 6 November 2026 at 15:23" }, generatedAtUtc: "2026-11-06T15:23:00.000Z" } });
  const t0 = Date.now();
  const a = await lib.c102Memo(store, "snap-stale", 1000, producer, () => lib.c102ColdSnap(NOW));
  const b = await lib.c102Memo(store, "snap-stale", 1000, producer, () => lib.c102ColdSnap(NOW));
  const dt = Date.now() - t0;
  assert.ok(dt < 250, "memo took " + dt);
  assert.equal(started, 1);
  assert.equal(a.body.cacheState, "stale");
  assert.equal(a.body.spot.price, 4100.25);
  assert.equal(a.body.spot.source, "gold-api.com");
  assert.match(a.body.cacheNote, /Stored reading from /);
  assert.match(a.body.cacheNote, /not a new print/);
  assert.equal(b.body.spot.price, 4100.25);
  assert.equal(JSON.stringify(a.body).includes("9999"), false);
  release();
  await new Promise((r) => setImmediate(r));
  const fresh = await lib.c102Memo(store, "snap-stale", 60 * 1000, producer, () => lib.c102ColdSnap(NOW));
  assert.equal(fresh.body.cacheState, "fresh");
  assert.equal(fresh.body.spot.price, 9999);
  assert.equal(fresh.body.cacheNote, undefined);
});

test("hung upstream does not delay /terminal/ html or the json routes", async () => {
  const pageSrc = fs.readFileSync(path.join(dir, "lib_c102.js"), "utf8");
  const pageFn = pageSrc.slice(pageSrc.indexOf("async function page"), pageSrc.indexOf("if (typeof handle"));
  assert.equal(pageFn.includes("c102Collect"), false);
  assert.equal(pageFn.includes("snapshot("), false);
  assert.equal(pageFn.includes("c102Get"), false);
  assert.equal(pageFn.includes("gold-api"), false);
  const built = spawnSync(process.execPath, ["build_block.js"], { cwd: dir, encoding: "utf8" });
  assert.equal(built.status, 0, built.stderr);
  let calls = 0;
  const box = {
    console: console, globalThis: {}, URL: URL, Date: Date, Map: Map, Promise: Promise, Intl: Intl,
    setTimeout: setTimeout, clearTimeout: clearTimeout, AbortController: AbortController,
    fetch: function (_url, opts) {
      calls += 1;
      return new Promise((_resolve, reject) => {
        const signal = opts && opts.signal;
        if (signal) signal.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
      });
    },
    handle: async function () { return "pass"; },
    c93Shell: function (s) { return "<!doctype html><title>Terminal</title>" + s.body; },
    c93Html: function (req, res, html) { res.end(html); }
  };
  box.globalThis = box;
  vm.createContext(box);
  vm.runInContext(fs.readFileSync(path.join(dir, "server_block_c102.js"), "utf8"), box);
  function ask(url) {
    const res = { writeHead: function (code, h) { res.code = code; res.headers = h; }, end: function (b) { res.body = b || ""; } };
    const t0 = Date.now();
    return box.handle({ method: "GET", url: url, headers: {} }, res).then(function () {
      res.ms = Date.now() - t0;
      return res;
    });
  }
  const html = await ask("/terminal/");
  const snap = await ask("/api/c102/terminal");
  const chart = await ask("/api/c102/chart");
  const again = await ask("/api/c102/terminal");
  await new Promise((r) => setImmediate(r));
  const after = calls;
  await ask("/api/c102/terminal");
  await ask("/api/c102/chart");
  await new Promise((r) => setImmediate(r));
  assert.ok(html.ms < 250, "html " + html.ms);
  assert.ok(snap.ms < 250, "snap " + snap.ms);
  assert.ok(chart.ms < 250, "chart " + chart.ms);
  assert.ok(again.ms < 250, "again " + again.ms);
  assert.match(html.body, /<section id="c102-mount" aria-busy="true"><p>Loading readings/);
  assert.equal(html.body.includes("4100"), false);
  const snapJson = JSON.parse(snap.body);
  const chartJson = JSON.parse(chart.body);
  assert.equal(snapJson.cacheState, "cold");
  assert.match(snapJson.cacheNote, /No stored reading yet/);
  assert.match(snapJson.cacheNote, /No number was filled in/);
  assert.equal(snapJson.spot.price, undefined);
  assert.equal(chartJson.cacheState, "cold");
  assert.equal(chartJson.bars, undefined);
  assert.match(chartJson.message, /No candles were filled in/);
  assert.equal(snap.headers["Cache-Control"], "no-store");
  assert.equal(calls, after);
  assert.ok(after > 0);
  const ui = { console: console, Intl: Intl, Date: Date };
  vm.createContext(ui);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c102.js"), "utf8"), ui);
  const shown = ui.c102ui.render({
    cacheNote: "Stored reading from 2026-11-09T15:00:00.000Z, 4 minutes ago. It was not refreshed for this response. It is not a new print.",
    generatedAtUtc: "2026-11-09T15:00:00.000Z",
    spot: { status: "ok", price: 4100.25, source: "gold-api.com", asOfUk: "Mon, 9 November 2026 at 15:00" }
  }, { cacheNote: "Stored chart from 2026-11-09T15:00:00.000Z. It is not a new print." });
  assert.match(shown, /not a new print/);
  assert.match(shown, /gold-api.com/);
  assert.match(shown, /4100\.25|4,100\.25/);
});

test("deploy.sh bytes match EXPECTED_SHA256 on their own", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  assert.ok(buf.length > 0);
});

test("bad project root is refused and mockup plus old backups stay untouched", () => {
  const root = fs.mkdtempSync("/tmp/c102-bad-");
  fs.writeFileSync(path.join(root, "server.js"), "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\nnope\n");
  fs.writeFileSync(path.join(root, "app.js"), "nope");
  fs.writeFileSync(path.join(root, "index.html"), "<html></html>");
  const bakDir = path.join(root, ".backups", "pre-bb8h-rt59");
  const mockDir = path.join(root, "artifacts", "mockup-sandbox");
  fs.mkdirSync(bakDir, { recursive: true });
  fs.mkdirSync(mockDir, { recursive: true });
  const bak = path.join(bakDir, "server.js");
  const mock = path.join(mockDir, "index.html");
  const oldBak = path.join(root, "server.js.20260101-000000.bak-chat102");
  fs.writeFileSync(bak, "backup-server");
  fs.writeFileSync(mock, "mock-index");
  fs.writeFileSync(oldBak, "previous-chat102-backup");
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  assert.notEqual(run.status, 0);
  assert.match(run.stdout, new RegExp("root server.js = " + root + "/server.js"));
  assert.match(run.stdout, new RegExp("root index.html = " + root + "/index.html"));
  assert.equal(run.stdout.includes("mockup-sandbox"), false);
  assert.equal(run.stdout.includes("pre-bb8h-rt59"), false);
  assert.equal(fs.readFileSync(bak, "utf8"), "backup-server");
  assert.equal(fs.readFileSync(mock, "utf8"), "mock-index");
  assert.equal(fs.readFileSync(oldBak, "utf8"), "previous-chat102-backup");
  assert.equal(fs.readFileSync(path.join(root, "server.js"), "utf8").includes("c102"), false);
});

test("remote payload is fetched and a lookalike first-chat102 root is not applied", () => {
  const appSrc = "/tmp/c102hash/app.js";
  assert.equal(fs.existsSync(appSrc), true, "patched chat102 app.js fixture missing");
  const oldBlock = require("child_process").execFileSync("git", ["-C", path.join(dir, ".."), "show", "d10d6b9:deploy-chat102/server_block_c102.js"]);
  const root = fs.mkdtempSync("/tmp/c102-r2-");
  const prefix = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\nfunction handle(){}\n";
  fs.writeFileSync(path.join(root, "server.js"), Buffer.concat([Buffer.from(prefix), oldBlock]));
  fs.copyFileSync(appSrc, path.join(root, "app.js"));
  const index = '<script src="/app.js?v=chat102"></script>\n';
  fs.writeFileSync(path.join(root, "index.html"), index);
  const mockDir = path.join(root, "artifacts", "mockup-sandbox");
  fs.mkdirSync(mockDir, { recursive: true });
  const mock = path.join(mockDir, "index.html");
  fs.writeFileSync(mock, "do-not-touch");
  const oldBak = path.join(root, "server.js.20260101-000000.bak-chat102");
  fs.writeFileSync(oldBak, "keep-me");
  const before = {
    server: fs.readFileSync(path.join(root, "server.js")),
    app: fs.readFileSync(path.join(root, "app.js")),
    index: fs.readFileSync(path.join(root, "index.html"))
  };
  const alone = fs.mkdtempSync("/tmp/c102-script-");
  fs.copyFileSync(path.join(dir, "deploy.sh"), path.join(alone, "deploy.sh"));
  const dry = spawnSync("bash", [path.join(alone, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(alone, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102\.js ([a-f0-9]{64})/) || [])[1];
  const out = dry.stdout + dry.stderr;
  assert.notEqual(dry.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, new RegExp("root server.js = " + root + "/server.js"));
  assert.equal(out.includes("mockup-sandbox"), false);
  assert.equal(out.includes("pre-bb8h"), false);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before.server);
  assert.deepEqual(fs.readFileSync(path.join(root, "app.js")), before.app);
  assert.equal(fs.readFileSync(path.join(root, "index.html"), "utf8"), index);
  assert.equal(fs.readFileSync(mock, "utf8"), "do-not-touch");
  assert.equal(fs.readFileSync(oldBak, "utf8"), "keep-me");
  assert.equal(fs.readdirSync(root).some((n) => /bak-chat102r\d/.test(n)), false);
});

test("deploy dry-run aborts when the live snapshot hash does not match chat101h", () => {
  const work = fs.mkdtempSync("/tmp/c102-deploy-");
  fs.writeFileSync(path.join(work, "server.js"), "const BB10I_MAINTENANCE_ON = false;\n");
  fs.writeFileSync(path.join(work, "app.js"), "nope");
  fs.writeFileSync(path.join(work, "index.html"), "<html></html>");
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", work], { encoding: "utf8" });
  assert.notEqual(run.status, 0);
  assert.match(run.stderr + run.stdout, /ABORT|md5|expected/);
  assert.equal(fs.readFileSync(path.join(work, "server.js"), "utf8").includes("c102"), false);
});
