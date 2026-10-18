#!/usr/bin/env python3
"""patch_rt29s.py — server.js on production 2443cdaf (c2ecfade + rt25s). Two independent, skippable parts.
  A. /api/coingecko: in-memory fresh cache (5 min, background refresh after 2 min, one in-flight fetch per path),
     stale-while-error from the newest good body for the same path or its family (same endpoint/params ignoring
     per_page/page/sparkline/price_change_percentage), served with X-Dispatch-Data-Status: stale + real As-Of,
     only if < 24h old; otherwise {unavailable:true}. The old persisted last-good copy is no longer served
     (it was days old). Installed by re-binding coinGecko at the end of the file — no anchor inside the
     function; it SKIPs itself at load if coinGecko / normalizeCoinGeckoPath / json are missing.
  B. /api/news-scores: a 25s deadline on the AI call, so a slow provider becomes the rt21s 200 {unavailable}
     instead of a proxy 502. Two exact anchors; SKIP if either is not found exactly once.
No startup work, no awaits before listen(). Never start server.js in the Replit workspace.
Usage: python3 patch_rt29s.py [--check] path/to/server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
applied, skipped = [], []

# ── A ──
A_MARK = '// rt29s: coinGecko stale-while-error'
A_CODE = r'''
// rt29s: coinGecko stale-while-error (fresh 5 min, family fallback < 24h, never days-old copies)
;(() => {
  try {
    if (typeof coinGecko !== "function" || typeof normalizeCoinGeckoPath !== "function" || typeof json !== "function") {
      console.warn("[rt29s] coinGecko override not installed (missing helper)"); return;
    }
    const FRESH = 5 * 60_000, SWR = 2 * 60_000, MAXSTALE = 24 * 3600_000;
    const fresh = new Map(), fam = new Map(), inflight = new Map();
    const famKey = p => {
      try {
        const u = new URL("https://x" + p);
        ["per_page", "page", "sparkline", "price_change_percentage"].forEach(k => u.searchParams.delete(k));
        return u.pathname + "?" + [...u.searchParams].sort((a, b) => (a[0] > b[0] ? 1 : -1)).map(([k, v]) => k + "=" + v).join("&");
      } catch { return p; }
    };
    const pull = path => {
      if (inflight.has(path)) return inflight.get(path);
      const pr = (async () => {
        const r = await fetch(`https://api.coingecko.com/api/v3${path}`, { headers: { "User-Agent": "DispatchMarkets/1.0" }, signal: AbortSignal.timeout(8_000) });
        if (!r.ok) throw new Error(`CoinGecko ${r.status}`);
        const data = await r.json();
        const at = Date.now(), rec = { data, at };
        fresh.set(path, rec); fam.set(famKey(path), rec);
        if (fresh.size > 64) fresh.delete(fresh.keys().next().value);
        if (fam.size > 64) fam.delete(fam.keys().next().value);
        return rec;
      })();
      inflight.set(path, pr);
      pr.then(() => inflight.delete(path), () => inflight.delete(path));
      return pr;
    };
    const hdr = (st, at) => ({ "X-Dispatch-Data-Status": st, "X-Dispatch-Data-As-Of": new Date(at).toISOString() });
    const fallback = (res, path) => {
      const g = fresh.get(path) || fam.get(famKey(path));
      if (g && Date.now() - g.at < MAXSTALE) return json(res, 200, g.data, hdr("stale", g.at));
      return json(res, 200, { unavailable: true }, { "X-Dispatch-Data-Status": "unavailable" });
    };
    const original = coinGecko;
    coinGecko = async function rt29sCoinGecko(req, res, rawPath) {
      const path = normalizeCoinGeckoPath(rawPath);
      if (!path) return original(req, res, rawPath);
      const f = fresh.get(path);
      if (f && Date.now() - f.at < FRESH) {
        if (Date.now() - f.at > SWR) pull(path).catch(() => {});
        return json(res, 200, f.data, hdr("fresh", f.at));
      }
      try {
        if (typeof coinGeckoRateLimiter !== "undefined" && coinGeckoRateLimiter && !coinGeckoRateLimiter.allow(req.socket?.remoteAddress || "unknown")) return fallback(res, path);
      } catch {}
      try { const rec = await pull(path); return json(res, 200, rec.data, hdr("fresh", rec.at)); }
      catch { return fallback(res, path); }
    };
    console.log("[rt29s] coinGecko stale-while-error installed");
  } catch (e) { console.warn("[rt29s] coinGecko override skipped:", e && e.message); }
})();
'''
if A_MARK in s: skipped.append('A coinGecko (already applied)')
elif 'async function coinGecko(' not in s or 'normalizeCoinGeckoPath' not in s: skipped.append('A coinGecko (function not found)')
else:
    s = s.rstrip('\n') + '\n' + A_CODE; applied.append('A coinGecko stale-while-error')

# ── B ──
B1 = '        try {\n        result = await generateAi({\n          system: `${MARKET_SYSTEM}\\nScore ONLY these supplied headlines.'
B2 = '          },\n        });\n        } catch (rt21sErr) {'
if 'rt29sDeadline' in s: skipped.append('B news-scores deadline (already applied)')
elif s.count(B1) != 1 or s.count(B2) != 1: skipped.append(f'B news-scores deadline (anchors matched {s.count(B1)}/{s.count(B2)})')
else:
    s = s.replace(B1, '        try {\n        const rt29sDeadline = new Promise((_, rej) => { const t = setTimeout(() => { const e = new Error("news-scores deadline"); e.code = "TIMEOUT"; e.status = 504; rej(e); }, 25_000); if (t.unref) t.unref(); });\n        result = await Promise.race([rt29sDeadline, generateAi({\n          system: `${MARKET_SYSTEM}\\nScore ONLY these supplied headlines.')
    s = s.replace(B2, '          },\n        })]);\n        } catch (rt21sErr) {')
    applied.append('B news-scores 25s deadline')

for a in applied: print('APPLY', a)
for k in skipped: print('SKIP ', k)
if not applied: print('Nothing to change; server.js left as is.'); sys.exit(0)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed, nothing written:', r.stderr[:300]); sys.exit(1)
print('node --check passed' + (' (dry run, nothing written)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
