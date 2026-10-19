#!/usr/bin/env python3
"""patch_rt54.py: client patch. Reads app.js?v=chatNN and writes chatNN+1.

The known live base is chat63 (rt53 and bb5 already on the page):
  app.js md5 4b094d30cc5070c2ca44d7979452d648
  index.html md5 0e595097e68bcf2f8c0c90395add2880
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

1) News tags. Crypto still wins first. A company, earnings, guidance, stock or
analyst story about an energy or mining name (BP, Shell, Exxon, Chevron, miners)
is Stocks, the site's existing equities tag. A story about the commodity itself
(oil price, OPEC, supply, barrels, Brent, WTI) stays Commodities.

2) Guest Ask paywall. The title sat on the left edge of an unpadded card while
the paragraph was a centered 360px column. Header, paragraph and card share one
left edge, and a tall card scrolls instead of clipping the title.

3) Beta. Both screens already show Yahoo summaryDetail.beta (5y monthly) when
the lookup works, so this does not add a source. The fit sheet reads the
regime-fit inputs row key === "sensitivity" and renders an em dash when value
is null (bb5b). The stock page keeps GET /api/financials valuation.beta and
labels it "5y monthly beta, Yahoo", including when that value is null. Client
desk figures (the 1.62 map, a forced SPY 1.0, a fallback of 1) are not shown.

4) The markets panel subtitle uses the same trading-now sentence as the header.

Usage: python3 patch_rt54.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "4b094d30cc5070c2ca44d7979452d648"
EXPECT_INDEX_MD5 = "0e595097e68bcf2f8c0c90395add2880"
NEED_MARKER = "function _rt53bTag("

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt54 ──' in s: already('rt54 already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
md5 = hashlib.md5(raw).hexdigest()
imd5 = hashlib.md5(raw_idx).hexdigest()
if md5 != EXPECT_APP_MD5:
    print('WARN md5 app.js: have %s expected %s (anchors still decide)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    print('WARN md5 index.html: have %s expected %s (anchors still decide)' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust matched %d times' % len(v))
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
print('base:', base, 'app.md5', md5, 'index.md5', imd5, '->', nxt)

def sub1(src, old, new, label):
    c = src.count(old)
    if c != 1: die('%s matched %d times' % (label, c))
    return src.replace(old, new, 1)

# 1) Tags. Crypto stays first. Company stories about energy and mining names
# are Stocks before a commodity keyword (oil, crude, brent) can outscore them.
s = sub1(s,
'''  if (hit(["bitcoin", "crypto", "cryptocurrency", "cryptocurrencies", "ethereum", "btc", "eth", "blockchain", "solana", "xrp", "dogecoin", "stablecoin", "binance", "coinbase", "defi", "altcoin"])) return "Crypto";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};''',
'''  if (hit(["bitcoin", "crypto", "cryptocurrency", "cryptocurrencies", "ethereum", "btc", "eth", "blockchain", "solana", "xrp", "dogecoin", "stablecoin", "binance", "coinbase", "defi", "altcoin"])) return "Crypto";
  // A named energy or mining company, told as a company story, is Stocks.
  // The commodity itself (price, OPEC, barrels, Brent, WTI) falls through to the rules below.
  if (hit(["bp", "shell", "exxon", "exxonmobil", "exxon mobil", "chevron", "conocophillips", "conoco", "totalenergies", "total energies", "equinor", "eni", "repsol", "woodside", "occidental", "bhp", "rio tinto", "vale", "glencore", "anglo american", "freeport", "newmont", "barrick", "southern copper", "antofagasta", "teck"])
      && hit(["guidance", "earnings", "revenue", "profit", "stock", "shares", "analyst", "bull case", "bear case", "upgrade", "downgrade", "price target", "dividend", "results", "output", "quarterly"])) return "Stocks";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};''',
'tag company stories')

# 2) Ask paywall header. One left edge for the kicker, the title and the paragraph.
s = sub1(s,
'''  ov.style.cssText='position:fixed;inset:0;z-index:950;background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(12px)';
  ov.innerHTML = `
    <div class="premium-gate" style="max-width:480px">
      <div class="eyebrow">PREMIUM</div>
      <h2 id="login-gate-title" tabindex="-1">${featureName}</h2>
      <p style="color:var(--text-secondary); max-width:360px; margin:12px auto 16px;">
        Free users keep tape, regime, desk brief &amp; Lab. This feature needs Premium (£15/mo · live Stripe).
      </p>''',
'''  ov.style.cssText='position:fixed;inset:0;z-index:950;background:rgba(0,0,0,0.88);display:flex;overflow:auto;padding:16px;backdrop-filter:blur(12px)';
  ov.innerHTML = `
    <div class="premium-gate" style="width:min(480px,100%);max-width:480px;box-sizing:border-box;margin:auto;flex:0 0 auto;padding:22px 20px 18px;text-align:left">
      <div class="eyebrow" style="margin:0 0 8px;padding:0;font-family:var(--mn);font-size:10px;font-weight:700;letter-spacing:0.16em;line-height:1.2;color:var(--gd);text-align:left">PREMIUM</div>
      <h2 id="login-gate-title" tabindex="-1" style="margin:0;padding:0;font-size:22px;line-height:1.25;letter-spacing:-0.02em;text-align:left">${featureName}</h2>
      <p style="color:var(--text-secondary);max-width:none;margin:10px 0 16px;text-align:left;line-height:1.5">
        Free users keep tape, regime, desk brief &amp; Lab. This feature needs Premium (£15/mo · live Stripe).
      </p>''',
'ask paywall header')

# 3) Beta. Sensitivity row: a null value is an em dash, never a desk constant.
s = sub1(s,
'''function _rt53FitInputLine(inp) {
  if (!inp) return "";
  // The last row is a clamp. It is usually 0, and a zero clamp is not a market input.
  if (String(inp.key || "") === "bounds" && Number(inp.contribution) === 0) return "";
  var missing = inp.value == null || inp.value === "";
  var val = missing ? "\\u2014" : String(inp.value);
  if (!missing && inp.unit) val += " " + String(inp.unit);''',
'''function _rt53FitInputLine(inp) {
  if (!inp) return "";
  // The last row is a clamp. It is usually 0, and a zero clamp is not a market input.
  if (String(inp.key || "") === "bounds" && Number(inp.contribution) === 0) return "";
  var sens = String(inp.key || "") === "sensitivity";
  var raw = inp.value;
  var missing = raw == null || raw === "" || (typeof raw === "number" && !isFinite(raw));
  var val;
  if (missing) val = "\\u2014";
  else if (sens) {
    var n = Number(raw);
    // Yahoo 5y monthly beta from this row only. A failed lookup (null) stays a dash.
    val = isFinite(n) ? n.toFixed(2) : "\\u2014";
    if (val === "\\u2014") missing = true;
  } else val = String(raw);
  if (!missing && inp.unit) val += " " + String(inp.unit);''',
'fit sensitivity dash')

# Stock page: valuation.beta, with the static Yahoo label, dash when null.
s = sub1(s,
'''${a.beta != null && a.beta !== "" && a.beta !== "\u2014" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>` : ""}''',
'''${a.cat === "Stock" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${_rt54BetaTxt(a.beta)}</span><div style="font-size:8px;color:var(--t3);margin-top:2px;letter-spacing:0.02em">5y monthly beta, Yahoo</div></div>` : (a.beta != null && a.beta !== "" && a.beta !== "\u2014" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>` : "")}''',
'desktop stock beta label')

s = sub1(s,
'''[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.beta},{l:"Sentiment",v:a.se}]''',
'''[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.cat==="Stock"?_rt54BetaCell(a.beta):a.beta},{l:"Sentiment",v:a.se}]''',
'mobile stock beta label')

s = sub1(s,
'''['Beta', fmt(m.beta)],''',
'''['Beta', _rt54BetaTxt(data.valuation && data.valuation.beta) + ' \\u00b7 5y monthly beta, Yahoo'],''',
'financials beta from valuation')

# The blanking pass already set stock betas to a dash. This line put 1.0 back on SPY.
s = sub1(s,
'''try { const spy = A.find(a => a.tk === "SPY"); if (spy) spy.beta = 1.0; } catch (e) {}''',
'''/* rt54: SPY uses valuation.beta, the same Yahoo figure as every other stock. */''',
'spy client beta')

s = sub1(s,
'''rows.push([`High beta (${_rt52BetaOf(tk, a)}, desk reference) while the regime avoids high-beta`, -12]);''',
'''rows.push([`High beta while the regime avoids high-beta`, -12]);''',
'desk reference beta copy')

s = sub1(s,
'''    let dayPnl = 0, betaWt = 0, total = 0, liveTotal = 0, liveN = 0;''',
'''    let dayPnl = 0, betaWt = 0, betaBase = 0, total = 0, liveTotal = 0, liveN = 0;''',
'portfolio beta base')
s = sub1(s,
'''      if (m.live) betaWt += val * _deskBeta(a || pos.tk, 1);''',
'''      const bN = _rt54BetaNum(a || pos.tk);
      if (m.live && bN != null) { betaWt += val * bN; betaBase += val; }''',
'portfolio beta weight')
s = sub1(s,
'''    const portBeta = liveTotal ? (betaWt / liveTotal).toFixed(2) : "\u2014";''',
'''    const portBeta = betaBase ? (betaWt / betaBase).toFixed(2) : "\u2014";''',
'portfolio beta text')

s = sub1(s,
'''  let totalVal = 0, weightedSc = 0, bullishW = 0, bearishW = 0, beatSpy = 0, weightedBeta = 0;''',
'''  let totalVal = 0, weightedSc = 0, bullishW = 0, bearishW = 0, beatSpy = 0, weightedBeta = 0, betaW = 0;''',
'scan beta weight')
s = sub1(s,
'''    const beta = parseFloat(String(r.a?.beta || "1").replace(/x/i, "")) || 1;
    weightedBeta += beta * w;''',
'''    const bN = _rt54BetaNum(r.a);
    if (bN != null) { weightedBeta += bN * w; betaW += w; }''',
'scan beta sum')
s = sub1(s,
'''weightedBeta: weightedBeta.toFixed(2),''',
'''weightedBeta: betaW ? (weightedBeta / betaW).toFixed(2) : "\\u2014",''',
'scan beta text')

s = sub1(s,
'''  const beta = _deskBeta(_labTk, 1);
  const oilImp = (sc.oil * 0.15 * beta).toFixed(1);
  const spyImp = (sc.spy * beta * 0.5).toFixed(1);
  const col = parseFloat(oilImp) >= 2 ? "var(--gn)" : parseFloat(oilImp) <= -2 ? "var(--rd)" : "var(--gd)";''',
'''  const beta = _rt54BetaNum(_labTk);
  const oilImp = beta == null ? null : sc.oil * 0.15 * beta;
  const spyImp = beta == null ? null : sc.spy * beta * 0.5;
  const col = oilImp == null ? "var(--t3)" : oilImp >= 2 ? "var(--gn)" : oilImp <= -2 ? "var(--rd)" : "var(--gd)";''',
'geo scenario beta')
s = sub1(s,
'''    <div class="lab-proj-val" style="color:${col}">${parseFloat(oilImp) >= 0 ? "+" : ""}${oilImp}%</div>
    <div class="lab-proj-sub">${sc.lbl} · oil channel · β ${beta.toFixed(2)} · SPY est ${spyImp}%</div>''',
'''    <div class="lab-proj-val" style="color:${col}">${oilImp == null ? "\\u2014" : (oilImp >= 0 ? "+" : "") + oilImp.toFixed(1) + "%"}</div>
    <div class="lab-proj-sub">${sc.lbl} · oil channel · β ${beta == null ? "\\u2014" : beta.toFixed(2)} · 5y monthly beta, Yahoo · SPY est ${spyImp == null ? "\\u2014" : spyImp.toFixed(1) + "%"}</div>''',
'geo scenario label')

s = sub1(s,
'''function _renderLabScenarioInner(){
  const beta=_deskBeta(_labTk,1);
  const {wR,wN,wO}=_labScenarioWeights();
  // Simple educational model: higher beta amplifies risk-on/off swings (not a forecast)
  const proj=(wR*beta*4.2+wN*0.2+wO*beta*-4.8);
  const p=proj.toFixed(1);
  const col=proj>=1?"var(--gn)":proj<=-1?"var(--rd)":"var(--gd)";
  const read=proj>=2''',
'''function _renderLabScenarioInner(){
  const beta=_rt54BetaNum(_labTk);
  const {wR,wN,wO}=_labScenarioWeights();
  // Illustrative only, and only with the Yahoo beta already on the name.
  const proj=beta==null?null:(wR*beta*4.2+wN*0.2+wO*beta*-4.8);
  const p=proj==null?"\\u2014":proj.toFixed(1);
  const col=proj==null?"var(--t3)":proj>=1?"var(--gn)":proj<=-1?"var(--rd)":"var(--gd)";
  const read=proj==null?"Beta is not on this name, so the blender shows a dash instead of a guessed swing.":proj>=2''',
'lab blender beta')
s = sub1(s,
'''  return`<div class="lab-proj-val" style="color:${col}">${proj>=0?"+":""}${p}%</div>
    <div class="lab-proj-sub"><strong>MODEL · illustrative 30-day impulse</strong> for ${_labTk} (β ${beta.toFixed(2)})</div>''',
'''  return`<div class="lab-proj-val" style="color:${col}">${proj==null?"\\u2014":(proj>=0?"+":"")+p+"%"}</div>
    <div class="lab-proj-sub"><strong>MODEL · illustrative 30-day impulse</strong> for ${_labTk} (β ${beta==null?"\\u2014":beta.toFixed(2)} · 5y monthly beta, Yahoo)</div>''',
'lab blender label')

s = sub1(s,
'''  const betaN=_deskBeta(a||_labTk,1);
  if(betaN>=1.3) tips.push(`Beta ~${betaN.toFixed(2)}: expect amplified moves when you slide Risk-On / Risk-Off.`);
  else if(betaN<0.8) tips.push(`Beta ~${betaN.toFixed(2)}: more defensive — scenario blender swings will be smaller than high-β names.`);''',
'''  const betaN=_rt54BetaNum(a||_labTk);
  if(betaN!=null&&betaN>=1.3) tips.push(`Beta ~${betaN.toFixed(2)} · 5y monthly beta, Yahoo: expect amplified moves when you slide Risk-On / Risk-Off.`);
  else if(betaN!=null&&betaN<0.8) tips.push(`Beta ~${betaN.toFixed(2)} · 5y monthly beta, Yahoo: more defensive \\u2014 scenario blender swings will be smaller than high-\\u03b2 names.`);''',
'lab look-for beta')

# 4) Markets panel uses the same trading-now sentence as the header.
s = sub1(s,
'''  document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${_rt42Ready() ? `${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live` : "syncing…"}`;''',
'''  document.getElementById('p1sub').textContent = (typeof _rt51Label === "function") ? _rt51Label() : `${tickers.length} of ${A.length} · ${_rt42Ready() ? `${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live` : "syncing…"}`;''',
'markets trading-now line')

BLOCK = r'''
// ── rt54 ── Shown beta is the Yahoo figure already on the name. A missing one is a dash.
function _rt54BetaNum(aOrTk) {
  var a = typeof aOrTk === "string" ? ((typeof A !== "undefined" && A.find(function (x) { return x.tk === aOrTk; })) || null) : aOrTk;
  if (!a || a.beta == null) return null;
  var n = parseFloat(String(a.beta).replace(/x/i, ""));
  return isFinite(n) ? n : null;
}
function _rt54BetaTxt(v) {
  var n = typeof v === "number" ? v : parseFloat(String(v == null ? "" : v).replace(/x/i, ""));
  return isFinite(n) ? n.toFixed(2) : "\u2014";
}
function _rt54BetaCell(v) {
  return _rt54BetaTxt(v) + '<div style="font-family:var(--mn);font-size:8px;font-weight:500;color:var(--t3);letter-spacing:0.02em;margin-top:2px">5y monthly beta, Yahoo</div>';
}
'''
if '// ── rt54 ──' in s: die('rt54 marker landed twice')
s = s.rstrip('\n') + '\n' + BLOCK
h = sub1(h, 'app.js?v=' + base + '"', 'app.js?v=' + nxt + '"', 'cache bust')

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
    t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if r.returncode: die('node --check failed: ' + (r.stderr or '')[:500])
print('OK rt54: %s -> %s; node --check passed%s' % (base, nxt, ' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
