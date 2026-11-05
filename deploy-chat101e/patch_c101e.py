#!/usr/bin/env python3
# chat101e on top of LIVE chat101d: market cards on the signed-in Gold Dashboard (app.js block; the public pages' chat96
# market renderer is copied from server.js, reading one detached table instead of the page), cache tag app.js?v=chat101e.
# server.js is read, never written. app.js has no support/contact address to change. Refuses a second run.
import sys, json
S, A, I, B = sys.argv[1:5]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, blk = rd(S), rd(A), rd(I), rd(B)
if '/app.js?v=chat101e"' in idx or "chat101e: market cards" in app: sys.exit("patch_c101e: already applied")
if '/app.js?v=chat101d"' not in idx or "chat101d: app views" not in app or "const C101D_CSS" not in srv: sys.exit("patch_c101e: chat101d is not applied")
L = [l for l in srv.split("\n") if l.startswith("const C96_LIVE_JS = ")]
if len(L) != 1: sys.exit("patch_c101e: renderer not found")
js, _ = json.JSONDecoder().raw_decode(L[0][len("const C96_LIVE_JS = "):])
OLDQ = 'document.querySelectorAll("tbody[data-rows]")'
if js.count(OLDQ) != 1: sys.exit("patch_c101e: renderer shape changed")
js = js.replace(OLDQ, 'ROOT.querySelectorAll("tbody[data-rows]")')
if blk.count("__RENDERER__") != 1 or blk.count("__C101E_RENDER__") != 2: sys.exit("patch_c101e: block shape")
blk = blk.replace("__RENDERER__", js)
for bad in ("GC=F", "cache.put", "buy now", "sell now"):
    if bad in blk: sys.exit("patch_c101e: block contains " + bad)
app = app.rstrip("\n") + "\n" + blk.lstrip("\n")
if idx.count('<script defer src="/app.js?v=chat101d"></script>') != 1: sys.exit("patch_c101e: idx-token")
idx = idx.replace('<script defer src="/app.js?v=chat101d"></script>', '<script defer src="/app.js?v=chat101e"></script>')
for p, t in ((A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101e: ok")
