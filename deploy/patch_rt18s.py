#!/usr/bin/env python3
"""patch_rt18s.py — server: gzip/brotli for static text assets (node zlib, no deps).
Usage: python3 patch_rt18s.py [--check] <path/to/server.js>
Adds one helper block before `async function handle(req, res) {` and one call
as the first statement after `const p = url.pathname;` in handle().
"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
if not args: print('usage: patch_rt18s.py [--check] server.js'); sys.exit(2)
F = args[0]
def die(m): print('ABORT:', m); sys.exit(1)
raw = open(F, 'rb').read(); crlf = b'\r\n' in raw
s = raw.decode('utf-8').replace('\r\n', '\n')
if 'rt18s:' in s or 'rt18sWrapResponse' in s: die('rt18s already applied')
for need in ['const fs = require("fs");', 'const path = require("path");', 'const root = __dirname;', 'res.writeHead(']:
    if need not in s: die('precondition missing: ' + need)
for bad in ['createGzip', 'brotliCompress', '"Content-Encoding"', "'Content-Encoding'", 'compression()']:
    if bad in s: die('server already does compression (' + bad + '); not stacking')
ANCHOR = 'async function handle(req, res) {\n  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);\n  const p = url.pathname;\n'
n = s.count(ANCHOR)
if n != 1: die(f'handle() anchor matched {n} times (want 1)')
BLOCK = r"""// ── rt18s: static text compression (gzip / brotli via node zlib) ──
// Wraps the response object at the top of handle(): compressible static responses
// (html/css/js/svg/json, not /api/*) are gzip/brotli-encoded per Accept-Encoding;
// app.js and styles.css are precompressed once per process (async, keyed by mtime).
// Existing status codes and cache headers are kept; 304/HEAD/ranges are untouched.
const rt18sZlib = require("zlib");
const RT18S_CT = /^(text\/(html|css|javascript|plain)|application\/(javascript|json|manifest\+json)|image\/svg\+xml)\b/i;
const RT18S_PRE = { "/app.js": "app.js", "/styles.css": "styles.css" };
const rt18sPreCache = new Map(); // name -> { mtimeMs, gzip, br, pending }
function rt18sAccepts(req) {
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
function rt18sPrecompressed(name, enc) {
  let st;
  try { st = fs.statSync(path.join(root, name)); } catch (e) { return null; }
  let entry = rt18sPreCache.get(name);
  if (!entry || entry.mtimeMs !== st.mtimeMs) {
    entry = { mtimeMs: st.mtimeMs, gzip: null, br: null, pending: true };
    rt18sPreCache.set(name, entry);
    fs.readFile(path.join(root, name), (err, buf) => {
      if (err) { entry.pending = false; return; }
      // Async (libuv threadpool): never blocks the event loop.
      rt18sZlib.gzip(buf, { level: 9 }, (e1, gz) => { if (!e1) entry.gzip = gz; });
      rt18sZlib.brotliCompress(buf, { params: { [rt18sZlib.constants.BROTLI_PARAM_QUALITY]: 11, [rt18sZlib.constants.BROTLI_PARAM_SIZE_HINT]: buf.length } }, (e2, br) => { if (!e2) entry.br = br; entry.pending = false; });
    });
  }
  return entry[enc] || null;
}
function rt18sWrapResponse(req, res, pathname) {
  if (req.method !== "GET" && req.method !== "HEAD") return;
  if (pathname.startsWith("/api/") || req.headers.range) return;
  const enc = rt18sAccepts(req);
  const origWriteHead = res.writeHead, origWrite = res.write, origEnd = res.end;
  let mode = null, pre = null, z = null; // mode: "plain" | "pre" | "stream"
  res.writeHead = function (status, a, b) {
    if (mode) return origWriteHead.apply(this, arguments);
    mode = "plain";
    let headers = (typeof a === "object" && a) ? a : (typeof b === "object" && b) ? b : null;
    const reason = typeof a === "string" ? a : undefined;
    const call = () => origWriteHead.call(this, status, ...(reason ? [reason] : []), ...(headers ? [headers] : []));
    const get = k => {
      if (headers) { const hk = Object.keys(headers).find(x => x.toLowerCase() === k); if (hk) return headers[hk]; }
      return res.getHeader(k);
    };
    const del = k => {
      if (headers) Object.keys(headers).forEach(x => { if (x.toLowerCase() === k) delete headers[x]; });
      res.removeHeader(k);
    };
    if (RT18S_PRE[pathname] && /[?&]v=/.test(req.url || "") && !/max-age=\d{4,}/i.test(String(get("cache-control") || ""))) {
      del("cache-control"); res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
    }
    const ct = String(get("content-type") || "");
    const compressible = status === 200 && RT18S_CT.test(ct) && !get("content-encoding");
    if (!compressible) return call();
    const vary = String(get("vary") || "");
    if (!/accept-encoding/i.test(vary)) { del("vary"); res.setHeader("Vary", vary ? `${vary}, Accept-Encoding` : "Accept-Encoding"); }
    const len = Number(get("content-length"));
    if (!enc || (Number.isFinite(len) && len > 0 && len < 1024)) return call();
    const etag = get("etag");
    if (etag) { del("etag"); res.setHeader("ETag", String(etag).replace(/"$/, `-${enc}"`)); }
    del("content-length");
    res.setHeader("Content-Encoding", enc);
    const preName = RT18S_PRE[pathname];
    pre = preName ? rt18sPrecompressed(preName, enc) : null;
    if (pre) { res.setHeader("Content-Length", pre.length); mode = "pre"; return call(); }
    mode = "stream";
    call();
    if (req.method !== "HEAD") {
      z = enc === "br"
        ? rt18sZlib.createBrotliCompress({ params: { [rt18sZlib.constants.BROTLI_PARAM_QUALITY]: 5 } })
        : rt18sZlib.createGzip({ level: 6 });
      z.on("data", d => origWrite.call(res, d));
      z.on("end", () => origEnd.call(res));
      z.on("error", () => { try { origEnd.call(res); } catch (e) {} });
    }
    return res;
  };
  // write/end are wrapped up front so an implicit header (setHeader + end(buf)) is handled too.
  const head = () => { if (!mode && !res.headersSent) res.writeHead(res.statusCode); };
  res.write = function (chunk, encoding, cb) {
    head();
    if (mode === "pre") return true;
    if (mode === "stream") { if (z) z.write(chunk, typeof encoding === "string" ? encoding : undefined); if (typeof encoding === "function") encoding(); else if (cb) cb(); return true; }
    return origWrite.apply(res, arguments);
  };
  res.end = function (chunk, encoding, cb) {
    head();
    const done = typeof chunk === "function" ? chunk : typeof encoding === "function" ? encoding : cb;
    if (mode === "pre") return origEnd.call(res, req.method === "HEAD" ? undefined : pre, done);
    if (mode === "stream") {
      if (!z) return origEnd.call(res, done);
      if (chunk != null && typeof chunk !== "function") z.end(chunk, typeof encoding === "string" ? encoding : undefined); else z.end();
      if (done) res.once("finish", done);
      return res;
    }
    return origEnd.apply(res, arguments);
  };
}
// Warm the precompressed cache at boot (async, off the event loop).
setImmediate(() => { Object.values(RT18S_PRE).forEach(n => { rt18sPrecompressed(n, "gzip"); }); });
"""
s = s.replace(ANCHOR, BLOCK + '\n' + ANCHOR + '  rt18sWrapResponse(req, res, p);\n')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt18s: 2 insertions; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(F, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', F)
