// chat108saferxC: v3 home PREVIEW fix (27 Nov 2026). Additive; layered on chat108saferxB (and A, chat105v3home2).
// Rule: when a free live or delayed quote exists it is the MAIN number, with a lag label and UK time; the official or daily
// close goes on a secondary line. On the gold futures chart card the latest delayed futures quote becomes the main figure,
// with the 3-month change measured to it (same continuous front-month series) and the last completed close on a secondary
// line; with no fresh quote the close stays main, labelled "Last close". Other v3 cards: a figure dated before today (UK)
// is no longer labelled "Delayed"/"Live" but "Last close" (key prices, five things that moved, range bars, chart tiles).
// How: the preview page (already built by B) loads the v3 renderer from /__v3p/home.js?v=chat108saferxC; only that URL is
// served with exact, counted text replacements (all or nothing; if any is missing the file is served unchanged). The
// renderer at its old URL, the normal homepage and every other route are untouched. One static asset: /__v3p/c10.css.
// No DB, auth, payments, AI, email, secret, config or network use.
(function () {
  var TAG = "chat108saferxC";
  var CSS = __CSS__;
  var PATCHES = __PATCHES__;
  var OLD_SRC = '<script src="/__v3p/home.js?v=chat105v3home2" defer></script>';
  var NEW_SRC = '<script src="/__v3p/home.js?v=' + TAG + '" defer></script>';
  function count(s, x) { return s.split(x).length - 1; }
  function patchJs(s) {
    if (typeof s !== "string" || s.indexOf("/* chat105v3home2: v3 home preview renderer") !== 0) return null;
    for (var i = 0; i < PATCHES.length; i++) if (count(s, PATCHES[i][0]) !== PATCHES[i][2]) return null;
    for (var j = 0; j < PATCHES.length; j++) s = s.split(PATCHES[j][0]).join(PATCHES[j][1]);
    return s;
  }
  function transform(t) {
    if (typeof t !== "string" || t.indexOf("/__v3p/c10.css") >= 0 || t.indexOf('id="v9-story"') < 0) return null;
    if (!/<html\b[^>]*\bclass="[^"]*\bv9b\b[^"]*"/i.test(t) || count(t, OLD_SRC) !== 1 || !/<\/head>/i.test(t)) return null;
    var out = t.replace(OLD_SRC, NEW_SRC);
    out = out.replace(/<\/head>/i, '<link rel="stylesheet" href="/__v3p/c10.css?v=' + TAG + '"></head>');
    return out;
  }
  function on(req) {
    var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), qs = q < 0 ? "" : u.slice(q + 1);
    if (path !== "/" || String(req.method || "GET").toUpperCase() !== "GET") return false;
    var pv = null;
    qs.split("&").forEach(function (p) { if (p.split("=")[0] === "preview") { try { pv = decodeURIComponent((p.split("=")[1] || "").replace(/\+/g, " ")); } catch (e) { pv = "?"; } } });
    if (pv === "v3") return true;
    if (pv !== null) return false;
    return /(?:^|;\s*)td_v3p=1(?:;|$)/.test(String((req.headers && req.headers.cookie) || ""));
  }
  function sendAsset(res, type, body) {
    var buf = Buffer.from(body, "utf8");
    res.statusCode = 200;
    res.setHeader("Content-Type", type);
    res.setHeader("Content-Length", buf.length);
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("X-Robots-Tag", "noindex, nofollow");
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.end(buf);
  }
  function wrap(res, fx, hdrName) {
    var chunks = [], ended = false, w0 = res.write, e0 = res.end, wh0 = res.writeHead;
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
      return res;
    };
    res.write = function (c, enc, cb) { push(c, enc); if (typeof enc === "function") enc(); else if (typeof cb === "function") cb(); return true; };
    res.end = function (c, enc, cb) {
      if (ended) return res;
      ended = true;
      if (typeof c === "function") { cb = c; c = null; } else if (typeof enc === "function") { cb = enc; enc = null; }
      push(c, enc);
      res.write = w0; res.end = e0; res.writeHead = wh0;
      var body = Buffer.concat(chunks), out = null;
      var ct = String(res.getHeader("content-type") || ""), ce = res.getHeader("content-encoding");
      if (res.statusCode === 200 && (hdrName ? /javascript/i : /text\/html/i).test(ct) && !ce) {
        try { out = fx(body.toString("utf8")); } catch (eT) { out = null; console.log("[" + TAG + "] preview skipped: " + (eT && eT.message || eT)); }
      }
      var fin = out != null ? Buffer.from(out, "utf8") : body;
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); if (out != null) res.setHeader("X-Dispatch-Preview", hdrName || "v3-home; chat108saferxA; chat108saferxB; " + TAG); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat108saferxC) return;
    if (!SP.emit || !SP.emit.__chat108saferxB) throw new Error("chat108saferxB preview is not attached; nothing to layer on");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), qs = q < 0 ? "" : u.slice(q + 1), m = String(req.method || "GET").toUpperCase();
        if (path === "/__v3p/c10.css" && (m === "GET" || m === "HEAD")) { sendAsset(res, "text/css; charset=utf-8", CSS); return true; }
        if (path === "/__v3p/home.js" && m === "GET" && qs === "v=" + TAG) wrap(res, patchJs, "v3-renderer; " + TAG);
        else if (on(req)) wrap(res, transform, null);
      } catch (eReq) {
        console.log("[" + TAG + "] preview skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    emit.__chat108saferxC = 1;
    emit.__chat108saferxB = 1;
    emit.__chat108saferxA = 1;
    emit.__chat105v3home2 = 1;
    SP.emit = emit;
    globalThis.__chat108saferxC = { transform: transform, patchJs: patchJs };
    console.log("[" + TAG + "] " + "preview attached");
  } catch (e) {
    console.log("[" + TAG + "] preview not attached: " + (e && e.message || e));
  }
})();
