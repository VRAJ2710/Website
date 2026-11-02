# deploy-chat101

Feature batch on top of the **chat100e build** (deploy/jack-chat100e, 343ec43f). Only server.js, app.js and index.html
change; c93.css and assets/founder.webp are untouched (checked only). Line 1 of server.js stays the maintenance=false line.
Free data sources only. No Stripe, env, package or DB schema changes. No new tables, so **no dev_create.sql**.

Base (chat100e) md5s: server.js `96020a62380b5fe7dfc85d27564fbf3c`, app.js `25e22204c78e72e60b4fb4be67225137`,
index.html `3ac8a07c186f1da17d2bfcc23b232e62`, c93.css `9d6a86a64135b1cc58e6af7b12973550`.
Result md5s: server.js `889e520487059390526900c96afc2d2a`, app.js `562cf0ff82cbac0008df9c8f7f4d29f9`,
index.html `5fc0897f4ae06c50d2d04ba00d9f4934` (cache tag `app.js?v=chat101`, css stays `c93.css?v=chat93`).
founder.webp sha256 `fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f` (unchanged).

## What it adds
1. **/tools/verify/**: checks a typed claim against Bank of England, FRED and gov.uk figures. Verdict is Supported,
   Not supported or Can't verify, each with the source, a UK as-of time and plain-English reasoning. 30 checks per 10 min.
2. **/tools/isa-sipp/**: an illustrative ISA/SIPP gold planner, marked "illustrative, not advice". Allowances (ISA £20,000,
   LISA £4,000, pension annual allowance £60,000) are cited to gov.uk with the date checked, plus "check gov.uk".
3. **/central-banks/**: Fed and BoE statement tone, with a redline of what changed since the last statement.
4. **/tools/scenario/**: OLS gold scenario simulator (gold monthly % on real-yield change and dollar %). Shows the sample,
   n, R², the coefficients, the formula, and a ±1.96×residual-SE range.
5. **/research/filing-changes/**: 10-K/10-Q Risk Factors and MD&A change detector. Each filing is downloaded only once.
   It respects the site-wide 25 SEC downloads a day and 5 starts per signed-in reader a day, and uses DISPATCH_SEC_UA.
   Guests see a sign-in prompt; preview sees no form; cross-origin POSTs get a 403.
6. **PWA**: /manifest.webmanifest (shortcuts Gold, Brief, Dashboard), icons, /sw.js, /offline/ and an install prompt.
   The service worker is network-first. It never caches /api, /api/me, admin or auth, never calls cache.put, and has no push.
7. **Source inspector** on the signed-in SPA /gold/ and /brief/ (the "Check and plan" menu; Enter opens the source pane).
8. **", London" removed after Vraj's name**: the server footer "Published by Vraj Patel · ©" and the index.html eyebrow.
   Guard: the patch and deploy.sh fail if "Vraj Patel, London" (any case) appears anywhere. Market and time-zone London stays.
   App strings showing "GC=F" now read "front month".

## Deploy (Republish is done by others, only when Vraj says so)
`bash deploy.sh --dry-run`, then `bash deploy.sh`. It checks the chat100e md5s, c93.css and the photo, and refuses a second run.
It fetches the three sha256-pinned files, runs the DDL grep, builds in scratch, runs `node --check`, matches the tested
md5/sha256, and runs the line-1 and wording guards. Then it makes timestamped `.bak-chat101` backups, installs and verifies.
It does NOT start the server. Undo: restore each file from its `.<timestamp>.bak-chat101` copy.
Tests: t_c101.js (harness, 252 checks) plus all earlier suites.
