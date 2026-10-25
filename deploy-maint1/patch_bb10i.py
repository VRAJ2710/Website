"""bb10i: site-wide maintenance page served by our own server (replaces a temporary Cloudflare block), on top of bb10g live. bb10h is NOT included.
(a) One flag, the first line of server.js: `const BB10I_MAINTENANCE_ON = true; // set false to turn maintenance off` (flip it, restart).
(b) While on, the outermost handler answers every request with 503 (Retry-After 3600, Cache-Control no-store, no ETag, never a 304): a self-contained
    dark/gold HTML page ("THE DISPATCH" / Under maintenance / one sentence / muted "Owner sign in" -> /__auth/login), or {"error":"maintenance"} for /api/*.
    HEAD gets the same headers without a body. Every other method is also 503.
(c) Pass through unchanged: /api/stripe/webhook (any method; body untouched), /health, /healthz, /api/health (GET/HEAD), /__auth/login, /__auth/logout,
    /__auth/recover, /__auth/reset (GET/POST), and any request whose dispatch_session cookie resolves (server-side, via currentUser) to an admin (isAdminUser).
    Guests with no cookie are answered with no session lookup. Non-admin users see the maintenance page. A failed lookup fails closed (503).
Server-only. No new secrets, env vars, timers, fetches, tables or packages. All new names are bb10i/BB10I-prefixed.
Usage: python3 patch_bb10i.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs. CRLF files stay CRLF."""
import sys, os, hashlib, subprocess
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
BASE_MD5 = "9777ab9b8bebaa77f475b738995aa3d8"
MARK = "// ── bb10i:"
FLAG = 'const BB10I_MAINTENANCE_ON = true; // set false to turn maintenance off (restart to apply)\n'
HEAD = 'const http = require("http");\n'
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''// ── bb10i: site-wide maintenance page (flag: BB10I_MAINTENANCE_ON, first line of the file) ─────────
// Outermost request handler (it wraps every earlier `handle`, so it runs before the canonical redirect, static files and every route).
// Flag false: one boolean test, then the previous handler untouched. Flag true: a path test first; the session and admin lookup only run for
// non-exempt paths and only when a dispatch_session cookie is present (guests without a cookie get the 503 with no lookup at all).
var BB10I_RETRY_AFTER = "3600";
var BB10I_JSON_BODY = '{"error":"maintenance"}';
var BB10I_HTML_BODY = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark">' +
  '<title>The Dispatch \u2014 Under maintenance</title>' +
  '<style>html,body{height:100%;margin:0}body{background:#0b0d10;color:#e8e6df;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;box-sizing:border-box;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}' +
  'main{max-width:30rem}.k{color:#d4a93a;letter-spacing:.32em;font-size:.8rem;font-weight:600;text-transform:uppercase;margin:0 0 1.4rem}' +
  'h1{font:400 2.4rem/1.2 Georgia,"Times New Roman",Times,serif;margin:0 0 1rem;color:#f3f0e8}p{margin:0;color:#b9b6ad}' +
  '.o{margin-top:3rem;font-size:.75rem}.o a{color:#6f6d66;text-decoration:none;border-bottom:1px solid #2a2c30}.o a:hover{color:#d4a93a;border-color:#d4a93a}</style></head>' +
  '<body><main><p class="k">The Dispatch</p><h1>Under maintenance</h1><p>We are making improvements and will be back shortly.</p>' +
  '<p class="o"><a href="/__auth/login" rel="nofollow">Owner sign in</a></p></main></body></html>';
var BB10I_AUTH_PATHS = new Set(["/__auth/login", "/__auth/logout", "/__auth/recover", "/__auth/reset"]);
function bb10iPath(req) {
  try { return new URL(req.url || "/", "http://localhost").pathname; } catch (e) { return null; }
}
function bb10iExempt(req, p) {
  var m = req.method;
  if (p === "/api/stripe/webhook") return true;                                    // raw-body handler, order and bytes untouched
  if (m === "GET" || m === "HEAD") {
    var h = p.length > 1 && p.charAt(p.length - 1) === "/" ? p.slice(0, -1) : p;  // same normalisation as bb5bEarly
    if (h === "/health" || h === "/healthz" || h === "/api/health") return true;
  }
  if ((m === "GET" || m === "POST") && BB10I_AUTH_PATHS.has(p)) return true;       // the owner sign-in flow (page is self-contained: no assets)
  return false;
}
function bb10iSend(req, res, p) {
  var api = p !== null && (p === "/api" || p.indexOf("/api/") === 0);
  var body = api ? BB10I_JSON_BODY : BB10I_HTML_BODY;
  var hd = {
    "Content-Type": api ? "application/json; charset=utf-8" : "text/html; charset=utf-8",
    "Cache-Control": "no-store",
    "Retry-After": BB10I_RETRY_AFTER,
    "Content-Length": Buffer.byteLength(body),
    "X-Content-Type-Options": "nosniff"
  };
  if (!api) hd["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
  res.writeHead(503, hd);
  res.end(req.method === "HEAD" ? undefined : body);
}
var bb10iHandle0 = handle;
handle = async function (req, res) {
  if (!BB10I_MAINTENANCE_ON) return bb10iHandle0.apply(this, arguments);
  var p = bb10iPath(req);
  if (p !== null && bb10iExempt(req, p)) return bb10iHandle0.apply(this, arguments);
  try {
    var ck = req.headers && req.headers.cookie;
    if (ck && dispatchSessionTokens(ck).length) {
      var u = await currentUser(req);
      if (isAdminUser(u)) return bb10iHandle0.apply(this, arguments);   // server-side session -> existing admin check; never a client flag
    }
  } catch (e) { /* fail closed: the maintenance page */ }
  return bb10iSend(req, res, p);
};
'''

ANCHOR = "// BB10G_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10I_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10i.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10i: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10g live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s or "BB10I_MAINTENANCE_ON" in s: print("REFUSE: bb10i already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    if not s.startswith(HEAD): print("REFUSE: server.js does not start with the expected first line"); return 0
    s = FLAG + s
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10i.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10i: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
