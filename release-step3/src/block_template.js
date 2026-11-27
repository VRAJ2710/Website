// chat107credits: data-source credits (commit 12e9f76f). release-step3 (27 Nov 2026): appended after the step-1 v3 blocks on
// the live r6n + r6p tree (no softgate); reader text never shows a raw FRED series ID: "(FRED PAYEMS)" becomes "(FRED)" plus an
// empty marker the client turns into the formal citation line under the table or card.
// Adds: FRED notice in the site footer and on /methodology; a per-series FRED citation line under each card that
// shows a FRED series (original source, series ID inside the citation only, FRED, UK access date of the fetch);
// a "Source: U.S. Treasury, Fiscal Data" credit next to any fiscaldata.treasury.gov link; FRED request spacing
// (at most 2 per second); and a 30-day cap on cached FRED data. No database, payment, email, secret or config use.
(function () {
  var TAG = "chat107credits";
  var FRED_NOTE = "This product uses FRED\u00ae data but is not endorsed or certified by the Federal Reserve Bank of St. Louis.";
  var RETAIN_MS = 30 * 864e5;
  var GAP_MS = 500;
  var SERIES = __SERIES__;
  var HIDE = {};
  Object.keys(SERIES).forEach(function (id) { if (SERIES[id].hide) HIDE[id] = 1; });
  var CLIENT = __CLIENT__;
  var CSS = "<style id=\"c107-css\">.c107-cites{margin:8px 0 0;padding:0;max-width:100%;min-width:0}.c107-cite{margin:4px 0 0;font-size:12px;line-height:1.45;opacity:.82;color:inherit;overflow-wrap:anywhere;word-break:break-word;max-width:100%}.c107-cite a,.c107-fred a,.c107-meth a{color:inherit;text-decoration:underline}.c107-fred{margin:8px 0 0;font-size:12px;line-height:1.45;opacity:.85;overflow-wrap:anywhere}.c107-meth{overflow-wrap:anywhere}.c107-hold{font-size:13px;opacity:.85}</style>";
  var seen = {};
  function ukDate(ms) {
    try { return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric", month: "long", year: "numeric" }).format(new Date(ms)); } catch (e) { return ""; }
  }
  function idsOfUrl(u) {
    var s = String(u || "");
    if (!/^https?:\/\/(?:fred|api)\.stlouisfed\.org\//i.test(s)) return null;
    var m = /[?&](?:id|series_id)=([^&#]+)/.exec(s), out = [];
    if (m) decodeURIComponent(m[1]).split(",").forEach(function (x) { x = x.trim().toUpperCase(); if (/^[A-Z0-9]+$/.test(x)) out.push(x); });
    return out;
  }
  // FRED request spacing: one request at a time per process, at least GAP_MS apart (<= 2 per second).
  var chain = Promise.resolve(), lastAt = 0;
  function spaced(run) {
    var p = chain.then(function () {
      var wait = Math.max(0, lastAt + GAP_MS - Date.now());
      return new Promise(function (r) { setTimeout(r, wait); }).then(function () { lastAt = Date.now(); return run(); });
    });
    chain = p.then(function () {}, function () {});
    return p;
  }
  function wrapFetch() {
    var f0 = globalThis.fetch;
    if (typeof f0 !== "function" || f0.__c107) return false;
    var f = function (input, init) {
      var u = "";
      try { u = typeof input === "string" ? input : (input && (input.href || input.url)) || ""; } catch (e) { u = ""; }
      var ids = idsOfUrl(u);
      if (!ids) return f0.apply(this, arguments);
      var self = this, args = arguments;
      return spaced(function () { return f0.apply(self, args); }).then(function (r) {
        if (r && r.ok) { var now = Date.now(); ids.forEach(function (id) { seen[id] = now; }); }
        return r;
      });
    };
    f.__c107 = 1;
    globalThis.fetch = f;
    return true;
  }
  function memAt(key) {
    try { if (typeof c97Mem !== "undefined" && c97Mem && typeof c97Mem.get === "function") { var e = c97Mem.get(key); if (e && e.v && e.at > 0) return e.at; } } catch (e1) {}
    return 0;
  }
  function accessMs(id) {
    var at = seen[id] || 0;
    at = Math.max(at, memAt("fred:" + id));
    try { if (id === "DFII10" && typeof RT53_RY !== "undefined" && RT53_RY && RT53_RY.v && RT53_RY.at > 0) at = Math.max(at, RT53_RY.at); } catch (e2) {}
    try { if ((id === "DCOILWTICO" || id === "DCOILBRENTEU") && typeof RT44_EIA !== "undefined" && RT44_EIA && RT44_EIA.src === "fred" && RT44_EIA.at > 0) at = Math.max(at, RT44_EIA.at); } catch (e3) {}
    if (id === "DFII10" || id === "DTWEXBGS") { var m = memAt("c101:model"); if (m) at = Math.max(at, m); }
    return at;
  }
  function eiaViaFred() {
    try { return typeof RT44_EIA !== "undefined" && RT44_EIA && RT44_EIA.src === "fred" && !!RT44_EIA.v; } catch (e) { return false; }
  }
  function cfgJson() {
    var d = {};
    Object.keys(SERIES).forEach(function (id) { var ms = accessMs(id); if (ms) d[id] = ukDate(ms); });
    return JSON.stringify({ d: d, eia: eiaViaFred(), hide: HIDE }).replace(/</g, "\\u003c");
  }
  // Retention: drop cached FRED data older than 30 days.
  function sweep() {
    var now = Date.now(), dropped = 0;
    try {
      if (typeof c97Mem !== "undefined" && c97Mem && typeof c97Mem.forEach === "function") {
        var del = [];
        c97Mem.forEach(function (e, k) { if (/^(fred:|c101:model$)/.test(String(k)) && e && e.at > 0 && now - e.at > RETAIN_MS && !e.p) del.push(k); });
        del.forEach(function (k) { c97Mem.delete(k); dropped++; });
      }
    } catch (e1) {}
    try { if (typeof RT53_RY !== "undefined" && RT53_RY && RT53_RY.v && RT53_RY.at > 0 && now - RT53_RY.at > RETAIN_MS) { RT53_RY.v = null; dropped++; } } catch (e2) {}
    try { if (typeof RT44_EIA !== "undefined" && RT44_EIA && RT44_EIA.src === "fred" && RT44_EIA.v && RT44_EIA.at > 0 && now - RT44_EIA.at > RETAIN_MS) { RT44_EIA.v = null; dropped++; } } catch (e3) {}
    Object.keys(seen).forEach(function (id) { if (now - seen[id] > RETAIN_MS) delete seen[id]; });
    return dropped;
  }
  function pathOf(url) { return String(url || "").split("?")[0].split("#")[0]; }
  function footerAdd(t) {
    if (t.indexOf("class=\"c107-fred\"") >= 0) return t;
    var i = t.indexOf("<footer class=\"site\"");
    if (i < 0) return t;
    var j = t.indexOf("</footer>", i);
    if (j < 0) return t;
    var p = "<p class=\"c107-fred\">" + FRED_NOTE + "</p>";
    var k = t.lastIndexOf("</div>", j);
    var at = (k > i && t.slice(k, j) === "</div>") ? k : j;
    return t.slice(0, at) + p + t.slice(at);
  }
  function methAdd(t, url) {
    if (pathOf(url).replace(/\/$/, "") !== "/methodology" || t.indexOf("class=\"c107-meth\"") >= 0 || t.indexOf("<main") < 0) return t;
    var mark = "</table>", h = t.indexOf("<h2>Times and trading sessions</h2>");
    var at = -1;
    if (h > 0) { var w = t.lastIndexOf("</div>", h); var tb = t.lastIndexOf(mark, h); at = (w > tb && t.slice(w, h) === "</div>") ? h : (tb > 0 ? tb + mark.length : -1); }
    if (at < 0) { var s = t.indexOf("</section>", t.indexOf("<main")); at = s; }
    if (at < 0) return t;
    var block = "<p class=\"c107-meth\">FRED: " + FRED_NOTE + " Where a figure on this site comes from a FRED series, the card shows a citation line naming the original source, the FRED series, and the date we retrieved it (UK date). U.S. Treasury Fiscal Data, where used, is credited as \u201cSource: U.S. Treasury, Fiscal Data\u201d with a link to <a href=\"https://fiscaldata.treasury.gov\" rel=\"noopener\">fiscaldata.treasury.gov</a>.</p>";
    return t.slice(0, at) + block + t.slice(at);
  }
  function scriptAdd(t, url) {
    if (/^\/__auth(?:\/|$)/.test(pathOf(url))) return t;
    if (t.indexOf("id=\"c107-credits\"") >= 0) return t;
    var i = t.lastIndexOf("</body>");
    if (i < 0) return t;
    var s = CSS + "<script id=\"c107-credits\">window.__c107cfg=" + cfgJson() + ";" + CLIENT + "</script>";
    return t.slice(0, i) + s + t.slice(i);
  }
  function isHtmlDoc(t) {
    var h = t.slice(0, 400).toLowerCase();
    return h.indexOf("<!doctype html") >= 0 || h.indexOf("<html") >= 0;
  }
  // "(FRED PAYEMS, UNRATE)" in reader text -> "(FRED)" + empty marker; scripts, styles, tags and attributes are left alone.
  function fredIds(t) {
    if (t.indexOf("(FRED ") < 0) return t;
    return t.replace(/<script\b[\s\S]*?<\/script\s*>|<style\b[\s\S]*?<\/style\s*>|<textarea\b[\s\S]*?<\/textarea\s*>|<[^>]*>|[^<]+/gi, function (m) {
      if (m.charAt(0) === "<") return m;
      return m.replace(/\(FRED ([A-Z0-9]+(?:, [A-Z0-9]+)*)\)/g, function (all, ids) {
        var list = ids.split(", "), i;
        for (i = 0; i < list.length; i++) if (!SERIES[list[i]]) return all;
        return "(FRED<span class=\"c107-ids\" data-c107-ids=\"" + list.join(",") + "\"></span>)";
      });
    });
  }
  function credit(t, url) {
    if (typeof t !== "string" || !t) return t;
    var out = footerAdd(t);
    if (isHtmlDoc(t) || t.indexOf("</body>") >= 0 || t.indexOf("</table>") >= 0) out = fredIds(out);
    out = methAdd(out, url);
    if (isHtmlDoc(t) || t.indexOf("</body>") >= 0) out = scriptAdd(out, url);
    return out;
  }
  try {
    var attached = [];
    if (wrapFetch()) attached.push("fetch");
    if (typeof c97Transform === "function" && !c97Transform.__c107) {
      var prevTr = c97Transform;
      var tr = function (html, req) {
        var out = prevTr.apply(this, arguments);
        try { if (typeof out === "string") out = credit(out, (req && req.url) || ""); } catch (e) { console.log("[" + TAG + "] credit failed: " + (e && e.message || e)); }
        return out;
      };
      tr.__c107 = 1;
      Object.keys(prevTr).forEach(function (k) { if (!(k in tr)) tr[k] = prevTr[k]; });
      c97Transform = tr;
      attached.push("c97Transform");
    }
    var http = null;
    try { http = typeof require === "function" ? require("http") : null; } catch (e2) { http = null; }
    var proto = http && http.ServerResponse && http.ServerResponse.prototype;
    function htmlRes(res) {
      try { var ct = typeof res.getHeader === "function" ? String(res.getHeader("content-type") || "") : ""; return !ct || /text\/html/i.test(ct); } catch (e) { return true; }
    }
    function rewrite(chunk, res, ending) {
      if (!res || !htmlRes(res)) return chunk;
      var text = null;
      if (typeof chunk === "string") text = chunk;
      else if (chunk && Buffer.isBuffer(chunk)) text = chunk.toString("utf8");
      if (!text || (text.indexOf("<footer class=\"site\"") < 0 && text.indexOf("</body>") < 0 && text.indexOf("</table>") < 0)) return chunk;
      if (res.headersSent) {
        var cl = null;
        try { cl = typeof res.getHeader === "function" ? res.getHeader("content-length") : null; } catch (e) { cl = null; }
        if (cl != null) return chunk;
      }
      var url = "";
      try { url = (res.req && res.req.url) || ""; } catch (e) { url = ""; }
      var next = credit(text, url);
      if (next === text) return chunk;
      if (!ending && !res.headersSent) { try { if (typeof res.getHeader === "function" && res.getHeader("content-length") != null) res.removeHeader("content-length"); } catch (e) {} }
      return typeof chunk === "string" ? next : Buffer.from(next);
    }
    if (proto && typeof proto.write === "function" && !proto.write.__c107) {
      var write0 = proto.write;
      var write = function (chunk, encoding, cb) {
        try { chunk = rewrite(chunk, this, false); } catch (e) { console.log("[" + TAG + "] credit failed: " + (e && e.message || e)); }
        return write0.apply(this, [chunk].concat([].slice.call(arguments, 1)));
      };
      write.__c107 = 1;
      proto.write = write;
      attached.push("res.write");
    }
    if (proto && typeof proto.end === "function" && !proto.end.__c107) {
      var end0 = proto.end;
      var end = function (chunk, encoding, cb) {
        if (chunk != null && typeof chunk !== "function") {
          var before = chunk;
          try { chunk = rewrite(chunk, this, true); } catch (e) { chunk = before; console.log("[" + TAG + "] credit failed: " + (e && e.message || e)); }
          if (chunk !== before && !this.headersSent) {
            try { this.setHeader("Content-Length", typeof chunk === "string" ? Buffer.byteLength(chunk, typeof encoding === "string" ? encoding : "utf8") : chunk.length); } catch (eL) {}
          }
        }
        return end0.apply(this, [chunk].concat([].slice.call(arguments, 1)));
      };
      end.__c107 = 1;
      proto.end = end;
      attached.push("res.end");
    }
    var t = setInterval(sweep, 6 * 3600e3);
    if (t && typeof t.unref === "function") t.unref();
    globalThis.__c107credits = { sweep: sweep, credit: credit, fredIds: fredIds, seen: seen, accessMs: accessMs, idsOfUrl: idsOfUrl, SERIES: SERIES };
    if (!attached.length) throw new Error("nothing to attach to");
    console.log("[" + TAG + "] attached");
  } catch (e) {
    console.log("[" + TAG + "] failed: " + (e && e.message || e));
  }
})();
