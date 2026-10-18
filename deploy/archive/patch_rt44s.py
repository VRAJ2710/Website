#!/usr/bin/env python3
"""patch_rt44s.py (server only): GET /api/eia-spot -> official EIA daily WTI/Brent spot (cached ~6 h, free sources only).
Refuses twice; safe-skip if the route anchor is absent. Usage: python3 patch_rt44s.py [--check] server.js"""
import sys, os, subprocess, shutil
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
if "// rt44: official EIA" in s: sys.exit("REFUSE: rt44s already applied")
ANC = 'if (rp === "/api/ext-hours") return rt43bExt(req, res);'
if s.count(ANC) != 1: print("SKIPPED: route anchor matched %d times; nothing changed" % s.count(ANC)); sys.exit(0)
if "function json(res" not in s: print("SKIPPED: json() helper missing; nothing changed"); sys.exit(0)
BLOCK = r'''
// rt44: official EIA daily spot reference for WTI (RWTC) and Brent (RBRTE); free sources only, cached ~6 h
// order: EIA API v2 (only if EIA_API_KEY is set; free key) -> EIA public spot table page -> FRED CSV (EIA series)
const RT44_EIA = { at: 0, tryAt: 0, v: null, src: "", reason: "", p: null };
function rt44Row(p, prev, date, series) { p = Number(p); prev = Number(prev); return p > 0 && /^\d{4}-\d{2}-\d{2}$/.test(date) ? { p: Math.round(p * 100) / 100, prev: prev > 0 ? Math.round(prev * 100) / 100 : null, date, series } : null; }
async function rt44Get(url) { const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (thedispatch.uk reference fetch)", Accept: "*/*" }, signal: AbortSignal.timeout(12000) }); if (!r.ok) throw new Error("http " + r.status); return r.text(); }
async function rt44FromApi() {
  const k = process.env.EIA_API_KEY; if (!k) throw new Error("no-key");
  const out = {};
  for (const [tk, s] of [["WTI", "RWTC"], ["BRENT", "RBRTE"]]) {
    const t = await rt44Get(`https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key=${encodeURIComponent(k)}&frequency=daily&data[0]=value&facets[series][]=${s}&sort[0][column]=period&sort[0][direction]=desc&length=2`);
    const d = (JSON.parse(t).response || {}).data || []; const row = d[0] && rt44Row(d[0].value, d[1] && d[1].value, String(d[0].period), s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44FromPage() {
  const h = await rt44Get("https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm");
  const dates = [...h.matchAll(/class="Series5"[^>]*>\s*(\d{2})\/(\d{2})\/(\d{2})\s*</g)].map(m => `20${m[3]}-${m[1]}-${m[2]}`);
  const out = {};
  for (const [tk, s] of [["WTI", "RWTC"], ["BRENT", "RBRTE"]]) {
    const i = h.indexOf("s=" + s + "&"); if (i < 0) continue;
    const seg = h.slice(Math.max(0, h.lastIndexOf('class="DataRow"', i)), i);
    const vals = [...seg.matchAll(/<td[^>]*class="(?:DataB|Current2)"[^>]*>\s*([\d.,]*)\s*</g)].map(m => m[1].replace(/,/g, ""));
    if (!dates.length || vals.length !== dates.length) continue;
    let j = vals.length - 1; while (j >= 0 && !(Number(vals[j]) > 0)) j--;
    let k = j - 1; while (k >= 0 && !(Number(vals[k]) > 0)) k--;
    const row = j >= 0 && rt44Row(vals[j], k >= 0 ? vals[k] : null, dates[j], s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44FromFred() {
  const out = {}, from = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  for (const [tk, id, s] of [["WTI", "DCOILWTICO", "RWTC"], ["BRENT", "DCOILBRENTEU", "RBRTE"]]) {
    const rows = (await rt44Get(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}&cosd=${from}`)).trim().split(/\r?\n/).slice(1).map(l => l.split(",")).filter(r => Number(r[1]) > 0);
    const a = rows[rows.length - 1], b = rows[rows.length - 2]; const row = a && rt44Row(a[1], b && b[1], a[0], s); if (row) out[tk] = row;
  }
  return out;
}
async function rt44Refresh() {
  const errs = [];
  for (const [name, fn] of [["eia-api", rt44FromApi], ["eia", rt44FromPage], ["fred", rt44FromFred]]) {
    try { const v = await fn(); if (v.WTI || v.BRENT) { RT44_EIA.v = v; RT44_EIA.src = name; RT44_EIA.at = Date.now(); RT44_EIA.reason = ""; return; } errs.push(name + "-empty"); }
    catch (e) { errs.push(name + "-" + String(e && e.message || "error").replace(/[^\w -]/g, "").slice(0, 30)); }
  }
  RT44_EIA.reason = errs.join(",");
}
async function rt44Eia(res) {
  const now = Date.now();
  if ((!RT44_EIA.v || now - RT44_EIA.at > 6 * 3600e3) && now - RT44_EIA.tryAt > 15 * 60e3) {
    RT44_EIA.tryAt = now;
    if (!RT44_EIA.p) RT44_EIA.p = rt44Refresh().finally(() => { RT44_EIA.p = null; });
  }
  if (RT44_EIA.p && !RT44_EIA.v) { try { await RT44_EIA.p; } catch {} }
  const v = RT44_EIA.v;
  if (!v) return json(res, 200, { available: false, reason: RT44_EIA.reason || "pending" }, { "Cache-Control": "no-store" });
  return json(res, 200, { available: true, source: RT44_EIA.src === "fred" ? "EIA via FRED" : "EIA", ...v, fetchedAt: new Date(RT44_EIA.at).toISOString(), ageSec: Math.round((now - RT44_EIA.at) / 1000) }, { "Cache-Control": "public, max-age=900" });
}
'''
out = s.replace(ANC, 'if (rp === "/api/eia-spot") return rt44Eia(res); // rt44: EIA official spot\n      ' + ANC)
out = out.rstrip("\n") + "\n" + BLOCK
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt44.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt44s would apply"); sys.exit(0)
shutil.copy(p, p + ".bak-rt44"); os.replace(tmp, p); print("APPLIED rt44s; backup at", p + ".bak-rt44")
