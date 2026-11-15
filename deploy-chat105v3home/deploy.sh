#!/usr/bin/env bash
# deploy-chat105v3home: v3 home page PREVIEW behind /?preview=v3 (cookie td_v3p=1). Preview only.
# Inserts one self-contained block into server.js just before the single last-write scrub marker.
# app.js and index.html are guarded and left byte-identical. / without the switch is passed through untouched.
# Does NOT start the server, npm, git, or republish. No DB, auth, Stripe, AI, email, secret or config change.
#
# Base: current Replit dev workspace HEAD fef1da0 (Claude Code, 15 Nov 14:16 UK). Guards below; a mismatch refuses
# and leaves every file untouched.
# Usage (from the project folder in the Replit Shell):
#   bash deploy.sh --measure      # read-only: prints md5s, marker and attach counts, exits
#   bash deploy.sh --dry-run
#   bash deploy.sh
set -u
SERVER_MD5=9c593e7ab7887a20ba876e938abca0fc
APP_MD5=d8ca8562df01bf88c68e4971752e602c
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
PREFIX_SHA=8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae
PREFIX_BYTES=2332205
PAYLOAD_COMMIT=2654bc92bceff1d9d2a0d2212a4fb77595475f58
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat105v3home"
TAG=chat105v3home
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102r6c last-write scrub.'
ATTACH='[chat105v3home] preview attached'
MANIFEST=(
  "patch_chat105v3home.py 50c4868ef41479a4686ec24cb4f61f343a0c23e0df5b4f7b1d7184518370ddda"
  "server_block_chat105v3home.js 2a3797f0d4573b1ae8d94a966fa6365e25d9c47f9f9c1fc1d02853f311ffde5b"
)
DRY=0; MEASURE=0; DIR=""; XS="$SERVER_MD5"; XA="$APP_MD5"; XI="$INDEX_MD5"
while [ $# -gt 0 ]; do case "$1" in
  --dry-run) DRY=1;; --measure) MEASURE=1;;
  --dir) shift; DIR="${1:-}";;
  *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-$TAG] $*"; }
die(){ echo "[deploy-$TAG] ABORT: $*" >&2; echo "[deploy-$TAG] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep cmp; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;; esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "project folder: $ROOT"
say "root md5: server $sm | app $am | index $im"
say "server.js bytes $(wc -c < "$SERVER") | scrub markers $(grep -cF "$MARKER" "$SERVER") | c102 attach lines $(grep -cE '\[c102r6[a-z]\] scrub attached' "$SERVER") | $TAG attach lines $(grep -cF "$ATTACH" "$SERVER")"
say "line 1 is the maintenance=false line: $([ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] && echo yes || echo NO)"
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing changed."; exit 0; fi
if grep -qF "$ATTACH" "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$sm" = "$XS" ] || die "server.js md5 $sm is not the guarded dev server $XS"
[ "$am" = "$XA" ] || die "app.js md5 $am is not the guarded dev app $XA"
[ "$im" = "$XI" ] || die "index.html md5 $im is not the guarded dev index $XI"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ "$(grep -cF "$MARKER" "$SERVER")" = "1" ] || die "server.js does not contain exactly one last-write scrub marker"
[ "$(grep -cE '\[c102r6[a-z]\] scrub attached' "$SERVER")" = "1" ] || die "server.js does not contain exactly one c102 scrub attach line"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat105v3home.py" "$S/server.js" "$P/server_block_chat105v3home.js" || die "patch failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG attach line"
PCHK="$PREFIX_SHA"; PB="$PREFIX_BYTES"
python3 - "$SERVER" "$S/server.js" "$P/server_block_chat105v3home.js" "$PCHK" "$PB" << 'PY' || die "bytes outside the inserted block changed"
import pathlib, sys, hashlib
old = pathlib.Path(sys.argv[1]).read_bytes(); new = pathlib.Path(sys.argv[2]).read_bytes()
blk = pathlib.Path(sys.argv[3]).read_bytes().rstrip(b"\n") + b"\n"
m = b"// chat102r6c last-write scrub."
i = old.find(m)
if new != old[:i] + blk + old[i:]: sys.exit("scratch is not old prefix + block + old suffix")
ps = hashlib.sha256(old[:i]).hexdigest()
if sys.argv[4] != "-" and (ps != sys.argv[4] or str(i) != sys.argv[5]): sys.exit("prefix sha256 " + ps + " / " + str(i) + " bytes is not the guarded " + sys.argv[4] + " / " + sys.argv[5])
print("prefix sha256", ps, "bytes", i)
print("suffix (scrub block to EOF) sha256", hashlib.sha256(old[i:]).hexdigest(), "bytes", len(old) - i)
print("inserted bytes", len(blk))
PY
NS=$(md5of "$S/server.js")
say "scratch build ok. Only the block was inserted; everything else is byte-identical."
echo "scratch server.js md5 $NS ($(wc -c < "$S/server.js") bytes)"
echo "scratch app.js md5 $(md5of "$S/app.js") | index.html md5 $(md5of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
[ "$(md5of "$SERVER")" = "$XS" ] || die "server.js changed during the run"
TS=$(date +%Y%m%d-%H%M%S); SUFF="bak-$TAG"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"; done
cp "$S/server.js" "$SERVER.new-$TAG" || die "staging copy failed (project-root files untouched)"
RB="restore server.js from server.js.$TS.$SUFF and DO NOT republish"
mv -f "$SERVER.new-$TAG" "$SERVER" || { echo "[deploy-$TAG] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-$TAG] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: server.js md5 $(md5of "$SERVER"). app.js $(md5of "$APP") and index.html $(md5of "$INDEX") unchanged. Backups *.$TS.$SUFF"
say "Next: restart ONLY the 'Start application' workflow, then expect exactly one '$ATTACH' log line. Nothing was republished."
say "To undo: cp server.js.$TS.$SUFF server.js and restart the workflow."
rm -rf "$W"
