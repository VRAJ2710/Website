#!/usr/bin/env python3
"""patch_rt59b.py: client patch on chat71. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat71, the output of patch_rt59.py:
  app.js md5 52f89956f8479aac3f251e89de789ca9
  index.html md5 7d692ede20c7b018ed1f9a012fe299af
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

The phone All-sections sheet and the bottom bar are redrawn. Desktop is left
on the sidebar. New fields and handlers use the fe71_ prefix.

Usage: python3 patch_rt59b.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "52f89956f8479aac3f251e89de789ca9"
EXPECT_INDEX_MD5 = "7d692ede20c7b018ed1f9a012fe299af"
NEED_MARKER = "// \u2500\u2500 rt59 \u2500\u2500"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// \u2500\u2500 rt59b \u2500\u2500' in s: already('rt59b already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
md5 = hashlib.md5(raw).hexdigest()
imd5 = hashlib.md5(raw_idx).hexdigest()
if md5 != EXPECT_APP_MD5:
    print('WARN md5 app.js: have %s expected %s (anchors still decide)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    print('WARN md5 index.html: have %s expected %s (anchors still decide)' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust matched %d times' % len(v))
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
print('base:', base, 'app.md5', md5, 'index.md5', imd5, '->', nxt)

def subn(src, old, new, label, n=1):
    c = src.count(old)
    if c != n: die('%s matched %d times' % (label, c))
    return src.replace(old, new)

for name in ('function openMoreNav()', 'function closeMoreNav()', 'function renderNav()'):
    if s.count(name) != 1: die('%s matched %d times' % (name, s.count(name)))

BLOCK = r"""// ── rt59b ──
// Phone "All sections" sheet and the bottom bar. Desktop rules stay in the
// stylesheet's min-width:768 block; everything visual here is max-width 767.
function fe71_esc(s) {
  if (typeof _escHtml === "function") return _escHtml(s);
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function fe71_motion() {
  try { return !window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return true; }
}
function fe71_ico(id) {
  var path = "";
  try { path = (typeof NAV_ICONS !== "undefined" && NAV_ICONS[id]) || ""; } catch (e) { path = ""; }
  if (!path && id === "ask") path = '<path d="M5 6.5h14a1.5 1.5 0 011.5 1.5v7a1.5 1.5 0 01-1.5 1.5H9l-4 3v-3H5a1.5 1.5 0 01-1.5-1.5V8A1.5 1.5 0 015 6.5z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/>';
  if (!path && id === "lock") path = '<rect x="7" y="11" width="10" height="8" rx="1.5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M9 11V8.2a3 3 0 016 0V11" stroke="currentColor" stroke-width="1.8" fill="none"/>';
  return '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">' + path + "</svg>";
}
var FE71_BLURB = {
  home: "Where the desk stands today",
  brief: "Today's house view, in one page",
  playbook: "The week's plan for gold",
  gold: "Gold prices, and what is moving them",
  ask: "Ask a question about these markets",
  dash: "The whole desk on one screen",
  lab: "Test one idea against the prices",
  sig: "What the desk is watching most closely",
  mkt: "Prices for shares, metals and currencies",
  scr: "Find shares that match a rule you set",
  sectors: "Which parts of the market are leading",
  heat: "Which sectors are moving today",
  crypto: "Bitcoin and the main coins, in one place",
  news: "Headlines, tied to the prices",
  paper: "Longer notes from the desk",
  research: "Reports you can read in full",
  intel: "Filings and papers, read for you",
  geo: "Wars, shipping lanes and political risk",
  watch: "The names you chose to follow",
  port: "What you hold, and how it moved",
  learn: "Short lessons on how markets work",
  settings: "Time zone, alerts and your account"
};
var FE71_LOCK = { playbook: 1, scr: 1, intel: 1, ask: 1 };
function fe71_locked(id) {
  if (!FE71_LOCK[id]) return false;
  try { if (typeof _isPremium === "function" && _isPremium()) return false; } catch (e) {}
  return true;
}
function fe71_who() {
  var signed = false, admin = false, prem = false, email = "";
  try { signed = typeof _userSignedIn !== "undefined" && _userSignedIn === true && typeof _userTierReady !== "undefined" && _userTierReady; } catch (e) {}
  try { admin = typeof _userAdmin !== "undefined" && _userAdmin === true; } catch (e2) {}
  try { prem = typeof _isPremium === "function" && _isPremium(); } catch (e3) {}
  try { email = String(window._tdMeEmail || ""); } catch (e4) {}
  if (!signed) return { guest: true, admin: false, plan: "", name: "", initials: "" };
  var local = email.split("@")[0] || "Member";
  var name = local.replace(/[._+-]+/g, " ").replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); });
  var bits = name.split(" ").filter(Boolean);
  var initials = ((bits[0] && bits[0][0]) || "M") + (bits[1] ? bits[1][0] : ((bits[0] && bits[0][1]) || ""));
  return { guest: false, admin: admin, plan: prem ? "Premium" : "Free", name: name, initials: initials.toUpperCase() };
}
function fe71_sessionLine() {
  var parts = [];
  try {
    var open = typeof _rt18MarketOpen === "function" && _rt18MarketOpen("AAPL");
    if (open) parts.push("US stocks open");
    else {
      var when = "";
      if (typeof _rt51Next === "function" && typeof _rt51When === "function") {
        var nx = _rt51Next("AAPL");
        when = nx ? _rt51When(nx) : "";
      }
      parts.push(when ? ("US stocks open " + when) : "US stocks closed");
    }
  } catch (e) {}
  try {
    var live = true;
    if (typeof _rt18MarketOpen === "function") live = _rt18MarketOpen("BTC") !== false;
    parts.push(live ? "crypto live" : "crypto quiet");
  } catch (e2) { parts.push("crypto live"); }
  return parts.join(" · ");
}
function fe71_label(id, fallback) {
  try { if (typeof NAV_LABELS !== "undefined" && NAV_LABELS[id]) return NAV_LABELS[id]; } catch (e) {}
  return fallback || id;
}
function fe71_tile(id, label, group) {
  var blurb = FE71_BLURB[id] || "";
  var on = (typeof pg !== "undefined" && pg === id) ? " on" : "";
  var lock = fe71_locked(id);
  var hay = (group + " " + label + " " + blurb).toLowerCase();
  var al = label + (blurb ? ". " + blurb : "") + (lock ? ". Premium" : "");
  return '<button type="button" class="fe71-tile' + on + '" data-fe71="' + fe71_esc(id) + '" data-fe71-item="1" data-fe71-hay="' + fe71_esc(hay) + '" aria-label="' + fe71_esc(al) + '"' + (on ? ' aria-current="page"' : "") + ">" +
    '<span class="fe71-ico">' + fe71_ico(id) + "</span>" +
    '<span class="fe71-copy"><span class="fe71-t">' + fe71_esc(label) + "</span>" +
    (blurb ? '<span class="fe71-d">' + fe71_esc(blurb) + "</span>" : "") +
    "</span>" +
    (lock ? '<span class="fe71-lock" title="Premium">' + fe71_ico("lock") + "</span>" : "") +
    "</button>";
}
function fe71_groups() {
  var groups = [];
  try {
    (NAV_GROUPS || []).forEach(function (gr) {
      var items = [];
      (gr.items || []).forEach(function (it) {
        items.push([it[0], it[1]]);
        (it[2] || []).forEach(function (s) { items.push([s[0], s[1]]); });
      });
      groups.push({ g: gr.g, items: items });
    });
  } catch (e) {}
  groups.push({ g: "Account", items: [["settings", "Settings"]] });
  return groups;
}
function fe71_sheetHtml() {
  var who = fe71_who();
  var pins = [["home", "Home"], ["brief", "Brief"], ["playbook", "Playbook"], ["gold", "Gold"], ["ask", "Ask"]];
  var pinHtml = pins.map(function (p) { return fe71_tile(p[0], p[1], "pin"); }).join("");
  var groups = fe71_groups().map(function (gr) {
    return '<section class="fe71-grp" data-fe71-group="' + fe71_esc(gr.g) + '"><h3>' + fe71_esc(gr.g) + "</h3><div class=\"fe71-grid\">" +
      gr.items.map(function (it) { return fe71_tile(it[0], it[1], gr.g); }).join("") +
      "</div></section>";
  }).join("");
  var ident = who.guest
    ? '<div class="fe71-id"><span class="fe71-ava" aria-hidden="true">?</span><div><div class="fe71-name">Sign in to the desk</div><div class="fe71-planrow"><a href="/__auth/login">Sign in</a><a href="/__auth/register">Create free account</a></div></div></div>'
    : '<div class="fe71-id"><span class="fe71-ava" aria-hidden="true">' + fe71_esc(who.initials) + '</span><div><div class="fe71-name">' + fe71_esc(who.name) + '</div><div class="fe71-planrow"><span class="fe71-plan">' + fe71_esc(who.plan) + "</span>" +
      (who.admin ? '<span class="fe71-admin">Admin</span>' : "") + "</div></div></div>";
  var line = fe71_sessionLine();
  return '<div class="more-nav-scrim" data-fe71-scrim="1"></div>' +
    '<div class="more-nav-panel" role="document">' +
    '<div class="fe71-swipe"><div class="fe71-grab" aria-hidden="true"></div>' +
    '<div class="fe71-head"><h2 id="fe71-title">Sections</h2>' + ident +
    '<button type="button" class="more-nav-x fe71-x" data-fe71-x="1" aria-label="Close all sections">×</button></div></div>' +
    (line ? '<p class="fe71-session">' + fe71_esc(line) + "</p>" : "") +
    '<label class="fe71-search"><input class="fe71-find" type="search" enterkeyhint="search" placeholder="Find a section" aria-label="Find a section" autocomplete="off"></label>' +
    '<div class="fe71-pin" aria-label="Home, Brief, Playbook, Gold and Ask">' + pinHtml + "</div>" +
    groups +
    '<p class="fe71-empty" hidden>Nothing matches. Try Heatmap, Gold or Brief.</p>' +
    "</div>";
}
function fe71_filter(sheet, raw) {
  var q = String(raw || "").trim().toLowerCase();
  var shown = 0;
  sheet.querySelectorAll("[data-fe71-item]").forEach(function (el) {
    var hay = el.getAttribute("data-fe71-hay") || "";
    var on = !q || hay.indexOf(q) >= 0;
    el.hidden = !on;
    if (on) shown++;
  });
  sheet.querySelectorAll("[data-fe71-group]").forEach(function (g) {
    var any = false;
    g.querySelectorAll("[data-fe71-item]").forEach(function (el) { if (!el.hidden) any = true; });
    g.hidden = !any;
  });
  var empty = sheet.querySelector(".fe71-empty");
  if (empty) empty.hidden = shown !== 0;
}
function fe71_go(id) {
  if (id === "ask") {
    closeMoreNav();
    try { _openResearchAssistant("What matters most in markets right now?"); } catch (e) {}
    return;
  }
  if (id === "settings") {
    closeMoreNav();
    try { openSettings(); } catch (e2) {}
    return;
  }
  if (typeof _moreNavGo === "function") _moreNavGo(id);
  else { closeMoreNav(); try { nav(id); } catch (e3) {} }
}
function fe71_lock() {
  try {
    document.documentElement.classList.add("fe71-lock");
    document.body.classList.add("fe71-lock");
  } catch (e) {}
}
function fe71_unlock() {
  try {
    document.documentElement.classList.remove("fe71-lock");
    document.body.classList.remove("fe71-lock");
    if (document.body.classList.contains("fe70-home")) {
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
      document.body.style.position = "";
      document.body.style.top = "";
      document.body.style.width = "";
    }
  } catch (e) {}
}
function fe71_swipe(panel) {
  var zone = panel.querySelector(".fe71-swipe");
  if (!zone) return;
  var y0 = 0, dy = 0, drag = false;
  zone.addEventListener("pointerdown", function (e) {
    if (e.target.closest("button, a, input, label")) return;
    drag = true; y0 = e.clientY; dy = 0;
    if (fe71_motion()) panel.style.transition = "none";
    try { zone.setPointerCapture(e.pointerId); } catch (err) {}
  });
  zone.addEventListener("pointermove", function (e) {
    if (!drag) return;
    dy = e.clientY - y0;
    if (dy < 0) dy = 0;
    if (fe71_motion()) panel.style.transform = "translate3d(0," + dy + "px,0)";
  });
  function fe71_swipeEnd() {
    if (!drag) return;
    drag = false;
    panel.style.transition = "";
    panel.style.transform = "";
    if (dy > 72) closeMoreNav();
  }
  zone.addEventListener("pointerup", fe71_swipeEnd);
  zone.addEventListener("pointercancel", fe71_swipeEnd);
}
function fe71_wire(sheet) {
  var scrim = sheet.querySelector("[data-fe71-scrim]");
  if (scrim) scrim.addEventListener("click", function () { closeMoreNav(); });
  var x = sheet.querySelector("[data-fe71-x]");
  if (x) x.addEventListener("click", function () { closeMoreNav(); });
  sheet.addEventListener("click", function (e) {
    var b = e.target.closest("[data-fe71]");
    if (!b || !sheet.contains(b)) return;
    fe71_go(b.getAttribute("data-fe71"));
  });
  var inp = sheet.querySelector(".fe71-find");
  if (inp) {
    inp.addEventListener("input", function () { fe71_filter(sheet, inp.value); });
    inp.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var vis = [];
      sheet.querySelectorAll("[data-fe71-item]").forEach(function (el) { if (!el.hidden) vis.push(el); });
      if (vis.length === 1) { e.preventDefault(); vis[0].click(); }
    });
  }
  fe71_swipe(sheet.querySelector(".more-nav-panel"));
}
function fe71_openMoreNav() {
  try { if (window.innerWidth >= 768) return; } catch (e0) {}
  try { if (_moreNavCloseTimer) { clearTimeout(_moreNavCloseTimer); _moreNavCloseTimer = null; } } catch (e) {}
  _moreNavOpen = true;
  var trigger = document.querySelector("[data-more-nav-trigger]");
  if (trigger) trigger.setAttribute("aria-expanded", "true");
  var sheet = document.getElementById("moreNav");
  if (!sheet) {
    sheet = document.createElement("div");
    sheet.id = "moreNav";
    document.body.appendChild(sheet);
  }
  sheet.className = "more-nav fe71";
  sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-modal", "true");
  sheet.setAttribute("aria-labelledby", "fe71-title");
  sheet.setAttribute("aria-label", "All sections");
  sheet.setAttribute("tabindex", "-1");
  sheet.setAttribute("aria-hidden", "false");
  sheet.innerHTML = fe71_sheetHtml();
  fe71_wire(sheet);
  fe71_lock();
  void sheet.offsetWidth;
  sheet.classList.add("on");
  try { document.addEventListener("keydown", _onMoreNavKeydown); } catch (e2) {}
  var focus = sheet.querySelector(".fe71-find") || sheet.querySelector(".fe71-x");
  try { if (focus) focus.focus(); } catch (e3) {}
}
function fe71_closeMoreNav() {
  if (!_moreNavOpen) return;
  _moreNavOpen = false;
  fe71_unlock();
  var sheet = document.getElementById("moreNav");
  try { document.removeEventListener("keydown", _onMoreNavKeydown); } catch (e) {}
  if (sheet) {
    sheet.setAttribute("aria-hidden", "true");
    sheet.classList.remove("on");
    var wait = fe71_motion() ? 420 : 0;
    _moreNavCloseTimer = setTimeout(function () {
      try { sheet.remove(); } catch (e2) {}
      _moreNavCloseTimer = null;
    }, wait);
  }
  var trigger = document.querySelector("[data-more-nav-trigger]");
  if (trigger) trigger.setAttribute("aria-expanded", "false");
  try { renderNav(); } catch (e3) {}
  try { if (trigger) trigger.focus(); } catch (e4) {}
}
function fe71_bar() {
  var el = document.getElementById("bnav");
  if (!el) return;
  el.classList.add("fe71-bar");
  el.querySelectorAll(".nav-lock").forEach(function (n) {
    if (n.querySelector("svg")) return;
    n.innerHTML = fe71_ico("lock");
  });
  var h = 0;
  try { h = el.offsetHeight || 0; } catch (e) {}
  if (h < 44) h = 64;
  var px = h + "px";
  try {
    document.documentElement.style.setProperty("--fe71-bar", px);
    document.documentElement.style.setProperty("--rt47bn", px);
  } catch (e2) {}
}
function fe71_renderNav() {
  fe71_renderNav0.apply(this, arguments);
  try { fe71_bar(); } catch (e) {}
}
function fe71_css() {
  if (document.getElementById("fe71-css")) return;
  var st = document.createElement("style");
  st.id = "fe71-css";
  st.textContent = [
    "html.fe71-lock,body.fe71-lock,body.fe70-home.fe71-lock{overflow:hidden!important;overscroll-behavior:none}",
    ".fe71{position:fixed;inset:0;z-index:420}",
    ".fe71 .more-nav-scrim{position:absolute;inset:0;background:rgba(6,6,8,.88);-webkit-backdrop-filter:blur(18px);backdrop-filter:blur(18px);opacity:0;transition:opacity .28s ease}",
    ".fe71.more-nav.on .more-nav-scrim{opacity:1}",
    ".fe71 .more-nav-panel{position:absolute;left:0;right:0;bottom:0;max-height:min(92dvh,calc(100dvh - env(safe-area-inset-top,0px) - 8px));overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;background:rgba(14,14,16,.96);-webkit-backdrop-filter:blur(22px);backdrop-filter:blur(22px);border-radius:20px 20px 0 0;border-top:1px solid rgba(217,174,82,.55);box-shadow:0 -28px 60px rgba(0,0,0,.55);padding:0 14px calc(16px + env(safe-area-inset-bottom,0px));transform:translate3d(0,110%,0);opacity:1;transition:transform .46s cubic-bezier(.22,1.12,.36,1)}",
    ".fe71.more-nav.on .more-nav-panel{transform:translate3d(0,0,0)}",
    ".fe71-grab{width:40px;height:4px;border-radius:4px;background:rgba(237,237,232,.38);margin:10px auto 6px}",
    ".fe71-swipe{touch-action:none;padding-bottom:4px}",
    ".fe71-head{display:flex;align-items:flex-start;gap:10px}",
    ".fe71-head h2{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}",
    ".fe71-id{display:flex;gap:10px;align-items:center;min-width:0;flex:1}",
    ".fe71-ava{flex:none;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(217,174,82,.14);color:#E8C56B;border:1px solid rgba(217,174,82,.45);font:700 13px/1 var(--mn,ui-monospace,monospace)}",
    ".fe71-name{font:600 15px/1.2 var(--sf,Georgia,serif);color:var(--tx,#f2f0e9)}",
    ".fe71-planrow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:4px}",
    ".fe71-plan{font:700 10px/1 var(--mn,ui-monospace,monospace);letter-spacing:.12em;text-transform:uppercase;color:#E8C56B;border:1px solid rgba(217,174,82,.45);border-radius:99px;padding:3px 7px}",
    ".fe71-admin{font:700 10px/1 var(--mn,ui-monospace,monospace);letter-spacing:.12em;text-transform:uppercase;color:#f2f0e9;background:rgba(217,174,82,.18);border-radius:99px;padding:3px 7px}",
    ".fe71-planrow a{min-height:44px;display:inline-flex;align-items:center;padding:0 2px;color:#E8C56B;font:600 13px/1 var(--sn,system-ui);text-decoration:none;border-bottom:1px solid rgba(217,174,82,.4)}",
    ".fe71-x{flex:none;width:44px;height:44px;min-width:44px;min-height:44px;border:0;background:transparent;color:var(--t2,#b7b3a8);font-size:22px;cursor:pointer}",
    ".fe71-session{margin:8px 2px 0;font:12px/1.4 var(--mn,ui-monospace,monospace);color:var(--t2,#b7b3a8)}",
    ".fe71-search{display:block;margin:10px 0}",
    ".fe71-find{width:100%;box-sizing:border-box;min-height:44px;border-radius:12px;border:1px solid rgba(217,174,82,.28);background:rgba(255,255,255,.04);color:var(--tx,#f2f0e9);font:15px/1 var(--sn,system-ui);padding:0 12px}",
    ".fe71-find::placeholder{color:var(--t3,#8a867c)}",
    ".fe71-pin{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:2px 0 12px}",
    ".fe71-pin .fe71-tile{min-height:88px;flex-direction:column;align-items:flex-start;gap:6px}",
    ".fe71-pin .fe71-d{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}",
    ".fe71-grp{margin:4px 0 12px}",
    ".fe71-grp h3{margin:0 0 8px;font:700 11px/1 var(--mn,ui-monospace,monospace);letter-spacing:.14em;text-transform:uppercase;color:rgba(232,197,107,.8)}",
    ".fe71-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}",
    ".fe71-tile{position:relative;display:flex;align-items:flex-start;gap:8px;width:100%;min-height:44px;text-align:left;padding:10px;border-radius:14px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.03);color:var(--tx,#f2f0e9);cursor:pointer}",
    ".fe71-tile.on{background:rgba(217,174,82,.08);border-color:rgba(217,174,82,.7);box-shadow:0 0 0 1px rgba(217,174,82,.45),0 0 18px rgba(217,174,82,.28);color:#F3E2B0}",
    ".fe71-ico{flex:none;width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:rgba(217,174,82,.12);color:#E8C56B}",
    ".fe71-ico svg,.fe71-lock svg{width:18px;height:18px;display:block}",
    ".fe71-copy{display:flex;flex-direction:column;gap:2px;min-width:0}",
    ".fe71-t{font:600 13px/1.25 var(--sn,system-ui)}",
    ".fe71-d{font:12px/1.35 var(--sn,system-ui);color:var(--t2,#b7b3a8)}",
    ".fe71-lock{position:absolute;top:8px;right:8px;color:#E8C56B}",
    ".fe71-empty{margin:12px 4px 20px;color:var(--t2,#b7b3a8);font:14px/1.45 var(--sf,Georgia,serif)}",
    ".fe71 [hidden]{display:none!important}",
    ".fe71 button:focus-visible,.fe71 input:focus-visible,.fe71 a:focus-visible{outline:2px solid #E8C56B;outline-offset:2px}",
    "@media (max-width:767px){#bnav.fe71-bar{position:fixed;left:0;right:0;bottom:0;z-index:40;display:flex;background:rgba(12,12,14,.72);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-top:1px solid rgba(217,174,82,.28);padding-bottom:env(safe-area-inset-bottom,0px)}#bnav.fe71-bar button{position:relative;flex:1;min-height:48px;border-top-color:transparent!important;background:transparent;color:var(--t3,#8a867c);font-size:10px;font-weight:600;gap:3px}#bnav.fe71-bar button svg{width:18px;height:18px;position:relative;z-index:1}#bnav.fe71-bar button span{position:relative;z-index:1}#bnav.fe71-bar button.on{color:#E8C56B;background:transparent}#bnav.fe71-bar button.on::after{content:\"\";position:absolute;left:6px;right:6px;top:4px;bottom:4px;border-radius:14px;background:rgba(217,174,82,.16);box-shadow:0 0 14px rgba(217,174,82,.32);z-index:0;transition:opacity .22s ease,transform .22s ease}.main{padding-bottom:calc(var(--fe71-bar,68px) + 16px)!important}}",
    "@media (max-width:389px){#bnav.fe71-bar button{font-size:9px;padding-left:0;padding-right:0}.fe71-pin .fe71-t{font-size:12px}}",
    "@media (min-width:768px){#bnav.fe71-bar{position:sticky}.fe71{display:none!important}}",
    "@media (prefers-reduced-motion:reduce){.fe71 .more-nav-panel,.fe71 .more-nav-scrim,#bnav.fe71-bar button.on::after{transition:none!important;animation:none!important}}"
  ].join("");
  document.head.appendChild(st);
}
try { fe71_css(); } catch (e) {}
var fe71_renderNav0 = renderNav;
renderNav = fe71_renderNav;
openMoreNav = fe71_openMoreNav;
closeMoreNav = fe71_closeMoreNav;
function fe71_onResize() {
  try { if (window.innerWidth >= 768 && _moreNavOpen) fe71_closeMoreNav(); } catch (e) {}
  try { fe71_bar(); } catch (e2) {}
}
try { fe71_bar(); } catch (e) {}
try { window.addEventListener("resize", fe71_onResize, { passive: true }); } catch (e) {}
"""
if not s.endswith('\n'): s += '\n'
s = s + '\n' + BLOCK
if s.count('function fe71_openMoreNav') != 1: die('fe71_openMoreNav missing after append')
if 'fe71-bar' not in s: die('bottom bar class missing')
h = subn(h, 'app.js?v=%s"' % base, 'app.js?v=%s"' % nxt, 'cache bust')

def write(path, text, use_crlf):
    data = text.replace('\n', '\r\n').encode('utf-8') if use_crlf else text.encode('utf-8')
    open(path, 'wb').write(data)

if CHECK:
    print('CHECK ONLY')
    sys.exit(0)
write(APP, s, crlf)
write(IDX, h, hcrlf)
tmp = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False)
tmp.write(s); tmp.close()
r = subprocess.run(['node', '--check', tmp.name], capture_output=True, text=True)
os.unlink(tmp.name)
if r.returncode != 0:
    die('node --check failed\n' + (r.stderr or r.stdout or ''))
print('OK', nxt, 'app.md5', hashlib.md5(open(APP,'rb').read()).hexdigest(), 'index.md5', hashlib.md5(open(IDX,'rb').read()).hexdigest())
