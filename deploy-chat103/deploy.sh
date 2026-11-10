#!/usr/bin/env bash
# deploy-chat103: public /cpi/ on the live chat102r5 root.
# Does NOT start the server, npm, git, or republish. Does not change EXPECT_TAG.
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
# Payload commit is the commit that already contains these blobs.
# Do not point this at a commit that only changes deploy.sh.
PAYLOAD_COMMIT=c3f8ac8f945ecfaef59ab41ae48dd1e9516a37c8
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${PAYLOAD_COMMIT}/deploy-chat103"

# chat102r5 root. App and index are the chat102 bytes. The server tail is the r5 block.
R5_TAIL_SHA256=099d7a7ebefb146220659d519fee5150315b18dee61f71fdc421cfcc9da8a054
R5_APP_MD5=b84058f6da16ad022640b06c9cdda72d
R5_INDEX_MD5=b3e02b0c6e403133843a96adf45d219c
# Full-file md5 of server.js after the r5 tail is applied to the r4 root
# (r4 md5 5e8e3e34b6c71ae9e510c40b298ee6fc, r4 tail 3e812cd7…). The r4 prefix
# is not in this repository, so the full-file md5 is checked when this is set
# to the value printed by the r5 dry run. An empty value does not skip the tail check.
R5_SERVER_MD5=
NEW_L1='const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)'
MARKER='// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.'
MANIFEST=(
  "patch_c103.py da78fdbdac04e0a11afff84c58fe2ee558bb9def3ce32234d8cf7c862b21443a"
  "server_block_c103.js a27c46b2d7a5e95d0a470f38a842cd495afeb68b521e58a56d81785d7c72185f"
  "app_block_c103.js ab0c067f42fe185c5f943610f17a953b70283061613f1de99b9b9c3c1e91ec79"
  "ddl_c103.sql daea13f16b65de38741f79f2da273b1723d83a7470c941c7f851270e25a09053"
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
[ "$am" = "$R5_APP_MD5" ] || die "root app.js md5 $am is not the chat102 app $R5_APP_MD5"
[ "$im" = "$R5_INDEX_MD5" ] || die "root index.html md5 $im is not the chat102 index $R5_INDEX_MD5"
if [ -n "$R5_SERVER_MD5" ] && [ "$sm" != "$R5_SERVER_MD5" ]; then
  die "root server.js md5 $sm is not the chat102r5 server $R5_SERVER_MD5"
fi
[ "$(head -n 1 "$SERVER")" = "$NEW_L1" ] || die "project-root server.js line 1 is not the maintenance=false line"
python3 - "$SERVER" "$MARKER" "$R5_TAIL_SHA256" << 'PY' || die "server.js tail is not the chat102r5 block"
import hashlib, pathlib, sys
server, marker, expect = sys.argv[1:]
text = pathlib.Path(server).read_text(encoding="utf-8")
if text.count(marker) != 1:
    sys.exit("project-root server.js does not contain exactly one chat102 block")
tail = text[text.find(marker):]
got = hashlib.sha256(tail.encode("utf-8")).hexdigest()
if got != expect:
    sys.exit("server.js tail sha256 " + got + " is not the chat102r5 block " + expect)
if "chat103 cpi day" in text:
    sys.exit("chat103 is already installed")
print("chat102r5 tail ok")
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
cp "$S/server.js" "$S/server.js.base"
python3 "$P/patch_c103.py" "$S/server.js" "$S/app.js" "$S/index.html" "$P/server_block_c103.js" "$P/app_block_c103.js" || die "patch_c103 failed (project-root files untouched)"
python3 - "$S" "$MARKER" "$R5_TAIL_SHA256" << 'PY' || die "scratch is not the guarded r5 edit"
import hashlib, pathlib, sys
scratch, marker, expect = sys.argv[1:]
root = pathlib.Path(scratch)
old = (root/"server.js.base").read_text(encoding="utf-8")
new = (root/"server.js").read_text(encoding="utf-8")
idx = old.find(marker)
tail = old[idx:]
if hashlib.sha256(tail.encode("utf-8")).hexdigest() != expect:
    sys.exit("base tail changed before the append")
if not new.startswith(old[:idx] + tail):
    sys.exit("chat102r5 bytes were not kept in front of the chat103 block")
if "chat103 cpi day" not in new[idx+len(tail):]:
    sys.exit("chat103 block was not appended")
app = (root/"app.js").read_text(encoding="utf-8")
if 'c102Path === "/terminal"' not in app or 'c102Path === "/cpi"' not in app:
    sys.exit("app.js lost the terminal guard or missed /cpi/")
idx_html = (root/"index.html").read_text(encoding="utf-8")
if idx_html.count('/app.js?v=chat103"') != 1 or '/app.js?v=chat102"' in idx_html:
    sys.exit("index.html is not the one cache-tag swap")
print("r5 prefix kept")
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
SUFF="bak-chat103"
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
