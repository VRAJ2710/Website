#!/usr/bin/env python3
# Headless render of the SIGNED-IN member app (harness session cookie) with client-side navigation between the 4 routes, to a
# non-target route and back. usage: app_render.py BASE OUTDIR [baseline]   ('baseline' = step-9b server: expect no layer)
import asyncio, json, sys, os
from playwright.async_api import async_playwright
B, OUT = sys.argv[1].rstrip("/"), sys.argv[2]; BASE = len(sys.argv) > 3 and sys.argv[3] == "baseline"
os.makedirs(OUT, exist_ok=True)
STATE = """(want)=>{const all=[...document.querySelectorAll('#chat114viz')];const v=all[0]||null;const de=document.documentElement;
 const mn=document.getElementById('main');const par=v&&v.parentElement;
 const r=v?v.getBoundingClientRect():null; const tg=par||mn; const vpTop=r?Math.round(r.top):null;
 return {path:location.pathname,n:all.length,page:v&&v.getAttribute('data-cz-page'),ready:v&&v.getAttribute('data-cz-ready'),
  parent:par?(par.id||(par.classList.contains('term-overlay-body')?((par.closest('.term-overlay')||{}).id||'')+'-body':par.tagName)):null,first:!!(par&&par.firstElementChild===v),visible:!!(r&&r.width>0&&r.height>0),top:vpTop,
  cards:v?v.querySelectorAll('.cz-card').length:0,gauges:v?v.querySelectorAll('.cz-g').length:0,chips:v?v.querySelectorAll('.cz-chip').length:0,
  sparks:v?v.querySelectorAll('svg.cz-spark').length:0,tiles:v?v.querySelectorAll('.cz-tile').length:0,events:v?v.querySelectorAll('.cz-tl li').length:0,
  cls:de.className.split(' ').filter(c=>/^cz-/.test(c)).join(' '),theme:de.getAttribute('data-theme'),
  overflow:de.scrollWidth>de.clientWidth+1,raw:v?/\\b(DGS10|DFII10|DTWEXBGS|GC=F|\\^VIX|TNX|CL=F)\\b/.test(v.innerText):false,
  appKids:tg?[...tg.children].filter(c=>c.id!=='chat114viz').length:0}}"""
async def settle(pg, expect, want):
    for _ in range(60):
        s = await pg.evaluate(STATE, want)
        if not expect or (s["n"] == 1 and s["ready"] == "1"): return
        await pg.wait_for_timeout(500)
async def run(b, w, scheme, res):
    ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme)
    await ctx.add_cookies([{"name": "dispatch_session", "value": "hmember", "url": B}])
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)[:200]))
    pg.on("console", lambda m: errs.append(m.text[:200]) if m.type == "error" else None)
    pg.on("response", lambda r: errs.append("HTTP %d %s" % (r.status, r.url.split("://", 1)[-1].split("/", 1)[-1].split("?")[0])) if r.status >= 400 else None)
    await pg.goto(B + "/brief/", wait_until="load", timeout=90000); await pg.wait_for_timeout(2500)
    want = "desk" if w >= 1024 else "main"
    steps = [("load /brief/", None, "brief"), ("nav gold", "gold", "gold"), ("nav markets", "mkt", "markets"), ("nav research", "research", "research"),
             ("nav brief", "brief", "brief"), ("nav non-target playbook", "playbook", None), ("history back", "BACK", "brief"), ("nav gold again", "gold", "gold")]
    for i, (label, act, exp) in enumerate(steps):
        if act == "BACK": await pg.evaluate("()=>history.back()")
        elif act: await pg.evaluate("(p)=>{ if (typeof nav==='function') nav(p, {history:'push'}); }", act)
        await pg.wait_for_timeout(1500)
        if not BASE: await settle(pg, exp, want)
        await pg.wait_for_timeout(800)
        s = await pg.evaluate(STATE, want); s["step"] = label; s["expect"] = exp
        if BASE: ok = s["n"] == 0
        elif exp: ok = (s["n"] == 1 and s["page"] == exp and s["ready"] == "1" and s["visible"] and s["first"] and (s["parent"] == "main" if want == "main" else s["parent"] in ("briefOv-body", "goldOv-body", "researchOv-body", "p1body", "OVBODY")) and s["top"] is not None and s["top"] < 900
                        and ("cz-" + exp) in s["cls"].split() and not s["raw"] and not s["overflow"] and s["appKids"] > 0)
        else: ok = s["n"] == 0 and s["cls"] == "" and not s["overflow"]
        s["ok"] = ok
        shot = os.path.join(OUT, f"{w}-{scheme}-{i}-{label.replace(' ', '_').replace('/', '')}.png")
        await pg.screenshot(path=shot, full_page=False); s["shot"] = os.path.basename(shot)
        res.append(dict(w=w, scheme=scheme, **s))
        print(("OK  " if ok else "BAD ") + f"{w} {scheme} {label}: path {s['path']} n={s['n']} page={s['page']} ready={s['ready']} parent={s['parent']} first={s['first']} cls='{s['cls']}' theme={s['theme']} cards={s['cards']} gauges={s['gauges']} chips={s['chips']} sparks={s['sparks']} tiles={s['tiles']} events={s['events']} overflow={s['overflow']} appKids={s['appKids']}", flush=True)
    await ctx.close(); return errs
async def main():
    res = []; allerr = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for w, scheme in ((1280, "dark"), (1280, "light"), (390, "dark"), (390, "light"), (320, "dark")):
            allerr[f"{w}-{scheme}"] = await run(b, w, scheme, res)
        await b.close()
    json.dump({"steps": res, "errors": allerr}, open(os.path.join(OUT, "app_render.json"), "w"), indent=1)
    for k, v in allerr.items(): print("console errors", k, len(v), sorted(set(v))[:6])
    print("APP_RENDER_OK" if all(r["ok"] for r in res) else "APP_RENDER_BAD")
asyncio.run(main())
