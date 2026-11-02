#!/usr/bin/env python3
# chat101: claim checker, ISA/SIPP gold planner, Fed/BoE statement tracker, gold scenario simulator, filing change detector,
# PWA (manifest, icons, service worker, offline page, install prompt), source inspector on the signed-in /gold/ and /brief/,
# and ", London" removed after Vraj's name everywhere. Applies on top of chat100e (server 96020a62, app 25e22204, index 3ac8a07c).
# Exact-count edits, then the server and app blocks are appended. No DDL. Refuses a second run.
import sys
S, A, I, SB, AB = sys.argv[1:6]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, sblk, ablk = rd(S), rd(A), rd(I), rd(SB), rd(AB)
if "/app.js?v=chat101\"" in idx or "// \u2500\u2500 chat101 \u2500\u2500" in srv or "chat101: \"Check and plan\"" in app: sys.exit("patch_c101: already applied")
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit("patch_c101: %s expected %d match(es), found %d" % (tag, n, c))
    return s.replace(old, new)
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101: server.js line 1 is not the maintenance=false line")
# ", London" after Vraj's name (market and time-zone uses of London are untouched)
srv = edit(srv, "<p>Published by Vraj Patel, London \\u00b7 \\u00a9 ${new Date().getUTCFullYear()}", "<p>Published by Vraj Patel \\u00b7 \\u00a9 ${new Date().getUTCFullYear()}", tag="srv-footer")
idx = edit(idx, "THE DISPATCH MARKET \u00b7 EDITED BY VRAJ PATEL, LONDON</p>", "THE DISPATCH MARKET \u00b7 EDITED BY VRAJ PATEL</p>", tag="idx-eyebrow")
# no raw ticker codes on the gold desk
app = edit(app, "COMEX gold futures (GC=F) daily bars, Yahoo Finance, delayed", "COMEX gold futures (front month) daily bars, Yahoo Finance, delayed", tag="app-asof")
app = edit(app, "COMEX gold futures (GC=F) \u00b7 Yahoo Finance daily bars, delayed", "COMEX gold futures (front month) \u00b7 Yahoo Finance daily bars, delayed", tag="app-futnote")
app = edit(app, 'return "COMEX gold futures (GC=F), delayed";', 'return "COMEX gold futures (front month), delayed";', tag="app-src")
app = edit(app, 'return "Gold \u00b7 COMEX futures (GC=F) \u00b7 delayed";', 'return "Gold \u00b7 COMEX futures (front month) \u00b7 delayed";', tag="app-kicker")
app = edit(app, '_rtGoldKicker() : "Gold \u00b7 COMEX futures (GC=F) \u00b7 delayed")', '_rtGoldKicker() : "Gold \u00b7 COMEX futures (front month) \u00b7 delayed")', tag="app-kicker2")
app = edit(app, 'var fut = closed ? "Futures (GC=F)" : "Futures (GC=F, delayed 10 min)";', 'var fut = closed ? "Futures (front month)" : "Futures (front month, delayed 10 min)";', tag="app-fut")
app = edit(app, '"\\u00a0\u00b7 Gold futures (GC=F)";', '"\\u00a0\u00b7 Gold futures (front month)";', tag="app-futs")
# cache token
idx = edit(idx, '<script defer src="/app.js?v=chat100e"></script>', '<script defer src="/app.js?v=chat101"></script>', tag="idx-token")
# blocks
if not sblk.lstrip().startswith("// \u2500\u2500 chat101 \u2500\u2500"): sys.exit("patch_c101: server block header missing")
srv = srv.rstrip("\n") + "\n" + sblk.lstrip("\n")
app = app.rstrip("\n") + "\n" + ablk.lstrip("\n")
# guards
import re
for nm, t in ((S, srv), (A, app), (I, idx)):
    if re.search(r"Vraj Patel,\s*London", t, re.I): sys.exit("patch_c101: 'Vraj Patel, London' left in " + nm)
    for bad in ("Edited by Vraj Patel, London", "Fix with Agent"):
        if bad in t: sys.exit("patch_c101: forbidden wording %r in %s" % (bad, nm))
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101: line 1 changed")
if "Edited by Vraj Patel" not in srv: sys.exit("patch_c101: byline missing")
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101: ok")
