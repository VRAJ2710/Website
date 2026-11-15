#!/usr/bin/env bash
# deploy-chat106softgate: email verification becomes a reminder, not a gate (Vraj, 15 Nov: option A,
# "keep checkout open with a reminder until it works").
#  - Sign-up, sign-in and checkout are never blocked because email_verified is false. They are blocked only if
#    the code constant VERIFY_ENFORCE (default false) is set to true. No env, secret or config change.
#  - Unverified readers see "Please verify your email" with a resend button on the checkout page and on the
#    signed-in app pages (account/settings, checkout hand-off). New routes: POST /__auth/verify/resend,
#    GET /__auth/verify/status, GET /__auth/verify/reminder.js.
#  - A failed send never stops sign-up or checkout; each failure is logged once.
#  - The email_verified column, the verification emails and the Ask order are unchanged. No DDL, no Stripe change.
# APPLY ORDER: after deploy-chat102r6p. Refuses on the pre-r6p root (r6o scrub still present).
# Guards (no fixed post-r6p md5 is known off-box, so the root is pinned by parts, byte-exact):
#   bytes before the chat105v3home2 block = fef1da0 prefix (sha256 8d292999..., 2,332,205 B)
#   then the chat105v3home2 block (sha256 1da4d654..., byte-exact), then the r6p scrub to EOF (b896eb5a..., 33,279 B)
#   prefix + v3home2 + r6o scrub must have md5 7a3aeaf7a9e317ce888e28e4b9d4461a (the pre-r6p dev server)
#   app.js d8ca8562df01bf88c68e4971752e602c, index.html 23e26d5287a773dadaf3fd2c40deb389 (both left unchanged)
# Only bytes before the chat105v3home2 block are edited. Does NOT start the server, npm, git, or republish.
# Usage (project folder, Replit Shell): bash deploy.sh --measure | --dry-run | (no flag to apply)
set -u
PAYLOAD_COMMIT=40e0eb4bdfa4f343f9072c46b63c699d417afd70
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat106softgate"
TAG=chat106softgate
APP_MD5=d8ca8562df01bf88c68e4971752e602c
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
PRE_R6P_MD5=7a3aeaf7a9e317ce888e28e4b9d4461a
PREFIX_SHA=8d29291995dacca242b934ccc5058afc5eb27cbae9d4ccbdc9383b4909a9f7ae
PREFIX_BYTES=2332205
POST_R6P_BYTES=2418347
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102r6c last-write scrub.'
ATTACH='[chat106softgate] attached'
MANIFEST=(
  "patch_chat106softgate.py 9330e3d9a3eef32d3fd7659ca04a6f2e9482713d73a501f566f99817e4ba4f2f"
  "server_block_chat106softgate.js 9d3bf507e515c517a860ca71332f6e755f987319fda68730686724c299c8cfa9"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
  "server_block_c102r6o.js e45d46bf24eca1e3585739491058fc7470b7faffd7ba54600764f90594d63cbc"
  "server_block_c102r6p.js b896eb5a35c3a1e5db30c8ff3143a189b513d1d9c86dc741d370ac76b0449445"
)
DRY=0; MEASURE=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --measure) MEASURE=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-$TAG] $*"; }
die(){ echo "[deploy-$TAG] ABORT: $*" >&2; echo "[deploy-$TAG] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
case "$PAYLOAD_COMMIT" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) die "PAYLOAD_COMMIT is not a 40-character commit" ;;
esac
[ "$PAYLOAD_COMMIT" != "0000000000000000000000000000000000000000" ] || [ -n "${C106SG_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;; esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); sb=$(wc -c < "$SERVER" | tr -d ' ')
say "project folder: $ROOT"
say "root md5: server $sm ($sb bytes) | app $am | index $im"
R6=none
grep -qF '[c102r6p] scrub attached' "$SERVER" && R6=r6p
grep -qF '[c102r6o] scrub attached' "$SERVER" && R6="$R6+r6o"
say "scrub markers $(grep -cF "$MARKER" "$SERVER") | c102 scrub: $R6 | chat105v3home2 attach $(grep -cF '[chat105v3home2] preview attached' "$SERVER") | $TAG attach $(grep -cF "$ATTACH" "$SERVER") | VERIFY_ENFORCE lines $(grep -c 'const VERIFY_ENFORCE = ' "$SERVER")"
[ "$sm" = "$PRE_R6P_MD5" ] && say "note: this is the pre-r6p dev server; apply deploy-chat102r6p first."
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing changed."; exit 0; fi
if grep -qF "$ATTACH" "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$sm" != "$PRE_R6P_MD5" ] || die "deploy-chat102r6p is not applied yet (server.js is still $PRE_R6P_MD5). Apply r6p first, then this installer."
[ "$am" = "$APP_MD5" ] || die "app.js md5 $am is not the guarded dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "index.html md5 $im is not the guarded dev index $INDEX_MD5"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "server.js line 1 is not the maintenance=false line"
[ "$sb" = "$POST_R6P_BYTES" ] || die "server.js is $sb bytes, not the post-r6p size $POST_R6P_BYTES"
[ "$(grep -cF "$MARKER" "$SERVER")" = "1" ] || die "server.js does not contain exactly one scrub marker"
[ "$R6" = "r6p" ] || die "server.js does not carry exactly the r6p scrub (found: $R6)"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
if [ -n "${C106SG_LOCAL_PAYLOAD:-}" ]; then say "LOCAL TEST payload from $C106SG_LOCAL_PAYLOAD"; else say "payload commit: $PAYLOAD_COMMIT"; fi
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${C106SG_LOCAL_PAYLOAD:-}" ]; then cp "$C106SG_LOCAL_PAYLOAD/$f" "$P/$f" || die "local payload copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate ' "$P"/* && die "a patch file mentions DDL"
say "DDL grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat106softgate.py" "$S/server.js" "$P/server_block_chat106softgate.js" "$P/server_block_chat105v3home2.js" "$P/server_block_c102r6o.js" "$P/server_block_c102r6p.js" "$PREFIX_SHA" "$PREFIX_BYTES" "$PRE_R6P_MD5" || die "patch refused (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG attach line"
[ "$(grep -c '^const VERIFY_ENFORCE = false;' "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one VERIFY_ENFORCE = false"
[ "$(grep -cF '[c102r6p] scrub attached' "$S/server.js")" = "1" ] || die "r6p scrub changed in scratch"
[ "$(grep -ciE 'alter table' "$S/server.js")" = "$(grep -ciE 'alter table' "$SERVER")" ] || die "DDL count changed"
NS=$(md5of "$S/server.js")
say "scratch build ok: only bytes before the chat105v3home2 block changed; v3home2 block and r6p scrub byte-identical."
echo "post-r6p server.js md5 (input) $sm"
echo "scratch server.js md5 $NS ($(wc -c < "$S/server.js" | tr -d ' ') bytes; about 2,429,345 expected if the indentation matches the fixture)"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi
[ "$(md5of "$SERVER")" = "$sm" ] || die "server.js changed during the run"
TS=$(date +%Y%m%d-%H%M%S); SUFF="bak-$TAG"
for f in "$SERVER" "$APP" "$INDEX"; do
  cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"
  say "backup: $f.$TS.$SUFF"; done
cp "$S/server.js" "$SERVER.new-$TAG" || die "staging copy failed (project-root files untouched)"
RB="restore server.js from server.js.$TS.$SUFF and DO NOT republish"
mv -f "$SERVER.new-$TAG" "$SERVER" || { echo "[deploy-$TAG] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" || { echo "[deploy-$TAG] ERROR: node --check failed after install; $RB" >&2; exit 1; }
say "DONE: server.js md5 $(md5of "$SERVER") (was $sm). app.js and index.html unchanged. Backups *.$TS.$SUFF"
say "Next: restart ONLY the 'Start application' workflow; expect exactly one '$ATTACH' log line. Nothing was republished."
say "To undo: cp server.js.$TS.$SUFF server.js and restart the workflow."
rm -rf "$W"
