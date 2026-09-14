# The Dispatch Markets

Live Replit autoscale app behind [https://thedispatch.uk](https://thedispatch.uk).

```sh
node server.js
```

Premium is **£15/month GBP**. Do not change pricing or invent Stripe keys.

## Production billing (Replit)

After deploying this revision:

1. In Replit **production** Secrets / `userenv.production`, set:
   - `DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk`
   - (currently may still be `https://www.thedispatch.uk` — change it)
2. Redeploy the autoscale app (`node server.js`).
3. Stripe webhook path is **`/api/stripe/webhook`** (alias `/api/stripe-webhook` also accepted). Dashboard endpoint: `https://thedispatch.uk/api/stripe/webhook`.

Session cookies are `Secure` + `Domain=thedispatch.uk` on production hosts so apex and www share the same login. `www.thedispatch.uk` 308s to apex.

## Manual test checklist

1. Open `https://thedispatch.uk/__auth/subscribe` (not www). Create a new test account.
2. Confirm `302 Location: /?checkout=1` and `Set-Cookie: dispatch_session=...; Secure; Domain=thedispatch.uk`.
3. Browser should go to `https://checkout.stripe.com/...` (not back to subscribe).
4. Pay or cancel. Cancel returns to `https://thedispatch.uk/?checkout=cancelled`.
5. After payment, `/api/me` → `tier:"premium"` on apex. Then open billing portal and confirm return to apex.
6. Repeat starting on `https://www.thedispatch.uk` — 308 to apex, same session.
7. Unauthenticated `POST /api/create-checkout` still 401; `POST /api/billing-portal` still 400.

Local helper tests (no Stripe secrets):

```sh
npm run test:billing
```
