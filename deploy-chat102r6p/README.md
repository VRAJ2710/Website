# deploy-chat102r6p

Fix Terminal `/api/c102/terminal` previous close for DX-Y.NYB, ^VIX and ^TNX.

`c102YahooQuote` used `meta.previousClose || meta.chartPreviousClose` on a `range=5d&interval=1d` Yahoo chart. On that request Yahoo omits `previousClose` and sets `chartPreviousClose` to the first daily close in the window (for DXY on 13 Nov 2026, Monday 9 Nov 101.65), so the day change was wrong. Market-reference-quotes and `/api/c100/macro` already used the last completed session close.

This installer replaces only the last-write scrub. The prefix sha is unchanged. A new `c102r6pSessionPrev` helper takes the last non-null daily bar whose session date is before the current session (from `regularMarketTime` in the exchange timezone). `chartPreviousClose` is never used for that decision. Additive fields: `prevAsOf` (YYYY-MM-DD) and `prevAsOfUk` (Europe/London). The ICE DX-Y.NYB series is unchanged; the Dispatch FX basket (DXY_FX) is not used. The 1d / 1m quote path is left as it was.

Does not start the server, npm, git, or republish. No new secrets, tables, timers, or paid feeds.

Base: current Replit dev at fef1da0. Guards:

- server.js md5 `9c593e7ab7887a20ba876e938abca0fc` (mismatch refuses and leaves files untouched)
- app.js md5 `d8ca8562df01bf88c68e4971752e602c`
- index.html md5 `23e26d5287a773dadaf3fd2c40deb389`
- prefix sha `8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae` (2,332,205 bytes)
- NEW_L1 and MARKER unchanged; tag remains chat102r6p
