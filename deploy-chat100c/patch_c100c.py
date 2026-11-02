#!/usr/bin/env python3
# chat100c (on the chat100 build; chat100b with spot-on-spot gold change): gold change vs our previous-UK-day spot snapshot everywhere gold spot appears, About founder card with
# photo and LinkedIn link, version tag chat100c. Line 1 stays maintenance OFF. No DDL.
# usage: patch_c100c.py server.js app.js index.html   (run after patch_c100.py)
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
def rd(p): return open(p if os.path.isabs(p) else os.path.join(HERE, p), encoding="utf-8").read()
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_c100c: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
def lit(js): return json.dumps(js)[1:-1]          # browser JS -> text inside the server's "..." string literal
S, A, I = [os.path.abspath(x) for x in sys.argv[1:4]]
srv, app, idx = rd(S), rd(A), rd(I)
if "// ── chat100b ──" in srv or "// ── chat100b ──" in app or "v=chat100c" in idx or "v=chat100b" in idx: sys.exit("patch_c100c: already applied")
if "// ── chat100 ──" not in srv or 'v=chat100"' not in idx: sys.exit("patch_c100c: needs the chat100 files (run patch_c100.py first)")
blk, ablk = rd("server_block_c100b.js"), rd("app_block_c100b.js")
for bad in ("create table", "alter table", "drop table", "truncate", "create index", "drop index"):
    if bad in blk.lower() or bad in ablk.lower(): sys.exit("patch_c100c: block contains DDL: " + bad)
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c100c: line 1 is not the maintenance-OFF line")
# Market context script (C96_LIVE_JS): fetch the gold change and fill the three gold rows; never blank.
srv = edit(srv, lit('want.tnx?get("/api/c97/dgs10"):null]).then(function(a){'),
           lit('want.tnx?get("/api/c97/dgs10"):null,want.gold?get("/api/c100b/gold-change"):null]).then(function(a){'), tag="ctx-fetch")
G_OLD = lit('rows.gold_gbp_g=["Gold spot, \\u00a3 per gram","\\u00a3"+n(oz/31.1034768,2),"",bs,null]}}\n')
G_NEW = G_OLD + lit(
    'var gc=a[7];function c1m(v,c){v=Number(v);return(v>0?"+":v<0?"\\u2212":"")+c+Math.abs(v).toLocaleString("en-GB",{minimumFractionDigits:2,maximumFractionDigits:2})}\n'
    '[["gold","usd","$",1],["gold_gbp_oz","gbp","\\u00a3",1],["gold_gbp_g","gbp","\\u00a3",31.1034768]].forEach(function(z){var r=rows[z[0]];if(!r)return;'
    'var c=gc&&gc.available?gc[z[1]]:null,nv=z[1]==="usd"?Number(gs.price):Number(oz),pv=c?Number(c.prev):0;'
    'if(c&&pv>0&&nv>0){var pc=(nv/pv-1)*100;r[2]=c1m((nv-pv)/z[3],z[2])+" ("+sg(pc,2,"%")+")";r[4]=pc;'
    'r[3]=r[3]+" \\u00b7 Change "+c.basis}else{r[2]="Change not available yet";r[4]=null}});\n')
srv = edit(srv, G_OLD, G_NEW, tag="ctx-gold")
srv = edit(srv, lit("'</td><td class=\"n'+cl+'\">'+esc(r[2])+'</td><td class=\"src\">'"),
           lit("'</td><td class=\"n'+cl+'\">'+esc(r[2]||(/^gold/.test(k)?\"Change not available yet\":\"\"))+'</td><td class=\"src\">'"), tag="ctx-blank")
srv = srv + "\n" + blk
app = app + ablk
idx = edit(idx, '<script defer src="/app.js?v=chat100"></script>', '<script defer src="/app.js?v=chat100c"></script>', tag="idx-token")
# legacy About markup in index.html (replaced by the app's About sheet when opened): same byline and link
idx = edit(idx, '<a href="https://www.linkedin.com/in/VRAJ2710" target="_blank" rel="noopener" class="about-li">',
           '<a href="https://www.linkedin.com/company/thedispatchmarket" target="_blank" rel="noopener noreferrer" class="about-li">', tag="idx-li")
idx = edit(idx, "            Connect on LinkedIn\n", "            The Dispatch Market on LinkedIn\n", tag="idx-li-label")
for nm, s in ((S, srv), (A, app), (I, idx)):
    open(nm, "w", encoding="utf-8").write(s)
print("patch_c100c: ok")
