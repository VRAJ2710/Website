# Ask/Expert chat and logged-out /api/me

Production is the Replit Autoscale app behind https://thedispatch.uk. Merging this PR does not by itself restart that process. Apply the patch in the Replit shell, set the secret, then republish.

Do not reset the Replit project to this Git branch. The live tree has later desk and billing edits that are not in GitHub `main`. Run the patcher against the files already on Replit.

## Secret

In Replit Secrets, set:

- `XAI_API_KEY` — xAI API key from the xAI console. This is the variable Ask/Expert uses for `POST https://api.x.ai/v1/chat/completions`.

Optional: `XAI_MODEL` (default `grok-4`), `XAI_BASE_URL` (default `https://api.x.ai/v1`, https only).

Do not paste the key into git.

## Apply

From a checkout of this branch (a scratch directory is fine; not a reset of the live app):

```sh
python3 scripts/apply_chat_me_fix.py --root /path/to/live/app
```

Or from the Replit shell, after copying `aiProvider.js` and this script next to the live app:

```sh
python3 apply_chat_me_fix.py --root . --ai-provider ./aiProvider.js
node --check server.js
node --check aiProvider.js
```

The script is idempotent. It writes `server.js.bak-chat-me` and, if present, `aiProvider.js.bak-chat-me`, then runs `node --check`. A failed check restores those backups. It does not edit Stripe checkout.

Restart with `node server.js` and republish the Autoscale deployment.

## What success looks like

`POST /api/chat` for a Premium (or existing admin) session:

- With `XAI_API_KEY` set and accepted by xAI: HTTP 200 and JSON `{ "reply": "<model text>", "meta": { "provider": "xAI", "model": "grok-4" } }`. The Ask/Expert panel shows that reply.
- With the secret missing and the Replit xAI connector also unable to answer: HTTP 503 `{ "code": "AI_KEY_MISSING" }` and an error that names `XAI_API_KEY`. The process stays up.
- With a key xAI rejects: HTTP 503 `{ "code": "PROVIDER_AUTH" }`. No stack trace is returned to the browser.

Logged-out `GET /api/me` (no cookie, cleared cookie, stale `dispatch_session`, or a session lookup error): HTTP 200

```json
{ "guest": true, "tier": "free", "billingPortal": false, "isAdmin": false }
```

The JSON has no `id`.

## Checks

1. Sign out. DevTools shows `GET /api/me` 200 and the guest JSON above. The account control shows Sign in, not the previous member.
2. Sign in as Premium or the existing admin. Open Ask/Expert and send a short market question.
3. Network: `POST /api/chat` is 200 and `reply` is non-empty. The panel shows that text, not “AI is temporarily unavailable. No answer was published.”
4. Temporarily rename `XAI_API_KEY` in Secrets and restart. The same send returns HTTP 503 with `code` `AI_KEY_MISSING`. Put the secret back and restart.
