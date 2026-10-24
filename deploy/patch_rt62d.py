#!/usr/bin/env python3
"""rt62d client patch: chat81 -> chat82. Anchors decide; md5 only warns.

One self-contained script. The fe82 runtime is inlined below.
Stale regime-loading copy, crypto tape percent, gold glance, Academy
time, signals skeleton, and Ask context. rt62b and rt62c guards stay.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "78e28a26d768f8cbd0458f1609717ffb"
EXPECT_INDEX_PREFIX = "83bb6a28"
NEED_MARKER = "// ── rt62c ──"
REFUSE_MARKER = "// ── rt62d ──"

BLOCK = r"""
// ── rt62d ──
// FE82_PURE_START
function fe82_ms(v) {
  if (v == null || v === "") return 0;
  if (typeof v === "number" && isFinite(v)) return v < 1e11 ? v * 1000 : v;
  var n = Date.parse(String(v));
  return isFinite(n) ? n : 0;
}
function fe82_loadHit(s) {
  return /regime inputs were still loading/i.test(String(s || ""));
}
function fe82_stripLoad(s) {
  return String(s == null ? "" : s)
    .replace(/regime inputs were still loading(?: when this brief was built)?\.?/ig, "")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\s+([,.;])/g, "$1")
    .replace(/^\s+|\s+$/g, "");
}
function fe82_regimeReady(re) {
  if (!re || typeof re !== "object" || Array.isArray(re)) return false;
  if (re.available === false || re.skeleton === true || re.loading) return false;
  if (re.score == null || re.score === "" || !isFinite(Number(re.score))) return false;
  return true;
}
function fe82_riskLine(re) {
  re = re || {};
  if (!fe82_regimeReady(re) && (re.loading || re.available === false || re.score == null || re.score === "")) {
    return "Regime inputs were still loading when this brief was built";
  }
  if (Number(re.score) < 50) return "Risk-off at brief time (" + re.score + "/100) — size down high-beta first";
  return "Risk-on can reverse fast if VIX spikes";
}
function fe82_tapePct(row, px) {
  row = row || {};
  var base = Number(row.baselinePrice);
  var p = Number(px != null ? px : (row.px != null ? row.px : (row.p != null ? row.p : row.price)));
  if (base > 0 && p > 0) {
    var pct = ((p / base) - 1) * 100;
    if (isFinite(pct)) return +pct.toFixed(2);
  }
  var srv = row.c != null ? row.c : (row.changePct != null ? row.changePct : row.change);
  if (srv != null && srv !== "" && isFinite(Number(srv))) return +Number(srv).toFixed(2);
  return null;
}
function fe82_goldPts(price, prev, extra) {
  extra = extra || {};
  var raw = extra.points != null ? extra.points : (extra.pointChange != null ? extra.pointChange : extra.changePoints);
  var pts = Number(raw);
  if (!isFinite(pts) || Number(pts.toFixed(2)) === 0) {
    var p = Number(price), q = Number(prev);
    if (p > 0 && q > 0) pts = p - q;
  }
  if (!isFinite(pts) || Number(pts.toFixed(2)) === 0) return "";
  var n = Number(pts);
  var abs = Math.abs(n);
  var body = abs >= 1000
    ? abs.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : abs.toFixed(2);
  return (n > 0 ? "+" : "-") + body;
}
function fe82_pxText(n, fx) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  var dp = fx ? 4 : 2;
  return v.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp });
}
function fe82_editionMs(j, items) {
  items = items || (j && j.items) || [];
  var i;
  for (i = 0; i < items.length; i++) {
    var it = items[i] || {};
    var m = fe82_ms(it.generatedAt || it.updatedAt || it.generated_at || it.updated_at);
    if (m) return m;
  }
  if (j) return fe82_ms(j.generatedAt || j.updatedAt || j.generated_at || j.updated_at);
  return 0;
}
function fe82_sigMode(st) {
  st = st || {};
  if (st.have) return "cards";
  var open = !!st.open;
  var err = !!st.err;
  var age = Number(st.age) || 0;
  if (err && !open) return "unavailable";
  if (!open && st.settled && !st.have) return "unavailable";
  if (age >= 20000) return "unavailable";
  return "skeleton";
}
// FE82_PURE_END
var fe82_acadAt = 0;
var fe82_goldDc = null;
var fe82_quoteWait = [];
var fe82_qGen = 1;
var fe82_sigT0 = 0;
var fe82_sigArmed = false;
var fe82_sigTimer = 0;
var FE82_SYM = { "BTC-USD": "BTC", "ETH-USD": "ETH", "SOL-USD": "SOL", "GC=F": "XAU", "CL=F": "WTI", "^VIX": "VIX", "^GSPC": "SPX", "DX-Y.NYB": "DXY" };
function fe82_isQuoteUrl(url) {
  return /yahoo-quote|desk-quotes|twelve|coingecko|market-reference|crypto-snapshot|ext-hours|gold-api/i.test(String(url || ""));
}
function fe82_sigState() {
  var have = false;
  try {
    have = (typeof SIGS !== "undefined" ? SIGS : []).some(function (s) {
      return s && typeof hasSyncedQuote === "function" && hasSyncedQuote(s.tk);
    });
  } catch (e) { have = false; }
  var open = false, err = false, settled = fe82_quoteWait.length > 0;
  for (var i = 0; i < fe82_quoteWait.length; i++) {
    var s = fe82_quoteWait[i];
    if (!s.done) { open = true; settled = false; }
    if (s.err) err = true;
  }
  if (!fe82_sigT0) fe82_sigT0 = Date.now();
  return fe82_sigMode({ have: have, open: open, err: err, settled: settled, age: Date.now() - fe82_sigT0 });
}
function fe82_sigSkel() {
  var n = 4;
  try { if (typeof SIGS !== "undefined" && SIGS.length) n = Math.min(SIGS.length, 4); } catch (e) {}
  var h = "";
  for (var i = 0; i < n; i++) {
    h += '<div class="gc gc-a rt52-sig fe82-sig-skel" data-fe82="sig-skel" style="padding:12px;margin-bottom:8px"><div style="height:12px;width:42%;background:var(--b3);border-radius:4px;margin-bottom:8px"></div><div style="height:10px;width:78%;background:var(--b3);border-radius:4px;margin-bottom:6px"></div><div style="height:10px;width:54%;background:var(--b3);border-radius:4px"></div></div>';
  }
  return h;
}
function fe82_sigPage() {
  var h = "";
  try { if (typeof _renderPgHdr === "function") h = _renderPgHdr("Signals", "Checking the live prices"); } catch (e) {}
  return h + fe82_sigSkel();
}
function fe82_onSig() {
  try {
    if (typeof pg === "string" && pg === "sig") return true;
    if (typeof IS_DESKTOP === "function" && IS_DESKTOP() && document.getElementById("p3body")) return true;
  } catch (e) {}
  return false;
}
function fe82_sigTick() {
  if (!fe82_onSig()) return;
  var mode = fe82_sigState();
  var desk = false;
  try { desk = typeof IS_DESKTOP === "function" && IS_DESKTOP(); } catch (e) {}
  var root = desk ? document.getElementById("p3body") : document.getElementById("main");
  if (!root) return;
  var skel = !!root.querySelector("[data-fe82=sig-skel]");
  var bad = /UNAVAILABLE|No price yet|On hold/i.test(root.textContent || "");
  if (mode === "skeleton") {
    if (!skel || bad) {
      if (desk) root.innerHTML = '<div style="padding:8px 16px;font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">DESK SIGNALS</div>' + fe82_sigSkel();
      else root.innerHTML = fe82_sigPage();
    }
    return;
  }
  if (skel) {
    try {
      if (desk && typeof fe82_p30 === "function") fe82_p30();
      else if (!desk && typeof renderMain === "function") renderMain();
    } catch (e2) {}
  }
}
function fe82_armSig() {
  if (!fe82_sigArmed) { fe82_sigArmed = true; fe82_sigT0 = Date.now(); }
  if (fe82_sigTimer) return;
  fe82_sigTimer = setInterval(fe82_sigTick, 250);
}
function fe82_takeQuotes(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return;
  Object.keys(data).forEach(function (k) {
    var q = data[k];
    if (!q || typeof q !== "object" || Array.isArray(q)) return;
    var px = Number(q.p != null ? q.p : q.price);
    if (!(px > 0)) return;
    var tk = FE82_SYM[k] || k;
    try { if (typeof resolveInternalTicker === "function") tk = resolveInternalTicker(tk) || tk; } catch (e) {}
    var c = q.c != null ? Number(q.c) : (q.changePct != null ? Number(q.changePct) : (q.change != null ? Number(q.change) : null));
    try {
      if (typeof _applyLiveQuote === "function") _applyLiveQuote(tk, { p: px, c: c, prev: q.prev, ts: q.ts || Date.now(), source: q.source || "yahoo" }, q.source || "yahoo");
    } catch (e2) {}
    try {
      if ((q.baselinePrice || q.changeBasis || q.displayChange) && typeof fe79_ingest === "function") fe79_ingest(tk, q);
    } catch (e3) {}
  });
}
function fe82_tapeCell(tk, ch, d) {
  var pct = (ch != null && isFinite(Number(ch))) ? Number(ch) : null;
  if (pct == null) {
    try { pct = fe79_liveCryptoPct(tk); } catch (e) { pct = null; }
  }
  if ((pct == null || !isFinite(Number(pct))) && d && d.c != null && d.c !== "" && d.c !== "—" && d.c !== "–" && d.c !== "-") {
    var n = Number(String(d.c).replace(/[%+,]/g, ""));
    if (isFinite(n)) pct = n;
  }
  if (pct == null || !isFinite(Number(pct))) return "—";
  var body = (Number(pct) >= 0 ? "+" : "") + Number(pct).toFixed(2) + "%";
  try { return fe78_chgHtml(tk, body); } catch (e2) { return body; }
}
function fe82_hubFresh() {
  if (fe82_acadAt) return fe82_acadAt;
  try { return Math.max((typeof _rt48Wk !== "undefined" && _rt48Wk.at) || 0, (typeof _rt48Nw !== "undefined" && _rt48Nw.at) || 0); } catch (e) { return 0; }
}
function fe82_takeEdition(data) {
  if (!data || typeof data !== "object") return;
  var items = data.items || (data.ai && data.ai.items) || [];
  var ms = fe82_editionMs(data, items);
  if (!ms) return;
  fe82_acadAt = ms;
  try { if (typeof _rt48Ai !== "undefined" && _rt48Ai) _rt48Ai.at = ms; } catch (e) {}
}
function fe82_scrubBriefObj() {
  var ready = false;
  try { ready = fe82_regimeReady(typeof _computeRegimeEngine === "function" ? _computeRegimeEngine() : null); } catch (e) { return; }
  if (!ready || typeof _brief === "undefined" || !_brief) return;
  ["summary", "headline", "houseView"].forEach(function (k) {
    if (typeof _brief[k] === "string" && fe82_loadHit(_brief[k])) _brief[k] = fe82_stripLoad(_brief[k]);
  });
  if (Array.isArray(_brief.risks)) {
    _brief.risks = _brief.risks.map(function (r) { return fe82_loadHit(r) ? fe82_stripLoad(r) : r; }).filter(function (r) { return r; });
  }
}
function fe82_scrubLoad() {
  var ready = false;
  try { ready = fe82_regimeReady(typeof _computeRegimeEngine === "function" ? _computeRegimeEngine() : null); } catch (e) { return; }
  if (!ready || typeof document === "undefined") return;
  fe82_scrubBriefObj();
  var roots = document.querySelectorAll("#main, #siteIntelCard, #siteIntelBar, .si-insight");
  for (var i = 0; i < roots.length; i++) {
    var walker = document.createTreeWalker(roots[i], NodeFilter.SHOW_TEXT);
    var n;
    while ((n = walker.nextNode())) {
      if (fe82_loadHit(n.nodeValue)) n.nodeValue = fe82_stripLoad(n.nodeValue);
    }
  }
}
function fe82_fixChip(el, tk) {
  if (!el) return;
  var pe = el.querySelector(".wl-g-p");
  var fx = false;
  try { fx = typeof fe76_isFx === "function" && fe76_isFx(tk); } catch (e) {}
  if (pe) {
    var raw = String(pe.textContent || "").replace(/,/g, "").replace(/^\$/, "").trim();
    if (/^[+-]?\d+(\.\d+)?$/.test(raw)) {
      var pretty = (String(pe.textContent).trim().charAt(0) === "$" ? "$" : "") + fe82_pxText(Number(raw), fx);
      if (pe.textContent !== pretty) pe.textContent = pretty;
    }
  }
  if (tk !== "XAU" && tk !== "GC=F") return;
  var g = null;
  try { g = (typeof fe81_goldHeld === "function" && fe81_goldHeld()) || (typeof fe79_goldNow === "function" && fe79_goldNow()); } catch (e2) { g = null; }
  if (!g || g.pct == null || !isFinite(Number(g.pct))) return;
  var pct = Number(g.pct);
  var arrow = pct > 0 ? "▲" : pct < 0 ? "▼" : "•";
  var sign = pct > 0 ? "+" : "";
  var px = 0, prev = 0;
  try { px = Number(P[tk] && P[tk].p) || Number(P.XAU && P.XAU.p) || Number(P["GC=F"] && P["GC=F"].p); } catch (e3) {}
  try { prev = Number(BASE[tk] && BASE[tk].p) || Number(BASE["GC=F"] && BASE["GC=F"].p) || Number(BASE.XAU && BASE.XAU.p); } catch (e4) {}
  var pts = fe82_goldPts(px, prev, fe82_goldDc || {});
  var ce = el.querySelector(".wl-g-c");
  if (ce) ce.textContent = "Gold futures (GC=F) " + arrow + " " + sign + pct.toFixed(2) + "%" + (pts ? " · " + pts : "");
  try {
    var src = (typeof fp === "function" && fp(tk) && fp(tk).src) || "";
    if (pe && /gold-api|spot/i.test(String(src))) pe.title = "Spot gold";
  } catch (e5) {}
  var se = el.querySelector(':scope > span[style*="display:block"]');
  if (se) se.textContent = "Gold futures (GC=F)";
}
function fe82_fixGlance() {
  var chips = document.querySelectorAll(".wl-glance-chip");
  for (var i = 0; i < chips.length; i++) {
    var oc = chips[i].getAttribute("onclick") || "";
    var m = oc.match(/openA\('([^']+)'\)/);
    fe82_fixChip(chips[i], m ? m[1] : "");
  }
}
function fe82_fixAsk(text) {
  var t = String(text || "");
  ["BTC", "ETH", "SOL"].forEach(function (tk) {
    var pct = null;
    try { pct = fe79_liveCryptoPct(tk); } catch (e) { pct = null; }
    if (pct == null || !isFinite(Number(pct))) return;
    var shown = (Number(pct) > 0 ? "+" : "") + Number(pct).toFixed(2);
    var re = new RegExp("\\b" + tk + "\\b([^%\\n]{0,16}?)[-+\\u2212]?\\d+\\.\\d+\\s*%", "g");
    t = t.replace(re, function (_m, mid) { return tk + mid + shown + "%"; });
  });
  var g = null;
  try { g = typeof fe79_goldNow === "function" ? fe79_goldNow() : null; } catch (e2) { g = null; }
  if (g && g.text && g.text !== "—") {
    t = t.replace(/\bGold\b([^%\n]{0,16}?)[-+\u2212]?\d+\.\d+\s*%/g, function (_m, mid) { return "Gold" + mid + String(g.text).replace(/^Gold\s+/i, ""); });
    if (t.indexOf("Gold display:") < 0) t += "\nGold display: " + g.text;
  }
  var bits = ["BTC", "ETH", "SOL"].map(function (tk) {
    var pct = null;
    try { pct = fe79_liveCryptoPct(tk); } catch (e3) { pct = null; }
    if (pct == null || !isFinite(Number(pct))) return tk + " —";
    return tk + " " + (Number(pct) > 0 ? "+" : "") + Number(pct).toFixed(2) + "%";
  });
  if (t.indexOf("Crypto 24h:") < 0) t += "\nCrypto 24h: " + bits.join(" · ");
  if (fe82_regimeReady(typeof _computeRegimeEngine === "function" ? _computeRegimeEngine() : null)) t = fe82_stripLoad(t);
  return t;
}
try {
  var fe82_lc0 = fe79_liveCryptoPct;
  fe79_liveCryptoPct = function (tk, px) {
    var n = px;
    if (!(Number(n) > 0)) { try { n = (typeof P !== "undefined" && P[tk]) ? P[tk].p : null; } catch (e) { n = null; } }
    var stored = (typeof fe79_srv !== "undefined" && fe79_srv && fe79_srv[tk]) || {};
    var pct = fe82_tapePct(stored, n);
    if (pct == null) {
      try {
        var row = typeof fe81_snapRow === "function" ? fe81_snapRow(tk) : null;
        if (row) pct = fe82_tapePct({ baselinePrice: row.baselinePrice, c: row.change != null ? row.change : row.c, changePct: row.changePct, change: row.change, price: row.price }, n || row.price);
      } catch (e2) {}
    }
    if (pct == null) {
      try {
        var c = (typeof P !== "undefined" && P[tk]) ? P[tk].c : null;
        if (c != null && isFinite(Number(c))) pct = +Number(c).toFixed(2);
      } catch (e3) {}
    }
    if (pct != null) return pct;
    try { return fe82_lc0.apply(this, arguments); } catch (e4) { return null; }
  };
} catch (eLc) {}
try {
  var fe82_fp0 = fp;
  fp = function (tk) {
    var d = fe82_fp0.apply(this, arguments);
    try {
      var id = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
      if (d && typeof fe79_isCryptoTk === "function" && fe79_isCryptoTk(id)) {
        var pct = fe79_liveCryptoPct(id);
        if (pct != null && (d.c == null || d.c === "" || d.c === "—" || d.c === "–" || d.c === "-")) d.c = Number(pct).toFixed(2);
      }
    } catch (e) {}
    return d;
  };
} catch (eFp) {}
try {
  var fe82_ing0 = fe79_ingest;
  fe79_ingest = function (tk, q) {
    try {
      if (q && (tk === "XAU" || tk === "GC=F") && q.displayChange && typeof q.displayChange === "object") fe82_goldDc = q.displayChange;
    } catch (e) {}
    var r = fe82_ing0.apply(this, arguments);
    try {
      if (/^(BTC|ETH|SOL)$/.test(String(tk || "")) && typeof _rt !== "undefined" && _rt && _rt.dirty) _rt.dirty.add(tk);
      if (/^(BTC|ETH|SOL)$/.test(String(tk || "")) && typeof renderTape === "function") renderTape();
    } catch (e2) {}
    return r;
  };
} catch (eIng) {}
try {
  var fe82_brief0 = _renderDispatchBrief;
  _renderDispatchBrief = function () {
    try { fe82_scrubBriefObj(); } catch (e) {}
    var h = fe82_brief0.apply(this, arguments);
    try {
      if (fe82_regimeReady(_computeRegimeEngine())) h = fe82_stripLoad(h);
    } catch (e2) {}
    return h;
  };
} catch (eBr) {}
try {
  var fe82_ctx0 = _buildChatContext;
  _buildChatContext = function () {
    var t = "";
    try { t = fe82_ctx0.apply(this, arguments); } catch (e) { t = "Regime: loading"; }
    try { t = fe82_fixAsk(t); } catch (e2) {}
    return t;
  };
} catch (eCtx) {}
try {
  var fe82_bit0 = _liveTapeBit;
  _liveTapeBit = function (label) {
    var tks = Array.prototype.slice.call(arguments, 1);
    if (tks.indexOf("XAU") >= 0 || tks.indexOf("GC=F") >= 0) {
      var g = null;
      try { g = fe79_goldNow(); } catch (e) { g = null; }
      if (g && g.text && g.text !== "—") {
        var px = "";
        try { var d = fp("XAU"); if (d && d.p && d.p !== "—") px = " " + d.p; } catch (e2) {}
        return String(label) + px + " " + g.text;
      }
    }
    return fe82_bit0.apply(this, arguments);
  };
} catch (eBit) {}
try {
  var fe82_ask0 = fe79_askChip;
  fe79_askChip = function (meta) {
    var chip = fe82_ask0.apply(this, arguments);
    try {
      if (chip && chip.price != null && chip.price !== "") {
        var n = Number(String(chip.price).replace(/,/g, "").replace(/^\$/, ""));
        if (isFinite(n)) {
          var lab = String(chip.label || "");
          var fx = lab.indexOf("/") >= 0 || /^(EUR|GBP|USD|JPY|AUD|CAD|CHF|NZD)[A-Z]{3}$/i.test(lab.replace(/\s/g, ""));
          chip.price = fe82_pxText(n, fx);
          chip.line = [chip.label, chip.price, chip.time].filter(function (x) { return x; }).join(" · ");
        }
      }
    } catch (e) {}
    return chip;
  };
} catch (eAsk) {}
try {
  var fe82_px0 = fe78_quotePx;
  fe78_quotePx = function (q, n) {
    var label = String((q && q.label) || "");
    var sym = String((q && (q.symbol || q.ticker)) || "").toUpperCase();
    var fx = label.indexOf("/") >= 0 || /^(EUR|GBP|USD|JPY|AUD|CAD|CHF|NZD)[A-Z]{3}$/.test(sym.replace(/=X$/, ""));
    var num = Number(n);
    if (!isFinite(num)) return fe82_px0.apply(this, arguments);
    var body = fe82_pxText(num, fx);
    return fx ? body : "$" + body;
  };
} catch (ePx) {}
try {
  var fe82_chip0 = _rtPaintChip;
  _rtPaintChip = function (el, tk) {
    var moved = false;
    try { moved = fe82_chip0.apply(this, arguments); } catch (e) { moved = false; }
    try { fe82_fixChip(el, tk); } catch (e2) {}
    return moved;
  };
} catch (eChip) {}
try {
  var fe82_wl0 = _paintWlGlance;
  _paintWlGlance = function () {
    var r = fe82_wl0.apply(this, arguments);
    try { fe82_fixGlance(); } catch (e) {}
    return r;
  };
} catch (eWl) {}
try {
  var fe82_ed0 = fe81_noteEdition;
  fe81_noteEdition = function (data) {
    try { fe82_ed0.apply(this, arguments); } catch (e) {}
    try { fe82_takeEdition(data); } catch (e2) {}
  };
} catch (eEd) {}
try {
  var fe82_store0 = fe78_academyStore;
  fe78_academyStore = function (box, j) {
    var out = fe82_store0.apply(this, arguments);
    try {
      var ms = fe82_editionMs(j, (j && j.items) || (out && out.items) || []);
      if (ms) {
        fe82_acadAt = ms;
        if (out) out.at = ms;
        if (typeof _rt48Ai !== "undefined" && _rt48Ai) _rt48Ai.at = ms;
      }
    } catch (e) {}
    return out;
  };
} catch (eSt) {}
try {
  var fe82_fr0 = _rt48Fresh;
  _rt48Fresh = function (t) {
    var use = t;
    try {
      if (fe82_acadAt && typeof _rt48Nw !== "undefined" && _rt48Nw && t && t === _rt48Nw.at && t !== fe82_acadAt) use = fe82_acadAt;
    } catch (e) {}
    return fe82_fr0.call(this, use);
  };
} catch (eFr) {}
try {
  var fe82_ns0 = _rt48NewsSteps;
  _rt48NewsSteps = function () {
    var st = fe82_ns0.apply(this, arguments);
    try { if (fe82_acadAt && st && st[0] && st[0].fresh) st[0].fresh = fe82_acadAt; } catch (e) {}
    return st;
  };
} catch (eNs) {}
try {
  var fe82_sig0 = renderSig;
  renderSig = function () {
    fe82_armSig();
    if (fe82_sigState() === "skeleton") return fe82_sigPage();
    return fe82_sig0.apply(this, arguments);
  };
} catch (eSig) {}
try {
  fe82_p30 = renderP3;
  renderP3 = function () {
    fe82_armSig();
    if (fe82_sigState() === "skeleton") {
      var el = document.getElementById("p3body");
      if (el) el.innerHTML = '<div style="padding:8px 16px;font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">DESK SIGNALS</div>' + fe82_sigSkel();
      return;
    }
    return fe82_p30.apply(this, arguments);
  };
} catch (eP3) {}
try {
  var fe82_fetch0 = window.fetch.bind(window);
  window.fetch = function (input) {
    var url = "";
    try { url = typeof input === "string" ? input : (input && input.url) || ""; } catch (e0) { url = ""; }
    var p;
    try { p = fe82_fetch0.apply(window, arguments); } catch (e) { return Promise.reject(e); }
    if (!fe82_isQuoteUrl(url)) return p;
    var slot = { done: false, err: false, gen: fe82_qGen };
    fe82_quoteWait.push(slot);
    if (fe82_quoteWait.length > 40) fe82_quoteWait.shift();
    return Promise.resolve(p).then(function (r) {
      slot.done = true;
      if (r && r.ok === false) slot.err = true;
      try {
        r.clone().json().then(function (data) {
          if (slot.gen !== fe82_qGen) return;
          fe82_takeQuotes(data);
        }).catch(function () {});
      } catch (e2) {}
      return r;
    }, function (err) {
      slot.done = true;
      slot.err = true;
      throw err;
    });
  };
} catch (eFetch) {}
try {
  setInterval(function () {
    try { fe82_scrubLoad(); } catch (e) {}
    try { if (fe82_onSig()) fe82_sigTick(); } catch (e2) {}
  }, 400);
} catch (eIv) {}
"""


def die(msg):
    print("FAIL", msg)
    sys.exit(1)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


def md5(raw):
    return hashlib.md5(raw).hexdigest()


def read_text(path):
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    return raw, raw.replace(b"\r\n", b"\n").decode("utf-8"), crlf


def write_text(path, text, crlf):
    data = text.encode("utf-8")
    if crlf:
        data = data.replace(b"\n", b"\r\n")
    path.write_bytes(data)


def paths():
    if len(sys.argv) >= 3:
        return pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if len(sys.argv) == 2:
        d = pathlib.Path(sys.argv[1])
        if d.is_dir():
            return d / "app.js", d / "index.html"
        return d, d.with_name("index.html")
    cwd = pathlib.Path.cwd()
    return cwd / "app.js", cwd / "index.html"


def anchors(app):
    app = once(
        app,
        're.loading ? "Regime inputs were still loading when this brief was built" : re.score < 50 ? `Risk-off at brief time (${re.score}/100) — size down high-beta first` : "Risk-on can reverse fast if VIX spikes"',
        "fe82_riskLine(re)",
        "brief risk",
    )
    app = once(
        app,
        '${ch==null?"—":fe78_chgHtml(k, chSign+d.c+"%")}',
        "${fe82_tapeCell(k, ch, d)}",
        "tape cell",
    )
    app = once(
        app,
        'var fe78tape = ch == null ? "—" : fe78_chgHtml(tk, sign + d.c + "%");',
        'var fe78tape = fe82_tapeCell(tk, ch, d);',
        "tape paint",
    )
    app = once(
        app,
        "const fresh = Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0);",
        "const fresh = (typeof fe82_hubFresh===\"function\"?fe82_hubFresh():Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0));",
        "academy hub",
    )
    app = once(
        app,
        "const t = Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0), s = t ? _rt48Fresh(t) : '';",
        "const t = (typeof fe82_hubFresh===\"function\"?fe82_hubFresh():Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0)), s = t ? _rt48Fresh(t) : '';",
        "academy refresh",
    )
    return app


def pure_slice(app):
    a = app.find("// FE82_PURE_START")
    b = app.find("// FE82_PURE_END")
    if a < 0 or b < 0 or b <= a:
        die("pure slice")
    return app[a:b]


def run_unit(app_text):
    src = pure_slice(app_text) + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
assert(fe82_loadHit("Regime inputs were still loading when this brief was built.") === true, "hit period");
assert(fe82_loadHit("regime inputs were still loading") === true, "hit short");
assert(fe82_stripLoad("Keep. Regime inputs were still loading when this brief was built. Next").indexOf("loading") < 0, "strip");
assert(fe82_stripLoad("regime inputs were still loading when this brief was built").indexOf("loading") < 0, "strip nopunct");
var ready = { available: true, score: 37, label: "Risk-Off", loading: false };
var down = { available: false, score: null, label: "" };
assert(fe82_regimeReady(ready) === true, "ready");
assert(fe82_regimeReady(down) === false, "down");
assert(fe82_regimeReady({ score: 50, label: "Cautious", loading: true }) === false, "loading");
assert(fe82_riskLine(down).indexOf("still loading") >= 0, "risk keep");
assert(fe82_riskLine(ready).indexOf("still loading") < 0, "risk drop");
var px = 9543, base = 10000;
assert(fe82_tapePct({ baselinePrice: base, c: -2.95, changeBasis: "24h" }, px) === +(((px / base) - 1) * 100).toFixed(2), "tape base");
assert(fe82_tapePct({ c: -3.82 }, 0) === -3.82, "tape c");
assert(fe82_tapePct({ changePct: -3.87 }, null) === -3.87, "tape pct");
assert(fe82_goldPts(3996.9, 4049.4, null) === "-52.50", "pts");
assert(fe82_goldPts(3996.9, 3996.9, null) === "", "pts zero");
assert(fe82_goldPts(10, null, { points: 0 }) === "", "pts missing");
assert(fe82_goldPts(10, null, { points: -52.5 }) === "-52.50", "pts field");
assert(fe82_pxText(3996.899902, false) === "3,996.90", "px");
assert(fe82_pxText(1.08542, true) === "1.0854", "fx");
var stamp = fe82_editionMs({ generatedAt: "2026-10-24T09:15:00Z" }, [{ generatedAt: "2026-10-24T08:05:00Z", h: "Fed" }]);
assert(stamp === Date.parse("2026-10-24T08:05:00Z"), "item time");
assert(fe82_sigMode({ have: true, err: true }) === "cards", "sig cards");
assert(fe82_sigMode({ err: true, open: false, age: 100 }) === "unavailable", "sig err");
assert(fe82_sigMode({ open: true, age: 3000 }) === "skeleton", "sig wait");
assert(fe82_sigMode({ open: true, age: 20000 }) === "unavailable", "sig timeout");
assert(fe82_sigMode({ settled: true, open: false, have: false, age: 50 }) === "unavailable", "sig miss");
console.log("fe82 unit ok");
"""
    if "function fe80_regArr(" not in app_text:
        die("fe80 guard missing")
    if "function fe81_capText(" not in app_text or "function fe81_goldKeep(" not in app_text:
        die("fe81 helpers missing")
    if "re.overweight.some" in app_text or "re.underweight.some" in app_text or "re.overweight.join" in app_text:
        die("raw regime read returned")
    if "fe80_chatCtx(" not in app_text:
        die("chat ctx missing")
    if 'app.js?v=chat82"' in app_text:
        die("cache bust leaked into app")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe82 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def main():
    if not BLOCK.lstrip().startswith("// ── rt62d ──"):
        die("block marker")
    app_path, index_path = paths()
    if not app_path.is_file() or not index_path.is_file():
        die("missing app.js or index.html")
    app_raw, app, app_crlf = read_text(app_path)
    index_raw, index, index_crlf = read_text(index_path)
    app_sum = md5(app_raw)
    index_sum = md5(index_raw)
    if app_sum != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (app_sum, EXPECT_APP_MD5))
    if not index_sum.startswith(EXPECT_INDEX_PREFIX):
        print("WARN index.html md5 %s expected prefix %s" % (index_sum, EXPECT_INDEX_PREFIX))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    if index.count('app.js?v=chat81"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count("function fe82_tapePct(") != 1:
        die("fe82_tapePct def")
    if app.count("function fe80_regArr(") != 1 or app.count("function fe81_capText(") != 1:
        die("prior helper def")
    index = index.replace('app.js?v=chat81"', 'app.js?v=chat82"', 1)
    if index.count('app.js?v=chat82"') != 1:
        die("cache bust")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        print("node --check ok")
        run_unit(app)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
