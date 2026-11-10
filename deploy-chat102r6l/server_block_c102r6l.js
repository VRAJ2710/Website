// chat102r6c last-write scrub. Append-only. Symbol fields stay machine-readable.
// chat102r6h: quote routes, FRED reader labels, gold/silver asOfUk, slim install bar.
// chat102r6i: desk-quotes vendor names, scenario copy, terminal axis labels.
// chat102r6j: scenario source sentence and nothing else in this block.
// chat102r6l: complete HTML. chat97 measures Content-Length, then this scrub used to lengthen the body,
// so Node cut every r2 page inside the install script ("var d=document.ge"). Rewrite runs in
// c97Transform before that measurement, and again on res.write for the chunked shell.
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
      if (proseKey(key)) {
        var raw = String(value);
        if (raw.indexOf("FRED series DFII10") >= 0 || raw.indexOf("FRED series DTWEXBGS") >= 0) raw = plainScenario(raw);
        return plainProse(raw);
      }
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
  function plainScenario(t) {
    var s = String(t);
    s = s.replace(/FRED series DFII10/g, "10-year real yield (TIPS), FRED");
    s = s.replace(/FRED series DTWEXBGS(?: \([^)]*\))?/g, "broad trade-weighted US dollar index, FRED");
    s = s.replace(/real yield,\s*(?:<[^>]*>\s*)*10-year real yield \(TIPS\), FRED(?:\s*<\/a>)?/g, "real yield: 10-year real yield (TIPS), FRED");
    s = s.replace(/dollar,\s*(?:<[^>]*>\s*)*broad trade-weighted US dollar index, FRED(?:\s*<\/a>)?/g, "dollar: broad trade-weighted US dollar index, FRED");
    return s;
  }
  var HEADER_CSS = '<style id="c102r6l-header">@media (min-width:1024px) and (max-width:1440px){header.site .wrap,header.site .nav,header.site form.c97tg{min-width:0;max-width:100%;box-sizing:border-box}header.site .wrap{display:flex;flex-wrap:wrap;height:auto}header.site .nav{display:flex;flex-wrap:wrap;flex:1 1 auto}header.site form.c97tg{flex:0 1 auto}header.site .nav a{white-space:normal}html.c97-dark header.site .wrap,html.c97-system header.site .wrap{display:flex;flex-wrap:wrap;height:auto;min-width:0}html.c97-dark header.site .nav,html.c97-system header.site .nav{display:flex;flex-wrap:wrap;flex:1 1 auto;min-width:0}html.c97-dark header.site form.c97tg,html.c97-system header.site form.c97tg{min-width:0;max-width:100%;flex:0 1 auto}html.c97-dark header.site .nav a,html.c97-system header.site .nav a{white-space:normal}}</style>';
  var SCEN_JS = '<script id="c102r6l-scen">(function(){var Y="FRED "+"series "+"DFII10",D="FRED "+"series "+"DTWEXBGS";function fix(s){var t=String(s).split(Y).join("10-year real yield (TIPS), FRED").split(D).join("broad trade-weighted US dollar index, FRED");t=t.replace(/ \\(Federal Reserve broad dollar index\\)/g,"");t=t.replace(/real yield,\\s*10-year real yield \\(TIPS\\), FRED/g,"real yield: 10-year real yield (TIPS), FRED");t=t.replace(/dollar,\\s*broad trade-weighted US dollar index, FRED/g,"dollar: broad trade-weighted US dollar index, FRED");return t}function walk(n){if(!n||n.nodeName==="SCRIPT"||n.nodeName==="STYLE")return;if(n.nodeType===3){var v=fix(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v;return}var c=n.childNodes,i;for(i=0;i<c.length;i++)walk(c[i])}function go(){walk(document.body);var all=document.querySelectorAll("p,li,span");var i;for(i=0;i<all.length;i++){var el=all[i];if(el.querySelector&&el.querySelector("p,div,li"))continue;var raw=el.textContent||"";var next=fix(raw);if(next!==raw)el.textContent=next}}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",go);else go();try{new MutationObserver(go).observe(document.documentElement,{subtree:true,childList:true,characterData:true})}catch(e){}})();</script>';
  var CRUMB_JS = '<script id="c102r6l-crumb-js">(function(){function esc(s){return String(s).replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}function guide(){var q="";try{q=new URLSearchParams(location.search).get("guide")||""}catch(e){}if(!q)return"";var h=document.querySelector("h1");var t=h?String(h.textContent||"").replace(/\\s+/g," ").trim():"";if(t&&t!=="Dispatch Academy")return t;return String(q).replace(/[-_]+/g," ")}function paint(){if(location.pathname.indexOf("/learn")!==0)return;var nav=document.querySelector("nav.c102r6l-crumb");if(!nav){nav=document.createElement("nav");nav.className="c102r6l-crumb";nav.setAttribute("aria-label","Breadcrumb");var host=document.querySelector("main")||document.body;if(!host)return;if(host.firstChild)host.insertBefore(nav,host.firstChild);else host.appendChild(nav)}var g=guide();nav.innerHTML=\'<a href="/">Home</a> › <a href="/learn/">Dispatch Academy</a>\'+(g?" › "+esc(g):"")}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",paint);else paint();try{new MutationObserver(paint).observe(document.documentElement,{subtree:true,childList:true})}catch(e){}})();</script>';
  function htmlEsc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]; });
  }
  function learnPage(html, url) {
    var path = "", guide = "";
    try {
      var u = new URL(url || "/", "http://localhost");
      path = u.pathname || "";
      guide = u.searchParams.get("guide") || "";
    } catch (e1) {}
    var marked = path.indexOf("/learn") === 0 || /rel="canonical" href="[^"]*\/learn\/?/.test(html) || /data-public-route="learn"/.test(html);
    return { yes: marked, guide: guide };
  }
  function place(html, payload, id) {
    if (!payload || html.indexOf(id) >= 0) return html;
    if (html.indexOf("</head>") >= 0) return html.replace("</head>", payload + "</head>");
    if (html.indexOf("</body>") >= 0) return html.replace("</body>", payload + "</body>");
    return html;
  }
  function learnChrome(html, url) {
    var t = place(html, CRUMB_JS, "c102r6l-crumb-js");
    var info = learnPage(t, url);
    if (!info.yes || t.indexOf("<nav class=\"c102r6l-crumb\"") >= 0) return t;
    var title = "";
    if (info.guide) {
      var h1 = (t.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1] || "";
      h1 = h1.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
      title = h1 && h1 !== "Dispatch Academy" ? h1 : String(info.guide).replace(/[-_]+/g, " ");
    }
    var crumb = '<nav class="c102r6l-crumb" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/learn/">Dispatch Academy</a>' + (title ? " › " + htmlEsc(title) : "") + "</nav>";
    if (t.indexOf("<main") >= 0) return t.replace(/<main\b[^>]*>/, function (m) { return m + crumb; });
    if (t.indexOf("<body") >= 0) return t.replace(/<body\b[^>]*>/, function (m) { return m + crumb; });
    return t;
  }
  function headerFit(html) {
    if (html.indexOf("c102r6l-header") >= 0) return html;
    if (html.indexOf("</body>") >= 0) return html.replace("</body>", HEADER_CSS + "</body>");
    if (html.indexOf("</head>") >= 0) return html.replace("</head>", HEADER_CSS + "</head>");
    return html;
  }
  var AXIS_OLD = "    var left = bars[0].sessionDate;\n    var right = bars[bars.length - 1].sessionDate;\n    ctx.fillText(left, padL, h - 8);";
  var AXIS_NEW = "    function c102AxisDay(iso) {\n      var ms = Date.parse(String(iso || \"\") + \"T12:00:00Z\");\n      if (!isFinite(ms)) return iso;\n      try {\n        return new Intl.DateTimeFormat(\"en-GB\", { timeZone: \"Europe/London\", weekday: \"short\", day: \"numeric\", month: \"short\" }).format(new Date(ms));\n      } catch (eAxis) { return iso; }\n    }\n    var left = c102AxisDay(bars[0].sessionDate);\n    var right = c102AxisDay(bars[bars.length - 1].sessionDate);\n    ctx.fillText(left, padL, h - 8);";
  function rewriteHtml(text, url) {
    var t = plainScenario(text);
    t = headerFit(t);
    t = learnChrome(t, url);
    if (String(url || "").indexOf("/tools/scenario") >= 0 || t.indexOf("c101scen") >= 0 || t.indexOf("Model rebuilt") >= 0) {
      t = place(t, SCEN_JS, "c102r6l-scen");
    }
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
    var pageUrl = "";
    try { pageUrl = (res && res.req && res.req.url) || ""; } catch (ePage) { pageUrl = ""; }
    var htmlish = text.charAt(0) === "<" || text.indexOf("<!doctype") >= 0 || text.indexOf("<html") >= 0 || text.indexOf("c101-inst-js") >= 0 || text.indexOf(AXIS_OLD) >= 0;
    if (htmlish) {
      var html = rewriteHtml(text, pageUrl);
      if (html === text) return chunk;
      return emit(chunk, html);
    }
    if (text.charAt(0) !== "{") return chunk;
    var onQuote = pathQuote(res);
    var forceProse = text.indexOf("FRED series DFII10") >= 0 || text.indexOf("FRED series DTWEXBGS") >= 0;
    if (!onQuote && !interesting(text) && !forceProse) return chunk;
    var obj;
    try { obj = JSON.parse(text); } catch (e) { return chunk; }
    if (!onQuote && !quoteBearing(obj) && !forceProse) return chunk;
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
    if (typeof c97Transform === "function" && !c97Transform.__c102r6l) {
      var prevTr = c97Transform;
      var tr = function (html, req) {
        var out = prevTr.apply(this, arguments);
        try {
          if (typeof out === "string") out = rewriteHtml(out, (req && req.url) || "");
        } catch (eTr) { console.log("[c102r6l] scrub failed: " + (eTr && eTr.message || eTr)); }
        return out;
      };
      tr.__c102r6l = 1;
      c97Transform = tr;
      attached.push("c97Transform");
    }
    if (typeof bb8oShape === "function" && !bb8oShape.__c102r6l) {
      var prevShape = bb8oShape;
      var shape = function () {
        var out = prevShape.apply(this, arguments);
        if (quoteBearing(out)) return scrub(out, "", quoteOrTerminal(out), deskBody(out));
        return out;
      };
      shape.__c102r6l = 1;
      bb8oShape = shape;
      try { globalThis.bb8oShape = shape; } catch (e1) {}
      attached.push("bb8oShape");
    }
    var http = null;
    try { http = typeof require === "function" ? require("http") : null; } catch (e2) { http = null; }
    var proto = http && http.ServerResponse && http.ServerResponse.prototype;
    function byteLen(body) {
      if (typeof body === "string") return Buffer.byteLength(body);
      if (body && Buffer.isBuffer(body)) return body.length;
      return null;
    }
    function syncLength(res, body) {
      if (!res || res.headersSent) return;
      var n = byteLen(body);
      if (n == null || typeof res.setHeader !== "function") return;
      try { res.setHeader("Content-Length", n); } catch (eLen) {}
    }
    function grownPast(res, before, after) {
      if (before === after) return after;
      if (!res || !res.headersSent) return after;
      var cl = null;
      try { cl = typeof res.getHeader === "function" ? res.getHeader("content-length") : null; } catch (eCl) { cl = null; }
      if (cl == null) return after;
      return before;
    }
    if (proto && typeof proto.write === "function" && !proto.write.__c102r6l) {
      var write0 = proto.write;
      var write = function (chunk, encoding, cb) {
        var before = chunk;
        try { chunk = rewriteChunk(chunk, this); } catch (e5) { console.log("[c102r6l] scrub failed: " + (e5 && e5.message || e5)); chunk = before; }
        chunk = grownPast(this, before, chunk);
        if (typeof encoding === "function") return write0.call(this, chunk, encoding);
        if (encoding === undefined) return write0.call(this, chunk, cb);
        return write0.call(this, chunk, encoding, cb);
      };
      write.__c102r6l = 1;
      proto.write = write;
      attached.push("res.write");
    }
    if (proto && typeof proto.end === "function" && !proto.end.__c102r6l) {
      var end0 = proto.end;
      var end = function (chunk, encoding, cb) {
        try { chunk = rewriteChunk(chunk, this); } catch (e3) { console.log("[c102r6l] scrub failed: " + (e3 && e3.message || e3)); }
        try { syncLength(this, chunk); } catch (e4) {}
        if (typeof encoding === "function") return end0.call(this, chunk, encoding);
        if (encoding === undefined) return end0.call(this, chunk, cb);
        return end0.call(this, chunk, encoding, cb);
      };
      end.__c102r6l = 1;
      proto.end = end;
      attached.push("res.end");
    }
    if (!attached.length) throw new Error("neither bb8oShape nor res.end could be wrapped");
    console.log("[c102r6l] scrub attached");
  } catch (e) {
    console.log("[c102r6l] scrub failed: " + (e && e.message || e));
  }
})();
