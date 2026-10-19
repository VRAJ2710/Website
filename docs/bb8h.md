# bb8h: Yahoo's published beta, [n] citations that match their line, card restatement filter, insiders cap and window

Server-only. Stacked on bb8g (server.js md5 `7d10de541da933783afa032a90a4e57c`, PR #53). `app.js` and `index.html` are unchanged.
To apply: `python3 deploy/patch_bb8h.py <folder>`. `--check` does a dry run. A second run prints REFUSE and exits 0.

## 1. Beta
- **What we found:** MU's 2.23 is Yahoo's own published beta, not a card-score number. It is `quoteSummary` `summaryDetail.beta` = `{raw: 2.226, fmt: "2.23"}`, and `defaultKeyStatistics.beta` gives the same value. The bb5 hooks already load it for the card's sensitivity input, which is labelled "5y monthly beta, Yahoo". The desk table's 1.62 is only used when Yahoo has no beta.
- **What bb8g got wrong:** it labelled this figure "Beta (Dispatch desk reference)" and cited it as The Dispatch.
- **What bb8h changes:**
  - It removes that line. When Yahoo publishes a beta, the card shows `MU's published beta is 2.23 (Yahoo Finance, 5-year monthly), so it has tended to move about 2.23 times as much as the market. [n]` instead.
  - It cites that line as `Yahoo Finance | https://finance.yahoo.com/quote/MU/key-statistics/ | as of <UK time>`.
  - Where the value comes from: bb5's 1-hour cache first. If that is empty, the same free `quoteSummary` call (`rt32Yahoo`), capped at 2.5 s.
  - If Yahoo has no beta, there is no beta line.
  - "The Dispatch" now cites only the card score ("Pulse card score (regime fit)").
- **Prompt:** the model is told that only the Yahoo Finance line may be called beta.
- **Model sentences:** any sentence that calls a number other than Yahoo's a beta is dropped.

## 2. Citation matching (model sentences, stream and JSON)
For each model sentence that carries `[n]`:
- **Sentence has figures:** these are numbers with %, pts, x, /100, currency, or the number a "beta" names, normalised to 2 dp. `[n]` must point at a fact line or source record that contains one of those figures.
- **Sentence has no figure:** `[n]` must instead point at a line that shares one of the sentence's tickers.
- **If `[n]` does not match:** it is re-pointed to the matching server fact line's source, or to any matching source record if no fact line matches.
- **If nothing matches:** the `[n]` is stripped. If the sentence then has no `[n]` and carries a figure that appears in no fact line, the sentence is dropped.
- **After all sentences are checked:** Sources are pruned and renumbered by the existing bb8e/bb2Footer path.

## 3. Card answers: no restating prose
- **Which model sentences are kept:** after the matching in section 2, a model sentence on a card answer survives only if it still carries an `[n]` and restates none of the bullet figures. These are the figures found anywhere in the lead lines: the move %, the SPY and SOXX moves and gaps, the card score, the beta, prices.
- **What is dropped:**
  - Uncited interpretation, e.g. "reflects increased investor caution towards MU".
  - Any sentence that repeats a bullet figure.
- **If nothing survives:** the answer is the bullets plus "In short".
- **Prompt:** the model is now also told not to restate the lines above, and to add at most two cited sentences of new context.

## 4. Insiders: answer within about 6.5 s
- **Parallel loading:** filings load 4 at a time through the shared bb8f limiter, which still allows at most 10 sec.gov starts per rolling second. A cold 40-filing scan is about 42 requests, so its floor is about 4.2 s.
- **The cap:** `/api/insiders` waits at most 6.5 s, down from 8 s. If the scan isn't finished, the response carries what is ready, marked as follows:
  - `meta.partial: true`
  - `meta.more: "loading"`
  - `note: "More filings loading — refresh shortly"`
  - `X-Dispatch-Data-Status: partial`
  - `Cache-Control: no-store`
- **Background fill:** the same scan carries on and fills the cache. Partial results are never cached.

## 5. Insiders window: never short-and-complete
- **Root cause:**
  - The free scan stops after 5 open-market trades, which is about 4 to 6 NVDA filings. The premium scan reads 40 filings. Both shared the cache key `f4:T`.
  - Once the premium entry was past its 6 h TTL, a free visitor's scan overwrote it.
  - The next cold premium scan ran past the 8 s budget, and bb8 answered it from that free entry as `stale`. The window was built from the free scan's filings ("Last 3 weeks"), with no partial flag.
- **Second issue:** a filing whose fetch failed (a limiter wait, an SEC 503 or a timeout) was counted as scanned. A scan with missing rows could therefore be cached and labelled as a complete 40-filing window.
- **Fix:**
  - `f4:T` only ever holds complete premium scans; free scans live in `f4:T:free`.
  - A complete entry is only replaced by another complete scan.
  - Entries from before bb8h that hold an incomplete scan under `f4:T` are dropped on read.
  - A filing that fails twice (an SEC 404 counts as a real answer, not a failure) ends the scan as partial (`meta.more: "retry"`). Partial scans are not cached.
  - The window and rows cover only the unbroken run of loaded filings, counting from the newest. The same applies to `before=` pages.

## Not added
No tables, intervals, dependencies, secrets, paid feeds or Stripe changes.
