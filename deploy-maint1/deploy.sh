#!/usr/bin/env bash
# deploy-maint1: SERVER-ONLY: apply bb10i (server.js) on top of live bb10g, in the Replit Shell. app.js and index.html are never modified.
# Does NOT: run the server, npm start, git, DB, .replit, package.json, env vars, Stripe. Click Republish yourself afterwards.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
#   --dry-run  do everything in a scratch dir and verify, but do not touch the live files.
set -u
REF="${DEPLOY_REF:-deploy/jack-maint1-bb10i}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-maint1"

# ---- expected values ----
LIVE_SERVER_MD5=9777ab9b8bebaa77f475b738995aa3d8   # bb10g
APP_MD5=21f3cee5da20d9fc2f2f03d21623dcb4           # chat86, must stay unchanged (informational check)
INDEX_MD5=35084b102b38f99b582838aa19dadfad         # chat86, must stay unchanged (informational check)
NEW_SERVER_MD5=d01094a38f0fbf00800ccd1bbc5f733c
NEW_SERVER_SHA256=8fa0ff7ff1ed2e2b39c705c496113abee0f365b1124b151cf2c7361dc973e069
SHA_PATCH_BB10I=90d962dedd0554e517fc13f6c5c76ba4bb170d002a80618a605499815c9452ad

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-maint1] $*"; }
die(){ echo "[deploy-maint1] ABORT: $*" >&2; echo "[deploy-maint1] Nothing was changed in the live files." >&2; exit 1; }
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
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-maint1/*' 2>/dev/null | sort); do
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
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); [ -f "$SERVER" ] || die "missing live server.js under $ROOT"
APP=$(find_one app.js "$APP_MD5"); INDEX=$(find_one index.html "$INDEX_MD5")
say "server.js = $SERVER"
sm=$(md5of "$SERVER"); say "current server.js md5: $sm"
am0=""; im0=""
if [ -f "$APP" ]; then am0=$(md5of "$APP"); say "app.js (NOT touched) = $APP md5 $am0"; fi
if [ -f "$INDEX" ]; then im0=$(md5of "$INDEX"); say "index.html (NOT touched) = $INDEX md5 $im0"; fi

# ---- 2. idempotency ----
if [ "$sm" = "$NEW_SERVER_MD5" ]; then
  say "REFUSE: already applied (server.js is at the maint1/bb10i md5). Nothing to do. Click Republish if not done yet."; exit 0
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (bb10g)"
say "live server.js md5 matches bb10g: ok"

# ---- 3. get + verify the patch scripts ----
W=$(mktemp -d /tmp/deploy-maint1.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_bb10i.py "$SHA_PATCH_BB10I"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"
python3 "$P/patch_bb10i.py" "$S" || die "bb10i patch script failed"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
say "node --check server.js: ok (scratch)"
rs=$(md5of "$S/server.js")
[ "$rs" = "$NEW_SERVER_MD5" ] || die "scratch server.js md5 $rs != expected $NEW_SERVER_MD5"
[ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js sha256 mismatch"
say "scratch result matches expected md5/sha256: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install ----
TS=$(date +%Y%m%d-%H%M%S)
cp -p "$SERVER" "$SERVER.$TS.bak-maint1" || die "backup failed for $SERVER"; [ "$(md5of "$SERVER.$TS.bak-maint1")" = "$sm" ] || die "backup verify failed for $SERVER"
say "backup: $SERVER.$TS.bak-maint1"
cp "$S/server.js" "$SERVER.new-maint1" || die "staging copy failed (live file still untouched)"
mv -f "$SERVER.new-maint1" "$SERVER" || { echo "[deploy-maint1] ERROR during install; restore from $SERVER.$TS.bak-maint1" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$SERVER" || { echo "[deploy-maint1] ERROR: node --check failed after install; restore from $SERVER.$TS.bak-maint1" >&2; exit 1; }
fs=$(md5of "$SERVER")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
[ -f "$APP" ] && echo "app.js     md5 $(md5of "$APP")  (untouched)"
[ -f "$INDEX" ] && echo "index.html md5 $(md5of "$INDEX")  (untouched)"
ok=1
[ "$fs" = "$NEW_SERVER_MD5" ] || ok=0
[ -z "$am0" ] || [ "$(md5of "$APP")" = "$am0" ] || ok=0
[ -z "$im0" ] || [ "$(md5of "$INDEX")" = "$im0" ] || ok=0
if [ "$ok" = "1" ]; then
  say "DONE: server.js matches expected; app.js and index.html unchanged. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-maint1] ERROR: final md5s differ from expected; restore from $SERVER.$TS.bak-maint1 and DO NOT republish" >&2; exit 1
fi
