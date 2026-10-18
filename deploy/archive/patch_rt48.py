#!/usr/bin/env python3
"""patch_rt48.py: chatN -> chatN+1 (client only). Stacks on rt47b output: either chat49 (app.js d864e7f2) or chat50 with
rt49about on top (app.js 4ea49365). Appends one block; it only wraps Academy (rt47) functions, so the About block is untouched.
Dispatch Academy "More activities": Activities hub with weekly challenge and 11 activity badges; speed round; paper trading
(virtual GBP 10,000 at live site prices, market hours, risk-based sizing with stop-loss); chart gym with 10 random drills incl. candle
patterns, highs/lows, breakouts and % moves; 17 scenarios; economic-calendar surprises; matching games; Price is right; and
auto-updating content rebuilt daily from the site's own feeds (this week's moves quiz, headline scenario cards, optional
/api/academy-daily explainers from rt48s). No new tables, no Stripe. Wrapper-only: no existing line is edited.
Usage: python3 patch_rt48.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt48 ──' in s: die('rt48 already applied')
if '// ── rt47b ──' not in s: die('base is not rt47b output')
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust not found exactly once')
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
if n < 49: die('index is %s; expected chat49 or later' % base)
print('base:', base, '(rt49about present)' if '// ── rt49about ──' in s else '(no rt49about)')
for need in ['function _rt47Meta(', 'function _rt47Open(', 'function _rt47StepHtml(', 'function _rt47PlayerHtml(', 'function _rt47HomeHtml(', 'function _rt47Hold(', 'function _rt47SigNow(',
             'function _rt47ScenCheck(', 'function _rt47Trd(', 'function _rt47SupCheck(', 'function _rt47bWaiting(', 'function _rt47bSnapFill(', 'function _rt47Award(', 'function _rt47Redraw(',
             'const RT47_SCEN', 'const RT45_GLOSS', 'const RT46_QUIZ', 'function _rt46Swap(', 'function _rt46Toast(', 'function _rt46Day(', 'function fp(', 'let NEWS', 'const RSS_FEEDS', 'async function fetchSingleFeed(',
             '<div class="rt47-grid">', "<div class=\"rt47-sk\">${k}</div>"]:
    if need not in s: die('missing ' + need)
BLOCK = r'''// ── rt48 ──
// ── rt48 data: more scenarios, calendar releases, asset descriptions, news templates, badges ──
const RT48_SCEN_ADD = [
  ['Bigger rate cut', 'The Federal Reserve cuts rates by 0.50 percentage points. Markets had priced in 0.25.', [
    ['US 2-year yield', 'down', 'Short-dated yields track expected policy rates, which just fell further than priced.'],
    ['US dollar (DXY)', 'down', 'Lower expected US rates make holding dollars less attractive.'],
    ['Gold', 'up', 'Lower yields cut the cost of holding an asset that pays nothing, and a softer dollar helps too.']]],
  ['Soft inflation print', 'US CPI rises 0.1% in the month. Economists expected 0.3%.', [
    ['US 10-year yield', 'down', 'Markets price in earlier or larger rate cuts.'],
    ['S&P 500', 'up', 'Lower expected rates raise the present value of future profits.'],
    ['US dollar (DXY)', 'down', 'Expected US rates fall relative to other countries.']]],
  ['Recession signal', 'US GDP shrinks at a 1% annual rate in the quarter. Economists expected growth of 1.5%.', [
    ['S&P 500', 'down', 'Weaker growth points to lower company earnings.'],
    ['US 10-year yield', 'down', 'Investors buy safer government bonds and expect rate cuts.'],
    ['Brent crude', 'down', 'A weaker economy usually means less demand for fuel.']]],
  ['Conflict escalates', 'Fighting escalates sharply between two countries in a major oil-producing region.', [
    ['Gold', 'up', 'Investors often buy gold as a safe haven when uncertainty jumps.'],
    ['Brent crude', 'up', 'Traders price in the risk that oil supply is disrupted.'],
    ['S&P 500', 'down', 'Risk-off: investors cut exposure to riskier assets.']]],
  ['Strong dollar day', 'The US dollar index jumps 1.2% in a day after strong US data.', [
    ['EUR/USD', 'down', 'The euro is the biggest weight in the dollar index (57.6%), so a strong DXY day usually means EUR/USD falls.'],
    ['Gold', 'down', 'Gold is priced in dollars, so a stronger dollar makes it dearer for buyers using other currencies.'],
    ['Emerging-market stocks', 'down', 'A stronger dollar tightens conditions for countries and companies that borrow in dollars.']]],
  ['China stimulus', 'China announces a large stimulus package, with interest-rate cuts and support for property and infrastructure.', [
    ['Copper', 'up', 'China is the largest buyer of industrial metals, so more building means more expected demand.'],
    ['Australian dollar', 'up', 'Australia exports large amounts of iron ore and other raw materials to China.'],
    ['Hang Seng index', 'up', 'Hong Kong-listed Chinese companies benefit most directly from stronger Chinese growth.']]],
  ['Record crypto ETF inflows', 'US spot bitcoin ETFs report their largest daily net inflows in months.', [
    ['Bitcoin', 'up', 'New ETF shares are backed by bitcoin the funds buy, so strong inflows mean real buying pressure.'],
    ['Ether', 'up', 'The big crypto assets tend to move together on shifts in sentiment.'],
    ['Crypto-related shares', 'up', 'Exchanges and miners are seen as geared to crypto prices and trading activity.']]],
  ['Earnings beat', 'A mega-cap tech company reports profit and revenue well above forecasts and raises its outlook.', [
    ['The company\'s shares', 'up', 'Results and the outlook beat what was priced in. If hopes were even higher, shares can still fall.'],
    ['Nasdaq-100 futures', 'up', 'Mega-cap tech companies carry a large weight in the index.'],
    ['Peer tech shares', 'up', 'Investors read across: strong demand at one firm may signal demand for its rivals and suppliers.']]],
  ['Earnings miss', 'A large US retailer misses profit forecasts and cuts its full-year outlook.', [
    ['The company\'s shares', 'down', 'Lower expected profits mean a lower value for the shares.'],
    ['Other retailers\' shares', 'down', 'Investors worry that weak consumer demand affects the whole sector.'],
    ['Consumer-discretionary stocks', 'down', 'The sector most exposed to spending on non-essentials is marked down too.']]],
  ['Bank failure', 'A mid-sized US bank fails after a run on its deposits.', [
    ['Bank shares', 'down', 'Investors fear contagion to other banks with similar weaknesses.'],
    ['US 2-year yield', 'down', 'There is a flight to safety, and markets bet the Fed will be slower to raise or quicker to cut.'],
    ['Gold', 'up', 'Gold carries no default risk, so it is often bought when confidence in banks is shaken.']]],
  ['Oil supply disruption', 'Attacks shut a key oil shipping route, cutting supply by several million barrels a day.', [
    ['Brent crude', 'up', 'Less supply for the same demand pushes prices up.'],
    ['Airline shares', 'down', 'Fuel is one of an airline\'s biggest costs.'],
    ['US inflation expectations', 'up', 'Higher energy prices feed into expected inflation, as seen in breakeven rates.']]]
];
// economic calendar: [release, surprise text, rows]; rows are always USD, yields, gold for US releases
const RT48_ECON = [
  ['US CPI · above forecast', 'US consumer prices rise 0.5% in the month. The forecast was 0.3%.', [['US dollar', 'up', 'Hotter inflation means rates may stay higher for longer.'], ['US 2-year yield', 'up', 'Markets price fewer or later rate cuts.'], ['Gold', 'down', 'Higher yields and a firmer dollar weigh on gold in the first reaction.']]],
  ['US CPI · below forecast', 'US consumer prices rise 0.1% in the month. The forecast was 0.3%.', [['US dollar', 'down', 'Cooler inflation brings expected rate cuts closer.'], ['US 2-year yield', 'down', 'Markets price earlier or larger cuts.'], ['Gold', 'up', 'Lower yields and a softer dollar support gold.']]],
  ['US payrolls · above forecast', 'US non-farm payrolls rise by 300,000. The forecast was 150,000.', [['US dollar', 'up', 'A strong jobs market reduces the need for rate cuts.'], ['US 2-year yield', 'up', 'Expected policy rates rise.'], ['Gold', 'down', 'Higher yields raise the cost of holding gold.']]],
  ['US payrolls · below forecast', 'US non-farm payrolls rise by 40,000. The forecast was 150,000.', [['US dollar', 'down', 'A weak jobs market makes rate cuts more likely.'], ['US 2-year yield', 'down', 'Expected policy rates fall.'], ['Gold', 'up', 'Lower yields and a softer dollar help gold.']]],
  ['US GDP · above forecast', 'US GDP grows at a 3.5% annual rate. The forecast was 2.0%.', [['US dollar', 'up', 'Stronger growth supports higher US rates and the dollar.'], ['US 10-year yield', 'up', 'Investors expect firmer growth and less need for cuts.'], ['Gold', 'down', 'The usual first reaction follows yields and the dollar. GDP moves markets less than CPI or payrolls.']]],
  ['US GDP · below forecast', 'US GDP grows at a 0.3% annual rate. The forecast was 2.0%.', [['US dollar', 'down', 'Weaker growth makes cuts more likely.'], ['US 10-year yield', 'down', 'Investors buy bonds on growth worries.'], ['Gold', 'up', 'Lower yields and safe-haven demand tend to help gold.']]],
  ['US ISM manufacturing · above forecast', 'The ISM manufacturing PMI comes in at 54. The forecast was 50. Above 50 means expansion.', [['US dollar', 'up', 'Factories are expanding faster than expected.'], ['US 10-year yield', 'up', 'Better growth reduces the case for rate cuts.'], ['Gold', 'down', 'Yields and the dollar are firmer.']]],
  ['US ISM manufacturing · below forecast', 'The ISM manufacturing PMI comes in at 46. The forecast was 50. Below 50 means contraction.', [['US dollar', 'down', 'Factory activity is shrinking.'], ['US 10-year yield', 'down', 'Growth worries pull yields lower.'], ['Gold', 'up', 'Lower yields help gold.']]],
  ['US retail sales · above forecast', 'US retail sales rise 1.2% in the month. The forecast was 0.4%.', [['US dollar', 'up', 'Strong consumer spending supports growth and rates.'], ['US 2-year yield', 'up', 'Markets trim expected rate cuts.'], ['Gold', 'down', 'Firmer yields and dollar weigh on gold.']]],
  ['US jobless claims · higher than forecast', 'Weekly initial jobless claims jump to 290,000. The forecast was 220,000.', [['US dollar', 'down', 'More people losing jobs signals a cooling labour market.'], ['US 2-year yield', 'down', 'Markets lean towards rate cuts.'], ['Gold', 'up', 'Lower yields support gold.']]],
  ['UK CPI · above forecast', 'UK inflation comes in at 3.8%. The forecast was 3.4%.', [['GBP/USD', 'up', 'Markets expect the Bank of England to keep rates higher.'], ['UK 2-year gilt yield', 'up', 'Expected Bank Rate rises.'], ['FTSE 100', 'down', 'Many FTSE 100 companies earn heavily abroad, so a stronger pound shrinks those earnings in pounds; higher rates also weigh.']]],
  ['Eurozone CPI · above forecast', 'Eurozone inflation comes in at 2.9%. The forecast was 2.4%.', [['EUR/USD', 'up', 'Markets expect the ECB to keep rates higher.'], ['German 2-year yield', 'up', 'Expected ECB rates rise.'], ['US dollar index (DXY)', 'down', 'The euro is 57.6% of the dollar index, so a stronger euro pulls DXY lower.']]]
];
const RT48_WIM = [
  ['Gold', 'A metal that pays no interest. It often struggles when real yields rise and is bought as a safe haven.'],
  ['Brent crude', 'The global oil benchmark, priced in dollars per barrel and sensitive to OPEC+ decisions.'],
  ['US dollar index (DXY)', 'Measures the dollar against six major currencies, with the euro the biggest weight.'],
  ['Bitcoin', 'A digital asset with a fixed maximum supply of 21 million coins that trades every day of the year.'],
  ['US 10-year yield', 'The return on ten-year US government debt, a key input for mortgage rates and share valuations.'],
  ['S&P 500', 'An index of about 500 large US companies, weighted by market value.'],
  ['VIX', 'Expected 30-day volatility of the S&P 500, worked out from option prices. Often called the fear gauge.'],
  ['EUR/USD', 'The most traded currency pair in the world: how many dollars one euro buys.'],
  ['Copper', 'An industrial metal used in building and electronics, watched as a gauge of global growth.'],
  ['Ether', 'The native token of the Ethereum blockchain, which runs smart contracts.'],
  ['FTSE 100', 'The 100 largest companies listed in London, many of which earn much of their money abroad.']
];
// news templates: headline pattern -> typical first reactions (indices into the combined scenario list are added at boot)
const RT48_FED = '(?=.*\\b(fed|federal reserve|fomc|powell)\\b)', RT48_US = '(?=.*\\b(us|u\\.s\\.|american|america|wall street)\\b)';
const RT48_NEWS_T = [
  [new RegExp(RT48_FED + '(?=.*\\b(cuts?|cutting|lowers?)\\b)(?=.*\\brates?\\b)', 'i'), 'Bigger rate cut'],
  [new RegExp(RT48_FED + '(?=.*\\b(raises?|hikes?|hiking|lifts?)\\b)(?=.*\\brates?\\b)', 'i'), 'Fed surprise'],
  [new RegExp(RT48_US + '(?=.*\\b(inflation|cpi|consumer prices)\\b)(?=.*\\b(hot|hotter|accelerat\\w*|jump\\w*|surg\\w*|higher than expected|tops? forecasts?)\\b)', 'i'), 'US CPI · above forecast'],
  [new RegExp(RT48_US + '(?=.*\\b(inflation|cpi|consumer prices)\\b)(?=.*\\b(cool\\w*|slow\\w*|eas(es|ed|ing)|lower than expected|soft\\w*)\\b)', 'i'), 'US CPI · below forecast'],
  [/(?=.*\b(payrolls?|jobs report)\b)(?=.*\b(beat\w*|strong\w*|surg\w*|jump\w*|tops?)\b)/i, 'US payrolls · above forecast'],
  [/(?=.*\b(payrolls?|jobs report)\b)(?=.*\b(miss\w*|weak\w*|slow\w*|disappoint\w*)\b)/i, 'US payrolls · below forecast'],
  [new RegExp(RT48_US + '(?=.*\\b(gdp|economy)\\b)(?=.*\\b(shrink\\w*|shrank|contract\\w*)\\b)', 'i'), 'Recession signal'],
  [/(?=.*\bopec\+?)(?=.*\b(cut\w*|reduc\w*)\b)(?=.*\b(output|production|supply)\b)/i, 'OPEC+ surprise cut'],
  [/(?=.*\b(strait|pipeline|tankers?|shipping route|refiner(y|ies)|oil (facilit\w*|terminals?|fields?|infrastructure|ports?)|energy (sites|facilities|infrastructure))\b)(?=.*\b(attack\w*|hits?|strikes?|struck|shut\w*|clos(e|ed|es|ure)|disrupt\w*|block\w*)\b)/i, 'Oil supply disruption'],
  [/(?=.*\b(bitcoin|crypto|ether)\b)(?=.*\betfs?\b)(?=.*\b(inflows?|record)\b)/i, 'Record crypto ETF inflows'],
  [/(?=.*\bchina\b)(?=.*\b(stimulus|easing|support package)\b)/i, 'China stimulus'],
  [/(?=.*\bbanks?\b)(?=.*\b(collaps\w*|fails|failed|failure|run on|bailout)\b)/i, 'Bank failure'],
  [/(?=.*\b(missiles?|airstrikes?|invasion|invades?|military strikes?|war|fighting|drone attacks?)\b)(?=.*\b(escalat\w*|launch\w*|attack\w*|strikes?|invad\w*|intensif\w*)\b)/i, 'Conflict escalates'],
  [/(?=.*\b(stocks|shares|wall street|s&p 500|nasdaq|dow|ftse)\b)(?=.*\b(tumbl\w*|plung\w*|sell-?off|slump\w*|sinks?|rout|crash\w*|break support)\b)/i, 'Risk-off shock'],
  [/\b(beats?|tops?|surpass\w*) (earnings|profit|revenue|estimates|forecasts|expectations)\b|\brecord (quarter|quarterly (profit|revenue))\b/i, 'Earnings beat'],
  [/\b(miss\w*) (earnings|profit|revenue|estimates|forecasts|expectations)\b|\b(cuts?|lowers?|slashe?s?) (its |annual |full-year )?(outlook|guidance)\b/i, 'Earnings miss'],
  [/(?=.*\b(us )?dollar\b)(?=.*\b(surg\w*|jump\w*|rall(y|ies|ied)|strengthen\w*|soar\w*)\b)/i, 'Strong dollar day']
];
const RT48_BADGES = [
  ['speed100', 'Quick Thinker', '⚡', 'Score 100+ in a speed round'], ['combo', 'Combo King', '🔥', 'Reach a ×3 combo'],
  ['match', 'Matchmaker', '🧩', 'Finish a matching game'], ['paper3', 'Paper Trader', '📄', 'Close 3 practice trades'],
  ['stop', 'Stop Respecter', '🛑', 'Have a stop-loss close a practice trade'], ['price', 'Price Sense', '🎯', 'Score 70%+ in Price is right'],
  ['cal', 'Calendar Pro', '📅', 'Call 5 calendar releases fully right'], ['pattern', 'Pattern Spotter', '🕯️', 'Get 5 new-style chart drills right'],
  ['scen10', 'Scenario Pro', '🌍', 'Get 10 different scenarios fully right'], ['news', 'News Reader', '📰', 'Finish an In the news set'],
  ['weekly', 'Weekly Winner', '🏆', 'Complete a weekly challenge set']
];
// weekly task pool: [key, label, target]
const RT48_WEEK_T = [
  ['speed', 'Play 3 speed rounds', 3], ['speed80', 'Score 80+ in a speed round', 1], ['trade', 'Close 2 practice trades', 2], ['drill', 'Get 6 chart drills right', 6],
  ['scen', 'Get 4 scenarios fully right', 4], ['match', 'Finish 2 matching games', 2], ['price', 'Play Price is right twice', 2], ['econ', 'Call 3 calendar releases right', 3],
  ['week', 'Finish This week in markets', 1], ['news', 'Finish an In the news set', 1], ['lesson', 'Complete a lesson', 1], ['daily', 'Do the daily challenge on 3 days', 3]
];

// ── rt48 core: activity store, XP caps, weekly challenge, badges, hub, routing ──
const _RT48_KEY = 'td_academy_act_v1';
function _rt48Blank() { return { sp: { best: 0, runs: 0 }, mt: { best: {}, runs: 0 }, pr: { best: 0, runs: 0 }, pt: null, ptr: [], ptn: 0, ptClosed: 0, cal: { ok: 0 }, gx: { ok: 0 }, sc: {}, wk: { id: '', c: {}, done: 0 }, bd: {}, cap: {}, days: {} }; }
function _rt48Load() { try { const o = JSON.parse(localStorage.getItem(_RT48_KEY) || '{}'), b = _rt48Blank(); for (const k in b) if (o[k] != null && (b[k] === null || typeof o[k] === typeof b[k])) b[k] = o[k]; return b; } catch (e) { return _rt48Blank(); } }
let _rt48S = _rt48Load();
function _rt48Save() { try { localStorage.setItem(_RT48_KEY, JSON.stringify(_rt48S)); } catch (e) {} }
function _rt48E(s) { return _rt47E(s); }
function _rt48Rand(seed) { let h = _rt46Hash(String(seed)) || 1; return () => { h = Math.imul(h ^ (h >>> 15), 2246822519) >>> 0; h = Math.imul(h ^ (h >>> 13), 3266489917) >>> 0; return ((h ^= h >>> 16) >>> 0) / 4294967296; }; }
function _rt48Shuf(a, r) { a = a.slice(); r = r || Math.random; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function _rt48UK(t) { try { return new Date(t).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London' }); } catch (e) { return ''; } }
function _rt48Fresh(t) { if (!t) return ''; const d = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/London' }).format(new Date(t)); return `${d === _rt46Day() ? 'Updated today' : 'Updated ' + _rt47Date(t)} · ${_rt48UK(t)} UK`; }
// XP with a per-day cap per activity, so repeat play can't farm levels
function _rt48XP(kind, n, el, cap) { n = Math.max(0, Math.round(n)); if (!n) return 0; const d = _rt46Day(); if (!_rt48S.cap[d]) _rt48S.cap = { [d]: {} };
  const used = _rt48S.cap[d][kind] || 0, give = cap ? Math.max(0, Math.min(n, cap - used)) : n; if (!give) return 0; _rt48S.cap[d][kind] = used + give; _rt48Save(); _rt47Award(give, el); return give; }
// weekly challenge: ISO week in London, 4 tasks picked deterministically from the pool
function _rt48Week() { const [y, m, dd] = _rt46Day().split('-').map(Number), t = new Date(Date.UTC(y, m - 1, dd)), day = (t.getUTCDay() + 6) % 7; t.setUTCDate(t.getUTCDate() - day + 3);
  const y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 4)), wk = 1 + Math.round(((t - y0) / 864e5 - 3 + ((y0.getUTCDay() + 6) % 7)) / 7); return `${t.getUTCFullYear()}-W${String(wk).padStart(2, '0')}`; }
function _rt48WeekTasks() { const id = _rt48Week(); return _rt48Shuf(RT48_WEEK_T, _rt48Rand('week:' + id)).slice(0, 4); }
function _rt48WeekSync() { const id = _rt48Week(); if (_rt48S.wk.id !== id) { _rt48S.wk = { id, c: {}, done: 0 }; _rt48Save(); } return _rt48S.wk; }
function _rt48Ev(key, n, el) { try { const w = _rt48WeekSync(); w.c[key] = (w.c[key] || 0) + (n == null ? 1 : n); _rt48Save();
  const ts = _rt48WeekTasks(); if (!w.done && ts.every(t => (w.c[t[0]] || 0) >= t[2])) { w.done = Date.now(); _rt48Save(); _rt47Award(60, el); _rt48Badge('weekly'); setTimeout(() => _rt46Toast('Weekly challenge complete: +60 XP'), 900); _rt47Confetti(); } } catch (e) {} }
function _rt48Badge(id) { if (_rt48S.bd[id]) return; const b = RT48_BADGES.find(x => x[0] === id); if (!b) return; _rt48S.bd[id] = Date.now(); _rt48Save(); setTimeout(() => _rt46Toast(`${b[2]} Badge unlocked: ${b[1]}`), 400); }
// ── merge scenario and calendar content into the shared scenario list ──
const RT48_SCEN_N0 = RT47_SCEN.length; RT48_SCEN_ADD.forEach(x => RT47_SCEN.push(x));
const RT48_SCEN_IDX = RT47_SCEN.map((x, i) => i);
const RT48_ECON_IDX = RT48_ECON.map(x => RT47_SCEN.push(x) - 1);
function _rt48ScenByName(nm) { return RT47_SCEN.findIndex(x => x[0] === nm); }
// daily challenge rotates through every scenario (not the calendar items), deterministic per London day
function _rt47DailyN() { try { return RT48_SCEN_IDX[_rt46Hash('daily:' + _rt46Day()) % RT48_SCEN_IDX.length]; } catch (e) { return _rt46Hash('daily:' + _rt46Day()) % 6; } }
// ── activities ──
const RT48_ACTS = {
  speed: { t: 'Speed round', ic: 'bolt', min: '1 min', xp: 'Up to 40 XP', d: '60 seconds, as many as you can. Streaks build a combo multiplier.' },
  paper: { t: 'Paper trading', ic: 'coin', min: '5+ min', xp: '5 XP a trade', d: 'Virtual £10,000 at live site prices. Size with a stop-loss.' },
  gym: { t: 'Chart gym', ic: 'candle', min: '6 min', xp: '10–15 XP a drill', d: 'Ten random drills: trends, levels, candle patterns, breakouts.', pl: 1 },
  scen: { t: 'Scenario room', ic: 'spark', min: '4 min', xp: '15 XP each', d: `Six of ${RT48_SCEN_IDX.length} market shocks. Call the usual first moves.`, pl: 1 },
  econ: { t: 'Economic calendar', ic: 'calendar', min: '3 min', xp: '15 XP each', d: 'CPI, payrolls, GDP beat or miss: call the dollar, yields and gold.', pl: 1 },
  match: { t: 'Match the terms', ic: 'book', min: '2 min', xp: '15 XP', d: 'Pair five terms with their meanings against the clock.' },
  asset: { t: 'Which asset?', ic: 'compass', min: '2 min', xp: '15 XP', d: 'Match descriptions to gold, oil, the dollar, Bitcoin and more.' },
  price: { t: 'Price is right', ic: 'gold', min: '2 min', xp: 'Up to 20 XP', d: 'Guess where gold, the dollar, the 10-year and Bitcoin trade now.' },
  week: { t: 'This week in markets', ic: 'bars', min: '2 min', xp: '10 XP a question', d: 'A quiz built from the past week\'s real moves.', pl: 1, auto: 1 },
  news: { t: 'In the news', ic: 'table', min: '3 min', xp: '10 XP each', d: 'Today\'s headlines turned into "what usually happens next?" cards.', pl: 1, auto: 1 }
};
let _rt48A = { id: '' };
function _rt48Open(id) { const m = RT48_ACTS[id]; if (!m) return; if (m.pl) return _rt47Open(id);
  _rt47Prog = Date.now(); try { if (typeof _rt45TipClose === 'function') _rt45TipClose(); } catch (e) {}
  try { if (typeof pg !== 'undefined' && pg !== 'learn' && !document.getElementById('learnOv')) nav('learn'); } catch (e) {}
  _rt48Stop(); _learnTab = 'start'; _learnSub = null; _rt47L = { id: '', i: 0, a: {}, xp: 0, fin: false, dir: 0 }; _rt48A = { id }; _rt48Init(id);
  _refreshView(); _rt47Top(); setTimeout(() => { const h = document.getElementById('rt48h'); if (h) h.focus({ preventScroll: true }); }, 30); }
function _rt48Close() { _rt48Stop(); _rt47Prog = Date.now(); _rt48A = { id: '' }; _refreshView(); _rt47Top(); setTimeout(() => { const b = document.querySelector('.rt48-card'); if (b) b.focus({ preventScroll: true }); }, 30); }
let _rt48Timers = [];
function _rt48Every(fn, ms) { const t = setInterval(() => { try { fn(); } catch (e) {} }, ms); _rt48Timers.push(t); return t; }
function _rt48Stop() { _rt48Timers.forEach(clearInterval); _rt48Timers = []; }
function _rt48Init(id) { try { if (id === 'speed') _rt48SpInit(); else if (id === 'paper') _rt48PtInit(); else if (id === 'match' || id === 'asset') _rt48MtInit(id); else if (id === 'price') _rt48PrInit(); } catch (e) {} }
function _rt48Body(id) { try { if (id === 'speed') return _rt48SpHtml(); if (id === 'paper') return _rt48PtHtml(); if (id === 'match' || id === 'asset') return _rt48MtHtml(); if (id === 'price') return _rt48PrHtml(); } catch (e) {} return '<p class="rt47-sb">This activity could not load. Please try again.</p>'; }
function _rt48Html() { const m = RT48_ACTS[_rt48A.id]; if (!m) return '';
  return `<section class="rt48-act${_rt46RM() ? ' rt47-rm' : ''}" id="rt48act" aria-labelledby="rt48h">
    <div class="rt47-ptop"><button type="button" class="rt47-x" onclick="_rt48Close()" aria-label="Close and go back to the Academy">✕</button><h1 class="rt48-h" id="rt48h" tabindex="-1">${_rt47Ic(m.ic)}${_rt48E(m.t)}</h1><span class="rt47-xpc" data-rt47xp>${_rt47Ic('bolt')}<span>${_rt47S.xp} XP</span></span></div>
    <div class="rt48-body" id="rt48body">${_rt48Body(_rt48A.id)}</div>
    <p class="rt47-disc">Education only, not financial advice. Practice activities use no real money.</p></section>`; }
function _rt48Draw(focusSel) { if (document.getElementById('rt48act')) _rt46Swap('rt48act', _rt48Html(), focusSel || null); }
// ── hub on the Academy home ──
function _rt48Status(id) { const S = _rt48S; try {
  if (id === 'speed') return S.sp.best ? `Best ${S.sp.best} pts` : 'New';
  if (id === 'paper') { const p = S.pt; return p ? `Equity ${_rt48GBP(_rt48PtEq())}` : 'New'; }
  if (id === 'gym') return _rt47S.chart.n ? `${_rt47S.chart.ok}/${_rt47S.chart.n} right` : 'New';
  if (id === 'scen') return `${Object.keys(S.sc).length}/${RT48_SCEN_IDX.length} mastered`;
  if (id === 'econ') return S.cal.ok ? `${S.cal.ok} called right` : 'New';
  if (id === 'match' || id === 'asset') { const b = S.mt.best[id]; return b ? `Best ${(b / 1000).toFixed(1)}s` : 'New'; }
  if (id === 'price') return S.pr.best ? `Best ${S.pr.best}%` : 'New';
  if (id === 'week') return _rt48WkReady() ? _rt48Fresh(_rt48Wk.at) : 'Building from live data…';
  if (id === 'news') return _rt48NwReady() ? _rt48Fresh(_rt48Nw.at) : 'Reading today\'s headlines…';
} catch (e) {} return ''; }
function _rt48HubHtml() { const w = _rt48WeekSync(), ts = _rt48WeekTasks(), all = ts.every(t => (w.c[t[0]] || 0) >= t[2]);
  try { _rt48AutoKick(); } catch (e) {}
  const fresh = Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0);
  return `<section class="rt48-hub" aria-labelledby="rt48hubh"><div class="rt48-hubh"><h2 class="rt47-h2" id="rt48hubh">Activities</h2>${fresh ? `<span class="rt48-fresh" data-rt48fresh>${_rt48E(_rt48Fresh(fresh))}</span>` : '<span class="rt48-fresh" data-rt48fresh></span>'}</div>
    <div class="rt48-week${all ? ' done' : ''}"><div class="rt47-ck">${_rt47Ic('flame')} WEEKLY CHALLENGE · ${_rt48E(w.id.replace('-W', ' · WEEK '))}</div>
      <p>${all ? 'Done this week. A new set starts on Monday.' : 'Finish all four this week for +60 XP and the Weekly Winner badge.'}</p>
      <ul class="rt48-wl">${ts.map(t => { const c = Math.min(t[2], w.c[t[0]] || 0); return `<li class="${c >= t[2] ? 'ok' : ''}"><span>${c >= t[2] ? '✓ ' : ''}${_rt48E(t[1])}</span><span class="rt48-wn">${c}/${t[2]}</span><span class="rt47-lvbar sm"><i style="width:${Math.round(c / t[2] * 100)}%"></i></span></li>`; }).join('')}</ul></div>
    <div class="rt48-grid">${Object.entries(RT48_ACTS).map(([id, m]) => `<button type="button" class="rt48-card${m.auto ? ' auto' : ''}" onclick="_rt48Open('${id}')" aria-label="${_rt48E(m.t)}. ${_rt48E(m.min)}. ${_rt48E(m.xp)}.">
      <span class="rt48-ci">${_rt47Ic(m.ic)}</span>${m.auto ? '<span class="rt48-auto">AUTO</span>' : ''}<span class="rt48-ct">${_rt48E(m.t)}</span><span class="rt48-cd">${_rt48E(m.d)}</span>
      <span class="rt48-cm"><span>⏱ ${_rt48E(m.min)}</span><span>⚡ ${_rt48E(m.xp)}</span></span><span class="rt48-cs" data-rt48st="${id}">${_rt48E(_rt48Status(id))}</span></button>`).join('')}</div>
    <div class="rt48-bdw"><div class="rt47-ck">${_rt47Ic('shield')} ACTIVITY BADGES</div><div class="rt47-bds">${RT48_BADGES.map(b => `<span class="rt47-bd${_rt48S.bd[b[0]] ? ' on' : ''}" title="${_rt48E(b[3])}"><span aria-hidden="true">${b[2]}</span><span>${_rt48E(b[1])}</span></span>`).join('')}</div></div></section>`; }
// live refresh of hub status lines without rebuilding the page
function _rt48HubTick() { document.querySelectorAll('[data-rt48st]').forEach(e => { const t = _rt48Status(e.dataset.rt48st); if (e.textContent !== t) e.textContent = t; });
  const f = document.querySelector('[data-rt48fresh]'); if (f) { const t = Math.max(_rt48Wk.at || 0, _rt48Nw.at || 0), s = t ? _rt48Fresh(t) : ''; if (f.textContent !== s) f.textContent = s; } }
setInterval(() => { try { if (document.getElementById('rt47home')) _rt48HubTick(); } catch (e) {} }, 3000);

// ── Speed round: 60 seconds, quiz bank + glossary, combo multiplier ──
function _rt48Mask(def, term) { let d = String(def); const parts = [term.replace(/\s*\(.*?\)\s*/g, ' ').trim(), ...(term.match(/\(([^)]+)\)/) || []).slice(1)].concat(term.split(/\s+and\s+|\//)).map(x => x.trim()).filter(x => x.length > 2);
  parts.forEach(p => { d = d.replace(new RegExp(p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), '…'); }); return d; }
function _rt48Clip(s, n) { s = String(s); if (s.length <= n) return s; const c = s.slice(0, n - 1), k = c.lastIndexOf(' '); return (k > n * 0.6 ? c.slice(0, k) : c).replace(/[\s,;:.]+$/, '') + '…'; }
function _rt48Bank() { const out = [];
  try { Object.values(RT46_QUIZ).forEach(qs => { if (Array.isArray(qs)) qs.forEach(q => { if (q && q[1] && q[1].length >= 2) out.push({ q: q[0], o: q[1].slice(), a: q[2], why: q[3] }); }); }); } catch (e) {}
  try { const G = RT45_GLOSS; G.forEach((g, i) => { const same = G.filter((x, k) => k !== i && x[2] === g[2]), pool = _rt48Shuf(same.length >= 3 ? same : G.filter((x, k) => k !== i)).slice(0, 3);
    const o = _rt48Shuf([g[1], ...pool.map(x => x[1])]); out.push({ q: `Which term matches: “${_rt48Clip(_rt48Mask(g[3], g[1]), 150)}”`, o, a: o.indexOf(g[1]), why: g[3] }); }); } catch (e) {}
  return _rt48Shuf(out); }
let _rt48Sp = null;
function _rt48SpInit() { _rt48Sp = { st: 'ready' }; }
function _rt48SpStart() { _rt48Stop(); const bank = _rt48Bank(); _rt48Sp = { st: 'run', bank, k: 0, score: 0, ok: 0, n: 0, combo: 0, maxc: 0, end: Date.now() + 60000, fb: null, lock: 0 }; _rt48Draw('#rt48spq');
  _rt48Every(_rt48SpTick, 200); }
function _rt48SpMult(c) { return c >= 6 ? 3 : c >= 3 ? 2 : 1; }
function _rt48SpTick() { const S = _rt48Sp; if (!S || S.st !== 'run') return; const left = Math.max(0, S.end - Date.now()), t = document.getElementById('rt48spt'), b = document.getElementById('rt48spb');
  if (t) t.textContent = Math.ceil(left / 1000) + 's'; if (b) b.style.width = (left / 600).toFixed(1) + '%'; if (left <= 0) _rt48SpFinish(); }
function _rt48SpAns(oi, el) { const S = _rt48Sp; if (!S || S.st !== 'run' || Date.now() < S.lock) return; const q = S.bank[S.k % S.bank.length], ok = oi === q.a; S.n++;
  if (ok) { S.combo++; S.maxc = Math.max(S.maxc, S.combo); S.ok++; const pts = 10 * _rt48SpMult(S.combo); S.score += pts; S.fb = { ok: 1, txt: `+${pts}${_rt48SpMult(S.combo) > 1 ? ' · combo ×' + _rt48SpMult(S.combo) : ''}` }; S.k++; _rt48Draw('#rt48spq'); }
  else { S.combo = 0; S.fb = { ok: 0, txt: `Answer: ${q.o[q.a]}` }; S.lock = Date.now() + 900; S.k++; _rt48Draw(); setTimeout(() => { if (_rt48Sp === S && S.st === 'run') { S.fb = null; _rt48Draw('#rt48spq'); } }, 900); } }
function _rt48SpFinish() { const S = _rt48Sp; if (!S || S.st !== 'run') return; _rt48Stop(); S.st = 'done'; const pb = S.score > (_rt48S.sp.best || 0); S.pb = pb; if (pb) _rt48S.sp.best = S.score; _rt48S.sp.runs++; _rt48Save();
  _rt48Draw('#rt48spr'); setTimeout(() => { const el = document.getElementById('rt48spr'); S.xp = _rt48XP('speed', Math.min(40, S.ok * 3), el, 80); if (S.score >= 100) _rt48Badge('speed100'); if (S.maxc >= 6) _rt48Badge('combo'); _rt48Ev('speed'); if (S.score >= 80) _rt48Ev('speed80'); if (pb && !_rt46RM()) _rt47Confetti(); _rt48Draw('#rt48spr'); }, 30); }
function _rt48SpHtml() { const S = _rt48Sp || { st: 'ready' };
  if (S.st === 'ready') return `<div class="rt48-intro"><p class="rt47-sb">Answer as many questions as you can in 60 seconds. Three right in a row doubles your points; six in a row triples them. A wrong answer resets the combo.</p>
    <ul class="rt48-facts"><li>Questions from the 10 lessons and the ${RT45_GLOSS.length}-term glossary</li><li>Keys 1–4 answer on a keyboard</li><li>Your best: <b>${_rt48S.sp.best || 0}</b> points</li></ul><button type="button" class="rt47-cta" id="rt48spgo" onclick="_rt48SpStart()">${_rt47Ic('play')}Start the clock</button></div>`;
  if (S.st === 'run') { const q = S.bank[S.k % S.bank.length], left = Math.max(0, S.end - Date.now()), m = _rt48SpMult(S.combo);
    return `<div class="rt48-sphud"><span class="rt48-spt" id="rt48spt" aria-label="Time left">${Math.ceil(left / 1000)}s</span><span class="rt47-bar"><i id="rt48spb" style="width:${(left / 600).toFixed(1)}%"></i></span><span class="rt48-sps">${S.score} pts</span><span class="rt48-combo${m > 1 ? ' on' : ''}">×${m}</span></div>
      <div class="rt47-stage rt48-spq"><div class="rt47-sk">QUESTION ${S.n + 1}</div><h2 class="rt48-q" id="rt48spq" tabindex="-1">${_rt48E(q.q)}</h2><div class="rt47-opts">${q.o.map((o, k) => `<button type="button" class="rt47-opt" id="rt48sp${k}" onclick="_rt48SpAns(${k},this)"><span class="rt48-key" aria-hidden="true">${k + 1}</span>${_rt48E(o)}</button>`).join('')}</div>
      <div class="rt48-spfb ${S.fb ? (S.fb.ok ? 'ok' : 'no') : ''}" role="status" aria-live="polite">${S.fb ? _rt48E(S.fb.txt) : ''}</div></div>`; }
  return `<div class="rt48-res" id="rt48spr" tabindex="-1"><div class="rt47-medal" aria-hidden="true">${_rt47Ic('bolt')}</div><h2 class="rt47-sh">${S.pb ? 'New personal best!' : 'Time!'}</h2>
    <div class="rt47-endstats"><div><b>${S.score}</b><span>points</span></div><div><b>${S.ok}/${S.n}</b><span>right</span></div><div><b>×${_rt48SpMult(S.maxc)}</b><span>best combo (${S.maxc} in a row)</span></div></div>
    <p class="rt47-sb sm">Best ever: ${_rt48S.sp.best} points.${S.xp != null ? ` XP earned: +${S.xp}${S.xp === 0 ? ' (daily cap for speed rounds reached)' : ''}.` : ''}</p><div class="rt47-endbtns"><button type="button" class="rt47-cta" onclick="_rt48SpStart()">Play again</button><button type="button" class="rt47-btn" onclick="_rt48Close()">Back to activities</button></div></div>`; }
document.addEventListener('keydown', e => { try { if (!_rt48Sp || _rt48Sp.st !== 'run' || _rt48A.id !== 'speed' || e.ctrlKey || e.metaKey || e.altKey) return; if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return; const k = Number(e.key);
  if (k >= 1 && k <= 4) { const b = document.getElementById('rt48sp' + (k - 1)); if (b) { e.preventDefault(); _rt48SpAns(k - 1, b); } } } catch (x) {} });

// ── Paper trading: virtual £10,000 at the site's live prices; practice only ──
const RT48_PT_ASSETS = [['XAU', 'Gold', 'XAU/USD'], ['BTC', 'Bitcoin', 'BTC/USD'], ['ETH', 'Ether', 'ETH/USD'], ['SPX', 'S&P 500', 'index'], ['EURUSD', 'EUR/USD', 'FX']];
const RT48_PT_START = 10000;
function _rt48GBP(v) { if (!isFinite(v)) return '—'; const s = v < 0 ? '−' : ''; return s + '£' + Math.abs(v).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function _rt48Num(s) { if (typeof s === 'number') return s; const n = Number(String(s || '').replace(/[^0-9.\-]/g, '')); return isFinite(n) && n > 0 ? n : NaN; }
function _rt48Px(tk) { try { const d = fp(tk); if (!d || d.status === 'unavailable') return null; let p = _rt48Num(d.p); if (!isFinite(p)) { const k = (typeof resolveInternalTicker === 'function' && resolveInternalTicker(tk)) || tk; p = P[k] && P[k].p; }
  if (!isFinite(p) || p <= 0) return null; return { p, st: String(d.status || ''), label: d.label || d.status || '' }; } catch (e) { return null; } }
// New York clock, so the weekly/daily sessions follow US daylight saving automatically
function _rt48NY() { try { const f = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()), g = k => (f.find(x => x.type === k) || {}).value;
  return { d: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(g('weekday')), m: Number(g('hour')) * 60 + Number(g('minute')) }; } catch (e) { return null; } }
function _rt48Mkt(tk) { const t = _rt48NY(); if (!t) return { open: true, why: '' }; const { d, m } = t;
  if (tk === 'BTC' || tk === 'ETH') return { open: true, why: 'Crypto trades 24/7' };
  if (tk === 'SPX') { const o = d >= 1 && d <= 5 && m >= 570 && m < 960; return { open: o, why: o ? 'US stock market open (9:30–16:00 New York)' : 'US stocks trade 9:30–16:00 New York time, Monday to Friday' }; }
  if (tk === 'EURUSD') { const o = (d >= 1 && d <= 4) || (d === 0 && m >= 1020) || (d === 5 && m < 1020); return { open: o, why: o ? 'FX market open' : 'FX closes Friday 17:00 and reopens Sunday 17:00 New York time' }; }
  if (tk === 'XAU') { const brk = m >= 1020 && m < 1080, o = ((d >= 1 && d <= 4) && !brk) || (d === 0 && m >= 1080) || (d === 5 && m < 1020); return { open: o, why: o ? 'Gold market open' : brk && d >= 1 && d <= 4 ? 'Gold takes a daily break 17:00–18:00 New York time' : 'Gold closes Friday 17:00 and reopens Sunday 18:00 New York time' }; }
  return { open: false, why: '' }; }
function _rt48Open2(tk) { const s = _rt48Mkt(tk), q = _rt48Px(tk); if (!q) return { ok: false, q, why: 'No price from the site feed right now' };
  if (!s.open || /closed|rth-close/.test(q.st)) return { ok: false, q, why: s.open ? 'The site shows this market as closed' : s.why }; return { ok: true, q, why: s.why }; }
function _rt48Rate() { const q = _rt48Px('GBPUSD'); if (q && q.p > 0.5 && q.p < 3) return q.p; return (_rt48S.pt && _rt48S.pt.rate) || NaN; }
function _rt48PtNew() { const r = _rt48Rate(); _rt48S.pt = { start: Date.now(), bal: RT48_PT_START, pos: [], hist: [], rate: isFinite(r) ? r : null, n: (_rt48S.ptn = (_rt48S.ptn || 0) + 1) }; _rt48Save(); }
function _rt48PtPnl(p, px) { const r = _rt48Rate(); if (!isFinite(px) || !isFinite(r)) return 0; return (px - p.entry) * p.qty * (p.side === 'long' ? 1 : -1) / r; }
function _rt48PtEq() { const t = _rt48S.pt; if (!t) return RT48_PT_START; return t.bal + t.pos.reduce((s, p) => { const q = _rt48Px(p.tk); return s + (q ? _rt48PtPnl(p, q.p) : (p.last || 0)); }, 0); }
let _rt48Pt = { tk: 'BTC', side: 'long', risk: 1, stop: 2, msg: '' };
function _rt48PtInit() { if (!_rt48S.pt) _rt48PtNew(); const firstOpen = RT48_PT_ASSETS.find(a => _rt48Open2(a[0]).ok); if (firstOpen && !_rt48Open2(_rt48Pt.tk).ok) _rt48Pt.tk = firstOpen[0]; _rt48Pt.msg = '';
  setTimeout(() => _rt48Every(_rt48PtTick, 2000), 0); }
function _rt48PtSize() { const t = _rt48S.pt, eq = _rt48PtEq(), used = t.pos.reduce((s, p) => s + p.notional, 0), free = Math.max(0, eq - used), want = eq * _rt48Pt.risk / 100 / (_rt48Pt.stop / 100);
  const notional = Math.min(want, free); return { eq, free, want, notional, risk: notional * _rt48Pt.stop / 100, capped: want > free + 0.005 }; }
function _rt48PtSet(k, v) { _rt48Pt[k] = v; _rt48Pt.msg = ''; _rt48Draw(`[data-pt="${k}:${v}"]`); }
function _rt48PtBuy() { const t = _rt48S.pt, o = _rt48Open2(_rt48Pt.tk), r = _rt48Rate();
  if (!o.ok) { _rt48Pt.msg = 'Market closed: ' + o.why + '.'; return _rt48Draw('#rt48ptgo'); }
  if (t.pos.length >= 3) { _rt48Pt.msg = 'You can hold up to 3 practice positions. Close one first.'; return _rt48Draw('#rt48ptgo'); }
  if (!isFinite(r)) { _rt48Pt.msg = 'The GBP/USD rate is not available yet, so sizes in pounds cannot be worked out. Try again in a moment.'; return _rt48Draw('#rt48ptgo'); }
  const z = _rt48PtSize(); if (z.notional < 50) { _rt48Pt.msg = 'Not enough free virtual capital for that size.'; return _rt48Draw('#rt48ptgo'); }
  const px = o.q.p, st = _rt48Pt.stop / 100, side = _rt48Pt.side, stopPx = side === 'long' ? px * (1 - st) : px * (1 + st);
  t.pos.push({ id: Date.now().toString(36), tk: _rt48Pt.tk, side, entry: px, qty: z.notional * r / px, notional: z.notional, stop: stopPx, risk: z.risk, at: Date.now() }); _rt48Save();
  _rt48Pt.msg = `Opened a practice ${side} in ${RT48_PT_ASSETS.find(a => a[0] === _rt48Pt.tk)[1]} at ${_rt47Num(px)}.`; _rt48Draw('#rt48ptgo'); }
function _rt48PtClose(id, why, el) { const t = _rt48S.pt, k = t.pos.findIndex(p => p.id === id); if (k < 0) return; const p = t.pos[k], o = _rt48Open2(p.tk);
  if (!o.ok && why !== 'stop') { _rt48Pt.msg = `Can't close: ${o.why}. Real markets don't fill orders while closed.`; return _rt48Draw(); }
  const px = o.q.p, pnl = _rt48PtPnl(p, px); t.bal += pnl; t.pos.splice(k, 1); t.hist.unshift({ tk: p.tk, side: p.side, entry: p.entry, exit: px, pnl, why, at: Date.now(), stop: p.stop }); t.hist = t.hist.slice(0, 30); _rt48Save();
  const nm = RT48_PT_ASSETS.find(a => a[0] === p.tk)[1];
  _rt48Pt.msg = why === 'stop' ? `Stop-loss closed your ${nm} ${p.side} at ${_rt47Num(px)} (stop ${_rt47Num(p.stop)}): ${_rt48GBP(pnl)}.` : `Closed ${nm} ${p.side} at ${_rt47Num(px)}: ${_rt48GBP(pnl)}.`;
  _rt48XP('trade', 5, el || document.getElementById('rt48pteq'), 25); _rt48Ev('trade'); if (why === 'stop') _rt48Badge('stop');
  _rt48S.ptClosed = (_rt48S.ptClosed || 0) + 1; if (t.hist.length >= 3 || _rt48S.ptClosed >= 3) _rt48Badge('paper3'); _rt48Save(); _rt48Draw(); }
function _rt48PtTick() { const t = _rt48S.pt; if (!t || _rt48A.id !== 'paper') return; let hit = false;
  t.pos.slice().forEach(p => { const o = _rt48Open2(p.tk); if (!o.ok) return; const px = o.q.p; p.last = _rt48PtPnl(p, px); if (p.side === 'long' ? px <= p.stop : px >= p.stop) { hit = true; _rt48PtClose(p.id, 'stop'); } });
  if (hit) return; // live cells only: never rebuild the whole panel on a tick
  const set = (id, v) => { const e = document.getElementById(id); if (e && e.textContent !== v) e.textContent = v; };
  set('rt48pteq', _rt48GBP(_rt48PtEq())); t.pos.forEach(p => { const q = _rt48Px(p.tk); if (q) { set('rt48pp' + p.id, _rt47Num(q.p)); const v = _rt48PtPnl(p, q.p), e = document.getElementById('rt48pl' + p.id); if (e) { const s = _rt48GBP(v); if (e.textContent !== s) e.textContent = s; e.className = 'rt48-pnl ' + (v > 0 ? 'up' : v < 0 ? 'dn' : ''); } } });
  RT48_PT_ASSETS.forEach(a => { const q = _rt48Px(a[0]); set('rt48pa' + a[0], q ? _rt47Num(q.p) : '—'); }); }
function _rt48PtFinish() { const t = _rt48S.pt; if (!t) return; if (t.pos.length) { _rt48Pt.msg = 'Close your open positions before finishing the run.'; return _rt48Draw(); }
  const eq = t.bal, ret = (eq / RT48_PT_START - 1) * 100, n = t.hist.length;
  if (n) { _rt48S.ptr.push({ n: t.n, start: t.start, end: Date.now(), eq, ret, trades: n, wins: t.hist.filter(h => h.pnl > 0).length, stops: t.hist.filter(h => h.why === 'stop').length }); _rt48S.ptr.sort((a, b) => b.ret - a.ret); _rt48S.ptr = _rt48S.ptr.slice(0, 10); }
  if (n >= 3) _rt48XP('ptfin', 10, document.getElementById('rt48ptfin'), 10);
  _rt48PtNew(); _rt48Pt.msg = n ? `Run saved: ${ret >= 0 ? '+' : ''}${ret.toFixed(2)}% over ${n} trade${n === 1 ? '' : 's'}. A fresh £10,000 is ready.` : 'Fresh £10,000 ready.'; _rt48Draw('#rt48ptgo'); }
function _rt48PtHtml() { const t = _rt48S.pt || (_rt48PtNew(), _rt48S.pt), eq = _rt48PtEq(), z = _rt48PtSize(), o = _rt48Open2(_rt48Pt.tk), nm = RT48_PT_ASSETS.find(a => a[0] === _rt48Pt.tk), r = _rt48Rate();
  const ch = (k, opts) => `<div class="rt48-seg" role="group" aria-label="${k === 'risk' ? 'Risk per trade' : k === 'stop' ? 'Stop-loss distance' : 'Direction'}">${opts.map(([v, l]) => `<button type="button" data-pt="${k}:${v}" class="${_rt48Pt[k] === v ? 'on' : ''}" aria-pressed="${_rt48Pt[k] === v}" onclick="_rt48PtSet('${k}',${typeof v === 'string' ? `'${v}'` : v})">${l}</button>`).join('')}</div>`;
  const px = o.q ? o.q.p : NaN, stopPx = isFinite(px) ? (_rt48Pt.side === 'long' ? px * (1 - _rt48Pt.stop / 100) : px * (1 + _rt48Pt.stop / 100)) : NaN;
  return `<div class="rt48-banner" role="note"><b>Practice only</b> · virtual £10,000 · no real money, no real orders. Prices come from the site's feeds and may be delayed; real trading adds spreads, fees and slippage.</div>
  <div class="rt48-pthead"><div><span class="rt47-stk">Equity</span><b id="rt48pteq">${_rt48GBP(eq)}</b></div><div><span class="rt47-stk">Return</span><b class="${eq >= RT48_PT_START ? 'up' : 'dn'}">${((eq / RT48_PT_START - 1) * 100).toFixed(2)}%</b></div><div><span class="rt47-stk">Run</span><b>#${t.n || 1}</b></div></div>
  <div class="rt48-ptgrid"><div class="rt48-ptform"><h2 class="rt47-h2">New practice trade</h2>
    <div class="rt48-assets" role="radiogroup" aria-label="Market">${RT48_PT_ASSETS.map(a => { const oo = _rt48Open2(a[0]); return `<button type="button" role="radio" data-pt="tk:${a[0]}" aria-checked="${_rt48Pt.tk === a[0]}" class="${_rt48Pt.tk === a[0] ? 'on' : ''}${oo.ok ? '' : ' shut'}" onclick="_rt48PtSet('tk','${a[0]}')"><span>${_rt48E(a[1])}</span><span class="rt48-apx" id="rt48pa${a[0]}">${oo.q ? _rt47Num(oo.q.p) : '—'}</span><span class="rt48-ast ${oo.ok ? 'on' : ''}">${oo.ok ? 'OPEN' : 'CLOSED'}</span></button>`; }).join('')}</div>
    <p class="rt48-sess ${o.ok ? 'ok' : 'no'}">${o.ok ? '● ' : '○ '}${_rt48E(nm[1])}: ${_rt48E(o.ok ? (o.why || 'open') + (o.q && o.q.label ? ' · ' + o.q.label : '') : 'closed. ' + o.why + '.')}</p>
    <label class="rt48-lab">Direction</label>${ch('side', [['long', '▲ Buy (long)'], ['short', '▼ Sell (short)']])}
    <label class="rt48-lab">Risk per trade <span>how much of your equity you accept losing if the stop is hit</span></label>${ch('risk', [[0.5, '0.5%'], [1, '1%'], [2, '2%']])}
    <label class="rt48-lab">Stop-loss distance <span>from the entry price</span></label>${ch('stop', [[1, '1%'], [2, '2%'], [3, '3%'], [5, '5%']])}
    <div class="rt48-calc"><div><span>Position size</span><b>${_rt48GBP(z.notional)}</b></div><div><span>Max loss at stop</span><b>${_rt48GBP(z.risk)}</b></div><div><span>Stop price</span><b>${isFinite(stopPx) ? _rt47Num(stopPx) : '—'}</b></div></div>
    <p class="rt47-fine">Size = risk ÷ stop distance: ${_rt48GBP(eq * _rt48Pt.risk / 100)} ÷ ${_rt48Pt.stop}% = ${_rt48GBP(z.want)}${z.capped ? `, capped at your free capital of ${_rt48GBP(z.free)} (no leverage here)` : ''}.${isFinite(r) ? ` Converted at GBP/USD ${r.toFixed(4)}.` : ''}</p>
    <button type="button" class="rt47-cta" id="rt48ptgo" onclick="_rt48PtBuy()" ${o.ok && t.pos.length < 3 ? '' : 'aria-disabled="true"'}>${o.ok ? `${_rt48Pt.side === 'long' ? 'Buy' : 'Sell'} ${_rt48E(nm[1])} (practice)` : 'Market closed'}</button>
    <div class="rt48-msg" role="status" aria-live="polite">${_rt48E(_rt48Pt.msg)}</div></div>
  <div class="rt48-ptside"><h2 class="rt47-h2">Open positions <span class="rt48-cnt">${t.pos.length}/3</span></h2>${t.pos.length ? `<ul class="rt48-pos">${t.pos.map(p => { const q = _rt48Px(p.tk), v = q ? _rt48PtPnl(p, q.p) : 0, oo = _rt48Open2(p.tk), an = RT48_PT_ASSETS.find(a => a[0] === p.tk)[1];
      return `<li><div class="rt48-pr"><b>${_rt48E(an)} · ${p.side === 'long' ? '▲ long' : '▼ short'}</b><span id="rt48pl${p.id}" class="rt48-pnl ${v > 0 ? 'up' : v < 0 ? 'dn' : ''}">${_rt48GBP(v)}</span></div><div class="rt48-pm">Entry ${_rt47Num(p.entry)} · now <span id="rt48pp${p.id}">${q ? _rt47Num(q.p) : '—'}</span> · stop ${_rt47Num(p.stop)} · size ${_rt48GBP(p.notional)}</div>${oo.ok ? '' : `<div class="rt48-pm">Market closed: the stop is checked again when it reopens. Prices can gap past a stop.</div>`}<button type="button" class="rt47-btn sm" onclick="_rt48PtClose('${p.id}','manual',this)" ${oo.ok ? '' : 'aria-disabled="true"'}>Close</button></li>`; }).join('')}</ul>` : '<p class="rt47-sb sm">No open positions. Pick an open market and place a practice trade.</p>'}
    <h2 class="rt47-h2">This run</h2>${t.hist.length ? `<ul class="rt48-hist">${t.hist.slice(0, 6).map(h => `<li><span>${_rt48E(RT48_PT_ASSETS.find(a => a[0] === h.tk)[1])} ${h.side === 'long' ? '▲' : '▼'} ${_rt47Num(h.entry)} → ${_rt47Num(h.exit)}${h.why === 'stop' ? ' · stop' : ''}</span><b class="${h.pnl > 0 ? 'up' : h.pnl < 0 ? 'dn' : ''}">${_rt48GBP(h.pnl)}</b></li>`).join('')}</ul>` : '<p class="rt47-sb sm">No closed trades yet.</p>'}
    <button type="button" class="rt47-btn" id="rt48ptfin" onclick="_rt48PtFinish()">Finish run and start fresh</button>
    <h2 class="rt47-h2">Your best runs</h2>${_rt48S.ptr.length ? `<ol class="rt48-lb">${_rt48S.ptr.slice(0, 5).map(x => `<li><span>Run #${x.n} · ${_rt47Date(x.end)} · ${x.trades} trade${x.trades === 1 ? '' : 's'}${x.stops ? ` · ${x.stops} stopped` : ''}</span><b class="${x.ret >= 0 ? 'up' : 'dn'}">${x.ret >= 0 ? '+' : ''}${x.ret.toFixed(2)}%</b></li>`).join('')}</ol>` : '<p class="rt47-sb sm">Finish a run to see it here. Only your own runs on this device are shown.</p>'}</div></div>
  <details class="rt48-why"><summary>Why size from the stop?</summary><p>Professional traders usually decide how much they are willing to lose first, then set the position size so that hitting the stop costs about that amount. A wider stop means a smaller position. A stop is filled at the next available price, so in fast or gapping markets the loss can be bigger than planned; that is slippage.</p></details>`; }

// ── Matching games: terms ↔ meanings, descriptions ↔ assets. Tap-tap, drag on desktop, full keyboard ──
let _rt48Mt = null;
function _rt48MtInit(mode) { const r = Math.random; let pairs;
  if (mode === 'asset') pairs = _rt48Shuf(RT48_WIM, r).slice(0, 5).map(x => ({ l: x[0], r: x[1] }));
  else { const cats = {}; const pick = []; _rt48Shuf(RT45_GLOSS, r).forEach(g => { if (pick.length < 5 && !pick.some(p => p[1] === g[1])) pick.push(g); }); pairs = pick.map(g => ({ l: g[1], r: _rt48Clip(_rt48Mask(g[3], g[1]), 120), full: g[3] })); }
  pairs.forEach((p, k) => p.k = k);
  _rt48Mt = { mode, pairs, L: _rt48Shuf(pairs.map(p => p.k), r), R: _rt48Shuf(pairs.map(p => p.k), r), sel: null, done: {}, wrong: 0, t0: 0, end: 0, flash: null }; }
function _rt48MtMs() { const M = _rt48Mt; if (!M || !M.t0) return 0; return (M.end || Date.now()) - M.t0 + M.wrong * 5000; }
function _rt48MtTap(side, k) { const M = _rt48Mt; if (!M || M.end || M.done[k] != null && side === 'L' || (side === 'R' && Object.values(M.done).includes(k))) return; if (!M.t0) { M.t0 = Date.now(); _rt48Every(_rt48MtTick, 250); }
  if (side === 'L') { M.sel = M.sel === k ? null : k; return _rt48Draw(`#rt48mL${k}`); }
  if (M.sel == null) { M.flash = { t: 'Pick a term on the left first.' }; return _rt48Draw(`#rt48mR${k}`); }
  _rt48MtTry(M.sel, k, `#rt48mR${k}`); }
function _rt48MtTry(lk, rk, foc) { const M = _rt48Mt;
  if (lk === rk) { M.done[lk] = rk; M.sel = null; M.flash = { ok: 1, t: 'Match!' }; if (Object.keys(M.done).length === M.pairs.length) return _rt48MtWin(); const nx = M.L.find(x => M.done[x] == null); return _rt48Draw(nx != null ? `#rt48mL${nx}` : null); }
  M.wrong++; M.flash = { t: '+5s: not a match. Try another.', no: rk }; M.sel = lk; _rt48Draw(foc); }
function _rt48MtTick() { const e = document.getElementById('rt48mtt'); if (e) e.textContent = (_rt48MtMs() / 1000).toFixed(1) + 's'; }
function _rt48MtWin() { const M = _rt48Mt; M.end = Date.now(); _rt48Stop(); const ms = _rt48MtMs(), b = _rt48S.mt.best[M.mode]; M.pb = !b || ms < b; if (M.pb) _rt48S.mt.best[M.mode] = ms; _rt48S.mt.runs++; _rt48Save();
  _rt48Draw('#rt48mres'); setTimeout(() => { M.xp = _rt48XP('match', 15, document.getElementById('rt48mres'), 45); _rt48Badge('match'); _rt48Ev('match'); if (M.pb && !_rt46RM()) _rt47Confetti(); _rt48Draw('#rt48mres'); }, 30); }
// native drag and drop (desktop); tap and keyboard always work
function _rt48MtDrag(ev, k) { try { ev.dataTransfer.setData('text/plain', String(k)); ev.dataTransfer.effectAllowed = 'move'; } catch (e) {} }
function _rt48MtDrop(ev, rk) { try { ev.preventDefault(); const lk = Number(ev.dataTransfer.getData('text/plain')); const M = _rt48Mt; if (!M || M.end || !isFinite(lk) || M.done[lk] != null) return; if (!M.t0) { M.t0 = Date.now(); _rt48Every(_rt48MtTick, 250); } _rt48MtTry(lk, rk, `#rt48mR${rk}`); } catch (e) {} }
function _rt48MtHtml() { const M = _rt48Mt; if (!M) return ''; const asset = M.mode === 'asset', matchedR = Object.values(M.done);
  if (M.end) { const ms = _rt48MtMs();
    return `<div class="rt48-res" id="rt48mres" tabindex="-1"><div class="rt47-medal" aria-hidden="true">${_rt47Ic('check')}</div><h2 class="rt47-sh">${M.pb ? 'New best time!' : 'All matched!'}</h2>
      <div class="rt47-endstats"><div><b>${(ms / 1000).toFixed(1)}s</b><span>time incl. penalties</span></div><div><b>${M.wrong}</b><span>wrong tries (+5s each)</span></div><div><b>${(_rt48S.mt.best[M.mode] / 1000).toFixed(1)}s</b><span>your best</span></div></div>
      <ul class="rt48-recap">${M.pairs.map(p => `<li><b>${_rt48E(p.l)}</b> ${_rt48E(p.full || p.r)}</li>`).join('')}</ul>
      ${M.xp != null ? `<p class="rt47-sb sm">XP earned: +${M.xp}${M.xp === 0 ? ' (daily cap for matching reached)' : ''}.</p>` : ''}<div class="rt47-endbtns"><button type="button" class="rt47-cta" onclick="_rt48MtInit('${M.mode}');_rt48Draw('#rt48mL0')">New set</button><button type="button" class="rt47-btn" onclick="_rt48Close()">Back to activities</button></div></div>`; }
  return `<p class="rt47-sb sm">${asset ? 'Match each market to its description.' : 'Match each term to its meaning.'} Tap one on the left, then its partner on the right${IS_DESKTOP() ? ', or drag it across' : ''}. Keyboard: Tab to a card and press Enter. A wrong pair adds 5 seconds.</p>
    <div class="rt48-mhud"><span>${_rt47Ic('bolt')}<b id="rt48mtt">${(_rt48MtMs() / 1000).toFixed(1)}s</b></span><span>${Object.keys(M.done).length}/${M.pairs.length} matched</span>${_rt48S.mt.best[M.mode] ? `<span>Best ${(_rt48S.mt.best[M.mode] / 1000).toFixed(1)}s</span>` : ''}</div>
    <div class="rt48-match${asset ? ' asset' : ''}"><div class="rt48-mcol" role="group" aria-label="${asset ? 'Markets' : 'Terms'}">${M.L.map(k => { const d = M.done[k] != null; return `<button type="button" id="rt48mL${k}" class="rt48-mc l${d ? ' ok' : ''}${M.sel === k ? ' sel' : ''}" ${d ? 'aria-disabled="true"' : `draggable="true" ondragstart="_rt48MtDrag(event,${k})"`} aria-pressed="${M.sel === k}" onclick="_rt48MtTap('L',${k})">${d ? '✓ ' : ''}${_rt48E(M.pairs[k].l)}</button>`; }).join('')}</div>
    <div class="rt48-mcol" role="group" aria-label="${asset ? 'Descriptions' : 'Meanings'}">${M.R.map(k => { const d = matchedR.includes(k); return `<button type="button" id="rt48mR${k}" class="rt48-mc r${d ? ' ok' : ''}${M.flash && M.flash.no === k ? ' no' : ''}" ${d ? 'aria-disabled="true"' : 'ondragover="event.preventDefault()"'} ondrop="_rt48MtDrop(event,${k})" onclick="_rt48MtTap('R',${k})">${d ? `<b>${_rt48E(M.pairs[k].l)}</b> ` : ''}${_rt48E(M.pairs[k].r)}</button>`; }).join('')}</div></div>
    <div class="rt48-msg ${M.flash && M.flash.ok ? 'ok' : ''}" role="status" aria-live="polite">${M.flash ? _rt48E(M.flash.t) : M.sel != null ? `Selected: ${_rt48E(M.pairs[M.sel].l)}. Now pick its partner.` : ''}</div>`; }

// ── Price is right: guess where key markets trade now, scored by closeness ──
const RT48_PR = { XAU: ['Gold', 'US dollars per troy ounce', 0.03], DXY: ['US Dollar Index (DXY)', 'index points', 0.02], TNX: ['US 10-year Treasury yield', 'percent', 0.08], BTC: ['Bitcoin', 'US dollars', 0.08],
  SPX: ['S&P 500', 'index points', 0.03], BRENT: ['Brent crude oil', 'US dollars per barrel', 0.05], EURUSD: ['EUR/USD', 'US dollars per euro', 0.015], ETH: ['Ether', 'US dollars', 0.10], WTI: ['WTI crude oil', 'US dollars per barrel', 0.05] };
const RT48_PR_BONUS = ['SPX', 'BRENT', 'EURUSD', 'ETH', 'WTI'];
let _rt48Pr = null;
function _rt48PrInit() { const bonus = RT48_PR_BONUS[_rt46Hash('prb:' + _rt46Day()) % RT48_PR_BONUS.length]; _rt48Pr = { tks: ['XAU', 'DXY', 'TNX', 'BTC', bonus], g: {}, res: null, bonus }; }
function _rt48PrIn(tk, v) { if (_rt48Pr && !_rt48Pr.res) _rt48Pr.g[tk] = v; }
function _rt48PrGo() { const R = _rt48Pr; if (!R || R.res) return; const rows = [];
  R.tks.forEach(tk => { const q = _rt48Px(tk), g = _rt48Num(String(R.g[tk] || '').replace(/,/g, '')), tol = RT48_PR[tk][2]; if (!q) { rows.push({ tk, na: 1 }); return; }
    const err = isFinite(g) ? Math.abs(g / q.p - 1) : 1, sc = isFinite(g) ? Math.round(100 * Math.max(0, 1 - err / tol)) : 0; rows.push({ tk, g, p: q.p, err, sc, label: q.label, st: q.st }); });
  const ok = rows.filter(r => !r.na); if (!ok.length) { R.msg = 'Prices are still loading from the site feed. Try again in a moment.'; return _rt48Draw('#rt48prgo'); }
  const tot = Math.round(ok.reduce((s, r) => s + r.sc, 0) / ok.length); R.res = { rows, tot }; R.pb = tot > (_rt48S.pr.best || 0); if (R.pb) _rt48S.pr.best = tot; _rt48S.pr.runs++; _rt48Save();
  _rt48Draw('#rt48prr'); setTimeout(() => { R.xp = _rt48XP('price', Math.round(tot / 5), document.getElementById('rt48prr'), 40); if (tot >= 70) _rt48Badge('price'); _rt48Ev('price'); _rt48Draw('#rt48prr'); }, 30); }
function _rt48PrFmt(tk, v) { return tk === 'TNX' ? v.toFixed(2) + '%' : tk === 'EURUSD' ? v.toFixed(4) : _rt47Num(v); }
function _rt48PrHtml() { const R = _rt48Pr || (_rt48PrInit(), _rt48Pr);
  if (R.res) { const r = R.res;
    return `<div class="rt48-res" id="rt48prr" tabindex="-1"><h2 class="rt47-sh">${R.pb ? 'New best score!' : 'Your score'}: ${r.tot}%</h2>
      <ul class="rt48-prl">${r.rows.map(x => { const m = RT48_PR[x.tk]; if (x.na) return `<li><b>${_rt48E(m[0])}</b><span>No price from the site feed right now, so this one is not scored.</span></li>`;
        const closed = /closed|rth-close|proxy/.test(x.st);
        return `<li><div class="rt48-prh"><b>${_rt48E(m[0])}</b><span class="rt48-psc ${x.sc >= 70 ? 'ok' : x.sc ? 'mid' : 'no'}">${x.sc}%</span></div><div class="rt48-pm">You: ${isFinite(x.g) ? _rt48PrFmt(x.tk, x.g) : 'no guess'} · actual: <b>${_rt48PrFmt(x.tk, x.p)}</b> (${_rt48E(x.label || '')}${closed ? '; last available price' : ''}) · off by ${isFinite(x.g) ? (x.err * 100).toFixed(1) + '%' : '—'} (the score reaches zero at ${(m[2] * 100).toFixed(1)}% off)</div>
          <span class="rt47-lvbar sm"><i style="width:${x.sc}%"></i></span></li>`; }).join('')}</ul>
      <p class="rt47-fine">Scoring allows more room for more volatile markets. Prices from the site's free feeds; some may be delayed or last close.</p>
      ${R.xp != null ? `<p class="rt47-sb sm">XP earned: +${R.xp}${R.xp === 0 ? ' (daily cap reached)' : ''}. Best ever: ${_rt48S.pr.best}%.</p>` : ''}
      <div class="rt47-endbtns"><button type="button" class="rt47-cta" onclick="_rt48PrInit();_rt48Draw('#rt48pr0')">Play again</button><button type="button" class="rt47-btn" onclick="_rt48Close()">Back to activities</button></div></div>`; }
  return `<p class="rt47-sb sm">Where does each market trade right now? Type your best guess. Knowing roughly where the big markets sit is the first step to spotting when something unusual is happening. Today's bonus: <b>${_rt48E(RT48_PR[R.bonus][0])}</b>.</p>
    <form class="rt48-prf" onsubmit="event.preventDefault();_rt48PrGo()">${R.tks.map((tk, k) => { const m = RT48_PR[tk]; return `<div class="rt48-prrow"><label for="rt48pr${k}"><b>${_rt48E(m[0])}</b><span>${_rt48E(m[1])}</span></label><input id="rt48pr${k}" type="text" inputmode="decimal" autocomplete="off" placeholder="${tk === 'TNX' ? 'yield in %' : tk === 'EURUSD' ? '4 decimals' : 'your guess'}" value="${_rt48E(R.g[tk] || '')}" oninput="_rt48PrIn('${tk}',this.value)"></div>`; }).join('')}
      <button type="submit" class="rt47-cta" id="rt48prgo">Reveal live prices</button></form><div class="rt48-msg" role="status" aria-live="polite">${_rt48E(R.msg || '')}</div>`; }

// ── Chart gym expansion: ten random drills on real daily candles ──
const RT48_PAT = { doji: ['Doji', 'Open and close almost equal, with wicks on both sides: buyers and sellers ended the day in a stand-off. It signals indecision, not a direction.'],
  hammer: ['Hammer', 'A small body at the top and a long lower wick, after a fall: sellers pushed price down but buyers drove it back up by the close. It can hint at a bounce, but needs confirmation.'],
  star: ['Shooting star', 'A small body at the bottom and a long upper wick, after a rise: buyers pushed up but sellers drove price back down. It can hint at a pullback, but needs confirmation.'],
  bull: ['Bullish engulfing', 'A down candle followed by a larger up candle whose body covers the previous body: buyers took over. Often read as a possible turn higher, especially after a fall.'],
  bear: ['Bearish engulfing', 'An up candle followed by a larger down candle whose body covers the previous body: sellers took over. Often read as a possible turn lower, especially after a rise.'] };
function _rt48Cls(w, j, avg) { const o = w.o[j], c = w.c[j], h = w.h[j], l = w.l[j], rg = h - l, bd = Math.abs(c - o), up = h - Math.max(o, c), lo = Math.min(o, c) - l; if (!(rg > 0) || j < 6) return null;
  const po = w.o[j - 1], pc = w.c[j - 1], pb = Math.abs(pc - po), fell = w.c[j - 6] > w.c[j - 1] * 1.005, rose = w.c[j - 6] < w.c[j - 1] * 0.995, hits = [];
  if (rg >= 0.5 * avg && bd <= 0.08 * rg && up >= 0.25 * rg && lo >= 0.25 * rg) hits.push('doji');
  if (rg >= 0.6 * avg && bd >= 0.04 * rg && bd <= 0.35 * rg && lo >= 2 * bd && lo >= 0.55 * rg && up <= 0.15 * rg && fell) hits.push('hammer');
  if (rg >= 0.6 * avg && bd >= 0.04 * rg && bd <= 0.35 * rg && up >= 2 * bd && up >= 0.55 * rg && lo <= 0.15 * rg && rose) hits.push('star');
  if (pc < po && c > o && pb >= 0.2 * avg && bd > pb * 1.05 && o <= pc && c >= po) hits.push('bull');
  if (pc > po && c < o && pb >= 0.2 * avg && bd > pb * 1.05 && o >= pc && c <= po) hits.push('bear');
  return hits.length === 1 ? hits[0] : null; }
function _rt48Seg(w, a, b) { return { t: w.t.slice(a, b), o: w.o.slice(a, b), h: w.h.slice(a, b), l: w.l.slice(a, b), c: w.c.slice(a, b) }; }
function _rt48Setup(kind, d, r) { const N = d.c.length; if (N < 45) return null; r = r || Math.random;
  if (kind === 'pattern') { const w = _rt48Win2(d, Math.min(N, 120)), n = w.c.length, rgs = w.h.map((h, k) => h - w.l[k]), cands = [];
    for (let j = Math.max(26, n - 80); j < n; j++) { const avg = rgs.slice(j - 20, j).reduce((s, x) => s + x, 0) / 20, k = _rt48Cls(w, j, avg); if (k) cands.push([j, k]); }
    if (!cands.length) return null; const kinds = [...new Set(cands.map(x => x[1]))], want = kinds[Math.floor(r() * kinds.length)], pick = cands.filter(x => x[1] === want).pop();
    const j = pick[0], seg = _rt48Seg(w, j - 25, j + 1); return { w: seg, ans: pick[1], hl: [seg.c.length - 2, seg.c.length - 1] }; }
  if (kind === 'hhll') { const out = []; for (let off = 0; off + 40 <= N && off <= 60; off += 5) { const seg = _rt48Seg(d, N - off - 40, N - off), H = [], L = [];
      for (let b = 0; b < 4; b++) { H.push(Math.max(...seg.h.slice(b * 10, b * 10 + 10))); L.push(Math.min(...seg.l.slice(b * 10, b * 10 + 10))); }
      const inc = x => x.every((v, k) => !k || v > x[k - 1]), dec = x => x.every((v, k) => !k || v < x[k - 1]), ans = inc(H) && inc(L) ? 'up' : dec(H) && dec(L) ? 'down' : 'mixed'; out.push({ w: seg, ans, H, L }); }
    const kinds = [...new Set(out.map(x => x.ans))], want = kinds[Math.floor(r() * kinds.length)]; return out.find(x => x.ans === want) || null; }
  if (kind === 'breakout') { const out = []; for (let b = N - 25; b >= Math.max(5, N - 110); b--) { const bx = _rt48Seg(d, b, b + 15), hi = Math.max(...bx.h), lo = Math.min(...bx.l), mid = (hi + lo) / 2, ht = (hi - lo) / mid; if (ht < 0.015 || ht > 0.15) continue;
      let k = -1; for (let q = b + 15; q < Math.min(N, b + 36); q++) if (d.c[q] > hi || d.c[q] < lo) { k = q; break; } if (k < 0 || k - (b + 15) < 3 || k - (b + 15) > 20) continue;
      const s0 = Math.max(0, b - 5), s1 = Math.min(N, k + 6); out.push({ w: _rt48Seg(d, s0, s1), box: [b - s0, b - s0 + 14], hi, lo, tgt: k - s0, dir: d.c[k] > hi ? 'up' : 'down' }); if (out.length >= 6) break; }
    return out.length ? out[Math.floor(r() * Math.min(3, out.length))] : null; }
  if (kind === 'pct') { const off = Math.floor(r() * 3) * 10, seg = _rt48Seg(d, N - off - 30, N - off), m = (seg.c[seg.c.length - 1] / seg.c[0] - 1) * 100; if (!isFinite(m)) return null;
    const gap = Math.max(1.5, Math.abs(m) * 0.35), sg = m >= 0 ? 1 : -1, cand = _rt48Shuf([-m, m * 2.2, m / 2.5, m + sg * 6, m - sg * 6, m + sg * 3.5, -m * 1.8], r), opts = [m];
    cand.forEach(x => { if (opts.length < 4 && opts.every(y => Math.abs(y - x) >= gap)) opts.push(x); }); if (opts.length < 4) return null;
    return { w: seg, m, opts: _rt48Shuf(opts, r).map(x => Math.round(x * 10) / 10), ans: Math.round(m * 10) / 10 }; }
  return null; }
function _rt48Win2(d, n) { return _rt47Win(d, n); }
function _rt48Pc(v) { return (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1) + '%'; }
// session builders
function _rt48GymSteps() { const syms = RT47_CHART_SYMS.map(x => x[0]), r = Math.random, pick = () => syms[Math.floor(r() * syms.length)];
  const kinds = _rt48Shuf(['trend', 'trend', 'support', 'resist', 'pattern', 'pattern', 'hhll', 'hhll', 'breakout', 'breakout', 'pct', 'pct'], r).slice(0, 10);
  if (!kinds.some(k => ['pattern', 'hhll', 'breakout', 'pct'].includes(k))) kinds[0] = 'pattern';
  return kinds.map((k, n) => ['trend', 'support', 'resist'].includes(k) ? { t: 'chart', k, s: pick(), alt: n % 2 } : { t: 'c2', k, s: pick() }); }
function _rt48C2Pick(i, s) { const a = _rt47L.a[i] || (_rt47L.a[i] = {}); if (a.set || a.none) return a.sym || '';
  if (!a.t0) { a.t0 = Date.now(); setTimeout(() => { try { if (_rt47L.a[i] === a && !a.set && _rt47L.i === i) _rt47Redraw(); } catch (e) {} }, RT47B_WAIT + 150); }
  const late = Date.now() - a.t0 >= RT47B_WAIT, order = [s.s, ..._rt48Shuf(RT47_CHART_SYMS.map(x => x[0]).filter(x => x !== s.s))]; order.forEach(x => _rt47Fetch(x)); if (late) _rt47bSnapFill();
  const loading = order.some(x => _rt47CD[x] && _rt47CD[x].st === 'loading'), ok = order.filter(x => _rt47CD[x] && _rt47CD[x].st === 'ok'), live = ok.filter(x => _rt47CD[x].src !== 'snap');
  if (!late && (_rt47CD[s.s] || {}).st === 'loading' && !live.length) return '';
  const fin = late || !loading; if (fin && !late) _rt47bSnapFill();
  const ok2 = order.filter(x => _rt47CD[x] && _rt47CD[x].st === 'ok'), tryList = live.concat(fin ? ok2.filter(x => !live.includes(x)) : []);
  for (const sym of tryList) { const st = _rt48Setup(s.k, _rt47CD[sym].d); if (st) { a.sym = sym; a.set = st; return sym; } }
  if (fin) a.none = 1; return ''; }
function _rt48Tap(ev, i) { try { const a = _rt47L.a[i]; if (!a || a.done || !a.set) return; const svg = ev.currentTarget, r = svg.getBoundingClientRect(), N = a.set.w.c.length; let x = (ev.clientX - r.left) / r.width * 340;
  try { const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; x = pt.matrixTransform(svg.getScreenCTM().inverse()).x; } catch (e) {} a.sel = Math.max(0, Math.min(N - 1, Math.floor((x - 4) / ((340 - 54) / N)))); _rt48C2Ans(i, a.sel, svg); } catch (e) {} }
function _rt48C2Sel(i, v) { const a = _rt47L.a[i]; if (!a || a.done) return; a.sel = Number(v); const b = document.getElementById('rt48cbox'); if (b) b.innerHTML = _rt48C2Svg(_rt47Steps(_rt47L.id)[i], i);
  const r = document.getElementById('rt48pick'); if (r) { const w = a.set.w; r.setAttribute('aria-valuetext', `${_rt47Date(w.t[a.sel])}: close ${_rt47Num(w.c[a.sel])}`); } }
function _rt48C2Ans(i, v, el) { const a = _rt47L.a[i], s = _rt47Steps(_rt47L.id)[i]; if (!a || a.done || !a.set) return; const S = a.set;
  a.v = v; a.ok = s.k === 'breakout' ? Math.abs(Number(v) - S.tgt) <= 1 : s.k === 'pct' ? Number(v) === S.ans : v === S.ans; a.done = true;
  _rt47S.chart.n++; if (a.ok) _rt47S.chart.ok++; _rt47Save(); if (a.ok) { _rt47Award(10, el); _rt48S.gx.ok++; _rt48Save(); if (_rt48S.gx.ok >= 5) _rt48Badge('pattern'); _rt48Ev('drill'); }
  _rt46Swap('rt47pl', _rt47PlayerHtml(), '#rt47fb'); }
function _rt48Chart(w, o) { o = o || {}; const N = w.c.length, W = 340, H = 180, pl = 4, pr = 50, pt = 12, pb = 22;
  let mx = Math.max(...w.h), mn = Math.min(...w.l); const pad = (mx - mn) * 0.07 || mx * 0.01; mx += pad; mn -= pad;
  const X = i => pl + (i + 0.5) * (W - pl - pr) / N, Y = v => pt + (mx - v) / (mx - mn) * (H - pt - pb), cw = Math.max(1.6, (W - pl - pr) / N * 0.64), sw = (W - pl - pr) / N, f1 = v => v.toFixed(1);
  let g = ''; for (let k = 0; k < 4; k++) { const v = mn + (mx - mn) * (k + 0.5) / 4; g += `<line x1="${pl}" x2="${W - pr}" y1="${f1(Y(v))}" y2="${f1(Y(v))}" stroke="var(--gb)" stroke-width=".6"/>${_rt47T(W - pr + 4, Y(v) + 3.5, _rt47Num(v), { fs: 9, f: 'm', c: 'var(--t3)' })}`; }
  let bg = ''; if (o.hl) bg += `<rect x="${f1(pl + o.hl[0] * sw)}" y="${pt - 4}" width="${f1((o.hl[1] - o.hl[0] + 1) * sw)}" height="${H - pt - pb + 8}" rx="3" fill="rgba(217,174,82,.16)" stroke="var(--gd)" stroke-width="1"/>`;
  if (o.box) bg += `<rect x="${f1(pl + o.box[0] * sw)}" y="${f1(Y(o.hi))}" width="${f1((o.box[1] - o.box[0] + 1) * sw)}" height="${f1(Y(o.lo) - Y(o.hi))}" fill="rgba(120,160,255,.12)" stroke="rgba(120,160,255,.6)" stroke-width="1"/>`
    + [o.hi, o.lo].map(v => `<line x1="${f1(pl + (o.box[1] + 1) * sw)}" x2="${W - pr}" y1="${f1(Y(v))}" y2="${f1(Y(v))}" stroke="rgba(120,160,255,.6)" stroke-width="1" stroke-dasharray="4 3"/>`).join('');
  let cs = ''; for (let i = 0; i < N; i++) { const up = w.c[i] >= w.o[i], col = up ? 'var(--gn)' : 'var(--rd)', y1 = Y(Math.max(w.o[i], w.c[i])), y2 = Y(Math.min(w.o[i], w.c[i]));
    cs += `<g class="${o.sel === i ? 'rt47-csel' : ''}${o.hit === i ? ' rt47-chit' : ''}"><line x1="${f1(X(i))}" x2="${f1(X(i))}" y1="${f1(Y(w.h[i]))}" y2="${f1(Y(w.l[i]))}" stroke="${col}" stroke-width="1"/><rect x="${f1(X(i) - cw / 2)}" y="${f1(y1)}" width="${f1(cw)}" height="${f1(Math.max(1, y2 - y1))}" fill="${col}"/></g>`; }
  let ov = '';
  if (o.marks) o.marks.forEach(m => { const y = Y(m.v); ov += `<line x1="${f1(pl + m.b * 10 * sw)}" x2="${f1(pl + (m.b * 10 + 10) * sw)}" y1="${f1(y)}" y2="${f1(y)}" stroke="${m.t === 'H' ? 'var(--gd)' : 'rgba(120,160,255,.9)'}" stroke-width="2"/>${_rt47T(pl + (m.b * 10 + 5) * sw, m.t === 'H' ? y - 4 : y + 11, m.lab, { a: 'middle', fs: 9, f: 'm', c: m.t === 'H' ? 'var(--gd)' : 'rgb(150,180,255)', w: 700 })}`; });
  if (o.dots) o.dots.forEach(k => { ov += `<circle cx="${f1(X(k))}" cy="${f1(Y(w.c[k]))}" r="4" fill="var(--gd)" stroke="#14151A" stroke-width="1.5"/>`; });
  if (o.join) ov += `<line x1="${f1(X(o.join[0]))}" y1="${f1(Y(w.c[o.join[0]]))}" x2="${f1(X(o.join[1]))}" y2="${f1(Y(w.c[o.join[1]]))}" stroke="var(--gd)" stroke-width="1.5" stroke-dasharray="5 4"/>`;
  if (o.sel != null && o.hit == null) ov += `<line x1="${f1(X(o.sel))}" x2="${f1(X(o.sel))}" y1="${pt}" y2="${H - pb}" stroke="var(--tx)" stroke-width="1" stroke-dasharray="2 3" opacity=".7"/>`;
  if (o.hit != null) ov += `<line x1="${f1(X(o.hit))}" x2="${f1(X(o.hit))}" y1="${pt}" y2="${H - pb}" stroke="var(--gd)" stroke-width="1.5"/>`;
  const dl = `${_rt47T(pl, H - 6, _rt47Date(w.t[0]), { fs: 9, f: 'm', c: 'var(--t3)' })}${_rt47T(W - pr, H - 6, _rt47Date(w.t[N - 1]), { a: 'end', fs: 9, f: 'm', c: 'var(--t3)' })}`;
  return `<svg class="rt47-svg rt47-chart${o.tap ? ' tap' : ''}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${_rt47E(o.label || 'Price chart')}"${o.tap ? ` onclick="_rt48Tap(event,${o.si})"` : ''}><title>${_rt47E(o.label || 'Price chart')}</title>${bg}${g}${cs}${ov}${dl}</svg>`; }
function _rt48C2Svg(s, i) { const a = _rt47L.a[i] || {}, S = a.set, w = S.w, nm = _rt47Name(a.sym), n = w.c.length, lab = `${nm}: ${n} daily candles, ${_rt47Date(w.t[0])} to ${_rt47Date(w.t[n - 1])}`;
  if (s.k === 'pattern') return _rt48Chart(w, { label: lab + '. The last two candles are highlighted.', hl: S.hl });
  if (s.k === 'hhll') return _rt48Chart(w, { label: lab + '. Split into four blocks of ten candles.', hl: null, marks: a.done ? [0, 1, 2, 3].flatMap(b => [{ b, v: S.H[b], t: 'H', lab: 'H' + (b + 1) }, { b, v: S.L[b], t: 'L', lab: 'L' + (b + 1) }]) : null });
  if (s.k === 'breakout') return _rt48Chart(w, { label: lab + '. The shaded box is the 15-day range.', box: S.box, hi: S.hi, lo: S.lo, tap: !a.done, si: i, sel: a.sel, hit: a.done ? S.tgt : null });
  if (s.k === 'pct') return _rt48Chart(w, { label: lab + '. Gold dots mark the first and last close.', dots: [0, n - 1], join: a.done ? [0, n - 1] : null });
  return ''; }
function _rt48C2Html(s, i) { const sym = _rt48C2Pick(i, s), a = _rt47L.a[i] || {}, H = (h, k) => `<div class="rt47-sk">${k}</div><h1 class="rt47-sh" id="rt47plh" tabindex="-1">${_rt47E(h)}</h1>`;
  const title = { pattern: 'Name the candle pattern', hhll: 'Highs and lows', breakout: 'Find the breakout', pct: 'Estimate the move' }[s.k] || 'Chart drill', c = sym ? _rt47CD[sym] : null, kick = c && c.src === 'snap' ? 'CHART GYM · SAVED DATA' : 'CHART GYM · REAL DATA';
  if (!a.set) { if (a.none) return `${H(title, 'CHART GYM')}<div class="rt47-load" role="status">No clean example of this pattern in the charts available right now. Skip to the next drill.</div><button type="button" class="rt47-btn" onclick="_rt47Skip(${i})">Skip this drill</button>`;
    return `${H(title, 'CHART GYM')}<div class="rt47-load" role="status"><span class="rt47-spin" aria-hidden="true"></span>Loading real chart data…</div>${_rt47bSkipBtn(i)}`; }
  const S = a.set, w = S.w, nm = _rt47Name(sym), n = w.c.length, fine = `<p class="rt47-fine">${_rt47E(nm)} · daily candles · ${_rt47Date(w.t[0])} to ${_rt47Date(w.t[n - 1])} · ${_rt47bSrc(sym)}</p>`;
  const box = `${_rt47bBadge(sym)}<div class="rt47-chartbox" id="rt48cbox">${_rt48C2Svg(s, i)}</div>`, fb = (ok, txt) => `<div class="rt47-fb ${ok ? 'ok' : 'no'}" id="rt47fb" tabindex="-1" role="status"><strong>${ok ? 'Correct!' : 'Not quite.'}</strong> ${txt}</div>`;
  const btns = (opts) => `<div class="rt47-opts rt48-c2o" role="group" aria-label="Answers">${opts.map(([v, l]) => { const st = !a.done ? '' : v === S.ans ? ' ok' : a.v === v ? ' no' : ' dim'; return `<button type="button" class="rt47-opt${st}" ${a.done ? 'aria-disabled="true"' : ''} onclick="_rt48C2Ans(${i},${typeof v === 'string' ? `'${v}'` : v},this)"><span class="rt47-ok-i" aria-hidden="true">${!a.done ? '' : v === S.ans ? '✓' : a.v === v ? '✗' : ''}</span>${_rt47E(l)}</button>`; }).join('')}</div>`;
  if (s.k === 'pattern') { const P = RT48_PAT[S.ans], j = n - 1;
    return `${H(title, kick)}<p class="rt47-sb sm">Look at the <b>last candle</b> in the gold box, together with the one before it. Which pattern is it?</p>${box}${btns(Object.entries(RT48_PAT).map(([k, v]) => [k, v[0]]))}
      ${a.done ? fb(a.ok, `It is a <b>${_rt47E(P[0])}</b> on ${_rt47Date(w.t[j])} (open ${_rt47Num(w.o[j])}, high ${_rt47Num(w.h[j])}, low ${_rt47Num(w.l[j])}, close ${_rt47Num(w.c[j])}). ${_rt47E(P[1])} A single candle is a weak signal on its own.`) : ''}${fine}${_rt47bSkipBtn(i)}`; }
  if (s.k === 'hhll') { const L = { up: 'Higher highs and higher lows', down: 'Lower highs and lower lows', mixed: 'Mixed: no clear structure' };
    return `${H(title, kick)}<p class="rt47-sb sm">Split this ${_rt47E(nm)} chart into four blocks of ten days. Do the highs and the lows both keep rising, both keep falling, or neither?</p>${box}${btns(Object.entries(L))}
      ${a.done ? fb(a.ok, `Block highs: ${S.H.map(_rt47Num).join(' → ')}. Block lows: ${S.L.map(_rt47Num).join(' → ')}. ${S.ans === 'up' ? 'Both rising is the classic definition of an uptrend.' : S.ans === 'down' ? 'Both falling is the classic definition of a downtrend.' : 'When highs and lows do not move together the market has no clean trend; many traders treat that as a range or a turning point.'}`) : ''}${fine}${_rt47bSkipBtn(i)}`; }
  if (s.k === 'breakout') { const k = S.tgt;
    return `${H(title, kick)}<p class="rt47-sb sm">The shaded box is a 15-day trading range on ${_rt47E(nm)}. Tap the <b>first candle that closes outside</b> the box.</p>${box}
      ${a.done ? fb(a.ok, `The first close outside the range was ${_rt47Date(w.t[k])} at ${_rt47Num(w.c[k])}, ${S.dir === 'up' ? 'above the top' : 'below the bottom'} of the box (${_rt47Num(S.dir === 'up' ? S.hi : S.lo)}). Many breakouts fail and slip back into the range, which is why traders watch the close, not just an intraday spike.`)
        : `<div class="rt47-kb"><label for="rt48pick">Or use the slider to choose a candle</label><input type="range" id="rt48pick" min="0" max="${n - 1}" value="${a.sel != null ? a.sel : Math.floor(n / 2)}" oninput="_rt48C2Sel(${i},this.value)" aria-valuetext="Choose a candle"><button type="button" class="rt47-btn" onclick="if(_rt47L.a[${i}]&&_rt47L.a[${i}].sel==null)_rt48C2Sel(${i},document.getElementById('rt48pick').value);_rt48C2Ans(${i},_rt47L.a[${i}].sel,this)">Check this candle</button></div>`}${fine}${_rt47bSkipBtn(i)}`; }
  if (s.k === 'pct') return `${H(title, kick)}<p class="rt47-sb sm">Roughly how much did ${_rt47E(nm)} move from the first close to the last close (the gold dots)? Use the price scale on the right.</p>${box}${btns(S.opts.map(v => [v, _rt48Pc(v)]))}
      ${a.done ? fb(a.ok, `From ${_rt47Num(w.c[0])} to ${_rt47Num(w.c[n - 1])} is ${_rt48Pc(S.m)}: (last ÷ first − 1) × 100. Charts that zoom to fit can make small moves look big, so always check the scale.`) : ''}${fine}${_rt47bSkipBtn(i)}`;
  return ''; }

// ── Auto-updating content: weekly-moves quiz, news cards, optional server explainers ──
// Everything is rebuilt once per London day from the site's own feeds and cached on the device.
const _RT48_AUTO_KEY = 'td_academy_auto_v1';
let _rt48Wk = { at: 0, qs: null }, _rt48Nw = { at: 0, cards: null }, _rt48Ai = { at: 0, items: [] }, _rt48AutoDay = '', _rt48AutoBusy = 0;
function _rt48DayNum() { return Math.floor(Date.parse(_rt46Day() + 'T00:00:00Z') / 864e5); }
function _rt48AutoSave() { try { localStorage.setItem(_RT48_AUTO_KEY, JSON.stringify({ day: _rt48AutoDay, wk: _rt48Wk, nw: _rt48Nw, ai: _rt48Ai })); } catch (e) {} }
function _rt48AutoLoad() { try { const o = JSON.parse(localStorage.getItem(_RT48_AUTO_KEY) || '{}'); if (o.day !== _rt46Day()) return false;
  if (o.wk && Array.isArray(o.wk.qs)) _rt48Wk = o.wk; if (o.nw && Array.isArray(o.nw.cards)) _rt48Nw = o.nw; if (o.ai && Array.isArray(o.ai.items)) _rt48Ai = o.ai; return true; } catch (e) { return false; } }
function _rt48WkReady() { return !!(_rt48Wk.qs && _rt48Wk.qs.length >= 2); }
function _rt48NwReady() { return !!(_rt48Nw.cards && _rt48Nw.at); }
function _rt48AutoKick() { const day = _rt46Day(); if (_rt48AutoDay === day) return; _rt48AutoDay = day; _rt48Wk = { at: 0, qs: null }; _rt48Nw = { at: 0, cards: null }; _rt48Ai = { at: 0, items: [] };
  const had = _rt48AutoLoad(); _rt48QuizReg();
  if (!_rt48WkReady()) _rt48WkBuild(); if (!_rt48NwReady()) _rt48NwBuild(); if (!had || !_rt48Ai.tried) _rt48AiFetch(); }
// register auto questions so the shared quiz player (and its once-only XP) can use them
function _rt48QuizReg() { try { RT46_QUIZ.week = {}; RT46_QUIZ.news = {}; const dn = _rt48DayNum(); (_rt48Wk.qs || []).forEach((q, k) => { RT46_QUIZ.week[dn * 10 + k] = q; }); (_rt48Ai.items || []).forEach((it, k) => { RT46_QUIZ.news[dn * 10 + 5 + k] = [it.q, it.o, it.a, it.e]; }); } catch (e) {} }
function _rt48AutoDone() { _rt48QuizReg(); _rt48AutoSave(); try { _rt48HubTick(); } catch (e) {}
  try { const s = _rt47L.id && _rt47Steps(_rt47L.id)[_rt47L.i]; if (s && s.t === 'wl') { delete _rt48Sess[_rt47L.id]; _rt47L.i = 0; _rt47L.a = {}; _rt47Redraw(); } } catch (e) {} }
// 1) This week in markets: last complete daily close vs the close a week earlier
const RT48_WK_SYMS = ['GC=F', '^GSPC', 'BTC-USD', 'ETH-USD', 'CL=F', 'EURUSD=X', 'DX-Y.NYB', '^FTSE'];
function _rt48WkBuild() { if (_rt48AutoBusy & 1) return; _rt48AutoBusy |= 1; const t0 = Date.now();
  const poll = () => { try { RT48_WK_SYMS.forEach(s => _rt47Fetch(s)); const loading = RT48_WK_SYMS.some(s => _rt47CD[s] && _rt47CD[s].st === 'loading');
    if (loading && Date.now() - t0 < 25000) return setTimeout(poll, 1500); _rt48AutoBusy &= ~1; const r = _rt48WkMake(); if (r) { _rt48Wk = r; _rt48AutoDone(); } else _rt48Wk = { at: 0, qs: null, fail: Date.now() }; } catch (e) { _rt48AutoBusy &= ~1; } };
  poll(); }
function _rt48WkMake() { const todayUTC = Math.floor(Date.now() / 864e5), M = [];
  RT48_WK_SYMS.forEach(sym => { const c = _rt47CD[sym]; if (!c || c.st !== 'ok' || c.src === 'snap') return; const d = c.d; let N = d.c.length; while (N > 0 && Math.floor(d.t[N - 1] / 864e5) >= todayUTC) N--; if (N < 8) return;
    const lt = d.t[N - 1]; if (Date.now() - lt > 6 * 864e5) return; let k = -1; for (let j = N - 2; j >= 0; j--) if (d.t[j] <= lt - 7 * 864e5 + 6 * 36e5) { k = j; break; } if (k < 0) return;
    M.push({ sym, nm: _rt47Name(sym), chg: (d.c[N - 1] / d.c[k] - 1) * 100, a: d.c[k], b: d.c[N - 1], ta: d.t[k], tb: lt }); });
  if (M.length < 4) return null; const R = _rt48Rand('wk:' + _rt46Day()), pc = v => _rt48Pc(v), byS = s => M.find(x => x.sym === s), qs = [], srt = M.slice().sort((x, y) => y.chg - x.chg);
  const from = Math.min(...M.map(x => x.ta)), to = Math.max(...M.map(x => x.tb)), list = srt.map(x => `${x.nm} ${pc(x.chg)}`).join(', ');
  const three = (best) => { const rest = _rt48Shuf(srt.filter(x => x !== best), R), pk = [best]; rest.forEach(x => { if (pk.length < 3 && pk.every(y => Math.abs(y.chg - x.chg) >= 0.3)) pk.push(x); }); return pk.length === 3 ? pk : null; };
  let p = three(srt[0]); if (p) { const o = _rt48Shuf(p, R).map(x => x.nm); qs.push(['Over the past week, which of these rose the most (or fell the least)?', o, o.indexOf(srt[0].nm), `${srt[0].nm} ${pc(srt[0].chg)}. The three: ${p.map(x => `${x.nm} ${pc(x.chg)}`).join(', ')}. Weekly change = latest daily close vs the close a week earlier.`]); }
  const g = byS('GC=F'); if (g) { const k = g.chg > 0.25 ? 0 : g.chg < -0.25 ? 1 : 2; qs.push([`Did gold end the week higher, lower or roughly flat (within ±0.25%)?`, ['Higher', 'Lower', 'Roughly flat'], k, `Gold futures went from ${_rt47Num(g.a)} (${_rt47Date(g.ta)}) to ${_rt47Num(g.b)} (${_rt47Date(g.tb)}): ${pc(g.chg)}.`]); }
  const w = srt[srt.length - 1]; p = three(w); if (p && w !== srt[0]) { const o = _rt48Shuf(p, R).map(x => x.nm); qs.push(['Which of these had the weakest week?', o, o.indexOf(w.nm), `${w.nm} ${pc(w.chg)}. The three: ${p.map(x => `${x.nm} ${pc(x.chg)}`).join(', ')}.`]); }
  const b = byS('BTC-USD'); if (b) { const v = b.chg, k = v < -5 ? 0 : v < 0 ? 1 : v <= 5 ? 2 : 3; qs.push(['How much did Bitcoin move over the week?', ['Down more than 5%', 'Down 0–5%', 'Up 0–5%', 'Up more than 5%'], k, `Bitcoin went from ${_rt47Num(b.a)} to ${_rt47Num(b.b)}: ${pc(v)}. Weekly swings of 5% or more are common for crypto and rare for major currencies.`]); }
  const dx = byS('DX-Y.NYB'); if (dx && g && Math.abs(dx.chg) >= 0.1 && Math.abs(g.chg) >= 0.1) { const opp = (dx.chg > 0) !== (g.chg > 0); qs.push(['Did the US dollar index and gold move in opposite directions this week?', ['Yes, opposite directions', 'No, the same direction'], opp ? 0 : 1, `Dollar index ${pc(dx.chg)}, gold ${pc(g.chg)}. Gold is priced in dollars, so the two often move in opposite directions, but not always: fear can lift both.`]); }
  if (qs.length < 2) return null; return { at: Date.now(), qs: qs.slice(0, 5), from, to, list }; }
// 2) In the news: recent headlines matched to scenario templates
const RT48_NEWS_ROWS = {
  'Earnings beat': [['The company\'s shares', 'up', 'Results that beat what was priced in usually lift the shares. If hopes were even higher, they can still fall.'], ['Shares of its closest rivals', 'up', 'Investors often read across from one firm to its peers. This is a weaker, less reliable effect.']],
  'Earnings miss': [['The company\'s shares', 'down', 'Lower expected profits mean a lower value for the shares.'], ['Shares of its closest rivals', 'down', 'Investors may worry the same problem hits the whole sector. This is a weaker, less reliable effect.']] };
let _rt48DynIdx = {}, RT48_DYN0 = 0;
function _rt48NewsItems(list) { const now = Date.now(), out = []; (list || []).forEach(it => { try { const h = String(it.x || it.title || it.headline || '').replace(/\s+/g, ' ').trim(); if (h.length < 20 || h.length > 240 || /\b\d+ (\w+ ){0,2}(stocks?|reasons?|ways|things)\b|should you|\bbuy (these|now)\b|regret|\blive\b|premier league|\?\s*$/i.test(h)) return;
  let t = typeof it.ts === 'number' ? it.ts : Date.parse(it.ts || it.t || it.pubDate || ''); if (t && t < 1e12) t *= 1000; if (!isFinite(t) || !t || now - t > 72 * 36e5 || t - now > 36e5) return;
  const link = /^https:\/\/[^\s"'<>]+$/.test(String(it.link || '')) ? String(it.link) : ''; out.push({ h, t, link, src: String(it.src || it.source || '').slice(0, 40) }); } catch (e) {} }); return out.sort((a, b) => b.t - a.t); }
function _rt48NwMake(list) { const items = _rt48NewsItems(list), used = {}, cards = [];
  for (const it of items) { if (cards.length >= 4) break; const m = RT48_NEWS_T.find(x => x[0].test(it.h)); if (!m || used[m[1]]) continue; const n = _rt48ScenByName(m[1]); if (n < 0) continue;
    used[m[1]] = 1; cards.push({ title: m[1], h: it.h, t: it.t, link: it.link, src: it.src, kind: RT48_ECON_IDX.includes(n) ? 'econ' : 'scen' }); }
  return { at: Date.now(), cards, seen: items.length }; }
function _rt48NwBuild() { if (_rt48AutoBusy & 2) return; _rt48AutoBusy |= 2; const t0 = Date.now();
  const go = async () => { try { let list = (typeof NEWS !== 'undefined' && Array.isArray(NEWS)) ? NEWS : [];
      if (_rt48NewsItems(list).length < 15 && Date.now() - t0 < 9000) return setTimeout(go, 1500);
      if (_rt48NewsItems(list).length < 15 && typeof fetchSingleFeed === 'function' && typeof RSS_FEEDS !== 'undefined') { const ids = ['f0', 'f1', 'f4', 'f9', 'f12'], fs = RSS_FEEDS.filter(f => ids.includes(f.id));
        const got = await Promise.all(fs.map(f => fetchSingleFeed(f).catch(() => []))); list = list.concat(...got); }
      _rt48Nw = _rt48NwMake(list); _rt48AutoBusy &= ~2; _rt48AutoDone(); } catch (e) { _rt48AutoBusy &= ~2; } };
  go(); }
function _rt48Card(c) { const key = 'n' + _rt46Hash(c.h); if (_rt48DynIdx[key] != null) return _rt48DynIdx[key]; const n = _rt48ScenByName(c.title); if (n < 0) return -1;
  const rows = RT48_NEWS_ROWS[c.title] || RT47_SCEN[n][2]; _rt48DynIdx[key] = RT47_SCEN.push([c.title, `“${c.h}”`, rows, { auto: 1, h: c.h, t: c.t, link: c.link, src: c.src, kind: c.kind, key }]) - 1; return _rt48DynIdx[key]; }
// 3) Optional server explainers (rt48s): strictly validated; any failure is silent and the templates stay
function _rt48AiOk(it) { if (!it || typeof it !== 'object') return null; const S = (v, n, m) => typeof v === 'string' && v.trim().length >= (m || 3) && v.length <= n && !/<|>|https?:/i.test(v) ? v.trim() : null;
  const q = S(it.q, 220), e = S(it.e, 420), h = S(it.h, 240), o = Array.isArray(it.o) && it.o.length === 3 ? it.o.map(x => S(x, 90, 2)) : null, a = Number.isInteger(it.a) && it.a >= 0 && it.a <= 2 ? it.a : null;
  if (!q || !e || !o || o.some(x => !x) || a == null || new Set(o).size !== 3) return null; const link = typeof it.link === 'string' && /^https:\/\/[^\s"'<>]{5,300}$/.test(it.link) ? it.link : '';
  return { q, e, h: h || '', o, a, link, src: typeof it.src === 'string' ? it.src.slice(0, 40).replace(/[<>]/g, '') : '' }; }
function _rt48AiFetch() { if (_rt48AutoBusy & 4) return; _rt48AutoBusy |= 4; let opts = {}; try { opts = { signal: AbortSignal.timeout(9000), credentials: 'same-origin' }; } catch (e) {}
  fetch('/api/academy-daily', opts).then(r => r && r.ok && /json/.test(r.headers.get('content-type') || '') ? r.json() : null).then(j => {
    const items = j && Array.isArray(j.items) ? j.items.map(_rt48AiOk).filter(Boolean).slice(0, 3) : [];
    _rt48Ai = { at: items.length ? (Date.parse(j.generatedAt) || Date.now()) : 0, items, kind: j && j.kind === 'ai' ? 'ai' : 'template', tried: 1 }; })
    .catch(() => { _rt48Ai = { at: 0, items: [], tried: 1 }; }).finally(() => { _rt48AutoBusy &= ~4; _rt48AutoDone(); }); }
// player sessions for auto content
function _rt48WeekSteps() { if (!_rt48WkReady()) { _rt48AutoKick(); if (!_rt48WkReady() && !(_rt48AutoBusy & 1) && _rt48Wk.fail) _rt48WkBuild(); return [{ t: 'wl' }]; }
  const dn = _rt48DayNum(), W = _rt48Wk;
  return [{ t: 'info', kick: 'AUTO-GENERATED · REAL DATA', h: 'This week in markets', b: `A quiz built automatically from real daily closes: ${_rt47Date(W.from)} to ${_rt47Date(W.to)}. It refreshes every day.`, fresh: W.at, fine: "Source: Yahoo Finance and CoinGecko via the site's chart feeds. Weekly change compares the latest complete daily close with the close a week earlier." },
    ...W.qs.map((q, k) => ({ t: 'q', n: dn * 10 + k, wk: 1 }))]; }
function _rt48NewsSteps() { if (!_rt48NwReady()) { _rt48AutoKick(); return [{ t: 'wl' }]; } const dn = _rt48DayNum(), cards = _rt48Nw.cards.slice(0, 4).map(c => _rt48Card(c)).filter(n => n >= 0);
  const st = [{ t: 'info', kick: 'AUTO-GENERATED · FROM TODAY\'S HEADLINES', h: 'In the news', b: cards.length ? `${cards.length} recent headline${cards.length === 1 ? '' : 's'} from the site's news feeds, matched automatically to a market scenario. Each card asks: if this news was a surprise, what is the usual first reaction?` : 'None of the latest headlines matched a scenario template today, so here are three from the scenario bank instead.', fresh: _rt48Nw.at, fine: 'Headlines are matched by keywords, so a card can occasionally mismatch the story. Typical first reactions, not rules or forecasts.' }];
  (cards.length ? cards : _rt48Shuf(RT48_SCEN_IDX, _rt48Rand('nwfb:' + _rt46Day())).slice(0, 3)).forEach(n => st.push({ t: 'scen', n, news: 1 }));
  (_rt48Ai.items || []).forEach((it, k) => st.push({ t: 'q', n: dn * 10 + 5 + k, ai: 1 })); return st; }

// ── rt48 wiring into the rt47 Academy (wrappers only; rt47 code is untouched) ──
RT48_DYN0 = RT47_SCEN.length;
let _rt48Sess = {};
const RT48_SESS_IDS = ['gym', 'scen', 'econ', 'week', 'news'];
{ const _me8 = _rt47Meta; _rt47Meta = function (id) {
  try {
    if (id === 'gym') return { t: 'Chart gym', ic: 'chart', min: 6, tag: 'Ten random drills on real daily charts', steps: _rt48Sess.gym || (_rt48Sess.gym = _rt48GymSteps()) };
    if (id === 'scen') return { t: 'Scenario room', ic: 'spark', min: 4, tag: 'What usually happens next?', steps: _rt48Sess.scen || (_rt48Sess.scen = _rt48Shuf(RT48_SCEN_IDX).slice(0, 6).map(n => ({ t: 'scen', n }))) };
    if (id === 'econ') return { t: 'Economic calendar', ic: 'calendar', min: 3, tag: 'Data surprises and the usual first moves', steps: _rt48Sess.econ || (_rt48Sess.econ = _rt48EconSteps()) };
    if (id === 'week') { const st = _rt48Sess.week || _rt48WeekSteps(); if (st[0].t !== 'wl') _rt48Sess.week = st; return { t: 'This week in markets', ic: 'bars', min: 2, tag: 'Built from real moves', steps: st }; }
    if (id === 'news') { const st = _rt48Sess.news || _rt48NewsSteps(); if (st[0].t !== 'wl') _rt48Sess.news = st; return { t: 'In the news', ic: 'table', min: 3, tag: 'Headlines into scenarios', steps: st }; }
  } catch (e) {}
  return _me8.apply(this, arguments); }; }
function _rt48EconSteps() { const st = [{ t: 'info', kick: 'ECONOMIC CALENDAR', h: 'Surprise is what moves markets', b: 'Markets price in the forecast before a release. What moves prices is the gap between the actual number and that forecast. For each release below, call the usual first reaction in the dollar, bond yields and gold.', fine: 'These are typical first reactions to a surprise, not rules. A big revision to last month, or other news the same day, can change the move.' }];
  try { (_rt48Nw.cards || []).filter(c => c.kind === 'econ').slice(0, 2).forEach(c => { const n = _rt48Card(c); if (n >= 0) st.push({ t: 'scen', n, news: 1 }); }); } catch (e) {}
  _rt48Shuf(RT48_ECON_IDX).slice(0, 6 - st.length).forEach(n => st.push({ t: 'scen', n })); return st; }
// fresh random session each time a practice set is opened; leaving an activity closes it
{ const _op8 = _rt47Open; _rt47Open = function (id) { try { if (RT48_SESS_IDS.includes(id)) delete _rt48Sess[id]; _rt48Stop(); _rt48A = { id: '' }; } catch (e) {} const r = _op8.apply(this, arguments); setTimeout(_rt45SyncUrl, 0); return r; }; }
// redraw guard: include the open activity in the view signature, and keep activities steady between user actions
{ const _sg8 = _rt47SigNow; _rt47SigNow = function () { return _sg8.apply(this, arguments) + '|' + (_rt48A.id || ''); }; }
{ const _ho8 = _rt47Hold; _rt47Hold = function () { if (_ho8.apply(this, arguments)) return true; try { const onL = (typeof pg !== 'undefined' && pg === 'learn') || !!document.getElementById('learnOv');
  return onL && !!document.getElementById('rt48act') && _rt47SigNow() === _rt47Sig && Date.now() - _rt47Prog > 1200; } catch (e) { return false; } }; }
{ const _rl8 = renderLearn; renderLearn = function () { const h = _rl8.apply(this, arguments);
  try { if (_rt48A.id && RT48_ACTS[_rt48A.id] && !_learnSub && _learnTab === 'start' && !_rt47L.id) { _rt47Sig = _rt47SigNow(); return `<div class="rt47-wrap rt47-inpl">${_rt47TopHtml(false)}${_rt48Html()}</div>`; } } catch (e) {} return h; }; }
{ const _hh8 = _rt47HomeHtml; _rt47HomeHtml = function () { let h = _hh8.apply(this, arguments);
  try { h = h.replace('<div class="rt47-grid">', _rt48HubHtml() + '<div class="rt47-grid">')
    .replace('Four quick drills on real daily charts of gold, the S&amp;P 500 and more.', 'Ten random drills on real daily charts: trends, levels, candle patterns, breakouts and % moves.')
    .replace('Six market shocks. Call the usual first move in gold, the dollar and yields.', `Six of ${RT48_SCEN_IDX.length} market shocks, picked at random. Call the usual first move in gold, the dollar and yields.`); } catch (e) {} return h; }; }
{ const _su8 = _rt45SyncUrl; _rt45SyncUrl = function () { try { if (_rt48A.id && !_rt47L.id && /^\/learn\/?$/.test(location.pathname) && !_learnSub && _learnTab === 'start') { const q = '?act=' + encodeURIComponent(_rt48A.id); if (location.search !== q) history.replaceState(history.state, '', '/learn/' + q);
  document.title = `${RT48_ACTS[_rt48A.id].t} | Dispatch Academy | The Dispatch Markets`; return; } } catch (e) {} return _su8.apply(this, arguments); }; }
{ const _tb8 = _rt45Tab; _rt45Tab = function () { _rt48Stop(); _rt48A = { id: '' }; return _tb8.apply(this, arguments); };
  const _op8 = _rt45Open; _rt45Open = function () { _rt48Stop(); _rt48A = { id: '' }; return _op8.apply(this, arguments); };
  const _te8 = _rt45Term; _rt45Term = function () { _rt48Stop(); _rt48A = { id: '' }; return _te8.apply(this, arguments); };
  try { const _nv8 = nav; nav = function (p) { if (p !== 'learn') { _rt48Stop(); _rt48A = { id: '' }; } return _nv8.apply(this, arguments); }; } catch (e) {} }
window.addEventListener('popstate', () => { try { if (_rt48A.id && !/[?&]act=/.test(location.search)) { _rt48Stop(); _rt48A = { id: '' }; } } catch (e) {} });
// deep links: /learn/?act=speed and /learn/?lesson=econ|week|news
try { if (/^\/learn\/?$/.test(location.pathname)) { const q = new URLSearchParams(location.search), act = q.get('act'), les = q.get('lesson');
  if (act && RT48_ACTS[act]) { if (RT48_ACTS[act].pl) { _rt47L = { id: act, i: 0, a: {}, xp: 0, fin: false, dir: 1 }; } else { _rt48A = { id: act }; _rt48Init(act); } _learnTab = 'start'; _learnSub = null; }
  else if (les && !_rt47L.id && ['econ', 'week', 'news'].includes(les)) { _rt47L = { id: les, i: 0, a: {}, xp: 0, fin: false, dir: 1 }; _learnTab = 'start'; _learnSub = null; } } } catch (e) {}
// new step types
{ const _sh8 = _rt47StepHtml; _rt47StepHtml = function (s, i) {
  const H = (h, k) => `${k ? `<div class="rt47-sk">${k}</div>` : ''}<h1 class="rt47-sh" id="rt47plh" tabindex="-1">${_rt47E(h)}</h1>`;
  try { if (s.t === 'c2') return _rt48C2Html(s, i);
    if (s.t === 'wl') return `${H(_rt47Meta(_rt47L.id).t, 'AUTO-GENERATED')}<div class="rt47-load" role="status"><span class="rt47-spin" aria-hidden="true"></span>${_rt47L.id === 'week' ? 'Building this week\'s quiz from real daily closes…' : 'Reading today\'s headlines…'}</div><p class="rt47-fine">This takes a few seconds the first time each day, then it is saved on this device.</p>`;
    if (s.t === 'info') return `${H(s.h, s.kick)}${s.fresh ? `<p class="rt48-fresh in">${_rt47E(_rt48Fresh(s.fresh))}</p>` : ''}<p class="rt47-sb">${_rt47E(s.b)}</p>${s.fine ? `<p class="rt47-fine">${_rt47E(s.fine)}</p>` : ''}`;
  } catch (e) { return `${H('Chart drill', 'CHART GYM')}<div class="rt47-load" role="status">This drill could not load. Skip to the next one.</div><button type="button" class="rt47-btn" onclick="_rt47Skip(${i})">Skip this drill</button>`; }
  let h = _sh8.apply(this, arguments);
  try { if (s.t === 'scen') { const sc = RT47_SCEN[s.n], m = sc && sc[3];
      if (m && m.auto) { h = h.replace(/<div class="rt47-sk">[^<]*<\/div>/, `<div class="rt47-sk">IN THE NEWS · AUTO-GENERATED</div>`).replace('<p class="rt47-sb sm">What is the usual first reaction?', `<p class="rt48-src">${m.src ? _rt47E(m.src) + ' · ' : ''}${_rt47E(_rt47Date(m.t))} ${_rt48UK(m.t)} UK${m.link ? ` · <a href="${_rt47E(m.link)}" target="_blank" rel="noopener noreferrer">Read the story ↗</a>` : ''}</p><p class="rt47-sb sm">If this news was a surprise, what is the usual first reaction?`); }
      else if (RT48_ECON_IDX.includes(s.n)) h = h.replace(/<div class="rt47-sk">[^<]*<\/div>/, '<div class="rt47-sk">ECONOMIC CALENDAR · DATA SURPRISE</div>'); }
    if (s.t === 'q' && s.wk) h = h.replace('<div class="rt47-sk">QUICK CHECK</div>', '<div class="rt47-sk">THIS WEEK · REAL DATA</div>');
    if (s.t === 'q' && s.ai) { const it = (_rt48Ai.items || [])[s.n % 10 - 5]; h = h.replace('<div class="rt47-sk">QUICK CHECK</div>', '<div class="rt47-sk">AUTO-GENERATED EXPLAINER</div>');
      if (it && it.h) h = h.replace('<div class="rt47-opts"', `<p class="rt48-src">Based on: “${_rt47E(it.h)}”${it.src ? ' · ' + _rt47E(it.src) : ''}${it.link ? ` · <a href="${_rt47E(it.link)}" target="_blank" rel="noopener noreferrer">Story ↗</a>` : ''} · ${_rt47E(_rt48Fresh(_rt48Ai.at))}</p><div class="rt47-opts"`); } } catch (e) {}
  return h; }; }
{ const _ca8 = _rt47Can; _rt47Can = function (i) { try { const s = _rt47Steps(_rt47L.id)[i], a = _rt47L.a[i];
  if (s && s.t === 'c2') return !!(a && (a.done || a.skip || a.none || (!a.set && a.t0 && Date.now() - a.t0 >= RT47B_WAIT))); if (s && s.t === 'wl') return false; } catch (e) {} return _ca8.apply(this, arguments); }; }
{ const _ph8 = _rt47PlayerHtml; _rt47PlayerHtml = function () { const h = _ph8.apply(this, arguments); try { const s = _rt47Steps(_rt47L.id)[_rt47L.i]; return h.replace(/(class="rt47-go"[^>]*disabled>)(<\/button>)/, `$1${s && s.t === 'wl' ? 'Loading…' : 'Answer to continue'}$2`); } catch (e) { return h; } }; }
{ const _wt8 = _rt47bWaiting; _rt47bWaiting = function () { if (_wt8.apply(this, arguments)) return true; try { if (!_rt47L.id) return false; const s = _rt47Steps(_rt47L.id)[_rt47L.i], a = _rt47L.a[_rt47L.i];
  return !!(s && s.t === 'c2' && !(a && ((a.set && a.shown === a.sym) || a.none))); } catch (e) { return false; } }; }
// progress events → weekly challenge and badges
{ const _sc8 = _rt47ScenCheck; _rt47ScenCheck = function (i, el) { let s, was, tmp = false; try { s = _rt47Steps(_rt47L.id)[i]; was = !!(_rt47L.a[i] && _rt47L.a[i].done); if (s && s.n >= RT48_DYN0 && !_rt47S.scen[s.n]) { _rt47S.scen[s.n] = 1; tmp = true; } } catch (e) {}
  const r = _sc8.apply(this, arguments);
  try { if (tmp) { delete _rt47S.scen[s.n]; _rt47Save(); } const a = _rt47L.a[i]; if (s && !was && a && a.done && a.ok) { const sc = RT47_SCEN[s.n], m = sc[3];
    if (m && m.auto) { if (!_rt48S.nw) _rt48S.nw = {}; if (!_rt48S.nw[m.key]) { _rt48S.nw[m.key] = 1; _rt48Save(); _rt47Award(10, el); } _rt48Ev(m.kind === 'econ' ? 'econ' : 'scen'); if (m.kind === 'econ') { _rt48S.cal.ok++; _rt48Save(); if (_rt48S.cal.ok >= 5) _rt48Badge('cal'); } }
    else if (RT48_ECON_IDX.includes(s.n)) { _rt48S.cal.ok++; _rt48Save(); if (_rt48S.cal.ok >= 5) _rt48Badge('cal'); _rt48Ev('econ'); }
    else { _rt48S.sc[sc[0]] = 1; _rt48Save(); if (Object.keys(_rt48S.sc).length >= 10) _rt48Badge('scen10'); _rt48Ev('scen'); } } } catch (e) {}
  return r; }; }
{ const wrapDrill = f => function (i) { const was = !!(_rt47L.a[i] && _rt47L.a[i].done); const r = f.apply(this, arguments); try { const a = _rt47L.a[i]; if (!was && a && a.done && a.ok) _rt48Ev('drill'); } catch (e) {} return r; };
  _rt47Trd = wrapDrill(_rt47Trd); _rt47SupCheck = wrapDrill(_rt47SupCheck); }
{ const _fi8 = _rt47Finish; _rt47Finish = function () { const id = _rt47L.id, d = _rt46Day(), had = !!_rt47S.daily[d], fin0 = _rt47L.fin;
  try { if (!fin0 && id === 'gym') { const st = _rt47Steps(id), dr = st.map((s, k) => [s, k]).filter(([s]) => (s.t === 'chart' && s.k !== 'view') || s.t === 'c2');
    if (dr.length && dr.every(([s, k]) => _rt47L.a[k] && _rt47L.a[k].skip && !_rt47L.a[k].done)) { _rt47L.fin = true; _rt47L.res = { ok: 0, n: 0, need: 0, pass: false }; return; } } } catch (e) {}
  const r = _fi8.apply(this, arguments);
  try { if (!fin0) { if (RT47_LESSONS[id] && _rt47L.res && _rt47L.res.pass) _rt48Ev('lesson'); if (id === 'daily' && !had && _rt47S.daily[d]) _rt48Ev('daily'); if (id === 'week') _rt48Ev('week'); if (id === 'news') { _rt48Ev('news'); _rt48Badge('news'); } } } catch (e) {}
  return r; }; }

try { const st = document.createElement('style'); st.id = 'rt48css'; st.textContent = `
.rt48-hub{margin:0 0 24px;min-width:0}
.rt48-hubh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}
.rt48-fresh{font-family:var(--mn);font-size:11px;color:var(--t3);letter-spacing:.04em}.rt48-fresh.in{margin:-4px 0 10px;color:var(--gd)}
.rt48-week{background:linear-gradient(135deg,rgba(217,174,82,.10),rgba(217,174,82,.02));border:1px solid rgba(217,174,82,.35);border-radius:14px;padding:14px 16px;margin:6px 0 12px}
.rt48-week.done{border-color:rgba(111,191,149,.45);background:rgba(111,191,149,.07)}
.rt48-week p{font-size:13.5px;color:var(--t2);margin:6px 0 8px;line-height:1.45}
.rt48-wl{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.rt48-wl li{display:grid;grid-template-columns:1fr auto;gap:2px 10px;font-size:13.5px;color:var(--tx);min-width:0}
.rt48-wl li .rt47-lvbar{grid-column:1/-1}.rt48-wl li.ok span:first-child{color:var(--gn)}
.rt48-wn{font-family:var(--mn);font-size:12px;color:var(--t2)}
.rt48-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;min-width:0}
.rt48-card{position:relative;display:flex;flex-direction:column;align-items:flex-start;gap:5px;text-align:left;min-width:0;padding:14px 13px 12px;border-radius:14px;border:1px solid var(--gb);background:var(--b2);color:var(--tx);font-family:var(--sn);cursor:pointer;transition:border-color .12s,transform .12s}
.rt48-card:hover{border-color:var(--gd);transform:translateY(-1px)}.rt48-card:focus-visible{outline:2px solid var(--tx);outline-offset:2px}
.rt48-ci{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:rgba(217,174,82,.12);color:var(--gd)}.rt48-ci .rt47-ic{width:19px;height:19px}
.rt48-auto{position:absolute;top:12px;right:10px;font-family:var(--mn);font-size:9.5px;letter-spacing:.12em;color:#14151A;background:var(--gd);border-radius:5px;padding:2px 5px;font-weight:700}
.rt48-ct{font-size:15px;font-weight:800;line-height:1.25}
.rt48-cd{font-size:12.5px;color:var(--t2);line-height:1.4;flex:1}
.rt48-cm{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:11.5px;color:var(--t3);font-family:var(--mn)}
.rt48-cs{font-size:11.5px;color:var(--gd);font-weight:700;min-height:14px;overflow-wrap:anywhere}
.rt48-bdw{margin-top:14px}
.rt48-act{max-width:760px;margin:0 auto;min-width:0}
.rt48-act .rt47-ptop{display:flex;align-items:center;gap:10px;margin:0 0 12px}
.rt48-h{flex:1;min-width:0;display:flex;align-items:center;gap:8px;font-family:var(--sf);font-size:22px;font-weight:700;margin:0;color:var(--tx);outline:none;border:0;padding:0;line-height:1.2}
.rt48-h .rt47-ic{width:22px;height:22px;color:var(--gd);flex:0 0 auto}
.rt48-body{background:var(--b2);border:1px solid var(--gb);border-radius:18px;padding:18px 16px;min-width:0}
.rt48-intro .rt47-cta{margin-top:6px}
.rt48-facts{margin:0 0 14px;padding-left:18px;color:var(--t2);font-size:14px;line-height:1.7}
.rt48-sphud{display:grid;grid-template-columns:auto 1fr auto auto;align-items:center;gap:10px;margin:0 0 12px}
.rt48-sphud .rt47-bar{display:block;height:8px;border-radius:99px;background:var(--b3);overflow:hidden}.rt48-sphud .rt47-bar i{display:block;height:100%;background:var(--gd);transition:width .2s linear}
.rt48-spt{font-family:var(--mn);font-size:20px;font-weight:700;color:var(--gd);min-width:42px}
.rt48-sps{font-family:var(--mn);font-size:14px;font-weight:700}
.rt48-combo{font-family:var(--mn);font-size:13px;font-weight:800;padding:3px 8px;border-radius:8px;background:var(--b3);color:var(--t2)}.rt48-combo.on{background:var(--gd);color:#14151A}
.rt48-spq{min-height:0;padding:16px 14px}
.rt48-q:focus{outline:none}.rt48-q{font-family:var(--sn);font-size:18px;font-weight:700;line-height:1.4;margin:6px 0 10px;color:var(--tx);border:0;padding:0;overflow-wrap:anywhere}
.rt48-key{flex:0 0 22px;height:22px;border-radius:6px;display:grid;place-items:center;background:var(--b3);font-family:var(--mn);font-size:12px;color:var(--t2)}
.rt48-spfb{min-height:22px;margin-top:10px;font-weight:700;font-size:14px}.rt48-spfb.ok{color:var(--gn)}.rt48-spfb.no{color:var(--gd)}
.rt48-res{text-align:center;outline:none}.rt48-res .rt47-endbtns{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:12px}
.rt48-banner{font-size:13px;line-height:1.5;background:rgba(217,174,82,.10);border:1px solid rgba(217,174,82,.45);border-radius:10px;padding:9px 12px;margin:0 0 12px;color:var(--tx)}.rt48-banner b{color:var(--gd)}
.rt48-pthead{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0 0 14px}
.rt48-pthead>div{background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:9px 11px;display:flex;flex-direction:column;gap:2px;min-width:0}
.rt48-pthead b{font-size:17px;font-weight:800;font-family:var(--mn);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rt48-act .up{color:var(--gn)}.rt48-act .dn{color:var(--rd)}
.rt48-ptgrid{display:grid;gap:18px;min-width:0}
.rt48-ptform,.rt48-ptside{min-width:0}
.rt48-assets{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:6px;margin:6px 0 8px}
.rt48-assets button{display:flex;flex-direction:column;align-items:flex-start;gap:1px;min-height:58px;padding:7px 9px;border-radius:10px;border:1.5px solid var(--gb);background:var(--b1);color:var(--tx);font-family:var(--sn);font-size:13px;font-weight:700;cursor:pointer;min-width:0;text-align:left}
.rt48-assets button.on{border-color:var(--gd);background:rgba(217,174,82,.10)}.rt48-assets button.shut{opacity:.7}
.rt48-apx{font-family:var(--mn);font-size:11.5px;color:var(--t2);font-weight:500;overflow-wrap:anywhere}
.rt48-ast{font-family:var(--mn);font-size:9.5px;letter-spacing:.1em;color:var(--t3)}.rt48-ast.on{color:var(--gn)}
.rt48-sess{font-size:12.5px;margin:0 0 10px;line-height:1.45}.rt48-sess.ok{color:var(--gn)}.rt48-sess.no{color:var(--t2)}
.rt48-lab{display:block;font-size:12.5px;font-weight:700;color:var(--tx);margin:10px 0 5px}.rt48-lab span{font-weight:400;color:var(--t3)}
.rt48-seg{display:flex;flex-wrap:wrap;gap:6px}
.rt48-seg button{min-height:40px;padding:0 13px;border-radius:9px;border:1.5px solid var(--gb);background:var(--b1);color:var(--tx);font-family:var(--sn);font-size:13.5px;font-weight:700;cursor:pointer}
.rt48-seg button.on{border-color:var(--gd);background:rgba(217,174,82,.14);color:var(--gd)}
.rt48-seg button:focus-visible,.rt48-assets button:focus-visible,.rt48-mc:focus-visible{outline:2px solid var(--tx);outline-offset:2px}
.rt48-calc{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:12px 0 4px}
.rt48-calc div{background:var(--b1);border-radius:10px;padding:8px 9px;display:flex;flex-direction:column;gap:2px;min-width:0}.rt48-calc span{font-size:11px;color:var(--t3)}.rt48-calc b{font-family:var(--mn);font-size:13.5px;overflow-wrap:anywhere}
.rt48-ptform .rt47-cta{width:100%;margin-top:8px;white-space:normal}.rt48-ptform .rt47-cta[aria-disabled=true],.rt47-btn[aria-disabled=true]{opacity:.5;cursor:not-allowed}
.rt48-msg{min-height:20px;font-size:13.5px;margin-top:8px;color:var(--t2);line-height:1.45}.rt48-msg.ok{color:var(--gn)}
.rt48-cnt{font-family:var(--mn);font-size:13px;color:var(--t3);font-weight:500}
.rt48-pos,.rt48-hist,.rt48-lb,.rt48-prl,.rt48-recap{list-style:none;margin:6px 0 14px;padding:0;display:grid;gap:8px}
.rt48-pos li{background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:10px 12px;display:grid;gap:4px}
.rt48-pr{display:flex;justify-content:space-between;gap:8px;font-size:14px}.rt48-pnl{font-family:var(--mn);font-weight:700}
.rt48-pm{font-size:12px;color:var(--t2);line-height:1.45;overflow-wrap:anywhere}
.rt47-btn.sm{min-height:36px;padding:0 12px;font-size:13px;justify-self:start}
.rt48-hist li,.rt48-lb li{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;color:var(--t2);border-bottom:1px solid var(--gb);padding-bottom:6px}.rt48-hist b,.rt48-lb b{font-family:var(--mn)}
.rt48-lb{counter-reset:lb}.rt48-lb li span::before{counter-increment:lb;content:counter(lb) ". ";color:var(--gd);font-weight:700}
.rt48-why{margin-top:14px;font-size:13.5px;color:var(--t2)}.rt48-why summary{cursor:pointer;color:var(--tx);font-weight:700;min-height:32px}.rt48-why p{line-height:1.55}
.rt48-mhud{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;font-size:13px;color:var(--t2);margin:0 0 12px}.rt48-mhud b{font-family:var(--mn);font-size:17px;color:var(--gd)}.rt48-mhud .rt47-ic{width:15px;height:15px;color:var(--gd);vertical-align:-2px}
.rt48-match{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.4fr);gap:8px}
.rt48-mcol{display:grid;gap:8px;align-content:start;min-width:0}
.rt48-mc{min-height:52px;padding:9px 11px;border-radius:11px;border:1.5px solid var(--gb);background:var(--b1);color:var(--tx);font-family:var(--sn);font-size:13px;line-height:1.35;text-align:left;cursor:pointer;min-width:0;overflow-wrap:anywhere}
.rt48-mc.l{font-weight:800;font-size:13.5px}.rt48-mc.sel{border-color:var(--gd);background:rgba(217,174,82,.16);box-shadow:0 0 0 2px rgba(217,174,82,.25)}
.rt48-mc.ok{border-color:rgba(111,191,149,.6);background:rgba(111,191,149,.10);color:var(--t2);cursor:default}.rt48-mc.ok b{color:var(--gn)}
.rt48-mc.no{border-color:var(--rd);animation:rt48shake .3s}
.rt48-recap{text-align:left;font-size:13px;color:var(--t2);line-height:1.5}.rt48-recap b{color:var(--tx);margin-right:4px}
@keyframes rt48shake{0%,100%{transform:none}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
.rt48-prf{display:grid;gap:10px}
.rt48-prrow{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,150px);gap:10px;align-items:center;background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:10px 12px}
.rt48-prrow label{display:flex;flex-direction:column;gap:2px;font-size:14px;min-width:0}.rt48-prrow label span{font-size:11.5px;color:var(--t3)}
.rt48-prrow input{width:100%;min-height:44px;border-radius:9px;border:1.5px solid var(--gb);background:var(--b2);color:var(--tx);font-family:var(--mn);font-size:16px;padding:0 10px}.rt48-prrow input:focus{outline:2px solid var(--gd);outline-offset:1px}
.rt48-prl{text-align:left}.rt48-prl li{background:var(--b1);border:1px solid var(--gb);border-radius:12px;padding:10px 12px;display:grid;gap:4px;font-size:14px}
.rt48-prh{display:flex;justify-content:space-between;gap:8px}.rt48-psc{font-family:var(--mn);font-weight:800}.rt48-psc.ok{color:var(--gn)}.rt48-psc.mid{color:var(--gd)}.rt48-psc.no{color:var(--rd)}
.rt48-src{font-size:12px;color:var(--t3);margin:-4px 0 10px;line-height:1.5;overflow-wrap:anywhere}.rt48-src a{color:var(--gd)}
.rt48-c2o{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
@media (min-width:900px){.rt48-ptgrid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
@media (max-width:767px){.rt48-act{padding-bottom:24px}.rt48-body{padding:14px 12px;border-radius:14px}.rt48-h{font-size:19px}.rt48-match{grid-template-columns:minmax(0,1fr) minmax(0,1.5fr)}.rt48-mc{font-size:12.5px;padding:8px 9px}.rt48-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.rt48-pthead b{font-size:14px}.rt48-pthead>div{padding:8px 9px}}
@media (prefers-reduced-motion:reduce){.rt48-card,.rt48-mc,.rt48-sphud .rt47-bar i{transition:none!important;animation:none!important}}
.rt47-rm .rt48-mc.no,.rt47-rm .rt48-card{animation:none!important;transition:none!important}
`; document.head.appendChild(st); } catch (e) {}

'''
s = s.rstrip('\n') + '\n' + BLOCK
h = h.replace('app.js?v=' + base + '"', 'app.js?v=' + nxt + '"')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt48: block appended + index ' + base + '->' + nxt + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
