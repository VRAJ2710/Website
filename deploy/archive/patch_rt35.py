#!/usr/bin/env python3
"""patch_rt35.py — chat31 -> chat32. Stacks on rt34 output (app.js 1d0b318c). Client + index.html cache bust.
INTEL request timeout (endless spinner), plain status labels, first-person / empty AI bullets cleaned,
consistent Ask CTA. Usage: python3 patch_rt35.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt35)' in s: die('rt35 already applied')
if 'REALTIME PRICE LAYER (rt34)' not in s: die('base is not rt34 output')
if 'app.js?v=chat31' not in h: die('index.html is not chat31')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt34)', '// REALTIME PRICE LAYER (rt35)')
R('intel timeout', 'body: JSON.stringify({ surface, ticker: tk, context: _siteIntelContext(surface, tk) })\n    });', 'body: JSON.stringify({ surface, ticker: tk, context: _siteIntelContext(surface, tk) }),\n      signal: AbortSignal.timeout(30000)\n    });')
R('neural label', '<span class="ns-lbl">NEURAL</span><span class="ns-val">${_siteIntel.aiLoad ? "SYNC" : aiOn ? "LINK" : _isPremium() ? "READY" : "LOCK"}</span>', '<span class="ns-lbl">AI</span><span class="ns-val">${_siteIntel.aiLoad ? "Updating" : aiOn ? "On" : _isPremium() ? "Ready" : "Premium"}</span>')
R('ask cta', '  if (/^analy[sz]e\\b/i.test(a.label) && !a.label.toUpperCase().includes(tk)) return { ...a, label: `Ask about ${tk}` };', '  if ((a.type === "chat" || !a.type) && /^(analy[sz]e|discuss|view detailed|explore|review|dig into|assess|ask)\\b/i.test(a.label)) return { ...a, label: `Ask about ${tk}` };')
R('txt clean', '  let s = _rt33Guard(_rt31Neg(t), tk);', '  let s = _rt35Txt(_rt33Guard(_rt31Neg(t), tk));')
BLOCK = r"""// Yahoo lists these coins under numbered ids; the bare -USD symbols return nothing
try { Object.assign(YAHOO_SYMBOLS, { UNI: "UNI7083-USD", MATIC: "POL28321-USD", APT: "APT21794-USD", SUI: "SUI20947-USD", PEPE: "PEPE24478-USD" }); } catch (e) {}
// ── rt35: AI copy is written in the house voice; empty bullets dropped ──
function _rt35Txt(s) {
  if (typeof s !== "string") return s;
  if (/^\s*(none identified|n\/a|none)\.?\s*$/i.test(s)) return "";
  return s.replace(/\bI'm\b/g, "we're").replace(/\bI am\b/g, "we are").replace(/\bI've\b/g, "we've").replace(/\bI'll\b/g, "we'll").replace(/(^|[.!?]\s+)I\b/g, "$1We").replace(/\sI\s/g, " we ").replace(/\bmy\b/g, "our").replace(/\bMy\b/g, "Our").replace(/(^|[.!?]\s+)we\b/g, (m, p) => p + "We");
}
"""
R('eco errors', 'let _ecoLoading = false;', 'let _ecoLoading = false;\nlet _ecoErrors = {};')
R('sector copy', "desc: 'Loading sector returns…' }", "desc: 'Sector returns loading' }")
R('rt35 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')

for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat31', 'app.js?v=chat32')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
