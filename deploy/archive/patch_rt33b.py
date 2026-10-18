import sys,subprocess,shutil
f=sys.argv[-1]; check='--check' in sys.argv
s=open(f,newline='').read()
if 'rt33b' in s: print('SKIP already applied'); sys.exit(0)
old='''    const clientAddress = req.socket?.remoteAddress || "unknown";
    if (!yahooRateLimiter.allow(clientAddress)) {
      return json(res, 200, {}, { "X-Dispatch-Data-Status": "rate_limited" });
    }
    const symbols = parseYahooSymbols(url.searchParams.get("symbols") || "");
    if (symbols === null) return json(res, 400, { error: "Invalid Yahoo symbols requested." });
    return json(res, 200, await yahooQuote(symbols));'''
new='''    // rt33b: per-visitor limit + last-good quotes when limited or failing
    const _fwdQ = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim(); const clientAddress = _fwdQ || req.socket?.remoteAddress || "unknown";
    const symbols = parseYahooSymbols(url.searchParams.get("symbols") || "");
    if (symbols === null) return json(res, 400, { error: "Invalid Yahoo symbols requested." });
    globalThis.__rt33bLastGood = globalThis.__rt33bLastGood || new Map();
    const _lg = globalThis.__rt33bLastGood;
    const _fromLastGood = () => { const out = {}; for (const sym of symbols) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000) out[sym] = e.q; } return out; };
    if (!yahooRateLimiter.allow(clientAddress)) {
      return json(res, 200, _fromLastGood(), { "X-Dispatch-Data-Status": "cached" });
    }
    let _data;
    try { _data = await yahooQuote(symbols); } catch (e) { return json(res, 200, _fromLastGood(), { "X-Dispatch-Data-Status": "stale" }); }
    try { if (_data && typeof _data === "object") { for (const [k, v] of Object.entries(_data)) { if (v && typeof v === "object") _lg.set(k, { q: v, t: Date.now() }); } if (_lg.size > 2000) { const first = _lg.keys().next().value; _lg.delete(first); } for (const sym of symbols) { if (!(_data && _data[sym])) { const e = _lg.get(sym); if (e && Date.now() - e.t < 72 * 3600 * 1000) _data[sym] = e.q; } } } } catch (e) {}
    return json(res, 200, _data);'''
crlf='\r\n' in s
o=old.replace('\n','\r\n') if crlf else old
n=new.replace('\n','\r\n') if crlf else new
c=s.count(o)
if c!=1: print(f'SKIP rt33b anchor matched {c} times'); sys.exit(0)
t=s.replace(o,n)
tmp='/tmp/rt33b_check.js'; open(tmp,'w',newline='').write(t)
r=subprocess.run(['node','--check',tmp])
if r.returncode: print('ABORT node --check failed'); sys.exit(1)
if check: print('APPLY rt33b yahoo-quote per-visitor + last-good; node --check passed (dry run)'); sys.exit(0)
open(f,'w',newline='').write(t); print('APPLY rt33b; node --check passed; written',f)
