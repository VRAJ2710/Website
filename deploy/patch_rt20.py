#!/usr/bin/env python3
"""patch_rt20.py — chat18 -> chat19. Stacks on rt19 output (t19). Client-only.
Usage: python3 patch_rt20.py [--check] <dir containing app.js + index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt20)' in s: die('rt20 already applied')
if 'REALTIME PRICE LAYER (rt19)' not in s: die('base is not rt19 output')
if 'app.js?v=chat18' not in h: die('index.html is not chat18')
E = []
def R(name, old, new, count=1): E.append((name, old, new, count))
R('marker', '// REALTIME PRICE LAYER (rt19)', '// REALTIME PRICE LAYER (rt20)')
# 1. closed labels use the real session close
R('closed meta', 'return { ...m, status: "closed", label: "CLOSED", detail: `Market closed — last close ${_rt18CloseLbl(m.asOf)}`, trusted: true };',
  'const ca = _rt20LastClose(tk) || m.asOf;\n  return { ...m, status: "closed", label: "CLOSED", closeAt: ca, detail: `Market closed — last close ${_rt18CloseLbl(ca)}`, trusted: true };')
R('closed asof tag', '· CLOSED · last close ${_rt18CloseLbl(d.asOf)}</span>`;', '· CLOSED · last close ${_rt18CloseLbl(_rt20LastClose(tk) || d.asOf)}</span>`;')
# 2. brief stance is the morning stance, never the current regime; skeletons while booting
R('brief stance', '<div class="home-brief-stance">${_escHtml(_rt16Dec(_brief.houseView || "House view"))}</div>',
  '<div class="home-brief-stance">${_escHtml(_rt20Stance(_brief, re))}</div>')
R('home regime cached label', '<div class="home-regime" style="color:${re.col}">${re.label}${re.score != null && !re.loading ? ` · <span class="home-regime-sc">${re.score}/100</span>` : ""}</div>',
  '<div class="home-regime" style="color:${re.col}">${re.label}${re.score != null && !re.loading ? ` · <span class="home-regime-sc">${re.score}/100</span>${_rt20RegCached(re)}` : ""}</div>')
R('home tape skeleton', ': "Awaiting the price feed — nothing on this page is a stored guess"}</div>', ': _rt20TapeFallback(re)}</div>')
R('brief skeleton', '''    h += `<div class="home-empty">
      <div>${_briefLoad ? "Loading today's brief…" : "No brief loaded yet."}</div>
      <button type="button" class="home-empty-btn" onclick="nav('brief');loadDispatchBrief(true)">Open the Brief</button>
    </div>`;''', '''    h += (_briefLoad || _rt20Booting()) ? _rt20Sk(3) : `<div class="home-empty">
      <div>No brief loaded yet.</div>
      <button type="button" class="home-empty-btn" onclick="nav('brief');loadDispatchBrief(true)">Open the Brief</button>
    </div>`;''')
R('book skeleton', '''    h += `<div class="home-empty">
      <div>${liveN ? "Nothing in your book has a live mark yet." : "Your book is empty."}</div>''', '''    h += (!liveN && _rt20Booting()) ? _rt20Sk(4) : `<div class="home-empty">
      <div>${liveN ? "Nothing in your book has a live mark yet." : "Your book is empty."}</div>''')
R('movers skeleton', '    h += `<div class="home-empty"><div>No live desk names yet this session.</div></div>`;',
  '    h += _rt20Booting() ? _rt20Sk(4) : `<div class="home-empty"><div>No live desk names yet this session.</div></div>`;')
# 3. guest hero: fixed marketing copy; stance in its own reserved line
R('hero h1', '<h1 id="front-door-title">${_escHtml(_frontDoorStance(brief))}</h1>', '<h1 id="front-door-title">Know what matters before gold moves.</h1>')
R('hero stance line', '<p class="front-door-deck">A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions.</p>',
  '<p class="front-door-deck">A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions.</p>\n      <p class="front-door-stance" aria-live="off">${_rt20HeroStance(brief)}</p>')
# 4. summaries: clean text at ingestion, clip at word boundaries everywhere
R('ingest summary x3', 'desc:(it.summary||"").replace(/<[^>]*>/g,"").trim().slice(0,200),', 'desc:_rt20Txt(it.summary,300),', 3)
R('ingest rss', '(entry.querySelector("description, summary, content")?.textContent||"").replace(/<[^>]*>/g,"").trim().slice(0,200);',
  '_rt20Txt(entry.querySelector("description, summary, content")?.textContent,300);')
R('news card desc', '${_escHtml(n.desc.slice(0,160))}${n.desc.length>160?"…":""}', '${_escHtml(_rt20Clip(n.desc,160))}')
R('paper desc', 'opts.lead?_escHtml((n.desc||"").slice(0,220)):_escHtml((n.desc||"").slice(0,110))', '_escHtml(_rt20Clip(n.desc,opts.lead?220:110))')
R('brief summary 220', 'String(brief.summary).slice(0, 220) + (brief.summary.length > 220 ? "…" : "")', '_rt20Clip(brief.summary, 220)')
R('house view 160', '${(_brief.summary || "").slice(0, 160)}', '${_rt20Clip(_brief.summary, 160)}')
R('brief list 100', '${(b.summary || "").slice(0, 100)}…', '${_rt20Clip(b.summary, 100)}')
R('paper rail 200', '${_escHtml(String(_brief.summary||"").slice(0,200))}${(_brief.summary||"").length>200?"…":""}', '${_escHtml(_rt20Clip(_brief.summary,200))}')
# polish: watch tag + price pairing
R('rel pills x3', 'const relHtml=rel.slice(0,2).map(r=>`<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA(\'${r.tk}\')">${r.tag} · ${r.tk}</span>`).join("");',
  'const relHtml=_rt20RelHtml(rel);', None)
R('price pill pairing', 'const pricePill=topTk&&hasSyncedQuote(topTk)?', 'const pricePill=topTk&&!rel.slice(0,2).some(r=>r.tk===topTk)&&hasSyncedQuote(topTk)?')
# polish: crypto table age
R('crypto stale age', '? `CoinGecko table delayed \\u00b7 as of ${_fmtAsOf(asOf.getTime())}`', '? `CoinGecko table delayed \\u00b7 as of ${_rt20AgeLbl(asOf.getTime())}`')
# polish: gold copy from GC=F bars
R('gold ai struct', 'const aiTxt = !aiBlind ? (d.structure?.summary || "") : "";', 'const aiTxt = !aiBlind ? _rt20GoldAi(d.structure?.summary || "", gs) : "";')
R('gold playbook summary', '<p class="gd-body">${_escHtml(pb.regime?.summary || d.structure?.summary || "")}</p>',
  '<p class="gd-body">${_escHtml(_rt20GoldAi(pb.regime?.summary || d.structure?.summary || "", _gdHist) || (_gdHist ? _gdStructText(_gdHist) : ""))}</p>')
R('gold badges', '${gs ? bd(gs.trend, "var(--gd)") + (gs.cond', '${gs ? bd(`${gs.trend} · 20/50-day`, "var(--gd)") + (gs.chgPct != null ? bd(`session ${gs.chgPct >= 0 ? "+" : ""}${gs.chgPct.toFixed(2)}%`, gs.chgPct >= 0 ? "var(--gn)" : "var(--rd)") : "") + (gs.cond')
R('gold trend line', '? `${gs.trend} · daily range ${gs.cond || "—"}', '? `${gs.trend} (20/50-day) · daily range ${gs.cond || "—"}')
# 7. news-scores: arm a short cooldown before the retry so a navigation mid-retry can't fire a third call
R('ns early cooldown', '  if (!res || res.status >= 500) {\n    await new Promise(r => setTimeout(r, 1500 + Math.random() * 1500));',
  '  if (!res || res.status >= 500) {\n    try { sessionStorage.setItem("td_ns_cool", String(Date.now() + 60 * 1000)); } catch (e) {}\n    await new Promise(r => setTimeout(r, 1500 + Math.random() * 1500));')
# polish: stable "Pick up where you left off"
R('pickup stable', 'const recent = (Array.isArray(_recentNav) ? _recentNav : [])\n    .filter(p => NAV_ALL.includes(p) && NAV_LABELS[p]).slice(0, 5);', 'const recent = _rt20Pickup();')

BLOCK = r"""// ── rt20: real session closes, morning stance, word-boundary summaries, strips, skeletons ──
const _rt20T0 = Date.now();
const _rt20CloseCache = {};
/** Most recent session close for this symbol's market (15-min grid; weekends + per-asset sessions, no holidays). */
function _rt20LastClose(tk) {
  try {
    tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
    const cls = _rt18Class(tk); if (cls === "crypto") return null;
    const key = _RT18_IDX[tk] ? tk : cls, q = 15 * 60000, now = Math.floor(Date.now() / q) * q;
    const c = _rt20CloseCache[key]; if (c && c.b === now) return c.v;
    let v = null;
    if (!_rt18MarketOpenAt(tk, new Date(now))) {
      for (let t = now; t > now - 5 * 86400000; t -= q) { if (_rt18MarketOpenAt(tk, new Date(t - q))) { v = t; break; } }
    }
    _rt20CloseCache[key] = { b: now, v };
    return v;
  } catch (e) { return null; }
}
function _rt20Booting() {
  try { if (typeof priceLastFetch !== "undefined" && priceLastFetch) return false; } catch (e) {}
  return Date.now() - _rt20T0 < 15000;
}
function _rt20Sk(n, cls) {
  return `<div class="rt20-sk ${cls || ""}" aria-hidden="true">${Array.from({ length: n }, (_, i) => `<i style="width:${[92, 78, 64, 85][i % 4]}%"></i>`).join("")}</div>`;
}
/** Stored brief stance is shown as the morning stance with its time, and dropped when it contradicts the live regime. */
function _rt20Stance(b, re) {
  const raw = String((typeof _rt16Dec === "function" ? _rt16Dec(b && b.houseView || "") : (b && b.houseView) || "")).trim();
  const ts = Date.parse(b && (b.generatedAt || b.asOf || b.createdAt || "")) || 0;
  const when = ts && typeof _rt18Fmt === "function" ? ` (as of ${_rt18Fmt(_rt17Tz(), "hm").format(new Date(ts))})` : (b && b.date ? ` (brief for ${b.date})` : "");
  if (!re || re.loading) return `Morning brief${when}`;
  const lbl = String(re.label || "");
  const bear = /cautio|defens|bear|risk[- ]?off/i, bull = /constructiv|bull|risk[- ]?on|opportun/i;
  const conflict = raw && lbl && ((/risk[- ]?on/i.test(lbl) && bear.test(raw)) || (/risk[- ]?off|defens/i.test(lbl) && bull.test(raw)));
  if (!raw || conflict) return `Morning brief${when}`;
  const w = raw.length > 28 ? raw.slice(0, 28).replace(/\s+\S*$/, "") + "…" : raw;
  return `Morning stance: ${w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()}${when}`;
}
function _rt20TapeFallback(re) {
  if (_rt20Booting()) return _rt20Sk(1, "rt20-sk-inline");
  let c = null; try { c = quoteStatusCounts(); } catch (e) {}
  const other = c ? (c.closed || 0) + (c.cached || 0) + (c.delayed || 0) : 0;
  if (!other) return "No prices yet — nothing on this page is a stored guess";
  return [c.closed ? `${c.closed} closed · last close` : "", (c.delayed || 0) + (c.cached || 0) ? `${(c.delayed || 0) + (c.cached || 0)} delayed/cached` : "",
    (re && re.vix != null && re.vix !== "—" && re.vix !== "") ? `VIX ${re.vix}` : "", (re && re.spx != null && re.spx !== "—" && re.spx !== "") ? `${re.spxProxy ? "SPY" : "SPX"} ${re.spx}` : ""].filter(Boolean).join(" · ");
}
function _rt20RegCached(re) {
  try { const m = _quoteMeta("VIX"); if (m && m.status === "cached") return ` <span class="home-regime-src">· from cached prices</span>`; } catch (e) {}
  return "";
}
function _rt20HeroStance(brief) {
  const t = brief && typeof _frontDoorStance === "function" ? _frontDoorStance(brief) : "";
  return t && t !== "Know what matters before gold moves." ? _escHtml(t) : "";
}
/** Feed text: tags become spaces, entities decoded, whitespace collapsed, glued words split, word-boundary clip. */
function _rt20Txt(s, n) {
  let t = String(s || "").replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/([a-z]{6,})([A-Z]{2,})(?=[^a-z]|$)/g, "$1 $2").replace(/([.!?;:])([A-Z][a-z])/g, "$1 $2")
    .replace(/\s+/g, " ").trim();
  return n ? _rt20Clip(t, n) : t;
}
/** Word-boundary clip; also tidies text an upstream already cut mid-word. */
function _rt20Clip(s, n) {
  s = String(s || "").trim();
  if (!s) return "";
  if (s.length > n) return _rt16Clip(s, n);
  if (s.length >= 180 && !/[.!?…"'”’)\]]$/.test(s)) return s.replace(/\s+\S*$/, "").replace(/[\s,;:·–—-]+$/, "") + "…";
  return s;
}
function _rt20RelHtml(rel) {
  return (rel || []).slice(0, 2).map(r => {
    let px = "";
    try { if (hasSyncedQuote(r.tk)) px = ` <b class="news-rel-px">${_escHtml(String(fp(r.tk).p))}</b>`; } catch (e) {}
    return `<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA('${r.tk}')">${r.tag} · ${r.tk}${px}</span>`;
  }).join("");
}
function _rt20AgeLbl(ts) {
  const age = Date.now() - ts;
  if (age < 3600000) return _fmtAsOf(ts);
  const d = _rt18CloseLbl(ts), hrs = Math.round(age / 3600000);
  return `${d} (${hrs < 48 ? hrs + "h" : Math.round(hrs / 24) + "d"} old)`;
}
/** Drop AI gold text that contradicts the GC=F bars (e.g. "stable / no movement" on a +1.4% session). */
function _rt20GoldAi(t, gs) {
  t = String(t || ""); if (!t || !gs || gs.chgPct == null) return t;
  const c = gs.chgPct;
  const flat = /\b(stable|no (?:significant |notable )?movement|unchanged|flat|steady|little changed|sideways)\b/i;
  const down = /\b(declin|fell|falling|lower|drop|slid|slump|bearish|sell-?off|weaker)/i, up = /\b(rall|rose|rising|higher|gain|climb|bullish|surg|stronger)/i;
  if (Math.abs(c) >= 0.5 && flat.test(t)) return "";
  if (c >= 0.5 && down.test(t) && !up.test(t)) return "";
  if (c <= -0.5 && up.test(t) && !down.test(t)) return "";
  return t;
}
let _rt20PickupCache = null;
/** Recent sections: the set is taken once per page load and shown in fixed menu order, so it doesn't reshuffle. */
function _rt20Pickup() {
  if (_rt20PickupCache) return _rt20PickupCache;
  const set = (Array.isArray(_recentNav) ? _recentNav : []).filter(p => NAV_ALL.includes(p) && NAV_LABELS[p] && p !== "home").slice(0, 5);
  _rt20PickupCache = set.sort((a, b) => NAV_ALL.indexOf(a) - NAV_ALL.indexOf(b));
  return _rt20PickupCache;
}
(function _rt20Css() {
  if (document.getElementById("rt20-css")) return;
  const st = document.createElement("style"); st.id = "rt20-css";
  st.textContent = `
.rt20-sk{display:flex;flex-direction:column;gap:8px;padding:6px 0 10px}
.rt20-sk i{display:block;height:12px;border-radius:4px;background:linear-gradient(90deg,rgba(255,255,255,.05),rgba(255,255,255,.11),rgba(255,255,255,.05));background-size:200% 100%;animation:rt20sk 1.4s ease-in-out infinite}
.rt20-sk-inline{padding:4px 0}.rt20-sk-inline i{height:10px;max-width:260px}
@keyframes rt20sk{0%{background-position:100% 0}100%{background-position:-100% 0}}
.td-reduce-motion .rt20-sk i{animation:none}
@media (prefers-reduced-motion:reduce){.rt20-sk i{animation:none}}
.home-regime-src{font-size:.6em;color:var(--t3);font-weight:400;letter-spacing:0}
.front-door-stance{min-height:5.8em;line-height:1.45;margin:6px 0 14px;font-size:14px;color:var(--t2,#bbb);font-style:italic}
@media (min-width:761px){.front-door-stance{min-height:3em}}
.news-rel{margin-right:4px;white-space:nowrap}.news-rel-px{font-weight:600;color:var(--tx,#eee);margin-left:3px}
.news-px{margin-left:6px;padding-left:6px;border-left:1px solid var(--b4,#333)}
.seo-panel-copy{display:none}
.panel-body:has(> .seo-panel-copy){min-height:120px;background:linear-gradient(rgba(255,255,255,.06),rgba(255,255,255,.06)) 16px 18px/70% 12px no-repeat,linear-gradient(rgba(255,255,255,.05),rgba(255,255,255,.05)) 16px 42px/55% 12px no-repeat,linear-gradient(rgba(255,255,255,.05),rgba(255,255,255,.05)) 16px 66px/62% 12px no-repeat}
@media (max-width:760px){
 .htec-status-l{flex-wrap:wrap;align-content:flex-start;max-height:34px;row-gap:24px;-webkit-mask-image:none;mask-image:none}
 .htec-status-l>*{flex:none}
}
@media (max-width:420px){
 .wl-glance-lbl{font-size:0}.wl-glance-lbl::before{content:"◎";font-size:12px}
 .wl-glance-track{min-width:120px;flex:1 1 auto}
 .wl-glance-chip{flex:none}
}`;
  document.head.appendChild(st);
})();
"""
R('rt20 block', 'function _rt17Default() {', BLOCK + 'function _rt17Default() {')
for name, old, new, count in E:
    n = s.count(old)
    if count is None:
        if n < 1: die(f"'{name}' anchor matched 0 times")
    elif n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
HE = [('cache bust', 'app.js?v=chat18', 'app.js?v=chat19')]
for name, old, new in HE:
    if h.count(old) != 1: die(f"index '{name}' matched {h.count(old)} times")
    h = h.replace(old, new)
for bad in ['"No brief loaded yet."', '.replace(/<[^>]*>/g,"").trim().slice(0,200)', '_escHtml(_frontDoorStance(brief))']:
    if bad in s: die('postcondition: still present: ' + bad)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits + {len(HE)} index edit; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
