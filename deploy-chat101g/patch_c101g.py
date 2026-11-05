#!/usr/bin/env python3
# chat101g on top of chat101f: the phone Account button opens a full-height, readable drawer (close X, backdrop, Esc,
# focus trap, scroll lock) instead of a 220px box placed off the left edge; signed-in free accounts get Settings / Sign out
# instead of "Sign in"; fixes from the tap-through audit. Touches app.js (appended block) and index.html (app.js?v=chat101g).
# Usage: patch_c101g.py SERVER APP INDEX APP_BLOCK
import sys
S, A, I, AB = sys.argv[1:5]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, blk = rd(S), rd(A), rd(I), rd(AB)
def die(m): sys.exit("patch_c101g: " + m)
if '/app.js?v=chat101g"' in idx or "chat101g: phone Account drawer" in app: die("already applied")
if '/app.js?v=chat101f"' not in idx or "chat101e: market cards" not in app or "chat101f: market quotes first" not in srv: die("chat101f is not applied")
LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != LINE1: die("line 1 changed")
if "// ── chat101g: phone Account drawer" not in blk: die("block marker")
for bad in ("GC=F", "CL=F", "^TNX", "buy now", "sell now", "stripe."):
    if bad in blk: die("block contains " + bad)
if idx.count('/app.js?v=chat101f"') != 1: die("index tag count")
app = app.rstrip("\n") + "\n" + blk.strip("\n") + "\n"
idx = idx.replace('/app.js?v=chat101f"', '/app.js?v=chat101g"')
open(A, "w", encoding="utf-8").write(app); open(I, "w", encoding="utf-8").write(idx)
print("patch_c101g: ok")
