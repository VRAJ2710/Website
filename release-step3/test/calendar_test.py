# /calendar/ (saved live page, 27 Nov): after the credits block no raw FRED series ID is in reader text, server HTML or rendered page;
# each series gets its formal citation line. Also: a page whose raw "(FRED X)" text only appears client-side is cleaned by the client.
import asyncio, os, re, subprocess, sys
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.abspath(__file__)); DEP = os.path.dirname(H)
IDS = r"\b(PAYEMS|UNRATE|PCEPI|A191RL1Q225SBEA|DFEDTARL|DFEDTARU|CPIAUCSL|DGS10|DFII10|DTWEXBGS)\b"
src = sys.argv[1] if len(sys.argv) > 1 else "/workspace/c110/live/_calendar_.body"
subprocess.run(["node", H + "/credit_page.js", DEP + "/server_block_chat107credits.js", src, "/calendar/", "/tmp/r3cal.html"], check=True)
html = open("/tmp/r3cal.html").read()
ok = bad = 0
def chk(n, c):
    global ok, bad
    print(("ok   - " if c else "FAIL - ") + n); ok += bool(c); bad += (not c)
raw_before = len(re.findall(r"\(FRED [A-Z0-9, ]+\)", open(src).read()))
def text_only(h): return re.sub(r"<script\b[\s\S]*?</script\s*>|<style\b[\s\S]*?</style\s*>|<[^>]*>", " ", h)
chk("saved page had %d raw '(FRED ID)' mentions" % raw_before, raw_before >= 3)
chk("server HTML text has no '(FRED ID)' and no series IDs (no-JS readers, crawlers)", not re.search(r"\(FRED [A-Z0-9]", text_only(html)) and not re.search(IDS, text_only(html)))
chk("markers placed for every mention", html.count('data-c107-ids="') == raw_before)
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 900})
        await pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith("http://r3.test/") else r.fulfill(status=200, content_type="text/html", body=html))
        await pg.goto("http://r3.test/calendar/"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("""()=>{const all=document.body.innerText;const cites=[...document.querySelectorAll('.c107-cite')].map(e=>e.getAttribute('data-id'));const dup=[...document.querySelectorAll('.c107-cites')].some(h=>{const a=[...h.children].map(e=>e.getAttribute('data-id'));return new Set(a).size!==a.length});
          const clone=document.body.cloneNode(true);clone.querySelectorAll('.c107-cites,script,style').forEach(e=>e.remove());
          return {dup:dup,cites:cites,reader:clone.innerText,payems:(document.querySelector('.c107-cite[data-id=PAYEMS]')||{}).textContent||'',sw:document.documentElement.scrollWidth}}""")
        chk("rendered reader text (citations aside) has no raw series IDs", not re.search(IDS, r["reader"]) and "(FRED " not in r["reader"])
        want = set(re.findall(r'data-c107-ids="([^"]+)"', html)); want = set(x for w in want for x in w.split(","))
        chk("formal citation line for every series, once per table/card (as in 12e9f76f): %s" % sorted(want), set(r["cites"]) >= want and not r["dup"])
        chk("PAYEMS citation is the formal FRED form with the access date", r["payems"].startswith("U.S. Bureau of Labor Statistics, All Employees, Total Nonfarm [PAYEMS], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/PAYEMS, 27 November 2026"))
        chk("no horizontal overflow at 390", r["sw"] <= 390)
        # client-only path: raw text injected after load (no server marker)
        await pg.evaluate("""()=>{const t=document.createElement('table');t.id='late';t.innerHTML='<tr><td><span class="c97s">Year-on-year change (FRED PCEPI)</span></td></tr>';document.querySelector('main').appendChild(t)}""")
        await pg.wait_for_timeout(1200)
        late = await pg.evaluate("()=>[document.getElementById('late').innerText, [...document.querySelectorAll('.c107-cite[data-id=PCEPI]')].length]")
        chk("client cleans late raw text to '(FRED)' and cites it once", "(FRED)" in late[0] and "PCEPI" not in late[0] and late[1] >= 1)
        await b.close()
asyncio.run(run())
print("%d passed, %d failed" % (ok, bad)); sys.exit(1 if bad else 0)
