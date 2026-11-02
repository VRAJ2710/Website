#!/usr/bin/env bash
# deploy-final: ONE combined publish of chat96 + chat97 + chat98 + chat99 on top of live chat94.
# Edits server.js, app.js, index.html (c93.css unchanged). Applies, in order:
#  - chat96: per-user-safe caching, labelled last-good figures, source names, free brief sign-up (stores only),
#            Plans/Pricing, gold in GBP, UK byline, 301s, /settings/, guest preview, auth CSRF/CSP, BYOK "Your AI keys"
#  - chat97: Light/Dark/System theme, gold dashboard, macro calendar (no consensus/rate-cut odds/transcripts),
#            "What changed today", site AI Gemini first with OpenAI fallback (xAI only as a reader's own key)
#  - chat98: in-app alerts (email OFF) and Portfolio X-ray; hidden until dev_create.sql tables exist (run by hand)
#  - chat99: SEC deep-dives for any US filer, filings screener, 25 SEC downloads a day (shared counter), Ask charts
# Does NOT: start the server, npm, git, .replit, package.json, env vars, Stripe, DB schema (no DDL).
# Maintenance line 1 stays `const BB10I_MAINTENANCE_ON = true;` (use deploy-reopen/deploy.sh later to open).
# Usage: bash deploy.sh [--dry-run] [--dir /path/to/project]
set -u
REF="${DEPLOY_REF:-deploy/jack-chat99}"
BASE_URL="https://raw.githubusercontent.com/VRAJ2710/Website/${REF}/deploy-final"

LIVE_SERVER_MD5=7a7a2df1fc685ba83dbca07e70a09567   # chat94
LIVE_APP_MD5=8a195ba9f9cf3ade9e10ed3a70091806      # chat94
LIVE_INDEX_MD5=b69f3596e29020ca80620246bae23f1b    # chat94
LIVE_CSS_MD5=9d6a86a64135b1cc58e6af7b12973550      # chat93 (unchanged throughout)
NEW_SERVER_MD5=16c8ecf81ba6c8da0c17a9b99e2b5ae4
NEW_APP_MD5=7beaf2917e0884b38c51253e937f6177
NEW_INDEX_MD5=fb535741645653c1f4bb4dc9df4846c9
NEW_SERVER_SHA256=cab6f2835ecef2b8c9f50a4269a620eb5d75e556967578b0dad3afd91dee1184
NEW_APP_SHA256=e0d3e55a130073108595b35b6b2cac4259a779a3b68d28d952c7728e6e5a53a0
NEW_INDEX_SHA256=b65f6e8ecb5692f879993c459914b02b7d98b893c495ecf854ca57234f623402
MANIFEST=(
  "chat96/app_block.js e4d506fd3cf65863d8dcf6c0ddac578677fb93cc545ba39270a84a83b9e62e65"
  "chat96/live96.js d2b505968fd59ef53bd9df3a53474e2049fe719a573d9a9b19759a9e387b7754"
  "chat96/patch_chat96.py a8038d094edecbaf5f5a196b1e2d6df8965a75e69128232aa8e4436eb0857aab"
  "chat96/plain.js 0e293e1280e889f73f02204231e75d123e9910270e89375b7057b751522e3e9b"
  "chat96/server_block.js ad018b7674b533a8640a88be858f5c733c63cbdca288cedc0335c272e2d9df77"
  "chat97/app_block97.js 7499724b9e128f1733ad1421cf41adfd4c59bb0fb3920db30d756916e73af22f"
  "chat97/app_c97.css a800fd2ab61e6e034e4beae39201f5a7f0a50181eafae4f75f657500b6ef3179"
  "chat97/app_dark.css 6705b67f3168b803201c19e58726ca0c0aced44b50e883698aabb6a41a852dbf"
  "chat97/live96.js d2b505968fd59ef53bd9df3a53474e2049fe719a573d9a9b19759a9e387b7754"
  "chat97/live97.js af7aac4cecf2c71c6c6288ea465cc0bb38b2c00f4383d08dc28b92eccb9a9bb0"
  "chat97/patch_chat97.py 63f764c3089b456fad40ab8fd1cee3d5429e61af270178db99416e130edfd691"
  "chat97/server_block97.js c9262e625e23cf4034adda5c780287b2326d2437bba5d9cb50120895eab66e68"
  "chat98/app_block98.js 392c8aa5f5def019ed41ba89ed91c2a810ffb5cfa1c3cd149ae1999bf1382863"
  "chat98/app_c98.css f287285981febb6b2fec9a63fe4f31253137e16781eeeaa80344e486c2866db5"
  "chat98/patch_chat98.py 28ee03ea6d1268162f9489f63b82243e407547c777970f6d59950640a758e037"
  "chat98/server_block98.js 8dad453d60d7a1d5e3ad583463bead55cc8a4221e28992c5ee37dd725b22a49e"
  "chat99/app_block99.js 57606e482cdd6e415fd86c47cc9eefe66b5ed06d8d14320b84aa96f89d55e6d5"
  "chat99/app_c99.css 0662101f6c97b4d7e8f47a86cdbdf6ffb5e89bff5ccb71ee7a79164a956ebafa"
  "chat99/patch_chat99.py a26742b6811a17cff93292a62ee89ad2d458037acb74a4dcc788aabe3ec6bb55"
  "chat99/server_block99.js e12e442d0b131a685104d9b97e1ccf97ba6e661e785ca8a803527070e9053c12"
)

DRY=0; DIR=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --dir) shift; DIR="${1:-}";; *) echo "unknown arg $1"; exit 2;; esac; shift; done
say(){ echo "[deploy-final] $*"; }
die(){ echo "[deploy-final] ABORT: $*" >&2; echo "[deploy-final] Nothing was changed in the live files." >&2; exit 1; }
md5of(){ md5sum "$1" | awk '{print $1}'; }
sha256of(){ sha256sum "$1" | awk '{print $1}'; }
for t in node python3 md5sum sha256sum curl cp grep find; do command -v "$t" >/dev/null 2>&1 || die "'$t' not found in this shell"; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' || die "python3 >= 3.8 required"
say "node $(node -v)"

# ---- 1. locate the live files ----
find_one(){ local name="$1" want="$2" alt="${3:-}" first="" p m
  for p in $(find "$ROOT" -maxdepth 3 -name "$name" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.cache/*' -not -path '*/.local/*' -not -path '*/deploy-chat9*' -not -path '*/deploy-final*' -not -path '*/deploy-reopen*' 2>/dev/null | sort); do
    [ -z "$first" ] && first="$p"; m=$(md5of "$p")
    { [ "$m" = "$want" ] || { [ -n "$alt" ] && [ "$m" = "$alt" ]; }; } && { echo "$p"; return 0; }
  done; echo "$first"; }
if [ -n "$DIR" ]; then ROOT="$DIR"; else ROOT=""
  for c in "$PWD" "${REPL_HOME:-}" "$HOME/workspace" /home/runner/workspace /home/runner/Website /home/runner; do [ -n "$c" ] && [ -f "$c/server.js" ] && { ROOT="$c"; break; }; done
  [ -z "$ROOT" ] && die "could not find server.js; cd into the project folder or pass --dir"; fi
say "project folder: $ROOT"
SERVER=$(find_one server.js "$LIVE_SERVER_MD5" "$NEW_SERVER_MD5"); APP=$(find_one app.js "$LIVE_APP_MD5" "$NEW_APP_MD5"); INDEX=$(find_one index.html "$LIVE_INDEX_MD5" "$NEW_INDEX_MD5")
for f in "$SERVER" "$APP" "$INDEX"; do [ -f "$f" ] || die "missing live file (server.js='$SERVER' app.js='$APP' index.html='$INDEX')"; done
SDIR=$(dirname "$SERVER"); CSS="$SDIR/c93.css"
say "server.js = $SERVER"; say "app.js    = $APP"; say "index.html= $INDEX"; say "c93.css   = $CSS (must stay chat93)"
sm=$(md5of "$SERVER"); am=$(md5of "$APP"); im=$(md5of "$INDEX"); say "current md5: server $sm | app $am | index $im"

# ---- 2. refuse a second run; check the base ----
if [ "$sm" = "$NEW_SERVER_MD5" ] || [ "$am" = "$NEW_APP_MD5" ] || [ "$im" = "$NEW_INDEX_MD5" ] || ls "$SERVER".*.bak-final >/dev/null 2>&1; then
  say "REFUSE: deploy-final is already applied (or a .bak-final backup exists). Nothing changed."; exit 0; fi
[ "$sm" = "$LIVE_SERVER_MD5" ] || die "server.js md5 $sm != expected live $LIVE_SERVER_MD5 (chat94)"
[ "$am" = "$LIVE_APP_MD5" ]    || die "app.js md5 $am != expected live $LIVE_APP_MD5 (chat94)"
[ "$im" = "$LIVE_INDEX_MD5" ]  || die "index.html md5 $im != expected live $LIVE_INDEX_MD5 (chat94)"
[ -f "$CSS" ] && [ "$(md5of "$CSS")" = "$LIVE_CSS_MD5" ] || die "c93.css missing or not the chat93 file ($CSS)"
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "server.js line 1 is not BB10I_MAINTENANCE_ON = true"
say "live md5s match chat94: ok"

# ---- 3. fetch + verify every patch file (sha256-pinned) ----
W=$(mktemp -d /tmp/deploy-final.XXXXXX) || die "mktemp failed"; P="$W/patches"; S="$W/scratch"; mkdir -p "$P/chat96" "$P/chat97" "$P/chat98" "$P/chat99" "$S"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
for e in "${MANIFEST[@]}"; do f="${e% *}"; h="${e#* }"
  if [ -n "$HERE" ] && [ -f "$HERE/$f" ] && [ "$(sha256of "$HERE/$f")" = "$h" ]; then cp "$HERE/$f" "$P/$f"
  else curl -fsSL --retry 2 "$BASE_URL/$f" -o "$P/$f" || die "download failed: $BASE_URL/$f"; fi
  [ "$(sha256of "$P/$f")" = "$h" ] || die "sha256 mismatch for $f"; say "patch file ok: $f ${h:0:16}…"; done

# ---- 4. DDL grep on everything that ends up in the live files ----
grep -inE 'create table|alter table|drop table|create index|truncate ' "$P"/chat9*/*.js "$P"/chat9*/*.css && die "a code block mentions DDL"
say "DDL grep (create/alter/drop table, create index, truncate): none"

# ---- 5. build in scratch and verify ----
cp "$SERVER" "$S/server.js"; cp "$APP" "$S/app.js"; cp "$INDEX" "$S/index.html"
for n in 96 97 98 99; do python3 "$P/chat$n/patch_chat$n.py" "$S/server.js" "$S/app.js" "$S/index.html" || die "patch_chat$n failed (live files untouched)"; done
node --check "$S/server.js" || die "node --check server.js failed (scratch)"
node --check "$S/app.js" || die "node --check app.js failed (scratch)"
[ "$(md5of "$S/server.js")" = "$NEW_SERVER_MD5" ] && [ "$(sha256of "$S/server.js")" = "$NEW_SERVER_SHA256" ] || die "scratch server.js differs from the tested build"
[ "$(md5of "$S/app.js")" = "$NEW_APP_MD5" ] && [ "$(sha256of "$S/app.js")" = "$NEW_APP_SHA256" ] || die "scratch app.js differs from the tested build"
[ "$(md5of "$S/index.html")" = "$NEW_INDEX_MD5" ] && [ "$(sha256of "$S/index.html")" = "$NEW_INDEX_SHA256" ] || die "scratch index.html differs from the tested build"
head -c 36 "$S/server.js" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || die "scratch server.js line 1 changed"
grep -q '/app.js?v=chat99' "$S/index.html" && grep -q '/c93.css?v=chat93' "$S/index.html" || die "cache tokens (app chat99, css chat93) missing"
say "scratch build matches the tested md5/sha256: ok"
if [ "$DRY" = "1" ]; then say "DRY RUN complete: live files untouched. Scratch: $W"; exit 0; fi

# ---- 6. timestamped backups, then install ----
TS=$(date +%Y%m%d-%H%M%S)
for f in "$SERVER" "$APP" "$INDEX"; do cp -p "$f" "$f.$TS.bak-final" || die "backup failed for $f"
  [ "$(md5of "$f.$TS.bak-final")" = "$(md5of "$f")" ] || die "backup verify failed for $f"; say "backup: $f.$TS.bak-final"; done
cp "$S/server.js" "$SERVER.new-final" && cp "$S/app.js" "$APP.new-final" && cp "$S/index.html" "$INDEX.new-final" || die "staging copy failed (live files untouched)"
RB="restore each file from its .$TS.bak-final copy and DO NOT republish"
mv -f "$APP.new-final" "$APP" && mv -f "$INDEX.new-final" "$INDEX" && mv -f "$SERVER.new-final" "$SERVER" || { echo "[deploy-final] ERROR during install; $RB" >&2; exit 1; }

# ---- 7. final verification ----
node --check "$SERVER" && node --check "$APP" || { echo "[deploy-final] ERROR: node --check failed after install; $RB" >&2; exit 1; }
head -c 36 "$SERVER" | grep -q '^const BB10I_MAINTENANCE_ON = true;' || { echo "[deploy-final] ERROR: maintenance line 1 changed; $RB" >&2; exit 1; }
fs=$(md5of "$SERVER"); fa=$(md5of "$APP"); fi_=$(md5of "$INDEX"); fc=$(md5of "$CSS")
echo "server.js  md5 $fs"; echo "app.js     md5 $fa"; echo "index.html md5 $fi_"; echo "c93.css    md5 $fc"
if [ "$fs" = "$NEW_SERVER_MD5" ] && [ "$fa" = "$NEW_APP_MD5" ] && [ "$fi_" = "$NEW_INDEX_MD5" ] && [ "$fc" = "$LIVE_CSS_MD5" ]; then
  say "DONE: all files match the tested build. Maintenance is still ON. The server was NOT started."
  say "Before Republish: set DISPATCH_BYOK_MASTER_KEY and DISPATCH_SEC_UA; run dev_create.sql by hand if you want Alerts/Portfolio X-ray."
  rm -rf "$W"; exit 0
else echo "[deploy-final] ERROR: final md5s differ; $RB" >&2; exit 1; fi
