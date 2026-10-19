# bb8b: Ask cold-cache facts, replayed-answer cleanup, fundamentals symbol fixes

Server-only patch `deploy/patch_bb8b.py`, stacked on bb8 (server md5 `c5cdaf0eb4cdee4daed380e57d2a1522`). The client is unchanged. No response fields were removed.

## Ask P1: the MU Pulse "Ask →" still got the old answer

There is no server-side answer cache. The only `data-cache/*.json` files are the CoinGecko last-good file and bb7 insiders. The valuation cache (`bb2Mem`) and fundamentals cache (`RT32.cache`) are in memory only. The old answer came from the cold path of the stream handler (`bb3bStreamInner`):

1. On a cold server the peer valuations are not cached. The handler started the Yahoo refresh, raced it against an **800 ms** timer, and built the system prompt straight away. The model therefore got **no FACT lines**, and the late lead was dropped once the timer won. bb8 made the refresh slower because it also fetches next-12-month EPS, so the timer lost almost every time on a cold start.
2. With no facts, the bb8 conclusion fix had nothing to work from. The model copied two things the client sends:
   - the terminal context, with forward P/E taken from the browser's `/api/financials` data loaded before the deploy (`forward P/E 4.2x`, `13.5x`);
   - the chat history stored in the browser, which replays the earlier "cannot directly compare" answer.
3. "as of 2026-10-16 20:00 UTC" is the Yahoo market time of Friday's close. It was correct, not stale.

Fix:
- The handler waits up to 3 s for the peer refresh before building the prompt, so the facts are in the prompt and the lead streams first. If the facts are still missing, it waits up to 4 s more after the model finishes and builds them then. The final reply always gets the lead, the bb8 conclusion and the next-12-month labels.
- Client context lines with a forward P/E are rewritten to the server's next-12-month figure (`forward P/E (next 12 months) 4.9x`), or `forward P/E not available` if the server has none.
- Earlier assistant turns sent back by the client get the same forward P/E rewrite. Their "cannot compare" sentences and filler are removed before they reach the model.
- Valuation cache entries are tagged `bb8b`. Untagged entries are ignored, so a future logic change can bump the tag to invalidate them.
- Generic filler ("This valuation metric provides insight into…", "Investors often use…", "The P/E ratio is a common…") is dropped. This happens in the prompt and in post-processing. Sentences with a number or a ticker are never dropped.
- A "Sources:" line written by the model is stripped, and the server footer always starts with a blank line.

## Fundamentals

- Non-US listings were sent to Yahoo with the dot changed to a dash (`BP.L` became `BP-L`, which returns 404), so BP.L had no valuation or earnings. Because the result was "unavailable" it was never cached, and every page load retried. Listings with an exchange suffix (L, HK, T, DE, PA, TO, AX and others) now keep the dot and skip the SEC lookup. US share classes still use a dash (`BRK.B` becomes `BRK-B`).
- Concurrent `rt32Build` calls for one symbol now share one in-flight build. This covers Ask's peer lookups, which bypassed the route's in-flight map.
- The 36 s cold load is not reproduced. Structurally, the Yahoo path makes up to 6 serial calls when the crumb is expired: fc.yahoo, getcrumb, quoteSummary returning 401, then the same three again. Each call has an 8 s timeout. With every call taking 6 s that is 36 s, measured with stubs. An overall 8 s cap with a partial result was deferred on Jack's guidance, because it needs a route-level response change.
