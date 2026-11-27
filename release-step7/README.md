# release-step7: verification emails, ENFORCEMENT OFF (chat112verifymail)

Changes ONLY server.js: its last block (step 6's chat111verify) is replaced by `server_block_chat112verifymail.js`.
Everything before it is byte-identical (sign-in, register, Stripe, checkout, Ask).

- New free or Premium sign-up (POST /__auth/register or /__auth/subscribe, 302 with a fresh session): after the response is
  sent, the new account is set email_verified=FALSE (as in step 6). Only when that actually flips it does it get a token
  (dispatch_email_verifications, 24 h) and ONE plain-text email through the existing Resend wiring: the Replit Resend connector
  (`connectors.proxy("resend", "/emails")`, as password recovery uses it), from DISPATCH_RECOVERY_EMAIL_FROM, only when
  DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend and the from-address is @thedispatch.uk. Timeout = DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS
  (500..15000, else 5000). Fire-and-forget; a failure or timeout writes one log line (no address in the log).
- GET /__auth/verify?token=: single-use; sets email_verified=TRUE and shows "Email confirmed" (existing auth page style).
  Used, expired, malformed or missing tokens get a friendly page. HEAD never uses the token up.
- POST /__auth/verify/resend: same-origin, signed-in, unverified; 1 per 5 min (memory + DB) and 5 per 24 h per user (memory,
  per instance), counting the sign-up email.
- GET /__auth/verify/status, GET /__auth/verify/reminder.js: the banner. Pages requested with a session cookie get one
  script tag; the banner shows only when the signed-in user is unverified. It can be dismissed for 24 h. Guests get
  byte-identical pages.
- VERIFY_ENFORCE=false: nothing blocks sign-in, /api/me, checkout or content. No schema change, new env var, secret or alert email.

Installer: `bash deploy.sh --measure | --dry-run | (apply)`. Refuses unless server.js is live step 6 (343f7f30…, 2,521,438 B).
Tests: `bash test/run_step7_tests.sh` (box only; Resend mocked, no network).
