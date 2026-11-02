# chat99 (on chat98): built and tested, not published

- SEC company deep-dives `/research/sec/<TICKER>/` for any US filer, beyond the 19 monitored companies.
  - Data comes from SEC XBRL companyfacts: 5 years of 10-K revenue, operating and net income, cash flow,
    free cash flow, cash, debt, equity and EPS.
  - Each one has bar charts, plain-English lines, the source, and the UK download time.
- Filings screener `/research/sec/screener/`, built from SEC XBRL frames.
  - Filters: revenue, growth and margins. Shows the top 100.
  - An admin builds it once, which costs 7 or 8 SEC downloads. It's cached for 40 days.
- Cap: 25 SEC downloads a day in total.
  - BB11_MAX_FACTS_PER_DAY goes from 4 to 25, sharing the existing bb11:sec_downloads counter.
  - Each member can trigger 5 a day. Cached deep-dives cost nothing.
  - It needs DISPATCH_SEC_UA. Without it, downloads are switched off and nothing is counted.
- Ask with charts, for both BYOK and the site AI: when a question names gold or a ticker, the answer gets a six-month
  Yahoo (delayed) chart. It shows a plain name, the source, the UK as-of time, and "Not investment advice. Capital at risk."
- No DDL. It reuses dispatch_openbb_research_cache.
