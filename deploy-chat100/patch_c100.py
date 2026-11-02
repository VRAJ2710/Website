#!/usr/bin/env python3
# chat100 (on the live reopen2 build): dashboard gold/macro defaults, calm Fear & Greed, self-building screener,
# source inspector. Line 1 stays maintenance OFF. No DDL. usage: patch_c100.py server.js app.js index.html
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
def rd(p): return open(p if os.path.isabs(p) else os.path.join(HERE, p), encoding="utf-8").read()
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_c100: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
S, A, I = [os.path.abspath(x) for x in sys.argv[1:4]]
srv, app, idx = rd(S), rd(A), rd(I)
if "// ── chat100 ──" in srv or "// ── chat100 ──" in app or "v=chat100" in idx: sys.exit("patch_c100: already applied")
if "// ── reopen2 ──" not in srv or "v=chat99r2" not in idx: sys.exit("patch_c100: needs the live reopen2 files")
blk, ablk = rd("server_block_c100.js"), rd("app_block_c100.js")
for bad in ("create table", "alter table", "drop table", "truncate", "create index", "drop index"):
    if bad in blk.lower() or bad in ablk.lower(): sys.exit("patch_c100: block contains DDL: " + bad)
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c100: line 1 is not the maintenance-OFF line")
# 3 screener: calm message until the first automatic build lands
srv = edit(srv, 'The screener has not been built yet.${admin ? "" : " Check back soon."}', '${bb11Ua() ? "Building the screener, check back shortly." : "The screener is not switched on yet. Check back soon."}', tag="srv-scr-msg")
srv = srv + "\n" + blk
# 1 dashboard defaults: gold and macro, plain names, no "V1" label
OLDD = "['SPY', 'NVDA', 'BTC', 'XAU', 'AAPL']"
NEWD = "['XAU', 'SLV', 'GBPUSD', 'DXY', 'TNX', 'BRENT', 'SPX']"
app = edit(app, "if (!watchlists[0]?.tickers?.length && !localStorage.getItem('td_wls')) {\n  watchlists[0].tickers = " + OLDD + ";\n  saveWatchlists();\n}",
  "if (!watchlists[0]?.tickers?.length && !localStorage.getItem('td_wls')) {\n  watchlists[0].tickers = " + NEWD + ";\n  saveWatchlists();\n} else if (watchlists[0] && Array.isArray(watchlists[0].tickers) && watchlists[0].tickers.slice().sort().join(',') === 'AAPL,BTC,NVDA,SPY,XAU') {\n  watchlists[0].tickers = " + NEWD + "; // chat100: the old stock defaults become gold and macro\n  saveWatchlists();\n}", tag="app-def")
app = edit(app, 'tickers: ["SPY", "NVDA", "BTC", "XAU", "AAPL"] }];', 'tickers: ["XAU", "SLV", "GBPUSD", "DXY", "TNX", "BRENT", "SPX"] }];', tag="app-reset")
app = edit(app, 'const _ONBOARD_PICKS = ["NVDA", "SPY", "AAPL", "BTC", "XAU"];', 'const _ONBOARD_PICKS = ["XAU", "SLV", "GBPUSD", "DXY", "TNX"];', tag="app-onb")
app = edit(app, '    <div class="gd-promise-k">V1 · GOLD FIRST</div>\n', '', tag="app-v1")
app = edit(app, "    </div>`;\n  if(!book.length){\n", "    </div>`;\n  h+=_c100MacroHtml();\n  if(!book.length){\n", tag="app-macro")
app = edit(app, '  h+=`<div class="book-price-row" role="list" aria-label="Book prices">`;\n  book.slice(0,10).forEach(tk=>{',
  '  const _c100Def=_c100IsDef(book);\n  h+=_c100Def?"":`<div class="book-section-lbl" style="margin-top:6px">Your book</div><div class="book-price-row" role="list" aria-label="Book prices">`;\n  (_c100Def?[]:book.slice(0,10)).forEach(tk=>{', tag="app-chips")
app = edit(app, "onclick=\"openA('${tk}')\" title=\"${tk}\">\n      <span class=\"book-px-tk\">${tk}</span>", "onclick=\"openA('${tk}')\" title=\"${_escAttr(_c100Nm(tk))}\">\n      <span class=\"book-px-tk\">${_escHtml(_c100Nm(tk))}</span>", tag="app-chipname")
app = edit(app, "  h+=`</div>`;\n  const activeAlerts=", "  h+=_c100Def?\"\":`</div>`;\n  const activeAlerts=", tag="app-chipclose")
app = "// chat100\n" + app + ablk
idx = edit(idx, '<script defer src="/app.js?v=chat99r2"></script>', '<script defer src="/app.js?v=chat100"></script>', tag="idx-token")
for nm, s in ((S, srv), (A, app), (I, idx)):
    open(nm, "w", encoding="utf-8").write(s)
print("patch_c100: ok")
