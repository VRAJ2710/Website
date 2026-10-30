#!/usr/bin/env bash
# deploy-chat92: on top of live chat91. Edits server.js ONLY (app.js and index.html are checked, not changed; no token bump).
#  1 boot SQL: case-insensitive, separator-tolerant, case-preserving 'Dispatch Markets' -> 'Dispatch Market' in stored editorial payloads
#  2 server-rendered <head> for /research/capital-sustainability, /method, /{TICKER}   3 /pricing og:/twitter: tags
#  4 maintenance gate exempts GET/HEAD /manifest.json only (line 1 stays true)        5 /api/monitor sec.downloads_today + sec.downloads_cap
# Does NOT: run the server, npm, git, DB (the SQL runs only when the server boots after you Republish), .replit, package.json, env vars, Stripe.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat92-fixes}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat92"

LIVE_SERVER_MD5=b6cff45b41890a82a0a5e94bedfea98f   # chat91
LIVE_APP_MD5=1640cc0d0be7f933ed5a54613c2157ba      # chat91 (unchanged by chat92)
LIVE_INDEX_MD5=ad60345de46342a6242a3791391c02cb    # chat91 (unchanged by chat92)
NEW_SERVER_MD5=df10e32fb82311423f475c62833d0763
NEW_SERVER_SHA256=0a83f10f073331dc84105eb756b4d5c9bba1d0fdcfdab00c8e4ed84c78230bac
SHA_PATCH_C92=4d13a33eb53efd34b51f04a98da083335732abc7a6bd16276bd6a6b20deb6a47

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat92] $*"; }
die(){ echo "[deploy-chat92] ABORT: $*" >&2; echo "[deploy-chat92] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }

for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])'); say "node $(node -v), python $PYV"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"

# ---- 1. locate the live files ----
find_one(){ # name expected_md5 [alt_md5]
  local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat90/*' -not -path '*/deploy-chat91/*' -not -path '*/deploy-chat92/*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"
    m=$(md5of "$p"); { [ "$m" = "$want" ] || { [ -n "$alt" ] && [ "$m" = "$alt" ]; }; } && { echo "$p"; return 0; }
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
SERVER=$(find_one server.js "$LIVE_SERVER_MD5" "$NEW_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file under $ROOT (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "current md5: server $sm | app $am | index $im"

# ---- 2. idempotency + base check ----
if [ "$sm" = "$NEW_SERVER_MD5" ] && [ "$am" = "$LIVE_APP_MD5" ] && [ "$im" = "$LIVE_INDEX_MD5" ]; then
  say "REFUSE: already applied (server.js is at the chat92 md5; app.js/index.html at chat91). Nothing to do. Click Republish if not done yet."; exit 0
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat91)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat91)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat91)"
say "live md5s match chat91: ok"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"

# ---- 3. get + verify the patch file ----
W=$(mktemp -d /tmp/deploy-chat92.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_chat92.py "$SHA_PATCH_C92"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"
python3 "$P/patch_chat92.py" "$S/server.js" || die "chat92 patch script failed (nothing written to live files)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
say "node --check server.js: ok (scratch)"
rs=$(md5of "$S/server.js")
[ "$rs" = "$NEW_SERVER_MD5" ] || die "scratch server.js md5 $rs != expected $NEW_SERVER_MD5"
[ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js sha256 mismatch"
say "scratch result matches expected md5/sha256: ok"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -c "UPDATE dispatch_editorial_content SET payload" "$S/server.js" | grep -qx 3 || die "scratch server.js lacks the 3 boot UPDATE statements"
grep -q 'if (p === "/manifest.json") return true;' "$S/server.js" || die "manifest exemption missing"
grep -q 'return text(res, 200, bb92MonitorShell(p)' "$S/server.js" || die "monitor head route missing"
grep -q 'og:title" content="Pricing · The Dispatch Market"' "$S/server.js" || die "pricing og tags missing"
grep -q 'sec.downloads_cap = BB11_MAX_FACTS_PER_DAY' "$S/server.js" || die "downloads_cap missing"
say "all 5 chat92 changes present: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install (server.js only) ----
TS=$(date +%Y%m%d-%H%M%S)
cp -p "$SERVER" "$SERVER.$TS.bak-chat92" || die "backup failed for $SERVER"
[ "$(md5of "$SERVER.$TS.bak-chat92")" = "$(md5of "$SERVER")" ] || die "backup verify failed for $SERVER"
say "backup written: $SERVER.$TS.bak-chat92"
cp "$S/server.js" "$SERVER.new-chat92" || die "staging copy failed (live files still untouched)"
mv -f "$SERVER.new-chat92" "$SERVER" || { echo "[deploy-chat92] ERROR during install; restore from $SERVER.$TS.bak-chat92" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" || { echo "[deploy-chat92] ERROR: node --check failed after install; restore from $SERVER.$TS.bak-chat92" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa  (unchanged)"
echo "index.html md5 $fi_  (unchanged)"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$LIVE_APP_MD5" ] && [ "$fi_" = "$LIVE_INDEX_MD5" ]; then
  say "DONE: server.js matches expected; app.js/index.html unchanged. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat92] ERROR: final md5s differ from expected; restore from $SERVER.$TS.bak-chat92 and DO NOT republish" >&2; exit 1
fi
