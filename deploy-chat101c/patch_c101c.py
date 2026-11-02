#!/usr/bin/env python3
# chat101c: calmer menu (one-column accordion below 1280px, quieter desktop grid). Applies on top of chat101b.
# Appends the server and app blocks and moves the cache tag to chat101c. Nav only: no routes, data or DDL. Refuses a second run.
import sys, re
S, A, I, SB, AB = sys.argv[1:6]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, sblk, ablk = rd(S), rd(A), rd(I), rd(SB), rd(AB)
if "/app.js?v=chat101c\"" in idx or "// \u2500\u2500 chat101c \u2500\u2500" in srv or "chat101c: calmer menu" in app: sys.exit("patch_c101c: already applied")
if "/app.js?v=chat101b\"" not in idx or "// \u2500\u2500 chat101b \u2500\u2500" not in srv or "chat101b: all sections" not in app: sys.exit("patch_c101c: chat101b is not applied")
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101c: server.js line 1 is not the maintenance=false line")
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit("patch_c101c: %s expected %d match(es), found %d" % (tag, n, c))
    return s.replace(old, new)
srv = edit(srv, "html = html.replace('<a class=\"cta\" href=\"/__auth/login\">Sign in</a>', '<a class=\"cta\" href=\"/dashboard/\">Your desk</a>')", "html = html.split('<a class=\"cta\" href=\"/__auth/login\">Sign in</a>').join('<a class=\"cta\" href=\"/dashboard/\">Your desk</a>')", tag="signed-header-all")  # every account button, not only the first
idx = edit(idx, '<script defer src="/app.js?v=chat101b"></script>', '<script defer src="/app.js?v=chat101c"></script>', tag="idx-token")
if not sblk.lstrip().startswith("// \u2500\u2500 chat101c \u2500\u2500"): sys.exit("patch_c101c: server block header missing")
if not ablk.lstrip().startswith("// \u2500\u2500 chat101c: calmer menu"): sys.exit("patch_c101c: app block header missing")
for blk in (sblk, ablk):
    if re.search(r"(create|alter|drop)\s+(table|index)|trunc" + r"ate\s", blk, re.I): sys.exit("patch_c101c: DDL in a block")
    if "GC=F" in blk or "Fix with Agent" in blk or re.search(r"Vraj Patel,\s*London", blk, re.I): sys.exit("patch_c101c: forbidden wording in a block")
srv = srv.rstrip("\n") + "\n" + sblk.lstrip("\n")
app = app.rstrip("\n") + "\n" + ablk.lstrip("\n")
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101c: line 1 changed")
if "Edited by Vraj Patel" not in srv or "Not investment advice. Capital at risk." not in srv: sys.exit("patch_c101c: byline or disclaimer missing")
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101c: ok")
