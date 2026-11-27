# usage: shots7.py <new front> <old front> <new server> <outdir> <cookies.json>
# cookies.json: {"unverified_new": tok, "verified_new": tok, "verified_old": tok}
import asyncio, sys, os, json, urllib.request
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
NEW, OLD, SRV, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]; C = json.load(open(sys.argv[5])); os.makedirs(OUT, exist_ok=True)
VIEWS = [(w, s) for w in (320, 390, 1280) for s in ("dark", "light")]
def diff(a, b):
  a, b = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
  if a.size != b.size: return 1.0
  m = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 24 else 0)
  return sum(m.histogram()[255:]) / (a.size[0] * a.size[1])
async def ctx_for(b, base, w, s, tok=None):
  ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=s)
  ck = [{"name": "dispatch_theme", "value": s, "url": base}]
  if tok: ck.append({"name": "dispatch_session", "value": tok, "url": base})
  await ctx.add_cookies(ck); return ctx
async def load(ctx, base, path, errs):
  pg = await ctx.new_page()
  pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
  await pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(base) else r.continue_())
  await pg.goto(base + path, wait_until="load"); await pg.wait_for_timeout(1500)
  await pg.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
  await pg.wait_for_timeout(300); return pg
OV = "()=>({sw:document.documentElement.scrollWidth,cw:innerWidth,h1:(document.querySelector('h1')||{}).textContent||'',banner:!!document.getElementById('c112v')})"
BAN = """()=>{const b=document.getElementById('c112v');if(!b)return null;const r=b.getBoundingClientRect(),t=b.querySelector('.c112v-t').getBoundingClientRect(),x=b.querySelector('.c112v-x').getBoundingClientRect(),y=b.querySelector('.c112v-r').getBoundingClientRect();
 const hit=(q)=>{const e=document.elementFromPoint(q.left+q.width/2,q.top+q.height/2);return !!(e&&b.contains(e))};
 return {top:Math.round(r.top),left:Math.round(r.left),right:Math.round(r.right),h:Math.round(r.height),text_visible:hit(t),dismiss_visible:hit(x),resend_visible:hit(y),sw:document.documentElement.scrollWidth,cw:innerWidth}}"""
async def run():
  R = {"issues": []}
  async with async_playwright() as p:
    b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for w, s in VIEWS:
      k = "%d-%s" % (w, s)
      # 1) /signin guest: pixel-identical to step 6
      e1, e2 = [], []
      for tag, base, errs in (("new", NEW, e1), ("old", OLD, e2)):
        c = await ctx_for(b, base, w, s); pg = await load(c, base, "/signin", errs); d = await pg.evaluate(OV)
        await pg.screenshot(path="%s/signin-%s.%s.png" % (OUT, k, tag)); await c.close()
        if tag == "new" and d["sw"] > d["cw"]: R["issues"].append("signin overflow " + k)
      R["signin " + k] = round(diff("%s/signin-%s.new.png" % (OUT, k), "%s/signin-%s.old.png" % (OUT, k)), 5)
      if len(e1) > len(e2): R["issues"].append("signin new console errors " + k)
      # 2) verify pages (new only): confirmed (fresh token) and expired/used
      tok = json.load(urllib.request.urlopen(SRV + "/__testdb/token?email=shots@example.com"))["token"]
      for name, path, want in (("verify-ok", "/__auth/verify?token=" + tok, "Email confirmed"), ("verify-bad", "/__auth/verify?token=" + tok, "expired or was already used")):
        c = await ctx_for(b, NEW, w, s); errs = []; pg = await load(c, NEW, path, errs); d = await pg.evaluate(OV)
        await pg.screenshot(path="%s/%s-%s.png" % (OUT, name, k)); await c.close()
        R["%s %s" % (name, k)] = d
        if want not in d["h1"]: R["issues"].append("%s %s h1=%r" % (name, k, d["h1"]))
        if d["sw"] > d["cw"]: R["issues"].append("%s overflow %s" % (name, k))
        if errs: R["issues"].append("%s console errors %s %s" % (name, k, errs[:2]))
      # 3) /gold/ as a signed-in UNVERIFIED user: banner visible, not covered, no overflow
      c = await ctx_for(b, NEW, w, s, C["unverified_new"]); errs = []; pg = await load(c, NEW, "/gold/", errs)
      await pg.wait_for_selector("#c112v", timeout=5000); bd = await pg.evaluate(BAN)
      await pg.screenshot(path="%s/banner-%s.png" % (OUT, k)); R["banner " + k] = bd
      if not (bd and bd["text_visible"] and bd["dismiss_visible"] and bd["resend_visible"] and bd["sw"] <= bd["cw"] and bd["left"] >= 0 and bd["right"] <= w):
        R["issues"].append("banner not fully visible/overflow " + k + " " + json.dumps(bd))
      await c.close()
      # 4) /gold/ as a signed-in VERIFIED user: no banner, pixel-identical to step 6 (same user signed in there); guest: no banner
      for who, tokn, tokold in (("verified", C["verified_new"], C["verified_old"]), ("guest", None, None)):
        shots = {}
        for tag, base, t in (("new", NEW, tokn), ("old", OLD, tokold)):
          c = await ctx_for(b, base, w, s, t); errs = []; pg = await load(c, base, "/gold/", errs); await pg.wait_for_timeout(1200)
          d = await pg.evaluate(OV); fn = "%s/gold-%s-%s.%s.png" % (OUT, who, k, tag); await pg.screenshot(path=fn); shots[tag] = fn; await c.close()
          if tag == "new" and d["banner"]: R["issues"].append("banner shown to %s user %s" % (who, k))
        R["gold-%s %s" % (who, k)] = round(diff(shots["new"], shots["old"]), 5)
    # 5) dismiss persists; resend button reports the limit (a link was just sent at sign-up)
    c = await ctx_for(b, NEW, 390, "dark", C["unverified_new"]); pg = await load(c, NEW, "/gold/", [])
    await pg.wait_for_selector("#c112v"); await pg.click("#c112v .c112v-r"); await pg.wait_for_timeout(800)
    R["resend_click_text"] = await pg.inner_text("#c112v .c112v-t")
    await pg.click("#c112v .c112v-x"); await pg.wait_for_timeout(200); gone = await pg.evaluate("()=>!document.getElementById('c112v')")
    await pg.reload(wait_until="load"); await pg.wait_for_timeout(1800); after = await pg.evaluate("()=>!document.getElementById('c112v')")
    R["dismiss"] = {"gone_on_click": gone, "gone_after_reload": after}; await c.close()
    await b.close()
  worst = max([v for k, v in R.items() if isinstance(v, float)] + [0])
  R["worst_identical_diff"] = worst
  json.dump(R, open(os.path.join(OUT, "shots.json"), "w"), indent=1)
  print("resend_click_text:", R["resend_click_text"]); print("dismiss:", R["dismiss"])
  for k, v in R.items():
    if k.startswith("banner "): print(k, v)
  print("RESULT worst_identical_diff=%.5f issues=%s" % (worst, R["issues"] or "none"))
asyncio.run(run())
