"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { spawnSync } = require("child_process");

const dir = __dirname;
const blockH = fs.readFileSync(path.join(dir, "server_block_c102r6h.js"), "utf8");
const blockG = fs.readFileSync(path.join(dir, "server_block_c102r6g.js"), "utf8");
const oldBlock = blockG;

function proseKey(key) {
  const k = String(key || "");
  return /^(note|cacheNote|statusNote|text|label|detail|message|caption|description)$/.test(k) || /(?:Note|Text|Label)$/.test(k);
}
const BAD = /GC=F|DX-Y\.NYB|\^TNX|\^VIX|\^GSPC|\bCL=F\b|\bSI=F\b|\bBTC-USD\b|[A-Z]{3}=X|\bDGS10\b|\bDFII10\b|\bCPIAUCSL\b|\bCPILFESL\b|\bPCEPI\b|\bPAYEMS\b|\b[A-Z]{1,4}=F\b|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

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
    Response: typeof Response === "function" ? Response : function Response() {},
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

function sameNonProse(g, h, trail) {
  const where = trail || "$";
  if (Array.isArray(g)) {
    assert.equal(Array.isArray(h), true, where);
    assert.equal(h.length, g.length, where);
    g.forEach(function (item, i) { sameNonProse(item, h[i], where + "[" + i + "]"); });
    return;
  }
  if (g && typeof g === "object") {
    assert.equal(h && typeof h === "object" && !Array.isArray(h), true, where);
    Object.keys(g).forEach(function (k) {
      if (proseKey(k)) return;
      const next = where + "." + k;
      if (k === "source" && typeof g[k] === "string" && /\bDFII10\b/.test(g[k])) {
        assert.equal(h[k], "FRED, US 10-year real yield (TIPS)", next);
        return;
      }
      if (k === "source" && typeof g[k] === "string" && /\bDGS10\b/.test(g[k])) {
        assert.equal(h[k], "FRED, US 10-year Treasury yield", next);
        return;
      }
      sameNonProse(g[k], h[k], next);
    });
    return;
  }
  assert.equal(h, g, where);
}

function proseHits(value, key, hits) {
  if (typeof value === "string") {
    if (key === "source") {
      if (/\bDGS10\b|\bDFII10\b|\bCPIAUCSL\b|\bCPILFESL\b|\bPCEPI\b|\bPAYEMS\b|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) hits.push("source=" + value);
      return;
    }
    const shown = proseKey(key) || key === "sourceLabel" || key === "asOfUk";
    if (!shown) return;
    if (BAD.test(value)) hits.push((key || "") + "=" + value);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(function (item) { proseHits(item, key, hits); });
    return;
  }
  if (!value || typeof value !== "object") return;
  Object.keys(value).forEach(function (k) { proseHits(value[k], k, hits); });
}

function terminalFixture() {
  return {
    fetchedAt: 1794325077671,
    generatedAtUtc: "2026-11-10T18:04:00.000Z",
    XAU: {
      p: 4050.1,
      source: "gold-api-spot-proxy",
      asOf: "2026-11-10T17:51:40.665Z",
      ts: 1794324700,
      displayChangeLabel: "Gold futures (GC=F, delayed 10 min)",
      displayChange: { symbol: "GC=F", text: "gold futures (GC=F) −1.43% today", asOf: "2026-11-10T17:51:40.665Z" },
      futuresChange: { symbol: "GC=F", text: "gold futures (gold futures) -2.18% today", ts: 1794324700 },
      bars: [{ timeUtc: "2026-11-10T05:00:00.000Z", c: 4050.1 }]
    },
    DXY: { p: 102.1, symbol: "DX-Y.NYB", source: "Yahoo Finance (DX-Y.NYB)", name: "US Dollar Index (ICE, Yahoo the ICE dollar index)", detail: "Yahoo Finance (the ICE dollar index)", asOf: "2026-11-10T17:27:55.000Z" },
    US10Y: { symbol: "^TNX", value: 4.99, source: "Yahoo Finance (^TNX, CBOE 10-year Treasury yield index)", note: "value is in percent (4.99 = 4.99%). Show the % once, in the UI.", asOf: "2026-11-10T17:26:14.000Z" },
    nominalOfficial: { series: "DGS10", value: 4.11, date: "2026-11-07", source: "US Treasury via FRED (DGS10), 10-year constant-maturity yield", sourceUrl: "https://fred.stlouisfed.org/series/DGS10" },
    realOfficial: { series: "DFII10", value: 1.84, date: "2026-11-07", source: "US Treasury via FRED (DFII10), 10-year inflation-protected yield", sourceUrl: "https://fred.stlouisfed.org/series/DFII10" },
    ratio: {
      status: "ok",
      value: 78.125,
      formula: "Gold spot (USD per troy ounce) ÷ silver spot (USD per troy ounce)",
      source: "gold-api.com",
      asOfUtc: "2026-11-10T17:51:40.665Z",
      numerator: { name: "Gold spot", price: 4050.1, asOfUtc: "2026-11-10T17:51:40.665Z" },
      denominator: { name: "Silver spot", price: 51.84, asOfUtc: "2026-11-10T17:51:40.665Z" }
    },
    cacheNote: "Stored reading from 2026-11-10T17:51:40.665Z. Series DGS10 and CPIAUCSL were not refreshed.",
    spot: { price: 4100.25, asOfUtc: "2026-11-10T17:51:40.665Z", source: "gold-api.com", timeUtc: "2026-11-10T05:00:00.000Z" }
  };
}

function deskFixture() {
  return {
    source: "Yahoo Finance (GC=F|DX-Y.NYB|^TNX)",
    quotes: {
      XAU: {
        price: 4050.1,
        symbol: "GC=F",
        source: "Yahoo Finance (GC=F)",
        asOf: "2026-11-10T17:51:40.665Z",
        displayChange: {
          symbol: "GC=F",
          label: "Gold futures (GC=F, delayed 10 min)",
          text: "gold futures (GC=F) −2.15% today",
          asOf: "2026-11-10T17:51:40.665Z"
        }
      },
      DXY: { price: 102.1, symbol: "DX-Y.NYB", source: "Yahoo Finance (DX-Y.NYB)", label: "US Dollar Index (ICE, Yahoo DX-Y.NYB)", asOf: "2026-11-10T17:27:55.000Z" },
      TNX: { value: 4.99, symbol: "^TNX", source: "Yahoo Finance (^TNX)", note: "CPIAUCSL is a different series. 2026-11-10T17:26:14.000Z", asOf: "2026-11-10T17:26:14.000Z" }
    }
  };
}

test("non-prose fields stay equal to r6g and prose drops raw ids", () => {
  const gCtx = load(blockG);
  const hCtx = load(blockH);
  const raw = terminalFixture();
  const g = send(gCtx, JSON.parse(JSON.stringify(raw)));
  const h = send(hCtx, JSON.parse(JSON.stringify(raw)));
  sameNonProse(g, h);
  assert.equal(h.generatedAtUtc, "2026-11-10T18:04:00.000Z");
  assert.equal(h.XAU.asOf, "2026-11-10T17:51:40.665Z");
  assert.equal(h.XAU.displayChange.symbol, "GC=F");
  assert.equal(h.XAU.bars[0].timeUtc, "2026-11-10T05:00:00.000Z");
  assert.equal(h.spot.asOfUtc, "2026-11-10T17:51:40.665Z");
  assert.equal(h.nominalOfficial.series, "DGS10");
  assert.equal(h.realOfficial.series, "DFII10");
  assert.equal(h.nominalOfficial.sourceUrl, g.nominalOfficial.sourceUrl);
  assert.equal(h.nominalOfficial.source, "FRED, US 10-year Treasury yield");
  assert.equal(h.realOfficial.source, "FRED, US 10-year real yield (TIPS)");
  assert.equal(h.ratio.asOfUtc, g.ratio.asOfUtc);
  assert.equal(h.ratio.asOfUk, "Tue 10 Nov, 17:51 UK");
  assert.equal(h.ratio.numerator.asOfUtc, g.ratio.numerator.asOfUtc);
  assert.equal(h.ratio.numerator.asOfUk, undefined);
  assert.equal(h.XAU.displayChange.text, "gold futures (COMEX, front month) −1.43% today");
  assert.equal(h.XAU.displayChangeLabel, "Gold futures (COMEX, front month, delayed 10 min)");
  assert.equal(h.DXY.source, g.DXY.source);
  assert.equal(h.DXY.sourceLabel, "Yahoo Finance, ICE US Dollar Index");
  assert.equal(h.US10Y.source, g.US10Y.source);
  assert.equal(h.US10Y.note, "Yield in percent.");
  assert.match(h.cacheNote, /Tue 10 Nov, 17:51 UK/);
  assert.equal(h.cacheNote.includes("DGS10"), false);
  assert.equal(h.cacheNote.includes("CPIAUCSL"), false);
  const hits = [];
  proseHits(h, "", hits);
  assert.deepEqual(hits, []);
});

test("desk-quotes and the other quote routes get the prose rules without moving source", () => {
  const gCtx = load(blockG);
  const hCtx = load(blockH);
  const raw = deskFixture();
  const g = send(gCtx, JSON.parse(JSON.stringify(raw)));
  const h = send(hCtx, JSON.parse(JSON.stringify(raw)));
  sameNonProse(g, h);
  assert.equal(h.source, "Yahoo Finance (GC=F|DX-Y.NYB|^TNX)");
  assert.equal(h.sourceLabel, "Yahoo Finance");
  assert.equal(h.quotes.XAU.source, "Yahoo Finance (GC=F)");
  assert.equal(h.quotes.XAU.symbol, "GC=F");
  assert.equal(h.quotes.XAU.displayChange.symbol, "GC=F");
  assert.equal(h.quotes.XAU.displayChange.asOf, "2026-11-10T17:51:40.665Z");
  assert.equal(h.quotes.XAU.displayChange.label, "Gold futures (COMEX, front month, delayed 10 min)");
  assert.equal(h.quotes.XAU.displayChange.text, "gold futures (COMEX, front month) −2.15% today");
  assert.equal(h.quotes.DXY.label.includes("DX-Y"), false);
  assert.equal(h.quotes.TNX.note.includes("CPIAUCSL"), false);
  assert.equal(h.quotes.TNX.note.includes("2026-11-10T"), false);
  assert.equal(h.quotes.TNX.asOf, raw.quotes.TNX.asOf);
  const hits = [];
  proseHits(h, "", hits);
  assert.deepEqual(hits, []);

  const yahoo = send(hCtx, {
    price: 4050,
    symbol: "GC=F",
    source: "Yahoo Finance (GC=F)",
    label: "Gold futures (GC=F, delayed 10 min)",
    asOf: "2026-11-10T17:51:40.665Z"
  }, "/api/yahoo-quote?symbol=GC%3DF");
  assert.equal(yahoo.symbol, "GC=F");
  assert.equal(yahoo.source, "Yahoo Finance (GC=F)");
  assert.equal(yahoo.asOf, "2026-11-10T17:51:40.665Z");
  assert.equal(yahoo.label, "Gold futures (COMEX, front month, delayed 10 min)");

  const rates = send(hCtx, {
    series: "DFII10",
    value: 1.84,
    source: "US Treasury via FRED (DFII10), 10-year inflation-protected yield",
    date: "2026-11-07"
  }, "/api/c97/dgs10");
  assert.equal(rates.series, "DFII10");
  assert.equal(rates.date, "2026-11-07");
  assert.equal(rates.source, "FRED, US 10-year real yield (TIPS)");
});

test("the terminal client prints source and does not parse prose as a date", () => {
  const client = fs.readFileSync(path.join(dir, "..", "deploy-chat102", "client_c102.js"), "utf8");
  assert.match(client, /esc\(row\.source \|\| ""\)/);
  assert.equal(client.includes("DGS10"), false);
  assert.equal(client.includes("DFII10"), false);
  assert.equal(/new Date\([^)]*\.note/.test(client), false);
  assert.equal(/new Date\([^)]*\.label/.test(client), false);
  assert.equal(/new Date\([^)]*\.message/.test(client), false);
  assert.equal(/Date\.parse\([^)]*cacheNote/.test(client), false);
  assert.match(client, /uk\(row\.asOfUtc\)/);
  const app = "/tmp/c102hash/app.js";
  assert.equal(fs.existsSync(app), true);
  const src = fs.readFileSync(app, "utf8");
  assert.match(src, /function fe76_quoteKind/);
  assert.match(src, /\[q\.symbol, q\.feedSymbol, q\.name, q\.source, q\.feed\]\.join/);
  assert.equal(src.includes('=== "Yahoo Finance (GC=F|DX-Y.NYB|^TNX)"'), false);
  assert.match(src, /\/\^\(TNX\|IRX\|FVX\|TYX\|US2Y\|US02Y\|US5Y\|US05Y\|US10Y\|US30Y\|DFII5\|DFII10\|/);
  const fn = src.slice(src.indexOf("function fe64_plainNote"), src.indexOf("var fe84_ukHmFmt"));
  assert.equal(/Date\.parse|new Date/.test(fn), false);
});

test("public HTML keeps a dismissible install bar that waits for a second visit or 30s", () => {
  const context = load(blockH);
  const Ctor = context.require("http").ServerResponse;
  const res = new Ctor();
  const css = "#c101-inst{position:fixed;left:12px;right:12px;bottom:12px;z-index:2147482000;max-width:560px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#fff;color:#1b1b1b;border:1px solid #c9c4b8;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:12px 14px;font:14px/1.45 Inter,system-ui,sans-serif}#c101-inst span{flex:1 1 220px}#c101-inst button{min-height:40px;padding:0 14px;border-radius:6px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}";
  const html = "<!doctype html><html><head><style id=\"c101-inst-css\">" + css + "</style></head><body><form class=\"c96su\" action=\"/free-brief\"></form><p id=\"cpi-count\">CPI</p><script id=\"c101-inst-js\">(function(){if(window.__c101i)return;window.__c101i=1;var K=\"c101-install-dismissed\",ev=null;function off(){try{var t=+localStorage.getItem(K)||0;return Date.now()-t<30*864e5}catch(e){return false}}function bar(){if(off()||document.getElementById(\"c101-inst\"))return;var d=document.createElement(\"div\");d.id=\"c101-inst\";d.innerHTML='<span>Add The Dispatch Market to your home screen for one-tap Gold, Brief and Dashboard.</span><button type=\"button\" class=\"y\">Install</button><button type=\"button\" class=\"n\" aria-label=\"Not now\">Not now</button>';document.body.appendChild(d);d.querySelector(\".n\").onclick=function(){try{localStorage.setItem(K,String(Date.now()))}catch(e){}d.remove()}}window.addEventListener(\"beforeinstallprompt\",function(e){e.preventDefault();ev=e;if(!/[?&]source=pwa/.test(location.search))setTimeout(bar,4000)});})();</script></body></html>";
  res.end(html);
  const out = res.written;
  assert.equal(out.includes("position:fixed;left:12px;right:12px;bottom:12px"), false);
  assert.match(out, /max-height:40px/);
  assert.match(out, /padding-bottom:44px/);
  assert.equal(out.includes("setTimeout(bar,4000)"), false);
  assert.match(out, /c101-install-visits/);
  assert.match(out, /setTimeout\(bar,30000\)/);
  assert.match(out, /c101-install-dismissed/);
  assert.match(out, /beforeinstallprompt/);
  assert.match(out, />Install</);
  assert.match(out, /__c102r6hFetch/);
  assert.match(out, /\/api\/c98\/alerts/);
  assert.match(out, /action="\/free-brief"/);
  assert.match(out, /id="cpi-count"/);
});

test("replacing the scrub block leaves the prefix byte-identical and patches the client anchors", () => {
  const work = fs.mkdtempSync("/tmp/c102r6h-patch-");
  const server = path.join(work, "server.js");
  const app = path.join(work, "app.js");
  const index = path.join(work, "index.html");
  const cpi = "/* CPI y/y wording. Do not edit. */\nfunction cpiNote(){ return \"year on year\"; }\n";
  const poll = fs.readFileSync(path.join(dir, "patch_c102r6h.py"), "utf8");
  const startMark = 'OLD_POLL = """';
  const start = poll.indexOf(startMark) + startMark.length;
  const oldPoll = poll.slice(start, poll.indexOf('"""', start));
  fs.writeFileSync(server, cpi + oldBlock);
  fs.writeFileSync(app, "function boot(){ return 1; }\n" + oldPoll + "\n");
  fs.writeFileSync(index, "<script src=\"/app.js?v=chat103c\"></script>\n");
  const run = spawnSync("python3", [
    path.join(dir, "patch_c102r6h.py"),
    server,
    app,
    index,
    path.join(dir, "server_block_c102r6g.js"),
    path.join(dir, "server_block_c102r6h.js")
  ], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr + run.stdout);
  const after = fs.readFileSync(server, "utf8");
  const fresh = blockH.endsWith("\n") ? blockH : blockH + "\n";
  assert.equal(after.slice(0, cpi.length), cpi);
  assert.equal(after.endsWith(fresh), true);
  assert.equal(spawnSync(process.execPath, ["--check", server], { encoding: "utf8" }).status, 0);
  const appAfter = fs.readFileSync(app, "utf8");
  assert.match(appAfter, /_userSignedIn !== true/);
  assert.match(appAfter, /r\.status === 401/);
  assert.equal(appAfter.includes("return r.ok ? r.json()"), false);
  assert.equal(spawnSync(process.execPath, ["--check", app], { encoding: "utf8" }).status, 0);
  assert.equal(fs.readFileSync(index, "utf8"), "<script src=\"/app.js?v=chat103d\"></script>\n");
});

test("deploy.sh bytes match EXPECTED_SHA256 and the guarded md5s", () => {
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
  assert.match(text, /6bdd7cf9ecd185e56ade2332ca8e673b/);
  assert.match(text, /93644cb45fc3884e7068bf9a902d73e3/);
  assert.match(text, /338615e7ece511104855785b67e9c10a/);
  assert.match(text, /bak-chat102r6h/);
});

test("remote payload is fetched and a non-matching root is refused", () => {
  const root = fs.mkdtempSync("/tmp/c102r6h-root-");
  fs.writeFileSync(path.join(root, "server.js"), "/* CPI */\n" + oldBlock);
  fs.writeFileSync(path.join(root, "app.js"), "app");
  fs.writeFileSync(path.join(root, "index.html"), "index");
  const before = {
    server: fs.readFileSync(path.join(root, "server.js")),
    app: fs.readFileSync(path.join(root, "app.js")),
    index: fs.readFileSync(path.join(root, "index.html"))
  };
  const run = spawnSync("bash", [path.join(dir, "deploy.sh"), "--dry-run", "--dir", root], { encoding: "utf8" });
  const spec = fs.readFileSync(path.join(dir, "deploy.sh"), "utf8");
  const payload = (spec.match(/PAYLOAD_COMMIT=([a-f0-9]{40})/) || [])[1];
  const blockHash = (spec.match(/server_block_c102r6h\.js ([a-f0-9]{64})/) || [])[1];
  const out = run.stdout + run.stderr;
  assert.notEqual(run.status, 0);
  assert.match(out, new RegExp("remote payload ok: server_block_c102r6h.js " + blockHash));
  assert.match(out, new RegExp(payload));
  assert.match(out, /replace refused/);
  assert.match(out, /6bdd7cf9ecd185e56ade2332ca8e673b/);
  assert.deepEqual(fs.readFileSync(path.join(root, "server.js")), before.server);
  assert.deepEqual(fs.readFileSync(path.join(root, "app.js")), before.app);
  assert.deepEqual(fs.readFileSync(path.join(root, "index.html")), before.index);
  assert.equal(fs.readdirSync(root).some((n) => n.includes("bak-chat102r6h")), false);
});
