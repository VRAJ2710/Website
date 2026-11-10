// chat102: keep /terminal/ from being rewritten to Home, and list it in the desk menu.
(function () {
  try {
    if (typeof C93_MENU !== "undefined" && C93_MENU && C93_MENU.length) {
      for (var i = 0; i < C93_MENU.length; i++) {
        var g = C93_MENU[i];
        if (!g || g[0] !== "Markets and data" || !g[1]) continue;
        var exists = g[1].some(function (it) { return it && it[0] === "/terminal/"; });
        if (!exists) g[1].unshift(["/terminal/", "Terminal", "Gold futures, spot and the readings beside them"]);
      }
    }
  } catch (e) {}
  try {
    var path = String(location.pathname || "");
    if ((path === "/terminal" || path === "/terminal/") && !document.getElementById("c102")) {
      if (!sessionStorage.getItem("c102once")) {
        sessionStorage.setItem("c102once", "1");
        location.replace("/terminal/");
      }
    }
  } catch (e2) {}
})();
