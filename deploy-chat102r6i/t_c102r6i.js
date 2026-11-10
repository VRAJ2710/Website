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

test("deploy.sh bytes match EXPECTED_SHA256 and the md5 guards are still placeholders", () => {
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
  assert.match(text, /715b843b5e7b15e38a16a6478337d7f94752eeb4da3b902b4bcd60603e15aaa7/);
  assert.match(text, /PENDING_AFTER_CHAT104_CHAT103H_SERVER/);
  assert.match(text, /PENDING_AFTER_CHAT104_CHAT103H_APP/);
  assert.match(text, /PENDING_AFTER_CHAT104_CHAT103H_INDEX/);
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
  assert.match(out, /PENDING_AFTER_CHAT104_CHAT103H_SERVER/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6i")), false);
});
