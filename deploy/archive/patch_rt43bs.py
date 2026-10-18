#!/usr/bin/env python3
"""patch_rt43bs.py (server, pairs with client patch_rt43b.py chat40->chat41). Requires rt43s.
A route   /api/ext-hours (US pre-market / after-hours prints, 60 s shared cache) next to /api/spot-energy (safe-skip)
P /pricing: admin note no longer mentions Manage billing (it is hidden for admin); subscribers still pointed to Settings
B append  /api/spot-energy diagnostics: Twelve Data error code in "reason" (key never echoed), key trimmed,
          2-minute backoff after a failure, partial results kept; rt43bExt handler
Usage: python3 patch_rt43bs.py [--check] path/to/server.js"""
import sys, os, subprocess, shutil
BLOCK = r'''// rt43b: Twelve Data energy diagnostics (non-secret reason codes)
try { if (typeof rt43sEnergyFetch === "function" && typeof rt43sEnergy === "function" && typeof RT43S_EN === "object") {
  RT43S_EN.err = null;
  const rt43bClean = (m, key) => String(m || "").split(key || "\u0000").join("***").replace(/apikey=[^&\s]+/gi, "apikey=***").replace(/[^\w .,:/'()-]/g, "").slice(0, 140);
  rt43sEnergyFetch = async function () {
    const key = String(process.env.TWELVE_DATA_API_KEY || "").trim();
    if (!key) { RT43S_EN.err = "no-key"; return null; }
    let r, j;
    try { r = await fetch(`https://api.twelvedata.com/quote?symbol=${encodeURIComponent("WTI/USD,XBR/USD")}&apikey=${encodeURIComponent(key)}`, { signal: AbortSignal.timeout(8000), headers: { accept: "application/json" } }); }
    catch (e) { RT43S_EN.err = "td-network-" + (e && e.name === "TimeoutError" ? "timeout" : "error"); return null; }
    if (!r.ok) { RT43S_EN.err = "td-http-" + r.status; return null; }
    try { j = await r.json(); } catch (e) { RT43S_EN.err = "td-bad-json"; return null; }
    if (j && j.status === "error") { RT43S_EN.err = `td-${j.code || "error"}: ${rt43bClean(j.message, key)}`; return null; }
    const errs = [];
    const one = (sym, name) => { const q = j && j[sym];
      if (!q) { errs.push(sym + " missing"); return null; }
      if (q.status === "error") { errs.push(`${sym} td-${q.code || "error"}: ${rt43bClean(q.message, key)}`); return null; }
      const p = Number(q.close), prev = Number(q.previous_close), ts = Number(q.last_quote_at || q.timestamp);
      if (!(p > 0)) { errs.push(sym + " no-price"); return null; }
      return { p, prev: prev > 0 ? prev : null, c: prev > 0 ? ((p - prev) / prev) * 100 : null, ts: ts > 0 ? ts : Math.floor(Date.now() / 1000), name, source: "twelve-spot", proxy: true }; };
    const out = { WTI: one("WTI/USD", "WTI crude spot"), BRENT: one("XBR/USD", "Brent crude spot") };
    RT43S_EN.err = errs.length ? errs.join(" | ") : null;
    return out;
  };
  rt43sEnergy = async function (res) {
    const now = Date.now(), day = new Date().toISOString().slice(0, 10);
    if (RT43S_EN.day !== day) { RT43S_EN.day = day; RT43S_EN.used = 0; }
    const budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));
    const left = budget - RT43S_EN.used;
    const msLeft = Date.parse(day + "T24:00:00Z") - now;
    const interval = left >= 2 ? Math.max(60_000, Math.floor(msLeft / (left / 2))) : Infinity;
    if (!String(process.env.TWELVE_DATA_API_KEY || "").trim()) return json(res, 200, { available: false, reason: "no-key" }, { "Cache-Control": "no-store" });
    // after a failure, retry no faster than every 2 min so errors don't burn the shared 8/min, 800/day free limits
    const due = RT43S_EN.data ? now - RT43S_EN.at >= interval : now - (RT43S_EN.failAt || 0) >= 120_000;
    if (due && !RT43S_EN.inflight && left >= 2) {
      RT43S_EN.inflight = rt43sEnergyFetch().then(d => { RT43S_EN.used += 2; if (d && (d.WTI || d.BRENT)) { RT43S_EN.data = d; RT43S_EN.at = Date.now(); } else RT43S_EN.failAt = Date.now(); })
        .catch(e => { RT43S_EN.used += 2; RT43S_EN.failAt = Date.now(); RT43S_EN.err = "td-exception"; }).finally(() => { RT43S_EN.inflight = null; });
      await Promise.race([RT43S_EN.inflight, new Promise(r => setTimeout(r, 6000))]);
    }
    const d = RT43S_EN.data;
    if (!d) return json(res, 200, { available: false, reason: left < 2 ? "budget" : RT43S_EN.inflight ? "pending" : (RT43S_EN.err || "unavailable"), retryInSec: Math.max(0, Math.round((120_000 - (Date.now() - (RT43S_EN.failAt || 0))) / 1000)) }, { "Cache-Control": "no-store" });
    const ageSec = Math.round((Date.now() - RT43S_EN.at) / 1000);
    const stale = ageSec > Math.max(180, (isFinite(interval) ? interval / 1000 : 0) * 3);
    return json(res, 200, { available: true, WTI: d.WTI && { ...d.WTI, stale }, BRENT: d.BRENT && { ...d.BRENT, stale }, fetchedAt: RT43S_EN.at, ageSec, refreshSec: isFinite(interval) ? Math.round(interval / 1000) : null, ...(RT43S_EN.err ? { partial: RT43S_EN.err } : {}) }, { "Cache-Control": "public, max-age=30" });
  };
} } catch (e) { console.warn("rt43b skipped:", e && e.message); }

// rt43b: US pre-market / after-hours prints (Yahoo v7 quote with the rt32 crumb), 60 s shared cache
const RT43B_EXT = new Map(); let RT43B_EXT_P = null;
async function rt43bExtFetch(syms) {
  for (let i = 0; i < 2; i++) {
    const crumb = await rt32Crumb(i > 0);
    const r = await rt32Get(`https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(syms.join(","))}&fields=preMarketPrice,preMarketTime,postMarketPrice,postMarketTime,marketState,regularMarketPrice&crumb=${encodeURIComponent(crumb)}`, { "User-Agent": RT32_BUA, Cookie: RT32.ck });
    if (r.status === 401 || r.status === 403) continue;
    if (!r.ok) throw new Error("yahoo " + r.status);
    const j = await r.json(), now = Date.now();
    const rows = (j && j.quoteResponse && j.quoteResponse.result) || [];
    if (RT43B_EXT.size > 3000) RT43B_EXT.clear();
    syms.forEach(s => RT43B_EXT.set(s, { at: now, v: null }));
    rows.forEach(q => { if (!q || !q.symbol) return; RT43B_EXT.set(String(q.symbol).toUpperCase(), { at: now, v: { state: String(q.marketState || ""), pre: Number(q.preMarketPrice) || null, preTs: Number(q.preMarketTime) || null, post: Number(q.postMarketPrice) || null, postTs: Number(q.postMarketTime) || null, reg: Number(q.regularMarketPrice) || null } }); });
    return;
  }
  throw new Error("yahoo auth");
}
async function rt43bExt(req, res) {
  let syms = [];
  try { syms = [...new Set(String(new URL(req.url, "http://localhost").searchParams.get("symbols") || "").toUpperCase().split(",").map(s => s.trim()).filter(s => /^[A-Z][A-Z.\-]{0,6}$/.test(s)))].slice(0, 60); } catch {}
  if (!syms.length) return json(res, 400, { available: false, reason: "symbols" }, { "Cache-Control": "no-store" });
  if (typeof rt32Crumb !== "function" || typeof rt32Get !== "function") return json(res, 200, { available: false, reason: "no-crumb" }, { "Cache-Control": "no-store" });
  const need = syms.filter(s => { const c = RT43B_EXT.get(s); return !c || Date.now() - c.at > 60_000; });
  let reason = null;
  if (need.length) {
    try { if (!RT43B_EXT_P) RT43B_EXT_P = rt43bExtFetch(need).finally(() => { RT43B_EXT_P = null; }); await RT43B_EXT_P; }
    catch (e) { reason = "yahoo-" + String(e && e.message || "error").replace(/[^\w -]/g, "").slice(0, 40); }
  }
  const quotes = {}; syms.forEach(s => { const c = RT43B_EXT.get(s); if (c && c.v) quotes[s] = c.v; });
  return json(res, 200, { available: Object.keys(quotes).length > 0, quotes, ...(reason ? { reason } : {}) }, { "Cache-Control": "public, max-age=30" });
}
'''
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// rt43b:" in s: sys.exit("REFUSE: rt43b already applied")
need = ["// rt43s: pricing, shared energy", "async function rt43sEnergyFetch(", "async function rt43sEnergy(res)", "const RT43S_EN = {"]
miss = [n for n in need if s.count(n) != 1]
if miss: sys.exit("REFUSE: rt43s anchors missing/duplicated: %r" % miss)
RA = '      if (rp === "/api/spot-energy") return rt43sEnergy(res);\n'
if s.count(RA) == 1:
    s = s.replace(RA, RA + '      if (rp === "/api/ext-hours") return rt43bExt(req, res); // rt43b: extended-hours prints\n'); print("A applied: /api/ext-hours route")
else: print("A SKIPPED: spot-energy route anchor matched %d times (ext-hours line will not show)" % s.count(RA))
PA = '${user.billingPortal ? `Manage billing from <a href="/settings/">Settings</a>.` : ""}'
if s.count(PA) == 1:
    s = s.replace(PA, '${!admin ? `Manage billing from <a href="/settings/">Settings</a>.` : "There is no Stripe subscription on an admin account."}'); print("P applied: /pricing admin note")
else: print("P SKIPPED: pricing note anchor matched %d times" % s.count(PA))
out = s.rstrip("\n") + "\n\n" + BLOCK.strip("\n") + "\n"
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt43b.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt43bs would apply (node --check passed)"); sys.exit(0)
shutil.copy(p, p + ".bak-rt43b"); os.replace(tmp, p); print("APPLIED rt43bs; backup at", p + ".bak-rt43b")
