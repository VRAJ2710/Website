#!/usr/bin/env python3
"""patch_rt41.py: chat37 -> chat38. Stacks on rt40 output (app.js a503437). Client + index.html cache bust.
Ask: peer block goes FIRST in the context (the server clips context at 12,000 chars) and the peer fetch is awaited
(max 3s) before sending. 393: Account button and Compare modal fit. Lookup tab title; ?t= restored after closing
Compare; Compare shows a loading skeleton instead of '—' while figures load. Usage: python3 patch_rt41.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt41)' in s: die('rt41 already applied')
if 'REALTIME PRICE LAYER (rt40)' not in s: die('base is not rt40 output')
if 'app.js?v=chat37' not in h: die('index.html is not chat37')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt40)', '// REALTIME PRICE LAYER (rt41)')
R('peer await', '    await Promise.race([Promise.all([...tickers.slice(0, 3).map(tk => _prefetchLensData(tk)), ..._rt38Peers(tickers, text).map(tk => _rt40Fin(tk))]), new Promise(r => setTimeout(r, 7000))]);',
  '    await Promise.race([Promise.all(_rt38Peers(tickers, text).map(tk => _rt40Fin(tk))), new Promise(r => setTimeout(r, 3000))]);\n    await Promise.race([Promise.all(tickers.slice(0, 3).map(tk => _prefetchLensData(tk))), new Promise(r => setTimeout(r, 4000))]);')
R('peer first', 'context: _buildChatContext() + _rt38PeerCtx(tickers, text),', 'context: (_rt38PeerCtx(tickers, text).trim() ? _rt38PeerCtx(tickers, text).trim() + "\\n\\n" : "") + _buildChatContext(),')
BLOCK = r'''// ── rt41 ──
(() => { try { const st = document.createElement("style"); st.textContent = `@media (max-width:500px){.acct-menu-btn{flex-shrink:0;font-size:0!important;padding:6px 9px!important;min-width:0!important}.acct-menu-btn::before{content:"☰";font-size:15px}.term-overlay-card{left:8px!important;right:8px!important;margin:0 auto!important;width:auto!important;max-width:calc(100vw - 16px)!important;transform:none!important;box-sizing:border-box}.term-overlay-card table{font-size:10px}.term-overlay-card td,.term-overlay-card th{padding:5px 4px!important}}
.rt41-sk{display:inline-block;width:38px;height:9px;border-radius:4px;background:linear-gradient(90deg,var(--b2,#222) 0%,var(--b1,#333) 50%,var(--b2,#222) 100%);background-size:200% 100%;animation:rt41sk 1.1s linear infinite;vertical-align:middle}@keyframes rt41sk{0%{background-position:200% 0}100%{background-position:-200% 0}}`; document.head.appendChild(st); } catch (e) {} })();
const _rt41Pend = new Set();
{
  const _ens0 = _rt33Ensure;
  _rt33Ensure = function (tk) {
    const a = A.find(x => x.tk === tk);
    if (!a || a.cat !== "Stock" || _finCache[tk]) return _ens0.apply(this, arguments);
    _rt41Pend.add(tk);
    const p = _ens0.apply(this, arguments);
    Promise.resolve(p).finally(() => { _rt41Pend.delete(tk); try { _refreshOverlay("compareOv", _renderCompare); } catch (e) {} });
    setTimeout(() => _rt41Pend.delete(tk), 9000);
    return p;
  };
  const _rc1 = _renderCompare;
  _renderCompare = function () {
    let h = _rc1.apply(this, arguments);
    try { if (_compareTks.some(t => _rt41Pend.has(t))) h = h.replace(/>(—|-)<\/td>/g, '><span class="rt41-sk" aria-label="loading"></span></td>'); } catch (e) {}
    return h;
  };
}
// lookup tab title; restore ?t= after closing Compare
let _rt41CmpUrl = "";
setInterval(() => { try {
  if (_dynTk) { const want = `${_dynTk} · Lookup | The Dispatch Markets`; if (document.title !== want) document.title = want; }
  const ov = document.getElementById("compareOv");
  if (ov) { if (!_rt41CmpUrl && /[?&]t=/.test(location.search)) _rt41CmpUrl = location.pathname + location.search; }
  else if (_rt41CmpUrl) { const u = _rt41CmpUrl; _rt41CmpUrl = ""; if (!/[?&]t=/.test(location.search) && location.pathname === u.split("?")[0]) history.replaceState(history.state, "", u); }
} catch (e) {} }, 300);
'''
R('rt41 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat37', 'app.js?v=chat38')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
