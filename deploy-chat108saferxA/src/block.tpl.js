// chat108saferxA: v3 home PREVIEW, batch A (27 Nov 2026). Additive and self-contained; layered on chat105v3home2.
// Only changes a response that chat105v3home2 has already turned into the v3 preview (GET / with ?preview=v3 or the
// td_v3p=1 cookie, and the page carries id="v3home"). Every other request, including / without the switch, is untouched.
// On the preview: full-screen hero (existing kicker, dek and byline kept; H1 set on two lines), an arc of tool links to real
// routes, swipeable desk tabs to real routes, slim header (all links stay in the full-screen menu), the duplicate signup card
// removed so the existing free-brief form is the only signup (moved, unchanged, into a closing band), a gold reading-progress
// bar, hero fade-in and card hover lift (all off under prefers-reduced-motion), and tighter cards.
// No DB, auth, payments, AI, email, secret, config or network use. Serves two static assets under /__v3p/.
(function () {
  var TAG = "chat108saferxA";
  var CSS = __CSS__;
  var JS = __JS__;
  var TOOLS = [
    ["/brief/", "Brief", "#3b82f6", "#1e40af", '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 12h6M10 16h6"/>'],
    ["/playbook/", "Playbook", "#f97316", "#b43c0c", '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11M9 8h6"/>'],
    ["/gold/", "Gold", "#d9a441", "#7d5410", '<path d="M3 19h18l-2.5-6h-13z"/><path d="M7.5 13 9.5 7h5l2 6"/>'],
    ["/lab/", "Lab", "#8b5cf6", "#5b21b6", '<path d="M9 3h6M10 3v6l-5.5 9.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.5-2.5L14 9V3"/><path d="M7.5 15h9"/>'],
    ["/signals/", "Signals", "#10b981", "#04694a", '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>'],
    ["/markets/", "Markets", "#06b6d4", "#0b6377", '<path d="M4 20h16"/><path d="M7 16v-5M12 16V6M17 16v-8"/>'],
    ["/news/", "Newsroom", "#ec4899", "#a3134f", '<path d="M4 5h13v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M17 9h3v10a2 2 0 0 1-2 2M8 9h5M8 13h5M8 17h3"/>']
  ];
  var ARC_Y = [46, 20, 5, 0, 5, 20, 46];
  var TABS = [["/", "Today"], ["/brief/", "Brief"], ["/gold/", "Gold"], ["/terminal/", "Terminal"], ["/markets/", "Markets"],
    ["/calendar/", "Calendar"], ["/signals/", "Signals"], ["/lab/", "Market Lab"], ["/news/", "Newsroom"], ["/research/", "Research"],
    ["/playbook/", "Playbook"], ["/cpi/", "CPI Day"], ["/crypto/", "Crypto"], ["/screener/", "Screener"]];
  function arcHtml() {
    var li = TOOLS.map(function (t, i) {
      return '<li style="--y:' + ARC_Y[i] + 'px"><a href="' + t[0] + '"><span class="v8-ic" style="--a:' + t[2] + ";--b:" + t[3] +
        '" aria-hidden="true"><svg viewBox="0 0 24 24">' + t[4] + "</svg></span><span>" + t[1] + "</span></a></li>";
    }).join("");
    return '<nav class="v8-arc" aria-label="Desk tools"><svg class="v8-arcline" viewBox="0 0 900 110" preserveAspectRatio="none" aria-hidden="true">' +
      '<path d="M20 100 Q450 -40 880 100" fill="none" stroke="var(--v-line2)" stroke-width="1.5"/></svg><ul>' + li + "</ul></nav>";
  }
  function tabsHtml() {
    return '<nav class="v8-tabs" aria-label="Desk sections"><ul>' + TABS.map(function (t) {
      return '<li><a href="' + t[0] + '"' + (t[0] === "/" ? ' aria-current="page"' : "") + ">" + t[1] + "</a></li>";
    }).join("") + "</ul></nav>";
  }
  var HERO_RE = /<section><div class="kicker">([^<]{1,120})<\/div><h1>([^<]{1,160})<\/h1>(<p class="dek">[\s\S]{0,1200}?<\/p>)?(<p class="byline">[\s\S]{0,600}?<\/p>)?<\/section>/;
  var SU_RE = /<section><form class="c96su" method="post" action="\/free-brief"[^>]*>[\s\S]{0,6000}?<\/form><\/section>/;
  var RIB_RE = /<p class="v3-rib">[\s\S]{0,600}?<\/p>/;
  var CSM_RE = /<section>(<div class="kicker">Research<\/div><h2[^>]*>Capital Sustainability Monitor)/;
  var SI_RE = /<\/details>(<a class="cta" href="(\/__auth\/[a-z]+|\/account\/?|\/settings\/?)">([^<]{1,40})<\/a>)<\/nav>/;
  function transform(t) {
    if (typeof t !== "string" || t.indexOf('id="v3home"') < 0 || t.indexOf('id="v8-hero"') >= 0) return null;
    if (!/<html\b[^>]*\bclass="[^"]*\bv3p\b[^"]*"/i.test(t) || !/<\/main>/i.test(t) || !/<\/body>/i.test(t)) return null;
    var out = t;
    out = out.replace(/<html\b([^>]*?)\bclass="([^"]*)"/i, function (m, a, c) { return "<html" + a + 'class="' + c + ' v8a"'; });
    out = out.replace(/<\/head>/i, '<link rel="stylesheet" href="/__v3p/a8.css?v=' + TAG + '"></head>');
    out = out.replace(/<body\b[^>]*>/i, function (m) { return m + '<div class="v8-prog" aria-hidden="true"><i></i></div>'; });
    var v3at = out.indexOf('<section class="v3" id="v3home"');
    if (v3at < 0) return null;
    // One signup: lift the existing free-brief form out (unchanged) and drop the duplicate v3 card.
    var su = SU_RE.exec(out), band = "";
    if (su && su.index > v3at && (su[0].match(/<form\b/g) || []).length === 1) {
      out = out.slice(0, su.index) + out.slice(su.index + su[0].length);
      band = '<section class="v8-band" id="v8-band" aria-label="Free daily brief">' + su[0].slice("<section>".length);
      var s0 = out.indexOf('<div class="v3-card v3-su">'), g0 = out.indexOf('<div class="v3-grid">');
      if (s0 > v3at && g0 > s0) {
        var seg = out.slice(s0, g0);
        if ((seg.match(/<form\b/g) || []).length === 1 && seg.indexOf('action="/free-brief"') > 0) out = out.slice(0, s0) + out.slice(g0);
      }
    }
    // Preview ribbon moves into the hero.
    var rib = "", rm = RIB_RE.exec(out);
    if (rm && rm.index > v3at) { rib = rm[0]; out = out.slice(0, rm.index) + out.slice(rm.index + rm[0].length); }
    // Hero from the existing first section (kicker, H1, dek and byline kept).
    var hm = HERO_RE.exec(out), hero = "";
    if (hm && hm.index > v3at) {
      out = out.slice(0, hm.index) + out.slice(hm.index + hm[0].length);
      var h1 = hm[2], two = /^Know what matters before gold moves\.$/.test(h1.trim());
      var h1html = two ? '<span class="v8-l1">Know what matters.</span> <span class="v8-l2">Before gold moves.</span>' : '<span class="v8-l1">' + h1 + "</span>";
      var dek = hm[3] ? hm[3].replace(/^<p class="dek">/, '<p class="v8-dek">') : "";
      var by = hm[4] ? hm[4].replace(/^<p class="byline">/, '<p class="v8-by">') : "";
      hero = '<section class="v8-hero" id="v8-hero" aria-labelledby="v8-h1"><div class="v8-hero-in">' + (rib ? "<div>" + rib + "</div>" : "") +
        '<p class="v8-kick">' + hm[1] + '</p><h1 id="v8-h1">' + h1html + "</h1>" + dek +
        '<div class="v8-ctas"><a class="v8-btn v8-btn-p" href="#v3home">See today\u2019s market</a>' +
        (band ? '<a class="v8-btn" href="#v8-band">Get the free brief</a>' : "") + "</div>" + arcHtml() + by + "</div></section>";
      rib = "";
    }
    v3at = out.indexOf('<section class="v3" id="v3home"');
    var open = out.indexOf(">", v3at) + 1;
    out = out.slice(0, open) + (rib || "") + tabsHtml() + out.slice(open);
    if (hero) out = out.slice(0, v3at) + hero + out.slice(v3at);
    out = out.replace(CSM_RE, '<section id="v8-csm">$1');
    if (band) { var me = out.lastIndexOf("</main>"); if (me > 0) out = out.slice(0, me) + band + out.slice(me); }
    // Slim header: a copy of the header's own sign-in link (whatever it says for this visitor) for narrow screens.
    var si = SI_RE.exec(out), dm = out.indexOf('<details class="menu">');
    if (si && dm > si.index) out = out.slice(0, dm) + '<a class="cta v8-si" href="' + si[2] + '">' + si[3] + "</a>" + out.slice(dm);
    var bi = out.toLowerCase().lastIndexOf("</body>");
    out = out.slice(0, bi) + '<script src="/__v3p/a8.js?v=' + TAG + '" defer></script>' + out.slice(bi);
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
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); if (out != null) res.setHeader("X-Dispatch-Preview", "v3-home; " + TAG); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat108saferxA) return;
    if (!SP.emit || !SP.emit.__chat105v3home2) throw new Error("chat105v3home2 preview is not attached; nothing to layer on");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q), m = String(req.method || "GET").toUpperCase();
        if ((path === "/__v3p/a8.css" || path === "/__v3p/a8.js") && (m === "GET" || m === "HEAD")) {
          if (path === "/__v3p/a8.css") sendAsset(res, "text/css; charset=utf-8", CSS);
          else sendAsset(res, "application/javascript; charset=utf-8", JS);
          return true;
        }
        if (on(req)) wrap(res);
      } catch (eReq) {
        console.log("[" + TAG + "] preview skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    emit.__chat108saferxA = 1;
    emit.__chat105v3home2 = 1;
    SP.emit = emit;
    globalThis.__chat108saferxA = { transform: transform };
    console.log("[" + TAG + "] " + "preview attached");
  } catch (e) {
    console.log("[" + TAG + "] preview not attached: " + (e && e.message || e));
  }
})();
