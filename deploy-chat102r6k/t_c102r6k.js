"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockK = fs.readFileSync(path.join(dir, "server_block_c102r6k.js"), "utf8");
const blockJ = fs.readFileSync(path.join(dir, "server_block_c102r6j.js"), "utf8");

function load(block) {
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function () {} },
    require: function (name) { if (name !== "http") throw new Error(name); return { ServerResponse: Res }; },
    Buffer: Buffer, JSON: JSON, Object: Object, Array: Array, String: String,
    Intl: Intl, Date: Date, Promise: Promise, Response: function Response() {}, isFinite: isFinite, URL: URL
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
function shell(inner, head) {
  return "<!doctype html><html><head>" + (head || "") + "</head><body>" +
    "<header class=\"site\"><div class=\"wrap\"><nav class=\"nav\"><a href=\"/markets/\">Markets</a><a href=\"/learn/\">Learn</a><a href=\"/data/\">Data</a></nav>" +
    "<form class=\"c97tg\"><button class=\"c97tg-one\">Theme: System</button></form></div></header>" +
    inner + "</body></html>";
}

test("scenario sentence is rewritten in the paragraph and inside the page script", () => {
  const context = load(blockK);
  const html = shell(
    "<main><p class=\"c97s\">Sources: gold, delayed; real yield, <a href=\"https://fred.stlouisfed.org/series/DFII10\" rel=\"noopener\">FRED series DFII10</a>; dollar, <a href=\"https://fred.stlouisfed.org/series/DTWEXBGS\" rel=\"noopener\">FRED series DTWEXBGS (Federal Reserve broad dollar index)</a>. Model rebuilt Tue 10 Nov, 19:08 UK.</p></main>" +
    "<script id=\"c100-insp-js\">var SRC=s===\"DFII10\"?\"daily (FRED series DFII10)\":s===\"DTWEXBGS\"?\"daily (FRED series DTWEXBGS (Federal Reserve broad dollar index))\":\"FRED series \"+s;var line=\"real yield, FRED series DFII10; dollar, FRED series DTWEXBGS\";</script>"
  );
  const out = end(context, { chunk: html, url: "/tools/scenario/" });
  assert.match(out, /real yield: 10-year real yield \(TIPS\), FRED/);
  assert.match(out, /dollar: broad trade-weighted US dollar index, FRED/);
  assert.equal(out.includes("FRED series DFII10"), false);
  assert.equal(out.includes("FRED series DTWEXBGS"), false);
  assert.match(out, /Model rebuilt Tue 10 Nov, 19:08 UK/);
  assert.match(out, /id="c100-insp-js"/);
  assert.match(out, /"FRED series "\+s/);
  const fixer = (out.match(/<script id="c102r6k-scen">[\s\S]*?<\/script>/) || [])[0] || "";
  assert.match(fixer, /id="c102r6k-scen"/);
  assert.equal(fixer.includes("FRED series DFII10"), false);
  assert.equal(fixer.includes("FRED series DTWEXBGS"), false);
  assert.equal((out.match(/<nav class="nav">[\s\S]*?<\/nav>/) || [""])[0].split("<a ").length, 4);
});

test("a later client write of the old sentence is corrected on either theme", () => {
  const context = load(blockK);
  const out = end(context, { chunk: shell("<main><p id=\"src\"></p></main>", ""), url: "/tools/scenario/" });
  const fixer = (out.match(/<script id="c102r6k-scen">([\s\S]*?)<\/script>/) || [])[1];
  assert.ok(fixer);
  function Node(type, name) {
    this.nodeType = type;
    this.nodeName = name;
    this.childNodes = [];
    this.nodeValue = "";
    this.attrs = {};
  }
  Node.prototype.append = function (c) { c.parentNode = this; this.childNodes.push(c); return c; };
  Object.defineProperty(Node.prototype, "textContent", {
    get: function () { return this.nodeType === 3 ? this.nodeValue : this.childNodes.map(function (c) { return c.textContent; }).join(""); },
    set: function (v) { this.childNodes = []; const t = new Node(3, "#text"); t.nodeValue = String(v); this.append(t); }
  });
  const p = new Node(1, "P");
  p.attrs.id = "src";
  p.textContent = "real yield, FRED series DFII10; dollar, FRED series DTWEXBGS (Federal Reserve broad dollar index). Model rebuilt Tue 10 Nov, 19:08 UK.";
  const body = new Node(1, "BODY");
  body.append(p);
  const doc = {
    body: body,
    readyState: "complete",
    documentElement: body,
    querySelectorAll: function () { return [p]; },
    addEventListener: function () {}
  };
  const sandbox = {
    document: doc,
    MutationObserver: function () { this.observe = function () {}; },
    String: String
  };
  vm.createContext(sandbox);
  vm.runInContext(fixer, sandbox);
  assert.equal(p.textContent.includes("FRED series DFII10"), false);
  assert.match(p.textContent, /real yield: 10-year real yield \(TIPS\), FRED/);
  assert.match(p.textContent, /dollar: broad trade-weighted US dollar index, FRED/);
  assert.equal(p.textContent.includes("Federal Reserve broad dollar index"), false);
  assert.match(p.textContent, /Model rebuilt Tue 10 Nov, 19:08 UK/);
});

test("header fits both themes, the Academy footer is only a relabel, and the learn breadcrumb is visible", () => {
  const context = load(blockK);
  const home = end(context, { chunk: shell("<main><h1>Desk</h1></main><footer><a href=\"/about/\">About</a></footer>"), url: "/" });
  assert.match(home, /id="c102r6k-header"/);
  assert.match(home, /min-width:1024px\) and \(max-width:1440px/);
  assert.match(home, /flex-wrap:wrap/);
  assert.match(home, /html\.c97-dark header\.site \.wrap/);
  assert.match(home, /html\.c97-system header\.site \.nav/);
  assert.equal(/nav a\{[^}]*display:\s*none/.test(home), false);
  assert.equal(home.includes("c102r6k-crumb"), false);
  assert.match(home, /<a href="\/about\/">About<\/a>/);
  assert.equal(home.includes("Dispatch Academy"), false);
  const learn = end(context, {
    chunk: shell("<main><h1>Dispatch Academy</h1></main><footer><a href=\"/about/\">About</a> <a href=\"/learn/\">Learn</a></footer>"),
    url: "/learn/"
  });
  assert.match(learn, /<nav class="c102r6k-crumb" aria-label="Breadcrumb"><a href="\/">Home<\/a> › <a href="\/learn\/">Dispatch Academy<\/a><\/nav>/);
  assert.match(learn, /<footer><a href="\/about\/">About<\/a> <a href="\/learn\/">Dispatch Academy<\/a><\/footer>/);
  assert.match(learn, /<a href="\/learn\/">Learn<\/a>/);
  const guide = end(context, {
    chunk: shell("<main><h1>What is a yield</h1></main><footer><a href=\"/learn/\">Dispatch Academy</a></footer>"),
    url: "/learn/?guide=what-is-a-yield"
  });
  assert.match(guide, /<a href="\/learn\/">Dispatch Academy<\/a> › What is a yield<\/nav>/);
  assert.match(guide, /href="\/learn\/"/);
});

test("prose JSON keys lose the series phrase and the sources array does not", () => {
  const context = load(blockK);
  const body = {
    note: "real yield, FRED series DFII10; dollar, FRED series DTWEXBGS",
    text: "Model uses FRED series DFII10",
    sources: ["FRED DFII10", "FRED DTWEXBGS", "FRED series DFII10"],
    fetchedAt: 1794332220000
  };
  const out = JSON.parse(end(context, { chunk: JSON.stringify(body), url: "/api/c101/scenario" }));
  assert.match(out.note, /real yield: 10-year real yield \(TIPS\), FRED/);
  assert.match(out.note, /dollar: broad trade-weighted US dollar index, FRED/);
  assert.equal(out.text.includes("FRED series DFII10"), false);
  assert.deepEqual(out.sources, ["FRED DFII10", "FRED DTWEXBGS", "FRED series DFII10"]);
  assert.equal(out.fetchedAt, 1794332220000);
  assert.equal(typeof out.fetchedAt, "number");
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/api/market-reference-quotes" };
  res.end(JSON.stringify({ fetchedAt: 1794332220000, XAU: { p: 4039.3, source: "gold-api-spot-proxy", asOf: "2026-11-10T21:07:00.000Z" } }));
  const kept = JSON.parse(res.written);
  assert.equal(kept.fetchedAt, 1794332220000);
  assert.equal(Object.prototype.hasOwnProperty.call(kept, "generatedAtUtc"), false);
  assert.equal(kept.XAU.source, "gold-api-spot-proxy");
});

test("the patch leaves the CPI block, app.js and the chat102r6j tag", () => {
  const work = fs.mkdtempSync("/tmp/c102r6k-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = [
    "// chat103 cpi day",
    "const gapRow = { period: \"2025-10\", periodLabel: \"October 2025\", gap: true };",
    "out[k] = { how: \"Year-on-year change against the same month a year earlier. A missing month is not filled from a neighbour.\" };",
    ""
  ].join("\n");
  fs.writeFileSync(server, cpi + blockJ);
  fs.writeFileSync(app, "function paint(){ return \"XAU\"; }\n");
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6j\"></script>\n");
  const appBefore = fs.readFileSync(app);
  const indexBefore = fs.readFileSync(index);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6k.py"), server, app, index,
    path.join(dir, "server_block_c102r6j.js"),
    path.join(dir, "server_block_c102r6k.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  function region(text) {
    return text.slice(text.indexOf("// chat103 cpi day"), text.indexOf("// chat102r6c last-write scrub."));
  }
  assert.equal(region(after), region(cpi + blockJ));
  assert.match(region(after), /October 2025/);
  assert.match(region(after), /A missing month is not filled from a neighbour/);
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6k] scrub attached"]);
  assert.equal(after.includes("[c102r6j] scrub attached"), false);
  assert.equal(after.trimEnd().endsWith("})();"), true);
  assert.equal(after.slice(0, after.indexOf("// chat102r6c last-write scrub.")), (cpi + blockJ).slice(0, (cpi + blockJ).indexOf("// chat102r6c last-write scrub.")));
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  assert.deepEqual(fs.readFileSync(app), appBefore);
  assert.deepEqual(fs.readFileSync(index), indexBefore);
});

test("deploy.sh bytes match EXPECTED_SHA256 and the post-r6j md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /a12d3cfe022ec3990801ef05226fbaa9/);
  assert.match(text, /ac695ac6f0a166c8aa1b8a33ee52763b/);
  assert.match(text, /b2bcb3ce97661e1d8cc016ead643a575/);
  assert.match(text, /bak-chat102r6k/);
  assert.match(text, /app\.js\?v=chat102r6j/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6k-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + blockJ);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6k\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6k.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /a12d3cfe022ec3990801ef05226fbaa9/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
