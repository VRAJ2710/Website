# Client checks on a local page: hide switch keeps the section, idempotent on mutations, fiscaldata credit, r6p FRED walker co-exists.
import asyncio, json, os, re
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
client = open(os.path.join(HERE, "..", "client_chat107credits.js")).read()
r6p = open(os.path.join(HERE, "..", "server_block_c102r6p.js")).read()
m = re.search(r"var FRED_JS = '(<script id=\"c102r6o-fred\">.*?</script>)';", r6p); fred_js = m.group(1).encode().decode("unicode_escape")
def page(cfg):
    return ("<!doctype html><html><body><nav><a href='/calendar/'>Calendar</a></nav><main><section id='cal'><h2>US</h2><div class='c101d-tw'><table class='c97t'><tbody>"
      "<tr><td>Jobs</td><td>+165k</td><td><span class='c97s'>Change in nonfarm payrolls (FRED PAYEMS), unemployment rate (FRED UNRATE)</span></td></tr>"
      "<tr><td>GDP</td><td>3.4%</td><td><span class='c97s'>Real GDP growth (FRED A191RL1Q225SBEA)</span></td></tr></tbody></table></div></section>"
      "<section id='d'><table class='ctx'><tr><td>US 10-year real yield</td><td><span class='c101f-off'>Official daily: 2.86% (US Treasury via FRED, 12 Nov)</span></td></tr></table></section>"
      "<section id='f'><p>Debt: <a href='https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/'>debt to the penny</a></p></section></main>"
      + fred_js + "<script>window.__c107cfg=" + json.dumps(cfg) + ";" + client + "</script></body></html>")
async def run():
    ok = 0; bad = 0
    def chk(n, c):
        nonlocal ok, bad
        print(("ok   - " if c else "FAIL - ") + n); ok += bool(c); bad += (not c)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page()
        await pg.set_content(page({"d": {"PAYEMS": "6 November 2026", "UNRATE": "6 November 2026", "DFII10": "16 November 2026"}, "eia": False, "hide": {"A191RL1Q225SBEA": 1}}))
        await pg.wait_for_timeout(2000)
        ids = await pg.eval_on_selector_all(".c107-cite", "e=>e.map(x=>x.getAttribute('data-id'))")
        chk("citations for PAYEMS, UNRATE, DFII10 and the Fiscal Data credit", sorted(ids) == sorted(["PAYEMS", "UNRATE", "DFII10", "fiscal"]))
        t = await pg.inner_text(".c107-cite[data-id=PAYEMS]")
        chk("citation text format", t == "U.S. Bureau of Labor Statistics, All Employees, Total Nonfarm [PAYEMS], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/PAYEMS, 6 November 2026")
        chk("hidden series gets no citation line", await pg.locator(".c107-cite[data-id=A191RL1Q225SBEA]").count() == 0)
        hid = await pg.inner_text("#cal tr[data-c107-hidden] td:nth-child(2)"); lab = await pg.inner_text("#cal tr[data-c107-hidden] td:nth-child(1)")
        chk("copyright-hidden series: figure replaced by the notice, section and menu link kept", hid.strip() == "Not shown: awaiting publisher permission" and lab == "GDP" and await pg.locator("nav a[href='/calendar/']").count() == 1 and await pg.locator("#cal h2").count() == 1)
        f = await pg.inner_text(".c107-cite[data-id=fiscal]")
        chk("Fiscal Data credit text", f == "Source: U.S. Treasury, Fiscal Data")
        chk("Fiscal Data credit link", await pg.get_attribute(".c107-cite[data-id=fiscal] a", "href") == "https://fiscaldata.treasury.gov")
        n0 = await pg.locator(".c107-cite").count()
        await pg.evaluate("()=>{const s=document.querySelector('#cal .c97s');s.textContent=s.textContent+' ';document.body.appendChild(document.createElement('div'))}")
        await pg.wait_for_timeout(1500)
        chk("idempotent after DOM mutations", await pg.locator(".c107-cite").count() == n0)
        chk("cites sit after the table wrapper, outside the table", await pg.evaluate("()=>{const h=document.querySelector('#cal .c107-cites');return h.previousElementSibling.classList.contains('c101d-tw')}"))
        await b.close()
    print(ok, "passed,", bad, "failed")
asyncio.run(run())
