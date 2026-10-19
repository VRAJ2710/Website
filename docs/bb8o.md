# bb8o: quote fallback, insider trade dates, LSE profile, canonical feed status, brief edition

Server only (`deploy/patch_bb8o.py`), stacked on bb8n (server.js md5 `9b48a917c654891a50e7c7c6bd8c9a49`, 16308 lines)
giving md5 `4354704c92cf75f9d79f1181d14abc31` (16952 lines). The block is appended at the end of server.js. Its 25 anchors are
long-standing declarations (json, handle, yahooQuote, fetchYahooQuote, bb5e/bb5g specs, bb7 Form 4 parser, parseForm4,
bb8lRowDates, rt32Crumb/rt32Get, rt32Yahoo, RT32, readBody, the `var bb2Read0 = …` alias, _rt48sHeads, bb8cUnit,
bb8dUk) and the `// BB8N_JS_END` marker, 29 in all. It doesn't wrap or anchor
on Ask grounding, the numeric guard, news-source relevance or chat meta, so it rebases cleanly onto bb8p.
No tables, timers, intervals, dependencies, secrets, paid feeds or Stripe changes, and no new SEC requests. The shared sec.gov
limiter is untouched (itest_f: max 10 starts in any rolling second).

## 1. Zero / null / non-finite prices

Findings (Mon 19 Oct, box, live Yahoo):

- The server never returned a zero price for 0700.HK, 9988.HK, 0005.HK, 7203.T, 005930.KS, 2330.TW, BHP.AX or RELIANCE.NS.
- The `0.00%` for 0700.HK is real: Yahoo's daily bars show HK$417.80 at the close on both Thu 15 and Fri 16 Oct (different OHLC).
- The `0.00%` for 2330.TW is also real: Fri 16 and Mon 19 Oct both closed at 2420.
- 2330.TW used the **US** session table ("US market closed · opens Mon 19 Oct, 14:30 UK"). bb8o adds the Taipei session
  (09:00 to 13:30 Asia/Taipei) for `.TW` and `.TWO`, so the note now reads "Taiwan market closed · opens Tue 20 Oct, 02:00 UK".

Guard (defence in depth):

- `yahooQuote` is wrapped, which covers /api/yahoo-quote, the Pulse cards (bb3), the Ask move pack, gold and macro.
  `fetchYahooQuote` (DXY inputs) is wrapped too.
- `json()` checks every quote row on /api/yahoo-quote, /api/market-reference-quotes, /api/twelve-data-quote, /api/finnhub
  (quote) and /api/spot-energy, plus `valuation.price` on /api/financials.
- A row whose price is 0, null, missing, NaN or Infinity gets the last valid price this process saw for that symbol.
  If there is none, it gets the last valid daily close from one free Yahoo chart read. If neither exists, the row is
  dropped; it is never sent as 0.
- A fallback row carries:
  `fallback: true`, `fallbackReason` (`zero-price` | `missing-price` | `non-finite-price`), `fallbackSource`,
  `ts` (the real timestamp of that close), `basis`, `prev`/`c`/`change` (that session's change vs the prior trading day),
  `session {kind, date, dayUk, asOf, asOfUk, local, label}` (for example `regular close, Fri 16 Oct, 16:08 HKT (09:08 UK)`),
  and `note` ("Last valid close · …").
- Valid prices with a non-finite change or previous close are sent as `c: 0, change: 0, prev: null, basis: "none",
  changeAvailable: false`. The client already shows "—" for basis none.
- There are no "reels" in the server, client or scripts. The brief has no server price data (prices come from the
  client's synced quotes).

## 2. Insider trade dates (NVDA)

- Form 4 rows (`bb7ParseForm4` and the legacy `parseForm4`) take the trade date from `transactionDate`. If that is missing they
  use `deemedExecutionDate`, then the document's `periodOfReport`. All three come from the same XML, so there are no extra
  SEC requests.
- Rows with none of these get `transactionDate: null`. The filing date is never substituted.
- On live NVDA, all 37 latest rows and all 199 rows of `before=2026-03-20` have a `transactionDate`.
- QA's "filing only" rows (2 Sep, 4 Jun 2026, 15 Oct 2025) are same-day filings where trade date = filing date. The client
  shows a single date for those, followed by the "Filing" link, so they looked like filing dates.
- Rows are now sorted by trade date (newest first), then filing date, so the 15 Oct 2025 rows no longer sit after 14 Oct.

Fields on every `insider[]` row (Frontend):

| field | value |
|---|---|
| `tradeDate` / `transactionDate` | `YYYY-MM-DD` or `null` |
| `tradeDateUk` / `transactionDateUk` | `21 Sep 2026` or `null` |
| `transactionDateMissing` | `true` when no date found |
| `transactionDateSource` | `transactionDate` \| `deemedExecutionDate` \| `periodOfReport` \| `null` |
| `filingDate`, `filingDateUk` | unchanged |
| `sameDayFiling` | `true` when trade date = filing date |
| `whenUk` | `21 Sep 2026 · filed 23 Sep 2026` / `2 Sep 2026 · filed same day` / `Trade date not reported · filed 2 Sep 2026` |

Frontend: render `whenUk` (or use `transactionDateMissing`) in `fe73_rowWhen` in place of falling back to the filing date.

## 3. BP.L: DYNAMIC LOOKUP vs Analysis

Cause (client):

- HSBA.L, AZN.L and SHEL.L are in the client's `RT43_INTL` list (app.js), so they get a desk entry and the Analysis view.
  BP.L, ULVR.L, VOD.L and RR.L are not, so they go through `lookupTicker`.
- `lookupTicker` reads `/api/search` as `result[]`, but the server only returned `quotes[]`. So `match` was null and the
  view showed "Listing details unavailable", with `mc` hard-coded to "—".

Fix (server):

- `/api/search` now also returns `result[]` in the client's shape: `{symbol, name, exchange, exchangeCode, type,
  quoteType, sector, industry}`. `quotes[]` is unchanged.
- For an exact LSE symbol query (`XXX.L`) the matching row and the body carry `profile`.
- New `GET /api/listing-profile?symbol=BP.L` (public, free Yahoo quoteSummary price/summaryDetail/defaultKeyStatistics/
  assetProfile). It is cached for 30 minutes and uses the existing Yahoo per-visitor limiter on a cache miss.

Profile fields:
`symbol, name, exchange ("LSE"), exchangeName, region ("UK"), type, priceCurrency ("GBp"), currency ("GBP"), unitNote,
price (pence), priceMajor (pounds), marketCap (GBP), marketCapCurrency, marketCapText ("£95.7bn"),
marketCapCheck {status ok|corrected-minor-units|computed|unverified|mismatch, sharesOutstanding, impliedMarketCap, ratio},
pe, sector, industry, about, asset {tk, nm, cat, ex, rg, pe, mc, th}, source, sourceUrl, asOf, asOfUk`.

GBp is handled as follows: the market cap is checked against shares × price ÷ 100. If it is 100× too big, it is divided
and flagged `corrected-minor-units`.

| symbol | market cap | check |
|---|---|---|
| BP.L | £95.7bn | ratio 1.000 |
| SHEL.L | £224.4bn | ok |
| AZN.L | £191.5bn | ok |
| ULVR.L | £105.7bn | ok |
| VOD.L | £27.9bn | ok |
| RR.L | £108.6bn | ok |
| HSBA.L | £239.7bn | ok |

`asset` has no score, sentiment or rating fields.

Frontend: in `lookupTicker`, use `searchJson.profile` (or `match.profile`) to fill `mc` and the name/exchange. To show the
full Analysis view, push `profile.asset` into `A` the way RT43_INTL does. Don't add a rating such as "Hold".

## 4. Canonical feed status

Every quote row on every quote route carries `feed`:

```
feed: { v: 1, symbol: "EURUSD=X", status: "live"|"delayed"|"stale"|"closed",
        reason: "fresh"|"exchange-delay"|"age"|"session-closed"|"thin-market"|"fallback"|"no-timestamp",
        ageSec: 24, asOf: ISO, asOfUk: "Mon 19 Oct, 11:51 UK", delayMin: 0, source: "yahoo",
        market: "FX", sessionDate: "2026-10-19", sessionDayUk: "Mon 19 Oct",
        sessionLabel: "regular close, Fri 16 Oct, 16:08 HKT (09:08 UK)" | null, fallback: false }
```

How `status` is set:

- `closed`: the venue session is closed. This uses the same session tables as the legacy status.
- Otherwise, with age = now − the row's own timestamp and d = the exchange delay:
  - `live`: age ≤ d + 180 s and d = 0.
  - `delayed`: age ≤ d + 180 s and d > 0, or age ≤ d + 20 min.
  - `stale`: anything older, or a fallback price while the venue is open.

The same function runs on every route, so two endpoints carrying the same observation give the same answer. A route that
serves an older cached row (for example the 15-minute Twelve Data cache) honestly reports its larger `ageSec`.
`feed.symbol` is the canonical key: `EUR/USD` becomes `EURUSD=X`. The legacy `status`/`stale`/`note` fields are unchanged.

Endpoints: `/api/yahoo-quote` (each key), `/api/market-reference-quotes` (XAU, DXY), `/api/twelve-data-quote`
(`quotes.*`, `directIndices.*`), `/api/finnhub?endpoint=quote`, `/api/spot-energy` (WTI, BRENT).

Frontend: read `feed.status` for the LIVE/DELAYED/CLOSED badge and `feed.asOfUk`/`feed.sessionDayUk` for the day tag.
The QA "Mon" tag on 0700.HK should come from `feed.sessionDayUk` = "Fri 16 Oct".

## 5. Brief edition

Routes: `GET /api/brief/edition` (public), and `edition` is added to a successful `POST /api/brief` response.

```
{ editionId: "2026-10-19.1-4e5624", day, seq, status: "ok", reason: "cold-start"|"new-day"|"broader-coverage"|"lead-aged",
  lead: {headline, source, link, publishedAt, publishedAtUk, coverage, sources[], assets[]}, also: [3 stories],
  updatedAt: ISO, updatedAtUk: "Updated 11:52 UK", checkedAt, checkedAtUk, rule, memory: "process" }
```

Rule (deterministic, evaluated on request, no timers):

- Headlines come from the existing approved RSS feeds through `_rt48sHeads()`, re-read at most once every 5 minutes, and
  only when a request arrives.
- Stories are ranked by score = 10 × outlets carrying the story + up to 3 for assets named. Ties go to the newer story,
  then A–Z.
- A new edition starts when:
  - no edition is in memory;
  - a new UK day begins;
  - after a 30-minute dwell, a story published after the lead scores at least 10 more, meaning one more outlet carries it;
  - or the lead is over 12 hours old and a newer story ranks at least as high.
- Otherwise the lead, `also`, `editionId` and `updatedAt` stay fixed.
- `editionId` is the UK date, a sequence number and a 6-character hash of the lead.

On restart, the edition lives only in this process's memory (no table). After a restart or deploy, the first request
elects a lead from the current feeds by the same rule (`reason: "cold-start"`, `seq` 1). If the feeds have not moved, the
lead and `editionId` are identical. If they have, the new edition starts there, with `updatedAt` = the restart's first
request. Autoscale instances each keep their own memory. Because the rule is deterministic they agree whenever they see
the same feeds, but they can differ for up to one 5-minute read window.

Frontend: the guest "Headline focus" (`_buildLocalBrief`, NEWS[0]) should use `edition.lead.headline` and `updatedAtUk`.

## 6. Analyst ratings and price targets (approved by Jack)

There is one sanitizer, `bb8oStripRatings`. It deletes these keys, case-insensitively, at any depth:

- `targetHighPrice targetLowPrice targetMeanPrice targetMedianPrice targetHigh targetLow targetMean targetMedian`
- `priceTarget(s) targetPrice analystTarget(s) consensusTarget`
- `recommendationKey recommendationMean recommendation recommendations recommendationTrend upgradeDowngradeHistory
  upgrades downgrades numberOfAnalystOpinions`
- `analystRating(s) averageAnalystRating consensusRating rating ratings ra`

Where it runs:

- **Response layer:** `json()`, so every JSON route. Live NVDA, MU, BP.L, AAPL, HSBA.L, MSFT, 0700.HK, SHEL.L and BTC-USD
  replays on 16 routes each, plus 7 general routes (151 responses), had 0 banned keys after. Before, `/api/financials`
  carried `valuation.targetMean` and `valuation.recommendation` for 8 of the 9 symbols. That was the only route that did.
- **Source:** the `rt32Yahoo` quoteSummary result. It removes `financialData.target*Price`, `recommendationKey/Mean`,
  `numberOfAnalystOpinions`, and the `recommendationTrend` / `upgradeDowngradeHistory` modules if present. So
  `rt32Build` (valuation), the Ask valuation and peer facts, the card beta/earnings lookups and bb8c's builds never get them.
- **Cache:** `RT32.cache.set` strips each stored entry, and existing entries are stripped once at load. So anything reading
  the fundamentals cache, including the numeric guard and peer blocks, never sees them.
- **AI request bodies:** `readBody` (/api/chat, /api/brief, committee and the other AI routes) and `bb2Read0` (Ask paths).
  Keys are stripped, and the scrubber `bb8oScrubText` removes three kinds of rating/target text before any fact or prompt
  builder runs:
  - "Rating: …" labels, for example the client's "AI score … | Rating: Strong Buy";
  - rating words between `·`/`|` separators, for example "Active ticker: NVDA … · Bullish · Strong Buy · $182.10";
  - price-target sentences with a figure, and "consensus/analyst/street rating X".
  Sentiment, score, price, beta and P/E are kept, and the user's question is untouched.
- **Finnhub:** `/api/finnhub` serves only `endpoint=quote`. Recommendation, price-target and upgrade-downgrade endpoints
  return `[]` and were checked in the scan.
- **AI JSON outputs:** a `recommendation` field in an AI JSON output (committee) is also removed from the response.

Client (Frontend's job, not changed here):

- `ra:` ratings ("Strong Buy", "Buy", "Hold", "Accumulate", "Avoid") are in the built-in asset list `A` (app.js lines
  228–466, about 200 entries) and in the RT43_INTL loop at line 19706 (`ra: "Hold"`). Other `ra:` lines are at 1182, 1185,
  1224, 4072, 4083 and 21322.
- The rating is shown or sent at line 584 (Ask context "Rating: …"), 9305 ("Rating:"), 13284 (badge), 20804 (Ask
  "Active ticker" line), and 1229/2964 ("Avoid" counts toward bearish weight).
- `renderFinancials` (line 10215 on) reads `priceTarget`, `recommendations` and `upgrades` and draws "ANALYST PRICE
  TARGETS" and Buy/Hold/Sell counts. Those fields are no longer sent, so those panels stay empty. Frontend should remove
  them.

Not stripped: consensus EPS and revenue estimates (`epsEstimate`, `earningsAverage`, `earningsTrend`, the forward P/E basis).
These are estimates, not ratings or targets.

## Tests

`node --test test/bb8o.test.js`: 11 tests, offline, using vm with stubs.
