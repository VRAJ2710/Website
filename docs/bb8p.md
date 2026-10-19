# bb8p: grounding guard for Ask Dispatch (P0, QA chat75)

Hotfix, server only, stacked on bb8n (live server.js md5 `9b48a917c654891a50e7c7c6bd8c9a49`, 16308 lines).
Ships before bb8o. Python patch `deploy/patch_bb8p.py`, Jack's deploy protocol: 26 anchors, an md5 mismatch only
warns, a second run prints `REFUSE: bb8p already applied` and exits 0, CRLF safe, `node --check` must pass,
`--check` is a dry run, it prints md5s and line counts and takes the folder as its argument. app.js and index.html
are not touched. No setInterval/setTimeout, no new tables, no secrets, no billing changes, free data only.

Applied to `dispatch-live64w`, the result is `server.js` md5 `92cdce800208671ab32ded68d15e24d1`, 16956 lines.

## 1. Root cause: the stream and JSON paths gave the model different instructions

* **Stream** (`bb3bStreamInner` → `bb2System` → `bb2Complete`): the system prompt never had `MARKET_SYSTEM`'s
  rules or the JSON route's "Answer using ONLY the context..." line. bb8j/bb8k/bb8m harmonised sources, hints,
  length and scope, but not grounding. The detailed LENGTH rule ("aim for 120–200 words") pushed the model to
  fill space, so on "What did the latest China GDP data show?" it made up 4.5% and 4.2% and causes.
* **JSON** (`?stream=0`): had the grounding line, but the openai slot cut the system prompt at 5000 characters
  (`clipped(options.system, 5000)`), so the end of the prompt (CITABLE SOURCES, scope rules) was dropped. It also
  had a server-side gold `LIVE MARKET DATA` block that stream never got.
* **Sources**: stream took the client's `sources` (whatever headlines were on screen: France, Putin, West Bank,
  Kenya...) and padded the footer with them, whatever the question was about.

## 2. Fix

1. **One grounding rule on both paths.** `BB8P_GROUND` goes first in the final system prompt for
   `bb2OpenAi`, `bb2Gemini` and `bb3bGenerateAi`, so both paths and both providers get it. The JSON chat clip is
   raised from 5000 to 14000 (`BB8P_CLIP`, the same as stream's `bb2Clip`). Gold questions on stream now get the
   same server `LIVE MARKET DATA` block (Yahoo v8 chart GC=F) that JSON already used.
2. **Hard numeric guard** (`bb8pKeep`, wired in through `bb8iKeep`, so it runs after the model and **before** the
   bb8m brief trim and bb8n prune, on both paths). Every figure in a sentence is pulled out (`bb8pNums`): %,
   currency amounts, bp, multiples (x), plain decimals, dates. Then it is checked against the "haystack"
   (`bb8pHayOf`): the final system prompt, the user/context messages, the body context, source details, the move
   lead, the server live block, the facts, and the move-pack/quote prices (p, prev, change, high, low; per the bb8o
   note these are always context values) plus the related quotes. Matching (`bb8pMatch`) normalises form
   (4.5% = 4.50%, $4,186.40 = 4186.4 = $4,186) and allows rounding to the decimals the answer shows. It does not
   round across classes loosely (2% does not match a 2.23 beta). bp and % match each other only when scaled. Exempt:
   `[n]` markers, years and dates that appear in the context, numbers that come from the question, small bare
   integers (<10), times, index names (S&P 500, FTSE 100), tenors (10-year, 5 years) and Q3/H1/FY labels. Any
   sentence with an unsupported figure is dropped. So is a follow-on "This/That/It ..." sentence after a drop, and
   a cause sentence ("driven by", "due to"...) that cites no source. Every drop is recorded with the reason
   (`st.bb8pDrops`, shown to admins in `meta.grounding.drops`).
   * **Honest no-data answer** (`bb8pFallback`): if lines were dropped and there are no facts, no move lead, fewer
     than 25 words left and no supported figure, the answer becomes: "We don't have China GDP figures in our data
     feed right now, so this answer does not quote any." + kept text + relevant headlines + related live moves
     from Yahoo Finance (China: USD/CNH, Hang Seng, copper; UK: GBP/USD, FTSE 100; US: S&P 500, 10y, DXY; ...)
     with `[n]` + In short + sources rebuilt from what was cited. Card/move answers never take this path.
   * **Stream painting**: deltas are held and painted in units (`bb8mUnits`). A unit with an unsupported figure is
     never painted, and a cut-off numeric fragment at the end is held back. The `done` event's final text still
     replaces the painted text, as before.
3. **Source relevance** (`bb8pTopic`/`bb8pRelevant`, through `bb8jSources` and `bb2ClientSources`). The question
   is matched to entity groups (China, Japan, UK, US, euro area, Germany, France, India, Korea, Asia, gold, silver,
   oil, copper, crypto, dollar) and series (GDP, inflation, jobs, rates, PMI, retail, trade, housing). If both are
   named, a headline must match both. With only one, it must match that one. In ticker mode it must match the
   ticker, company or sector words. If there is no topic, nothing changes. No padding: the footer lists only
   cited sources, and the server's own price/quote sources are always kept.
4. **provider/model only for admins.** `POST /api/chat` checks `isAdminUser(await currentUser(req))`, the same
   check `/api/ai-status` uses, and fails closed. For non-admins, `meta.provider` and `meta.model` are removed from
   the JSON body and from every SSE `data:` event (meta and done). Admins still see them. No tier strings.
5. **meta.quote** (P1 gold feed, below) and **meta.grounding** `{dropped, noData, sourcesDropped}` (admins also get
   `drops`).
6. **Brief keeps the timeframe** (`bb8pKeepTf` wraps `bb8mTrim`). If the question names today / this week / this
   month..., the sentence with that timeframe is kept by the brief trim.

## 3. Gold feed (P1): header $4165.60 vs answer/chart $4,186.40

Three different feeds:

| Surface | Feed | Basis |
|---|---|---|
| Header tape XAU | gold-api.com spot (`RT_GOLD_URL` in the browser, `fetchGoldProxy` on `/api/market-reference-quotes`) | spot. It has no previous close (c:0, prev = price), so the client takes the % change from GC=F futures (`_rt.gcPct`) |
| Ask card / quote pack | Yahoo quote GC=F (`bb3Quotes`/`bb5dYahooQuote`) | Dec 26 COMEX futures, 10 min delayed |
| JSON live block + chart | Yahoo v8 chart GC=F (`buildChatLiveMarketBlock`, `/api/yahoo-chart`) | the same futures, daily bars |

Probe, Mon 19 Oct 11:57 UK: GC=F 4184.00 vs gold-api spot 4171.70. The ~$12–20 gap is the futures–spot carry,
not a bug in any one feed. The header shows spot alongside a futures % change, which mixes the two.

**Recommendation:** make Yahoo GC=F the one canonical XAU for price, previous close, change, chart and Ask, with
the label "Gold futures (GC=F, delayed 10 min)". Or keep spot and label each surface "spot" or "futures". bb8o's
per-symbol status/age (q.session, q.feed, q.fallback) fits straight into `meta.quote` (bb8p already reads
`q.session`, `q.fallback` and `q.fallbackReason` when they are there, and does not depend on them).

`meta.quote` fields: `symbol, feedSymbol, name, price, change, prevClose, currency, asOf (ISO), asOfUk, source,
feed, session, fallback, fallbackReason, delayMin`, taken from the card pack quote, else the gold live block
(`feed: "server buildChatLiveMarketBlock (Yahoo v8 chart GC=F 3mo/1d)"`), else the client tape gold.

## 4. Known, not changed here

* The brief trim can drop the beta line on "What is Micron's beta?" (brief; same before and after).
* On stream, the bb8m brief inner layer can glue raw chunks to the corrected text while painting. The final text
  replaces it.
* The detailed stream answer loses paragraph breaks; JSON gold "Live:" prefix has no full stop.
* Move-pack availability depends on live Yahoo latency. When the pack misses, the card lead is absent on both
  before and after (bb8p then gives the honest answer rather than the model's figures).

## 5. Tests

`node --test test/bb8p.test.js` (offline, vm): protocol/names/forbidden code, guard cases (China invented
figures, rounding, forms, dates, question numbers, bp), keep/drop reasons, relevance, fallback text and cites,
timeframe trim, meta strip/quote, grounding rule and clip.
