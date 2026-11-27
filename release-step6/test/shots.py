# usage: shots.py <new base> <old base> <outdir>. /signin and /?settings=1 at 320/390/1280, dark+light, new vs old.
import asyncio, sys, os, json
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
NEW, OLD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)
PAGES = [("signin", "/signin"), ("settings", "/?settings=1")]
async def grab(b, base, path, w, s, fn):
  ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=s)
  await ctx.add_cookies([{"name": "dispatch_theme", "value": s, "url": base}])
  pg = await ctx.new_page(); errs = []
  pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
  await pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(base) else r.continue_())
  await pg.goto(base + path, wait_until="load"); await pg.wait_for_timeout(1500)
  await pg.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
  await pg.wait_for_timeout(300)
  d = await pg.evaluate("()=>({url:location.pathname+location.search,sw:document.documentElement.scrollWidth,cw:innerWidth,theme:document.documentElement.className})")
  await pg.screenshot(path=fn); await ctx.close(); d["errors"] = [e for e in errs if "net::ERR_FAILED" not in e]; return d
async def run():
  res = {}; worst = 0
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for name, path in PAGES:
      for w in (320, 390, 1280):
        for s in ("dark", "light"):
          k = "%s-%d-%s" % (name, w, s); fn = {t: os.path.join(OUT, "%s.%s.png" % (k, t)) for t in ("new", "old")}
          dn = await grab(b, NEW, path, w, s, fn["new"]); do = await grab(b, OLD, path, w, s, fn["old"])
          a, c = Image.open(fn["new"]).convert("RGB"), Image.open(fn["old"]).convert("RGB")
          if a.size != c.size: ratio = 1.0
          else:
            bb = ImageChops.difference(a, c).convert("L").point(lambda v: 255 if v > 24 else 0)
            ratio = sum(bb.histogram()[255:]) / (a.size[0] * a.size[1])
          worst = max(worst, ratio)
          res[k] = {"new": dn, "old": do, "pixel_diff_ratio": round(ratio, 5), "overflow_new": dn["sw"] > dn["cw"]}
          print(k, dn["url"], "overflow" if dn["sw"] > dn["cw"] else "no-overflow", "diff=%.5f" % ratio, "errs=%d" % len(dn["errors"]), flush=True)
    await b.close()
  json.dump(res, open(os.path.join(OUT, "shots.json"), "w"), indent=1)
  ov = [k for k, v in res.items() if v["overflow_new"]]; newerr = [k for k, v in res.items() if len(v["new"]["errors"]) > len(v["old"]["errors"])]
  print("RESULT worst_diff=%.5f overflow=%s new_console_errors=%s" % (worst, ov or "none", newerr or "none"))
asyncio.run(run())
