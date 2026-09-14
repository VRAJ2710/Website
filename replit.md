# Running The Dispatch Markets

This project runs as a same-origin Node preview server:

```sh
node server.js
```

The original Cloudflare Worker was not included in the import. `server.js` replaces its preview-facing routes: a small core US-equity/FX tape uses Twelve Data through a server-side 15-minute shared cache sized for the free plan, while Yahoo Finance supplies explicitly delayed broader-market quotes. CoinGecko is proxied and cached server-side, and the local session flow makes account/member gating testable. Stripe-managed Premium billing is configured in test mode. xAI-powered Premium research is integrated, subject to available provider credits.

Production (autoscale) must set `DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk`. Session cookies use `Secure` and `Domain=thedispatch.uk` on that host. `www.thedispatch.uk` is 308-redirected to the apex. Stripe webhook path is `/api/stripe/webhook` (not `/api/stripe-webhook` in the Dashboard; the alias is accepted as a fallback).