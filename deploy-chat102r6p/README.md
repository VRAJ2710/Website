# deploy-chat102r6p

Fix Terminal `/api/c102/terminal` previous close for DX-Y.NYB, ^VIX and ^TNX.

`c102YahooQuote` used `meta.previousClose || meta.chartPreviousClose` on a `range=5d&interval=1d` Yahoo chart. On that request Yahoo omits `previousClose` and sets `chartPreviousClose` to the first daily close in the window (for DXY on 13 Nov 2026, Monday 9 Nov 101.65), so the day change was wrong. Market-reference-quotes and `/api/c100/macro` already used the last completed session close.

This installer replaces only the last-write scrub. Bytes before the scrub are preserved (prefix sha compared before and after). A new `c102r6pSessionPrev` helper takes the last non-null daily bar whose session date is before the current session (from `regularMarketTime` in the exchange timezone). `chartPreviousClose` is never used for that decision. Additive fields: `prevAsOf` (YYYY-MM-DD) and `prevAsOfUk` (Europe/London). The ICE DX-Y.NYB series is unchanged; the Dispatch FX basket (DXY_FX) is not used. The 1d / 1m quote path is left as it was.

Does not start the server, npm, git, or republish. No new secrets, tables, timers, or paid feeds.

Base: current dev after the v3 home preview blocks (chat105v3home / chat105v3home2) were inserted before the scrub. Guards:

- server.js md5 `7a3aeaf7a9e317ce888e28e4b9d4461a` (mismatch refuses and leaves files untouched)
- app.js md5 `d8ca8562df01bf88c68e4971752e602c`
- index.html md5 `23e26d5287a773dadaf3fd2c40deb389`
- r6o scrub (MARKER to EOF) must be 29,743 B with sha256 `e45d46bf24eca1e3585739491058fc7470b7faffd7ba54600764f90594d63cbc`; the prefix is whatever precedes it and must be unchanged after install
- NEW_L1 and MARKER unchanged; tag remains chat102r6p
