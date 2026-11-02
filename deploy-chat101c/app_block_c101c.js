// ── chat101c: calmer menu ── "Menu" and "All sections" open one full-screen sheet with a solid background and a close
// button: one column, each group a tap-to-expand heading (aria-expanded / aria-controls) in the old All sections style;
// only the group with the current page starts open (front page: all closed). Body scroll is locked while it is open;
// Escape and the close button shut it and focus returns to the button that opened it. "Your desk" / "Sign in" sits at
// the top and the sign-in note is small at the bottom. Every chat101b link is kept; Admin Console stays admin-only.
(function () {
  try {
    var G = window.C101B_GROUPS; if (!G || typeof c93_menuHtml !== "function") return;
    var ADMIN = ["", "/__admin", "Admin Console", "Admin only"];
    var NOTE = "Some pages are for signed-in readers or members; signed out, they show a sign-in or plans page.";
    function admin() { try { return typeof _userAdmin !== "undefined" && _userAdmin === true && !window._tdMePreview; } catch (e) { return false; } }
    function visitor() { try { return typeof _isVisitor === "function" ? !!_isVisitor() : true; } catch (e) { return true; } }
    function esc(s) { return typeof c93_esc === "function" ? c93_esc(s) : String(s == null ? "" : s); }
    function items(g) { return g[0] === "Account" && admin() ? g[1].concat([ADMIN]) : g[1]; }
    function curGroup() {
      var p = location.pathname || "/", id = "", i, j, best = -1, bl = 0;
      try { id = typeof pg !== "undefined" && pg ? String(pg) : ""; } catch (e) {}
      if (p === "/") return -1;                    // the front page starts with every group closed
      for (i = 0; i < G.length; i++) for (j = 0; j < G[i][1].length; j++) if (G[i][1][j][1] === p) return i;
      if (id) for (i = 0; i < G.length; i++) for (j = 0; j < G[i][1].length; j++) if (G[i][1][j][0] === id) return i;
      for (i = 0; i < G.length; i++) for (j = 0; j < G[i][1].length; j++) { var h = G[i][1][j][1]; if (h.length > 1 && h.charAt(h.length - 1) === "/" && p.indexOf(h) === 0 && h.length > bl) { best = i; bl = h.length; } }
      return best;
    }
    window.c101cCurGroup = curGroup;
    function link(it, cur) {
      return '<li><a href="' + esc(it[1]) + '"' + (it[0] ? ' data-c93-nav="' + esc(it[0]) + '"' : "") + (it[1] === cur ? ' aria-current="page"' : "") +
        (it === ADMIN ? " data-c101b-admin" : "") + ' title="' + esc(it[3]) + '">' + esc(it[2]) + "</a></li>";
    }
    var X = '<button type="button" class="c101c-x" aria-label="Close menu"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>';
    c93_menuHtml = function () {
      var cur = location.pathname, on = curGroup(), keep = null, m0 = document.getElementById("c93Menu");
      if (m0 && !m0.hidden && m0.querySelector(".c101c-btn")) {   // rebuilt while open (account data arrived): keep what is open and where focus is
        keep = [].map.call(m0.querySelectorAll(".c101c-btn"), function (b) { return b.getAttribute("aria-expanded") === "true"; });
        var ae = document.activeElement, fk = ae && m0.contains(ae) ? (ae.id ? "#" + ae.id : ae.classList.contains("c101c-x") ? ".c101c-x" : ae.getAttribute("href") ? 'a[href="' + ae.getAttribute("href") + '"]' : ".c101c-x") : null;
        if (fk) (window.queueMicrotask || function (f) { Promise.resolve().then(f); })(function () { var m = document.getElementById("c93Menu"), f = m && !m.hidden && m.querySelector(fk); if (f && !m.contains(document.activeElement)) try { f.focus({ preventScroll: true }); } catch (e) {} });  // a microtask, so focus is back before the next key press
      }
      var top = visitor() ? '<a class="c101c-cta" href="/__auth/login">Sign in</a>' : '<a class="c101c-cta" href="/dashboard/" data-c93-nav="dash">Your desk</a>';
      return '<div class="c101c-bar"><span class="c101c-title">All sections</span>' + X + '</div><div class="c101c-in"><div class="c101c-top">' + top + '</div><div class="c101c-acc">' + G.map(function (g, gi) {
        var its = items(g), o = keep && gi < keep.length ? keep[gi] : gi === on;
        return '<div class="c101c-sec"><h2 class="c101c-hd"><button type="button" class="c101c-btn" id="c101c-ab' + gi + '" aria-expanded="' + o + '" aria-controls="c101c-al' + gi + '">' +
          '<span class="c101c-t">' + esc(g[0]) + '</span><span class="c101c-n"><span class="c101c-vh">, </span>' + its.length + '<span class="c101c-vh"> links</span></span><span class="c101c-ch" aria-hidden="true"></span></button></h2>' +
          '<ul id="c101c-al' + gi + '" aria-labelledby="c101c-ab' + gi + '"' + (o ? "" : " hidden") + ">" + its.map(function (it) { return link(it, cur); }).join("") + "</ul></div>";
      }).join("") + '</div><p class="c101c-note">' + NOTE + "</p></div>";
    };
    var opener = null, H = document.documentElement;
    function lock(on) { H.classList.toggle("c101c-lock", !!on); }
    var tog1 = c93_menuToggle;
    c93_menuToggle = function (btn) {
      var m0 = document.getElementById("c93Menu"), wasHidden = !m0 || m0.hidden;
      var r = tog1.apply(this, arguments);
      var m = document.getElementById("c93Menu");
      if (m) {
        if (wasHidden && !m.querySelector(".c101c-bar")) m.innerHTML = c93_menuHtml();
        m.classList.add("c101c-sheet"); m.setAttribute("aria-modal", "true");
        if (!m.hidden) { opener = btn; lock(true); var f = m.querySelector(".c101c-x"); if (f) try { f.focus({ preventScroll: true }); } catch (e) {} }
        else lock(false);
      }
      return r;
    };
    var close0 = c93_menuClose;
    c93_menuClose = function () { var r = close0.apply(this, arguments); lock(false); return r; };
    function visibleOpener() {
      if (opener && opener.offsetParent !== null) return opener;
      return [].slice.call(document.querySelectorAll("[aria-controls='c93Menu']")).filter(function (e) { return e.offsetParent !== null; })[0] || opener;
    }
    document.addEventListener("click", function (e) {
      var t = e.target && e.target.closest ? e.target : null; if (!t) return;
      if (t.closest("#c93Menu .c101c-x")) { e.preventDefault(); c93_menuClose(); var o = visibleOpener(); if (o) try { o.focus(); } catch (e2) {} return; }
      var b = t.closest("#c93Menu .c101c-btn"); if (!b) return;
      e.preventDefault();
      var l = document.getElementById(b.getAttribute("aria-controls")), on = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", on ? "true" : "false"); if (l) { if (on) l.removeAttribute("hidden"); else l.setAttribute("hidden", ""); }
    });
    window.addEventListener("keydown", function (e) {   // Escape: close, then focus the menu button even if the header was re-rendered
      var m = document.getElementById("c93Menu"); if (e.key !== "Escape" || !m || m.hidden) return;
      c93_menuClose(); var o = visibleOpener(); if (o) try { o.focus(); } catch (e2) {}
    }, true);
    window.addEventListener("keydown", function (e) {   // Tab stays in the sheet (it is modal)
      var m = document.getElementById("c93Menu"); if (!m || m.hidden || e.key !== "Tab") return;
      var f = [].filter.call(m.querySelectorAll("a[href],button"), function (z) { return z.offsetParent !== null; }); if (!f.length) return;
      var a = document.activeElement, inM = a && m.contains(a);
      if (!inM || (e.shiftKey && a === f[0]) || (!e.shiftKey && a === f[f.length - 1])) { e.preventDefault(); (e.shiftKey ? f[f.length - 1] : f[0]).focus(); }
    }, true);
    window.addEventListener("focusin", function (e) {   // focus never wanders behind the open sheet; bring it back instead of closing
      var m = document.getElementById("c93Menu"), t = e.target;
      if (!m || m.hidden || !t || t === window || t === document || m.contains(t)) return;
      e.stopImmediatePropagation(); var x = m.querySelector(".c101c-x"); if (x) try { x.focus({ preventScroll: true }); } catch (e2) {}
    }, true);
    var st = document.createElement("style");
    st.textContent =
      "html.c93 .c93-menu.c101c-sheet{position:fixed;top:0!important;right:0;bottom:0;left:0;width:auto;height:100vh;height:100dvh;max-height:none;margin:0;padding:0;z-index:2000;" +
      "background:var(--paper);color:var(--ink);border:0;border-radius:0;box-shadow:none;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;box-sizing:border-box}" +
      "html.c93 .c93-menu.c101c-sheet[hidden]{display:none!important}" +
      "html.c101c-lock,html.c101c-lock body{overflow:hidden!important}" +
      "html.c93 .c93-menu .c101c-bar{position:sticky;top:0;z-index:1;display:flex;align-items:center;justify-content:space-between;gap:12px;height:60px;padding:0 20px;background:var(--paper);border-bottom:1px solid var(--rule-2);box-sizing:border-box}" +
      "html.c93 .c93-menu .c101c-title{font:600 15px/1.2 var(--ui);color:var(--ink)}" +
      "html.c93 .c93-menu .c101c-x{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;margin:0 -6px 0 0;padding:0;background:var(--paper);color:var(--ink);border:1px solid var(--rule-2);border-radius:4px;cursor:pointer}" +
      "html.c93 .c93-menu .c101c-x:hover{border-color:var(--ink)}html.c93 .c93-menu .c101c-x:focus-visible{outline:2px solid var(--gold);outline-offset:2px}" +
      "html.c93 .c93-menu .c101c-in{max-width:640px;margin:0 auto;padding:16px 20px 40px;box-sizing:border-box}" +
      "html.c93 .c93-menu .c101c-top{margin:0 0 18px}" +
      "html.c93 .c93-menu.c101b-menu a.c101c-cta{display:block;min-height:46px;box-sizing:border-box;padding:13px 16px;text-align:center;font:600 15px/1.25 var(--ui);background:var(--ink);color:var(--paper)!important;border:1px solid var(--ink);border-radius:4px}" +
      "html.c93 .c93-menu.c101b-menu a.c101c-cta:hover{opacity:.92;color:var(--paper)!important}" +
      "html.c93 .c93-menu .c101c-sec{border-bottom:1px solid var(--rule-soft)}html.c93 .c93-menu .c101c-sec:first-child{border-top:1px solid var(--rule-soft)}" +
      "html.c93 .c93-menu.c101b-menu h2.c101c-hd{margin:0;padding:0;font:inherit;letter-spacing:0;text-transform:none}" +
      "html.c93 .c93-menu .c101c-btn{display:flex;align-items:center;width:100%;min-height:52px;box-sizing:border-box;margin:0;padding:0 2px;background:transparent;border:0;border-radius:0;" +
      "color:var(--ink-3);font:600 12px/1.2 var(--ui);letter-spacing:.06em;text-transform:uppercase;text-align:left;cursor:pointer;-webkit-tap-highlight-color:transparent}" +
      "html.c93 .c93-menu .c101c-btn:hover,html.c93 .c93-menu .c101c-btn[aria-expanded=true]{color:var(--ink)}" +
      "html.c93 .c93-menu .c101c-btn:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}" +
      "html.c93 .c93-menu .c101c-t{flex:1 1 auto}" +
      "html.c93 .c93-menu .c101c-n{flex:0 0 auto;font:500 12px/1 var(--ui);letter-spacing:0;color:var(--ink-3);min-width:22px;text-align:right;font-variant-numeric:tabular-nums}" +
      "html.c93 .c93-menu .c101c-ch{flex:0 0 auto;width:7px;height:7px;margin:-4px 6px 0 14px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);transition:transform .15s ease}" +
      "html.c93 .c93-menu .c101c-btn[aria-expanded=true] .c101c-ch{transform:rotate(-135deg);margin-top:4px}" +
      "html.c93 .c93-menu.c101b-menu .c101c-acc ul{display:block;margin:0 0 10px;padding:0;list-style:none}html.c93 .c93-menu .c101c-acc ul[hidden]{display:none!important}" +
      "html.c93 .c93-menu.c101b-menu .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;padding:10px 4px;border:0;border-top:1px solid var(--rule-soft);font:500 15px/1.3 var(--ui)}" +
      "html.c93 .c93-menu .c101c-acc a[aria-current=page]{font-weight:600;color:var(--gold)!important;box-shadow:inset 2px 0 0 var(--gold);padding-left:12px}" +
      "html.c93 .c93-menu p.c101c-note{font:400 12px/1.45 var(--ui);color:var(--ink-3);margin:18px 0 0}" +
      ".c101c-vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}" +
      "@media (prefers-reduced-motion:reduce){html.c93 .c93-menu .c101c-ch{transition:none}}";
    (document.head || document.documentElement).appendChild(st);
  } catch (e) {}
})();
