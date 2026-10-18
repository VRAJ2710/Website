# Content-Security-Policy-Report-Only (draft)

Not applied. Do not add this header to `server.js`, Replit, or Cloudflare as part of rt52ops. It is a starting policy for the live chat56 page, so a later change can watch violations before anything is enforced.

The origins below are what the browser actually loads from `https://thedispatch.uk/` and `app.js?v=chat56` (fetched 2026-10-18). RSS hosts, Twelve Data, Finnhub, and Yahoo chart calls go through `/api/*` on `thedispatch.uk`. Stripe Checkout is a full-page navigation to the URL returned by `/api/create-checkout` (Stripe-hosted Checkout, typically `https://checkout.stripe.com`). The page does not load `js.stripe.com`.

## Header

```
Content-Security-Policy-Report-Only: default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com https://i.replit.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data:; connect-src 'self' https://api.gold-api.com https://api.coingecko.com https://i.replit.com wss://ws-feed.exchange.coinbase.com wss://streamer.finance.yahoo.com wss://ws.kraken.com; frame-src https://www.tradingview.com; manifest-src 'self'; worker-src 'self' blob:; report-uri /api/csp-report
```

| Directive | Why it is there |
| --- | --- |
| `script-src 'self' 'unsafe-inline' https://unpkg.com https://i.replit.com` | `/app.js`, the inline boot script in `index.html`, `lightweight-charts@4.2.0` on unpkg, and `https://i.replit.com/script.js` |
| `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com` | `/styles.css`, inline `style` attributes the client sets, Google Fonts CSS |
| `font-src 'self' https://fonts.gstatic.com data:` | Font files referenced by the Google Fonts stylesheet |
| `img-src 'self' data:` | `/logo-mark.svg`, `/og-card.png`, `/founder.jpg`, the inline favicon SVG |
| `connect-src` | Same-origin `/api/*`, `https://api.gold-api.com`, CoinGecko when the client calls it directly, Replit analytics `POST https://i.replit.com/api/send`, and the three browser sockets: Coinbase, Yahoo Finance, Kraken |
| `frame-src https://www.tradingview.com` | The chart fallback iframe (`/widgetembed/`). Its own scripts stay inside the frame |
| `frame-ancestors 'none'` | Matches the live `X-Frame-Options: DENY` |
| `report-uri /api/csp-report` | Same-origin collector. This route does not exist yet |

`'unsafe-inline'` is required for the current boot script and for inline styles. A later enforcement pass can replace it with hashes. Until then, report-only will stay noisy if those tokens are omitted, which hides real violations.

`https://checkout.stripe.com` is intentionally not a script, frame, or connect source. Navigation to Checkout is not blocked by this policy. Add it to `form-action` only if a form starts posting there.

## Collecting reports

1. Leave the header as `Content-Security-Policy-Report-Only`. Do not send `Content-Security-Policy` until the report stream is quiet.
2. Add a `POST /api/csp-report` that accepts `application/csp-report` and `application/reports+json`, stores the JSON body, and returns 204. Do not reflect the body into HTML.
3. Browsers also print each violation in the devtools console while the policy is report-only. That is the quick check; the POST body is the record.
4. `report-uri` is the one the header above uses, because every browser that loads this site still sends it. The newer Reporting API is the same idea with two headers: `Reporting-Endpoints: csp-endpoint="https://thedispatch.uk/api/csp-report"` and `report-to csp-endpoint` on the policy. Use both when the collector exists.
5. Read a sample of reports before enforcing. Expect noise from extensions and from `'unsafe-inline'` if that token is removed too early. Group by `violated-directive` and `blocked-uri`.
