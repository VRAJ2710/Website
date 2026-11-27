#!/usr/bin/env bash
# release-step4b (27 Nov 2026): DELTA on top of the staged step 4. Changes ONLY server.js, inside the appended chat110navy block:
# embedded site.css gains html.nvb body:has(#c101-inst){padding-bottom:184px!important} (phone width; the footer's last line, the FRED
# notice, was hidden behind the install bar) and the site.css cache tag becomes v=chat110navyb. Refuses unless server.js is the staged
# step 4 (md5 ec413c6bd2562aa0cd14fc6d69e16210, 2,517,162 B) and app.js/index.html/styles.css/c93.css are the step-4 files.
# Snapshots server.js into .release-snapshots/step4b-<TS>/ first (manifest + restore_release.py).
# Does NOT restart, publish, touch the DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=25819f1f41c67cdbda2f56b461bd02259cd3b088
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step4b"
MANIFEST=(
  "release_step4b.py 465c1f9d9f0a14565e3c9c6678ca421b2c899246bd58ce35921d25f06f589ed5"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "server_block_chat110navy.js 6b5b922def77f0e0caf4d9536dce2f5d73ae4f54586403c3d16f9f2fc025a602"
  "server_block_chat110navyb.js d8cd20fb7f716b9b2b768b58c902f2f211f3be169e5f63fbc997d1a32d5f9be7"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step4b] ABORT: $*" >&2; echo "[release-step4b] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R4B_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step4b.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R4B_LOCAL_PAYLOAD:-}" ]; then cp "$R4B_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step4b] payload ok: $f $got"; done
python3 "$P/release_step4b.py" "$MODE" "$ROOT" "$P"
