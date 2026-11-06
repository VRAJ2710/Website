#!/usr/bin/env bash
# deploy-chat102r3: public /terminal/ on the project-root chat101h files,
# or a replacement of the first chat102 revision when that root trio matches.
# Does NOT start the server, npm, git, or republish. Does not change EXPECT_TAG.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit 5531239 already contains these exact blobs.
# Do not point this at the commit that only changes deploy.sh, and do not
# read server_block/patch/app_block from the directory next to this script.
PAYLOAD_COMMIT=553123957c18c39f2294139267a27a1e2ac46195
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat102"

# Fresh base: audited chat101h. Replacement base: first chat102 (d10d6b9), whose
# app.js hash is unchanged by later server/index corrections.
LIVE_SERVER_MD5=6077bef9728ffe5b26d8d6fcb887294b
LIVE_APP_MD5=6c8ddd1be4db078df1de146163f99b11
LIVE_APP_SHA256=80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989
LIVE_INDEX_MD5=e5ab1af080974da456e086a1835d1e7b
NEW_APP_MD5=b84058f6da16ad022640b06c9cdda72d
NEW_APP_SHA256=b5dcd5fca7514f1d09a29d4e5c67c7a1c2d64d54bf92969cadf7244dd9073440
PREV_SERVER_TAIL_SHA256=7d229c3f63a61d31c43ed29c71a7a5bcc0627f9d4818e6bcc35556582dfcac61
# Full-file md5s of the successful chat102r2 preview root. App md5 is unchanged.
PREV_SERVER_MD5=e767bbae93a0db1c4ebf9d7dd3ccde70
PREV_INDEX_MD5=b3e02b0c6e403133843a96adf45d219c
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.'
MANIFEST=(
  "patch_c102.py 52d44b7c3c4a0f800fc3f7d5e1198d1f5c873e072e6ea740c3a446f18f87712b"
  "server_block_c102.js c8518e4cb15589c412a63f95b14ff47171014db6994d26803a4a3120d13425f6"
  "app_block_c102.js dbed6c1ac0ca8181e44aa92ac3528cf9aa137b7a60f31d583e3efcef09c0a206"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102] $*"; }
die(){ echo "[deploy-chat102] ABORT: $*" >&2; echo "[deploy-chat102] Nothing was changed in the project-root files." >&2; exit 1; }
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
as=$(sha256of "$APP")
say "root md5: server $sm | app $am | index $im"
say "root app.js sha256 $as"

MODE=""
if [ "$sm" = "$LIVE_SERVER_MD5" ] && [ "$am" = "$LIVE_APP_MD5" ] && [ "$as" = "$LIVE_APP_SHA256" ] && [ "$im" = "$LIVE_INDEX_MD5" ]; then MODE=fresh
elif [ "$am" = "$NEW_APP_MD5" ] && [ "$as" = "$NEW_APP_SHA256" ]; then MODE=replace
else die "root app.js md5 $am matches neither chat101h $LIVE_APP_MD5 nor first chat102 $NEW_APP_MD5. Same app md5 as first chat102 means server.js/index.html may still be updated; a different app md5 is not this revision."; fi
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "project-root server.js line 1 is not the maintenance=false line"
say "mode: $MODE"

W=$(mktemp -d /tmp/deploy-chat102.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/* && die "a patch file mentions DDL"
grep -q '/api/gold-desk' "$P"/* && die "a patch file calls /api/gold-desk"
say "DDL grep: none. gold-desk: not called"

cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
cp "$S/server.js" "$S/server.js.base"; cp "$S/app.js" "$S/app.js.base"; cp "$S/index.html" "$S/index.html.base"
if [ "$MODE" = "fresh" ]; then
  python3 "$P/patch_c102.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c102.js" "$P/app_block_c102.js" || die "patch_c102 failed (project-root files untouched)"
  python3 - "$S" "$P/server_block_c102.js" "$P/app_block_c102.js" << 'PY' || die "scratch is not the guarded fresh edit"
import pathlib, sys
s, sb, ab = sys.argv[1:]
def rd(p): return pathlib.Path(p).read_text(encoding="utf-8")
old_s, new_s = rd(s+"/server.js.base"), rd(s+"/server.js")
old_a, new_a = rd(s+"/app.js.base"), rd(s+"/app.js")
old_i, new_i = rd(s+"/index.html.base"), rd(s+"/index.html")
blk, appb = rd(sb).strip("\n") + "\n", rd(ab).strip("\n") + "\n"
if not new_s.startswith(old_s.rstrip("\n") + "\n"):
    sys.exit("server.js lost its chat101h prefix")
if new_s[len(old_s.rstrip("\n"))+1:] != blk:
    sys.exit("server.js tail is not the chat102 block")
if old_i.count('/app.js?v=chat101h"') != 1 or new_i != old_i.replace('/app.js?v=chat101h"', '/app.js?v=chat102"', 1):
    sys.exit("index.html is not the one cache-tag swap")
if "c102Path === \"/terminal\"" not in new_a or "chat102: keep /terminal/" not in new_a:
    sys.exit("app.js is missing the terminal guard")
if new_a.count('["gold","Gold"]') != old_a.count('["gold","Gold"]'):
    sys.exit("Gold nav entries changed")
if new_s.split("\n", 1)[0] != old_s.split("\n", 1)[0]:
    sys.exit("line 1 changed")
print("exact prefix preserved")
PY
else
  say "preview chat102r2 full-file md5 was server $PREV_SERVER_MD5 index $PREV_INDEX_MD5"
  say "this root full-file md5 is server $sm index $im"
  if [ "$sm" != "$PREV_SERVER_MD5" ] || [ "$im" != "$PREV_INDEX_MD5" ]; then
    die "replace refused: root server.md5 $sm index.md5 $im is not the chat102r2 root (server $PREV_SERVER_MD5 index $PREV_INDEX_MD5). App md5 $NEW_APP_MD5 only identifies the app patch. Inspect server.js and index.html before apply."
  fi
  python3 - "$S" "$P/server_block_c102.js" "$MARKER" "$PREV_SERVER_TAIL_SHA256" << 'PY' || die "replacement of the first chat102 revision was refused (project-root files untouched)"
import hashlib, pathlib, sys
s, block_path, marker, prev = sys.argv[1:]
root = pathlib.Path(s)
old = (root/"server.js.base").read_bytes()
block = pathlib.Path(block_path).read_bytes()
text = old.decode("utf-8")
if text.count(marker) != 1:
    sys.exit("project-root server.js does not contain exactly one chat102 block")
tail = text[text.find(marker):].encode("utf-8")
got = hashlib.sha256(tail).hexdigest()
new_tail = block.decode("utf-8").strip("\n") + "\n"
new_hash = hashlib.sha256(new_tail.encode("utf-8")).hexdigest()
if got == new_hash:
    sys.exit("already chat102r3")
if got != prev:
    sys.exit("server.js tail sha256 " + got + " is not the first chat102 block " + prev)
idx = (root/"index.html.base").read_text(encoding="utf-8")
if idx.count('/app.js?v=chat102"') != 1 or '/app.js?v=chat101h"' in idx:
    sys.exit("project-root index.html is not the first chat102 cache tag")
prefix = text[:text.find(marker)]
(root/"server.js").write_text(prefix + new_tail, encoding="utf-8")
print("replaced first chat102 server tail")
PY
fi
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch line 1 changed"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
grep -q '/app.js?v=chat102"' "$S/index.html" || die "app cache token chat102 missing"
grep -q "api/c102/terminal" "$S/server.js" || die "terminal route missing"
if [ "$MODE" = "replace" ]; then
  cmp -s "$S/app.js" "$S/app.js.base" || die "replacement changed app.js; the first-revision app hash must stay"
  cmp -s "$S/index.html" "$S/index.html.base" || die "replacement changed index.html; this revision does not alter the cache tag"
fi
say "scratch build ok ($MODE). Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch app.js sha256 $(sha256of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
echo "scratch index.html sha256 $(sha256of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi

TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat102r3"
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.$SUFF"; done
cp "$S/server.js" "$SERVER.new-chat102r3" && cp "$S/app.js" "$APP.new-chat102r3" && cp "$S/index.html" "$INDEX.new-chat102r3" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat102r3" "$SERVER" && mv -f "$APP.new-chat102r3" "$APP" && mv -f "$INDEX.new-chat102r3" "$INDEX" || { echo "[deploy-chat102] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat102] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat102] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
[ "$(md5of "$APP")" = "$NEW_APP_MD5" ] || { echo "[deploy-chat102] ERROR: app.js md5 changed unexpectedly; $RB" >&2; exit 1; }
say "DONE ($MODE): project-root server.js, app.js and index.html updated. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
