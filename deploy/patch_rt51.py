#!/usr/bin/env python3
"""patch_rt51.py: chatN -> chatN+1 (client only). Stacks on live chat55 (app.js 296eaebe, rt48e on top).
Appends one block that only wraps existing functions:
- counts explain themselves: "35 trading now · 173 closed for the weekend · 4 quiet" (narrow screens: "35 trading now · 177 not
  trading"); tap or Enter on any count opens a breakdown per market group with each group's next open in the user's time zone;
  hero: "35 trading now · US stocks closed · open Mon 14:30 UK"; sessions pill lists who trades now and the next opens.
  Every group is judged by its own venue hours; never a site-wide "markets closed".
- venue hours: CBOT grains (Sun-Fri 19:00-07:45 and 08:30-13:20 CT), ICE softs (coffee, cocoa, OJ, sugar; ET day sessions),
  CME lumber (09:00-15:05 CT) instead of the 23-hour Globex rule;
- DXY is computed from the live FX pairs even while USD/SEK (4.2% weight) has not traded yet after the Sunday open (last SEK price,
  stated in the detail) instead of falling back to Friday's ICE print;
- the brief's regime score is labelled with the time it was written ("44/100 at 18:05 UK"); when it differs from the live score the
  brief card says "Written 18:05 UK, when the regime read 44/100 · now Risk-Off 37/100".
No server change, no new tables, no Stripe.
Usage: python3 patch_rt48b.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt51 ──' in s: die('rt51 already applied')
if '// ── rt43' not in s and 'function _rt43eReady(' not in s: die('base lacks rt43 (spot/DXY) code')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 55: die('index is %s; expected chat55 or later' % base)
print('base:', base, '(rt48e present)' if '// ── rt48e ──' in s else '(no rt48e)')
for need in ['function _rt18MarketOpenAt(', 'function _rt18Parts(', 'const _rt18OpenCache', 'const _RT18_IDX', 'function _rt39Live(', 'function _rt43eReady(', 'let _rt43Sek', 'const RT43_DXY', 'const _rt43Ms', 'function _rt38Sessions(', 'function _rt37Hero(', 'function _rt37Sum(', 'function _renderLatencyStrip(', 'function _rt18BriefClean(', 'function _rt20Stance(', 'function _rt16BriefWhen(', 'function _rt17Tz(', 'function _quoteMeta(', 'let _brief']:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt51 ── "What's trading now": per-venue counts that explain themselves (trading / quiet / closed, with each group's next open),
// a tap-for-breakdown dialog, venue hours for CBOT grains, ICE softs and CME lumber, a live computed DXY while USD/SEK has not
// traded yet, and the brief's regime score labelled with the time it was written (the header and footer show the live score).
// Never a site-wide "markets closed": every group is judged by its own venue hours.
// 1) venue hours the generic futures rule got wrong (exchange holidays are still not modelled)
const RT51_SOFT = { COFFEE: [255, 810], COCOA: [285, 810], OJ: [480, 840], SUGAR: [210, 780] };
function _rt51Venue(a, d) {
  if (!a || a.cat !== 'Commodity') return null;
  const wk = w => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].includes(w);
  if (a.ex === 'CBOT' || /^(WHEAT|CORN|SOYBEAN|SOYBEANS|SOY|OATS)$/.test(a.tk)) { // Sun-Fri 19:00-07:45 CT and Mon-Fri 08:30-13:20 CT
    const p = _rt18Parts('America/Chicago', d); return (['Sun', 'Mon', 'Tue', 'Wed', 'Thu'].includes(p.wd) && p.m >= 1140) || (wk(p.wd) && (p.m < 465 || (p.m >= 510 && p.m < 800))); }
  if (RT51_SOFT[a.tk]) { const [o, c] = RT51_SOFT[a.tk], p = _rt18Parts('America/New_York', d); return wk(p.wd) && p.m >= o && p.m < c; } // ICE US softs, ET
  if (a.tk === 'LUMBER') { const p = _rt18Parts('America/Chicago', d); return wk(p.wd) && p.m >= 540 && p.m < 905; } // CME lumber 09:00-15:05 CT
  return null;
}
{ const _mo = _rt18MarketOpenAt; _rt18MarketOpenAt = function (tk, d) { try { const v = _rt51Venue(A.find(x => x.tk === tk), d || new Date()); if (v != null) return v; } catch (e) {} return _mo.apply(this, arguments); };
  try { _rt18OpenCache.m = {}; _rt18OpenCache.t = 0; } catch (e) {} }
// 2) computed DXY: USD/SEK (4.2% of the index) is often the last pair to trade after the Sunday open; use its last price meanwhile
let _rt51SekOld = 0;
function _rt51Dxy() { try {
  if (!_rt43Sek || Date.now() - _rt43Sek.at > 10 * 60_000 || !(_rt43Sek.p > 0)) return; const sekTs = _rt43Ms(_rt43Sek.ts) || 0;
  if (Date.now() - sekTs < 10 * 60_000) { _rt51SekOld = 0; return; } // fresh SEK: the rt43 computation already runs
  if (Date.now() - sekTs > 4 * 864e5 || !_rt18MarketOpen('EURUSD')) return;
  let v = 50.14348112, pv = 50.14348112, tsMin = Infinity;
  for (const [tk, e] of RT43_DXY) { let p, prev, ts;
    if (tk === 'USDSEK') { p = _rt43Sek.p; prev = _rt43Sek.prev; ts = null; }
    else { if (!hasSyncedQuote(tk) || !_rt18MarketOpen(tk) || _rt43Stale[tk]) return; p = P[tk].p; prev = BASE[tk] && BASE[tk].p > 0 ? BASE[tk].p : null; ts = _rt43Ms(liveQuoteTs[tk]); if (!(Date.now() - ts < 10 * 60_000)) return; }
    if (!(p > 0)) return; v *= p ** e; pv = pv && prev > 0 ? pv * prev ** e : null; if (ts) tsMin = Math.min(tsMin, ts); }
  _rt51SekOld = sekTs; _rt43Spot.DXY = { at: Date.now() }; if (liveQuoteSrc.DXY !== 'dxy-computed') liveQuoteTs.DXY = 0;
  _rtApply('DXY', +v.toFixed(3), { src: 'dxy-computed', ts: tsMin, prev: pv, proxy: true, name: 'US Dollar Index (computed from live FX)', repaint: true });
} catch (e) {} }
setInterval(_rt51Dxy, 2000);
{ const _qm = _quoteMeta; _quoteMeta = function (tk) { const m = _qm.apply(this, arguments); try { if (tk === 'DXY' && liveQuoteSrc.DXY === 'dxy-computed' && _rt51SekOld && m && m.status === 'live')
  return { ...m, detail: `Computed in your browser from five live FX pairs with the ICE weights, plus the last USD/SEK price (${_rt51When(_rt51SekOld)}; SEK is 4.2% of the index and has not traded since).` }; } catch (e) {} return m; }; }
// 3) one breakdown for every count surface
function _rt51TzL() { const tz = _rt17Tz(); if (tz === 'Europe/London') return 'UK'; try { return (new Intl.DateTimeFormat('en-GB', { timeZone: tz, timeZoneName: 'short' }).formatToParts(new Date()).find(x => x.type === 'timeZoneName') || {}).value || tz; } catch (e) { return tz; } }
function _rt51When(ms) { try { const tz = _rt17Tz(), d = new Date(ms), day = x => new Intl.DateTimeFormat('en-CA', { timeZone: tz }).format(x);
  const hm = new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(d);
  const wd = day(d) === day(new Date()) ? '' : new Intl.DateTimeFormat('en-GB', { timeZone: tz, weekday: 'short' }).format(d) + ' ';
  return `${wd}${hm} ${_rt51TzL()}`; } catch (e) { return ''; } }
const RT51_G = { crypto: 'Crypto', fx: 'Currencies (FX)', cmd: 'Commodities (futures and spot)', us: 'US stocks, ETFs and indices', eu: 'UK and Europe stocks', asia: 'Asia-Pacific stocks' };
function _rt51Grp(a) { if (a.cat === 'Crypto') return 'crypto'; if (a.cat === 'FX' && a.ex !== 'US') return 'fx'; if (a.cat === 'Commodity') return 'cmd';
  const ix = typeof _RT18_IDX !== 'undefined' && _RT18_IDX[a.tk]; if (ix) return /^Europe/.test(ix[0]) ? 'eu' : 'asia';
  if (['LSE', 'XETRA', 'EURONEXT', 'SIX', 'BME', 'BIT'].includes(a.ex)) return 'eu'; if (['TSE', 'HKEX', 'KRX', 'ASX', 'NSE', 'BSE', 'SGX', 'TWSE', 'SSE', 'SZSE'].includes(a.ex)) return 'asia'; return 'us'; }
const _rt51NextC = {};
function _rt51Next(tk) { const now = Date.now(), c = _rt51NextC[tk]; if (c && now - c.at < 60_000 && (!c.v || c.v > now)) return c.v;
  let t = Math.ceil((now + 1) / 9e5) * 9e5, v = 0; try { for (let k = 0; k < 8 * 96; k++, t += 9e5) if (_rt18MarketOpenAt(tk, new Date(t))) { v = t; break; } } catch (e) {}
  _rt51NextC[tk] = { at: now, v }; return v; }
let _rt51BC = null;
function _rt51Brk() { const now = Date.now(); if (_rt51BC && now - _rt51BC.at < 2000) return _rt51BC;
  const g = {}, o = { at: now, total: A.length, priced: 0, live: 0, quiet: 0, closed: 0, g };
  try { const keyNext = {}; A.forEach(a => { const k = _rt51Grp(a), G = g[k] || (g[k] = { k, n: 0, priced: 0, live: 0, quiet: [], closed: 0, next: [] }); G.n++;
    if (!hasSyncedQuote(a.tk)) return; G.priced++; o.priced++;
    const open = _rt18MarketOpen(a.tk); if (_rt39Live(a.tk)) { G.live++; o.live++; } else if (open) { G.quiet.push(a.tk); o.quiet++; } else { G.closed++; o.closed++;
      const hk = a.cat + '|' + a.ex + '|' + (_rt51Venue(a, new Date()) != null || (typeof _RT18_IDX !== 'undefined' && _RT18_IDX[a.tk]) ? a.tk : ''); if (!(hk in keyNext)) keyNext[hk] = _rt51Next(a.tk); if (keyNext[hk]) G.next.push(keyNext[hk]); } }); } catch (e) {}
  try { const p = _rt18Parts('Europe/London', new Date(now)); o.weekend = p.wd === 'Sat' || p.wd === 'Sun'; } catch (e) {}
  return (_rt51BC = o); }
function _rt51Label(short) { const b = _rt51Brk(); if (!b.priced) return 'Prices loading';
  if (short) return `${b.live} trading now · ${b.priced - b.live} not trading`;
  return `${b.live} trading now · ${b.closed} closed${b.weekend ? ' for the weekend' : ''}${b.quiet ? ` · ${b.quiet} quiet` : ''}`; }
function _rt51Narrow() { try { return innerWidth < 768; } catch (e) { return false; } }
function _rt51Ready() { try { return typeof _rt43eReady !== 'function' || _rt43eReady(); } catch (e) { return true; } }
_rt37Sum = function () { if (!_rt51Ready()) return 'Syncing…'; return _rt51Label(_rt51Narrow()); };
try { quoteStatusSummary = function (tickers) { if (!_rt51Ready()) return 'Syncing…'; if (!tickers) return _rt51Label(_rt51Narrow());
  const list = [...new Set(tickers.filter(Boolean))], p = list.filter(t => hasSyncedQuote(t)).length; if (!p) return 'prices loading';
  return `${p} prices · ${list.filter(t => _rt39Live(t)).length} trading now`; }; } catch (e) {}
function _rt51Us() { const b = _rt51Brk(), G = b.g.us; if (!G) return ''; if (G.live || G.quiet.length) return 'US stocks open'; const n = G.next.length ? Math.min(...G.next) : 0; return `US stocks closed${n ? ` · open ${_rt51When(n)}` : ''}`; }
_rt37Hero = function () { const b = _rt51Brk(), out = [`${b.live} trading now`]; const u = _rt51Us(); if (u) out.push(u);
  try { if (hasSyncedQuote('BTC')) out.push(`BTC ${fp('BTC').p}`); } catch (e) {} try { if (hasSyncedQuote('XAU')) out.push(`Gold ${fp('XAU').p}`); } catch (e) {} return out.join(' · '); };
_rt38Sessions = function () { try { const b = _rt51Brk(), G = Object.values(b.g); const nm = { crypto: 'Crypto', fx: 'FX', cmd: 'commodities', us: 'US stocks', eu: 'Europe', asia: 'Asia' };
  const tr = G.filter(x => x.live).map(x => nm[x.k]); const nx = G.filter(x => !x.live && !x.quiet.length && x.next.length).map(x => [x.k, Math.min(...x.next)]).sort((a, b) => a[1] - b[1]);
  const bits = []; if (tr.length) bits.push(`${tr.join(', ').replace(/^./, c => c.toUpperCase())} trading`);
  nx.slice(0, 2).forEach(([k, t]) => bits.push(`${nm[k].replace(/^./, c => c.toUpperCase())} ${k === 'cmd' ? 'from' : 'open'} ${_rt51When(t)}`));
  if (!nx.slice(0, 2).some(x => x[0] === 'us')) { const u = nx.find(x => x[0] === 'us'); if (u) bits.push(`US stocks ${_rt51When(u[1])}`); }
  return bits.join(' · '); } catch (e) { return ''; } };
{ const _ls = _renderLatencyStrip; _renderLatencyStrip = function () { let h = _ls.apply(this, arguments); try { h = h.replace(/\d+ prices · \d+ live/, _rt51Label(_rt51Narrow())); } catch (e) {} return h; }; }
// the breakdown dialog (tap or Enter on any count)
function _rt51E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function _rt51Html() { const b = _rt51Brk(); _rt51BC = null; const order = ['crypto', 'fx', 'cmd', 'us', 'eu', 'asia'];
  const rows = order.filter(k => b.g[k]).map(k => b.g[k]).sort((x, y) => (y.live > 0) - (x.live > 0)).map(G => {
    const bits = []; if (G.live) bits.push(`<span class="rt51-ok">${G.live} of ${G.n} trading${G.k === 'crypto' ? ' · 24/7' : ''}</span>`);
    if (G.quiet.length) bits.push(`${G.quiet.length} quiet (open, no new price for 20 min): ${_rt51E(G.quiet.slice(0, 5).join(', '))}${G.quiet.length > 5 ? '…' : ''}`);
    if (G.closed) { const n = G.next.length ? Math.min(...G.next) : 0, m = G.next.length ? Math.max(...G.next) : 0;
      bits.push(`${G.live || G.quiet.length ? G.closed + ' closed' : 'Closed'}${n ? ` · ${m - n > 9e5 ? 'first reopen' : 'reopens'} ${_rt51E(_rt51When(n))}` : ''}`); }
    if (G.priced < G.n) bits.push(`${G.n - G.priced} without a price yet`);
    return `<li><div class="rt51-g">${_rt51E(RT51_G[G.k])}</div><div class="rt51-s">${bits.join('<br>')}</div></li>`; }).join('');
  return `<div class="rt51-box" role="dialog" aria-modal="true" aria-labelledby="rt51h"><div class="rt51-hd"><h2 id="rt51h">What's trading now</h2><button type="button" class="rt51-x" aria-label="Close">×</button></div>
    <p class="rt51-sum">${_rt51E(_rt51Label(false))}</p><p class="rt51-at">${_rt51E(_rt51When(Date.now()))} · ${b.priced} of ${b.total} instruments have a price. Each market keeps its own hours; nothing here is a site-wide close.</p>
    <ul class="rt51-list">${rows}</ul><p class="rt51-fine">“Trading now” means the market is in session and a new price arrived in the last 20 minutes. Free feeds: some prices are delayed (futures about 10 minutes). Exchange holidays are not shown.</p></div>`; }
let _rt51Back = null;
function _rt51Close() { const o = document.getElementById('rt51dlg'); if (o) o.remove(); try { if (_rt51Back && _rt51Back.isConnected) _rt51Back.focus(); } catch (e) {} _rt51Back = null; }
function _rt51Open(from) { _rt51Close(); _rt51Back = from || document.activeElement; const o = document.createElement('div'); o.id = 'rt51dlg'; o.className = 'rt51-ov'; o.innerHTML = _rt51Html();
  o.addEventListener('click', e => { if (e.target === o || (e.target.closest && e.target.closest('.rt51-x'))) _rt51Close(); });
  o.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); _rt51Close(); } else if (e.key === 'Tab') { e.preventDefault(); o.querySelector('.rt51-x').focus(); } });
  document.body.appendChild(o); o.querySelector('.rt51-x').focus(); }
document.addEventListener('click', e => { const el = e.target && e.target.closest && e.target.closest('.rt51-cnt'); if (!el) return; e.preventDefault(); e.stopPropagation(); _rt51Open(el); }, true);
document.addEventListener('keydown', e => { const el = e.target && e.target.closest && e.target.closest('.rt51-cnt'); if (el && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); _rt51Open(el); } }, true);
setInterval(() => { try { document.querySelectorAll('#statusBar .htec-chip-live,#statusBar .htec-chip-muted,#cmdLive,#latency-strip .latency-pill,.home-tape').forEach(el => {
    if (!/trading now/.test(el.textContent || '')) { if (el.classList.contains('rt51-cnt')) { el.classList.remove('rt51-cnt'); el.removeAttribute('role'); el.removeAttribute('tabindex'); } return; }
    if (!el.classList.contains('rt51-cnt')) { el.classList.add('rt51-cnt'); el.setAttribute('role', 'button'); el.setAttribute('tabindex', '0'); el.setAttribute('aria-haspopup', 'dialog'); el.title = 'What’s trading now: tap for each market’s hours'; } });
  const p1 = document.getElementById('p1sub'); if (p1 && / prices · \d+ live$/.test(p1.textContent)) p1.textContent = p1.textContent.replace(/(\d+) live$/, (m, n) => `${_rt51Brk().live} trading now`);
  const o = document.getElementById('rt51dlg'); if (o) { const s = o.querySelector('.rt51-sum'); if (s && s.textContent !== _rt51Label(false)) { const f = document.activeElement; o.innerHTML = _rt51Html(); o.querySelector('.rt51-x').focus(); } }
} catch (e) {} }, 1500);
(() => { try { const st = document.createElement('style'); st.textContent = `.rt51-cnt{cursor:pointer}.rt51-cnt:focus-visible{outline:2px solid var(--gd,#d4a64a);outline-offset:2px}
.rt51-ov{position:fixed;inset:0;z-index:10050;background:rgba(0,0,0,.62);display:flex;align-items:center;justify-content:center;padding:12px}
.rt51-box{width:100%;max-width:460px;max-height:86vh;overflow:auto;background:var(--bg2,#121826);color:var(--t1,#e6e9ef);border:1px solid var(--b2,#2a3346);border-radius:14px;padding:16px 16px 12px;box-shadow:0 10px 40px rgba(0,0,0,.5);font-size:14px;line-height:1.45}
.rt51-hd{display:flex;align-items:center;justify-content:space-between;gap:8px}.rt51-hd h2{margin:0;font-size:17px;font-weight:700}
.rt51-x{background:none;border:1px solid var(--b2,#2a3346);color:inherit;border-radius:8px;width:36px;height:36px;font-size:20px;line-height:1;cursor:pointer;flex:none}
.rt51-x:focus-visible{outline:2px solid var(--gd,#d4a64a);outline-offset:2px}
.rt51-sum{margin:10px 0 2px;font-weight:600}.rt51-at{margin:0 0 10px;color:var(--t3,#97a0b3);font-size:12.5px}
.rt51-list{list-style:none;margin:0;padding:0}.rt51-list li{padding:9px 0;border-top:1px solid var(--b2,#2a3346)}.rt51-g{font-weight:600}.rt51-s{color:var(--t2,#c3c9d5);font-size:13px;overflow-wrap:anywhere}
.rt51-ok{color:var(--gn,#3fbf7f)}.rt51-fine{margin:10px 0 0;color:var(--t3,#97a0b3);font-size:12px}`; document.head.appendChild(st); } catch (e) {} })();
// 4) the brief's regime score is a snapshot: label it with the time it was written; the header/footer keep the live score
const RT51_SC = /\b((?:regime|composite|overall|market|risk)\s+(?:score|reading)\s+(?:of|at|is|was|reads?|stands at)?\s*|score\s+(?:of|at|is|was|reads?)\s+|regime\s+(?:at|of|reads?)\s+)(\d{1,3})\s*\/\s*100\b(?!\s*(?:at \d|\(at|\(written|when written))/gi;
function _rt51BriefAt(b) { const ts = Date.parse(b && (b.generatedAt || b.asOf || b.createdAt || b.builtAt || '')) || 0; return ts ? _rt51When(ts) : ''; }
function _rt51BriefMark(b) { try { if (!b || typeof b !== 'object' || b._rt51) return b; const at = _rt51BriefAt(b), tag = at ? ` at ${at}` : ' (when written)'; let then = null;
  ['headline', 'summary'].forEach(k => { if (typeof b[k] !== 'string') return; b[k] = b[k].replace(RT51_SC, (m, pre, n, off, s) => { if (/conviction|confidence|fit|quality|\(/i.test(s.slice(Math.max(0, off - 30), off))) return m; if (then == null) then = Number(n); return `${pre}${n}/100${tag}`; }); });
  b._rt51 = 1; b._rt51Then = then; b._rt51At = at; } catch (e) {} return b; }
{ const _bc = _rt18BriefClean; _rt18BriefClean = function (b) { return _rt51BriefMark(_bc.apply(this, arguments)); }; }
setInterval(() => { try { if (_brief && !_brief._rt51) { _rt51BriefMark(_brief); if (typeof renderMain === 'function' && document.querySelector('.home-brief')) renderMain(); } } catch (e) {} }, 1500);
{ const _st = _rt20Stance; _rt20Stance = function (b, re) { try { if (b && b._rt51Then != null && re && !re.loading && re.score != null && Math.abs(b._rt51Then - re.score) >= 2)
  return `Written ${b._rt51At || 'earlier'}, when the regime read ${b._rt51Then}/100 · now ${re.label} ${re.score}/100`; } catch (e) {} return _st.apply(this, arguments); }; }
{ const _bw = _rt16BriefWhen; _rt16BriefWhen = function (b) { try { const at = _rt51BriefAt(b); if (at) return `Written ${at}`; } catch (e) {} return _bw.apply(this, arguments); }; }
'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt51: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
