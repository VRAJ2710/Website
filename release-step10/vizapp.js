/* chat115vizapp: shows the approved chat114viz Market Snapshot layer (same markup, same data, same viz.js) to signed-in readers
   inside the member app on /brief/, /gold/, /markets/ and /research/. It only adds one <section id="chat114viz"> at the top of the
   visible page body (#main on phones; on desktop the page's overlay body, or the prices panel for markets) and removes it on any
   other route. It does not
   change, move or hide anything the app draws. Any error stops this script and leaves the app as it was. Not investment advice. */
(function () {
  "use strict";
  if (window.__chat115vizapp) return; window.__chat115vizapp = 1;
  try {
    var PAGES = { brief: 1, gold: 1, markets: 1, research: 1 };
    var VIZ_JS = "/__chat114viz/viz.js?v=chat114viz", FRESH_MS = 5 * 60 * 1000;
    var cache = {}, loading = null, dead = false, queued = false, errors = 0;
    var D = document, de = D.documentElement;
    function routePage() {
      var m = /^\/(brief|gold|markets|research)\/?$/.exec(location.pathname || "");
      return m && PAGES[m[1]] ? m[1] : null;
    }
    function visible(el) { return !!(el && el.isConnected && el.getClientRects().length && el.offsetWidth > 0); }
    // Where the app draws the page the reader sees: phones use #main; on desktop brief, gold and research open in their overlay
    // (#briefOv, #goldOv, #researchOv, body .term-overlay-body) and markets is the expanded prices panel (#p1body).
    var OV = { brief: "briefOv", gold: "goldOv", research: "researchOv" };
    function target(page) {
      var ov = OV[page] && D.getElementById(OV[page]);
      if (ov && visible(ov)) { var ob = ov.querySelector(".term-overlay-body"); if (ob && visible(ob)) return ob; }
      var main = D.getElementById("main"); if (visible(main)) return main;
      if (page === "markets") { var p1 = D.getElementById("p1body"); if (visible(p1)) return p1; }
      return null;
    }
    function setClasses(page) {
      ["brief", "gold", "markets", "research"].forEach(function (p) { if (p !== page) de.classList.remove("cz-" + p); });
      if (page) { de.classList.add("cz-on"); de.classList.add("cz-" + page); } else de.classList.remove("cz-on");
    }
    function strays(keep) {
      var all = D.querySelectorAll("#chat114viz");
      for (var i = 0; i < all.length; i++) if (all[i] !== keep && all[i].parentNode) all[i].parentNode.removeChild(all[i]);
    }
    function build(page) {
      var s = D.createElement("section");
      s.id = "chat114viz"; s.className = "cz-root cz-app"; s.setAttribute("data-cz-page", page);
      s.setAttribute("aria-label", "Market snapshot and key figures");
      s.innerHTML = '<p class="cz-loading">Loading the market snapshot from this site\u2019s free feeds\u2026</p>';
      return { el: s, t: Date.now(), ran: false };
    }
    function run(entry) {
      // viz.js draws into the element with id="chat114viz" that is in the page when it runs; it runs once per load, so it is
      // re-run (same cached file) for each new snapshot. Only one run at a time.
      if (loading || entry.ran) return;
      entry.ran = true; loading = entry;
      var sc = D.createElement("script");
      sc.src = VIZ_JS; sc.async = true;
      sc.onload = sc.onerror = function () { loading = null; if (sc.parentNode) sc.parentNode.removeChild(sc); schedule(); };
      try { window.__chat114viz = 0; } catch (e) {}
      (D.head || de).appendChild(sc);
    }
    function ensure() {
      queued = false;
      if (dead) return;
      try {
        var page = routePage();
        if (!page) { strays(null); setClasses(null); return; }
        var t = target(page); if (!t) { strays(null); return; }
        var e = cache[page];
        if (!e || (e.el.parentNode !== t && Date.now() - e.t > FRESH_MS && !loading)) { e = cache[page] = build(page); }
        if (e.el.parentNode !== t || t.firstElementChild !== e.el) {
          if (loading && loading !== e && loading.el.isConnected) return; // let a pending draw finish first
          t.insertBefore(e.el, t.firstChild);
        }
        strays(e.el); setClasses(page);
        if (!e.ran) run(e);
        else if (!loading && !e.el.getAttribute("data-cz-ready") && e.el.querySelector(".cz-loading") && Date.now() - e.t > 20000 && !e.retried) { e.retried = true; e.ran = false; run(e); }
      } catch (err) {
        if (++errors >= 3) stop();
      }
    }
    function schedule() { if (queued || dead) return; queued = true; (window.requestAnimationFrame || setTimeout)(ensure, 16); }
    var mo = null, iv = null;
    function stop() {
      dead = true;
      try { if (mo) mo.disconnect(); } catch (e) {}
      try { clearInterval(iv); } catch (e) {}
      try { strays(null); setClasses(null); } catch (e) {}
    }
    ["pushState", "replaceState"].forEach(function (k) {
      var o = history[k]; if (typeof o !== "function") return;
      history[k] = function () { var r = o.apply(this, arguments); try { schedule(); } catch (e) {} return r; };
    });
    window.addEventListener("popstate", schedule);
    window.addEventListener("resize", schedule);
    function start() {
      try { mo = new MutationObserver(schedule); mo.observe(D.body, { childList: true, subtree: true }); } catch (e) {}
      iv = setInterval(schedule, 2000);
      schedule();
    }
    if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", start); else start();
  } catch (e) {}
})();
