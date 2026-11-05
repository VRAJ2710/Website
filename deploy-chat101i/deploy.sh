#!/usr/bin/env bash
# deploy-chat101i: revise only /research/bank-rate-energy-shock-sterling-gold/ on the LIVE chat101h build.
# Live base after chat101h: server 6077bef9, app 6c8ddd1b, index e5ab1af0. Line 1 stays false.
# Touches server.js only. app.js, index.html, c93.css, the service worker and the other two articles stay.
# Does NOT: start the server, npm, git, Stripe, the database, or CI.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/6650acf4ddf0fe3d3d69fad72ef49038cd1ba523/deploy-chat101i"

LIVE_SERVER_MD5=6077bef9728ffe5b26d8d6fcb887294b
LIVE_APP_MD5=6c8ddd1be4db078df1de146163f99b11
LIVE_APP_SHA256=80954f1cfde5add82ee75d9b783e3740c799e1fb8237bc8f01881a5514fbf989
LIVE_INDEX_MD5=e5ab1af080974da456e086a1835d1e7b
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550
PHOTO_REL="assets/founder.webp"
PHOTO_SHA256=fe56cbdeba4feb5aee61a1dc175aa1e67df85f3807cd3276e1aff0d501eee08f
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MANIFEST=(
  "patch_c101i.py 938beb5f3d7ee0b967f9ed657bee85a2a108d6bbbd036eb09db54686a5ff21fa"
  "old_bank.frag 333170c1957dbfde1be7f45b57cc45b58c0cced520de8faab927e4811f044f52"
  "new_bank.frag e66ac2bcfc44ab311a18eb62b127b04d9d7411c6ea1abc0540c0cd7a0c6c0ec1"
  "css_old.frag d373b97494ffead9612421305e351f57eafd31629d272c4b04e8e91a09491b5b"
  "css_new.frag bb8afbbdd66ca2b3fe56c1a8f9c5652f418b6343879bb0eb261cc461f4c97a22"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat101i] $*"; }
die(){ echo "[deploy-chat101i] ABORT: $*" >&2; echo "[deploy-chat101i] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

find_one(){ local name="$1" want="$2" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' -not -path '*/deploy-final*' -not -path '*/deploy-reopen*' -not -path '*/deploy-chat1*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"; m=$(md5of "$p")
    [ "$m" = "$want" ] && { echo "$p"; return 0; }
  done; echo "$first"; }
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"; PHOTO="$SDIR/$PHOTO_REL"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "current md5: server $sm | app $am | index $im"
if ls "$SERVER".*.bak-chat101i >/dev/null 2>&1 || grep -q "chat101i: bank-rate article" "$SERVER" 2>/dev/null; then
  say "REFUSE: deploy-chat101i is already applied (or a .bak-chat101i backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected chat101h result $LIVE_SERVER_MD5"
[ "$am" = "$LIVE_APP_MD5" ] && [ "$(sha256of "$APP")" = "$LIVE_APP_SHA256" ] || die "app.js is not the chat101h build $LIVE_APP_MD5"
[ "$im" = "$LIVE_INDEX_MD5" ] || die "index.html md5 $im != expected chat101h result $LIVE_INDEX_MD5"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or changed ($CSS)"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ -f "$PHOTO" ] && [ "$(sha256of "$PHOTO")" = "$PHOTO_SHA256" ] || die "$PHOTO missing or changed"
SW="$SDIR/sw.js"; SW_BEFORE=""
if [ -f "$SW" ]; then SW_BEFORE=$(md5of "$SW"); say "sw.js md5 $SW_BEFORE (must stay unchanged)"; fi
say "live md5s match the chat101h build: ok"

W=$(mktemp -d /tmp/deploy-chat101i.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done
grep -inE 'create table|alter table|drop table|create index|drop index|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
LON_RE='Vraj Patel,'
LON_RE="${LON_RE}[[:space:]]*London"
grep -qiE "$LON_RE" "$P"/* && die "patch contains a London byline"
say "London byline grep: none"

cp "$SERVER" "$S/server.js"; cp "$S/server.js" "$S/server.js.base"
python3 "$P/patch_c101i.py" "$S/server.js" "$P/old_bank.frag" "$P/new_bank.frag" "$P/css_old.frag" "$P/css_new.frag" || die "patch_c101i failed (live files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
python3 "$P/patch_c101i.py" --check "$S/server.js.base" "$S/server.js" "$P/old_bank.frag" "$P/new_bank.frag" "$P/css_old.frag" "$P/css_new.frag" || die "replacement check failed (live files untouched)"
grep -q '\$108 per barrel' "$S/server.js" && grep -q '216 pence per therm' "$S/server.js" && grep -q 'one-for-now' "$S/server.js" && grep -q '21 May 2019' "$S/server.js" || die "checked facts or the other articles are missing"
grep -q "chat101i: bank-rate article" "$S/server.js" && grep -q "Capital Sustainability Monitor" "$S/server.js" || die "marker or monitor text missing"
[ "$(md5of "$APP")" = "$LIVE_APP_MD5" ] && [ "$(md5of "$INDEX")" = "$LIVE_INDEX_MD5" ] || die "app.js or index.html changed before install"
say "scratch build: only the Bank Rate article and its table helper changed"
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

TS=$(date +%Y%m%d-%H%M%S)
cp -p "$SERVER" "$SERVER.$TS.bak-chat101i" || die "backup failed"
[ "$(md5of "$SERVER.$TS.bak-chat101i")" = "$LIVE_SERVER_MD5" ] || die "backup verify failed"
say "backup: $SERVER.$TS.bak-chat101i"
cp "$S/server.js" "$SERVER.new-chat101i" || die "staging copy failed (live file untouched)"
RB="restore server.js from $SERVER.$TS.bak-chat101i and DO NOT republish"
mv -f "$SERVER.new-chat101i" "$SERVER" || { echo "[deploy-chat101i] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-chat101i] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat101i] ERROR: line 1 changed; $RB" >&2; exit 1; }
[ "$(md5of "$APP")" = "$LIVE_APP_MD5" ] && [ "$(md5of "$INDEX")" = "$LIVE_INDEX_MD5" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || { echo "[deploy-chat101i] ERROR: a file that must stay unchanged was modified; $RB" >&2; exit 1; }
if [ -n "$SW_BEFORE" ] && [ "$(md5of "$SW")" != "$SW_BEFORE" ]; then echo "[deploy-chat101i] ERROR: sw.js changed; $RB" >&2; exit 1; fi
echo "server.js md5 $(md5of "$SERVER")"
echo "server.js sha256 $(sha256of "$SERVER")"
echo "app.js md5 $(md5of "$APP") (unchanged)"
echo "index.html md5 $(md5of "$INDEX") (unchanged)"
head -n 1 "$SERVER"
say "DONE: server.js is the chat101h file with the Bank Rate article replaced. app.js and index.html were not written. The server was NOT started."
say "To undo: restore server.js from $SERVER.$TS.bak-chat101i."
rm -rf "$W"
exit 0
