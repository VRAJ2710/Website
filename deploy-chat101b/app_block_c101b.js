// ── chat101b: all sections ── every core section back in the header menu (desktop "All sections", mobile "Menu").
// Items: [app page id or "", path, label, description]. Signed-in readers open app pages in place; everyone else follows the link.
(function () {
  var G = [
    ["Start", [["home", "/", "Home", "The front page"], ["brief", "/brief/", "Brief", "The daily view"], ["playbook", "/playbook/", "Playbook", "Weekly gold and macro scenarios"], ["gold", "/gold/", "Gold", "Gold price, drivers and levels"]]],
    ["Desk", [["dash", "/dashboard/", "Dashboard", "Your overview"], ["lab", "/lab/", "Market Lab", "Charts and comparisons"], ["sig", "/signals/", "Signals", "What the indicators say"]]],
    ["Markets", [["mkt", "/markets/", "Markets", "Prices across asset classes"], ["scr", "/screener/", "Screener", "Filter companies"], ["sectors", "/sectors/", "Sectors", "Sector moves"], ["heat", "/heatmap/", "Heatmap", "Moves at a glance"], ["crypto", "/crypto/", "Crypto", "Bitcoin and other coins"]]],
    ["Research", [["news", "/news/", "Newsroom", "Market news with sources"], ["paper", "/paper/", "Paper", "Practice trading, no real money"], ["research", "/research/", "Research", "Reports and the monitor"], ["intel", "/documents/", "Documents", "Your document library"], ["geo", "/geo/", "Geo Ops", "Energy and shipping risk"]]],
    ["Book", [["watch", "/watchlist/", "Watchlist", "Companies you follow"], ["port", "/portfolio/holdings/", "Portfolio", "Track holdings"], ["learn", "/learn/", "Learn", "Lessons and guides"]]],
    ["Gold and macro", [["", "/gold/dashboard/", "Gold dashboard", "Gold in \u00a3, $ and \u20ac, with what moves it"], ["", "/calendar/", "Calendar", "US and UK releases in UK time"], ["", "/what-changed/", "What changed today", "Sourced moves since the morning"], ["", "/markets/yields/", "Yields", "UK and US yield curves, end of day"], ["", "/gold/positioning/", "Gold positioning", "CFTC weekly report, ten-year percentile"], ["", "/central-banks/", "Central banks", "Fed and BoE statements, redlined"], ["", "/data-status/", "Data status", "When each free source last answered"]]],
    ["Tools and filings", [["", "/tools/", "Tools", "All the checking and planning tools"], ["", "/tools/verify/", "Verify this claim", "Supported, not supported or can't verify"], ["", "/tools/isa-sipp/", "ISA/SIPP planner", "Illustrative, not advice"], ["", "/tools/scenario/", "Scenario simulator", "Real yields, the dollar and gold"], ["", "/alerts/", "Alerts", "Gold, yields and release alerts"], ["", "/portfolio/", "Portfolio X-ray", "How your mix leans on rates, gold and the dollar"], ["", "/research/filing-changes/", "Filing change detector", "What companies changed in 10-Qs and 10-Ks"], ["", "/research/sec/", "Company filings", "Five years of SEC figures for any US company"], ["", "/research/sec/screener/", "Filings screener", "Revenue, growth and margins from 10-Ks"], ["", "/research/capital-sustainability", "Capital Sustainability Monitor", "What filings show about capital spending"]]],
    ["About", [["", "/about", "About", "Who we are"], ["", "/pricing", "Pricing", "Free and Premium"], ["", "/free-brief/", "Free brief", "The daily brief by email"], ["", "/methodology", "Methodology", "Where figures come from"], ["", "/editorial-standards", "Editorial standards", "How we write and check"], ["", "/corrections", "Corrections", "What we fixed"], ["", "/contact", "Contact", "Get in touch"]]],
    ["Account", [["settings", "/settings/", "Settings", "Theme, alerts and your account"]]]
  ];
  var ADMIN = ["", "/__admin", "Admin Console", "Admin only"];
  window.C101B_GROUPS = G;
  function admin() { try { return typeof _userAdmin !== "undefined" && _userAdmin === true && !window._tdMePreview; } catch (e) { return false; } }
  function esc(s) { return typeof c93_esc === "function" ? c93_esc(s) : String(s == null ? "" : s); }
  try {
    if (typeof C93_MENU !== "undefined") {                // keep the shared list in step (older add-ons look for their own group names and now find none)
      C93_MENU.length = 0;
      G.forEach(function (g) { C93_MENU.push([g[0], g[1].map(function (it) { return [it[0] && it[0] !== "home" && it[0] !== "settings" ? it[0] : it[1], it[2], it[3]]; })]); });
    }
    c93_menuHtml = function () {
      var cur = location.pathname;
      return '<p class="c101b-h" aria-hidden="true">All sections</p><div class="c101b-cols">' + G.map(function (g) {
        var its = g[0] === "Account" && admin() ? g[1].concat([ADMIN]) : g[1];
        return '<div class="c101b-g"><h2>' + esc(g[0]) + "</h2><ul>" + its.map(function (it) {
          return '<li><a href="' + esc(it[1]) + '"' + (it[0] ? ' data-c93-nav="' + esc(it[0]) + '"' : "") + (it[1] === cur ? ' aria-current="page"' : "") + (it === ADMIN ? " data-c101b-admin" : "") + ">" + esc(it[2]) + '<span class="c93-menu-d">' + esc(it[3]) + "</span></a></li>";
        }).join("") + "</ul></div>";
      }).join("") + '</div><p class="c101b-note">Some pages are for signed-in readers or members; signed out, they show a sign-in or plans page.</p>';
    };
    var opener = null, tog0 = c93_menuToggle;
    c93_menuToggle = function (btn) {
      var m = document.getElementById("c93Menu");
      if (m && m.hidden) m.innerHTML = c93_menuHtml();     // rebuilt on every open, so the admin item follows the account
      var r = tog0.apply(this, arguments);
      m = document.getElementById("c93Menu");
      if (m) { m.classList.add("c101b-menu"); m.setAttribute("aria-label", "All sections"); if (!m.hidden) opener = btn; }
      return r;
    };
    document.addEventListener("keydown", function (e) {
      var m = document.getElementById("c93Menu");
      if (e.key === "Escape" && m && !m.hidden) { c93_menuClose(); if (opener) try { opener.focus(); } catch (e2) {} }
    }, true);
    document.addEventListener("focusin", function (e) {
      var m = document.getElementById("c93Menu");
      if (!m || m.hidden || m.contains(e.target) || (e.target.closest && e.target.closest("[aria-controls='c93Menu']"))) return;
      c93_menuClose();
    });
    var st = document.createElement("style");
    st.textContent = "html.c93 .c93-menu.c101b-menu{width:min(920px,calc(100vw - 32px))}" +
      "html.c93 .c93-menu .c101b-h{font:600 15px/1.2 var(--ui);color:var(--ink);margin:0 0 10px}" +
      "html.c93 .c93-menu .c101b-cols{columns:3 220px;column-gap:24px}html.c93 .c93-menu .c101b-g{break-inside:avoid;margin:0 0 12px}" +
      "html.c93 .c93-menu.c101b-menu ul{display:block}html.c93 .c93-menu.c101b-menu h2{margin:0 0 4px}" +
      "html.c93 .c93-menu .c101b-note{font:400 12px/1.4 var(--ui);color:var(--ink-3);margin:6px 0 0}" +
      "html.c93 .c93-menu a:focus-visible{outline:2px solid var(--gold);outline-offset:1px}" +
      "@media (max-width:767px){html.c93 .c93-menu.c101b-menu{width:auto;max-height:calc(100vh - 72px)}html.c93 .c93-menu .c101b-cols{columns:2 150px;column-gap:16px}html.c93 .c93-menu.c101b-menu .c93-menu-d{display:none}html.c93 .c93-menu.c101b-menu a{padding:9px 2px}}";
    (document.head || document.documentElement).appendChild(st);
  } catch (e) {}
  // /?open=intel and /?open=port (from /documents/ and /portfolio/holdings/): open that desk page once the account is known.
  try {
    var mo = /[?&]open=(intel|port)(?:&|$)/.exec(location.search);
    if (mo) {
      var t0 = Date.now(), iv = setInterval(function () {
        var ready = false; try { ready = !!_userTierReady; } catch (e) {}
        if (ready) {
          clearInterval(iv);
          try { history.replaceState(history.state, "", "/"); } catch (e) {}
          var vis = true; try { vis = _isVisitor(); } catch (e) {}
          if (!vis) setTimeout(function () { try { sbNav(mo[1]); } catch (e) {} }, 300);
        } else if (Date.now() - t0 > 15000) clearInterval(iv);
      }, 150);
    }
  } catch (e) {}
})();
