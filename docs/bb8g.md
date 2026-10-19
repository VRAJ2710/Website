# bb8g: source labels, cited card answers with a server "In short:", no restated peer figures

Server-only patch, stacked on server.js md5 `b9f30e995bc43d97738b839abf9cf3e3` (bb8f). Apply with
`python3 deploy/patch_bb8g.py <folder>` (`--check` is a dry run). It adds no tables, intervals, dependencies, secrets or paid feeds.
`app.js` and `index.html` are not changed.

**(a) Source labels.** An Ask source is labelled from its `publisher` field when it has one. Otherwise the label comes from the link's host,
using a friendly name (stocktwits.com → Stocktwits, reuters.com → Reuters, ft.com → Financial Times…) or, for an unknown host, the bare host.
A generic label ("Yahoo Finance news", "News") or a Yahoo label is never kept on a link that isn't on Yahoo.
A client-supplied publisher name, such as "Reuters" from the news feed, is kept. A name that already matches its host is kept too, e.g. "Yahoo Finance quote" on finance.yahoo.com.
Server-built news sources are labelled from the host. `/api/ticker-news` items whose link isn't on Yahoo now carry the host's publisher as `source`/`publisher`, plus `via: "Yahoo Finance RSS"`.

**(b) Card / move answers.**
- The card-score line is now cited. So is a new server fact line for beta, taken from the card's own `sensitivity` input:
  "Beta (Dispatch desk reference): 2.23, so MU tends to move about 2.23 times as much as the market. [n]".
  Both cite a "The Dispatch" source (Pulse card score and desk beta).
- A model sentence with no valid [n] and no figure from the fact lines is dropped whole, using the bb8d splitter, in both the streamed and the final text.
  The prompt asks the model to cite every claim and not to guess at positioning, rotation or sentiment.
- A deterministic line goes last, after the filters, citing the quote source:
  `In short: MU fell 5.63%, 4.52 pts behind SPY, in a Risk-Off session; no confirmed cause. [n]`
  It covers rises and falls (open sessions read "is up/down"), ahead of / behind / in line with the benchmark (SPY, FTSE 100, DAX…), a missing benchmark
  ("with no market comparison available"), and a missing mood. The cause is always "no confirmed cause", because headlines are shown only as not confirmed.
  It contains no buy/sell calls or targets.

**(c) Valuation answers.** A model sentence is dropped when it restates a peer line: the same ticker with the same multiple, an "it/this" sentence with a listed figure,
a lower/higher/below/above comparison naming a listed peer, or a listed "not reported". Interpretation stays. The prompt says not to restate.

The Sources list still matches the cited [n], renumbered 1..n, on both the stream and JSON paths.

Tests: `node --test test/bb8g.test.js` (5 tests).
