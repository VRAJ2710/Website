#!/usr/bin/env python3
"""patch_rt39s.py: server. The /api/chat gold-context prefix ("Live: Gold ... / Windows: ...") fired on any question
containing level|support|resistance|macro. It now fires only when the question names gold/XAU/GC=F/bullion AND the
request carries no non-gold ticker. Safe-skip if the anchor does not match exactly once. Never runs server.js.
Usage: python3 patch_rt39s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt39s-gold' in s: print('SKIP rt39s already applied'); sys.exit(0)
old = 'if (/gold|xau|level|support|resistance|macro/i.test(_lu) && Number.isFinite(sn.goldLast))'
new = ('if (/\\b(gold|xau|gc=f|bullion)\\b/i.test(_lu) && !(Array.isArray(body && body.tickers) && body.tickers.some(t => !/^(XAU|GC=F|GLD|GOLD|IAU)$/i.test(String(t || "")))) '
       '&& Number.isFinite(sn.goldLast)) /* rt39s-gold */')
c = s.count(old)
if c != 1: print(f'SKIP gold prefix (anchor matched {c} times); server.js left as is'); sys.exit(0)
s = s.replace(old, new)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY gold prefix only for gold questions')
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
