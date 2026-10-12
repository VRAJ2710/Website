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
function _rt37LensRegime() {
  const r = _getRegimeState();
  try { const e = _computeRegimeEngine(), l = String(e.label || ""); r.label = l || r.label; r.id = /strong/i.test(l) ? "risk-on-strong" : /risk[- ]?off/i.test(l) ? "risk-off" : "risk-on-fragile"; } catch (e) {}
  return r;
}
function _rt37Hints(tks) {
  let h; try { h = typeof _rt17AskHints === "function" ? _rt17AskHints() : undefined; } catch (e) {}
  if (h && tks && tks.length && !tks.some(t => /^(XAU|GC=F|GLD|GOLD)$/i.test(t))) h = { ...h, focus: undefined };
  return h;
}
function _rt37Reply(t, tks) {
  try {
    let s = String(t || "");
    if (tks && tks.length && !tks.some(x => /^(XAU|GC=F|GLD|GOLD)$/i.test(x))) s = s.split(/\n/).filter(l => !/^\s*(\*\*)?\s*live:\s*gold\b/i.test(l)).join("\n").replace(/^\s*Live: Gold[^.\n]*\.\s*/i, "");
    return tks && tks[0] ? _rt32Txt(s, tks[0]) : s;
  } catch (e) { return t; }
}
async function _rt37Rss(sym) {
  try {
    const ys = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[sym]) || sym;
    const r = await fetch("/api/ticker-news?symbol=" + encodeURIComponent(ys), { signal: AbortSignal.timeout(10000) });
    if (!r.ok) return [];
    const d = await r.json();
    return (d.items || []).map(it => { const date = new Date(it.ts || Date.now()); return { t: String(date.getHours()).padStart(2, "0") + ":" + String(date.getMinutes()).padStart(2, "0"), x: it.title, desc: it.summary || "", tg: detectTag(it.title + " " + (it.summary || ""), "Stocks"), im: detectImpact(it.title), src: "Yahoo Finance", tier: 1, ts: it.ts || Date.now(), link: _newsLink({ link: it.link, x: it.title }), company: sym }; });
  } catch (e) { return []; }
}
function _rt37Ref(tk, q) {
  try {
    if (!q || !(q.p > 0)) return q;
    const flat = !(Number(q.c)) || (q.prev && Math.abs(q.prev - q.p) < 1e-9);
    if (!flat) return q;
    if (tk === "XAU") { _rt34Gc(); if (_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) return { ...q, c: _rt.gcPct.c, prev: q.p / (1 + _rt.gcPct.c / 100) }; }
    const o = { ...q }; delete o.c; delete o.prev; return o;
  } catch (e) { return q; }
}
function _rt37BriefDate(b) {
  try {
    const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date());
    const built = Date.parse(b.builtAt || b.generatedAt || b.asOf || "") || 0;
    const d = Date.parse(b.date || "");
    if (built) { const bd = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date(built)); if (!d || Math.abs(d - Date.parse(bd)) > 2 * 864e5) return bd; }
    if (!d || Date.now() - d > 4 * 864e5) return today;
    return b.date;
  } catch (e) { return b.date; }
}
try {
  const _cg0 = cgFetch;
  cgFetch = async function (url, opts) {
    const r = await _cg0(url, opts);
    try {
      const ao = r && r.headers && r.headers.get("X-Dispatch-Data-As-Of"), st = r && r.ok ? (r.headers.get("X-Dispatch-Data-Status") || "") : "bad";
      if (((ao && Date.now() - Date.parse(ao) > 24 * 3600e3) || st === "unavailable" || st === "bad") && /^https:\/\/api\.coingecko\.com\//.test(url)) {
        const d = await fetch(url, { credentials: "omit", signal: AbortSignal.timeout(8000) });
        if (d.ok) return d;
      }
    } catch (e) {}
    return r;
  };
} catch (e) {}
// chart watchdog: never leave 'LOADING CHART…' for more than 20s
setInterval(() => { try { document.querySelectorAll("div,text").forEach(el => { if (el.childElementCount || !/^LOADING CHART…$/.test((el.textContent || "").trim())) return; const t = +(el.dataset && el.dataset.rt37) || 0; if (!t) { if (el.dataset) el.dataset.rt37 = String(Date.now()); return; } if (Date.now() - t > 20000) el.textContent = "Chart unavailable right now"; }); } catch (e) {} }, 4000);
// phone: stock tabs stay reachable; the bottom bar hides while scrolling down so it never sits over a tapped tab
(() => { try {
  const st = document.createElement("style");
  st.textContent = `@media (max-width:767px){#main .tabs{position:sticky;top:0;z-index:6;background:var(--bg,#0b1018)}[data-rt34t]{table-layout:fixed;width:100%}[data-rt34t] td:first-child,[data-rt34t] th:first-child{width:44%}#bnav.rt37-hide{transform:translateY(110%);transition:transform .2s}#bnav{transition:transform .2s}}`;
  document.head.appendChild(st);
  let y0 = 0; addEventListener("scroll", () => { const b = document.getElementById("bnav"); if (!b || IS_DESKTOP()) return; const y = scrollY; if (y > y0 + 8 && y > 120) b.classList.add("rt37-hide"); else if (y < y0 - 8 || y < 120) b.classList.remove("rt37-hide"); y0 = y; }, { passive: true });
} catch (e) {} })();
function _rt37Hero() {
  const c = _rt37Count();
  if (c.open) return `${c.live} live`;
  const lc = _rt37LastClose();
  return `Markets closed${lc ? ` · last close ${lc}` : ""}`;
}
"""
R('p1 sub', "document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${feedSummary}`;", "document.getElementById('p1sub').textContent = `${tickers.length} of ${A.length} · ${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices${_usRegularOpen() ? '' : ' · markets closed'}`;")
R('rt mkt prefix', 'const t = (typeof _usRegularOpen === "function" && !_usRegularOpen() ? "US MARKETS CLOSED · " : "") + quoteStatusSummary(undefined, { includeUnavailable: true });', 'const t = _rt37Sum();')
R('lens regime', 'const regime = _getRegimeState();', 'const regime = _rt37LensRegime();')
R('ask hints', 'hints: typeof _rt17AskHints === "function" ? _rt17AskHints() : undefined', 'hints: _rt37Hints(tickers)')
R('ask reply', '      content: data.reply,', '      content: _rt37Reply(data.reply, tickers),')
R('chat purge', 'try { _chatMsgs = JSON.parse(sessionStorage.getItem("td_chat") || "[]"); } catch (e) { _chatMsgs = []; }', 'try { _chatMsgs = JSON.parse(sessionStorage.getItem("td_chat") || "[]"); } catch (e) { _chatMsgs = []; }\ntry { if (localStorage.getItem("td_chat_v") !== "chat34") { _chatMsgs = []; sessionStorage.removeItem("td_chat"); localStorage.removeItem("td_chat"); localStorage.setItem("td_chat_v", "chat34"); } } catch (e) {}')
R('flagship badge', 'id:"spx2026",\n    badge:"FLAGSHIP",', 'id:"spx2026",\n    badge:"ARCHIVE",')
R('flagship deck', 'Equal-weighting three scenarios yields a blended target of ~6,800.', 'Archived April outlook: the index has since moved well past these scenarios, so read it as a record of the reasoning, not a current target.')
R('flagship body', '<strong>Equal-weighting three scenarios — Iran-truce baseline, oil-shock stagflation, and a hyperscaler AI-capex boom — produces a blended target of ~6,800, flat from current levels but masking 60+ points of dispersion.</strong>', '<strong>Archived piece, published Apr 26, 2026. The index has since moved well above the scenario levels below; they are kept for the record and are not a current target.</strong>')
R('xau basis', 'if (_applyLiveQuote("XAU", data.XAU, data.XAU?.source)) hits++;', 'if (_applyLiveQuote("XAU", _rt37Ref("XAU", data.XAU), data.XAU?.source)) hits++;')
R('dxy basis', 'if (_applyLiveQuote("DXY", data.DXY, data.DXY?.source)) hits++;', 'if (_applyLiveQuote("DXY", _rt37Ref("DXY", data.DXY), data.DXY?.source)) hits++;')
R('closed label', 'label = proxy ? "STALE·PROXY" : "STALE";', 'label = !_usRegularOpen() ? "CLOSED" : proxy ? "STALE·PROXY" : "STALE";')
R('learn modules', "(LEARN_MODULES[_learnTab] || []).length} modules on professional analysis methodologies.", "(LEARN_MODULES[_learnTab] || []).length || Object.values(LEARN_MODULES).reduce((n, v) => n + (Array.isArray(v) ? v.length : 0), 0)} lessons on professional analysis methods.")
R('learn econ hide', "    ['economics','📈 Live Economics'],\n", "")
R('toast clear', 'clearTimeout(toastTO);toastTO=setTimeout(()=>el.classList.remove("show"),3200);', 'clearTimeout(toastTO);toastTO=setTimeout(()=>{el.classList.remove("show");el.textContent="";},3600);')
R('status ring', '${ring}<span class="${pulseCls}"></span>', '<span class="${pulseCls}"></span>', 2)
R('rss news', '_companyNewsCache[sym]={ts:Date.now(),items:mapped};', '_companyNewsCache[sym]={ts:Date.now(),items:mapped.length?mapped:await _rt37Rss(sym)};', 2)
R('brief date', 'function _rt18BriefClean(b) {\n  if (!b || typeof b !== "object") return b;\n  const out = { ...b };', 'function _rt18BriefClean(b) {\n  if (!b || typeof b !== "object") return b;\n  const out = { ...b };\n  out.date = _rt37BriefDate(out);')
R('brief hist', 'function _getBriefHistory() {\n  try { return JSON.parse(localStorage.getItem("td_brief_hist") || "[]"); } catch (e) { return []; }', 'function _getBriefHistory() {\n  try { return JSON.parse(localStorage.getItem("td_brief_hist") || "[]").filter(h => h && h.date && Date.now() - Date.parse(h.date) < 15 * 864e5); } catch (e) { return []; }')
R('desk compare', '    h += `<div class="tabs"><button class="${aTab==="ov"?"on":""}" onclick="_setATab(\'ov\')">Overview</button>', '    h += `<div style="display:flex;justify-content:flex-end;padding:6px 12px 0"><button type="button" class="hdr-act-btn" onclick="_toggleCompare(\'${termSelTk}\')">⚖ Compare</button></div>`;\n    h += `<div class="tabs"><button class="${aTab==="ov"?"on":""}" onclick="_setATab(\'ov\')">Overview</button>')
R('news chip', '${scoreLabel} ${scoreInfo.score}/10 · ${_escHtml(scoreDir)}${scoreInfo.tickers?.length?` · ${_escHtml(scoreInfo.tickers.join(","))}`:""}</span>${score!=null&&score>=4?`<span class="news-score" title="Desk relevance">R${score}</span>`:""}', 'Impact ${scoreInfo.score}/10</span>')
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
