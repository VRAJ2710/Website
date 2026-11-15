# deploy-chat105v3home (PREVIEW ONLY)

v3 home page preview for thedispatch.uk, shown only on `/?preview=v3` (sets cookie `td_v3p=1`, 7 days; `/?preview=off` clears it).
Normal `/` without the switch is passed straight to the existing handler: byte-identical output and headers.

What it adds (one block inserted just before the `// chat102r6c last-write scrub.` marker; every other byte unchanged):
- `GET /` with the switch: the normal home HTML gets `class="v3p"` on `<html>`, a noindex meta, a link to `/__v3p/home.css`,
  the v3 section at the top of `<main>` (free-brief sign-up first, then snapshot, gauges, key prices, gold chart,
  events timeline, chart tiles, 5-bullet summary), and `/__v3p/home.js`. Every existing section, the header, the old
  full-screen menu and the footer stay in place. Response: `Cache-Control: private, no-store`, `X-Robots-Tag: noindex, nofollow`,
  corrected Content-Length.
- `/__v3p/home.css`, `/__v3p/home.js`: static assets (no-store, noindex).
- Data: browser fetches of existing same-origin free feeds only: /api/brief/edition, /api/c100/macro, /api/regime,
  /api/c97/calendar, /api/c97/today, /api/c102/chart, /api/yahoo-chart. No new endpoints, tables, timers or paid feeds.

No DB, auth, Stripe, AI-provider, email, secret or config change. Does not start the server or republish.

Guards (Replit dev workspace HEAD fef1da0): server.js 9c593e7ab7887a20ba876e938abca0fc, app.js d8ca8562df01bf88c68e4971752e602c,
index.html 23e26d5287a773dadaf3fd2c40deb389, prefix before the scrub marker sha256 8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae (2,332,205 bytes).
Expected new server.js size 2,411,277 bytes.

Run in the Replit Shell, in the project folder:
```
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/<INSTALLER_COMMIT>/deploy-chat105v3home/deploy.sh -o /tmp/d105.sh
echo "<SHA256>  /tmp/d105.sh" | sha256sum -c -
bash /tmp/d105.sh --measure
bash /tmp/d105.sh --dry-run
bash /tmp/d105.sh
```
Then restart only the "Start application" workflow and expect one `[chat105v3home] preview attached` log line.
Undo: `cp server.js.<TS>.bak-chat105v3home server.js` and restart the workflow.
