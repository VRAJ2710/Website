# deploy-chat94: fixes from the chat93 admin QA pass

Built and tested only. **NOT published.** Apply only when Vraj says so.

Base (live chat93, published e9388b69): server.js 60116e5449f03befbeef1c8e3511ef57, app.js 3b19083ada923e33b767c0ae476f068f,
index.html 1411a118530e30f20b53e77761fe50bf, c93.css 9d6a86a64135b1cc58e6af7b12973550 (c93.css is not changed by chat94).

Result: server.js 7a7a2df1fc685ba83dbca07e70a09567, app.js 8a195ba9f9cf3ade9e10ed3a70091806, index.html b69f3596e29020ca80620246bae23f1b.

## What it changes
1. **Admin-only guest preview.** Add `?view=guest` to any guest page (`/?view=guest`, `/markets/?view=guest`, `/research/?view=guest`, `/MSFT?view=guest` …).
   This works for an administrator session only. The page shows a "Guest preview" banner with an Exit link, its internal links keep `?view=guest`, and it is sent `private, no-store` with noindex.
   Guests and non-admin members: the parameter is ignored (maintenance 503 or the normal page). The admin Console and the admin menus get a "Guest preview" link.
2. **About** now carries "We are funded by reader subscriptions. We do not take payment to cover companies or assets." Editorial standards already had the full sentence.
3. **Short company paths.** `/MSFT` renders the monitor page ("Ranked N of 19"; canonical stays `/research/capital-sustainability/MSFT`).
   `/msft`, `/Msft` and `/MSFT/` 301 to `/MSFT`. This covers only the 19 monitor tickers, and 301s keep the query string. The route was never built in chat93, which is why /MSFT returned 404.
4. **No "V" avatar.** The Research hub and SPX 2026 author blocks lose the placeholder. The About overlay hides the photo slot, so there is no "VP" monogram until a photo is supplied.
5. **Other changes:**
   - A monitor page rendered for a signed-in reader is sent `private, max-age=60` instead of a public cache.
   - The maintenance page carries "Not investment advice. Capital at risk."
   - The app.js cache token is now `chat94`.

It does not run the server, npm, git, .replit, package.json, env, Stripe or the DB schema (no DDL). Line 1 stays `const BB10I_MAINTENANCE_ON = true;`.

## Apply (Replit Shell, project folder), only on Vraj's word
```
bash deploy-chat94/deploy.sh --dry-run
bash deploy-chat94/deploy.sh
```
Without a checkout, use: `curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat94-fixes/deploy-chat94/deploy.sh -o /tmp/d94.sh && bash /tmp/d94.sh --dry-run`.

What the script does:
- Checks the chat93 md5s and the c93.css md5.
- Refuses a second run.
- Pins the patch file by sha256.
- Builds in scratch, then runs node --check and checks the md5/sha256 against the tested build.
- Makes timestamped `.bak-chat94` backups, then installs.
- Never starts the server.

Rollback: copy each `*.bak-chat94` back over its file and do not republish.
