#!/usr/bin/env python3
"""patch_rt52.py: chatN -> chatN+1 (client only). Stacks on live chat56 (app.js b9d3d0a3, rt51 on top).
Appends one block that only redefines or wraps existing functions:
- a "basis" sheet (tap i, or the dotted score): what it is, how it is worked out, source, as of (UK) and why it matters, for the regime
  score (point by point, same rules as the engine), every Signal, chokepoint and country scores, Market Lab fit and desk scores, Geo tiles;
- Signals: "Desk conviction 50/100" with the reason it is held (e.g. "Desk rating 88, held at 50: XOM moved +2.46% on Fri, past the
  1.5% review line"), horizon in words, venue status with reopen time, no stray "V" chip (Visa matched inside "reserves");
- 13F: grouped by fund, ticker, $ values (unit fixed for filers that report dollars), change vs previous quarter, % of portfolio,
  quarter and filing dates, one-line "why it matters"; insider rows formatted; "checked 22:22 UK" instead of ISO timestamps;
- Geo Ops: no fake week-on-week %, scores "/100" with basis, tiles with as-of and hours, WTI "closed · opens 23:00 UK",
  conflict timeline and dossier headlines from the live news feed (no stale hard-coded events), reference figures labelled;
- every "as of" reads "21:03 UK" / "Fri 21:03 UK"; raw ISO dates/timestamps on screen become words; "MODEL (NOT LLM)" plain;
- one regime-fit result on every screen (beta from the desk reference list); DXY keeps computing from the last USD/SEK price;
- "What's trading now": same split at every width, each group's hours (grains/softs/lumber corrected), per-market list, Esc closes;
- INTEL banner waits for prices and news to sync and drops "not yet synced" claims; news tags use whole words (Bitcoin -> Crypto);
- Academy "In the news" headline cards refresh when 2h+ old or thin (max 8 a day); brief archive cleaned like today's brief;
- Market Lab guide shows on the first visit only.
No server change in this file, no new tables, no Stripe.
Usage: python3 patch_rt52.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT (nothing written):', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt52 ──' in s: die('rt52 already applied')
if '// ── rt51 ──' not in s: die('base lacks rt51 (expected live chat56)')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 56: die('index is %s; expected chat56 or later' % base)
print('base:', base, '(rt51 present)')
for need in ['function renderSig(', 'function renderP3(', 'function _paintChokepointStrip(', 'function _renderGeoMacroTiles(', 'function _geoEnergyRow(', 'function _renderConflictTimeline(', 'function _renderCommodityExposureTable(', 'function _renderCountryDossier(', 'function renderGeoOps(', 'function renderLab(', 'function _tickerRegimeFit(', 'async function _loadInstitutional(', 'function _renderInstitutionalIntelligence(', 'function _rt51Html(', 'function _rt51Label(', 'function _rt51Next(', 'function _rt51When(', 'function _rt27CleanAi(', 'async function _fetchSiteIntelAI(', 'function detectTag(', 'const TAG_RULES', 'function _rt48NwBuild(', 'function _rt48AutoKick(', 'function _getBriefHistory(', 'function _rt18BriefClean(', 'function _signalEvidence(', 'function _fmtAsOf(', 'const RT43_DXY', 'let _rt43Sek', 'const TD_CHOKEPOINTS', 'const TD_COUNTRY_DOSSIERS', 'function _geoCpScore(', 'function _quoteSourceLabel(', 'let _rt51SekOld', 'function _rt51Brk(']:
    if need not in s: die('app.js anchor missing: ' + need)
BLOCK = r'''// ── rt52 ── Every number shows its basis: a tap-for-basis sheet (what it is, how it's worked out, source, as of, why it matters) on
// the regime score, Signals, chokepoints, country scores, Lab scores and quote tiles; 13F rows with ticker, $ value, change vs the
// previous quarter and % of portfolio; insider rows formatted; UK times with the day; reopen times for closed venues; no raw ISO
// timestamps; Geo timeline from live headlines; DXY keeps computing from the last USD/SEK price when the SEK poll is rate-limited.
// 0) formatting
function _rt52E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function _rt52Tz() { try { return _rt17Tz() || 'Europe/London'; } catch (e) { return 'Europe/London'; } }
function _rt52TzL() { try { return _rt51TzL(); } catch (e) { return 'UK'; } }
function _rt52Ms(t) { if (t == null || t === '') return 0; if (typeof t === 'number') return t < 1e11 ? t * 1000 : t; const n = Date.parse(t); return isFinite(n) ? n : 0; }
function _rt52At(t, opt) { const ms = _rt52Ms(t); if (!ms) return '—'; try { const tz = _rt52Tz(), d = new Date(ms), day = x => new Intl.DateTimeFormat('en-CA', { timeZone: tz }).format(x);
  const hm = new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', second: opt === 's' ? '2-digit' : undefined, hourCycle: 'h23' }).format(d);
  const age = Date.now() - ms; let pre = '';
  if (day(d) !== day(new Date())) pre = age < 6 * 864e5 && age > -864e5 ? new Intl.DateTimeFormat('en-GB', { timeZone: tz, weekday: 'short' }).format(d) + ' ' : new Intl.DateTimeFormat('en-GB', { timeZone: tz, day: 'numeric', month: 'short' }).format(d) + ', ';
  return `${pre}${hm} ${_rt52TzL()}`; } catch (e) { return '—'; } }
function _rt52Day(s) { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || '')); if (!m) return s ? String(s) : '—';
  return `${Number(m[3])} ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][Number(m[2]) - 1]} ${m[1]}`; }
function _rt52Qtr(p) { const m = /^(\d{4})-(\d{2})/.exec(String(p || '')); return m ? `Q${Math.ceil(Number(m[2]) / 3)} ${m[1]}` : ''; }
function _rt52Money(n) { n = Number(n); if (!isFinite(n)) return '—'; const a = Math.abs(n), s = n < 0 ? '−' : '';
  const f = (v, u) => `${s}$${v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(1).replace(/\.0$/, '') : v.toFixed(2).replace(/0$/, '').replace(/\.0$/, '')}${u}`;
  return a >= 1e12 ? f(a / 1e12, 'tn') : a >= 1e9 ? f(a / 1e9, 'bn') : a >= 1e6 ? f(a / 1e6, 'm') : a >= 1e3 ? f(a / 1e3, 'k') : `${s}$${Math.round(a).toLocaleString('en-GB')}`; }
function _rt52Cnt(n) { n = Number(n); if (!isFinite(n)) return '—'; const a = Math.abs(n), s = n < 0 ? '−' : '';
  return a >= 1e9 ? `${s}${(a / 1e9).toFixed(2)}bn` : a >= 1e6 ? `${s}${(a / 1e6).toFixed(a >= 1e8 ? 0 : a >= 1e7 ? 1 : 2)}m` : `${s}${Math.round(a).toLocaleString('en-GB')}`; }
function _rt52Pc(n, dp) { n = Number(n); if (!isFinite(n)) return ''; return `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n).toFixed(dp == null ? (Math.abs(n) >= 100 ? 0 : 1) : dp)}%`; }
// every "as of" across the site: UK clock time with the day when it is not today
try { _fmtAsOf = function (ts) { return ts ? _rt52At(ts) : '—'; }; } catch (e) {}
// 1) venue status in plain words: "Closed · opens 23:00 UK"
function _rt52Open(tk) { try { return _rt18MarketOpen(tk); } catch (e) { return true; } }
function _rt52Reopen(tk) { try { const n = _rt51Next(tk); return n ? `opens ${_rt51When(n)}` : ''; } catch (e) { return ''; } }
function _rt52State(tk) { let m = {}; try { m = _quoteMeta(tk) || {}; } catch (e) {}
  if (!hasSyncedQuote(tk)) return { open: _rt52Open(tk), txt: 'No price yet', at: '' };
  const at = m.asOf ? _rt52At(m.asOf) : '';
  if (!_rt52Open(tk)) { const r = _rt52Reopen(tk); return { open: false, txt: `Closed${r ? ' · ' + r : ''}`, at: at ? `last price ${at}` : '' }; }
  let live = false; try { live = _rt39Live(tk); } catch (e) {}
  return { open: true, txt: live ? 'Trading now' : 'Open · no new price for 20 min', at: at ? `as of ${at}` : '' }; }
const RT52_Q = {
  VIX: ['Cboe Volatility Index: the options market’s expected swing in the S&P 500 over the next 30 days, in % a year.', 'Above 20 means traders are paying up for protection; above 28 is stress. It is the biggest single input to the regime score.'],
  DXY: ['US Dollar Index: the dollar against six major currencies (euro 57.6%, yen 13.6%, pound 11.9%, Canadian dollar 9.1%, krona 4.2%, franc 3.6%).', 'A stronger dollar usually weighs on gold, commodities and emerging markets.'],
  WTI: ['West Texas Intermediate crude oil, US dollars a barrel.', 'Oil above $95 adds inflation pressure, so it takes 5 points off the regime score.'],
  BRENT: ['Brent crude oil, the global benchmark, US dollars a barrel.', 'Brent prices most of the world’s oil, so it shows supply shocks first.'],
  XAU: ['Spot gold, US dollars a troy ounce.', 'Gold tends to rise when real yields fall, the dollar weakens or risk rises.'],
  TNX: ['US 10-year Treasury yield, % a year.', 'Higher yields raise borrowing costs and lower the value of future profits, weighing on growth stocks and gold.'],
  SPX: ['S&P 500 index of 500 large US companies.', 'Its daily move is an input to the regime score (above +0.5% adds 8 points, below −0.5% takes 10 off).'],
  BTC: ['Bitcoin in US dollars, trading 24/7.', 'A gain above 2% on the day adds 4 points to the regime score as a sign of risk appetite.'],
};
function _rt52Src(tk) { try { const m = _quoteMeta(tk) || {}; return m.src ? _quoteSourceLabel(m.src) : (liveQuoteSrc[tk] ? _quoteSourceLabel(liveQuoteSrc[tk]) : 'No source yet'); } catch (e) { return '—'; } }
// 2) the basis sheet
const RT52_B = {};
function _rt52I(id, arg, label) { return `<button type="button" class="rt52-i" data-rt52b="${_rt52E(id)}" data-rt52a="${_rt52E(arg || '')}" aria-label="${_rt52E('How this is worked out' + (label ? ': ' + label : ''))}" title="How this is worked out">i</button>`; }
function _rt52Sheet(b) { const li = a => (a || []).filter(Boolean).map(x => `<li>${x}</li>`).join('');
  return `<div class="rt52-box" role="dialog" aria-modal="true" aria-labelledby="rt52h"><div class="rt52-hd"><div><div class="rt52-k">${_rt52E(b.k || 'BASIS')}</div><h2 id="rt52h">${_rt52E(b.t)}</h2></div><button type="button" class="rt52-x" aria-label="Close">×</button></div>
  ${b.v ? `<div class="rt52-v">${b.v}</div>` : ''}
  <div class="rt52-sec"><div class="rt52-sl">What it is</div><p>${b.what}</p></div>
  ${b.how && b.how.length ? `<div class="rt52-sec"><div class="rt52-sl">How it’s worked out</div><ul>${li(b.how)}</ul></div>` : ''}
  <div class="rt52-sec rt52-two"><div><div class="rt52-sl">Source</div><p>${b.src}</p></div><div><div class="rt52-sl">As of</div><p>${b.at || _rt52At(Date.now())}</p></div></div>
  ${b.why ? `<div class="rt52-sec"><div class="rt52-sl">Why it matters</div><p>${b.why}</p></div>` : ''}
  <p class="rt52-fine">${b.fine || 'Research only, not investment advice.'}</p></div>`; }
let _rt52Back = null, _rt52Cur = null;
function _rt52Close() { const o = document.getElementById('rt52dlg'); if (o) o.remove(); _rt52Cur = null; try { if (_rt52Back && _rt52Back.isConnected) _rt52Back.focus(); } catch (e) {} _rt52Back = null; }
function _rt52Show(id, arg, from) { const f = RT52_B[id]; if (!f) return; let b; try { b = f(arg); } catch (e) { b = null; } if (!b) return;
  const had = !!document.getElementById('rt52dlg'); if (had) { const o0 = document.getElementById('rt52dlg'); o0.remove(); } else _rt52Back = from || document.activeElement;
  const o = document.createElement('div'); o.id = 'rt52dlg'; o.className = 'rt52-ov'; o.innerHTML = _rt52Sheet(b); _rt52Cur = [id, arg];
  o.addEventListener('click', e => { if (e.target === o || (e.target.closest && e.target.closest('.rt52-x'))) _rt52Close(); });
  o.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); _rt52Close(); } else if (e.key === 'Tab') { e.preventDefault(); o.querySelector('.rt52-x').focus(); } });
  document.body.appendChild(o); o.querySelector('.rt52-x').focus(); }
document.addEventListener('click', e => { const el = e.target && e.target.closest && e.target.closest('[data-rt52b]'); if (!el || el.closest('#rt52dlg')) return; e.preventDefault(); e.stopPropagation(); _rt52Show(el.getAttribute('data-rt52b'), el.getAttribute('data-rt52a'), el); }, true);
document.addEventListener('keydown', e => { const el = e.target && e.target.closest && e.target.closest('[data-rt52b]'); if (el && el.tagName !== 'BUTTON' && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); e.stopPropagation(); _rt52Show(el.getAttribute('data-rt52b'), el.getAttribute('data-rt52a'), el); } }, true);
// 3) regime score: the same rules as the engine, shown point by point
function _rt52Regime() { const re = _computeRegimeEngine(), r = _getRegimeState();
  const num = v => { if (v == null || v === '—' || v === '') return null; const n = parseFloat(v); return isFinite(n) ? n : null; };
  const vix = num(r.vix), spx = num(r.spxChg), oil = num(r.oil), dxy = num(r.dxy); let btc = null; try { btc = liveSymbols.has('BTC') ? liveChg('BTC') : null; } catch (e) {}
  const rows = [['Starting point', 50, 'every score starts at 50']]; let s = 50; const add = (l, p, n) => { rows.push([l, p, n]); s += p; };
  const st = tk => { const x = _rt52State(tk); return x.open ? '' : ` (${x.at || 'last price'}; market closed)`; };
  if (vix != null) { const p = vix < 16 ? 18 : vix < 20 ? 8 : vix > 28 ? -22 : vix > 22 ? -12 : 0; add(`VIX ${vix.toFixed(2)}${st('VIX')}`, p, vix < 16 ? 'calm: below 16 adds 18' : vix < 20 ? 'below 20 adds 8' : vix > 28 ? 'above 28 takes 22 off' : vix > 22 ? 'above 22 takes 12 off' : '20 to 22 is neutral'); } else rows.push(['VIX', 0, 'no price yet, counted as neutral']);
  if (spx != null) { const p = spx > 0.5 ? 8 : spx < -0.5 ? -10 : 0; add(`${r.spxProxy ? 'SPY (S&P 500 fund)' : 'S&P 500'} ${spx >= 0 ? '+' : ''}${spx}% on the day${st(r.spxProxy || 'SPX')}`, p, spx > 0.5 ? 'above +0.5% adds 8' : spx < -0.5 ? 'below −0.5% takes 10 off' : 'within ±0.5% is neutral'); }
  if (dxy != null) { const p = dxy < 99 ? 6 : dxy > 101 ? -6 : 0; add(`Dollar index ${dxy.toFixed(2)}`, p, dxy < 99 ? 'below 99 adds 6' : dxy > 101 ? 'above 101 takes 6 off' : '99 to 101 is neutral'); }
  if (oil != null) { const p = oil > 95 ? -5 : 0; add(`WTI oil $${oil.toFixed(2)}${st('WTI')}`, p, oil > 95 ? 'above $95 takes 5 off' : 'at or below $95 is neutral'); }
  if (btc != null) { const p = btc > 2 ? 4 : 0; add(`Bitcoin ${btc >= 0 ? '+' : ''}${btc.toFixed(2)}% on the day`, p, btc > 2 ? 'above +2% adds 4' : 'up to +2% is neutral'); }
  const total = Math.max(0, Math.min(100, s)); return { re, rows, total, ok: total === Number(re.score) }; }
RT52_B.regime = () => { const g = _rt52Regime(), re = g.re; if (re.loading) return { t: 'Market regime', what: 'The regime score is waiting for VIX and S&P 500 prices.', src: 'Free market feeds', why: '' };
  const pts = p => `<b class="${p > 0 ? 'rt52-up' : p < 0 ? 'rt52-dn' : ''}">${p > 0 ? '+' : p < 0 ? '−' : '±'}${Math.abs(p)}</b>`;
  return { k: 'REGIME SCORE', t: `${re.label} · ${re.score}/100`, v: `<table class="rt52-tbl">${g.rows.map(([l, p, n]) => `<tr><td>${_rt52E(l)}<small>${_rt52E(n)}</small></td><td>${pts(p)}</td></tr>`).join('')}<tr class="rt52-sum"><td>Score (kept between 0 and 100)</td><td><b>${g.ok ? g.total : re.score}</b></td></tr></table>`,
    what: 'A 0–100 read of how much risk the market is willing to take, worked out in your browser from five live prices. 72 and above is Risk-On (Strong), 55–71 Risk-On (Fragile), 40–54 Transition, below 40 Risk-Off.',
    how: ['Each input adds or takes away points using fixed thresholds (left). Missing prices count as neutral rather than being guessed.', 'Recalculated every time a new price arrives. Closed markets use their last price until they reopen.'],
    src: `VIX, S&P 500 and oil from ${_rt52E(_rt52Src('VIX'))}; dollar index ${_rt52E(_rt52Src('DXY'))}; Bitcoin ${_rt52E(_rt52Src('BTC'))}`, at: _rt52At(Date.now()),
    why: `It sets which styles the desk favours right now (favour: ${_rt52E((re.overweight || []).slice(0, 3).join(', '))}; avoid: ${_rt52E((re.underweight || []).slice(0, 2).join(', '))}) and feeds the brief, Signals and Market Lab fit scores. An educational model, not a forecast.` }; };
RT52_B.q = tk => { const d = RT52_Q[tk] || [`${tk} price.`, '']; const s = _rt52State(tk); let p = '—'; try { p = hasSyncedQuote(tk) ? fp(tk).p : '—'; } catch (e) {}
  let det = ''; try { det = (_quoteMeta(tk) || {}).detail || ''; } catch (e) {}
  return { k: 'PRICE', t: `${tk} ${p}`, what: d[0], how: [s.txt + (s.at ? ` · ${s.at}` : ''), det ? _rt52E(det) : ''], src: _rt52E(_rt52Src(tk)), at: s.at ? s.at.replace(/^(last price|as of) /, '') : '—', why: d[1] }; };
// 4) Signals: the conviction is the desk's fixed rating, held at 50 when the live check fails
function _rt52Link(s) { try { return A.find(a => a.tk === s.tk) || A.find(a => a.tk.length >= 3 && new RegExp(`\\b${a.tk.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`).test(s.a.toUpperCase())) || null; } catch (e) { return null; } }
const RT52_HZ = { '1wk': '1 week', '1-2wk': '1–2 weeks', 'Qtr': 'this quarter', '3-6mo': '3–6 months', '6-12mo': '6–12 months' };
function _rt52Sig(s) { const ev = _signalEvidence(s), st = _rt52State(s.tk), mv = ev.move;
  const day = (() => { try { const d = _rt26Day(s.tk); return d === 'today' ? 'today' : `on ${d}`; } catch (e) { return 'today'; } })();
  const mvT = mv == null ? '' : `${mv >= 0 ? '+' : '−'}${Math.abs(mv).toFixed(2)}% ${day}`;
  const held = ev.conviction != null && ev.conviction < s.cf;
  const why = ev.conviction == null ? `On hold: no comparable price for ${s.tk} yet` : held ? (Math.abs(mv || 0) > 1.5 ? `Desk rating ${s.cf}, held at ${ev.conviction}: ${s.tk} moved ${mvT}, past the 1.5% review line` : `Desk rating ${s.cf}, held at ${ev.conviction}: the ${s.tk} price is not current`) : `Desk rating ${s.cf} · ${s.tk} ${mvT || 'unchanged'}, within the 1.5% review line`;
  const line = `${s.tk} ${ev.price}${mvT ? ` · ${mvT}` : ''} · ${st.txt}${st.at ? ` · ${st.at}` : ''} · ${ev.source}`;
  return { ev, st, mvT, held, why, line, hz: RT52_HZ[s.hz] || s.hz, cf: ev.conviction }; }
RT52_B.sig = i => { const s = SIGS[Number(i)]; if (!s) return null; const g = _rt52Sig(s);
  return { k: 'SIGNAL', t: `${s.a}: conviction ${g.cf == null ? 'on hold' : g.cf + '/100'}`, v: `<p class="rt52-q">“${_rt52E(s.x)}”</p>`,
    what: `The desk’s view on ${_rt52E(s.a)} (${_rt52E(s.cat.toLowerCase())}, ${_rt52E(s.s.toLowerCase())} strength, horizon ${_rt52E(g.hz)}). Conviction is how strongly the desk holds the view, from 0 to 100. It is not a probability.`,
    how: [`The desk sets the rating (${s.cf}/100 for this view). It does not move with prices.`, `Live check: the comparison price is ${_rt52E(s.tk)}. If it is unavailable, not current, or has moved more than 1.5% on its last session, the rating is held at 50 at most until the view is re-checked against that move.`, `Now: ${_rt52E(g.why)}.`],
    src: `View: The Dispatch desk. Price: ${_rt52E(g.ev.source)}`, at: _rt52E(g.st.at ? g.st.at.replace(/^(last price|as of) /, '') : '—'),
    why: `Use it to see which themes the desk leans on for the next ${_rt52E(g.hz)}, and check the live price before acting on it. A held rating means the market has moved since the view was set.` }; };
function _rt52SigCard(s, i) { const g = _rt52Sig(s), ev = g.ev;
  const bc = s.cat.includes('Bull') || s.cat === 'Momentum' || s.cat === 'Accumulation' || s.cat === 'Contrarian' ? 'var(--gn)' : s.cat.includes('Warning') || s.cat === 'Geopolitical' ? 'var(--rd)' : 'var(--gd)';
  const col = g.cf == null ? 'var(--t3)' : g.held ? 'var(--gd)' : g.cf >= 75 ? 'var(--gn)' : 'var(--gd)'; const linked = _rt52Link(s);
  return `<div class="gc gc-a rt52-sig" style="border-left:3px solid ${g.held ? 'var(--gd)' : bc};padding:12px;cursor:pointer" onclick="${linked ? `openA('${linked.tk}')` : 'void(0)'}">
    <div class="rt52-sig-top"><span class="rt52-sig-n">${_rt52E(s.a)}</span><span class="rt52-sig-c" style="color:${col}">${g.cf == null ? 'On hold' : `${g.cf}<small>/100</small>`}${_rt52I('sig', i, s.a + ' conviction')}</span></div>
    <div class="rt52-sig-k">DESK CONVICTION · ${_rt52E(s.cat.toUpperCase())} · ${_rt52E(s.s.toUpperCase())} · HORIZON ${_rt52E(g.hz.toUpperCase())}</div>
    <div class="rt52-sig-x">${_rt52E(s.x)}</div>
    <div class="rt52-bar"><i style="width:${g.cf || 0}%;background:${col}"></i>${g.held ? `<em style="left:${s.cf}%" title="Desk rating ${s.cf}"></em>` : ''}</div>
    <div class="rt52-sig-w${g.held ? ' held' : ''}">${_rt52E(g.why)}</div>
    <div class="rt52-sig-e">${_rt52E(g.line)}</div></div>`; }
try { renderSig = function () { const re = _computeRegimeEngine();
  let h = _renderPgHdr('Signals', 'Desk views with a live price check · tap i for how each is scored');
  h += _renderSiteIntelCard('signals');
  if (!re.loading) h += `<div class="gc" style="padding:12px;border-left:3px solid ${re.col};margin-bottom:10px">
    <div style="display:flex;align-items:center;gap:6px;font-family:var(--mn);font-size:9px;color:${re.col};letter-spacing:0.14em;margin-bottom:6px">REGIME PLAYBOOK · ${_rt52E(re.label.toUpperCase())} · ${re.score}/100 ${_rt52I('regime', '', 'regime score')}</div>
    <div style="font-size:12px;color:var(--t2);line-height:1.55;margin-bottom:8px">${re.narrative}</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">${re.overweight.slice(0, 3).map(x => `<span class="rt52-pill up">Favour ${_rt52E(x)}</span>`).join('')}${re.underweight.slice(0, 2).map(x => `<span class="rt52-pill dn">Avoid ${_rt52E(x)}</span>`).join('')}</div></div>`;
  SIGS.forEach((s, i) => { h += _rt52SigCard(s, i); });
  return h + `<p class="rt52-foot">Conviction is the desk’s own 0–100 rating for each view, checked against the live price of the instrument shown. Prices from free feeds; some are delayed.</p>`; }; } catch (e) {}
try { const _p3 = renderP3; renderP3 = function () { _p3.apply(this, arguments); try { const el = document.getElementById('p3body'); if (!el) return;
  const rows = [...el.children].filter(c => c.getAttribute && /_toggleSig\(\d+\)/.test(c.getAttribute('onclick') || ''));
  const hdr = el.firstElementChild; if (hdr && /MARKET SIGNALS/.test(hdr.textContent)) hdr.innerHTML = `<div style="font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:0.15em;padding-top:8px;display:flex;align-items:center;gap:6px">DESK SIGNALS · CONVICTION 0–100 ${_rt52I('sig', '0', 'how signals are scored')}</div>`;
  rows.forEach(r => { const i = Number((r.getAttribute('onclick').match(/\d+/) || [])[0]), s = SIGS[i]; if (!s) return; const g = _rt52Sig(s);
    const box = document.createElement('div'); box.className = 'rt52-p3'; box.innerHTML = `<div class="rt52-sig-w${g.held ? ' held' : ''}">${_rt52E(g.why)}</div><div class="rt52-sig-e">${_rt52E(g.line)} · horizon ${_rt52E(g.hz)}</div>`;
    r.querySelectorAll('div').forEach(d => { if (/^SRC /.test(d.textContent.trim()) && !d.children.length) d.replaceWith(box.cloneNode(true)); if (/^SOURCE .* SYMBOL /.test(d.textContent.trim()) && !d.children.length) d.textContent = `${g.line}`; });
    r.querySelectorAll('span').forEach(sp => { if (!sp.children.length && /^\d{1,3}%$/.test(sp.textContent.trim())) { sp.innerHTML = `${g.cf}<small style="opacity:.6">/100</small> ${_rt52I('sig', i, s.a)}`; } });
    r.querySelectorAll('div').forEach(d => { if (!d.children.length && /^(\d{1,3}%|ON HOLD)$/.test(d.textContent.trim())) d.textContent = g.cf == null ? 'On hold' : `${g.cf}/100`; if (!d.children.length && RT52_HZ[d.textContent.trim()]) d.textContent = RT52_HZ[d.textContent.trim()]; });
    r.querySelectorAll('span').forEach(sp => { if (!sp.children.length && sp.textContent.trim() === 'CONFIDENCE') sp.textContent = 'CONVICTION'; if (!sp.children.length && sp.textContent.trim() === 'TARGET') sp.textContent = 'TYPE'; });
  }); } catch (e) {} }; } catch (e) {}
// 5) Geo Ops: chokepoint and country scores are desk baselines (explained), timeline from live headlines, tiles with as-of and hours
RT52_B.cp = id => { const cp = TD_CHOKEPOINTS.find(c => c.id === id); if (!cp) return null; const sc = _geoCpScore(cp), oilC = liveChg('WTI'), vix = livePx('VIX');
  const how = [`Desk baseline for ${_rt52E(cp.full)}: ${cp.base}. 0 means normal traffic, 100 means the route is shut. The desk sets the baseline from shipping and security reporting; it is not a live feed.`];
  if (cp.id === 'hormuz' || cp.id === 'bab') { how.push(oilC != null ? `Oil adjustment: twice today’s WTI move (${oilC >= 0 ? '+' : '−'}${Math.abs(oilC).toFixed(2)}%), up to 12: +${Math.round(Math.min(12, Math.abs(oilC) * 2) * 10) / 10}` : 'Oil adjustment: no WTI move yet, so none'); how.push(vix != null ? (vix > 20 ? `VIX ${vix.toFixed(1)} is above 20: +4` : `VIX ${vix.toFixed(1)} is 20 or below: no adjustment`) : 'VIX: no price yet'); }
  else how.push('No live adjustment for this route.');
  how.push(`Score now: ${sc}/100 (rounded, capped at 99). 70+ shows red, 40–69 amber, under 40 green.`);
  return { k: 'CHOKEPOINT RISK', t: `${cp.full} · ${sc}/100`, what: `How disrupted the desk judges ${_rt52E(cp.full)} to be, on a 0–100 scale.`, how, src: `Baseline: The Dispatch desk. Live inputs: WTI ${_rt52E(_rt52Src('WTI'))}, VIX ${_rt52E(_rt52Src('VIX'))}`, at: _rt52At(Date.now()),
    why: `Linked holdings: ${_rt52E(cp.tickers.join(', '))}. Disruption here usually lifts oil and shipping costs and weighs on importers.` }; };
RT52_B.cii = iso => { const d = TD_COUNTRY_DOSSIERS[iso]; if (!d) return null;
  return { k: 'COUNTRY STRESS', t: `${d.name} · ${d.cii}/100`, what: `A desk score for how much political and security stress ${_rt52E(d.name)} adds to markets, from 0 (calm) to 100 (crisis).`, how: ['Set by the desk from conflict, sanctions and policy reporting. It is a baseline, not a live index, and does not change during the day.', '70+ shows red, 50–69 amber, under 50 green.'],
    src: 'The Dispatch desk (baseline). Headlines below the score are live.', at: 'Desk baseline', why: `Linked markets: ${_rt52E(d.tickers.join(', '))}.` }; };
try { _paintChokepointStrip = function () { let bar = document.getElementById('chokepointStrip');
  if (!bar) { bar = document.createElement('div'); bar.id = 'chokepointStrip'; const anchor = document.getElementById('siteIntelBar'); if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bar, anchor.nextSibling); else { const ap = document.getElementById('app'); if (ap) ap.appendChild(bar); } }
  const chips = TD_CHOKEPOINTS.map(cp => { const sc = _geoCpScore(cp); return `<button type="button" class="cp-chip" data-rt52b="cp" data-rt52a="${cp.id}" title="${_rt52E(cp.full)}: desk risk ${sc}/100 · tap for how it is scored" aria-label="${_rt52E(cp.full)} risk ${sc} out of 100"><span class="cp-name">${_rt52E(cp.name)}</span><span class="cp-score" style="color:${_geoCpCol(sc)}">${sc}</span><span class="cp-wow" style="color:var(--t3)">/100</span></button>`; }).join('');
  bar.className = 'chokepoint-strip';
  bar.innerHTML = `<div class="cp-strip-inner"><span class="cp-strip-lbl" onclick="nav('geo')">CHOKEPOINT RISK</span><div class="cp-strip-track">${chips}</div><button type="button" class="cp-strip-more" onclick="nav('geo')">GEO OPS →</button></div>`;
  try { _syncDeskChrome(); } catch (e) {} }; } catch (e) {}
try { _renderGeoMacroTiles = function () { const re = _computeRegimeEngine();
  const T = [['VIX', 'VIX', v => v.toFixed(1)], ['DXY', 'DOLLAR (DXY)', v => v.toFixed(2)], ['WTI', 'WTI OIL', v => '$' + v.toFixed(2)], ['XAU', 'GOLD', v => '$' + Math.round(v).toLocaleString('en-GB')], ['TNX', 'US 10Y', v => v.toFixed(2) + '%']];
  const tile = (l, v, c, sub, b, a) => `<button type="button" class="geo-macro-tile rt52-tile" data-rt52b="${b}" data-rt52a="${a}"><div class="geo-macro-l">${l}</div><div class="geo-macro-v" style="color:${c}">${v}</div><div class="rt52-tile-s">${sub}</div></button>`;
  let h = tile('REGIME', re.loading ? '—' : `${_rt52E(re.label)}`, re.col || 'var(--t3)', re.loading ? 'loading' : `${re.score}/100 · ${_rt52At(Date.now())}`, 'regime', '');
  T.forEach(([tk, l, f]) => { const v = livePx(tk), s = _rt52State(tk); const c = v == null ? 'var(--t3)' : tk === 'VIX' ? (v > 20 ? 'var(--rd)' : 'var(--gn)') : tk === 'DXY' ? 'var(--bl)' : tk === 'WTI' ? 'var(--gd)' : tk === 'XAU' ? 'var(--gn)' : 'var(--t2)';
    const sub = v == null ? 'no price yet' : s.open ? (s.at || s.txt) : s.txt; h += tile(l, v == null ? '—' : f(v), c, _rt52E(sub), 'q', tk); });
  return `<div class="geo-macro-tiles">${h}</div><p class="rt52-foot" style="margin-top:-4px">Tap any tile for what it is, its source and hours. Times are ${_rt52E(_rt52TzL())} time.</p>`; }; } catch (e) {}
try { const _ger = _geoEnergyRow; _geoEnergyRow = function (label, tk, fb) { let h = _ger.apply(this, arguments); try { const used = hasSyncedQuote(tk) ? tk : fb && hasSyncedQuote(fb) ? fb : tk; const s = _rt52State(used);
  if (!s.open) h = h.replace(/ · (◌ )?CLOSED<\/span>/, ` · ${_rt52E(s.txt.replace(/^Closed/, 'closed'))}</span>`); h = h.replace('</span></div>', `</span></div><div class="rt52-row-s">${_rt52E(_rt52Src(used))}${s.at ? ' · ' + _rt52E(s.at) : ''}</div>`); } catch (e) {} return h; }; } catch (e) {}
const RT52_GEO = /\b(iran|israel|gaza|hormuz|red sea|houthi|yemen|ukrain|russia|taiwan|china|sanction|missile|strike|ceasefire|attack|opec|tanker|suez|panama canal|militar|troops|war)\b/i;
function _rt52GeoNews(re, n) { try { return (NEWS || []).filter(x => x && x.x && (re || RT52_GEO).test(x.x)).slice(0, n || 6); } catch (e) { return []; } }
try { _renderConflictTimeline = function () { const items = _rt52GeoNews(null, 6);
  let h = `<div class="gc geo-conflict-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">CONFLICT &amp; POLICY HEADLINES</div><span class="pro-feat-badge">Live news</span></div>`;
  if (!items.length) h += `<div class="geo-quake-empty">No conflict or sanctions headlines in the current news feed.</div>`;
  items.forEach(x => { const t = x.ts ? _rt52At(x.ts) : ''; h += `<a class="geo-conflict-row rt52-gn" href="${_escAttr(x.link || '#')}" target="_blank" rel="noopener noreferrer"><span class="geo-conflict-h">${_rt52E(x.x)}</span><span class="geo-conflict-d">${_rt52E([x.src || x.source || '', t].filter(Boolean).join(' · '))}</span></a>`; });
  return h + `<div class="rt52-row-s" style="padding:6px 2px 0">Matched by keyword from the live news feed (${_rt52E(newsLastFetch ? 'updated ' + _rt52At(newsLastFetch.getTime()) : 'loading')}). Open a story for the full report.</div></div>`; }; } catch (e) {}
try { _renderCommodityExposureTable = function () { let h = `<div class="gc geo-commod-card"><div class="pro-feat-hdr"><div class="pro-feat-kicker">COMMODITY ROUTE EXPOSURE</div><span class="pro-feat-badge">Reference figures</span></div><table class="geo-route-table"><thead><tr><th>Route</th><th>Chokepoint</th><th>Approx. share</th><th>Tickers</th></tr></thead><tbody>`;
  TD_COMMODITY_ROUTES.forEach(r => { h += `<tr><td>${r.route}</td><td>${r.choke}</td><td>${r.share}</td><td>${r.tickers.map(t => `<button type="button" class="geo-tk-chip sm" onclick="openA('${t}')">${t}</button>`).join('')}</td></tr>`; });
  return h + `</tbody></table><div class="rt52-row-s" style="padding:6px 2px 0">Approximate shares from published estimates (EIA for Hormuz oil flows; industry estimates for trade and container traffic). Reference only, not live.</div></div>`; }; } catch (e) {}
try { const _cd = _renderCountryDossier; _renderCountryDossier = function (iso) { let h = _cd.apply(this, arguments); const d = TD_COUNTRY_DOSSIERS[iso]; if (!d || !h) return h;
  try { h = h.replace(/<div class="geo-dossier-cii-lbl">CII-LITE STRESS<\/div><div class="geo-dossier-cii-d"[^>]*>[^<]*<\/div>/, `<div class="geo-dossier-cii-lbl">DESK STRESS SCORE /100 ${_rt52I('cii', iso, d.name + ' stress score')}</div><div class="geo-dossier-cii-d" style="color:var(--t3)">Desk baseline, not live</div>`);
    const nm = { IR: 'iran|tehran|hormuz', IL: 'israel|gaza|netanyahu|west bank', UA: 'ukrain|kyiv|zelensk', RU: 'russia|kremlin|putin|moscow', YE: 'yemen|houthi|red sea', SA: 'saudi|opec', CN: 'china|beijing|taiwan|xi jinping' }[iso];
    const hits = nm ? _rt52GeoNews(new RegExp(`\\b(${nm})`, 'i'), 4) : [];
    const live = hits.length ? hits.map(x => `<a class="geo-dossier-sig rt52-gn" href="${_escAttr(x.link || '#')}" target="_blank" rel="noopener noreferrer">${_rt52E(x.x)}<small>${_rt52E([x.src || '', x.ts ? _rt52At(x.ts) : ''].filter(Boolean).join(' · '))}</small></a>`).join('') : `<div class="geo-dossier-sig" style="color:var(--t3)">No ${_rt52E(d.name)} headlines in the current news feed.</div>`;
    const bg = d.signals.filter(s => !/\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b|\$\d/.test(s));
    h = h.replace(/<div class="geo-dossier-sec"><div class="geo-dossier-k">ACTIVE SIGNALS<\/div>[\s\S]*?<\/div>\s*<div class="geo-dossier-sec"><div class="geo-dossier-k">LINKED/, `<div class="geo-dossier-sec"><div class="geo-dossier-k">LATEST HEADLINES · LIVE</div>${live}</div>${bg.length ? `<div class="geo-dossier-sec"><div class="geo-dossier-k">DESK THEMES</div>${bg.map(s => `<div class="geo-dossier-sig">${_rt52E(s)}</div>`).join('')}</div>` : ''}<div class="geo-dossier-sec"><div class="geo-dossier-k">LINKED`); } catch (e) {}
  return h; }; } catch (e) {}
try { const _rge = renderGeoOps; renderGeoOps = function () { let h = _rge.apply(this, arguments);
  try { h = h.replace(/<span style="color:(var\(--(?:rd|gd|gn)\))">(\d+)<\/span><\/button>/g, '<span style="color:$1">$2<small style="opacity:.6">/100</small></span></button>').replace('COUNTRY DOSSIERS · tap to open', 'COUNTRY DOSSIERS · desk stress score /100 · tap to open'); } catch (e) {} return h; }; } catch (e) {}
// 6) Market Lab: scores say what they are; the guide shows on the first visit only
function _rt52Fit(tk) { const re = _computeRegimeEngine(), a = A.find(x => x.tk === tk), chg = liveChg(tk), rows = [['Starting point', 50]];
  if (a && a.se && a.se.includes('Bull') && re.score >= 55) rows.push([`Desk view ${a.se} and regime 55+`, 18]);
  if (a && a.se && a.se.includes('Bear') && re.score < 45) rows.push([`Desk view ${a.se} and regime under 45`, 12]);
  if (a && a.cat === 'Commodity' && re.overweight.some(x => /Energy|Gold|commodit/i.test(x))) rows.push(['Commodity while the regime favours energy or gold', 15]);
  if (a && a.cat === 'Crypto' && re.score >= 58) rows.push(['Crypto with regime 58+', 12]);
  if (a && a.cat === 'Crypto' && re.score < 42) rows.push(['Crypto with regime under 42', -15]);
  if (chg != null && chg > 1.5 && re.score >= 55) rows.push([`Up ${chg.toFixed(2)}% with regime 55+`, 8]);
  if (chg != null && chg < -2) rows.push([`Down ${Math.abs(chg).toFixed(2)}% on the day`, -10]);
  if (re.underweight.some(x => /growth|crypto|beta/i.test(x)) && _rt52BetaOf(tk, a) > 1.5) rows.push([`High beta (${_rt52BetaOf(tk, a)}, desk reference) while the regime avoids high-beta`, -12]);
  return { rows, fit: _tickerRegimeFit(tk, re) }; }
RT52_B.fit = tk => { const g = _rt52Fit(tk); return { k: 'REGIME FIT', t: `${tk} · ${g.fit.score}/100 · ${g.fit.label}`, v: `<table class="rt52-tbl">${g.rows.map(([l, p]) => `<tr><td>${_rt52E(l)}</td><td><b class="${p > 0 && l !== 'Starting point' ? 'rt52-up' : p < 0 ? 'rt52-dn' : ''}">${l === 'Starting point' ? p : (p > 0 ? '+' : '−') + Math.abs(p)}</b></td></tr>`).join('')}<tr class="rt52-sum"><td>Fit (kept between 0 and 100)</td><td><b>${g.fit.score}</b></td></tr></table>`,
  what: 'How well this name suits the current market regime, from 0 to 100. 68+ is regime-aligned, 45–67 a neutral fit, under 45 a headwind.', how: ['Starts at 50; fixed rules add or take points using the regime score, the desk’s view on the name, its asset class, beta and today’s move.'], src: `Regime model plus ${_rt52E(_rt52Src(tk))} for the price`, at: _rt52At(Date.now()), why: 'A quick check before you dig in: a headwind means the name is fighting the current backdrop.' }; };
RT52_B.conv = tk => { const a = A.find(x => x.tk === tk) || {}; return { k: 'DESK SCORE', t: `${tk} · ${a.sc != null ? a.sc + '/100' : '—'}`, what: `The desk’s overall score for ${_rt52E(a.nm || tk)} (${_rt52E(a.se || 'no view')}), from 0 to 100.`, how: ['Set by the desk from the investment case (thesis, valuation, momentum). It does not change with each price tick.'], src: 'The Dispatch desk', at: 'Desk score', why: _rt52E(a.th || '') }; };
try { const _rl = renderLab; renderLab = function () { const h = _rl.apply(this, arguments); try { if (localStorage.getItem('td_lab_guide_v1') == null) localStorage.setItem('td_lab_guide_v1', '1'); } catch (e) {}
  try { return h.replace('<div class="lab-hud-l">CONVICTION · MODEL</div>', `<div class="lab-hud-l">DESK SCORE ${_rt52I('conv', _labTk, 'desk score')}</div>`)
    .replace(/<div class="lab-hud-l">REGIME FIT · MODEL<\/div>(<div class="lab-hud-v"[^>]*>)(\d+)%/, (m, a, n) => `<div class="lab-hud-l">REGIME FIT ${_rt52I('fit', _labTk, 'regime fit')}</div>${a}${n}<small style="opacity:.6">/100</small>`)
    .replace(/(<div class="lab-regime-score">Score \d+\/100)<\/div>/, (m, a) => `${a} ${_rt52I('regime', '', 'regime score')}</div>`); } catch (e) { return h; } }; } catch (e) {}
// 7) Institutional Intelligence: tickers, dollars, change vs the previous quarter, % of portfolio, dates in words
const RT52_ACT = { NEW: ['New position', 'up'], ADDED: ['Added', 'up'], INCREASED: ['Added', 'up'], TRIMMED: ['Trimmed', 'dn'], REDUCED: ['Trimmed', 'dn'], 'SOLD OUT': ['Sold out', 'dn'], REPORTED: ['Held', ''], UNCHANGED: ['Unchanged', ''] };
function _rt52Title(s) { return String(s || '').toLowerCase().replace(/\b([a-z])/g, c => c.toUpperCase()).replace(/\b(Inc|Corp|Co|Ltd|Plc|Llc|Lp|Nv|Sa|Ag)\b\.?/g, m => m).replace(/\bFinl\b/, 'Financial').replace(/\bIntl\b/, 'International').replace(/\bHldgs?\b/, 'Holdings').replace(/\bTr\b/, 'Trust').replace(/\b(Etf|Adr|Spdr|Us|Usa)\b/g, m => m.toUpperCase()); }
function _rt52Mgr(m) { return String(m || 'Fund').replace(/,?\s*(L\.?L\.?C\.?|L\.?P\.?|Inc\.?|LLC|LP)\s*$/i, '').replace(/^The /, ''); }
function _rt52F13(d) { const items = (d && Array.isArray(d.items) ? d.items : []).slice(); const v2 = d && d.version === 2; const by = new Map();
  items.forEach(x => { const k = x.manager || 'Fund'; if (!by.has(k)) by.set(k, []); by.get(k).push(x); });
  if (!v2) by.forEach(rows => { // older server: the value column was multiplied by 1,000 for filers that already report dollars
    const px = rows.filter(r => r.shares > 0 && r.value > 0).map(r => r.value / r.shares).sort((a, b) => a - b), med = px.length ? px[Math.floor(px.length / 2)] : 0;
    if (med > 2000) rows.forEach(r => { if (r.value != null) r.value = r.value / 1000; }); });
  return { by, v2, meta: new Map(((d && d.managers) || []).map(m => [m.manager, m])) }; }
let _rt52F13All = {};
function _rt52F13Row(x, mgr) { const a = RT52_ACT[x.action] || [x.action ? _rt52Title(x.action) : 'Held', ''], nm = _rt52Title(x.security || '');
  const ch = x.sharesChange != null && x.action !== 'NEW' && x.action !== 'SOLD OUT' ? ` (${x.sharesChange > 0 ? '+' : '−'}${_rt52Cnt(Math.abs(x.sharesChange))})` : '';
  const tag = x.action === 'NEW' ? 'New' : x.action === 'SOLD OUT' ? 'Sold out' : x.sharesChangePct != null ? `${a[0]} ${_rt52Pc(x.sharesChangePct)}` : a[0];
  const facts = x.action === 'SOLD OUT' ? [`${_rt52Cnt(x.priorShares)} shares sold`, x.priorValue != null ? `worth ${_rt52Money(x.priorValue)} at ${_rt52E(x.priorQuarter || 'the previous quarter')} end` : ''] : [`${_rt52Cnt(x.shares)} shares${ch}`, x.value != null ? _rt52Money(x.value) : '', x.pctOfPortfolio != null ? `${x.pctOfPortfolio < 0.1 ? '<0.1' : x.pctOfPortfolio}% of portfolio` : ''];
  const q = x.quarter || _rt52Qtr(x.period), who = _rt52Mgr(mgr);
  const why = x.action === 'NEW' ? `${who} opened this position in ${q}${x.pctOfPortfolio != null ? `; it is ${x.pctOfPortfolio}% of what the fund reported` : ''}.`
    : x.action === 'SOLD OUT' ? `${who} exited completely in ${q}.`
    : x.sharesChangePct != null ? `${who} ${x.sharesChange > 0 ? 'raised' : 'cut'} this stake by ${Math.abs(x.sharesChangePct)}% in ${q}${x.pctOfPortfolio != null ? `; it is now ${x.pctOfPortfolio}% of the portfolio` : ''}.`
    : `${who} reported this holding at the end of ${q}.`;
  return `<div class="rt52-f13r"><div class="rt52-f13t"><span class="rt52-tk">${_rt52E(x.ticker || '')}</span><span class="rt52-nm">${_rt52E(nm || '—')}</span><span class="rt52-act ${a[1]}">${_rt52E(tag)}</span></div>
    <div class="rt52-f13f">${facts.filter(Boolean).map(_rt52E).join(' · ')}</div><div class="rt52-f13w">${_rt52E(why)}</div></div>`; }
function _rt52Render13f(d) { const g = _rt52F13(d); let h = '';
  g.by.forEach((rows, mgr) => { const m = g.meta.get(mgr) || {}, x0 = rows[0] || {}, q = m.quarter || x0.quarter || _rt52Qtr(x0.period), all = _rt52F13All[mgr], show = all ? rows : rows.slice(0, 4);
    const stats = [m.portfolioValue || x0.portfolioValue ? `${_rt52Money(m.portfolioValue || x0.portfolioValue)} across ${m.positions || x0.positions} positions` : '', (m.positionsChanged || x0.positionsChanged) != null && (m.priorQuarter || x0.priorQuarter) ? `${m.positionsChanged ?? x0.positionsChanged} changes vs ${m.priorQuarter || x0.priorQuarter}` : ''].filter(Boolean);
    const nt = m.laterNotice || x0.laterNotice;
    h += `<div class="rt52-f13m"><div class="rt52-f13h"><strong>${_rt52E(_rt52Mgr(mgr))}</strong><span>${_rt52E(q)} holdings · quarter end ${_rt52E(_rt52Day(x0.period))} · filed ${_rt52E(_rt52Day(x0.filingDate))}${x0.sourceUrl ? ` · <a href="${_escAttr(x0.sourceUrl)}" target="_blank" rel="noopener noreferrer">filing ↗</a>` : ''}</span>${stats.length ? `<span>${_rt52E(stats.join(' · '))}</span>` : ''}${nt ? `<span class="rt52-warn">The ${_rt52E(_rt52Qtr(nt.period))} holdings were reported under another manager’s filing (13F notice filed ${_rt52E(_rt52Day(nt.filed))}), so ${_rt52E(q)} is the latest here.</span>` : ''}</div>
      ${show.map(x => _rt52F13Row(x, mgr)).join('')}${rows.length > 4 ? `<button type="button" class="news-act rt52-more" onclick="_rt52F13All[${_rt52E(JSON.stringify(mgr)).replace(/&quot;/g, '&quot;')}]=${all ? 'false' : 'true'};_refreshNewsView()">${all ? 'Show fewer' : `Show all ${rows.length} changes`}</button>` : ''}</div>`; });
  return h; }
RT52_B.f13 = () => ({ k: 'SUPER-INVESTOR 13F', t: 'What these rows show', what: 'US managers with more than $100m in US stocks must file Form 13F each quarter, listing what they held on the last day of the quarter. We follow eight well-known funds.',
  how: ['Change = shares at this quarter end vs the previous quarter’s 13F (amendments skipped). New = not held last quarter; Sold out = held last quarter, not now.', 'Value = US dollars as filed (shares × quarter-end price). % of portfolio = this holding ÷ everything the fund reported.', 'Rows are ranked by the size of the change in dollars. Options and bonds are left out. Tickers come from OpenFIGI, with an SEC name match as backup.'],
  src: 'SEC EDGAR (Form 13F-HR), via the Dispatch server', at: (_institutionalData['13f'] && _institutionalData['13f'].asOf) ? `checked ${_rt52At(_institutionalData['13f'].asOf)}` : '—',
  why: 'Filings arrive up to 45 days after the quarter ends, so they show where big investors stood then, not what they own today. Useful for ideas and crowding, not for timing.' });
try { _loadInstitutional = async function (type, force = false) { if (_institutionalLoading[type] || (!force && _institutionalData[type])) return; if (force) _institutionalData[type] = null;
  _institutionalLoading[type] = true; _institutionalError[type] = ''; _refreshNewsView();
  try { const res = await fetch(`/api/institutional-data?type=${encodeURIComponent(type)}&symbols=${encodeURIComponent(_institutionalSymbols())}`, { credentials: 'include', signal: AbortSignal.timeout(type === '13f' ? 40000 : 15000) });
    const data = await res.json().catch(() => ({})); if (!res.ok) throw new Error(data.error || 'The filings service did not answer'); _institutionalData[type] = data;
  } catch (e) { _institutionalError[type] = /abort|timeout/i.test(String(e && (e.name + e.message))) ? 'The filings service is slow right now. Try again in a minute.' : String((e && e.message) || 'The filings service is unavailable'); }
  _institutionalLoading[type] = false; _refreshNewsView(); }; } catch (e) {}
try { _renderInstitutionalIntelligence = function () { const type = _institutionalTab, labels = { insider: 'Insider Form 4', congress: 'Congress', '13f': 'Super-investor 13F' };
  const sub = { insider: 'Company insiders’ own buys and sells (SEC Form 4) for the names in your book', congress: 'Trades disclosed by members of the US Congress', '13f': 'Quarter-end holdings of eight well-known funds (SEC Form 13F)' };
  const d = _institutionalData[type], loading = _institutionalLoading[type], err = _institutionalError[type];
  let h = `<section class="institutional-intel gc"><div class="institutional-head"><div><div class="sec-label">INSTITUTIONAL INTELLIGENCE</div><div class="institutional-sub">${_rt52E(sub[type] || '')}</div></div><button type="button" class="news-act" aria-label="Refresh ${labels[type]} disclosures" onclick="_loadInstitutional('${type}',true)">⟳</button></div><div class="institutional-tabs">${Object.entries(labels).map(([k, v]) => `<button type="button" class="news-act ${k === type ? 'news-act-gold' : ''}" onclick="_setInstitutionalTab('${k}')">${v}</button>`).join('')}</div>`;
  if (loading) h += `<div class="institutional-state">Loading ${labels[type]} filings…</div>`;
  else if (err) h += `<div class="institutional-state unavailable">${_rt52E(err)}</div>`;
  else if (!d) h += `<div class="institutional-state">Choose a disclosure feed to load current public filings.</div>`;
  else if (String(d.status || '').toLowerCase() === 'unavailable') h += `<div class="institutional-state unavailable">${_rt52E(d.note || 'Filings are unavailable right now.')}${d.asOf ? ` · checked ${_rt52E(_rt52At(d.asOf))}` : ''}</div>`;
  else if (!Array.isArray(d.items) || !d.items.length) h += `<div class="institutional-state">No filings returned by ${_rt52E(d.source || 'the provider')}${d.asOf ? ` (checked ${_rt52E(_rt52At(d.asOf))})` : ''}.</div>`;
  else { const partial = type === 'congress' && String(d.status || '').toLowerCase() === 'partial';
    h += `<div class="institutional-asof rt52-asof"><span>${_rt52E(d.source || 'Provider')} · checked ${_rt52E(_rt52At(d.asOf))}${d.note && !partial ? ` · ${_rt52E(d.note)}` : ''}</span>${type === '13f' ? _rt52I('f13', '', '13F rows') : ''}</div>${partial ? `<div class="institutional-warning" role="alert"><strong>PARTIAL CONGRESS FEED</strong>${d.note ? `<span>${_rt52E(d.note)}</span>` : ''}</div>` : ''}`;
    if (type === '13f') h += `<div class="institutional-list rt52-f13">${_rt52Render13f(d)}</div><p class="rt52-foot">Quarter-end snapshots filed up to 45 days later: trades since the quarter end are not shown.</p>`;
    else { h += '<div class="institutional-list">'; d.items.slice(0, 12).forEach(x => { const link = x.sourceUrl ? `<a href="${_escAttr(x.sourceUrl)}" target="_blank" rel="noopener noreferrer">Filing ↗</a>` : '';
      if (type === 'insider') { const px = x.shares > 0 && x.value > 0 ? x.value / x.shares : null; h += `<div class="institutional-row"><strong>${_rt52E(x.ticker || '')}</strong><span>${_rt52E(_rt52Title(x.insider || 'Insider'))}${x.role ? ` · ${_rt52E(x.role)}` : ''}</span><span>${_rt52E(x.transactionType || 'Transaction')}${x.shares != null ? ` · ${_rt52E(_rt52Cnt(x.shares))} shares` : ''}${x.value ? ` · ${_rt52E(_rt52Money(x.value))}` : ''}${px ? ` at $${px.toFixed(2)}` : ''}</span><small>${_rt52E(_rt52Day(x.date))} ${link}</small></div>`; }
      else h += `<div class="institutional-row"><strong>${_rt52E(x.ticker || '')}</strong><span>${_rt52E(x.representative || 'Member of Congress')} · ${_rt52E(x.transactionType || 'Trade')}</span><span>${_rt52E(x.approximateSize || 'Size not disclosed')}</span><small>Disclosed ${_rt52E(_rt52Day(x.disclosureDate))} ${link}</small></div>`; });
      h += '</div>'; } }
  return h + '</section>'; }; } catch (e) {}
// 8) DXY: keep computing from the last USD/SEK price when the SEK poll is rate-limited, hidden or slow after the Sunday open
let _rt52Sek = null; try { const o = JSON.parse(localStorage.getItem('td_rt52_sek') || 'null'); if (o && o.p > 0 && Date.now() - o.ts < 5 * 864e5) _rt52Sek = o; } catch (e) {}
async function _rt52SekPoll() { try { const r = await fetch('/api/yahoo-quote?symbols=SEK%3DX', { signal: AbortSignal.timeout(8000) }); const j = await r.json(); const q = j && j['SEK=X'];
  if (q && q.p > 0) { const ts = _rt43Ms(q.ts) || 0; if (!_rt52Sek || ts >= (_rt52Sek.ts || 0)) { _rt52Sek = { p: q.p, prev: q.prev > 0 ? q.prev : null, ts: ts || Date.now() }; try { localStorage.setItem('td_rt52_sek', JSON.stringify(_rt52Sek)); } catch (e) {} } } } catch (e) {} }
setTimeout(_rt52SekPoll, 1500); setInterval(() => { if (!document.hidden) _rt52SekPoll(); }, 120_000);
function _rt52Dxy() { try {
  if (liveQuoteSrc.DXY === 'dxy-computed' && _rt43Spot.DXY && Date.now() - _rt43Spot.DXY.at < 6000) return; // rt43/rt51 already computing
  if (!_rt18MarketOpen('EURUSD')) return;
  let sek = _rt43Sek && _rt43Sek.p > 0 ? _rt43Sek : null; if (_rt52Sek && (!sek || (_rt52Sek.ts || 0) > (_rt43Ms(sek.ts) || 0))) sek = _rt52Sek; if (!sek) return;
  const sekTs = _rt43Ms(sek.ts) || 0; if (!sekTs || Date.now() - sekTs > 4 * 864e5) return;
  let v = 50.14348112, pv = 50.14348112, tsMin = Infinity;
  for (const [tk, e] of RT43_DXY) { let p, prev, ts;
    if (tk === 'USDSEK') { p = sek.p; prev = sek.prev; ts = null; }
    else { if (!hasSyncedQuote(tk) || !_rt18MarketOpen(tk) || _rt43Stale[tk]) return; p = P[tk].p; prev = BASE[tk] && BASE[tk].p > 0 ? BASE[tk].p : null; ts = _rt43Ms(liveQuoteTs[tk]); if (!(Date.now() - ts < 30 * 60_000)) return; }
    if (!(p > 0)) return; v *= p ** e; pv = pv && prev > 0 ? pv * prev ** e : null; if (ts) tsMin = Math.min(tsMin, ts); }
  _rt51SekOld = Date.now() - sekTs > 10 * 60_000 ? sekTs : 0; _rt43Spot.DXY = { at: Date.now() }; if (liveQuoteSrc.DXY !== 'dxy-computed') liveQuoteTs.DXY = 0;
  _rtApply('DXY', +v.toFixed(3), { src: 'dxy-computed', ts: Math.max(tsMin, Date.now() - 19 * 60_000), prev: pv, proxy: true, name: 'US Dollar Index (computed from live FX)', repaint: true });
} catch (e) {} }
setInterval(_rt52Dxy, 2500);
// 9) decorate shared chrome: regime score and quote labels open their basis; raw dates and timestamps read as words
const RT52_HMS = /\b(as of|AS OF|As of|updated|Updated|UPDATED) (\d\d):(\d\d):\d\d\b(?! ?UK)/g;
const _rt52LdnTz = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone === 'Europe/London'; } catch (e) { return false; } })();
const RT52_ISO = /\b(20\d\d)-(\d\d)-(\d\d)(?:T(\d\d):(\d\d)(?::\d\d(?:\.\d+)?)?(Z|[+-]\d\d:?\d\d)?)?\b/g;
function _rt52Words(t) { return t.replace(RT52_ISO, (m, y, mo, d, hh, mi) => hh ? _rt52At(m) : _rt52Day(m)).replace(RT52_HMS, (m, w, hh, mi) => `${w} ${hh}:${mi}${_rt52LdnTz ? ' UK' : ''}`).replace(/MODEL \(NOT LLM\)/g, 'RULES-BASED MODEL').replace(/\bmodel \(not LLM\)/gi, 'rules-based model'); }
function _rt52Tap(el, id, arg, label) { if (!el || el.getAttribute('data-rt52b')) return; el.setAttribute('data-rt52b', id); el.setAttribute('data-rt52a', arg || ''); if (el.tagName !== 'BUTTON') { el.setAttribute('role', 'button'); el.setAttribute('tabindex', '0'); }
  el.classList.add('rt52-tap'); el.setAttribute('aria-haspopup', 'dialog'); el.title = `${label}: tap for how it is worked out`; }
function _rt52Decorate() { try {
  document.querySelectorAll('.htec-chip-regime:not(.htec-chip-muted),.regime-score,.lab-regime-score').forEach(el => _rt52Tap(el, 'regime', '', 'Regime score'));
  document.querySelectorAll('.desk-letter-tag').forEach(el => { if (/^Score \d+\/100$/.test(el.textContent.trim())) _rt52Tap(el, 'regime', '', 'Regime score'); });
  document.querySelectorAll('.gc-regime').forEach(el => { if (!el.querySelector('.rt52-i')) { const s = [...el.querySelectorAll('div')].find(d => d.textContent.trim() === 'SCORE'); if (s) s.insertAdjacentHTML('beforeend', ' ' + _rt52I('regime', '', 'regime score')); } });
  const root = document.getElementById('app') || document.body; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: n => ((RT52_ISO.lastIndex = 0, RT52_ISO.test(n.nodeValue)) || /NOT LLM/i.test(n.nodeValue) || /\b(?:as of|updated) \d\d:\d\d:\d\d\b/i.test(n.nodeValue)) && !(n.parentElement && n.parentElement.closest('script,style,textarea,input,code,pre,[contenteditable]')) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT });
  const hits = []; let n; while ((n = w.nextNode())) { hits.push(n); if (hits.length > 200) break; } RT52_ISO.lastIndex = 0;
  hits.forEach(t => { const v = _rt52Words(t.nodeValue); RT52_ISO.lastIndex = 0; if (v !== t.nodeValue) t.nodeValue = v; });
  const o = document.getElementById('rt52dlg'); if (o && _rt52Cur && !o.contains(document.activeElement) === false) {}
} catch (e) {} }
setInterval(_rt52Decorate, 1200); setTimeout(_rt52Decorate, 300);
(() => { try { const st = document.createElement('style'); st.id = 'rt52-css'; st.textContent = `
.rt52-i{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;min-width:18px;margin-left:4px;padding:0;border-radius:50%;border:1px solid var(--gb,#2a3346);background:transparent;color:var(--gd,#d4a64a);font:italic 700 11px/1 Georgia,serif;cursor:pointer;vertical-align:middle;position:relative}
.rt52-i::before{content:'';position:absolute;inset:-12px}.rt52-i:hover,.rt52-i:focus-visible{border-color:var(--gd,#d4a64a);outline:none;background:rgba(212,166,74,.1)}
.rt52-tap{cursor:pointer;text-decoration:underline dotted rgba(212,166,74,.55);text-underline-offset:3px}.rt52-tap:focus-visible{outline:2px solid var(--gd,#d4a64a);outline-offset:2px}
.rt52-ov{position:fixed;inset:0;z-index:10060;background:rgba(0,0,0,.62);display:flex;align-items:center;justify-content:center;padding:12px}
@media (max-width:767px){.rt52-ov{align-items:flex-end;padding:0}.rt52-box{border-radius:16px 16px 0 0!important;max-height:88vh!important}}
.rt52-box{width:100%;max-width:480px;max-height:86vh;overflow:auto;background:var(--bg2,#121826);color:var(--t1,#e6e9ef);border:1px solid var(--b2,#2a3346);border-radius:14px;padding:16px 16px 14px;box-shadow:0 10px 40px rgba(0,0,0,.5);font-size:14px;line-height:1.5;font-family:var(--sn,system-ui)}
.rt52-hd{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.rt52-hd h2{margin:2px 0 0;font-size:18px;font-weight:700;font-family:var(--sf,Georgia,serif)}
.rt52-k{font-family:var(--mn,monospace);font-size:10px;letter-spacing:.14em;color:var(--gd,#d4a64a)}
.rt52-x{background:none;border:1px solid var(--b2,#2a3346);color:inherit;border-radius:8px;width:36px;height:36px;font-size:20px;line-height:1;cursor:pointer;flex:none}.rt52-x:focus-visible{outline:2px solid var(--gd,#d4a64a);outline-offset:2px}
.rt52-v{margin:12px 0 4px}.rt52-q{margin:0;color:var(--t2,#c3c9d5);font-style:italic}
.rt52-sec{padding:10px 0 0;margin-top:10px;border-top:1px solid var(--b2,#2a3346)}.rt52-sec p{margin:2px 0 0;color:var(--t2,#c3c9d5);font-size:13.5px}.rt52-sec ul{margin:4px 0 0;padding-left:18px;color:var(--t2,#c3c9d5);font-size:13.5px}.rt52-sec li{margin:3px 0}
.rt52-sl{font-family:var(--mn,monospace);font-size:10px;letter-spacing:.12em;color:var(--t3,#97a0b3);text-transform:uppercase}
.rt52-two{display:grid;grid-template-columns:1.4fr 1fr;gap:12px}.rt52-fine{margin:12px 0 0;color:var(--t3,#97a0b3);font-size:12px}
.rt52-tbl{width:100%;border-collapse:collapse;font-size:13px}.rt52-tbl td{padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}.rt52-tbl td:last-child{text-align:right;font-family:var(--mn,monospace);white-space:nowrap;padding-left:10px}
.rt52-tbl small{display:block;color:var(--t3,#97a0b3);font-size:11.5px}.rt52-sum td{border-bottom:0;font-weight:700;padding-top:8px}.rt52-up{color:var(--gn,#3fbf7f)}.rt52-dn{color:var(--rd,#ef4444)}
.rt52-sig-top{display:flex;justify-content:space-between;align-items:center;gap:8px}.rt52-sig-n{font-size:14px;font-weight:700}.rt52-sig-c{font-family:var(--mn);font-weight:800;font-size:18px;display:inline-flex;align-items:center;white-space:nowrap}.rt52-sig-c small{font-size:10px;opacity:.6;font-weight:600}
.rt52-sig-k{font-family:var(--mn);font-size:8.5px;letter-spacing:.1em;color:var(--t3);margin-top:3px}.rt52-sig-x{font-size:12px;color:var(--t2);line-height:1.5;margin-top:6px}
.rt52-bar{position:relative;height:4px;background:var(--b3,#1f2636);border-radius:2px;margin-top:9px}.rt52-bar i{position:absolute;left:0;top:0;bottom:0;border-radius:2px}.rt52-bar em{position:absolute;top:-3px;width:2px;height:10px;background:var(--t3);border-radius:1px}
.rt52-sig-w{font-size:11.5px;color:var(--t2);margin-top:7px;line-height:1.45}.rt52-sig-w.held{color:var(--gd)}.rt52-sig-e{font-family:var(--mn);font-size:9.5px;color:var(--t3);margin-top:4px;line-height:1.5;overflow-wrap:anywhere}
.rt52-p3{margin-top:4px}.rt52-pill{font-family:var(--mn);font-size:9.5px;padding:3px 8px;border-radius:6px;border:1px solid}.rt52-pill.up{background:var(--gnG);color:var(--gn);border-color:rgba(16,185,129,.2)}.rt52-pill.dn{background:var(--rdG);color:var(--rd);border-color:rgba(239,68,68,.2)}
.rt52-foot{font-size:11px;color:var(--t3);line-height:1.5;margin:8px 2px 12px}
.rt52-tile{text-align:left;cursor:pointer;font:inherit;color:inherit}.rt52-tile:focus-visible{outline:2px solid var(--gd);outline-offset:2px}.rt52-tile-s{font-family:var(--mn);font-size:8.5px;color:var(--t3);margin-top:3px;line-height:1.35;overflow-wrap:anywhere}
.rt52-row-s{font-family:var(--mn);font-size:9px;color:var(--t3);margin:-2px 0 6px}
a.rt52-gn{display:flex;flex-direction:column;gap:2px;text-decoration:none;color:inherit}a.rt52-gn small{font-family:var(--mn);font-size:9px;color:var(--t3)}a.rt52-gn .geo-conflict-d{white-space:normal}
.rt52-asof{display:flex;align-items:center;justify-content:space-between;gap:8px}
.rt52-f13m{padding:10px 0 4px;border-top:1px solid var(--gb)}.rt52-f13m:first-child{border-top:0}.rt52-f13h{display:flex;flex-direction:column;gap:2px;margin-bottom:6px}.rt52-f13h strong{font-size:14px}.rt52-f13h span{font-family:var(--mn);font-size:9.5px;color:var(--t3);line-height:1.5}.rt52-f13h a{color:var(--gd)}
.rt52-warn{color:var(--gd)!important}.rt52-f13r{padding:8px 10px;margin:6px 0;border:1px solid var(--gb);border-radius:8px;background:var(--b1)}
.rt52-f13t{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.rt52-tk{font-family:var(--mn);font-weight:800;font-size:13px;color:var(--tx)}.rt52-tk:empty{display:none}.rt52-nm{font-size:12.5px;color:var(--t2);flex:1;min-width:0}
.rt52-act{font-family:var(--mn);font-size:9.5px;font-weight:700;padding:2px 7px;border-radius:5px;background:var(--b3,#1f2636);color:var(--t2)}.rt52-act.up{background:var(--gnG);color:var(--gn)}.rt52-act.dn{background:var(--rdG);color:var(--rd)}
.rt52-f13f{font-family:var(--mn);font-size:10.5px;color:var(--tx);margin-top:4px}.rt52-f13w{font-size:11.5px;color:var(--t3);margin-top:3px;line-height:1.45}.rt52-more{margin:2px 0 6px}
.cp-chip[data-rt52b]{cursor:pointer}
.rt52-hrs{font-size:12px;color:var(--t3,#97a0b3);margin-top:3px;line-height:1.45}.rt52-gl{margin-top:4px}.rt52-gl summary{cursor:pointer;color:var(--gd,#d4a64a);font-size:12.5px;padding:4px 0;min-height:24px}
.rt52-gl summary:focus-visible{outline:2px solid var(--gd,#d4a64a);outline-offset:2px}.rt52-gl ul{list-style:none;margin:2px 0 0;padding:0;font-size:12.5px}.rt52-gl li{display:flex;gap:6px;flex-wrap:wrap;padding:3px 0!important;border-top:1px dashed rgba(255,255,255,.06)!important}
.rt52-gl li b{font-family:var(--mn,monospace);min-width:62px}.rt52-gl li span{color:var(--t2,#c3c9d5);flex:1;min-width:0}.rt52-gl li em{font-style:normal;color:var(--t3,#97a0b3)}.rt52-gl li em.rt51-ok{color:var(--gn,#3fbf7f)}`; document.head.appendChild(st); } catch (e) {} })();
// 10) one regime-fit result everywhere: beta comes from the desk's reference list (live fundamentals used to replace it on some
// screens only, which is why the same name could read 28 on one device and 40 on another)
const RT52_BETA = {"AAPL":1.18,"NVDA":1.72,"XOM":0.82,"MSFT":0.92,"AVGO":1.28,"TSLA":2.05,"AMZN":1.22,"GOOGL":1.08,"META":1.35,"JPM":1.12,"GS":1.38,"AMD":1.68,"NFLX":1.2,"DIS":1.05,"V":0.92,"MA":0.95,"PYPL":1.38,"CRM":1.18,"ORCL":0.88,"ADBE":1.22,"INTC":1.28,"QCOM":1.32,"MU":1.62,"CSCO":0.82,"NOW":1.08,"PANW":1.18,"CRWD":1.42,"PLTR":2.12,"COIN":3.2,"UBER":1.35,"SHOP":1.65,"SNOW":1.42,"RIVN":2.85,"F":1.38,"GM":1.22,"BA":1.42,"CAT":1.08,"DE":0.95,"NKE":0.92,"SBUX":0.88,"MCD":0.72,"JNJ":0.62,"UNH":0.68,"PFE":0.58,"LLY":0.48,"ABBV":0.62,"MRK":0.55,"WMT":0.52,"COST":0.72,"HD":1.02,"BAC":1.38,"WFC":1.18,"C":1.45,"BLK":1.28,"ISRG":0.92,"TSM":1.22,"ASML":1.18,"NVO":0.45,"SAP":0.82,"BABA":0.92,"BP":0.68,"SHEL":0.72,"ARM":1.85,"SMCI":2.2,"MRVL":1.65,"KO":0.58,"PEP":0.52,"PG":0.48,"ABNB":1.42,"DASH":1.52,"BRKB":0.88,"ACN":1.02,"SONY":0.92,"VALE":1.02,"RIO":0.78,"INFY":0.82,"CAC":1.12,"ASX200":0.85,"KOSPI":1.05,"TMO":0.72,"ABT":0.75,"PM":0.62,"NEE":0.52,"RTX":0.92,"HON":0.95,"T":0.62,"VZ":0.42,"MS":1.42,"SCHW":1.28,"TXN":1.08,"AMAT":1.45,"LRCX":1.55,"REGN":0.52,"AMGN":0.55,"CVX":0.92,"COP":0.98,"INTU":1.18,"ADSK":1.12,"NET":1.42,"DDOG":1.35,"ZS":1.38,"UPS":1.02,"LOW":1.12,"DUK":0.42,"TM":0.72,"NVS":0.48,"UL":0.52,"DEO":0.58,"SPY":1.0,"QQQ":1.15,"IWM":1.25,"RUT":1.25,"EEM":1.1,"SOXX":1.6,"ARKK":1.8,"XLK":1.2,"XLC":1.1,"XLY":1.15,"XLF":1.1,"XLV":0.7,"XLE":0.9,"XLI":1.05,"XLP":0.55,"XLB":1.0,"XLU":0.45,"XLRE":0.85,"RKLB":2.1,"HOOD":2.4,"MSTR":3.5,"GME":2.8,"SPOT":1.5,"LMT":0.65,"BMY":0.45,"GILD":0.42,"ENPH":2.0,"FSLR":1.4,"EOG":1.1,"SLB":1.2,"SO":0.42,"PLD":1.0,"AMT":0.88,"EQIX":0.95,"SPG":1.2,"O":0.75,"VRTX":0.55,"URA":1.3};
function _rt52BetaOf(tk, a) { const b = RT52_BETA[tk]; if (b != null) return b; const n = parseFloat(String(a && a.beta != null ? a.beta : '').replace(/x/i, '')); return isFinite(n) ? n : 0; }
try { _tickerRegimeFit = function (tk, re) { const a = A.find(x => x.tk === tk), chg = liveChg(tk); let score = 50;
  if (a && a.se && a.se.includes('Bull') && re.score >= 55) score += 18;
  if (a && a.se && a.se.includes('Bear') && re.score < 45) score += 12;
  if (a && a.cat === 'Commodity' && re.overweight.some(x => /Energy|Gold|commodit/i.test(x))) score += 15;
  if (a && a.cat === 'Crypto' && re.score >= 58) score += 12;
  if (a && a.cat === 'Crypto' && re.score < 42) score -= 15;
  if (chg != null && chg > 1.5 && re.score >= 55) score += 8;
  if (chg != null && chg < -2) score -= 10;
  if (re.underweight.some(x => /growth|crypto|beta/i.test(x)) && _rt52BetaOf(tk, a) > 1.5) score -= 12;
  score = Math.max(0, Math.min(100, score)); const label = score >= 68 ? 'Regime-aligned' : score >= 45 ? 'Neutral fit' : 'Headwind';
  const chgLbl = chg == null ? 'no price yet' : `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}% ${_rt26Day(tk)}`;
  return { tk, score, label, note: `${label} · regime fit ${score}/100 · ${chgLbl}` }; }; } catch (e) {}
// 11) "What's trading now": the same split at every width, each group's hours, and a per-market list
function _rt52Off(tz, ms) { try { const p = {}; new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).formatToParts(new Date(ms)).forEach(x => p[x.type] = x.value);
  return Math.round((Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute) - ms) / 6e4); } catch (e) { return 0; } }
function _rt52Hm(tz, min) { const now = Date.now(), m = ((min - _rt52Off(tz, now) + _rt52Off(_rt52Tz(), now)) % 1440 + 1440) % 1440; return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`; }
function _rt52Hours(k) { const NY = 'America/New_York', CH = 'America/Chicago', L = _rt52TzL(), H = _rt52Hm;
  if (k === 'crypto') return 'Trades 24 hours a day, 7 days a week.';
  if (k === 'fx') return `Sun ${H(NY, 1020)} to Fri ${H(NY, 1020)} ${L}, round the clock. Some emerging-market pairs only trade in their local day.`;
  if (k === 'cmd') return `Most futures (oil, gold, metals, gas): Sun–Fri ${H(NY, 1080)}–${H(NY, 1020)} ${L}, with a one-hour break. Wheat, corn, soybeans: ${H(CH, 1140)}–${H(CH, 465)} & ${H(CH, 510)}–${H(CH, 800)} ${L}. Coffee ${H(NY, 255)}–${H(NY, 810)}, cocoa ${H(NY, 285)}–${H(NY, 810)}, sugar ${H(NY, 210)}–${H(NY, 780)}, orange juice ${H(NY, 480)}–${H(NY, 840)}, lumber ${H(CH, 540)}–${H(CH, 905)} ${L}, weekdays. Spot gold and silver follow the futures week.`;
  if (k === 'us') return `Mon–Fri ${H(NY, 570)}–${H(NY, 960)} ${L} (regular session).`;
  if (k === 'eu') return `London ${H('Europe/London', 480)}–${H('Europe/London', 990)}, Frankfurt and Paris ${H('Europe/Paris', 540)}–${H('Europe/Paris', 1050)} ${L}, weekdays.`;
  if (k === 'asia') return `Tokyo ${H('Asia/Tokyo', 540)}–${H('Asia/Tokyo', 930)}, Hong Kong ${H('Asia/Hong_Kong', 570)}–${H('Asia/Hong_Kong', 960)}, Seoul ${H('Asia/Seoul', 540)}–${H('Asia/Seoul', 930)}, Sydney ${H('Australia/Sydney', 600)}–${H('Australia/Sydney', 960)}, India ${H('Asia/Kolkata', 555)}–${H('Asia/Kolkata', 930)} ${L}, weekdays.`;
  return ''; }
const _rt52GOpen = new Set();
try { _rt51Label = function (short) { const b = _rt51Brk(); if (!b.priced) return 'Prices loading';
  return `${b.live} trading now · ${b.closed} closed${b.weekend && !short ? ' for the weekend' : ''}${b.quiet ? ` · ${b.quiet} quiet` : ''}`; }; } catch (e) {}
try { _rt51Html = function () { const b = _rt51Brk(); _rt51BC = null; const order = ['crypto', 'fx', 'cmd', 'us', 'eu', 'asia'];
  const rows = order.filter(k => b.g[k]).map(k => b.g[k]).sort((x, y) => (y.live > 0) - (x.live > 0)).map(G => {
    const bits = []; if (G.live) bits.push(`<span class="rt51-ok">${G.live} of ${G.n} trading${G.k === 'crypto' ? ' · 24/7' : ''}</span>`);
    if (G.quiet.length) bits.push(`${G.quiet.length} quiet (open, no new price for 20 min): ${_rt51E(G.quiet.slice(0, 5).join(', '))}${G.quiet.length > 5 ? '…' : ''}`);
    if (G.closed) { const n = G.next.length ? Math.min(...G.next) : 0, m = G.next.length ? Math.max(...G.next) : 0; bits.push(`${G.live || G.quiet.length ? G.closed + ' closed' : 'Closed'}${n ? ` · ${m - n > 9e5 ? 'first reopen' : 'reopens'} ${_rt51E(_rt51When(n))}` : ''}`); }
    if (G.priced < G.n) bits.push(`${G.n - G.priced} without a price yet`);
    const list = A.filter(a => _rt51Grp(a) === G.k).map(a => { let st = 'no price yet', c = '';
      if (hasSyncedQuote(a.tk)) { if (_rt39Live(a.tk)) { st = 'trading'; c = 'rt51-ok'; } else if (_rt18MarketOpen(a.tk)) st = 'quiet'; else { const nx = _rt51Next(a.tk); st = `closed${nx ? ' · opens ' + _rt51When(nx) : ''}`; } }
      return `<li><b>${_rt51E(a.tk)}</b> <span>${_rt51E(a.nm || '')}</span> <em class="${c}">${_rt51E(st)}</em></li>`; }).join('');
    return `<li><div class="rt51-g">${_rt51E(RT51_G[G.k])}</div><div class="rt51-s">${bits.join('<br>')}</div><div class="rt52-hrs">${_rt51E(_rt52Hours(G.k))}</div>
      <details class="rt52-gl" data-g="${G.k}"${_rt52GOpen.has(G.k) ? ' open' : ''}><summary>Show all ${G.n} markets</summary><ul>${list}</ul></details></li>`; }).join('');
  return `<div class="rt51-box" role="dialog" aria-modal="true" aria-labelledby="rt51h"><div class="rt51-hd"><h2 id="rt51h">What's trading now</h2><button type="button" class="rt51-x" aria-label="Close">×</button></div>
    <p class="rt51-sum">${_rt51E(_rt51Label(false))}</p><p class="rt51-at">${_rt51E(_rt51When(Date.now()))} · ${b.priced} of ${b.total} instruments have a price. Each market keeps its own hours (shown in ${_rt51E(_rt52TzL())} time); nothing here is a site-wide close.</p>
    <ul class="rt51-list">${rows}</ul><p class="rt51-fine">“Trading now” means the market is in session and a new price arrived in the last 20 minutes. Free feeds: some prices are delayed (futures about 10 minutes). Exchange holidays are not shown.</p></div>`; }; } catch (e) {}
document.addEventListener('toggle', e => { const d = e.target; if (d && d.classList && d.classList.contains('rt52-gl')) { if (d.open) _rt52GOpen.add(d.dataset.g); else _rt52GOpen.delete(d.dataset.g); } }, true);
window.addEventListener('keydown', e => { if (e.key !== 'Escape') return; if (document.getElementById('rt52dlg')) { e.preventDefault(); e.stopImmediatePropagation(); _rt52Close(); return; }
  if (document.getElementById('rt51dlg')) { e.preventDefault(); e.stopImmediatePropagation(); try { _rt51Close(); } catch (x) {} } }, true);
// 12) the INTEL banner is written only after prices and news have synced; stale "not synced" claims are dropped
const RT52_NOSYNC = /[^.!?]*\b(not (?:yet )?synced|unsynced|awaiting (?:the )?(?:price |data )?feed|gaps in data accuracy|data (?:is|are) (?:not )?(?:yet )?(?:available|synced))\b[^.!?]*[.!?]?/gi;
function _rt52Scrub(v) { if (typeof v === 'string') return v.replace(RT52_NOSYNC, '').replace(/\s{2,}/g, ' ').trim(); if (Array.isArray(v)) return v.map(_rt52Scrub).filter(x => x !== ''); if (v && typeof v === 'object') { const o = {}; Object.keys(v).forEach(k => o[k] = _rt52Scrub(v[k])); return o; } return v; }
try { const _ca = _rt27CleanAi; _rt27CleanAi = function (o) { return _ca.call(this, _rt52Scrub(o)); }; } catch (e) {}
try { const _fa = _fetchSiteIntelAI; let _w = 0; _fetchSiteIntelAI = function (surface, extra) { if ((!priceLastFetch || !newsLastFetch) && _w < 20) { _w++; const a = arguments; setTimeout(() => _fetchSiteIntelAI.apply(this, a), 2000); return Promise.resolve(); } _w = 0; return _fa.apply(this, arguments); }; } catch (e) {}
// 13) news tags: whole words only (no "oil" in "turmoil", "gold" in "Goldman"), and a Bitcoin story is Crypto even if it mentions mining
try { const _kw = {}; detectTag = function (text, feedCat) { const low = ' ' + String(text || '').toLowerCase() + ' '; let best = feedCat || 'Stocks', bestScore = 0; const sc = {};
  for (const [tag, cfg] of Object.entries(TAG_RULES)) { let s = 0; for (const kw of cfg.k) { const re = _kw[kw] || (_kw[kw] = (() => { const k = kw.trim(), e = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); return new RegExp(`${/^[a-z0-9]/i.test(k) ? '(^|[^a-z0-9])' : ''}${e}${/[a-z0-9]$/i.test(k) ? '($|[^a-z0-9])' : ''}`, 'i'); })()); if (re.test(low)) s += cfg.w; } sc[tag] = s; if (s > bestScore) { bestScore = s; best = tag; } }
  if (sc.Crypto > 0 && /(^|[^a-z])(bitcoin|crypto|cryptocurrenc\w*|ethereum|btc|stablecoins?|solana|xrp|dogecoin)([^a-z]|$)/.test(low) && sc.Crypto * 2 > (sc.Commodities || 0)) return 'Crypto';
  if (bestScore === 0 && feedCat) return feedCat; if (bestScore > 0 && bestScore < 3 && feedCat && feedCat !== 'Stocks') return feedCat; return best; }; } catch (e) {}
function _rt52Retag() { try { const cat = {}; (RSS_FEEDS || []).forEach(f => cat[f.src] = f.cat); (NEWS || []).forEach(n => { if (!n || n._rt52) return; n._rt52 = 1; if (!n.x) return; const t = detectTag(n.x + ' ' + (n.desc || ''), cat[n.src] || (n.company ? 'Stocks' : undefined)); if (t && t !== n.tg) n.tg = t; }); } catch (e) {} }
setInterval(_rt52Retag, 1500);
// 14) Academy "In the news" headline cards follow the explainers' refresh rules: rebuilt when 2h+ old or thin, at most 8 a day
let _rt52Nw = { n: 0, at: 0, day: '' };
function _rt52NwNeed() { const N = _rt48Nw || {}, k = Array.isArray(N.cards) ? N.cards.length : 0; return !N.at || Date.now() - N.at > 2 * 36e5 || k < 2; }
function _rt52NwKick() { try { const day = _rt46Day(); if (_rt48AutoDay !== day || (_rt48AutoBusy & 2)) return; if (_rt52Nw.day !== day) _rt52Nw = { n: 0, at: 0, day };
  if (!_rt52NwNeed() || _rt52Nw.n >= 8 || Date.now() - _rt52Nw.at < 15 * 6e4 || !(Array.isArray(NEWS) && NEWS.length)) return;
  _rt52Nw.n++; _rt52Nw.at = Date.now(); const before = JSON.stringify((_rt48Nw.cards || []).map(c => c.h)); _rt48NwBuild();
  const t0 = Date.now(), wait = () => { if ((_rt48AutoBusy & 2) && Date.now() - t0 < 30000) return setTimeout(wait, 800);
    try { if (JSON.stringify((_rt48Nw.cards || []).map(c => c.h)) !== before && _rt47L.id === 'news' && !_rt47L.fin && _rt47L.i === 0) { delete _rt48Sess.news; _rt47L.a = {}; _rt47Redraw(); } else if (_rt47L.id !== 'news') delete _rt48Sess.news; } catch (e) {} };
  setTimeout(wait, 800); } catch (e) {} }
try { const _ak2 = _rt48AutoKick; _rt48AutoKick = function () { const r = _ak2.apply(this, arguments); _rt52NwKick(); return r; }; } catch (e) {}
setInterval(_rt52NwKick, 60000);
// 15) brief archive: older saved briefs get the same clean-up as today's (no "VIX —, SPX —", no "Load sector data")
try { const _gh = _getBriefHistory; _getBriefHistory = function () { const h = _gh.apply(this, arguments); try { return h.map(b => { const c = _rt18BriefClean(b) || b; ['summary', 'houseView', 'headline'].forEach(k => { if (typeof c[k] === 'string') c[k] = c[k].replace(/\b(VIX|SPX|SPY|DXY|BTC|Gold|WTI|Oil)\s*[:=]?\s*\$?—%?[,;.]?/g, '').replace(/Load sector data to see rotation signal\.?/gi, '').replace(/\(\s*[,;·]?\s*\)/g, '').replace(/\s+([,.;])/g, '$1').replace(/([,;])\s*([,;.])/g, '$2').replace(/\s{2,}/g, ' ').trim(); }); return c; }); } catch (e) { return h; } }; } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt52: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
