#!/usr/bin/env bash
# deploy-reopen: turns maintenance OFF after deploy-final. It changes ONLY line 1 of server.js:
#   const BB10I_MAINTENANCE_ON = true; ...  ->  const BB10I_MAINTENANCE_ON = false; ...
# Pinned to the deploy-final server.js (md5 + sha256), and checks the sha256 of the result. Backup + node --check.
# Does NOT start or restart the server, publish, or touch app.js/index.html/env/Stripe/DB. Republish only when Vraj says so.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
BASE_SERVER_MD5=ccd31a713886f6638787e0cd7408bb0b
BASE_SERVER_SHA256=1a50d0fa509f9e1b3d51bec1d8dbfbd89ce05d859decd3baaf99eb7790438bc8
OPEN_SERVER_MD5=3c3df45f8e0428fd3bb6c378e0b67c52
OPEN_SERVER_SHA256=a2a7526253640fcd9136a03ecee9eb8fd18ecacfa49cc39866414d8c731230c9
OLD_L1='const BB10I_MAINTENANCE_ON = true; // set false to turn maintenance off (restart to apply)'
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-reopen] $*"; }
die(){ echo "[deploy-reopen] ABORT: $*" >&2; echo "[deploy-reopen] Nothing was changed." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }; sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node md5sum sha256sum head tail cp mktemp; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found"; done
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
SERVER="$ROOT/server.js"; [ -f "$SERVER" ] || die "no server.js in $ROOT"
say "server.js = $SERVER"
sm=$(md5of "$SERVER"); ss=$(sha256of "$SERVER"); say "current md5 $sm"
if [ "$sm" = "$OPEN_SERVER_MD5" ] || ls "$SERVER".*.bak-reopen >/dev/null 2>&1; then say "REFUSE: already reopened (or a .bak-reopen backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$BASE_SERVER_MD5" ] && [ "$ss" = "$BASE_SERVER_SHA256" ] || die "server.js is not the deploy-final build (md5 $sm, want $BASE_SERVER_MD5)"
[ "$(head -n 1 "$SERVER")" = "$OLD_L1" ] || die "line 1 is not the expected maintenance=true line"
W=$(mktemp -d /tmp/deploy-reopen.XXXXXX) || die "mktemp failed"
{ printf '%s\n' "$NEW_L1"; tail -n +2 "$SERVER"; } > "$W/server.js" || die "could not build scratch copy"
[ "$(sha256of "$W/server.js")" = "$OPEN_SERVER_SHA256" ] && [ "$(md5of "$W/server.js")" = "$OPEN_SERVER_MD5" ] || die "scratch result differs from the pinned reopened build"
node --check "$W/server.js" || die "node --check failed (scratch)"
say "scratch: only line 1 changed, sha256 matches, node --check ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: nothing changed. Scratch: $W"; exit 0; fi
TS=$(date +%Y%m%d-%H%M%S); B="$SERVER.$TS.bak-reopen"
cp -p "$SERVER" "$B" && [ "$(md5of "$B")" = "$sm" ] || die "backup failed"; say "backup: $B"
cp "$W/server.js" "$SERVER.new-reopen" && mv -f "$SERVER.new-reopen" "$SERVER" || { echo "[deploy-reopen] ERROR during install; restore from $B" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-reopen] ERROR: node --check failed; restore from $B and DO NOT republish" >&2; exit 1; }
[ "$(sha256of "$SERVER")" = "$OPEN_SERVER_SHA256" ] || { echo "[deploy-reopen] ERROR: result differs; restore from $B" >&2; exit 1; }
echo "server.js md5 $(md5of "$SERVER")"; head -n 1 "$SERVER"
say "DONE: maintenance is OFF in server.js. The server was NOT started. It takes effect on Republish (only when Vraj says so)."
say "To undo: cp \"$B\" \"$SERVER\""; rm -rf "$W"; exit 0
