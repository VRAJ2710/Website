#!/usr/bin/env bash
# release-step8 (28 Nov 2026): flatten the Premium sign-up Set-Cookie array (block chat113cookie, plus one
# unique prefix replace). After a NEW Premium account (POST /__auth/subscribe) Node was given a nested
# Set-Cookie array and joined the session cookies with commas, so browsers stored an empty session and
# the member returned from checkout signed out. The fix flattens with [].concat and appends
# dispatch_account_created instead of overwriting. A trailing chat113cookie block logs
# '[chat113cookie] attached'. Changes ONLY server.js. No Stripe, webhook, secret, config, schema,
# route or page edits. Refuses unless server.js is the LIVE step 7 (md5 589ede82983f3e9feda48c1dde7e805e,
# 2,538,324 B), app.js/index.html/styles.css/c93.css are the live files, the file ends with the exact
# chat112verifymail block and the buggy Set-Cookie line occurs once. Snapshots server.js into
# .release-snapshots/step8-<TS>/. Does NOT restart, publish, touch the DB, secrets, git or the network
# beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=d4eb1f36ab5660adb386a17dfe69fce85ba75da6
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step8"
MANIFEST=(
  "release_step8.py bd3a44261fa0f771b049c787322d9d3f73d2838f86335c673ad1295c7d48b6d9"
  "anchors.py 9f70d12215ee6ce5a7855964c23ce4aba612f384c44b6ab9ce0dfcbb27d1818a"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat112verifymail.js 160253b99d6934f47b188d83867ef46b34d2f31349d388a6234f86515e4f9148"
  "server_block_chat113cookie.js 4d9d8357c574affbc448e3595f956d5a15560deacf867e1201e41786f6131791"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step8] ABORT: $*" >&2; echo "[release-step8] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R8_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step8.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R8_LOCAL_PAYLOAD:-}" ]; then cp "$R8_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step8] payload ok: $f $got"; done
python3 "$P/release_step8.py" "$MODE" "$ROOT" "$P"
