#!/usr/bin/env python3
"""patch_rt22.py — chat20 -> chat21. Stacks on rt21 output (t21). Client + index.html.
Usage: python3 patch_rt22.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt22)' in s: die('rt22 already applied')
if 'REALTIME PRICE LAYER (rt21)' not in s: die('base is not rt21 output')
if 'app.js?v=chat20' not in h: die('index.html is not chat20')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt21)', '// REALTIME PRICE LAYER (rt22)')
# 1. admin desktop home brief: the home overlay was not in the brief refresh set
R('brief refresh homeOv', '  if (IS_DESKTOP() && (document.getElementById("briefOv") || document.getElementById("dashOv"))) return true;',
  '  if (IS_DESKTOP() && (document.getElementById("homeOv") || document.getElementById("briefOv") || document.getElementById("dashOv"))) return true;')
R('brief paint local first', '  _archiveBrief(_brief);\n\n  // 2) AI upgrade:', '  _archiveBrief(_brief);\n  _refreshBriefSurfaces(); // rt22: show the free brief now; the AI upgrade replaces it when it lands\n\n  // 2) AI upgrade:')
R('brief empty copy', '      <div>No brief loaded yet.</div>', '      <div>Morning brief not published yet today.</div>')
# 3. news text
R('clip ellipsis', '  if (s.length > n) return _rt16Clip(s, n);\n  if (s.length >= 180',
  '  if (/(\\.\\.\\.|…)$/.test(s)) { const b = s.replace(/\\s*(\\.\\.\\.|…)$/, ""); const w = /[A-Za-z0-9]$/.test(b) && b.lastIndexOf(" ") > 20 ? b.slice(0, b.lastIndexOf(" ")) : b; s = w.replace(/[\\s,;:·–—-]+$/, "") + "…"; if (s.length <= n) return s; }\n  if (s.length > n) return _rt16Clip(s, n);\n  if (s.length >= 180')
R('txt block separators', '  let t = String(s || "").replace(/<[^>]*>/g, " ")',
  '  let t = String(s || "").replace(/<\\/(p|div|li|h[1-6]|blockquote)>|<br\\s*\\/?>|\\n+/gi, "\\u2029").replace(/<[^>]*>/g, " ")')
R('txt block join', '    .replace(/\\s+/g, " ").trim();\n  return n ? _rt20Clip(t, n) : t;',
  '    .replace(/([^\\s.!?:;…"”’)\\u2029])\\s*\\u2029[\\s\\u2029]*(?=["“‘]?[A-Z])/g, "$1. ").replace(/\\u2029/g, " ")\n    .replace(/\\s+/g, " ").trim();\n  return n ? _rt20Clip(t, n) : t;')
# 4. one relation chip per card (the most relevant)
R('news rel one chip', '  return (rel || []).slice(0, 2).map(r => {', '  return (rel || []).slice(0, 1).map(r => {')
# 5. /crypto/ auto-load once per page view
R('crypto autoload', '  if(!_cryptoMktData){\n    h+=`<div class="gc" role="status"',
  '  if(!_cryptoMktData&&!_cryptoError&&!window.__rt22CgAuto){window.__rt22CgAuto=1;setTimeout(()=>{if(!_cryptoMktData&&!_cryptoMktLoading)fetchCryptoMarket();},0);}\n  if(!_cryptoMktData){\n    h+=`<div class="gc" role="status"')
# 6. XAU spot proxy: % on the GC=F basis (same as tape and /gold/); no basis -> no %
R('gc pct record', '  if (hasPrev && !proxyish && !RT_SRC.has(src) && !_rtIsCrypto(tk) && (tk !== "XAU" || src === "twelve-data")) _rt.goodPrev[tk] = q.prev;',
  '  if (hasPrev && !proxyish && !RT_SRC.has(src) && !_rtIsCrypto(tk) && (tk !== "XAU" || src === "twelve-data")) _rt.goodPrev[tk] = q.prev;\n  if (tk === "XAU" && hasPrev && !proxyish && !RT_SRC.has(src) && src !== "twelve-data" && q.p > 0) _rt.gcPct = { c: ((q.p - q.prev) / q.prev) * 100, at: now };')
R('gold poll basis', '_rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Spot Gold (proxy)", repaint: true });',
  '_rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Spot Gold (proxy)", repaint: true, ...((_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) ? { prev: p / (1 + _rt.gcPct.c / 100) } : { noBasePrev: true }) });')
# 8. status pill leaves 'Loading prices…' with the first painted price
R('pill sig', 'const sig=[_userTierReady?"r":"w",priceLastFetch?"p":"n",', 'const sig=[_userTierReady?"r":"w",priceLastFetch?"p":(liveSymbols.size?"l":"n"),')
R('pill first price', '    :(!priceLastFetch&&!hasFeed)\n      ?`<span class="htec-chip htec-chip-muted">Loading prices…</span>`',
  '    :(!priceLastFetch&&!hasFeed&&!liveSymbols.size)\n      ?`<span class="htec-chip htec-chip-muted">Loading prices…</span>`\n      :(!hasFeed&&liveSymbols.size&&priceFetching)\n        ?`<span class="htec-chip htec-chip-muted">${liveSymbols.size} prices · syncing</span>`')
# stock detail: tab strip without emoji, valuation copy
OLD_TABS = '''<button class="${aTab==="val"?"on":""}" onclick="_setATab('val')">💰 Valuation</button><button class="${aTab==="earn"?"on":""}" onclick="_setATab('earn')">📈 Earnings</button>'''
R('tabs no emoji', OLD_TABS, OLD_TABS.replace('💰 ', '').replace('📈 ', ''), 2)
R('tabs inst', '''onclick="_setATab('inst')">🏛 Institutions${''', '''onclick="_setATab('inst')">Institutions${''', 2)
R('tab active into view', 'function _setATab(t){aTab=t;if(IS_DESKTOP())renderP2();else renderMain();}',
  'function _setATab(t){aTab=t;if(IS_DESKTOP())renderP2();else renderMain();_rt22TabIntoView();}\nfunction _rt22TabIntoView(){requestAnimationFrame(()=>document.querySelectorAll(".tabs > button.on").forEach(b=>{const s=b.parentElement;if(s&&s.scrollWidth>s.clientWidth)s.scrollLeft=Math.max(0,b.offsetLeft-s.offsetLeft-(s.clientWidth-b.offsetWidth)/2);}));}')
R('valuation copy', """Valuation data not available for '+tk+'<br><span style="font-size:11px">US-listed stocks with financial metrics only</span></div>';""",
  """'+_rt22NoData('Valuation figures', tk)+'</div>';""")

# chat20 QA: clear also resets the watchlist; honest 'Syncing…'; no payments-mode label for customers
R('clear watchlist', '  try { localStorage.removeItem(RT17_PREFS_KEY); } catch (e) {}\n  _rt17Prefs = _rt17Default(); _rt17Apply(); _rt17Render();',
  '  try { localStorage.removeItem(RT17_PREFS_KEY); localStorage.removeItem("td_awl"); localStorage.removeItem("td_wls"); } catch (e) {}\n  _rt22ResetWatchlists();\n  _rt17Prefs = _rt17Default(); _rt17Apply(); _rt17Render();')
R('cleared copy', 'Cleared. Settings are back to defaults on this device.', 'Cleared. Settings and watchlists are back to defaults on this device.')
R('clear ask copy', '<span>Clear all settings on this device?</span>', '<span>Clear all settings and watchlists on this device?</span>')
R('premium kicker', '★ DISPATCH PREMIUM · LIVE PAYMENTS', '★ DISPATCH PREMIUM · £15/MONTH')

# stock detail audit: fundamentals endpoints are empty server stubs -> honest copy, hide on non-stocks
R('fin nodata', 'function renderFinancials(tk, data) {\n  const m = data.metrics || {};',
  'function renderFinancials(tk, data) {\n  if (!data || !data.metrics || !Object.values(data.metrics).some(v => v != null && v !== 0)) return `<div style="padding:20px;text-align:center;font-family:var(--sn);font-size:13px;color:var(--t3)">${_rt22NoData("Financial figures", tk)}</div>`;\n  const m = data.metrics || {};')
R('earn nodata', "No earnings history for '+tk+'</div>';", "'+_rt22NoData('Earnings figures', tk)+'</div>';")
R('inst nodata', 'No institutional holder data for ${tk}</div>`;', '${_rt22NoData("Institutional holdings", tk)}</div>`;')
for _t in ('fi', 'val', 'earn'):
    R(f'tab hide {_t}', f"""<button class="${{aTab==="{_t}"?"on":""}}" onclick="_setATab('{_t}')">""", f"""<button class="${{aTab==="{_t}"?"on":""}}"${{_rt22Fund()?"":" hidden"}} onclick="_setATab('{_t}')">""", 2)
R('tab hide inst', """<button class="${aTab==="inst"?"on":""}" onclick="_setATab('inst')">""", """<button class="${aTab==="inst"?"on":""}"${_rt22Fund()?"":" hidden"} onclick="_setATab('inst')">""", 2)

R('rss title clip', 'x:title.length>120?title.slice(0,117)+"...":title,', 'x:_rt16Clip(title,120),')
R('lens thesis clip', '${(a.th || "").slice(0, 80)}...`', '${_rt16Clip(a.th || "", 80)}`')
R('xau flat proxy', "        // upstream refreshes about every 30s: aim 2s after the next refresh",
  "        if (!(_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) && P.XAU && !P.XAU.c) liveQuoteChangeAvailable.XAU = false; // rt22: never show a flat proxy as a real 0.00%\n        // upstream refreshes about every 30s: aim 2s after the next refresh")
BLOCK = r"""// ── rt22: honest empty states and a clean tab strip on the stock detail view ──
function _rt22Name(tk) { try { const a = A.find(x => x.tk === tk); return a && a.nm ? a.nm : tk; } catch (e) { return tk; } }
function _rt22NoData(what, tk) {
  return `${what} aren't available for ${_escHtml(_rt22Name(tk))} right now.<br><span style="font-size:11px">The free data source returned nothing for this ticker. Overview, News and Alerts still work.</span>`;
}
function _rt22Fund() {
  try { const tk = (IS_DESKTOP() && typeof termSelTk !== "undefined" && termSelTk) || selTk; const a = A.find(x => x.tk === tk);
    return !a || (a.cat === "Stock" && !/\bETF\b|\bTrust\b|\bFund\b/i.test(a.nm || "")); } catch (e) { return true; }
}
function _rt22NoSync() { try { return (_rt20Booting() || priceFetching || !priceLastFetch) ? "Syncing…" : "NO LIVE SYNC"; } catch (e) { return "NO LIVE SYNC"; } }
function _rt22ResetWatchlists() {
  try {
    ["td_w", "qe_w"].forEach(k => localStorage.removeItem(k));
    watchlists = [{ id: "wl1", name: "My Watchlist", tickers: ["SPY", "NVDA", "BTC", "XAU", "AAPL"] }];
    activeWlId = "wl1"; saveWatchlists();
  } catch (e) {}
}
(function _rt22Css() {
  if (document.getElementById("rt22-css")) return;
  const st = document.createElement("style"); st.id = "rt22-css";
  st.textContent = `
.tabs{display:flex;flex-wrap:nowrap;gap:18px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;scroll-padding:0 24px}
.tabs>button{flex:0 0 auto;white-space:nowrap;min-height:44px}
@media (max-width:767px){.tabs{gap:14px;padding-right:24px;-webkit-mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 28px),transparent);mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 28px),transparent)}}`;
  document.head.appendChild(st);
})();
"""
R('rt22 block', 'function _rt21BriefWords(o) {', BLOCK + 'function _rt21BriefWords(o) {')
import re as _re
_n0 = len(_re.findall(r'(?<=[?:])\s*"NO LIVE SYNC"|"NO LIVE SYNC"(?=\s*:)', s))
if _n0 < 6: die(f'NO LIVE SYNC expression sites: {_n0} (want >= 6)')
s = _re.sub(r'((?<=[?:])\s*)"NO LIVE SYNC"', lambda m: m.group(1) + '_rt22NoSync()', s)
s = _re.sub(r'"NO LIVE SYNC"(?=\s*:)', '_rt22NoSync()', s)
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
HE = [('cache bust', 'app.js?v=chat20', 'app.js?v=chat21')]
OLD_HERO = [('THE DISPATCH MARKETS · GOLD &amp; MACRO RESEARCH</p>', 'THE WEEK AHEAD · GOLD &amp; MACRO</p>'),
            ('A conditional weekly stance for independent traders: gold structure, macro context, and the evidence that would confirm or invalidate the read.</p>',
             'A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions.</p>')]
for name, old, new in HE:
    if h.count(old) != 1: die(f"index '{name}' matched {h.count(old)} times")
    h = h.replace(old, new)
for old, new in OLD_HERO:  # static shell copy, when present (the server renders the same block; see patch_rt22s)
    n = h.count(old)
    if n > 1: die('index hero anchor ambiguous')
    if n == 1: h = h.replace(old, new)
    else: print('  note: index hero copy not found (server-rendered only):', old[:40])
for bad in ['💰 Valuation', 'No brief loaded yet', 'US-listed stocks with financial metrics only']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
