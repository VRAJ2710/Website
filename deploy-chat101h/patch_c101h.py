#!/usr/bin/env python3
# chat101h on top of live chat101g: three sourced Research articles.
# Appends a server block and an app block. index.html cache tag chat101g -> chat101h.
# Does not edit line 1, Stripe, the database, c93.css, or the service worker.
# Usage: patch_c101h.py SERVER APP INDEX SERVER_BLOCK APP_BLOCK
import sys
S, A, I, SB, AB = sys.argv[1:6]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, sblk, ablk = rd(S), rd(A), rd(I), rd(SB), rd(AB)
def die(m):
    sys.exit("patch_c101h: " + m)
LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != LINE1:
    die("line 1 changed")
if "chat101h:" in srv or "chat101h:" in app or "/app.js?v=chat101h\"" in idx:
    die("already applied")
if "chat101f: market quotes first" not in srv:
    die("chat101f server marker missing")
if "c97Transform" not in srv or "renderPublicSitemap" not in srv or "c93Html" not in srv:
    die("research hooks missing")
if "chat101g: phone Account drawer" not in app:
    die("chat101g app marker missing")
if idx.count('/app.js?v=chat101g"') != 1:
    die("index cache tag count")
if "// ── chat101h:" not in sblk or "// ── chat101h:" not in ablk:
    die("block marker")
_london = "Vraj Patel," + " London"
for bad in ("GC=F", "CL=F", "^TNX", "buy now", "sell now", "stripe.", _london):
    if bad in sblk or bad in ablk:
        die("block contains a forbidden token")
_ddl = ("create" + " table", "alter" + " table", "drop" + " table", "truncate" + " ")
if any(x in (sblk + ablk).lower() for x in _ddl):
    die("block mentions DDL")
srv = srv.rstrip("\n") + "\n" + sblk.strip("\n") + "\n"
app = app.rstrip("\n") + "\n" + ablk.strip("\n") + "\n"
idx = idx.replace('/app.js?v=chat101g"', '/app.js?v=chat101h"', 1)
if srv.split("\n", 1)[0] != LINE1:
    die("line 1 lost")
open(S, "w", encoding="utf-8").write(srv)
open(A, "w", encoding="utf-8").write(app)
open(I, "w", encoding="utf-8").write(idx)
print("patch_c101h: ok")
