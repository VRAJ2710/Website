# Running The Dispatch Markets

This project runs as a same-origin Node preview server:

```sh
node server.js
```

The original Cloudflare Worker was not included in the import. `server.js` replaces its preview-facing routes: a small core US-equity/FX tape uses Twelve Data through a server-side 15-minute shared cache sized for the free plan, while Yahoo Finance supplies explicitly delayed broader-market quotes. CoinGecko is proxied and cached server-side, and the local session flow makes account/member gating testable. Stripe-managed Premium billing is configured in test mode. xAI-powered Premium research is integrated, subject to available provider credits.

## Feed secrets (soft-fail)

Do not commit key values. Missing keys must leave a labelled degraded feed, not a stuck "AWAITING FEED".

| Env | Required for | When missing |
| --- | --- | --- |
| `TWELVE_DATA_API_KEY` | `/api/twelve-data-quote` core tape | `{configured:false,quotes:{}}` and a server warning. Yahoo still fills the tape. |
| `FINNHUB_API_KEY` | Finnhub news/quotes | Quote falls back to Yahoo. News returns `[]` with `X-Dispatch-Data-Status: degraded`. RSS (`/api/rss-feed?feed=f0`…`f25`) is the news source. |
| `DATABASE_URL` | Accounts, sessions, Stripe sync | Process refuses to boot. Market quote routes do not read this key. |
| Replit xAI connector | Premium AI routes | Those routes return a provider error. Quotes and RSS do not use it. |

Gold and the synthetic dollar index use keyless reference feeds (`api.gold-api.com`, Frankfurter ECB rates) via `/api/market-reference-quotes`.

## Republish on Replit Autoscale

Live `thedispatch.uk` is Replit Autoscale, not GitHub Pages. The running bundle is ahead of `main`. Do not replace the Repl's `app.js` or `server.js` with an older checkout.

1. Pull this branch into the Repl (or copy `rssFetch.js`, `feedStatus.js`, `scripts/apply_feed_bootstrap_replit.py`, and the `server.js` feed changes).
2. From the Repl root run `python3 scripts/apply_feed_bootstrap_replit.py`. It patches the live files in place and cache-busts to `pricefix8`.
3. Republish the Autoscale deployment. Confirm `app.js?v=pricefix8`, then run `BASE_URL=https://thedispatch.uk node scripts/smoke-feed-bootstrap.mjs`.
4. Do not spend Replit AI credits on this apply. The script is the free path.

The pricefix8 apply follows HTTPS redirects for RSS (MarketWatch, Guardian Business, and CoinDesk otherwise return an empty 200), maps `LUMBER` to `LBR=F` with a `WOOD` fallback, and lets `DXY` print from Yahoo `DX-Y.NYB`.