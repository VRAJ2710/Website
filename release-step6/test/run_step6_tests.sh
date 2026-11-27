#!/usr/bin/env bash
# LOCAL tests for release-step6 (box only). Fixture = live step-4b stand-in (step-3 fixture + real step-4 + real step-4b installers)
# with a TEST-ONLY auth harness injected into the prefix: the verbatim lineage auth code (c101g) over PGlite (real Postgres 17).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); C112=/workspace/c112; S4=$C112/release-step4; S4B=$C112/release-step4b
F=/tmp/r6fix; O=${OUT:-/workspace/qa-dispatch/release-step6/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O; mkdir -p $O
read SM SS RM < <(bash "$S4/test/make_fixture.sh" $F | tail -1); cd $F
R4_LOCAL_PAYLOAD="$S4" R4_LOCAL_TEST=1 R4_TEST_SERVER_SIZE="$SS" R4_TEST_R6N_MD5="$RM" bash "$S4/deploy.sh" --dir $F > $O/s4.out 2>&1
S4MD5=$(md5sum < server.js | cut -c1-32); S4SZ=$(wc -c < server.js)
R4B_LOCAL_PAYLOAD="$S4B" R4B_LOCAL_TEST=1 R4B_TEST_SERVER_MD5=$S4MD5 R4B_TEST_SERVER_SIZE=$S4SZ bash "$S4B/deploy.sh" --dir $F > $O/s4b.out 2>&1
chk "fixture: real step-4 then real step-4b installers applied" 'grep -q "DONE: server.js md5" $O/s4.out && grep -q "DONE: server.js md5" $O/s4b.out'
python3 $H/make_auth_prefix.py $H/auth_prefix.js
python3 - $H/auth_prefix.js <<'PY'
import sys
s = open("server.js").read(); a = open(sys.argv[1]).read()
i = s.index("\n") + 1; s = s[:i] + a + s[i:]
hook = '    const path = req.url.split("?")[0];\n'; assert s.count(hook) == 1
s = s.replace(hook, hook + '    if (authHarness(req, res)) return;\n'); open("server.js", "w").write(s)
PY
node --check server.js && rm -rf .release-snapshots && git add -A >/dev/null 2>&1 && git commit -qm "live step 4b stand-in + auth harness" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r6old; mkdir -p /tmp/r6old; cp server.js app.js index.html styles.css c93.css /tmp/r6old/
B4MD5=$(md5sum < server.js | cut -c1-32); B4SZ=$(wc -c < server.js)
export R6_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R6_LOCAL_TEST=1 R6_TEST_SERVER_MD5=$B4MD5 R6_TEST_SERVER_SIZE=$B4SZ D "$@"; }
TO(){ R6_LOCAL_TEST=1 R6_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R6_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5
D --measure > $O/g0.out 2>&1; chk "refuses without the live step-4b server.js (real pins c8e4af65, 2,517,276 B)" 'grep -q "not the live step-4b" $O/g0.out && snapall | cmp -s - $O/pre.md5'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R6_LOCAL_TEST=1 R6_TEST_SERVER_MD5=0000 R6_TEST_SERVER_SIZE=$B4SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the live step-4b" $O/g1.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done && snapall | cmp -s - $O/pre.md5'
python3 -c "
b=open('server.js','rb').read(); i=b.rindex(b'padding:18px 16px'); open('server.js','wb').write(b[:i]+b'padding:18px 17px'+b[i+17:])"
TO --dry-run > $O/g2.out 2>&1; cp /tmp/r6old/server.js server.js
chk "refuses when the chat110navyb block differs by one byte" 'grep -q "does not end with the exact live chat110navyb" $O/g2.out'
sed -i 's/async function setSession(req, res, user, oldToken = null) {/async function setSession(req, res, user, oldToken) {/' server.js
TO --dry-run > $O/g3.out 2>&1; cp /tmp/r6old/server.js server.js
chk "refuses when a prefix anchor (setSession) is not exactly as expected" 'grep -q "prefix anchor .*setSession.* occurs 0 times" $O/g3.out'
sed -i '2i // email_verified already here' server.js
TO --dry-run > $O/g4.out 2>&1; cp /tmp/r6old/server.js server.js
chk "refuses when verification code already exists (email_verified in prefix)" "grep -q \"prefix anchor b'email_verified' occurs 1 times\" \$O/g4.out"
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; sed -i 's/var VERIFY_ENFORCE = false;/var VERIFY_ENFORCE = true; /' bad/server_block_chat111verify.js
R6_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5.out 2>&1; rm -rf bad; chk "tampered payload (VERIFY_ENFORCE=true) refused by sha256" 'grep -q "sha256 mismatch" $O/g5.out'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step6-* | head -1)
chk "snapshot step6-<TS>: server.js (= 4b) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r6old/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step6-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); app/index/styles/c93 byte-identical; node --check" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r6old/$f || exit 1; done && node --check server.js'
chk "server.js = 4b server.js + the block appended, byte-for-byte (nothing before it changed)" 'cat /tmp/r6old/server.js $DEP/server_block_chat111verify.js | cmp -s - server.js'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 4b back byte-exact" 'cmp -s server.js /tmp/r6old/server.js'
echo x >> server.js; sleep 1; python3 $SN/restore_release.py $SN > $O/r2.out 2>&1; chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r6old/server.js server.js; sleep 1; T > $O/a2.out 2>&1; chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step6-* | wc -l) = 2 ]'
# ---- run old (4b) and new (step 6) side by side, each with its own fresh PGlite DB, logging outbound connections ----
CD=/tmp/r2cache; for p in 8871 8862 8863 8892 8893; do kp $p; done; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > $O/proxy.log 2>&1 &); sleep 0.7
rm -f $O/net.new $O/net.old
(NETLOG=$O/net.new NODE_OPTIONS="--require $H/netlog.js" UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8862 node server.js > $O/rel.log 2>&1 &)
(NETLOG=$O/net.old NODE_OPTIONS="--require $H/netlog.js" UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8863 node /tmp/r6old/server.js > $O/old.log 2>&1 &); sleep 4
(UPSTREAM_PORT=8862 STATIC_DIR=/tmp/r6old EDITS=$S4/index_edits.json PORT=8892 node $S4/test/navyfront.js > $O/front.log 2>&1 &)
(UPSTREAM_PORT=8863 STATIC_DIR=/tmp/r6old EDITS=$S4/index_edits.json PORT=8893 node $S4/test/navyfront.js > $O/oldfront.log 2>&1 &); sleep 1
chk "log: chat111verify attaches once (enforcement off) + navy/credits/r6p once each; old server has no chat111verify" '[ "$(grep -c "\[chat111verify\] attached (enforcement off, no emails)" $O/rel.log)" = 1 ] && for t in "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done && ! grep -q chat111verify $O/old.log'
curl -s -o /dev/null localhost:8862/gold/; NB=$(wc -l < $O/net.new)
A=$O/auth; mkdir -p $A
post(){ curl -s -o $A/$1.body -D $A/$1.hdr -c $A/$1.jar -X POST --data "$3" "http://localhost:$2$4"; }
me(){ curl -s -b $A/$1.jar "http://localhost:$2/api/me"; }
db(){ curl -s "http://localhost:$1/__testdb/users"; }
for side in new:8862 old:8863; do n=${side%%:*}; p=${side##*:}
  post reg_$n $p 'name=&email=new1@example.com&password=newpassword1' /__auth/register; me reg_$n $p > $A/me_reg_$n.json
  post login_new_$n $p 'email=new1@example.com&password=newpassword1' /__auth/login; me login_new_$n $p > $A/me_login_new_$n.json
  post login_old_$n $p 'email=old@example.com&password=oldpassword1' /__auth/login; me login_old_$n $p > $A/me_login_old_$n.json
  post badpw_$n $p 'email=old@example.com&password=wrongpassword' /__auth/login
  post dup_$n $p 'email=old@example.com&password=whatever123' /__auth/register
  post sub_$n $p 'email=new2@example.com&password=newpassword2' /__auth/subscribe; me sub_$n $p > $A/me_sub_$n.json
  post subold_$n $p 'email=old@example.com&password=oldpassword1' /__auth/subscribe
done
sleep 1; db 8862 > $A/db_new.json; db 8863 > $A/db_old.json
python3 - $A > $A/summary.txt <<'PY'
import json, sys, re
A = sys.argv[1]
def st(k):  # status, location, cookie names + attributes (token values masked)
    h = open("%s/%s.hdr" % (A, k)).read().splitlines()
    s = h[0].split(" ")[1]; loc = [l for l in h if l.lower().startswith("location:")]
    ck = [re.sub(r"dispatch_session=[0-9a-f]{64}", "dispatch_session=<token>", l) for l in h if l.lower().startswith("set-cookie:")]
    return [s, loc, ck]
for k in ("reg", "login_new", "login_old", "badpw", "dup", "sub", "subold"):
    n, o = st(k + "_new"), st(k + "_old"); bn, bo = open("%s/%s_new.body" % (A, k), "rb").read(), open("%s/%s_old.body" % (A, k), "rb").read()
    print("%-10s same_status_location_cookies=%s same_body=%s new=%s" % (k, n == o, bn == bo, n[:2]))
for k in ("reg", "login_new", "login_old", "sub"):
    a, b = json.load(open("%s/me_%s_new.json" % (A, k))), json.load(open("%s/me_%s_old.json" % (A, k)))
    a.pop("id", None); b.pop("id", None); print("me_%-9s same=%s new=%s" % (k, a == b, a))
for t in ("new", "old"):
    print("db_" + t, {r["email"]: r["email_verified"] for r in json.load(open("%s/db_%s.json" % (A, t)))})
PY
cat $A/summary.txt
chk "register a new user -> 302 / + session; same status/location/cookie set/body as 4b" 'grep -q "^reg        same_status_location_cookies=True same_body=True new=\[.302., \[.Location: /.\]\]" $A/summary.txt'
chk "/api/me right after registering shows the new user signed in (same as 4b)" 'grep -q "^me_reg       same=True new={.guest.: False, .email.: .new1@example.com." $A/summary.txt'
chk "new (unverified) user can sign in again immediately and /api/me shows them" 'grep -q "^login_new  same_status_location_cookies=True same_body=True new=\[.302." $A/summary.txt && grep -q "^me_login_new same=True new={.guest.: False, .email.: .new1@example.com." $A/summary.txt'
chk "existing user sign-in unchanged (302, signed in, same as 4b)" 'grep -q "^login_old  same_status_location_cookies=True same_body=True new=\[.302." $A/summary.txt && grep -q "^me_login_old same=True new={.guest.: False, .email.: .old@example.com." $A/summary.txt'
chk "wrong password and duplicate register: identical pages to 4b" 'grep -q "^badpw      same_status_location_cookies=True same_body=True" $A/summary.txt && grep -q "^dup        same_status_location_cookies=True same_body=True" $A/summary.txt'
chk "Premium sign-up (subscribe) -> 302 /?checkout=1 with a fresh session cookie, identical to 4b (status, location, cookies, body, /api/me); existing-user subscribe identical" 'grep -q "^sub        same_status_location_cookies=True same_body=True new=\[.302., \[.Location: /?checkout=1.\]\]" $A/summary.txt && grep -q "^me_sub       same=True" $A/summary.txt && grep -q "dispatch_session=[0-9a-f]\{64\}" $A/sub_new.hdr && grep -q "^subold     same_status_location_cookies=True same_body=True" $A/summary.txt'
chk "DB: new sign-ups email_verified=false on step 6, existing user stays true; 4b keeps everyone true" "grep -q \"^db_new {'old@example.com': True, 'new1@example.com': False, 'new2@example.com': False}\" \$A/summary.txt && grep -q \"^db_old {'old@example.com': True, 'new1@example.com': True, 'new2@example.com': True}\" \$A/summary.txt"
tail -n +$((NB+1)) $O/net.new > $O/net.auth; sort $O/net.new | uniq -c > $O/net.summary
chk "netlog works (the proxied GETs to localhost:8871 are seen) and there is no outbound connection to Resend or any non-local host, during auth flows or at all" '[ -s $O/net.new ] && grep -q "^localhost:8871$" $O/net.new && ! grep -qi resend $O/net.new && [ -z "$(grep -v "^localhost:8871$\|^127.0.0.1:8871$" $O/net.new)" ] && [ -z "$(grep -v "^localhost:8871$\|^127.0.0.1:8871$" $O/net.auth)" ]'
j(){ curl -s "http://localhost:$1$2"; }
chk "guest /api/me byte-identical to 4b and to the live capture" '[ "$(j 8862 /api/me | md5sum)" = "$(j 8863 /api/me | md5sum)" ] && [ "$(j 8862 /api/me | md5sum)" = "$(curl -s localhost:8871/api/me | md5sum)" ] && j 8862 /api/me | grep -q "\"guest\":true"'
chk "/__auth/login and /__auth/register render byte-identical to 4b; /signin same status+redirect" 'for u in /__auth/login /__auth/register; do [ "$(j 8862 $u | md5sum)" = "$(j 8863 $u | md5sum)" ] || exit 1; done && [ "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8862/signin)" = "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8863/signin)" ]'
chk "/__auth/verify is still the same response as 4b (no new route)" '[ "$(curl -s -o /dev/null -w "%{http_code}" localhost:8862/__auth/verify)" = "$(curl -s -o /dev/null -w "%{http_code}" localhost:8863/__auth/verify)" ]'
kp 8864; (TEST_NO_COLUMN=1 UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8864 node $F/server.js > $O/nocol.log 2>&1 &); sleep 4
for i in 1 2; do post nocol$i 8864 "email=nc$i@example.com&password=newpassword1" /__auth/register; me nocol$i 8864 > $A/me_nocol$i.json; done; sleep 1
chk "DB without the column (e.g. a dev DB): sign-up still 302 + signed in, error logged once, no crash" 'grep -q "^HTTP/1.1 302" $A/nocol2.hdr && grep -q "\"email\":\"nc2@example.com\"" $A/me_nocol2.json && [ "$(grep -c "could not record unverified status" $O/nocol.log)" = 1 ] && curl -s -o /dev/null -w "%{http_code}" localhost:8864/api/me | grep -q 200'
kp 8864
mkdir -p $O/cmp; cd $O/cmp; n=0; bad=""
while read r; do k=$(echo "$r" | tr '/?=.' '____'); curl -s -o n$k "http://localhost:8862$r"; curl -s -o o$k "http://localhost:8863$r"
  cmp -s n$k o$k || bad="$bad $r"; n=$((n+1)); done < /tmp/routes.txt
echo "$bad" > $O/route_diffs.txt
chk "all 57 routes byte-identical to 4b" '[ -z "$(tr -d " " < $O/route_diffs.txt)" ] && [ $n = 57 ]'
cd $F
python3 $H/shots.py http://localhost:8892 http://localhost:8893 $O/shots > $O/shots.txt 2>&1
chk "browser: /signin and /?settings=1 at 320/390/1280 dark+light: no overflow, no new console errors, pixel-identical to 4b" 'grep -q "^RESULT worst_diff=0.00000 overflow=none new_console_errors=none" $O/shots.txt'
echo "RESULT pass=$PASS fail=$FAIL"; echo "servers left running: 8892 (step6+front) 8893 (4b+front)"; [ $FAIL = 0 ]
