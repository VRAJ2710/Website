# bb8q2: Yahoo DX-Y.NYB as the dollar index, UK CPI/gilt wording, and a cited gold futures move after a cold start

Stacked on bb8q (PR #69). Applies to server `b4f66c896a13a73fb03656386c4ae802` (17,865 lines) and is server-only:
`python3 deploy/patch_bb8q2.py <folder>` (`--check` does a dry run). The patch appends one block, marked `// ── bb8q2 ──` …
`// BB8Q2_JS_END`. It adds no timers, tables, secrets, paid feeds or Stripe changes. It reuses bb8's existing `bb8Late`
deadline and has no new setTimeout. A second run prints `REFUSE: bb8q2 already applied` and exits 0.

## 1. Dollar index: Yahoo DX-Y.NYB everywhere (Jack's call 1)
- Label: **"US Dollar Index (ICE, Yahoo DX-Y.NYB)"**. Source: Yahoo Finance (DX-Y.NYB), about 10 minutes delayed.
- `/api/market-reference-quotes`: `DXY` is now the ICE quote. Before, it was the FX-computed index. The header reads this
  route through `fetchReferencePrices`, and `generateGoldDesk` uses the same function.
- The FX-computed index is still returned, but only as `DXY_FX` with the label **"Dispatch FX basket"**. If Yahoo has no
  DX-Y.NYB quote, `DXY` falls back to the labelled basket with `fallback: true` and `fallbackReason`.
- `fetchSyntheticDxy()` now names its output "Dispatch FX basket", so the old name "US Dollar Index (computed from live
  FX)" no longer appears in any output.
- The regime input (`bb3Pack().dxy`) and the Ask "For context" and regime facts now use DX-Y.NYB. The old value is kept as
  `pack.dxyFx`. The chat live block line reads "US Dollar Index (ICE, Yahoo DX-Y.NYB)".
- "How is the dollar doing?" now uses the DX-Y.NYB timeframe, with no `$` sign. A 0.00% move reads "unchanged".

### Frontend fields: `GET /api/market-reference-quotes`
| field | DXY (ICE) | DXY_FX |
|---|---|---|
| `symbol` | `"DX-Y.NYB"` | `"DISPATCH-FX"` |
| `label` / `name` | `"US Dollar Index (ICE, Yahoo DX-Y.NYB)"` | `"Dispatch FX basket"` |
| `price` (= `p`) | last price | computed value |
| `prevClose` (= `prev`) | Yahoo previous close | basket's previous value |
| `change` | price − prevClose | same |
| `changePct` (= `c`) | % change vs prevClose | same |
| `asOf` / `asOfUk` | ISO UTC / `"Mon 19 Oct, 13:15 UK"` | same |
| `source` | `"Yahoo Finance (DX-Y.NYB)"` | basket source |
| other | `exchange "ICE"`, `delayMin 10`, `proxy false`, `changeAvailable` | `note`, and `fallback` / `fallbackReason` when it stands in for DXY |

The legacy `p` / `c` / `prev` keys are kept, so `_applyLiveQuote` keeps working with no client change.

### Recommended app.js changes (client, not in this patch)
1. `fetchReferencePrices` (~line 5351): show `data.DXY.label` as the name (`liveQuoteName.DXY = data.DXY.label`). Pass
   `"yahoo"` (or `data.DXY.source`) as the source, so the header badge reads "DELAYED" and not "SYNTH·DXY".
2. ~Line 4942: drop the `"SYNTH·DXY"` badge for DXY. If `data.DXY.fallback` is true, badge it "FX BASKET" with the
   detail "Dispatch FX basket".
3. Lines 4943, 6778, 12779 and 12825: the fallback names `"US dollar index"` should become
   `"US Dollar Index (ICE, Yahoo DX-Y.NYB)"`, or `"Dispatch FX basket"` for FX-computed sources.
4. `_rt37Ref` (~line 19185): stop borrowing the GC=F % into XAU when spot is flat. When `data.XAU.futuresChange` is set,
   show it as its own labelled line: `futuresChange.text` ("gold futures (GC=F) +0.14% today"), never as spot's change.

## 2. UK CPI and gilts (Jack's call 2)
- The UK no-data line now says "We don't carry UK CPI in our data feed right now, so this answer does not quote any."
  For gilt questions it says "We don't carry UK gilt yields in our data feed right now…", and for questions that cover
  both it says "UK CPI or UK gilt yields".
- The gilt wording is added whenever the question mentions gilts, yields, bonds, Bank Rate, the BoE/MPC or the rate path
  (`BB8Q2_RATES`). "UK inflation rate" alone does not trigger it.
- The proxy line now says "What we do have, from Yahoo Finance as of … UK, as market proxies (not CPI or gilt data): GBP/USD
  … [1]; the FTSE 100 … [2]". On gilt questions it adds "the US 10-year Treasury yield (^TNX), a related yield but not a
  gilt yield, is 5.10% [3]". Any invented gilt figure is dropped, as in bb8q.

## 3. Gold spot change after a restart (Jack's call 3)
**Findings: no free, keyless source gives spot's previous close.** Checked 13:10–13:20 BST, 19 Oct 2026:
- gold-api.com `/history` and `/ohlc` (documented in https://gold-api.com/llms.txt) return 401 `{"error": "No x-api-key
  header."}`. They need an API key (free tier, 10 requests/hour), and we add no secrets, so they're out. `/price/XAU` is
  keyless but has no previous close.
- Yahoo `XAUUSD=X` and `XAU=X` return "No data found, symbol may be delisted".
- freegoldapi.com `data/latest.json` is stale (it ends 2026-02-20) and its source is Yahoo futures, not spot.
- Stooq `xauusd` is behind a JavaScript challenge, or returns 404.
- LBMA (prices.lbma.org.uk JSON) returns 403 (Cloudflare).
- Swissquote's public feed has live bid/ask only, with no previous close.

**What ships instead:** the fallback Jack approved. bb8q's in-memory spot previous close (`bb8qSpotMem`, filled on request
after a UK day roll) still gives spot's own change once warm. Until then:
- The Ask spot line reads "Gold spot is at $4,166.90 (gold-api.com, as of … UK); spot has no previous close in our feed yet,
  so today's move comes from gold futures (GC=F, delayed 10 min), up 0.12% today. [1][2]". It cites both the gold-api.com
  and the Yahoo GC=F sources, and the % matches the "In short" line. No answer says only "no change is given".
- Reference XAU (cold start): spot `change` / `changePct` / `prevClose` stay null, `changeAvailable: false`. Two fields
  are added: `futuresChange` `{symbol:"GC=F", label:"Gold futures (GC=F, delayed 10 min)", price, prevClose, change,
  changePct, asOf, asOfUk, source:"Yahoo Finance", delayMin:10, text:"gold futures (GC=F) +0.14% today"}` and `changeNote`.
  The `futures` object also gains `prevClose`, `changePct`, `asOfUk` and `delayMin`.
- Ask `meta.quote` (XAU) gets the same `futuresChange` and `changeNote`.
- Warm start: `futuresChange` is `null`, and spot shows its own change against the remembered previous close.

## Known limits
- Spot's own change is available only after the server has seen a UK day roll (as in bb8q). On a fresh restart, the
  futures change stands in, labelled.
- Regime scores now use DX-Y.NYB, not the FX basket. The two usually differ by a few hundredths of a percent, so a card's
  score can shift slightly.
- The header label and badges need the app.js changes above. The server-side fields are ready.
