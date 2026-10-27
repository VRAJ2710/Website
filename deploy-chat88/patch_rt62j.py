#!/usr/bin/env python3
"""rt62j client patch: chat86 -> chat87. Anchors decide; md5 only warns.

Applies on the chat86 output (PR #83). Keeps every fe84, fe85 and fe86 guard.

The gold desk headline is the futures price with the futures change. Spot is a
labelled secondary with no daily move. A closed price keeps the session stamp,
never the clock that generated the AI line. Commodity badges say CLOSED while
the venue is shut, and a commodity row's main figure is the futures print.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "21f3cee5da20d9fc2f2f03d21623dcb4"
EXPECT_INDEX_PREFIX = "cb90c315"
NEED_MARKER = "// ── rt62i ──"
REFUSE_MARKER = "// ── rt62j ──"

BLOCK = r"""
// ── rt62j ──
// fe87: one gold book on the desk, a closed price keeps its session time,
// and a commodity row quotes the same futures figure it labels.
// fe87-pure-begin
function fe87_esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function fe87_chg(pts, pct, day, open) {
  var when = open ? "today" : (day || "");
  var line = "";
  if (pts && pct) line = String(pts) + " (" + String(pct) + ")";
  else if (pct) line = String(pct);
  else if (pts) line = String(pts);
  if (when) line = line ? (line + " " + when) : when;
  return line;
}
function fe87_book(futPx, spotPx, pts, pct, day, open) {
  var chg = fe87_chg(pts, pct, day, open);
  var spot = spotPx ? ("Spot $" + spotPx) : "";
  return {
    label: "Gold futures (GC=F)",
    px: futPx ? ("$" + futPx) : "",
    chg: chg,
    spot: spot,
    ok: !/%/.test(spot) && (!pct || chg.indexOf(String(pct)) >= 0) && (!pts || chg.indexOf(String(pts)) >= 0)
  };
}
function fe87_feet(futStamp, spotStamp, aiHm, reopen, closed) {
  var fut = closed ? "Futures (GC=F)" : "Futures (GC=F, delayed 10 min)";
  if (futStamp) fut += " \u00b7 as of " + futStamp;
  if (closed) fut += " \u00b7 market closed" + (reopen ? ", " + reopen : "");
  var spot = "Spot (gold-api)";
  if (spotStamp) spot += " \u00b7 as of " + spotStamp;
  var ai = "AI scenario analysis";
  var hm = String(aiHm || "").replace(/\s*UK$/i, "").trim();
  if (hm) ai += " \u00b7 generated " + hm + " UK";
  return { fut: fut, spot: spot, ai: ai };
}
function fe87_aiInPrice(feet, hm) {
  var t = String(hm || "").replace(/\s*UK$/i, "").trim();
  if (!t || !feet) return false;
  return String(feet.fut).indexOf(t) >= 0 || String(feet.spot).indexOf(t) >= 0;
}
function fe87_jargon(s) {
  return /api\.|\/price\/|\(api/i.test(String(s || ""));
}
function fe87_macroMeta(stamp, reopen, closed, nowHm) {
  if (!closed) return stamp ? ("as of " + stamp) : "";
  var use = stamp && (!nowHm || String(stamp).indexOf(nowHm) < 0) ? stamp : "";
  var tail = "market closed" + (reopen ? ", " + reopen : "");
  var line = use ? ("as of " + use + " \u00b7 " + tail) : tail;
  if (nowHm && line.indexOf(nowHm) >= 0) line = tail;
  return line;
}
function fe87_badge(closed, reopen) {
  if (!closed) return "";
  var r = String(reopen || "").replace(/\s+/g, " ").trim();
  if (!r) r = "reopens Sunday evening UK";
  if (!/^reopens\b/i.test(r)) r = "reopens " + r;
  return "CLOSED \u00b7 " + r;
}
function fe87_dropNow(text, nowHm, stamp) {
  var t = String(text || "");
  if (!nowHm || t.indexOf(nowHm) < 0) return t;
  var use = stamp && String(stamp).indexOf(nowHm) < 0 ? stamp : "";
  var repl = use ? ("as of " + use) : "";
  t = t.split("as of " + nowHm + " UK").join(repl);
  t = t.split("as of " + nowHm).join(repl);
  if (t.indexOf(nowHm) >= 0) t = t.split(nowHm).join(use);
  t = t.replace(/(?:\s*\u00b7\s*)?as of UK\b/g, "");
  t = t.replace(/\bUK UK\b/g, "UK");
  t = t.replace(/\s*\u00b7\s*\u00b7\s*/g, " \u00b7 ");
  t = t.replace(/\s{2,}/g, " ").replace(/^[\s\u00b7]+|[\s\u00b7]+$/g, "");
  return t;
}
function fe87_intelShort(s, date) {
  var t = String(s || "").replace(/\s+/g, " ").trim();
  var m = t.match(/(\d+)\s+of\s+(\d+)\s+markets\s+trading\s+now(?:\s*[\u00b7,]\s*(\d+)\s+closed)?/i);
  if (!m) return t;
  var out = m[1] + " of " + m[2] + " markets open";
  if (m[3]) out += " \u00b7 " + m[3] + " closed";
  var dm = t.match(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+[A-Za-z]{3}\b/);
  var d = dm ? dm[0] : (date || "");
  if (d) out += " \u00b7 " + d;
  return out;
}
function fe87_samePx(main, quoted) {
  function n(s) {
    var m = String(s || "").replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
    return m ? Number(m[0]) : NaN;
  }
  var a = n(main), b = n(quoted);
  return isFinite(a) && isFinite(b) && Math.abs(a - b) < 0.001;
}
function fe87_subClosed(text) {
  var t = String(text || "");
  t = t.replace(/\s*\u00b7\s*delayed\s+\d+\s*min\b/ig, "");
  t = t.replace(/\bdelayed\s+\d+\s*min\b/ig, "");
  return t.replace(/\s{2,}/g, " ").replace(/\s*\u00b7\s*$/g, "").trim();
}
// fe87-pure-end
var fe87_at = 0;
var fe87_inMeta = false;
var fe87_spotMem = Object.create(null);
var fe87_badgeCache = Object.create(null);
var fe87_msCache = Object.create(null);
var fe87_CMD = { WTI: 1, BRENT: 1, COPPER: 1, PALLADIUM: 1, NG: 1, SLV: 1, PLAT: 1 };
function fe87_cmdTk(tk) { return !!fe87_CMD[String(tk || "")]; }
function fe87_id(tk) {
  try { if (typeof fe86_id === "function") return fe86_id(tk) || tk; } catch (e) {}
  return tk;
}
function fe87_isClosed(tk) {
  try { if (typeof fe86_closed === "function") return !!fe86_closed(tk); } catch (e) {}
  try { return typeof fe83f_marketClosed === "function" && !!fe83f_marketClosed(tk); } catch (e2) {}
  return false;
}
function fe87_pxText(n) {
  try { if (typeof fe83f_px === "function") return fe83f_px(n) || ""; } catch (e) {}
  var v = Number(n);
  return isFinite(v) ? v.toFixed(2) : "";
}
function fe87_ms(v) {
  if (v == null || v === "") return 0;
  if (typeof v === "number" && isFinite(v)) {
    if (v > 1e12) return v;
    if (v > 1e9) return v * 1000;
    return 0;
  }
  if (typeof v === "string") {
    var n = Date.parse(v);
    if (isFinite(n)) return n;
    if (/^\d{13}$/.test(v)) return Number(v);
    if (/^\d{10}$/.test(v)) return Number(v) * 1000;
  }
  return 0;
}
function fe87_best(list, now) {
  var best = 0;
  for (var i = 0; i < list.length; i++) {
    var ms = list[i];
    if (!(ms > 1e11)) continue;
    if (Math.abs(now - ms) < 15 * 60 * 1000) continue;
    if (!best || ms > best) best = ms;
  }
  return best;
}
function fe87_sessionMs(tk) {
  var now = Date.now();
  var hit = fe87_msCache[tk];
  if (hit && now - hit.at < 8000) return hit.v;
  var session = [], generic = [];
  function add(bucket, v) { var ms = fe87_ms(v); if (ms) bucket.push(ms); }
  if (tk === "XAU" || tk === "GC=F") {
    try {
      var f = typeof fe77_futObj === "function" ? fe77_futObj() : null;
      if (f) { add(session, f.regularMarketTime); add(session, f.sessionAsOf); add(generic, f.asOf); add(generic, f.ts); }
    } catch (e) {}
    try { if (typeof _gdHist !== "undefined" && _gdHist) add(session, _gdHist.asOf); } catch (e2) {}
    try { if (typeof fe82_goldDc !== "undefined" && fe82_goldDc) { add(session, fe82_goldDc.regularMarketTime); add(generic, fe82_goldDc.asOf); } } catch (e3) {}
  }
  try {
    var b = typeof fe78_bag === "function" ? fe78_bag(tk) : null;
    if (b) { add(session, b.regularMarketTime); add(session, b.sessionAsOf); add(generic, b.asOf); add(generic, b.ts); }
  } catch (e4) {}
  try {
    var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null;
    if (y) { add(session, y.regularMarketTime); add(generic, y.asOf); add(generic, y.ts); }
  } catch (e5) {}
  try { var rec = fe87_futRec(tk); if (rec) add(session, rec.ts); } catch (e6) {}
  try { var d = typeof fp === "function" ? fp(tk) : null; if (d) add(generic, d.asOf); } catch (e7) {}
  try { if (typeof liveQuoteTs !== "undefined") add(generic, liveQuoteTs[tk]); } catch (e8) {}
  var v = fe87_best(session, now) || fe87_best(generic, now) || 0;
  if (v) fe87_msCache[tk] = { at: now, v: v };
  return v;
}
function fe87_stamp(ms) {
  if (!(ms > 0)) return "";
  var wd = "", hm = "";
  try { wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date(ms)); } catch (e) { wd = ""; }
  try { hm = typeof fe64_ukHm === "function" ? fe64_ukHm(ms) : ""; } catch (e2) { hm = ""; }
  if (!hm) return "";
  return (wd ? wd + " " : "") + hm + " UK";
}
function fe87_nowHm() {
  try { return typeof fe64_ukHm === "function" ? (fe64_ukHm(Date.now()) || "") : ""; } catch (e) { return ""; }
}
function fe87_reopenPhrase(tk) {
  var o = "";
  try { o = typeof fe85_opens === "function" ? (fe85_opens(tk) || "") : ""; } catch (e) { o = ""; }
  if (o && /opens\s+\S/i.test(o)) return String(o).replace(/^\s*opens\b/i, "reopens").replace(/\s+/g, " ").trim();
  try {
    var note = typeof fe65_closedNote === "function" ? fe65_closedNote(tk, null) : "";
    if (note && /opens\s+\d/i.test(note)) return String(note).replace(/^\s*opens\b/i, "reopens").replace(/\s+/g, " ").trim();
  } catch (e2) {}
  if (tk === "XAU" || tk === "GC=F" || fe87_cmdTk(tk)) return "reopens Sunday evening UK";
  return "";
}
function fe87_futRec(tk) {
  try {
    var rec = (typeof _rt43Fut !== "undefined" && _rt43Fut) ? _rt43Fut[tk] : null;
    if (rec && rec.p > 0) return rec;
  } catch (e) {}
  return null;
}
function fe87_applyFut(tk) {
  if (!fe87_cmdTk(tk)) return 0;
  var rec = fe87_futRec(tk);
  if (!rec) return 0;
  try {
    if (typeof P !== "undefined" && P[tk] && Math.abs(Number(P[tk].p) - Number(rec.p)) >= 0.0005) {
      if (!(fe87_spotMem[tk] > 0)) fe87_spotMem[tk] = Number(P[tk].p);
      P[tk] = { p: rec.p, c: isFinite(Number(rec.c)) ? +Number(rec.c).toFixed(2) : P[tk].c };
    }
  } catch (e) {}
  return rec.p;
}
function fe87_css() {
  try {
    if (typeof document === "undefined" || document.getElementById("fe87-css")) return;
    var st = document.createElement("style");
    st.id = "fe87-css";
    st.textContent = '[data-bb1-tile="gold"] .fe87-label{display:block;margin-top:4px;font:500 12px/1.35 var(--data,ui-monospace);color:var(--ink-2,#A8ADB6);white-space:normal}[data-bb1-tile="gold"] .bb1-v{display:block;white-space:normal}[data-bb1-tile="gold"] .bb1-c{display:block;margin:3px 0 0;white-space:normal}.gd-hero .fe87-chg{display:block;margin-top:2px}.gd-hero .fe87-spot{display:block;margin-top:4px;font:500 13px/1.35 var(--mn,ui-monospace);color:var(--t2,#A8ADB6)}.gd-hero .gd-asof .fe87-fut,.gd-hero .gd-asof .fe87-spot-src,.gd-hero .gd-asof .fe87-ai{display:block;margin-top:2px}.fe87-futsrc,.fe87-spotpx{display:block;margin-top:3px;font:500 11px/1.35 var(--mn,ui-monospace);color:var(--t2,#A8ADB6);white-space:normal}@media(max-width:430px){#siteIntelBar .si-bar-inner{flex-wrap:wrap}#siteIntelBar .si-bar-scroll-wrap{overflow:visible;flex:1 1 auto;min-width:0;max-width:100%}#siteIntelBar .si-bar-scroll-track{display:block;width:100%;max-width:100%;animation:none !important}#siteIntelBar .si-bar-chunk{white-space:normal;display:inline}#siteIntelBar .si-bar-chunk+.si-bar-chunk{display:none !important}}';
    document.head.appendChild(st);
  } catch (e) {}
}
function fe87_ukDate(ms) {
  try {
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short" }).formatToParts(new Date(ms));
    var wd = "", day = "", mon = "";
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].type === "weekday") wd = parts[i].value;
      else if (parts[i].type === "day") day = parts[i].value;
      else if (parts[i].type === "month") mon = parts[i].value;
    }
    return wd && day && mon ? (wd + " " + day + " " + mon) : "";
  } catch (e) { return ""; }
}
function fe87_heroModel() {
  var b = null;
  try { b = fe83f_goldBits(); } catch (e) { b = null; }
  if (!b || b.kind !== "futures" || b.px == null) return null;
  var px = fe87_pxText(b.px);
  if (!px) return null;
  var closed = fe87_isClosed("XAU");
  var day = "";
  try { day = (typeof fe86_day === "function" && fe86_day("XAU")) || (typeof fe85_goldDay === "function" && fe85_goldDay()) || ""; } catch (e2) { day = ""; }
  if (closed && !day) day = "Fri";
  var pct = b.pct == null ? "" : fe85_signed(b.pct, "%");
  var pts = b.pts || "";
  if (!pts) {
    try {
      var n = fe85_ptsFrom(null, typeof fe82_goldDc !== "undefined" ? fe82_goldDc : null, typeof fe77_futObj === "function" ? fe77_futObj() : null);
      if (n != null) pts = fe85_signed(n, "");
    } catch (e3) { pts = ""; }
  }
  var spotN = 0;
  try { spotN = Number(P.XAU && P.XAU.p); } catch (e4) { spotN = 0; }
  var spotPx = spotN > 0 && Math.abs(spotN - Number(b.px)) >= 0.05 ? fe87_pxText(spotN) : "";
  var book = fe87_book(px, spotPx, pts, pct, day, !closed);
  var nowHm = fe87_nowHm();
  var ai = "";
  try { ai = fe87_stamp(fe87_ms(_goldDesk && _goldDesk.asOf)); } catch (e5) { ai = ""; }
  var aiHm = ai ? ai.replace(/^[A-Za-z]{3}\s+\d{1,2}\s+[A-Za-z]{3}\s+\u00b7\s+/, "") : "";
  try {
    var raw = _goldDesk && _goldDesk.asOf ? fe87_ms(_goldDesk.asOf) : 0;
    if (raw) aiHm = (typeof fe64_ukHm === "function" ? fe64_ukHm(raw) : "") || aiHm;
  } catch (e6) {}
  var futStamp = fe87_stamp(fe87_sessionMs("XAU"));
  if (nowHm && futStamp && futStamp.indexOf(nowHm) >= 0) futStamp = "";
  if (aiHm && futStamp && futStamp.indexOf(aiHm) >= 0) futStamp = "";
  var spotStamp = "";
  var reopen = closed ? fe87_reopenPhrase("XAU") : "";
  var feet = fe87_feet(futStamp, spotStamp, aiHm ? (aiHm + " UK") : "", reopen, closed);
  book.cls = String(pct).charAt(0) === "-" ? "px-dn" : "px-up";
  book.feet = feet;
  book.closed = closed;
  return book;
}
function fe87_heroHtml(h) {
  if (typeof h !== "string" || h.indexOf("gd-px") < 0) return h;
  var model = null;
  try { model = fe87_heroModel(); } catch (e) { model = null; }
  if (!model) return h;
  h = h.replace(/(<div class="gd-kicker"[^>]*>)[\s\S]*?(<\/div>)/, "$1" + fe87_esc(model.label) + "$2");
  var block = '<div class="gd-px">' + fe87_esc(model.px) + '</div><div class="gd-chg fe87-chg ' + model.cls + '">' + fe87_esc(model.chg) + "</div>";
  if (model.spot) block += '<div class="fe87-spot">' + fe87_esc(model.spot) + "</div>";
  h = h.replace(/<div class="gd-px">[\s\S]*?<\/div>/, block);
  h = h.replace(/<div class="fe77-fut">(?!Futures high)[\s\S]*?<\/div>/g, "");
  var foot = '<div class="fe87-fut">' + fe87_esc(model.feet.fut) + '</div><div class="fe87-spot-src">' + fe87_esc(model.feet.spot) + '</div><div class="fe87-ai">' + fe87_esc(model.feet.ai) + "</div>";
  h = h.replace(/<div class="gd-asof">[\s\S]*?<\/div>/, '<div class="gd-asof">' + foot + "</div>");
  return h;
}
function fe87_heroDom() {
  var page = "";
  try { page = typeof pg === "string" ? pg : ""; } catch (e) { page = ""; }
  if (page && page !== "gold" && page !== "playbook") return;
  if (typeof document === "undefined") return;
  var hero = document.querySelector(".gd-hero");
  if (!hero) return;
  var model = fe87_heroModel();
  if (!model) return;
  var k = hero.querySelector(".gd-kicker");
  if (k && k.textContent !== model.label) k.textContent = model.label;
  var gd = hero.querySelector(".gd-px");
  if (gd) {
    var want = model.px + " ";
    var t = gd.firstChild;
    if (!t || t.nodeType !== 3) gd.insertBefore(document.createTextNode(want), gd.firstChild);
    else if (t.textContent !== want) t.textContent = want;
    var inner = gd.querySelector(".gd-chg");
    if (inner && inner.parentNode) inner.parentNode.removeChild(inner);
  }
  var ch = hero.querySelector(".fe87-chg");
  if (!ch && gd && gd.parentNode) {
    ch = document.createElement("div");
    ch.className = "gd-chg fe87-chg " + model.cls;
    gd.parentNode.insertBefore(ch, gd.nextSibling);
  }
  if (ch) {
    if (ch.textContent !== model.chg) ch.textContent = model.chg;
    ch.className = "gd-chg fe87-chg " + model.cls;
  }
  var extra = hero.querySelectorAll(".fe77-fut");
  for (var i = extra.length - 1; i >= 0; i--) {
    if (!/high|low/i.test(extra[i].textContent || "") && extra[i].parentNode) extra[i].parentNode.removeChild(extra[i]);
  }
  var spotEl = hero.querySelector(".fe87-spot");
  if (model.spot) {
    if (!spotEl) {
      spotEl = document.createElement("div");
      spotEl.className = "fe87-spot";
      var anchor = ch || gd;
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(spotEl, anchor.nextSibling);
    }
    if (spotEl.textContent !== model.spot) spotEl.textContent = model.spot;
  } else if (spotEl && spotEl.parentNode) spotEl.parentNode.removeChild(spotEl);
  var asof = hero.querySelector(".gd-asof");
  if (asof) {
    var html = '<div class="fe87-fut">' + fe87_esc(model.feet.fut) + '</div><div class="fe87-spot-src">' + fe87_esc(model.feet.spot) + '</div><div class="fe87-ai">' + fe87_esc(model.feet.ai) + "</div>";
    if (asof.getAttribute("data-fe87") !== html) {
      asof.innerHTML = html;
      asof.setAttribute("data-fe87", html);
    }
  }
}
function fe87_goldTile(tile, nowHm) {
  var b = null;
  try { b = fe83f_goldBits(); } catch (e) { b = null; }
  if (!b || b.kind !== "futures" || b.px == null) return;
  var px = fe87_pxText(b.px);
  var v = tile.querySelector(".bb1-v");
  var c = tile.querySelector(".bb1-c");
  if (v && c && c.parentNode === v && v.parentNode) v.parentNode.insertBefore(c, v.nextSibling);
  var label = tile.querySelector(".fe87-label");
  if (!label && v && v.parentNode) {
    label = document.createElement("div");
    label.className = "fe87-label";
    v.parentNode.insertBefore(label, v);
  }
  if (label && label.textContent !== "Gold futures (GC=F)") label.textContent = "Gold futures (GC=F)";
  if (v) {
    var node = v.firstChild;
    if (node && node.nodeType === 3) { if (node.textContent.replace(/\s+/g, "") !== px) node.textContent = px; }
    else if ((v.textContent || "").replace(/\s+/g, "") !== px) v.textContent = px;
  }
  var closed = fe87_isClosed("XAU");
  var day = "";
  try { day = (typeof fe86_day === "function" && fe86_day("XAU")) || ""; } catch (e2) { day = ""; }
  if (closed && !day) day = "Fri";
  var pct = b.pct == null ? "" : fe85_signed(b.pct, "%");
  var chg = fe87_chg(b.pts || "", pct, day, !closed);
  if (c && chg && c.textContent !== chg) c.textContent = chg;
  var meta = tile.querySelector(".bb1-meta");
  if (meta) {
    var line = fe87_macroMeta(fe87_stamp(fe87_sessionMs("XAU")), closed ? fe87_reopenPhrase("XAU") : "", closed, nowHm);
    if (line && meta.textContent !== line) meta.textContent = line;
  }
}
function fe87_otherTile(tile, tk, nowHm) {
  if (!fe87_isClosed(tk)) return;
  var meta = tile.querySelector(".bb1-meta");
  if (!meta) return;
  var line = fe87_macroMeta(fe87_stamp(fe87_sessionMs(tk)), fe87_reopenPhrase(tk), true, nowHm);
  if (line && meta.textContent !== line) meta.textContent = line;
}
function fe87_macro() {
  if (typeof document === "undefined") return;
  var tiles = document.querySelectorAll("[data-bb1-tile]");
  if (!tiles.length) return;
  var map = { gold: "XAU", dollar: "DXY", us10: "TNX", vix: "VIX", brent: "BRENT", wti: "WTI" };
  var nowHm = fe87_nowHm();
  for (var i = 0; i < tiles.length; i++) {
    var id = tiles[i].getAttribute("data-bb1-tile") || "";
    if (id === "gold") fe87_goldTile(tiles[i], nowHm);
    else if (map[id]) fe87_otherTile(tiles[i], map[id], nowHm);
  }
}
function fe87_srcLine(tk, pretty, closed) {
  var spec = null;
  try { spec = fe86_cmd(tk); } catch (e) { spec = null; }
  var label = spec ? spec.label : String(tk);
  var line = label + " " + pretty;
  if (!closed) return line + " \u00b7 delayed 10 min";
  var day = "";
  try { day = typeof fe86_day === "function" ? fe86_day(tk) : ""; } catch (e2) { day = ""; }
  line += " \u00b7 CLOSED" + (day ? " \u00b7 " + day : "");
  var stamp = fe87_stamp(fe87_sessionMs(tk));
  var nowHm = fe87_nowHm();
  if (stamp && (!nowHm || stamp.indexOf(nowHm) < 0)) line += " \u00b7 as of " + stamp;
  var reopen = fe87_reopenPhrase(tk);
  if (reopen) line += " \u00b7 " + reopen;
  return line;
}
function fe87_fixCard(el, tk) {
  if (!el || !fe87_cmdTk(tk)) return;
  var closed = fe87_isClosed(tk);
  var nowHm = fe87_nowHm();
  var badge = el.querySelector(".trust-stat");
  if (badge && closed && badge.textContent.indexOf("reopens") < 0) {
    var text = fe87_badge(true, fe87_reopenPhrase(tk));
    if (badge.textContent !== text) badge.textContent = text;
  }
  var rec = fe87_futRec(tk);
  var pretty = rec ? fe87_pxText(rec.p) : "";
  if (pretty) {
    var node = el.querySelector(".asset-price, .spine-px, .idx-card-px, .conv-px");
    if (node) {
      var cur = node.textContent || "";
      var want = (cur.indexOf("$") >= 0 || el.getAttribute("data-price-dollar") === "1") ? ("$" + pretty) : pretty;
      if (node.textContent !== want) node.textContent = want;
    } else if (el.getAttribute && el.getAttribute("data-fl") === tk && el.firstChild && el.firstChild.nodeType === 3) {
      var raw = el.firstChild.textContent || "";
      var want2 = raw.indexOf("$") >= 0 ? ("$" + pretty) : pretty;
      if (raw !== want2) el.firstChild.textContent = want2;
    }
    var src = el.querySelector(".spine-asof, .asof-tag, .fe87-futsrc");
    var line = fe87_srcLine(tk, pretty, closed);
    if (!src) {
      src = document.createElement("div");
      src.className = "fe87-futsrc";
      el.appendChild(src);
    }
    var shown = fe87_dropNow(line, nowHm, fe87_stamp(fe87_sessionMs(tk)));
    if (src.textContent !== shown) src.textContent = shown;
    var spot = fe87_spotMem[tk];
    if (spot > 0 && Math.abs(spot - Number(rec.p)) >= 0.005) {
      var note = el.querySelector(".fe87-spotpx");
      if (!note) {
        note = document.createElement("div");
        note.className = "fe87-spotpx";
        el.appendChild(note);
      }
      var spotLine = (tk === "SLV" ? "SLV ETF $" : "spot $") + fe87_pxText(spot);
      if (note.textContent !== spotLine) note.textContent = spotLine;
    }
  }
  var bits = el.querySelectorAll(".asof-tag, .spine-asof, .bb1-meta, .fe87-futsrc, .trust-stat");
  var stamp = fe87_stamp(fe87_sessionMs(tk));
  for (var i = 0; i < bits.length; i++) {
    if (!closed) continue;
    var next = fe87_subClosed(fe87_dropNow(bits[i].textContent || "", nowHm, stamp));
    if (/delay/i.test(bits[i].textContent || "") && bits[i].classList.contains("trust-stat")) next = fe87_badge(true, fe87_reopenPhrase(tk));
    if (next && next !== bits[i].textContent) bits[i].textContent = next;
  }
}
function fe87_cards() {
  if (typeof document === "undefined") return;
  var keys = ["WTI", "BRENT", "COPPER", "PALLADIUM", "NG", "SLV", "PLAT"];
  var i, j, list;
  for (i = 0; i < keys.length; i++) {
    try { list = document.querySelectorAll("[data-price-card='" + keys[i] + "'], [data-fl='" + keys[i] + "']"); } catch (e) { list = []; }
    for (j = 0; j < list.length; j++) fe87_fixCard(list[j], keys[i]);
  }
  var spines = document.querySelectorAll(".spine-cell");
  for (i = 0; i < spines.length; i++) {
    var idn = spines[i].querySelector(".spine-tk");
    var id = idn ? String(idn.textContent || "").trim() : "";
    if (fe87_cmdTk(id)) fe87_fixCard(spines[i], id);
  }
  var heats = document.querySelectorAll(".heat-tile");
  if (heats.length && heats.length < 80) {
    for (i = 0; i < heats.length; i++) {
      var oc = heats[i].getAttribute("onclick") || "";
      var m = oc.match(/openA\('([^']+)'\)/);
      if (m && fe87_cmdTk(m[1])) fe87_fixCard(heats[i], m[1]);
    }
  }
}
function fe87_intelDom() {
  if (typeof document === "undefined") return;
  var bar = document.getElementById("siteIntelBar");
  if (!bar) return;
  var date = fe87_ukDate(Date.now());
  var chunks = bar.querySelectorAll(".si-bar-chunk");
  for (var i = 0; i < chunks.length; i++) {
    var next = fe87_intelShort(chunks[i].textContent, date);
    if (next && next !== chunks[i].textContent) chunks[i].textContent = next;
  }
  try {
    if (window.innerWidth <= 430) {
      var wrap = bar.querySelector(".si-bar-scroll-wrap");
      if (wrap) wrap.classList.remove("si-scroll-on");
    }
  } catch (e) {}
}
function fe87_tick() {
  var now = Date.now();
  if (now - fe87_at < 1000) return;
  fe87_at = now;
  var page = "";
  try { page = typeof pg === "string" ? pg : ""; } catch (e) { page = ""; }
  if (page === "gold" || page === "playbook") { try { fe87_heroDom(); } catch (e1) {} }
  if (!page || page === "home") { try { fe87_macro(); } catch (e2) {} }
  if (page === "dash" || page === "brief" || page === "mkt" || page === "sig" || page === "lab") {
    try { fe87_cards(); } catch (e3) {}
  }
}
function fe87_fixSpineHtml(html) {
  var s = String(html || "");
  var nowHm = fe87_nowHm();
  var keys = ["WTI", "BRENT", "COPPER", "PALLADIUM", "NG", "SLV", "PLAT", "XAU"];
  for (var i = 0; i < keys.length; i++) {
    var tk = keys[i];
    if (!fe87_isClosed(tk)) continue;
    var token = '<span class="spine-tk">' + tk + "</span>";
    var at = s.indexOf(token);
    if (at < 0) continue;
    var from = s.lastIndexOf("<button", at);
    var to = s.indexOf("</button>", at);
    if (from < 0 || to < 0) continue;
    var btn = s.slice(from, to);
    var next = btn;
    if (fe87_cmdTk(tk)) {
      var rec = fe87_futRec(tk);
      var pretty = rec ? fe87_pxText(rec.p) : "";
      var line = fe87_srcLine(tk, pretty, true);
      if (pretty) next = next.replace(/(<span class="spine-px">)[\s\S]*?(<\/span>)/, "$1" + fe87_esc(pretty) + "$2");
      next = next.replace(/(<span class="spine-asof">)[\s\S]*?(<\/span>)/, "$1" + fe87_esc(line) + "$2");
    }
    if (nowHm && next.indexOf(nowHm) >= 0) next = fe87_dropNow(next, nowHm, fe87_stamp(fe87_sessionMs(tk)));
    if (fe87_cmdTk(tk)) next = fe87_subClosed(next);
    if (next !== btn) s = s.slice(0, from) + next + s.slice(to);
  }
  return s;
}
try { fe87_css(); } catch (eCss) {}
try {
  var fe87_hrs0 = fe73_hours;
  fe73_hours = function (tk) {
    try { if (typeof fe86_cmd === "function" && fe86_cmd(tk)) return null; } catch (e) {}
    return fe87_hrs0.apply(this, arguments);
  };
  try { if (_rt51NextC) delete _rt51NextC.COPPER; } catch (e2) {}
  try { if (fe85_openMap && fe85_openMap.delete) fe85_openMap.delete("COPPER"); } catch (e3) {}
} catch (eHrs) {}
try {
  var fe87_extra = [
    { tk: "SLV", lbl: "Silver" },
    { tk: "PLAT", lbl: "Platinum" },
    { tk: "PALLADIUM", lbl: "Palladium" },
    { tk: "BRENT", lbl: "Brent" }
  ];
  var fe87_atSpine = 0, fe87_si, fe87_sj, fe87_sk, fe87_have;
  for (fe87_si = 0; fe87_si < DESK_SPINE.length; fe87_si++) if (DESK_SPINE[fe87_si].tk === "COPPER") fe87_atSpine = fe87_si + 1;
  for (fe87_sj = fe87_extra.length - 1; fe87_sj >= 0; fe87_sj--) {
    fe87_have = false;
    for (fe87_sk = 0; fe87_sk < DESK_SPINE.length; fe87_sk++) if (DESK_SPINE[fe87_sk].tk === fe87_extra[fe87_sj].tk) fe87_have = true;
    if (!fe87_have) DESK_SPINE.splice(fe87_atSpine, 0, fe87_extra[fe87_sj]);
  }
} catch (eSpine) {}
try {
  var fe87_gs0 = _renderGoldSurface;
  _renderGoldSurface = function () {
    var h = fe87_gs0.apply(this, arguments);
    try { h = fe87_heroHtml(h); } catch (e) {}
    return h;
  };
} catch (eGs) {}
try {
  var fe87_rt0 = _rtPaint;
  _rtPaint = function () {
    var r = fe87_rt0.apply(this, arguments);
    try { fe87_heroDom(); } catch (e) {}
    return r;
  };
} catch (eRt) {}
try {
  var fe87_glance0 = fe85_paintGlance;
  fe85_paintGlance = function () {
    try { fe87_glance0.apply(this, arguments); } catch (e) {}
    try { fe87_macro(); } catch (e2) {}
  };
} catch (eGl) {}
try {
  var fe87_pass0 = fe85_pass;
  fe85_pass = function () {
    var r;
    try { r = fe87_pass0.apply(this, arguments); } catch (e) { r = undefined; }
    try { fe87_tick(); } catch (e2) {}
    return r;
  };
} catch (ePass) {}
try {
  var fe87_bar0 = _paintSiteIntelBar;
  _paintSiteIntelBar = function () {
    var r = fe87_bar0.apply(this, arguments);
    try { fe87_intelDom(); } catch (e) {}
    return r;
  };
} catch (eBar) {}
try {
  var fe87_sync0 = _syncIntelScroll;
  _syncIntelScroll = function () {
    try {
      if (window.innerWidth <= 430) {
        var wrap = document.querySelector("#siteIntelBar .si-bar-scroll-wrap");
        if (wrap) wrap.classList.remove("si-scroll-on");
        return;
      }
    } catch (e) {}
    return fe87_sync0.apply(this, arguments);
  };
} catch (eSync) {}
try {
  var fe87_stat0 = stat;
  stat = function (tk) {
    var html = "";
    try { html = fe87_stat0.apply(this, arguments) || ""; } catch (e) { html = ""; }
    var id = fe87_id(tk);
    if (!fe87_cmdTk(id) || !fe87_isClosed(id) || html.indexOf("reopens") >= 0) return html;
    var text = fe87_badge(true, fe87_reopenPhrase(id));
    return html.replace(/>([^<]*)</, ">" + fe87_esc(text) + "<");
  };
} catch (eStat) {}
try {
  var fe87_as0 = asOfTag;
  asOfTag = function (tk) {
    var html = "";
    try { html = fe87_as0.apply(this, arguments) || ""; } catch (e) { html = ""; }
    var id = fe87_id(tk);
    if (!fe87_isClosed(id)) return html;
    var nowHm = fe87_nowHm();
    var stamp = fe87_stamp(fe87_sessionMs(id));
    var plain = html.replace(/<[^>]+>/g, "");
    var next = fe87_dropNow(plain, nowHm, stamp);
    if (fe87_cmdTk(id)) {
      next = fe87_subClosed(next);
      var rec = fe87_futRec(id);
      if (rec && rec.p > 0) {
        var pretty = fe87_pxText(rec.p);
        if (pretty && next.indexOf(pretty) < 0) {
          var spec = null;
          try { spec = fe86_cmd(id); } catch (e2) { spec = null; }
          var label = spec ? spec.label : id;
          next = next.indexOf(label) >= 0 ? next.replace(label, label + " " + pretty) : (label + " " + pretty + (next ? " \u00b7 " + next : ""));
        }
      }
    }
    if (next === plain) return html;
    return html.replace(/>([^<]*)</, ">" + fe87_esc(next) + "<");
  };
} catch (eAs) {}
try {
  var fe87_spine0 = _renderDeskSpine;
  _renderDeskSpine = function () {
    var h = "";
    try { h = fe87_spine0.apply(this, arguments) || ""; } catch (e) { h = ""; }
    try { h = fe87_fixSpineHtml(h); } catch (e2) {}
    return h;
  };
} catch (eSp2) {}
try {
  var fe87_ev0 = _signalEvidence;
  _signalEvidence = function (signal) {
    var ev = fe87_ev0.apply(this, arguments);
    try {
      var tk = fe87_id((signal && signal.tk) || (ev && ev.tk));
      if (ev && fe87_isClosed(tk) && fe87_cmdTk(tk)) {
        ev.status = fe87_badge(true, fe87_reopenPhrase(tk));
        var nowHm = fe87_nowHm();
        if (nowHm && String(ev.asOf || "").indexOf(nowHm) >= 0) ev.asOf = fe87_stamp(fe87_sessionMs(tk)) || "\u2014";
        var rec = fe87_futRec(tk);
        if (rec && rec.p > 0) ev.price = fe87_pxText(rec.p);
      }
    } catch (e) {}
    return ev;
  };
} catch (eEv) {}
try {
  var fe87_sub0 = _rt43SubText;
  _rt43SubText = function (tk) {
    var t = "";
    try { t = fe87_sub0.apply(this, arguments) || ""; } catch (e) { t = ""; }
    var id = fe87_id(tk);
    if (fe87_cmdTk(id) && fe87_isClosed(id)) t = fe87_subClosed(t);
    return t;
  };
} catch (eSub) {}
try {
  var fe87_spot0 = _rt43ApplySpot;
  _rt43ApplySpot = function (tk, p) {
    if (fe87_cmdTk(tk) && Number(p) > 0) fe87_spotMem[tk] = Number(p);
    var r = fe87_spot0.apply(this, arguments);
    try { fe87_applyFut(tk); } catch (e) {}
    return r;
  };
} catch (eSpot) {}
try {
  var fe87_keep0 = _rt43KeepFut;
  _rt43KeepFut = function (tk) {
    var r = fe87_keep0.apply(this, arguments);
    try { fe87_applyFut(tk); } catch (e) {}
    return r;
  };
} catch (eKeep) {}
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
    pure = app_text.split("// fe87-pure-begin", 1)[1].split("// fe87-pure-end", 1)[0]
    src = pure + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
var book = fe87_book("4,007.90", "3,996.90", "-52.50", "-1.29%", "Fri", false);
assert(book.px === "$4,007.90" && book.chg === "-52.50 (-1.29%) Fri" && book.spot === "Spot $3,996.90" && book.ok, "book " + JSON.stringify(book));
assert(book.spot.indexOf("%") < 0 && book.chg.indexOf("3,996") < 0, "spot not in the change");
assert(fe87_chg("-51.70", "-1.29%", "Fri", false) === "-51.70 (-1.29%) Fri", "fixture points");
assert(fe87_chg("-52.50", "-1.29%", "Fri", true) === "-52.50 (-1.29%) today", "open says today");
var feet = fe87_feet("Fri 21:59 UK", "", "14:36 UK", "reopens Sun 22:00 UK", true);
assert(feet.fut.indexOf("Fri 21:59 UK") >= 0 && feet.fut.indexOf("14:36") < 0, "fut stamp");
assert(feet.fut.indexOf("delayed") < 0 && feet.ai.indexOf("14:36") >= 0, "ai only");
assert(fe87_aiInPrice(feet, "14:36") === false, "ai not in price");
assert(!fe87_jargon(feet.fut) && !fe87_jargon(feet.spot) && !fe87_jargon(feet.ai), "jargon");
var openFeet = fe87_feet("", "", "", "", false);
assert(openFeet.fut.indexOf("delayed 10 min") >= 0, "open delay");
var meta = fe87_macroMeta("Fri 21:59 UK", "reopens Sun 22:00 UK", true, "14:36");
assert(meta.indexOf("Fri 21:59 UK") >= 0 && meta.indexOf("14:36") < 0 && meta.indexOf("market closed") >= 0, "macro " + meta);
assert(fe87_badge(true, "reopens Sun 22:00 UK") === "CLOSED \u00b7 reopens Sun 22:00 UK", "badge");
assert(fe87_badge(true, "").indexOf("delayed") < 0 && fe87_badge(true, "").indexOf("Sunday evening") >= 0, "badge fallback");
assert(fe87_badge(false, "reopens Sun 22:00 UK") === "", "open badge empty");
var dropped = fe87_dropNow("Copper futures (HG=F) \u00b7 as of 14:36 UK", "14:36", "Fri 21:59 UK");
assert(dropped.indexOf("14:36") < 0 && dropped.indexOf("Fri 21:59 UK") >= 0 && dropped.indexOf("UK UK") < 0, "drop now " + dropped);
var dropped2 = fe87_dropNow("as of 14:36 UK</span> as of 14:36 UK", "14:36", "Fri 21:59 UK");
assert(dropped2.indexOf("UK UK") < 0 && dropped2.indexOf("14:36") < 0, "drop both " + dropped2);
var dropped3 = fe87_dropNow("WTI futures \u00b7 as of 14:36 UK", "14:36", "");
assert(dropped3.indexOf("14:36") < 0 && dropped3.indexOf("as of") < 0, "drop empty " + dropped3);
var intel = fe87_intelShort("1 of 13 markets trading now, 12 closed (Sun 25 Oct, 14:36 UK)", "");
assert(intel === "1 of 13 markets open \u00b7 12 closed \u00b7 Sun 25 Oct", "intel " + intel);
assert(fe87_samePx("$6.53", "6.53") && fe87_samePx("$1,562.40", "1562.40") && !fe87_samePx("$6.53", "6.51"), "same px");
assert(fe87_subClosed("Futures 6.51 \u00b7 delayed 10 min").indexOf("delayed") < 0, "sub closed");
console.log("fe87 unit ok");
"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe87 tests failed\n" + test.stdout + test.stderr)
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
    if index.count('app.js?v=chat86"') != 1:
        die("cache bust anchor missing")
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count(REFUSE_MARKER) != 1:
        die("refuse marker")
    if app.count("function fe87_book(") != 1 or app.count("function fe87_intelShort(") != 1:
        die("pure defs")
    if "function fe84_dtfShim" not in app or not app.startswith("(function fe84_dtfShim(){"):
        die("shim moved")
    if app.count(NEED_MARKER) != 1:
        die("rt62i marker drifted")
    index = index.replace('app.js?v=chat86"', 'app.js?v=chat87"', 1)
    if index.count('app.js?v=chat87"') != 1 or "chat86" in index:
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
