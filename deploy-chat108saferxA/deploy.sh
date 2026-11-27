#!/usr/bin/env bash
# deploy-chat108saferxA: v3 home PREVIEW, batch A (27 Nov 2026). APPLY ORDER: after deploy-chat102r6p, deploy-chat106softgate
# and deploy-chat107credits. Appends one self-contained block after the chat107credits block; no existing byte changes.
# Only GET / with ?preview=v3 (or the td_v3p=1 cookie) changes; the normal homepage and every other route are untouched.
#  - Full-screen hero (existing kicker, dek, byline; H1 on two lines with a gold gradient) and an arc of 7 tool links.
#  - One signup: the existing free-brief form (endpoint and fields unchanged) moves into a closing band; the v3 duplicate goes.
#  - Slim header (5 links, Sign in, menu); the full-screen menu keeps all 48 links. Swipeable desk tabs to real routes.
#  - Gold reading-progress bar, hero fade-in, card hover lift; all off under prefers-reduced-motion.
#  - No DB, DDL, Stripe, email, secret, config or network change. Does NOT start the server, npm, git, or republish.
# Guards: post-credits server.js is 2,449,079 B (2,429,645 + 19,434), ends byte-exact with the chat107credits block
#   (10ff789f...), contains the chat105v3home2 block once, one softgate attach, one VERIFY_ENFORCE = false, one r6p attach,
#   one credits TAG, no chat108saferxA yet. app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389
#   (left unchanged). The post-credits md5 was never captured, so --measure prints it; C108_SERVER_MD5=<md5> pins it for a run.
# Usage (project folder, Replit Shell): bash deploy.sh --measure | --dry-run | (no flag to apply)
set -u
PAYLOAD_COMMIT=4718a41bd1f7079b4f8f3fbbb886f836a29d8545
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat108saferxA"
TAG=chat108saferxA
APP_MD5=8726da25f103e569c25f13ea1b155d66
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
SERVER_BYTES=2449079
if [ -n "${C108_LOCAL_PAYLOAD:-}" ] && [ -n "${C108_TEST_BYTES:-}" ]; then SERVER_BYTES="$C108_TEST_BYTES"; fi
SERVER_MD5="${C108_SERVER_MD5:-}"
ATTACH='[chat108saferxA] preview attached'
MANIFEST=(
  "patch_chat108saferxA.py aa9aaeb88afbf10fbcb6443d476d312c3d30dcdcca274983a127a0346090eaa2"
  "server_block_chat108saferxA.js 482affe68ca5f333bf8e9f4feb9b13ccfd16ab9213480b25ae3f8517fa63bd8c"
  "server_block_chat107credits.js 10ff789f878eac48e8f02a442053c7333986740d67d3155276617b25bdef7e25"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
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
say "markers: softgate attach $(cnt '[chat106softgate] attached') | VERIFY_ENFORCE=false $(cnt 'const VERIFY_ENFORCE = false;') | r6p attach $(cnt '[c102r6p] scrub attached') | r6o attach $(cnt '[c102r6o] scrub attached') | v3home2 attach $(cnt '[chat105v3home2] preview attached') | credits TAG $(cnt 'var TAG = "chat107credits";') | $TAG block $(cnt 'var TAG = "chat108saferxA";')"
for b in "$SERVER".*.bak-chat107credits; do [ -f "$b" ] && say "backup present: $(basename "$b") md5 $(md5of "$b")"; done
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing downloaded, nothing changed."; exit 0; fi
if grep -qF 'var TAG = "chat108saferxA";' "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$am" = "$APP_MD5" ] || die "app.js md5 $am is not the guarded dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "index.html md5 $im is not the guarded dev index $INDEX_MD5"
[ "$sb" = "$SERVER_BYTES" ] || die "server.js is $sb bytes, not the post-credits size $SERVER_BYTES"
[ -z "$SERVER_MD5" ] || [ "$sm" = "$SERVER_MD5" ] || die "server.js md5 $sm is not the pinned $SERVER_MD5"
[ "$(cnt '[chat106softgate] attached')" = "1" ] || die "softgate is not applied exactly once"
[ "$(cnt 'var TAG = "chat107credits";')" = "1" ] || die "chat107credits is not applied exactly once"
[ "$(cnt '[chat105v3home2] preview attached')" = "1" ] || die "chat105v3home2 is not present exactly once"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
if [ -n "${C108_LOCAL_PAYLOAD:-}" ]; then say "LOCAL TEST payload from $C108_LOCAL_PAYLOAD"; else say "payload commit: $PAYLOAD_COMMIT"; fi
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${C108_LOCAL_PAYLOAD:-}" ]; then cp "$C108_LOCAL_PAYLOAD/$f" "$P/$f" || die "local payload copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate |process\.env|stripe|child_process' "$P/server_block_chat108saferxA.js" && die "the block mentions DDL, env, Stripe or child_process"
say "DDL/env/Stripe grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat108saferxA.py" "$S/server.js" "$P/server_block_chat108saferxA.js" "$P/server_block_chat107credits.js" "$P/server_block_chat105v3home2.js" "$SERVER_BYTES" || die "patch refused (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
cmp -n "$sb" "$S/server.js" "$SERVER" >/dev/null || die "existing bytes changed in scratch"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "0" ] || die "attach text present literally (expected built at runtime)"
[ "$(grep -cF 'var TAG = "chat108saferxA";' "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG block"
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
