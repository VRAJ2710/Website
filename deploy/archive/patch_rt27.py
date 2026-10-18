#!/usr/bin/env python3
"""patch_rt27.py — chat24 -> chat25. Stacks on rt26 output (t26 = app.js 05e42d8a). Client + index.html cache bust.
Usage: python3 patch_rt27.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt27)' in s: die('rt27 already applied')
if 'REALTIME PRICE LAYER (rt26)' not in s: die('base is not rt26 output')
if 'app.js?v=chat24' not in h: die('index.html is not chat24')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt26)', '// REALTIME PRICE LAYER (rt27)')
# 1+2. intelligence: ticker-tagged responses, stale ones never rendered, AI text cleaned
R('ai cache tk', '        _siteIntel.ai = c.intel;\n', '        _siteIntel.ai = _rt27CleanAi(c.intel);\n        _siteIntel.tk = tk;\n')
R('ai fetch tk', '    _siteIntel.ai = data.intel;\n', '    _siteIntel.ai = _rt27CleanAi(data.intel);\n    _siteIntel.tk = tk;\n')
R('ai merge guard', '  const ai = (_siteIntel.ai && _siteIntel.surface === surface) ? _siteIntel.ai : null;',
  '  const ai = (_siteIntel.ai && _siteIntel.surface === surface && (surface !== "ticker" || (_siteIntel.tk || "") === _rt27CurTk(extra))) ? _siteIntel.ai : null;')
# 4. PULSE news: ticker-relevant only, full titles
R('news full', 'highNews.forEach(n => anomalies.push({ t: "news", m: _rt16Clip(n.x, 72) }));', 'highNews.forEach(n => anomalies.push({ t: "news", m: String(n.x || "").trim() }));')
R('ticker news', '      actions.push({ label: `Lens on ${tk}`, type: "lens", value: tk });\n      if (comRes) {',
  '      actions.push({ label: `Lens on ${tk}`, type: "lens", value: tk });\n      for (let i = anomalies.length - 1; i >= 0; i--) if (anomalies[i].t === "news") anomalies.splice(i, 1);\n      _rt27TkNews(tk).forEach(m => anomalies.push({ t: "news", m }));\n      if (comRes) {')
# 3. crypto: fresher wins, stale retried, one age format
R('cg fresher', '_cryptoMktData=Array.isArray(data)?data:null;', '{const nd=Array.isArray(data)?data:null,nl=_rt26CgRowsTs(nd),ol=_rt26CgRowsTs(_cryptoMktData);if(nd&&!(ol&&nl&&nl<ol))_cryptoMktData=nd;}')
R('cg retry', "  if(_cryptoError){clearTimeout(window.__cgRetry);window.__cgRetry=setTimeout(()=>{if(pg==='crypto')fetchCryptoMarket();},60000);}",
  "  if(_cryptoError){clearTimeout(window.__cgRetry);window.__cgRetry=setTimeout(()=>{if(pg==='crypto')fetchCryptoMarket();},60000);}\n  else if(_cryptoAsOf&&(window.__rt27CgN=(window.__rt27CgN||0)+1)<=5){clearTimeout(window.__cgRetry);window.__cgRetry=setTimeout(()=>{if(pg==='crypto'||document.getElementById('cryptoOv'))fetchCryptoMarket();},60000);}")
R('ago fmt', '  return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.round(s / 60)}m ago` : _rt20AgeLbl(ts);',
  '  return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.round(s / 60)}m ago` : s < 86400 ? `${Math.round(s / 3600)}h ago` : `${Math.round(s / 86400)}d ago`;')
R('cg stale fmt', '? `CoinGecko table delayed \\u00b7 as of ${_rt20AgeLbl(asOf.getTime())}`', '? `CoinGecko table delayed \\u00b7 updated ${_rt26Ago(asOf.getTime())}`')
# 5. phone price line names the session day when closed
R('phone day', '(chAn==null?"—":`${chSign}${d.chg} (${chSign}${d.c}%)`)', '(chAn==null?"—":`${chSign}${d.chg} (${chSign}${d.c}%)${_rt26Day(a.tk)==="today"?"":" "+_rt26Day(a.tk)}`)')
# 6. factor columns: hide each empty one; drop junk items; futures 0.00 rule covers COPPER etc.
R('factor junk', "    const bullish = thWords.filter(", "    const _rt27F = x => String(x || '').replace(/[—\\s.·-]+/g, '').length > 3;\n    const bullish = thWords.filter(_rt27F).filter(")
R('factor junk2', "    const bearish = thWords.filter(", "    const bearish = thWords.filter(_rt27F).filter(")
R('factor grid', '    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--gb)">`;', '    h += `<div style="display:grid;grid-template-columns:${bullish.length && bearish.length ? "1fr 1fr" : "1fr"};gap:1px;background:var(--gb)">`;')
R('factor bull col', '    h += `<div style="background:var(--bg);padding:10px 14px">\n      <div style="font-family:var(--mn);font-size:9px;color:var(--gn)', '    if (bullish.length) h += `<div style="background:var(--bg);padding:10px 14px">\n      <div style="font-family:var(--mn);font-size:9px;color:var(--gn)')
R('factor bear col', '    h += `<div style="background:var(--bg);padding:10px 14px">\n      <div style="font-family:var(--mn);font-size:9px;color:var(--rd)', '    if (bearish.length) h += `<div style="background:var(--bg);padding:10px 14px">\n      <div style="font-family:var(--mn);font-size:9px;color:var(--rd)')
R('fut zero', '(tk === "WTI" || tk === "NG" || tk === "SLV")', '_rt27Fut(tk)', 2)
# polish: desktop Overview populated with PULSE + thesis summary
R('ov pulse', '    if(aTab==="ov"){\n      h += `<div style="padding:8px 16px;border-bottom:1px solid var(--gb);background:var(--b1)">',
  '    if(aTab==="ov"){\n      try { h += `<div style="padding:10px 12px 0">${_renderSiteIntelCard("ticker", { tk: a.tk })}</div>`; } catch (e) {}\n      h += `<div class="ap-thesis">${_rt26Sent(_rt24Th(a), 200)}</div>`;\n      h += `<div style="padding:8px 16px;border-bottom:1px solid var(--gb);background:var(--b1)">')
# polish: stock URL ?t=, back/deep link; desktop overlays give way to the stock view
R('openA desk', '    _onPageIntel("ticker", { tk });\n    _updateSmartDock();', '    _onPageIntel("ticker", { tk });\n    _rt27Url(tk);\n    try { document.querySelectorAll(".term-overlay").forEach(o => _closeA11yDialog(o, false)); } catch (e) {}\n    _updateSmartDock();')
R('openA phone', 'if(selTk!==tk){comRes=null;comLoad=false;comErr="";lensMeta=null;lensIntel=null;}', '_rt27Url(tk);if(selTk!==tk){comRes=null;comLoad=false;comErr="";lensMeta=null;lensIntel=null;}')
BLOCK = r"""// ── rt27 helpers ──
function _rt27CurTk(extra) {
  try { return String((extra && extra.tk) || (IS_DESKTOP() && typeof termSelTk !== "undefined" && termSelTk) || selTk || ""); } catch (e) { return ""; }
}
function _rt27Head(t) {
  if (typeof t !== "string") return t;
  let x = _rt26Copy(t).trim();
  const m = x.match(/^(?:current\s+)?market\s+(?:regime|context|overview|update)(?:\s+update)?\s*(?::|for|-|—)\s*(.+)$/i);
  if (m) {
    let v = m[1].replace(/\s+(highlights|insights|environment|update|overview|snapshot)\s*$/i, "").trim();
    const tk = v.match(/\(([A-Z0-9.\-=^]{1,10})\)\s*$/); if (tk) v = tk[1];
    x = `Market regime: ${v}`;
  }
  return x;
}
function _rt27Ins(t) {
  if (typeof t !== "string") return t;
  let s = t.replace(/\s+/g, " ").trim();
  if (/^[a-z,;:)…]/.test(s) || /^\.\.\./.test(s)) { const i = s.search(/[.!?]\s+[A-Z]/); s = i >= 0 ? s.slice(i + 1).trim() : ""; }
  let live = null; try { const fg = calcFearGreed(); live = fg && fg.score != null ? Number(fg.score) : null; } catch (e) {}
  const parts = (s.match(/[^.!?]+[.!?]*(?=\s|$)/g) || []).map(p => p.trim()).filter(Boolean);
  s = parts.filter(p => { if (!/fear|greed/i.test(p)) return true; const n = (p.match(/\b(\d{1,3})(?:\s*\/\s*100)?\b/) || [])[1]; return n == null || (live != null && Math.abs(Number(n) - live) <= 2); }).join(" ").trim();
  return s;
}
function _rt27CleanAi(o) {
  if (!o || typeof o !== "object") return o;
  const c = Object.assign({}, o);
  if (typeof c.headline === "string") c.headline = _rt27Head(c.headline);
  if (typeof c.insight === "string") c.insight = _rt27Ins(c.insight);
  if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => typeof a === "string" ? _rt27Ins(a) : a).filter(a => a && (typeof a !== "string" || a.length > 3));
  return c;
}
function _rt27TkNews(tk) {
  const out = [], seen = new Set();
  try {
    const keys = [tk]; try { if (YAHOO_SYMBOLS[tk]) keys.push(YAHOO_SYMBOLS[tk]); } catch (e) {}
    const a = A.find(x => x.tk === tk); const nm = a && a.nm ? String(a.nm).split(/[ ,.(]/)[0] : "";
    NEWS.forEach(n => {
      if (out.length >= 2) return;
      const x = String((n && n.x) || "").trim(); if (!x || seen.has(x)) return;
      let hit = false; try { hit = _newsMatchesBook(n, keys); } catch (e) {}
      if (!hit && nm.length >= 4) hit = new RegExp(`\\b${nm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(x);
      if (hit) { seen.add(x); out.push(x); }
    });
  } catch (e) {}
  return out;
}
function _rt27Fut(tk) {
  if (tk === "WTI" || tk === "NG" || tk === "SLV" || tk === "COPPER" || tk === "HG") return true;
  try { const a = A.find(x => x.tk === tk); return !!(a && a.cat === "Commodity" && tk !== "XAU"); } catch (e) { return false; }
}
let _rt27NoPush = false;
function _rt27Url(tk) {
  if (_rt27NoPush) return;
  try {
    const u = new URL(location.href); if (u.searchParams.get("t") === tk) return;
    u.searchParams.set("t", tk);
    history.pushState(Object.assign({}, history.state || {}, { rt27tk: tk }), "", u.pathname + u.search + u.hash);
  } catch (e) {}
}
function _rt27OpenFromUrl() {
  try {
    const t = new URLSearchParams(location.search).get("t"); if (!t) return;
    const tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(t)) || t;
    _rt27NoPush = true; try { openA(tk); } finally { _rt27NoPush = false; }
  } catch (e) { _rt27NoPush = false; }
}
window.addEventListener("popstate", () => { setTimeout(_rt27OpenFromUrl, 0); });
window.addEventListener("load", () => { setTimeout(_rt27OpenFromUrl, 1200); });
"""
R('rt27 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat24') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat24', 'app.js?v=chat25')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
