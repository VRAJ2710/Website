#!/usr/bin/env python3
"""patch_rt43c.py (server only). Requires rt43s + rt43bs. Append + monkeypatch.
Shared Twelve Data credit budget: trims the core basket's FX legs (Yahoo streams them live) and schedules
/api/spot-energy (WTI/USD, XBR/USD) through the core basket's own coordination row (8/min, 800/day minus margin,
with the core's worst-case need for the rest of the day reserved). Honest fallback unchanged.
Env: RT43C_TD_BASKET_DROP (default "EUR/USD,GBP/USD,USD/JPY"; "" keeps the basket), RT43C_TD_MINUTE_LIMIT (8),
RT43C_TD_DAILY_MARGIN (20), RT43_TD_ENERGY_DAILY (300, from rt43s).
Usage: python3 patch_rt43c.py [--check] path/to/server.js"""
import sys, os, subprocess, shutil
BLOCK = r'''// rt43c: one shared Twelve Data credit budget for the core basket and energy spot
// Core basket refreshes cost one credit per symbol per 15-minute cache miss; the free plan allows 8/min and 800/day.
// 1) the FX legs Yahoo already streams live leave the basket (RT43C_TD_BASKET_DROP; "" keeps all)
// 2) energy (2 credits) is claimed from the SAME coordination row the core basket uses, only in a minute the core
//    is not about to use, and only if the core's worst-case need for the rest of the 24h window still fits
const RT43C = { trimmed: false, dropped: [], coreCost: 0, lastTry: 0, lastClaim: null, reason: "" };
try {
  const drop = String(process.env.RT43C_TD_BASKET_DROP ?? "EUR/USD,GBP/USD,USD/JPY").split(",").map(s => s.trim()).filter(Boolean);
  if (typeof twelveDataAllowedSymbols !== "undefined" && Array.isArray(twelveDataAllowedSymbols)) {
    if (!Object.isFrozen(twelveDataAllowedSymbols)) {
      for (const s of drop) { const i = twelveDataAllowedSymbols.indexOf(s); if (i >= 0 && twelveDataAllowedSymbols.length > 1) { twelveDataAllowedSymbols.splice(i, 1); RT43C.dropped.push(s); } }
      RT43C.trimmed = RT43C.dropped.length > 0;
    } else RT43C.reason = "basket-frozen";
    RT43C.coreCost = twelveDataAllowedSymbols.length;
  }
  console.log("rt43c: Twelve Data core basket", RT43C.coreCost, "symbols", RT43C.dropped.length ? "(dropped " + RT43C.dropped.join(",") + ")" : "(unchanged" + (RT43C.reason ? ", " + RT43C.reason : "") + ")");
} catch (e) { console.warn("rt43c basket trim skipped:", e && e.message); }
const RT43C_MIN = Math.max(1, Number(process.env.RT43C_TD_MINUTE_LIMIT || 8));
const RT43C_DAY = Math.max(1, Number(typeof TWELVE_DATA_DAILY_CREDIT_LIMIT !== "undefined" && Number(TWELVE_DATA_DAILY_CREDIT_LIMIT) > 0 ? TWELVE_DATA_DAILY_CREDIT_LIMIT : 800));
const RT43C_MARGIN = Math.max(0, Number(process.env.RT43C_TD_DAILY_MARGIN || 20));
async function rt43cClaimEnergy(cost) {
  const core = RT43C.coreCost || 8, key = typeof TWELVE_DATA_COORDINATION_KEY !== "undefined" ? TWELVE_DATA_COORDINATION_KEY : "core-tape";
  if (typeof sql === "function" && typeof databaseReady !== "undefined" && databaseReady) {
    const r = await sql`
      UPDATE dispatch_market_data_coordination SET
        minute_window_started_at = CASE WHEN minute_window_started_at <= NOW() - INTERVAL '1 minute' THEN NOW() ELSE minute_window_started_at END,
        minute_credits = CASE WHEN minute_window_started_at <= NOW() - INTERVAL '1 minute' THEN ${cost}::int ELSE minute_credits + ${cost}::int END,
        daily_window_started_at = CASE WHEN daily_window_started_at <= NOW() - INTERVAL '24 hours' THEN NOW() ELSE daily_window_started_at END,
        daily_credits = CASE WHEN daily_window_started_at <= NOW() - INTERVAL '24 hours' THEN ${cost}::int ELSE daily_credits + ${cost}::int END,
        updated_at = NOW()
      WHERE cache_key = ${key}
        AND (refresh_lease_id IS NULL OR refresh_lease_expires_at <= NOW())
        AND (cache_expires_at IS NULL OR cache_expires_at > NOW() + INTERVAL '90 seconds')
        AND (minute_window_started_at <= NOW() - INTERVAL '1 minute' OR minute_credits + ${cost}::int <= ${RT43C_MIN}::int)
        AND (daily_window_started_at <= NOW() - INTERVAL '24 hours'
          OR daily_credits + ${cost}::int + ${core}::int * CEIL(GREATEST(0, EXTRACT(EPOCH FROM (daily_window_started_at + INTERVAL '24 hours' - NOW()))) / 900.0)::int <= ${RT43C_DAY - RT43C_MARGIN}::int)
      RETURNING minute_credits, daily_credits`;
    if (r && r[0]) { RT43C.lastClaim = { at: Date.now(), minute: Number(r[0].minute_credits), daily: Number(r[0].daily_credits) }; return true; }
    const s = await sql`SELECT minute_credits, daily_credits, minute_window_started_at > NOW() - INTERVAL '1 minute' AS minute_open,
        EXTRACT(EPOCH FROM (daily_window_started_at + INTERVAL '24 hours' - NOW()))::int AS day_left_s,
        cache_expires_at <= NOW() + INTERVAL '90 seconds' AS core_due, (refresh_lease_id IS NOT NULL AND refresh_lease_expires_at > NOW()) AS core_busy
      FROM dispatch_market_data_coordination WHERE cache_key = ${key}`;
    const x = s && s[0];
    if (!x) { RT43C.reason = "no-core-row"; return false; }
    const dl = Math.max(0, Number(x.day_left_s) || 0), reserve = core * Math.ceil(dl / 900);
    RT43C.reason = x.core_busy || x.core_due ? "core-refresh-due" : (x.minute_open && Number(x.minute_credits) + cost > RT43C_MIN) ? `minute-full ${x.minute_credits}/${RT43C_MIN}`
      : `daily-reserve ${x.daily_credits}+${cost}+core ${reserve} > ${RT43C_DAY - RT43C_MARGIN}`;
    return false;
  }
  // no database: the in-process limiters the core basket already uses
  if (typeof twelveDataMinuteCreditLimiter !== "undefined" && !twelveDataMinuteCreditLimiter.allow(key, cost)) { RT43C.reason = "minute-full"; return false; }
  if (typeof twelveDataDailyCreditLimiter !== "undefined" && !twelveDataDailyCreditLimiter.allow(key, cost)) { RT43C.reason = "daily-full"; return false; }
  return true;
}
try { if (typeof rt43sEnergyFetch === "function") {
  const _ef0 = rt43sEnergyFetch;
  rt43sEnergyFetch = async function () {
    // a refused slot spends no credit: cancel the +2 the caller books for every attempt
    if (Date.now() - RT43C.lastTry < 30_000) { RT43S_EN.used -= 2; RT43S_EN.err = "td-slot-wait: " + (RT43C.reason || "throttled"); return null; }
    RT43C.lastTry = Date.now();
    let ok = false; try { ok = await rt43cClaimEnergy(2); } catch (e) { RT43C.reason = "claim-error"; }
    if (!ok) { RT43S_EN.used -= 2; RT43S_EN.err = "td-slot-wait: " + RT43C.reason; return null; }
    return _ef0.apply(this, arguments);
  };
} } catch (e) { console.warn("rt43c energy wrap skipped:", e && e.message); }
'''
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// rt43c:" in s: sys.exit("REFUSE: rt43c already applied")
need = ["// rt43b: Twelve Data energy diagnostics", "async function rt43sEnergyFetch(", "const twelveDataAllowedSymbols = ", "const TWELVE_DATA_COORDINATION_KEY = ", "dispatch_market_data_coordination"]
miss = [n for n in need if n not in s]
if miss: sys.exit("REFUSE: anchors missing: %r" % miss)
out = s.rstrip("\n") + "\n\n" + BLOCK.strip("\n") + "\n"
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt43c.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt43c would apply (append, node --check passed)"); sys.exit(0)
shutil.copy(p, p + ".bak-rt43c"); os.replace(tmp, p); print("APPLIED rt43c; backup at", p + ".bak-rt43c")
