#!/usr/bin/env python3
"""patch_rt53.py: client home freeze. Reads app.js?v=chatNN and writes chatNN+1.

The known live base is chat59 (bb3_ask then bb3_fit):
  app.js md5 d38b70eb458091fa69143f9fe3bfe193
  index.html md5 b15074aedc3261bf9e2ca611084082ba
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

Home stops rebuilding the hidden four-panel desk, and the 26 news feeds wait until the desk
or the news panel is opened. News tagging is memoized and regime keywords are computed once
per sort. The DXY/rt51 quote path caches its Intl formatters and as-of string. rt52's
Bitcoin-is-Crypto tag rule is left in place and only wrapped.

Home gains a macro signal grid (bb1): gold, the dollar, the US real yield, the US 10-year,
VIX, Brent, WTI, Bitcoin. The real yield is read from /api/real-yield (deploy/patch_rt53s.py).
bb1 is this script. There is no patch_rt53b.py.

The regime-fit card renders a server payload only (bb3). The client never computes a fit
score for that card, the lab control, or the basis sheet. Absent field: "Fit score not
available yet", with no number.

Usage: python3 patch_rt53.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "d38b70eb458091fa69143f9fe3bfe193"
EXPECT_INDEX_MD5 = "b15074aedc3261bf9e2ca611084082ba"
NEED_MARKER = "// ── rt52 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt53 ──' in s: already('rt53 already applied')
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
  try { if (typeof _rt53GridHtml === "function") { var g = _rt53GridHtml(); if (g) return g; } } catch (e) {}
  return _frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index");
}''',
'front door quotes')
s = sub1(s,
'''    : _rt20TapeFallback(re)}</div>
  </div>`;

  // ── Today's brief ──''',
'''    : _rt20TapeFallback(re)}</div>
  </div>`;
  try { if (typeof _rt53GridHtml === "function") h += _rt53GridHtml() || ""; } catch (e) {}

  // ── Today's brief ──''',
'renderHome macro grid')
# Quote ticks already repaint the front door. Include the rest of the grid, still not doTick.
s = sub1(s,
'if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG"))) {',
'if (pg === "home" && (dirty.has("XAU") || dirty.has("DXY") || dirty.has("PAXG") || dirty.has("VIX") || dirty.has("TNX") || dirty.has("BRENT") || dirty.has("WTI") || dirty.has("BTC"))) {',
'home quote paint')
s = sub1(s,
'Keys are configured in Replit Secrets, never on this page.',
"Keys are kept in this site's private settings, never on this page.",
'settings jargon')
def nsub(hay, old, new, n, label):
    c = hay.count(old)
    if c != n: die('%s matched %d times, expected %d' % (label, c, n))
    return hay.replace(old, new)
s = nsub(s, 'vixN.toFixed(1)', 'vixN.toFixed(2)', 2, 'vixN rounding')
s = nsub(s, 'vix.toFixed(1)', 'vix.toFixed(2)', 3, 'vix rounding')
s = nsub(s, "['VIX', 'VIX', v => v.toFixed(1)]", "['VIX', 'VIX', v => v.toFixed(2)]", 1, 'geo VIX tile')

# Regime fit is rendered from the server payload only. These three sites are the ones that
# print a computed fit on the ticker card and in Market Lab. The ranking engine is left as it is.
s = sub1(s,
'''    h+=`<div class="gc" style="padding:12px;margin-top:8px"><div style="font-family:var(--mn);font-size:8px;color:var(--gd);letter-spacing:0.15em;margin-bottom:6px">REGIME FIT · ${re.label}</div>
      <div style="font-size:11px;color:var(--t2);line-height:1.5">${a.cat==="Commodity"&&re.overweight.includes("Energy")?"Aligned with regime overweight (Energy/commodities).":a.cat==="Crypto"&&re.score>=55?"Crypto favoured in risk-on regime — size to volatility.":a.se.includes("Bull")&&re.score>=55?"Bullish thesis aligns with risk-on regime.":a.se.includes("Bear")||re.score<45?"Defensive positioning may suit current regime.":"Mixed regime fit — verify with Lens Engine."}</div>
      <button onclick="_setATab('cm')" style="margin-top:10px;width:100%;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">⬢ Run Lens Engine on ${a.tk}</button></div>`;''',
'''    h+=_rt53FitHtml(a.tk)+`<button type="button" onclick="_setATab('cm')" style="margin-top:10px;width:100%;background:var(--blG);color:var(--bl);border:1px solid rgba(79,142,247,0.2);border-radius:8px;padding:10px;font-family:var(--sn);font-size:11px;font-weight:700;cursor:pointer">⬢ Run Lens Engine on ${a.tk}</button>`;''',
'ticker regime fit card')
s = sub1(s,
'''  if(fit.score>=70) tips.push(`Regime fit is <strong style="color:var(--gn)">${fit.score}%</strong> — ${_labTk} is aligned with ${re.label}. Look for pullbacks to add / confirm, not chase extended moves without a plan.`);
  else if(fit.score>=45) tips.push(`Regime fit is <strong style="color:var(--gd)">${fit.score}%</strong> — mixed. Look for a catalyst or sector confirmation before sizing up.`);
  else tips.push(`Regime fit is <strong style="color:var(--rd)">${fit.score}%</strong> — ${_labTk} is fighting ${re.label}. Look for invalidation levels; treat longs as counter-trend.`);''',
'''  try { tips.push(_rt53FitLook()); } catch (e) { tips.push("Fit score not available yet."); }''',
'lab look-for fit sentence')
s = sub1(s,
'''  const fit=_tickerRegimeFit(_labTk,re);
  const strip=[...new Set([_labTk,...getActiveWl().tickers.slice(0,6),"SPX","BTC","XAU","XLK","XLE"])].slice(0,10);
  const ranges=[["1d","1D"],["5d","5D"],["1mo","1M"],["3mo","3M"],["1y","1Y"]];
  const fitCol=fit.score>=70?"var(--gn)":fit.score>=45?"var(--gd)":"var(--rd)";''',
'''  const fit={score:null,label:""};
  const strip=[...new Set([_labTk,...getActiveWl().tickers.slice(0,6),"SPX","BTC","XAU","XLK","XLE"])].slice(0,10);
  const ranges=[["1d","1D"],["5d","5D"],["1mo","1M"],["3mo","3M"],["1y","1Y"]];''',
'lab fit compute')
s = sub1(s,
'''          <div class="lab-hud-stat" title="How well this ticker matches current regime model"><div class="lab-hud-l">REGIME FIT · MODEL</div><div class="lab-hud-v" style="color:${fitCol}">${fit.score}%</div></div>''',
'''          ${_rt53FitHtml(_labTk,"hud")}''',
'lab regime fit hud')
s = sub1(s,
'''    const sc = a?.sc != null ? a.sc : Math.round(_tickerRegimeFit(tk, _computeRegimeEngine()).score);''',
'''    const sc = a?.sc != null ? a.sc : null;''',
'heatmap local fit fallback')
s = sub1(s,
'''      <div style="font-family:var(--mn);font-size:16px;font-weight:900;color:var(--gd);margin:4px 0">${sc}</div>''',
'''      <div style="font-family:var(--mn);font-size:16px;font-weight:900;color:var(--gd);margin:4px 0">${sc == null ? "\u2014" : sc}</div>''',
'heatmap empty fit cell')
s = sub1(s,
'''      const scShow = a._dyn ? Math.round(_tickerRegimeFit(a.tk, reP4).score) : a.sc;''',
'''      const scShow = _rt53ShownScore(a);''',
'desktop watchlist fit cell')
s = sub1(s,
'''    const scShow=a._dyn?Math.round(_tickerRegimeFit(a.tk,reWl).score):a.sc;''',
'''    const scShow=_rt53ShownScore(a);''',
'mobile watchlist fit cell')

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
var _rt53UkFmt = null, _rt53UkDateFmt = null;
function _rt53Uk(ms) {
  if (!ms) return "";
  try {
    if (!_rt53UkFmt) _rt53UkFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    return _rt53UkFmt.format(new Date(ms)) + " UK";
  } catch (e) { return ""; }
}
function _rt53UkDate(iso) {
  try {
    var p = String(iso).split("-"), y = +p[0], m = +p[1], d = +p[2];
    if (!y || !m || !d) return "";
    if (!_rt53UkDateFmt) _rt53UkDateFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short", year: "numeric" });
    return _rt53UkDateFmt.format(new Date(Date.UTC(y, m - 1, d, 12)));
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
// A function, not a var: boot calls the grid from nav('home') before this block's statements run,
// and a var would still be undefined. That throw is what raises the "could not finish loading" card.
function _rt53TileList() { return [
  ["gold", "XAU", "Gold", "The metal this desk is built around. It tends to firm when real yields fall, or when investors want an asset that is nobody\u2019s liability.", "pct"],
  ["dollar", "DXY", "Dollar", "A dearer dollar usually makes gold more expensive for buyers outside America.", "pct"],
  ["real", "", "US real yield", "The interest given up by holding gold, which pays none. When this rises, gold has to work harder.", "real"],
  ["us10", "TNX", "US 10-year", "The bond market\u2019s price of money, and the rate that tugs on everything else.", "yield"],
  ["vix", "VIX", "VIX", "What investors are paying to insure against a sharp fall in American shares.", "pct"],
  ["brent", "BRENT", "Brent", "The oil price most of the world actually pays, and a direct feed into inflation.", "pct"],
  ["wti", "WTI", "WTI", "The American crude benchmark. It usually travels with Brent; US supply can pull them apart.", "pct"],
  ["btc", "BTC", "Bitcoin", "A read on risk appetite. It has been trading with technology shares more often than with gold.", "pct"]
]; }
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
function _rt53Inner() { return '<div class="bb1-h">Macro</div><div class="bb1-grid">' + _rt53TileList().map(_rt53One).join("") + '</div>'; }
function _rt53GridHtml() { try { return '<section class="bb1-sec" data-bb1 aria-label="Macro signals">' + _rt53Inner() + '</section>'; } catch (e) { return ""; } }
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
// Freeze fix 2. Memoize the taggers as they stand after rt26 and rt52 (the Bitcoin story stays
// Crypto: that test lives inside detectTag, which this only caches). Regime keywords are read
// once per turn, so a sort does not recompute them on every comparison.
var _rt53Tag0 = _tagNewsHeadline, _rt53TagCache = new Map(), _rt53TagN = 0;
_tagNewsHeadline = function (text) {
  var n = (typeof A !== "undefined" && A && A.length) || 0;
  if (n !== _rt53TagN) { _rt53TagCache.clear(); _rt53TagN = n; }
  var key = text == null ? "" : String(text);
  if (_rt53TagCache.has(key)) return _rt53TagCache.get(key);
  var r = _rt53Tag0.apply(this, arguments);
  if (_rt53TagCache.size > 800) _rt53TagCache.clear();
  _rt53TagCache.set(key, r);
  return r;
};
var _rt53Dt0 = detectTag, _rt53DtCache = new Map();
detectTag = function (text, feedCat) {
  var key = (text == null ? "" : String(text)) + "\n" + (feedCat == null ? "" : String(feedCat));
  if (_rt53DtCache.has(key)) return _rt53DtCache.get(key);
  var r = _rt53Dt0.apply(this, arguments);
  if (_rt53DtCache.size > 800) _rt53DtCache.clear();
  _rt53DtCache.set(key, r);
  return r;
};
var _rt53Kw0 = _newsRegimeKeywords, _rt53KwArmed = false, _rt53KwOn = false, _rt53KwBox = null;
_newsRegimeKeywords = function () {
  if (!_rt53KwArmed) {
    _rt53KwArmed = true; _rt53KwOn = false;
    var done = function () { _rt53KwArmed = false; _rt53KwOn = false; _rt53KwBox = null; };
    if (typeof queueMicrotask === "function") queueMicrotask(done); else setTimeout(done, 0);
  }
  if (_rt53KwOn) return _rt53KwBox;
  _rt53KwBox = _rt53Kw0();
  _rt53KwOn = true;
  return _rt53KwBox;
};
// Freeze fix 3. Cache the Intl formatters and the as-of string used by the DXY / rt51 quote
// wrapper, and reuse that wrapper's DXY meta while the SEK timestamp and quote time are unchanged.
var _rt53WhenFmt = Object.create(null), _rt53WhenMemo = new Map(), _rt53When0 = _rt51When;
var _rt53TzL0 = _rt51TzL, _rt53TzLCache = Object.create(null);
_rt51TzL = function () {
  var tz = ""; try { tz = _rt17Tz() || ""; } catch (e) {}
  if (tz in _rt53TzLCache) return _rt53TzLCache[tz];
  var v = _rt53TzL0.apply(this, arguments);
  _rt53TzLCache[tz] = v;
  return v;
};
_rt51When = function (ms) {
  try {
    var tz = _rt17Tz(), pack = _rt53WhenFmt[tz];
    if (!pack) pack = _rt53WhenFmt[tz] = {
      day: new Intl.DateTimeFormat("en-CA", { timeZone: tz }),
      hm: new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }),
      wd: new Intl.DateTimeFormat("en-GB", { timeZone: tz, weekday: "short" })
    };
    var today = pack.day.format(new Date()), key = tz + "|" + today + "|" + ms;
    if (_rt53WhenMemo.has(key)) return _rt53WhenMemo.get(key);
    var d = new Date(ms), day = pack.day.format(d), hm = pack.hm.format(d);
    var wd = day === today ? "" : pack.wd.format(d) + " ";
    var v = wd + hm + " " + _rt51TzL();
    if (_rt53WhenMemo.size > 64) _rt53WhenMemo.clear();
    _rt53WhenMemo.set(key, v);
    return v;
  } catch (e) { return _rt53When0.apply(this, arguments); }
};
var _rt53Qm = _quoteMeta, _rt53DxyM = null, _rt53DxyK = "";
_quoteMeta = function (tk) {
  if (tk === "DXY") {
    var src = "", sek = 0, ts = 0, tz = "", today = "";
    try {
      src = (liveQuoteSrc && liveQuoteSrc.DXY) || ""; sek = _rt51SekOld || 0; ts = (liveQuoteTs && liveQuoteTs.DXY) || 0; tz = _rt17Tz() || "";
      if (_rt53WhenFmt[tz]) today = _rt53WhenFmt[tz].day.format(new Date());
    } catch (e) {}
    var k = src + "|" + sek + "|" + ts + "|" + tz + "|" + today;
    if (_rt53DxyM && _rt53DxyK === k && src === "dxy-computed" && sek) return _rt53DxyM;
    var m = _rt53Qm.apply(this, arguments);
    if (src === "dxy-computed" && sek && m && m.status === "live") { _rt53DxyK = k; _rt53DxyM = m; }
    else { _rt53DxyK = ""; _rt53DxyM = null; }
    return m;
  }
  return _rt53Qm.apply(this, arguments);
};
// Regime fit. One reader, _rt53FitPick: repoint that function when bb3 confirms where the
// field lives. The card, the lab control and the basis sheet render this object only.
var _rt53FitBag = Object.create(null), _rt53FitAsked = Object.create(null), _rt53FitAtFmt = null;
function _rt53FitPick(tk) {
  // Harness fixture, then the bag filled only by GET /api/regime-fit. No financials field,
  // no dynamic payload, and no in-browser score is a display source.
  var fx = typeof window !== "undefined" ? window._rt53FitFixture : null;
  if (fx && typeof fx === "object") {
    if (Object.prototype.hasOwnProperty.call(fx, tk)) return fx[tk] || null;
    if (String(fx.ticker || fx.symbol || "").toUpperCase() === tk) return fx;
  }
  if (_rt53FitBag && Object.prototype.hasOwnProperty.call(_rt53FitBag, tk)) return _rt53FitBag[tk];
  return undefined;
}
function _rt53FitNorm(raw, tk) {
  if (!raw || typeof raw !== "object") return { state: "absent", ticker: tk };
  var hasScore = Object.prototype.hasOwnProperty.call(raw, "score");
  var score = null;
  if (hasScore && raw.score != null && raw.score !== "") {
    var n = Math.round(Number(raw.score));
    if (isFinite(n)) score = Math.max(0, Math.min(100, n));
  }
  var label = raw.label === "Tailwind" || raw.label === "Neutral" || raw.label === "Headwind" ? raw.label : "";
  var inputs = Array.isArray(raw.inputs) ? raw.inputs.filter(function (x) { return x && typeof x === "object"; }) : [];
  var bench = raw.benchmark && typeof raw.benchmark === "object" ? raw.benchmark : null;
  if (!hasScore && !raw.reason && !label && !raw.method && !inputs.length) return { state: "absent", ticker: tk };
  return {
    state: score == null ? "null" : "score",
    ticker: String(raw.ticker || tk),
    score: score,
    reason: raw.reason ? String(raw.reason) : "",
    label: label,
    regime: raw.regime ? String(raw.regime) : "",
    asOf: raw.asOf ? String(raw.asOf) : "",
    method: raw.method ? String(raw.method) : "",
    version: raw.version != null ? String(raw.version) : "",
    inputs: inputs,
    benchmark: bench
  };
}
function _rt53FitPeek(tk) {
  tk = String(tk || "").toUpperCase();
  try {
    var raw = _rt53FitPick(tk);
    if (raw === undefined) return { state: "loading", ticker: tk };
    if (raw == null) return { state: "absent", ticker: tk };
    return _rt53FitNorm(raw, tk);
  } catch (e) { return { state: "absent", ticker: tk }; }
}
function _rt53FitRead(tk) {
  tk = String(tk || "").toUpperCase();
  try {
    var raw = _rt53FitPick(tk);
    if (raw === undefined) { _rt53FitAsk(tk); return { state: "loading", ticker: tk }; }
    if (raw == null) return { state: "absent", ticker: tk };
    return _rt53FitNorm(raw, tk);
  } catch (e) { return { state: "absent", ticker: tk }; }
}
function _rt53ShownScore(a) {
  if (!a || !a._dyn) return a && a.sc != null ? a.sc : "\u2014";
  var f = _rt53FitRead(a.tk);
  if (f.state === "score") return f.score;
  if (f.state === "loading") return "\u2026";
  return "\u2014";
}
function _rt53FitTake(j, tk) {
  if (!j || typeof j !== "object") return null;
  if (j.regimeFit && typeof j.regimeFit === "object" && !Array.isArray(j.regimeFit)) return j.regimeFit;
  if (Array.isArray(j.regimeFit)) {
    for (var i = 0; i < j.regimeFit.length; i++) if (j.regimeFit[i] && String(j.regimeFit[i].ticker || "").toUpperCase() === tk) return j.regimeFit[i];
    return null;
  }
  if (Object.prototype.hasOwnProperty.call(j, "score") || j.reason || j.method) return j;
  return null;
}
function _rt53FitRepaint() {
  try {
    document.querySelectorAll(".rt53-fit-hud, .rt53-fit-wrap").forEach(function (el) {
      var btn = el.querySelector("[data-rt52a]");
      var tk = btn ? btn.getAttribute("data-rt52a") : "";
      if (!tk) return;
      var hold = document.createElement("div");
      hold.innerHTML = _rt53FitHtml(tk, el.classList.contains("rt53-fit-hud") ? "hud" : "");
      if (hold.firstElementChild) el.replaceWith(hold.firstElementChild);
    });
    var look = document.querySelector(".lab-lookfor li");
    if (look) look.innerHTML = _rt53FitLook();
    document.querySelectorAll(".smart-fit[data-tk]").forEach(function (el) {
      var f = _rt53FitPeek(el.getAttribute("data-tk"));
      el.textContent = f.state === "score" ? String(f.score) : "";
    });
    var card = document.getElementById("siteIntelCard");
    if (card && typeof _renderSiteIntelCard === "function") {
      var hold2 = document.createElement("div");
      hold2.innerHTML = _renderSiteIntelCard((typeof _siteIntel !== "undefined" && _siteIntel.surface) || "ticker", { tk: typeof selTk !== "undefined" ? selTk : "" });
      if (hold2.firstElementChild) card.replaceWith(hold2.firstElementChild);
    }
    try { if (typeof _intelBarSig !== "undefined") _intelBarSig = ""; if (typeof _paintSiteIntelBar === "function") _paintSiteIntelBar(); } catch (e2) {}
  } catch (e) {}
}
function _rt53FitAsk(tk) {
  if (!_rt53FitAsked) _rt53FitAsked = Object.create(null);
  if (!_rt53FitBag) _rt53FitBag = Object.create(null);
  if (_rt53FitAsked[tk]) return;
  _rt53FitAsked[tk] = 1;
  var bag = _rt53FitBag;
  // Single source: GET /api/regime-fit. 404 (bb3 not deployed yet) and any other miss stay on "not available yet". The client never fills a number in.
  fetch("/api/regime-fit?ticker=" + encodeURIComponent(tk), { credentials: "same-origin", signal: AbortSignal.timeout(8000) }).then(function (r) {
    if (r.status === 404 || !r.ok) return null;
    return r.json();
  }).then(function (j) {
    bag[tk] = _rt53FitTake(j, tk);
    _rt53FitRepaint();
  }).catch(function () { bag[tk] = null; _rt53FitRepaint(); });
}
function _rt53FitAt(iso) {
  if (!iso) return "\u2014";
  var d = new Date(iso);
  if (!isFinite(d.getTime())) return "\u2014";
  try {
    if (!_rt53FitAtFmt) _rt53FitAtFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    return _rt53FitAtFmt.format(d) + " UK";
  } catch (e) { return "\u2014"; }
}
function _rt53FitPts(n) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  if (Object.is(v, -0)) v = 0;
  if (v > 0) return "+" + (Math.round(v * 10) / 10);
  if (v < 0) return "\u2212" + (Math.round(Math.abs(v) * 10) / 10);
  return "0";
}
function _rt53FitInputLine(inp) {
  if (!inp) return "";
  // The last row is a clamp. It is usually 0, and a zero clamp is not a market input.
  if (String(inp.key || "") === "bounds" && Number(inp.contribution) === 0) return "";
  var missing = inp.value == null || inp.value === "";
  var val = missing ? "\u2014" : String(inp.value);
  if (!missing && inp.unit) val += " " + String(inp.unit);
  var bits = [inp.label || inp.key || "Input", val];
  if (inp.source) bits.push(String(inp.source));
  if (inp.asOf) bits.push(_rt53FitAt(inp.asOf));
  if (inp.contribution != null && inp.contribution !== "") bits.push(_rt53FitPts(inp.contribution) + " points");
  return bits.join(" \u00b7 ");
}
function _rt53FitSheet(tk) {
  var f = _rt53FitRead(tk), E = function (v) { try { return _rt52E(v); } catch (e) { return _rt53Esc(v); } };
  if (f.state === "loading") return { k: "REGIME FIT", t: (f.ticker || tk) + " \u00b7 Loading", what: E("The published fit is on its way from the desk. This page does not estimate a number while it waits."), how: [], src: E("Dispatch server"), at: "\u2014", why: "" };
  if (f.state === "absent") return { k: "REGIME FIT", t: (f.ticker || tk) + " \u00b7 Fit score not available yet", what: E("The desk publishes one fit score from the server. It is not on this page yet, so nothing is estimated here."), how: [], src: E("Dispatch server"), at: "\u2014", why: "" };
  var how = (f.inputs || []).map(function (inp) { return _rt53FitInputLine(inp); }).filter(Boolean).map(E);
  var bench = "SPY \u2014";
  if (f.benchmark) bench = String(f.benchmark.symbol || "SPY") + " " + (f.benchmark.value == null || f.benchmark.value === "" ? "\u2014" : f.benchmark.value) + (f.benchmark.asOf ? " \u00b7 " + _rt53FitAt(f.benchmark.asOf) : "");
  var title = f.state === "score" ? (f.ticker + " \u00b7 " + f.score + "/100" + (f.label ? " \u00b7 " + f.label : "")) : (f.ticker + " \u00b7 " + (f.reason || "No fit score"));
  var what = f.state === "null" ? (f.reason || "No fit score was published for this name.") : "How well this name suits the current market mood. The score starts at 50. Each row adds or takes off points. A missing price is shown as a dash and adds nothing.";
  var method = f.method ? '<details class="rt53-fit-how"><summary>How this is calculated</summary><p>' + E(f.method) + "</p></details>" : "";
  return { k: "REGIME FIT", t: title, v: method, what: E(what), how: how, src: E(bench), at: f.asOf ? _rt53FitAt(f.asOf) : "\u2014", why: f.regime ? E("Market mood: " + f.regime + (f.version ? " \u00b7 version " + f.version : "")) : (f.version ? E("Version " + f.version) : "") };
}
function _rt53FitHtml(tk, mode) {
  try {
    var f = _rt53FitRead(tk), v = "", sub = "Fit score not available yet", tone = "";
    if (f.state === "loading") {
      v = '<span class="rt53-fit-v rt53-fit-skel" aria-hidden="true"></span>';
      sub = "Loading the published fit";
    } else if (f.state === "score") {
      v = '<span class="rt53-fit-v">' + f.score + '<span class="rt53-fit-of">/100</span></span>';
      sub = [f.label, f.regime].filter(Boolean).join(" \u00b7 ") || "Published fit";
      tone = f.label === "Tailwind" ? " up" : f.label === "Headwind" ? " dn" : "";
    } else if (f.state === "null") {
      sub = f.reason || "No fit score for this name.";
      if (f.label || f.regime) sub += " \u00b7 " + [f.label, f.regime].filter(Boolean).join(" \u00b7 ");
    }
    var card = '<button type="button" class="rt53-fit-card' + tone + '" data-rt52b="rt53fit" data-rt52a="' + _rt53Esc(tk) + '" aria-haspopup="dialog"><span class="rt53-fit-k">REGIME FIT</span>' + v + '<span class="rt53-fit-s">' + _rt53Esc(sub) + '</span></button>';
    var ctl = '<button type="button" class="rt53-fit-ctl" data-rt52b="rt53fit" data-rt52a="' + _rt53Esc(tk) + '" aria-haspopup="dialog">How this fit is worked out</button>';
    if (mode === "hud") return '<div class="lab-hud-stat rt53-fit-hud">' + card + ctl + '</div>';
    return '<div class="gc rt53-fit-wrap">' + card + ctl + '</div>';
  } catch (e) { return '<div class="gc rt53-fit-wrap"><p class="rt53-fit-s">Fit score not available yet</p></div>'; }
}
function _rt53FitLook() {
  var f = _rt53FitRead(typeof _labTk !== "undefined" ? _labTk : "");
  if (f.state === "score") return "Regime fit is <strong>" + f.score + "/100</strong>" + (f.label ? " \u00b7 " + _rt53Esc(f.label) : "") + (f.regime ? " \u00b7 " + _rt53Esc(f.regime) : "") + ". The figure is the desk\u2019s published score.";
  if (f.state === "null") return _rt53Esc(f.reason || "No fit score for this name.");
  if (f.state === "loading") return "The published fit is still loading.";
  return "Fit score not available yet.";
}
function _rt53FitPhrase(tk) {
  var f = _rt53FitRead(tk);
  if (f.state === "score") return "regime fit " + f.score + "/100";
  if (f.state === "null") return f.reason || "no fit score";
  if (f.state === "loading") return "regime fit loading";
  return "fit score not available yet";
}
try { RT52_B.rt53fit = function (tk) { return _rt53FitSheet(tk); }; RT52_B.fit = RT52_B.rt53fit; } catch (e) {}
try {
  var _rt53Local0 = _computeLocalIntel;
  _computeLocalIntel = function (surface, extra) {
    var r = _rt53Local0.apply(this, arguments);
    if (!r) return r;
    try {
      var tk = (extra && extra.tk) || (typeof selTk !== "undefined" ? selTk : "");
      var phrase = surface === "ticker" && tk ? _rt53FitPhrase(tk) : "";
      r.insight = String(r.insight || "")
        .replace(/(?:Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral) · regime fit \d+\/100 · (?:no sync|no price yet) · /gi, phrase ? phrase + " · " : "")
        .replace(/(?:Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral) · regime fit \d+\/100 · /gi, phrase ? phrase + " · " : "")
        .replace(/regime fit \d+\/100/gi, phrase || "fit score not available yet")
        .replace(/Top fit: ([A-Z0-9.\-=^]{1,12}) \(\d+\)/g, function (_, t) { var f = _rt53FitRead(t); return "Top fit: " + t + (f.state === "score" ? " (" + f.score + ")" : ""); })
        .replace(/Weakest: ([A-Z0-9.\-=^]{1,12}) \(\d+\)/g, function (_, t) { var f = _rt53FitRead(t); return "Weakest: " + t + (f.state === "score" ? " (" + f.score + ")" : ""); });
      if (surface === "ticker" && typeof r.headline === "string") {
        var f = _rt53FitRead(tk);
        if (f.state === "score" && f.label) r.headline = String(tk).toUpperCase() + " \u2014 " + f.label;
        else r.headline = r.headline.replace(/ — (Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral)\b/, "");
      }
      if (Array.isArray(r.fit)) r.fit = r.fit.filter(function (item) { return item && item.tk; });
    } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var _rt53Head0 = _rt28Head;
  _rt28Head = function (t) {
    var x = _rt53Head0.apply(this, arguments);
    try {
      if (typeof x !== "string") return x;
      var m = x.match(/^([A-Z0-9.\-=^]{1,12}) — (Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral)\b/);
      if (!m) return x;
      var f = _rt53FitPeek(m[1]);
      if (f.state === "score" && f.label) return x.replace(m[0], m[1] + " \u2014 " + f.label);
      return x.replace(m[0], m[1]);
    } catch (e2) { return x; }
  };
} catch (e) {}
try {
  var _rt53Badge0 = _smartFitBadge;
  _smartFitBadge = function (tk) {
    var f = _rt53FitPeek(tk);
    if (f.state !== "score") return "";
    return String(_rt53Badge0.apply(this, arguments)).replace(/>\s*\d+\s*</, ">" + f.score + "<").replace('class="smart-fit"', 'class="smart-fit" data-tk="' + _rt53Esc(tk) + '"');
  };
} catch (e) {}
try {
  var _rt53SiCard0 = _renderSiteIntelCard;
  _renderSiteIntelCard = function () {
    var h = String(_rt53SiCard0.apply(this, arguments));
    return h.replace(/<span class="si-fit-chip"[^>]*>([A-Z0-9.\-=^]{1,12}) \d+<\/span>/g, function (_, t) {
      var f = _rt53FitRead(t);
      if (f.state === "score") return '<span class="si-fit-chip">' + t + " " + f.score + "</span>";
      if (f.state === "loading") return '<span class="si-fit-chip">' + t + ' <i class="rt53-fit-skel"></i></span>';
      return '<span class="si-fit-chip">' + t + "</span>";
    });
  };
} catch (e) {}
try {
  var _rt53DeskCard0 = _renderMorningDeskRunCard;
  _renderMorningDeskRunCard = function () {
    var h = String(_rt53DeskCard0.apply(this, arguments));
    return h.replace(/(<span>([A-Z0-9.\-=^]{1,12})<\/span>)<b>[^<]*<\/b>/g, function (_, span, t) {
      var f = _rt53FitRead(t);
      if (f.state === "score") return span + "<b>" + f.score + "/100</b>";
      if (f.state === "loading") return span + '<b class="rt53-fit-skel"></b>';
      return span;
    });
  };
} catch (e) {}
try {
  var _rt53Notes0 = _renderDeskNotesPanel;
  _renderDeskNotesPanel = function () {
    return String(_rt53Notes0.apply(this, arguments)).replace(/ · fit [^·<]*%/g, "");
  };
  var _rt53SaveNote0 = saveDeskNote;
  saveDeskNote = function () {
    var r = _rt53SaveNote0.apply(this, arguments);
    try {
      var list = _deskNotesStore();
      if (list[0] && list[0].fit != null) { delete list[0].fit; _deskNotesSave(list); }
      var host = document.getElementById("lab-notes");
      if (host) host.outerHTML = _renderDeskNotesPanel();
    } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var notes = JSON.parse(localStorage.getItem("td_desk_notes_v1") || "[]"), dirty = false;
  (Array.isArray(notes) ? notes : []).forEach(function (n) { if (n && Object.prototype.hasOwnProperty.call(n, "fit")) { delete n.fit; dirty = true; } });
  if (dirty) localStorage.setItem("td_desk_notes_v1", JSON.stringify(notes));
} catch (e) {}
try {
  var run = JSON.parse(sessionStorage.getItem("td_desk_run") || "null");
  if (run) {
    ["top", "weak"].forEach(function (k) { (run[k] || []).forEach(function (x) { if (x && x.score != null) delete x.score; }); });
    sessionStorage.setItem("td_desk_run", JSON.stringify(run));
  }
} catch (e) {}
// ── rt53 QA ── dossier sheet, one trading-now line, news tags, desk score, 13F, hours slot, signals paint.
function _rt53bTag(text) {
  var low = " " + String(text || "").toLowerCase().replace(/\s+/g, " ") + " ";
  var cache = _rt53bTag.re || (_rt53bTag.re = Object.create(null));
  function hit(words) {
    for (var i = 0; i < words.length; i++) {
      var k = String(words[i] || "").trim();
      if (!k) continue;
      var re = cache[k];
      if (!re) {
        var e = k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        var pre = /^[a-z0-9]/i.test(k) ? "(^|[^a-z0-9])" : "";
        var post = /[a-z0-9]$/i.test(k) ? "($|[^a-z0-9])" : "";
        re = cache[k] = new RegExp(pre + e + post, "i");
      }
      if (re.test(low)) return true;
    }
    return false;
  }
  if (hit(["bitcoin", "crypto", "cryptocurrency", "cryptocurrencies", "ethereum", "btc", "eth", "blockchain", "solana", "xrp", "dogecoin", "stablecoin", "binance", "coinbase", "defi", "altcoin"])) return "Crypto";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};
  Object.keys(rules).forEach(function (tag) {
    if (tag === "Crypto") return;
    var cfg = rules[tag] || {}, keys = cfg.k || [], s = 0;
    for (var i = 0; i < keys.length; i++) if (hit([keys[i]])) s += cfg.w || 1;
    if (s > bestScore) { bestScore = s; best = tag; }
  });
  return bestScore > 0 ? best : "Other";
}
try {
  if (typeof _rt53Dt0 === "function") { _rt53Dt0 = _rt53bTag; if (_rt53DtCache && _rt53DtCache.clear) _rt53DtCache.clear(); }
  else detectTag = _rt53bTag;
  (typeof NEWS !== "undefined" ? NEWS : []).forEach(function (n) { if (n) delete n._rt52; });
  if (typeof _rt52Retag === "function") _rt52Retag();
} catch (e) {}
try {
  _rt51Label = function () {
    var b = _rt51Brk();
    if (!b || !b.priced) return "Prices loading";
    return b.live + " trading now \u00b7 " + b.closed + " closed" + (b.weekend ? " for the weekend" : "") + (b.quiet ? " \u00b7 " + b.quiet + " quiet" : "");
  };
} catch (e) {}
try {
  RT52_B.dossier = function (iso) {
    var d = (typeof TD_COUNTRY_DOSSIERS !== "undefined") ? TD_COUNTRY_DOSSIERS[iso] : null;
    if (!d) return null;
    var E = function (v) { try { return _rt52E(v); } catch (e2) { return _rt53Esc(v); } };
    var asOf = "";
    try { asOf = _rt53FitAt(new Date().toISOString()); } catch (e2) {}
    var how = (d.signals || []).map(function (x) { return "Desk note: " + x; });
    how.push("Desk stress score: " + d.cii + " out of 100. It is a baseline set by the desk, not a live index.");
    if (d.tickers && d.tickers.length) how.push("Linked markets: " + d.tickers.join(", "));
    return { k: "COUNTRY DOSSIER", t: d.name + " \u00b7 " + d.cii + "/100", what: E("What this is: a short desk note on " + d.name + " and the markets tied to it."), how: how.map(E), src: E("The Dispatch desk. Headlines elsewhere on Geo Ops come from the news wires."), at: asOf || "\u2014", why: E("Why it matters: stress in " + d.name + " can move the linked prices. It is context for the tape, not a forecast.") };
  };
  openCountryDossier = function (iso) { try { _geoDossierIso = iso; } catch (e2) {} if (typeof _rt52Show === "function") _rt52Show("dossier", iso); };
} catch (e) {}
try {
  RT52_B.desk = function (score) {
    var n = String(score == null ? "" : score);
    var E = function (v) { try { return _rt52E(v); } catch (e2) { return _rt53Esc(v); } };
    return { k: "DESK SCORE", t: "Impact " + n + " out of 10", what: E("A plain reading of this headline, from 0 to 10. It uses the words in the story. It is not a forecast."), how: [E("Urgent words, such as a break, a strike or a record, sit higher."), E("A clear rise or a clear fall in the wording moves the number a step further."), E("The same headline always gets the same number.")], src: E("The Dispatch desk, from the headline text"), at: (function () { try { return _rt53FitAt(new Date().toISOString()); } catch (e2) { return "\u2014"; } })(), why: E("It shows how hard the desk thinks the headline can hit prices. It is not a recommendation.") };
  };
  var _rt53bCard = _renderNewsCard;
  _renderNewsCard = function () {
    var h = _rt53bCard.apply(this, arguments);
    return String(h).replace(/<span class="news-impact-score ([^"]*)" title="[^"]*">Impact (\d+)\/10<\/span>/g, '<button type="button" class="news-impact-score $1" data-rt52b="desk" data-rt52a="$2" aria-haspopup="dialog">Impact $2/10</button>');
  };
} catch (e) {}
try {
  _rt48eIntro = function (st) {
    try {
      if (typeof _rt48QuizReg === "function") _rt48QuizReg();
      if (!st || !st[0] || st[0].t !== "info" || !/in the news/i.test(String(st[0].h || ""))) return st;
      var heads = [], bank = [], exps = [];
      st.forEach(function (step) {
        if (!step) return;
        if (step.t === "scen") {
          var sc = (typeof RT47_SCEN !== "undefined") ? RT47_SCEN[step.n] : null, m = sc && sc[3];
          if (m && m.auto && m.h) heads.push(m.h);
          else if (sc && sc[0]) bank.push(sc[0]);
        } else if (step.t === "q" && step.ai) {
          var q = (typeof RT46_QUIZ !== "undefined" && RT46_QUIZ.news) ? RT46_QUIZ.news[step.n] : null;
          if (q && q[0]) exps.push(q[0]);
        }
      });
      function pl(k, w) { return k + " " + w + (k === 1 ? "" : "s"); }
      var b = "";
      if (heads.length) b = pl(heads.length, "recent headline") + " from the site's news feeds, matched automatically to a market scenario. " + (heads.length === 1 ? "The card asks" : "Each card asks") + ": if this news was a surprise, what is the usual first reaction?";
      else if (bank.length) b = "None of the latest headlines matched a scenario template today, so here " + (bank.length === 1 ? "is 1 scenario" : "are " + bank.length + " scenarios") + " from the scenario bank instead.";
      if (exps.length) b += (b ? " Then " : "") + pl(exps.length, "short explainer") + " on how " + (exps.length === 1 ? "a headline" : "headlines") + " like " + (exps.length === 1 ? "this" : "these") + " usually " + (exps.length === 1 ? "moves" : "move") + " gold, oil, the dollar, yields, stocks or crypto.";
      if (b) st[0] = Object.assign({}, st[0], { b: b });
    } catch (e2) {}
    return st;
  };
} catch (e) {}
try {
  var _rt53bF13 = _rt52F13Row;
  _rt52F13Row = function (x, mgr) {
    var h = _rt53bF13.apply(this, arguments);
    try {
      if (x && String(x.ticker || "").trim()) return h;
      var nm = (typeof _rt52Title === "function" ? _rt52Title(x && x.security) : "") || "Holding";
      var badge = '<span class="rt52-tk rt53-name">' + _rt52E(nm) + "</span>";
      if (h.indexOf('<span class="rt52-tk"></span>') >= 0) return h.replace('<span class="rt52-tk"></span>', badge);
    } catch (e2) {}
    return h;
  };
} catch (e) {}
function _rt53bMount13() {
  try {
    if (typeof IS_DESKTOP === "function" && !IS_DESKTOP()) return;
    if ((typeof termSelTk !== "undefined" && termSelTk) || (typeof _dynTk !== "undefined" && _dynTk)) return;
    var el = document.getElementById("p2body");
    if (!el || el.querySelector(".institutional-intel") || typeof _renderInstitutionalIntelligence !== "function") return;
    var box = document.createElement("div");
    box.innerHTML = _renderInstitutionalIntelligence();
    while (box.firstChild) el.appendChild(box.firstChild);
    if (typeof _institutionalData !== "undefined" && !_institutionalData["13f"] && typeof _loadInstitutional === "function") _loadInstitutional("13f");
  } catch (e) {}
}
function _rt53bMountFit() {
  try {
    if (typeof IS_DESKTOP !== "function" || !IS_DESKTOP()) return;
    if (typeof termSelTk === "undefined" || !termSelTk) return;
    var el = document.getElementById("p2body");
    if (!el || el.querySelector(".rt53-fit-hud")) return;
    var box = document.createElement("div");
    box.innerHTML = _rt53FitHtml(termSelTk, "hud");
    if (box.firstElementChild) el.insertBefore(box.firstElementChild, el.firstChild);
  } catch (e) {}
}
try {
  var _rt53bP2 = renderP2;
  renderP2 = function () { var r = _rt53bP2.apply(this, arguments); _rt53bMountFit(); _rt53bMount13(); return r; };
} catch (e) {}
try {
  var _rt53bRnv = _refreshNewsView;
  _refreshNewsView = function () {
    var r = _rt53bRnv.apply(this, arguments);
    try {
      var old = document.querySelector("#p2body .institutional-intel");
      if (old && typeof _renderInstitutionalIntelligence === "function") {
        var box = document.createElement("div");
        box.innerHTML = _renderInstitutionalIntelligence();
        if (box.firstElementChild) old.replaceWith(box.firstElementChild);
      }
    } catch (e2) {}
    return r;
  };
} catch (e) {}
function _rt53bReserveSess(root) {
  try {
    (root || document).querySelectorAll("#latency-strip").forEach(function (el) {
      if (el.querySelector(".rt38-sess")) return;
      var s = document.createElement("span");
      s.className = "latency-pill rt38-sess";
      s.setAttribute("aria-hidden", "true");
      s.textContent = "\u00a0";
      el.insertBefore(s, el.children[1] || null);
    });
  } catch (e) {}
}
try {
  var _rt53bLS = _renderLatencyStrip;
  _renderLatencyStrip = function () {
    var h = _rt53bLS.apply(this, arguments);
    try {
      if (String(h).indexOf("rt38-sess") < 0) h = String(h).replace(/(<span class="latency-pill">[\s\S]*?<\/span>)/, '$1<span class="latency-pill rt38-sess" aria-hidden="true">\u00a0</span>');
    } catch (e2) {}
    return h;
  };
} catch (e) {}
try { _rt53bReserveSess(); setTimeout(_rt53bReserveSess, 0); } catch (e) {}
try {
  var _rt53bPanels = renderTerminalPanels, _rt53bSigIdle = 0;
  renderTerminalPanels = function () {
    var onSig = false;
    try { onSig = typeof pg === "string" && pg === "sig" && typeof IS_DESKTOP === "function" && IS_DESKTOP() && !termSelTk && !_dynTk; } catch (e2) {}
    if (!onSig) return _rt53bPanels.apply(this, arguments);
    try { renderP3(); } catch (e2) {}
    try { var liveEl = document.getElementById("cmdLive"); if (liveEl && typeof _rt37Sum === "function") liveEl.textContent = _rt37Sum(); } catch (e2) {}
    if (!_rt53bSigIdle) {
      _rt53bSigIdle = 1;
      var rest = function () { _rt53bSigIdle = 0; try { if (pg === "sig") { renderP1(); renderP4(); renderP2(); } } catch (e3) {} };
      if (typeof requestIdleCallback === "function") requestIdleCallback(rest, { timeout: 700 }); else setTimeout(rest, 40);
    }
  };
} catch (e) {}
(function () { try { var st = document.createElement("style"); st.setAttribute("data-rt53", ""); st.textContent = '.bb1-sec{margin:16px 0 8px}.bb1-h{margin:0 0 8px;font:800 10px/1.3 var(--mn,ui-monospace);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3,#8b909a)}.bb1-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--rule,#2a2e36);border:1px solid var(--rule,#2a2e36)}.bb1-tile{background:var(--paper,#14151A);color:var(--ink,#EDEDE8);padding:11px 12px 12px;min-width:0}.bb1-k{font:700 10px/1.2 var(--ui,system-ui);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2,#A8ADB6)}.bb1-v{margin-top:5px;font:500 20px/1.15 var(--data,ui-monospace);font-variant-numeric:tabular-nums;color:var(--ink,#EDEDE8)}.bb1-c{font:500 12px/1 var(--data,ui-monospace);margin-left:4px}.bb1-day{font:400 10px/1 var(--ui,system-ui);letter-spacing:0;color:var(--ink-3,#8b909a);margin-left:3px}.bb1-up{color:var(--pos,#3fbf7f)}.bb1-dn{color:var(--neg,#e05a5a)}.bb1-why{margin:8px 0 0;color:var(--ink-2,#C5C8CE);font:400 12px/1.45 var(--ui,system-ui)}.bb1-meta{margin-top:8px;color:var(--ink-3,#8b909a);font:400 10px/1.4 var(--data,ui-monospace)}.front-door-quotes:has(.bb1-sec){display:block;background:transparent;gap:0}.front-door-quotes>.bb1-sec{grid-column:1 / -1}@media(min-width:768px){.bb1-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.bb1-v{font-size:22px}}.rt53-fit-wrap{padding:0}.rt53-fit-hud{display:flex;flex-direction:column;align-items:stretch;gap:8px;min-width:0}.rt53-fit-card{display:flex;flex-direction:column;align-items:flex-start;gap:4px;width:100%;min-height:44px;margin:0;padding:12px;text-align:left;background:transparent;border:0;color:inherit;font:inherit;cursor:pointer}.rt53-fit-k{font:700 8px/1.2 var(--mn,ui-monospace);letter-spacing:.15em;color:var(--gd,#d4a64a)}.rt53-fit-v{font:800 22px/1.1 var(--mn,ui-monospace);font-variant-numeric:tabular-nums;color:var(--tx,#eee)}.rt53-fit-card.up .rt53-fit-v{color:var(--gn,#3fbf7f)}.rt53-fit-card.dn .rt53-fit-v{color:var(--rd,#e05a5a)}.rt53-fit-of{font-size:12px;font-weight:700;opacity:.65}.rt53-fit-s{font:400 12px/1.45 var(--sn,system-ui);color:var(--t2,#c3c9d5)}.rt53-fit-ctl{display:none}@media(min-width:1280px){.lab-hud>.rt53-fit-hud{grid-column:1 / -1;flex-direction:row;align-items:center;justify-content:space-between;gap:16px}.lab-hud .rt53-fit-card{flex-direction:row;flex-wrap:wrap;align-items:baseline;gap:6px 14px;width:auto;flex:1;padding:4px 0}.rt53-fit-card{pointer-events:none;cursor:default}.rt53-fit-ctl{display:inline-flex;align-items:center;align-self:center;flex:0 0 auto;pointer-events:auto;cursor:pointer;min-height:44px;padding:8px 12px;background:transparent;border:1px solid var(--gb,#333);border-radius:8px;color:var(--gd,#d4a64a);font:700 11px/1.2 var(--sn,system-ui);white-space:nowrap}#p2body>.rt53-fit-hud{flex-direction:row;align-items:center;justify-content:space-between;gap:16px;padding:8px 12px;border-bottom:1px solid var(--gb,#333)}}.rt53-fit-how{margin:0 0 10px}.rt53-fit-how summary{cursor:pointer;color:var(--gd,#d4a64a);font:700 12px/1.4 var(--sn,system-ui)}.rt53-fit-how p{margin:8px 0 0;color:var(--t2,#c3c9d5)}.latency-strip .rt38-sess{display:inline-block;min-height:18px;vertical-align:middle}.news-impact-score{cursor:pointer}.rt52-tk.rt53-name{letter-spacing:0;text-transform:none;font-size:11px;max-width:9em}.rt53-fit-skel{display:inline-block;width:3.2em;height:.85em;border-radius:4px;background:linear-gradient(90deg,rgba(255,255,255,.08),rgba(255,255,255,.22),rgba(255,255,255,.08));background-size:200% 100%;animation:rt53sh 1.1s linear infinite;vertical-align:middle}@keyframes rt53sh{0%{background-position:100% 0}100%{background-position:-100% 0}}'; document.head.appendChild(st); } catch (e) {} })();
'''
# bb3_fit has already signed the Hormuz oil lines. Leave that text in place.
for bit in (
    'bb3fit: a rise in oil raises this supply-risk score',
    'capped at 12 points either way',
    '${Math.abs(oilC).toFixed(2)}',
):
    if s.count(bit) != 1: die('bb3 Hormuz text matched %d times: %s' % (s.count(bit), bit[:48]))
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
