#!/usr/bin/env python3
# chat101f on top of chat101e: market quotes first. The US 10-year yield, the 10-year real yield and WTI crude show a free,
# delayed market quote that refreshes through the day (Tradeweb via CNBC for yields, NYMEX futures via the existing Yahoo
# path for WTI); the official daily figure (FRED, EIA) is a secondary line underneath, or is used, clearly labelled, only if
# the quote is missing. Gold's change reads "since yesterday's close (23:57 UK, 4 Nov)". Public pages re-read prices every
# 5 minutes while visible; short server caches wait briefly for a refresh instead of serving a reading far past its TTL.
# Touches server.js, app.js (re-embeds the renderer in the chat101e block) and index.html (app.js?v=chat101f).
# Usage: patch_c101f.py SERVER APP INDEX SRV_BLOCK REND_MID REND_BRIEF
import sys, json
S, A, I, SB, RM, RB = sys.argv[1:7]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx, sblk, rmid, rbrief = rd(S), rd(A), rd(I), rd(SB), rd(RM), rd(RB)
def die(m): sys.exit("patch_c101f: " + m)
if '/app.js?v=chat101f"' in idx or "chat101f:" in app or "chat101f: market quotes first" in srv: die("already applied")
if '/app.js?v=chat101e"' not in idx or "chat101e: market cards" not in app: die("chat101e is not applied")
LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != LINE1: die("line 1 changed")
def rep(t, old, new, n=1, what=""):
    c = t.count(old)
    if c != n: die("anchor %s: found %d, want %d" % (what or old[:60], c, n))
    return t.replace(old, new)

# ── 1. the public renderer (C96_LIVE_JS) ──
P = "const C96_LIVE_JS = "
L = [l for l in srv.split("\n") if l.startswith(P)]
if len(L) != 1: die("renderer not found")
old_line = L[0]
js0, end = json.JSONDecoder().raw_decode(old_line[len(P):])
tail = old_line[len(P) + end:]
if tail != "; // chat97: DGS10 first": die("renderer tail changed")
js = js0
js = rep(js, 'wtif:["WTI","WTI crude futures (NYMEX, front month)","$",2]', 'wtif:["WTI","WTI crude oil futures (NYMEX, front month, delayed)","$",2]', what="wtif")
js = rep(js, 'tnx:["TNX","US 10-year Treasury yield","",2,"%"]', 'tnx:["TNX","US 10-year Treasury yield (Cboe index, delayed)","",2,"%"]', what="tnx")
js = rep(js, 'want.gold?get("/api/c100b/gold-change"):null]).then(', 'want.gold?get("/api/c100b/gold-change"):null,(want.tnx||want.ry)?get("/api/c101f/rates"):null]).then(', what="fetch")
i = js.find('if(ry&&ry.available&&isFinite(Number(ry.value)))rows.ry=')
E = 'else if(rows.wtif)rows.wti=rows.wtif;\n'
j = js.find(E)
if i < 0 or j < i or js.count(E) != 1 or js.count('if(ry&&ry.available&&isFinite(Number(ry.value)))rows.ry=') != 1: die("rows block")
js = js[:i] + rmid.strip("\n") + "\n" + js[j + len(E):]
bi = js.find('if(rows.ry)p.push("The US 10-year real yield was ')
BE = '" on the day":"")+".");\n'
bj = js.find(BE, bi)
if bi < 0 or bj < 0 or js.count(BE) != 1: die("brief block")
js = js[:bi] + rbrief.strip("\n") + "\n" + js[bj + len(BE):]
js = rep(js, 'r[3]=r[3]+" \\u00b7 Change "+c.basis}', 'r[3]=r[3]+" \\u00b7 Change "+(c.label||c.basis)}', what="gold basis")
js = rep(js, "'<span class=\"src msrc\">'+esc(r[3])+'</span></td><td class=\"n\">'",
         "'<span class=\"src msrc\">'+esc(r[3])+(r[6]?'<span class=\"c101f-off\">'+esc(r[6])+'</span>':\"\")+(r[7]?'<span class=\"c101f-ses\">'+esc(r[7])+'</span>':\"\")+'</span></td><td class=\"n\">'", what="msrc")
js = rep(js, "'</td><td class=\"src\">'+esc(r[3])+'</td></tr>'",
         "'</td><td class=\"src\">'+esc(r[3])+(r[6]?'<span class=\"c101f-off\">'+esc(r[6])+'</span>':\"\")+(r[7]?'<span class=\"c101f-ses\">'+esc(r[7])+'</span>':\"\")+'</td></tr>'", what="src td")
CSS = 'try{if(!document.getElementById("c101f-css")){var c101fS=document.createElement("style");c101fS.id="c101f-css";c101fS.textContent=".c101f-off,.c101f-ses{display:block;margin-top:2px}.c101f-off{font-weight:600}";(document.head||document.documentElement).appendChild(c101fS)}}catch(e){}\n'
if not js.startswith("(function(){\n"): die("renderer head")
js = "(function(){\n" + CSS + js[len("(function(){\n"):]
for bad in ("GC=F", "CL=F", "^TNX", "</script", "buy now", "sell now"):
    if bad in js: die("renderer contains " + bad)
# public pages: run now, then re-read every 5 minutes while the tab is visible
pub = 'window.__c96run=function(){' + js.rstrip("\n") + '};window.__c96run();if(!window.__c96t)window.__c96t=setInterval(function(){if(!document.hidden)window.__c96run()},300000);\n'
new_line = P + json.dumps(pub) + "; // chat101f: market quotes first, official daily figure underneath; refresh every 5 min"
srv = rep(srv, old_line + "\n", new_line + "\n", what="renderer line")

# ── 2. short server caches: wait briefly for a refresh when a reading is well past its TTL ──
srv = rep(srv, "  if (e.v == null && e.p) await Promise.race([e.p, new Promise(r => setTimeout(r, waitMs || 9000))]);\n  return { v: e.v, at: e.at, err: e.err, stale:",
          "  if (e.v == null && e.p) await Promise.race([e.p, new Promise(r => setTimeout(r, waitMs || 9000))]);\n"
          "  else if (e.p && ttl <= 15 * 60e3 && now - e.at > ttl + 5 * 60e3) await Promise.race([e.p, new Promise(r => setTimeout(r, 3500))]);   // chat101f: no reading far past its TTL\n"
          "  return { v: e.v, at: e.at, err: e.err, stale:", what="c97Cached")
# ── 3. session line on the public pages, gold dashboard note, "What changed today", dashboard tiles ──
srv = rep(srv, '". Treasury yields: the latest daily figure"', '". Treasury yields: market quotes, delayed; the official daily figure is shown under each"', what="ses fx")
srv = rep(srv, "Treasury yields are official end-of-day prints, published the next US morning. The dollar index is a delayed market price.",
          "Treasury yields are delayed market quotes (Tradeweb via CNBC) that update through the day; the official daily figure from the US Treasury via FRED is shown under each. If the quote is missing, the official figure is shown and labelled. The dollar index is a delayed market price.", what="gold note")
srv = rep(srv, 'for (const k of ["tnx", "ry"]) { const r = R[k]; if (r && r.date >= yd)', 'for (const k of ["tnx", "ry"]) { const r = R[k] && R[k].offRow || R[k]; if (r && r.date >= yd)', what="today")
srv = rep(srv, 'fromGd("tnx", "US 10-year yield", "10-year US Treasury yield, constant maturity, daily (FRED series DGS10)", C100_URL.fred("DGS10"));',
          'fromGd("tnx", "US 10-year yield", R.tnx && R.tnx.live ? "10-year US Treasury yield, market quote (Tradeweb via CNBC), delayed. " + (R.tnx.official ? R.tnx.official + "; FRED series DGS10" : "Official daily figure: FRED series DGS10") : "10-year US Treasury yield, constant maturity, daily (FRED series DGS10)", R.tnx && R.tnx.live ? R.tnx.url : C100_URL.fred("DGS10"));', what="macro tnx")
srv = rep(srv, 'fromGd("ry", "US real yield (10-year)", "10-year US Treasury inflation-protected yield, daily (FRED series DFII10)", C100_URL.fred("DFII10"));',
          'fromGd("ry", "US real yield (10-year)", R.ry && R.ry.live ? "10-year US inflation-protected Treasury (TIPS) yield, market quote via CNBC, delayed. " + (R.ry.official ? R.ry.official + "; FRED series DFII10" : "Official daily figure: FRED series DFII10") : "10-year US Treasury inflation-protected yield, daily (FRED series DFII10)", R.ry && R.ry.live ? R.ry.url : C100_URL.fred("DFII10"));', what="macro ry")
# ── 4. source inspector: market-quote rows point at the quote, and the secondary lines are not read as the source ──
srv = rep(srv, 'var SRC=[[/FRED \\((\\w+)\\)|FRED series (\\w+)/,',
          'var SRC=[[/Tradeweb|CNBC/i,function(m,t){var tp=/real yield|TIPS|inflation/i.test(t);return["Market quote via CNBC (delayed)","https://www.cnbc.com/quotes/"+(tp?"US10YTIP":"US10Y"),tp?"10-year US inflation-protected Treasury (TIPS) yield, market quote":"10-year US Treasury yield, market quote"]}],\n[/FRED \\((\\w+)\\)|FRED series (\\w+)/,', what="inspector SRC")
srv = rep(srv, 'if(sc&&sc.length!==undefined){srcT=[].map.call(sc,T).join(" · ")}else if(sc)srcT=T(sc);',
          'if(sc&&sc.length!==undefined){srcT=[].filter.call(sc,function(x){return!x.classList.contains("c101f-off")}).map(function(x){return T(x)}).join(" · ")}else if(sc){var sc1=sc.cloneNode(true);[].forEach.call(sc1.querySelectorAll(".c101f-off,.c101f-ses,.c101e-ses"),function(x){x.remove()});srcT=T(sc1)}', what="inspector srcT")
# ── 5. server block ──
for bad in ("GC=F", "CL=F", "^TNX", "buy now", "sell now"):
    if bad in sblk: die("server block contains " + bad)
srv = srv.rstrip("\n") + "\n" + sblk.lstrip("\n")
if srv.split("\n", 1)[0] != LINE1: die("line 1 lost")

# ── app.js: re-embed the renderer in the chat101e block; per-row session lines win over the group label ──
OLDQ = 'document.querySelectorAll("tbody[data-rows]")'
if js0.count(OLDQ) != 1 or js.count(OLDQ) != 1: die("renderer shape changed")
old_emb, new_emb = js0.replace(OLDQ, 'ROOT.querySelectorAll("tbody[data-rows]")'), js.replace(OLDQ, 'ROOT.querySelectorAll("tbody[data-rows]")')
app = rep(app, old_emb, new_emb, what="embedded renderer")
app = rep(app, 'if (v && sc) { var sp = document.createElement("span"); sp.className = "c101e-ses";', 'if (v && sc && !sc.querySelector(".c101f-ses")) { var sp = document.createElement("span"); sp.className = "c101e-ses";', what="app finish")
app = rep(app, 'if (g === "Rates") return "Treasury yields: the latest daily figure";', 'if (g === "Rates") return /official/i.test(name) ? "Treasury yields: the official daily figure" : "Treasury yields: market quotes, delayed";', what="app rates")
app = rep(app, "Free feeds are delayed; official yields are daily prints.", "Free feeds are delayed; yields are market quotes. Tap a yield for its official daily figure.", what="app macro note")
app = rep(app, '".c101e-mk .msrc{display:none}.c101e-mk .c101e-ses{display:block;margin-top:2px}"', '".c101e-mk .msrc{display:none}.c101e-mk .c101e-ses,.c101e-mk .c101f-ses,.c101e-mk .c101f-off{display:block;margin-top:2px}.c101e-mk .c101f-off{font-weight:600}"', what="app css")
app = app.rstrip("\n") + "\n// ── chat101f: market quotes first in the Market context cards (renderer re-embedded from server.js at build time) ──\n"
if idx.count('<script defer src="/app.js?v=chat101e"></script>') != 1: die("idx-token")
idx = idx.replace('<script defer src="/app.js?v=chat101e"></script>', '<script defer src="/app.js?v=chat101f"></script>')
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101f: ok")
