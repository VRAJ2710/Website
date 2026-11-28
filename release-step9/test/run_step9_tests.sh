#!/usr/bin/env bash
# LOCAL tests for release-step9 (box only). Fixture = the step-8 stand-in /tmp/r8fix (the live step-7 stand-in with the real step-8
# installer applied, TEST-ONLY auth harness in the prefix, mocked connectors SDK). Live pages/APIs come through a read-only caching proxy.
# The real step-8 server.js (a633becf, 2,539,589 B) is not on the box, so the md5/size pins are exercised via R9_LOCAL_TEST overrides.
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
F=/tmp/r9fix; O=${OUT:-/workspace/qa-dispatch/release-step9/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O $F; mkdir -p $O; cp -a /tmp/r8fix $F; cd $F; rm -rf .release-snapshots; git add -A >/dev/null 2>&1; git commit -qm "live step 8 stand-in" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r9old; mkdir -p /tmp/r9old; cp server.js app.js index.html styles.css c93.css /tmp/r9old/
B8MD5=$(md5sum < server.js | cut -c1-32); B8SZ=$(wc -c < server.js)
export R9_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B8MD5 R9_TEST_SERVER_SIZE=$B8SZ D "$@"; }
TO(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R9_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5
echo "---- unit tests of the block ----"
node $H/unit_block.js > $O/unit.out 2>&1; chk "unit_block.js: all block cases pass (injection == preview inject(), br/404/json/chunked/fail-safe, assets, 304, startup log)" 'grep -q " 0 failed" $O/unit.out'; tail -1 $O/unit.out

echo "---- installer guards ----"
D --measure > $O/g0.out 2>&1; chk "refuses without the live step-8 server.js (real pins a633becf, 2,539,589 B)" 'grep -q "not the live step-8" $O/g0.out'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
sed -n 's/.*Expected server.js md5 \([0-9a-f]*\), \([0-9]*\) B.*/fixture expected md5 \1 size \2/p' $O/m.out | tee $O/expected.txt
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=0000 R9_TEST_SERVER_SIZE=$B8SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the live step-8" $O/g1.out'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B8MD5 R9_TEST_SERVER_SIZE=1 D --dry-run > $O/g1b.out 2>&1; chk "refuses a wrong server.js size" 'grep -q "B, not the live step-8" $O/g1b.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done'
sed -i 's/var TAG = "chat113cookie";/var TAG = "chat113cookieX";/' server.js; TO --dry-run > $O/g2.out 2>&1; cp /tmp/r9old/server.js server.js
chk "refuses when the chat113cookie block differs" 'grep -q "does not end with the exact live chat112verifymail + chat113cookie" $O/g2.out'
sed -i 's/var TAG = "chat112verifymail";/var TAG = "chat112verifymailX";/' server.js; TO --dry-run > $O/g2b.out 2>&1; cp /tmp/r9old/server.js server.js
chk "refuses when the chat112verifymail block differs" 'grep -q "does not end with the exact live chat112verifymail + chat113cookie" $O/g2b.out'
echo "// trailing change" >> server.js; TO --dry-run > $O/g2c.out 2>&1; cp /tmp/r9old/server.js server.js
chk "refuses when server.js does not END with the chat113cookie block" 'grep -q "does not end with the exact" $O/g2c.out'
sed -i '2i // chat114viz already here' server.js; TO --dry-run > $O/g4.out 2>&1; cp /tmp/r9old/server.js server.js
chk "refuses when chat114viz already exists" 'grep -q "already contains chat114viz" $O/g4.out'
for f in release_step9.py restore_release.py server_block_chat112verifymail.js server_block_chat113cookie.js server_block_chat114viz.js viz.css viz.js; do
  rm -rf bad; mkdir bad; cp "$DEP"/*.py "$DEP"/*.js "$DEP"/viz.css bad/ 2>/dev/null; echo '//x' >> bad/$f
  R9_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5_$f.out 2>&1; done; rm -rf bad
chk "tampered payload refused by sha256 (each of the 7 payload files)" 'for f in release_step9.py restore_release.py server_block_chat112verifymail.js server_block_chat113cookie.js server_block_chat114viz.js viz.css viz.js; do grep -q "sha256 mismatch for $f" $O/g5_$f.out || exit 1; done'
# consistent but wrong: viz.js changed AND its manifest entry refreshed -> the block no longer embeds the payload
rm -rf bad2; mkdir bad2; cp "$DEP"/*.py "$DEP"/*.js "$DEP"/viz.css "$DEP"/deploy.sh bad2/; echo '//changed' >> bad2/viz.js; python3 bad2/finalize.py >/dev/null
R9_LOCAL_PAYLOAD=$F/bad2 R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B8MD5 R9_TEST_SERVER_SIZE=$B8SZ bash bad2/deploy.sh --dir $F --dry-run > $O/g6.out 2>&1; rm -rf bad2
chk "refuses when the block does not embed the exact viz.js/viz.css payload" 'grep -q "does not embed the exact viz.css / viz.js" $O/g6.out'
chk "unpinned PAYLOAD_COMMIT refused without local payload" '(unset R9_LOCAL_PAYLOAD; bash $DEP/deploy.sh --dir $F --measure 2>&1 | grep -q "PAYLOAD_COMMIT is not pinned") || (unset R9_LOCAL_PAYLOAD; bash $DEP/deploy.sh --dir $F --measure 2>&1 | grep -q "download failed\|sha256")'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'

echo "---- apply / snapshot / restore / re-apply ----"
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step9-* | head -1)
chk "snapshot step9-<TS>: server.js (= step 8) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r9old/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step9-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); app/index/styles/c93 byte-identical; node --check; new == old + block" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r9old/$f || exit 1; done && node --check server.js && cmp -s server.js <(cat /tmp/r9old/server.js $DEP/server_block_chat114viz.js) && [ "$(wc -c < server.js)" = "$(sed -n "s/.*size \([0-9]*\)/\1/p" $O/expected.txt)" ]'
chk "no new file created in the project (only .release-snapshots)" '[ "$(find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort)" = "$(awk "{print \$2}" $O/pre.md5 | sort)" ]'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 8 back byte-exact" 'cmp -s server.js /tmp/r9old/server.js && snapall | cmp -s - $O/pre.md5'
echo x >> server.js; python3 $SN/restore_release.py $SN > $O/r2.out 2>&1; chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r9old/server.js server.js; sleep 1; T > $O/a2.out 2>&1
chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step9-* | wc -l) = 2 ]'
T > $O/a3.out 2>&1; chk "a second apply on the released file is refused (no double block)" 'grep -q "is not the live step-8\|B, not the live step-8" $O/a3.out && [ "$(grep -c "var TAG = \"chat114viz\"" server.js)" = 1 ]'

echo "---- servers: step 9 (new) and step 8 (old) ----"
mkdir -p /tmp/node_modules/@replit/connectors-sdk; cp /workspace/c113/release-step8/test/mock/connectors-sdk.js /tmp/node_modules/@replit/connectors-sdk/index.js
CD=/tmp/r9cache; rm -rf $CD; for p in 8971 8964 8965; do kp $p; done
(CACHE_DIR=$CD PORT=8971 node /workspace/c109/release-step1/test/cacheproxy.js > $O/proxy.log 2>&1 &)
sleep 0.7
ENVP="DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS=1500 UPSTREAM_HTTP=localhost:8971 RAW_HTML=/workspace/c109/live_home.html"
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.new NETLOG=$O/net.new NODE_OPTIONS="--require $H/netlog.js" PORT=8964 node server.js > $O/rel.log 2>&1 &)
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.old MOCK_RESEND_LOG=$O/mail.old NETLOG=$O/net.old NODE_OPTIONS="--require $H/netlog.js" PORT=8965 node /tmp/r9old/server.js > $O/old.log 2>&1 &)
sleep 5
chk "log: '[chat114viz] attached' exactly once, right after '[chat113cookie] attached'; step 8 server has none" '[ "$(grep -c "\[chat114viz\] attached" $O/rel.log)" = 1 ] && [ "$(grep -c "chat114viz" $O/rel.log)" = 1 ] && grep -n "attached" $O/rel.log | grep -A1 "chat113cookie" | grep -q chat114viz && ! grep -q chat114viz $O/old.log'
chk "log: navy, verifymail, credits, r6p, cookie still attach once each" 'for t in "chat113cookie\] attached" "chat112verifymail\] attached" "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done'
chk "no startup error lines new vs old" '[ "$(grep -ci "error\|not attached\|skipped" $O/rel.log)" = "$(grep -ci "error\|not attached\|skipped" $O/old.log)" ]'
cp /tmp/routes.txt $O/routes.txt
python3 $H/compare_routes.py http://localhost:8965 http://localhost:8964 /tmp/routes.txt /workspace/c114/visuals/proxy.js > $O/routes.out 2>&1; cat $O/routes.out | cut -c1-230
chk "routes: 4 pages injected exactly as the preview, 53 other routes + variants byte-identical, assets served" '! grep -q "^FAIL" $O/routes.out && [ "$(grep -c "^PASS" $O/routes.out)" -ge 14 ]'
for z in "Accept-Encoding: br" "Accept-Encoding: gzip, deflate, br"; do curl -sS -H "$z" -D $O/br.hdr -o $O/br.body http://localhost:8964/gold/ ; done
chk "requests with Accept-Encoding br/gzip: injected page, correct Content-Length, ends </html>" 'grep -q "chat114viz" $O/br.body && [ "$(tr -d "\r" < $O/br.hdr | sed -n "s/^[Cc]ontent-[Ll]ength: //p")" = "$(wc -c < $O/br.body)" ] && tail -c 200 $O/br.body | grep -q "</html>"'

echo "---- auth unchanged ----"
A=$O/auth; mkdir -p $A
for n in new:8964 old:8965; do s=${n%%:*}; p=${n##*:}
  curl -sS -o $A/login_$s.body -D $A/login_$s.hdr "http://localhost:$p/__auth/login"; curl -sS -o $A/reg_$s.body -D $A/reg_$s.hdr "http://localhost:$p/__auth/register"
  curl -sS -o $A/regpost_$s.body -D $A/regpost_$s.hdr -c $A/$s.jar -X POST --data 'name=&email=viz9@example.com&password=newpassword1' "http://localhost:$p/__auth/register"
  curl -sS -b $A/$s.jar "http://localhost:$p/api/me" > $A/me_$s.json
  curl -sS -o $A/loginpost_$s.body -D $A/loginpost_$s.hdr -X POST --data 'email=old@example.com&password=oldpassword1' "http://localhost:$p/__auth/login"
  curl -sS -o $A/bad_$s.body -D $A/bad_$s.hdr -X POST --data 'email=old@example.com&password=wrongwrong1' "http://localhost:$p/__auth/login"
done
norm(){ tr -d "\r" < $1 | grep -viE "^date:|^set-cookie:" | sort; tr -d "\r" < $1 | grep -i "^set-cookie:" | sed -E "s/[0-9a-f]{64}/<tok>/g; s/Expires=[^;]*/Expires=<d>/Ig" | sort; }
chk "GET /__auth/login and /__auth/register: body + headers byte-identical to step 8" 'cmp -s $A/login_new.body $A/login_old.body && cmp -s $A/reg_new.body $A/reg_old.body && [ "$(norm $A/login_new.hdr)" = "$(norm $A/login_old.hdr)" ] && [ "$(norm $A/reg_new.hdr)" = "$(norm $A/reg_old.hdr)" ]'
chk "POST register / login / bad login: same status, Location and Set-Cookie shape (tokens masked); /api/me same" 'for k in regpost loginpost bad; do [ "$(norm $A/${k}_new.hdr)" = "$(norm $A/${k}_old.hdr)" ] && cmp -s $A/${k}_new.body $A/${k}_old.body || exit 1; done; python3 -c "
import json;a=json.load(open(\"$A/me_new.json\"));b=json.load(open(\"$A/me_old.json\"));[x.pop(k,None) for x in (a,b) for k in (\"id\",\"email\")];assert a==b and a.get(\"guest\") is False,(a,b)"'
chk "outbound network: step 9 contacts no host that step 8 does not" '[ -z "$(sort -u $O/net.new 2>/dev/null | comm -23 - <(sort -u $O/net.old 2>/dev/null))" ]'

echo "---- local render of the 4 pages (step 9 server) vs the preview proxy ----"
PXB=""; curl -s -o /dev/null -m 5 -w "%{http_code}" http://127.0.0.1:8714/logo-mark.svg | grep -q 200 && PXB=http://127.0.0.1:8714
if [ -z "$PXB" ]; then (cd /workspace/c114/visuals && nohup node proxy.js 8714 > proxy.log 2>&1 &); sleep 1.5; PXB=http://127.0.0.1:8714; fi
python3 $H/render_check.py http://localhost:8964 $O/render $PXB > $O/render.out 2>&1; cat $O/render.out | cut -c1-250
chk "render: 4 pages x (1280 dark, 390 dark, 390 light, 320 dark): layer ready, no overflow, no console errors, same structure and text as the preview" 'grep -q "^RENDER_OK" $O/render.out'
for p in 8964 8965 8971; do kp $p; done
echo; echo "step9 tests: $PASS passed, $FAIL failed" | tee $O/summary.txt
[ $FAIL = 0 ]
