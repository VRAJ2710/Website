#!/usr/bin/env bash
# deploy-chat101d: support email -> vraj2710@hotmail.com, plus live-bug fixes, on top of the LIVE chat101c build
#   (server 29466d26, app 999036af, index 4049a9ac; c93.css 9d6a86a6). Line 1 stays false.
#  - server.js: C93_CONTACT (footer "Contact:", About "Get in touch", Contact page, Editorial standards, Corrections,
#    Pricing/footer, desk footer) and the Terms "Questions:" + Privacy "Contact:" mailto links now show vraj2710@hotmail.com;
#    on phones, tables (not the market-context cards) scroll inside their own box instead of widening the page;
#    JSON-LD publisher URL lower-cased to linkedin.com/in/vraj2710 (name stays "Vraj Patel").
#  - app.js: app views never scroll sideways on phones; the /watchlist "Daily check" button gets solid AA colours (light and dark).
#  - index.html: cache tag app.js?v=chat101d (shown on /dashboard/); JSON-LD publisher URL lower-cased.
#  - Left alone on purpose: the outbound data-feed User-Agent strings (SEC/official sources) and the recovery email From (env var).
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, routes, menus, data, DB schema (no DDL), c93.css, the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/94effc06a4aa94d84a4f085e9b821768ffcdb114/deploy-chat101d"

LIVE_SERVER_MD5=29466d26a31ae628c37f3b7ea1f524c8   # chat101c (deploy/jack-chat101c fdc72d3b), maintenance OFF
LIVE_APP_MD5=999036af68d57c3198e0d5018fdeffd0      # chat101c
LIVE_INDEX_MD5=4049a9acf36b90db9ddb4665c1e05914
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=7a959bc6c9430d0364e8ef65d7934c09
NEW_APP_MD5=5773e359eb0a88af42d0c03df2d0bebd
NEW_INDEX_MD5=90055663d4c88a2690ed7770e105ee23
NEW_SERVER_SHA256=fb6923fd1c4126deddc552a5ca6777894259bd5fbbbc33e8e01a505a04bba3e6
NEW_APP_SHA256=7f2a04d0e0c42c234ccc3be2b312410165322dfbed7b0e84fbe95924d64b378c
NEW_INDEX_SHA256=7ca34c79ba1dcc2deffb46b98be7173df1657aba942307955e9db85a6f853c7f
NEW_EMAIL="vraj2710@hotmail.com"
OLD_EMAIL="dispatchmarket@mail.grokbot.com"
PHOTO_REL="assets/founder.webp"                     # chat100e photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101d.py d89b8ef4baf0290521e4fcb9d7a445219fc08a89911115bd292ddc6d208097cc"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101d] $*"; }
die(){ echo "[deploy-chat101d] ABORT: $*" >&2; echo "[deploy-chat101d] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat101d >/dev/null 2>&1; then
  say "REFUSE: deploy-chat101d is already applied (or a .bak-chat101d backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat101c)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat101c)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat101c)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat101c build, photo ok: ok"

# ---- 3. fetch + verify the patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat101d.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c101d.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c101d failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat101d"' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101d, css chat93) missing"
grep -qF "const C100B_FOUNDER_PHOTO_FILE = \"$PHOTO_REL\";" "$S/server.js" || die "photo path constant in server.js is not $PHOTO_REL"
say "scratch build matches the tested md5/sha256: ok"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$S/server.js" "$S/app.js" "$S/index.html" && die "scratch build still contains 'Vraj Patel, London'"
for bad in 'Edited by Vraj Patel, London' 'edits every piece from London' 'Fix with Agent'; do grep -qF "$bad" "$S/server.js" "$S/app.js" "$S/index.html" && die "scratch build still contains: $bad"; done
for bad in 'COMEX gold futures (GC=F) daily bars, Yahoo' 'COMEX futures (GC=F)' '"Futures (GC=F' 'Gold futures (GC=F)' 'COMEX gold futures (GC=F),' 'COMEX gold futures (GC=F) ·'; do grep -qF "$bad" "$S/app.js" && die "scratch app.js still shows a raw ticker code: $bad"; done
grep -qF 'Edited by Vraj Patel' "$S/server.js" || die "byline 'Edited by Vraj Patel' missing"
grep -qF "const C93_CONTACT = \"$NEW_EMAIL\";" "$S/server.js" || die "contact constant is not $NEW_EMAIL"
[ "$(grep -o "$OLD_EMAIL" "$S/server.js" | wc -l)" = "1" ] && grep -qF "const C97_UA = \"The Dispatch Market research ($OLD_EMAIL)\";" "$S/server.js" || die "old address still present outside the data-feed User-Agent"
grep -qF "$OLD_EMAIL" "$S/app.js" "$S/index.html" && die "old address in app.js/index.html"
grep -qF "mailto:$NEW_EMAIL" "$S/server.js" || die "new mailto missing"
grep -qF '${C101C_CSS}${C101D_CSS}</style>' "$S/server.js" && grep -qF "chat101d: app views" "$S/app.js" || die "chat101d fix blocks missing"
grep -qF 'GC=F' "$P/patch_c101d.py" && die "patch must not contain GC=F"
grep -qF 'aria-label="Close menu"' "$S/server.js" && grep -qF 'aria-label="Close menu"' "$S/app.js" || die "menu sheet close button missing"
grep -qF 'Not investment advice. Capital at risk.' "$S/server.js" || die "disclaimer 'Not investment advice. Capital at risk.' missing"
say "wording guards (no 'Vraj Patel, London', no raw GC=F, byline and disclaimer kept, Close X present, contact = new address, old address only in the data-feed User-Agent): ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101d" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101d")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101d"; done
cp "$S/server.js" "$SERVER.new-chat101d" && cp "$S/app.js" "$APP.new-chat101d" && cp "$S/index.html" "$INDEX.new-chat101d" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat101d copy and DO NOT republish"
mv -f "$APP.new-chat101d" "$APP" && mv -f "$INDEX.new-chat101d" "$INDEX" && mv -f "$SERVER.new-chat101d" "$SERVER" || { echo "[deploy-chat101d] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101d] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101d] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-chat101d copy."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101d] ERROR: final files differ; $RB" >&2; exit 1; fi
