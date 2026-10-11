#!/usr/bin/env python3
"""patch_rt26.py — chat23 -> chat24. Stacks on rt24 output (t24, app.js b8556c01). Client + index.html cache bust.
Usage: python3 patch_rt26.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt26)' in s: die('rt26 already applied')
if 'REALTIME PRICE LAYER (rt24)' not in s: die('base is not rt24 output')
if 'app.js?v=chat23' not in h: die('index.html is not chat23')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt24)', '// REALTIME PRICE LAYER (rt26)')
# 1. Fear/Greed in the stored brief: real timestamp or drop it (INTEL carries the live value)
R('fg brief', 'o.summary = o.summary.replace(/Fear\\/Greed: /g, `Fear/Greed ${w}: `); }',
  'o.summary = t ? o.summary.replace(/Fear\\/Greed: /g, `Fear/Greed ${w}: `) : o.summary.replace(/\\s*Fear\\/Greed: [^.]*\\.\\s*/g, " ").trim(); }\n  if (typeof o.summary === "string") o.summary = o.summary.replace(/\\s*Fear\\/Greed morning: [^.]*\\.\\s*/g, " ").trim();')
# 2. /crypto/: one as-of source = newest row last_updated; relative age
R('cg rows ts', 'if(typeof _rt!=="undefined")_rt.cgAt=Date.now();',
  'if(typeof _rt!=="undefined"){const lu=_rt26CgRowsTs(_cryptoMktData);_rt.cgAt=lu||Date.now();if(_cryptoAsOf&&lu&&lu>_cryptoAsOf.getTime())_cryptoAsOf=Date.now()-lu<20*60000?null:new Date(lu);}')
R('cg hdr ago', '(_rt.cgAt ? `CoinGecko table \\u00b7 fetched ${_fmtAsOf(_rt.cgAt)}` : "CoinGecko table");',
  '(_rt.cgAt ? `CoinGecko table \\u00b7 updated ${_rt26Ago(_rt.cgAt)}` : "CoinGecko table");')
R('cg subtitle', 'function _rt24CgAge() { try { return _rt.cgAt ? ` · updated ${_fmtAsOf(_rt.cgAt)}` : ""; } catch (e) { return ""; } }',
  'function _rt24CgAge() { return ""; }')
# 3. lightweight-charts: never touch a removed chart
R('chart ro', '      chart.applyOptions({ width: chartEl.clientWidth });\n      if (rsiChart && rsiEl) rsiChart.applyOptions({ width: rsiEl.clientWidth });\n    });',
  '      if (!chartEl.isConnected) { try { ro.disconnect(); } catch (e) {} return; }\n      try {\n        chart.applyOptions({ width: chartEl.clientWidth });\n        if (rsiChart && rsiEl && rsiEl.isConnected) rsiChart.applyOptions({ width: rsiEl.clientWidth });\n      } catch (e) { try { ro.disconnect(); } catch (_) {} }\n    });')
# 4. RANGE = (H-L)/L
R('range', "      ['RANGE', rangePos, 'var(--cy)'],",
  "      ['RANGE (H−L)/L', (isFinite(h24) && isFinite(l24) && l24 > 0 && h24 >= l24) ? (((h24 - l24) / l24) * 100).toFixed(2) + '%' : '—', 'var(--cy)'],")
# 5. relative strength: one unit (pts), named period, grammar, no crypto vs SPY
R('rs crypto', 'function _tickerRelStrength(tk) {', 'function _tickerRelStrength(tk) {\n  try { if (_rtIsCrypto(tk)) return { rel: null, col: "var(--t3)", label: "Not compared (crypto trades 24h)" }; } catch (e) {}')
R('rs inline', 'if (Math.abs(rel) < 0.05) return { rel, col: "var(--t3)", label: "In line" };', 'if (Math.abs(rel) < 0.05) return { rel, col: "var(--t3)", label: "In line with" };')
R('rs pulse', 'const rsLbl = rs.rel == null ? rs.label : `${rs.label} SPY by ${Math.abs(rs.rel).toFixed(2)} pts`;', 'const rsLbl = _rt26RsTxt(tk, rs);')
R('rs tile', 'const rsVal=rs.rel==null?"—":`${rs.rel>=0?"+":""}${rs.rel.toFixed(2)}%`;', 'const rsVal=rs.rel==null?"—":`${rs.rel>=0?"+":""}${rs.rel.toFixed(2)} pts`;')
R('rs cmp', 'return `<td style="text-align:right;padding:8px;color:${c}">${rel >= 0 ? "+" : ""}${rel.toFixed(2)}%</td>`;', 'return `<td style="text-align:right;padding:8px;color:${c}">${rel >= 0 ? "+" : ""}${rel.toFixed(2)} pts</td>`;')
R('rs cmp lbl', 'vs SPY (day)</td>', 'vs SPY (day, pts)</td>')
# 6. PULSE / thesis: end on whole sentences; INTEL copy
R('pulse sent', '${_rt16Clip(_rt24Th(a), 140)}', '${_rt26Sent(_rt24Th(a), 160)}')
R('card sent', '${_rt16Clip(_rt24Th(a), 120)}', '${_rt26Sent(_rt24Th(a), 140)}')
R('intel head', '_rt24Copy(intel.headline)', '_rt26Copy(intel.headline)', 2)
R('intel insight', '(intel.insight || "").replace(/</g, "<")', '_rt26Sent(_rt26Copy(intel.insight || ""), 420).replace(/</g, "<")', 2)
R('phone back', '  let h=`<div class="rt23-stock"', '  let h=`<button type="button" class="rt26-back" onclick="_rt26Back()" aria-label="Back">← Back</button><div class="rt23-stock"')
# 7. phone palette
R('palette enter', '  if (e.key === "Enter" && _searchIdx >= 0 && items[_searchIdx]) { e.preventDefault(); items[_searchIdx].click(); return; }',
  '  if (e.key === "Enter" && items.length) { e.preventDefault(); items[_searchIdx >= 0 && items[_searchIdx] ? _searchIdx : 0].click(); return; }')
R('palette ph', 'sinp.placeholder=IS_DESKTOP()?"Ticker, command, or research…":"Search tickers & commands…";', 'sinp.placeholder=IS_DESKTOP()?"Ticker, command, or research…":"Search tickers…";')
# 8. full words
R('tags full', '  const m = { Accumulation: "ACCUM.", Geopolitical: "GEOPOL.", Geopolitics: "GEOPOL.", Commodities: "COMMOD." };', '  const m = {};')
# polish: closed-day wording, no feed age while closed
R('day word', '% today`', '% ${_rt26Day(tk)}`', 2)
R('day word hdr', '(${sign}${d.c}%) today`', '(${sign}${d.c}%) ${_rt26Day(a.tk)}`', 2)
R('feed age', '            ${priceLastFetch?`<span', '            ${priceLastFetch&&!_rt20LastClose(a.tk)?`<span')
R('feedlbl1', "    const feedLbl = d.status === 'unavailable'", "    const feedLbl = (d.status !== 'unavailable' && _rt20LastClose(a.tk)) ? 'CLOSED' : d.status === 'unavailable'")
R('feedlbl2', '  const feedLbl=d.status==="unavailable"?', '  const feedLbl=(d.status!=="unavailable"&&_rt20LastClose(a.tk))?"CLOSED":d.status==="unavailable"?')
# factors hidden when empty; overview no longer repeats the Thesis tab
R('factors open', '    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb)">`;', '    if (bullish.length || bearish.length) {\n    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb)">`;')
R('factors close', '    h += `</div>`;\n\n    h += `<div class="tabs">', '    h += `</div>`;\n    }\n\n    h += `<div class="tabs">')
R('ov thesis', '    if(aTab==="ov"){\n      h += `<div class="ap-thesis">${_rt24Th(a)}</div>`;', '    if(aTab==="ov"){')
# WTI and other futures: an exact 0.00 is a missing basis, not a real change
R('fut zero', '  { const xc = _rt24XauChg(tk); if (xc !== undefined) return xc; }\n  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;\n  const c = P[tk]?.c;',
  '  { const xc = _rt24XauChg(tk); if (xc !== undefined) return xc; }\n  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;\n  if ((tk === "WTI" || tk === "NG" || tk === "SLV") && Number(P[tk]?.c) === 0) return null;\n  const c = P[tk]?.c;', 2)
# book tiles: desk tickers only (no BTC + BTC-USD, XAU + GC=F)
R('book dedupe', '  const book=_newsBookTickers();\n  const re=_computeRegimeEngine();', '  const book=_rt26BookDesk();\n  const re=_computeRegimeEngine();', 2)
BLOCK = r"""// ── rt26 helpers ──
function _rt26Ago(ts) {
  const s = Math.max(0, Math.round((Date.now() - ts) / 1000));
  return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.round(s / 60)}m ago` : _rt20AgeLbl(ts);
}
function _rt26CgRowsTs(data) {
  let m = 0; try { (data || []).forEach(c => { const t = Date.parse(c && c.last_updated); if (t > m) m = t; }); } catch (e) {}
  return m && m <= Date.now() + 60000 ? m : 0;
}
function _rt26Day(tk) {
  try { const lc = _rt20LastClose(tk); if (lc) return new Date(lc).toLocaleDateString("en-GB", { weekday: "short", timeZone: (_rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.tz) || "Europe/London" }); } catch (e) {}
  return "today";
}
function _rt26RsTxt(tk, rs) {
  if (rs.rel == null) return rs.label;
  const when = _rt26Day(tk) === "today" ? "today" : `on ${_rt26Day(tk)}`;
  if (rs.label === "In line with") return `In line with SPY ${when}`;
  return `${rs.label} SPY by ${Math.abs(rs.rel).toFixed(2)} pts ${when}`;
}
/** Whole sentences up to ~max; a trailing cut fragment ('…' / '...') is dropped back to the last full sentence. */
function _rt26Sent(t, max) {
  let s = String(t || "").replace(/\s+/g, " ").trim();
  if (/(\.\.\.|…)$/.test(s)) {
    const m = s.replace(/\s*(\.\.\.|…)$/, "");
    const i = Math.max(m.lastIndexOf(". "), m.lastIndexOf("! "), m.lastIndexOf("? "));
    s = i > 0 ? m.slice(0, i + 1) : m.replace(/[\s,;:·–—-]+$/, "") + ".";
  }
  if (!max || s.length <= max) return s;
  const parts = s.match(/[^.!?]+[.!?]+(?=\s|$)/g) || [s];
  let out = "";
  for (const p of parts) { const n = (out + " " + p.trim()).trim(); if (n.length > max && out) break; out = n; if (out.length > max) break; }
  return out.length <= max * 1.8 ? out : _rt16Clip(s, max);
}
function _rt26Copy(t) {
  if (typeof t !== "string") return t;
  return _rt24Copy(t).replace(/Market Regime Update:\s*([^.·|]+?)\s+Environment\b/gi, "Market regime: $1").replace(/Market Regime Update:\s*/gi, "Market regime: ");
}
function _rt26Back() {
  try { if (history.state && history.length > 1) { history.back(); return; } } catch (e) {}
  try { selTk = null; nav("mkt"); } catch (e) {}
}
function _rt26BookDesk() {
  const out = [], seen = new Set();
  const add = t => { if (!t) return; const d = (typeof resolveInternalTicker === "function" && resolveInternalTicker(String(t))) || String(t); if (!seen.has(d)) { seen.add(d); out.push(d); } };
  try { getActiveWl().tickers.forEach(add); } catch (e) {}
  try { portfolio.forEach(p => add(p && p.tk)); } catch (e) {}
  out.__rt26 = true; // news matching re-expands to wire forms (BTC-USD, GC=F)
  return out;
}
(function _rt26Init() {
  if (document.getElementById("rt26-css")) return;
  const st = document.createElement("style"); st.id = "rt26-css";
  st.textContent = `
.rt26-back{display:none;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:6px;font-family:var(--mn);font-size:11px;padding:0 12px;min-height:36px;margin:0 0 8px;cursor:pointer}
@media (max-width:767px){.rt26-back{display:inline-flex;align-items:center}}
@media (min-width:768px){#wlGlanceBar{-webkit-mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 36px),transparent);mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 36px),transparent)}}`;
  document.head.appendChild(st);
})();
"""
R('news book expand', 'function _newsMatchesBook(n,book){', 'function _newsMatchesBook(n,book){\n  try{if(book&&book.__rt26)book=_newsBookTickers();}catch(e){}')
R('rt26 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
E = [e for e in E if e[0] != 'xx']
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat23') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat23', 'app.js?v=chat24')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
