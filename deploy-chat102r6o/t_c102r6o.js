"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockO = fs.readFileSync(path.join(dir, "server_block_c102r6o.js"), "utf8");
const blockN = fs.readFileSync(path.join(dir, "server_block_c102r6n.js"), "utf8");

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
  assert.ok(body.endsWith("</html>"));
  return body;
}

test("install bar reserves space at 320 and UK UK time becomes UK time", () => {
  const context = load(blockO);
  const before = "<!doctype html><html><head></head><body><footer>Prices last refreshed 19:08 UK UK time. Every time is UK time.</footer><p title=\"Checked 19:08 UK UK time\">midnight UK time</p></body></html>";
  const body = deliver(context, before, "/");
  assert.equal(before.includes("UK UK time"), true);
  assert.equal(body.includes("UK UK time"), false);
  assert.match(body, /19:08 UK time/);
  assert.match(body, /Every time is UK time/);
  assert.match(body, /midnight UK time/);
  assert.match(body, /id="c102r6o-inst"/);
  assert.match(body, /@media \(max-width:390px\)/);
  assert.match(body, /body:has\(#c101-inst\)\{padding-bottom:120px\}/);
  assert.match(body, /max-width:100%/);
  assert.match(body, /id="c102r6o-fix"/);
  assert.equal(body.includes("c101-install-dismissed"), false);
  const code = vm.runInNewContext(body.match(/<script id="c102r6o-fix">([\s\S]*?)<\/script>/)[1] ? "undefined" : "undefined");
  const inner = body.match(/<script id="c102r6o-fix">([\s\S]*?)<\/script>/)[1];
  new vm.Script(inner);
  assert.match(inner, /paddingBottom/);
  assert.match(inner, /childList:true/);
  assert.equal(inner.includes("documentElement"), false);
});

test("glance vendor line, cap rows and news labels", () => {
  const work = fs.mkdtempSync("/tmp/c102r6o-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const beforeApp = [
    'const upd = _lf ? `Prices last refreshed <span class="stf-time">${_rt16Hms(_lf)}</span> UK time` : "";',
    'return `<div class="cap-row"><span class="cap-lbl">${p.lbl}</span><span class="cap-nums">${p.a} — · ${p.b} —</span>`;',
    'return `<div class="cap-row"><span class="cap-nums">${p.a} ${ca >= 0 ? "+" : ""}${ca.toFixed(1)}% · ${p.b} ${cb >= 0 ? "+" : ""}${cb.toFixed(1)}%</span>`;',
    'return `<span class="news-px">${topTk} ${d.p}</span>`;',
    '`${topTk?`<button class="news-act" onclick="openA(\'${topTk}\')">Open ${topTk}</button>`:""}`',
    "function fe83f_afterPaint() {",
    "    try { c102r6nDashGold(); } catch (eN) {}",
    "}"
  ].join("\n");
  fs.writeFileSync(server, "prefix\n" + blockN);
  fs.writeFileSync(app, beforeApp);
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6n\"></script>\n");
  assert.equal(beforeApp.includes("UK time`"), true);
  assert.equal(beforeApp.includes("${p.a} —"), true);
  assert.equal(beforeApp.includes("Open ${topTk}"), true);
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6o.py"), server, app, index,
    path.join(dir, "server_block_c102r6n.js"), path.join(dir, "server_block_c102r6o.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const patched = fs.readFileSync(app, "utf8");
  assert.equal(patched.includes("${_rt16Hms(_lf)}</span> UK time"), false);
  assert.match(patched, /replace\(\/\\s\*UK\\s\*\$\/i, ""\)/);
  assert.match(patched, /p\.a==="XAU"\|\|p\.a==="GC=F"\?"Gold":p\.a/);
  assert.match(patched, /Open Gold/);
  assert.match(patched, /openA\('\$\{topTk\}'\)/);
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat102r6o\"></script>\n");
  const after = fs.readFileSync(server, "utf8");
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6o] scrub attached"]);
  assert.equal(after.slice(0, 7), "prefix\n");
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  const start = patched.indexOf("function c102r6oAfter");
  const end = patched.indexOf("function fe83f_afterPaint");
  const src = patched.slice(start, end) + "\nfunction c102r6nGoldRow(){return {fut:true,src:'yahoo',sym:'GC=F'};}\nfunction c102r6nLine(){return 'Gold futures (COMEX, front month) · Yahoo Finance, delayed';}\n";
  function node(cls, text, attrs) {
    const el = {
      className: cls, attrs: attrs || {}, children: [], childNodes: [], nodeType: 1,
      getAttribute: function (k) { return this.attrs[k] || ""; },
      setAttribute: function (k, v) { this.attrs[k] = String(v); },
      querySelector: function (sel) { return this.querySelectorAll(sel)[0] || null; },
      querySelectorAll: function (sel) {
        const out = [];
        const walk = (n) => { if (n !== this && hit(n, sel)) out.push(n); n.children.forEach(walk); };
        this.children.forEach(walk);
        return out;
      },
      appendChild: function (ch) { ch.parentNode = this; this.children.push(ch); this.childNodes.push(ch); return ch; }
    };
    Object.defineProperty(el, "textContent", {
      get: function () { return this.childNodes.map(function (n) { return n.nodeType === 3 ? n.nodeValue : n.textContent; }).join(""); },
      set: function (v) { const t = { nodeType: 3, nodeValue: String(v), parentNode: this }; this.children = []; this.childNodes = [t]; }
    });
    if (text != null) el.textContent = text;
    return el;
  }
  function hit(n, sel) {
    return String(sel).split(",").some(function (part) {
      part = part.trim();
      return part.charAt(0) === "." && String(n.className || "").split(/\s+/).indexOf(part.slice(1)) >= 0;
    });
  }
  function add(parent, child) { child.parentNode = parent; parent.children.push(child); parent.childNodes.push(child); }
  const chip = node("wl-glance-chip", null, { onclick: "openA('XAU')" });
  add(chip, node("wl-g-tk", "GC=F"));
  add(chip, node("wl-g-p", "4039"));
  add(chip, node("", "GC=F · spot"));
  const cap = node("cap-nums", "XAU +0.4% · DXY +0.1%");
  const news = node("news-px", "XAU 4039");
  const act = node("news-act", "Open XAU", { onclick: "openA('XAU')" });
  const doc = {
    body: node("body", "19:08 UK UK time"),
    createElement: function () { return node("c102r6o-lag", ""); },
    createTreeWalker: function (root) {
      const list = [];
      const walk = (n) => { (n.childNodes || []).forEach(function (c) { if (c.nodeType === 3) list.push(c); else walk(c); }); };
      walk(root);
      return { nextNode: function () { return list.shift() || null; } };
    },
    querySelectorAll: function (sel) { return [chip, cap, news, act].filter(function (n) { return hit(n, sel); }); }
  };
  const box = { document: doc, NodeFilter: { SHOW_TEXT: 4 } };
  vm.createContext(box);
  vm.runInContext(src + "\nc102r6oAfter();", box);
  const visible = chip.textContent;
  assert.equal(/\bGC=F\b|\bXAU\b/.test(visible), false, visible);
  assert.equal(/\bspot\b/i.test(visible), false, visible);
  assert.match(visible, /Gold futures \(COMEX, front month\) · Yahoo Finance, delayed/);
  assert.equal(cap.textContent, "Gold +0.4% · DXY +0.1%");
  assert.equal(news.textContent, "Gold 4039");
  assert.equal(act.textContent, "Open Gold");
  assert.equal(act.attrs.onclick, "openA('XAU')");
  assert.equal(doc.body.textContent, "19:08 UK time");
});

test("deploy.sh bytes match EXPECTED_SHA256 and the live r6n md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /4bfbb35e6854158b8e6e09309aa7aa61/);
  assert.match(text, /bd13a193f2a16ef7d7a4508c25231bb9/);
  assert.match(text, /932c42324a218a02a1bd69f64a6f5757/);
  assert.match(text, /app\.js\?v=chat102r6o/);
  assert.match(text, /bak-chat102r6o/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6o-root-");
  fs.writeFileSync(path.join(root, "server.js"), blockN);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6o\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6o.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /4bfbb35e6854158b8e6e09309aa7aa61/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
