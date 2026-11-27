#!/usr/bin/env bash
# LOCAL tests for deploy-chat108saferxB (box only). Uses a synthetic post-A server.js (post-credits chain + A block) with the real chain tail.
# The test copy of deploy.sh swaps only the app.js/index.html md5 guards for the synthetic files (the real guards stay in deploy.sh).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
R=$(mktemp -d /tmp/c108Btest.XXXXXX); PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
md5(){ md5sum "$1" | awk '{print $1}'; }
python3 "$H/make_synthetic.py" "${RAW_HTML:-/workspace/c108/raw-system2.html}" "$R/server.js" >/dev/null
cat "$DEP/server_block_chat108saferxA.js" >> "$R/server.js"  # synthetic post-A: post-credits chain + the exact A block
printf "console.log('app');\n" > "$R/app.js"; printf "<!doctype html><html><body></body></html>\n" > "$R/index.html"
cp "$R/server.js" "$R/server.js.orig"; SB=$(wc -c < "$R/server.js" | tr -d ' '); S0=$(md5 "$R/server.js"); A0=$(md5 "$R/app.js"); I0=$(md5 "$R/index.html")
sed -e "s/^APP_MD5=.*/APP_MD5=$A0/" -e "s/^INDEX_MD5=.*/INDEX_MD5=$I0/" "$DEP/deploy.sh" > "$R/deploy-test.sh"
export C108_LOCAL_PAYLOAD="$DEP" C108_TEST_BYTES="$SB" C108_TEST_MD5="$S0"
cd "$R"
bash deploy-test.sh --measure > m.out 2>&1; chk "measure exits 0 and changes nothing" '[ $? -eq 0 ] && [ "$(md5 server.js)" = "$S0" ] && grep -q "MEASURE only" m.out'
bash deploy-test.sh --dry-run > d.out 2>&1; chk "dry-run ok, files untouched" 'grep -q "DRY RUN complete" d.out && [ "$(md5 server.js)" = "$S0" ] && ! ls server.js.*.bak-chat108saferxB >/dev/null 2>&1'
C108_TEST_BYTES=$((SB+1)) bash deploy-test.sh --dry-run > s.out 2>&1; chk "size guard refuses" 'grep -q "not the post-A size" s.out'
C108_TEST_MD5=00000000000000000000000000000000 bash deploy-test.sh > p.out 2>&1; chk "md5 pin guard refuses" 'grep -q "is not the pinned" p.out && [ "$(md5 server.js)" = "$S0" ]'
sed -e "s/^APP_MD5=.*/APP_MD5=deadbeef/" deploy-test.sh > deploy-badapp.sh; bash deploy-badapp.sh > a.out 2>&1; chk "app.js md5 guard refuses" 'grep -q "app.js md5" a.out && grep -q ABORT a.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat108saferxB.js
C108_LOCAL_PAYLOAD="$R/bad" bash deploy-test.sh > t.out 2>&1; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" t.out && [ "$(md5 server.js)" = "$S0" ]'
bash deploy-test.sh > ap.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js" ap.out'
chk "backups made and match originals" '[ "$(md5 server.js.*.bak-chat108saferxB)" = "$S0" ] && [ "$(md5 app.js.*.bak-chat108saferxB)" = "$A0" ]'
chk "prefix byte-exact, block appended once" 'cmp -n "$SB" server.js server.js.*.bak-chat108saferxB >/dev/null && [ "$(grep -cF "var TAG = \"chat108saferxB\";" server.js)" = "1" ]'
chk "app.js and index.html untouched" '[ "$(md5 app.js)" = "$A0" ] && [ "$(md5 index.html)" = "$I0" ]'
chk "node --check passes" 'node --check server.js'
S1=$(md5 server.js); bash deploy-test.sh > ap2.out 2>&1; chk "second run is a no-op" 'grep -q "already applied" ap2.out && [ "$(md5 server.js)" = "$S1" ]'
PORT=${PORT:-8831}; RAW_HTML=${RAW_HTML:-/workspace/c108/raw-system2.html} PORT=$PORT node server.js > run.log 2>&1 & SP=$!; sleep 1.5
chk "one attach line each" '[ "$(grep -c "\[chat108saferxB\] preview attached" run.log)" = "1" ] && [ "$(grep -c "\[chat108saferxA\] preview attached" run.log)" = "1" ] && [ "$(grep -c "\[chat105v3home2\] preview attached" run.log)" = "1" ] && grep -q "\[chat107credits\] attached" run.log && grep -q "\[c102r6p\] scrub attached" run.log'
curl -s -o plain.html "http://localhost:$PORT/"; curl -s -o off.html "http://localhost:$PORT/?preview=off"; curl -s -D v3.h -o v3.html "http://localhost:$PORT/?preview=v3"
curl -s -o ck.html -H "Cookie: td_v3p=1" "http://localhost:$PORT/"
AC=$(curl -s -o b9.css -w "%{http_code}" "http://localhost:$PORT/__v3p/b9.css"); AJ=$(curl -s -o b9.js -w "%{http_code}" "http://localhost:$PORT/__v3p/b9.js"); A8=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/__v3p/a8.css")
curl -s -o post.html -X POST "http://localhost:$PORT/?preview=v3"
cp server.js.*.bak-chat108saferxB /tmp/c108B_pre.js; kill $SP; sleep 0.5
RAW_HTML=${RAW_HTML:-/workspace/c108/raw-system2.html} PORT=$PORT node /tmp/c108B_pre.js > run0.log 2>&1 & SP0=$!; sleep 1.5
curl -s -o plain0.html "http://localhost:$PORT/"; curl -s -o off0.html "http://localhost:$PORT/?preview=off"; curl -s -o v3A.html "http://localhost:$PORT/?preview=v3"; curl -s -o post0.html -X POST "http://localhost:$PORT/?preview=v3"; kill $SP0
chk "normal homepage byte-identical before/after" 'cmp -s plain.html plain0.html && cmp -s off.html off0.html'
chk "preview has hero, band, one signup form" 'grep -q "id=\"v8-hero\"" v3.html && grep -q "id=\"v8-band\"" v3.html && [ "$(grep -o "action=\"/free-brief\"" v3.html | wc -l)" = "1" ]'
chk "cookie preview also transformed" 'grep -q "id=\"v9-story\"" ck.html'
chk "normal homepage has no v8/v9 markup" '! grep -q "v8-\|v9-\|v9b" plain.html && ! grep -q "v8-\|v9-\|v9b" off.html'
chk "assets served (200, css and js), A asset still served" '[ "$AC" = "200" ] && [ "$AJ" = "200" ] && [ "$A8" = "200" ] && grep -q "v9-split" b9.css && grep -q "__v9b" b9.js'
chk "preview has story, strip, charts, 1-2-3 and Full table" 'grep -q "id=\"v9-story\"" v3.html && grep -q "id=\"v9-strip\"" v3.html && grep -q "id=\"v9-charts\"" v3.html && grep -q "id=\"v9-how\"" v3.html && grep -q "<details class=\"v9-full\"" v3.html'
chk "all seven v3 cards kept once, context table kept" 'for i in v3-snap v3-gauges v3-prices v3-gold v3-cal v3-tiles v3-moves; do [ "$(grep -o "id=\"$i\"" v3.html | wc -l)" = "1" ] || exit 1; done; [ "$(grep -o "<table class=\"ctx\"" v3.html | wc -l)" = "$(grep -o "<table class=\"ctx\"" v3A.html | wc -l)" ]'
chk "A preview output otherwise kept (hero, band, tabs)" 'grep -q "id=\"v8-hero\"" v3.html && grep -q "id=\"v8-band\"" v3.html && grep -q "class=\"v8-tabs" v3.html'
chk "POST / unchanged by B" 'cmp -s post.html post0.html'
chk "preview keeps 48 menu links and both sheets" '[ "$(python3 -c "import re,sys;t=open(\"v3.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(len(re.findall(r\"<a \",t[i:j])))")" = "48" ]'
head -c -1 "$R/server.js.orig" > "$R/notail.js"; printf ";" >> "$R/notail.js"
python3 "$DEP/patch_chat108saferxB.py" "$R/notail.js" "$DEP/server_block_chat108saferxB.js" "$DEP/server_block_chat108saferxA.js" "$SB" > "$R/nt.out" 2>&1; chk "patch refuses when server.js does not end with the A block" 'grep -q "does not end with the chat108saferxA block" "$R/nt.out"'
node -e 'require("http");' && RAWV3=/workspace/c108/dev-v3A.html node -e '
const fs=require("fs");require("/workspace/c108/deploy-chat108saferxA/server_block_chat105v3home2.js");require("/workspace/c108/deploy-chat108saferxA/server_block_chat108saferxA.js");require(process.argv[1]);
const t=fs.readFileSync(process.env.RAWV3,"utf8"),o=globalThis.__chat108saferxB.transform(t);
if(!o||o.indexOf("id=\"v9-story\"")<0)process.exit(1);
if(globalThis.__chat108saferxB.transform(o)!==null)process.exit(2);
if(globalThis.__chat108saferxB.transform(t.replace("<div class=\"v3-grid\">","<div class=\"v3-grid\"><p>x</p>"))!==null)process.exit(3);
if(globalThis.__chat108saferxB.transform(t.replace(/ v8a/,""))!==null)process.exit(4);' "$DEP/server_block_chat108saferxB.js" > "$R/real.out" 2>&1; chk "transform works on the REAL dev A output; idempotent; unknown grid or no A = untouched" '[ $? -eq 0 ]'
echo "RESULT pass=$PASS fail=$FAIL dir=$R"
[ "$FAIL" = "0" ]
