# deploy-chat96

chat96 on top of the live chat94 files. It includes all of chat95, which never shipped on its own.
Part of one combined release, together with chat97, chat98 and chat99. **Do not publish this on its own.**

**What it changes:** `server.js`, `app.js` and `index.html` (cache token `v=chat96`). `c93.css` stays unchanged.
**What it doesn't touch:** Stripe, npm, `package.json`, `.replit`, env, git or the DB schema. There is no DDL.
Line 1 of server.js stays `const BB10I_MAINTENANCE_ON = true;`.

**How it works:** `bash deploy.sh --dry-run`, then `bash deploy.sh`. The script:
- checks the live chat94 md5s and aborts on any other base;
- refuses a second run;
- builds in a scratch folder and checks the result against the tested md5 and sha256;
- writes `.bak-chat96` backups before it changes anything;
- never starts the server.

**Files:**
- `patch_chat96.py`: the patch script.
- `plain.js`: plain market names.
- `app_block.js`: client code, including the Settings → Your AI keys UI.
- `server_block.js`: server code, including BYOK.
- `live96.js`: the public-page live-figures script.

**BYOK** needs a Replit Secret named `DISPATCH_BYOK_MASTER_KEY`: 32 random bytes, base64 encoded (`openssl rand -base64 32`).
Without it, Settings shows "Your AI keys are not available yet" and the API refuses. Keys are stored AES-256-GCM encrypted in the existing table
`dispatch_openbb_research_cache` under `byok:<userId>:<provider>`.
If the secret is changed later, the saved keys can no longer be read, and users will need to add them again.
