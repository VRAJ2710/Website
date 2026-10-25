#!/usr/bin/env python3
"""rt62h client patch: chat84 -> chat85. Anchors decide; md5 only warns.

Applies on the chat84 output (PR #81). Keeps the fe84 guards and memos.

Gold futures rows drop raw source paths and the spot label, and show the
futures point change. Repeated status words collapse. The regime line uses
the quote bag's last close. Signals keep the existing mode machine: a row
stays a skeleton while its feed is still loading, shows a last close when
the server sent one, and says UNAVAILABLE only after the load finishes
empty, with a plain reason. Body scrub timers no longer scan document.body
on the fast intervals.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "293c103a4efdd0fddaffc114bc3870ee"
EXPECT_INDEX_PREFIX = "76207426"
NEED_MARKER = "// ── rt62g ──"
REFUSE_MARKER = "// ── rt62h ──"

BLOCK = r"""
// ── rt62h ──
// fe85: source paths never reach a label, repeated status words collapse,
// gold futures keep the futures name and the point change, the regime line
// reads the last close, and a signal row waits out the existing load machine.
// fe85-pure-begin
function fe85_num(v) {
  var n = Number(v);
  return typeof v === "boolean" || !isFinite(n) ? null : n;
}
function fe85_signed(v, suffix) {
  var n = fe85_num(v);
  if (n == null) return "";
  var sign = n > 0 ? "+" : (n < 0 ? "-" : "");
  return sign + Math.abs(n).toFixed(2) + (suffix || "");
}
function fe85_clean(s) {
  var t = String(s == null ? "" : s);
  if (!t) return t;
  var path = /api\.|\/price\/|\(api|gold-api|https?:/i.test(t);
  var dup = /\b(CLOSED|LIVE|STALE|DELAYED|CACHED|UNAVAILABLE)\b(\s*[·|•]\s*)\1\b/i.test(t);
  if (!path && !dup) return t;
  t = t.replace(/https?:\/\/\S+/gi, "");
  t = t.replace(/\bgold-api\.com\b/gi, "");
  t = t.replace(/\(\s*api[^)]{0,120}\)/gi, "");
  t = t.replace(/api\.[\/.][^\s)·]*/gi, "");
  t = t.replace(/\/price\/[A-Za-z0-9._-]*/gi, "");
  var i = 0, prev;
  do {
    prev = t;
    t = t.replace(/\b(CLOSED|LIVE|STALE|DELAYED|CACHED|UNAVAILABLE)\b(\s*[·|•]\s*)\1\b/gi, "$1");
    if (++i > 4) break;
  } while (t !== prev);
  t = t.replace(/\s*[·|]\s*[·|]\s*/g, " · ");
  t = t.replace(/\(\s*\)/g, "");
  t = t.replace(/\s{2,}/g, " ");
  t = t.replace(/(^[\s·|]+)|([\s·|]+$)/g, "");
  return t;
}
function fe85_ptsFrom(g, dc, fut) {
  var list = [g, dc, fut];
  function push(o, k) { try { if (o && o[k] && typeof o[k] === "object") list.push(o[k]); } catch (e) {} }
  push(g, "displayChange");
  push(g, "futuresChange");
  push(dc, "displayChange");
  push(dc, "futuresChange");
  push(fut, "displayChange");
  push(fut, "futuresChange");
  var keys = ["points", "pointChange", "changePoints", "point", "pts"];
  var i, j, n;
  for (i = 0; i < list.length; i++) {
    var o = list[i];
    if (!o || typeof o !== "object") continue;
    for (j = 0; j < keys.length; j++) {
      n = fe85_num(o[keys[j]]);
      if (n != null && Number(n.toFixed(2)) !== 0) return n;
    }
  }
  for (i = 0; i < list.length; i++) {
    var o2 = list[i];
    if (!o2 || typeof o2 !== "object") continue;
    n = fe85_num(o2.change != null ? o2.change : o2.absChange);
    var pct = fe85_num(o2.changePct != null ? o2.changePct : (o2.pct != null ? o2.pct : o2.c));
    if (n != null && (pct == null || Math.abs(n - pct) > 0.05) && Math.abs(n) >= 5) return n;
    var px = fe85_num(o2.price != null ? o2.price : o2.p);
    var prev = fe85_num(o2.prevClose != null ? o2.prevClose : (o2.prev != null ? o2.prev : o2.previousClose));
    if (px != null && prev != null && px > 0 && prev > 0) {
      var dlt = px - prev;
      if (Number(dlt.toFixed(2)) !== 0) return dlt;
    }
  }
  return null;
}
function fe85_goldLine(pct, pts, day) {
  var parts = [];
  if (pts) parts.push(String(pts));
  if (pct) parts.push(String(pct));
  var line = parts.join(" · ");
  if (day) line = (line ? line + " " : "") + day;
  return line;
}
function fe85_regimeText(name, px, pct, day, closed, opens) {
  if (!px) return "";
  var bit = String(name || "") + " " + px;
  if (pct) bit += " · " + pct;
  if (day) bit += " " + day;
  if (closed) bit += " · closed" + (opens ? ", " + opens : "");
  return bit;
}
function fe85_paren(pts, pct, day) {
  var line = "";
  if (pts && pct) line = String(pts) + " (" + String(pct) + ")";
  else if (pct) line = String(pct);
  else if (pts) line = String(pts);
  if (day) line = (line ? line + " " : "") + day;
  return line;
}
function fe85_clockText(ms) {
  var d = new Date(ms);
  if (!isFinite(d.getTime())) return "";
  var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short" }).formatToParts(d);
  var wd = "", day = "", mon = "";
  for (var i = 0; i < parts.length; i++) {
    if (parts[i].type === "weekday") wd = parts[i].value;
    else if (parts[i].type === "day") day = parts[i].value;
    else if (parts[i].type === "month") mon = parts[i].value;
  }
  var hm = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(d);
  if (!wd || !day || !mon || !hm) return "";
  return wd + " " + day + " " + mon + " · " + hm + " UK";
}
// fe85-pure-end
var fe85_boot = Date.now();
var fe85_walkAt = 0;
var fe85_domAt = 0;
var fe85_passing = false;
var fe85_waitKey = "";
function fe85_id(tk) {
  try { if (typeof resolveInternalTicker === "function") return resolveInternalTicker(tk) || tk; } catch (e) {}
  return tk;
}
function fe85_live(tk) {
  var id = fe85_id(tk);
  try { return !!(typeof liveSymbols !== "undefined" && (liveSymbols.has(id) || liveSymbols.has(tk))); } catch (e) { return false; }
}
function fe85_fetchOpen() {
  var slots = (typeof fe82_quoteWait !== "undefined" && fe82_quoteWait) ? fe82_quoteWait : [];
  for (var i = 0; i < slots.length; i++) {
    if (!slots[i] || !slots[i].done || slots[i].pendingBody) return true;
  }
  try { if (typeof priceFetching !== "undefined" && priceFetching) return true; } catch (e) {}
  return false;
}
function fe85_waiting(tk) {
  if (fe85_live(tk)) return false;
  if (Date.now() - fe85_boot >= 20000) return false;
  return true;
}
function fe85_cleanHtml(html) {
  var s = String(html || "");
  if (!/api\.|\/price\/|\(api|gold-api|CLOSED\s*[·|]\s*CLOSED|STALE\s*[·|]\s*STALE|LIVE\s*[·|]\s*LIVE/i.test(s)) return s;
  s = s.replace(/>([^<]*)</g, function (_m, t) { return ">" + fe85_clean(t) + "<"; });
  s = s.replace(/\b(title|aria-label)="([^"]*)"/g, function (_m, k, t) { return k + '="' + fe85_clean(t) + '"'; });
  return s;
}
function fe85_goldDay() {
  var day = "";
  try { day = fe83f_pickDay("XAU") || ""; } catch (e) { day = ""; }
  var closed = false;
  try { closed = fe83f_marketClosed("XAU"); } catch (e2) { closed = false; }
  if (closed && (day === "Sat" || day === "Sun" || !day)) {
    var today = "";
    try { today = fe83f_todayWd(); } catch (e3) { today = ""; }
    if (!day || day === "Sat" || day === "Sun" || today === "Sat" || today === "Sun") day = "Fri";
  }
  return day === "Sat" || day === "Sun" ? (closed ? "Fri" : day) : day;
}
function fe85_goldChg(b) {
  if (!b || b.kind !== "futures") return "";
  var pct = b.pct == null ? "" : fe85_signed(b.pct, "%");
  var line = fe85_goldLine(pct, b.pts || "", fe85_goldDay());
  try { if (typeof fe83f_fixSigns === "function") line = fe83f_fixSigns(line); } catch (e) {}
  if (fe85_goldDay() === "Fri") line = line.replace(/\b(Sat|Sun)\b/g, "Fri");
  return line;
}
function fe85_asofBits() {
  var ts = 0;
  try {
    var d = typeof fp === "function" ? fp("XAU") : null;
    ts = d && d.asOf ? Number(d.asOf) : 0;
  } catch (e) { ts = 0; }
  if (!(ts > 0)) { try { ts = (typeof liveQuoteTs !== "undefined" && Number(liveQuoteTs.XAU)) || 0; } catch (e2) { ts = 0; } }
  var hm = "";
  try { if (ts > 0 && typeof fe64_ukHm === "function") hm = fe64_ukHm(ts) || ""; } catch (e3) { hm = ""; }
  return hm ? ("Gold futures (GC=F) · as of " + hm + " UK") : "Gold futures (GC=F)";
}
var fe85_openMap = new Map();
function fe85_opens(tk) {
  var now = Date.now();
  var hit = fe85_openMap.get(tk);
  if (hit && now - hit.at < 1000) return hit.v;
  var ms = 0;
  try { if (typeof _rt51Next === "function") ms = _rt51Next(tk) || 0; } catch (e) { ms = 0; }
  var bag = null;
  try { bag = (typeof fe78_bag === "function" && fe78_bag(tk)) || (typeof fe64_yqBag === "function" && fe64_yqBag(tk)); } catch (e2) { bag = null; }
  if (!(ms > 0) && bag && bag.nextOpen) {
    ms = typeof bag.nextOpen === "number" ? bag.nextOpen : Date.parse(bag.nextOpen);
  }
  var out = "";
  if (ms > 0 && isFinite(ms)) {
    var wd = "", hm = "";
    try { wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date(ms)); } catch (e3) { wd = ""; }
    try { hm = typeof fe64_ukHm === "function" ? fe64_ukHm(ms) : ""; } catch (e4) { hm = ""; }
    if (hm) out = "opens " + (wd ? wd + " " : "") + hm + " UK";
  }
  if (!out) {
    try {
      var note = typeof fe65_closedNote === "function" ? fe65_closedNote(tk, bag) : "";
      if (note && /opens\s+\d/i.test(note)) out = String(note).replace(/\s+/g, " ").trim();
    } catch (e5) { out = ""; }
  }
  if (fe85_openMap.size > 40) fe85_openMap.clear();
  fe85_openMap.set(tk, { at: now, v: out });
  return out;
}
var fe85_lineMap = new Map();
function fe85_sessionLine(tk, name) {
  var now = Date.now();
  var hit = fe85_lineMap.get(tk);
  if (hit && now - hit.at < 1000) return hit.v;
  var v = "";
  try {
    if (fe85_live(tk)) {
      var id = fe85_id(tk);
      var d = null;
      try { d = fp(tk); } catch (e) { d = null; }
      var px = d && d.p && d.p !== "—" && d.p !== "–" ? String(d.p) : "";
      if (!px) {
        try {
          var n = P[id] && P[id].p;
          if (typeof n === "number" && n > 0) px = (typeof fe83f_px === "function" && fe83f_px(n)) || n.toFixed(2);
        } catch (e2) { px = ""; }
      }
      if (px) {
        var pctN = null;
        try { pctN = liveChg(tk); } catch (e3) { pctN = null; }
        if (pctN == null) { try { if (P[id] && isFinite(Number(P[id].c))) pctN = Number(P[id].c); } catch (e4) {} }
        var day = "";
        try { day = fe83f_pickDay(tk) || ""; } catch (e5) { day = ""; }
        var closed = false;
        try { closed = fe83f_marketClosed(tk); } catch (e6) { closed = false; }
        v = fe85_regimeText(name, px, pctN == null ? "" : fe85_signed(pctN, "%"), day, closed, closed ? fe85_opens(tk) : "");
      }
    }
  } catch (e7) { v = ""; }
  if (fe85_lineMap.size > 40) fe85_lineMap.clear();
  fe85_lineMap.set(tk, { at: now, v: v });
  return v;
}
function fe85_skel() {
  try { if (typeof fe78_skel === "function") return fe78_skel(); } catch (e) {}
  return '<span class="fe78-skel" style="display:inline-block;height:8px;width:42px;background:var(--b3);border-radius:4px"></span>';
}
function fe85_rowSkel() {
  return '<div class="gc gc-a rt52-sig fe85-row-wait" data-fe85="row-wait" style="padding:12px;margin-bottom:8px"><div style="height:12px;width:42%;background:var(--b3);border-radius:4px;margin-bottom:8px"></div><div style="height:10px;width:78%;background:var(--b3);border-radius:4px;margin-bottom:6px"></div><div style="height:10px;width:54%;background:var(--b3);border-radius:4px"></div></div>';
}
function fe85_plainReason() {
  return "No quote from the free feeds for this symbol this session";
}
function fe85_walk(root) {
  if (!root || typeof document === "undefined" || !document.createTreeWalker) return;
  var blob = "";
  try { blob = root.textContent || ""; } catch (e) { return; }
  if (/api\.|\/price\/|\(api|gold-api|CLOSED\s*[·|]\s*CLOSED|STALE\s*[·|]\s*STALE|LIVE\s*[·|]\s*LIVE|DELAYED\s*[·|]\s*DELAYED|CACHED\s*[·|]\s*CACHED|UNAVAILABLE\s*[·|]\s*UNAVAILABLE/i.test(blob)) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var n;
    while ((n = walker.nextNode())) {
      var p = n.parentNode;
      if (!p || /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(p.tagName || "")) continue;
      var v = n.nodeValue;
      if (!v) continue;
      var next = fe85_clean(v);
      if (next !== v) n.nodeValue = next;
    }
  }
  var nodes;
  try { nodes = root.querySelectorAll("[title],[aria-label]"); } catch (e2) { nodes = []; }
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var title = el.getAttribute("title");
    if (title) {
      var nt = fe85_clean(title);
      if (nt !== title) el.setAttribute("title", nt);
    }
    var al = el.getAttribute("aria-label");
    if (al) {
      var na = fe85_clean(al);
      if (na !== al) el.setAttribute("aria-label", na);
    }
  }
}
function fe85_paintTapeOnly() {
  if (typeof document === "undefined") return;
  var b = null;
  try { b = fe83f_goldBits(); } catch (e) { b = null; }
  if (!b || b.kind !== "futures") return;
  var label = fe85_asofBits();
  var chg = fe85_goldChg(b);
  var badgeTxt = label.indexOf("·") >= 0 ? ("\u00a0" + label.slice(label.indexOf("·"))) : "";
  var nodes = document.querySelectorAll("#tape .ti[data-tk='XAU'],#tape .ti[data-tk='GC=F']");
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var badge = el.querySelector(".tape-badge");
    if (badge && badgeTxt && badge.textContent !== badgeTxt) badge.textContent = badgeTxt;
    if (el.getAttribute("title") !== label) el.setAttribute("title", label);
    var kids = el.children || [];
    if (chg && kids.length >= 3 && kids[2].textContent !== chg) kids[2].textContent = chg;
    if (chg) {
      var fut = el.querySelector(".fe77-fut");
      if (fut && fut.textContent) fut.textContent = "";
    }
  }
}
function fe85_paintGoldDom() {
  fe85_paintTapeOnly();
  var b = null;
  try { b = fe83f_goldBits(); } catch (e) { b = null; }
  if (!b || b.kind !== "futures" || typeof document === "undefined") return;
  var label = fe85_asofBits();
  var chg = fe85_goldChg(b);
  document.querySelectorAll("[data-tk='XAU'] .trust-stat, [data-fl='XAU'] .trust-stat, [data-price-card='XAU'] .trust-stat").forEach(function (node) {
    var tx = node.textContent || "";
    if (!/spot/i.test(tx)) return;
    var next = tx.replace(/(\s*[·|•]\s*)spot\b/ig, "").replace(/\s{2,}/g, " ").trim();
    if (next && next !== tx) node.textContent = next;
  });
  document.querySelectorAll("[data-price-card='XAU']").forEach(function (el) {
    var ce = el.querySelector(".asset-chg,.change,.conv-chg,.idx-card-chg,.spine-chg");
    if (ce && chg && ce.textContent !== chg) ce.textContent = chg;
    var nm = el.querySelector(".conv-nm,.idx-card-name,.spine-lbl,.rt47-qn");
    if (nm && /spot|api\.|\/price\//i.test(nm.textContent || "")) nm.textContent = "Gold futures (GC=F)";
    el.querySelectorAll(".asof-tag,.trust-stat,[title]").forEach(function (node) {
      var tx = node.textContent || "";
      var title = node.getAttribute && node.getAttribute("title");
      if (/spot|api\.|\/price\/|\(api/i.test(tx) && node.classList && (node.classList.contains("asof-tag") || node.classList.contains("trust-stat"))) node.textContent = label;
      if (title && /spot|api\.|\/price\/|\(api/i.test(title)) node.setAttribute("title", label);
    });
  });
}
function fe85_holdCards() {
  if (typeof document === "undefined") return;
  document.querySelectorAll("[data-price-card]").forEach(function (el) {
    var tk = el.getAttribute("data-price-card") || "";
    if (!tk || !fe85_waiting(tk) || fe85_live(tk)) return;
    var px = el.querySelector(".asset-price,.idx-card-px,.conv-px,.ap-price");
    if (px && !px.querySelector(".fe78-skel")) px.innerHTML = fe85_skel();
    var st = el.querySelector(".trust-stat,.idx-card-stat,.asof-tag");
    if (st && /UNAVAILABLE|no quote|No source/i.test(st.textContent || "")) st.innerHTML = fe85_skel();
  });
}
function fe85_paintRegimeDom() {
  if (typeof document === "undefined") return;
  var line = "";
  try { line = fe83f_regimeLine({}); } catch (e) { line = ""; }
  if (!line) return;
  var text = String(line).replace(/<[^>]+>/g, "");
  var nodes = document.querySelectorAll(".fe83f-regime-in");
  if (!nodes.length) {
    var card = document.querySelector(".gc-regime");
    if (!card) return;
    var holder = document.createElement("div");
    holder.className = "fe83f-regime-in";
    holder.style.cssText = "font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5";
    holder.textContent = text;
    var score = card.querySelector("div");
    if (score && score.parentNode) score.parentNode.insertBefore(holder, score.nextSibling);
    else card.appendChild(holder);
    return;
  }
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].textContent !== text) nodes[i].textContent = text;
  }
}
function fe85_pass() {
  if (fe85_passing || typeof document === "undefined") return;
  fe85_passing = true;
  try {
    try { fe85_paintTapeOnly(); } catch (e) {}
    var domNow = Date.now();
    if (domNow - fe85_domAt >= 500) {
      fe85_domAt = domNow;
      try { fe85_paintGoldDom(); } catch (eD) {}
      try { fe85_paintRegimeDom(); } catch (eR) {}
      try { fe85_paintGlance(); } catch (eG) {}
      try { fe85_holdCards(); } catch (e2) {}
    }
    var now = Date.now();
    if (now - fe85_walkAt < 2000) return;
    fe85_walkAt = now;
    var sels = ["#main", "#tape", "#p2body", "#p3body", "#p4body"];
    for (var i = 0; i < sels.length; i++) {
      var el = null;
      try { el = document.querySelector(sels[i]); } catch (e3) { el = null; }
      if (el) fe85_walk(el);
    }
  } finally {
    fe85_passing = false;
  }
}
try {
  var fe85_sync0 = hasSyncedQuote;
  hasSyncedQuote = function (tk) {
    var ok = false;
    try { ok = !!fe85_sync0.apply(this, arguments); } catch (e) { ok = false; }
    if (ok) return true;
    var id = fe85_id(tk);
    try {
      return !!(typeof liveSymbols !== "undefined" && liveSymbols.has(id) && P[id] && typeof P[id].p === "number" && isFinite(P[id].p) && P[id].p > 0);
    } catch (e2) { return false; }
  };
} catch (eSync) {}
try {
  var fe85_from0 = fe83f_goldFrom;
  fe83f_goldFrom = function (g, dc, fut, spot) {
    var b = fe85_from0.apply(this, arguments);
    if (!b || b.kind !== "futures" || b.pts) return b;
    var n = fe85_ptsFrom(g, dc, fut);
    if (n == null) {
      try { n = fe85_ptsFrom(typeof fe77_xauRaw !== "undefined" ? fe77_xauRaw : null, typeof fe82_goldDc !== "undefined" ? fe82_goldDc : null, typeof fe77_futObj === "function" ? fe77_futObj() : null); } catch (e) { n = null; }
    }
    if (n != null) b.pts = fe85_signed(n, "");
    return b;
  };
} catch (eFrom) {}
try {
  var fe85_bits0 = fe83f_goldBits;
  var fe85_bitsAt = 0, fe85_bitsVal = null;
  fe83f_goldBits = function () {
    var now = Date.now();
    if (fe85_bitsVal && fe85_bitsVal.kind === "futures" && now - fe85_bitsAt < 200) return fe85_bitsVal;
    fe85_bitsAt = now;
    try { fe85_bitsVal = fe85_bits0.apply(this, arguments); } catch (e) { fe85_bitsVal = null; }
    return fe85_bitsVal;
  };
} catch (eBits) {}
try {
  var fe85_src0 = _quoteSourceLabel;
  var fe85_srcBusy = false;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe85_src0.apply(this, arguments) || ""; } catch (e) { out = String(src || ""); }
    out = fe85_clean(out);
    if (fe85_srcBusy) return out || "market feed";
    fe85_srcBusy = true;
    try {
      var blob = String(src || "") + " " + out;
      if (/gold-api|gold|GC=F|XAU|api\.|\/price\//i.test(blob)) {
        var b = null;
        try { b = fe83f_goldBits(); } catch (e2) { b = null; }
        if (b && b.kind === "futures") return "Gold futures (GC=F)";
        if (/gold/i.test(blob)) return "Gold spot";
      }
    } finally { fe85_srcBusy = false; }
    if (/api\.|\/price\/|\(api|gold-api|https?:/i.test(out)) return "market feed";
    return out || "market feed";
  };
} catch (eSrc) {}
try {
  var fe85_tw0 = fe65_tapeWords;
  fe65_tapeWords = function (d) {
    var w = "";
    try { w = fe85_tw0.apply(this, arguments) || ""; } catch (e) { w = ""; }
    w = fe85_clean(w);
    if (!d) return w;
    var blob = String(d.detail || "") + " " + String(d.fe64Note || "") + " " + String(d.src || "") + " " + String(d.label || "") + " " + String(d.lb || "");
    if (/silver|\bSLV\b|\bCOPPER\b/i.test(blob)) return w;
    if (!/GC=F|Spot gold|Gold futures|\bXAU\b/i.test(blob)) return w;
    var b = null;
    try { b = fe83f_goldBits(); } catch (e2) { b = null; }
    if (!(b && b.kind === "futures")) return w;
    var hm = "";
    try { if (d.asOf && typeof fe64_ukHm === "function") hm = fe64_ukHm(d.asOf) || ""; } catch (e3) { hm = ""; }
    return hm ? ("\u00a0· as of " + hm + " UK") : "\u00a0· Gold futures (GC=F)";
  };
} catch (eTw) {}
try {
  var fe85_feed0 = fe65_feedLbl;
  fe65_feedLbl = function (d, tk) {
    var out = "";
    try { out = fe85_feed0.apply(this, arguments) || ""; } catch (e) { out = ""; }
    return fe85_clean(out);
  };
} catch (eFeed) {}
try {
  var fe85_as0 = asOfTag;
  asOfTag = function (tk) {
    var id = fe85_id(tk);
    if ((id === "XAU" || id === "GC=F") && !fe85_waiting(id)) {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      if (b && b.kind === "futures") {
        var label = fe85_asofBits();
        return '<span class="asof-tag" title="' + (typeof _escAttr === "function" ? _escAttr(label) : label) + '">' + (typeof _escHtml === "function" ? _escHtml(label) : label) + "</span>";
      }
    }
    var html = "";
    try { html = fe85_as0.apply(this, arguments) || ""; } catch (e2) { html = ""; }
    return fe85_cleanHtml(html);
  };
} catch (eAs) {}
try {
  var fe85_stat0 = stat;
  stat = function (tk) {
    var id = fe85_id(tk);
    if (fe85_waiting(id) && !fe85_live(id)) return fe85_skel();
    var html = "";
    try { html = fe85_stat0.apply(this, arguments) || ""; } catch (e) { html = ""; }
    if (fe85_live(id) && /UNAVAILABLE/.test(html)) {
      var closed = false;
      try { closed = fe83f_marketClosed(id); } catch (e2) { closed = false; }
      if (closed) html = html.replace(/>UNAVAILABLE</g, ">CLOSED<");
    }
    if ((id === "XAU" || id === "GC=F") && /spot/i.test(html)) {
      var fut = false;
      try { var gb = fe83f_goldBits(); fut = !!(gb && gb.kind === "futures"); } catch (e3) { fut = false; }
      if (fut) html = html.replace(/(\s*[·|•]\s*)spot\b/ig, "");
    }
    return fe85_cleanHtml(html);
  };
} catch (eStat) {}
try {
  var fe85_cell0 = fe82_tapeCell;
  fe82_tapeCell = function (tk, ch, d) {
    var id = fe85_id(tk);
    if (id === "XAU" || id === "GC=F" || tk === "XAU") {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      var line = fe85_goldChg(b);
      if (line) return line;
    }
    var out = "";
    try { out = fe85_cell0.apply(this, arguments); } catch (e2) { out = ""; }
    return out;
  };
} catch (eCell) {}
try {
  var fe85_chg0 = fe66_chgLine;
  fe66_chgLine = function (tk, d, na) {
    var id = fe85_id(tk);
    if (id === "XAU" || id === "GC=F") {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      var line = fe85_goldChg(b);
      if (line) return line;
    }
    var out = "";
    try { out = fe85_chg0.apply(this, arguments) || ""; } catch (e2) { out = ""; }
    return fe85_clean(out);
  };
} catch (eChg) {}
try {
  var fe85_badge0 = fe68_badge;
  var fe85_badgeBusy = false;
  fe68_badge = function (m, tk, now) {
    var o = fe85_badge0.apply(this, arguments);
    if (!o || fe85_badgeBusy) return o;
    fe85_badgeBusy = true;
    try {
      var id = fe85_id(tk);
      if (id === "XAU" || id === "GC=F") {
        var b = null;
        try { b = fe83f_goldBits(); } catch (e) { b = null; }
        if (b && b.kind === "futures") {
          o.detail = "Gold futures (GC=F)";
          if (/spot|api\.|\/price\/|gold-api/i.test(String(o.fe64Note || "") + " " + String(o.label || ""))) {
            var hm = "";
            try { hm = typeof fe64_ukHm === "function" ? fe64_ukHm(o.asOf) : ""; } catch (e2) { hm = ""; }
            var asof = hm ? ("as of " + hm + " UK") : "Gold futures (GC=F)";
            if (/spot|api|gold-api/i.test(String(o.fe64Note || ""))) o.fe64Note = asof;
            if (/spot|api|gold-api/i.test(String(o.label || ""))) o.label = o.status === "live" ? "LIVE" : asof;
          }
        }
      }
      if (o.status === "closed" && /^closed$/i.test(String(o.fe64Note || "").trim())) o.fe64Note = "";
      o.label = fe85_clean(o.label);
      o.detail = fe85_clean(o.detail);
      o.fe64Note = fe85_clean(o.fe64Note);
    } catch (e3) {}
    fe85_badgeBusy = false;
    return o;
  };
} catch (eBd) {}
try {
  var fe85_reg0 = fe83f_regimeLine;
  fe83f_regimeLine = function (re) {
    re = re || {};
    var owns = function (k) { return Object.prototype.hasOwnProperty.call(re, k); };
    // The regime object is the prior builder's contract, including a leg the
    // caller left out. The bag sentence is for the painter's empty call, and
    // for a card whose own figures are the dash.
    var regimeObj = owns("spx") || owns("vix") || owns("score") || owns("label") || owns("loading") || owns("oil") || owns("btc") || owns("spxChg");
    var dashed = re.spx === "—" || re.spx === "–" || re.vix === "—" || re.vix === "–";
    if (regimeObj && !dashed) {
      try { return fe85_reg0.apply(this, arguments); } catch (e0) { return ""; }
    }
    var spxName = re && re.spxProxy ? "SPY" : "SPX";
    var spxTk = re && re.spxProxy ? "SPY" : "SPX";
    var bits = [];
    var a = "", b = "";
    try { a = fe85_sessionLine(spxTk, spxName); } catch (e) { a = ""; }
    try { b = fe85_sessionLine("VIX", "VIX"); } catch (e2) { b = ""; }
    if (a) bits.push(a);
    if (b) bits.push(b);
    if (!bits.length) {
      if (fe85_waiting("SPX") || fe85_waiting("VIX")) return "";
      if (!fe85_live("SPX") && !fe85_live("SPY") && !fe85_live("VIX")) {
        return '<div class="fe83f-regime-in" style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5">SPX — · VIX —</div>';
      }
      try { return fe85_reg0.apply(this, arguments); } catch (e3) { return ""; }
    }
    return '<div class="fe83f-regime-in" style="font-size:10px;color:var(--t2);margin-top:4px;line-height:1.5">' + bits.join(" · ") + "</div>";
  };
} catch (eReg) {}
try {
  var fe85_lbl0 = _signalSourceLabel;
  _signalSourceLabel = function (meta) {
    var out = "";
    try { out = fe85_lbl0.apply(this, arguments) || ""; } catch (e) { out = ""; }
    out = fe85_clean(out);
    if (!out || /no source returned/i.test(out)) return fe85_plainReason();
    return out;
  };
} catch (eLbl) {}
try {
  var fe85_ev0 = _signalEvidence;
  _signalEvidence = function (signal) {
    var ev = fe85_ev0.apply(this, arguments);
    if (!ev || !signal) return ev;
    try {
      var id = fe85_id(signal.tk);
      if (fe85_waiting(id) && !fe85_live(id)) {
        ev.price = "…";
        ev.status = "…";
        ev.source = "Checking the live prices";
        ev.asOf = "…";
        ev.reason = "";
        ev.stale = false;
        ev.fe85Wait = true;
        return ev;
      }
      if (fe85_live(id) && (ev.price === "UNAVAILABLE" || ev.status === "UNAVAILABLE" || /no source returned/i.test(String(ev.source || "")))) {
        var d = null;
        try { d = fp(id); } catch (e) { d = null; }
        if (d && d.p && d.p !== "—") {
          ev.price = d.p;
          var closed = false;
          try { closed = fe83f_marketClosed(id); } catch (e2) { closed = false; }
          ev.status = closed ? "CLOSED" : (d.label || d.status || ev.status);
          try { if (d.asOf && typeof _fmtAsOf === "function") ev.asOf = _fmtAsOf(d.asOf); } catch (e3) {}
          try { ev.source = _quoteSourceLabel(d.src); } catch (e4) {}
          ev.reason = "";
          ev.stale = d.status === "stale";
          ev.fe85Wait = false;
        }
      }
      if (/no source returned/i.test(String(ev.source || "") + " " + String(ev.reason || ""))) {
        ev.source = fe85_plainReason();
        ev.reason = fe85_plainReason();
      }
      ev.source = fe85_clean(ev.source);
      ev.reason = fe85_clean(ev.reason);
      ev.status = fe85_clean(ev.status);
    } catch (e5) {}
    return ev;
  };
} catch (eEv) {}
try {
  var fe85_st0 = _rt52State;
  _rt52State = function (tk) {
    var id = fe85_id(tk);
    if (fe85_waiting(id) && !fe85_live(id)) return { open: false, txt: "", at: "" };
    var st = fe85_st0.apply(this, arguments);
    if (st && st.txt) st.txt = fe85_clean(st.txt);
    if (st && /no price yet/i.test(st.txt || "") && fe85_live(id)) st.txt = "Closed";
    return st;
  };
} catch (eSt) {}
try {
  var fe85_sig0 = _rt52Sig;
  _rt52Sig = function (s) {
    var id = fe85_id(s && s.tk);
    if (s && fe85_waiting(id) && !fe85_live(id)) {
      return { ev: { price: "…", source: "Checking the live prices", status: "…", reason: "", stale: false, conviction: null, move: null }, st: { txt: "", at: "" }, mvT: "", held: false, why: "", line: "", hz: "", cf: null, fe85Wait: true };
    }
    var g = fe85_sig0.apply(this, arguments);
    if (!g) return g;
    if (g.line) g.line = fe85_clean(String(g.line).replace(/No source returned/gi, fe85_plainReason()));
    if (g.why) g.why = fe85_clean(String(g.why).replace(/No source returned/gi, fe85_plainReason()));
    if (g.ev && g.ev.source) g.ev.source = fe85_clean(String(g.ev.source).replace(/No source returned/gi, fe85_plainReason()));
    return g;
  };
} catch (eSig) {}
try {
  var fe85_card0 = _rt52SigCard;
  _rt52SigCard = function (s, i) {
    var id = fe85_id(s && s.tk);
    if (s && fe85_waiting(id) && !fe85_live(id)) return fe85_rowSkel();
    return fe85_card0.apply(this, arguments);
  };
} catch (eCard) {}
try {
  var fe85_tick0 = fe82_sigTick;
  fe82_sigTick = function () {
    var out = fe85_tick0.apply(this, arguments);
    try {
      if (typeof fe82_onSig !== "function" || !fe82_onSig()) return out;
      var desk = false;
      try { desk = typeof IS_DESKTOP === "function" && IS_DESKTOP(); } catch (e) { desk = false; }
      var root = desk ? document.getElementById("p3body") : document.getElementById("main");
      if (!root) return out;
      var list = typeof SIGS !== "undefined" && SIGS ? SIGS : [];
      var key = "";
      for (var i = 0; i < list.length; i++) {
        if (fe85_waiting(list[i] && list[i].tk)) key += (list[i].tk || "") + ",";
      }
      if (!root.querySelector("[data-fe85=row-wait]")) { fe85_waitKey = key; return out; }
      if (key !== fe85_waitKey) {
        fe85_waitKey = key;
        if (desk && typeof fe82_p30 === "function") fe82_p30();
        else if (!desk && typeof renderMain === "function") renderMain();
      }
    } catch (e2) {}
    return out;
  };
} catch (eTick) {}
try {
  var fe85_after0 = fe83f_afterPaint;
  fe83f_afterPaint = function () {
    var out = fe85_after0.apply(this, arguments);
    try { fe85_pass(); } catch (e) {}
    return out;
  };
} catch (eAfter) {}
try {
  var fe85_z0 = fe78_scrubZeros;
  var fe85_zAt = 0;
  fe78_scrubZeros = function (root) {
    try {
      if (typeof document !== "undefined" && root === document.body) {
        var now = Date.now();
        if (now - fe85_zAt < 1000) return;
        fe85_zAt = now;
        var sels = ["#main", "#tape", "#p2body", "#p3body", "#p4body"];
        for (var i = 0; i < sels.length; i++) {
          var el = document.querySelector(sels[i]);
          if (el) fe85_z0(el);
        }
        return;
      }
    } catch (e) {}
    return fe85_z0.apply(this, arguments);
  };
} catch (eZ) {}
try {
  var fe85_s79 = fe79_scrub;
  var fe85_s79At = 0;
  fe79_scrub = function (root) {
    try {
      if (typeof document !== "undefined" && root === document.body) {
        var now = Date.now();
        if (now - fe85_s79At < 1000) return;
        fe85_s79At = now;
        var sels = ["#main", "#tape", "#p2body", "#p3body", "#p4body"];
        for (var i = 0; i < sels.length; i++) {
          var el = document.querySelector(sels[i]);
          if (el) fe85_s79(el);
        }
        return;
      }
    } catch (e) {}
    return fe85_s79.apply(this, arguments);
  };
} catch (e79) {}
try {
  var fe85_s80 = fe80_scrubRegime;
  var fe85_s80At = 0;
  fe80_scrubRegime = function (root) {
    try {
      if (typeof document !== "undefined" && root === document.body) {
        var now = Date.now();
        if (now - fe85_s80At < 1000) return;
        fe85_s80At = now;
        var sels = ["#main", "#p2body", "#p3body", "#p4body"];
        for (var i = 0; i < sels.length; i++) {
          var el = document.querySelector(sels[i]);
          if (el) fe85_s80(el);
        }
        return;
      }
    } catch (e) {}
    return fe85_s80.apply(this, arguments);
  };
} catch (e80) {}
function fe85_headerClock(now) {
  var ms = now && now.getTime ? now.getTime() : Date.now();
  var day = "", hm = "";
  try { day = _rt18Fmt("Europe/London", "day").format(new Date(ms)).replace(/,/g, "").replace(/\s+/g, " ").trim(); } catch (e) { day = ""; }
  try { hm = fe64_ukHm(ms); } catch (e2) { hm = ""; }
  if (day && hm) return day + " · " + hm + " UK";
  return fe85_clockText(ms);
}
function fe85_writeClock() {
  if (typeof document === "undefined") return;
  var line = "";
  try { line = fe85_headerClock(new Date()); } catch (e) { line = ""; }
  if (!line || line.indexOf("UK") < 0) return;
  var clk = document.getElementById("clk");
  var clkD = document.getElementById("clkD");
  if (clk && clk.textContent !== line) clk.textContent = line;
  if (clk && clk.getAttribute("title") !== "UK time") clk.setAttribute("title", "UK time");
  if (clkD && clkD.textContent) clkD.textContent = "";
}
function fe85_cryptoTk(tk) {
  try { if (typeof fe79_isCryptoTk === "function" && fe79_isCryptoTk(tk)) return true; } catch (e) {}
  try { if (typeof fe78_isCrypto === "function" && fe78_isCrypto(tk)) return true; } catch (e2) {}
  return false;
}
function fe85_glanceBits(tk) {
  var id = fe85_id(tk);
  if (!id) return "";
  var pct = null, pts = "";
  var goldName = "";
  if (id === "XAU" || id === "GC=F") {
    var b = null;
    try { b = fe83f_goldBits(); } catch (e) { b = null; }
    if (b && b.kind === "futures") { pct = b.pct; pts = b.pts || ""; goldName = "Gold futures (GC=F)"; }
  } else if (fe85_cryptoTk(id)) {
    try { pct = fe79_liveCryptoPct(id); } catch (e2) { pct = null; }
    var px = null, base = null;
    try { px = Number(P[id] && P[id].p); } catch (e3) { px = null; }
    try { var bag = fe79_cryptoBase(id); base = bag && Number(bag.base); } catch (e4) { base = null; }
    if (!(base > 0)) {
      try {
        var stored = (typeof fe79_srv !== "undefined" && fe79_srv[id]) || null;
        var basis = stored ? String(stored.changeBasisLabel || stored.changeBasis || "") : "";
        if (/24h/i.test(basis) && Number(stored.baselinePrice) > 0) base = Number(stored.baselinePrice);
      } catch (e4b) { base = null; }
    }
    if (px > 0 && base > 0 && Math.abs(px - base) >= 0.005) pts = fe85_signed(px - base, "");
  } else {
    try { pct = typeof liveChg === "function" ? liveChg(id) : null; } catch (e5) { pct = null; }
    var raw = null, pc = null, px2 = null, prev = null;
    try { var d = fp(id); raw = d && typeof d.raw === "number" ? d.raw : null; if (d && d.c != null && d.c !== "") pc = Number(String(d.c).replace(/[%+,]/g, "")); } catch (e6) {}
    if (raw != null && isFinite(raw) && Math.abs(raw) >= 0.05 && (pc == null || !isFinite(pc) || Math.abs(raw - pc) > 0.05)) pts = fe85_signed(raw, "");
    if (!pts) {
      try { px2 = Number(P[id] && P[id].p); } catch (e7) { px2 = null; }
      try { prev = Number(BASE[id] && BASE[id].p); } catch (e8) { prev = null; }
      if (px2 > 0 && prev > 0 && Math.abs(px2 - prev) >= 0.05) pts = fe85_signed(px2 - prev, "");
    }
  }
  var pctS = pct == null || !isFinite(Number(pct)) ? "" : fe85_signed(pct, "%");
  var day = "";
  if (!fe85_cryptoTk(id)) {
    try { if (typeof fe83f_marketClosed === "function" && fe83f_marketClosed(id)) day = fe83f_pickDay(id) || ""; } catch (e9) { day = ""; }
  }
  var line = fe85_paren(pts, pctS, day);
  if (goldName && line) line = goldName + " " + line;
  try { if (typeof fe83f_fixSigns === "function") line = fe83f_fixSigns(line); } catch (e10) {}
  return line;
}
function fe85_paintGlance() {
  if (typeof document === "undefined") return;
  var rows = document.querySelectorAll(".home-row");
  for (var i = 0; i < rows.length; i++) {
    var oc = rows[i].getAttribute("onclick") || "";
    var m = oc.match(/openA\('([^']+)'\)/);
    var nameEl = rows[i].querySelector(".home-row-tk");
    var tk = m ? m[1] : (nameEl ? nameEl.textContent : "");
    var line = fe85_glanceBits(tk);
    var ch = rows[i].querySelector(".home-row-ch");
    if (ch && line && ch.textContent !== line) ch.textContent = line;
  }
  var chips = document.querySelectorAll(".wl-glance-chip");
  for (var j = 0; j < chips.length; j++) {
    var oc2 = chips[j].getAttribute("onclick") || "";
    var m2 = oc2.match(/openA\('([^']+)'\)/);
    if (!m2) continue;
    var line2 = fe85_glanceBits(m2[1]);
    var ce = chips[j].querySelector(".wl-g-c");
    if (ce && line2 && ce.textContent !== line2) ce.textContent = line2;
  }
  var tiles = document.querySelectorAll("[data-bb1-tile]");
  var map = { gold: "XAU", dollar: "DXY", vix: "VIX", brent: "BRENT", wti: "WTI", btc: "BTC" };
  for (var k = 0; k < tiles.length; k++) {
    var id = tiles[k].getAttribute("data-bb1-tile") || "";
    var sym = map[id];
    if (!sym) continue;
    var line3 = fe85_glanceBits(sym);
    if (!line3) continue;
    if (id === "gold") {
      var futs = tiles[k].querySelectorAll(".fe77-fut");
      for (var f = 0; f < futs.length; f++) {
        if (!/high|low/i.test(futs[f].textContent || "")) futs[f].textContent = "";
      }
      var meta = tiles[k].querySelector(".bb1-meta");
      if (meta && /spot|\(api|\/price\/|api\./i.test(meta.textContent || "")) {
        var asof = "";
        try { asof = fe85_asofBits(); } catch (eM) { asof = "Gold futures (GC=F)"; }
        if (meta.textContent !== asof) meta.textContent = asof;
      }
    }
    var c = tiles[k].querySelector(".bb1-c");
    if (!c) {
      var v = tiles[k].querySelector(".bb1-v");
      if (!v) continue;
      c = document.createElement("span");
      c.className = "bb1-c";
      v.appendChild(document.createTextNode(" "));
      v.appendChild(c);
    }
    if (c.textContent !== line3) c.textContent = line3;
  }
}
try { setInterval(function () { try { fe85_paintGoldDom(); fe85_paintRegimeDom(); fe85_writeClock(); } catch (e) {} }, 1000); } catch (eIv) {}
try {
  fe85_writeClock();
  var fe85_clkEl = document.getElementById("clk");
  if (fe85_clkEl && typeof MutationObserver === "function") {
    var fe85_clkObs = new MutationObserver(function () {
      var line = "";
      try { line = fe85_headerClock(new Date()); } catch (e) { line = ""; }
      if (line && fe85_clkEl.textContent !== line) fe85_clkEl.textContent = line;
      var day = document.getElementById("clkD");
      if (day && day.textContent) day.textContent = "";
    });
    fe85_clkObs.observe(fe85_clkEl, { characterData: true, childList: true, subtree: true });
    var fe85_dayEl = document.getElementById("clkD");
    if (fe85_dayEl) fe85_clkObs.observe(fe85_dayEl, { characterData: true, childList: true, subtree: true });
  }
} catch (eClk) {}
try {
  var fe85_tape0 = renderTape;
  renderTape = function () {
    var r = fe85_tape0.apply(this, arguments);
    try { fe85_paintTapeOnly(); } catch (e) {}
    return r;
  };
} catch (eTape) {}
try {
  var fe85_rtp0 = _rtPaint;
  _rtPaint = function () {
    var r = fe85_rtp0.apply(this, arguments);
    try { fe85_paintTapeOnly(); } catch (e) {}
    return r;
  };
} catch (eRtp) {}
try {
  var fe85_ptsBit0 = fe83f_ptsBit;
  fe83f_ptsBit = function (d) {
    var n = null;
    try { n = fe85_ptsBit0.apply(this, arguments); } catch (e) { n = null; }
    if (d && typeof d.chg === "string" && d.chg.indexOf("%") < 0 && (n == null || Math.abs(Number(n)) < 0.05)) {
      var alt = fe85_num(d.chg);
      if (alt != null && Math.abs(alt) >= 5) return alt;
    }
    return n;
  };
} catch (ePts) {}
try {
  var fe85_fix0 = fe82_fixChip;
  fe82_fixChip = function (el, tk) {
    try { fe85_fix0.apply(this, arguments); } catch (e) {}
    var line = "";
    try { line = fe85_glanceBits(tk); } catch (e2) { line = ""; }
    var ce = el && el.querySelector ? el.querySelector(".wl-g-c") : null;
    if (ce && line && ce.textContent !== line) ce.textContent = line;
  };
} catch (eFix) {}
try {
  var fe85_wl0 = _paintWlGlance;
  _paintWlGlance = function () {
    var r = fe85_wl0.apply(this, arguments);
    try { fe85_paintGlance(); } catch (e) {}
    return r;
  };
} catch (eWl) {}
try {
  var fe85_wd0 = fe83f_todayWd;
  var fe85_wdAt = 0, fe85_wdVal = "";
  fe83f_todayWd = function () {
    var now = Date.now();
    if (fe85_wdVal && now - fe85_wdAt < 30000) return fe85_wdVal;
    fe85_wdAt = now;
    try { fe85_wdVal = fe85_wd0.apply(this, arguments) || ""; } catch (e) { fe85_wdVal = ""; }
    return fe85_wdVal;
  };
} catch (eWd) {}
"""


def die(msg):
    print("FAIL", msg)
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


def run_unit(app_text):
    pure = app_text.split("// fe85-pure-begin", 1)[1].split("// fe85-pure-end", 1)[0]
    src = pure + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
var spot = fe85_clean("CLOSED · spot (api./price/XAU)");
assert(spot.indexOf("api./") < 0 && spot.indexOf("/price/") < 0 && spot.indexOf("(api") < 0, "path");
assert(fe85_clean("CLOSED · SPOT (API./PRICE/XAU)").toLowerCase().indexOf("api") < 0, "path case");
assert(fe85_clean("https://api.gold-api.com/price/XAU").indexOf("price") < 0, "url");
assert(fe85_clean("CLOSED · CLOSED") === "CLOSED", "dup");
assert(fe85_clean("Yahoo Finance · CLOSED · CLOSED") === "Yahoo Finance · CLOSED", "yahoo");
assert(fe85_clean("WTI CLOSED · CLOSED") === "WTI CLOSED", "wti");
assert(fe85_clean("EURUSD CLOSED · CLOSED") === "EURUSD CLOSED", "eur");
assert(fe85_clean("STALE · STALE") === "STALE", "stale");
assert(fe85_clean("Gold futures (GC=F) · as of 23:31 UK") === "Gold futures (GC=F) · as of 23:31 UK", "keep asof");
assert(fe85_ptsFrom(null, { points: -51.7, pct: -1.29 }, null) === -51.7, "pts field");
assert(fe85_ptsFrom({ displayChange: { change: -51.7, changePct: -1.29 } }, null, null) === -51.7, "displayChange");
assert(fe85_ptsFrom(null, { futuresChange: { points: -51.7, changePct: -1.29 } }, null) === -51.7, "futuresChange");
assert(fe85_ptsFrom(null, { changePct: -1.29 }, null) == null, "pct is not points");
var gold = fe85_goldLine("-1.29%", "-51.70", "Fri");
assert(gold === "-51.70 · -1.29% Fri", "gold line");
assert(gold.indexOf("Sat") < 0, "no sat");
var reg = fe85_regimeText("SPX", "7,623.68", "-0.52%", "Fri", true, "opens Mon 13:30 UK");
assert(reg === "SPX 7,623.68 · -0.52% Fri · closed, opens Mon 13:30 UK", "regime");
assert(reg.indexOf("—") < 0 && reg.indexOf("CLOSED · CLOSED") < 0, "regime shape");
assert(fe85_regimeText("SPX", "", "", "", true, "") === "", "empty close");
assert(fe85_paren("-51.70", "-1.29%", "Fri") === "-51.70 (-1.29%) Fri", "paren");
assert(fe85_paren("-51.70", "-1.29%", "Fri").indexOf("+-") < 0, "no double sign");
var clk = fe85_clockText(Date.parse("2026-10-24T23:52:00Z"));
assert(clk === "Sun 25 Oct · 00:52 UK", "clock " + clk);
assert(clk.indexOf("19:52") < 0 && clk.indexOf("24-10-2026") < 0, "not local date");
console.log("fe85 unit ok");
"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe85 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def check_js(text, label):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8", newline="\n")
    try:
        tmp.write(text)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die(label + "\n" + chk.stdout + chk.stderr)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


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
    if not index_sum.startswith(EXPECT_INDEX_PREFIX):
        print("WARN index.html md5 %s expected prefix %s" % (index_sum, EXPECT_INDEX_PREFIX))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if app.count(NEED_MARKER) != 1:
        die("need marker count %s" % app.count(NEED_MARKER))
    if index.count('app.js?v=chat84"') != 1:
        die("cache bust anchor missing")
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count(REFUSE_MARKER) != 1:
        die("refuse marker")
    if app.count("function fe85_clean(") != 1 or app.count("function fe85_ptsFrom(") != 1:
        die("pure defs")
    if "function fe84_dtfShim" not in app or not app.startswith("(function fe84_dtfShim(){"):
        die("shim moved")
    index = index.replace('app.js?v=chat84"', 'app.js?v=chat85"', 1)
    if index.count('app.js?v=chat85"') != 1 or "chat84" in index:
        die("cache bust")
    check_js(app, "node --check failed")
    print("node --check ok")
    crlf = app.replace("\n", "\r\n")
    back = crlf.replace("\r\n", "\n")
    if back != app or b"\r\n" not in crlf.encode("utf-8"):
        die("crlf roundtrip")
    check_js(back, "crlf node --check failed")
    print("crlf ok")
    run_unit(app)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
