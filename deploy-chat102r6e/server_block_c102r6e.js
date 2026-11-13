// chat102r6c last-write scrub. Append-only. Symbol fields stay machine-readable.
(function () {
  var SOURCE_PLAIN = {
    "gold-api-spot-proxy": "gold-api.com spot price",
    "gold-api-spot-proxy-browser": "gold-api.com spot price",
    "dxy-fx-computed": "Dispatch FX basket (our calculation from Yahoo Finance FX rates)"
  };

  function ukStamp(iso) {
    var ms = Date.parse(iso);
    if (!isFinite(ms)) return iso;
    try {
      return new Intl.DateTimeFormat("en-GB", {
        timeZone: "Europe/London",
        weekday: "short",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
      }).format(new Date(ms)) + " UK";
    } catch (e) { return iso; }
  }
  function plain(s) {
    var t = String(s);
    t = t.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z/g, function (iso) { return ukStamp(iso); });
    t = t.replace(/\bgold-api-spot-proxy(?:-browser)?\b/g, "gold-api.com spot price");
    t = t.replace(/\bdxy-fx-computed\b/g, "Dispatch FX basket (our calculation from Yahoo Finance FX rates)");
    t = t.replace(/Gold futures \(GC=F, delayed (\d+) min\)/g, "Gold futures (COMEX, front month), delayed $1 min");
    t = t.replace(/gold futures \(gold futures\)/gi, "gold futures (COMEX, front month)");
    t = t.replace(/gold futures \(GC=F\)/g, "gold futures (COMEX, front month)");
    t = t.replace(/\(GC=F, delayed (\d+) min\)/g, "(COMEX, front month), delayed $1 min");
    t = t.replace(/\(GC=F\)/g, "(COMEX, front month)");
    t = t.replace(/US Dollar Index \(ICE, Yahoo DX-Y\.NYB\)/g, "US Dollar Index (ICE), Yahoo Finance");
    t = t.replace(/Yahoo Finance \(DX-Y\.NYB\)/g, "Yahoo Finance (ICE US Dollar Index)");
    t = t.replace(/Yahoo DX-Y\.NYB unavailable; this is the Dispatch FX basket/g, "Yahoo's ICE dollar index was unavailable; this is the Dispatch FX basket");
    t = t.replace(/\bGC=F\b/g, "COMEX gold futures, front month");
    t = t.replace(/Yahoo Finance \(\^TNX,\s*/g, "Yahoo Finance (");
    t = t.replace(/\(\^TNX,\s*/g, "(");
    t = t.replace(/\^TNX\b/g, "the US 10-year yield");
    t = t.replace(/Yahoo DX-Y\.NYB/g, "ICE");
    t = t.replace(/\bDX-Y\.NYB\b/g, "the ICE dollar index");
    t = t.replace(/\^VIX\b/g, "the VIX");
    t = t.replace(/\^GSPC\b/g, "the S&P 500");
    t = t.replace(/\bCL=F\b/g, "WTI crude futures");
    t = t.replace(/\bBTC-USD\b/g, "Bitcoin");
    t = t.replace(/\b([A-Z]{3})([A-Z]{3})=X\b/g, "$1/$2");
    t = t.replace(/\b([A-Z]{3})=X\b/g, "USD/$1");
    t = t.replace(/Gold futures \(gold futures, delayed (\d+) min\)/gi, "Gold futures (COMEX, front month), delayed $1 min");
    t = t.replace(/Gold futures \(COMEX gold futures, front month, delayed (\d+) min\)/g, "Gold futures (COMEX, front month), delayed $1 min");
    t = t.replace(/US Dollar Index \(ICE, Yahoo the ICE dollar index\)/g, "US Dollar Index (ICE), Yahoo Finance");
    t = t.replace(/US Dollar Index \(ICE, ICE\)/g, "US Dollar Index (ICE), Yahoo Finance");
    t = t.replace(/Yahoo Finance \(the ICE dollar index\)/g, "Yahoo Finance (ICE US Dollar Index)");
    t = t.replace(/Yahoo the ICE dollar index unavailable; this is the Dispatch FX basket/g, "Yahoo's ICE dollar index was unavailable; this is the Dispatch FX basket");
    t = t.replace(/(gold futures \(COMEX, front month\)) -(\d)/gi, "$1 −$2");
    t = t.replace(/\(\s*,\s*/g, "(").replace(/\(\s*\)/g, "").replace(/ {2,}/g, " ").trim();
    return t;
  }
  function skipKey(key) {
    return key === "symbol" || key === "symbols" || /(?:Id|Url|Key|Code)$/.test(String(key || ""));
  }
  function scrub(value, key) {
    if (typeof value === "string") return skipKey(key) ? value : plain(value);
    if (Array.isArray(value)) return value.map(function (item) { return scrub(item, key); });
    if (!value || typeof value !== "object") return value;
    var out = {};
    Object.keys(value).forEach(function (k) {
      if (k === "source" && typeof value.source === "string" && SOURCE_PLAIN[value.source] && !value.sourceId) {
        out.sourceId = value.source;
        out.source = SOURCE_PLAIN[value.source];
        return;
      }
      out[k] = scrub(value[k], k);
    });
    return out;
  }
  function interesting(text) {
    return text.indexOf("displayChange") >= 0 || text.indexOf("US10Y") >= 0 || text.indexOf("\"spot\"") >= 0 || text.indexOf("cacheState") >= 0 || text.indexOf("cacheNote") >= 0 || text.indexOf("XAU") >= 0 || text.indexOf("fallbackReason") >= 0;
  }
  function quoteOrTerminal(body) {
    if (!body || typeof body !== "object" || Array.isArray(body)) return false;
    if (body.XAU || body.US10Y || body.DXY) return true;
    if (body.spot || body.cacheState === "cold" || body.cacheState === "fresh" || body.cacheState === "stale" || body.cacheNote) return true;
    return false;
  }
  function rewriteChunk(chunk) {
    var text = null;
    if (typeof chunk === "string") text = chunk;
    else if (chunk && typeof Buffer !== "undefined" && Buffer.isBuffer(chunk)) text = chunk.toString("utf8");
    if (!text || text.charAt(0) !== "{" || !interesting(text)) return chunk;
    var obj;
    try { obj = JSON.parse(text); } catch (e) { return chunk; }
    if (!quoteOrTerminal(obj)) return chunk;
    var next = JSON.stringify(scrub(obj));
    if (typeof chunk === "string") return next;
    return Buffer.from(next);
  }
  try {
    var attached = [];
    if (typeof bb8oShape === "function" && !bb8oShape.__c102r6c) {
      var prevShape = bb8oShape;
      var shape = function () {
        var out = prevShape.apply(this, arguments);
        if (quoteOrTerminal(out)) return scrub(out);
        return out;
      };
      shape.__c102r6c = 1;
      bb8oShape = shape;
      try { globalThis.bb8oShape = shape; } catch (e1) {}
      attached.push("bb8oShape");
    }
    var http = null;
    try { http = typeof require === "function" ? require("http") : null; } catch (e2) { http = null; }
    var proto = http && http.ServerResponse && http.ServerResponse.prototype;
    if (proto && typeof proto.end === "function" && !proto.end.__c102r6c) {
      var end0 = proto.end;
      var end = function (chunk, encoding, cb) {
        try { chunk = rewriteChunk(chunk); } catch (e3) { console.log("[c102r6c] scrub failed: " + (e3 && e3.message || e3)); }
        if (typeof encoding === "function") return end0.call(this, chunk, encoding);
        if (encoding === undefined) return end0.call(this, chunk, cb);
        return end0.call(this, chunk, encoding, cb);
      };
      end.__c102r6c = 1;
      proto.end = end;
      attached.push("res.end");
    }
    if (!attached.length) throw new Error("neither bb8oShape nor res.end could be wrapped");
    console.log("[c102r6c] scrub attached");
  } catch (e) {
    console.log("[c102r6c] scrub failed: " + (e && e.message || e));
  }
})();
