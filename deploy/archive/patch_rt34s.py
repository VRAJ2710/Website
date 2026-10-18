#!/usr/bin/env python3
"""patch_rt34s.py: server. Adds Terms / Privacy links to every /__auth page (shared page() template).
Pair with rt33s (which serves /terms and /privacy). Safe-skip if the anchor is absent; never runs server.js.
Usage: python3 patch_rt34s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt34s-legal' in s: print('SKIP rt34s already applied; server.js left as is.'); sys.exit(0)
OLD = '<body><main>${content}</main></body></html>`);'
NEW = '<body><main>${content}<p class="muted rt34s-legal" style="margin:22px 0 0;text-align:center"><a href="/terms" style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Terms</a> · <a href="/privacy" style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Privacy</a></p></main></body></html>`);'
n = s.count(OLD)
if n != 1: print(f'SKIP auth legal links (anchor matched {n} times)'); sys.exit(0)
s = s.replace(OLD, NEW)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY auth legal links')
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
