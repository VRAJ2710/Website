// chat98: server alerts and Portfolio X-ray appear only when their tables exist (/api/c98/status).
var _c98St = null;
function _c98Esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
function _c98Menu() {
  try {
    if (!_c98St || typeof C93_MENU === "undefined") return;
    var g = C93_MENU.filter(function (x) { return x[0] === "Your tools"; })[0]; if (!g) return;
    var add = [];
    if (_c98St.alerts && !g[1].some(function (x) { return x[0] === "/alerts/"; })) add.push(["/alerts/", "Alerts", "Gold, yields and release alerts"]);
    if (_c98St.portfolio && !g[1].some(function (x) { return x[0] === "/portfolio/"; })) add.push(["/portfolio/", "Portfolio X-ray", "How your mix leans on rates, gold and the dollar"]);
    if (!add.length) return;
    var pi = g[1].findIndex(function (x) { return x[0] === "port"; });
    Array.prototype.splice.apply(g[1], [pi >= 0 ? pi + 1 : g[1].length, 0].concat(add));
    var m = document.getElementById("c93Menu"); if (m && typeof c93_menuHtml === "function") m.innerHTML = c93_menuHtml();
  } catch (e) {}
}
function _c98Banner(n, msg) {
  if (document.getElementById("c98Alert")) return;
  var d = document.createElement("div"); d.id = "c98Alert"; d.className = "c98-alertbar"; d.setAttribute("role", "status");
  d.innerHTML = "<strong>" + (n > 1 ? n + " alerts" : "Alert") + "</strong> \u00b7 " + _c98Esc(msg) + ' <a href="/alerts/">See alerts</a> <button type="button" aria-label="Dismiss" data-c98-x>\u00d7</button>';
  document.body.insertBefore(d, document.body.firstChild);
  d.querySelector("[data-c98-x]").addEventListener("click", function () { d.remove(); try { sessionStorage.setItem("c98Dismiss", msg); } catch (e) {} });
}
function _c98Poll() {
  if (!_c98St || !_c98St.alerts || window._tdMePreview) return;
  fetch("/api/c98/alerts", { credentials: "same-origin", cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (!j || !j.unseen) return;
    var e = (j.events || []).filter(function (x) { return !x.seen; })[0]; if (!e) return;
    try { if (sessionStorage.getItem("c98Dismiss") === e.message) return; } catch (x) {}
    _c98Banner(j.unseen, e.message);
  }).catch(function () {});
}
(function () {
  var go = function () {
    fetch("/api/c98/status", { credentials: "same-origin", cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (s) {
      if (!s) return; _c98St = s; _c98Menu();
      setTimeout(_c98Poll, 3000); setInterval(_c98Poll, 5 * 60e3);
    }).catch(function () {});
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go); else go();
})();
