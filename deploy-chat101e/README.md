# deploy-chat101e

On top of the LIVE chat101d build (server 7a959bc6, app 5773e359, index 90055663; c93.css 9d6a86a6).

- **app.js**: the signed-in Gold Dashboard gets a "Market context" section with the same market cards as the public pages:
  Gold and silver, Currencies, Rates, Energy, Crypto. It reuses the public pages' chat96 renderer (copied out of server.js at
  patch time) and the same quotes APIs (`/api/desk-quotes`, `/api/c96/gold-spot`, `/api/real-yield`, `/api/c97/dgs10`,
  `/api/eia-spot`, `/api/crypto-snapshot`, `/api/c100b/gold-change`). Every card: plain name, level, change, source, as-of (UK),
  "Delayed" where delayed, and its own venue's session label (New York hours, same rules as the server's c93SesClass).
  Cards below 600px wide, a normal table on desktop. If the quotes fail it shows a plain note; refreshes every 5 minutes.
- **app.js support email**: app.js contains no support/contact address (checked: no `@` address and no `mailto:`), so nothing to change.
  The server-side contact address is already vraj2710@hotmail.com since chat101d.
- **index.html**: cache tag `app.js?v=chat101e`.
- **server.js**: read only (unchanged; line 1 stays maintenance=false).

Run on Replit: `bash deploy.sh --dry-run` then `bash deploy.sh`. It does not start the server or publish.
