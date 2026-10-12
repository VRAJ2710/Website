#!/usr/bin/env python3
"""patch_rt32.py — chat28 -> chat29. Stacks on rt31 output (app.js b4103db7). Client + index.html cache bust.
Real Financials / Valuation / Earnings / Institutions tables from the rt32s payload (works with old stub too: shows honest empty copy).
Usage: python3 patch_rt32.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt32)' in s: die('rt32 already applied')
if 'REALTIME PRICE LAYER (rt31)' not in s: die('base is not rt31 output')
if 'app.js?v=chat28' not in h: die('index.html is not chat28')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt31)', '// REALTIME PRICE LAYER (rt32)')
R('lens icon', 'const mem=INVEST_LENSES.find(m=>m.nm===c.name);', 'const mem=_rt32Lens(c.name);')
R('lens clean', '  return { lenses: data.lenses, intelligence: data.intelligence, meta: data.meta };\n}',
  '  return { lenses: _rt32Deep(data.lenses, tk), intelligence: _rt32Deep(data.intelligence, tk), meta: data.meta };\n}')
R('intel clean', '  if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => typeof a === "string" ? _rt28Clean(a) : a).filter(a => a && (typeof a !== "string" || a.length > 3));\n  return c;',
  '  if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => typeof a === "string" ? _rt28Clean(a) : a).filter(a => a && (typeof a !== "string" || a.length > 3));\n  { const tk = _rt27CurTk(); ["headline", "insight"].forEach(k => { c[k] = _rt32Txt(c[k], tk); }); if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => _rt32Txt(a, tk)); if (Array.isArray(c.actions)) c.actions = c.actions.map(a => _rt32Act(a, tk)); }\n  return c;')
BLOCK = r"""// ── rt32: fundamentals tables (SEC EDGAR + Yahoo via /api/financials), lens icons, AI copy ──
let _rt32Per = "annual";
function _rt32E(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]); }
function _rt32N(v, k) {
  if (v == null || !isFinite(v)) return "—";
  const a = Math.abs(v), sg = v < 0 ? "-" : "";
  if (k === "x") return v > 0 ? v.toFixed(1) + "×" : "—";
  if (k === "pct") return (v * 100).toFixed(2) + "%";
  if (k === "eps") return sg + "$" + a.toFixed(2);
  if (k === "n") return a >= 1e9 ? sg + (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? sg + (a / 1e6).toFixed(1) + "M" : a >= 1e3 ? sg + (a / 1e3).toFixed(0) + "K" : sg + a.toFixed(0);
  return sg + "$" + (a >= 1e12 ? (a / 1e12).toFixed(2) + "T" : a >= 1e9 ? (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a.toFixed(0));
}
function _rt32Src(sec) {
  if (!sec) return "";
  let t = ""; try { t = new Date(sec.asOf).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" }); } catch (e) {}
  return `<div style="padding:8px 14px;font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.04em;border-top:1px solid var(--gb)">Source: ${_rt32E(sec.source)}${t ? " · as of " + t : ""}</div>`;
}
function _rt32Empty(what, tk) {
  return `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">No ${what} reported for ${_rt32E(_rt22Name(tk))} by SEC EDGAR or Yahoo Finance.</div>`;
}
function _rt32Head(t) { return `<div style="padding:10px 14px;font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em;border-bottom:1px solid var(--gb);background:var(--b1)">${t}</div>`; }
const _rt32Th = 'style="padding:7px 10px;text-align:right;font-size:9px;color:var(--t3);white-space:nowrap"';
const _rt32Td = 'style="padding:7px 10px;text-align:right;white-space:nowrap"';
function _rt32SetPer(p) { _rt32Per = p; try { if (_finTk && _finCid) loadFinancials(_finTk, _finCid); } catch (e) {} }
renderFinancials = function (tk, data) {
  if (_rt32Cx(tk)) return _rt32NA(tk);
  const f = data && data.financials;
  if (!f || !((f.annual || []).length || (f.quarterly || []).length)) return _rt32Empty("financial statements", tk);
  const per = _rt32Per === "quarterly" && (f.quarterly || []).length ? "quarterly" : "annual";
  const rows = (per === "annual" ? f.annual : f.quarterly).slice(0, 5);
  const btn = (p, l) => `<button type="button" onclick="_rt32SetPer('${p}')" aria-pressed="${per === p}" style="font-family:var(--mn);font-size:10px;font-weight:700;padding:6px 12px;min-height:32px;border-radius:6px;cursor:pointer;border:1px solid ${per === p ? "var(--gd)" : "var(--gb)"};background:${per === p ? "var(--gdG)" : "transparent"};color:${per === p ? "var(--gd)" : "var(--t2)"}">${l}</button>`;
  const L = [["Revenue", "revenue"], ["Gross profit", "grossProfit"], ["Operating income", "operatingIncome"], ["Net income", "netIncome"], ["EPS (diluted)", "eps", "eps"], ["Free cash flow", "fcf"], ["Cash", "cash"], ["Debt", "debt"]]
    .filter(([, k]) => rows.some(r => r[k] != null));
  let o = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid var(--gb);background:var(--b1)"><div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.12em">FINANCIALS · ${_rt32E(tk)}</div><div style="display:flex;gap:6px">${btn("annual", "Annual")}${btn("quarterly", "Quarterly")}</div></div>`;
  o += `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:${120 + rows.length * 78}px"><thead><tr style="border-bottom:1px solid var(--gb)"><th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3)">${per === "annual" ? "FISCAL YEAR" : "QUARTER ENDED"}</th>${rows.map(r => `<th ${_rt32Th}>${_rt32E(per === "annual" ? r.period : r.end)}</th>`).join("")}</tr></thead><tbody>`;
  L.forEach(([lbl, k, kind]) => { o += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03)"><td style="padding:7px 10px;color:var(--t2);white-space:nowrap">${lbl}</td>${rows.map(r => `<td ${_rt32Td}>${_rt32N(r[k], kind)}</td>`).join("")}</tr>`; });
  return o + "</tbody></table></div>" + _rt32Src(f);
};
renderValuation = function (tk, cache) {
  if (_rt32Cx(tk)) return _rt32NA(tk);
  const v = cache && cache.finData && cache.finData.valuation;
  if (!v) return _rt32Empty("valuation figures", tk);
  const M = [["P/E (TTM)", v.pe, "x"], ["Forward P/E", v.forwardPe, "x"], ["Price / Sales", v.ps, "x"], ["Price / Book", v.pb, "x"], ["EV / EBITDA", v.evEbitda, "x"], ["Market cap", v.marketCap], ["Dividend yield", v.divYield, "pct"]]
    .filter(m => m[1] != null);
  if (!M.length) return _rt32Empty("valuation figures", tk);
  let o = _rt32Head(`VALUATION · ${_rt32E(tk)}${v.price ? " · at $" + Number(v.price).toFixed(2) : ""}`);
  o += `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:1px;background:rgba(255,255,255,0.04)">${M.map(([l, x, k]) => `<div style="background:var(--bg);padding:12px 14px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:4px">${l.toUpperCase()}</div><div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--tx)">${_rt32N(x, k)}</div></div>`).join("")}</div>`;
  return o + _rt32Src(v);
};
renderEarnings = function (tk, data) {
  if (_rt32Cx(tk)) return _rt32NA(tk);
  const e = data && data.earnings;
  if (!e || (!(e.history || []).length && !e.next)) return _rt32Empty("earnings history", tk);
  const H = (e.history || []).slice(0, 4);
  let o = _rt32Head(`EARNINGS · ${_rt32E(tk)}`);
  if (e.next && e.next.date) o += `<div style="padding:10px 14px;font-family:var(--sn);font-size:13px;color:var(--tx);border-bottom:1px solid var(--gb)">Next report: <strong>${_rt32E(e.next.date)}</strong>${e.next.isEstimate ? " (estimated)" : ""}${e.next.estimate != null ? ` · consensus EPS ${_rt32N(e.next.estimate, "eps")}` : ""}</div>`;
  if (H.length) {
    o += `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:320px"><thead><tr style="border-bottom:1px solid var(--gb)"><th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3)">QUARTER</th><th ${_rt32Th}>ESTIMATE</th><th ${_rt32Th}>ACTUAL</th><th ${_rt32Th}>SURPRISE</th></tr></thead><tbody>`;
    H.forEach(r => { const c = r.beat == null ? "var(--t2)" : r.beat ? "var(--gn)" : "var(--rd)"; o += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03)"><td style="padding:7px 10px">${_rt32E(r.quarter)}</td><td ${_rt32Td}>${_rt32N(r.estimate, "eps")}</td><td style="padding:7px 10px;text-align:right;color:${c};font-weight:700">${_rt32N(r.actual, "eps")}</td><td style="padding:7px 10px;text-align:right;color:${c}">${r.surprisePct != null ? (r.surprisePct > 0 ? "+" : "") + r.surprisePct.toFixed(1) + "%" : "—"}</td></tr>`; });
    o += "</tbody></table></div>";
  }
  return o + _rt32Src(e);
};
renderHolders = function (tk, data) {
  if (_rt32Cx(tk)) return _rt32NA(tk);
  const I = data && data.institutions;
  if (!I || (!(I.holders || []).length && I.pctHeld == null)) return _rt32Empty("institutional holdings", tk);
  let o = _rt32Head(`INSTITUTIONS · ${_rt32E(tk)}`);
  o += `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:rgba(255,255,255,0.04)">${[["HELD BY INSTITUTIONS", _rt32N(I.pctHeld, "pct")], ["INSIDERS", _rt32N(I.insidersPct, "pct")], ["INSTITUTIONS", I.count != null ? Number(I.count).toLocaleString("en-GB") : "—"]].map(([l, x]) => `<div style="background:var(--bg);padding:12px 10px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.1em;margin-bottom:4px">${l}</div><div style="font-family:var(--mn);font-size:16px;font-weight:800">${x}</div></div>`).join("")}</div>`;
  if ((I.holders || []).length) {
    o += `<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:330px"><thead><tr style="border-bottom:1px solid var(--gb)"><th style="padding:7px 10px;text-align:left;font-size:9px;color:var(--t3)">TOP HOLDERS</th><th ${_rt32Th}>% HELD</th><th ${_rt32Th}>SHARES</th><th ${_rt32Th}>VALUE</th></tr></thead><tbody>`;
    I.holders.slice(0, 10).forEach(x => { o += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03)"><td style="padding:7px 10px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${_rt32E(x.name)}">${_rt32E(x.name)}</td><td ${_rt32Td}>${_rt32N(x.pct, "pct")}</td><td ${_rt32Td}>${_rt32N(x.shares, "n")}</td><td ${_rt32Td}>${_rt32N(x.value)}</td></tr>`; });
    o += "</tbody></table></div>";
    if (I.holders[0] && I.holders[0].date) o += `<div style="padding:6px 14px;font-family:var(--mn);font-size:9px;color:var(--t3)">13F positions reported ${_rt32E(I.holders[0].date)}</div>`;
  }
  return o + _rt32Src(I);
};
function _rt32Cx(tk) { try { const a = A.find(x => x.tk === tk); return !!a && /crypto/i.test(a.cat || ""); } catch (e) { return false; } }
function _rt32NA(tk) { return `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">Company fundamentals don't apply to ${_rt32E(tk)} (crypto asset).</div>`; }
function _rt32MiniTick() {
  try {
    const st = !IS_DESKTOP() && document.querySelector("#main .rt23-stock");
    let m = document.getElementById("rt32Mini");
    const show = !!st && st.getBoundingClientRect().bottom < 0;
    if (!show) { if (m) m.classList.remove("on"); return; }
    if (!m) { m = document.createElement("div"); m.id = "rt32Mini"; m.setAttribute("role", "region"); m.setAttribute("aria-label", "Current instrument"); document.body.appendChild(m); }
    const tk = selTk, a = A.find(x => x.tk === tk) || {}, px = livePx(tk), ch = a.ch;
    const html = `<button type="button" onclick="_rt26Back()" aria-label="Back">←</button><strong style="color:var(--tx)">${_rt32E(tk)}</strong><span style="color:var(--tx)">${px ? "$" + Number(px).toLocaleString("en-US", { maximumFractionDigits: px < 10 ? 4 : 2 }) : ""}</span>${ch != null && isFinite(ch) ? `<span style="color:${ch >= 0 ? "var(--gn)" : "var(--rd)"}">${ch >= 0 ? "+" : ""}${Number(ch).toFixed(2)}%</span>` : ""}`;
    if (m.dataset.h !== html) { m.innerHTML = html; m.dataset.h = html; }
    m.classList.add("on");
  } catch (e) {}
}
try { const _rt32RM = renderMain; renderMain = function () { const r = _rt32RM.apply(this, arguments); _rt32MiniTick(); return r; }; } catch (e) {}
window.addEventListener("scroll", () => { if (!_rt32MiniTick.q) { _rt32MiniTick.q = 1; requestAnimationFrame(() => { _rt32MiniTick.q = 0; _rt32MiniTick(); }); } }, { passive: true });
function _rt32Lens(name) {
  const n = String(name || "");
  const hit = INVEST_LENSES.find(m => m.nm === n) || INVEST_LENSES.find(m => {
    const k = n.toLowerCase();
    return (/macro|rates|cycle/.test(k) && /Macro/.test(m.nm)) || (/value|fundament/.test(k) && /Value/.test(m.nm)) || (/quality|compound/.test(k) && /Quality/.test(m.nm)) || (/catalyst|event/.test(k) && /Catalyst/.test(m.nm)) || (/trend|momentum|technical|flow/.test(k) && /Trend/.test(m.nm));
  });
  if (hit) return hit;
  const ini = n.replace(/\b(analyst|lens)\b/ig, "").trim().split(/\s+/).filter(Boolean).map(w => w[0]).join("").slice(0, 2).toUpperCase() || "AI";
  return { nm: n, cl: "var(--bl)", ic: `<span style="font-family:var(--mn);font-size:15px;font-weight:800">${_rt32E(ini)}</span>`, tagline: "" };
}
function _rt32Txt(t, tk) {
  if (typeof t !== "string") return t;
  let s = _rt31Neg(t);
  try {
    const re = _computeRegimeEngine();
    if (re && !re.loading && /^Risk-(On|Off)/i.test(re.label || "")) s = s.replace(/\bRisk[- ](On|Off)\s*\((Strong|Fragile|Weak|Moderate|Building|Fading|Firm|Mild)\)/gi, re.label);
  } catch (e) {}
  if (tk && /^[A-Z]{2,5}$/.test(tk)) s = s.replace(new RegExp(`\\b${tk[0]}${tk.slice(1).toLowerCase()}(?='s\\b)`, "g"), tk);
  return s;
}
function _rt32Act(a, tk) {
  if (!a || typeof a.label !== "string" || !tk) return a;
  if (/^analy[sz]e\b/i.test(a.label) && !a.label.toUpperCase().includes(tk)) return { ...a, label: `Ask about ${tk}` };
  return a;
}
function _rt32Deep(o, tk, d) {
  d = d || 0;
  if (d > 6 || o == null) return o;
  if (typeof o === "string") return _rt32Txt(o, tk);
  if (Array.isArray(o)) return o.map(x => _rt32Deep(x, tk, d + 1));
  if (typeof o === "object") { const r = {}; for (const k in o) r[k] = k === "label" && typeof o[k] === "string" ? _rt32Act({ label: _rt32Txt(o[k], tk) }, tk).label : _rt32Deep(o[k], tk, d + 1); return r; }
  return o;
}
"""
R('mini head css', '@media (max-width:767px){body:has(#main .rt23-stock) #siteIntelBar,body:has(#main .rt23-stock) #wlGlanceBar{display:none!important}}',
  '@media (max-width:767px){body:has(#main .rt23-stock) #siteIntelBar,body:has(#main .rt23-stock) #wlGlanceBar{display:none!important}}#rt32Mini{position:fixed;left:0;right:0;top:0;z-index:60;display:none;align-items:center;gap:10px;padding:calc(8px + env(safe-area-inset-top,0px)) 14px 8px;background:var(--bg);border-bottom:1px solid var(--gb);font-family:var(--mn);font-size:13px;box-shadow:0 6px 12px -8px rgba(0,0,0,.7)}#rt32Mini.on{display:flex}#rt32Mini button{background:none;border:0;color:var(--t2);font-size:13px;min-height:32px;padding:0 6px 0 0;cursor:pointer}@media (min-width:768px){#rt32Mini{display:none!important}}')
R('rt32 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat28', 'app.js?v=chat29')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
