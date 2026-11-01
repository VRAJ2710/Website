# deploy-chat93 — The Dispatch Market credibility redesign (v2: groups A–G)

Built and tested only. **Not deployed, not published.** Apply only when Vraj says so.

## What it changes
- **A Trust pages**: /about, /methodology, /editorial-standards, /corrections, /contact (server-rendered, ~70 KB each), all in sitemap.xml.
  Byline "Edited by Vraj Patel, London", contact dispatchmarket@mail.grokbot.com, mission line. No photo; no placeholder.
  /manifest.json renamed to "The Dispatch Market" with paper colours.
- **B Look**: paper theme in `c93.css` (free Google Fonts: Source Serif 4 + Inter), text wordmark, plain nav, "Not investment advice. Capital at risk." strip and trust footer on every page; paper-style 404, sign-in, pricing, terms and privacy pages; OG/Twitter tags.
- **C Honest numbers**: no dash, "NO LIVE SYNC", "Not available", "No price yet" or "n/a" values: a failed feed shows the last official figure with its date (server/Treasury/EIA prints or a 14-day browser last-good cache), otherwise the row is left out with one small note; empty sections are hidden; session labels per asset class (US stocks, futures, crypto 24/7, FX); every figure carries source + UK as-of time; desk-score / jargon lines removed.
- **D Company page** (/research/capital-sustainability/TICKER): plain-English summary, UK dates, source line, flag names spelled out.
- **E** SEC daily download counter also saved in the existing `dispatch_openbb_research_cache` table (row `bb11:sec_downloads`; no DDL).
- **G v2 layout (matches the approved mockups)**: signed-out visitors get server-rendered pages: Home (masthead, disclaimer strip, mission hero with byline, Market context table, Today's brief, Capital Sustainability Monitor top 3, footer), Markets, Gold, Brief, Signals, News and Research, all in the research-page style. No ticker tape, "markets trading now" line, macro card grid, watchlist table or session movers for guests. Signed-in desk keeps its tables in the calm style (no tape, light headers, no placeholder rows). Mobile header: Sign in sits in the header row / Menu.
- **F Lighter**: unpkg removed, background polling pauses when the tab is hidden, duplicate GETs share one request. (No code-split.)

Unchanged: maintenance line 1 (`BB10I_MAINTENANCE_ON = true`), Stripe, auth, Admin Console, Academy, Ask, all /api contracts, rate limiter, package.json, .replit, env, DB schema.

## Files
| file | role |
|---|---|
| deploy.sh | sha256-pinned installer (dry-run, idempotent, backups) |
| patch_chat93.py | exact-count edits to server.js, app.js, index.html; aborts without writing if any edit misses |
| c93_pre.js / c93_post.js | front-end additions injected into app.js |
| c93_server_pages.js | trust/pricing/legal/404 page renderer injected into server.js |
| c93_fe88_company.js | company page rewrite |
| c93_live.js | small client script for the server-rendered pages: fills figures from the site's own /api, keeps last-good values |
| c93.css | stylesheet, installed next to server.js and allow-listed as /c93.css |

## Run (Replit Shell, project folder) — only after Vraj's go-ahead
```
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat93-redesign/deploy-chat93/deploy.sh -o /tmp/deploy-chat93.sh
bash /tmp/deploy-chat93.sh --dry-run
bash /tmp/deploy-chat93.sh
```
Requires live md5s server df10e32f…, app 1640cc0d…, index ad60345d… (chat92). It never starts the server.
Then Republish (Vraj only). Rollback: copy each `*.TIMESTAMP.bak-chat93` back over its file, delete c93.css, republish.
