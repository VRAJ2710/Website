#!/usr/bin/env python3
"""patch_rt19s.py — server: /settings/ -> app (redirect to /?settings), /favicon.ico -> logo svg.
Stacks with or without rt18s. Usage: python3 patch_rt19s.py [--check] path/to/server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT:', m); sys.exit(1)
if 'rt19sRoute' in s: die('rt19s already applied')
ANCHOR = '  attachSecurityHeaders(res);\n  if (writeCanonicalHostRedirect(req, res)) return;\n'
if s.count(ANCHOR) != 1: die(f'handle() anchor matched {s.count(ANCHOR)} times (want 1)')
FN = 'async function handle(req, res) {'
if s.count(FN) != 1: die(f'handle() declaration matched {s.count(FN)} times (want 1)')
HELPER = r'''// rt19s: tiny client-route shims (no DB, no file IO)
function rt19sRoute(req, res) {
  if (req.method !== "GET" && req.method !== "HEAD") return false;
  let pth = "/";
  try { pth = new URL(req.url || "/", "http://x").pathname; } catch (e) { return false; }
  if (pth === "/settings" || pth === "/settings/") {
    res.writeHead(302, { Location: "/?settings=1", "Cache-Control": "no-store" });
    res.end();
    return true;
  }
  if (pth === "/favicon.ico") {
    res.writeHead(301, { Location: "/logo-mark.svg", "Cache-Control": "public, max-age=86400" });
    res.end();
    return true;
  }
  return false;
}
'''
s = s.replace(FN, HELPER + FN)
s = s.replace(ANCHOR, ANCHOR + '  if (rt19sRoute(req, res)) return;\n')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:300])
print('OK rt19s: helper + 1 call; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
