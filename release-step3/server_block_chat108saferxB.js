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
  var CSS = "/* chat108saferxB: v3 home preview, batch B (split story, prices and mood strip, chart band, 1-2-3, market colours and icons, Full table disclosure). Scoped to html.v8a.v9b; preview only. */\nhtml.v9b{--mk-gold:#8a6312;--mk-dollar:#1f5fbf;--mk-yields:#6a3fcf;--mk-oil:#a3195b;--mk-crypto:#a8420c;--mk-equities:#0b6e66}\nhtml.v9b.c97-dark,html.v9b[data-theme=\"dark\"]{--mk-gold:#e6b95e;--mk-dollar:#7aa8ff;--mk-yields:#b69cff;--mk-oil:#f58fbf;--mk-crypto:#ff9b5e;--mk-equities:#3fd2c4}\n@media (prefers-color-scheme:dark){html.v9b.c97-system,html.v9b:not(.c97-light):not(.c97-dark):not([data-theme=\"light\"]):not([data-theme=\"dark\"]){--mk-gold:#e6b95e;--mk-dollar:#7aa8ff;--mk-yields:#b69cff;--mk-oil:#f58fbf;--mk-crypto:#ff9b5e;--mk-equities:#3fd2c4}}\nhtml.v9b [data-mk=\"gold\"]{--mk:var(--mk-gold)}html.v9b [data-mk=\"dollar\"]{--mk:var(--mk-dollar)}html.v9b [data-mk=\"yields\"]{--mk:var(--mk-yields)}\nhtml.v9b [data-mk=\"oil\"]{--mk:var(--mk-oil)}html.v9b [data-mk=\"crypto\"]{--mk:var(--mk-crypto)}html.v9b [data-mk=\"equities\"]{--mk:var(--mk-equities)}\n/* section rhythm: small kickers, no big type below the hero */\nhtml.v9b .v9-sec{margin:22px 0 0}\nhtml.v9b .v9-hdrow{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 16px;margin:0 0 10px}\nhtml.v9b .v9-hd{display:flex;align-items:center;gap:10px;font:700 12px/1.3 \"DM Sans\",Inter,system-ui,sans-serif!important;letter-spacing:.14em;text-transform:uppercase;color:var(--v-ink3)!important;margin:0 0 10px!important}\nhtml.v9b .v9-hdrow .v9-hd{margin:0!important}\nhtml.v9b .v9-hd::after{content:\"\";flex:1 1 40px;min-width:24px;height:1px;background:var(--v-line2)}\nhtml.v9b .v9 .v3-s2,html.v9b .v9 .v3-s3{grid-column:auto}\n/* 2. split story: sticky left (gold chart, fits under the header and tabs), right scrolls (snapshot, events, what moved).\n   One flat grid so the reading and phone order is snapshot, chart, events, moved. */\nhtml.v9b .v9-split{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}\n@media (min-width:1000px){\nhtml.v9b .v9-split{grid-template-columns:minmax(0,5fr) minmax(0,7fr);align-items:start}\nhtml.v9b .v9-split>#v3-snap,html.v9b .v9-split>#v3-cal,html.v9b .v9-split>#v3-moves{grid-column:2}\nhtml.v9b .v9-split>#v3-snap{grid-row:1}html.v9b .v9-split>#v3-cal{grid-row:2}html.v9b .v9-split>#v3-moves{grid-row:3}\nhtml.v9b .v9-split>#v3-gold{grid-column:1;grid-row:1/span 3;align-self:start;position:sticky;top:var(--v9-top,120px)}\n}\n/* price and gauge strip */\nhtml.v9b .v9-strip{display:grid;grid-template-columns:minmax(0,1fr);gap:12px}\n@media (min-width:1000px){html.v9b .v9-strip{grid-template-columns:minmax(0,7fr) minmax(0,5fr);align-items:start}}\nhtml.v9b .v9-strip .v3-prices{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}\n@media (max-width:600px){html.v9b .v9-strip .v3-prices{grid-template-columns:repeat(2,minmax(0,1fr))}}\nhtml.v9b .v3-pt{position:relative;border-top:3px solid var(--mk,var(--v-line2))!important}\nhtml.v9b .v3-pt .n,html.v9b .v3-tile .n{display:flex;align-items:flex-start;gap:6px;color:var(--v-ink2)}\nhtml.v9b .v9-mi{flex:0 0 auto;display:inline-grid;place-items:center;width:18px;height:18px;border-radius:6px;color:var(--mk);background:color-mix(in srgb,var(--mk) 14%,transparent)}\nhtml.v9b .v9-mi svg{width:12px;height:12px;fill:none;stroke:currentColor;stroke-width:2.1;stroke-linecap:round;stroke-linejoin:round}\nhtml.v9b .v3-ul li b .v9-mi{display:inline-grid;vertical-align:-3px;margin-right:5px}\nhtml.v9b .v9-legend{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}\nhtml.v9b .v9-legend li{display:inline-flex;align-items:center;gap:5px;padding:4px 9px 4px 5px;border-radius:999px;border:1px solid var(--v-line);background:var(--v-chip);font:600 12px/1.2 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--mk)}\nhtml.v9b #v3-gold .v3-k svg{color:var(--mk-gold)}\nhtml.v9b #v3-gold .v3-bign b{font-size:28px}\n/* chart band */\nhtml.v9b .v3-tile{border-top:3px solid var(--mk,var(--v-line2))!important}\n@media (min-width:1000px){html.v9b #v9-charts .v3-tiles{grid-template-columns:repeat(3,minmax(0,1fr))}html.v9b #v9-charts .v3-tile svg{height:72px}}\n/* 1-2-3 */\nhtml.v9b .v9-steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:minmax(0,1fr);gap:12px;counter-reset:v9s}\n@media (min-width:760px){html.v9b .v9-steps{grid-template-columns:repeat(3,minmax(0,1fr))}}\nhtml.v9b .v9-steps li{counter-increment:v9s;display:grid;grid-template-columns:34px minmax(0,1fr);gap:4px 12px;align-items:start}\nhtml.v9b .v9-steps li::before{content:counter(v9s);grid-row:1/span 3;width:34px;height:34px;border-radius:12px;display:grid;place-items:center;font:700 15px/1 \"DM Sans\",Inter,system-ui,sans-serif;color:#1a1305;background:linear-gradient(180deg,#f0c66d,#d9a441)}\nhtml.v9b .v9-steps .v9-sk{font:700 11px/1.3 \"DM Sans\",Inter,system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--v-ink3);margin:0}\nhtml.v9b .v9-steps h3{font:700 16px/1.3 \"DM Sans\",Inter,system-ui,sans-serif;margin:0;color:var(--v-ink)}\nhtml.v9b .v9-steps p{font-size:13.5px;line-height:1.45;color:var(--v-ink2);margin:0}\nhtml.v9b .v9-steps a{color:var(--v-gold)!important}\n/* Full table: the old market-context table, collapsed, nothing deleted */\nhtml.v9b details.v9-full{border:1px solid var(--v-line);border-radius:14px;background:var(--v-chip);padding:0}\nhtml.v9b details.v9-full>summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:44px;padding:10px 14px;font:700 13px/1.3 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink)}\nhtml.v9b details.v9-full>summary::-webkit-details-marker{display:none}\nhtml.v9b details.v9-full>summary::after{content:\"\";width:8px;height:8px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;transform:rotate(45deg);margin-top:-4px;flex:0 0 auto}\nhtml.v9b details.v9-full[open]>summary::after{transform:rotate(-135deg);margin-top:4px}\nhtml.v9b details.v9-full>summary:focus-visible{outline:2px solid var(--v8-ring,currentColor);outline-offset:2px;border-radius:14px}\nhtml.v9b details.v9-full>[data-need]{padding:0 14px 12px;overflow-x:auto}\nhtml.v9b details.v9-full .v9-fs{font:400 12px/1.3 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink3)}\nhtml.v9b details.v9-full:has(>[data-need][hidden]){display:none}\n/* hero headline centring (site h1 rules cap its width and left-align it) */\nhtml.v9b .v8-hero h1{max-width:none!important;width:100%;margin-left:auto!important;margin-right:auto!important;text-align:center!important}\nhtml.v9b .v8-hero h1 span{margin-left:auto;margin-right:auto;text-align:center}\nhtml.v9b .v9-hdrow .v9-hd{flex:1 1 220px;white-space:nowrap}\nhtml.v9b #c93top .grid{align-items:start}\n";
  var JS = "/* chat108saferxB: market colours and icons on the existing v3 cards, bitcoin and WTI from the existing market-context table\n   into the key-price strip, and the sticky offset for the split story. No network, no storage; reads only the page. */\n(function(){\n\"use strict\";\nif(window.__v9b)return;window.__v9b=1;\nvar D=document;\nvar IC={gold:'<path d=\"M3 19h18l-2.5-6h-13z\"/><path d=\"M7.5 13 9.5 7h5l2 6\"/>',\ndollar:'<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M14.6 9.2c-.5-1-1.5-1.5-2.8-1.5-1.5 0-2.6.8-2.6 2s1.1 1.7 2.7 2c1.7.3 2.8.9 2.8 2.2s-1.2 2.1-2.8 2.1c-1.3 0-2.4-.6-2.9-1.6M12 6v1.7M12 16.3V18\"/>',\nyields:'<path d=\"M19 5 5 19\"/><circle cx=\"7\" cy=\"7\" r=\"2.3\"/><circle cx=\"17\" cy=\"17\" r=\"2.3\"/>',\noil:'<path d=\"M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z\"/>',\ncrypto:'<path d=\"M12 2.8 20 7.4v9.2L12 21.2 4 16.6V7.4z\"/><path d=\"M10 8.5h3a1.75 1.75 0 0 1 0 3.5h-3zm0 3.5h3.5a1.75 1.75 0 0 1 0 3.5H10zM10 8.5v7\"/>',\nequities:'<path d=\"M7 4v16M17 4v16\"/><rect x=\"5\" y=\"8\" width=\"4\" height=\"7\" rx=\"1\"/><rect x=\"15\" y=\"6\" width=\"4\" height=\"9\" rx=\"1\"/>'};\nfunction mk(t){t=String(t||\"\").toLowerCase();\n if(/gold|silver|platinum/.test(t))return\"gold\";\n if(/bitcoin|ether|crypto|solana/.test(t))return\"crypto\";\n if(/crude|brent|wti|oil|natural gas/.test(t))return\"oil\";\n if(/yield|treasury|gilt|bank rate/.test(t))return\"yields\";\n if(/dollar|pound|euro|yen|sterling/.test(t))return\"dollar\";\n if(/s&p|s&amp;p|nasdaq|dow|ftse|stock|equit|index \\(context\\)|vix/.test(t))return\"equities\";\n return\"\";}\nfunction icon(m){var s=D.createElement(\"span\");s.className=\"v9-mi\";s.setAttribute(\"aria-hidden\",\"true\");s.innerHTML='<svg viewBox=\"0 0 24 24\">'+IC[m]+\"<\/svg>\";return s}\nfunction tagEl(el,nameEl){if(!el||!nameEl)return;var m=mk(nameEl.textContent);if(!m)return;if(el.getAttribute(\"data-mk\")!==m)el.setAttribute(\"data-mk\",m);if(!nameEl.querySelector(\".v9-mi\"))nameEl.insertBefore(icon(m),nameEl.firstChild)}\nfunction tagAll(){\n Array.prototype.forEach.call(D.querySelectorAll(\"#v3-prices .v3-pt,#v3-tiles .v3-tile\"),function(t){tagEl(t,t.querySelector(\".n\"))});\n Array.prototype.forEach.call(D.querySelectorAll(\"#v3-moves .v3-ul li\"),function(li){var b=li.querySelector(\"b\");if(b)tagEl(li,b)});\n var g=D.getElementById(\"v3-gold\");if(g&&!g.getAttribute(\"data-mk\"))g.setAttribute(\"data-mk\",\"gold\");}\n/* bitcoin and WTI: copied (text only) from the existing market-context table rows, with their own source, time and lag */\nfunction lagOf(s){s=String(s||\"\");return /stale|stored/i.test(s)?[\"Stale\",\"st\"]:/official daily|EIA/i.test(s)?[\"Official daily\",\"ok\"]:/last close|closed/i.test(s)?[\"Last close\",\"\"]:/delayed/i.test(s)?[\"Delayed\",\"ok\"]:/live/i.test(s)?[\"Live\",\"ok\"]:[\"Delay not stated\",\"\"]}\nfunction extraRows(){var out=[],tb=D.querySelector(\"#c93top table.ctx tbody\");if(!tb)return out;\n Array.prototype.forEach.call(tb.querySelectorAll(\"tr\"),function(tr){var td=tr.children;if(td.length<4)return;\n  var c0=td[0].cloneNode(true);Array.prototype.forEach.call(c0.querySelectorAll(\".msrc\"),function(x){x.remove()});var name=c0.textContent.replace(/\\s+/g,\" \").trim();\n  var key=/^bitcoin/i.test(name)?\"btc\":/^wti/i.test(name)?\"wti\":\"\";if(!key)return;\n  var lvl=td[1].textContent.trim();if(!lvl)return;\n  var src=\"\";for(var i=0;i<td[3].childNodes.length;i++){var n=td[3].childNodes[i];if(n.nodeType===3)src+=n.nodeValue}src=src.replace(/\\s+/g,\" \").trim()||td[3].textContent.trim();\n  out.push({key:key,name:name,lvl:lvl,chg:td[2].textContent.trim(),dir:/\\bup\\b/.test(td[2].className)?\"v3-up\":/\\bdown\\b/.test(td[2].className)?\"v3-down\":\"v3-flat\",src:src})});\n return out}\nfunction el(tag,cls,txt){var e=D.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}\nfunction addExtras(){var grid=D.querySelector(\"#v3-prices .v3-prices\");if(!grid)return;\n Array.prototype.forEach.call(grid.querySelectorAll(\"[data-v9x]\"),function(x){x.remove()});\n var have=Array.prototype.map.call(grid.querySelectorAll(\".v3-pt .n\"),function(n){return n.textContent.toLowerCase()}).join(\"|\");\n extraRows().forEach(function(r){if(r.key===\"btc\"&&/bitcoin/.test(have))return;if(r.key===\"wti\"&&/wti/.test(have))return;\n  var t=el(\"div\",\"v3-pt\");t.setAttribute(\"data-v9x\",r.key);t.appendChild(el(\"div\",\"n\",r.name));t.appendChild(el(\"div\",\"v\",r.lvl));\n  t.appendChild(el(\"span\",\"c \"+(r.chg?r.dir:\"v3-flat\"),r.chg||\"No change figure\"));\n  var p=el(\"p\",\"v3-src\",r.src+\" \");var lg=lagOf(r.src);p.appendChild(el(\"span\",\"v3-lag \"+lg[1],lg[0]));t.appendChild(p);grid.appendChild(t)});}\nvar busy=false,mo=null,WATCH=[\"v3-prices\",\"v3-tiles\",\"v3-moves\",\"v3-gold\"];\nfunction run(){if(busy)return;busy=true;if(mo)mo.disconnect();try{addExtras();tagAll()}catch(e){}observe();busy=false}\nfunction observe(){if(!mo)return;WATCH.forEach(function(id){var x=D.getElementById(id);if(x)mo.observe(x,{childList:true})});var tb=D.querySelector(\"#c93top table.ctx tbody\");if(tb)mo.observe(tb,{childList:true})}\nif(\"MutationObserver\" in window){mo=new MutationObserver(function(){window.requestAnimationFrame(run)})}\nrun();\n/* sticky offset: under the sticky tape, header and desk tabs */\nvar story=D.getElementById(\"v9-story\"),tabs=D.querySelector(\".v8-tabs\"),hdr=D.querySelector(\"header.site\");\nfunction top(){if(!story)return;var t=12;if(hdr){var c=window.getComputedStyle(hdr);if(c.position===\"sticky\"||c.position===\"fixed\")t+=(parseFloat(c.top)||0)+hdr.offsetHeight}if(tabs&&window.getComputedStyle(tabs).position===\"sticky\")t+=tabs.offsetHeight;story.style.setProperty(\"--v9-top\",Math.round(t)+\"px\")}\ntop();window.addEventListener(\"resize\",top,{passive:true});\n})();\n";
  var MK = [["gold", "Gold"], ["dollar", "Dollar"], ["yields", "Yields"], ["oil", "Oil"], ["crypto", "Crypto"], ["equities", "Equities"]];
  var IC = {gold:'<path d="M3 19h18l-2.5-6h-13z"/><path d="M7.5 13 9.5 7h5l2 6"/>',
dollar:'<circle cx="12" cy="12" r="9"/><path d="M14.6 9.2c-.5-1-1.5-1.5-2.8-1.5-1.5 0-2.6.8-2.6 2s1.1 1.7 2.7 2c1.7.3 2.8.9 2.8 2.2s-1.2 2.1-2.8 2.1c-1.3 0-2.4-.6-2.9-1.6M12 6v1.7M12 16.3V18"/>',
yields:'<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.3"/><circle cx="17" cy="17" r="2.3"/>',
oil:'<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
crypto:'<path d="M12 2.8 20 7.4v9.2L12 21.2 4 16.6V7.4z"/><path d="M10 8.5h3a1.75 1.75 0 0 1 0 3.5h-3zm0 3.5h3.5a1.75 1.75 0 0 1 0 3.5H10zM10 8.5v7"/>',
equities:'<path d="M7 4v16M17 4v16"/><rect x="5" y="8" width="4" height="7" rx="1"/><rect x="15" y="6" width="4" height="9" rx="1"/>'};
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
