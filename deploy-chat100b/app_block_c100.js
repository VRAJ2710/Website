
// ── chat100 ──
// Dashboard: gold and macro readings first (plain names, source and UK time under each, tap for the source inspector).
// Fear & Greed: a calm "Not enough data yet" state instead of a 50/100 placeholder while inputs are missing.
var C100_DEF = ["XAU", "SLV", "GBPUSD", "DXY", "TNX", "BRENT", "SPX"];
var C100_NM = { XAU: "Gold", SLV: "Silver", XAG: "Silver", GBPUSD: "Pound in dollars", EURUSD: "Euro in dollars", USDJPY: "Dollar in yen", DXY: "US dollar index", TNX: "US 10-year yield",
  BRENT: "Brent crude", WTI: "WTI crude", NG: "US natural gas", SPX: "S&P 500", DJIA: "Dow Jones", IXIC: "Nasdaq Composite", VIX: "Volatility index (VIX)", BTC: "Bitcoin", ETH: "Ether", SOL: "Solana",
  SPY: "S&P 500 fund", QQQ: "Nasdaq-100 fund", FTSE: "FTSE 100", DAX: "DAX", N225: "Nikkei 225" };
function _c100Nm(tk) {
  tk = String(tk || ""); if (C100_NM[tk]) return C100_NM[tk];
  try { var a = (typeof A !== "undefined" ? A : []).find(function (x) { return x.tk === tk; }); if (a && a.nm) return String(a.nm); } catch (e) {}
  return tk;
}
function _c100IsDef(book) { try { var b = (book || []).slice().sort().join(","); return b === C100_DEF.slice().sort().join(","); } catch (e) { return false; } }
var _c100M = null, _c100MAt = 0, _c100MLoading = false;
function _c100Esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
function _c100Hm(t) { try { return new Date(t).toLocaleTimeString("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit" }); } catch (e) { return ""; } }
function _c100Saved() { try { var s = JSON.parse(localStorage.getItem("c100macro") || "null"); if (s && Array.isArray(s.rows) && Date.now() - s.at < 864e5) return { rows: s.rows, at: s.at, stale: true }; } catch (e) {} return null; }
function _c100Paint() { try { var el = document.getElementById("c100-macro"); if (el) el.outerHTML = _c100MacroHtml(); } catch (e) {} }
function _c100LoadMacro() {
  if (_c100MLoading || Date.now() - _c100MAt < 60e3) return;
  _c100MLoading = true;
  var fail = function () { if (!_c100M || _c100M.stale) _c100M = _c100Saved() || _c100M; };
  fetch("/api/c100/macro", { credentials: "same-origin", signal: AbortSignal.timeout(10000) }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (j && j.available && Array.isArray(j.rows) && j.rows.length) { _c100M = { rows: j.rows, at: Date.now(), stale: false }; try { localStorage.setItem("c100macro", JSON.stringify(_c100M)); } catch (e) {} }
    else fail();
  }).catch(fail).finally(function () { _c100MLoading = false; _c100MAt = Date.now(); _c100Paint(); });
}
function _c100MacroHtml() {
  try { if (!_c100M) _c100M = _c100Saved(); } catch (e) {}
  var m = _c100M, h = '<section class="c100-macro" id="c100-macro" aria-label="Gold and macro">';
  h += '<div class="c100-m-head"><div class="book-section-lbl">Gold and macro</div><span class="c100-m-sub">Tap a figure for its source</span></div>';
  if (!m || !m.rows || !m.rows.length) h += '<div class="c100-m-empty" role="status">Updating…</div>';
  else {
    h += '<div class="c100-grid" role="list">';
    m.rows.forEach(function (r) {
      var at = m.stale ? "Last known, saved " + _c100Hm(m.at) + " UK" : r.asOf, st = m.stale ? "Last known: the feed did not answer, so this is the last reading saved at " + _c100Hm(m.at) + " UK" : (r.status === "Delayed" ? "Delayed: free feeds lag the market, usually by 15 to 20 minutes" : "Official print: published once a day, dated as shown");
      var chc = /^\+/.test(r.change || "") ? "px-up" : /^[−-]/.test(r.change || "") ? "px-dn" : "px-flat";
      h += '<button type="button" role="listitem" class="c100-tile" data-c100 aria-haspopup="dialog" data-c100-name="' + _c100Esc(r.name) + '" data-c100-value="' + _c100Esc(r.value) + '" data-c100-src="' + _c100Esc(r.source) + '" data-c100-url="' + _c100Esc(r.sourceUrl) + '" data-c100-series="' + _c100Esc(r.series) + '" data-c100-at="' + _c100Esc(at) + '" data-c100-status="' + _c100Esc(st) + '" data-c100-formula="' + _c100Esc(r.formula || "") + '">' +
        '<span class="c100-nm">' + _c100Esc(r.name) + '</span><span class="c100-v">' + _c100Esc(r.value) + '</span>' + (r.change && !m.stale ? '<span class="c100-ch ' + chc + '">' + _c100Esc(r.change) + '</span>' : '') +
        '<span class="c100-src">' + _c100Esc(r.source) + '</span><span class="c100-src">' + _c100Esc(at) + '</span></button>';
    });
    h += '</div>';
  }
  h += '<p class="c100-m-note">Free feeds are delayed; official yields are daily prints. Information only. Not investment advice. Capital at risk.</p></section>';
  try { setTimeout(_c100LoadMacro, 0); } catch (e) {}
  return h;
}
(function () {
  try {
    var prev = calcFearGreed;
    calcFearGreed = function () {
      var r = prev.apply(this, arguments);
      if (r && (r.incomplete || r.vix == null || !(r.nLive >= 3))) return { score: null, label: "Not enough data yet", color: "var(--t3)", vix: r ? r.vix : null, nLive: r ? r.nLive || 0 : 0, incomplete: true };
      return r;
    };
    var prevR = renderFearGreed;
    renderFearGreed = function () {
      var r = calcFearGreed();
      if (!r.incomplete) return prevR.apply(this, arguments);
      return '<div class="gc c100-fg" style="padding:14px" role="status"><div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.18em;margin-bottom:10px">FEAR & GREED · MODEL</div>' +
        '<div style="font-size:15px;font-weight:700;color:var(--t1,inherit)">Not enough data yet</div>' +
        '<div style="font-size:12px;color:var(--t2,inherit);margin-top:6px;line-height:1.5">This gauge needs the volatility index and at least three live prices. It will appear once they arrive. Updating…</div></div>';
    };
  } catch (e) {}
})();
(function () {
  if (document.getElementById("c100-app")) return;
  var st = document.createElement("style"); st.id = "c100-app";
  st.textContent = ".c100-macro{margin:4px 0 14px}.c100-m-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap;margin:0 0 8px}.c100-m-sub{font-size:12px;color:var(--ink-mute,var(--t3))}" +
    ".c100-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}@media (max-width:480px){.c100-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}" +
    ".c100-tile{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-align:left;min-height:44px;padding:10px;border:1px solid var(--rule,var(--gb));border-radius:6px;background:transparent;color:inherit;font:inherit;cursor:pointer}" +
    ".c100-tile:hover{border-color:var(--ink-mute,var(--t3))}.c100-tile:focus-visible{outline:2px solid #2563eb;outline-offset:2px}" +
    ".c100-nm{font-size:12.5px;font-weight:600}.c100-v{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}.c100-ch{font-size:12px;font-variant-numeric:tabular-nums}.c100-src{font-size:11px;color:var(--ink-mute,var(--t3));line-height:1.35}" +
    ".c100-m-empty{font-size:13px;color:var(--ink-mute,var(--t3));padding:8px 0}.c100-m-note{font-size:11.5px;color:var(--ink-mute,var(--t3));margin:8px 0 0}";
  (document.head || document.documentElement).appendChild(st);
})();
