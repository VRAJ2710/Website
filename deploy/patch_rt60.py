#!/usr/bin/env python3
"""rt60 client patch: chat73 -> chat74. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "25b1632712ec576378e42203850a1d9b"
EXPECT_INDEX_MD5 = "a2f7cf6fef50a39d5b1ba2c17112cbaa"
NEED_MARKER = "// ── rt59c ──"
REFUSE_MARKER = "// ── rt60 ──"

BLOCK = r'''
// ── rt60 ──
// fe73-pure-begin
function fe73_ccy(tk, hint) {
  var h = hint == null ? "" : String(hint);
  var t = String(tk || "");
  if (/\.L$/i.test(t)) return "GBp";
  if (/\.HK$/i.test(t)) return "HKD";
  if (/\.T$/i.test(t)) return "JPY";
  if (/\.AX$/i.test(t)) return "AUD";
  if (/\.KS$/i.test(t)) return "KRW";
  if (/\.NS$/i.test(t)) return "INR";
  if (/\.(DE|PA)$/i.test(t)) return "EUR";
  if (/=X$/i.test(t) || /^[A-Z]{6}$/.test(t)) return "FX";
  if (/^\^/.test(t) || /^(FTSE|DAX|CAC|N225|HSI|NSEI|ASX200|KOSPI|SPX|NDX|DJI|VIX)$/i.test(t)) return "PTS";
  if (h) return h;
  try { if (typeof fe66_ccy === "function") return fe66_ccy(t); } catch (e) {}
  return "USD";
}
function fe73_prev(px, prev, ccy) {
  var a = Number(px), b = Number(prev);
  if (!(a > 0) || !(b > 0)) return b;
  if (ccy === "GBp" || ccy === "GBX") {
    var r = a / b;
    if (r >= 50 && r <= 200) return b * 100;
    if (r >= 0.005 && r <= 0.02) return b / 100;
  }
  return b;
}
function fe73_absText(ccy, n) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  var sign = v < 0 ? "-" : (v > 0 ? "+" : "");
  var a = Math.abs(v);
  var whole = ccy === "JPY" || ccy === "KRW";
  var num = whole ? String(Math.round(a)) : ((ccy === "FX" && a < 1) ? a.toFixed(4) : a.toFixed(2));
  if (ccy === "GBp" || ccy === "GBX") return sign + num + "p";
  if (ccy === "GBP") return sign + "\u00a3" + num;
  if (ccy === "HKD") return sign + "HK$" + num;
  if (ccy === "JPY") return sign + "\u00a5" + num;
  if (ccy === "EUR") return sign + "\u20ac" + num;
  if (ccy === "KRW") return sign + "\u20a9" + num;
  if (ccy === "AUD") return sign + "A$" + num;
  if (ccy === "INR") return sign + "\u20b9" + num;
  if (ccy === "FX" || ccy === "PTS") return sign + num;
  return sign + "$" + num;
}
function fe73_pctText(n) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  var body = Math.abs(v).toFixed(2);
  if (v > 0) return "+" + body + "%";
  if (v < 0) return "-" + body + "%";
  return "+0.00%";
}
function fe73_ukDate(v) {
  var s = String(v || "").trim();
  var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return s;
  var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var mon = months[Number(m[2]) - 1] || m[2];
  return String(Number(m[3])) + " " + mon + " " + m[1];
}
function fe73_rowDate(row) {
  var s = String((row && (row.transactionDate || row.filingDate)) || "");
  var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? m[0] : "";
}
function fe73_windowLabel(rows) {
  var dates = [];
  (rows || []).forEach(function (r) {
    var d = fe73_rowDate(r);
    if (d) dates.push(d);
  });
  if (!dates.length) return "";
  dates.sort();
  var a = fe73_ukDate(dates[0]);
  var b = fe73_ukDate(dates[dates.length - 1]);
  return a === b ? a : (a + " \u2013 " + b);
}
function fe73_textDates(s) {
  return String(s || "").replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, function (_a, y, mo, d) {
    return fe73_ukDate(y + "-" + mo + "-" + d);
  });
}
function fe73_showDate(uk, iso) {
  var u = uk == null ? "" : String(uk).trim();
  if (u) return /^\d{4}-\d{2}-\d{2}/.test(u) ? fe73_ukDate(u) : u;
  var s = iso == null ? "" : String(iso).trim();
  if (!s) return "";
  return /^\d{4}-\d{2}-\d{2}/.test(s) ? fe73_ukDate(s) : s;
}
function fe73_rowWhen(row) {
  row = row || {};
  var tx = fe73_showDate(row.transactionDateUk, row.transactionDate);
  var fl = fe73_showDate(row.filingDateUk, row.filingDate);
  if (tx && fl && tx !== fl) return tx + " \u00b7 filed " + fl;
  return tx || fl || "";
}
function fe73_houseWhen(item) {
  item = item || {};
  var filed = fe73_showDate(item.filingDateUk, item.filingDate);
  var bits = [];
  (item.trades || []).forEach(function (tr) {
    var d = fe73_showDate(tr && tr.dateUk, tr && (tr.date || tr.transactionDate));
    if (d) bits.push(d);
  });
  if (!bits.length) return filed;
  return filed ? (filed + " \u00b7 " + bits.join(", ")) : bits.join(", ");
}
function fe73_spanLabel(meta, rows) {
  meta = meta || {};
  var span = meta.span;
  if (span && span.label) return fe73_textDates(String(span.label));
  if (span && (span.fromUk || span.toUk || span.from || span.to)) {
    var a = fe73_showDate(span.fromUk, span.from);
    var b = fe73_showDate(span.toUk, span.to);
    if (a && b) return a === b ? a : (a + " \u2013 " + b);
    if (a || b) return a || b;
  }
  var win = meta.window;
  if (win && win.label) return fe73_textDates(String(win.label));
  return fe73_windowLabel(rows || []);
}
function fe73_form4Note() {
  return "Insider trades: available for US-listed shares (SEC Form 4)";
}
function fe73_form4(tk, cat) {
  var t = String(tk || "").trim().toUpperCase();
  if (!t) return false;
  if (/\.(HK|L|T|AX|KS|NS|DE|PA|TO|SS|SZ|TW)$/.test(t)) return false;
  if (/=X$/.test(t) || /=F$/.test(t) || /^\^/.test(t)) return false;
  if (/^(SPX|DJIA|IXIC|FTSE|DAX|CAC|N225|HSI|NSEI|ASX200|KOSPI|VIX|RUT|STOXX50|DXY|TNX)$/.test(t)) return false;
  if (/^[A-Z]{6}$/.test(t) && /USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD/.test(t)) return false;
  var tapeCry = " BTC ETH SOL XRP DOGE ADA AVAX LINK DOT LTC UNI POL NEAR ALGO HBAR TON BCH XLM FIL APT SUI SHIB PEPE ATOM INJ ";
  var tapeCmd = " XAU WTI SLV NG COFFEE PLAT COCOA OJ LUMBER PALLADIUM COPPER WHEAT CORN BRENT ";
  if (tapeCry.indexOf(" " + t + " ") >= 0 || tapeCmd.indexOf(" " + t + " ") >= 0) return false;
  var c = String(cat || "").toLowerCase();
  if (c === "cry" || c === "crypto" || c === "cmd" || c === "fx" || c === "fut" || c.indexOf("commod") === 0) return false;
  return true;
}
function fe73_move(o) {
  o = o || {};
  var tk = o.tk || "";
  var ccy = fe73_ccy(tk, o.ccy);
  var px = Number(o.px);
  var prev = fe73_prev(px, o.prev, ccy);
  var absN = null, pctN = null;
  if (isFinite(px) && isFinite(prev) && prev !== 0) {
    absN = px - prev;
    pctN = (absN / Math.abs(prev)) * 100;
  } else if (isFinite(px) && px > 0 && o.c != null && isFinite(Number(o.c)) && Number(o.c) !== 0) {
    var implied = px / (1 + Number(o.c) / 100);
    implied = fe73_prev(px, implied, ccy);
    if (isFinite(implied) && implied !== 0) {
      absN = px - implied;
      pctN = (absN / Math.abs(implied)) * 100;
    }
  } else if (o.c != null && isFinite(Number(o.c))) {
    pctN = Number(o.c);
  }
  var open = !(o.open === false || o.open === 0);
  var day = "";
  if (!open && o.lastWd && String(o.lastWd) !== "today") day = String(o.lastWd);
  var abs = absN == null ? "" : fe73_absText(ccy, absN);
  var pct = fe73_pctText(pctN);
  var arrow = "";
  var dir = absN == null ? pctN : absN;
  if (dir > 0) arrow = "\u2191 ";
  else if (dir < 0) arrow = "\u2193 ";
  var core = "\u2014";
  if (abs && pct) core = arrow + abs + " (" + pct + ")";
  else if (abs) core = arrow + abs;
  else if (pct) core = arrow + pct;
  return { abs: abs, pct: pct, day: day, line: core + (day ? " " + day : ""), ccy: ccy };
}
// fe73-pure-end

function fe73_hours(tk) {
  var t = String(tk || "").toUpperCase();
  var idx = {
    "^FTSE": ["Europe/London", 480, 990], "FTSE": ["Europe/London", 480, 990],
    "^GDAXI": ["Europe/Berlin", 540, 1050], "^FCHI": ["Europe/Paris", 540, 1050],
    "^N225": ["Asia/Tokyo", 540, 930], "^HSI": ["Asia/Hong_Kong", 570, 960],
    "^NSEI": ["Asia/Kolkata", 555, 930], "^AXJO": ["Australia/Sydney", 600, 960],
    "^KS11": ["Asia/Seoul", 540, 930], "^GSPC": ["America/New_York", 570, 960],
    "^DJI": ["America/New_York", 570, 960], "^IXIC": ["America/New_York", 570, 960]
  };
  if (idx[t]) return { tz: idx[t][0], o: idx[t][1], c: idx[t][2] };
  if (/\.L$/.test(t)) return { tz: "Europe/London", o: 480, c: 990 };
  if (/\.HK$/.test(t)) return { tz: "Asia/Hong_Kong", o: 570, c: 960, lunch: [720, 780] };
  if (/\.T$/.test(t)) return { tz: "Asia/Tokyo", o: 540, c: 930, lunch: [690, 750] };
  if (/\.AX$/.test(t)) return { tz: "Australia/Sydney", o: 600, c: 960 };
  if (/\.KS$/.test(t)) return { tz: "Asia/Seoul", o: 540, c: 930 };
  if (/\.NS$/.test(t)) return { tz: "Asia/Kolkata", o: 555, c: 930 };
  if (/\.DE$/.test(t)) return { tz: "Europe/Berlin", o: 540, c: 1050 };
  if (/\.PA$/.test(t)) return { tz: "Europe/Paris", o: 540, c: 1050 };
  if (/=X$/.test(t) || /^[A-Z]{6}$/.test(t)) return { fx: true };
  return null;
}
function fe73_num(v) {
  var n = Number(v);
  return isFinite(n) ? n : null;
}
function fe73_px(tk, d) {
  var n = d ? fe73_num(d.p) : null;
  if (n != null && n > 0) return n;
  try { if (typeof P !== "undefined" && P[tk]) { n = fe73_num(P[tk].p); if (n != null && n > 0) return n; } } catch (e) {}
  try { if (typeof fp === "function") { var f = fp(tk); n = f ? fe73_num(f.p) : null; if (n != null && n > 0) return n; } } catch (e2) {}
  return null;
}
function fe73_prevOf(tk, d) {
  var n = null;
  if (d && d.prev != null) n = fe73_num(d.prev);
  if (n != null && n > 0) return n;
  try { if (typeof BASE !== "undefined" && BASE[tk]) { n = fe73_num(BASE[tk].p); if (n != null && n > 0) return n; } } catch (e) {}
  return null;
}
function fe73_chgLine(tk, d, na) {
  try { var lunch = typeof fe66b_line === "function" ? fe66b_line(tk) : ""; if (lunch) return lunch; } catch (e0) {}
  var venueOpen = false;
  try { venueOpen = typeof _rt18MarketOpen === "function" && !!_rt18MarketOpen(tk); } catch (e1) {}
  var closed = false;
  try { closed = typeof fe66_closedQuote === "function" && fe66_closedQuote(tk, d); } catch (e2) {}
  if (venueOpen) closed = false;
  if (na && !closed) return "awaiting feed";
  var px = fe73_px(tk, d);
  var prev = fe73_prevOf(tk, d);
  var ccy = "";
  try { ccy = (d && (d.currency || d.ccy)) || ""; } catch (e3) {}
  var c = null;
  try {
    if (d && d.c != null) c = fe73_num(d.c);
    else if (typeof P !== "undefined" && P[tk]) c = fe73_num(P[tk].c);
  } catch (e4) {}
  var lastWd = "";
  if (!venueOpen) {
    try { lastWd = typeof _rt26Day === "function" ? (_rt26Day(tk) || "") : ""; } catch (e5) { lastWd = ""; }
  }
  var moved = fe73_move({ tk: tk, px: px, prev: prev, c: c, ccy: ccy, open: venueOpen, lastWd: lastWd });
  if (!moved.line || moved.line === "\u2014") return closed ? "Last close" : "\u2014";
  if (closed) {
    var note = "";
    try { note = typeof fe66_note === "function" ? fe66_note(tk) : ""; } catch (e6) {}
    return note ? moved.line + " \u00b7 " + note : moved.line;
  }
  return moved.line;
}
function fe73_dates(html) {
  return fe73_textDates(html);
}
function fe73_viewRow(row) {
  if (!row || typeof row !== "object") return row;
  var copy = {};
  var k;
  for (k in row) if (Object.prototype.hasOwnProperty.call(row, k)) copy[k] = row[k];
  var when = fe73_rowWhen(row);
  if (when) { copy.transactionDate = when; copy.filingDate = ""; }
  return copy;
}
function fe73_viewHouse(house) {
  if (!house || !Array.isArray(house.items)) return house;
  var copy = {};
  var k;
  for (k in house) if (Object.prototype.hasOwnProperty.call(house, k)) copy[k] = house[k];
  copy.items = house.items.map(function (item) {
    var it = {};
    var key;
    for (key in item) if (Object.prototype.hasOwnProperty.call(item, key)) it[key] = item[key];
    it.filingDate = fe73_houseWhen(item);
    it.filingDateUk = "";
    return it;
  });
  return copy;
}
function fe73_viewData(data) {
  if (!data || typeof data !== "object") return data;
  var copy = {};
  var k;
  for (k in data) if (Object.prototype.hasOwnProperty.call(data, k)) copy[k] = data[k];
  if (Array.isArray(data.insider)) copy.insider = data.insider.map(fe73_viewRow);
  if (data.house) copy.house = fe73_viewHouse(data.house);
  return copy;
}
function fe73_person() {
  return '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 19.2c1.4-3 3.6-4.5 6.5-4.5s5.1 1.5 6.5 4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
}
function fe73_sheetHtml() {
  var who = fe71_who();
  var pins = [["home", "Home"], ["brief", "Brief"], ["playbook", "Playbook"], ["gold", "Gold"], ["ask", "Ask"]];
  var pinHtml = pins.map(function (p) { return fe71_tile(p[0], p[1], "pin"); }).join("");
  var groups = fe71_groups().map(function (gr) {
    return '<section class="fe71-grp" data-fe71-group="' + fe71_esc(gr.g) + '"><h3>' + fe71_esc(gr.g) + '</h3><div class="fe71-grid">' +
      gr.items.map(function (it) { return fe71_tile(it[0], it[1], gr.g); }).join("") +
      "</div></section>";
  }).join("");
  var ident = who.guest
    ? '<div class="fe71-id"><span class="fe71-ava" aria-hidden="true">' + fe73_person() + '</span><div><div class="fe71-name">Guest</div><div class="fe71-planrow"><button type="button" class="fe71-auth" data-fe73-auth="/__auth/login">Sign in</button><button type="button" class="fe71-auth" data-fe73-auth="/__auth/register">Create free account</button></div></div></div>'
    : '<div class="fe71-id"><span class="fe71-ava" aria-hidden="true">' + fe71_esc(who.initials) + '</span><div><div class="fe71-name">' + fe71_esc(who.name) + '</div><div class="fe71-planrow"><span class="fe71-plan">' + fe71_esc(who.plan || "Free") + "</span>" +
      (who.admin ? '<span class="fe71-admin">Admin</span>' : "") + "</div></div></div>";
  var line = fe71_sessionLine();
  return '<div class="more-nav-scrim" data-fe71-scrim="1"></div>' +
    '<div class="more-nav-panel" role="document">' +
    '<div class="fe71-swipe"><div class="fe71-grab" aria-hidden="true"></div>' +
    '<div class="fe71-head"><h2 id="fe71-title">Sections</h2>' + ident +
    '<button type="button" class="more-nav-x fe71-x" data-fe71-x="1" aria-label="Close all sections">\u00d7</button></div>' +
    (line ? '<p class="fe71-session">' + fe71_esc(line) + "</p>" : "") +
    "</div>" +
    '<label class="fe71-search"><input class="fe71-find" type="search" enterkeyhint="search" placeholder="Find a section" aria-label="Find a section" autocomplete="off"></label>' +
    '<div class="fe71-pin" aria-label="Home, Brief, Playbook, Gold and Ask">' + pinHtml + "</div>" +
    groups +
    '<p class="fe71-empty" hidden>Nothing matches. Try Heatmap, Gold or Brief.</p>' +
    "</div>";
}
function fe73_swipe(panel) {
  var zone = panel.querySelector(".fe71-swipe");
  if (!zone) return;
  var y0 = 0, dy = 0, drag = false;
  zone.addEventListener("pointerdown", function (e) {
    if (e.target.closest("button, a, input, label")) return;
    drag = true; y0 = e.clientY; dy = 0;
    panel.classList.add("fe73-drag");
    try { document.body.style.userSelect = "none"; } catch (err0) {}
    if (fe71_motion()) panel.style.transition = "none";
    try { zone.setPointerCapture(e.pointerId); } catch (err) {}
  });
  zone.addEventListener("pointermove", function (e) {
    if (!drag) return;
    dy = e.clientY - y0;
    if (dy < 0) dy = 0;
    if (fe71_motion()) panel.style.transform = "translate3d(0," + dy + "px,0)";
  });
  function fe73_swipeEnd() {
    if (!drag) return;
    drag = false;
    panel.classList.remove("fe73-drag");
    try { document.body.style.userSelect = ""; } catch (err1) {}
    panel.style.transition = "";
    panel.style.transform = "";
    if (dy > 72) closeMoreNav();
  }
  zone.addEventListener("pointerup", fe73_swipeEnd);
  zone.addEventListener("pointercancel", fe73_swipeEnd);
}
function fe73_css() {
  if (document.getElementById("fe73-css")) return;
  var st = document.createElement("style");
  st.id = "fe73-css";
  st.textContent = [
    "html body.fe70-home #homeOv,html body.fe70-home #homeOv.term-overlay,html body.fe70-home #homeOv.front-door-overlay{position:fixed!important;inset:auto 0 0 0!important;top:var(--desk-chrome,92px)!important;left:0!important;right:0!important;bottom:0!important;width:auto!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:auto!important;z-index:35!important}",
    "@media (min-width:768px){html body.fe70-home #homeOv,html body.fe70-home #homeOv.term-overlay,html body.fe70-home #homeOv.front-door-overlay{left:var(--sidebar-w,172px)!important}}",
    "html body.fe70-home #homeOv .term-overlay-card,html body.fe70-home #homeOv .term-overlay-body{height:auto!important;max-height:none!important;overflow:visible!important}",
    "body.fe70-home .tape,body.fe70-home:not(.app-booting) .tape{display:block!important;visibility:visible!important;max-width:100%;position:sticky;top:0;z-index:80}",
    ".tape,.tape-track{max-width:100%}",
    "html body.fe68-lenses .panel.p-expanded{position:fixed!important;inset:auto 0 0 auto!important;top:var(--desk-chrome,92px)!important;left:var(--sidebar-w,172px)!important;right:0!important;bottom:0!important;width:auto!important;height:auto!important;min-height:0!important;margin:0!important;z-index:45!important;overflow:auto!important}",
    "@media (max-width:767px){html body.fe68-lenses .panel.p-expanded{left:0!important;top:48px!important}[data-fe73-sub]{white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;max-width:100%}[data-fe73-back]{flex:none;min-width:44px;min-height:44px;margin-right:8px}}",
    "@media (max-width:767px){.hdr{display:flex!important;flex-wrap:nowrap!important;align-items:center;max-width:100%!important;overflow:hidden;min-width:0}.hdr .logo-text,.hdr .clk,.hdr .clk-d,.hdr .info-btn,.hdr .srch-kbd{display:none!important}.hdr .srch{flex:1 1 0;min-width:0;max-width:34%}#hdrAuthBtn,.hdr .hdr-auth{flex:1 1 auto;min-width:0;flex-wrap:nowrap!important;overflow:hidden}#hdrAuthBtn .auth-btn--premium,#hdrAuthBtn a[href*='subscribe'],#hdrAuthBtn .auth-btn__badge:not(.auth-btn__badge--admin),#hdrAuthBtn a[href='/__admin']{display:none!important}[data-fe70-ask=mob]{display:inline-flex!important;flex:0 0 44px!important;width:44px!important;min-width:44px!important;max-width:44px!important;visibility:visible!important}}",
    "@media (min-width:768px){[data-fe70-ask=desk]{display:inline-flex!important;flex:0 0 auto!important;min-width:44px!important;visibility:visible!important;position:relative;z-index:262}#cmdAuthBtn{min-width:0;overflow:hidden}#cmdAuthBtn .auth-btn__badge:not(.auth-btn__badge--admin){display:none!important}}",
    ".fe71 .more-nav-panel{scrollbar-width:none;-ms-overflow-style:none}",
    ".fe71 .more-nav-panel::-webkit-scrollbar{width:0;height:0;display:none}",
    ".fe71 .fe71-swipe{position:sticky;top:0;z-index:5;background:rgb(14,14,16);padding-bottom:8px;user-select:none;-webkit-user-select:none;touch-action:none}",
    ".fe71.fe73-drag,.fe71.fe73-drag *{user-select:none!important;-webkit-user-select:none!important}",
    ".fe71-session{font-family:var(--sn,system-ui,sans-serif)!important;font-weight:500}",
    ".fe71-grp h3{color:#F6E7B8!important}",
    ".fe71-planrow a,.fe71-auth{border-bottom:0!important;text-decoration:none!important}",
    ".fe71-auth{min-height:44px;display:inline-flex;align-items:center;padding:0 12px;border-radius:10px;border:1px solid rgba(217,174,82,.55);background:rgba(217,174,82,.14);color:#F6E7B8;font:600 13px/1 var(--sn,system-ui,sans-serif);cursor:pointer}",
    ".fe71-ava svg{display:block}",
    ".fe71-pin{display:grid!important;grid-template-columns:1fr 1fr!important;grid-auto-rows:92px;gap:8px}",
    ".fe71-pin .fe71-tile{height:92px;min-height:92px;overflow:hidden}",
    ".fe71-pin .fe71-tile:last-child{grid-column:1 / -1}",
    ".fe71-pin .fe71-d,.fe71-grid .fe71-d{display:-webkit-box!important;-webkit-line-clamp:2!important;-webkit-box-orient:vertical;overflow:hidden}",
    ".fe71-grid{align-items:stretch;grid-auto-rows:72px}",
    ".fe71-grid .fe71-tile{height:72px;min-height:72px;overflow:hidden}",
    ".fe71-grid .fe71-tile:last-child:nth-child(odd){grid-column:1 / -1}",
    "@media (max-width:767px){#bnav.fe71-bar{background:rgba(12,12,14,.96)!important;-webkit-backdrop-filter:none!important;backdrop-filter:none!important}#bnav.fe71-bar button.on::after{background:rgba(217,174,82,.22)!important;border:1px solid rgba(217,174,82,.9)!important;box-shadow:none!important;filter:none!important}}"
  ].join("");
  document.head.appendChild(st);
}
function fe73_keepTape() {
  var t = document.querySelector(".tape");
  if (!t) return;
  try {
    var cs = getComputedStyle(t);
    if (cs.display === "none") t.style.setProperty("display", "block", "important");
    if (cs.visibility === "hidden") t.style.setProperty("visibility", "visible", "important");
  } catch (e) {}
  t.classList.remove("hide");
}
function fe73_homeTop() {
  try {
    if (typeof pg !== "undefined" && pg !== "home") return;
    if (window.scrollY > 80) window.scrollTo(0, 0);
    var m = document.getElementById("main");
    if (m && m.scrollTop > 80) m.scrollTop = 0;
  } catch (e) {}
}
function fe73_armNews() {
  try {
    if (typeof newsFetching !== "undefined" && newsFetching) return;
    if (typeof NEWS !== "undefined" && NEWS && NEWS.length) return;
    if (typeof fetchLiveNews === "function") fetchLiveNews();
  } catch (e) {}
}
function fe73_fitHeader() {
  var wide = false;
  try { wide = window.innerWidth >= 768; } catch (e) {}
  var ask = document.querySelector(wide ? '[data-fe70-ask="desk"]' : '[data-fe70-ask="mob"]');
  if (ask) {
    ask.style.setProperty("display", "inline-flex", "important");
    ask.style.setProperty("flex", "0 0 auto", "important");
    ask.style.setProperty("min-width", "44px", "important");
    ask.style.setProperty("visibility", "visible", "important");
    if (!wide) ask.style.setProperty("width", "44px", "important");
  }
  var host = document.getElementById(wide ? "cmdAuthBtn" : "hdrAuthBtn");
  if (!host) return;
  host.querySelectorAll(".auth-btn__badge:not(.auth-btn__badge--admin)").forEach(function (el) {
    el.style.setProperty("display", "none", "important");
  });
  if (!wide) {
    host.querySelectorAll(".auth-btn--premium, a[href*='subscribe']").forEach(function (el) {
      el.style.setProperty("display", "none", "important");
    });
  }
  if (!wide) {
    host.querySelectorAll("a[href='/__admin']").forEach(function (el) {
      el.style.setProperty("display", "none", "important");
    });
    var guard = 0;
    while (document.body.scrollWidth > document.documentElement.clientWidth + 1 && guard++ < 6) {
      var link = host.querySelector("a.auth-btn--ghost:last-of-type, a[href*='register']");
      if (!link) break;
      var w = link.getBoundingClientRect().width;
      if (w < 48) break;
      link.style.setProperty("max-width", Math.max(48, w - 24) + "px", "important");
      link.style.setProperty("overflow", "hidden", "important");
      link.style.setProperty("text-overflow", "ellipsis", "important");
    }
  }
}
function fe73_lensesChrome() {
  var narrow = false;
  try { narrow = window.innerWidth < 768; } catch (e) {}
  var nodes = document.querySelectorAll(".gc div");
  for (var i = 0; i < nodes.length; i++) {
    var n = nodes[i];
    if (!/^Lens Engine/.test(String(n.textContent || ""))) continue;
    n.setAttribute("data-fe73-sub", "1");
    n.style.whiteSpace = "nowrap";
    n.style.overflow = "hidden";
    n.style.textOverflow = "ellipsis";
    if (!narrow) continue;
    var row = n.parentElement && n.parentElement.parentElement;
    if (!row || row.querySelector("[data-fe73-back]")) continue;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "hdr-act-btn";
    b.setAttribute("data-fe73-back", "1");
    b.textContent = "Back";
    b.onclick = function () {
      try { if (typeof _rt26Back === "function") { _rt26Back(); return; } } catch (e2) {}
      try { nav("mkt"); } catch (e3) {}
    };
    row.insertBefore(b, row.firstChild);
  }
}
try { if (typeof FE71_BLURB !== "undefined") {
  FE71_BLURB.home = "Today's desk";
  FE71_BLURB.brief = "House view";
  FE71_BLURB.playbook = "Week plan";
  FE71_BLURB.gold = "Gold prices";
  FE71_BLURB.ask = "Ask the desk";
  FE71_BLURB.dash = "Whole desk";
  FE71_BLURB.lab = "Test one idea";
  FE71_BLURB.sig = "What we watch";
  FE71_BLURB.mkt = "Shares and metals";
  FE71_BLURB.scr = "Match a rule";
  FE71_BLURB.sectors = "Who is leading";
  FE71_BLURB.heat = "Sector moves";
  FE71_BLURB.crypto = "Bitcoin and coins";
  FE71_BLURB.news = "Headlines";
  FE71_BLURB.paper = "Longer notes";
  FE71_BLURB.research = "Full reports";
  FE71_BLURB.intel = "Filings, read";
  FE71_BLURB.geo = "Political risk";
  FE71_BLURB.watch = "Names you follow";
  FE71_BLURB.port = "What you hold";
  FE71_BLURB.learn = "Short lessons";
  FE71_BLURB.settings = "Account";
} } catch (e) {}
try {
  var fe73_openAt = _rt18MarketOpenAt;
  _rt18MarketOpenAt = function (tk, d) {
    var h = fe73_hours(tk);
    if (!h) return fe73_openAt.apply(this, arguments);
    try {
      if (h.fx) {
        var fx = _rt18Parts("America/New_York", d);
        if (fx.wd === "Sat") return false;
        if (fx.wd === "Fri" && fx.m >= 1020) return false;
        if (fx.wd === "Sun" && fx.m < 1020) return false;
        return true;
      }
      var p = _rt18Parts(h.tz, d);
      if (p.wd === "Sat" || p.wd === "Sun") return false;
      if (p.m < h.o || p.m >= h.c) return false;
      if (h.lunch && p.m >= h.lunch[0] && p.m < h.lunch[1]) return false;
      return true;
    } catch (e) { return fe73_openAt.apply(this, arguments); }
  };
  try { _rt18OpenCache.t = 0; _rt18OpenCache.m = {}; } catch (e2) {}
} catch (e) {}
try {
  var fe73_last0 = _rt20LastClose;
  _rt20LastClose = function (tk) {
    var h = null;
    try { h = fe73_hours(tk); } catch (e0) { h = null; }
    if (!h || h.fx) return fe73_last0.apply(this, arguments);
    try {
      var q = 15 * 60000, now = Math.floor(Date.now() / q) * q;
      if (_rt18MarketOpenAt(tk, new Date(now))) return null;
      var t;
      for (t = now; t > now - 8 * 86400000; t -= q) {
        if (_rt18MarketOpenAt(tk, new Date(t - q))) return t;
      }
    } catch (e1) {}
    return fe73_last0.apply(this, arguments);
  };
  try { if (typeof _rt20CloseCache !== "undefined") { for (var fe73k in _rt20CloseCache) delete _rt20CloseCache[fe73k]; } } catch (e2) {}
} catch (e) {}
try { fe66_chgLine = fe73_chgLine; } catch (e) {}
function fe73_usForm4(tk) {
  var t = String(tk || "").trim().toUpperCase();
  var cat = "";
  try { if (typeof TICKER_CATS !== "undefined" && TICKER_CATS[t]) cat = TICKER_CATS[t]; } catch (e) {}
  if (!fe73_form4(t, cat)) return false;
  try {
    if (typeof _rt18Class === "function") {
      var cls = _rt18Class(t);
      if (cls === "crypto" || cls === "fx" || cls === "fut") return false;
    }
  } catch (e2) {}
  try { if (typeof fe66_nonUs === "function" && fe66_nonUs(t)) return false; } catch (e3) {}
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && String(x.tk).toUpperCase() === t; }) : null;
    if (a) {
      var c2 = String(a.cat || "").toLowerCase();
      if (c2 === "crypto" || c2 === "fx" || c2.indexOf("commod") === 0) return false;
      if (a._rt43) return false;
    }
  } catch (e4) {}
  return true;
}
function fe73_form4Html() {
  return '<div class="fe68-ins"><p class="ex">' + fe73_form4Note() + "</p></div>";
}
try {
  var fe73_ins0 = fe69_insHtml;
  fe69_insHtml = function (tk, data, err) {
    try { if (tk && !fe73_usForm4(tk)) return fe73_form4Html(); } catch (e0) {}
    var saved = null;
    var html = "";
    try {
      if (typeof fe69_extra !== "undefined") {
        saved = fe69_extra[tk];
        fe69_extra[tk] = (saved || []).map(fe73_viewRow);
      }
      html = fe73_ins0.call(this, tk, fe73_viewData(data), err);
    } catch (e1) {
      html = fe73_ins0.apply(this, arguments);
    } finally {
      try { if (saved !== null && typeof fe69_extra !== "undefined") fe69_extra[tk] = saved; } catch (e2) {}
    }
    try {
      var rows = [];
      if (data && Array.isArray(data.insider)) rows = rows.concat(data.insider);
      if (typeof fe69_extra !== "undefined" && fe69_extra[tk]) rows = rows.concat(fe69_extra[tk]);
      var label = fe73_spanLabel(data && data.meta, rows);
      if (label) {
        var para = '<p class="ex fe69-win">' + fe68_esc(label) + "</p>";
        if (html.indexOf("fe69-win") >= 0) html = html.replace(/<p class="ex fe69-win">[\s\S]*?<\/p>/, para);
        else html = html.replace('<div class="fe68-ins">', '<div class="fe68-ins">' + para);
      }
    } catch (e3) {}
    return fe73_dates(html);
  };
  fe68_insHtml = fe69_insHtml;
} catch (e) {}
try {
  var fe73_loadIns0 = fe69_loadInsiders;
  fe69_loadInsiders = async function (tk, rootId) {
    if (tk && !fe73_usForm4(tk)) {
      var root = typeof fe69_insRoot === "function" ? fe69_insRoot(rootId) : null;
      if (root) root.innerHTML = fe73_form4Html();
      return;
    }
    return fe73_loadIns0.apply(this, arguments);
  };
  fe68_loadInsiders = fe69_loadInsiders;
} catch (e) {}
try { fe68_usStock = function (a) { return !!(a && a.tk); }; } catch (e) {}
var fe73_lastPayload = null;
try {
  var fe73_fetchIns0 = fe69_fetchIns;
  fe69_fetchIns = async function (url) {
    try {
      var fe73m = /[?&]t=([^&]+)/.exec(String(url || ""));
      var fe73tk = fe73m ? decodeURIComponent(fe73m[1]) : "";
      if (fe73tk && !fe73_usForm4(fe73tk)) return { res: { status: 200 }, data: { insider: [] } };
    } catch (e0) {}
    var got = await fe73_fetchIns0.apply(this, arguments);
    try { fe73_lastPayload = got && got.data; } catch (e1) {}
    return got;
  };
  var fe73_older0 = fe69_loadOlder;
  fe69_loadOlder = async function (tk) {
    fe73_lastPayload = null;
    var out = await fe73_older0.apply(this, arguments);
    try {
      var base = fe69_loadInsiders.last;
      var span = fe73_lastPayload && fe73_lastPayload.meta && fe73_lastPayload.meta.span;
      if (base && base.meta) {
        if (span && (span.label || span.from || span.to || span.fromUk || span.toUk)) base.meta.span = span;
        else delete base.meta.span;
        var root = typeof fe69_insRoot === "function" ? fe69_insRoot(fe69_loadOlder.rootId || "") : null;
        if (root) root.innerHTML = fe69_insHtml(tk, base, "");
      }
    } catch (e2) {}
    return out;
  };
} catch (e) {}
try {
  var fe73_newsHead0 = fe69_newsHead;
  fe69_newsHead = function (d) {
    var html = fe73_newsHead0.apply(this, arguments);
    try {
      var by = (d && d.byTk) || {};
      Object.keys(by).forEach(function (tk) {
        var info = by[tk] || {};
        var label = fe73_spanLabel({ span: info.span, window: info.window }, []);
        if (!label || !info.window || !info.window.label) return;
        var from = fe68_esc(tk + " \u00b7 " + info.window.label);
        var to = fe68_esc(tk + " \u00b7 " + label);
        if (from !== to) html = html.split(from).join(to);
      });
    } catch (e1) {}
    return fe73_dates(html);
  };
} catch (e) {}
try {
  var fe73_groups0 = fe71_groups;
  fe71_groups = function () {
    var groups = fe73_groups0();
    var book = null, account = null, rest = [];
    groups.forEach(function (g) {
      if (g.g === "Account") account = g;
      else { rest.push(g); if (g.g === "Book") book = g; }
    });
    if (account && book) account.items.forEach(function (it) { book.items.push(it); });
    else if (account) rest.push(account);
    return rest;
  };
} catch (e) {}
try {
  var fe73_session0 = fe71_sessionLine;
  fe71_sessionLine = function () {
    var parts = [];
    try { if (typeof _rt18MarketOpen === "function" && _rt18MarketOpen("HSBA.L")) parts.push("London open"); } catch (e) {}
    try { if (typeof _rt18MarketOpen === "function" && (_rt18MarketOpen("SAP.DE") || _rt18MarketOpen("MC.PA"))) parts.push("Europe open"); } catch (e2) {}
    var rest = "";
    try { rest = fe73_session0(); } catch (e3) {}
    if (rest) parts.push(rest);
    return parts.join(" \u00b7 ");
  };
} catch (e) {}
try { fe71_sheetHtml = fe73_sheetHtml; } catch (e) {}
try { fe71_swipe = fe73_swipe; } catch (e) {}
try {
  var fe73_wire0 = fe71_wire;
  fe71_wire = function (sheet) {
    fe73_wire0(sheet);
    sheet.querySelectorAll("[data-fe73-auth]").forEach(function (b) {
      b.addEventListener("click", function () {
        var href = b.getAttribute("data-fe73-auth");
        if (href) location.href = href;
      });
    });
  };
} catch (e) {}
try {
  var fe73_open0 = fe71_openMoreNav;
  fe71_openMoreNav = function () {
    var sheet0 = document.getElementById("moreNav");
    if (sheet0) { try { sheet0.inert = false; } catch (e0) {} }
    var focus0 = HTMLElement.prototype.focus;
    HTMLElement.prototype.focus = function () {
      try { if (this.classList && this.classList.contains("fe71-find")) return; } catch (e1) {}
      return focus0.apply(this, arguments);
    };
    try { fe73_open0.apply(this, arguments); }
    finally { HTMLElement.prototype.focus = focus0; }
    var sheet = document.getElementById("moreNav");
    try { if (sheet) { sheet.inert = false; sheet.focus(); } } catch (e2) {}
    function fe73_reveal(n) {
      try {
        var on = sheet && sheet.querySelector(".fe71-tile.on");
        var panel = sheet && sheet.querySelector(".more-nav-panel");
        if (!on || !panel) return;
        var delta = on.getBoundingClientRect().top - panel.getBoundingClientRect().top - 64;
        if (Math.abs(delta) > 8) panel.scrollTop += delta;
        if (n < 4) setTimeout(function () { fe73_reveal(n + 1); }, 160);
      } catch (e4) {}
    }
    try { setTimeout(function () { fe73_reveal(0); }, 80); } catch (e3) {}
  };
  openMoreNav = fe71_openMoreNav;
} catch (e) {}
try {
  var fe73_close0 = fe71_closeMoreNav;
  fe71_closeMoreNav = function () {
    var sheet = document.getElementById("moreNav");
    var trigger = document.querySelector("[data-more-nav-trigger]");
    try {
      var ae = document.activeElement;
      if (sheet && ae && sheet.contains(ae) && ae.blur) ae.blur();
      if (sheet) sheet.inert = true;
    } catch (e0) {}
    var out = fe73_close0.apply(this, arguments);
    try {
      trigger = document.querySelector("[data-more-nav-trigger]");
      if (trigger && trigger.focus) trigger.focus();
    } catch (e1) {}
    return out;
  };
  closeMoreNav = fe71_closeMoreNav;
} catch (e) {}
try {
  var fe73_fetch0 = fetchLiveNews;
  fetchLiveNews = async function () {
    var out = await fe73_fetch0.apply(this, arguments);
    try { if (typeof fe70_repaintNews === "function") fe70_repaintNews(); } catch (e) {}
    return out;
  };
} catch (e) {}
try {
  var fe73_nav0 = nav;
  nav = function (p) {
    var out = fe73_nav0.apply(this, arguments);
    try { if (p === "home") { fe73_homeTop(); fe73_armNews(); } } catch (e) {}
    try { fe73_fitHeader(); fe73_lensesChrome(); } catch (e2) {}
    return out;
  };
} catch (e) {}
try {
  var fe73_tog0 = toggleExpand;
  toggleExpand = function (id) {
    var out = fe73_tog0.apply(this, arguments);
    try {
      var p = document.getElementById(id);
      if (p && p.classList.contains("p-expanded")) {
        window.scrollTo(0, 0);
        if (p.scrollIntoView) p.scrollIntoView({ block: "start" });
      }
    } catch (e) {}
    try { fe73_lensesChrome(); } catch (e2) {}
    return out;
  };
} catch (e) {}
try {
  var fe73_auth0 = renderAuthButtons;
  renderAuthButtons = function () {
    var out = fe73_auth0.apply(this, arguments);
    try { fe73_fitHeader(); } catch (e) {}
    return out;
  };
} catch (e) {}
try {
  var fe73_main0 = renderMain;
  renderMain = function () {
    var out = fe73_main0.apply(this, arguments);
    try { fe73_lensesChrome(); fe73_fitHeader(); } catch (e) {}
    return out;
  };
} catch (e) {}
function fe73_chatRead() {
  var ver = "chat70";
  try {
    var v = localStorage.getItem("td_chat_v");
    if (v !== ver) {
      _chatMsgs = [];
      try { sessionStorage.removeItem("td_chat"); } catch (e1) {}
      try { localStorage.removeItem("td_chat"); } catch (e2) {}
      try { localStorage.setItem("td_chat_v", ver); } catch (e3) {}
      return;
    }
    var raw = localStorage.getItem("td_chat");
    if (raw == null) {
      _chatMsgs = [];
      try { sessionStorage.removeItem("td_chat"); } catch (e4) {}
      return;
    }
    var parsed = JSON.parse(raw);
    _chatMsgs = Array.isArray(parsed) ? parsed.slice(-20) : [];
    try { sessionStorage.removeItem("td_chat"); } catch (e5) {}
  } catch (e) { _chatMsgs = []; }
}
function fe73_chatWrite() {
  var blob = "[]";
  try { blob = JSON.stringify((_chatMsgs || []).slice(-20)); } catch (e) { blob = "[]"; }
  try { localStorage.setItem("td_chat", blob); } catch (e2) {}
  try { localStorage.setItem("td_chat_v", "chat70"); } catch (e3) {}
  try { sessionStorage.removeItem("td_chat"); } catch (e4) {}
}
try { _persistChat = fe73_chatWrite; } catch (e) {}
try {
  var fe73_clear0 = clearChat;
  clearChat = function () {
    _chatMsgs = [];
    try { localStorage.removeItem("td_chat"); } catch (e1) {}
    try { sessionStorage.removeItem("td_chat"); } catch (e2) {}
    try { if (typeof fe73_clear0 === "function") fe73_clear0(); } catch (e3) {}
    try { if (typeof _renderChatMsgs === "function") _renderChatMsgs(); } catch (e4) {}
  };
} catch (e) {}
try {
  var fe73_rm0 = Storage.prototype.removeItem;
  var fe73_rmBusy = false;
  Storage.prototype.removeItem = function (key) {
    var out = fe73_rm0.apply(this, arguments);
    if (fe73_rmBusy || String(key) !== "td_chat" || this !== window.localStorage) return out;
    fe73_rmBusy = true;
    try { fe73_rm0.call(window.sessionStorage, "td_chat"); } catch (e1) {}
    finally { fe73_rmBusy = false; }
    return out;
  };
} catch (e) {}
try { fe73_chatRead(); } catch (e) {}
try { fe73_css(); } catch (e) {}
try { fe73_armNews(); fe73_fitHeader(); fe73_homeTop(); fe73_keepTape(); } catch (e) {}
try {
  var fe73_n = 0;
  var fe73_boot = setInterval(function () {
    fe73_n++;
    try { fe73_keepTape(); fe73_fitHeader(); if (fe73_n < 8) fe73_homeTop(); } catch (e) {}
    try {
      if ((typeof NEWS === "undefined" || !NEWS.length) && fe73_n % 4 === 0) fe73_armNews();
      else if (typeof fe70_repaintNews === "function" && document.body && /Loading headlines/.test(document.body.innerText || "")) fe70_repaintNews();
    } catch (e2) {}
    if (fe73_n > 40) clearInterval(fe73_boot);
  }, 500);
} catch (e) {}
try { window.addEventListener("resize", function () { try { fe73_fitHeader(); fe73_lensesChrome(); } catch (e) {} }, { passive: true }); } catch (e) {}
'''


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
        "function fe66_chgLine(",
        "function _rt18MarketOpenAt(",
        "function fe71_sheetHtml(",
        "function fe71_openMoreNav(",
        "function fe71_closeMoreNav(",
        "function fe69_insHtml(",
        "function fe68_insHtml(",
        "function _rt53HomeOn(",
        "function toggleExpand(",
        "function fetchLiveNews(",
        "function renderAuthButtons(",
    ]
    for a in anchors:
        n = app.count(a)
        if n != 1:
            die("anchor %s count %s" % (a, n))
    if index.count('app.js?v=chat73"') != 1:
        die("cache bust anchor missing")
    if "data-fe70-ask=\"mob\"" not in index:
        die("mobile ask anchor missing")
    swaps = [
        (
            "byTk[tk] = { window: (data.meta && data.meta.window) || null, partial: !!(data.meta && data.meta.partial) };",
            "byTk[tk] = { window: (data.meta && data.meta.window) || null, span: (data.meta && data.meta.span) || null, partial: !!(data.meta && data.meta.partial) };",
            1,
        ),
        (
            "d.byTk[tk] = { window: data.meta.window, partial: !!data.meta.partial };",
            "d.byTk[tk] = { window: data.meta.window, span: (data.meta && data.meta.span) || null, partial: !!data.meta.partial };",
            1,
        ),
        (
            "date: row.transactionDate || row.filingDate, sourceUrl: row.filingUrl",
            "date: (typeof fe73_showDate===\"function\"?fe73_showDate(row.transactionDateUk||row.filingDateUk, row.transactionDate||row.filingDate):(row.transactionDate||row.filingDate)), sourceUrl: row.filingUrl",
            3,
        ),
        (
            "(tx.transactionDate||tx.filingDate||'').slice(0,10)",
            "(typeof fe73_showDate===\"function\"?fe73_showDate(tx.transactionDateUk||tx.filingDateUk, tx.transactionDate||tx.filingDate):(tx.transactionDate||tx.filingDate||''))",
            1,
        ),
        (
            "    h+=(typeof _rt53FitHtml===\"function\"?_rt53FitHtml(_dynTk):\"\");\n    h+=`<div style=\"padding:6px 8px;border-top:1px solid var(--b4)\">",
            "    h+=(typeof _rt53FitHtml===\"function\"?_rt53FitHtml(_dynTk):\"\");\n"
            "    h+=`<div class=\"tabs\"><button type=\"button\" class=\"${aTab===\"ins\"?\"on\":\"\"}\" onclick=\"_setATab('ins')\">Insiders</button></div>`;\n"
            "    if(aTab===\"ins\"){h+=`<div id=\"term-ins-root\" class=\"fe68-ins\"><div style=\"padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3)\">Loading insider filings…</div></div>`;setTimeout(function(){try{fe68_loadInsiders(_dynTk,\"term-ins-root\");}catch(e){}},40);}\n"
            "    h+=`<div style=\"padding:6px 8px;border-top:1px solid var(--b4)\">",
            1,
        ),
        (
            "  h+=(typeof _rt53FitHtml===\"function\"?_rt53FitHtml(_dynTk):\"\");\n  h+=`<button onclick=\"_dynClear()\"",
            "  h+=(typeof _rt53FitHtml===\"function\"?_rt53FitHtml(_dynTk):\"\");\n"
            "  h+=`<div class=\"tabs\"><button type=\"button\" class=\"${aTab===\"ins\"?\"on\":\"\"}\" onclick=\"_setATab('ins')\">Insiders</button></div>`;\n"
            "  if(aTab===\"ins\"){h+=`<div id=\"anlz-ins-root\" class=\"fe68-ins\"><div style=\"padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3)\">Loading insider filings…</div></div>`;setTimeout(function(){try{fe68_loadInsiders(_dynTk,\"anlz-ins-root\");}catch(e){}},40);}\n"
            "  h+=`<button onclick=\"_dynClear()\"",
            1,
        ),
    ]
    for old, new, n in swaps:
        got = app.count(old)
        if got != n:
            die("anchor %s count %s" % (old[:48], got))
        app = app.replace(old, new)
    app = app + BLOCK
    if app.count("function fe73_move(") != 1:
        die("fe73_move count")
    if app.count("function fe73_form4(") != 1:
        die("fe73_form4 count")
    if app.count("function fe73_chatRead(") != 1:
        die("fe73_chatRead count")
    index = index.replace('app.js?v=chat73"', 'app.js?v=chat74"', 1)
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
