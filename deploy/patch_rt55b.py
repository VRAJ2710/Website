#!/usr/bin/env python3
"""patch_rt55b.py: client patch on chat65. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat65, the output of patch_rt55.py on chat64:
  app.js md5 21e1d946e1b19a11d683f2b6120a8a34
  index.html md5 86eb7984bc6828d75dfc74847cf024f6
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

1) A chart with no history says what happened. A closed venue says when it
opens, from the quote status and nextOpen (the fe64 formatter) or the venue
calendar when the server sent no status.
2) " · ETF proxy" becomes " · tracked via an ETF".
3) Other user-visible fallback / proxy / insufficient wording is plain.
Code identifiers, comments and admin-only console text stay.
4) Ask list items use normal wrapping so a newline between items is not a
blank line. The chunk join is not touched.

No server file is changed.

Usage: python3 patch_rt55b.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "21e1d946e1b19a11d683f2b6120a8a34"
EXPECT_INDEX_MD5 = "86eb7984bc6828d75dfc74847cf024f6"
NEED_MARKER = "// ── rt55 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt55b ──' in s: already('rt55b already applied')
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

# 1) Chart copy. The sentence is chosen when the chart is drawn.
s = sub1(s,
'''      container.innerHTML = `<div class="dispatch-chart-unavailable">Chart unavailable for ${_escHtml(tk)}<br><span>Dispatch and fallback market feeds returned insufficient history.</span></div>`;''',
'''      container.innerHTML = `<div class="dispatch-chart-unavailable">Chart unavailable for ${_escHtml(tk)}<br><span>${_escHtml(fe65b_chartNote(tk))}</span></div>`;''',
'chart history sentence')
s = sub1(s,
'''        <span>TRADINGVIEW FALLBACK · ${_escHtml(tk)}</span>''',
'''        <span>Chart from TradingView · ${_escHtml(tk)}</span>''',
'tradingview heading')

# 2) The S&P line names the fund without calling it a proxy.
s = sub1(s, ' · ETF proxy', ' · tracked via an ETF', 'etf wording')

# 3) Other sentences a person can read.
s = sub1(s, 'China commodity demand proxy.', 'Tracks China commodity demand.', 'aud thesis')
s = sub1(s, 'Risk sentiment proxy at lower volatility.', 'Moves with risk sentiment, at lower volatility.', 'nzd thesis')
s = sub1(s, 'China demand proxy.', 'Tracks China demand.', 'asx thesis')
s = sub1(s, 'domestic economy proxy.', 'tracks the domestic economy.', 'iwm thesis')
s = sub1(s, 'Long-duration Treasury proxy.', 'Tracks long-duration Treasuries.', 'tlt thesis')
s = sub1(s, 'Rate-sensitive speculative proxy.', 'Rate-sensitive and speculative.', 'arkk thesis')
s = sub1(s, 'PMI and capex cycle proxy.', 'Tracks the PMI and capex cycle.', 'xli thesis')
s = sub1(s, 'Bond-proxy defensive sector.', 'Defensive sector that moves with bonds.', 'xlu thesis')
s = sub1(s, 'Equity as leveraged BTC proxy.', 'The shares move more than Bitcoin.', 'mstr thesis')
s = sub1(s, 'Bond-proxy with inflation escalators.', 'Moves with bonds, with inflation escalators.', 'o thesis')
s = sub1(s, 'Risk sentiment proxy.', 'Moves with risk sentiment.', 'eurjpy thesis')
s = sub1(s,
'''  let detail = "Free Yahoo/proxy feed — typically delayed, not exchange co-located";''',
'''  let detail = "Free Yahoo feed — typically delayed, not from the exchange";''',
'yahoo detail')
s = sub1(s,
'''    label = src.startsWith("gold-api-spot-proxy") ? "SPOT PROXY" : "SYNTH·DXY";''',
'''    label = src.startsWith("gold-api-spot-proxy") ? "free feed" : "SYNTH·DXY";''',
'gold label')
s = sub1(s,
'''    detail = "Finnhub free/proxy path — may be delayed or rate-limited";''',
'''    detail = "Finnhub free quote — may be delayed or rate-limited";''',
'finnhub detail')
s = sub1(s,
'''    label = !_rt18MarketOpen(tk) ? "CLOSED" : proxy ? "STALE·PROXY" : "STALE";''',
'''    label = !_rt18MarketOpen(tk) ? "CLOSED" : "STALE";''',
'stale label')
s = sub1(s,
'''    detail = `${proxy ? "Proxy value" : "Feed tick"} ${_fmtAge(ts)} old — not current market data`;''',
'''    detail = `${proxy ? "Older price" : "Feed tick"} ${_fmtAge(ts)} old — not current market data`;''',
'stale detail')
s = sub1(s,
'''  if (src === "gold-api-spot-proxy-browser") return "gold-api.com spot proxy";''',
'''  if (src === "gold-api-spot-proxy-browser") return "free gold feed";''',
'gold source name')
s = sub1(s,
'''  if (src.startsWith("gold-api-spot-proxy")) return "Spot Gold proxy";''',
'''  if (src.startsWith("gold-api-spot-proxy")) return "free gold feed";''',
'gold source prefix')
s = sub1(s,
'''  if (src === "frankfurter-ecb" || src === "open-exchange-rate-api") return "Synthetic DXY proxy";''',
'''  if (src === "frankfurter-ecb" || src === "open-exchange-rate-api") return "US dollar index";''',
'dollar source name')
s = sub1(s,
'''  if (degraded) parts.push("Price feed degraded or empty — free Yahoo/proxy can lag or fail.");''',
'''  if (degraded) parts.push("Price feed is delayed or empty. Free market prices can lag.");''',
'degraded banner')
s = sub1(s,
"    : d.status === \"proxy\" ? '<span class=\"tape-badge tape-cache\" title=\"Proxy reference price\">ref</span>'",
"    : d.status === \"proxy\" ? '<span class=\"tape-badge tape-cache\" title=\"Reference price\">ref</span>'",
'tape badge title')
s = sub1(s,
"      :d.status===\"proxy\"?'<span class=\"tape-badge tape-cache\" title=\"Proxy reference price\">ref</span>'",
"      :d.status===\"proxy\"?'<span class=\"tape-badge tape-cache\" title=\"Reference price\">ref</span>'",
'tape first-paint title')
s = sub1(s,
'''    ? `<div class="gd-sm">Volume profile is a range-distributed proxy, not exchange volume-at-price.</div>`''',
'''    ? `<div class="gd-sm">Volume profile spreads trades across the price range. It is not the exchange volume at each price.</div>`''',
'volume profile note')
s = sub1(s,
'''      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "Proxy levels — not dealer GEX.")}</p>''',
'''      <p class="gd-disclaimer">${_escHtml(d.gamma?.disclaimer || "Estimated levels, not the dealers' gamma exposure.")}</p>''',
'gamma disclaimer')
s = sub1(s,
'''    if (quoteHits < 4) throw new Error('Insufficient sector quote data');''',
'''    if (quoteHits < 4) throw new Error('Not enough sector prices to draw this view.');''',
'sector error')
s = sub1(s,
'''| SPOT PROXY | A free reference spot price, such as gold from gold-api.com. Close to the market, but not an exchange feed. |''',
'''| Reference spot | A free reference price, such as gold from a public gold feed. Close to the market, but not an exchange quote. |''',
'learn label row')
s = sub1(s,
''' ['spot-proxy','Spot proxy','Prices & data',''',
''' ['spot-proxy','Reference spot','Prices & data',''',
'glossary title')

BLOCK = r'''
// ── rt55b ──
function fe65b_openHm(tk, d) {
  var note = d && d.fe64Note ? String(d.fe64Note) : "";
  var m = note.match(/(\d{1,2}:\d{2})\s*UK/);
  if (m) return m[1];
  var bag = null;
  try { bag = fe64_yqBag(tk); } catch (e) { bag = null; }
  if (bag && (bag.note || bag.nextOpen || bag.nextOpen === 0)) {
    var words = "";
    try { words = fe64_closedWords(bag); } catch (e2) { words = ""; }
    var m2 = String(words || "").match(/(\d{1,2}:\d{2})\s*UK/);
    if (m2) return m2[1];
    try { if (!m2 && fe64_ukHm(bag.nextOpen)) return fe64_ukHm(bag.nextOpen); } catch (e3) {}
  }
  var ms = 0;
  try { ms = _rt51Next(tk); } catch (e4) { ms = 0; }
  try { return fe64_ukHm(ms) || ""; } catch (e5) { return ""; }
}
function fe65b_venue(tk) {
  var venue = "the market";
  try {
    var a = (typeof A !== "undefined" && A && A.find) ? A.find(function (x) { return x && x.tk === tk; }) : null;
    if (a && typeof _rt39Ex === "function") venue = _rt39Ex(a) || (a.ex || venue);
    else if (a && a.ex) venue = a.ex;
  } catch (e) {}
  return venue || "the market";
}
function fe65b_chartClosed(tk, d) {
  if (d && d.status) return d.status === "closed";
  try { return typeof _rt18MarketOpen === "function" && !_rt18MarketOpen(tk); } catch (e) { return false; }
}
function fe65b_chartNote(tk) {
  var d = null;
  try { d = typeof fp === "function" ? fp(tk) : null; } catch (e) { d = null; }
  if (!fe65b_chartClosed(tk, d)) return "Not enough price history yet for this chart. The latest price above is still live.";
  var hm = fe65b_openHm(tk, d);
  if (hm && /^\d:\d{2}$/.test(hm)) hm = "0" + hm;
  var venue = fe65b_venue(tk);
  return hm ? ("Chart fills in when " + venue + " opens (" + hm + " UK).") : ("Chart fills in when " + venue + " opens.");
}
function fe65b_css() {
  var st = document.createElement("style");
  st.setAttribute("data-fe65b", "chat");
  st.textContent = ".chat-body{white-space:normal}.chat-li{display:block;margin:0;padding:1px 0 1px 14px;line-height:1.35}";
  document.head.appendChild(st);
}
try { fe65b_css(); } catch (e) {}
'''
if '// ── rt55b ──' in s: die('rt55b marker landed twice')
s = s.rstrip('\n') + '\n' + BLOCK
h = sub1(h, 'app.js?v=' + base + '"', 'app.js?v=' + nxt + '"', 'cache bust')

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
    t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if r.returncode: die('node --check failed: ' + (r.stderr or '')[:800])
print('OK rt55b: %s -> %s; node --check passed%s' % (base, nxt, ' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
