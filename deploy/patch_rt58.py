#!/usr/bin/env python3
"""patch_rt58.py: client patch on chat69. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat69, the output of patch_rt57.py on chat68:
  app.js md5 843c42b73f671d80c6e563d2edddb829
  index.html md5 07137d3795c694d726cb9a295719849e
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

News tags use word-boundary keywords. A cached snapshot's STALE status does not
outlive a newer quote. Suffixed lookups paint when the quote returns. Insider
rows match the Form 4 numbers, and bb8 window fields are shown when the server
sends them. Saved chats from before chat70 are cleared once. Partial financials
are rendered and refetched once, and statement currency follows the payload.
Pulse Ask sends its question once as soon as the panel is open, with or without
a saved chat. An open stock keeps its own intel card when a regime cache exists.
No server file is changed.

Usage: python3 patch_rt58.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "843c42b73f671d80c6e563d2edddb829"
EXPECT_INDEX_MD5 = "07137d3795c694d726cb9a295719849e"
NEED_MARKER = "// ── rt57 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt58 ──' in s: already('rt58 already applied')
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

def subn(src, old, new, label, n=1):
    c = src.count(old)
    if c != n: die('%s matched %d times' % (label, c))
    return src.replace(old, new)

s = subn(s, '''function fe68_storyTag(text, low, hit, feedCat) {
  var raw = " " + String(text == null ? "" : text).toLowerCase().replace(/\\s+/g, " ") + " ";
  var rules = [
    ["Crypto", ["bitcoin", "btc", "ethereum", "crypto", "cryptocurrency", "tokenized", "tokenization", "stablecoin", "token", "custody", "bitcoin etf", "crypto etf"]],
    ["Forex", ["dollar", "euro", "yen", "sterling", "forex", "fx", "currency pair", "eur/usd", "gbp/usd", "usd/jpy"]],
    ["Commodities", ["newpeak", "ampol", "new hope", "gold", "silver", "copper", "drilling", "mining", "coal", "oil", "crude", "brent", "wti", "natural gas", "wheat", "corn", "grain"]],
    ["Stocks", ["skyworks", "coreweave", "fleetpartners", "fleet partners", "starboard", "hang seng", "kospi", "nikkei", "asx", "msci", "s&p 500", "s&p", "nasdaq", "dow jones", "asian stocks", "shares", "share", "stocks", "stock", "equities", "equity"]],
    ["Macro", ["central bank", "federal reserve", "interest rate", "rate cut", "rate hike", "labour market", "labor market", "unemployment", "inflation", "gdp", "bond yield", "bond rout", "bonds", "yields"]],
    ["Geopolitics", ["ceasefire", "sanctions", "sanction", "military", "election", "tariff", "war"]]
  ];
  var found = [], i, at;
  for (i = 0; i < rules.length; i++) {
    at = fe68_at(raw, rules[i][1]);
    if (at >= 0) found.push({ tag: rules[i][0], at: at });
  }
  if (!found.length) {
    if (/\\bmarkets?\\b/.test(raw) && feedCat) {
      var chip = fe68_chip(feedCat);
      if (chip && chip !== "Other") return chip;
    }
    return "Other";
  }
  found.sort(function (a, b) { return a.at - b.at; });
  var top = found[0].at;
  var tied = found.filter(function (x) { return x.at === top; });
  if (tied.length > 1 && feedCat) {
    var want = fe68_chip(feedCat);
    for (i = 0; i < tied.length; i++) if (tied[i].tag === want) return want;
  }
  return tied[0].tag;
}''', '''function fe68_storyTag(text, low, hit, feedCat) {
  var raw = " " + String(text == null ? "" : text).toLowerCase().replace(/[\\u2018\\u2019\\u201B]/g, "'").replace(/\\s+/g, " ") + " ";
  var rules = [
    ["Crypto", ["bitcoin", "btc", "ethereum", "crypto", "cryptocurrency", "tokenized", "tokenization", "stablecoin", "token", "custody", "bitcoin etf", "crypto etf"]],
    ["Forex", ["dollar", "euro", "yen", "sterling", "forex", "fx", "currency pair", "eur/usd", "gbp/usd", "usd/jpy"]],
    ["Commodities", ["newpeak", "ampol", "new hope", "gold", "silver", "copper", "drilling", "mining", "coal", "oil", "crude", "brent", "wti", "natural gas", "wheat", "corn", "grain"]],
    ["Stocks", ["skyworks", "coreweave", "fleetpartners", "fleet partners", "starboard", "hang seng", "kospi", "nikkei", "asx", "msci", "s&p 500", "s&p", "nasdaq", "dow jones", "asian stocks", "pharma", "biotech", "moderna", "merck", "stocktwits", "gift nifty", "nifty", "vwap", "shares", "stocks", "stock", "equities", "equity"]],
    ["Macro", ["central bank", "federal reserve", "interest rate", "rate cut", "rate hike", "labour market", "labor market", "unemployment", "economic growth", "china's growth", "home prices", "house prices", "government spending", "inflation", "gdp", "cpi", "pmi", "budget", "bond yield", "bond rout", "bonds", "yields"]],
    ["Geopolitics", ["ceasefire", "sanctions", "sanction", "election", "tariff", "trade war", "hormuz", "iran", "strait", "shipping lane", "war"]],
    ["Regulation", ["sec", "fca", "cftc", "esma", "regulator"]]
  ];
  var found = [], i, at;
  for (i = 0; i < rules.length; i++) {
    at = fe68_at(raw, rules[i][1]);
    if (at >= 0) found.push({ tag: rules[i][0], at: at });
  }
  if (fe68_at(raw, ["sec", "fca", "cftc", "esma", "regulator"]) >= 0) return "Regulation";
  if (!found.length) {
    if (fe68_at(raw, ["framework", "rule"]) >= 0 && fe68_at(raw, ["stock", "stocks", "market", "markets", "crypto", "token", "tokenized", "trading", "exchange", "listing", "bond", "equity", "fund", "tariff"]) >= 0) return "Regulation";
    if (/\\bmarkets?\\b/.test(raw) && feedCat) {
      var chip = fe68_chip(feedCat);
      if (chip && chip !== "Other") return chip;
    }
    return "Other";
  }
  found.sort(function (a, b) { return a.at - b.at; });
  var top = found[0].at;
  var tied = found.filter(function (x) { return x.at === top; });
  if (tied.length > 1 && feedCat) {
    var want = fe68_chip(feedCat);
    for (i = 0; i < tied.length; i++) if (tied[i].tag === want) return want;
  }
  return tied[0].tag;
}''', 'story tags')

s = subn(s, '''    re = new RegExp("(^|[^a-z0-9])" + k.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + "($|[^a-z0-9])", "i");''',
    '''    re = new RegExp("(^|[^a-z0-9])" + k.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + "s?($|[^a-z0-9])", "i");''',
    'plural boundary')

s = subn(s, '''function fe68_chip(tag) {
  try { if (typeof fe64_chip === "function") return fe64_chip(tag); } catch (e) {}
  var k = String(tag == null ? "" : tag).trim().toLowerCase();
  if (k === "stock" || k === "stocks" || k === "earnings" || k === "etf") return "Stocks";
  if (k === "commodity" || k === "commodities") return "Commodities";
  if (k === "fx" || k === "forex" || k === "currency") return "Forex";
  if (k === "crypto" || k === "cryptocurrency") return "Crypto";
  if (k === "macro" || k === "central bank") return "Macro";
  if (k === "geopolitics" || k === "geopolitical") return "Geopolitics";
  return "Other";
}''',
    '''function fe68_chip(tag) {
  try { if (typeof fe64_chip === "function") return fe64_chip(tag); } catch (e) {}
  var k = String(tag == null ? "" : tag).trim().toLowerCase();
  if (k === "stock" || k === "stocks" || k === "earnings" || k === "etf") return "Stocks";
  if (k === "commodity" || k === "commodities") return "Commodities";
  if (k === "fx" || k === "forex" || k === "currency") return "Forex";
  if (k === "crypto" || k === "cryptocurrency") return "Crypto";
  if (k === "macro" || k === "central bank") return "Macro";
  if (k === "geopolitics" || k === "geopolitical") return "Geopolitics";
  if (k === "regulation" || k === "regulatory") return "Regulation";
  return "Other";
}''', 'regulation chip')

s = subn(s, '    label = "DELAYED·CG";', '    label = "delayed";', 'cg suffix')
s = subn(s, '    label = "DELAYED·FH";', '    label = "delayed";', 'fh suffix')
s = subn(s, 'src === "coinbase-ws" ? "DELAYED·CB" : "DELAYED·KR"', 'src === "coinbase-ws" ? "delayed" : "delayed"', 'cb kr suffix')
s = subn(s, '  if (src === "gold-api-spot-proxy-browser") return "free gold feed";',
    '  if (src === "gold-api-spot-proxy-browser") return "Spot gold";', 'gold browser label')
s = subn(s, '  if (src.startsWith("gold-api-spot-proxy")) return "free gold feed";',
    '  if (src.startsWith("gold-api-spot-proxy")) return "Spot gold";', 'gold proxy label')
s = subn(s, '      if (/gold/i.test(String(src || "") + " " + out)) return "free gold feed";',
    '      if (/gold/i.test(String(src || "") + " " + out)) return "Spot gold";', 'gold wrap label')

s = subn(s, '''async function _fetchLivePrices(){
  if(updatePaused)return;
  priceFetching=true;''',
    '''async function _fetchLivePrices(){
  if(updatePaused)return;
  priceFetching=true;
  try { if (typeof fe69_armBoot === "function") fe69_armBoot(); } catch (e) {}''',
    'arm boot')
s = subn(s, '  successCount += await fetchReferencePrices();',
    '  successCount += Number(await fe69_cap(fetchReferencePrices(), 2500, 0)) || 0;', 'cap reference')
s = subn(s, '  successCount += await fetchTwelveDataPrices();',
    '  successCount += Number(await fe69_cap(fetchTwelveDataPrices(), 2500, 0)) || 0;', 'cap twelve')
s = subn(s, '  const priHits=await _fetchYahooPriceChunk(PRICE_PRIORITY.filter(tk=>YAHOO_SYMBOLS[tk]&&tk!=="XAU"));',
    '  const priHits=Number(await fe69_cap(_fetchYahooPriceChunk(PRICE_PRIORITY.filter(tk=>YAHOO_SYMBOLS[tk]&&tk!=="XAU")), 2500, 0)) || 0;',
    'cap priority')
s = subn(s, '''    else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();
  }

  const restTickers=Object.keys(YAHOO_SYMBOLS).filter(tk=>!PRICE_PRIORITY.includes(tk)&&tk!=="XAU");''',
    '''    else if(pg==="dash"||pg==="mkt")_patchLiveDataIfNeeded();
  }
  try { if (typeof fe69_paintBoot === "function") fe69_paintBoot(); } catch (e) {}

  const restTickers=Object.keys(YAHOO_SYMBOLS).filter(tk=>!PRICE_PRIORITY.includes(tk)&&tk!=="XAU");''',
    'paint after priority')
s = subn(s, '    const results=await Promise.allSettled(pair.map(c=>_fetchYahooPriceChunk(c)));',
    '    const results=await fe69_cap(Promise.allSettled(pair.map(c=>_fetchYahooPriceChunk(c))), 4000, []);',
    'cap chunks')
s = subn(s, '  const cryptoData = await fetchCrypto();',
    '  const cryptoData = await fe69_cap(fetchCrypto(), 2500, null);', 'cap crypto')

s = subn(s, '''function _rt20Booting() {
  try { if (typeof priceLastFetch !== "undefined" && priceLastFetch) return false; } catch (e) {}
  return Date.now() - _rt20T0 < 15000;
}''',
    '''function _rt20Booting() {
  try { if (typeof fe69_bootDone !== "undefined" && fe69_bootDone) return false; } catch (e0) {}
  try { if (typeof priceLastFetch !== "undefined" && priceLastFetch) return false; } catch (e) {}
  return Date.now() - _rt20T0 < 15000;
}''', 'boot flag')

s = subn(s, '''  const yhSym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])?YAHOO_SYMBOLS[sym]:sym;
  let fe68Ready=null;
  if(typeof fe68_suffixed==="function"&&fe68_suffixed(sym)){try{fe68Ready=await fe68_yahooQuote(yhSym);}catch(e){fe68Ready=null;}fe68_pending=fe68Ready;}
  _dynTk=sym;_dynData=null;_dynLoading=true;termSelTk=null;''',
    '''  const yhSym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])?YAHOO_SYMBOLS[sym]:sym;
  _dynTk=sym;_dynData=null;_dynLoading=true;termSelTk=null;''',
    'lookup paints first')
s = subn(s, '''    renderNav();
  }
  try{
    // All price data via Yahoo Finance — works for every exchange worldwide''',
    '''    renderNav();
  }
  let fe68Ready=null;
  if(typeof fe68_suffixed==="function"&&fe68_suffixed(sym)){try{fe68Ready=await fe68_yahooQuote(yhSym);}catch(e){fe68Ready=null;}fe68_pending=fe68Ready;}
  if(fe68Ready&&typeof fe68Ready.p==="number"&&fe68Ready.p>0&&seq===_lookupSeq){try{fe69_paintLookup(sym,fe68Ready,seq);}catch(e){}}
  try{
    // All price data via Yahoo Finance — works for every exchange worldwide''',
    'quote then paint')

s = subn(s, '''  if (!container || !tvSymbol) {
    if (container) {
      container.innerHTML = `<div class="dispatch-chart-unavailable">Chart unavailable for ${_escHtml(tk)}<br><span>${_escHtml(fe65b_chartNote(tk))}</span></div>`;
    }
    return;
  }''',
    '''  if (!container || !tvSymbol) {
    if (container) {
      container.innerHTML = `<div class="dispatch-chart-unavailable">Loading chart…</div>`;
      if (typeof fe69_chartFallback === "function") fe69_chartFallback(tk, range, container);
      else container.innerHTML = `<div class="dispatch-chart-unavailable">Chart unavailable for ${_escHtml(tk)}<br><span>${_escHtml(fe65b_chartNote(tk))}</span></div>`;
    }
    return;
  }''', 'chart fallback')

s = subn(s, '''function fe68_hlHtml(tk) {
  try { if (typeof fe66_nonUs !== "function" || !fe66_nonUs(tk)) return ""; } catch (e) { return ""; }''',
    '''function fe68_hlHtml(tk) {
  try { if (typeof fe69_hlHtml === "function") return fe69_hlHtml(tk); } catch (e0) {}
  try { if (typeof fe66_nonUs !== "function" || !fe66_nonUs(tk)) return ""; } catch (e) { return ""; }''',
    'hl delegate')

s = subn(s, '    if (fe68_older(tk, q)) {',
    '    try { fe69_noteQuote(tk, q); } catch (eN) {}\n    if ((typeof fe69_older === "function" ? fe69_older(tk, q) : fe68_older(tk, q))) {',
    'newer quote wins')

s = subn(s, '    if (typeof _institutionalData !== "undefined" && !_institutionalData["13f"] && typeof _loadInstitutional === "function") _loadInstitutional("13f");',
    '    if (typeof _institutionalData !== "undefined" && !_institutionalData["13f"] && typeof _loadInstitutional === "function" && typeof fe69_allowFilings === "function" && fe69_allowFilings()) _loadInstitutional("13f");',
    'lazy 13f')

s = subn(s, '  if (loading) h += `<div class="institutional-state">Loading ${labels[type]} filings…</div>`;',
    '  if (loading) h += `<div class="institutional-state">${type === "insider" ? "Loading insider filings…" : ("Loading " + labels[type] + " filings…")}</div>`;',
    'insider loading copy')
s = subn(s, "d.items.slice(0, 12).forEach",
    'd.items.slice(0, type === "insider" ? 200 : 12).forEach',
    'insider slice')

BLOCK = r'''
// ── rt58 ──
// fe69-pure-begin
function fe69_words(s) {
  var t = String(s == null ? "" : s);
  t = t.replace(/\bfree gold feed\b/ig, "Spot gold");
  t = t.replace(/\bDELAYED\s*[·.\-]\s*(CG|FH|CB|KR|YS)\b/ig, "delayed");
  t = t.replace(/\bLIVE\s*[·.\-]\s*(CG|FH|CB|KR|YS)\b/ig, "LIVE");
  t = t.replace(/[·.\-](CG|FH|CB|KR|YS)\b/g, "");
  t = t.replace(/\bdelayed\s+(\d+)\s*m(?:in)?\b/ig, "delayed $1 min");
  return t.replace(/\s{2,}/g, " ").replace(/^[\s·\-]+|[\s·\-]+$/g, "").trim();
}
function fe69_cnt(n) {
  n = Number(n);
  if (!isFinite(n)) return "";
  var a = Math.abs(n), s = n < 0 ? "\u2212" : "";
  if (a >= 1e9) return s + (a / 1e9).toFixed(2) + "bn";
  if (a >= 1e6) return s + (a / 1e6).toFixed(a >= 1e8 ? 0 : a >= 1e7 ? 1 : 2) + "m";
  return s + Math.round(a).toLocaleString("en-GB");
}
function fe69_money(n) {
  n = Number(n);
  if (!isFinite(n) || n === 0) return "";
  var a = Math.abs(n), sig = n < 0 ? "\u2212" : "";
  var f = function (v, u) { return sig + "$" + (v >= 100 ? String(Math.round(v)) : v >= 10 ? v.toFixed(1).replace(/\.0$/, "") : v.toFixed(2).replace(/0$/, "").replace(/\.0$/, "")) + u; };
  if (a >= 1e12) return f(a / 1e12, "tn");
  if (a >= 1e9) return f(a / 1e9, "bn");
  if (a >= 1e6) return f(a / 1e6, "m");
  if (a >= 1e3) return f(a / 1e3, "k");
  return sig + "$" + Math.round(a).toLocaleString("en-GB");
}
function fe69_insSpan(shares, value) {
  var bits = [];
  if (shares != null && shares !== "" && isFinite(Number(shares))) bits.push(fe69_cnt(shares) + " shares");
  var money = value ? fe69_money(value) : "";
  if (money) bits.push(money);
  var px = "";
  if (Number(shares) > 0 && Number(value) > 0) px = " at $" + (Number(value) / Number(shares)).toFixed(2);
  return (bits.length ? " \u00b7 " + bits.join(" \u00b7 ") : "") + px;
}
function fe69_beforeDate(win) {
  if (!win) return "";
  var raw = win.next != null && String(win.next).trim() !== "" ? String(win.next) : (win.from != null ? String(win.from) : "");
  var m = raw.match(/(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : "";
}
function fe69_hasNext(win) {
  return !!(win && win.next != null && String(win.next).trim() !== "");
}
function fe69_reconcile(m, bag) {
  var o = {}, k;
  m = m || {};
  for (k in m) if (Object.prototype.hasOwnProperty.call(m, k)) o[k] = m[k];
  bag = bag || {};
  var delay = typeof bag.delayMin === "number" && bag.delayMin > 0 ? Math.round(bag.delayMin) : 0;
  var st = bag.status || "";
  if (o.status === "closed" || o.status === "lunch" || st === "closed" || st === "lunch") {
    o.label = fe69_words(o.label);
    return o;
  }
  if (delay > 0 && o.status !== "live") {
    o.status = "delayed";
    o.label = "delayed " + delay + " min";
    o.detail = "delayed " + delay + " min by exchange";
    o.fe64Note = o.detail;
  } else if (st === "delayed" && (o.status === "stale" || /STALE/i.test(String(o.label || "")))) {
    o.status = "delayed";
    o.label = "delayed";
  } else if (st === "fresh" && /DELAYED\s*[·.\-]\s*(CG|FH|CB|KR|YS)/i.test(String(o.label || ""))) {
    o.label = "delayed";
  }
  o.label = fe69_words(o.label);
  o.detail = fe69_words(o.detail);
  o.fe64Note = fe69_words(o.fe64Note);
  return o;
}
function fe69_srcGap(s) {
  return String(s == null ? "" : s).replace(/([^\n])[ \t]*\n?[ \t]*(Sources:)/g, "$1\n\n$2");
}
function fe69_srcHtml(s) {
  return fe69_srcGap(s).replace(/\n+\s*Sources:/g, "<br><br>Sources:");
}
function fe69_keepPrice(prev, next) {
  if (prev && Number(prev.price) > 0 && !(next && Number(next.price) > 0)) return prev;
  return next || prev;
}
function fe69_chatFresh(ver) {
  return String(ver || "") !== "chat70";
}
function fe69_finPartial(data, status) {
  if (data && data.meta && data.meta.partial) return true;
  return String(status || "").trim().toLowerCase() === "partial";
}
function fe69_finTagged(data) {
  return !!(data && data.priceCurrency && data.financialCurrency && data.fx != null && data.fx !== "");
}
function fe69_finRaw(n) {
  var v = Number(n);
  return isFinite(v) ? v : null;
}
function fe69_finSym(ccy) {
  var c = String(ccy || "USD");
  if (c === "USD") return { pre: "$", post: "" };
  if (c === "GBP") return { pre: "\u00a3", post: "" };
  if (c === "GBp" || c === "GBX") return { pre: "", post: "p" };
  if (c === "EUR") return { pre: "\u20ac", post: "" };
  if (c === "JPY") return { pre: "\u00a5", post: "" };
  if (c === "HKD") return { pre: "HK$", post: "" };
  return { pre: c + " ", post: "" };
}
function fe69_finPrice(n, ccy) {
  var v = fe69_finRaw(n);
  if (v == null) return "\u2014";
  var s = fe69_finSym(ccy || "USD");
  var num = Math.abs(v) >= 1 ? Math.abs(v).toFixed(2) : Math.abs(v).toFixed(4);
  return (v < 0 ? "-" : "") + s.pre + num + s.post;
}
function fe69_finStmt(n, ccy) {
  var v = fe69_finRaw(n);
  if (v == null) return "\u2014";
  var a = Math.abs(v);
  var body = a >= 1e12 ? (a / 1e12).toFixed(2) + "T" : a >= 1e9 ? (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a.toFixed(0);
  var s = fe69_finSym(ccy || "USD");
  return (v < 0 ? "-" : "") + s.pre + body + s.post;
}
function fe69_finRatio(n) {
  var v = fe69_finRaw(n);
  if (v == null || !(v > 0 && v < 250)) return "n/m";
  return v.toFixed(1) + "\u00d7";
}
function fe69_finView(data) {
  var tagged = fe69_finTagged(data);
  var pc = tagged ? String(data.priceCurrency) : "USD";
  var fc = tagged ? String(data.financialCurrency) : "USD";
  var v = (data && data.valuation) || {};
  var ann = data && data.financials && data.financials.annual;
  var row = ann && ann.length ? ann[0] : {};
  var pe = fe69_finRaw(v.pe);
  var price = fe69_finRaw(v.price);
  var rev = fe69_finRaw(row.revenue);
  var cap = fe69_finRaw(v.marketCap);
  return {
    tagged: tagged,
    pe: pe,
    peText: fe69_finRatio(pe),
    price: price,
    priceText: fe69_finPrice(price, pc),
    revenue: rev,
    revenueText: fe69_finStmt(rev, fc),
    marketCap: cap,
    marketCapText: fe69_finStmt(cap, fc),
    priceCurrency: pc,
    financialCurrency: fc
  };
}
// fe69-pure-end
var fe69_finOnce = Object.create(null);
function fe69_readFin(r) {
  var st = "";
  try { st = r && r.headers && r.headers.get ? (r.headers.get("X-Dispatch-Data-Status") || "") : ""; } catch (e) {}
  if (!r || !r.ok) return Promise.resolve(null);
  return r.json().then(function (d) { return d ? { data: d, status: st } : null; }).catch(function () { return null; });
}
function fe69_finRetry(tk) {
  if (!tk || fe69_finOnce[tk]) return;
  fe69_finOnce[tk] = true;
  setTimeout(function () { fe69_finRefetch(tk); }, 5000);
}
function fe69_finPut(tk, data, status) {
  if (!tk || !data || typeof _finCache === "undefined") return false;
  if (fe69_finPartial(data, status)) {
    fe69_finRetry(tk);
    return false;
  }
  _finCache[tk] = data;
  return true;
}
function fe69_finPaint(tk, data) {
  var cur = "";
  try { cur = (typeof IS_DESKTOP === "function" && IS_DESKTOP()) ? termSelTk : selTk; } catch (e) {}
  if (cur && cur !== tk) return;
  try { if (typeof _rt33Apply === "function") _rt33Apply(tk); } catch (e2) {}
  ["term-fin-root", "anlz-fin-root"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el && typeof renderFinancials === "function") el.innerHTML = renderFinancials(tk, data);
  });
  ["term-val-root", "anlz-val-root"].forEach(function (id) {
    var el = document.getElementById(id);
    if (!el || typeof renderValuation !== "function") return;
    var cache = { finData: data };
    if (typeof _valCache !== "undefined") {
      if (_valCache[tk]) cache = _valCache[tk];
      cache.finData = data;
      _valCache[tk] = cache;
    }
    el.innerHTML = renderValuation(tk, cache);
  });
}
function fe69_finRefetch(tk) {
  fetch("/api/financials?symbol=" + encodeURIComponent(tk)).then(function (r) {
    return fe69_readFin(r);
  }).then(function (pack) {
    if (!pack || !pack.data || fe69_finPartial(pack.data, pack.status)) return;
    _finCache[tk] = pack.data;
    fe69_finPaint(tk, pack.data);
  }).catch(function () {});
}
var fe69_bootDone = false, fe69_bootArmed = false, fe69_filingsOn = false, fe69_seen = Object.create(null), fe69_sess = Object.create(null), fe69_extra = Object.create(null), fe69_win = Object.create(null), fe69_hlOnce = Object.create(null);
function fe69_cap(p, ms, fallback) {
  return new Promise(function (resolve) {
    var done = false;
    var t = setTimeout(function () { if (!done) { done = true; resolve(fallback); } }, ms);
    Promise.resolve(p).then(function (v) {
      if (done) return;
      done = true;
      clearTimeout(t);
      resolve(v);
    }, function () {
      if (done) return;
      done = true;
      clearTimeout(t);
      resolve(fallback);
    });
  });
}
function fe69_paintBoot() {
  if (fe69_bootDone) return;
  fe69_bootDone = true;
  try { if (typeof renderTape === "function") renderTape(); } catch (e) {}
  try { if (typeof pg !== "undefined" && pg === "home" && typeof _refreshHomeAfterPrices === "function") _refreshHomeAfterPrices(); } catch (e2) {}
  try { if (typeof IS_DESKTOP === "function" && IS_DESKTOP() && typeof _rt53RTP === "function") _rt53RTP(); } catch (e3) {}
}
function fe69_armBoot() {
  if (fe69_bootArmed) return;
  fe69_bootArmed = true;
  setTimeout(fe69_paintBoot, 2500);
}
function fe69_allowFilings() { return !!fe69_filingsOn; }
function fe69_older(tk, q) {
  try {
    var srcIn = String((q && (q.source || q.src)) || "");
    var snapIn = !!(q && (q.cached === true || /last-good|session-cache/.test(srcIn)));
    var cur = "";
    try { cur = String((liveQuoteSrc && liveQuoteSrc[tk]) || ""); } catch (e1) { cur = ""; }
    var curSnap = cur === "session-cache" || !!(typeof liveQuoteCached !== "undefined" && liveQuoteCached && liveQuoteCached[tk]);
    if (!snapIn && curSnap) return false;
  } catch (e) {}
  return fe68_older(tk, q);
}
function fe69_noteQuote(tk, q) {
  if (!tk || !q) return;
  fe69_seen[tk] = { at: Date.now(), status: q.status || "", delayMin: typeof q.delayMin === "number" ? q.delayMin : null };
}
function fe69_fixMeta(tk, m) {
  var bag = null;
  try { bag = fe64_yqBag(tk); } catch (e) { bag = null; }
  var seen = fe69_seen[tk];
  if (seen && seen.delayMin > 0 && (!bag || !(bag.delayMin > 0))) bag = Object.assign({}, bag || {}, { delayMin: seen.delayMin, status: seen.status || (bag && bag.status) });
  return fe69_reconcile(m, bag);
}
function fe69_paintLookup(sym, priceInfo, seq) {
  if (seq !== _lookupSeq || !priceInfo || !(priceInfo.p > 0)) return;
  try {
    _applyLiveQuote(sym, Object.assign({}, priceInfo, {
      p: priceInfo.p,
      c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
      prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined
    }, (typeof fe64_yqFields === "function" ? fe64_yqFields(priceInfo) : {})), "yahoo");
  } catch (e) {}
  var quoteMeta = {};
  try { quoteMeta = _quoteMeta(sym) || {}; } catch (e2) { quoteMeta = {}; }
  var live = null, ch = null;
  try { if (typeof hasSyncedQuote === "function" && hasSyncedQuote(sym)) { live = livePx(sym); ch = liveChg(sym); } } catch (e3) {}
  _dynData = {
    name: priceInfo.name || sym,
    exchange: priceInfo.exchange || "",
    type: "",
    price: priceInfo.p,
    chgPct: typeof priceInfo.c === "number" ? priceInfo.c : 0,
    chgAbs: priceInfo.p - (priceInfo.prev || priceInfo.p),
    prev: priceInfo.prev || priceInfo.p,
    chart: (_dynData && _dynData.chart) || [],
    news: (_dynData && _dynData.news) || [],
    fe69Search: (_dynData && _dynData.fe69Search === "done") ? "done" : "loading",
    fe69Chart: (_dynData && _dynData.chart && _dynData.chart.length >= 5) ? "done" : ((_dynData && _dynData.fe69Chart === "fail") ? "fail" : "loading"),
    mc: "\u2014",
    ticker: sym,
    status: quoteMeta.status,
    source: quoteMeta.src || "yahoo",
    asOf: quoteMeta.asOf,
    livePrice: live != null ? live : priceInfo.p,
    liveChange: ch != null ? ch : (typeof priceInfo.c === "number" ? priceInfo.c : null)
  };
  _dynLoading = false;
  try { if (IS_DESKTOP()) renderP2(); else renderMain(); } catch (e4) {}
}
function fe69_css() {
  var st = document.createElement("style");
  st.setAttribute("data-fe69", "chat");
  st.textContent = "body.fe68-lenses .panel-grid{align-content:start!important;grid-template-rows:auto!important}body.fe68-lenses .panel{min-height:0!important;height:auto!important}body.fe68-lenses .panel-body{min-height:0!important}.fe69-win,.fe69-partial,.fe69-ph{font-family:var(--mn);font-size:11px;color:var(--t3);margin:4px 0}.fe69-src{display:block;margin-top:10px}.panel-grid.has-expanded>.panel.p-expanded>.panel-hdr{pointer-events:none}.panel-grid.has-expanded>.panel.p-expanded>.panel-hdr button,.panel-grid.has-expanded>.panel.p-expanded>.panel-hdr a{pointer-events:auto;position:relative;z-index:5}.panel-hdr-r .hdr-act-btn,.panel-hdr-r .p-exp-btn{flex:0 0 auto;position:relative;z-index:2}.chat-body p+p{margin-top:8px}";
  document.head.appendChild(st);
}
try { fe69_css(); } catch (e) {}
async function fe69_sessionBars(tk) {
  var sym = tk;
  try { sym = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk; } catch (e) { sym = tk; }
  try {
    var res = await chartFetch("/api/yahoo-chart?symbol=" + encodeURIComponent(sym) + "&range=6mo&interval=1d", { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return null;
    var data = await res.json();
    var result = data && data.chart && data.chart.result && data.chart.result[0];
    var q = result && result.indicators && result.indicators.quote && result.indicators.quote[0];
    if (!q) return null;
    var C = q.close || [], H = q.high || [], L = q.low || [], closes = [], hi = 0, lo = 0, i, meta = (result && result.meta) || {};
    for (i = 0; i < C.length; i++) if (typeof C[i] === "number" && isFinite(C[i]) && C[i] > 0) closes.push(C[i]);
    for (i = C.length - 1; i >= 0; i--) {
      if (typeof H[i] === "number" && typeof L[i] === "number" && H[i] > 0 && L[i] > 0 && H[i] !== L[i]) { hi = H[i]; lo = L[i]; break; }
    }
    if (!(hi > 0) && Number(meta.regularMarketDayHigh) > 0 && Number(meta.regularMarketDayLow) > 0 && Number(meta.regularMarketDayHigh) !== Number(meta.regularMarketDayLow)) {
      hi = Number(meta.regularMarketDayHigh);
      lo = Number(meta.regularMarketDayLow);
    }
    if (!(hi > 0) || !(lo > 0) || closes.length < 3) return null;
    return { h: hi, l: lo, closes: closes.slice(-60) };
  } catch (e2) { return null; }
}
function fe69_fillHl(tk) {
  if (!tk || fe69_hlOnce[tk]) return;
  fe69_hlOnce[tk] = 1;
  fe69_sessionBars(tk).then(function (bars) {
    if (!bars) return;
    try { fe68_day[tk] = { h: bars.h, l: bars.l }; } catch (e) {}
    fe69_sess[tk] = bars;
    try {
      var viewing = (typeof termSelTk !== "undefined" && termSelTk === tk) || (typeof selTk !== "undefined" && selTk === tk) || (typeof _dynTk !== "undefined" && _dynTk === tk);
      if (!viewing) return;
      if (typeof IS_DESKTOP === "function" && IS_DESKTOP()) renderP2();
      else renderMain();
    } catch (e2) {}
  });
}
function fe69_hlHtml(tk) {
  try { if (typeof fe66_nonUs !== "function" || !fe66_nonUs(tk)) return ""; } catch (e) { return ""; }
  var hl = (typeof fe68_day !== "undefined" && fe68_day[tk]) || fe69_sess[tk] || {};
  var h = Number(hl.h), l = Number(hl.l), px = 0;
  try { px = P[tk] && P[tk].p; } catch (e2) { px = 0; }
  if (!(h > 0) || !(l > 0) || h === l || (px > 0 && Math.abs(h - px) < 1e-6 && Math.abs(l - px) < 1e-6)) {
    fe69_fillHl(tk);
    return "";
  }
  var money = function (n) { try { return fe66_money(tk, n); } catch (e3) { return String(n); } };
  return '<div class="fe68-hl"><span>High ' + money(h) + '</span><span>Low ' + money(l) + '</span></div>';
}
function fe69_chartFallback(tk, range, container) {
  fe69_sessionBars(tk).then(function (bars) {
    if (!container || !container.isConnected) return;
    if (!bars) {
      var note = "Chart unavailable";
      try { note = fe65b_chartNote(tk); } catch (e) {}
      var name = tk;
      try { name = _escHtml(tk); } catch (e2) {}
      container.innerHTML = '<div class="dispatch-chart-unavailable">Chart unavailable for ' + name + '<br><span>' + note + '</span></div>';
      return;
    }
    try { fe68_day[tk] = { h: bars.h, l: bars.l }; } catch (e3) {}
    fe69_sess[tk] = bars;
    var closes = bars.closes, mn = Math.min.apply(null, closes), mx = Math.max.apply(null, closes), rng = (mx - mn) || 1;
    var pts = closes.map(function (v, n) { return ((n / (closes.length - 1)) * 300) + "," + (50 - ((v - mn) / rng) * 44); }).join(" ");
    var money = function (n) { try { return fe66_money(tk, n); } catch (e4) { return String(n); } };
    container.innerHTML = '<div class="fe68-svgchart"><svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block"><polyline points="' + pts + '" fill="none" stroke="var(--bl)" stroke-width="1.5"/></svg><div class="fe68-hl"><span>High ' + money(bars.h) + '</span><span>Low ' + money(bars.l) + '</span></div></div>';
  });
}
function fe69_equities() {
  var out = [];
  try {
    getActiveWl().tickers.forEach(function (tk) {
      if (!tk) return;
      var u = String(tk).toUpperCase();
      var a = null;
      try { a = (typeof A !== "undefined" ? A : []).find(function (x) { return x && String(x.tk).toUpperCase() === u; }); } catch (e2) { a = null; }
      if (a && (a.cat === "Crypto" || a.cat === "FX" || a.cat === "Commodity" || a._rt43)) return;
      if (/\./.test(u) || !/^[A-Z]{1,5}$/.test(u)) return;
      if (out.indexOf(u) < 0) out.push(u);
    });
  } catch (e) {}
  return out;
}
function fe69_premium() {
  try { return typeof _isPremium === "function" && !!_isPremium(); } catch (e) { return false; }
}
function fe69_rowKey(row) {
  return [row.insiderName || row.insider || "", row.transactionDate || row.filingDate || row.date || "", row.shares, row.value, row.transactionCode || ""].join("|");
}
function fe69_mergeRows(base, extra) {
  var seen = Object.create(null), out = [];
  (base || []).concat(extra || []).forEach(function (row) {
    if (!row) return;
    var k = fe69_rowKey(row);
    if (seen[k]) return;
    seen[k] = 1;
    out.push(row);
  });
  return out;
}
function fe69_insRow(row) {
  var link = row.filingUrl ? ' <a href="' + fe68_esc(row.filingUrl) + '" target="_blank" rel="noopener noreferrer">Filing</a>' : "";
  var span = fe69_insSpan(row.shares, row.value);
  return '<div class="institutional-row"><strong>' + fe68_esc(row.insiderName || "Insider") + '</strong><span>' + fe68_esc(row.insiderRole || "") + '</span><span>' + fe68_esc(row.codeLabel || row.transactionCode || "") + span + '</span><small>' + fe68_esc(row.transactionDate || row.filingDate || "") + link + '</small></div>';
}
function fe69_insHtml(tk, data, err) {
  var ui = fe68_insUi[tk] || (fe68_insUi[tk] = { all: false, house: false });
  var premium = fe69_premium();
  var h = '<div class="fe68-ins">';
  if (err === "unknown") return h + '<p class="ex">Unknown ticker.</p></div>';
  if (err) return h + '<p class="ex">' + fe68_esc(err) + '</p></div>';
  if (!data) return h + '<p class="ex">Loading insider filings…</p></div>';
  if (data.unavailable) return h + '<p class="ex">' + fe68_esc(data.message || "Insider filings unavailable right now") + '</p></div>';
  var ex = data.explainer || {};
  if (ex.what) h += '<p class="ex"><strong>What.</strong> ' + fe68_esc(ex.what) + '</p>';
  if (ex.where) h += '<p class="ex"><strong>Where.</strong> ' + fe68_esc(ex.where) + '</p>';
  if (ex.why) h += '<p class="ex"><strong>Why.</strong> ' + fe68_esc(ex.why) + '</p>';
  var win = (data.meta && data.meta.window) || fe69_win[tk] || null;
  if (win && win.label) h += '<p class="ex fe69-win">' + fe68_esc(win.label) + '</p>';
  if (data.meta && data.meta.partial) h += '<p class="ex fe69-partial">Still loading older filings, refresh in a moment</p>';
  if (data.stale) h += '<p class="ex">Last saved copy' + (data.asOf ? " \u00b7 " + fe68_esc(data.asOf) : "") + '.</p>';
  if (premium) {
    h += '<div class="fe68-hl"><button type="button" class="hdr-act-btn" onclick="fe68_insUi[\'' + tk + '\'].all=' + (ui.all ? 'false' : 'true') + ';fe69_extra[\'' + tk + '\']=[];fe68_loadInsiders(\'' + tk + '\')">' + (ui.all ? 'Open-market only' : 'Awards and exercises') + '</button>';
    h += '<button type="button" class="hdr-act-btn" onclick="fe68_insUi[\'' + tk + '\'].house=' + (ui.house ? 'false' : 'true') + ';fe68_loadInsiders(\'' + tk + '\')">' + (ui.house ? 'Hide House' : 'House filings') + '</button>';
    if (fe69_hasNext(win)) h += '<button type="button" class="hdr-act-btn" onclick="fe69_loadOlder(\'' + tk + '\')">Load older</button>';
    h += '</div>';
  }
  var rows = fe69_mergeRows(Array.isArray(data.insider) ? data.insider : [], fe69_extra[tk] || []);
  if (!rows.length) h += '<p class="ex">' + fe68_esc(data.note || "No Form 4 filings for this ticker.") + '</p>';
  else {
    h += rows.map(fe69_insRow).join("");
    if (data.meta && data.meta.limited) h += '<div class="institutional-row"><strong>See full history with Premium</strong><span>Five open-market rows are shown here.</span></div>';
  }
  if (premium && data.house && Array.isArray(data.house.items)) {
    var houseLabel = data.house.label || "House.";
    h += '<p class="ex"><strong>' + fe68_esc(houseLabel) + '</strong></p>';
    if (data.house.note) h += '<p class="ex">' + fe68_esc(data.house.note) + '</p>';
    data.house.items.forEach(function (item) {
      h += '<div class="institutional-row"><strong>' + fe68_esc(item.member || "Member") + '</strong><span>' + fe68_esc(item.filingDate || "") + '</span><span>' + fe68_esc(item.note || "See filing") + '</span>' + (item.pdfUrl ? '<a href="' + fe68_esc(item.pdfUrl) + '" target="_blank" rel="noopener noreferrer">Filing</a>' : '') + '</div>';
    });
  }
  return h + '</div>';
}
function fe69_insRoot(rootId) {
  var root = rootId ? document.getElementById(rootId) : null;
  if (!root) {
    var panes = document.querySelectorAll("#term-ins-root, #anlz-ins-root");
    for (var i = 0; i < panes.length; i++) { if (panes[i].getClientRects().length) root = panes[i]; }
    if (!root && panes.length) root = panes[panes.length - 1];
  }
  return root;
}
async function fe69_fetchIns(url) {
  var last = null, i, res, data;
  for (i = 0; i < 2; i++) {
    try {
      res = await fetch(url, { credentials: "include", signal: AbortSignal.timeout(12000) });
      data = await res.json().catch(function () { return {}; });
      return { res: res, data: data };
    } catch (e) { last = e; }
  }
  throw last || new Error("unavailable");
}
async function fe69_loadInsiders(tk, rootId) {
  var root = fe69_insRoot(rootId);
  if (!tk) return;
  if (root) root.innerHTML = fe69_insHtml(tk, null, "");
  var ui = fe68_insUi[tk] || (fe68_insUi[tk] = { all: false, house: false });
  var premium = fe69_premium();
  var q = "/api/insiders?t=" + encodeURIComponent(tk);
  if (premium && ui.all) q += "&codes=all";
  if (premium && ui.house) q += "&house=1";
  try {
    var got = await fe69_fetchIns(q);
    var data = got.data || {};
    if (data.meta && data.meta.window) fe69_win[tk] = data.meta.window;
    var html = got.res.status === 404 ? fe69_insHtml(tk, null, "unknown") : fe69_insHtml(tk, data, data && data.unavailable ? (data.message || "Insider filings unavailable right now") : "");
    if (root) root.innerHTML = html;
    fe69_loadInsiders.last = data;
  } catch (e) {
    if (root) root.innerHTML = fe69_insHtml(tk, null, "Insider filings unavailable right now");
  }
}
async function fe69_loadOlder(tk) {
  if (!fe69_premium()) return;
  var win = fe69_win[tk];
  if (!fe69_hasNext(win)) return;
  var before = fe69_beforeDate(win);
  if (!before) return;
  var ui = fe68_insUi[tk] || { all: false, house: false };
  var q = "/api/insiders?t=" + encodeURIComponent(tk) + "&before=" + encodeURIComponent(before);
  if (ui.all) q += "&codes=all";
  if (ui.house) q += "&house=1";
  try {
    var got = await fe69_fetchIns(q);
    var data = got.data || {};
    if (data.meta && data.meta.window) fe69_win[tk] = data.meta.window;
    else fe69_win[tk] = Object.assign({}, win, { next: "" });
    fe69_extra[tk] = fe69_mergeRows(fe69_extra[tk] || [], data.insider || []);
    var root = fe69_insRoot("");
    var base = fe69_loadInsiders.last || { insider: [], explainer: data.explainer, meta: {} };
    base.meta = Object.assign({}, base.meta || {}, data.meta || {}, { window: fe69_win[tk] });
    base.insider = base.insider || [];
    if (data.house) base.house = data.house;
    if (root) root.innerHTML = fe69_insHtml(tk, base, "");
  } catch (e) {}
}
async function fe69_newsInsiders(force) {
  fe69_filingsOn = true;
  if (_institutionalLoading.insider || (!force && _institutionalData.insider)) return;
  _institutionalLoading.insider = true;
  _institutionalError.insider = "";
  try { _refreshNewsView(); } catch (e) {}
  var tks = fe69_equities();
  var items = [], notes = [], explainer = null, asOf = "", failed = 0, byTk = {}, partial = false;
  var packed = await Promise.all(tks.map(async function (tk) {
    try {
      var got = await fe69_fetchIns("/api/insiders?t=" + encodeURIComponent(tk));
      return { tk: tk, res: got.res, data: got.data || {} };
    } catch (e2) { return { tk: tk, error: true }; }
  }));
  packed.forEach(function (pack) {
    var tk = pack.tk, data = pack.data || {};
    if (pack.error) { failed++; notes.push(tk + ": Insider filings unavailable right now"); return; }
    if (pack.res && pack.res.status === 404) { notes.push(tk + ": " + (data.error || "Unknown ticker.")); return; }
    if (data.unavailable) { failed++; notes.push(tk + ": " + (data.message || "Insider filings unavailable right now")); return; }
    if (data.explainer) explainer = data.explainer;
    if (data.asOf) asOf = data.asOf;
    if (data.meta && data.meta.partial) partial = true;
    byTk[tk] = { window: (data.meta && data.meta.window) || null, partial: !!(data.meta && data.meta.partial) };
    if (data.meta && data.meta.window) fe69_win[tk] = data.meta.window;
    if (!data.insider || !data.insider.length) { if (data.note) notes.push(tk + ": " + data.note); return; }
    data.insider.forEach(function (row) {
      items.push({ ticker: tk, insider: row.insiderName, role: row.insiderRole, transactionType: row.codeLabel || row.transactionCode, shares: row.shares, value: row.value, date: row.transactionDate || row.filingDate, sourceUrl: row.filingUrl });
    });
  });
  _institutionalData.insider = { items: items, source: "SEC EDGAR", asOf: asOf, explainer: explainer, note: notes.filter(Boolean).join(" \u00b7 "), status: !items.length && failed === tks.length ? "unavailable" : "", byTk: byTk, partial: partial };
  _institutionalLoading.insider = false;
  try { _refreshNewsView(); } catch (e3) {}
}
async function fe69_loadOlderNews(tk) {
  if (!fe69_premium() || !fe69_hasNext(fe69_win[tk])) return;
  var before = fe69_beforeDate(fe69_win[tk]);
  if (!before) return;
  try {
    var got = await fe69_fetchIns("/api/insiders?t=" + encodeURIComponent(tk) + "&before=" + encodeURIComponent(before));
    var data = got.data || {};
    var d = _institutionalData.insider || { items: [], byTk: {} };
    if (data.meta && data.meta.window) { fe69_win[tk] = data.meta.window; d.byTk[tk] = { window: data.meta.window, partial: !!data.meta.partial }; }
    else { fe69_win[tk] = Object.assign({}, fe69_win[tk] || {}, { next: "" }); if (d.byTk[tk]) d.byTk[tk].window = fe69_win[tk]; }
    (data.insider || []).forEach(function (row) {
      d.items.push({ ticker: tk, insider: row.insiderName, role: row.insiderRole, transactionType: row.codeLabel || row.transactionCode, shares: row.shares, value: row.value, date: row.transactionDate || row.filingDate, sourceUrl: row.filingUrl });
    });
    _institutionalData.insider = d;
    try { _refreshNewsView(); } catch (e2) {}
  } catch (e) {}
}
function fe69_newsHead(d) {
  if (!d) return "";
  var h = "", premium = fe69_premium();
  if (d.partial) h += '<p class="ex fe69-partial">Still loading older filings, refresh in a moment</p>';
  var by = d.byTk || {};
  Object.keys(by).forEach(function (tk) {
    var w = by[tk] && by[tk].window;
    if (w && w.label) h += '<p class="ex fe69-win">' + fe68_esc(tk + " \u00b7 " + w.label) + '</p>';
    if (premium && fe69_hasNext(w)) h += '<button type="button" class="hdr-act-btn" onclick="fe69_loadOlderNews(\'' + tk + '\')">Load older</button>';
  });
  return h ? '<div class="fe68-ins">' + h + '</div>' : "";
}
try { fe68_bookFive = fe69_equities; } catch (e) {}
try { fe68_insRow = fe69_insRow; } catch (e) {}
try { fe68_insHtml = fe69_insHtml; } catch (e) {}
try { fe68_loadInsiders = fe69_loadInsiders; } catch (e) {}
try { fe68_newsInsiders = fe69_newsInsiders; } catch (e) {}
try {
  var fe69_qm = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe69_qm.apply(this, arguments);
    try { m = fe69_fixMeta(tk, m); } catch (e) {}
    return m;
  };
} catch (e) {}
try {
  var fe69_sl = _quoteSourceLabel;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe69_sl.apply(this, arguments); } catch (e) { out = String(src || ""); }
    out = fe69_words(out);
    if (/gold-api/i.test(String(src || ""))) return /metal/i.test(String(src || "")) ? "Spot metal" : "Spot gold";
    if (/free gold feed/i.test(out)) return "Spot gold";
    return out;
  };
} catch (e) {}
try {
  var fe69_ri = _renderInstitutionalIntelligence;
  _renderInstitutionalIntelligence = function () {
    var h = String(fe69_ri.apply(this, arguments) || "");
    try {
      if (_institutionalTab === "insider" && _institutionalData && _institutionalData.insider) {
        var cap = fe69_newsHead(_institutionalData.insider);
        if (cap) {
          if (h.indexOf('<div class="institutional-list">') >= 0) h = h.replace('<div class="institutional-list">', cap + '<div class="institutional-list">');
          else h = cap + h;
        }
      }
    } catch (e2) {}
    return h;
  };
} catch (e) {}
try {
  var fe69_nav = nav;
  nav = function (p) {
    var r = fe69_nav.apply(this, arguments);
    try {
      if (p === "news") {
        fe69_filingsOn = true;
        if (typeof _loadInstitutional === "function") _loadInstitutional("insider");
      }
    } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe69_rn = renderNews;
  renderNews = function () {
    try { fe69_filingsOn = true; setTimeout(function () { if (typeof _loadInstitutional === "function") _loadInstitutional("insider"); }, 40); } catch (e) {}
    return fe69_rn.apply(this, arguments);
  };
} catch (e) {}
function fe69_takeChart(sym, seq, chart) {
  if (seq !== _lookupSeq || !_dynData || !(_dynData.price > 0)) return;
  if (String(_dynTk || "") !== String(sym || "") && String(_dynData.ticker || "") !== String(sym || "")) return;
  if (Array.isArray(chart) && chart.length >= 5) {
    _dynData.chart = chart;
    _dynData.fe69Chart = "done";
    try { HIST[sym] = chart.slice(-60); } catch (e) {}
  } else {
    _dynData.fe69Chart = "fail";
  }
  try { if (IS_DESKTOP()) renderP2(); else renderMain(); } catch (e2) {}
}
function fe69_placeAsk() {
  var btn = document.querySelector("[data-fe69-ask]");
  if (!btn) {
    var home0 = document.querySelector("#p1 .panel-hdr-r");
    btn = home0 && home0.querySelector("button.hdr-act-btn");
    if (!btn) return;
    btn.setAttribute("data-fe69-ask", "1");
  }
  var exp = document.querySelector("#p2.p-expanded .panel-hdr-r");
  var home = document.querySelector("#p1 .panel-hdr-r");
  var host = exp || home;
  if (!host || btn.parentElement === host) return;
  var anchor = host.querySelector(".p-exp-btn");
  if (anchor) host.insertBefore(btn, anchor);
  else host.appendChild(btn);
}
function fe69_openAsk(question) {
  try {
    if (typeof _isPremium === "function" && !_isPremium()) {
      if (typeof _showLoginGate === "function") _showLoginGate("Dispatch Research Assistant");
      return;
    }
  } catch (e) {}
  try { if (!document.getElementById("chatPanel") && typeof initChatWidget === "function") initChatWidget(); } catch (e2) {}
  try { if (typeof _chatOpen !== "undefined" && !_chatOpen && typeof toggleChat === "function") toggleChat(); } catch (e3) {}
  var panel = document.getElementById("chatPanel");
  if (panel) {
    panel.classList.remove("hide");
    try { _chatOpen = true; document.body.classList.add("chat-open"); } catch (e4) {}
  }
  var inp = document.getElementById("chatInp");
  if (inp && question) { inp.value = question; try { inp.focus(); } catch (e5) {} }
}
var fe69_asked = {};
function fe69_intelTk() {
  try {
    if (typeof termSelTk !== "undefined" && termSelTk && typeof _expPanel !== "undefined" && _expPanel === "p2") return String(termSelTk);
  } catch (e) {}
  try {
    if (typeof pg !== "undefined" && pg === "anlz" && typeof selTk !== "undefined" && selTk) return String(selTk);
  } catch (e2) {}
  try {
    if (typeof location !== "undefined" && /^\/markets\/?$/.test(location.pathname || "")) {
      var q = new URLSearchParams(location.search).get("t");
      if (q) return String((typeof resolveInternalTicker === "function" && resolveInternalTicker(q)) || q);
    }
  } catch (e3) {}
  return "";
}
function fe69_askHead(btn) {
  var head = "";
  try {
    var card = btn && btn.closest ? btn.closest(".si-card, #siteIntelCard") : null;
    var el = card && card.querySelector(".si-headline");
    if (!el) el = document.querySelector("#siteIntelCard .si-headline, .si-card .si-headline, #siteIntelBar .si-bar-chunk");
    if (el) head = String(el.textContent || "").replace(/\s+/g, " ").trim();
  } catch (e) {}
  if (!head) { try { head = fe69_intelTk(); } catch (e2) {} }
  return head || "markets right now";
}
function fe69_askCard(btn) {
  try {
    if (typeof _isPremium === "function" && !_isPremium()) {
      if (typeof _showLoginGate === "function") _showLoginGate("Dispatch Research Assistant");
      return;
    }
  } catch (e) {}
  try { if (!document.getElementById("chatPanel") && typeof initChatWidget === "function") initChatWidget(); } catch (e2) {}
  try { if (typeof _chatOpen !== "undefined" && !_chatOpen && typeof toggleChat === "function") toggleChat(); } catch (e3) {}
  var panel = document.getElementById("chatPanel");
  if (panel) {
    panel.classList.remove("hide");
    try { _chatOpen = true; document.body.classList.add("chat-open"); } catch (e4) {}
  }
  var tk = "markets";
  try { tk = fe69_intelTk() || "markets"; } catch (e5) {}
  var key = String(tk).toUpperCase();
  if (fe69_asked[key]) return;
  var inp = document.getElementById("chatInp");
  if (!inp || typeof sendChatMessage !== "function") return;
  fe69_asked[key] = 1;
  inp.value = "What matters most about " + fe69_askHead(btn) + "?";
  try { sendChatMessage(); } catch (e6) {}
}
function fe69_regimeAi(ai) {
  if (!ai || typeof ai !== "object") return false;
  var head = typeof ai.headline === "string" ? ai.headline : "";
  return /^(?:current\s+)?market\b/i.test(head) || /^market regime:/i.test(head);
}
try { _openResearchAssistant = fe69_openAsk; } catch (e) {}
try { fe69_placeAsk(); } catch (e) {}
try {
  var fe69_merge0 = _mergeIntel;
  _mergeIntel = function (surface, extra) {
    var tk = "";
    try { tk = (extra && extra.tk) || (surface === "ticker" ? fe69_intelTk() : ""); } catch (e) {}
    if (surface === "ticker" && tk) {
      var prev = null, nulled = false;
      try {
        var ai = _siteIntel.ai;
        var other = ai && _siteIntel.tk && String(_siteIntel.tk).toUpperCase() !== String(tk).toUpperCase();
        if (ai && (other || fe69_regimeAi(ai))) { prev = ai; _siteIntel.ai = null; nulled = true; }
      } catch (e2) {}
      try { return fe69_merge0.apply(this, arguments); }
      finally { if (nulled) { try { _siteIntel.ai = prev; } catch (e3) {} } }
    }
    return fe69_merge0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe69_cur0 = _rt27CurTk;
  _rt27CurTk = function () {
    var v = "";
    try { v = String(fe69_cur0.apply(this, arguments) || ""); } catch (e) {}
    if (v) return v;
    try { return fe69_intelTk(); } catch (e2) { return ""; }
  };
} catch (e) {}
try {
  var fe69_paint0 = _paintSiteIntelBar;
  _paintSiteIntelBar = function () {
    var tk = "";
    try { tk = fe69_intelTk(); } catch (e) {}
    if (tk) {
      try { _siteIntel.surface = "ticker"; } catch (e2) {}
    }
    return fe69_paint0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe69_page0 = _onPageIntel;
  _onPageIntel = function (surface, extra) {
    var tk = "";
    try { tk = fe69_intelTk(); } catch (e) {}
    if (tk) {
      surface = "ticker";
      extra = extra || {};
      if (!extra.tk) extra.tk = tk;
    }
    return fe69_page0.call(this, surface, extra);
  };
} catch (e) {}
try {
  var fe69_ai0 = _fetchSiteIntelAI;
  _fetchSiteIntelAI = function (surface, extra) {
    var tk = "";
    try { tk = fe69_intelTk(); } catch (e) {}
    if (tk && surface !== "ticker") {
      surface = "ticker";
      extra = Object.assign({}, extra || {}, { tk: (extra && extra.tk) || tk });
    }
    return fe69_ai0.call(this, surface, extra);
  };
} catch (e) {}
try { _intelBarSig = ""; if (typeof _paintSiteIntelBar === "function") _paintSiteIntelBar(); } catch (e) {}
try {
  var fe69c = document.getElementById("siteIntelCard");
  var fe69t = fe69_intelTk();
  if (fe69c && fe69t && typeof _renderSiteIntelCard === "function") {
    var fe69box = document.createElement("div");
    fe69box.innerHTML = _renderSiteIntelCard("ticker", { tk: fe69t });
    if (fe69box.firstElementChild) fe69c.replaceWith(fe69box.firstElementChild);
  }
} catch (e) {}
'''

s = subn(s, '''      const open = IS_DESKTOP() ? (termSelTk === want && _expPanel === "p2") : (pg === "anlz" && selTk === want);''',
'''      const dyn = typeof _dynTk !== "undefined" && _dynTk === want;
      const open = dyn || (IS_DESKTOP() ? (termSelTk === want && _expPanel === "p2") : (pg === "anlz" && selTk === want));''',
    'dyn lookup stays open')
s = subn(s, '''    const [priceRes,searchRes,chartData]=await Promise.allSettled([
      fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSym)}`,{signal:AbortSignal.timeout(8000)}),
      fetch(`/api/search?q=${encodeURIComponent(sym)}`,{signal:AbortSignal.timeout(5000)}),
      Promise.race([fetchYahooIntraday(yhSym),new Promise(r=>setTimeout(()=>r(null),9000))]),
    ]);
    if(seq!==_lookupSeq)return;

    let priceJson=priceRes.status==='fulfilled'&&priceRes.value.ok?await priceRes.value.json():{};
    let priceInfo=priceJson[yhSym]||priceJson[sym]||null;
    if((!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0))&&fe68Ready&&typeof fe68Ready.p==="number"&&fe68Ready.p>0)priceInfo=fe68Ready;
    if(priceInfo&&!(typeof priceInfo.p==="number"&&priceInfo.p>0))priceInfo=null;

    const searchJson=searchRes.status==='fulfilled'&&searchRes.value.ok?await searchRes.value.json():{result:[]};''',
'''    const fe69ChartP=Promise.race([fetchYahooIntraday(yhSym),new Promise(r=>setTimeout(()=>r(null),9000))]).catch(()=>null);
    const fe69SearchP=fetch(`/api/search?q=${encodeURIComponent(sym)}`,{signal:AbortSignal.timeout(5000)}).then(r=>r.ok?r.json():{result:[]}).catch(()=>({result:[]}));
    let priceJson={};
    try{const priceRes=await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSym)}`,{signal:AbortSignal.timeout(8000)});if(priceRes.ok)priceJson=await priceRes.json();}catch(e){}
    if(seq!==_lookupSeq)return;
    let priceInfo=priceJson[yhSym]||priceJson[sym]||null;
    if((!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0))&&fe68Ready&&typeof fe68Ready.p==="number"&&fe68Ready.p>0)priceInfo=fe68Ready;
    if(priceInfo&&!(typeof priceInfo.p==="number"&&priceInfo.p>0))priceInfo=null;
    if(priceInfo&&seq===_lookupSeq){try{fe69_paintLookup(sym,priceInfo,seq);}catch(e){}}
    const searchJson=await fe69SearchP;
    if(seq!==_lookupSeq)return;''',
    'quote gates fetching')
s = subn(s, '''    let chart=chartData.status==='fulfilled'?chartData.value:null;
    if((!chart||chart.length<5)&&wireSym!==yhSym){
      try{chart=await fetchYahooIntraday(wireSym);}catch(e){/* keep prior */}
    }''',
'''    let chart=null;
    if(wireSym!==yhSym){
      Promise.race([fetchYahooIntraday(wireSym),new Promise(r=>setTimeout(()=>r(null),9000))]).catch(()=>null).then(c=>{try{fe69_takeChart(deskSym||sym,seq,c);}catch(e){}});
    }else{
      fe69ChartP.then(c=>{try{fe69_takeChart(deskSym||sym,seq,c);}catch(e){}});
    }''',
    'chart does not block')
s = subn(s, '''    if(!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0)){
      _dynData=null; // ticker not found on Yahoo/CoinGecko
    } else {''',
'''    if(!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0)){
      if(!_dynData||!(_dynData.price>0))_dynData=null;
    } else {''',
    'keep painted price')
s = subn(s, '''        chart:chart||[],
        news:newsArr,''',
'''        chart:(Array.isArray(chart)&&chart.length>=5)?chart:((_dynData&&Array.isArray(_dynData.chart))?_dynData.chart:[]),
        fe69Search:match?"done":"fail",
        fe69Chart:(Array.isArray(chart)&&chart.length>=5)?"done":((_dynData&&_dynData.fe69Chart)||"loading"),
        news:newsArr,''',
    'lookup slots')
s = subn(s, '''  }catch(e){_dynData=null;}''',
'''  }catch(e){if(!_dynData||!(_dynData.price>0))_dynData=null;}''',
    'lookup catch keeps price')
s = subn(s, '''           ${context}
        </div>''',
'''           ${context}
           ${d.fe69Search==="loading"?'<div class="fe69-ph">Looking up the listing…</div>':d.fe69Search==="fail"?'<div class="fe69-ph">Listing details unavailable</div>':''}
        </div>''',
    'search placeholder')
s = subn(s, '''        <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:4px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>
      </div>`;
    }
    // News''',
'''        <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:4px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>
      </div>`;
    } else if(d.fe69Chart==="loading"||d.fe69Chart==="fail"){
      h+=`<div class="fe69-ph" style="padding:8px">${d.fe69Chart==="loading"?"Loading chart…":"Chart unavailable"}</div>`;
    }
    // News''',
    'chart placeholder')
s = subn(s, '''  const hd=(d.chart||[]).filter(v=>typeof v==='number'&&isFinite(v)&&v>0);
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||1;const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${50-((v-mn)/rng)*44}`).join(' ');h+=`<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.08em;margin-bottom:4px">${fe66_dynHead(_dynTk)}</div><svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg><div style="font-family:var(--mn);font-size:10px;color:var(--t3);margin:4px 0 10px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>`;}''',
'''  const hd=(d.chart||[]).filter(v=>typeof v==='number'&&isFinite(v)&&v>0);
  h+=d.fe69Search==="loading"?'<div class="fe69-ph">Looking up the listing…</div>':d.fe69Search==="fail"?'<div class="fe69-ph">Listing details unavailable</div>':'';
  if(hd.length>=5){const mn=Math.min(...hd),mx=Math.max(...hd),rng=mx-mn||1;const pts=hd.map((v,i)=>`${(i/(hd.length-1))*300},${50-((v-mn)/rng)*44}`).join(' ');h+=`<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.08em;margin-bottom:4px">${fe66_dynHead(_dynTk)}</div><svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg><div style="font-family:var(--mn);font-size:10px;color:var(--t3);margin:4px 0 10px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>`;}
  else if(d.fe69Chart==="loading"||d.fe69Chart==="fail"){h+=`<div class="fe69-ph">${d.fe69Chart==="loading"?"Loading chart…":"Chart unavailable"}</div>`;}''',
    'mobile placeholders')
s = subn(s, '''  _syncDeskChrome();
  updateSidebarActive();
}

// Keyboard shortcuts''',
'''  _syncDeskChrome();
  updateSidebarActive();
  try { fe69_placeAsk(); } catch (e) {}
}

// Keyboard shortcuts''',
    'ask above ticker')
s = subn(s, '''function _chatMd(text) {
  // ── bb3b ── a numbered marker with no text is never an item
  if (!text) return "";''',
'''function _chatMd(text) {
  // ── bb3b ── a numbered marker with no text is never an item
  text = (typeof fe69_srcGap === "function") ? fe69_srcGap(text) : text;
  if (!text) return "";''',
    'ask sources break')
s = subn(s, '''      <div style="font-size:12px;color:var(--t2);line-height:1.65">${b.summary || ""}</div>''',
'''      <div style="font-size:12px;color:var(--t2);line-height:1.65">${typeof fe69_srcHtml==="function"?fe69_srcHtml(b.summary||""):(b.summary||"")}</div>''',
    'brief sources break')
s = subn(s, '''    <div style="font-size:10px;color:var(--t3);line-height:1.5">Sources: BEA''',
'''    <div class="fe69-src" style="font-size:10px;color:var(--t3);line-height:1.5">Sources: BEA''',
    'report sources space')
s = subn(s, '''      <button type="button" class="si-ask" onclick="toggleChat()" title="Ask Dispatch Expert">Ask →</button>''',
'''      <button type="button" class="si-ask" onclick="fe69_askCard(this)" title="Ask Dispatch Expert">Ask →</button>''',
    'ask auto send')
s = subn(s, '''        if (f.state === "score" && f.label) r.headline = String(tk).toUpperCase() + " \\u2014 " + f.label;
        else r.headline = r.headline.replace(/ — (Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral)\\b/, "");''',
'''        if (f.state === "score" && f.label) r.headline = String(tk).toUpperCase() + " \\u2014 " + f.label;''',
    'keep local fit label')
s = subn(s, '''      if (f.state === "score" && f.label) return x.replace(m[0], m[1] + " \\u2014 " + f.label);
      return x.replace(m[0], m[1]);''',
'''      if (f.state === "score" && f.label) return x.replace(m[0], m[1] + " \\u2014 " + f.label);
      return x;''',
    'keep headwind headline')
s = subn(s, '''try { if (localStorage.getItem("td_chat_v") !== "chat37") { _chatMsgs = []; sessionStorage.removeItem("td_chat"); localStorage.removeItem("td_chat"); localStorage.setItem("td_chat_v", "chat37"); } } catch (e) {}''',
'''try { if (localStorage.getItem("td_chat_v") !== "chat70") { _chatMsgs = []; sessionStorage.removeItem("td_chat"); localStorage.removeItem("td_chat"); localStorage.setItem("td_chat_v", "chat70"); } } catch (e) {}''',
    'chat version')
s = subn(s, '''  if (!_finCache[tk]) tasks.push(fetch("/api/financials?symbol=" + encodeURIComponent(tk)).then(r => r.ok ? r.json() : null).then(d => { if (d) _finCache[tk] = d; }).catch(() => {}));''',
'''  if (!_finCache[tk]) tasks.push(fetch("/api/financials?symbol=" + encodeURIComponent(tk)).then(r => fe69_readFin(r)).then(p => { if (p) fe69_finPut(tk, p.data, p.status); }).catch(() => {}));''',
    'lens fin cache')
s = subn(s, '''    let finData = _finCache[tk];
    if (!finData) {
      const res = await fetch('/api/financials?symbol='+encodeURIComponent(tk), { signal: AbortSignal.timeout(12000) });
      if (res.ok) { finData = await res.json(); _finCache[tk] = finData; }
    }''',
'''    let finData = _finCache[tk];
    let finStatus = "";
    if (!finData) {
      const res = await fetch('/api/financials?symbol='+encodeURIComponent(tk), { signal: AbortSignal.timeout(12000) });
      const pack = await fe69_readFin(res);
      if (pack) { finData = pack.data; finStatus = pack.status; fe69_finPut(tk, pack.data, pack.status); }
    }''',
    'valuation fetch')
s = subn(s, '''          const r = await fetch('/api/financials?symbol='+encodeURIComponent(peer), { signal: AbortSignal.timeout(8000) });
          if (r.ok) { peerData[peer] = await r.json(); _finCache[peer] = peerData[peer]; }''',
'''          const r = await fetch('/api/financials?symbol='+encodeURIComponent(peer), { signal: AbortSignal.timeout(8000) });
          const pack = await fe69_readFin(r);
          if (pack) { peerData[peer] = pack.data; fe69_finPut(peer, pack.data, pack.status); }''',
    'peer fin cache')
s = subn(s, '''    if (_valLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    // Price is read live in renderValuation — never freeze a $0 snapshot from pre-sync load
    _valCache[tk] = { finData, peerData, peers };
    el2.innerHTML = renderValuation(tk, _valCache[tk]);''',
'''    if (_valLoadTk !== tk) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    // Price is read live in renderValuation — never freeze a $0 snapshot from pre-sync load
    const shown = { finData, peerData, peers };
    if (!(typeof fe69_finPartial === "function" && fe69_finPartial(finData, finStatus))) _valCache[tk] = shown;
    el2.innerHTML = renderValuation(tk, shown);''',
    'valuation partial')
s = subn(s, '''    const res = await fetch(`/api/financials?symbol=${encodeURIComponent(tk)}`, { signal: AbortSignal.timeout(12000) });
    if (!res.ok) throw new Error('no data');
    const data = await res.json();
    if (_finTk !== tk || _finCid !== containerId) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    _finCache[tk] = data;
    el2.innerHTML = renderFinancials(tk, data);''',
'''    const res = await fetch(`/api/financials?symbol=${encodeURIComponent(tk)}`, { signal: AbortSignal.timeout(12000) });
    const pack = await fe69_readFin(res);
    if (!pack) throw new Error('no data');
    const data = pack.data;
    if (_finTk !== tk || _finCid !== containerId) return;
    const el2 = document.getElementById(containerId);
    if (!el2) return;
    fe69_finPut(tk, data, pack.status);
    el2.innerHTML = renderFinancials(tk, data);''',
    'financials partial')
s = subn(s, '''    if(!_finCache[tk])fetch('/api/financials?symbol='+encodeURIComponent(tk)).then(r=>r.ok?r.json():null).then(d=>{if(d)_finCache[tk]=d;}).catch(()=>{});''',
'''    if(!_finCache[tk])fetch('/api/financials?symbol='+encodeURIComponent(tk)).then(r=>fe69_readFin(r)).then(p=>{if(p)fe69_finPut(tk,p.data,p.status);}).catch(()=>{});''',
    'prefetch fin cache')
s = subn(s, '''function _rt32N(v, k) {
  if (v == null || !isFinite(v)) return "—";
  const a = Math.abs(v), sg = v < 0 ? "-" : "";
  if (k === "x") return v > 0 && v < 250 ? v.toFixed(1) + "×" : "n/m";
  if (k === "pct") return (v * 100).toFixed(2) + "%";
  if (k === "eps") return sg + "$" + a.toFixed(2);
  if (k === "n") return a >= 1e9 ? sg + (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? sg + (a / 1e6).toFixed(1) + "M" : a >= 1e3 ? sg + (a / 1e3).toFixed(0) + "K" : sg + a.toFixed(0);
  return sg + "$" + (a >= 1e12 ? (a / 1e12).toFixed(2) + "T" : a >= 1e9 ? (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a.toFixed(0));
}''',
'''function _rt32N(v, k, ccy) {
  if (v == null || !isFinite(v)) return "—";
  const a = Math.abs(v), sg = v < 0 ? "-" : "";
  if (k === "x") return v > 0 && v < 250 ? v.toFixed(1) + "×" : "n/m";
  if (k === "pct") return (v * 100).toFixed(2) + "%";
  if (k === "n") return a >= 1e9 ? sg + (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? sg + (a / 1e6).toFixed(1) + "M" : a >= 1e3 ? sg + (a / 1e3).toFixed(0) + "K" : sg + a.toFixed(0);
  if (ccy && typeof fe69_finPrice === "function") return k === "eps" ? fe69_finPrice(v, ccy) : fe69_finStmt(v, ccy);
  if (k === "eps") return sg + "$" + a.toFixed(2);
  return sg + "$" + (a >= 1e12 ? (a / 1e12).toFixed(2) + "T" : a >= 1e9 ? (a / 1e9).toFixed(2) + "B" : a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a.toFixed(0));
}''',
    'statement currency')
s = subn(s, '''  L.forEach(([lbl, k, kind]) => { o += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03)"><td style="padding:7px 10px;color:var(--t2);white-space:nowrap">${lbl}</td>${rows.map(r => `<td ${_rt32Td}>${_rt32N(r[k], kind)}</td>`).join("")}</tr>`; });''',
'''  const fe69fc = (typeof fe69_finTagged === "function" && fe69_finTagged(data)) ? data.financialCurrency : "";
  L.forEach(([lbl, k, kind]) => { o += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03)"><td style="padding:7px 10px;color:var(--t2);white-space:nowrap">${lbl}</td>${rows.map(r => `<td ${_rt32Td}>${_rt32N(r[k], kind, fe69fc)}</td>`).join("")}</tr>`; });''',
    'statement rows')
s = subn(s, '''  let o = _rt32Head(`VALUATION · ${_rt32E(tk)}${v.price ? " · at " + fe66_money(tk, v.price) : ""}`);
  o += `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:1px;background:rgba(255,255,255,0.04)">${M.map(([l, x, k]) => `<div style="background:var(--bg);padding:12px 14px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:4px">${l.toUpperCase()}</div><div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--tx)">${_rt32N(x, k)}</div></div>`).join("")}</div>`;''',
'''  const fe69bag = cache && cache.finData;
  const fe69tag = typeof fe69_finTagged === "function" && fe69_finTagged(fe69bag);
  const fe69pc = fe69tag ? fe69bag.priceCurrency : "";
  const fe69fc = fe69tag ? fe69bag.financialCurrency : "";
  const fe69px = v.price ? " · at " + (fe69pc ? fe69_finPrice(v.price, fe69pc) : fe66_money(tk, v.price)) : "";
  let o = _rt32Head(`VALUATION · ${_rt32E(tk)}${fe69px}`);
  o += `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:1px;background:rgba(255,255,255,0.04)">${M.map(([l, x, k]) => `<div style="background:var(--bg);padding:12px 14px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:4px">${l.toUpperCase()}</div><div style="font-family:var(--mn);font-size:18px;font-weight:800;color:var(--tx)">${_rt32N(x, k, k ? "" : fe69fc)}</div></div>`).join("")}</div>`;''',
    'valuation currency')
s = subn(s, '''function _rt33Mc(v) { if (v == null || !isFinite(v) || v <= 0) return "—"; return "$" + (v >= 1e12 ? (v / 1e12).toFixed(2) + "T" : v >= 1e9 ? (v / 1e9).toFixed(1) + "B" : (v / 1e6).toFixed(0) + "M"); }''',
'''function _rt33Mc(v, ccy) { if (v == null || !isFinite(v) || v <= 0) return "—"; const body = (v >= 1e12 ? (v / 1e12).toFixed(2) + "T" : v >= 1e9 ? (v / 1e9).toFixed(1) + "B" : (v / 1e6).toFixed(0) + "M"); if (ccy && ccy !== "USD" && typeof fe69_finSym === "function") { const s = fe69_finSym(ccy); return s.pre + body + s.post; } return "$" + body; }''',
    'market cap currency')
s = subn(s, '''  a.pe = v.pe > 0 ? v.pe.toFixed(1) + "x" : "—";
  a.mc = _rt33Mc(v.marketCap);''',
'''  const fe69bag = _finCache[tk];
  const fe69fc = (typeof fe69_finTagged === "function" && fe69_finTagged(fe69bag)) ? fe69bag.financialCurrency : "";
  a.pe = v.pe > 0 ? v.pe.toFixed(1) + "x" : "—";
  a.mc = _rt33Mc(v.marketCap, fe69fc);''',
    'apply market cap')
s = subn(s, '''    .then(r => r.ok ? r.json() : null).then(d => {
      if (d) _finCache[tk] = d;
      if (_rt33Apply(tk) && !wait) {''',
'''    .then(r => fe69_readFin(r)).then(p => {
      var d = p && p.data, applied = false;
      if (d) {
        if (!fe69_finPut(tk, d, p.status) && d.valuation) {
          _finCache[tk] = d;
          try { applied = _rt33Apply(tk); } catch (e) {}
          delete _finCache[tk];
        } else applied = _rt33Apply(tk);
      }
      if (applied && !wait) {''',
    'ensure partial')
s = subn(s, '''    if (r.ok) { const d = await r.json(); if (d && d.valuation) _finCache[tk] = d; }''',
'''    const pack = await fe69_readFin(r); if (pack && pack.data && pack.data.valuation) fe69_finPut(tk, pack.data, pack.status);''',
    'ask fin cache')
s = s + BLOCK
if "fe69_reconcile" not in s: die('helper missing')
if 'return "free gold feed"' in s: die('free gold feed still returned')
h2 = re.sub(r'app\.js\?v=chat\d+"', 'app.js?v=%s"' % nxt, h, count=1)
out = s.replace('\n', '\r\n').encode('utf-8') if crlf else s.encode('utf-8')
tmp = tempfile.NamedTemporaryFile('wb', suffix='.js', delete=False)
tmp.write(out); tmp.close()
try:
    chk = subprocess.run(['node', '--check', tmp.name], capture_output=True, text=True)
finally:
    os.unlink(tmp.name)
if chk.returncode != 0:
    die('node --check failed\n' + (chk.stderr or chk.stdout or ''))
if not CHECK:
    open(APP, 'wb').write(out)
    open(IDX, 'wb').write(h2.replace('\n', '\r\n').encode('utf-8') if hcrlf else h2.encode('utf-8'))
print('OK', nxt, 'app.md5', hashlib.md5(out).hexdigest())
