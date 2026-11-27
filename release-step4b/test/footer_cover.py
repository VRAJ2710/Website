# usage: footer_cover.py <new base> <old base>. Shows the install bar (same markup as c101-inst-js), scrolls to the end and measures
# how many px of the footer's last line sit under the install bar / bottom bar.
import asyncio, sys
from playwright.async_api import async_playwright
NEW, OLD = sys.argv[1], sys.argv[2]
PAGES = ["/brief/", "/gold/", "/terminal/", "/markets/", "/news/", "/research/", "/calendar/", "/about"]
JS = """async()=>{if(!document.getElementById('c101-inst')){const d=document.createElement('div');d.id='c101-inst';d.setAttribute('role','region');
d.innerHTML='<span>Add The Dispatch Market to your home screen for one-tap Gold, Brief and Dashboard.</span><button class="y">Install</button><button class="n">Not now</button>';document.body.appendChild(d)}
await new Promise(r=>setTimeout(r,600));window.scrollTo(0,1e7);await new Promise(r=>setTimeout(r,500));
const ib=document.getElementById('c101-inst').getBoundingClientRect();const bb=document.querySelector('.nv-bbar');const br=bb&&getComputedStyle(bb).display!='none'?bb.getBoundingClientRect():null;
const f=document.querySelector('footer.site')||document.querySelector('footer');const last=Math.max(...[...f.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().height>0&&e.children.length==0).map(e=>e.getBoundingClientRect().bottom));
const ob=Math.min(ib.top,br?br.top:1e9);return {covered:Math.max(0,Math.round(last-ob)),inst:[Math.round(ib.top),Math.round(ib.bottom)],bbar:br&&[Math.round(br.top),Math.round(br.bottom)],sw:document.documentElement.scrollWidth,cw:innerWidth}}"""
async def run():
  mx = {"new": 0, "old": 0}
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for tag, base in (("new", NEW), ("old", OLD)):
      for w in (320, 390):
        for s in ("dark", "light"):
          ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=s)
          for r in PAGES:
            pg = await ctx.new_page(); await pg.goto(base + r, wait_until="load", timeout=60000); await pg.wait_for_timeout(800)
            d = await pg.evaluate(JS); mx[tag] = max(mx[tag], d["covered"]); print(tag, w, s, r, d)
            if tag == "new" and r == "/gold/" and s == "dark": await pg.screenshot(path=f"/tmp/r4bout/cover-gold-{w}.png")
            await pg.close()
          await ctx.close()
    await b.close()
  print("RESULT new_max_covered=%d old_max_covered=%d" % (mx["new"], mx["old"]))
asyncio.run(run())
