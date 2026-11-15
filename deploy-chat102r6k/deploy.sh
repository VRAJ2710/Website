#!/usr/bin/env bash
# deploy-chat102r6k: header fit, Dispatch Academy breadcrumb, scenario script sentence.
# Staged on the r6j dev root. Does NOT start the server, npm, git, or republish.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit 4f0c827 already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=4f0c8273b67a1bc4a9830bfc53e6241e2b05083d
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102r6k"
# Staged r6j root. Index tag stays app.js?v=chat102r6j.
SERVER_MD5=a12d3cfe022ec3990801ef05226fbaa9
APP_MD5=ac695ac6f0a166c8aa1b8a33ee52763b
INDEX_MD5=b2bcb3ce97661e1d8cc016ead643a575
PREFIX_SHA=7e54c7c211dc81b68de5de5b61c52708756b462082529f55a825d358d23cfbef
MANIFEST=(
  "patch_c102r6k.py d349df1c0f1285627c5a19031613b57419fad85bf1d70503c3c5f9bab457ffac"
  "server_block_c102r6j.js df67816167d4b678789d67bec49f336416c3219c04f93ffdbb85c756b0524c67"
  "server_block_c102r6k.js 9a725217fdbd34998c7d84cfc364ee32ed48312256b94038dd98333a4ce2473b"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102r6k] $*"; }
die(){ echo "[deploy-chat102r6k] ABORT: $*" >&2; echo "[deploy-chat102r6k] Nothing was changed in the project-root files." >&2; exit 1; }
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
W=$(mktemp -d /tmp/deploy-chat102r6k.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
if [ "$sm" != "$SERVER_MD5" ] || [ "$am" != "$APP_MD5" ] || [ "$im" != "$INDEX_MD5" ]; then
  die "replace refused: root server.md5 $sm app.md5 $am index.md5 $im is not the post-r6j root (server $SERVER_MD5 app $APP_MD5 index $INDEX_MD5)."
fi
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c102r6k.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c102r6j.js" "$P/server_block_c102r6k.js" || die "patch_c102r6k failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
cmp -s "$APP" "$S/app.js" || die "app.js changed"
cmp -s "$INDEX" "$S/index.html" || die "index.html changed"
grep -q 'app.js?v=chat102r6j' "$S/index.html" || die "index cache tag is not app.js?v=chat102r6j"
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
SUFF="bak-chat102r6k"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"
done
cp "$S/server.js" "$SERVER.new-chat102r6k" && cp "$S/app.js" "$APP.new-chat102r6k" && cp "$S/index.html" "$INDEX.new-chat102r6k" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat102r6k" "$SERVER" && mv -f "$APP.new-chat102r6k" "$APP" && mv -f "$INDEX.new-chat102r6k" "$INDEX" || { echo "[deploy-chat102r6k] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat102r6k] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: project-root server.js, app.js and index.html updated. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
