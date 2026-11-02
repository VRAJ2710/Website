
// ── chat101: "Check and plan" menu group; source inspector on the signed-in /gold/ and /brief/ figures; no raw ticker codes ──
(function () {
  try {
    if (typeof C93_MENU !== "undefined" && !C93_MENU.some(function (g) { return g[0] === "Check and plan"; })) {
      C93_MENU.splice(Math.min(3, C93_MENU.length), 0, ["Check and plan", [["/tools/verify/", "Verify a claim", "Supported, not supported or can't verify"], ["/tools/isa-sipp/", "ISA and SIPP planner", "Illustrative, not advice"], ["/tools/scenario/", "Gold scenarios", "Real yields, the dollar and gold"], ["/central-banks/", "Central banks", "Fed and BoE statements, redlined"], ["/research/filing-changes/", "Filing changes", "What companies changed in 10-Qs and 10-Ks"]]]);
      var m = document.getElementById("c93Menu"); if (m && typeof c93_menuHtml === "function") m.innerHTML = c93_menuHtml();
    }
  } catch (e) {}
  function T(e) { return e ? String(e.textContent || "").replace(/\s+/g, " ").trim() : ""; }
  function ukT(el) { var m = /(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d{1,2} [A-Z][a-z]{2},? \d{1,2}:\d{2} UK\b/.exec(T(el)); return m ? m[0] : "Time shown on the page"; }
  function when(el, part) { var a = null, x = el; while (x && x !== document.body && !(a = x.querySelector && x.querySelector(".gd-asof"))) x = x.parentElement; a = a || document.querySelector(".gd-asof"); if (!a) return "Shown under the price"; var b = (part && a.querySelector(part)) || a; var m = /as of ((?:(?!\u00b7|Spot \(|Futures \(|AI scenario).)+)/.exec(T(b)); return m ? m[1].trim() : "Shown under the price"; }
  function tag(el, o) {
    if (!el) return;
    if (el.getAttribute("data-c100")) { if (o.value && el.getAttribute("data-c100-value") !== o.value) el.setAttribute("data-c100-value", o.value); if (o.at) el.setAttribute("data-c100-at", o.at); return; }
    el.setAttribute("data-c100", "1"); el.classList.add("c101-fig"); el.setAttribute("tabindex", "0"); el.setAttribute("role", "button"); el.setAttribute("aria-haspopup", "dialog");
    el.setAttribute("title", "Show the source of this figure");
    Object.keys(o).forEach(function (k) { if (o[k]) el.setAttribute("data-c100-" + k, o[k]); });
  }
  var YF = "https://finance.yahoo.com/markets/";
  function deco() {
    try {
      var px = document.querySelector(".gd-px");
      if (px) tag(px, { name: "Gold price (US$ per troy ounce)", value: T(px), src: "Reference spot feed, with COMEX gold futures (front month) via Yahoo Finance for levels", url: YF, series: "Gold, US dollars per troy ounce", at: when(px, ".fe87-spot-src"), status: "Delayed: free feeds lag the market, usually by 15 to 20 minutes", formula: "Change = latest price \u2212 previous close" });
      [].forEach.call(document.querySelectorAll(".gd-macro-mini span"), function (s) {
        var b = s.querySelector("b"); if (!b) return; var k = T(s).split(" ")[0];
        var d = k === "DXY" ? ["US dollar index (ICE)", "ICE US Dollar Index, via Yahoo Finance", YF, "The dollar against six major currencies"] : k === "10Y" ? ["US 10-year Treasury yield", "US Treasury yield via Yahoo Finance", YF, "10-year US Treasury yield"] : k === "VIX" ? ["VIX volatility index (Cboe)", "Cboe VIX index, via Yahoo Finance", YF, "Expected 30-day volatility of the S&P 500"] : null;
        if (d) tag(b, { name: d[0], value: T(b), src: d[1], url: d[2], series: d[3], at: when(s, ".fe87-fut"), status: "Delayed: free feeds lag the market, usually by 15 to 20 minutes" });
      });
      [].forEach.call(document.querySelectorAll(".gd-levels .gd-chip"), function (c) {
        tag(c, { name: "Model level: " + (c.getAttribute("title") || "scenario level"), value: T(c), src: "The Dispatch Market model", url: "/methodology/", series: "Estimated from COMEX gold futures (front month) daily bars, Yahoo Finance, delayed", at: when(c, ".fe87-fut"), status: "Model output: an estimate, not a forecast or advice", formula: "Built from recent daily highs, lows and volatility" });
      });
      [].forEach.call(document.querySelectorAll(".gc-regime"), function (r) {
        var v = [].slice.call(r.querySelectorAll("div")).find(function (d) { var pv = d.previousElementSibling; return !d.children.length && /^\d{1,3}$/.test(T(d)) && pv && /^SCORE\b/i.test(T(pv)); }); if (!v) return;
        tag(v, { name: "Risk-appetite score (0 to 100)", value: T(v), src: "The Dispatch Market model", url: "/methodology/", series: "In-house gauge built from the market figures on this page", at: ukT(r), status: "Model output: lower means more risk-off", formula: "Weighted blend of price trends, volatility and breadth, scaled 0 to 100" });
      });
      [].forEach.call(document.querySelectorAll(".gc-regime .fe83f-regime-in"), function (d) {
        if (!/\d/.test(T(d))) return;
        tag(d, { name: "Market snapshot behind the score", value: T(d), src: "Yahoo Finance and Cboe index data", url: YF, series: "S&P 500 and VIX, last price and daily change", at: "Shown with each figure", status: "Delayed: free feeds lag the market, usually by 15 to 20 minutes" });
      });
      [].forEach.call(document.querySelectorAll(".openbb-customer-section .openbb-grid > div"), function (d) {
        var st = d.querySelector("strong"), sp = d.querySelector("span"); if (!st) return;
        var sec = d.closest(".openbb-customer-section"), meta = sec && sec.querySelector(".openbb-meta"), mt = T(meta);
        tag(st, { name: T(sp) || "Figure", value: T(st), src: mt.split(" \u00b7 ")[0] || "OpenBB research", url: "", series: mt.split(" \u00b7 ").slice(0, 2).join(" \u00b7 "), at: (/(?:through|as of) ([^\u00b7]+)/.exec(mt) || [])[1] || "Date shown on the page", status: "Not live: research data, dated as shown" });
      });
    } catch (e) {}
  }
  function clean(root) {
    try {
      var w = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, null), n, re = /\(GC=F([,)])/g;
      while ((n = w.nextNode())) if (n.nodeValue.indexOf("GC=F") >= 0 && !(n.parentNode && /^(SCRIPT|STYLE)$/.test(n.parentNode.nodeName))) n.nodeValue = n.nodeValue.replace(re, "(front month$1").replace(/\bgold futures GC=F\b/gi, "gold futures (front month)");
      [].forEach.call((root || document).querySelectorAll ? (root || document).querySelectorAll("[title*='GC=F'],[aria-label*='GC=F']") : [], function (e) { ["title", "aria-label"].forEach(function (a) { var v = e.getAttribute(a); if (v && v.indexOf("GC=F") >= 0) e.setAttribute(a, v.replace(re, "(front month$1")); }); });
    } catch (e) {}
  }
  var tm; function sch() { clearTimeout(tm); tm = setTimeout(function () { deco(); clean(document.body); }, 200); }
  document.addEventListener("keydown", function (e) { var t = e.target; if ((e.key === "Enter" || e.key === " ") && t && t.classList && t.classList.contains("c101-fig")) { e.preventDefault(); e.stopPropagation(); t.click(); } }, true);
  try { var st = document.createElement("style"); st.id = "c101-app-css"; st.textContent = ".c101-fig{cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px}.c101-fig:focus-visible{outline:2px solid #2563eb;outline-offset:2px;border-radius:2px}"; (document.head || document.documentElement).appendChild(st); } catch (e) {}
  if (document.readyState !== "loading") sch(); else document.addEventListener("DOMContentLoaded", sch);
  try { new MutationObserver(function () { sch(); }).observe(document.documentElement, { childList: true, subtree: true, characterData: true }); } catch (e) {}
})();
