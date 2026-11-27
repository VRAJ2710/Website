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
  var CSS = "/* chat108saferxC: gold chart card, latest delayed quote as the main figure, last close on a secondary line. Preview only. */\nhtml.v9b #v3-gold .v10-sec{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;margin:0 0 6px;padding:7px 10px;border:1px solid var(--v-line);border-radius:10px;background:var(--v-chip);font:500 12.5px/1.4 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink2)}\nhtml.v9b #v3-gold .v10-sec b{font-weight:700;color:var(--v-ink)}\nhtml.v9b #v3-gold .v10-sec .v3-flat,html.v9b #v3-gold .v10-sec .v3-up,html.v9b #v3-gold .v10-sec .v3-down{font-weight:700}\nhtml.v9b #v3-gold .v10-main{margin:0 0 8px}\n";
  var PATCHES = [["function lag(s){return s?'<span class=\"v3-lag '+lagCls(s)+'\">'+esc(s)+'<\/span>':\"\"}","function lag(s){return s?'<span class=\"v3-lag '+lagCls(s)+'\">'+esc(s)+'<\/span>':\"\"}\n/* chat108saferxC: a figure dated before today (UK) is not labelled Delayed or Live; it is the last close */\nfunction isTodayUK(ms){return isFinite(ms)&&ms>0&&ukDate(ms)===ukDate(Date.now())}\nfunction strToday(s){var m=/\\b(\\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\b/.exec(String(s||\"\"));return !m||(Number(m[1])+\" \"+m[2])===ukDate(Date.now())}\nfunction lagFix(st,t){return /^\\s*(delayed|live)\\s*$/i.test(String(st||\"\"))&&!strToday(t)?\"Last close\":st}",1],["function src(r,extra){return 'Yahoo Finance, '+esc(extra)+' \\u00b7 as of '+esc(uk(r.t))+' '+lag(\"Delayed\")}","function src(r,extra){return 'Yahoo Finance, '+esc(extra)+' \\u00b7 as of '+esc(uk(r.t))+' '+lag(isTodayUK(r.t)?\"Delayed\":\"Last close\")}",1],["\"Cboe VIX index, delayed\"","\"Cboe VIX index\"",1],["lag(r.status||a.lag)","lag(lagFix(r.status||a.lag,a.time))",2],["' '+lag(\"Delayed\")+'<\/p><\/div>'})","' '+lag(isTodayUK(m.regularMarketTime*1000)?\"Delayed\":\"Last close\")+'<\/p><\/div>'})",1],["the big number is the latest delayed quote.","the big number is the latest delayed quote, or the last close where it is labelled so.",1],["/* 4. Gold chart (big) */\nfunction rGold(){var el=$(\"v3-gold\");if(!el)return;var c=S.gch,h=k(\"chart\",\"Gold futures (COMEX, front month) \\u00b7 last 3 months\",[\"/gold/\",\"Gold desk\"]);\n var bars=(c&&c.status===\"ok\"&&c.bars)||[];if(bars.length<10){el.innerHTML=h+empty(\"The gold futures chart isn't available just now. We'll try again in two minutes.\");return}\n function sd(d){var m=/^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(d||\"\");return m?Number(m[3])+\" \"+[\"Jan\",\"Feb\",\"Mar\",\"Apr\",\"May\",\"Jun\",\"Jul\",\"Aug\",\"Sep\",\"Oct\",\"Nov\",\"Dec\"][m[2]-1]+\" \"+m[1]:d}\n var b=bars.slice(-63),v=b.map(function(x){return x.c}),last=b[b.length-1],first=b[0],ch=(last.c/first.c-1)*100,mn=Math.min.apply(null,v),mx=Math.max.apply(null,v);\n var yq=S.y[\"GC=F\"],m=yq&&yq.chart&&yq.chart.result&&yq.chart.result[0]&&yq.chart.result[0].meta;\n h+='<div class=\"v3-bign\"><b>$'+esc(nf(last.c,1))+'<\/b><span class=\"'+cls(ch)+'\" style=\"font-weight:700\">'+esc(sg(ch,2,\"%\"))+' over 3 months<\/span><\/div>';\n h+='<p class=\"v3-src\" style=\"margin:0 0 8px\">Last completed session close, '+esc(sd(last.sessionDate))+' (New York session). Futures, not the spot price.'+(m&&isFinite(m.regularMarketPrice)?' Latest delayed futures quote: $'+esc(nf(m.regularMarketPrice,1))+', as of '+esc(uk(m.regularMarketTime*1000))+'.':\"\")+'<\/p>';\n h+='<div style=\"position:relative\">'+spark(v,640,290,true,\"var(--v-gold)\").replace('<svg ','<svg class=\"v3-big\" ')+'<\/div>';\n h+='<div class=\"v3-gends\" style=\"max-width:none\"><span>'+esc(sd(first.sessionDate))+' \\u00b7 low $'+esc(nf(mn,0))+'<\/span><span>high $'+esc(nf(mx,0))+' \\u00b7 '+esc(sd(last.sessionDate))+'<\/span><\/div>';\n var note=c.cacheState&&c.cacheState!==\"fresh\"&&c.cacheNote?\" \"+plain(c.cacheNote):\"\";\n h+='<p class=\"v3-src\">'+esc(plain(c.source||\"Yahoo Finance, delayed\"))+', daily closes of the continuous front-month series.'+esc(note)+' '+lag(c.cacheState===\"stale\"?\"Stored reading\":\"Daily bars\")+'<\/p>';\n el.innerHTML=h}\n","/* 4. Gold chart (big). chat108saferxC: the latest free delayed futures quote is the main figure (lag label, UK time); the last\n   completed close is on a secondary line. The 3-month change is measured from the first close in the window to the main figure;\n   both come from the same continuous front-month series. With no fresh quote, the close is the main figure, labelled so. */\nfunction rGold(){var el=$(\"v3-gold\");if(!el)return;var c=S.gch,h=k(\"chart\",\"Gold futures (COMEX, front month) \\u00b7 last 3 months\",[\"/gold/\",\"Gold desk\"]);\n var bars=(c&&c.status===\"ok\"&&c.bars)||[];if(bars.length<10){el.innerHTML=h+empty(\"The gold futures chart isn't available just now. We'll try again in two minutes.\");return}\n function sd(d){var m=/^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(d||\"\");return m?Number(m[3])+\" \"+[\"Jan\",\"Feb\",\"Mar\",\"Apr\",\"May\",\"Jun\",\"Jul\",\"Aug\",\"Sep\",\"Oct\",\"Nov\",\"Dec\"][m[2]-1]+\" \"+m[1]:d}\n var b=bars.slice(-63),v=b.map(function(x){return x.c}),last=b[b.length-1],first=b[0],mn=Math.min.apply(null,v),mx=Math.max.apply(null,v);\n var yq=S.y[\"GC=F\"],m=yq&&yq.chart&&yq.chart.result&&yq.chart.result[0]&&yq.chart.result[0].meta;\n var qp=m&&isFinite(m.regularMarketPrice)&&m.regularMarketPrice>0?Number(m.regularMarketPrice):null,qt=m&&isFinite(m.regularMarketTime)?m.regularMarketTime*1000:NaN;\n var lastT=Date.parse(last.timeUtc||\"\")||Date.parse((last.sessionDate||\"\")+\"T05:00:00Z\");\n var fresh=qp!=null&&isFinite(qt)&&qt>lastT+18*36e5&&(isTodayUK(qt)||Date.now()-qt<12*36e5);\n var chC=(last.c/first.c-1)*100;\n if(fresh){var chQ=(qp/first.c-1)*100;\n  h+='<div class=\"v3-bign\"><b>$'+esc(nf(qp,1))+'<\/b><span class=\"'+cls(chQ)+'\" style=\"font-weight:700\">'+esc(sg(chQ,2,\"%\"))+' over 3 months<\/span><\/div>';\n  h+='<p class=\"v3-src v10-main\">Latest delayed futures quote, as of '+esc(uk(qt))+'. Futures, not the spot price. The 3-month change runs from the '+esc(sd(first.sessionDate))+' close to this quote, on the same continuous front-month series. '+lag(\"Delayed\")+'<\/p>';\n  h+='<div class=\"v10-sec\"><span>Last completed close<\/span><b>$'+esc(nf(last.c,1))+'<\/b><span>'+esc(sd(last.sessionDate))+' (New York session)<\/span><span class=\"'+cls(chC)+'\">'+esc(sg(chC,2,\"%\"))+' close to close over 3 months<\/span>'+lag(\"Daily close\")+'<\/div>'}\n else{\n  h+='<div class=\"v3-bign\"><b>$'+esc(nf(last.c,1))+'<\/b><span class=\"'+cls(chC)+'\" style=\"font-weight:700\">'+esc(sg(chC,2,\"%\"))+' over 3 months, close to close<\/span><\/div>';\n  h+='<p class=\"v3-src v10-main\">Last completed session close, '+esc(sd(last.sessionDate))+' (New York session). Futures, not the spot price. No fresh delayed quote is available just now'+(qp!=null&&isFinite(qt)?' (the newest one we have is $'+esc(nf(qp,1))+', as of '+esc(uk(qt))+')':\"\")+'. '+lag(\"Last close\")+'<\/p>'}\n h+='<div style=\"position:relative\">'+spark(v,640,290,true,\"var(--v-gold)\").replace('<svg ','<svg class=\"v3-big\" ')+'<\/div>';\n h+='<div class=\"v3-gends\" style=\"max-width:none\"><span>'+esc(sd(first.sessionDate))+' \\u00b7 low $'+esc(nf(mn,0))+'<\/span><span>high $'+esc(nf(mx,0))+' \\u00b7 '+esc(sd(last.sessionDate))+'<\/span><\/div>';\n var note=c.cacheState&&c.cacheState!==\"fresh\"&&c.cacheNote?\" \"+plain(c.cacheNote):\"\";\n h+='<p class=\"v3-src\">'+esc(plain(c.source||\"Yahoo Finance, delayed\"))+', daily closes of the continuous front-month series'+(fresh?'; main figure: Yahoo Finance delayed quote for the same series':\"\")+'.'+esc(note)+' '+lag(c.cacheState===\"stale\"?\"Stored reading\":\"Daily bars\")+'<\/p>';\n el.innerHTML=h}\n\n",1]];
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
