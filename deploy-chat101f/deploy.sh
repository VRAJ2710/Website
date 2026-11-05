#!/usr/bin/env bash
# deploy-chat101f: market quotes first, on top of the chat101e build (server 7a959bc6, app 79bef7ba, index 141f4133;
#   c93.css 9d6a86a6). Line 1 stays false.
#  - server.js: US 10-year and 10-year real (TIPS) yields from a free delayed market quote (Tradeweb via CNBC), Cboe index and
#    then the official FRED figure as fallbacks; official daily figure shown as a secondary line; WTI shows NYMEX futures first
#    with the EIA official spot underneath; public pages re-read prices every 5 minutes; short caches no longer serve a reading
#    far past its TTL; gold change reads "since yesterday's close (23:57 UK, 4 Nov)"; new GET /api/c101f/rates.
#  - app.js: member Gold Dashboard cards use the same renderer; Rates session/notes wording.
#  - index.html: cache tag app.js?v=chat101f.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, menus, data, DB schema (no DDL), c93.css, the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/e5c2dec9951d15045ee88146f4c179acd68a92f8/deploy-chat101f"

LIVE_SERVER_MD5=7a959bc6c9430d0364e8ef65d7934c09   # chat101e base (server unchanged since chat101d)
LIVE_SERVER_SHA256=fb6923fd1c4126deddc552a5ca6777894259bd5fbbbc33e8e01a505a04bba3e6
LIVE_APP_MD5=79bef7ba3d98e33f87379e955ffaa68a      # chat101e
LIVE_INDEX_MD5=141f4133329d9e2899d4cd0181819934    # chat101e
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=6f4266e5439b000710b218785b1007bc
NEW_APP_MD5=a4d35033d47d8e23a00d1f00384b1a83
NEW_INDEX_MD5=5749d2ae43918b36d6071b046e7f4c78
NEW_SERVER_SHA256=2507caad03ec81b57436de8c4a7610cdcf2c82a5e7d613d95f203f079c18a57e
NEW_APP_SHA256=e0fb8e17c279be3e53f62bff67a1fd17f31df94541f6e383c8545ac62296d458
NEW_INDEX_SHA256=801bf3baae902f07a86a1967cdc414c4ec57f901ae148d9ff8c2b49ffc30b3bb
PHOTO_REL="assets/founder.webp"                     # chat100e photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101f.py aee746c52fc4dac8c5e67442240fe5d4f38124677e3124dbf77d630abaa3ffcb"
  "srv_block_c101f.js 7e0dc94cc8c27f9dc6d5eb2f3d3fa313577c37b911ce1ca1effa4af497e10884"
  "rend_mid.js 08accac81e633a4e30170f99f80a91770f0672b9f5675a4df5bfb7a8e211231b"
  "rend_brief.js c4fe79b27aa3fa1a3b7d999531c8e28ed0b907fca8927a31dc88c32100edf39d"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101f] $*"; }
die(){ echo "[deploy-chat101f] ABORT: $*" >&2; echo "[deploy-chat101f] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum base64 curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

# ---- 1. locate the live files ----
find_one(){ local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' -not -path '*/deploy-final*' -not -path '*/deploy-reopen*' -not -path '*/deploy-chat1*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"; m=$(md5of "$p")
    { [ "$m" = "$want" ] || { [ -n "$alt" ] && [ "$m" = "$alt" ]; }; } && { echo "$p"; return 0; }
  done; echo "$first"; }
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5" "$NEW_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5" "$NEW_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5" "$NEW_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"; PHOTO="$SDIR/$PHOTO_REL"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css   = $CSS (must stay chat93)"; say "photo     = $PHOTO"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"


# ---- 2. refuse a second run; check the base ----
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat101f >/dev/null 2>&1 || ls "$APP".*.bak-chat101f >/dev/null 2>&1 || ls "$INDEX".*.bak-chat101f >/dev/null 2>&1; then
  say "REFUSE: deploy-chat101f is already applied (or a .bak-chat101f backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] && [ "$(sha256of "$SERVER")" = "$LIVE_SERVER_SHA256" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat101e)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat101e)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat101e)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat101e build, photo ok: ok"

# ---- 3. fetch + verify the patch files (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat101f.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done

# ---- 4. DDL grep on everything that ends up in the live files ----
grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep (create/alter/drop table, create/drop index, truncate): none"

# ---- 5. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c101f.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/srv_block_c101f.js" "$P/rend_mid.js" "$P/rend_brief.js" || die "patch_c101f failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
grep -q '/app.js?v=chat101f"' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101f, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$S/app.js" "$S/index.html" && die "scratch build contains 'Vraj Patel, London'"
for f in srv_block_c101f.js rend_mid.js rend_brief.js; do grep -qE 'GC=F|CL=F|\^TNX' "$P/$f" && die "$f must not contain a raw ticker"; done
sed -n '/chat101e: market cards/,$p' "$S/app.js" | grep -qF 'GC=F' && die "the chat101e/chat101f app block must not contain GC=F"
grep -qF "chat101f: market quotes first" "$S/server.js" && grep -qF '/api/c101f/rates' "$S/server.js" || die "chat101f server block missing"
grep -qF "chat101e: market cards" "$S/app.js" && grep -qF "chat101f: market quotes first" "$S/app.js" && grep -qF "chat101d: app views" "$S/app.js" || die "chat101d/chat101e/chat101f app blocks missing"
grep -qF 'Edited by Vraj Patel' "$S/server.js" && grep -qF 'Not investment advice. Capital at risk.' "$S/server.js" || die "byline or disclaimer missing"
grep -qF 'aria-label="Close menu"' "$S/app.js" || die "menu sheet close button missing"
say "wording guards (no 'Vraj Patel, London', no raw GC=F/CL=F/^TNX in new blocks, chat101f server block present, byline and disclaimer kept, Close X present): ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install (server.js, app.js, index.html) ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101f" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101f")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101f"; done
cp "$S/server.js" "$SERVER.new-chat101f" && cp "$S/app.js" "$APP.new-chat101f" && cp "$S/index.html" "$INDEX.new-chat101f" || die "staging copy failed (live files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.bak-chat101f copies and DO NOT republish"
mv -f "$SERVER.new-chat101f" "$SERVER" && mv -f "$APP.new-chat101f" "$APP" && mv -f "$INDEX.new-chat101f" "$INDEX" || { echo "[deploy-chat101f] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101f] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101f] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore server.js, app.js and index.html from their .$TS.bak-chat101f copies."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101f] ERROR: final files differ; $RB" >&2; exit 1; fi
