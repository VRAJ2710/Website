"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockN = fs.readFileSync(path.join(dir, "server_block_c102r6n.js"), "utf8");
const blockM = fs.readFileSync(path.join(dir, "server_block_c102r6m.js"), "utf8");

function load(block) {
  function Res() { this.headers = {}; this.headersSent = false; }
  Res.prototype.setHeader = function (k, v) { this.headers[String(k).toLowerCase()] = v; };
  Res.prototype.getHeader = function (k) { return this.headers[String(k).toLowerCase()]; };
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  Res.prototype.write = function () { return true; };
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
function textOf(body) { return Buffer.isBuffer(body) ? body.toString("utf8") : String(body); }

test("the learn breadcrumb is gone and the other r6 fixes stay", () => {
  const context = load(blockN);
  const html = "<!doctype html><html><head></head><body>" +
    "<header class=\"site\"><nav class=\"nav\"><a href=\"/learn/\">Learn</a></nav></header>" +
    "<main><h1>How to Read the Markets Table</h1>" +
    "<nav class=\"c102r6m-crumb\" aria-label=\"Breadcrumb\"><a href=\"/\">Home</a> › <a href=\"/learn/\">Dispatch Academy</a></nav>" +
    "<script id=\"c102r6l-crumb-js\">paint()</script>" +
    "<p>US Treasury daily print via FRED (DGS10)</p></main></body></html>";
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/learn/?guide=how-to-read-the-markets-table" };
  const out = context.c97Transform(html, res.req);
  const len = Buffer.byteLength(out);
  res.setHeader("Content-Length", len);
  res.headersSent = true;
  res.end(out);
  const body = textOf(res.written);
  assert.equal(Buffer.byteLength(body), Number(res.getHeader("content-length")));
  assert.ok(body.endsWith("</html>"));
  assert.equal(body.includes("c102r6m-crumb"), false);
  assert.equal(body.includes("c102r6l-crumb"), false);
  assert.equal(body.includes("c102r6n-crumb"), false);
  assert.equal(body.includes("Home ›"), false);
  assert.match(body, /id="c102r6n-header"/);
  assert.match(body, /id="c102r6n-fred"/);
  assert.match(body, />10-year Treasury yield, FRED</);
  assert.match(body, /<a href="\/learn\/">Learn<\/a>/);
});

function el(cls, attrs, text) {
  const node = {
    className: cls || "",
    attrs: Object.assign({}, attrs),
    children: [],
    childNodes: [],
    nodeType: 1,
    parentNode: null,
    getAttribute: function (k) { return this.attrs[k] || ""; },
    setAttribute: function (k, v) { this.attrs[k] = String(v); },
    querySelector: function (sel) { return this.querySelectorAll(sel)[0] || null; },
    querySelectorAll: function (sel) {
      const out = [];
      const walk = (n) => {
        if (n !== this && matches(n, sel)) out.push(n);
        n.children.forEach(walk);
      };
      this.children.forEach(walk);
      return out;
    }
  };
  Object.defineProperty(node, "textContent", {
    get: function () { return this.childNodes.map(function (n) { return n.nodeType === 3 ? n.nodeValue : n.textContent; }).join(""); },
    set: function (v) { this.children = []; this.childNodes = [{ nodeType: 3, nodeValue: String(v), parentNode: this }]; }
  });
  if (text != null) node.textContent = text;
  return node;
}
function matches(node, sel) {
  return String(sel).split(",").some(function (part) {
    part = part.trim();
    if (part.charAt(0) === ".") return String(node.className || "").split(/\s+/).indexOf(part.slice(1)) >= 0;
    return false;
  });
}
function add(parent, child) { child.parentNode = parent; parent.children.push(child); parent.childNodes.push(child); return child; }

test("dashboard gold labels follow a Yahoo futures quote and a gold-api spot quote", () => {
  const work = fs.mkdtempSync("/tmp/c102r6n-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  fs.writeFileSync(server, "// chat103 cpi day\nconst gap = \"October 2025\";\n" + blockM);
  fs.writeFileSync(app, "function fe83f_afterPaint() {\n    try { fe83f_paintGold(); } catch (e2) {}\n    try { fe83f_paintDays(); } catch (e3) {}\n}\n");
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6m\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6n.py"), server, app, index,
    path.join(dir, "server_block_c102r6m.js"), path.join(dir, "server_block_c102r6n.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const patched = fs.readFileSync(app, "utf8");
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat102r6n\"></script>\n");
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  const after = fs.readFileSync(server, "utf8");
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6n] scrub attached"]);
  assert.match(after, /October 2025/);
  const start = patched.indexOf("function c102r6nGoldRow");
  const end = patched.indexOf("function fe83f_afterPaint");
  const src = patched.slice(start, end);
  function paint(row) {
    const spine = el("spine-cell", { onclick: "setLabTicker('XAU');nav('lab')" });
    add(spine, el("spine-lbl", {}, "Gold spot"));
    add(spine, el("spine-tk", {}, "XAU"));
    add(spine, el("spine-px", {}, "4039"));
    add(spine, el("spine-chg", {}, "+0.4%"));
    add(spine, el("spine-asof", {}, "spot · as of 19:08 UK"));
    const glance = el("wl-glance-chip", { onclick: "openA('XAU')" });
    add(glance, el("wl-g-tk", {}, "GC=F"));
    add(glance, el("wl-g-p", {}, "4039"));
    add(glance, el("wl-g-c", {}, "Gold spot +0.4%"));
    add(glance, el("", {}, "GC=F · delayed"));
    const conv = el("conv-card", { "data-price-card": "XAU" });
    add(conv, el("conv-tk", {}, "XAU"));
    add(conv, el("conv-nm", {}, "Gold spot"));
    add(conv, el("conv-chg", {}, "spot"));
    add(conv, el("asof-tag", {}, "as of 19:08 UK"));
    const oil = el("spine-cell", { onclick: "setLabTicker('WTI');nav('lab')" });
    add(oil, el("spine-lbl", {}, "Oil"));
    add(oil, el("spine-tk", {}, "WTI"));
    const doc = {
      querySelectorAll: function (sel) { return [spine, glance, conv, oil].filter(function (n) { return matches(n, sel); }); }
    };
    const box = { document: doc, fe79_srv: { XAU: row }, liveQuoteSrc: {} };
    vm.createContext(box);
    vm.runInContext(src + "\nc102r6nDashGold();", box);
    return { spine: spine, glance: glance, conv: conv, oil: oil };
  }
  const yahoo = paint({ source: "yahoo", symbol: "GC=F", instrument: "futures", displayChange: { instrument: "futures", symbol: "GC=F" } });
  [yahoo.spine, yahoo.glance, yahoo.conv].forEach(function (node) {
    const visible = node.textContent;
    assert.equal(/\bXAU\b|\bGC=F\b/.test(visible), false, visible);
    assert.equal(/\bspot\b/i.test(visible), false, visible);
    assert.match(visible, /futures/i);
  });
  assert.match(yahoo.spine.textContent, /Gold futures \(COMEX, front month\) · Yahoo Finance, delayed/);
  assert.match(yahoo.spine.textContent, /as of 19:08 UK/);
  assert.match(yahoo.glance.textContent, /Yahoo Finance, delayed/);
  assert.equal(yahoo.oil.textContent, "OilWTI");
  const api = paint({ source: "gold-api-spot-proxy", instrument: "spot", symbol: "XAU" });
  assert.match(api.spine.textContent, /spot/i);
  assert.equal(/\bXAU\b|\bGC=F\b/.test(api.spine.textContent), false);
  assert.equal(/\bfutures\b/i.test(api.conv.querySelector(".conv-nm").textContent), false);
});

test("deploy.sh bytes match EXPECTED_SHA256 and the post-r6m md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /66bc9ed04f25962a918fe200b0f87daa/);
  assert.match(text, /361862363f6e4dccc88915751cc50169/);
  assert.match(text, /9b5238f41f06ca0d5f413155862f050a/);
  assert.match(text, /app\.js\?v=chat102r6n/);
  assert.match(text, /bak-chat102r6n/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6n-root-");
  fs.writeFileSync(path.join(root, "server.js"), blockM);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6n\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6n.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /66bc9ed04f25962a918fe200b0f87daa/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
