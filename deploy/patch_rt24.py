#!/usr/bin/env python3
"""patch_rt24.py — chat22 -> chat23. Stacks on rt23 output (t23). Client + index.html cache bust.
Usage: python3 patch_rt24.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt24)' in s: die('rt24 already applied')
if 'REALTIME PRICE LAYER (rt23)' not in s: die('base is not rt23 output')
if 'app.js?v=chat22' not in h: die('index.html is not chat22')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt23)', '// REALTIME PRICE LAYER (rt24)')
# 1. search: exact ticker, then ticker prefix, then name, then fuzzy
R('search rank', '  }catch(e){}\n  return r;\n}\nfunction doSearch(q){', '  }catch(e){}\n  return _rt24RankHits(r,raw);\n}\nfunction doSearch(q){')
R('ac slice', "  const localHits=A.filter(a=>a.tk.toLowerCase().startsWith(ql)||a.nm.toLowerCase().includes(ql)).slice(0,5);", "  const localHits=_rt24RankA(A.filter(a=>a.tk.toLowerCase().startsWith(ql)||a.nm.toLowerCase().includes(ql)),q).slice(0,5);")
R('meta label', '      status: "unavailable",\n      label: "NO SYNC",\n      detail: "Not received from a market feed this session', '      status: "unavailable",\n      label: (typeof _rt20Booting === "function" && (_rt20Booting() || !priceLastFetch)) ? "SYNCING" : "NO QUOTE",\n      detail: "Not received from a market feed this session')
R('ac rank', '  const localTks=new Set(localHits.map(a=>a.tk));', '  localHits=_rt24RankA(localHits,q);\n  const localTks=new Set(localHits.map(a=>a.tk));')
R('go exact', "  if (ac && ac.classList.contains('show')) {", "  if (ac && ac.classList.contains('show') && !A.some(a=>a.tk===val)) {")
# 2. signals tags: full words / proper abbreviations
R('sig tag', '${s.cat.toUpperCase().slice(0,6)}</span>', '${_rt24Tag(s.cat)}</span>')
# 4. XAU change: GC=F basis or '—' on every path
R('xau liveChg', '  if (!hasSyncedQuote(tk)) return null;\n  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;\n  const c = P[tk]?.c;',
  '  if (!hasSyncedQuote(tk)) return null;\n  { const xc = _rt24XauChg(tk); if (xc !== undefined) return xc; }\n  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;\n  const c = P[tk]?.c;')
R('xau refChg', '  if (referencePx(tk) == null) return null;\n', '  if (referencePx(tk) == null) return null;\n  { const xc = _rt24XauChg(tk); if (xc !== undefined) return xc; }\n')
R('xau fp', '    p, c: pctN.toFixed(2), chg: fmtChg, raw: chg, d: dir,', '    p, ..._rt24XauFp(tk, d.p, { c: pctN.toFixed(2), chg: fmtChg, raw: chg, d: dir }),')
R('stock card chg', ':`${chSign}${d.chg} (${chSign}${d.c}%)`}</div>', ':(chAn==null?"—":`${chSign}${d.chg} (${chSign}${d.c}%)`)}</div>')
# 5. /crypto/: desktop overlay refresh on load + age in the header
R('crypto overlay refresh', "if(pg==='crypto'){renderMain();if(typeof _refreshOverlay==='function')_refreshOverlay('cryptoOv',renderCryptoPage);}",
  "if(pg==='crypto'||document.getElementById('cryptoOv')){if(pg==='crypto')renderMain();if(typeof _refreshOverlay==='function')_refreshOverlay('cryptoOv',renderCryptoPage);}", 2)
R('crypto hdr age', '_renderPgHdr("Crypto Markets", "Top 50 by market cap · CoinGecko",', '_renderPgHdr("Crypto Markets", "Top 50 by market cap · CoinGecko" + _rt24CgAge(),')
# ADA: a stale CoinGecko snapshot never beats a newer desk quote
R('coin desk newer', '    } else if (!liveQuoteCached[tk] && age < 30 * 60_000 && ts >= out.ts - 3 * 60_000) {',
  '    } else if ((!liveQuoteCached[tk] && age < 30 * 60_000 && ts >= out.ts - 3 * 60_000) || (_rtTableStale() && ts > out.ts && age < 6 * 3600_000)) {')
# 6. sync labels
R('nosync helper', 'function _rt22NoSync() { try { return (_rt20Booting() || priceFetching || !priceLastFetch) ? "Syncing…" : "NO LIVE SYNC"; } catch (e) { return "NO LIVE SYNC"; } }',
  'function _rt22NoSync() { try { return (_rt20Booting() || !priceLastFetch) ? "Syncing…" : "—"; } catch (e) { return "—"; } }')
R('asof no sync', '  if(d.status==="unavailable"||!d.asOf)return `<span class="asof-tag asof-na" title="No feed tick this session">no sync</span>`;',
  '  if(d.status==="unavailable"||!d.asOf){try{if(_rt20Booting()||!priceLastFetch)return "";}catch(e){}return `<span class="asof-tag asof-na" title="${_escAttr(d.detail||"No quote from the free feeds for this symbol this session")}">no quote</span>`;}')
R('fp label', '      status: "unavailable", label: "NO SYNC",', '      status: "unavailable", label: (typeof _rt20Booting === "function" && (_rt20Booting() || !priceLastFetch)) ? "SYNCING" : "NO QUOTE",')
# 7. one chart label on phone and desktop
R('desktop chart lbl', 'HISTORICAL ${String(usedRange).toUpperCase()} · ${tk}${proxyNote} · ${quoteContext}', '${_rt24ChartHead(tk, usedRange)} · ${tk}${proxyNote} · ${quoteContext}')
R('phone chart lbl', '  return open ? "INTRADAY · UPDATES ON FETCH" : "LAST SESSION · MARKET CLOSED";', '  return open ? "INTRADAY · UPDATES ON FETCH" : _rt24ChartHead(tk, "1d");')
R('phone fb lbl', 'label = `LAST SESSION · ${day(s.last).toUpperCase()}`;', 'label = `LAST SESSION · ${day(s.last).toUpperCase()} · YAHOO`;')
R('phone fb lbl2', 'label = "DAILY · 1M"; }', 'label = "DAILY · 1M · YAHOO"; }')
# polish: thesis staleness guard, copy
R('th pulse', '${_rt16Clip(a.th || "", 140)}', '${_rt16Clip(_rt24Th(a), 140)}')
R('th card', '${_rt16Clip(a.th, 120)}', '${_rt16Clip(_rt24Th(a), 120)}')
R('th ap', '<div class="ap-thesis">${a.th}</div>', '<div class="ap-thesis">${_rt24Th(a)}</div>', 2)
R('th tab', 'line-height:1.6;margin-top:6px">${a.th}</div></div>`;', 'line-height:1.6;margin-top:6px">${_rt24Th(a)}</div></div>`;')
R('rs pts', '`${rs.label} SPY by ${rs.rel >= 0 ? "+" : ""}${rs.rel.toFixed(2)}%`', '`${rs.label} SPY by ${Math.abs(rs.rel).toFixed(2)} pts`')
R('intel copy bar', 'const headRaw = String(intel.headline || reLabel())', 'const headRaw = String(_rt24Copy(intel.headline) || reLabel())')
R('intel copy card', '    <div class="si-headline">${(intel.headline || "").replace(/</g, "&lt;")}</div>', '    <div class="si-headline">${(_rt24Copy(intel.headline) || "").replace(/</g, "&lt;")}</div>')
R('back label', '← BACK TO NEWS<', '← BACK<', 2)
R('cmp table', '<table style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:320px">', '<table class="rt24-cmp" style="width:100%;border-collapse:collapse;font-family:var(--mn);font-size:11px;min-width:320px">')
R('fg snapshot', '  ["headline", "summary", "houseView"].forEach(k => { if (typeof o[k] === "string") o[k] = fix(o[k]); });',
  '  ["headline", "summary", "houseView"].forEach(k => { if (typeof o[k] === "string") o[k] = fix(o[k]); });\n  if (typeof o.summary === "string" && /Fear\\/Greed: /.test(o.summary)) { const t = Date.parse(o.generatedAt || o.asOf || o.createdAt || ""); let w = "morning"; try { if (t) w = "at " + new Date(t).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: (_rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.tz) || "Europe/London" }); } catch (e) {} o.summary = o.summary.replace(/Fear\\/Greed: /g, `Fear/Greed ${w}: `); }')
R('ns 2844', '${chg==null?"NO SYNC":`${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`}</div', '${chg==null?_rt22NoSync():`${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`}</div')
R('ns now', ': "now — NO SYNC";', ': "now —";')
R('ns pnl', '      : "day P&L NO SYNC";', '      : "day P&L —";')
R('ns cost', ':`at cost · NO SYNC`;', ':`at cost · no quote`;')
R('ns badge', '`<span class="bd" style="background:var(--b3);color:var(--t3);font-size:7.5px">NO SYNC</span>`', '`<span class="bd" title="No quote from the free feeds this session — valued at cost" style="background:var(--b3);color:var(--t3);font-size:7.5px">NO QUOTE</span>`')
R('rs nosync', 'return { rel: null, col: "var(--t3)", label: "No sync" };', 'return { rel: null, col: "var(--t3)", label: "vs SPY —" };')
R('cap nosync', '<span class="cap-st" style="color:var(--t3)">No sync</span>', '<span class="cap-st" style="color:var(--t3)" title="Needs a day change for both legs; one or both have no change basis right now">—</span>')
BLOCK = r"""// ── rt24: search ranking, XAU basis, chart labels, thesis guard, copy ──
function _rt24Score(tk, nm, q) {
  const Q = String(q || "").trim().toUpperCase(); if (!Q) return 0;
  const T = String(tk || "").toUpperCase(), N = String(nm || "").toUpperCase();
  return T === Q ? 4 : T.startsWith(Q) ? 3 : N.startsWith(Q) ? 2 : (T.includes(Q) || N.includes(Q)) ? 1 : 0;
}
function _rt24RankHits(r, raw) {
  r.forEach((x, i) => {
    x._i = i;
    if (x.tk) { const sc = _rt24Score(x.tk, String(x.nm || "").replace(/^[^—]*—\s*/, ""), raw); if (sc === 4) x.priority = 10; else if (sc === 3) x.priority = Math.max(x.priority || 0, 2.5); else if (sc === 2) x.priority = Math.max(x.priority || 0, 2.2); }
  });
  return r.sort((a, b) => (b.priority || 0) - (a.priority || 0) || a._i - b._i);
}
function _rt24RankA(list, q) {
  return (list || []).map((a, i) => [a, i]).sort((x, y) => _rt24Score(y[0].tk, y[0].nm, q) - _rt24Score(x[0].tk, x[0].nm, q) || x[1] - y[1]).map(x => x[0]);
}
function _rt24Tag(cat) {
  const m = { Accumulation: "ACCUM.", Geopolitical: "GEOPOL.", Geopolitics: "GEOPOL.", Commodities: "COMMOD." };
  return m[cat] || String(cat || "").toUpperCase();
}
/** XAU: every source's own prior close disagrees (spot proxy has none; weekend spot prev ~ flat). One basis: GC=F session %, else '—'. */
function _rt24XauChg(tk) {
  if (tk !== "XAU") return undefined;
  try {
    const g = _rt.gcPct; return g && Date.now() - g.at < 6 * 3600_000 && isFinite(g.c) ? +g.c.toFixed(2) : null;
  } catch (e) { return undefined; }
}
function _rt24XauFp(tk, p, o) {
  const xc = _rt24XauChg(tk);
  if (xc === undefined) return o;
  if (xc === null) return { c: "—", chg: "—", raw: 0, d: 0 };
  const abs = p - p / (1 + xc / 100);
  return { c: xc.toFixed(2), chg: abs.toFixed(2), raw: abs, d: xc > 0 ? 1 : xc < 0 ? -1 : 0 };
}
function _rt24CgAge() { try { return _rt.cgAt ? ` · updated ${_fmtAsOf(_rt.cgAt)}` : ""; } catch (e) { return ""; } }
function _rt24ChartHead(tk, range) {
  try {
    const lc = String(range || "").toLowerCase() === "1d" ? _rt20LastClose(tk) : null;
    if (lc) return `LAST SESSION · ${new Date(lc).toLocaleDateString("en-GB", { weekday: "short", timeZone: (_rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.tz) || "Europe/London" }).toUpperCase()}`;
  } catch (e) {}
  return String(range || "").toLowerCase() === "1d" ? "INTRADAY" : `HISTORICAL ${String(range || "").toUpperCase()}`;
}
/** Seed theses are static: drop sentences whose price levels are >10% away from the current price. */
function _rt24Th(a) {
  const th = String((a && a.th) || "");
  let px = null; try { const v = P[a.tk] && P[a.tk].p; if ((hasSyncedQuote(a.tk) || hasRetainedQuote(a.tk)) && v > 0) px = v; } catch (e) {}
  if (!(px > 0) || !/\$/.test(th)) return th;
  const sents = th.split(/(?<=[.!?])\s+/);
  const keep = sents.filter(sn => {
    let stale = false;
    for (const m of sn.matchAll(/\$\s?(\d+(?:[.,]\d+)?)(?:\s?[-–]\s?\$?(\d+(?:[.,]\d+)?))?\s?([KkMmBb])?\b/g)) {
      const mul = /k/i.test(m[3] || "") ? 1e3 : /m/i.test(m[3] || "") ? 1e6 : /b/i.test(m[3] || "") ? 1e9 : 1;
      const v = [m[1], m[2]].filter(Boolean).map(x => parseFloat(x.replace(/,/g, "")) * mul);
      const levels = v.filter(x => x >= px * 0.5 && x <= px * 2);
      if (levels.length && !levels.some(x => Math.abs(x - px) / px <= 0.10)) stale = true;
    }
    return !stale;
  });
  return keep.join(" ").trim() || th;
}
function _rt24Copy(t) {
  return typeof t === "string" ? t.replace(/Market Regime Update for (?:Ticker )?([A-Z0-9.\-^=]{1,12})/g, "Market regime: $1") : t;
}
(function _rt24Init() {
  if (document.getElementById("rt24-css")) return;
  const st = document.createElement("style"); st.id = "rt24-css";
  st.textContent = `
@media (max-width:767px){
 .sov .sbox{box-sizing:border-box;width:auto;max-width:calc(100vw - 16px);margin:0 8px}
 .sov .sbox .sr-only{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;clip:rect(0 0 0 0)!important;white-space:nowrap}
 .sov .sbox-inp-wrap{min-width:0}.sov .sinp{min-width:0;flex:1 1 auto}
 .sov .sres{flex-wrap:wrap;min-width:0}.sov .sres-nm,.sov .sres-d{min-width:0;overflow-wrap:anywhere}
 .sov .sbox-chips{overflow-x:auto;flex-wrap:nowrap;scrollbar-width:none}
 .rt24-cmp{min-width:0!important;table-layout:auto}\n .rt24-cmp td,.rt24-cmp th{white-space:normal;overflow:visible!important;text-overflow:clip!important;max-width:none!important;padding:5px 4px!important;font-size:10px;word-break:normal}\n .rt24-cmp .asof-tag{display:block;font-size:8px}
}`;
  document.head.appendChild(st);
  // Hover-style tooltips can stick on touch: blur the focused control on scroll or a tap elsewhere.
  const drop = ev => { try { const a = document.activeElement; if (a && a !== document.body && !(ev && ev.target && a.contains(ev.target)) && !/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) a.blur(); } catch (e) {} };
  window.addEventListener("scroll", drop, { passive: true, capture: true });
  document.addEventListener("touchstart", drop, { passive: true });
})();
"""
R('rt24 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat22') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat22', 'app.js?v=chat23')
for bad in ['s.cat.toUpperCase().slice(0,6)', '← BACK TO NEWS']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
