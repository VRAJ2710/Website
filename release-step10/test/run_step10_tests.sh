#!/usr/bin/env bash
# LOCAL tests for release-step10 (box only).
# A) Stand-in /tmp/r10fix = /tmp/r8fix (step-8 stand-in) + the exact step-9b block (= the staged step 9b shape): installer guards,
#    apply/snapshot/restore/re-apply, guest routes byte-identical to step 9b, auth unchanged, startup log.
# B) Real lineage /tmp/r10real = /workspace/hh101/off (real server.js lineage, maintenance off, harness sessions) + the real release
#    blocks + step 9b (+ step 10), with the CURRENT live app.js/index.html/styles.css/c93.css: signed-in app shell and a headless
#    render of the member app with client-side navigation (1280/390 dark+light, 320 dark).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
F=/tmp/r10fix; O=${OUT:-/workspace/qa-dispatch/release-step10/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O $F; mkdir -p $O; cp -a /tmp/r8fix $F; cd $F; rm -rf .release-snapshots
cat $DEP/server_block_chat114viz.js >> server.js
git add -A >/dev/null 2>&1; git -c user.name=t -c user.email=t@t commit -qm "staged step 9b stand-in" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r10old; mkdir -p /tmp/r10old; cp server.js app.js index.html styles.css c93.css /tmp/r10old/
B9MD5=$(md5sum < server.js | cut -c1-32); B9SZ=$(wc -c < server.js); echo "stand-in step 9b: md5 $B9MD5 $B9SZ B" | tee $O/standin.txt
export R9_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=$B9SZ D "$@"; }
TO(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R9_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5
echo "---- unit tests ----"
node $H/unit_block.js > $O/unit.out 2>&1; grep -E "^(PASS|FAIL)" $O/unit.out | sed 's/^/  /'; chk "unit_block.js: shell injection (identity/br/gzip), guest/public/json/404/non-UTF-8/api pass-through, asset+304, logs" 'grep -q " 0 failed" $O/unit.out'
echo "---- installer guards ----"
D --measure > $O/g0.out 2>&1; chk "refuses without the staged step-9b server.js (real pins 9a875821, 2,588,699 B)" 'grep -q "not the staged step-9b" $O/g0.out'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
sed -n 's/.*Expected server.js md5 \([0-9a-f]*\), \([0-9]*\) B.*/fixture expected md5 \1 size \2/p' $O/m.out | tee $O/expected.txt
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=0000 R9_TEST_SERVER_SIZE=$B9SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the staged step-9b" $O/g1.out'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=1 D --dry-run > $O/g1b.out 2>&1; chk "refuses a wrong server.js size" 'grep -q "B, not the staged step-9b" $O/g1b.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done'
for t in chat113cookie chat112verifymail; do sed -i "s/var TAG = \"$t\";/var TAG = \"${t}X\";/" server.js; TO --dry-run > $O/g2_$t.out 2>&1; cp /tmp/r10old/server.js server.js; done
chk "refuses when the chat113cookie or chat112verifymail block differs" 'grep -q "does not end with the exact" $O/g2_chat113cookie.out && grep -q "does not end with the exact" $O/g2_chat112verifymail.out'
head -c -$(wc -c < $DEP/server_block_chat114viz.js) /tmp/r10old/server.js > server.js; cat /workspace/c114/release-step9b/server_block_chat114viz_step9.js >> server.js; TO --dry-run > $O/g3.out 2>&1; cp /tmp/r10old/server.js server.js
chk "refuses the old step-9 server.js (step-9 chat114viz block, not 9b)" 'grep -q "does not end with the exact" $O/g3.out'
echo "// trailing change" >> server.js; TO --dry-run > $O/g2c.out 2>&1; cp /tmp/r10old/server.js server.js
chk "refuses when server.js does not END with the step-9b block" 'grep -q "does not end with the exact" $O/g2c.out'
sed -i '2i // chat115vizapp already here' server.js; TO --dry-run > $O/g4.out 2>&1; cp /tmp/r10old/server.js server.js
chk "refuses when chat115vizapp already exists" 'grep -q "already contains chat115vizapp" $O/g4.out'
PF="release_step10.py restore_release.py server_block_chat112verifymail.js server_block_chat113cookie.js server_block_chat114viz.js server_block_chat115vizapp.js vizapp.js"
for f in $PF; do rm -rf bad; mkdir bad; cp "$DEP"/*.py "$DEP"/*.js bad/ 2>/dev/null; echo '//x' >> bad/$f; R9_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5_$f.out 2>&1; done; rm -rf bad
chk "tampered payload refused by sha256 (each of the 7 payload files)" 'for f in $PF; do grep -q "sha256 mismatch for $f" $O/g5_$f.out || exit 1; done'
rm -rf bad2; mkdir bad2; cp "$DEP"/*.py "$DEP"/*.js "$DEP"/deploy.sh bad2/; echo '//changed' >> bad2/vizapp.js; python3 bad2/finalize.py >/dev/null
R9_LOCAL_PAYLOAD=$F/bad2 R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=$B9SZ bash bad2/deploy.sh --dir $F --dry-run > $O/g6.out 2>&1; rm -rf bad2
chk "refuses when the block does not embed the exact vizapp.js payload" 'grep -q "does not embed the exact vizapp.js" $O/g6.out'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'
echo "---- apply / snapshot / restore / re-apply ----"
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step10-* | head -1)
chk "snapshot step10-<TS>: server.js (= step 9b) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r10old/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step10-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); others byte-identical; node --check; new == step 9b + block; size = expected" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r10old/$f || exit 1; done && node --check server.js && cmp -s server.js <(cat /tmp/r10old/server.js $DEP/server_block_chat115vizapp.js) && [ "$(wc -c < server.js)" = "$(sed -n "s/.*size \([0-9]*\)/\1/p" $O/expected.txt)" ]'
chk "no new file created in the project (only .release-snapshots)" '[ "$(find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort)" = "$(awk "{print \$2}" $O/pre.md5 | sort)" ]'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 9b back byte-exact" 'cmp -s server.js /tmp/r10old/server.js && snapall | cmp -s - $O/pre.md5'
T > /dev/null 2>&1; echo x >> server.js; SN2=$(ls -d $F/.release-snapshots/step10-* | tail -1); python3 $SN2/restore_release.py $SN2 > $O/r2.out 2>&1
chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r10old/server.js server.js; sleep 1; T > $O/a2.out 2>&1
chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step10-* | wc -l) = 3 ]'
T > $O/a3.out 2>&1; chk "a second apply on the step-10 file is refused (no double block)" 'grep -q "not the staged step-9b" $O/a3.out && [ "$(grep -c "var TAG = \"chat115vizapp\"" server.js)" = 1 ]'

echo "---- A) stand-in servers: step 10 (new) vs step 9b (old), guest ----"
mkdir -p /tmp/node_modules/@replit/connectors-sdk; cp /workspace/c113/release-step8/test/mock/connectors-sdk.js /tmp/node_modules/@replit/connectors-sdk/index.js
CD=/tmp/r10cache; rm -rf $CD; for p in 8982 8976 8977; do kp $p; done
(CACHE_DIR=$CD PORT=8982 node /workspace/c114/release-step9b/test/cacheproxy_dev.js > $O/proxy.log 2>&1 &)
sleep 0.7
ENVP="DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS=1500 UPSTREAM_HTTP=localhost:8982 RAW_HTML=/workspace/c109/live_home.html"
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.new NETLOG=$O/net.new NODE_OPTIONS="--require /workspace/c114/release-step9b/test/netlog.js" PORT=8976 node server.js > $O/rel.log 2>&1 &)
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.old MOCK_RESEND_LOG=$O/mail.old NETLOG=$O/net.old NODE_OPTIONS="--require /workspace/c114/release-step9b/test/netlog.js" PORT=8977 node /tmp/r10old/server.js > $O/old.log 2>&1 &)
sleep 5
for p in brief gold markets research; do curl -s http://localhost:8977/$p/ > /dev/null; done   # warm the cache through the old server first
python3 $H/compare_guest.py http://localhost:8977 http://localhost:8976 /tmp/routes.txt > $O/guest.out 2>&1; cat $O/guest.out | cut -c1-200
chk "guest: all routes (+variants, assets, with and without br/gzip) byte-identical to step 9b; new asset only on step 10" '! grep -q "^FAIL" $O/guest.out'
chk "log: '[chat115vizapp] attached' once right after '[chat114viz] attached'; guests trigger no injected/not-injected line" '[ "$(grep -c "\[chat115vizapp\] attached" $O/rel.log)" = 1 ] && grep -n "attached" $O/rel.log | grep -A1 "chat114viz" | grep -q chat115vizapp && [ "$(grep -c chat115vizapp $O/rel.log)" = 1 ]'
chk "log: earlier blocks still attach once each; no new error/skip lines" 'for t in "chat114viz\] attached" "chat113cookie\] attached" "chat112verifymail\] attached" "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done && [ "$(grep -ci "error\|not attached\|skipped\|not injected" $O/rel.log)" = "$(grep -ci "error\|not attached\|skipped\|not injected" $O/old.log)" ]'
echo "---- auth unchanged ----"
A=$O/auth; mkdir -p $A
for n in new:8976 old:8977; do s=${n%%:*}; p=${n##*:}
  curl -sS -o $A/login_$s.body -D $A/login_$s.hdr "http://localhost:$p/__auth/login"; curl -sS -o $A/reg_$s.body -D $A/reg_$s.hdr "http://localhost:$p/__auth/register"
  curl -sS -o $A/regpost_$s.body -D $A/regpost_$s.hdr -c $A/$s.jar -X POST --data 'name=&email=viz10@example.com&password=newpassword1' "http://localhost:$p/__auth/register"
  curl -sS -b $A/$s.jar "http://localhost:$p/api/me" > $A/me_$s.json
  curl -sS -o $A/loginpost_$s.body -D $A/loginpost_$s.hdr -X POST --data 'email=old@example.com&password=oldpassword1' "http://localhost:$p/__auth/login"
  curl -sS -o $A/bad_$s.body -D $A/bad_$s.hdr -X POST --data 'email=old@example.com&password=wrongwrong1' "http://localhost:$p/__auth/login"
done
norm(){ tr -d "\r" < $1 | grep -viE "^date:|^set-cookie:" | sort; tr -d "\r" < $1 | grep -i "^set-cookie:" | sed -E "s/[0-9a-f]{64}/<tok>/g; s/Expires=[^;]*/Expires=<d>/Ig" | sort; }
chk "GET /__auth/login and /__auth/register: body + headers byte-identical to step 9b" 'cmp -s $A/login_new.body $A/login_old.body && cmp -s $A/reg_new.body $A/reg_old.body && [ "$(norm $A/login_new.hdr)" = "$(norm $A/login_old.hdr)" ] && [ "$(norm $A/reg_new.hdr)" = "$(norm $A/reg_old.hdr)" ]'
chk "POST register / login / bad login: same status, Location and Set-Cookie shape; /api/me same" 'for k in regpost loginpost bad; do [ "$(norm $A/${k}_new.hdr)" = "$(norm $A/${k}_old.hdr)" ] && cmp -s $A/${k}_new.body $A/${k}_old.body || exit 1; done; python3 -c "
import json;a=json.load(open(\"$A/me_new.json\"));b=json.load(open(\"$A/me_old.json\"));[x.pop(k,None) for x in (a,b) for k in (\"id\",\"email\")];assert a==b and a.get(\"guest\") is False,(a,b)"'
chk "outbound network: step 10 contacts no host that step 9b does not" '[ -z "$(sort -u $O/net.new 2>/dev/null | comm -23 - <(sort -u $O/net.old 2>/dev/null))" ]'
for p in 8976 8977 8982; do kp $p; done

echo "---- B) real server.js lineage + current app files: signed-in member app ----"
RL=/tmp/r10real; rm -rf $RL ${RL}9b; mkdir -p $RL; (cd /workspace/hh101/off && for f in *; do [ "$f" = zipFile.zip ] || cp -r "$f" $RL/; done); cp /tmp/r8fix/{app.js,index.html,styles.css,c93.css} $RL/
BL=$O/real_blocks8.js; tail -n +$(grep -n "^// chat102r6c last-write scrub" /tmp/r8fix/server.js | cut -d: -f1) /tmp/r8fix/server.js > $BL
cp -a $RL ${RL}9b; cat /workspace/hh101/off/server.js $BL $DEP/server_block_chat114viz.js > ${RL}9b/server.js; cat ${RL}9b/server.js $DEP/server_block_chat115vizapp.js > $RL/server.js
kp 8994; kp 8995
(cd $RL && PORT=5994 HARNESS_PORT=8994 H_MASTER=x setsid node -r /workspace/hh101/preload.js $RL/wrap.js > $O/real10.log 2>&1 < /dev/null &)
(cd ${RL}9b && PORT=5995 HARNESS_PORT=8995 H_MASTER=x setsid node -r /workspace/hh101/preload.js ${RL}9b/wrap.js > $O/real9b.log 2>&1 < /dev/null &)
for i in $(seq 1 90); do sleep 1; grep -q "harness on" $O/real10.log && grep -q "harness on" $O/real9b.log && break; done
for v in 10:8994 9b:8995; do s=${v%%:*}; p=${v##*:}
  curl -s -b dispatch_session=hmember http://127.0.0.1:$p/brief/ -o $O/shell_$s.html
  curl -s -b dispatch_session=hmember -H "Accept-Encoding: gzip, deflate, br" -D $O/shellbr_$s.hdr http://127.0.0.1:$p/gold/ -o $O/shellbr_$s.bin
  curl -s -b dispatch_session=hmember http://127.0.0.1:$p/api/prefs -o $O/prefs_$s.json -w "%{http_code}\n" > $O/prefs_$s.code; done
chk "real lineage: signed-in app shell = step-9b shell + exactly the 2 tags (identity; the credits date map, live feed state, normalised)" 'python3 $H/check_real.py shell $O > $O/check_shell.out 2>&1'
chk "real lineage: brotli app shell still brotli, Content-Length right, decodes to the injected shell" 'grep -qi "^content-encoding: br" $O/shellbr_10.hdr && [ "$(tr -d "\r" < $O/shellbr_10.hdr | sed -n "s/^[Cc]ontent-[Ll]ength: //p")" = "$(wc -c < $O/shellbr_10.bin)" ] && node -e "const s=require(\"zlib\").brotliDecompressSync(require(\"fs\").readFileSync(\"$O/shellbr_10.bin\")).toString();process.exit(s.includes(\"/__chat115vizapp/vizapp.js\")&&s.includes(\"/__chat114viz/viz.css\")?0:1)"'
chk "real lineage log: chat115vizapp attached, then exactly one injected line" 'grep -q "^\[chat115vizapp\] attached$" $O/real10.log && [ "$(grep -c "\[chat115vizapp\] injected " $O/real10.log)" = 1 ]'
chk "real lineage: /api/prefs answers the same on step 9b and step 10 (not touched)" 'cmp -s $O/prefs_10.code $O/prefs_9b.code && cmp -s $O/prefs_10.json $O/prefs_9b.json'
python3 $H/app_render.py http://127.0.0.1:8995 $O/render9b baseline > $O/render9b.out 2>&1
python3 $H/app_render.py http://127.0.0.1:8994 $O/render10 > $O/render10.out 2>&1; grep -E "^(OK|BAD)|console errors" $O/render10.out | cut -c1-230
chk "baseline: step 9b shows no layer anywhere in the member app (the audit finding)" 'grep -q "^APP_RENDER_OK" $O/render9b.out'
chk "render (step 10, signed-in app): 1280/390 dark+light and 320 dark; load + client nav brief>gold>markets>research>brief>playbook(non-target)>back>gold: one layer at the top of the visible page body, ready, right page, removed on playbook, no overflow, no raw codes, app content kept" 'grep -q "^APP_RENDER_OK" $O/render10.out'
chk "console/HTTP errors in the member app: step 10 adds none, except the two snapshot feeds this older box server lacks (/api/c102/terminal, /api/c102/chart; 200 on dev per the audit)" 'python3 $H/check_real.py errors $O > $O/check_errors.out 2>&1'
kp 8994; kp 8995
echo; echo "step10 tests: $PASS passed, $FAIL failed" | tee $O/summary.txt
[ $FAIL = 0 ]
