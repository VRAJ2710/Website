"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const block = fs.readFileSync(path.join(dir, "server_block_c102r6c.js"), "utf8");
const RX = /GC=F|DX-Y|\^TNX|=X\b|\^VIX|\^GSPC|CL=F|BTC-USD/;
const SKIP = new Set(["symbol", "symbols", "id", "wire"]);

function readerStrings(value, key, acc) {
  if (typeof value === "string") {
    if (!key || !SKIP.has(key)) acc.push(value);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(function (item) { readerStrings(item, key, acc); });
    return;
  }
  if (value && typeof value === "object") Object.keys(value).forEach(function (k) { readerStrings(value[k], k, acc); });
}

test("a shaper that re-adds GC=F after an early scrub is cleaned at res.end", () => {
  const logs = [];
  function Res() {}
  Res.prototype.end = function (chunk) { this.written = chunk; return this; };
  const context = {
    console: { log: function (line) { logs.push(String(line)); } },
    require: function (name) {
      if (name !== "http") throw new Error("unexpected require " + name);
      return { ServerResponse: Res };
    },
    Buffer: Buffer,
    JSON: JSON,
    Object: Object,
    Array: Array,
    String: String,
    Promise: Promise
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(`
    function bb8oShape(res, status, body) {
      var out = Object.assign({}, body);
      out.XAU = Object.assign({}, body.XAU || {}, {
        displayChangeLabel: "Gold futures (GC=F, delayed 10 min)",
        displayChange: {
          symbol: "GC=F",
          label: "Gold futures (GC=F, delayed 10 min)",
          text: "gold futures (GC=F) \\u22121.43% today",
          note: "the change shown is the change in gold futures (GC=F). It is not spot's change."
        }
      });
      out.US10Y = Object.assign({}, body.US10Y || {}, {
        symbol: "^TNX",
        value: 4.99,
        source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)"
      });
      return out;
    }
    function addRaw(body) {
      var out = Object.assign({}, body);
      out.XAU = Object.assign({}, body.XAU || {}, {
        displayChangeLabel: "Gold futures (GC=F, delayed 10 min)",
        displayChange: {
          symbol: "GC=F",
          label: "Gold futures (GC=F, delayed 10 min)",
          text: "gold futures (GC=F) \\u22121.43% today",
          note: "the change shown is the change in gold futures (GC=F). It is not spot's change."
        }
      });
      out.US10Y = Object.assign({}, body.US10Y || {}, {
        symbol: "^TNX",
        value: 4.99,
        source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)"
      });
      return out;
    }
    function json(res, status, body) {
      if (body && body.XAU) {
        body = Object.assign({}, body, { XAU: Object.assign({}, body.XAU, { displayChangeLabel: "Gold futures (COMEX, front month), delayed 10 min" }) });
      }
      var shaped = addRaw(body);
      res.end(JSON.stringify(shaped));
    }
  `, context);
  vm.runInContext(block, context);
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  context.json(res, 200, { XAU: { p: 4050.1, label: "Gold spot" }, US10Y: { symbol: "^TNX", value: 4.99, source: "Yahoo Finance" } });
  const body = JSON.parse(res.written);
  assert.equal(body.XAU.displayChangeLabel, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChange.label, "Gold futures (COMEX, front month), delayed 10 min");
  assert.equal(body.XAU.displayChange.text, "gold futures (COMEX, front month) −1.43% today");
  assert.equal(body.XAU.displayChange.note.includes("GC=F"), false);
  assert.match(body.XAU.displayChange.note, /COMEX, front month/);
  assert.equal(body.US10Y.source, "Yahoo Finance (CBOE 10-year Treasury yield index)");
  assert.equal(body.XAU.displayChange.symbol, "GC=F");
  assert.equal(body.US10Y.symbol, "^TNX");
  const readers = [];
  readerStrings(body, "", readers);
  assert.deepEqual(readers.filter(function (s) { return RX.test(s); }), []);
  assert.ok(logs.some(function (line) { return line === "[c102r6c] scrub attached"; }));
  const shaped = context.bb8oShape(null, 200, { XAU: { p: 1, label: "Gold spot" }, US10Y: { symbol: "^TNX", source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)" } });
  const again = [];
  readerStrings(shaped, "", again);
  assert.deepEqual(again.filter(function (s) { return RX.test(s); }), []);
});

test("the app anchors become plain names and the cache tag moves to chat103c", () => {
  const work = fs.mkdtempSync("/tmp/c102r6c-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  fs.writeFileSync(server, "// chat102r6b reader-facing scrub.\nfunction bb8oShape(){ return {}; }\n");
  fs.writeFileSync(app, [
    'var label = held.label && /GC=F|futures/i.test(String(held.label)) ? String(held.label) : "GC=F";',
    'var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";',
    'var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";'
  ].join("\n") + "\n");
  fs.writeFileSync(index, '<script src="/app.js?v=chat103b"></script>\n');
  const run = spawnSync("python3", [path.join(dir, "patch_c102r6c.py"), server, app, index, path.join(dir, "server_block_c102r6c.js")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const nextApp = fs.readFileSync(app, "utf8");
  assert.equal(nextApp.includes('"GC=F"'), false);
  assert.equal((nextApp.match(/Gold futures/g) || []).length, 3);
  assert.equal(fs.readFileSync(index, "utf8"), '<script src="/app.js?v=chat103c"></script>\n');
  assert.match(fs.readFileSync(server, "utf8"), /chat102r6c last-write scrub/);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  const again = spawnSync("python3", [path.join(dir, "patch_c102r6c.py"), server, app, index, path.join(dir, "server_block_c102r6c.js")], { encoding: "utf8" });
  assert.notEqual(again.status, 0);
  assert.match(again.stderr + again.stdout, /already chat102r6c/);
});

test("deploy.sh bytes match EXPECTED_SHA256 on their own", () => {
  const spec = fs.readFileSync(path.join(dir, "EXPECTED_SHA256"), "utf8");
  const sha = (spec.match(/sha256 ([a-f0-9]{64})/) || [])[1];
  const bytes = Number((spec.match(/bytes (\d+)/) || [])[1]);
  const buf = fs.readFileSync(path.join(dir, "deploy.sh"));
  assert.equal(buf.length, bytes);
  assert.equal(require("crypto").createHash("sha256").update(buf).digest("hex"), sha);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6c-root-");
  fs.writeFileSync(path.join(root, "server.js"), "// chat102r6b reader-facing scrub.\n");
  fs.writeFileSync(path.join(root, "app.js"), "nope");
  fs.writeFileSync(path.join(root, "index.html"), '<script src="/app.js?v=chat103b"></script>\n');
  const before = fs.readFileSync(path.join(root, "server.js"));
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6c\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6c.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /aba3ab8b407bafb610911d8e2cef5fb5/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before);
  assert.equal(fs.readFileSync(path.join(root, "index.html"), "utf8").includes("chat103c"), false);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6c")), false);
});

test("the known gold-label anchors are unique in the chat102 app generation", () => {
  const src = "/tmp/c102hash/app.js";
  if (!fs.existsSync(src)) return;
  const text = fs.readFileSync(src, "utf8");
  assert.equal(text.split('var label = held.label && /GC=F|futures/i.test(String(held.label)) ? String(held.label) : "GC=F";').length, 2);
  assert.equal(text.split('var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";').length, 3);
});
