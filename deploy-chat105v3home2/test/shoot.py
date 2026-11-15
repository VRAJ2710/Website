import asyncio, json, sys, os
from playwright.async_api import async_playwright
from PIL import Image
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8787'
OUT=sys.argv[2] if len(sys.argv)>2 else '/workspace/v3-home-preview/local'
os.makedirs(OUT,exist_ok=True)
CODES=r"GC=F|SI=F|BZ=F|CL=F|DX-Y|\^TNX|\^VIX|\^GSPC|BTC-USD|GBPUSD=X|\bDGS\d+\b|\bDFII\d+\b|CPIAUCSL|CPILFESL|PCEPI|PAYEMS|UNRATE|DFEDTAR[LU]|A191RL1Q225SBEA|DTWEXBGS|T10YIE|gold-api-spot-proxy|dxy-fx-computed|UK UK|CACHED|NO LIVE SYNC|TIME UNAVAILABLE|SOURCE UNAVAILABLE|REFERENCE FEEDS|gold-api\\.com spot price"
SPOT=r"spot[^.\n]{0,25}futures|futures[^.\n]{0,25}\bspot\b(?! price\.)"
CHECK="""()=>{const W=innerWidth;const bad=[];document.querySelectorAll('body *').forEach(e=>{if(e.closest('svg')||e.closest('.c96hp'))return;const st=getComputedStyle(e);if(st.position==='fixed'||st.display==='none'||st.visibility==='hidden')return;let p=e.parentElement,clip=false;while(p&&p!==document.body){const o=getComputedStyle(p).overflowX;if(o!=='visible'){const pr=p.getBoundingClientRect();if(pr.right<=W+0.5&&pr.left>=-0.5){clip=true;break}}p=p.parentElement}if(clip)return;const r=e.getBoundingClientRect();if(r.width&&(r.right>W+0.5||r.left<-0.5))bad.push((typeof e.className==='string'&&e.className?e.className:e.tagName)+':'+Math.round(r.left)+'-'+Math.round(r.right))});
const v3=document.getElementById('v3home');const txt=document.body.innerText;const vt=v3?v3.innerText:'';
const codes=(txt.match(new RegExp(%r,'g'))||[]);const spot=(vt.match(new RegExp(%r,'gi'))||[]);
const empties=[...document.querySelectorAll('#v3home .v3-empty')].map(e=>e.closest('article,div.v3-card')?.id+': '+e.innerText);
const loading=document.querySelectorAll('#v3home .v3-load').length;
const links=[...document.querySelectorAll('header.site a[href]')].map(a=>a.getAttribute('href'));
return {sw:document.documentElement.scrollWidth,bw:document.body.scrollWidth,W,bad:bad.slice(0,10),codes,spot,empties,loading,menuLinks:links.length,uniqMenu:[...new Set(links)].length,ready:v3&&v3.getAttribute('data-v3-ready'),tape:(document.querySelector('.public-market-tape')||{}).innerText||null,themeBtn:(document.querySelector('.c97tg-one')||{}).innerText||null,htmlClass:document.documentElement.className,srcLines:document.querySelectorAll('#v3home .v3-src').length,lags:document.querySelectorAll('#v3home .v3-lag').length,bg:getComputedStyle(document.body).backgroundColor}}"""%(CODES,SPOT)
async def main():
    res={}
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        for th in ['dark','light']:
            for w in [320,390,1280]:
                ctx=await b.new_context(viewport={'width':w,'height':844 if w<900 else 900},device_scale_factor=2 if w<900 else 1,color_scheme=th)
                pg=await ctx.new_page()
                await pg.goto(BASE+'/?preview=v3',wait_until='domcontentloaded',timeout=90000)
                try: await pg.wait_for_selector('#v3home[data-v3-ready="1"]',timeout=90000)
                except Exception as e: print('not ready',th,w)
                await pg.wait_for_timeout(800)
                c=await pg.evaluate(CHECK); c['ok']=c['sw']<=w and not c['bad'] and not c['codes'] and not c['spot']
                res[f'{th}-{w}']=c; print(th,w,json.dumps(c)[:600])
                base=f'{OUT}/home-v3-{w}-{th}'
                if w==390:
                    await pg.screenshot(path=base+'-screen.png')
                if w in (390,1280):
                    await pg.screenshot(path=base+'-full.png',full_page=True)
                if w==390 and th=='dark':
                    await pg.click('header.site details.menu>summary'); await pg.wait_for_timeout(400)
                    await pg.screenshot(path=f'{OUT}/home-v3-390-dark-menu.png')
                    mv=await pg.evaluate("()=>{const n=document.querySelector('header.site details.menu[open]>nav.c101c-sheet');if(!n)return null;const r=n.getBoundingClientRect();return {open:true,w:r.width,h:r.height,links:n.querySelectorAll('a[href]').length}}")
                    res['menu-390-dark']=mv; print('menu',mv)
                await ctx.close()
        await b.close()
    json.dump(res,open(f'{OUT}/overflow.json','w'),indent=1)
    for f in os.listdir(OUT):
        if f.endswith('.png'):
            Image.open(f'{OUT}/{f}').convert('RGB').save(f'{OUT}/{f[:-4]}.jpg','JPEG',quality=84,optimize=True)
asyncio.run(main())
