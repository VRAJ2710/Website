#!/usr/bin/env bash
# deploy-chat105v3home2: replaces the chat105v3home preview block with chat105v3home2. Preview only.
#  - In the preview, a visitor with no dispatch_theme cookie (no real choice) is rendered as "system", so the page
#    follows the device; a real Light/Dark/System choice is kept. Light v3 tokens apply.
#  - In the preview, the market tape shows plain-English labels. The tape outside the preview is untouched.
# Normal / without the switch is passed through untouched, as before. app.js and index.html are guarded and unchanged.
# Guards (no fixed server md5): the chat105v3home block (sha256 2a3797f0...) must be present exactly once, end at the
# single scrub marker, the bytes before it must be the fef1da0 prefix and the bytes from the marker to EOF the r6o scrub.
# Does NOT start the server, npm, git, or republish. No DB, auth, Stripe, AI, email, secret or config change.
# Usage (project folder, Replit Shell): bash deploy.sh --measure | --dry-run | (no flag to apply)
set -u
PAYLOAD_COMMIT=abcae4a04fb134f98ccbe4faaf2fbefb2e2d02ee
OLD_COMMIT=2654bc92bceff1d9d2a0d2212a4fb77595475f58
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat105v3home2"
OLD_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${OLD_COMMIT}/deploy-chat105v3home"
TAG=chat105v3home2
APP_MD5=d8ca8562df01bf88c68e4971752e602c
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
PREFIX_SHA=8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae
PREFIX_BYTES=2332205
SCRUB_SHA=e45d46bf24eca1e3585739491058fc7470b7faffd7ba54600764f90594d63cbc
SCRUB_BYTES=29743
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102r6c last-write scrub.'
OLD_ATTACH='[chat105v3home] preview attached'
ATTACH='[chat105v3home2] preview attached'
MANIFEST=(
  "$BASE_URL patch_chat105v3home2.py e3cfa1a236079f657fd28438f0cfb2b490013f87772669e82f971885eee08414"
  "$BASE_URL server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
  "$OLD_URL server_block_chat105v3home.js 2a3797f0d4573b1ae8d94a966fa6365e25d9c47f9f9c1fc1d02853f311ffde5b"
)
DRY=0; MEASURE=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --measure) MEASURE=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-$TAG] $*"; }
die(){ echo "[deploy-$TAG] ABORT: $*" >&2; echo "[deploy-$TAG] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;; esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "project folder: $ROOT"
say "root md5: server $sm ($(wc -c < "$SERVER") bytes) | app $am | index $im"
say "scrub markers $(grep -cF "$MARKER" "$SERVER") | c102 attach $(grep -cE '\[c102r6[a-z]\] scrub attached' "$SERVER") | chat105v3home attach $(grep -cF "$OLD_ATTACH" "$SERVER") | chat105v3home2 attach $(grep -cF "$ATTACH" "$SERVER")"
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing changed."; exit 0; fi
if grep -qF "$ATTACH" "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$am" = "$APP_MD5" ] || die "app.js md5 $am is not the guarded dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "index.html md5 $im is not the guarded dev index $INDEX_MD5"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ "$(grep -cF "$MARKER" "$SERVER")" = "1" ] || die "server.js does not contain exactly one scrub marker"
[ "$(grep -cE '\[c102r6[a-z]\] scrub attached' "$SERVER")" = "1" ] || die "server.js does not contain exactly one c102 scrub attach line"
[ "$(grep -cF "$OLD_ATTACH" "$SERVER")" = "1" ] || die "server.js does not contain exactly one chat105v3home attach line"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT (old block from $OLD_COMMIT)"
for e in "${MANIFEST[@]}"; do set -- $e; u="$1"; f="$2"; h="$3"
  curl -fsSL --retry 2 "$u/$f" -o "$P/$f" || die "download failed: $u/$f"
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat105v3home2.py" "$S/server.js" "$P/server_block_chat105v3home.js" "$P/server_block_chat105v3home2.js" "$PREFIX_SHA" "$PREFIX_BYTES" "$SCRUB_SHA" "$SCRUB_BYTES" || die "patch refused (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG attach line"
[ "$(grep -cF "$OLD_ATTACH" "$S/server.js")" = "0" ] || die "old attach line still in scratch server.js"
NS=$(md5of "$S/server.js")
say "scratch build ok: only the preview block changed."
echo "scratch server.js md5 $NS ($(wc -c < "$S/server.js") bytes, expected 2414811)"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
[ "$(md5of "$SERVER")" = "$sm" ] || die "server.js changed during the run"
TS=$(date +%Y%m%d-%H%M%S); SUFF="bak-$TAG"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"; done
cp "$S/server.js" "$SERVER.new-$TAG" || die "staging copy failed (project-root files untouched)"
RB="restore server.js from server.js.$TS.$SUFF and DO NOT republish"
mv -f "$SERVER.new-$TAG" "$SERVER" || { echo "[deploy-$TAG] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-$TAG] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: server.js md5 $(md5of "$SERVER") (was $sm). app.js and index.html unchanged. Backups *.$TS.$SUFF"
say "Next: restart ONLY the 'Start application' workflow; expect exactly one '$ATTACH' line and no '$OLD_ATTACH' line. Nothing was republished."
say "To undo: cp server.js.$TS.$SUFF server.js and restart the workflow."
rm -rf "$W"
