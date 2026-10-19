# bb8l: UK time in user-visible text and model prompts; next-earnings line; insiders span and UK dates (server only)

Stacked on bb8k. server.js md5 `0510fe845e43ec1e865dbc4257b00418` (15197 lines) becomes `4b2fe7d9bdb6768a97eb5b864e442d1b` (15736 lines).
The patch makes one in-place edit (the rt39s gold reply prefix; its anchor matches once) and appends one block (`// ── bb8l ──` … `// BB8L_JS_END`). app.js and index.html are not touched. It adds no tables, intervals, new timer code (per-request waits reuse bb8's `bb8Late`), dependencies, secrets, paid feeds or Stripe/auth/webhook changes.

## How it converts
- **Full timestamps** (ISO with Z or an offset, and `YYYY-MM-DD HH:MM UTC|GMT`) go through bb8d's formatter (`bb8dUk`, Europe/London) → `Fri 16 Oct, 21:00 UK`.
- **Time-only stamps** (`HH:MM UTC|GMT`, `HH:MMZ`) become `HH:MM UK`, using the UTC date of the request. They carry no date, so this is the only possible reading.
- **BST and GMT** both come from `Intl` with the Europe/London zone, including the changeover hours. Tested for 25 Oct 2026 and 28 Mar 2027, and with the process TZ set to UTC and to America/New_York.

## Inventory (line numbers are in the 64t server.js)
### Converted
| Site | Before | After |
|---|---|---|
| 8180 `bb2AsOf` → 8309/8320 `bb2BuildFacts().block` (JSON valuation prompt) | `AUTHORITATIVE PEER COMPARISONS as of 2026-10-16 20:00 UTC`, `\| as of 2026-10-16 20:00 UTC` | `as of Fri 16 Oct, 21:00 UK` (bb2BuildFacts wrapper). `built.asOf` stays the machine value. The stream prompt was already converted by bb8d's bb2System wrapper. |
| 7118 rt39s-gold JSON reply prefix | `Live: Gold (GC=F) 4192.80 as of 08:49 UTC` | `as of Mon 19 Oct, 09:49 UK` (in place, `bb8lGoldHm`) |
| 2212 Congressional snapshot note | `…snapshot from <ISO asOf>.` | UK (institutionalResponse wrapper on `note` only; `asOf` stays ISO) |
| Every model prompt: `generateAi` → `bb3bGenerateAi` (Ask JSON, brief, lenses, intelligence, committee, news scores) and the stream's `bb2Complete` | Client-supplied ISO / UTC in system text, context, brief context and message text reached the model unconverted | system and message text converted (copies; the caller's objects are not changed) |
| Ask replies: streamed general-answer sentences (`bb8jFix`, `bb8iLine`) and the final reply on both paths (`bb8jAssemble`) | A model-echoed `2026-10-19T06:30:00Z` was painted raw while streaming; `06:30 UTC` survived in the final reply | UK while painting and in the final reply |
| Brief text fields (`rt33sBriefDate`: headline, houseView, summary, risks, …) | Model-echoed ISO / UTC | UK. `date` (London date), `generatedAt` and `generatedAtUk` are unchanged |

### Already UK before bb8l (checked, no change)
- The live gold/DXY/10y block (bb8d wraps `buildChatLiveMarketBlock`).
- Sources footers (bb8d `bb2Footer`).
- The stream system prompt (bb8d `bb2System`).
- Card/move leads (`bb8dUk`).
- Quote notes (`updated HH:MM UK`).
- The insiders `statusLabel` / `window.note` (bb8i).
- The JSON CITABLE SOURCES list (bb8k).
- The brief `generatedAtUk`.

### Intentionally left (machine values or not timestamps)
- **Machine JSON fields (ISO by contract):** asOf, ts, savedAt, generatedAt, checkedAt, fetchedAt, firstPriceAt, nextOpen, expiresAt, publishedAt, exportedAt, `sources[].asOf`, `time`, `bb8iAt`. These are the 85 `toISOString()` sites, apart from the converted text sites above.
- **HTTP headers:** `X-Dispatch-Data-As-Of` / `X-Dispatch-As-Of` (7412).
- **DB writes:** 1619, 3003–3223.
- **Sitemap and SEO:** sitemap `<lastmod>` (5357) and the article `published_time` / `modified_time` meta tags and JSON-LD `datePublished` / `dateModified` (5558–5590). Crawlers need ISO 8601 here.
- **Date-only keys:** `toISOString().slice(0, 10)` (1162, 1168, 1664, 3990, 4089, 4205, 7844, 7931, 8098, 11300) are cache days, query parameters and dates. The ET session dates in the gold block and windows (`session 2026-10-19`, `2026-10-12–2026-10-16`), filing dates and `brief.date` are dates, not timestamps.
- **Arithmetic and parsing:** `Date.UTC` / `getUTC*` (1167–1205, 8158–8162, 12127), the 4508 parse, and bb8d's own converter regexes (13160–13166).
- **Comments** that mention UTC: 4360, 4377.
- **Admin editorial console (5635):** `new Date(updatedAt).toLocaleString()` runs in the admin's browser and shows the viewer's local time. It is an admin-only, noindex page and not server text.
- **Client-built context strings:** e.g. `prices as of 19/10/2026, 07:40`, formatted in the reader's browser. They carry no zone and are not UTC or ISO.
- **Structured outputs of lenses, intelligence, committee and news scores:** their JSON objects mix model text with machine fields, so no text pass runs over them. Their prompts are now UK-only, so the model has no UTC to echo.
- **Stripe, auth, webhook, the AI-readiness alert row and the OpenBB health row:** not touched (DB and machine values).
- **Searched for and not found:** user-facing error messages with timestamps and server-side alert or email text with times.

## Grep evidence
`grep_before_after.txt` has the pattern counts and string-building sites. The same producing sites remain because the conversion happens at the text and prompt boundary. The extra `UTC` and `GMT` hits in "after" are the bb8l converter's own regex and comments, plus the fallback in the 7118 edit.

## chat73 (1): "Next earnings" fact line in Ask answers
- **Source:** Yahoo Finance quoteSummary `calendarEvents.earnings`. This is the same field `/api/financials` returns as `nextEarnings` and `earnings.next` (MU on 19 Oct 2026: `{"date":"2026-12-23","isEstimate":true}`, see evidence/financials_mu.txt).
  - The `/api/financials` 12 h cache (`RT32.cache`) is read first.
  - Otherwise there is one quoteSummary request, capped at 2.5 s. Concurrent calls for a symbol share it, and a success is reused for 30 s, so the card's beta and earnings lookups make one request.
  - A small 1 h in-memory memo holds the result. No new feed, table or job.
- **Line:** `Next earnings: Wed 23 Dec 2026 (estimated) [n]`.
  - `(estimated)` appears only when `isEarningsDateEstimate` is true.
  - The date is a calendar date (no time zone).
  - There is no line when Yahoo gives no date, or when the date is before today's UK date.
- **Source entry** (Sources footer and JSON `sources`): `{ name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/MU/", asOf: <ISO, machine>, detail: "MU next earnings date (Yahoo Finance calendarEvents, estimated)" }`. The footer prints the as-of in UK time (`as of Mon 19 Oct, 10:18 UK`).
- **Where the line appears:**
  - **Card answers:** always (when there is a date), in the lead after the beta line and before the "In the news" lines. It is painted on the stream like the other lead lines.
  - **Move / general answers about a ticker:** when the question mentions earnings, results, report, quarter, EPS or guidance.
  - **Valuation answers:** under the same condition. The line goes before `In short:`, with the final [n], on both the stream final and JSON. The model prompt gets the line too, numbered as the final source list numbers it. While streaming, the valuation line appears with the final text (done event), as the peer footer does.
- **Filters:**
  - **bb8h:** a sentence about the next earnings date ("Micron is set to report … on 23 Dec") keeps the line's [n], or is pointed at it.
  - **bb8i:** "is set to / likely to report" is allowed only when it cites this line.
  - **Dropped:** sentences that give another date ("18 Nov"), call an estimated date confirmed or official, attribute views ("Analysts expect strong results…"), or speculate ("could see…").
  - A sentence that is not about earnings may not cite the line; its [n] is re-pointed by bb8h's usual rules.
  - The line never carries an EPS estimate or forecast.

## chat73 (2) and (3): insiders, for Frontend (rt60)
**Finding:** on a `before=` page, `meta.window` describes that page only. For NVDA, page 1 is 2026-03-20 → 2026-10-13 ("Last 7 months") and the `before=2026-03-20` page is 2025-10-15 → 2026-03-19 ("Last 5 months"), which is why the label shrank.

**Use these fields:**
| Field | Meaning |
|---|---|
| `meta.span.label` | **Show this as the window label.** The whole loaded span, from this page's `from` through the newest filing on page 1 (e.g. "Last 1 year" after one Load older, "Last 15 months" after two). |
| `meta.span.from` / `meta.span.to` | ISO dates of that span. `fromUk` / `toUk` are the display forms ("15 Oct 2025" / "13 Oct 2026"). |
| `meta.span.before` | The `before=` value of this page; `null` on the first page. |
| `meta.span.toSource` | Where `to` came from. `"page"` means the first page or the page's own window. `"newest-filing"` means the newest filing from the cached first-page scan or the SEC submissions list. |
| `meta.span.partial` | Present (true) when the scan behind the window is partial. |
| `meta.window` | **Unchanged, kept for compatibility:** this page's own window (`label`, `from`, `to`, `filings`, `more`, `next`). Keep using `meta.window.next` for Load older. `meta.window.fromUk` / `toUk` are added. |

- Free users see `meta.span.label` equal to `meta.window.label` ("Latest 5 open-market trades"), with empty from/to.

**Display dates** (one format, `D Mon YYYY`, e.g. "15 Oct 2025"; `""` when there is no date). The ISO fields are unchanged.
| Object | ISO field (unchanged) | Display field (new) |
|---|---|---|
| `insider[]` row | `transactionDate` | `transactionDateUk` |
| `insider[]` row | `filingDate` | `filingDateUk` |
| `house.items[]` filing | `filingDate` | `filingDateUk` |
| `house.items[].trades[]` (when parsed) | `date` | `dateUk` |
| `meta.window` / `meta.span` | `from`, `to` | `fromUk`, `toUk` |

The client today prints `transactionDate` raw in some places and its own format in others. Switching to the `…Uk` fields gives one format.

Evidence: insiders_span_dates.txt (replay of recorded real sec.gov responses, before and after), earnings_samples.txt, financials_mu.txt.

**Known difference, already in 64t:** a ticker question that mentions earnings but is not a card ("When does MU next report earnings, and how has it moved?") is composed from the peer facts on the stream path and from the move lead on the JSON path. bb8l adds the Next earnings line on both paths: in the lead on JSON, and before `In short:` on the stream. The other sentences and sources still differ the way they did before (evidence/earnings_samples.txt and sources_check.txt show it for both before and after). Card, valuation and general answers match between stream and JSON.
