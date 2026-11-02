# deploy-chat100e

Small change on top of the **live chat100d build** (publish 0089d1b9). Only server.js, app.js and index.html change;
c93.css and assets/founder.webp are untouched. Line 1 of server.js stays the maintenance=false line.

Base (live chat100d) md5s: server.js `15ecc24180575004f6b9674445722d79`, app.js `0e4bb0e3d7749dbeecff35a3c1f20df3`,
index.html `b0961c778217e08ba9a29178f62aa223`, c93.css `9d6a86a64135b1cc58e6af7b12973550`.
Result md5s: server.js `96020a62380b5fe7dfc85d27564fbf3c`, app.js `25e22204c78e72e60b4fb4be67225137`,
index.html `3ac8a07c186f1da17d2bfcc23b232e62` (cache tag `app.js?v=chat100e`), c93.css unchanged.
founder.webp sha256 `fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f` (unchanged, checked only).

## What changes (patch_c100e.py, exact-count edits, nothing else)
1. Byline "Edited by Vraj Patel, London" becomes "Edited by Vraj Patel" everywhere it appeared:
   - server.js `C93_EDITOR` (guest About card, /about and /editorial-standards bylines, article/brief/research page bylines
     via c96Byline, and the home page meta description); the contact block line; a code comment;
   - app.js: the app About sheet byline, the footer brand line, a code comment;
   - index.html: the legacy About byline.
   JSON-LD and the author meta tags only ever named "Vraj Patel" (no London), so they needed no change.
2. Bio (guest About and app About) is exactly: "Vraj Patel founded The Dispatch Market to give independent investors a
   careful, sourced read on gold and macro."
3. Guards: the patch (and deploy.sh on the scratch build) fail if "Edited by Vraj Patel, London" or
   "edits every piece from London" remains (also the older draft wording and any company LinkedIn URL).

Left unchanged on purpose: the server-rendered footer "Published by Vraj Patel, London · © … The Dispatch Market".

## Deploy (Republish is done by others)
`bash deploy.sh --dry-run`, then `bash deploy.sh`. It checks the live chat100d md5s and the photo, refuses a second run,
builds in scratch, runs `node --check`, the DDL grep, the line-1 and wording guards, makes timestamped `.bak-chat100e`
backups, installs, and verifies. It does NOT start the server. Undo: restore each file from its `.<timestamp>.bak-chat100e` copy.
Tests: t_c100e.js (harness; t_c100c_unit.js and the other harness tests are unchanged, see deploy-chat100d).
