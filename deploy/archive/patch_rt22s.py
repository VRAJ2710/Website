#!/usr/bin/env python3
"""patch_rt22s.py — server: the server-rendered home hero uses the same copy the app paints, so the old
'THE DISPATCH MARKETS · GOLD & MACRO RESEARCH' / 'A conditional weekly stance…' never flashes.
Two exact string anchors, no startup work, independent of rt20s/rt21s.
Usage: python3 patch_rt22s.py [--check] path/to/server.js     (harness-test only off Replit; never start server.js in the workspace)"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if 'eyebrow: "THE WEEK AHEAD · GOLD & MACRO",' in s: die('rt22s already applied')
E = [('    eyebrow: "THE DISPATCH MARKETS · GOLD & MACRO RESEARCH",\n', '    eyebrow: "THE WEEK AHEAD · GOLD & MACRO",\n'),
     ('    intro: "A conditional weekly stance for independent traders: gold structure, macro context, and the evidence that would confirm or invalidate the read.",\n',
      '    intro: "A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions.",\n')]
for a, c in E:
    if s.count(a) != 1: die(f'anchor matched {s.count(a)} times: {a.strip()[:50]}')
    s = s.replace(a, c)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:300])
print('OK rt22s: home hero copy; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
