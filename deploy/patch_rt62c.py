#!/usr/bin/env python3
"""rt62c client patch: chat80 -> chat81. Anchors decide; md5 only warns.

One self-contained script. The fe81 runtime is inlined below.
Market-cap text, regime skeleton, gold displayChange, crypto 24h baseline,
index points, and Academy tagging. rt62b guards stay in place.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "777effe4bca52c3cc1dbd0d14d5f54f8"
EXPECT_INDEX_PREFIX = "0f56bcfa"
NEED_MARKER = "// ── rt62b ──"
REFUSE_MARKER = "// ── rt62c ──"

BLOCK = r"""
// ── rt62c ──
// FE81_PURE_START
function fe81_esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;" : "&quot;";
  });
}
function fe81_capText(t) {
  t = t == null ? "" : String(t).trim();
  if (!t || t === "-" || t === "\u2014" || t === "\u2013" || /^null$/i.test(t) || t === "undefined" || t === "NaN") return "";
  if (/^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(t)) return "";
  return t;
}
function fe81_scrCap(s) {
  s = s || {};
  return fe81_capText(s.marketCapText || s.market_cap_text || "") || "\u2014";
}
function fe81_badNum(v) {
  return /^\s*[+-]?\d+(?:\.\d+)?i\s*$/i.test(String(v == null ? "" : v));
}
function fe81_hidePe(a) {
  var cat = String((a && a.cat) || "");
  return /yield|index|fx|commodity|crypto/i.test(cat);
}
function fe81_inputsReal(re) {
  if (!re || typeof re !== "object" || Array.isArray(re)) return false;
  if (re.loading || re.skeleton === true || re.available === false) return false;
  if (/loading/i.test(String(re.label || ""))) return false;
  if (re.score == null || re.score === "" || !isFinite(Number(re.score))) return false;
  var vix = Number(re.vix);
  var spx = re.spxChg != null && re.spxChg !== "" ? Number(re.spxChg) : Number(re.spx);
  return isFinite(vix) && isFinite(spx);
}
function fe81_nsVal(re) {
  if (!re || typeof re !== "object") return "Regime";
  if (typeof fe80_hideScore === "function" && fe80_hideScore(re)) return "Regime";
  if (re.loading || re.skeleton === true || re.available === false) return "Regime";
  if (/loading/i.test(String(re.label || ""))) return "Regime";
  if (re.score == null || re.score === "" || !isFinite(Number(re.score))) return "Regime";
  var label = re.label;
  try {
    if (typeof IS_DESKTOP === "function" && !IS_DESKTOP() && typeof _mobShortRegime === "function") label = _mobShortRegime(re.label);
  } catch (e) {}
  return String(label || "Regime") + " \u00b7 " + re.score;
}
function fe81_goldKeep(held, next) {
  if (!held || held.instrument !== "futures" || held.pct == null || !isFinite(Number(held.pct))) return null;
  next = next || {};
  var dc = next.displayChange;
  var incoming = false;
  if (dc && typeof dc === "object" && (dc.instrument === "futures" || /GC=F|futures/i.test(String(dc.label || "")))) incoming = true;
  if (!dc && next.futuresChange && typeof next.futuresChange === "object") incoming = true;
  if (incoming) return null;
  var pct = +Number(held.pct).toFixed(2);
  var label = held.label && /GC=F|futures/i.test(String(held.label)) ? String(held.label) : "GC=F";
  return {
    pct: pct,
    instrument: "futures",
    label: label,
    text: held.text || ((pct > 0 ? "+" : "") + pct.toFixed(2) + "%")
  };
}
function fe81_cryptoPick(row, px) {
  row = row || {};
  var basis = row.changeBasis || row.changeBasisLabel || row.changeSource;
  var base = Number(row.baselinePrice);
  var p = Number(px);
  if (basis && base > 0 && p > 0) return +(((p / base) - 1) * 100).toFixed(2);
  var srv = row.change != null ? Number(row.change) : (row.changePct != null ? Number(row.changePct) : NaN);
  if (basis && isFinite(srv)) return +srv.toFixed(2);
  return null;
}
function fe81_usSubject(headline) {
  var h = String(headline || "");
  var india = /\b(India|Indian|RBI|gilt|gilts)\b/i.test(h);
  var treasury = /\b(US|U\.S\.|United States)\s+Treasury\b/i.test(h) || /\bTreasury yields\b/i.test(h) || /\bTreasuries\b/i.test(h);
  var fed = /\b(Federal Reserve|FOMC|the Fed|\bFed\b)\b/i.test(h);
  if (india && !treasury && !fed) return false;
  if (india && !/\b(US|U\.S\.|United States)\b/.test(h) && !fed) return false;
  return !!(treasury || fed);
}
function fe81_freshLine(line, edition) {
  edition = String(edition || "").toLowerCase();
  if (edition === "yesterday" || edition === "sample" || edition === "legacy" || edition === "older") {
    return String(line || "").replace(/^Updated today\b/, "Updated");
  }
  return String(line || "");
}
function fe81_dxyChg(line) {
  return String(line == null ? "" : line).replace(/\$/g, "").replace(/\bUSD\b/g, "").replace(/\s{2,}/g, " ").trim();
}
function fe81_metricRow(a) {
  a = a || {};
  var bits = [];
  var betaOk = false;
  try { betaOk = a.cat === "Stock" && typeof fe79_showBeta === "function" && fe79_showBeta(a.tk); } catch (e) {}
  if (betaOk && a.beta != null && a.beta !== "" && a.beta !== "\u2014" && !fe81_badNum(a.beta)) {
    var bt = "";
    try { bt = typeof fe64_betaTxt === "function" ? fe64_betaTxt(a.beta) : String(a.beta); } catch (e2) { bt = String(a.beta); }
    if (bt && bt !== "\u2014" && !fe81_badNum(bt)) {
      bits.push('<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">' + fe81_esc(bt) + '</span><div style="font-size:8px;color:var(--t3);margin-top:2px;letter-spacing:0.02em">5y monthly beta, Yahoo</div></div>');
    }
  }
  if (!fe81_hidePe(a)) {
    var pe = a.pe;
    if (pe != null && pe !== "" && pe !== "-" && pe !== "\u2014" && pe !== "\u2013" && !fe81_badNum(pe)) {
      bits.push('<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">P/E: <span style="color:var(--tx)">' + fe81_esc(pe) + "</span></div>");
    }
  }
  return bits.join("");
}
function fe81_ctxMetrics(a) {
  a = a || {};
  var bits = [];
  var betaOk = false;
  try { betaOk = a.cat === "Stock" && typeof fe79_showBeta === "function" && fe79_showBeta(a.tk); } catch (e) {}
  if (betaOk && a.beta != null && a.beta !== "" && a.beta !== "\u2014" && !fe81_badNum(a.beta)) bits.push("Beta: " + a.beta);
  if (!fe81_hidePe(a) && a.pe && a.pe !== "-" && a.pe !== "\u2014" && !fe81_badNum(a.pe)) bits.push("P/E: " + a.pe);
  var cap = "";
  try { cap = fe81_capText(typeof fe79_capFor === "function" ? fe79_capFor(a) : ""); } catch (e2) { cap = ""; }
  if (!cap) cap = fe81_capText(a.marketCapText || "");
  if (cap) bits.push("Market cap: " + cap);
  return bits.length ? bits.join(" | ") : "";
}
function fe81_plainItem(it) {
  it = it || {};
  var h = it.h || it.headline || it.title || it.x || "";
  h = String(h == null ? "" : h);
  if (h === "null" || h === "undefined") h = "";
  var src = it.src || it.source || "";
  src = String(src == null || src === "null" ? "" : src);
  var link = typeof it.link === "string" ? it.link : "";
  return { plain: true, untagged: true, q: null, asset: null, h: h, src: src, link: link };
}
function fe81_plainHtml(it) {
  it = it || {};
  var h = fe81_esc(it.h || "");
  var src = fe81_esc(it.src || "");
  var link = typeof it.link === "string" && /^https:\/\//.test(it.link) ? it.link : "";
  var a = link ? (' <a href="' + fe81_esc(link) + '" target="_blank" rel="noopener noreferrer">Story</a>') : "";
  var meta = src || a ? ('<p class="rt48-src">' + src + a + "</p>") : "";
  return '<div class="fe81-plain" data-fe81="plain"><h1 class="rt47-sh">' + h + "</h1>" + meta + "</div>";
}
// FE81_PURE_END
var fe81_caps = Object.create(null);
var fe81_snap = null;
var fe81_edition = "";
function fe81_readCap(data) {
  if (!data || typeof data !== "object") return "";
  var bag = data.valuation ? data : (data.data && typeof data.data === "object" ? data.data : data);
  var v = bag.valuation || {};
  return fe81_capText(bag.marketCapText || v.marketCapText || data.marketCapText || "");
}
function fe81_valHtml(tk, cache, html) {
  html = String(html || "");
  var bag = (cache && cache.finData) || {};
  var v = bag.valuation || {};
  var stored = fe81_caps[tk] || {};
  var text = fe81_capText(bag.marketCapText || v.marketCapText || stored.text || "");
  var cellRe = /<div style="background:var\(--bg\);padding:12px 14px"><div style="font-family:var\(--mn\);font-size:8px;color:var\(--t3\);letter-spacing:0\.12em;margin-bottom:4px">MARKET CAP<\/div><div style="font-family:var\(--mn\);font-size:18px;font-weight:800;color:var\(--tx\)">[^<]*<\/div><\/div>/;
  if (cellRe.test(html)) {
    if (!text) return html.replace(cellRe, "");
    return html.replace(cellRe, function (m) {
      return m.replace(/(color:var\(--tx\)">)[^<]*/, "$1" + fe81_esc(text));
    });
  }
  if (text && /VALUATION/.test(html)) {
    var cell = '<div style="background:var(--bg);padding:12px 14px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:4px">MARKET CAP</div><div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--tx)">' + fe81_esc(text) + "</div></div>";
    return html.replace(/(<div style="display:grid;grid-template-columns:repeat\(auto-fill,minmax\(130px,1fr\)\);gap:1px;background:rgba\(255,255,255,0\.04\)">)/, "$1" + cell);
  }
  return html;
}
function fe81_peekLocal() {
  try { if (typeof fe78_eng0 === "function") return fe78_eng0(); } catch (e) {}
  return null;
}
function fe81_localBox(local) {
  var copy = {};
  var k;
  for (k in local) if (Object.prototype.hasOwnProperty.call(local, k)) copy[k] = local[k];
  var lab = String(copy.label || "Regime");
  if (lab.indexOf("Dispatch local estimate") < 0) copy.label = lab + " \u00b7 Dispatch local estimate";
  copy.localEstimate = true;
  copy.loading = false;
  copy.skeleton = false;
  copy.available = true;
  copy.source = "local";
  copy._hide = false;
  return copy;
}
function fe81_snapRow(tk) {
  if (!fe81_snap || fe81_snap.available === false || !Array.isArray(fe81_snap.rows)) return null;
  tk = String(tk || "").toUpperCase();
  for (var i = 0; i < fe81_snap.rows.length; i++) {
    var r = fe81_snap.rows[i] || {};
    var id = String(r.symbol || r.coin || r.tk || "").toUpperCase();
    if (id === tk) return r;
  }
  return null;
}
function fe81_cryptoShown(tk, px) {
  if (fe81_snap && fe81_snap.available === false) return { pct: null, hide: true };
  var row = fe81_snapRow(tk);
  if (row && row.change != null && isFinite(Number(row.change))) return { pct: +Number(row.change).toFixed(2), hide: false };
  var stored = (typeof fe79_srv !== "undefined" && fe79_srv && fe79_srv[tk]) || {};
  var n = px;
  if (!(Number(n) > 0)) {
    try { n = (typeof P !== "undefined" && P[tk]) ? P[tk].p : null; } catch (e) { n = null; }
  }
  var picked = fe81_cryptoPick(stored, n);
  if (picked != null) return { pct: picked, hide: false };
  return null;
}
function fe81_takeSnap(data) {
  if (!data || typeof data !== "object") return;
  if (data.available === false) {
    fe81_snap = { available: false, rows: [], pulse: null };
    return;
  }
  if (!Array.isArray(data.rows)) return;
  fe81_snap = data;
  (data.rows || []).forEach(function (row) {
    if (!row || typeof row !== "object") return;
    var tk = String(row.symbol || row.coin || row.tk || "").toUpperCase();
    if (!tk) return;
    try {
      fe79_ingest(tk, {
        p: row.price,
        price: row.price,
        change: row.change,
        changePct: row.change,
        changeBasis: row.changeBasis || "rolling 24h",
        changeBasisLabel: row.changeBasisLabel || "24h",
        baselinePrice: row.baselinePrice,
        changeSource: "snapshot",
        ts: row.timestamp
      });
    } catch (e) {}
  });
}
function fe81_noteEdition(data) {
  if (!data || typeof data !== "object") return;
  var ed = data.edition != null ? String(data.edition).trim().toLowerCase() : "";
  if (data.sample === true) ed = "sample";
  if (data.legacy === true) ed = "legacy";
  fe81_edition = ed;
  try { if (typeof _rt48Ai !== "undefined" && _rt48Ai) _rt48Ai.edition = ed; } catch (e) {}
}
function fe81_goldHeld() {
  var a = null, b = null;
  try { a = fe79_srv.XAU && fe79_srv.XAU.gold; } catch (e) { a = null; }
  try { b = fe79_srv["GC=F"] && fe79_srv["GC=F"].gold; } catch (e2) { b = null; }
  if (a && a.instrument === "futures") return a;
  if (b && b.instrument === "futures") return b;
  return a || b || null;
}
try {
  var fe81_ing0 = fe79_ingest;
  fe79_ingest = function (tk, q) {
    try {
      if (q && typeof q === "object") {
        if (tk === "XAU" || tk === "GC=F") {
          var held = fe81_goldHeld();
          var keep = fe81_goldKeep(held, q);
          if (keep) q = Object.assign({}, q, { displayChange: keep });
        }
        if (/^(BTC|ETH|SOL)$/.test(String(tk || ""))) {
          var prev = (fe79_srv && fe79_srv[tk]) || {};
          var hasBase = Number(prev.baselinePrice) > 0 || prev.changeBasis || prev.changeBasisLabel;
          var incoming = Number(q.baselinePrice) > 0 || q.changeBasis || q.changeBasisLabel || q.changeSource === "snapshot";
          if (hasBase && !incoming && (q.c != null || q.changePct != null)) {
            q = Object.assign({}, q);
            delete q.c;
            delete q.changePct;
          }
        }
      }
    } catch (e) {}
    var r = fe81_ing0.call(this, tk, q);
    try {
      if ((tk === "XAU" || tk === "GC=F") && fe79_srv[tk] && fe79_srv[tk].gold) {
        var g = fe79_srv[tk].gold;
        if (!fe79_srv.XAU) fe79_srv.XAU = {};
        if (!fe79_srv["GC=F"]) fe79_srv["GC=F"] = {};
        fe79_srv.XAU.gold = g;
        fe79_srv["GC=F"].gold = g;
      }
    } catch (e2) {}
    return r;
  };
} catch (eIng) {}
try {
  var fe81_lc0 = fe79_liveCryptoPct;
  fe79_liveCryptoPct = function (tk, px) {
    var shown = null;
    try { shown = fe81_cryptoShown(tk, px); } catch (e) { shown = null; }
    if (shown && shown.hide) return null;
    if (shown && shown.pct != null) return shown.pct;
    try { return fe81_lc0.apply(this, arguments); } catch (e2) { return null; }
  };
} catch (eLc) {}
try {
  var fe81_ccy0 = fe73_ccy;
  fe73_ccy = function (tk, hint) {
    var t = String(tk || "");
    if (/^(DXY|DX-Y\.NYB|TNX|US10Y|VIX)$/i.test(t)) return "PTS";
    try {
      var a = (typeof A !== "undefined" && A.find) ? A.find(function (x) { return x.tk === t; }) : null;
      if (a && (a.cat === "Index" || a.cat === "Yield")) return "PTS";
    } catch (e) {}
    return fe81_ccy0.apply(this, arguments);
  };
  var fe81_line0 = fe73_chgLine;
  fe73_chgLine = function (tk) {
    var line = "";
    try { line = fe81_line0.apply(this, arguments); } catch (e) { line = ""; }
    if (/^(DXY|DX-Y\.NYB)$/i.test(String(tk || ""))) line = fe81_dxyChg(line);
    return line;
  };
  fe66_chgLine = fe73_chgLine;
} catch (eCcy) {}
try {
  var fe81_mc0 = _rt33Mc;
  _rt33Mc = function () { return "\u2014"; };
  void fe81_mc0;
  var fe81_ap0 = _rt33Apply;
  _rt33Apply = function (tk) {
    var ok = false;
    try { ok = fe81_ap0.apply(this, arguments); } catch (e) { ok = false; }
    try {
      var a = (typeof A !== "undefined" && A.find) ? A.find(function (x) { return x.tk === tk; }) : null;
      var fin = (typeof _finCache !== "undefined" && _finCache[tk]) || {};
      var text = fe81_capText(fin.marketCapText || (fin.valuation && fin.valuation.marketCapText) || (fe81_caps[tk] && fe81_caps[tk].text) || "");
      if (a) a.mc = text || "\u2014";
    } catch (e2) {}
    return ok;
  };
} catch (eMc) {}
try {
  var fe81_rv0 = renderValuation;
  renderValuation = function (tk, cache) {
    var h = "";
    try { h = fe81_rv0.apply(this, arguments); } catch (e) { h = ""; }
    try { h = fe81_valHtml(tk, cache, h); } catch (e2) {}
    return h;
  };
} catch (eRv) {}
try {
  var fe81_cg0 = _rt36CgMc;
  _rt36CgMc = function () {
    var r = fe81_cg0.apply(this, arguments);
    try {
      (_cryptoMktData || []).forEach(function (c) {
        var sym = String((c && c.symbol) || "").toUpperCase();
        var tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(sym)) || sym;
        var a = (typeof A !== "undefined" && A.find) ? A.find(function (x) { return x.tk === tk && x.cat === "Crypto"; }) : null;
        if (a && /^\$/.test(String(a.mc || ""))) a.mc = fe81_capText(c.marketCapText) || "\u2014";
      });
    } catch (e) {}
    return r;
  };
} catch (eCg) {}
try {
  var fe81_ok0 = fe79_metricOk;
  fe79_metricOk = function (label, value) {
    if (fe81_badNum(value)) return false;
    return fe81_ok0.apply(this, arguments);
  };
} catch (eOk) {}
try {
  var fe81_bt0 = fe64_betaTxt;
  fe64_betaTxt = function (v) {
    if (fe81_badNum(v)) return "\u2014";
    return fe81_bt0.apply(this, arguments);
  };
  var fe81_bn0 = fe64_betaNum;
  fe64_betaNum = function (a) {
    var raw = a && typeof a === "object" ? a.beta : a;
    if (fe81_badNum(raw)) return null;
    return fe81_bn0.apply(this, arguments);
  };
} catch (eBt) {}
try {
  var fe81_db0 = _deskBeta;
  _deskBeta = function (a) {
    var raw = a && typeof a === "object" ? a.beta : null;
    if (fe81_badNum(raw)) return arguments.length > 1 ? arguments[1] : 1;
    return fe81_db0.apply(this, arguments);
  };
} catch (eDb) {}
try {
  var fe81_b52 = _rt52BetaOf;
  _rt52BetaOf = function (tk, a) {
    if (a && fe81_badNum(a.beta)) return 0;
    return fe81_b52.apply(this, arguments);
  };
} catch (eB52) {}
try {
  var fe81_from0 = fe78_regimeFrom;
  fe78_regimeFrom = function (raw, local) {
    try {
      if (raw && typeof raw === "object" && raw.localEstimate !== true && (raw.available === false || raw.score == null || raw.score === "")) {
        var peek = local && fe81_inputsReal(local) ? local : fe81_peekLocal();
        if (fe81_inputsReal(peek)) return fe81_localBox(peek);
      }
    } catch (e) {}
    return fe81_from0.apply(this, arguments);
  };
} catch (eFrom) {}
try {
  var fe81_take0 = fe79_takeRegime;
  fe79_takeRegime = function (raw) {
    try {
      if (raw && typeof raw === "object" && (raw.available === false || raw.score == null || raw.score === "")) {
        var peek = fe81_peekLocal();
        if (fe81_inputsReal(peek)) {
          fe79_regimeBox = fe81_localBox(peek);
          fe79_regimeHold = true;
          try { fe79_paintRegime(); } catch (eP) {}
          return fe79_regimeBox;
        }
      }
    } catch (e) {}
    return fe81_take0.apply(this, arguments);
  };
} catch (eTake) {}
try {
  var fe81_note0 = fe79_noteJson;
  fe79_noteJson = function (url, data) {
    try { fe81_note0.apply(this, arguments); } catch (e) {}
    try {
      url = String(url || "");
      if (/crypto-snapshot/.test(url)) fe81_takeSnap(data);
      if (/academy-daily/.test(url)) fe81_noteEdition(data);
      if (/financials|listing-profile/.test(url) && data && typeof data === "object") {
        var sym = "";
        try { sym = decodeURIComponent((url.match(/symbol=([^&]+)/) || [])[1] || ""); } catch (eSym) { sym = ""; }
        var text = fe81_readCap(data);
        var ccy = data.marketCapCurrency || (data.valuation && data.valuation.marketCapCurrency) || (data.data && data.data.marketCapCurrency) || "";
        if (sym) {
          fe81_caps[sym] = { text: text, currency: ccy ? String(ccy) : "" };
          if (!fe79_srv[sym]) fe79_srv[sym] = {};
          if (text) fe79_srv[sym].marketCapText = text;
          if (ccy) fe79_srv[sym].marketCapCurrency = String(ccy);
          var finBag = data.valuation ? data : (data.data || data);
          if (finBag && typeof finBag === "object") {
            if (!fe79_fin[sym]) fe79_fin[sym] = finBag;
            if (text) fe79_fin[sym].marketCapText = text;
          }
        }
      }
    } catch (e2) {}
  };
} catch (eNote) {}
try {
  var fe81_paint = fe79_paintRegime;
  fe79_paintRegime = function () {
    var r;
    try { r = fe81_paint.apply(this, arguments); } catch (e) { r = undefined; }
    try {
      var re = null;
      try { re = _computeRegimeEngine(); } catch (e2) { re = fe79_regimeBox; }
      var txt = fe81_nsVal(re);
      var nodes = document.querySelectorAll(".ns-regime .ns-val");
      for (var i = 0; i < nodes.length; i++) nodes[i].textContent = txt;
    } catch (e3) {}
    return r;
  };
} catch (ePaint) {}
try {
  var fe81_wl0 = _paintWlGlance;
  _paintWlGlance = function () {
    var r = fe81_wl0.apply(this, arguments);
    try {
      var g = fe81_goldHeld();
      if (g && g.instrument === "futures" && g.pct != null) {
        var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";
        var chips = document.querySelectorAll(".wl-glance-chip");
        for (var i = 0; i < chips.length; i++) {
          var oc = chips[i].getAttribute("onclick") || "";
          if (oc.indexOf("XAU") < 0 && oc.indexOf("GC=F") < 0) continue;
          var c = chips[i].querySelector(".wl-g-c");
          if (c) c.textContent = txt;
        }
      }
    } catch (e) {}
    return r;
  };
} catch (eWl) {}
try {
  var fe81_qc0 = _rt47QCells;
  _rt47QCells = function (tk) {
    var html = fe81_qc0.apply(this, arguments);
    try {
      if (tk === "XAU") {
        var g = fe81_goldHeld();
        if (g && g.instrument === "futures" && g.pct != null) {
          var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";
          html = String(html).replace(/(<span class="rt47-qc[^"]*">)[^<]*(<\/span>)/, "$1" + txt + "$2");
          html = String(html).replace(/(<span class="rt47-qs[^"]*">)[^<]*(<\/span>)/, function (m, a, b) {
            var inner = m.slice(a.length, m.length - b.length);
            if (/futures|GC=F/i.test(inner)) return a + b;
            return m;
          });
        }
      }
    } catch (e) {}
    return html;
  };
  var fe81_qrow0 = _rt47QRow;
  _rt47QRow = function (tk) {
    var html = fe81_qrow0.apply(this, arguments);
    try {
      if (tk === "XAU") {
        var g = fe81_goldHeld();
        if (g && g.instrument === "futures") {
          html = String(html).replace(/(<span class="rt47-qn">)(?:Gold futures \(GC=F\)|Gold \(spot\))(<\/span>)/, "$1Gold (spot)$2");
        }
      }
    } catch (e) {}
    return html;
  };
} catch (eRow) {}
try {
  var fe81_ai0 = _rt48AiOk;
  _rt48AiOk = function (it) {
    try {
      if (it && typeof it === "object") {
        var head = it.h || it.headline || it.title || it.x || "";
        var yields = it.asset === "yields" && !fe81_usSubject(head);
        if (it.untagged === true || it.q == null || it.asset == null || yields) return fe81_plainItem(it);
      }
    } catch (e) {}
    return fe81_ai0.apply(this, arguments);
  };
} catch (eAi) {}
try {
  var fe81_steps0 = _rt48NewsSteps;
  _rt48NewsSteps = function () {
    var st = fe81_steps0.apply(this, arguments);
    try {
      st = (st || []).map(function (s) {
        if (!s || s.t !== "q" || !s.ai) return s;
        var it = (_rt48Ai.items || [])[s.n % 10 - 5];
        if (it && it.plain) return { t: "info", plain: true, h: it.h, src: it.src, link: it.link, kick: "IN THE NEWS" };
        return s;
      });
    } catch (e) {}
    return st;
  };
} catch (eSt) {}
try {
  var fe81_step0 = _rt47StepHtml;
  _rt47StepHtml = function (s) {
    if (s && s.plain) return fe81_plainHtml(s);
    var html = fe81_step0.apply(this, arguments);
    try {
      if (s && s.ai) {
        var it = (typeof _rt48Ai !== "undefined" && _rt48Ai && _rt48Ai.items) ? _rt48Ai.items[s.n % 10 - 5] : null;
        if (it && (it.plain || it.asset == null || it.q == null)) html = String(html).replace(/<p class="fe79-asset"[\s\S]*?<\/p>/g, "");
      }
    } catch (e) {}
    return html;
  };
} catch (eStep) {}
try {
  var fe81_quiz0 = _rt48QuizReg;
  _rt48QuizReg = function () {
    var r = fe81_quiz0.apply(this, arguments);
    try {
      var dn = _rt48DayNum();
      (_rt48Ai.items || []).forEach(function (it, k) {
        if (it && it.plain && typeof RT46_QUIZ !== "undefined" && RT46_QUIZ.news) delete RT46_QUIZ.news[dn * 10 + 5 + k];
      });
    } catch (e) {}
    return r;
  };
} catch (eQz) {}
try {
  var fe81_fresh0 = _rt48Fresh;
  _rt48Fresh = function (t) {
    var line = "";
    try { line = fe81_fresh0.apply(this, arguments); } catch (e) { line = ""; }
    var ed = fe81_edition;
    try { if (!ed && typeof _rt48Ai !== "undefined" && _rt48Ai && _rt48Ai.edition) ed = _rt48Ai.edition; } catch (e2) {}
    return fe81_freshLine(line, ed);
  };
} catch (eFr) {}
try {
  var fe81_intel0 = _computeLocalIntel;
  _computeLocalIntel = function (surface) {
    var o = null;
    try { o = fe81_intel0.apply(this, arguments); } catch (e) { o = null; }
    try {
      if (o && surface === "crypto" && typeof o.insight === "string") {
        if (fe81_snap && fe81_snap.available === false) o.insight = o.insight.replace(/\s*Top:[\s\S]*?\./, "");
        else if (fe81_snap && Array.isArray(fe81_snap.rows) && fe81_snap.rows.length) {
          var top = " Top: " + fe81_snap.rows.slice(0, 3).map(function (row) {
            var id = String(row.symbol || row.coin || row.tk || "").toUpperCase();
            var ch = Number(row.change);
            var txt = isFinite(ch) ? ((ch > 0 ? "+" : "") + ch.toFixed(2) + "%") : "\u2014";
            return id + " " + txt;
          }).join(", ") + ".";
          if (/ Top: /.test(o.insight)) o.insight = o.insight.replace(/ Top: [\s\S]*?\./, top);
          else o.insight += top;
        }
      }
    } catch (e2) {}
    return o;
  };
} catch (eIn) {}
try {
  var fe81_top0 = _rtPaintCryptoTop;
  _rtPaintCryptoTop = function () {
    if (fe81_snap && fe81_snap.available === false) {
      try {
        var el = document.querySelector("#siteIntelCard .si-insight");
        if (el) el.textContent = String(el.textContent || "").replace(/\s*Top:[\s\S]*?\./, "");
      } catch (e) {}
      return;
    }
    return fe81_top0.apply(this, arguments);
  };
} catch (eTop) {}
try {
  setTimeout(function () {
    try { fetch("/api/crypto-snapshot?coins=BTC,ETH,SOL&limit=3", { cache: "no-store" }).catch(function () {}); } catch (e) {}
  }, 40);
} catch (eBoot) {}
try {
  setInterval(function () {
    try {
      var re = typeof _computeRegimeEngine === "function" ? _computeRegimeEngine() : null;
      if (typeof fe80_hideScore === "function" && fe80_hideScore(re)) {
        var nodes = document.querySelectorAll(".ns-regime .ns-val,.home-regime,.htec-chip-regime,.lab-regime-lbl");
        for (var i = 0; i < nodes.length; i++) {
          var t = nodes[i].textContent || "";
          if (/Regime:\s*loading/i.test(t) && /50/.test(t)) nodes[i].textContent = "Regime";
          else if (/loading/i.test(t) && /50\s*\/\s*100/.test(t)) nodes[i].textContent = "Regime";
        }
      }
      document.querySelectorAll(".ap-chg").forEach(function (el) {
        var card = el.closest ? el.closest(".ap-hdr") : null;
        var blob = (card ? card.textContent : "") + (el.textContent || "");
        if (/\bDXY\b/.test(blob) && /\$/.test(el.textContent || "")) el.textContent = fe81_dxyChg(el.textContent);
      });
    } catch (e) {}
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
        "${IS_DESKTOP() ? re.label : _mobShortRegime(re.label)} · ${re.score}",
        "${fe81_nsVal(re)}",
        "neural strip",
    )
    app = once(
        app,
        """        ${a.cat === "Stock" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${fe64_betaTxt(a.beta)}</span><div style="font-size:8px;color:var(--t3);margin-top:2px;letter-spacing:0.02em">5y monthly beta, Yahoo</div></div>` : (a.beta != null && a.beta !== "" && a.beta !== "—" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>` : "")}
        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">P/E: <span style="color:var(--tx)">${a.pe}</span></div>""",
        "        ${fe81_metricRow(a)}",
        "desk beta pe",
    )
    app = once(app, "${fmtMC(s.marketCap)}", "${fe81_scrCap(s)}", "screener cap")
    app = once(app, "MARKET CAP MIN ($)", "MARKET CAP MIN", "screener min")
    app = once(app, "MARKET CAP MAX ($)", "MARKET CAP MAX", "screener max")
    app = once(app, "fe79_capFor(a)||a.mc", "fe81_capText(fe79_capFor(a))", "header cap")
    app = once(
        app,
        'if(m.l==="Beta"&&!fe79_showBeta(a.tk))return;',
        'if((m.l==="Beta"&&!fe79_showBeta(a.tk))||(m.l==="P/E"&&fe81_hidePe(a))||fe81_badNum(m.v))return;',
        "phone metrics",
    )
    app = once(
        app,
        '${a.beta != null && a.beta !== "" && a.beta !== "—" ? `Beta: ${a.beta} | ` : ""}P/E: ${a.pe || "—"} | Market cap: ${a.mc || "—"}${_rt33Ctx(tk)}',
        "${fe81_ctxMetrics(a)}${_rt33Ctx(tk)}",
        "chat metrics",
    )
    app = once(
        app,
        "\\/api\\/(regime|session-summary|market-reference-quotes|desk-quotes|brief|financials|listing-profile)|yahoo-quote|ext-hours|coingecko",
        "\\/api\\/(regime|session-summary|market-reference-quotes|desk-quotes|brief|financials|listing-profile|crypto-snapshot|academy-daily)|yahoo-quote|ext-hours|coingecko",
        "fetch watch",
    )
    return app


def pure_slice(app):
    a = app.find("// FE81_PURE_START")
    b = app.find("// FE81_PURE_END")
    if a < 0 or b < 0 or b <= a:
        die("pure slice")
    return app[a:b]


def run_unit(app_text):
    src = pure_slice(app_text) + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
assert(fe81_capText("HK$3.48T") === "HK$3.48T", "hk text");
assert(fe81_capText("3.48e12") === "" && fe81_capText("-") === "" && fe81_capText(null) === "", "hide bare");
assert(fe81_scrCap({ marketCap: 3.48e12 }) === "\u2014", "scr hide");
assert(fe81_scrCap({ marketCapText: "HK$3.48T" }) === "HK$3.48T", "scr text");
assert(fe81_badNum("0.1i") === true && fe81_badNum("0.10") === false && fe81_badNum("12.4x") === false, "bad num");
assert(fe81_inputsReal({ score: 50, label: "Regime: loading\u2026", loading: true, vix: 16, spxChg: 1 }) === false, "loading inputs");
assert(fe81_inputsReal({ score: 50, label: "Cautious" }) === false, "cautious bare");
assert(fe81_inputsReal({ score: 62, label: "Risk-On", vix: 16, spxChg: 1.2, loading: false }) === true, "real inputs");
assert(fe81_inputsReal({ available: false, score: 50, label: "Cautious", vix: 16, spxChg: 1 }) === false, "avail false");
assert(fe81_nsVal({ score: 50, label: "Regime: loading\u2026", loading: true }).indexOf("50") < 0, "ns load");
assert(fe81_nsVal({ available: false, score: 50, label: "Cautious" }) === "Regime", "ns skel");
assert(fe81_nsVal({ score: 50, label: "Cautious" }) === "Cautious \u00b7 50", "ns cautious");
var held = { pct: -1.29, instrument: "futures", label: "Gold futures (GC=F)", text: "\u22121.29%" };
var spot = fe81_goldKeep(held, { displayChange: { pct: -0.18, instrument: "spot", label: "Gold spot" }, spotChangePct: -0.18 });
assert(spot && spot.instrument === "futures" && spot.pct.toFixed(2) === "-1.29", "gold spot");
var bare = fe81_goldKeep(held, { spotChangePct: -0.18 });
assert(bare && bare.pct.toFixed(2) === "-1.29" && bare.label.indexOf("GC=F") >= 0, "gold bare");
assert(fe81_goldKeep(held, { displayChange: { pct: -0.4, instrument: "futures", label: "GC=F" } }) === null, "gold fresh");
var px = 9543, base = 10000;
var picked = fe81_cryptoPick({ baselinePrice: base, changeBasisLabel: "24h", c: -3.89, change: -3.89 }, px);
assert(picked === +(((px / base) - 1) * 100).toFixed(2), "crypto baseline");
assert(picked !== -3.89, "crypto ignores stale");
assert(fe81_cryptoPick({ c: -3.89 }, px) === null, "crypto no basis");
assert(fe81_usSubject("India local bond auction lifts gilt yields") === false, "india");
assert(fe81_usSubject("US Treasury yields rise after the Fed") === true, "ust");
assert(fe81_usSubject("The Fed holds rates") === true, "fed");
assert(fe81_freshLine("Updated today \u00b7 09:15 UK", "yesterday").indexOf("today") < 0, "yday");
assert(fe81_freshLine("Updated today \u00b7 09:15 UK", "sample").indexOf("today") < 0, "sample");
assert(fe81_freshLine("Updated today \u00b7 09:15 UK", "legacy").indexOf("today") < 0, "legacy");
assert(fe81_freshLine("Updated today \u00b7 09:15 UK", "today").indexOf("Updated today") === 0, "today");
assert(fe81_dxyChg("\u2193 -$0.42 (-0.34%)").indexOf("$") < 0, "dxy");
var tnx = fe81_metricRow({ tk: "TNX", cat: "Yield", beta: "0.1i", pe: "-" });
assert(tnx.indexOf("Beta") < 0 && tnx.indexOf("P/E") < 0 && tnx.indexOf("0.1i") < 0, "tnx row");
var plain = fe81_plainHtml(fe81_plainItem({ h: "India local bond auction", src: "Reuters", q: null, asset: null, untagged: true }));
assert(plain.indexOf("null") < 0 && plain.indexOf("India local bond") >= 0 && plain.indexOf("fe79-asset") < 0, "plain");
console.log("fe81 unit ok");
"""
    if "fe80_regArr(" not in app_text:
        die("fe80 guard missing")
    if "re.overweight.some" in app_text or "re.underweight.some" in app_text or "re.overweight.join" in app_text:
        die("raw regime read returned")
    if "fe80_chatCtx(" not in app_text:
        die("chat ctx missing")
    if "function fe81_capText(" not in app_text or "function fe81_nsVal(" not in app_text:
        die("fe81 helpers missing")
    if 'app.js?v=chat81"' in app_text:
        die("cache bust leaked into app")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe81 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def main():
    if not BLOCK.lstrip().startswith("// ── rt62c ──"):
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
    if index.count('app.js?v=chat80"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count("function fe81_capText(") != 1:
        die("fe81_capText def")
    if app.count("function fe80_regArr(") != 1:
        die("fe80_regArr def")
    index = index.replace('app.js?v=chat80"', 'app.js?v=chat81"', 1)
    if index.count('app.js?v=chat81"') != 1:
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
