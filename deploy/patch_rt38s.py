#!/usr/bin/env python3
"""patch_rt38s.py: server, stacks on rt37s. CoinGecko cold miss: when this instance has no in-memory copy, ask the
original handler and pass its answer through ONLY if its X-Dispatch-Data-As-Of is under 24h (or it is marked fresh);
otherwise answer {unavailable} as before (the client then fetches CoinGecko directly). Safe-skip. Never runs server.js.
Usage: python3 patch_rt38s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt38sCgAged' in s: print('SKIP rt38s already applied'); sys.exit(0)
old = '''  try { const g = fresh.get(path) || fam.get(famKey(path)); if (g && Date.now() - g.at < 24 * 3600_000) return fallback(res, path); } catch {}
  return fallback(res, path);
}'''
new = '''  try { const g = fresh.get(path) || fam.get(famKey(path)); if (g && Date.now() - g.at < 24 * 3600_000) return fallback(res, path); } catch {}
  return rt38sCgAged(req, res, rawPath, path, original, fallback);
}'''
c = s.count(old)
if c != 1: print(f'SKIP coingecko aged pass-through (anchor matched {c} times); server.js left as is'); sys.exit(0)
s = s.replace(old, new).rstrip('\n') + r'''

// rt38s: pass the original handler's persisted CoinGecko copy through only when it is under 24h old
function rt38sCgAged(req, res, rawPath, path, original, fallback) {
  const hdr = {}; let status = 200, done = false; const chunks = [];
  const o = { setHeader: res.setHeader, writeHead: res.writeHead, write: res.write, end: res.end };
  const restore = () => { res.setHeader = o.setHeader; res.writeHead = o.writeHead; res.write = o.write; res.end = o.end; };
  const bail = () => { if (done) return; done = true; restore(); try { fallback(res, path); } catch {} };
  res.setHeader = (k, v) => { hdr[String(k).toLowerCase()] = v; return res; };
  res.writeHead = (st, a, b2) => { status = st; const h = a && typeof a === "object" ? a : (b2 || {}); for (const [k, v] of Object.entries(h)) hdr[k.toLowerCase()] = v; return res; };
  res.write = c => { if (c) chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c))); return true; };
  res.end = c => {
    if (done) return res; done = true;
    if (c) chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c)));
    restore();
    const ao = Date.parse(hdr["x-dispatch-data-as-of"] || "");
    const ok = status === 200 && (ao ? Date.now() - ao < 24 * 3600_000 : String(hdr["x-dispatch-data-status"] || "") === "fresh");
    if (!ok) { try { fallback(res, path); } catch {} return res; }
    res.writeHead(status, hdr); return res.end(Buffer.concat(chunks));
  };
  setTimeout(bail, 12_000).unref?.();
  try { const r = original(req, res, rawPath); if (r && typeof r.catch === "function") r.catch(bail); return r; } catch { bail(); }
}
'''
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
print('APPLY coingecko aged pass-through')
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
