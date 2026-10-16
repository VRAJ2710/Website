#!/usr/bin/env python3
"""patch_rt43.py: chat39 -> chat40. Stacks on rt42 output (app.js 0a97a3d9). Client + index.html.
A spot commodities (gold-api.com XAG/XPT/XPD/HG in the browser; WTI/Brent spot from the server's shared Twelve Data
  cache) as the primary figure, futures kept as a 'delayed 10 min' secondary line; CME futures labelled DELAYED 10m
B fast poll keeps futures while their venue is open (no >30 min skip at the 23:00 BST reopen)
C DXY computed in the browser from six live FX pairs (ICE weights); ECB/frankfurter never displayed
D last-good / rate-limited copies shown as STALE with their age
E numbered Yahoo ids for UNI/MATIC(POL)/APT/SUI/PEPE in the source map
F phone stream cap 40 -> 100 with visible rows first; ES=F / YM=F overnight lines for S&P/Dow; US pre-market and
  after-hours prints as a labelled secondary line
G home listings HSBA.L AZN.L SHEL.L SAP.DE SIE.DE MC.PA 7203.T 6758.T 0700.HK 9988.HK 005930.KS with venue hours,
  lunch breaks and local currency
tidy: FX live window one rule for strip and table; INTEL headline fit = Pulse fit; one regime label desktop/phone;
pricing copy (Manage billing, plan label, Create free account, no BYOK, consistent Free/Premium lists)
Usage: python3 patch_rt43.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt43)' in s: die('rt43 already applied')
if 'REALTIME PRICE LAYER (rt42)' not in s: die('base is not rt42 output')
if 'app.js?v=chat39' not in h: die('index.html is not chat39')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt42)', '// REALTIME PRICE LAYER (rt43)')
R('F phone cap', 'const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 40;', 'const RT_YS_CAP_DESK = 150, RT_YS_CAP_PHONE = 100;')
R('F visible first', 'for (const tk of _rt.want) {\n      const yh = YAHOO_SYMBOLS[tk];\n      if (!yh || !rev[yh] || _rtYsSkip(tk, yh)) continue;',
  'for (const tk of new Set([...(_rt.visible || []), ..._rt.want])) {\n      const yh = YAHOO_SYMBOLS[tk];\n      if (!yh || !rev[yh] || _rtYsSkip(tk, yh)) continue;')
R('F ext stream', 'if (_rtIsUsEquitySym(yh) && !usOpen) continue;', 'if (_rtIsUsEquitySym(yh) && !usOpen && !_rt43ExtOpen()) continue;', 2)
R('F ext tick', '    if (!_usRegularOpen()) return;', '    if (!_usRegularOpen()) { try { _rt43ExtTick(tks, d); } catch (e) {} return; }')
R('B futures reopen', '    if (liveQuoteTs[tk] && now - liveQuoteTs[tk] > 30 * 60_000) return false;',
  '    if (liveQuoteTs[tk] && now - liveQuoteTs[tk] > 30 * 60_000 && !(/=F$/.test(yh) && _rt18MarketOpen(tk))) return false;')
R('E uni/matic', 'UNI:"UNI-USD",MATIC:"MATIC-USD"', 'UNI:"UNI7083-USD",MATIC:"POL28321-USD"')
R('E apt/sui', 'APT:"APT-USD",SUI:"SUI-USD"', 'APT:"APT21794-USD",SUI:"SUI20947-USD"')
R('E pepe', 'PEPE:"PEPE-USD"', 'PEPE:"PEPE24478-USD"')
R('E crypto ok', 'const YAHOO_CRYPTO_OK=new Set(["BTC","ETH","SOL","XRP","DOGE","ADA","LTC","LINK","AVAX","BCH","DOT","ATOM","NEAR"]);',
  'const YAHOO_CRYPTO_OK=new Set(["BTC","ETH","SOL","XRP","DOGE","ADA","LTC","LINK","AVAX","BCH","DOT","ATOM","NEAR","UNI","MATIC","APT","SUI","PEPE"]);')
R('regime phone', '>${_mobShortRegime(re.label)}</span>`;', '>${re.label} · ${re.score}/100</span>`;')
R('regime phone loading', 'Regime…</span>', 'Regime: loading…</span>')
R('billing btn', 'Manage billing (Stripe)', 'Manage billing')
R('billing menu', 'Plan &amp; billing</button>', 'Manage billing</button>')
R('admin plan', '"Admin · full access"', '"Admin · Premium included"')
R('signup', '<a href="/__auth/subscribe" class="${cls}">Sign up</a>', '<a href="/__auth/register" class="${cls}">Create free account</a>')
R('onboard copy', 'Gold desk · conditional weekly playbook · your own AI keys next. Not four chatbots.', 'Gold desk · conditional weekly playbook · AI research assistant on Premium.')
R('tier 1', '<li>AI Dispatch Brief (LLM)</li>', '<li>Weekly Gold Playbook</li>\n          <li>AI Dispatch Brief</li>')
R('tier 2', '<li>Lens Engine · Expert chat</li>', '<li>Ask research assistant · AI lenses</li>')
R('tier 3', '<li>Statements · institutions</li>', '<li>Company statements · institutional holders</li>')
R('fd dollar desc', 'return _frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "ICE index");', 'return _frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index");')
R('feed chip class', '<span style="font-family:var(--mn);font-size:9px;background:${isLive?\'var(--gnG)\':\'var(--b3)\'};', '<span class="rt43-feed" data-tk="${a.tk}" style="font-family:var(--mn);font-size:9px;background:${isLive?\'var(--gnG)\':\'var(--b3)\'};')
R('upsell', 'Free: tape, regime, desk brief, Lab models · Premium: LLM + deep data · £15/mo via Stripe', 'Free: prices, regime, desk brief, Lab · Premium: Gold Playbook, AI brief, Ask, statements · £15/month')
BLOCK = r'''// ── rt43 ──
// G: home-exchange listings (Yahoo symbol = internal ticker), venue hours with lunch breaks, local currency
const RT43_INTL = [["HSBA.L", "HSBC Holdings", "LSE", "GBp", "UK"], ["AZN.L", "AstraZeneca", "LSE", "GBp", "UK"], ["SHEL.L", "Shell", "LSE", "GBp", "UK"],
  ["SAP.DE", "SAP", "XETRA", "EUR", "DE"], ["SIE.DE", "Siemens", "XETRA", "EUR", "DE"], ["MC.PA", "LVMH", "EURONEXT", "EUR", "FR"],
  ["7203.T", "Toyota Motor", "TSE", "JPY", "JP"], ["6758.T", "Sony Group", "TSE", "JPY", "JP"], ["0700.HK", "Tencent", "HKEX", "HKD", "HK"],
  ["9988.HK", "Alibaba Group", "HKEX", "HKD", "HK"], ["005930.KS", "Samsung Electronics", "KRX", "KRW", "KR"]];
const RT43_CUR = {}, RT43_SYM = { EUR: "€", JPY: "¥", HKD: "HK$", KRW: "₩" };
try { RT43_INTL.forEach(([tk, nm, ex, cur, rg]) => { RT43_CUR[tk] = cur; if (A.some(a => a.tk === tk)) return;
  A.push({ tk, nm: `${nm} (${ex})`, cat: "Stock", ex, rg, sc: 60, se: "Neutral", ra: "Hold", beta: null, pe: "", mc: "", th: `${nm}, home listing on ${ex}, quoted in ${cur === "GBp" ? "pence (GBp)" : cur}. Prices stream from Yahoo during the ${ex} session; outside it the last close is shown.`, _rt43: true });
  YAHOO_SYMBOLS[tk] = tk; try { if (TICKER_CATS.AAPL) TICKER_CATS[tk] = TICKER_CATS.AAPL; } catch (e) {} }); } catch (e) {}
{
  const _fp0 = fp;
  fp = function (tk) {
    const r = _fp0.apply(this, arguments);
    try { const k = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk, cur = RT43_CUR[k];
      if (cur && r && r.p !== "—" && typeof r.p === "string" && r.p[0] !== "\u2063") r.p = "\u2063" + (cur === "GBp" ? `${r.p}p` : RT43_SYM[cur] + r.p); } catch (e) {}
    return r;
  };
  // renderers put "$" in front of fp().p for stocks: drop it when a local-currency marker follows
  const fix = n => { try { if (n.nodeType === 3) { if (n.nodeValue.indexOf("$\u2063") >= 0) n.nodeValue = n.nodeValue.split("$\u2063").join(""); }
    else if (n.nodeType === 1 && n.textContent.indexOf("$\u2063") >= 0) { const w = document.createTreeWalker(n, 4); let t; while ((t = w.nextNode())) if (t.nodeValue.indexOf("$\u2063") >= 0) t.nodeValue = t.nodeValue.split("$\u2063").join(""); } } catch (e) {} };
  try { new MutationObserver(ms => { for (const m of ms) { if (m.type === "characterData") fix(m.target); else m.addedNodes.forEach(fix); } }).observe(document.documentElement, { subtree: true, childList: true, characterData: true }); } catch (e) {}
  const H = { LSE: ["Europe/London", 480, 990], XETRA: ["Europe/Berlin", 540, 1050], EURONEXT: ["Europe/Paris", 540, 1050], TSE: ["Asia/Tokyo", 540, 930, 690, 750], HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780], KRX: ["Asia/Seoul", 540, 930] };
  const _mo1 = _rt18MarketOpenAt;
  _rt18MarketOpenAt = function (tk, d) {
    try { const a = A.find(x => x.tk === tk);
      if (a && a._rt43 && H[a.ex]) { const [tz, o, c, lo, lc] = H[a.ex], p = _rt18Parts(tz, d || new Date());
        if (["Sat", "Sun"].includes(p.wd) || (lo && p.m >= lo && p.m < lc)) return false; return p.m >= o && p.m < c; } } catch (e) {}
    return _mo1.apply(this, arguments);
  };
  try { _rt18OpenCache.m = {}; } catch (e) {}
}
// A/C/D: spot commodities, computed DXY, honest stale labels
const RT43_METAL = { SLV: ["XAG", "Spot silver"], PLAT: ["XPT", "Spot platinum"], PALLADIUM: ["XPD", "Spot palladium"], COPPER: ["HG", "Spot copper"] };
const RT43_ENERGY = { WTI: 1, BRENT: 1 };
const _rt43Spot = {}, _rt43Fut = {}, _rt43Stale = {}, _rt43Bad = {}, _rt43Ovn = {}, _rt43Ext = {};
let _rt43Sek = null;
try { ["gold-api-spot-metal", "twelve-spot", "dxy-computed"].forEach(x => RT_SRC.add(x)); } catch (e) {}
const _rt43Ms = t => { t = Number(t) || 0; return t > 0 && t < 1e10 ? t * 1000 : t; };
function _rt43SpotFresh(tk) { const s = _rt43Spot[tk]; return !!s && Date.now() - s.at < (tk === "DXY" ? 60_000 : RT43_ENERGY[tk] ? 20 * 60_000 : 180_000); }
function _rt43KeepFut(tk, p, c, ts) { if (p > 0) _rt43Fut[tk] = { p, c: Number(c), ts: _rt43Ms(ts), at: Date.now() }; }
function _rt43ApplySpot(tk, p, ts, src, name, pctHint) {
  if (!(p > 0)) return;
  if (!_rt43Fut[tk] && P[tk] && P[tk].p > 0 && !RT_SRC.has(liveQuoteSrc[tk])) _rt43KeepFut(tk, P[tk].p, P[tk].c, liveQuoteTs[tk]);
  const f = _rt43Fut[tk];
  if (f && f.p > 0 && Math.abs(p / f.p - 1) > 0.08) { _rt43Bad[tk] = true; return; } // unit or contract mismatch: keep futures
  const pct = pctHint != null && isFinite(pctHint) ? pctHint : f && isFinite(f.c) && Date.now() - f.at < 6 * 3600_000 ? f.c : null;
  _rt43Spot[tk] = { at: Date.now() };
  if (liveQuoteSrc[tk] !== src) liveQuoteTs[tk] = 0;
  _rtApply(tk, p, { src, ts: _rt43Ms(ts), proxy: true, name, prev: pct != null ? p / (1 + pct / 100) : null, repaint: true });
}
async function _rt43MetalPoll() {
  if (document.hidden) return;
  await Promise.all(Object.entries(RT43_METAL).map(async ([tk, [sym, nm]]) => {
    if (_rt43Bad[tk]) return;
    try { const r = await fetch(`https://api.gold-api.com/price/${sym}`, { cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(8000) });
      if (!r.ok) return; const j = await r.json(); const ts = Date.parse(j && j.updatedAt);
      if (ts > 0 && Date.now() - ts < 10 * 60_000) _rt43ApplySpot(tk, Number(j.price), ts, "gold-api-spot-metal", `${nm} (gold-api.com)`); } catch (e) {}
  }));
}
async function _rt43EnergyPoll() {
  if (document.hidden) return;
  try { const r = await fetch("/api/spot-energy", { signal: AbortSignal.timeout(9000) }); if (!r.ok) return; const j = await r.json();
    if (!j || !j.available) return;
    ["WTI", "BRENT"].forEach(tk => { const q = j[tk]; if (q && q.p > 0 && !q.stale) _rt43ApplySpot(tk, q.p, q.ts, "twelve-spot", q.name || `${tk} spot`, q.prev > 0 ? (q.p - q.prev) / q.prev * 100 : null); });
  } catch (e) {}
}
const RT43_DXY = [["EURUSD", -0.576], ["USDJPY", 0.136], ["GBPUSD", -0.119], ["USDCAD", 0.091], ["USDSEK", 0.042], ["USDCHF", 0.036]];
async function _rt43SekPoll() {
  if (document.hidden) return;
  try { const r = await fetch("/api/yahoo-quote?symbols=SEK%3DX", { signal: AbortSignal.timeout(8000) }); const j = await r.json(); const q = j && j["SEK=X"];
    if (q && q.p > 0 && !q.stale && !/last-good/.test(String(q.source || ""))) _rt43Sek = { p: q.p, prev: q.prev > 0 ? q.prev : null, ts: _rt43Ms(q.ts) || Date.now(), at: Date.now() }; } catch (e) {}
}
function _rt43Dxy() {
  try {
    let v = 50.14348112, pv = 50.14348112, tsMin = Infinity;
    for (const [tk, e] of RT43_DXY) {
      let p, prev, ts;
      if (tk === "USDSEK") { if (!_rt43Sek || Date.now() - _rt43Sek.at > 10 * 60_000) return; ({ p, prev, ts } = _rt43Sek); }
      else { if (!hasSyncedQuote(tk) || !_rt18MarketOpen(tk) || _rt43Stale[tk]) return; p = P[tk].p; prev = BASE[tk] && BASE[tk].p > 0 ? BASE[tk].p : null; ts = _rt43Ms(liveQuoteTs[tk]); }
      if (!(p > 0) || !(Date.now() - ts < 10 * 60_000)) return;
      v *= p ** e; pv = pv && prev > 0 ? pv * prev ** e : null; tsMin = Math.min(tsMin, ts);
    }
    _rt43Spot.DXY = { at: Date.now() };
    if (liveQuoteSrc.DXY !== "dxy-computed") liveQuoteTs.DXY = 0;
    _rtApply("DXY", +v.toFixed(3), { src: "dxy-computed", ts: tsMin, prev: pv, proxy: true, name: "US Dollar Index (computed from live FX)", repaint: true });
  } catch (e) {}
}
{
  const _ra0 = _rtApply;
  _rtApply = function (tk, p, o) {
    try { const src = o && o.src;
      if (_rt43SpotFresh(tk) && !/^(gold-api-spot-metal|twelve-spot|dxy-computed)$/.test(src || "") && !(tk === "XAU")) { if (tk !== "DXY") _rt43KeepFut(tk, p, o && o.prev > 0 ? (p - o.prev) / o.prev * 100 : NaN, o && o.ts); return false; } } catch (e) {}
    const r = _ra0.apply(this, arguments); if (r) delete _rt43Stale[tk]; return r;
  };
  const _g0 = _rtGuard;
  _rtGuard = function (tk, q, source) {
    try { const src = String((q && q.source) || source || "");
      if (tk === "DXY" && (src === "frankfurter-ecb" || src === "open-exchange-rate-api")) return true; // ECB daily fix is never displayed
      if ((RT43_METAL[tk] || RT43_ENERGY[tk]) && q && q.p > 0 && !/spot/.test(src)) { _rt43KeepFut(tk, q.p, q.c, q.ts); if (_rt43SpotFresh(tk)) return true; }
      if (tk === "DXY" && _rt43SpotFresh("DXY") && src !== "dxy-computed") return true; } catch (e) {}
    return _g0.apply(this, arguments);
  };
  const _a0 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q, source) {
    const r = _a0.apply(this, arguments);
    try { if (r) { if (q && (q.stale === true || /last-good/.test(String(q.source || "")))) _rt43Stale[tk] = Date.now(); else delete _rt43Stale[tk]; } } catch (e) {}
    return r;
  };
  const _q0 = _quoteMeta;
  _quoteMeta = function (tk) {
    const m = _q0.apply(this, arguments);
    try {
      const src = liveQuoteSrc[tk] || "", tsMs = _rt43Ms(liveQuoteTs[tk]), age = tsMs ? Date.now() - tsMs : null;
      if (src === "gold-api-spot-metal") { const ok = age != null && age < 5 * 60_000; return { ...m, asOf: tsMs || m.asOf, status: ok ? "live" : "stale", label: ok ? "SPOT" : "STALE·SPOT", detail: "Spot price from gold-api.com (about every 30s). The COMEX/NYMEX future is a separate line, 10 minutes delayed." }; }
      if (src === "twelve-spot") { const ok = age != null && age < 20 * 60_000; return { ...m, asOf: tsMs || m.asOf, status: ok ? "live" : "stale", label: ok ? "SPOT" : "STALE·SPOT", detail: `Spot price from Twelve Data via the Dispatch server, shared by all visitors and refreshed every few minutes within the free plan (as of ${age != null ? _fmtAge(tsMs) : "—"} ago). The NYMEX/ICE future is a separate line, 10 minutes delayed.` }; }
      if (src === "dxy-computed") return { ...m, asOf: tsMs || m.asOf, status: "live", label: "LIVE FX", detail: "Computed in your browser from six live FX pairs with the ICE weights (EUR, JPY, GBP, CAD, SEK, CHF)." };
      if (src === "dxy-fx-computed") return { ...m, label: m.status === "stale" ? m.label : "FX-COMPUTED", detail: "Computed on the Dispatch server from Yahoo FX pairs with the ICE weights." };
      const closed = m.status === "closed" || /CLOSED/.test(m.label || "");
      if (!closed && (_rt43Stale[tk] || (liveQuoteCached[tk] && age != null && age > 15 * 60_000 && _rt18MarketOpen(tk))))
        return { ...m, status: "stale", label: `STALE · ${age != null ? _fmtAge(tsMs) : "—"}`, detail: "Last good copy (the feed was busy or rate-limited). Not current market data." };
      if (!closed && /=F$/.test(YAHOO_SYMBOLS[tk] || "") && (src === "yahoo" || src === "yahoo-stream") && tk !== "XAU")
        return { ...m, status: "delayed", label: "DELAYED 10m", detail: "CME/ICE futures are delayed 10 minutes at source (Yahoo Finance)." };
    } catch (e) {}
    return m;
  };
  try { const _sl0 = _quoteSourceLabel; _quoteSourceLabel = function (src) { return src === "gold-api-spot-metal" ? "gold-api.com spot" : src === "twelve-spot" ? "Twelve Data spot" : src === "dxy-computed" ? "Computed from live FX" : src === "dxy-fx-computed" ? "FX-computed index" : _sl0.apply(this, arguments); }; } catch (e) {}
  try { const _e0 = _rt39IsEtf; _rt39IsEtf = function (a) { return a && a.cat === "Commodity" ? false : _e0.apply(this, arguments); }; } catch (e) {}
  // FX ticks are sparse: one 2-minute rule decides LIVE for the strip, tape and table alike
  const _tf0 = _rtTickFresh;
  _rtTickFresh = function (tk) { try { const a = A.find(x => x.tk === tk); if (a && a.cat === "FX") return Date.now() - (_rt.lastRecv[tk] || 0) <= 120_000; } catch (e) {} return _tf0.apply(this, arguments); };
  // INTEL headline fit label comes from the same score as the Pulse card
  const _h0 = _rt28Head;
  _rt28Head = function (t) {
    let x = _h0.apply(this, arguments);
    try { const m = typeof x === "string" && x.match(/^([A-Z0-9.\-=^]{1,12}) — (Regime-aligned|Neutral fit|Headwind|Tailwind|Neutral)\b/);
      if (m && A.some(a => a.tk === m[1])) x = x.replace(m[0], `${m[1]} — ${_tickerRegimeFit(m[1], _computeRegimeEngine()).label}`); } catch (e) {}
    return x;
  };
}
// F: overnight index futures and US extended-hours prints (secondary lines; the close stays the headline)
function _rt43ExtOpen() { try { const p = _rt18Parts("America/New_York", new Date()); return !["Sat", "Sun"].includes(p.wd) && ((p.m >= 240 && p.m < 570) || (p.m >= 960 && p.m < 1200)); } catch (e) { return false; } }
function _rt43ExtTick(tks, d) { if (!_rt43ExtOpen() || !(d.price > 0)) return; const p = _rt18Parts("America/New_York", new Date()); const lbl = p.m < 570 ? "Pre-market" : "After hours"; tks.forEach(tk => { _rt43Ext[tk] = { p: d.price, ts: _rt43Ms(d.time), lbl, at: Date.now() }; }); }
async function _rt43OvnPoll() {
  if (document.hidden || _usRegularOpen() || !_rt18MarketOpen("WTI")) return;
  try { const r = await fetch("/api/yahoo-quote?symbols=" + encodeURIComponent("ES=F,YM=F"), { signal: AbortSignal.timeout(8000) }); const j = await r.json();
    [["SPX", "ES=F", "S&P 500 futures"], ["DJIA", "YM=F", "Dow futures"]].forEach(([tk, s, nm]) => { const q = j && j[s]; if (q && q.p > 0) _rt43Ovn[tk] = { p: q.p, c: Number(q.c), nm, stale: !!q.stale, at: Date.now() }; }); } catch (e) {}
}
function _rt43N(v) { return Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function _rt43Pct(c) { return isFinite(c) ? ` (${c >= 0 ? "+" : ""}${c.toFixed(2)}%)` : ""; }
function _rt43SubText(tk) {
  const f = _rt43Fut[tk];
  if (tk !== "DXY" && _rt43SpotFresh(tk) && f && Date.now() - f.at < 30 * 60_000) return `Futures ${_rt43N(f.p)}${_rt43Pct(f.c)} · delayed 10 min`;
  if (tk === "DXY" && liveQuoteSrc.DXY === "dxy-computed") return "Computed from 6 live FX pairs · ICE weights";
  const o = _rt43Ovn[tk]; if (o && !_usRegularOpen() && Date.now() - o.at < 10 * 60_000) return `${o.nm} ${_rt43N(o.p)}${_rt43Pct(o.c)} · overnight, delayed 10 min${o.stale ? " · stale" : ""}`;
  const x = _rt43Ext[tk]; if (x && _rt43ExtOpen() && Date.now() - x.at < 30 * 60_000 && P[tk] && P[tk].p > 0) return `${x.lbl} ${_rt43N(x.p)}${_rt43Pct((x.p - P[tk].p) / P[tk].p * 100)} · ${x.lbl === "Pre-market" ? "pre-market" : "after hours"}`;
  return "";
}
setInterval(() => { try {
  const ut = new URLSearchParams(location.search).get("t");
  const tk = (IS_DESKTOP() ? (typeof termSelTk !== "undefined" && termSelTk) : (typeof selTk !== "undefined" && selTk)) || (ut && A.some(a => a.tk === ut.toUpperCase()) ? ut.toUpperCase() : null);
  document.querySelectorAll(".rt43-sub").forEach(e => { if (e.dataset.tk !== tk || !e.isConnected) e.remove(); });
  if (IS_DESKTOP() && typeof termSelTk !== "undefined" && termSelTk) document.querySelectorAll("#p2body .asof-tag.asof-na").forEach(e => { const h = asOfTag(termSelTk); if (h && !/asof-na/.test(h)) e.outerHTML = h; }); // cold-load tag catches up with the price
  document.querySelectorAll(".rt43-feed").forEach(e => { const t = e.dataset.tk, d = fp(t); const lbl = (d.status !== "unavailable" && _rt20LastClose(t)) ? "CLOSED" : d.status === "unavailable" ? "NO SYNC" : d.status === "live" ? "LIVE" : d.status === "stale" ? "STALE" : d.status === "cached" ? "CACHED" : d.status === "proxy" ? "PROXY" : "DELAYED";
    const live = lbl === "LIVE", txt2 = (live ? "● " : "◌ ") + lbl; if (e.textContent !== txt2) { e.textContent = txt2; e.style.background = live ? "var(--gnG)" : "var(--b3)"; e.style.color = live ? "var(--gn)" : "var(--t3)"; } });
  if (!tk) return;
  const txt = _rt43SubText(tk);
  let el = [...document.querySelectorAll(".rt43-sub")].find(e => e.dataset.tk === tk);
  if (!txt) { if (el) el.remove(); return; }
  if (!el) {
    const px = String(fp(tk).p); if (px === "—") return;
    const bare = px.replace("\u2063", ""), num = Number(bare.replace(/[^0-9.]/g, "")), loc = isFinite(num) && num > 0 ? num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : bare, want = new Set([px, bare, "$" + bare, loc, "$" + loc]);
    const cand = [...document.querySelectorAll("div,span,strong")].filter(e => e.childElementCount === 0 && want.has(e.textContent.trim()) && e.offsetParent !== null);
    if (!cand.length) return;
    const t = cand.sort((a, b) => parseFloat(getComputedStyle(b).fontSize) - parseFloat(getComputedStyle(a).fontSize))[0];
    el = document.createElement("div"); el.className = "rt43-sub"; el.dataset.tk = tk;
    el.style.cssText = "font-size:11px;line-height:1.3;color:var(--t2);font-family:var(--mn);margin-top:2px;white-space:normal";
    t.insertAdjacentElement("afterend", el);
  }
  if (el.textContent !== txt) el.textContent = txt;
} catch (e) {} }, 1500);
setTimeout(() => { _rt43MetalPoll(); _rt43EnergyPoll(); _rt43SekPoll(); _rt43OvnPoll(); }, 2500);
setInterval(_rt43MetalPoll, 30_000);
setInterval(_rt43EnergyPoll, 60_000);
setInterval(_rt43SekPoll, 60_000);
setInterval(_rt43OvnPoll, 60_000);
setInterval(_rt43Dxy, 2000);
'''
R('rt43 block', '// ── rt42 ──\n', BLOCK + '// ── rt42 ──\n')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
HX = [('index byok', 'Weekly Gold Playbook and BYOK AI layer. Platform access, not token mark-up.', 'Weekly Gold Playbook, AI Dispatch Brief, Ask research assistant and company statements. No token mark-up. <a href="/pricing">Compare plans</a>'),
      ('index bust', 'app.js?v=chat39', 'app.js?v=chat40')]
for name, old, new in HX:
    if h.count(old) != 1: die(f"'{name}' anchor matched {h.count(old)} times in index.html")
    h = h.replace(old, new)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} app.js edits + {len(HX)} index.html edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
