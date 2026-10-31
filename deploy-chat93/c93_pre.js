/* chat93 (F): polling hygiene. Interval callbacks skip while the tab is hidden, and identical GET requests to the
   public market feeds below share one response for 60 seconds. Never applied to accounts, auth, billing, Ask or admin. */
(function () {
  try {
    var si = window.setInterval;
    if (si && !si.__c93) {
      var w = function (fn, ms) {
        if (typeof fn !== "function") return si.apply(window, arguments);
        var rest = Array.prototype.slice.call(arguments, 2);
        return si.call(window, function () { if (document.hidden) return; return fn.apply(this, rest.length ? rest : arguments); }, ms);
      };
      w.__c93 = 1; window.setInterval = w;
    }
  } catch (e) {}
  try {
    var of = window.fetch;
    if (typeof of !== "function" || of.__c93) return;
    var C = new Map();
    var ALLOW = /^\/api\/(?:yahoo-quote|finnhub|market-reference-quotes|ext-hours|twelve-data-quote|spot-energy|eia-spot|desk-quotes|crypto-snapshot|coingecko|rss-feed|news-scores|real-yield|regime|session-summary|geo|ai-status)(?:[\/?]|$)|^https:\/\/api\.gold-api\.com\//;
    var DENY = /\/(?:me|auth|ask|chat|admin|stripe|billing|prefs|account|create-checkout|monitor)(?:[\/?]|$)|__auth|__admin/;
    var f = function (input, init) {
      try {
        var m = (init && init.method) || (input && typeof input === "object" && input.method) || "GET";
        if (String(m).toUpperCase() !== "GET" || (init && init.body)) return of.apply(this, arguments);
        var url = typeof input === "string" ? input : (input && input.url) || String(input || "");
        var key = url;
        try { var u = new URL(url, location.href); key = u.origin === location.origin ? u.pathname + u.search : u.href; } catch (e) {}
        if (!ALLOW.test(key) || DENY.test(key)) return of.apply(this, arguments);
        var now = Date.now(), hit = C.get(key);
        if (hit && now - hit.t < 60000) return hit.p.then(function (r) { return r.clone(); });
        var p = of.apply(this, arguments).then(function (r) { if (!r || !r.ok) C.delete(key); return r; }, function (err) { C.delete(key); throw err; });
        C.set(key, { t: now, p: p });
        if (C.size > 150) C.delete(C.keys().next().value);
        return p.then(function (r) { return r.clone(); });
      } catch (e2) { return of.apply(this, arguments); }
    };
    f.__c93 = 1; window.fetch = f;
  } catch (e) {}
})();
