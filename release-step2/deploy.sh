#!/usr/bin/env bash
# release-step2 (27 Nov 2026): live step 1 (r6n + v3 default) + the r6p data fixes, for a separate publish.
# Order: step 2 of 7 (v3 default, r6p, credits, navy visuals, softgate, email_verified column, verification emails).
# server.js only: guards the live step-1 server (md5 dc4ceaf9..., 2,465,272 B), proves it is the r6n backup + the five v3
# blocks byte-exact, and replaces only the r6n last-write scrub with the r6p scrub. Snapshots server.js into
# .release-snapshots/step2-<TS>/ first (manifest + restore_release.py).
# Does NOT restart, publish, touch the DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=7f9d37e1589afc7d2a415a68fe52155fa00fcc92
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step2"
MANIFEST=(
  "release_step2.py fea5f69499289fa93be2d60e3af2c0acc1b62e6ec5ee3e32b2090c7a9938612a"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_c102r6n.js 7d681e0672432f3e6df7f478014854f463ee42b1c800cfd7715534378eb57ee3"
  "server_block_c102r6p.js a015681e81fd55f6c93c72b1aaea3ce3899f025d1e680df150767c367bab9532"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
  "server_block_chat108saferxA.js 482affe68ca5f333bf8e9f4feb9b13ccfd16ab9213480b25ae3f8517fa63bd8c"
  "server_block_chat108saferxB.js bd06d3bcd0e0e0c04728d11cbe130a208c47a45de921a947cb9c967a7569492c"
  "server_block_chat108saferxC.js 99d9ec80c7415022785287874631115494887a1e8edbf24c4a15b8785dc246c5"
  "server_block_chat109v3default.js 8f7d8a29dc6def835b2e1ce10a8f6b90ae0e1575cccced50f3b367ba77ab7f49"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step2] ABORT: $*" >&2; echo "[release-step2] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R2_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step2.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R2_LOCAL_PAYLOAD:-}" ]; then cp "$R2_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step2] payload ok: $f $got"; done
python3 "$P/release_step2.py" "$MODE" "$ROOT" "$P"
