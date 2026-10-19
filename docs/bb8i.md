# bb8i: speculative-claim filter and insiders stale-on-failed-refresh (server only)

Stacked on bb8h (server.js md5 `dabd441e6cd87c6ce828601861142798`, 14762 lines). After the patch: md5 `eb6937c7284919ed1a86f7e9d8b87d9c`, 15051 lines.
The patch appends one block (`// ── bb8i ──` … `// BB8I_JS_END`). app.js and index.html are not touched. It adds no tables, intervals, timers, dependencies, secrets or paid feeds.

Apply: `python3 deploy/patch_bb8i.py <folder> --check`, then `python3 deploy/patch_bb8i.py <folder>`. Running it a second time prints REFUSE and exits 0.

## (a) Speculative and attributed claims
- **What counts:** a sentence that attributes a view or speculates. Examples: "analysts / investors / traders / the market / many … see, expect, believe, are favoring, are pricing in…", "is likely to", "likely / poised to", "could / may see, benefit, rally…", "stands to", "reflects … optimism/expectations", "sentiment is…". Such a sentence is kept only if one of its `[n]` cites points at a **news** source whose headline shares the sentence's ticker or topic words.
- **What is not news:** quote lines, key-statistics and P/E lines, the peer source, beta lines and The Dispatch's own card all fail the news check.
- **Plain facts stay:** factual sentences that say "expected" ("MU's next earnings are expected on 18 Dec [1]") are not matched and are kept.
- **Whole sentences only:** the drop removes the whole sentence, using the bb8d splitter. It runs after the bb8h citation matching and before the server's "In short".
- **Where it applies:**
  - Card and valuation answers go through `bb8dCleanLine`, on both the stream and JSON paths.
  - General answers (no card or facts) are filtered line by line and sentence by sentence as they stream, then again on the final compose, and Sources are renumbered through bb8e.
- **The model is told:** `BB8I_RULE` is added to the Ask system prompt.
- **bb8h interaction:** bb8h's no-figure rule needed a shared ticker. A cite to a news headline sharing the sentence's topic words ("Analysts expect Micron shares to rise…" → "Micron shares rise…") now also counts as a match, so the cite survives to this check.
- **Bug fix along the way:** the bb3b pump dropped the newline at the end of a delta, which glued general-answer lines together ("forecasts [1].Analysts"). bb8i composes the final general reply from its filtered text, so the lines stay separate.

## (b) Insiders, premium only: stale instead of partial when a refresh fails
- **When it applies:** a premium refresh fails mid-scan (bb8h `meta.more: "retry"`, or SEC errors) while an older complete `f4:T` entry exists.
- **What is served:** the complete entry, with:
  - `stale: true` and `meta.stale: true`
  - `X-Dispatch-Data-Status: stale`
  - `meta.statusLabel` and `meta.window.note` set to `Updated <bb8dUk time> · refreshing`
- **The cache:** the complete entry stays in place and is never overwritten by the partial.
- **Approach chosen: request-driven, with no timers.** After a failed refresh, the next refresh is allowed only on a request arriving after the backoff: 60 s, doubling each time, capped at 15 min. Requests inside the window get the stale entry instantly with 0 SEC calls. Concurrent requests share one in-flight refresh (`bb8iFlight`). A successful refresh clears the backoff and serves fresh.
- **Unchanged:**
  - The free tier (`f4:T:free`).
  - With no complete entry, bb8h's partial and retry behaviour.
