#!/usr/bin/env python3
# usage: compare_guest.py OLD_BASE NEW_BASE ROUTES_FILE -> every route byte-identical for a guest (no cookie), with and without
# Accept-Encoding; the new asset exists only on NEW. Exit 1 on any FAIL.
import sys, http.client
OLD, NEW, RF = [a.rstrip("/") for a in sys.argv[1:4]]
def fetch(base, path, hdrs=None):
    host, port = base.replace("http://", "").split(":"); c = http.client.HTTPConnection(host, int(port), timeout=60)
    c.request("GET", path, headers=hdrs or {}); r = c.getresponse(); b = r.read(); h = {k.lower(): v for k, v in r.getheaders()}; c.close(); return r.status, h, b
bad = 0; n = 0
routes = [l.strip() for l in open(RF) if l.strip().startswith("/")] + ["/brief", "/gold", "/brief/?utm=x", "/__chat114viz/viz.css?v=chat114viz", "/__chat114viz/viz.js?v=chat114viz"]
for r in routes:
    for hd in ({}, {"Accept-Encoding": "gzip, deflate, br"}):
        so, ho, bo = fetch(OLD, r, hd); sn, hn, bn = fetch(NEW, r, hd)
        ok = so == sn and bo == bn and all(ho.get(k) == hn.get(k) for k in ("content-type", "cache-control", "location", "content-length", "content-encoding", "etag"))
        n += 1
        if not ok: bad += 1; print("FAIL route %s %s: old %s %d B, new %s %d B" % (r, hd, so, len(bo), sn, len(bn)))
print(("PASS " if not bad else "FAIL ") + "guest: %d route x encoding fetches byte-identical (status, body, type, cache, location, length, encoding, etag); %d differ" % (n, bad))
so, ho, bo = fetch(OLD, "/__chat115vizapp/vizapp.js?v=chat115vizapp"); sn, hn, bn = fetch(NEW, "/__chat115vizapp/vizapp.js?v=chat115vizapp")
ok = sn == 200 and so != 200 and int(hn["content-length"]) == len(bn); bad += not ok
print(("PASS " if ok else "FAIL ") + "asset /__chat115vizapp/vizapp.js: new 200 (%d B), step 9b %s" % (len(bn), so))
sys.exit(1 if bad else 0)
