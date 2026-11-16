# FRED series used by the site (checked 16 Nov 2026)

Found in: the Nov 6 server.js snapshot and later installer blocks on the box (c97Fred, rt53/rt44, c101, c102), the live dev
app.js (md5 8726da25...), and public GET reads of the dev pages and APIs on 16 Nov. Copyright tag read from FRED's public
tag listings (fred.stlouisfed.org/tags/series?t=public+domain:+citation+requested;...), and each series page shows no copyright
notice. No FRED API key is on the box, so the fred/series/tags API was not used.

| ID | Plain name | Original source | FRED copyright tag | Where shown | Action |
|---|---|---|---|---|---|
| DGS10 | US 10-year Treasury yield, official daily | Board of Governors of the Federal Reserve System (US), H.15 | Public Domain: Citation Requested | Home/markets/gold tables, gold dashboard, v3 preview prices card, Terminal | Citation line |
| DFII10 | US 10-year real yield (TIPS), official daily | Board of Governors of the Federal Reserve System (US), H.15 | Public Domain: Citation Requested | Same as DGS10; scenario tool model | Citation line |
| DTWEXBGS | Broad trade-weighted US dollar index | Board of Governors of the Federal Reserve System (US), H.10 | Public Domain: Citation Requested | Scenario tool model sources | Citation line |
| DCOILWTICO | WTI crude spot | U.S. Energy Information Administration | Public Domain: Citation Requested | Oil spot row when the EIA feed falls back to FRED (live on 16 Nov: "EIA via FRED") | Citation line only while FRED is the source |
| DCOILBRENTEU | Brent crude spot | U.S. Energy Information Administration | Public Domain: Citation Requested | Same, Brent row | Citation line only while FRED is the source |
| PAYEMS | US nonfarm payrolls | U.S. Bureau of Labor Statistics | Public Domain: Citation Requested | Macro calendar | Citation line |
| UNRATE | US unemployment rate | U.S. Bureau of Labor Statistics | Public Domain: Citation Requested | Macro calendar | Citation line |
| PCEPI | US PCE price index | U.S. Bureau of Economic Analysis | Public Domain: Citation Requested | Macro calendar | Citation line |
| A191RL1Q225SBEA | US real GDP growth | U.S. Bureau of Economic Analysis | Public Domain: Citation Requested | Macro calendar | Citation line |
| DFEDTARU | Fed funds target range, upper | Board of Governors of the Federal Reserve System (US) | Public Domain: Citation Requested | Macro calendar | Citation line |
| DFEDTARL | Fed funds target range, lower | Board of Governors of the Federal Reserve System (US) | Public Domain: Citation Requested | Macro calendar | Citation line |
| CPIAUCSL | US CPI | U.S. Bureau of Labor Statistics | Public Domain: Citation Requested | Fetched by the old calendar code; the live calendar now shows US CPI from BLS directly | Citation line if it ever shows |

No series is Copyrighted, so nothing is hidden. The hide switch exists per series ("hide": true in series.json shows
"Not shown: awaiting publisher permission" in place of the figure and keeps the section and its menu link).
Names only, never fetched in the code seen: DGS2, DGS30, T10YIE, CPILFESL, DFF (labels in the r6p FRED_NAME map).
