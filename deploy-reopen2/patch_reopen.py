#!/usr/bin/env python3
# reopen2 (on the live final build): maintenance OFF on line 1 + live QA fixes F1-F5, admin AI status without xAI,
# quoted thousands in Portfolio X-ray CSV. No DDL. usage: patch_reopen.py server.js app.js index.html
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
def rd(p): return open(p if os.path.isabs(p) else os.path.join(HERE, p), encoding="utf-8").read()
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_reopen: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
S, A, I = [os.path.abspath(x) for x in sys.argv[1:4]]
srv, app, idx = rd(S), rd(A), rd(I)
if "reopen2" in srv or "reopen2" in app or "v=chat99r2" in idx: sys.exit("patch_reopen: already applied")
if "// ── chat99 ──" not in srv or "v=chat99" not in idx: sys.exit("patch_reopen: needs the live final files")
blk, ablk = rd("server_block_r2.js"), rd("app_block_r2.js")
for bad in ("create table", "alter table", "drop table", "truncate", "create index", "drop index"):
    if bad in blk.lower() or bad in ablk.lower(): sys.exit("patch_reopen: block contains DDL: " + bad)
L1_OLD = "const BB10I_MAINTENANCE_ON = true; // set false to turn maintenance off (restart to apply)"
L1_NEW = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
first, rest = srv.split("\n", 1)
if first != L1_OLD: sys.exit("patch_reopen: line 1 is not the expected maintenance line")
srv = L1_NEW + "\n" + rest
# F3: signed-in home, Market context first (wide column), brief card beside it
old = '`<section id="c93top"><div class="grid" data-auto>` + c96BriefCard("Today\'s brief") + `<div data-need hidden><h2>Market context</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds, delayed.</p>${c93CtxTable("gold,gold_gbp_oz,dxy,tnx,ry,wti,btc")}</div></div></section'
new = '`<section id="c93top"><div class="grid" data-auto><div data-need hidden><h2>Market context</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds, delayed.</p>${c93CtxTable("gold,gold_gbp_oz,dxy,tnx,ry,wti,btc")}</div>` + c96BriefCard("Today\'s brief") + `</div></section'
srv = edit(srv, old, new, tag="srv-home-order")
srv = srv + "\n// ── reopen2 ──\n" + blk
# F5: calm labels on the desk, never "0 priced"
app = edit(app, "Syncing…", "Updating…", 14, tag="app-sync")
app = edit(app, "Syncing\\u2026", "Updating\\u2026", 2, tag="app-sync-u")
app = edit(app, '${book.length?` · ${liveN} priced`:""}', '${book.length?(liveN?` · ${liveN} priced`:" · Updating…"):""}', tag="app-priced")
app = edit(app, '].filter(Boolean).join(" · ") || "awaiting feed";', '].filter(Boolean).join(" · ") || "Updating…";', 2, tag="app-tape")
app = edit(app, ': "awaiting feed"}</span>', ': "Updating…"}</span>', tag="app-spine")
app = edit(app, 'const feedNote=incomplete?"awaiting feed":', 'const feedNote=incomplete?"Updating…":', tag="app-fg")
app = edit(app, '_rt17Sec("c96keys", "Your AI keys", ', '_rt17Sec("c96keys", (typeof r2NoByok === "function" && r2NoByok()) ? "Your own AI key" : "Your AI keys", ', tag="app-keys-title")
app = edit(app, 'score>=60?"#86efac":', 'score>=60?(document.documentElement.classList.contains("c97-dark")?"#86efac":"#166534"):', tag="app-fg-green")
app = "// reopen2\n" + app + ablk
idx = edit(idx, '<script defer src="/app.js?v=chat99"></script>', '<script defer src="/app.js?v=chat99r2"></script>', tag="idx-token")
for nm, s in ((S, srv), (A, app), (I, idx)):
    open(nm, "w", encoding="utf-8").write(s)
print("patch_reopen: ok")
