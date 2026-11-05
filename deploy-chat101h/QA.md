# chat101h QA — 5 November 2026

## Mechanism

The public Research page at `/research/` is still the server-rendered hub (Capital Sustainability Monitor, then Check and plan, then Also from the desk). There is no article CMS import. chat101h appends a block that:

- serves three article URLs for every reader, including signed-in free, premium and admin, and admin guest preview
- inserts a “Sourced notes” list on `/research/` without removing the monitor, tools or desk links
- adds the three URLs to the sitemap
- links the same three notes from the top of the signed-in Research desk

Existing routes such as `/research/capital-sustainability`, `/research/sec/`, `/research/filing-changes/` and `/research/research-desk/` are not claimed by the new matcher.

## Source check

- Bank of England monetary-policy summary, raw HTML, 20:01 UK (GMT): meeting ending 4 November 2026, vote 8–1, Bank Rate increased 0.25 percentage points to 4%, dissenter preferred a larger increase. Published 5 November 2026.
- November 2026 Monetary Policy Report, raw HTML: Box A, indirect effects, fixed-price contracts and hedging, and risk premia in the market curve are on the page. The article does not add the report’s CPI, oil or projection figures.
- Federal Reserve TIPS yield-curve page and the 21 May 2019 staff note, both HTTP 200 at 20:01 UK. The curve page says inflation compensation may be driven by risk premiums, and that the curve is hypothetical, delayed and revised.
- IMF guide PDF returned HTTP 403 from this network (Akamai). The reserves note keeps the 19:50 UK citation and does not add a later check or any current total.

## Tests that passed

`node deploy-chat101h/t_c101h.js`: 126 passed, 0 failed.

- Fixture server: all three articles for guest, free, premium and admin; disclaimer, “Edited by Vraj Patel”, canonical URL, JSON-LD editor and no author field, source links, slash redirects, sitemap entries.
- Hub still contains the monitor, Check and plan, and Also from the desk.
- Existing fixture routes are not rewritten.
- Admin guest preview still renders the article as a guest.
- Downloaded live `app.js` matched md5 `0b4c442a055584920d9539fb50c9a7f1`. After the append, `node --check` passed. A second patch is refused. The append hash is unchanged by the London scrub: md5 `6c8ddd1be4db078df1de146163f99b11`, sha256 `80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989`.
- The dry-run London guard matches no line in the patch files. `patch_c101h.py` sha256 `958fd7f71273c37ca532afca283e58c70610755e8542e4bb2ae85ef9dc768b07`. Server and app blocks are unchanged: `f8d60e6d7814374ba60c174ac07b179fa7808da0e5937c204838ceaf2a043db6` and `d3ea0f5453b9dfa38d93da83de4395c82d5f0bb5225c008532e51c7fe651805b`.
- `bash deploy.sh --dry-run --dir` on this git checkout aborted because `server.js` is not the live file (md5 `2954f8b7`). It did not modify `server.js`, `app.js` or `index.html`.

Chrome (headless) on the fixture, 320 / 390 / 1280, light and dark: no horizontal overflow, disclaimer visible, article cards navigate, back link returns to Research, Federal Reserve source is an absolute link. Screenshots are in the run artifacts.

Chrome on the current live site, guest, 390 and 1280, 36 existing routes including `/`, `/research/`, gold, brief, markets, the monitor, filings, tools, central banks, dashboard and offline: each returned 200 and did not overflow horizontally. That is the site before this patch is republished.

## Gaps

- `deploy.sh --dry-run` was not completed against the production `server.js` and `index.html`. Those files are not in git and are not served publicly. The script will abort, without writing, if the live md5 or sha256 differs from chat101g.
- No logged-in production session was used. The Account drawer was not opened on the live site in this run. The patch does not edit that drawer; the live `app.js` bytes before the append are unchanged. Role HTML was checked on the fixture, not by signing in on thedispatch.uk.
- The live Research menu was not tap-tested after a failed click on a non-clickable summary. The fixture menu is a simplified stand-in and is not the production menu.
- The IMF PDF was not re-read.
- PWA manifest and service worker are unchanged. They were not retested beyond the existing live `/offline/` page returning 200.
