#!/usr/bin/env python3
"""patch_rt42b.py: server only, after rt42s (production server.js 1ac7dc4e).
Ticker URL redirects /markets|stock|stocks|ticker|quote|symbol/:TICKER -> 301 /markets/?t=TICKER,
inserted right after `if (writeCanonicalRedirect(req, res)) return;` at the head of handle().
SAFE-SKIP when the two-line anchor is not found exactly once. Usage: python3 patch_rt42b.py [--check] server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt42b:' in s or '// rt42s: pretty ticker URLs' in s: print('ABORT: ticker redirects already present'); sys.exit(1)
OLD = 'async function handle(req, res) {\n  if (writeCanonicalRedirect(req, res)) return;\n'
NEW = OLD + '''  { // rt42b: pretty ticker URLs -> the markets deep link
    let rp = ""; try { rp = new URL(req.url, "http://localhost").pathname; } catch {}
    const m = req.method === "GET" || req.method === "HEAD" ? rp.match(/^\\/(?:markets|stock|stocks|ticker|quote|symbol)\\/([A-Za-z0-9^][A-Za-z0-9.\\-=^]{0,14})\\/?$/) : null;
    if (m && !/\\.(?:html?|js|css|json|xml|txt|png|jpe?g|svg|ico|webp|map|gz|br)$/i.test(m[1])) {
      res.writeHead(301, { Location: "/markets/?t=" + encodeURIComponent(m[1].toUpperCase()), "Cache-Control": "public, max-age=3600" });
      return res.end();
    }
  }
'''
n = s.count(OLD)
if n != 1: print(f'SKIP ticker redirects (anchor matched {n}x); server.js left as is'); sys.exit(0)
s = s.replace(OLD, NEW)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY ticker redirects; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
