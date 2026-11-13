"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockI = fs.readFileSync(path.join(dir, "server_block_c102r6i.js"), "utf8");
const blockH = fs.readFileSync(path.join(dir, "server_block_c102r6h.js"), "utf8");

function load(block) {
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer: Buffer,
    JSON: JSON,
    Object: Object,
    Array: Array,
    String: String,
    Intl: Intl,
    Date: Date,
    Promise: Promise,
    Response: function Response() {},
    isFinite: isFinite
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext("function json(res, status, body) { res.end(JSON.stringify(body)); }", context);
  vm.runInContext(block, context);
  return context;
}
function send(context, body, url) {
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  if (url) res.req = { url: url };
  context.json(res, 200, body);
  return JSON.parse(res.written);
}

test("app.js does not compare desk-quotes vendor strings and does branch on market-reference ids", () => {
  const app = fs.readFileSync("/tmp/c102hash/app.js", "utf8");
  assert.equal(app.includes('=== "Yahoo Finance (GC=F)"'), false);
  assert.equal(app.includes('=== "Yahoo Finance (DX-Y.NYB)"'), false);
  assert.equal(app.includes('=== "Yahoo Finance (^TNX)"'), false);
  assert.match(app, /gold-api-spot-proxy/);
  assert.match(app, /dxy-fx-computed/);
  assert.match(app, /frankfurter-ecb/);
  assert.equal(app.split('return hm ? ("Gold futures (COMEX, front month) · delayed · as of " + hm + " UK")').length, 2);
  assert.equal(app.split('if (b && b.kind === "futures") return "Gold futures (COMEX, front month)";').length, 2);
});

test("desk-quotes sources become Yahoo Finance and market-reference machine ids stay", () => {
  const hCtx = load(blockH);
  const iCtx = load(blockI);
  const desk = {
    source: "Yahoo Finance (GC=F|DX-Y.NYB|^TNX)",
    quotes: {
      XAU: { price: 4050.1, symbol: "GC=F", source: "Yahoo Finance (GC=F)", asOf: "2026-11-10T19:13:00.000Z", displayChange: { symbol: "GC=F", label: "Gold futures (GC=F, delayed 10 min)", text: "gold futures (GC=F) −2.15% today" } },
      DXY: { price: 102.1, symbol: "DX-Y.NYB", source: "Yahoo Finance (DX-Y.NYB)", asOf: "2026-11-10T19:13:00.000Z" },
      TNX: { value: 4.11, symbol: "^TNX", source: "Yahoo Finance (^TNX)", asOf: "2026-11-10T19:13:00.000Z" }
    }
  };
  const out = send(iCtx, JSON.parse(JSON.stringify(desk)), "/api/desk-quotes?symbols=XAU,DXY,TNX");
  assert.equal(out.source, "Yahoo Finance");
  assert.equal(out.sourceLabel, "Yahoo Finance");
  assert.equal(out.quotes.XAU.source, "Yahoo Finance");
  assert.equal(out.quotes.XAU.sourceLabel, "Gold futures (COMEX, front month), Yahoo Finance");
  assert.equal(out.quotes.XAU.symbol, "GC=F");
  assert.equal(out.quotes.XAU.asOf, "2026-11-10T19:13:00.000Z");
  assert.equal(out.quotes.XAU.displayChange.label, "Gold futures (COMEX, front month, delayed 10 min)");
  assert.equal(out.quotes.DXY.source, "Yahoo Finance");
  assert.equal(out.quotes.DXY.sourceLabel, "ICE US Dollar Index, Yahoo Finance");
  assert.equal(out.quotes.TNX.source, "Yahoo Finance");
  assert.equal(out.quotes.TNX.sourceLabel, "CBOE 10-year Treasury yield index, Yahoo Finance");
  assert.equal(out.quotes.TNX.asOf, desk.quotes.TNX.asOf);

  const ref = {
    XAU: { p: 4050.1, source: "gold-api-spot-proxy", asOf: "2026-11-10T19:13:00.000Z", symbol: "XAU" },
    DXY: { p: 99.1, source: "dxy-fx-computed", asOf: "2026-11-10T19:13:00.000Z" },
    EURUSD: { p: 1.08, source: "frankfurter-ecb", asOf: "2026-11-10T19:13:00.000Z" }
  };
  const h = send(hCtx, JSON.parse(JSON.stringify(ref)), "/api/market-reference-quotes");
  const i = send(iCtx, JSON.parse(JSON.stringify(ref)), "/api/market-reference-quotes");
  assert.deepEqual(i, h);
  assert.equal(i.XAU.source, "gold-api-spot-proxy");
  assert.equal(i.DXY.source, "dxy-fx-computed");
  assert.equal(i.EURUSD.source, "frankfurter-ecb");
  assert.equal(i.XAU.asOf, ref.XAU.asOf);

  const live = {
    fetchedAt: 1794332220000,
    XAU: { p: 4050.1, source: "gold-api-spot-proxy", asOf: "2026-11-10T19:37:00.000Z" },
    DXY: { p: 99.4, source: "dxy-fx-computed", asOf: "2026-11-10T19:37:00.000Z" },
    US10Y: { value: 4.11, source: "frankfurter-ecb", asOf: "2026-11-10T19:37:00.000Z" }
  };
  const kept = send(iCtx, JSON.parse(JSON.stringify(live)), "/api/market-reference-quotes");
  const keptH = send(hCtx, JSON.parse(JSON.stringify(live)), "/api/market-reference-quotes");
  assert.deepEqual(kept, keptH);
  assert.equal(Object.prototype.hasOwnProperty.call(kept, "generatedAtUtc"), false);
  assert.equal(typeof kept.fetchedAt, "number");
  assert.equal(kept.fetchedAt, 1794332220000);
  assert.equal(kept.XAU.asOf, live.XAU.asOf);
  assert.equal(kept.DXY.source, "dxy-fx-computed");
  assert.equal(kept.US10Y.source, "frankfurter-ecb");
  const client = fs.readFileSync(path.join(dir, "..", "deploy-chat102", "client_c102.js"), "utf8");
  assert.equal(client.includes("fetchedAt"), false);
  assert.match(client, /uk\(model\.generatedAtUtc\)/);
  const app = fs.readFileSync("/tmp/c102hash/app.js", "utf8");
  assert.match(app, /Number\(data\.fetchedAt\)/);
});

test("scenario copy and the terminal axis label are reader text, and bar dates stay ISO", () => {
  const context = load(blockI);
  const Ctor = context.require("http").ServerResponse;
  const page = new Ctor();
  const html = '<!doctype html><p>real yield, <a href="https://fred.stlouisfed.org/series/DFII10" rel="noopener">FRED series DFII10</a>; dollar, <a href="https://fred.stlouisfed.org/series/DTWEXBGS" rel="noopener">FRED series DTWEXBGS (Federal Reserve broad dollar index)</a>.</p>' +
    "\n    var left = bars[0].sessionDate;\n    var right = bars[bars.length - 1].sessionDate;\n    ctx.fillText(left, padL, h - 8);\n";
  page.end(html);
  const out = page.written;
  assert.match(out, />10-year real yield \(TIPS\), FRED</);
  assert.match(out, />Broad trade-weighted US dollar index, FRED</);
  assert.equal(out.includes(">FRED series DFII10<"), false);
  assert.equal(out.includes(">FRED series DTWEXBGS"), false);
  assert.match(out, /series\/DFII10/);
  assert.match(out, /series\/DTWEXBGS/);
  assert.match(out, /function c102AxisDay/);
  assert.match(out, /c102AxisDay\(bars\[0\]\.sessionDate\)/);
  assert.equal(out.includes("var left = bars[0].sessionDate;"), false);

  const bars = send(context, {
    generatedAtUtc: "2026-11-10T19:37:00.000Z",
    XAU: { p: 1, source: "gold-api-spot-proxy", bars: [{ sessionDate: "2026-11-09", timeUtc: "2026-11-09T05:00:00.000Z", c: 4000 }] }
  }, "/api/c102/terminal");
  assert.equal(bars.XAU.bars[0].sessionDate, "2026-11-09");
  assert.equal(bars.XAU.bars[0].timeUtc, "2026-11-09T05:00:00.000Z");
  assert.equal(bars.generatedAtUtc, "2026-11-10T19:37:00.000Z");
  assert.equal(bars.XAU.source, "gold-api-spot-proxy");
});

test("replacing the scrub block leaves the prefix and patches the client anchors", () => {
  const work = fs.mkdtempSync("/tmp/c102r6i-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = "/* CPI y/y wording. Do not edit. */\nfunction cpiNote(){ return \"year on year\"; }\n";
  const src = fs.readFileSync("/tmp/c102hash/app.js", "utf8");
  fs.writeFileSync(server, cpi + blockH);
  fs.writeFileSync(app, src);
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat104\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6i.py"),
    server, app, index,
    path.join(dir, "server_block_c102r6h.js"),
    path.join(dir, "server_block_c102r6i.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  const fresh = blockI.endsWith("\n") ? blockI : blockI + "\n";
  assert.equal(after.slice(0, cpi.length), cpi);
  assert.equal(after.endsWith(fresh), true);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  const appAfter = fs.readFileSync(app, "utf8");
  assert.match(appAfter, /Yahoo Finance, delayed · as of /);
  assert.match(appAfter, /if \(futK\) return "Gold futures \(COMEX, front month\) · Yahoo Finance, delayed"/);
  assert.match(appAfter, /Gold spot\\b/);
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat102r6i\"></script>\n");
});

test("the CPI region stays byte-identical and one r6i attach log remains", () => {
  const work = fs.mkdtempSync("/tmp/c102r6i-cpi-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = [
    "// chat103 cpi day",
    "const gapRow = { period: \"2025-10\", periodLabel: \"October 2025\", gap: true, yoyLabel: \"Not published by BLS (no October 2025 data)\" };",
    "const gap = base === \"2025-10\" ? \"year-on-year not published by BLS (no October 2025 data)\" : \"published\";",
    "out[k] = { how: \"Year-on-year change against the same month a year earlier (FRED \" + id + \"). A missing month is not filled from a neighbour.\" };",
    ""
  ].join("\n");
  fs.writeFileSync(server, cpi + blockH);
  fs.writeFileSync(app, fs.readFileSync("/tmp/c102hash/app.js"));
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat104\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6i.py"),
    server, app, index,
    path.join(dir, "server_block_c102r6h.js"),
    path.join(dir, "server_block_c102r6i.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const before = fs.readFileSync(server, "utf8");
  // The patch already wrote `before`. Re-read the pre-image from the fixture we still have in `cpi + blockH`.
  const prior = cpi + blockH;
  function cpiRegion(text) {
    const start = text.indexOf("// chat103 cpi day");
    const end = text.indexOf("// chat102r6c last-write scrub.");
    assert.ok(start >= 0 && end > start);
    return text.slice(start, end);
  }
  assert.equal(cpiRegion(before), cpiRegion(prior));
  assert.match(cpiRegion(before), /October 2025/);
  assert.match(cpiRegion(before), /A missing month is not filled from a neighbour/);
  const logs = before.match(/\[c102r6[a-z]?\] scrub attached/g);
  assert.deepEqual(logs, ["[c102r6i] scrub attached"]);
  assert.equal(before.trimEnd().endsWith("})();"), true);
  assert.equal(before.includes("[c102r6h] scrub attached"), false);
});

test("chat104 Learn renames do not move the gold-futures anchors", () => {
  const patch = spawnSync("git", ["show", "f3124f6e3924b40e827c5595f7da27f596e70890:deploy-chat104/patch_c104.py"], { encoding: "utf8" });
  assert.equal(patch.status, 0, patch.stderr);
  const script = [
    "import json, pathlib, sys",
    "ns = {}",
    "exec(sys.stdin.read().split('def tail')[0], ns)",
    "print(json.dumps(ns['PAIRS']))"
  ].join("\n");
  const pairsRun = spawnSync("python3", ["-c", script], { input: patch.stdout, encoding: "utf8" });
  assert.equal(pairsRun.status, 0, pairsRun.stderr);
  const pairs = JSON.parse(pairsRun.stdout).filter(function (pair) { return pair[0] === "app.js"; });
  const anchors = [
    'return hm ? ("Gold futures (COMEX, front month) · delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · delayed";',
    'if (b && b.kind === "futures") return "Gold futures (COMEX, front month)";',
    "function _rtGoldKicker() {\n  // rt14: plain words up front; the provider / status / checked detail moves to the tooltip (_rtGoldKickerTitle).\n  if (typeof livePx === \"function\" && livePx(\"XAU\") != null && liveQuoteSrc.XAU) {",
    'if (fut) html = html.replace(/(\\s*[·|•]\\s*)spot\\b/ig, "");'
  ];
  pairs.forEach(function (pair) {
    anchors.forEach(function (anchor) {
      assert.equal(anchor.includes(pair[1]), false, pair[1]);
      assert.equal(pair[1].includes(anchor), false, pair[1]);
    });
  });
  let app = fs.readFileSync("/tmp/c102hash/app.js", "utf8");
  anchors.forEach(function (anchor) { assert.equal(app.split(anchor).length - 1, 1); });
  pairs.forEach(function (pair) {
    const found = app.split(pair[1]).length - 1;
    if (found === pair[3]) app = app.split(pair[1]).join(pair[2]);
  });
  anchors.forEach(function (anchor) { assert.equal(app.split(anchor).length - 1, 1, anchor.slice(0, 48)); });
});

test("deploy.sh bytes match EXPECTED_SHA256 and the md5 guards are the staged root", () => {
  const specPath = path.join(dir, "EXPECTED_SHA256");
  const deployPath = path.join(dir, "deploy.sh");
  assert.equal(fs.existsSync(specPath) && fs.existsSync(deployPath), true);
  const spec = fs.readFileSync(specPath, "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(deployPath);
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /ebc29e2d257228adf720f98c5f1703fc/);
  assert.match(text, /459d922ab3a3f6e504b0b534b2ea4f5d/);
  assert.match(text, /ea5575ca8b4efc735105872497bbe684/);
  assert.match(text, /bak-chat102r6i/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6i-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + blockH);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6i\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6i.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /ebc29e2d257228adf720f98c5f1703fc/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6i")), false);
});
