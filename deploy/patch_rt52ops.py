#!/usr/bin/env python3
"""patch_rt52ops.py — stop the static file handler from publishing the workspace.

Production (thedispatch.uk, Replit Autoscale, server.js md5 e4a4a1f0e18d192357b8dd6c07928ade,
7581 lines) is a raw Node http server. There is no express.static and no sendFile.
serveStatic reads the workspace root, so uv.lock, pnpm-lock.yaml, zipFile.zip, deploy/,
artifacts/, .pythonlibs, and *.bak* files are public today.

This patch inserts an allowlist at the top of:

    function serveStatic(req, res, pathname, searchParams) {

That line must match exactly once. The caller must also match exactly once:

    if (serveStatic(req, res, p, url.searchParams)) return;

If that caller falls through to the normal 404, denied paths return false and the
existing not-found runs (same 404 the site already sends). If the caller instead
falls through to an SPA / index.html shell, denied paths write the 404 themselves
and return true so the shell cannot resurrect a leaked file. Paths that are neither
allowlisted nor denied (client routes such as /settings, /markets/AAPL, /api/*)
always return false, so API routing and the SPA fallback stay with the caller.

Allowed through to the existing body (query string untouched, so ?v=chat56 still
works, and /favicon.ico plus /index.html still hit whatever redirect the body or
the canonical-host redirect already implements):

  /, /index.html, /favicon.ico, /app.js, /styles.css,
  root images (.svg .png .jpg .jpeg .ico .webp .gif),
  /manifest.json, /robots.txt, /sitemap.xml, /llms.txt,
  route index documents from the chat56 manifest and sitemap:
    pricing, brief, playbook, gold, markets, news, research, signals,
    dashboard, learn, portfolio, watchlist, lab, screener, sectors, heatmap,
    crypto, paper, geo, brief/dispatch-brief, report/spx2026,
    research/research-desk
  (also the explicit <route>/index.html path, so either pathname serveStatic
  already accepts keeps working). /settings is the home shell, not a static
  file (live /settings/index.html is 404); it is left to the caller.

Belt-and-braces denylist, case-insensitive, after decoding and after rejecting
.. traversal: *.lock *.yaml *.yml *.zip *.bak* *.backup *.py *.md, dotfiles, and
/deploy/ /artifacts/ /.pythonlibs/ /node_modules/.

/og-card.png is still served by the existing body, but Content-Type is forced to
image/png and Cache-Control to public, max-age=86400.

Idempotent: a second run prints that rt52ops is already present and writes nothing.
Anchor missing or repeated: ABORT, nothing written. Never runs node server.js
(node --check on a temp copy only).

Usage:
  python3 deploy/patch_rt52ops.py --dry-run /tmp/server.js   # diff, do not write
  python3 deploy/patch_rt52ops.py --check   /tmp/server.js   # same, one-line summary
  python3 deploy/patch_rt52ops.py /tmp/server.js             # write that copy

Jack: copy the live server.js to /tmp first. Dry-run that copy. Do not point this
script at the running file until the diff has been read. Do not start server.js.
"""
import difflib, os, re, subprocess, sys, tempfile

FN = 'function serveStatic(req, res, pathname, searchParams) {'
CALL = '  if (serveStatic(req, res, p, url.searchParams)) return;'
MARKER = '// ── rt52ops:'

HELPERS = r'''// ── rt52ops: workspace-root static allowlist. Only the public site files
// fall through to the original serveStatic body. Leaks return before any read.
const RT52OPS_WRITE_DENY = __RT52OPS_WRITE_DENY__;
const RT52OPS_ROUTES = ["pricing","brief","playbook","gold","markets","news","research","signals","dashboard","learn","portfolio","watchlist","lab","screener","sectors","heatmap","crypto","paper","geo","brief/dispatch-brief","report/spx2026","research/research-desk"];
const RT52OPS_ASSET_DIRS = []; // chat56 images are at the workspace root (logo, og-card, founder)
const RT52OPS_ROOT_FILES = new Set(["/app.js","/styles.css","/manifest.json","/robots.txt","/sitemap.xml","/llms.txt","/favicon.ico","/index.html"]);
function rt52opsNormalize(pathname) {
  if (pathname == null) return null;
  let p = String(pathname);
  if (p.indexOf("\0") !== -1) return null;
  p = p.split("#")[0].split("?")[0];
  for (let i = 0; i < 4; i++) {
    let d;
    try { d = decodeURIComponent(p); } catch (e) { break; }
    if (d === p) break;
    p = d;
  }
  if (p.indexOf("\0") !== -1) return null;
  p = p.replace(/\\/g, "/");
  if (p.charAt(0) !== "/") p = "/" + p;
  const parts = [];
  for (const seg of p.split("/")) {
    if (seg === "" || seg === ".") continue;
    if (seg === "..") return null;
    parts.push(seg);
  }
  return "/" + parts.join("/");
}
function rt52opsClassify(norm) {
  if (norm == null) return "deny";
  const path = String(norm);
  const lower = path.toLowerCase();
  const segs = lower.split("/").filter(Boolean);
  for (const seg of segs) {
    if (seg.charAt(0) === ".") return "deny";
    // *.bak* (file.bak, file.bak1, server.js.bak-rt48c) and *.backup*
    if (seg.indexOf(".bak") !== -1 || seg.indexOf(".backup") !== -1) return "deny";
    if (/\.(?:lock|ya?ml|zip|py|md)$/i.test(seg)) return "deny";
  }
  if (lower === "/deploy" || lower.indexOf("/deploy/") === 0) return "deny";
  if (lower === "/artifacts" || lower.indexOf("/artifacts/") === 0) return "deny";
  if (lower === "/.pythonlibs" || lower.indexOf("/.pythonlibs/") === 0) return "deny";
  if (lower === "/node_modules" || lower.indexOf("/node_modules/") === 0) return "deny";
  if (lower === "/" || lower === "/index.html") return "allow";
  if (RT52OPS_ROOT_FILES.has(lower)) return "allow";
  const slash = lower.lastIndexOf("/");
  const base = lower.slice(slash + 1);
  const dir = slash <= 0 ? "/" : lower.slice(0, slash);
  if (base === "og-card.png" && dir === "/") return "og";
  if (/\.(?:svg|png|jpe?g|ico|webp|gif)$/i.test(base)) {
    if (dir === "/") return "allow";
    for (let i = 0; i < RT52OPS_ASSET_DIRS.length; i++) {
      const d = RT52OPS_ASSET_DIRS[i];
      if (dir === d || dir.indexOf(d + "/") === 0) return "allow";
    }
  }
  for (let i = 0; i < RT52OPS_ROUTES.length; i++) {
    const r = "/" + RT52OPS_ROUTES[i];
    if (lower === r || lower === r + "/index.html") return "allow";
  }
  return "skip";
}
function rt52opsEsc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
  });
}
function rt52opsWriteNotFound(res, pathname) {
  const shown = rt52opsEsc(pathname || "/");
  const body = '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page not found | The Dispatch Markets</title><style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px system-ui;display:grid;place-items:center;min-height:100vh}main{width:min(620px,calc(100% - 40px));background:#111a26;border:1px solid #293849;border-radius:14px;padding:28px;box-sizing:border-box}h1{font-size:28px;margin:0 0 8px;color:#f5a623}p,li{color:#9baabb;line-height:1.6}a{color:#f5a623}ul{padding-left:22px}</style></head><body><main><p>THE DISPATCH MARKETS · 404</p><h1>That market page is not here</h1><p>We could not find <strong>' + shown + '</strong>. Continue with a public market surface:</p><ul><li><a href="/">Know what matters before gold moves.</a></li><li><a href="/brief/">Dispatch Brief: a daily market view</a></li><li><a href="/playbook/">Weekly Playbook: conditional gold and macro scenarios</a></li><li><a href="/gold/">Gold Desk: structure, levels, and macro context</a></li><li><a href="/markets/">Markets: prices, sectors, and cross-asset context</a></li><li><a href="/news/">Newsroom: market news with context</a></li><li><a href="/research/">Research Desk: explain the market before acting</a></li></ul></main></body></html>';
  res.writeHead(404, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  res.end(body);
}
function rt52opsPinOgCard(res) {
  if (!res || res.__rt52opsOg) return;
  try { Object.defineProperty(res, "__rt52opsOg", { value: true }); } catch (e) { res.__rt52opsOg = true; }
  const origSet = res.setHeader, origWrite = res.writeHead;
  const CT = "image/png", CC = "public, max-age=86400";
  if (typeof origSet === "function") {
    res.setHeader = function (name, value) {
      const n = String(name).toLowerCase();
      if (n === "content-type") value = CT;
      else if (n === "cache-control") value = CC;
      return origSet.call(this, name, value);
    };
  }
  if (typeof origWrite === "function") {
    res.writeHead = function (status, a, b) {
      const fix = function (headers) {
        if (!headers || typeof headers !== "object" || Array.isArray(headers)) return headers;
        const out = {};
        const keys = Object.keys(headers);
        for (let i = 0; i < keys.length; i++) {
          const n = keys[i].toLowerCase();
          if (n === "content-type" || n === "cache-control") continue;
          out[keys[i]] = headers[keys[i]];
        }
        out["Content-Type"] = CT;
        out["Cache-Control"] = CC;
        return out;
      };
      try { if (typeof origSet === "function") origSet.call(this, "Content-Type", CT); } catch (e) {}
      try { if (typeof origSet === "function") origSet.call(this, "Cache-Control", CC); } catch (e) {}
      if (a && typeof a === "object" && !Array.isArray(a)) return origWrite.call(this, status, fix(a));
      if (b && typeof b === "object" && !Array.isArray(b)) return origWrite.call(this, status, a, fix(b));
      return origWrite.apply(this, arguments);
    };
  }
}
'''

GUARD = '''  const rt52opsNorm = rt52opsNormalize(pathname);
  const rt52opsCls = rt52opsClassify(rt52opsNorm);
  if (rt52opsCls === "deny") {
    if (RT52OPS_WRITE_DENY) { rt52opsWriteNotFound(res, rt52opsNorm || pathname || "/"); return true; }
    return false;
  }
  if (rt52opsCls !== "allow" && rt52opsCls !== "og") return false;
  if (rt52opsCls === "og") rt52opsPinOgCard(res);
'''


def die(m):
    print('ABORT:', m)
    sys.exit(1)


def caller_window(src):
    n = src.count(CALL)
    if n != 1:
        die('serveStatic caller matched %d times (want 1): %s' % (n, CALL.strip()))
    i = src.find(CALL)
    # The tail of handle() after the call. Long enough to see a 404 or an SPA shell,
    # short of scanning the rest of a 7k-line file into a false match.
    return '\n'.join(src[i + len(CALL):].splitlines()[:80])


def deny_writes(window):
    spa = re.search(
        r'serveStatic\(\s*req\s*,\s*res\s*,\s*[\'\"]/?index\.html|sendSpa|spaFallback|sendFile\([^\n]*index\.html',
        window,
    )
    not_found = re.search(r'\b404\b|Not found|notFound|Page not found', window)
    if spa and not not_found:
        return True
    if not_found and not spa:
        return False
    if spa and not_found:
        if not_found.start() < spa.start():
            return False
        return True
    die('after the serveStatic call, the handler neither 404s nor falls back to a shell; refusing to guess')


def transform(src):
    if MARKER in src:
        return src, 'already', None
    n = src.count(FN)
    if n != 1:
        die('anchor matched %d times (want 1): %s' % (n, FN))
    window = caller_window(src)
    write = deny_writes(window)
    helpers = HELPERS.replace('__RT52OPS_WRITE_DENY__', 'true' if write else 'false')
    if not src.endswith('\n'):
        src += '\n'
    out = src.replace(FN, helpers + FN + '\n' + GUARD, 1)
    mode = 'write-404' if write else 'return-false'
    return out, 'patched', mode


def check_js(text):
    fd, tmp = tempfile.mkstemp(prefix='rt52ops-', suffix='.js')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if r.returncode:
        die('node --check failed: ' + (r.stderr or r.stdout or '')[:500])


def load(path):
    b = open(path, 'rb').read()
    return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b


def main():
    argv = sys.argv[1:]
    dry = '--dry-run' in argv or '--check' in argv
    brief = '--check' in argv and '--dry-run' not in argv
    argv = [a for a in argv if a not in ('--dry-run', '--check')]
    if len(argv) != 1:
        die('usage: python3 patch_rt52ops.py [--dry-run|--check] <server.js>')
    path = argv[0]
    if not os.path.isfile(path):
        die('not a file: ' + path)
    src, crlf = load(path)
    out, status, mode = transform(src)
    if status == 'already':
        print('OK rt52ops already applied; no change (%s)' % path)
        return
    check_js(out)
    print('ANCHOR: %s  (1 match)' % FN)
    print('CALLER: %s  (1 match)' % CALL.strip())
    print('DENY: %s' % ('write the normal HTML 404 and return true (caller falls through to an SPA shell)' if mode == 'write-404' else 'return false (caller falls through to the normal 404)'))
    if dry:
        diff = ''.join(difflib.unified_diff(
            src.splitlines(True), out.splitlines(True),
            fromfile=path, tofile=path + ' (rt52ops, not written)',
        ))
        print('DRY-RUN: original not written; node --check passed; deny mode %s' % mode)
        if brief:
            print('DRY-RUN diff: %d lines (pass --dry-run to print it)' % diff.count('\n'))
        else:
            sys.stdout.write(diff if diff.endswith('\n') or not diff else diff + '\n')
        return
    data = out.replace('\n', '\r\n') if crlf else out
    open(path, 'wb').write(data.encode('utf-8'))
    print('OK rt52ops written %s; node --check passed; deny mode %s' % (path, mode))


if __name__ == '__main__':
    main()
