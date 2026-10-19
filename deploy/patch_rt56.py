#!/usr/bin/env python3
"""patch_rt56.py: client patch on chat66. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat66, the output of patch_rt55b.py on chat65:
  app.js md5 ab9438b2e11e98c2e8e1113a7af6a013
  index.html md5 57a12c2078e8822f7f868097d4ea643d
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

A closed quote whose basis is previous_close is a last close, including a
zero change. The ticker page shows that price in the quote currency, the
words Last close, and the server note unchanged. A holiday the weekday
calendar does not know still reads Last session and the real last trading
day. Regime fit and the desk AI score are labelled as different figures.

No server file is changed.

Usage: python3 patch_rt56.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "ab9438b2e11e98c2e8e1113a7af6a013"
EXPECT_INDEX_MD5 = "57a12c2078e8822f7f868097d4ea643d"
NEED_MARKER = "// ── rt55b ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt56 ──' in s: already('rt56 already applied')
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

# The yahoo chunk accepts a keyed row or a flat quote object.
s = sub1(s,
    '      const q = data && (data[yhSym] || data[tk]);\n      if (q && q.p > 0 && _applyLiveQuote(tk, q, "yahoo")) hits++;',
    '      const q = fe66_pick(data, yhSym, tk);\n      if (q && q.p > 0 && _applyLiveQuote(tk, q, "yahoo")) hits++;',
    'yahoo chunk pick')

# Desktop headline. A closed previous close is a price, not NO SYNC.
s = sub1(s,
    "    const feedLbl = fe65_feedLbl(d, a.tk);",
    "    const feedLbl = fe66_feedLbl(d, a.tk);",
    'desktop feed label')
s = sub1(s,
'''           <div class="ap-price" style="color:${na?'var(--t3)':col}">${na?'NO LIVE SYNC':(money?'$':'')+d.p}</div>
          <div class="ap-chg" style="color:${col}">${na?'awaiting feed':`${arrow} ${sign}${d.chg} (${sign}${d.c}%) ${_rt26Day(a.tk)}`}</div>''',
'''           <div class="ap-price" style="color:${na?'var(--t3)':col}">${fe66_priceLine(a.tk, d, na)}</div>
          <div class="ap-chg" style="color:${col}">${fe66_chgLine(a.tk, d, na)}</div>''',
'desktop price line')
s = sub1(s,
    '>AI SCORE <span title="Score from 0–100 based on sentiment, momentum, fundamentals and analyst ratings"',
    '>AI score <span title="Desk score from 0–100. This is not the regime fit."',
    'ai score label')

# Live header refresh uses the same lines.
s = sub1(s,
    '  const feedLbl=fe65_feedLbl(d, a.tk);',
    '  const feedLbl=fe66_feedLbl(d, a.tk);',
    'patch feed label')
s = sub1(s,
    '    priceEl.textContent=na?_rt22NoSync():(money?"$":"")+d.p;',
    '    priceEl.textContent=fe66_priceLine(a.tk, d, na);',
    'patch price')
s = sub1(s,
    '    chgEl.textContent=na||chN==null?"awaiting feed":`${arrow} ${sign}${d.chg} (${sign}${d.c}%) ${_rt26Day(a.tk)}`;',
    '    chgEl.textContent=fe66_chgLine(a.tk, d, na);',
    'patch change')

# The pill painter must not put NO SYNC back.
s = sub1(s,
    'document.querySelectorAll(".rt43-feed").forEach(e => { const t = e.dataset.tk, d = fp(t); const lbl = fe65_feedLbl(d, t);',
    'document.querySelectorAll(".rt43-feed").forEach(e => { const t = e.dataset.tk, d = fp(t); const lbl = fe66_feedLbl(d, t);',
    'feed pill painter')

# Chart footer uses the quote currency. A closed venue names the last session.
s = sub1(s,
    '    const fmtPx = v => (isFinite(v) ? "$" + (v >= 1 ? v.toFixed(2) : v.toFixed(4)) : "—");',
    '    const fmtPx = v => (isFinite(v) ? fe66_money(tk, v) : "—");',
    'chart high low')
s = sub1(s,
    '${_rt24ChartHead(tk, usedRange)} · ${tk}${proxyNote} · ${quoteContext}',
    '${fe66_chartBit(tk, usedRange, quoteMeta, proxyNote, quoteContext)}',
    'chart session label')

# Compare price, alerts, dynamic lookup, mobile headline, valuation price, sticky bar.
s = sub1(s,
    '${na?_rt22NoSync():"$"+d.p}<div>${asOfTag(r.tk)}</div>',
    '${na?_rt22NoSync():fe66_show(r.tk, d)}<div>${asOfTag(r.tk)}</div>',
    'compare price')
s = sub1(s,
'''      const pxShow=curPrice!=null?`$${curPrice.toFixed(2)}`:"— NO SYNC";
      h += `<div style="padding:14px 16px">''',
'''      const pxShow=curPrice!=null?fe66_money(a.tk, curPrice):"—";
      h += `<div style="padding:14px 16px">''',
'desktop alert price')
s = sub1(s,
'''    const pxShow=curPrice!=null?`$${curPrice.toFixed(2)}`:"— NO SYNC";
    h+=`<div class="gc" style="padding:14px">''',
'''    const pxShow=curPrice!=null?fe66_money(a.tk, curPrice):"—";
    h+=`<div class="gc" style="padding:14px">''',
'mobile alert price')
s = sub1(s,
    '${livePrice == null ? _rt22NoSync() : "$" + Number(livePrice).toFixed(2)}',
    '${livePrice == null ? _rt22NoSync() : fe66_money(_dynTk, livePrice)}',
    'dynamic desktop price')
s = sub1(s,
    '''           <div class="ap-chg" style="color:${col}">${chN!=null?`${sign}${Number(d.chgAbs||0).toFixed(2)} (${sign}${chN.toFixed(2)}%)`:"awaiting feed"}</div>''',
    '''           <div class="ap-chg" style="color:${col}">${fe66_chgLine(_dynTk, {status:d.status}, livePrice==null)}</div>''',
    'dynamic desktop change')
s = sub1(s,
    '''       ? `<div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:5px">Context only: $${Number(d.price).toFixed(2)} · ${_quoteSourceLabel(d.source)} · as of ${_fmtAsOf(d.asOf)}</div>`''',
    '''       ? `<div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:5px">Context only: ${fe66_money(_dynTk, d.price)} · ${_quoteSourceLabel(d.source)} · as of ${_fmtAsOf(d.asOf)}</div>`''',
    'dynamic context price')
s = sub1(s,
    '''          <div style="font-family:var(--mn);font-size:11px;font-weight:600">$${d.prev.toFixed(2)}</div>''',
    '''          <div style="font-family:var(--mn);font-size:11px;font-weight:600">${fe66_money(_dynTk, d.prev)}</div>''',
    'dynamic prev close')
s = sub1(s,
    '''    if (subEl) subEl.textContent = _dynData ? (_dynData.exchange||'DYNAMIC LOOKUP') : (_dynLoading?'FETCHING…':'NOT FOUND');''',
    '''    if (subEl) subEl.textContent = _dynData ? (fe66_closedQuote(_dynTk, {status:_dynData.status}) ? (fe66_note(_dynTk) || "Last close") : (_dynData.exchange||'DYNAMIC LOOKUP')) : (_dynLoading?'FETCHING…':'NOT FOUND');''',
    'dynamic header')
s = sub1(s,
'''      h+=`<div style="padding:6px 8px;border-bottom:1px solid var(--b4)">
        <div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:3px">INTRADAY</div>
        <svg width="100%" viewBox="0 0 280 42" style="display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg>
      </div>`;''',
'''      h+=`<div style="padding:6px 8px;border-bottom:1px solid var(--b4)">
        <div style="font-family:var(--mn);font-size:7.5px;color:var(--t3);letter-spacing:0.15em;margin-bottom:3px">${fe66_dynHead(_dynTk)}</div>
        <svg width="100%" viewBox="0 0 280 42" style="display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg>
        <div style="font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:4px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>
      </div>`;''',
    'dynamic chart label')
s = sub1(s,
    '''    h+=`<div style="padding:6px 8px;border-top:1px solid var(--b4)"><button onclick="_dynClear()" style="background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:3px;padding:4px 12px;font-family:var(--mn);font-size:8.5px;cursor:pointer;letter-spacing:0.1em">← BACK</button></div>`;''',
    '''    h+=(typeof _rt53FitHtml==="function"?_rt53FitHtml(_dynTk):"");
    h+=`<div style="padding:6px 8px;border-top:1px solid var(--b4)"><button onclick="_dynClear()" style="background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:3px;padding:4px 12px;font-family:var(--mn);font-size:8.5px;cursor:pointer;letter-spacing:0.1em">← BACK</button></div>`;''',
    'dynamic regime fit')
s = sub1(s,
    "${pxN!=null?('$'+pxN.toFixed(2)):'NO LIVE SYNC'}",
    "${pxN!=null?fe66_money(_dynTk, pxN):'NO LIVE SYNC'}",
    'dynamic mobile price')
s = sub1(s,
    "${chN!=null?`${sign}${absN!=null?absN.toFixed(2):'—'} (${sign}${chN.toFixed(2)}%)`:'awaiting feed'}",
    "${fe66_chgLine(_dynTk, {status:d.status}, livePrice==null)}",
    'dynamic mobile change')
s = sub1(s,
    'Context only: $${Number(d.price).toFixed(2)}',
    'Context only: ${fe66_money(_dynTk, d.price)}',
    'dynamic mobile context')
s = sub1(s,
    '''h+=`<svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block;margin-bottom:10px"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg>`;''',
    '''h+=`<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.08em;margin-bottom:4px">${fe66_dynHead(_dynTk)}</div><svg viewBox="0 0 300 60" style="width:100%;height:60px;display:block"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/></svg><div style="font-family:var(--mn);font-size:10px;color:var(--t3);margin:4px 0 10px">High ${fe66_money(_dynTk, mx)} · Low ${fe66_money(_dynTk, mn)}</div>`;''',
    'dynamic mobile chart')
s = sub1(s,
    '''  h+=`<button onclick="_dynClear()" style="margin-top:12px;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:8px;padding:8px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">← Back</button></div>`;''',
    '''  h+=(typeof _rt53FitHtml==="function"?_rt53FitHtml(_dynTk):"");
  h+=`<button onclick="_dynClear()" style="margin-top:12px;background:var(--b2);color:var(--t2);border:1px solid var(--gb);border-radius:8px;padding:8px 16px;font-family:var(--sn);font-size:12px;cursor:pointer">← Back</button></div>`;''',
    'dynamic mobile regime')
s = sub1(s,
'''       _applyLiveQuote(markTk, Object.assign({
        p: priceInfo.p,
        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
        prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined,
      }, fe64_yqFields(priceInfo)), src==="coingecko"?"coingecko":"yahoo");''',
'''       _applyLiveQuote(markTk, Object.assign({}, priceInfo, {
        p: priceInfo.p,
        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,
        prev: typeof priceInfo.prev === "number" && priceInfo.prev > 0 ? priceInfo.prev : undefined,
      }, fe64_yqFields(priceInfo)), src==="coingecko"?"coingecko":"yahoo");''',
    'lookup keeps currency')
s = sub1(s,
    '''${hasSyncedQuote(a.tk)?((a.cat==="Stock"||a.cat==="Crypto"||a.cat==="Commodity")?"$":"")+d.p:_rt22NoSync()}''',
    '''${fe66_priceLine(a.tk, d, !hasSyncedQuote(a.tk))}''',
    'mobile price')
s = sub1(s,
    '''${!hasSyncedQuote(a.tk)?`<span style="font-size:10px;letter-spacing:0.08em">${d.label||"NO LIVE SYNC"}</span>`:(chAn==null?"—":`${chSign}${d.chg} (${chSign}${d.c}%)${_rt26Day(a.tk)==="today"?"":" "+_rt26Day(a.tk)}`)}''',
    '''${fe66_chgLine(a.tk, d, !hasSyncedQuote(a.tk))}''',
    'mobile change')
s = sub1(s,
    '${bd("Score: "+a.sc,scC(a.sc))}',
    '${bd("AI score "+a.sc,scC(a.sc))}',
    'mobile ai score')
s = sub1(s,
    '${v.price ? " · at $" + Number(v.price).toFixed(2) : ""}',
    '${v.price ? " · at " + fe66_money(tk, v.price) : ""}',
    'valuation price')
s = sub1(s,
    '${px ? "$" + Number(px).toLocaleString("en-US", { maximumFractionDigits: px < 10 ? 4 : 2 }) : ""}',
    '${px ? fe66_money(tk, px) : ""}',
    'sticky price')
s = sub1(s, '[/^AI SCORE\\b/, \'ai-score\']', '[/^AI score\\b/i, \'ai-score\']', 'ai score basis key')

# Regime fit is a different figure from the desk AI score.
s = sub1(s, '<span class="rt53-fit-k">REGIME FIT</span>', '<span class="rt53-fit-k">Regime fit</span>', 'regime kicker')
s = sub1(s,
    'if (f.state === "loading") return { k: "REGIME FIT", t:',
    'if (f.state === "loading") return { k: "Regime fit", t:',
    'regime sheet loading')
s = sub1(s,
    'if (f.state === "absent") return { k: "REGIME FIT", t:',
    'if (f.state === "absent") return { k: "Regime fit", t:',
    'regime sheet absent')
s = sub1(s,
    'return { k: "REGIME FIT", t: title',
    'return { k: "Regime fit", t: title',
    'regime sheet score')
s = sub1(s,
    ' : (f.ticker + " \\u00b7 " + (f.reason || "No fit score"));',
    ' : (f.ticker + " \\u00b7 " + fe66_fitSub(f.ticker || tk, f));',
    'regime sheet title')
s = sub1(s,
    'var what = f.state === "null" ? (f.reason || "No fit score was published for this name.") : ',
    'var what = f.state === "null" ? fe66_fitSub(f.ticker || tk, f) : ',
    'regime sheet body')
s = sub1(s,
    '      sub = f.reason || "No fit score for this name.";',
    '      sub = fe66_fitSub(tk, f);',
    'regime card empty')
s = sub1(s,
    '  if (f.state === "null") return _rt53Esc(f.reason || "No fit score for this name.");',
    '  if (f.state === "null") return _rt53Esc(fe66_fitSub(f.ticker, f));',
    'regime look line')
s = sub1(s,
    '  if (f.state === "null") return f.reason || "no fit score";',
    '  if (f.state === "null") return fe66_fitSub(tk, f);',
    'regime phrase')

BLOCK = r'''
// ── rt56 ──
// fe66-pure-begin
function fe66_setCcy(tk, c) {
  if (!c) return;
  if (!fe66_setCcy.map) fe66_setCcy.map = Object.create(null);
  fe66_setCcy.map[tk] = String(c);
}
function fe66_ccy(tk) {
  if (fe66_setCcy.map && fe66_setCcy.map[tk]) return fe66_setCcy.map[tk];
  try { if (typeof RT43_CUR !== "undefined" && RT43_CUR[tk]) return RT43_CUR[tk]; } catch (e) {}
  return "USD";
}
function fe66_setBasis(tk, b) {
  if (!b) return;
  if (!fe66_setBasis.map) fe66_setBasis.map = Object.create(null);
  fe66_setBasis.map[tk] = String(b);
}
function fe66_basis(tk) {
  return (fe66_setBasis.map && fe66_setBasis.map[tk]) || "";
}
function fe66_money(tk, n) {
  var v = Number(n);
  if (!isFinite(v)) return "\u2014";
  var ccy = fe66_ccy(tk);
  var whole = ccy === "JPY" || ccy === "KRW";
  var num = whole ? Math.round(v).toLocaleString("en-GB") : (Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(4));
  if (ccy === "GBp" || ccy === "GBX") return num + "p";
  if (ccy === "GBP") return "\u00a3" + num;
  if (ccy === "HKD") return "HK$" + num;
  if (ccy === "JPY") return "\u00a5" + num;
  if (ccy === "EUR") return "\u20ac" + num;
  if (ccy === "KRW") return "\u20a9" + num;
  return "$" + num;
}
function fe66_pct(ch) {
  var n = Number(ch);
  if (!isFinite(n)) return "";
  var body = n.toFixed(2);
  if (n < 0) return body + " (" + body + "%)";
  if (n > 0) return "+" + body + " (" + body + "%)";
  return "+0.00 (0.00%)";
}
function fe66_pick(data, yh, tk) {
  if (!data || typeof data !== "object") return null;
  if (yh && data[yh] && typeof data[yh] === "object" && typeof data[yh].p === "number") return data[yh];
  if (tk && data[tk] && typeof data[tk] === "object" && typeof data[tk].p === "number") return data[tk];
  if (typeof data.p === "number") return data;
  return null;
}
function fe66_nonUs(tk) {
  var t = String(tk || "");
  if (/\.(HK|L|T|DE|PA|KS|AX|NS|TO|SS|TW)$/i.test(t)) return true;
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && x.tk === t; }) : null;
    if (a && a._rt43) return true;
    if (a && a.cat === "Stock" && a.ex && !/^(NYSE|NASDAQ|AMEX|NYSEARCA|ARCA)$/.test(String(a.ex))) return true;
  } catch (e) {}
  return false;
}
function fe66_fitSub(tk, f) {
  var reason = f && f.reason ? String(f.reason) : "";
  if (!fe66_nonUs(tk || (f && f.ticker) || "")) {
    if (reason && !/no score is shown/i.test(reason)) return reason;
    return "Regime fit is not published for this name.";
  }
  if (reason && !/enter a market symbol/i.test(reason) && !/no score is shown/i.test(reason)) return reason;
  return "Fit score covers US-listed stocks for now.";
}
function fe66_tz(tk) {
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && x.tk === tk; }) : null;
    var map = { HKEX: "Asia/Hong_Kong", LSE: "Europe/London", TSE: "Asia/Tokyo", XETRA: "Europe/Berlin", EURONEXT: "Europe/Paris", KRX: "Asia/Seoul", NYSE: "America/New_York", NASDAQ: "America/New_York" };
    if (a && map[a.ex]) return map[a.ex];
  } catch (e) {}
  var t = String(tk || "");
  if (/\.HK$/i.test(t)) return "Asia/Hong_Kong";
  if (/\.L$/i.test(t)) return "Europe/London";
  if (/\.T$/i.test(t)) return "Asia/Tokyo";
  if (/\.DE$/i.test(t)) return "Europe/Berlin";
  if (/\.PA$/i.test(t)) return "Europe/Paris";
  if (/\.KS$/i.test(t)) return "Asia/Seoul";
  return "Europe/London";
}
function fe66_dynHead(tk) {
  if (fe66_closedQuote(tk)) {
    var wd = fe66_wd(tk);
    return wd ? ("Last session \u00b7 " + wd) : "Last session";
  }
  return "INTRADAY";
}
function fe66_dayKey(tk, ms) {
  try { return new Intl.DateTimeFormat("en-CA", { timeZone: fe66_tz(tk), year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms)); } catch (e) { return ""; }
}
function fe66_note(tk) {
  try {
    var bag = fe64_yqBag(tk);
    if (bag && bag.note) return String(bag.note);
  } catch (e) {}
  return "";
}
function fe66_closedQuote(tk, d) {
  if (d && d.status === "closed") return true;
  try { var bag = fe64_yqBag(tk); if (bag && bag.status === "closed") return true; } catch (e) {}
  try {
    if (typeof hasSyncedQuote === "function" && hasSyncedQuote(tk) && typeof _rt18MarketOpen === "function" && !_rt18MarketOpen(tk)) return true;
  } catch (e) {}
  return false;
}
function fe66_prevSession(tk) {
  var q = 15 * 60000, now = Date.now(), today = fe66_dayKey(tk, now);
  for (var t = now; t > now - 8 * 86400000; t -= q) {
    if (fe66_dayKey(tk, t) === today) continue;
    try { if (typeof _rt18MarketOpenAt === "function" && _rt18MarketOpenAt(tk, new Date(t))) return t; } catch (e) {}
  }
  return 0;
}
function fe66_wd(tk) {
  var ts = 0;
  try { ts = Number(liveQuoteTs[tk]) || 0; } catch (e) {}
  if (ts > 0 && ts < 1e10) ts *= 1000;
  if (!(ts > 0)) {
    var holiday = false;
    try { holiday = fe66_closedQuote(tk) && typeof _rt18MarketOpen === "function" && !!_rt18MarketOpen(tk); } catch (e) {}
    if (holiday) ts = fe66_prevSession(tk);
    else { try { ts = (typeof _rt20LastClose === "function" && _rt20LastClose(tk)) || 0; } catch (e) {} }
  }
  if (!(ts > 0)) return "";
  try { return new Date(ts).toLocaleDateString("en-GB", { weekday: "short", timeZone: "Europe/London" }); } catch (e) { return ""; }
}
function fe66_show(tk, d) {
  var n = null;
  try { n = P[tk] && P[tk].p; } catch (e) {}
  if (typeof n === "number" && isFinite(n) && n > 0) return fe66_money(tk, n);
  var p = d && d.p != null ? String(d.p) : "";
  if (p.charAt(0) === "\u2063") return p.slice(1);
  return p || "\u2014";
}
function fe66_priceLine(tk, d, na) {
  if (!na) {
    try { if (typeof hasSyncedQuote === "function" && !hasSyncedQuote(tk)) na = true; } catch (e) {}
  }
  if (na && !fe66_closedQuote(tk, d)) {
    try { return _rt22NoSync(); } catch (e) { return "Syncing\u2026"; }
  }
  var px = fe66_show(tk, d);
  if (px && px !== "\u2014") return px;
  try { return _rt22NoSync(); } catch (e) { return "Syncing\u2026"; }
}
function fe66_chgLine(tk, d, na) {
  var closed = fe66_closedQuote(tk, d);
  if (na && !closed) return "awaiting feed";
  var ch = null;
  try { ch = liveChg(tk); } catch (e) {}
  if (ch == null) { try { if (P[tk] && typeof P[tk].c === "number" && isFinite(P[tk].c)) ch = P[tk].c; } catch (e) {} }
  var pct = typeof ch === "number" && isFinite(ch) ? fe66_pct(ch) : "";
  if (closed) {
    var note = fe66_note(tk);
    var line = "Last close" + (pct ? " \u00b7 " + pct : "");
    return note ? line + " \u00b7 " + note : line;
  }
  if (ch == null) return "\u2014";
  var sign = ch >= 0 ? "+" : "";
  var arrow = ch > 0 ? "\u2191 " : ch < 0 ? "\u2193 " : "";
  var day = "today";
  try { day = _rt26Day(tk) || "today"; } catch (e) {}
  var abs = "";
  try { abs = d && d.chg != null ? d.chg : Number(ch).toFixed(2); } catch (e) { abs = Number(ch).toFixed(2); }
  var pctBody = "";
  try { pctBody = d && d.c != null ? d.c : Number(ch).toFixed(2); } catch (e) { pctBody = Number(ch).toFixed(2); }
  return arrow + sign + abs + " (" + sign + pctBody + "%)" + (day && day !== "today" ? " " + day : "");
}
function fe66_feedLbl(d, tk) {
  if (fe66_closedQuote(tk, d)) {
    var note = fe66_note(tk);
    return note || "Last close";
  }
  try { return fe65_feedLbl(d, tk); } catch (e) { return (d && d.label) || ""; }
}
function fe66_chartBit(tk, range, meta, proxyNote, quoteContext) {
  if (fe66_closedQuote(tk, meta) && String(range || "1d").toLowerCase() === "1d") {
    var wd = fe66_wd(tk);
    return wd ? ("Last session \u00b7 " + wd) : "Last session";
  }
  var head = "INTRADAY";
  try { head = _rt24ChartHead(tk, range); } catch (e) {}
  return head + " \u00b7 " + tk + (proxyNote || "") + " \u00b7 " + (quoteContext || "");
}
// fe66-pure-end
function fe66_force(tk, q, source) {
  if (!q || !(q.p > 0)) return false;
  if (!(q.status === "closed" || q.basis === "previous_close")) return false;
  try {
    var c = typeof q.c === "number" && isFinite(q.c) ? q.c : 0;
    P[tk] = { p: q.p, c: +Number(c).toFixed(2) };
    if (q.prev > 0) BASE[tk] = { p: q.prev, c: 0 };
    liveSymbols.add(tk);
    liveQuoteSrc[tk] = (q && q.source) || source || "yahoo";
    var ts = Number(q.ts || q.fetchedAt);
    if (ts > 0 && ts < 1e10) ts *= 1000;
    if (ts > 0) liveQuoteTs[tk] = ts;
    else if (!liveQuoteTs[tk]) liveQuoteTs[tk] = Date.now();
    liveQuoteMarketClosed[tk] = true;
    liveQuoteChangeAvailable[tk] = true;
    liveQuoteCached[tk] = !!q.cached;
    if (q.name) liveQuoteName[tk] = q.name;
    return true;
  } catch (e) { return false; }
}
function fe66_pull(tk) {
  try { tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk; } catch (e) {}
  if (!tk) return;
  if (!fe66_pull.on) fe66_pull.on = Object.create(null);
  if (fe66_pull.on[tk]) return;
  fe66_pull.on[tk] = 1;
  var yh = tk;
  try { yh = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk; } catch (e) {}
  fetch("/api/yahoo-quote?symbols=" + encodeURIComponent(yh), { signal: AbortSignal.timeout(8000) }).then(function (r) {
    return r && r.ok ? r.json() : null;
  }).then(function (data) {
    var q = fe66_pick(data, yh, tk);
    if (!q || !(q.p > 0)) { delete fe66_pull.on[tk]; return; }
    try { _applyLiveQuote(tk, q, "yahoo"); } catch (e) {}
    try { if (typeof _patchP2LiveHeader === "function") _patchP2LiveHeader(); } catch (e) {}
    try {
      if (typeof IS_DESKTOP === "function" && IS_DESKTOP()) { if (typeof renderP2 === "function") renderP2(); }
      else if (typeof renderMain === "function") renderMain();
    } catch (e) {}
  }).catch(function () { delete fe66_pull.on[tk]; });
}
try {
  var fe66_apply0 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q, source) {
    try {
      if (q && typeof q === "object") {
        if (q.currency) fe66_setCcy(tk, q.currency);
        if (q.basis) fe66_setBasis(tk, q.basis);
        if ((q.status === "closed" || q.basis === "previous_close") && q.p > 0) {
          if (!q.marketClosed) q.marketClosed = true;
          if (typeof q.c !== "number" || !isFinite(q.c)) q.c = (q.prev > 0 ? ((q.p - q.prev) / q.prev) * 100 : 0);
        }
      }
    } catch (e) {}
    var ok = false;
    try { ok = fe66_apply0.apply(this, arguments); } catch (e) { ok = false; }
    try { if (q) fe64_keepYq(tk, q); } catch (e) {}
    try {
      if (q && q.p > 0 && (q.status === "closed" || q.basis === "previous_close") && P[tk] && P[tk].p > 0) {
        if (typeof q.c === "number" && isFinite(q.c)) P[tk].c = +Number(q.c).toFixed(2);
        if (q.prev > 0) BASE[tk] = { p: q.prev, c: 0 };
        liveQuoteChangeAvailable[tk] = true;
        if (q.status === "closed") liveQuoteMarketClosed[tk] = true;
        liveSymbols.add(tk);
        var ts2 = Number(q.ts || q.fetchedAt);
        if (ts2 > 0 && ts2 < 1e10) ts2 *= 1000;
        if (ts2 > 0) liveQuoteTs[tk] = ts2;
      }
    } catch (e) {}
    var have = false;
    try { have = liveSymbols.has(tk) && P[tk] && P[tk].p > 0; } catch (e) {}
    if (!have) have = fe66_force(tk, q, source);
    try { if (q) fe64_keepYq(tk, q); } catch (e) {}
    return ok || have;
  };
} catch (e) {}
try {
  var fe66_qm = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe66_qm.apply(this, arguments);
    try {
      var bag = fe64_yqBag(tk);
      if (bag && bag.status === "closed" && liveSymbols.has(tk) && P[tk] && P[tk].p > 0) {
        var note = bag.note ? String(bag.note) : ((m && m.fe64Note) || "");
        m = Object.assign({}, m || {}, { status: "closed", label: "CLOSED", fe64Note: note, detail: note || "Last close" });
      }
    } catch (e) {}
    return m;
  };
} catch (e) {}
try {
  var fe66_lc = liveChg;
  liveChg = function (tk) {
    var r = null;
    try { r = fe66_lc.apply(this, arguments); } catch (e) { r = null; }
    if (r != null) return r;
    try {
      var fut = false;
      try { fut = typeof _rt27Fut === "function" && _rt27Fut(tk); } catch (e) {}
      if (!fut && (fe66_basis(tk) === "previous_close" || fe66_closedQuote(tk)) && P[tk] && typeof P[tk].c === "number" && isFinite(P[tk].c)) return P[tk].c;
    } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe66_cl0 = _rt23ChartLbl;
  _rt23ChartLbl = function (tk) {
    try {
      if (fe66_closedQuote(tk)) {
        var wd = fe66_wd(tk);
        if (wd) return "Last session \u00b7 " + wd;
      }
    } catch (e) {}
    return fe66_cl0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe66_term = termSelect;
  termSelect = function (tk) { var r = fe66_term.apply(this, arguments); try { fe66_pull(tk); } catch (e) {} return r; };
} catch (e) {}
try {
  var fe66_open = openA;
  openA = function (tk) { var r = fe66_open.apply(this, arguments); try { fe66_pull(tk); } catch (e) {} return r; };
} catch (e) {}
try {
  var fe66_boot = new URLSearchParams(location.search).get("t");
  if (fe66_boot) setTimeout(function () { fe66_pull(fe66_boot); }, 0);
} catch (e) {}
'''
if '// ── rt56 ──' in s: die('rt56 marker landed twice')
s = s.rstrip('\n') + '\n' + BLOCK
h = sub1(h, 'app.js?v=' + base + '"', 'app.js?v=' + nxt + '"', 'cache bust')

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
    t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if r.returncode: die('node --check failed: ' + (r.stderr or '')[:800])
print('OK rt56: %s -> %s; node --check passed%s' % (base, nxt, ' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
