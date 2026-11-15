#!/usr/bin/env python3
"""Render the reminder on the dev checkout page and the toast on the dev app page (dev HTML fetched read-only,
reminder injected locally) at 320/390/1280 in light and dark; report horizontal overflow. Writes PNGs to argv[1]."""
import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = pathlib.Path("/tmp/c106r")
DEV = "https://41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev"
HERE = pathlib.Path(__file__).resolve().parent
block = (HERE.parent / "server_block_chat106softgate.js").read_text()
js = subprocess.run(["node", "-e", """
const src=require('fs').readFileSync(process.argv[1],'utf8');
const stub='function withAssetVersion(h){return h} function issueEmailVerification(){return true} function currentUser(){return null}';
const f=new Function('console', stub+'\\n'+src+'\\nreturn {html:c106sgReminderHtml({id:"u1",email:"reader.with.a.long.address@example-domain.co.uk",emailVerified:false}), js:C106SG_CLIENT_JS};');
process.stdout.write(JSON.stringify(f({log(){}})));""", str(HERE.parent / "server_block_chat106softgate.js")], capture_output=True, text=True, check=True).stdout
parts = json.loads(js)
report = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for theme in ("light", "dark"):
        sub = (SRC / f"sub_{theme}.html").read_text()
        sub = sub.replace("<main>", "<main>" + parts["html"], 1)
        spa = (SRC / f"spa_{theme}.html").read_text()
        spa = spa.replace("</body>", '<script defer src="/__auth/verify/reminder.js?v=chat106softgate"></script></body>', 1)
        for w in (320, 390, 1280):
            for name, html in (("checkout", sub), ("app", spa)):
                ctx = b.new_context(viewport={"width": w, "height": 800}, color_scheme=theme)
                pg = ctx.new_page()
                def make(html):
                  def handler(route):
                      u = route.request.url
                      if u.startswith("https://dev.test/__auth/verify/reminder.js"):
                          return route.fulfill(status=200, content_type="application/javascript", body=parts["js"])
                      if u.startswith("https://dev.test/__auth/verify/status"):
                          return route.fulfill(status=200, content_type="application/json", body='{"reminder":true}')
                      if u.startswith("https://dev.test/__auth/verify/resend"):
                          return route.fulfill(status=200, content_type="application/json", body='{"state":"sent"}')
                      if u == "https://dev.test/page":
                          return route.fulfill(status=200, content_type="text/html", body=html)
                      if u.startswith("https://dev.test/") and route.request.method == "GET":
                          if route.request.resource_type != "stylesheet":
                              return route.fulfill(status=404, body="")
                          try:
                              r = route.fetch(url=DEV + u[len("https://dev.test"):])
                              return route.fulfill(response=r)
                          except Exception:
                              return None
                      return route.abort()
                  return handler
                pg.route("**/*", make(html))
                pg.goto("https://dev.test/page", wait_until="load")
                pg.wait_for_timeout(700)
                sel = ".c106sg-reminder" if name == "checkout" else "#c106sg-reminder"
                vis = pg.locator(sel).count() == 1 and pg.locator(sel).is_visible()
                if name == "app" and vis:
                    pg.click("#c106sg-reminder button:has-text('Resend')"); pg.wait_for_timeout(300)
                msg = pg.locator(sel).inner_text() if vis else ""
                ov = pg.evaluate("() => { const r = document.querySelector('%s'); const b = r ? r.getBoundingClientRect() : null; return { docW: document.documentElement.scrollWidth, vw: innerWidth, box: b ? [Math.round(b.left), Math.round(b.right)] : null }; }" % sel)
                pg.screenshot(path=str(OUT / f"{name}_{theme}_{w}.png"))
                report.append({"page": name, "theme": theme, "width": w, "visible": vis, "boxInside": bool(ov["box"]) and ov["box"][0] >= 0 and ov["box"][1] <= ov["vw"], "docOverflow": ov["docW"] > ov["vw"], "sentMsg": "sent a new" in msg})
                ctx.close()
    b.close()
print(json.dumps(report, indent=0))
