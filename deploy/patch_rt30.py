#!/usr/bin/env python3
"""patch_rt30.py — chat26 -> chat27. Stacks on rt28 output (t28 = app.js 0d8af148). Client + index.html cache bust.
Usage: python3 patch_rt30.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt30)' in s: die('rt30 already applied')
if 'REALTIME PRICE LAYER (rt28)' not in s: die('base is not rt28 output')
if 'app.js?v=chat26' not in h: die('index.html is not chat26')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt28)', '// REALTIME PRICE LAYER (rt30)')
# 1. deep link: ?t= captured at script load (before any router strips it); used once on boot
R('deep read', '    const t = new URLSearchParams(location.search).get("t"); if (!t) return;',
  '    let t = new URLSearchParams(location.search).get("t");\n    if (!t && _rt30T0 && !_rt30Used && /^\\/markets\\/?$/.test(location.pathname)) t = _rt30T0;\n    _rt30Used = true;\n    if (!t) return;')
# 2+3+4. one desktop stock-open path: URL, error state, in-flight lookup, INTEL
R('termSelect', '  termSelTk = tk;\n  // Surface analysis panel', '  termSelTk = tk;\n  _rt30Opened(tk);\n  // Surface analysis panel')
R('openA phone', '_rt27Url(tk);if(selTk!==tk){', '_rt27Url(tk);_rt30Cancel();if(selTk!==tk){')
R('lookup late', '    if(!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0)){\n      _dynData=null; // ticker not found',
  '    if(seq!==_lookupSeq)return;\n    if(!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0)){\n      _dynData=null; // ticker not found')
R('bar tk', '  const intel = _mergeIntel(_siteIntel.surface || "pulse", { tk: selTk });', '  const intel = _mergeIntel(_siteIntel.surface || "pulse", { tk: _rt27CurTk() });')
R('tick tk', '_computeLocalIntel(_siteIntel.surface || "pulse", { tk: selTk })', '_computeLocalIntel(_siteIntel.surface || "pulse", { tk: _rt27CurTk() })', 3)
R('head norm', '_rt28Head(intel.headline)', '_rt30Head(intel.headline)', 2)
# polish: palette input, AI double negatives
R('palette raw', '  const raw=q.trim();', '  const raw=_rt30Q(q);')
R('cmd raw', '  const raw = input.value.trim();', '  const raw = _rt30Q(input.value);')
R('double neg', '  let s = _rt26Copy(String(t || "")).replace(/\\s+/g, " ").trim();',
  '  let s = _rt26Copy(String(t || "")).replace(/\\s+/g, " ").trim().replace(/\\b(declines?|declined|falls?|fell|drops?|dropped|decreased?|slid|slips?|slipped|lost|loses)\\s+(by\\s+)?-(?=\\d)/gi, (m, v) => `${v} `);')
# dashboard: brief risk lines are snapshots — no stale score, no risk-off claim from partial inputs
R('brief risk', '      re.score < 50 ? "Risk-off regime — size down high-beta first" : "Risk-on can reverse fast if VIX spikes",',
  '      re.loading ? "Regime inputs were still loading when this brief was built" : re.score < 50 ? `Risk-off at brief time (${re.score}/100) — size down high-beta first` : "Risk-on can reverse fast if VIX spikes",')
R('brief validate', '      `Validate regime score (${re.score}) vs VIX / SPX move`,', '      "Check the live regime score against the VIX / SPX move",')
R('awaiting', "  if (!cN || !dN) return { label: 'Awaiting Data', col: 'var(--t3)', desc: '' };", "  if (!cN || !dN) return { label: '—', col: 'var(--t3)', desc: 'Sector data not loaded on this page' };")
BLOCK = r"""// ── rt30: one stock-open path, deep-link capture, INTEL headline normalisation ──
var _rt30T0 = (() => { try { return new URLSearchParams(location.search).get("t") || ""; } catch (e) { return ""; } })();
var _rt30Used = false;
(() => { try { if (_rt30T0 && /^\/?$/.test(location.pathname)) location.replace(`/markets/?t=${encodeURIComponent(_rt30T0)}`); } catch (e) {} })();
function _rt30Cancel() {
  try { _lookupSeq++; } catch (e) {}
  try { _dynTk = null; _dynData = null; _dynLoading = false; } catch (e) {}
}
function _rt30Opened(tk) {
  _rt30Cancel();
  try { selTk = tk; } catch (e) {}
  _rt27Url(tk);
  try { _siteIntel.local = _computeLocalIntel("ticker", { tk }); if (_siteIntel.surface !== "ticker") _siteIntel.surface = "ticker"; } catch (e) {}
  _rt28Repaint();
}
function _rt30Q(q) {
  return String(q || "").trim().replace(/^\??\s*t\s*=\s*/i, "").replace(/['"`]/g, "").trim();
}
function _rt30Head(t) {
  if (typeof t !== "string") return t;
  let x = _rt28Head(t);
  if (/^(?:current\s+)?market\b/i.test(x) && !/^market regime: /i.test(x)) {
    let lbl = ""; try { lbl = _computeRegimeEngine().label; } catch (e) {}
    x = lbl ? `Market regime: ${lbl}` : x;
  }
  return x;
}
"""
R('rt30 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat26') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat26', 'app.js?v=chat27')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
