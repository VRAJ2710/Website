# Live Replit billing patch

Use this when production is the Autoscale Node app (`node server.js`) and you need to pin checkout, cookies, and Stripe return URLs to apex `https://thedispatch.uk` without editing this GitHub tree's `server.js` / `app.js` by hand.

The patcher is idempotent. It no-ops if `canonicalPublicOrigin` is already present. It writes `server.js.bak-billing` and `app.js.bak-billing` before changing anything, then runs `node --check server.js`.

## Replit one-liner

In the Replit Shell, from the project root that contains `server.js` and `app.js`:

```sh
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/cursor/apply-live-billing-fix-fdb2/scripts/apply_live_billing_fix.py -o apply_live_billing_fix.py && python3 apply_live_billing_fix.py
```

If the repo is already cloned on the box:

```sh
python3 scripts/apply_live_billing_fix.py
```

## After the script succeeds

1. In Replit **production** Secrets / `userenv.production`, set:

   `DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk`

   Change this even if it is currently `https://www.thedispatch.uk`. A www origin splits `dispatch_session` from apex.

2. Redeploy the Autoscale deployment (`node server.js`).

3. Confirm Stripe Dashboard webhook is `https://thedispatch.uk/api/stripe/webhook` (not `/api/stripe-webhook`). Events: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`.

## What the script changes

- Inserts `canonicalPublicOrigin`, `sessionCookieHeader`, `clearSessionCookieHeader`, and `writeCanonicalHostRedirect` before `setSession`.
- Changes `setSession(res, ...)` to `setSession(req, res, ...)` and sets cookies with `Secure` + `Domain=thedispatch.uk` on production hosts.
- Pins `publicUrl()` to `canonicalPublicOrigin()` (www rewritten to apex).
- Registers the Stripe webhook on `canonicalPublicOrigin()`.
- 308-redirects `www.thedispatch.uk` to apex at the start of `handle()`.
- Clears the session cookie with `clearSessionCookieHeader` on logout.
- Stops `serveStatic` from serving `server.js`, `stripeClient.js`, `*.md`, and `package.json`.
- Updates `app.js` `_startCheckout` to `credentials: "include"` and reuses `/api/me.checkoutSession` on 401 instead of bouncing a signed-in member to subscribe.
