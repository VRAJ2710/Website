// chat105v3home: v3 home page PREVIEW. Additive and self-contained.
// Only GET / with ?preview=v3 (or the td_v3p=1 cookie it sets) is changed. Every other request,
// including / without the switch, is passed to the existing handler untouched.
// /?preview=off clears the cookie. Preview responses are no-index and no-store.
// No DB, auth, Stripe, AI, email, secret or config use. Reads existing same-origin free feeds in the browser.
(function () {
  var TAG = "chat105v3home";
  var CSS = __CSS__;
  var JS = __JS__;
  var SNIP = __SNIP__;
  function cookieOn(req) {
    var c = (req && req.headers && req.headers.cookie) || "";
    return /(?:^|;\s*)td_v3p=1(?:;|$)/.test(c);
  }
  function secure(req) {
    var p = String((req.headers && req.headers["x-forwarded-proto"]) || "").split(",")[0].trim();
    return p === "https" || !!(req.socket && req.socket.encrypted);
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
  function addClass(html) {
    return html.replace(/<html\b([^>]*)>/i, function (m, attrs) {
      if (/\bclass\s*=\s*"/i.test(attrs)) return "<html" + attrs.replace(/\bclass\s*=\s*"([^"]*)"/i, function (mm, v) { return 'class="' + (v ? v + " " : "") + 'v3p"'; }) + ">";
      return "<html" + attrs + ' class="v3p">';
    });
  }
  function transform(html) {
    if (typeof html !== "string" || html.indexOf("v3home") >= 0) return null;
    if (!/<\/html>\s*$/i.test(html) || !/<\/head>/i.test(html) || !/<\/body>/i.test(html)) return null;
    var out = addClass(html);
    out = out.replace(/<\/head>/i, '<meta name="robots" content="noindex, nofollow"><link rel="stylesheet" href="/__v3p/home.css?v=' + TAG + '"></head>');
    var mm = /<main\b[^>]*>/i.exec(out);
    if (mm) out = out.slice(0, mm.index + mm[0].length) + SNIP + out.slice(mm.index + mm[0].length);
    else {
      var hh = /<\/header>/i.exec(out);
      if (!hh) return null;
      out = out.slice(0, hh.index + hh[0].length) + '<main class="wrap">' + SNIP + "</main>" + out.slice(hh.index + hh[0].length);
    }
    var bi = out.toLowerCase().lastIndexOf("</body>");
    out = out.slice(0, bi) + '<script src="/__v3p/home.js?v=' + TAG + '" defer></script>' + out.slice(bi);
    return out;
  }
  function wrap(req, res, setCookie) {
    var chunks = [], ended = false;
    var w0 = res.write, e0 = res.end, wh0 = res.writeHead;
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
    res.write = function (c, enc, cb) {
      push(c, enc);
      if (typeof enc === "function") enc(); else if (typeof cb === "function") cb();
      return true;
    };
    res.end = function (c, enc, cb) {
      if (ended) return res;
      ended = true;
      if (typeof c === "function") { cb = c; c = null; }
      else if (typeof enc === "function") { cb = enc; enc = null; }
      push(c, enc);
      res.write = w0; res.end = e0; res.writeHead = wh0;
      var body = Buffer.concat(chunks);
      var ct = String(res.getHeader("content-type") || "");
      var ce = res.getHeader("content-encoding");
      var out = null;
      if (res.statusCode === 200 && /text\/html/i.test(ct) && !ce) {
        try { out = transform(body.toString("utf8")); } catch (eT) { out = null; console.log("[" + TAG + "] preview skipped: " + (eT && eT.message || eT)); }
      }
      if (!res.headersSent) {
        try {
          if (setCookie) res.setHeader("Set-Cookie", [].concat(res.getHeader("set-cookie") || [], setCookie));
          if (out != null) {
            res.removeHeader("ETag"); res.removeHeader("Last-Modified");
            res.setHeader("Cache-Control", "private, no-store");
            res.setHeader("X-Robots-Tag", "noindex, nofollow");
            res.setHeader("X-Dispatch-Preview", "v3-home");
          }
        } catch (eH) {}
      }
      var final = out != null ? Buffer.from(out, "utf8") : body;
      if (!res.headersSent) { try { res.setHeader("Content-Length", final.length); } catch (eL) {} }
      return e0.call(res, final, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat105v3home) return;
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || "");
        var q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), qs = q < 0 ? "" : u.slice(q + 1);
        var m = String(req.method || "GET").toUpperCase();
        if ((path === "/__v3p/home.css" || path === "/__v3p/home.js") && (m === "GET" || m === "HEAD")) {
          if (path === "/__v3p/home.css") sendAsset(res, "text/css; charset=utf-8", CSS);
          else sendAsset(res, "application/javascript; charset=utf-8", JS);
          return true;
        }
        if (path !== "/" || m !== "GET") return emit0.apply(this, arguments);
        var params = qs ? qs.split("&") : [], pv = null, rest = [];
        params.forEach(function (p) { var k = p.split("=")[0]; if (k === "preview") pv = decodeURIComponent((p.split("=")[1] || "").replace(/\+/g, " ")); else if (p) rest.push(p); });
        var on = false, setCookie = null, flag = secure(req) ? "; Secure" : "";
        if (pv === "v3") { on = true; setCookie = "td_v3p=1; Path=/; Max-Age=604800; HttpOnly; SameSite=Lax" + flag; }
        else if (pv === "off") { on = false; setCookie = "td_v3p=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax" + flag; }
        else if (pv === null && cookieOn(req)) on = true;
        if (!on && !setCookie) return emit0.apply(this, arguments);
        req.url = "/" + (rest.length ? "?" + rest.join("&") : "");
        if (!on) {
          var sc = setCookie, added = false;
          var addCk = function () { if (added) return; added = true; try { if (!res.headersSent) res.setHeader("Set-Cookie", [].concat(res.getHeader("set-cookie") || [], sc)); } catch (eS) {} };
          var wh = res.writeHead, en = res.end;
          res.writeHead = function () { addCk(); res.writeHead = wh; return wh.apply(res, arguments); };
          res.end = function () { addCk(); res.end = en; return en.apply(res, arguments); };
          return emit0.apply(this, arguments);
        }
        delete req.headers["accept-encoding"];
        delete req.headers["if-none-match"];
        delete req.headers["if-modified-since"];
        wrap(req, res, setCookie);
      } catch (eReq) {
        console.log("[" + TAG + "] preview skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    emit.__chat105v3home = 1;
    SP.emit = emit;
    console.log("[chat105v3home] preview attached");
  } catch (e) {
    console.log("[" + TAG + "] preview not attached: " + (e && e.message || e));
  }
})();
