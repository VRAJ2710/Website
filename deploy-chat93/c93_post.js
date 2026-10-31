// ═══════════════════════════════════════════════════════════
// chat93: credibility redesign runtime (header nav, Tools menu, plain-English text, lazy charts)
// ═══════════════════════════════════════════════════════════
function c93_loadCharts() {
  if (typeof LightweightCharts !== "undefined") return Promise.resolve(true);
  if (window.__c93ChartsP) return window.__c93ChartsP;
  window.__c93ChartsP = new Promise(function (resolve, reject) {
    var s = document.createElement("script");
    s.src = "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js";
    s.async = true;
    s.onload = function () { resolve(true); };
    s.onerror = function () { window.__c93ChartsP = null; reject(new Error("chart library failed to load")); };
    document.head.appendChild(s);
  });
  return window.__c93ChartsP;
}
var C93_MENU = [
  ["Read", [["brief", "Brief", "The daily view"], ["playbook", "Playbook", "Weekly gold and macro scenarios"], ["gold", "Gold", "Gold price, drivers and levels"], ["news", "News", "Market news with sources"], ["research", "Research", "Reports and the monitor"], ["/research/capital-sustainability", "Capital Sustainability Monitor", "What filings show about capital spending"]]],
  ["Markets and data", [["mkt", "Markets", "Prices across asset classes"], ["sig", "Signals", "What the indicators say"], ["sectors", "Sectors", "Sector moves"], ["heat", "Heatmap", "Moves at a glance"], ["crypto", "Crypto", "Bitcoin and other coins"], ["geo", "Geopolitical risk", "Energy and shipping risk"]]],
  ["Your tools", [["dash", "Dashboard", "Your overview"], ["watch", "Watchlist", "Companies you follow"], ["port", "Portfolio", "Track holdings"], ["paper", "Practice trading", "Paper portfolio, no real money"], ["scr", "Screener", "Filter companies"], ["lab", "Market Lab", "Charts and comparisons"], ["learn", "Academy", "Lessons and guides"]]],
  ["About us", [["/about", "About", "Who we are"], ["/methodology", "Methodology", "Where figures come from"], ["/editorial-standards", "Editorial standards", "How we write and check"], ["/corrections", "Corrections", "What we fixed"], ["/contact", "Contact", "Get in touch"], ["/pricing", "Pricing", "Free and Premium"]]]
];
function c93_href(id) {
  if (id.charAt(0) === "/") return id;
  try { if (typeof PUBLIC_NAV_PATHS !== "undefined" && PUBLIC_NAV_PATHS[id]) return PUBLIC_NAV_PATHS[id]; } catch (e) {}
  return "/" + id + "/";
}
function c93_esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
function c93_menuHtml() {
  return C93_MENU.map(function (g) {
    return "<h2>" + c93_esc(g[0]) + "</h2><ul>" + g[1].map(function (it) {
      var app = it[0].charAt(0) !== "/";
      return '<li><a href="' + c93_esc(c93_href(it[0])) + '"' + (app ? ' data-c93-nav="' + c93_esc(it[0]) + '"' : "") + ">" + c93_esc(it[1]) + '<span class="c93-menu-d">' + c93_esc(it[2]) + "</span></a></li>";
    }).join("") + "</ul>";
  }).join("");
}
function c93_menuClose() {
  var m = document.getElementById("c93Menu");
  if (m) m.hidden = true;
  document.querySelectorAll("[aria-controls='c93Menu']").forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
}
function c93_menuToggle(btn) {
  var m = document.getElementById("c93Menu");
  if (!m) {
    m = document.createElement("div");
    m.id = "c93Menu"; m.className = "c93-menu"; m.setAttribute("role", "dialog"); m.setAttribute("aria-label", "All pages and tools"); m.hidden = true;
    m.innerHTML = c93_menuHtml();
    document.body.appendChild(m);
  }
  var open = m.hidden;
  c93_menuClose();
  if (open) {
    var r = btn.getBoundingClientRect();
    m.style.top = Math.round(r.bottom + 8) + "px";
    m.hidden = false; btn.setAttribute("aria-expanded", "true");
    var a = m.querySelector("a"); if (a) try { a.focus({ preventScroll: true }); } catch (e) {}
  }
}
function c93_current() {
  var p = location.pathname.replace(/\/+$/, "/") || "/";
  var map = { "/brief/": "brief", "/gold/": "gold", "/markets/": "mkt", "/research/": "research", "/methodology/": "/methodology", "/about/": "/about" };
  if (p.indexOf("/research/") === 0) return "research";
  return map[p] || "";
}
function c93_markNav() {
  var cur = c93_current();
  document.querySelectorAll("#c93Nav a").forEach(function (a) {
    var id = a.getAttribute("data-c93-nav") || a.getAttribute("href");
    if (id === cur) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
}
document.addEventListener("click", function (e) {
  var t = e.target && e.target.closest ? e.target : null;
  if (!t) return;
  var btn = t.closest("[aria-controls='c93Menu']");
  if (btn) { e.preventDefault(); c93_menuToggle(btn); return; }
  var a = t.closest("a[data-c93-nav]");
  if (a) {
    var id = a.getAttribute("data-c93-nav");
    var visitor = true;
    try { visitor = typeof _isVisitor === "function" ? _isVisitor() : true; } catch (e2) {}
    c93_menuClose();
    if (!visitor && typeof sbNav === "function" && !(e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1)) {
      e.preventDefault();
      try { sbNav(id); setTimeout(c93_markNav, 50); } catch (e3) { location.href = a.href; }
    }
    return;
  }
  if (!t.closest("#c93Menu")) c93_menuClose();
}, true);
document.addEventListener("keydown", function (e) { if (e.key === "Escape") c93_menuClose(); });
window.addEventListener("popstate", function () { setTimeout(c93_markNav, 50); });

// Plain-English normaliser: rewrites leftover jargon and lone dash placeholders as they are rendered.
var C93_TEXT = [
  [/NO LIVE SYNC/g, "No current price"],
  [/\bNo live sync\b/g, "No current price"],
  [/\bUNAVAILABLE\b/g, "Not available"],
  [/Run Lens Engine on /g, "Open the research view for "],
  [/\bLens Engine\b/g, "research view"],
  [/\bDesk Run\b/g, "Daily check"],
  [/\bDESK RUN\b/g, "DAILY CHECK"],
  [/\bconviction-weighted\b/g, "evidence-weighted"],
  [/\bConviction-weighted\b/g, "Evidence-weighted"],
  [/\bCONVICTION-WEIGHTED\b/g, "EVIDENCE-WEIGHTED"],
  [/\b(RESEARCH|DISPATCH) TERMINAL\b/g, "THE DISPATCH MARKET"],
  [/\bThe Dispatch terminal\b/g, "The Dispatch Market"],
  [/\bDispatch Markets\b/g, "Dispatch Market"],
  [/\bTHE DISPATCH\b(?! MARKET)/g, "THE DISPATCH MARKET"],
  [/\bThe Dispatch\b(?! Market)/g, "The Dispatch Market"],
  [/\s*·\s*FREE DESK\s*·\s*MODEL \(NOT LLM\)/g, ""],
  [/Top desk score: [A-Z0-9.^-]+ \d+\/100 \(Dispatch desk score\)\.\s*/g, ""],
  [/\bMarkets closed\b/g, "Outside US stock hours"],
  [/\bmarkets closed\b/g, "outside US stock hours"],
  [/\bMARKETS CLOSED\b/g, "OUTSIDE US STOCK HOURS"]
];
var C93_DASH = /^\s*(?:[\u2014\u2013\-]{1,2}|\u2026|\$\u2014|\u2014%|[\u2014\u2013]\s*%|n\/a\u2014)\s*$/;
var C93_SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, OPTION: 1, CODE: 1, PRE: 1, NOSCRIPT: 1, svg: 1, SVG: 1 };
function c93_skip(el) {
  for (var n = el, i = 0; n && i < 40; n = n.parentNode, i++) {
    if (n.nodeType !== 1) continue;
    if (C93_SKIP[n.nodeName] || n.isContentEditable || (n.classList && n.classList.contains("c93-keep"))) return true;
    if (n.id === "raMsgs" || (n.classList && (n.classList.contains("ra-msgs") || n.classList.contains("cmd-ac")))) return true;
  }
  return false;
}
function c93_fixText(node) {
  var v = node.nodeValue, o = v;
  if (!v || v.length > 4000) return;
  for (var i = 0; i < C93_TEXT.length; i++) if (C93_TEXT[i][0].test(v)) { C93_TEXT[i][0].lastIndex = 0; v = v.replace(C93_TEXT[i][0], C93_TEXT[i][1]); }
  if (v !== o) node.nodeValue = v;
}
function c93_fixLeaf(el) {
  if (el.children.length || el.getAttribute("aria-hidden") === "true") return; // re-check c93-na too: the app re-renders dashes into the same element
  var t = el.textContent;
  if (!t || t.length > 6 || !C93_DASH.test(t)) return;
  if (/^(?:BUTTON|A|OPTION|LABEL)$/.test(el.nodeName)) return;
  el.textContent = "n/a";
  el.classList.add("c93-na");
  if (!el.title) el.title = "Not available from our free data feed right now";
}
function c93_walk(root) {
  if (!root) return;
  if (root.nodeType === 3) { if (root.parentNode && !c93_skip(root.parentNode)) { c93_fixText(root); if (root.parentNode && root.parentNode.nodeType === 1) c93_fixLeaf(root.parentNode); } return; }
  if (root.nodeType !== 1 || c93_skip(root)) return;
  var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n, leafs = [];
  while ((n = w.nextNode())) {
    var p = n.parentNode;
    if (!p || C93_SKIP[p.nodeName]) continue;
    c93_fixText(n);
    if (p.nodeType === 1 && !p.children.length) leafs.push(p);
  }
  for (var i = 0; i < leafs.length; i++) if (!c93_skip(leafs[i])) c93_fixLeaf(leafs[i]);
}
var c93_q = [], c93_raf = 0;
function c93_flush() {
  c93_raf = 0;
  var q = c93_q; c93_q = [];
  for (var i = 0; i < q.length; i++) { try { if (q[i].isConnected) c93_walk(q[i]); } catch (e) {} }
}
function c93_observe() {
  try {
    document.title = document.title.replace(/\bThe Dispatch\b(?! Market)/g, "The Dispatch Market");
    c93_walk(document.body);
    new MutationObserver(function (recs) {
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        if (r.type === "characterData") c93_q.push(r.target);
        else for (var j = 0; j < r.addedNodes.length; j++) c93_q.push(r.addedNodes[j]);
      }
      if (c93_q.length && !c93_raf) c93_raf = requestAnimationFrame(c93_flush);
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  } catch (e) {}
}
(function c93_boot() {
  var go = function () {
    c93_markNav();
    c93_observe();
    try { if (typeof _syncDeskChrome === "function") _syncDeskChrome(); } catch (e) {}
    try { document.documentElement.style.setProperty("--sidebar-w", "0px"); } catch (e) {}
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
