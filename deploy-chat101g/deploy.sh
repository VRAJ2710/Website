#!/usr/bin/env bash
# deploy-chat101g: phone Account drawer + tap-through fixes, on top of the LIVE chat101f build
#   (server 6f4266e5, app a4d35033, index 5749d2ae; c93.css 9d6a86a6). Line 1 stays false.
#  - app.js: the phone "☰" Account menu (premium/admin) was positioned off the left edge of the screen with dark-on-dark text;
#    it is now a labelled "Account" button that opens a full-height left drawer (85% wide, max 360px) with readable text, a close X,
#    a backdrop that closes it, Esc, focus trap and scroll lock. Same items as before (Admin console, Guest preview, Manage billing,
#    Settings, Sign out); nothing removed. Signed-in free members get Settings + Sign out instead of "Sign in"/"Create free account".
#    Contrast fixes: /paper/ lock card, /dashboard/ desk letter, /learn/ locked badges, /heatmap/ tiles + legend, /sectors/ tiles,
#    "/100" scores (/geo/, /signals/, /dashboard/, /lab/), /documents/ "Analyse with AI", chat Send. Esc closes the Ask chat panel.
#    Empty context menu hidden on /settings/. Heatmap tile source text no longer spills into neighbouring tiles.
#  - index.html: cache tag app.js?v=chat101g.
#  - server.js: READ ONLY (checked, never written).
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, routes, menus, data, DB schema (no DDL), c93.css, the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/2736bab62d1531f30e24f2f1655c87beead97a28/deploy-chat101g"

LIVE_SERVER_MD5=6f4266e5439b000710b218785b1007bc   # chat101f, maintenance OFF; unchanged by chat101g
LIVE_SERVER_SHA256=2507caad03ec81b57436de8c4a7610cdcf2c82a5e7d613d95f203f079c18a57e
LIVE_APP_MD5=a4d35033d47d8e23a00d1f00384b1a83      # chat101f
LIVE_INDEX_MD5=5749d2ae43918b36d6071b046e7f4c78    # chat101f
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_APP_MD5=0b4c442a055584920d9539fb50c9a7f1
NEW_INDEX_MD5=4b7ffe2b91d4bd3c8438cf62d81df5e9
NEW_APP_SHA256=67e260e4146cf63d847efa382a6c925416393af1ba1ba584e049eac9554a7d5c
NEW_INDEX_SHA256=0a5f2834eaf5c9147106d63baf364e8759ed6adda8a2af17a6437e5b1ccfc22d
PHOTO_REL="assets/founder.webp"                     # chat100e photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101g.py 999e78353c3aea4e65886be6f8c044782ff24125f2518c9150e4afb3a4793bf0"
  "app_block_c101g.js 5501dd2d04aea5fd05daf1b74187c4479e870f0a8a4a426d89911cfff4738bd4"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101g] $*"; }
die(){ echo "[deploy-chat101g] ABORT: $*" >&2; echo "[deploy-chat101g] Nothing was changed in the live files." >&2; exit 1; }
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
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5" "$NEW_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5" "$NEW_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"; PHOTO="$SDIR/$PHOTO_REL"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css   = $CSS (must stay chat93)"; say "photo     = $PHOTO"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"


# ---- 2. refuse a second run; check the base ----
if [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$APP".*.bak-chat101g >/dev/null 2>&1 || ls "$INDEX".*.bak-chat101g >/dev/null 2>&1; then
  say "REFUSE: deploy-chat101g is already applied (or a .bak-chat101g backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] && [ "$(sha256of "$SERVER")" = "$LIVE_SERVER_SHA256" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat101f)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat101f)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat101f)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat101f build, photo ok: ok"

# ---- 3. fetch + verify the patch files (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat101g.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c101g.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/app_block_c101g.js" || die "patch_c101g failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$LIVE_SERVER_MD5" ] || die "scratch server.js changed; chat101g must not touch it"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
grep -q '/app.js?v=chat101g"' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101g, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$S/app.js" "$S/index.html" && die "scratch build contains 'Vraj Patel, London'"
grep -qF 'GC=F' "$P/app_block_c101g.js" && die "the new app block must not contain GC=F"
sed -n '/chat101g: phone Account drawer/,$p' "$S/app.js" | grep -qF 'GC=F' && die "the installed chat101g block must not contain GC=F"
grep -qF "chat101g: phone Account drawer" "$S/app.js" && grep -qF "chat101e: market cards" "$S/app.js" && grep -qF "chat101d: app views" "$S/app.js" && grep -qF "chat101f: market quotes first" "$S/server.js" || die "chat101d/e/f/g blocks missing"
grep -qF 'Edited by Vraj Patel' "$S/server.js" && grep -qF 'Not investment advice. Capital at risk.' "$S/server.js" || die "byline or disclaimer missing"
grep -qF 'aria-label="Close menu"' "$S/app.js" || die "menu sheet close button missing"
grep -qF 'c101g-x' "$S/app.js" && grep -qF '/__auth/logout' "$S/app.js" && grep -qF 'Admin console' "$S/app.js" && grep -qF 'Manage billing' "$S/app.js" || die "Account drawer close X or menu items missing"
say "wording guards (no 'Vraj Patel, London', no raw GC=F, byline and disclaimer kept, Close X present): ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install (app.js + index.html only) ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101g" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101g")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101g"; done
cp "$S/app.js" "$APP.new-chat101g" && cp "$S/index.html" "$INDEX.new-chat101g" || die "staging copy failed (live files untouched)"
RB="restore app.js and index.html from their .$TS.bak-chat101g copies and DO NOT republish"
mv -f "$APP.new-chat101g" "$APP" && mv -f "$INDEX.new-chat101g" "$INDEX" || { echo "[deploy-chat101g] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101g] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101g] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$LIVE_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore app.js and index.html from their .$TS.bak-chat101g copies."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101g] ERROR: final files differ; $RB" >&2; exit 1; fi
