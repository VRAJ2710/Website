#!/usr/bin/env python3
"""patch_rt53.py: chatN -> chatN+1 (client only). Stacks on live chat56 (app.js sha256 27f7cbcb44bf683c, rt51 on top).

Home stops rebuilding the hidden four-panel desk, and the 26 news feeds wait until the desk
or the news panel is opened. Home gains a macro signal grid (bb1): gold, the dollar, the US
real yield, the US 10-year, VIX, Brent, WTI, Bitcoin. The real yield is read from /api/real-yield
(deploy/patch_rt53s.py — a cached FRED proxy, no new table). bb1 is this script, not a separate
patch_rt53b.py.

Retarget when rebasing onto rt52 (that patch takes chat56 -> chat57; this one should then
expect chat57 -> chat58). Change only these two lines:
  MIN_CHAT = 57
  EXPECT_SHA16 = "<first 16 hex chars of sha256(app.js) before this patch>"
Set EXPECT_SHA16 = "" to skip the hash check. The cache-buster bump stays chatN -> chatN+1.

Usage: python3 patch_rt53.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

# ── retarget these when rt52 has landed (chat57 -> chat58) ──
MIN_CHAT = 56
EXPECT_SHA16 = "27f7cbcb44bf683c"  # "" skips; first 16 of sha256 of app.js BEFORE this patch
NEED_MARKER = "// ── rt51 ──"      # the release this patch stacks on

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
raw = open(APP, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt53 ──' in s: die('rt53 already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
sha = hashlib.sha256(raw).hexdigest()
if EXPECT_SHA16 and not sha.startswith(EXPECT_SHA16):
    die('app.js sha256 %s does not start with %s (set EXPECT_SHA16 to %s, or to empty to skip)' % (sha[:16], EXPECT_SHA16, sha[:16]))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < MIN_CHAT: die('index is %s; expected chat%d or later' % (base, MIN_CHAT))
print('base:', base, 'sha256', sha[:16], '->', nxt)

def sub1(src, old, new, label):
    c = src.count(old)
    if c != 1: die('%s matched %d times' % (label, c))
    return src.replace(old, new, 1)

# Freeze fix 1 — doTick, and every desktop branch of _fetchLivePrices (three; the third is the
# priHits===0 fallback). Home keeps painting through _paintFrontDoorQuotes. The command-bar
# chip is _rtRecountStatus, which already runs on its own 2s pass.
SKIP = 'if(!(typeof _rt53HomeOn==="function"&&_rt53HomeOn()))renderTerminalPanels();'
s = sub1(s,
'''      }else{
        renderTerminalPanels();
      }
    } else {
      // MOBILE: never full renderMain() here''',
'''      }else{
        %s
      }
    } else {
      // MOBILE: never full renderMain() here''' % SKIP,
'doTick renderTerminalPanels')
s = sub1(s,
'''      else renderTerminalPanels();
      _patchLiveDataIfNeeded(); _patchCuratedPrices();''',
'''      else { %s }
      _patchLiveDataIfNeeded(); _patchCuratedPrices();''' % SKIP,
'prices primary renderTerminalPanels')
s = sub1(s,
'''        else renderTerminalPanels();
        _patchLiveDataIfNeeded();
      }
      else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();''',
'''        else { %s }
        _patchLiveDataIfNeeded();
      }
      else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();''' % SKIP,
'prices fallback renderTerminalPanels')
s = sub1(s,
'''    }else{
      renderTerminalPanels();
    }
  }
  if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  if(pg==="brief"||pg==="dash"||pg==="home"){ try{ _refreshBriefSurfaces(); }catch(e){} }
}''',
'''    }else{
      %s
    }
  }
  if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  if(pg==="brief"||pg==="dash"||pg==="home"){ try{ _refreshBriefSurfaces(); }catch(e){} }
}''' % SKIP,
'prices final renderTerminalPanels')

# Freeze fix 4 — the boot call runs before any later wrapper, and the interval captured the
# function itself. Both have to change here. A refresh button still calls fetchLiveNews().
s = sub1(s,
'''fetchLiveNews();
// Crypto loads lazily on first visit to the Crypto page (see nav()).''',
'''/* rt53: the news feeds wait until the desk or the news panel is opened */
// Crypto loads lazily on first visit to the Crypto page (see nav()).''',
'boot fetchLiveNews')
s = sub1(s,
'setInterval(fetchLiveNews, isMobile ? MOBILE_NEWS_FREQ * 1000 : 600000);',
'setInterval(() => { try { if (typeof _rt53NewsOn !== "undefined" && _rt53NewsOn) fetchLiveNews(); } catch (e) {} }, isMobile ? MOBILE_NEWS_FREQ * 1000 : 600000);',
'news interval')
# A fetch that finishes while Home is up must not rebuild the hidden news panel.
s = sub1(s,
'''  if(IS_DESKTOP()&&!termSelTk&&!_dynTk){
    renderP2();''',
'''  if(IS_DESKTOP()&&!termSelTk&&!_dynTk&&!(typeof _rt53HomeOn==="function"&&_rt53HomeOn())){
    renderP2();''',
'fetchLiveNews renderP2')

# bb1 mounts: guest front door, and signed-in Home under the hero tape.
s = sub1(s,
'''function _frontDoorQuotesHtml() {
  return _frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index");
}''',
'''function _frontDoorQuotesHtml() {
  return (typeof _rt53GridHtml === "function") ? _rt53GridHtml() : (_frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index"));
}''',
'front door quotes')
s = sub1(s,
'''    : _rt20TapeFallback(re)}</div>
  </div>`;

  // ── Today's brief ──''',
'''    : _rt20TapeFallback(re)}</div>
  </div>`;
  if (typeof _rt53GridHtml === "function") h += _rt53GridHtml();

  // ── Today's brief ──''',
'renderHome macro grid')
# Quote ticks already repaint the front door. Include the rest of the grid, still not doTick.
s = sub1(s,
'if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG"))) {',
'if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG") || dirty.has("VIX") || dirty.has("TNX") || dirty.has("BRENT") || dirty.has("WTI") || dirty.has("BTC"))) {',
'home quote paint')

BLOCK = r'''// ── rt53 ── Home no longer rebuilds the hidden desk. The news feeds start when the desk or the news panel
// is first opened. The macro grid (bb1) paints with the front door, including a daily US real yield.
function _rt53HomeOn() {
  try {
    if (document.body && document.body.classList.contains("front-door-mode")) return true;
    if (typeof pg === "string") return pg === "home";
    var ov = document.getElementById("homeOv");
    return !!(ov && ov.isConnected);
  } catch (e) { return false; }
}
var _rt53NewsOn = false, _rt53PanelsOnce = false, _rt53Ry = null;
// Anything else that still calls renderTerminalPanels while Home is the page (a layout change, a
// screener refresh) would rebuild the hidden desk. The three price-fetch branches and doTick also skip.
var _rt53RTP = renderTerminalPanels;
renderTerminalPanels = function () { if (_rt53HomeOn()) return; return _rt53RTP.apply(this, arguments); };
function _rt53FillPanels(page) {
  var sync = page === "mkt" || page === "news" || page === "sig" || page === "watch" || page === "anlz";
  if (_rt53PanelsOnce) { if (sync) { try { _rtRecountStatus(); } catch (e) {} } return; }
  var run = function () {
    if (_rt53PanelsOnce) return;
    _rt53PanelsOnce = true;
    try { if (typeof IS_DESKTOP === "function" && IS_DESKTOP()) renderTerminalPanels(); } catch (e) {}
    try { _rtRecountStatus(); } catch (e) {}
  };
  if (typeof IS_DESKTOP === "function" && !IS_DESKTOP()) { _rt53PanelsOnce = true; try { _rtRecountStatus(); } catch (e) {} return; }
  if (sync) run();
  else if (typeof requestIdleCallback === "function") requestIdleCallback(run, { timeout: 1200 });
  else setTimeout(run, 350);
}
var _rt53Desk = { dash: 1, mkt: 1, news: 1, sig: 1, watch: 1, anlz: 1, scr: 1, paper: 1 };
function _rt53ArmNews(page) {
  if (!_rt53Desk[page]) return;
  _rt53NewsOn = true;
  try { if (typeof newsLastFetch !== "undefined" && !newsLastFetch && !newsFetching) fetchLiveNews(); } catch (e) {}
}
var _rt53Nav = nav;
nav = function (p) {
  var from = (typeof pg === "string") ? pg : "";
  var out = _rt53Nav.apply(this, arguments);
  try {
    if (p && p !== "home") {
      _rt53ArmNews(p);
      if (from === "home" || _rt53Desk[p]) _rt53FillPanels(p);
    }
  } catch (e) {}
  return out;
};
function _rt53Esc(v) { try { return _escHtml(v == null ? "" : String(v)); } catch (e) { return String(v == null ? "" : v).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); } }
function _rt53Uk(ms) {
  if (!ms) return "";
  try { return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms)) + " UK"; }
  catch (e) { return ""; }
}
function _rt53UkDate(iso) {
  try {
    var p = String(iso).split("-"), y = +p[0], m = +p[1], d = +p[2];
    if (!y || !m || !d) return "";
    return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short", year: "numeric" }).format(new Date(Date.UTC(y, m - 1, d, 12)));
  } catch (e) { return ""; }
}
function _rt53Pp(n) { if (n == null || !isFinite(Number(n))) return ""; var v = Math.round(Number(n) * 100) / 100; var s = v > 0 ? "+" : v < 0 ? "\u2212" : ""; return s + Math.abs(v).toFixed(2); }
function _rt53Pct(n) { if (n == null || !isFinite(Number(n))) return ""; var v = Number(n); var s = v > 0 ? "+" : v < 0 ? "\u2212" : ""; return s + Math.abs(v).toFixed(2) + "%"; }
function _rt53Open(tk) { try { return !!_rt18MarketOpen(tk); } catch (e) { return true; } }
function _rt53Src(tk) {
  var src = ""; try { src = (liveQuoteSrc && liveQuoteSrc[tk]) || ""; } catch (e) {}
  if (tk === "XAU") return /gold-api|spot/i.test(src) ? "Spot gold" : "COMEX";
  if (tk === "DXY") return "ICE";
  if (tk === "BTC") { if (src === "coinbase-ws") return "Coinbase"; if (src === "kraken-ws") return "Kraken"; return "Market price"; }
  if (tk === "BRENT") return "ICE Brent";
  if (tk === "WTI") return "NYMEX";
  if (tk === "VIX" || tk === "TNX") return "CBOE";
  return "Market price";
}
function _rt53Status(tk) {
  var open = _rt53Open(tk);
  if (tk === "BRENT") return open ? "ICE open \u00b7 delayed" : "ICE closed \u00b7 delayed";
  if (tk === "WTI") return open ? "NYMEX open \u00b7 delayed" : "NYMEX closed \u00b7 delayed";
  if (tk === "XAU") return open ? "COMEX open" : "COMEX closed";
  if (tk === "DXY") return open ? "Dollar trading" : "Dollar closed";
  if (tk === "VIX" || tk === "TNX") return open ? "CBOE open" : "CBOE closed";
  if (tk === "BTC") return "Trading";
  return open ? "Open" : "Closed";
}
function _rt53Row(tk) {
  try {
    if (typeof hasSyncedQuote !== "function" || !hasSyncedQuote(tk)) return null;
    var d = fp(tk);
    var prev = (typeof BASE !== "undefined" && BASE[tk] && BASE[tk].p > 0) ? BASE[tk].p : null;
    var pts = (prev != null && P[tk] && isFinite(P[tk].p)) ? (P[tk].p - prev) : null;
    return { text: d.p, pct: (typeof liveChg === "function") ? liveChg(tk) : null, pts: pts, asOf: d.asOf || null };
  } catch (e) { return null; }
}
var _rt53Tiles = [
  ["gold", "XAU", "Gold", "The metal this desk is built around. It tends to firm when real yields fall, or when investors want an asset that is nobody\u2019s liability.", "pct"],
  ["dollar", "DXY", "Dollar", "A dearer dollar usually makes gold more expensive for buyers outside America.", "pct"],
  ["real", "", "US real yield", "The interest given up by holding gold, which pays none. When this rises, gold has to work harder.", "real"],
  ["us10", "TNX", "US 10-year", "The bond market\u2019s price of money, and the rate that tugs on everything else.", "yield"],
  ["vix", "VIX", "VIX", "What investors are paying to insure against a sharp fall in American shares.", "pct"],
  ["brent", "BRENT", "Brent", "The oil price most of the world actually pays, and a direct feed into inflation.", "pct"],
  ["wti", "WTI", "WTI", "The American crude benchmark. It usually travels with Brent; US supply can pull them apart.", "pct"],
  ["btc", "BTC", "Bitcoin", "A read on risk appetite. It has been trading with technology shares more often than with gold.", "pct"]
];
function _rt53One(spec) {
  var id = spec[0], tk = spec[1], name = spec[2], why = spec[3], kind = spec[4];
  var value = "\u2014", change = "", cls = "", meta = "";
  if (kind === "real") {
    var y = _rt53Ry;
    if (y && isFinite(y.value)) {
      value = (Math.round(y.value * 100) / 100).toFixed(2) + "%";
      var c = isFinite(y.change) ? y.change : (isFinite(y.prev) ? y.value - y.prev : null);
      if (c != null && isFinite(c)) { change = _rt53Pp(c); cls = c > 0 ? "bb1-up" : c < 0 ? "bb1-dn" : ""; change += ' <span class="bb1-day">on the day</span>'; }
      meta = "Daily official print \u00b7 US Treasury \u00b7 " + (_rt53UkDate(y.date) || "latest print");
    } else meta = "Daily official print \u00b7 US Treasury";
  } else {
    var row = _rt53Row(tk);
    if (!row) meta = "Awaiting a price \u00b7 " + _rt53Src(tk);
    else {
      value = kind === "yield" ? String(row.text).replace(/%$/, "") + "%" : String(row.text);
      var ch = kind === "yield" ? row.pts : row.pct;
      var shown = kind === "yield" ? _rt53Pp(ch) : _rt53Pct(ch);
      if (shown) { change = shown; cls = ch > 0 ? "bb1-up" : ch < 0 ? "bb1-dn" : ""; if (kind === "yield") change += ' <span class="bb1-day">on the day</span>'; }
      var asOf = _rt53Uk(row.asOf), st = _rt53Status(tk), srcName = _rt53Src(tk);
      if (st.indexOf(srcName.split(" ")[0]) === 0) srcName = "";
      meta = [st, srcName, asOf].filter(Boolean).join(" \u00b7 ");
    }
  }
  return '<article class="bb1-tile" data-bb1-tile="' + id + '"><div class="bb1-k">' + _rt53Esc(name) + '</div><div class="bb1-v">' + _rt53Esc(value) +
    (change ? ' <span class="bb1-c ' + cls + '">' + change + '</span>' : '') + '</div><p class="bb1-why">' + _rt53Esc(why) + '</p><div class="bb1-meta">' + _rt53Esc(meta) + '</div></article>';
}
function _rt53Inner() { return '<div class="bb1-h">Macro</div><div class="bb1-grid">' + _rt53Tiles.map(_rt53One).join("") + '</div>'; }
function _rt53GridHtml() { return '<section class="bb1-sec" data-bb1 aria-label="Macro signals">' + _rt53Inner() + '</section>'; }
var _rt53Paint0 = _paintFrontDoorQuotes;
_paintFrontDoorQuotes = function () {
  var ok = false;
  try { ok = !!_rt53Paint0.apply(this, arguments); } catch (e) {}
  try {
    if (typeof pg === "undefined" || pg === "home") {
      var html = _rt53Inner();
      document.querySelectorAll("[data-bb1]").forEach(function (el) { if (el.innerHTML !== html) el.innerHTML = html; });
      if (document.querySelector("[data-bb1]")) ok = true;
    }
  } catch (e) {}
  return ok;
};
function _rt53RyStart() {
  var go = function () {
    fetch("/api/real-yield", { credentials: "same-origin", signal: AbortSignal.timeout(12000) }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || j.available === false || !isFinite(Number(j.value)) || !j.date) return;
      _rt53Ry = { value: Number(j.value), prev: j.prev == null || !isFinite(Number(j.prev)) ? null : Number(j.prev), change: j.change == null || !isFinite(Number(j.change)) ? null : Number(j.change), date: String(j.date) };
      try { if (typeof pg === "undefined" || pg === "home") _paintFrontDoorQuotes(); } catch (e) {}
    }).catch(function () {});
  };
  if (typeof requestIdleCallback === "function") requestIdleCallback(go, { timeout: 2500 });
  else setTimeout(go, 1200);
}
try { if (typeof pg === "string" && pg !== "home") { _rt53ArmNews(pg); _rt53FillPanels(pg); } } catch (e) {}
try { if (typeof newsFetching !== "undefined" && newsFetching) _rt53NewsOn = true; } catch (e) {}
_rt53RyStart();
(function () { try { var st = document.createElement("style"); st.setAttribute("data-rt53", ""); st.textContent = '.bb1-sec{margin:16px 0 8px}.bb1-h{margin:0 0 8px;font:800 10px/1.3 var(--mn,ui-monospace);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3,#8b909a)}.bb1-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--rule,#2a2e36);border:1px solid var(--rule,#2a2e36)}.bb1-tile{background:var(--paper,#14151A);color:var(--ink,#EDEDE8);padding:11px 12px 12px;min-width:0}.bb1-k{font:700 10px/1.2 var(--ui,system-ui);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2,#A8ADB6)}.bb1-v{margin-top:5px;font:500 20px/1.15 var(--data,ui-monospace);font-variant-numeric:tabular-nums;color:var(--ink,#EDEDE8)}.bb1-c{font:500 12px/1 var(--data,ui-monospace);margin-left:4px}.bb1-day{font:400 10px/1 var(--ui,system-ui);letter-spacing:0;color:var(--ink-3,#8b909a);margin-left:3px}.bb1-up{color:var(--pos,#3fbf7f)}.bb1-dn{color:var(--neg,#e05a5a)}.bb1-why{margin:8px 0 0;color:var(--ink-2,#C5C8CE);font:400 12px/1.45 var(--ui,system-ui)}.bb1-meta{margin-top:8px;color:var(--ink-3,#8b909a);font:400 10px/1.4 var(--data,ui-monospace)}.front-door-quotes:has(.bb1-sec){display:block;background:transparent;gap:0}.front-door-quotes>.bb1-sec{grid-column:1 / -1}@media(min-width:768px){.bb1-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.bb1-v{font-size:22px}}'; document.head.appendChild(st); } catch (e) {} })();
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt53: anchors + block; index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
