#!/usr/bin/env bash
# deploy-chat82: apply bb10c (server.js) + rt62d (app.js, index.html) on top of live bb10b / chat81, in the Replit Shell.
# Does NOT: run the server, npm start, git, DB, .replit, package.json, env vars, Stripe. Click Republish yourself afterwards.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
#   --dry-run  do everything in a scratch dir and verify, but do not touch the live files.
set -u
REF="${DEPLOY_REF:-deploy/jack-chat82-bb10c-rt62d}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat82"

# ---- expected values ----
LIVE_SERVER_MD5=e7f75c9bccd6668a8b075d682444af49   # bb10b
LIVE_APP_MD5=78e28a26d768f8cbd0458f1609717ffb      # chat81
LIVE_INDEX_MD5=1d1a37cfa43dde4d1281363414452954    # chat81
NEW_SERVER_MD5=e5391dbbb4a41e4ddfed1140560973e2
NEW_SERVER_SHA256=602b3ef3318072afb7ad9acecbfd6c4a90379aeee0ea6b6b4c25adb390c4136a
NEW_APP_MD5=e45d14a361587253a328c0de1ff4c791
NEW_APP_SHA256=e6b3b6ba2311841c3b966b3fc2f1748660d139f9eb53aec4507d9f98d407bea0
NEW_INDEX_MD5=16c4bade1ff3baf1e7d1f335402d74fa
NEW_INDEX_SHA256=eb7dad16a30653695392d61396a44de96aa916dfaf3403a93829925d56a60622
SHA_PATCH_BB10C=1e66449950523be9088ea04cc2a201c7efa9bbb74234fa5af35c8b03a20ba043
SHA_PATCH_RT62D=62eae1ed2f1402d3967d22b64d1ee309fce6a73630c2d6f663edcafb7abc689a

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat82] $*"; }
die(){ echo "[deploy-chat82] ABORT: $*" >&2; echo "[deploy-chat82] Nothing was changed in the live files." >&2; exit 1; }
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
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat82/*' 2>/dev/null | sort); do
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
  say "REFUSE: already applied (all three files are at the chat82/bb10c md5s). Nothing to do. Click Republish if not done yet."; exit 0
fi
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ]; then
  die "PARTIAL state: some files already patched, some not (server $sm, app $am, index $im). Do not continue; report this."
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (bb10b)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat81)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat81)"
say "live md5s match bb10b / chat81: ok"

# ---- 3. get + verify the patch scripts ----
W=$(mktemp -d /tmp/deploy-chat82.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_bb10c.py "$SHA_PATCH_BB10C"; getp patch_rt62d.py "$SHA_PATCH_RT62D"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_bb10c.py" "$S" || die "bb10c patch script failed"
python3 "$P/patch_rt62d.py" "$S/app.js" "$S/index.html" || die "rt62d patch script failed"
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
diff "$INDEX" "$S/index.html" | grep -q 'app.js?v=chat82' || die "index.html change is not the chat82 bump"
say "index.html change = only app.js?v=chat81 -> chat82: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat82" || die "backup failed for $f"; [ "$(md5of "$f.$TS.bak-chat82")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; done
say "backups: $SERVER.$TS.bak-chat82 (+app.js, +index.html)"
cp "$S/server.js" "$SERVER.new-chat82" && cp "$S/app.js" "$APP.new-chat82" && cp "$S/index.html" "$INDEX.new-chat82" || die "staging copy failed (live files still untouched)"
mv -f "$SERVER.new-chat82" "$SERVER" && mv -f "$APP.new-chat82" "$APP" && mv -f "$INDEX.new-chat82" "$INDEX" || { echo "[deploy-chat82] ERROR during install; restore from *.$TS.bak-chat82" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat82] ERROR: node --check failed after install; restore from *.$TS.bak-chat82" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa  sha256 $(sha256of "$APP")"
echo "index.html md5 $fi_  sha256 $(sha256of "$INDEX")"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ]; then
  say "DONE: all three files match expected. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat82] ERROR: final md5s differ from expected; restore from *.$TS.bak-chat82 and DO NOT republish" >&2; exit 1
fi
