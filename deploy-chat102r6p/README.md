# deploy-chat102r6p (re-pinned on dev 5ce95f3, 16 Nov 2026)

Fix Terminal `/api/c102/terminal` previous close for DX-Y.NYB, ^VIX and ^TNX. `c102YahooQuote` used
`meta.previousClose || meta.chartPreviousClose` on a `range=5d&interval=1d` Yahoo chart, where Yahoo omits `previousClose` and
sets `chartPreviousClose` to the first daily close in the window. The `c102r6pSessionPrev` helper takes the last non-null daily bar
whose session date is before the current session. `chartPreviousClose` is never used for that. The r6p logic is unchanged from bd275cb1.

Re-pin: on 15 Nov the Replit Agent commits a54c1c3/5ba9f35/5ce95f3 (a) committed the chat105v3home2 block byte-identical, and
(b) added 5 lines to `rewriteHtml` inside the r6o last-write scrub: auth pages (`/__auth/...`) get all `<script>` tags stripped,
so the install-bar/label scripts don't fight the auth CSP `script-src 'none'`. That change sits inside the block r6p replaces, so
both payload blocks here carry the same 5 lines (old r6o block: 30,043 B, sha256 97cf896d...; new r6p block: 33,579 B, sha256
3f02d689...). Without this, r6p would have dropped that fix.

Guards: server.js md5 `5b2b6d8061d876f0093cbe7caa4629af` (2,415,111 B), app.js `8726da25f103e569c25f13ea1b155d66`, index.html
`23e26d5287a773dadaf3fd2c40deb389`; the scrub (marker to EOF) must be 30,043 B with sha256 97cf896d...; bytes before it must be
unchanged after install. Expected post-install size 2,418,647 B (md5 is printed by --dry-run; it cannot be computed off-box).

Modes: `--measure` (read-only report, no download), `--dry-run` (scratch build only), no flag = apply with timestamped
`.bak-chat102r6p` backups. Does not start the server, npm, git, or republish. No new secrets, tables, timers or paid feeds.
Expect exactly one `[c102r6p] scrub attached` line after restarting "Start application".
