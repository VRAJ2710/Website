#!/usr/bin/env bash
# deploy-chat93: credibility redesign (groups A-F) on top of live chat92. Edits server.js, app.js, index.html; adds c93.css.
#  A trust pages /about /methodology /editorial-standards /corrections /contact, brand-correct /manifest.json, sitemap entries
#  B paper theme (c93.css), text wordmark + plain nav + disclaimer strip, trust footer, paper 404/auth/pricing/legal pages
#  C no dash or "NO LIVE SYNC" values, per-asset session labels, plain-English Brief card, desk-score lines removed
#  D capital-sustainability company page rewritten (correct "Rank N of 19", four figures, source line, plain flags)
#  G v2: server-rendered guest Home, Markets, Gold, Brief, Signals, News, Research and monitor pages (mockup layout);
#    no placeholder rows (last official figure with its date, else the row is left out); calm signed-in desk
#  E SEC daily download count also kept in dispatch_openbb_research_cache (existing table, no DDL)
#  F background polling pauses when the tab is hidden; duplicate GETs within 60 s share one request; charts lib loads on first chart
# Does NOT: run the server, npm, git, .replit, package.json, env vars, Stripe, DB schema. Maintenance line 1 stays true.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat93-redesign}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat93"

LIVE_SERVER_MD5=df10e32fb82311423f475c62833d0763   # chat92
LIVE_APP_MD5=1640cc0d0be7f933ed5a54613c2157ba      # chat91/92
LIVE_INDEX_MD5=ad60345de46342a6242a3791391c02cb    # chat91/92
NEW_SERVER_MD5=360b7a180faea428882826aad5a8b440
NEW_APP_MD5=3b19083ada923e33b767c0ae476f068f
NEW_INDEX_MD5=1411a118530e30f20b53e77761fe50bf
NEW_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550
NEW_SERVER_SHA256=51f2b155eca662be8917d49c135a77e4218f283b97561cd4d85ef033fa810cb6
NEW_APP_SHA256=eb0e7f7977607585c812d5f297c6dbf52b36cdcef715da0ed53324fbb607a766
NEW_INDEX_SHA256=eeb2fc9804c7c672e54c2d03979c60642dd6a442391d345667c1f6ff1ef02f44
SHA_PATCH=36b0d14e243a60297ab8bc957f881634d54f62616caf80c88a6644b2ff133686
SHA_PRE=9461fdf0ef72ea5606a4973ed47214dc5d590609e02469729f559207fd0e3f81
SHA_POST=76671face82b127468cf805a32d2e1821f031f7adb93d6be74b2ac128575680f
SHA_PAGES=cca42647a814a3b57d8522406a1d22c911efeb4fa2a10df48b492342bf902f4d
SHA_FE88=61bc6b12ff5f24bf74aa9bf8494266149546088cab7e8c3e5845e79273add9e6
SHA_LIVE=45edfa6bca6d807ba401fa4bab4910eefc50a71638a0ac6487cb280e5a309460
SHA_CSS=f45cbad74b055f94f6598b968a15552a3ea39dd0ec9ef0adc7de688ae1fc7bd0

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat93] $*"; }
die(){ echo "[deploy-chat93] ABORT: $*" >&2; echo "[deploy-chat93] Nothing was changed in the live files." >&2; exit 1; }
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
[ -f "$SDIR/styles.css" ] || die "styles.css is not next to server.js ($SDIR); c93.css must sit beside it"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css  -> $CSS"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"

# ---- 2. refuse a second run; check the base ----
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat93 >/dev/null 2>&1; then
  say "REFUSE: chat93 is already applied (or a .bak-chat93 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat92)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match chat92: ok"

# ---- 3. fetch + verify the patch files ----
W=$(mktemp -d /tmp/deploy-chat93.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1"; say "patch file ok: $1 ${2:0:16}…"; }
getp patch_chat93.py "$SHA_PATCH"; getp c93_pre.js "$SHA_PRE"; getp c93_post.js "$SHA_POST"
getp c93_server_pages.js "$SHA_PAGES"; getp c93_fe88_company.js "$SHA_FE88"; getp c93_live.js "$SHA_LIVE"; getp c93.css "$SHA_CSS"

# ---- 4. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat93.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P" || die "patch script failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
[ "$(md5of "$P/c93.css")" = "$NEW_CSS_MD5" ] || die "c93.css differs from the tested build"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -q '/app.js?v=chat93' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache token chat93 missing"
grep -q '"/c93.css"' "$S/server.js" || die "c93.css not on the static allowlist"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat93" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat93")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat93"; done
[ -f "$CSS" ] && { cp -p "$CSS" "$CSS.$TS.bak-chat93"; say "backup: $CSS.$TS.bak-chat93"; }
cp "$S/server.js" "$SERVER.new-chat93" && cp "$S/app.js" "$APP.new-chat93" && cp "$S/index.html" "$INDEX.new-chat93" && cp "$P/c93.css" "$CSS.new-chat93" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat93 copy (and delete $CSS) and DO NOT republish"
mv -f "$CSS.new-chat93" "$CSS" && mv -f "$APP.new-chat93" "$APP" && mv -f "$INDEX.new-chat93" "$INDEX" && mv -f "$SERVER.new-chat93" "$SERVER" || { echo "[deploy-chat93] ERROR during install; $RB" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat93] ERROR: node --check failed after install; $RB" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$NEW_CSS_MD5" ]; then
  say "DONE: all four files match the tested build. The server was NOT started. Next: Republish (only when Vraj says so)."; rm -rf "$W"; exit 0
else echo "[deploy-chat93] ERROR: final md5s differ; $RB" >&2; exit 1; fi
