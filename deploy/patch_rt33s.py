#!/usr/bin/env python3
"""patch_rt33s.py — fix the shared Yahoo rate limit that blanks prices for everyone.
Root cause: /api/yahoo-quote and /api/yahoo-chart key their 30/min limiters on req.socket.remoteAddress, which behind
the Replit proxy is the proxy itself — so ALL visitors share one 30-requests-per-minute bucket. Once spent, every
yahoo-quote batch returns {} (X-Dispatch-Data-Status: rate_limited) and the lists show UNAVAILABLE.
  A. Key both limiters on the client IP (last X-Forwarded-For hop, which the proxy appends; falls back to the socket).
  B. When a client is limited, /api/yahoo-quote answers from a server-wide last-good cache (per symbol, < 15 min old,
     header cached) instead of {}. Successful responses feed that cache. No upstream calls are added.
  C. The chart limiter goes from 30 to 90 per client per minute (charts are already cached server-side).
Each part SKIPs on its own if its anchor is not found exactly once. No startup work. Never start server.js in the workspace.
Usage: python3 patch_rt33s.py [--check] path/to/server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
applied, skipped = [], []
if 'rt33sIp' in s: print('SKIP rt33s already applied; server.js left as is.'); sys.exit(0)
def part(name, old, new):
    global s
    n = s.count(old)
    if n != 1: skipped.append(f'{name} (anchor matched {n} times)'); return False
    s = s.replace(old, new); applied.append(name); return True
A1 = '    const clientAddress = req.socket?.remoteAddress || "unknown";\n    if (!yahooRateLimiter.allow(clientAddress)) {\n      return json(res, 200, {}, { "X-Dispatch-Data-Status": "rate_limited" });\n    }\n    const symbols = parseYahooSymbols(url.searchParams.get("symbols") || "");\n    if (symbols === null) return json(res, 400, { error: "Too many Yahoo symbols requested." });\n    return json(res, 200, await yahooQuote(symbols));'
A1n = '    const clientAddress = rt33sIp(req);\n    if (!yahooRateLimiter.allow(clientAddress)) {\n      const rt33sHit = rt33sYqCached(url.searchParams.get("symbols") || "");\n      return json(res, 200, rt33sHit, { "X-Dispatch-Data-Status": Object.keys(rt33sHit).length ? "cached" : "rate_limited" });\n    }\n    const symbols = parseYahooSymbols(url.searchParams.get("symbols") || "");\n    if (symbols === null) return json(res, 400, { error: "Too many Yahoo symbols requested." });\n    const rt33sQ = await yahooQuote(symbols);\n    rt33sYqStore(rt33sQ);\n    return json(res, 200, rt33sQ);'
okA = part('A+B yahoo-quote per-client limiter + last-good cache', A1, A1n)
part('A yahoo-chart per-client limiter', '    const clientAddress = req.socket?.remoteAddress || "unknown";\n    if (!yahooChartRateLimiter.allow(clientAddress)) {', '    const clientAddress = rt33sIp(req);\n    if (!yahooChartRateLimiter.allow(clientAddress)) {')
part('C chart limit 90/min', 'const yahooChartRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });', 'const yahooChartRateLimiter = new FixedWindowRateLimiter({ limit: 90, windowMs: 60_000, maxKeys: 1024 });')
part('A quote limiter key space', 'const yahooRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 256 });', 'const yahooRateLimiter = new FixedWindowRateLimiter({ limit: 30, windowMs: 60_000, maxKeys: 1024 });')
part('D coingecko per-client limiter', '!coinGeckoRateLimiter.allow(req.socket?.remoteAddress || "unknown")) return fallback(res, path);', '!coinGeckoRateLimiter.allow(rt33sIp(req))) return rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback);')
part('D coingecko cold miss -> original last-good', '      catch { return fallback(res, path); }', '      catch { return rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback); }')
part('E fundamentals: reject crypto, slim per path', 'if (["/api/financials", "/api/earnings", "/api/statements", "/api/holders"].includes(p)) return rt32Fundamentals(req, res, p, url);',
  'if (p === "/terms" || p === "/terms/" || p === "/privacy" || p === "/privacy/") return rt33sLegal(res, p);\n  if (["/api/financials", "/api/earnings", "/api/statements", "/api/holders"].includes(p)) return rt33sFund(req, res, p, url);')
part('F brief date = today (London)', 'return json(res, 200, { brief: result.validated || validateBriefResponse(result.text), cached: false,', 'return json(res, 200, { brief: rt33sBriefDate(result.validated || validateBriefResponse(result.text)), cached: false,')
if not applied: print('Nothing to change; server.js left as is.'); [print('SKIP ', k) for k in skipped]; sys.exit(0)
s = s.rstrip('\n') + r'''

// rt33s: per-client Yahoo limiter key + last-good quote cache
function rt33sIp(req) {
  try {
    const xf = String(req.headers["x-forwarded-for"] || "").split(",").map(x => x.trim()).filter(Boolean);
    return xf.length ? xf[xf.length - 1] : (req.socket?.remoteAddress || "unknown");
  } catch { return req.socket?.remoteAddress || "unknown"; }
}
const rt33sYq = new Map();
function rt33sYqStore(q) {
  try {
    if (!q || typeof q !== "object") return;
    const at = Date.now();
    for (const [k, v] of Object.entries(q)) if (v && typeof v.p === "number" && v.p > 0) rt33sYq.set(k, { v, at });
    while (rt33sYq.size > 2000) rt33sYq.delete(rt33sYq.keys().next().value);
  } catch {}
}
function rt33sYqCached(raw) {
  const out = {};
  try {
    for (const k of String(raw).split(",").map(x => x.trim()).filter(Boolean).slice(0, 200)) {
      const e = rt33sYq.get(k);
      if (e && Date.now() - e.at < 15 * 60_000) out[k] = { ...e.v, cached: true };
    }
  } catch {}
  return out;
}
function rt33sCgMiss(req, res, rawPath, path, original, fresh, fam, famKey, fallback) {
  // rt29s only kept in-memory copies; a fresh instance has none, so a 429 became {unavailable}. Prefer any
  // in-memory copy (< 24h), else let the original handler answer from its own persisted last-good copy.
  try { const g = fresh.get(path) || fam.get(famKey(path)); if (g && Date.now() - g.at < 24 * 3600_000) return fallback(res, path); } catch {}
  try { return original(req, res, rawPath); } catch { return fallback(res, path); }
}
const RT33S_CRYPTO = new Set(["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX","DOT","LINK","MATIC","POL","LTC","BCH","XLM","ATOM","NEAR","ALGO","HBAR","FIL","APT","SUI","INJ","SHIB","PEPE","UNI","TON","TRX","BNB","ARB","OP","ETC","XMR","ICP","AAVE","MKR"]);
async function rt33sFund(req, res, p, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  const empty = reason => ({ symbol: sym, unavailable: true, reason, data: [], earnings: [], holders: [], history: [] });
  if (RT33S_CRYPTO.has(sym) || /-USD$/.test(sym)) return json(res, 200, empty("crypto asset: company fundamentals do not apply"));
  if (p === "/api/financials" || typeof rt32Build !== "function" || typeof RT32 === "undefined") return rt32Fundamentals(req, res, p, url);
  if (!/^[A-Z0-9][A-Z0-9.\-]{0,9}$/.test(sym)) return json(res, 200, empty("bad symbol"));
  let data = null; const hit = RT32.cache.get(sym);
  if (hit && Date.now() - hit.at < 12 * 3600e3) data = hit.data;
  else {
    try {
      if (!RT32.inflight.has(sym)) RT32.inflight.set(sym, rt32Build(sym).finally(() => RT32.inflight.delete(sym)));
      data = await RT32.inflight.get(sym);
      if (data.financials || data.valuation || data.earnings || data.institutions) RT32.cache.set(sym, { at: Date.now(), data });
    } catch (e) { data = hit ? hit.data : null; }
  }
  if (!data) return json(res, 200, empty("source error"));
  const base = { symbol: sym, asOf: data.asOf, sources: data.sources };
  if (p === "/api/earnings") return json(res, 200, { ...base, earnings: data.earnings, history: data.history || [], nextEarnings: data.nextEarnings || null, beatRate: data.beatRate, avgSurprise: data.avgSurprise });
  if (p === "/api/holders") return json(res, 200, { ...base, institutions: data.institutions, holders: data.holders || [] });
  return json(res, 200, { ...base, financials: data.financials, data: [] });
}
function rt33sBriefDate(b) {
  try { if (b && typeof b === "object") b.date = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date()); } catch {}
  return b;
}
function rt33sLegal(res, p) {
  const terms = /terms/.test(p);
  const title = terms ? "Terms of Use" : "Privacy Notice";
  const body = terms
    ? "<p>The Dispatch Markets (thedispatch.uk) publishes market research and data for information only. Nothing on this site is investment advice or a recommendation to buy or sell any security. Prices come from free third-party feeds and may be delayed or incomplete.</p><p>Premium is a monthly subscription billed through Stripe. You can cancel at any time from Manage billing; access continues to the end of the paid period.</p><p>You may not scrape, resell or redistribute site content or data. We may change or withdraw features at any time.</p><p>Questions: <a href=\"mailto:support@thedispatch.uk\">support@thedispatch.uk</a></p>"
    : "<p>We collect only what we need to run the service: your email address and account settings when you register, and your subscription status from Stripe if you subscribe. Card details are handled by Stripe and never reach our servers.</p><p>Watchlists, alerts and display settings are stored in your browser; signed-in settings may also be saved to your account. We use essential cookies for sign-in only, and no advertising trackers.</p><p>You can ask us to export or delete your data at any time.</p><p>Contact: <a href=\"mailto:support@thedispatch.uk\">support@thedispatch.uk</a></p>";
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} | The Dispatch Markets</title><link rel="canonical" href="https://thedispatch.uk${terms ? "/terms" : "/privacy"}"><style>body{margin:0;background:#0d1016;color:#d8dde6;font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}main{max-width:720px;margin:0 auto;padding:40px 20px}h1{font-size:28px;margin:0 0 6px}a{color:#e5b453}.k{font:12px ui-monospace,monospace;letter-spacing:.12em;color:#8a94a6}</style></head><body><main><div class="k">THE DISPATCH MARKETS</div><h1>${title}</h1>${body}<p><a href="/">← Back to The Dispatch</a></p></main></body></html>`;
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600" });
  res.end(html);
}
'''
for a in applied: print('APPLY', a)
for k in skipped: print('SKIP ', k)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed, nothing written:', r.stderr[:300]); sys.exit(1)
print('node --check passed' + (' (dry run, nothing written)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
