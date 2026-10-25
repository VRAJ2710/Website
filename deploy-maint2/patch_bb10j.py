"""bb10j: on top of bb10j (live on Replit). While maintenance is on, GET/HEAD "/" answers 200 with the maintenance page (noindex) so the Replit Autoscale Promote health check passes.
While maintenance is on (BB10I_MAINTENANCE_ON), GET/HEAD "/" (exact pathname, any query string, any Host) answers 200 with the branded maintenance page
(X-Robots-Tag: noindex, <meta name="robots" content="noindex">, Cache-Control: no-store, no Retry-After; HEAD = headers only) so the Autoscale Promote health probe passes.
Every other non-exempt path, all /api/*, and non-GET/HEAD methods on "/" stay 503 + Retry-After 3600 + no-store (also X-Robots-Tag: noindex). Exemptions and the admin cookie bypass are bb10i's, unchanged.
Server-only. No new secrets, env vars, timers, fetches, tables or packages. All new names are bb10j-prefixed.
Usage: python3 patch_bb10j.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs. CRLF files stay CRLF."""
import sys, os, hashlib, subprocess
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
BASE_MD5 = "d01094a38f0fbf00800ccd1bbc5f733c"
MARK = "// ── bb10j:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''// ── bb10j: GET/HEAD "/" answers 200 (maintenance page, noindex) so the Replit Autoscale Promote health check passes ─────────
// Only the maintenance responder changes (bb10i's handler, exemptions and admin check are untouched). With the flag false nothing here is reachable.
//  - "/" (raw request path exactly "/" - or the absolute-form http://host/ - any query string, any Host; "//x", "/." and "/./" stay 503) on GET/HEAD: 200, same branded page, X-Robots-Tag noindex, Cache-Control no-store, no Retry-After.
//    A HEAD gets the headers without a body. Cookie-less guests: no DB, no session lookup. A cookie holder is still checked by bb10i first (admin -> real site); a non-admin gets this 200 page.
//  - every other maintenance response stays 503 + Retry-After 3600 + no-store (API JSON body unchanged) and now also carries X-Robots-Tag: noindex.
//  - the HTML (200 and 503) gets <meta name="robots" content="noindex">.
var BB10J_HTML_BODY = BB10I_HTML_BODY.replace('<meta name="color-scheme" content="dark">', '<meta name="color-scheme" content="dark"><meta name="robots" content="noindex">');
BB10I_HTML_BODY = BB10J_HTML_BODY;
var BB10J_HTML_LEN = Buffer.byteLength(BB10J_HTML_BODY);
var bb10jSend0 = bb10iSend;
bb10iSend = function bb10jSend(req, res, p) {
  var bb10jRaw = String(req.url || "").split(/[?#]/)[0];
  if (p === "/" && (req.method === "GET" || req.method === "HEAD") && (bb10jRaw === "/" || /^https?:\/\/[^\/]*\/?$/i.test(bb10jRaw))) {
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex",
      "Content-Length": BB10J_HTML_LEN,
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    });
    res.end(req.method === "HEAD" ? undefined : BB10J_HTML_BODY);
    return;
  }
  res.setHeader("X-Robots-Tag", "noindex");
  return bb10jSend0(req, res, p);
};
'''

ANCHOR = "// BB10I_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10J_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10j.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10j: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10i live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s or "BB10J_JS_END" in s: print("REFUSE: bb10j already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    if "BB10I_MAINTENANCE_ON" not in s or "bb10iSend" not in s: print("REFUSE: bb10i is not applied (BB10I_MAINTENANCE_ON / bb10iSend missing)"); return 0
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10j.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10j: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
