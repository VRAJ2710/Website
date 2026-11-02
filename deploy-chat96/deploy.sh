#!/usr/bin/env bash
# deploy-chat96: chat96 on top of live chat94 (includes everything from chat95, which never shipped on its own).
# Edits server.js, app.js, index.html (c93.css unchanged). Main changes:
#  - caching: only public endpoints share a cache; signed-in and personal answers are private/no-store
#  - last good figures: about 10 minutes on the server and 24 hours on tiles, labelled Delayed / Last known
#  - each figure names its own source (no Yahoo default) and plain market names, no raw codes
#  - free brief sign-up (stores the address only, sends nothing), Plans nav, plain Pricing (GBP 0 / GBP 15 a month)
#  - gold in GBP per ounce and per gram, UK byline, brief preview and Premium sample, calmer signed-in home
#  - 301s (www, /signup, /login, /research/:T), /settings/ page, admin guest-preview cookie, login and reset CSRF,
#    auth CSP and security headers, public-only sitemap, maintenance page tidy (white, favicon, email, disclaimer)
#  - BYOK "Your AI keys" in Settings: AES-256-GCM with env DISPATCH_BYOK_MASTER_KEY, stored in the existing
#    dispatch_openbb_research_cache table under byok:<userId>:<provider>. Without that secret the feature says
#    "Your AI keys are not available yet" and refuses. app.js cache token chat96.
# Does NOT: run the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL). Maintenance line 1 stays true.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat96}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat96"

LIVE_SERVER_MD5=7a7a2df1fc685ba83dbca07e70a09567   # chat94
LIVE_APP_MD5=8a195ba9f9cf3ade9e10ed3a70091806      # chat94
LIVE_INDEX_MD5=b69f3596e29020ca80620246bae23f1b    # chat94
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged by chat94 or chat96)
NEW_SERVER_MD5=e3664233c33925d78473fe15c636e78b
NEW_APP_MD5=2cbeb4f2d231e702c666334b2115a576
NEW_INDEX_MD5=40f4d5ea6c3fac7b696304eb2b75fee2
NEW_SERVER_SHA256=e21a93cc3ac37e04bd07843aac01d501991cbb1935bab88040b21f00d474dc61
NEW_APP_SHA256=5b9fc391d2165ad66fc4c4f9e92fd10d252164a188a008e900e79b8fc00fcfa7
NEW_INDEX_SHA256=65b94867571e35f02026970e0bcc1ae0c968a8021754afd4a739f520d866b1c2
SHA_PATCH=a8038d094edecbaf5f5a196b1e2d6df8965a75e69128232aa8e4436eb0857aab
SHA_PLAIN=0e293e1280e889f73f02204231e75d123e9910270e89375b7057b751522e3e9b
SHA_APPBLK=e4d506fd3cf65863d8dcf6c0ddac578677fb93cc545ba39270a84a83b9e62e65
SHA_SRVBLK=ad018b7674b533a8640a88be858f5c733c63cbdca288cedc0335c272e2d9df77
SHA_LIVE=d2b505968fd59ef53bd9df3a53474e2049fe719a573d9a9b19759a9e387b7754

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat96] $*"; }
die(){ echo "[deploy-chat96] ABORT: $*" >&2; echo "[deploy-chat96] Nothing was changed in the live files." >&2; exit 1; }
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
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-chat96 >/dev/null 2>&1; then
  say "REFUSE: chat96 is already applied (or a .bak-chat96 backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat94)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat94)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat94)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match chat94: ok"

# ---- 3. fetch + verify the patch file ----
W=$(mktemp -d /tmp/deploy-chat96.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1"; say "patch file ok: $1 ${2:0:16}…"; }
getp patch_chat96.py "$SHA_PATCH"; getp plain.js "$SHA_PLAIN"; getp app_block.js "$SHA_APPBLK"; getp server_block.js "$SHA_SRVBLK"; getp live96.js "$SHA_LIVE"

# ---- 4. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat96.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch script failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -q '/app.js?v=chat96' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat96, css chat93) missing"
cat "$P"/* | grep -qi 'drop table\|alter table\|create table' && die "patch file mentions DDL"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat96" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-chat96")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-chat96"; done
cp "$S/server.js" "$SERVER.new-chat96" && cp "$S/app.js" "$APP.new-chat96" && cp "$S/index.html" "$INDEX.new-chat96" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-chat96 copy and DO NOT republish"
mv -f "$APP.new-chat96" "$APP" && mv -f "$INDEX.new-chat96" "$INDEX" && mv -f "$SERVER.new-chat96" "$SERVER" || { echo "[deploy-chat96] ERROR during install; $RB" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat96] ERROR: node --check failed after install; $RB" >&2; exit 1; }
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || { echo "[deploy-chat96] ERROR: maintenance line 1 changed; $RB" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. The server was NOT started. Next: Republish (only when Vraj says so)."; rm -rf "$W"; exit 0
else echo "[deploy-chat96] ERROR: final md5s differ; $RB" >&2; exit 1; fi
