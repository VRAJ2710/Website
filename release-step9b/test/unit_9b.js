// Step 9b regression tests. devraw/ = the live page copies with Replit's hosting analytics tag (added by Replit's published hosting
// after the server responds, so absent on dev and in what the server itself sends) removed: the pages then end "</nav></body></html>",
// exactly as the dev pages do. The step-9 block must reproduce the dev failure on them; the step-9b block must inject exactly like
// the preview proxy, log '[chat114viz] injected <path>' once, and cap 'not injected' reasons at 3.
const http = require("http"), fs = require("fs"), path = require("path"), assert = require("assert");
const DEP = path.dirname(__dirname), DEV = path.join(__dirname, "devraw"), LIVE = "/workspace/c114/visuals/raw";
const NEW = fs.readFileSync(path.join(DEP, "server_block_chat114viz.js"), "utf8"), OLD = fs.readFileSync(path.join(DEP, "server_block_chat114viz_step9.js"), "utf8");
const proxySrc = fs.readFileSync("/workspace/c114/visuals/proxy.js", "utf8");
const proxyInject = new Function(proxySrc.slice(proxySrc.indexOf("function inject("), proxySrc.indexOf("function cookieFix")) + "; return inject;")();
let pass = 0, fail = 0; const clog = console.log, logs = [];
const chkA = async (n, f) => { try { await f(); clog("PASS " + n); pass++; } catch (e) { clog("FAIL " + n + " :: " + String(e.message || e).slice(0, 300)); fail++; } };
function attach(src) { const SP = http.Server.prototype, orig = SP.emit; const base = function () { return orig.apply(this, arguments); }; base.__chat113cookie = 1; SP.emit = base;
  console.log = (...a) => logs.push(a.join(" ")); try { new Function("require", src)(require); } finally { console.log = clog; } return () => { SP.emit = orig; }; }
const rd = (d, n) => fs.readFileSync(path.join(d, n + ".html"));
function app(dir) { return new Promise(ok => { const s = http.createServer((q, r) => { const p = q.url.split("?")[0].replace(/\//g, "");
  let b; if (p === "nomain") b = Buffer.from('<html class="a"><head></head><body>x</body></html>'); else b = rd(dir, p);
  r.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "private, max-age=60", "Content-Length": b.length }); r.end(b); }); s.listen(0, "127.0.0.1", () => ok(s)); }); }
function get(port, p) { return new Promise((ok, no) => { http.get({ host: "127.0.0.1", port, path: p }, res => { const b = []; res.on("data", d => b.push(d)); res.on("end", () => ok({ h: res.headers, b: Buffer.concat(b) })); }).on("error", no); }); }
const P = ["brief", "gold", "markets", "research"];
(async () => {
  // 1. reproduce: the step-9 block on dev-shaped pages injects nothing and logs nothing
  let un = attach(OLD); let s = await app(DEV); logs.length = 0; console.log = (...a) => logs.push(a.join(" "));
  const oldRes = {}; for (const p of P) oldRes[p] = await get(s.address().port, "/" + p + "/"); console.log = clog; s.close(); un();
  await chkA("REPRO: step-9 block on dev-shaped pages (end </nav></body></html>): 0 injections, pages byte-identical, no log line (the dev symptom)", async () => {
    for (const p of P) assert(oldRes[p].b.equals(rd(DEV, p)), p); assert.deepStrictEqual(logs, []); });
  // the same step-9 block on the live copies (Replit analytics tag present) DID inject: why the box tests passed
  un = attach(OLD); s = await app(LIVE); const lv = await get(s.address().port, "/brief/"); s.close(); un();
  await chkA("REPRO: step-9 block on live copies (end ...></script></body></html>) injects: the last 24 chars happened to match", async () => { assert(lv.b.toString().includes('id="chat114viz"')); });
  // 2. step 9b on dev-shaped and live pages
  for (const [name, dir] of [["dev-shaped", DEV], ["live", LIVE]]) {
    logs.length = 0; un = attach(NEW); s = await app(dir); console.log = (...a) => logs.push(a.join(" "));
    const r = {}; for (const p of P) r[p] = await get(s.address().port, "/" + p + "/"); const again = await get(s.address().port, "/brief/");
    console.log = clog; s.close(); un();
    await chkA("9b on " + name + " pages: all 4 == preview proxy inject(); Content-Length right; </body></html> tail kept; repeat request same", async () => {
      for (const p of P) { const exp = proxyInject(rd(dir, p).toString("utf8"), p); assert.strictEqual(r[p].b.toString("utf8"), exp, p); assert.strictEqual(+r[p].h["content-length"], r[p].b.length);
        assert(r[p].b.toString().endsWith(name === "live" ? "</script></body></html>" : '<script src="/__chat114viz/viz.js?v=chat114viz" defer></script></body></html>')); }
      assert(again.b.equals(r.brief.b)); });
    await chkA("9b on " + name + " pages: logs exactly ['[chat114viz] attached', '[chat114viz] injected /brief/'] (one-time)", async () => {
      assert.deepStrictEqual(logs, ["[chat114viz] attached", "[chat114viz] injected /brief/"]); });
  }
  // 3. reasons are logged, at most 3 times
  logs.length = 0; un = attach(NEW); s = await app(DEV);
  const M = { "/nomain": 1 }; // not a target page: must not be wrapped at all
  console.log = (...a) => logs.push(a.join(" "));
  const SP = http.Server.prototype; // route /gold/ to a no-main page by swapping the dir file via a tiny handler
  s.close(); s = await new Promise(ok => { const x = http.createServer((q, r) => { const b = Buffer.from('<html class="a"><head></head><body>x</body></html>'); r.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Length": b.length }); r.end(b); }); x.listen(0, "127.0.0.1", () => ok(x)); });
  const outs = []; for (let i = 0; i < 5; i++) outs.push(await get(s.address().port, "/gold/")); console.log = clog; s.close(); un();
  await chkA("9b fail-safe page without <main class=\"wrap\">: served unchanged x5, reason logged 3 times then silent", async () => {
    for (const o of outs) assert.strictEqual(o.b.toString(), '<html class="a"><head></head><body>x</body></html>');
    assert.deepStrictEqual(logs.slice(1), Array(3).fill('[chat114viz] not injected /gold/: no </head>, <main class="wrap"> or </body> in order')); });
  clog("\nunit_9b: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
})();
