# bb8q: one shared grounding context, cited figures, gold spot headline (P0)

Stacked on bb8p (PR #67). The base is the live server.js, md5 `92cdce800208671ab32ded68d15e24d1` (16,956 lines).
The change is server-only: `deploy/patch_bb8q.py` follows the deploy/ protocol (anchor-based, an md5 mismatch only
WARNs, a second run REFUSEs and exits 0, CRLF-safe, `node --check`, `--check` is a dry run, takes a folder argument).
It adds no timers, tables, secrets or paid feeds. All data is free (Yahoo quote/chart, gold-api.com spot).

## What QA saw (bb8p retest) and why

| Symptom | Root cause |
|---|---|
| Regime 37/100, SPX −1.09%, VIX 18.65 quoted with 0 sources | The two paths grounded on different text. The JSON route prompt carried `buildChatLiveMarketBlock()` and the stream carried the page payload. Neither block was a source, so a correct figure still had no [n], and bb8p's guard only checked that a figure appeared *somewhere* in context. |
| 10Y 5.10% | Correct. Yahoo `^TNX` is quoted in percent (5.098 = 5.10%), and no ÷10 scale is applied anywhere on the server. This was checked against the raw quote. It was flagged only because it had no source. |
| DXY 101.81 −0.05% vs context 101.80 +0.03% | These are two instruments. The page and header use the FX-computed index (`dxy-fx-computed`, its previous close also computed from FX), while the JSON prompt used Yahoo `DX-Y.NYB`. Each sign was right for its own instrument, but they disagree intraday. Ask now quotes only `DX-Y.NYB`, with the change recomputed from that symbol's own price and previous close. |
| Gold page spot 4,170.30 below "day low" 4,176.00 | The day range was GC=F futures (about $20 above spot) shown next to gold-api spot. The client also borrowed GC=F's % change when spot's change was 0. |
| UK inflation stream answer dodged the question | There was no CPI series in the feed and the no-data rule ran only on the JSON path. |
| XAU card Brief = Detailed, no "this week" | The card-move template ignored the length hint and had no timeframe data. |
| No stream meta event | The stream sent meta only inside `done`. |

## Design

* **One context per request.** `bb2Read0` is the body read that both `/api/chat` paths use (the JSON `readBody` wrapper and
  the stream's `bb3bStreamInner`). bb8q wraps it once and builds `st.bb8qCtx = { facts:[{id,text,src}], sources, gold, spot, fut, tf, tfMore, regime, topic }`
  with a 2.5 s budget (`bb8Late`, request-driven).
  * Facts include the regime (`Dispatch regime model`, ours, https://thedispatch.uk/markets/), S&P 500 `^GSPC`, VIX `^VIX`, DXY `DX-Y.NYB`
    and US 10Y `^TNX`, each with its Yahoo quote URL.
  * Gold questions add gold spot (gold-api.com) and gold futures (GC=F, labelled "delayed 10 min").
  * Topic proxies: China uses `USDCNH=X`, `^HSI`, `HG=F`. UK CPI/inflation uses `GBPUSD=X`, `^FTSE`.
  * Timeframes: this week, today, this month and YTD come from free Yahoo daily bars (1y/1d).
    Week-to-date runs from the last close before this week's Monday (last Friday's close) to now.
  * The same sources are appended to `bb8jSources` / `bb2ClientSources`, so the stream's CITABLE SOURCES, the JSON fill's list
    and the final footer number them the same way. The prompt block is `SERVER DATA (…)`, with each line tagged with its [n] in that path's list.
* **Citation rule (extends bb8pKeep).** Every kept figure needs a valid [n] that points to a source containing it.
  If no [n] is given and exactly one source contains the figure, its [n] is attached. Otherwise the sentence is dropped.
  The ambiguity tie-break goes by name (spot/futures/DXY/10Y/regime/proxy).
  Exempt: years, small counts under 10, the question's own numbers, and server-authored lines.
  `meta.grounding` gains `uncitedDropped`, `citesAdded` and `sharedFacts`.
* **No-data first (both paths).** When the question names a series we do not hold (China GDP, UK CPI…), the reply opens with
  "We don't have <series> in our data feed right now, so this answer does not quote any." This is followed by
  "What we do have, from Yahoo Finance as of …: <proxy quotes with [n]>", up to two relevant headlines labelled "a headline, not our data", and
  "In short: no <series> in our feed; related live markets are above." The model's own "not in our feed" sentences give way to this.
  The stream also paints the opener first.
* **UK 10Y gilt.** No free Yahoo symbol was found. Tried: `GB10Y=RR`, `GB10YT=RR`, `^GUKG10`, `TMBMKGB-10Y`, `GBGB10YR=X`,
  `UK10Y=RR`, `^UK10Y`, `GB10Y=X`, `^GB10Y`, `TNX-GB`. All return no quote, so none is used.
* **Card move.** Brief keeps the head, the gold spot line (or the first price line), the timeframe line (or the line that best
  answers the question) and In short. Detailed adds "For context:", which holds the other timeframe windows, futures 5/20-session
  ranges, regime, DXY and 10Y, each cited.
* **B1.** `bb8mTrim` keeps the sentence that best answers the question (e.g. the beta line for "What is Micron's beta?").
* **B2.** General stream answers are painted from the raw model text, one whole sentence at a time, after every line rule, with
  the model's paragraph breaks. These travel as `bb8eNextSep`, because the stream's line rewrite trims bare whitespace. Detailed final text
  keeps blank lines between paragraphs.
* **B3.** The JSON "Live:" gold prefix is replaced by one cited line that ends in a full stop:
  `Live: Gold spot is at $… [n]; gold futures (GC=F, delayed 10 min) are … [m].`
* **B4.** When `bb8eMovePack` misses its budget, the last pack for that name (in memory, request-driven, up to 24 h) is used.
  Its lines keep their own as-of. `meta.quote.cached = true` and `meta.quote.cachedAtUk` are set.

## Gold (Jack's decision): field shapes for Frontend

gold-api spot is the headline gold price everywhere on the server: cards, Ask `meta.quote`, answer price sentences, and
`/api/market-reference-quotes` (`XAU`). Its change uses only spot's own previous close. That close is the last spot price the server
saw before the UK day rolled. It is held in memory and request-driven, so it is empty after a restart until a UK day has rolled. When it is missing,
change fields are `null` with a flag. The day range from the spot feed is not available, so it is `null`. The futures range is labelled.

`/api/market-reference-quotes` → `XAU`:
```json
{ "p": 4160.70, "c": null, "prev": null, "change": null, "changePct": null, "prevClose": null,
  "changeAvailable": false, "noPrevClose": true, "prevCloseSource": null,
  "dayHigh": null, "dayLow": null, "dayRangeAvailable": false,
  "name": "Gold spot", "label": "Gold spot", "feed": "gold-api.com spot (api.gold-api.com/price/XAU)",
  "source": "gold-api-spot-proxy", "currency": "USD", "ts": 1792411410,
  "futures": { "symbol": "GC=F", "label": "Gold futures (GC=F, delayed 10 min)", "price": 4189.4,
               "dayHigh": 4211.2, "dayLow": 4176.0, "asOf": "…Z", "source": "Yahoo Finance" } }
```
After the UK day roll: `prev`/`prevClose` = previous spot, `c`/`changePct` = % from it, `change` = $ change, `changeAvailable: true`,
`prevCloseSource: "last gold-api spot seen before the UK day roll (YYYY-MM-DD)"`. `futures` is present only when a GC=F
snapshot from the last 6 h exists.

**Frontend:** when `changeAvailable === false`, show no change. Do not borrow GC=F's % (`app.js _rt37Ref` does this today).
Label any day range taken from `futures` as futures.

Ask `meta.quote` for gold:
```json
{ "symbol": "XAU", "label": "Gold spot", "name": "Gold spot", "price": 4167, "currency": "USD",
  "change": null, "changePct": null, "prevClose": null, "changeAvailable": false, "prevCloseSource": null,
  "dayHigh": null, "dayLow": null, "dayRangeAvailable": false,
  "asOf": "2026-10-19T11:57:59.000Z", "asOfUk": "Mon 19 Oct, 12:57 UK",
  "source": "gold-api.com", "feed": "gold-api.com spot (api.gold-api.com/price/XAU)", "session": null,
  "futures": { "symbol": "GC=F", "label": "Gold futures (GC=F, delayed 10 min)", "price": 4189.4, "prevClose": 4181.1,
               "changePct": 0.1985, "dayHigh": 4211.2, "dayLow": 4176, "asOf": "…Z", "asOfUk": "Mon 19 Oct, 12:48 UK",
               "source": "Yahoo Finance", "delayMin": 10 } }
```
Non-gold quotes keep the bb8p shape. A cached move pack adds `cached: true, cachedAtUk`.

## Stream meta event

The stream now sends exactly one meta event before `done`:
```
data: {"meta":{"quote":{…|null},"grounding":{"dropped":0,"noData":true,"sourcesDropped":12,"uncitedDropped":2,"citesAdded":3,"sharedFacts":["regime","^GSPC","^VIX","DX-Y.NYB","^TNX","proxy:USDCNH=X",…]},"streamed":true}}
data: {"done":true,"reply":"…","meta":{…same…},"sources":[…]}
```
`provider` and `model` appear only for admins (`isAdminUser(await currentUser(req))`). The meta event copies the
already-stripped `done` meta. The client parser reads `t`, `done` and `error` and ignores other events, so this is backward-compatible.

## Known limits

* Spot change stays `null` until the server has seen a UK day roll (in-memory, no job). This is by design.
* The header's DXY (`/api/market-reference-quotes` → `DXY`) is still the FX-computed index, and Ask quotes `DX-Y.NYB`.
  Both are self-consistent. Unifying the header is a separate product call.
* The card's In-short % uses the move pack's GC=F quote, and the timeframe line uses the chart's last price. They can differ by 0.01 pp.
