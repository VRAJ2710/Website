#!/usr/bin/env bash
# deploy-chat95: fixes on top of live chat94. Edits server.js, app.js, index.html (c93.css unchanged).
#  1 macro grid: all eight tiles render from the first paint. A tile with no fresh figure shows its last known value with
#    the UK time it was saved, else a labelled "Loading latest..." placeholder (never an empty grey cell). The US real yield
#    is fetched at once (no idle wait), kept with its print date, retried once; the server warms it at boot.
#  2 no raw market codes (GC=F, DX-Y.NYB, EURUSD=X, BTC-USD...) in reader-facing text: plain names such as
#    "Gold futures (COMEX, front month)", with the source in the as-of line ("Yahoo Finance, delayed"). JSON source fields unchanged.
#  3 About / Methodology / other trust pages keep ?view=guest inside the admin guest preview
#  4 desk and crypto quote routes answer identical requests from a 15 s cache (and a last good answer, marked as such,
#    instead of a 429). The rate limiter itself (30 per minute per address) is unchanged. app.js cache token chat95
# Does NOT: run the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL). Maintenance line 1 stays true.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat95-fixes}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat95"

LIVE_SERVER_MD5=7a7a2df1fc685ba83dbca07e70a09567   # chat94
LIVE_APP_MD5=8a195ba9f9cf3ade9e10ed3a70091806      # chat94
LIVE_INDEX_MD5=b69f3596e29020ca80620246bae23f1b    # chat94
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged by chat94 and chat95)
NEW_SERVER_MD5=4d826690a8d93016cca4833c5751dcf9
NEW_APP_MD5=970cf9ecebf0cfa5d8750937bdb0b537
NEW_INDEX_MD5=278960434e869d5f2801c5a5512bf4ad
NEW_SERVER_SHA256=07456d26998bb3d4d9532ae4a1c8c6bd57915c87d7812f4355cbdd5fb09c618d
NEW_APP_SHA256=0cfa28c3b35b0ff4694e4464872356b222ec2e877567a6beaba4d1636582d103
NEW_INDEX_SHA256=a53a6061a1889c33745445cfcadf5c3b039c4bdb5dbe0e4183db5b002c9ea527
SHA_PATCH=e07ee9abb5a665c0622c781c854b6f5bba05d19c4f30e99601c1ad6ba53e63b2
SHA_PLAIN=0e293e1280e889f73f02204231e75d123e9910270e89375b7057b751522e3e9b
SHA_APPBLK=4c155c401143c9f66d8fad53e1a5420ba01b6797e97329cc8eb3170ff1bc30dc
SHA_SRVBLK=583f5f9b02855e09d1385d6796b740f484209f705b7dba0bf9db0dda83e7e37f

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat95] $*"; }
die(){ echo "[deploy-chat95] ABORT: $*" >&2; echo "[deploy-chat95] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat95 >/dev/null 2>&1; then
  say "REFUSE: chat95 is already applied (or a .bak-chat95 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat94)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat94)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat94)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match chat94: ok"

# ---- 3. fetch + verify the patch file ----
W=$(mktemp -d /tmp/deploy-chat95.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1"; say "patch file ok: $1 ${2:0:16}…"; }
getp patch_chat95.py "$SHA_PATCH"; getp plain.js "$SHA_PLAIN"; getp app_block.js "$SHA_APPBLK"; getp server_block.js "$SHA_SRVBLK"

# ---- 4. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat95.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch script failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -q '/app.js?v=chat95' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat95, css chat93) missing"
cat "$P"/* | grep -qi 'drop table\|alter table\|create table' && die "patch file mentions DDL"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat95" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat95")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat95"; done
cp "$S/server.js" "$SERVER.new-chat95" && cp "$S/app.js" "$APP.new-chat95" && cp "$S/index.html" "$INDEX.new-chat95" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat95 copy and DO NOT republish"
mv -f "$APP.new-chat95" "$APP" && mv -f "$INDEX.new-chat95" "$INDEX" && mv -f "$SERVER.new-chat95" "$SERVER" || { echo "[deploy-chat95] ERROR during install; $RB" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat95] ERROR: node --check failed after install; $RB" >&2; exit 1; }
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || { echo "[deploy-chat95] ERROR: maintenance line 1 changed; $RB" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. The server was NOT started. Next: Republish (only when Vraj says so)."; rm -rf "$W"; exit 0
else echo "[deploy-chat95] ERROR: final md5s differ; $RB" >&2; exit 1; fi
