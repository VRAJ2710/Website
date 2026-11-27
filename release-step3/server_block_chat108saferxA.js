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
  var CSS = "/* chat108saferxA: v3 home preview, batch A (hero, one closing signup, slim header, desk tabs, light motion, tighter Barebone-style cards). Scoped to html.v3p.v8a; served only with the preview switch. */\nhtml.v3p.v8a{--v8-g1:#9a6b0f;--v8-g2:#86590a;--v8-g3:#6e4a08;--v8-ring:rgba(138,99,18,.5)}\nhtml.v3p.v8a.c97-dark,html.v3p.v8a[data-theme=\"dark\"]{--v8-g1:#f6d998;--v8-g2:#e6b95e;--v8-g3:#c8913a;--v8-ring:rgba(230,185,94,.55)}\n@media (prefers-color-scheme:dark){html.v3p.v8a.c97-system,html.v3p.v8a:not(.c97-light):not(.c97-dark):not([data-theme=\"light\"]):not([data-theme=\"dark\"]){--v8-g1:#f6d998;--v8-g2:#e6b95e;--v8-g3:#c8913a;--v8-ring:rgba(230,185,94,.55)}}\n/* sticky needs a non-scrolling root: clip (not hidden) on the preview only; old browsers ignore it and keep hidden */\nhtml.v3p.v8a,html.v3p.v8a body{overflow-x:clip!important}\n/* reading progress */\n.v8-prog{position:fixed;top:0;left:0;right:0;height:3px;z-index:2147483000;pointer-events:none;background:transparent}\n.v8-prog i{display:block;height:100%;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,#b8862b,#e6b95e 55%,#f6d998);box-shadow:0 0 8px rgba(230,185,94,.55)}\n/* slim header (preview only). Every link stays in the full-screen menu. */\nhtml.v8a header.site{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;border-bottom:1px solid var(--v-line)!important}\nhtml.v8a header.site>.wrap{display:flex!important;flex-wrap:nowrap!important;align-items:center;gap:10px;min-height:56px;padding-top:6px;padding-bottom:6px}\nhtml.v8a header.site .mark{flex:0 1 auto;margin-right:auto;min-width:0;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\nhtml.v8a header.site form.c97tg{order:3;flex:0 0 auto!important;margin:0;min-width:max-content!important}html.v8a header.site form.c97tg .c97tg-one{flex:0 0 auto!important}\nhtml.v8a header.site form.c97tg .c97tg-one{font:600 12px/1 \"DM Sans\",Inter,system-ui,sans-serif!important;padding:8px 12px!important;border-radius:999px!important;border:1px solid var(--v-line2)!important;background:var(--v-chip)!important;color:var(--v-ink)!important;min-height:34px;width:auto!important;max-width:none!important;white-space:nowrap;overflow:visible!important}\nhtml.v8a header.site details.menu{order:4;flex:0 0 auto}\nhtml.v8a header.site details.menu>summary{font:600 13px/1 \"DM Sans\",Inter,system-ui,sans-serif;padding:9px 14px!important;border-radius:999px;border:1px solid var(--v-line2);background:var(--v-chip);color:var(--v-ink);min-height:34px;display:inline-flex;align-items:center;gap:7px}\nhtml.v8a header.site details.menu>summary::before,html.v8a header.site .c101b-all>summary::before{content:\"\";width:14px;height:10px;flex:0 0 auto;background:linear-gradient(currentColor,currentColor) 0 0/100% 2px no-repeat,linear-gradient(currentColor,currentColor) 0 4px/100% 2px no-repeat,linear-gradient(currentColor,currentColor) 0 8px/100% 2px no-repeat}\nhtml.v8a header.site .v8-si{order:2;flex:0 0 auto;display:inline-flex;align-items:center;min-height:34px;padding:8px 14px!important;margin:0!important;border-radius:999px!important;border:0!important;background:linear-gradient(180deg,#f0c66d,#d9a441)!important;color:#1a1305!important;font:700 13px/1 \"DM Sans\",Inter,system-ui,sans-serif;text-decoration:none;white-space:nowrap}\n@media (min-width:1280px){\nhtml.v8a header.site .v8-si{display:none!important}\nhtml.v8a header.site .mark{flex:0 0 auto}\nhtml.v8a header.site .nav{order:1;flex:0 1 auto!important;flex-wrap:nowrap!important;justify-content:flex-end;gap:2px}\nhtml.v8a header.site .nav>a:not(.cta):not([href=\"/brief/\"]):not([href=\"/gold/\"]):not([href=\"/terminal/\"]):not([href=\"/markets/\"]):not([href=\"/research/\"]){display:none!important}\nhtml.v8a header.site .nav>a:not(.cta){margin:0!important;padding:8px 11px;border-radius:999px;font:500 14px/1 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink2)!important;text-decoration:none}\nhtml.v8a header.site .nav>a:not(.cta):hover{background:var(--v-chip);color:var(--v-ink)!important}\nhtml.v8a header.site .c101b-all{margin-left:8px!important}\nhtml.v8a header.site .c101b-all>summary{display:inline-flex!important;align-items:center;gap:7px;font:600 13px/1 \"DM Sans\",Inter,system-ui,sans-serif!important;padding:9px 14px!important;border-radius:999px!important;border:1px solid var(--v-line2)!important;background:var(--v-chip);color:var(--v-ink)!important}\nhtml.v8a header.site .nav>a.cta{margin-left:8px!important;padding:9px 16px!important;border-radius:999px!important;font:700 13px/1 \"DM Sans\",Inter,system-ui,sans-serif}\n}\n@media (max-width:480px){\nhtml.v8a header.site>.wrap{gap:6px;padding-left:12px;padding-right:12px}\nhtml.v8a header.site .mark{font-size:16px}\nhtml.v8a header.site form.c97tg .c97tg-one{font-size:0!important;width:34px;height:34px;padding:0!important;display:inline-flex;align-items:center;justify-content:center}\nhtml.v8a header.site form.c97tg .c97tg-one::before{content:\"\";width:14px;height:14px;border-radius:50%;border:2px solid currentColor;background:linear-gradient(90deg,currentColor 50%,transparent 50%)}\nhtml.v8a header.site .v8-si,html.v8a header.site details.menu>summary{padding:8px 11px!important;font-size:12.5px}\n}\n@media (max-width:359px){html.v8a header.site .mark{font-size:15px}html.v8a header.site .v8-si{display:none!important}html.v8a header.site details.menu>summary::before{display:none}}\n/* hero: big type lives only here */\nhtml.v8a main>.v8-hero{position:relative;display:grid;place-items:center;text-align:center;min-height:calc(100vh - 150px);min-height:calc(100svh - 150px);padding:28px 0 26px!important;margin:0 0 6px!important;background:transparent!important;border:0!important;box-shadow:none!important;overflow:hidden;isolation:isolate}\nhtml.v8a .v8-hero::before{content:\"\";position:absolute;inset:-10% -20% auto;height:80%;z-index:-1;background:radial-gradient(600px 300px at 50% 35%,var(--v-goldw),transparent 70%);pointer-events:none}\nhtml.v8a .v8-hero-in{width:100%;max-width:1120px;margin:0 auto;font-family:\"DM Sans\",Inter,system-ui,sans-serif}\nhtml.v8a .v8-hero .v3-rib{display:inline-flex;margin:0 auto 22px;max-width:100%}\nhtml.v8a .v8-kick{font:700 12px/1.3 \"DM Sans\",Inter,system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--v-gold);margin:0 0 14px}\nhtml.v8a .v8-hero h1{font:700 clamp(38px,7.1vw,96px)/.98 \"DM Sans\",Inter,system-ui,sans-serif;letter-spacing:-.04em;margin:0 0 20px;color:var(--v-ink);overflow-wrap:break-word}\nhtml.v8a .v8-hero h1 span{display:block}\nhtml.v8a .v8-hero h1 .v8-l2{background:linear-gradient(92deg,var(--v8-g1) 0%,var(--v8-g2) 45%,var(--v8-g3) 100%);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;padding-bottom:.06em}\n@media (forced-colors:active){html.v8a .v8-hero h1 .v8-l2{color:CanvasText;-webkit-text-fill-color:CanvasText;background:none}}\nhtml.v8a .v8-hero .v8-dek{font:400 18px/1.55 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink2)!important;max-width:640px;margin:0 auto 22px}\nhtml.v8a .v8-ctas{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:0 0 30px}\nhtml.v8a .v8-btn{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:11px 20px;border-radius:999px;font:700 14.5px/1.1 \"DM Sans\",Inter,system-ui,sans-serif;text-decoration:none!important;border:1px solid var(--v-line2);background:var(--v-chip);color:var(--v-ink)!important}\nhtml.v8a .v8-btn-p{background:linear-gradient(180deg,#f0c66d,#d9a441);border-color:transparent;color:#1a1305!important}\nhtml.v8a .v8-btn:focus-visible,html.v8a .v8-arc a:focus-visible,html.v8a .v8-tabs a:focus-visible{outline:2px solid var(--v8-ring);outline-offset:3px}\nhtml.v8a .v8-arc{position:relative;margin:4px auto 18px;max-width:900px}\nhtml.v8a .v8-arc ul{list-style:none;margin:0;padding:0 0 46px;display:flex;justify-content:center;gap:clamp(10px,2.4vw,30px)}\nhtml.v8a .v8-arc li{transform:translateY(var(--y,0))}\nhtml.v8a .v8-arc svg.v8-arcline{position:absolute;left:0;right:0;top:44px;width:100%;height:110px;z-index:-1;pointer-events:none}\nhtml.v8a .v8-arc a{display:flex;flex-direction:column;align-items:center;gap:8px;text-decoration:none!important;color:var(--v-ink2)!important;font:600 13px/1.2 \"DM Sans\",Inter,system-ui,sans-serif;border-radius:16px;padding:4px}\nhtml.v8a .v8-arc a:hover{color:var(--v-ink)!important}\nhtml.v8a .v8-ic{width:62px;height:62px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(150deg,var(--a),var(--b));box-shadow:0 10px 24px -8px var(--b),inset 0 1px 0 rgba(255,255,255,.25);position:relative}\nhtml.v8a .v8-ic::after{content:\"\";position:absolute;top:8px;right:8px;width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.85)}\nhtml.v8a .v8-ic svg{width:28px;height:28px;stroke:#fff;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}\nhtml.v8a .v8-by{font:400 13.5px/1.5 \"DM Sans\",Inter,system-ui,sans-serif;color:var(--v-ink3);margin:0}\nhtml.v8a .v8-by a{color:var(--v-gold)!important}\n@media (max-width:700px){\nhtml.v8a main>.v8-hero{min-height:0;padding:22px 0 18px!important}\nhtml.v8a .v8-hero .v8-dek{font-size:16px}\nhtml.v8a .v8-arc svg.v8-arcline{display:none}\nhtml.v8a .v8-arc ul{flex-wrap:wrap;gap:14px 0;padding:0}\nhtml.v8a .v8-arc li{transform:none;flex:0 0 25%}\nhtml.v8a .v8-ic{width:52px;height:52px;border-radius:15px}\nhtml.v8a .v8-ic svg{width:24px;height:24px}\nhtml.v8a .v8-arc a{font-size:12px}\n}\n@media (max-width:359px){html.v8a .v8-hero h1{font-size:34px}html.v8a .v8-ic{width:46px;height:46px}html.v8a .v8-btn{padding:10px 15px;font-size:13.5px}}\n/* desk tabs: swipeable scroll-snap pills to real sections */\nhtml.v8a .v8-tabs{position:relative;z-index:50;margin:0 calc(50% - 50vw) 14px;padding:8px max(12px,calc(50vw - 50%));background:color-mix(in srgb,var(--v-bg) 92%,transparent);border-bottom:1px solid var(--v-line)}\nhtml.v8a .v8-tabs.v8-stick{position:sticky;top:var(--v8-top,0px)}\nhtml.v8a .v8-tabs ul{list-style:none;margin:0 auto;padding:2px 0;display:flex;gap:8px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}\nhtml.v8a .v8-tabs ul::-webkit-scrollbar{display:none}\nhtml.v8a .v8-tabs li{flex:0 0 auto;scroll-snap-align:start}\nhtml.v8a .v8-tabs a{display:inline-flex;align-items:center;min-height:36px;padding:8px 14px;border-radius:999px;border:1px solid var(--v-line2);background:var(--v-chip);color:var(--v-ink2)!important;font:600 13px/1 \"DM Sans\",Inter,system-ui,sans-serif;text-decoration:none!important;white-space:nowrap}\nhtml.v8a .v8-tabs a:hover{color:var(--v-ink)!important;border-color:var(--v8-ring)}\nhtml.v8a .v8-tabs a[aria-current]{background:var(--v-ink);color:var(--v-bg)!important;border-color:var(--v-ink)}\n@media (max-width:600px){html.v8a .v8-tabs{padding-top:6px;padding-bottom:6px;margin-bottom:10px}html.v8a .v8-tabs a{min-height:32px;padding:6px 12px;font-size:12.5px}}\n/* Barebone-style density: same v3 components, tighter */\nhtml.v8a .v3{padding-top:0!important}\nhtml.v8a .v3-grid{gap:12px}\nhtml.v8a .v3-card{padding:16px 18px;border-radius:18px}\nhtml.v8a .v3-h{font:700 25px/1.2 \"DM Sans\",Inter,system-ui,sans-serif;letter-spacing:-.015em}\nhtml.v8a .v3-k{font-size:11px;letter-spacing:.1em;margin-bottom:8px}\nhtml.v8a .v3-p{font-size:14.5px;line-height:1.5}\nhtml.v8a .v3-prices{gap:8px}\nhtml.v8a .v3-pt{padding:10px 11px;border-radius:12px}\nhtml.v8a .v3-pt .v{font-size:18px}\nhtml.v8a .v3-tiles{gap:8px}\nhtml.v8a .v3-tile{padding:10px 11px;border-radius:12px}\nhtml.v8a .v3-bars{gap:10px}\nhtml.v8a .v3-ul{gap:8px}\nhtml.v8a .v3-ul li{font-size:13.5px}\nhtml.v8a .v3-src{font-size:11.5px}\nhtml.v8a .v3-more{font:700 12px/1.3 \"DM Sans\",Inter,system-ui,sans-serif!important;letter-spacing:.14em;text-transform:uppercase;color:var(--v-ink3)!important;margin:26px 0 4px!important}\nhtml.v8a main>section:not(.v3):not(.v8-hero):not(.v8-band) h1,html.v8a main>section:not(.v3):not(.v8-hero):not(.v8-band) h2{font-family:\"DM Sans\",Inter,system-ui,sans-serif;font-weight:700;letter-spacing:-.01em;font-size:22px}\n@media (max-width:600px){html.v8a .v3-h{font-size:21px}html.v8a .v3-card{padding:14px}html.v8a .v3-pt .v{font-size:16px}}\n/* closing band: the page's only signup (existing form, unchanged behaviour) */\nhtml.v8a main>section.v8-band{position:relative;margin:28px 0 8px!important;padding:clamp(22px,4vw,44px)!important;text-align:center;border-radius:24px!important;border:1px solid var(--v8-ring)!important;background:radial-gradient(520px 220px at 50% 0%,var(--v-goldw),transparent 70%),var(--v-card)!important;overflow:hidden}\nhtml.v8a .v8-band .c96su{max-width:620px;margin:0 auto}\nhtml.v8a .v8-band .c96su h2{font:700 clamp(24px,3.4vw,34px)/1.15 \"DM Sans\",Inter,system-ui,sans-serif!important;letter-spacing:-.02em;margin:8px 0 8px!important}\nhtml.v8a .v8-band .c96su p{margin-left:auto!important;margin-right:auto!important;color:var(--v-ink2)!important}\nhtml.v8a .v8-band .c96su-row{justify-content:center;margin:14px auto 0}\nhtml.v8a .v8-band .c96su button{min-height:44px;padding:10px 20px!important;font-weight:700}\nhtml.v8a .v8-band .c96su input[type=email]{min-height:44px;padding:10px 16px!important}\nhtml.v8a .v8-band .kicker{color:var(--v-gold)!important;letter-spacing:.14em}\n/* light motion: off under reduced motion. The site stylesheet sets animation/transition none !important on *, so the preview opts back in with !important here only. */\n@media (prefers-reduced-motion:no-preference){\nhtml.v8a .v8-hero-in>*{animation:v8in .8s cubic-bezier(.2,.7,.2,1) both!important}\nhtml.v8a .v8-hero-in>:nth-child(2){animation-delay:.06s!important}html.v8a .v8-hero-in>:nth-child(3){animation-delay:.12s!important}html.v8a .v8-hero-in>:nth-child(4){animation-delay:.2s!important}html.v8a .v8-hero-in>:nth-child(5){animation-delay:.28s!important}html.v8a .v8-hero-in>:nth-child(6){animation-delay:.36s!important}html.v8a .v8-hero-in>:nth-child(n+7){animation-delay:.44s!important}\n@keyframes v8in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}\n}\n@media (hover:hover) and (prefers-reduced-motion:no-preference){\nhtml.v8a .v3-card,html.v8a main>section:not(.v3):not(.v8-hero),html.v8a .v8-ic,html.v8a .v8-btn{transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease!important}\nhtml.v8a .v3-card:hover,html.v8a main>section:not(.v3):not(.v8-hero):hover{transform:translateY(-3px);border-color:var(--v-line2)!important;box-shadow:0 14px 34px -12px rgba(0,0,0,.35),0 0 0 1px var(--v-line2)}\nhtml.v8a .v8-arc a:hover .v8-ic{transform:translateY(-4px)}\nhtml.v8a .v8-btn:hover{transform:translateY(-2px)}\n}\n@media (prefers-reduced-motion:reduce){html.v8a .v8-prog{display:none}html.v8a *{scroll-behavior:auto!important}}\n";
  var JS = "/* chat108saferxA: sticky desk tabs offset and reading-progress bar for the v3 home preview. No network, no storage. */\n(function(){\n\"use strict\";\nif(window.__v8a)return;window.__v8a=1;\nvar D=document,bar=D.querySelector(\".v8-prog i\");\nvar tabs=D.querySelector(\".v8-tabs\"),hdr=D.querySelector(\"header.site\");\nfunction stick(){if(!tabs||!hdr)return;var c=window.getComputedStyle(hdr),t=0;if(c.position===\"sticky\"||c.position===\"fixed\")t=(parseFloat(c.top)||0)+hdr.offsetHeight;tabs.style.setProperty(\"--v8-top\",Math.max(0,Math.round(t))+\"px\");tabs.classList.add(\"v8-stick\");}\nstick();window.addEventListener(\"resize\",stick,{passive:true});\nvar rm=window.matchMedia?window.matchMedia(\"(prefers-reduced-motion: reduce)\"):null;\nif(!bar||(rm&&rm.matches))return;\nvar busy=false;\nfunction upd(){busy=false;var h=D.documentElement,max=h.scrollHeight-h.clientHeight,y=window.pageYOffset||h.scrollTop||0;var p=max>0?Math.min(1,Math.max(0,y/max)):0;bar.style.transform=\"scaleX(\"+p.toFixed(4)+\")\";}\nfunction on(){if(busy)return;busy=true;window.requestAnimationFrame(upd);}\nwindow.addEventListener(\"scroll\",on,{passive:true});\nwindow.addEventListener(\"resize\",on,{passive:true});\nupd();\n})();\n";
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
