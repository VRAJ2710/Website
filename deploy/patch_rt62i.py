#!/usr/bin/env python3
"""rt62i client patch: chat85 -> chat86. Anchors decide; md5 only warns.

Applies on the chat85 output (PR #82). Keeps every fe84 and fe85 guard.

The home tape gold row uses the futures price, the futures point change and
the session day. A metal tile keeps its own futures label and is LIVE only
while that market is open. A brief-strip value that is only a placeholder
is removed once it would otherwise stand as the finished text.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "a88ca4b4e780faaddd756700375445b9"
EXPECT_INDEX_PREFIX = "696df415"
NEED_MARKER = "// ── rt62h ──"
REFUSE_MARKER = "// ── rt62i ──"

BLOCK = r"""
// ── rt62i ──
// fe86: the tape gold row is the futures print, a metal tile keeps its own
// contract, and a brief-strip placeholder is not a finished value.
// fe86-pure-begin
function fe86_cmd(tk) {
  var id = String(tk == null ? "" : tk).toUpperCase().replace(/\s/g, "");
  var map = {
    COPPER: ["Copper futures", "HG=F"],
    HG: ["Copper futures", "HG=F"],
    "HG=F": ["Copper futures", "HG=F"],
    SLV: ["Silver futures", "SI=F"],
    SI: ["Silver futures", "SI=F"],
    "SI=F": ["Silver futures", "SI=F"],
    PLAT: ["Platinum futures", "PL=F"],
    "PL=F": ["Platinum futures", "PL=F"],
    PALLADIUM: ["Palladium futures", "PA=F"],
    "PA=F": ["Palladium futures", "PA=F"],
    NG: ["Natural gas futures", "NG=F"],
    "NG=F": ["Natural gas futures", "NG=F"],
    WTI: ["WTI futures", "CL=F"],
    "CL=F": ["WTI futures", "CL=F"],
    BRENT: ["Brent futures", "BZ=F"],
    "BZ=F": ["Brent futures", "BZ=F"]
  };
  var row = map[id];
  if (!row) return null;
  return { name: row[0], sym: row[1], label: row[0] + " (" + row[1] + ")" };
}
function fe86_srcGold(src) {
  var s = String(src == null ? "" : src);
  if (/spot-metal/i.test(s)) return false;
  if (/gold-api-spot-proxy/i.test(s)) return true;
  if (/\bGC=F\b/i.test(s)) return true;
  if (/\bXAU\b/.test(s)) return true;
  return false;
}
function fe86_valOnly(s) {
  var t = String(s == null ? "" : s).replace(/<[^>]+>/g, "").replace(/\s+/g, "");
  return t === "\u2026" || t === "\u2014" || t === "\u2013" || t === "..." || t === "-" || t === "\u2015";
}
function fe86_stripHtml(html) {
  return String(html || "").replace(/<div class="ns-cell\b[^"]*"[^>]*>(?:(?!<div\b)[\s\S])*?<\/div>/g, function (block) {
    var m = block.match(/<span class="ns-val(?:\s[^"]*)?"[^>]*>([\s\S]*?)<\/span>/);
    if (m && fe86_valOnly(m[1])) return "";
    return block;
  });
}
function fe86_cmdLine(label, closed, day, asof) {
  var line = String(label || "");
  if (closed) line += " \u00b7 CLOSED" + (day ? " \u00b7 " + day : "");
  if (asof) line += " \u00b7 as of " + String(asof).replace(/^as of\s+/i, "");
  return line.replace(/\s+/g, " ").trim();
}
function fe86_goldRow(px, chg) {
  var row = "Gold " + String(px || "");
  var c = String(chg || "").replace(/^\s+/, "");
  if (c) row += " " + c;
  return row.replace(/\s+/g, " ").trim();
}
function fe86_needs(cur, line) {
  var c = String(cur || "").replace(/\s+/g, " ").trim();
  var l = String(line || "").replace(/\s+/g, " ").trim();
  if (!l || c === l) return false;
  if (!c || c === "\u2014" || c === "\u2013" || c === "-" || c === "\u2026") return true;
  if (/\b(Mon|Tue|Wed|Thu|Fri)\b/.test(l) && !/\b(Mon|Tue|Wed|Thu|Fri)\b/.test(c)) return true;
  if (/\([^)]*%\)/.test(l) && !/\([^)]*%\)/.test(c)) return true;
  return false;
}
function fe86_esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
// fe86-pure-end
var fe86_tapeAt = 0;
var fe86_cmdAt = 0;
var fe86_stripAt = 0;
var fe86_lineAt = Object.create(null);
var fe86_lineVal = Object.create(null);
var fe86_clAt = Object.create(null);
var fe86_clVal = Object.create(null);
var fe86_bdBusy = false;
function fe86_id(tk) {
  try { if (typeof fe85_id === "function") return fe85_id(tk) || tk; } catch (e) {}
  try { if (typeof resolveInternalTicker === "function") return resolveInternalTicker(tk) || tk; } catch (e2) {}
  return tk;
}
function fe86_crypto(tk) {
  try { if (typeof fe85_cryptoTk === "function") return !!fe85_cryptoTk(tk); } catch (e) {}
  return false;
}
function fe86_closed(tk) {
  var now = Date.now();
  if (fe86_clVal[tk] != null && now - (fe86_clAt[tk] || 0) < 8000) return fe86_clVal[tk];
  var v = false;
  try { v = typeof fe83f_marketClosed === "function" && !!fe83f_marketClosed(tk); } catch (e) { v = false; }
  fe86_clAt[tk] = now;
  fe86_clVal[tk] = v;
  return v;
}
function fe86_day(tk) {
  var day = "";
  try { day = (typeof fe83f_pickDay === "function" && fe83f_pickDay(tk)) || ""; } catch (e) { day = ""; }
  if (fe86_closed(tk) && (!day || day === "Sat" || day === "Sun")) day = "Fri";
  if (!fe86_closed(tk) && (day === "Sat" || day === "Sun")) day = "";
  return day;
}
function fe86_rowState(tk) {
  var now = Date.now();
  var sig = "";
  try {
    var row = typeof P !== "undefined" && P ? P[tk] : null;
    sig = row ? String(row.p) + ":" + String(row.c) : "";
  } catch (e0) { sig = ""; }
  var hit = fe86_lineVal[tk];
  if (hit && hit.sig === sig && now - (fe86_lineAt[tk] || 0) < 8000) return hit;
  var closed = !fe86_crypto(tk) && fe86_closed(tk);
  var line = "";
  if (closed) {
    try { line = (typeof fe85_glanceBits === "function" && fe85_glanceBits(tk)) || ""; } catch (e) { line = ""; }
    line = String(line).replace(/^Gold futures \(GC=F\)\s*/, "").replace(/^Gold spot\s*/, "");
  }
  hit = { closed: closed, line: line, sig: sig };
  fe86_lineAt[tk] = now;
  fe86_lineVal[tk] = hit;
  return hit;
}
function fe86_cachedLine(tk) {
  return fe86_rowState(tk).line || "";
}
function fe86_goldChg(b) {
  if (!b || b.kind !== "futures") return "";
  var pct = b.pct == null ? "" : fe85_signed(b.pct, "%");
  var line = fe85_paren(b.pts || "", pct, fe86_day("XAU"));
  try { if (typeof fe83f_fixSigns === "function") line = fe83f_fixSigns(line); } catch (e) {}
  return line;
}
function fe86_fixGold(nodes) {
  var b = null;
  try { b = fe83f_goldBits(); } catch (e) { b = null; }
  var i, j;
  for (i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var kids = el.children || [];
    if (kids.length < 3) continue;
    var extra = el.querySelectorAll(".fe77-fut");
    for (j = extra.length - 1; j >= 0; j--) {
      if (extra[j].parentNode) extra[j].parentNode.removeChild(extra[j]);
    }
    if (b && b.kind === "futures" && b.px != null) {
      var px = "";
      try { px = fe83f_px(b.px); } catch (e2) { px = ""; }
      var chg = fe86_goldChg(b);
      if (kids[0].textContent !== "Gold ") kids[0].textContent = "Gold ";
      if (px && kids[1].textContent !== px) kids[1].textContent = px;
      if (chg) {
        var cell = " \u00b7 " + chg;
        if (kids[2].textContent !== cell) kids[2].textContent = cell;
      }
      if (el.getAttribute("title") !== "Gold futures (GC=F)") el.setAttribute("title", "Gold futures (GC=F)");
    } else if (b && b.kind === "spot") {
      var sp = "";
      try { sp = fe83f_px(b.px); } catch (e3) { sp = ""; }
      if (kids[0].textContent !== "Gold spot") kids[0].textContent = "Gold spot";
      if (sp && kids[1].textContent !== sp) kids[1].textContent = sp;
      if (kids[2].textContent === "\u2014" || kids[2].textContent === "\u2013") kids[2].textContent = "";
      if (el.getAttribute("title") !== "Gold spot") el.setAttribute("title", "Gold spot");
    }
  }
}
function fe86_fixRow(el) {
  var tk = el.getAttribute("data-tk") || "";
  var id = fe86_id(tk);
  if (!id || id === "XAU" || id === "GC=F" || fe86_crypto(id)) return;
  var kids = el.children || [];
  if (kids.length < 3) return;
  var state = fe86_rowState(id);
  if (!state.closed) return;
  var line = state.line;
  if (!fe86_needs(kids[2].textContent || "", line)) return;
  kids[2].textContent = line;
}
function fe86_fixTape() {
  if (typeof document === "undefined") return;
  var gold = document.querySelectorAll("#tape .ti[data-tk='XAU'],#tape .ti[data-tk='GC=F']");
  fe86_fixGold(gold);
  var now = Date.now();
  if (now - fe86_tapeAt < 4000) return;
  fe86_tapeAt = now;
  var rows = document.querySelectorAll("#tape .ti[data-tk]");
  for (var i = 0; i < rows.length; i++) fe86_fixRow(rows[i]);
}
function fe86_tileTk(el) {
  var tk = el.getAttribute("data-price-card") || "";
  if (tk) return tk;
  var s = el.querySelector && el.querySelector(".spine-tk");
  if (s && s.textContent) return String(s.textContent).trim();
  if (el.classList && el.classList.contains("heat-tile")) {
    var d = el.querySelector("div");
    if (d && d.textContent) return String(d.textContent).trim();
  }
  return "";
}
function fe86_paintOne(el) {
  var tk = fe86_tileTk(el);
  var spec = fe86_cmd(fe86_id(tk));
  if (!spec) return;
  var closed = fe86_closed(tk);
  var have = el.textContent || "";
  if (have.indexOf(spec.sym) >= 0 && have.indexOf("Gold futures") < 0 && have.indexOf("market feed") < 0) {
    if (!closed || (have.indexOf("CLOSED") >= 0 && have.indexOf("LIVE") < 0 && have.indexOf("Fri") >= 0)) return;
  }
  var day = closed ? fe86_day(tk) : "";
  var hm = "";
  var asof = el.querySelector(".spine-asof, .asof-tag");
  if (asof) {
    var found = String(asof.textContent || "").match(/as of (.+UK)/);
    if (found) hm = found[1];
    var line = fe86_cmdLine(spec.label, closed, day, hm);
    if (asof.textContent !== line) asof.textContent = line;
  }
  var leaves = el.querySelectorAll("span, div");
  for (var j = 0; j < leaves.length; j++) {
    if (leaves[j].children && leaves[j].children.length) continue;
    if (asof && leaves[j] === asof) continue;
    var t = leaves[j].textContent || "";
    if (/Gold futures \(GC=F\)|Gold spot|market feed|gold-api|Spot metal|Spot copper|Spot silver|Spot platinum|Spot palladium/i.test(t)) {
      var keep = (String(t).match(/as of (.+UK)/) || [])[1] || hm;
      var next = fe86_cmdLine(spec.label, closed, day, keep);
      if (leaves[j].textContent !== next) leaves[j].textContent = next;
    } else if (closed && /^(LIVE|SPOT|STALE[·|]SPOT)$/i.test(t.trim())) {
      leaves[j].textContent = "CLOSED";
    }
  }
  var title = el.getAttribute("title") || "";
  if (/Gold futures \(GC=F\)|gold-api|market feed/i.test(title)) el.setAttribute("title", spec.label);
  var al = el.getAttribute("aria-label") || "";
  if (/Gold futures \(GC=F\)/.test(al)) el.setAttribute("aria-label", al.replace(/Gold futures \(GC=F\)/g, spec.label));
}
function fe86_paintCmd() {
  var now = Date.now();
  if (now - fe86_cmdAt < 4000 || typeof document === "undefined") return;
  fe86_cmdAt = now;
  var nodes;
  try { nodes = document.querySelectorAll(".heat-tile"); } catch (e) { return; }
  for (var i = 0; i < nodes.length; i++) {
    try { fe86_paintOne(nodes[i]); } catch (e2) {}
  }
}
function fe86_paintStrip() {
  if (typeof document === "undefined") return;
  var now = Date.now();
  if (now - fe86_stripAt < 2000) return;
  fe86_stripAt = now;
  var cells;
  try { cells = document.querySelectorAll(".neural-strip .ns-cell"); } catch (e) { return; }
  for (var i = cells.length - 1; i >= 0; i--) {
    var val = cells[i].querySelector(".ns-val");
    if (val && fe86_valOnly(val.textContent) && cells[i].parentNode) cells[i].parentNode.removeChild(cells[i]);
  }
}
function fe86_fixSpineHtml(html) {
  var s = String(html || "");
  var keys = ["COPPER", "SLV", "PLAT", "PALLADIUM", "NG", "WTI", "BRENT"];
  for (var i = 0; i < keys.length; i++) {
    var tk = keys[i];
    var spec = fe86_cmd(tk);
    if (!spec) continue;
    var token = '<span class="spine-tk">' + tk + "</span>";
    var at = s.indexOf(token);
    if (at < 0) continue;
    var from = s.lastIndexOf("<button", at);
    var to = s.indexOf("</button>", at);
    if (from < 0 || to < 0) continue;
    var btn = s.slice(from, to);
    var closed = fe86_closed(tk);
    var day = closed ? fe86_day(tk) : "";
    var hm = "";
    var m = btn.match(/as of (.+UK)/);
    if (m) hm = m[1];
    var line = fe86_cmdLine(spec.label, closed, day, hm);
    btn = btn.replace(/(<span class="spine-asof">)[\s\S]*?(<\/span>)/, "$1" + fe86_esc(line) + "$2");
    btn = btn.replace(/Gold futures \(GC=F\)/g, spec.label);
    if (closed) btn = btn.replace(/>LIVE</g, ">CLOSED<");
    s = s.slice(0, from) + btn + s.slice(to);
  }
  return s;
}
try {
  var fe86_src0 = _quoteSourceLabel;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe86_src0.apply(this, arguments) || ""; } catch (e) { out = String(src || ""); }
    if (!fe86_srcGold(src) && /Gold futures \(GC=F\)|^Gold spot$/.test(out)) return "market feed";
    return out;
  };
} catch (eSrc) {}
try {
  var fe86_bd0 = fe68_badge;
  fe68_badge = function (m, tk, now) {
    var o = fe86_bd0.apply(this, arguments);
    if (!o || fe86_bdBusy) return o;
    var spec = fe86_cmd(fe86_id(tk));
    if (!spec) return o;
    fe86_bdBusy = true;
    try {
      o.detail = spec.label;
      if (fe86_closed(fe86_id(tk))) {
        o.status = "closed";
        o.label = "CLOSED";
        var day = fe86_day(fe86_id(tk));
        if (!o.fe64Note || /spot|gold|live|api/i.test(String(o.fe64Note))) o.fe64Note = day || "";
      }
    } catch (e) {}
    fe86_bdBusy = false;
    return o;
  };
} catch (eBd) {}
try {
  var fe86_as0 = asOfTag;
  asOfTag = function (tk) {
    var id = fe86_id(tk);
    var spec = fe86_cmd(id);
    if (spec) {
      var d = null;
      try { d = fp(tk); } catch (e) { d = null; }
      var closed = fe86_closed(id);
      var day = closed ? fe86_day(id) : "";
      var hm = "";
      try { if (d && d.asOf && typeof fe64_ukHm === "function") hm = fe64_ukHm(d.asOf) || ""; } catch (e2) { hm = ""; }
      var line = fe86_cmdLine(spec.label, closed, day, hm ? hm + " UK" : "");
      var esc = typeof _escHtml === "function" ? _escHtml(line) : fe86_esc(line);
      var attr = typeof _escAttr === "function" ? _escAttr(spec.label) : fe86_esc(spec.label);
      return '<span class="asof-tag" title="' + attr + '">' + esc + "</span>";
    }
    var html = "";
    try { html = fe86_as0.apply(this, arguments) || ""; } catch (e3) { html = ""; }
    if (id !== "XAU" && id !== "GC=F" && /Gold futures \(GC=F\)/.test(html)) html = html.replace(/Gold futures \(GC=F\)/g, "market feed");
    return html;
  };
} catch (eAs) {}
try {
  var fe86_stat0 = stat;
  stat = function (tk) {
    var html = "";
    try { html = fe86_stat0.apply(this, arguments) || ""; } catch (e) { html = ""; }
    var id = fe86_id(tk);
    var spec = fe86_cmd(id);
    if (!spec) return html;
    if (/Gold futures \(GC=F\)/.test(html)) html = html.replace(/Gold futures \(GC=F\)/g, spec.label);
    if (fe86_closed(id)) html = html.replace(/>\s*LIVE\s*</g, ">CLOSED<");
    return html;
  };
} catch (eSt) {}
try {
  var fe86_spine0 = _renderDeskSpine;
  _renderDeskSpine = function () {
    var h = "";
    try { h = fe86_spine0.apply(this, arguments) || ""; } catch (e) { h = ""; }
    try { h = fe86_fixSpineHtml(h); } catch (e2) {}
    return h;
  };
} catch (eSp) {}
try {
  var fe86_ns0 = _renderNeuralSessionStrip;
  _renderNeuralSessionStrip = function () {
    var h = "";
    try { h = fe86_ns0.apply(this, arguments) || ""; } catch (e) { h = ""; }
    try { h = fe86_stripHtml(h); } catch (e2) {}
    return h;
  };
} catch (eNs) {}
try {
  var fe86_ev0 = _signalEvidence;
  _signalEvidence = function (signal) {
    var ev = fe86_ev0.apply(this, arguments);
    try {
      var tk = (signal && signal.tk) || (ev && ev.tk);
      var spec = fe86_cmd(fe86_id(tk));
      if (spec && ev) {
        ev.source = spec.label;
        if (fe86_closed(tk)) ev.status = "CLOSED";
      }
    } catch (e) {}
    return ev;
  };
} catch (eEv) {}
try {
  var fe86_nm0 = fe65_tapeName;
  fe65_tapeName = function (tk) {
    var id = fe86_id(tk);
    if (id === "XAU" || id === "GC=F") {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      if (b && b.kind === "spot") return "Gold spot";
      return "Gold";
    }
    return fe86_nm0.apply(this, arguments);
  };
} catch (eNm) {}
try {
  var fe86_cell0 = fe82_tapeCell;
  var fe86_cellBusy = false;
  fe82_tapeCell = function (tk, ch, d) {
    if (fe86_cellBusy) {
      try { return fe86_cell0.apply(this, arguments); } catch (e0) { return ""; }
    }
    var id = fe86_id(tk);
    if (id === "XAU" || id === "GC=F" || tk === "XAU") {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      var line = fe86_goldChg(b);
      if (line) return " \u00b7 " + line;
      if (b && b.kind === "spot") return "";
    }
    if (id && !fe86_crypto(id)) {
      fe86_cellBusy = true;
      var state = null;
      try { state = fe86_rowState(id); } catch (e2) { state = null; }
      fe86_cellBusy = false;
      if (state && state.closed && state.line) return state.line;
    }
    try { return fe86_cell0.apply(this, arguments); } catch (e3) { return ""; }
  };
} catch (eCell) {}
try {
  var fe86_bit0 = _liveTapeBit;
  _liveTapeBit = function (label) {
    var tks = Array.prototype.slice.call(arguments, 1);
    var gold = label === "Gold" || tks.indexOf("XAU") >= 0 || tks.indexOf("GC=F") >= 0;
    if (gold) {
      var b = null;
      try { b = fe83f_goldBits(); } catch (e) { b = null; }
      if (b && b.kind === "futures" && b.px != null) {
        var pct = b.pct == null ? "" : " (" + fe85_signed(b.pct, "%") + ")";
        return "Gold futures (GC=F) " + fe83f_px(b.px) + pct;
      }
      if (b && b.kind === "spot" && b.px != null) return "Gold spot " + fe83f_px(b.px);
    }
    return fe86_bit0.apply(this, arguments);
  };
} catch (eBit) {}
try {
  var fe86_tapeOnly0 = fe85_paintTapeOnly;
  fe85_paintTapeOnly = function () {
    try { fe86_fixTape(); } catch (e) {}
  };
} catch (eTo) {}
try {
  var fe86_pass0 = fe85_pass;
  fe85_pass = function () {
    var r;
    try { r = fe86_pass0.apply(this, arguments); } catch (e) { r = undefined; }
    try { fe86_paintStrip(); } catch (e2) {}
    try { fe86_paintCmd(); } catch (e3) {}
    return r;
  };
} catch (ePass) {}
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
    pure = app_text.split("// fe86-pure-begin", 1)[1].split("// fe86-pure-end", 1)[0]
    src = pure + r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
var cu = fe86_cmd("COPPER");
assert(cu && cu.label === "Copper futures (HG=F)" && cu.sym === "HG=F", "copper");
assert(fe86_cmd("HG=F").label === "Copper futures (HG=F)", "hg");
assert(fe86_cmd("SLV").sym === "SI=F", "silver");
assert(fe86_cmd("PLAT").label === "Platinum futures (PL=F)", "plat");
assert(fe86_cmd("PALLADIUM").label === "Palladium futures (PA=F)", "pall");
assert(fe86_cmd("NG").label === "Natural gas futures (NG=F)", "ng");
assert(fe86_cmd("WTI").sym === "CL=F", "wti");
assert(fe86_cmd("BRENT").sym === "BZ=F", "brent");
assert(fe86_cmd("XAU") == null && fe86_cmd("GC=F") == null, "gold not a metal fallback");
assert(fe86_srcGold("gold-api-spot-metal") === false, "metal source");
assert(fe86_srcGold("gold-api-spot-proxy") === true, "gold proxy");
assert(fe86_srcGold("gold-api-spot-proxy-browser") === true, "gold browser");
assert(fe86_srcGold("yahoo") === false, "yahoo");
assert(fe86_valOnly("\u2026") && fe86_valOnly("\u2014") && fe86_valOnly("  \u2026  ") && !fe86_valOnly("RISK+") && !fe86_valOnly("MIX"), "vals");
var html = '<div class="neural-strip"><div class="ns-cell ns-regime"><div><span class="ns-lbl">REGIME</span><span class="ns-val">Risk-On</span></div></div><div class="ns-cell ns-sector"><span class="ns-lbl">ROTATION</span><span class="ns-val">\u2026</span></div><div class="ns-cell"><span class="ns-lbl">LEAD</span><span class="ns-val">XLK +1.2%</span></div><div class="ns-cell"><span class="ns-lbl">LAG</span><span class="ns-val">\u2014</span></div><div class="ns-cell"><span class="ns-lbl">PRICED</span><span class="ns-val">12</span></div></div>';
var out = fe86_stripHtml(html);
assert(out.indexOf("ROTATION") < 0 && out.indexOf("LAG") < 0, "placeholders hidden");
assert(out.indexOf("XLK") >= 0 && out.indexOf("Risk-On") >= 0 && out.indexOf("PRICED") >= 0, "real cells stay");
var liveHtml = '<div class="ns-cell"><span class="ns-lbl">PRICED</span><span class="ns-val ns-live">\u2026</span></div><div class="ns-cell"><span class="ns-lbl">LIVE</span><span class="ns-val ns-live">5</span></div>';
var liveOut = fe86_stripHtml(liveHtml);
assert(liveOut.indexOf("PRICED") < 0 && liveOut.indexOf(">5<") >= 0, "ns-live placeholder");
assert(fe86_cmdLine("Copper futures (HG=F)", true, "Fri", "08:09 UK") === "Copper futures (HG=F) \u00b7 CLOSED \u00b7 Fri \u00b7 as of 08:09 UK", "cu line");
assert(fe86_cmdLine("Copper futures (HG=F)", false, "", "08:09 UK").indexOf("CLOSED") < 0, "open line");
assert(fe86_cmdLine("Copper futures (HG=F)", true, "Fri", "08:09 UK").indexOf("Gold") < 0, "no gold");
var row = fe86_goldRow("4,007.90", "\u00b7 -52.50 (-1.29%) Fri");
assert(row === "Gold 4,007.90 \u00b7 -52.50 (-1.29%) Fri", "gold row " + row);
assert(row.indexOf("3996") < 0 && row.indexOf("3,996") < 0, "no spot");
assert(fe86_needs("\u2014", "-1.20 (-0.40%) Fri") === true, "needs dash");
assert(fe86_needs("-0.40%", "-1.20 (-0.40%) Fri") === true, "needs points");
assert(fe86_needs("-0.40% Fri", "-0.40% Fri") === false, "same");
assert(fe86_needs("-1.20 (-0.40%) Fri", "-1.20 (-0.40%) Fri") === false, "full same");
console.log("fe86 unit ok");
"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe86 tests failed\n" + test.stdout + test.stderr)
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
    if index.count('app.js?v=chat85"') != 1:
        die("cache bust anchor missing")
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count(REFUSE_MARKER) != 1:
        die("refuse marker")
    if app.count("function fe86_cmd(") != 1 or app.count("function fe86_stripHtml(") != 1:
        die("pure defs")
    if "function fe84_dtfShim" not in app or not app.startswith("(function fe84_dtfShim(){"):
        die("shim moved")
    if app.count(NEED_MARKER) != 1:
        die("rt62h marker drifted")
    index = index.replace('app.js?v=chat85"', 'app.js?v=chat86"', 1)
    if index.count('app.js?v=chat86"') != 1 or "chat85" in index:
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
