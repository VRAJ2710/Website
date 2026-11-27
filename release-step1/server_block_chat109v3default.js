// chat109v3default: make the v3 home page (chat105v3home2 + chat108saferxA/B/C) the DEFAULT home page at / for everyone.
// Additive and self-contained; appended after the chat108saferxC block, which it requires.
// Plain GET / (no query, or only utm_/gclid/fbclid/ref tags) is served as v3: the request is marked internally (td_v3p=1 is added to the request's
// cookie header only; no cookie is set on the reader). On the finished v3 page the preview ribbon, the preview noindex meta
// and the preview headers are removed, so the page is indexable and reads as the home page. The header, the full-screen menu
// (every link), the footer and every existing home section stay. /?preview=off still returns the previous home page (for
// checks and rollback comparison). Every other route is untouched. No DB, auth, payments, AI, email, secret or config use.
(function () {
  var TAG = "chat109v3default";
  var RIB_RE = /<p class="v3-rib">[\s\S]{0,600}?<\/p>/;
  var META = '<meta name="robots" content="noindex, nofollow"><link rel="stylesheet" href="/__v3p/home.css?v=chat105v3home2">';
  function transform(t) {
    if (typeof t !== "string" || t.indexOf('id="v3home"') < 0 || t.indexOf('data-v3default') >= 0) return null;
    if (!/<html\b[^>]*\bclass="[^"]*\bv3p\b[^"]*\bv8a\b[^"]*\bv9b\b[^"]*"/i.test(t)) return null;
    if (t.split(META).length !== 2) return null;
    var out = t.replace(META, '<link rel="stylesheet" href="/__v3p/home.css?v=chat105v3home2">');
    out = out.replace(RIB_RE, "");
    out = out.replace('<section class="v3" id="v3home" aria-label="Today: new home page preview">', '<section class="v3" id="v3home" aria-label="Today" data-v3default="1">');
    if (out.indexOf("data-v3default") < 0) return null;
    return out;
  }
  function wrap(res) {
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
      if (res.statusCode === 200 && /text\/html/i.test(ct) && !ce) {
        try { out = transform(body.toString("utf8")); } catch (eT) { out = null; console.log("[" + TAG + "] skipped: " + (eT && eT.message || eT)); }
      }
      var fin = out != null ? Buffer.from(out, "utf8") : body;
      if (!res.headersSent) {
        try {
          if (out != null) { res.removeHeader("X-Robots-Tag"); res.removeHeader("X-Dispatch-Preview"); res.setHeader("X-Dispatch-Home", "v3"); }
          res.setHeader("Content-Length", fin.length);
        } catch (eL) {}
      }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat109v3default) return;
    if (!SP.emit || !SP.emit.__chat108saferxC) throw new Error("chat108saferxC is not attached; v3 stays off");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), qs = q < 0 ? "" : u.slice(q + 1);
        if (path === "/" && String(req.method || "GET").toUpperCase() === "GET") {
          var keys = qs ? qs.split("&").map(function (p) { return p.split("=")[0]; }) : [];
          var hasSwitch = keys.indexOf("preview") >= 0;
          // only the plain home page (optionally with campaign tags) becomes v3; /?settings=1, /?checkout=1 and every
          // other "/?..." app route keep their own response
          var plain = keys.every(function (k) { return k === "" || /^(utm_[a-z]+|gclid|fbclid|ref)$/.test(k); });
          if (!hasSwitch && plain) {
            var ck = String((req.headers && req.headers.cookie) || "");
            if (!/(?:^|;\s*)td_v3p=1(?:;|$)/.test(ck)) req.headers.cookie = (ck ? ck + "; " : "") + "td_v3p=1";
          }
          if (!hasSwitch && !plain && req.headers && req.headers.cookie) {
            // a td_v3p cookie left from the preview must not turn an app route such as /?settings=1 into the home page
            req.headers.cookie = String(req.headers.cookie).replace(/(?:^|;\s*)td_v3p=1(?=;|$)/g, "").replace(/^;\s*/, "");
          }
          if ((!hasSwitch && plain) || /(?:^|&)preview=v3(?:&|$)/.test(qs)) wrap(res);
        }
      } catch (eReq) {
        console.log("[" + TAG + "] skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    emit.__chat109v3default = 1;
    emit.__chat108saferxC = 1;
    emit.__chat108saferxB = 1;
    emit.__chat108saferxA = 1;
    emit.__chat105v3home2 = 1;
    SP.emit = emit;
    console.log("[" + TAG + "] " + "attached");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
