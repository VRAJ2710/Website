#!/usr/bin/env python3
"""patch_rt54.py: client patch. Reads app.js?v=chatNN and writes chatNN+1.

The known live base is chat63 (rt53 and bb5 already on the page):
  app.js md5 4b094d30cc5070c2ca44d7979452d648
  index.html md5 0e595097e68bcf2f8c0c90395add2880
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

1) News tags. Crypto wins only when the story is really about crypto. A company
stock story is Stocks even when it mentions oil: a Stock/Shares word with an
exchange:ticker such as (LSE:BP.) or (NYSE:XOM), a known equity ticker or
company name, or earnings/guidance wording about a company. A story about the
commodity itself (oil price, OPEC, barrels, Brent, WTI) stays Commodities.

2) Newsroom counts and the Academy intro. Desktop All was counting every loaded
headline and painting 18. The cards and the "shown" count now come from the
same list, so All renders every loaded card (the 80). The "In the news" intro
is the Academy lesson, not a block on /, /news/ or /geo/; the sentence says so.

3) One chip vocabulary on filters, the market table and cards: Stocks,
Commodities, Crypto, Forex, Macro, Geopolitics, Regulation, Other. Earnings
and Central Bank fold into Stocks and Macro. A filter matches the badge the
card shows, not the feed category or a keyword haystack.

4) Ask. Streamed tokens are joined without a line break inside a word, and an
entity such as "Micron Technology (MU)" stays one inline run.

5) Guest Ask paywall. The PREMIUM kicker shares the card's horizontal padding
with the title and the paragraph.

6) Guest home. An inline head script marks the document when JS runs, and CSS
hides the static fallback. The nodes stay in the DOM for no-JS visitors. The
mounted app does not paint the unstyled front-door letter; guests get the
styled home.

7) Quote badges, per instrument. A /api/yahoo-quote item may carry status
(fresh, delayed, stale, closed or quiet), delayMin, note and nextOpen.
fe64_ wrappers sit on _quoteMetaBase and on the quote-meta function after
the rt43 wrapper. Closed shows CLOSED plus that item's note, or
"opens HH:MM UK" from nextOpen (Europe/London). Quiet shows the note.
Delayed shows the note. Only stale shows STALE. Fresh keeps today's live
or as-of label. A missing status keeps today's behaviour, including when
the note happens to contain the word quiet. This never paints a site-wide
"markets closed".

8) CoinGecko. A stale /api/coingecko reply keeps its JSON and sets
X-Dispatch-Data-Status: stale plus X-Dispatch-As-Of (the older
X-Dispatch-Data-As-Of header still counts). Rankings, market cap and
dominance then say "as of HH:MM UK". A fresh reply is unchanged. Callers that
only read the JSON are unchanged.

9) Beta. Both screens already show Yahoo summaryDetail.beta (5y monthly) when
the lookup works, so this does not add a source. The fit sheet reads the
regime-fit inputs row key === "sensitivity" and renders an em dash when value
is null (bb5b). The stock page keeps GET /api/financials valuation.beta and
labels it "5y monthly beta, Yahoo", including when that value is null. Client
desk figures (the 1.62 map, a forced SPY 1.0, a fallback of 1) are not shown.

10) The markets panel subtitle uses the same trading-now sentence as the header.

No server file is changed. The client reads bb5c, bb5d and bb5e fields when
they are present. Guest ?diag=1 returning 200 is a server item.
deploy/check_rt54_quote.js mocks the badge and the CoinGecko headers.

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

def subn(src, old, new, label, n):
    c = src.count(old)
    if c != n: die('%s matched %d times, wanted %d' % (label, c, n))
    return src.replace(old, new)

# 1) Tags. Crypto only when the story is really about crypto. A company-stock
# story is Stocks before a commodity keyword (oil, crude, brent) can win.
s = sub1(s,
'''  if (hit(["bitcoin", "crypto", "cryptocurrency", "cryptocurrencies", "ethereum", "btc", "eth", "blockchain", "solana", "xrp", "dogecoin", "stablecoin", "binance", "coinbase", "defi", "altcoin"])) return "Crypto";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};''',
'''  if (fe64_cryptoStory(low, hit)) return "Crypto";
  if (fe64_equityStory(low, hit)) return "Stocks";
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
      <h2 id="login-gate-title" tabindex="-1" style="margin:0;padding:0;font-size:22px;line-height:1.25;letter-spacing:-0.02em;text-align:left;outline:none">${featureName}</h2>
      <p style="color:var(--text-secondary);max-width:none;margin:10px 0 16px;text-align:left;line-height:1.5">
        Free users keep tape, regime, desk brief &amp; Lab. This feature needs Premium (£15/month, cancel anytime).
      </p>''',
'ask paywall header')
s = sub1(s,
'''  _openA11yDialog(ov,()=>_closeA11yDialog(ov),"#login-gate-title");''',
'''  ov.tabIndex=-1;ov.style.outline="none";
  _openA11yDialog(ov,()=>_closeA11yDialog(ov),null);
  setTimeout(function(){ try { ov.focus(); } catch (e) {} }, 40);''',
'paywall focus stays on the dialog')

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
'''${a.cat === "Stock" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${fe64_betaTxt(a.beta)}</span><div style="font-size:8px;color:var(--t3);margin-top:2px;letter-spacing:0.02em">5y monthly beta, Yahoo</div></div>` : (a.beta != null && a.beta !== "" && a.beta !== "\u2014" ? `<div style="font-family:var(--mn);font-size:9.5px;color:var(--t2)">Beta: <span style="color:var(--tx)">${a.beta}</span></div>` : "")}''',
'desktop stock beta label')

s = sub1(s,
'''[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.beta},{l:"Sentiment",v:a.se}]''',
'''[{l:"P/E",v:a.pe},{l:"Mkt Cap",v:a.mc},{l:"Beta",v:a.cat==="Stock"?fe64_betaCell(a.beta):a.beta},{l:"Sentiment",v:a.se}]''',
'mobile stock beta label')

s = sub1(s,
'''['Beta', fmt(m.beta)],''',
'''['Beta', fe64_betaTxt(data.valuation && data.valuation.beta) + ' \\u00b7 5y monthly beta, Yahoo'],''',
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
'''      const bN = fe64_betaNum(a || pos.tk);
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
'''    const bN = fe64_betaNum(r.a);
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
'''  const beta = fe64_betaNum(_labTk);
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
  const beta=fe64_betaNum(_labTk);
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
'''  const betaN=fe64_betaNum(a||_labTk);
  if(betaN!=null&&betaN>=1.3) tips.push(`Beta ~${betaN.toFixed(2)} · 5y monthly beta, Yahoo: expect amplified moves when you slide Risk-On / Risk-Off.`);
  else if(betaN!=null&&betaN<0.8) tips.push(`Beta ~${betaN.toFixed(2)} · 5y monthly beta, Yahoo: more defensive \\u2014 scenario blender swings will be smaller than high-\\u03b2 names.`);''',
'lab look-for beta')

# 4) Markets panel uses the same trading-now sentence as the header.
s = sub1(s,
'''  document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${_rt42Ready() ? `${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live` : "syncing…"}`;''',
'''  document.getElementById('p1sub').textContent = (typeof _rt51Label === "function") ? _rt51Label() : `${tickers.length} of ${A.length} · ${_rt42Ready() ? `${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live` : "syncing…"}`;''',
'markets trading-now line')

# Newsroom: a filter matches the badge on the card, not the feed category or a keyword.
s = sub1(s,
'''function _newsInCategory(n, filterId){
  if(!filterId||filterId==="all")return true;
  if(filterId==="world")return _newsIsWorld(n);
  const filterMap={
    stocks:['Stocks','Earnings'],
    commodities:['Commodities'],
    fx:['FX'],
    geopolitics:['Geopolitics'],
    world:['Geopolitics'],
    crypto:['Crypto'],
    macro:['Macro','Central Bank','Regulation']
  };
  if(filterMap[filterId]?.includes(n.tg))return true;
  if(n.cat&&filterMap[filterId]?.includes(n.cat))return true;
  // Keyword fallback — commodity headlines often mis-tagged as Stocks/Macro
  const kws=NEWS_CAT_KEYWORDS[filterId];
  if(!kws)return false;
  const hay=_newsHaystack(n);
  return kws.some(k=>hay.includes(k));
}''',
'''function _newsInCategory(n, filterId){
  if(!filterId||filterId==="all")return true;
  if(filterId==="world")return _newsIsWorld(n);
  const want={stocks:"Stocks",commodities:"Commodities",fx:"Forex",forex:"Forex",geopolitics:"Geopolitics",crypto:"Crypto",macro:"Macro",regulation:"Regulation",other:"Other"}[filterId];
  if(!want)return false;
  return fe64_chip(n&&n.tg)===want;
}''',
'news filter matches the card badge')

s = sub1(s,
'''  const tc=n.im==="high"?"var(--rd)":n.tg==="Crypto"?"var(--pu)":n.tg==="Commodities"?"var(--gd)":n.tg==="Macro"||n.tg==="Central Bank"?"var(--cy)":n.tg==="Geopolitics"?"var(--rd)":n.tg==="FX"?"var(--cy)":"var(--bl)";''',
'''  const tc=n.im==="high"?"var(--rd)":fe64_chipColor(n.tg);''',
'card badge colour')
s = sub1(s,
'''NEWS.slice(0,5).forEach((n,i)=>{const tc=n.im==="high"?"var(--rd)":n.tg==="Crypto"?"var(--pu)":n.tg==="Commodities"?"var(--gd)":n.tg==="FX"?"var(--cy)":n.tg==="Geopolitics"?"var(--rd)":"var(--bl)";''',
'''NEWS.slice(0,5).forEach((n,i)=>{const tc=n.im==="high"?"var(--rd)":fe64_chipColor(n.tg);''',
'dash card badge colour')
s = sub1(s,
'''<div class="news-meta-left">${bd(n.tg,tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}</div>''',
'''<div class="news-meta-left">${bd(fe64_chip(n.tg),tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}</div>''',
'dash card badge label')
s = sub1(s,
'''flex-wrap:wrap">${bd(n.tg,tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}${sent}''',
'''flex-wrap:wrap">${bd(fe64_chip(n.tg),tc)}${n.im==="high"?bd("⚡","var(--rd)"):""}${relHtml}${sent}''',
'news card badge label')

s = sub1(s,
'''    {id:'fx',label:'FX',icon:'💱'},
    {id:'geopolitics',label:'Geopolitics',icon:'🌍'},
    {id:'crypto',label:'Crypto',icon:'₿'},
    {id:'macro',label:'Macro',icon:'🏛'}
  ];''',
'''    {id:'fx',label:'Forex',icon:'💱'},
    {id:'geopolitics',label:'Geopolitics',icon:'🌍'},
    {id:'crypto',label:'Crypto',icon:'₿'},
    {id:'macro',label:'Macro',icon:'🏛'},
    {id:'regulation',label:'Regulation',icon:'§'},
    {id:'other',label:'Other',icon:'·'}
  ];''',
'news filter labels')

s = sub1(s,
'''    NEWS.forEach(n=>{tagCounts[n.tg]=(tagCounts[n.tg]||0)+1;});
    h+=`<div class="news-tag-stats">`;
    Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).forEach(([tag,count])=>{
      const tc2=tag==="Crypto"?"var(--pu)":tag==="Commodities"?"var(--gd)":tag==="Geopolitics"?"var(--rd)":tag==="FX"?"var(--cy)":tag==="Macro"||tag==="Central Bank"?"var(--gn)":"var(--bl)";''',
'''    NEWS.forEach(n=>{const chip=fe64_chip(n.tg);tagCounts[chip]=(tagCounts[chip]||0)+1;});
    h+=`<div class="news-tag-stats">`;
    Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).forEach(([tag,count])=>{
      const tc2=fe64_chipColor(tag);''',
'news tag stats use the chip')

# The toolbar counted every loaded headline. Desktop All painted 18 of them.
# Render the same list the count is taken from.
s = sub1(s,
'''    const show=compact?list.slice(0,18):list;''',
'''    const show=list;''',
'news renders the counted list')

s = sub1(s,
'''  const filterBtns = ['all','Stock','Crypto','Commodity','FX'].map(f =>
    `<button onclick="_sf('${f}')" style="font-family:var(--mn);font-size:9px;padding:3px 9px;border-radius:10px;cursor:pointer;border:1px solid ${_screenerFilter===f?'var(--gd)':'var(--b4)'};background:${_screenerFilter===f?'var(--gdG)':'transparent'};color:${_screenerFilter===f?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${f==='all'?'All':f}</button>`
  ).join('');''',
'''  const filterBtns = ['all','Stock','Crypto','Commodity','FX'].map(f =>
    `<button onclick="_sf('${f}')" style="font-family:var(--mn);font-size:9px;padding:3px 9px;border-radius:10px;cursor:pointer;border:1px solid ${_screenerFilter===f?'var(--gd)':'var(--b4)'};background:${_screenerFilter===f?'var(--gdG)':'transparent'};color:${_screenerFilter===f?'var(--gd)':'var(--t3)'};white-space:nowrap;flex-shrink:0">${f==='all'?'All':fe64_chip(f)}</button>`
  ).join('');''',
'market table chip labels')
s = sub1(s,
'''<td class="tt-cat" style="font-family:var(--sn);font-size:11px;color:var(--t3);white-space:nowrap">${_escHtml(a.cat)}</td>''',
'''<td class="tt-cat" style="font-family:var(--sn);font-size:11px;color:var(--t3);white-space:nowrap">${_escHtml(fe64_chip(a.cat))}</td>''',
'market table category cell')

s = sub1(s,
'''      if (exps.length) b += (b ? " Then " : "") + pl(exps.length, "short explainer") + " on how " + (exps.length === 1 ? "a headline" : "headlines") + " like " + (exps.length === 1 ? "this" : "these") + " usually " + (exps.length === 1 ? "moves" : "move") + " gold, oil, the dollar, yields, stocks or crypto.";
      if (b) st[0] = Object.assign({}, st[0], { b: b });''',
'''      if (exps.length) b += (b ? " Then " : "") + pl(exps.length, "short explainer") + " on how " + (exps.length === 1 ? "a headline" : "headlines") + " like " + (exps.length === 1 ? "this" : "these") + " usually " + (exps.length === 1 ? "moves" : "move") + " gold, oil, the dollar, yields, stocks or crypto.";
      if (b) b += " These cards are this Academy lesson. Home, the Newsroom and Geo Ops do not include an In the news block.";
      if (b) st[0] = Object.assign({}, st[0], { b: b });''',
'academy intro does not promise a site block')

s = sub1(s,
'''    acc += chunk;''',
'''    acc = fe64_joinChunk(acc, chunk);''',
'ask token join')

# The static article stays in the page for no-JS. The mounted app uses the styled home,
# not the unstyled front-door letter.
s = sub1(s,
'''function renderHome() {
  _syncFrontDoorMode();
  if (_isVisitor()) return renderPublicHome();''',
'''function renderHome() {
  _syncFrontDoorMode();
  if (false) return renderPublicHome();''',
'styled home replaces the unstyled letter')
s = sub1(s,
'''        if (main) main.innerHTML = renderPublicHome();''',
'''        if (main) main.innerHTML = renderHome();''',
'mobile home uses the styled home')
s = sub1(s,
'''        if(main) main.innerHTML=renderPublicHome();''',
'''        if(main) main.innerHTML=renderHome();''',
'price refresh uses the styled home')
s = sub1(s,
'''  if (pg === "home") {
    _syncFrontDoorMode();
    if (IS_DESKTOP()) _desktopRoute("home");
    else renderMain();
  }
  _finishAppBoot();''',
'''  if (pg === "home") {
    _syncFrontDoorMode();
    if (IS_DESKTOP()) _desktopRoute("home");
    else if (typeof _isPublicDocumentVisitor === "function" && _isPublicDocumentVisitor()) {
      var fe64Main = document.getElementById("main");
      if (fe64Main) fe64Main.innerHTML = renderHome();
    } else renderMain();
  }
  _finishAppBoot();''',
'guest home paints the styled home before the veil lifts')

# Guest home: JS hides the static fallback before first paint. No-JS still shows it.
h = sub1(h,
'''  document.documentElement.setAttribute('data-theme', 'dark');''',
'''  document.documentElement.setAttribute('data-theme', 'dark');
  document.documentElement.classList.add('fe64-js');''',
'guest js class')
h = sub1(h,
'''@media(max-width:760px){.seo-public-sections{grid-template-columns:1fr}.seo-public{padding-top:20px}.seo-public-hero{padding:24px 20px}}''',
'''@media(max-width:760px){.seo-public-sections{grid-template-columns:1fr}.seo-public{padding-top:20px}.seo-public-hero{padding:24px 20px}}
html.fe64-js .seo-public,html.fe64-js .seo-panel-copy{display:none!important}''',
'guest fallback hidden once js runs')
s = subn(s,
'''title="Open Stripe billing to cancel your subscription"''',
'''title="Cancel this subscription"''',
'billing button wording', 3)
s = sub1(s,
'''Admin account: Premium is included and there is no Stripe subscription, so there is no billing to manage.''',
'''Admin account: Premium is included, so there is no billing to manage.''',
'admin billing sentence')
s = sub1(s,
'''Premium is already active on this account (no Stripe billing to manage)''',
'''Premium is already active on this account.''',
'checkout toast wording')


# 7a) Keep server quote status on the instrument. Callers that pass only p/c/prev
# still forward status, note, delayMin and nextOpen.
s = sub1(s,
'''  liveQuoteProxy[tk] = !!q.proxy
    || liveQuoteSrc[tk].startsWith("gold-api-spot-proxy")
    || liveQuoteSrc[tk] === "frankfurter-ecb"
    || liveQuoteSrc[tk] === "open-exchange-rate-api";
  return true;''',
'''  liveQuoteProxy[tk] = !!q.proxy
    || liveQuoteSrc[tk].startsWith("gold-api-spot-proxy")
    || liveQuoteSrc[tk] === "frankfurter-ecb"
    || liveQuoteSrc[tk] === "open-exchange-rate-api";
  try { fe64_keepYq(tk, q); } catch (e) {}
  return true;''',
'store quote status on the instrument')
s = sub1(s,
'''  if (ageMs != null && ageMs > staleAfterMs && status !== "unavailable" && status !== "cached" && status !== "closed") {''',
'''  if (ageMs != null && ageMs > staleAfterMs && status !== "unavailable" && status !== "cached" && status !== "closed" && fe64_allowAgeStale(tk)) {''',
'do not age a server quote into stale')
s = sub1(s,
'''        _applyLiveQuote(tk, { p: q.p, c: q.c, prev: q.prev }, "yahoo");''',
'''        _applyLiveQuote(tk, Object.assign({ p: q.p, c: q.c, prev: q.prev }, fe64_yqFields(q)), "yahoo");''',
'sector holdings keep quote status')
s = sub1(s,
'''      if (q && _applyLiveQuote(sym, { p: q.p, c: q.c, prev: q.prev }, "yahoo")) {''',
'''      if (q && _applyLiveQuote(sym, Object.assign({ p: q.p, c: q.c, prev: q.prev }, fe64_yqFields(q)), "yahoo")) {''',
'sector quotes keep quote status')
s = sub1(s,
'''       _applyLiveQuote(markTk, {
        p: priceInfo.p,
        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
        prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined,
      }, src==="coingecko"?"coingecko":"yahoo");''',
'''       _applyLiveQuote(markTk, Object.assign({
        p: priceInfo.p,
        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
        prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined,
      }, fe64_yqFields(priceInfo)), src==="coingecko"?"coingecko":"yahoo");''',
'lookup keeps quote status')
s = sub1(s,
'''    status: meta.status, label: meta.label,
    asOf: meta.asOf, age: meta.asOf ? _fmtAge(meta.asOf) : "—",
    src: meta.src, detail: meta.detail''',
'''    status: meta.status, label: meta.label,
    asOf: meta.asOf, age: meta.asOf ? _fmtAge(meta.asOf) : "—",
    src: meta.src, detail: meta.detail, fe64Note: meta.fe64Note || ""''',
'price object carries the plain note')
s = sub1(s,
'''  if(s==="closed")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CLOSED</span>`;''',
'''  if(s==="closed")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CLOSED${d.fe64Note?" · "+_escHtml(d.fe64Note):""}</span>`;''',
'closed badge plus the note')
s = sub1(s,
'''  if(d.status==="closed")return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · last close ${_rt18CloseLbl(_rt20LastClose(tk) || d.asOf)}</span>`;''',
'''  if(d.status==="closed")return d.fe64Note?`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · ${_escHtml(d.fe64Note)}</span>`:`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · last close ${_rt18CloseLbl(_rt20LastClose(tk) || d.asOf)}</span>`;''',
'closed as-of line uses the note')
s = sub1(s,
'''      ? `${_quoteSourceLabel(quoteMeta.src)} · as of ${_fmtAsOf(quoteMeta.asOf)} · ${quoteMeta.label}`''',
'''      ? `${_quoteSourceLabel(quoteMeta.src)} · as of ${_fmtAsOf(quoteMeta.asOf)} · ${quoteMeta.label}${quoteMeta.status==="closed"&&quoteMeta.fe64Note?" · "+quoteMeta.fe64Note:""}`''',
'quote line keeps a closed note')

# 7b) Read CoinGecko stale headers. The JSON body is still what callers parse.
s = sub1(s,
'''    let cgStaleTs=NaN;try{if(res.headers.get('X-Dispatch-Data-Status')==='stale')cgStaleTs=Date.parse(res.headers.get('X-Dispatch-Data-As-Of')||'');}catch(e){}''',
'''    let cgStaleTs=NaN;try{var fe64s=fe64_cgRead(res,"simple");if(fe64s&&fe64s.stale)cgStaleTs=Date.parse(fe64s.asOf||"");}catch(e){}''',
'simple price reads both as-of headers')
s = sub1(s,
'''      const data=await mktRes.value.json();try{const st=mktRes.value.headers.get('X-Dispatch-Data-Status'),ao=mktRes.value.headers.get('X-Dispatch-Data-As-Of');_cryptoAsOf=(st==='stale'&&ao)?new Date(ao):null;}catch(e){_cryptoAsOf=null;}''',
'''      var fe64m=null;try{fe64m=fe64_cgRead(mktRes.value,"markets");}catch(e){}
      const data=await mktRes.value.json();try{_cryptoAsOf=(fe64m&&fe64m.stale&&fe64m.asOf)?new Date(fe64m.asOf):null;}catch(e){_cryptoAsOf=null;}''',
'rankings read both as-of headers')
s = sub1(s,
'''      const gd=await globalRes.value.json();''',
'''      try{fe64_cgRead(globalRes.value,"global");}catch(e){}
      const gd=await globalRes.value.json();''',
'dominance reads both as-of headers')
s = sub1(s,
r'''  const cg = stale
    ? `CoinGecko table delayed \u00b7 updated ${_rt26Ago(asOf.getTime())}`
    : (_rt.cgAt ? `CoinGecko table \u00b7 updated ${_rt26Ago(_rt.cgAt)}` : "CoinGecko table");
  const fr = f ? ` \u00b7 ${f} row${f === 1 ? "" : "s"} from desk quotes (hover for source)` : "";
  return last
    ? `\u25cf Live \u00b7 ${_quoteSourceLabel(src)} \u00b7 last tick ${_fmtAsOf(last)} \u00b7 ${n} streamed row${n === 1 ? "" : "s"} marked \u25cf \u00b7 other values: ${cg}${fr}`
    : (stale ? `Delayed \u00b7 ${cg}${fr}` : `${cg}${fr}`);''',
r'''  const fe64uk = typeof fe64_cgAsOf === "function" ? fe64_cgAsOf("markets") : "";
  const cg = fe64uk ? fe64uk
    : stale
    ? `CoinGecko table delayed \u00b7 updated ${_rt26Ago(asOf.getTime())}`
    : (_rt.cgAt ? `CoinGecko table \u00b7 updated ${_rt26Ago(_rt.cgAt)}` : "CoinGecko table");
  const fr = f ? ` \u00b7 ${f} row${f === 1 ? "" : "s"} from desk quotes (hover for source)` : "";
  return last
    ? `\u25cf Live \u00b7 ${_quoteSourceLabel(src)} \u00b7 last tick ${_fmtAsOf(last)} \u00b7 ${n} streamed row${n === 1 ? "" : "s"} marked \u25cf \u00b7 other values: ${fe64uk || cg}${fr}`
    : (fe64uk ? `${fe64uk}${fr}` : stale ? `Delayed \u00b7 ${cg}${fr}` : `${cg}${fr}`);''',
'rankings header as-of')
s = sub1(s,
r'''  const title = (v.stream || v.desk) ? `${_quoteSourceLabel(v.src)} \u00b7 ${_quoteMeta(v.tk).label} \u00b7 as of ${_fmtAsOf(v.ts)}` : staleTbl ? `CoinGecko \u00b7 delayed \u00b7 as of ${_fmtAsOf(v.ts)}` : `CoinGecko \u00b7 fetched ${_fmtAsOf(v.ts)}`;''',
r'''  const fe64cell = typeof fe64_cgAsOf === "function" ? fe64_cgAsOf("markets") : "";
  const title = (v.stream || v.desk) ? `${_quoteSourceLabel(v.src)} \u00b7 ${_quoteMeta(v.tk).label} \u00b7 as of ${_fmtAsOf(v.ts)}` : fe64cell ? fe64cell : staleTbl ? `CoinGecko \u00b7 delayed \u00b7 as of ${_fmtAsOf(v.ts)}` : `CoinGecko \u00b7 fetched ${_fmtAsOf(v.ts)}`;''',
'rankings cell as-of')
s = sub1(s,
'''      insight = `BTC dominance ${_cryptoDominance.btc}% · ETH ${_cryptoDominance.eth}% · Total mcap ${tmc}.`;''',
'''      insight = `BTC dominance ${_cryptoDominance.btc}% · ETH ${_cryptoDominance.eth}% · Total mcap ${tmc}.` + ((typeof fe64_cgAsOf === "function" && fe64_cgAsOf("global")) ? " " + fe64_cgAsOf("global") + "." : "");''',
'dominance sentence as-of')
s = sub1(s,
'''      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">CRYPTO MARKET DOMINANCE</div>''',
'''      <div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;margin-bottom:8px">CRYPTO MARKET DOMINANCE${(typeof fe64_cgAsOf==="function"&&fe64_cgAsOf("global"))?" · "+fe64_cgAsOf("global"):""}</div>''',
'dominance heading as-of')
s = sub1(s,
'''function _rt24CgAge() { return ""; }''',
'''function _rt24CgAge() { var t = typeof fe64_cgAsOf === "function" ? (fe64_cgAsOf("markets") || fe64_cgAsOf("global") || fe64_cgAsOf("simple")) : ""; return t ? " \\u00b7 " + t : ""; }''',
'rankings subtitle as-of')

BLOCK = r'''
// ── rt54 ── Shown beta is the Yahoo figure already on the name. A missing one is a dash.
function fe64_betaNum(aOrTk) {
  var a = typeof aOrTk === "string" ? ((typeof A !== "undefined" && A.find(function (x) { return x.tk === aOrTk; })) || null) : aOrTk;
  if (!a || a.beta == null) return null;
  var n = parseFloat(String(a.beta).replace(/x/i, ""));
  return isFinite(n) ? n : null;
}
function fe64_betaTxt(v) {
  var n = typeof v === "number" ? v : parseFloat(String(v == null ? "" : v).replace(/x/i, ""));
  return isFinite(n) ? n.toFixed(2) : "\u2014";
}
function fe64_betaCell(v) {
  return fe64_betaTxt(v) + '<div style="font-family:var(--mn);font-size:8px;font-weight:500;color:var(--t3);letter-spacing:0.02em;margin-top:2px">5y monthly beta, Yahoo</div>';
}
function fe64_chip(tag) {
  var k = String(tag == null ? "" : tag).trim().toLowerCase();
  if (k === "stock" || k === "stocks" || k === "earnings" || k === "etf") return "Stocks";
  if (k === "commodity" || k === "commodities") return "Commodities";
  if (k === "fx" || k === "forex" || k === "currency") return "Forex";
  if (k === "crypto" || k === "cryptocurrency") return "Crypto";
  if (k === "macro" || k === "central bank") return "Macro";
  if (k === "regulation" || k === "regulatory") return "Regulation";
  if (k === "geopolitics" || k === "geopolitical") return "Geopolitics";
  return "Other";
}
function fe64_chipColor(tag) {
  var c = fe64_chip(tag);
  if (c === "Crypto") return "var(--pu)";
  if (c === "Commodities" || c === "Regulation") return "var(--gd)";
  if (c === "Geopolitics") return "var(--rd)";
  if (c === "Forex" || c === "Macro") return "var(--cy)";
  if (c === "Other") return "var(--t3)";
  return "var(--bl)";
}
function fe64_equityStory(low, hit) {
  var text = String(low || "");
  var exch = /\(\s*(?:nyse|nasdaq|lse|amex|tsx|asx|hkex|xetra|euronext)\s*:\s*[a-z0-9][a-z0-9.\-]{0,12}\s*\)/.test(text)
    || /(?:^|[^a-z0-9])(?:nyse|nasdaq|lse|amex|tsx|asx)\s*:\s*[a-z0-9][a-z0-9.\-]{0,12}(?:$|[^a-z0-9])/.test(text);
  var stockWord = hit(["stock", "stocks", "share", "shares", "equity", "equities"]);
  if (exch && stockWord) return true;
  var names = ["bp", "shell", "exxon", "exxonmobil", "exxon mobil", "chevron", "conocophillips", "conoco", "totalenergies", "total energies", "equinor", "eni", "repsol", "woodside", "occidental", "bhp", "rio tinto", "vale", "glencore", "anglo american", "freeport", "newmont", "barrick", "southern copper", "antofagasta", "teck", "micron", "apple", "microsoft", "nvidia", "tesla", "amazon", "meta", "alphabet", "jpmorgan"];
  if (hit(names)) return true;
  try {
    if (typeof A !== "undefined" && A && A.forEach) {
      var found = false;
      A.forEach(function (a) {
        if (found || !a || a.cat !== "Stock") return;
        var tk = String(a.tk || "").toLowerCase();
        if (tk.length >= 3 && hit([tk])) found = true;
        else if (tk.length === 2 && exch && hit([tk])) found = true;
        else {
          var stem = String(a.nm || "").toLowerCase().replace(/[,.]?\s+(inc|corp(oration)?|technology|technologies|holdings|group|company|co|plc|ltd|platforms|class [a-z])\b.*$/, "").trim();
          if (stem.length >= 4 && hit([stem])) found = true;
        }
      });
      if (found) return true;
    }
  } catch (e) {}
  if (hit(["guidance", "earnings", "revenue", "profit", "eps", "beat estimates", "missed estimates", "price target", "analyst", "bull case", "bear case", "upgrade", "downgrade", "dividend", "results", "quarterly"])
      && (stockWord || hit(["company", "companies"]))) return true;
  return false;
}
function fe64_cryptoStory(low, hit) {
  var coins = ["bitcoin", "crypto", "cryptocurrency", "cryptocurrencies", "ethereum", "btc", "eth", "blockchain", "solana", "xrp", "dogecoin", "stablecoin", "binance", "coinbase", "defi", "altcoin"];
  if (!hit(coins)) return false;
  if (fe64_equityStory(low, hit)) {
    var lead = /^\s*(bitcoin|crypto|ethereum|btc|eth|solana|xrp|dogecoin|binance|coinbase)\b/.test(String(low || "").trim());
    if (!lead && !hit(["coinbase", "binance", "bitcoin miner", "bitcoin miners", "crypto miner", "crypto miners", "crypto exchange"])) return false;
  }
  return true;
}
function fe64_joinChunk(acc, chunk) {
  chunk = String(chunk == null ? "" : chunk);
  acc = String(acc == null ? "" : acc);
  if (!chunk) return acc;
  if (!acc) return chunk;
  var a = acc.replace(/[\n\r]+$/g, "");
  var c = chunk.replace(/^[\n\r]+/g, "");
  var broke = a.length !== acc.length || c.length !== chunk.length;
  var end = a.slice(-1), start = c.charAt(0);
  if (!broke) return acc + chunk;
  if (end === "(" && /[A-Za-z0-9]/.test(start)) return a + c;
  if (/[A-Za-z0-9]$/.test(end) && /^[a-z0-9)]/.test(start)) return a + c;
  if (/[A-Za-z0-9)]$/.test(end) && /^[A-Z(]/.test(start)) return a + " " + c;
  return a + c;
}
function fe64_flattenName(text) {
  return String(text == null ? "" : text)
    .replace(/([A-Za-z])\s*[\n\r]+\s*([a-z])/g, "$1$2")
    .replace(/([A-Za-z0-9])\s*[\n\r]+\s*([A-Z])/g, "$1 $2")
    .replace(/([A-Za-z])\s*[\n\r]+\s*\(/g, "$1 (")
    .replace(/\(\s*[\n\r]+\s*([A-Za-z])/g, "($1");
}
function fe64_entHtml(html) {
  return String(html || "").replace(/([A-Z][A-Za-z0-9&;.'-]{1,40}(?:\s+[A-Z][A-Za-z0-9&;.'-]{1,40}){0,4})\s*\(\s*([A-Z][A-Z0-9.]{1,8})\s*\)/g, '<span class="fe64-ent">$1 ($2)</span>');
}
// fe64-quote-begin
function fe64_yqKey(tk) {
  try {
    if (typeof resolveInternalTicker === "function") {
      var r = resolveInternalTicker(tk);
      if (r) return r;
    }
  } catch (e) {}
  return tk;
}
function fe64_keepYq(tk, q) {
  if (!fe64_keepYq.map) fe64_keepYq.map = Object.create(null);
  var key = fe64_yqKey(tk);
  if (!key) return;
  var st = q && typeof q.status === "string" ? q.status : "";
  var known = st === "closed" || st === "quiet" || st === "stale" || st === "delayed" || st === "fresh";
  var note = q && typeof q.note === "string" ? q.note : "";
  var nextOpen = q && (typeof q.nextOpen === "string" || typeof q.nextOpen === "number") ? q.nextOpen : "";
  var delayMin = q && typeof q.delayMin === "number" && isFinite(q.delayMin) ? q.delayMin : null;
  if (known) fe64_keepYq.map[key] = { status: st, delayMin: delayMin, note: note, nextOpen: nextOpen };
  else delete fe64_keepYq.map[key];
}
function fe64_yqBag(tk) {
  var map = fe64_keepYq.map;
  if (!map) return null;
  return map[fe64_yqKey(tk)] || null;
}
function fe64_yqFields(q) {
  var o = {};
  if (!q) return o;
  if (q.status === "closed" || q.status === "quiet" || q.status === "stale" || q.status === "delayed" || q.status === "fresh") o.status = q.status;
  if (typeof q.delayMin === "number" && isFinite(q.delayMin)) o.delayMin = q.delayMin;
  if (typeof q.note === "string" && q.note) o.note = q.note;
  if (typeof q.nextOpen === "string" && q.nextOpen) o.nextOpen = q.nextOpen;
  else if (typeof q.nextOpen === "number" && isFinite(q.nextOpen)) o.nextOpen = q.nextOpen;
  return o;
}
function fe64_plainNote(note) {
  var s = String(note == null ? "" : note).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  if (!s) return "";
  if (/x-dispatch|\basof\b|bb5|json|\bheader\b|status===|delaymin|nextopen|api\//i.test(s)) return "";
  return s;
}
function fe64_ukHm(iso) {
  var ms = typeof iso === "number" ? iso : Date.parse(iso || "");
  if (typeof iso === "string" && /^\d{11,}$/.test(iso)) ms = Number(iso);
  if (!isFinite(ms)) return "";
  try {
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    return h && mi ? h + ":" + mi : "";
  } catch (e) { return ""; }
}
function fe64_closedWords(bag) {
  var note = fe64_plainNote(bag && bag.note);
  if (note) return note;
  var hm = fe64_ukHm(bag && bag.nextOpen);
  return hm ? "opens " + hm + " UK" : "";
}
function fe64_delayWords(bag) {
  var s = fe64_plainNote(bag && bag.note);
  if (s) return s;
  var n = bag && bag.delayMin;
  if (typeof n === "number" && isFinite(n) && n > 0) return "delayed " + Math.round(n) + "m by exchange";
  return "delayed by the exchange";
}
function fe64_allowAgeStale(tk) {
  var bag = fe64_yqBag(tk);
  if (!bag) return true;
  if (bag.status === "closed" || bag.status === "quiet" || bag.status === "delayed" || bag.status === "fresh") return false;
  return true;
}
function fe64_freshUndo(m) {
  if (!m || m.status !== "stale") return m;
  var src = m.src || "", asOf = "";
  try { if (m.asOf && typeof _fmtAsOf === "function") asOf = _fmtAsOf(m.asOf); } catch (e) {}
  if (src === "coinbase-ws" || src === "kraken-ws" || src === "yahoo-stream") {
    var label = src === "coinbase-ws" ? "LIVE·CB" : src === "kraken-ws" ? "LIVE·KR" : "LIVE·YS";
    return Object.assign({}, m, { status: "live", label: label, detail: asOf ? ("as of " + asOf) : "Live", trusted: true });
  }
  return Object.assign({}, m, { status: "live", label: asOf ? ("as of " + asOf) : "LIVE", detail: asOf ? ("as of " + asOf) : "Live", trusted: true });
}
function fe64_quoteApply(tk, m) {
  var bag = fe64_yqBag(tk);
  if (!bag || !m || m.status === "unavailable") return m;
  if (bag.status === "closed") {
    var words = fe64_closedWords(bag);
    return Object.assign({}, m, { status: "closed", label: "CLOSED", detail: words || "Market closed", fe64Note: words });
  }
  if (bag.status === "quiet") {
    var quiet = fe64_plainNote(bag.note) || "Quiet";
    return Object.assign({}, m, { status: "quiet", label: quiet, detail: quiet, fe64Note: quiet });
  }
  if (bag.status === "stale") return Object.assign({}, m, { status: "stale", label: "STALE", detail: "This price is not current." });
  if (bag.status === "delayed") {
    var delay = fe64_delayWords(bag);
    return Object.assign({}, m, { status: "delayed", label: delay, detail: delay, fe64Note: delay });
  }
  if (bag.status === "fresh") return m.status === "stale" ? fe64_freshUndo(m) : m;
  return m;
}
function fe64_cgHdr(res, name) {
  try { return (res && res.headers && res.headers.get(name)) || ""; } catch (e) { return ""; }
}
function fe64_cgRead(res, kind) {
  var st = String(fe64_cgHdr(res, "X-Dispatch-Data-Status") || "").toLowerCase();
  var ao = fe64_cgHdr(res, "X-Dispatch-As-Of") || fe64_cgHdr(res, "X-Dispatch-Data-As-Of") || "";
  var rec = { stale: st === "stale", asOf: ao };
  if (!fe64_cgRead.bag) fe64_cgRead.bag = Object.create(null);
  if (kind) fe64_cgRead.bag[kind] = rec;
  return rec;
}
function fe64_cgAsOf(kind) {
  var rec = fe64_cgRead.bag && fe64_cgRead.bag[kind];
  if (!rec || !rec.stale || !rec.asOf) return "";
  var hm = fe64_ukHm(rec.asOf);
  return hm ? "as of " + hm + " UK" : "";
}
// fe64-quote-end
(function () {
  try {
    var st = document.createElement("style");
    st.setAttribute("data-fe64", "chat");
    st.textContent = ".chat-panel{position:fixed;z-index:940;right:16px;bottom:16px;width:min(420px,calc(100vw - 24px));height:min(640px,calc(100vh - 32px));display:flex;flex-direction:column;background:var(--bg,#14151a);border:1px solid var(--gb,rgba(255,255,255,.14));border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.45);overflow:hidden}.chat-panel.hide{display:none!important}.chat-msg,.chat-body,.chat-headline,.chat-body p,.chat-h2,.chat-h3,.chat-li{word-break:normal!important;overflow-wrap:break-word}.fe64-ent{display:inline!important;white-space:nowrap;word-break:keep-all}#loginGateOv:focus,#login-gate-title:focus{outline:none}#loginGateOv button:focus-visible,#loginGateOv a:focus-visible{outline:2px solid var(--gd);outline-offset:3px}@media(max-width:767px){.chat-panel{right:0;bottom:0;width:100%;height:min(78vh,640px);border-radius:14px 14px 0 0}}";
    document.head.appendChild(st);
  } catch (e) {}
  try {
    var md = _chatMd;
    _chatMd = function (text) {
      var html = md.call(this, fe64_flattenName(text));
      try { html = fe64_entHtml(html); } catch (e2) {}
      return html;
    };
  } catch (e) {}
})();
try {
  var fe64_qBase0 = _quoteMetaBase_rt18;
  _quoteMetaBase_rt18 = function (tk) {
    var m = fe64_qBase0.apply(this, arguments);
    try { m = fe64_quoteApply(tk, m); } catch (e) {}
    return m;
  };
} catch (e) {}
try {
  var fe64_qMeta0 = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe64_qMeta0.apply(this, arguments);
    try { m = fe64_quoteApply(tk, m); } catch (e) {}
    return m;
  };
} catch (e) {}
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
