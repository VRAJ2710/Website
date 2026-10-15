#!/usr/bin/env python3
"""patch_rt42s.py: server, stacks on rt41s (production server.js 1bc528b6).
A  /markets/:ticker, /stock/:t, /stocks/:t, /ticker/:t, /quote/:t, /symbol/:t  -> 301 /markets/?t=TICKER (validated)
   inserted at the top of handle(); SAFE-SKIP when the anchor is not found exactly once.
B  appended: Ask latency guard. Peer block memoised 10 min per base symbol (no refetch per question), and the
   /api/chat generateAi call gets an overall 55s deadline (it walks every provider with 25s each plus validation
   retries, which is how a question reached ~2 min), returning a clean 504 TIMEOUT instead. Logs elapsed ms.
Usage: python3 patch_rt42s.py [--check] server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt42s:' in s: print('ABORT: rt42s already applied'); sys.exit(1)
if 'rt41s:' not in s: print('ABORT: rt41s not present (apply rt41s first)'); sys.exit(1)
A_OLD = 'async function handle(req, res) {\n  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);\n  const p = url.pathname;\n'
A_NEW = A_OLD + '''  { // rt42s: pretty ticker URLs -> the markets deep link
    const m = req.method === "GET" || req.method === "HEAD" ? p.match(/^\\/(?:markets|stock|stocks|ticker|quote|symbol)\\/([A-Za-z0-9^][A-Za-z0-9.\\-=^]{0,14})\\/?$/) : null;
    if (m && !/\\.(?:html?|js|css|json|xml|txt|png|jpe?g|svg|ico|webp|map|gz|br)$/i.test(m[1])) {
      res.writeHead(301, { Location: "/markets/?t=" + encodeURIComponent(m[1].toUpperCase()), "Cache-Control": "public, max-age=3600" });
      return res.end();
    }
  }
'''
n = s.count(A_OLD)
if n == 1: s = s.replace(A_OLD, A_NEW); print('APPLY A ticker URL redirects')
else: print(f'SKIP  A ticker URL redirects (anchor matched {n}x); server.js otherwise patched')
B = r'''
// rt42s: Ask latency guard (memoised peer block + overall deadline on /api/chat generations)
try {
  if (typeof rt41sPeerBlock === "function") {
    const rt42sPb0 = rt41sPeerBlock, rt42sPbMemo = new Map();
    rt41sPeerBlock = async function (base) {
      const hit = rt42sPbMemo.get(base);
      if (hit && Date.now() - hit.at < 10 * 60e3) return hit.v;
      const v = await rt42sPb0(base);
      if (v) rt42sPbMemo.set(base, { at: Date.now(), v });
      return v;
    };
  }
  const rt42sGen0 = generateAi;
  generateAi = async function (options, ...rest) {
    const isChat = options && typeof options.system === "string" && options.system.includes('{"reply":"string"') && Array.isArray(options.messages);
    if (!isChat) return rt42sGen0.call(this, options, ...rest);
    const t0 = Date.now(); let timer;
    try {
      return await Promise.race([
        rt42sGen0.call(this, options, ...rest),
        new Promise((_, rej) => { timer = setTimeout(() => rej(new AiRequestError(504, "The research assistant took too long to answer. Please try again.", "TIMEOUT")), 55000); }),
      ]);
    } finally { clearTimeout(timer); console.warn("rt42s chat ms", Date.now() - t0); }
  };
} catch (e) { console.warn("rt42s latency guard skipped"); }
'''
s = s.rstrip('\n') + '\n' + B
print('APPLY B Ask latency guard')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed', r.stderr[:400]); sys.exit(1)
print('node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
