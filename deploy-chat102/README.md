# deploy-chat102

Public `/terminal/` for The Dispatch Market. One page, two reads (`/api/c102/terminal` and `/api/c102/chart`). It is added to the live chat101h files. It does not start the server, change `EXPECT_TAG`, publish the Replit deployment, or touch Stripe, the database, or the member Gold Desk.

chat101i is a separate unpublished research edit. This bundle does not apply it. The hash check below refuses to run unless `server.js`, `app.js` and `index.html` are still the chat101h bytes.

## Live base that must be on disk

Checked against https://thedispatch.uk on 6 November 2026. `app.js` was downloaded and matched. `server.js` and `index.html` are not served as raw files; the script checks the on-disk bytes and stops if they differ.

| File | Required md5 | Required sha256 |
| --- | --- | --- |
| `server.js` | `6077bef9728ffe5b26d8d6fcb887294b` | printed by the dry run, not pre-pinned |
| `app.js` | `6c8ddd1be4db078df1de146163f99b11` | `80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989` |
| `index.html` | `e5ab1af080974da456e086a1835d1e7b` | printed by the dry run |

After a matching patch, `app.js` must be md5 `b84058f6da16ad022640b06c9cdda72d`, sha256 `b5dcd5fca7514f1d09a29d4e5c67c7a1c2d64d54bf92969cadf7244dd9073440`. Line 1 of `server.js` stays the maintenance-off line. `index.html` only changes `app.js?v=chat101h` to `app.js?v=chat102`.

A mismatched snapshot prints `ABORT` and does not write the live files. A second run refuses if `.bak-chat102` backups or the chat102 markers are already present.

## Preview on Replit, without republish

Do not `git pull` or merge on the production Replit. Do not run `node server.js`. Do not press Run. Do not republish.

```sh
bash deploy.sh --dry-run
bash deploy.sh
```

The dry run prints the scratch md5 and sha256 for `server.js` and `index.html` and leaves the live files untouched. Undo is restore `server.js`, `app.js` and `index.html` from their `.bak-chat102` copies. Republish only when a person decides to, and only the existing Autoscale deployment.

Local checks, from this folder:

```sh
node build_block.js
node --test t_c102.js
```

`t_c102.js` covers the instrument rules, the failure states, the hash abort, and `node --check` on a patched copy of the chat101h `app.js`.

## What the page is

`/terminal/` is a public page in the existing site shell. The header gains Terminal after Gold, and All sections lists it under Gold and macro. Dashboard, Gold, and the member Gold Desk are unchanged.

Desktop shows six tiles, then the futures chart, then Macro and Positioning side by side, then Events, then Risk and sources. At 390 and 320 the groups stack. Body text stays at 15px. There is no ticker and no forecast.

The chart is drawn on a canvas in this bundle. It does not load TradingView and it does not use the desk's global chart loader. Range, the two averages, and the session table are buttons. Arrow keys on the chart read the selected session into a polite live region only after a key or a tap. Vertical scrolling stays available (`touch-action: pan-y`).

The document title stays `Terminal | The Dispatch Market` when a feed fails.

## Data rules

The browser calls two same-origin URLs. Symbols are fixed in the server. A query string cannot choose a host. Upstream requests do not forward cookies. Each upstream wait is 7 or 8 seconds, in parallel. A warm response is the in-memory cache (60 seconds for the snapshot, 120 seconds for the chart). API responses send `Cache-Control: no-store`, `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`. The HTML page does not add a Content-Security-Policy, because the existing shell loads its fonts from Google and a `default-src 'none'` policy would break that shell.

| Reading | Source used | What is refused |
| --- | --- | --- |
| Gold spot | gold-api.com `XAU`, USD per troy ounce | A futures percentage is not copied onto the spot change |
| Spot change | The desk's gold-api snapshot when that snapshot publishes one | `market-reference-quotes` often has `c: null`. Empty stays empty |
| Silver and the ratio | gold-api.com `XAG` over the same USD/oz unit | If the two timestamps differ by more than three minutes, no ratio |
| Front-month future | Yahoo Finance chart `GC=F`, labelled with the returned name (`Gold Dec 26 future · delayed` on 6 Nov 2026) | Not spot, not XAU, not a single-expiry history, not back-adjusted here. The series kind is `continuous-rolling-proxy` |
| Chart sessions | Completed sessions only, in `America/New_York` | The bar dated today is left out of the candles and of the 20- and 50-session averages. Fewer than 50 completed sessions means no 50-session line |
| Volume | Futures volume when the feed returns a positive number | Null and zero are "no volume", and the candle is still drawn |
| Dollar index | Yahoo `DX-Y.NYB` only when the exchange name is ICE | `DXY_FX` is a computed basket and is not shown as ICE |
| US 10-year | Yahoo `^TNX`, delayed, its own time | FRED `DGS10` is a second line with its own observation date. That date is not called today |
| Real yield | CNBC/Tradeweb via the existing `c101fRates` when that function answers | FRED `DFII10` stays on its own date. `/api/gold-desk` is not called |
| Volatility | Yahoo `^VIX` only when the name is the Cboe Volatility Index | `VXX` is rejected |
| Positioning | CFTC Socrata, `commodity_name=GOLD`, market `GOLD - COMMODITY EXCHANGE INC.`, code `088691`, latest report date | Micro gold is dropped. The figure is weekly and is not advice |
| Calendar | Existing `/api/c97/calendar` rows for BLS, BEA, ONS, the Federal Reserve and the Bank of England | Consensus is not copied onto the page |

A panel that times out, comes back malformed, or has no number says so. The other panels still render. A change of zero is shown as zero. An older stored reading, if shown at all, carries its time and its age.

## Live check on 6 November 2026, 15:38 UK

One cold `c102Collect` plus the chart fetch finished in about 2.8 seconds. Every panel answered. This is a sample, not a promise about the next cold call.

| Reading | As of (UK) | Value |
| --- | --- | --- |
| Gold spot, gold-api.com | 15:38 | 4047.30 USD/oz. Desk snapshot change −0.99% since yesterday's close (23:56 UK, 5 Nov) |
| Gold/silver ratio | both prints, gold-api.com | 77.956 |
| US dollar index, ICE via Yahoo | 15:28 | 102.116 |
| US 10-year, Cboe via Yahoo | 15:23 | 4.876% |
| US 10-year real, CNBC | 15:34 | 2.612% |
| Official 10-year, FRED DGS10 | observation date 4 Nov 2026 | 4.90% |
| Official real yield, FRED DFII10 | observation date 4 Nov 2026 | 2.64% |
| Cboe Volatility Index via Yahoo | 15:23 | 23.58 |
| CFTC COMEX gold, weekly | report date 27 Oct 2026 | net 105,562 contracts |
| Chart | last completed session 5 Nov 2026, America/New_York | `Gold Dec 26 future · delayed`. Today's bar was excluded. 20- and 50-session averages were present. 251 completed bars |

## Choices and what is still open

The chart is a canvas in this bundle so the public page does not load the desk bundle or a new library. Colours are read from the site's CSS variables and redrawn when the theme class changes.

The real-yield market quote depends on `c101fRates` already being on the server. If that function is missing, the tile falls through to the FRED daily print and says which source it is. Yahoo's multi-symbol quote URL returned 401 on 6 Nov, so the three quotes are three parallel chart requests, not one batch and not six serial calls.

The coordinator should still look at a Replit preview at 390 and 320, in light and dark, and confirm the live header wraps the new Terminal link without crowding Brief, Gold, Calendar and the rest. Also worth a look: a closed COMEX session (does "today" still drop a finished bar), a GoldAPI pair whose timestamps differ by more than a second, and a CFTC week when the report date is more than 21 days old. Those states are covered by fixtures. They were not all seen on this live pull.
