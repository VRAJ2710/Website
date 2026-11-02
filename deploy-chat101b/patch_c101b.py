#!/usr/bin/env python3
# chat101b: every core section back in the header and the "All sections" menu (server pages and the app),
# plus /what-changed/ and sign-in pages for Documents and Portfolio. Applies on top of chat101 (run patch_c101.py first).
# Exact-count edits, then the server and app blocks are appended. No DDL. Refuses a second run.
import sys, re
S, A, I, SB, AB = sys.argv[1:6]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, sblk, ablk = rd(S), rd(A), rd(I), rd(SB), rd(AB)
if "/app.js?v=chat101b\"" in idx or "// \u2500\u2500 chat101b \u2500\u2500" in srv or "chat101b: all sections" in app: sys.exit("patch_c101b: already applied")
if "/app.js?v=chat101\"" not in idx or "// \u2500\u2500 chat101 \u2500\u2500" not in srv: sys.exit("patch_c101b: chat101 is not applied; run patch_c101.py first")
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit("patch_c101b: %s expected %d match(es), found %d" % (tag, n, c))
    return s.replace(old, new)
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101b: server.js line 1 is not the maintenance=false line")
# app header: the "Tools" button becomes "All sections"; Pricing joins the top links; the mobile Menu says what it opens
idx = edit(idx, '<a href="/about">About</a><button type="button" class="c93-more" aria-controls="c93Menu" aria-expanded="false">Tools</button></nav>',
               '<a href="/about">About</a><a href="/pricing">Pricing</a><button type="button" class="c93-more" aria-controls="c93Menu" aria-expanded="false" aria-haspopup="true">All sections</button></nav>', tag="idx-allsections")
idx = edit(idx, '<button type="button" class="c93-menu-btn" aria-controls="c93Menu" aria-expanded="false">Menu</button>',
               '<button type="button" class="c93-menu-btn" aria-controls="c93Menu" aria-expanded="false" aria-haspopup="true" aria-label="Menu: all sections">Menu</button>', tag="idx-menu")
idx = edit(idx, '<script defer src="/app.js?v=chat101"></script>', '<script defer src="/app.js?v=chat101b"></script>', tag="idx-token")
# boot fix: the dashboard can render during start-up, before C100_NM / C100_DEF are assigned further down app.js,
# which threw "reading 'XAU'" and stopped start-up for signed-in readers. Guard both reads.
app = edit(app, '  tk = String(tk || ""); if (C100_NM[tk]) return C100_NM[tk];',
               '  tk = String(tk || ""); if (C100_NM && C100_NM[tk]) return C100_NM[tk];', tag="app-c100nm")
app = edit(app, 'return b === C100_DEF.slice().sort().join(",");', 'return b === (C100_DEF || ["XAU", "SLV", "GBPUSD", "DXY", "TNX", "BRENT", "SPX"]).slice().sort().join(",");', tag="app-c100def")
if not sblk.lstrip().startswith("// \u2500\u2500 chat101b \u2500\u2500"): sys.exit("patch_c101b: server block header missing")
if not ablk.lstrip().startswith("// \u2500\u2500 chat101b: all sections"): sys.exit("patch_c101b: app block header missing")
srv = srv.rstrip("\n") + "\n" + sblk.lstrip("\n")
app = app.rstrip("\n") + "\n" + ablk.lstrip("\n")
for nm, t in ((S, srv), (A, app), (I, idx)):
    if re.search(r"Vraj Patel,\s*London", t, re.I): sys.exit("patch_c101b: 'Vraj Patel, London' left in " + nm)
    if "Fix with Agent" in t: sys.exit("patch_c101b: forbidden wording in " + nm)
for bad in ("(GC=F)", "GC=F"):
    if bad in sblk or bad in ablk: sys.exit("patch_c101b: raw ticker code in a block")
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101b: line 1 changed")
if "Edited by Vraj Patel" not in srv: sys.exit("patch_c101b: byline missing")
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101b: ok")
