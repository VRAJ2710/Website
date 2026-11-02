#!/usr/bin/env bash
# deploy-chat100e: small change on top of the LIVE chat100d build (publish 0089d1b9). Line 1 stays false. c93.css and assets/founder.webp unchanged.
#  - Byline "Edited by Vraj Patel, London" -> "Edited by Vraj Patel" everywhere it appears: guest About card, /about and
#    /editorial-standards bylines, article/brief/research page bylines and the home meta description (all via C93_EDITOR),
#    the contact block, the app About sheet, the app footer brand line, and the legacy About in index.html.
#  - Bio -> "Vraj Patel founded The Dispatch Market to give independent investors a careful, sourced read on gold and macro."
#    (guest About and app About). The footer "Published by Vraj Patel, London" is left as it is.
#  - patch_c100e.py fails if "Edited by Vraj Patel, London" or "edits every piece from London" remains. Tag app.js?v=chat100e.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL), the photo.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/94255b95f94c1b5c88cb9ddc9afdfb17ef34ee51/deploy-chat100e"

LIVE_SERVER_MD5=15ecc24180575004f6b9674445722d79   # live chat100d (publish 0089d1b9), maintenance OFF
LIVE_APP_MD5=0e4bb0e3d7749dbeecff35a3c1f20df3
LIVE_INDEX_MD5=b0961c778217e08ba9a29178f62aa223
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=96020a62380b5fe7dfc85d27564fbf3c
NEW_APP_MD5=25e22204c78e72e60b4fb4be67225137
NEW_INDEX_MD5=3ac8a07c186f1da17d2bfcc23b232e62
NEW_SERVER_SHA256=8c2bf350c1a7b0ff59977d2d56b72f8d7e168c8b4c797b77337dcb841fa9ac85
NEW_APP_SHA256=03279c72ec330b3dcfedefba6d5ddb377fd79c4968e152d7510e017c9c78c91c
NEW_INDEX_SHA256=978dd3debcb9482dcf60d5362f4bb856d064d85eacdc065a4f89ac278469649b
PHOTO_REL="assets/founder.webp"                     # live chat100d photo; checked, never written
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c100e.py 26345a3e696218d8ff5c75ba03d4556524fbf2e43f44a063f00301c0f213b55b"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat100e] $*"; }
die(){ echo "[deploy-chat100e] ABORT: $*" >&2; echo "[deploy-chat100e] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat100e >/dev/null 2>&1; then
  say "REFUSE: deploy-chat100e is already applied (or a .bak-chat100e backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (live chat100d)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (live chat100d)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (live chat100d)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or not the chat100d photo"
say "live md5s match the live chat100d build, photo ok: ok"

# ---- 3. fetch + verify the patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat100e.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_c100e.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c100e failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat100e' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat100e, css chat93) missing"
grep -qF "const C100B_FOUNDER_PHOTO_FILE = \"$PHOTO_REL\";" "$S/server.js" || die "photo path constant in server.js is not $PHOTO_REL"
say "scratch build matches the tested md5/sha256: ok"
for bad in 'Edited by Vraj Patel, London' 'edits every piece from London'; do grep -qF "$bad" "$S/server.js" "$S/app.js" "$S/index.html" && die "scratch build still contains: $bad"; done
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat100e" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat100e")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat100e"; done
cp "$S/server.js" "$SERVER.new-chat100e" && cp "$S/app.js" "$APP.new-chat100e" && cp "$S/index.html" "$INDEX.new-chat100e" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat100e copy and DO NOT republish"
mv -f "$APP.new-chat100e" "$APP" && mv -f "$INDEX.new-chat100e" "$INDEX" && mv -f "$SERVER.new-chat100e" "$SERVER" || { echo "[deploy-chat100e] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat100e] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat100e] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-chat100e copy."
  rm -rf "$W"; exit 0
else echo "[deploy-chat100e] ERROR: final files differ; $RB" >&2; exit 1; fi
