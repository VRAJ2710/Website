"use strict";
// Academy progress sync and /api/academy-daily resilience.
// Never starts server.js (it initialises Stripe). Fixtures are copies only.
const test = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const vm = require("vm");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const TODAY = "2026-10-18";
const SECRET = "sk-test-DO-NOT-PRINT";
const BASE = path.join(os.tmpdir(), "bb4-base");

function homeFreezeMarker(extra) {
  return "// \u2500\u2500 " + String.fromCharCode(114, 116, 53, 51) + (extra || "") + " \u2500\u2500";
}
function md5(file) {
  return crypto.createHash("md5").update(fs.readFileSync(file)).digest("hex");
}
function run(script, args) {
  try {
    const stdout = execFileSync("python3", [path.join(ROOT, "deploy", script), ...args], {
      encoding: "utf8",
      timeout: 180000,
      maxBuffer: 8 * 1024 * 1024,
    });
    return { code: 0, stdout };
  } catch (error) {
    return { code: error.status == null ? 1 : error.status, stdout: String(error.stdout || "") + String(error.stderr || "") };
  }
}
function plain(value) {
  return JSON.parse(JSON.stringify(value));
}
function copyTree(src, dest) {
  fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(dest, { recursive: true });
  for (const name of ["app.js", "index.html", "server.js"]) {
    fs.copyFileSync(path.join(src, name), path.join(dest, name));
  }
}
function toCrlf(file) {
  const text = fs.readFileSync(file, "utf8").replace(/\r\n/g, "\n").replace(/\n/g, "\r\n");
  fs.writeFileSync(file, text);
}

const LIVE_UPLOAD = {
  app: "/home/ubuntu/.cursor/projects/workspace/uploads/app_b90c.js",
  index: "/home/ubuntu/.cursor/projects/workspace/uploads/index_4b54.html",
  server: "/home/ubuntu/.cursor/projects/workspace/uploads/server_def1.js",
};
const LIVE_MD5 = {
  app: "d38b70eb458091fa69143f9fe3bfe193",
  index: "b15074aedc3261bf9e2ca611084082ba",
  server: "6972fdeb0fc892f370ef63fe21b80b55",
};

function buildBase() {
  for (const file of Object.values(LIVE_UPLOAD)) {
    if (!fs.existsSync(file)) throw new Error("live fixture missing: " + file);
  }
  fs.rmSync(BASE, { recursive: true, force: true });
  fs.mkdirSync(BASE, { recursive: true });
  fs.copyFileSync(LIVE_UPLOAD.app, path.join(BASE, "app.js"));
  fs.copyFileSync(LIVE_UPLOAD.index, path.join(BASE, "index.html"));
  fs.copyFileSync(LIVE_UPLOAD.server, path.join(BASE, "server.js"));
  if (md5(path.join(BASE, "app.js")) !== LIVE_MD5.app) throw new Error("live app.js md5 mismatch");
  if (md5(path.join(BASE, "index.html")) !== LIVE_MD5.index) throw new Error("live index.html md5 mismatch");
  if (md5(path.join(BASE, "server.js")) !== LIVE_MD5.server) throw new Error("live server.js md5 mismatch");
  const app = fs.readFileSync(path.join(BASE, "app.js"), "utf8");
  for (const needle of ["// ── rt52 ──", "function _rt47Save()", "Saved in this browser only."]) {
    if (!app.includes(needle)) throw new Error("live app.js missing " + needle);
  }
  if (!app.includes("// ── bb2 ──")) throw new Error("live app.js missing bb2");
  const foot = app.split("\n").find(line => line.includes("Saved in this browser only."));
  if (!foot || !foot.includes("`")) throw new Error("footer is not inside a template literal");
  if (!fs.readFileSync(path.join(BASE, "index.html"), "utf8").includes('app.js?v=chat59"')) {
    throw new Error("live index is not chat59");
  }
  const server = fs.readFileSync(path.join(BASE, "server.js"), "utf8");
  if (!server.includes("function hasPremiumAccess(") || !server.includes("// ── rt52s")) {
    throw new Error("live server.js missing rt52s or hasPremiumAccess");
  }
}

function pureFns(appText) {
  const start = appText.indexOf("/* BB4A_PURE_START */");
  const end = appText.indexOf("/* BB4A_PURE_END */");
  assert.ok(start >= 0 && end > start, "PURE markers");
  const code = appText.slice(start, end);
  const sandbox = { Intl, Date, Math, JSON, Number, String, Set, Array, isFinite };
  vm.runInNewContext(code, sandbox);
  return sandbox;
}

function serverFns(serverText) {
  const start = serverText.indexOf("/* BB4A_SERVER_START */");
  const end = serverText.indexOf("/* BB4A_SERVER_END */");
  assert.ok(start >= 0 && end > start, "server markers");
  const code = serverText.slice(start, end);
  const sandbox = {
    Intl, Date, Math, JSON, Number, String, Set, Array, isFinite, Error,
    rt17SanitizePrefs(input) {
      const p = input && typeof input === "object" ? input : {};
      const out = {};
      if (p.layout) out.layout = JSON.parse(JSON.stringify(p.layout));
      if (p.sentinel != null) out.sentinel = p.sentinel;
      if (p.v != null) out.v = p.v;
      return out;
    },
  };
  vm.runInNewContext(code, sandbox);
  return sandbox;
}

function mockRes() {
  return {
    headersSent: false,
    writableEnded: false,
    statusCode: 0,
    headers: null,
    body: "",
    writeHead(status, headers) { this.statusCode = status; this.headers = headers; this.headersSent = true; },
    end(body) { this.body = String(body || ""); this.writableEnded = true; },
  };
}

function loadAcademy(serverText) {
  const start = serverText.indexOf("// ── rt48c:");
  const end = serverText.indexOf("const MARKET_SYSTEM");
  assert.ok(start >= 0 && end > start, "academy slice");
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "bb4ad-"));
  const sandbox = {
    console, Buffer, URL, URLSearchParams, TextDecoder, TextEncoder, Intl,
    setTimeout, clearTimeout, AbortSignal, AbortController, Map, Set, Promise, Date, Math, JSON, RegExp, Error,
    encodeURIComponent, decodeURIComponent, isFinite, parseInt, Number, String, Object, Array,
    process: { env: { OPENAI_API_KEY: SECRET, ACADEMY_AI: "on" } },
    require(name) {
      if (name === "fs") return fs;
      if (name === "path") return path;
      if (name === "os") return { tmpdir: () => tmp };
      throw new Error("require " + name);
    },
    fetch: async () => { throw new Error("fetch unset"); },
    generateAi: async () => { throw new Error("generateAi must not run on the lesson build"); },
    generateWithAiProvider: async () => { throw new Error("provider unset"); },
    currentUser: async () => null,
    isAdminUser() { return false; },
    approvedRssFeedUrl() { return "https://example.test/rss"; },
  };
  vm.runInNewContext(serverText.slice(start, end) + `
function _bb4dTestPrep(patch) {
  if (patch.items) _rt48sState.items = patch.items;
  if ("day" in patch) _rt48sState.day = patch.day;
  if ("tries" in patch) _rt48sState.tries = patch.tries;
  if ("generatedAt" in patch) _rt48sState.generatedAt = patch.generatedAt;
  if ("buildLast" in patch) _rt48sState.last = patch.buildLast;
  if ("kind" in patch) _rt48sState.kind = patch.kind;
  if ("lastMem" in patch) _bb4dLast = patch.lastMem;
  return { v3: _rt48sFile, last: _bb4dLastFile };
}
function _bb4dTestBusy() { return _rt48sState.busy; }
`, sandbox);
  sandbox.tmp = tmp;
  return sandbox;
}

function noSecret(body) {
  assert.equal(JSON.stringify(body).includes(SECRET), false, "response contained a secret");
}

buildBase();

test("live base is the uploaded chat59 trio, after bb3", () => {
  assert.equal(md5(path.join(BASE, "app.js")), LIVE_MD5.app);
  assert.equal(md5(path.join(BASE, "index.html")), LIVE_MD5.index);
  assert.equal(md5(path.join(BASE, "server.js")), LIVE_MD5.server);
  const server = fs.readFileSync(path.join(BASE, "server.js"), "utf8");
  assert.match(server, /\/\/ ── rt52s: 13F v2 ──/);
  assert.match(server, /\/\/ ── bb2 ──/);
  assert.match(server, /\/\/ ── bb3 ──/);
  assert.match(server, /\/\/ ── bb3fit ──/);
  assert.match(server, /function hasPremiumAccess\(/);
});

test("dry run writes nothing and a second run refuses", () => {
  const dir = path.join(os.tmpdir(), "bb4-dry");
  copyTree(BASE, dir);
  const before = ["app.js", "index.html", "server.js"].map(name => md5(path.join(dir, name)));
  const dry = run("patch_bb4_academy.py", ["--check", dir]);
  assert.equal(dry.code, 0, dry.stdout);
  assert.match(dry.stdout, /chat59 -> chat60/);
  assert.match(dry.stdout, /dry run, nothing written/);
  const after = ["app.js", "index.html", "server.js"].map(name => md5(path.join(dir, name)));
  assert.deepEqual(after, before);
  const applied = run("patch_bb4_academy.py", [dir]);
  assert.equal(applied.code, 0, applied.stdout);
  console.log(applied.stdout);
  const again = run("patch_bb4_academy.py", ["--check", dir]);
  assert.equal(again.code, 0, again.stdout);
  assert.match(again.stdout, /REFUSE: bb4academy already applied/);
  const againApply = run("patch_bb4_academy.py", [dir]);
  assert.equal(againApply.code, 0, againApply.stdout);
  assert.match(againApply.stdout, /REFUSE: bb4academy already applied/);
  assert.match(fs.readFileSync(path.join(dir, "index.html"), "utf8"), /app\.js\?v=chat60"/);
});

test("daily then academy, and academy then daily, leave neighbouring markers in place", () => {
  const first = path.join(os.tmpdir(), "bb4-order-a");
  const second = path.join(os.tmpdir(), "bb4-order-b");
  copyTree(BASE, first);
  copyTree(BASE, second);
  for (const dir of [first, second]) {
    fs.appendFileSync(path.join(dir, "app.js"), "\n// ── bb2 ──\n");
    fs.appendFileSync(path.join(dir, "server.js"), "\n// ── bb2 ──\nasync function bb3RegimeFit(ticker) { return { ticker: ticker, regimeFit: 28 }; }\n");
  }
  const indexBefore = md5(path.join(first, "index.html"));
  const dailyFirst = run("patch_bb4_daily.py", [path.join(first, "server.js")]);
  assert.equal(dailyFirst.code, 0, dailyFirst.stdout);
  console.log(dailyFirst.stdout);
  assert.equal(md5(path.join(first, "index.html")), indexBefore);
  assert.equal(run("patch_bb4_academy.py", [first]).code, 0);
  const prefsFirst = run("patch_bb4_academy.py", [second]);
  assert.equal(prefsFirst.code, 0, prefsFirst.stdout);
  const dailySecond = run("patch_bb4_daily.py", [path.join(second, "server.js")]);
  assert.equal(dailySecond.code, 0, dailySecond.stdout);
  for (const dir of [first, second]) {
    const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
    const app = fs.readFileSync(path.join(dir, "app.js"), "utf8");
    assert.match(server, /\/\/ ── bb4daily ──/);
    assert.match(server, /\/\/ ── bb4academy ──/);
    assert.equal(server.includes(homeFreezeMarker("")), false);
    assert.equal(server.includes(homeFreezeMarker("s")), false);
    assert.match(server, /async function bb3RegimeFit\(ticker\)/);
    assert.match(server, /function hasPremiumAccess\(user\)/);
    assert.match(server, /\/\/ ── bb2 ──/);
    assert.equal(server.includes("ON CONFLICT (user_id) DO UPDATE SET prefs=EXCLUDED.prefs"), false);
    assert.match(app, /\/\/ ── bb4academy ──/);
    assert.equal(app.includes(homeFreezeMarker("")), false);
    assert.match(app, /\/\/ ── bb2 ──/);
    assert.match(fs.readFileSync(path.join(dir, "index.html"), "utf8"), /app\.js\?v=chat60"/);
    const region = server.slice(server.indexOf("/* BB4A_SERVER_START */"), server.indexOf("/* BB4A_SERVER_END */"));
    assert.equal(region.includes("user.tier"), false);
    const daily = server.slice(server.indexOf("// ── bb4daily ──"), server.indexOf("const MARKET_SYSTEM"));
    assert.equal(daily.includes("user.tier"), false);
    const clientAt = app.indexOf("// ── bb4academy ──");
    assert.ok(clientAt >= 0, "client marker");
    const client = app.slice(clientAt);
    assert.equal(client.includes("user.tier"), false);
    assert.equal(server.split("async function academyDaily(req, res) {").length, 2);
  }
  const refuse = run("patch_bb4_daily.py", [path.join(first, "server.js")]);
  assert.equal(refuse.code, 0, refuse.stdout);
  assert.match(refuse.stdout, /REFUSE: bb4daily already applied/);
});

test("a later bust increments, chat57 is refused, a missing anchor writes nothing", () => {
  const later = path.join(os.tmpdir(), "bb4-chat60");
  copyTree(BASE, later);
  const index = path.join(later, "index.html");
  fs.writeFileSync(index, fs.readFileSync(index, "utf8").replace("chat59", "chat60"));
  const bumped = run("patch_bb4_academy.py", [later]);
  assert.equal(bumped.code, 0, bumped.stdout);
  assert.match(fs.readFileSync(index, "utf8"), /app\.js\?v=chat61"/);

  const early = path.join(os.tmpdir(), "bb4-chat57");
  copyTree(BASE, early);
  const earlyIndex = path.join(early, "index.html");
  const earlyHash = md5(path.join(early, "app.js"));
  fs.writeFileSync(earlyIndex, fs.readFileSync(earlyIndex, "utf8").replace("chat59", "chat57"));
  const refused = run("patch_bb4_academy.py", [early]);
  assert.equal(refused.code, 1, refused.stdout);
  assert.match(refused.stdout, /chat57/);
  assert.equal(md5(path.join(early, "app.js")), earlyHash);

  const missing = path.join(os.tmpdir(), "bb4-missing");
  copyTree(BASE, missing);
  const server = path.join(missing, "server.js");
  const before = md5(server);
  const broken = fs.readFileSync(server, "utf8").split("function hasPremiumAccess(").join("function premiumHelper(");
  fs.writeFileSync(server, broken);
  const stripped = md5(server);
  const aborted = run("patch_bb4_daily.py", [server]);
  assert.equal(aborted.code, 1, aborted.stdout);
  assert.match(aborted.stdout, /hasPremiumAccess/);
  assert.equal(md5(server), stripped);
  assert.notEqual(stripped, before);
  assert.equal(fs.readFileSync(path.join(missing, "app.js"), "utf8").includes("// ── bb4academy ──"), false);
});

test("CRLF files stay CRLF and still parse", () => {
  const dir = path.join(os.tmpdir(), "bb4-crlf");
  copyTree(BASE, dir);
  for (const name of ["app.js", "index.html", "server.js"]) toCrlf(path.join(dir, name));
  const prefs = run("patch_bb4_academy.py", [dir]);
  assert.equal(prefs.code, 0, prefs.stdout);
  const daily = run("patch_bb4_daily.py", [path.join(dir, "server.js")]);
  assert.equal(daily.code, 0, daily.stdout);
  for (const name of ["app.js", "server.js"]) {
    const bytes = fs.readFileSync(path.join(dir, name));
    assert.ok(bytes.includes(Buffer.from("\r\n")));
    execFileSync("node", ["--check", path.join(dir, name)], { timeout: 120000 });
  }
});

test("merge rules for xp, badges, and streaks", () => {
  const dir = path.join(os.tmpdir(), "bb4-merge");
  copyTree(BASE, dir);
  assert.equal(run("patch_bb4_academy.py", [dir]).code, 0);
  const app = fs.readFileSync(path.join(dir, "app.js"), "utf8");
  const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
  const clientPure = app.slice(app.indexOf("/* BB4A_PURE_START */"), app.indexOf("/* BB4A_PURE_END */"));
  const serverPure = server.slice(server.indexOf("/* BB4A_PURE_START */"), server.indexOf("/* BB4A_PURE_END */"));
  assert.equal(clientPure, serverPure);
  const { bb4aMerge, bb4aClean } = pureFns(app);
  const merge = (a, b) => bb4aMerge(a, b, TODAY);
  assert.equal(merge({ xp: 10 }, { xp: 40 }).xp, 40);
  assert.equal(merge({ xp: 999999 }, { xp: 1 }).xp, 20000);
  assert.equal(bb4aClean({ xp: -4, badges: ["news"] }, TODAY).xp, 0);
  assert.deepEqual(plain(merge({ badges: ["weekly"] }, { badges: ["combo", "admin", "combo"] }).badges), ["combo", "weekly"]);
  const kept = bb4aClean({ xp: 10, streak: 5, last: "2026-10-17" }, TODAY);
  assert.deepEqual(plain(kept.days), []);
  assert.equal(kept.streak, 5);
  const bridged = merge({ streak: 5, last: "2026-10-17" }, { streak: 1, last: TODAY });
  assert.equal(bridged.streak, 6);
  assert.equal(bridged.days.length, 6);
  assert.equal(bridged.days[bridged.days.length - 1], TODAY);
  assert.equal(merge({ streak: 3, last: TODAY }, { streak: 5, last: TODAY }).streak, 5);
  assert.equal(merge({ streak: 9, last: "2026-10-01" }, { streak: 2, last: TODAY }).streak, 2);
  const runDays = merge({ days: ["2026-10-16", "2026-10-17"] }, { days: [TODAY] });
  assert.equal(runDays.streak, 3);
  assert.deepEqual(plain(runDays.days), ["2026-10-16", "2026-10-17", TODAY]);
  const gapped = merge({ days: ["2026-10-10"] }, { days: [TODAY] });
  assert.equal(gapped.streak, 1);
  assert.deepEqual(plain(gapped.days), ["2026-10-10", TODAY]);
  const many = [];
  for (let i = 199; i >= 0; i--) many.push(new Date(Date.UTC(2026, 9, 18 - i)).toISOString().slice(0, 10));
  const capped = merge({ days: many }, { days: [] });
  assert.equal(capped.days.length, 120);
  assert.equal(capped.days[capped.days.length - 1], TODAY);
  assert.equal(capped.streak, 120);
  const dirty = bb4aClean({ xp: 3, badges: ["news"], days: ["2026-02-31", "2023-12-31", "2026-10-21", "2024-02-29"] }, TODAY);
  assert.deepEqual(plain(dirty.days), ["2024-02-29"]);
  assert.equal(dirty.streak, 0);
  console.log(JSON.stringify({
    maxXp: 40, cap: 20000, negative: 0, badges: ["combo", "weekly"],
    bridge: bridged.streak, sameDay: 5, broken: 2, threeDay: runDays.streak, gap: gapped.streak, capDays: capped.days.length,
  }));
});

test("prefs writes merge, keep other fields, and retry a clash", async () => {
  const dir = path.join(os.tmpdir(), "bb4-prefs");
  copyTree(BASE, dir);
  assert.equal(run("patch_bb4_academy.py", [dir]).code, 0);
  const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
  const box = serverFns(server);
  let db = {
    prefs: {
      rev: 1,
      layout: { density: "compact" },
      sentinel: "keep-me",
      academy: { v: 1, xp: 10, badges: ["combo"], days: [TODAY], last: TODAY, streak: 1 },
    },
    updated_at: "t0",
  };
  let selects = 0;
  box.sql = async (strings, ...vals) => {
    const query = strings.join(" ");
    if (query.includes("SELECT")) {
      const snap = JSON.parse(JSON.stringify(db));
      selects += 1;
      await new Promise(resolve => setImmediate(resolve));
      return [{ prefs: snap.prefs, updated_at: snap.updated_at }];
    }
    if (query.includes("INSERT")) {
      if (db) return [];
      db = { prefs: JSON.parse(vals[1]), updated_at: "t" };
      return [{ prefs: db.prefs, updated_at: db.updated_at }];
    }
    if (query.includes("UPDATE")) {
      const rev = vals[2];
      const current = Math.round(Number(db.prefs.rev) || 0);
      if (current !== rev) return [];
      db.prefs = JSON.parse(vals[0]);
      db.updated_at = "t2";
      return [{ prefs: db.prefs, updated_at: db.updated_at }];
    }
    throw new Error(query);
  };
  const user = { id: "user-1" };
  const [left, right] = await Promise.all([
    box.bb4aPutPrefs(user, { prefs: { academy: { xp: 40, badges: ["news"], days: [TODAY] } } }),
    box.bb4aPutPrefs(user, { prefs: { academy: { xp: 15, badges: ["match"], days: ["2026-10-17", TODAY] } } }),
  ]);
  assert.ok(selects >= 2);
  assert.equal(left.prefs.sentinel, "keep-me");
  assert.equal(right.prefs.layout.density, "compact");
  assert.equal(left.prefs.rev, undefined);
  assert.equal(db.prefs.academy.xp, 40);
  assert.deepEqual(db.prefs.academy.badges, ["combo", "match", "news"]);
  assert.deepEqual(db.prefs.academy.days, ["2026-10-17", TODAY]);
  assert.equal(db.prefs.sentinel, "keep-me");
  assert.equal(db.prefs.rev, 3);
  const settings = await box.bb4aPutPrefs(user, { prefs: { v: 1, layout: { density: "comfortable" }, sentinel: "next" } });
  assert.equal(settings.prefs.layout.density, "comfortable");
  assert.equal(settings.prefs.sentinel, "next");
  assert.equal(settings.prefs.academy.xp, 40);
  assert.equal(settings.prefs.academy.badges.includes("news"), true);
  await assert.rejects(
    () => box.bb4aPutPrefs(user, { prefs: { v: 1, sentinel: "x".repeat(50000) } }),
    error => error.code === "RT17_TOO_LARGE"
  );
  box.sql = async (strings) => {
    const query = strings.join(" ");
    if (query.includes("SELECT")) return [{ prefs: { rev: 1, layout: { density: "compact" }, sentinel: "keep-me" }, updated_at: "t" }];
    if (query.includes("UPDATE") || query.includes("INSERT")) return [];
    throw new Error(query);
  };
  await assert.rejects(
    () => box.bb4aPutPrefs(user, { prefs: { academy: { xp: 1, badges: ["news"] } } }),
    error => error.code === "BB4A_CONFLICT"
  );
  console.log(JSON.stringify({ xp: db.prefs.academy.xp, badges: db.prefs.academy.badges, days: db.prefs.academy.days, rev: db.prefs.rev, sentinel: settings.prefs.sentinel }));
});

test("academy-daily survives a dead feed, serves the last good lesson, and hides diag", async () => {
  const dir = path.join(os.tmpdir(), "bb4-daily");
  copyTree(BASE, dir);
  const dailyPatch = run("patch_bb4_daily.py", [path.join(dir, "server.js")]);
  assert.equal(dailyPatch.code, 0, dailyPatch.stdout);
  const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
  const fed = "<rss><item><title>The Federal Reserve cuts rates in a surprise move</title><link>https://example.test/fed</link></item></rss>";

  const live = loadAcademy(server);
  let fetched = 0;
  live.fetch = async () => { fetched += 1; return { ok: true, text: async () => fed }; };
  live.generateAi = async () => { throw Object.assign(new Error("provider down"), { code: "NO_AI" }); };
  const liveRes = mockRes();
  await live.academyDaily({ url: "/api/academy-daily" }, liveRes);
  const liveBody = JSON.parse(liveRes.body);
  assert.equal(liveRes.statusCode, 200);
  assert.equal(liveBody.source, "live");
  assert.ok(liveBody.asOf);
  assert.ok(liveBody.items.length >= 1);
  liveBody.items.forEach(item => assert.equal(live._rt48bValid(item), true));
  noSecret(liveBody);
  assert.ok(fetched >= 1);

  const down = loadAcademy(server);
  down.fetch = async () => { throw new Error("network"); };
  down.generateAi = async () => { throw new Error("provider down"); };
  const downRes = mockRes();
  await down.academyDaily({ url: "/api/academy-daily" }, downRes);
  const downBody = JSON.parse(downRes.body);
  assert.equal(downRes.statusCode, 200);
  assert.equal(downBody.source, "fallback");
  assert.equal(down._rt48bValid(downBody.items[0]), true);
  assert.equal(downBody.stale, false);
  noSecret(downBody);
  assert.equal(fs.existsSync(path.join(down.tmp, "dispatch-academy-daily-last.json")), false);

  const stale = loadAcademy(server);
  const sample = stale._rt48bItem(
    { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" },
    "gold", "up",
    "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.",
    "template"
  );
  assert.equal(stale._rt48bValid(sample), true);
  const generatedAt = "2026-10-16T12:00:00.000Z";
  const paths = stale._bb4dTestPrep({ items: [], day: "", tries: 3, generatedAt: "", lastMem: null });
  fs.writeFileSync(paths.last, JSON.stringify({
    v: 1, at: Date.parse(generatedAt), day: "2026-10-16", generatedAt, items: [sample], kind: "template",
  }));
  stale.fetch = async () => { throw new Error("network"); };
  const staleRes = mockRes();
  await stale.academyDaily({ url: "/api/academy-daily" }, staleRes);
  const staleBody = JSON.parse(staleRes.body);
  assert.equal(staleRes.statusCode, 200);
  assert.equal(staleBody.source, "stale");
  assert.equal(staleBody.asOf, generatedAt);
  assert.equal(staleBody.stale, true);
  noSecret(staleBody);

  const hidden = loadAcademy(server);
  let hiddenFetch = 0;
  hidden.fetch = async () => { hiddenFetch += 1; throw new Error("should not build"); };
  const hiddenRes = mockRes();
  await hidden.academyDaily({ url: "/api/academy-daily?diag=1" }, hiddenRes);
  assert.equal(hiddenRes.statusCode, 403);
  assert.deepEqual(JSON.parse(hiddenRes.body), { error: "Administrator access required." });
  assert.equal(hiddenFetch, 0);
  const refresh = mockRes();
  hidden.fetch = async () => { throw new Error("network"); };
  await hidden.academyDaily({ url: "/api/academy-daily?refresh=1" }, refresh);
  assert.equal(refresh.statusCode, 200);
  assert.equal(JSON.parse(refresh.body).source, "fallback");

  const admin = loadAcademy(server);
  admin.currentUser = async () => ({ id: "admin", tier: "free" });
  admin.isAdminUser = () => true;
  admin.fetch = async () => { throw new Error("network"); };
  const adminRes = mockRes();
  await admin.academyDaily({ url: "/api/academy-daily?diag=1" }, adminRes);
  const adminBody = JSON.parse(adminRes.body);
  assert.equal(adminRes.statusCode, 200);
  assert.equal(typeof adminBody.diag, "object");
  assert.equal(adminBody.diag.aiSwitch, "on");
  noSecret(adminBody);

  const hung = loadAcademy(server);
  hung.fetch = (url, opts) => new Promise((resolve, reject) => {
    const timer = setTimeout(() => resolve({ ok: true, text: async () => "" }), 30000);
    const signal = opts && opts.signal;
    if (signal) signal.addEventListener("abort", () => {
      clearTimeout(timer);
      const error = new Error("aborted");
      error.name = "AbortError";
      reject(error);
    });
  });
  hung.generateAi = () => new Promise(resolve => setTimeout(() => resolve({ text: "" }), 3800));
  const started = Date.now();
  const hungRes = mockRes();
  await hung.academyDaily({ url: "/api/academy-daily" }, hungRes);
  const elapsed = Date.now() - started;
  assert.equal(hungRes.statusCode, 200);
  assert.ok(elapsed < 1600, "cold hung upstream returned in " + elapsed + "ms");
  assert.ok(elapsed >= 700, "cold path returned before the timeout: " + elapsed + "ms");
  assert.equal(JSON.parse(hungRes.body).source, "fallback");
  noSecret(JSON.parse(hungRes.body));

  const warm = loadAcademy(server);
  const warmItem = warm._rt48bItem(
    { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" },
    "gold", "up",
    "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.",
    "ai"
  );
  assert.equal(warm._rt48bValid(warmItem), true);
  const today = warm._rt48sDay();
  warm._bb4dTestPrep({
    items: [warmItem, Object.assign({}, warmItem), Object.assign({}, warmItem)],
    day: today,
    tries: 1,
    generatedAt: new Date().toISOString(),
    buildLast: Date.now(),
    kind: "ai",
    lastMem: null,
  });
  let warmFetch = 0;
  let warmAi = 0;
  let warmProvider = 0;
  warm.fetch = async () => { warmFetch += 1; throw new Error("warm path must not fetch"); };
  warm.generateAi = () => { warmAi += 1; return new Promise(resolve => setTimeout(() => resolve({ text: "" }), 3800)); };
  warm.generateWithAiProvider = () => { warmProvider += 1; return new Promise(resolve => setTimeout(() => resolve({ text: "" }), 3800)); };
  const warmStarted = Date.now();
  const warmRes = mockRes();
  await warm.academyDaily({ url: "/api/academy-daily" }, warmRes);
  const warmMs = Date.now() - warmStarted;
  const warmBody = JSON.parse(warmRes.body);
  assert.equal(warmRes.statusCode, 200);
  assert.equal(warmBody.source, "cache");
  assert.equal(warmBody.stale, false);
  assert.ok(warmMs < 250, "warm response took " + warmMs + "ms");
  assert.equal(warmFetch, 0);
  assert.equal(warmAi, 0);
  assert.equal(warmProvider, 0);
  noSecret(warmBody);

  const swr = loadAcademy(server);
  const swrItem = swr._rt48bItem(
    { h: "The Federal Reserve cuts rates in a surprise move", src: "Dispatch Academy", link: "" },
    "gold", "up",
    "Gold often rises on a surprise Fed cut: lower rates reduce the cost of holding a metal that pays no interest, and the dollar tends to weaken.",
    "template"
  );
  swr._bb4dTestPrep({ items: [], day: "", tries: 0, generatedAt: "", buildLast: 0, lastMem: null });
  fs.writeFileSync(swr._bb4dTestPrep({ items: [], day: "", tries: 0, generatedAt: "", buildLast: 0, lastMem: null }).last, JSON.stringify({
    v: 1, at: Date.parse("2026-10-16T12:00:00.000Z"), day: "2026-10-16", generatedAt: "2026-10-16T12:00:00.000Z", items: [swrItem], kind: "template",
  }));
  let swrFetch = 0;
  swr.fetch = (url, opts) => {
    swrFetch += 1;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => resolve({ ok: true, text: async () => "" }), 30000);
      const signal = opts && opts.signal;
      if (signal) signal.addEventListener("abort", () => { clearTimeout(timer); reject(Object.assign(new Error("aborted"), { name: "AbortError" })); });
    });
  };
  const swrStarted = Date.now();
  const swrRes = mockRes();
  await swr.academyDaily({ url: "/api/academy-daily" }, swrRes);
  const swrMs = Date.now() - swrStarted;
  const swrBody = JSON.parse(swrRes.body);
  assert.equal(swrBody.source, "stale");
  assert.ok(swrMs < 250, "stale-while-revalidate took " + swrMs + "ms");
  assert.ok(swrFetch >= 1, "a stale lesson still starts a refresh");
  noSecret(swrBody);

  const before = await timeLiveHandler();
  console.log(JSON.stringify({
    live: { status: 200, source: liveBody.source, items: liveBody.items.length },
    down: { status: 200, source: downBody.source },
    stale: { status: 200, source: staleBody.source, asOf: staleBody.asOf },
    diag: 403, adminDiag: true,
    beforeMs: before,
    coldMs: elapsed, warmMs: warmMs, swrMs: swrMs,
  }));
});

test("lesson build tries gpt-4o-mini then Gemini and never calls generateAi or xAI", async () => {
  const dir = path.join(os.tmpdir(), "bb4-providers");
  copyTree(BASE, dir);
  assert.equal(run("patch_bb4_daily.py", [path.join(dir, "server.js")]).code, 0);
  const server = fs.readFileSync(path.join(dir, "server.js"), "utf8");
  const build = server.slice(server.indexOf("async function _rt48sBuild("), server.indexOf("// ── bb4daily ──"));
  assert.equal(build.includes("generateAi"), false);
  assert.match(build, /_bb4dGen\(/);

  const box = loadAcademy(server);
  const calls = [];
  let genAi = 0;
  box.generateAi = async () => { genAi += 1; throw new Error("generateAi must not run"); };
  box.generateWithAiProvider = async (provider, opts) => {
    calls.push([provider, opts.model]);
    if (provider === "xai") throw new Error("xai must not run");
    if (provider === "openai") throw Object.assign(new Error("openai down"), { code: "NO_AI" });
    return { text: "{}", model: opts.model };
  };
  const got = await box._bb4dGen({ maxTokens: 100, temperature: 0.2, system: "s", messages: [] });
  assert.equal(got.model, "gemini-2.5-flash");
  assert.deepEqual(calls, [["openai", "gpt-4o-mini"], ["google", "gemini-2.5-flash"]]);
  assert.equal(genAi, 0);

  const slow = loadAcademy(server);
  const slowCalls = [];
  slow.generateAi = async () => { throw new Error("generateAi must not run"); };
  slow.generateWithAiProvider = (provider, opts) => {
    slowCalls.push([provider, opts.model, !!(opts && opts.signal)]);
    if (provider === "openai") return new Promise(() => {});
    return Promise.resolve({ text: "{}", model: opts.model });
  };
  const t0 = Date.now();
  const slowGot = await slow._bb4dGen({});
  const dt = Date.now() - t0;
  assert.equal(slowGot.model, "gemini-2.5-flash");
  assert.deepEqual(slowCalls.map(row => row[0] + ":" + row[1]), ["openai:gpt-4o-mini", "google:gemini-2.5-flash"]);
  assert.equal(slowCalls[0][2], true);
  assert.ok(dt >= 2200 && dt < 4500, "openai cap then Gemini took " + dt + "ms");
});

test("a burst of academy-daily requests starts one build", async () => {
  const dir = path.join(os.tmpdir(), "bb4-burst");
  copyTree(BASE, dir);
  assert.equal(run("patch_bb4_daily.py", [path.join(dir, "server.js")]).code, 0);
  const box = loadAcademy(fs.readFileSync(path.join(dir, "server.js"), "utf8"));
  const fed = "<rss><item><title>The Federal Reserve cuts rates in a surprise move</title><link>https://example.test/fed</link></item></rss>";
  let fetches = 0;
  const providers = [];
  box.fetch = (url, opts) => {
    fetches += 1;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => resolve({ ok: true, text: async () => fed }), 200);
      const signal = opts && opts.signal;
      if (signal) signal.addEventListener("abort", () => {
        clearTimeout(timer);
        reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
      });
    });
  };
  box.generateAi = async () => { throw new Error("generateAi must not run"); };
  box.generateWithAiProvider = (provider, opts) => {
    providers.push(provider + ":" + opts.model);
    if (provider === "openai") return new Promise(() => {});
    return Promise.resolve({ text: "{}", model: opts.model });
  };
  const responses = await Promise.all([0, 1, 2, 3, 4].map(async () => {
    const res = mockRes();
    await box.academyDaily({ url: "/api/academy-daily" }, res);
    return res;
  }));
  responses.forEach(res => {
    assert.equal(res.statusCode, 200);
    noSecret(JSON.parse(res.body));
  });
  const busy = box._bb4dTestBusy();
  if (busy) await busy;
  assert.equal(fetches, 6, "feeds fetched " + fetches + " times");
  assert.deepEqual(providers, ["openai:gpt-4o-mini", "google:gemini-2.5-flash"]);
});

async function timeLiveHandler() {
  const text = fs.readFileSync(LIVE_UPLOAD.server, "utf8");
  const start = text.indexOf("// ── rt48c:");
  const end = text.indexOf("const MARKET_SYSTEM");
  assert.ok(start >= 0 && end > start, "live academy slice");
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "bb4before-"));
  let aiCalls = 0;
  const sandbox = {
    console, Buffer, URL, URLSearchParams, TextDecoder, TextEncoder, Intl,
    setTimeout, clearTimeout, AbortSignal, Map, Set, Promise, Date, Math, JSON, RegExp, Error,
    encodeURIComponent, decodeURIComponent, isFinite, parseInt, Number, String, Object, Array,
    process: { env: { OPENAI_API_KEY: SECRET, ACADEMY_AI: "on" } },
    require(name) {
      if (name === "fs") return fs;
      if (name === "path") return path;
      if (name === "os") return { tmpdir: () => tmp };
      throw new Error("require " + name);
    },
    fetch: async () => ({ ok: true, text: async () => "<rss><item><title>The Federal Reserve cuts rates in a surprise move</title><link>https://example.test/fed</link></item></rss>" }),
    generateAi() {
      aiCalls += 1;
      return new Promise(resolve => setTimeout(() => resolve({ text: "", model: "slow" }), 3800));
    },
    currentUser: async () => null,
    isAdminUser() { return false; },
    approvedRssFeedUrl() { return "https://example.test/rss"; },
  };
  vm.runInNewContext(text.slice(start, end), sandbox);
  const res = mockRes();
  const t0 = Date.now();
  await sandbox.academyDaily({ url: "/api/academy-daily" }, res);
  const ms = Date.now() - t0;
  const body = JSON.parse(res.body);
  noSecret(body);
  assert.equal(res.statusCode, 200);
  assert.equal(aiCalls, 1);
  assert.ok(ms >= 3400 && ms < 6500, "unpatched handler took " + ms + "ms");
  assert.equal(body.asOf, undefined);
  return ms;
}
