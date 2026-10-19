# bb8 API changes

Server-only patch `deploy/patch_bb8.py`, stacked on bb7 (server md5 `e10bf8fdeb7f9c7f3265ab2a0e0ec549`). The client is unchanged. Everything in `docs/bb7-api.md` still applies. This file lists what bb8 adds.

## /api/insiders

`GET /api/insiders?t=TICKER[&codes=all][&house=1][&before=YYYY-MM-DD]`

### `meta.window` (new, every 200 response)

Premium:

```json
"meta": {
  "limited": false, "count": 34, "codes": "PS",
  "window": { "label": "Last 6 months", "from": "2026-04-16", "to": "2026-10-13", "filings": 40, "more": true, "next": "before=2026-04-16" }
}
```

- `label` describes the span of Form 4 filings that were scanned. The default load scans the latest 40 Form 4 and 4/A filings, so the span depends on the company: about 6 to 8 months for AAPL. The UI should show `label` as the section caption, for example "Last 6 months".
- `from` and `to` are the oldest and newest filing dates scanned.
- `more` is true when older Form 4 filings exist. `next` is the query to append to load the next page.

Free:

```json
"meta": { "limited": true, "count": 5, "codes": "PS", "upgrade": "premium", "window": { "label": "Latest 5 open-market trades", "premiumOnly": false } }
```

### `before=YYYY-MM-DD` (new, premium only)

This returns the next 40 Form 4 filings dated before `before`, in the same object shape, with `meta.before` echoed back. For guests and free members the parameter is ignored and they get the normal five-row response. A malformed date returns 400 `{ "error": "before must be YYYY-MM-DD." }`. Each page is cached for 6 hours. The default load makes no extra EDGAR calls because of this parameter. A page costs one submissions call plus one call per filing, only when the user asks for it.

### EDGAR cost per load

Form 4 XML is now read directly: the `primaryDocument` path without its `xslF345X0n/` prefix. That takes one request per filing. bb7 used three requests per filing: the rendered HTML, `index.json`, then the XML. A cold premium AAPL load measured 122 EDGAR requests and 12.2 s on bb7. On bb8 it measured 44 requests and 4.5 s, including the House index. The 10 requests per second token bucket is unchanged.

### Cold cache (fail-soft)

On a cache miss the server waits up to 8 s for EDGAR. If a fast failure leaves more than 1.5 s, it retries once. The 8 s limit keeps the answer inside the client's 12 s abort.

- If the load finishes in time, the normal response is returned (`X-Dispatch-Data-Status: fresh`).
- If not, and an older cached copy exists, that copy is returned as `stale` (as in bb7).
- If not, and some filings are already parsed, they are returned as a partial response. The fetch keeps going in the same request's promise and fills the cache, so a refresh a few seconds later is complete.

```json
{ "...": "...", "meta": { "partial": true, "window": { "label": "Last 3 weeks" } }, "note": "Showing the filings loaded so far. Refresh in a few seconds for the full list." }
```

Header: `X-Dispatch-Data-Status: partial`.

- Otherwise it returns `{ "unavailable": true, "message": "Insider filings unavailable right now" }` as before.

### House section (`house=1`)

```json
"house": {
  "label": "Latest House trade filings (all members)",
  "scope": "all-members",
  "tickerFiltered": false,
  "items": [ { "member": "Hon. Jane Doe", "state": "CA", "district": "11", "filingDate": "2026-10-10", "docId": "20012345", "pdfUrl": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20012345.pdf", "parsed": false, "note": "See filing" } ],
  "asOf": "...", "note": "..."
}
```

The House Clerk index has only member, district, filing date and DocID. It has no ticker or issuer, so filings cannot be matched to the ticker without reading the PDFs. Nothing is flagged per ticker, and the list is labelled as all members.

## Ask (`/api/chat`)

- **Forward P/E** is now price divided by next-12-month consensus EPS. That EPS is Yahoo `earningsTrend` current-year (`0y`) and next-year (`+1y`) estimates, weighted by the days left in the current fiscal year. Yahoo's own `forwardPE` divides by `epsForward`, which is the **next fiscal year** estimate (`+1y`), so it was 15 to 22 months out and the horizon differed by fiscal calendar. If the NTM inputs are missing, the forward figure is "not reported" rather than Yahoo's number. Peer rows label it "forward P/E (next 12 months)" and show EPS TTM and next-12-month consensus EPS. `/api/fundamentals` `valuation.forwardPe` and `metrics.forwardPE` use the same basis, with `valuation.forwardBasis`.
- **Conclusion**: when peer FACT lines exist, a "cannot compare" sentence is replaced by a conclusion built from those lines. The conclusion names peers whose figure was not reported. The model is told to conclude consistently and never claim the companies cannot be compared.

## Quote notes

`note` reads `delayed N min by exchange` (was `delayed Nm by exchange`) on every server route that sets it.
