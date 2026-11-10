# CPI day (chat103) — design proposal

Public page at `/cpi/` on The Dispatch Market. Release tag `chat103`. This sits on the chat102r4 root (installer commit `bde7d247`, payload `cd0161a`). It does not publish, does not touch Replit, and does not change Stripe.

Checked against the BLS public API and the BLS news-release calendar on 10 November 2026. The latest index month in that pull was September 2026. The ICS lists CPI at 08:30 US Eastern from 15 January 2025 through 10 December 2026. The HTML schedule adds 13 January 2027, 08:30, as the December 2026 reference month.

## Data sources

| Reading | Source | What we refuse |
| --- | --- | --- |
| Release instants | BLS calendar `https://www.bls.gov/schedule/news_release/bls.ics` (`DTSTART;TZID=US-Eastern`, summary exactly `Consumer Price Index`). On 10 Nov 2026 that file runs from 15 Jan 2025 through 10 Dec 2026. The CPI HTML schedule `https://www.bls.gov/schedule/news_release/cpi.htm` adds the reference month and the 2027 dates, including 13 Jan 2027 08:30. A date in both uses the ICS instant. | PPI and import-price rows. A date typed in by us, except the labelled fallback below. |
| Headline and core indexes, category indexes | BLS Public API `https://api.bls.gov/publicAPI/v2/timeseries/data/`, POST, no registration key unless `BLS_API_KEY` is already in the environment. v1 is the same host with `/v1/` if v2 refuses. | FRED. Any number not present in the response or in a stored release. |
| Month and year percent changes | Computed here from those index levels. Month change uses the seasonally adjusted series. Year change uses the not-seasonally-adjusted series. Shown to 1 decimal, half away from zero, which matches the September 2026 news release (0.6 / 3.7 headline, 0.3 / 2.6 core). | BLS `calculations=true` (the keyless API disabled it on 10 Nov 2026). A rounded figure with no index behind it. |
| Relative importance | BLS CPI news release Table 1, `https://www.bls.gov/news.release/cpi.t01.htm`, which prints the prior-month weight. Citation also names `https://www.bls.gov/cpi/tables/relative-importance/`. | A weight we added up ourselves. A contribution when the weight did not parse. |
| Gold around past releases | Yahoo Finance delayed COMEX front-month futures, the same chart host the Terminal already uses. Label, exactly: `Gold futures (COMEX, front month), Yahoo Finance delayed`. | The word spot. A raw ticker. A forecast, a tip, or any “what to expect” line. |
| Our own gold tape from 10 Dec 2026 | Rows we write in `cpi_gold_snapshots` only while the process is inside a release window on or after that date. | Backfilling old releases with a pretend 08:30 print. |

Labelled fallback, used only when that civil date is absent from the cached calendar, and always captioned as a fallback: 10 December 2026 08:30 US Eastern, and 13 January 2027 08:30 US Eastern. On 10 Nov 2026 the December date is already in the calendar, so only 13 January 2027 needs the fallback until BLS extends the file.

UK time uses `Europe/London`. The zone name is GMT or BST from `Intl`, not a fixed offset. 08:30 US Eastern is 13:30 in London when both sides are on standard time or both are on daylight time, and 12:30 in London in the March and late-October weeks when only the US has changed.

## Series IDs

CPI-U, US city average. `CUUR` is not seasonally adjusted (year change). `CUSR` is seasonally adjusted (month change). Item codes were checked against `cu.item` on download.bls.gov. Each ID below returned September 2026 observations from the public API on 10 Nov 2026, except Recreation, whose item code `SAR` is in `cu.item` and is requested the same way; a failed id is left blank rather than swapped.

| Category | Month series | Year series |
| --- | --- | --- |
| All items | CUSR0000SA0 | CUUR0000SA0 |
| All items less food and energy | CUSR0000SA0L1E | CUUR0000SA0L1E |
| Food | CUSR0000SAF1 | CUUR0000SAF1 |
| Food at home | CUSR0000SAF11 | CUUR0000SAF11 |
| Food away from home | CUSR0000SEFV | CUUR0000SEFV |
| Energy | CUSR0000SA0E | CUUR0000SA0E |
| Energy commodities | CUSR0000SACE | CUUR0000SACE |
| Energy services | CUSR0000SEHF | CUUR0000SEHF |
| Gasoline (all types) | CUSR0000SETB01 | CUUR0000SETB01 |
| Shelter | CUSR0000SAH1 | CUUR0000SAH1 |
| Rent of primary residence | CUSR0000SEHA | CUUR0000SEHA |
| Owners' equivalent rent of residences | CUSR0000SEHC | CUUR0000SEHC |
| Apparel | CUSR0000SAA | CUUR0000SAA |
| New vehicles | CUSR0000SETA01 | CUUR0000SETA01 |
| Used cars and trucks | CUSR0000SETA02 | CUUR0000SETA02 |
| Medical care | CUSR0000SAM | CUUR0000SAM |
| Medical care commodities | CUSR0000SAM1 | CUUR0000SAM1 |
| Medical care services | CUSR0000SAM2 | CUUR0000SAM2 |
| Transportation services | CUSR0000SAS4 | CUUR0000SAS4 |
| Commodities less food and energy commodities | CUSR0000SACL1E | CUUR0000SACL1E |
| Services less energy services | CUSR0000SASLE | CUUR0000SASLE |
| Recreation | CUSR0000SAR | CUUR0000SAR |

Keyless v2 allows 25 series per query, so a refresh is two POSTs (50 with a key would still be two, because the list is 44). Ten years of months is inside the keyless limit. A key, when present, is sent as `registrationkey` and the start year moves back to twenty years. No new secret is added.

Approximate contribution is `(relative importance ÷ 100) × category month change`, in index percentage points. The weight is the Table 1 weight for the month before the change (August 2026 weights beside the September change). The line on the page is exactly `approx. contribution, our calculation from BLS data`. Medical care as a whole has an index but, in the September 2026 Table 1, no single weight row; its contribution stays unloaded. The commodities and services rows have weights and can show a contribution.

September 2026 checks, from the API indexes and the news release: headline SA 334.131 → 336.298 is 0.6 percent; headline NSA 324.800 → 336.940 is 3.7 percent; core SA 337.765 → 338.896 is 0.3 percent; core NSA 330.804 → 339.287 is 2.6 percent.

## Schema

New tables only. `CREATE TABLE IF NOT EXISTS`. No foreign keys into existing tables, so nothing about `dispatch_users` changes.

- `cpi_releases` — one row per reference month (`period` `YYYY-MM`). Release instant, whether that instant came from the calendar or the labelled fallback, headline and core changes, BLS fetch time, and the JSON we are willing to serve again.
- `cpi_series_values` — `(series_id, period)` and the index level. Archive months are rebuilt from these rows.
- `cpi_gold_reactions` — one row per release instant. Anchor price (last completed bar before 08:30 US Eastern), the +1 hour bar where hourly data exists, the +1 trading day close and the +5 trading day close. Nulls stay null.
- `cpi_gold_snapshots` — observations this process saved on or after 10 December 2026. `window_kind` is `pre`, `plus_1h`, or `session`. Unique on release instant, kind, and observed time.
- `cpi_notice_dismissals` — `(user_id, release_key)` for the in-app banner. No email table and no mail call.

Gold windows. Hourly bars are timestamped at the start of the hour. The anchor is the last bar that ends at or before 08:30 US Eastern, and only if that bar ended within three hours of 08:30. The +1 hour price is the close of the first later bar that ends at or after 09:30 US Eastern. Daily bars use the session date in `America/New_York`. The anchor session is the last session before the release date. +1 trading day is one session after that anchor (the release day’s close, when the market was open). +5 trading days is five sessions after the anchor. Older than the hourly feed (about two years) leaves the hour cell empty and still shows the daily cells when those bars exist.

## Routes

- `GET /cpi` redirects to `GET /cpi/`.
- `GET /cpi/` is the page shell. It does not embed figures.
- `GET /api/c103/cpi` is the JSON the page draws.
- `POST /api/c103/notice/dismiss` stores a dismissal for the signed-in user. Guests get 401.

The header `C93_NAV` gains CPI Day immediately after Markets, so it sits between Markets and Research. All sections gains the same URL inside Gold and macro, immediately after Terminal when that link is present. Existing links stay, in their existing order. Admin Console is untouched and still depends on the existing admin check.

Sitemap gains `/cpi/` the same way Terminal was added.

## Caching and latency

Same shape as chat102r4. The page and the JSON read an in-memory model and return. They do not wait on BLS or Yahoo.

- Fresh for 15 minutes, then the stored model is served with `Cache-Control: private, max-age=0, stale-while-revalidate=120` and a note that it is the stored release, not a new print.
- A missing model returns `not loaded yet`, `Cache-Control: no-store`, and starts one background refresh.
- One refresh per key (single-flight). A second request does not start a second fetch.
- Each upstream attempt dies at 2.5 seconds. The production path uses `https.request` and calls `req.destroy()` so the socket is aborted, not only the promise.
- A refresh that fails does not replace a stored release. The stored row keeps its fetch time.
- Schedule is refreshed in the background about daily. Series are refreshed in the background about every six hours, and sooner when a release instant has passed and that reference month is not stored yet. Gold history is refreshed about hourly. Monthly CPI does not need a call per page view.
- Database reads are not on the BLS/Yahoo path. Boot hydrates memory from the new tables. A request never runs DDL. DDL runs once, off the request, and only the five statements above.
- Empty Neon lookups use `json_agg`, so a missing row comes back as `[]`.

## Gating

The existing check is `user.tier === "premium"` or `isAdminUser(user)`, the same one the brief uses. No Stripe change.

Free JSON has countdown, headline, core, the 24-month trend, and the headline/core archive. Premium JSON adds `categories`, `contributions`, and `gold`. Those keys are omitted on the server for everyone else, not hidden with CSS. The static HTML has no figures in it.

The “CPI is out” banner is for any signed-in reader, once per release, and only after that release’s figures are actually stored. Dismiss writes `cpi_notice_dismissals`. There is no mail.

## Layout

Terminal density: 15px body, site type and the c97 variables (`--ink`, `--paper`, `--rule`, `--pos`, `--neg`, `--gold`). Light, dark, and system all come from those variables, including `prefers-color-scheme` on `html.c93.c97-system`. The canvas reads the computed colours and redraws when the theme class changes.

- 1280: four figure cards in a row, the trend chart full width, then the archive. Premium adds the category table and the gold table beside each other.
- 390 and 320: one column. Cards stack. Nothing on the page scrolls sideways.
- Tables live in their own `overflow-x: auto` box with a caption, a row header, and `overscroll-behavior-x: contain`.
- The chart is a `canvas` with `role="img"`, a text summary, and the same numbers in a table underneath. Arrow keys move a polite live region. `touch-action: pan-y` so the page still scrolls.

Every card says what the number is, which source and date it came from, and why it is on the page, in plain language. A failed card says `not loaded yet` or shows the stored release with its date.

## Installer

`deploy-chat103/deploy.sh` follows deploy-chat102. It refuses any project root that is not the chat102r5 server (payload `023165d`, installer `5fe33d23`):

- chat102 tail sha256 `099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054`
- `app.js` md5 `b84058f6da16ad022640b06c9cdda72d` (unchanged from r4)
- `index.html` md5 `b3e02b0c6e403133843a96adf45d219c` (unchanged from r4)
- full `server.js` md5 is the r5 file: the r4 prefix (the bytes before the chat102 marker in the file whose md5 is `5e8e3e34b6c71ae9e510c40b298ee6fc`) plus the r5 tail. That prefix is not in this repository. The installer prints the full md5 once it is on that root, and refuses a different tail.

A failed BLS series, the schedule, the weight table, the hourly gold feed, or the daily gold feed keeps that feed’s last good values, with the original source and as-of time, and the note “Stored reading from … It was not refreshed. It is not a new print.” “No number was filled in” is only for a feed that has never succeeded.

It downloads a pinned payload commit, checks those blob hashes, and runs the DDL audit. `--dry-run` leaves the project root untouched. Any refusal exits non-zero. An apply copies `*.bak-chat103` backups, appends the server block after the chat102 tail, adds the `/cpi/` boot guard and the menu block to `app.js`, and swaps the cache token to `app.js?v=chat103`. It does not start the server and does not republish.

## Risks

1. The keyless quota is 25 queries a day. A restart loop could spend it. The refresh backs off once a stored month exists, and a failure keeps the stored release.
2. Table 1 HTML is the weight source and BLS can change the markup. If the parse fails, contributions are `not loaded yet` rather than a guessed weight.
3. Yahoo hourly history is about two years, and the bars are hourly, so +1 hour lands on the 09:00–10:00 bar’s close (10:00 US Eastern), not on 09:30 exactly. The cell shows both bar times.
4. The snapshot recorder only writes while this process is awake inside the window. A sleeping host misses that print. It does not invent one later. The Yahoo history still fills the public table for past days.
5. If a later calendar file drops 13 January 2027, the labelled fallback still shows it and the caption says it was not in the cached schedule. While the HTML table contains it, the caption cites the HTML schedule instead.
6. This checkout does not contain the chat102r4 root bytes, so the success-path dry-run can only be executed on the machine that has those files. The refusal path is tested here.
