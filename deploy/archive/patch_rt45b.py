#!/usr/bin/env python3
"""patch_rt45b.py: chat44 -> chat45 (client). Stacks on rt45 output (app.js 4b434dfe).
Fix: direct loads of /learn/?guide=<id>, /learn/?term=<id> and /learn/?tab=<id> open (and keep) the requested view even
when a later boot step (signed-in session re-running nav('learn')) clears the Learn state; the URL is no longer stripped.
Usage: python3 patch_rt45b.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt45b ──' in s: die('rt45b already applied')
if '// ── rt45 ──' not in s: die('base is not rt45 output')
if 'app.js?v=chat44' not in h: die('index.html is not chat44')
for need in ['function _rt45SyncUrl(', 'const _rt45Boot = ', 'let _rt45BootDone', 'const _RT45_TABS', 'function _rt45AllMods(']:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt45b ──
// Direct loads of /learn/?guide=… /learn/?term=… /learn/?tab=… must survive later boot steps (a signed-in session re-runs
// nav('learn') after the account loads, which clears _learnSub; rt45's URL sync then stripped ?guide=). The request stays
// "pending" until the visitor first interacts (pointer/key/wheel/touch), leaves /learn/, or 15 s pass. While pending, every
// Learn render re-applies it, a watcher repairs state/URL, and the URL sync never strips the deep link.
const _rt45bWant = (() => { try { const b = _rt45Boot; if (!b) return null;
  if (b.guide && _rt45AllMods().some(x => x.id === b.guide)) return { guide: b.guide, q: '?guide=' + encodeURIComponent(b.guide) };
  if (b.term && _RT45_GIDS.has(b.term)) return { term: b.term, q: '?term=' + encodeURIComponent(b.term) };
  if (b.tab && _RT45_TABS.some(t => t[0] === b.tab)) return { tab: b.tab, q: '?tab=' + encodeURIComponent(b.tab) };
  return null; } catch (e) { return null; } })();
let _rt45bPending = !!_rt45bWant, _rt45bTermEl = null;
const _rt45bT0 = Date.now();
function _rt45bOnPath() { return /^\/learn\/?$/.test(location.pathname); }
function _rt45bOnLearn() { try { return (typeof pg !== 'undefined' && pg === 'learn') || !!document.getElementById('learnOv'); } catch (e) { return false; } }
function _rt45bRelease() { if (!_rt45bPending) return; _rt45bPending = false; _rt45BootDone = true; }
function _rt45bMatch() { const w = _rt45bWant; if (!w) return true;
  if (w.guide) return _learnSub === w.guide;
  return !_learnSub && _learnTab === (w.term ? 'glossary' : w.tab); }
function _rt45bSet() { const w = _rt45bWant; if (!w) return;
  if (w.guide) { for (const [k, v] of Object.entries(LEARN_MODULES)) if (Array.isArray(v) && v.some(x => x.id === w.guide)) { _learnTab = k; break; } _learnSub = w.guide; }
  else { _learnSub = null; _learnTab = w.term ? 'glossary' : w.tab; if (w.term) _rt45Hi = w.term; } }
function _rt45bLive() { if (!_rt45bPending) return false; if (Date.now() - _rt45bT0 > 15000 || !_rt45bOnPath()) { _rt45bRelease(); return false; } return true; }
['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(ev => window.addEventListener(ev, e => { if (e.isTrusted) _rt45bRelease(); }, { capture: true, passive: true }));
{ const _su0 = _rt45SyncUrl;
  _rt45SyncUrl = function () {
    if (_rt45bLive()) { try {
      if (_rt45bMatch() && _rt45bWant.guide) { _rt45BootDone = true; _su0.apply(this, arguments); _rt45BootDone = false; }
      if (location.search !== _rt45bWant.q) history.replaceState(history.state, '', '/learn/' + _rt45bWant.q);
    } catch (e) {} return; }
    const r = _su0.apply(this, arguments);
    // a highlighted glossary term keeps its shareable ?term= link instead of collapsing to ?tab=glossary
    try { if (_rt45BootDone && _rt45bOnPath() && !_learnSub && _learnTab === 'glossary' && _rt45Hi && _RT45_GIDS.has(_rt45Hi) && location.search === '?tab=glossary') history.replaceState(history.state, '', '/learn/?term=' + encodeURIComponent(_rt45Hi)); } catch (e) {}
    return r;
  }; }
if (_rt45bWant) {
  _rt45BootDone = false;
  { const _rl1 = renderLearn;
    renderLearn = function () { try { if (_rt45bLive() && !_rt45bMatch()) _rt45bSet(); } catch (e) {} return _rl1.apply(this, arguments); }; }
  const _rt45bTick = () => { try {
    if (!_rt45bLive()) { clearInterval(_rt45bIv); return; }
    if (!_rt45bOnLearn()) return;
    if (!_rt45bMatch()) { _rt45bSet(); _refreshView(); if (typeof _rt45Scroll === 'function' && _rt45bWant.guide) _rt45Scroll(); }
    if (location.search !== _rt45bWant.q) history.replaceState(history.state, '', '/learn/' + _rt45bWant.q);
    if (_rt45bWant.term) { const el = document.querySelector(`[data-rt45t="${_rt45bWant.term}"]`); if (el && el !== _rt45bTermEl) { _rt45bTermEl = el; el.classList.add('rt45-hi'); el.scrollIntoView({ block: 'center' }); } }
  } catch (e) {} };
  const _rt45bIv = setInterval(_rt45bTick, 250);
  setTimeout(_rt45bTick, 0);
}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat44') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat44', 'app.js?v=chat45')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt45b block appended + index chat44->chat45; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
