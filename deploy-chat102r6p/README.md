# deploy-chat102r6p

Fix Terminal `/api/c102/terminal` previous close for DX-Y.NYB, ^VIX and ^TNX.

`c102YahooQuote` used `meta.previousClose || meta.chartPreviousClose` on a `range=5d&interval=1d` Yahoo chart. On that request Yahoo omits `previousClose` and sets `chartPreviousClose` to the first daily close in the window (for DXY on 13 Nov 2026, Monday 9 Nov 101.65), so the day change was wrong. Market-reference-quotes and `/api/c100/macro` already used the last completed session close.

This installer replaces only the last-write scrub. The prefix sha is unchanged. A new `c102r6pSessionPrev` helper takes the last non-null daily bar whose session date is before the current session (from `regularMarketTime` in the exchange timezone). `chartPreviousClose` is never used for that decision. Additive fields: `prevAsOf` (YYYY-MM-DD) and `prevAsOfUk` (Europe/London). The ICE DX-Y.NYB series is unchanged; the Dispatch FX basket (DXY_FX) is not used. The 1d / 1m quote path is left as it was.

Does not start the server, npm, git, or republish. No new secrets, tables, timers, or paid feeds.

Base: current dev r6o. Agent bc-aa734e0e's r6p was not on GitHub when this was built, so the guards are the r6o app/index md5s, the prefix sha, and the single r6o attach log.
