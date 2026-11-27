#!/usr/bin/env bash
# LOCAL tests for release-step3 (box only). Step-2 stand-in = stub + r6p scrub (installed by the pinned step-2 installer) + v3 blocks.
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); F=/tmp/r3fix; PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ P=$(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); [ -n "$P" ] && kill $P; true; }
read SM SS RM < <(bash "$H/make_fixture.sh" $F | tail -1); O=/tmp/r3out; rm -rf $O; mkdir -p $O; cd $F
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
snapall > /tmp/r3_pre.md5; cp server.js /tmp/r3srv2
export R3_LOCAL_PAYLOAD="$DEP" R3_LOCAL_TEST=1 R3_TEST_SERVER_SIZE="$SS" R3_TEST_R6N_MD5="$RM"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
chk "fixture is the step-2 build (one r6p attach, no r6n)" '[ "$(grep -c "\[c102r6p\] scrub attached" server.js)" = 1 ] && ! grep -q "\[c102r6n\] scrub attached" server.js'
D --measure > $O/m.out 2>&1; chk "measure ok, nothing written, prints expected md5/size" 'grep -q "MEASURE only" $O/m.out && grep -q "post-step-2 build, byte-exact" $O/m.out && snapall | cmp -s - /tmp/r3_pre.md5'
STEP2_SERVER_MD5=$SM D --dry-run > $O/d.out 2>&1; chk "dry-run ok with the optional step-2 md5, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - /tmp/r3_pre.md5'
STEP2_SERVER_MD5=0000 D --dry-run > $O/g0.out 2>&1; chk "refuses a wrong STEP2_SERVER_MD5" 'grep -q "is not STEP2_SERVER_MD5" $O/g0.out'
R3_TEST_SERVER_SIZE=2472342 D --dry-run > $O/g1.out 2>&1; chk "refuses a server.js of the wrong size" 'grep -q "not the post-step-2" $O/g1.out'
python3 -c "
b=open('server.js','rb').read(); i=b.index(b'realYieldPrev'); open('server.js','wb').write(b[:i]+b'realYieldPreX'+b[i+13:])"
D --dry-run > $O/g2.out 2>&1; cp /tmp/r3srv2 server.js; chk "refuses when one r6p byte differs (same size)" 'grep -q "not exactly the step-2 build" $O/g2.out'
cp /tmp/r3srv2 /tmp/r3x; python3 -c "
b=open('server.js','rb').read(); i=b.index(b'chat109v3default'); open('server.js','wb').write(b[:i]+b'chat109v3defaulT'+b[i+16:])"
D --dry-run > $O/g3.out 2>&1; cp /tmp/r3srv2 server.js; chk "refuses when a v3 block byte differs" 'grep -q "not exactly the step-2 build" $O/g3.out'
echo x >> index.html; D --dry-run > $O/g4.out 2>&1; git checkout -q index.html; chk "refuses a changed index.html" 'grep -q "index.html md5" $O/g4.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat107credits.js
R3_LOCAL_PAYLOAD=$F/bad D --dry-run > $O/g5.out 2>&1; rm -rf bad; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" $O/g5.out'
snapall > /tmp/r3_pre.md5
D > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
S=$(ls -d $F/.release-snapshots/step3-* | head -1)
chk "snapshot has server.js + manifest + restore script" '[ -f $S/manifest.json ] && [ -f $S/restore_release.py ] && cmp -s $S/files/server.js /tmp/r3srv2'
chk "only server.js changed; it is step 2 + credits block appended, node --check" '[ "$(snapall | diff - /tmp/r3_pre.md5 | grep -c "^<")" = 1 ] && cmp -n $(wc -c < /tmp/r3srv2) server.js /tmp/r3srv2 && node --check server.js && [ $(wc -c < server.js) = $(( $(wc -c < /tmp/r3srv2) + $(wc -c < $DEP/server_block_chat107credits.js) )) ]'
CD=/tmp/r2cache; kp 8871; kp 8860; kp 8861; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > /tmp/r3proxy.log 2>&1 &); sleep 0.7
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8860 node server.js > $O/rel.log 2>&1 &)
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8861 node /tmp/r3srv2 > $O/old.log 2>&1 &); sleep 2.5
chk "release log: credits + r6p + 5 v3 attach lines, once each" 'for t in "chat107credits\] attached" "c102r6p\] scrub attached" "chat105v3home2\] preview attached" "chat108saferxA\] preview attached" "chat108saferxB\] preview attached" "chat108saferxC\] preview attached" "chat109v3default\] attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done'
mkdir -p $O/cmp; cd $O/cmp
curl -s -D h.txt -o home.html http://localhost:8860/; curl -s -o home2.html http://localhost:8861/
chk "/ is the v3 home with step-1 headers; minus the credits additions it is byte-identical to step 2" 'grep -q "id=\"v9-story\"" home.html && grep -qi "x-dispatch-home: v3" h.txt && python3 $H/strip_credits.py home.html home2.html'
chk "/ has the FRED footer notice once and the credits script" '[ "$(grep -o "class=\"c107-fred\"" home.html | wc -l)" = 1 ] && grep -q "id=\"c107-credits\"" home.html && grep -q "This product uses FRED® data but is not endorsed or certified by the Federal Reserve Bank of St. Louis." home.html'
j(){ curl -s "http://localhost:$1$2"; }
chk "r6p unchanged: real-yield blank-day fix, equal days kept" '[ "$(j 8860 "/api/real-yield?case=blank" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "None None" ] && [ "$(j 8860 "/api/real-yield?case=equal" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "2.79 0" ]'
chk "r6p unchanged: page fixes on /, no scripts on the sign-in page, JSON byte-identical" 'grep -q "id=\"c102r6o-fred\"" home.html && [ "$(j 8860 /__auth/login | grep -c "<script")" = 0 ] && [ "$(j 8860 /api/c100/macro | md5sum)" = "$(j 8861 /api/c100/macro | md5sum)" ] && [ "$(j 8860 /api/me | md5sum)" = "$(j 8861 /api/me | md5sum)" ]'
curl -s -o cal.html http://localhost:8860/calendar/; curl -s -o cal2.html http://localhost:8861/calendar/
chk "/calendar/: no raw (FRED ID) in the HTML text; markers instead; otherwise identical to step 2" '! python3 -c "import re,sys;t=re.sub(r\"<script\\b[\\s\\S]*?</script\\s*>|<style\\b[\\s\\S]*?</style\\s*>|<[^>]*>\",\" \",open(\"cal.html\").read());sys.exit(0 if re.search(r\"\\(FRED [A-Z0-9]\",t) else 1)" && grep -q "data-c107-ids=" cal.html && python3 $H/strip_credits.py cal.html cal2.html'
curl -s -o meth.html http://localhost:8860/methodology; chk "/methodology has the credits paragraph once" '[ "$(grep -o "class=\"c107-meth\"" meth.html | wc -l)" = 1 ]'
python3 - > links.txt <<'PY'
import re;t=open("/workspace/c109/live_home.html").read();i=t.index('<details class="menu">');j=t.index("</details>",i)
print("\n".join(sorted(set(h for h in re.findall(r'href="([^"]+)"',t[i:j]) if h.startswith("/") and h!="/"))))
PY
bad=0; while read l; do a=$(curl -s -o /tmp/r3a -w '%{http_code}' "http://localhost:8860$l"); b=$(curl -s -o /tmp/r3b -w '%{http_code}' "http://localhost:8861$l"); [ "$a" = "$b" ] || { echo "  code differs: $l"; bad=1; }; python3 $H/strip_credits.py /tmp/r3a /tmp/r3b || { echo "  differs beyond credits: $l"; bad=1; }; done < links.txt
chk "all $(wc -l < links.txt) menu-link routes: same status, byte-identical to step 2 apart from the credits additions" '[ $bad = 0 ]'
for p in "/?preview=off" "/?settings=1" "/?checkout=1" /styles.css /app.js; do n=$(echo "$p" | tr '/?=.' '____'); curl -s -o r$n "http://localhost:8860$p"; curl -s -o o$n "http://localhost:8861$p"; done
chk "old-home queries differ only by credits; styles.css and app.js byte-identical" 'for n in __preview_off __settings_1 __checkout_1; do python3 $H/strip_credits.py r$n o$n || exit 1; done; cmp -s r_styles_css o_styles_css && cmp -s r_app_js o_app_js'
cd $F; kp 8860; kp 8861
python3 $S/restore_release.py $S > $O/rs.out 2>&1; chk "restore puts server.js back exactly (every file md5)" 'grep -q "\[restore\] DONE" $O/rs.out && snapall | cmp -s - /tmp/r3_pre.md5'
D --dry-run > $O/d2.out 2>&1; chk "after restore the installer accepts the tree again" 'grep -q "DRY RUN complete" $O/d2.out'
echo "RESULT pass=$PASS fail=$FAIL"; [ $FAIL = 0 ]
