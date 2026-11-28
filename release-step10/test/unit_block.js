// Unit tests for server_block_chat115vizapp.js on a bare http server. Fixtures: the real-lineage step-9b app shell (signed-in /brief/)
// and a step-9b public page. Run: node test/unit_block.js
const http = require("http"), fs = require("fs"), path = require("path"), zlib = require("zlib"), assert = require("assert");
const DEP = path.dirname(__dirname), FX = path.join(__dirname, "fixtures");
const code = fs.readFileSync(path.join(DEP, "server_block_chat115vizapp.js"), "utf8"), mjs = fs.readFileSync(path.join(DEP, "vizapp.js"));
const SHELL = fs.readFileSync(path.join(FX, "shell.html")), PUB = fs.readFileSync(path.join(FX, "public_gold.html"));
const CSS = '<link rel="stylesheet" href="/__chat114viz/viz.css?v=chat114viz">', JS = '<script src="/__chat115vizapp/vizapp.js?v=chat115vizapp" defer></script>';
const expShell = (() => { const s = SHELL.toString(); const h = s.lastIndexOf("</head>"), b = s.lastIndexOf("</body>"); return s.slice(0, h) + CSS + s.slice(h, b) + JS + s.slice(b); })();
let pass = 0, fail = 0; const clog = console.log, logs = [];
const chkA = async (n, f) => { try { await f(); clog("PASS " + n); pass++; } catch (e) { clog("FAIL " + n + " :: " + String(e.message || e).slice(0, 300)); fail++; } };
function attach(flag) { const SP = http.Server.prototype, orig = SP.emit; const base = function () { return orig.apply(this, arguments); }; if (flag) base.__chat114viz = 1; SP.emit = base;
  logs.length = 0; console.log = (...a) => logs.push(a.join(" ")); try { new Function("require", code)(require); } finally { console.log = clog; } return () => { SP.emit = orig; }; }
// inner handler mimics rt20s: compresses inside the handler when the client accepts it, setting Content-Encoding late
function handler(q, r) {
  const p = q.url.split("?")[0], ae = String(q.headers["accept-encoding"] || "");
  let body = p === "/pub/" ? PUB : p === "/api/x" ? Buffer.from("{}") : p === "/bin/" ? Buffer.concat([SHELL.slice(0, 900), Buffer.from([0xff]), SHELL.slice(900)]) : SHELL;
  const ct = p === "/api/x" ? "application/json" : "text/html; charset=utf-8";
  if (p === "/404/") { r.writeHead(404, { "Content-Type": ct }); return r.end(body); }
  if (/br/.test(ae) && p !== "/api/x") { r.setHeader("Content-Type", ct); r.setHeader("Content-Encoding", "br"); r.writeHead(200); const z = zlib.brotliCompressSync(body); r.write(z.slice(0, 500)); return r.end(z.slice(500)); }
  if (/gzip/.test(ae) && p !== "/api/x") { r.writeHead(200, { "Content-Type": ct, "Content-Encoding": "gzip" }); return r.end(zlib.gzipSync(body)); }
  r.writeHead(200, { "Content-Type": ct, "Content-Length": body.length, "Cache-Control": "private, no-store" }); r.end(body);
}
function get(port, p, h, m) { return new Promise((ok, no) => { const rq = http.request({ host: "127.0.0.1", port, path: p, method: m || "GET", headers: h || {} }, res => { const b = []; res.on("data", d => b.push(d)); res.on("end", () => ok({ s: res.statusCode, h: res.headers, b: Buffer.concat(b) })); }); rq.on("error", no); rq.end(); }); }
const dec = r => r.h["content-encoding"] === "br" ? zlib.brotliDecompressSync(r.b) : r.h["content-encoding"] === "gzip" ? zlib.gunzipSync(r.b) : r.b;
(async () => {
  let un = attach(false);
  await chkA("without chat114viz: logs 'not attached', emit unchanged", async () => { assert(logs.some(l => /\[chat115vizapp\] not attached: chat114viz is not attached/.test(l))); assert(!http.Server.prototype.emit.__chat115vizapp); }); un();
  un = attach(true);
  await chkA("startup log exactly ['[chat115vizapp] attached']; keeps __chat114viz", async () => { assert.deepStrictEqual(logs, ["[chat115vizapp] attached"]); assert(http.Server.prototype.emit.__chat114viz && http.Server.prototype.emit.__chat115vizapp); });
  const srv = http.createServer(handler); await new Promise(ok => srv.listen(0, "127.0.0.1", ok)); const port = srv.address().port; const C = { cookie: "a=1; dispatch_session=abc" };
  logs.length = 0; console.log = (...a) => logs.push(a.join(" "));
  const id = await get(port, "/brief/", C), br = await get(port, "/gold/", Object.assign({ "accept-encoding": "gzip, deflate, br" }, C)), gz = await get(port, "/markets/", Object.assign({ "accept-encoding": "gzip" }, C)), again = await get(port, "/research/", C);
  console.log = clog;
  await chkA("signed-in app shell (identity): exactly the 2 tags added; Content-Length right; headers kept", async () => { assert.strictEqual(id.b.toString(), expShell); assert.strictEqual(+id.h["content-length"], id.b.length); assert.strictEqual(id.h["cache-control"], "private, no-store"); });
  await chkA("signed-in app shell (brotli, Content-Encoding set late, streamed in 2 writes): decompresses, injects, recompresses br; Content-Length right", async () => { assert.strictEqual(br.h["content-encoding"], "br"); assert.strictEqual(dec(br).toString(), expShell); assert.strictEqual(+br.h["content-length"], br.b.length); });
  await chkA("signed-in app shell (gzip): same result, gzip kept", async () => { assert.strictEqual(gz.h["content-encoding"], "gzip"); assert.strictEqual(dec(gz).toString(), expShell); });
  await chkA("logs: one '[chat115vizapp] injected /brief/' only", async () => { assert.deepStrictEqual(logs, ["[chat115vizapp] injected /brief/"]); assert(again.b.toString() === expShell); });
  for (const [n, p, h] of [["guest (no cookie) app shell", "/brief/", {}], ["guest (no cookie) brotli", "/gold/", { "accept-encoding": "br" }], ["signed-in public page (main.wrap)", "/pub/", C], ["signed-in JSON", "/api/x", C], ["signed-in 404", "/404/", C], ["signed-in not-UTF-8", "/bin/", C], ["signed-in /api path skipped", "/api/x", Object.assign({ "accept-encoding": "br" }, C)], ["signed-in asset-like path", "/x.js", C]]) {
    await chkA("passed through byte-identical: " + n, async () => {
      const SP = http.Server.prototype, cur = SP.emit; const r = await get(port, p, h);
      SP.emit = Object.getPrototypeOf(SP).emit; const o = await get(port, p, h); SP.emit = cur;
      assert(r.b.equals(o.b), "body differs"); assert.strictEqual(r.s, o.s); assert.strictEqual(r.h["content-encoding"], o.h["content-encoding"]); });
  }
  await chkA("HEAD on the app shell untouched", async () => { const r = await get(port, "/brief/", C, "HEAD"); assert.strictEqual(r.b.length, 0); assert.strictEqual(+r.h["content-length"], SHELL.length); });
  await chkA("asset /__chat115vizapp/vizapp.js: byte-identical to vizapp.js, JS type, cache headers, nosniff, ETag + 304, HEAD", async () => {
    const r = await get(port, "/__chat115vizapp/vizapp.js?v=chat115vizapp"); assert.strictEqual(r.s, 200); assert(r.b.equals(mjs)); assert(/javascript/.test(r.h["content-type"])); assert.strictEqual(r.h["cache-control"], "public, max-age=300"); assert.strictEqual(r.h["x-content-type-options"], "nosniff");
    const r2 = await get(port, "/__chat115vizapp/vizapp.js", { "if-none-match": r.h.etag }); assert.strictEqual(r2.s, 304); assert.strictEqual(r2.b.length, 0);
    const r3 = await get(port, "/__chat115vizapp/vizapp.js", {}, "HEAD"); assert.strictEqual(r3.b.length, 0); assert.strictEqual(+r3.h["content-length"], mjs.length); });
  await chkA("already-injected shell is not injected twice", async () => { const SP = http.Server.prototype; const s2 = http.createServer((q, r) => { const b = Buffer.from(expShell); r.writeHead(200, { "Content-Type": "text/html", "Content-Length": b.length }); r.end(b); }); await new Promise(ok => s2.listen(0, "127.0.0.1", ok)); const r = await get(s2.address().port, "/gold/", C); s2.close(); assert.strictEqual(r.b.toString(), expShell); });
  srv.close(); un();
  clog("\nunit_block: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
})();
