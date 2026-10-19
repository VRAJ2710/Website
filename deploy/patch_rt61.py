#!/usr/bin/env python3
"""rt61 client patch: chat75 -> chat76. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "f04a23106569a925bd4f8b8b761023ca"
EXPECT_INDEX_MD5 = "9c36a61819819960b2b25487f8c27d0e"
NEED_MARKER = "// ── rt60b ──"
REFUSE_MARKER = "// ── rt61 ──"

BLOCK = r'''
// ── rt61 ──
function fe76_vword(v) {
  if (v == null) return "";
  return String(v)
    .replace(/\b(?:AVOID|Avoid|avoid)\b/g, "Weak")
    .replace(/\b(?:BUY|Buy|buy)\b/g, "Positive")
    .replace(/\b(?:SELL|Sell|sell)\b/g, "Negative");
}
var fe76_hold = Object.create(null);
var fe76_spotPrev = null;
var fe76_skipRender = 0;
function fe76_ms(v) {
  var n = Number(v);
  if (!(n > 0)) return 0;
  if (n < 1e11) n *= 1000;
  return n;
}
function fe76_group(n, dp) {
  return Number(n).toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp });
}
function fe76_commas(s) {
  return String(s == null ? "" : s).replace(/(\d+)(\.\d+)?/g, function (_m, i, d) {
    return i.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (d || "");
  });
}
function fe76_isFx(tk) {
  var raw = String(tk || "");
  var t = raw.toUpperCase();
  if (/=X$/.test(t)) return true;
  try { if (typeof fe73_ccy === "function" && fe73_ccy(t) === "FX") return true; } catch (e) {}
  var bare = t.replace(/=X$/, "");
  if (/^[A-Z]{6}$/.test(bare) && /USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD|HKD|CNH|SEK|NOK/.test(bare)) return true;
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && String(x.tk).toUpperCase() === bare; }) : null;
    if (a && String(a.cat || "").toUpperCase() === "FX") return true;
  } catch (e2) {}
  return false;
}
function fe76_jpy(tk) {
  return String(tk || "").toUpperCase().replace(/=X$/, "").indexOf("JPY") >= 0;
}
function fe76_looksZero(tk, n) {
  var v = Number(n);
  if (!isFinite(v) || !(v > 0)) return true;
  var dp = 2;
  if (fe76_isFx(tk)) dp = fe76_jpy(tk) ? 2 : 4;
  else if (Math.abs(v) < 1) dp = 4;
  return Number(v.toFixed(dp)) === 0;
}
function fe76_plain(tk, n) {
  var v = Number(n);
  if (fe76_isFx(tk)) return fe76_group(v, fe76_jpy(tk) ? 2 : 4);
  try {
    if (typeof _rtIsCrypto === "function" && _rtIsCrypto(tk) && v < 1 && typeof _rtCryptoPx === "function") return _rtCryptoPx(v);
  } catch (e) {}
  var whole = false;
  try { var c = fe66_ccy(tk); whole = c === "JPY" || c === "KRW"; } catch (e2) {}
  if (whole) return fe76_group(Math.round(v), 0);
  return fe76_group(v, Math.abs(v) >= 1 ? 2 : 4);
}
function fe76_open(tk) {
  try { return typeof _rt18MarketOpen === "function" && !!_rt18MarketOpen(tk); } catch (e) { return false; }
}
function fe76_wdAt(ms) {
  if (!(ms > 0)) return "";
  try { return new Date(ms).toLocaleDateString("en-GB", { weekday: "short", timeZone: "Europe/London" }); } catch (e) { return ""; }
}
function fe76_quoteMs(tk) {
  var ts = 0;
  try { var h = fe76_hold[tk]; if (h && h.ts) ts = h.ts; } catch (e) {}
  if (!(ts > 0)) { try { ts = fe76_ms(typeof liveQuoteTs !== "undefined" ? liveQuoteTs[tk] : 0); } catch (e2) {} }
  if (ts && Math.abs(Date.now() - ts) < 180000) return 0;
  return ts || 0;
}
function fe76_barWd(tk) {
  try { var bag = (typeof _rt23Ch !== "undefined") ? _rt23Ch[tk] : null; if (bag && bag.fe76wd) return bag.fe76wd; } catch (e) {}
  return "";
}
var fe76_feedMap = Object.create(null);
function fe76_keepFeed(tk, q) {
  if (!tk || !q || !q.feed || typeof q.feed !== "object") return;
  var f = q.feed;
  if (!f.status && !f.sessionDayUk && !f.sessionLabel && !f.fallback) return;
  fe76_feedMap[tk] = f;
}
function fe76_feedOf(tk) {
  var f = fe76_feedMap[tk];
  if (f) return f;
  try {
    var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null;
    if (y && y.feed && typeof y.feed === "object") return y.feed;
  } catch (e) {}
  return null;
}
function fe76_feedLabel(f) {
  if (!f) return "";
  if (f.fallback && f.sessionLabel) return String(f.sessionLabel);
  var st = String(f.status || "").toLowerCase();
  if (st === "live") return "LIVE";
  if (st === "delayed") {
    var n = Number(f.delayMin);
    if (!(n > 0) && Number(f.ageSec) > 0) n = Math.max(1, Math.round(Number(f.ageSec) / 60));
    return n > 0 ? ("delayed " + Math.round(n) + " min") : "delayed";
  }
  if (st === "stale") return "stale";
  if (st === "closed") return "CLOSED";
  return "";
}
function fe76_priceDay(tk) {
  var f = fe76_feedOf(tk);
  if (f && f.sessionDayUk) return String(f.sessionDayUk);
  var ms = fe76_quoteMs(tk);
  if (ms) return fe76_wdAt(ms);
  var bar = fe76_barWd(tk);
  if (bar) return bar;
  try { ms = fe76_ms(typeof _rt20LastClose === "function" ? _rt20LastClose(tk) : 0); } catch (e) {}
  return fe76_wdAt(ms);
}
function fe76_chartDay(tk) {
  var f = fe76_feedOf(tk);
  if (f && f.sessionDayUk) return String(f.sessionDayUk);
  var bar = fe76_barWd(tk);
  if (bar) return bar;
  return fe76_priceDay(tk);
}
function fe76_day(tk) { return fe76_priceDay(tk); }
function fe76_head(tk) {
  var f = fe76_feedOf(tk);
  if (f) {
    if (f.fallback && f.sessionLabel) return String(f.sessionLabel);
    var st = String(f.status || "").toLowerCase();
    if (st === "live" || st === "delayed") return "Today";
    if (f.sessionDayUk) return "Last session \u00b7 " + f.sessionDayUk;
  }
  if (fe76_open(tk)) return "Today";
  var wd = fe76_chartDay(tk);
  return wd ? ("Last session \u00b7 " + wd) : "Last session";
}
function fe76_fixDay(tk, s) {
  var head = fe76_head(tk);
  var up = fe76_open(tk) ? "TODAY" : head.toUpperCase();
  return String(s || "").replace(/Last session(?: \u00b7 [A-Za-z]{3})?/ig, head).replace(/LAST SESSION(?: \u00b7 [A-Za-z]{3})?/g, up);
}
function fe76_quote(tk) {
  var live = null, prev = null, c = null;
  try {
    if (typeof P !== "undefined" && P[tk]) {
      live = Number(P[tk].p);
      if (isFinite(Number(P[tk].c))) c = Number(P[tk].c);
    }
  } catch (e) {}
  try { if (typeof BASE !== "undefined" && BASE[tk]) prev = Number(BASE[tk].p); } catch (e2) {}
  var px = (live > 0 && !fe76_looksZero(tk, live)) ? live : null;
  if (px == null) {
    var holdPrev = 0;
    try { holdPrev = fe76_hold[tk] && Number(fe76_hold[tk].prev); } catch (eH) { holdPrev = 0; }
    if (prev > 0 && !fe76_looksZero(tk, prev)) {
      px = prev;
      prev = null;
      c = null;
    } else if (holdPrev > 0 && !fe76_looksZero(tk, holdPrev)) {
      px = holdPrev;
      prev = null;
      c = null;
    } else {
      var hist = [], i, a = null, b = null, h;
      try { hist = (typeof HIST !== "undefined" && HIST[tk]) || []; } catch (e3) { hist = []; }
      for (i = hist.length - 1; i >= 0; i--) {
        h = Number(hist[i]);
        if (h > 0 && !fe76_looksZero(tk, h)) { if (a == null) a = h; else { b = h; break; } }
      }
      if (a == null) {
        try {
          var pts = _rt23Ch[tk] && _rt23Ch[tk].pts;
          if (pts) {
            for (i = pts.length - 1; i >= 0; i--) {
              h = Number(pts[i]);
              if (h > 0 && !fe76_looksZero(tk, h)) { if (a == null) a = h; else { b = h; break; } }
            }
          }
        } catch (e4) {}
      }
      if (a != null) {
        px = a;
        if (b != null) { prev = b; c = ((a - b) / Math.abs(b)) * 100; }
        else { prev = null; c = null; }
      }
    }
  }
  var out = { px: px, prev: prev > 0 ? prev : null, c: c, live: (live > 0 && !fe76_looksZero(tk, live)) ? live : 0 };
  if (String(tk || "") === "XAU" || String(tk || "").toUpperCase() === "GC=F") {
    var sp = (typeof fe76_spotPrev === "number" && fe76_spotPrev > 0 && out.px > 0 && Math.abs(fe76_spotPrev - out.px) > Math.max(0.01, out.px * 1e-8)) ? fe76_spotPrev : null;
    out.prev = sp;
    out.c = sp ? ((out.px - sp) / Math.abs(sp)) * 100 : null;
  }
  return out;
}
function fe76_applyStatus(tk, o) {
  if (!o) return o;
  var feed = fe76_feedOf(tk);
  if (feed && (feed.status || feed.fallback)) {
    var fl = fe76_feedLabel(feed);
    if (fl) {
      if (feed.status) o.status = String(feed.status);
      o.label = fl;
      o.fe64Note = fl;
      o.detail = fl;
      if (feed.asOf) o.asOf = feed.asOf;
      if (feed.ageSec != null) o.ageSec = feed.ageSec;
      return o;
    }
  }
  var src = String(o.src || "");
  try { if (!src && typeof liveQuoteSrc !== "undefined") src = String(liveQuoteSrc[tk] || ""); } catch (e) {}
  var asOf = 0;
  try { asOf = fe76_ms(o.asOf || (typeof liveQuoteTs !== "undefined" ? liveQuoteTs[tk] : 0)); } catch (e2) {}
  var age = asOf ? Date.now() - asOf : null;
  var stream = /yahoo-stream|coinbase-ws|kraken-ws/.test(src);
  var fresh = !!(stream && age != null && age < 30000 && age > -60000);
  var delay = 0;
  try { var b = typeof fe70_bag === "function" ? fe70_bag(tk) : null; if (b && b.delayMin > 0) delay = Math.round(b.delayMin); } catch (e3) {}
  try { var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null; if (y && y.delayMin > 0) delay = Math.round(y.delayMin); } catch (e4) {}
  var status = o.status, label = "";
  if (delay > 0 && status !== "closed" && status !== "lunch" && status !== "opening") {
    status = "delayed";
    label = "delayed " + delay + " min";
  } else if (fresh || status === "live") {
    status = "live";
    label = "LIVE";
  } else return o;
  o.status = status;
  o.label = label;
  o.fe64Note = label;
  if (!o.detail || /delayed|live/i.test(String(o.detail))) o.detail = label;
  return o;
}
try {
  var fe76_money0 = fe66_money;
  fe66_money = function (tk, n) {
    var v = Number(n);
    if (!isFinite(v) || fe76_looksZero(tk, v)) return "\u2014";
    if (fe76_isFx(tk)) return fe76_plain(tk, v);
    return fe76_commas(fe76_money0(tk, v));
  };
} catch (e) {}
try {
  var fe76_absTk = "";
  var fe76_abs0 = fe73_absText;
  fe73_absText = function (ccy, n) {
    if (ccy === "FX" || fe76_isFx(fe76_absTk)) {
      var v = Number(n);
      if (!isFinite(v)) return "";
      var sign = v < 0 ? "-" : (v > 0 ? "+" : "");
      return sign + fe76_group(Math.abs(v), fe76_jpy(fe76_absTk) ? 2 : 4);
    }
    return fe76_commas(fe76_abs0(ccy, n));
  };
  var fe76_move0 = fe73_move;
  fe73_move = function (o) {
    fe76_absTk = o && o.tk || "";
    try { return fe76_move0.apply(this, arguments); }
    finally { fe76_absTk = ""; }
  };
} catch (e) {}
try {
  var fe76_show0 = fe66_show;
  fe66_show = function (tk) {
    var q = fe76_quote(tk);
    if (q.px > 0) return fe66_money(tk, q.px);
    var s = "";
    try { s = fe76_show0.apply(this, arguments); } catch (e) { s = ""; }
    if (!s || /^HK\$0\.00|^\$0\.00|^0\.00/.test(String(s))) return "\u2014";
    return s;
  };
} catch (e) {}
try {
  fe66_pull = function (tk) {
    try { tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk; } catch (e0) {}
    if (!tk) return;
    if (!fe66_pull.on) fe66_pull.on = Object.create(null);
    if (fe66_pull.on[tk]) return;
    fe66_pull.on[tk] = 1;
    var yh = tk;
    try { yh = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk; } catch (e1) {}
    fetch("/api/yahoo-quote?symbols=" + encodeURIComponent(yh), { signal: AbortSignal.timeout(8000) }).then(function (r) {
      return r && r.ok ? r.json() : null;
    }).then(function (data) {
      var q = null;
      try { q = fe66_pick(data, yh, tk); } catch (e2) { q = null; }
      if (!q) { delete fe66_pull.on[tk]; return; }
      try { fe76_keepFeed(tk, q); } catch (e3) {}
      var px = Number(q.p), prev = Number(q.prev);
      if (!(px > 0) || fe76_looksZero(tk, px)) {
        if (prev > 0 && !fe76_looksZero(tk, prev)) {
          fe76_hold[tk] = { prev: prev, ts: fe76_ms(q.ts || q.fetchedAt) || 0 };
          try { if (q.currency && typeof fe66_setCcy === "function" && q.currency !== "FX") fe66_setCcy(tk, q.currency); } catch (e4) {}
        }
        delete fe66_pull.on[tk];
      } else {
        try { _applyLiveQuote(tk, q, "yahoo"); } catch (e5) {}
      }
      try { if (typeof _patchP2LiveHeader === "function") _patchP2LiveHeader(); } catch (e6) {}
      try {
        if (typeof IS_DESKTOP === "function" && IS_DESKTOP()) { if (typeof renderP2 === "function") renderP2(); }
        else if (typeof renderMain === "function") renderMain();
      } catch (e7) {}
    }).catch(function () { delete fe66_pull.on[tk]; });
  };
  setTimeout(function () {
    var bootTk = "";
    try { bootTk = new URLSearchParams(location.search).get("t") || ""; } catch (e8) {}
    if (!bootTk) {
      try { bootTk = (typeof termSelTk !== "undefined" && termSelTk) || (typeof selTk !== "undefined" && selTk) || ""; } catch (e9) { bootTk = ""; }
    }
    if (!bootTk) return;
    try { if (fe66_pull.on) delete fe66_pull.on[bootTk]; } catch (e10) {}
    try { fe66_pull(bootTk); } catch (e11) {}
  }, 30);
} catch (e) {}
try {
  var fe76_p2 = renderP2;
  renderP2 = function () {
    var r = fe76_p2.apply(this, arguments);
    try { if (document.body.classList.contains("fe68-lenses")) fe76_lensPlace(); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_pl0 = fe66_priceLine;
  fe66_priceLine = function (tk) {
    var q = fe76_quote(tk);
    if (q.px > 0) return fe66_money(tk, q.px);
    return fe76_pl0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_chg0 = fe73_chgLine;
  fe73_chgLine = function (tk, d, na) {
    var q = fe76_quote(tk);
    if ((String(tk) === "XAU" || String(tk).toUpperCase() === "GC=F") && q.c == null) return "";
    var open = fe76_open(tk);
    if (!(q.live > 0)) {
      if (!(q.px > 0)) return "\u2014";
      if (q.c == null) {
        var quiet = open ? "" : fe76_priceDay(tk);
        return quiet || (open ? "" : "Last close");
      }
      var day = open ? "" : fe76_priceDay(tk);
      var moved = fe73_move({ tk: tk, px: q.px, prev: q.prev, c: q.c, open: open, lastWd: day });
      var line = moved && moved.line && moved.line !== "\u2014" ? moved.line : "";
      if (!line) return open ? "\u2014" : ("Last close" + (day ? " \u00b7 " + day : ""));
      if (!open && day && !/(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$/.test(line)) line += " " + day;
      return line;
    }
    var out = fe76_chg0.apply(this, arguments);
    out = fe76_fixDay(tk, out);
    if (open) out = String(out).replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$/i, "");
    else if (fe76_day(tk)) {
      out = String(out).replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$/i, "");
      if (out && out !== "\u2014") out += " " + fe76_day(tk);
    }
    return out;
  };
  fe66_chgLine = fe73_chgLine;
} catch (e) {}
try {
  var fe76_fp0 = fp;
  fp = function (tk) {
    var d = fe76_fp0.apply(this, arguments);
    if (!d) return d;
    var q = fe76_quote(tk);
    if (!(q.px > 0)) { d.p = "\u2014"; return d; }
    d.p = fe76_plain(tk, q.px);
    if ((String(tk) === "XAU" || String(tk).toUpperCase() === "GC=F") && q.c == null) { d.c = ""; d.chg = ""; return d; }
    if (q.c == null && !(q.live > 0)) { d.c = "\u2014"; d.chg = "\u2014"; }
    return d;
  };
} catch (e) {}
try {
  var fe76_px0 = _rtCryptoPx;
  _rtCryptoPx = function (v) {
    var n = Number(v);
    if (!isFinite(n) || !(n > 0)) return "\u2014";
    if (n >= 1) return fe76_group(n, 2);
    return fe76_px0(n);
  };
} catch (e) {}
try {
  var fe76_dyn0 = fe66_dynHead;
  fe66_dynHead = function (tk) {
    try { var lunch = typeof fe66b_line === "function" ? fe66b_line(tk) : ""; if (lunch) return lunch; } catch (e) {}
    var s = "";
    try { s = fe76_dyn0.apply(this, arguments); } catch (e2) { s = ""; }
    return fe76_fixDay(tk, s);
  };
} catch (e) {}
try {
  var fe76_bit0 = fe66_chartBit;
  fe66_chartBit = function (tk) {
    if (String(tk || "") === "XAU" || String(tk || "").toUpperCase() === "GC=F") return "Gold futures (GC=F, delayed 10 min)";
    try { var lunch = typeof fe66b_line === "function" ? fe66b_line(tk) : ""; if (lunch) return lunch; } catch (e) {}
    var s = "";
    try { s = fe76_bit0.apply(this, arguments); } catch (e2) { s = ""; }
    return fe76_fixDay(tk, s);
  };
} catch (e) {}
try {
  var fe76_ch0 = _rt24ChartHead;
  _rt24ChartHead = function (tk, range) {
    if (String(range || "").toLowerCase() === "1d") return fe76_head(tk);
    return fe76_ch0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_lbl0 = _rt23ChartLbl;
  _rt23ChartLbl = function (tk) {
    try { var lunch = typeof fe66b_line === "function" ? fe66b_line(tk) : ""; if (lunch) return lunch; } catch (e) {}
    if (fe76_open(tk)) return "Today";
    var s = "";
    try { s = fe76_lbl0.apply(this, arguments); } catch (e2) { s = ""; }
    if (/last session/i.test(s) || !s) return fe76_head(tk);
    return fe76_fixDay(tk, s);
  };
} catch (e) {}
try {
  var fe76_cf0 = _rt23ChartFetch;
  _rt23ChartFetch = async function (tk) {
    var out = await fe76_cf0.apply(this, arguments);
    try {
      var bag = _rt23Ch[tk];
      var m = bag && bag.label ? /LAST SESSION \u00b7 ([A-Za-z]{3})/.exec(bag.label) : null;
      if (m) bag.fe76wd = m[1].charAt(0).toUpperCase() + m[1].slice(1).toLowerCase();
    } catch (e) {}
    return out;
  };
} catch (e) {}
try {
  var fe76_badge0 = fe68_badge;
  fe68_badge = function (m, tk) {
    var o = fe76_badge0.apply(this, arguments);
    return fe76_applyStatus(tk, o);
  };
} catch (e) {}
try {
  var fe76_fin0 = fe70_finish;
  fe70_finish = function (tk, m) {
    var o = fe76_fin0.apply(this, arguments);
    return fe76_applyStatus(tk, o);
  };
} catch (e) {}
try {
  var fe76_fl0 = fe65_feedLbl;
  fe65_feedLbl = function (d, tk) {
    var o = fe76_applyStatus(tk, Object.assign({}, d || {}));
    if (o && o.label && (o.status === "live" || o.status === "delayed")) return o.label;
    return fe76_fl0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_view0 = fe73_viewRow;
  fe73_viewRow = function (row) {
    var copy = fe76_view0(row);
    if (!copy || !row) return copy;
    var whenUk = row.whenUk ? String(row.whenUk) : "";
    if (!whenUk && row.transactionDateMissing) {
      var miss = "";
      try { miss = fe73_showDate(row.filingDateUk, row.filingDate) || ""; } catch (eM) { miss = ""; }
      whenUk = miss ? ("Trade date not reported \u00b7 filed " + miss) : "Trade date not reported";
    }
    if (whenUk) {
      copy.fe76Trade = whenUk;
      copy.fe76Filed = "";
    } else {
      try { copy.fe76Trade = fe73_showDate(row.transactionDateUk, row.transactionDate) || ""; } catch (e) { copy.fe76Trade = ""; }
      try { copy.fe76Filed = fe73_showDate(row.filingDateUk, row.filingDate) || ""; } catch (e2) { copy.fe76Filed = ""; }
    }
    copy.fe76Role = row.insiderRole || "";
    return copy;
  };
} catch (e) {}
try {
  fe69_insRow = function (row) {
    row = row || {};
    var role = row.fe76Role || row.insiderRole || "";
    var trade = row.fe76Trade || "";
    var filed = row.fe76Filed || "";
    if (!trade && !row.fe76Trade && !row.fe76Filed) {
      var shown = String(row.transactionDate || "");
      var fm = shown.match(/^(.*?)\s+\u00b7\s+filed\s+(.*)$/);
      if (fm) { trade = fm[1]; filed = fm[2]; }
      else trade = shown || String(row.filingDate || "");
    }
    if (!trade) trade = "\u2014";
    var link = row.filingUrl ? ' <a href="' + fe68_esc(row.filingUrl) + '" target="_blank" rel="noopener noreferrer">Filing</a>' : "";
    var span = "";
    try { span = fe69_insSpan(row.shares, row.value); } catch (e) { span = ""; }
    var tip = "";
    try { tip = typeof _escAttr === "function" ? _escAttr(role) : fe68_esc(role); } catch (e2) { tip = fe68_esc(role); }
    return '<div class="institutional-row fe76-ins"><strong>' + fe68_esc(row.insiderName || "Insider") + '</strong><span class="fe76-role" title="' + tip + '">' + fe68_esc(role) + '</span><span>' + fe68_esc(row.codeLabel || row.transactionCode || "") + span + '</span><small>' + fe68_esc(trade) + (filed ? " \u00b7 filed " + fe68_esc(filed) : "") + link + "</small></div>";
  };
} catch (e) {}
try {
  var fe76_ins0 = fe69_insHtml;
  fe69_insHtml = function (tk, data) {
    var html = fe76_ins0.apply(this, arguments);
    var n = 0;
    try { if (data && Array.isArray(data.insider)) n += data.insider.length; } catch (e) {}
    try { if (typeof fe69_extra !== "undefined" && fe69_extra[tk]) n += fe69_extra[tk].length; } catch (e2) {}
    if (!n) html = String(html).replace(/<p class="ex[^"]*"[^>]*>[\s\S]*?Latest 5 open-market trades[\s\S]*?<\/p>/gi, "");
    return html;
  };
  fe68_insHtml = fe69_insHtml;
} catch (e) {}
function fe76_closeLens() {
  try { document.body.classList.remove("fe68-lenses"); } catch (e) {}
  try { document.body.style.overflow = ""; document.documentElement.style.overflow = ""; } catch (e2) {}
  var bd = document.getElementById("fe76-lens-bd");
  if (bd) bd.remove();
  try {
    var p = document.querySelector(".panel.p-expanded");
    if (p) p.classList.remove("p-expanded");
    var g = document.getElementById("panelGrid");
    if (g) g.classList.remove("has-expanded");
    if (typeof _expPanel !== "undefined") _expPanel = null;
  } catch (e3) {}
}
function fe76_scroller(el) {
  var n = el;
  while (n && n !== document.documentElement) {
    try {
      var oy = getComputedStyle(n).overflowY;
      if ((oy === "auto" || oy === "scroll") && n.scrollHeight > n.clientHeight + 4) return n;
    } catch (e) {}
    n = n.parentElement;
  }
  return el;
}
function fe76_lensPlace() {
  var wide = false;
  try { wide = window.innerWidth >= 768; } catch (e) {}
  var on = false;
  try { on = document.body.classList.contains("fe68-lenses"); } catch (e2) {}
  var bd = document.getElementById("fe76-lens-bd");
  if (!wide || !on) {
    if (bd) bd.remove();
    if (!on) { try { document.body.style.overflow = ""; } catch (e3) {} }
    return;
  }
  if (!bd) {
    bd = document.createElement("div");
    bd.id = "fe76-lens-bd";
    document.body.appendChild(bd);
  }
  try { document.body.style.overflow = "hidden"; } catch (e4) {}
  var host = document.querySelector(".panel.p-expanded") || document.getElementById("p2");
  if (!host) return;
  var area = host.querySelector("#term-lens-thesis") || host.querySelector(".ap-committee-btn");
  var target = area && area.parentElement ? area.parentElement : area;
  if (!target) return;
  var body = document.getElementById("p2body") || host.querySelector(".panel-body");
  var sc = null;
  var nodes = [body, host];
  var i, n, oy;
  for (i = 0; i < nodes.length; i++) {
    n = nodes[i];
    if (!n) continue;
    try {
      oy = getComputedStyle(n).overflowY;
      if ((oy === "auto" || oy === "scroll") && n.scrollHeight > n.clientHeight + 4) { sc = n; break; }
    } catch (e5) {}
  }
  if (!sc) sc = fe76_scroller(target) || body || host;
  var delta = target.getBoundingClientRect().top - sc.getBoundingClientRect().top;
  if (Math.abs(delta) > 2) sc.scrollTop += delta;
}
function fe76_fitAsk() {
  var wide = false;
  try { wide = window.innerWidth >= 768; } catch (e) {}
  if (!wide) return;
  var ask = document.querySelector('[data-fe70-ask="desk"]');
  var auth = document.getElementById("cmdAuthBtn");
  if (!ask || !auth) return;
  ask.style.setProperty("position", "static", "important");
  ask.style.setProperty("z-index", "auto", "important");
  auth.style.setProperty("flex", "0 0 auto", "important");
  auth.style.setProperty("overflow", "visible", "important");
  var input = document.querySelector(".cmd-input");
  var guard = 0;
  function hit() {
    var a = ask.getBoundingClientRect(), b = auth.getBoundingClientRect();
    if (a.width < 2 || b.width < 2) return false;
    return !(a.right <= b.left + 0.5 || b.right <= a.left + 0.5 || a.bottom <= b.top + 0.5 || b.bottom <= a.top + 0.5);
  }
  while (hit() && input && guard++ < 14) {
    var w = input.getBoundingClientRect().width;
    if (w <= 88) break;
    input.style.setProperty("max-width", Math.max(80, Math.floor(w - 36)) + "px", "important");
  }
}
function fe76_ovLock() {
  var ov = null, desk = false;
  try { ov = document.querySelector(".term-overlay"); desk = window.innerWidth >= 768 && ov && ov.getClientRects().length; } catch (e) {}
  try { document.documentElement.classList.toggle("fe76-ov", !!desk); } catch (e2) {}
}
function fe76_css() {
  if (document.getElementById("fe76-css")) return;
  var st = document.createElement("style");
  st.id = "fe76-css";
  st.textContent = [
    "@media (max-width:767px){#bnav,#bnav.fe71-bar{background:#0c0c0e!important;background-color:#0c0c0e!important;-webkit-backdrop-filter:none!important;backdrop-filter:none!important}}",
    ".fe71-session{display:flex;flex-wrap:wrap;align-items:baseline}",
    ".fe76-chunk{white-space:nowrap}",
    ".fe76-span{grid-column:1 / -1!important}",
    ".fe71 .more-nav-panel{scroll-padding-top:160px}",
    ".fe71-grp h3{scroll-margin-top:160px}",
    ".fe71-grid .fe71-tile:last-child:nth-child(odd){grid-column:1 / -1!important}",
    "@media (min-width:768px){html body.fe70-home #homeOv,html body.fe70-home #homeOv.term-overlay{padding-left:28px!important;padding-right:28px!important;box-sizing:border-box}}",
    "@media (min-width:768px){.cmd-bar{flex-wrap:nowrap;min-width:0}.cmd-ac-wrap{min-width:0;flex:1 1 auto}[data-fe70-ask=desk]{position:static!important;z-index:auto!important;flex:0 0 auto}#cmdAuthBtn{flex:0 0 auto!important;overflow:visible!important;min-width:max-content;position:relative;z-index:3}}",
    "@media (min-width:768px){#fe76-lens-bd{position:fixed;inset:0;background:rgba(6,6,8,.62);z-index:92}html body.fe68-lenses .sidebar{z-index:40!important}html body.fe68-lenses .panel.p-expanded{position:fixed!important;top:var(--desk-chrome,92px)!important;left:var(--sidebar-w,172px)!important;right:0!important;bottom:0!important;height:auto!important;max-height:none!important;margin:0!important;z-index:94!important;background:var(--paper,#14161c)!important;overflow:auto!important}html body.fe68-lenses #p2body{padding-bottom:75vh!important}}",
    "#term-ins-root,#anlz-ins-root,.fe68-ins{flex:0 0 auto!important;height:auto!important;min-height:0!important;padding-bottom:8px!important}",
    ".fe68-ins .institutional-row{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1.6fr) minmax(0,1.3fr) minmax(88px,.9fr);gap:6px 12px;align-items:start;padding:8px 0;border-top:1px solid rgba(255,255,255,.06)}",
    ".fe68-ins .fe76-role{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere;min-width:0}",
    "html.fe76-ov,html.fe76-ov body{overflow:hidden!important}",
    "html.fe76-ov .term-overlay{background:var(--paper,#101114)!important}",
    ".fe76-qlines{margin-top:8px}",
    ".fe76-qline{font-variant-numeric:tabular-nums;margin-top:4px;color:var(--t2,#c8c8c8);font-size:12px;letter-spacing:0}",
    ".fe76-fut{font-family:var(--mn);font-size:10px;color:var(--t3);padding:6px 2px 0}"
  ].join("");
  document.head.appendChild(st);
}
try { fe76_css(); } catch (e) {}
try {
  var fe76_open0 = fe71_openMoreNav;
  fe71_openMoreNav = function () {
    var out = fe76_open0.apply(this, arguments);
    function fe76_sheet(n) {
      var sheet = document.getElementById("moreNav");
      var panel = sheet && sheet.querySelector(".more-nav-panel");
      if (!panel) return;
      var on = sheet.querySelector(".fe71-tile.on");
      var id = on ? on.getAttribute("data-fe71") : "";
      var home = !on || id === "home" || (typeof pg !== "undefined" && pg === "home");
      if (home) { panel.scrollTop = 0; }
      else {
        var anchor = on;
        var sec = on.closest ? on.closest(".fe71-grp") : null;
        var h3 = sec && sec.querySelector("h3");
        if (h3) anchor = h3;
        var pr = panel.getBoundingClientRect();
        var tr = anchor.getBoundingClientRect();
        var stick = 0;
        var swipe = sheet.querySelector(".fe71-swipe");
        if (swipe) stick = swipe.getBoundingClientRect().height;
        var hidden = tr.top < pr.top + stick - 1 || tr.bottom > pr.bottom - 1;
        if (hidden) panel.scrollTop += tr.top - pr.top - stick - 8;
      }
      if (n < 6) setTimeout(function () { fe76_sheet(n + 1); }, 180);
    }
    try { setTimeout(function () { fe76_sheet(0); }, 100); } catch (e) {}
    return out;
  };
  openMoreNav = fe71_openMoreNav;
} catch (e) {}
try {
  var fe76_html0 = fe71_sheetHtml;
  fe71_sheetHtml = function () {
    var html = fe76_html0.apply(this, arguments);
    html = String(html).replace(/<p class="fe71-session">([\s\S]*?)<\/p>/, function (_m, inner) {
      var text = inner.replace(/<[^>]+>/g, "");
      var parts = text.split("\u00b7").map(function (p) { return p.trim(); }).filter(Boolean);
      return '<p class="fe71-session">' + parts.map(function (p) { return '<span class="fe76-chunk">' + p + "</span>"; }).join('<span class="fe76-dot"> \u00b7 </span>') + "</p>";
    });
    html = html.replace(/<div class="fe71-grid">([\s\S]*?)<\/div>/g, function (_m, inner) {
      var tiles = inner.match(/<(?:button|a)\b/g) || [];
      if (tiles.length % 2 === 0) return '<div class="fe71-grid">' + inner + "</div>";
      var at = Math.max(inner.lastIndexOf("<button "), inner.lastIndexOf("<a "));
      if (at < 0) return '<div class="fe71-grid">' + inner + "</div>";
      var patched = inner.slice(0, at) + inner.slice(at).replace('class="fe71-tile', 'class="fe71-tile fe76-span');
      return '<div class="fe71-grid">' + patched + "</div>";
    });
    return html;
  };
} catch (e) {}
try {
  document.addEventListener("click", function (e) {
    var wide = false;
    try { wide = window.innerWidth >= 768; } catch (err) {}
    if (!wide || !document.body.classList.contains("fe68-lenses")) return;
    if (e.target && e.target.id === "fe76-lens-bd") {
      e.preventDefault();
      e.stopPropagation();
      fe76_closeLens();
      return;
    }
    var b = e.target && e.target.closest ? e.target.closest("button") : null;
    if (!b) return;
    var t = String(b.textContent || "").replace(/\s+/g, " ").trim();
    if (t === "\u2190 BACK" || t === "\u2190 Back") {
      e.preventDefault();
      e.stopPropagation();
      fe76_closeLens();
    }
  }, true);
} catch (e) {}
try {
  document.addEventListener("keydown", function (e) {
    if (!e || e.key !== "Escape") return;
    var wide = false;
    try { wide = window.innerWidth >= 768; } catch (err) {}
    if (!wide || !document.body.classList.contains("fe68-lenses")) return;
    e.preventDefault();
    e.stopPropagation();
    fe76_closeLens();
  }, true);
} catch (e) {}
try {
  var fe76_tab0 = _setATab;
  _setATab = function (t) {
    var r = fe76_tab0.apply(this, arguments);
    try {
      fe76_lensPlace();
      if (window.fe76_lensIv) clearInterval(window.fe76_lensIv);
      var ticks = 0;
      window.fe76_lensIv = setInterval(function () {
        ticks++;
        if (ticks > 16 || !document.body.classList.contains("fe68-lenses")) { clearInterval(window.fe76_lensIv); window.fe76_lensIv = 0; return; }
        fe76_lensPlace();
      }, 200);
    } catch (e) {}
    try { fe76_ovLock(); } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_fit0 = fe73_fitHeader;
  fe73_fitHeader = function () {
    var r = fe76_fit0.apply(this, arguments);
    try { fe76_fitAsk(); } catch (e) {}
    try { fe76_ovLock(); } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_nav0 = nav;
  nav = function () {
    var r = fe76_nav0.apply(this, arguments);
    try { fe76_fitAsk(); fe76_ovLock(); fe76_lensPlace(); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_aq0 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q) {
    var ok = false;
    try { ok = fe76_aq0.apply(this, arguments); } catch (e) { ok = false; }
    try {
      if (q && tk) {
        var px = Number(q.p), prev = Number(q.prev), ts = fe76_ms(q.ts || q.fetchedAt || q.regularMarketTime);
        try { if (q.currency && typeof fe66_setCcy === "function" && q.currency !== "FX") fe66_setCcy(tk, q.currency); } catch (eC) {}
        try { fe76_keepFeed(tk, q); } catch (eF) {}
        if (tk === "XAU" && px > 0 && fe76_spotSrc(q) && fe76_ownPrev(px, prev)) fe76_spotPrev = prev;
        if (!(px > 0) || fe76_looksZero(tk, px)) {
          if (prev > 0 && !fe76_looksZero(tk, prev)) fe76_hold[tk] = { prev: prev, ts: ts || 0 };
        } else if (ts && Math.abs(Date.now() - ts) >= 180000) {
          fe76_hold[tk] = { prev: prev > 0 ? prev : px, ts: ts, real: 1 };
        }
      }
    } catch (e2) {}
    return ok;
  };
} catch (e) {}
try { setTimeout(function () { try { fe76_fitAsk(); fe76_ovLock(); } catch (e) {} }, 400); } catch (e) {}
var fe76_chatGen = 1;
var fe76_chatSeal = 0;
var fe76_liveEpoch = 1;
var fe76_saveT = 0;
function fe76_chatScrub() {
  var ver = "chat70";
  try { var cur = localStorage.getItem("td_chat_v"); if (cur) ver = cur; } catch (e) {}
  try {
    var lk = Object.keys(localStorage);
    for (var i = 0; i < lk.length; i++) {
      if (/^td_chat/.test(lk[i]) && lk[i] !== "td_chat_v") localStorage.removeItem(lk[i]);
    }
    localStorage.setItem("td_chat_v", ver);
  } catch (e2) {}
  try {
    var sk = Object.keys(sessionStorage);
    for (var j = 0; j < sk.length; j++) if (/^td_chat/.test(sk[j])) sessionStorage.removeItem(sk[j]);
  } catch (e3) {}
}
function fe76_installMsgs(arr) {
  var base = Array.isArray(arr) ? arr.slice() : [];
  _chatMsgs = new Proxy(base, {
    get: function (t, p) {
      if (p === "push" || p === "unshift") {
        return function () {
          if (fe76_chatSeal === fe76_chatGen) return t.length;
          return Array.prototype[p].apply(t, arguments);
        };
      }
      var v = t[p];
      return typeof v === "function" ? v.bind(t) : v;
    },
    set: function (t, p, v) {
      if (fe76_chatSeal === fe76_chatGen) {
        if (p === "length") t.length = v > 0 ? t.length : 0;
        return true;
      }
      t[p] = v;
      return true;
    }
  });
}
function fe76_chatWriteNow() {
  if (fe76_chatSeal === fe76_chatGen) { fe76_chatScrub(); return; }
  var msgs = _chatMsgs || [];
  if (!msgs.length) {
    try { localStorage.removeItem("td_chat"); } catch (e) {}
    try { sessionStorage.removeItem("td_chat"); } catch (e2) {}
    try { if (!localStorage.getItem("td_chat_v")) localStorage.setItem("td_chat_v", "chat70"); } catch (e3) {}
    return;
  }
  var blob = "[]";
  try { blob = JSON.stringify(msgs.slice(-20)); } catch (e4) { blob = "[]"; }
  try { localStorage.setItem("td_chat", blob); } catch (e5) {}
  try { localStorage.setItem("td_chat_v", "chat70"); } catch (e6) {}
  try {
    var sk = Object.keys(sessionStorage);
    for (var i = 0; i < sk.length; i++) if (/^td_chat/.test(sk[i])) sessionStorage.removeItem(sk[i]);
  } catch (e7) {}
}
function fe76_chatSave() {
  var gen = fe76_chatGen;
  clearTimeout(fe76_saveT);
  fe76_saveT = setTimeout(function () {
    if (gen !== fe76_chatGen) return;
    fe76_chatWriteNow();
  }, 180);
}
function fe76_chatFlush() {
  clearTimeout(fe76_saveT);
  if (fe76_chatSeal === fe76_chatGen) { fe76_chatScrub(); return; }
  fe76_chatWriteNow();
}
function fe76_chatHold() {
  try {
    var sk = Object.keys(sessionStorage);
    for (var i = 0; i < sk.length; i++) if (/^td_chat/.test(sk[i])) sessionStorage.removeItem(sk[i]);
  } catch (e) {}
  if (fe76_chatSeal !== fe76_chatGen) return;
  fe76_chatScrub();
  fe76_installMsgs([]);
}
function fe76_chatWipe() {
  fe76_chatGen++;
  fe76_chatSeal = fe76_chatGen;
  fe76_liveEpoch++;
  try { _chatLoad = false; } catch (e0) {}
  clearTimeout(fe76_saveT);
  fe76_chatScrub();
  fe76_installMsgs([]);
  fe76_chatScrub();
}
try {
  var fe76_set0 = Storage.prototype.setItem;
  Storage.prototype.setItem = function (key, val) {
    var k = String(key);
    if (fe76_chatSeal === fe76_chatGen && /^td_chat/.test(k) && k !== "td_chat_v" && (this === window.localStorage || this === window.sessionStorage)) return;
    return fe76_set0.apply(this, arguments);
  };
} catch (e) {}
try { fe76_installMsgs(_chatMsgs); } catch (e) {}
try { _persistChat = fe76_chatSave; } catch (e) {}
try { fe73_chatWrite = fe76_chatSave; } catch (e) {}
try {
  var fe76_clearPrev = clearChat;
  clearChat = function () {
    fe76_chatWipe();
    try { if (typeof fe76_clearPrev === "function") fe76_clearPrev(); } catch (e) {}
    fe76_chatWipe();
    try { if (typeof _renderChatMsgs === "function") _renderChatMsgs(); } catch (e2) {}
  };
} catch (e) {}
try {
  var fe76_readPrev = fe73_chatRead;
  fe73_chatRead = function () {
    if (fe76_chatSeal === fe76_chatGen) { fe76_chatHold(); return; }
    var r = fe76_readPrev.apply(this, arguments);
    try { fe76_installMsgs(_chatMsgs); } catch (e) {}
    try {
      var sk = Object.keys(sessionStorage);
      for (var i = 0; i < sk.length; i++) if (/^td_chat/.test(sk[i])) sessionStorage.removeItem(sk[i]);
    } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_tgPrev = toggleChat;
  toggleChat = function () {
    fe76_chatHold();
    var r = fe76_tgPrev.apply(this, arguments);
    fe76_chatHold();
    return r;
  };
} catch (e) {}
try {
  var fe76_osPrev = openSettings;
  openSettings = function () {
    fe76_chatHold();
    var r = fe76_osPrev.apply(this, arguments);
    fe76_chatHold();
    return r;
  };
} catch (e) {}
try {
  window.addEventListener("beforeunload", fe76_chatFlush);
  window.addEventListener("pagehide", fe76_chatFlush);
} catch (e) {}
try {
  var fe76_sendPrev = sendChatMessage;
  sendChatMessage = function (retryText) {
    if (retryText == null) {
      fe76_chatGen++;
      fe76_chatSeal = 0;
      fe76_liveEpoch++;
      try { _chatLoad = false; } catch (e0) {}
    }
    return fe76_sendPrev.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_fetchPrev = window.fetch;
  window.fetch = function (input, init) {
    var u = "";
    try { u = typeof input === "string" ? input : (input && input.url) || ""; } catch (e0) { u = ""; }
    var chat = String(u).indexOf("/api/chat") >= 0;
    var epoch = fe76_liveEpoch;
    var p = fe76_fetchPrev.apply(this, arguments);
    if (p && typeof p.then === "function" && String(u).indexOf("/api/search") >= 0) {
      var symQ = "";
      try { var qm = String(u).match(/[?&]q=([^&]+)/); if (qm) symQ = decodeURIComponent(qm[1]).toUpperCase(); } catch (e1) {}
      fe76_lastSearch = { sym: symQ, p: p.then(function (res) { return res.clone().json(); }).catch(function () { return null; }) };
    }
    if (p && typeof p.then === "function" && String(u).indexOf("/api/brief") >= 0) {
      p.then(function (res) { return res.clone().json().then(function (j) { fe76_noteEdition(j); }).catch(function () {}); }).catch(function () {});
    }
    if (!chat || !p || typeof p.then !== "function") return p;
    return p.then(function (res) {
      if (epoch !== fe76_liveEpoch) return new Promise(function () {});
      return res;
    });
  };
} catch (e) {}
function fe76_spotSrc(o) {
  var src = String((o && (o.src || o.source)) || "");
  return /gold-api|twelve-data|spot-proxy/i.test(src);
}
function fe76_ownPrev(p, prev) {
  if (!(prev > 0) || !(p > 0)) return false;
  if (Math.abs(prev - p) <= Math.max(0.01, Math.abs(p) * 1e-8)) return false;
  try {
    var g = (typeof _rt !== "undefined" && _rt) ? _rt.gcPct : null;
    if (g && isFinite(g.c) && Math.abs(g.c) > 1e-9) {
      var synth = p / (1 + g.c / 100);
      if (Math.abs(prev - synth) <= Math.max(0.05, Math.abs(p) * 1e-5)) return false;
    }
  } catch (e) {}
  return true;
}
function fe76_spotPct() {
  var p = 0;
  try { p = Number(P.XAU && P.XAU.p); } catch (e) {}
  if (!fe76_ownPrev(p, fe76_spotPrev)) return null;
  return +(((p - fe76_spotPrev) / fe76_spotPrev) * 100).toFixed(2);
}
function fe76_blankXau() {
  if (fe76_spotPct() != null) return;
  try {
    document.querySelectorAll('#tape .ti[data-tk="XAU"]').forEach(function (el) {
      if (el.children && el.children[2]) el.children[2].textContent = "";
    });
  } catch (e) {}
}
try {
  var fe76_applySpot0 = _rtApply;
  _rtApply = function (tk, p, o) {
    var opt = o || {};
    if (tk === "XAU") {
      opt = Object.assign({}, opt);
      var prev = typeof opt.prev === "number" ? opt.prev : null;
      if (fe76_spotSrc(opt) && fe76_ownPrev(p, prev)) fe76_spotPrev = prev;
      else {
        delete opt.prev;
        opt.noBasePrev = true;
      }
    }
    var ok = fe76_applySpot0.call(this, tk, p, opt);
    if (tk === "XAU" && ok) {
      var pct = fe76_spotPct();
      try {
        if (pct == null) {
          if (P.XAU) P.XAU.c = 0;
          liveQuoteChangeAvailable.XAU = false;
        } else if (P.XAU) {
          P.XAU.c = pct;
          liveQuoteChangeAvailable.XAU = true;
        }
      } catch (e2) {}
    }
    return ok;
  };
} catch (e) {}
try {
  var fe76_xauChg0 = _rt24XauChg;
  _rt24XauChg = function (tk) {
    if (tk === "XAU") return fe76_spotPct();
    return fe76_xauChg0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_ref0 = _rt37Ref;
  _rt37Ref = function (tk, q) {
    if (tk === "XAU") return q;
    return fe76_ref0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_39 = _rt39Chg;
  _rt39Chg = function (tk) {
    if (tk === "XAU") return null;
    return fe76_39.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_lc1 = liveChg;
  liveChg = function (tk) {
    if (tk === "XAU") return fe76_spotPct();
    return fe76_lc1.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_rc1 = referenceChg;
  referenceChg = function (tk) {
    if (tk === "XAU") return fe76_spotPct();
    return fe76_rc1.apply(this, arguments);
  };
} catch (e) {}
try { _rtGoldKicker = function () { return "Gold spot"; }; } catch (e) {}
try { _rtGoldKickerTitle = function () { return "Gold spot"; }; } catch (e) {}
try {
  var fe76_tape0 = fe65_tapeName;
  fe65_tapeName = function (tk) {
    if (tk === "XAU") return "Gold spot";
    return fe76_tape0.apply(this, arguments);
  };
} catch (e) {}
try {
  _gdPx = function (n) {
    var v = Number(n);
    if (!isFinite(v)) return "\u2014";
    return fe76_group(v, Math.abs(v) >= 1 ? 2 : 4);
  };
} catch (e) {}
try {
  var fe76_fd0 = _frontDoorQuote;
  _frontDoorQuote = function (tk, name, description) {
    if (tk === "XAU") name = "Gold spot";
    return fe76_fd0.call(this, tk, name, description);
  };
} catch (e) {}
try {
  var fe76_goldHtml0 = _renderGoldSurface;
  _renderGoldSurface = function () {
    var h = fe76_goldHtml0.apply(this, arguments);
    if (typeof h !== "string") return h;
    var fut = "Gold futures (GC=F, delayed 10 min)";
    h = h.replace(/Spot: reference feed · Levels &amp; volatility: COMEX gold futures \(GC=F\) daily bars, Yahoo Finance, delayed/g, "Gold spot · " + fut);
    h = h.replace(/COMEX gold futures \(GC=F\) · Yahoo Finance daily bars, delayed[^<]*/g, fut);
    h = h.replace(/Computed from COMEX futures daily bars \(20\/50-day averages, ATR 14\)\./g, fut + ".");
    h = h.replace(/Support\/resistance: swing lows\/highs on COMEX futures daily bars \(last 90 sessions\), in futures prices\. Touches = sessions that came within 0\.3%\./g, fut + ".");
    h = h.replace(/COMEX gold futures daily bars\. Condition: ATR under 0\.9% of price = low, 0\.9–1\.8% = normal, above 1\.8% = elevated\./g, fut + ".");
    h = h.replace(/Loading COMEX futures bars…/g, fut);
    h = h.replace(/COMEX gold futures/g, fut);
    return h;
  };
} catch (e) {}
try {
  var fe76_struct0 = _gdStructText;
  _gdStructText = function () {
    return String(fe76_struct0.apply(this, arguments) || "").replace(/COMEX gold futures/g, "Gold futures (GC=F, delayed 10 min)");
  };
} catch (e) {}
try {
  var fe76_candle0 = renderCandleChart;
  renderCandleChart = async function (tk) {
    var r = await fe76_candle0.apply(this, arguments);
    try {
      if (String(tk || "") !== "XAU" && String(tk || "").toUpperCase() !== "GC=F") return r;
      var box = document.getElementById(arguments[2]);
      if (!box || box.querySelector(".fe76-fut")) return r;
      var note = document.createElement("div");
      note.className = "fe76-fut";
      note.textContent = "Gold futures (GC=F, delayed 10 min)";
      var stats = box.querySelector("div[style*='grid-template-columns:repeat(4,1fr)']");
      if (stats && stats.parentNode) stats.parentNode.insertBefore(note, stats);
      else box.appendChild(note);
    } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_tapeRender0 = renderTape;
  renderTape = function () {
    var r = fe76_tapeRender0.apply(this, arguments);
    fe76_blankXau();
    return r;
  };
} catch (e) {}
function fe76_stamp(v) {
  if (v == null || v === "") return 0;
  var n = fe76_ms(v);
  if (n > 0) return n;
  if (typeof v === "string") {
    var p = Date.parse(v);
    if (p > 0) return p;
    var m = v.match(/(\d{1,2}):(\d{2}):(\d{2})/);
    if (m) {
      try {
        var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
        var y = "1970", mo = "01", d = "01";
        parts.forEach(function (x) { if (x.type === "year") y = x.value; if (x.type === "month") mo = x.value; if (x.type === "day") d = x.value; });
        var utc = Date.now();
        var london = new Date(new Date(utc).toLocaleString("en-US", { timeZone: "Europe/London" })).getTime();
        var off = london - utc;
        var hh = m[1].length === 1 ? "0" + m[1] : m[1];
        return Date.parse(y + "-" + mo + "-" + d + "T" + hh + ":" + m[2] + ":" + m[3] + "Z") - off;
      } catch (e) { return 0; }
    }
  }
  return 0;
}
function fe76_hms(ms) {
  if (!(ms > 0)) return "";
  try {
    return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23", timeZone: "Europe/London" }).replace(/[^\d:]/g, "");
  } catch (e) { return ""; }
}
function fe76_moneyLine(sym, px) {
  var s = "";
  try { if (typeof fe66_money === "function") s = fe66_money(sym, px); } catch (e) {}
  if (!s || s === "\u2014") {
    try { s = fe76_plain(sym, px); } catch (e2) { s = ""; }
    if (s && !fe76_isFx(sym) && s.charAt(0) !== "$") s = "$" + s;
  }
  return s;
}
function fe76_esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function fe76_quoteOf(meta) {
  var q = meta && typeof meta === "object" ? meta.quote : null;
  if (!q || typeof q !== "object" || Array.isArray(q)) return null;
  var price = q.price != null ? q.price : (q.px != null ? q.px : q.last);
  var n = typeof price === "number" ? price : Number(String(price == null ? "" : price).replace(/[^0-9.\-]/g, ""));
  if (!isFinite(n)) return null;
  return q;
}
function fe76_quoteKind(q) {
  var blob = [q.symbol, q.feedSymbol, q.name, q.source, q.feed].join(" ");
  if (/GC=F|futures|yahoo v8 chart|COMEX/i.test(blob) && !/gold-api/i.test(blob)) return "fut";
  return "spot";
}
function fe76_quoteAsOf(q) {
  if (q.asOfUk) return String(q.asOfUk);
  var ms = fe76_stamp(q.asOf != null ? q.asOf : q.ts);
  var h = fe76_hms(ms);
  return h ? (h + " UK") : "";
}
function fe76_quoteChg(q, px) {
  var prev = Number(q.prevClose != null ? q.prevClose : (q.prev != null ? q.prev : NaN));
  if (!fe76_ownPrev(px, prev)) return "";
  var abs = px - prev;
  var pct = (abs / prev) * 100;
  var sign = abs > 0 ? "+" : "";
  return " " + sign + fe76_group(abs, 2) + " (" + sign + pct.toFixed(2) + "%)";
}
function fe76_quoteBlock(meta) {
  var q = fe76_quoteOf(meta);
  if (!q) return "";
  var price = q.price != null ? q.price : (q.px != null ? q.px : q.last);
  var n = typeof price === "number" ? price : Number(String(price).replace(/[^0-9.\-]/g, ""));
  var fut = fe76_quoteKind(q) === "fut";
  var label = fut ? "Gold futures (GC=F, delayed 10 min)" : "Gold spot";
  var px = fe76_moneyLine("XAU", n);
  var asOf = fe76_quoteAsOf(q);
  var line = label + " " + px + fe76_quoteChg(q, n) + (asOf ? " \u00b7 " + asOf : "");
  return '<div class="fe76-qlines"><div class="fe76-qline">' + fe76_esc(line) + "</div></div>";
}
function fe76_swapBot(top) {
  var el = null;
  try { el = document.getElementById("chatMsgs"); } catch (e0) { el = null; }
  if (!el) return;
  var idx = _chatMsgs.length - 1;
  var m = _chatMsgs[idx];
  if (!m || m.role !== "assistant") return;
  var html = "";
  try { html = _renderBotMsg(m, idx); } catch (e1) { return; }
  var hold = document.createElement("template");
  hold.innerHTML = String(html || "").trim();
  var next = hold.content.firstElementChild;
  if (!next) return;
  var nodes = el.children;
  var node = null;
  var i;
  for (i = nodes.length - 1; i >= 0; i--) {
    if (nodes[i].classList && nodes[i].classList.contains("chat-msg") && nodes[i].classList.contains("bot") && !nodes[i].classList.contains("chat-thinking")) {
      node = nodes[i];
      break;
    }
  }
  if (node) node.replaceWith(next);
  else el.appendChild(next);
  var think = el.querySelector(".chat-thinking");
  if (think) think.remove();
  if (typeof top === "number") el.scrollTop = top;
  fe76_skipRender = 1;
}
try {
  var fe76_botPrev = _renderBotMsg;
  _renderBotMsg = function (m) {
    var html = fe76_botPrev.apply(this, arguments);
    try {
      var extra = m && m.meta ? fe76_quoteBlock(m.meta) : "";
      if (extra) html = String(html).replace(/<\/div>\s*$/, extra + "</div>");
    } catch (e) {}
    return html;
  };
} catch (e) {}
try {
  var fe76_rcSkip = _renderChatMsgs;
  _renderChatMsgs = function () {
    if (fe76_skipRender) { fe76_skipRender = 0; return; }
    return fe76_rcSkip.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_paintPrev = _rtPaint;
  _rtPaint = function () {
    var r = fe76_paintPrev.apply(this, arguments);
    try { fe76_blankXau(); } catch (e) {}
    return r;
  };
} catch (e) {}
var fe76_edition = null;
var fe76_lastSearch = null;
function fe76_noteEdition(j) {
  if (!j || typeof j !== "object") return;
  var ed = j.edition && j.edition.lead ? j.edition : (j.lead ? j : null);
  if (!ed || !ed.lead || !ed.lead.headline) return;
  fe76_edition = ed;
  try { fe76_applyEdition(); } catch (e) {}
}
function fe76_applyEdition() {
  var ed = fe76_edition;
  if (!ed || !ed.lead || !ed.lead.headline || typeof _brief === "undefined" || !_brief) return;
  var head = String(ed.lead.headline);
  var sum = String(_brief.summary || "");
  if (/Headline focus:/.test(sum)) sum = sum.replace(/Headline focus:\s*[^.]+\./, "Headline focus: " + head + ".");
  else sum = ("Headline focus: " + head + ". " + sum).trim();
  _brief.summary = sum;
  _brief.fe76Focus = head;
  if (ed.updatedAtUk) _brief.fe76Updated = String(ed.updatedAtUk);
  try { if (typeof _refreshBriefSurfaces === "function") _refreshBriefSurfaces(); } catch (e) {}
}
try {
  var fe76_briefPrev = _buildLocalBrief;
  _buildLocalBrief = function () {
    var b = fe76_briefPrev.apply(this, arguments);
    var ed = fe76_edition;
    if (b && ed && ed.lead && ed.lead.headline) {
      var head = String(ed.lead.headline);
      var sum = String(b.summary || "");
      if (/Headline focus:/.test(sum)) sum = sum.replace(/Headline focus:\s*[^.]+\./, "Headline focus: " + head + ".");
      else sum = ("Headline focus: " + head + ". " + sum).trim();
      b.summary = sum;
      b.fe76Focus = head;
      if (ed.updatedAtUk) b.fe76Updated = String(ed.updatedAtUk);
    }
    return b;
  };
} catch (e) {}
try {
  var fe76_bwhenPrev = _rt16BriefWhen;
  _rt16BriefWhen = function (b) {
    if (b && b.fe76Updated) return b.fe76Updated;
    return fe76_bwhenPrev.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_writtenPrev = fe70_written;
  fe70_written = function (b) {
    if (b && b.fe76Updated) return b.fe76Updated;
    return fe76_writtenPrev.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe76_whenPrev = fe73_rowWhen;
  fe73_rowWhen = function (row) {
    row = row || {};
    if (row.whenUk) return String(row.whenUk);
    if (row.transactionDateMissing) {
      var fl = "";
      try { fl = fe73_showDate(row.filingDateUk, row.filingDate) || ""; } catch (e) { fl = ""; }
      return fl ? ("Trade date not reported \u00b7 filed " + fl) : "Trade date not reported";
    }
    return fe76_whenPrev.apply(this, arguments);
  };
} catch (e) {}
function fe76_rateKey(k) {
  k = String(k || "");
  return /^(ra|rating)$/i.test(k) || /recommend/i.test(k) || /price.?target|target.?mean|target.?low|target.?high/i.test(k);
}
function fe76_dropRate(obj, depth) {
  if (!obj || typeof obj !== "object" || (depth || 0) > 4) return;
  Object.keys(obj).forEach(function (k) {
    if (fe76_rateKey(k)) delete obj[k];
    else if (obj[k] && typeof obj[k] === "object") fe76_dropRate(obj[k], (depth || 0) + 1);
  });
}
try { A.forEach(function (a) { fe76_dropRate(a); }); } catch (e) {}
try {
  var fe76_finPrev = renderFinancials;
  renderFinancials = function (tk, data) {
    try { fe76_dropRate(data); } catch (e) {}
    return fe76_finPrev.apply(this, arguments);
  };
} catch (e) {}
function fe76_profileFrom(searchJson, sym) {
  if (!searchJson || typeof searchJson !== "object") return null;
  var rows = Array.isArray(searchJson.result) ? searchJson.result : [];
  var i, row;
  for (i = 0; i < rows.length; i++) {
    row = rows[i];
    if (!row) continue;
    if (row.profile && (row.symbol === sym || (row.profile.symbol === sym))) return row.profile;
  }
  if (searchJson.profile && typeof searchJson.profile === "object") {
    if (!sym || !searchJson.profile.symbol || searchJson.profile.symbol === sym) return searchJson.profile;
  }
  return null;
}
function fe76_useProfile(sym, prof) {
  if (!prof || typeof prof !== "object") return;
  var mc = prof.marketCapText ? String(prof.marketCapText) : "";
  if (typeof _dynData !== "undefined" && _dynData && (_dynTk === sym || _dynData.ticker === sym)) {
    _dynData.mc = mc || "\u2014";
    if (prof.name) _dynData.name = prof.name;
    if (prof.exchange || prof.exchangeName) _dynData.exchange = prof.exchange || prof.exchangeName;
    try { if (typeof renderP2 === "function" && typeof IS_DESKTOP === "function" && IS_DESKTOP()) renderP2(); else if (typeof renderMain === "function") renderMain(); } catch (e) {}
  }
  var asset = prof.asset;
  if (!asset || typeof asset !== "object" || !asset.tk) return;
  var row = null;
  try { row = A.find(function (a) { return a && a.tk === asset.tk; }); } catch (e2) { row = null; }
  if (!row) { row = { tk: asset.tk, cat: "Stock" }; try { A.push(row); } catch (e3) {} }
  var k;
  for (k in asset) {
    if (!Object.prototype.hasOwnProperty.call(asset, k)) continue;
    if (fe76_rateKey(k)) continue;
    row[k] = asset[k];
  }
  fe76_dropRate(row);
  if (mc) { row.mc = mc; row._fe76Cap = mc; }
  if (!row.cat) row.cat = "Stock";
  if (!row.th) row.th = (prof.name || asset.tk) + " on " + (prof.exchange || "the home exchange") + ".";
  try { _dynTk = null; _dynData = null; _dynLoading = false; } catch (e4) {}
  try {
    if (typeof IS_DESKTOP === "function" && IS_DESKTOP() && typeof termSelect === "function") termSelect(asset.tk);
    else if (typeof openA === "function") openA(asset.tk);
  } catch (e5) {}
}
try {
  var fe76_keepYqPrev = fe64_keepYq;
  fe64_keepYq = function (tk, q) {
    var r = fe76_keepYqPrev.apply(this, arguments);
    try { fe76_keepFeed(tk, q); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe76_lookPrev = lookupTicker;
  lookupTicker = async function (tk) {
    var sym = String(tk || "").trim().toUpperCase();
    var out = fe76_lookPrev.apply(this, arguments);
    var searchP = fe76_lastSearch && fe76_lastSearch.sym === sym ? fe76_lastSearch.p : null;
    try { await out; } catch (e) {}
    var prof = null;
    try { if (searchP) prof = fe76_profileFrom(await searchP, sym); } catch (e2) {}
    if (!prof || !prof.marketCapText) {
      try {
        var res = await fetch("/api/listing-profile?symbol=" + encodeURIComponent(sym), { signal: AbortSignal.timeout(8000) });
        if (res && res.ok) {
          var got = await res.json();
          if (got && (got.marketCapText || got.asset || got.name)) prof = got;
        }
      } catch (e3) {}
    }
    if (prof) fe76_useProfile(sym, prof);
    return out;
  };
} catch (e) {}
try {
  var fe76_rt33 = _rt33Apply;
  _rt33Apply = function (tk) {
    var cap = "";
    try {
      var a0 = A.find(function (a) { return a && a.tk === tk; });
      cap = a0 && a0._fe76Cap || "";
    } catch (e0) {}
    var r = fe76_rt33.apply(this, arguments);
    if (cap) {
      try {
        var a1 = A.find(function (a) { return a && a.tk === tk; });
        if (a1 && (!a1.mc || a1.mc === "\u2014" || a1.mc === "-")) a1.mc = cap;
      } catch (e1) {}
    }
    return r;
  };
} catch (e) {}
try { setTimeout(function () { try { fetch("/api/brief/edition", { signal: AbortSignal.timeout(8000) }).catch(function () {}); } catch (e) {} }, 600); } catch (e) {}
'''


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


def times(text, old, new, label, n):
    c = text.count(old)
    if c != n:
        die("%s count %s" % (label, c))
    return text.replace(old, new)


def strip_ratings(app):
    """Remove broker-rating fields and every reader. Anchors, not line numbers."""
    pat = re.compile(r", ?ra: ?\"[^\"]*\"")
    found = pat.findall(app)
    if len(found) < 190:
        die("ra fields %s" % len(found))
    app = pat.sub("", app)
    if re.search(r"\bra\s*:", app):
        die("ra field remains")
    app = once(
        app,
        "AI score: ${a.sc}/100 | Sentiment: ${a.se} | Rating: ${a.ra || \"—\"}",
        "AI score: ${a.sc}/100 | Sentiment: ${a.se}",
        "lens rating line",
    )
    app = once(
        app,
        "    const rec = fin.recommendations?.[0];\n"
        "    if (rec) finBlock += ` | Analyst: ${rec.strongBuy + rec.buy} buy / ${rec.hold} hold / ${rec.sell + rec.strongSell} sell`;\n"
        "    if (fin.priceTarget?.targetMean) finBlock += ` | PT mean $${fin.priceTarget.targetMean}`;\n",
        "",
        "lens analyst payload",
    )
    app = once(
        app,
        '  const metrics = ["sc", "se", "ra", "pe", "beta", "mc", "cat"];\n',
        '  const metrics = ["sc", "se", "pe", "beta", "mc", "cat"];\n',
        "compare metrics",
    )
    app = once(
        app,
        '  const bearish = w.filter(a => String(a.se || "").includes("Bear") || a.ra === "Avoid").length;\n',
        '  const bearish = w.filter(a => String(a.se || "").includes("Bear") || (Number(liveChg(a.tk)) < 0)).length;\n',
        "watchlist bearish",
    )
    app = once(
        app,
        '    if (r.se.includes("Bear") || r.a?.ra === "Avoid") bearishW += w;\n',
        '    if (r.se.includes("Bear") || (Number(liveChg(r.pos.tk)) < 0)) bearishW += w;\n',
        "portfolio bearish",
    )
    app = once(
        app,
        '        <div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Rating: <span style="color:var(--tx)">${a.ra}</span></div>\n',
        "",
        "profile rating row",
    )
    app = once(
        app,
        '${bd(a.ra,a.ra.includes("Buy")?"var(--gn)":"var(--bl)")}',
        "",
        "phone rating badge",
    )
    app = once(
        app,
        " · ${a.ra || \"—\"} · ",
        " · ",
        "ask active ticker",
    )
    app = once(
        app,
        "  const pt = data.priceTarget || {};\n"
        "  const ins = data.insiders || [];\n"
        "  const peers = data.peers || [];\n"
        "  const recs = data.recommendations || [];\n"
        "  const upgrades = data.upgrades || [];\n",
        "  const ins = data.insiders || [];\n"
        "  const peers = data.peers || [];\n",
        "financials rating locals",
    )
    start = app.find("  // ── WALL STREET CONSENSUS GAUGE ──\n")
    end = app.find("  // ── INSIDER TRANSACTIONS ──\n")
    if start < 0 or end < 0 or end <= start:
        die("financials panel anchors")
    if app.find("  // ── WALL STREET CONSENSUS GAUGE ──\n", start + 1) >= 0:
        die("financials panel not unique")
    app = app[:start] + app[end:]
    app = once(
        app,
        "- **AI Score (0 to 100)** on each instrument combines sentiment, momentum, fundamentals and analyst ratings. It is indicative only.\n",
        "- **AI Score (0 to 100)** on each instrument combines sentiment, momentum and fundamentals. It is indicative only.\n",
        "learn score copy",
    )
    app = once(
        app,
        "combining sentiment, momentum, fundamentals and analyst ratings. Indicative only, not a recommendation.",
        "combining sentiment, momentum and fundamentals. Indicative only, not a forecast.",
        "glossary score copy",
    )
    app = once(
        app,
        " ['analyst-rating','Analyst rating','The Dispatch','The consensus view of brokers\\' analysts, such as Buy, Hold or Sell. Ratings often lag the price and are only one input among many.','start-dispatch'],\n",
        "",
        "glossary analyst entry",
    )
    app = once(
        app,
        "[/^Rating\\b/, 'analyst-rating'], ",
        "",
        "rating tooltip",
    )
    app = once(
        app,
        "Lens Engine fuses latest quote · momentum · financials · earnings · analyst data",
        "Lens Engine fuses latest quote · momentum · financials · earnings",
        "lens analyst data",
    )
    app = once(
        app,
        "Lens Engine fuses the latest Yahoo quote, 52-week momentum, Finnhub financials, earnings, analyst targets, your terminal feed, and web search into five framework analyses.",
        "Lens Engine fuses the latest Yahoo quote, 52-week momentum, Finnhub financials, earnings, your terminal feed, and web search into five framework analyses.",
        "lens analyst targets",
    )
    if re.search(r"\.ra\b", app):
        die("ra reader remains")
    if "Strong Buy" in app or "ANALYST PRICE TARGETS" in app or "Rating:" in app:
        die("rating phrase remains")
    return app


def neutralise_verdicts(app):
    """Display-only. Scoring still reads BUY / SELL / AVOID."""
    pairs = [
        ("${wDir||dir}", "${fe76_vword(wDir||dir)}", "phone vote headline"),
        ("simple vote: ${dir}", "simple vote: ${fe76_vword(dir)}", "phone simple vote"),
        ("${buyCount} Buy", '${buyCount} ${fe76_vword("Buy")}', "phone buy count"),
        ("${avoidCount} Avoid", '${avoidCount} ${fe76_vword("Avoid")}', "phone avoid count"),
        (">Buy ${buyPct}%", '>${fe76_vword("Buy")} ${buyPct}%', "phone buy pct"),
        (">Avoid ${avoidPct}%", '>${fe76_vword("Avoid")} ${avoidPct}%', "phone avoid pct"),
        ('${c.verdict||"—"}', '${fe76_vword(c.verdict)||"—"}', "phone member verdict"),
        ('${synth.verdict||"MONITOR"}', '${fe76_vword(synth.verdict)||"MONITOR"}', "phone synth verdict"),
        (">${w.dir}</div>", ">${fe76_vword(w.dir)}</div>", "desk vote dir"),
        (">${synth.verdict}</div>", ">${fe76_vword(synth.verdict)}</div>", "desk synth verdict"),
        (">${c.verdict}</span>", ">${fe76_vword(c.verdict)}</span>", "desk member verdict"),
        ('${intel.verdict || "MONITOR"}', '${fe76_vword(intel.verdict) || "MONITOR"}', "intel verdict"),
        ("Lens verdict: ${synth.verdict} (", "Lens verdict: ${fe76_vword(synth.verdict)} (", "insight verdict"),
        ('<span class="cr-v">${h.verdict || "—"}</span>', '<span class="cr-v">${fe76_vword(h.verdict) || "—"}</span>', "continue chip"),
        ('${(st.verdict || "MONITOR").replace(/</g, "&lt;")}', '${fe76_vword(st.verdict || "MONITOR").replace(/</g, "&lt;")}', "chat verdict"),
        ("<strong>Avoid tilt:</strong>", "<strong>Lower weight:</strong>", "regime tilt"),
        (">Avoid ${_rt52E(x)}</span>", ">Lower weight ${_rt52E(x)}</span>", "regime pill"),
        ("*BUY signals: Strong fundamentals with clear moat at reasonable valuation*", "*Positive signals: Strong fundamentals with clear moat at reasonable valuation*", "guide buy value"),
        ("*AVOID signals: Price too high for intrinsic value, or business quality unclear*", "*Weak signals: Price too high for intrinsic value, or business quality unclear*", "guide avoid value"),
        ("*AVOID is the most powerful signal — permanent impairment risks outweigh upside*", "*Weak is the most powerful signal — permanent impairment risks outweigh upside*", "guide avoid quality"),
        ("*BUY signals: Clear catalyst identified, sum-of-parts undervaluation, actionable timeline*", "*Positive signals: Clear catalyst identified, sum-of-parts undervaluation, actionable timeline*", "guide buy catalyst"),
    ]
    for old, new, label in pairs:
        app = once(app, old, new, label)
    app = times(app, '${r.verdict || "MONITOR"}', '${fe76_vword(r.verdict) || "MONITOR"}', "journal verdict", 2)
    app = times(app, "bd(r.verdict,", "bd(fe76_vword(r.verdict),", "history badge", 2)
    return app


def fix_lists(app):
    """Watchlist cells prefixed $ for every row, including FX."""
    return once(
        app,
        "<td data-fl=\"${a.tk}\">${na?'<span style=\"color:var(--t3);opacity:0.55\">—</span>':'$'+d.p}</td>",
        "<td data-fl=\"${a.tk}\">${na?'<span style=\"color:var(--t3);opacity:0.55\">—</span>':((a.cat==='Stock'||a.cat==='Crypto'||a.cat==='Commodity')?'$':'')+d.p}</td>",
        "watchlist fx dollar",
    )


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


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


def patch_stream(app):
    old = (
        "    if (_chatMsgs.length && _chatMsgs[_chatMsgs.length - 1]._bb2) _chatMsgs.pop();\n"
        "    _chatMsgs.push({\n"
        "      role: \"assistant\",\n"
        "      content: _rt37Reply(reply, tickers),\n"
        "      structured: _rt38St(final && final.structured, tickers),\n"
        "      meta: (final && final.meta) || null\n"
        "    });\n"
        "    _persistChat();"
    )
    new = (
        "    var fe76Reply = _rt37Reply(reply, tickers);\n"
        "    var fe76Meta = (final && final.meta) || null;\n"
        "    var fe76St = _rt38St(final && final.structured, tickers);\n"
        "    var fe76Box = document.getElementById(\"chatMsgs\");\n"
        "    var fe76Top = fe76Box ? fe76Box.scrollTop : 0;\n"
        "    var fe76Last = _chatMsgs.length ? _chatMsgs[_chatMsgs.length - 1] : null;\n"
        "    if (fe76Last && fe76Last._bb2) {\n"
        "      fe76Last.content = fe76Reply;\n"
        "      fe76Last.structured = fe76St;\n"
        "      fe76Last.meta = fe76Meta;\n"
        "      delete fe76Last._bb2;\n"
        "    } else {\n"
        "      _chatMsgs.push({ role: \"assistant\", content: fe76Reply, structured: fe76St, meta: fe76Meta });\n"
        "    }\n"
        "    try { if (typeof fe76_swapBot === \"function\") fe76_swapBot(fe76Top); } catch (e76) {}\n"
        "    _persistChat();"
    )
    return once(app, old, new, "stream final swap")


def main():
    app_path, index_path = paths()
    if not app_path.is_file() or not index_path.is_file():
        die("missing app.js or index.html")
    app_raw, app, app_crlf = read_text(app_path)
    index_raw, index, index_crlf = read_text(index_path)
    app_sum = md5(app_raw)
    index_sum = md5(index_raw)
    if app_sum != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (app_sum, EXPECT_APP_MD5))
    if index_sum != EXPECT_INDEX_MD5:
        print("WARN index.html md5 %s expected %s" % (index_sum, EXPECT_INDEX_MD5))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    anchors = [
        "function fe66_money(",
        "function fe73_absText(",
        "function fe73_chgLine(",
        "function fe73_px(",
        "function fp(",
        "function fe68_badge(",
        "function fe70_finish(",
        "function fe65_feedLbl(",
        "function _rt23ChartLbl(",
        "function _rt23ChartFetch(",
        "function fe66_dynHead(",
        "function fe66_chartBit(",
        "function fe69_insRow(",
        "function fe69_insHtml(",
        "function fe71_openMoreNav(",
        "function _rt24ChartHead(",
    ]
    for a in anchors:
        n = app.count(a)
        if n != 1:
            die("anchor %s count %s" % (a, n))
    if index.count('app.js?v=chat75"') != 1:
        die("cache bust anchor missing")
    app = strip_ratings(app)
    app = neutralise_verdicts(app)
    app = fix_lists(app)
    app = patch_stream(app)
    app = app + BLOCK
    if "fe76_cardLock" in app or "gap >= 60000" in app:
        die("old gold gap logic remains")
    if app.count("function fe76_quote(") != 1:
        die("fe76_quote count")
    if app.count("function fe76_closeLens(") != 1:
        die("fe76_closeLens count")
    if app.count("function fe76_vword(") != 1:
        die("fe76_vword count")
    index = index.replace('app.js?v=chat75"', 'app.js?v=chat76"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
