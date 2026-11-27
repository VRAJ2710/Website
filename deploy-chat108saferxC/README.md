# deploy-chat108saferxC (27 Nov 2026): v3 home preview fix, main figure = latest delayed quote

Preview only. Apply AFTER deploy-chat108saferxB. One block is appended after the B block; no existing byte of server.js
changes; app.js and index.html are not touched. Nothing is published.

Rule (Vraj): when a free live or delayed quote exists it is the MAIN number, with a "Delayed" lag label and UK time; the
official or daily close goes on a secondary line.
- Gold futures chart card: main figure = latest Yahoo Finance delayed quote for the same continuous front-month series
  (e.g. $3,711.1, Fri 27 Nov 09:11 UK, Delayed). The 3-month change is measured from the first close in the 63-session window
  to that quote, and says so. Secondary line: "Last completed close $3,535.8, 25 Nov 2026 (New York session), -21.95% close
  to close over 3 months, Daily close". "Futures, not the spot price" and the source line are kept. If there is no fresh
  quote (newer than the last session and from today UK or the last 12 h), the close stays the main figure, labelled
  "Last close", with the change marked "close to close" and the newest stale quote named.
- Other v3 cards: a figure dated before today (UK) is relabelled "Last close" instead of "Delayed"/"Live": key prices and
  five things that moved (e.g. S&P 500, Wed 25 Nov 21:32 UK), range bars and chart tiles (e.g. US 10-year, S&P 500).
  Already correct and untouched: snapshot (no figure without its card), events, Bitcoin/WTI tiles, regime gauge.

How: the B-built preview page loads the renderer from /__v3p/home.js?v=chat108saferxC (plus /__v3p/c10.css). Only that URL is
served with 7 exact, counted text replacements (src/patches.py + the rGold swap); if any is missing, the file is served
unchanged. /__v3p/home.js at its old URL, /, /?preview=off and every other route are byte-identical (tested).

Guards: server.js 2,500,286 B, md5 4228d5923590382ab8f3dc71830139c2 (dev after B), ends byte-exact with the chat108saferxB
block (sha256 bd06d3bc...), A, B TAGs once, softgate/VERIFY_ENFORCE/r6p/credits/v3home2 once, no r6o, no chat108saferxC.
app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389.
Modes: --measure | --dry-run | apply (timestamped .bak-chat108saferxC backups; second run refuses). After applying, restart
ONLY "Start application"; expect one "[chat108saferxC] preview attached" line after the B line. Undo: copy the .bak back.
No DB, DDL, payments, email, secret, config, storage or network use.
Tests: test/run_deploy_tests.sh (26 checks, including the transform and patch on the REAL dev B page and REAL dev renderer).
