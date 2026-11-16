# Render the dev pages with and without the credits at 320/390/1280, light and dark; check overflow and credit placement.
import asyncio, json, subprocess, sys, time, urllib.request, os
from playwright.async_api import async_playwright
D = "https://41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev"
HERE = os.path.dirname(os.path.abspath(__file__)); SHOTS = os.path.join(HERE, "shots"); os.makedirs(SHOTS, exist_ok=True)
PAGES = sys.argv[1].split(",") if len(sys.argv) > 1 else ["/", "/?preview=v3", "/terminal/", "/calendar/", "/gold/dashboard/", "/tools/scenario/", "/methodology", "/markets/"]
WIDTHS = [320, 390, 1280]
helper = subprocess.Popen(["node", os.path.join(HERE, "transform_server.js"), "8797"], stdout=subprocess.PIPE)
helper.stdout.readline()
def credit(html, url):
    r = urllib.request.Request("http://127.0.0.1:8797/", data=html, headers={"x-url": url}); return urllib.request.urlopen(r).read()
MEASURE = r"""() => { const W = innerWidth; const sw = document.scrollingElement.scrollWidth;
  const els = [...document.querySelectorAll('.c107-cite,.c107-fred,.c107-meth')];
  const bad = els.filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > W + 1 || r.left < -1 || e.scrollWidth > e.clientWidth + 1); }).map(e => e.className + ':' + e.textContent.slice(0, 60));
  const vis = els.filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.3; }).length;
  function lum(c){const m=c.match(/[\d.]+/g);if(!m)return 1;const [r,g,b]=m.slice(0,3).map(x=>{x=x/255;return x<=0.03928?x/12.92:Math.pow((x+0.055)/1.055,2.4)});return 0.2126*r+0.7152*g+0.0722*b}
  function bg(e){while(e){const c=getComputedStyle(e).backgroundColor;if(c&&!/rgba\(0, 0, 0, 0\)|transparent/.test(c))return c;e=e.parentElement}return 'rgb(255,255,255)'}
  const contrast = els.filter(e=>e.getBoundingClientRect().width>0).map(e=>{const a=lum(getComputedStyle(e).color),b=lum(bg(e));const r=(Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);return Math.round(r*10)/10});
  return { sw, W, n: els.length, vis, cites: [...document.querySelectorAll('.c107-cite')].map(e => e.getAttribute('data-id')), bad, minContrast: contrast.length ? Math.min(...contrast) : null, dark: document.documentElement.className };
}"""
async def run():
    out = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for pg in PAGES:
            for theme in ["light", "dark"]:
                for w in WIDTHS:
                    res = {}
                    for mode in ["base", "credits"]:
                        c = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=theme)
                        await c.add_cookies([{"name": "dispatch_theme", "value": theme, "url": D}])
                        async def handle(route, request, mode=mode):
                            try:
                                r = await route.fetch()
                                body = await r.body()
                                ct = r.headers.get("content-type", "")
                                if mode == "credits" and "text/html" in ct:
                                    u = request.url[len(D):] or "/"
                                    body = credit(body, u)
                                h = dict(r.headers); h.pop("content-length", None); h.pop("content-encoding", None)
                                await route.fulfill(status=r.status, headers=h, body=body)
                            except Exception:
                                try: await route.continue_()
                                except Exception: pass
                        await c.route(lambda u: u.startswith(D) and "/api/" not in u and not u.split("?")[0].endswith((".js", ".css", ".png", ".svg", ".ico", ".woff2", ".json", ".webmanifest")), handle)
                        page = await c.new_page()
                        try:
                            await page.goto(D + pg, wait_until="domcontentloaded", timeout=60000)
                            await page.wait_for_timeout(9000)
                            res[mode] = await page.evaluate(MEASURE)
                            if mode == "credits" and (w in (320, 1280)):
                                name = (pg.strip("/").replace("/", "_").replace("?", "_").replace("=", "_") or "home") + f"_{theme}_{w}"
                                await page.screenshot(path=os.path.join(SHOTS, name + ".png"), full_page=True)
                                els = await page.query_selector_all(".c107-cites,.c107-fred,.c107-meth")
                                for i, e in enumerate(els[:3]):
                                    try: await e.screenshot(path=os.path.join(SHOTS, f"{name}_el{i}.png"))
                                    except Exception: pass
                        except Exception as e:
                            res[mode] = {"error": str(e)[:200]}
                        await c.close()
                    r = {"page": pg, "theme": theme, "w": w, **res}
                    bs, cs = res.get("base", {}), res.get("credits", {})
                    ok = isinstance(cs, dict) and "error" not in cs and not cs.get("bad") and cs.get("sw", 1e9) <= max(bs.get("sw", w), w) + 1
                    r["ok"] = ok
                    out.append(r)
                    print(("ok  " if ok else "BAD ") + f"{pg} {theme} {w}: base sw {bs.get('sw')} | credits sw {cs.get('sw')} n {cs.get('n')} vis {cs.get('vis')} cites {cs.get('cites')} bad {cs.get('bad')} contrast {cs.get('minContrast')} {cs.get('error','')}", flush=True)
        await b.close()
    json.dump(out, open(os.path.join(HERE, "render_results.json"), "w"), indent=1)
    helper.terminate()
    print(sum(1 for r in out if r["ok"]), "of", len(out), "ok")
asyncio.run(run())
