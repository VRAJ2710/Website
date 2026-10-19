# bb8c: /api/financials time cap, single Yahoo re-auth, Ask cleanup on every /api/chat path, quote-unit fixes

Stacked on bb8b (server.js md5 `5683b5b2720ee7ced93b95f69690b81e`). Changes server.js only; app.js and index.html are unchanged.
Run `python3 deploy/patch_bb8c.py <folder>` (or `--check <folder>` for a dry run). A second run prints REFUSE and exits 0. Backup: `server.js.bb8cbak`.

## 1. Time cap with partial results
- `/api/financials`, `/api/earnings`, `/api/statements` and `/api/holders` answer within about **7.5s** (`bb8cBudget`, measured from the start of the shared build).
- If a source is still loading at the deadline, the response contains what is ready and adds:
  - the header `X-Dispatch-Data-Status: partial` with `Cache-Control: no-store`;
  - `meta: { partial: true, pending: ["yahoo" | "sec"] }`, and `sources.<name> = "pending"`.
  Existing fields keep their shape, so `meta` is the only new key.
- If a stale cache entry (>12h) exists, that entry is served instead of a partial (`X-Dispatch-Data-Status: stale`).
- Complete answers carry `X-Dispatch-Data-Status: fresh`. Warm cache hits still use the old path (`Cache-Control: public, max-age=600`).
- The shared in-flight build (`bb8cFlight`, one per symbol) keeps running after the deadline and writes the cache, so the next call comes back complete. Partial snapshots are never cached. A build where a source failed is cached for 10 minutes rather than 12 hours.
- Ask's peer lookups (`rt32Build`, which feeds `rt32Fundamentals`) wait on the same shared build and always get the full result, never a partial.

## 2. Yahoo crumb/cookie expiry
- quoteSummary is tried once. On 401/403 there is **one re-auth, then one retry**. The old path could chain up to 6 calls at 8s each.
- The re-auth first tries `getcrumb` with the existing cookie (1 call). Only if that fails does it go to `fc.yahoo.com` + `getcrumb`.
- Concurrent requests share a single re-auth promise (`bb8cAuthP`). A crumb refreshed in the last 15s is reused.
- Per-call timeouts: auth 6.5s, quoteSummary 7s, and a 20s cap on the whole Yahoo chain.

## 3. /api/chat: every output path
`/api/chat` has two server paths:
- the SSE stream (`bb2StreamChat` → `bb3bStreamInner`), used when an OpenAI/Gemini integration is configured;
- the original JSON handler, with `bb2Finish` in `res.end`, used otherwise.

Both now go through the same steps:
- **Request** (`readBody` and `bb2Read0`, `/api/chat` POST only):
  - In replayed assistant turns, the old "Peer comparisons" block, every sentence that quotes a P/E figure, and the Sources footer are removed. The bb8/bb8b dead-end and filler cleanup runs as well.
  - Forward P/E figures in the client context are rewritten to the next-12-months value, including the `MU's forward P/E (4.2x)` form.
- **Reply** (`bb3bCompose`, which builds both the stream's `done.reply` and the JSON reply): after the bb8 conclusion rewrite, filler removal and blank line before Sources, a body sentence is dropped if it quotes a P/E multiple that does not appear in the precomputed comparison lines. The lead block and the Sources footer are not touched.

## 4. Minor-unit quotes (.L, .JO, .TA)
Yahoo quotes these listings in GBp/GBX, ZAc or ILA. EPS estimates are in the company's financial currency, often USD. Changes:
- The price is divided by 100 and converted to the financial currency before the next-12-months forward P/E is calculated. The FX rate comes from Yahoo's chart for `GBPUSD=X` and similar pairs: the same free Yahoo feed, cached for 6 hours. If the rate is not known yet, forward P/E is `null` rather than a pence-based figure.
- P/B = Yahoo priceToBook ÷ 100.
- P/S and EV/EBITDA use market cap converted to the financial currency.
- Yahoo's trailingPE and dividendYield already use one major unit on both sides, so they are left as Yahoo reports them.
- New valuation fields: `priceCurrency`, `currency`, `financialCurrency`, `fx` and `marketCapCurrency`. `price` and `marketCap` keep Yahoo's values.
- The Ask peer values (`bb2StoreQuote` / `bb8ApplyNtm`) use the same conversion.

BP.L, Yahoo raw data at the 2026-10-16 close: price 614.1 GBp, financialCurrency USD, NTM EPS $0.9714, GBPUSD 1.333.

| | before | after | working |
|---|---|---|---|
| forward P/E | 632.18 | 8.43 | 6.141 × 1.333 / 0.9714 |
| P/B | 217.43 | 2.17 | 217.43 / 100 = £6.141 / £2.824 |
| P/S | 0.440 | 0.587 | (£94.90B × 1.333) / $215.47B |
| EV/EBITDA | 3.80 | 4.60 | (148.78 − 94.90 + 94.90 × 1.333) / 39.20 |
| trailing P/E | 24.56 | 24.56 | £6.141 / £0.25. Check: net income $5.43B / 15.45B shares = $0.351 = £0.263, which gives 23.3x, so no correction |
| dividend yield | 4.08% | 4.08% | £0.25 / £6.141 |

Known limit: Yahoo does not label the currency of `bookValue`. For TEVA.TA it appears to be USD, so P/B there (19.27 after ÷100) may still be off by the FX rate.

## Limits respected
No new tables, intervals, dependencies, secrets, paid feeds or Stripe changes. All new functions use the `bb8c` prefix.

## Known client-side limitations (no client change in this patch)
- app.js restores the chat from localStorage (`td_chat`, version key `chat37`, not bumped since). A tab opened before bb8 shows the pre-bb8 answers as they were saved. The server cannot rewrite text the browser has already stored.

app.js stores the first `/api/financials` response in `_finCache` for the whole session, and that includes a partial one. Until the page reloads, that tab keeps the partial data even after the server cache has filled. A follow-up client patch could skip caching when `meta.partial` is set.

## Tests
`node --test test/bb8c.test.js` runs offline with stubs and takes about 22s, because one test uses real 6s delays.
