#!/usr/bin/env python3
"""patch_rt24s.py — server: safeText() (AI/editorial text sent to the client) cuts at a word boundary and
adds '…' instead of hard-slicing mid-word. One exact anchor, no startup work; independent of rt20s/21s/22s.
Optional: if the safeText anchor is not exactly once, it SKIPs (exit 0) and changes nothing.
Usage: python3 patch_rt24s.py [--check] path/to/server.js   (harness-test only off Replit; never start server.js in the workspace)"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if 'function rt24sWordClip(' in s: print('SKIP: rt24s already applied; nothing to do'); sys.exit(0)
A = 'function safeText(value, max) {\n  return clipped(value, max).replace('
if s.count(A) != 1:
    print(f'SKIP: safeText anchor matched {s.count(A)} times (want 1); server.js left unchanged (optional patch)'); sys.exit(0)
s = s.replace(A, '''function rt24sWordClip(value, max) {
  const t = String(value || "").trim();
  if (!(max > 1) || t.length <= max) return t;
  const cut = t.slice(0, max - 1), sp = cut.lastIndexOf(" ");
  return (sp > max * 0.6 ? cut.slice(0, sp) : cut).replace(/[\\s,;:·–—-]+$/, "") + "…";
}
function safeText(value, max) {
  return rt24sWordClip(value, max).replace(''')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:300])
print('OK rt24s: safeText word-boundary clip; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
