#!/usr/bin/env bash
# deploy-chat102r6i: desk-quotes vendor names, futures source line, scenario copy, chart axis.
# Runs after chat104 and chat103h. Md5 guards below are placeholders until those land.
# Does NOT start the server, npm, git, or republish.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit 0e00102 already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=0e001025592b73d99aec102e0681b71ba5db1232
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102r6i"
# Re-pin these three after chat104 then chat103h are on the dev root.
SERVER_MD5=PENDING_AFTER_CHAT104_CHAT103H_SERVER
APP_MD5=PENDING_AFTER_CHAT104_CHAT103H_APP
INDEX_MD5=PENDING_AFTER_CHAT104_CHAT103H_INDEX
PREFIX_SHA=715b843b5e7b15e38a16a6478337d7f94752eeb4da3b902b4bcd60603e15aaa7
MANIFEST=(
  "patch_c102r6i.py 5a6b9ed5864536050c9a3ef36cd165be707cfc8a171f10a2d98c8bee7c0725c5"
  "server_block_c102r6h.js a43946915199319e6e607b61cb3307e37f8639e03c2d85c2b3fbf84c83e820e0"
  "server_block_c102r6i.js c5825601a87596b480fd6fec40c9da9e2ac865296c959293e1b3b7d057f61313"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102r6i] $*"; }
die(){ echo "[deploy-chat102r6i] ABORT: $*" >&2; echo "[deploy-chat102r6i] Nothing was changed in the project-root files." >&2; exit 1; }
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
W=$(mktemp -d /tmp/deploy-chat102r6i.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
if [ "$sm" != "$SERVER_MD5" ] || [ "$am" != "$APP_MD5" ] || [ "$im" != "$INDEX_MD5" ]; then
  die "replace refused: root server.md5 $sm app.md5 $am index.md5 $im is not the post-chat104+chat103h root (server $SERVER_MD5 app $APP_MD5 index $INDEX_MD5)."
fi
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c102r6i.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c102r6h.js" "$P/server_block_c102r6i.js" || die "patch_c102r6i failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
grep -q 'app.js?v=chat102r6i' "$S/index.html" || die "index cache tag was not bumped"
grep -q 'Yahoo Finance, delayed' "$S/app.js" || die "app.js futures source line was not updated"
python3 - "$SERVER" "$S/server.js" "$PREFIX_SHA" << 'PY' || die "bytes before the scrub block changed"
import hashlib, pathlib, sys
old = pathlib.Path(sys.argv[1]).read_bytes()
new = pathlib.Path(sys.argv[2]).read_bytes()
expect = sys.argv[3]
marker = b"// chat102r6c last-write scrub."
io, inn = old.find(marker), new.rfind(marker)
if io < 0 or inn < 0:
    sys.exit("marker missing")
if old[:io] != new[:inn]:
    sys.exit("prefix mismatch")
got = hashlib.sha256(old[:io]).hexdigest()
if got != expect:
    sys.exit("prefix sha256 " + got + " is not " + expect)
if not new.rstrip().endswith(b"})();"):
    sys.exit("scrub block is not last")
print("prefix sha256", got)
print("prefix bytes", io)
print("scrub block is last")
PY
say "scratch build ok. CPI and every byte before the scrub block are unchanged. Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch app.js sha256 $(sha256of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
echo "scratch index.html sha256 $(sha256of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat102r6i"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"
done
cp "$S/server.js" "$SERVER.new-chat102r6i" && cp "$S/app.js" "$APP.new-chat102r6i" && cp "$S/index.html" "$INDEX.new-chat102r6i" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat102r6i" "$SERVER" && mv -f "$APP.new-chat102r6i" "$APP" && mv -f "$INDEX.new-chat102r6i" "$INDEX" || { echo "[deploy-chat102r6i] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat102r6i] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: project-root server.js, app.js and index.html updated. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
