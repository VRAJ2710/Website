# pricefix12 — login cookie + desk sync (Replit apply)

Production is the Replit Autoscale app. Do not replace live `app.js` or `index.html` with the GitHub checkout. Run this script in the Replit shell from the directory that contains `server.js` and `app.js`.

```sh
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/cursor/fix-session-cookie-kickout-4f8b/scripts/apply_pricefix12.py -o apply_pricefix12.py
python3 apply_pricefix12.py
```

The script is idempotent. It writes `*.bak-pricefix12` before changing a file and runs `node --check`. If the check fails, those backups are restored.

Then republish the Autoscale deployment (`node server.js`).

## What it changes

- `billingOrigin.js`: on set and clear, emit a host-only `Max-Age=0` cookie and a `Domain=thedispatch.uk` `Max-Age=0` cookie, then set one `Domain=thedispatch.uk` session cookie on apex, www, and `the-dispatch.replit.app`. `the-dispatch.replit.app` 308s to `https://thedispatch.uk` the same way www does. Preview hosts are left alone.
- `server.js`: `/api/me` tries each `dispatch_session` in the Cookie header until one matches a live row. Logout and login delete every presented token, not only the first.
- `app.js` (only if it still has the pricefix11 `isPrimaryLiveQuote` gates): desk spine, compare, geo energy, search, dynamic lookup, dashboard `primaryLiveCount`, latency strip, and book counts use `hasSyncedQuote`, so a delayed, stale, cached, or proxy Yahoo print is shown with its existing provenance badge. The truly-live predicate and the watchlist live dot stay as they are.
- `index.html`: `pricefix11` becomes `pricefix12` (`TD-pricefix12` and `/app.js?v=pricefix12`).

`pricefix11` `app.js` does not contain the strings `Authentication Error` or `Failed to get user data after login.` That modal is what the client shows when the follow-up user fetch has no id. The script still adds `credentials: "include"` to any bare `fetch("/api/me")` in a file that contains that text. The dual-cookie clear is what makes `/api/me` return `id`.

## Verify

1. Sign in at `https://thedispatch.uk/__auth/login`.
2. DevTools → Application → Cookies for `https://thedispatch.uk`: one `dispatch_session`, Domain `thedispatch.uk`.
3. `/api/me` includes `id`. The account control shows Sign out. The authentication modal does not appear.
4. Desk spine shows prices for Oil, Nat Gas, Copper, S&P, Nasdaq, Russell, DXY, EURUSD, and Bitcoin when `/api/yahoo-quote` has a print. Badges may still say DELAYED or STALE. They should not say NO LIVE SYNC for those prints.
5. View source: `app.js?v=pricefix12`.
