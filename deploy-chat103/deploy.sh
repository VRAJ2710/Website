#!/usr/bin/env bash
# deploy-chat103g: replace the chat103 block on the staged chat103f root.
# chat102r6, r6b and the r6c last-write scrub stay after it, byte for byte.
# Does NOT start the server, npm, git, or republish. Does not change EXPECT_TAG.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit is the commit that already contains these blobs.
# Do not point this at a commit that only changes deploy.sh.
PAYLOAD_COMMIT=5a20274a6eb3328e67585fab5469195953084aef
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat103"

# Staged root after chat103b, chat102r6, r6b and r6c (cache tag chat103c).
# The chat102r5 block in front of chat103 stays. r6c must remain the last write.
R5_TAIL_SHA256=099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054
BASE_APP_MD5=93644cb45fc3884e7068bf9a902d73e3
BASE_INDEX_MD5=338615e7ece511104855785b67e9c10a
BASE_SERVER_MD5=b2e44157f0a86a38d145072aea5f89b9
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.'
MANIFEST=(
  "patch_c103.py 516ec023add1e63f754d98723ecf7d1c07a482dd2929d52540933b63fb3f1bea"
  "server_block_c103.js ca6e59116d4d6f41a0a37e732fbea55ae39b10bfa2561c242faa761f93393d1c"
  "ddl_c103.sql 90e84a3513161531846a52350f815f88c261a7e6540ac42e9b5e888862820794"
)
DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-chat103] $*"; }
die(){ echo "[deploy-chat103] ABORT: $*" >&2; echo "[deploy-chat103] Nothing was changed in the project-root files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
case "$PAYLOAD_COMMIT" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) die "PAYLOAD_COMMIT is not a 40-character commit" ;;
esac
for t in node python3 md5sum sha256sum curl cp grep; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find project-root server.js; cd into the project folder or pass --dir"; fi
case "$ROOT" in
  *mockup-sandbox*|*/artifacts/mockup*|*/.backups|*/.backups/*|*pre-bb8h*) die "refusing a mockup or backup directory: $ROOT" ;;
esac
SERVER="$ROOT/server.js"; APP="$ROOT/app.js"; INDEX="$ROOT/index.html"
say "project folder: $ROOT"
say "root server.js = $SERVER"
say "root app.js = $APP"
say "root index.html = $INDEX"
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing project-root file $f"; done
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX")
say "root md5: server $sm | app $am | index $im"
[ "$am" = "$BASE_APP_MD5" ] || die "root app.js md5 $am is not the staged chat103c app $BASE_APP_MD5"
[ "$im" = "$BASE_INDEX_MD5" ] || die "root index.html md5 $im is not the staged chat103c index $BASE_INDEX_MD5"
[ -n "$BASE_SERVER_MD5" ] || die "BASE_SERVER_MD5 is empty"
[ "$sm" = "$BASE_SERVER_MD5" ] || die "root server.js md5 $sm is not the staged chat103f server $BASE_SERVER_MD5"
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "project-root server.js line 1 is not the maintenance=false line"
python3 - "$SERVER" "$MARKER" "$R5_TAIL_SHA256" << 'PY' || die "server.js is not the staged chat103 root"
import hashlib, pathlib, sys
server, marker, expect = sys.argv[1:]
text = pathlib.Path(server).read_text(encoding="utf-8")
if text.count(marker) != 1:
    sys.exit("project-root server.js does not contain exactly one chat102 block")
c103 = text.find("\n// chat103 cpi day")
if c103 < 0 or text.find("\n// chat103 cpi day", c103 + 1) >= 0:
    sys.exit("chat103 block is missing or not unique")
start = text.find(marker)
if start < 0 or start > c103:
    sys.exit("chat102 block is not in front of chat103")
tail = text[start:c103 + 1]
got = hashlib.sha256(tail.encode("utf-8")).hexdigest()
if got != expect:
    sys.exit("chat102r5 bytes in front of chat103 hash to " + got + ", not " + expect)
print("staged chat103 root ok; chat102r5 tail kept")
PY

W=$(mktemp -d /tmp/deploy-chat103.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P" "$S"
say "payload commit: $PAYLOAD_COMMIT"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"
  got=$(sha256of "$P/$f")
  [ "$got" = "$h" ] || die "sha256 mismatch for $f from $PAYLOAD_COMMIT: got $got expected $h"
  say "remote payload ok: $f $got"; done
python3 - "$P" << 'PY' || die "DDL check refused the payload"
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
allowed = {"cpi_releases", "cpi_series_values", "cpi_gold_reactions", "cpi_gold_snapshots", "cpi_notice_dismissals"}
banned = re.compile(r"\b(?:alter\s+table|drop\s+table|drop\s+index|truncate|create\s+index)\b", re.I)
bare = re.compile(r"create\s+table(?!\s+if\s+not\s+exists)\b", re.I)
create = re.compile(r"create\s+table\s+if\s+not\s+exists\s+([a-z0-9_]+)", re.I)
found = []
for path in root.iterdir():
    text = path.read_text(encoding="utf-8", errors="replace")
    if banned.search(text) or bare.search(text):
        sys.exit("banned DDL in " + path.name)
    for m in create.finditer(text):
        name = m.group(1).lower()
        if name not in allowed:
            sys.exit("refused statement " + m.group(0))
        found.append(name)
missing = sorted(allowed - set(found))
if missing:
    sys.exit("missing tables " + ",".join(missing))
print("DDL check ok: " + " ".join(sorted(set(found))))
PY
say "DDL check: CREATE TABLE IF NOT EXISTS of the five new tables only"

cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
cp "$S/server.js" "$S/server.js.base"; cp "$S/app.js" "$S/app.js.base"
python3 "$P/patch_c103.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c103.js" || die "patch_c103 failed (project-root files untouched)"
cmp -s "$S/app.js.base" "$S/app.js" || die "app.js changed; chat103d does not edit it, so the cache tag stays chat103c"
cmp -s "$S/index.html" "$INDEX" || die "index.html changed"
python3 - "$S" "$MARKER" "$R5_TAIL_SHA256" << 'PY' || die "scratch disturbed chat102r6c or the chat102r5 prefix"
import hashlib, pathlib, sys
scratch, marker, expect = sys.argv[1:]
root = pathlib.Path(scratch)
old = (root/"server.js.base").read_text(encoding="utf-8")
new = (root/"server.js").read_text(encoding="utf-8")
r6 = "\n// chat102r6 market-reference cache."
r6c = "\n// chat102r6c last-write scrub."
if old.find(r6) < 0 or old.find(r6c) < 0:
    sys.exit("base is missing the r6 anchors")
if new[new.find(r6):] != old[old.find(r6):]:
    sys.exit("bytes from chat102r6 onward changed")
if new[new.find(r6c):] != old[old.find(r6c):]:
    sys.exit("chat102r6c last-write block changed")
if new.count("proto.end = end") != old.count("proto.end = end"):
    sys.exit("a response-end wrapper was added after r6c")
cut = old.find("\n// chat103 cpi day")
if not new.startswith(old[:cut + 1]):
    sys.exit("bytes in front of chat103 changed")
tail = old[old.find(marker):cut + 1]
if hashlib.sha256(tail.encode("utf-8")).hexdigest() != expect:
    sys.exit("chat102r5 tail changed")
if "Year-on-year not published:" not in new[cut:new.find(r6)]:
    sys.exit("year-on-year note missing from the chat103 block")
idx = (root/"index.html").read_text(encoding="utf-8")
if idx.count("app.js?v=chat103c") != 1 or "app.js?v=chat103d" in idx:
    sys.exit("index cache tag is not still chat103c")
print("r6c last-write kept; chat103 block replaced")
PY
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
grep -q "/api/c103/cpi" "$S/server.js" || die "cpi route missing"
grep -q 'CREATE TABLE IF NOT EXISTS cpi_releases' "$S/server.js" || die "cpi_releases table missing"
say "scratch build ok. Project-root files are not written yet."
echo "scratch server.js md5 $(md5of "$S/server.js")"
echo "scratch server.js sha256 $(sha256of "$S/server.js")"
echo "scratch app.js md5 $(md5of "$S/app.js")"
echo "scratch index.html md5 $(md5of "$S/index.html")"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: project-root files untouched. Scratch: $W"; exit 0; fi

TS=$(date +%Y%m%d-%H%M%S)
SUFF="bak-chat103g"
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.$SUFF" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.$SUFF")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.$SUFF"; done
cp "$S/server.js" "$SERVER.new-chat103" && cp "$S/app.js" "$APP.new-chat103" && cp "$S/index.html" "$INDEX.new-chat103" || die "staging copy failed (project-root files untouched)"
RB="restore server.js, app.js and index.html from their .$TS.$SUFF copies and DO NOT republish"
mv -f "$SERVER.new-chat103" "$SERVER" && mv -f "$APP.new-chat103" "$APP" && mv -f "$INDEX.new-chat103" "$INDEX" || { echo "[deploy-chat103] ERROR during install; $RB" >&2; exit 1; }
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-chat103] ERROR: node --check failed after install; $RB" >&2; exit 1; }
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || { echo "[deploy-chat103] ERROR: line 1 is not maintenance=false; $RB" >&2; exit 1; }
say "DONE: project-root server.js, app.js and index.html updated. Backup suffix $SUFF. The server was NOT started and nothing was republished."
say "To undo: restore the three root files from their .$TS.$SUFF copies."
rm -rf "$W"
