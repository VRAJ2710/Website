# Insider and House disclosures

`GET /api/insiders?t=TICKER[&codes=all][&house=1]`

Server only. Guests and free members get the last five non-derivative open-market rows (codes P and S). `hasPremiumAccess` (premium members and admins) can request every transaction code and the House list. The client is unchanged.

Source is SEC EDGAR. No API key. Calls send `User-Agent: TheDispatchMarkets admin@thedispatch.uk` and stay at or under 10 requests a second. Form 4 bodies are cached for 6 hours. The House yearly index is cached for 24 hours. A miss is refreshed on the next request. There is no background job.

## Query

| Param | Values | Who |
|---|---|---|
| `t` | ticker, required | everyone |
| `codes` | `all` includes A, M, F, other codes, and derivative rows | premium only; ignored otherwise |
| `house` | `1` adds the House section | premium only; otherwise `house` is `null` |

## 200, free

```json
{
  "ticker": "AAPL",
  "cik": "0000320193",
  "company": "Apple Inc.",
  "asOf": "2026-10-19T12:00:00.000Z",
  "stale": false,
  "source": { "name": "SEC EDGAR", "url": "https://www.sec.gov/edgar" },
  "explainer": {
    "what": "Form 4 is the filing a company insider (director, officer or 10% owner) must make within two business days of trading the company's shares.",
    "where": "From SEC EDGAR, the US regulator's public filing system.",
    "why": "Open-market purchases (code P) and sales (code S) show what insiders did with their own money. Sales are often routine (tax, diversification, pre-set 10b5-1 plans), and this is a disclosure, not a signal to trade.",
    "house": "Members of the US House must report securities trades over $1,000 within 45 days in a Periodic Transaction Report; amounts are disclosed as ranges."
  },
  "insider": [
    {
      "insiderName": "COOK TIMOTHY D",
      "insiderRole": "director, Chief Executive Officer",
      "transactionCode": "P",
      "codeLabel": "Open-market purchase",
      "shares": 100,
      "price": 10.5,
      "value": 1050,
      "sharesOwnedAfter": 500,
      "transactionDate": "2026-03-02",
      "filingDate": "2026-03-07",
      "acquiredDisposed": "A",
      "isDerivative": false,
      "accession": "0000320193-26-000010",
      "filingUrl": "https://www.sec.gov/Archives/edgar/data/320193/000032019326000010/0000320193-26-000010-index.html"
    }
  ],
  "house": null,
  "meta": { "limited": true, "count": 1, "codes": "PS", "upgrade": "premium" }
}
```

`acquiredDisposed` is `A` (acquired) or `D` (disposed). `filingUrl` is the EDGAR index page. `meta.count` is the number of rows returned, at most 5 for a free response. `meta.upgrade` is present only when `limited` is true.

## 200, premium `codes=all`

Same object. `meta.limited` is false, `meta.upgrade` is omitted, `meta.codes` is `"all"`, and `insider` includes grants (A), exercises (M), tax withholding (F), and derivative rows (`isDerivative: true`). The fetch cap is the latest 40 Form 4 and 4/A filings.

## 200, premium `house=1`

`house` is an object. `package.json` has no `pdf-parse` or `pdfjs-dist`, so every filing is listed and marked `See filing`. A text-layer parser is in the server for a future library; scanned or unreadable PDFs stay `See filing`.

```json
{
  "items": [
    {
      "member": "Hon. Mark Alford",
      "state": "MO",
      "district": "04",
      "filingDate": "2026-03-31",
      "docId": "20034201",
      "pdfUrl": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20034201.pdf",
      "parsed": false,
      "note": "See filing"
    }
  ],
  "asOf": "2026-10-19T12:00:00.000Z",
  "note": "No PDF text library is installed, so each Periodic Transaction Report is listed with its link and marked See filing."
}
```

When a PDF text layer can be read, a matching trade is `{ asset, ticker, type, date, amountRange, owner }` and that filing's `parsed` is true. Senate filings are not included.

The index is `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.zip` (the XML inside). Only `FilingType` `P` is returned.

## 200, no Form 4 filings

ETFs and funds that have a CIK but no Form 4 come back with `insider: []` and `note: "No Form 4 filings for this ticker."`

## 200, EDGAR down

Warm cache: the last body, with `stale: true` and `asOf`. Headers: `X-Dispatch-Data-Status: stale` and `X-Dispatch-As-Of` set to that timestamp. A 429 uses this same path.

No cache:

```json
{ "unavailable": true, "message": "Insider filings unavailable right now" }
```

Header: `X-Dispatch-Data-Status: unavailable`.

## 404, unknown ticker

```json
{ "error": "Unknown ticker." }
```

## 400

`t` missing or not a ticker: `{ "error": "Ticker required." }`
