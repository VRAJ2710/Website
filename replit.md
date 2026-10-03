# Running The Dispatch Markets

This project runs as a same-origin Node preview server:

```sh
node server.js
```

The original Cloudflare Worker was not included in the import. `server.js` replaces its preview-facing routes: a small core US-equity/FX tape uses Twelve Data through a server-side 15-minute shared cache sized for the free plan, while Yahoo Finance supplies explicitly delayed broader-market quotes. CoinGecko is proxied and cached server-side, and the local session flow makes account/member gating testable. Stripe-managed Premium billing is configured in test mode. xAI-powered Premium research is integrated, subject to available provider credits.

## Ask / Expert (`POST /api/chat`)

A signed-in Premium member (or an account already marked `isAdmin`) receives `{ "reply": "<model text>", "meta": { "provider": "xAI", "model": "<model id>" } }` with HTTP 200 when a provider can answer.

Replit Secret the deployment must have:

- `XAI_API_KEY` — xAI API key from the xAI console. The server calls `POST https://api.x.ai/v1/chat/completions`. Do not commit the key.

Optional:

- `XAI_MODEL` — defaults to `grok-4`
- `XAI_BASE_URL` — defaults to `https://api.x.ai/v1` and must be `https`

If `XAI_API_KEY` is unset, the server tries the Replit xAI connector. If that connector cannot complete a chat, the route returns HTTP 503 `{ "error": "...", "code": "AI_KEY_MISSING" }` and names `XAI_API_KEY`. It does not throw. A key that xAI rejects is also HTTP 503 (`PROVIDER_AUTH`), not a process crash.

Logged-out `GET /api/me` is always HTTP 200 `{ "guest": true, "tier": "free", "billingPortal": false, "isAdmin": false }` with no `id`, including when the session cookie is stale or the session lookup throws.