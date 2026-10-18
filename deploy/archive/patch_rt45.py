#!/usr/bin/env python3
"""patch_rt45.py: chat43 -> chat44 (client). Stacks on rt44 output (app.js 792a473f).
Learn upgrade: "Start here" tab with 10 plain-English guides (markets table labels, gold & macro, oil/EIA gap, FX,
crypto, stocks/ETFs/indices, charts, risk & position sizing, data releases, using The Dispatch); searchable glossary
(82 terms, topic chips, deep links /learn/?term=); shareable URLs /learn/?guide= and /learn/?tab=; tappable glossary
terms inside lessons; (i) "what's this?" tips on instrument detail labels; one "Labels" help entry on Markets.
No nav changes (Learn already in desktop sidebar + phone More). No server dependency.
Usage: python3 patch_rt45.py [--check] <dir containing app.js and index.html>"""
import sys, os, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')
def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt45 ──' in s: die('rt45 already applied')
if '// ── rt44 ──' not in s: die('base is not rt44 output')
if 'app.js?v=chat43' not in h: die('index.html is not chat43')
for need in ['function renderLearn(', 'const LEARN_MODULES = {', 'function renderLearnArticle(', 'function renderMkt(', 'function _refreshView(', 'function nav(', 'let _learnTab', 'function _escHtml(']:
    if need not in s: die('missing ' + need)
# optional source edit: Learn intel card headline names the tab properly ("Learn · beginner guides" not "Learn · start frameworks")
EDITS = [
 ('*The August 2024 yen carry unwind caused a 12% drop in the S&P in 3 days — a reminder of how FX dynamics can overwhelm equity fundamentals.*',
  '*In the August 2024 yen carry unwind, Japan\'s Nikkei 225 fell about 12% in a single day (5 August), a reminder of how FX dynamics can overwhelm equity fundamentals.*'),
 ('insight = _learnSub ? `Reading: ${_learnSub}.`',
  'insight = _learnSub ? `Reading: ${(Object.values(LEARN_MODULES).flat().find(x => x && x.id === _learnSub) || { title: _learnSub }).title}.`'),
 ('headline = `Learn · ${_learnTab} frameworks`;',
  'headline = `Learn · ${({ start: "beginner guides", glossary: "glossary" })[_learnTab] || _learnTab + " frameworks"}`;'),
 ('`${(LEARN_MODULES[_learnTab] || []).length || Object.values(LEARN_MODULES).reduce((n, v) => n + (Array.isArray(v) ? v.length : 0), 0)} lessons on professional analysis methods.`',
  '(_learnTab === "glossary" ? "Plain-English definitions of the terms used across The Dispatch." : _learnTab === "start" ? `${(LEARN_MODULES.start || []).length} plain-English guides for beginners and improvers.` : `${(LEARN_MODULES[_learnTab] || []).length || Object.values(LEARN_MODULES).reduce((n, v) => n + (Array.isArray(v) ? v.length : 0), 0)} lessons on professional analysis methods.`)'),
]
for old, new in EDITS:
    n = s.count(old)
    if n == 1: s = s.replace(old, new); print('edit ok:', old[:48])
    else: print('edit skipped (%d matches): %s' % (n, old[:48]))
BLOCK = r'''// ── rt45 ──
// 1: beginner-to-intermediate guides ("Start here" tab), rendered by the existing Learn article renderer
const RT45_GUIDES = [
{
  id:'start-markets-table', level:'BEGINNER', mins:6, tag:'START HERE', tagCol:'var(--gd)',
  title:'How to Read the Markets Table',
  summary:'What LIVE, DELAYED, SPOT, CLOSED and the other labels mean, why a price can be minutes old, and how futures, spot and pre-market prices differ.',
  content:`
## Every price comes with a label

Each row on [[go:mkt=Markets]] shows a price, the change on the day, a status label and a short line saying where the price came from and when it was last updated. The label tells you how fresh the number is. Read it before you read the price.

| Label | What it means |
| LIVE | Streamed or polled in real time from a free public feed. Usually seconds old. |
| LIVE·CB / LIVE·KR | Streamed live from Coinbase or Kraken (crypto). |
| LIVE·YS | Streamed from a free Yahoo Finance feed and less than a minute behind. |
| DELAYED 10m | The source itself is delayed, for example CME and ICE futures, which free feeds show 10 minutes late. |
| DELAYED·CG / ·FH | A delayed snapshot from CoinGecko or Finnhub. |
| SPOT | A spot (cash) price rather than a futures contract. |
| SPOT PROXY | A free reference spot price, such as gold from gold-api.com. Close to the market, but not an exchange feed. |
| CLOSED | That venue is shut. You are seeing the last close, and the time shown is when it closed. |
| STALE | The venue is open but the feed has not updated recently. Treat the price with caution. |
| CACHED | The last confirmed value, kept while the feed reconnects. |
| UNAVAILABLE / NO SYNC | No trustworthy price right now. The site shows a dash rather than guess. |

---

## Each market has its own hours

The Dispatch covers crypto, commodities, currencies and stocks around the world, so there is never one "market closed" switch. Crypto trades all day, every day. Currencies trade from Sunday evening to Friday evening (UK time). US stocks have a regular session from 09:30 to 16:00 New York time, which is usually 14:30 to 21:00 in the UK. CME energy and metals futures pause for an hour every weekday evening (22:00 to 23:00 UK time for most of the year).

That is why one row can say LIVE while the row below it says CLOSED. Both are correct.

*The counter at the top, for example "212 prices · 25 live", tells you how many instruments have a synced price and how many of those are updating in real time right now.*

---

## Spot, futures and official reference prices

- **Spot** is the price for delivery now. Gold and silver spot trade almost around the clock.
- **Futures** are contracts to buy or sell at a set price on a future date. Oil and many commodities are mostly traded through futures, so the headline "oil price" is usually the nearest futures contract.
- **Official reference prices**, such as the US Energy Information Administration (EIA) daily spot price shown under WTI and Brent, are published once a day, a few days after the date they cover. They are a useful anchor, not a live quote.

Spot and futures prices for the same commodity can differ, sometimes by a lot. See [[guide:start-oil=Oil: WTI, Brent and the EIA gap]] for why.

---

## Pre-market and after-hours

Many US shares trade before the opening bell (pre-market, from as early as 04:00 New York time) and after the close (after-hours, to 20:00). Where available, The Dispatch shows these as a separate line under the regular price.

- Volume outside regular hours is thin, so prices can jump around and the gap between buying and selling prices (the [[g:spread=spread]]) is wider.
- A big pre-market move often shrinks or grows once the full market opens. Treat it as an early signal, not a settled price.

---

## Reading the change column

- **Chg%** is the move since the previous close for that venue. For crypto it is usually a rolling 24 hours.
- On a Monday morning a stock still shows Friday's move until US trading opens.
- A large move with a STALE or CLOSED label may simply be yesterday's story.

**Quick checklist before you act on a price**
- What does the label say: LIVE, DELAYED or CLOSED?
- When was it last updated?
- Is this spot, futures or an official reference price?
- Is the venue in its regular session, pre-market or closed?
  `
},
{
  id:'start-gold-macro', level:'BEGINNER', mins:8, tag:'MACRO BASICS', tagCol:'var(--gd)',
  title:'Gold and Macro Basics: Why Gold Moves',
  summary:'Real yields, the dollar, central banks and inflation: the handful of forces that explain most big moves in gold.',
  content:`
## What gold is, in market terms

Gold is priced in US dollars per [[g:troy-ounce=troy ounce]] (31.1 grams). It pays no interest or dividend, it cannot be printed, and central banks hold it as a reserve. That mix means it behaves partly like a commodity, partly like a currency and partly like insurance.

You will see it quoted as **XAU/USD** (spot gold) and **GC** (COMEX gold futures). In London, the LBMA Gold Price is set twice each business day and is widely used as a benchmark.

---

## Force 1: real yields

A [[g:real-yield=real yield]] is the interest rate on a bond after expected inflation. The most watched measure is the yield on 10-year US inflation-protected bonds (TIPS).

- When real yields rise, holding gold costs you more in interest you could have earned elsewhere, which tends to weigh on gold.
- When real yields fall, or turn negative, that cost shrinks and gold tends to benefit.

*This link is strong over long periods but not fixed. In recent years gold has at times risen alongside higher real yields, a period when heavy central-bank buying was a big part of demand.*

---

## Force 2: the US dollar

Because gold is priced in dollars, a stronger dollar makes it more expensive for buyers using other currencies, and a weaker dollar makes it cheaper. Gold and the [[g:dxy=dollar index (DXY)]] often move in opposite directions, though not every day.

The DXY measures the dollar against six currencies: euro (about 58%), yen, pound, Canadian dollar, Swedish krona and Swiss franc. The Dispatch calculates it in your browser from those six live currency pairs.

---

## Force 3: the Federal Reserve and other central banks

The Federal Reserve sets the [[g:fed-funds=federal funds rate]] and has two goals: maximum employment and stable prices (a 2% inflation target). The Bank of England and the European Central Bank also target 2% inflation.

- Signs of rate cuts usually push real yields and the dollar lower, which tends to help gold.
- Signs of more hikes, or rates staying high for longer, tend to do the opposite.
- Markets move on expectations, so the surprise matters more than the decision itself.

Central banks also buy and sell gold for their reserves. Large, steady official buying can support prices even when rates are high.

---

## Force 4: inflation and fear

- [[g:inflation=Inflation]] erodes cash. Gold has a long record as a store of value, though over months and years its link to inflation figures is loose.
- In shocks, such as wars, banking stress or market crashes, investors often buy gold as a [[g:safe-haven=safe haven]]. These moves can be fast and can reverse when the fear fades.

---

## Putting it together

| Driver | Usually good for gold | Usually bad for gold |
| Real yields | Falling | Rising |
| US dollar | Weaker | Stronger |
| Fed outlook | Cuts expected | Hikes or higher for longer |
| Risk mood | Fear, shocks | Calm, strong risk appetite |
| Official demand | Central banks buying | Central banks selling |

These are tendencies, not rules. More than one force is always at work, and the strongest one wins.

**Where to look on The Dispatch**
- [[go:gold=Gold Desk]] for structure, levels and the macro backdrop.
- [[go:playbook=Weekly Playbook]] for conditional scenarios and invalidation levels.
- [[go:sig=Signals]] and the regime card for the wider risk mood.
- For deeper reading, try [[guide:regime-framework=The Four Macro Regimes]] and [[guide:rate-cycles=Central Bank Cycle Analysis]].
  `
},
{
  id:'start-oil', level:'BEGINNER', mins:6, tag:'COMMODITIES', tagCol:'var(--bl)',
  title:'Oil: WTI, Brent and the EIA Gap',
  summary:'Why there are two oil prices, what the official EIA spot price is, and why it can sit far from the futures price you see in the table.',
  content:`
## Two benchmarks

| Benchmark | What it is | Where it trades |
| WTI | West Texas Intermediate, a light US crude delivered at Cushing, Oklahoma | NYMEX (CME Group) futures |
| Brent | A blend of North Sea crudes, the main global benchmark | ICE Futures Europe |

Both are priced in US dollars per [[g:barrel=barrel]] (42 US gallons, about 159 litres). Brent usually trades above WTI because it is easier to ship around the world, but the gap changes with shipping costs, US output and local storage.

---

## The price in the table is a futures price

When people say "oil is at $X", they almost always mean the nearest futures contract. On The Dispatch, WTI and Brent come from CME and ICE futures, which free sources show **10 minutes delayed**. No free source offers live CME or ICE prices, so the label says DELAYED 10m rather than pretend otherwise.

Futures stop trading for an hour each weekday evening (22:00 to 23:00 UK time for most of the year) and close for the weekend.

---

## The official EIA spot line

Under WTI and Brent you will see a line such as "Official spot (EIA) $X · as of DATE". This comes from the US Energy Information Administration, a government statistics agency.

- It is a **daily** figure for physical crude, published a few days after the date it covers.
- It is free and authoritative, which makes it a good reference.
- It is **not** a live price. Always check the date next to it.

---

## Why the EIA price and the futures price can differ

It is normal for the two to disagree, sometimes by several dollars, and occasionally by much more when supply is tight.

- **Different timing.** The EIA figure is for a past day. Futures are for now.
- **Different delivery date.** Spot is for oil delivered soon. The futures price in the table is for a contract that delivers in a later month.
- **Tight markets.** When buyers need oil urgently, physical barrels trade well above later-dated contracts. This is called [[g:backwardation=backwardation]]. When supply is plentiful, the reverse ([[g:contango=contango]]) is common.
- **Different assessments.** The EIA's Brent figure tracks physical North Sea cargoes, which is not the same thing as the ICE Brent futures contract.

*A large gap between the EIA line and the futures price is information, not a bug: it usually tells you how tight the physical market is.*

---

## What moves oil

- **Supply:** OPEC+ production decisions, US shale output, outages and sanctions.
- **Demand:** global growth, especially China, the US and Europe, plus the seasons (summer driving, winter heating).
- **Stocks:** the EIA's weekly petroleum status report on US inventories, usually out on Wednesdays.
- **Geopolitics:** risks to key routes such as the Strait of Hormuz. See [[go:geo=Geo Risk]] for chokepoints.
- **The dollar:** like gold, oil is priced in dollars.
  `
},
{
  id:'start-fx', level:'BEGINNER', mins:5, tag:'CURRENCIES', tagCol:'var(--bl)',
  title:'FX Basics: How Currency Pairs Work',
  summary:'Base and quote currencies, pips, spreads, trading hours and what actually moves exchange rates.',
  content:`
## Reading a currency pair

Currencies are always quoted in pairs. In **EUR/USD 1.0850**, the euro is the base currency and the dollar is the quote currency: one euro costs 1.0850 dollars.

- If EUR/USD rises, the euro is strengthening against the dollar.
- **GBP/USD** (often called "cable") shows dollars per pound. **USD/JPY** shows yen per dollar, so a rise there means a stronger dollar.

---

## Pips, spreads and lots

- A [[g:pip=pip]] is the standard small step: 0.0001 for most pairs and 0.01 for yen pairs. EUR/USD moving from 1.0850 to 1.0870 is 20 pips.
- The [[g:spread=spread]] is the gap between the buying (ask) and selling (bid) price. It is the hidden cost of every trade and widens when markets are quiet or stressed.
- A standard lot is 100,000 units of the base currency. Most retail platforms also offer smaller sizes.

---

## When FX trades

The currency market has no single exchange. It trades around the clock from about 22:00 UK time on Sunday to about 22:00 on Friday, passing from Sydney and Tokyo to London and then New York. The London and New York overlap (roughly 13:00 to 17:00 UK time) is usually the busiest period.

---

## What moves exchange rates

- **Interest rates.** Higher rates, or expectations of higher rates, tend to attract money into a currency.
- **Growth and inflation data.** Strong data can lift a currency by changing rate expectations.
- **Risk mood.** In stress, money often flows to the US dollar, Japanese yen and Swiss franc.
- **Trade and politics.** Elections, budgets and trade disputes can move a currency sharply.

*The US dollar sits on one side of the large majority of all currency trades, which is why the dollar index (DXY) matters for almost every market.*

**On The Dispatch**
- Major pairs show LIVE when the free feed is streaming.
- The DXY is calculated from six live pairs. See [[g:dxy=dollar index]] in the glossary.
- For how currencies affect share prices, read [[guide:fx-framework=Currency Analysis for Equities Investors]].
  `
},
{
  id:'start-crypto', level:'BEGINNER', mins:6, tag:'CRYPTO', tagCol:'var(--pu)',
  title:'Crypto Basics: Bitcoin, Ether and the Risks',
  summary:'What Bitcoin and Ether are, why crypto trades 24/7, what stablecoins do, and the risks to understand before you put money in.',
  content:`
## The two big ones

- **Bitcoin (BTC)** is a digital asset with a fixed maximum supply of 21 million coins. New coins are created at a rate that halves roughly every four years (the [[g:halving=halving]]); the most recent was in April 2024.
- **Ether (ETH)** is the native asset of the Ethereum network, which runs applications and smart contracts. Since 2022 Ethereum has used proof of stake rather than mining.

Bitcoin's share of the total crypto market is called [[g:btc-dominance=Bitcoin dominance]]. When it rises, money is usually concentrating in Bitcoin rather than smaller coins.

---

## How crypto trades

- Crypto trades 24 hours a day, 7 days a week, on many exchanges at once. There is no closing price, so daily change is usually measured over a rolling 24 hours.
- Prices on different exchanges are close but not identical.
- On The Dispatch, Bitcoin often shows LIVE·CB, meaning a live price streamed from Coinbase straight into your browser.

---

## Stablecoins

[[g:stablecoin=Stablecoins]] such as USDT and USDC aim to stay worth one US dollar, usually backed by cash and short-term government bonds. They are used to move money between exchanges and to park funds without leaving crypto. A peg can fail, and some smaller stablecoins have collapsed.

---

## Risks to understand first

- **Volatility.** Moves of 5% or more in a day are common, and falls of more than 50% from a peak have happened several times.
- **Protection.** In the UK most crypto investments are not covered by the Financial Services Compensation Scheme or the Financial Ombudsman Service.
- **Exchange and custody risk.** If an exchange fails or is hacked, you may lose what you hold there.
- **Scams.** Fake apps, "guaranteed returns" and social-media investment schemes are widespread.
- **Leverage.** Selling crypto derivatives to UK retail customers has been banned by the FCA since January 2021. Offshore platforms that offer high leverage carry extra risk.

*The FCA's standard warning applies: don't invest unless you are prepared to lose all the money you invest.*

**On The Dispatch:** the [[go:crypto=Crypto]] page ranks the top 50 coins by market value with Bitcoin and Ether dominance and 24-hour moves.
  `
},
{
  id:'start-stocks', level:'BEGINNER', mins:7, tag:'STOCKS', tagCol:'var(--gn)',
  title:'Stocks, ETFs and Indices',
  summary:'What a share is, how indices like the S&P 500 and FTSE 100 work, what ETFs such as SPY and QQQ hold, and the numbers worth knowing.',
  content:`
## Shares

A share is a small piece of ownership in a company. Its price moves with expectations about the company's future profits, interest rates and the general mood of the market. Some companies pay part of their profits to shareholders as [[g:dividend=dividends]].

---

## Indices: the market in one number

An [[g:index=index]] tracks a basket of shares.

| Index | What it tracks | How it is weighted |
| S&P 500 | About 500 large US companies | By market value (bigger firms count more) |
| Nasdaq-100 | 100 of the largest non-financial companies listed on Nasdaq | By market value, with caps |
| Dow Jones Industrial Average | 30 large US companies | By share price |
| FTSE 100 | The 100 largest companies on the London Stock Exchange | By market value |
| Nikkei 225 | 225 large Japanese companies | By share price |

Because the S&P 500 and Nasdaq-100 are weighted by size, a handful of the biggest companies can drive much of their daily move.

---

## ETFs

An [[g:etf=exchange-traded fund (ETF)]] is a fund you can buy and sell like a share. Many simply track an index.

- **SPY** tracks the S&P 500.
- **QQQ** tracks the Nasdaq-100.
- **IWM** tracks the Russell 2000 index of smaller US companies.

ETFs give instant spread across many companies, usually at low cost. Check the fund's charges and what it actually holds.

---

## Numbers worth knowing

- **Market cap:** share price times the number of shares, the company's total market value.
- **P/E ratio:** price divided by earnings per share. A high P/E means investors expect strong growth or are paying up.
- **Beta:** how much a share has tended to move compared with the S&P 500. 1.0 means in line with the market; 1.5 means about 50% bigger swings.
- **Volume:** how many shares changed hands. Moves on high volume carry more weight.

All of these are in the [[tab:glossary=glossary]].

---

## Trading hours

- **US:** 09:30 to 16:00 New York time (usually 14:30 to 21:00 UK time), plus pre-market and after-hours sessions.
- **London:** 08:00 to 16:30 UK time.
- **Tokyo:** 09:00 to 15:30 Japan time, with a lunch break.

The US and UK change their clocks on different dates in spring and autumn, so for a couple of weeks a year the US open is an hour earlier in UK time.

**On The Dispatch:** browse [[go:mkt=Markets]], compare sectors on [[go:sectors=Sectors]], see breadth on the [[go:heat=Heatmap]] and filter names with the [[go:scr=Screener]].
  `
},
{
  id:'start-charts', level:'BEGINNER', mins:6, tag:'CHARTS', tagCol:'var(--bl)',
  title:'How to Read a Price Chart',
  summary:'Candlesticks, timeframes, volume, moving averages and the RSI momentum line, using the charts on The Dispatch as the example.',
  content:`
## Candlesticks

Each [[g:candlestick=candlestick]] shows four prices for one period, such as one day or five minutes:

- **Open** and **close** form the thick body.
- **High** and **low** are the thin lines (wicks) above and below.
- A green (or hollow) body means the price closed higher than it opened. Red means it closed lower.

Long wicks show the price was pushed a long way and then rejected. A small body shows indecision.

---

## Timeframes

The buttons above each chart (1D, 5D, 1M, 6M, 1Y, 2Y) change the period shown. Short timeframes show noise and intraday swings; longer ones show the trend. A sensible habit is to start with the longer view and then zoom in.

---

## Volume

The bars along the bottom show how much traded in each period. A price move on rising volume suggests real conviction. A move on very low volume, such as pre-market or holiday trading, is easier to reverse.

---

## Moving averages

A [[g:moving-average=moving average]] smooths the price by averaging recent closes. The Dispatch draws the 20-day (gold line) and 50-day (blue line) averages.

- Price above both, with the 20-day above the 50-day, is a common sign of an uptrend.
- Price below both suggests a downtrend.
- Averages lag the price. They describe the trend; they do not predict it.

---

## RSI: a momentum gauge

The [[g:rsi=Relative Strength Index (RSI)]] under the chart runs from 0 to 100 and compares recent gains with recent losses over 14 periods.

- Above 70 is usually called overbought (the site says "stretched").
- Below 30 is usually called oversold ("washed-out").
- In strong trends RSI can stay above 70 or below 30 for a long time, so it is not a sell or buy signal on its own.

---

## Support and resistance

[[g:support=Support]] is a price area where buying has repeatedly stepped in; [[g:resistance=resistance]] is where selling has. They are zones, not exact lines, and a clean break through one often turns it into the other.

*Charts show what has happened, not what will happen. Use them alongside the macro picture and a clear plan for what would prove you wrong.*

For more, read [[guide:factor-investing=Factor Investing]] and [[guide:market-microstructure=Market Microstructure and Flow Analysis]].
  `
},
{
  id:'start-risk', level:'INTERMEDIATE', mins:7, tag:'RISK', tagCol:'var(--rd)',
  title:'Risk Management and Position Sizing',
  summary:'How to decide how much to put on a trade, where stops fit, why leverage cuts both ways and how losses compound.',
  content:`
## Start with what you can lose

Before asking how much you could make, decide how much of your account you are willing to lose if the idea is wrong. Many traders cap this at a small, fixed share of the account on any single idea, often 1% to 2%. It is a rule of thumb, not a law, but it keeps one bad call from doing lasting damage.

---

## The position-sizing formula

**Position size = amount you are willing to risk ÷ distance to your stop**

*Illustrative example only: a £10,000 account risking 1% is willing to lose £100. If you buy at £50 with a stop at £48, you risk £2 per share, so the position is £100 ÷ £2 = 50 shares (£2,500 of stock).*

Notice that the position (£2,500) is much larger than the risk (£100). The stop, not the size of the position, defines the risk. The [[tab:calc=Calculators]] tab can do this maths for you.

---

## Stops are not guarantees

- A [[g:stop-loss=stop-loss]] order closes a position when a price is reached, but in a fast market it can fill at a worse price ([[g:slippage=slippage]]).
- Prices can [[g:gap=gap]] overnight or over a weekend straight past your stop.
- Set stops where your idea is proven wrong, not at an arbitrary percentage.

---

## Leverage cuts both ways

[[g:leverage=Leverage]] lets you control a large position with a small deposit (margin). Gains and losses are both magnified.

- In the UK, retail CFD and spread-betting leverage is capped by the FCA, for example at 30:1 on major currency pairs, 20:1 on gold and major indices and 5:1 on individual shares.
- CFD providers must publish the share of their retail accounts that lose money. Read that figure before you open an account.

---

## Losses compound against you

| Loss | Gain needed to get back to where you started |
| 10% | 11% |
| 25% | 33% |
| 50% | 100% |
| 75% | 300% |

This is simple arithmetic, and it is why protecting capital matters more than chasing the last few percent of a move. A fall from a peak is called a [[g:drawdown=drawdown]].

---

## Spread your risk

- Several positions that all depend on the same thing (for example, all tech, or all betting on lower rates) are really one big position. See [[g:correlation=correlation]].
- Write down, before you enter, what would make you exit: the price, the event or the date.

**Go further:** [[guide:position-sizing=Professional Position Sizing]] and [[guide:correlation-risk=Correlation, Diversification and Tail Risk]].
  `
},
{
  id:'start-data', level:'INTERMEDIATE', mins:5, tag:'MACRO DATA', tagCol:'var(--gd)',
  title:'Economic Data Releases That Move Markets',
  summary:'Inflation, jobs, growth and central-bank meetings: what each release measures, when it lands and why the surprise matters more than the number.',
  content:`
## Why scheduled data matters

Prices already reflect what the market expects. When a figure comes out, markets react to the gap between the actual number and the forecast (the consensus). A "good" number that was even better expected can still send a market lower.

---

## The big releases

| Release | What it measures | Usual timing (UK time) |
| US CPI | Consumer price inflation | Monthly, 13:30 (08:30 New York) |
| US non-farm payrolls | Jobs added and the unemployment rate | Usually the first Friday of the month, 13:30 |
| US PCE prices | The Fed's preferred inflation measure | Monthly, 13:30 |
| UK CPI | UK consumer price inflation (ONS) | Monthly, 07:00 |
| PMI surveys | Business activity; above 50 means expansion | Around the start of each month |
| GDP | Total economic output | Quarterly, with later revisions |

US release times shift by an hour for a few weeks a year when the US and UK clocks change on different dates.

---

## Central-bank meetings

The Federal Reserve's FOMC and the Bank of England's Monetary Policy Committee each meet eight times a year. Markets watch the rate decision, the statement, the vote split and the press conference for hints about the next move.

---

## How each one tends to hit markets

- **Hotter inflation** than expected: yields and the dollar often rise; gold and growth stocks often fall.
- **Stronger jobs** than expected: similar, because it makes rate cuts less likely.
- **Weak growth or PMIs:** bonds often rally (yields fall); cyclical shares and oil can drop.

*These are typical first reactions. They can reverse within the hour as traders digest the detail.*

**On The Dispatch:** the [[go:brief=Dispatch Brief]] and [[go:playbook=Weekly Playbook]] flag the releases that matter for the week ahead.
  `
},
{
  id:'start-dispatch', level:'BEGINNER', mins:5, tag:'PLATFORM', tagCol:'var(--gd)',
  title:'How to Use The Dispatch',
  summary:'A tour of the tools: the regime score, signals, watchlists, price alerts, Ask, the Lab, the Brief and keyboard shortcuts.',
  content:`
## A good daily routine

- Open the [[go:brief=Dispatch Brief]] for the house view of the day.
- Check the regime score and [[go:sig=Signals]] to see the overall risk mood.
- Scan your [[go:watch=Watchlist]] for anything that has moved.
- Dig into one name or market at a time, with a clear question.

---

## The regime score

The pill at the top, for example "Risk-Off · 37/100", is The Dispatch's read of the overall risk mood. It starts at 50 and moves with the VIX volatility index, the S&P 500's move on the day, the dollar index, oil and Bitcoin.

| Score | Label |
| 72 to 100 | Risk-On (Strong) |
| 55 to 71 | Risk-On (Fragile) |
| 40 to 54 | Transition |
| 0 to 39 | Risk-Off |

It is a model, not a forecast, and it shows "loading" rather than a made-up number when its inputs are missing.

---

## Scores and signals

- **AI Score (0 to 100)** on each instrument combines sentiment, momentum, fundamentals and analyst ratings. It is indicative only.
- **Signals** are conviction-weighted reads across macro, equities, gold and risk appetite. Each one explains what supports or weakens it.
- **Fear/Greed** is an in-house gauge built mainly from the VIX, plus the average move across synced prices.

---

## Watchlists and alerts

- Tap the ★ on any instrument to add it to your watchlist.
- Open an instrument and use the alerts tab to set a price alert above or below the current price.
- Price alerts and the [[go:port=Portfolio]] are stored in your browser, so your positions are not sent to our server. If you are signed in, your watchlist can also be saved to your account settings.

---

## Ask and the Lab

- **Ask** is the research assistant: ask a question about a market, a company or a headline and it answers with context. It is part of Premium. See Pricing for what each plan includes.
- The [[go:lab=Market Lab]] tests a thesis against today's regime: fit score, scenarios, sector rotation and what would invalidate the idea.
- **Compare** puts two instruments side by side.

---

## Keyboard shortcuts (desktop)

| Key | Action |
| / | Focus the search box |
| Ctrl/⌘ + K | Command palette |
| 1 to 4 | Expand a panel |
| F | Focus mode |
| Esc | Close the current panel or overlay |

*Everything on The Dispatch is for research and education. It is not financial advice or a recommendation to buy or sell anything.*
  `
},
];
// 2: searchable glossary (plain British English); "guide" links to the guide that explains the idea in context
const RT45_GLOSS = [
 ['live-price','Live price','Prices & data','A price streamed or polled in real time from a free public feed, usually seconds old. Shown as LIVE, LIVE·CB (Coinbase), LIVE·KR (Kraken) or LIVE·YS (Yahoo stream).','start-markets-table'],
 ['delayed-price','Delayed price','Prices & data','A price the source releases late on purpose, such as CME and ICE futures that free feeds show 10 minutes behind. Shown as DELAYED with the delay where known.','start-markets-table'],
 ['last-close','Last close (CLOSED)','Prices & data','The final price from the most recent session of a venue that is now shut. The time shown is when that venue closed, not when you loaded the page.','start-markets-table'],
 ['stale','Stale price','Prices & data','The venue is open but the feed has not updated recently, so the price may be out of date. Treat it with caution until it refreshes.','start-markets-table'],
 ['spot-proxy','Spot proxy','Prices & data','A free reference spot price (for example gold from gold-api.com) used instead of an exchange feed. Close to the market, but not an official exchange quote.','start-markets-table'],
 ['spot','Spot price','Prices & data','The price for buying or selling something for immediate delivery, as opposed to a futures price for a later date.','start-markets-table'],
 ['futures','Futures contract','Prices & data','An agreement to buy or sell an asset at a set price on a future date. Oil, metals and stock indices are heavily traded through futures, and headline commodity prices are usually the nearest contract.','start-oil'],
 ['pre-market','Pre-market and after-hours','Prices & data','Trading in US shares outside the regular 09:30 to 16:00 New York session. Volume is thin, so prices can be jumpy and spreads wider.','start-markets-table'],
 ['bid-ask','Bid and ask','Prices & data','The bid is the highest price a buyer will pay; the ask (or offer) is the lowest price a seller will accept. You buy at the ask and sell at the bid.','start-fx'],
 ['spread','Spread','Prices & data','The gap between the bid and the ask. It is a cost on every trade and usually widens when markets are quiet, closed or stressed.','start-fx'],
 ['volume','Volume','Prices & data','How many shares, contracts or coins changed hands in a period. Price moves on high volume are generally taken more seriously than moves on thin volume.','start-charts'],
 ['day-range','Day range','Prices & data','The gap between the highest and lowest price of the session. The Dispatch shows it as a percentage of the low, (high − low) ÷ low.','start-charts'],
 ['52-week','52-week high and low','Prices & data','The highest and lowest prices over the past year. Useful for seeing where today\'s price sits within its recent history.','start-stocks'],
 ['eia-spot','Official spot (EIA)','Commodities','The US Energy Information Administration\'s daily spot price for WTI and Brent crude. Authoritative and free, but published a few days after the date it covers, so always check the date.','start-oil'],
 ['wti','WTI crude','Commodities','West Texas Intermediate, a light US crude oil delivered at Cushing, Oklahoma, and the main US oil benchmark. Traded as NYMEX futures.','start-oil'],
 ['brent','Brent crude','Commodities','A blend of North Sea crude oils and the main global oil benchmark. Traded as ICE futures; physical cargoes are assessed separately.','start-oil'],
 ['barrel','Barrel','Commodities','The standard unit for oil: 42 US gallons, about 159 litres. Oil prices are quoted in US dollars per barrel.','start-oil'],
 ['backwardation','Backwardation','Commodities','When near-dated prices are higher than later-dated ones, usually a sign of a tight market where buyers need supply now.','start-oil'],
 ['contango','Contango','Commodities','When later-dated futures are priced above near-dated ones, common when supply is plentiful and storage costs are built into the price.','start-oil'],
 ['opec','OPEC+','Commodities','The Organization of the Petroleum Exporting Countries plus allies such as Russia. Its production decisions are one of the biggest influences on oil prices.','start-oil'],
 ['troy-ounce','Troy ounce','Commodities','The unit used for precious metals: 31.1035 grams, slightly heavier than an ordinary ounce. Gold and silver are quoted in dollars per troy ounce.','start-gold-macro'],
 ['xau','XAU/USD','Commodities','The code for spot gold priced in US dollars per troy ounce. XAG/USD is the same for silver.','start-gold-macro'],
 ['safe-haven','Safe haven','Macro','An asset investors tend to buy in times of stress, such as gold, US Treasuries, the US dollar, the Japanese yen or the Swiss franc. The effect is not guaranteed.','start-gold-macro'],
 ['inflation','Inflation','Macro','The rate at which prices in an economy are rising, usually measured by the Consumer Price Index (CPI). Most major central banks target 2% a year.','start-data'],
 ['cpi','CPI','Macro','The Consumer Price Index, which tracks the price of a typical basket of goods and services. Published monthly in the US by the BLS and in the UK by the ONS.','start-data'],
 ['pce','PCE prices','Macro','Personal Consumption Expenditures prices, the US inflation measure the Federal Reserve targets at 2%.','start-data'],
 ['nfp','Non-farm payrolls','Macro','The monthly US jobs report showing how many jobs were added outside farming, plus the unemployment rate. Usually released on the first Friday of the month.','start-data'],
 ['pmi','PMI','Macro','Purchasing Managers\' Index, a monthly business survey. Above 50 suggests activity is expanding; below 50 suggests it is shrinking.','start-data'],
 ['gdp','GDP','Macro','Gross Domestic Product, the total value of goods and services an economy produces. Two quarters of falling GDP is a common rule-of-thumb definition of recession.','start-data'],
 ['fed-funds','Federal funds rate','Macro','The Federal Reserve\'s main policy interest rate, set as a target range by the FOMC. It influences borrowing costs, the dollar and asset prices worldwide.','start-gold-macro'],
 ['fomc','FOMC','Macro','The Federal Open Market Committee, the Fed group that sets US interest rates. It meets eight times a year.','start-data'],
 ['boe','Bank Rate (Bank of England)','Macro','The Bank of England\'s policy interest rate, set by its Monetary Policy Committee, which meets eight times a year and targets 2% CPI inflation.','start-data'],
 ['hawkish-dovish','Hawkish and dovish','Macro','Hawkish means leaning towards higher interest rates to fight inflation; dovish means leaning towards lower rates to support growth and jobs.','start-gold-macro'],
 ['bond-yield','Bond yield','Macro','The return a bond pays as a percentage of its price. When bond prices fall, yields rise, and the reverse. The US 10-year yield is a key global benchmark.','start-gold-macro'],
 ['real-yield','Real yield','Macro','A bond yield after expected inflation, often measured by the 10-year US TIPS yield. Rising real yields tend to weigh on gold and expensive growth stocks.','start-gold-macro'],
 ['tips','TIPS','Macro','Treasury Inflation-Protected Securities, US government bonds whose value is adjusted for inflation. Their yield is the market\'s real yield.','start-gold-macro'],
 ['breakeven','Breakeven inflation','Macro','The gap between a normal Treasury yield and the TIPS yield of the same maturity: the inflation rate the bond market is pricing in.','start-gold-macro'],
 ['yield-curve','Yield curve','Macro','A line showing bond yields from short to long maturities. When short-term yields are above long-term ones (an inverted curve), markets often expect slower growth ahead.','regime-framework'],
 ['qe-qt','QE and QT','Macro','Quantitative easing is a central bank buying bonds to push long-term rates down; quantitative tightening is the reverse, shrinking its balance sheet.','rate-cycles'],
 ['recession','Recession','Macro','A significant, broad decline in economic activity lasting more than a few months. Markets often start pricing it in well before it is officially declared.','regime-framework'],
 ['stagflation','Stagflation','Macro','Weak growth combined with high inflation, a difficult mix for both shares and bonds.','regime-framework'],
 ['risk-on-off','Risk-on and risk-off','Macro','Risk-on is when investors favour shares, high-yield credit and crypto; risk-off is when they move to cash, government bonds, gold and safe-haven currencies.','start-dispatch'],
 ['vix','VIX','Macro','A measure of expected volatility in the S&P 500 over the next 30 days, derived from options prices. Often called the "fear gauge": higher readings mean more expected turbulence.','start-dispatch'],
 ['dxy','Dollar index (DXY)','FX','The US dollar measured against six currencies: euro (about 58%), yen, pound, Canadian dollar, Swedish krona and Swiss franc. The Dispatch calculates it from those six live pairs.','start-gold-macro'],
 ['currency-pair','Currency pair','FX','Two currencies quoted against each other, such as EUR/USD. The first is the base currency; the price tells you how much of the second it costs to buy one unit of the first.','start-fx'],
 ['pip','Pip','FX','The standard small price step in currencies: 0.0001 for most pairs and 0.01 for pairs involving the Japanese yen.','start-fx'],
 ['cable','Cable','FX','Market nickname for GBP/USD, the pound against the dollar, dating from the transatlantic telegraph cable.','start-fx'],
 ['carry-trade','Carry trade','FX','Borrowing in a low-interest currency to hold a higher-interest one and earn the difference. It can unwind violently when markets turn.','start-fx'],
 ['bitcoin','Bitcoin (BTC)','Crypto','The first and largest cryptocurrency, with a fixed maximum supply of 21 million coins.','start-crypto'],
 ['ether','Ether (ETH)','Crypto','The native asset of the Ethereum network, which runs smart contracts and decentralised applications.','start-crypto'],
 ['stablecoin','Stablecoin','Crypto','A crypto token designed to hold a steady value, usually one US dollar, such as USDT or USDC. Pegs can and sometimes do fail.','start-crypto'],
 ['halving','Halving','Crypto','The point, roughly every four years, when the number of new bitcoins created per block is cut in half. The most recent was in April 2024.','start-crypto'],
 ['btc-dominance','Bitcoin dominance','Crypto','Bitcoin\'s share of the total value of all cryptocurrencies. A rising share usually means money is concentrating in Bitcoin rather than smaller coins.','start-crypto'],
 ['market-cap','Market cap','Stocks','Market capitalisation: share price multiplied by the number of shares. For crypto, price multiplied by coins in circulation.','start-stocks'],
 ['pe','P/E ratio','Stocks','Price-to-earnings: the share price divided by earnings per share. A higher P/E means investors are paying more for each pound or dollar of profit, usually because they expect growth.','start-stocks'],
 ['eps','EPS','Stocks','Earnings per share: a company\'s profit divided by its number of shares. Quarterly EPS against forecasts drives many earnings-day moves.','start-stocks'],
 ['beta','Beta','Stocks','How much a share has tended to move compared with the market (usually the S&P 500). 1.0 moves in line; above 1 swings more; below 1 swings less. Based on past data.','start-stocks'],
 ['dividend','Dividend','Stocks','A cash payment a company makes to shareholders out of its profits. Dividend yield is the annual dividend as a percentage of the share price.','start-stocks'],
 ['index','Index','Stocks','A basket of shares tracked as one number, such as the S&P 500 or FTSE 100. It may be weighted by company size or by share price.','start-stocks'],
 ['etf','ETF','Stocks','Exchange-traded fund: a fund that trades on an exchange like a share. Many track an index, such as SPY for the S&P 500 or QQQ for the Nasdaq-100.','start-stocks'],
 ['earnings-season','Earnings season','Stocks','The weeks after each quarter ends when most listed companies report results. Individual shares can move sharply on the numbers and guidance.','start-stocks'],
 ['candlestick','Candlestick','Charts','A chart bar showing the open, high, low and close for one period. The body spans open to close; the thin wicks show the high and low.','start-charts'],
 ['moving-average','Moving average','Charts','The average closing price over a set number of periods, redrawn each day. The Dispatch shows the 20-day and 50-day averages. It describes the trend but lags the price.','start-charts'],
 ['rsi','RSI','Charts','Relative Strength Index, a 0 to 100 momentum gauge over 14 periods. Above 70 is often called overbought ("stretched"), below 30 oversold ("washed-out").','start-charts'],
 ['support','Support','Charts','A price zone where buying has repeatedly stopped a fall. It is an area, not an exact line.','start-charts'],
 ['resistance','Resistance','Charts','A price zone where selling has repeatedly stopped a rise. A clean break above it can turn it into support.','start-charts'],
 ['volatility','Volatility','Risk','How much and how quickly a price moves. Higher volatility means bigger swings in both directions, and usually calls for smaller positions.','start-risk'],
 ['leverage','Leverage','Risk','Using borrowed money or margin to control a larger position than your cash would allow. It magnifies both gains and losses.','start-risk'],
 ['margin','Margin','Risk','The deposit you put up to open a leveraged position. If losses eat into it, the broker can ask for more (a margin call) or close the position.','start-risk'],
 ['stop-loss','Stop-loss','Risk','An order to close a position automatically if the price reaches a set level, to limit the loss. It is not guaranteed to fill at that exact price.','start-risk'],
 ['slippage','Slippage','Risk','The difference between the price you expected and the price you actually got, common in fast or thin markets.','start-risk'],
 ['gap','Gap','Risk','When a price opens well above or below the previous close with no trading in between, often after news overnight or at the weekend.','start-risk'],
 ['position-size','Position size','Risk','How much you put into one trade. A common method: the amount you are willing to lose divided by the distance from your entry to your stop.','start-risk'],
 ['drawdown','Drawdown','Risk','The fall from a peak to a trough in an account or a price. A 50% drawdown needs a 100% gain to recover.','start-risk'],
 ['correlation','Correlation','Risk','How closely two prices move together, from +1 (in step) to −1 (opposite). Highly correlated positions behave like one bigger position.','start-risk'],
 ['diversification','Diversification','Risk','Spreading money across assets that do not all move together, so one bad outcome does less damage. It can weaken in a crisis, when many assets fall at once.','correlation-risk'],
 ['regime-score','Regime score','The Dispatch','The Dispatch\'s 0 to 100 read of the overall risk mood, built from the VIX, the S&P 500\'s daily move, the dollar index, oil and Bitcoin. 72+ Risk-On (Strong), 55 to 71 Risk-On (Fragile), 40 to 54 Transition, below 40 Risk-Off.','start-dispatch'],
 ['ai-score','AI Score','The Dispatch','A 0 to 100 score on each instrument combining sentiment, momentum, fundamentals and analyst ratings. Indicative only, not a recommendation.','start-dispatch'],
 ['fear-greed','Fear/Greed','The Dispatch','An in-house 0 to 100 sentiment gauge, built mostly from the VIX plus the average daily move across synced prices. 80+ Extreme Greed, below 20 Extreme Fear.','start-dispatch'],
 ['sentiment','Sentiment','The Dispatch','The overall tone of news and commentary around an instrument (positive, neutral or negative). One input into the AI Score.','start-dispatch'],
 ['analyst-rating','Analyst rating','The Dispatch','The consensus view of brokers\' analysts, such as Buy, Hold or Sell. Ratings often lag the price and are only one input among many.','start-dispatch'],
 ['conviction','Signal conviction','The Dispatch','How strongly the evidence behind a signal agrees, shown as a percentage. Higher conviction means more of the inputs point the same way, not that the outcome is certain.','reading-signals'],
];
// 3: wire the guides into LEARN_MODULES under a new "start" tab (existing renderer + list), default Learn tab = Start here
try { LEARN_MODULES.start = RT45_GUIDES.map(g => ({ ...g, summary: g.summary })); } catch (e) {}
const _RT45_GIDS = new Set(RT45_GLOSS.map(x => x[0]));
const _RT45_TABS = [['start','🎓 Start here'],['glossary','📖 Glossary'],['macro','🌍 Macro'],['fundamental','📊 Fundamental'],['technical','⚡ Technical'],['portfolio','🛡 Risk & Portfolio'],['signals','🤖 AI & Signals'],['calc','🧮 Calculators']];
const _rt45Boot = (() => { try { if (!/^\/learn\/?$/.test(location.pathname)) return null; const q = new URLSearchParams(location.search);
  const o = { guide: q.get('guide') || '', tab: q.get('tab') || '', term: q.get('term') || '' }; return (o.guide || o.tab || o.term) ? o : null; } catch (e) { return null; } })();
let _rt45BootDone = !_rt45Boot, _rt45Hi = '', _rt45Q = '';
try { if (typeof _learnTab !== 'undefined' && _learnTab === 'macro') _learnTab = 'start'; } catch (e) {}
function _rt45AllMods() { try { return Object.values(LEARN_MODULES).flat(); } catch (e) { return []; } }
function _rt45Esc(s) { return typeof _escHtml === 'function' ? _escHtml(s) : String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]); }
// [[g:id=Label]] glossary term · [[go:page=Label]] site page · [[guide:id=Label]] another lesson · [[tab:id=Label]] Learn tab
function _rt45Links(html) {
  return String(html).replace(/\[\[(g|go|guide|tab):([a-z0-9\-]+)=([^\]]+)\]\]/g, (m, k, id, lb) => {
    if (k === 'g') return _RT45_GIDS.has(id) ? `<button type="button" class="rt45-gl" data-rt45g="${id}" onclick="_rt45Tip(event,'${id}')">${lb}</button>` : lb;
    if (k === 'guide') return _rt45AllMods().some(x => x.id === id) ? `<a class="rt45-lk" href="/learn/?guide=${id}" onclick="event.preventDefault();_rt45Open('${id}')">${lb}</a>` : lb;
    if (k === 'tab') return `<a class="rt45-lk" href="/learn/?tab=${id}" onclick="event.preventDefault();_rt45Tab('${id}')">${lb}</a>`;
    const path = (typeof PUBLIC_NAV_PATHS !== 'undefined' && PUBLIC_NAV_PATHS[id]) || '/';
    return `<a class="rt45-lk" href="${path}" onclick="event.preventDefault();_rt45Go('${id}')">${lb}</a>`;
  });
}
// article fixes for every Learn lesson: table body rows render as <td> (the base renderer made every row a header, uppercase
// and unwrapped), empty separator rows dropped, and bullet text wrapped in one span so bold words / links stay inline
function _rt45Fix(html) {
  html = String(html).replace(/<p style="[^"]*">\|[-|:\s]+\|<\/p>/g, '').replace(/(<span style="color:var\(--gd\);flex-shrink:0">→<\/span>)([\s\S]*?)(<\/div>)/g, '$1<span style="min-width:0">$2</span>$3');
  return html.replace(/<table([^>]*)>([\s\S]*?)<\/table>/g, (m, a, body) => {
    let i = 0;
    body = body.replace(/<tr><\/tr>/g, '').replace(/<tr>([\s\S]*?)<\/tr>/g, (r, cells) => (i++ === 0) ? `<tr>${cells}</tr>` :
      `<tr>${cells.replace(/<th style="[^"]*">/g, '<td>').replace(/<\/th>/g, '</td>')}</tr>`);
    return `<table class="rt45-tbl"${a}>${body}</table>`;
  });
}
function _rt45Go(p) { try { _rt45TipClose(); if (typeof nav === 'function') nav(p); } catch (e) { location.href = (PUBLIC_NAV_PATHS && PUBLIC_NAV_PATHS[p]) || '/'; } }
function _rt45Scroll() { setTimeout(() => { try { const ov = document.querySelector('#learnOv'); const sc = ov && ov.offsetParent !== null ? (ov.querySelector('.ov-body,.overlay-body') || ov) : document.querySelector('.main'); if (sc) sc.scrollTo(0, 0); window.scrollTo(0, 0); } catch (e) {} }, 50); }
function _rt45Open(id) { _rt45TipClose(); const m = _rt45AllMods().find(x => x.id === id); if (!m) return;
  for (const [k, v] of Object.entries(LEARN_MODULES)) if (Array.isArray(v) && v.some(x => x.id === id)) { _learnTab = k; break; }
  if (typeof pg !== 'undefined' && pg !== 'learn' && !document.getElementById('learnOv')) { try { nav('learn'); } catch (e) {} }
  _learnSub = id; _refreshView(); _rt45Scroll(); }
function _rt45Tab(t) { _rt45TipClose(); if (typeof pg !== 'undefined' && pg !== 'learn' && !document.getElementById('learnOv')) { try { nav('learn'); } catch (e) {} } _learnTab = t; _learnSub = null; _refreshView(); _rt45Scroll(); }
function _rt45Term(id) { _rt45Hi = id; _rt45Q = ''; _rt45Tab('glossary'); setTimeout(() => { try { const el = document.querySelector(`[data-rt45t="${id}"]`); if (el) el.scrollIntoView({ block: 'center' }); } catch (e) {} }, 120); }
// keep the address bar shareable: /learn/?guide=… /learn/?tab=… (only while the Learn page owns the URL)
function _rt45SyncUrl() { try {
  if (!_rt45BootDone || !/^\/learn\/?$/.test(location.pathname)) return;
  const want = _learnSub ? `?guide=${encodeURIComponent(_learnSub)}` : (_learnTab && _learnTab !== 'start') ? `?tab=${encodeURIComponent(_learnTab)}` : '';
  if (location.search !== want) history.replaceState(history.state, '', '/learn/' + want);
  const m = _learnSub && _rt45AllMods().find(x => x.id === _learnSub);
  if (m) { document.title = `${m.title} | Learn | The Dispatch Markets`; const md = document.querySelector('meta[name="description"]'); if (md) md.setAttribute('content', m.summary); }
  else if (/\| Learn \| The Dispatch Markets$/.test(document.title) || /^Learn \| Market Analysis Frameworks/.test(document.title)) { document.title = 'Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Markets'; }
} catch (e) {} }
function _rt45StartHtml() {
  const list = LEARN_MODULES.start || [];
  let h = `<div class="gc rt45-hero"><div class="rt45-k">NEW TO MARKETS? START HERE</div>
    <div class="rt45-h">Plain-English guides, from reading a price to sizing a position</div>
    <div class="rt45-p">${list.length} short guides for beginners and improvers, a searchable <a class="rt45-lk" href="/learn/?tab=glossary" onclick="event.preventDefault();_rt45Tab('glossary')">glossary of ${RT45_GLOSS.length} terms</a>, then the professional frameworks in the other tabs. Tap any <span class="rt45-gl rt45-gl-demo">underlined term</span> for a quick definition.</div>
    <div class="rt45-disc">Education only, not financial advice. Markets carry risk and you can lose money.</div></div>`;
  h += `<div class="rt45-grid">` + list.map((m, i) => `<a class="gc gc-a rt45-card" href="/learn/?guide=${m.id}" onclick="event.preventDefault();_rt45Open('${m.id}')" style="border-left:3px solid ${m.tagCol}">
      <div class="rt45-cm"><span class="rt45-n">${String(i + 1).padStart(2, '0')}</span><span class="rt45-tag" style="color:${m.tagCol};background:${m.tagCol}18">${m.tag}</span><span class="rt45-lv">${m.level} · ${m.mins} MIN</span></div>
      <div class="rt45-ct">${_rt45Esc(m.title)}</div><div class="rt45-cs">${_rt45Esc(m.summary)}</div></a>`).join('') + `</div>`;
  return h;
}
function _rt45GlossHtml() {
  const cats = [...new Set(RT45_GLOSS.map(x => x[2]))];
  const sorted = RT45_GLOSS.slice().sort((a, b) => a[1].localeCompare(b[1], 'en-GB', { sensitivity: 'base' }));
  let h = `<div class="gc rt45-gs"><label for="rt45q" class="rt45-k">SEARCH ${RT45_GLOSS.length} TERMS</label>
    <input id="rt45q" type="search" autocomplete="off" placeholder="e.g. real yield, spread, RSI" value="${_rt45Esc(_rt45Q)}" oninput="_rt45Filter(this.value)" aria-controls="rt45gl">
    <div class="rt45-chips" role="group" aria-label="Filter by topic"><button type="button" class="rt45-chip on" data-c="" onclick="_rt45Cat(this)">All</button>${cats.map(c => `<button type="button" class="rt45-chip" data-c="${_rt45Esc(c)}" onclick="_rt45Cat(this)">${_rt45Esc(c)}</button>`).join('')}</div>
    <div class="rt45-cnt" id="rt45cnt" aria-live="polite"></div></div><div id="rt45gl" class="rt45-gl-list">`;
  h += sorted.map(([id, t, c, d, g]) => {
    const gm = g && _rt45AllMods().find(x => x.id === g);
    return `<div class="gc rt45-term${_rt45Hi === id ? ' rt45-hi' : ''}" id="term-${id}" data-rt45t="${id}" data-c="${_rt45Esc(c)}" data-k="${_rt45Esc((t + ' ' + d + ' ' + c).toLowerCase())}">
      <div class="rt45-tt"><span>${_rt45Esc(t)}</span><span class="rt45-tc">${_rt45Esc(c)}</span></div><div class="rt45-td">${_rt45Esc(d)}</div>
      ${gm ? `<a class="rt45-lk rt45-tg" href="/learn/?guide=${g}" onclick="event.preventDefault();_rt45Open('${g}')">Read: ${_rt45Esc(gm.title)} →</a>` : ''}</div>`;
  }).join('');
  h += `<div class="gc rt45-none" id="rt45none" hidden>No terms match. Try a shorter word, or <a class="rt45-lk" href="#" onclick="event.preventDefault();_rt45Ask()">ask the research assistant</a>.</div></div>`;
  h += `<div class="rt45-disc" style="margin-top:12px">Definitions are simplified for learning. Education only, not financial advice.</div>`;
  return h;
}
let _rt45CatSel = '';
function _rt45Apply() { try {
  const q = (_rt45Q || '').trim().toLowerCase(); let n = 0;
  document.querySelectorAll('#rt45gl .rt45-term').forEach(el => { const ok = (!q || el.dataset.k.includes(q)) && (!_rt45CatSel || el.dataset.c === _rt45CatSel); el.hidden = !ok; if (ok) n++; });
  const c = document.getElementById('rt45cnt'); if (c) c.textContent = n === RT45_GLOSS.length ? `${n} terms` : `${n} of ${RT45_GLOSS.length} terms`;
  const z = document.getElementById('rt45none'); if (z) z.hidden = n > 0;
} catch (e) {} }
function _rt45Filter(v) { _rt45Q = v || ''; _rt45Hi = ''; _rt45Apply(); }
function _rt45Cat(b) { _rt45CatSel = b.dataset.c || ''; document.querySelectorAll('.rt45-chip').forEach(x => x.classList.toggle('on', x === b)); _rt45Apply(); }
function _rt45Ask() { try { if (typeof _openResearchAssistant === 'function') _openResearchAssistant('Explain this market term in plain English: ' + (_rt45Q || '')); } catch (e) {} }
function _rt45Pager(id) {
  const list = LEARN_MODULES.start || []; const i = list.findIndex(x => x.id === id); if (i < 0) return '';
  const pv = list[i - 1], nx = list[i + 1];
  return `<div class="rt45-pager">${pv ? `<a class="gc gc-a rt45-pg" href="/learn/?guide=${pv.id}" onclick="event.preventDefault();_rt45Open('${pv.id}')"><span>← Previous</span>${_rt45Esc(pv.title)}</a>` : '<span></span>'}${nx ? `<a class="gc gc-a rt45-pg rt45-pg-n" href="/learn/?guide=${nx.id}" onclick="event.preventDefault();_rt45Open('${nx.id}')"><span>Next →</span>${_rt45Esc(nx.title)}</a>` : `<a class="gc gc-a rt45-pg rt45-pg-n" href="/learn/?tab=glossary" onclick="event.preventDefault();_rt45Tab('glossary')"><span>Next →</span>Browse the glossary</a>`}</div>`;
}
{
  const _rl0 = renderLearn;
  renderLearn = function () {
    let h = '';
    try { h = _rl0.apply(this, arguments); } catch (e) { h = ''; }
    try {
      const tabs = `<div class="tabs" role="tablist">${_RT45_TABS.map(([id, lb]) => `<button role="tab" aria-selected="${_learnTab === id}" class="${_learnTab === id ? 'on' : ''}" onclick="_rt45Tab('${id}')">${lb}</button>`).join('')}</div>`;
      h = h.replace(/<div class="tabs">[\s\S]*?<\/div>/, tabs);
      h = h.replace('Professional analysis frameworks · Hedge fund methodologies', 'Plain-English guides · Glossary · Professional frameworks');
      if (_learnSub) {
        const isStart = (LEARN_MODULES.start || []).some(x => x.id === _learnSub);
        if (isStart) { const m = LEARN_MODULES.start.find(x => x.id === _learnSub);
          const bk = h.indexOf('← Back</button>');
          if (bk > 0) h = h.slice(0, bk) + h.slice(bk).replace(/(<span style="font-family:var\(--mn\);font-size:9px;background:[^"]*">)([^<]*)(<\/span>)/, `$1$2$3<span class="rt45-lv rt45-lv-a">${m.level} · ${m.mins} MIN READ</span>`);
          const disc = h.lastIndexOf('<div style="margin-top:24px;padding:14px;background:var(--b1)');
          if (disc > 0) h = h.slice(0, disc) + _rt45Pager(_learnSub) + h.slice(disc);
        }
        h = _rt45Links(_rt45Fix(h));
      } else if (_learnTab === 'start') {
        const at = h.indexOf('</div>', h.indexOf('role="tablist"')) + 6;
        h = h.slice(0, at) + _rt45StartHtml();
      } else if (_learnTab === 'glossary') {
        const at = h.indexOf('</div>', h.indexOf('role="tablist"')) + 6;
        h = h.slice(0, at) + _rt45GlossHtml();
        setTimeout(_rt45Apply, 0);
      } else {
        h = _rt45Links(h);
      }
    } catch (e) {}
    setTimeout(_rt45SyncUrl, 0);
    return h;
  };
}
// boot: honour /learn/?guide= /learn/?tab= /learn/?term= once the app has drawn the Learn page
function _rt45BootApply() { try {
  if (_rt45BootDone) return; if (typeof pg !== 'undefined' && pg !== 'learn' && !document.getElementById('learnOv')) return;
  const b = _rt45Boot; _rt45BootDone = true;
  if (b.guide && _rt45AllMods().some(x => x.id === b.guide)) _rt45Open(b.guide);
  else if (b.term && _RT45_GIDS.has(b.term)) _rt45Term(b.term);
  else if (b.tab && _RT45_TABS.some(t => t[0] === b.tab)) _rt45Tab(b.tab);
  else _refreshView();
} catch (e) { _rt45BootDone = true; } }
if (_rt45Boot) { [0, 600, 1500, 3000].forEach(t => setTimeout(_rt45BootApply, t)); setTimeout(() => { _rt45BootDone = true; }, 3500); }
window.addEventListener('popstate', () => setTimeout(() => { try { if (!/^\/learn\/?$/.test(location.pathname)) return; const q = new URLSearchParams(location.search), g = q.get('guide');
  if (g && g !== _learnSub && _rt45AllMods().some(x => x.id === g)) _rt45Open(g); } catch (e) {} }, 60));

// 4: "what's this?" tips: tap an underlined term or an (i) for a short definition, with a link into the glossary
function _rt45TipClose() { try { const t = document.getElementById('rt45tip'); if (t) t.remove(); } catch (e) {} }
function _rt45Tip(ev, id) {
  try { if (ev) { ev.preventDefault(); ev.stopPropagation(); } } catch (e) {}
  const row = RT45_GLOSS.find(x => x[0] === id); if (!row) return;
  const open = document.getElementById('rt45tip'); if (open && open.dataset.id === id) { _rt45TipClose(); return; }
  _rt45TipClose();
  const [, t, , d, g] = row; const gm = g && _rt45AllMods().find(x => x.id === g);
  const el = document.createElement('div'); el.id = 'rt45tip'; el.className = 'rt45-tip'; el.dataset.id = id; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', t);
  el.innerHTML = `<div class="rt45-tip-h"><span>${_rt45Esc(t)}</span><button type="button" aria-label="Close" onclick="_rt45TipClose()">×</button></div><div class="rt45-tip-d">${_rt45Esc(d)}</div>
    <div class="rt45-tip-a"><a class="rt45-lk" href="/learn/?term=${id}" onclick="event.preventDefault();_rt45Term('${id}')">Open in glossary →</a>${gm && gm.id !== _learnSub ? `<a class="rt45-lk" href="/learn/?guide=${g}" onclick="event.preventDefault();_rt45Open('${g}')">Read the guide →</a>` : ''}</div>`;
  document.body.appendChild(el);
  const W = window.innerWidth;
  if (W < 600) { el.classList.add('rt45-sheet'); }
  else { try { const r = (ev && ev.currentTarget && ev.currentTarget.getBoundingClientRect) ? ev.currentTarget.getBoundingClientRect() : (ev && ev.target ? ev.target.getBoundingClientRect() : null);
    if (r) { const w = 300; let x = Math.min(Math.max(8, r.left), W - w - 8); let y = r.bottom + 8; if (y + 180 > window.innerHeight) y = Math.max(8, r.top - 8 - el.offsetHeight); el.style.left = x + 'px'; el.style.top = y + 'px'; } } catch (e) {} }
}
document.addEventListener('click', e => { try { const t = document.getElementById('rt45tip'); if (t && !t.contains(e.target) && !e.target.closest('.rt45-i,.rt45-gl')) _rt45TipClose(); } catch (x) {} }, true);
document.addEventListener('keydown', e => { if (e.key === 'Escape') _rt45TipClose(); });
window.addEventListener('scroll', () => { const t = document.getElementById('rt45tip'); if (t && !t.classList.contains('rt45-sheet')) _rt45TipClose(); }, true);
// (i) buttons beside known labels on instrument detail views (desktop panel 02 and the phone analysis page) only
const _RT45_LBL = [
  [/^Beta\b/, 'beta'], [/^P\/E\b/, 'pe'], [/^Sentiment\b/, 'sentiment'], [/^Rating\b/, 'analyst-rating'], [/^(Mkt Cap|Market cap|MARKET CAP)\b/, 'market-cap'],
  [/^VOLUME$/, 'volume'], [/^RANGE \(H−L\)\/L$/, 'day-range'], [/^Momentum \(RSI\)/, 'rsi'], [/^─ 20-day average$/, 'moving-average'], [/^52W (High|Low)$/, '52-week'],
  [/^(LIVE|LIVE·CB|LIVE·KR|LIVE·YS|LIVE FX)$/, 'live-price'], [/^DELAYED/, 'delayed-price'], [/^SPOT PROXY$/, 'spot-proxy'], [/^(◌ )?CLOSED$/, 'last-close'], [/^STALE/, 'stale'], [/^SYNTH·DXY$/, 'dxy'],
  [/^Official spot \(EIA\)/, 'eia-spot'], [/^AI SCORE\b/, 'ai-score']
];
function _rt45Roots() { const out = []; try {
  if (typeof IS_DESKTOP === 'function' && IS_DESKTOP()) { if (typeof selTk !== 'undefined' && selTk) { const p = document.getElementById('p2body'); if (p) out.push(p); } }
  else if (typeof pg !== 'undefined' && pg === 'anlz') { const m = document.getElementById('main'); if (m) out.push(m); }
} catch (e) {} return out; }
function _rt45Scan() { try {
  for (const root of _rt45Roots()) {
    root.querySelectorAll('div,span,th,td,label,strong,b').forEach(el => {
      if (el.querySelector(':scope > .rt45-i') || (el.nextElementSibling && el.nextElementSibling.classList.contains('rt45-i')) || el.closest('.rt45-tip,.tape-track,#tape,nav,header,button,a,.pulse,[class*="intel"]')) return;
      if (el.childElementCount > 1) return;
      const t = (el.textContent || '').trim(); if (!t || t.length > 46) return;
      const hit = _RT45_LBL.find(([re]) => re.test(t)); if (!hit) return;
      if (hit[1] === 'ai-score' && el.childElementCount === 1) { const s = el.firstElementChild; if (s && /ⓘ/.test(s.textContent)) { s.style.display = 'none'; } }
      else if (el.childElementCount === 1 && !/^(Beta|P\/E|Sentiment|Rating)/.test(t)) return;
      const b = document.createElement('button'); b.type = 'button'; b.className = 'rt45-i'; b.textContent = 'i'; b.title = "What's this?"; b.setAttribute('aria-label', "What's this: " + ((RT45_GLOSS.find(x => x[0] === hit[1]) || [])[1] || 'definition'));
      b.addEventListener('click', ev => _rt45Tip(ev, hit[1]));
      if (/^(live-price|delayed-price|spot-proxy|last-close|stale|dxy)$/.test(hit[1])) el.insertAdjacentElement('afterend', b); else el.appendChild(b);
    });
  }
} catch (e) {} }
setInterval(_rt45Scan, 1200);
// one "price labels" help entry on the Markets list (desktop panel header + phone page top), linking to the table guide
function _rt45MktHelp() { try {
  const hdr = document.querySelector('#p1 .panel-hdr-r');
  if (hdr && !hdr.querySelector('.rt45-mh')) { const a = document.createElement('a'); a.className = 'rt45-mh'; a.href = '/learn/?guide=start-markets-table'; a.textContent = 'ⓘ Labels'; a.title = 'What LIVE, DELAYED, SPOT and CLOSED mean';
    a.addEventListener('click', e => { e.preventDefault(); _rt45Open('start-markets-table'); }); hdr.insertBefore(a, hdr.firstChild); }
} catch (e) {} }
setInterval(_rt45MktHelp, 2000);
{
  const _rm0 = typeof renderMkt === 'function' ? renderMkt : null;
  if (_rm0) renderMkt = function () { let h = _rm0.apply(this, arguments);
    try { if (typeof IS_DESKTOP === 'function' && !IS_DESKTOP() && typeof h === 'string' && h) h = `<a class="rt45-mh rt45-mh-m" href="/learn/?guide=start-markets-table" onclick="event.preventDefault();_rt45Open('start-markets-table')">ⓘ What do LIVE, DELAYED, SPOT and CLOSED mean?</a>` + h; } catch (e) {}
    return h; };
}
try { const st = document.createElement('style'); st.id = 'rt45css'; st.textContent = `
.rt45-hero{padding:18px;margin-bottom:14px;border-left:3px solid var(--gd)}
.rt45-k{display:block;font-family:var(--mn);font-size:9px;letter-spacing:.16em;color:var(--gd);font-weight:700;margin-bottom:8px}
.rt45-h{font-family:var(--sn);font-size:18px;font-weight:800;color:var(--tx);line-height:1.25;margin-bottom:8px}
.rt45-p{font-family:var(--sn);font-size:13px;color:var(--t2);line-height:1.6}
.rt45-disc{font-family:var(--mn);font-size:9.5px;color:var(--t3);margin-top:10px;line-height:1.5}
.rt45-grid{display:grid;grid-template-columns:1fr;gap:12px;margin-bottom:12px}
@media(min-width:900px){.rt45-grid{grid-template-columns:1fr 1fr}}
.rt45-card{display:block;padding:16px;color:inherit;text-decoration:none;min-width:0}
.rt45-cm{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.rt45-n{font-family:var(--mn);font-size:10px;color:var(--t3)}
.rt45-tag{font-family:var(--mn);font-size:9px;padding:2px 8px;border-radius:4px;font-weight:700}
.rt45-lv{font-family:var(--mn);font-size:9px;color:var(--t3);letter-spacing:.06em}
.rt45-lv-a{margin-left:8px;display:inline-block}
.rt45-ct{font-family:var(--sn);font-size:16px;font-weight:800;color:var(--tx);line-height:1.25;margin-bottom:6px}
.rt45-cs{font-family:var(--sn);font-size:12px;color:var(--t2);line-height:1.55}
.rt45-tbl th{white-space:normal!important}
.rt45-tbl td{padding:8px 10px;border-bottom:1px solid var(--gb);color:var(--t2);font-family:var(--sn);font-size:12px;line-height:1.5;white-space:normal;text-transform:none;letter-spacing:normal;vertical-align:top;overflow-wrap:anywhere}
.rt45-tbl td:first-child{font-family:var(--mn);font-size:11px;color:var(--tx);min-width:90px}
.rt45-tbl tr:hover td{background:transparent}
.rt45-lk{color:var(--gd);text-decoration:underline;text-underline-offset:2px;cursor:pointer}
.rt45-gl{background:none;border:0;padding:0;font:inherit;color:inherit;cursor:help;text-decoration:underline dotted var(--gd);text-decoration-thickness:1.5px;text-underline-offset:3px}
.rt45-gl:hover,.rt45-gl:focus-visible{color:var(--gd)}
.rt45-gs{padding:14px;margin-bottom:12px}
.rt45-gs input{width:100%;box-sizing:border-box;background:var(--b2);border:1px solid var(--gb);color:var(--tx);border-radius:8px;padding:11px 12px;font-family:var(--sn);font-size:16px;outline:none}
.rt45-gs input:focus{border-color:var(--gd)}
.rt45-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.rt45-chip{font-family:var(--sn);font-size:11px;padding:6px 10px;border-radius:999px;border:1px solid var(--gb);background:var(--b2);color:var(--t2);cursor:pointer}
.rt45-chip.on{border-color:var(--gd);color:var(--gd);background:var(--gdG)}
.rt45-cnt{font-family:var(--mn);font-size:9.5px;color:var(--t3);margin-top:8px}
.rt45-term{padding:14px 16px;margin-bottom:8px;scroll-margin-top:160px}
.rt45-term[hidden],.rt45-none[hidden]{display:none!important}
.rt45-hi{outline:2px solid var(--gd);outline-offset:-2px}
.rt45-tt{display:flex;justify-content:space-between;gap:10px;align-items:baseline;font-family:var(--sn);font-size:14px;font-weight:800;color:var(--tx);margin-bottom:5px}
.rt45-tc{font-family:var(--mn);font-size:9px;font-weight:400;color:var(--t3);white-space:nowrap}
.rt45-td{font-family:var(--sn);font-size:12.5px;color:var(--t2);line-height:1.6;overflow-wrap:anywhere}
.rt45-tg{display:inline-block;margin-top:7px;font-family:var(--sn);font-size:11.5px}
.rt45-none{padding:16px;text-align:center;font-family:var(--sn);font-size:12.5px;color:var(--t2)}
.rt45-pager{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}
.rt45-pg{display:block;padding:12px 14px;color:var(--tx);text-decoration:none;font-family:var(--sn);font-size:12.5px;font-weight:700;line-height:1.35;min-width:0;overflow-wrap:anywhere}
.rt45-pg span{display:block;font-family:var(--mn);font-size:9px;font-weight:400;color:var(--gd);letter-spacing:.08em;margin-bottom:4px}
.rt45-pg-n{text-align:right}
.rt45-i{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;margin-left:5px;padding:0;border-radius:50%;border:1px solid var(--t3);background:transparent;color:var(--t2);font:italic 700 9px/1 Georgia,serif;cursor:help;vertical-align:middle;flex:0 0 auto;position:relative}
.rt45-i::after{content:"";position:absolute;inset:-8px}
.rt45-i:hover,.rt45-i:focus-visible{border-color:var(--gd);color:var(--gd)}
.rt45-tip{position:fixed;z-index:100000;width:300px;max-width:calc(100vw - 16px);box-sizing:border-box;background:var(--b1,#151821);border:1px solid var(--gb);border-radius:10px;padding:12px 14px;box-shadow:0 12px 32px rgba(0,0,0,.5)}
.rt45-tip.rt45-sheet{left:8px!important;right:8px;bottom:calc(72px + env(safe-area-inset-bottom,0px));top:auto!important;width:auto;max-width:none}
.rt45-tip-h{display:flex;justify-content:space-between;align-items:center;gap:8px;font-family:var(--sn);font-size:14px;font-weight:800;color:var(--tx);margin-bottom:6px}
.rt45-tip-h button{background:none;border:0;color:var(--t2);font-size:20px;line-height:1;cursor:pointer;padding:0 4px;min-width:32px;min-height:32px}
.rt45-tip-d{font-family:var(--sn);font-size:12.5px;color:var(--t2);line-height:1.55}
.rt45-tip-a{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-family:var(--sn);font-size:12px}
.rt45-mh{font-family:var(--mn);font-size:9.5px;color:var(--t2);text-decoration:none;border:1px solid var(--gb);border-radius:6px;padding:3px 8px;margin-right:6px;white-space:nowrap;cursor:pointer}
.rt45-mh:hover{color:var(--gd);border-color:var(--gd)}
.rt45-mh-m{display:block;margin:0 0 12px;padding:9px 12px;font-size:11px;white-space:normal;line-height:1.4}
`; document.head.appendChild(st); } catch (e) {}
'''
s = s.rstrip('\n') + '\n' + BLOCK
if h.count('app.js?v=chat43') != 1: die('index bust anchor')
h = h.replace('app.js?v=chat43', 'app.js?v=chat44')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt45 block appended + index chat43->chat44; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
