# bb8h: Yahoo's published beta on card answers, and [n] citations that match their line

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

## Not added
No tables, intervals, dependencies, secrets, paid feeds or Stripe changes.
