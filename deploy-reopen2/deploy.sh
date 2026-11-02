#!/usr/bin/env bash
# deploy-reopen2: live QA fixes on top of the live final build (publish fd2d2c71) AND maintenance OFF.
# Edits server.js, app.js, index.html (c93.css unchanged). Fixes:
#  - line 1 -> const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)
#  - F1 admin ?view=guest / ?view=exit act on the same request; signed-in pages never publicly cached
#  - F2 with no DISPATCH_BYOK_MASTER_KEY: "Use your own AI key: coming soon" (full BYOK copy returns once the key is set)
#  - F3 signed-in home: Market context in the wide column; F4 one free-brief form per page
#  - F5 desk: calm "Updating…" (never "Syncing… / awaiting feed / 0 priced"), no greyed banner or sync strip
#  - admin AI status no longer lists xAI; Portfolio X-ray CSV accepts "12,500" in quoted amounts
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL).
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/620af7693e297f2b30866568db267c6f6799d40d/deploy-reopen2"

LIVE_SERVER_MD5=ccd31a713886f6638787e0cd7408bb0b   # live final (fd2d2c71)
LIVE_APP_MD5=8d085d79ad06baceed05aac8c18aa66b
LIVE_INDEX_MD5=fb535741645653c1f4bb4dc9df4846c9
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged)
NEW_SERVER_MD5=bd50fb5335bcaf937fa3e68ed3bf96bb
NEW_APP_MD5=9ebadee3093d77dafb70559b4984ee12
NEW_INDEX_MD5=79b9249f6afcbf65b0af7464a4c2afb6
NEW_SERVER_SHA256=b463a5173720de91ee8398c17c1eb9ff55bab0f3b27ab3d5375740e7cbeab573
NEW_APP_SHA256=a905594c237b7b7c71f408f4c0aef34a5dd581aede70e01a9706c7a5a10cb4c5
NEW_INDEX_SHA256=de11c0e97ff9e2bf18ad7bab45d0834e2814ffebbf4c5d900f93647a0b9a5b7d
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_reopen.py 6626ae2634c15f658c634f2ba44b3539b7686739778ca44889cfbd551d8451bc"
  "server_block_r2.js 18206f575f795b54c2964435b9eeb47df094eb022b1a3a566b7e8d1920a981c5"
  "app_block_r2.js 134a1e09317db5a6fe0e0c7b453fbcea56eba53165b18502f3b3f58b623e6ac2"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-reopen2] $*"; }
die(){ echo "[deploy-reopen2] ABORT: $*" >&2; echo "[deploy-reopen2] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

# ---- 1. locate the live files ----
find_one(){ local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' -not -path '*/deploy-final*' -not -path '*/deploy-reopen*' 2>/dev/null | sort); do
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-reopen2 >/dev/null 2>&1; then
  say "REFUSE: deploy-reopen2 is already applied (or a .bak-reopen2 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (live final)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (live final)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (live final)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match the live final build: ok"

# ---- 3. fetch + verify every patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-reopen2.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
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
python3 "$P/patch_reopen.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_reopen failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(head -n 1 "$S/server.js")" = "$NEW_L1" ] || die "scratch server.js line 1 is not the maintenance=false line"
grep -q '/app.js?v=chat99r2' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat99r2, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-reopen2" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-reopen2")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-reopen2"; done
cp "$S/server.js" "$SERVER.new-reopen2" && cp "$S/app.js" "$APP.new-reopen2" && cp "$S/index.html" "$INDEX.new-reopen2" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-reopen2 copy and DO NOT republish"
mv -f "$APP.new-reopen2" "$APP" && mv -f "$INDEX.new-reopen2" "$INDEX" && mv -f "$SERVER.new-reopen2" "$SERVER" || { echo "[deploy-reopen2] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-reopen2] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-reopen2] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
head -n 1 "$SERVER"
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. Line 1 = maintenance OFF. The server was NOT started; it takes effect on Republish (only when Vraj says so)."
  say "To undo: restore each file from its .$TS.bak-reopen2 copy."
  rm -rf "$W"; exit 0
else echo "[deploy-reopen2] ERROR: final md5s differ; $RB" >&2; exit 1; fi
