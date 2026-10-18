#!/usr/bin/env python3
"""patch_rt18.py — chat16 -> chat17. Stacks on rt17 output. Client-only.
Usage: python3 patch_rt18.py [--check] <dir containing app.js + index.html>
"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

def load(p):
    b = open(p, 'rb').read(); crlf = b'\r\n' in b
    return b.decode('utf-8').replace('\r\n', '\n'), crlf
def die(m): print('ABORT:', m); sys.exit(1)

s, crlf = load(APP); h, hcrlf = load(IDX)
if 'REALTIME PRICE LAYER (rt18)' in s: die('rt18 already applied')
if 'REALTIME PRICE LAYER (rt17)' not in s: die('base is not rt17 output')
if 'app.js?v=chat16' not in h: die('index.html is not chat16')

E = []
def R(name, old, new, count=1):
    E.append((name, old, new, count))

R('marker', '// REALTIME PRICE LAYER (rt17)', '// REALTIME PRICE LAYER (rt18)')
# --- item 1: bounded price fallback, rate-limit aware, boot timeouts
R('yq rate-limit detect', '      if (!res.ok) continue;\n      Object.assign(data, await res.json());',
  '      if (!res.ok) { window._rt18YqLimited = Date.now(); continue; }\n      if (/rate|limit/i.test(res.headers.get("x-dispatch-data-status") || "")) window._rt18YqLimited = Date.now();\n      Object.assign(data, await res.json());')
R('fh fallback rename', 'async function _fetchFinnhubPriceFallback(symbols) {', 'async function _fetchFinnhubPriceFallbackUnbounded_rt18(symbols) {')
R('me timeout', 'const res=await fetch("/api/me",{credentials:"include"});', 'const res=await fetch("/api/me",{credentials:"include",signal:AbortSignal.timeout(5000)});')
R('editorial timeout', 'fetch(`/api/public/content?type=${type}`,{credentials:"include"})', 'fetch(`/api/public/content?type=${type}`,{credentials:"include",signal:AbortSignal.timeout(4000)})')
# --- item 2: regime narrative + brief text
R('rotation no-instruction', "if (!cN || !dN) return { label: 'Awaiting Data', col: 'var(--t3)', desc: 'Load sector data to see rotation signal' };",
  "if (!cN || !dN) return { label: 'Awaiting Data', col: 'var(--t3)', desc: '' };")
R('narrative drop blanks', 'narrative: `${label} · Regime score ${score}/100. ${rot.desc || ""} VIX ${vixLbl}, SPX ${spxLbl}.` };',
  'narrative: [`${label} · Regime score ${score}/100.`, rot.desc ? `${rot.desc}.` : "", vix != null ? `VIX ${vixLbl}.` : "", spxC != null ? `SPX ${spxLbl}.` : ""].filter(Boolean).join(" ") };')
R('local brief no stale tape', '  const summaryParts = [\n    re.narrative,\n    tapeBits ? `Live tape: ${tapeBits}.` : "Live tape: awaiting feed sync.",',
  '  const summaryParts = [')
R('local brief headline', '    headline: `${re.label} — free desk brief from live tape`,', '    headline: `Desk brief · ${_rt18BriefDay(Date.now())}`,\n    builtAt: Date.now(),')
R('brief clean cache', '        _brief = JSON.parse(c);', '        _brief = _rt18BriefClean(JSON.parse(c));')
R('brief clean local', '  _brief = local;', '  _brief = _rt18BriefClean(local);')
R('brief clean ai', '          _brief = data.brief;', '          _brief = _rt18BriefClean(data.brief);')
R('brief clean archive', '  if (b) { _brief = b; renderMain();', '  if (b) { _brief = _rt18BriefClean(b); renderMain();')
R('intel wrap', 'function _mergeIntel(surface, extra) {', 'function _mergeIntelBase_rt18(surface, extra) {')
R('regime repaint hook', '  const re=_computeRegimeEngine();\n  const feedCounts', '  const re=_computeRegimeEngine();\n  _rt18RegimeTick(re);\n  const feedCounts')
# --- item 1b: first paint — last-known prices from localStorage, bounded editorial wait
R('price cache read ls', '    const raw=sessionStorage.getItem(PRICE_CACHE_KEY)||sessionStorage.getItem("td_price_cache_v1");\n    if(!raw)return false;\n    const data=JSON.parse(raw);\n    if(!data?.ts||Date.now()-data.ts>PRICE_CACHE_MAX_AGE)return false;',
  '    let _rt18Ls=false;\n    let raw=sessionStorage.getItem(PRICE_CACHE_KEY)||sessionStorage.getItem("td_price_cache_v1");\n    if(!raw){try{raw=localStorage.getItem("td_price_cache_ls");_rt18Ls=!!raw;}catch(e){}}\n    if(!raw)return false;\n    const data=JSON.parse(raw);\n    if(!data?.ts||Date.now()-data.ts>(_rt18Ls?12*3600*1000:PRICE_CACHE_MAX_AGE))return false;')
R('price cache write ls', '    sessionStorage.setItem(PRICE_CACHE_KEY,JSON.stringify(payload));',
  '    const _rt18Json=JSON.stringify(payload);\n    sessionStorage.setItem(PRICE_CACHE_KEY,_rt18Json);\n    try{ if(Date.now()-(window._rt18LsSaved||0)>30000){ localStorage.setItem("td_price_cache_ls",_rt18Json); window._rt18LsSaved=Date.now(); } }catch(e){}')
R('editorial bounded wait', '  await editorialReady;\n  _userTierReady=true;',
  '  const _rt18EdPath=/^\\/(brief|report|research)\\/[^/]+\\/?$/.test(location.pathname);\n  let _rt18EdDone=false; editorialReady.then(()=>{_rt18EdDone=true;});\n  await Promise.race([editorialReady,new Promise(r=>setTimeout(r,_rt18EdPath?4000:150))]);\n  if(!_rt18EdDone)editorialReady.then(()=>{try{if(pg==="home"){if(IS_DESKTOP())_desktopRoute("home");else renderMain();}}catch(e){}});\n  _userTierReady=true;')
# --- rt18b: regime loading state + page-aware paywall
R('regime base', 'function _computeRegimeEngine() {', 'function _computeRegimeEngineBase_rt18() {')
R('regime chip', '  const regimeChip=`<span class="htec-chip htec-chip-regime" title="Market regime model (educational)">${re.label} · ${re.score}/100</span>`;',
  '  const regimeChip=re.loading?`<span class="htec-chip htec-chip-regime htec-chip-muted" title="Waiting for VIX and S&amp;P 500 inputs">Regime: loading…</span>`:`<span class="htec-chip htec-chip-regime" title="Market regime model (educational)">${re.label} · ${re.score}/100</span>`;')
R('regime chip mob', '  const regimeChipMob=`<span class="htec-chip htec-chip-regime" title="Market regime model (educational): ${re.label} · ${re.score}/100">${_mobShortRegime(re.label)}</span>`;',
  '  const regimeChipMob=re.loading?`<span class="htec-chip htec-chip-regime htec-chip-muted" title="Waiting for VIX and S&amp;P 500 inputs">Regime…</span>`:`<span class="htec-chip htec-chip-regime" title="Market regime model (educational): ${re.label} · ${re.score}/100">${_mobShortRegime(re.label)}</span>`;')
R('home brief regime', '${re && re.label ? ` · live regime now ${_escHtml(re.label)} ${re.score}/100` : ""}',
  '${re && re.loading ? " · Regime: loading…" : re && re.label ? ` · live regime now ${_escHtml(re.label)} ${re.score}/100` : ""}')
R('paywall title', '<div class="empty-title">${premiumGate ? "The Gold Dashboard is part of Premium" : "Gold desk unavailable"}</div>',
  '<div class="empty-title">${premiumGate ? `${_rt18PageName()} is part of Premium` : "Gold desk unavailable"}</div>')
R('paywall sub', '<div class="empty-sub" style="margin-bottom:12px">Sign in or subscribe to see gold levels, sessions and volatility.</div>',
  '<div class="empty-sub" style="margin-bottom:12px">${_rt18PageBlurb()}</div>')
R('home regime loading', '${re.label}${re.score != null ? ` · <span class="home-regime-sc">${re.score}/100</span>` : ""}</div>',
  '${re.label}${re.score != null && !re.loading ? ` · <span class="home-regime-sc">${re.score}/100</span>` : ""}</div>')
R('home tape no dashes', '      ? `${liveN} symbol${liveN === 1 ? "" : "s"} live · VIX ${re.vix} · ${re.spxProxy ? "SPY" : "SPX"} ${re.spx === "—" ? "—" : re.spx}`',
  '      ? [`${liveN} symbol${liveN === 1 ? "" : "s"} live`, (re.vix != null && re.vix !== "—" && re.vix !== "") ? `VIX ${re.vix}` : "", (re.spx != null && re.spx !== "—" && re.spx !== "") ? `${re.spxProxy ? "SPY" : "SPX"} ${re.spx}` : ""].filter(Boolean).join(" · ")')
# --- item 3 + 6: status pill
R('pill sig', 'const sig=[IS_DESKTOP()?"d":"m",feedKey,', 'const sig=[_userTierReady?"r":"w",priceLastFetch?"p":"n",IS_DESKTOP()?"d":"m",feedKey,')
R('pill no blank while syncing', '    :spinning\n      ?``\n      :degraded', '    :(!priceLastFetch&&!hasFeed)\n      ?`<span class="htec-chip htec-chip-muted">Loading prices…</span>`\n      :degraded')
R('pill text', '        ?`<span class="htec-chip htec-chip-live" title="Shared quote status across the curated Markets universe">${_usRegularOpen()?"FEED":"US MARKETS CLOSED · FEED"} · ${_escHtml(feedSummary)}</span>`',
  '        ?`<span class="htec-chip htec-chip-live" title="Shared quote status across the curated Markets universe">${_usRegularOpen()?"":"US CLOSED · "}${_escHtml(feedSummary)}${IS_DESKTOP()?` · Updated <span class="rt18-upd">${_fmtAsOf(Date.now())}</span>`:""}</span>`')
R('pill tier wait', '  const liveChip = _isPremium()\n    ? premiumLiveChip', '  const liveChip = !_userTierReady\n    ? `<span class="htec-chip htec-chip-muted">Loading prices…</span>`\n    : _isPremium()\n    ? premiumLiveChip')
R('ai chip tier wait', 'const aiChip=_isPremium()', 'const aiChip=!_userTierReady?"":_isPremium()')
# --- item 4: closed markets
R('quoteMeta base', 'function _quoteMeta(tk) {\n  tk = (typeof resolveInternalTicker', 'function _quoteMetaBase_rt18(tk) {\n  tk = (typeof resolveInternalTicker')
R('asOfTag closed', '  return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · as of ${_fmtAsOf(d.asOf)} · ${d.age}</span>`;',
  '  if(d.status==="closed")return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · last close ${_rt18CloseLbl(d.asOf)}</span>`;\n  return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · as of ${_fmtAsOf(d.asOf)} · ${d.age}</span>`;')
# --- item 5: time formats
R('time desk run', 'const t = r.at ? new Date(r.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";', 'const t = r.at ? _fmtAsOf(new Date(r.at).getTime()) : "";')
R('time invalidation', 'Updated ${new Date(inv.updated).toLocaleString()}', 'Updated ${_rt18CloseLbl(new Date(inv.updated).getTime())}')
R('time cg', 'as of ${asOf.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}', 'as of ${_fmtAsOf(asOf.getTime())}')
R('time sectors', "new Date(_sectorFetchedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })", '_fmtAsOf(_sectorFetchedAt)')
R('fmtAsOf cached', '    return new Date(ts).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: _rt17Tz() });',
  '    return _rt18Fmt(_rt17Tz(), "hms").format(new Date(ts));')
# --- item 7: news WATCH WATCH
R('news rel dedupe', 'const relHtml=rel.map(r=>`<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA(\'${r.tk}\')">${r.tag}</span>`).join("");',
  'const relHtml=rel.slice(0,2).map(r=>`<span class="news-rel" style="color:${r.col};border-color:${r.col}40" onclick="event.stopPropagation();openA(\'${r.tk}\')">${r.tag} · ${r.tk}</span>`).join("");', 2)
# clock updates pill time too
R('clock pill', '      const els = document.querySelectorAll(".site-trust-footer .stf-time");', '      const els = document.querySelectorAll(".site-trust-footer .stf-time, .rt18-upd");')

BLOCK = r"""// ── rt18: bounded fallback, closed-market sessions, brief hygiene, strip fades ──
window._rt18YqLimited = window._rt18YqLimited || 0;
const _rt18Fh = { until: 0, neg: {}, inflight: false };
// Replaces the unbounded fan-out (one /api/finnhub request per missing symbol,
// ~200 at once when the Yahoo proxy is rate-limited). Max 6 symbols, 2 in flight,
// negative cache per symbol, global back-off on 429 or an empty proxy.
async function _fetchFinnhubPriceFallback(symbols) {
  const now = Date.now();
  if (now < _rt18Fh.until || _rt18Fh.inflight) return 0;
  if (now - (window._rt18YqLimited || 0) < 120000) return 0;
  const eligible = (symbols || []).filter(tk => tk && !["XAU","DXY","^TNX","^VIX"].includes(tk) && /^[A-Z][A-Z0-9.-]{0,9}$/.test(tk) && !(_rt18Fh.neg[tk] > now)).slice(0, 6);
  if (!eligible.length) return 0;
  _rt18Fh.inflight = true;
  let hits = 0, empty = 0;
  try {
    for (let i = 0; i < eligible.length; i += 2) {
      await Promise.all(eligible.slice(i, i + 2).map(async tk => {
        try {
          const r = await fetch(`/api/finnhub?endpoint=quote&symbol=${encodeURIComponent(tk)}`, { signal: AbortSignal.timeout(6000) });
          if (r.status === 429) { _rt18Fh.until = Date.now() + 300000; return; }
          if (!r.ok) { _rt18Fh.neg[tk] = Date.now() + 600000; empty++; return; }
          const q = await r.json();
          if (_applyLiveQuote(tk, q, "finnhub")) hits++;
          else { empty++; _rt18Fh.neg[tk] = Date.now() + 600000; }
        } catch (e) { _rt18Fh.neg[tk] = Date.now() + 300000; }
      }));
      if (Date.now() < _rt18Fh.until) break;
    }
  } finally { _rt18Fh.inflight = false; }
  if (!hits && empty >= eligible.length) _rt18Fh.until = Date.now() + 600000;
  return hits;
}
// Last-resort boot guard: never leave the loader up if a request hangs.
setTimeout(() => { try { if (document.getElementById("dispatchBootLoader") && typeof _finishAppBoot === "function") _finishAppBoot(); } catch (e) {} }, 9000);

// Intl formatters are expensive to build (~0.1-1 ms each); cache them. Building one
// per row per repaint was the dominant long-task cost in the rt18 profile.
const _rt18FmtCache = {};
function _rt18Fmt(tz, kind) {
  const k = tz + "|" + kind;
  if (_rt18FmtCache[k]) return _rt18FmtCache[k];
  const o = kind === "hms" ? { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: tz }
    : kind === "hm" ? { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: tz }
    : kind === "wd" ? { weekday: "short", timeZone: tz }
    : kind === "day" ? { weekday: "short", day: "numeric", month: "short", timeZone: tz }
    : { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false };
  return (_rt18FmtCache[k] = new Intl.DateTimeFormat(kind === "parts" ? "en-US" : "en-GB", o));
}
function _rt18Parts(tz, d) {
  const o = {};
  _rt18Fmt(tz, "parts").formatToParts(d).forEach(x => { o[x.type] = x.value; });
  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };
}
const _rt18OpenCache = { t: 0, m: {} };
const _RT18_IDX = {
  FTSE: ["Europe/London", 480, 990], DAX: ["Europe/Berlin", 540, 1050], CAC: ["Europe/Paris", 540, 1050], STOXX50: ["Europe/Berlin", 540, 1050],
  N225: ["Asia/Tokyo", 540, 930], HSI: ["Asia/Hong_Kong", 570, 960], NSEI: ["Asia/Kolkata", 555, 930], ASX200: ["Australia/Sydney", 600, 960],
  KOSPI: ["Asia/Seoul", 540, 930], "^AXJO": ["Australia/Sydney", 600, 960], "^KS11": ["Asia/Seoul", 540, 930]
};
function _rt18Class(tk) {
  try { if (typeof _rtIsCrypto === "function" && _rtIsCrypto(tk)) return "crypto"; } catch (e) {}
  const tc = (typeof TICKER_CATS !== "undefined" && TICKER_CATS[tk]) || "";
  const a = (typeof A !== "undefined" && A.find(x => x.tk === tk)) || null;
  const cat = String((a && a.cat) || "").toLowerCase();
  if (tc === "cry" || cat === "crypto") return "crypto";
  if (tc === "fx" || cat === "fx") return "fx";
  if (tc === "cmd" || cat.startsWith("commod")) return "fut";
  return "us";
}
/** Is this symbol's market in session now? Weekends + per-asset sessions; exchange holidays are not modelled. */
function _rt18MarketOpen(tk, when) {
  if (!when) {
    const now = Date.now();
    if (now - _rt18OpenCache.t > 15000) { _rt18OpenCache.t = now; _rt18OpenCache.m = {}; }
    if (tk in _rt18OpenCache.m) return _rt18OpenCache.m[tk];
    return (_rt18OpenCache.m[tk] = _rt18MarketOpenAt(tk, new Date(now)));
  }
  return _rt18MarketOpenAt(tk, new Date(when));
}
function _rt18MarketOpenAt(tk, d) {
  const cls = _rt18Class(tk);
  if (cls === "crypto") return true;
  try {
    if (_RT18_IDX[tk]) {
      const [tz, o, c] = _RT18_IDX[tk]; const p = _rt18Parts(tz, d);
      return !["Sat", "Sun"].includes(p.wd) && p.m >= o && p.m < c;
    }
    const p = _rt18Parts("America/New_York", d);
    if (cls === "fx" || cls === "fut") {
      if (p.wd === "Sat") return false;
      if (p.wd === "Fri" && p.m >= 1020) return false;
      if (p.wd === "Sun" && p.m < (cls === "fx" ? 1020 : 1080)) return false;
      if (cls === "fut" && p.m >= 1020 && p.m < 1080) return false;
      return true;
    }
    return !["Sat", "Sun"].includes(p.wd) && p.m >= 570 && p.m < 960;
  } catch (e) { return true; }
}
function _rt18CloseLbl(ts) {
  if (!ts) return "—";
  try {
    const tz = typeof _rt17Tz === "function" ? _rt17Tz() : "Europe/London";
    const d = new Date(ts);
    const wd = _rt18Fmt(tz, "wd").format(d);
    const hm = _rt18Fmt(tz, "hm").format(d);
    return `${wd} ${hm}`;
  } catch (e) { return "—"; }
}
function _quoteMeta(tk) {
  const m = _quoteMetaBase_rt18(tk);
  if (!m || !["stale", "delayed", "cached", "rth-close"].includes(m.status)) return m;
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  if (_rt18MarketOpen(tk)) return m;
  return { ...m, status: "closed", label: "CLOSED", detail: `Market closed — last close ${_rt18CloseLbl(m.asOf)}`, trusted: true };
}
/** One regime source: any "<regime> · NN/100" claim in AI/cached intel text is rewritten to the live engine value. */
const _RT18_REG_RE = /\b(Risk-On(?: \(Fragile\))?|Risk-Off|Transition|Neutral|Defensive|Mixed|Caution|Risk On|Risk Off)\s*·\s*(?:Regime score\s*)?\d{1,3}\/100/gi;
function _rt18LiveRegimeText(t, re) {
  if (typeof t !== "string" || !t) return t;
  if (!re) { try { re = _computeRegimeEngine(); } catch (e) {} }
  let out = re ? t.replace(_RT18_REG_RE, re.loading ? "Regime: loading…" : `${re.label} · ${re.score}/100`) : t;
  if (re && re.loading) out = out.replace(/Regime: loading…\s*·\s*\d{1,3}\/100/g, "Regime: loading…");
  return out.replace(/Load sector data to see rotation signal\.?/gi, "").replace(/\b(VIX|SPX|DXY)\s+—[,.]?/g, "")
    .replace(/[^.]*\bno (?:updated|current|live) (?:market )?prices?[^.]*\.?/gi, "").replace(/\s{2,}/g, " ").trim();
}
function _mergeIntel(surface, extra) {
  const r = _mergeIntelBase_rt18(surface, extra);
  if (!r || typeof r !== "object") return r;
  let re = null; try { re = _computeRegimeEngine(); } catch (e) {}
  const o = { ...r };
  ["headline", "insight"].forEach(k => { if (typeof o[k] === "string") o[k] = _rt18LiveRegimeText(o[k], re); });
  if (Array.isArray(o.anomalies)) o.anomalies = o.anomalies.map(a => typeof a === "string" ? _rt18LiveRegimeText(a, re) : (a && typeof a.m === "string" ? { ...a, m: _rt18LiveRegimeText(a.m, re) } : a));
  return o;
}
// Called from renderStatus (which already runs whenever prices/regime change). Repaints the
// signature-gated intel bar only when the live regime label/score actually moved. No timers.
let _rt18RegSig = "";
function _rt18RegimeTick(re) {
  const sig = re ? `${re.label}|${re.score}|${re.loading ? 1 : 0}` : "";
  if (!sig || sig === _rt18RegSig) return;
  _rt18RegSig = sig;
  Promise.resolve().then(() => {
    try { _paintSiteIntelBar(); } catch (e) {}
    try {
      const c = document.getElementById("siteIntelCard");
      if (c && typeof _renderSiteIntelCard === "function") {
        const t = document.createElement("div");
        t.innerHTML = _renderSiteIntelCard(_siteIntel.surface || "pulse", { tk: selTk });
        if (t.firstElementChild) c.replaceWith(t.firstElementChild);
      }
    } catch (e) {}
  });
}
/** Regime is "loading" until both VIX and SPX inputs exist; never show a half-input score. */
function _computeRegimeEngine() {
  const r = _computeRegimeEngineBase_rt18();
  const ok = v => v != null && v !== "—" && v !== "" && isFinite(parseFloat(v));
  if (r && (!ok(r.vix) || !ok(r.spxChg))) {
    return { ...r, loading: true, label: "Regime: loading…", narrative: "Regime: loading…" };
  }
  return r;
}
const _RT18_PAGES = {
  gold: ["The Gold Dashboard", "Sign in or subscribe to see gold levels, sessions and volatility."],
  playbook: ["Playbook", "Sign in or subscribe to see the weekly gold playbook: levels, scenarios and invalidation."],
  brief: ["The Dispatch Brief", "Sign in or subscribe to read the full daily brief."],
  lab: ["The Lab", "Sign in or subscribe to use the research lab."],
  markets: ["Markets", "Sign in or subscribe to see the full markets desk."],
  news: ["The Newsroom", "Sign in or subscribe to see the full newsroom."]
};
function _rt18PageName() { const p = (typeof pg === "string" && _RT18_PAGES[pg]) || null; return p ? p[0] : "This section"; }
function _rt18PageBlurb() { const p = (typeof pg === "string" && _RT18_PAGES[pg]) || null; return p ? p[1] : "Sign in or subscribe to unlock this section."; }
function _rt18BriefDay(ts) {
  try { return _rt18Fmt(typeof _rt17Tz === "function" ? _rt17Tz() : "Europe/London", "day").format(new Date(ts)); } catch (e) { return ""; }
}
/** Stored brief text is a dated morning note: strip regime scores, stale price claims and empty fragments. */
function _rt18BriefClean(b) {
  if (!b || typeof b !== "object") return b;
  const out = { ...b };
  const day = _rt18BriefDay(out.builtAt || (out.date ? out.date + "T08:00:00Z" : Date.now()));
  const strip = t => String(t || "")
    .replace(/[^.]*\bRegime score \d+\/100\.?/gi, "")
    .replace(/Load sector data to see rotation signal\.?/gi, "")
    .replace(/Live tape:[^]*?(\.\s|\.$|$)/gi, "")
    .replace(/[^.]*\bno (?:updated|current|live) (?:market )?prices?[^.]*\.?/gi, "")
    .replace(/\b(VIX|SPX|DXY|BTC|Gold|WTI)\s+—[,.]?/g, "")
    .replace(/\s{2,}/g, " ").replace(/^[\s·,.]+/, "").trim();
  if (typeof out.headline === "string" && /free desk brief from live tape|AI response could not|AI credits empty/i.test(out.headline)) out.headline = `Desk brief · ${day}`;
  ["summary", "houseView"].forEach(k => { if (typeof out[k] === "string") out[k] = strip(out[k]); });
  out._rt18Day = day;
  return out;
}
(function _rt18Css() {
  if (document.getElementById("rt18-css")) return;
  const st = document.createElement("style"); st.id = "rt18-css";
  st.textContent = `
.tape{-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 28px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 28px),transparent)}
@media (max-width:760px){
 .htec-status-l{min-width:0;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent)}
 .htec-status-l .htec-chip{white-space:nowrap;flex:none}
 .wl-glance-track,.wl-g-row{-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent)}
}
.rt18-upd{font-variant-numeric:tabular-nums}`;
  document.head.appendChild(st);
})();
"""
R('rt18 block', 'function _rt17Default() {', BLOCK + 'function _rt17Default() {')

for name, old, new, count in E:
    n = s.count(old)
    if n != count: die(f"'{name}' anchor matched {n} times (want {count})")
    s = s.replace(old, new)
for name, old, new, count in E:
    pass
h = h.replace('app.js?v=chat16', 'app.js?v=chat17')
# post-conditions
for must in ['_quoteMetaBase_rt18', 'function _quoteMeta(tk) {\n  const m = _quoteMetaBase_rt18', 'async function _fetchFinnhubPriceFallback(symbols) {\n  const now']:
    if must not in s: die('postcondition missing: ' + must[:40])
if "desc: 'Load sector data" in s: die('instruction text still present')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print(f'OK {len(E)} edits; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    def save(p, txt, c):
        open(p, 'wb').write((txt.replace('\n', '\r\n') if c else txt).encode('utf-8'))
    save(APP, s, crlf); save(IDX, h, hcrlf); print('written', APP, IDX)
