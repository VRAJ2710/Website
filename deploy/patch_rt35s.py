#!/usr/bin/env python3
"""patch_rt35s.py: server. Makes "start your Premium checkout" on /__auth/login a real link to /__auth/subscribe.
Safe-skip if absent.
Usage: python3 patch_rt35s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt35s-login-link' in s: print('SKIP rt35s already applied; server.js left as is.'); sys.exit(0)
OLD = 'or start your Premium checkout.</p>'
NEW = 'or <a class="rt35s-login-link" href="/__auth/subscribe" style="display:inline;margin:0;padding:0;background:none;color:#f5a623;font-weight:600">start your Premium checkout</a>.</p>'
n = s.count(OLD)
if n != 1: print(f'SKIP login checkout link (anchor matched {n} times)'); sys.exit(0)
s = s.replace(OLD, NEW)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY login checkout link')
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
