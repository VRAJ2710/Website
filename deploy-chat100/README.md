# deploy-chat100

Small bundle on top of the **live reopen2 build** (maintenance OFF). Line 1 of server.js stays
`const BB10I_MAINTENANCE_ON = false; ...`. c93.css unchanged.

Base (live) md5s: server.js `bd50fb5335bcaf937fa3e68ed3bf96bb`, app.js `9ebadee3093d77dafb70559b4984ee12`,
index.html `79b9249f6afcbf65b0af7464a4c2afb6`, c93.css `9d6a86a64135b1cc58e6af7b12973550`.

What it changes
1. Dashboard: a "Gold and macro" panel first: gold spot, silver, gold in pounds, US dollar index, US 10-year yield,
   US real yield, Brent crude, pound in dollars, S&P 500 (context). Plain names, source and UK time underneath, from the new
   `GET /api/c100/macro` (2-minute server cache, last-known copy kept in the browser). The old default book
   (SPY, NVDA, BTC, XAU, AAPL) becomes XAU, SLV, GBPUSD, DXY, TNX, BRENT, SPX; chips use plain names; "V1 · GOLD FIRST" removed.
2. Fear & Greed: "Not enough data yet" (no needle, no 50/100) until the VIX and 3+ live prices are in.
3. SEC screener: builds itself on the first visit (or 2 minutes after start) when the persisted daily SEC counter
   (bb11:sec_downloads, cap 25) has room for the 7-8 downloads; otherwise retries in 30 min; 6 h back-off on error.
   Until then the page says "Building the screener, check back shortly."
4. Source inspector on figures (Market context / brief figures, gold dashboard, yields, positioning, dashboard tiles):
   source + link, series in plain words, retrieval time (UK), delayed / last-known / official print, and the formula where
   there is one. role=dialog, Esc closes, Tab is trapped, focus returns; bottom sheet at <=600 px; light and dark.

Files: patch_c100.py, server_block_c100.js, app_block_c100.js, t_c100.js (harness test), deploy.sh (sha256-pinned).
No DDL, no Stripe, no env, no package changes. deploy.sh never starts the server.
