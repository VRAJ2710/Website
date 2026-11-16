#!/usr/bin/env bash
# Chain test on the fixture: dev-5ce95f3-like root (fixture prefix + chat105v3home2 + r6o scrub with the 5ce95f3 rewriteHtml
# change) -> deploy-chat102r6p -> deploy-chat106softgate -> behaviour tests. Guard constants are swapped for fixture values in
# COPIES of both deploy.sh files; payloads are the local files (same sha256 checks). Usage: bash run_chain_tests.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd); SG=$(dirname "$HERE"); R6=$(dirname "$SG")/deploy-chat102r6p
W=$(mktemp -d /tmp/c106sg-chain.XXXXXX); R="$W/root"; mkdir -p "$R"
python3 - "$SG" "$R" <<'PY'
import pathlib, sys
sg, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pre = (sg / "test/fixture_prefix.js").read_bytes()
v3 = (sg / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
(root / "server.js").write_bytes(pre + v3 + (sg / "server_block_c102r6o.js").read_bytes())
(root / "app.js").write_text("console.log('app');\n"); (root / "index.html").write_text("<!doctype html><html><body></body></html>\n")
PY
md5(){ md5sum "$1" | cut -d' ' -f1; }
PRE_LEN=$(wc -c < "$HERE/fixture_prefix.js" | tr -d ' '); PRE_SHA=$(sha256sum "$HERE/fixture_prefix.js" | cut -d' ' -f1)
S0=$(md5 "$R/server.js"); A0=$(md5 "$R/app.js"); I0=$(md5 "$R/index.html")
sed -e "s/^SERVER_MD5=.*/SERVER_MD5=$S0/" -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$R6/deploy.sh" > "$W/r6p.sh"
pass=0; fail=0
chk(){ if eval "$2"; then echo "ok   - $1"; pass=$((pass+1)); else echo "FAIL - $1"; fail=$((fail+1)); fi; }
out=$(bash "$W/r6p.sh" --measure --dir "$R" 2>&1); rc=$?; echo "$out" | sed 's/^/    /'
chk "r6p --measure exits 0, no change" '[ $rc = 0 ] && [ "$(md5 "$R/server.js")" = "$S0" ]'
out=$(R6P_LOCAL_PAYLOAD="$R6" bash "$W/r6p.sh" --dry-run --dir "$R" 2>&1); rc=$?; echo "$out" | tail -6 | sed 's/^/    /'
chk "r6p --dry-run exits 0, no change" '[ $rc = 0 ] && [ "$(md5 "$R/server.js")" = "$S0" ]'
out=$(R6P_LOCAL_PAYLOAD="$R6" bash "$W/r6p.sh" --dir "$R" 2>&1); rc=$?; echo "$out" | tail -3 | sed 's/^/    /'
chk "r6p apply exits 0" '[ $rc = 0 ]'
chk "r6p: one r6p attach, no r6o attach" '[ "$(grep -cF "[c102r6p] scrub attached" "$R/server.js")" = 1 ] && [ "$(grep -cF "[c102r6o] scrub attached" "$R/server.js")" = 0 ]'
chk "r6p keeps the 5ce95f3 auth-page script strip" '[ "$(grep -cF "Auth documents deliberately use script-src" "$R/server.js")" = 1 ]'
chk "r6p: 3 .bak-chat102r6p backups" '[ "$(ls "$R" | grep -c "\.bak-chat102r6p$")" = 3 ]'
S1=$(md5 "$R/server.js"); B1=$(wc -c < "$R/server.js" | tr -d ' ')
sed -e "s/^PREFIX_SHA=.*/PREFIX_SHA=$PRE_SHA/" -e "s/^PREFIX_BYTES=.*/PREFIX_BYTES=$PRE_LEN/" -e "s/^PRE_R6P_MD5=.*/PRE_R6P_MD5=$S0/" \
    -e "s/^POST_R6P_BYTES=.*/POST_R6P_BYTES=$B1/" -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$SG/deploy.sh" > "$W/sg.sh"
out=$(C106SG_LOCAL_PAYLOAD="$SG" bash "$W/sg.sh" --dry-run --dir "$R" 2>&1); rc=$?; echo "$out" | grep -E 'edit ok|scratch server|ABORT|refused' | sed 's/^/    /'
chk "softgate --dry-run after r6p exits 0, no change" '[ $rc = 0 ] && [ "$(md5 "$R/server.js")" = "$S1" ]'
out=$(C106SG_LOCAL_PAYLOAD="$SG" bash "$W/sg.sh" --dir "$R" 2>&1); rc=$?
chk "softgate apply exits 0" '[ $rc = 0 ]'
chk "one softgate attach, one r6p attach, auth strip kept" '[ "$(grep -cF "[chat106softgate] attached" "$R/server.js")" = 1 ] && [ "$(grep -cF "[c102r6p] scrub attached" "$R/server.js")" = 1 ] && [ "$(grep -cF "Auth documents deliberately use script-src" "$R/server.js")" = 1 ]'
chk "node --check final server.js" 'node --check "$R/server.js"'
python3 - "$R/server.js" "$SG" "$W/final_prefix.js" <<'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1]).read_bytes(); v3 = (pathlib.Path(sys.argv[2]) / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
pathlib.Path(sys.argv[3]).write_bytes(d[: d.index(v3)])
PY
for mode in off; do r=$(node "$HERE/behaviour.test.js" "$W/final_prefix.js" $mode 2>&1); chk "behaviour after r6p+softgate (flag $mode)" 'echo "$r" | grep -q "passed" && ! echo "$r" | grep -q FAIL'; echo "$r" | tail -1 | sed 's/^/    /'; done
sed 's/^const VERIFY_ENFORCE = false;/const VERIFY_ENFORCE = true;/' "$W/final_prefix.js" > "$W/final_prefix_on.js"
r=$(node "$HERE/behaviour.test.js" "$W/final_prefix_on.js" on 2>&1); chk "behaviour after r6p+softgate (flag on)" 'echo "$r" | grep -q "passed" && ! echo "$r" | grep -q FAIL'; echo "$r" | tail -1 | sed 's/^/    /'
# softgate on the un-r6p'd 5ce95f3 root must refuse
python3 - "$SG" "$W/pre" <<'PY'
import pathlib, sys
sg, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); root.mkdir()
pre = (sg / "test/fixture_prefix.js").read_bytes(); v3 = (sg / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
(root / "server.js").write_bytes(pre + v3 + (sg / "server_block_c102r6o.js").read_bytes())
(root / "app.js").write_text("console.log('app');\n"); (root / "index.html").write_text("<!doctype html><html><body></body></html>\n")
PY
out=$(C106SG_LOCAL_PAYLOAD="$SG" bash "$W/sg.sh" --dry-run --dir "$W/pre" 2>&1); rc=$?
chk "softgate before r6p refuses" '[ $rc != 0 ] && echo "$out" | grep -q "Apply r6p first"'
# shipped (real-guard) installers refuse the fixture
out=$(bash "$R6/deploy.sh" --dry-run --dir "$W/pre" 2>&1); rc=$?
chk "shipped r6p deploy.sh refuses the fixture root" '[ $rc != 0 ]'
echo "$pass passed, $fail failed"; rm -rf "$W"; [ $fail = 0 ]
