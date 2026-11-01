# deploy-chat95: all eight macro tiles, no raw market codes, preview links on trust pages

Built and tested only. **NOT published.** Apply only when Vraj says so.

Base (live chat94): server.js 7a7a2df1fc685ba83dbca07e70a09567, app.js 8a195ba9f9cf3ade9e10ed3a70091806,
index.html b69f3596e29020ca80620246bae23f1b, c93.css 9d6a86a64135b1cc58e6af7b12973550 (c93.css is not changed by chat95).

Result: server.js 4d826690a8d93016cca4833c5751dcf9, app.js 970cf9ecebf0cfa5d8750937bdb0b537, index.html 278960434e869d5f2801c5a5512bf4ad.

## Why the desk showed 7 tiles
- The macro grid dropped any tile without a figure ("no figure, no tile"), so the grid briefly had 7 cells and a grey gap.
- The US real yield came last: the browser waited for idle time before asking, the server held the FRED figure in memory only
  (cold after every restart, 8 s deadline), and a failed fetch was not retried for 15 minutes.
- Labels such as "Gold futures (GC=F)" were hard-coded market codes.
- Inside the admin guest preview, About and Methodology are served by the trust-page path, which did not add ?view=guest to its links.

## What it changes
1. **Eight tiles from the first paint.** A tile with no fresh figure shows its last known value with "Last known, saved <time> UK"
   (kept in the browser for up to 7 days), else a labelled "Loading latest..." placeholder. It is never an empty grey cell.
   The real yield is requested immediately, restored from its last official print (with its date), and retried once after 20 s.
   The server warms it 3 s after boot and retries a failure after 2 minutes, not 15.
2. **No raw codes in reader-facing text.** GC=F, SI=F, CL=F, DX-Y.NYB, ^TNX, EURUSD=X, BTC-USD and similar are now plain names,
   e.g. "Gold futures (COMEX, front month)", "US Dollar Index (ICE)". The as-of line names the source ("Yahoo Finance, delayed").
   A small page-side pass catches any remaining code in visible text. JSON "source" fields are unchanged.
3. **Guest preview.** About, Methodology and the other trust pages keep ?view=guest on their links inside an admin preview.
4. **Rate limiter review.** The limit (30 requests per minute per address) is unchanged. The desk and crypto quote routes now answer
   identical requests from a 15 s cache, which is not counted against the limit. When the limit is hit and we hold a good answer
   from the last 30 minutes, that answer is returned marked served:"last-good" instead of a 429.
5. The app.js cache token is now chat95.

It does not run the server, npm, git, .replit, package.json, env, Stripe or the DB schema (no DDL). Line 1 stays `const BB10I_MAINTENANCE_ON = true;`.

## Apply (Replit Shell, project folder), only on Vraj's word
```
bash deploy-chat95/deploy.sh --dry-run
bash deploy-chat95/deploy.sh
```
Without a checkout: `curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat95-fixes/deploy-chat95/deploy.sh -o /tmp/d95.sh && bash /tmp/d95.sh --dry-run`
(it downloads the four pinned patch files by sha256).

The script checks the chat94 md5s and the c93.css md5, refuses a second run, pins every patch file by sha256, builds in scratch,
runs node --check, checks the md5/sha256 against the tested build, makes timestamped `.bak-chat95` backups, then installs. It never starts the server.

Rollback: copy each `*.bak-chat95` back over its file and do not republish.
