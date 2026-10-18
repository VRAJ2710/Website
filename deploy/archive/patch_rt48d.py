#!/usr/bin/env python3
"""patch_rt48d.py: chatN -> chatN+1 (client only). Stacks on rt48b: live chat53 (app.js 8b755d7b, with rt50console) or chat52 without it.
Appends one block that only reassigns/wraps rt48/rt48b Academy functions:
- a saved same-day /api/academy-daily result is refreshed (no-store) when it is older than 2h, has fewer than 3 items, has no AI item,
  or predates the server's v3 format; the 15-minute minimum and the 8-a-day cap stay; saved items keep showing while it refreshes,
  and a poorer reply never replaces a fuller or AI one;
- up to 4 valid items are shown in "In the news", each with its own explanation;
- if the set changes while the lesson is on its intro it is rebuilt in place. No server change, no new tables, no Stripe.
Usage: python3 patch_rt48b.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt48d ──' in s: die('rt48d already applied')
if '// ── rt48b ──' not in s: die('base is not rt48b output')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 52: die('index is %s; expected chat52 or later' % base)
print('base:', base, '(rt50console present)' if 'rt50console' in s else '(no rt50console)')
for need in ['function _rt48AiOk(', 'function _rt48bDec(', 'const RT48B_AS =', 'function _rt48AiFetch(', 'function _rt48AutoKick(', 'function _rt48AutoLoad(', 'function _rt48AutoDone(', 'function _rt48NewsItems(',
             'function _rt48NewsSteps(', 'let _rt48Sess', 'let _rt47L', 'function _rt47Redraw(', 'function _rt46Day(', "const _RT48_AUTO_KEY = 'td_academy_auto_v1';"]:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt48d ── Academy explainers: refresh a saved same-day result when it is stale (2h+), short (<3), has no AI item or predates the
// server's format (v<3); keeps the 15-minute minimum and 8-a-day cap; keeps showing the saved items while refreshing; up to 4 items.
const RT48D_MAX = 4, RT48D_V = 3;
function _rt48dNeed() { const A = _rt48Ai || {}, it = Array.isArray(A.items) ? A.items : [];
  return it.length < 3 || !it.some(x => x && x.kind === 'ai') || (A.v || 0) < RT48D_V || Date.now() - (A.got || A.tryAt || 0) > 2 * 36e5; }
// re-read the device copy so up to 4 items, the server version and the fetch time survive a reload
{ const _al = _rt48AutoLoad; _rt48AutoLoad = function () { const r = _al.apply(this, arguments); try { const o = JSON.parse(localStorage.getItem(_RT48_AUTO_KEY) || '{}'), A = o.ai || {};
  if (o.day === _rt46Day() && Array.isArray(A.items)) { const items = A.items.map(_rt48AiOk).filter(Boolean).slice(0, RT48D_MAX);
    _rt48Ai = { at: items.length ? (A.at || 0) : 0, items, kind: items.some(x => x.kind === 'ai') ? 'ai' : 'template', n: A.n || 0, tryAt: A.tryAt || 0, got: items.length ? (A.got || 0) : 0, v: items.length ? (A.v || 0) : 0 }; } } catch (e) {} return r; }; }
_rt48AiFetch = function () { const A = _rt48Ai || {}, prev = Array.isArray(A.items) ? A.items : [];
  if (_rt48AutoDay !== _rt46Day() || (_rt48AutoBusy & 4) || !_rt48dNeed() || (A.tryAt && Date.now() - A.tryAt < 15 * 6e4) || (A.n || 0) >= 8) return;
  _rt48AutoBusy |= 4; const n = (A.n || 0) + 1, day = _rt46Day(); _rt48Ai = Object.assign({}, A, { n, tryAt: Date.now() });
  let opts = { cache: 'no-store', credentials: 'same-origin' }; try { opts.signal = AbortSignal.timeout(9000); } catch (e) {}
  fetch('/api/academy-daily', opts).then(r => r && r.ok && /json/.test(r.headers.get('content-type') || '') ? r.json() : null).then(j => {
    if (_rt46Day() !== day || !j || j.date !== day || !Array.isArray(j.items)) return; const items = j.items.map(_rt48AiOk).filter(Boolean).slice(0, RT48D_MAX);
    // never swap a fuller or AI result for a poorer one
    const score = l => l.length + (l.some(x => x.kind === 'ai') ? 10 : 0);
    if (items.length && score(items) >= score(prev)) _rt48Ai = { at: Date.parse(j.generatedAt) || Date.now(), items, kind: items.some(x => x.kind === 'ai') ? 'ai' : 'template', n, tryAt: Date.now(), got: Date.now(), v: Number(j.v) || 0 };
    else if (items.length) _rt48Ai = Object.assign({}, _rt48Ai, { got: Date.now(), v: Number(j.v) || 0 }); })
    .catch(() => {}).finally(() => { _rt48AutoBusy &= ~4; _rt48AutoDone(); }); };
{ const _ak = _rt48AutoKick; _rt48AutoKick = function () { const r = _ak.apply(this, arguments); try { if (_rt48AutoDay === _rt46Day()) _rt48AiFetch(); } catch (e) {} return r; }; }
{ const _ns = _rt48NewsSteps; _rt48NewsSteps = function () { try { _rt48AutoKick(); } catch (e) {} return _ns.apply(this, arguments); }; }
// a refreshed set that differs from what the open lesson shows: rebuild it if the learner is still on the intro
{ const _ad = _rt48AutoDone; _rt48AutoDone = function () { const r = _ad.apply(this, arguments); try { const st = _rt48Sess.news, k = (_rt48Ai.items || []).length;
  if (st && _rt47L.id === 'news' && !_rt47L.fin && _rt47L.i === 0 && st[0].t !== 'wl' && st.filter(s => s.ai).length !== k) { delete _rt48Sess.news; _rt47L.a = {}; _rt47Redraw(); }
  else if (st && _rt47L.id !== 'news') delete _rt48Sess.news; } catch (e) {} return r; }; }
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48d: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
