#!/usr/bin/env python3
# usage: compare_routes.py OLD_BASE NEW_BASE ROUTES_FILE PROXY_SRC  -> PASS/FAIL lines; exit 1 on any FAIL
import sys, urllib.request, urllib.error, re, http.client
OLD, NEW, RF, PX = [a.rstrip("/") for a in sys.argv[1:5]]
src = open(PX).read(); inj = src[src.index("function inject("):src.index("function cookieFix")]
import subprocess, json
INJ = "const f=(()=>{" + inj + ";return inject})();const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(f(d.h,d.p))"
def inject(h, p): return subprocess.run(["node", "-e", INJ], input=json.dumps({"h": h, "p": p}), capture_output=True, text=True, check=True).stdout
def fetch(base, path, hdrs=None):
    u = base.replace("http://", ""); host, port = u.split(":"); c = http.client.HTTPConnection(host, int(port), timeout=60)
    c.request("GET", path, headers=hdrs or {}); r = c.getresponse(); b = r.read(); h = {k.lower(): v for k, v in r.getheaders()}; c.close(); return r.status, h, b
PAGES = {"/brief/": "brief", "/gold/": "gold", "/markets/": "markets", "/research/": "research"}
bad = 0
def say(ok, m):
    global bad; print(("PASS " if ok else "FAIL ") + m); bad += (not ok)
routes = [l.strip() for l in open(RF) if l.strip().startswith("/")]
same = inj_n = 0
for r in routes:
    so, ho, bo = fetch(OLD, r); sn, hn, bn = fetch(NEW, r)
    if r in PAGES and so == 200:
        exp = inject(bo.decode("utf-8"), PAGES[r]).encode("utf-8")
        ok = sn == 200 and bn == exp and int(hn.get("content-length", -1)) == len(bn) and bn.rstrip().endswith(b"</html>") and bo != bn
        # every header the old page had is unchanged except content-length
        ok = ok and all(hn.get(k) == v for k, v in ho.items() if k not in ("content-length", "date", "etag"))
        say(ok, "injected page %s: body == preview inject(old body), Content-Length %s == %d, ends </html>, other headers same" % (r, hn.get("content-length"), len(bn))); inj_n += ok
    else:
        ok = (so, bo) == (sn, bn) and all(ho.get(k) == hn.get(k) for k in ("content-type", "cache-control", "location", "content-length", "content-encoding"))
        if not ok: say(False, "route %s differs: old %s %d B, new %s %d B" % (r, so, len(bo), sn, len(bn)))
        same += ok
say(True, "%d other routes byte-identical (status, body, content-type, cache-control, location, content-length)" % same) if same == len(routes) - inj_n else None
say(inj_n == 4, "exactly the 4 target pages are injected (%d)" % inj_n)
# trailing-slash variants and query
for r, ex in (("/brief", 301), ("/gold", None), ("/markets", 301), ("/research", None), ("/brief/?utm=x", 200), ("/gold/dashboard/", 200), ("/research/sec/", 200), ("/markets/yields/", 200)):
    so, ho, bo = fetch(OLD, r); sn, hn, bn = fetch(NEW, r); isp = r.split("?")[0] in PAGES and so == 200
    say(so == sn and (b"chat114viz" in bn) == isp and (isp or bo == bn), "variant %s: status old %s new %s, injected=%s (expected %s)" % (r, so, sn, b"chat114viz" in bn, isp))
for r in ("/__chat114viz/viz.css?v=chat114viz", "/__chat114viz/viz.js?v=chat114viz"):
    so, ho, bo = fetch(OLD, r); sn, hn, bn = fetch(NEW, r)
    import os
    if os.environ.get("ASSETS_SAME") == "1": say(sn == 200 and so == 200 and bo == bn and int(hn["content-length"]) == len(bn), "asset %s: new 200 (%d B), byte-identical to step 9" % (r, len(bn)))
    else: say(sn == 200 and so != 200 and int(hn["content-length"]) == len(bn), "asset %s: new 200 (%d B), step 8 %s" % (r, len(bn), so))
sys.exit(1 if bad else 0)
