# deploy-chat106softgate (dev only, held for the next single release)

Vraj, 15 Nov 2026 (option A): "Go with A: add the DNS records, test it, and keep checkout open with a reminder until it works".

What changes in `server.js` (only bytes before the chat105v3home2 block; app.js and index.html untouched):
- `const VERIFY_ENFORCE = false;` is a code constant (not env, not a secret, not config). When false, sign-up, sign-in and
  checkout are never blocked because `email_verified` is false. Set it to true to restore the Claude Code hard gate exactly.
- The session lookup accepts unverified accounts unless VERIFY_ENFORCE (`AND (u.email_verified=TRUE OR $n=1)`).
- Sign-up: a new account is still stored with `email_verified=false`, the existing verification email is sent, and the
  reader is signed in. Re-registering an unverified address with the right password signs in and sends a fresh link.
- Sign-in: no verify-first page unless VERIFY_ENFORCE.
- Checkout (`POST /__auth/subscribe`): a new unverified account gets its email and goes on to `/?checkout=1`.
- Reminder: "Please verify your email" with a resend button on the signed-in checkout page (plain HTML, works with the
  auth CSP `script-src 'none'`) and as a dismissible card on the signed-in app pages (account/settings, checkout hand-off)
  via `/__auth/verify/reminder.js`, added to INDEX_TEMPLATE output through `withAssetVersion`. Guests and verified
  readers see nothing (status endpoint returns `{reminder:false}`).
- New routes: `POST /__auth/verify/resend` (same-origin, auth rate limit, 60 s per-account cooldown),
  `GET /__auth/verify/status`, `GET /__auth/verify/reminder.js`.
- A failed or throwing send never stops sign-up or checkout. Delivery failures are logged once by the existing
  `reportRecoveryDeliveryFailure`; a throw in the send path is logged once as `verification_email_failed` (no address).
- Unchanged: the `email_verified` column and its ALTER, `issueEmailVerification` / the Resend email text, the
  /__auth/verify routes, the Ask provider order, Stripe code, the webhook rejection log. No DDL, no secret/config change.

Apply order: AFTER deploy-chat102r6p (re-pinned on dev 5ce95f3, 16 Nov 2026). On the pre-r6p root it refuses ("apply r6p first").

Guards (the post-r6p md5 cannot be computed off-box, so the root is pinned byte-exact by parts):
- bytes before the chat105v3home2 block: sha256 8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae, 2,332,205 B
- chat105v3home2 block byte-exact (sha256 1da4d654...), ending at the single scrub marker
- marker to EOF = r6p scrub byte-exact (sha256 3f02d689..., 33,579 B, includes the 5ce95f3 rewriteHtml auth-page script strip); total 2,418,647 B
- prefix + chat105v3home2 + r6o scrub (sha256 97cf896d..., 30,043 B) must have md5 5b2b6d8061d876f0093cbe7caa4629af (dev 5ce95f3)
- app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389

Every edit is an anchored regex that must match exactly once (indentation-tolerant); otherwise nothing is written.

Run in the Replit Shell, in the project folder, after r6p:
```
curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/<INSTALLER_COMMIT>/deploy-chat106softgate/deploy.sh -o /tmp/d106.sh
echo "<SHA256>  /tmp/d106.sh" | sha256sum -c -
bash /tmp/d106.sh --measure
bash /tmp/d106.sh --dry-run
bash /tmp/d106.sh
```
Restart only the "Start application" workflow; expect exactly one `[chat106softgate] attached` line.
Undo: `cp server.js.<TS>.bak-chat106softgate server.js` and restart the workflow.

Tests (box): `python3 test/run_patch_tests.py` (patch + behaviour with the flag off and on, refusals, indentation),
`bash test/run_deploy_tests.sh` (measure / dry-run / apply / re-run / pre-r6p refusal on a fixture),
`python3 test/render_check.py <outdir>` (reminder at 320/390/1280, light and dark). The fixture is a reconstruction
of the dev auth code from the exported diff, not the real dev server.js.
