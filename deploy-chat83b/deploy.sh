#!/usr/bin/env bash
# deploy-chat83b: CLIENT-ONLY hotfix. Replaces app.js with the bundled chat82 base, applies rt62f (-> chat83b), bumps index.html v=chat83b.
# server.js (bb10d) is only VERIFIED unchanged (md5), never modified or backed up. Run in the Replit Shell.
# Does NOT: run the server, npm start, git, DB, .replit, package.json, env vars, Stripe. Click Republish yourself afterwards.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
#   --dry-run  do everything in a scratch dir and verify, but do not touch the live files.
set -u
REF="${DEPLOY_REF:-deploy/jack-chat83b-rt62f}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat83b"

# ---- expected values ----
LIVE_SERVER_MD5=6a359cecb836848284c2264d13122482   # bb10d (must stay untouched)
LIVE_APP_MD5=ef0ce14cde79cd45a9eae72e2031ece7      # chat83
LIVE_INDEX_MD5=1d6725049d4a819e7a5d268713037bcc    # chat83
BASE_APP_MD5=e45d14a361587253a328c0de1ff4c791      # chat82 app.js (bundled, gzip)
BASE_INDEX_MD5=16c4bade1ff3baf1e7d1f335402d74fa    # chat82 index.html (bundled)
NEW_APP_MD5=f63c681c5f366e2185e36dd7d4ccd23c
NEW_APP_SHA256=9bc65b0ab48fc35ade2c96639747d83af880e5ad896f281b53b55f625206dbd3
NEW_INDEX_MD5=4ef366778c09fe776757f39d083f9ae2
NEW_INDEX_SHA256=a95eecc5b5356ebf061d11e1b240da762e75e455a47a35198da9fddee9e1ab10
SHA_PATCH_RT62F=393823a97af5a33b005dc18611ee1c2f106f12b445f056e61886a6a68ca25a96
SHA_BASE_APP_GZ=e6cd7470dd417155c877e26e09ff58905bf57b3ad09b59e0562170b3a4ef68f0
SHA_BASE_INDEX=eb7dad16a30653695392d61396a44de96aa916dfaf3403a93829925d56a60622

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat83b] $*"; }
die(){ echo "[deploy-chat83b] ABORT: $*" >&2; echo "[deploy-chat83b] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }

for t in node python3 md5sum sha256sum curl cp gzip; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])'); say "node $(node -v), python $PYV"
python3 - <<'PY' || die "python3 >= 3.8 required"
import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)
PY

# ---- 1. locate the live files ----
find_one(){ # name expected_md5 -> prints path of the file with that name whose md5 is expected; else first candidate path
  local name="$1" want="$2" first="" p
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat83*/*' 2>/dev/null | sort); do
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
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected $LIVE_SERVER_MD5 (bb10d; this hotfix never touches the server, so it must already be bb10d)"
if [ "$am" = "$NEW_APP_MD5" ] && [ "$im" = "$NEW_INDEX_MD5" ]; then
  say "REFUSE: already applied (app.js and index.html are at the chat83b md5s; server.js unchanged). Nothing to do. Click Republish if not done yet."; exit 0
fi
if [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ]; then
  die "PARTIAL state: only one of app.js/index.html is already chat83b (app $am, index $im). Do not continue; report this."
fi
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat83)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat83)"
say "live md5s match bb10d server / chat83 client: ok"

# ---- 3. get + verify the patch scripts ----
W=$(mktemp -d /tmp/deploy-chat83b.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_rt62f.py "$SHA_PATCH_RT62F"; getp base-chat82-app.js.gz "$SHA_BASE_APP_GZ"; getp base-chat82-index.html "$SHA_BASE_INDEX"

# ---- 4. dry run in scratch ----
gzip -dc "$P/base-chat82-app.js.gz" > "$S/app.js" || die "gunzip of bundled chat82 app.js failed"
cp "$P/base-chat82-index.html" "$S/index.html"
[ "$(md5of "$S/app.js")" = "$BASE_APP_MD5" ]     || die "bundled chat82 app.js md5 $(md5of "$S/app.js") != $BASE_APP_MD5"
[ "$(md5of "$S/index.html")" = "$BASE_INDEX_MD5" ] || die "bundled chat82 index.html md5 != $BASE_INDEX_MD5"
say "bundled chat82 base verified (app e45d14a3…, index 16c4bade…)"
python3 "$P/patch_rt62f.py" "$S/app.js" "$S/index.html" || die "rt62f patch script failed"
node --check "$S/app.js"    || die "node --check app.js failed (scratch)"
say "node --check app.js: ok (scratch)"
ra=$(md5of "$S/app.js"); ri=$(md5of "$S/index.html")
[ "$ra" = "$NEW_APP_MD5" ]    || die "scratch app.js md5 $ra != expected $NEW_APP_MD5"
[ "$ri" = "$NEW_INDEX_MD5" ]  || die "scratch index.html md5 $ri != expected $NEW_INDEX_MD5"
[ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ]       || die "scratch app.js sha256 mismatch"
[ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html sha256 mismatch"
say "scratch result matches expected md5/sha256: ok"
ch=$(diff "$INDEX" "$S/index.html" | grep -c '^[<>]'); [ "$ch" = "2" ] || die "index.html differs by $ch lines (expected exactly 2: the app.js?v= bump)"
diff "$INDEX" "$S/index.html" | grep -q 'app.js?v=chat83b' || die "index.html change is not the chat83b bump"
say "index.html change = only app.js?v=chat83 -> chat83b: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install (app.js + index.html only) ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-chat83b" || die "backup failed for $f"; [ "$(md5of "$f.$TS.bak-chat83b")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; done
say "backups: $APP.$TS.bak-chat83b (+index.html)"
cp "$S/app.js" "$APP.new-chat83b" && cp "$S/index.html" "$INDEX.new-chat83b" || die "staging copy failed (live files still untouched)"
mv -f "$APP.new-chat83b" "$APP" && mv -f "$INDEX.new-chat83b" "$INDEX" || { echo "[deploy-chat83b] ERROR during install; restore from *.$TS.bak-chat83b" >&2; exit 1; }

# ---- 6. final verification ----
node --check "$APP" || { echo "[deploy-chat83b] ERROR: node --check failed after install; restore from *.$TS.bak-chat83b" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  (unchanged, expected $LIVE_SERVER_MD5)"
echo "app.js     md5 $fa  sha256 $(sha256of "$APP")"
echo "index.html md5 $fi_  sha256 $(sha256of "$INDEX")"
if [ "$fs" = "$LIVE_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ]; then
  say "DONE: app.js + index.html match expected, server.js unchanged. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat83b] ERROR: final md5s differ from expected; restore from *.$TS.bak-chat83b and DO NOT republish" >&2; exit 1
fi
