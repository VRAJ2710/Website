#!/usr/bin/env python3
# Single-window, one-page-at-a-time audit of the step-4(+4b) dev preview. Non-app pages only. Stops at the first stall.
# usage: python3 dev_single.py [BASE] [--out DIR] [--ba DIR] [--pause SEC]
# default BASE = the Replit dev preview; output: /workspace/qa-dispatch/release-step4/dev-audit/single/ and pairs in .../dev-ba/
import asyncio, json, os, re, subprocess, sys, time
from playwright.async_api import async_playwright
A = sys.argv[1:]; BASE = next((x for x in A if x.startswith("http")), "https://41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev").rstrip("/")
ROOT = "/workspace/qa-dispatch/release-step4"
opt = lambda k, d: A[A.index(k) + 1] if k in A else d
OUT = opt("--out", ROOT + "/dev-audit/single"); BA = opt("--ba", ROOT + "/dev-ba"); BEFORE = ROOT + "/before"; PAUSE = float(opt("--pause", "2"))
PAGES = ["/", "/brief/", "/gold/", "/terminal/", "/markets/", "/news/", "/research/", "/calendar/"]
PAIRS = {("terminal", 390, "dark"), ("terminal", 1280, "dark"), ("markets", 390, "dark"), ("markets", 1280, "dark"), ("news", 390, "dark"),
         ("news", 1280, "dark"), ("research", 390, "dark"), ("research", 1280, "dark"), ("gold", 390, "light"),
         ("brief", 390, "dark"), ("brief", 1280, "dark"), ("gold", 390, "dark"), ("gold", 1280, "dark")}
RAW = re.compile(r'GC=F|DX-Y\.NYB|\^TNX|\^GSPC|\^VIX|CL=F|SI=F|BTC-USD|\bUK UK\b|NO LIVE SYNC|SOURCE UNAVAILABLE|undefined|NaN|\[object')
os.makedirs(OUT, exist_ok=True); os.makedirs(BA, exist_ok=True)
slug = lambda r: r.strip("/").replace("/", "_") or "home"
def healthy():
    r = subprocess.run(["curl", "-s", "--max-time", "15", "-o", "/dev/null", "-w", "%{http_code}", BASE + "/logo-mark.svg"], capture_output=True, text=True)
    return r.stdout.strip() == "200"
class Stall(Exception): pass
def guard():
    if healthy(): return
    time.sleep(10)
    if not healthy(): raise Stall("dev did not answer /logo-mark.svg twice (15 s timeout, 10 s apart)")
INST = """()=>{if(!document.getElementById('c101-inst')){const d=document.createElement('div');d.id='c101-inst';d.setAttribute('role','region');
d.innerHTML='<span>Add The Dispatch Market to your home screen for one-tap Gold, Brief and Dashboard.</span><button class="y">Install</button><button class="n">Not now</button>';document.body.appendChild(d)}}"""
COVER = """async()=>{window.scrollTo(0,1e7);await new Promise(r=>setTimeout(r,500));const ib=document.getElementById('c101-inst');const bb=document.querySelector('.nv-bbar');
const br=bb&&getComputedStyle(bb).display!='none'?bb.getBoundingClientRect():null;const ir=ib?ib.getBoundingClientRect():null;
const f=document.querySelector('footer.site')||document.querySelector('footer');if(!f)return {covered:null,why:'no footer'};
const last=Math.max(...[...f.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().height>0&&e.children.length==0).map(e=>e.getBoundingClientRect().bottom));
const ob=Math.min(ir?ir.top:1e9,br?br.top:1e9);return {covered:Math.max(0,Math.round(last-ob)),inst:ir&&[Math.round(ir.top),Math.round(ir.bottom)],bbar:br&&[Math.round(br.top),Math.round(br.bottom)],
 instOverlapsBbar:!!(ir&&br&&!(ir.bottom<=br.top+1||ir.top>=br.bottom-1))}}"""
async def page_check(b, r, w, s, res):
    guard()
    ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=s); pg = await ctx.new_page(); cons = []; perr = []
    pg.on("console", lambda m: cons.append(m.text[:200]) if m.type == "error" else None); pg.on("pageerror", lambda e: perr.append(str(e)[:200]))
    try:
        resp = await pg.goto(BASE + r, wait_until="load", timeout=45000)
    except Exception as e:
        await ctx.close(); raise Stall("page load timed out: %s %s %s (%s)" % (r, w, s, str(e)[:80]))
    await pg.wait_for_timeout(2500)
    d = await pg.evaluate("""()=>{const de=document.documentElement,t=document.body.innerText;return {cls:de.className,theme:de.getAttribute('data-theme'),
      sw:de.scrollWidth,cw:de.clientWidth,navyb:!!document.querySelector('link[href*="site.css?v=chat110navyb"]'),
      bbar:!!document.querySelector('.nv-bbar')&&getComputedStyle(document.querySelector('.nv-bbar')).display!='none',tape:!!document.querySelector('.public-market-tape'),text:t}}""")
    d["status"] = resp.status if resp else None
    try: d["ends"] = (await resp.text()).rstrip().endswith("</html>")
    except Exception: d["ends"] = None
    d["raw"] = sorted(set(RAW.findall(d.pop("text")))); d["overflow"] = d["sw"] > d["cw"] + 1
    fn = "%s-%d-%s.png" % (slug(r), w, s); await pg.screenshot(path=os.path.join(OUT, fn)); d["shot"] = fn
    if w < 768:
        await pg.evaluate(INST); await pg.wait_for_timeout(500); d["footer"] = await pg.evaluate(COVER)
        await pg.screenshot(path=os.path.join(OUT, "footer-" + fn))
    d["console"] = cons[:5]; d["pageerrors"] = perr[:5]
    res["%s|%d|%s" % (r, w, s)] = d; await ctx.close()
async def menu_check(b, r, w, res):
    guard(); ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme="dark"); pg = await ctx.new_page(); out = {}
    try:
        await pg.goto(BASE + r, wait_until="load", timeout=45000); await pg.wait_for_timeout(2000)
        sel = ".c101b-all>summary" if w >= 1024 and await pg.query_selector("header.site .c101b-all>summary") else "details.menu>summary"
        if await pg.query_selector(sel + ":visible"):
            await pg.locator(sel + ":visible").first.click(); await pg.wait_for_timeout(800)
            out = await pg.evaluate("""(sel)=>{const det=[...document.querySelectorAll(sel)].map(s=>s.parentElement).find(d=>d.open);if(!det)return {open:false};
              const n=det.querySelector('nav')||det;const rr=n.getBoundingClientRect();const groups=[...n.querySelectorAll('h2,summary')].map(e=>e.textContent.trim()).filter(Boolean);
              return {open:true,links:n.querySelectorAll('a').length,groups:groups.length,groupNames:groups.slice(0,14),h:Math.round(rr.height),fullscreen:rr.height>=innerHeight*0.8}}""", sel)
        else:
            btn = pg.locator('button:visible:has-text("Menu"), button:visible:has-text("All sections")').first
            await btn.click(); await pg.wait_for_timeout(800)
            out = await pg.evaluate("""()=>{const n=[...document.querySelectorAll('.c93-menu,.c101c-sheet,[role=dialog]')].find(e=>e.getBoundingClientRect().height>100);if(!n)return {open:false};
              const rr=n.getBoundingClientRect();return {open:true,links:n.querySelectorAll('a').length,groups:n.querySelectorAll('h2,summary').length,h:Math.round(rr.height),fullscreen:rr.height>=innerHeight*0.8}}""")
            sel = "button Menu"
        out["sel"] = sel; await pg.screenshot(path=os.path.join(OUT, "menu-%s-%d.png" % (slug(r), w)))
    except Exception as e: out["error"] = str(e)[:200]
    res["menu %s|%d" % (r, w)] = out; await ctx.close()
async def theme_check(b, r, w, res):
    guard(); ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme="dark"); pg = await ctx.new_page(); out = {}
    g = lambda: pg.evaluate("()=>({cls:(document.documentElement.className.match(/c97-\\w+/)||[''])[0],dt:document.documentElement.getAttribute('data-theme'),bg:getComputedStyle(document.body).backgroundColor,label:((document.querySelector('.c97tg-one')||{}).textContent||'').trim()})")
    try:
        await pg.goto(BASE + r, wait_until="load", timeout=45000); await pg.wait_for_timeout(1500); out["start"] = await g()
        for i in range(3):
            await pg.locator(".c97tg-one:visible").first.click(); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(1500); out["click%d" % (i + 1)] = await g()
        seq = [out[k]["cls"] for k in ("start", "click1", "click2", "click3")]
        out["cycle"] = seq; out["ok"] = len(set(seq[:3])) == 3 and seq[0] == seq[3] and out["click1"]["bg"] != out["click2"]["bg"]
    except Exception as e: out["error"] = str(e)[:200]
    res["theme %s|%d" % (r, w)] = out; await ctx.close()
def pairs():
    from PIL import Image, ImageDraw
    made = []
    for (p, w, s) in sorted(PAIRS):
        fn = "%s-%d-%s.png" % (p, w, s); a, d = os.path.join(BEFORE, fn), os.path.join(OUT, fn)
        if not (os.path.exists(a) and os.path.exists(d)): continue
        A_, B_ = Image.open(a), Image.open(d); h = max(A_.height, B_.height); im = Image.new("RGB", (A_.width + B_.width + 20, h + 30), "white")
        im.paste(A_, (0, 30)); im.paste(B_, (A_.width + 20, 30)); dr = ImageDraw.Draw(im)
        dr.text((5, 5), "BEFORE (live, pre-publish) " + fn, fill="black"); dr.text((A_.width + 25, 5), "AFTER (%s, %s UK)" % (BASE.split("//")[1][:24], time.strftime("%H:%M")), fill="black")
        im.save(os.path.join(BA, fn)); made.append(os.path.join(BA, fn))
    return made
def summary(res):
    issues = []
    for k, d in res.items():
        if k.startswith("menu "):
            if not d.get("open") or d.get("links", 0) < 40: issues.append(("HIGH", k, "menu did not open with all sections", d))
        elif k.startswith("theme "):
            if not d.get("ok"): issues.append(("MED", k, "theme toggle did not cycle", d))
        else:
            if d.get("status") != 200: issues.append(("HIGH", k, "status %s" % d.get("status")))
            if d.get("ends") is False: issues.append(("HIGH", k, "no </html>"))
            if d.get("overflow"): issues.append(("HIGH", k, "horizontal overflow %s>%s" % (d["sw"], d["cw"])))
            if d.get("pageerrors"): issues.append(("HIGH", k, "page errors", d["pageerrors"]))
            if d.get("console"): issues.append(("MED", k, "console errors", d["console"]))
            if d.get("raw"): issues.append(("MED", k, "raw/placeholder text", d["raw"]))
            if not d.get("navyb"): issues.append(("HIGH", k, "site.css?v=chat110navyb link missing (4b not staged?)"))
            f = d.get("footer")
            if f is not None and (f.get("covered") or f.get("instOverlapsBbar")): issues.append(("HIGH", k, "footer covered / install bar overlaps bottom bar", f))
    return issues
async def run():
    res = {}; stalled = None; t0 = time.time()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        try:
            for s in ("dark", "light"):
                for w in (320, 390, 1280):
                    for r in PAGES:
                        await page_check(b, r, w, s, res); print("ok", r, w, s, flush=True); json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1); await asyncio.sleep(PAUSE)
            for r in ("/", "/brief/", "/gold/", "/markets/"):
                for w in (390, 1280):
                    await menu_check(b, r, w, res); print("menu", r, w, flush=True); await asyncio.sleep(PAUSE)
            for r in ("/brief/", "/gold/"):
                for w in (390, 1280):
                    await theme_check(b, r, w, res); print("theme", r, w, flush=True); await asyncio.sleep(PAUSE)
        except Stall as e:
            stalled = str(e); print("STOPPED:", stalled, flush=True)
        await b.close()
    json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1)
    made = pairs(); issues = summary(res)
    with open(os.path.join(OUT, "summary.txt"), "w") as f:
        f.write("base %s | %d results | %.0f s | %s\n" % (BASE, len(res), time.time() - t0, "STOPPED: " + stalled if stalled else "completed"))
        for i in issues: f.write(" ".join(str(x) for x in i) + "\n")
        f.write("pairs:\n" + "\n".join(made) + "\n")
        f.write("VERDICT: %s\n" % ("INCOMPLETE" if stalled else ("CLEAN" if not issues else "ISSUES")))
    print(open(os.path.join(OUT, "summary.txt")).read())
asyncio.run(run())
