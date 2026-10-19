# bb8r: quote labels, GC=F YTD bar, citations, one regime, GBp market cap

Server only (`deploy/patch_bb8r.py`). Stacked on bb8o. Expected `server.js` md5 before apply is `77aa597819385227f1407cd5d6c69f53` (the file after bb8o). The block is appended after `// BB8O_JS_END`. A second apply prints `REFUSE` and exits 0. A missing or repeated anchor ABORTs and writes nothing. An md5 mismatch only WARNs; anchors still decide. `--check` is a dry run. CRLF in the base is preserved. `node --check` runs before the write.

Apply order on the live stack: bb8q (`b4f66c89`, 17865 lines) → bb8q2 (`af877dde`, 18188 lines) → bb8o → bb8r.

This checkout's `server.js` is the unpatched stub (md5 `2954f8b7412619b1030abeebe3c57456`, 933 lines). The post-bb8o bytes are not in the repo, so the md5 of `77aa5978` plus this block cannot be computed here. The block itself is 777 lines, md5 `f5bf56f0cea47848a93974bb0f3a37ac`, sha256 `fc02a376147ac4f3351e32d6a56a6d6f53717792089006eed6a9e82b235994ba`. Patch file sha256 `7ea20601799146d6a08884a3846574470712a42ed08d1fa237decc73d1f94922`.

No new tables, timers, intervals, secrets, Stripe, or Replit. Every new top-level name starts with `bb8r` or `BB8R_`. In-memory only: regime for 10 minutes (`BB8R_REGIME_MS`), calendars for 6 hours (`BB8R_CAL_MS`).

## P0 (1) Footer label is the Ask subject

QA's MU answer carried the right price and the wrong label: `Gold spot $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK`.

`bb8rQuoteMeta` is the one quote object for both paths. It wraps `bb8pQuoteMeta` (the stream meta event) and `bb8pMetaFix` (the JSON body). For MU, NVDA and AAPL the label and the name are the company (`Micron Technology`, `NVIDIA`, `Apple`, with the trailing Inc / Corporation stripped). `quoteLine` is rebuilt from that label. XAU / GOLD / GC=F / XAUUSD=X stays `Gold spot` and uses the gold-api spot price. A reply line that still says `Gold spot $…` under a non-gold subject is replaced with `quoteLine`.

`bb8p` stores the percent in `change`. `bb8rFixChange` puts the cash move in `change` and the percent in `changePct`, which is what the footer prints.

Fields that can feed a footer:

| field | who sets it | bb8r |
|---|---|---|
| `meta.quote.label`, `name`, `price`, `change`, `changePct`, `asOfUk`, `quoteLine` | stream meta event and JSON `bb8pMetaFix` | subject label and `quoteLine` |
| reply text | both paths via `bb8qFinish` → `bb8rAfter` | `Gold spot $` under a non-gold subject becomes `quoteLine` |
| move-card lead (`bb8e`) | card prose, not the chat chip | not a footer label; gold questions already say Gold spot in bb8q |

Sample footer: `Micron Technology $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK`.

## P0 (2) GC=F year-to-date bar

Live Yahoo chart `GC=F` `interval=1d`, timezone `America/New_York`, fetched 19 Oct 2026. Unadjusted close equals adjclose on these bars.

| exchange date | timestamp | open | high | low | close | volume |
|---|---|---|---|---|---|---|
| Mon 29 Dec 2025 | | 4568.0 | 4581.2998 | 4316.0 | 4343.6001 | 316961 |
| Tue 30 Dec 2025 | | 4350.2998 | 4420.5 | 4338.7998 | 4386.2998 | 189751 |
| Wed 31 Dec 2025 | 1767157200 | 4353.0 | 4384.8999 | 4284.2998 | **4341.10009765625** | 161782 |
| Fri 2 Jan 2026 | | 4340.0 | 4414.7998 | 4319.7002 | 4329.6001 | 154807 |

`bb8rYtdPick` takes the last daily bar whose exchange-local date is before `YYYY-01-01`, and uses the unadjusted close. Display rounding of that Wednesday bar is **4341.10**. Direction and percent are `bb8rYtdDir` from the two cited numbers (4341.10 to about 4181.20 is down about 3.7%). The bb8o sign guard is unchanged; its 3341.10 fixture is a direction test, not this baseline. A YTD sentence that says both "gold spot" and GC=F is relabelled gold futures (GC=F). Spot and GC=F are not mixed on the same YTD line.

## P0 (3) Citations renumber after the drop

`bb8rCites` runs before `bb8qRender`. A sentence about the dollar index, the 10-year, VIX, the S&P, a futures range, or the regime is rebound to the source whose key or title contains that instrument and the figures in the sentence. `bb8qRender` then numbers `[n]` by appearance. A Fortitude / news row is not a futures-range source. DXY lands on `DX-Y.NYB`, the 10-year on `^TNX`, the 5-session high/low on the GC=F chart.

## P0 (4) One regime figure

`bb3Mood` is wrapped. The first call in a process is stored with an as-of for 10 minutes. Later calls, including a JSON ask a couple of minutes after the stream, return that same regime and score. `bb8rStampRegime` writes it into the regime fact. `meta.regime` and `marketReferenceQuotes().regime` carry `{ regime, score, asOf, asOfUk }`. No new table.

## P0 (5) BP.L market cap

Live Yahoo, 19 Oct 2026 about 14:09 UTC (crumb + quoteSummary on query1; chart v8 needs no crumb). Chart meta has no shares or market cap.

| field | value |
|---|---|
| currency | **GBp** (pence) |
| exchange / instrumentType | LSE / EQUITY |
| longName | BP p.l.c. |
| regularMarketPrice | **622.0** (the hint ≈618.9 was a few minutes earlier; chart meta matched 622.0) |
| price.marketCap | **96121077760** |
| summaryDetail.marketCap | **96121077760** |
| summaryDetail.currency | GBp |
| sharesOutstanding | **15453548807** |
| impliedSharesOutstanding | 15453548807 |
| floatShares | 15068362907 |
| shares × (622 / 100) | 96121073579.54 |
| ratio yahoo / implied | 1.000 |

Yahoo's `marketCap` is already pounds. Dividing it by 100 again would print about £0.96bn. Multiplying the raw pence price by the share count and calling that pounds would print about £9.61tn. Adding Yahoo's cap to the computed cap would print about £192bn. `bb8rCap` does none of those:

- ratio 0.8–1.25: keep Yahoo, status `ok` (this is BP.L today, **£96.1bn**)
- ratio 1.6–2.4: the figure looks like the cap added to itself; use shares × (price/100) once, status `deduped`
- ratio 50–200: Yahoo was about 100× too big; divide by 100, status `corrected-minor-units`
- no Yahoo cap: compute shares × (pence/100), status `computed`
- no share count: keep Yahoo and do not divide it, status `unverified`

£94.7bn is this same path at about 613p (`15453548807 × 6.13 / 1e9 ≈ 94.7`). £60–70bn is what that share count would be near 450p. These fields do not support £60–70bn, so the patch does not invent a lower share count.

ADR cross-check, same fetch: `BP` currency USD, price 49.77, sharesOutstanding 2575591468, marketCap 128187187200. Ordinary shares / ADR shares = 6. `49.77 / (6 × 6.22) ≈ 1.334` GBPUSD, and the dollar cap at that rate is the same £96.1bn.

The listing profile (`bb8oProfileFrom`) and the Ask market-cap sentence both go through `bb8rCap`. The sentence is in pounds. The source detail keeps `price`, `priceCurrency`, `sharesOutstanding` and `yahooMarketCap`. `marketCapCheck` on the profile carries the same inputs.

## P1

**Gold this week.** The reply opens with `Gold spot $4,156.30 (gold-api.com, as of Mon 19 Oct, 14:42 UK).` The GC=F week sentence follows. A leading `Live:` is removed from the following line; it is not deleted.

**Calendar.** Keyless fetches, cached 6 hours in memory:

- FOMC `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` (200). 2026 decision days include 28 Jan, 18 Mar, 29 Apr, 17 Jun, 29 Jul, 16 Sep, **28 Oct**, 9 Dec. The week of Mon 19–Sun 25 Oct 2026 does not include one. Next is 27–28 Oct.
- BEA `https://www.bea.gov/news/schedule` (200). Next GDP advance and Personal Income are **29 Oct 2026**, after this week.
- ONS `https://www.ons.gov.uk/releasecalendar` (200). This week's titles are not CPI, CPIH, GDP, labour, retail sales or earnings, so they are not listed as macro releases.
- BLS `https://www.bls.gov/schedule/news_release/bls.jr.htm` returned **403**. BLS is recorded as failed. No BLS dates are invented.

If FOMC, BEA or ONS loaded and nothing macro falls this week, the old "No scheduled Fed…" line becomes `No FOMC, BEA or ONS release falls this week (calendars checked; BLS did not load)`. If every fetch fails, that original line is left as it is.

**Cited figures.** A `$x,xxx.xx` within $1 of a figure in the cited source, and not equal to it, is replaced (4181.00 → 4181.20). A gap such as 4341.10 versus 4386.30 is left alone.

**Filler.** Sentences matching "it's essential to monitor" / "essential to monitor" / "monitor related economic indicators" are dropped. A cite token after the previous sentence stays with that sentence.

**As-of and "As a proxy, ".** Each proxy clause uses that source's own `asOfUk`. A closed session is `{day} close` (`Fri 16 Oct close`), not a later headline clock time. The clause is prefixed with the exact words `As a proxy, `.

## P2

**DXY.** Prose uses `US Dollar Index (ICE)`. The source detail still contains `Yahoo DX-Y.NYB`. The bb8q2 constant is not edited.

**0700.HK.** `changeDay` is the weekday of the row's own timestamp in `Asia/Hong_Kong`. Fri 16 Oct 2026 08:08 UTC is `Fri`. The same tag is set on `feed` when `feed` is an object, and on `session`. A string `feed` is left as a string.

## Frontend notes (app.js is not edited)

This repo's `app.js` has no `Gold spot` string. `_renderChatMsgs` (line 15382) renders the message text. It does not paint a quote chip. The chip QA saw is a newer client.

Proposed client, chat footer: render `meta.quote.quoteLine`. If the client builds the line itself, use `meta.quote.label` (the Ask subject) with `price`, `change`, `changePct` and `asOfUk`. Do not keep a previous turn's Gold spot label.

Proposed client, regime pill: `_computeRegimeEngine` (lines 629–669) and `_renderRegimeRing` (lines 2143–2147) recompute a local score (at least 72 Risk-On Strong, at least 55 Risk-On Fragile, at least 40 Transition, otherwise Risk-Off). Read `meta.regime` on the chat payload, or `regime` on `GET /api/market-reference-quotes`, and use that score, label and as-of for the pill.

## Tests

`node --test test/bb8r.test.js` covers both quote paths, the 31 Dec bar, citation rebind, the regime cache, the BP.L unit cases, the gold-week opener, the calendar parsers, the snap, the filler, the proxy as-of, the DXY label, the 0700.HK Friday tag, and the apply protocol (refuse, dry run, CRLF, md5 warn, missing anchor abort, `node --check`). `test/bb8o.test.js`, `test/bb8q.test.js`, `test/bb8q2.test.js` and `test/bb8p.test.js` still pass.
