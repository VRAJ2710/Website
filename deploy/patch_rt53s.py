#!/usr/bin/env python3
"""patch_rt53s.py (server only): GET /api/real-yield -> FRED DFII10, the US 10-year real yield.

Keyless CSV (https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10). The browser cannot
read it: FRED sends no Access-Control-Allow-Origin. Cached in memory for about 6 hours.
No new table, no key, no Stripe.

Refuses if this route is already present. The anchor is the rt44 EIA route, which is on the
live server and not in the August repo snapshot. Usage: python3 patch_rt53s.py [--check] server.js"""
import sys, os, subprocess, shutil
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// ── rt53s ──" in s or 'rp === "/api/real-yield"' in s: sys.exit("REFUSE: rt53s already applied")
ANC = 'if (rp === "/api/eia-spot") return rt44Eia(res);'
if s.count(ANC) != 1: print("SKIPPED: eia-spot anchor matched %d times; nothing changed" % s.count(ANC)); sys.exit(0)
if "function json(res" not in s: print("SKIPPED: json() helper missing; nothing changed"); sys.exit(0)
BLOCK = r'''
// ── rt53s ── US 10-year real yield, FRED series DFII10 (a daily Treasury print). Keyless CSV, memory only.
const RT53_RY = { at: 0, tryAt: 0, v: null, p: null, reason: "" };
async function rt53RyFetch() {
  const r = await fetch("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10", { headers: { "User-Agent": "Mozilla/5.0 (thedispatch.uk reference fetch)", Accept: "text/csv,*/*" }, signal: AbortSignal.timeout(12000) });
  if (!r.ok) throw new Error("http " + r.status);
  const rows = (await r.text()).trim().split(/\r?\n/).slice(1).map(l => l.split(",")).filter(x => x[0] && isFinite(Number(x[1])) && x[1] !== ".");
  const a = rows[rows.length - 1], b = rows[rows.length - 2];
  if (!a) throw new Error("empty");
  const value = Math.round(Number(a[1]) * 100) / 100;
  const prev = b ? Math.round(Number(b[1]) * 100) / 100 : null;
  RT53_RY.v = { available: true, value, prev, change: prev == null ? null : Math.round((value - prev) * 100) / 100, date: a[0], source: "US Treasury via FRED", series: "DFII10" };
  RT53_RY.at = Date.now(); RT53_RY.reason = "";
}
async function rt53RealYield(res) {
  const now = Date.now();
  if ((!RT53_RY.v || now - RT53_RY.at > 6 * 3600e3) && now - RT53_RY.tryAt > 15 * 60e3) {
    RT53_RY.tryAt = now;
    if (!RT53_RY.p) RT53_RY.p = rt53RyFetch().catch(e => { RT53_RY.reason = String(e && e.message || "error").replace(/[^\w .-]/g, "").slice(0, 80); }).finally(() => { RT53_RY.p = null; });
  }
  if (RT53_RY.p && !RT53_RY.v) { try { await RT53_RY.p; } catch (e) {} }
  if (!RT53_RY.v) return json(res, 200, { available: false, reason: RT53_RY.reason || "pending" }, { "Cache-Control": "no-store" });
  return json(res, 200, Object.assign({ fetchedAt: new Date(RT53_RY.at).toISOString() }, RT53_RY.v), { "Cache-Control": "public, max-age=900" });
}
'''
out = s.replace(ANC, 'if (rp === "/api/real-yield") return rt53RealYield(res);\n      ' + ANC, 1)
out = out.rstrip("\n") + "\n" + BLOCK
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt53s.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt53s would apply"); sys.exit(0)
shutil.copy(p, p + ".bak-rt53s"); os.replace(tmp, p); print("APPLIED rt53s; backup at", p + ".bak-rt53s")
