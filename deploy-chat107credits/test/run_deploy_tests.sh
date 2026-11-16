#!/usr/bin/env bash
# Installer tests on the chain fixture: fef1da0 reconstruction + 5ce95f3 changes -> deploy-chat102r6p -> deploy-chat106softgate
# -> deploy-chat107credits. Guard constants are swapped for fixture values in COPIES of the deploy.sh files.
# Usage: bash run_deploy_tests.sh   (C107_REMOTE=1 to download the pinned payload instead of the local copy)
set -u
HERE=$(cd "$(dirname "$0")" && pwd); C7=$(dirname "$HERE"); REPIN=/workspace/repin-5ce95f3; SG=$REPIN/deploy-chat106softgate; R6=$REPIN/deploy-chat102r6p
W=$(mktemp -d /tmp/c107-chain.XXXXXX); R="$W/root"; mkdir -p "$R"
python3 - "$SG" "$R" <<'PY'
import pathlib, sys
sg, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pre = (sg / "test/fixture_prefix.js").read_bytes(); v3 = (sg / "server_block_chat105v3home2.js").read_bytes().rstrip(b"\n") + b"\n"
(root / "server.js").write_bytes(pre + v3 + (sg / "server_block_c102r6o.js").read_bytes())
(root / "app.js").write_text("console.log('app');\n"); (root / "index.html").write_text("<!doctype html><html><body></body></html>\n")
PY
md5(){ md5sum "$1" | cut -d' ' -f1; }
PRE_LEN=$(wc -c < "$SG/test/fixture_prefix.js" | tr -d ' '); PRE_SHA=$(sha256sum "$SG/test/fixture_prefix.js" | cut -d' ' -f1)
S0=$(md5 "$R/server.js"); A0=$(md5 "$R/app.js"); I0=$(md5 "$R/index.html")
sed -e "s/^SERVER_MD5=.*/SERVER_MD5=$S0/" -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$R6/deploy.sh" > "$W/r6p.sh"
R6P_LOCAL_PAYLOAD="$R6" bash "$W/r6p.sh" --dir "$R" > "$W/r6p.log" 2>&1 || { echo "chain setup: r6p failed"; cat "$W/r6p.log"; exit 1; }
B1=$(wc -c < "$R/server.js" | tr -d ' ')
sed -e "s/^PREFIX_SHA=.*/PREFIX_SHA=$PRE_SHA/" -e "s/^PREFIX_BYTES=.*/PREFIX_BYTES=$PRE_LEN/" -e "s/^PRE_R6P_MD5=.*/PRE_R6P_MD5=$S0/" \
    -e "s/^POST_R6P_BYTES=.*/POST_R6P_BYTES=$B1/" -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$SG/deploy.sh" > "$W/sg.sh"
C106SG_LOCAL_PAYLOAD="$SG" bash "$W/sg.sh" --dir "$R" > "$W/sg.log" 2>&1 || { echo "chain setup: softgate failed"; cat "$W/sg.log"; exit 1; }
rm -f "$R"/*.bak-chat102r6p "$R"/*.bak-chat106softgate 2>/dev/null; true
S2=$(md5 "$R/server.js"); B2=$(wc -c < "$R/server.js" | tr -d ' ')
echo "    fixture post-softgate server.js: $B2 bytes, md5 $S2"
mk(){ sed -e "s/^SERVER_BYTES=.*/SERVER_BYTES=$B2/" -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$C7/deploy.sh" > "$1"; }
mk "$W/c7.sh"
if [ "${C107_REMOTE:-}" = "1" ]; then LP=""; else LP="$C7"; fi
pass=0; fail=0
chk(){ if eval "$2"; then echo "ok   - $1"; pass=$((pass+1)); else echo "FAIL - $1"; fail=$((fail+1)); fi; }
run(){ C107_LOCAL_PAYLOAD="$LP" bash "$W/c7.sh" "$@" 2>&1; }
cp -r "$R" "$W/orig"
out=$(run --measure --dir "$R"); rc=$?; echo "$out" | sed 's/^/    /'
chk "--measure exits 0, prints full 32-hex md5s, changes nothing" '[ $rc = 0 ] && echo "$out" | grep -qE "server.js md5 [0-9a-f]{32}$" && echo "$out" | grep -qE "app.js md5 [0-9a-f]{32} " && [ "$(md5 "$R/server.js")" = "$S2" ]'
out=$(run --dry-run --dir "$R"); rc=$?; echo "$out" | tail -5 | sed 's/^/    /'
chk "--dry-run exits 0 and changes nothing" '[ $rc = 0 ] && [ "$(md5 "$R/server.js")" = "$S2" ] && [ -z "$(ls "$R" | grep bak-chat107credits)" ]'
out=$(run --dir "$R"); rc=$?; echo "$out" | tail -3 | sed 's/^/    /'
chk "apply exits 0" '[ $rc = 0 ]'
chk "existing bytes unchanged (cmp prefix)" 'cmp -n "$B2" "$R/server.js" "$W/orig/server.js" >/dev/null'
chk "one credits block, softgate and r6p attach once, VERIFY_ENFORCE false once" '[ "$(grep -cF "var TAG = \"chat107credits\";" "$R/server.js")" = 1 ] && [ "$(grep -cF "[chat106softgate] attached" "$R/server.js")" = 1 ] && [ "$(grep -cF "[c102r6p] scrub attached" "$R/server.js")" = 1 ] && [ "$(grep -c "^const VERIFY_ENFORCE = false;" "$R/server.js")" = 1 ]'
chk "node --check final server.js" 'node --check "$R/server.js"'
chk "3 timestamped .bak-chat107credits backups equal to the originals" '[ "$(ls "$R" | grep -c "\.bak-chat107credits$")" = 3 ] && [ "$(md5 "$(ls "$R"/server.js.*.bak-chat107credits)")" = "$S2" ]'
chk "app.js and index.html untouched" '[ "$(md5 "$R/app.js")" = "$A0" ] && [ "$(md5 "$R/index.html")" = "$I0" ]'
out=$(run --dir "$R"); rc=$?
chk "second run refuses as already applied, no change" '[ $rc = 0 ] && echo "$out" | grep -q "already applied" && [ "$(ls "$R" | grep -c "\.bak-chat107credits$")" = 3 ]'
# runtime: load the final file's appended block with the r6p wrappers already present -> exactly one attach line
python3 - "$R/server.js" "$W/orig/server.js" "$W/tail.js" <<'PY'
import sys; a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); open(sys.argv[3],'wb').write(a[len(b):])
PY
L=$(node -e '
const vm=require("vm"),fs=require("fs");const logs=[];const ctx={console:{log:m=>logs.push(String(m))},require,setTimeout,setInterval:()=>({unref(){}}),Buffer,Intl,Promise,Date,fetch:async()=>({ok:true})};ctx.globalThis=ctx;vm.createContext(ctx);
vm.runInContext("var c97Transform=function(h){return h};const c97Mem=new Map();\n"+fs.readFileSync(process.argv[1],"utf8"),ctx);console.log(logs.filter(l=>/chat107credits/.test(l)).join("|"))' "$W/tail.js")
chk "runtime: exactly one '[chat107credits] attached' log line" '[ "$L" = "[chat107credits] attached" ]'
# refusals
cp -r "$W/orig" "$W/bad1"; printf '\n// extra\n' >> "$W/bad1/server.js"
out=$(run --dry-run --dir "$W/bad1"); rc=$?; chk "refuses a server.js of the wrong size" '[ $rc != 0 ] && echo "$out" | grep -q "not the post-softgate size"'
cp -r "$W/orig" "$W/bad2"; python3 - "$W/bad2/server.js" <<'PY'
import sys; p=sys.argv[1]; d=open(p,'rb').read(); i=d.rfind(b'scrub attached'); d=d[:i]+b'scrub attacheD'+d[i+14:]; open(p,'wb').write(d)
PY
out=$(run --dry-run --dir "$W/bad2"); rc=$?; chk "refuses when the r6p tail is not byte-exact (same size)" '[ $rc != 0 ] && echo "$out" | grep -q "REFUSE"'
cp -r "$W/orig" "$W/bad3"; echo "x" >> "$W/bad3/app.js"
out=$(run --dry-run --dir "$W/bad3"); rc=$?; chk "refuses a changed app.js" '[ $rc != 0 ] && echo "$out" | grep -q "app.js md5"'
cp -r "$W/orig" "$W/bad4"; sed -i 's/^const VERIFY_ENFORCE = false;/const VERIFY_ENFORCE = !1;;/' "$W/bad4/server.js"
out=$(run --dry-run --dir "$W/bad4"); rc=$?; chk "refuses when VERIFY_ENFORCE = false is missing" '[ $rc != 0 ]'
out=$(C107_SERVER_MD5=00000000000000000000000000000000 run --dry-run --dir "$W/orig"); rc=$?; chk "optional exact md5 pin refuses a mismatch" '[ $rc != 0 ] && echo "$out" | grep -q "not the pinned"'
out=$(C107_SERVER_MD5=$S2 run --dry-run --dir "$W/orig"); rc=$?; chk "optional exact md5 pin accepts the right md5" '[ $rc = 0 ]'
out=$(bash "$C7/deploy.sh" --dry-run --dir "$W/orig" 2>&1); rc=$?; chk "shipped deploy.sh (real guards) refuses the fixture" '[ $rc != 0 ]'
echo "$pass passed, $fail failed"; rm -rf "$W"; [ $fail = 0 ]
