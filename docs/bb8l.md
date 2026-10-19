# bb8l: UK time in user-visible text and model prompts (server only)

Stacked on bb8k. server.js md5 `0510fe845e43ec1e865dbc4257b00418` (15197 lines) becomes `122d59534f69d67583a0e1080fc9a724` (15317 lines).
The patch makes one in-place edit (the rt39s gold reply prefix; its anchor matches once) and appends one block (`// ── bb8l ──` … `// BB8L_JS_END`). app.js and index.html are not touched. It adds no tables, intervals, timers, dependencies, secrets or Stripe/auth/webhook changes.

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
