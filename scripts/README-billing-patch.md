# Live Replit billing session/host patch

For production Replit project `https://replit.com/@vraj2710/the-dispatch` (diverged from this repo's smaller `server.js`).

## Apply

In Replit Shell at the project root:

```bash
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/cursor/replit-billing-apply-script/scripts/apply_live_billing_fix.py -o apply_live_billing_fix.py
python3 apply_live_billing_fix.py
```

After merge to `main`, use the `main` raw URL instead.

## Then

1. Secret: `DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk` (not www)
2. Redeploy Autoscale
3. Confirm: `grep canonicalPublicOrigin server.js` and that `www.thedispatch.uk` 308s to apex
