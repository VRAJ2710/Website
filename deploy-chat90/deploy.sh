#!/usr/bin/env bash
# deploy-chat90: brand rename "The Dispatch Markets" -> "The Dispatch Market" on top of live chat89, in the Replit Shell.
# Edits server.js, app.js, index.html (token app.js?v=chat89 -> chat90) and, if present, manifest.json, llms.txt, og-card.png.
# Does NOT: run the server, npm start, git, DB, .replit, package.json, env vars, Stripe. Click Republish yourself afterwards.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat90-brand}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-chat90"

LIVE_SERVER_MD5=03fd66ca2c1ddac8417fcb0ed8e37414   # chat89
LIVE_APP_MD5=d45e0c8d6cb77fceb437ca9db6dfa73c      # chat89
LIVE_INDEX_MD5=8987d0ba0999841844da72d9381ad2f0    # chat89 (v=chat89)
NEW_SERVER_MD5=357d8300e6041fbee752ff6f10ee0a93
NEW_SERVER_SHA256=e45f00b020c5eb4986ba9ed938ac5e719624b57292e7dc786a0b0d078cc11cff
NEW_APP_MD5=9caddff097af8e72adab562746973603
NEW_APP_SHA256=5e7e6c6dc2cacb482d6366fbbfdbced8e9d55e8007e098b85e5eb246fcaec474
NEW_INDEX_MD5=65a78b0a630a306780d22708a2120590
NEW_INDEX_SHA256=5fe42feae40a13a2400d940569e1e09dbc48aa0c6de59c913e4f258db265ab75
SHA_PATCH_BRAND=4650c6b0ebe804c934f9739617dd8e26a8d705fac63ade6247df76d60fe11d26
SHA_OGCARD_NEW=cae73e252de7e7aa31b7183fc2624e9c89634708e1ec9192258dea5b7fef8a70
OGCARD_OLD_MD5=a2bd86fb5760361cc879178b1302d38c    # known live og-card.png (replaced only if it matches)
MANIFEST_OLD_MD5=99759344788b05ccb3b448a28cc6934d  # informational
LLMS_OLD_MD5=b4dba7c8029ea83b9d92dcc36beb90e6      # informational

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done

say(){ echo "[deploy-chat90] $*"; }
die(){ echo "[deploy-chat90] ABORT: $*" >&2; echo "[deploy-chat90] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }

for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])'); say "node $(node -v), python $PYV"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"

# ---- 1. locate the live files ----
find_one(){ # name expected_md5
  local name="$1" want="$2" first="" p
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat90/*' 2>/dev/null | sort); do
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
SD="$(dirname "$SERVER")"   # static files live next to server.js
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "current md5: server $sm | app $am | index $im"

# ---- 2. idempotency ----
if [ "$sm" = "$NEW_SERVER_MD5" ] && [ "$am" = "$NEW_APP_MD5" ] && [ "$im" = "$NEW_INDEX_MD5" ]; then
  say "REFUSE: already applied (all three files are at the chat90 md5s). Nothing to do. Click Republish if not done yet."; exit 0
fi
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ]; then
  die "PARTIAL state: some files already patched, some not (server $sm, app $am, index $im). Do not continue; report this."
fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat89)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat89)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat89)"
say "live md5s match chat89: ok"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"

# ---- 3. get + verify the patch files ----
W=$(mktemp -d /tmp/deploy-chat90.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
getp(){ # file sha
  if [ -n "$HERE" ] && [ -f "$HERE/$1" ] && [ "$(sha256of "$HERE/$1")" = "$2" ]; then cp "$HERE/$1" "$P/$1"
  else curl -fsSL --retry 2 "$BASE_URL/$1" -o "$P/$1" || die "download failed: $BASE_URL/$1"; fi
  [ "$(sha256of "$P/$1")" = "$2" ] || die "sha256 mismatch for $1 (got $(sha256of "$P/$1"), want $2)"
  say "patch file ok: $1 sha256 ${2:0:16}…"
}
getp patch_brand.py "$SHA_PATCH_BRAND"; getp og-card.png "$SHA_OGCARD_NEW"

# ---- 4. dry run in scratch ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
STATIC_CHANGED=""
for sn in manifest.json llms.txt; do [ -f "$SD/$sn" ] && cp "$SD/$sn" "$S/$sn" && say "static present: $SD/$sn (md5 $(md5of "$SD/$sn"))"; done
[ -f "$S/manifest.json" ] && [ "$(md5of "$S/manifest.json")" != "$MANIFEST_OLD_MD5" ] && say "note: manifest.json differs from the known version; only the brand string is replaced"
[ -f "$S/llms.txt" ] && [ "$(md5of "$S/llms.txt")" != "$LLMS_OLD_MD5" ] && say "note: llms.txt differs from the known version; only the brand string is replaced"
python3 "$P/patch_brand.py" "$S/server.js" "$S/app.js" "$S/index.html" --static "$S" || die "brand patch script failed"
for sn in manifest.json llms.txt; do [ -f "$S/$sn" ] && ! cmp -s "$S/$sn" "$SD/$sn" && STATIC_CHANGED="$STATIC_CHANGED $sn"; done
OG_DO=0
if [ -f "$SD/og-card.png" ]; then
  if [ "$(md5of "$SD/og-card.png")" = "$OGCARD_OLD_MD5" ]; then OG_DO=1; say "og-card.png matches known version: will replace (MARKETS -> MARKET in the image)"
  else say "og-card.png differs from the known version: LEFT AS IS (still says MARKETS; needs a new image)"; fi
else say "og-card.png not found in $SD: skipped"; fi
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
if grep -n -i -E 'dispatch(\s|·|<[^>]*>)+markets\b' "$S/server.js" "$S/app.js" "$S/index.html" $( for sn in manifest.json llms.txt; do [ -f "$S/$sn" ] && echo "$S/$sn"; done ) >/dev/null 2>&1; then die "brand 'Dispatch Markets' still present in scratch output"; fi
say "no brand 'Dispatch Markets' left in server.js / app.js / index.html / manifest.json / llms.txt: ok"
ch=$(diff "$INDEX" "$S/index.html" | grep -c '^[<>]'); [ "$ch" = "30" ] || die "index.html differs by $ch lines (expected 30 = 15 changed lines)"
diff "$INDEX" "$S/index.html" | grep -q 'app.js?v=chat90' || die "index.html lacks the chat90 token"
say "index.html: 15 changed lines incl. app.js?v=chat89 -> chat90: ok"

if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 5. backup + install ----
TS=$(date +%Y%m%d-%H%M%S)
BK="$SERVER $APP $INDEX"; for sn in $STATIC_CHANGED; do BK="$BK $SD/$sn"; done; [ "$OG_DO" = "1" ] && BK="$BK $SD/og-card.png"
for f in $BK; do cp -p "$f" "$f.$TS.bak-chat90" || die "backup failed for $f"; [ "$(md5of "$f.$TS.bak-chat90")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; done
say "backups written: *.$TS.bak-chat90 for: $BK"
cp "$S/server.js" "$SERVER.new-chat90" && cp "$S/app.js" "$APP.new-chat90" && cp "$S/index.html" "$INDEX.new-chat90" || die "staging copy failed (live files still untouched)"
for sn in $STATIC_CHANGED; do cp "$S/$sn" "$SD/$sn.new-chat90" || die "staging copy failed for $sn"; done
[ "$OG_DO" = "1" ] && { cp "$P/og-card.png" "$SD/og-card.png.new-chat90" || die "staging copy failed for og-card.png"; }
mv -f "$SERVER.new-chat90" "$SERVER" && mv -f "$APP.new-chat90" "$APP" && mv -f "$INDEX.new-chat90" "$INDEX" || { echo "[deploy-chat90] ERROR during install; restore from *.$TS.bak-chat90" >&2; exit 1; }
for sn in $STATIC_CHANGED; do mv -f "$SD/$sn.new-chat90" "$SD/$sn" || { echo "[deploy-chat90] ERROR installing $sn; restore from *.$TS.bak-chat90" >&2; exit 1; }; done
[ "$OG_DO" = "1" ] && { mv -f "$SD/og-card.png.new-chat90" "$SD/og-card.png" || { echo "[deploy-chat90] ERROR installing og-card.png; restore from backup" >&2; exit 1; }; }

# ---- 6. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat90] ERROR: node --check failed after install; restore from *.$TS.bak-chat90" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX")
echo "server.js  md5 $fs  sha256 $(sha256of "$SERVER")"
echo "app.js     md5 $fa  sha256 $(sha256of "$APP")"
echo "index.html md5 $fi_  sha256 $(sha256of "$INDEX")"
for sn in manifest.json llms.txt og-card.png; do [ -f "$SD/$sn" ] && echo "$sn md5 $(md5of "$SD/$sn")"; done
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ]; then
  say "DONE: all three files match expected. Server was NOT started. Next: click Republish."
  rm -rf "$W"; exit 0
else
  echo "[deploy-chat90] ERROR: final md5s differ from expected; restore from *.$TS.bak-chat90 and DO NOT republish" >&2; exit 1
fi
