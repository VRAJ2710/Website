#!/usr/bin/env bash
# deploy-chat102r6f: wording pass that leaves source machine ids untouched.
# Server only. Does NOT start the server, npm, git, or republish.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit ac838da already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=ac838da794c69114468348d6fa1e1adc3bd3d768
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102r6f"
SERVER_MD5=d0a74a6c26e3a8dd7dcbf8ad0939f926
APP_MD5=93644cb45fc3884e7068bf9a902d73e3
INDEX_MD5=338615e7ece511104855785b67e9c10a
MANIFEST=(
  "patch_c102r6f.py d8a132d95d6dc88cf184b3f1a2c0e7e16f7d3669b9a7251ed37356caff06c5d6"
  "server_block_c102r6d.js 21859ae19cb9119684fe5294f59ae6b47c24e5c9cf5b55746b1e304c38700d90"
  "server_block_c102r6f.js 7702efaf7dc1dc4abb29335f9d2a5c8e46d341f5af6b7f7770e69195a61773fd"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102r6f] $*"; }
die(){ echo "[deploy-chat102r6f] ABORT: $*" >&2; echo "[deploy-chat102r6f] Nothing was changed in the project-root files." >&2; exit 1; }
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
W=$(mktemp -d /tmp/deploy-chat102r6f.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
if [ "$sm" != "$SERVER_MD5" ] || [ "$am" != "$APP_MD5" ] || [ "$im" != "$INDEX_MD5" ]; then
  die "replace refused: root server.md5 $sm app.md5 $am index.md5 $im is not the current dev root (server $SERVER_MD5 app $APP_MD5 index $INDEX_MD5)."
fi
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c102r6f.py" "$S/server.js" "$P/server_block_c102r6d.js" "$P/server_block_c102r6f.js" || die "patch_c102r6f failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
cmp -s "$S/app.js" "$APP" || die "app.js changed; this revision does not edit it"
cmp -s "$S/index.html" "$INDEX" || die "index.html changed; this revision does not edit it"
python3 - "$SERVER" "$S/server.js" << 'PY' || die "bytes before the scrub block changed"
import hashlib, pathlib, sys
old = pathlib.Path(sys.argv[1]).read_bytes()
new = pathlib.Path(sys.argv[2]).read_bytes()
marker = b"// chat102r6c last-write scrub."
io, inn = old.find(marker), new.rfind(marker)
if io < 0 or inn < 0:
    sys.exit("marker missing")
if old[:io] != new[:inn]:
    sys.exit("prefix mismatch")
if not new.rstrip().endswith(b"})();"):
    sys.exit("scrub block is not last")
print("prefix sha256", hashlib.sha256(old[:io]).hexdigest())
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
SUFF="bak-chat102r6f"
cp -p "$SERVER" "$SERVER.$TS.$SUFF" || die "backup failed for server.js"
[ "$(md5of "$SERVER.$TS.$SUFF")" = "$sm" ] || die "backup verify failed for server.js"
say "backup: $SERVER.$TS.$SUFF"
cp "$S/server.js" "$SERVER.new-chat102r6f" || die "staging copy failed (project-root files untouched)"
mv -f "$SERVER.new-chat102r6f" "$SERVER" || { echo "[deploy-chat102r6f] ERROR during install; restore server.js from $SERVER.$TS.$SUFF and DO NOT republish" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-chat102r6f] ERROR: node --check failed after install; restore server.js from $SERVER.$TS.$SUFF" >&2; exit 1; }
[ "$(md5of "$APP")" = "$APP_MD5" ] && [ "$(md5of "$INDEX")" = "$INDEX_MD5" ] || { echo "[deploy-chat102r6f] ERROR: app.js or index.html changed; restore server.js from $SERVER.$TS.$SUFF" >&2; exit 1; }
say "DONE: project-root server.js updated. app.js and index.html were not written. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore server.js from $SERVER.$TS.$SUFF."
rm -rf "$W"
