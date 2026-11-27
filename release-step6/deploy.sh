#!/usr/bin/env bash
# release-step6 (27 Nov 2026): email_verified bookkeeping, ENFORCEMENT OFF (block chat111verify). Changes ONLY server.js by appending
# one block after the live chat110navyb block. After a NEW sign-up (POST /__auth/register or /__auth/subscribe, 302 + fresh session)
# it sets dispatch_users.email_verified=FALSE for that new account only. Nothing reads the column, nothing is blocked, no email,
# no outbound HTTP, no schema change, no route, env var or secret. Refuses unless server.js is the LIVE step 4b
# (md5 c8e4af6528a4a75936f18e9a2740140c, 2,517,276 B), app.js/index.html/styles.css/c93.css are the live step-4 files and all prefix
# anchors match. Snapshots server.js into .release-snapshots/step6-<TS>/ first (manifest + restore_release.py).
# Does NOT restart, publish, touch the DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=f5a5aa34a93f7b879bfb9c67eaf3e95e31188523
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step6"
MANIFEST=(
  "release_step6.py e80de467178b5f88d1f8eed7d3d8ba1af617a06c056fab735c42674e6a8758a5"
  "anchors.py cc52711c833b4d2191292aaf5a2fc05914012c041487d6e37ce9c45d1407c131"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat110navyb.js d8cd20fb7f716b9b2b768b58c902f2f211f3be169e5f63fbc997d1a32d5f9be7"
  "server_block_chat111verify.js 5b0afa41576778795edd5af1887c10e54501f7f63715276b4ea42467c5a074bc"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step6] ABORT: $*" >&2; echo "[release-step6] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R6_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step6.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R6_LOCAL_PAYLOAD:-}" ]; then cp "$R6_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step6] payload ok: $f $got"; done
python3 "$P/release_step6.py" "$MODE" "$ROOT" "$P"
