# release-step6: email_verified bookkeeping, ENFORCEMENT OFF (chat111verify)

Changes ONLY server.js: one block (`server_block_chat111verify.js`) appended after the live chat110navyb block.

What changes: after a NEW account is created through POST /__auth/register or POST /__auth/subscribe (302 with a fresh
dispatch_session cookie, after the response has been sent), that one account gets `dispatch_users.email_verified = FALSE`
(only if created within the last 10 minutes and still TRUE). Existing accounts stay TRUE (the column default).

What does not change: every response, page, header, cookie and redirect. Nothing reads email_verified, so nobody is blocked from
sign-in, /api/me, checkout or content. No email, no Resend, no outbound HTTP. No CREATE/ALTER, no migration, no route,
env var or secret. `VERIFY_ENFORCE = false` is a code constant and the installer refuses a block where it is not false.
Stripe/billing code untouched (the prefix is byte-identical). If the column is missing (for example on the dev DB), the UPDATE fails,
one log line is written and the account is unaffected.

Installer: `bash deploy.sh --measure | --dry-run | (apply)`. Refuses unless server.js is live step 4b (c8e4af65…, 2,517,276 B)
ending in the exact chat110navyb block, app/index/styles/c93 are the live files, and every prefix anchor in anchors.py matches
(and no verification code exists yet). Snapshot: .release-snapshots/step6-<TS>/ with restore_release.py.

Tests: `bash test/run_step6_tests.sh` (box only; auth harness = verbatim lineage auth code over PGlite / Postgres 17).
