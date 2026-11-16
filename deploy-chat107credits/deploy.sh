#!/usr/bin/env bash
# deploy-chat107credits: data-source credits (Vraj, 16 Nov). APPLY ORDER: after deploy-chat102r6p and deploy-chat106softgate
# (both from ebeeb7c0). Appends one self-contained block after the r6p last-write scrub; no existing byte changes.
#  - Footer, every page: "This product uses FRED(R) data but is not endorsed or certified by the Federal Reserve Bank of St. Louis."
#    The same notice plus a short credits note on /methodology, under the Sources table.
#  - Under each card that shows a FRED series: "<original source>, <FRED title> [ID], retrieved from FRED, Federal Reserve Bank
#    of St. Louis; https://fred.stlouisfed.org/series/ID, <UK date the data was fetched>". The ID appears only in that line.
#  - Next to any fiscaldata.treasury.gov link: "Source: U.S. Treasury, Fiscal Data" (none found on 16 Nov).
#  - FRED requests are spaced to at most 2 per second; cached FRED data older than 30 days is dropped (6-hourly sweep).
#  - No DB, DDL, Stripe, email, secret or config change. Does NOT start the server, npm, git, or republish.
# Guards: post-softgate server.js is 2,429,645 B (its md5 was not captured exactly, so the size and structure are pinned):
#   ends with the r6p scrub byte-exact (3f02d689..., 33,579 B), preceded by the chat105v3home2 block byte-exact (1da4d654...),
#   exactly one '[chat106softgate] attached', one 'const VERIFY_ENFORCE = false;', one r6p attach, no r6o attach, no chat107credits.
#   app.js 8726da25f103e569c25f13ea1b155d66, index.html 23e26d5287a773dadaf3fd2c40deb389 (left unchanged).
#   Set SERVER_MD5 below (or C107_SERVER_MD5 in the shell) to also pin the exact md5 once --measure has printed it.
# Usage (project folder, Replit Shell): bash deploy.sh --measure | --dry-run | (no flag to apply)
set -u
PAYLOAD_COMMIT=3a954cfba1cd41dfadb95c38187e969de4c573d9
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat107credits"
TAG=chat107credits
APP_MD5=8726da25f103e569c25f13ea1b155d66
INDEX_MD5=23e26d5287a773dadaf3fd2c40deb389
SERVER_BYTES=2429645
SERVER_MD5="${C107_SERVER_MD5:-}"
ATTACH='[chat107credits] attached'
MANIFEST=(
  "patch_chat107credits.py 667fb068fd2c79a364de382cf6535cc44fd05de93264f9cee8a1100b6f19c4c7"
  "server_block_chat107credits.js 10ff789f878eac48e8f02a442053c7333986740d67d3155276617b25bdef7e25"
  "server_block_c102r6p.js 3f02d689fe58951deb789b0809bcecf78fdb2252abe89fbe6af8a722a90b88a8"
  "server_block_chat105v3home2.js 1da4d65430058dc310a42642ca65a95cf84b8e3dd03e82182335f9a916e9340f"
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
for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;; esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); sb=$(wc -c < "$SERVER" | tr -d ' ')
say "project folder: $ROOT"
say "server.js md5 $sm"
say "server.js sha256 $(sha256of "$SERVER")"
say "server.js bytes $sb (guard $SERVER_BYTES)"
say "app.js md5 $am (guard $APP_MD5) | $(wc -c < "$APP" | tr -d ' ') bytes"
say "index.html md5 $im (guard $INDEX_MD5) | $(wc -c < "$INDEX" | tr -d ' ') bytes"
say "markers: softgate attach $(grep -cF '[chat106softgate] attached' "$SERVER") | VERIFY_ENFORCE=false $(grep -cF 'const VERIFY_ENFORCE = false;' "$SERVER") | r6p attach $(grep -cF '[c102r6p] scrub attached' "$SERVER") | r6o attach $(grep -cF '[c102r6o] scrub attached' "$SERVER") | v3home2 attach $(grep -cF '[chat105v3home2] preview attached' "$SERVER") | $TAG block $(grep -cF 'var TAG = "chat107credits";' "$SERVER")"
for b in "$SERVER".*.bak-chat102r6p "$SERVER".*.bak-chat106softgate; do [ -f "$b" ] && say "backup present: $(basename "$b") md5 $(md5of "$b")"; done
if [ "$MEASURE" = "1" ]; then say "MEASURE only: nothing downloaded, nothing changed."; exit 0; fi
[ "$PAYLOAD_COMMIT" != "0000000000000000000000000000000000000000" ] || [ -n "${C107_LOCAL_PAYLOAD:-}" ] || die "PAYLOAD_COMMIT is not pinned"
if grep -qF 'var TAG = "chat107credits";' "$SERVER"; then say "REFUSE: $TAG is already applied. Nothing changed."; exit 0; fi
[ "$am" = "$APP_MD5" ] || die "app.js md5 $am is not the guarded dev app $APP_MD5"
[ "$im" = "$INDEX_MD5" ] || die "index.html md5 $im is not the guarded dev index $INDEX_MD5"
[ "$sb" = "$SERVER_BYTES" ] || die "server.js is $sb bytes, not the post-softgate size $SERVER_BYTES"
[ -z "$SERVER_MD5" ] || [ "$sm" = "$SERVER_MD5" ] || die "server.js md5 $sm is not the pinned $SERVER_MD5"
[ "$(grep -cF '[chat106softgate] attached' "$SERVER")" = "1" ] || die "softgate is not applied exactly once"
[ "$(grep -cF 'const VERIFY_ENFORCE = false;' "$SERVER")" = "1" ] || die "VERIFY_ENFORCE = false is not present exactly once"
W=$(mktemp -d /tmp/deploy-$TAG.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
if [ -n "${C107_LOCAL_PAYLOAD:-}" ]; then say "LOCAL TEST payload from $C107_LOCAL_PAYLOAD"; else say "payload commit: $PAYLOAD_COMMIT"; fi
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "${C107_LOCAL_PAYLOAD:-}" ]; then cp "$C107_LOCAL_PAYLOAD/$f" "$P/$f" || die "local payload copy failed: $f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  got=$(sha256of "$P/$f"); [ "$got" = "$h" ] || die "sha256 mismatch for $f: got $got expected $h"
  say "payload ok: $f $got"; done
grep -inE 'create table|alter table|drop table|truncate |process\.env|stripe' "$P/server_block_chat107credits.js" "$P/patch_chat107credits.py" && die "the credits payload mentions DDL, env or Stripe"
say "DDL/env/Stripe grep: none"
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
python3 "$P/patch_chat107credits.py" "$S/server.js" "$P/server_block_chat107credits.js" "$P/server_block_c102r6p.js" "$P/server_block_chat105v3home2.js" "$SERVER_BYTES" || die "patch refused (project-root files untouched)"
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
cmp -n "$sb" "$S/server.js" "$SERVER" >/dev/null || die "existing bytes changed in scratch"
[ "$(md5of "$S/app.js")" = "$am" ] && [ "$(md5of "$S/index.html")" = "$im" ] || die "app.js or index.html changed"
[ "$(grep -cF "$ATTACH" "$S/server.js")" = "0" ] || die "attach text present literally (expected built at runtime)"
[ "$(grep -cF 'var TAG = "chat107credits";' "$S/server.js")" = "1" ] || die "scratch server.js does not have exactly one $TAG block"
[ "$(grep -cF '[chat106softgate] attached' "$S/server.js")" = "1" ] && [ "$(grep -cF '[c102r6p] scrub attached' "$S/server.js")" = "1" ] || die "softgate or r6p attach count changed"
[ "$(grep -ciE 'alter table' "$S/server.js")" = "$(grep -ciE 'alter table' "$SERVER")" ] || die "DDL count changed"
NS=$(md5of "$S/server.js")
say "scratch build ok: $sb existing bytes unchanged, credits block appended."
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
say "To undo: cp server.js.$TS.$SUFF server.js and restart the workflow."
rm -rf "$W"
