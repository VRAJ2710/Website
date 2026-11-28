#!/usr/bin/env bash
# release-step10 (28 Nov 2026): chat115vizapp. Shows the approved visuals layer (Market Snapshot, gauges, key prices, sparklines, tiles,
# events; the same viz.css/viz.js as chat114viz) to SIGNED-IN readers inside the member app on /brief/, /gold/, /markets/ and /research/,
# without editing app.js. Appends one block to server.js; it logs '[chat115vizapp] attached', then '[chat115vizapp] injected <path>' once.
# Guest pages are untouched. No Stripe, webhook, secret, config, schema, route, endpoint or page-file edits. Refuses unless server.js is the
# STAGED step 9b (md5 9a8758213ee7a63eb5d24757c3aa78f3, 2,588,699 B) ending in the exact chat112verifymail + chat113cookie + step-9b
# chat114viz blocks, app.js/index.html/styles.css/c93.css are the live files and the block anchors match. Snapshots server.js into
# .release-snapshots/step10-<TS>/. Does NOT restart, publish, touch the DB, secrets, git or the network beyond this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=9153ebb8c9b11ccb3ff976709c072db96bdf8b85
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step10"
MANIFEST=(
  "release_step10.py 3645b06a0f33ce1d6f75758ae186ea6d2b61fd72557aa07ded3685942481e430"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat112verifymail.js 160253b99d6934f47b188d83867ef46b34d2f31349d388a6234f86515e4f9148"
  "server_block_chat113cookie.js 4d9d8357c574affbc448e3595f956d5a15560deacf867e1201e41786f6131791"
  "server_block_chat114viz.js 0ca32ae88513ddf0639f1d5f4425a9ddca8c2f18fac9abbed2c23cbd0ab11c90"
  "server_block_chat115vizapp.js 7d93f571513f551560c96c5b3e1b691e1a191f4388e020afff1d47375be8af86"
  "vizapp.js 61a2cd99be9193f8f0ab2320fd602d509d9b95a63bdbabc65c26fb1a2161e792"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step10] ABORT: $*" >&2; echo "[release-step10] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R9_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step10.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R9_LOCAL_PAYLOAD:-}" ]; then cp "$R9_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step10] payload ok: $f $got"; done
python3 "$P/release_step10.py" "$MODE" "$ROOT" "$P"
