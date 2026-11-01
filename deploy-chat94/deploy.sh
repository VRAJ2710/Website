#!/usr/bin/env bash
# deploy-chat94: fixes from the chat93 admin QA pass, on top of live chat93. Edits server.js, app.js, index.html (c93.css unchanged).
#  1 admin-only guest preview: any guest page + ?view=guest, for an administrator session only (banner, no-store, noindex);
#    "Guest preview" links on the admin Console and the admin menus. Guests and members: the parameter is ignored.
#  2 About carries the full funding sentence (Editorial standards already had it in full)
#  3 short company paths: /MSFT renders the monitor company page (canonical stays /research/capital-sustainability/MSFT);
#    /msft, /Msft, /MSFT/ 301 to /MSFT. Only the 19 monitor tickers. Redirects keep the query string.
#  4 no "V" avatar placeholders (Research hub and SPX 2026 author blocks); the About overlay hides the photo slot, no "VP" monogram
#  + a monitor page rendered for a signed-in reader ("Your desk") is sent private, not public cache; app.js cache token chat94
# Does NOT: run the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL). Maintenance line 1 stays true.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat94-fixes}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat94"

LIVE_SERVER_MD5=60116e5449f03befbeef1c8e3511ef57   # chat93
LIVE_APP_MD5=3b19083ada923e33b767c0ae476f068f      # chat93
LIVE_INDEX_MD5=1411a118530e30f20b53e77761fe50bf    # chat93
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged by chat94)
NEW_SERVER_MD5=7a7a2df1fc685ba83dbca07e70a09567
NEW_APP_MD5=8a195ba9f9cf3ade9e10ed3a70091806
NEW_INDEX_MD5=b69f3596e29020ca80620246bae23f1b
NEW_SERVER_SHA256=821f8d289cf6a2e2ef694abf558130f0ad510c7ddcab53d26b0b14a5b668fdf2
NEW_APP_SHA256=ba857c4d79f1d818be062369b2cc3458d1bb1882182b7a8a7a6342da58661a0e
NEW_INDEX_SHA256=aca50c2ece11e55dd08eecaf1f071a4181699deabe2d6c9467d2cf4c4fead6b1
SHA_PATCH=9829458ca43cf194e2e6a5ed3834ccc3320f56e6d94767fd2e11d00897ad6253

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat94] $*"; }
die(){ echo "[deploy-chat94] ABORT: $*" >&2; echo "[deploy-chat94] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

# ---- 1. locate the live files ----
find_one(){ local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' 2>/dev/null | sort); do
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat94 >/dev/null 2>&1; then
  say "REFUSE: chat94 is already applied (or a .bak-chat94 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat93)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat93)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat93)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match chat93: ok"

# ---- 3. fetch + verify the patch file ----
W=$(mktemp -d /tmp/deploy-chat94.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1"; say "patch file ok: $1 ${2:0:16}…"; }
getp patch_chat94.py "$SHA_PATCH"

# ---- 4. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat94.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch script failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -q '/app.js?v=chat94' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat94, css chat93) missing"
grep -qi 'drop table\|alter table\|create table' "$P/patch_chat94.py" && die "patch file mentions DDL"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat94" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat94")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat94"; done
cp "$S/server.js" "$SERVER.new-chat94" && cp "$S/app.js" "$APP.new-chat94" && cp "$S/index.html" "$INDEX.new-chat94" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat94 copy and DO NOT republish"
mv -f "$APP.new-chat94" "$APP" && mv -f "$INDEX.new-chat94" "$INDEX" && mv -f "$SERVER.new-chat94" "$SERVER" || { echo "[deploy-chat94] ERROR during install; $RB" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat94] ERROR: node --check failed after install; $RB" >&2; exit 1; }
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || { echo "[deploy-chat94] ERROR: maintenance line 1 changed; $RB" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. The server was NOT started. Next: Republish (only when Vraj says so)."; rm -rf "$W"; exit 0
else echo "[deploy-chat94] ERROR: final md5s differ; $RB" >&2; exit 1; fi
