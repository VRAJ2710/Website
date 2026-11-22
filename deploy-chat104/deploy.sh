#!/usr/bin/env bash
# deploy-chat104: rename the reader-facing Learn section to Dispatch Academy.
# One installer. Does NOT start the server, npm, git, or republish.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit is the commit that already contains this patch.
# Do not point this at the commit that only changes deploy.sh.
PAYLOAD_COMMIT=f3124f6e3924b40e827c5595f7da27f596e70890
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat104"
SERVER_MD5=9a4070ba75c5900cfa4b34ac5b7899e1
APP_MD5=c56a1cc883539489e4e33ea30e191d77
INDEX_MD5=c21e347055d307db38116dd304ac30dc
MANIFEST=(
  "patch_c104.py 824cd42d9010c483239d11ff8be09c45e8b1c40f0167e7325d7619832d1dd68b"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat104] $*"; }
die(){ echo "[deploy-chat104] ABORT: $*" >&2; echo "[deploy-chat104] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
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
W=$(mktemp -d /tmp/deploy-chat104.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c104.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c104 failed (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
grep -q 'app.js?v=chat104' "$S/index.html" || die "index cache tag was not bumped"
grep -q 'app.js?v=chat103d' "$S/index.html" && die "old chat103d cache tag still present"
grep -q 'Dispatch Academy | Beginner Guides, Glossary & Frameworks | The Dispatch Market' "$S/server.js" || die "learn title was not renamed"
grep -q '/learn/' "$S/server.js" || die "learn path missing from server.js"
python3 - "$SERVER" "$S/server.js" << 'PY' || die "CPI block or last-write scrub changed"
import pathlib, sys
old = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
new = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
cpi = "// chat103 cpi day"
scrub = "// chat102r6c last-write scrub."
io, inn = old.find(cpi), new.find(cpi)
if io < 0 or inn < 0:
    sys.exit("CPI marker missing")
if old[io:] != new[inn:]:
    sys.exit("bytes from the CPI block through the scrub changed")
if scrub not in new[inn:]:
    sys.exit("scrub block is not after the CPI block")
if not new.rstrip().endswith("})();"):
    sys.exit("scrub block is not last")
print("CPI and scrub bytes", len(old) - io)
print("scrub block is last")
PY
say "scratch build ok. CPI block and last-write scrub are unchanged. Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch app.js sha256 $(sha256of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
echo "scratch index.html sha256 $(sha256of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat104"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"
done
cp "$S/server.js" "$SERVER.new-chat104" && cp "$S/app.js" "$APP.new-chat104" && cp "$S/index.html" "$INDEX.new-chat104" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat104" "$SERVER" && mv -f "$APP.new-chat104" "$APP" && mv -f "$INDEX.new-chat104" "$INDEX" || { echo "[deploy-chat104] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat104] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: project-root server.js, app.js and index.html updated. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
