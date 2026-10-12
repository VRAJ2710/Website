#!/usr/bin/env python3
"""patch_rt39.py: chat35 -> chat36. Stacks on rt38 output (app.js 7f477349). Client + index.html cache bust.
Idempotent phone Compare button; COMPARE A B from header bar and palette; ETF · NYSE Arca label; one live-count
source (_rt39Live) on header, Markets, strip, dashboard, /brief/ and the guest chip; Signals label no longer STALE for
a big move on an open venue; XAU change in Your Book; single-key shortcuts need Alt+Shift; tab title only for the
open stock; TNV Back clears ?t=; news tags must appear in the text; P/E guard accepts quoted peer figures.
Usage: python3 patch_rt39.py [--check] <dir>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt39)' in s: die('rt39 already applied')
if 'REALTIME PRICE LAYER (rt38)' not in s: die('base is not rt38 output')
if 'app.js?v=chat35' not in h: die('index.html is not chat35')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt38)', '// REALTIME PRICE LAYER (rt39)')
R('compare idempotent', 'document.querySelectorAll(".rt26-back").forEach(b => {\n    if (!t || b.nextElementSibling && b.nextElementSibling.classList.contains("rt38-cmp")) return;',
  'document.querySelectorAll(".rt26-back:not(.rt38-cmp)").forEach(b => {\n    if (!t || (b.parentElement && b.parentElement.querySelector(".rt38-cmp")) || document.querySelectorAll(".rt38-cmp").length) return;')
R('dyn back', 'onclick="_dynTk=null;_dynData=null;_rt26Back()"', 'onclick="_rt39DynBack()"')
R('signals label', '    status: stale ? "STALE" : meta.label,', '    status: unavailable ? "UNAVAILABLE" : meta.status === "stale" ? (_rt18MarketOpen(tk) ? "STALE" : "CLOSED") : meta.label,')
R('focus key', "if(!inInput&&e.key.toLowerCase()==='f'&&!e.ctrlKey&&!e.metaKey)", "if(!inInput&&e.code==='KeyF'&&e.altKey&&e.shiftKey&&!e.ctrlKey&&!e.metaKey)")
R('letter keys', "if(!e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.shiftKey&&e.key.length===1&&!onControl){\n      const k=e.key.toLowerCase();",
  "if(e.altKey&&e.shiftKey&&!e.ctrlKey&&!e.metaKey&&!onControl&&/^Key[A-Z]$/.test(e.code||\"\")&&document.hasFocus()){\n      const k=e.code.slice(3).toLowerCase();")
R('title only open stock', 'try { if (tk) document.title = ', 'try { if (tk && (tk === (typeof termSelTk !== "undefined" ? termSelTk : null) || tk === (typeof selTk !== "undefined" ? selTk : null))) document.title = ')
R('etf header', '${a.cat.toUpperCase()} · ${a.ex} · ${feedLbl}', '${_rt39Cat(a).toUpperCase()} · ${_rt39Ex(a)} · ${feedLbl}', 2)
R('etf badge', 'bd(/\\bETF\\b/.test(a.nm||"")?"ETF":a.cat,catBd(a.cat))', 'bd(_rt39Cat(a),catBd(a.cat))', 2)
R('guest chip', ':`<span class="htec-chip htec-chip-muted" title="Free market feeds may be delayed or unavailable">PRICES MAY BE DELAYED</span>`;', ':`<span class="htec-chip htec-chip-muted" title="Free market feeds; some prices are delayed">${_escHtml(_rt37Sum())}</span>`;')
R('strip live', '${_c.priced?`${_c.priced} prices · ${_rt37Upd(priceLastFetch&&priceLastFetch.getTime())}`:"Prices loading"}', '${_c.priced?`${_c.priced} prices · ${_c.live} live · ${_rt37Upd(priceLastFetch&&priceLastFetch.getTime())}`:"Prices loading"}')
R('brief live', '<div class="ns-cell"><span class="ns-lbl">PRICED</span><span class="ns-val ns-live">${_rt37Count().priced}</span></div>', '<div class="ns-cell"><span class="ns-lbl">PRICED</span><span class="ns-val ns-live">${_rt37Count().priced}</span></div>\n    <div class="ns-cell"><span class="ns-lbl">LIVE</span><span class="ns-val ns-live">${_rt37Count().live}</span></div>')
R('book xau', '    out.push({ tk, ch, px: hasSyncedQuote(tk) ? fp(tk).p : "…" });', '    out.push({ tk, ch: ch != null ? ch : _rt39Chg(tk), px: hasSyncedQuote(tk) ? fp(tk).p : "…" });')
BLOCK = r'''// ── rt39 ──
function _rt39Live(tk) {
  try {
    if (!hasSyncedQuote(tk) || !_rt18MarketOpen(tk)) return false;
    const m = _quoteMeta(tk); if (m.status === "live") return true;
    const ts = Number(liveQuoteTs[tk]) || 0; return ts > 0 && Date.now() - (ts < 1e10 ? ts * 1000 : ts) < 20 * 60000;
  } catch (e) { return false; }
}
_rt37Count = function () {
  let priced = 0, live = 0;
  try { A.forEach(a => { if (!hasSyncedQuote(a.tk)) return; priced++; if (_rt39Live(a.tk)) live++; }); } catch (e) {}
  return { priced, live, total: A.length, open: _usRegularOpen() };
};
try {
  quoteStatusSummary = function (tickers) {
    const c = _rt37Count();
    if (!c.priced) return "prices loading";
    if (!tickers) return `${c.priced} prices · ${c.live} live`;
    const list = [...new Set(tickers.filter(Boolean))];
    const p = list.filter(t => hasSyncedQuote(t)).length;
    return `${p} prices · ${c.live} live`;
  };
} catch (e) {}
const RT39_ARCA = new Set(["SPY", "IWM", "DIA", "GLD", "SLV", "TLT", "ARKK", "XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "EEM", "EFA", "HYG", "LQD", "USO", "UNG", "VTI", "VOO", "GDX", "SMH", "KRE", "XBI"]);
function _rt39IsEtf(a) { return !!(a && (/\bETF\b|\bTrust\b.*\bSPDR\b|\biShares\b|\bSPDR\b|\bInvesco QQQ\b/i.test(a.nm || "") || RT39_ARCA.has(a.tk))); }
function _rt39Cat(a) { return _rt39IsEtf(a) ? "ETF" : a.cat; }
function _rt39Ex(a) { return _rt39IsEtf(a) && (a.ex === "NYSE" || RT39_ARCA.has(a.tk)) && a.ex !== "NASDAQ" ? "NYSE Arca" : a.ex; }
function _rt39Chg(tk) {
  try { if (tk === "XAU") { _rt34Gc(); if (_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000 && isFinite(_rt.gcPct.c)) return Number(Number(_rt.gcPct.c).toFixed(2)); } } catch (e) {}
  return null;
}
function _rt39DynBack() {
  _dynTk = null; _dynData = null;
  try { const u = new URL(location.href); if (u.searchParams.has("t")) { u.searchParams.delete("t"); history.replaceState(history.state, "", u.pathname + (u.search || "") + u.hash); } } catch (e) {}
  _rt26Back();
}
{
  const _b0 = _rt26Back;
  _rt26Back = function () {
    const wasDyn = !!_dynTk;
    const r = _b0.apply(this, arguments);
    if (wasDyn) { try { const u = new URL(location.href); if (u.searchParams.has("t")) { u.searchParams.delete("t"); history.replaceState(history.state, "", u.pathname + (u.search || "") + u.hash); } } catch (e) {} }
    return r;
  };
}
// COMPARE A B typed into the header bar or the palette: run before the input's own handlers strip the spaces
document.addEventListener("keydown", e => {
  try {
    if (e.key !== "Enter") return;
    const el = e.target; if (!el || el.tagName !== "INPUT") return;
    const v = String(el.value || "").trim();
    if (!/^compare\s+\S+/i.test(v)) return;
    e.preventDefault(); e.stopImmediatePropagation();
    el.value = ""; try { document.getElementById("cmdAc")?.classList.remove("show"); } catch (x) {}
    try { if (typeof closeSearch === "function") closeSearch(); } catch (x) {}
    lookupTicker(v);
  } catch (x) {}
}, true);
// news tags: a ticker tag needs the ticker or the company name in the text; crypto tag needs a crypto word
{
  const _tg0 = _tagNewsHeadline;
  _tagNewsHeadline = function (text) {
    const r = _tg0.apply(this, arguments); const t = String(text || "");
    if (!Array.isArray(r)) return r;
    return r.filter(tk => {
      try {
        const a = A.find(x => x.tk === tk) || {};
        if (new RegExp(`(^|[^A-Za-z0-9])${tk.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^A-Za-z0-9]|$)`).test(t)) return true;
        const stem = String(a.nm || "").replace(/[,.]?\s+(Inc|Corp(oration)?|Technology|Technologies|Holdings|Group|Company|Co|plc|Ltd|Platforms|Industrial Average|Index|Composite|Class [A-Z])\b.*$/i, "").trim();
        return stem.length >= 3 && new RegExp(`\\b${stem.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i").test(t);
      } catch (e) { return true; }
    });
  };
  const _dt0 = detectTag;
  detectTag = function (text) { const r = _dt0.apply(this, arguments); if (r === "Crypto" && !/bitcoin|crypto|ether|\bBTC\b|\bETH\b|solana|token|blockchain|stablecoin|coinbase|binance|\bXRP\b|dogecoin/i.test(String(text || ""))) return "Stocks"; return r; };
}
{
  const _st0 = _rt38St;
  _rt38St = function (st, tks) { const o = _st0.apply(this, arguments); try { if (o && /^(informative|analysis complete|complete|done)$/i.test(String(o.verdict || "").trim())) o.verdict = ""; } catch (e) {} return o; };
  const _rp0 = _rt37Reply;
  _rt37Reply = function (t, tks) {
    let s = String(t || "");
    try { if (tks && tks.length && !tks.some(x => RT38_GOLD.test(x))) s = s.replace(/^\s*Live:[^\n]*(\n+\s*Windows:[^\n]*)?\n*/i, "").replace(/^\s*Windows:[^\n]*\n*/im, ""); } catch (e) {}
    return _rp0.call(this, s, tks);
  };
}
// P/E guard: a quoted P/E or market cap is kept when it matches ANY ticker the desk has live figures for (peers)
_rt33Guard = function (s, tk) {
  if (typeof s !== "string" || !/P\/E|market cap/i.test(s)) return s;
  const vals = []; try { Object.keys(_finCache).forEach(k => { const v = _rt33Val(k); if (v) vals.push(v); }); } catch (e) {}
  if (!vals.length) return s;
  const near = (n, live, tol) => live != null && isFinite(live) && live > 0 && Math.abs(n - live) / live <= tol;
  const keep = p => {
    for (const m of p.matchAll(/\bP\/E(?:\s+ratio)?(?:\s+(?:of|at|is|near|around|about|~))*\s*~?(\d+(?:\.\d+)?)\s*x/gi)) { const n = +m[1]; if (!vals.some(v => near(n, v.pe, 0.12) || near(n, v.forwardPe, 0.12))) return false; }
    for (const m of p.matchAll(/market\s+cap(?:italisation|italization)?(?:\s+(?:of|at|is|near|around|about|approximately|roughly|~))*\s*~?\$?\s*(\d+(?:\.\d+)?)\s*(T|B|M|trillion|billion|million)\b/gi)) { const u = m[2][0].toUpperCase(), n = +m[1] * (u === "T" ? 1e12 : u === "B" ? 1e9 : 1e6); if (!vals.some(v => near(n, v.marketCap, 0.15))) return false; }
    return true;
  };
  const parts = _rt28Split(s), out = parts.filter(keep);
  return out.length === parts.length ? s : out.join(" ");
};
'''
R('markets live', "${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices`;", "${tickers.filter(a => hasSyncedQuote(a.tk)).length} prices · ${_rt37Count().live} live`;")
R('rt39 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
h = h.replace('app.js?v=chat35', 'app.js?v=chat36')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
