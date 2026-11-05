#!/usr/bin/env bash
# deploy-chat101e: market cards on the signed-in Gold Dashboard, on top of the LIVE chat101d build
#   (server 7a959bc6, app 5773e359, index 90055663; c93.css 9d6a86a6). Line 1 stays false.
#  - app.js: "Market context" section on the member Gold Dashboard: Gold and silver, Currencies, Rates, Energy, Crypto cards
#    (phones) / table (desktop), using the public pages' market renderer and quotes APIs; plain names, level, change, source,
#    as-of UK, "Delayed", each venue's session label; a plain note if quotes fail.
#  - index.html: cache tag app.js?v=chat101e.
#  - server.js: READ ONLY (checked, never written). app.js had no support/contact address, so no email change there.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, routes, menus, data, DB schema (no DDL), c93.css, the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/242fe9ec94b773c13e24511282af204151f8cacc/deploy-chat101e"

LIVE_SERVER_MD5=7a959bc6c9430d0364e8ef65d7934c09   # chat101d (publish a753ad06), maintenance OFF; unchanged by chat101e
LIVE_SERVER_SHA256=fb6923fd1c4126deddc552a5ca6777894259bd5fbbbc33e8e01a505a04bba3e6
LIVE_APP_MD5=5773e359eb0a88af42d0c03df2d0bebd      # chat101d
LIVE_INDEX_MD5=90055663d4c88a2690ed7770e105ee23    # chat101d
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_APP_MD5=79bef7ba3d98e33f87379e955ffaa68a
NEW_INDEX_MD5=141f4133329d9e2899d4cd0181819934
NEW_APP_SHA256=9d62d6630e28644b5b278790a543d94470d3bbf6396bf31b4198231885ce8887
NEW_INDEX_SHA256=f317ce5cad8327ebbacfe856ce0cb83bbf64b6e2181365558bff6fab65d42031
PHOTO_REL="assets/founder.webp"                     # chat100e photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101e.py 80d7e79082265020cee754e273e429d28fe7441c6c11c48e268303f76e1b0c37"
  "app_block_c101e.js 1c54894be5b9f36d5e520ec1164900683c80527deff0205b62e34ccd1e3fd534"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101e] $*"; }
die(){ echo "[deploy-chat101e] ABORT: $*" >&2; echo "[deploy-chat101e] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$APP".*.bak-chat101e >/dev/null 2>&1 || ls "$INDEX".*.bak-chat101e >/dev/null 2>&1; then
  say "REFUSE: deploy-chat101e is already applied (or a .bak-chat101e backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] && [ "$(sha256of "$SERVER")" = "$LIVE_SERVER_SHA256" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat101d)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat101d)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat101d)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat101d build, photo ok: ok"

# ---- 3. fetch + verify the patch files (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat101e.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c101e.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/app_block_c101e.js" || die "patch_c101e failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$LIVE_SERVER_MD5" ] || die "scratch server.js changed; chat101e must not touch it"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
grep -q '/app.js?v=chat101e"' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101e, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$S/app.js" "$S/index.html" && die "scratch build contains 'Vraj Patel, London'"
grep -qF 'GC=F' "$P/app_block_c101e.js" && die "the new app block must not contain GC=F"
sed -n '/chat101e: market cards/,$p' "$S/app.js" | grep -qF 'GC=F' && die "the installed chat101e block must not contain GC=F"
grep -qF "chat101e: market cards" "$S/app.js" && grep -qF "chat101d: app views" "$S/app.js" || die "chat101d/chat101e app blocks missing"
grep -qF 'Edited by Vraj Patel' "$S/server.js" && grep -qF 'Not investment advice. Capital at risk.' "$S/server.js" || die "byline or disclaimer missing"
grep -qF 'aria-label="Close menu"' "$S/app.js" || die "menu sheet close button missing"
say "wording guards (no 'Vraj Patel, London', no raw GC=F, byline and disclaimer kept, Close X present): ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install (app.js + index.html only) ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101e" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101e")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101e"; done
cp "$S/app.js" "$APP.new-chat101e" && cp "$S/index.html" "$INDEX.new-chat101e" || die "staging copy failed (live files untouched)"
RB="restore app.js and index.html from their .$TS.bak-chat101e copies and DO NOT republish"
mv -f "$APP.new-chat101e" "$APP" && mv -f "$INDEX.new-chat101e" "$INDEX" || { echo "[deploy-chat101e] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101e] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101e] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$LIVE_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore app.js and index.html from their .$TS.bak-chat101e copies."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101e] ERROR: final files differ; $RB" >&2; exit 1; fi
