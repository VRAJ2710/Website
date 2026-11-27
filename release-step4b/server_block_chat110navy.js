
// chat110navy: release-step4 (27 Nov 2026). Navy redesign VISUALS for the server-rendered public pages, as a response
// transform appended after chat107credits (it needs the step-1..3 blocks attached). Presentation only:
// on a finished 200 text/html page that still carries the old inline c93 stylesheet it (1) drops that inline stylesheet and
// the Inter/Source Serif font link, (2) links the navy /styles.css?v=chat110navy (DM Sans) before the c97 theme style,
// (3) adds the shared site layer /__navy/site.css (served by this block; html class "nv", "nv-v3" on the v3 home) and a
// mobile bottom bar of links to existing sections, sets data-theme on <html> from the existing c97-light/dark/system class (default stays "system") and keeps it in step
// with the theme toggle, and (4) adds the market tape (gold and the dollar index from the existing same-origin
// /api/market-reference-quotes) with plain-English source, UK time and delay labels and no raw feed codes (items carry
// data-v3p="1" so the v3 home's tape relabeller, written for the dev tape, leaves them as they are).
// Never touches: /api/*, /__auth/*, sign-in, account, checkout, admin, webhooks, assets, non-HTML or encoded responses,
// streaming responses (passed straight through), request handling, cookies, status codes, DB, auth, payments, AI, email.
(function () {
  var TAG = "chat110navy";
  var SITE_CSS = "/* chat110navy site layer: one shared look for every server-rendered page (html.nv) and the app shell (html.dispatch-shell).\n   Presentation only: colours, type, spacing, cards, header/footer, mobile bottom bar. No content is hidden or moved. */\nhtml.nv,html.dispatch-shell{--nv-bg:#060708;--nv-glow:radial-gradient(900px 520px at 85% -8%,rgba(92,104,140,.22),transparent 62%),radial-gradient(800px 480px at -10% 8%,rgba(214,166,72,.09),transparent 60%);\n --nv-card:linear-gradient(180deg,#16181d 0%,#101216 55%,#0c0d10 100%);--nv-card2:linear-gradient(160deg,#1d1f26 0%,#121419 55%,#0c0d10 100%);--nv-solid:#111317;--nv-sunk:#0b0c0f;\n --nv-ink:#f1f2f4;--nv-ink2:#b7bcc6;--nv-ink3:#8e95a1;--nv-line:rgba(255,255,255,.08);--nv-line2:rgba(255,255,255,.15);--nv-gold:#e6b95e;--nv-goldw:rgba(230,185,94,.12);\n --nv-blue:#7aa8ff;--nv-up:#3fd08f;--nv-down:#ff6d61;--nv-nav:rgba(10,11,13,.94);--nv-shadow:0 12px 34px rgba(0,0,0,.45);--nv-r:20px;--nv-r2:12px;\n --nv-ui:'DM Sans',system-ui,-apple-system,'Segoe UI',Arial,sans-serif;--nv-serif:'Source Serif 4',Georgia,serif;--nv-mono:'IBM Plex Mono',ui-monospace,Menlo,monospace}\nhtml.nv.c97-light,html.dispatch-shell.c97-light{--nv-bg:#f3f1ec;--nv-glow:radial-gradient(900px 520px at 85% -8%,rgba(120,132,170,.16),transparent 62%),radial-gradient(800px 480px at -10% 8%,rgba(176,132,40,.10),transparent 60%);\n --nv-card:linear-gradient(180deg,#fff 0%,#fdfcf9 60%,#faf8f3 100%);--nv-card2:linear-gradient(160deg,#fff 0%,#fbf6ea 100%);--nv-solid:#fff;--nv-sunk:#f6f4ef;\n --nv-ink:#121418;--nv-ink2:#3a414c;--nv-ink3:#5c6572;--nv-line:rgba(18,20,26,.09);--nv-line2:rgba(18,20,26,.16);--nv-gold:#8a6312;--nv-goldw:rgba(138,99,18,.09);\n --nv-blue:#1f5fbf;--nv-up:#0f7a4b;--nv-down:#c2352a;--nv-nav:rgba(255,255,255,.94);--nv-shadow:0 1px 2px rgba(18,20,26,.05),0 10px 28px rgba(18,20,26,.07)}\n@media (prefers-color-scheme:light){html.nv.c97-system,html.dispatch-shell.c97-system{--nv-bg:#f3f1ec;--nv-glow:radial-gradient(900px 520px at 85% -8%,rgba(120,132,170,.16),transparent 62%),radial-gradient(800px 480px at -10% 8%,rgba(176,132,40,.10),transparent 60%);\n --nv-card:linear-gradient(180deg,#fff 0%,#fdfcf9 60%,#faf8f3 100%);--nv-card2:linear-gradient(160deg,#fff 0%,#fbf6ea 100%);--nv-solid:#fff;--nv-sunk:#f6f4ef;\n --nv-ink:#121418;--nv-ink2:#3a414c;--nv-ink3:#5c6572;--nv-line:rgba(18,20,26,.09);--nv-line2:rgba(18,20,26,.16);--nv-gold:#8a6312;--nv-goldw:rgba(138,99,18,.09);\n --nv-blue:#1f5fbf;--nv-up:#0f7a4b;--nv-down:#c2352a;--nv-nav:rgba(255,255,255,.94);--nv-shadow:0 1px 2px rgba(18,20,26,.05),0 10px 28px rgba(18,20,26,.07)}}\n/* map the existing page tokens onto the shared palette so every older rule follows it */\nhtml.nv:root,html.nv.c97-dark:root,html.nv.c97-light:root,html.nv.c97-system:root,html.dispatch-shell:root,html.dispatch-shell[data-theme]:root{\n --paper:var(--nv-bg);--paper-2:var(--nv-solid);--carbon:var(--nv-solid);--carbon-2:var(--nv-sunk);--ink:var(--nv-ink);--ink-2:var(--nv-ink2);--ink-3:var(--nv-ink3);--muted:var(--nv-ink3);\n --rule:var(--nv-line);--rule-2:var(--nv-line2);--rule-soft:var(--nv-line);--rule-hair:var(--nv-line);--accent:var(--nv-gold);--gold:var(--nv-gold);--gold-2:var(--nv-gold);--gold-wash:var(--nv-goldw);\n --up:var(--nv-up);--down:var(--nv-down);--pos:var(--nv-up);--neg:var(--nv-down);--b1:var(--nv-bg);--b2:var(--nv-solid);--b3:var(--nv-sunk);--gb:var(--nv-line);--tx:var(--nv-ink);--t2:var(--nv-ink2);--t3:var(--nv-ink3);\n --gd:var(--nv-gold);--gn:var(--nv-up);--rd:var(--nv-down);--sans:var(--nv-ui);--ui:var(--nv-ui);--serif:var(--nv-serif)}\nhtml.nv,html.nv body{background:var(--nv-bg)!important;color:var(--nv-ink)!important}\nhtml.nv body{background-image:var(--nv-glow)!important;background-repeat:no-repeat!important;background-attachment:fixed;font-family:var(--nv-ui)!important;font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}\nhtml.nv a{color:var(--nv-blue)}\nhtml.nv .wrap{max-width:1120px;padding-left:20px;padding-right:20px;box-sizing:border-box}\n/* header */\nhtml.nv header.site{position:sticky;top:0;z-index:250;background:var(--nv-nav)!important;border-bottom:1px solid var(--nv-line)!important;-webkit-backdrop-filter:saturate(140%) blur(12px);backdrop-filter:saturate(140%) blur(12px)}\nhtml.nv .public-market-tape+header.site{top:44px}\nhtml.nv header.site .mark{color:var(--nv-ink)!important;font-family:var(--nv-serif)!important;font-weight:600;letter-spacing:-.01em}\nhtml.nv header.site .nav a{color:var(--nv-ink2)!important;border-radius:999px;padding:6px 10px;margin-left:2px;text-decoration:none!important;font-weight:500}\nhtml.nv header.site .nav a:hover{background:var(--nv-goldw);color:var(--nv-ink)!important}\nhtml.nv header.site .nav a[aria-current]{background:var(--nv-goldw);color:var(--nv-gold)!important}\nhtml.nv header.site a.cta,html.nv header.site .auth-btn{background:var(--nv-gold)!important;color:#121418!important;border:0!important;border-radius:999px!important;padding:8px 14px!important;font-weight:600}\nhtml.nv header.site details.menu>summary,html.nv header.site details.c101b-all>summary,html.nv form.c97tg button{border:1px solid var(--nv-line2)!important;border-radius:999px!important;background:transparent!important;color:var(--nv-ink)!important}\nhtml.nv .strip{background:transparent!important;border-bottom:1px solid var(--nv-line)!important;color:var(--nv-ink3)!important;font-size:12.5px}\nhtml.nv .strip .disc{color:var(--nv-ink2)!important}\n/* page body: hero + rounded cards */\nhtml.nv main.wrap{padding-top:18px;padding-bottom:32px}\nhtml.nv main.wrap>section{background:var(--nv-card)!important;border:1px solid var(--nv-line)!important;border-radius:var(--nv-r)!important;box-shadow:var(--nv-shadow);padding:22px 22px!important;margin:16px 0!important;max-width:100%;box-sizing:border-box;overflow-x:auto;color:var(--nv-ink)}\nhtml.nv main.wrap>section:first-child{background:transparent!important;border:0!important;box-shadow:none;padding:18px 2px 6px!important;overflow:visible}\nhtml.nv .kicker,html.nv .c101h-kind{display:inline-block;color:var(--nv-gold)!important;background:var(--nv-goldw);border-radius:999px;padding:3px 10px;font:600 11px/1.5 var(--nv-ui)!important;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}\nhtml.nv h1{font-family:var(--nv-ui)!important;font-weight:700!important;letter-spacing:-.025em!important;line-height:1.08!important;font-size:clamp(30px,5.2vw,48px)!important;color:var(--nv-ink)!important;margin:4px 0 12px!important}\nhtml.nv h2{font-family:var(--nv-ui)!important;font-weight:650;letter-spacing:-.015em;font-size:clamp(19px,2.6vw,23px)!important;color:var(--nv-ink)!important;margin:0 0 10px!important}\nhtml.nv h3{font-family:var(--nv-ui)!important;color:var(--nv-ink)!important}\nhtml.nv .dek{font-family:var(--nv-serif)!important;color:var(--nv-ink2)!important;font-size:clamp(16px,2vw,19px)!important;line-height:1.55;max-width:760px}\nhtml.nv .byline,html.nv .note,html.nv p.src,html.nv .src,html.nv .msrc,html.nv .c97s,html.nv .c97note{color:var(--nv-ink3)!important}\nhtml.nv main.wrap>section p,html.nv main.wrap>section li{color:var(--nv-ink2)}\nhtml.nv main.wrap>section strong,html.nv main.wrap>section b{color:var(--nv-ink)}\nhtml.nv .card,html.nv section.c101card,html.nv .c96wall,html.nv .about-tier{background:var(--nv-card2)!important;border:1px solid var(--nv-line2)!important;border-radius:var(--nv-r2)!important;padding:16px!important;color:var(--nv-ink)!important}\nhtml.nv .grid{gap:16px}\nhtml.nv .big{color:var(--nv-ink)!important;font-family:var(--nv-mono)}\n/* tables and editorial lists */\nhtml.nv table{border-collapse:collapse;width:100%;background:transparent!important;color:var(--nv-ink)}\nhtml.nv th{color:var(--nv-ink3)!important;font:600 11px/1.4 var(--nv-ui)!important;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--nv-line2)!important;background:transparent!important}\nhtml.nv td{border-bottom:1px solid var(--nv-line)!important;color:var(--nv-ink);background:transparent!important}\nhtml.nv td.n,html.nv th.n{font-family:var(--nv-mono);font-variant-numeric:tabular-nums}\nhtml.nv tr:hover td{background:rgba(127,127,127,.05)!important}\nhtml.nv main.wrap td a,html.nv ul.c101h-list a,html.nv ol.c97tl a{color:var(--nv-ink)!important;font-weight:600;text-decoration:none}\nhtml.nv main.wrap td a:hover,html.nv ul.c101h-list a:hover{color:var(--nv-gold)!important}\nhtml.nv ul.c101h-list{list-style:none;padding:0;margin:0}\nhtml.nv ul.c101h-list li{padding:12px 0;border-top:1px solid var(--nv-line)}\nhtml.nv ul.c101h-list li:first-child{border-top:0}\nhtml.nv .c101tools{display:flex;flex-wrap:wrap;gap:8px}\nhtml.nv .c101tools a,html.nv .c96su button,html.nv main.wrap a.btn{border:1px solid var(--nv-line2)!important;border-radius:999px!important;padding:7px 12px!important;background:var(--nv-sunk)!important;color:var(--nv-ink)!important;text-decoration:none!important}\nhtml.nv .c96su input{background:var(--nv-sunk)!important;color:var(--nv-ink)!important;border:1px solid var(--nv-line2)!important;border-radius:999px!important;padding:9px 14px!important}\nhtml.nv .c96su button{background:var(--nv-gold)!important;color:#121418!important;border:0!important;font-weight:600}\nhtml.nv .c100b-up,html.nv .up{color:var(--nv-up)!important}html.nv .c100b-dn,html.nv .down{color:var(--nv-down)!important}\n/* footer */\nhtml.nv footer.site{background:var(--nv-sunk)!important;border-top:1px solid var(--nv-line)!important;color:var(--nv-ink3)!important;margin-top:24px}\nhtml.nv footer.site a{color:var(--nv-ink2)!important}\n/* full-screen menu keeps its behaviour; colours only */\nhtml.nv .c93-menu.c101c-sheet,html.nv nav.c101c-sheet{background:var(--nv-bg)!important;color:var(--nv-ink)!important}\nhtml.nv .c101c-bar{background:var(--nv-nav)!important;border-bottom:1px solid var(--nv-line)!important}\nhtml.nv .c101c-sheet a{color:var(--nv-ink)!important}\n/* mobile bottom bar (links to existing sections only) */\n.nv-bbar{display:none}\n@media (max-width:767px){\n html.nvb .nv-bbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:300;justify-content:space-around;align-items:stretch;background:var(--nv-nav);border-top:1px solid var(--nv-line);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);padding:0 0 env(safe-area-inset-bottom)}\n html.nvb .nv-bbar a{flex:1 1 0;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:56px;color:var(--nv-ink3)!important;font:600 11px/1.2 var(--nv-ui);text-decoration:none!important;gap:3px}\n html.nvb .nv-bbar a[aria-current=page]{color:var(--nv-gold)!important}\n html.nvb .nv-bbar i{display:block;width:18px;height:2px;border-radius:2px;background:currentColor;opacity:.7}\n html.nvb body{padding-bottom:64px}\n html.nvb #c101-inst{bottom:64px!important}\n html.nv main.wrap>section{padding:18px 16px!important;border-radius:16px!important}\n html.nv .wrap{padding-left:14px;padding-right:14px}\n}\n/* app shell (SPA routes): same palette and cards */\nhtml.dispatch-shell body{background:var(--nv-bg)!important;background-image:var(--nv-glow)!important;background-repeat:no-repeat!important;color:var(--nv-ink)}\nhtml.dispatch-shell .gc,html.dispatch-shell .card,html.dispatch-shell .news-card,html.dispatch-shell .panel,html.dispatch-shell .lab-panel,html.dispatch-shell .pro-hub-card{background:var(--nv-card)!important;border:1px solid var(--nv-line)!important;border-radius:16px!important}\nhtml.dispatch-shell .cmd-bar,html.dispatch-shell .hdr{background:var(--nv-nav)!important;border-bottom:1px solid var(--nv-line)!important}\nhtml.dispatch-shell .site-trust-footer{background:var(--nv-sunk)!important;border-top:1px solid var(--nv-line)}\n";
  var SITE_LINK = '<link rel="stylesheet" href="/__navy/site.css?v=chat110navy">';
  var CSS_LINK = '<link rel="stylesheet" href="/styles.css?v=chat110navy">';
  var C93_START = "<style>:root{--paper:#fbfaf7;--ink:#1b1b1b;";
  var FONT_LINK = '<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;600&display=swap" rel="stylesheet">';
  var SKIP = /^\/(?:api|__auth|__v3p|admin|signin|signup|login|logout|register|account|checkout|billing|webhook|webhooks|stripe|auth|reset|verify)(?:[\/?#.]|$)/i;
  var TAPE = '<aside class="public-market-tape" aria-label="Market prices" data-c110-tape="1"><div class="public-market-tape-label" data-v3p="1">Markets <span>reference prices</span></div>' +
    '<div class="public-market-tape-track" id="publicMarketTape" aria-live="polite"><span class="public-market-tape-empty">Prices updating…</span></div></aside>' +
    '<script>(function(){var root=document.getElementById("publicMarketTape");if(!root||root.getAttribute("data-on"))return;root.setAttribute("data-on","1");' +
    'var keys=[["XAU","Gold spot","$"],["DXY","US dollar index",""]];' +
    'function src(q){var f=q.feed||{},c=[q.sourceLabel,q.feedLabel,q.source,f.source,q.exchange].map(function(v){return String(v||"")}).join(" ").toLowerCase();' +
    'if(c.indexOf("gold-api")>=0)return"gold-api.com";if(c.indexOf("yahoo")>=0)return"Yahoo Finance";if(c.indexOf("stooq")>=0)return"Stooq";if(c.indexOf("coinbase")>=0)return"Coinbase";' +
    'var l=String(q.sourceLabel||q.feedLabel||"");return/\\s/.test(l)&&!/[_]/.test(l)?l:"Source not given"}' +
    'function stamp(q){var f=q.feed||{};if(q.asOfUk)return q.asOfUk;if(f.asOfUk)return f.asOfUk;var v=q.asOf||f.asOf||q.ts||q.timestamp;if(!v)return"Time not given";var d=new Date(typeof v==="number"?(v<1e12?v*1000:v):v);' +
    'return isNaN(d.getTime())?"Time not given":d.toLocaleString("en-GB",{timeZone:"Europe/London",weekday:"short",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",hour12:false})+" UK"}' +
    'function fresh(q){var f=q.feed||{},s=String(q.status||f.status||"").toLowerCase(),dm=Number(q.delayMin!=null?q.delayMin:f.delayMin);' +
    'if(q.stale||s==="stale")return"Stale";if(s==="closed")return"Last close";if(s==="live"&&!q.proxy)return"Live";if(s==="delayed"||q.cached)return dm>0?"Delayed "+Math.round(dm)+" min":"Delayed";' +
    'if(q.proxy)return"Reference price";return dm>0?"Delayed "+Math.round(dm)+" min":"Delayed"}' +
    'function fmt(n){n=Number(n);if(!isFinite(n)||n<=0)return"";return n>=10000?Math.round(n).toLocaleString("en-GB"):n>=1?n.toLocaleString("en-GB",{minimumFractionDigits:2,maximumFractionDigits:2}):n.toFixed(4)}' +
    'function render(data){root.textContent="";keys.forEach(function(x){var q=data&&data[x[0]],it=document.createElement("span");it.className="public-market-tape-item";it.setAttribute("data-v3p","1");' +
    'var nm=document.createElement("strong");nm.textContent=x[1];it.appendChild(nm);' +
    'if(!q||!(Number(q.p)>0)){var e=document.createElement("span");e.className="public-market-tape-empty";e.textContent="No current price";it.appendChild(e);root.appendChild(it);return}' +
    'var b=document.createElement("b");b.textContent=x[2]+fmt(q.p);it.appendChild(b);' +
    'var ch=q.changePct!=null?Number(q.changePct):q.c!=null?Number(q.c):null;if(ch!=null&&isFinite(ch)){var c=document.createElement("span");c.className="public-market-change "+(ch>0?"up":ch<0?"down":"");c.textContent=(ch>0?"+":ch<0?"\\u2212":"")+Math.abs(ch).toFixed(2)+"%";it.appendChild(c)}' +
    'var m=document.createElement("small");m.textContent=[fresh(q),src(q),stamp(q)].join(" \\u00b7 ");it.appendChild(m);root.appendChild(it)})}' +
    'function pull(){fetch("/api/market-reference-quotes",{credentials:"same-origin",cache:"no-store"}).then(function(r){if(!r.ok)throw new Error("x");return r.json()}).then(render).catch(function(){render(null)})}' +
    'pull();setInterval(pull,60000)})();</script>';
  var SYNC = '<script>(function(){var de=document.documentElement;function s(){var m=/\\bc97-(light|dark|system)\\b/.exec(de.className||"");var v=m?m[1]:"system";if(de.getAttribute("data-theme")!==v)de.setAttribute("data-theme",v)}' +
    's();try{new MutationObserver(s).observe(de,{attributes:true,attributeFilter:["class"]})}catch(e){}})();</script>';
  var BB = [["/", "Today"], ["/brief/", "Brief"], ["/gold/", "Gold"], ["/markets/", "Markets"], ["/research/", "Research"]];
  function bbar(path) {
    var p = String(path || "/"), h = '<nav class="nv-bbar" aria-label="Main sections">', i, cur;
    for (i = 0; i < BB.length; i++) {
      cur = BB[i][0] === "/" ? p === "/" : p.indexOf(BB[i][0]) === 0;
      h += '<a href="' + BB[i][0] + '"' + (cur ? ' aria-current="page"' : "") + "><i></i>" + BB[i][1] + "</a>";
    }
    return h + "</nav>";
  }
  function transform(t, path) {
    if (typeof t !== "string" || t.indexOf("data-c110navy") >= 0) return null;
    var i = t.indexOf(C93_START);
    if (i < 0) return null;
    var j = t.indexOf("</style>", i);
    if (j < 0 || j - i > 12000 || j - i < 1500) return null;
    var hm = /<html\b([^>]*)>/i.exec(t);
    if (!hm || hm.index > i) return null;
    var out = t.slice(0, i) + t.slice(j + 8);
    out = out.split(FONT_LINK).join("");
    var k = out.indexOf('<style id="c97-theme">');
    if (k < 0) k = out.indexOf("</head>");
    if (k < 0) return null;
    out = out.slice(0, k) + CSS_LINK + out.slice(k);
    out = out.replace('<meta name="theme-color" content="#fbfaf7">', '<meta name="theme-color" content="#111820">');
    out = out.replace(/<html\b([^>]*)>/i, function (m, a) {
      var sm = /\bc97-(light|dark|system)\b/.exec(a), scheme = sm ? sm[1] : "system";
      var extra = /\bclass="[^"]*\bv3p\b/.test(a) ? "nv-v3 nvb" : "nv nvb";
      a = a.replace(/\sdata-theme="[^"]*"/i, "");
      if (/\sclass="/i.test(a)) a = a.replace(/\sclass="([^"]*)"/i, function (cm, c) { return ' class="' + c + " " + extra + '"'; });
      else a += ' class="' + extra + '"';
      return "<html" + a + ' data-theme="' + scheme + '" data-c110navy="1">';
    });
    var he = out.lastIndexOf("</head>");
    if (he < 0) return null;
    out = out.slice(0, he) + SITE_LINK + out.slice(he);
    var bm = /<body\b[^>]*>/i.exec(out);
    if (!bm) return null;
    var at = bm.index + bm[0].length;
    var tape = out.indexOf('class="public-market-tape"') >= 0 ? "" : TAPE;
    out = out.slice(0, at) + SYNC + tape + out.slice(at);
    var be = out.lastIndexOf("</body>");
    if (be > 0) out = out.slice(0, be) + bbar(path) + out.slice(be);
    return out;
  }
  function wrap(res, path) {
    var chunks = [], mode = null, ended = false, w0 = res.write, e0 = res.end, wh0 = res.writeHead;
    function restore() { res.write = w0; res.end = e0; res.writeHead = wh0; }
    function decide() {
      if (mode) return mode;
      var ct = "", ce = null;
      try { ct = String(res.getHeader("content-type") || ""); ce = res.getHeader("content-encoding"); } catch (e) {}
      mode = (res.statusCode === 200 && /text\/html/i.test(ct) && !ce) ? "buf" : "pass";
      if (mode === "pass") restore();
      return mode;
    }
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
      if (decide() === "pass") return wh0.call(res, res.statusCode);
      return res;
    };
    res.write = function (c, enc, cb) {
      if (decide() === "pass") return w0.apply(res, arguments);
      push(c, enc); if (typeof enc === "function") enc(); else if (typeof cb === "function") cb(); return true;
    };
    res.end = function (c, enc, cb) {
      if (ended) return res;
      if (decide() === "pass") { ended = true; return e0.apply(res, arguments); }
      ended = true;
      if (typeof c === "function") { cb = c; c = null; } else if (typeof enc === "function") { cb = enc; enc = null; }
      push(c, enc);
      restore();
      var body = Buffer.concat(chunks), out = null;
      try { out = transform(body.toString("utf8"), path); } catch (eT) { out = null; console.log("[" + TAG + "] skipped: " + (eT && eT.message || eT)); }
      var fin = out != null ? Buffer.from(out, "utf8") : body;
      if (!res.headersSent) { try { res.setHeader("Content-Length", fin.length); } catch (eL) {} }
      return e0.call(res, fin, cb);
    };
  }
  try {
    var http = typeof require === "function" ? require("http") : null;
    var SP = http && http.Server && http.Server.prototype;
    if (!SP) throw new Error("http.Server not found");
    if (SP.emit && SP.emit.__chat110navy) return;
    if (!SP.emit || !SP.emit.__chat109v3default) throw new Error("chat109v3default is not attached; navy stays off");
    var emit0 = SP.emit;
    var emit = function (type, req, res) {
      if (type !== "request" || !req || !res) return emit0.apply(this, arguments);
      try {
        var u = String(req.url || ""), q = u.indexOf("?"), path = q < 0 ? u : u.slice(0, q);
        var m = String(req.method || "GET").toUpperCase();
        if (path === "/__navy/site.css" && (m === "GET" || m === "HEAD")) {
          var buf = Buffer.from(SITE_CSS, "utf8");
          res.statusCode = 200; res.setHeader("Content-Type", "text/css; charset=utf-8"); res.setHeader("Content-Length", buf.length);
          res.setHeader("Cache-Control", "public, max-age=300"); res.setHeader("X-Content-Type-Options", "nosniff");
          res.end(m === "HEAD" ? undefined : buf); return true;
        }
        if (m === "GET" && !SKIP.test(path) && !/\.[a-z0-9]{1,8}$/i.test(path)) wrap(res, path);
      } catch (eReq) {
        console.log("[" + TAG + "] skipped: " + (eReq && eReq.message || eReq));
      }
      return emit0.apply(this, arguments);
    };
    Object.keys(emit0).forEach(function (k) { if (/^__/.test(k)) emit[k] = emit0[k]; });
    emit.__chat110navy = 1;
    SP.emit = emit;
    globalThis.__c110navy = { transform: transform };
    console.log("[" + TAG + "] " + "attached");
  } catch (e) {
    console.log("[" + TAG + "] not attached: " + (e && e.message || e));
  }
})();
