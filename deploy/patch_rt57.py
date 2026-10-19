#!/usr/bin/env python3
"""patch_rt57.py: client patch on chat68. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat68, the output of patch_rt56b.py on chat67:
  app.js md5 d798611d56f2a02ca346f05712fe12c0
  index.html md5 e12cba89c75dfa6550311cc41e3c0097
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

News tags follow the headline. Quote badges go through one formatter.
Exchange-suffixed lookups ask /api/yahoo-quote first. No server file is changed.

Usage: python3 patch_rt57.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "d798611d56f2a02ca346f05712fe12c0"
EXPECT_INDEX_MD5 = "e12cba89c75dfa6550311cc41e3c0097"
NEED_MARKER = "// ── rt56b ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt57 ──' in s: already('rt57 already applied')
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

# Topic first. The feed category is no longer allowed to override the headline.
s = subn(s, '''function fe65_storyTag(text, low, hit, feedCat, src) {
  var raw = String(text || "");
  if (!fe65_hasMarket(low, hit, raw)) return "Other";
  if (fe65_commoditySubject(raw)) return "Commodities";
  if (fe65_strictEquity(low, hit, raw)) return "Stocks";
  if (fe65_feedCrypto(feedCat, src)) return "Crypto";
  if (typeof fe64_cryptoStory === "function" && fe64_cryptoStory(low, hit)) return "Crypto";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};
  Object.keys(rules).forEach(function (tag) {
    if (tag === "Crypto" || tag === "Stocks" || tag === "Earnings") return;
    var cfg = rules[tag] || {}, keys = cfg.k || [], sc = 0;
    for (var i = 0; i < keys.length; i++) if (hit([keys[i]])) sc += cfg.w || 1;
    if (sc > bestScore) { bestScore = sc; best = tag; }
  });
  if (bestScore > 0 && typeof fe64_chip === "function") return fe64_chip(best);
  if (bestScore > 0) return best;
  if (feedCat && typeof fe64_chip === "function") return fe64_chip(feedCat);
  return "Other";
}''', '''function fe65_storyTag(text, low, hit, feedCat, src) {
  return fe68_storyTag(text, low, hit, feedCat, src);
}''', 'story tag')

s = subn(s, '  if (typeof n === "number" && isFinite(n) && n > 0) return "delayed " + Math.round(n) + "m by exchange";',
    '  if (typeof n === "number" && isFinite(n) && n > 0) return "delayed " + Math.round(n) + " min by exchange";',
    'delay minutes')

s = subn(s, '''  t = t.replace(/cached\\s*[·.\\-]?\\s*yh/ig, "CACHED");
  t = t.replace(/\\bxau\\s+spot\\s+proxy\\b/ig, "Gold");
  t = t.replace(/\\bspot\\s+proxy\\b/ig, "");
  t = t.replace(/gold-api\\.com/ig, "");
  t = t.replace(/\\bproxy\\b/ig, "");
  if (!keepMin) {
    t = t.replace(/\\bdelayed\\s+\\d+\\s*m\\b/ig, "delayed");
    t = t.replace(/\\s*·\\s*\\d+\\s*m\\b/ig, "");
    t = t.replace(/\\b\\d+\\s*m\\b/ig, "");
    t = t.replace(/\\bas of\\s+ago\\b/ig, "");
  }''',
    '''  t = t.replace(/\\bcached\\b/ig, "");
  t = t.replace(/\\bxau\\s+spot\\s+proxy\\b/ig, "Spot gold");
  t = t.replace(/\\bspot\\s+proxy\\b/ig, "");
  t = t.replace(/gold-api\\.com/ig, "");
  t = t.replace(/\\bfree gold feed\\b/ig, "Spot gold");
  t = t.replace(/\\bproxy\\b/ig, "");
  t = t.replace(/\\bdelayed\\s+(\\d+)\\s*m\\b/ig, "delayed $1 min");
  t = t.replace(/\\b(\\d+)\\s*m\\b(?=\\s+by\\b)/ig, "$1 min");
  if (!keepMin) {
    t = t.replace(/\\bas of\\s+ago\\b/ig, "");
  }''', 'scrub cached')

s = subn(s, '  if (d.status === "cached") return "CACHED";',
    '  if (d.status === "cached") return fe68_words(d.fe64Note || d.label || "as of");',
    'feed label cached')

s = subn(s, '  if(s==="cached")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">CACHED</span>`;',
    '  if(s==="cached")return `<span class="bd trust-stat trust-stat-cached" title="${title}" style="background:var(--puG);color:var(--pu);font-size:7.5px">${_escHtml(d.label||d.fe64Note||"as of")}</span>`;',
    'status pill cached')

s = subn(s, '  if (tk === "XAU") return /gold-api|spot/i.test(src) ? "Spot gold" : "COMEX";',
    '  if (tk === "SLV") return "SLV · silver ETF";\n  if (tk === "XAU") return /gold-api|spot/i.test(src) ? "Spot gold" : "COMEX";',
    'silver etf name')

s = subn(s, 'const RT38_GOLD = /^(XAU|GC=F|GLD|GOLD|SLV|XAG)$/i;',
    'const RT38_GOLD = /^(XAU|GC=F|GLD|GOLD)$/i;',
    'silver is not gold')

s = subn(s, '  return "Fit score covers US-listed stocks for now.";',
    '  return "Regime fit is not published for this name.";',
    'regime empty state')

s = subn(s, '  const H = { LSE: ["Europe/London", 480, 990], XETRA: ["Europe/Berlin", 540, 1050], EURONEXT: ["Europe/Paris", 540, 1050], TSE: ["Asia/Tokyo", 540, 930, 690, 750], HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780], KRX: ["Asia/Seoul", 540, 930] };',
    '  const H = { LSE: ["Europe/London", 480, 990], XETRA: ["Europe/Berlin", 540, 1050], EURONEXT: ["Europe/Paris", 540, 1050], TSE: ["Asia/Tokyo", 540, 930, 690, 750], HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780], SSE: ["Asia/Shanghai", 570, 900, 690, 780], SZSE: ["Asia/Shanghai", 570, 900, 690, 780], KRX: ["Asia/Seoul", 540, 930] };',
    'sse szse calendar')

s = subn(s, 'setTimeout(() => { try { if (_lookupSeq === seq0 && _dynLoading) { _lookupSeq++; _dynLoading = false; _dynData = null; if (IS_DESKTOP()) renderP2(); else renderMain(); } } catch (e) {} }, 9000);',
    'setTimeout(() => { try { if (_lookupSeq === seq0 && _dynLoading) { if (typeof fe68_lookupHold === "function" && fe68_lookupHold(tk)) return; _lookupSeq++; _dynLoading = false; _dynData = null; if (IS_DESKTOP()) renderP2(); else renderMain(); } } catch (e) {} }, (typeof fe68_lookupWait === "function" ? fe68_lookupWait(tk) : 9000));',
    'lookup watchdog')

s = subn(s, '  const yhSym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])?YAHOO_SYMBOLS[sym]:sym;',
    '  const yhSym=(typeof YAHOO_SYMBOLS!=="undefined"&&YAHOO_SYMBOLS[sym])?YAHOO_SYMBOLS[sym]:sym;\n  let fe68Ready=null;\n  if(typeof fe68_suffixed==="function"&&fe68_suffixed(sym)){try{fe68Ready=await fe68_yahooQuote(yhSym);}catch(e){fe68Ready=null;}fe68_pending=fe68Ready;}',
    'quote first')

s = subn(s, '    let priceInfo=priceJson[yhSym]||priceJson[sym]||null;',
    '    let priceInfo=priceJson[yhSym]||priceJson[sym]||null;\n    if((!priceInfo||!(typeof priceInfo.p==="number"&&priceInfo.p>0))&&fe68Ready&&typeof fe68Ready.p==="number"&&fe68Ready.p>0)priceInfo=fe68Ready;',
    'use quote first')

s = subn(s, '>"${shown}" — no price data found.</div>',
    '>We couldn\'t load a price for ${shown} just now. Try again in a minute.</div>',
    'desktop not found')

s = subn(s, 'Dynamic ticker lookup: you typed a symbol that is not in the curated list, and Yahoo returned no quote for it (wrong symbol, bad suffix, or feed gap).',
    'The price feed did not answer for this symbol. Wait a minute and try the same symbol again.',
    'yahoo no quote copy')

s = subn(s, '(_dynLoading?\'FETCHING…\':\'NOT FOUND\')',
    '(_dynLoading?\'FETCHING…\':\'TRY AGAIN\')',
    'not found subtitle')

s = subn(s, '>"${_dynTk}" — no price data found</div>',
    '>We couldn\'t load a price for ${_dynTk} just now. Try again in a minute.</div>',
    'mobile not found')

s = subn(s, '''  if (typeof LightweightCharts === 'undefined') {
    _renderTradingViewFallback(tk, range, container);
    return;
  }''',
    '''  if (typeof LightweightCharts === 'undefined') {
    if (typeof fe68_chartSvg === "function" && await fe68_chartSvg(tk, range, container)) return;
    _renderTradingViewFallback(tk, range, container);
    return;
  }''', 'chart without library')

s = subn(s, '''  } catch (e) {
    if (_chartLoad.tk !== tk || _chartLoad.cid !== containerId) return;
    _renderTradingViewFallback(tk, range, container);
  }
}''',
    '''  } catch (e) {
    if (_chartLoad.tk !== tk || _chartLoad.cid !== containerId) return;
    if (typeof fe68_chartSvg === "function" && await fe68_chartSvg(tk, range, container)) return;
    _renderTradingViewFallback(tk, range, container);
  }
}''', 'chart catch')

s = subn(s, '/\\.(HK|L|T|DE|PA|KS|AX|NS|TO|SS|TW)$/i',
    '/\\.(HK|L|T|DE|PA|KS|AX|NS|TO|SS|SZ|TW)$/i',
    'szse non-us')

s = subn(s, '<button class="${aTab==="cm"?"on":""}" onclick="_setATab(\'cm\')">Lenses</button>',
    '<button class="${aTab==="cm"?"on":""}" onclick="_setATab(\'cm\')">Lenses</button>${typeof fe68_usStock==="function"&&fe68_usStock(a)?`<button class="${aTab==="ins"?"on":""}" onclick="_setATab(\'ins\')">Insiders</button>`:""}',
    'insiders tab', 2)

s = subn(s, '''    if(aTab==="inst"){
      h+=`<div id="term-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
      setTimeout(()=>loadHolders(termSelTk,'term-inst-root'),50);
    }''',
    '''    if(aTab==="inst"){
      h+=`<div id="term-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
      setTimeout(()=>loadHolders(termSelTk,'term-inst-root'),50);
    }
    if(aTab==="ins"){
      h+=`<div id="term-ins-root" class="fe68-ins"><div style="padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3)">Loading insider filings…</div></div>`;
      setTimeout(()=>fe68_loadInsiders(termSelTk,'term-ins-root'),40);
    }''', 'desktop insiders pane')

s = subn(s, '''  if(aTab==="inst"){
    h+=`<div id="anlz-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
    setTimeout(()=>loadHolders(a.tk,'anlz-inst-root'),50);
  }''',
    '''  if(aTab==="inst"){
    h+=`<div id="anlz-inst-root"><div style="padding:20px;text-align:center"><div style="width:14px;height:14px;border:2px solid var(--gd);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 10px"></div><div style="font-family:var(--mn);font-size:10px;color:var(--t3)">LOADING INSTITUTIONAL DATA…</div></div></div>`;
    setTimeout(()=>loadHolders(a.tk,'anlz-inst-root'),50);
  }
  if(aTab==="ins"){
    h+=`<div id="anlz-ins-root" class="fe68-ins"><div style="padding:16px;font-family:var(--mn);font-size:10px;color:var(--t3)">Loading insider filings…</div></div>`;
    setTimeout(()=>fe68_loadInsiders(a.tk,'anlz-ins-root'),40);
  }''', 'mobile insiders pane')

s = subn(s, '  h+=`</svg></div>`;\n\n  h += _renderSiteIntelCard("ticker", { tk: a.tk });',
    '  h+=`</svg></div>`;\n  try { h += fe68_hlHtml(a.tk); } catch (e) {}\n\n  h += _renderSiteIntelCard("ticker", { tk: a.tk });',
    'mobile high low')

s = subn(s, 'body.fe65-guest .cmd-bar,body.fe65-guest .sidebar{display:flex!important;visibility:visible!important;position:relative;z-index:80}',
    'body.fe65-guest .cmd-bar{display:flex!important;visibility:visible!important;position:relative;z-index:80}body.fe65-guest .sidebar{display:flex!important;visibility:visible!important;position:sticky;top:0;z-index:80;height:calc(100vh - var(--desk-chrome,92px));max-height:calc(100vh - var(--desk-chrome,92px));overflow-y:auto}',
    'sidebar sticky')

BLOCK = r'''
// ── rt57 ──
// fe68-pure-begin
function fe68_chip(tag) {
  try { if (typeof fe64_chip === "function") return fe64_chip(tag); } catch (e) {}
  var k = String(tag == null ? "" : tag).trim().toLowerCase();
  if (k === "stock" || k === "stocks" || k === "earnings" || k === "etf") return "Stocks";
  if (k === "commodity" || k === "commodities") return "Commodities";
  if (k === "fx" || k === "forex" || k === "currency") return "Forex";
  if (k === "crypto" || k === "cryptocurrency") return "Crypto";
  if (k === "macro" || k === "central bank") return "Macro";
  if (k === "geopolitics" || k === "geopolitical") return "Geopolitics";
  return "Other";
}
function fe68_at(low, words) {
  var best = -1, i, k, re, m;
  for (i = 0; i < words.length; i++) {
    k = String(words[i] || "").toLowerCase();
    if (!k) continue;
    re = new RegExp("(^|[^a-z0-9])" + k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^a-z0-9])", "i");
    m = re.exec(low);
    if (m && (best < 0 || m.index < best)) best = m.index;
  }
  return best;
}
function fe68_storyTag(text, low, hit, feedCat) {
  var raw = " " + String(text == null ? "" : text).toLowerCase().replace(/\s+/g, " ") + " ";
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
    if (/\bmarkets?\b/.test(raw) && feedCat) {
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
}
function fe68_ms(v) {
  if (v == null || v === "") return 0;
  var n = typeof v === "number" ? v : Date.parse(v);
  if (typeof v === "string" && /^\d{11,}$/.test(v)) n = Number(v);
  if (!isFinite(n) || n <= 0) return 0;
  if (n < 1e10) n *= 1000;
  return n;
}
function fe68_uk(ms) {
  if (!(ms > 0)) return "";
  try {
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    if (/^\d:\d{2}$/.test(h + ":" + mi)) h = "0" + h;
    return h && mi ? h + ":" + mi : "";
  } catch (e) { return ""; }
}
function fe68_threshold(src) {
  var s = String(src || "");
  if (s.indexOf("gold-api") >= 0) return 10 * 60 * 1000;
  if (s === "coingecko" || s === "coinbase-ws" || s === "kraken-ws") return 10 * 60 * 1000;
  if (s === "twelve-data") return 15 * 60 * 1000;
  if (s === "yahoo" || s === "yahoo-stream") return 30 * 60 * 1000;
  if (s === "frankfurter-ecb" || s === "open-exchange-rate-api") return 36 * 60 * 60 * 1000;
  return 15 * 60 * 1000;
}
function fe68_words(s) {
  var t = String(s == null ? "" : s);
  t = t.replace(/\bfree gold feed\b/ig, "Spot gold");
  t = t.replace(/\bgold\s*·\s*free market feed\b/ig, "Spot gold");
  t = t.replace(/\bfree market feed\b/ig, "");
  t = t.replace(/\bfree feed\b/ig, "");
  t = t.replace(/\bCACHED\b/ig, "");
  t = t.replace(/\bcached\b/ig, "");
  t = t.replace(/\bLIVE·(?:CB|YS|KR)\b/g, "LIVE");
  t = t.replace(/\bdelayed\s+(\d+)\s*m\b/ig, "delayed $1 min");
  t = t.replace(/\b(\d+)\s*m\b(?=\s+by\b)/ig, "$1 min");
  return t.replace(/\s{2,}/g, " ").replace(/^[\s·\-]+|[\s·\-]+$/g, "").trim();
}
function fe68_badge(m, tk, now) {
  var o = Object.assign({}, m || {});
  var src = String(o.src || "");
  var when = typeof now === "number" ? now : Date.now();
  var asOf = fe68_ms(o.asOf);
  var age = asOf ? when - asOf : null;
  var limit = fe68_threshold(src);
  var fresh = age != null && age >= -60000 && age < limit;
  var gold = src.indexOf("gold-api") >= 0;
  if (gold && tk === "XAU" && o.checkedAge != null && o.checkedAge >= 0 && o.checkedAge < 3 * 60 * 1000) fresh = true;
  var cached = o.status === "cached" || o.status === "proxy" || o.cached === true || /last-good|session-cache|free feed|free gold|CACHED/i.test(src + " " + String(o.label || ""));
  if (/^LIVE·/.test(String(o.label || "")) || (o.status === "live" && /coinbase-ws|kraken-ws|yahoo-stream/.test(src))) {
    var who = src === "coinbase-ws" ? "Coinbase" : src === "kraken-ws" ? "Kraken" : src === "yahoo-stream" ? "Yahoo" : "";
    o.status = "live";
    o.label = "LIVE";
    if (who) o.title = who;
    if (who && String(o.detail || "").indexOf(who) < 0) o.detail = (o.detail ? String(o.detail) + " · " : "") + who;
  }
  if (gold && o.status !== "closed" && o.status !== "lunch" && (fresh || (age != null && age < 10 * 60 * 1000))) {
    o.status = "live";
    o.label = "LIVE";
    if (tk === "XAU") { o.detail = "Spot gold"; o.fe64Note = "Spot gold"; }
    cached = false;
  } else if (gold && (o.status === "stale" || /STALE/i.test(String(o.label || "")))) {
    var ghm = fe68_uk(asOf);
    if (age != null && age < 30 * 60 * 1000) {
      o.status = "cached";
      o.label = ghm ? ("as of " + ghm + " UK") : "as of";
    } else {
      o.status = "delayed";
      o.label = "delayed";
    }
    o.fe64Note = o.label;
    if (tk === "XAU") o.detail = "Spot gold";
    else if (/gold|free/i.test(String(o.detail || ""))) o.detail = o.label;
    cached = false;
  }
  if (cached && o.status !== "closed" && o.status !== "lunch" && o.status !== "live") {
    if (age != null && age > limit) {
      o.status = "delayed";
      o.label = "delayed";
      o.fe64Note = "delayed";
      o.detail = "delayed";
    } else {
      var hm = fe68_uk(asOf);
      var words = hm ? ("as of " + hm + " UK") : "as of";
      o.status = "cached";
      o.label = words;
      o.fe64Note = words;
      o.detail = words;
    }
  } else if (o.status === "stale" && cached) {
    o.status = fresh ? "cached" : "delayed";
    o.label = fresh ? (fe68_uk(asOf) ? ("as of " + fe68_uk(asOf) + " UK") : "as of") : "delayed";
    o.fe64Note = o.label;
    o.detail = o.label;
  }
  o.label = fe68_words(o.label);
  o.detail = fe68_words(o.detail);
  o.fe64Note = fe68_words(o.fe64Note);
  if (gold && tk && tk !== "XAU") {
    if (/gold|free feed|free gold|free market/i.test(String(o.detail || ""))) o.detail = "Spot metal";
  }
  if (tk === "SLV") {
    o.detail = "SLV · silver ETF";
    if (!o.label || /gold|spot gold|free/i.test(o.label)) o.label = o.status === "live" ? "LIVE" : "SLV · silver ETF";
    if (/gold/i.test(o.fe64Note || "")) o.fe64Note = "SLV · silver ETF";
  }
  if (tk === "XAU") {
    if (!o.detail || /free|gold feed/i.test(o.detail)) o.detail = "Spot gold";
    if (/free|CACHED|cached/i.test(o.label || "")) o.label = fresh ? "LIVE" : "Spot gold";
  }
  if (/cached/i.test(String(o.label || ""))) o.label = o.fe64Note && !/cached/i.test(o.fe64Note) ? o.fe64Note : "as of";
  return o;
}
function fe68_suffixed(sym) {
  return /\.(L|T|HK|AX|KS|NS|PA|DE|TO|SS|SZ|TW|SI|VX|SW|OL|CO|HE|AS|BR|MX)$/i.test(String(sym || ""));
}
// fe68-pure-end
var fe68_pending = null;
var fe68_day = Object.create(null);
var fe68_insUi = Object.create(null);
function fe68_lookupWait(tk) { return fe68_suffixed(tk) ? 25000 : 9000; }
function fe68_lookupHold(tk) { return !!(fe68_pending && fe68_pending.p > 0 && fe68_suffixed(tk)); }
async function fe68_yahooQuote(sym) {
  var i, r, j, q;
  for (i = 0; i < 2; i++) {
    try {
      r = await fetch("/api/yahoo-quote?symbols=" + encodeURIComponent(sym), { signal: AbortSignal.timeout(8000) });
      if (!r.ok) continue;
      j = await r.json();
      q = j && (j[sym] || j[String(sym || "").toUpperCase()]);
      if (q && typeof q.p === "number" && q.p > 0) return q;
    } catch (e) {}
  }
  return null;
}
function fe68_older(tk, q) {
  try {
    var srcIn = String((q && (q.source || q.src)) || "");
    var staleIn = !!(q && (q.stale === true || q.cached === true || /last-good|session-cache/.test(srcIn)));
    var cur = "";
    try { cur = String((liveQuoteSrc && liveQuoteSrc[tk]) || ""); } catch (e0) { cur = ""; }
    if (staleIn && /coinbase-ws|kraken-ws|yahoo-stream|gold-api/.test(cur)) {
      var recv = 0;
      try { recv = _rt && _rt.lastRecv ? Number(_rt.lastRecv[tk]) : 0; } catch (e1) { recv = 0; }
      if (recv && Date.now() - recv < 120000) return true;
    }
    var next = fe68_ms(q && (q.ts || q.fetchedAt));
    var have = fe68_ms(liveQuoteTs && liveQuoteTs[tk]);
    if (!(next > 0) || !(have > 0)) return false;
    return next + 1500 < have;
  } catch (e) { return false; }
}
function fe68_dayHl(tk) { return fe68_day[tk] || null; }
function fe68_hlHtml(tk) {
  try { if (typeof fe66_nonUs !== "function" || !fe66_nonUs(tk)) return ""; } catch (e) { return ""; }
  var hl = fe68_day[tk] || {};
  var h = Number(hl.h), l = Number(hl.l);
  if (!(h > 0) || !(l > 0)) {
    var s = [];
    try { s = (HIST[tk] || []).filter(function (v) { return typeof v === "number" && isFinite(v) && v > 0; }); } catch (e2) { s = []; }
    if (s.length >= 2) { h = Math.max.apply(null, s); l = Math.min.apply(null, s); }
  }
  if (!(h > 0) || !(l > 0)) return "";
  var money = function (n) { try { return fe66_money(tk, n); } catch (e3) { return String(n); } };
  return '<div class="fe68-hl"><span>High ' + money(h) + '</span><span>Low ' + money(l) + '</span></div>';
}
function fe68_usStock(a) {
  if (!a || a.cat !== "Stock") return false;
  if (a._rt43) return false;
  if (/\./.test(String(a.tk || ""))) return false;
  return /^(NYSE|NASDAQ|AMEX|NYSEARCA|ARCA)$/.test(String(a.ex || ""));
}
function fe68_bookFive() {
  var out = [], raw = [];
  try {
    getActiveWl().tickers.forEach(function (tk) {
      if (!tk) return;
      var u = String(tk).toUpperCase();
      raw.push(u);
      if (out.length >= 5) return;
      var a = null;
      try { a = (typeof A !== "undefined" ? A : []).find(function (x) { return x && String(x.tk).toUpperCase() === u; }); } catch (e2) { a = null; }
      if (a && (a.cat === "Crypto" || a.cat === "FX" || a.cat === "Commodity" || a._rt43)) return;
      if (/\./.test(u) || !/^[A-Z]{1,5}$/.test(u)) return;
      out.push(u);
    });
  } catch (e) {}
  return out.length ? out : raw.slice(0, 5);
}
function fe68_esc(v) { try { return _escHtml(v == null ? "" : String(v)); } catch (e) { return String(v == null ? "" : v); } }
function fe68_insRow(row) {
  var link = row.filingUrl ? ' <a href="' + fe68_esc(row.filingUrl) + '" target="_blank" rel="noopener noreferrer">Filing</a>' : "";
  return '<div class="institutional-row"><strong>' + fe68_esc(row.insiderName || "Insider") + '</strong><span>' + fe68_esc(row.insiderRole || "") + '</span><span>' + fe68_esc(row.codeLabel || row.transactionCode || "") + (row.shares != null ? " · " + fe68_esc(row.shares) + " shares" : "") + (row.value ? " · " + fe68_esc(row.value) : "") + '</span><small>' + fe68_esc(row.transactionDate || row.filingDate || "") + link + '</small></div>';
}
function fe68_insHtml(tk, data, err) {
  var ui = fe68_insUi[tk] || (fe68_insUi[tk] = { all: false, house: false });
  var premium = false;
  try { premium = typeof _isPremium === "function" && _isPremium(); } catch (e) {}
  var h = '<div class="fe68-ins">';
  if (err === "unknown") return h + '<p class="ex">Unknown ticker.</p></div>';
  if (err) return h + '<p class="ex">' + fe68_esc(err) + '</p></div>';
  if (!data) return h + '<p class="ex">Loading insider filings…</p></div>';
  if (data.unavailable) return h + '<p class="ex">' + fe68_esc(data.message || "Insider filings unavailable right now") + '</p></div>';
  var ex = data.explainer || {};
  if (ex.what) h += '<p class="ex"><strong>What.</strong> ' + fe68_esc(ex.what) + '</p>';
  if (ex.where) h += '<p class="ex"><strong>Where.</strong> ' + fe68_esc(ex.where) + '</p>';
  if (ex.why) h += '<p class="ex"><strong>Why.</strong> ' + fe68_esc(ex.why) + '</p>';
  if (data.stale) h += '<p class="ex">Last saved copy' + (data.asOf ? " · " + fe68_esc(data.asOf) : "") + '.</p>';
  if (premium) {
    h += '<div class="fe68-hl"><button type="button" class="hdr-act-btn" onclick="fe68_insUi[\'' + tk + '\'].all=' + (ui.all ? 'false' : 'true') + ';fe68_loadInsiders(\'' + tk + '\')"> ' + (ui.all ? 'Open-market only' : 'Awards and exercises') + '</button>';
    h += '<button type="button" class="hdr-act-btn" onclick="fe68_insUi[\'' + tk + '\'].house=' + (ui.house ? 'false' : 'true') + ';fe68_loadInsiders(\'' + tk + '\')"> ' + (ui.house ? 'Hide House' : 'House filings') + '</button></div>';
  }
  var rows = Array.isArray(data.insider) ? data.insider : [];
  if (!rows.length) h += '<p class="ex">' + fe68_esc(data.note || "No Form 4 filings for this ticker.") + '</p>';
  else {
    h += rows.map(fe68_insRow).join("");
    if (data.meta && data.meta.limited) h += '<div class="institutional-row"><strong>See full history with Premium</strong><span>Five open-market rows are shown here.</span></div>';
  }
  if (premium && data.house && Array.isArray(data.house.items)) {
    h += '<p class="ex"><strong>House.</strong> ' + fe68_esc((data.house.note || "Periodic Transaction Reports")) + '</p>';
    data.house.items.forEach(function (item) {
      h += '<div class="institutional-row"><strong>' + fe68_esc(item.member || "Member") + '</strong><span>' + fe68_esc(item.filingDate || "") + '</span><span>' + fe68_esc(item.note || "See filing") + '</span>' + (item.pdfUrl ? '<a href="' + fe68_esc(item.pdfUrl) + '" target="_blank" rel="noopener noreferrer">Filing</a>' : '') + '</div>';
    });
  }
  return h + '</div>';
}
async function fe68_loadInsiders(tk, rootId) {
  var root = rootId ? document.getElementById(rootId) : null;
  if (!root) {
    var panes = document.querySelectorAll("#term-ins-root, #anlz-ins-root");
    for (var i = 0; i < panes.length; i++) { if (panes[i].getClientRects().length) root = panes[i]; }
    if (!root && panes.length) root = panes[panes.length - 1];
  }
  if (!tk) return;
  var ui = fe68_insUi[tk] || (fe68_insUi[tk] = { all: false, house: false });
  var premium = false;
  try { premium = typeof _isPremium === "function" && _isPremium(); } catch (e) {}
  var q = "/api/insiders?t=" + encodeURIComponent(tk);
  if (premium && ui.all) q += "&codes=all";
  if (premium && ui.house) q += "&house=1";
  try {
    var res = await fetch(q, { credentials: "include", signal: AbortSignal.timeout(12000) });
    var data = await res.json().catch(function () { return {}; });
    var html = res.status === 404 ? fe68_insHtml(tk, null, "unknown") : fe68_insHtml(tk, data, data && data.unavailable ? (data.message || "Insider filings unavailable right now") : "");
    if (root) root.innerHTML = html;
  } catch (e) {
    if (root) root.innerHTML = fe68_insHtml(tk, null, "Insider filings unavailable right now");
  }
}
async function fe68_newsInsiders(force) {
  if (_institutionalLoading.insider || (!force && _institutionalData.insider)) return;
  _institutionalLoading.insider = true;
  _institutionalError.insider = "";
  try { _refreshNewsView(); } catch (e) {}
  var tks = fe68_bookFive();
  var items = [], notes = [], explainer = null, asOf = "", failed = 0;
  await Promise.all(tks.map(async function (tk) {
    try {
      var res = await fetch("/api/insiders?t=" + encodeURIComponent(tk), { credentials: "include", signal: AbortSignal.timeout(12000) });
      var data = await res.json().catch(function () { return {}; });
      if (res.status === 404) { notes.push(tk + ": " + (data.error || "Unknown ticker.")); return; }
      if (data.unavailable) { failed++; notes.push(tk + ": " + (data.message || "Insider filings unavailable right now")); return; }
      if (data.explainer) explainer = data.explainer;
      if (data.asOf) asOf = data.asOf;
      if (!data.insider || !data.insider.length) { if (data.note) notes.push(tk + ": " + data.note); return; }
      data.insider.forEach(function (row) {
        items.push({ ticker: tk, insider: row.insiderName, role: row.insiderRole, transactionType: row.codeLabel || row.transactionCode, shares: row.shares, value: row.value, date: row.transactionDate || row.filingDate, sourceUrl: row.filingUrl });
      });
    } catch (e2) { failed++; }
  }));
  _institutionalData.insider = { items: items, source: "SEC EDGAR", asOf: asOf, explainer: explainer, note: notes.filter(Boolean).join(" · "), status: !items.length && failed === tks.length ? "unavailable" : "" };
  _institutionalLoading.insider = false;
  try { _refreshNewsView(); } catch (e3) {}
}
async function fe68_chartSvg(tk, range, container) {
  if (!container) return false;
  var symbols = [];
  try { symbols = _chartSymbolCandidates(tk); } catch (e) { symbols = [tk]; }
  var urls = [];
  symbols.forEach(function (sym) {
    urls.push("/api/yahoo-chart?symbol=" + encodeURIComponent(sym) + "&range=6mo&interval=1d");
    urls.push("/api/yahoo-chart?symbol=" + encodeURIComponent(sym) + "&range=" + encodeURIComponent(range || "1d") + "&interval=5m");
  });
  var bars = [];
  for (var i = 0; i < urls.length && bars.length < 3; i++) {
    try {
      var res = await chartFetch(urls[i], { signal: AbortSignal.timeout(12000) });
      if (!res.ok) continue;
      var data = await res.json();
      var result = data && data.chart && data.chart.result && data.chart.result[0];
      var parsed = _candlesFromYahooResult(result);
      if (parsed && parsed.candles && parsed.candles.length >= 3) bars = parsed.candles;
    } catch (e2) {}
  }
  if (bars.length < 3) return false;
  var closes = bars.map(function (b) { return b.close; });
  var hi = Math.max.apply(null, bars.map(function (b) { return b.high; }));
  var lo = Math.min.apply(null, bars.map(function (b) { return b.low; }));
  var mn = Math.min.apply(null, closes), mx = Math.max.apply(null, closes), rng = (mx - mn) || 1;
  var pts = closes.map(function (v, n) { return ((n / (closes.length - 1)) * 300) + "," + (50 - ((v - mn) / rng) * 44); }).join(" ");
  var money = function (n) { try { return fe66_money(tk, n); } catch (e3) { return String(n); } };
  container.innerHTML = '<div class="fe68-svgchart"><svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block"><polyline points="' + pts + '" fill="none" stroke="var(--bl)" stroke-width="1.5"/></svg><div class="fe68-hl"><span>High ' + money(hi) + '</span><span>Low ' + money(lo) + '</span></div></div>';
  return true;
}
function fe68_css() {
  var st = document.createElement("style");
  st.setAttribute("data-fe68", "chat");
  st.textContent = "@media(min-width:768px){body .sidebar,body.fe65-guest .sidebar{position:sticky!important;top:0!important;align-self:flex-start!important;height:100vh!important;max-height:100vh!important;overflow-y:auto!important;z-index:80}body.fe68-lenses .sidebar,body.fe65-guest.fe68-lenses .sidebar{position:fixed!important;top:0!important;left:0!important;width:var(--sidebar-w,172px)!important;height:100vh!important;max-height:100vh!important;z-index:90!important}body.fe68-lenses .terminal-wrap{padding-left:var(--sidebar-w,172px)}} .fe68-hl{display:flex;gap:14px;flex-wrap:wrap;font-family:var(--mn);font-size:11px;color:var(--t2);padding:6px 0} .fe68-ins{padding:12px 14px} .fe68-ins .ex{font-size:12px;line-height:1.45;color:var(--t2);margin:4px 0}";
  document.head.appendChild(st);
}
try { fe68_css(); } catch (e) {}
try {
  var fe68_qm = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe68_qm.apply(this, arguments);
    try {
      var src = "";
      try { src = (liveQuoteSrc && liveQuoteSrc[tk]) || (m && m.src) || ""; } catch (e2) { src = (m && m.src) || ""; }
      var asOf = m && m.asOf;
      var cached = false;
      try { cached = !!(liveQuoteCached && liveQuoteCached[tk]) || /last-good|session-cache/.test(src); } catch (e3) {}
      var extra = { src: src, asOf: asOf, cached: cached };
      try { if (tk === "XAU" && _rt && _rt.goldChecked) extra.checkedAge = Date.now() - _rt.goldChecked; } catch (e5) {}
      m = fe68_badge(Object.assign({}, m, extra), tk);
    } catch (e4) {}
    return m;
  };
} catch (e) {}
try {
  var fe68_aq = _applyLiveQuote;
  _applyLiveQuote = function (tk, q, source) {
    if (fe68_older(tk, q)) {
      try {
        var curS = String((liveQuoteSrc && liveQuoteSrc[tk]) || "");
        if (/coinbase-ws|kraken-ws|yahoo-stream|gold-api/.test(curS)) delete _rt43Stale[tk];
      } catch (e0) {}
      return true;
    }
    var r = fe68_aq.apply(this, arguments);
    try {
      if (q) {
        var hi = Number(q.high != null ? q.high : (q.dayHigh != null ? q.dayHigh : q.regularMarketDayHigh));
        var lo = Number(q.low != null ? q.low : (q.dayLow != null ? q.dayLow : q.regularMarketDayLow));
        if (hi > 0 && lo > 0) fe68_day[tk] = { h: hi, l: lo };
      }
      var src = String((q && q.source) || source || "");
      if (q && (q.stale === true || /last-good/.test(src))) {
        var ts = fe68_ms(q.ts) || Date.now();
        if (Date.now() - ts < fe68_threshold(src)) { try { delete _rt43Stale[tk]; } catch (e2) {} }
      }
    } catch (e3) {}
    return r;
  };
} catch (e) {}
try {
  var fe68_tw = fe65_tapeWords;
  fe65_tapeWords = function (d) {
    var w = "";
    try { w = fe68_tw.apply(this, arguments); } catch (e) { w = ""; }
    w = fe68_words(w);
    if (!w && d) w = fe68_words(d.fe64Note || d.label || "");
    if (/cached/i.test(w)) w = fe68_words((d && (d.fe64Note || d.label)) || "as of");
    return w;
  };
} catch (e) {}
try {
  var fe68_sl = _quoteSourceLabel;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe68_sl.apply(this, arguments); } catch (e) { out = String(src || ""); }
    var s = String(src || "");
    if (/gold-api-spot-metal/i.test(s)) return "Spot metal";
    if (/gold-api/i.test(s)) return "Spot gold";
    out = fe68_words(out);
    if (/free gold feed|free market feed/i.test(out)) return "Spot gold";
    return out;
  };
} catch (e) {}
try {
  var fe68_tab = _setATab;
  _setATab = function (t) {
    var r = fe68_tab.apply(this, arguments);
    try { document.body.classList.toggle("fe68-lenses", t === "cm"); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe68_li = _loadInstitutional;
  _loadInstitutional = function (type, force) {
    if (type === "insider") return fe68_newsInsiders(force);
    return fe68_li.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe68_ri = _renderInstitutionalIntelligence;
  _renderInstitutionalIntelligence = function () {
    var h = String(fe68_ri.apply(this, arguments) || "");
    try {
      var d = _institutionalData && _institutionalData.insider;
      if (_institutionalTab === "insider" && d && d.explainer) {
        var ex = d.explainer;
        var block = '<div class="fe68-ins"><p class="ex"><strong>What.</strong> ' + fe68_esc(ex.what || "") + '</p><p class="ex"><strong>Where.</strong> ' + fe68_esc(ex.where || "") + '</p><p class="ex"><strong>Why.</strong> ' + fe68_esc(ex.why || "") + '</p></div>';
        if (h.indexOf("institutional-list") >= 0) h = h.replace('<div class="institutional-list">', block + '<div class="institutional-list">');
        else h = block + h;
      }
    } catch (e2) {}
    return h;
  };
} catch (e) {}
try {
  var fe68_cc = renderCandleChart;
  renderCandleChart = async function (tk, range, containerId) {
    try {
      var r = await fe68_cc.apply(this, arguments);
      return r;
    } catch (e) {
      var container = document.getElementById(containerId);
      if (container && await fe68_chartSvg(tk, range, container)) return;
      throw e;
    }
  };
} catch (e) {}
try { if (_rt53DtCache && _rt53DtCache.clear) _rt53DtCache.clear(); } catch (e) {}
try { (typeof NEWS !== "undefined" ? NEWS : []).forEach(function (n) { if (n) delete n._rt52; }); if (typeof _rt52Retag === "function") _rt52Retag(); } catch (e) {}
'''

s = s + BLOCK
if "fe68_storyTag" not in s: die('helper missing')
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
