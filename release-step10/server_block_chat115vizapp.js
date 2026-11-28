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
  var VIZAPP_JS = "/* chat115vizapp: shows the approved chat114viz Market Snapshot layer (same markup, same data, same viz.js) to signed-in readers\n   inside the member app on /brief/, /gold/, /markets/ and /research/. It only adds one <section id=\"chat114viz\"> at the top of the\n   visible page body (#main on phones; on desktop the page's overlay body, or the prices panel for markets) and removes it on any\n   other route. It does not\n   change, move or hide anything the app draws. Any error stops this script and leaves the app as it was. Not investment advice. */\n(function () {\n  \"use strict\";\n  if (window.__chat115vizapp) return; window.__chat115vizapp = 1;\n  try {\n    var PAGES = { brief: 1, gold: 1, markets: 1, research: 1 };\n    var VIZ_JS = \"/__chat114viz/viz.js?v=chat114viz\", FRESH_MS = 5 * 60 * 1000;\n    var cache = {}, loading = null, dead = false, queued = false, errors = 0;\n    var D = document, de = D.documentElement;\n    function routePage() {\n      var m = /^\\/(brief|gold|markets|research)\\/?$/.exec(location.pathname || \"\");\n      return m && PAGES[m[1]] ? m[1] : null;\n    }\n    function visible(el) { return !!(el && el.isConnected && el.getClientRects().length && el.offsetWidth > 0); }\n    // Where the app draws the page the reader sees: phones use #main; on desktop brief, gold and research open in their overlay\n    // (#briefOv, #goldOv, #researchOv, body .term-overlay-body) and markets is the expanded prices panel (#p1body).\n    var OV = { brief: \"briefOv\", gold: \"goldOv\", research: \"researchOv\" };\n    function target(page) {\n      var ov = OV[page] && D.getElementById(OV[page]);\n      if (ov && visible(ov)) { var ob = ov.querySelector(\".term-overlay-body\"); if (ob && visible(ob)) return ob; }\n      var main = D.getElementById(\"main\"); if (visible(main)) return main;\n      if (page === \"markets\") { var p1 = D.getElementById(\"p1body\"); if (visible(p1)) return p1; }\n      return null;\n    }\n    function setClasses(page) {\n      [\"brief\", \"gold\", \"markets\", \"research\"].forEach(function (p) { if (p !== page) de.classList.remove(\"cz-\" + p); });\n      if (page) { de.classList.add(\"cz-on\"); de.classList.add(\"cz-\" + page); } else de.classList.remove(\"cz-on\");\n    }\n    function strays(keep) {\n      var all = D.querySelectorAll(\"#chat114viz\");\n      for (var i = 0; i < all.length; i++) if (all[i] !== keep && all[i].parentNode) all[i].parentNode.removeChild(all[i]);\n    }\n    function build(page) {\n      var s = D.createElement(\"section\");\n      s.id = \"chat114viz\"; s.className = \"cz-root cz-app\"; s.setAttribute(\"data-cz-page\", page);\n      s.setAttribute(\"aria-label\", \"Market snapshot and key figures\");\n      s.innerHTML = '<p class=\"cz-loading\">Loading the market snapshot from this site\\u2019s free feeds\\u2026</p>';\n      return { el: s, t: Date.now(), ran: false };\n    }\n    function run(entry) {\n      // viz.js draws into the element with id=\"chat114viz\" that is in the page when it runs; it runs once per load, so it is\n      // re-run (same cached file) for each new snapshot. Only one run at a time.\n      if (loading || entry.ran) return;\n      entry.ran = true; loading = entry;\n      var sc = D.createElement(\"script\");\n      sc.src = VIZ_JS; sc.async = true;\n      sc.onload = sc.onerror = function () { loading = null; if (sc.parentNode) sc.parentNode.removeChild(sc); schedule(); };\n      try { window.__chat114viz = 0; } catch (e) {}\n      (D.head || de).appendChild(sc);\n    }\n    function ensure() {\n      queued = false;\n      if (dead) return;\n      try {\n        var page = routePage();\n        if (!page) { strays(null); setClasses(null); return; }\n        var t = target(page); if (!t) { strays(null); return; }\n        var e = cache[page];\n        if (!e || (e.el.parentNode !== t && Date.now() - e.t > FRESH_MS && !loading)) { e = cache[page] = build(page); }\n        if (e.el.parentNode !== t || t.firstElementChild !== e.el) {\n          if (loading && loading !== e && loading.el.isConnected) return; // let a pending draw finish first\n          t.insertBefore(e.el, t.firstChild);\n        }\n        strays(e.el); setClasses(page);\n        if (!e.ran) run(e);\n        else if (!loading && !e.el.getAttribute(\"data-cz-ready\") && e.el.querySelector(\".cz-loading\") && Date.now() - e.t > 20000 && !e.retried) { e.retried = true; e.ran = false; run(e); }\n      } catch (err) {\n        if (++errors >= 3) stop();\n      }\n    }\n    function schedule() { if (queued || dead) return; queued = true; (window.requestAnimationFrame || setTimeout)(ensure, 16); }\n    var mo = null, iv = null;\n    function stop() {\n      dead = true;\n      try { if (mo) mo.disconnect(); } catch (e) {}\n      try { clearInterval(iv); } catch (e) {}\n      try { strays(null); setClasses(null); } catch (e) {}\n    }\n    [\"pushState\", \"replaceState\"].forEach(function (k) {\n      var o = history[k]; if (typeof o !== \"function\") return;\n      history[k] = function () { var r = o.apply(this, arguments); try { schedule(); } catch (e) {} return r; };\n    });\n    window.addEventListener(\"popstate\", schedule);\n    window.addEventListener(\"resize\", schedule);\n    function start() {\n      try { mo = new MutationObserver(schedule); mo.observe(D.body, { childList: true, subtree: true }); } catch (e) {}\n      iv = setInterval(schedule, 2000);\n      schedule();\n    }\n    if (D.readyState === \"loading\") D.addEventListener(\"DOMContentLoaded\", start); else start();\n  } catch (e) {}\n})();\n";
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
