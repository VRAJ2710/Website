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
- Extras:
  - `/markets/yields/` Gilt and Treasury yields: US Treasury daily par yield curve CSV (home.treasury.gov) and the
    Bank of England par gilt yields (IADB). Curve chart (latest and a month earlier), week and month changes,
    plain-English gaps (US 10y vs 2y, UK 20y vs 5y, UK vs US 10y), end-of-day date and "Checked <UK time>". Cached 3h / 6h.
  - `/gold/positioning/` Gold positioning: CFTC disaggregated Commitments of Traders (Socrata, free), money managers'
    net position, ten-year percentile and range, chart, report date and checked UK time. Cached 12h. No buy/sell wording.
  - Both are free official sources, no keys. If a source does not answer, the page says so and shows no figures.
  - Both are gated by maintenance like every other page, and are added to the menu.
  - `/data-status/` Data status: each free feed's source, how often we check, last good copy (UK time) and status
    (up to date / last good copy / not answering / not checked since restart). Read from memory only, no outbound calls.
    Links to /corrections and repeats the "needs a paid source" note. Linked from the menu and the two pages above.
- Fix: the guest brief "for members" box (chat96) had a white background in dark mode; chat99 adds a dark override.
- No DDL. It reuses dispatch_openbb_research_cache.
