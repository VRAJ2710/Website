# deploy-reopen2

Live QA fixes on top of the live final build (publish fd2d2c71), plus maintenance OFF on line 1 of server.js.

- Base md5 (live): server ccd31a713886f6638787e0cd7408bb0b, app 8d085d79ad06baceed05aac8c18aa66b, index fb535741645653c1f4bb4dc9df4846c9, c93.css 9d6a86a64135b1cc58e6af7b12973550 (unchanged).
- `deploy.sh` fetches these files at a pinned commit, checks sha256, applies `patch_reopen.py` to scratch copies, checks the result md5/sha256 matches the tested build, makes `.bak-reopen2` backups, installs, and runs node --check. It refuses a second run. It never starts the server.
- Fixes: F1 admin preview on the same request; F2 "Use your own AI key: coming soon" while DISPATCH_BYOK_MASTER_KEY is unset; F3 signed-in home layout; F4 one free-brief form per page; F5 calm "Updating…" desk labels, no greyed panels; admin AI status without xAI; quoted thousands in Portfolio X-ray CSV.
- No DDL, no Stripe, no env, no npm.
