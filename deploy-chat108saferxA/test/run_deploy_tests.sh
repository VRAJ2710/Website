#!/usr/bin/env bash
# LOCAL tests for deploy-chat108saferxA (box only). Uses a synthetic post-credits server.js with the real chain tail.
# The test copy of deploy.sh swaps only the app.js/index.html md5 guards for the synthetic files (the real guards stay in deploy.sh).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
R=$(mktemp -d /tmp/c108test.XXXXXX); PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
md5(){ md5sum "$1" | awk '{print $1}'; }
python3 "$H/make_synthetic.py" "${RAW_HTML:-/workspace/c108/raw-system.html}" "$R/server.js" >/dev/null
printf "console.log('app');\n" > "$R/app.js"; printf "<!doctype html><html><body></body></html>\n" > "$R/index.html"
SB=$(wc -c < "$R/server.js" | tr -d ' '); S0=$(md5 "$R/server.js"); A0=$(md5 "$R/app.js"); I0=$(md5 "$R/index.html")
sed -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$DEP/deploy.sh" > "$R/deploy-test.sh"
export C108_LOCAL_PAYLOAD="$DEP" C108_TEST_BYTES="$SB"
cd "$R"
bash deploy-test.sh --measure > m.out 2>&1; chk "measure exits 0 and changes nothing" '[ $? -eq 0 ] && [ "$(md5 server.js)" = "$S0" ] && grep -q "MEASURE only" m.out'
bash deploy-test.sh --dry-run > d.out 2>&1; chk "dry-run ok, files untouched" 'grep -q "DRY RUN complete" d.out && [ "$(md5 server.js)" = "$S0" ] && ! ls server.js.*.bak-chat108saferxA >/dev/null 2>&1'
C108_TEST_BYTES=$((SB+1)) bash deploy-test.sh --dry-run > s.out 2>&1; chk "size guard refuses" 'grep -q "not the post-credits size" s.out'
C108_SERVER_MD5=00000000000000000000000000000000 bash deploy-test.sh > p.out 2>&1; chk "md5 pin guard refuses" 'grep -q "is not the pinned" p.out && [ "$(md5 server.js)" = "$S0" ]'
sed -e "s/^APP_MD5=.*/APP_MD5=deadbeef/" deploy-test.sh > deploy-badapp.sh; bash deploy-badapp.sh > a.out 2>&1; chk "app.js md5 guard refuses" 'grep -q "app.js md5" a.out && grep -q ABORT a.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat108saferxA.js
C108_LOCAL_PAYLOAD="$R/bad" bash deploy-test.sh > t.out 2>&1; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" t.out && [ "$(md5 server.js)" = "$S0" ]'
C108_SERVER_MD5="$S0" bash deploy-test.sh > ap.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js" ap.out'
chk "backups made and match originals" '[ "$(md5 server.js.*.bak-chat108saferxA)" = "$S0" ] && [ "$(md5 app.js.*.bak-chat108saferxA)" = "$A0" ]'
chk "prefix byte-exact, block appended once" 'cmp -n "$SB" server.js server.js.*.bak-chat108saferxA >/dev/null && [ "$(grep -cF "var TAG = \"chat108saferxA\";" server.js)" = "1" ]'
chk "app.js and index.html untouched" '[ "$(md5 app.js)" = "$A0" ] && [ "$(md5 index.html)" = "$I0" ]'
chk "node --check passes" 'node --check server.js'
S1=$(md5 server.js); bash deploy-test.sh > ap2.out 2>&1; chk "second run is a no-op" 'grep -q "already applied" ap2.out && [ "$(md5 server.js)" = "$S1" ]'
PORT=${PORT:-8821}; RAW_HTML=${RAW_HTML:-/workspace/c108/raw-system.html} PORT=$PORT node server.js > run.log 2>&1 & SP=$!; sleep 1.5
chk "one attach line each" '[ "$(grep -c "\[chat108saferxA\] preview attached" run.log)" = "1" ] && [ "$(grep -c "\[chat105v3home2\] preview attached" run.log)" = "1" ] && grep -q "\[chat107credits\] attached" run.log && grep -q "\[c102r6p\] scrub attached" run.log'
curl -s -o plain.html "http://localhost:$PORT/"; curl -s -o off.html "http://localhost:$PORT/?preview=off"; curl -s -D v3.h -o v3.html "http://localhost:$PORT/?preview=v3"
curl -s -o ck.html -H "Cookie: td_v3p=1" "http://localhost:$PORT/"
AC=$(curl -s -o a8.css -w "%{http_code}" "http://localhost:$PORT/__v3p/a8.css"); AJ=$(curl -s -o a8.js -w "%{http_code}" "http://localhost:$PORT/__v3p/a8.js")
cp server.js.*.bak-chat108saferxA /tmp/c108_pre.js; kill $SP; sleep 0.5
RAW_HTML=${RAW_HTML:-/workspace/c108/raw-system.html} PORT=$PORT node /tmp/c108_pre.js > run0.log 2>&1 & SP0=$!; sleep 1.5
curl -s -o plain0.html "http://localhost:$PORT/"; curl -s -o off0.html "http://localhost:$PORT/?preview=off"; kill $SP0
chk "normal homepage byte-identical before/after" 'cmp -s plain.html plain0.html && cmp -s off.html off0.html'
chk "preview has hero, band, one signup form" 'grep -q "id=\"v8-hero\"" v3.html && grep -q "id=\"v8-band\"" v3.html && [ "$(grep -o "action=\"/free-brief\"" v3.html | wc -l)" = "1" ]'
chk "cookie preview also transformed" 'grep -q "id=\"v8-hero\"" ck.html'
chk "normal homepage has no v8 markup" '! grep -q "v8-" plain.html && ! grep -q "v8-" off.html'
chk "assets served (200, css and js)" '[ "$AC" = "200" ] && [ "$AJ" = "200" ] && grep -q "v8-hero" a8.css && grep -q "__v8a" a8.js'
chk "preview keeps 48 menu links and both sheets" '[ "$(python3 -c "import re,sys;t=open(\"v3.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(len(re.findall(r\"<a \",t[i:j])))")" = "48" ]'
echo "RESULT pass=$PASS fail=$FAIL dir=$R"
[ "$FAIL" = "0" ]
