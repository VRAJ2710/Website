#!/usr/bin/env bash
# deploy-chat100: small bundle on top of the LIVE chat100 build (maintenance already OFF). Line 1 stays false.
# Edits server.js, app.js, index.html (c93.css unchanged). Adds:
#  - dashboard: gold and macro readings first (gold spot, silver, gold in pounds, US dollar index, US 10-year yield,
#    US real yield, Brent, pound in dollars, S&P 500 as context), plain names with source + UK time underneath;
#    old AAPL/SPY/NVDA default book becomes gold/macro; "V1 · GOLD FIRST" label removed
#  - Fear & Greed: calm "Not enough data yet" instead of a 50/100 placeholder while inputs are missing
#  - SEC screener: first build happens by itself (first visit or 2 min after start) inside the 25-a-day cap
#    (persisted bb11:sec_downloads); until then "Building the screener, check back shortly."
#  - source inspector: click/tap/Enter on a figure opens a small panel (source + link, series, UK time, status, formula)
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL).
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/9803f1ec8ede796205c70c3de2eec8d108ba499f/deploy-chat100"

LIVE_SERVER_MD5=bd50fb5335bcaf937fa3e68ed3bf96bb   # live reopen2, maintenance OFF
LIVE_APP_MD5=9ebadee3093d77dafb70559b4984ee12
LIVE_INDEX_MD5=79b9249f6afcbf65b0af7464a4c2afb6
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=e001ba80b46850f6c3480d07228d1d48
NEW_APP_MD5=0560b1974961e09940bd99736babeb86
NEW_INDEX_MD5=4d603143dafbd09dd9ffca07c7a072dd
NEW_SERVER_SHA256=22d3c578d602fd5ba64aa6b19ad3c7164463f4f9be7b2fa76bde5fc5aa2fe115
NEW_APP_SHA256=a1dfc7cf92e1566debfebe9e8e54c7b791f3c9d55f3fda87de9e60a4885f46d6
NEW_INDEX_SHA256=6dd64046dfbcbe0f4a4337cde50dcbd8827a7710b3a60940ec253a4dac5ed382
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c100.py 436a288cf61cac0cbf39375c834fd0ca561c876fbfe848d38cb424cfc90c444d"
  "server_block_c100.js 4118b6c938050da7341bad246dd5e602fae14d6b68f5049c86db6af3c3c8458b"
  "app_block_c100.js c579db32df6a75d17afda844631b8ece5e531924cc23ea4906b27581f05eb2e9"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat100] $*"; }
die(){ echo "[deploy-chat100] ABORT: $*" >&2; echo "[deploy-chat100] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
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
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css   = $CSS (must stay chat93)"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"

# ---- 2. refuse a second run; check the base ----
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat100 >/dev/null 2>&1; then
  say "REFUSE: deploy-chat100 is already applied (or a .bak-chat100 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (live reopen2)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (live reopen2)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (live reopen2)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
say "live md5s match the live reopen2 build: ok"

# ---- 3. fetch + verify every patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-chat100.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done

# ---- 4. DDL grep on everything that ends up in the live files ----
grep -inE 'create table|alter table|drop table|create index|truncate ' "$P"/*.js && die "a code block mentions DDL"
say "DDL grep (create/alter/drop table, create index, truncate): none"

# ---- 5. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_c100.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_c100 failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat100' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat100, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat100" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat100")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat100"; done
cp "$S/server.js" "$SERVER.new-chat100" && cp "$S/app.js" "$APP.new-chat100" && cp "$S/index.html" "$INDEX.new-chat100" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat100 copy and DO NOT republish"
mv -f "$APP.new-chat100" "$APP" && mv -f "$INDEX.new-chat100" "$INDEX" && mv -f "$SERVER.new-chat100" "$SERVER" || { echo "[deploy-chat100] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat100] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat100] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. Line 1 still = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-chat100 copy."
  rm -rf "$W"; exit 0
else echo "[deploy-chat100] ERROR: final md5s differ; $RB" >&2; exit 1; fi
