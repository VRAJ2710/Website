# bb8n: no beta or card score for non-equities; Sources list only what is cited

Stacked on bb8m (PR #63). Base `server.js` md5 `464c5b95c3079b067a840b5b0a8fde25` (16079 lines). The patch is server-only and adds one appended block (`// ── bb8n ──` … `// BB8N_JS_END`). `app.js` and `index.html` are not touched.

```
python3 deploy/patch_bb8n.py <folder> --check   # dry run
python3 deploy/patch_bb8n.py <folder>           # apply; a second run prints REFUSE and exits 0
```

The patch follows the usual protocol. Every anchor must match exactly once, or it aborts and writes nothing. An md5 mismatch only prints WARN. The patch is CRLF-safe and runs `node --check` before it writes. It prints md5s and line counts before and after. It adds no timers, DB tables, npm dependencies, secrets or paid feeds.

## (a) Equity check

Before bb8n the server had no equity test. Card and move answers loaded bb8h's Yahoo beta and the Dispatch card fit for every base. That is why the XAU card printed "published beta is 0.00" and "Card score 65/100".

`bb8nKind(base)` returns `{ equity, kind, via }`. It checks in this order:

1. **Symbol patterns.** These need no network. The checks use the Yahoo symbol from `bb3Yahoo`/`BB3_ALIAS` and the base itself:
   - `XAU`/`XAG`/`XPT`/`XPD` (± `USD`) and `GC=F`, `SI=F`, `PL=F`, `PA=F`, `HG=F` → **metal**
   - `…=X` or a six-letter currency pair (EURUSD, GBPUSD, USDJPY …) → **fx**
   - Other `…=F` → **future**; `ZN`/`ZB`/`ZF`/`ZT`/`GE`/`SR3=F` → **rates**
   - `^…`, `DX-Y.NYB`, and index names (SPX, FTSE, DAX, VIX, DXY …) → **index**; `^TNX`/`^TYX`/`^FVX`/`^IRX` and `US10Y` → **rates**
   - `…-USD`/`-USDT` → **crypto**
   - BB3 rows with `cat` `crypto` or `commodity` → that kind
2. **Yahoo `price.quoteType`.** This applies when the patterns cannot tell. It comes from the `quoteSummary` the card already loads through `rt32Yahoo`, and it shares bb8l's in-flight call. The wait is at most 2.5 s through `bb8Late`.
   - `EQUITY` and `ETF` count as equity.
   - `CURRENCY`, `CRYPTOCURRENCY`, `INDEX`, `FUTURE`, `MUTUALFUND`, `MONEYMARKET`, `OPTION` and anything else count as non-equity.
3. **Neither pattern nor quoteType.** The asset is treated as an equity, which was the behaviour before bb8n. The beta must still be finite and non-zero.

For a **non-equity**:
- The move pack drops `fit` and `bb8hBeta`. The lead therefore has no "Card score (Dispatch regime fit)" line, no beta line and no "The Dispatch" score source, and none of these reach the prompt.
- The header becomes "X's latest move, as of …".
- bb8h's "Only the Yahoo Finance line may be called beta" rule is replaced with "not an equity: do not mention a beta, a card score or a regime-fit score".
- The client context `Active ticker:` line loses `· Score N/100` and `· Beta x`.
- Model sentences that restate a beta, a card score or a regime fit are dropped by the shared sentence filter (`bb8dDrop`) on both paths. A symbol-only flag is set in the hints hook, so the filter holds even when the move pack is late.
- Sentences that cite the market regime (`Risk-Off 32/100`) or Fear/Greed, and sector labels such as "high-beta tech", are kept.

For an **equity**, a missing, zero or non-finite beta is dropped, and the context `Beta 0.00` or `Beta —` is removed. MU keeps the Yahoo beta line (2.23) and its card score.

Free-form gold questions keep bb8m's live-gold answer. The XAU card appears only for the card prompt.

## (b) Sources list only what is cited

`bb8jAssemble` is the shared assembler for the stream `done` event and the JSON reply. After every filter and the bb8m length trim, it calls `bb8nPrune`, which:
- keeps only the sources the body cites (the In short line included), in order of first appearance;
- renumbers them 1..n and rewrites every `[n]` and `[a, b]` group;
- removes markers that point at nothing;
- returns the pruned list as `sources` and as `st.bb8jSources`, which is the JSON top-level `sources` (`bb8kSources`).

On the stream, `app.js` replaces the painted text with `done.reply`, so the final text and Sources always match. Painted numbering never survives.

- **No cited source:** the list stays as the earlier patches left it, and only the markers that point at nothing are removed.
- **Footer and source array disagree in length:** the answer is left alone.
- **Brief trim cuts every cite:** if the plain bb8m brief trim would remove every cited sentence (an answer that opens with uncited context), bb8n keeps the first cited sentence within the 80-word budget, so the brief answer still cites a source.

## Limits

- ETFs keep beta and score, because Yahoo publishes both for ETFs.
- An unknown symbol with no quoteType in time is treated as an equity, and its beta is still checked.
- For equities whose beta comes from bb5's memory cache, the quoteType check may add one Yahoo quoteSummary call. Otherwise it shares the call the card already makes.
