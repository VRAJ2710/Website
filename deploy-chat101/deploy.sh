#!/usr/bin/env bash
# deploy-chat101: feature batch on top of the chat100e build (server 96020a62, app 25e22204, index 3ac8a07c). Line 1 stays false.
#  - New pages: /tools/ (hub), /tools/verify/ (claim checker), /tools/isa-sipp/ (illustrative ISA/SIPP gold planner),
#    /tools/scenario/ (OLS gold scenario simulator), /central-banks/ (Fed/BoE tone and redline tracker),
#    /research/filing-changes/ (10-K/10-Q Risk Factors and MD&A change detector; 25 SEC downloads a day, DISPATCH_SEC_UA).
#  - PWA: /manifest.webmanifest, /sw.js (never caches /api, /api/me, admin or auth; no push), icons, /offline/, install prompt.
#  - Source inspector on the signed-in /gold/ and /brief/; "Check and plan" tools menu in the app.
#  - ", London" removed after Vraj's name (server footer, index.html eyebrow) with a guard; market/time-zone London stays.
#  - On-screen "GC=F" in the app replaced by "front month". Tag app.js?v=chat101. c93.css and assets/founder.webp unchanged.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL, no new tables), the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/PENDING/deploy-chat101"

LIVE_SERVER_MD5=96020a62380b5fe7dfc85d27564fbf3c   # chat100e (deploy/jack-chat100e 343ec43f), maintenance OFF
LIVE_APP_MD5=25e22204c78e72e60b4fb4be67225137
LIVE_INDEX_MD5=3ac8a07c186f1da17d2bfcc23b232e62
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=889e520487059390526900c96afc2d2a
NEW_APP_MD5=562cf0ff82cbac0008df9c8f7f4d29f9
NEW_INDEX_MD5=5fc0897f4ae06c50d2d04ba00d9f4934
NEW_SERVER_SHA256=c3f61b3e9af0eab47533456bd906762c03a15db1328cb2c2cb342ad4c6b50e9b
NEW_APP_SHA256=f2a14bde692d3636c714f664cd3f72f6b725ec080552687d5e887e24e6427e50
NEW_INDEX_SHA256=0a04644b88407ca02f7ad3fdebe33c584da5f8856ea2a9eed94ebffe9f921516
PHOTO_REL="assets/founder.webp"                     # chat100e photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101.py eb9ea0cd8512a69ba82d15be5a9da380b7163f93119515ba573428d6dab8270b"
  "server_block_c101.js cb7c6f42d92dd26531d7f150053ad68107952afc70b15e861051966da5254723"
  "app_block_c101.js b7eebf30602da80c8c509e9f3dd041768b3addc135d0c91ae9d394539a869d59"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101] $*"; }
die(){ echo "[deploy-chat101] ABORT: $*" >&2; echo "[deploy-chat101] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat101 >/dev/null 2>&1; then
  say "REFUSE: deploy-chat101 is already applied (or a .bak-chat101 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat100e)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat100e)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat100e)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100e photo"
say "live md5s match the chat100e build, photo ok: ok"

# ---- 3. fetch + verify the patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat101.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c101.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c101.js" "$P/app_block_c101.js" || die "patch_c101 failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat101' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat101, css chat93) missing"
grep -qF "const C100B_FOUNDER_PHOTO_FILE = \"$PHOTO_REL\";" "$S/server.js" || die "photo path constant in server.js is not $PHOTO_REL"
say "scratch build matches the tested md5/sha256: ok"
grep -qiE 'Vraj Patel,[[:space:]]*London' "$S/server.js" "$S/app.js" "$S/index.html" && die "scratch build still contains 'Vraj Patel, London'"
for bad in 'Edited by Vraj Patel, London' 'edits every piece from London' 'Fix with Agent'; do grep -qF "$bad" "$S/server.js" "$S/app.js" "$S/index.html" && die "scratch build still contains: $bad"; done
for bad in 'COMEX gold futures (GC=F) daily bars, Yahoo' 'COMEX futures (GC=F)' '"Futures (GC=F' 'Gold futures (GC=F)' 'COMEX gold futures (GC=F),' 'COMEX gold futures (GC=F) ·'; do grep -qF "$bad" "$S/app.js" && die "scratch app.js still shows a raw ticker code: $bad"; done
grep -qF 'Edited by Vraj Patel' "$S/server.js" || die "byline 'Edited by Vraj Patel' missing"
grep -q 'cache.put\|pushManager\|addEventListener("push"' "$P/server_block_c101.js" && die "service worker must not cache-put or use push"
say "wording guards (no 'Vraj Patel, London', no raw GC=F on screen, byline kept, SW no push/cache.put): ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat101" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat101")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat101"; done
cp "$S/server.js" "$SERVER.new-chat101" && cp "$S/app.js" "$APP.new-chat101" && cp "$S/index.html" "$INDEX.new-chat101" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat101 copy and DO NOT republish"
mv -f "$APP.new-chat101" "$APP" && mv -f "$INDEX.new-chat101" "$INDEX" && mv -f "$SERVER.new-chat101" "$SERVER" || { echo "[deploy-chat101] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat101] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-chat101 copy."
  rm -rf "$W"; exit 0
else echo "[deploy-chat101] ERROR: final files differ; $RB" >&2; exit 1; fi
