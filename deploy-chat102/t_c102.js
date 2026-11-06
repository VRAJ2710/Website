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
