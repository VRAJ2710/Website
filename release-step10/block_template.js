// ===== chat115vizapp (release step 10, 28 Nov 2026): the approved chat114viz layer for SIGNED-IN readers in the member app =====
// Signed-in readers get the member app shell (<main class="main" id="main">, /app.js) on /brief/, /gold/, /markets/ and /research/,
// not the public article, so chat114viz (which needs <main class="wrap">) never applies to them. This block adds, to the app shell
// HTML of a request that carries a dispatch_session cookie, two tags: the existing chat114viz stylesheet before </head> and one
// deferred mount script before the last </body>. The mount script (served here at /__chat115vizapp/vizapp.js) puts the same
// <section id="chat114viz"> at the top of the visible page body on those four app routes and runs the same /__chat114viz/viz.js,
// so the markup and data are the approved ones. It removes the section on other routes and never edits app.js or any app node.
// Requests without a dispatch_session cookie are passed straight through (guest pages stay byte-identical to step 9b).
// The app shell leaves the server already compressed (rt20s brotli/gzip inside the handler), which is why an emit-level hook that
// skips encoded responses (chat110navy, chat114viz) can never see it. This block decompresses that one HTML body, adds the two tags
// and compresses it again with the same encoding and the same settings as rt20s (brotli quality 5, gzip level 6). A body that is
// not the app shell, or that fails to decompress, is sent with its original bytes.
// Fail-safe: anything unexpected serves the page byte-for-byte as it was. No endpoint, secret, config, cookie, schema or write.
// Needs chat114viz attached (it is the previous trailing block).
;(function () {
  var TAG = "chat115vizapp";
  var VIZAPP_JS = /*@@JS@@*/;
  var ASSET = "/__chat115vizapp/vizapp.js";
  var CSS_LINK = '<link rel="stylesheet" href="/__chat114viz/viz.css?v=chat114viz">';
  var JS_TAG = '<script src="/__chat115vizapp/vizapp.js?v=chat115vizapp" defer></script>';
  var SKIP = /^\/(?:api|__auth|__v3p|__navy|__chat114viz|__chat115vizapp|admin|signin|signup|login|logout|register|account|checkout|billing|webhook|webhooks|stripe|auth|reset|verify)(?:[\/?#.]|$)/i;
  var crypto = require("crypto"), zlib = require("zlib"), injectedOnce = 0, whyN = 0, lastWhy = "";
  function why(r) { lastWhy = r; }
  function inject(html) {
    if (html.indexOf("chat115vizapp") >= 0) { why("already has the mount script"); return null; }
    if (!/<main\b[^>]*\bid="main"/i.test(html) || html.indexOf("/app.js?v=") < 0) { why("not the app shell"); return null; }
    if (html.indexOf('id="chat114viz"') >= 0 || html.indexOf('<main class="wrap">') >= 0) { why("public page"); return null; }
    var h = html.lastIndexOf("</head>"), b = html.lastIndexOf("</body>"), m = html.search(/<main\b[^>]*\bid="main"/i);
    if (h < 0 || b < 0 || h > m || b < m) { why("no </head> or </body> in order"); return null; }
    return html.slice(0, h) + CSS_LINK + html.slice(h, b) + JS_TAG + html.slice(b);
  }
  function transform(buf) {
    lastWhy = "";
    var s = buf.toString("utf8");
    if (!Buffer.from(s, "utf8").equals(buf)) { why("not clean UTF-8"); return null; }
    var out = inject(s); if (out == null) return null;
    var tb = s.lastIndexOf("</body>"), to = out.lastIndexOf("</body>");
    if (tb < 0 || to < 0 || out.slice(to) !== s.slice(tb)) { why("tail changed"); return null; }
    return Buffer.from(out, "utf8");
  }
  function wrap(res, path) {
    var chunks = [], mode = null, enc = null, ended = false, w0 = res.write, e0 = res.end, wh0 = res.writeHead;
    function restore() { res.write = w0; res.end = e0; res.writeHead = wh0; }
    function decide() {
      if (mode) return mode;
      var ct = "", ce = null;
      try { ct = String(res.getHeader("content-type") || ""); ce = res.getHeader("content-encoding"); } catch (e) {}
      enc = ce ? String(ce).trim().toLowerCase() : null;
      mode = (res.statusCode === 200 && /text\/html/i.test(ct) && (!enc || enc === "br" || enc === "gzip")) ? "buf" : "pass";
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
      try {
        // the encoding is read again here: an inner layer (rt20s) may set it after this wrapper's first decision
        var ce2 = null; try { ce2 = res.getHeader("content-encoding"); } catch (eH) {}
        enc = ce2 ? String(ce2).trim().toLowerCase() : null;
        if (enc && enc !== "br" && enc !== "gzip") { out = null; lastWhy = "encoding " + enc; }
        else if (!enc) out = transform(body);
        else {
          var plain = enc === "br" ? zlib.brotliDecompressSync(body) : zlib.gunzipSync(body);
          var t2 = transform(plain);
          if (t2 != null) out = enc === "br" ? zlib.brotliCompressSync(t2, { params: { [zlib.constants.BROTLI_PARAM_QUALITY]: 5 } }) : zlib.gzipSync(t2, { level: 6 });
        }
      } catch (eT) { out = null; lastWhy = "error: " + (eT && eT.message || eT); }
      try {
        if (out != null) { if (!injectedOnce) { injectedOnce = 1; console.log("[" + TAG + "] injected " + path); } }
        else if (whyN < 3 && lastWhy && lastWhy !== "not the app shell" && lastWhy !== "public page") { whyN++; console.log("[" + TAG + "] not injected " + path + ": " + lastWhy); }
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
    if (SP.emit && SP.emit.__chat115vizapp) return;
    if (!SP.emit || !SP.emit.__chat114viz) throw new Error("chat114viz is not attached; step 10 stays off");
    var emit0 = SP.emit, abuf = Buffer.from(VIZAPP_JS, "utf8");
    var etag = '"' + crypto.createHash("sha1").update(VIZAPP_JS).digest("hex").slice(0, 16) + '"';
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q);
        var m = String(req.method || "GET").toUpperCase();
        if (path === ASSET && (m === "GET" || m === "HEAD")) {
          res.setHeader("Content-Type", "application/javascript; charset=utf-8"); res.setHeader("Cache-Control", "public, max-age=300");
          res.setHeader("X-Content-Type-Options", "nosniff"); res.setHeader("ETag", etag);
          if (req.headers && req.headers["if-none-match"] === etag) { res.statusCode = 304; res.end(); return true; }
          res.statusCode = 200; res.setHeader("Content-Length", abuf.length);
          res.end(m === "HEAD" ? undefined : abuf); return true;
        }
        var ck = String((req.headers && req.headers.cookie) || "");
        if (m === "GET" && /(?:^|;\s*)dispatch_session=/.test(ck) && !SKIP.test(path) && !/\.[a-z0-9]{1,8}$/i.test(path)) wrap(res, path);
      } catch (eReq) {
        try { console.log("[" + TAG + "] skipped: " + (eReq && eReq.message || eReq)); } catch (e2) {}
      }
      return emit0.apply(this, arguments);
    };
    Object.keys(emit0).forEach(function (k) { if (/^__/.test(k)) emit[k] = emit0[k]; });
    emit.__chat115vizapp = 1;
    SP.emit = emit;
    console.log("[" + TAG + "] attached");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
