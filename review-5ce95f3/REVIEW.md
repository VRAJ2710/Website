# Review: dev fef1da0 -> 5ce95f3 (Replit Agent commits a54c1c3 18:40, 5ba9f35 18:50, 5ce95f3 18:56 UK time, 15 Nov 2026)

Source: `.review-tmp/d.patch` (60,346 B, md5 a752e7a6f8962a2e2046113cb82f7442), read only. Files in the diff: app.js, scripts/compare-redesign-tests.py (new), server.js, test/presentation-redesign.test.js.
Dev md5s now: server.js 5b2b6d8061d876f0093cbe7caa4629af (2,415,111 B), app.js 8726da25f103e569c25f13ea1b155d66 (2,655,365 B), index.html 23e26d5287a773dadaf3fd2c40deb389 (unchanged).

## Flags (checklist)

| Area | Touched? | Notes |
|---|---|---|
| Stripe / checkout | No | No Stripe or checkout lines in the diff. |
| DB ALTER / DROP | No | No DDL. (The email_verified ALTER from 11 Nov is untouched and still there.) |
| Emails (Resend) / alerts | No in app code. **Caution** in the new script | `scripts/compare-redesign-tests.py` copies the whole `os.environ` (only DATABASE_URL / APPLICATION_DATABASE_URL are blanked) and runs `test/recovery-sender.test.js` and `test/auth.integration.test.js`. If those tests can send through Resend when a real key is in the environment, running the script on Replit could send real mail. Not run by the app; only if someone runs it by hand. Not verified either way (test files not in the diff). |
| Secrets / config | No | No .replit, env or secrets edits in this diff. |
| Removed menu links or sections | No | The only removed lines (4) are the CoinGecko direct-fetch fallback in app.js. |
| v3 preview block | Yes, additive | chat105v3home2 block is now committed in server.js, byte-identical to our copy (sha256 1da4d654..., 52,863 B), inserted just before the `// chat102r6c last-write scrub.` marker. It guards against double-run with chat105v3home. |
| chat105v3home / chat105v3home2 code | Only the above | No change to the old chat105v3home code; prefix bytes are unchanged (size check: 2,332,205 + 52,863 + 30,043 = 2,415,111 = dev). |
| Email-verify gate code (softgate anchors) | No | Lives in the prefix, which is unchanged, so all softgate anchors E0-E7 still apply. |
| /api/c102/terminal, c102YahooQuote | No | Not in the diff. |
| **r6o scrub block (r6p's target)** | **Yes** | `rewriteHtml` now strips every `<script>` from `/__auth/...` pages (5 lines) so auth pages keep CSP `script-src 'none'`. This made the old r6p refuse (scrub sha changed), and replacing the block with the old r6p block would have dropped the fix. The re-pinned r6p block carries the same 5 lines. |

Other changes:
- app.js ~line 19334: the CoinGecko stale-data wrapper no longer falls back to a direct browser fetch of api.coingecko.com; it always returns the same-origin proxy response. Reasonable (keeps CSP/same-origin); stale crypto data shows stale rather than refreshing from CoinGecko directly.
- test/presentation-redesign.test.js: 2 new tests (auth script strip; CoinGecko same-origin wrapper).
- scripts/compare-redesign-tests.py: dev tooling. `git archive 885a733` into a temp dir and runs test suites on both trees; read-only to git. See the email caution above.

Softgate interaction: the auth-page strip does not hurt softgate. The checkout/account reminder is a plain HTML form (no script); the SPA toast script is injected by withAssetVersion into app pages, not `/__auth/...` pages.

## Not covered by this diff
a54c1c3 reportedly also touched styles.css, .replit, data-cache files and a backup file; those are outside `d.patch` and were not reviewed. index.html md5 is unchanged; styles.css and .replit were not checked.
