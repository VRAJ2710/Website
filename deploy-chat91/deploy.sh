#!/usr/bin/env bash
# deploy-chat91: boot-time editorial brand data fix + short title suffix ("| The Dispatch" -> "| The Dispatch Market") on top of live chat90.
# Edits server.js, app.js, index.html (token app.js?v=chat90 -> chat91). Nothing else: no static files, no og-card, no manifest.
# Does NOT: run the server, npm start, git, DB (the SQL runs only when the server boots after you Republish), .replit, package.json, env vars, Stripe.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat91-brand2}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat91"

LIVE_SERVER_MD5=357d8300e6041fbee752ff6f10ee0a93   # chat90
LIVE_APP_MD5=9caddff097af8e72adab562746973603      # chat90
LIVE_INDEX_MD5=65a78b0a630a306780d22708a2120590    # chat90 (v=chat90)
NEW_SERVER_MD5=b6cff45b41890a82a0a5e94bedfea98f
NEW_SERVER_SHA256=ddb479a92a27c2e4c85afe20d5bad60c3be557df5b1ea155cf72501f060ded19
NEW_APP_MD5=1640cc0d0be7f933ed5a54613c2157ba
NEW_APP_SHA256=26a0c582610526a31d6f5649bdd6f67551304e5ebed0f1d67f9947a3fa754088
NEW_INDEX_MD5=ad60345de46342a6242a3791391c02cb
NEW_INDEX_SHA256=b69e610fd71484ef378a663265ca2162ad37f9ab5377b027dd61524409af036a
SHA_PATCH_BRAND2=fcec24651718d915b4b17f65d812257f4e828568ac5313d9e4c5a7344d72aca6

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat91] $*"; }
die(){ echo "[deploy-chat91] ABORT: $*" >&2; echo "[deploy-chat91] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }

for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])'); say "node $(node -v), python $PYV"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"

# ---- 1. locate the live files ----
find_one(){ # name expected_md5
  local name="$1" want="$2" first="" p
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat90/*' -not -path '*/deploy-chat91/*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"
    [ "$(md5of "$p")" = "$want" ] && { echo "$p"; return 0; }
  done
  echo "$first"
}
if [ -n "$DIR" ]; then ROOT="$DIR"; else
  ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do
    [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }
  done
  [ -z "$ROOT" ] && die "could not find server.js (looked in \$PWD, \$HOME/workspace, /home/runner/workspace). cd into the project folder or pass --dir"
fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file under $ROOT (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "current md5: server $sm | app $am | index $im"

# ---- 2. idempotency ----
if [ "$sm" = "$NEW_SERVER_MD5" ] && [ "$am" = "$NEW_APP_MD5" ] && [ "$im" = "$NEW_INDEX_MD5" ]; then
  say "REFUSE: already applied (all three files are at the chat91 md5s). Nothing to do. Click Republish if not done yet."; exit 0
fi
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ]; then
  die "PARTIAL state: some files already patched, some not (server $sm, app $am, index $im). Do not continue; report this."
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat90)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat90)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat90)"
say "live md5s match chat90: ok"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"

# ---- 3. get + verify the patch files ----
W=$(mktemp -d /tmp/deploy-chat91.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_brand2.py "$SHA_PATCH_BRAND2"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_brand2.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "chat91 patch script failed (nothing written to live files)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js"    || die "node --check app.js failed (scratch)"
say "node --check server.js / app.js: ok (scratch)"
rs=$(md5of "$S/server.js"); ra=$(md5of "$S/app.js"); ri=$(md5of "$S/index.html")
[ "$rs" = "$NEW_SERVER_MD5" ] || die "scratch server.js md5 $rs != expected $NEW_SERVER_MD5"
[ "$ra" = "$NEW_APP_MD5" ]    || die "scratch app.js md5 $ra != expected $NEW_APP_MD5"
[ "$ri" = "$NEW_INDEX_MD5" ]  || die "scratch index.html md5 $ri != expected $NEW_INDEX_MD5"
[ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js sha256 mismatch"
[ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ]       || die "scratch app.js sha256 mismatch"
[ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html sha256 mismatch"
say "scratch result matches expected md5/sha256: ok"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
if grep -n -i -E 'dispatch(\s|·|<[^>]*>)+markets\b' "$S/server.js" "$S/app.js" "$S/index.html" | grep -v "bb91" >/dev/null 2>&1; then die "brand 'Dispatch Markets' present in scratch output outside the chat91 SQL"; fi
grep -c "UPDATE dispatch_editorial_content SET payload" "$S/server.js" | grep -qx 2 || die "scratch server.js lacks the 2 boot UPDATE statements"
grep -q "await seedEditorialContent();" "$S/server.js" || die "seedEditorialContent call missing"
say "boot data fix present (2 UPDATE statements after seedEditorialContent): ok"
ch=$(diff "$INDEX" "$S/index.html" | grep -c '^[<>]'); [ "$ch" = "2" ] || die "index.html differs by $ch lines (expected 2 = the token line only)"
diff "$INDEX" "$S/index.html" | grep -q 'app.js?v=chat91' || die "index.html lacks the chat91 token"
say "index.html: only app.js?v=chat90 -> chat91 changed: ok"
for f in "$S/server.js" "$S/app.js"; do
  if grep -n -E '(\| |· )The Dispatch(",|</title>|";)' "$f" | grep -v "Under maintenance" >/dev/null 2>&1; then die "short-suffix title still present in $f"; fi
done
say "no '| The Dispatch' / '· The Dispatch' short-suffix titles left: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install ----
TS=$(date +%Y%m%d-%H%M%S)
BK="$SERVER $APP $INDEX"
for f in $BK; do cp -p "$f" "$f.$TS.bak-chat91" || die "backup failed for $f"; [ "$(md5of "$f.$TS.bak-chat91")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; done
say "backups written: *.$TS.bak-chat91 for: $BK"
cp "$S/server.js" "$SERVER.new-chat91" && cp "$S/app.js" "$APP.new-chat91" && cp "$S/index.html" "$INDEX.new-chat91" || die "staging copy failed (live files still untouched)"
mv -f "$SERVER.new-chat91" "$SERVER" && mv -f "$APP.new-chat91" "$APP" && mv -f "$INDEX.new-chat91" "$INDEX" || { echo "[deploy-chat91] ERROR during install; restore from *.$TS.bak-chat91" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat91] ERROR: node --check failed after install; restore from *.$TS.bak-chat91" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa  sha256 $(sha256of "$APP")"
echo "index.html md5 $fi_  sha256 $(sha256of "$INDEX")"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ]; then
  say "DONE: all three files match expected. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat91] ERROR: final md5s differ from expected; restore from *.$TS.bak-chat91 and DO NOT republish" >&2; exit 1
fi
