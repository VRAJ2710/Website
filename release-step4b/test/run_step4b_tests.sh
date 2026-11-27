#!/usr/bin/env bash
# LOCAL tests for release-step4b (box only). Fixture = step-3 stand-in + the real step-4 installer applied, then 4b on top.
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); S4=$(dirname "$DEP")/release-step4; F=/tmp/r4bfix; O=/tmp/r4bout; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
read SM SS RM < <(bash "$S4/test/make_fixture.sh" $F | tail -1); rm -rf $O; mkdir -p $O; cd $F
R4_LOCAL_PAYLOAD="$S4" R4_LOCAL_TEST=1 R4_TEST_SERVER_SIZE="$SS" R4_TEST_R6N_MD5="$RM" bash "$S4/deploy.sh" --dir $F > $O/s4.out 2>&1
chk "fixture: real step-4 installer applied" 'grep -q "DONE: server.js md5" $O/s4.out'
git add -A >/dev/null 2>&1; git commit -qm step4 >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
mkdir -p /tmp/r4bold; cp server.js app.js index.html styles.css c93.css /tmp/r4bold/
S4MD5=$(md5sum < server.js | cut -c1-32); S4SZ=$(wc -c < server.js)
export R4B_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R4B_LOCAL_TEST=1 R4B_TEST_SERVER_MD5=$S4MD5 R4B_TEST_SERVER_SIZE=$S4SZ D "$@"; }
snapall > $O/pre.md5
D --measure > $O/g0.out 2>&1; chk "refuses without the staged step-4 server.js (real pins: ec413c6b, 2,517,162 B)" 'grep -q "not the staged step-4" $O/g0.out && snapall | cmp -s - $O/pre.md5'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R4B_LOCAL_TEST=1 R4B_TEST_SERVER_MD5=0000 R4B_TEST_SERVER_SIZE=$S4SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the staged step-4" $O/g1.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done && snapall | cmp -s - $O/pre.md5'
python3 -c "
b=open('server.js','rb').read(); i=b.rindex(b'padding:18px 16px'); open('server.js','wb').write(b[:i]+b'padding:18px 17px'+b[i+17:])"
R4B_LOCAL_TEST=1 R4B_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R4B_TEST_SERVER_SIZE=$S4SZ D --dry-run > $O/g2.out 2>&1; cp /tmp/r4bold/server.js server.js
chk "refuses when the step-4 block differs by one byte (md5 override, same size)" 'grep -q "does not end with the exact step-4" $O/g2.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat110navyb.js
R4B_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g3.out 2>&1; rm -rf bad; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" $O/g3.out'
snapall > $O/pre.md5
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step4b-* | head -1)
chk "snapshot: server.js (= step 4) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r4bold/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ]'
chk "exactly 1 file changed (server.js); app/index/styles/c93 byte-identical; node --check" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r4bold/$f || exit 1; done && node --check server.js'
diff /tmp/r4bold/server.js server.js > $O/server.diff
chk "server.js diff = only the SITE_CSS line and the SITE_LINK line, +114 B; everything before the block byte-identical" '[ "$(grep -c "^<" $O/server.diff)" = 2 ] && [ "$(grep -c "^>" $O/server.diff)" = 2 ] && [ $(( $(wc -c < server.js) - $(wc -c < /tmp/r4bold/server.js) )) = 114 ] && grep "^>" $O/server.diff | grep -q "padding-bottom:184px" && [ "$(grep "^>" $O/server.diff | grep -c "site.css?v=chat110navyb")" = 1 ] && N=$(( $(wc -c < /tmp/r4bold/server.js) - $(wc -c < $DEP/server_block_chat110navy.js) )) && cmp -n $N server.js /tmp/r4bold/server.js'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 4 back byte-exact" 'cmp -s server.js /tmp/r4bold/server.js'
sleep 1; T > $O/a2.out 2>&1; chk "re-apply ok" 'grep -q "DONE" $O/a2.out'
cp server.js /tmp/r4bnew.server.js
# serve old (step 4) and new (4b) and compare every route
CD=/tmp/r2cache; for p in 8871 8862 8863 8892 8893; do kp $p; done; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > /tmp/r4bproxy.log 2>&1 &); sleep 0.7
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8862 node server.js > $O/rel.log 2>&1 &)
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8863 node /tmp/r4bold/server.js > $O/old.log 2>&1 &); sleep 2.5
(UPSTREAM_PORT=8862 STATIC_DIR=/tmp/r4bold EDITS=$S4/index_edits.json PORT=8892 node $S4/test/navyfront.js > $O/front.log 2>&1 &)
(UPSTREAM_PORT=8863 STATIC_DIR=/tmp/r4bold EDITS=$S4/index_edits.json PORT=8893 node $S4/test/navyfront.js > $O/oldfront.log 2>&1 &); sleep 1
chk "log: navy + credits + r6p attach once each" 'for t in "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done'
mkdir -p $O/cmp; cd $O/cmp; n=0; bad=""
while read r; do k=$(echo "$r" | tr '/?=.' '____'); curl -s -o n$k "http://localhost:8862$r"; curl -s -o o$k "http://localhost:8863$r"
  if ! cmp -s n$k o$k; then if ! cmp -s n$k <(sed 's#/__navy/site.css?v=chat110navy">#/__navy/site.css?v=chat110navyb">#' o$k); then bad="$bad $r"; fi; fi; n=$((n+1)); done < /tmp/routes.txt
echo "$bad" > $O/route_diffs.txt
chk "all 57 routes: 4b output == step-4 output except the site.css cache tag (v=chat110navyb)" '[ -z "$(cat $O/route_diffs.txt | tr -d " ")" ] && [ $n = 57 ]'
chk "inner pages link /__navy/site.css?v=chat110navyb, none still on the old tag" 'grep -q "site.css?v=chat110navyb" n_gold_ && ! grep -q "site.css?v=chat110navy\"" n_gold_ && grep -q "site.css?v=chat110navyb" n_brief_'
curl -s -o css.new "http://localhost:8862/__navy/site.css?v=chat110navyb"; curl -s -o css.old "http://localhost:8863/__navy/site.css?v=chat110navy"
chk "/__navy/site.css = step-4 css + exactly the one new rule" '[ "$(diff css.old css.new | grep -c "^[<>]")" = 1 ] && diff css.old css.new | grep -q "^>  html.nvb body:has(#c101-inst){padding-bottom:184px!important}$"'
j(){ curl -s "http://localhost:$1$2"; }
chk "auth untouched: /__auth/login, /__auth/register, /api/me, /signin identical" 'for u in /__auth/login /__auth/register /api/me; do [ "$(j 8862 "$u" | md5sum)" = "$(j 8863 "$u" | md5sum)" ] || exit 1; done && [ "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8862/signin)" = "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8863/signin)" ]'
python3 $H/footer_cover.py http://localhost:8892 http://localhost:8893 > $O/cover.txt 2>&1
chk "browser: footer 0 px covered at 320/390 with the install bar showing (4b) on 8 pages; step 4 still shows the bug" 'grep -q "^RESULT new_max_covered=0 " $O/cover.txt && grep -q " old_max_covered=[1-9]" $O/cover.txt'
echo "RESULT pass=$PASS fail=$FAIL"; echo "servers left running: 8892 (4b+front) 8893 (step 4+front)"; [ $FAIL = 0 ]
