#!/usr/bin/env bash
# deploy-chat108saferxC: v3 home PREVIEW fix (27 Nov 2026). APPLY ORDER: after deploy-chat108saferxB (A, credits, softgate, r6p
# before it). Appends one self-contained block after the chat108saferxB block; no existing byte changes.
# Only the preview changes (GET /?preview=v3 or the td_v3p=1 cookie, page already built by B, plus the renderer at its new
# cache-busted URL /__v3p/home.js?v=chat108saferxC). The normal homepage, /__v3p/home.js at its old URL and every other route
# are untouched.
#  - Gold futures chart card: latest delayed futures quote is the main figure (Delayed label, UK time), 3-month change measured
#    to it on the same continuous front-month series, last completed close on a secondary line; no fresh quote = close, "Last close".
#  - Key prices, five things that moved, range bars, chart tiles: a figure dated before today (UK) reads "Last close", not "Delayed".
#  - No DB, DDL, payments, email, secret, config or network change. Does NOT start the server, npm, git, or republish.
# Guards: post-B server.js is 2,500,286 B with md5 4228d5923590382ab8f3dc71830139c2 (dev, 27 Nov 2026), ends byte-exact with
#   the chat108saferxB block (bd06d3bc...), B block and B TAG once, A TAG once, softgate/r6p/credits/v3home2 once, no
#   chat108saferxC yet. app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389 (left unchanged).
# Usage (project folder, Replit Shell): bash deploy.sh --measure | --dry-run | (no flag to apply)
set -u
PAYLOAD_COMMIT=80b851709abf2dac8cc315d0adc211b5af817e8f
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat108saferxC"
TAG=chat108saferxC
APP_MD5=8726da25f103e569c25f13ea1b155d66
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
SERVER_BYTES=2500286
if [ -n "${C108_LOCAL_PAYLOAD:-}" ] && [ -n "${C108_TEST_BYTES:-}" ]; then SERVER_BYTES="$C108_TEST_BYTES"; fi
SERVER_MD5=4228d5923590382ab8f3dc71830139c2
if [ -n "${C108_LOCAL_PAYLOAD:-}" ] && [ -n "${C108_TEST_MD5:-}" ]; then SERVER_MD5="$C108_TEST_MD5"; fi
ATTACH='[chat108saferxC] preview attached'
MANIFEST=(
  "patch_chat108saferxC.py c4f952cfa5f56a3a903a871056c4966a62ab3de9cb3bfe8116c5658e9428c59a"
  "server_block_chat108saferxC.js 99d9ec80c7415022785287874631115494887a1e8edbf24c4a15b8785dc246c5"
  "server_block_chat108saferxB.js bd06d3bcd0e0e0c04728d11cbe130a208c47a45de921a947cb9c967a7569492c"
)
DRY=0; MEASURE=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --measure) MEASURE=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-$TAG] $*"; }
die(){ echo "[deploy-$TAG] ABORT: $*" >&2; echo "[deploy-$TAG] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
echo "$PAYLOAD_COMMIT" | grep -qE '^[0-9a-f]{40}$' || [ -n "${C108_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not a 40-character commit"
for t in node python3 md5sum sha256sum curl cp grep awk mktemp; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;; esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); sb=$(wc -c < "$SERVER" | tr -d ' ')
cnt(){ grep -cF "$1" "$SERVER"; }
say "project folder: $ROOT"
say "server.js md5 $sm"
say "server.js sha256 $(sha256of "$SERVER")"
say "server.js bytes $sb (guard $SERVER_BYTES)"
say "app.js md5 $am (guard $APP_MD5) | $(wc -c < "$APP" | tr -d ' ') bytes"
say "index.html md5 $im (guard $INDEX_MD5) | $(wc -c < "$INDEX" | tr -d ' ') bytes"
say "markers: softgate attach $(cnt '[chat106softgate] attached') | VERIFY_ENFORCE=false $(cnt 'const VERIFY_ENFORCE = false;') | r6p attach $(cnt '[c102r6p] scrub attached') | r6o attach $(cnt '[c102r6o] scrub attached') | v3home2 attach $(cnt '[chat105v3home2] preview attached') | credits TAG $(cnt 'var TAG = "chat107credits";') | A TAG $(cnt 'var TAG = "chat108saferxA";') | B TAG $(cnt 'var TAG = "chat108saferxB";') | $TAG block $(cnt 'var TAG = "chat108saferxC";')"
for b in "$SERVER".*.bak-chat108saferxB; do [ -f "$b" ] && say "backup present: $(basename "$b") md5 $(md5of "$b")"; done
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing downloaded, nothing changed."; exit 0; fi
if grep -qF 'var TAG = "chat108saferxC";' "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$am" = "$APP_MD5" ] || die "app.js md5 $am is not the guarded dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "index.html md5 $im is not the guarded dev index $INDEX_MD5"
[ "$sb" = "$SERVER_BYTES" ] || die "server.js is $sb bytes, not the post-B size $SERVER_BYTES"
[ "$sm" = "$SERVER_MD5" ] || die "server.js md5 $sm is not the pinned $SERVER_MD5"
[ "$(cnt '[chat106softgate] attached')" = "1" ] || die "softgate is not applied exactly once"
[ "$(cnt 'var TAG = "chat107credits";')" = "1" ] || die "chat107credits is not applied exactly once"
[ "$(cnt '[chat105v3home2] preview attached')" = "1" ] || die "chat105v3home2 is not present exactly once"
[ "$(cnt 'var TAG = "chat108saferxA";')" = "1" ] || die "chat108saferxA is not applied exactly once"
[ "$(cnt 'var TAG = "chat108saferxB";')" = "1" ] || die "chat108saferxB is not applied exactly once"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
if [ -n "${C108_LOCAL_PAYLOAD:-}" ]; then say "LOCAL TEST payload from $C108_LOCAL_PAYLOAD"; else say "payload commit: $PAYLOAD_COMMIT"; fi
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${C108_LOCAL_PAYLOAD:-}" ]; then cp "$C108_LOCAL_PAYLOAD/$f" "$P/$f" || die "local payload copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate |process\.env|stripe|child_process' "$P/server_block_chat108saferxC.js" && die "the block mentions DDL, env, payments or child_process"
say "DDL/env/payments grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat108saferxC.py" "$S/server.js" "$P/server_block_chat108saferxC.js" "$P/server_block_chat108saferxB.js" "$SERVER_BYTES" || die "patch refused (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
cmp -n "$sb" "$S/server.js" "$SERVER" >/dev/null || die "existing bytes changed in scratch"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "0" ] || die "attach text present literally (expected built at runtime)"
[ "$(grep -cF 'var TAG = "chat108saferxC";' "$S/server.js")" = "1" ] && [ "$(grep -cF 'var TAG = "chat108saferxB";' "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG block"
[ "$(grep -ciE 'alter table' "$S/server.js")" = "$(grep -ciE 'alter table' "$SERVER")" ] || die "DDL count changed"
NS=$(md5of "$S/server.js")
say "scratch build ok: $sb existing bytes unchanged, $TAG block appended."
echo "scratch server.js md5 $NS"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch server.js bytes $(wc -c < "$S/server.js" | tr -d ' ')"
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
say "DONE: server.js md5 $(md5of "$SERVER") ($(wc -c < "$SERVER" | tr -d ' ') bytes; was $sm). app.js and index.html unchanged. Backups *.$TS.$SUFF"
say "Next: restart ONLY the 'Start application' workflow; expect exactly one '$ATTACH' log line. Nothing was republished."
say "Check: /?preview=v3 shows the new hero; / (no flag) and /?preview=off are unchanged."
say "To undo: cp server.js.$TS.$SUFF server.js and restart the workflow."
rm -rf "$W"
