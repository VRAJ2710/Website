#!/usr/bin/env python3
"""patch_rt43d.py (server only). Requires rt43s (+ rt43b/rt43c if present). Append + monkeypatch.
/api/spot-energy answers {available:false, reason:"not-on-plan"} instantly with no Twelve Data call unless
RT43D_TD_ENERGY=1. Because the energy fetch is never reached, rt43c's shared-slot claims never touch the core row;
any basket trim rt43c managed is undone, so the core Twelve Data feed behaves exactly as before rt43c.
Usage: python3 patch_rt43d.py [--check] path/to/server.js"""
import sys, os, subprocess, shutil
BLOCK = r'''// rt43d: Twelve Data energy spot is not on the free plan (td-403 for WTI/USD and XBR/USD): no energy calls at all
// unless RT43D_TD_ENERGY=1, and the core basket exactly as before rt43c (basket restored; no energy credit claims)
try {
  if (typeof RT43C === "object" && RT43C && Array.isArray(RT43C.dropped) && RT43C.dropped.length && typeof twelveDataAllowedSymbols !== "undefined" && !Object.isFrozen(twelveDataAllowedSymbols)) {
    for (const s of RT43C.dropped) if (!twelveDataAllowedSymbols.includes(s)) twelveDataAllowedSymbols.push(s);
    console.log("rt43d: core basket restored to", twelveDataAllowedSymbols.length, "symbols");
    RT43C.dropped = []; RT43C.trimmed = false;
  }
} catch (e) { console.warn("rt43d basket restore skipped:", e && e.message); }
try { if (typeof rt43sEnergy === "function") {
  const _en0 = rt43sEnergy;
  rt43sEnergy = async function (res) {
    if (String(process.env.RT43D_TD_ENERGY || "") === "1") return _en0.apply(this, arguments);
    return json(res, 200, { available: false, reason: "not-on-plan", detail: "WTI and Brent spot are not on the free Twelve Data plan; the 10-minute-delayed NYMEX/ICE futures are shown instead." }, { "Cache-Control": "public, max-age=3600" });
  };
} } catch (e) { console.warn("rt43d energy gate skipped:", e && e.message); }
'''
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// rt43d:" in s: sys.exit("REFUSE: rt43d already applied")
if s.count("async function rt43sEnergy(res)") != 1: sys.exit("REFUSE: rt43s energy handler not found")
out = s.rstrip("\n") + "\n\n" + BLOCK.strip("\n") + "\n"
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt43d.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt43d would apply (append, node --check passed)"); sys.exit(0)
shutil.copy(p, p + ".bak-rt43d"); os.replace(tmp, p); print("APPLIED rt43d; backup at", p + ".bak-rt43d")
