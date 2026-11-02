# deploy-chat101b

chat101 and the full section menu in one run, on top of the LIVE chat100e build
(server 96020a62380b5fe7dfc85d27564fbf3c, app 25e22204c78e72e60b4fb4be67225137, index 3ac8a07c186f1da17d2bfcc23b232e62).

Why: Vraj said core sections had gone from the header. Every section is back, in the site header and in the app, at desktop and phone size.

Run in the project folder (it does not start the server or publish anything):

    bash deploy.sh --dry-run
    bash deploy.sh

What deploy.sh does:
- checks the chat100e md5s, c93.css (chat93), line 1 (maintenance false) and the photo
- refuses to run again if the chat101b build or a `.bak-chat101b` backup is already there; stops if it finds the chat101-only build
- downloads the six patch files, pinned by sha256, from this commit, then greps them for DDL
- builds in a scratch folder (patch_c101.py, then patch_c101b.py), runs `node --check`, compares md5 and sha256 with the tested build, and checks the `app.js?v=chat101b` tag and the wording guards
- makes timestamped `.bak-chat101b` backups, then installs

Files:
- `patch_c101.py`, `server_block_c101.js` and `app_block_c101.js` are the chat101 files, byte for byte
- `patch_c101b.py`, `server_block_c101b.js` and `app_block_c101b.js` add the menu, the new routes and the C100_NM start-up guard
- `t_c101b.js` holds the harness tests, and `audit.js` the Puppeteer audit at 390 and 1280 px for guest, member and admin
- `t_c100_b.js` and `t_c100e.js` are harness tests with the cache-token regex widened to `chat10(0e|1|1b)`

There is no DDL, and nothing touches Stripe, env vars, package.json or .replit.
