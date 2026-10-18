#!/usr/bin/env python3
"""patch_rt38.py: chat34 -> chat35. Stacks on rt37 output (app.js 61eec45a). Client + index.html cache bust.
Greeting hour bands; Ask gold pills/hints + peer valuations; MU/UNH seed P/E removed; research archive badge on the
editorial render path; regime ring removed from /brief/ strip; Your Book race; Compare (2nd ticker input, COMPARE A B,
phone entry); dashboard desk-model calendar hidden; lookup 9s watchdog + Back; ticker news relevance and tagging;
overview AI gets live valuation; crypto header wording; ETF label.
Usage: python3 patch_rt38.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt38)' in s: die('rt38 already applied')
if 'REALTIME PRICE LAYER (rt37)' not in s: die('base is not rt37 output')
if 'app.js?v=chat34' not in h: die('index.html is not chat34')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt37)', '// REALTIME PRICE LAYER (rt38)')
R('seed MU', 'beta:1.62,pe:"18.4x",mc:"$115B"', 'beta:1.62,pe:"—",mc:"—"')
R('seed UNH', 'beta:0.68,pe:"18.4x",mc:"$555B"', 'beta:0.68,pe:"—",mc:"—"')
R('ask peers', '    await Promise.all(tickers.slice(0, 3).map(tk => _prefetchLensData(tk)));\n    const res = await fetch("/api/chat", {',
  '    await Promise.race([Promise.all([...tickers.slice(0, 3).map(tk => _prefetchLensData(tk)), ..._rt38Peers(tickers, text).map(tk => _rt33Ensure(tk, true))]), new Promise(r => setTimeout(r, 7000))]);\n    const res = await fetch("/api/chat", {')
R('ask ctx', '        context: _buildChatContext(),\n        tickers,', '        context: _buildChatContext() + _rt38PeerCtx(tickers, text),\n        tickers,')
R('ask pills', '      structured: data.structured || null,', '      structured: _rt38St(data.structured, tickers),')
R('research badge', '  editorialReports.forEach(rep=>{', '  editorialReports.forEach(rep=>{ if(rep.id==="spx2026"){ rep.badge="ARCHIVE · APR 2026"; rep.deck=(REPORTS.find(r=>r.id==="spx2026")||{}).deck||rep.deck; }')
R('research promo', '<div class="meta">FLAGSHIP RESEARCH</div>', '<div class="meta">ARCHIVED RESEARCH · APR 2026</div>')
R('brief ring', '<div class="ns-cell ns-regime">${_regimeRingSvg(re.score, re.col)}<div>', '<div class="ns-cell ns-regime"><div>')
R('book race', '    if (ch == null) return; // no feed this session — do not show a stale mark\n    out.push({ tk, ch, px: fp(tk).p });',
  '    out.push({ tk, ch, px: hasSyncedQuote(tk) ? fp(tk).p : "…" });')
R('book ch', '<span class="home-row-ch ${cls}">${r.ch > 0 ? "+" : ""}${r.ch.toFixed(2)}%</span>', '<span class="home-row-ch ${cls}">${r.ch == null ? "—" : (r.ch > 0 ? "+" : "") + r.ch.toFixed(2) + "%"}</span>')
R('calendar hide', 'function renderCalendar(){\n  const now=Date.now();', 'function renderCalendar(){\n  return ""; // rt38: the modelled (not live) calendar is hidden\n  const now=Date.now();')
R('lookup back', '<div style="padding:20px 16px">\n        <div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">"${shown}" — no price data found.</div>',
  '<div style="padding:20px 16px">\n        <button type="button" class="rt26-back" onclick="_dynTk=null;_dynData=null;_rt26Back()">← Back</button>\n        <div style="font-family:var(--sn);font-size:14px;color:var(--rd);margin-bottom:12px">"${shown}" — no price data found.</div>')
R('intel val', '  if (surface === "ticker" && tk) parts.push(_rt28Focus(tk));', '  if (surface === "ticker" && tk) { parts.push(_rt28Focus(tk)); try { parts.push(_rt33Ctx(tk)); } catch (e) {} }')
R('intel wait', '  _paintSiteIntelBar();\n  try {\n    const res = await fetch("/api/intelligence", {', '  _paintSiteIntelBar();\n  try { if (tk) await Promise.race([_rt33Ensure(tk, true), new Promise(r => setTimeout(r, 5000))]); } catch (e) {}\n  try {\n    const res = await fetch("/api/intelligence", {')
R('crypto hdr', '    : `Delayed \\u00b7 ${cg}${fr}`;', '    : (stale ? `Delayed \\u00b7 ${cg}${fr}` : `${cg}${fr}`);')
R('etf label', 'bd(a.cat,catBd(a.cat))', 'bd(/\\bETF\\b/.test(a.nm||"")?"ETF":a.cat,catBd(a.cat))', 2)
BLOCK = r'''// ── rt38 ──
// Sessions per asset class: never a global "markets closed"
{
  const _mo0 = _rt18MarketOpenAt;
  const VEN = { KRX: ["Asia/Seoul", 540, 930], ASX: ["Australia/Sydney", 600, 960], EURONEXT: ["Europe/Paris", 540, 1050], LSE: ["Europe/London", 480, 990], TSE: ["Asia/Tokyo", 540, 930], HKEX: ["Asia/Hong_Kong", 570, 960], NSE: ["Asia/Kolkata", 555, 930] };
  _rt18MarketOpenAt = function (tk, d) {
    try {
      const a = A.find(x => x.tk === tk);
      if (a && VEN[a.ex]) { const [tz, o, c] = VEN[a.ex]; const p = _rt18Parts(tz, d); return !["Sat", "Sun"].includes(p.wd) && p.m >= o && p.m < c; }
      if (a && a.cat === "FX" && a.ex === "US") { const p = _rt18Parts("America/New_York", d); return !["Sat", "Sun"].includes(p.wd) && p.m >= 570 && p.m < 960; }
    } catch (e) {}
    return _mo0(tk, d);
  };
  try { _rt18OpenCache.m = {}; } catch (e) {}
}
function _rt38Rep(cls) { const a = A.find(x => (cls === "fx" ? x.cat === "FX" && x.ex === "FOREX" : cls === "fut" ? x.cat === "Commodity" : cls === "asia" ? ["KRX", "ASX", "TSE", "HKEX"].includes(x.ex) : x.cat === "Stock" && (x.ex === "NYSE" || x.ex === "NASDAQ"))); return a ? a.tk : null; }
function _rt38Sessions() {
  try {
    const st = k => { const t = _rt38Rep(k); return t ? _rt18MarketOpen(t) : null; };
    const us = st("us"), fx = st("fx"), fut = st("fut"), asia = st("asia");
    const open = ["Crypto"]; if (fx) open.push("FX"); if (fut) open.push("futures"); if (asia) open.push("Asia");
    const bits = [`US stocks ${us ? "open" : "closed"}`, `${open.join(", ")} live`];
    if (fx === false) bits.push("FX opens Sun 22:00");
    else if (fut === false) bits.push("futures reopen 23:00");
    return bits.join(" · ");
  } catch (e) { return ""; }
}
_rt37Count = function () {
  let priced = 0, live = 0;
  try { A.forEach(a => { if (!hasSyncedQuote(a.tk)) return; priced++; let fresh = false; try { const m = _quoteMeta(a.tk); const ts = Number(liveQuoteTs[a.tk]) || 0; fresh = m.status === "live" || (ts > 0 && Date.now() - (ts < 1e10 ? ts * 1000 : ts) < 20 * 60000); } catch (e) {} if (_rt18MarketOpen(a.tk) && fresh) live++; }); } catch (e) {}
  return { priced, live, total: A.length, open: _usRegularOpen() };
};
_rt37Sum = function () {
  const c = _rt37Count();
  if (!c.priced) return "Prices loading";
  return `${c.priced} prices · ${c.live} live`;
};
try {
  quoteStatusSummary = function (tickers) {
    const list = [...new Set((tickers || A.map(a => a.tk)).filter(Boolean))];
    let priced = 0, live = 0;
    list.forEach(tk => { if (hasSyncedQuote(tk)) { priced++; if (_rt18MarketOpen(tk) && _quoteMeta(tk).status !== "stale") live++; } });
    if (!priced) return "prices loading";
    return `${priced} prices · ${live} live`;
  };
} catch (e) {}
_rt37Hero = function () {
  const c = _rt37Count(), out = [`${c.live} live`];
  if (!c.open) { const lc = _rt37LastClose(); out.push(`US stocks closed${lc ? ` · US close ${lc}` : ""}`); } else out.push("US stocks open");
  try { if (hasSyncedQuote("BTC")) out.push(`BTC ${fp("BTC").p}`); } catch (e) {}
  try { if (hasSyncedQuote("XAU")) out.push(`Gold ${fp("XAU").p}`); } catch (e) {}
  return out.join(" · ");
};
// sessions line under the price count on the strip and status chip
setInterval(() => { try {
  const t = _rt38Sessions(); if (!t) return;
  document.querySelectorAll("#latency-strip").forEach(el => { let s = el.querySelector(".rt38-sess"); if (!s) { s = document.createElement("span"); s.className = "latency-pill rt38-sess"; el.insertBefore(s, el.children[1] || null); } if (s.textContent !== t) s.textContent = t; });
} catch (e) {} }, 2000);
_homeGreeting = function () {
  let h = NaN;
  try { h = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).find(p => p.type === "hour").value) % 24; } catch (e) {}
  if (isNaN(h)) return "";
  if (h >= 5 && h < 12) return "Good morning";
  if (h >= 12 && h < 17) return "Good afternoon";
  if (h >= 17 && h < 22) return "Good evening";
  return "";
};
const RT38_GOLD = /^(XAU|GC=F|GLD|GOLD|SLV|XAG)$/i;
const RT38_SEMI = ["NVDA", "AMD", "AVGO", "MU", "TSM", "INTC", "QCOM"];
function _rt38Peers(tks, text) {
  try {
    const set = [];
    (tks || []).forEach(t => { if (!set.includes(t)) set.push(t); });
    if (tks && tks[0] && /peer|compar|versus|\bvs\b|relative|cheap|expensive|valuation|p\/e/i.test(String(text || ""))) {
      if (RT38_SEMI.includes(tks[0])) RT38_SEMI.forEach(t => { if (!set.includes(t)) set.push(t); });
    }
    return set.filter(t => { const a = A.find(x => x.tk === t); return a && a.cat === "Stock"; }).slice(0, 6);
  } catch (e) { return []; }
}
function _rt38PeerCtx(tks, text) {
  try {
    const peers = _rt38Peers(tks, text);
    if (!peers.length) return "";
    const f = x => x == null || !isFinite(x) ? "—" : Number(x).toFixed(1) + "x";
    const rows = peers.map(t => { const v = _rt33Val(t); return v ? `${t} P/E ${f(v.pe)} · fwd P/E ${f(v.forwardPe)} · mkt cap ${_rt33Mc(v.marketCap)}` : `${t} valuation unavailable`; });
    let spy = ""; try { const sv = _finCache.SPY && _finCache.SPY.valuation; if (sv && sv.pe) spy = ` | SPY (S&P 500 ETF) P/E ${f(sv.pe)}`; } catch (e) {}
    return `\nPeer valuations (live, from /api/financials — quote only these; do not lead with gold or macro unless asked):\n${rows.join("\n")}${spy}`;
  } catch (e) { return ""; }
}
function _rt38St(st, tks) {
  try {
    if (!st || typeof st !== "object") return st || null;
    const o = { ...st };
    const nonGold = tks && tks.length && !tks.some(t => RT38_GOLD.test(t));
    if (/^informative$/i.test(String(o.verdict || ""))) o.verdict = "";
    if (nonGold && Array.isArray(o.dataUsed)) o.dataUsed = o.dataUsed.filter(d => !/\bgold\b|GC=F|XAU|^\s*windows?:/i.test(String(d)));
    if (nonGold && Array.isArray(o.sources)) o.sources = o.sources.filter(s => !/\bgold\b|GC=F|XAU|windows?:/i.test(JSON.stringify(s || "")));
    return o;
  } catch (e) { return st; }
}
_rt37Hints = function (tks) {
  let h; try { h = typeof _rt17AskHints === "function" ? _rt17AskHints() : undefined; } catch (e) {}
  if (h && tks && tks.length && !tks.some(t => RT38_GOLD.test(t))) { h = { ...h }; delete h.focus; }
  return h;
};
_rt37Rss = async function (sym) {
  try {
    const a = A.find(x => x.tk === sym) || {};
    const ys = (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[sym]) || sym;
    const r = await fetch("/api/ticker-news?symbol=" + encodeURIComponent(ys), { signal: AbortSignal.timeout(10000) });
    if (!r.ok) return [];
    const d = await r.json();
    const stem = String(a.nm || "").replace(/[,.]?\s+(Inc|Corp(oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd|SA|NV|Platforms|Class [A-Z])\b.*$/i, "").trim();
    const esc = x => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const names = [sym.length >= 2 ? `\\b${esc(sym)}\\b` : `\\(${esc(sym)}\\)`, stem && stem.length >= 3 ? `\\b${esc(stem)}` : "", a.cat === "Crypto" ? `\\b${esc(String(a.nm || "").split(" ")[0])}\\b` : ""].filter(Boolean);
    const re = new RegExp(names.join("|"), a.cat === "Crypto" || sym.length >= 3 ? "i" : "");
    return (d.items || []).filter(it => re.test(it.title || "")).map(it => { const date = new Date(it.ts || Date.now()); return { t: String(date.getHours()).padStart(2, "0") + ":" + String(date.getMinutes()).padStart(2, "0"), x: it.title, desc: it.summary || "", tg: a.cat === "Crypto" ? "Crypto" : "Stocks", im: detectImpact(it.title), src: "Yahoo Finance", tier: 1, ts: it.ts || Date.now(), link: _newsLink({ link: it.link, x: it.title }), company: sym }; });
  } catch (e) { return []; }
};
// Compare: second-ticker input, COMPARE A B command, phone entry
function _rt38CmpAdd(v) {
  const t = resolveInternalTicker(String(v || "").trim()) || String(v || "").trim().toUpperCase();
  if (!t) return;
  if (!_compareTks.includes(t)) { if (_compareTks.length >= 3) { showToast("Max 3 tickers to compare", "var(--gd)"); return; } _compareTks.push(t); }
  Promise.race([_rt33Ensure(t, true), new Promise(r => setTimeout(r, 6000))]).then(() => { try { _refreshOverlay("compareOv", _renderCompare); } catch (e) {} });
  try { _refreshOverlay("compareOv", _renderCompare) || _showOverlay("compareOv", "⚖ Ticker Compare", _renderCompare()); } catch (e) {}
}
{
  const _rc0 = _renderCompare;
  _renderCompare = function () {
    const add = `<form style="display:flex;gap:6px;padding:12px 12px 0" onsubmit="event.preventDefault();_rt38CmpAdd(this.t.value);this.t.value=''"><input name="t" aria-label="Add a ticker to compare" placeholder="Add ticker, e.g. NVDA" autocomplete="off" style="flex:1;min-width:0;background:var(--b1);border:1px solid var(--gb);color:var(--tx);border-radius:8px;padding:8px;font-family:var(--mn)"><button type="submit" class="hdr-act-btn">Add</button></form>`;
    return add + _rc0.apply(this, arguments);
  };
  const _tc0 = _toggleCompare;
  _toggleCompare = function (tk) { _tc0.apply(this, arguments); try { _compareTks.forEach(t => Promise.race([_rt33Ensure(t, true), new Promise(r => setTimeout(r, 6000))]).then(() => _refreshOverlay("compareOv", _renderCompare))); } catch (e) {} };
  const _lt0 = lookupTicker;
  lookupTicker = async function (tk) {
    const m = String(tk || "").trim().toUpperCase().match(/^COMPARE\s+([A-Z0-9.\-=^]{1,12})(?:\s*(?:VS\.?|,|\s)\s*([A-Z0-9.\-=^]{1,12}))?(?:\s*(?:VS\.?|,|\s)\s*([A-Z0-9.\-=^]{1,12}))?$/);
    if (m) { _compareTks = []; m.slice(1).filter(Boolean).forEach(_rt38CmpAdd); if (!document.getElementById("compareOv")) _showOverlay("compareOv", "⚖ Ticker Compare", _renderCompare()); return; }
    const seq0 = _lookupSeq + 1;
    setTimeout(() => { try { if (_lookupSeq === seq0 && _dynLoading) { _lookupSeq++; _dynLoading = false; _dynData = null; if (IS_DESKTOP()) renderP2(); else renderMain(); } } catch (e) {} }, 9000);
    return _lt0.apply(this, arguments);
  };
}
setInterval(() => { try {
  if (IS_DESKTOP()) return;
  const t = (typeof selTk !== "undefined" && selTk) || null;
  document.querySelectorAll(".rt26-back").forEach(b => {
    if (!t || b.nextElementSibling && b.nextElementSibling.classList.contains("rt38-cmp")) return;
    if (!document.querySelector(".rt23-stock")) return;
    const c = document.createElement("button"); c.type = "button"; c.className = "rt38-cmp rt26-back"; c.style.marginLeft = "8px"; c.textContent = "⚖ Compare";
    c.onclick = () => _toggleCompare(selTk); b.after(c);
  });
} catch (e) {} }, 800);
(() => { try { const st = document.createElement("style"); st.textContent = `@media (max-width:400px){[data-rt34t] td,[data-rt34t] th{padding:5px 4px!important;font-size:10px!important;overflow-wrap:anywhere;white-space:normal!important}[data-rt34t] td:last-child,[data-rt34t] th:last-child{text-align:right}}`; document.head.appendChild(st); } catch (e) {} })();
// AI overview text: drop "not provided" sentences when live valuation exists
{
  const _cl0 = _rt32Txt;
  _rt32Txt = function () { const r = _cl0.apply(this, arguments); return typeof r === "string" ? r.replace(/[^.!?]*\b(?:are|is|were|was)\s+not\s+(?:provided|available|supplied)\b[^.!?]*[.!?]\s*/gi, "").replace(/[^.!?]*\bnot provided\b[^.!?]*[.!?]\s*/gi, "") : r; };
}
'''
R('stale closed per venue', 'label = !_usRegularOpen() ? "CLOSED" : proxy ? "STALE·PROXY" : "STALE";', 'label = !_rt18MarketOpen(tk) ? "CLOSED" : proxy ? "STALE·PROXY" : "STALE";')
R('adopt closed per venue', 'closed = !_usRegularOpen();', 'closed = !_rt18MarketOpen(tk);')
R('p1sub', "${_usRegularOpen() ? '' : ' · markets closed'}", "")
R('hero vix', 'VIX${_usRegularOpen() ? "" : " close"}', 'VIX${_usRegularOpen() ? "" : " US close"}')
R('hero spx', '${re.spxProxy ? "SPY" : "SPX"}${_usRegularOpen() ? "" : " close"}', '${re.spxProxy ? "SPY" : "SPX"}${_usRegularOpen() ? "" : " US close"}')
R('chart lbl', '  let open = true; try { open = _usRegularOpen(); } catch (e) {}\n  return open ? "INTRADAY · UPDATES ON FETCH"', '  let open = true; try { open = _rt18MarketOpen(tk); } catch (e) {}\n  return open ? "INTRADAY · UPDATES ON FETCH"')
R('rt38 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat34', 'app.js?v=chat35')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
