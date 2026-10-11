#!/usr/bin/env python3
"""patch_rt20s.py — lazy static compression for server.js (replaces the failed rt18s).
  python3 patch_rt20s.py --check  server.js   dry run
  python3 patch_rt20s.py          server.js   apply
  python3 patch_rt20s.py --selftest server.js [--port 3999] [--timeout 90]
      starts `node server.js` with PORT=3999, waits for the port, then checks
      GET / and HEAD / (plain and br), and /app.js Content-Encoding. Exit 0 = pass.
"""
import sys, os, subprocess, tempfile, time, socket, urllib.request, re, zlib
BLOCK = r'''// ── rt20s: static text compression (gzip 6 / brotli 5 via node zlib) ──
// Zero startup work: nothing is read or compressed until the first request asks for it.
// Any failure inside the shim falls back to the plain, uncompressed response; end() always fires.
// Kill switch: DISPATCH_COMPRESSION=0 disables the shim without a code change.
const rt20sZlib = require("zlib");
const RT20S_ON = process.env.DISPATCH_COMPRESSION !== "0";
const RT20S_CT = /^(text\/(html|css|javascript|plain)|application\/(javascript|json|manifest\+json)|image\/svg\+xml)\b/i;
const RT20S_PRE = new Set(["/app.js", "/styles.css"]);
const RT20S_BR = { params: { [rt20sZlib.constants.BROTLI_PARAM_QUALITY]: 5 } };
const RT20S_GZ = { level: 6 };
const rt20sCache = new Map(); // `${path}|${enc}|${size}|${etag||mtime}` -> Buffer (filled lazily from a served response)
function rt20sAccepts(req) {
  const out = {};
  String(req.headers["accept-encoding"] || "").split(",").forEach(part => {
    const [tok, ...params] = part.trim().toLowerCase().split(";");
    if (!tok) return;
    let q = 1;
    params.forEach(pv => { const m = /^\s*q=([0-9.]+)\s*$/.exec(pv); if (m) q = Number(m[1]); });
    out[tok] = q;
  });
  const ok = enc => (out[enc] ?? out["*"] ?? 0) > 0;
  return ok("br") ? "br" : ok("gzip") ? "gzip" : null;
}
function rt20sWrapResponse(req, res) {
  if (!RT20S_ON) return;
  try {
    if (req.method !== "GET" && req.method !== "HEAD") return;
    if (req.headers.range) return;
    let pathname = "/";
    try { pathname = new URL(req.url || "/", "http://localhost").pathname; } catch (e) { return; }
    if (pathname.startsWith("/api/") || pathname.startsWith("/__")) return;
    const enc = rt20sAccepts(req);
    const isPre = RT20S_PRE.has(pathname);
    const versioned = isPre && /[?&]v=/.test(req.url || "");
    if (!enc && !versioned) return; // nothing to do for this request
    const oWriteHead = res.writeHead, oWrite = res.write, oEnd = res.end;
    let mode = null; // "plain" | "stream" | "cached"
    let z = null, cached = null, cacheKey = null, cacheParts = null, cacheBytes = 0;
    const restore = () => { res.writeHead = oWriteHead; res.write = oWrite; res.end = oEnd; };
    res.writeHead = function (status, a, b) {
      if (mode) return oWriteHead.apply(this, arguments);
      mode = "plain";
      const args = arguments;
      try {
        const headers = (a && typeof a === "object" && !Array.isArray(a)) ? a : (b && typeof b === "object" && !Array.isArray(b)) ? b : null;
        if ((a && Array.isArray(a)) || (b && Array.isArray(b))) { restore(); return oWriteHead.apply(this, args); }
        const get = k => { if (headers) { const hk = Object.keys(headers).find(x => x.toLowerCase() === k); if (hk) return headers[hk]; } return res.getHeader(k); };
        const del = k => { if (headers) Object.keys(headers).forEach(x => { if (x.toLowerCase() === k) delete headers[x]; }); res.removeHeader(k); };
        if (versioned && status === 200 && !/max-age=\d{4,}/i.test(String(get("cache-control") || ""))) {
          del("cache-control"); res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
        }
        const ct = String(get("content-type") || "");
        const compressible = status === 200 && RT20S_CT.test(ct) && !get("content-encoding");
        if (compressible) {
          const vary = String(get("vary") || "");
          if (!/accept-encoding/i.test(vary)) { del("vary"); res.setHeader("Vary", vary ? `${vary}, Accept-Encoding` : "Accept-Encoding"); }
        }
        const len = Number(get("content-length"));
        if (!compressible || !enc || (Number.isFinite(len) && len > 0 && len < 1024)) { restore(); return oWriteHead.apply(this, args); }
        const etag = get("etag");
        if (isPre) cacheKey = `${pathname}|${enc}|${Number.isFinite(len) ? len : "?"}|${etag || ""}`;
        cached = cacheKey && Number.isFinite(len) ? rt20sCache.get(cacheKey) || null : null;
        if (etag) { del("etag"); res.setHeader("ETag", String(etag).replace(/"$/, `-${enc}"`)); }
        del("content-length");
        res.setHeader("Content-Encoding", enc);
        if (cached) { res.setHeader("Content-Length", cached.length); mode = "cached"; return oWriteHead.apply(this, args); }
        if (req.method === "HEAD") { mode = "cached"; cached = null; return oWriteHead.apply(this, args); }
        z = enc === "br" ? rt20sZlib.createBrotliCompress(RT20S_BR) : rt20sZlib.createGzip(RT20S_GZ);
        if (cacheKey && Number.isFinite(len)) cacheParts = [];
        z.on("data", d => { if (cacheParts) { cacheParts.push(d); cacheBytes += d.length; if (cacheBytes > 8e6) cacheParts = null; } try { oWrite.call(res, d); } catch (e) {} });
        z.on("end", () => { if (cacheParts) rt20sCache.set(cacheKey, Buffer.concat(cacheParts)); try { oEnd.call(res); } catch (e) {} });
        z.on("error", () => { try { oEnd.call(res); } catch (e) {} });
        res.once("close", () => { try { if (z && !z.writableEnded) z.destroy(); } catch (e) {} });
        mode = "stream";
        return oWriteHead.apply(this, args);
      } catch (e) {
        // Any failure before headers are sent: plain response.
        restore();
        if (!res.headersSent) return oWriteHead.apply(this, args);
        return res;
      }
    };
    const head = () => { if (!mode && !res.headersSent) res.writeHead(res.statusCode); };
    res.write = function (chunk, encoding, cb) {
      try { head(); } catch (e) {}
      if (mode === "cached") { const done = typeof encoding === "function" ? encoding : cb; if (done) process.nextTick(done); return true; }
      if (mode === "stream" && z) { try { z.write(chunk, typeof encoding === "string" ? encoding : undefined); } catch (e) {} const done = typeof encoding === "function" ? encoding : cb; if (done) process.nextTick(done); return true; }
      return oWrite.apply(res, arguments);
    };
    res.end = function (chunk, encoding, cb) {
      try { head(); } catch (e) {}
      const done = typeof chunk === "function" ? chunk : typeof encoding === "function" ? encoding : cb;
      if (mode === "cached") return oEnd.call(res, (req.method === "HEAD" || !cached) ? undefined : cached, done);
      if (mode === "stream" && z) {
        try {
          if (chunk != null && typeof chunk !== "function") z.end(chunk, typeof encoding === "string" ? encoding : undefined); else z.end();
        } catch (e) { try { oEnd.call(res); } catch (e2) {} }
        if (done) res.once("finish", done);
        return res;
      }
      return oEnd.apply(res, arguments);
    };
  } catch (e) { /* leave the response untouched */ }
}
'''
argv = sys.argv[1:]
def opt(name, default):
    if name in argv: i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
    return default
PORT = int(opt('--port', '3999')); TMO = float(opt('--timeout', '90'))
CHECK = '--check' in argv; SELF = '--selftest' in argv
args = [a for a in argv if not a.startswith('--')]
P = args[0] if args else 'server.js'
def die(m): print('ABORT:', m); sys.exit(1)

def selftest(path):
    d = os.path.dirname(os.path.abspath(path))
    src = open(path, encoding='utf-8').read()
    if 'rt20sWrapResponse(req, res);' not in src: die('selftest: rt20s is not applied to ' + path)
    env = dict(os.environ, PORT=str(PORT))
    log = open(os.path.join(tempfile.gettempdir(), f'rt20s_selftest_{PORT}.log'), 'w')
    t0 = time.time()
    proc = subprocess.Popen(['node', os.path.basename(path)], cwd=d, env=env, stdout=log, stderr=subprocess.STDOUT)
    fails = []
    try:
        up = None
        while time.time() - t0 < TMO:
            if proc.poll() is not None: break
            try:
                socket.create_connection(('127.0.0.1', PORT), timeout=0.5).close(); up = time.time() - t0; break
            except OSError: time.sleep(0.1)
        if up is None:
            die(f'server did not open port {PORT} within {TMO:.0f}s (exit={proc.poll()}); see {log.name}')
        print(f'  time-to-listen: {up:.2f}s')
        def req(method, url, ae):
            h = {'Accept-Encoding': ae} if ae else {}
            r = urllib.request.Request(f'http://127.0.0.1:{PORT}{url}', method=method, headers=h)
            t = time.time()
            try:
                with urllib.request.urlopen(r, timeout=20) as resp:
                    body = resp.read(); return resp.status, dict((k.lower(), v) for k, v in resp.getheaders()), body, time.time() - t
            except urllib.error.HTTPError as e:
                return e.code, dict((k.lower(), v) for k, v in e.headers.items()), e.read(), time.time() - t
        def chk(name, cond, info=''):
            print(('  PASS ' if cond else '  FAIL ') + name + (f'  [{info}]' if info else ''))
            if not cond: fails.append(name)
        s, h, b, dt = req('GET', '/', None)
        chk('GET / plain 200, no Content-Encoding', s == 200 and 'content-encoding' not in h and len(b) > 0, f'{s} {len(b)}B {dt*1000:.0f}ms')
        s, h, b, dt = req('HEAD', '/', None)
        chk('HEAD / plain 200, empty body', s == 200 and len(b) == 0, f'{s} {dt*1000:.0f}ms')
        s, h, b, dt = req('GET', '/', 'br, gzip')
        chk('GET / br 200', s == 200, f'{s} enc={h.get("content-encoding")} {len(b)}B {dt*1000:.0f}ms')
        s, h, b, dt = req('HEAD', '/', 'br, gzip')
        chk('HEAD / br 200, empty body', s == 200 and len(b) == 0, f'{s} enc={h.get("content-encoding")} {dt*1000:.0f}ms')
        s, h, b, dt = req('GET', '/', 'gzip')
        ok = s == 200
        if h.get('content-encoding') == 'gzip':
            try: zlib.decompress(b, 16 + zlib.MAX_WBITS)
            except Exception: ok = False
        chk('GET / gzip decodes', ok, f'enc={h.get("content-encoding")}')
        m = re.search(r'/app\.js\?v=[^"\'\s>]+', req('GET', '/', None)[2].decode('utf-8', 'replace'))
        app = m.group(0) if m else '/app.js'
        for i in (1, 2):
            s, h, b, dt = req('GET', app, 'br, gzip')
            chk(f'GET {app} br (request {i}) Content-Encoding=br, Vary', s == 200 and h.get('content-encoding') == 'br' and 'accept-encoding' in h.get('vary', '').lower(), f'{s} {len(b)}B {dt*1000:.0f}ms cc={h.get("cache-control")}')
        s, h, b, dt = req('GET', app, None)
        chk(f'GET {app} plain, no Content-Encoding', s == 200 and 'content-encoding' not in h, f'{len(b)}B')
    finally:
        proc.terminate()
        try: proc.wait(5)
        except Exception: proc.kill()
        log.close()
    if fails: print(f'SELFTEST FAILED ({len(fails)}): ' + '; '.join(fails)); sys.exit(2)
    print('SELFTEST PASSED'); sys.exit(0)

if SELF: selftest(P)
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt20sWrapResponse' in s: die('rt20s already applied')
if 'rt18sWrapResponse' in s: die('rt18s is present; roll it back first (rt20s replaces it)')
ANCHOR = '  attachSecurityHeaders(res);\n  if (writeCanonicalHostRedirect(req, res)) return;\n'
FN = 'async function handle(req, res) {'
if s.count(ANCHOR) != 1: die(f'handle() anchor matched {s.count(ANCHOR)} times (want 1)')
if s.count(FN) != 1: die(f'handle() declaration matched {s.count(FN)} times (want 1)')
s = s.replace(FN, BLOCK + FN).replace(ANCHOR, ANCHOR + '  rt20sWrapResponse(req, res);\n')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:300])
print('OK rt20s: helper block + 1 call; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
    print(f'next: python3 {os.path.basename(sys.argv[0])} --selftest {P}')
