#!/usr/bin/env bash
# release-step4 (27 Nov 2026): live step 3 (r6n + r6p + v3 default + FRED credits) + navy redesign VISUALS (chat110navy), for a
# separate publish. Order: step 4 of 7. Proves server.js is the exact step-3 build (2,493,329 B; rebuilt from the r6n backup +
# pinned blocks) and app.js/index.html/styles.css/c93.css are the live files, then: styles.css -> navy (DM Sans), c93.css -> compat
# import, index.html -> 7 exact edits (navy shell, device-default theme, v=chat110navy), app.js -> 46 presentation hunks on the live
# bd13a193, server.js += presentation-only response block. Snapshots all five files into .release-snapshots/step4-<TS>/ first
# (manifest + restore_release.py). Optional: STEP3_SERVER_MD5=<md5 printed after step 3> adds an md5 check.
# Does NOT restart, publish, touch the DB, secrets, git or the network beyond downloading this pinned payload.
# Usage (Replit Shell, project folder): bash deploy.sh --measure | --dry-run | (no flag = apply)
set -u
PAYLOAD_COMMIT=5f8b52d3825a8663b28c00744d3dd1288f485fb8
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/release-step4"
MANIFEST=(
  "release_step4.py a4f04ce4b9c331a746d2a10bf9af73a0f3ffa6812cc56172df9f82aa0932473f"
  "restore_release.py 446d8fd266f30833a752827b1dadb0b59b5ecca1102307c6cb07ff70bb84088d"
  "index_edits.json 0b0604675b85e63ab01654a5b8f470bcd61dbea683eeba1ad78260d52a97986c"
  "app_navy_patch.json ed684f8ca3919ad32941c5c8aecc55113ebef757e90c85ab30bfc0d3afd56165"
  "styles.navy.css e563fc5667367eb1e020378c7f600f06de1ce3ad255480f82db24ff1f567e330"
  "c93.css f476bf2ca121709835b84f9f49cf738ce4a4a3517ce78f5e595e49d8738cd7bd"
  "server_block_c102r6n.js 7d681e0672432f3e6df7f478014854f463ee42b1c800cfd7715534378eb57ee3"
  "server_block_c102r6p.js a015681e81fd55f6c93c72b1aaea3ce3899f025d1e680df150767c367bab9532"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
  "server_block_chat108saferxA.js 482affe68ca5f333bf8e9f4feb9b13ccfd16ab9213480b25ae3f8517fa63bd8c"
  "server_block_chat108saferxB.js bd06d3bcd0e0e0c04728d11cbe130a208c47a45de921a947cb9c967a7569492c"
  "server_block_chat108saferxC.js 99d9ec80c7415022785287874631115494887a1e8edbf24c4a15b8785dc246c5"
  "server_block_chat109v3default.js 8f7d8a29dc6def835b2e1ce10a8f6b90ae0e1575cccced50f3b367ba77ab7f49"
  "server_block_chat107credits.js b31efd1828d78863a36e31c6c6179199ca56352b010dc4ef61a0098dcd54e7b1"
  "server_block_chat110navy.js 6b5b922def77f0e0caf4d9536dce2f5d73ae4f54586403c3d16f9f2fc025a602"
)
MODE=apply; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry-run;; --measure) MODE=measure;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
die(){ echo "[release-step4] ABORT: $*" >&2; echo "[release-step4] Nothing in the project was changed." >&2; exit 1; }
for t in node python3 git sha256sum curl; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${R4_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find the project folder; cd into it or pass --dir"; fi
case "$ROOT" in *mockup*|*/.backups*|*/.release-snapshots*) die "refusing $ROOT";; esac
P=$(mktemp -d /tmp/release-step4.XXXXXX) || die "mktemp failed"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${R4_LOCAL_PAYLOAD:-}" ]; then cp "$R4_LOCAL_PAYLOAD/$f" "$P/$f" || die "local copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $f"; fi
  got=$(sha256sum "$P/$f" | awk '{print $1}'); [ "$got" = "$h" ] || die "sha256 mismatch for $f: $got (expected $h)"
  echo "[release-step4] payload ok: $f $got"; done
python3 "$P/release_step4.py" "$MODE" "$ROOT" "$P"
