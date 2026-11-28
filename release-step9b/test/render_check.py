#!/usr/bin/env python3
# Local render of the 4 pages from the step-9 server, against the preview proxy (if reachable): same layer, same structure.
# usage: render_check.py NEW_BASE OUTDIR [PROXY_BASE]
import asyncio, json, re, sys, os
from playwright.async_api import async_playwright
NEW, OUT = sys.argv[1].rstrip("/"), sys.argv[2]; PROXY = sys.argv[3].rstrip("/") if len(sys.argv) > 3 else None
os.makedirs(OUT, exist_ok=True)
JS = """()=>{const v=document.getElementById('chat114viz');if(!v)return null;const de=document.documentElement;
 return {text:v.innerText.replace(/[0-9]+([.,][0-9]+)*/g,'#').replace(/\\s+/g,' ').trim(),cards:v.querySelectorAll('.cz-card').length,gauges:v.querySelectorAll('.cz-g').length,chips:v.querySelectorAll('.cz-chip').length,
 sparks:v.querySelectorAll('svg.cz-spark').length,tiles:v.querySelectorAll('.cz-tile').length,events:v.querySelectorAll('.cz-tl li').length,ready:v.getAttribute('data-cz-ready'),
 cls:de.className.split(' ').filter(c=>/^cz-/.test(c)).join(' '),sw:de.scrollWidth,cw:de.clientWidth,
 css:!![...document.styleSheets].find(s=>(s.href||'').includes('/__chat114viz/viz.css')),zeroNA:[...v.querySelectorAll('.cz-card .cz-nav')].length}}"""
async def one(b, base, page, w, scheme, shot):
    ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme); pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:150])); pg.on("console", lambda m: errs.append(m.text[:150]) if m.type == "error" and "replit.com" not in m.text and "ERR_CONNECTION_CLOSED" not in m.text else None)
    await pg.goto(f"{base}/{page}/", wait_until="load", timeout=90000)
    try: await pg.wait_for_selector("#chat114viz[data-cz-ready]", timeout=60000)
    except Exception: pass
    await pg.wait_for_timeout(1200); d = await pg.evaluate(JS)
    if shot: await pg.screenshot(path=shot, full_page=True)
    await ctx.close(); return d, errs
async def main():
    res = {}; ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for page in ("brief", "gold", "markets", "research"):
            for w, scheme in ((1280, "dark"), (390, "dark"), (390, "light"), (320, "dark")):
                d, errs = await one(b, NEW, page, w, scheme, f"{OUT}/{page}-{w}-{scheme}.png")
                q = None
                if PROXY and w == 1280:
                    for _try in range(3):  # the preview proxy fetches live on every request; retry a transient miss
                        q, _ = await one(b, PROXY, page, w, scheme, None)
                        if q and q["ready"]: break
                same = None
                if q and q.get("ready") and d:
                    nz = lambda t: re.sub(r"\s*· stored reading(, not refreshed)?", "", t)  # the stored-reading flag follows the feed's own cache state, not the layer
                    same = {k: (nz(d[k]) == nz(q[k]) if k == "text" else d[k] == q[k]) for k in ("text", "cards", "gauges", "chips", "sparks", "tiles", "events")}
                elif PROXY and w == 1280: same = {"proxy_unavailable": False}
                row = {"ready": bool(d and d["ready"]), "overflow": bool(d and d["sw"] > d["cw"] + 1), "css": bool(d and d["css"]), "cls": d and d["cls"], "counts": d and {k: d[k] for k in ("cards", "gauges", "chips", "sparks", "tiles", "events")}, "errors": errs[:3], "same_as_proxy_preview": same}
                res[f"{page}|{w}|{scheme}"] = row
                good = row["ready"] and not row["overflow"] and row["css"] and not errs and (same is None or all(same.values()))
                ok = ok and good; print(("PASS" if good else "FAIL"), page, w, scheme, json.dumps(row)[:260], flush=True)
        await b.close()
    json.dump(res, open(OUT + "/render.json", "w"), indent=1); print("RENDER_" + ("OK" if ok else "BAD"))
asyncio.run(main())
