#!/usr/bin/env bash
# release-step9 (28 Nov 2026): the visuals pass, block chat114viz. Adds a Market Snapshot card, gauge bars, a key-price row with
# coloured % changes, sparklines, tiles and an events timeline to /brief/, /gold/, /markets/ and /research/ (the layer the owner
# approved in the preview). The block serves /__chat114viz/viz.css and viz.js itself and injects them into those four pages'
# finished HTML; it logs '[chat114viz] attached'. Changes ONLY server.js (one appended block). No Stripe, webhook, secret, config,
# schema, route, endpoint or page-file edits. Refuses unless server.js is the LIVE step 8 (md5 a633becfed6eb4e12c88415cdccf6fd7,
# 2,539,589 B) ending in the exact chat112verifymail + chat113cookie blocks, app.js/index.html/styles.css/c93.css are the live
# files and the block anchors match. Snapshots server.js into .release-snapshots/step9-<TS>/. Does NOT restart, publish, touch the
# DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=f33958f91e6ed4934ed32cfef1b9c71847ca3510
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step9"
MANIFEST=(
  "release_step9.py b411dd26f3c4b60041a69eed44ed19f538bd45e54640b149bfb68b1d4e7703e0"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat112verifymail.js 160253b99d6934f47b188d83867ef46b34d2f31349d388a6234f86515e4f9148"
  "server_block_chat113cookie.js 4d9d8357c574affbc448e3595f956d5a15560deacf867e1201e41786f6131791"
  "server_block_chat114viz.js ebd90c4889d1d9dcdba21762d7d04162c3ea45caf515c88513f0a20219b4d8b6"
  "viz.css 1f9469b689b52ebb1409d1e120307e7eb973cd956b80ab4acc6203c932489076"
  "viz.js 22d9ec7789d5f9e4d1e49111b95f9852c07da7a9520fd16c4e3469d95468e934"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step9] ABORT: $*" >&2; echo "[release-step9] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R9_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step9.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R9_LOCAL_PAYLOAD:-}" ]; then cp "$R9_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step9] payload ok: $f $got"; done
python3 "$P/release_step9.py" "$MODE" "$ROOT" "$P"
