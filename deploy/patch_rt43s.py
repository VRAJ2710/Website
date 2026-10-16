#!/usr/bin/env python3
"""patch_rt43s.py: server, stacks on production server.js 1ac7dc4e + rt42b.
A  routes at the top of handle(), inserted just before the rt42b ticker-redirect block (SAFE-SKIP if not found once):
   /upgrade -> 302 /pricing ; /pricing (Free vs Premium £15/month) ; /api/spot-energy (WTI/Brent spot, Twelve Data,
   one shared server cache, paced to a daily credit budget)
T  Terms: states £15/month (exact rt33s sentence; SAFE-SKIP)
S  Subscribe page feature sentence aligned with /pricing (SAFE-SKIP)
B  appended monkeypatches (each guarded with typeof; skipped if the helper is absent):
   gold reference cache 30s; last-good gold/DXY copies marked stale:true with staleAgeSec, never fresh;
   synthetic DXY from Yahoo's live FX pairs (ICE weights), ECB/frankfurter no longer used for display;
   Yahoo last-good / rate-limited cache copies marked stale:true + staleAgeSec;
   Ask peer block: never compare trailing P/E with forward P/E.
Usage: python3 patch_rt43s.py [--check] server.js"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt43s:' in s: print('ABORT: rt43s already applied'); sys.exit(1)
if 'rt41s:' not in s: print('ABORT: rt41s not present'); sys.exit(1)
ROUTES = '''  { // rt43s: pricing page, /upgrade, shared energy spot
    let rp = ""; try { rp = new URL(req.url, "http://localhost").pathname; } catch {}
    if (req.method === "GET" || req.method === "HEAD") {
      if (rp === "/upgrade" || rp === "/upgrade/") { res.writeHead(302, { Location: "/pricing" }); return res.end(); }
      if (rp === "/pricing" || rp === "/pricing/") return rt43sPricing(req, res);
      if (rp === "/api/spot-energy") return rt43sEnergy(res);
    }
  }
'''
done = False
for anchor in ['  { // rt42b: pretty ticker URLs -> the markets deep link\n', '  { // rt42s: pretty ticker URLs -> the markets deep link\n']:
    n = s.count(anchor)
    if n == 1:
        s = s.replace(anchor, ROUTES + anchor); done = True; print('APPLY A routes (/pricing, /upgrade, /api/spot-energy)'); break
if not done: print('SKIP  A routes (rt42b/rt42s anchor not found once): /pricing, /upgrade, /api/spot-energy NOT added')
T_OLD = '<p>Premium is a monthly subscription billed through Stripe.'
T_NEW = '<p>Premium costs £15 per month, billed monthly through Stripe.'
n = s.count(T_OLD)
if n == 1: s = s.replace(T_OLD, T_NEW); print('APPLY T terms £15/month')
else: print(f'SKIP  T terms (anchor matched {n}x)')
S_OLD = 'Continue to Stripe Checkout to unlock AI briefs, lenses, portfolio analysis, and Dispatch Expert.'
S_NEW = 'Continue to Stripe Checkout to unlock the weekly Gold Playbook, the AI Dispatch Brief, Ask and AI lenses, company statements and institutional holders. <a href="/pricing">Compare plans</a>.'
n = s.count(S_OLD)
if n == 1: s = s.replace(S_OLD, S_NEW); print('APPLY S subscribe copy')
else: print(f'SKIP  S subscribe copy (anchor matched {n}x)')
B = r'''
// rt43s: pricing, shared energy spot, honest reference/last-good marking, synthetic DXY from live FX
const RT43S_FREE = ["Live and delayed market prices with charts", "Markets, crypto, newsroom and heatmaps", "Regime model and the free desk brief", "Market Lab, Desk Run and the Letter", "Watchlists and price alerts"];
const RT43S_PREM = ["Everything in Free", "Weekly Gold Playbook", "AI Dispatch Brief", "Ask research assistant and AI lenses", "Company statements and institutional holders", "Custom screener and document intelligence", "Cancel any time from Manage billing"];
async function rt43sPricing(req, res) {
  let user = null; try { user = await currentUser(req); } catch {}
  const admin = (() => { try { return isAdminUser(user); } catch { return false; } })();
  const prem = !!user && (user.tier === "premium" || admin);
  const li = a => a.map(x => `<li>${x}</li>`).join("");
  const cta = prem
    ? `<p class="muted">${admin ? "Admin · Premium included." : "Premium active."} ${user.billingPortal ? `Manage billing from <a href="/settings/">Settings</a>.` : ""}</p>`
    : `${user ? "" : `<a href="/__auth/register">Create free account</a> · `}<a href="/__auth/subscribe">Get Premium · £15/month</a>`;
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  if (req.method === "HEAD") return res.end();
  return res.end(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pricing · The Dispatch</title>
<meta name="description" content="The Dispatch Markets: Free and Premium (£15/month) plans.">
<style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px/1.5 system-ui}main{max-width:860px;margin:0 auto;padding:32px 20px}
h1{font-size:28px;margin:0 0 6px}.g{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}@media(max-width:640px){.g{grid-template-columns:1fr}}
.c{background:#111a26;border:1px solid #293849;border-radius:14px;padding:22px}.c.p{border-color:#c9a227}h2{margin:0 0 4px;font-size:20px}.pr{font-size:26px;font-weight:800;margin:6px 0 10px}
ul{padding-left:18px;margin:0}li{margin:6px 0}a{color:#e7c35a}.muted{color:#93a1b3;font-size:14px}</style></head><body><main>
<a href="/">← The Dispatch</a><h1>Pricing</h1><p class="muted">One plan upgrade, no token mark-up. Prices in GBP, billed monthly through Stripe.</p>
<div class="g"><section class="c"><h2>Free</h2><div class="pr">£0</div><ul>${li(RT43S_FREE)}</ul></section>
<section class="c p"><h2>Premium</h2><div class="pr">£15/month</div><ul>${li(RT43S_PREM)}</ul></section></div>
<p>${cta}</p><p class="muted">Research and data for information only; not investment advice. See the <a href="/terms">Terms</a> and <a href="/privacy">Privacy notice</a>.</p>
</main></body></html>`);
}
const RT43S_EN = { at: 0, data: null, day: "", used: 0, inflight: null };
async function rt43sEnergyFetch() {
  const key = process.env.TWELVE_DATA_API_KEY;
  if (!key) return null;
  const r = await fetch(`https://api.twelvedata.com/quote?symbol=${encodeURIComponent("WTI/USD,XBR/USD")}&apikey=${encodeURIComponent(key)}`, { signal: AbortSignal.timeout(8000), headers: { accept: "application/json" } });
  if (!r.ok) throw new Error("twelve " + r.status);
  const j = await r.json();
  const one = (q, name) => { const p = Number(q && q.close), prev = Number(q && q.previous_close), ts = Number(q && (q.last_quote_at || q.timestamp));
    return p > 0 ? { p, prev: prev > 0 ? prev : null, c: prev > 0 ? ((p - prev) / prev) * 100 : null, ts: ts > 0 ? ts : Math.floor(Date.now() / 1000), name, source: "twelve-spot", proxy: true } : null; };
  return { WTI: one(j["WTI/USD"], "WTI crude spot"), BRENT: one(j["XBR/USD"], "Brent crude spot") };
}
async function rt43sEnergy(res) {
  const now = Date.now(), day = new Date().toISOString().slice(0, 10);
  if (RT43S_EN.day !== day) { RT43S_EN.day = day; RT43S_EN.used = 0; }
  const budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));
  const left = budget - RT43S_EN.used;
  const msLeft = Date.parse(day + "T24:00:00Z") - now;
  const interval = left >= 2 ? Math.max(60_000, Math.floor(msLeft / (left / 2))) : Infinity;
  if (!process.env.TWELVE_DATA_API_KEY) return json(res, 200, { available: false, reason: "no-key" }, { "Cache-Control": "no-store" });
  if ((!RT43S_EN.data || now - RT43S_EN.at >= interval) && !RT43S_EN.inflight && left >= 2) {
    RT43S_EN.inflight = rt43sEnergyFetch().then(d => { RT43S_EN.used += 2; if (d && (d.WTI || d.BRENT)) { RT43S_EN.data = d; RT43S_EN.at = Date.now(); } }).catch(() => { RT43S_EN.used += 2; }).finally(() => { RT43S_EN.inflight = null; });
    await Promise.race([RT43S_EN.inflight, new Promise(r => setTimeout(r, 6000))]);
  }
  const d = RT43S_EN.data;
  if (!d) return json(res, 200, { available: false, reason: left < 2 ? "budget" : "unavailable" }, { "Cache-Control": "no-store" });
  const ageSec = Math.round((Date.now() - RT43S_EN.at) / 1000);
  const stale = ageSec > Math.max(180, (isFinite(interval) ? interval / 1000 : 0) * 3);
  return json(res, 200, { available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null }, { "Cache-Control": "public, max-age=30" });
}
const rt43sAge = ts => { const t = Number(ts); return t > 0 ? Math.max(0, Math.round(Date.now() / 1000 - (t > 1e10 ? t / 1000 : t))) : null; };
try {
  if (typeof fetchGoldProxy === "function") {
    const g = { at: 0, q: null };
    fetchGoldProxy = async function () {
      if (g.q && Date.now() - g.at < 30_000) return { ...g.q, cached: true };
      try {
        const r = await fetch("https://api.gold-api.com/price/XAU", { signal: AbortSignal.timeout(6000), headers: { accept: "application/json" } });
        if (!r.ok) throw new Error("gold " + r.status);
        const d = await r.json(); const price = Number(d && d.price), ts = Date.parse((d && d.updatedAt) || "");
        if (!(price > 0)) throw new Error("gold invalid");
        const q = { p: price, c: 0, prev: price, change: 0, currency: "USD", exchange: "FREE REFERENCE", name: "Spot Gold (proxy)", ts: Number.isFinite(ts) ? Math.floor(ts / 1000) : Math.floor(Date.now() / 1000), source: "gold-api-spot-proxy", proxy: true };
        g.q = q; g.at = Date.now(); try { rememberReferenceQuote("spot-gold-proxy", q); } catch {}
        return q;
      } catch {
        let lg = g.q; try { lg = lg || lastGoodReferenceQuote("spot-gold-proxy"); } catch {}
        return lg ? { ...lg, cached: true, stale: true, staleAgeSec: rt43sAge(lg.ts) } : null;
      }
    };
  }
  if (typeof fetchSyntheticDxy === "function" && typeof fetchYahooQuote === "function") {
    const W = [["EURUSD=X", -0.576, true], ["JPY=X", 0.136, false], ["GBPUSD=X", -0.119, true], ["CAD=X", 0.091, false], ["SEK=X", 0.042, false], ["CHF=X", 0.036, false]];
    const d = { at: 0, q: null };
    fetchSyntheticDxy = async function () {
      if (d.q && Date.now() - d.at < 30_000) return { ...d.q, cached: true };
      try {
        const qs = await Promise.all(W.map(([s]) => fetchYahooQuote(s).catch(() => null)));
        if (qs.some(q => !q || !(q.p > 0) || /last-good/.test(String(q.source || "")))) throw new Error("fx incomplete");
        const idx = k => 50.14348112 * W.reduce((m, [, e], i) => m * (qs[i][k] ** e), 1);
        const p = idx("p"); const prevOk = qs.every(q => q.prev > 0); const prev = prevOk ? 50.14348112 * W.reduce((m, [, e], i) => m * (qs[i].prev ** e), 1) : null;
        const ts = Math.min(...qs.map(q => Number(q.ts) > 1e10 ? Number(q.ts) / 1000 : Number(q.ts) || Date.now() / 1000));
        const q = { p: Number(p.toFixed(3)), prev: prev ? Number(prev.toFixed(3)) : null, c: prev ? ((p - prev) / prev) * 100 : null, change: prev ? p - prev : null, currency: "USD", exchange: "SYNTHETIC", name: "US Dollar Index (computed from live FX)", ts: Math.floor(ts), source: "dxy-fx-computed", proxy: true };
        d.q = q; d.at = Date.now(); try { rememberReferenceQuote("synthetic-dxy-proxy", q); } catch {}
        return q;
      } catch {
        return d.q ? { ...d.q, cached: true, stale: true, staleAgeSec: rt43sAge(d.q.ts) } : null;
      }
    };
  }
  const rt43sMark = out => { try { for (const k of Object.keys(out || {})) { const q = out[k]; if (q && typeof q === "object" && (q.cached || /last-good/.test(String(q.source || ""))) && /last-good/.test(String(q.source || "")) ) { q.stale = true; q.staleAgeSec = rt43sAge(q.ts); } } } catch {} return out; };
  if (typeof yahooQuote === "function") { const yq0 = yahooQuote; yahooQuote = async function (...a) { return rt43sMark(await yq0.apply(this, a)); }; }
  if (typeof rt33sYqCached === "function") { const yc0 = rt33sYqCached; rt33sYqCached = function (...a) { const out = yc0.apply(this, a); try { for (const k of Object.keys(out || {})) { const q = out[k]; if (q && typeof q === "object") { q.stale = true; q.cached = true; q.staleAgeSec = rt43sAge(q.ts); } } } catch {} return out; }; }
  if (typeof rt41sPeerBlock === "function") { const pb0 = rt41sPeerBlock; rt41sPeerBlock = async function (...a) { const v = await pb0.apply(this, a); return v ? v + "\nCompare like with like: trailing P/E with trailing P/E, forward P/E with forward P/E. Never compare one company's trailing P/E with another company's forward P/E; if a figure is n/a, say so for that company only." : v; }; }
} catch (e) { console.warn("rt43s monkeypatch skipped"); }
'''
s = s.rstrip('\n') + '\n' + B
print('APPLY B appended monkeypatches')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed', r.stderr[:500]); sys.exit(1)
print('node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
