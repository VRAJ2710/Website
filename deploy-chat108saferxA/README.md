# deploy-chat108saferxA (27 Nov 2026): v3 home preview, batch A

Preview only. Changes nothing unless the request is `GET /?preview=v3` (or carries the `td_v3p=1` cookie that sets) AND
chat105v3home2 has already built the v3 preview. `/`, `/?preview=off` and every other route are byte-identical (tested).
Apply AFTER deploy-chat102r6p, deploy-chat106softgate and deploy-chat107credits. One block is appended after the
chat107credits block; no existing byte of server.js changes; app.js and index.html are not touched. Nothing is published.

What the preview shows (structure and motion from SaferX; desk density from Barebone, which stays the main benchmark):
1. Full-screen hero: the page's existing kicker, dek and byline, the H1 set on two lines ("Know what matters." /
   "Before gold moves.", line 2 in a gold gradient), two buttons (#v3home, #v8-band), and an arc of 7 tool links to real
   routes from the menu: /brief/ /playbook/ /gold/ /lab/ /signals/ /markets/ /news/ (all 200 on dev, 27 Nov).
7. One signup: the existing free-brief form (`POST /free-brief`, id c96su-home, from=home, honeypot) is moved unchanged into
   a closing band; the duplicate v3 signup card is removed. If the form is not found, nothing is removed.
8. Slim header: one row; at >=1280 px five links (Brief, Gold, Terminal, Markets, Research), the "All sections" menu
   button and Sign in; below 1280 px a copy of the header's own sign-in link plus Menu (the copy is hidden under 360 px; Sign
   in stays at the top of the menu sheet). Both full-screen menus keep all 48 links (tested). Theme control kept (icon at <=480 px).
   Swipeable scroll-snap desk tabs (Today + 13 real routes) stick under the header.
6. Motion: gold reading-progress bar, hero fade-in, card hover lift. All off under prefers-reduced-motion. (The site
   stylesheet turns animation/transition off globally with !important, so the preview opts back in with !important.)
+  Tighter v3 cards (sans headlines, smaller padding/gaps); every v3 card, figure, source line, lag label and section stays.

Guards: server.js 2,449,079 B (post-softgate 2,429,645 + credits 19,434), ends byte-exact with the chat107credits block
(sha256 10ff789f...), chat105v3home2 block present once, one softgate attach, one VERIFY_ENFORCE = false, one r6p attach,
no r6o attach, one credits TAG, no chat108saferxA. app.js 8726da25f103e569c25f13ea1b155d66, index.html
23e26d5287a773dadaf3fd2c40deb389. The post-credits md5 was never captured: --measure prints it; C108_SERVER_MD5=<md5> pins it.
Modes: --measure (read-only), --dry-run (scratch build), no flag = apply with timestamped .bak-chat108saferxA backups.
A second run refuses ("already applied") and changes nothing. After applying, restart ONLY the "Start application" workflow
and expect exactly one "[chat108saferxA] preview attached" log line. Undo: copy the .bak back and restart.

No DB, DDL, payments, email, secret, config or network use. Two static assets: /__v3p/a8.css, /__v3p/a8.js (no-store, noindex).
Tests: test/run_deploy_tests.sh (19 checks on a synthetic post-credits server with the real chain tail).
