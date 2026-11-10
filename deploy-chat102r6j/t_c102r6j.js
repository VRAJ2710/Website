"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockJ = fs.readFileSync(path.join(dir, "server_block_c102r6j.js"), "utf8");
const blockI = fs.readFileSync(path.join(dir, "server_block_c102r6i.js"), "utf8");
const SPINE_OLD = "    var tk = el.querySelector(\".spine-tk\");\n    if (!tk || String(tk.textContent || \"\").trim() !== \"XAU\") return;";
const STAT_OLD = 'if (fut) html = html.replace(/\\bSPOT\\b/g, "DELAYED").replace(/(\\s*[·|•]\\s*)spot\\b/ig, "").replace(/\\bGold spot\\b/g, "Gold futures (COMEX, front month)");';

function load(block) {
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer: Buffer, JSON: JSON, Object: Object, Array: Array, String: String,
    Intl: Intl, Date: Date, Promise: Promise, Response: function Response() {}, isFinite: isFinite
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(block, context);
  return context;
}
function end(context, body) {
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  if (body && body.url) res.req = { url: body.url };
  res.end(body.chunk);
  return res.written;
}

test("scenario sources read as plain names with or without the link tags", () => {
  const context = load(blockJ);
  const linked = '<!doctype html><p class="c97s">Sources: gold, delayed; real yield, <a href="https://fred.stlouisfed.org/series/DFII10" rel="noopener">FRED series DFII10</a>; dollar, <a href="https://fred.stlouisfed.org/series/DTWEXBGS" rel="noopener">FRED series DTWEXBGS (Federal Reserve broad dollar index)</a>. Model rebuilt Tue 10 Nov, 19:08 UK.</p>';
  const plain = "<p>real yield, FRED series DFII10; dollar, FRED series DTWEXBGS. Model rebuilt Tue 10 Nov, 19:08 UK.</p>";
  [linked, plain].forEach(function (html) {
    const out = end(context, { chunk: html });
    assert.match(out, /real yield: 10-year real yield \(TIPS\), FRED/);
    assert.match(out, /dollar: broad trade-weighted US dollar index, FRED/);
    assert.equal(out.includes("FRED series DFII10"), false);
    assert.equal(out.includes("FRED series DTWEXBGS"), false);
    assert.match(out, /Model rebuilt Tue 10 Nov, 19:08 UK/);
  });
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/api/market-reference-quotes" };
  res.end(JSON.stringify({ fetchedAt: 1794332220000, XAU: { p: 4039.3, source: "gold-api-spot-proxy", asOf: "2026-11-10T21:07:00.000Z" } }));
  const kept = JSON.parse(res.written);
  assert.equal(kept.fetchedAt, 1794332220000);
  assert.equal(typeof kept.fetchedAt, "number");
  assert.equal(Object.prototype.hasOwnProperty.call(kept, "generatedAtUtc"), false);
  assert.equal(kept.XAU.source, "gold-api-spot-proxy");
});

test("the desk-spine anchors are the post-r6i strings and the patch leaves the CPI block", () => {
  const known = fs.readFileSync("/tmp/c102hash/app.js", "utf8");
  assert.equal(known.split('if (!tk || String(tk.textContent || "").trim() !== "XAU") return;').length, 2);
  const work = fs.mkdtempSync("/tmp/c102r6j-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = [
    "// chat103 cpi day",
    "const gapRow = { period: \"2025-10\", periodLabel: \"October 2025\", gap: true };",
    "out[k] = { how: \"Year-on-year change against the same month a year earlier. A missing month is not filled from a neighbour.\" };",
    ""
  ].join("\n");
  fs.writeFileSync(server, cpi + blockI);
  fs.writeFileSync(app, "function paint(el, b) {\n" + SPINE_OLD + "\n  return tk;\n}\nfunction stat(fut, html) {\n  " + STAT_OLD + "\n  return html;\n}\n");
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6i\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6j.py"), server, app, index,
    path.join(dir, "server_block_c102r6i.js"),
    path.join(dir, "server_block_c102r6j.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  function region(text) {
    return text.slice(text.indexOf("// chat103 cpi day"), text.indexOf("// chat102r6c last-write scrub."));
  }
  assert.equal(region(after), region(cpi + blockI));
  assert.match(region(after), /October 2025/);
  assert.match(region(after), /A missing month is not filled from a neighbour/);
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6j] scrub attached"]);
  assert.equal(after.includes("[c102r6i] scrub attached"), false);
  assert.equal(after.trimEnd().endsWith("})();"), true);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  const appAfter = fs.readFileSync(app, "utf8");
  assert.match(appAfter, />\(\\s\*\)spot\(\s\*\)Futures|>\(\s*\)spot\(\s*\)<|Futures/);
  assert.match(appAfter, /tk\.textContent = "Gold futures"/);
  assert.match(appAfter, /badges\[bi\]\.textContent = "Futures"/);
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat102r6j\"></script>\n");
});

test("deploy.sh bytes match EXPECTED_SHA256 and the staged md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /aeeb6218efa701603d1490e41bfff24c/);
  assert.match(text, /274cc52857487668b70810753a62115d/);
  assert.match(text, /5e13c195b7014abf2824ec7e8d634693/);
  assert.match(text, /bak-chat102r6j/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6j-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + blockI);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6j\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6j.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /aeeb6218efa701603d1490e41bfff24c/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
