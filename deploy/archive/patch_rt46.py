#!/usr/bin/env python3
"""patch_rt46.py: chat45 -> chat46 (client only). Stacks on rt45b output (app.js e085f127).
Learn, more interactive: end-of-guide quizzes (38 questions, instant feedback + explanations) on all 10 Start-here guides;
progress bar, read/passed ticks and 11 badges (localStorage td_learn_v1, this browser only); 4 slider simulators
(position size, real yield vs gold, leverage/margin, compounding); Term of the day flip card; Practise tab with
flashcards and a no-money "Guess the move" game scored from the live feed; background price refreshes no longer
redraw Learn while a slider/search/select is in use. Respects prefers-reduced-motion and the reduce-motion setting.
Usage: python3 patch_rt46.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt46 ──' in s: die('rt46 already applied')
if '// ── rt45b ──' not in s: die('base is not rt45b output')
if 'app.js?v=chat45' not in h: die('index.html is not chat45')
for need in ['function _rt45StartHtml(', 'const _RT45_TABS', 'const RT45_GLOSS', 'function _rt45Esc(', 'function _rt45Term(', 'function _rt45Tab(', 'function _refreshView(', 'function fp(']:
    if need not in s: die('missing ' + need)
OLD = 'headline = `Learn · ${({ start: "beginner guides", glossary: "glossary" })[_learnTab] || _learnTab + " frameworks"}`;'
if s.count(OLD) == 1: s = s.replace(OLD, OLD.replace('glossary: "glossary" }', 'glossary: "glossary", play: "practice" }')); print('edit ok: intel headline')
else: print('edit skipped: intel headline (%d matches)' % s.count(OLD))
BLOCK = r'''// ── rt46 ──
// 1: end-of-guide quizzes: [question, [options], correct index, explanation]
const RT46_QUIZ = {
 'start-markets-table': [
  ['A row shows CLOSED next to the price. What are you looking at?', ['A live price that has stopped moving', 'The last price from that venue\'s most recent session', 'A price The Dispatch has estimated'], 1, 'CLOSED means that venue is shut, so you see its last close, and the time shown is when it closed.'],
  ['Why are WTI and Brent labelled DELAYED 10m?', ['The site refreshes them slowly to save data', 'Free sources only publish CME and ICE futures 10 minutes late', 'Oil only trades every 10 minutes'], 1, 'The delay is at the source. No free feed offers live CME or ICE futures, so the label says so rather than pretend.'],
  ['One row says LIVE and the row below says CLOSED. What is most likely?', ['A bug: everything should share one status', 'The two instruments trade on venues with different hours', 'The CLOSED row has been delisted'], 1, 'Each market keeps its own hours. Crypto can be live while a stock exchange is shut.'],
  ['Which statement about pre-market prices is true?', ['They are as reliable as the regular session', 'Volume is thin, so prices can jump and spreads are wider', 'They only exist for crypto'], 1, 'Outside regular hours fewer people trade, so moves are easier to make and easier to reverse.'],
 ],
 'start-gold-macro': [
  ['What is a real yield?', ['A bond yield after expected inflation', 'The yield on gold', 'A bond yield before tax'], 0, 'Real yield = nominal yield minus expected inflation. The 10-year US TIPS yield is the usual gauge.'],
  ['All else equal, rising real yields tend to…', ['Help gold, because bonds look riskier', 'Weigh on gold, because holding a non-paying asset costs more', 'Have no link to gold at all'], 1, 'Gold pays no interest, so higher real yields raise the opportunity cost of holding it. The link is a tendency, not a rule.'],
  ['Gold is priced in US dollars. A stronger dollar usually…', ['Makes gold cheaper for buyers using other currencies', 'Makes gold more expensive for buyers using other currencies', 'Has no effect'], 1, 'A stronger dollar raises the local-currency cost of gold for most of the world, which can weigh on demand.'],
  ['Which currency has the largest weight in the dollar index (DXY)?', ['Japanese yen', 'Euro', 'British pound'], 1, 'The euro makes up about 58% of the DXY. The other five are the yen, pound, Canadian dollar, Swedish krona and Swiss franc.'],
 ],
 'start-oil': [
  ['Where is WTI crude delivered?', ['Rotterdam', 'Cushing, Oklahoma', 'The North Sea'], 1, 'WTI is a US crude delivered at Cushing, Oklahoma, and traded as NYMEX futures.'],
  ['The official EIA spot price is…', ['A live tick-by-tick quote', 'A daily figure published a few days after the date it covers', 'The same thing as the ICE Brent futures price'], 1, 'It is authoritative and free, but daily and lagged, so always check the date beside it.'],
  ['Physical oil trades well above later-dated futures. This is called…', ['Contango', 'Backwardation', 'Arbitrage'], 1, 'Backwardation usually signals a tight market where buyers need barrels now.'],
  ['How many US gallons are in a barrel of oil?', ['42', '55', '100'], 0, 'A barrel is 42 US gallons, about 159 litres.'],
 ],
 'start-fx': [
  ['EUR/USD is 1.0850. What does that mean?', ['One dollar costs 1.0850 euros', 'One euro costs 1.0850 dollars', 'The euro is up 8.5% today'], 1, 'The first currency is the base. The price is how many units of the second currency buy one unit of the first.'],
  ['EUR/USD moves from 1.0850 to 1.0870. How many pips is that?', ['2', '20', '200'], 1, 'For most pairs a pip is 0.0001, so 0.0020 is 20 pips.'],
  ['If USD/JPY rises, the dollar is…', ['Strengthening against the yen', 'Weakening against the yen', 'Unchanged'], 0, 'USD/JPY shows yen per dollar, so a higher number means each dollar buys more yen.'],
  ['When is the currency market usually busiest?', ['Saturday afternoon', 'The London and New York overlap', 'Midnight UK time'], 1, 'Roughly 13:00 to 17:00 UK time, when both big centres are open.'],
 ],
 'start-crypto': [
  ['What is Bitcoin\'s maximum supply?', ['21 million coins', '100 million coins', 'There is no limit'], 0, 'Bitcoin is capped at 21 million coins, with new issuance halving roughly every four years.'],
  ['What does a stablecoin aim to do?', ['Grow steadily in value', 'Hold a steady value, usually one US dollar', 'Track the price of Bitcoin'], 1, 'Stablecoins such as USDT and USDC aim for a $1 peg, though pegs can fail.'],
  ['In the UK, most crypto investments are…', ['Covered by the FSCS, like a bank account', 'Not covered by the FSCS or the Financial Ombudsman', 'Guaranteed by the Bank of England'], 1, 'That is why the FCA warns: don\'t invest unless you are prepared to lose all the money you invest.'],
  ['Why is crypto daily change usually a rolling 24 hours?', ['Crypto trades all day, every day, with no daily close', 'Exchanges are only open 24 hours a week', 'It is a legal requirement'], 0, 'With no closing bell, there is no natural "previous close" to measure from.'],
 ],
 'start-stocks': [
  ['How is the S&P 500 weighted?', ['Every company counts equally', 'By market value, so bigger firms count more', 'By share price'], 1, 'Because it is weighted by size, a handful of the largest companies can drive much of its daily move.'],
  ['Which ETF tracks the Nasdaq-100?', ['SPY', 'QQQ', 'IWM'], 1, 'QQQ tracks the Nasdaq-100. SPY tracks the S&P 500 and IWM the Russell 2000.'],
  ['A share has a beta of 1.5. Historically it has…', ['Swung about 50% more than the market', 'Paid a 1.5% dividend', 'Traded at 1.5 times its earnings'], 0, 'Beta compares a share\'s past moves with the market. 1.0 is in line; 1.5 is bigger swings both ways.'],
  ['What does a high P/E ratio usually tell you?', ['The company is losing money', 'Investors are paying more for each unit of profit, often expecting growth', 'The share is guaranteed to fall'], 1, 'Price ÷ earnings per share. High can mean growth expectations, or simply an expensive share.'],
 ],
 'start-charts': [
  ['On a candlestick, what do the thin wicks show?', ['The opening and closing prices', 'The high and low of the period', 'Trading volume'], 1, 'The body spans open to close; the wicks reach the period\'s high and low.'],
  ['RSI is above 70. What does that usually mean?', ['A guaranteed sell signal', 'Momentum is stretched to the upside, which can last in strong trends', 'The market is closed'], 1, 'RSI above 70 is often called overbought, but in strong trends it can stay there a long time.'],
  ['Moving averages…', ['Predict tomorrow\'s price', 'Describe the trend but lag the price', 'Only work on crypto'], 1, 'They smooth past closes, so they describe what has happened rather than forecast.'],
 ],
 'start-risk': [
  ['£20,000 account, 1% risk, entry £40, stop £38. How many shares?', ['50', '100', '200'], 1, 'Risk = £200. Risk per share = £2. £200 ÷ £2 = 100 shares (£4,000 of stock).'],
  ['After a 50% loss, what gain do you need to get back to where you started?', ['50%', '75%', '100%'], 2, 'Half of the account must double to recover, which is why limiting losses matters so much.'],
  ['Which statement about stop-loss orders is true?', ['They always fill at exactly your price', 'Prices can gap through them, so you may get a worse fill', 'They make losses impossible'], 1, 'In fast markets or after weekend news, slippage and gaps can push the fill past your stop.'],
  ['What is the FCA cap on retail CFD leverage for major currency pairs?', ['5:1', '30:1', '100:1'], 1, 'UK retail leverage is capped at 30:1 on major pairs, 20:1 on gold and major indices and 5:1 on shares.'],
 ],
 'start-data': [
  ['Markets mostly react to…', ['The number itself', 'The gap between the number and what was expected', 'Whatever was released last month'], 1, 'Prices already reflect forecasts. The surprise is what moves them.'],
  ['When is the US jobs report (non-farm payrolls) usually released?', ['Every Monday', 'Usually the first Friday of the month', 'Once a quarter'], 1, 'Typically the first Friday of the month at 13:30 UK time.'],
  ['A PMI reading above 50 suggests…', ['Activity is expanding', 'Activity is shrinking', 'Inflation is above target'], 0, 'PMIs are surveys centred on 50: above means expansion, below means contraction.'],
  ['How often does the Fed\'s FOMC meet to set rates?', ['Four times a year', 'Eight times a year', 'Every month'], 1, 'The FOMC and the Bank of England\'s MPC each meet eight times a year.'],
 ],
 'start-dispatch': [
  ['The regime score reads 37/100. Which label is that?', ['Risk-On (Strong)', 'Transition', 'Risk-Off'], 2, 'Below 40 is Risk-Off; 40 to 54 Transition; 55 to 71 Risk-On (Fragile); 72+ Risk-On (Strong).'],
  ['How do you add an instrument to your watchlist?', ['Email support', 'Tap the ★ on the instrument', 'It happens automatically'], 1, 'The star toggles it on your watchlist.'],
  ['Where are price alerts and your Portfolio stored?', ['In your browser', 'On a public server', 'With your broker'], 0, 'They live in your browser, so your positions are not sent to our server.'],
 ],
};
const RT46_BADGES = [
 ['start-markets-table', 'Label Reader', '🏷️'], ['start-gold-macro', 'Gold Bug', '🥇'], ['start-oil', 'Oil Watcher', '🛢️'], ['start-fx', 'FX Navigator', '💱'],
 ['start-crypto', 'Crypto Aware', '🪙'], ['start-stocks', 'Index Insider', '📈'], ['start-charts', 'Chart Reader', '🕯️'], ['start-risk', 'Risk Manager', '🛡️'],
 ['start-data', 'Data Detective', '🗓️'], ['start-dispatch', 'Dispatch Pro', '🧭'],
];

// 2: progress store (this browser only; nothing is sent to the server)
const _RT46_KEY = 'td_learn_v1';
function _rt46Load() { try { const o = JSON.parse(localStorage.getItem(_RT46_KEY) || '{}'); return { read: o.read || {}, quiz: o.quiz || {}, game: Object.assign({ played: 0, wins: 0, streak: 0, best: 0, open: null, last: null }, o.game || {}), fc: Object.assign({ got: 0, again: 0 }, o.fc || {}) }; } catch (e) { return { read: {}, quiz: {}, game: { played: 0, wins: 0, streak: 0, best: 0, open: null, last: null }, fc: { got: 0, again: 0 } }; } }
let _rt46P = _rt46Load();
function _rt46Save() { try { localStorage.setItem(_RT46_KEY, JSON.stringify(_rt46P)); } catch (e) {} }
const _rt46GIDS = RT46_BADGES.map(b => b[0]);
function _rt46Passed(id) { return !!(_rt46P.quiz[id] && _rt46P.quiz[id].passed); }
function _rt46Read(id) { return !!_rt46P.read[id] || _rt46Passed(id); }
function _rt46Grad() { return _rt46GIDS.every(_rt46Passed); }
function _rt46MarkRead(id) { if (!_rt46GIDS.includes(id) || _rt46P.read[id]) return; _rt46P.read[id] = Date.now(); _rt46Save(); }
function _rt46E(s) { return _rt45Esc(s); }
function _rt46Hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
function _rt46Order(q) { const n = q[1].length, idx = [...Array(n).keys()]; let h = _rt46Hash(q[0]); for (let i = n - 1; i > 0; i--) { h = Math.imul(h ^ (h >>> 15), 2246822519) >>> 0; const j = h % (i + 1); [idx[i], idx[j]] = [idx[j], idx[i]]; } return idx; }
function _rt46RM() { try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches || !!(typeof _rt17Prefs !== 'undefined' && _rt17Prefs && _rt17Prefs.display && _rt17Prefs.display.reduceMotion); } catch (e) { return false; } }
function _rt46Toast(msg) { try { let t = document.getElementById('rt46toast'); if (!t) { t = document.createElement('div'); t.id = 'rt46toast'; t.className = 'rt46-toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite'); document.body.appendChild(t); }
  t.textContent = msg; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 3200); } catch (e) {} }

// 3: quizzes (state in memory so live re-renders keep answers; best result saved)
const _rt46QS = {};
function _rt46QuizHtml(g) {
  const qs = RT46_QUIZ[g]; if (!qs) return '';
  const st = _rt46QS[g] || (_rt46QS[g] = { a: qs.map(() => null) });
  const done = st.a.every(x => x !== null), score = st.a.reduce((n, x, i) => n + (x === qs[i][2] ? 1 : 0), 0), need = Math.ceil(qs.length * 2 / 3);
  const prev = _rt46P.quiz[g], badge = RT46_BADGES.find(b => b[0] === g);
  let h = `<section class="gc rt46-quiz rt46-live" id="rt46q-${g}" data-g="${g}" aria-labelledby="rt46qh-${g}">
    <div class="rt46-qk">CHECK YOURSELF</div><h2 class="rt46-qh" id="rt46qh-${g}">Quick quiz · ${qs.length} questions</h2>
    <p class="rt46-qp">Pass with ${need} or more to earn the <strong>${badge ? badge[2] + ' ' + _rt46E(badge[1]) : ''}</strong> badge.${prev ? ` Your best so far: ${prev.best}/${qs.length}${prev.passed ? ' ✓' : ''}.` : ''}</p>`;
  qs.forEach((q, qi) => {
    const ans = st.a[qi], ord = _rt46Order(q);
    h += `<fieldset class="rt46-qq"><legend><span class="rt46-qn">${qi + 1}.</span> ${_rt46E(q[0])}</legend><div class="rt46-opts">`;
    ord.forEach(oi => {
      const cls = ans === null ? '' : oi === q[2] ? ' ok' : oi === ans ? ' no' : ' dim';
      h += `<button type="button" class="rt46-opt${cls}" id="rt46o-${g}-${qi}-${oi}" ${ans !== null ? 'aria-disabled="true"' : ''} aria-pressed="${ans === oi}" onclick="_rt46Ans('${g}',${qi},${oi})">${ans !== null && oi === q[2] ? '<span aria-hidden="true">✓ </span>' : ans === oi ? '<span aria-hidden="true">✗ </span>' : ''}${_rt46E(q[1][oi])}</button>`;
    });
    h += `</div><div class="rt46-fb" id="rt46fb-${g}-${qi}" role="status" aria-live="polite" tabindex="-1">${ans === null ? '' : `<strong class="${ans === q[2] ? 'rt46-c-ok' : 'rt46-c-no'}">${ans === q[2] ? 'Correct.' : 'Not quite.'}</strong> ${_rt46E(q[3])}`}</div></fieldset>`;
  });
  if (done) {
    const pass = score >= need;
    h += `<div class="rt46-res ${pass ? 'pass' : ''}" role="status" aria-live="polite" tabindex="-1" id="rt46res-${g}"><div class="rt46-rs">${score}/${qs.length}</div><div>${pass ? `Passed! ${badge ? `Badge unlocked: ${badge[2]} <strong>${_rt46E(badge[1])}</strong>.` : ''}${_rt46Grad() ? ' 🎓 You have passed all ten guides: <strong>Graduate</strong>!' : ''}` : `Nearly there. You need ${need} to pass. Re-read the guide and try again.`}</div>
      <button type="button" class="rt46-btn" onclick="_rt46Retry('${g}')">Try again</button></div>`;
  }
  return h + `</section>`;
}
function _rt46Swap(id, html, focusSel) { try { const el = document.getElementById(id); if (!el) return; const t = document.createElement('div'); t.innerHTML = html; const n = t.firstElementChild; el.replaceWith(n); if (focusSel) { const f = n.querySelector(focusSel) || document.querySelector(focusSel); if (f) f.focus({ preventScroll: true }); } } catch (e) {} }
function _rt46Ans(g, qi, oi) {
  const qs = RT46_QUIZ[g], st = _rt46QS[g] || (_rt46QS[g] = { a: qs.map(() => null) }); if (!qs || st.a[qi] !== null) return;
  st.a[qi] = oi; _rt46MarkRead(g);
  if (st.a.every(x => x !== null)) {
    const score = st.a.reduce((n, x, i) => n + (x === qs[i][2] ? 1 : 0), 0), need = Math.ceil(qs.length * 2 / 3), pass = score >= need;
    const wasGrad = _rt46Grad(), prev = _rt46P.quiz[g] || { best: 0, passed: false };
    const newly = pass && !prev.passed;
    _rt46P.quiz[g] = { best: Math.max(prev.best || 0, score), n: qs.length, passed: prev.passed || pass, at: Date.now() }; _rt46Save();
    _rt46Swap('rt46q-' + g, _rt46QuizHtml(g), '#rt46res-' + g);
    const b = RT46_BADGES.find(x => x[0] === g);
    if (newly && b) _rt46Toast(`${b[2]} Badge unlocked: ${b[1]}`);
    if (!wasGrad && _rt46Grad()) setTimeout(() => _rt46Toast('🎓 Graduate! All ten guides passed.'), 1500);
  } else _rt46Swap('rt46q-' + g, _rt46QuizHtml(g), '#rt46fb-' + g + '-' + qi);
}
function _rt46Retry(g) { delete _rt46QS[g]; _rt46Swap('rt46q-' + g, _rt46QuizHtml(g), '.rt46-opt'); }
// a guide counts as read once its quiz scrolls into view
let _rt46IO = null;
setInterval(() => { try {
  if (!('IntersectionObserver' in window)) return;
  if (!_rt46IO) _rt46IO = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) _rt46MarkRead(e.target.dataset.g); }), { threshold: 0.05 });
  document.querySelectorAll('.rt46-quiz:not([data-io])').forEach(el => { el.dataset.io = '1'; _rt46IO.observe(el); });
} catch (e) {} }, 1000);

// 4: interactive mini-simulators (sliders; illustrative maths only)
const _rt46S = { pos: { acct: 10000, risk: 1, entry: 50, stop: 4 }, ry: { nom: 4.5, inf: 2.5 }, lev: { dep: 1000, lev: 10, move: -5 }, cmp: { start: 1000, monthly: 100, rate: 5, years: 20 } };
const _RT46_SIMS = {
  pos: { t: 'Try it: position-size calculator', f: [['acct', 'Account size', 1000, 100000, 1000, v => '£' + v.toLocaleString('en-GB')], ['risk', 'Risk per trade', 0.25, 5, 0.25, v => v + '%'], ['entry', 'Entry price', 1, 500, 1, v => '£' + v], ['stop', 'Stop distance below entry', 0.5, 25, 0.5, v => v + '%']] },
  ry: { t: 'Try it: real yields and gold', f: [['nom', 'Nominal 10-year bond yield', 0, 8, 0.1, v => v.toFixed(1) + '%'], ['inf', 'Expected inflation', 0, 8, 0.1, v => v.toFixed(1) + '%']] },
  lev: { t: 'Try it: leverage and margin', f: [['dep', 'Your deposit (margin)', 100, 10000, 100, v => '£' + v.toLocaleString('en-GB')], ['lev', 'Leverage', 1, 30, 1, v => v + ':1'], ['move', 'Price move', -20, 20, 0.5, v => (v > 0 ? '+' : '') + v + '%']] },
  cmp: { t: 'Try it: the power of compounding', f: [['start', 'Starting amount', 0, 50000, 500, v => '£' + v.toLocaleString('en-GB')], ['monthly', 'Added each month', 0, 2000, 25, v => '£' + v.toLocaleString('en-GB')], ['rate', 'Average yearly return', 0, 12, 0.5, v => v + '%'], ['years', 'Years', 1, 40, 1, v => v + (v === 1 ? ' year' : ' years')]] },
};
function _rt46GBP(n, dp) { return (n < 0 ? '−£' : '£') + Math.abs(n).toLocaleString('en-GB', { minimumFractionDigits: dp || 0, maximumFractionDigits: dp || 0 }); }
function _rt46Out(k) {
  const s = _rt46S[k];
  if (k === 'pos') {
    const riskAmt = s.acct * s.risk / 100, stopPx = s.entry * (1 - s.stop / 100), per = s.entry - stopPx, units = per > 0 ? Math.floor(riskAmt / per) : 0, val = units * s.entry, pct = val / s.acct * 100;
    return `<div class="rt46-kv"><span>You are willing to lose</span><b>${_rt46GBP(riskAmt)}</b></div><div class="rt46-kv"><span>Stop price</span><b>${_rt46GBP(stopPx, 2)}</b></div>
      <div class="rt46-kv"><span>Risk per share</span><b>${_rt46GBP(per, 2)}</b></div><div class="rt46-kv rt46-big"><span>Position size</span><b>${units.toLocaleString('en-GB')} shares</b></div>
      <div class="rt46-kv"><span>Position value</span><b>${_rt46GBP(val)} (${pct.toFixed(0)}% of account)</b></div>
      <p class="rt46-note">${pct > 100 ? '⚠ The position is bigger than your account, so you would need leverage. A wider stop or a smaller risk % shrinks it.' : 'Notice the stop, not the position size, sets how much you can lose. Widen the stop and the position must shrink.'}</p>`;
  }
  if (k === 'ry') {
    const r = Math.round((s.nom - s.inf) * 10) / 10, pc = Math.max(0, Math.min(100, (r + 4) / 10 * 100));
    const note = r < 0 ? 'Negative real yield: bonds and cash are losing to inflation, so the cost of holding gold (which pays nothing) is low. Historically this has been a supportive backdrop for gold.'
      : r <= 1 ? 'Low positive real yield: a modest opportunity cost for holding gold. Other forces, such as the dollar and fear, often matter more here.'
      : 'Clearly positive real yield: holding gold means giving up a meaningful inflation-beating return elsewhere. Historically a headwind for gold, though heavy central-bank buying has at times outweighed it.';
    return `<div class="rt46-kv rt46-big"><span>Real yield ≈ nominal − inflation</span><b class="${r < 0 ? 'rt46-c-ok' : r > 1 ? 'rt46-c-no' : ''}">${r > 0 ? '+' : ''}${r.toFixed(1)}%</b></div>
      <div class="rt46-gauge" aria-hidden="true"><span style="left:${pc}%"></span><em style="left:40%">0%</em></div><div class="rt46-gl3" aria-hidden="true"><span>Tailwind for gold</span><span>Headwind for gold</span></div>
      <p class="rt46-note">${note}</p><p class="rt46-note rt46-dim">A simple approximation. Markets measure real yields directly with inflation-protected bonds (TIPS). Tendencies, not rules.</p>`;
  }
  if (k === 'lev') {
    const pos = s.dep * s.lev, pl = pos * s.move / 100, pctDep = pl / s.dep * 100, wipe = 100 / s.lev;
    let warn = '';
    if (pl <= -s.dep) warn = '⚠ This move wipes out your whole deposit. UK retail CFD clients have negative balance protection, so you should not lose more than your deposit with an FCA-regulated provider, but the deposit is gone.';
    else if (pl <= -s.dep / 2) warn = '⚠ Your loss has reached half your margin. Under UK rules, retail CFD providers must start closing positions at this point (margin close-out), locking in the loss.';
    return `<div class="rt46-kv"><span>Position you control</span><b>${_rt46GBP(pos)}</b></div><div class="rt46-kv rt46-big"><span>Profit or loss</span><b class="${pl < 0 ? 'rt46-c-no' : pl > 0 ? 'rt46-c-ok' : ''}">${pl >= 0 ? '+' : ''}${_rt46GBP(pl)}</b></div>
      <div class="rt46-kv"><span>Change in your deposit</span><b>${pctDep >= 0 ? '+' : ''}${pctDep.toFixed(0)}%</b></div><div class="rt46-kv"><span>Move against you that wipes out the deposit</span><b>${wipe.toFixed(wipe < 10 ? 1 : 0)}%</b></div>
      ${warn ? `<p class="rt46-note rt46-warn">${warn}</p>` : `<p class="rt46-note">At ${s.lev}:1, a ${Math.abs(s.move)}% price move changes your deposit by ${Math.abs(pctDep).toFixed(0)}%. Leverage magnifies gains and losses equally.</p>`}`;
  }
  if (k === 'cmp') {
    const r = s.rate / 100 / 12, n = s.years * 12, g = Math.pow(1 + r, n), fv = s.start * g + (r > 0 ? s.monthly * (g - 1) / r : s.monthly * n), paid = s.start + s.monthly * n, gr = fv - paid, pg = fv > 0 ? Math.max(0, Math.min(100, gr / fv * 100)) : 0;
    return `<div class="rt46-kv rt46-big"><span>Value after ${s.years} ${s.years === 1 ? 'year' : 'years'}</span><b>${_rt46GBP(fv)}</b></div><div class="rt46-kv"><span>You put in</span><b>${_rt46GBP(paid)}</b></div>
      <div class="rt46-kv"><span>Growth</span><b class="rt46-c-ok">${_rt46GBP(gr)}</b></div><div class="rt46-bar2" role="img" aria-label="${pg.toFixed(0)}% of the final value is growth"><span style="width:${100 - pg}%"></span><i style="width:${pg}%"></i></div>
      <div class="rt46-gl3" aria-hidden="true"><span>Your money</span><span>Growth</span></div>
      <p class="rt46-note rt46-dim">Illustrative only: assumes the same return every month, compounded monthly. Real returns vary year to year, can be negative, and charges and inflation reduce them.</p>`;
  }
  return '';
}
function _rt46SimHtml(k) {
  const d = _RT46_SIMS[k]; if (!d) return '';
  return `<section class="gc rt46-sim rt46-live" id="rt46sim-${k}" aria-labelledby="rt46simh-${k}"><div class="rt46-qk">INTERACTIVE</div><h3 class="rt46-simh" id="rt46simh-${k}">${d.t}</h3>
    ${d.f.map(([f, lb, mn, mx, stp, fmt]) => { const v = _rt46S[k][f]; return `<div class="rt46-fld"><label for="rt46-${k}-${f}"><span>${lb}</span><output id="rt46-${k}-${f}-v" for="rt46-${k}-${f}">${fmt(v)}</output></label>
      <input type="range" id="rt46-${k}-${f}" min="${mn}" max="${mx}" step="${stp}" value="${v}" aria-valuetext="${_rt46E(fmt(v))}" oninput="_rt46Set('${k}','${f}',this)"></div>`; }).join('')}
    <div class="rt46-out" id="rt46-${k}-out" aria-live="polite">${_rt46Out(k)}</div><div class="rt46-disc2">Education only, not financial advice.</div></section>`;
}
function _rt46Set(k, f, el) { const d = _RT46_SIMS[k]; const fd = d && d.f.find(x => x[0] === f); if (!fd) return; const v = Number(el.value); _rt46S[k][f] = v;
  const t = fd[5](v); el.setAttribute('aria-valuetext', t); const o = document.getElementById(`rt46-${k}-${f}-v`); if (o) o.textContent = t;
  const out = document.getElementById(`rt46-${k}-out`); if (out) out.innerHTML = _rt46Out(k); }
// place the simulators inside the guides (marker lines; the existing renderer outputs them as paragraphs)
try { const ins = (id, anchor, mk) => { const m = (LEARN_MODULES.start || []).find(x => x.id === id); if (m && m.content.includes(anchor) && !m.content.includes(mk)) m.content = m.content.replace(anchor, anchor + '\n\n' + mk + '\n'); };
  ins('start-risk', 'The [[tab:calc=Calculators]] tab can do this maths for you.', '[[sim:pos]]');
  ins('start-risk', '- CFD providers must publish the share of their retail accounts that lose money. Read that figure before you open an account.', '[[sim:lev]]');
  ins('start-gold-macro', 'a period when heavy central-bank buying was a big part of demand.*', '[[sim:ry]]');
  ins('start-stocks', 'Check the fund\'s charges and what it actually holds.', '[[sim:cmp]]');
} catch (e) {}

// 5: term of the day (same for everyone on a UK calendar day) + flashcards + "Guess the move" game on a new Practise tab
function _rt46Day() { try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/London' }).format(new Date()); } catch (e) { return new Date().toISOString().slice(0, 10); } }
function _rt46Tod() { return RT45_GLOSS[_rt46Hash('tod:' + _rt46Day()) % RT45_GLOSS.length]; }
let _rt46TodOn = false;
function _rt46Card(id, term, cat, def, on, extra) {
  return `<div class="rt46-fc${on ? ' on' : ''}${_rt46RM() ? ' rm' : ''}" id="${id}"><button type="button" class="rt46-fc-in" id="${id}-btn" data-t="${_rt46E(term)}" aria-pressed="${on}" aria-label="${_rt46E(term)}. ${on ? 'Showing definition. Press to show the term.' : 'Press to reveal the definition.'}" onclick="_rt46Flip('${id}')">
    <span class="rt46-fc-f" aria-hidden="${on}"><span class="rt46-fc-c">${_rt46E(cat)}</span><span class="rt46-fc-t">${_rt46E(term)}</span><span class="rt46-fc-h">Tap to flip</span></span>
    <span class="rt46-fc-b" aria-hidden="${!on}"><span class="rt46-fc-c">${_rt46E(term)}</span><span class="rt46-fc-d">${_rt46E(def)}</span></span></button>${extra || ''}</div>`;
}
function _rt46Flip(id) { const el = document.getElementById(id); if (!el) return; const on = !el.classList.contains('on'); el.classList.toggle('on', on);
  if (id === 'rt46tod') _rt46TodOn = on; if (id === 'rt46fcard') _rt46F.on = on;
  const b = el.querySelector('.rt46-fc-in'); if (b) { b.setAttribute('aria-pressed', on); const t = b.getAttribute('data-t') || ''; b.setAttribute('aria-label', t + '. ' + (on ? 'Showing definition. Press to show the term.' : 'Press to reveal the definition.')); }
  el.querySelector('.rt46-fc-f')?.setAttribute('aria-hidden', on); el.querySelector('.rt46-fc-b')?.setAttribute('aria-hidden', !on);
  if (id === 'rt46fcard') { const a = document.getElementById('rt46fc-acts'); if (a) a.hidden = !on; } }
function _rt46ProgressHtml() {
  const passed = _rt46GIDS.filter(_rt46Passed).length, read = _rt46GIDS.filter(_rt46Read).length, pct = Math.round(passed / _rt46GIDS.length * 100), grad = _rt46Grad();
  const tod = _rt46Tod();
  return `<div class="rt46-row2">
    <section class="gc rt46-prog" aria-labelledby="rt46ph"><div class="rt46-qk">YOUR PROGRESS</div><h2 class="rt46-ph" id="rt46ph">${passed}/10 guides passed · ${read}/10 read</h2>
      <div class="rt46-bar" role="progressbar" aria-valuemin="0" aria-valuemax="10" aria-valuenow="${passed}" aria-label="Guides passed"><span style="width:${pct}%"></span></div>
      <div class="rt46-badges" role="list" aria-label="Badges">${RT46_BADGES.map(([g, n, e]) => { const on = _rt46Passed(g); return `<span role="listitem" class="rt46-bd${on ? ' on' : ''}" title="${_rt46E(n)}${on ? '' : ' (pass the quiz to unlock)'}" aria-label="${_rt46E(n)} badge, ${on ? 'unlocked' : 'locked'}"><i aria-hidden="true">${e}</i><span>${_rt46E(n)}</span></span>`; }).join('')}
      <span role="listitem" class="rt46-bd rt46-bd-g${grad ? ' on' : ''}" aria-label="Graduate badge, ${grad ? 'unlocked' : 'locked: pass all ten quizzes'}"><i aria-hidden="true">🎓</i><span>Graduate</span></span></div>
      <div class="rt46-pfoot">Saved in this browser only. ${passed || read ? `<button type="button" class="rt46-link" onclick="_rt46Reset()">Reset progress</button>` : 'Finish a guide\'s quiz to earn its badge.'}</div></section>
    <section class="gc rt46-tod" aria-labelledby="rt46th"><div class="rt46-qk" id="rt46th">TERM OF THE DAY</div>${_rt46Card('rt46tod', tod[1], tod[2], tod[3], _rt46TodOn)}
      <div class="rt46-tod-a"><a class="rt45-lk" href="/learn/?term=${tod[0]}" onclick="event.preventDefault();_rt45Term('${tod[0]}')">In the glossary →</a><a class="rt45-lk" href="/learn/?tab=play" onclick="event.preventDefault();_rt45Tab('play')">Practise with flashcards →</a></div></section></div>`;
}
function _rt46Reset() { try { if (!confirm('Reset your Learn progress and badges in this browser?')) return; } catch (e) {} const g = _rt46P.game; _rt46P = _rt46Load(); _rt46P.read = {}; _rt46P.quiz = {}; _rt46P.game = g; _rt46Save(); for (const k in _rt46QS) delete _rt46QS[k]; _refreshView(); }
// flashcards
const _rt46F = { deck: null, i: 0, on: false, cat: '', got: 0, again: 0 };
function _rt46Deck() { const all = RT45_GLOSS.filter(x => !_rt46F.cat || x[2] === _rt46F.cat).map(x => x[0]); for (let i = all.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [all[i], all[j]] = [all[j], all[i]]; } _rt46F.deck = all; _rt46F.i = 0; _rt46F.on = false; }
function _rt46FcHtml() {
  if (!_rt46F.deck || !_rt46F.deck.length) _rt46Deck();
  const id = _rt46F.deck[_rt46F.i % _rt46F.deck.length], r = RT45_GLOSS.find(x => x[0] === id) || RT45_GLOSS[0];
  const cats = [...new Set(RT45_GLOSS.map(x => x[2]))];
  return `<section class="gc rt46-fcs rt46-live" id="rt46fcs" aria-labelledby="rt46fch"><div class="rt46-qk">FLASHCARDS</div><h2 class="rt46-ph" id="rt46fch">Test yourself on ${RT45_GLOSS.length} market terms</h2>
    <div class="rt46-fcbar"><label for="rt46fccat" class="rt46-sr">Topic</label><select id="rt46fccat" onchange="_rt46F.cat=this.value;_rt46Deck();_rt46Swap('rt46fcs',_rt46FcHtml(),'#rt46fccat')"><option value="">All topics</option>${cats.map(c => `<option${_rt46F.cat === c ? ' selected' : ''}>${_rt46E(c)}</option>`).join('')}</select>
      <span class="rt46-fcn">Card ${(_rt46F.i % _rt46F.deck.length) + 1} of ${_rt46F.deck.length} · ✓ ${_rt46F.got} · ↺ ${_rt46F.again}</span></div>
    ${_rt46Card('rt46fcard', r[1], r[2], r[3], _rt46F.on, `<div class="rt46-fca" id="rt46fc-acts"${_rt46F.on ? '' : ' hidden'}><button type="button" class="rt46-btn rt46-btn-s" onclick="_rt46FcNext(false)">↺ Again</button><button type="button" class="rt46-btn" onclick="_rt46FcNext(true)">✓ Got it</button></div>`)}
    <div class="rt46-pfoot">Flip the card, then mark whether you knew it. "Again" puts the card back in the deck.</div></section>`;
}
function _rt46FcNext(got) { const d = _rt46F.deck; if (!d) return; const cur = d[_rt46F.i % d.length];
  if (got) { _rt46F.got++; _rt46P.fc.got++; } else { _rt46F.again++; _rt46P.fc.again++; d.splice(Math.min(d.length, _rt46F.i + 4), 0, cur); }
  _rt46Save(); _rt46F.i++; if (_rt46F.i >= d.length) _rt46Deck(); _rt46F.on = false; _rt46Swap('rt46fcs', _rt46FcHtml(), '.rt46-fc-in'); }
// "Guess the move": a game using the site's live feeds; no money, no prizes
const _RT46_GAME = [['BTC', 'Bitcoin'], ['ETH', 'Ether'], ['XAU', 'Gold spot'], ['EURUSD', 'EUR/USD']];
const _RT46_ROUND = 300000;
let _rt46GameTk = '';
function _rt46Px(tk) { try { const d = fp(tk); const p = P[tk] && P[tk].p; return d && (d.status === 'live' || (d.status === 'delayed' && (tk === 'BTC' || tk === 'ETH'))) && typeof p === 'number' && isFinite(p) && p > 0 ? { p, label: d.label } : null; } catch (e) { return null; } }
function _rt46Fmt(tk, p) { return tk === 'EURUSD' ? p.toFixed(5) : '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function _rt46GameResolve() { try {
  const g = _rt46P.game, o = g.open; if (!o) return false; const age = Date.now() - o.at; if (age < _RT46_ROUND) return false;
  const q = _rt46Px(o.tk); let res;
  if (age > _RT46_ROUND + 120000 || !q) res = { r: 'void', why: q ? 'The round ran past its window while the page was closed, so it is not scored.' : 'The live feed was not available at the finish, so the round is not scored.' };
  else if (q.p === o.p) res = { r: 'flat', why: 'The price finished exactly where it started.' };
  else { const up = q.p > o.p, win = (o.dir === 'up') === up; res = { r: win ? 'win' : 'loss', why: `${_rt46Fmt(o.tk, o.p)} → ${_rt46Fmt(o.tk, q.p)} (${up ? 'up' : 'down'} ${(Math.abs(q.p - o.p) / o.p * 100).toFixed(3)}%).` };
    g.played++; if (win) { g.wins++; g.streak++; g.best = Math.max(g.best, g.streak); } else g.streak = 0; }
  g.last = Object.assign({ tk: o.tk, dir: o.dir }, res); g.open = null; _rt46Save(); return true;
} catch (e) { return false; } }
function _rt46GameHtml() {
  _rt46GameResolve();
  const g = _rt46P.game, o = g.open, avail = _RT46_GAME.filter(([tk]) => _rt46Px(tk));
  if (!_rt46GameTk || !avail.some(a => a[0] === _rt46GameTk)) _rt46GameTk = avail.length ? avail[0][0] : '';
  let body = '';
  if (o) { const left = Math.max(0, _RT46_ROUND - (Date.now() - o.at)), nm = (_RT46_GAME.find(x => x[0] === o.tk) || [o.tk, o.tk])[1], q = _rt46Px(o.tk);
    body = `<div class="rt46-gm-open"><div>You said <b>${nm}</b> goes <b class="${o.dir === 'up' ? 'rt46-c-ok' : 'rt46-c-no'}">${o.dir === 'up' ? '▲ UP' : '▼ DOWN'}</b> from <b>${_rt46Fmt(o.tk, o.p)}</b>.</div>
      <div class="rt46-gm-cd" aria-live="off">Resolves in <b id="rt46gcd">${Math.floor(left / 60000)}:${String(Math.floor(left / 1000) % 60).padStart(2, '0')}</b> · now <b id="rt46gnow">${q ? _rt46Fmt(o.tk, q.p) : '—'}</b></div></div>`; }
  else if (!avail.length) body = `<p class="rt46-note">None of the game's markets has a fresh price right now. Bitcoin and Ether normally stream around the clock, so try again in a moment.</p>`;
  else { const q = _rt46Px(_rt46GameTk);
    body = `<div class="rt46-chips2" role="group" aria-label="Choose a market">${avail.map(([tk, nm]) => `<button type="button" class="rt46-chip2${tk === _rt46GameTk ? ' on' : ''}" aria-pressed="${tk === _rt46GameTk}" onclick="_rt46GameTk='${tk}';_rt46Swap('rt46game',_rt46GameHtml(),'.rt46-chip2.on')">${nm}</button>`).join('')}</div>
      <div class="rt46-gm-px">Price now: <b id="rt46gpx">${q ? _rt46Fmt(_rt46GameTk, q.p) : '—'}</b> <span class="rt46-dim">${q ? _rt46E(q.label) : ''}</span></div>
      <div class="rt46-gm-btns"><button type="button" class="rt46-btn rt46-up" onclick="_rt46Guess('up')">▲ Higher in 5 min</button><button type="button" class="rt46-btn rt46-dn" onclick="_rt46Guess('down')">▼ Lower in 5 min</button></div>`; }
  const l = g.last, acc = g.played ? Math.round(g.wins / g.played * 100) : 0;
  return `<section class="gc rt46-game rt46-live" id="rt46game" aria-labelledby="rt46gh"><div class="rt46-qk">GAME · NO MONEY</div><h2 class="rt46-ph" id="rt46gh">Guess the move</h2>
    <p class="rt46-qp">Will the live price be higher or lower in five minutes? Keep the page open; the round is scored from the site's live feed.</p>${body}
    ${l ? `<div class="rt46-gm-last" role="status" aria-live="polite"><b class="${l.r === 'win' ? 'rt46-c-ok' : l.r === 'loss' ? 'rt46-c-no' : ''}">${l.r === 'win' ? 'You called it!' : l.r === 'loss' ? 'Not this time.' : l.r === 'flat' ? 'No change.' : 'Not scored.'}</b> ${_rt46E(l.why)}</div>` : ''}
    <div class="rt46-gm-st"><span>Played <b>${g.played}</b></span><span>Correct <b>${g.wins}</b> (${acc}%)</span><span>Streak <b>${g.streak}</b></span><span>Best <b>${g.best}</b></span></div>
    <p class="rt46-note rt46-dim">Just a game: no money, no prizes. Five-minute moves are mostly random noise, so a good score here says little about skill. It is not a trading signal.</p></section>`;
}
function _rt46Guess(dir) { const q = _rt46Px(_rt46GameTk); if (!q || _rt46P.game.open) return; _rt46P.game.open = { tk: _rt46GameTk, dir, p: q.p, at: Date.now() }; _rt46P.game.last = null; _rt46Save(); _rt46Swap('rt46game', _rt46GameHtml(), '#rt46gh'); }
setInterval(() => { try {
  const el = document.getElementById('rt46game'); const o = _rt46P.game.open;
  if (o && Date.now() - o.at >= _RT46_ROUND) { if (_rt46GameResolve() && el) { _rt46Swap('rt46game', _rt46GameHtml()); _rt46Toast(_rt46P.game.last.r === 'win' ? '🎯 You called the move!' : 'Round finished: see the result'); } return; }
  if (!el) return;
  if (o) { const left = Math.max(0, _RT46_ROUND - (Date.now() - o.at)); const cd = document.getElementById('rt46gcd'); if (cd) cd.textContent = `${Math.floor(left / 60000)}:${String(Math.floor(left / 1000) % 60).padStart(2, '0')}`;
    const q = _rt46Px(o.tk), n = document.getElementById('rt46gnow'); if (n && q) n.textContent = _rt46Fmt(o.tk, q.p); }
  else { const q = _rt46Px(_rt46GameTk), n = document.getElementById('rt46gpx'); if (n && q) n.textContent = _rt46Fmt(_rt46GameTk, q.p); }
} catch (e) {} }, 1000);
function _rt46PlayHtml() { return `<div class="rt46-play">${_rt46FcHtml()}${_rt46GameHtml()}</div><div class="rt45-disc" style="margin-top:12px">Education only, not financial advice.</div>`; }

// 6: wire into Learn: Practise tab, progress + term of the day on Start here, card ticks, quiz + simulators inside guides
try { if (!_RT45_TABS.some(t => t[0] === 'play')) _RT45_TABS.splice(2, 0, ['play', '🎮 Practise']); } catch (e) {}
{
  const _sh0 = _rt45StartHtml;
  _rt45StartHtml = function () {
    let h = _sh0.apply(this, arguments);
    try {
      h = h.replace(/(<a class="gc gc-a rt45-card" href="\/learn\/\?guide=([a-z0-9-]+)"[\s\S]*?<span class="rt45-lv">[^<]*<\/span>)/g, (m, all, id) => {
        const q = _rt46P.quiz[id];
        return all + (_rt46Passed(id) ? `<span class="rt46-st ok">✓ Passed ${q.best}/${q.n}</span>` : _rt46Read(id) ? `<span class="rt46-st">Read · quiz to do</span>` : '');
      });
      const at = h.indexOf('<div class="rt45-grid">'); if (at > 0) h = h.slice(0, at) + _rt46ProgressHtml() + h.slice(at);
    } catch (e) {}
    return h;
  };
}
{
  const _rl2 = renderLearn;
  renderLearn = function () {
    let h = _rl2.apply(this, arguments);
    try {
      if (_learnSub && RT46_QUIZ[_learnSub]) {
        h = h.replace(/<p[^>]*>\[\[sim:([a-z]+)\]\]<\/p>/g, (m, k) => _rt46SimHtml(k));
        const pg2 = h.lastIndexOf('<div class="rt45-pager">');
        if (pg2 > 0) h = h.slice(0, pg2) + _rt46QuizHtml(_learnSub) + h.slice(pg2);
      } else if (!_learnSub && _learnTab === 'play') {
        const at = h.indexOf('</div>', h.indexOf('role="tablist"')) + 6;
        if (at > 5) h = h.slice(0, at) + _rt46PlayHtml();
      }
      h = h.replace(/<p[^>]*>\[\[sim:[a-z]+\]\]<\/p>/g, '');
    } catch (e) {}
    return h;
  };
}
// background price refreshes must not redraw Learn while you are dragging a slider, typing in a search box or using a select
let _rt46UserAt = 0;
['pointerdown', 'keydown'].forEach(ev => document.addEventListener(ev, e => { try { if (!e.target.closest || !e.target.closest('.rt46-live input,.rt46-live select,#rt45q')) _rt46UserAt = Date.now(); } catch (x) {} }, true));
function _rt46Hold() { try {
  const a = document.activeElement, onLearn = (typeof pg !== 'undefined' && pg === 'learn') || !!document.getElementById('learnOv');
  return !!(onLearn && a && a.matches && a.matches('.rt46-live input,.rt46-live select,#rt45q') && Date.now() - _rt46UserAt > 400);
} catch (e) { return false; } }
{
  const _rv0 = _refreshView;
  // after a redraw, put keyboard focus back on the same rt45/rt46 control if it still exists
  const _keep = (fn, ctx, args) => { let id = ''; try { const a = document.activeElement; if (a && a.id && /^rt4[56]/.test(a.id)) id = a.id; } catch (e) {}
    const r = fn.apply(ctx, args);
    if (id) { try { const n = document.getElementById(id); if (n && document.activeElement !== n) n.focus({ preventScroll: true }); } catch (e) {} }
    return r; };
  _refreshView = function () { if (_rt46Hold()) return; return _keep(_rv0, this, arguments); };
  try { const _rm0 = renderMain; renderMain = function () { if (_rt46Hold()) return; return _keep(_rm0, this, arguments); }; } catch (e) {}
}
// keyboard focus fix (site-wide): an older touch-tooltip helper blurs the focused control on every scroll, so a Tab that
// scrolls the page dropped focus to <body>. When the last input was the keyboard, put focus back on the same control.
let _rt46Kb = 0;
document.addEventListener('keydown', e => { _rt46Kb = e.key === 'Escape' ? 0 : Date.now(); }, true);
['pointerdown', 'touchstart'].forEach(ev => document.addEventListener(ev, () => { _rt46Kb = 0; }, { capture: true, passive: true }));
document.addEventListener('focusout', e => { try {
  const t = e.target; if (e.relatedTarget || !t || !t.isConnected || !_rt46Kb || Date.now() - _rt46Kb > 1500 || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  setTimeout(() => { try { const a = document.activeElement; if ((!a || a === document.body) && t.isConnected && document.hasFocus()) t.focus({ preventScroll: true }); } catch (x) {} }, 0);
} catch (x) {} }, true);
try { const st = document.createElement('style'); st.id = 'rt46css'; st.textContent = `
.rt46-qk{font-family:var(--mn);font-size:9px;letter-spacing:.16em;color:var(--gd);font-weight:700;margin-bottom:6px}
.rt46-quiz,.rt46-sim,.rt46-prog,.rt46-tod,.rt46-fcs,.rt46-game{padding:16px;margin:16px 0;min-width:0}
.rt46-qh,.rt46-ph{font-family:var(--sn);font-size:17px;font-weight:800;color:var(--tx);margin:0 0 6px;line-height:1.3;border:0;padding:0}
.rt46-simh{font-family:var(--sn);font-size:15px;font-weight:800;color:var(--tx);margin:0 0 10px}
.rt46-qp{font-family:var(--sn);font-size:12.5px;color:var(--t2);line-height:1.55;margin:0 0 10px}
.rt46-qq{border:0;border-top:1px solid var(--gb);margin:0;padding:12px 0 4px;min-width:0}
.rt46-qq legend{font-family:var(--sn);font-size:14px;font-weight:700;color:var(--tx);line-height:1.45;padding:0;margin-bottom:8px;float:left;width:100%}
.rt46-qq legend+*{clear:both}
.rt46-qn{color:var(--gd);font-family:var(--mn)}
.rt46-opts{display:grid;gap:7px}
.rt46-opt{text-align:left;font-family:var(--sn);font-size:13px;line-height:1.4;color:var(--tx);background:var(--b2);border:1px solid var(--gb);border-radius:8px;padding:10px 12px;cursor:pointer;min-height:44px;width:100%;overflow-wrap:anywhere}
.rt46-opt:hover:not([aria-disabled]){border-color:var(--gd)}
.rt46-opt:focus-visible,.rt46-btn:focus-visible,.rt46-fc-in:focus-visible,.rt46-chip2:focus-visible{outline:2px solid var(--gd);outline-offset:2px}
.rt46-opt[aria-disabled]{cursor:default}
.rt46-opt.ok{border-color:var(--gn);background:var(--gnG,rgba(34,197,94,.12));color:var(--gn)}
.rt46-opt.no{border-color:var(--rd);background:rgba(239,68,68,.1);color:var(--rd)}
.rt46-opt.dim{opacity:.55}
.rt46-fb{font-family:var(--sn);font-size:12.5px;color:var(--t2);line-height:1.55;margin:8px 0 4px;outline:none}
.rt46-fb:empty{display:none}
.rt46-c-ok{color:var(--gn)}.rt46-c-no{color:var(--rd)}
.rt46-res{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:12px;padding:12px;border-radius:10px;background:var(--b2);border:1px solid var(--gb);font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.5;outline:none}
.rt46-res>div:nth-child(2){flex:1 1 180px}
.rt46-res.pass{border-color:var(--gd);background:var(--gdG)}
.rt46-rs{font-family:var(--mn);font-size:22px;font-weight:800;color:var(--tx)}
.rt46-btn{font-family:var(--sn);font-size:13px;font-weight:700;padding:10px 16px;min-height:44px;border-radius:8px;border:1px solid var(--gd);background:var(--gd);color:var(--bg,#0b0d12);cursor:pointer}
.rt46-btn-s{background:transparent;color:var(--gd)}
.rt46-link{background:none;border:0;padding:0;color:var(--gd);text-decoration:underline;cursor:pointer;font:inherit}
.rt46-fld{margin:10px 0}
.rt46-fld label{display:flex;justify-content:space-between;gap:10px;font-family:var(--sn);font-size:12.5px;color:var(--t2);margin-bottom:4px}
.rt46-fld output{font-family:var(--mn);color:var(--tx);font-weight:700;white-space:nowrap}
.rt46-fld input[type=range]{width:100%;accent-color:var(--gd);min-height:28px;margin:0}
.rt46-out{margin-top:12px;padding:12px;border-radius:10px;background:var(--b2);border:1px solid var(--gb)}
.rt46-kv{display:flex;justify-content:space-between;gap:10px;font-family:var(--sn);font-size:12.5px;color:var(--t2);padding:4px 0;align-items:baseline}
.rt46-kv b{font-family:var(--mn);color:var(--tx);text-align:right}
.rt46-big b{font-size:17px}
.rt46-note{font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55;margin:8px 0 0}
.rt46-warn{color:var(--gd)}
.rt46-dim{color:var(--t3)!important}
.rt46-disc2{font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:8px}
.rt46-gauge{position:relative;height:8px;border-radius:4px;margin:12px 0 4px;background:linear-gradient(90deg,var(--gn),var(--gd) 45%,var(--rd))}
.rt46-gauge span{position:absolute;top:-4px;width:4px;height:16px;margin-left:-2px;background:var(--tx);border-radius:2px;transition:left .2s}
.rt46-gauge em{position:absolute;top:10px;font:normal 9px var(--mn);color:var(--t3);transform:translateX(-50%)}
.rt46-gl3{display:flex;justify-content:space-between;font-family:var(--mn);font-size:9px;color:var(--t3);margin-top:12px}
.rt46-bar2{display:flex;height:10px;border-radius:5px;overflow:hidden;margin-top:10px;background:var(--b1)}
.rt46-bar2 span{background:var(--bl)}.rt46-bar2 i{background:var(--gn)}
.rt46-row2{display:grid;grid-template-columns:1fr;gap:0 12px}
@media(min-width:900px){.rt46-row2{grid-template-columns:3fr 2fr}}
.rt46-prog,.rt46-tod{margin:0 0 12px}
.rt46-bar{height:10px;border-radius:5px;background:var(--b2);overflow:hidden;margin:8px 0 12px}
.rt46-bar span{display:block;height:100%;background:linear-gradient(90deg,var(--gd),var(--gn));transition:width .4s}
.rt46-badges{display:flex;flex-wrap:wrap;gap:6px}
.rt46-bd{display:inline-flex;align-items:center;gap:5px;font-family:var(--sn);font-size:11px;color:var(--t3);border:1px dashed var(--gb);border-radius:999px;padding:4px 9px;filter:grayscale(1);opacity:.6}
.rt46-bd.on{filter:none;opacity:1;color:var(--tx);border-style:solid;border-color:var(--gd);background:var(--gdG)}
.rt46-bd i{font-style:normal}
.rt46-pfoot{font-family:var(--mn);font-size:9.5px;color:var(--t3);margin-top:10px;line-height:1.5}
.rt46-st{font-family:var(--mn);font-size:9px;color:var(--t2);border:1px solid var(--gb);border-radius:4px;padding:1px 6px}
.rt46-st.ok{color:var(--gn);border-color:var(--gn)}
.rt46-tod-a{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-family:var(--sn);font-size:12px}
.rt46-fc{perspective:900px}
.rt46-fc-in{position:relative;display:block;width:100%;min-height:150px;padding:0;border:0;background:none;cursor:pointer;color:inherit;text-align:left;transform-style:preserve-3d;transition:transform .5s ease;border-radius:12px}
.rt46-fc.on .rt46-fc-in{transform:rotateY(180deg)}
.rt46-fc-f,.rt46-fc-b{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:6px;padding:16px;border-radius:12px;border:1px solid var(--gb);background:var(--b2);backface-visibility:hidden;-webkit-backface-visibility:hidden;overflow:auto}
.rt46-fc-b{transform:rotateY(180deg);border-color:var(--gd)}
.rt46-fc-c{font-family:var(--mn);font-size:9px;letter-spacing:.12em;color:var(--t3);text-transform:uppercase}
.rt46-fc-t{font-family:var(--sn);font-size:22px;font-weight:800;color:var(--tx);line-height:1.2}
.rt46-fc-h{font-family:var(--mn);font-size:9.5px;color:var(--gd)}
.rt46-fc-d{font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.55}
.rt46-fcs .rt46-fc-in{min-height:190px}
.rt46-fc.rm .rt46-fc-in{transition:none;transform:none!important}
.rt46-fc.rm .rt46-fc-f,.rt46-fc.rm .rt46-fc-b{backface-visibility:visible;transform:none}
.rt46-fc.rm .rt46-fc-b,.rt46-fc.rm.on .rt46-fc-f{display:none}
.rt46-fc.rm.on .rt46-fc-b{display:flex}
@media (prefers-reduced-motion: reduce){.rt46-fc-in,.rt46-bar span,.rt46-gauge span,.rt46-toast{transition:none!important}}
.rt46-fca{display:flex;gap:10px;justify-content:flex-end;margin-top:10px}
.rt46-fca[hidden]{display:none}
.rt46-fcbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin:6px 0 12px}
.rt46-fcbar select{background:var(--b2);border:1px solid var(--gb);color:var(--tx);border-radius:8px;padding:8px 10px;font-family:var(--sn);font-size:14px;min-height:40px;max-width:100%}
.rt46-fcn{font-family:var(--mn);font-size:10px;color:var(--t3)}
.rt46-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.rt46-chips2{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.rt46-chip2{font-family:var(--sn);font-size:12px;padding:8px 12px;min-height:38px;border-radius:999px;border:1px solid var(--gb);background:var(--b2);color:var(--t2);cursor:pointer}
.rt46-chip2.on{border-color:var(--gd);color:var(--gd);background:var(--gdG)}
.rt46-gm-px,.rt46-gm-cd,.rt46-gm-open{font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.6;margin:8px 0}
.rt46-gm-px b,.rt46-gm-cd b{font-family:var(--mn);color:var(--tx)}
.rt46-gm-btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}
.rt46-up{background:transparent;color:var(--gn);border-color:var(--gn)}.rt46-dn{background:transparent;color:var(--rd);border-color:var(--rd)}
.rt46-gm-last{font-family:var(--sn);font-size:13px;color:var(--t2);padding:10px 12px;border-radius:8px;background:var(--b2);margin:10px 0;line-height:1.5}
.rt46-gm-st{display:flex;flex-wrap:wrap;gap:6px 16px;font-family:var(--mn);font-size:10.5px;color:var(--t3);margin-top:8px}
.rt46-gm-st b{color:var(--tx)}
.rt46-toast{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom,0px));transform:translate(-50%,20px);opacity:0;pointer-events:none;z-index:100001;background:var(--b1,#151821);color:var(--tx);border:1px solid var(--gd);border-radius:999px;padding:10px 16px;font-family:var(--sn);font-size:13px;font-weight:700;box-shadow:0 10px 28px rgba(0,0,0,.5);transition:opacity .25s,transform .25s;max-width:calc(100vw - 24px);text-align:center}
.rt46-toast.on{opacity:1;transform:translate(-50%,0)}
`; document.head.appendChild(st); } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat45') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat45', 'app.js?v=chat46')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt46 block appended + index chat45->chat46; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
