#!/usr/bin/env bash
# deploy-chat100d: CUMULATIVE bundle (chat100 + chat100b + chat100c spot-only gold fix + chat100d final About bio and founder LinkedIn /in/vraj2710; replaces deploy-chat100b and deploy-chat100c) on top of the LIVE reopen2 build (maintenance OFF). Line 1 stays false.
# Edits server.js, app.js, index.html (c93.css unchanged) and writes assets/founder.webp (embedded below, sha256-checked).
#  chat100 : gold/macro dashboard tiles, calm Fear & Greed, self-building SEC screener, source inspector (see deploy-chat100/README.md)
#  chat100c: gold change spot vs OUR OWN previous-UK-day gold-api spot snapshot (no futures) on every gold spot row
#            (Market context /, /gold/, /brief/, dashboard tiles, gold dashboard incl. EUR); "Change not available yet"
#            until a previous-day snapshot exists (expected right after publish). Snapshot kept in the existing cache table.
#            About: founder card (photo, "Edited by Vraj Patel, London", LinkedIn link) on /about and in the app.
#  chat100d: About bio is the final approved text; founder LinkedIn is linkedin.com/in/vraj2710 ("Vraj Patel on LinkedIn"). Tag app.js?v=chat100d.
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL).
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/3e0ed5b776fb62b9719e1ad79e4666f8c72b99b9/deploy-chat100d"

LIVE_SERVER_MD5=bd50fb5335bcaf937fa3e68ed3bf96bb   # live reopen2, maintenance OFF
LIVE_APP_MD5=9ebadee3093d77dafb70559b4984ee12
LIVE_INDEX_MD5=79b9249f6afcbf65b0af7464a4c2afb6
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=15ecc24180575004f6b9674445722d79
NEW_APP_MD5=0e4bb0e3d7749dbeecff35a3c1f20df3
NEW_INDEX_MD5=b0961c778217e08ba9a29178f62aa223
NEW_SERVER_SHA256=94dbe6383465971a1f2742f9664d03caacbbd2b3d1cb98ca1aafc618926f8f33
NEW_APP_SHA256=b8e8fb8833c5726a1e81c0f37a0652a855b734b66669e9be11219ce475fc84ba
NEW_INDEX_SHA256=8d136ee9587f3405984c8fabde66a82659cca5ba6908646cf5e1854a7346e3d6
PHOTO_REL="assets/founder.webp"                     # must match C100B_FOUNDER_PHOTO_FILE in server.js
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c100.py 436a288cf61cac0cbf39375c834fd0ca561c876fbfe848d38cb424cfc90c444d"
  "server_block_c100.js 4118b6c938050da7341bad246dd5e602fae14d6b68f5049c86db6af3c3c8458b"
  "app_block_c100.js c579db32df6a75d17afda844631b8ece5e531924cc23ea4906b27581f05eb2e9"
  "patch_c100d.py bfc88e39df92cccec99ceec587cfaacb3111f7a87fa26a77b3f024e1085090a2"
  "server_block_c100b.js 94de1b2cce3492105541ac260524bf79aac47db01caacfd6340fac9105e9d1c2"
  "app_block_c100b.js 6ea417a6404bcdb209c595ce67e82f28851431d82621f580917660f98d252174"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat100d] $*"; }
die(){ echo "[deploy-chat100d] ABORT: $*" >&2; echo "[deploy-chat100d] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat100d >/dev/null 2>&1; then
  say "REFUSE: deploy-chat100d is already applied (or a .bak-chat100d backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (live reopen2)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (live reopen2)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (live reopen2)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
say "live md5s match the live reopen2 build: ok"

# ---- 3. fetch + verify every patch file (sha256-pinned); decode the photo ----
W=$(mktemp -d /tmp/deploy-chat100d.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done
base64 -d > "$S/founder.webp" <<'PHOTO_B64' || die "photo base64 decode failed"
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
wTNeBU178XAAAAA=
PHOTO_B64
[ "$(sha256of "$S/founder.webp")" = "$PHOTO_SHA256" ] || die "sha256 mismatch for the embedded photo"
say "photo ok: founder.webp ${PHOTO_SHA256:0:16}… ($(wc -c < "$S/founder.webp") bytes)"

# ---- 4. DDL grep on everything that ends up in the live files ----
grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/*.js && die "a code block mentions DDL"
say "DDL grep (create/alter/drop table, create/drop index, truncate): none"

# ---- 5. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c100.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c100 failed (live files untouched)"
python3 "$P/patch_c100d.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c100d failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat100d' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat100d, css chat93) missing"
grep -qF "const C100B_FOUNDER_PHOTO_FILE = \"$PHOTO_REL\";" "$S/server.js" || die "photo path constant in server.js is not $PHOTO_REL"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched, photo not written. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat100d" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat100d")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat100d"; done
PHOTO_NEW=1
if [ -f "$PHOTO" ]; then
  if [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ]; then PHOTO_NEW=0; say "photo already present and identical: $PHOTO"
  else cp -p "$PHOTO" "$PHOTO.$TS.bak-chat100d" || die "backup failed for $PHOTO"; say "backup: $PHOTO.$TS.bak-chat100d"; fi; fi
mkdir -p "$(dirname "$PHOTO")" || die "could not create $(dirname "$PHOTO")"
cp "$S/server.js" "$SERVER.new-chat100d" && cp "$S/app.js" "$APP.new-chat100d" && cp "$S/index.html" "$INDEX.new-chat100d" || die "staging copy failed (live files untouched)"
if [ "$PHOTO_NEW" = "1" ]; then cp "$S/founder.webp" "$PHOTO.new-chat100d" || die "staging copy of the photo failed (live files untouched)"; fi
RB="restore each file from its .$TS.bak-chat100d copy (delete $PHOTO if it had no backup) and DO NOT republish"
if [ "$PHOTO_NEW" = "1" ]; then mv -f "$PHOTO.new-chat100d" "$PHOTO" || { echo "[deploy-chat100d] ERROR installing the photo; $RB" >&2; exit 1; }; fi
mv -f "$APP.new-chat100d" "$APP" && mv -f "$INDEX.new-chat100d" "$INDEX" && mv -f "$SERVER.new-chat100d" "$SERVER" || { echo "[deploy-chat100d] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat100d] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat100d] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS"); fp=$(sha256of "$PHOTO")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"; echo "$PHOTO_REL sha256 $fp"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ] && [ "$fp" = "$PHOTO_SHA256" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-chat100d copy (delete $PHOTO if it was new)."
  rm -rf "$W"; exit 0
else echo "[deploy-chat100d] ERROR: final files differ; $RB" >&2; exit 1; fi
