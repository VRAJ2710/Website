#!/usr/bin/env python3
"""patch_rt53.py: chat59 -> chat60 (client only).

bb3_ask then bb3_fit ship first (chat58 -> chat59). This patch refuses unless
the tree is that bundle:
  app.js md5 d38b70eb458091fa69143f9fe3bfe193
  index.html md5 b15074aedc3261bf9e2ca611084082ba and exactly app.js?v=chat59
  and the rt52 block is present.
A second run prints REFUSE (already applied) and exits 0. Any other miss
aborts with a non-zero status. Finishes with node --check.

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

BASE_CHAT = 59
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
    die('app.js md5 %s != %s (this patch applies only to the chat59 bundle, bb3_ask then bb3_fit)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    die('index.html md5 %s != %s' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n != BASE_CHAT: die('index is %s; this patch requires chat%d' % (base, BASE_CHAT))
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
  var fx = typeof window !== "undefined" ? window._rt53FitFixture : null;
  if (fx && typeof fx === "object") {
    if (Object.prototype.hasOwnProperty.call(fx, tk)) return fx[tk] || null;
    if (String(fx.ticker || fx.symbol || "").toUpperCase() === tk) return fx;
  }
  try {
    if (typeof _finCache !== "undefined" && _finCache && Object.prototype.hasOwnProperty.call(_finCache, tk)) {
      var fin = _finCache[tk];
      if (fin && typeof fin === "object" && Object.prototype.hasOwnProperty.call(fin, "regimeFit")) return fin.regimeFit || null;
    }
  } catch (e) {}
  try {
    if (typeof _dynData !== "undefined" && _dynData && typeof _dynData === "object" && Object.prototype.hasOwnProperty.call(_dynData, "regimeFit")) {
      var dt = String(_dynData.ticker || _dynData.symbol || (typeof _dynTk !== "undefined" ? _dynTk : "") || "").toUpperCase();
      if (!dt || dt === tk) return _dynData.regimeFit || null;
    }
  } catch (e) {}
  try {
    var mk = typeof window !== "undefined" ? window._rt53FitMarkets : null;
    if (mk && typeof mk === "object") {
      if (Object.prototype.hasOwnProperty.call(mk, tk)) return mk[tk] || null;
      var list = mk.regimeFit ? (Array.isArray(mk.regimeFit) ? mk.regimeFit : [mk.regimeFit]) : [];
      for (var i = 0; i < list.length; i++) if (list[i] && String(list[i].ticker || "").toUpperCase() === tk) return list[i];
    }
  } catch (e) {}
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
    if (raw == null) return { state: "absent", ticker: tk };
    return _rt53FitNorm(raw, tk);
  } catch (e) { return { state: "absent", ticker: tk }; }
}
function _rt53FitRead(tk) {
  tk = String(tk || "").toUpperCase();
  try {
    var raw = _rt53FitPick(tk);
    if (raw === undefined) { _rt53FitAsk(tk); return { state: "absent", ticker: tk }; }
    if (raw == null) return { state: "absent", ticker: tk };
    return _rt53FitNorm(raw, tk);
  } catch (e) { return { state: "absent", ticker: tk }; }
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
  } catch (e) {}
}
function _rt53FitAsk(tk) {
  if (!_rt53FitAsked) _rt53FitAsked = Object.create(null);
  if (!_rt53FitBag) _rt53FitBag = Object.create(null);
  if (_rt53FitAsked[tk]) return;
  _rt53FitAsked[tk] = 1;
  var bag = _rt53FitBag;
  fetch("/api/regime-fit?ticker=" + encodeURIComponent(tk), { credentials: "same-origin", signal: AbortSignal.timeout(8000) }).then(function (r) {
    return r.ok ? r.json() : null;
  }).then(function (j) {
    bag[tk] = _rt53FitTake(j, tk);
    _rt53FitRepaint();
  }).catch(function () { bag[tk] = null; });
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
function _rt53FitInputLine(inp) {
  var val = inp.value == null || inp.value === "" ? "\u2014" : String(inp.value);
  if (inp.unit) val += (inp.value == null || inp.value === "" ? "" : " ") + String(inp.unit);
  var bits = [inp.label || inp.key || "Input", val];
  if (inp.source) bits.push(String(inp.source));
  if (inp.asOf) bits.push(_rt53FitAt(inp.asOf));
  if (inp.weight != null && inp.weight !== "") bits.push("weight " + inp.weight);
  if (inp.contribution != null && inp.contribution !== "") bits.push("contribution " + inp.contribution);
  return bits.join(" \u00b7 ");
}
function _rt53FitSheet(tk) {
  var f = _rt53FitRead(tk), E = function (v) { try { return _rt52E(v); } catch (e) { return _rt53Esc(v); } };
  if (f.state === "absent") return { k: "REGIME FIT", t: (f.ticker || tk) + " \u00b7 Fit score not available yet", what: E("The desk publishes one fit score from the server. It is not on this page yet, so nothing is estimated here."), how: [], src: E("Dispatch server"), at: "\u2014", why: "" };
  var how = (f.inputs || []).map(function (inp) { return E(_rt53FitInputLine(inp)); });
  var bench = "SPY \u2014";
  if (f.benchmark) bench = String(f.benchmark.symbol || "SPY") + " " + (f.benchmark.value == null || f.benchmark.value === "" ? "\u2014" : f.benchmark.value) + (f.benchmark.asOf ? " \u00b7 " + _rt53FitAt(f.benchmark.asOf) : "");
  var title = f.state === "score" ? (f.ticker + " \u00b7 " + f.score + "/100" + (f.label ? " \u00b7 " + f.label : "")) : (f.ticker + " \u00b7 " + (f.reason || "No fit score"));
  return { k: "REGIME FIT", t: title, what: E(f.method || (f.state === "null" ? (f.reason || "No fit score was published for this name.") : "\u2014")), how: how, src: E(bench), at: f.asOf ? _rt53FitAt(f.asOf) : "\u2014", why: f.regime ? E("Regime: " + f.regime + (f.version ? " \u00b7 version " + f.version : "")) : (f.version ? E("Version " + f.version) : "") };
}
function _rt53FitHtml(tk, mode) {
  try {
    var f = _rt53FitRead(tk), v = "", sub = "Fit score not available yet", tone = "";
    if (f.state === "score") {
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
  return "Fit score not available yet.";
}
try { RT52_B.rt53fit = function (tk) { return _rt53FitSheet(tk); }; RT52_B.fit = RT52_B.rt53fit; } catch (e) {}
try {
  var _rt53Local0 = _computeLocalIntel;
  _computeLocalIntel = function (surface, extra) {
    var r = _rt53Local0.apply(this, arguments);
    if (!r || surface !== "ticker") return r;
    try {
      var tk = (extra && extra.tk) || (typeof selTk !== "undefined" ? selTk : "");
      var f = _rt53FitPeek(tk);
      r.insight = String(r.insight || "").replace(/(?:Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral) · regime fit \d+\/100 · /gi, "").replace(/regime fit \d+\/100/gi, f.state === "score" ? ("regime fit " + f.score + "/100") : "fit score not available yet");
      if (typeof r.headline === "string") {
        if (f.state === "score" && f.label) r.headline = tk + " \u2014 " + f.label;
        else r.headline = r.headline.replace(/ — (Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral)\b/, "");
      }
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
(function () { try { var st = document.createElement("style"); st.setAttribute("data-rt53", ""); st.textContent = '.bb1-sec{margin:16px 0 8px}.bb1-h{margin:0 0 8px;font:800 10px/1.3 var(--mn,ui-monospace);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3,#8b909a)}.bb1-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;background:var(--rule,#2a2e36);border:1px solid var(--rule,#2a2e36)}.bb1-tile{background:var(--paper,#14151A);color:var(--ink,#EDEDE8);padding:11px 12px 12px;min-width:0}.bb1-k{font:700 10px/1.2 var(--ui,system-ui);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2,#A8ADB6)}.bb1-v{margin-top:5px;font:500 20px/1.15 var(--data,ui-monospace);font-variant-numeric:tabular-nums;color:var(--ink,#EDEDE8)}.bb1-c{font:500 12px/1 var(--data,ui-monospace);margin-left:4px}.bb1-day{font:400 10px/1 var(--ui,system-ui);letter-spacing:0;color:var(--ink-3,#8b909a);margin-left:3px}.bb1-up{color:var(--pos,#3fbf7f)}.bb1-dn{color:var(--neg,#e05a5a)}.bb1-why{margin:8px 0 0;color:var(--ink-2,#C5C8CE);font:400 12px/1.45 var(--ui,system-ui)}.bb1-meta{margin-top:8px;color:var(--ink-3,#8b909a);font:400 10px/1.4 var(--data,ui-monospace)}.front-door-quotes:has(.bb1-sec){display:block;background:transparent;gap:0}.front-door-quotes>.bb1-sec{grid-column:1 / -1}@media(min-width:768px){.bb1-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.bb1-v{font-size:22px}}.rt53-fit-wrap{padding:0}.rt53-fit-hud{display:flex;flex-direction:column;align-items:stretch;gap:8px;min-width:0}.rt53-fit-card{display:flex;flex-direction:column;align-items:flex-start;gap:4px;width:100%;min-height:44px;margin:0;padding:12px;text-align:left;background:transparent;border:0;color:inherit;font:inherit;cursor:pointer}.rt53-fit-k{font:700 8px/1.2 var(--mn,ui-monospace);letter-spacing:.15em;color:var(--gd,#d4a64a)}.rt53-fit-v{font:800 22px/1.1 var(--mn,ui-monospace);font-variant-numeric:tabular-nums;color:var(--tx,#eee)}.rt53-fit-card.up .rt53-fit-v{color:var(--gn,#3fbf7f)}.rt53-fit-card.dn .rt53-fit-v{color:var(--rd,#e05a5a)}.rt53-fit-of{font-size:12px;font-weight:700;opacity:.65}.rt53-fit-s{font:400 12px/1.45 var(--sn,system-ui);color:var(--t2,#c3c9d5)}.rt53-fit-ctl{display:none}@media(min-width:1280px){.lab-hud>.rt53-fit-hud{grid-column:1 / -1;flex-direction:row;align-items:center;justify-content:space-between;gap:16px}.lab-hud .rt53-fit-card{flex-direction:row;flex-wrap:wrap;align-items:baseline;gap:6px 14px;width:auto;flex:1;padding:4px 0}.rt53-fit-card{pointer-events:none;cursor:default}.rt53-fit-ctl{display:inline-flex;align-items:center;align-self:center;flex:0 0 auto;pointer-events:auto;cursor:pointer;min-height:44px;padding:8px 12px;background:transparent;border:1px solid var(--gb,#333);border-radius:8px;color:var(--gd,#d4a64a);font:700 11px/1.2 var(--sn,system-ui);white-space:nowrap}}'; document.head.appendChild(st); } catch (e) {} })();
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
