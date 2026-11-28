// ===== chat114viz (release step 9b, 28 Nov 2026): visuals pass for /brief/, /gold/, /markets/ and /research/ =====
// Step 9b replaces the step-9 block. Step 9 attached but never injected: its final safety check compared the last 24 characters of
// the page before and after injection, and those characters include the text just before </body>, where the script tag goes.
// The check now compares everything from the last </body> to the end (the part that must not change). Same hook point as
// chat110navy, same assets, same insertions. Logs '[chat114viz] injected <path>' once, on the first page it changes, and up to
// 3 'not injected' reasons, so a silent skip can no longer happen.
// Adds, to the finished HTML of exactly those four pages, the same three insertions as the approved preview proxy (inject() in
// /workspace/c114/visuals/proxy.js): a stylesheet link before </head>, a mount <section id="chat114viz"> right after the page's first
// section inside <main class="wrap">, and a deferred script before the last </body>; plus "cz-on cz-<page>" classes on <html>.
// The layer (viz.js, viz.css) is served by this block from the two strings below at /__chat114viz/viz.css and /__chat114viz/viz.js.
// viz.js reads only the site's own existing free GET endpoints (market-reference-quotes, desk-quotes, crypto-snapshot, regime, c102/terminal,
// c102/chart, c101f/rates, real-yield, c97/dgs10, eia-spot). It adds no endpoint, secret, config, cookie, schema or write.
// Fail-safe: any problem (no </head>, no main/section, not UTF-8 clean, an exception) serves the page byte-for-byte as it was.
// Only a finished 200 text/html GET without content-encoding is touched; Content-Length is recomputed after injection; the tail of the page
// (</html>) is unchanged. Every other route is passed straight through. Needs chat113cookie attached (it is the previous trailing block).
;(function () {
  var TAG = "chat114viz";
  var VIZ_CSS = /*@@CSS@@*/;
  var VIZ_JS = /*@@JS@@*/;
  var PAGES = { "/brief": "brief", "/brief/": "brief", "/gold": "gold", "/gold/": "gold", "/markets": "markets", "/markets/": "markets", "/research": "research", "/research/": "research" };
  var ASSETS = { "/__chat114viz/viz.css": ["text/css; charset=utf-8", VIZ_CSS], "/__chat114viz/viz.js": ["application/javascript; charset=utf-8", VIZ_JS] };
  var crypto = require("crypto"), logged = 0;
  function note(m) { if (logged++ < 5) { try { console.log("[" + TAG + "] " + m); } catch (e) {} } }
  var injectedOnce = 0, whyN = 0, lastWhy = "";
  function why(r) { lastWhy = r; }
  var CSS_LINK = '<link rel="stylesheet" href="/__chat114viz/viz.css?v=chat114viz">';
  var JS_TAG = '<script src="/__chat114viz/viz.js?v=chat114viz" defer></script>';
  function mount(page) { return '<section id="chat114viz" class="cz-root" data-cz-page="' + page + '" aria-label="Market snapshot and key figures"><p class="cz-loading">Loading the market snapshot from this site\u2019s free feeds\u2026</p></section>'; }
  function inject(html, page) {
    if (html.indexOf('id="chat114viz"') >= 0) { why("already has the layer"); return null; }
    var h = html.lastIndexOf("</head>"), m = html.indexOf('<main class="wrap">'), b = html.lastIndexOf("</body>");
    if (h < 0 || m < 0 || b < 0 || h > m || b < m) { why("no </head>, <main class=\"wrap\"> or </body> in order"); return null; }
    var e = html.indexOf("</section>", m); if (e < 0) { why("no </section> after main"); return null; }
    var hm = /<html\b([^>]*)\bclass="/i.exec(html); if (!hm || hm.index > h) { why("no <html class>"); return null; }
    var out = html.slice(0, h) + CSS_LINK + html.slice(h, e + 10) + mount(page) + html.slice(e + 10, b) + JS_TAG + html.slice(b);
    var k = out.indexOf(hm[0]); // the <html ... class=" opening tag sits before everything inserted above
    return out.slice(0, k) + hm[0] + "cz-on cz-" + page + " " + out.slice(k + hm[0].length);
  }
  function transform(buf, page) {
    lastWhy = "";
    var s = buf.toString("utf8");
    if (!Buffer.from(s, "utf8").equals(buf)) { why("not clean UTF-8"); return null; } // leave untouched
    var out = inject(s, page); if (out == null) return null;
    var tb = s.lastIndexOf("</body>"), to = out.lastIndexOf("</body>");
    if (tb < 0 || to < 0 || out.slice(to) !== s.slice(tb)) { why("tail changed"); return null; } // </body></html> tail unchanged
    return Buffer.from(out, "utf8");
  }
  function wrap(res, page, path) {
    var chunks = [], mode = null, ended = false, w0 = res.write, e0 = res.end, wh0 = res.writeHead;
    function restore() { res.write = w0; res.end = e0; res.writeHead = wh0; }
    function decide() {
      if (mode) return mode;
      var ct = "", ce = null;
      try { ct = String(res.getHeader("content-type") || ""); ce = res.getHeader("content-encoding"); } catch (e) {}
      mode = (res.statusCode === 200 && /text\/html/i.test(ct) && !ce) ? "buf" : "pass";
      if (mode === "pass") restore();
      return mode;
    }
    function push(c, enc) {
      if (c == null) return;
      if (typeof c === "string") chunks.push(Buffer.from(c, typeof enc === "string" ? enc : "utf8"));
      else if (Buffer.isBuffer(c)) chunks.push(c);
      else if (c instanceof Uint8Array) chunks.push(Buffer.from(c));
    }
    res.writeHead = function (code, a, b) {
      var hdrs = (a && typeof a === "object") ? a : (b && typeof b === "object" ? b : null);
      if (typeof code === "number") res.statusCode = code;
      if (typeof a === "string") res.statusMessage = a;
      if (hdrs) {
        if (Array.isArray(hdrs)) { for (var i = 0; i + 1 < hdrs.length; i += 2) res.setHeader(hdrs[i], hdrs[i + 1]); }
        else Object.keys(hdrs).forEach(function (h) { res.setHeader(h, hdrs[h]); });
      }
      if (decide() === "pass") return wh0.call(res, res.statusCode);
      return res;
    };
    res.write = function (c, enc, cb) {
      if (decide() === "pass") return w0.apply(res, arguments);
      push(c, enc); if (typeof enc === "function") enc(); else if (typeof cb === "function") cb(); return true;
    };
    res.end = function (c, enc, cb) {
      if (ended) return res;
      if (decide() === "pass") { ended = true; return e0.apply(res, arguments); }
      ended = true;
      if (typeof c === "function") { cb = c; c = null; } else if (typeof enc === "function") { cb = enc; enc = null; }
      push(c, enc);
      restore();
      var body = Buffer.concat(chunks), out = null;
      try { out = transform(body, page); } catch (eT) { out = null; note("skipped: " + (eT && eT.message || eT)); }
      try {
        if (out != null) { if (!injectedOnce) { injectedOnce = 1; console.log("[" + TAG + "] injected " + path); } }
        else if (whyN < 3) { whyN++; console.log("[" + TAG + "] not injected " + path + ": " + (lastWhy || "unknown")); }
      } catch (eN) {}
      var fin = out != null ? out : body;
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat114viz) return;
    if (!SP.emit || !SP.emit.__chat113cookie) throw new Error("chat113cookie is not attached; step 9 stays off");
    var emit0 = SP.emit, etag = {};
    Object.keys(ASSETS).forEach(function (k) { etag[k] = '"' + crypto.createHash("sha1").update(ASSETS[k][1]).digest("hex").slice(0, 16) + '"'; });
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q);
        var m = String(req.method || "GET").toUpperCase();
        if (ASSETS[path] && (m === "GET" || m === "HEAD")) {
          var buf = Buffer.from(ASSETS[path][1], "utf8");
          res.setHeader("Content-Type", ASSETS[path][0]); res.setHeader("Cache-Control", "public, max-age=300"); res.setHeader("X-Content-Type-Options", "nosniff"); res.setHeader("ETag", etag[path]);
          if (req.headers && req.headers["if-none-match"] === etag[path]) { res.statusCode = 304; res.end(); return true; }
          res.statusCode = 200; res.setHeader("Content-Length", buf.length);
          res.end(m === "HEAD" ? undefined : buf); return true;
        }
        if (m === "GET" && Object.prototype.hasOwnProperty.call(PAGES, path)) wrap(res, PAGES[path], path);
      } catch (eReq) {
        note("skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    Object.keys(emit0).forEach(function (k) { if (/^__/.test(k)) emit[k] = emit0[k]; });
    emit.__chat114viz = 1;
    SP.emit = emit;
    console.log("[" + TAG + "] attached");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
