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
  assert.match(spec, /b84058f6da16ad022640b06c9cdda72d/);
  assert.match(spec, /b3e02b0c6e403133843a96adf45d219c/);
  assert.match(spec, /R5_SERVER_MD5=0284a3b26acaa055ed4699b1c36b6ddc/);
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
  const arrived = { previousEvents: [release, later], latest: { period: release.referencePeriod } };
  assert.ok(lib.c103CacheMs(arrived, after) > 60 * 1000);
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
    latest: { periodLabel: "September 2026", headline: { momRounded: 0.6, yoyRounded: 3.7, saIndex: 1, nsaIndex: 1, momSeries: "CUSR0000SA0", yoySeries: "CUUR0000SA0", why: "Broad index.", source: "Source: U.S. Bureau of Labor Statistics" }, core: { momRounded: 0.3, yoyRounded: 2.6, saIndex: 1, nsaIndex: 1, why: "Slower part.", source: "Source: U.S. Bureau of Labor Statistics" } },
    categories: [{ name: "Shelter", why: "Largest weight.", momRounded: 0.4, yoyRounded: 3.2, weight: 35.323, weightMonth: "Aug. 2026", contribution: 0.14, contributionNote: "", momSeries: "CUSR0000SAH1" }],
    gold: [row],
    relativeImportance: { citation: "https://www.bls.gov/news.release/cpi.t01.htm" }
  });
  assert.match(html, /BLS data/);
  assert.equal(/>CUSR0000SA0</.test(html), false);
  assert.match(html, /prior session close/);
  assert.match(html, /href="https:\/\/data\.bls\.gov\/timeseries\//);
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

test("recorder stays quiet before 10 December 2026", () => {
  const early = lib.c103ReleaseInstant(2026, 11, 10, 8, 15);
  const release = lib.c103ReleaseInstant(2026, 12, 10, 8, 30);
  assert.equal(lib.c103SnapshotDecision(early.startMs, [release]), null);
  const pre = lib.c103SnapshotDecision(release.startMs - 10 * 60 * 1000, [release]);
  assert.equal(pre.windowKind, "pre");
  assert.equal(pre.releaseAtUtc, release.releaseAtUtc);
});
