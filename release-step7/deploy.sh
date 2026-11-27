#!/usr/bin/env bash
# release-step7 (27 Nov 2026): verification emails, ENFORCEMENT OFF (block chat112verifymail, replaces step 6's chat111verify).
# Changes ONLY server.js (its last block). After a NEW sign-up it sends ONE verification email through the server's existing
# Resend connector wiring (same settings as password recovery), fire-and-forget with a timeout. Adds GET /__auth/verify,
# POST /__auth/verify/resend (rate-limited), GET /__auth/verify/status, GET /__auth/verify/reminder.js and a dismissible banner
# for signed-in unverified users only. Nobody is blocked. No schema change, no new env var or secret, no other email.
# Refuses unless server.js is the LIVE step 6 (md5 343f7f30ecebc6526a60ff90e1f49a48, 2,521,438 B), app.js/index.html/
# styles.css/c93.css are the live files and all prefix anchors match. Snapshots server.js into .release-snapshots/step7-<TS>/.
# Does NOT restart, publish, touch the DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=b97d4ae231d33904818d836e61f5af945b72ce58
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step7"
MANIFEST=(
  "release_step7.py 02648d35779bd8e4a0e68aa0fd20938929c54fe45641f72f5699ea5b728b6654"
  "anchors.py 9bf703aecdf1ce112ed2f49d1f7ecd4e54f62e50402a6e1b59c296bbd47f03ff"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat110navyb.js d8cd20fb7f716b9b2b768b58c902f2f211f3be169e5f63fbc997d1a32d5f9be7"
  "server_block_chat111verify.js 5b0afa41576778795edd5af1887c10e54501f7f63715276b4ea42467c5a074bc"
  "server_block_chat112verifymail.js 160253b99d6934f47b188d83867ef46b34d2f31349d388a6234f86515e4f9148"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step7] ABORT: $*" >&2; echo "[release-step7] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R7_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step7.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R7_LOCAL_PAYLOAD:-}" ]; then cp "$R7_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step7] payload ok: $f $got"; done
python3 "$P/release_step7.py" "$MODE" "$ROOT" "$P"
