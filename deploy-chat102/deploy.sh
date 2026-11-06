#!/usr/bin/env bash
# deploy-chat102: public /terminal/ on the LIVE chat101h build.
# Does NOT start the server, npm, git, or republish. Does not change EXPECT_TAG.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/d9a2d72cd7da97fa073d57f4625ef1d74695da3c/deploy-chat102"

# Audited live chat101h files. A mismatch aborts before anything is written.
LIVE_SERVER_MD5=6077bef9728ffe5b26d8d6fcb887294b
LIVE_APP_MD5=6c8ddd1be4db078df1de146163f99b11
LIVE_APP_SHA256=80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989
LIVE_INDEX_MD5=e5ab1af080974da456e086a1835d1e7b
NEW_APP_MD5=b84058f6da16ad022640b06c9cdda72d
NEW_APP_SHA256=b5dcd5fca7514f1d09a29d4e5c67c7a1c2d64d54bf92969cadf7244dd9073440
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c102.py 52d44b7c3c4a0f800fc3f7d5e1198d1f5c873e072e6ea740c3a446f18f87712b"
  "server_block_c102.js 7d229c3f63a61d31c43ed29c71a7a5bcc0627f9d4818e6bcc35556582dfcac61"
  "app_block_c102.js dbed6c1ac0ca8181e44aa92ac3528cf9aa137b7a60f31d583e3efcef09c0a206"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat102] $*"; }
die(){ echo "[deploy-chat102] ABORT: $*" >&2; echo "[deploy-chat102] Nothing was changed in the live files. The snapshot did not match chat101h, so this run stopped." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

find_one(){ local name="$1" want="$2" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"; m=$(md5of "$p")
    [ "$m" = "$want" ] && { echo "$p"; return 0; }
  done; echo "$first"; }
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "current md5: server $sm | app $am | index $im"
say "expected chat101h md5: server $LIVE_SERVER_MD5 | app $LIVE_APP_MD5 | index $LIVE_INDEX_MD5"

if grep -q "api/c102/terminal" "$SERVER" 2>/dev/null || grep -q "chat102: keep /terminal/" "$APP" 2>/dev/null || ls "$SERVER".*.bak-chat102 >/dev/null 2>&1; then
  say "REFUSE: deploy-chat102 is already applied (or a .bak-chat102 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live chat101h $LIVE_SERVER_MD5"
[ "$am" = "$LIVE_APP_MD5" ] && [ "$(sha256of "$APP")" = "$LIVE_APP_SHA256" ] || die "app.js md5 $am != expected live chat101h $LIVE_APP_MD5"
[ "$im" = "$LIVE_INDEX_MD5" ] || die "index.html md5 $im != expected live chat101h $LIVE_INDEX_MD5"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
say "live snapshot matches chat101h: ok"

W=$(mktemp -d /tmp/deploy-chat102.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done
grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/* && die "a patch file mentions DDL"
grep -q '/api/gold-desk' "$P"/* && die "a patch file calls /api/gold-desk"
say "DDL grep: none. gold-desk: not called"

cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
cp "$S/server.js" "$S/server.js.base"; cp "$S/app.js" "$S/app.js.base"; cp "$S/index.html" "$S/index.html.base"
python3 "$P/patch_c102.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c102.js" "$P/app_block_c102.js" || die "patch_c102 failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
python3 - "$S" "$P/server_block_c102.js" "$P/app_block_c102.js" << 'PY' || die "scratch is not the guarded edit"
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
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch line 1 changed"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
grep -q '/app.js?v=chat102"' "$S/index.html" || die "app cache token was not moved to chat102"
grep -q "api/c102/terminal" "$S/server.js" || die "terminal route missing"
grep -q 'href="/dashboard/"' "$S/app.js" || grep -q 'dash' "$S/app.js" || die "dashboard route missing from app.js"
say "scratch build: chat101h prefix kept, terminal added, line 1 still maintenance off"
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch app.js sha256 $(sha256of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
echo "scratch index.html sha256 $(sha256of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat102" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat102")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat102"; done
cp "$S/server.js" "$SERVER.new-chat102" && cp "$S/app.js" "$APP.new-chat102" && cp "$S/index.html" "$INDEX.new-chat102" || die "staging copy failed (live files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.bak-chat102 copies and DO NOT republish"
mv -f "$SERVER.new-chat102" "$SERVER" && mv -f "$APP.new-chat102" "$APP" && mv -f "$INDEX.new-chat102" "$INDEX" || { echo "[deploy-chat102] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat102] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat102] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
say "DONE: chat102 is installed on the chat101h files. The server was NOT started and nothing was republished."
say "To undo: restore server.js, app.js and index.html from their .$TS.bak-chat102 copies."
rm -rf "$W"
