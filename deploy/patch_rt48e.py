#!/usr/bin/env python3
"""patch_rt48e.py: chatN -> chatN+1 (client only). Stacks on rt48d: live chat54 (app.js 35d9a4c2).
Appends one block that only wraps rt47/rt48 Academy functions:
- the "In the news" intro counts headline cards, bank scenarios and explainers from the steps actually built, with singular/plural;
- while the lesson is on its first screen (loading screen or intro), it is redrawn whenever its steps change, e.g. when today's
  headlines finish loading or explainers are refreshed in place (previously the loading screen could stay up and the intro could
  show the old counts). No server change, no new tables, no Stripe.
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
if '// ── rt48e ──' in s: die('rt48e already applied')
if '// ── rt48d ──' not in s: die('base is not rt48d output')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 53: die('index is %s; expected chat53 or later' % base)
print('base:', base, '(rt50console present)' if 'rt50console' in s else '(no rt50console)')
for need in ['function _rt47PlayerHtml(', 'const RT47_SCEN', 'function _rt48dNeed(', 'function _rt48AiOk(', 'function _rt48bDec(', 'const RT48B_AS =', 'function _rt48AiFetch(', 'function _rt48AutoKick(', 'function _rt48AutoLoad(', 'function _rt48AutoDone(', 'function _rt48NewsItems(',
             'function _rt48NewsSteps(', 'let _rt48Sess', 'let _rt47L', 'function _rt47Redraw(', 'function _rt46Day(', "const _RT48_AUTO_KEY = 'td_academy_auto_v1';"]:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt48e ── "In the news": intro counts come from the steps actually built (singular/plural), and the open lesson is redrawn
// whenever its steps change while the learner is still on the first screen (loading screen or intro), e.g. after an in-place rebuild.
function _rt48eSig(st) { try { return (st || []).map(s => s.t + (s.n != null ? s.n : '') + (s.ai ? 'a' : '')).join(',') + '|' + ((st && st[0] && st[0].b) || ''); } catch (e) { return ''; } }
function _rt48eIntro(st) { try { if (!st || !st[0] || st[0].t !== 'info') return st; const pl = (k, w) => `${k} ${w}${k === 1 ? '' : 's'}`;
  const sc = st.filter(s => s.t === 'scen'), auto = sc.filter(s => { const m = RT47_SCEN[s.n] && RT47_SCEN[s.n][3]; return !!(m && m.auto); }).length, bank = sc.length - auto, ai = st.filter(s => s.t === 'q' && s.ai).length;
  let b = auto ? `${pl(auto, 'recent headline')} from the site's news feeds, matched automatically to a market scenario. ${auto === 1 ? 'The card asks' : 'Each card asks'}: if this news was a surprise, what is the usual first reaction?`
    : bank ? `None of the latest headlines matched a scenario template today, so here ${bank === 1 ? 'is one scenario' : 'are ' + bank + ' scenarios'} from the scenario bank instead.` : '';
  if (ai) b += `${b ? ' Then ' : ''}${pl(ai, 'short explainer')} on how ${ai === 1 ? 'a headline' : 'headlines'} like ${ai === 1 ? 'this' : 'these'} usually ${ai === 1 ? 'moves' : 'move'} gold, oil, the dollar, yields, stocks or crypto.`;
  if (b) st[0] = Object.assign({}, st[0], { b }); } catch (e) {} return st; }
{ const _ns = _rt48NewsSteps; _rt48NewsSteps = function () { return _rt48eIntro(_ns.apply(this, arguments)); }; }
let _rt48eShown = '';
{ const _ph = _rt47PlayerHtml; _rt47PlayerHtml = function () { const h = _ph.apply(this, arguments); try { _rt48eShown = _rt47L.id === 'news' ? _rt48eSig(_rt47Steps('news').slice(0, -1)) : ''; } catch (e) {} return h; }; }
function _rt48eSync() { try { if (_rt47L.id !== 'news' || _rt47L.fin || _rt47L.i !== 0 || !document.getElementById('rt47pl')) return;
  const fresh = _rt48NewsSteps(); if (!fresh || !fresh[0] || fresh[0].t === 'wl') return; const sig = _rt48eSig(fresh);
  if (sig !== _rt48eShown) { _rt48Sess.news = fresh; _rt47L.a = {}; _rt47Redraw(); } } catch (e) {} }
{ const _ad = _rt48AutoDone; _rt48AutoDone = function () { const r = _ad.apply(this, arguments); _rt48eSync(); return r; }; }
setInterval(_rt48eSync, 2000);
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48e: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
