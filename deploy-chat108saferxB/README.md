# deploy-chat108saferxB (27 Nov 2026): v3 home preview, batch B

Preview only. Changes nothing unless the request is `GET /?preview=v3` (or carries the `td_v3p=1` cookie) AND chat108saferxA
has already built the batch-A preview (html class v8a). `/`, `/?preview=off`, POST / and every other route are byte-identical
(tested). Apply AFTER deploy-chat108saferxA. One block is appended after the A block; no existing byte of server.js changes;
app.js and index.html are not touched. Nothing is published.

Layout after the hero and desk tabs (all existing Barebone-style v3 cards, regrouped, none replaced or deleted):
2. Today's story: >=1000 px a sticky left column with the gold futures chart (436 px, sits 12 px under the tabs) while the
   right column scrolls the market snapshot (headline, summary, "updated X min ago", also-in-brief list), upcoming events
   and "Five things that moved". Phones stack: snapshot, chart, events, moved (also the reading order).
4. Prices and mood: key prices (now with Bitcoin and WTI tiles, copied as text from the market-context table rows with their
   own source, time and lag label) beside the market mood gauges; market colour key. Then Charts (one month), then a 1-2-3
   "How to use the desk" (Brief, Prices and mood, Terminal/Calendar). The old "Market context" table is kept, collapsed
   under a "Full table" disclosure (all 12 rows, sources and times; nothing deleted).
3. Market colours and icons: Gold, Dollar, Yields, Oil, Crypto, Equities on price tiles, chart tiles, moved rows and the key.
   Text contrast vs page: dark 8.5-11.0:1, light 4.8-6.5:1 (AA both themes).
5. Big type only in the hero; section heads are small kickers; cards stay dense. Hero headline now centred (fix).

Guards: server.js 2,477,261 B, md5 dbe6c78c4fcf9f7af94eabac0f56c139 (dev after A, 27 Nov), ends byte-exact with the
chat108saferxA block (sha256 482affe6...), A block and A TAG once, softgate/VERIFY_ENFORCE/r6p/credits/v3home2 once, no r6o,
no chat108saferxB. app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389.
Modes: --measure (read-only), --dry-run (scratch build), no flag = apply with timestamped .bak-chat108saferxB backups.
A second run refuses ("already applied"). After applying, restart ONLY the "Start application" workflow and expect exactly
one "[chat108saferxB] preview attached" line (after the A line). Undo: copy server.js.<ts>.bak-chat108saferxB back, restart.

No DB, DDL, payments, email, secret, config, storage or network use. Two static assets: /__v3p/b9.css, /__v3p/b9.js.
If the v3 grid is not exactly the seven known cards, the block leaves the page as A built it.
Tests: test/run_deploy_tests.sh (25 checks on a synthetic post-A server with the real chain, plus the transform run on the
real dev A output).
