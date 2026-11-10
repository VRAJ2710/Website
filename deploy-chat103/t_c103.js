"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");
const lib = require("./lib_c103.js");

const dir = __dirname;
const NOW = Date.parse("2026-11-10T08:35:00.000Z");

test("ET to UK time across the two DST gaps", () => {
  const cases = [
    [2026, 12, 10, "2026-12-10T13:30:00.000Z", "13:30 GMT"],
    [2026, 7, 14, "2026-07-14T12:30:00.000Z", "13:30 BST"],
    [2026, 3, 11, "2026-03-11T12:30:00.000Z", "12:30 GMT"],
    [2026, 10, 28, "2026-10-28T12:30:00.000Z", "12:30 GMT"],
    [2026, 11, 10, "2026-11-10T13:30:00.000Z", "13:30 GMT"]
  ];
  for (const [y, m, d, utc, uk] of cases) {
    const when = lib.c103ZonedToUtc(y, m, d, 8, 30, "America/New_York");
    assert.equal(when.toISOString(), utc);
    assert.match(lib.c103FormatUk(when.getTime()), new RegExp(uk.replace(" ", "\\s")));
  }
});

test("m/m and y/y match the September 2026 BLS print", () => {
  assert.equal(lib.c103Round1(lib.c103Pct(336.298, 334.131)), 0.6);
  assert.equal(lib.c103Round1(lib.c103Pct(336.94, 324.8)), 3.7);
  assert.equal(lib.c103Round1(lib.c103Pct(338.896, 337.765)), 0.3);
  assert.equal(lib.c103Round1(lib.c103Pct(339.287, 330.804)), 2.6);
  assert.equal(lib.c103Round1(lib.c103Pct(182.176, 184.869)), -1.5);
  const months = lib.c103BuildMonths({
    CUSR0000SA0: [{ year: 2026, month: 8, value: 334.131 }, { year: 2026, month: 9, value: 336.298 }],
    CUUR0000SA0: [{ year: 2025, month: 9, value: 324.8 }, { year: 2026, month: 9, value: 336.94 }],
    CUSR0000SA0L1E: [{ year: 2026, month: 8, value: 337.765 }, { year: 2026, month: 9, value: 338.896 }],
    CUUR0000SA0L1E: [{ year: 2025, month: 9, value: 330.804 }, { year: 2026, month: 9, value: 339.287 }]
  }, null);
  const sep = months.find((row) => row.period === "2026-09");
  assert.equal(sep.headline.momRounded, 0.6);
  assert.equal(sep.headline.yoyRounded, 3.7);
  assert.equal(sep.core.momRounded, 0.3);
  assert.equal(sep.core.yoyRounded, 2.6);
});

test("a missing year-ago index is named and not replaced", () => {
  const series = {
    CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }, { year: 2026, month: 10, value: 337.643 }],
    CUUR0000SA0: [{ year: 2025, month: 9, value: 324.8 }, { year: 2026, month: 10, value: 338 }],
    CUSR0000SA0L1E: [{ year: 2026, month: 9, value: 338.896 }, { year: 2026, month: 10, value: 339.913 }],
    CUUR0000SA0L1E: [{ year: 2025, month: 9, value: 330.804 }, { year: 2026, month: 10, value: 341 }],
    CUSR0000SAH1: [{ year: 2026, month: 9, value: 100 }, { year: 2026, month: 10, value: 100.4 }],
    CUUR0000SAH1: [{ year: 2025, month: 9, value: 98 }, { year: 2026, month: 10, value: 101 }]
  };
  const months = lib.c103BuildMonths(series, { byName: { Shelter: 35.323 }, weightMonth: "Sep. 2026" });
  const oct = months.find((row) => row.period === "2026-10");
  assert.equal(oct.headline.momRounded, 0.4);
  assert.equal(oct.core.momRounded, 0.3);
  assert.equal(oct.headline.yoyRounded, null);
  assert.equal(oct.core.yoyRounded, null);
  assert.equal(oct.headline.yoy, null);
  assert.match(oct.headline.yoyNote, /Year-on-year not published: BLS has no October 2025 index because of the 2025 US government shutdown\./);
  assert.match(oct.core.yoyNote, /October 2025/);
  const shelter = oct.categories.find((row) => row.key === "shelter");
  assert.equal(shelter.yoyRounded, null);
  assert.equal(shelter.contribution, lib.c103Contribution(35.323, shelter.mom));
  assert.equal(shelter.contributionNote, "");
  const gap = lib.c103BuildMonths({
    CUSR0000SA0: [{ year: 2024, month: 3, value: 110 }],
    CUUR0000SA0: [{ year: 2022, month: 3, value: 90 }, { year: 2024, month: 3, value: 100 }]
  }, { byName: { "All items": 100 }, weightMonth: "Feb. 2024" });
  const mar = gap.find((row) => row.period === "2024-03");
  assert.equal(mar.headline.yoy, null);
  assert.match(mar.headline.yoyNote, /BLS has no March 2023 index\./);
  assert.equal(/shutdown/.test(mar.headline.yoyNote), false);
  assert.equal(mar.headline.contribution, null);
  assert.match(mar.headline.contributionNote, /February 2024/);
  const model = lib.c103Compose({
    series: { ok: true, series: series },
    ri: { ok: true, byName: { Shelter: 35.323 }, weightMonth: "Sep. 2026" },
    icsOk: false,
    htmlOk: false,
    hourly: [],
    daily: []
  }, Date.parse("2026-11-13T16:00:00.000Z"));
  const trend = model.trend.find((row) => row.period === "2026-10");
  const arch = model.archive.find((row) => row.period === "2026-10");
  assert.equal(trend.headlineYoy, null);
  assert.match(trend.headlineYoyNote, /October 2025/);
  assert.match(arch.headline.yoyNote, /October 2025/);
  const ui = { document: { documentElement: {} }, devicePixelRatio: 1, encodeURIComponent: encodeURIComponent };
  ui.getComputedStyle = () => ({ getPropertyValue: () => "" });
  vm.createContext(ui);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c103.js"), "utf8"), ui);
  const free = lib.c103Respond(model, { premium: false }, []);
  const html = ui.c103ui.render(free);
  assert.match(html, /Year-on-year not published: BLS has no October 2025 index because of the 2025 US government shutdown\./);
  assert.equal((html.match(/October 2025/g) || []).length >= 2, true);
  const premium = lib.c103Respond(model, { premium: true }, []);
  const member = ui.c103ui.render(premium);
  assert.match(member, /October 2025/);
  assert.match(member, /pp/);
  assert.equal(premium.categories.find((row) => row.key === "shelter").contribution, shelter.contribution);
});

test("contribution is the weight times the category change", () => {
  assert.equal(lib.c103Contribution(35.323, 0.4), 35.323 * 0.4 / 100);
  assert.equal(lib.c103Contribution(13.507, 0), 0);
  assert.equal(lib.c103Contribution(null, 0.4), null);
  const html = "<table><tr><th id=\"w\">Relative<br/>importance<br/>Aug.<br/>2026</th><th>Change</th></tr><tr><th>Shelter</th><td headers=\"w\">35.323</td><td>0.4</td></tr></table>";
  const ri = lib.c103ParseRi(html);
  assert.equal(ri.weightMonth, "Aug. 2026");
  assert.equal(ri.byName.Shelter, 35.323);
  const months = lib.c103BuildMonths({
    CUSR0000SAH1: [{ year: 2026, month: 8, value: 100 }, { year: 2026, month: 9, value: 100.4 }],
    CUUR0000SAH1: [{ year: 2025, month: 9, value: 100 }, { year: 2026, month: 9, value: 103 }]
  }, ri);
  const shelter = months.find((row) => row.period === "2026-09").categories.find((row) => row.key === "shelter");
  assert.equal(shelter.momRounded, 0.4);
  assert.equal(shelter.contribution, lib.c103Contribution(35.323, shelter.mom));
  assert.equal(shelter.contributionUnit, "pp");
  assert.match(shelter.weightMonth, /Aug/);
  assert.equal(shelter.contributionLabel, "approx. contribution, our calculation from BLS data");
});

test("premium fields are absent from the free response", () => {
  const full = lib.c103Compose({
    series: { ok: true, series: {
      CUSR0000SA0: [{ year: 2026, month: 8, value: 334.131 }, { year: 2026, month: 9, value: 336.298 }],
      CUUR0000SA0: [{ year: 2025, month: 9, value: 324.8 }, { year: 2026, month: 9, value: 336.94 }],
      CUSR0000SAH1: [{ year: 2026, month: 8, value: 100 }, { year: 2026, month: 9, value: 100.4 }],
      CUUR0000SAH1: [{ year: 2025, month: 9, value: 100 }, { year: 2026, month: 9, value: 103 }]
    } },
    ri: { ok: true, byName: { Shelter: 35.323 }, asOf: "Aug. 2026", citation: "Table 1" },
    icsOk: false,
    htmlOk: false,
    hourly: [{ startMs: 1, endMs: 2, close: 2000, timeUtc: "2026-09-10T12:00:00.000Z", sessionDate: "2026-09-10" }],
    daily: [],
    fetchedAt: "2026-11-10T08:00:00.000Z",
    snapshots: []
  }, NOW);
  full.categories[0].contribution = 4242.5;
  full.gold = [{ plus1hPct: 4242.5, sourceLabel: lib.C103_GOLD_LABEL }];
  const free = lib.c103Respond(full, { premium: false, signedIn: false }, []);
  const premium = lib.c103Respond(full, { premium: true, signedIn: true }, []);
  assert.equal(free.access, "free");
  assert.equal(Object.hasOwn(free, "categories"), false);
  assert.equal(Object.hasOwn(free, "contributions"), false);
  assert.equal(Object.hasOwn(free, "gold"), false);
  assert.equal(JSON.stringify(free).includes("4242.5"), false);
  assert.equal(JSON.stringify(free).includes("Shelter"), false);
  assert.equal(free.latest.headline.momRounded, 0.6);
  assert.equal(/CUSR|CUUR|momSeries|yoySeries/.test(JSON.stringify(free)), false);
  assert.equal(/CUSR|CUUR|momSeries|yoySeries/.test(JSON.stringify(premium)), false);
  assert.equal(premium.access, "premium");
  assert.equal(premium.categories[0].contribution, 4242.5);
  assert.equal(premium.goldLabel, "Gold futures (COMEX, front month), Yahoo Finance delayed");
  assert.equal(JSON.stringify(premium).includes("GC=F"), false);
  assert.equal(JSON.stringify(premium).toLowerCase().includes("spot"), false);
});

function hangRequest() {
  const reqs = [];
  function request() {
    const req = {
      destroyed: false,
      destroy() { this.destroyed = true; },
      setTimeout() {},
      on() {},
      write() {},
      end() {}
    };
    reqs.push(req);
    return req;
  }
  request.reqs = reqs;
  return request;
}

test("a hung upstream is aborted and does not invent a figure", async () => {
  const request = hangRequest();
  const t0 = Date.now();
  const model = await lib.c103Refresh({ request, timeoutMs: 80, apiKey: "" }, NOW, null);
  const dt = Date.now() - t0;
  assert.ok(dt < 500, "refresh took " + dt);
  assert.ok(request.reqs.length > 0);
  assert.ok(request.reqs.every((req) => req.destroyed));
  assert.equal(model.latest, null);
  assert.equal(model.statusNote, "not loaded yet");
  assert.equal(JSON.stringify(model.latest), "null");
  const free = lib.c103Respond(model, { premium: false, signedIn: false }, []);
  assert.equal(free.latest, null);
  assert.equal(JSON.stringify(free).includes("336.298"), false);
  assert.match(free.statusNote, /not loaded yet/);
});

test("a later timeout keeps the last good BLS print and the last good gold feed", async () => {
  const store = new Map();
  let hangBls = false;
  let hangHourly = false;
  const blsBody = JSON.stringify({
    status: "REQUEST_SUCCEEDED",
    Results: { series: [
      { seriesID: "CUSR0000SA0", data: [
        { year: "2026", period: "M08", value: "334.131" },
        { year: "2026", period: "M09", value: "336.298" }
      ] },
      { seriesID: "CUUR0000SA0", data: [
        { year: "2025", period: "M09", value: "324.800" },
        { year: "2026", period: "M09", value: "336.940" }
      ] }
    ] }
  });
  const hourly = JSON.stringify({
    chart: { result: [{
      meta: { symbol: ["GC", "=F"].join(""), instrumentType: "FUTURE", shortName: "Gold Dec 26", exchangeTimezoneName: "America/New_York" },
      timestamp: [Date.parse("2026-09-11T11:00:00.000Z") / 1000, Date.parse("2026-09-11T12:00:00.000Z") / 1000, Date.parse("2026-09-11T13:00:00.000Z") / 1000],
      indicators: { quote: [{ close: [2000, 2010, 2030] }] }
    }] }
  });
  const daily = JSON.stringify({
    chart: { result: [{
      meta: { symbol: ["GC", "=F"].join(""), instrumentType: "FUTURE", shortName: "Gold Dec 26", exchangeTimezoneName: "America/New_York" },
      timestamp: [Date.parse("2026-09-10T04:00:00.000Z") / 1000, Date.parse("2026-09-11T04:00:00.000Z") / 1000],
      indicators: { quote: [{ close: [1990, 2040] }] }
    }] }
  });
  const deps = {
    timeoutMs: 60,
    apiKey: "",
    fetch: async (url) => {
      const u = String(url);
      if (u.includes("timeseries") && hangBls) return new Promise(() => {});
      if (u.includes("interval=1h") && hangHourly) return new Promise(() => {});
      if (u.includes("timeseries")) return { ok: true, text: async () => blsBody };
      if (u.includes("interval=1h")) return { ok: true, text: async () => hourly };
      if (u.includes("interval=1d")) return { ok: true, text: async () => daily };
      if (u.includes(".ics")) return { ok: true, text: async () => "BEGIN:VEVENT\nSUMMARY:Consumer Price Index\nDTSTART;TZID=US-Eastern:20260911T083000\nEND:VEVENT\nBEGIN:VEVENT\nSUMMARY:Consumer Price Index\nDTSTART;TZID=US-Eastern:20261110T083000\nEND:VEVENT\nBEGIN:VEVENT\nSUMMARY:Producer Price Index\nDTSTART;TZID=US-Eastern:20261113T083000\nEND:VEVENT\n" };
      if (u.includes("cpi.t01")) return { ok: true, text: async () => "<tr><td>Shelter</td><td>35.323</td></tr>" };
      if (u.includes("cpi.htm")) return { ok: true, text: async () => "<tr><td>October 2026</td><td>Nov. 10, 2026</td><td>08:30 AM</td></tr>" };
      return { ok: false, status: 500, text: async () => "" };
    }
  };
  const producer = () => {
    const prev = store.get("cpi");
    return lib.c103Refresh(deps, NOW, prev && prev.body);
  };
  const cold = await lib.c103Memo(store, "cpi", 1000, producer, () => lib.c103Cold(NOW));
  assert.equal(cold.cacheState, "cold");
  assert.equal(cold.latest, null);
  await new Promise((r) => setTimeout(r, 250));
  const saved = store.get("cpi");
  assert.equal(saved.body.latest.headline.momRounded, 0.6);
  assert.equal(saved.body.latest.headline.yoyRounded, 3.7);
  assert.equal(saved.body.latest.fetchedAt, saved.body.fetchedAt || saved.body.latest.fetchedAt);
  const keptAt = saved.body.latest.fetchedAt;
  const keptGold = saved.body.gold.find((row) => row.hourlyAvailable);
  assert.ok(keptGold);
  assert.equal(keptGold.sourceLabel, "Gold futures (COMEX, front month), Yahoo Finance delayed");
  saved.at = Date.now() - 120000;
  hangBls = true;
  hangHourly = true;
  const t0 = Date.now();
  const stale = await lib.c103Memo(store, "cpi", 1000, producer, () => lib.c103Cold(NOW));
  assert.ok(Date.now() - t0 < 250, "stale read " + (Date.now() - t0));
  assert.equal(stale.latest.headline.momRounded, 0.6);
  await new Promise((r) => setTimeout(r, 300));
  const after = await lib.c103Memo(store, "cpi", 60 * 1000, producer, () => lib.c103Cold(NOW));
  assert.equal(after.latest.headline.momRounded, 0.6);
  assert.equal(after.latest.headline.yoyRounded, 3.7);
  assert.equal(after.latest.headline.source, "Source: U.S. Bureau of Labor Statistics");
  assert.equal(after.latest.fetchedAt, keptAt);
  assert.match(after.latest.headline.message, /Stored reading from /);
  assert.match(after.latest.headline.message, /not a new print/);
  assert.equal(after.latest.headline.message.includes("No number was filled in"), false);
  const gold = after.gold.find((row) => row.releaseAtUtc === keptGold.releaseAtUtc) || after.gold.find((row) => row.hourlyAvailable);
  assert.ok(gold);
  assert.equal(gold.plus1hPct, keptGold.plus1hPct);
  assert.equal(gold.anchorPrice, keptGold.anchorPrice);
  assert.match(gold.hourMessage, /not a new print/);
  assert.equal(String(gold.sourceLabel), "Gold futures (COMEX, front month), Yahoo Finance delayed");
});

test("DDL allows only the five new tables", () => {
  const sql = lib.C103_DDL.join("\n");
  assert.equal(lib.c103DdlAudit(sql).ok, true);
  assert.deepEqual(lib.c103DdlAudit(sql).tables.sort(), lib.C103_TABLES.slice().sort());
  assert.equal(lib.c103DdlAudit(sql + "\nALTER TABLE dispatch_users ADD COLUMN x int").ok, false);
  assert.equal(lib.c103DdlAudit("DROP TABLE cpi_releases").ok, false);
  assert.equal(lib.c103DdlAudit(sql + "\nCREATE TABLE IF NOT EXISTS dispatch_users (id INT)").ok, false);
  assert.equal(lib.c103DdlAudit(sql + "\nCREATE TABLE cpi_releases (id INT)").ok, false);
  const text = fs.readFileSync(path.join(dir, "lib_c103.js"), "utf8");
  assert.equal(/\bALTER\s+TABLE\b/i.test(text), false);
  assert.equal(/\bDROP\s+TABLE\b/i.test(text), false);
});

test("the menu keeps every existing link and adds CPI Day beside them", () => {
  const nav = [["/brief/", "Brief"], ["/gold/", "Gold"], ["/terminal/", "Terminal"], ["/markets/", "Markets"], ["/research/", "Research"], ["/methodology", "Methodology"], ["/about", "About"]];
  const groups = [
    ["Start", [["/", "Home"], ["/brief/", "Brief"], ["/playbook/", "Playbook"], ["/gold/", "Gold"]]],
    ["Desk", [["/dashboard/", "Dashboard"], ["/lab/", "Market Lab"], ["/signals/", "Signals"]]],
    ["Markets", [["/markets/", "Markets"], ["/screener/", "Screener"], ["/sectors/", "Sectors"], ["/heatmap/", "Heatmap"], ["/crypto/", "Crypto"]]],
    ["Research", [["/news/", "Newsroom"], ["/paper/", "Paper"], ["/research/", "Research"], ["/documents/", "Documents"], ["/geo/", "Geo Ops"]]],
    ["Book", [["/watchlist/", "Watchlist"], ["/portfolio/holdings/", "Portfolio"], ["/learn/", "Learn"]]],
    ["Gold and macro", [["/terminal/", "Terminal"], ["/gold/dashboard/", "Gold dashboard"], ["/calendar/", "Calendar"], ["/what-changed/", "What changed today"], ["/markets/yields/", "Yields"], ["/gold/positioning/", "Gold positioning"], ["/central-banks/", "Central banks"], ["/data-status/", "Data status"]]],
    ["Tools and filings", [["/tools/", "Tools"], ["/tools/verify/", "Verify this claim"], ["/tools/isa-sipp/", "ISA/SIPP planner"], ["/tools/scenario/", "Scenario simulator"], ["/alerts/", "Alerts"], ["/portfolio/", "Portfolio X-ray"], ["/research/filing-changes/", "Filing change detector"], ["/research/sec/", "Company filings"], ["/research/sec/screener/", "Filings screener"], ["/research/capital-sustainability", "Capital Sustainability Monitor"]]],
    ["About", [["/about", "About"], ["/pricing", "Pricing"], ["/free-brief/", "Free brief"], ["/methodology", "Methodology"], ["/editorial-standards", "Editorial standards"], ["/corrections", "Corrections"], ["/contact", "Contact"]]],
    ["Account", [["/settings/", "Settings"], ["/__admin", "Admin Console"]]]
  ];
  const before = lib.c103Paths(nav, groups);
  lib.c103InsertNav(nav, groups);
  const after = lib.c103Paths(nav, groups);
  assert.deepEqual(after.filter((p) => p !== "/cpi/"), before);
  assert.equal(nav[nav.findIndex((x) => x[0] === "/markets/") + 1][0], "/cpi/");
  assert.equal(nav.filter((x) => x[0] === "/research/").length, 1);
  const gold = groups.find((g) => g[0] === "Gold and macro")[1];
  assert.equal(gold[gold.findIndex((x) => x[0] === "/terminal/") + 1][0], "/cpi/");
  assert.equal(groups.find((g) => g[0] === "Account")[1].some((x) => x[0] === "/__admin"), true);
  assert.equal(gold.some((x) => x[0] === "/__admin"), false);
  const box = { C101B_GROUPS: JSON.parse(JSON.stringify(groups)), C93_NAV: nav.map((x) => x.slice()), C93_MENU: [] };
  box.window = box;
  box.location = { pathname: "/", replace() {} };
  box.sessionStorage = { getItem() { return null; }, setItem() {} };
  box.document = { getElementById() { return null; } };
  vm.createContext(box);
  vm.runInContext(fs.readFileSync(path.join(dir, "app_block_c103.js"), "utf8"), box);
  const clientPaths = [];
  box.C101B_GROUPS.forEach((g) => g[1].forEach((it) => clientPaths.push(it[1] || it[0])));
  before.forEach((p) => {
    const hit = clientPaths.includes(p) || box.C93_NAV.some((x) => x[0] === p) || box.C101B_GROUPS.some((g) => g[1].some((it) => it[0] === p || it[1] === p));
    assert.equal(hit, true, "missing " + p);
  });
  assert.ok(box.C101B_GROUPS.some((g) => g[1].some((it) => it[0] === "/cpi/" || it[1] === "/cpi/")));
  assert.ok(box.C101B_GROUPS.some((g) => g[0] === "Account" && g[1].some((it) => it[0] === "/__admin")));
  assert.equal(box.C101B_GROUPS.find((g) => g[0] === "Gold and macro")[1].some((it) => it[0] === "/__admin"), false);
});

test("deploy dry-run refuses a mismatched root and writes nothing", () => {
  const root = fs.mkdtempSync("/tmp/c103-bad-");
  fs.writeFileSync(path.join(root, "server.js"), "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\nnope\n");
  fs.writeFileSync(path.join(root, "app.js"), "nope");
  fs.writeFileSync(path.join(root, "index.html"), "<html></html>");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  assert.notEqual(run.status, 0);
  assert.match(run.stderr + run.stdout, /ABORT/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readdirSync(root).some((name) => name.includes("bak-chat103")), false);
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  assert.match(spec, /099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054/);
  assert.match(spec, /BASE_SERVER_MD5=67a9c7972e1d8880b78d38056ffa876f/);
  assert.match(spec, /BASE_APP_MD5=93644cb45fc3884e7068bf9a902d73e3/);
  assert.match(spec, /BASE_INDEX_MD5=338615e7ece511104855785b67e9c10a/);
});

test("chat103d replaces only the CPI block and leaves the r6c last write in place", () => {
  const root = fs.mkdtempSync("/tmp/c103-up-");
  const block = fs.readFileSync(path.join(dir, "../deploy-chat102/server_block_c102.js"), "utf8");
  const tail = "// chat102r6 market-reference cache.\nr6();\n// chat102r6b reader-facing scrub.\nr6b();\n// chat102r6c last-write scrub.\nproto.end = end;\nconsole.log(\"[c102r6c] scrub attached\");\n";
  const server = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\n" + block + "// chat103 cpi day. old\nold();\n" + tail;
  const app = "staged app bytes\n";
  const index = '<script src="/app.js?v=chat103c"></script>\n';
  fs.writeFileSync(path.join(root, "server.js"), server);
  fs.writeFileSync(path.join(root, "app.js"), app);
  fs.writeFileSync(path.join(root, "index.html"), index);
  const run = spawnSync("python3", [path.join(dir, "patch_c103.py"), path.join(root, "server.js"), path.join(root, "app.js"), path.join(root, "index.html"), path.join(dir, "server_block_c103.js")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr);
  const next = fs.readFileSync(path.join(root, "server.js"), "utf8");
  const cut = server.indexOf("\n// chat103 cpi day");
  assert.equal(next.slice(0, cut + 1), server.slice(0, cut + 1));
  assert.equal(next.slice(next.indexOf("\n// chat102r6 market-reference cache.")), "\n" + tail);
  assert.equal(next.slice(next.indexOf("\n// chat102r6c last-write scrub.")), "\n" + tail.slice(tail.indexOf("// chat102r6c")));
  assert.equal(next.split("proto.end = end").length, server.split("proto.end = end").length);
  assert.match(next.slice(cut, next.indexOf("\n// chat102r6 market-reference cache.")), /Year-on-year not published:/);
  const marker = "// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.";
  const kept = next.slice(next.indexOf(marker), next.indexOf("\n// chat103 cpi day") + 1);
  assert.equal(require("crypto").createHash("sha256").update(kept).digest("hex"), "099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054");
  assert.equal(fs.readFileSync(path.join(root, "app.js"), "utf8"), app);
  assert.equal(fs.readFileSync(path.join(root, "index.html"), "utf8"), index);
});

test("labelled fallback is used only when the schedule does not already have that date", () => {
  const ics = "BEGIN:VEVENT\nSUMMARY:Consumer Price Index\nDTSTART;TZID=US-Eastern:20261210T083000\nEND:VEVENT\n";
  const html = "<tr><td>December 2026</td><td>Jan. 13, 2027</td><td>08:30 AM</td></tr>";
  const events = lib.c103MergeSchedule(lib.c103ParseIcs(ics), lib.c103ParseHtmlSchedule(html));
  const dec = events.find((ev) => ev.etDate === "2026-12-10");
  const jan = events.find((ev) => ev.etDate === "2027-01-13");
  assert.equal(dec.source, "bls-ics");
  assert.equal(jan.source, "bls-html");
  assert.equal(jan.referencePeriod, "2026-12");
  const onlyFallback = lib.c103MergeSchedule([], []);
  assert.equal(onlyFallback.find((ev) => ev.etDate === "2027-01-13").source, "labelled-fallback");
});

test("BLS calls stay inside the keyless budget", () => {
  assert.equal(lib.c103BlsSeriesCap(""), 25);
  assert.equal(lib.c103BlsSeriesCap("key"), 50);
  const empty = lib.c103BlsPlan({ calls: 0, dayKey: "2026-11-10", lastBlsAt: 0 }, NOW, { apiKey: "", hasStored: false });
  assert.equal(empty.call, true);
  assert.equal(empty.reason, "empty");
  const daily = lib.c103BlsPlan({ calls: 2, dayKey: "2026-11-10", lastBlsAt: NOW - 60 * 60 * 1000 }, NOW, { apiKey: "", hasStored: true, inReleaseWindow: false, hasNewMonth: true });
  assert.equal(daily.call, false);
  assert.equal(daily.reason, "daily");
  const due = lib.c103BlsPlan({ calls: 2, dayKey: "2026-11-10", lastBlsAt: NOW - 25 * 3600 * 1000 }, NOW, { apiKey: "", hasStored: true });
  assert.equal(due.call, true);
  assert.equal(due.reason, "daily");
  const soon = lib.c103BlsPlan({ calls: 3, dayKey: "2026-11-10", lastBlsAt: NOW - 4 * 60 * 1000 }, NOW, { apiKey: "", hasStored: true, inReleaseWindow: true, hasNewMonth: false });
  assert.equal(soon.call, false);
  const poll = lib.c103BlsPlan({ calls: 3, dayKey: "2026-11-10", lastBlsAt: NOW - 6 * 60 * 1000 }, NOW, { apiKey: "", hasStored: true, inReleaseWindow: true, hasNewMonth: false });
  assert.equal(poll.call, true);
  assert.equal(poll.batches, 1);
  assert.equal(poll.batch, 25);
  const keyed = lib.c103BlsPlan({ calls: 3, dayKey: "2026-11-10", lastBlsAt: NOW - 6 * 60 * 1000 }, NOW, { apiKey: "present", hasStored: true, inReleaseWindow: true, hasNewMonth: false });
  assert.equal(keyed.batch, 50);
  assert.equal(keyed.cap, 500);
  const stopped = lib.c103BlsPlan({ calls: 20, dayKey: "2026-11-10", lastBlsAt: NOW - 60 * 60 * 1000 }, NOW, { apiKey: "", hasStored: false });
  assert.equal(stopped.call, false);
  assert.equal(stopped.reason, "budget");
  const charged = lib.c103BlsCharge(poll, 1, NOW);
  assert.equal(charged.calls, 4);
});

test("countdown is recomputed and the cache stops at the release", () => {
  const release = lib.c103ReleaseInstant(2026, 11, 10, 8, 30);
  const later = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  const model = { previousEvents: [release, later], latest: { period: "2026-09" } };
  const before = release.startMs - 30 * 1000;
  assert.ok(lib.c103CacheMs(model, before) <= 30 * 1000);
  const shown = lib.c103ForNow(model, before);
  assert.equal(shown.countdown.releaseAtUtc, release.releaseAtUtc);
  const after = release.startMs + 60 * 1000;
  assert.equal(lib.c103CacheMs(model, after), 60 * 1000);
  const moved = lib.c103ForNow(model, after);
  assert.equal(moved.countdown.releaseAtUtc, later.releaseAtUtc);
  const period = release.referencePeriod;
  const [ys, ms] = period.split("-");
  const point = [{ year: Number(ys), month: Number(ms), value: 1 }];
  const series = {};
  lib.C103_CATALOG.forEach((row) => { series[row[2]] = point; series[row[3]] = point; });
  const arrived = { previousEvents: [release, later], latest: { period: period }, previousSeries: series, previousRi: { weightMonth: "Sep. 2026" } };
  assert.ok(lib.c103CacheMs(arrived, after) > 60 * 1000);
});

test("the cache stays at 60s until the second batch and the weights catch up", () => {
  const release = lib.c103ReleaseInstant(2026, 11, 10, 8, 30);
  const later = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  const period = release.referencePeriod;
  const [ys, ms] = period.split("-");
  const point = [{ year: Number(ys), month: Number(ms), value: 1 }];
  const series = {};
  lib.C103_CATALOG.forEach((row) => { series[row[2]] = point; series[row[3]] = point; });
  const at = release.startMs + 2 * 60 * 1000;
  const partial = Object.assign({}, series);
  delete partial[lib.C103_CATALOG[lib.C103_CATALOG.length - 1][2]];
  const pendingBatch = { previousEvents: [release, later], latest: { period: period }, previousSeries: partial, previousRi: { weightMonth: "Sep. 2026" } };
  assert.equal(lib.c103CacheMs(pendingBatch, at), 60 * 1000);
  const pendingWeights = { previousEvents: [release, later], latest: { period: period }, previousSeries: series, previousRi: { weightMonth: "Aug. 2026" } };
  assert.equal(lib.c103CacheMs(pendingWeights, at), 60 * 1000);
  const held = lib.c103BlsPlan({ calls: 4, dayKey: "2026-11-10", lastBlsAt: at - 60 * 1000 }, at, { apiKey: "", hasStored: true, inReleaseWindow: true, hasNewMonth: true, needsSecondBatch: true });
  assert.equal(held.call, false);
  assert.equal(held.reason, "poll-wait");
  const once = lib.c103BlsPlan({ calls: 4, dayKey: "2026-11-10", lastBlsAt: at - 6 * 60 * 1000 }, at, { apiKey: "", hasStored: true, inReleaseWindow: true, hasNewMonth: true, needsSecondBatch: true });
  assert.equal(once.call, true);
  assert.equal(once.batches, 1);
  assert.equal(once.offset, 25);
});

test("relative importance uses the weight column and the prior month", () => {
  const html = fs.readFileSync(path.join(dir, "fixture_ri_excerpt.html"), "utf8");
  const ri = lib.c103ParseRi(html);
  assert.equal(ri.byName["Food away from home"], 5.304);
  assert.equal(ri.byName["Medical care commodities"], 1.396);
  assert.equal(ri.byName["Owners' equivalent rent of residences"], 25.902);
  assert.equal(ri.weightMonth, "Aug. 2026");
  assert.equal(lib.c103WeightsMatch("Aug. 2026", "2026-09"), true);
  assert.equal(lib.c103WeightsMatch("Jul. 2026", "2026-09"), false);
  const months = lib.c103BuildMonths({
    CUSR0000SEHC: [{ year: 2026, month: 8, value: 100 }, { year: 2026, month: 9, value: 100.4 }],
    CUUR0000SEHC: [{ year: 2025, month: 9, value: 100 }, { year: 2026, month: 9, value: 103 }]
  }, Object.assign({}, ri, { weightMonth: "Jul. 2026", asOf: "Jul. 2026" }));
  const oer = months.find((row) => row.period === "2026-09").categories.find((row) => row.key === "oer");
  assert.equal(oer.contribution, null);
  assert.match(oer.contributionNote, /not shown/);
});

test("an empty schedule parse keeps the last good dates", () => {
  const kept = [lib.c103ReleaseInstant(2026, 12, 10, 8, 30)];
  kept[0].source = "bls-ics";
  const model = lib.c103Compose({
    series: { ok: false, series: {} },
    previousSeries: {},
    previousEvents: kept,
    icsOk: true,
    ics: [],
    htmlOk: true,
    html: [],
    hourly: [],
    daily: []
  }, NOW);
  assert.ok(model.previousEvents.some((ev) => ev.etDate === "2026-12-10" && ev.source === "bls-ics"));
});

test("gold day moves use the prior session and the hour label is not a raw timestamp", () => {
  const release = lib.c103ReleaseInstant(2026, 9, 11, 8, 30);
  const hourly = [
    { startMs: Date.parse("2026-09-11T11:00:00.000Z"), endMs: Date.parse("2026-09-11T12:00:00.000Z"), close: 2000, sessionDate: "2026-09-11" },
    { startMs: Date.parse("2026-09-11T13:00:00.000Z"), endMs: Date.parse("2026-09-11T14:00:00.000Z"), close: 2030, sessionDate: "2026-09-11" },
    { startMs: NOW, endMs: NOW + 3600000, close: 9999, sessionDate: "2026-11-10" }
  ];
  const daily = [
    { startMs: 1, endMs: 2, close: 1900, open: 1890, sessionDate: "2026-09-10" },
    { startMs: 3, endMs: 4, close: 2100, open: 1940, sessionDate: "2026-09-11" }
  ];
  const row = lib.c103GoldReaction(release, hourly, daily, NOW);
  assert.equal(row.dayAnchorLabel, "prior session close");
  assert.equal(row.plus1dPct, lib.c103Pct(2100, 1900));
  assert.match(row.hourLabel, /ET \(hourly bars\)/);
  assert.equal(/\d{4}-\d{2}-\d{2}T/.test(row.hourLabel + row.anchorUk), false);
  assert.match(row.rollNote, /contract roll/);
  const ui = { document: { documentElement: { } }, devicePixelRatio: 1, encodeURIComponent: encodeURIComponent };
  ui.getComputedStyle = () => ({ getPropertyValue: () => "" });
  vm.createContext(ui);
  vm.runInContext(fs.readFileSync(path.join(dir, "client_c103.js"), "utf8"), ui);
  const html = ui.c103ui.render({
    access: "premium",
    source: "Source: U.S. Bureau of Labor Statistics",
    countdown: { releaseAtUtc: "2026-12-10T13:30:00.000Z", releaseUk: "Thu, 10 December 2026 at 13:30 GMT", zoneName: "GMT", days: 30, hours: 0, minutes: 0, what: "Time left until the next US CPI news release.", why: "The clock is in UK time.", referenceLabel: "December 2026", source: "bls-ics" },
    latest: { periodLabel: "September 2026", headline: { momRounded: 0.6, yoyRounded: 3.7, saIndex: 1, nsaIndex: 1, momSeries: "CUSR0000SA0", yoySeries: "CUUR0000SA0", why: "Broad index.", source: "Source: U.S. Bureau of Labor Statistics" }, core: { momRounded: 0.3, yoyRounded: 2.6, saIndex: 1, nsaIndex: 1, why: "Slower part.", source: "Source: U.S. Bureau of Labor Statistics" } },
    categories: [{ name: "Shelter", why: "Largest weight.", momRounded: 0.4, yoyRounded: 3.2, weight: 35.323, weightMonth: "Aug. 2026", contribution: 0.14, contributionNote: "", momSeries: "CUSR0000SAH1" }],
    gold: [row],
    relativeImportance: { citation: "https://www.bls.gov/news.release/cpi.t01.htm" }
  });
  assert.match(html, /BLS data/);
  assert.equal(/CUSR0000|CUUR0000/.test(html), false);
  assert.match(html, /prior session close/);
  assert.match(html, /href="https:\/\/www\.bls\.gov\/cpi\/"/);
  assert.equal(/GMT \(GMT\)/.test(html), false);
  assert.equal((html.match(/13:30 GMT/g) || []).length, 1);
  const summer = ui.c103ui.render({ countdown: { releaseAtUtc: "2026-07-14T12:30:00.000Z", releaseUk: lib.c103FormatUk(Date.parse("2026-07-14T12:30:00.000Z")), zoneName: "GMT", days: 1, hours: 2, minutes: 3, what: "Time left", why: "UK time", referenceLabel: "June 2026", source: "bls-ics" } });
  assert.match(summer, /13:30 BST/);
  assert.equal(/BST \(BST\)|GMT \(GMT\)/.test(summer), false);
  assert.match(html, /Core, dashed/);
  assert.equal(html.includes("2026-09-11T"), false);
});

test("dismiss accepts only a known release from this site", () => {
  const known = ["2026-11-10T13:30:00.000Z"];
  const limiter = { allow: () => true };
  const badOrigin = lib.c103DismissGate({ headers: { origin: "https://evil.example", "content-type": "application/json" } }, known[0], known, limiter, NOW, "u1");
  assert.equal(badOrigin.status, 403);
  const badType = lib.c103DismissGate({ headers: { origin: "https://thedispatch.uk", "content-type": "text/plain" } }, known[0], known, limiter, NOW, "u1");
  assert.equal(badType.status, 415);
  const unknown = lib.c103DismissGate({ headers: { origin: "https://thedispatch.uk", "content-type": "application/json" } }, "2020-01-01T00:00:00.000Z", known, limiter, NOW, "u1");
  assert.equal(unknown.status, 400);
  let calls = 0;
  const limited = { allow: () => { calls += 1; return calls < 2; } };
  const ok = lib.c103DismissGate({ headers: { origin: "https://thedispatch.uk", "content-type": "application/json" } }, known[0], known, limited, NOW, "u1");
  assert.equal(ok.ok, true);
  const blocked = lib.c103DismissGate({ headers: { origin: "https://thedispatch.uk", "content-type": "application/json" } }, known[0], known, limited, NOW, "u1");
  assert.equal(blocked.status, 429);
});

test("the recorder uses a fresh bar only inside a release window on or after 10 Dec", async () => {
  const early = await lib.c103RecordTick({ events: [], fetch: async () => { throw new Error("no"); } }, Date.parse("2026-11-10T13:00:00.000Z"));
  assert.equal(early, null);
  const release = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  const barEnd = release.startMs - 5 * 60 * 1000;
  const payload = {
    chart: { result: [{
      meta: { symbol: "GC=F", instrumentType: "FUTURE", shortName: "Gold", exchangeTimezoneName: "America/New_York" },
      timestamp: [(barEnd - 5 * 60 * 1000) / 1000],
      indicators: { quote: [{ close: [4100], open: [4090] }] }
    }] }
  };
  const snap = await lib.c103RecordTick({
    events: [release],
    timeoutMs: 1000,
    fetch: async () => ({ ok: true, text: async () => JSON.stringify(payload) })
  }, release.startMs - 2 * 60 * 1000);
  assert.equal(snap.windowKind, "pre");
  assert.equal(snap.price, 4100);
  assert.equal(snap.sourceLabel, "Gold futures (COMEX, front month), Yahoo Finance delayed");
});

test("stored gold stays when the schedule no longer lists that release", () => {
  const old = { releaseAtUtc: "2024-06-12T12:30:00.000Z", releaseUk: "Wed, 12 June 2024 at 13:30 BST", plus1dPct: 0.4, sourceLabel: lib.C103_GOLD_LABEL };
  const model = lib.c103Compose({
    series: { ok: false },
    previousEvents: [],
    storedGold: [old],
    hourly: [],
    daily: [],
    icsOk: false,
    htmlOk: false
  }, NOW);
  assert.ok(model.gold.some((row) => row.releaseAtUtc === old.releaseAtUtc && row.plus1dPct === 0.4));
});

test("a restart after the release refetches the missing month without burning a failed call", async () => {
  const release = lib.c103ReleaseInstant(2026, 11, 10, 8, 30);
  release.source = "bls-ics";
  const at = Date.parse("2026-11-10T16:45:00.000Z");
  const previous = {
    latest: { period: "2026-09", periodLabel: "September 2026", fetchedAt: "2026-11-10T14:00:00.000Z", headline: { momRounded: 0.6, saIndex: 336.298 } },
    previousSeries: { CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }, { year: 2026, month: 8, value: 334.131 }], CUUR0000SA0: [{ year: 2026, month: 9, value: 336.94 }, { year: 2025, month: 9, value: 324.8 }] },
    previousEvents: [release],
    feedTimes: { schedule: "2026-11-10T12:00:00.000Z", bls: "2026-11-10T14:00:00.000Z" },
    blsBudget: { dayKey: "2026-11-10", calls: 4, lastBlsAt: at - 11 * 60 * 1000 }
  };
  const plan = lib.c103BlsPlan(previous.blsBudget, at, { apiKey: "", hasStored: true, missingReleaseMonth: true });
  assert.equal(plan.call, true);
  assert.equal(plan.reason, "missing-month");
  assert.equal(plan.batches, 1);
  const held = lib.c103BlsCharge(plan, 0, at);
  assert.equal(held.calls, 4);
  assert.equal(held.lastBlsAt, previous.blsBudget.lastBlsAt);
  const stopped = lib.c103BlsPlan({ dayKey: "2026-11-10", calls: 20, lastBlsAt: at - 60 * 60 * 1000 }, at, { apiKey: "", hasStored: true, missingReleaseMonth: true });
  assert.equal(stopped.call, false);
  assert.equal(stopped.reason, "budget");
  let calls = 0;
  const body = await lib.c103Refresh({
    timeoutMs: 1000,
    blsBudget: previous.blsBudget,
    fetch: async (url) => {
      calls += String(url).includes("api.bls.gov") ? 1 : 0;
      if (String(url).includes("api.bls.gov")) {
        return { ok: true, status: 200, text: async () => JSON.stringify({ status: "REQUEST_SUCCEEDED", Results: { series: [
          { seriesID: "CUSR0000SA0", data: [{ year: "2026", period: "M10", value: "337.643" }, { year: "2026", period: "M09", value: "336.298" }] },
          { seriesID: "CUUR0000SA0", data: [{ year: "2026", period: "M10", value: "338" }, { year: "2026", period: "M09", value: "336.94" }, { year: "2025", period: "M09", value: "324.8" }] }
        ] } }) };
      }
      return { ok: false, status: 500, text: async () => "" };
    }
  }, at, previous);
  assert.equal(calls, 1);
  assert.equal(body.latest.period, "2026-10");
  assert.equal(body.latest.headline.momRounded, 0.4);
  assert.equal(body.blsBudget.calls, 5);
  assert.match(body.latest.headline.yoyNote, /October 2025/);
});

test("an older BLS response does not replace a newer stored month", () => {
  const newer = { CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }, { year: 2026, month: 10, value: 337.643 }], CUUR0000SA0: [{ year: 2026, month: 10, value: 338 }, { year: 2026, month: 9, value: 336.94 }] };
  const older = { CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }], CUUR0000SA0: [{ year: 2026, month: 9, value: 336.94 }, { year: 2025, month: 9, value: 324.8 }] };
  const model = lib.c103Compose({
    series: { ok: true, series: older },
    previousSeries: newer,
    icsOk: false,
    htmlOk: false,
    hourly: [],
    daily: []
  }, Date.parse("2026-11-10T16:45:00.000Z"));
  assert.equal(model.latest.period, "2026-10");
  assert.equal(model.latest.headline.momRounded, 0.4);
  assert.equal(model.seriesFresh, false);
  const rows = lib.c103ChangedSeries(newer, model.previousSeries);
  assert.equal(rows.some((row) => row.period === "2026-10" && row.value !== 337.643), false);
});

test("a missing second batch is requested and the first batch's month stays", () => {
  const at = Date.parse("2026-11-10T18:00:00.000Z");
  const release = lib.c103ReleaseInstant(2026, 11, 10, 8, 30);
  release.source = "bls-ics";
  const series = {};
  lib.C103_CATALOG.forEach((row, index) => {
    const points = [{ year: 2026, month: 9, value: 100 + index }, { year: 2026, month: 8, value: 99 + index }];
    if (index < 12) points.push({ year: 2026, month: 10, value: 101 + index });
    series[row[2]] = points;
    series[row[3]] = points.slice();
  });
  const previous = { latest: { period: "2026-10" }, previousSeries: series, previousEvents: [release], blsBudget: { dayKey: "2026-11-10", calls: 3, lastBlsAt: at - 6 * 60 * 1000 } };
  const plan = lib.c103BlsPlan(previous.blsBudget, at, { apiKey: "", hasStored: true, hasNewMonth: true, needsSecondBatch: true });
  assert.equal(plan.reason, "second-batch");
  assert.equal(plan.offset, 25);
  assert.equal(plan.batches, 1);
  const kept = lib.c103Compose({ series: { ok: false }, previousSeries: series, previousEvents: [release], icsOk: false, htmlOk: false, hourly: [], daily: [] }, at);
  assert.equal(kept.latest.period, "2026-10");
  assert.equal(typeof kept.latest.headline.saIndex, "number");
});

test("only changed series values are written", () => {
  const prev = { CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }] };
  const next = { CUSR0000SA0: [{ year: 2026, month: 9, value: 336.298 }, { year: 2026, month: 10, value: 337 }] };
  const rows = lib.c103ChangedSeries(prev, next);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].period, "2026-10");
});

test("CPI Day is added in the same in-app menu group as Terminal", () => {
  const menu = [["Markets and data", [["/terminal/", "Terminal", "Futures"], ["/markets/", "Markets", "Prices"]]]];
  const before = menu[0][1].map((it) => it[0]);
  const box = { C93_MENU: menu, window: {}, location: { pathname: "/" }, sessionStorage: { getItem() { return null; }, setItem() {} }, document: { getElementById() { return null; } } };
  box.window = box;
  vm.createContext(box);
  vm.runInContext(fs.readFileSync(path.join(dir, "app_block_c103.js"), "utf8"), box);
  const paths = box.C93_MENU[0][1].map((it) => it[0]);
  assert.deepEqual(paths.filter((p) => p !== "/cpi/"), before);
  assert.equal(paths[paths.indexOf("/terminal/") + 1], "/cpi/");
});

test("archive dates older than the ICS are daily-only", () => {
  const html = '<a href="/news.release/archives/cpi_01122022.htm">January 2022</a><a href="/news.release/archives/cpi_10142026.htm">October 2026</a>';
  const rows = lib.c103ParseArchive(html, NOW);
  assert.ok(rows.some((row) => row.etDate === "2022-01-12" && row.dailyOnly && row.source === "bls-archive"));
  assert.ok(rows.some((row) => row.etDate === "2026-10-14"));
  const ancient = lib.c103ParseArchive('<a href="/news.release/archives/cpi_02152008.htm">old</a>', NOW);
  assert.equal(ancient.length, 0);
});

test("an archive duplicate does not replace an ICS release or its intraday figure", () => {
  const ics = lib.c103ReleaseInstant(2026, 1, 14, 8, 30);
  ics.source = "bls-ics";
  const archive = Object.assign({}, ics, { source: "bls-archive", dailyOnly: true });
  const hourly = [{ startMs: ics.startMs - 3600000, endMs: ics.startMs - 60 * 1000, close: 2000, sessionDate: "2026-01-14" }, { startMs: ics.startMs, endMs: ics.startMs + 3600000, close: 2060, sessionDate: "2026-01-14" }];
  const model = lib.c103Compose({
    series: { ok: false },
    icsOk: true,
    ics: [ics],
    htmlOk: false,
    archiveOk: true,
    archive: [archive],
    hourly: hourly,
    daily: [{ startMs: 1, endMs: 2, close: 1900, open: 1900, sessionDate: "2026-01-13" }, { startMs: 3, endMs: 4, close: 2100, open: 1910, sessionDate: "2026-01-14" }],
    storedGold: [{ releaseAtUtc: ics.releaseAtUtc, plus1hPct: 1.25, hourlyAvailable: true, hourLabel: "08:00\u219210:00 ET (hourly bars)", sourceLabel: lib.C103_GOLD_LABEL }]
  }, Date.parse("2026-11-10T16:00:00.000Z"));
  const ev = model.previousEvents.find((row) => row.etDate === ics.etDate);
  assert.equal(ev.source, "bls-ics");
  assert.equal(ev.dailyOnly, undefined);
  const gold = model.gold.find((row) => row.releaseAtUtc === ics.releaseAtUtc);
  assert.equal(gold.hourlyAvailable, true);
  assert.equal(typeof gold.plus1hPct, "number");
  assert.match(gold.hourLabel, /hourly bars/);
  const kept = lib.c103Compose({
    series: { ok: false },
    icsOk: true,
    ics: [ics],
    htmlOk: false,
    archiveOk: true,
    archive: [archive],
    hourly: [],
    daily: [],
    storedGold: [{ releaseAtUtc: ics.releaseAtUtc, plus1hPct: 1.25, hourlyAvailable: true, hourLabel: "08:00\u219210:00 ET (hourly bars)", sourceLabel: lib.C103_GOLD_LABEL }]
  }, Date.parse("2026-11-10T16:00:00.000Z"));
  const stored = kept.gold.find((row) => row.releaseAtUtc === ics.releaseAtUtc);
  assert.equal(stored.plus1hPct, 1.25);
  assert.equal(stored.hourlyAvailable, true);
  assert.match(stored.hourLabel, /hourly bars/);
});

test("the second BLS batch and Table 1 run once the new month is in", () => {
  const second = lib.c103BlsPlan({ calls: 4, dayKey: "2026-11-10", lastBlsAt: NOW - 6 * 60 * 1000 }, NOW, { apiKey: "", hasStored: true, inReleaseWindow: true, hasNewMonth: true, needsSecondBatch: true });
  assert.equal(second.reason, "second-batch");
  assert.equal(second.batches, 1);
  assert.equal(second.offset, 25);
  assert.equal(second.batch, 25);
});

test("a restart keeps the stored schedule and is stale enough to refresh", async () => {
  const release = lib.c103ReleaseInstant(2026, 11, 10, 8, 30);
  release.source = "bls-ics";
  const fetchedAt = "2026-11-09T18:00:00.000Z";
  const sql = async () => [];
  sql.query = async (text) => {
    if (text.includes("__schedule")) return [{ data: [{ payload: { events: [release], fetchedAt: fetchedAt }, bls_fetched_at: fetchedAt }] }];
    if (text.includes("^[0-9]{4}")) return [{ data: [{ period: "2026-09", bls_fetched_at: fetchedAt }] }];
    if (text.includes("cpi_series_values")) return [{ data: [{ series_id: "CUSR0000SA0", period: "2026-09", value: 336.298 }, { series_id: "CUUR0000SA0", period: "2026-09", value: 336.94 }, { series_id: "CUUR0000SA0", period: "2025-09", value: 324.8 }] }];
    if (text.includes("hour_label")) return [{ data: [{ release_at: release.releaseAtUtc, reference_period: "2026-10", plus_1h_pct: 0.4, plus_1d_pct: null, plus_5d_pct: null, hourly_available: true, recorded: false, hour_label: "08:00\u219210:00 ET (hourly bars)", source_label: lib.C103_GOLD_LABEL }] }];
    return [{ data: [] }];
  };
  const loaded = await lib.c103LoadStored({ sql: sql });
  assert.equal(loaded.latest.fetchedAt, fetchedAt);
  assert.ok(loaded.previousEvents.some((ev) => ev.etDate === "2026-11-10" && ev.source === "bls-ics"));
  assert.equal(loaded.storedGold[0].hourLabel, "08:00\u219210:00 ET (hourly bars)");
  const at = Date.parse("2026-11-10T13:25:00.000Z");
  const view = lib.c103ForNow(loaded, at);
  assert.equal(view.countdown.releaseAtUtc, release.releaseAtUtc);
  const store = new Map();
  store.set("m", { ok: true, at: 0, body: loaded });
  let started = 0;
  await lib.c103Memo(store, "m", (body) => lib.c103CacheMs(body, at), () => { started += 1; return loaded; }, () => lib.c103Cold(at));
  assert.equal(started, 1);
});

test("the post snapshot is the bar nearest an hour after the release", async () => {
  const release = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  const target = release.startMs + 60 * 60 * 1000;
  function bar(deltaMin, close) {
    const end = target + deltaMin * 60 * 1000;
    return { t: (end - 5 * 60 * 1000) / 1000, c: close };
  }
  const payload = {
    chart: { result: [{
      meta: { symbol: "GC=F", instrumentType: "FUTURE", shortName: "Gold", exchangeTimezoneName: "America/New_York" },
      timestamp: [bar(-30, 4000).t, bar(0, 4100).t, bar(30, 4200).t],
      indicators: { quote: [{ close: [4000, 4100, 4200], open: [3990, 4090, 4190] }] }
    }] }
  };
  const at90 = target + 30 * 60 * 1000;
  const late = await lib.c103RecordTick({ events: [release], timeoutMs: 1000, fetch: async () => ({ ok: true, text: async () => JSON.stringify(payload) }) }, at90);
  assert.equal(late, null);
  const at62 = target + 2 * 60 * 1000;
  const post = await lib.c103RecordTick({ events: [release], timeoutMs: 1000, fetch: async () => ({ ok: true, text: async () => JSON.stringify(payload) }) }, at62);
  assert.equal(post.windowKind, "post");
  assert.equal(post.price, 4100);
  assert.match(lib.c103FormatUk(Date.parse(post.observedAtUtc)), /GMT|BST/);
});

test("CPI CSS uses only variables the server pages define", () => {
  const src = fs.readFileSync(path.join(dir, "lib_c103.js"), "utf8");
  const css = src.slice(src.indexOf("<style"), src.indexOf("</style>"));
  const allowed = new Set(["--paper", "--ink", "--muted", "--rule", "--accent", "--down", "--up", "--amber", "--serif", "--sans"]);
  const used = [...css.matchAll(/var\(\s*(--[a-z0-9-]+)/g)].map((m) => m[1]);
  used.forEach((name) => assert.equal(allowed.has(name), true, name));
  assert.ok(css.includes("var(--up)"));
  assert.ok(css.includes("var(--amber)"));
  assert.equal(css.includes("--gold"), false);
  assert.equal(css.includes("--pos"), false);
  assert.match(css, /header\.site \.nav\{flex:1 1 0;flex-wrap:wrap/);
  assert.equal(/header\.site \.nav\{display:none/.test(css), false);
  const app = fs.readFileSync(path.join(dir, "app_block_c103.js"), "utf8");
  assert.match(app, /c103-navfit/);
  assert.match(app, /flex-wrap:wrap/);
});

test("release-day simulation", async () => {
  const REL = Date.parse("2026-11-10T13:30:00.000Z");
  const ids = [];
  lib.C103_CATALOG.forEach((row) => { ids.push(row[2], row[3]); });
  const base = {};
  ids.forEach((id, i) => { base[id] = [{ year: "2026", period: "M09", value: String(300 + i) }, { year: "2025", period: "M09", value: String(280 + i) }, { year: "2026", period: "M08", value: String(299 + i) }]; });
  const ics = "BEGIN:VEVENT\nSUMMARY:Consumer Price Index\nDTSTART;TZID=US-Eastern:20250115T083000\nEND:VEVENT\nBEGIN:VEVENT\nSUMMARY:Consumer Price Index\nDTSTART;TZID=US-Eastern:20261110T083000\nEND:VEVENT\n";
  const arch = '<a href="/news.release/archives/cpi_01152025.htm">Jan 2025</a><a href="/news.release/archives/cpi_11102026.htm">Nov 2026</a><a href="/news.release/archives/cpi_01122022.htm">Jan 2022</a>';
  const ri = (month) => `<table><tr><th id="w">Relative<br/>importance<br/>${month}<br/>2026</th></tr><tr><th>Shelter</th><td headers="w">35.323</td><td>0.4</td></tr></table>`;
  const hourly = { chart: { result: [{ meta: { symbol: "GC=F", instrumentType: "FUTURE", shortName: "Gold", exchangeTimezoneName: "America/New_York" }, timestamp: [Date.parse("2025-01-15T12:00:00.000Z") / 1000, Date.parse("2025-01-15T14:00:00.000Z") / 1000], indicators: { quote: [{ close: [2600, 2620], open: [2590, 2610] }] } }] } };
  const daily = { chart: { result: [{ meta: { symbol: "GC=F", instrumentType: "FUTURE", shortName: "Gold", exchangeTimezoneName: "America/New_York" }, timestamp: [Date.parse("2025-01-14T05:00:00.000Z") / 1000, Date.parse("2025-01-15T05:00:00.000Z") / 1000], indicators: { quote: [{ close: [2590, 2630], open: [2588, 2592] }] } }] } };
  let riCalls = 0;
  const blsCalls = [];
  let now = 0;
  const deps = () => ({ timeoutMs: 2500, fetch: async (url, opt) => {
    let text;
    if (String(url).includes("api.bls.gov")) {
      const want = JSON.parse(opt.body).seriesid;
      blsCalls.push(want.length);
      const series = want.map((id) => {
        const data = base[id].slice();
        if (now >= REL + 3 * 60 * 1000) data.unshift({ year: "2026", period: "M10", value: String(Number(data[0].value) + 1) });
        return { seriesID: id, data: data };
      });
      text = JSON.stringify({ status: "REQUEST_SUCCEEDED", Results: { series: series } });
    } else if (String(url).includes("bls.ics")) text = ics;
    else if (String(url).includes("schedule/news_release/cpi.htm")) text = "<tr><td>October 2026</td><td>Nov. 10, 2026</td><td>08:30 AM</td></tr>";
    else if (String(url).includes("cpi.t01")) { riCalls += 1; text = ri(now >= REL + 3 * 60 * 1000 ? "Sep." : "Aug."); }
    else if (String(url).includes("news-release/cpi.htm")) text = arch;
    else if (String(url).includes("interval=1h")) text = JSON.stringify(hourly);
    else if (String(url).includes("interval=1d")) text = JSON.stringify(daily);
    else throw new Error(String(url));
    return { ok: true, status: 200, text: async () => text };
  } });
  let model = null;
  let at = 0;
  const log = [];
  for (now = Date.parse("2026-11-10T12:00:00.000Z"); now < Date.parse("2026-11-10T16:00:00.000Z"); now += 60000) {
    const ttl = model ? lib.c103CacheMs(model, now) : 0;
    if (!model || now - at >= ttl) {
      model = await lib.c103Refresh(deps(), now, model);
      at = now;
      if (now >= REL - 60000 && now <= REL + 40 * 60000) {
        const cats = (model.categories || []).filter((c) => c.period === "2026-10" && c.saIndex != null).length;
        log.push(new Date(now).toISOString().slice(11, 16) + " latest=" + (model.latest && model.latest.period) + " cats_oct=" + cats + "/" + (model.categories || []).length + " contrib=" + (model.contributions || []).filter((c) => typeof c.contribution === "number").length);
      }
    }
  }
  console.log(log.join("\n"));
  console.log("BLS calls", blsCalls.length, blsCalls.join(" "));
  console.log("RI fetches", riCalls);
  const premium = model.categories;
  assert.equal(premium.filter((c) => c.period === "2026-10" && c.saIndex != null).length, premium.length);
  assert.ok(model.contributions.filter((c) => typeof c.contribution === "number").length > 0);
  const jan = model.gold.find((row) => String(row.releaseAtUtc).startsWith("2025-01-15"));
  assert.ok(jan && jan.hourlyAvailable);
  assert.equal(/Daily windows only/.test(jan.hourMessage || ""), false);
  const restartAt = Date.parse("2026-11-10T13:25:00.000Z");
  const restarted = lib.c103ForNow({ previousEvents: model.previousEvents, latest: { period: "2026-09", fetchedAt: "2026-11-09T18:00:00.000Z" } }, restartAt);
  assert.equal(restarted.countdown.releaseAtUtc, "2026-11-10T13:30:00.000Z");
  console.log("end latest", model.latest.period, "cats", premium.filter((c) => c.saIndex != null).length, "/", premium.length, "intraday", model.gold.filter((r) => r.hourlyAvailable).length, "restart", restarted.countdown.releaseUk);
});

test("recorder stays quiet before 10 December 2026", () => {
  const early = lib.c103ReleaseInstant(2026, 11, 10, 8, 15);
  const release = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  assert.equal(lib.c103SnapshotDecision(early.startMs, [release]), null);
  const pre = lib.c103SnapshotDecision(release.startMs - 10 * 60 * 1000, [release]);
  assert.equal(pre.windowKind, "pre");
  assert.equal(pre.releaseAtUtc, release.releaseAtUtc);
});
