#!/usr/bin/env python3
"""rt62e client patch: chat82 -> chat83. Anchors decide; md5 only warns.

One self-contained script. The fe83 runtime is inlined below.
Regime fields, one sign, gold instrument, Academy week time,
signals load window, and a fixed DXY name. rt62b-rt62d stay.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "e45d14a361587253a328c0de1ff4c791"
EXPECT_INDEX_PREFIX = "30af5ae4"
NEED_MARKER = "// ── rt62d ──"
REFUSE_MARKER = "// ── rt62e ──"

BLOCK = r"""
// ── rt62e ──
// FE83_PURE_START
function fe83_num(v) {
  if (v == null || typeof v === "boolean") return null;
  if (typeof v === "number") return isFinite(v) ? v : null;
  var s = String(v).trim();
  if (!s || s === "—" || s === "–" || s === "-" || /undefined|nan|^null$/i.test(s)) return null;
  s = s.replace(/[$,%\s]/g, "").replace(/[−–]/g, "-").replace(/^\((.*)\)$/, "$1");
  var neg = false;
  s = s.replace(/^[+-]+/, function (m) {
    neg = (m.split("-").length - 1) % 2 === 1;
    return "";
  });
  if (!s || /[^0-9.]/.test(s)) return null;
  var n = Number(s);
  if (!isFinite(n)) return null;
  return neg ? -Math.abs(n) : n;
}
function fe83_signed(v, suffix) {
  var n = fe83_num(v);
  if (n == null) return "";
  var body = Math.abs(n).toFixed(2);
  var sign = n > 0 ? "+" : (n < 0 ? "-" : "");
  return sign + body + (suffix || "");
}
function fe83_fixSigns(s) {
  var t = String(s == null ? "" : s);
  var prev;
  do {
    prev = t;
    t = t.replace(/\+\s*\(\s*\+\s*-(\d[\d,]*(?:\.\d+)?%?)\)/g, "-$1");
    t = t.replace(/\+\s*\(\s*-(\d[\d,]*(?:\.\d+)?%?)\)/g, "-$1");
    t = t.replace(/\+\s*\(\s*\+(\d[\d,]*(?:\.\d+)?%?)\)/g, "+$1");
    t = t.replace(/\(\s*\+\s*-(\d)/g, "(-$1");
    t = t.replace(/\+\s*-(\d)/g, "-$1");
    t = t.replace(/--(\d)/g, "-$1");
  } while (t !== prev);
  return t;
}
function fe83_pctBit(d) {
  var n = fe83_num(d && d.c);
  if (n == null) return "—";
  return fe83_signed(n, "%");
}
function fe83_ptsBit(d) {
  var n = null;
  if (d && typeof d.raw === "number" && isFinite(d.raw)) n = d.raw;
  else n = fe83_num(d && d.chg);
  if (n == null) return "";
  return fe83_signed(n, "");
}
function fe83_chgPair(d) {
  var pts = fe83_ptsBit(d);
  var pct = fe83_num(d && d.c);
  var p = pct == null ? "" : fe83_signed(pct, "%");
  if (pts && p) return pts + " (" + p + ")";
  if (p) return p;
  if (pts) return pts;
  return "—";
}
function fe83_lvl(v) {
  var n = fe83_num(v);
  if (n == null) return "";
  if (Math.abs(n) >= 1000) return n.toLocaleString("en-GB", { maximumFractionDigits: 2 });
  var s = String(n);
  if (s.indexOf("e") >= 0 || s.indexOf("E") >= 0) s = n.toFixed(2);
  return s;
}
function fe83_px(n) {
  var v = fe83_num(n);
  if (v == null) return "";
  return v.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fe83_regimeLine(re) {
  re = re || {};
  var bits = [];
  var name = re.spxProxy ? "SPY" : "SPX";
  var px = fe83_lvl(re.spx);
  var ch = fe83_num(re.spxChg);
  if (px) {
    var bit = name + " " + px;
    if (ch != null) bit += " (" + fe83_signed(ch, "%") + ")";
    if (re.spxProxy) bit += " · tracked via an ETF";
    bits.push(bit);
  } else if (ch != null) bits.push(name + " (" + fe83_signed(ch, "%") + ")");
  var vix = fe83_lvl(re.vix);
  if (vix) bits.push("VIX " + vix);
  var oil = fe83_lvl(re.oil);
  if (oil) bits.push("Oil " + oil);
  var btc = fe83_lvl(re.btc);
  if (btc) bits.push("BTC " + btc);
  if (!bits.length) return "";
  return '<div class="fe83-regime-in" style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5">' + bits.join(" · ") + "</div>";
}
function fe83_vixCell(re) {
  var vix = fe83_lvl(re && re.vix);
  if (!vix) return "";
  return '<div class="ns-cell"><span class="ns-lbl">VIX</span><span class="ns-val">' + vix + "</span></div>";
}
function fe83_scrubText(s) {
  return String(s == null ? "" : s).replace(/(^|[^A-Za-z0-9_])(undefined|NaN|null)(?![A-Za-z0-9_])/g, "$1");
}
function fe83_wd(s) {
  var m = String(s || "").trim().match(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/i);
  if (!m) return "";
  var x = m[1].toLowerCase();
  return x.charAt(0).toUpperCase() + x.slice(1, 3);
}
function fe83_pickDayPure(changeDay, label, feedDay, closed, todayWd) {
  var a = fe83_wd(changeDay) || fe83_wd(label) || fe83_wd(feedDay);
  if (a) return a;
  if (closed && (todayWd === "Sat" || todayWd === "Sun")) return "Fri";
  return "";
}
function fe83_isDxy(sym) {
  var s = String(sym == null ? "" : sym).toUpperCase().replace(/\s/g, "");
  return s === "DXY" || s === "DX-Y.NYB" || s.indexOf("DX-Y.NYB") >= 0;
}
function fe83_goldFrom(g, dc, fut, spotPx) {
  g = g || {};
  dc = (dc && typeof dc === "object") ? dc : {};
  fut = (fut && typeof fut === "object") ? fut : {};
  var pct = fe83_num(g.pct != null ? g.pct : (dc.pct != null ? dc.pct : (fut.changePct != null ? fut.changePct : (fut.c != null ? fut.c : fut.change))));
  var futPx = fe83_num(g.futuresPrice != null ? g.futuresPrice : (g.instrument === "futures" ? (g.price != null ? g.price : g.p) : null));
  if (futPx == null) futPx = fe83_num(dc.price != null ? dc.price : (dc.futuresPrice != null ? dc.futuresPrice : (fut.price != null ? fut.price : fut.p)));
  var spot = fe83_num(g.spotPrice != null ? g.spotPrice : (g.instrument === "spot" ? (g.price != null ? g.price : g.p) : spotPx));
  var inst = String(g.instrument || dc.instrument || "");
  var ptsN = fe83_num(g.points != null ? g.points : (g.pointChange != null ? g.pointChange : (dc.points != null ? dc.points : (dc.pointChange != null ? dc.pointChange : (dc.changePoints != null ? dc.changePoints : fut.points)))));
  var wantFut = inst === "futures" || (futPx != null && pct != null && inst !== "spot");
  if (wantFut && futPx != null) {
    return { kind: "futures", px: futPx, pct: pct, pts: ptsN == null ? "" : fe83_signed(ptsN, ""), label: "Gold futures (GC=F)" };
  }
  if (spot != null) return { kind: "spot", px: spot, pct: null, pts: "", label: "Gold spot" };
  return null;
}
function fe83_goldText(b) {
  if (!b || b.px == null) return "";
  var px = fe83_px(b.px);
  if (!px) return "";
  if (b.kind === "spot") return "Gold spot " + px;
  var pct = b.pct == null ? "" : fe83_signed(b.pct, "%");
  var pts = b.pts ? " · " + b.pts : "";
  return "Gold futures (GC=F) " + px + (pct ? " " + pct : "") + pts;
}
function fe83_sigMode(st) {
  st = st || {};
  if (st.have) return "cards";
  var age = Number(st.age) || 0;
  var hard = !!st.hard || (!!st.err && !st.soft);
  if (age >= 20000) return "unavailable";
  if (st.open || st.pending) return "skeleton";
  if (st.soft && !hard) return "skeleton";
  if (hard) return "unavailable";
  if (st.settled && !st.have && !st.soft) return "unavailable";
  return "skeleton";
}
function fe83_weekLine() {
  var line = "";
  try { if (typeof fe82_acadLabel === "string" && fe82_acadLabel) line = fe82_acadLabel; } catch (e) { line = ""; }
  if (!line) {
    try { if (typeof fe82_hubLine === "function") line = fe82_hubLine() || ""; } catch (e2) { line = ""; }
  }
  return line || "";
}
// FE83_PURE_END
function fe83_todayWd() {
  try { return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date()); } catch (e) { return ""; }
}
function fe83_sessionDay(tk) {
  var b = null, f = null;
  try { b = typeof fe78_bag === "function" ? fe78_bag(tk) : null; } catch (e) { b = null; }
  try { f = typeof fe76_feedOf === "function" ? fe76_feedOf(tk) : null; } catch (e2) { f = null; }
  var feedDay = "";
  if (f) feedDay = f.changeDay || f.sessionDay || f.sessionDayUk || "";
  return fe83_wd(b && b.changeDay) || fe83_wd(b && b.changeDayLabel) || fe83_wd(feedDay);
}
function fe83_marketClosed(tk) {
  try { if (typeof fe78_isClosed === "function" && fe78_isClosed(tk)) return true; } catch (e) {}
  try { if (typeof _rt18MarketOpen === "function") return !_rt18MarketOpen(tk); } catch (e2) {}
  return false;
}
function fe83_pickDay(tk) {
  try { if (typeof fe79_isCryptoTk === "function" && fe79_isCryptoTk(tk)) return ""; } catch (e) {}
  return fe83_pickDayPure(fe83_sessionDay(tk), "", "", fe83_marketClosed(tk), fe83_todayWd());
}
function fe83_goldBits() {
  var g = null, dc = null, fut = null, spot = null;
  try { g = (typeof fe81_goldHeld === "function" && fe81_goldHeld()) || (typeof fe79_goldNow === "function" && fe79_goldNow()); } catch (e) { g = null; }
  try { dc = fe82_goldDc; } catch (e2) { dc = null; }
  try { fut = typeof fe77_futObj === "function" ? fe77_futObj() : null; } catch (e3) { fut = null; }
  try { spot = (typeof P !== "undefined" && P.XAU) ? P.XAU.p : null; } catch (e4) { spot = null; }
  return fe83_goldFrom(g, dc, fut, spot);
}
function fe83_goldLine() {
  return fe83_goldText(fe83_goldBits());
}
function fe83_scrubDom() {
  if (typeof document === "undefined" || !document.body) return;
  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  var n;
  while ((n = walker.nextNode())) {
    var p = n.parentNode;
    if (!p || /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(p.tagName || "")) continue;
    var v = n.nodeValue;
    if (!v) continue;
    if (/undefined|\bNaN\b|\bnull\b/.test(v)) n.nodeValue = fe83_scrubText(v);
    if (v.indexOf("Dispatch FX basket") >= 0) n.nodeValue = n.nodeValue.replace(/Dispatch FX basket/g, "US Dollar Index (ICE)");
  }
}
function fe83_paintGold() {
  var b = fe83_goldBits();
  if (!b || typeof document === "undefined") return;
  var px = fe83_px(b.px);
  var pct = b.kind === "futures" && b.pct != null ? fe83_signed(b.pct, "%") : "";
  var day = fe83_pickDay("XAU");
  var chg = b.kind === "spot" ? "Gold spot" : ((pct || "") + (b.pts ? " · " + b.pts : "") + (day ? " " + day : "")).replace(/^\s+/, "");
  document.querySelectorAll(".wl-glance-chip").forEach(function (el) {
    var oc = el.getAttribute("onclick") || "";
    if (oc.indexOf("XAU") < 0 && oc.indexOf("GC=F") < 0) return;
    var pe = el.querySelector(".wl-g-p"), ce = el.querySelector(".wl-g-c");
    if (pe) { pe.textContent = px; pe.title = b.label; }
    if (ce) ce.textContent = (b.label + (chg ? " " + chg : "")).replace(/\s+/g, " ").trim();
  });
  document.querySelectorAll(".rt47-qrow").forEach(function (row) {
    var html = row.innerHTML || "";
    if (html.indexOf("XAU") < 0 && html.indexOf("Gold") < 0 && html.indexOf("GC=F") < 0) return;
    var qn = row.querySelector(".rt47-qn"), qp = row.querySelector(".rt47-qp"), qc = row.querySelector(".rt47-qc");
    if (qn) qn.textContent = b.label;
    if (qp) qp.textContent = px;
    if (qc) qc.textContent = pct;
  });
  document.querySelectorAll("[data-price-card='XAU'],[data-tk='XAU']").forEach(function (el) {
    var pe = el.querySelector(".asset-price,.conv-px,.idx-card-px");
    var ce = el.querySelector(".asset-chg,.change,.conv-chg,.idx-card-chg");
    var nm = el.querySelector(".conv-nm,.idx-card-name,.spine-lbl");
    if (nm) nm.textContent = b.label;
    if (pe && px) pe.textContent = (el.getAttribute("data-price-dollar") === "1" ? "$" : "") + px;
    if (ce && b.kind === "futures") ce.textContent = fe83_fixSigns((pct || "") + (b.pts ? " · " + b.pts : "") + (day ? " " + day : ""));
    if (ce && b.kind === "spot") ce.textContent = "Gold spot";
  });
  document.querySelectorAll(".spine-cell").forEach(function (el) {
    var tk = el.querySelector(".spine-tk");
    if (!tk || String(tk.textContent || "").trim() !== "XAU") return;
    var lb = el.querySelector(".spine-lbl");
    var pe = el.querySelector(".spine-px");
    var ce = el.querySelector(".spine-chg");
    if (lb) {
      var rest = lb.innerHTML.replace(/^[^<]*/, "");
      lb.innerHTML = b.label + (rest && rest.charAt(0) !== " " && rest.charAt(0) !== "<" ? " " : "") + rest;
    }
    if (pe && px) pe.textContent = px;
    if (ce && b.kind === "futures") ce.textContent = fe83_fixSigns((pct || "") + (b.pts ? " · " + b.pts : "") + (day ? " " + day : ""));
    if (ce && b.kind === "spot") ce.textContent = "Gold spot";
  });
}
function fe83_paintDays() {
  if (typeof document === "undefined") return;
  document.querySelectorAll(".asset-chg,.wl-g-c,.spine-chg,.idx-card-chg,.conv-chg,.sector-dash-pct").forEach(function (el) {
    if (el.children && el.children.length) return;
    var t = el.textContent || "";
    var n = fe83_fixSigns(t);
    var card = el.closest("[data-price-card],[data-tk]");
    var tk = card ? (card.getAttribute("data-price-card") || card.getAttribute("data-tk") || "") : "";
    if (!tk && el.classList.contains("wl-g-c")) {
      var chip = el.closest(".wl-glance-chip");
      var oc = chip ? (chip.getAttribute("onclick") || "") : "";
      var m = oc.match(/openA\('([^']+)'\)/);
      tk = m ? m[1] : "";
    }
    var day = tk ? fe83_pickDay(tk) : "";
    if (day) n = n.replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b(?!.*\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b)/, day);
    if (n !== t) el.textContent = n;
  });
}
function fe83_afterPaint() {
  try { fe83_scrubDom(); } catch (e) {}
  try { fe83_paintGold(); } catch (e2) {}
  try { fe83_paintDays(); } catch (e3) {}
}
function fe83_sigView() {
  var have = false, open = false, hard = false, soft = false, pending = false, settled = false;
  try {
    have = (typeof SIGS !== "undefined" ? SIGS : []).some(function (s) {
      return s && typeof hasSyncedQuote === "function" && hasSyncedQuote(s.tk);
    });
  } catch (e) { have = false; }
  var slots = (typeof fe82_quoteWait !== "undefined" && fe82_quoteWait) ? fe82_quoteWait : [];
  if (slots.length) settled = true;
  for (var i = 0; i < slots.length; i++) {
    var s = slots[i];
    if (!s.done || s.pendingBody) { open = true; settled = false; }
    if (s.pendingBody) pending = true;
    if (s.soft) soft = true;
    else if (s.err) hard = true;
  }
  var age = 0;
  try { age = fe82_sigT0 ? (Date.now() - fe82_sigT0) : 0; } catch (e2) { age = 0; }
  return fe83_sigMode({ have: have, open: open, hard: hard, soft: soft, pending: pending, settled: settled, age: age });
}
var fe83_sigShown = "";
try {
  var fe83_chgText0 = fe78_chgText;
  fe78_chgText = function (tk, s) {
    var out = "";
    try { out = fe83_chgText0.apply(this, arguments); } catch (e) { out = String(s || ""); }
    out = fe83_fixSigns(out);
    var day = fe83_pickDay(tk);
    if (day && /\d/.test(out)) {
      out = String(out).replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b(?!.*\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b)/i, "");
      if (out.indexOf(day) < 0) out = out.replace(/\s+$/, "") + " " + day;
    }
    return fe83_scrubText(out);
  };
} catch (eChg) {}
try {
  var fe83_day0 = _rt26Day;
  _rt26Day = function (tk) {
    var sess = fe83_sessionDay(tk);
    if (sess) return sess;
    var prev = "";
    try { prev = fe83_day0.apply(this, arguments) || ""; } catch (e) { prev = ""; }
    var today = fe83_todayWd();
    if (fe83_marketClosed(tk) && (prev === today || /^sat|^sun/i.test(prev))) {
      if (today === "Sat" || today === "Sun" || /^sat|^sun/i.test(prev)) return "Fri";
      return "";
    }
    return prev;
  };
} catch (eDay) {}
try {
  var fe83_qm0 = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe83_qm0.apply(this, arguments);
    try {
      var day = fe83_pickDay(tk);
      if (day && m && m.detail) m.detail = String(m.detail).replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/, day);
    } catch (e) {}
    return m;
  };
} catch (eQm) {}
try {
  var fe83_fp0 = fp;
  fp = function (tk) {
    var d = fe83_fp0.apply(this, arguments);
    try {
      var id = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
      if ((id === "XAU" || id === "GC=F") && d) {
        var b = fe83_goldBits();
        if (b && b.kind === "futures") {
          d.p = fe83_px(b.px);
          if (b.pct != null) d.c = Number(b.pct).toFixed(2);
          if (b.pts) d.chg = b.pts;
        } else if (b && b.kind === "spot") {
          d.p = fe83_px(b.px);
          d.c = "";
          d.chg = "";
        }
      }
    } catch (e) {}
    return d;
  };
} catch (eFp) {}
try {
  var fe83_lc0 = liveChg;
  liveChg = function (tk) {
    var id = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
    if (id === "XAU" || id === "GC=F") {
      var b = null;
      try { b = fe83_goldBits(); } catch (e) { b = null; }
      if (b && b.kind === "futures" && b.pct != null) return b.pct;
      if (b && b.kind === "spot") return null;
    }
    return fe83_lc0.apply(this, arguments);
  };
} catch (eLc) {}
try {
  var fe83_tape0 = fe65_tapeName;
  fe65_tapeName = function (tk) {
    var key = tk;
    try { key = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk; } catch (e) { key = tk; }
    if (fe83_isDxy(key) || fe83_isDxy(tk)) return "US Dollar Index (ICE)";
    if (key === "XAU" || key === "GC=F") {
      var b = fe83_goldBits();
      if (b) return b.label;
    }
    return fe83_tape0.apply(this, arguments);
  };
} catch (eTape) {}
try { fe77_dxyName = function () { return "US Dollar Index (ICE)"; }; } catch (eDn) {}
try { fe77_dxyTitle = function () { return "US Dollar Index (ICE)"; }; } catch (eDt) {}
try { fe78_dxyLabel = function () { return "US Dollar Index (ICE)"; }; } catch (eDl) {}
try {
  var fe83_prep0 = fe77_prepDxy;
  fe77_prepDxy = function (data) {
    var q = fe83_prep0.apply(this, arguments);
    if (q && typeof q === "object") q.name = "US Dollar Index (ICE)";
    try { if (typeof liveQuoteName !== "undefined") liveQuoteName.DXY = "US Dollar Index (ICE)"; } catch (e) {}
    return q;
  };
} catch (ePrep) {}
try {
  var fe83_ref0 = fe77_takeRef;
  fe77_takeRef = function (data) {
    var r = fe83_ref0.apply(this, arguments);
    try { fe77_dxyLabel = "US Dollar Index (ICE)"; } catch (e) {}
    try { if (typeof liveQuoteName !== "undefined") liveQuoteName.DXY = "US Dollar Index (ICE)"; } catch (e2) {}
    return r;
  };
} catch (eRef) {}
try {
  var fe83_chip0 = fe82_fixChip;
  fe82_fixChip = function (el, tk) {
    try { fe83_chip0.apply(this, arguments); } catch (e) {}
    try { if (tk === "XAU" || tk === "GC=F") fe83_paintGold(); } catch (e2) {}
  };
} catch (eChip) {}
try {
  var fe83_re0 = _renderRegimeEngine;
  _renderRegimeEngine = function (re) {
    var h = "";
    try { h = fe83_re0.apply(this, arguments); } catch (e) { h = ""; }
    return fe83_scrubText(h);
  };
} catch (eRe) {}
try {
  var fe83_ctx0 = _buildChatContext;
  _buildChatContext = function () {
    var t = "";
    try { t = fe83_ctx0.apply(this, arguments); } catch (e) { t = ""; }
    return fe83_scrubText(fe83_fixSigns(t));
  };
} catch (eCtx) {}
try {
  var fe83_br0 = _renderDispatchBrief;
  _renderDispatchBrief = function () {
    var h = "";
    try { h = fe83_br0.apply(this, arguments); } catch (e) { h = ""; }
    return fe83_scrubText(h);
  };
} catch (eBr) {}
try {
  var fe83_intel0 = _computeLocalIntel;
  _computeLocalIntel = function () {
    var o = null;
    try { o = fe83_intel0.apply(this, arguments); } catch (e) { o = null; }
    try {
      if (o && typeof o.insight === "string") o.insight = fe83_scrubText(fe83_fixSigns(o.insight));
      if (o && typeof o.headline === "string") o.headline = fe83_scrubText(o.headline);
    } catch (e2) {}
    return o;
  };
} catch (eIn) {}
try {
  var fe83_fresh0 = _rt48Fresh;
  _rt48Fresh = function (t) {
    try {
      if (typeof t === "number" && typeof _rt48Wk !== "undefined" && _rt48Wk && t === _rt48Wk.at && fe82_acadLabel) return fe82_acadLabel;
    } catch (e) {}
    var line = "";
    try { line = fe83_fresh0.apply(this, arguments); } catch (e2) { line = ""; }
    return fe83_scrubText(line);
  };
} catch (eFr) {}
try {
  fe82_sigMode = function (st) { return fe83_sigMode(st); };
  fe82_sigState = function () { return fe83_sigView(); };
} catch (eMode) {}
try {
  var fe83_tick0 = fe82_sigTick;
  fe82_sigTick = function () {
    var mode = "";
    try { mode = fe82_sigState(); } catch (e) { mode = ""; }
    var prev = fe83_sigShown;
    try { fe83_tick0.apply(this, arguments); } catch (e2) {}
    try {
      if (!fe82_onSig()) return;
      var desk = typeof IS_DESKTOP === "function" && IS_DESKTOP();
      var root = desk ? document.getElementById("p3body") : document.getElementById("main");
      if (!root) return;
      var skel = !!root.querySelector("[data-fe82=sig-skel]");
      var bad = /UNAVAILABLE|No price yet|No source returned/i.test(root.textContent || "");
      if ((mode === "cards" || mode === "unavailable") && (skel || (bad && prev !== mode) || prev === "skeleton" || prev === "unavailable")) {
        if (desk && typeof fe82_p30 === "function") fe82_p30();
        else if (!desk && typeof renderMain === "function") renderMain();
      }
    } catch (e3) {}
    if (mode) fe83_sigShown = mode;
  };
} catch (eTick) {}
try {
  var fe83_fetch0 = window.fetch.bind(window);
  window.fetch = function (input) {
    var url = "";
    try { url = typeof input === "string" ? input : (input && input.url) || ""; } catch (e0) { url = ""; }
    var p = fe83_fetch0.apply(window, arguments);
    if (typeof fe82_isQuoteUrl !== "function" || !fe82_isQuoteUrl(url)) return p;
    var slot = (fe82_quoteWait && fe82_quoteWait.length) ? fe82_quoteWait[fe82_quoteWait.length - 1] : null;
    return Promise.resolve(p).then(function (r) {
      if (slot) slot.pendingBody = true;
      try {
        r.clone().text().then(function (t) {
          if (!slot) return;
          slot.pendingBody = false;
          if (/no source returned/i.test(String(t || "")) && !/"p"\s*:\s*[1-9]/.test(String(t || ""))) {
            slot.soft = true;
            slot.err = false;
          }
        }).catch(function () { if (slot) slot.pendingBody = false; });
      } catch (e2) { if (slot) slot.pendingBody = false; }
      return r;
    }, function (err) {
      var msg = String((err && err.message) || err || "");
      if (slot && /no source returned/i.test(msg)) { slot.soft = true; slot.err = false; slot.pendingBody = false; }
      throw err;
    });
  };
} catch (eFetch) {}
try {
  var fe83_ask0 = fe79_askChip;
  fe79_askChip = function (meta) {
    var chip = fe83_ask0.apply(this, arguments);
    try {
      var q = (meta && meta.quote) || meta || {};
      if (q && q.quoteLine) return chip;
      var blob = [q.symbol, q.ticker, q.tk, q.label, q.name].join(" ");
      if (/XAU|GC=F|gold/i.test(blob) && chip && typeof chip === "object") {
        var line = fe83_goldLine();
        if (line) {
          chip.line = line;
          if (line.indexOf("%") < 0) chip.basis = "";
        }
      }
    } catch (e) {}
    return chip;
  };
} catch (eAsk) {}
try { setInterval(fe83_afterPaint, 400); } catch (eIv) {}
"""


def die(msg):
    print("FAIL", msg)
    sys.exit(1)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


def nrep(text, old, new, label, nexpected):
    n = text.count(old)
    if n != nexpected:
        die("%s count %s expected %s" % (label, n, nexpected))
    return text.replace(old, new)


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
    start = '<div style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5">'
    i = app.find(start)
    if i < 0 or app.find(start, i + 1) >= 0:
        die("regime line count")
    j = app.find("</div>", i)
    block = app[i:j + len("</div>")]
    if "VIX ${re.vix}" not in block or "re.btc" not in block:
        die("regime line shape")
    app = app[:i] + "${fe83_regimeLine(re)}" + app[j + len("</div>"):]
    app = once(
        app,
        '<div class="ns-cell"><span class="ns-lbl">VIX</span><span class="ns-val">${re.vix}</span></div>',
        "${fe83_vixCell(re)}",
        "vix cell",
    )
    app = once(
        app,
        "if (id === 'week') return _rt48WkReady() ? _rt48Fresh(_rt48Wk.at) : 'Building from live data…';",
        "if (id === 'week') { var fe83w = (typeof fe83_weekLine===\"function\" ? fe83_weekLine() : \"\"); return fe83w || (_rt48WkReady() ? _rt48Fresh(_rt48Wk.at) : 'Building from live data…'); }",
        "week status",
    )
    app = nrep(app, '${sign}${d.chg} (${sign}${d.c}%)', '${fe83_chgPair(d)}', "chg pair", 6)
    app = nrep(app, '${sign}${d.c}%', '${fe83_pctBit(d)}', "chg pct", 10)
    app = nrep(app, 'sign+d.c+"%"', "fe83_pctBit(d)", "book pct", 2)
    app = once(
        app,
        'const abs = hasChange ? `${d.raw >= 0 ? "+" : ""}${d.chg}` : "";',
        "const abs = hasChange ? fe83_ptsBit(d) : \"\";",
        "glance pts",
    )
    app = once(
        app,
        'const chgLbl=na?(d.status==="unavailable"?"NO SYNC":d.label):`${ch!=null&&ch>=0?"+":""}${d.c}%`;',
        'const chgLbl=na?(d.status==="unavailable"?"NO SYNC":d.label):fe83_pctBit(d);',
        "watch pct",
    )
    app = once(
        app,
        '<div class="sector-dash-pct" style="color:${col}">${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%</div>',
        '<div class="sector-dash-pct" style="color:${col}">${fe83_signed(pct, "%")}</div>',
        "sector pct",
    )
    app = once(
        app,
        'return arrow + sign + abs + " (" + sign + pctBody + "%)" + (day && day !== "today" ? " " + day : "");',
        'return fe83_fixSigns(arrow + fe83_signed(abs, "") + " (" + fe83_signed(pctBody, "%") + ")" + (day && day !== "today" ? " " + fe83_pickDayPure(day, "", "", false, "") : ""));',
        "fe66 line",
    )
    app = once(
        app,
        'return " " + sign + fe76_group(abs, 2) + " (" + sign + pct.toFixed(2) + "%)";',
        'return " " + fe83_chgPair({ raw: abs, c: pct });',
        "quote chg",
    )
    app = once(
        app,
        'const chg = !synced || chN == null ? "—" : fe78_chgHtml(s.tk, `${chN >= 0 ? "+" : ""}${d.c}%`);',
        'const chg = !synced || chN == null ? "—" : fe78_chgHtml(s.tk, fe83_pctBit(d) || "—");',
        "spine pct",
    )
    app = once(
        app,
        'const avgLbl = avg == null ? "—" : `${avg >= 0 ? "+" : ""}${avg.toFixed(2)}%`;',
        'const avgLbl = avg == null ? "—" : (fe83_signed(avg, "%") || "—");',
        "sector avg",
    )
    app = once(
        app,
        '`${ch > 0 ? "▲" : ch < 0 ? "▼" : "•"} ${sign}${Number(ch).toFixed(2)}%`',
        '`${ch > 0 ? "▲" : ch < 0 ? "▼" : "•"} ${fe83_signed(ch, "%")}`',
        "glance fallback",
    )
    return app


def pure_slice(app):
    a = app.find("// FE83_PURE_START")
    b = app.find("// FE83_PURE_END")
    if a < 0 or b < 0 or b <= a:
        die("pure slice")
    return app[a:b]


def run_unit(app_text):
    src = pure_slice(app_text) + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
assert(fe83_signed(-1.29, "%") === "-1.29%", "neg");
assert(fe83_signed(1.29, "%") === "+1.29%", "pos");
assert(fe83_signed("-1.29", "%") === "-1.29%", "neg str");
assert(fe83_signed("+-1.29", "%") === "-1.29%", "dbl str");
assert(fe83_fixSigns("+ (+-1.29%) Sat").indexOf("+-") < 0, "fix pair");
assert(fe83_fixSigns("+ (+-1.29%) Sat").indexOf("+ (") < 0, "fix paren");
assert(fe83_fixSigns("+-1.29% Sat") === "-1.29% Sat", "fix concat");
assert(fe83_fixSigns("--1.29%") === "-1.29%", "fix minus");
assert(fe83_fixSigns("+1.29%") === "+1.29%", "keep pos");
assert(fe83_fixSigns("-1.29%") === "-1.29%", "keep neg");
assert(fe83_pctBit({ c: "-1.29" }) === "-1.29%", "pct bit");
assert(fe83_chgPair({ raw: -52.5, c: "-1.29" }) === "-52.50 (-1.29%)", "pair");
assert(fe83_chgPair({ raw: -52.5, c: "-1.29" }).indexOf("+-") < 0, "pair clean");
var full = fe83_regimeLine({ spx: 7623.68, spxChg: -0.52, vix: 18.2, oil: 78, btc: 9613 });
assert(full.indexOf("SPX 7,623.68 (-0.52%)") >= 0, "spx");
assert(full.indexOf("VIX 18.2") >= 0, "vix");
assert(full.indexOf("undefined") < 0 && full.indexOf("NaN") < 0, "full clean");
assert(fe83_regimeLine({ spx: undefined, vix: undefined, oil: undefined, btc: undefined }) === "", "none");
assert(fe83_regimeLine({ vix: 18.2, spx: null, oil: NaN, btc: "undefined" }).indexOf("SPX") < 0, "only vix names");
assert(fe83_regimeLine({ vix: 18.2 }).indexOf("VIX 18.2") >= 0, "only vix");
assert(fe83_regimeLine({ spx: 100, spxChg: undefined, vix: null }).indexOf("undefined") < 0, "miss chg");
assert(fe83_vixCell({ vix: undefined }) === "", "vix omit");
assert(fe83_vixCell({ vix: 18.2 }).indexOf("18.2") >= 0, "vix show");
assert(fe83_scrubText("SPX $undefined (undefined%) · VIX undefined").indexOf("undefined") < 0, "scrub");
assert(fe83_scrubText("value null and NaN").indexOf("null") < 0 && fe83_scrubText("value null and NaN").indexOf("NaN") < 0, "scrub words");
assert(fe83_pickDayPure("Fri", "", "", true, "Sat") === "Fri", "day fri");
assert(fe83_pickDayPure("", "Friday session", "Fri 23 Oct", true, "Sat") === "Fri", "day label");
assert(fe83_pickDayPure("", "", "", true, "Sat") === "Fri", "weekend");
assert(fe83_pickDayPure("Thu", "Fri", "", true, "Sat") === "Thu", "changeDay wins");
assert(fe83_isDxy("DXY") && fe83_isDxy("DX-Y.NYB"), "dxy");
var fut = fe83_goldFrom({ instrument: "futures", pct: -1.29, price: 4007.9, points: -51.7 }, {}, {}, 3996.9);
var futTxt = fe83_goldText(fut);
assert(fut.kind === "futures", "fut kind");
assert(futTxt.indexOf("Gold futures (GC=F)") >= 0 && futTxt.indexOf("4,007.90") >= 0 && futTxt.indexOf("-1.29%") >= 0, "fut line");
assert(futTxt.indexOf("3,996.90") < 0, "fut not spot");
var spot = fe83_goldFrom({ instrument: "spot", price: 3996.9 }, {}, {}, 3996.9);
var spotTxt = fe83_goldText(spot);
assert(spot.kind === "spot" && spotTxt.indexOf("Gold spot") >= 0 && spotTxt.indexOf("%") < 0, "spot line");
var mixed = fe83_goldFrom({ instrument: "futures", pct: -1.29 }, {}, {}, 3996.9);
assert(fe83_goldText(mixed).indexOf("%") < 0 && fe83_goldText(mixed).indexOf("Gold spot") >= 0, "no mix");
assert(fe83_sigMode({ have: true, hard: true, age: 100 }) === "cards", "sig cards");
assert(fe83_sigMode({ open: true, age: 3500, hard: true }) === "skeleton", "sig open");
assert(fe83_sigMode({ soft: true, settled: true, age: 4000 }) === "skeleton", "sig soft");
assert(fe83_sigMode({ hard: true, settled: true, age: 500 }) === "unavailable", "sig hard");
assert(fe83_sigMode({ settled: true, age: 500 }) === "unavailable", "sig empty");
assert(fe83_sigMode({ open: true, age: 20000 }) === "unavailable", "sig timeout");
assert(fe83_sigMode({ pending: true, age: 4000, settled: true }) === "skeleton", "sig pending");
assert(fe83_sigMode({ err: true, settled: true, age: 400 }) === "unavailable", "sig err flag");
assert(fe83_sigMode({ err: true, soft: true, age: 4000 }) === "skeleton", "sig err soft");
assert(fe83_weekLine() === "" || typeof fe83_weekLine() === "string", "week");
console.log("fe83 unit ok");
"""
    if "function fe82_tapePct(" not in app_text or "function fe80_regArr(" not in app_text:
        die("prior guards missing")
    if "re.overweight.some" in app_text or "re.underweight.some" in app_text:
        die("raw regime read returned")
    if 'app.js?v=chat83"' in app_text:
        die("cache bust leaked into app")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe83 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def main():
    if not BLOCK.lstrip().startswith("// ── rt62e ──"):
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
    if index.count('app.js?v=chat82"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count("function fe83_signed(") != 1 or app.count("function fe83_regimeLine(") != 1:
        die("fe83 def")
    if app.count("function fe82_tapePct(") != 1 or app.count("function fe80_regArr(") != 1:
        die("prior helper def")
    index = index.replace('app.js?v=chat82"', 'app.js?v=chat83"', 1)
    if index.count('app.js?v=chat83"') != 1:
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
