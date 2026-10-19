# bb8o: quote fallback, insider trade dates, LSE profile, canonical feed status, brief edition

Server only (`deploy/patch_bb8o.py`), stacked on bb8p (PR #67, branch `cursor/bb8p-grounding-guard-p0`, server.js md5
`92cdce800208671ab32ded68d15e24d1`, 16956 lines) giving md5 `0ac5d92b95f7b382841665c3ea4a8234` (17768 lines). The block is
appended after the `// BB8P_JS_END` marker, so the first 16956 lines are byte-identical to bb8p, with no in-place edits.
Its 30 anchors are long-standing declarations (json, handle, yahooQuote, fetchYahooQuote, bb5e/bb5g specs, bb7 Form 4 parser,
parseForm4, bb8lRowDates, rt32Crumb/rt32Get, rt32Yahoo, RT32, readBody, the `var bb2Read0 = …` alias, _rt48sHeads, bb8cUnit,
bb8dUk, crypto) plus the `// BB8N_JS_END` and `// BB8P_JS_END` markers. Section 7 also wraps `generateAi` (outermost) and
reads the four AI validators by identity; those are found at load time with `typeof` checks, not anchors. bb8o doesn't wrap or anchor on bb8p's grounding rule,
numeric guard, source relevance, provider/model, meta.quote or timeframe code. bb8o's hooks are installed after bb8p's, so
they're the outer wrappers on `json` and `handle`.
No tables, timers, intervals, dependencies, secrets, paid feeds or Stripe changes, and no new SEC requests. The shared sec.gov
limiter is untouched (itest_f: max 10 starts in any rolling second).
Gold spot / headline gold and the Ask answer fixes (brief direct answer, paragraph breaks, "Live:" full stop, move-pack
fallback) are not in bb8o. They moved to bb8q.

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

## 6. Analyst ratings and price targets (approved by Jack; narrowed per Jack's 12:13 request)

There is one sanitizer, `bb8oStripRatings(x, generic)`. It uses two key lists (case-insensitive, any depth):

- **Target / analyst keys (`BB8O_TARGET_KEYS`, stripped globally):** `targetHighPrice targetLowPrice targetMeanPrice
  targetMedianPrice targetHigh targetLow targetMean targetMedian priceTarget(s) targetPrice analystTarget(s) consensusTarget
  recommendationKey recommendationMean recommendationTrend upgradeDowngradeHistory numberOfAnalystOpinions analystRating(s)
  averageAnalystRating consensusRating`.
- **Generic keys (`BB8O_GENERIC_KEYS`, market / security payloads only):** `rating ratings ra recommendation recommendations
  upgrades downgrades`.

The generic keys are stripped only where the payload really is market or security data. That's an explicit allowlist,
not the global JSON helper:

- **Routes (`BB8O_MARKET_ROUTES`, exact path match):** `/api/financials /api/earnings /api/holders /api/insiders
  /api/institutional-data /api/openbb/fundamentals /api/openbb/summary /api/openbb/historical /api/yahoo-quote /api/yahoo-chart
  /api/market-reference-quotes /api/twelve-data-quote /api/finnhub /api/ext-hours /api/coingecko /api/spot-energy /api/eia-spot
  /api/gold-desk /api/real-yield /api/search /api/listing-profile /api/screener /api/regime-fit /api/ticker-news
  /api/news-scores /api/brief /api/brief/edition`.
- **Payload builders:** the `rt32Yahoo` quoteSummary result and every `RT32.cache` entry (the fundamentals source and cache
  behind /api/financials, Ask valuation and peer facts, card beta/earnings and the numeric guard). Existing cache entries are
  stripped once at load.
- **AI request bodies (`readBody`, `bb2Read0`):** only the client-supplied context / fact fields (`BB8O_CTX_FIELDS`: context,
  terminalContext, contextNotes, notes, facts, fact, tickers, assets, asset, sources, marketData, quotes, portfolio,
  watchlist) are sanitized in full. That covers both key lists and the text scrubber `bb8oScrubText`, which removes
  "Rating: …" labels, rating words between `·`/`|` separators, price-target sentences with a figure, "consensus/analyst/street
  rating X", "Analyst: n buy / n hold / n sell" and "PT mean $x". `messages` is skipped entirely. `question`, `userThesis` and
  every other user-typed field keep their text; only target / analyst keys are removed from non-context objects. So the user's
  question reaches the model byte-identical. "Should I buy MU?" arrives unchanged on both Ask paths with bb8p's guard in
  front, and the answer still gives no buy/sell advice: bb8p's grounding rule, the system rule "No buy or sell recommendation
  and no price target" and the base advice rewrite still apply.

Everywhere else (`/api/me`, Academy/quiz, prefs, account export, admin and Console routes, `/api/ai-status`, editorial
content, the Stripe webhook), only target / analyst keys are removed. A quiz `rating`, an editorial `recommendation` or a
`ra` field passes through. The replay against bb8p is byte-identical (see Tests).

**AI committee / lenses / intelligence / chat outputs are not in the generic allowlist.** Their JSON is the AI's own analysis.
In the server's output normaliser (`recognizedKeys`, server line 3973), `recommendation` is a prose section of that analysis
(next to `summary`, `verdict`, `thesis`), not a market rating field, so stripping it would delete the AI's text, not a rating.
The no-advice / no-target rules for those outputs live in their prompts. Target / analyst keys are still removed from them.

- **Finnhub:** `/api/finnhub` serves only `endpoint=quote`. Recommendation, price-target and upgrade-downgrade endpoints return
  `[]` and were checked in the scan.
- **Scan:** live NVDA, MU, BP.L, AAPL, HSBA.L, MSFT, 0700.HK, SHEL.L and BTC-USD replays on 16 market routes each, plus 7
  general routes (151 responses), had 0 target keys and 0 generic keys after. On bb8p, `/api/financials` carried
  `valuation.targetMean` and `valuation.recommendation` for 8 of the 9 symbols.

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

## 7. AI committee, lenses, intelligence and brief: no buy / sell / hold calls or price targets

**Prompts.** Before this change, `/api/committee`, `/api/lenses`, `/api/intelligence` and `/api/brief` only had MARKET_SYSTEM's
"Do not provide personalized financial advice". The lenses schema even asked for `"verdict":"BUY|HOLD|SELL|MONITOR|IMPLEMENT"`
and a `positionSizing`. bb8o wraps `generateAi` and appends `BB8O_NO_ADVICE` to the system prompt of those four routes only.
A route is recognised by its validator (`validateCommitteeResponse`, `validateLensesResponse`, `validateIntelligenceResponse`,
`validateBriefResponse`). The rule is added once and never reaches Ask, chat, news-scores, the gold desk or the Academy.
The rule: never give a buy, sell, hold, accumulate, trim, add, reduce, avoid, overweight, underweight, outperform, strong buy,
go long or go short call, a rating, a price target, a fair value, an upside or downside level, entry / exit / stop levels
or a position size. Describe facts, risks and what to watch. Verdict / recommendation / rating / action fields are a neutral
takeaway (a lens verdict is MONITOR).

**Output filter (`bb8oAdviceBody`, response layer, status 200 only, error bodies untouched).** It is a sentence-level drop,
in the same spirit as bb8i's speculative-claim drop. bb8i's filter tests a different claim, so it isn't reused; `bb8oIsAdvice`
is bb8o's own. An advice sentence is removed whole, and the rest of the text, its line breaks and its bullets stay as they were.
- Matched: imperative calls ("Buy/Sell/Hold/Accumulate/Trim/Reduce/Avoid/Add/Rotate/Rebalance/Overweight …", "Go long/short",
  "Take profits", "Consider buying …", including after "Label:" or "**Verdict:**"); modal advice ("you / investors / we should
  buy …"); "we recommend / suggest / rate …"; rating calls ("rating is Strong Buy", "is a buy", "upgraded to Outperform",
  "move to overweight"); "buy the dip / on weakness"; "good time to buy", "entry point"; position sizing ("allocate 5%",
  "keep position size …", "starter position"); targets and valuation levels ("price target", "target of $X", "fair value of
  $X", "upside to $X", "25% upside", "stop-loss at $X", "$X target").
- Not matched (tested): "insiders sold", "buybacks", "sell-off", "selling pressure", "funds bought", "gold held steady",
  "holders of the notes", "short interest rose", "underperformed the SOXX", "Technology is overweight at 45% of the portfolio",
  "NVDA added 3%", "the Fed will hold rates", "hedge funds sold", "investors rotated into bonds", "add to that …".
- Fields covered: every string, at any depth, of `/api/committee` `content[].text` (JSON: parsed, filtered as a tree,
  re-serialised; plain text: filtered line by line), `/api/lenses` `lenses[]` (`analysis`, `role`, `verdict`) and
  `intelligence` (`verdict`, `bullCase`, `bearCase`, `actionPlan`, `positionSizing`, `keyDisagreements`, `catalysts`, `risks`),
  `/api/intelligence` `intel` (`headline`, `insight`, `anomalies`, `actions[].label/value`), and `/api/brief` `brief`
  (`headline`, `summary`, `houseView`, `risks`). Identifier fields (ticker, tk, symbol, type, id, priority, severity, sentiment,
  documentType, company, date, focusTickers) and numbers are left alone.
- A bare rating label in a verdict / recommendation / rating / houseView / action field becomes `MONITOR`, the schemas' own
  neutral value. Prose emptied by the filter becomes "No takeaway beyond the facts above.". A string list keeps its other items
  and gets the neutral line only if nothing is left. An action, chip or rebalance item whose `label` / `action` / `point` was
  advice is dropped whole, because its `value` would point at the advice. If every item goes, one is kept with its neutral fields.
- **Takeaway.** Every object with a `recommendation` or `verdict` also gets `takeaway`, holding the same filtered text
  (`recommendation` first). The old keys stay, for compatibility. Headings "Recommendation" / "Verdict" (markdown `#`, `**…**`, or
  a line start before ":") become "Takeaway". An emptied section keeps its heading with the neutral line.
- Not changed, for Jack to decide: brief `overweight[]`, which is a theme list (Gold, Treasuries) shown under an "Overweight"
  label; the gold desk scenarios (`entry`, `invalidation`, `targets`, labelled "Conditional research scenario — not investment
  advice"); the client-side committee prompts in app.js, which ask for "rebalance" actions, "tradingImplication" and
  "BULLISH_SETUP / WATCH / CAUTIOUS" verdicts, so the server filter catches the advice they produce. Client labels such as
  "Recommendation" / "Verdict" are Frontend's job.

Replay (box, stub model that deliberately writes advice and targets; no real model key is on the box): lenses,
intelligence, committee (earnings, document, portfolio and plain-text prompts) for MU and NVDA, plus the brief. Before: 73
advice sentences. After: 0. All 147 factual sentences were kept; the only things removed besides advice are the dropped action
items and the renamed headings. Those routes now differ from bb8p on purpose; every other route still replays byte-identically.

## Tests

`node --test test/bb8o.test.js`: 16 tests, offline, using vm with stubs. They cover items 1–5, Taiwan, ratings (target keys
global; generic keys on allowlisted routes only, with 10 non-market routes keeping `rating`/`ra`/`recommendation(s)`; AI body
context sanitized while messages, question and userThesis stay byte-identical; a stub model capturing the prompt) and section 7 (29 advice and 24 factual sentences, every field of the four routes, takeaway, labels, the
prompt rule on those routes only) and protocol
(bb8o prefix, no timers, anchors, the BB8P_JS_END position, REFUSE, `--check`, bb8p code untouched).

Box replays (stub DB/session, stubbed Stripe client, real Stripe never called): `/api/me` (admin, free, none),
`/api/academy-daily` (quiz, plus `?diag=1`), GET/PUT `/api/prefs`, `/api/account/export`, `/api/admin/content` (5 views plus a 403),
`/api/public/content` (3), `/api/ai-status` (admin plus a 403), `/api/admin/ai-readiness`, `/api/admin/market-data`, both
admin alert routes, `/api/openbb/status`, `/api/stripe-status`, `/api/health`, and `/api/stripe/webhook` twice. All 32 steps
were byte-identical to bb8p, and the webhook stub received the same event bytes (sha256 85da9b0b…6e43). Editorial content keeps
`rating/ratings/ra/recommendation(s)`. Prefs drop them on both builds, which is base `rt17SanitizePrefs` behaviour.
