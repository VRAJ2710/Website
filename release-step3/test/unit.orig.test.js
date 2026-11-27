// Unit and HTTP tests for the chat107credits block. Usage: node unit.test.js
const fs = require("fs"), path = require("path"), vm = require("vm"), http = require("http"), assert = require("assert");
const BLOCK = fs.readFileSync(path.join(__dirname, "..", "server_block_chat107credits.js"), "utf8");
let pass = 0, fail = 0; const results = [];
async function t(name, fn) { try { await fn(); pass++; console.log("ok   - " + name); } catch (e) { fail++; console.log("FAIL - " + name + ": " + (e && e.stack || e)); } }
function load(opts) {
  opts = opts || {};
  const calls = [];
  const ctx = { console: { log: (m) => (opts.logs || []).push(String(m)) }, setTimeout, clearTimeout, setInterval: (f, ms) => ({ unref() {} }), Buffer, Intl, Promise, Date, JSON, Math, Object, String, Array, RegExp, Error, decodeURIComponent,
    require: opts.require || ((m) => m === "http" ? { ServerResponse: { prototype: opts.proto || { write() {}, end() {} } } } : require(m)) };
  ctx.globalThis = ctx;
  ctx.fetch = opts.fetch || (async (u) => { calls.push([Date.now(), String(u)]); return { ok: !/fail/.test(String(u)) }; });
  vm.createContext(ctx);
  const pre = "var c97Transform = function (html, req) { return html; }; const c97Mem = new Map(); const RT53_RY = { at: 0, v: null }; const RT44_EIA = { at: 0, v: null, src: '' };\n";
  const post = "\n;globalThis.__t = { c97Mem, RT53_RY, RT44_EIA, get tr() { return c97Transform; } };";
  vm.runInContext(pre + BLOCK + post, ctx, { filename: "server_block_chat107credits.js" });
  return { ctx, calls, api: ctx.__c107credits, t: ctx.__t };
}
function strip(s) {
  return s.replace(/<p class="c107-fred">[^<]*<\/p>/g, "")
    .replace(/<p class="c107-meth">[\s\S]*?<\/p>/g, "")
    .replace(/<style id="c107-css">[\s\S]*?<\/style><script id="c107-credits">[\s\S]*?<\/script>/g, "");
}
(async () => {
  await t("attach line logged exactly once", async () => {
    const logs = []; load({ logs }); assert.deepStrictEqual(logs.filter((l) => /attached/.test(l)), ["[chat107credits] attached"]);
  });
  await t("idsOfUrl reads FRED ids and ignores other hosts", async () => {
    const { api } = load();
    assert.deepStrictEqual(Array.from(api.idsOfUrl("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10&cosd=2003-01-01")), ["DFII10"]);
    assert.deepStrictEqual(Array.from(api.idsOfUrl("https://api.stlouisfed.org/fred/series/observations?series_id=PAYEMS&file_type=json")), ["PAYEMS"]);
    assert.strictEqual(api.idsOfUrl("https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF"), null);
    assert.strictEqual(api.idsOfUrl("https://example.com/?id=DGS10"), null);
  });
  await t("FRED requests are spaced >= 500 ms (<= 2 per second); other hosts are not delayed", async () => {
    const L = load(); const f = L.ctx.fetch; const t0 = Date.now();
    const ps = ["DGS10", "DFII10", "PAYEMS", "UNRATE", "PCEPI"].map((id) => f("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + id));
    const other = f("https://gold-api.com/price/XAU"); await other;
    assert.ok(L.calls.find((c) => /gold-api/.test(c[1]))[0] - t0 < 100, "non-FRED request delayed");
    await Promise.all(ps);
    const fr = L.calls.filter((c) => /stlouisfed/.test(c[1])).map((c) => c[0]);
    for (let i = 1; i < fr.length; i++) assert.ok(fr[i] - fr[i - 1] >= 495, "gap " + (fr[i] - fr[i - 1]));
    for (let i = 2; i < fr.length; i++) assert.ok(fr[i] - fr[i - 2] >= 990, "3 in 1 s");
  });
  await t("a failed FRED fetch does not block the queue and is not recorded as accessed", async () => {
    const L = load({ fetch: async (u) => { if (/FAILX/.test(u)) throw new Error("net"); return { ok: true }; } });
    await L.ctx.fetch("https://fred.stlouisfed.org/graph/fredgraph.csv?id=FAILX").catch(() => {});
    await L.ctx.fetch("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10");
    assert.ok(L.api.seen.DGS10 > 0); assert.ok(!L.api.seen.FAILX);
  });
  await t("access date is the UK date of the cache timestamp (GMT and BST)", async () => {
    const L = load();
    L.t.c97Mem.set("fred:PAYEMS", { v: [[1]], at: Date.parse("2026-11-15T23:30:00Z") });
    L.t.c97Mem.set("fred:UNRATE", { v: [[1]], at: Date.parse("2026-07-01T23:30:00Z") });
    L.t.RT53_RY.v = { value: 1 }; L.t.RT53_RY.at = Date.parse("2026-11-16T19:35:55Z");
    const html = "<!doctype html><html><body><p>x</p></body></html>";
    const out = L.api.credit(html, "/"); const m = /window\.__c107cfg=(\{[^;]*\});/.exec(out); const cfg = JSON.parse(m[1]);
    assert.strictEqual(cfg.d.PAYEMS, "15 November 2026"); assert.strictEqual(cfg.d.UNRATE, "2 July 2026"); assert.strictEqual(cfg.d.DFII10, "16 November 2026");
    assert.ok(!("DGS10" in cfg.d), "no date invented for a series not fetched");
  });
  await t("retention: cached FRED data older than 30 days is dropped, newer kept, in-flight kept", async () => {
    const L = load(); const now = Date.now(), d = 864e5;
    L.t.c97Mem.set("fred:OLD", { v: [[1]], at: now - 31 * d }); L.t.c97Mem.set("fred:NEW", { v: [[1]], at: now - 29 * d });
    L.t.c97Mem.set("fred:BUSY", { v: [[1]], at: now - 40 * d, p: Promise.resolve() }); L.t.c97Mem.set("ons:x", { v: 1, at: now - 90 * d });
    L.t.c97Mem.set("c101:model", { v: {}, at: now - 31 * d });
    L.t.RT53_RY.v = { a: 1 }; L.t.RT53_RY.at = now - 31 * d; L.t.RT44_EIA.v = { a: 1 }; L.t.RT44_EIA.src = "fred"; L.t.RT44_EIA.at = now - 31 * d;
    L.api.sweep();
    assert.ok(!L.t.c97Mem.has("fred:OLD")); assert.ok(L.t.c97Mem.has("fred:NEW")); assert.ok(L.t.c97Mem.has("fred:BUSY")); assert.ok(L.t.c97Mem.has("ons:x")); assert.ok(!L.t.c97Mem.has("c101:model"));
    assert.strictEqual(L.t.RT53_RY.v, null); assert.strictEqual(L.t.RT44_EIA.v, null);
  });
  const files = fs.readdirSync(path.join(__dirname, "pages")).concat(fs.readdirSync(path.join(__dirname, "pages", "sm")).map((f) => "sm/" + f)).filter((f) => /\.html$/.test(f));
  await t("every saved dev page (" + files.length + "): output minus the credit lines is byte-identical; idempotent", async () => {
    const L = load(); let footers = 0;
    for (const f of files) {
      const html = fs.readFileSync(path.join(__dirname, "pages", f), "utf8");
      const url = "/" + path.basename(f, ".html").replace(/^p_|^_/, "").replace(/_/g, "/");
      const out = L.api.credit(html, url);
      assert.strictEqual(strip(out), html, f + " differs beyond the credits");
      assert.strictEqual(L.api.credit(out, url), out, f + " not idempotent");
      if (html.indexOf('<footer class="site"') >= 0) { footers++; const i = out.indexOf('<footer class="site"'), j = out.indexOf("</footer>", i), k = out.indexOf('class="c107-fred"', i); assert.ok(k > i && k < j, f + " footer note not inside the footer"); }
      if (html.indexOf("</body>") >= 0) assert.strictEqual(out.split('id="c107-credits"').length - 1, 1, f + " script count");
    }
    assert.ok(footers > 20);
  });
  await t("methodology: one credits paragraph right after the Sources table, before 'Times and trading sessions'", async () => {
    const L = load(); const html = fs.readFileSync(path.join(__dirname, "pages", "p_methodology.html"), "utf8");
    const out = L.api.credit(html, "/methodology");
    assert.strictEqual(out.split('class="c107-meth"').length - 1, 1);
    const k = out.indexOf('class="c107-meth"'), h = out.indexOf("<h2>Times and trading sessions</h2>"), tb = out.lastIndexOf("</table>", k);
    assert.ok(tb > 0 && k > tb && k < h);
    assert.ok(!/@/.test(out.slice(k - 20, out.indexOf("</p>", k))), "no email address in the credit");
    assert.strictEqual(L.api.credit(html, "/about").indexOf('class="c107-meth"'), -1);
  });
  await t("auth pages get the footer note only, no script", async () => {
    const L = load(); const html = '<!doctype html><html><body><main>x</main><footer class="site"><div class="wrap"><p>a</p></div></footer></body></html>';
    const out = L.api.credit(html, "/__auth/login?x=1"); assert.ok(out.indexOf("c107-fred") > 0); assert.strictEqual(out.indexOf("<script"), -1);
  });
  await t("FRED note text is exact and mentions no email", async () => {
    const L = load(); const out = L.api.credit('<footer class="site"><div class="wrap"></div></footer>', "/");
    assert.ok(out.indexOf("This product uses FRED\u00ae data but is not endorsed or certified by the Federal Reserve Bank of St. Louis.") > 0);
    assert.ok(!/stlouisfed\.org\b[^"]*@|@stls|mailto/i.test(BLOCK), "no FRED email in the block");
  });
  await t("JSON and non-HTML bodies are untouched", async () => {
    const L = load(); const j = JSON.stringify({ source: "US Treasury via FRED", html: "</table>" });
    assert.strictEqual(L.api.credit(j, "/api/c97/dgs10"), j);
  });
  // Real HTTP: wraps the real http.ServerResponse in this process.
  const logs = []; const R = load({ require, logs });
  const page = fs.readFileSync(path.join(__dirname, "pages", "p_.html"), "utf8");
  const srv = http.createServer((req, res) => {
    if (req.url === "/len") { res.setHeader("Content-Type", "text/html; charset=utf-8"); res.setHeader("Content-Length", Buffer.byteLength(page)); return res.end(page); }
    if (req.url === "/chunks") { res.setHeader("Content-Type", "text/html; charset=utf-8"); const a = page.slice(0, 1000); res.write(a); return res.end(page.slice(1000)); }
    if (req.url === "/tr") { res.setHeader("Content-Type", "text/html; charset=utf-8"); const h = R.t.tr(page, req); res.setHeader("Content-Length", Buffer.byteLength(h)); return res.end(h); }
    if (req.url === "/json") { res.setHeader("Content-Type", "application/json"); const j = JSON.stringify({ a: "</body>" }); res.setHeader("Content-Length", Buffer.byteLength(j)); return res.end(j); }
    if (req.url === "/buf") { res.setHeader("Content-Type", "text/html"); return res.end(Buffer.from(page)); }
  });
  await new Promise((r) => srv.listen(0, r)); const port = srv.address().port;
  function get(p) { return new Promise((r, j) => http.get({ port, path: p }, (res) => { const b = []; res.on("data", (c) => b.push(c)); res.on("end", () => r({ h: res.headers, body: Buffer.concat(b).toString("utf8") })); }).on("error", j)); }
  for (const p of ["/len", "/chunks", "/tr", "/buf"]) {
    await t("HTTP " + p + ": full body, credits once, Content-Length consistent, rest identical", async () => {
      const r = await get(p);
      assert.strictEqual(strip(r.body), page);
      assert.strictEqual(r.body.split('class="c107-fred"').length - 1, 1); assert.strictEqual(r.body.split('id="c107-credits"').length - 1, 1);
      if (r.h["content-length"]) assert.strictEqual(Number(r.h["content-length"]), Buffer.byteLength(r.body));
      assert.ok(r.body.trim().endsWith("</html>"));
    });
  }
  await t("HTTP JSON untouched", async () => { const r = await get("/json"); assert.strictEqual(r.body, JSON.stringify({ a: "</body>" })); });
  srv.close();
  console.log(pass + " passed, " + fail + " failed"); process.exit(fail ? 1 : 0);
})();
