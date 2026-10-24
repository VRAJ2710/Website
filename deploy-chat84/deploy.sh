#!/usr/bin/env bash
# deploy-chat84: apply bb10e (server.js) + rt62g (app.js, index.html) on top of live bb10d / chat83b, in the Replit Shell.
# Does NOT: run the server, npm start, git, DB, .replit, package.json, env vars, Stripe. Click Republish yourself afterwards.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
#   --dry-run  do everything in a scratch dir and verify, but do not touch the live files.
set -u
REF="${DEPLOY_REF:-deploy/jack-chat84-bb10e-rt62g}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat84"

# ---- expected values ----
LIVE_SERVER_MD5=6a359cecb836848284c2264d13122482   # bb10d
LIVE_APP_MD5=f63c681c5f366e2185e36dd7d4ccd23c      # chat83b
LIVE_INDEX_MD5=4ef366778c09fe776757f39d083f9ae2    # chat83b
NEW_SERVER_MD5=6b4612281efc32ada0cabf38fa808ccb
NEW_SERVER_SHA256=1a42d427019469a853d4704c2bcec22d3b760f433a5767d4e3200944ecca2530
NEW_APP_MD5=293c103a4efdd0fddaffc114bc3870ee
NEW_APP_SHA256=24c1a308d448935a061f9a2f7378532f78d31f6bc0edadfdc57572b6ccc27433
NEW_INDEX_MD5=abd27d2e409eeef2dc8cf866927bc584
NEW_INDEX_SHA256=c8ff211628c83de21668a593623a50a068c3cb8b59458530cb5726c0bee3eb38
SHA_PATCH_BB10E=957e4b26e8d209df4f1268011eb4c5572a5c02e818b7a58bc185b7dc12fd9d03
SHA_PATCH_RT62G=34b15d60f6906d9e3aff2c8f972dbb103502357c7450898ea160aae087c7aaa8

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat84] $*"; }
die(){ echo "[deploy-chat84] ABORT: $*" >&2; echo "[deploy-chat84] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }

for t in node python3 md5sum sha256sum curl cp; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
# informational only (--dry-run): can this host reach the Coinbase endpoint bb10 uses for the crypto 24h basis? Never aborts.
if [ "$DRY" = "1" ]; then
  CB=$(curl -sS --max-time 10 -w ' HTTP_%{http_code}' -A 'Mozilla/5.0' https://api.exchange.coinbase.com/products/BTC-USD/stats 2>&1 || true)
  case "$CB" in
    *HTTP_200) say "Coinbase BTC-USD/stats: REACHABLE ($(printf '%s' "$CB" | sed 's/ HTTP_200$//' | cut -c1-120))";;
    *) say "Coinbase BTC-USD/stats: UNREACHABLE (informational only; bb10 then falls back to the previous-close basis and labels it): $(printf '%s' "$CB" | cut -c1-160)";;
  esac
fi
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])'); say "node $(node -v), python $PYV"
python3 - <<'PY' || die "python3 >= 3.8 required"
import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)
PY

# ---- 1. locate the live files ----
find_one(){ # name expected_md5 -> prints path of the file with that name whose md5 is expected; else first candidate path
  local name="$1" want="$2" first="" p
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat84/*' 2>/dev/null | sort); do
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
  say "REFUSE: already applied (all three files are at the chat84/bb10e md5s). Nothing to do. Click Republish if not done yet."; exit 0
fi
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ]; then
  die "PARTIAL state: some files already patched, some not (server $sm, app $am, index $im). Do not continue; report this."
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (bb10d)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat83b)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat83b)"
say "live md5s match bb10d / chat83b: ok"

# ---- 3. get + verify the patch scripts ----
W=$(mktemp -d /tmp/deploy-chat84.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_bb10e.py "$SHA_PATCH_BB10E"; getp patch_rt62g.py "$SHA_PATCH_RT62G"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_bb10e.py" "$S" || die "bb10e patch script failed"
python3 "$P/patch_rt62g.py" "$S/app.js" "$S/index.html" || die "rt62g patch script failed"
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
ch=$(diff "$INDEX" "$S/index.html" | grep -c '^[<>]'); [ "$ch" = "2" ] || die "index.html differs by $ch lines (expected exactly 2: the app.js?v= bump)"
diff "$INDEX" "$S/index.html" | grep -q 'app.js?v=chat84' || die "index.html change is not the chat84 bump"
say "index.html change = only app.js?v=chat83b -> chat84: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat84" || die "backup failed for $f"; [ "$(md5of "$f.$TS.bak-chat84")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; done
say "backups: $SERVER.$TS.bak-chat84 (+app.js, +index.html)"
cp "$S/server.js" "$SERVER.new-chat84" && cp "$S/app.js" "$APP.new-chat84" && cp "$S/index.html" "$INDEX.new-chat84" || die "staging copy failed (live files still untouched)"
mv -f "$SERVER.new-chat84" "$SERVER" && mv -f "$APP.new-chat84" "$APP" && mv -f "$INDEX.new-chat84" "$INDEX" || { echo "[deploy-chat84] ERROR during install; restore from *.$TS.bak-chat84" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat84] ERROR: node --check failed after install; restore from *.$TS.bak-chat84" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa  sha256 $(sha256of "$APP")"
echo "index.html md5 $fi_  sha256 $(sha256of "$INDEX")"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ]; then
  say "DONE: all three files match expected. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat84] ERROR: final md5s differ from expected; restore from *.$TS.bak-chat84 and DO NOT republish" >&2; exit 1
fi
