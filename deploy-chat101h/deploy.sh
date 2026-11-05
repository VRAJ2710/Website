#!/usr/bin/env bash
# deploy-chat101h: publish three sourced Research articles on the LIVE chat101g build
#   (server 6f4266e5, app 0b4c442a, index 4b7ffe2b; c93.css 9d6a86a6). Line 1 stays false.
#  - server.js: public article pages under /research/<slug>/ and a listing on the existing
#    Research hub. The Capital Sustainability Monitor, Check and plan, Also from the desk,
#    filings, filing-changes and research-desk routes are not removed.
#  - app.js: the same three notes are linked at the top of the signed-in Research desk.
#  - index.html: cache tag app.js?v=chat101h.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema
# (no DDL), c93.css, the service worker, or the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/c4b804e8c722b258887c165f0fb142bd0a1af4e9/deploy-chat101h"

LIVE_SERVER_MD5=6f4266e5439b000710b218785b1007bc
LIVE_SERVER_SHA256=2507caad03ec81b57436de8c4a7610cdcf2c82a5e7d613d95f203f079c18a57e
LIVE_APP_MD5=0b4c442a055584920d9539fb50c9a7f1
LIVE_APP_SHA256=67e260e4146cf63d847efa382a6c925416393af1ba1ba584e049eac9554a7d5c
LIVE_INDEX_MD5=4b7ffe2b91d4bd3c8438cf62d81df5e9
LIVE_INDEX_SHA256=0a5f2834eaf5c9147106d63baf364e8759ed6adda8a2af17a6437e5b1ccfc22d
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550
NEW_APP_MD5=6c8ddd1be4db078df1de146163f99b11
NEW_APP_SHA256=80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989
PHOTO_REL="assets/founder.webp"
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101h.py aa506110ccf391414b7672bc0dedba5538013857b03832c6a66ab51e14035522"
  "server_block_c101h.js f8d60e6d7814374ba60c174ac07b179fa7808da0e5937c204838ceaf2a043db6"
  "app_block_c101h.js d3ea0f5453b9dfa38d93da83de4395c82d5f0bb5225c008532e51c7fe651805b"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101h] $*"; }
die(){ echo "[deploy-chat101h] ABORT: $*" >&2; echo "[deploy-chat101h] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum base64 curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

find_one(){ local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' -not -path '*/deploy-final*' -not -path '*/deploy-reopen*' -not -path '*/deploy-chat1*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"; m=$(md5of "$p")
    { [ "$m" = "$want" ] || { [ -n "$alt" ] && [ "$m" = "$alt" ]; }; } && { echo "$p"; return 0; }
  done; echo "$first"; }
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5" "$NEW_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"; PHOTO="$SDIR/$PHOTO_REL"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css   = $CSS (must stay chat93)"; say "photo     = $PHOTO"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"

if [ "$am" = "$NEW_APP_MD5" ] || ls "$SERVER".*.bak-chat101h >/dev/null 2>&1 || ls "$APP".*.bak-chat101h >/dev/null 2>&1 || ls "$INDEX".*.bak-chat101h >/dev/null 2>&1 || grep -q "chat101h: three sourced research articles" "$SERVER" 2>/dev/null || grep -q "chat101h: sourced research articles" "$APP" 2>/dev/null; then
  say "REFUSE: deploy-chat101h is already applied (or a .bak-chat101h backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] && [ "$(sha256of "$SERVER")" = "$LIVE_SERVER_SHA256" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat101g)"
[ "$am" = "$LIVE_APP_MD5" ] && [ "$(sha256of "$APP")" = "$LIVE_APP_SHA256" ] || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat101g)"
[ "$im" = "$LIVE_INDEX_MD5" ] && [ "$(sha256of "$INDEX")" = "$LIVE_INDEX_SHA256" ] || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat101g)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat101g build, photo ok: ok"

W=$(mktemp -d /tmp/deploy-chat101h.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done

grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep (create/alter/drop table, create/drop index, truncate): none"

cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
cp "$S/server.js" "$S/server.js.base"; cp "$S/app.js" "$S/app.js.base"; cp "$S/index.html" "$S/index.html.base"
python3 "$P/patch_c101h.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c101h.js" "$P/app_block_c101h.js" || die "patch_c101h failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
python3 - "$S" "$P/server_block_c101h.js" "$P/app_block_c101h.js" << 'PY' || die "scratch is not an exact append / token swap"
import pathlib, sys
s, sb, ab = sys.argv[1:]
def rd(p): return pathlib.Path(p).read_text(encoding="utf-8")
old_s, new_s = rd(s+"/server.js.base"), rd(s+"/server.js")
old_a, new_a = rd(s+"/app.js.base"), rd(s+"/app.js")
old_i, new_i = rd(s+"/index.html.base"), rd(s+"/index.html")
blk, appb = rd(sb), rd(ab)
exp_s = old_s.rstrip("\n") + "\n" + blk.strip("\n") + "\n"
exp_a = old_a.rstrip("\n") + "\n" + appb.strip("\n") + "\n"
exp_i = old_i.replace('/app.js?v=chat101g"', '/app.js?v=chat101h"', 1)
if new_s != exp_s: sys.exit("server.js is not the live file plus the block")
if new_a != exp_a: sys.exit("app.js is not the live file plus the block")
if old_i.count('/app.js?v=chat101g"') != 1 or new_i != exp_i: sys.exit("index.html is not the one cache-tag swap")
if new_s.split("\n", 1)[0] != old_s.split("\n", 1)[0]: sys.exit("line 1 changed")
print("exact prefix preserved")
PY
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch line 1 changed"
grep -q '/app.js?v=chat101h"' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101h, css chat93) missing"
grep -q "chat101h: three sourced research articles" "$S/server.js" && grep -q "Capital Sustainability Monitor" "$S/server.js" && grep -q "chat101f: market quotes first" "$S/server.js" || die "article block or existing research marker missing"
grep -q "chat101h: sourced research articles" "$S/app.js" && grep -q "chat101g: phone Account drawer" "$S/app.js" || die "app block or chat101g drawer missing"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$P"/* && die "patch contains 'Vraj Patel, London'"
grep -qF 'GC=F' "$P/server_block_c101h.js" "$P/app_block_c101h.js" && die "a new block contains GC=F"
grep -qF 'Not investment advice. Capital at risk.' "$S/server.js" && grep -qF 'Edited by Vraj Patel' "$S/server.js" || die "byline or disclaimer missing"
say "scratch build: exact append, app hash pinned, line 1 false, existing research text kept"
NS=$(sha256of "$S/server.js"); NI=$(sha256of "$S/index.html")
echo "scratch server.js sha256 $NS"
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch index.html sha256 $NI"
echo "scratch index.html md5 $(md5of "$S/index.html")"
echo "scratch app.js sha256 $NEW_APP_SHA256"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101h" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101h")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101h"; done
cp "$S/server.js" "$SERVER.new-chat101h" && cp "$S/app.js" "$APP.new-chat101h" && cp "$S/index.html" "$INDEX.new-chat101h" || die "staging copy failed (live files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.bak-chat101h copies and DO NOT republish"
mv -f "$SERVER.new-chat101h" "$SERVER" && mv -f "$APP.new-chat101h" "$APP" && mv -f "$INDEX.new-chat101h" "$INDEX" || { echo "[deploy-chat101h] ERROR during install; $RB" >&2; exit 1; }

node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101h] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101h] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "server.js  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "index.html sha256 $(sha256of "$INDEX")"
echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fa" = "$NEW_APP_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ] && grep -q "chat101h: three sourced research articles" "$SERVER" && grep -q '/app.js?v=chat101h"' "$INDEX"; then
  say "DONE: app.js matches the tested build. server.js is the live file plus the pinned block. index.html is the one cache-tag swap. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when the coordinator does that)."
  say "To undo: restore server.js, app.js and index.html from their .$TS.bak-chat101h copies."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101h] ERROR: final files differ; $RB" >&2; exit 1; fi
