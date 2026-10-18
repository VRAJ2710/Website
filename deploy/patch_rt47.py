#!/usr/bin/env python3
"""patch_rt47.py: chat47 -> chat48 (client only). Stacks on rt46b output (app.js d9d946cc).
Dispatch Academy: Learn overhaul. Hero with one primary CTA, a 10-lesson learning path (3 units), a bite-sized
lesson player (one idea per screen, swipe/arrow keys, progress dots, sticky thumb-zone nav), inline SVG diagrams
and animations, XP/levels/streak, a daily challenge, "real market now" panels from live site prices, chart drills
on real daily candles (spot the trend, tap support/resistance), and scenario challenges. Reduced-motion aware.
No server change, no DB change. Usage: python3 patch_rt47.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt47 ──' in s: die('rt47 already applied')
if '// ── rt46b ──' not in s: die('base is not rt46b output')
if 'app.js?v=chat47' not in h: die('index.html is not chat47')
for need in ['const _RT45_TABS', 'function renderLearn(', 'function _rt45SyncUrl(', 'function _rt45Tab(', 'function _rt45Open(', 'function _rt45Term(', 'function nav(', 'function _refreshView(', 'function renderMain(', 'const RT46_QUIZ', 'const RT46_BADGES', 'let _rt46P', 'function _rt46Save(', 'function _rt46Card(', 'function _rt46SimHtml(', 'function _rt46Swap(', 'function _rt46Toast(', 'function chartFetch(', 'function fp(', 'function _computeRegimeEngine(']:
    if need not in s: die('missing ' + need)
OLD_T = 'title: "📚 Learn — Financial Education"'
if s.count(OLD_T) == 1: s = s.replace(OLD_T, 'title: "Dispatch Academy · Learn"'); print('overlay title updated')
else: print('note: overlay title anchor not found, left as is')
BLOCK = r'''// ── rt47 ──
// ── rt47 visuals: inline SVG diagrams (decorative text duplicated in the step copy; each has a <title>) ──
const _RT47G = { gd: 'var(--gd)', gn: 'var(--gn)', rd: 'var(--rd)', t2: 'var(--t2)', t3: 'var(--t3)', tx: 'var(--tx)', gb: 'var(--gb)', b2: 'var(--b2)', b3: 'var(--b3)' };
function _rt47Svg(vb, title, body, cls) { return `<svg class="rt47-svg ${cls || ''}" viewBox="${vb}" role="img" aria-label="${_rt47E(title)}" preserveAspectRatio="xMidYMid meet"><title>${_rt47E(title)}</title>${body}</svg>`; }
function _rt47T(x, y, s, o) { o = o || {}; return `<text x="${x}" y="${y}" fill="${o.c || _RT47G.t2}" font-size="${o.fs || 11}" font-family="${o.f === 'm' ? 'var(--mn)' : o.f === 's' ? 'var(--sf)' : 'var(--sn)'}" font-weight="${o.w || 500}" text-anchor="${o.a || 'start'}"${o.cl ? ` class="${o.cl}"` : ''}>${_rt47E(s)}</text>`; }
const RT47_VIZ = {
  candle() {
    return _rt47Svg('0 0 320 210', 'How a candlestick forms: open, high, low and close', `
      <line x1="20" x2="300" y1="190" y2="190" stroke="${_RT47G.gb}"/>
      <g class="rt47-cd-g">
        <line class="rt47-cd-wick" x1="110" x2="110" y1="28" y2="178" stroke="${_RT47G.gn}" stroke-width="2.5" stroke-linecap="round"/>
        <rect class="rt47-cd-body" x="88" y="62" width="44" height="88" rx="3" fill="${_RT47G.gn}"/>
      </g>
      <g class="rt47-cd-lbl">
        <line x1="138" x2="168" y1="150" y2="150" stroke="${_RT47G.t3}" stroke-dasharray="3 3"/>${_rt47T(174, 154, 'Open', { c: _RT47G.tx, w: 700 })}
        <line x1="138" x2="168" y1="62" y2="62" stroke="${_RT47G.t3}" stroke-dasharray="3 3"/>${_rt47T(174, 66, 'Close', { c: _RT47G.tx, w: 700 })}
        <line x1="116" x2="168" y1="28" y2="28" stroke="${_RT47G.t3}" stroke-dasharray="3 3"/>${_rt47T(174, 32, 'High (top of wick)')}
        <line x1="116" x2="168" y1="178" y2="178" stroke="${_RT47G.t3}" stroke-dasharray="3 3"/>${_rt47T(174, 182, 'Low (bottom of wick)')}
      </g>
      ${_rt47T(110, 205, 'Green: closed above the open', { a: 'middle', fs: 10, c: _RT47G.t3 })}`, 'rt47-anim-candle');
  },
  hours() {
    const X = h => 70 + h * 10, row = (y, l, segs, c) => `${_rt47T(4, y + 11, l, { fs: 10.5, c: _RT47G.tx, w: 600 })}${segs.map(([a, b]) => `<rect x="${X(a)}" y="${y}" width="${(b - a) * 10}" height="14" rx="3" fill="${c}" opacity=".85"/>`).join('')}`;
    return _rt47Svg('0 0 320 150', 'Typical trading hours in UK time', `
      ${row(14, 'Crypto', [[0, 24]], _RT47G.gd)}${row(40, 'FX (Mon–Fri)', [[0, 24]], 'var(--t3)')}
      <rect x="${X(13)}" y="38" width="40" height="18" rx="3" fill="none" stroke="${_RT47G.gd}" stroke-width="1.5"/>
      ${row(66, 'London shares', [[8, 16.5]], _RT47G.gn)}${row(92, 'US shares', [[14.5, 21]], _RT47G.gn)}
      ${[0, 6, 12, 18, 24].map(h => `<line x1="${X(h)}" x2="${X(h)}" y1="10" y2="112" stroke="${_RT47G.gb}"/>${_rt47T(X(h), 126, String(h).padStart(2, '0') + ':00', { a: 'middle', fs: 9, f: 'm', c: _RT47G.t3 })}`).join('')}
      ${_rt47T(160, 144, 'UK time, typical. Gold box: London/New York overlap.', { a: 'middle', fs: 9.5, c: _RT47G.t3 })}`);
  },
  ma() {
    const p = [60, 72, 64, 80, 74, 92, 84, 100, 95, 112, 104, 118, 110, 98, 104, 90, 96, 82, 88, 76], pts = p.map((v, i) => [16 + i * 15, 170 - v]);
    const ma = p.map((v, i) => { const s = p.slice(Math.max(0, i - 4), i + 1); return [16 + i * 15, 170 - s.reduce((a, b) => a + b, 0) / s.length]; });
    const d = a => a.map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y.toFixed(1)}`).join(' ');
    return _rt47Svg('0 0 320 170', 'Illustration: a moving average smooths price but turns after it', `
      <path d="${d(pts)}" fill="none" stroke="${_RT47G.t2}" stroke-width="1.6"/>
      <path class="rt47-draw" d="${d(ma)}" fill="none" stroke="${_RT47G.gd}" stroke-width="3" stroke-linecap="round"/>
      ${_rt47T(10, 162, 'Price', { fs: 10, c: _RT47G.t2 })}${_rt47T(54, 162, '5-period average (lags)', { fs: 10, c: _RT47G.gd, w: 700 })}${_rt47T(312, 162, 'Illustration', { a: 'end', fs: 9, c: _RT47G.t3 })}`);
  },
  surprise() {
    return _rt47Svg('0 0 320 170', 'Illustration: the market reacts to the gap between forecast and actual', `
      <line x1="30" x2="290" y1="140" y2="140" stroke="${_RT47G.gb}"/>
      <rect x="70" y="80" width="60" height="60" rx="4" fill="var(--t3)" opacity=".6"/>${_rt47T(100, 158, 'Forecast', { a: 'middle', fs: 11 })}
      <rect class="rt47-grow" x="190" y="38" width="60" height="102" rx="4" fill="${_RT47G.gd}"/>${_rt47T(220, 158, 'Actual', { a: 'middle', fs: 11, c: _RT47G.tx, w: 700 })}
      <line x1="140" x2="182" y1="80" y2="80" stroke="${_RT47G.t3}" stroke-dasharray="3 3"/><line x1="160" x2="160" y1="40" y2="80" stroke="${_RT47G.gd}" stroke-width="2"/>
      <line x1="154" x2="166" y1="40" y2="40" stroke="${_RT47G.gd}" stroke-width="2"/><line x1="154" x2="166" y1="80" y2="80" stroke="${_RT47G.gd}" stroke-width="2"/>
      ${_rt47T(160, 28, 'The surprise moves prices', { a: 'middle', fs: 11, c: _RT47G.gd, w: 700 })}`);
  },
  pmi() {
    const X = v => 30 + (v - 40) * 13;
    return _rt47Svg('0 0 320 110', 'PMI scale: above 50 means expanding, below 50 contracting', `
      <rect x="${X(40)}" y="40" width="${X(50) - X(40)}" height="16" rx="3" fill="${_RT47G.rd}" opacity=".55"/><rect x="${X(50)}" y="40" width="${X(60) - X(50)}" height="16" rx="3" fill="${_RT47G.gn}" opacity=".6"/>
      <line x1="${X(50)}" x2="${X(50)}" y1="30" y2="66" stroke="${_RT47G.tx}" stroke-width="2"/>${_rt47T(X(50), 24, '50', { a: 'middle', fs: 12, w: 700, c: _RT47G.tx, f: 'm' })}
      ${_rt47T(X(45), 84, 'Contracting', { a: 'middle', fs: 11 })}${_rt47T(X(55), 84, 'Expanding', { a: 'middle', fs: 11 })}${_rt47T(X(40), 102, '40', { a: 'middle', fs: 9, f: 'm', c: _RT47G.t3 })}${_rt47T(X(60), 102, '60', { a: 'middle', fs: 9, f: 'm', c: _RT47G.t3 })}`);
  },
  realyield() {
    const bar = (x, h, c, l, v) => `<rect class="rt47-grow" x="${x}" y="${140 - h}" width="56" height="${h}" rx="4" fill="${c}"/>${_rt47T(x + 28, 158, l, { a: 'middle', fs: 10.5 })}${_rt47T(x + 28, 132 - h, v, { a: 'middle', fs: 13, w: 700, c: _RT47G.tx, f: 'm' })}`;
    return _rt47Svg('0 0 320 170', 'Example: a 4.5% bond yield minus 2.5% expected inflation is about a 2% real yield', `
      <line x1="20" x2="300" y1="140" y2="140" stroke="${_RT47G.gb}"/>${bar(30, 90, 'var(--t3)', 'Bond yield', '4.5%')}${_rt47T(110, 100, '−', { a: 'middle', fs: 22, c: _RT47G.t2 })}${bar(132, 50, _RT47G.rd, 'Inflation exp.', '2.5%')}${_rt47T(212, 100, '=', { a: 'middle', fs: 22, c: _RT47G.t2 })}${bar(234, 40, _RT47G.gd, 'Real yield', '≈2.0%')}`);
  },
  seesaw() {
    return _rt47Svg('0 0 320 170', 'Seesaw: when real yields rise, gold tends to fall, and the other way round', `
      <polygon points="160,140 146,162 174,162" fill="var(--t3)"/>
      <g class="rt47-see"><rect x="40" y="134" width="240" height="6" rx="3" fill="${_RT47G.t2}"/>
        <g transform="translate(70 104)"><rect x="-34" y="0" width="68" height="30" rx="6" fill="var(--b3)" stroke="${_RT47G.gb}"/>${_rt47T(0, 19, 'Real yields', { a: 'middle', fs: 11, c: _RT47G.tx, w: 700 })}</g>
        <g transform="translate(250 104)"><rect x="-30" y="0" width="60" height="30" rx="6" fill="${_RT47G.gd}"/>${_rt47T(0, 20, 'Gold', { a: 'middle', fs: 12, c: '#14151A', w: 800 })}</g></g>
      ${_rt47T(160, 22, 'One side up, the other tends to go down', { a: 'middle', fs: 11, c: _RT47G.t2 })}${_rt47T(160, 40, 'A tendency, not a law', { a: 'middle', fs: 9.5, c: _RT47G.t3 })}`, 'rt47-anim-see');
  },
  dxy() {
    const w = [['EUR', 57.6], ['JPY', 13.6], ['GBP', 11.9], ['CAD', 9.1], ['SEK', 4.2], ['CHF', 3.6]], cols = [_RT47G.gd, '#B88E3E', '#8F7444', '#6E6250', '#5A5650', '#4A4A4A'];
    let x = 10; const seg = w.map(([c, v], i) => { const ww = v * 3; const s = `<rect x="${x}" y="40" width="${ww - 1.5}" height="34" fill="${cols[i]}"/>${ww > 30 ? _rt47T(x + ww / 2, 62, c, { a: 'middle', fs: 11, c: i ? _RT47G.tx : '#14151A', w: 800 }) : ''}`; x += ww; return s; }).join('');
    return _rt47Svg('0 0 320 130', 'Dollar index weights: euro 57.6%, yen 13.6%, pound 11.9%, Canadian dollar 9.1%, Swedish krona 4.2%, Swiss franc 3.6%', `
      ${_rt47T(10, 26, 'What the dollar index (DXY) is measured against', { fs: 11, c: _RT47G.t2 })}${seg}
      ${w.map(([c, v], i) => _rt47T(10 + (i % 3) * 104, 98 + Math.floor(i / 3) * 18, `${c} ${v}%`, { fs: 10.5, f: 'm', c: i ? _RT47G.t2 : _RT47G.gd, w: i ? 500 : 700 }))}`);
  },
  pip() {
    return _rt47Svg('0 0 320 130', 'EUR/USD from 1.0850 to 1.0870 is a 20 pip move', `
      ${_rt47T(70, 52, '1.08', { a: 'end', fs: 26, f: 'm', c: _RT47G.t2 })}${_rt47T(70, 52, '50', { fs: 26, f: 'm', c: _RT47G.tx, w: 700 })}
      ${_rt47T(160, 50, '→', { a: 'middle', fs: 22, c: _RT47G.gd })}
      ${_rt47T(260, 52, '1.08', { a: 'end', fs: 26, f: 'm', c: _RT47G.t2 })}${_rt47T(260, 52, '70', { fs: 26, f: 'm', c: _RT47G.gd, w: 700 })}
      <line x1="72" x2="102" y1="62" y2="62" stroke="${_RT47G.tx}" stroke-width="2"/><line x1="262" x2="292" y1="62" y2="62" stroke="${_RT47G.gd}" stroke-width="2"/>
      ${_rt47T(160, 96, '4th decimal = 1 pip (0.0001)', { a: 'middle', fs: 12, c: _RT47G.tx, w: 600 })}${_rt47T(160, 116, '+0.0020 = 20 pips', { a: 'middle', fs: 12, f: 'm', c: _RT47G.gd, w: 700 })}`);
  },
  curve() {
    const X = m => 40 + m * 22;
    return _rt47Svg('0 0 320 180', 'Futures curves: contango slopes up over later months, backwardation slopes down', `
      <line x1="40" x2="300" y1="150" y2="150" stroke="${_RT47G.gb}"/><line x1="40" x2="40" y1="20" y2="150" stroke="${_RT47G.gb}"/>
      <path class="rt47-draw" d="M${X(0)},100 C${X(4)},92 ${X(8)},76 ${X(11)},62" fill="none" stroke="var(--t2)" stroke-width="3"/>${_rt47T(X(11), 54, 'Contango', { a: 'end', fs: 11, c: _RT47G.tx, w: 700 })}
      <path class="rt47-draw" d="M${X(0)},60 C${X(4)},76 ${X(8)},104 ${X(11)},118" fill="none" stroke="${_RT47G.gd}" stroke-width="3"/>${_rt47T(X(11), 136, 'Backwardation', { a: 'end', fs: 11, c: _RT47G.gd, w: 700 })}
      ${_rt47T(170, 170, 'Months ahead →', { a: 'middle', fs: 10, c: _RT47G.t3 })}${_rt47T(14, 86, 'Price', { fs: 10, c: _RT47G.t3 })}`);
  },
  capw() {
    const b = [[90, 'Largest'], [70, ''], [52, ''], [38, ''], [26, ''], [18, ''], [12, ''], [8, ''], [6, ''], [4, 'Smallest']];
    return _rt47Svg('0 0 320 150', 'Illustration: in a cap-weighted index the biggest companies carry the most weight', `
      ${b.map(([h, l], i) => `<rect class="rt47-grow" x="${18 + i * 29}" y="${120 - h}" width="22" height="${h}" rx="3" fill="${i < 3 ? _RT47G.gd : 'var(--t3)'}"/>${l ? _rt47T(29 + i * 29, 138, l, { a: 'middle', fs: 9.5 }) : ''}`).join('')}
      ${_rt47T(160, 16, 'Weight in the index', { a: 'middle', fs: 11, c: _RT47G.t2 })}${_rt47T(312, 148, 'Illustration', { a: 'end', fs: 9, c: _RT47G.t3 })}`);
  },
  supply() {
    const pts = [[2009, 0], [2012.9, 10.5], [2016.5, 15.75], [2020.4, 18.375], [2024.3, 19.6875], [2028.3, 20.34], [2040, 20.9], [2060, 21]];
    const X = y => 30 + (y - 2009) * 5.1, Y = v => 150 - v * 6;
    return _rt47Svg('0 0 320 175', 'Bitcoin supply approaches a 21 million cap, with issuance halving roughly every four years', `
      <line x1="30" x2="310" y1="${Y(21)}" y2="${Y(21)}" stroke="${_RT47G.gd}" stroke-dasharray="4 4"/>${_rt47T(306, Y(21) - 6, '21 million cap', { a: 'end', fs: 10.5, c: _RT47G.gd, w: 700 })}
      <path class="rt47-draw" d="${pts.map(([x, v], i) => `${i ? 'L' : 'M'}${X(x).toFixed(1)},${Y(v).toFixed(1)}`).join(' ')}" fill="none" stroke="${_RT47G.tx}" stroke-width="2.5"/>
      ${[2012.9, 2016.5, 2020.4, 2024.3].map(y => `<circle cx="${X(y)}" cy="${Y(pts.find(p => p[0] === y)[1])}" r="3.5" fill="${_RT47G.gd}"/>`).join('')}
      <line x1="30" x2="310" y1="150" y2="150" stroke="${_RT47G.gb}"/>${[2009, 2020, 2040, 2060].map(y => _rt47T(X(y), 166, String(y), { a: 'middle', fs: 9, f: 'm', c: _RT47G.t3 }))}
      ${_rt47T(150, 100, 'Gold dots: halvings (2012, 2016, 2020, 2024)', { fs: 9.5, c: _RT47G.t3 })}`);
  },
  possize() {
    return _rt47Svg('0 0 320 150', 'Position size equals account times risk percent, divided by the distance from entry to stop', `
      <rect x="10" y="14" width="300" height="56" rx="8" fill="var(--b3)" stroke="${_RT47G.gb}"/>
      ${_rt47T(160, 38, 'Size = (Account × Risk %)', { a: 'middle', fs: 14, c: _RT47G.tx, w: 700, f: 'm' })}${_rt47T(160, 58, '÷ (Entry − Stop)', { a: 'middle', fs: 14, c: _RT47G.gd, w: 700, f: 'm' })}
      ${_rt47T(160, 96, '£10,000 × 1% = £100 at risk', { a: 'middle', fs: 12, c: _RT47G.t2, f: 'm' })}${_rt47T(160, 116, '£100 ÷ £2 stop distance', { a: 'middle', fs: 12, c: _RT47G.t2, f: 'm' })}${_rt47T(160, 138, '= 50 shares', { a: 'middle', fs: 13, c: _RT47G.gd, w: 800, f: 'm' })}`);
  },
  drawdown() {
    const r = [[10, 11.1], [25, 33.3], [50, 100]];
    return _rt47Svg('0 0 320 170', 'Losses need bigger gains to recover: 10% needs 11.1%, 25% needs 33.3%, 50% needs 100%', `
      <line x1="20" x2="300" y1="80" y2="80" stroke="${_RT47G.gb}"/>
      ${r.map(([l, g], i) => { const x = 46 + i * 92; return `<rect class="rt47-grow-dn" x="${x}" y="80" width="30" height="${l * 1.3}" rx="3" fill="${_RT47G.rd}"/><rect class="rt47-grow" x="${x + 34}" y="${80 - g * 0.65}" width="30" height="${g * 0.65}" rx="3" fill="${_RT47G.gn}"/>${_rt47T(x + 15, 80 + l * 1.3 + 14, '−' + l + '%', { a: 'middle', fs: 11, c: _RT47G.rd, w: 700, f: 'm' })}${_rt47T(x + 49, 76 - g * 0.65, '+' + g + '%', { a: 'middle', fs: 11, c: _RT47G.gn, w: 700, f: 'm' })}`; }).join('')}
      ${_rt47T(160, 166, 'Red: the loss · Green: the gain needed to get back', { a: 'middle', fs: 9.5, c: _RT47G.t3 })}`);
  },
  regime() {
    let sc = null, lb = ''; try { const r = _computeRegimeEngine(); if (r && !r.loading && isFinite(r.score)) { sc = Math.max(0, Math.min(100, Math.round(Number(r.score)))); lb = r.label; } } catch (e) {}
    const X = v => 20 + v * 2.8, band = (a, b, c) => `<rect x="${X(a)}" y="50" width="${X(b) - X(a) - 1}" height="16" fill="${c}" opacity=".75"/>`;
    return _rt47Svg('0 0 320 130', `Regime score bands: below 40 Risk-Off, 40 to 54 Transition, 55 to 71 Risk-On (Fragile), 72 and above Risk-On (Strong)${sc != null ? `. Today ${sc}, ${lb}` : ''}`, `
      ${band(0, 40, _RT47G.rd)}${band(40, 55, 'var(--t3)')}${band(55, 72, _RT47G.gd)}${band(72, 100, _RT47G.gn)}
      ${[0, 40, 55, 72, 100].map(v => _rt47T(X(v), 82, String(v), { a: 'middle', fs: 9, f: 'm', c: _RT47G.t3 })).join('')}
      ${[[20, 'Risk-Off'], [47.5, 'Transition'], [63.5, 'On (Fragile)'], [86, 'On (Strong)']].map(([v, l]) => _rt47T(X(v), 100, l, { a: 'middle', fs: 9.5 })).join('')}
      ${sc != null ? `<polygon points="${X(sc)},48 ${X(sc) - 6},37 ${X(sc) + 6},37" fill="${_RT47G.tx}"/>${_rt47T(X(sc), 28, `Today: ${sc} · ${lb}`, { a: X(sc) > 220 ? 'end' : X(sc) < 80 ? 'start' : 'middle', fs: 11.5, c: _RT47G.tx, w: 700 })}` : _rt47T(160, 28, 'Today\'s score appears once market data loads', { a: 'middle', fs: 10, c: _RT47G.t3 })}
      ${_rt47T(160, 122, 'Bands as used by the site\'s regime engine', { a: 'middle', fs: 9, c: _RT47G.t3 })}`);
  },
  hero() {
    // decorative candles, deliberately abstract (no prices)
    const c = [[0, 60, 40, 70, 30, 1], [1, 45, 62, 70, 38, 0], [2, 58, 36, 64, 30, 1], [3, 40, 52, 58, 34, 0], [4, 50, 30, 54, 24, 1], [5, 32, 20, 36, 14, 1], [6, 22, 34, 40, 18, 0], [7, 32, 14, 36, 8, 1]];
    return `<svg class="rt47-hero-art" viewBox="0 0 220 110" aria-hidden="true" focusable="false">${c.map(([i, o, cl, l, h, up]) => { const x = 14 + i * 26; return `<line x1="${x + 7}" x2="${x + 7}" y1="${h + 10}" y2="${l + 30}" stroke="${up ? _RT47G.gd : 'var(--t3)'}" stroke-width="1.5"/><rect class="rt47-hc" style="animation-delay:${i * 90}ms" x="${x}" y="${Math.min(o, cl) + 20}" width="14" height="${Math.max(4, Math.abs(o - cl))}" rx="2" fill="${up ? _RT47G.gd : 'var(--t3)'}"/>`; }).join('')}<path d="M10,96 C60,90 90,70 120,58 S180,26 214,18" fill="none" stroke="${_RT47G.gd}" stroke-width="1.5" stroke-dasharray="3 4" opacity=".7"/></svg>`;
  },
};
const RT47_ICON = {
  table: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M9 10v9"/>',
  candle: '<path d="M8 3v4M8 15v6M16 6v3M16 17v3"/><rect x="5.5" y="7" width="5" height="8" rx="1"/><rect x="13.5" y="9" width="5" height="8" rx="1"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  gold: '<path d="M4 17l3-8h10l3 8z"/><path d="M8 9l1.5-4h5L16 9"/>',
  fx: '<path d="M4 8h13l-3-3M20 16H7l3 3"/>',
  oil: '<path d="M12 3s6 7 6 11a6 6 0 01-12 0c0-4 6-11 6-11z"/>',
  bars: '<path d="M5 20V10M10 20V4M15 20v-7M20 20v-4"/>',
  coin: '<circle cx="12" cy="12" r="8.5"/><path d="M9.5 8.5h4a2 2 0 010 4h-4h4.5a2 2 0 010 4h-4.5zM11 7v2M11 16v2"/>',
  shield: '<path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
  flame: '<path d="M12 3c1 3 5 5 5 10a5 5 0 01-10 0c0-2.5 1.5-3.5 2-5 1 1.5 1.5 2 2.5 2C11 7.5 11 5 12 3z"/>',
  bolt: '<path d="M13 2L5 13h6l-1 9 8-11h-6z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  play: '<path d="M8 5v14l11-7z"/>',
  chart: '<path d="M4 19h16"/><path d="M5 15l4-4 3 3 6-7"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18"/>',
  book: '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/>',
};
function _rt47Ic(k, cls) { return `<svg class="rt47-ic ${cls || ''}" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${RT47_ICON[k] || ''}</svg>`; }
// ── rt47 lessons: one idea per step. q:n = question n of RT46_QUIZ[lesson] ──
const RT47_UNITS = [
  ['Read the screen', 'Prices, charts and the data calendar', ['start-markets-table', 'start-charts', 'start-data']],
  ['Gold & macro', 'The forces behind gold, the dollar and oil', ['start-gold-macro', 'start-fx', 'start-oil']],
  ['Assets & risk', 'Shares, crypto, and protecting your account', ['start-stocks', 'start-crypto', 'start-risk', 'start-dispatch']],
];
const RT47_LESSONS = {
  'start-markets-table': { t: 'Read the markets table', ic: 'table', min: 3, tag: 'How fresh is a price?', steps: [
    { t: 'live', h: 'Every price wears a label', b: 'Each row shows a price and a status chip. The chip tells you how fresh that number is, which matters as much as the number itself. These rows are live from the site right now.', tks: ['BTC', 'BRENT', 'SPX'] },
    { t: 'i', h: 'LIVE versus DELAYED', b: 'LIVE prices stream from a public feed straight into your browser. DELAYED prices come from free sources that publish late. US oil futures (WTI) and Brent, for example, are 10 minutes behind at source.' },
    { t: 'q', n: 1 },
    { t: 'i', h: 'Different markets, different hours', b: 'Bitcoin trades 24/7. Currencies trade around the clock on weekdays. US shares mostly trade 14:30–21:00 UK time. So one row can be LIVE while the next says CLOSED, and nothing is broken.', v: 'hours' },
    { t: 'q', n: 2 },
    { t: 'q', n: 0 },
    { t: 'i', h: 'Pre-market is thin', b: 'Before the opening bell, few shares change hands. Prices can jump and spreads (the gap between buy and sell prices) are wider, so treat early moves with caution.' },
    { t: 'q', n: 3 },
  ] },
  'start-charts': { t: 'Read a price chart', ic: 'candle', min: 4, tag: 'Candles, trend, support', steps: [
    { t: 'i', h: 'One candle, four prices', b: 'A candlestick sums up one period (a day, an hour, five minutes) in four prices: open, high, low and close. Watch one form.', v: 'candle', replay: 1 },
    { t: 'i', h: 'Body and wicks', b: 'The thick body runs from open to close: green if it closed higher than it opened, red if lower. The thin wicks mark the highest and lowest prices of the period.' },
    { t: 'q', n: 0 },
    { t: 'chart', k: 'view', s: 'GC=F', h: 'Real candles: gold', b: 'These are real daily candles for gold futures. Each one is a trading day.' },
    { t: 'i', h: 'Trend first', b: 'Before any pattern, ask the big question. Is price making higher highs and higher lows (an uptrend), lower highs and lower lows (a downtrend), or neither (sideways)?' },
    { t: 'chart', k: 'trend' },
    { t: 'i', h: 'Support and resistance', b: 'Support is a zone where falls have stopped before. Resistance is a zone where rises have stalled. They are areas, not exact lines, and they do break.' },
    { t: 'chart', k: 'support', s: 'GC=F' },
    { t: 'i', h: 'Moving averages lag', b: 'A moving average is the average closing price over the last N periods. It smooths out noise and shows the trend, but it always turns after the price does.', v: 'ma' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'RSI measures momentum', b: 'RSI runs from 0 to 100. Above 70 is often called overbought and below 30 oversold. In strong trends, though, RSI can stay there for weeks.' },
    { t: 'q', n: 1 },
  ] },
  'start-data': { t: 'Data that moves markets', ic: 'calendar', min: 3, tag: 'Surprises, payrolls, PMIs', steps: [
    { t: 'i', h: 'The surprise is the story', b: 'Forecasts are priced in before a release. The move comes from the gap between the actual number and what was expected.', v: 'surprise' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'The big three', b: 'US jobs (non-farm payrolls) usually come out on the first Friday of the month. US CPI inflation is monthly. The Fed\'s FOMC sets rates at eight scheduled meetings a year.' },
    { t: 'q', n: 1 },
    { t: 'q', n: 3 },
    { t: 'i', h: 'PMIs: 50 is the line', b: 'Purchasing managers\' indices survey businesses each month. Above 50 signals expanding activity, below 50 shrinking. They arrive early, before most official data.', v: 'pmi' },
    { t: 'q', n: 2 },
    { t: 'scen', n: 1 },
    { t: 'i', h: 'Check the calendar first', b: 'Before acting on any chart, check what is due today. A big release can override every pattern in seconds.' },
  ] },
  'start-gold-macro': { t: 'Why gold moves', ic: 'gold', min: 4, tag: 'Real yields, the dollar', steps: [
    { t: 'i', h: 'Gold pays nothing', b: 'Gold has no coupon and no dividend. So its biggest competitor is a safe investment that does pay: inflation-protected government bonds.' },
    { t: 'i', h: 'Meet the real yield', b: 'A real yield is a bond yield after expected inflation. A 4.5% yield with 2.5% expected inflation gives a real yield of about 2%.', v: 'realyield' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'The seesaw', b: 'When real yields rise, holding gold means giving up more income elsewhere, so gold tends to fall. When they fall, gold tends to rise. It is a tendency, not a law: heavy central-bank buying has at times outweighed it.', v: 'seesaw' },
    { t: 'q', n: 1 },
    { t: 'sim', k: 'ry', h: 'Try it: move the sliders' },
    { t: 'i', h: 'The dollar matters too', b: 'Gold is priced in US dollars. A stronger dollar makes gold dearer for buyers who use other currencies, which tends to weigh on demand.' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'What is the dollar index?', b: 'DXY measures the dollar against six currencies. The euro is by far the biggest weight, at about 58%.', v: 'dxy' },
    { t: 'q', n: 3 },
    { t: 'live', h: 'Gold, the dollar and yields now', b: 'One day rarely follows the textbook neatly. Read these three together, over weeks rather than hours.', tks: ['XAU', 'DXY', 'TNX'] },
    { t: 'scen', n: 0 },
  ] },
  'start-fx': { t: 'Currencies in four minutes', ic: 'fx', min: 4, tag: 'Pairs, pips, sessions', steps: [
    { t: 'i', h: 'A pair is one price', b: 'EUR/USD at 1.0850 means one euro costs 1.0850 US dollars. The first currency is the base and the second is the quote.' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'Pips', b: 'Most pairs are quoted to four decimal places, and one pip is 0.0001. So 1.0850 to 1.0870 is a 20-pip move. In yen pairs, a pip is 0.01.', v: 'pip' },
    { t: 'q', n: 1 },
    { t: 'i', h: 'Up means the base got stronger', b: 'If USD/JPY rises from 150 to 152, one dollar now buys more yen. The dollar has strengthened against the yen.' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'When FX is busiest', b: 'Currencies trade around the clock on weekdays. Volume peaks when London and New York overlap, roughly 13:00–17:00 UK time.', v: 'hours' },
    { t: 'q', n: 3 },
    { t: 'live', h: 'The majors now', b: 'Check the labels. FX shows CLOSED at weekends.', tks: ['EURUSD', 'USDJPY', 'DXY'] },
    { t: 'scen', n: 5 },
  ] },
  'start-oil': { t: 'Oil: WTI, Brent and the curve', ic: 'oil', min: 4, tag: 'Benchmarks and futures', steps: [
    { t: 'i', h: 'Two benchmarks', b: 'WTI is US crude, delivered at Cushing, Oklahoma. Brent is the North Sea benchmark used to price most of the world\'s oil. Brent usually trades above WTI.' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'A barrel is 42 gallons', b: 'Oil is priced per barrel: 42 US gallons, or about 159 litres.' },
    { t: 'q', n: 3 },
    { t: 'i', h: 'The futures curve', b: 'Futures for later months can trade above today\'s price (contango, typical of a well-supplied market) or below it (backwardation, often a sign of tight supply).', v: 'curve' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'Official prices come later', b: 'The EIA publishes official daily spot prices a few days after the date they cover. They are useful for history, not for watching today\'s market.' },
    { t: 'q', n: 1 },
    { t: 'live', h: 'Crude now', b: 'Both are futures prices from free sources, so they are typically 10 minutes delayed.', tks: ['WTI', 'BRENT'] },
    { t: 'scen', n: 3 },
  ] },
  'start-stocks': { t: 'Indices, ETFs and valuation', ic: 'bars', min: 4, tag: 'S&P 500, beta, P/E', steps: [
    { t: 'i', h: 'Bigger firms count more', b: 'The S&P 500 weights each company by its stock-market value, so the largest firms move the index the most.', v: 'capw' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'An ETF is an index in one trade', b: 'An ETF holds a basket of assets and trades like a single share. SPY tracks the S&P 500 and QQQ tracks the Nasdaq-100.' },
    { t: 'q', n: 1 },
    { t: 'i', h: 'Beta', b: 'Beta compares a share\'s past swings with the market\'s. A beta of 1.5 means it has historically moved about 50% more than the market, both up and down.' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'P/E: the price of profits', b: 'Price divided by earnings per share. A high P/E means investors pay more for each £1 of profit, often because they expect growth. A low P/E is not automatically cheap.' },
    { t: 'q', n: 3 },
    { t: 'sim', k: 'cmp', h: 'Try it: time and compounding' },
    { t: 'live', h: 'US stocks now', b: 'The VIX is the "fear gauge". It is built from S&P 500 option prices and tends to rise when shares fall.', tks: ['SPX', 'QQQ', 'VIX'] },
  ] },
  'start-crypto': { t: 'Crypto without the hype', ic: 'coin', min: 3, tag: 'Supply, stablecoins, risk', steps: [
    { t: 'i', h: 'Built-in scarcity', b: 'Bitcoin\'s supply is capped at 21 million coins. The rate of new issuance halves roughly every four years.', v: 'supply' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'Stablecoins', b: 'A stablecoin aims to hold a steady value, usually one US dollar, using reserves or other mechanisms. It aims to; some have failed.' },
    { t: 'q', n: 1 },
    { t: 'i', h: 'No closing bell', b: 'Crypto trades every minute of every day. So "daily change" usually means the last rolling 24 hours, not the change since a close.' },
    { t: 'q', n: 3 },
    { t: 'i', h: 'Protection is limited', b: 'In the UK, most cryptoassets are not covered by the FSCS or the Financial Ombudsman. If a platform fails, you can lose everything.' },
    { t: 'q', n: 2 },
    { t: 'live', h: 'Crypto now', b: 'Streamed live from public exchange feeds where available.', tks: ['BTC', 'ETH'] },
    { t: 'chart', k: 'trend', s: 'BTC-USD' },
  ] },
  'start-risk': { t: 'Protect your account', ic: 'shield', min: 5, tag: 'Sizing, stops, leverage', steps: [
    { t: 'i', h: 'Risk first, size second', b: 'First decide how much of your account you could lose if you are wrong. Many traders use 1% or less. Then size the position from that.' },
    { t: 'i', h: 'The formula', b: 'Shares = (account × risk %) ÷ (entry − stop). £10,000 × 1% puts £100 at risk. With a £2 gap between entry and stop, that is 50 shares.', v: 'possize' },
    { t: 'q', n: 0 },
    { t: 'sim', k: 'pos', h: 'Try it: size a trade' },
    { t: 'i', h: 'Losses compound against you', b: 'A 10% loss needs an 11% gain to recover, 25% needs 33%, and 50% needs 100%. Small losses are survivable; big ones are not.', v: 'drawdown' },
    { t: 'q', n: 1 },
    { t: 'i', h: 'Stops are not guarantees', b: 'A stop-loss becomes a market order when it is hit. After weekend news, or in fast markets, price can gap through it and you may get a worse fill.' },
    { t: 'q', n: 2 },
    { t: 'i', h: 'Leverage cuts both ways', b: 'UK retail CFD leverage is capped at 30:1 on major FX pairs, 20:1 on gold and major indices, and 5:1 on shares. At 30:1, a 3.3% move against you equals your whole margin.' },
    { t: 'q', n: 3 },
    { t: 'sim', k: 'lev', h: 'Try it: leverage and margin' },
  ] },
  'start-dispatch': { t: 'Use The Dispatch like a desk', ic: 'compass', min: 3, tag: 'Regime, watchlist, routine', steps: [
    { t: 'i', h: 'One number for the backdrop', b: 'The regime score combines market signals into a single 0–100 reading. Below 40 is Risk-Off, 40–54 Transition, 55–71 Risk-On (Fragile), and 72 or more Risk-On (Strong).', v: 'regime' },
    { t: 'q', n: 0 },
    { t: 'i', h: 'Your watchlist', b: 'Tap the ★ on any instrument to add it to your watchlist. Your watchlist, price alerts and Portfolio are stored in this browser.' },
    { t: 'q', n: 1 },
    { t: 'q', n: 2 },
    { t: 'i', h: 'A ten-minute routine', b: 'Read the Brief for the day\'s story. Check the regime and the calendar. Then scan your watchlist. Do it every morning.' },
    { t: 'scen', n: 4 },
  ] },
};
// scenario challenges: usual first reactions (tendencies), with the reason
const RT47_SCEN = [
  ['Fed surprise', 'The Federal Reserve raises rates by 0.50 percentage points. Markets had priced in 0.25.', [
    ['US 2-year yield', 'up', 'Short-dated yields track expected policy rates, which just jumped.'],
    ['US dollar (DXY)', 'up', 'Higher US rates make holding dollars more attractive.'],
    ['Gold', 'down', 'Higher yields raise the cost of holding an asset that pays nothing, and a firmer dollar weighs too.']]],
  ['Hot inflation print', 'US CPI rises 0.6% in the month. Economists expected 0.3%.', [
    ['US 10-year yield', 'up', 'Markets price in more, or longer-lasting, rate rises.'],
    ['S&P 500', 'down', 'Higher rates lower the value of future profits and can squeeze margins.'],
    ['Gold', 'down', 'The usual first reaction: yields and the dollar rise. Over longer periods gold can still benefit from inflation.']]],
  ['Jobs miss', 'US non-farm payrolls show 20,000 jobs added. The forecast was 180,000.', [
    ['US 2-year yield', 'down', 'Markets bring forward expected rate cuts.'],
    ['US dollar (DXY)', 'down', 'Lower expected US rates make the dollar less attractive.'],
    ['Gold', 'up', 'Lower yields and a softer dollar both tend to support gold.']]],
  ['OPEC+ surprise cut', 'OPEC+ announces an unexpected cut to its oil output.', [
    ['Brent crude', 'up', 'Less supply for the same demand.'],
    ['Canadian dollar vs US dollar', 'up', 'Canada is a major oil exporter, and its currency often rises with crude.'],
    ['Airline shares', 'down', 'Fuel is one of airlines\' biggest costs.']]],
  ['Risk-off shock', 'A sudden geopolitical shock hits markets on a quiet morning.', [
    ['S&P 500', 'down', 'Investors cut risk first and ask questions later.'],
    ['VIX ("fear gauge")', 'up', 'Demand for protection pushes option prices up.'],
    ['Gold', 'up', 'Gold often attracts safe-haven buying in shocks.']]],
  ['ECB surprise', 'The European Central Bank signals more rate rises than markets expected. The Fed is unchanged.', [
    ['EUR/USD', 'up', 'Higher expected euro rates support the euro.'],
    ['US dollar index (DXY)', 'down', 'The euro is about 58% of DXY, so a stronger euro pulls the index down.'],
    ['German 10-year yield', 'up', 'Bund yields rise with expected ECB rates.']]],
];
const RT47_CHART_SYMS = [['GC=F', 'Gold futures'], ['^GSPC', 'S&P 500'], ['BTC-USD', 'Bitcoin'], ['DX-Y.NYB', 'US dollar index'], ['EURUSD=X', 'EUR/USD'], ['CL=F', 'WTI crude futures'], ['^FTSE', 'FTSE 100'], ['ETH-USD', 'Ether']];
// ── rt47 logic: Academy home, lesson player, XP/levels/streaks, chart gym, scenarios ──
function _rt47E(s) { return _rt46E(s); }
const _RT47_KEY = 'td_academy_v1';
function _rt47Blank() { return { xp: 0, days: {}, qa: {}, done: {}, scen: {}, chart: { n: 0, ok: 0 }, daily: {} }; }
function _rt47Load() { try { const o = JSON.parse(localStorage.getItem(_RT47_KEY) || '{}'), b = _rt47Blank(); for (const k in b) if (o[k] != null && typeof o[k] === typeof b[k]) b[k] = o[k]; b.xp = Math.max(0, Number(b.xp) || 0); return b; } catch (e) { return _rt47Blank(); } }
let _rt47S = _rt47Load();
function _rt47Save() { try { localStorage.setItem(_RT47_KEY, JSON.stringify(_rt47S)); } catch (e) {} }
const RT47_LEVELS = [[0, 'Novice'], [100, 'Apprentice'], [250, 'Analyst'], [500, 'Strategist'], [900, 'Senior strategist'], [1400, 'Macro pro']];
function _rt47Lvl(xp) { let i = 0; RT47_LEVELS.forEach((l, k) => { if (xp >= l[0]) i = k; }); const c = RT47_LEVELS[i], nx = RT47_LEVELS[i + 1];
  return { n: i + 1, name: c[1], at: c[0], next: nx ? nx[0] : null, pct: nx ? Math.round((xp - c[0]) / (nx[0] - c[0]) * 100) : 100 }; }
function _rt47DayOff(off) { const [y, m, d] = _rt46Day().split('-').map(Number); const t = new Date(Date.UTC(y, m - 1, d - off)); return t.toISOString().slice(0, 10); }
function _rt47Streak() { const D = _rt47S.days, today = !!D[_rt47DayOff(0)]; let n = 0, off = today ? 0 : 1; while (D[_rt47DayOff(off + n)]) n++; return { n, today }; }
function _rt47Done(id) { return (typeof _rt46Passed === 'function' && _rt46Passed(id)) || !!(_rt47S.done[id] && _rt47S.done[id].pass); }
function _rt47Order() { return RT47_UNITS.flatMap(u => u[2]); }
function _rt47Next() { return _rt47Order().find(id => !_rt47Done(id)) || ''; }
function _rt47Num(v) { if (!isFinite(v)) return '—'; const a = Math.abs(v); return v.toLocaleString('en-GB', { minimumFractionDigits: a < 10 ? 4 : a < 1000 ? 2 : 0, maximumFractionDigits: a < 10 ? 4 : a < 1000 ? 2 : 0 }); }
function _rt47Date(t) { try { return new Date(t).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'Europe/London' }); } catch (e) { return ''; } }
// ── XP, celebration ──
let _rt47Prog = 0, _rt47Act = 0, _rt47Sig = '';
function _rt47SigNow() { try { return [_learnTab, _learnSub, _rt47L.id, (typeof pg !== 'undefined' ? pg : ''), IS_DESKTOP() ? 'd' : 'm'].join('|'); } catch (e) { return String(Math.random()); } }
function _rt47Award(n, el) { if (!n) return; const lv0 = _rt47Lvl(_rt47S.xp).n; _rt47S.xp += n; const d = _rt46Day(); _rt47S.days[d] = (_rt47S.days[d] || 0) + n; _rt47Save();
  if (_rt47L.id) _rt47L.xp += n; _rt47Pop('+' + n + ' XP', el);
  const lv = _rt47Lvl(_rt47S.xp); if (lv.n > lv0) { setTimeout(() => _rt46Toast(`Level ${lv.n} reached: ${lv.name}`), 700); _rt47Confetti(); }
  document.querySelectorAll('[data-rt47xp]').forEach(e => { e.innerHTML = `${_rt47Ic('bolt')}<span>${_rt47S.xp} XP</span>`; e.classList.remove('bump'); void e.offsetWidth; e.classList.add('bump'); }); }
function _rt47Pop(txt, el) { try { const p = document.createElement('div'); p.className = 'rt47-pop' + (_rt46RM() ? ' rm' : ''); p.textContent = txt; p.setAttribute('aria-hidden', 'true');
  const r = el && el.getBoundingClientRect ? el.getBoundingClientRect() : null; p.style.left = Math.round(r ? Math.min(window.innerWidth - 90, Math.max(10, r.left + r.width / 2 - 40)) : window.innerWidth / 2 - 40) + 'px'; p.style.top = Math.round(r ? Math.max(70, r.top - 8) : 120) + 'px';
  document.body.appendChild(p); setTimeout(() => p.remove(), 1300); } catch (e) {} }
function _rt47Confetti() { try { if (_rt46RM()) return; const box = document.createElement('div'); box.className = 'rt47-conf'; box.setAttribute('aria-hidden', 'true');
  const cols = ['#D9AE52', '#F1D28C', '#B88E3E', '#6FBF95', '#EDEDE8']; for (let i = 0; i < 34; i++) { const s = document.createElement('i'); s.style.left = (Math.random() * 100) + '%'; s.style.background = cols[i % cols.length]; s.style.animationDelay = (Math.random() * 250) + 'ms'; s.style.setProperty('--dx', ((Math.random() - .5) * 160).toFixed(0) + 'px'); s.style.setProperty('--r', ((Math.random() - .5) * 720).toFixed(0) + 'deg'); box.appendChild(s); }
  document.body.appendChild(box); setTimeout(() => box.remove(), 1900); } catch (e) {} }
// ── live prices ──
const RT47_TKN = { XAU: 'Gold (spot)', DXY: 'US dollar index', TNX: 'US 10-year yield', WTI: 'WTI crude', BRENT: 'Brent crude', BTC: 'Bitcoin', ETH: 'Ether', SPX: 'S&P 500', QQQ: 'Nasdaq-100 ETF', VIX: 'VIX', EURUSD: 'EUR/USD', USDJPY: 'USD/JPY' };
const RT47_TKL = { XAU: 'start-gold-macro', DXY: 'start-fx', TNX: 'start-gold-macro', BRENT: 'start-oil', WTI: 'start-oil', BTC: 'start-crypto', SPX: 'start-stocks' };
function _rt47Q(tk) { try { const d = fp(tk); if (!d || d.status === 'unavailable') return { p: '—', c: null, lb: d && d.label ? d.label : 'LOADING', st: 'na' };
  const c = Number(d.c), st = d.status === 'live' ? 'live' : /closed|rth-close/.test(d.status) ? 'closed' : 'delayed';
  return { p: tk === 'TNX' ? d.p + '%' : d.p, c: isFinite(c) ? c : null, lb: d.label || d.status, st }; } catch (e) { return { p: '—', c: null, lb: '', st: 'na' }; } }
function _rt47QCells(tk) { const q = _rt47Q(tk); return `<span class="rt47-qp">${_rt47E(q.p)}</span><span class="rt47-qc ${q.c == null ? '' : q.c > 0 ? 'up' : q.c < 0 ? 'dn' : ''}">${q.c == null ? '' : (q.c > 0 ? '+' : '') + q.c.toFixed(2) + '%'}</span><span class="rt47-qs ${q.st}">${_rt47E(q.lb)}</span>`; }
function _rt47QRow(tk, link) { const l = link && RT47_TKL[tk]; return `<li class="rt47-qrow"${l ? '' : ''}><span class="rt47-qn">${_rt47E(RT47_TKN[tk] || tk)}</span><span class="rt47-qv" data-rt47tk="${tk}">${_rt47QCells(tk)}</span>${l ? `<button type="button" class="rt47-qgo" onclick="_rt47Open('${l}')" aria-label="Lesson: ${_rt47E(RT47_LESSONS[l].t)}">Learn why →</button>` : ''}</li>`; }
function _rt47Tick() { try { const bn = document.querySelector('.bnav'); const v = bn && bn.offsetHeight ? bn.offsetHeight + 'px' : '55px'; if (document.documentElement.style.getPropertyValue('--rt47bn') !== v) document.documentElement.style.setProperty('--rt47bn', v); } catch (e) {} document.querySelectorAll('[data-rt47tk]').forEach(e => { const h = _rt47QCells(e.dataset.rt47tk); if (e._h !== h) { e.innerHTML = h; e._h = h; } }); }
setInterval(() => { try { _rt47Tick(); } catch (e) {} }, 3000);
// ── real chart data (daily candles via the site's chart proxy) ──
const _rt47CD = {};
function _rt47Fetch(sym) { const c = _rt47CD[sym]; if (c && (c.st !== 'err' || Date.now() - c.at < 30000)) return c;
  _rt47CD[sym] = { st: 'loading', at: Date.now() }; let opts = {}; try { opts = { signal: AbortSignal.timeout(12000) }; } catch (e) {}
  const f = typeof chartFetch === 'function' ? chartFetch : fetch;
  Promise.resolve().then(() => f(`/api/yahoo-chart?symbol=${encodeURIComponent(sym)}&range=6mo&interval=1d`, opts)).then(r => r && r.ok ? r.json() : null).then(j => {
    const r = j && j.chart && j.chart.result && j.chart.result[0], q = r && r.indicators && r.indicators.quote && r.indicators.quote[0], ts = r && r.timestamp; if (!q || !ts) throw new Error('no data');
    const d = { t: [], o: [], h: [], l: [], c: [] };
    ts.forEach((t, i) => { const o = q.open[i], h = q.high[i], l = q.low[i], c = q.close[i]; if ([o, h, l, c].every(v => typeof v === 'number' && isFinite(v) && v > 0)) { d.t.push(t * 1000); d.o.push(o); d.h.push(Math.max(h, o, c)); d.l.push(Math.min(l, o, c)); d.c.push(c); } });
    if (d.c.length < 40) throw new Error('short'); _rt47CD[sym] = { st: 'ok', d, at: Date.now() };
  }).catch(() => { _rt47CD[sym] = { st: 'err', at: Date.now() }; }).finally(() => { try { _rt47Redraw(); } catch (e) {} });
  return _rt47CD[sym]; }
function _rt47Win(d, n) { const s = Math.max(0, d.c.length - n); return { t: d.t.slice(s), o: d.o.slice(s), h: d.h.slice(s), l: d.l.slice(s), c: d.c.slice(s) }; }
function _rt47Trend(c) { const n = c.length, y = c.map(Math.log), xm = (n - 1) / 2, ym = y.reduce((a, b) => a + b, 0) / n; let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { const dx = i - xm, dy = y[i] - ym; sxy += dx * dy; sxx += dx * dx; syy += dy * dy; }
  const b = sxy / sxx, r2 = syy ? sxy * sxy / (sxx * syy) : 0, chg = Math.exp(b * (n - 1)) - 1;
  const k = Math.abs(chg) < 0.02 ? 'side' : chg >= 0.04 && r2 >= 0.4 ? 'up' : chg <= -0.04 && r2 >= 0.4 ? 'down' : null; return { k, chg, r2, b, a: ym - b * xm }; }
function _rt47ChartSvg(w, o) { o = o || {}; const N = w.c.length, W = 340, H = 180, pl = 4, pr = 50, pt = 12, pb = 22;
  let mx = Math.max(...w.h), mn = Math.min(...w.l); const pad = (mx - mn) * 0.07 || mx * 0.01; mx += pad; mn -= pad;
  const X = i => pl + (i + 0.5) * (W - pl - pr) / N, Y = v => pt + (mx - v) / (mx - mn) * (H - pt - pb), cw = Math.max(1.6, (W - pl - pr) / N * 0.64);
  let g = ''; for (let k = 0; k < 4; k++) { const v = mn + (mx - mn) * (k + 0.5) / 4; g += `<line x1="${pl}" x2="${W - pr}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--gb)" stroke-width=".6"/>${_rt47T(W - pr + 4, Y(v) + 3.5, _rt47Num(v), { fs: 9, f: 'm', c: 'var(--t3)' })}`; }
  let cs = ''; for (let i = 0; i < N; i++) { const up = w.c[i] >= w.o[i], col = up ? 'var(--gn)' : 'var(--rd)', y1 = Y(Math.max(w.o[i], w.c[i])), y2 = Y(Math.min(w.o[i], w.c[i]));
    cs += `<g class="${o.sel === i ? 'rt47-csel' : ''}${o.hit === i ? ' rt47-chit' : ''}"><line x1="${X(i).toFixed(1)}" x2="${X(i).toFixed(1)}" y1="${Y(w.h[i]).toFixed(1)}" y2="${Y(w.l[i]).toFixed(1)}" stroke="${col}" stroke-width="1"/><rect x="${(X(i) - cw / 2).toFixed(1)}" y="${y1.toFixed(1)}" width="${cw.toFixed(1)}" height="${Math.max(1, y2 - y1).toFixed(1)}" fill="${col}"/></g>`; }
  let ov = '';
  if (o.fit) { const f = o.fit, ya = Math.exp(f.a), yb = Math.exp(f.a + f.b * (N - 1)); ov += `<line class="rt47-draw" x1="${X(0)}" y1="${Y(ya).toFixed(1)}" x2="${X(N - 1)}" y2="${Y(yb).toFixed(1)}" stroke="var(--gd)" stroke-width="2.5" stroke-dasharray="6 4"/>`; }
  if (o.level != null) ov += `<line x1="${pl}" x2="${W - pr}" y1="${Y(o.level).toFixed(1)}" y2="${Y(o.level).toFixed(1)}" stroke="var(--gd)" stroke-width="2" stroke-dasharray="5 4"/><rect x="${W - pr + 1}" y="${(Y(o.level) - 8).toFixed(1)}" width="${pr - 2}" height="15" rx="3" fill="var(--gd)"/>${_rt47T(W - pr / 2, Y(o.level) + 3.5, _rt47Num(o.level), { a: 'middle', fs: 8.5, f: 'm', c: '#14151A', w: 700 })}`;
  if (o.sel != null && o.level == null) ov += `<line x1="${X(o.sel).toFixed(1)}" x2="${X(o.sel).toFixed(1)}" y1="${pt}" y2="${H - pb}" stroke="var(--tx)" stroke-width="1" stroke-dasharray="2 3" opacity=".7"/>`;
  const dl = `${_rt47T(pl, H - 6, _rt47Date(w.t[0]), { fs: 9, f: 'm', c: 'var(--t3)' })}${_rt47T(W - pr, H - 6, _rt47Date(w.t[N - 1]), { a: 'end', fs: 9, f: 'm', c: 'var(--t3)' })}`;
  return `<svg class="rt47-svg rt47-chart${o.tap ? ' tap' : ''}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${_rt47E(o.label || 'Price chart')}"${o.tap ? ` onclick="_rt47Tap(event,${o.si})"` : ''}><title>${_rt47E(o.label || 'Price chart')}</title>${g}${cs}${ov}${dl}</svg>`; }
// ── lessons and player ──
let _rt47L = { id: '', i: 0, a: {}, xp: 0, fin: false, dir: 0 };
function _rt47DailyN() { return _rt46Hash('daily:' + _rt46Day()) % RT47_SCEN.length; }
function _rt47Meta(id) { if (RT47_LESSONS[id]) return RT47_LESSONS[id];
  if (id === 'gym') return { t: 'Chart gym', ic: 'chart', min: 3, tag: 'Real daily charts', steps: [{ t: 'chart', k: 'trend' }, { t: 'chart', k: 'support', s: 'GC=F' }, { t: 'chart', k: 'resist', s: '^GSPC' }, { t: 'chart', k: 'trend', alt: 1 }] };
  if (id === 'scen') return { t: 'Scenario room', ic: 'spark', min: 4, tag: 'What usually happens next?', steps: RT47_SCEN.map((x, n) => ({ t: 'scen', n })) };
  if (id === 'daily') return { t: 'Daily challenge', ic: 'bolt', min: 1, tag: RT47_SCEN[_rt47DailyN()][0], steps: [{ t: 'scen', n: _rt47DailyN(), daily: 1 }] };
  return null; }
function _rt47Steps(id) { const m = _rt47Meta(id); return m ? [...m.steps, { t: 'end' }] : []; }
try { const q = /^\/learn\/?$/.test(location.pathname) ? new URLSearchParams(location.search).get('lesson') : ''; if (q && _rt47Meta(q)) { _rt47L.id = q; try { _learnTab = 'start'; _learnSub = null; } catch (e) {} } } catch (e) {}
function _rt47Open(id) { if (!_rt47Meta(id)) return; _rt47Prog = Date.now(); try { if (typeof _rt45TipClose === 'function') _rt45TipClose(); } catch (e) {}
  try { if (typeof pg !== 'undefined' && pg !== 'learn' && !document.getElementById('learnOv')) nav('learn'); } catch (e) {}
  _learnTab = 'start'; _learnSub = null; _rt47L = { id, i: 0, a: {}, xp: 0, fin: false, dir: 1 };
  _refreshView(); _rt47Top(); setTimeout(() => { const h = document.getElementById('rt47plh'); if (h) h.focus({ preventScroll: true }); }, 30); }
function _rt47Close() { _rt47Prog = Date.now(); _rt47L = { id: '', i: 0, a: {}, xp: 0, fin: false, dir: 0 }; _refreshView(); _rt47Top(); setTimeout(() => { const b = document.querySelector('.rt47-cta'); if (b) b.focus({ preventScroll: true }); }, 30); }
function _rt47Top() { try { const el = document.getElementById('rt47pl') || document.getElementById('rt47home'); const sc = document.querySelector('#learnOv .term-overlay-body') || null;
  if (sc) sc.scrollTop = 0; const r = el && el.getBoundingClientRect(); if (r && r.top < 0) el.scrollIntoView({ block: 'start' }); else if (!sc) window.scrollTo(0, 0); document.querySelector('.main')?.scrollTo?.(0, 0); } catch (e) {} }
function _rt47Can(i) { const s = _rt47Steps(_rt47L.id)[i], a = _rt47L.a[i]; if (!s) return false;
  if (s.t === 'q') return !!a; if (s.t === 'scen') return !!(a && a.done); if (s.t === 'chart' && s.k !== 'view') return !!(a && (a.done || a.skip)); return true; }
function _rt47Go(i) { const st = _rt47Steps(_rt47L.id); if (i < 0 || i >= st.length) return; if (i > _rt47L.i && !_rt47Can(_rt47L.i)) return;
  _rt47L.dir = i > _rt47L.i ? 1 : -1; _rt47L.i = i; _rt47Prog = Date.now();
  if (st[i].t === 'end') _rt47Finish();
  _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47plh'); _rt47Top(); setTimeout(_rt45SyncUrl, 0); }
function _rt47Finish() { if (_rt47L.fin) return; _rt47L.fin = true; const id = _rt47L.id, st = _rt47Steps(id);
  const qs = st.map((s, i) => [s, i]).filter(([s]) => s.t === 'q'), ok = qs.filter(([s, i]) => _rt47L.a[i] && _rt47L.a[i].ok).length, n = qs.length, need = Math.ceil(n * 2 / 3), pass = n ? ok >= need : true;
  _rt47L.res = { ok, n, need, pass };
  if (RT47_LESSONS[id]) {
    const first = !_rt47S.done[id]; _rt47S.done[id] = { at: Date.now(), pass: pass || !!(_rt47S.done[id] && _rt47S.done[id].pass), best: Math.max(ok, (_rt47S.done[id] && _rt47S.done[id].best) || 0), n }; _rt47Save();
    try { const prev = _rt46P.quiz[id] || { best: 0, passed: false }; const newly = pass && !prev.passed; _rt46P.read[id] = _rt46P.read[id] || Date.now();
      _rt46P.quiz[id] = { best: Math.max(prev.best || 0, ok), n, passed: prev.passed || pass, at: Date.now() }; _rt46Save();
      _rt47L.res.badge = newly ? RT46_BADGES.find(b => b[0] === id) : null; _rt47L.res.grad = newly && _rt46Grad(); } catch (e) {}
    if (pass) _rt47Award(first ? 40 : 10, document.querySelector('.rt47-nav .rt47-go'));
  } else if (id === 'daily') { const d = _rt46Day(); if (!_rt47S.daily[d]) { _rt47S.daily[d] = 1; _rt47Save(); _rt47Award(20, document.querySelector('.rt47-nav .rt47-go')); } }
  if (pass) setTimeout(_rt47Confetti, 120); }
function _rt47Ans(i, oi, el) { const st = _rt47Steps(_rt47L.id), s = st[i]; if (!s || s.t !== 'q' || _rt47L.a[i]) return; const q = RT46_QUIZ[_rt47L.id][s.n], ok = oi === q[2];
  _rt47L.a[i] = { o: oi, ok }; const key = _rt47L.id + ':' + s.n; if (ok && !_rt47S.qa[key]) { _rt47S.qa[key] = 1; _rt47Save(); _rt47Award(10, el); }
  _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47fb'); }
function _rt47Pick(i, r, dir) { const a = _rt47L.a[i] || (_rt47L.a[i] = { pick: {}, done: false }); if (a.done) return; a.pick[r] = dir; _rt46Swap('rt47pl', _rt47PlayerHtml(), `#rt47s${r}${dir}`); }
function _rt47ScenCheck(i, el) { const s = _rt47Steps(_rt47L.id)[i], a = _rt47L.a[i], sc = RT47_SCEN[s.n]; if (!a || a.done || Object.keys(a.pick).length < sc[2].length) return;
  a.done = true; a.ok = sc[2].every((row, r) => a.pick[r] === row[1]); if (a.ok && !_rt47S.scen[s.n]) { _rt47S.scen[s.n] = 1; _rt47Save(); _rt47Award(15, el); }
  _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47fb'); }
function _rt47ChartPick(i, s) { const a = _rt47L.a[i] || (_rt47L.a[i] = {}); if (a.sym) return a.sym; const syms = RT47_CHART_SYMS.map(x => x[0]);
  if (s.k === 'trend') { const order = s.s ? [s.s, ...syms.filter(x => x !== s.s)] : syms; const st = order.map(x => _rt47Fetch(x)); if (st.some(c => c.st === 'loading') && !st.some(c => c.st === 'ok')) return '';
    const clear = order.filter(x => _rt47CD[x].st === 'ok' && _rt47Trend(_rt47Win(_rt47CD[x].d, 60).c).k); if (!clear.length) { if (st.some(c => c.st === 'loading')) return ''; a.fallback = 1; a.sym = order.find(x => _rt47CD[x].st === 'ok') || ''; return a.sym; }
    if (s.s && _rt47CD[s.s].st === 'loading') return ''; a.sym = clear[s.alt ? Math.min(1, clear.length - 1) : 0]; return a.sym; }
  const c = _rt47Fetch(s.s || 'GC=F'); if (c.st === 'loading') return ''; if (c.st === 'ok') { a.sym = s.s || 'GC=F'; return a.sym; }
  const alt = syms.find(x => (_rt47Fetch(x)).st === 'ok'); if (alt) a.sym = alt; return a.sym || ''; }
function _rt47Name(sym) { return (RT47_CHART_SYMS.find(x => x[0] === sym) || [sym, sym])[1]; }
function _rt47Trd(i, k, el) { const a = _rt47L.a[i]; if (!a || a.done || !a.sym) return; const w = _rt47Win(_rt47CD[a.sym].d, 60), f = _rt47Trend(w.c);
  a.done = true; a.k = k; a.ok = k === f.k; _rt47S.chart.n++; if (a.ok) _rt47S.chart.ok++; _rt47Save(); if (a.ok) _rt47Award(15, el); _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47fb'); }
function _rt47Tap(ev, i) { try { const a = _rt47L.a[i]; if (!a || a.done || !a.sym) return; const svg = ev.currentTarget, r = svg.getBoundingClientRect(), w = _rt47Win(_rt47CD[a.sym].d, 60), N = w.c.length;
  let x = (ev.clientX - r.left) / r.width * 340; try { const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; x = pt.matrixTransform(svg.getScreenCTM().inverse()).x; } catch (e) {} const idx = Math.max(0, Math.min(N - 1, Math.floor((x - 4) / ((340 - 54) / N)))); a.sel = idx; _rt47SupCheck(i, svg); } catch (e) {} }
function _rt47SupSel(i, v) { const a = _rt47L.a[i]; if (!a || a.done) return; a.sel = Number(v); const b = document.getElementById('rt47chartbox'); if (b) { const s = _rt47Steps(_rt47L.id)[i]; b.innerHTML = _rt47ChartBox(s, i); } const r = document.getElementById('rt47pick'); if (r) { const w = _rt47Win(_rt47CD[a.sym].d, 60); r.setAttribute('aria-valuetext', `${_rt47Date(w.t[a.sel])}: high ${_rt47Num(w.h[a.sel])}, low ${_rt47Num(w.l[a.sel])}`); } }
function _rt47SupCheck(i, el) { const a = _rt47L.a[i], s = _rt47Steps(_rt47L.id)[i]; if (!a || a.done || a.sel == null) return; const w = _rt47Win(_rt47CD[a.sym].d, 60), res = s.k === 'resist';
  const tgt = res ? w.h.indexOf(Math.max(...w.h)) : w.l.indexOf(Math.min(...w.l)), lvl = res ? w.h[tgt] : w.l[tgt];
  a.ok = Math.abs(a.sel - tgt) <= 2 || (res ? w.h[a.sel] >= lvl * 0.99 : w.l[a.sel] <= lvl * 1.01); a.done = true; a.tgt = tgt; a.lvl = lvl; _rt47S.chart.n++; if (a.ok) _rt47S.chart.ok++; _rt47Save(); if (a.ok) _rt47Award(15, el);
  _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47fb'); }
function _rt47Skip(i) { const a = _rt47L.a[i] || (_rt47L.a[i] = {}); a.skip = true; _rt47Go(i + 1); }
function _rt47ChartBox(s, i) { const a = _rt47L.a[i] || {}, w = _rt47Win(_rt47CD[a.sym].d, s.k === 'view' ? 30 : 60), nm = _rt47Name(a.sym), res = s.k === 'resist';
  if (s.k === 'view') return _rt47ChartSvg(w, { label: `${nm}: last ${w.c.length} daily candles` });
  if (s.k === 'trend' && !a.fallback) return _rt47ChartSvg(w, { label: `${nm}: last ${w.c.length} daily candles`, fit: a.done ? _rt47Trend(w.c) : null });
  return _rt47ChartSvg(w, { label: `${nm}: last ${w.c.length} daily candles. ${res ? 'Find the highest high' : 'Find the lowest low'}`, tap: !a.done, si: i, sel: a.sel, hit: a.done ? a.tgt : null, level: a.done ? a.lvl : null }); }
function _rt47StepHtml(s, i) { const id = _rt47L.id, a = _rt47L.a[i];
  const H = (h, k) => `${k ? `<div class="rt47-sk">${k}</div>` : ''}<h1 class="rt47-sh" id="rt47plh" tabindex="-1">${_rt47E(h)}</h1>`;
  if (s.t === 'i') return `${H(s.h)}<p class="rt47-sb">${_rt47E(s.b)}</p>${s.v && RT47_VIZ[s.v] ? `<figure class="rt47-fig${s.v === 'candle' ? ' rt47-play' : ''}" id="rt47fig">${RT47_VIZ[s.v]()}${s.replay ? `<button type="button" class="rt47-replay" onclick="_rt47Replay()">↻ Replay</button>` : ''}</figure>` : ''}`;
  if (s.t === 'live') return `${H(s.h, 'REAL MARKET NOW')}<p class="rt47-sb">${_rt47E(s.b)}</p><ul class="rt47-qlist">${s.tks.map(tk => _rt47QRow(tk)).join('')}</ul><p class="rt47-fine">Prices from the site's free feeds. The chip shows how fresh each one is.</p>`;
  if (s.t === 'sim') return `${H(s.h || 'Try it', 'INTERACTIVE')}<div class="rt47-simw">${typeof _rt46SimHtml === 'function' ? _rt46SimHtml(s.k) : ''}</div>`;
  if (s.t === 'q') { const q = RT46_QUIZ[id][s.n], ord = _rt46Order(q);
    return `${H(q[0], 'QUICK CHECK')}<div class="rt47-opts" role="group" aria-label="Answers">${ord.map(oi => { const st = !a ? '' : oi === q[2] ? ' ok' : a.o === oi ? ' no' : ' dim';
      return `<button type="button" class="rt47-opt${st}" ${a ? 'aria-disabled="true"' : ''} aria-pressed="${!!a && a.o === oi}" onclick="_rt47Ans(${i},${oi},this)"><span class="rt47-ok-i" aria-hidden="true">${!a ? '' : oi === q[2] ? '✓' : a.o === oi ? '✗' : ''}</span>${_rt47E(q[1][oi])}</button>`; }).join('')}</div>
      ${a ? `<div class="rt47-fb ${a.ok ? 'ok' : 'no'}" id="rt47fb" tabindex="-1" role="status"><strong>${a.ok ? 'Correct!' : 'Not quite.'}</strong> ${_rt47E(q[3])}</div>` : ''}`; }
  if (s.t === 'scen') { const sc = RT47_SCEN[s.n], A = a || { pick: {} }, all = Object.keys(A.pick).length === sc[2].length;
    return `${H(sc[0], s.daily ? 'DAILY CHALLENGE' : 'SCENARIO')}<div class="rt47-news"><span class="rt47-live-dot" aria-hidden="true"></span><span>${_rt47E(sc[1])}</span></div><p class="rt47-sb sm">What is the usual first reaction? Pick up or down for each.</p>
      <div class="rt47-scen">${sc[2].map((row, r) => { const p = A.pick[r], dn = A.done, good = dn && p === row[1];
        return `<div class="rt47-srow${dn ? good ? ' ok' : ' no' : ''}"><div class="rt47-sn">${_rt47E(row[0])}</div><div class="rt47-sbtn" role="group" aria-label="${_rt47E(row[0])}">${['up', 'down'].map(d => `<button type="button" id="rt47s${r}${d}" class="rt47-ud ${d}${p === d ? ' on' : ''}" aria-pressed="${p === d}" ${dn ? 'aria-disabled="true"' : ''} onclick="_rt47Pick(${i},${r},'${d}')">${d === 'up' ? '▲ Up' : '▼ Down'}</button>`).join('')}</div>
          ${dn ? `<div class="rt47-swhy"><b>${good ? '✓' : '✗'} Usually ${row[1]}.</b> ${_rt47E(row[2])}</div>` : ''}</div>`; }).join('')}</div>
      ${A.done ? `<div class="rt47-fb ${A.ok ? 'ok' : 'no'}" id="rt47fb" tabindex="-1" role="status"><strong>${A.ok ? 'All three right!' : 'Good try.'}</strong> These are the usual first reactions, not rules. Positioning and other news can flip them.</div>`
        : `<button type="button" class="rt47-btn rt47-check" ${all ? '' : 'disabled'} onclick="_rt47ScenCheck(${i},this)">Check my answers</button>`}`; }
  if (s.t === 'chart') { const sym = _rt47ChartPick(i, s), c = sym ? _rt47CD[sym] : null, A = _rt47L.a[i] || {}, res = s.k === 'resist';
    const kick = s.k === 'view' ? 'REAL CHART' : 'CHART GYM · REAL DATA';
    if (!sym || !c || c.st !== 'ok') { const err = !sym && RT47_CHART_SYMS.every(x => _rt47CD[x[0]] && _rt47CD[x[0]].st === 'err') || (c && c.st === 'err');
      return `${H(s.h || (s.k === 'trend' ? 'Spot the trend' : res ? 'Find resistance' : 'Find support'), kick)}<div class="rt47-load" role="status">${err ? 'Chart data is unavailable right now. You can skip this step.' : '<span class="rt47-spin" aria-hidden="true"></span>Loading real chart data…'}</div>${err && s.k !== 'view' ? `<button type="button" class="rt47-btn" onclick="_rt47Skip(${i})">Skip this exercise</button>` : ''}`; }
    const w = _rt47Win(c.d, s.k === 'view' ? 30 : 60), nm = _rt47Name(sym), last = w.c[w.c.length - 1];
    const fine = `<p class="rt47-fine">${_rt47E(nm)} · daily candles · ${_rt47Date(w.t[0])} to ${_rt47Date(w.t[w.t.length - 1])} · source: Yahoo Finance via the site's chart feed</p>`, box = `<div class="rt47-chartbox" id="rt47chartbox">${_rt47ChartBox(s, i)}</div>`, body = box + fine;
    if (s.k === 'view') return `${H(s.h, kick)}<p class="rt47-sb">${_rt47E(s.b)} Latest close: <b>${_rt47Num(last)}</b>.</p>${body}`;
    if (s.k === 'trend' && !A.fallback) { const f = _rt47Trend(w.c);
      return `${H('Spot the trend', kick)}<p class="rt47-sb sm">${_rt47E(nm)}, last ${w.c.length} daily candles. Up, down or sideways?</p>${box}
        ${A.done ? `<div class="rt47-fb ${A.ok ? 'ok' : 'no'}" id="rt47fb" tabindex="-1" role="status"><strong>${A.ok ? 'Correct!' : 'Not quite.'}</strong> The gold dashed line is the best-fit trend: ${f.chg >= 0 ? 'up' : 'down'} ${(Math.abs(f.chg) * 100).toFixed(1)}% over the window${f.k === 'side' ? ', which is small enough to call sideways' : `, and a ${f.r2 >= 0.7 ? 'steady' : 'fairly clear'} one`}. Trends change; this describes the past, not the future.</div>`
        : `<div class="rt47-tr" role="group" aria-label="Choose the trend">${[['up', '↗ Up'], ['side', '→ Sideways'], ['down', '↘ Down']].map(([k, l]) => `<button type="button" class="rt47-btn rt47-trb" onclick="_rt47Trd(${i},'${k}',this)">${l}</button>`).join('')}</div>`}${fine}`; }
    const tgtW = res ? 'highest high' : 'lowest low', lvl = A.done ? A.lvl : null;
    return `${H(res ? 'Find resistance' : 'Find support', kick)}<p class="rt47-sb sm">Tap the candle with the <b>${tgtW}</b> on this ${_rt47E(nm)} chart. That level is the clearest ${res ? 'resistance' : 'support'} in the window.</p>${box}
      ${A.done ? `<div class="rt47-fb ${A.ok ? 'ok' : 'no'}" id="rt47fb" tabindex="-1" role="status"><strong>${A.ok ? 'Found it!' : 'Not quite.'}</strong> The ${tgtW} was ${_rt47Num(lvl)} on ${_rt47Date(w.t[A.tgt])}. The latest close is ${Math.abs((last / lvl - 1) * 100).toFixed(1)}% ${last >= lvl ? 'above' : 'below'} it. Levels like this are zones that often attract buyers${res ? ' or sellers' : ''} again, but they can break.</div>`
        : `<div class="rt47-kb"><label for="rt47pick">Or use the slider to choose a candle</label><input type="range" id="rt47pick" min="0" max="${w.c.length - 1}" value="${A.sel != null ? A.sel : Math.floor(w.c.length / 2)}" oninput="_rt47SupSel(${i},this.value)" aria-valuetext="Choose a candle"><button type="button" class="rt47-btn" onclick="if(_rt47L.a[${i}]&&_rt47L.a[${i}].sel==null)_rt47SupSel(${i},document.getElementById('rt47pick').value);_rt47SupCheck(${i},this)">Check this candle</button></div>`}${fine}`; }
  if (s.t === 'end') { const m = _rt47Meta(id), r = _rt47L.res || { ok: 0, n: 0, pass: true }, lv = _rt47Lvl(_rt47S.xp), sk = _rt47Streak(), real = !!RT47_LESSONS[id], ord = _rt47Order(), nx = real ? ord.slice(ord.indexOf(id) + 1).find(x => !_rt47Done(x)) || ord.find(x => !_rt47Done(x)) : _rt47Next();
    return `<div class="rt47-end${r.pass ? ' pass' : ''}"><div class="rt47-medal" aria-hidden="true">${_rt47Ic(r.pass ? 'check' : 'spark')}</div>
      ${H(r.pass ? (real ? 'Lesson complete' : 'Nice work') : 'Nearly there')}<p class="rt47-sb">${real ? (r.n ? `You got <b>${r.ok} of ${r.n}</b> quick checks right${r.pass ? '.' : `. You need ${r.need} to complete the lesson; go back over the steps and try again.`}` : '') : _rt47E(m.tag)}</p>
      ${r.badge ? `<div class="rt47-badge-new">${r.badge[2]} Badge unlocked: <b>${_rt47E(r.badge[1])}</b>${r.grad ? ' · 🎓 Graduate!' : ''}</div>` : ''}
      <div class="rt47-endstats"><div><b>+${_rt47L.xp}</b><span>XP this lesson</span></div><div><b>${sk.n}</b><span>day streak</span></div><div><b>Lv ${lv.n}</b><span>${_rt47E(lv.name)}</span></div></div>
      <div class="rt47-lvbar" role="progressbar" aria-label="Level progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${lv.pct}"><i style="width:${lv.pct}%"></i></div><p class="rt47-fine">${lv.next ? `${lv.next - _rt47S.xp} XP to level ${lv.n + 1}` : 'Top level reached'}</p>
      <div class="rt47-endbtns">${!r.pass && real ? `<button type="button" class="rt47-cta" onclick="_rt47Open('${id}')">Try the lesson again</button>` : nx ? `<button type="button" class="rt47-cta" onclick="_rt47Open('${nx}')">${_rt47Ic('play')} Next: ${_rt47E(RT47_LESSONS[nx].t)}</button>` : `<button type="button" class="rt47-cta" onclick="_rt47Open('gym')">${_rt47Ic('chart')} Chart gym</button>`}
        <button type="button" class="rt47-btn" onclick="_rt47Close()">Back to your path</button>${real ? `<a class="rt47-link" href="/learn/?guide=${id}" onclick="event.preventDefault();_rt47L.id='';_rt45Open('${id}')">Read the full guide →</a>` : ''}</div></div>`; }
  return ''; }
function _rt47Replay() { const f = document.getElementById('rt47fig'); if (!f) return; f.classList.remove('rt47-play'); void f.offsetWidth; f.classList.add('rt47-play'); }
function _rt47PlayerHtml() { const m = _rt47Meta(_rt47L.id); if (!m) return ''; const st = _rt47Steps(_rt47L.id), i = Math.max(0, Math.min(_rt47L.i, st.length - 1)), s = st[i], n = st.length - 1, can = _rt47Can(i), end = s.t === 'end';
  const needs = s.t === 'q' ? 'Choose an answer' : s.t === 'scen' ? 'Check your answers' : s.t === 'chart' && s.k !== 'view' ? 'Answer to continue' : '';
  return `<section class="rt47-pl${_rt46RM() ? ' rt47-rm' : ''}" id="rt47pl" aria-label="Lesson: ${_rt47E(m.t)}">
    <div class="rt47-ptop"><button type="button" class="rt47-x" onclick="_rt47Close()" aria-label="Close lesson and go back to your path">✕</button>
      <div class="rt47-bar" role="progressbar" aria-label="Lesson progress" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${Math.min(i, n)}"><i style="width:${(Math.min(i, n) / n * 100).toFixed(1)}%"></i></div>
      <span class="rt47-xpc" data-rt47xp>${_rt47Ic('bolt')}<span>${_rt47S.xp} XP</span></span></div>
    <div class="rt47-ltitle">${_rt47Ic(m.ic)}<span>${_rt47E(m.t)}</span>${end ? '' : `<span class="rt47-stepn">${i + 1} / ${n}</span>`}</div>
    <div class="rt47-stage${_rt47L.dir > 0 ? ' in-r' : _rt47L.dir < 0 ? ' in-l' : ''}" id="rt47stage" data-i="${i}">${_rt47StepHtml(s, i)}</div>
    ${end ? '' : `<div class="rt47-nav"><div class="rt47-dots" aria-hidden="true">${st.slice(0, n).map((x, k) => `<i class="${k < i ? 'd' : k === i ? 'c' : ''}"></i>`).join('')}</div>
      <div class="rt47-navb"><button type="button" class="rt47-btn rt47-back" onclick="_rt47Go(${i - 1})" ${i ? '' : 'disabled'} aria-label="Previous step">←</button>
      <button type="button" class="rt47-go" onclick="_rt47Go(${i + 1})" ${can ? '' : 'disabled'}>${can ? (i === n - 1 ? 'Finish' : 'Continue') : _rt47E(needs)}</button></div></div>`}
  </section>`; }
function _rt47Redraw() { if (document.getElementById('rt47pl')) { const a = document.activeElement, fid = a && a.id && document.getElementById('rt47pl').contains(a) ? '#' + a.id : null; _rt46Swap('rt47pl', _rt47PlayerHtml(), fid); } else _rt47Tick(); }
// swipe + arrow keys inside the player
let _rt47Tx = null;
document.addEventListener('touchstart', e => { try { const s = e.target.closest && e.target.closest('#rt47stage'); _rt47Tx = s && !e.target.closest('input,select,textarea,.rt47-chart.tap') ? [e.touches[0].clientX, e.touches[0].clientY, Date.now()] : null; } catch (x) { _rt47Tx = null; } }, { passive: true });
document.addEventListener('touchend', e => { try { if (!_rt47Tx) return; const t = e.changedTouches[0], dx = t.clientX - _rt47Tx[0], dy = t.clientY - _rt47Tx[1]; const ok = Math.abs(dx) > 60 && Math.abs(dy) < 50 && Date.now() - _rt47Tx[2] < 700; _rt47Tx = null;
  if (ok && _rt47L.id) _rt47Go(_rt47L.i + (dx < 0 ? 1 : -1)); } catch (x) {} }, { passive: true });
document.addEventListener('keydown', e => { try { if (!_rt47L.id || !document.getElementById('rt47pl') || e.altKey || e.ctrlKey || e.metaKey) return; const a = document.activeElement; if (a && /^(INPUT|SELECT|TEXTAREA)$/.test(a.tagName)) return;
  if (e.key === 'ArrowRight') { e.preventDefault(); _rt47Go(_rt47L.i + 1); } else if (e.key === 'ArrowLeft') { e.preventDefault(); _rt47Go(_rt47L.i - 1); } } catch (x) {} });
// ── Academy home ──
function _rt47Stats() { const lv = _rt47Lvl(_rt47S.xp), sk = _rt47Streak(), done = _rt47Order().filter(_rt47Done).length;
  return `<div class="rt47-stats"><div class="rt47-st lv"><span class="rt47-stk">Level ${lv.n}</span><b>${_rt47E(lv.name)}</b><span class="rt47-lvbar sm" aria-hidden="true"><i style="width:${lv.pct}%"></i></span></div>
    <div class="rt47-st"><span class="rt47-stk">XP</span><b data-rt47xp>${_rt47Ic('bolt')}<span>${_rt47S.xp} XP</span></b></div>
    <div class="rt47-st${sk.today ? ' hot' : ''}"><span class="rt47-stk">Streak</span><b>${_rt47Ic('flame')}${sk.n} day${sk.n === 1 ? '' : 's'}</b></div>
    <div class="rt47-st"><span class="rt47-stk">Lessons</span><b>${done}/10</b></div></div>`; }
function _rt47PathHtml() { const nx = _rt47Next(); let k = 0;
  return RT47_UNITS.map(([u, sub, ids], ui) => `<section class="rt47-unit" aria-labelledby="rt47u${ui}"><div class="rt47-uh"><span class="rt47-un">UNIT ${ui + 1}</span><h3 id="rt47u${ui}">${_rt47E(u)}</h3><p>${_rt47E(sub)}</p></div><ol class="rt47-path">${ids.map(id => { k++; const L = RT47_LESSONS[id], d = _rt47Done(id), cur = id === nx;
    return `<li class="rt47-node${d ? ' done' : cur ? ' next' : ''}"><button type="button" class="rt47-nb" onclick="_rt47Open('${id}')" aria-label="Lesson ${k}: ${_rt47E(L.t)}. ${d ? 'Completed.' : cur ? 'Up next.' : ''} ${L.min} minutes."><span class="rt47-orb">${_rt47Ic(d ? 'check' : L.ic)}</span>
      <span class="rt47-nt"><span class="rt47-nk">LESSON ${k} · ${L.min} MIN</span><span class="rt47-ntt">${_rt47E(L.t)}</span><span class="rt47-ns">${_rt47E(L.tag)}</span></span><span class="rt47-ngo">${d ? 'Review' : cur ? 'Start' : ''}</span></button></li>`; }).join('')}</ol></section>`).join(''); }
function _rt47HomeHtml() { const nx = _rt47Next(), fresh = !_rt47S.xp && !_rt47Order().some(_rt47Done), L = nx ? RT47_LESSONS[nx] : null, ord = _rt47Order(), dn = _rt47DailyN(), dd = !!_rt47S.daily[_rt46Day()], tod = typeof _rt46Tod === 'function' ? _rt46Tod() : null;
  const cta = L ? `<button type="button" class="rt47-cta" onclick="_rt47Open('${nx}')">${_rt47Ic('play')}${fresh ? 'Start your first lesson' : 'Continue learning'}</button><span class="rt47-ctam">Lesson ${ord.indexOf(nx) + 1} · ${_rt47E(L.t)} · ${L.min} min</span>`
    : `<button type="button" class="rt47-cta" onclick="_rt47Open('gym')">${_rt47Ic('chart')}All 10 done: try the chart gym</button><span class="rt47-ctam">🎓 Graduate. Keep your streak with the daily challenge.</span>`;
  return `<div class="rt47-home${_rt46RM() ? ' rt47-rm' : ''}" id="rt47home">
    <section class="rt47-hero" aria-labelledby="rt47h1"><div class="rt47-hero-txt"><div class="rt47-kick">DISPATCH ACADEMY · FREE</div>
      <h1 class="rt47-h1" id="rt47h1">Read markets like a macro desk.</h1>
      <p class="rt47-sub">Ten bite-sized lessons of 3–5 minutes each, built on live prices and real charts. Learn one idea at a time, check yourself as you go, and build a daily streak.</p>
      <div class="rt47-ctarow">${cta}</div></div>${RT47_VIZ.hero()}</section>
    ${_rt47Stats()}
    <div class="rt47-grid"><div class="rt47-main"><h2 class="rt47-h2">Your path</h2>${_rt47PathHtml()}
      <details class="rt47-lib"><summary>${_rt47Ic('book')}Prefer reading? The 10 full guides</summary><ul>${ord.map((id, n) => `<li><a href="/learn/?guide=${id}" onclick="event.preventDefault();_rt45Open('${id}')">${n + 1}. ${_rt47E(((LEARN_MODULES.start || []).find(x => x.id === id) || { title: RT47_LESSONS[id].t }).title)}</a></li>`).join('')}</ul></details></div>
      <aside class="rt47-side" aria-label="Practice and live markets">
        <section class="rt47-card rt47-daily"><div class="rt47-ck">${_rt47Ic('bolt')} DAILY CHALLENGE</div><h3>${_rt47E(RT47_SCEN[dn][0])}</h3><p>${_rt47E(RT47_SCEN[dn][1])}</p>
          ${dd ? `<div class="rt47-donechip">${_rt47Ic('check')} Done today. A new one tomorrow.</div><button type="button" class="rt47-btn" onclick="_rt47Open('scen')">Scenario room</button>` : `<button type="button" class="rt47-cta sm" onclick="_rt47Open('daily')">Take the challenge · +20 XP</button>`}</section>
        <section class="rt47-card"><div class="rt47-ck">${_rt47Ic('chart')} REAL MARKET NOW</div><ul class="rt47-qlist">${['XAU', 'DXY', 'TNX', 'BRENT', 'BTC', 'SPX'].map(tk => _rt47QRow(tk, true)).join('')}</ul><p class="rt47-fine">From the site's free feeds. The chip shows how fresh each price is.</p></section>
        <section class="rt47-card rt47-gym"><div class="rt47-ck">${_rt47Ic('candle')} CHART GYM</div><h3>Spot the trend. Find support.</h3><p>Four quick drills on real daily charts of gold, the S&amp;P 500 and more.${_rt47S.chart.n ? ` Your record: ${_rt47S.chart.ok}/${_rt47S.chart.n}.` : ''}</p><button type="button" class="rt47-btn" onclick="_rt47Open('gym')">Open the chart gym</button></section>
        <section class="rt47-card"><div class="rt47-ck">${_rt47Ic('spark')} SCENARIO ROOM</div><h3>"The Fed surprises. Now what?"</h3><p>Six market shocks. Call the usual first move in gold, the dollar and yields.</p><button type="button" class="rt47-btn" onclick="_rt47Open('scen')">Play scenarios</button></section>
        ${tod ? `<section class="rt47-card"><div class="rt47-ck">${_rt47Ic('book')} TERM OF THE DAY</div>${_rt46Card('rt46tod', tod[1], tod[2], tod[3], typeof _rt46TodOn !== 'undefined' && _rt46TodOn)}<button type="button" class="rt47-link" onclick="_rt45Term('${tod[0]}')">In the glossary →</button></section>` : ''}
        <section class="rt47-card"><div class="rt47-ck">${_rt47Ic('shield')} BADGES</div><div class="rt47-bds">${RT46_BADGES.map(b => `<span class="rt47-bd${_rt47Done(b[0]) ? ' on' : ''}" title="${_rt47E(b[1])}"><span aria-hidden="true">${b[2]}</span><span>${_rt47E(b[1])}</span></span>`).join('')}<span class="rt47-bd${_rt46Grad() ? ' on' : ''}"><span aria-hidden="true">🎓</span><span>Graduate</span></span></div></section>
      </aside></div>
    <p class="rt47-disc">Education only, not financial advice. Markets carry risk and you can lose money. Diagrams marked "illustration" are not real data; charts and prices marked live or real come from the site's data feeds.</p></div>`; }
function _rt47TopHtml(h1) { const lv = _rt47Lvl(_rt47S.xp), sk = _rt47Streak();
  return `<div class="rt47-top"><${h1 ? 'h1' : 'div'} class="rt47-brand"><span class="rt47-dia" aria-hidden="true">◆</span>Dispatch Academy</${h1 ? 'h1' : 'div'}><div class="rt47-me"><span>Lv ${lv.n}</span><span data-rt47xp>${_rt47Ic('bolt')}<span>${_rt47S.xp} XP</span></span><span class="${sk.today ? 'hot' : ''}">${_rt47Ic('flame')}${sk.n}</span></div></div>`; }
// tabs: text only, Academy first
try { const lbl = { start: 'Academy', glossary: 'Glossary', play: 'Practise', macro: 'Macro', fundamental: 'Fundamental', technical: 'Technical', portfolio: 'Risk & portfolio', signals: 'AI & signals', calc: 'Calculators' }; _RT45_TABS.forEach(t => { if (lbl[t[0]]) t[1] = lbl[t[0]]; }); } catch (e) {}
{
  const _rl3 = renderLearn;
  renderLearn = function () {
    let h = _rl3.apply(this, arguments);
    try { _rt47Sig = _rt47SigNow();
      const ti = h.indexOf('<div class="tabs" role="tablist">'); if (ti < 0) return h;
      const home = !_learnSub && _learnTab === 'start';
      if (home && _rt47L.id && _rt47Meta(_rt47L.id)) return `<div class="rt47-wrap rt47-inpl">${_rt47TopHtml(false)}${_rt47PlayerHtml()}</div>`;
      let rest = h.slice(ti).replace('<div class="tabs" role="tablist">', '<div class="tabs rt47-tabs" role="tablist" aria-label="Learn sections">');
      if (home) { const te = rest.indexOf('</div>') + 6; rest = rest.slice(0, te) + _rt47HomeHtml(); }
      h = `<div class="rt47-wrap">${_rt47TopHtml(!home && !_learnSub)}${rest}</div>`;
    } catch (e) {}
    return h;
  };
}
{ const _su7 = _rt45SyncUrl;
  _rt45SyncUrl = function () { try { if (_rt47L.id && /^\/learn\/?$/.test(location.pathname) && !_learnSub && _learnTab === 'start') { const q = '?lesson=' + encodeURIComponent(_rt47L.id); if (location.search !== q) history.replaceState(history.state, '', '/learn/' + q); const m = _rt47Meta(_rt47L.id); if (m) document.title = `${m.t} | Dispatch Academy | The Dispatch Markets`; return; } } catch (e) {} return _su7.apply(this, arguments); }; }
{ const _tb7 = _rt45Tab; _rt45Tab = function () { _rt47L.id = ''; _rt47Prog = Date.now(); return _tb7.apply(this, arguments); };
  const _op7 = _rt45Open; _rt45Open = function () { _rt47L.id = ''; _rt47Prog = Date.now(); return _op7.apply(this, arguments); };
  const _te7 = _rt45Term; _rt45Term = function () { _rt47L.id = ''; _rt47Prog = Date.now(); return _te7.apply(this, arguments); };
  try { const _nv7 = nav; nav = function (p) { _rt47Prog = Date.now(); if (p !== 'learn') _rt47L.id = ''; return _nv7.apply(this, arguments); }; } catch (e) {} }
// background price refreshes must not rebuild the Academy (it would restart animations and move focus); live cells tick on their own
['pointerdown', 'keydown', 'touchstart'].forEach(ev => document.addEventListener(ev, e => { if (e.isTrusted) _rt47Act = Date.now(); }, { capture: true, passive: true }));
window.addEventListener('popstate', () => { _rt47Act = Date.now(); try { if (_rt47L.id && !/[?&]lesson=/.test(location.search)) _rt47L.id = ''; } catch (e) {} });
function _rt47Hold() { try { const onL = (typeof pg !== 'undefined' && pg === 'learn') || !!document.getElementById('learnOv');
  return onL && !!(document.getElementById('rt47pl') || document.getElementById('rt47home')) && _rt47SigNow() === _rt47Sig && Date.now() - _rt47Act > 1200 && Date.now() - _rt47Prog > 1200; } catch (e) { return false; } }
{ const _rv7 = _refreshView; _refreshView = function () { if (_rt47Hold()) { _rt47Tick(); return; } return _rv7.apply(this, arguments); };
  try { const _rm7 = renderMain; renderMain = function () { if (_rt47Hold()) { _rt47Tick(); return; } return _rm7.apply(this, arguments); }; } catch (e) {} }
try { const st = document.createElement('style'); st.id = 'rt47css'; st.textContent = `
.rt47-wrap{min-width:0;max-width:100%;font-family:var(--sn);color:var(--tx)}
.rt47-wrap *{box-sizing:border-box}
.rt47-top{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:4px 2px 12px;min-width:0}
.rt47-brand{font-family:var(--sf);font-size:19px;font-weight:700;margin:0;letter-spacing:-.01em;display:flex;align-items:center;gap:8px;color:var(--tx);border:0;padding:0;line-height:1.2}
.rt47-dia{color:var(--gd);font-size:13px}
.rt47-me{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.rt47-me>span{display:inline-flex;align-items:center;gap:4px;font-family:var(--mn);font-size:11px;color:var(--t2);background:var(--b2);border:1px solid var(--gb);border-radius:999px;padding:4px 9px;white-space:nowrap}
.rt47-me .hot,.rt47-st.hot b{color:var(--gd)}
.rt47-ic{width:16px;height:16px;flex:0 0 auto;vertical-align:-3px}
[data-rt47xp]{display:inline-flex;align-items:center;gap:4px}
[data-rt47xp].bump{animation:rt47bump .5s ease}
@keyframes rt47bump{40%{transform:scale(1.18);color:var(--gd)}}
.rt47-tabs{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto;gap:6px;scrollbar-width:none;margin:0 0 18px!important;padding:2px 0 6px!important;border:0!important;-webkit-mask-image:linear-gradient(90deg,#000 88%,transparent);mask-image:linear-gradient(90deg,#000 88%,transparent)}
.rt47-tabs::-webkit-scrollbar{display:none}
.rt47-tabs button{flex:0 0 auto;border:1px solid var(--gb)!important;border-radius:999px!important;padding:8px 14px!important;font-family:var(--sn)!important;font-size:13px!important;font-weight:600!important;color:var(--t2)!important;background:transparent!important;min-height:38px}
.rt47-tabs button.on{background:var(--gd)!important;color:#14151A!important;border-color:var(--gd)!important}
.rt47-tabs button:last-child{margin-right:28px}
.rt47-hero{position:relative;overflow:hidden;border-radius:16px;padding:24px 20px 22px;background:radial-gradient(120% 90% at 100% 0%,rgba(217,174,82,.20),transparent 55%),linear-gradient(180deg,var(--b2),var(--b1));border:1px solid rgba(217,174,82,.28);margin-bottom:14px}
.rt47-hero-txt{position:relative;z-index:1;max-width:560px}
.rt47-kick,.rt47-ck,.rt47-un,.rt47-sk,.rt47-nk,.rt47-stk{font-family:var(--mn);font-size:10.5px;letter-spacing:.14em;color:var(--gd);font-weight:600}
.rt47-h1{font-family:var(--sf);font-weight:700;font-size:32px;line-height:1.08;letter-spacing:-.02em;margin:10px 0 10px;color:var(--tx);border:0;padding:0}
.rt47-sub{font-size:15px;line-height:1.55;color:var(--t2);margin:0 0 18px;max-width:46ch}
.rt47-ctarow{display:flex;flex-direction:column;gap:8px;align-items:stretch}
.rt47-cta{white-space:nowrap;flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:52px;padding:0 22px;border:0;border-radius:12px;background:var(--gd);color:#14151A;font-family:var(--sn);font-size:16px;font-weight:800;cursor:pointer;box-shadow:0 6px 24px rgba(217,174,82,.25);transition:transform .15s ease,box-shadow .15s ease}
.rt47-cta:hover{transform:translateY(-1px);box-shadow:0 10px 28px rgba(217,174,82,.32)}
.rt47-cta:focus-visible,.rt47-btn:focus-visible,.rt47-go:focus-visible,.rt47-nb:focus-visible,.rt47-opt:focus-visible,.rt47-ud:focus-visible,.rt47-x:focus-visible{outline:2px solid var(--tx);outline-offset:2px}
.rt47-cta.sm{min-height:44px;font-size:14px;width:100%}
.rt47-cta .rt47-ic{width:18px;height:18px}
.rt47-ctam{font-family:var(--mn);font-size:11px;color:var(--t2);text-align:center}
.rt47-hero-art{position:absolute;right:-24px;top:4px;width:200px;opacity:.16;z-index:0}
.rt47-hc{transform-origin:center bottom;transform-box:fill-box;animation:rt47rise .7s cubic-bezier(.2,.8,.2,1) both}
@keyframes rt47rise{from{transform:scaleY(0);opacity:0}}
.rt47-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:0 0 22px}
.rt47-st{background:var(--b2);border:1px solid var(--gb);border-radius:12px;padding:10px 12px;min-width:0;display:flex;flex-direction:column;gap:3px}
.rt47-st b{font-size:16px;font-weight:800;display:inline-flex;align-items:center;gap:5px;color:var(--tx)}
.rt47-lvbar{display:block;height:8px;border-radius:99px;background:var(--b3);overflow:hidden;margin:6px 0 2px}
.rt47-lvbar.sm{height:4px;margin:4px 0 0}
.rt47-lvbar i{display:block;height:100%;background:linear-gradient(90deg,#B88E3E,var(--gd));border-radius:99px}
.rt47-grid{display:grid;gap:22px;min-width:0}
.rt47-main,.rt47-side{min-width:0}
.rt47-h2{font-family:var(--sf);font-size:23px;font-weight:700;margin:0 0 6px;color:var(--tx);border:0;padding:0}
.rt47-unit{margin:14px 0 6px}
.rt47-uh h3{font-family:var(--sn);font-size:17px;font-weight:800;margin:2px 0 2px;color:var(--tx)}
.rt47-uh p{margin:0 0 10px;font-size:13px;color:var(--t2)}
.rt47-path{list-style:none;margin:0;padding:0 0 0 0;position:relative}
.rt47-path:before{content:"";position:absolute;left:27px;top:12px;bottom:12px;width:2px;background:repeating-linear-gradient(180deg,var(--gb) 0 6px,transparent 6px 11px)}
.rt47-node{position:relative;margin:0 0 10px}
.rt47-nb{display:flex;align-items:center;gap:14px;width:100%;text-align:left;background:var(--b2);border:1px solid var(--gb);border-radius:14px;padding:12px 14px 12px 8px;cursor:pointer;color:inherit;font:inherit;min-height:72px;transition:border-color .15s,transform .15s}
.rt47-nb:hover{border-color:rgba(217,174,82,.6)}
.rt47-orb{position:relative;z-index:1;flex:0 0 40px;height:40px;border-radius:50%;display:grid;place-items:center;background:var(--b3);border:2px solid var(--gb);color:var(--t2)}
.rt47-orb .rt47-ic{width:20px;height:20px}
.rt47-node.done .rt47-orb{background:var(--gd);border-color:var(--gd);color:#14151A}
.rt47-node.next .rt47-nb{border-color:var(--gd);background:linear-gradient(90deg,rgba(217,174,82,.12),var(--b2) 70%)}
.rt47-node.next .rt47-orb{border-color:var(--gd);color:var(--gd);box-shadow:0 0 0 0 rgba(217,174,82,.5);animation:rt47pulse 2.2s infinite}
@keyframes rt47pulse{70%{box-shadow:0 0 0 10px rgba(217,174,82,0)}100%{box-shadow:0 0 0 0 rgba(217,174,82,0)}}
.rt47-nt{display:flex;flex-direction:column;gap:2px;min-width:0;flex:1}
.rt47-nk{font-size:9.5px;color:var(--t3)}
.rt47-node.next .rt47-nk{color:var(--gd)}
.rt47-ntt{font-size:15.5px;font-weight:800;line-height:1.25;color:var(--tx)}
.rt47-ns{font-size:12.5px;color:var(--t2)}
.rt47-ngo{font-family:var(--mn);font-size:11px;font-weight:600;color:var(--t3);flex:0 0 auto}
.rt47-node.next .rt47-ngo{color:#14151A;background:var(--gd);padding:6px 10px;border-radius:8px}
.rt47-lib{margin:16px 0 0;border:1px solid var(--gb);border-radius:12px;padding:12px 14px;background:var(--b1)}
.rt47-lib summary{cursor:pointer;font-weight:700;font-size:14px;display:flex;align-items:center;gap:8px;color:var(--tx)}
.rt47-lib ul{margin:10px 0 0;padding:0 0 0 4px;list-style:none;display:grid;gap:8px}
.rt47-lib a{color:var(--t2);font-size:13.5px;text-decoration:none}
.rt47-lib a:hover{color:var(--gd)}
.rt47-card{background:var(--b2);border:1px solid var(--gb);border-radius:14px;padding:16px;margin:0 0 12px;min-width:0}
.rt47-card h3{font-family:var(--sn);font-size:16px;font-weight:800;margin:6px 0 6px;color:var(--tx);line-height:1.3}
.rt47-card p{font-size:13.5px;color:var(--t2);line-height:1.5;margin:0 0 12px}
.rt47-ck{display:flex;align-items:center;gap:6px}
.rt47-ck .rt47-ic{width:14px;height:14px}
.rt47-daily{border-color:rgba(217,174,82,.45);background:linear-gradient(160deg,rgba(217,174,82,.10),var(--b2) 60%)}
.rt47-donechip{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--gn);margin:0 0 10px;font-weight:700}
.rt47-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:0 16px;border-radius:10px;border:1px solid var(--gb);background:var(--b3);color:var(--tx);font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer}
.rt47-btn:hover{border-color:var(--gd)}
.rt47-btn:disabled{opacity:.45;cursor:not-allowed}
.rt47-link{background:none;border:0;color:var(--gd);font-family:var(--sn);font-size:13px;font-weight:700;cursor:pointer;padding:8px 0;text-decoration:none;display:inline-block}
.rt47-qlist{list-style:none;margin:6px 0 8px;padding:0}
.rt47-qrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;padding:9px 0;border-bottom:1px solid var(--gb);align-items:center}
.rt47-qrow:last-child{border-bottom:0}
.rt47-qn{font-size:13.5px;font-weight:700;color:var(--tx);min-width:0}
.rt47-qv{display:flex;gap:8px;align-items:center;justify-content:flex-end;font-family:var(--mn);font-size:12.5px;flex-wrap:wrap}
.rt47-qp{color:var(--tx);font-weight:600}
.rt47-qc.up{color:var(--gn)}.rt47-qc.dn{color:var(--rd)}
.rt47-qs{font-size:9px;letter-spacing:.06em;padding:2px 6px;border-radius:5px;border:1px solid var(--gb);color:var(--t3)}
.rt47-qs.live{color:var(--gn);border-color:rgba(111,191,149,.4)}.rt47-qs.delayed{color:var(--gd);border-color:rgba(217,174,82,.4)}
.rt47-qgo{grid-column:1/-1;justify-self:start;background:none;border:0;padding:2px 0;color:var(--t3);font-size:12px;cursor:pointer;font-family:var(--sn)}
.rt47-qgo:hover{color:var(--gd)}
.rt47-bds{display:flex;flex-wrap:wrap;gap:6px}
.rt47-bd{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;padding:5px 9px;border-radius:999px;border:1px solid var(--gb);color:var(--t3);filter:grayscale(1);opacity:.6}
.rt47-bd.on{filter:none;opacity:1;color:var(--tx);border-color:rgba(217,174,82,.5);background:rgba(217,174,82,.08)}
.rt47-disc{font-size:11.5px;color:var(--t3);line-height:1.5;margin:22px 0 8px}
.rt47-fine{font-size:11px;color:var(--t3);line-height:1.45;margin:8px 0 0}
/* player */
.rt47-pl{max-width:640px;margin:0 auto;min-height:60vh;display:flex;flex-direction:column}
.rt47-ptop{display:flex;align-items:center;gap:12px;margin:0 0 12px}
.rt47-x{flex:0 0 44px;height:44px;border-radius:12px;border:1px solid var(--gb);background:var(--b2);color:var(--t2);font-size:17px;cursor:pointer}
.rt47-bar{flex:1;height:10px;border-radius:99px;background:var(--b3);overflow:hidden}
.rt47-bar i{display:block;height:100%;background:linear-gradient(90deg,#B88E3E,var(--gd));border-radius:99px;transition:width .35s ease}
.rt47-xpc{font-family:var(--mn);font-size:12px;color:var(--gd);white-space:nowrap}
.rt47-ltitle{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--t2);margin:0 0 6px;font-weight:600;min-width:0}
.rt47-ltitle>span:first-of-type{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rt47-stepn{font-family:var(--mn);font-size:11px;color:var(--t3)}
.rt47-stage{flex:1;background:var(--b2);border:1px solid var(--gb);border-radius:18px;padding:22px 18px 20px;min-height:340px;min-width:0}
.rt47-stage.in-r{animation:rt47inr .32s cubic-bezier(.2,.8,.2,1)}.rt47-stage.in-l{animation:rt47inl .32s cubic-bezier(.2,.8,.2,1)}
@keyframes rt47inr{from{opacity:0;transform:translateX(28px)}}@keyframes rt47inl{from{opacity:0;transform:translateX(-28px)}}
.rt47-sh{font-family:var(--sf);font-weight:700;font-size:26px;line-height:1.15;letter-spacing:-.015em;margin:6px 0 12px;color:var(--tx);outline:none;border:0;padding:0}
.rt47-sb{font-size:16.5px;line-height:1.6;color:var(--tx);margin:0 0 14px;opacity:.92}
.rt47-sb.sm{font-size:14.5px;color:var(--t2)}
.rt47-fig{margin:14px 0 0;background:var(--b1);border:1px solid var(--gb);border-radius:14px;padding:12px;position:relative}
.rt47-svg{display:block;width:100%;height:auto;max-height:260px}
.rt47-replay{display:block;margin:6px 0 0 auto;background:var(--b3);border:1px solid var(--gb);color:var(--t2);border-radius:8px;font-size:12px;padding:5px 9px;cursor:pointer}
.rt47-play .rt47-cd-body{transform-box:fill-box;transform-origin:center bottom;animation:rt47body 1.4s .5s cubic-bezier(.3,.7,.2,1) both}
.rt47-play .rt47-cd-wick{stroke-dasharray:160;animation:rt47wick 1s 1.7s ease both}
.rt47-play .rt47-cd-lbl>*{animation:rt47fade .5s ease both}
.rt47-play .rt47-cd-lbl>*:nth-child(-n+2){animation-delay:.3s}.rt47-play .rt47-cd-lbl>*:nth-child(n+3):nth-child(-n+4){animation-delay:1.8s}.rt47-play .rt47-cd-lbl>*:nth-child(n+5){animation-delay:2.5s}
@keyframes rt47body{0%{transform:scaleY(.02)}55%{transform:scaleY(1.25)}75%{transform:scaleY(.85)}100%{transform:scaleY(1)}}
@keyframes rt47wick{from{stroke-dashoffset:160}to{stroke-dashoffset:0}}
@keyframes rt47fade{from{opacity:0}}
.rt47-anim-see .rt47-see{transform-origin:160px 137px;animation:rt47see 5s ease-in-out infinite}
@keyframes rt47see{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}
.rt47-draw{stroke-dasharray:600;animation:rt47drawk 1.4s ease both}
@keyframes rt47drawk{from{stroke-dashoffset:600}to{stroke-dashoffset:0}}
.rt47-grow{transform-box:fill-box;transform-origin:center bottom;animation:rt47rise .8s cubic-bezier(.2,.8,.2,1) both}
.rt47-grow-dn{transform-box:fill-box;transform-origin:center top;animation:rt47rise .8s cubic-bezier(.2,.8,.2,1) both}
.rt47-opts{display:grid;gap:10px;margin:8px 0 0}
.rt47-opt{display:flex;align-items:center;gap:10px;text-align:left;min-height:54px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--gb);background:var(--b1);color:var(--tx);font-family:var(--sn);font-size:15px;font-weight:600;line-height:1.35;cursor:pointer;transition:border-color .12s,transform .12s}
.rt47-opt:hover:not([aria-disabled]){border-color:var(--gd)}
.rt47-opt:active:not([aria-disabled]){transform:scale(.99)}
.rt47-ok-i{flex:0 0 20px;font-weight:800;text-align:center}
.rt47-opt.ok{border-color:var(--gn);background:rgba(111,191,149,.12)}.rt47-opt.ok .rt47-ok-i{color:var(--gn)}
.rt47-opt.no{border-color:var(--rd);background:rgba(217,122,114,.12)}.rt47-opt.no .rt47-ok-i{color:var(--rd)}
.rt47-opt.dim{opacity:.55}
.rt47-opt[aria-disabled]{cursor:default}
.rt47-fb{margin:14px 0 0;padding:12px 14px;border-radius:12px;font-size:14.5px;line-height:1.55;outline:none;border:1px solid}
.rt47-fb.ok{background:rgba(111,191,149,.10);border-color:rgba(111,191,149,.4)}.rt47-fb.ok strong{color:var(--gn)}
.rt47-fb.no{background:rgba(217,174,82,.08);border-color:rgba(217,174,82,.35)}.rt47-fb.no strong{color:var(--gd)}
.rt47-fb.ok{animation:rt47pop .35s ease}
@keyframes rt47pop{0%{transform:scale(.97);opacity:.4}60%{transform:scale(1.01)}}
.rt47-nav{position:sticky;bottom:0;z-index:5;padding:12px 0 6px;background:linear-gradient(180deg,transparent,var(--bg) 26%)}
.rt47-dots{display:flex;gap:5px;justify-content:center;flex-wrap:wrap;margin:0 0 10px}
.rt47-dots i{width:7px;height:7px;border-radius:50%;background:var(--b3);border:1px solid var(--gb)}
.rt47-dots i.d{background:rgba(217,174,82,.55);border-color:transparent}.rt47-dots i.c{background:var(--gd);border-color:var(--gd);width:20px;border-radius:99px}
.rt47-navb{display:flex;gap:10px}
.rt47-back{flex:0 0 56px;font-size:18px;min-height:54px}
.rt47-go{flex:1;min-height:54px;border:0;border-radius:12px;background:var(--gd);color:#14151A;font-family:var(--sn);font-size:16px;font-weight:800;cursor:pointer}
.rt47-go:disabled{background:var(--b3);color:var(--t3);cursor:not-allowed;font-weight:600;font-size:14px}
.rt47-news{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:12px;background:var(--b1);border-left:3px solid var(--rd);font-size:15px;font-weight:700;line-height:1.45;margin:0 0 12px}
.rt47-live-dot{flex:0 0 8px;height:8px;border-radius:50%;background:var(--rd);margin-top:7px;animation:rt47blink 1.4s infinite}
@keyframes rt47blink{50%{opacity:.25}}
.rt47-scen{display:grid;gap:10px}
.rt47-srow{border:1px solid var(--gb);border-radius:12px;padding:10px 12px;background:var(--b1);display:grid;grid-template-columns:minmax(0,1fr);gap:8px}
.rt47-srow.ok{border-color:rgba(111,191,149,.5)}.rt47-srow.no{border-color:rgba(217,122,114,.5)}
.rt47-sn{font-weight:700;font-size:14.5px}
.rt47-sbtn{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.rt47-ud{min-height:44px;border-radius:10px;border:1.5px solid var(--gb);background:var(--b2);color:var(--t2);font-family:var(--sn);font-size:14px;font-weight:700;cursor:pointer}
.rt47-ud.up.on{border-color:var(--gn);color:var(--gn);background:rgba(111,191,149,.1)}.rt47-ud.down.on{border-color:var(--rd);color:var(--rd);background:rgba(217,122,114,.1)}
.rt47-ud[aria-disabled]{cursor:default}
.rt47-swhy{font-size:13.5px;line-height:1.5;color:var(--t2)}
.rt47-srow.ok .rt47-swhy b{color:var(--gn)}.rt47-srow.no .rt47-swhy b{color:var(--rd)}
.rt47-check{width:100%;margin-top:12px;background:var(--b3)}
.rt47-chartbox{background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:8px}
.rt47-chart.tap{cursor:crosshair;touch-action:manipulation}
.rt47-csel rect,.rt47-csel line{stroke:var(--tx);stroke-width:1.2}
.rt47-chit rect{stroke:var(--gd);stroke-width:2}
.rt47-tr{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.rt47-trb{min-height:50px;padding:0 6px;font-size:14px}
.rt47-kb{display:grid;gap:8px;margin-top:12px}
.rt47-kb label{font-size:12px;color:var(--t3)}
.rt47-kb input[type=range]{width:100%;accent-color:var(--gd);min-height:32px}
.rt47-load{display:flex;align-items:center;gap:10px;padding:30px 12px;justify-content:center;color:var(--t2);font-size:14px;background:var(--b1);border-radius:12px;margin:0 0 12px}
.rt47-spin{width:18px;height:18px;border-radius:50%;border:2px solid var(--gb);border-top-color:var(--gd);animation:rt47spin .8s linear infinite}
@keyframes rt47spin{to{transform:rotate(360deg)}}
.rt47-simw .rt46-sim{margin:6px 0 0;border:0;padding:0;background:none}
.rt47-simw .rt46-qk,.rt47-simw .rt46-simh{display:none}
.rt47-end{text-align:center;padding:10px 0}
.rt47-medal{width:84px;height:84px;margin:6px auto 6px;border-radius:50%;display:grid;place-items:center;background:var(--b3);border:2px solid var(--gb);color:var(--t2)}
.rt47-end.pass .rt47-medal{background:radial-gradient(circle at 35% 30%,#F1D28C,var(--gd) 55%,#9C742C);border-color:#F1D28C;color:#14151A;box-shadow:0 10px 40px rgba(217,174,82,.35);animation:rt47medal .7s cubic-bezier(.2,1.4,.4,1) both}
@keyframes rt47medal{from{transform:scale(.3) rotate(-30deg);opacity:0}}
.rt47-medal .rt47-ic{width:40px;height:40px;stroke-width:2.4}
.rt47-endstats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0 10px}
.rt47-endstats div{background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:10px 6px;display:flex;flex-direction:column;gap:2px}
.rt47-endstats b{font-size:19px;font-weight:800;color:var(--gd)}.rt47-endstats span{font-size:11.5px;color:var(--t2)}
.rt47-badge-new{display:inline-block;margin:6px 0 4px;padding:8px 14px;border-radius:999px;background:rgba(217,174,82,.12);border:1px solid rgba(217,174,82,.5);font-size:14px}
.rt47-endbtns{display:grid;gap:10px;margin-top:16px}
.rt47-pop{position:fixed;z-index:9999;font-family:var(--mn);font-weight:700;font-size:15px;color:var(--gd);pointer-events:none;animation:rt47up 1.2s ease-out forwards;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.rt47-pop.rm{animation:rt47fadeout 1.2s ease forwards}
@keyframes rt47up{from{transform:translateY(0);opacity:1}to{transform:translateY(-46px);opacity:0}}
@keyframes rt47fadeout{70%{opacity:1}to{opacity:0}}
.rt47-conf{position:fixed;left:0;right:0;top:0;height:0;z-index:9998;pointer-events:none}
.rt47-conf i{position:absolute;top:-12px;width:8px;height:12px;border-radius:2px;animation:rt47fall 1.6s cubic-bezier(.2,.6,.4,1) forwards}
@keyframes rt47fall{to{transform:translate(var(--dx),85vh) rotate(var(--r));opacity:0}}
.rt47-rm *,.rt47-rm *:before{animation:none!important;transition:none!important}
@media (prefers-reduced-motion:reduce){.rt47-wrap *,.rt47-pop,.rt47-conf i{animation:none!important;transition:none!important}}
@media (min-width:600px){.rt47-stats{grid-template-columns:repeat(4,minmax(0,1fr))}.rt47-ctarow{flex-direction:row;align-items:center;gap:14px}.rt47-ctam{text-align:left}.rt47-h1{font-size:40px}.rt47-hero{padding:32px 30px 28px}.rt47-hero-art{width:300px;opacity:.5;top:auto;bottom:10px;right:16px}.rt47-sh{font-size:30px}.rt47-stage{padding:28px 28px 24px}}
@media (min-width:768px){.rt47-pl .rt47-svg{max-height:210px}.rt47-pl .rt47-chart{max-height:240px}.rt47-stage{min-height:0}}
@media (min-width:1000px){.rt47-grid{grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:26px}.rt47-hero-txt{max-width:460px}}
@media (max-width:767px){.rt47-nav{position:fixed;left:0;right:0;bottom:var(--rt47bn,55px);padding:14px 16px 8px;background:linear-gradient(180deg,rgba(20,21,26,0),var(--bg) 22%)}.rt47-pl{min-height:0;padding-bottom:118px}.rt47-inpl .rt47-top{display:none}.rt47-stage{min-height:0;padding:18px 14px 16px}.rt47-fig{padding:8px}.rt47-chartbox{padding:4px}.rt47-brand{font-size:17px}.rt47-me>span{padding:3px 8px}.rt47-sh{font-size:25px}}
`; document.head.appendChild(st); } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat47') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat47', 'app.js?v=chat48')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt47 block appended + index chat47->chat48; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
