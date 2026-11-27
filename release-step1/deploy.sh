#!/usr/bin/env bash
# release-step1 (27 Nov 2026): build the r6n + v3-default release tree in the Replit workspace, for a separate publish.
# Order: step 1 of 7 (v3 default, r6p, credits, navy visuals, softgate, email_verified column, verification emails).
# Starts from the exact live r6n files: server.js/app.js/index.html from the dev *.bak-chat102r6o backups (r6n pins:
# server 4bfbb35e..., app bd13a193... = live app.js), every other file from the git commit holding them (styles.css and
# c93.css must equal live). Snapshots every dev file it touches into .release-snapshots/step1-<TS>/ first (manifest +
# restore_release.py). Appends v3home2, chat108saferxA/B/C and chat109v3default to the r6n server.js.
# Does NOT restart, publish, touch the DB, secrets, git history or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=656568eedf5ad457bd31cf2d06260d8150b3a320
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step1"
MANIFEST=(
  "release_step1.py 8bb3b8b4ad5ca44e5284cc7a3714e189c6a53ef7611385916809b66d7b7f1505"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
  "server_block_chat108saferxA.js 482affe68ca5f333bf8e9f4feb9b13ccfd16ab9213480b25ae3f8517fa63bd8c"
  "server_block_chat108saferxB.js bd06d3bcd0e0e0c04728d11cbe130a208c47a45de921a947cb9c967a7569492c"
  "server_block_chat108saferxC.js 99d9ec80c7415022785287874631115494887a1e8edbf24c4a15b8785dc246c5"
  "server_block_chat109v3default.js 8f7d8a29dc6def835b2e1ce10a8f6b90ae0e1575cccced50f3b367ba77ab7f49"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step1] ABORT: $*" >&2; echo "[release-step1] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R1_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step1.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R1_LOCAL_PAYLOAD:-}" ]; then cp "$R1_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step1] payload ok: $f $got"; done
python3 "$P/release_step1.py" "$MODE" "$ROOT" "$P"
