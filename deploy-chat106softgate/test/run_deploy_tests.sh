#!/usr/bin/env bash
# End-to-end test of deploy.sh on the fixture: guard constants are swapped for fixture values in a COPY of deploy.sh.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); PKG=$(dirname "$HERE")
W=$(mktemp -d /tmp/c106sg-deploy.XXXXXX); R="$W/root"; mkdir -p "$R"
python3 - "$PKG" "$R" <<'PY'
import pathlib, sys
pkg, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pre = (pkg / "test/fixture_prefix.js").read_bytes()
v3 = (pkg / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
(root / "server.js").write_bytes(pre + v3 + (pkg / "server_block_c102r6p.js").read_bytes())
(root / "server.pre_r6p.js").write_bytes(pre + v3 + (pkg / "server_block_c102r6o.js").read_bytes())
(root / "app.js").write_text("console.log('app');\n"); (root / "index.html").write_text("<!doctype html><html><body></body></html>\n")
PY
PRE_LEN=$(python3 -c "import sys;print(len(open('$HERE/fixture_prefix.js','rb').read()))")
PRE_SHA=$(sha256sum "$HERE/fixture_prefix.js" | cut -d' ' -f1)
PRE_MD5=$(md5sum "$R/server.pre_r6p.js" | cut -d' ' -f1)
POST_BYTES=$(wc -c < "$R/server.js" | tr -d ' ')
APPM=$(md5sum "$R/app.js" | cut -d' ' -f1); IDXM=$(md5sum "$R/index.html" | cut -d' ' -f1)
sed -e "s/^PREFIX_SHA=.*/PREFIX_SHA=$PRE_SHA/" -e "s/^PREFIX_BYTES=.*/PREFIX_BYTES=$PRE_LEN/" -e "s/^PRE_R6P_MD5=.*/PRE_R6P_MD5=$PRE_MD5/" \
    -e "s/^POST_R6P_BYTES=.*/POST_R6P_BYTES=$POST_BYTES/" -e "s/^APP_MD5=.*/APP_MD5=$APPM/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$IDXM/" "$PKG/deploy.sh" > "$W/deploy_fixture.sh"
export C106SG_LOCAL_PAYLOAD="$PKG"
pass=0; fail=0
chk(){ if eval "$2"; then echo "ok   - $1"; pass=$((pass+1)); else echo "FAIL - $1"; fail=$((fail+1)); fi; }
M0=$(md5sum "$R/server.js" | cut -d' ' -f1)
out=$(bash "$W/deploy_fixture.sh" --measure --dir "$R" 2>&1); echo "$out" | sed 's/^/    /'
chk "--measure exits 0 and changes nothing" '[ "$(md5sum "$R/server.js" | cut -d" " -f1)" = "$M0" ]'
out=$(bash "$W/deploy_fixture.sh" --dry-run --dir "$R" 2>&1); rc=$?; echo "$out" | sed 's/^/    /'
chk "--dry-run exits 0" '[ $rc = 0 ]'
chk "--dry-run leaves root untouched" '[ "$(md5sum "$R/server.js" | cut -d" " -f1)" = "$M0" ] && [ -z "$(ls "$R" | grep bak-)" ]'
DRY_MD5=$(echo "$out" | awk '/^scratch server.js md5/{print $4}')
out=$(bash "$W/deploy_fixture.sh" --dir "$R" 2>&1); rc=$?; echo "$out" | sed 's/^/    /'
chk "apply exits 0" '[ $rc = 0 ]'
chk "applied md5 equals dry-run md5" '[ "$(md5sum "$R/server.js" | cut -d" " -f1)" = "$DRY_MD5" ]'
chk "three timestamped .bak-chat106softgate backups" '[ "$(ls "$R" | grep -c "\.bak-chat106softgate$")" = 3 ]'
chk "backup equals original" '[ "$(md5sum "$R"/server.js.*.bak-chat106softgate | cut -d" " -f1)" = "$M0" ]'
chk "exactly one attach line" '[ "$(grep -cF "[chat106softgate] attached" "$R/server.js")" = 1 ]'
chk "node --check" 'node --check "$R/server.js"'
out=$(bash "$W/deploy_fixture.sh" --dir "$R" 2>&1); rc=$?
chk "second apply refuses (already applied), exit 0, no change" '[ $rc = 0 ] && echo "$out" | grep -q "already applied" && [ "$(md5sum "$R/server.js" | cut -d" " -f1)" = "$DRY_MD5" ]'
cp "$R/server.pre_r6p.js" "$R/server.js"; rm -f "$R"/*.bak-chat106softgate
out=$(bash "$W/deploy_fixture.sh" --dry-run --dir "$R" 2>&1); rc=$?
chk "pre-r6p root refused with 'apply r6p first'" '[ $rc != 0 ] && echo "$out" | grep -q "Apply r6p first"'
cp "$R/server.pre_r6p.js" "$R/server.js"
# The shipped deploy.sh (real guards) must refuse the fixture.
python3 - "$PKG" "$R" <<'PY'
import pathlib, sys
pkg, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pre = (pkg / "test/fixture_prefix.js").read_bytes(); v3 = (pkg / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
(root / "server.js").write_bytes(pre + v3 + (pkg / "server_block_c102r6p.js").read_bytes())
PY
out=$(bash "$PKG/deploy.sh" --dry-run --dir "$R" 2>&1); rc=$?
chk "shipped deploy.sh refuses the fixture root (guards hold)" '[ $rc != 0 ]'; echo "$out" | tail -2 | sed 's/^/    /'
echo "$pass passed, $fail failed"; rm -rf "$W"; [ $fail = 0 ]
