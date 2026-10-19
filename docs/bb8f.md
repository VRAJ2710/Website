# bb8f: one shared SEC limiter (at most 10 request starts in any rolling 1000 ms)

Server-only patch, stacked on server.js md5 `3fb9d02cb61081cec1d58484b1aef905` (bb8e). Apply with
`python3 deploy/patch_bb8f.py <folder>` (`--check` is a dry run). It adds no tables, intervals, dependencies, secrets or paid feeds.
`app.js` and `index.html` are not changed.

## What goes through it
Every request to `*.sec.gov`, whichever helper builds it:
- bb7/bb8 insiders: `company_tickers.json`, `submissions/CIK…`, Form 4 documents, the raw-XML fallback and the bb8 retry pass.
- rt32 fundamentals: `rt32CikMap` (`company_tickers.json`) and `companyfacts`.
- bb8c financials: `bb8cSec` companyfacts.
- `secText` / `rt52SecBig`: the 13F and legacy Form 4 paths. The existing 80/min `secRateLimiter` still applies on top.

It does this by wrapping `globalThis.fetch` for sec.gov hosts only. Other hosts pass straight through.
`bb7FetchBuf` routes its sec.gov calls through the same queue (bulk lane) and no longer uses the old `bb7Pace` bucket.

## How it works
- `bb8fStarts` holds the start times of the last 10 requests. A request starts only when fewer than 10 starts fall in the last 1000 ms, plus a 2 ms guard.
  The start is stamped in the same synchronous step that calls fetch.
- Waiters queue FIFO in two lanes: interactive (financials, ticker map, 13F) first, then bulk insider Form 4 fills.
  One `setTimeout` at a time wakes the queue when the oldest start leaves the window. There is no `setInterval`.
- A queued request leaves the queue with an error when its own `AbortSignal` fires (rt32Get 8 s, secText timeout) or after 30 s.
  The 8 s insiders and 7.5 s financials races are unchanged, so partial results still come back on time.
- User-Agent headers are unchanged: each caller sends its own.

## Root cause of "max 11"
1. **Stamp before start.** `bb7TakeToken` stamped `bb7Now()` when it granted the token. The fetch began only after `await bb7Pace()` resumed.
   Under load, with XML parsing and many microtasks, that was 1–10 ms later.
   So the next wave, admitted 1000 ms after the *token* stamps, began 990–999 ms after the *real* starts: 11 real starts in one second.
   On the e0a1e5ea/3fb9d02c server this happened in 8 of 10 runs of the itest 5d load. The token stamps themselves never exceeded 10.
2. **Paths outside the bucket.** `rt32Get` (company_tickers + companyfacts), `bb8cSec` companyfacts, `secText` and `rt52SecBig` had no per-second pacing at all.
   They only had an 80-per-minute fixed window, which allows bursts.
   Mixed load (5 cold insiders + 5 financials) reached 16 per rolling second before bb8f; it reaches 10 after.

Tests: `node --test test/bb8f.test.js` (mixed concurrent load; both entry points plus retries; abort, queue cap and non-SEC bypass).
