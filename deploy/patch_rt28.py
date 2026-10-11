#!/usr/bin/env python3
"""patch_rt28.py — chat25 -> chat26. Stacks on rt27 output (t27 = app.js 57a2792c). Client + index.html cache bust.
Usage: python3 patch_rt28.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt28)' in s: die('rt28 already applied')
if 'REALTIME PRICE LAYER (rt27)' not in s: die('base is not rt27 output')
if 'app.js?v=chat25' not in h: die('index.html is not chat25')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt27)', '// REALTIME PRICE LAYER (rt28)')
# 1+2. what the AI receives: explicit signed % units, live F/G only, focus ticker quote; old cached AI dropped
R('ctx focus', '  if (surface === "ticker" && tk) parts.push(`Focus ticker: ${tk}`);', '  if (surface === "ticker" && tk) parts.push(_rt28Focus(tk));\n  parts.push(_rt28Units());')
R('ctx brief fg', '    if (_brief.summary) parts.push(`Brief summary: ${_brief.summary}`);', '    if (_brief.summary) parts.push(`Brief summary: ${String(_brief.summary).replace(/\\s*Fear\\/Greed[^.]*\\.?/gi, " ").trim()}`);')
R('ctx fg live', '    `Fear/Greed: ${fg.label} (${fg.score != null ? fg.score : "—"}/100)`,\n  ];', '    `Fear/Greed (live, computed now — the only valid value): ${fg.label} (${fg.score != null ? fg.score : "—"}/100)`,\n  ];')
R('si cache key', '  return `td_si_${surface}_${tk || ""}_${new Date().toISOString().split("T")[0]}`;', '  return `td_si2_${surface}_${tk || ""}_${new Date().toISOString().split("T")[0]}`;')
# render-time guard on every AI headline / insight path
R('render head', '_rt26Copy(intel.headline)', '_rt28Head(intel.headline)', 2)
R('render ins', '_rt26Sent(_rt26Copy(intel.insight || ""), 420)', '_rt26Sent(_rt28Clean(intel.insight || ""), 420)', 2)
R('clean ai', '  if (typeof c.insight === "string") c.insight = _rt27Ins(c.insight);', '  if (typeof c.insight === "string") c.insight = _rt28Clean(c.insight);\n  if (typeof c.headline === "string") c.headline = _rt28Head(c.headline);')
R('clean anoms', '  if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => typeof a === "string" ? _rt27Ins(a) : a)', '  if (Array.isArray(c.anomalies)) c.anomalies = c.anomalies.map(a => typeof a === "string" ? _rt28Clean(a) : a)')
# 3. INTEL repaints on ticker change
R('repaint desk', '    _rt27Url(tk);\n', '    _rt27Url(tk);\n    _rt28Repaint();\n')
R('repaint phone', 'renderMain();renderNav();document.querySelector(".main")?.scrollTo(0,0);', 'renderMain();renderNav();document.querySelector(".main")?.scrollTo(0,0);_rt28Repaint();')
# 4. PULSE news: strict matching, full titles, hidden when none
R('tk news', '      _rt27TkNews(tk).forEach(m => anomalies.push({ t: "news", m }));', '      _rt28TkNews(tk).forEach(m => anomalies.push({ t: "news", m }));')
# 6. typo lookup: hard cap + not-found
R('lookup cap', '    const [priceRes,searchRes,chartData]=await Promise.allSettled([\n      fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSym)}`,{signal:AbortSignal.timeout(8000)}),\n      fetch(`/api/search?q=${encodeURIComponent(sym)}`,{signal:AbortSignal.timeout(5000)}),\n      fetchYahooIntraday(yhSym),\n    ]);',
  '    const [priceRes,searchRes,chartData]=await Promise.allSettled([\n      fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSym)}`,{signal:AbortSignal.timeout(8000)}),\n      fetch(`/api/search?q=${encodeURIComponent(sym)}`,{signal:AbortSignal.timeout(5000)}),\n      Promise.race([fetchYahooIntraday(yhSym),new Promise(r=>setTimeout(()=>r(null),9000))]),\n    ]);\n    if(seq!==_lookupSeq)return;')
# 8. chart sized after layout
R('chart layout', '    ro.observe(container);', '    ro.observe(container);\n    requestAnimationFrame(() => requestAnimationFrame(() => { try { if (chartEl.isConnected && chartEl.clientWidth) { chart.applyOptions({ width: chartEl.clientWidth }); chart.timeScale().fitContent(); } } catch (e) {} }));')
# 8+9. ?t= lives on /markets/ only; deep link opens as soon as the shell exists
R('url path', '    u.searchParams.set("t", tk);\n    history.pushState(', '    u.searchParams.set("t", tk); u.pathname = "/markets/";\n    history.pushState(')
R('url guard', '    const t = new URLSearchParams(location.search).get("t"); if (!t) return;', '    const t = new URLSearchParams(location.search).get("t"); if (!t) return;\n    if (!/^\\/markets\\/?$/.test(location.pathname)) { const u = new URL(location.href); u.searchParams.delete("t"); history.replaceState(history.state, "", u.pathname + u.search + u.hash); return; }')
R('url boot', 'window.addEventListener("load", () => { setTimeout(_rt27OpenFromUrl, 1200); });', '_rt28DeepBoot();')
# 10. one score: palette badge = desk score shown on the stock view
R('fit badge', '  const f = _tickerRegimeFit(tk, _computeRegimeEngine());\n  const c = f.score >= 68', '  const f0 = _tickerRegimeFit(tk, _computeRegimeEngine()), a0 = A.find(x => x.tk === tk);\n  const f = a0 && a0.sc != null ? { score: a0.sc, label: `Desk score · ${f0.label}` } : f0;\n  const c = f.score >= 68')
# 11. brief survives Back
R('brief keep', '  if (_brief?.headline) {\n    // houseView is the short stance', '  _rt28BriefKeep();\n  if (_brief?.headline) {\n    // houseView is the short stance')
BLOCK = r"""// ── rt28: AI number guard, live F/G, strict ticker news, deep links ──
function _rt28Pct(v) { return v == null || !isFinite(v) ? null : `${v >= 0 ? "+" : ""}${Number(v).toFixed(2)}%`; }
function _rt28Focus(tk) {
  const a = A.find(x => x.tk === tk), px = (typeof livePx === "function") ? livePx(tk) : null, ch = liveChg(tk);
  let day = "today"; try { day = _rt26Day(tk); } catch (e) {}
  return `Focus ticker: ${tk}${a ? ` (${a.nm})` : ""}${px != null ? ` · price $${px}` : ""}${ch != null ? ` · change ${day === "today" ? "today" : "on " + day}: ${_rt28Pct(ch)}` : " · change: unavailable"}${a && a.sc != null ? ` · desk score ${a.sc}/100` : ""}`;
}
function _rt28Units() {
  return "Units: every change above is already a percentage with its sign (e.g. -0.52% means minus zero point five two percent). Quote percentages exactly as given, never rescale them, and do not invent percentages that are not listed.";
}
function _rt28Allowed() {
  const set = [];
  try { A.forEach(a => { const c = liveChg(a.tk); if (c != null) set.push(Math.abs(c)); }); } catch (e) {}
  try { const ctx = _siteIntelContext(_siteIntel.surface || "pulse", _rt27CurTk()); (ctx.match(/-?\d+(?:\.\d+)?(?=\s*%)/g) || []).forEach(n => set.push(Math.abs(Number(n)))); } catch (e) {}
  return set;
}
/** Drop sentences whose percentages match no live / supplied value, and Fear/Greed sentences that disagree with the live gauge. */
function _rt28Clean(t) {
  let s = _rt26Copy(String(t || "")).replace(/\s+/g, " ").trim();
  if (/^[a-z,;:)…]/.test(s) || /^\.\.\./.test(s)) { const i = s.search(/[.!?]\s+[A-Z]/); s = i >= 0 ? s.slice(i + 1).trim() : ""; }
  if (!s) return s;
  let allowed = null;
  let fg = null; try { fg = calcFearGreed(); } catch (e) {}
  const liveWord = fg && fg.label ? String(fg.label).toLowerCase().replace(/^extreme\s+/, "") : "";
  const parts = _rt28Split(s);
  return parts.filter(p => {
    const pcts = p.match(/-?\d+(?:\.\d+)?(?=\s*%)/g);
    if (pcts) {
      allowed = allowed || _rt28Allowed();
      if (!pcts.every(n => { const v = Math.abs(Number(n)); return allowed.some(a => Math.abs(a - v) <= Math.max(0.06, a * 0.02)); })) return false;
    }
    if (/fear|greed/i.test(p)) {
      const n = (p.match(/\b(\d{1,3})\s*(?:\/\s*100)?\b/) || [])[1];
      if (n != null) { if (!(fg && fg.score != null && Math.abs(Number(n) - fg.score) <= 2)) return false; }
      else { const w = (p.match(/\b(extreme\s+)?(fear|greed|greedy|neutral)\b/i) || [])[2]; if (w && liveWord && !liveWord.startsWith(w.toLowerCase().replace("greedy", "greed"))) return false; }
    }
    return true;
  }).join(" ").trim();
}
function _rt28Split(s) { return String(s || "").split(/(?<=[.!?])\s+(?=["'(\[]?[A-Z0-9$])/).map(p => p.trim()).filter(Boolean); }
function _rt28Head(t) {
  if (typeof t !== "string") return t;
  let x = _rt27Head(t);
  const m = x.match(/^market\s+(?:update|analysis|sentiment|overview|context|insights?)\b.*?\b(?:on|for)\s+(?:ticker\s+)?([A-Z][A-Z0-9.\-]{0,9})\b/i);
  if (m) return `Market regime: ${m[1].toUpperCase()}`;
  return x;
}
function _rt28Repaint() {
  setTimeout(() => { try { _intelBarSig = ""; _paintSiteIntelBar(); } catch (e) {} }, 0);
}
function _rt28TkNews(tk) {
  const out = [], seen = new Set();
  try {
    const a = A.find(x => x.tk === tk);
    const nm = a && a.nm ? String(a.nm).replace(/\s*\(.*?\)\s*/g, " ").replace(/[,.]?\s+(inc|corp|corporation|co|ltd|plc|holdings|group|adr|class [a-z])\.?$/i, "").trim() : "";
    const esc = v => v.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const reTk = tk.length >= 2 ? new RegExp(`(^|[^A-Za-z0-9$])\\$?${esc(tk)}(?![A-Za-z0-9])`) : new RegExp(`\\$${esc(tk)}(?![A-Za-z0-9])`);
    const reNm = nm.length >= 3 ? new RegExp(`(^|\\W)${esc(nm)}(?!\\w)`, "i") : null;
    NEWS.forEach(n => {
      if (out.length >= 2) return;
      const x = String((n && n.x) || "").replace(/\s+/g, " ").trim();
      if (!x || seen.has(x.toLowerCase()) || /(…|\.\.\.)$/.test(x)) return;
      if (reTk.test(x) || (reNm && reNm.test(x))) { seen.add(x.toLowerCase()); out.push(x); }
    });
  } catch (e) {}
  return out;
}
function _rt28DeepBoot() {
  let n = 0;
  const go = () => {
    n++;
    const ready = typeof A !== "undefined" && A.length && document.getElementById(IS_DESKTOP() ? "p2body" : "main");
    if (ready) { _rt27OpenFromUrl(); return; }
    if (n < 60) setTimeout(go, 100);
  };
  setTimeout(go, 0);
}
function _rt28BriefKeep() {
  try {
    const k = "rt28_brief", day = new Date().toISOString().slice(0, 10);
    if (_brief && _brief.headline) { sessionStorage.setItem(k, JSON.stringify({ day, b: _brief })); return; }
    const c = JSON.parse(sessionStorage.getItem(k) || "null");
    if (c && c.day === day && c.b && c.b.headline) _brief = c.b;
  } catch (e) {}
}
"""
R('sent split', '  const parts = s.match(/[^.!?]+[.!?]+(?=\\s|$)/g) || [s];', '  const parts = _rt28Split(s).length ? _rt28Split(s) : [s];')
R('rt28 block', 'const _rt23Ch = {};', BLOCK + 'const _rt23Ch = {};')
for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
if h.count('app.js?v=chat25') != 1: die('index cache-bust anchor')
h = h.replace('app.js?v=chat25', 'app.js?v=chat26')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + index; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
