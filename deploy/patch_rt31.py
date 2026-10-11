#!/usr/bin/env python3
"""patch_rt31.py — chat27 -> chat28. Stacks on rt30 output (app.js e813efa0). Client + index.html cache bust.
Usage: python3 patch_rt31.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt31)' in s: die('rt31 already applied')
if 'REALTIME PRICE LAYER (rt30)' not in s: die('base is not rt30 output')
if 'app.js?v=chat27' not in h: die('index.html is not chat27')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt30)', '// REALTIME PRICE LAYER (rt31)')
# 1. deep link wins over later (admin) route renders: re-assert until the user interacts
R('deep sticky', '    _rt27NoPush = true; try { openA(tk); } finally { _rt27NoPush = false; }\n  } catch (e) { _rt27NoPush = false; }',
  '    _rt27NoPush = true; try { openA(tk); } finally { _rt27NoPush = false; }\n    _rt31Stick(tk);\n  } catch (e) { _rt27NoPush = false; }')
# 3. stored/cached brief text rewritten at render
R('brief render', '  const b = _brief;\n  const vc = b.houseView', '  const b = _rt31Brief(_brief);\n  const vc = b.houseView')
R('ow engine', 'OVERWEIGHT</div>${re.overweight', 'OVERWEIGHT · REGIME ENGINE · LIVE</div>${re.overweight')
R('ow brief', 'OVERWEIGHT</div>${b.overweight', 'OVERWEIGHT · ${_rt31BriefSrc(b)}</div>${b.overweight')
# 4. double-negative cleanup on every shared copy path (headline strip, INTEL headline)
R('copy neg', '  return _rt24Copy(t).replace(/Market Regime Update:', '  return _rt31Neg(_rt24Copy(t)).replace(/Market Regime Update:')
R('head neg', '  let x = _rt28Head(t);', '  let x = _rt31Neg(_rt28Head(t));')
BLOCK = r"""// ── rt31: sticky deep link, stored-brief rewrite, double negatives ──
function _rt31Neg(t) {
  return typeof t !== "string" ? t : t.replace(/\b(declines?|declined|falls?|fell|drops?|dropped|decreased?|slid|slips?|slipped|lost|loses|down)\s+(by\s+)?-(?=\d)/gi, (m, v, by) => `${v} ${by || ""}`.replace(/\bby\s+$/i, "").replace(/\s+$/, " "));
}
function _rt31Stick(tk) {
  if (_rt31Stick.on) return;
  _rt31Stick.on = true;
  let n = 0, stop = false;
  const off = () => { stop = true; };
  ["pointerdown", "keydown", "wheel", "touchstart"].forEach(ev => window.addEventListener(ev, off, { once: true, capture: true }));
  const chk = () => {
    if (stop || ++n > 40) return;
    try {
      const q = new URLSearchParams(location.search).get("t");
      if (!q || !/^\/markets\/?$/.test(location.pathname)) return;
      const want = (typeof resolveInternalTicker === "function" && resolveInternalTicker(q)) || q;
      const open = IS_DESKTOP() ? (termSelTk === want && _expPanel === "p2") : (pg === "anlz" && selTk === want);
      if (!open) { _rt27NoPush = true; try { openA(want); } finally { _rt27NoPush = false; } }
    } catch (e) { _rt27NoPush = false; }
    setTimeout(chk, 400);
  };
  setTimeout(chk, 400);
}
function _rt31BriefSrc(b) {
  const ts = b && (b.generatedAt || b.createdAt || b.asOf || b.ts);
  let tm = "";
  try { if (ts) { const d = new Date(typeof ts === "number" && ts < 1e12 ? ts * 1000 : ts); if (!isNaN(d)) tm = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" }); } } catch (e) {}
  return `BRIEF${tm ? " · " + tm : b && b.date ? " · " + b.date : ""}`;
}
function _rt31Brief(b) {
  if (!b || typeof b !== "object") return b;
  let re = null; try { re = _computeRegimeEngine(); } catch (e) {}
  const on = re && !re.loading && re.score >= 50;
  const fix = x => typeof x !== "string" ? x : _rt31Neg(x)
    .replace(/Validate regime score \(\d+(?:\/100)?\)/gi, "Check the live regime score")
    .replace(/^⚠?\s*Risk-off regime\s*—\s*size down high-beta first/i, on ? "Risk-on can reverse fast if VIX spikes" : "$&");
  const o = { ...b };
  ["headline", "summary"].forEach(k => { o[k] = fix(o[k]); });
  ["risks", "actionItems", "catalysts"].forEach(k => { if (Array.isArray(o[k])) o[k] = o[k].map(fix); });
  return o;
}
"""
R('rt31 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat27', 'app.js?v=chat28')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
