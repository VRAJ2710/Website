"""bb12d = bb12c + two diagnostic response headers, as ONE patch on the live server bb12b (md5 5d4cb84f987f2e189d0a298e6f44025c, 24582 lines).
bb12c part: the /api/monitor rate-limit key = the LAST X-Forwarded-For entry (normalised IP); cf-connecting-ip ignored; no usable XFF entry -> socket address; 120/min per key + 2000/min global backstop; limiter before the ETag/304/HEAD branch, for everybody incl. admin; 429 = JSON + Retry-After 60 + no-store.
bb12d part: every /api/monitor and /api/monitor/{T} response (200, 304, 429, HEAD, and the 405/400/404 errors) carries X-Dispatch-Xff-N (number of comma-separated non-empty X-Forwarded-For entries, 0 if absent/empty) and X-Dispatch-RL-Key (last | socket). Never an address, never the XFF value. Cache-Control unchanged (200/304 stay public, max-age=300, swr=600, so an edge cache may replay these two headers).
Server-only: 1 function replaced (+1 added), 3 call sites; no timers/DB/env/packages. Usage: python3 patch_bb12d.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs. CRLF files stay CRLF."""
import sys, os, hashlib, subprocess
BASE_MD5 = "5d4cb84f987f2e189d0a298e6f44025c"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

EDITS = [
    (r'''function bb12bClientKey(req) {                                            // bb12b: rate-limit key for the monitor routes. Never the client-set first X-Forwarded-For entry.
  var h = (req && req.headers) || {}, k = bb12bIp(h["cf-connecting-ip"]);  // 1) cf-connecting-ip, when it looks like an IP
  if (k) return k;
  var xf = String(h["x-forwarded-for"] || "").slice(-2048).split(",").map(function (x) { return x.trim(); }).filter(Boolean);
  if (xf.length) { k = bb12bIp(xf.length >= 2 ? xf[xf.length - 2] : xf[0]); if (k) return k; }   // 2) entry before the last (Google frontend appends client, then its own hop); 3) the only entry
  return bb12bIp(req && req.socket && req.socket.remoteAddress) || "unknown";   // 4) socket address
}
''',
     r'''function bb12cClientKey(req) {                                            // bb12c: rate-limit key for the monitor routes = the LAST X-Forwarded-For entry (the hop the platform proxy appended; client-set entries before it are ignored). cf-connecting-ip is NOT read (the site is DNS-only, not behind Cloudflare). No usable XFF entry -> the socket address.
  var h = (req && req.headers) || {}, k;
  var xf = String(h["x-forwarded-for"] || "").slice(-2048).split(",").map(function (x) { return x.trim(); }).filter(Boolean);
  if (xf.length) { k = bb12bIp(xf[xf.length - 1]); if (k) return k; }
  return bb12bIp(req && req.socket && req.socket.remoteAddress) || "unknown";
}
function bb12dDiag(req) {                                             // bb12d: two diagnostic response headers for the monitor routes. NEVER an address or part of one, never the XFF value: only a count and a word.
  var raw = String(((req && req.headers) || {})["x-forwarded-for"] || "");   // node already joins repeated X-Forwarded-For lines with ", "
  var n = raw.split(",").map(function (x) { return x.trim(); }).filter(Boolean).length;
  var tail = raw.slice(-2048).split(",").map(function (x) { return x.trim(); }).filter(Boolean);   // same window and parsing as bb12cClientKey
  return { "X-Dispatch-Xff-N": String(n), "X-Dispatch-RL-Key": tail.length && bb12bIp(tail[tail.length - 1]) ? "last" : "socket" };
}
'''),
    (r'''bb11Rl.allow(bb12bClientKey(req), bb11Now())''',
     r'''bb11Rl.allow(bb12cClientKey(req), bb11Now())'''),
    (r'''extra && extra.headers); }
async function bb11Route''',
     r'''Object.assign({}, extra && extra.headers, bb12dDiag(req))); }
async function bb11Route'''),
    (r'''"X-Robots-Tag": "noindex" }, SECURITY_HEADERS);
  if (req.headers["if-none-match"]''',
     r'''"X-Robots-Tag": "noindex" }, SECURITY_HEADERS, bb12dDiag(req));
  if (req.headers["if-none-match"]'''),
]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb12d.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb12d: {f} md5 {m0} lines {raw.count(b'\n')}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb12b live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if "bb12dDiag" in s: print("REFUSE: bb12d already applied"); return 0
    if "function bb12bClientKey(req)" not in s or "var bb12bGlobalRl" not in s: print("REFUSE: bb12b is not applied (bb12bClientKey / bb12bGlobalRl missing)"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb12d.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
    os.replace(tmp, f); print(f"bb12d: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
if __name__ == "__main__": sys.exit(main())
