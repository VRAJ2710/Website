#!/usr/bin/env python3
"""patch_rt37.py — chat33 -> chat34. Stacks on rt36 output (app.js cb92677d). Client + index.html cache bust.
One price count everywhere (_rt37Count): status chip, latency strip, Markets header, dashboard badge, Home hero.
Plain time labels (Updated just now / HH:MM), "Delayed data" disclaimer, UK-time greeting, closing labels when closed.
Usage: python3 patch_rt37.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt37)' in s: die('rt37 already applied')
if 'REALTIME PRICE LAYER (rt36)' not in s: die('base is not rt36 output')
if 'app.js?v=chat33' not in h: die('index.html is not chat33')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt36)', '// REALTIME PRICE LAYER (rt37)')
R('summary x3', 'const feedSummary = quoteStatusSummary(undefined, { includeUnavailable: true });', 'const feedSummary = _rt37Sum();', 3)
R('dot prefix', 'liveEl.textContent = (_usRegularOpen() ? "" : "US MARKETS CLOSED · ") + feedSummary;', 'liveEl.textContent = feedSummary;')
R('chip prefix', '${_usRegularOpen()?"":"US CLOSED · "}${_escHtml(feedSummary)}', '${_escHtml(feedSummary)}')
R('strip', """   const nLive=[...liveSymbols].filter(hasSyncedQuote).length;
  return `<div class="latency-strip" id="latency-strip">
    <span class="latency-pill">${nLive?nLive+" SYNCED":"NO FEED"}</span>
    <span class="latency-pill">PRICES ${pAge} · as of ${pAs}</span>
    <span class="latency-pill">NEWS ${nAge}</span>
    <span class="latency-pill latency-muted">YAHOO DELAYED · NOT BLOOMBERG</span>""", """   const _c=_rt37Count();
  return `<div class="latency-strip" id="latency-strip">
    <span class="latency-pill">${_c.priced?`${_c.priced} prices · ${_rt37Upd(priceLastFetch&&priceLastFetch.getTime())}`:"Prices loading"}</span>
    <span class="latency-pill">News ${_rt37Upd(newsLastFetch&&newsLastFetch.getTime()).replace(/^U/,"u")}</span>
    <span class="latency-pill latency-muted">Delayed data</span>""")
R('dash badge', 'bd(primaryLiveCount + " of " + A.length + " priced", "var(--gn)")', 'bd(_rt37Count().priced + " prices", "var(--gn)")')
R('strip priced', '${A.length - quoteStatusCounts().unavailable}', '${_rt37Count().priced}')
R('hero count', 'const liveN = quoteStatusCounts().live;', 'const liveN = _rt37Count().priced;')
R('hero tape', '[`${liveN} symbol${liveN === 1 ? "" : "s"} live`, (re.vix != null && re.vix !== "—" && re.vix !== "") ? `VIX ${re.vix}` : "", (re.spx != null && re.spx !== "—" && re.spx !== "") ? `${re.spxProxy ? "SPY" : "SPX"} ${re.spx}` : ""]',
  '[_rt37Hero(), (re.vix != null && re.vix !== "—" && re.vix !== "") ? `VIX${_usRegularOpen() ? "" : " close"} ${re.vix}` : "", (re.spx != null && re.spx !== "—" && re.spx !== "") ? `${re.spxProxy ? "SPY" : "SPX"}${_usRegularOpen() ? "" : " close"} ${re.spx}` : ""]')
R('greeting', 'function _homeGreeting() {\n  const h = new Date().getHours();\n  if (h < 12) return "Good morning";\n  if (h < 18) return "Good afternoon";\n  return "Good evening";\n}',
  'function _homeGreeting() {\n  let h = new Date().getHours();\n  try { h = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", hour12: false }).format(new Date())) % 24; } catch (e) {}\n  if (h >= 5 && h < 12) return "Good morning";\n  if (h >= 12 && h < 17) return "Good afternoon";\n  return "Good evening";\n}')
R('yahoo detail', 'detail = "Yahoo Finance via Dispatch proxy — free retail feed, not Bloomberg";', 'detail = "Yahoo Finance · delayed data";')
R('paper rail', 'Prices: Yahoo / CoinGecko delayed free feeds — never seed prints.', 'Prices: delayed data from Yahoo Finance and CoinGecko.')
BLOCK = r"""// ── rt37: one price count for every surface ──
function _rt37Count() {
  let priced = 0, live = 0;
  try { A.forEach(a => { if (hasSyncedQuote(a.tk)) { priced++; if (_quoteMeta(a.tk).status === "live") live++; } }); } catch (e) {}
  return { priced, live, total: A.length, open: _usRegularOpen() };
}
function _rt37Sum() {
  const c = _rt37Count();
  if (!c.priced) return "Prices loading";
  return c.open ? `${c.priced} prices · ${c.live} live` : `${c.priced} prices · markets closed`;
}
function _rt37Upd(ts) {
  if (!ts) return "Updating…";
  const s = (Date.now() - ts) / 1000;
  if (s < 60) return "Updated just now";
  try { return "Updated " + new Intl.DateTimeFormat("en-GB", { timeZone: _rt17Tz(), hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(ts)); } catch (e) { return "Updated"; }
}
function _rt37LastClose() {
  try {
    const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", hour: "2-digit", hour12: false }).formatToParts(new Date()).map(x => [x.type, x.value]));
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]; let d = days.indexOf(p.weekday); const h = Number(p.hour) % 24;
    if (d >= 1 && d <= 5 && h >= 16) return d === new Date().getDay() ? "today" : days[d];
    do { d = (d + 6) % 7; } while (d === 0 || d === 6);
    return days[d];
  } catch (e) { return ""; }
}
try {
  quoteStatusSummary = function (tickers) {
    const list = [...new Set((tickers || A.map(a => a.tk)).filter(Boolean))];
    let priced = 0, live = 0;
    list.forEach(tk => { if (hasSyncedQuote(tk)) { priced++; if (_quoteMeta(tk).status === "live") live++; } });
    if (!priced) return "prices loading";
    return _usRegularOpen() ? `${priced} prices · ${live} live` : `${priced} prices · markets closed`;
  };
} catch (e) {}
function _rt37Hero() {
  const c = _rt37Count();
  if (c.open) return `${c.live} live`;
  const lc = _rt37LastClose();
  return `Markets closed${lc ? ` · last close ${lc}` : ""}`;
}
"""
R('p1 sub', "document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${feedSummary}`;", "document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices${_usRegularOpen() ? '' : ' · markets closed'}`;")
R('rt mkt prefix', 'const t = (typeof _usRegularOpen === "function" && !_usRegularOpen() ? "US MARKETS CLOSED · " : "") + quoteStatusSummary(undefined, { includeUnavailable: true });', 'const t = _rt37Sum();')
R('rt37 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')

for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat33', 'app.js?v=chat34')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
