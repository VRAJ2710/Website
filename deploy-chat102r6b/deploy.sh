#!/usr/bin/env bash
# deploy-chat102r6b: scrub reader-facing tickers on the staged chat102r6 server.
# Server only. Does NOT start the server, npm, git, or republish.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit 491cbfc already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=491cbfcc65b6a357709586228617437610ca245c
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102r6b"
SERVER_MD5=a53eb7ebc9030ed0d1656354b9b8ef78
APP_MD5=780c96cdb52a1622664edca43faf9c34
INDEX_MD5=f926872550af1e09d3eef426438174e4
MANIFEST=(
  "patch_c102r6b.py 017ae7fcd32890d0c2c0990326a959843653cac51d78d739f6e4b66dd08e02a0"
  "server_block_c102r6b.js ac6c0b8775a66cb1a1f02ae2ab814c39a859996d3f991cb306d87847c69b88a9"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102r6b] $*"; }
die(){ echo "[deploy-chat102r6b] ABORT: $*" >&2; echo "[deploy-chat102r6b] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
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
W=$(mktemp -d /tmp/deploy-chat102r6b.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
if [ "$sm" != "$SERVER_MD5" ] || [ "$am" != "$APP_MD5" ] || [ "$im" != "$INDEX_MD5" ]; then
  die "replace refused: root server.md5 $sm app.md5 $am index.md5 $im is not the staged chat102r6 root (server $SERVER_MD5 app $APP_MD5 index $INDEX_MD5)."
fi
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c102r6b.py" "$S/server.js" "$P/server_block_c102r6b.js" || die "patch_c102r6b failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
cmp -s "$S/app.js" "$APP" || die "scratch app.js differs from the root app"
cmp -s "$S/index.html" "$INDEX" || die "scratch index.html differs from the root index"
grep -q "chat102r6b reader-facing scrub" "$S/server.js" || die "scrub marker missing"
say "scratch build ok. Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat102r6b"
cp -p "$SERVER" "$SERVER.$TS.$SUFF" || die "backup failed for server.js"
[ "$(md5of "$SERVER.$TS.$SUFF")" = "$sm" ] || die "backup verify failed for server.js"
say "backup: $SERVER.$TS.$SUFF"
cp "$S/server.js" "$SERVER.new-chat102r6b" || die "staging copy failed (project-root files untouched)"
mv -f "$SERVER.new-chat102r6b" "$SERVER" || { echo "[deploy-chat102r6b] ERROR during install; restore server.js from $SERVER.$TS.$SUFF and DO NOT republish" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-chat102r6b] ERROR: node --check failed after install; restore server.js from $SERVER.$TS.$SUFF" >&2; exit 1; }
[ "$(md5of "$APP")" = "$APP_MD5" ] && [ "$(md5of "$INDEX")" = "$INDEX_MD5" ] || { echo "[deploy-chat102r6b] ERROR: app.js or index.html changed; restore them and server.js from the r6b backup" >&2; exit 1; }
say "DONE: project-root server.js updated. app.js and index.html were not written. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore server.js from $SERVER.$TS.$SUFF."
rm -rf "$W"
