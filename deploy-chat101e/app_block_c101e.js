// ── chat101e: market cards on the signed-in Gold Dashboard ── the public pages' market-context renderer (chat96, copied
// in at build time from server.js) fills one detached table from the same quotes APIs; the rows are grouped (Gold and silver,
// Currencies, Rates, Energy, Crypto) exactly as on the public pages, each row gets its own venue's session label, and the
// result is painted into every copy of the Gold Dashboard (phone shell and desktop overlay). Cards below 600px, a table above.
// If the quotes fail, a plain note says so. Refreshes every 5 minutes while the Gold Dashboard is open.
(function () {
  try {
    if (window.__c101e || typeof renderGoldDesk !== "function") return; window.__c101e = 1;
    var KEYS = "gold,gold_gbp_oz,silver,dxy,gbpusd,eurusd,usdjpy,tnx,ry,wti,ng,btc,eth";
    var st = { html: "", state: "load", at: 0 }, busy = false, timer = null;
    function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
    function ny() {
      try {
        var p = {}; new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "long", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
          .formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
        return { d: p.weekday || "", t: Number(p.hour || 0) % 24 * 60 + Number(p.minute || 0) };
      } catch (e) { return { d: "", t: 0 }; }
    }
    function ses() {                                   // same rules as the server's c93SesClass (New York hours)
      var n = ny(), d = n.d, t = n.t;
      var us = /Monday|Tuesday|Wednesday|Thursday|Friday/.test(d) && t >= 570 && t < 960;
      var fut = (d === "Sunday" && t >= 1080) || (/Monday|Tuesday|Wednesday|Thursday/.test(d) && (t < 1020 || t >= 1080)) || (d === "Friday" && t < 1020);
      var wk = d === "Saturday" || (d === "Sunday" && t < 1080) || (d === "Friday" && t >= 1020);
      var shut = wk ? "closed for the weekend; prices are Friday's close" : "between sessions; prices are the last close";
      return { us: us, fut: fut, wk: wk, shut: shut };
    }
    function grp(t) { t = String(t || ""); return /^(gold|silver|platinum)/i.test(t) ? "M" : /crude|wti|brent|natural gas|oil/i.test(t) ? "Energy" : /bitcoin|ether|crypto|solana/i.test(t) ? "Crypto" : /yield|treasury|gilt|bank rate|interest/i.test(t) ? "Rates" : /dollar|pound|euro|yen|sterling/i.test(t) ? "Currencies" : /s&p|nasdaq|ftse|dow|stocks|equit|vix/i.test(t) ? "Stocks" : "Other"; }
    function venue(name, s) {
      var g = grp(name), tr = s.fut ? "trading, prices delayed" : s.shut;
      if (g === "M") return /^silver/i.test(name) ? "COMEX silver futures: " + tr : "Spot gold: " + (s.fut ? "trading" : s.shut);
      if (g === "Energy") return /futures/i.test(name) ? "NYMEX energy futures: " + tr : "Official daily price from the US EIA; NYMEX futures " + (s.fut ? "trading" : s.shut.replace(/;.*/, ""));
      if (g === "Currencies") return /Index/.test(name) ? "ICE dollar index futures: " + tr : "Currencies: " + (s.fut ? "trading" : s.shut);
      if (g === "Rates") return "Treasury yields: the latest daily figure";
      if (g === "Crypto") return "Crypto: trades every day";
      if (g === "Stocks") return "US shares: " + (s.us ? "open, prices delayed" : s.wk ? "closed for the weekend; prices are Friday's close" : "closed; prices are the last close");
      return "";
    }
    function finish(tb) {                              // group headings + venue labels, as the public cards show them
      var rows = Array.prototype.slice.call(tb.children), s = ses(), last = null;
      var silver = rows.some(function (r) { return /^silver/i.test(r.cells[0] && r.cells[0].firstChild ? r.cells[0].firstChild.textContent : ""); });
      rows.forEach(function (r) {
        var c = r.cells[0]; if (!c) return; var name = c.firstChild ? c.firstChild.textContent : c.textContent;
        var v = venue(name, s), sc = r.querySelector("td.src");
        if (v && sc) { var sp = document.createElement("span"); sp.className = "c101e-ses"; sp.textContent = v; sc.appendChild(sp); }
        var g = grp(name); if (g === "M") g = silver ? "Gold and silver" : "Gold"; if (g === last) return; last = g;
        var h = document.createElement("tr"); h.className = "c101c-gh"; var th = document.createElement("th"); th.colSpan = 4; th.scope = "colgroup"; th.textContent = g; h.appendChild(th); tb.insertBefore(h, r);
      });
      return rows.length;
    }
    function body() {
      if (st.state === "load") return '<p class="c101e-note">Loading the latest market levels\u2026</p>';
      if (st.state === "fail") return '<p class="c101e-note" role="status">Market prices are not available right now. We will try again in a few minutes; the rest of the Gold Dashboard is unaffected.</p>';
      return '<table class="ctx c101e-t"><thead><tr><th scope="col">Measure</th><th scope="col" class="n">Level</th><th scope="col" class="n">Change</th><th scope="col" class="src">Source, as of (UK)</th></tr></thead><tbody>' + st.html + "</tbody></table>" +
        (st.miss ? '<p class="c101e-note">Some prices are delayed; where a feed is quiet we show the last known figure with its time.</p>' : "");
    }
    function section() {
      return '<section class="gc c101e-mk" aria-labelledby="c101e-h"><h2 id="c101e-h" class="c101e-h">Market context</h2>' +
        '<p class="c101e-dek">Gold, silver, currencies, rates, energy and crypto from free public feeds, delayed. Where a market is shut we show its last close. Not investment advice.</p>' +
        '<div class="c101e-b" aria-live="polite">' + body() + "</div></section>";
    }
    function paint() { Array.prototype.forEach.call(document.querySelectorAll(".c101e-mk .c101e-b"), function (b) { b.innerHTML = body(); }); }
    function load() {
      if (busy) return; busy = true;
      var root = document.createElement("div");
      root.innerHTML = '<section data-need hidden><table class="ctx"><tbody data-rows="' + KEYS + '"><tr><td>\u2026</td></tr></tbody></table><p class="c93miss" hidden></p></section>';
      var tb = root.querySelector("tbody"), done = false;
      function end(ok) {
        if (done) return; done = true; busy = false;
        try {
          var n = ok ? finish(tb) : 0;
          if (n) { st.html = tb.innerHTML; st.state = "ok"; st.miss = !root.querySelector(".c93miss").hidden; st.at = Date.now(); }
          else if (!st.html) st.state = "fail";
        } catch (e) { if (!st.html) st.state = "fail"; }
        paint();
      }
      var mo = new MutationObserver(function () { mo.disconnect(); end(true); });
      mo.observe(tb, { childList: true });
      setTimeout(function () { mo.disconnect(); end(false); }, 15000);
      try { __C101E_RENDER__(root); } catch (e) { mo.disconnect(); end(false); }
    }
    function tick() { try { if (typeof pg !== "undefined" && pg === "gold" && document.querySelector(".c101e-mk") && Date.now() - st.at > 3e5) load(); } catch (e) {} }
    var orig = renderGoldDesk;
    renderGoldDesk = function () {
      var h = orig.apply(this, arguments), sec = section();
      if (!timer) { timer = setInterval(tick, 60000); setTimeout(load, 0); }
      var i = h.indexOf('<div class="gc');                    // after the page header, before the first card
      return i > 0 ? h.slice(0, i) + sec + h.slice(i) : h + sec;
    };
    var css = document.createElement("style");
    css.textContent =
      ".c101e-mk{margin:0 0 14px;padding:16px;box-sizing:border-box;max-width:100%;overflow:hidden}" +
      ".c101e-mk .c101e-h{margin:0 0 6px;font:600 17px/1.3 var(--ui,var(--sans,system-ui));color:var(--ink,inherit)}" +
      ".c101e-mk .c101e-dek,.c101e-mk .c101e-note{margin:0 0 10px;font:400 13px/1.45 var(--ui,var(--sans,system-ui));color:var(--ink-3,var(--muted,#555))}" +
      ".c101e-mk table.ctx{width:100%;border-collapse:collapse;font:400 14px/1.4 var(--ui,var(--sans,system-ui));color:var(--ink,inherit)}" +
      ".c101e-mk table.ctx th{text-align:left;font-weight:600;font-size:12px;color:var(--ink-3,var(--muted,#555));padding:6px 8px;border-bottom:1px solid var(--rule-2,var(--rule,#ccc))}" +
      ".c101e-mk table.ctx td{padding:8px;border-bottom:1px solid var(--rule-2,var(--rule,#ddd));vertical-align:top}" +
      ".c101e-mk table.ctx .n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}" +
      ".c101e-mk table.ctx td.src{font-size:12px;color:var(--ink-3,var(--muted,#555))}" +
      ".c101e-mk .msrc{display:none}.c101e-mk .c101e-ses{display:block;margin-top:2px}" +
      ".c101e-mk table.ctx tr.c101c-gh th{padding:12px 8px 4px;border-bottom:0;font-size:12px;letter-spacing:.06em;text-transform:uppercase}" +
      "@media (max-width:599px){.c101e-mk{padding:14px 12px}.c101e-mk table.ctx,.c101e-mk table.ctx tbody{display:block;width:100%}" +
      ".c101e-mk table.ctx thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}" +
      ".c101e-mk table.ctx tr.c101c-gh{display:block}.c101e-mk table.ctx tr.c101c-gh th{display:block;padding:14px 2px 6px;text-align:left}" +
      ".c101e-mk table.ctx tbody tr.c101c-gh:first-child th{padding-top:2px}" +
      ".c101e-mk table.ctx tbody tr:not(.c101c-gh){display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:'name val' 'name chg' 'src src';column-gap:14px;row-gap:2px;align-items:start;" +
      "margin:0 0 8px;padding:12px 14px;border:1px solid var(--rule-2,var(--rule,#ddd));border-radius:6px;background:var(--paper,transparent);box-sizing:border-box}" +
      ".c101e-mk table.ctx tbody tr:not(.c101c-gh)>td{display:block;padding:0;border:0;min-width:0}" +
      ".c101e-mk table.ctx tbody tr>td:nth-child(1){grid-area:name;font-weight:600;font-size:15px;overflow-wrap:anywhere}" +
      ".c101e-mk table.ctx tbody tr>td:nth-child(2){grid-area:val;text-align:right;font-weight:600;font-size:16px}" +
      ".c101e-mk table.ctx tbody tr>td:nth-child(3){grid-area:chg;text-align:right;font-size:13px;white-space:normal}" +
      ".c101e-mk table.ctx tbody tr>td.src{grid-area:src;margin-top:6px;overflow-wrap:anywhere}}";
    (document.head || document.documentElement).appendChild(css);
  } catch (e) {}
})();
function __C101E_RENDER__(ROOT) {
__RENDERER__
}
