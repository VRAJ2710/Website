"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockM = fs.readFileSync(path.join(dir, "server_block_c102r6m.js"), "utf8");
const blockL = fs.readFileSync(path.join(dir, "server_block_c102r6l.js"), "utf8");

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
function scriptText(block, id) {
  const exprStart = block.indexOf("'<script id=\"" + id + "\">");
  const exprEnd = block.indexOf("</script>';", exprStart) + "</script>';".length;
  const html = vm.runInNewContext(block.slice(exprStart, exprEnd));
  return html.replace(/^<script[^>]*>/, "").replace(/<\/script>$/, "");
}

test("the learn breadcrumb settles and uses the guide title", () => {
  const code = scriptText(blockM, "c102r6m-crumb-js");
  assert.equal(code.includes("documentElement"), false);
  assert.match(code, /disconnect\(\)/);
  let writes = 0;
  let callbacks = 0;
  function fire(node) {
    let n = node;
    while (n) {
      if (n.__mo && n.__mo.on) {
        callbacks++;
        if (callbacks > 30) throw new Error("breadcrumb observer did not settle");
        const mo = n.__mo;
        mo.cb([]);
        return;
      }
      n = n.parentNode;
    }
  }
  class El {
    constructor(tag) {
      this.nodeType = 1;
      this.tagName = tag.toUpperCase();
      this.nodeName = this.tagName;
      this.childNodes = [];
      this.attrs = {};
      this.parentNode = null;
    }
    getAttribute(k) { return this.attrs[k] == null ? null : this.attrs[k]; }
    setAttribute(k, v) { this.attrs[k] = String(v); }
    get className() { return this.attrs.class || ""; }
    set className(v) { this.attrs.class = String(v); }
    closest(sel) {
      const parts = sel.split(",").map(function (s) { return s.trim(); });
      let n = this;
      while (n) {
        if (n.nodeType === 1 && parts.indexOf(n.tagName.toLowerCase()) >= 0) return n;
        n = n.parentNode;
      }
      return null;
    }
    querySelector(sel) { const all = this.querySelectorAll(sel); return all[0] || null; }
    querySelectorAll(sel) {
      const out = [];
      const walk = (n) => {
        if (n !== this && n.nodeType === 1 && matches(n, sel)) out.push(n);
        (n.childNodes || []).forEach(walk);
      };
      this.childNodes.forEach(walk);
      return out;
    }
    appendChild(ch) { ch.parentNode = this; this.childNodes.push(ch); fire(this); return ch; }
    insertBefore(ch) { return this.appendChild(ch); }
    get textContent() { return this.childNodes.map(function (c) { return c.textContent; }).join(""); }
    set innerHTML(v) {
      writes++;
      if (writes > 8) throw new Error("breadcrumb rewrote itself " + writes + " times");
      this.childNodes = [];
      const t = { nodeType: 3, nodeValue: String(v), childNodes: [], parentNode: this, textContent: String(v) };
      this.appendChild(t);
    }
  }
  function matches(el, sel) {
    if (sel === "main") return el.tagName === "MAIN";
    if (sel === "#app") return el.attrs.id === "app";
    if (sel === "h1") return el.tagName === "H1";
    if (sel === "article h1") return el.tagName === "H1" && el.parentNode && el.parentNode.tagName === "ARTICLE";
    if (sel === "main h1") return el.tagName === "H1" && !!el.closest("main");
    if (sel === "[data-guide-title]") return el.attrs["data-guide-title"] != null;
    if (sel === "nav.c102r6m-crumb") return el.tagName === "NAV" && el.attrs.class === "c102r6m-crumb";
    return false;
  }
  function h1(text, parent) {
    const el = new El("h1");
    el.childNodes = [{ nodeType: 3, textContent: text, parentNode: el }];
    parent.appendChild(el);
    return el;
  }
  const header = new El("header");
  const main = new El("main");
  const body = new El("body");
  body.appendChild(header);
  body.appendChild(main);
  h1("The Dispatch Markets", header);
  h1("Dispatch Academy", main);
  const doc = {
    body: body,
    title: "Dispatch Academy",
    readyState: "complete",
    createElement: function (tag) { return new El(tag); },
    querySelector: function (sel) { return body.querySelector(sel); },
    querySelectorAll: function (sel) { return body.querySelectorAll(sel); }
  };
  class MO {
    constructor(cb) { this.cb = cb; this.on = false; }
    observe(target) { this.on = true; this.t = target; target.__mo = this; }
    disconnect() { this.on = false; if (this.t && this.t.__mo === this) this.t.__mo = null; }
  }
  const sandbox = {
    document: doc,
    location: { pathname: "/learn/", search: "?guide=how-to-read-the-markets-table" },
    MutationObserver: MO,
    URLSearchParams: URLSearchParams
  };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  assert.equal(writes, 1);
  assert.match(main.textContent, /Home<\/a> › <a href="\/learn\/">Dispatch Academy/);
  assert.equal(main.textContent.includes("How to Read"), false);
  const before = writes;
  for (let i = 0; i < 6; i++) main.appendChild(new El("span"));
  assert.equal(writes, before);
  assert.ok(callbacks <= 6);
  const article = new El("article");
  main.appendChild(article);
  h1("How to Read the Markets Table", article);
  assert.match(main.textContent, /How to Read the Markets Table/);
  assert.equal(main.textContent.includes("how to read the markets table"), false);
  const settled = writes;
  assert.ok(settled <= 3);
  const calls = callbacks;
  main.appendChild(new El("p"));
  assert.equal(writes, settled);
  assert.equal(callbacks, calls);
});

test("visible FRED ids become plain names and hrefs, scripts and machine fields stay", () => {
  const context = load(blockM);
  const html = "<!doctype html><html><head></head><body>" +
    "<p>US Treasury daily print via FRED (DGS10)</p>" +
    "<p title=\"FRED (DFII10)\">real yield</p>" +
    "<a href=\"https://fred.stlouisfed.org/series/DGS10\">series page</a>" +
    "<script>var keep = \"FRED (DGS10)\"; if (s===\"DGS10\") {}</script>" +
    "</body></html>";
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  res.req = { url: "/brief/" };
  const out = context.c97Transform(html, res.req);
  const len = Buffer.byteLength(out);
  res.setHeader("Content-Length", len);
  res.headersSent = true;
  res.end(out);
  const body = textOf(res.written);
  assert.equal(Buffer.byteLength(body), len);
  assert.ok(body.endsWith("</html>"));
  assert.match(body, />10-year Treasury yield, FRED</);
  assert.match(body, /title="10-year real yield \(TIPS\), FRED"/);
  assert.match(body, /href="https:\/\/fred\.stlouisfed\.org\/series\/DGS10"/);
  assert.match(body, /<script>var keep = "FRED \(DGS10\)"/);
  assert.match(body, /id="c102r6m-fred"/);
  assert.equal(scriptText(blockM, "c102r6m-fred").includes("MutationObserver"), false);
  const api = new Ctor();
  api.req = { url: "/api/brief" };
  api.end(JSON.stringify({
    source: "US Treasury via FRED (DGS10), 10-year constant-maturity yield",
    note: "Official print FRED (DFII10)",
    series: "DGS10-machine"
  }));
  const kept = JSON.parse(textOf(api.written));
  assert.equal(kept.source, "US Treasury via FRED (DGS10), 10-year constant-maturity yield");
  assert.equal(kept.series, "DGS10-machine");
  assert.equal(kept.note.includes("DFII10"), false);
  assert.match(kept.note, /10-year real yield \(TIPS\), FRED/);
  const fixer = scriptText(blockM, "c102r6m-fred");
  const shown = { nodeType: 3, nodeValue: "US Treasury daily print via FRED (DGS10)", parentNode: { tagName: "P" } };
  const hidden = { nodeType: 3, nodeValue: "FRED (DFII10)", parentNode: { tagName: "SCRIPT" } };
  const titled = { tagName: "ABBR", getAttribute: function () { return "FRED (DGS10)"; }, setAttribute: function (k, v) { this.title = v; } };
  const root = {
    createTreeWalker: function () {
      const nodes = [shown, hidden];
      return { nextNode: function () { return nodes.shift() || null; } };
    },
    querySelectorAll: function () { return [titled]; }
  };
  vm.runInNewContext(fixer, { document: { body: root, createTreeWalker: root.createTreeWalker, readyState: "complete", addEventListener: function () {} }, window: { addEventListener: function () {} }, NodeFilter: { SHOW_TEXT: 4 }, setTimeout: function () {} });
  assert.equal(shown.nodeValue, "10-year Treasury yield, FRED");
  assert.equal(hidden.nodeValue, "FRED (DFII10)");
  assert.equal(titled.title, "10-year Treasury yield, FRED");
});

test("the gold label uses the displayed source and the tag becomes chat102r6m", () => {
  const work = fs.mkdtempSync("/tmp/c102r6m-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = [
    "// chat103 cpi day",
    "const gapRow = { period: \"2025-10\", periodLabel: \"October 2025\", gap: true };",
    "out[k] = { how: \"Year-on-year change against the same month a year earlier. A missing month is not filled from a neighbour.\" };",
    ""
  ].join("\n");
  const appSrc = [
    "function _rtGoldKicker() {",
    "  var futK = false;",
    "  if (futK) return \"Gold futures (COMEX, front month) · Yahoo Finance, delayed\";",
    "}",
    "function _quoteSourceLabel(src) {",
    "  if (b && b.kind === \"futures\") return \"Gold futures (COMEX, front month) · Yahoo Finance, delayed\";",
    "}",
    "function fe85_asofBits() {",
    "  return hm ? (\"Gold futures (COMEX, front month) · Yahoo Finance, delayed · as of \" + hm + \" UK\") : \"Gold futures (COMEX, front month) · Yahoo Finance, delayed\";",
    "}",
    ""
  ].join("\n");
  fs.writeFileSync(server, cpi + blockL);
  fs.writeFileSync(app, appSrc);
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat102r6j\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6m.py"), server, app, index,
    path.join(dir, "server_block_c102r6l.js"),
    path.join(dir, "server_block_c102r6m.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  function region(text) {
    return text.slice(text.indexOf("// chat103 cpi day"), text.indexOf("// chat102r6c last-write scrub."));
  }
  assert.equal(region(after), region(cpi + blockL));
  assert.match(region(after), /October 2025/);
  assert.match(region(after), /A missing month is not filled from a neighbour/);
  assert.deepEqual(after.match(/\[c102r6[a-z]?\] scrub attached/g), ["[c102r6m] scrub attached"]);
  assert.equal(after.trimEnd().endsWith("})();"), true);
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat102r6m\"></script>\n");
  const patched = fs.readFileSync(app, "utf8");
  assert.equal(patched.includes("Gold futures (COMEX, front month) · Yahoo Finance, delayed"), false);
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  const start = patched.indexOf("function c102r6mVendor");
  const end = patched.indexOf("function fe85_asofBits");
  const helper = patched.slice(start, end);
  function label(held, live) {
    const box = { fe81_goldHeld: function () { return held; }, liveQuoteSrc: live || {}, out: "" };
    vm.createContext(box);
    vm.runInContext(helper + "\nout = c102r6mGoldLabel('futures');", box);
    return box.out;
  }
  assert.equal(label({ source: "twelve-data", instrument: "spot" }), "Gold · Twelve Data, delayed");
  assert.equal(label({ source: "twelve-data", instrument: "futures" }), "Gold futures (COMEX, front month) · Twelve Data, delayed");
  assert.equal(label({ source: "gold-api-spot-proxy", instrument: "futures" }), "Gold · gold-api");
  assert.equal(label({ source: "yahoo", instrument: "futures" }), "Gold futures (COMEX, front month) · Yahoo Finance, delayed");
  assert.equal(label(null, { "GC=F": "yahoo" }), "Gold futures (COMEX, front month) · Yahoo Finance, delayed");
  ["twelve-data", "yahoo", "gold-api-spot-proxy"].forEach(function (src) {
    const line = label({ source: src, instrument: src.indexOf("yahoo") >= 0 ? "futures" : "spot" });
    assert.equal(/\bGC=F\b|\bXAU\b/.test(line), false);
    assert.equal(/\bspot\b/i.test(line), false);
  });
});

test("deploy.sh bytes match EXPECTED_SHA256 and the post-r6l md5s", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
  const text = buf.toString("utf8");
  assert.match(text, /7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef/);
  assert.match(text, /0e365bf63b69fe7cdbf7223528938902/);
  assert.match(text, /ac695ac6f0a166c8aa1b8a33ee52763b/);
  assert.match(text, /b2bcb3ce97661e1d8cc016ead643a575/);
  assert.match(text, /app\.js\?v=chat102r6m/);
  assert.match(text, /bak-chat102r6m/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6m-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + blockL);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6m\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6m.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /0e365bf63b69fe7cdbf7223528938902/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
});
