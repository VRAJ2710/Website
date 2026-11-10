// chat102r6c last-write scrub. Append-only. Symbol fields stay machine-readable.
// chat102r6h: quote routes, FRED reader labels, gold/silver asOfUk, slim install bar.
// chat102r6i: desk-quotes vendor names, scenario copy, terminal axis labels.
(function () {
  var SOURCE_LABEL = {
    "gold-api-spot-proxy": "gold-api.com spot price",
    "gold-api-spot-proxy-browser": "gold-api.com spot price",
    "dxy-fx-computed": "Dispatch FX basket (our calculation from Yahoo Finance FX rates)"
  };
  var QUOTE_PATH = /\/api\/(?:desk-quotes|market-reference-quotes|yahoo-quote|real-yield|eia-spot|crypto-snapshot|session-summary|c96\/gold-spot|c97\/dgs10|c100b\/gold-change|c101f\/rates|c102\/|ext-hours|twelve-data-quote|spot-energy)(?:[\/?#]|$)/;
  var PIPE_SOURCE = /GC=F\|DX-Y\.NYB\|\^TNX/;
  var YAHOO_DESK = /Yahoo Finance \((?:GC=F|DX-Y\.NYB|\^TNX)\)/;
  var MACHINE_SOURCE = /^(?:gold-api-spot-proxy(?:-browser)?|dxy-fx-computed|dxy-computed|frankfurter-ecb|open-exchange-rate-api)$/;

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
  function plainR6d(s) {
    var t = String(s);
    t = t.replace(/Gold futures \(GC=F, delayed (\d+) min\)/g, "Gold futures (COMEX, front month), delayed $1 min");
    t = t.replace(/gold futures \(GC=F\)/g, "gold futures (COMEX, front month)");
    t = t.replace(/\(GC=F, delayed (\d+) min\)/g, "(COMEX, front month), delayed $1 min");
    t = t.replace(/\(GC=F\)/g, "(COMEX, front month)");
    t = t.replace(/US Dollar Index \(ICE, Yahoo DX-Y\.NYB\)/g, "US Dollar Index (ICE), Yahoo Finance");
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
    t = t.replace(/Yahoo the ICE dollar index unavailable; this is the Dispatch FX basket/g, "Yahoo's ICE dollar index was unavailable; this is the Dispatch FX basket");
    t = t.replace(/\(\s*,\s*/g, "(").replace(/\(\s*\)/g, "").replace(/ {2,}/g, " ").trim();
    return t;
  }
  function plainFred(s) {
    var t = String(s);
    t = t.replace(/US Treasury via FRED \(DFII10\)(?:, [^.]*)?/g, "FRED, US 10-year real yield (TIPS)");
    t = t.replace(/US Treasury via FRED \(DGS10\)(?:, [^.]*)?/g, "FRED, US 10-year Treasury yield");
    t = t.replace(/\bDFII10\b/g, "US 10-year real yield (TIPS)");
    t = t.replace(/\bDGS10\b/g, "US 10-year Treasury yield");
    t = t.replace(/\bCPIAUCSL\b/g, "US CPI");
    t = t.replace(/\bCPILFESL\b/g, "US core CPI");
    t = t.replace(/\bPCEPI\b/g, "US PCE price index");
    t = t.replace(/\bPAYEMS\b/g, "US nonfarm payrolls");
    return t;
  }
  function fredSource(s) {
    var t = String(s);
    if (/\bDFII10\b/.test(t) && /\bDGS10\b/.test(t)) return plainFred(t);
    if (/\bDFII10\b/.test(t)) return "FRED, US 10-year real yield (TIPS)";
    if (/\bDGS10\b/.test(t)) return "FRED, US 10-year Treasury yield";
    return null;
  }
  function plainProse(s) {
    var t = String(s).replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z/g, function (iso) { return ukStamp(iso); });
    t = plainR6d(t);
    t = plainFred(t);
    t = t.replace(/Yahoo Finance \(the ICE dollar index\)/g, "Yahoo Finance (ICE US Dollar Index)");
    t = t.replace(/gold futures \(gold futures\)/gi, "gold futures (COMEX, front month)");
    t = t.replace(/(gold futures \(COMEX, front month\)) -(\d)/gi, "$1 −$2");
    t = t.replace(/Gold futures \(COMEX, front month\), delayed (\d+) min/g, "Gold futures (COMEX, front month, delayed $1 min)");
    t = t.replace(/\bSI=F\b/g, "COMEX silver futures");
    t = t.replace(/\bgold-api-spot-proxy-browser\b/g, "gold-api.com spot price");
    t = t.replace(/\bgold-api-spot-proxy\b/g, "gold-api.com spot price");
    t = t.replace(/\bdxy-fx-computed\b/g, "Dispatch FX basket");
    return t;
  }
  function r6dReads(key) {
    return /label|note|text|source|name|narrative|method|basis|title|summary|plain|kicker|reason/i.test(String(key || ""));
  }
  function proseKey(key) {
    var k = String(key || "");
    return /^(note|cacheNote|statusNote|text|label|detail|message|caption|description)$/.test(k) || /(?:Note|Text|Label)$/.test(k);
  }
  function quoteOrTerminal(body) {
    if (!body || typeof body !== "object" || Array.isArray(body)) return false;
    if (body.XAU || body.US10Y || body.DXY) return true;
    if (body.spot || body.cacheState === "cold" || body.cacheState === "fresh" || body.cacheState === "stale" || body.cacheNote || body.generatedAtUtc) return true;
    return false;
  }
  function quoteBearing(body) {
    if (!body || typeof body !== "object" || Array.isArray(body)) return false;
    if (quoteOrTerminal(body)) return true;
    if (body.quotes && typeof body.quotes === "object") return true;
    if (body.displayChange || body.displayChangeLabel) return true;
    if (body.ratio && typeof body.ratio === "object" && body.ratio.asOfUtc) return true;
    if (body.series && /^(DGS10|DFII10)$/.test(String(body.series))) return true;
    if ((body.price != null || body.p != null || body.value != null) && (body.symbol || body.label || body.source || body.displayChange)) return true;
    var keys = Object.keys(body);
    for (var i = 0; i < keys.length; i++) {
      if (/^(XAU|DXY|TNX|US10Y|SLV|WTI|VIX|BTC|ETH|GBPUSD|EURUSD)$/.test(keys[i]) && body[keys[i]] && typeof body[keys[i]] === "object") return true;
    }
    return false;
  }
  function yahooDeskSource(s) {
    return YAHOO_DESK.test(String(s || "")) || PIPE_SOURCE.test(String(s || ""));
  }
  function machineSource(s) {
    return MACHINE_SOURCE.test(String(s || ""));
  }
  function deskBody(body) {
    return !!(body && typeof body === "object" && !Array.isArray(body) && body.quotes && typeof body.quotes === "object" && !body.generatedAtUtc && !body.XAU && !body.US10Y);
  }
  function deskInstrument(obj) {
    var sym = "";
    var src = "";
    if (obj && typeof obj === "object") {
      sym = String(obj.symbol || obj.ticker || (obj.displayChange && obj.displayChange.symbol) || "");
      src = String(obj.source || "");
    }
    var blob = sym + " " + src;
    if (PIPE_SOURCE.test(src)) return "Yahoo Finance";
    if (/GC=F/.test(blob)) return "Gold futures (COMEX, front month), Yahoo Finance";
    if (/DX-Y\.NYB/.test(blob)) return "ICE US Dollar Index, Yahoo Finance";
    if (/\^TNX/.test(blob) || sym === "TNX" || sym === "US10Y") return "CBOE 10-year Treasury yield index, Yahoo Finance";
    return "Yahoo Finance";
  }
  function ratioObject(obj, key) {
    if (!obj || typeof obj !== "object" || !obj.asOfUtc) return false;
    if (key === "ratio") return true;
    return !!(obj.numerator && obj.denominator && obj.value != null);
  }
  function scrub(value, key, legacy, desk) {
    if (typeof value === "string") {
      if (proseKey(key)) return plainProse(value);
      if (key === "source") {
        var fred = fredSource(value);
        if (fred) return fred;
        if (desk && yahooDeskSource(value) && !machineSource(value)) return "Yahoo Finance";
        if (legacy) return plainR6d(value);
        return value;
      }
      if (legacy && r6dReads(key)) return plainR6d(value);
      return value;
    }
    if (Array.isArray(value)) return value.map(function (item) { return scrub(item, key, legacy, desk); });
    if (!value || typeof value !== "object") return value;
    var out = {};
    Object.keys(value).forEach(function (k) { out[k] = scrub(value[k], k, legacy, desk); });
    if (key === "DXY") out.sourceLabel = "Yahoo Finance, ICE US Dollar Index";
    else if (key === "US10Y") {
      out.sourceLabel = "Yahoo Finance, CBOE 10-year Treasury yield index";
      if (typeof value.note === "string" && /percent|Show the %/i.test(value.note)) out.note = "Yield in percent.";
    } else if (typeof value.source === "string" && SOURCE_LABEL[value.source] && out.sourceLabel == null) {
      out.sourceLabel = SOURCE_LABEL[value.source];
    }
    if (typeof value.source === "string" && PIPE_SOURCE.test(value.source) && !desk) out.sourceLabel = "Yahoo Finance";
    if (desk && typeof value.source === "string" && yahooDeskSource(value.source) && !machineSource(value.source)) out.sourceLabel = deskInstrument(value);
    if (ratioObject(value, key) && !out.asOfUk) out.asOfUk = ukStamp(value.asOfUtc);
    return out;
  }
  function interesting(text) {
    return text.indexOf("displayChange") >= 0 || text.indexOf("US10Y") >= 0 || text.indexOf("\"spot\"") >= 0 || text.indexOf("cacheState") >= 0 || text.indexOf("cacheNote") >= 0 || text.indexOf("XAU") >= 0 || text.indexOf("fallbackReason") >= 0 || text.indexOf("generatedAtUtc") >= 0 || text.indexOf("DGS10") >= 0 || text.indexOf("DFII10") >= 0 || text.indexOf("\"quotes\"") >= 0 || text.indexOf("GC=F") >= 0 || text.indexOf("asOfUtc") >= 0 || text.indexOf("desk-quotes") >= 0;
  }
  function pathQuote(res) {
    var url = "";
    try { url = (res && res.req && res.req.url) || ""; } catch (e) { url = ""; }
    return QUOTE_PATH.test(String(url));
  }
  var AXIS_OLD = "    var left = bars[0].sessionDate;\n    var right = bars[bars.length - 1].sessionDate;\n    ctx.fillText(left, padL, h - 8);";
  var AXIS_NEW = "    function c102AxisDay(iso) {\n      var ms = Date.parse(String(iso || \"\") + \"T12:00:00Z\");\n      if (!isFinite(ms)) return iso;\n      try {\n        return new Intl.DateTimeFormat(\"en-GB\", { timeZone: \"Europe/London\", weekday: \"short\", day: \"numeric\", month: \"short\" }).format(new Date(ms));\n      } catch (eAxis) { return iso; }\n    }\n    var left = c102AxisDay(bars[0].sessionDate);\n    var right = c102AxisDay(bars[bars.length - 1].sessionDate);\n    ctx.fillText(left, padL, h - 8);";
  function rewriteHtml(text) {
    var t = String(text);
    if (t.indexOf("FRED series DFII10") >= 0) t = t.replace(/>FRED series DFII10</g, ">10-year real yield (TIPS), FRED<");
    if (t.indexOf("FRED series DTWEXBGS") >= 0) {
      t = t.replace(/>FRED series DTWEXBGS \(Federal Reserve broad dollar index\)</g, ">Broad trade-weighted US dollar index, FRED<");
      t = t.replace(/>FRED series DTWEXBGS</g, ">Broad trade-weighted US dollar index, FRED<");
    }
    if (t.indexOf(AXIS_OLD) >= 0) t = t.replace(AXIS_OLD, AXIS_NEW);
    if (t.indexOf("c101-inst") < 0) return t;
    var cssOld = "#c101-inst{position:fixed;left:12px;right:12px;bottom:12px;z-index:2147482000;max-width:560px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#fff;color:#1b1b1b;border:1px solid #c9c4b8;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:12px 14px;font:14px/1.45 Inter,system-ui,sans-serif}#c101-inst span{flex:1 1 220px}#c101-inst button{min-height:40px;padding:0 14px;border-radius:6px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}";
    var cssNew = "#c101-inst{position:fixed;left:0;right:0;bottom:0;z-index:20;max-width:none;max-height:40px;margin:0;display:flex;flex-wrap:nowrap;gap:8px;align-items:center;background:#fff;color:#1b1b1b;border:0;border-top:1px solid #c9c4b8;border-radius:0;box-shadow:none;padding:4px 10px;font:13px/1.3 Inter,system-ui,sans-serif;overflow:hidden}#c101-inst span{flex:1 1 auto;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#c101-inst button{min-height:32px;padding:0 10px;border-radius:6px;font:600 13px Inter,system-ui,sans-serif;cursor:pointer}body:has(#c101-inst){padding-bottom:44px}";
    if (t.indexOf(cssOld) >= 0) t = t.replace(cssOld, cssNew);
    var whenOld = "if(!/[?&]source=pwa/.test(location.search))setTimeout(bar,4000)";
    var whenNew = "if(!/[?&]source=pwa/.test(location.search)){var n=1;try{n=(+localStorage.getItem(\"c101-install-visits\")||0)+1;localStorage.setItem(\"c101-install-visits\",String(n))}catch(err){}if(n>=2)bar();else setTimeout(bar,30000)}";
    if (t.indexOf(whenOld) >= 0) t = t.replace(whenOld, whenNew);
    var guard = "if(!window.__c102r6hFetch){window.__c102r6hFetch=1;var _f=window.fetch;if(typeof _f===\"function\"){window.fetch=function(input,init){var u=\"\";try{u=typeof input===\"string\"?input:(input&&input.url)||\"\"}catch(e0){}if(String(u).indexOf(\"/api/c98/alerts\")>=0&&window._userSignedIn!==true){return Promise.resolve(new Response(\"\",{status:204}))}return _f.apply(this,arguments)}}}";
    var mark = "window.__c101i=1;";
    if (t.indexOf(mark) >= 0 && t.indexOf("__c102r6hFetch") < 0) t = t.replace(mark, mark + guard);
    return t;
  }
  function emit(chunk, next) {
    if (typeof chunk === "string") return next;
    return Buffer.from(next);
  }
  function rewriteChunk(chunk, res) {
    var text = null;
    if (typeof chunk === "string") text = chunk;
    else if (chunk && typeof Buffer !== "undefined" && Buffer.isBuffer(chunk)) text = chunk.toString("utf8");
    if (!text) return chunk;
    if (text.charAt(0) === "<" || text.indexOf("c101-inst-js") >= 0 || text.indexOf("FRED series DFII10") >= 0 || text.indexOf(AXIS_OLD) >= 0) {
      var html = rewriteHtml(text);
      if (html === text) return chunk;
      return emit(chunk, html);
    }
    if (text.charAt(0) !== "{") return chunk;
    var onQuote = pathQuote(res);
    if (!onQuote && !interesting(text)) return chunk;
    var obj;
    try { obj = JSON.parse(text); } catch (e) { return chunk; }
    if (!onQuote && !quoteBearing(obj)) return chunk;
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return chunk;
    var url = "";
    try { url = (res && res.req && res.req.url) || ""; } catch (eUrl) { url = ""; }
    var desk = /\/api\/desk-quotes(?:[\/?#]|$)/.test(url) || (!/\/api\/market-reference-quotes/.test(url) && deskBody(obj));
    var legacy = quoteOrTerminal(obj);
    var next = JSON.stringify(scrub(obj, "", legacy, desk));
    return emit(chunk, next);
  }
  try {
    var attached = [];
    if (typeof bb8oShape === "function" && !bb8oShape.__c102r6i) {
      var prevShape = bb8oShape;
      var shape = function () {
        var out = prevShape.apply(this, arguments);
        if (quoteBearing(out)) return scrub(out, "", quoteOrTerminal(out), deskBody(out));
        return out;
      };
      shape.__c102r6i = 1;
      bb8oShape = shape;
      try { globalThis.bb8oShape = shape; } catch (e1) {}
      attached.push("bb8oShape");
    }
    var http = null;
    try { http = typeof require === "function" ? require("http") : null; } catch (e2) { http = null; }
    var proto = http && http.ServerResponse && http.ServerResponse.prototype;
    if (proto && typeof proto.end === "function" && !proto.end.__c102r6i) {
      var end0 = proto.end;
      var end = function (chunk, encoding, cb) {
        try { chunk = rewriteChunk(chunk, this); } catch (e3) { console.log("[c102r6i] scrub failed: " + (e3 && e3.message || e3)); }
        if (typeof encoding === "function") return end0.call(this, chunk, encoding);
        if (encoding === undefined) return end0.call(this, chunk, cb);
        return end0.call(this, chunk, encoding, cb);
      };
      end.__c102r6i = 1;
      proto.end = end;
      attached.push("res.end");
    }
    if (!attached.length) throw new Error("neither bb8oShape nor res.end could be wrapped");
    console.log("[c102r6i] scrub attached");
  } catch (e) {
    console.log("[c102r6i] scrub failed: " + (e && e.message || e));
  }
})();
