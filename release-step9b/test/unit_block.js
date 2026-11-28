// Unit tests for server_block_chat114viz.js on a bare http server (no network). Run: node test/unit_block.js [PAGES_DIR]
// PAGES_DIR holds brief.html gold.html markets.html research.html (real live HTML copies).
const http = require("http"), fs = require("fs"), path = require("path"), assert = require("assert");
const DEP = path.dirname(__dirname), PAGES = process.argv[2] || "/workspace/c114/visuals/raw";
const code = fs.readFileSync(path.join(DEP, "server_block_chat114viz.js"), "utf8");
const proxySrc = fs.readFileSync("/workspace/c114/visuals/proxy.js", "utf8");
const inj = proxySrc.slice(proxySrc.indexOf("function inject("), proxySrc.indexOf("function cookieFix"));
const proxyInject = new Function(inj + "; return inject;")();
let pass = 0, fail = 0; const chk = (n, f) => { try { f(); console.log("PASS " + n); pass++; } catch (e) { console.log("FAIL " + n + " :: " + (e.message || e).toString().slice(0, 300)); fail++; } };
const chkA = async (n, f) => { try { await f(); console.log("PASS " + n); pass++; } catch (e) { console.log("FAIL " + n + " :: " + (e.message || e).toString().slice(0, 300)); fail++; } };
const logs = []; const clog = console.log; 
function attach(src, withFlag) {
  const SP = http.Server.prototype, orig = SP.emit; logs.length = 0;
  const base = function () { return orig.apply(this, arguments); }; if (withFlag) base.__chat113cookie = 1; SP.emit = base;
  console.log = (...a) => { logs.push(a.join(" ")); clog(...a); };
  try { new Function("require", src)(require); } finally { console.log = clog; }
  return () => { SP.emit = orig; };
}
const page = n => fs.readFileSync(path.join(PAGES, n + ".html"));
function startApp(handlers) {
  return new Promise(ok => { const s = http.createServer((req, res) => { const p = req.url.split("?")[0]; (handlers[p] || handlers["*"])(req, res); }); s.listen(0, "127.0.0.1", () => ok(s)); });
}
function get(port, p, opt) {
  return new Promise((ok, no) => { const r = http.request({ host: "127.0.0.1", port, path: p, method: (opt && opt.method) || "GET", headers: (opt && opt.headers) || {} }, res => { const b = []; res.on("data", d => b.push(d)); res.on("end", () => ok({ s: res.statusCode, h: res.headers, b: Buffer.concat(b) })); }); r.on("error", no); r.end(opt && opt.body); });
}
const html = (res, b, extra) => { res.writeHead(200, Object.assign({ "Content-Type": "text/html; charset=utf-8", "Cache-Control": "private, max-age=60", "Content-Length": b.length }, extra || {})); res.end(b); };
(async () => {
  // 0. not attached without chat113cookie
  let un = attach(code, false); chk("without chat113cookie: logs 'not attached' and no emit change", () => { assert(logs.some(l => /\[chat114viz\] not attached: chat113cookie is not attached/.test(l))); assert(!http.Server.prototype.emit.__chat114viz); }); un();
  const unAll = attach(code, true);
  chk("startup log: exactly one '[chat114viz] attached'", () => assert.deepStrictEqual(logs.filter(l => /chat114viz/.test(l)), ["[chat114viz] attached"]));
  chk("emit marks __chat114viz and keeps __chat113cookie", () => { const e = http.Server.prototype.emit; assert(e.__chat114viz && e.__chat113cookie); });
  const H = {};
  for (const n of ["brief", "gold", "markets", "research"]) H["/" + n + "/"] = (q, r) => html(r, page(n));
  H["/brief"] = (q, r) => { r.writeHead(301, { Location: "/brief/", "Content-Type": "text/html" }); r.end(); };
  H["/gold/dashboard/"] = (q, r) => html(r, page("gold")); H["/terminal/"] = (q, r) => html(r, page("brief")); H["/"] = (q, r) => html(r, page("markets"));
  H["/research/sec/"] = (q, r) => html(r, page("research"));
  H["/enc/"] = H["/x"] = null;
  H["/chunked/"] = null; H["*"] = (q, r) => { r.statusCode = 404; r.end("nf"); };
  const app = await startApp(H), port = app.address().port;
  // pages
  for (const n of ["brief", "gold", "markets", "research"]) {
    await chkA("/" + n + "/ injected exactly as the preview proxy's inject(); Content-Length right; ends </html>; headers kept", async () => {
      const orig = page(n), r = await get(port, "/" + n + "/");
      assert.strictEqual(r.s, 200); assert.strictEqual(r.b.toString("utf8"), proxyInject(orig.toString("utf8"), n));
      assert.strictEqual(+r.h["content-length"], r.b.length); assert(r.b.toString().trimEnd().endsWith("</html>"));
      assert.strictEqual(r.h["cache-control"], "private, max-age=60"); assert(/text\/html/.test(r.h["content-type"]));
      const s = r.b.toString(); assert.strictEqual(s.split('id="chat114viz"').length, 2); assert.strictEqual(s.split("/__chat114viz/viz.css?v=chat114viz").length, 2); assert.strictEqual(s.split("/__chat114viz/viz.js?v=chat114viz").length, 2);
      assert(new RegExp('<html[^>]*class="cz-on cz-' + n + ' ').test(s));
    });
  }
  await chkA("query string still injected (/brief/?utm=x)", async () => { const r = await get(port, "/brief/?utm=x"); assert(r.b.toString().includes('id="chat114viz"')); });
  await chkA("/brief (no slash, 301) passes through untouched", async () => { const r = await get(port, "/brief"); assert.strictEqual(r.s, 301); assert.strictEqual(r.h.location, "/brief/"); assert.strictEqual(r.b.length, 0); });
  await chkA("HEAD /brief/ and POST /brief/ are not wrapped", async () => { const h = await get(port, "/brief/", { method: "HEAD" }); assert.strictEqual(h.b.length, 0); assert.strictEqual(+h.h["content-length"], page("brief").length); const p = await get(port, "/brief/", { method: "POST", body: "a=1" }); assert(!p.b.toString().includes("chat114viz")); });
  for (const p of ["/", "/gold/dashboard/", "/terminal/", "/research/sec/", "/nope"]) await chkA("other route byte-identical: " + p, async () => { const r = await get(port, p), exp = ({ "/": page("markets"), "/gold/dashboard/": page("gold"), "/terminal/": page("brief"), "/research/sec/": page("research") })[p] || Buffer.from("nf"); assert(r.b.equals(exp)); });
  // assets
  const css = fs.readFileSync(path.join(DEP, "viz.css")), js = fs.readFileSync(path.join(DEP, "viz.js"));
  for (const [p, f, ct] of [["/__chat114viz/viz.css?v=chat114viz", css, /^text\/css/], ["/__chat114viz/viz.js?v=chat114viz", js, /^application\/javascript/]]) {
    await chkA("asset " + p + " served byte-identical to the payload file with cache headers", async () => {
      const r = await get(port, p); assert.strictEqual(r.s, 200); assert(r.b.equals(f)); assert(ct.test(r.h["content-type"])); assert.strictEqual(+r.h["content-length"], f.length);
      assert.strictEqual(r.h["cache-control"], "public, max-age=300"); assert.strictEqual(r.h["x-content-type-options"], "nosniff"); assert(r.h.etag);
      const r2 = await get(port, p, { headers: { "If-None-Match": r.h.etag } }); assert.strictEqual(r2.s, 304); assert.strictEqual(r2.b.length, 0);
      const hd = await get(port, p, { method: "HEAD" }); assert.strictEqual(hd.s, 200); assert.strictEqual(hd.b.length, 0); assert.strictEqual(+hd.h["content-length"], f.length);
    });
  }
  // synthetic pipeline cases
  app.close();
  const H2 = {};
  const src = page("gold");
  H2["/gold/"] = (q, r) => { if (q.headers["x-case"] === "br") { r.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Encoding": "br", "Content-Length": src.length }); return r.end(src); }
    if (q.headers["x-case"] === "chunks") { r.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); const t = Math.floor(src.length / 3); r.write(src.slice(0, t)); r.write(src.slice(t, 2 * t)); r.end(src.slice(2 * t)); return; }
    if (q.headers["x-case"] === "string") { r.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); return r.end(src.toString("utf8")); }
    if (q.headers["x-case"] === "nohead") { return html(r, Buffer.from("<html class=\"a\"><body><main class=\"wrap\"><section>x</section></main></body></html>")); }
    if (q.headers["x-case"] === "nomain") { return html(r, Buffer.from("<html class=\"a\"><head></head><body>x</body></html>")); }
    if (q.headers["x-case"] === "bad8") { return html(r, Buffer.concat([src.slice(0, 5000), Buffer.from([0xff, 0xfe]), src.slice(5000)])); }
    if (q.headers["x-case"] === "already") { return html(r, Buffer.from(proxyInject(src.toString(), "gold"))); }
    if (q.headers["x-case"] === "404") { r.writeHead(404, { "Content-Type": "text/html; charset=utf-8" }); return r.end(src); }
    if (q.headers["x-case"] === "json") { r.writeHead(200, { "Content-Type": "application/json" }); return r.end("{}"); }
    if (q.headers["x-case"] === "empty") { return html(r, Buffer.alloc(0)); }
    html(r, src); };
  const app2 = await startApp(Object.assign({ "*": (q, r) => { r.end("x"); } }, H2)), p2 = app2.address().port, G = c => get(p2, "/gold/", { headers: { "x-case": c } });
  await chkA("content-encoding: br page passes through byte-identical (no injection, no corruption)", async () => { const r = await G("br"); assert(r.b.equals(src)); assert.strictEqual(r.h["content-encoding"], "br"); });
  await chkA("chunked res.write/end (string+buffer chunks) is buffered, injected, Content-Length correct", async () => { const r = await G("chunks"); assert.strictEqual(r.b.toString(), proxyInject(src.toString(), "gold")); assert.strictEqual(+r.h["content-length"], r.b.length); assert(!r.h["transfer-encoding"]); });
  await chkA("res.end(string) body is injected identically, Content-Length correct", async () => { const r = await G("string"); assert.strictEqual(r.b.toString(), proxyInject(src.toString(), "gold")); assert.strictEqual(+r.h["content-length"], r.b.length); });
  for (const c of ["nohead", "nomain", "bad8", "already", "404", "json", "empty"]) await chkA("fail-safe: case " + c + " served unchanged, Content-Length correct", async () => {
    const r = await G(c); const exp = { nohead: Buffer.from("<html class=\"a\"><body><main class=\"wrap\"><section>x</section></main></body></html>"), nomain: Buffer.from("<html class=\"a\"><head></head><body>x</body></html>"), bad8: Buffer.concat([src.slice(0, 5000), Buffer.from([0xff, 0xfe]), src.slice(5000)]), already: Buffer.from(proxyInject(src.toString(), "gold")), 404: src, json: Buffer.from("{}"), empty: Buffer.alloc(0) }[c];
    assert(r.b.equals(exp)); if (c !== "404" && c !== "json") assert.strictEqual(+r.h["content-length"], exp.length); });
  app2.close(); unAll();
  // exception inside inject => page unchanged + 'skipped' log
  const bad = code.replace("function inject(html, page) {", "function inject(html, page) { throw new Error('boom');");
  const un3 = attach(bad, true); const app3 = await startApp({ "/gold/": (q, r) => html(r, src), "*": (q, r) => r.end("x") });
  await chkA("injection throws => page served unchanged, one 'skipped: boom' log, Content-Length correct", async () => { logs.length = 0; console.log = (...a) => logs.push(a.join(" ")); const r = await get(app3.address().port, "/gold/"); console.log = clog; assert(r.b.equals(src)); assert.strictEqual(+r.h["content-length"], src.length); assert(logs.some(l => l === "[chat114viz] skipped: boom")); });
  app3.close(); un3();
  clog("\nunit_block: " + pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
})();
