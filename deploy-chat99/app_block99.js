// ── chat99: Company filings + screener in the menu; a small chart under Ask answers (BYOK and site AI alike) ──
(function () {
  try {
    if (typeof C93_MENU !== "undefined") {
      var g = C93_MENU.filter(function (x) { return x[0] === "Markets and data"; })[0];
      if (g && !g[1].some(function (x) { return x[0] === "/research/sec/"; })) g[1].push(["/research/sec/", "Company filings", "Five years of SEC figures for any US company"], ["/research/sec/screener/", "Filings screener", "Revenue, growth and margins from 10-Ks"], ["/markets/yields/", "Gilt and Treasury yields", "UK and US yield curves, end of day"], ["/gold/positioning/", "Gold positioning", "CFTC weekly report, ten-year percentile"]);
    }
  } catch (e) {}
})();
var _c99Ch = {}, _c99Skip = { XAG: 1, WTI: 1, BRENT: 1, BTC: 1, ETH: 1, DXY: 1, SPX: 1, VIX: 1, TNX: 1 };
function _c99Esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
function _c99Key(q) {
  var tks = []; try { tks = _rt40Tks(q) || []; } catch (e) {}
  for (var i = 0; i < tks.length; i++) { var t = tks[i]; if (t === "XAU") return "gold"; if (!_c99Skip[t] && /^[A-Z]{1,5}(\.[A-Z]{1,2})?$/.test(t)) return t; }
  return /\b(gold|bullion)\b/i.test(q) ? "gold" : null;
}
function _c99Svg(d) {
  var p = d.points || [], W = 520, H = 150, pd = 6; if (p.length < 2) return "";
  var t0 = p[0][0], t1 = p[p.length - 1][0], lo = Infinity, hi = -Infinity;
  p.forEach(function (x) { lo = Math.min(lo, x[1]); hi = Math.max(hi, x[1]); }); if (hi === lo) hi = lo + 1;
  var pts = p.map(function (x) { return ((x[0] - t0) / (t1 - t0 || 1) * (W - pd * 2) + pd).toFixed(1) + "," + (H - pd - (x[1] - lo) / (hi - lo) * (H - pd * 2)).toFixed(1); }).join(" ");
  var up = p[p.length - 1][1] >= p[0][1];
  return '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + _c99Esc(d.title + ". " + d.plain) + '"><polyline points="' + pts + '" fill="none" stroke-width="2" class="' + (up ? "up" : "dn") + '"/></svg>' +
    '<div class="c99ax"><span>Six-month range: ' + _c99Esc(Number(lo).toLocaleString("en-GB")) + ' to ' + _c99Esc(Number(hi).toLocaleString("en-GB")) + '</span></div>';
}
function _c99Fig(d) {
  return '<figure class="c99ask"><figcaption>' + _c99Esc(d.title) + '</figcaption>' + _c99Svg(d) +
    '<p class="c99p">' + _c99Esc(d.plain) + '</p><p class="c99s">Source: ' + _c99Esc(d.source) + ' · ' + _c99Esc(d.asOf) + (d.filings ? ' · <a href="' + _c99Esc(d.filings) + '">Company filings</a>' : '') + '</p><p class="c99s">Not investment advice. Capital at risk.</p></figure>';
}
if (typeof _renderChatMsgs === "function") {
  var _c99Render0 = _renderChatMsgs;
  _renderChatMsgs = function () {
    var r = _c99Render0.apply(this, arguments);
    try {
      if (typeof _chatLoad !== "undefined" && _chatLoad) return r;
      var el = document.getElementById("chatMsgs"); if (!el || !_chatMsgs || !_chatMsgs.length) return r;
      var i = _chatMsgs.length - 1, m = _chatMsgs[i];
      if (!m || m.role !== "assistant" || m._bb2 || !String(m.content || (m.structured && m.structured.answer) || "").trim()) return r;
      var q = ""; for (var j = i - 1; j >= 0; j--) if (_chatMsgs[j].role === "user") { q = String(_chatMsgs[j].content || ""); break; }
      var k = _c99Key(q); if (!k) return r;
      var c = _c99Ch[k];
      if (c && c.d && Date.now() - c.at < 10 * 60e3) { el.insertAdjacentHTML("beforeend", _c99Fig(c.d)); return r; }
      if (c && (c.busy || (c.none && Date.now() - c.at < 10 * 60e3))) return r;
      _c99Ch[k] = { busy: true, at: Date.now() };
      fetch("/api/c99/chart?k=" + encodeURIComponent(k), { credentials: "same-origin" }).then(function (x) { return x.ok ? x.json() : null; }).then(function (d) {
        _c99Ch[k] = d && d.points ? { d: d, at: Date.now() } : { none: true, at: Date.now() };
        if (d && d.points && _chatMsgs[_chatMsgs.length - 1] === m) _renderChatMsgs();
      }).catch(function () { _c99Ch[k] = { none: true, at: Date.now() }; });
    } catch (e) {}
    return r;
  };
}
