# bb8c: /api/financials time cap and single Yahoo re-auth

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

## Limits respected
No new tables, intervals, dependencies, secrets, paid feeds or Stripe changes. All new functions use the `bb8c` prefix.

## Known client-side limitation (no client change in this patch)
app.js stores the first `/api/financials` response in `_finCache` for the whole session, and that includes a partial one. Until the page reloads, that tab keeps the partial data even after the server cache has filled. A follow-up client patch could skip caching when `meta.partial` is set.

## Tests
`node --test test/bb8c.test.js` runs offline with stubs and takes about 22s, because one test uses real 6s delays.
