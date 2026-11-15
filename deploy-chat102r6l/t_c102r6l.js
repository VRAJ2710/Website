"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockL = fs.readFileSync(path.join(dir, "server_block_c102r6l.js"), "utf8");
const blockK = fs.readFileSync(path.join(dir, "server_block_c102r6k.js"), "utf8");
const CSS = "#c101-inst{position:fixed;left:12px;right:12px;bottom:12px;z-index:2147482000;max-width:560px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#fff;color:#1b1b1b;border:1px solid #c9c4b8;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:12px 14px;font:14px/1.45 Inter,system-ui,sans-serif}#c101-inst span{flex:1 1 220px}#c101-inst button{min-height:40px;padding:0 14px;border-radius:6px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}";
const INSTALL = "(function(){if(window.__c101i)return;window.__c101i=1;function bar(){if(document.getElementById(\"c101-inst\"))return;var d=document.createElement(\"div\");document.body.appendChild(d)}function go(){if(!ev)return;ev.prompt();var d=document.getElementById(\"c101-inst\");if(d)d.remove()}var ev=null;window.addEventListener(\"beforeinstallprompt\",function(e){e.preventDefault();ev=e;if(!/[?&]source=pwa/.test(location.search))setTimeout(bar,4000)});window.addEventListener(\"appinstalled\",function(){var d=document.getElementById(\"c101-inst\");if(d)d.remove()})})();";

function load(block) {
  function Res() { this.headers = {}; this.headersSent = false; this.chunks = []; }
  Res.prototype.setHeader = function (k, v) { this.headers[String(k).toLowerCase()] = v; };
  Res.prototype.getHeader = function (k) { return this.headers[String(k).toLowerCase()]; };
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  Res.prototype.write = function (chunk) { this.chunks.push(chunk); return true; };
  function c97Transform(html) { return html; }
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer: Buffer, JSON: JSON, Object: Object, Array: Array, String: String,
    Intl: Intl, Date: Date, Promise: Promise, Response: function Response() {}, isFinite: isFinite, URL: URL,
    c97Transform: c97Transform
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(block, context);
  return context;
}
function textOf(body) {
  return Buffer.isBuffer(body) ? body.toString("utf8") : String(body);
}
function page(title, extra) {
  return "<!doctype html><html><head><title>" + title + "</title></head><body>" +
    "<header class=\"site\"><div class=\"wrap\"><nav class=\"nav\"><a href=\"/markets/\">Markets</a><a href=\"/learn/\">Learn</a><a href=\"/cpi/\">CPI</a><a href=\"/terminal/\">Terminal</a></nav>" +
    "<form class=\"c97tg\"><button class=\"c97tg-one\">Theme: System</button></form></div></header>" +
    "<main><h1>" + title + "</h1>" + (extra || "") + "</main>" +
    "<footer><a href=\"/about/\">About</a></footer>" +
    "<style id=\"c101-inst-css\">" + CSS + "</style>" +
    "<script id=\"c101-inst-js\">" + INSTALL + "</script></body></html>";
}
function deliver(context, html, url) {
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: url };
  const out = context.c97Transform(html, res.req);
  const len = Buffer.byteLength(out);
  res.setHeader("Content-Length", len);
  res.headersSent = true;
  res.end(out);
  const body = textOf(res.written);
  assert.equal(Buffer.byteLength(body), len);
  assert.equal(Number(res.getHeader("content-length")), len);
  assert.equal(Buffer.byteLength(body), Buffer.byteLength(out));
  return body;
}
function lastScript(body) {
  const scripts = body.match(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi) || [];
  assert.ok(scripts.length > 0);
  const raw = scripts[scripts.length - 1];
  return raw.replace(/^<script\b[^>]*>/i, "").replace(/<\/script>$/i, "");
}

test("the four r2 pages stay complete and their final script parses", () => {
  const context = load(blockL);
  const pages = [
    ["/", "Home", ""],
    ["/cpi/", "CPI", "<p id=\"cpi-count\">CPI</p>"],
    ["/terminal/", "Terminal", ""],
    ["/tools/scenario/", "Scenario", "<p class=\"c97s\" id=\"c101scen\">real yield, FRED series DFII10; dollar, FRED series DTWEXBGS (Federal Reserve broad dollar index). Model rebuilt Tue 10 Nov, 19:08 UK.</p>"]
  ];
  pages.forEach(function (row) {
    const html = page(row[1], row[2]);
    const body = deliver(context, html, row[0]);
    assert.ok(body.endsWith("</html>"), row[0]);
    assert.equal(body.includes("</script></body></html>") || body.endsWith("</body></html>"), true);
    assert.ok(Buffer.byteLength(body) > Buffer.byteLength(html));
    assert.equal(body.slice(0, Buffer.byteLength(html)).endsWith("</html>"), false);
    assert.match(body, /id="c102r6l-header"/);
    assert.match(body, /flex-wrap:wrap/);
    assert.match(body, /html\.c97-dark header\.site \.nav/);
    assert.match(body, /html\.c97-system header\.site \.wrap/);
    assert.equal(/nav a\{[^}]*display:\s*none/.test(body), false);
    assert.equal((body.match(/<nav class="nav">[\s\S]*?<\/nav>/) || [""])[0].split("<a ").length, 5);
    assert.match(body, /<footer><a href="\/about\/">About<\/a><\/footer>/);
    assert.match(body, /appinstalled/);
    assert.match(body, /document\.getElementById\("c101-inst"\)/);
    new vm.Script(lastScript(body));
    assert.doesNotThrow(function () { new vm.Script(INSTALL); });
  });
  const scenario = deliver(context, page("Scenario", "<p id=\"c101scen\">real yield, <a href=\"https://fred.stlouisfed.org/series/DFII10\">FRED series DFII10</a>; dollar, FRED series DTWEXBGS. Model rebuilt Tue 10 Nov, 19:08 UK.</p>"), "/tools/scenario/");
  assert.match(scenario, /id="c102r6l-scen"/);
  assert.equal(scenario.includes("FRED series DFII10"), false);
  assert.equal(scenario.includes("FRED series DTWEXBGS"), false);
  assert.match(scenario, /real yield: 10-year real yield \(TIPS\), FRED/);
  const fixer = (scenario.match(/<script id="c102r6l-scen">([\s\S]*?)<\/script>/) || [])[1];
  new vm.Script(fixer);
  assert.equal(fixer.includes("FRED series DFII10"), false);
});

test("an end() before headers are sent refreshes Content-Length to the final body", () => {
  const context = load(blockL);
  const html = page("Home", "");
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/" };
  res.setHeader("Content-Length", Buffer.byteLength(html));
  res.end(html);
  const body = textOf(res.written);
  assert.ok(body.endsWith("</html>"));
  assert.equal(Number(res.getHeader("content-length")), Buffer.byteLength(body));
  assert.ok(Buffer.byteLength(body) > Buffer.byteLength(html));
  new vm.Script(lastScript(body));
});

test("the chunked shell gets the header CSS and the learn breadcrumb, with no footer link added", () => {
  const context = load(blockL);
  const Ctor = context.require("http").ServerResponse;
  function stream(url, tail) {
    const res = new Ctor();
    res.req = { url: url };
    res.headersSent = true;
    const head = "<!doctype html><html><head><title>Shell</title></head>";
    res.write(head);
    res.write(tail);
    res.end();
    return textOf(res.chunks[0]) + textOf(res.chunks[1]) + textOf(res.written || "");
  }
  const learn = stream("/learn/?guide=what-is-a-yield", "<body><header class=\"site\"><nav class=\"nav\"><a href=\"/markets/\">Markets</a><a href=\"/learn/\">Learn</a></nav></header><main><h1>What is a yield</h1></main><footer><a href=\"/about/\">About</a></footer></body></html>");
  assert.match(learn, /id="c102r6l-header"/);
  assert.match(learn, /id="c102r6l-crumb-js"/);
  assert.match(learn, /<nav class="c102r6l-crumb" aria-label="Breadcrumb"><a href="\/">Home<\/a> › <a href="\/learn\/">Dispatch Academy<\/a> › What is a yield<\/nav>/);
  assert.match(learn, /<footer><a href="\/about\/">About<\/a><\/footer>/);
  assert.equal(/nav a\{[^}]*display:\s*none/.test(learn), false);
  const dash = stream("/dashboard/", "<body><header class=\"site\"><nav class=\"nav\"><a href=\"/markets/\">Markets</a><a href=\"/learn/\">Learn</a></nav></header><div id=\"app\"></div><footer><a href=\"/about/\">About</a></footer></body></html>");
  assert.match(dash, /id="c102r6l-header"/);
  assert.match(dash, /id="c102r6l-crumb-js"/);
  assert.equal(dash.includes("<nav class=\"c102r6l-crumb\""), false);
  assert.match(dash, /<a href="\/learn\/">Learn<\/a>/);
  assert.match(dash, /<footer><a href="\/about\/">About<\/a><\/footer>/);
});

test("prose JSON keys lose the series phrase and the sources array does not", () => {
  const context = load(blockL);
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/api/c101/scenario" };
  res.end(JSON.stringify({
    note: "real yield, FRED series DFII10; dollar, FRED series DTWEXBGS",
    text: "Model uses FRED series DFII10",
    sources: ["FRED DFII10", "FRED DTWEXBGS", "FRED series DFII10"],
    fetchedAt: 1794332220000
  }));
  const out = JSON.parse(textOf(res.written));
  assert.match(out.note, /real yield: 10-year real yield \(TIPS\), FRED/);
  assert.equal(out.text.includes("FRED series DFII10"), false);
  assert.deepEqual(out.sources, ["FRED DFII10", "FRED DTWEXBGS", "FRED series DFII10"]);
  assert.equal(out.fetchedAt, 1794332220000);
  assert.equal(typeof out.fetchedAt, "number");
});

test("the patch leaves the CPI block, app.js and the chat102r6j tag", () => {
  const work = fs.mkdtempSync("/tmp/c102r6l-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = [
    "// chat103 cpi day",
    "const gapRow = { period: \"2025-10\", periodLabel: \"October 2025\", gap: true };",
    "out[k] = { how: \"Year-on-year change against the same month a year earlier. A missing month is not filled from a neighbour.\" };",
    ""
  ].join("\n");
  fs.writeFileSync(server, cpi + blockK);
  fs.writeFileSync(app, "function paint(){ return \"XAU\"; }\n");
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6j\"></script>\n");
  const appBefore = fs.readFileSync(app);
  const indexBefore = fs.readFileSync(index);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6l.py"), server, app, index,
    path.join(dir, "server_block_c102r6k.js"),
    path.join(dir, "server_block_c102r6l.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  function region(text) {
    return text.slice(text.indexOf("// chat103 cpi day"), text.indexOf("// chat102r6c last-write scrub."));
  }
  assert.equal(region(after), region(cpi + blockK));
  assert.match(region(after), /October 2025/);
  assert.match(region(after), /A missing month is not filled from a neighbour/);
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6l] scrub attached"]);
  assert.equal(after.includes("[c102r6k] scrub attached"), false);
  assert.equal(after.trimEnd().endsWith("})();"), true);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  assert.deepEqual(fs.readFileSync(app), appBefore);
  assert.deepEqual(fs.readFileSync(index), indexBefore);
});

test("deploy.sh bytes match EXPECTED_SHA256 and the post-r6k md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /874a0374c9c8a4cc9a87031f2f4a350c/);
  assert.match(text, /ac695ac6f0a166c8aa1b8a33ee52763b/);
  assert.match(text, /b2bcb3ce97661e1d8cc016ead643a575/);
  assert.match(text, /bak-chat102r6l/);
  assert.match(text, /app\.js\?v=chat102r6j/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6l-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + blockK);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6l\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6l.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /874a0374c9c8a4cc9a87031f2f4a350c/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
