# Prod snapshot — thedispatch.uk build chat56 (served assets)

- Source: https://thedispatch.uk (Replit Autoscale), fetched read-only with curl (no auth, no cookies).
- Fetch 1: Sun 18 Oct 2026 22:51:38–22:51:51 BST (Europe/London). Fetch 2: 22:52:11–22:52:26 BST. index.html also fetched at 22:50:59 BST.
- Result: all 32 files identical across both fetches (no nonces/timestamps in the served HTML). The HTML has build markers `app.js?v=chat56`, `styles.css?v=chat1`, `logo-mark.svg?v=fd7364ffa1e17f1c` / `?v=1786750501`.
- app.js md5 = b9d3d0a3fc9cbd3e094ec28245f3285e (matches the expected chat56 hash). `/app.js` and `/app.js?v=chat56` serve the same bytes.
- Route pages (from sitemap.xml) are stored as `<route>/index.html`. `/pricing` is stored as `pricing/index.html`.
- Not stored: `/index.html` (308 to `/`), `/favicon.ico` (301 to `/logo-mark.svg`), `/settings/` (302 to auth). `/sw.js`, `/apple-touch-icon.png` and `/.well-known/security.txt` all return 404.
- Third-party scripts referenced but not mirrored: unpkg lightweight-charts@4.2.0, i.replit.com/script.js, Google Fonts.
- server.js is not public and is not included.

Verify with: `cd prod-snapshot && md5sum -c MANIFEST.md5`
See SOURCES.txt for the file-to-URL map and the HTTP status of each fetch.
