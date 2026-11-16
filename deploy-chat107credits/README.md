# deploy-chat107credits (16 Nov 2026)

Data-source credits. Apply AFTER deploy-chat102r6p and deploy-chat106softgate (ebeeb7c0). One self-contained block is appended
after the r6p last-write scrub; no existing byte of server.js changes; app.js and index.html are not touched.

What readers see (nothing else changes):
- Footer, every page with the site footer: "This product uses FRED® data but is not endorsed or certified by the Federal Reserve
  Bank of St. Louis." (auth pages get this line too, but no script).
- /methodology, right under the Sources table: the same notice plus one sentence on how figures are cited.
- Under each card or table that shows a FRED series, a small citation line, e.g. "U.S. Bureau of Labor Statistics, All Employees,
  Total Nonfarm [PAYEMS], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/PAYEMS,
  16 November 2026". The series ID appears only inside that line. The date is the UK date of the cache timestamp of the fetch
  (c97 cache, real-yield cache, oil cache, model cache, or the fetch itself); a series with no recorded fetch gets no date
  rather than an invented one. The v3 home preview gets the same lines (under its prices card).
- Any link to fiscaldata.treasury.gov gets "Source: U.S. Treasury, Fiscal Data" linked to https://fiscaldata.treasury.gov.
  No Treasury Fiscal Data use was found on 16 Nov ("US Treasury via FRED" figures are Federal Reserve H.15 series).

Server side: FRED requests (fred.stlouisfed.org, api.stlouisfed.org) through global fetch are queued one at a time, at least
500 ms apart (<= 2 per second). Every 6 hours, cached FRED data older than 30 days is dropped (c97 "fred:*" and "c101:model"
entries, the real-yield and FRED-sourced oil caches). All FRED caches were already memory-only; nothing is written to disk or DB.

Guards: server.js 2,429,645 B (post-softgate), ending byte-exact with the chat105v3home2 block then the r6p scrub; exactly one
softgate attach, one VERIFY_ENFORCE = false, one r6p attach, no r6o attach, no credits block yet; app.js 8726da25...,
index.html 23e26d52.... The post-softgate md5 was not captured exactly, so it is not pinned; --measure prints it in full, and
C107_SERVER_MD5=<md5> pins it for a run. Modes: --measure (read-only), --dry-run (scratch build), no flag = apply with
timestamped .bak-chat107credits backups. Expect exactly one "[chat107credits] attached" line after restarting "Start application".
