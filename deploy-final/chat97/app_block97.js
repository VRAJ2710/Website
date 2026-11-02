
// ── chat97: Light / Dark / System theme, saved on this device and (signed in) in your account settings ──
var C97_SCHEMES = ["light", "dark", "system"];
function _c97Cookie() { try { var m = /(?:^|;\s*)dispatch_theme=(light|dark|system)(?:;|$)/.exec(document.cookie || ""); return m ? m[1] : ""; } catch (e) { return ""; } }
function _c97Scheme() {
  var c = _c97Cookie(); if (c) return c;
  try { var l = localStorage.getItem("dispatch_theme"); if (C97_SCHEMES.indexOf(l) >= 0) return l; } catch (e) {}
  return "system";
}
function _c97IsDark(s) { return s === "dark" || (s === "system" && !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)); }
function _c97ApplyTheme(s) {
  if (C97_SCHEMES.indexOf(s) < 0) s = "system";
  var de = document.documentElement;
  C97_SCHEMES.forEach(function (x) { de.classList.toggle("c97-" + x, x === s); });
  try { var mt = document.querySelector('meta[name="theme-color"]:not([media])'); if (mt) mt.setAttribute("content", _c97IsDark(s) ? "#151b23" : "#fbfaf7"); } catch (e) {}
  try {
    document.querySelectorAll("[data-c97-tg] button[data-v]").forEach(function (b) { var on = b.getAttribute("data-v") === s; b.setAttribute("aria-pressed", on ? "true" : "false"); b.classList.toggle("on", on); });
    document.querySelectorAll("[data-c97-cycle]").forEach(function (b) { b.textContent = "Theme: " + s.charAt(0).toUpperCase() + s.slice(1); b.setAttribute("aria-label", "Theme: " + s + ". Change theme"); });
  } catch (e) {}
}
function _c97Store(s) {
  try { document.cookie = "dispatch_theme=" + s + "; Path=/; Max-Age=31536000; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : ""); } catch (e) {}
  try { localStorage.setItem("dispatch_theme", s); } catch (e) {}
}
function _c97SetScheme(s) {
  if (C97_SCHEMES.indexOf(s) < 0) return;
  _c97Store(s); _c97ApplyTheme(s);
  try { if (typeof _rt17Prefs === "object" && _rt17Prefs) { _rt17Prefs.display = _rt17Prefs.display || {}; _rt17Prefs.display.scheme = s; if (typeof _rt17Save === "function") _rt17Save(); } } catch (e) {}
  try { var ov = document.getElementById("settingsOv"); if (ov && ov.innerHTML && typeof _rt17Render === "function") _rt17Render(); } catch (e) {}
}
function _c97Cycle() { var s = _c97Scheme(), i = C97_SCHEMES.indexOf(s); _c97SetScheme(C97_SCHEMES[(i + 1) % 3]); }
// Signed in: the account's saved choice wins once it loads. Guests: this device's choice.
(function () {
  if (typeof _rt17Apply !== "function") return;
  var a0 = _rt17Apply;
  _rt17Apply = function () {
    var r = a0.apply(this, arguments);
    try {
      var sv = _rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.scheme;
      if (typeof _rt17Signed === "function" && _rt17Signed() && !window._tdMePreview && C97_SCHEMES.indexOf(sv) >= 0 && sv !== _c97Scheme()) { _c97Store(sv); _c97ApplyTheme(sv); }
    } catch (e) {}
    return r;
  };
})();
function _c97Header() {
  if (document.querySelector("[data-c97-tg]")) return;
  var s = _c97Scheme();
  var seg = '<div class="c97-tg" data-c97-tg role="group" aria-label="Colour theme">' + C97_SCHEMES.map(function (v) { return '<button type="button" data-v="' + v + '" aria-pressed="' + (v === s) + '" class="' + (v === s ? "on" : "") + '" onclick="_c97SetScheme(\'' + v + '\')">' + v.charAt(0).toUpperCase() + v.slice(1) + '</button>'; }).join("") + '</div>';
  var nav = document.getElementById("c93Nav");
  if (nav) nav.insertAdjacentHTML("afterend", seg);
  var mb = document.querySelector(".hdr .c93-menu-btn");
  if (mb) mb.insertAdjacentHTML("afterend", '<button type="button" class="c97-cyc" data-c97-cycle onclick="_c97Cycle()"></button>');
  _c97ApplyTheme(s);
}
// Guest preview: the app shows the same bar as the server pages, so an admin always knows what they are looking at.
function _c97PreviewBar() {
  if (!window._tdMePreview || document.querySelector("[data-c94-preview]")) return;
  var maint = !!window.__c97Maint;
  var d = document.createElement("div");
  d.setAttribute("role", "note"); d.setAttribute("data-c94-preview", "");
  d.className = "c97-pvbar";
  d.innerHTML = "<strong>Guest preview</strong> \u00b7 only administrators can see this. It shows the site as a signed-out reader sees it. Settings changes are not saved in preview. It ends after 30 minutes. <a href=\"?view=exit\">Exit preview</a>";
  document.body.insertBefore(d, document.body.firstChild);
}
(function () {
  var go = function () { try { _c97Header(); } catch (e) {} var n = 0, t = setInterval(function () { n++; try { if (window._tdMePreview) { _c97PreviewBar(); clearInterval(t); } } catch (e) {} if (n > 40) clearInterval(t); }, 500); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
  try { if (window.matchMedia) window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () { _c97ApplyTheme(_c97Scheme()); }); } catch (e) {}
})();
try { if (typeof C93_MENU !== "undefined" && C93_MENU[0] && C93_MENU[0][1]) { var _c97gi = C93_MENU[0][1].findIndex(function (x) { return x[0] === "gold"; }); C93_MENU[0][1].splice(_c97gi + 1, 0, ["/gold/dashboard/", "Gold dashboard", "Gold in \u00a3, $ and \u20ac, with what moves it"], ["/calendar/", "Macro calendar", "US and UK releases in UK time"]); } } catch (e) {}
