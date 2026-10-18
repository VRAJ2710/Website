#!/usr/bin/env python3
"""patch_rt48b.py: chatN -> chatN+1 (client only). Stacks on rt48: either chat51 (app.js 526fcc0b) or chat52 with rt50console
on top (app.js 02ad407a). Appends one block that only reassigns/wraps rt48 Academy functions:
- a failed or empty /api/academy-daily result is never cached; it is retried (15 min apart, max 8 a day), old cached results are revalidated;
- explainers must name an allowed asset (gold, oil, USD, US yields, S&P 500, Nasdaq, BTC, ETH, EUR/USD, GBP) with answers Up/Down/Little change;
  stablecoin items are rejected; HTML entities in headlines are decoded;
- explainers that arrive while "In the news" is on its intro are shown without reopening.
Pair with patch_rt48bs.py (server). No new tables, no Stripe.
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
if '// ── rt48b ──' in s: die('rt48b already applied')
if '// ── rt48 ──' not in s: die('base is not rt48 output')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 51: die('index is %s; expected chat51 or later' % base)
print('base:', base, '(rt50console present)' if 'rt50console' in s else '(no rt50console)')
for need in ['function _rt48AiOk(', 'function _rt48AiFetch(', 'function _rt48AutoKick(', 'function _rt48AutoLoad(', 'function _rt48AutoDone(', 'function _rt48NewsItems(',
             'function _rt48NewsSteps(', 'let _rt48Sess', 'let _rt47L', 'function _rt47Redraw(', 'function _rt46Day(', "const _RT48_AUTO_KEY = 'td_academy_auto_v1';"]:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt48b ── Academy auto-explainers: retry failed fetches (never cache a miss), strict asset/direction validation, entity decoding
const RT48B_AS = { gold: 'the gold price', oil: 'oil prices', usd: 'the US dollar', yields: 'US Treasury yields', spx: 'the S&P 500', nasdaq: 'the Nasdaq', btc: 'Bitcoin', eth: 'Ether', eurusd: 'EUR/USD', gbp: 'the British pound' };
const RT48B_O = ['Up', 'Down', 'Little change'];
function _rt48bDec(s) { s = String(s == null ? '' : s); try { for (let k = 0; k < 3 && /&(#x?[0-9a-f]+|[a-z]+\d*);/i.test(s); k++) { const t = document.createElement('textarea'); t.innerHTML = s; s = t.value; } } catch (e) {} return s.replace(/[\u0000-\u001f]/g, ' ').replace(/\s+/g, ' ').trim(); }
_rt48AiOk = function (it) { try { if (!it || typeof it !== 'object' || !Object.prototype.hasOwnProperty.call(RT48B_AS, it.asset)) return null;
  const D = v => typeof v === 'string' ? _rt48bDec(v) : '', bad = /<|>|https?:|&(#x?[0-9a-f]+|[a-z]+);/i, ban = /stablecoin|tether|\busd[ct]\b/i;
  const q = D(it.q), e = D(it.e), h = D(it.h), o = Array.isArray(it.o) ? it.o.map(D) : [], a = it.a;
  if (q.length < 10 || q.length > 220 || e.length < 30 || e.length > 420 || h.length > 240 || [q, e, h].some(x => bad.test(x)) || [q, e, h].some(x => ban.test(x))) return null;
  if (o.length !== 3 || o.some((x, k) => x !== RT48B_O[k]) || !Number.isInteger(a) || a < 0 || a > 2) return null;
  if (q !== `If this news is a surprise to markets, what is the typical first reaction in ${RT48B_AS[it.asset]}?`) return null;
  if (it.dir != null && ['up', 'down', 'flat'].indexOf(it.dir) !== a) return null;
  const link = typeof it.link === 'string' && /^https:\/\/[^\s"'<>]{5,300}$/.test(it.link) ? it.link : '';
  return { q, e, h, o, a, link, asset: it.asset, dir: ['up', 'down', 'flat'][a], kind: it.kind === 'ai' ? 'ai' : 'template', src: typeof it.src === 'string' ? D(it.src).slice(0, 40).replace(/[<>]/g, '') : '' }; } catch (e) { return null; } };
{ const _ni = _rt48NewsItems; _rt48NewsItems = function (list) { try { list = (list || []).map(it => { if (!it || typeof it !== 'object') return it; const c = Object.assign({}, it); ['x', 'title', 'headline'].forEach(k => { if (typeof c[k] === 'string') c[k] = _rt48bDec(c[k]); }); return c; }); } catch (e) {} return _ni.call(this, list); }; }
// revalidate what the device cached (old-format or failed results are dropped, so they are fetched again)
{ const _al = _rt48AutoLoad; _rt48AutoLoad = function () { const r = _al.apply(this, arguments); try { const A = _rt48Ai || {}, items = Array.isArray(A.items) ? A.items.map(_rt48AiOk).filter(Boolean).slice(0, 3) : [];
  _rt48Ai = items.length ? { at: A.at || Date.now(), items, kind: A.kind === 'ai' ? 'ai' : 'template', n: A.n || 1, tryAt: A.tryAt || 0 } : { at: 0, items: [], n: A.tryAt ? (A.n || 0) : 0, tryAt: A.tryAt || 0 };
  if (_rt48Nw && Array.isArray(_rt48Nw.cards)) _rt48Nw.cards.forEach(c => { if (c && typeof c.h === 'string') c.h = _rt48bDec(c.h); }); } catch (e) { _rt48Ai = { at: 0, items: [] }; } return r; }; }
_rt48AiFetch = function () { const A = _rt48Ai || {}; if ((_rt48AutoBusy & 4) || (A.items && A.items.length) || (A.tryAt && Date.now() - A.tryAt < 15 * 6e4) || (A.n || 0) >= 8) return;
  _rt48AutoBusy |= 4; const n = (A.n || 0) + 1, day = _rt46Day(); _rt48Ai = { at: 0, items: [], n, tryAt: Date.now() }; let opts = { cache: 'no-store', credentials: 'same-origin' }; try { opts.signal = AbortSignal.timeout(9000); } catch (e) {}
  fetch('/api/academy-daily', opts).then(r => r && r.ok && /json/.test(r.headers.get('content-type') || '') ? r.json() : null).then(j => {
    if (_rt46Day() !== day) return; const items = j && j.date === day && Array.isArray(j.items) ? j.items.map(_rt48AiOk).filter(Boolean).slice(0, 3) : [];
    if (items.length) _rt48Ai = { at: Date.parse(j.generatedAt) || Date.now(), items, kind: j.kind === 'ai' ? 'ai' : 'template', n, tryAt: Date.now() }; })
    .catch(() => {}).finally(() => { _rt48AutoBusy &= ~4; _rt48AutoDone(); }); };
{ const _ak = _rt48AutoKick; _rt48AutoKick = function () { const r = _ak.apply(this, arguments); try { if (_rt48AutoDay === _rt46Day() && !(_rt48Ai.items && _rt48Ai.items.length)) _rt48AiFetch(); } catch (e) {} return r; }; }
// when explainers arrive while "In the news" is open on its intro, rebuild that session so they appear
{ const _ad = _rt48AutoDone; _rt48AutoDone = function () { const r = _ad.apply(this, arguments); try { if (_rt47L.id === 'news' && !_rt47L.fin && _rt47L.i === 0 && _rt48Ai.items && _rt48Ai.items.length) { const st = _rt48Sess.news;
  if (st && st[0].t !== 'wl' && !st.some(s => s.ai)) { delete _rt48Sess.news; _rt47L.a = {}; _rt47Redraw(); } } } catch (e) {} return r; }; }
{ const _ns = _rt48NewsSteps; _rt48NewsSteps = function () { const st = _ns.apply(this, arguments); try { const k = (_rt48Ai.items || []).length; if (st[0] && st[0].t === 'info' && k) st[0] = Object.assign({}, st[0], { b: st[0].b + ` Then ${k} short explainer${k === 1 ? '' : 's'} on how ${k === 1 ? 'a headline' : 'headlines'} like these usually move gold, oil, the dollar, yields, stocks or crypto.` }); } catch (e) {} return st; }; }
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48b: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
