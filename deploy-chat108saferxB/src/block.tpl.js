// chat108saferxB: v3 home PREVIEW, batch B (27 Nov 2026). Additive; layered on chat108saferxA (and chat105v3home2).
// Only changes a response that chat108saferxA has already turned into the batch-A preview (html class v8a, id="v3home").
// Every other request, including / and /?preview=off, is untouched. The existing v3 cards are regrouped, not replaced:
// Today's story (sticky left: gold futures chart; right scrolls: market snapshot, upcoming events, what moved; phones stack
// snapshot, chart, events, moved), Prices and mood (key prices,
// plus bitcoin and WTI copied from the market-context table, and the gauges), Charts (one-month tiles), How to use the desk.
// The old market-context table is kept, collapsed under "Full table". Market colours and icons are added in the browser.
// No DB, auth, payments, AI, email, secret, config or network use. Serves two static assets under /__v3p/.
(function () {
  var TAG = "chat108saferxB";
  var CSS = __CSS__;
  var JS = __JS__;
  var MK = [["gold", "Gold"], ["dollar", "Dollar"], ["yields", "Yields"], ["oil", "Oil"], ["crypto", "Crypto"], ["equities", "Equities"]];
  var IC = __IC__;
  var IDS = ["v3-snap", "v3-gauges", "v3-prices", "v3-gold", "v3-cal", "v3-tiles", "v3-moves"];
  var FULL_RE = /<div data-need hidden><h2>Market context<\/h2>[\s\S]{0,4000}?<\/table><p class="note c93miss" hidden>[^<]{0,300}<\/p><\/div>/;
  function legend() {
    return '<ul class="v9-legend" aria-label="Market colour key">' + MK.map(function (m) {
      return '<li data-mk="' + m[0] + '"><span class="v9-mi" aria-hidden="true"><svg viewBox="0 0 24 24">' + IC[m[0]] + "</svg></span>" + m[1] + "</li>";
    }).join("") + "</ul>";
  }
  function steps() {
    return '<ol class="v9-steps">' +
      '<li><p class="v9-sk">Start here</p><h3>Read the Brief</h3><p>Today\u2019s main theme in one short read, with the source and UK time of every figure. <a href="/brief/">Open the Brief</a></p></li>' +
      '<li><p class="v9-sk">Then</p><h3>Check prices and mood</h3><p>Key prices, the fear gauge and 1-year ranges, each with its source, time and delay label. <a href="#v9-strip">Prices and mood</a></p></li>' +
      '<li><p class="v9-sk">Go deeper</p><h3>Charts and the calendar</h3><p>Longer charts in the Terminal and official release times in the Calendar. <a href="/terminal/">Terminal</a> \u00b7 <a href="/calendar/">Calendar</a></p></li>' +
      "</ol>";
  }
  function transform(t) {
    if (typeof t !== "string" || t.indexOf('id="v9-story"') >= 0 || t.indexOf('id="v3home"') < 0) return null;
    if (!/<html\b[^>]*\bclass="[^"]*\bv8a\b[^"]*"/i.test(t) || !/<\/body>/i.test(t)) return null;
    var g0 = t.indexOf('<div class="v3-grid">');
    if (g0 < 0) return null;
    var lastId = t.indexOf('id="v3-moves"', g0);
    if (lastId < 0) return null;
    var aEnd = t.indexOf("</article>", lastId);
    if (aEnd < 0 || t.slice(aEnd + 10, aEnd + 16) !== "</div>") return null;
    var g1 = aEnd + 16, grid = t.slice(g0, g1), A = {};
    for (var i = 0; i < IDS.length; i++) {
      var re = new RegExp('<article class="[^"]*" id="' + IDS[i] + '">[\\s\\S]{0,400}?</article>'), m = re.exec(grid);
      if (!m || grid.split('id="' + IDS[i] + '"').length !== 2) return null;
      A[IDS[i]] = m[0];
    }
    var rest = grid.slice('<div class="v3-grid">'.length, -6);
    IDS.forEach(function (id) { rest = rest.replace(A[id], ""); });
    if (rest.replace(/\s+/g, "") !== "") return null; // the grid holds only the seven cards; anything else, leave the page alone
    var html = '<div class="v9">' +
      '<section class="v9-sec" id="v9-story" aria-labelledby="v9-h-story"><h2 class="v9-hd" id="v9-h-story">Today\u2019s story</h2>' +
      '<div class="v9-split">' + A["v3-snap"] + A["v3-gold"] + A["v3-cal"] + A["v3-moves"] + "</div></section>" +
      '<section class="v9-sec" id="v9-strip" aria-labelledby="v9-h-strip"><div class="v9-hdrow"><h2 class="v9-hd" id="v9-h-strip">Prices and mood</h2>' + legend() + "</div>" +
      '<div class="v9-strip">' + A["v3-prices"] + A["v3-gauges"] + "</div></section>" +
      '<section class="v9-sec" id="v9-charts" aria-labelledby="v9-h-charts"><h2 class="v9-hd" id="v9-h-charts">Charts \u00b7 one month</h2>' + A["v3-tiles"] + "</section>" +
      '<section class="v9-sec" id="v9-how" aria-labelledby="v9-h-how"><h2 class="v9-hd" id="v9-h-how">How to use the desk</h2>' + steps() + "</section></div>";
    var out = t.slice(0, g0) + html + t.slice(g1);
    var fm = FULL_RE.exec(out);
    if (fm) out = out.slice(0, fm.index) + '<details class="v9-full" id="v9-full"><summary>Full table: market context <span class="v9-fs">(all measures, sources and times)</span></summary>' + fm[0] + "</details>" + out.slice(fm.index + fm[0].length);
    out = out.replace(/<html\b([^>]*?)\bclass="([^"]*)"/i, function (m, a, c) { return "<html" + a + 'class="' + c + ' v9b"'; });
    out = out.replace(/<\/head>/i, '<link rel="stylesheet" href="/__v3p/b9.css?v=' + TAG + '"></head>');
    var bi = out.toLowerCase().lastIndexOf("</body>");
    out = out.slice(0, bi) + '<script src="/__v3p/b9.js?v=' + TAG + '" defer></script>' + out.slice(bi);
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
        try { out = transform(body.toString("utf8")); } catch (eT) { out = null; console.log("[" + TAG + "] preview skipped: " + (eT && eT.message || eT)); }
      }
      var fin = out != null ? Buffer.from(out, "utf8") : body;
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); if (out != null) res.setHeader("X-Dispatch-Preview", "v3-home; chat108saferxA; " + TAG); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat108saferxB) return;
    if (!SP.emit || !SP.emit.__chat108saferxA) throw new Error("chat108saferxA preview is not attached; nothing to layer on");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), m = String(req.method || "GET").toUpperCase();
        if ((path === "/__v3p/b9.css" || path === "/__v3p/b9.js") && (m === "GET" || m === "HEAD")) {
          if (path === "/__v3p/b9.css") sendAsset(res, "text/css; charset=utf-8", CSS);
          else sendAsset(res, "application/javascript; charset=utf-8", JS);
          return true;
        }
        if (on(req)) wrap(res);
      } catch (eReq) {
        console.log("[" + TAG + "] preview skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    emit.__chat108saferxB = 1;
    emit.__chat108saferxA = 1;
    emit.__chat105v3home2 = 1;
    SP.emit = emit;
    globalThis.__chat108saferxB = { transform: transform };
    console.log("[" + TAG + "] " + "preview attached");
  } catch (e) {
    console.log("[" + TAG + "] preview not attached: " + (e && e.message || e));
  }
})();
