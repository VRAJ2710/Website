#!/usr/bin/env bash
# deploy-chat102r6p: Terminal previous close is the last completed daily session.
# Re-pinned after v3 home preview blocks (chat105v3home / chat105v3home2)
# were inserted before the scrub marker. The payload is unchanged.
# Does NOT start the server, npm, git, or republish. Does not change EXPECT_TAG.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=85f68bc7386b444085545274688016b1059058f1
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102r6p"
# app.js and index.html stay the current dev bytes. server.js must match the
# full-file md5 below; a mismatch refuses and leaves files untouched.
# The r6o scrub is identified by MARKER-to-EOF size and sha256, not a fixed prefix.
APP_MD5=d8ca8562df01bf88c68e4971752e602c
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
SERVER_MD5=7a3aeaf7a9e317ce888e28e4b9d4461a
SCRUB_SHA=e45d46bf24eca1e3585739491058fc7470b7faffd7ba54600764f90594d63cbc
SCRUB_BYTES=29743
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102r6c last-write scrub.'
MANIFEST=(
  "patch_c102r6p.py 43eebfd9f2cefa09cf0139ba4b897f1b202b6055098d90c425eb3c54ea968a41"
  "server_block_c102r6o.js e45d46bf24eca1e3585739491058fc7470b7faffd7ba54600764f90594d63cbc"
  "server_block_c102r6p.js b896eb5a35c3a1e5db30c8ff3143a189b513d1d9c86dc741d370ac76b0449445"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102r6p] $*"; }
die(){ echo "[deploy-chat102r6p] ABORT: $*" >&2; echo "[deploy-chat102r6p] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
case "$PAYLOAD_COMMIT" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) die "PAYLOAD_COMMIT is not a 40-character commit" ;;
esac
# 40 zeros is the unpinned placeholder and must not be used on a live root.
[ "$PAYLOAD_COMMIT" != "0000000000000000000000000000000000000000" ] || die "PAYLOAD_COMMIT is not pinned"
for t in node python3 md5sum sha256sum curl cp grep cmp; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in
  *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;;
esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
say "project folder: $ROOT"
say "root server.js = $SERVER"
say "root app.js = $APP"
say "root index.html = $INDEX"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "root md5: server $sm | app $am | index $im"
W=$(mktemp -d /tmp/deploy-chat102r6p.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
[ "$am" = "$APP_MD5" ] || die "replace refused: root app.js md5 $am is not the current dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "replace refused: root index.html md5 $im is not the current dev index $INDEX_MD5"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "project-root server.js line 1 is not the maintenance=false line"
if grep -q '\[c102r6p\] scrub attached' "$SERVER" && [ "$am" = "$APP_MD5" ] && [ "$im" = "$INDEX_MD5" ]; then
  say "REFUSE: deploy-chat102r6p is already applied. Nothing changed."
  rm -rf "$W"
  exit 0
fi
[ "$sm" = "$SERVER_MD5" ] || die "replace refused: root server.js md5 $sm is not the current dev server $SERVER_MD5"
python3 - "$SERVER" "$MARKER" "$SCRUB_SHA" "$SCRUB_BYTES" << 'PY' || die "replace refused: server.js does not end with the current r6o scrub block"
import pathlib, sys, hashlib
server, marker, expect, expect_bytes = sys.argv[1:]
raw = pathlib.Path(server).read_bytes()
mb = marker.encode("utf-8")
idx = raw.find(mb)
if idx < 0 or raw.find(mb, idx + 1) >= 0:
    sys.exit("project-root server.js does not contain exactly one last-write scrub marker")
if raw.count(b"[c102r6p] scrub attached") >= 1:
    sys.exit("r6p attach log present on a root that is not already-applied")
if raw.count(b"[c102r6o] scrub attached") != 1:
    sys.exit("project-root server.js does not have the single r6o attach log")
block = raw[idx:]
n = len(block)
got = hashlib.sha256(block).hexdigest()
if str(n) != expect_bytes:
    sys.exit("scrub block bytes " + str(n) + " is not " + expect_bytes)
if got != expect:
    sys.exit("scrub block sha256 " + got + " is not " + expect)
prefix = raw[:idx]
print("prefix sha256", hashlib.sha256(prefix).hexdigest())
print("prefix bytes", len(prefix))
print("scrub sha256", got)
print("scrub bytes", n)
PY
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c102r6p.py" "$S/server.js" "$P/server_block_c102r6o.js" "$P/server_block_c102r6p.js" || die "patch_c102r6p failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/app.js")" = "$APP_MD5" ] && [ "$(md5of "$S/index.html")" = "$INDEX_MD5" ] || die "app.js or index.html changed"
grep -q '\[c102r6p\] scrub attached' "$S/server.js" || die "r6p attach log missing from scratch server.js"
grep -q '\[c102r6o\] scrub attached' "$S/server.js" && die "r6o attach log is still in the scratch server.js"
python3 - "$SERVER" "$S/server.js" << 'PY' || die "bytes before the scrub block changed"
import hashlib, pathlib, sys
old = pathlib.Path(sys.argv[1]).read_bytes()
new = pathlib.Path(sys.argv[2]).read_bytes()
marker = b"// chat102r6c last-write scrub."
io, inn = old.find(marker), new.find(marker)
if io < 0 or inn < 0:
    sys.exit("marker missing")
if old.find(marker, io + 1) >= 0 or new.find(marker, inn + 1) >= 0:
    sys.exit("marker is not unique")
if old[:io] != new[:inn]:
    sys.exit("prefix mismatch")
old_sha = hashlib.sha256(old[:io]).hexdigest()
new_sha = hashlib.sha256(new[:inn]).hexdigest()
if old_sha != new_sha:
    sys.exit("prefix sha256 changed: " + old_sha + " -> " + new_sha)
if not new.rstrip().endswith(b"})();"):
    sys.exit("scrub block is not last")
print("prefix sha256 before", old_sha)
print("prefix sha256 after", new_sha)
print("prefix bytes", io)
print("scrub block is last")
PY
say "scratch build ok. CPI and every byte before the scrub block are unchanged. Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat102r6p"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"
done
cp "$S/server.js" "$SERVER.new-chat102r6p" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat102r6p" "$SERVER" || { echo "[deploy-chat102r6p] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-chat102r6p] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: project-root server.js updated. app.js and index.html were left as the current dev bytes. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
