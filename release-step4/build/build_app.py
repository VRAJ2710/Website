import hunks,hashlib,json,sys
live=open('app.live.js').read(); assert hashlib.md5(live.encode()).hexdigest()=='bd13a193f2a16ef7d7a4508c25231bb9'
hs=hunks.parse(open('app.diff').read()); H={h['id']:h for h in hs}
EXCL={
 # r6o client label fixes (commit 6c0847e, not a navy commit; the r6p server scrub already covers them)
 '2737c':'r6o','2742c':'r6o','13845c':'r6o','13849c':'r6o','37248a':'r6o','37255a':'r6o',
 # d757562/e60934a Ask widget (not navy commits): a11y + stream-failure behaviour
 '20739c':'ask','21034a':'ask','21039c':'ask','21045a':'ask','21153c':'ask-behaviour','21227a':'ask','21229c':'ask','21231c':'ask','21235c':'ask','21239c':'ask','21241a':'ask',
 '19298c':'data-fetch (CoinGecko browser fallback removal)',
 '41044d':'plain-English rewrite removal (would show NO LIVE SYNC / UNAVAILABLE)',
 '41363c':'default theme dark (kept system)','41367c':'default theme dark (kept system)'}
OVR={
 # deliberate deviation from dev: keep the live calm desk (no dense terminal ticker tape with raw symbols) on the navy shell
 '30111c':['  if (document.documentElement.classList.contains("c93") || document.documentElement.classList.contains("dispatch-shell")) return; // chat110navy: calm desk kept'],
 '13235c':[H['13235c']['new'][0], H['13235c']['new'][1].replace('const primary=isPrimaryLiveQuote(a.tk);','const primary=hasSyncedQuote(a.tk);')],
 '13256c':[H['13256c']['new'][0].replace('d.p:"NO LIVE SYNC"}','d.p:_rt22NoSync()}'), H['13256c']['new'][1]],
}
assert 'hasSyncedQuote' in OVR['13235c'][1] and '_rt22NoSync()' in OVR['13256c'][0]
INC={h['id'] for h in hs if h['id'] not in EXCL}
assert len(INC)+len(EXCL)==len(hs)
lines=live.split('\n')
# chat110navy-only presentation fix (not in dev): the footer clock re-adds "UK" before the literal " UK time" -> "UK UK time"
_L='      els.forEach(el => { if (el.textContent !== txt) el.textContent = txt; });'
assert lines.count(_L)==1
_n=lines.index(_L)+1
hs.append({'id':'%dc'%_n,'key':'custom','a1':_n,'a2':_n,'op':'c','old':[_L],'new':['      els.forEach(el => { const v = el.classList.contains("stf-time") ? String(txt).replace(/\\s*UK\\s*$/i, "") : txt; if (el.textContent !== v) el.textContent = v; }); // chat110navy: no "UK UK time"']})
INC.add('%dc'%_n)
out='\n'.join(hunks.apply(lines,hs,INC,OVR))
open('app.navy.js','w').write(out)
json.dump({'included':sorted(INC,key=lambda x:int(x[:-1])),'excluded':EXCL,'overrides':list(OVR)},open('app_split.json','w'),indent=1)
print(hashlib.md5(out.encode()).hexdigest(), len(out.encode()), len(INC), len(EXCL))
patch=[{'id':h['id'],'a1':h['a1'],'a2':h['a2'],'op':h['op'],'old':h['old'],'new':OVR.get(h['id'],h['new'])} for h in hs if h['id'] in INC]
json.dump({'base_md5':'bd13a193f2a16ef7d7a4508c25231bb9','result_md5':hashlib.md5(out.encode()).hexdigest(),'hunks':patch,'excluded':EXCL},open('/workspace/c112/release-step4/app_navy_patch.json','w'),indent=0,ensure_ascii=False)
