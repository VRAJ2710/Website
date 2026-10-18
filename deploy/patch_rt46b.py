#!/usr/bin/env python3
"""patch_rt46b.py: chat46 -> chat47 (client only). Stacks on rt46 output (app.js 9565cc65).
Guess the move: shows "Loading prices..." while feeds warm up, redraws the moment a price lands, falls back to the
site's CoinGecko cache for Bitcoin/Ether, says unavailable only after 30s with nothing fresh, and scores each round from
the source it started with. Account buttons: neutral placeholder until /api/me answers (no "Sign in" flash for admins).
Usage: python3 patch_rt46b.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt46b ──' in s: die('rt46b already applied')
if '// ── rt46 ──' not in s: die('base is not rt46 output')
if 'app.js?v=chat46' not in h: die('index.html is not chat46')
for need in ['function _rt46GameHtml(', 'function _rt46GameResolve(', 'function _rt46Px(', 'function _rt46Guess(', 'function _rt46Swap(', 'function _rt46RM(', 'const _RT46_GAME', 'function _renderOverlayAccountActions(', 'function renderAuthButtons(', 'function cgFetch(', 'let _userTierReady', 'function fp(']:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt46b ──
// 1) Guess the move: the game drew once before the first price arrived and never redrew, so it could say "no fresh price"
//    while Bitcoin streamed. Now: "Loading prices…" during warm-up, redraw as soon as a price lands, CoinGecko fallback
//    (the site's own server cache) for BTC/ETH, and "unavailable" only after 30s with nothing fresh from either source.
//    A round is scored from the same source it started with, so stream and CoinGecko prices are never mixed.
// 2) Account buttons: neutral placeholder until /api/me answers, so admins no longer see "Sign in" flash first.
const _RT46B_CG = { BTC: 'bitcoin', ETH: 'ethereum' };
const _RT46B_WS_FRESH = 90000, _RT46B_CG_FRESH = 300000, _RT46B_WARM = 30000, _RT46B_GRACE = 120000;
const _rt46bCg = {};
let _rt46bCgAt = 0, _rt46bCgBusy = false, _rt46bSeen = 0, _rt46bAuthGiveUp = false;
function _rt46bMs(v) { if (v == null) return 0; if (typeof v === 'number') return v < 1e12 ? v * 1000 : v; const n = Date.parse(v); return isFinite(n) ? n : 0; }
function _rt46bAgo(t) { const s = Math.max(0, Math.round((Date.now() - t) / 1000)); return s < 60 ? s + 's ago' : Math.round(s / 60) + 'm ago'; }
function _rt46bWs(tk) { try {
  const d = fp(tk), x = P[tk], p = x && x.p;
  if (!d || d.status !== 'live' || typeof p !== 'number' || !isFinite(p) || p <= 0) return null;
  const ts = _rt46bMs(typeof liveQuoteTs !== 'undefined' ? liveQuoteTs[tk] : null);
  if (ts && Date.now() - ts > _RT46B_WS_FRESH) return null;
  return { p, label: d.label, s: 'ws', asOf: ts || Date.now() };
} catch (e) { return null; } }
function _rt46bCgPx(tk) { const c = _rt46bCg[tk]; return c && Date.now() - c.asOf <= _RT46B_CG_FRESH ? { p: c.p, label: 'CoinGecko · ' + _rt46bAgo(c.asOf), s: 'cg', asOf: c.asOf } : null; }
_rt46Px = function (tk) {
  try { const o = _rt46P.game.open; if (o && o.tk === tk && o.s === 'cg') return _rt46bCgPx(tk); } catch (e) {}
  return _rt46bWs(tk) || (_RT46B_CG[tk] ? _rt46bCgPx(tk) : null);
};
function _rt46bFetch(force) {
  if (_rt46bCgBusy || typeof cgFetch !== 'function') return;
  if (!force && Date.now() - _rt46bCgAt < 20000) return;
  if (typeof _cgBackoffUntil !== 'undefined' && Date.now() < _cgBackoffUntil) return;
  _rt46bCgBusy = true; _rt46bCgAt = Date.now();
  // same URL as the site's own crypto poll, so it is served from the Dispatch server's shared cache
  const ids = typeof CG_IDS === 'string' && /\bbitcoin\b/.test(CG_IDS) && /\bethereum\b/.test(CG_IDS) ? CG_IDS : 'bitcoin,ethereum';
  let opts = {}; try { opts = { signal: AbortSignal.timeout(9000) }; } catch (e) {}
  Promise.resolve().then(() => cgFetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`, opts)).then(async r => {
    if (!r || !r.ok) return;
    const h = Date.parse((r.headers && r.headers.get('X-Dispatch-Data-As-Of')) || ''), asOf = isFinite(h) ? Math.min(h, Date.now()) : Date.now();
    const j = await r.json();
    for (const tk in _RT46B_CG) { const v = j && j[_RT46B_CG[tk]] && j[_RT46B_CG[tk]].usd;
      if (typeof v === 'number' && isFinite(v) && v > 0 && (!_rt46bCg[tk] || asOf >= _rt46bCg[tk].asOf)) _rt46bCg[tk] = { p: v, asOf }; }
  }).catch(() => {}).finally(() => { _rt46bCgBusy = false; _rt46bSync(); });
}
_rt46GameResolve = function () { try {
  const g = _rt46P.game, o = g.open; if (!o) return false;
  const end = o.at + _RT46_ROUND, now = Date.now(); if (now < end) return false;
  let q = null, res;
  // CoinGecko's cache can run a couple of minutes behind, so a CoinGecko round is timed in CoinGecko's own clock
  if (now - end <= (o.s === 'cg' ? _RT46B_GRACE * 2 : _RT46B_GRACE)) {
    if (o.s === 'cg') { const c = _rt46bCg[o.tk]; if (c && c.asOf >= (o.asOf || o.at) + _RT46_ROUND - 60000) q = { p: c.p }; else _rt46bFetch(); }
    else q = _rt46bWs(o.tk);
    if (!q) return false; // keep waiting inside the grace window
  }
  if (!q) res = { r: 'void', why: 'No fresh closing price from the same source arrived in time (or the page was closed), so the round is not scored.' };
  else if (q.p === o.p) res = { r: 'flat', why: 'The price finished exactly where it started.' };
  else { const up = q.p > o.p, win = (o.dir === 'up') === up;
    res = { r: win ? 'win' : 'loss', why: `${_rt46Fmt(o.tk, o.p)} → ${_rt46Fmt(o.tk, q.p)} (${up ? 'up' : 'down'} ${(Math.abs(q.p - o.p) / o.p * 100).toFixed(3)}%)${o.s === 'cg' ? ', CoinGecko prices' : ''}.` };
    g.played++; if (win) { g.wins++; g.streak++; g.best = Math.max(g.best, g.streak); } else g.streak = 0; }
  g.last = Object.assign({ tk: o.tk, dir: o.dir }, res); g.open = null; _rt46Save(); return true;
} catch (e) { return false; } };
_rt46Guess = function (dir) {
  const q = _rt46Px(_rt46GameTk); if (!q || _rt46P.game.open) return;
  _rt46P.game.open = { tk: _rt46GameTk, dir, p: q.p, at: Date.now(), s: q.s, asOf: q.asOf }; _rt46P.game.last = null; _rt46Save();
  _rt46Swap('rt46game', _rt46GameHtml(), '#rt46gh');
};
function _rt46bAvail() { return _RT46_GAME.filter(([tk]) => _rt46Px(tk)).map(a => a[0]); }
function _rt46bState() { return _rt46bAvail().length ? 'ok' : (_rt46bCgBusy || Date.now() - _rt46bSeen < _RT46B_WARM) ? 'loading' : 'none'; }
function _rt46bSig() { return _rt46P.game.open ? 'open' : _rt46bAvail().join(',') + '|' + _rt46bState(); }
function _rt46bRetry() { _rt46bSeen = Date.now(); _rt46bFetch(true); _rt46Swap('rt46game', _rt46GameHtml(), '#rt46gh'); }
{
  const _gh0 = _rt46GameHtml;
  _rt46GameHtml = function () {
    if (!_rt46bSeen) { _rt46bSeen = Date.now(); }
    if (!_rt46bWs('BTC') && !_rt46bWs('ETH') && !_rt46bCgPx('BTC')) setTimeout(() => _rt46bFetch(), 0);
    let h = _gh0.apply(this, arguments);
    const st = _rt46bState();
    const msg = st === 'loading'
      ? `<p class="rt46-note rt46b-load${_rt46RM() ? ' rm' : ''}" role="status" aria-live="polite"><span class="rt46b-dot" aria-hidden="true"></span>Loading prices…</p>`
      : `<p class="rt46-note" role="status">No fresh Bitcoin or Ether price has arrived from the live stream or from CoinGecko for a while. That is usually a brief outage at the data provider. <button type="button" class="rt46-btn rt46-btn-s" onclick="_rt46bRetry()">Try again</button></p>`;
    h = h.replace(/<p class="rt46-note">None of the game's markets[^<]*<\/p>/, msg);
    h = h.replace("the round is scored from the site's live feed.", 'the round is scored from the same price source it started with.');
    h = h.replace('<b id="rt46gpx">', '<b id="rt46gpx" aria-live="off">').replace(/(<b id="rt46gpx"[^>]*>[^<]*<\/b> )<span class="rt46-dim">/, '$1<span class="rt46-dim" id="rt46gsrc">');
    h = h.replace('class="rt46-btn rt46-up"', 'class="rt46-btn rt46-up" id="rt46gup"').replace('class="rt46-btn rt46-dn"', 'class="rt46-btn rt46-dn" id="rt46gdn"').replace(/<button type="button" class="rt46-chip2([^"]*)" aria-pressed="(true|false)" onclick="_rt46GameTk='([A-Z]+)'/g, '<button type="button" class="rt46-chip2$1" data-tk="$3" aria-pressed="$2" onclick="_rt46GameTk=\'$3\'');
    return h.replace('id="rt46game"', `id="rt46game" data-sig="${_rt46bSig()}"`);
  };
}
function _rt46bSync() { try {
  const el = document.getElementById('rt46game'); if (!el || _rt46P.game.open) return;
  if (el.dataset.sig === _rt46bSig()) return;
  const a = document.activeElement, inside = el.contains(a);
  _rt46Swap('rt46game', _rt46GameHtml(), inside ? (a.id ? '#' + a.id : a.dataset && a.dataset.tk ? `.rt46-chip2[data-tk="${a.dataset.tk}"]` : '.rt46-chip2.on') : null);
  if (inside && document.activeElement === document.body) { const f = document.querySelector('#rt46game .rt46-chip2.on') || document.getElementById('rt46gh'); if (f) f.focus({ preventScroll: true }); }
} catch (e) {} }
setInterval(() => { try {
  const el = document.getElementById('rt46game'); if (!el) return;
  const o = _rt46P.game.open;
  if ((!_rt46bWs('BTC') && !_rt46bWs('ETH') && Date.now() - _rt46bSeen > 3000) || (o && o.s === 'cg')) _rt46bFetch();
  _rt46bSync();
  if (o && Date.now() >= o.at + _RT46_ROUND) { const cd = document.getElementById('rt46gcd'); if (cd && !/closing/.test(cd.textContent)) cd.textContent = '0:00 · getting the closing price…'; }
  if (!o) { const q = _rt46Px(_rt46GameTk), s = document.getElementById('rt46gsrc'); if (s && q && s.textContent !== q.label) s.textContent = q.label; }
} catch (e) {} }, 1000);
// 2) no "Sign in" flash for signed-in users
function _rt46bAuthWait(compact) { return `<span class="rt46b-aw${compact ? ' c' : ''}" aria-hidden="true"></span>`; }
function _rt46bAuthPh() { ['cmdAuthBtn', 'hdrAuthBtn'].forEach(id => { const e = document.getElementById(id); if (e && !e.querySelector('.rt46b-aw')) e.innerHTML = _rt46bAuthWait(id === 'hdrAuthBtn'); });
  document.querySelectorAll('.term-overlay-account').forEach(n => { if (!n.querySelector('.rt46b-aw')) n.innerHTML = _rt46bAuthWait(true); }); }
function _rt46bAuthPending() { return typeof _userTierReady !== 'undefined' && !_userTierReady && !_rt46bAuthGiveUp; }
{
  const _oa0 = _renderOverlayAccountActions;
  _renderOverlayAccountActions = function () { if (_rt46bAuthPending()) return `<span class="term-overlay-account">${_rt46bAuthWait(true)}</span>`; return _oa0.apply(this, arguments); };
  const _ra0 = renderAuthButtons;
  renderAuthButtons = function () {
    if (_rt46bAuthPending()) { _rt46bAuthPh(); return; }
    const r = _ra0.apply(this, arguments);
    try { document.querySelectorAll('.term-overlay-account').forEach(n => { const t = document.createElement('div'); t.innerHTML = _renderOverlayAccountActions(); const m = t.firstElementChild; if (m && n.outerHTML !== m.outerHTML) n.replaceWith(m); }); } catch (e) {}
    return r;
  };
}
try { if (_rt46bAuthPending()) _rt46bAuthPh(); } catch (e) {}
setTimeout(() => { try { if (typeof _userTierReady !== 'undefined' && !_userTierReady) { _rt46bAuthGiveUp = true; renderAuthButtons(); } } catch (e) {} }, 7000);
try { const st = document.createElement('style'); st.id = 'rt46bcss'; st.textContent = `
.rt46b-aw{display:inline-block;width:168px;height:28px;border-radius:7px;background:var(--b2);border:1px solid var(--gb);opacity:.5;vertical-align:middle;max-width:100%}
.rt46b-aw.c{width:118px;height:24px}
.rt46b-load{display:flex;align-items:center;gap:8px}
.rt46b-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--gd);animation:rt46bp 1.2s ease-in-out infinite;flex:0 0 auto}
.rt46b-load.rm .rt46b-dot{animation:none}
@keyframes rt46bp{0%,100%{opacity:.25}50%{opacity:1}}
@media (prefers-reduced-motion:reduce){.rt46b-dot{animation:none}}`; document.head.appendChild(st); } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat46') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat46', 'app.js?v=chat47')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt46b block appended + index chat46->chat47; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
