#!/usr/bin/env python3
"""patch_rt36s.py: server. Plain SEO meta descriptions for /screener/, /sectors/, /heatmap/, /crypto/, /geo/
(the old ones described internal 'unavailable state' / 'no-sync' / 'diagnostics' handling).
Each line is safe-skip if absent. Never runs server.js. Usage: python3 patch_rt36s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt36s' in s: print('SKIP rt36s already applied; server.js left as is.'); sys.exit(0)
E = [
 ('screener', 'Run free market screens across supported quotes and keep unavailable data clearly labelled instead of silently filling gaps.', 'Screen US and global markets by move, volume, market cap, sector and more with the free Dispatch screener.'),
 ('sectors', 'Review free sector rotation and relative-strength context with explicit loading, stale, and unavailable states.', 'Track sector rotation and relative strength across the S&P 500 sectors, cyclical versus defensive.'),
 ('heatmap', 'Scan market breadth and daily moves with honest no-sync labels when a qualifying quote is unavailable.', 'See market breadth and the day\'s moves at a glance across stocks, ETFs, commodities and crypto.'),
 ('crypto', 'Review free crypto market rankings and dominance context with a visible unavailable state when the public feed cannot be reached.', 'Top 50 crypto assets by market cap, with BTC and ETH dominance and 24-hour moves.'),
 ('geo', 'Review free geopolitical and chokepoint context with bounded public event data and no internal diagnostics.', 'Geopolitical risk, shipping chokepoints and country dossiers, with the markets each one moves.'),
]
done = []
for n, o, w in E:
    c = s.count(o)
    if c != 1: print(f'SKIP {n} (anchor matched {c} times)'); continue
    s = s.replace(o, w); done.append(n)
if not done: print('Nothing to change'); sys.exit(0)
s = s.rstrip('\n') + '\n// rt36s: plain SEO descriptions\n'
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
for n in done: print('APPLY', n)
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
