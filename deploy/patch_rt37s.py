#!/usr/bin/env python3
"""patch_rt37s.py: server. (A) /api/ticker-news?symbol=X: per-ticker Yahoo Finance RSS headlines (free, no key),
15-min cache, 8s timeout. (B) CoinGecko cold miss never serves the original's multi-day persisted copy (24h rule);
the client then fetches CoinGecko directly from the browser. (C) /__auth/subscribe shows 'Premium active' for premium/admin.
Each part is safe-skip. Never runs server.js. Usage: python3 patch_rt37s.py [--check] <server.js>"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
P = [a for a in sys.argv[1:] if a != '--check'][0] if len(sys.argv) > 1 else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt37sNews' in s: print('SKIP rt37s already applied; server.js left as is.'); sys.exit(0)
done = []
def part(name, old, new):
    global s
    c = s.count(old)
    if c != 1: print(f'SKIP  {name} (anchor matched {c} times)'); return
    s = s.replace(old, new); done.append(name)
part('A ticker-news route', 'if (p === "/terms" || p === "/terms/" || p === "/privacy" || p === "/privacy/") return rt33sLegal(res, p);',
     'if (p === "/api/ticker-news") return rt37sNews(res, url);\n  if (p === "/terms" || p === "/terms/" || p === "/privacy" || p === "/privacy/") return rt33sLegal(res, p);')
part('B coingecko 24h rule', '  try { return original(req, res, rawPath); } catch { return fallback(res, path); }', '  return fallback(res, path);')
part('C premium active', 'if (user) return page(res, "Premium · The Dispatch", `<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout',
     'if (user && (user.tier === "premium" || isAdminUser(user))) return page(res, "Premium active · The Dispatch", `<h1>PREMIUM ACTIVE</h1><p>Your account already has Premium. Nothing else to buy.</p>${user.billingPortal ? `<p class="muted">Manage or cancel your subscription from Settings → Manage billing.</p><a href="/settings/">Open Settings</a>` : `<p class="muted">Premium is included with this account, so there is no Stripe billing to manage.</p><a href="/">Back to The Dispatch</a>`}`);\n    if (user) return page(res, "Premium · The Dispatch", `<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout')
if not done: print('Nothing to change'); sys.exit(0)
s = s.rstrip('\n') + r'''

// rt37s: per-ticker Yahoo Finance RSS headlines
const rt37sNewsCache = new Map();
function rt37sDec(t) { return String(t || "").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/<[^>]+>/g, "").trim(); }
async function rt37sNews(res, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z0-9.^=\-]{1,15}$/.test(sym)) return json(res, 400, { error: "bad symbol", items: [] });
  const hit = rt37sNewsCache.get(sym);
  if (hit && Date.now() - hit.at < 15 * 60_000) return json(res, 200, { symbol: sym, items: hit.items, cached: true }, { "Cache-Control": "public, max-age=300" });
  try {
    const r = await fetch(`https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(sym)}&region=US&lang=en-US`, { headers: { "User-Agent": "Mozilla/5.0 (TheDispatch support@thedispatch.uk)" }, signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error("rss " + r.status);
    const xml = await r.text();
    const items = [];
    for (const m of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
      const g = tag => { const x = m[1].match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`)); return x ? rt37sDec(x[1]) : ""; };
      const title = g("title"), link = g("link"), ts = Date.parse(g("pubDate")) || 0;
      if (title && /^https?:\/\//.test(link)) items.push({ title: title.slice(0, 300), link, ts, summary: g("description").slice(0, 400), source: "Yahoo Finance" });
      if (items.length >= 20) break;
    }
    rt37sNewsCache.set(sym, { at: Date.now(), items });
    while (rt37sNewsCache.size > 500) rt37sNewsCache.delete(rt37sNewsCache.keys().next().value);
    return json(res, 200, { symbol: sym, items }, { "Cache-Control": "public, max-age=300" });
  } catch (e) {
    return json(res, 200, { symbol: sym, items: hit ? hit.items : [], unavailable: !hit });
  }
}
'''
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s)
r = subprocess.run(['node', '--check', t.name], capture_output=True, text=True); os.unlink(t.name)
if r.returncode: print('ABORT node --check failed', r.stderr[:400]); sys.exit(1)
for n in done: print('APPLY', n)
if CHECK: print('node --check passed (dry run, nothing written)'); sys.exit(0)
open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('node --check passed\nwritten', P)
