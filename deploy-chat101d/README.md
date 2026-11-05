# deploy-chat101d

Base: LIVE chat101c (server 29466d26, app 999036af, index 4049a9ac, c93.css 9d6a86a6).

Only change: the public support/contact email becomes vraj2710@hotmail.com (Vraj's request, 5 Nov 2026), and the cache tag moves to app.js?v=chat101d.

- server.js: `C93_CONTACT` constant (footer, About, Contact, Editorial standards, Corrections, Pricing, desk footer) and the hard-coded Terms "Questions:" and Privacy "Contact:" mailto links.
- index.html: `/app.js?v=chat101c` -> `/app.js?v=chat101d`.
- app.js, c93.css, photo: unchanged.
- Left alone: outbound data-feed User-Agent strings (SEC/official sources; never shown to readers) and the recovery-email From (env var).

Run in the Replit Shell: `bash deploy.sh --dry-run`, then `bash deploy.sh`. Never start the server; Republish only.


## Update: live-bug fixes folded in (same release)
- Phones (<=599px): tables other than the market-context cards scroll inside their own box (/research/capital-sustainability, /tools/isa-sipp/, /tools/scenario/ and any other c93 table).
- App views (/dashboard/ etc.): no sideways page scroll at <=600px.
- /watchlist "Daily check" button: solid white on navy (11.5:1) in light and dark.
- JSON-LD publisher URL lower-cased to linkedin.com/in/vraj2710; name stays "Vraj Patel".
- app.js now changes (one appended style block).
