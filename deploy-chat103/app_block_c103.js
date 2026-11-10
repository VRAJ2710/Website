// chat103: keep /cpi/ in the desk menu, beside the other macro pages. Existing links stay in their existing order.
(function () {
  function pathOf(it) {
    if (!it || !it.length) return "";
    if (it.length >= 4 && typeof it[1] === "string" && it[1].charAt(0) === "/") return it[1];
    if (typeof it[0] === "string" && it[0].charAt(0) === "/") return it[0];
    return "";
  }
  function insert(list) {
    if (!list || !list.length) return;
    var i;
    for (i = 0; i < list.length; i++) if (pathOf(list[i]) === "/cpi/") return;
    var sample = null;
    for (i = 0; i < list.length; i++) if (list[i] && list[i].length) { sample = list[i]; break; }
    var row = sample && sample.length >= 4
      ? ["", "/cpi/", "CPI Day", "US inflation release, in UK time"]
      : sample && sample.length === 3
        ? ["/cpi/", "CPI Day", "US inflation release, in UK time"]
        : ["/cpi/", "CPI Day"];
    var at = -1;
    for (i = 0; i < list.length; i++) if (pathOf(list[i]) === "/terminal/") at = i;
    if (at >= 0) list.splice(at + 1, 0, row);
    else list.push(row);
  }
  try {
    if (typeof C101B_GROUPS !== "undefined" && C101B_GROUPS) {
      for (var g = 0; g < C101B_GROUPS.length; g++) {
        if (C101B_GROUPS[g] && C101B_GROUPS[g][0] === "Gold and macro") insert(C101B_GROUPS[g][1]);
      }
    }
  } catch (e) {}
  try {
    if (typeof window !== "undefined" && window.C101B_GROUPS) {
      for (var w = 0; w < window.C101B_GROUPS.length; w++) {
        if (window.C101B_GROUPS[w] && window.C101B_GROUPS[w][0] === "Gold and macro") insert(window.C101B_GROUPS[w][1]);
      }
    }
  } catch (e2) {}
  function groupWith(list, path) {
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      var items = list[i] && list[i][1];
      if (!items) continue;
      for (var j = 0; j < items.length; j++) if (pathOf(items[j]) === path) return items;
    }
    return null;
  }
  try {
    if (typeof C93_MENU !== "undefined" && C93_MENU) {
      var menuItems = groupWith(C93_MENU, "/terminal/");
      if (menuItems) insert(menuItems);
      else {
        for (var m = 0; m < C93_MENU.length; m++) {
          if (C93_MENU[m] && C93_MENU[m][0] === "Gold and macro") insert(C93_MENU[m][1]);
        }
      }
    }
  } catch (e3) {}
  try {
    if (typeof C93_NAV !== "undefined" && C93_NAV && !C93_NAV.some(function (x) { return x && x[0] === "/cpi/"; })) {
      var markets = -1, research = -1, n;
      for (n = 0; n < C93_NAV.length; n++) {
        if (C93_NAV[n] && C93_NAV[n][0] === "/markets/") markets = n;
        if (C93_NAV[n] && C93_NAV[n][0] === "/research/") research = n;
      }
      var item = ["/cpi/", "CPI Day"];
      if (markets >= 0) C93_NAV.splice(markets + 1, 0, item);
      else if (research >= 0) C93_NAV.splice(research, 0, item);
      else C93_NAV.push(item);
    }
  } catch (e4) {}
  try {
    var path = String(location.pathname || "");
    if ((path === "/cpi" || path === "/cpi/") && !document.getElementById("c103")) {
      if (!sessionStorage.getItem("c103once")) {
        sessionStorage.setItem("c103once", "1");
        location.replace("/cpi/");
      }
    }
  } catch (e5) {}
})();
