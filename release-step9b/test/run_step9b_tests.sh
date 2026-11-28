#!/usr/bin/env bash
# LOCAL tests for release-step9b (box only).
# A) Stand-in: /tmp/r8fix (step-8 stand-in) + the exact step-9 block appended (= what the step-9 installer produced) -> /tmp/r9bfix.
#    Live pages come through a DEV-SHAPED caching proxy (Replit's hosting analytics tag removed), so pages end </nav></body></html>
#    as on dev; with that, step 9 reproduces the dev failure (0 injections) and step 9b must inject.
# B) Real lineage: /workspace/hh101/off (the real server.js lineage, c101g era, maintenance off, test harness) + the real release blocks
#    r6p..chat113cookie + the step-9 block, then the 9b block. Reproduces the dev symptom exactly with step 9 (attached, 0 injections,
#    pages end </nav></body></html>) and shows 9b injecting.
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
F=/tmp/r9bfix; O=${OUT:-/workspace/qa-dispatch/release-step9b/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O $F; mkdir -p $O; cp -a /tmp/r8fix $F; cd $F; rm -rf .release-snapshots
cat $DEP/server_block_chat114viz_step9.js >> server.js
git add -A >/dev/null 2>&1; git commit -qm "staged step 9 stand-in" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r9bold; mkdir -p /tmp/r9bold; cp server.js app.js index.html styles.css c93.css /tmp/r9bold/
B9MD5=$(md5sum < server.js | cut -c1-32); B9SZ=$(wc -c < server.js); echo "stand-in step 9: md5 $B9MD5 $B9SZ B" | tee $O/standin.txt
export R9_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=$B9SZ D "$@"; }
TO(){ R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R9_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5
echo "---- unit tests ----"
node $H/unit_block.js > $O/unit.out 2>&1; chk "unit_block.js on live copies (28 cases: injection == preview inject(), br/404/json/chunked/fail-safe, assets, 304, startup log)" 'grep -q " 0 failed" $O/unit.out'
node $H/unit_block.js $H/devraw > $O/unit_dev.out 2>&1; chk "unit_block.js on dev-shaped copies (same 28 cases)" 'grep -q " 0 failed" $O/unit_dev.out'
node $H/unit_9b.js > $O/unit9b.out 2>&1; cat $O/unit9b.out; chk "unit_9b.js: step 9 reproduces the dev failure; 9b injects == preview, one-time injected log, capped reasons" 'grep -q " 0 failed" $O/unit9b.out'

echo "---- installer guards ----"
D --measure > $O/g0.out 2>&1; chk "refuses without the staged step-9 server.js (real pins 8e08169a, 2,587,429 B)" 'grep -q "not the staged step-9" $O/g0.out'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
sed -n 's/.*Expected server.js md5 \([0-9a-f]*\), \([0-9]*\) B.*/fixture expected md5 \1 size \2/p' $O/m.out | tee $O/expected.txt
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=0000 R9_TEST_SERVER_SIZE=$B9SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the staged step-9" $O/g1.out'
R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=1 D --dry-run > $O/g1b.out 2>&1; chk "refuses a wrong server.js size" 'grep -q "B, not the staged step-9" $O/g1b.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done'
for t in chat113cookie chat112verifymail; do sed -i "s/var TAG = \"$t\";/var TAG = \"${t}X\";/" server.js; TO --dry-run > $O/g2_$t.out 2>&1; cp /tmp/r9bold/server.js server.js; done
chk "refuses when the chat113cookie or chat112verifymail block differs" 'grep -q "does not end with the exact" $O/g2_chat113cookie.out && grep -q "does not end with the exact" $O/g2_chat112verifymail.out'
sed -i 's/var JS_TAG = /var JS_TAG =  /' server.js; TO --dry-run > $O/g3.out 2>&1; cp /tmp/r9bold/server.js server.js
chk "refuses when the trailing chat114viz block is not the exact step-9 block" 'grep -q "does not end with the exact" $O/g3.out'
echo "// trailing change" >> server.js; TO --dry-run > $O/g2c.out 2>&1; cp /tmp/r9bold/server.js server.js
chk "refuses when server.js does not END with the step-9 block" 'grep -q "does not end with the exact" $O/g2c.out'
head -c -$(wc -c < $DEP/server_block_chat114viz_step9.js) /tmp/r9bold/server.js > server.js; TO --dry-run > $O/g4.out 2>&1; cp /tmp/r9bold/server.js server.js
chk "refuses step 8 (no chat114viz block yet)" 'grep -q "does not end with the exact" $O/g4.out'
PF="release_step9b.py restore_release.py server_block_chat112verifymail.js server_block_chat113cookie.js server_block_chat114viz_step9.js server_block_chat114viz.js viz.css viz.js"
for f in $PF; do rm -rf bad; mkdir bad; cp "$DEP"/*.py "$DEP"/*.js "$DEP"/viz.css bad/ 2>/dev/null; echo '//x' >> bad/$f; R9_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5_$f.out 2>&1; done; rm -rf bad
chk "tampered payload refused by sha256 (each of the 8 payload files)" 'for f in $PF; do grep -q "sha256 mismatch for $f" $O/g5_$f.out || exit 1; done'
rm -rf bad2; mkdir bad2; cp "$DEP"/*.py "$DEP"/*.js "$DEP"/viz.css "$DEP"/deploy.sh bad2/; echo '//changed' >> bad2/viz.js; python3 bad2/finalize.py >/dev/null
R9_LOCAL_PAYLOAD=$F/bad2 R9_LOCAL_TEST=1 R9_TEST_SERVER_MD5=$B9MD5 R9_TEST_SERVER_SIZE=$B9SZ bash bad2/deploy.sh --dir $F --dry-run > $O/g6.out 2>&1; rm -rf bad2
chk "refuses when a block does not embed the exact viz.js/viz.css payload" 'grep -q "does not embed the exact viz.css / viz.js" $O/g6.out'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'

echo "---- apply / snapshot / restore / re-apply ----"
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step9b-* | head -1)
chk "snapshot step9b-<TS>: server.js (= step 9) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r9bold/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step9b-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); others byte-identical; node --check; new == step 9 minus old block + new block; size = expected" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r9bold/$f || exit 1; done && node --check server.js && cmp -s server.js <(head -c -$(wc -c < $DEP/server_block_chat114viz_step9.js) /tmp/r9bold/server.js; cat $DEP/server_block_chat114viz.js) && [ "$(wc -c < server.js)" = "$(sed -n "s/.*size \([0-9]*\)/\1/p" $O/expected.txt)" ] && [ $(( B9SZ - $(wc -c < $DEP/server_block_chat114viz_step9.js) + $(wc -c < $DEP/server_block_chat114viz.js) )) = "$(wc -c < server.js)" ] && [ "$(grep -c "var TAG = \"chat114viz\"" server.js)" = 1 ]'
chk "no new file created in the project (only .release-snapshots)" '[ "$(find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort)" = "$(awk "{print \$2}" $O/pre.md5 | sort)" ]'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 9 back byte-exact" 'cmp -s server.js /tmp/r9bold/server.js && snapall | cmp -s - $O/pre.md5'
T > /dev/null 2>&1; echo x >> server.js; SN2=$(ls -d $F/.release-snapshots/step9b-* | tail -1); python3 $SN2/restore_release.py $SN2 > $O/r2.out 2>&1
chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r9bold/server.js server.js; sleep 1; T > $O/a2.out 2>&1
chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step9b-* | wc -l) = 3 ]'
TO > $O/a3.out 2>&1; chk "a second apply on the 9b file is refused (no double block)" 'grep -q "does not end with the exact" $O/a3.out && [ "$(grep -c "var TAG = \"chat114viz\"" server.js)" = 1 ]'

echo "---- A) stand-in servers: step 9b (new) vs step 9 (old), dev-shaped pages ----"
mkdir -p /tmp/node_modules/@replit/connectors-sdk; cp /workspace/c113/release-step8/test/mock/connectors-sdk.js /tmp/node_modules/@replit/connectors-sdk/index.js
CD=/tmp/r9bcache; rm -rf $CD; for p in 8981 8974 8975; do kp $p; done
(CACHE_DIR=$CD PORT=8981 node $H/cacheproxy_dev.js > $O/proxy.log 2>&1 &)
sleep 0.7
ENVP="DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS=1500 UPSTREAM_HTTP=localhost:8981 RAW_HTML=/workspace/c109/live_home.html"
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.new NETLOG=$O/net.new NODE_OPTIONS="--require $H/netlog.js" PORT=8974 node server.js > $O/rel.log 2>&1 &)
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.old MOCK_RESEND_LOG=$O/mail.old NETLOG=$O/net.old NODE_OPTIONS="--require $H/netlog.js" PORT=8975 node /tmp/r9bold/server.js > $O/old.log 2>&1 &)
sleep 5
for p in brief gold markets research; do curl -s http://localhost:8975/$p/ -o $O/old_$p.html; done
chk "REPRO (stand-in, step 9): 4 pages end </nav></body></html> and contain 0 'chat114viz'; log has only 'attached'" 'for p in brief gold markets research; do [ "$(grep -c chat114viz $O/old_$p.html)" = 0 ] && tail -c 25 $O/old_$p.html | grep -q "</nav></body></html>$" || exit 1; done && [ "$(grep -c chat114viz $O/old.log)" = 1 ]'
cp /tmp/routes.txt $O/routes.txt
ASSETS_SAME=1 python3 $H/compare_routes.py http://localhost:8975 http://localhost:8974 /tmp/routes.txt /workspace/c114/visuals/proxy.js > $O/routes.out 2>&1; cut -c1-230 $O/routes.out
chk "routes: 4 pages == preview inject(step-9 page), 53 other routes + variants byte-identical, assets byte-identical" '! grep -q "^FAIL" $O/routes.out && [ "$(grep -c "^PASS" $O/routes.out)" -ge 14 ]'
chk "log: '[chat114viz] attached' once right after chat113cookie, then '[chat114viz] injected /brief/' once" '[ "$(grep -c "\[chat114viz\] attached" $O/rel.log)" = 1 ] && grep -n "attached" $O/rel.log | grep -A1 "chat113cookie" | grep -q chat114viz && [ "$(grep -c "\[chat114viz\] injected " $O/rel.log)" = 1 ] && grep -q "^\[chat114viz\] injected /brief/$" $O/rel.log'
chk "log: navy, verifymail, credits, r6p, cookie still attach once each; no new error/skip lines" 'for t in "chat113cookie\] attached" "chat112verifymail\] attached" "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done && [ "$(grep -ci "error\|not attached\|skipped\|not injected" $O/rel.log)" = "$(grep -ci "error\|not attached\|skipped\|not injected" $O/old.log)" ]'
for z in "Accept-Encoding: br" "Accept-Encoding: gzip, deflate, br"; do curl -sS -H "$z" -D $O/br.hdr -o $O/br.body http://localhost:8974/gold/ ; done
chk "Accept-Encoding br/gzip: injected page, correct Content-Length, ends </html>" 'grep -q "chat114viz" $O/br.body && [ "$(tr -d "\r" < $O/br.hdr | sed -n "s/^[Cc]ontent-[Ll]ength: //p")" = "$(wc -c < $O/br.body)" ] && tail -c 200 $O/br.body | grep -q "</html>"'
echo "---- auth unchanged ----"
A=$O/auth; mkdir -p $A
for n in new:8974 old:8975; do s=${n%%:*}; p=${n##*:}
  curl -sS -o $A/login_$s.body -D $A/login_$s.hdr "http://localhost:$p/__auth/login"; curl -sS -o $A/reg_$s.body -D $A/reg_$s.hdr "http://localhost:$p/__auth/register"
  curl -sS -o $A/regpost_$s.body -D $A/regpost_$s.hdr -c $A/$s.jar -X POST --data 'name=&email=viz9b@example.com&password=newpassword1' "http://localhost:$p/__auth/register"
  curl -sS -b $A/$s.jar "http://localhost:$p/api/me" > $A/me_$s.json
  curl -sS -o $A/loginpost_$s.body -D $A/loginpost_$s.hdr -X POST --data 'email=old@example.com&password=oldpassword1' "http://localhost:$p/__auth/login"
  curl -sS -o $A/bad_$s.body -D $A/bad_$s.hdr -X POST --data 'email=old@example.com&password=wrongwrong1' "http://localhost:$p/__auth/login"
done
norm(){ tr -d "\r" < $1 | grep -viE "^date:|^set-cookie:" | sort; tr -d "\r" < $1 | grep -i "^set-cookie:" | sed -E "s/[0-9a-f]{64}/<tok>/g; s/Expires=[^;]*/Expires=<d>/Ig" | sort; }
chk "GET /__auth/login and /__auth/register: body + headers byte-identical to step 9" 'cmp -s $A/login_new.body $A/login_old.body && cmp -s $A/reg_new.body $A/reg_old.body && [ "$(norm $A/login_new.hdr)" = "$(norm $A/login_old.hdr)" ] && [ "$(norm $A/reg_new.hdr)" = "$(norm $A/reg_old.hdr)" ]'
chk "POST register / login / bad login: same status, Location and Set-Cookie shape; /api/me same" 'for k in regpost loginpost bad; do [ "$(norm $A/${k}_new.hdr)" = "$(norm $A/${k}_old.hdr)" ] && cmp -s $A/${k}_new.body $A/${k}_old.body || exit 1; done; python3 -c "
import json;a=json.load(open(\"$A/me_new.json\"));b=json.load(open(\"$A/me_old.json\"));[x.pop(k,None) for x in (a,b) for k in (\"id\",\"email\")];assert a==b and a.get(\"guest\") is False,(a,b)"'
chk "outbound network: step 9b contacts no host that step 9 does not" '[ -z "$(sort -u $O/net.new 2>/dev/null | comm -23 - <(sort -u $O/net.old 2>/dev/null))" ]'
echo "---- local render of the 4 pages (step 9b stand-in) vs the preview proxy ----"
PXB=""; curl -s -o /dev/null -m 5 -w "%{http_code}" http://127.0.0.1:8714/logo-mark.svg | grep -q 200 && PXB=http://127.0.0.1:8714
if [ -z "$PXB" ]; then (cd /workspace/c114/visuals && nohup node proxy.js 8714 > proxy.log 2>&1 &); sleep 1.5; PXB=http://127.0.0.1:8714; fi
python3 $H/render_check.py http://localhost:8974 $O/render $PXB > $O/render.out 2>&1; cut -c1-250 $O/render.out
chk "render: 4 pages x (1280 dark, 390 dark, 390 light, 320 dark): layer ready, no overflow, no console errors, same structure and text as the preview" 'grep -q "^RENDER_OK" $O/render.out'
for p in 8974 8975 8981; do kp $p; done

echo "---- B) real server.js lineage (hh101/off) + real release blocks: step 9 vs step 9b ----"
RL=/tmp/r9breal; rm -rf $RL; mkdir -p $RL; (cd /workspace/hh101/off && for f in *; do [ "$f" = zipFile.zip ] || cp -r "$f" $RL/; done)
tail -n +$(grep -n "^// chat102r6c last-write scrub" /tmp/r8fix/server.js | cut -d: -f1) /tmp/r8fix/server.js > $O/real_blocks8.js
cat /workspace/hh101/off/server.js $O/real_blocks8.js $DEP/server_block_chat114viz_step9.js > $RL/server9.js
cat /workspace/hh101/off/server.js $O/real_blocks8.js $DEP/server_block_chat114viz.js > $RL/server9b.js
for v in 9 9b; do kp 8991; cp $RL/server$v.js $RL/server.js; (cd $RL && PORT=5991 HARNESS_PORT=8991 H_MASTER=x setsid node -r /workspace/hh101/preload.js $RL/wrap.js > $O/real$v.log 2>&1 < /dev/null &)
  for i in $(seq 1 90); do sleep 1; grep -q "harness on" $O/real$v.log && break; done
  for p in brief gold markets research; do curl -s -D $O/real${v}_$p.hdr http://127.0.0.1:8991/$p/ -o $O/real${v}_$p.html; done
  curl -s -b "dispatch_session=hmember" http://127.0.0.1:8991/gold/ -o $O/real${v}_signed_gold.html; sleep 0.5; kp 8991; done
chk "REPRO (real lineage, step 9): attached, 0 'chat114viz' in the 4 pages, pages end </nav></body></html>, no other chat114viz log (the exact dev symptom)" 'grep -q "^\[chat114viz\] attached$" $O/real9.log && [ "$(grep -c chat114viz $O/real9.log)" = 1 ] && for p in brief gold markets research; do [ "$(grep -c chat114viz $O/real9_$p.html)" = 0 ] && tail -c 25 $O/real9_$p.html | grep -q "</nav></body></html>$" || exit 1; done'
python3 - $O > $O/real_cmp.out <<'PY'
import sys,re,subprocess,json
O=sys.argv[1]; src=open("/workspace/c114/visuals/proxy.js").read(); inj=src[src.index("function inject("):src.index("function cookieFix")]
INJ="const f=(()=>{"+inj+";return inject})();const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(f(d.h,d.p))"
ok=True
for p in ["brief","gold","markets","research"]:
    n=open(f"{O}/real9b_{p}.html",encoding="utf-8").read(); h=open(f"{O}/real9b_{p}.hdr").read()
    cl=int(re.search(r"(?im)^content-length:\s*(\d+)",h).group(1))
    strip=n.replace('<link rel="stylesheet" href="/__chat114viz/viz.css?v=chat114viz">',"").replace('<script src="/__chat114viz/viz.js?v=chat114viz" defer></script>',"").replace("cz-on cz-%s "%p,"",1)
    strip=re.sub(r'<section id="chat114viz" class="cz-root"[^>]*><p class="cz-loading">[^<]*</p></section>',"",strip,count=1)
    re_inj=subprocess.run(["node","-e",INJ],input=json.dumps({"h":strip,"p":p}),capture_output=True,text=True).stdout
    good = re_inj==n and cl==len(n.encode()) and n.count('id="chat114viz"')==1 and n.endswith('<script src="/__chat114viz/viz.js?v=chat114viz" defer></script></body></html>') and strip.endswith("</nav></body></html>")
    print(("OK " if good else "BAD ")+p, len(n.encode()), cl); ok&=good
print("REAL_OK" if ok else "REAL_BAD")
PY
cat $O/real_cmp.out
chk "real lineage, step 9b: 4 pages injected; page minus the 4 insertions + preview inject() == served page; Content-Length right" 'grep -q "^REAL_OK" $O/real_cmp.out'
chk "real lineage, step 9b log: attached, then exactly one 'injected /brief/'" 'grep -q "^\[chat114viz\] attached$" $O/real9b.log && [ "$(grep -c "\[chat114viz\] injected" $O/real9b.log)" = 1 ] && grep -q "^\[chat114viz\] injected /brief/$" $O/real9b.log'
chk "real lineage: signed-in /gold/ (different page, no <main class=\"wrap\">) is byte-unchanged in shape and logs a 'not injected' reason (fail-safe)" '[ "$(grep -c chat114viz $O/real9b_signed_gold.html)" = 0 ] && grep -q "not injected /gold/: no </head>" $O/real9b.log'
echo; echo "step9b tests: $PASS passed, $FAIL failed" | tee $O/summary.txt
[ $FAIL = 0 ]
