#!/usr/bin/env python3
"""patch_rt33.py — chat29 -> chat30. Stacks on rt32 output (app.js af390ee5). Client + index.html cache bust.
Built-in P/E / market cap / beta seed figures are hidden and replaced from /api/financials (shared _finCache);
lens + committee AI context gets the live valuation; AI P/E and market-cap claims that don't match are dropped;
signal matching uses whole-word ticker matches (MU no longer matches 'MOMENTUM').
Usage: python3 patch_rt33.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt33)' in s: die('rt33 already applied')
if 'REALTIME PRICE LAYER (rt32)' not in s: die('base is not rt32 output')
if 'app.js?v=chat29' not in h: die('index.html is not chat29')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt32)', '// REALTIME PRICE LAYER (rt33)')
R('sig match', '    if (sa.includes(up) || sx.includes(up) || sx.includes("$" + up)) return true;',
  '    if (_rt33Has(sa, up) || _rt33Has(sx, up)) return true;')
R('lens ctx', 'Beta: ${a.beta || "—"} | P/E: ${a.pe || "—"} | Market cap: ${a.mc || "—"}',
  'Beta: ${a.beta || "—"} | P/E: ${a.pe || "—"} | Market cap: ${a.mc || "—"}${_rt33Ctx(tk)}')
R('prefetch apply', 'async function _prefetchLensData(tk) {\n  const a = A.find(x => x.tk === tk);\n  if (!a || a.cat !== "Stock") return;',
  'async function _prefetchLensData(tk) {\n  const a = A.find(x => x.tk === tk);\n  if (!a || a.cat !== "Stock") return;\n  await _rt33Ensure(tk, true);')
R('heat seed', '_parseMc(a.mc)', '_parseMc(a._mc0 || a.mc)', 2)
R('open desk', '  _rt30Opened(tk);\n  // Surface analysis panel', '  _rt30Opened(tk);\n  _rt33Ensure(tk);\n  // Surface analysis panel')
R('open phone', '_rt27Url(tk);_rt30Cancel();if(selTk!==tk){', '_rt27Url(tk);_rt30Cancel();_rt33Ensure(tk);if(selTk!==tk){')
R('txt guard', 'function _rt32Txt(t, tk) {\n  if (typeof t !== "string") return t;\n  let s = _rt31Neg(t);',
  'function _rt32Txt(t, tk) {\n  if (typeof t !== "string") return t;\n  let s = _rt33Guard(_rt31Neg(t), tk);')
BLOCK = r"""// ── rt33: live fundamentals replace seed figures; AI valuation guard; whole-word signal match ──
(() => { try { A.forEach(a => { if (a.cat === "Stock") { a._mc0 = a.mc; a._pe0 = a.pe; a.pe = "—"; a.mc = "—"; a.beta = "—"; } }); } catch (e) {} })();
const _rt33P = {};
// No built-in seed prices: a price shows only once a feed (or a chart close) supplies it
(() => { try { Object.keys(P).forEach(k => { if (!liveSymbols.has(k)) { P[k] = { p: null, c: null }; if (BASE[k]) BASE[k] = { p: null, c: 0 }; } }); } catch (e) {} })();
function _rt33HeadOk(x) {
  const m = typeof x === "string" && x.match(/^Market regime: (.+)$/);
  if (!m) return x;
  const v = m[1].trim();
  let live = ""; try { live = _computeRegimeEngine().label || ""; } catch (e) {}
  const ok = (typeof A !== "undefined" && A.some(a => a.tk === v)) || /^(Risk[- ](On|Off)|Transition|Neutral|Defensive|Mixed|Cautious|Constructive)\b/i.test(v);
  return ok ? x : (live ? `Market regime: ${live}` : "Market regime");
}
function _rt33Old(b) {
  try { const d = b && b.date && Date.parse(b.date); return !!d && Date.now() - d > 4 * 864e5; } catch (e) { return false; }
}
var _rt33Meta = {};
function _rt33Close(tk) {
  try {
    if (liveSymbols.has(tk)) return false;
    const yh = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk, m = _rt33Meta[yh];
    let p = m && m.regularMarketPrice, ts = m && m.regularMarketTime;
    if (!(p > 0)) { const h = (HIST[tk] || []).filter(v => typeof v === "number" && v > 0); p = h[h.length - 1]; ts = null; }
    if (!(p > 0)) return false;
    // Last close from the chart: price only — no change basis, so the change cell stays "—"
    return _applyLiveQuote(tk, { p, ts: ts || undefined, marketClosed: true, source: "yahoo-chart-close", name: (m && (m.shortName || m.longName)) || "" }, "yahoo-chart-close");
  } catch (e) { return false; }
}
async function _rt33CloseFallback(list) {
  const vis = tk => { try { return document.querySelector(`[data-spark-tk="${tk}"],[data-price-card="${tk}"]`) ? 0 : 1; } catch (e) { return 1; } };
  const got = [], todo = list.filter(tk => !liveSymbols.has(tk)).sort((a, b) => vis(a) - vis(b)).slice(0, 60);
  for (let i = 0; i < todo.length; i += 4) {
    await Promise.all(todo.slice(i, i + 4).map(async tk => {
      const yh = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk;
      if (!_rt33Meta[yh]) { try { const s = await fetchYahooIntraday(yh); if (s && s.length >= 5 && !((HIST[tk] || []).length >= 5)) HIST[tk] = s.slice(-60); } catch (e) {} }
      if (_rt33Close(tk)) got.push(tk);
    }));
  }
  if (got.length) { try { _patchCuratedPrices(); } catch (e) {} try { got.forEach(_patchSparkline); } catch (e) {} }
  return got;
}
function _rt33Has(s, t) {
  if (!t || t.length < 1) return false;
  const e = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^A-Z0-9])\\$?${e}(?![A-Z0-9])`).test(String(s || "").toUpperCase());
}
function _rt33Val(tk) { const d = _finCache[tk]; return d && d.valuation ? d.valuation : null; }
function _rt33Mc(v) { if (v == null || !isFinite(v) || v <= 0) return "—"; return "$" + (v >= 1e12 ? (v / 1e12).toFixed(2) + "T" : v >= 1e9 ? (v / 1e9).toFixed(1) + "B" : (v / 1e6).toFixed(0) + "M"); }
function _rt33Apply(tk) {
  const a = A.find(x => x.tk === tk), v = _rt33Val(tk);
  if (!a || a.cat !== "Stock" || !v) return false;
  a.pe = v.pe > 0 ? v.pe.toFixed(1) + "x" : "—";
  a.mc = _rt33Mc(v.marketCap);
  a.beta = v.beta != null && isFinite(v.beta) ? Number(v.beta).toFixed(2) : "—";
  return true;
}
function _rt33Ensure(tk, wait) {
  const a = A.find(x => x.tk === tk);
  if (!a || a.cat !== "Stock") return Promise.resolve();
  if (_finCache[tk]) { _rt33Apply(tk); return Promise.resolve(); }
  if (!_rt33P[tk]) _rt33P[tk] = fetch("/api/financials?symbol=" + encodeURIComponent(tk), { signal: AbortSignal.timeout(10000) })
    .then(r => r.ok ? r.json() : null).then(d => {
      if (d) _finCache[tk] = d;
      if (_rt33Apply(tk) && !wait) {
        const cur = IS_DESKTOP() ? termSelTk : selTk;
        if (cur === tk) { try { if (IS_DESKTOP()) { if (aTab === "ov") renderP2(); } else if (pg === "anlz" && aTab === "ov") renderMain(); } catch (e) {} }
      }
    }).catch(() => {}).finally(() => { delete _rt33P[tk]; });
  return _rt33P[tk];
}
function _rt33Ctx(tk) {
  const v = _rt33Val(tk);
  if (!v) return "\nValuation: live figures unavailable — do not quote P/E, market cap or other valuation numbers.";
  const f = (x, k) => x == null || !isFinite(x) ? "—" : k === "x" ? Number(x).toFixed(1) + "x" : k === "%" ? (x * 100).toFixed(2) + "%" : _rt33Mc(x);
  return `\nLive valuation (${v.source}): P/E ${f(v.pe, "x")} | Forward P/E ${f(v.forwardPe, "x")} | P/S ${f(v.ps, "x")} | P/B ${f(v.pb, "x")} | EV/EBITDA ${f(v.evEbitda, "x")} | Market cap ${f(v.marketCap)} | Dividend yield ${f(v.divYield, "%")}. Quote only these figures.`;
}
function _rt33Guard(s, tk) {
  if (typeof s !== "string" || !/P\/E|market cap/i.test(s)) return s;
  const v = tk ? _rt33Val(tk) : null;
  const near = (n, live, tol) => live != null && isFinite(live) && live > 0 && Math.abs(n - live) / live <= tol;
  const keep = p => {
    const pe = p.match(/\bP\/E(?:\s+ratio)?(?:\s+(?:of|at|is|near|around|about|~))*\s*~?(\d+(?:\.\d+)?)\s*x?/i);
    if (pe) { const n = +pe[1]; if (!(v && (near(n, v.pe, 0.12) || near(n, v.forwardPe, 0.12)))) return false; }
    const mc = p.match(/market\s+cap(?:italisation|italization)?(?:\s+(?:of|at|is|near|around|about|approximately|roughly|~))*\s*~?\$?\s*(\d+(?:\.\d+)?)\s*(T|B|M|trillion|billion|million)\b/i);
    if (mc) { const u = mc[2][0].toUpperCase(), n = +mc[1] * (u === "T" ? 1e12 : u === "B" ? 1e9 : 1e6); if (!(v && near(n, v.marketCap, 0.15))) return false; }
    return true;
  };
  const parts = _rt28Split(s);
  const out = parts.filter(keep);
  return out.length === parts.length ? s : out.join(" ");
}
"""
R('meta1', '    const result=data?.chart?.result?.[0];\n    const closes=result?.indicators?.quote?.[0]?.close;\n    if(Array.isArray(closes)){\n      const clean=closes.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);\n      if(clean.length>=5)return clean;',
  '    const result=data?.chart?.result?.[0];\n    if(result?.meta)_rt33Meta[yhSym]=result.meta;\n    const closes=result?.indicators?.quote?.[0]?.close;\n    if(Array.isArray(closes)){\n      const clean=closes.filter(v=>typeof v==="number"&&isFinite(v)&&v>0);\n      if(clean.length>=5)return clean;')
R('meta2', '    const closes=data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close;', '    if(data?.chart?.result?.[0]?.meta&&!_rt33Meta[yhSym])_rt33Meta[yhSym]=data.chart.result[0].meta;\n    const closes=data?.chart?.result?.[0]?.indicators?.quote?.[0]?.close;')
R('yq fallback', '  if (missing.length && typeof _fetchFinnhubPriceFallback === "function") {\n    hits += await _fetchFinnhubPriceFallback(missing);',
  '  if (missing.length) { const got = await _rt33CloseFallback(missing); hits += got.length; got.forEach(tk => missing.splice(missing.indexOf(tk), 1)); }\n  if (missing.length && typeof _fetchFinnhubPriceFallback === "function") {\n    hits += await _fetchFinnhubPriceFallback(missing);')
R('sig cat', '    if (cat && s.tg.toLowerCase().includes(cat)) return true;', '    if (cat && cat !== "stock" && s.tg.toLowerCase().includes(cat)) return true;')
R('dominance guard', '      _cryptoDominance={btc:gd.data?.market_cap_percentage?.btc?.toFixed(1),eth:gd.data?.market_cap_percentage?.eth?.toFixed(1),totalMcap:gd.data?.total_market_cap?.usd};',
  '      {const _rt33d={btc:gd.data?.market_cap_percentage?.btc?.toFixed(1),eth:gd.data?.market_cap_percentage?.eth?.toFixed(1),totalMcap:gd.data?.total_market_cap?.usd};if(_rt33d.btc!=null&&_rt33d.eth!=null)_cryptoDominance=_rt33d;}')
R('crypto retry', """      <div style="font-family:var(--sn);font-size:13px;color:${_cryptoError?'var(--rd)':'var(--t2)'}">${_cryptoError?'Crypto data delayed, retrying\\u2026':'Crypto rankings are ready to load.'}</div>
      <button type="button" onclick="fetchCryptoMarket()\"""",
  """      <div style="font-family:var(--sn);font-size:13px;color:${_cryptoError?'var(--rd)':'var(--t2)'}">${_cryptoMktLoading?'Loading CoinGecko rankings\\u2026':_cryptoError?'CoinGecko did not return rankings. It retries automatically every minute.':'Crypto rankings are ready to load.'}</div>
      <button type="button" ${_cryptoMktLoading?'disabled':''} onclick="fetchCryptoMarket();setTimeout(()=>{try{if(pg==='crypto')renderMain();}catch(e){}},0)\"""")
R('retry label', "${_cryptoError?'Retry':'Load Rankings'}</button>", "${_cryptoMktLoading?'Loading\\u2026':_cryptoError?'Retry now':'Load Rankings'}</button>")
R('head valid', '    x = lbl ? `Market regime: ${lbl}` : x;\n  }\n  return x;\n}', '    x = lbl ? `Market regime: ${lbl}` : x;\n  }\n  return _rt33HeadOk(x);\n}')
R('typo url', 'async function lookupTicker(tk){', 'async function lookupTicker(tk){\n  try{const _u=String(tk||"").trim().toUpperCase();if(/^[A-Z0-9.\\-=^]{1,12}$/.test(_u))_rt27Url(_u);}catch(e){}')
R('alert check', '  showToast(`Alert set: ${sym} ${d==="above"?"≥":"≤"} $${t}`,"var(--gd)");', '  showToast(`Alert set: ${sym} ${d==="above"?"≥":"≤"} $${t}`,"var(--gd)");\n  setTimeout(()=>{try{checkAlerts();if(IS_DESKTOP()&&termSelTk)renderP2();else _refreshView();}catch(e){}},60);')
R('brief stale', '  const b = _rt31Brief(_brief);\n  const vc = b.houseView', '  if (_rt33Old(_brief)) return _renderBriefTeaser();\n  const b = _rt31Brief(_brief);\n  const vc = b.houseView')
R('conf 0', '${b.confidence != null ? `<span style="font-family:var(--mn);font-size:10px;color:var(--t3)">Confidence ${b.confidence}</span>` : ""}', '${b.confidence > 0 ? `<span style="font-family:var(--mn);font-size:10px;color:var(--t3)">Confidence ${b.confidence}</span>` : ""}')
R('val nm', '  if (k === "x") return v > 0 ? v.toFixed(1) + "×" : "—";', '  if (k === "x") return v > 0 && v < 250 ? v.toFixed(1) + "×" : "n/m";')
R('rt33 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat29', 'app.js?v=chat30')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
