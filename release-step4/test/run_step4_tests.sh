#!/usr/bin/env bash
# LOCAL tests for release-step4 (box only). Step-3 stand-in = stub + r6p + v3 blocks + credits (installed by the pinned step-2/3 installers).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); F=/tmp/r4fix; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
read SM SS RM < <(bash "$H/make_fixture.sh" $F | tail -1); O=/tmp/r4out; rm -rf $O; mkdir -p $O; cd $F
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
snapall > /tmp/r4_pre.md5; mkdir -p /tmp/r4old; cp server.js app.js index.html styles.css c93.css /tmp/r4old/
export R4_LOCAL_PAYLOAD="$DEP" R4_LOCAL_TEST=1 R4_TEST_SERVER_SIZE="$SS" R4_TEST_R6N_MD5="$RM"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
D --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && grep -q "post-step-3 build, byte-exact" $O/m.out && snapall | cmp -s - /tmp/r4_pre.md5'
STEP3_SERVER_MD5=$SM D --dry-run > $O/d.out 2>&1; chk "dry-run ok with the optional step-3 md5, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - /tmp/r4_pre.md5'
STEP3_SERVER_MD5=0000 D --dry-run > $O/g0.out 2>&1; chk "refuses a wrong STEP3_SERVER_MD5" 'grep -q "is not STEP3_SERVER_MD5" $O/g0.out'
R4_TEST_SERVER_SIZE=2472342 D --dry-run > $O/g1.out 2>&1; chk "refuses a server.js of the wrong size (e.g. step 2)" 'grep -q "not the post-step-3" $O/g1.out'
python3 -c "
b=open('server.js','rb').read(); i=b.index(b'function fredIds'); open('server.js','wb').write(b[:i]+b'function fredIdz'+b[i+16:])"
D --dry-run > $O/g2.out 2>&1; cp /tmp/r4old/server.js server.js; chk "refuses when one credits byte differs (same size)" 'grep -q "not exactly the step-3 build" $O/g2.out'
echo x >> index.html; D --dry-run > $O/g3.out 2>&1; git checkout -q index.html; chk "refuses a changed index.html" 'grep -q "index.html md5" $O/g3.out'
echo "//x" >> app.js; D --dry-run > $O/g4.out 2>&1; git checkout -q app.js; chk "refuses a changed app.js" 'grep -q "app.js md5" $O/g4.out'
echo "/*x*/" >> styles.css; D --dry-run > $O/g5.out 2>&1; git checkout -q styles.css; chk "refuses a changed styles.css" 'grep -q "styles.css md5" $O/g5.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/*.json "$DEP"/*.css "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat110navy.js
R4_LOCAL_PAYLOAD=$F/bad D --dry-run > $O/g6.out 2>&1; rm -rf bad; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" $O/g6.out'
snapall > /tmp/r4_pre.md5
D > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
S=$(ls -d $F/.release-snapshots/step4-* | head -1)
chk "snapshot has all 5 files + manifest + restore script" '[ -f $S/manifest.json ] && [ -f $S/restore_release.py ] && for f in server.js app.js index.html styles.css c93.css; do cmp -s $S/files/$f /tmp/r4old/$f || exit 1; done'
chk "exactly 5 files changed, to the expected md5s; node --check" '[ "$(snapall | diff - /tmp/r4_pre.md5 | grep -c "^<")" = 5 ] && [ "$(md5sum < app.js | cut -c1-32)" = f7678ca9b0284afea8bf74581fdf44eb ] && [ "$(md5sum < styles.css | cut -c1-32)" = 290a380259ad5a4f1bdbcc787df8e196 ] && [ "$(md5sum < c93.css | cut -c1-32)" = 7858e81781d304e1d1ef19a4562a4fc6 ] && [ "$(md5sum < index.html | cut -c1-32)" = 11652c2aaeb8a06a5d83c308d3a472e7 ] && node --check server.js && node --check app.js'
chk "server.js = step 3 + navy block appended" 'cmp -n $(wc -c < /tmp/r4old/server.js) server.js /tmp/r4old/server.js && [ $(wc -c < server.js) = $(( $(wc -c < /tmp/r4old/server.js) + $(wc -c < $DEP/server_block_chat110navy.js) )) ]'
# auth / provider-order proof on app.js: every changed line, both sides
diff /tmp/r4old/app.js app.js | grep '^[<>]' > $O/app_changed_lines.txt
chk "app.js changed lines mention no auth/verification/Resend/checkout/provider/Stripe/email_verified/AI-order code" '! grep -Eiq "verif|resend|checkout|stripe|email_verified|webhook|password|login|signin|sign-in|register|/__auth|/api/me|isAdmin|premium-lock|fallbackOrder|providers?[^ a-z]|fallback|xai|anthropic|claude|gemini|openai|grok|CHAT_AI|sendChatMessage|toggleChat|_chat|localStorage.setItem|document.cookie|fetch\(" $O/app_changed_lines.txt'
grep -c '^>' $O/app_changed_lines.txt > $O/app_added_count.txt
CD=/tmp/r2cache; for p in 8871 8860 8861 8890 8891; do kp $p; done; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > /tmp/r4proxy.log 2>&1 &); sleep 0.7
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8860 node server.js > $O/rel.log 2>&1 &)
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8861 node /tmp/r4old/server.js > $O/old.log 2>&1 &); sleep 2.5
(UPSTREAM_PORT=8860 STATIC_DIR=$F EDITS=$DEP/index_edits.json PORT=8890 node $H/navyfront.js > $O/front.log 2>&1 &)
(UPSTREAM_PORT=8861 STATIC_DIR=/tmp/r4old PORT=8891 node $H/navyfront.js > $O/oldfront.log 2>&1 &); sleep 1
chk "release log: navy + credits + r6p + 5 v3 attach lines, once each" 'for t in "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached" "chat105v3home2\] preview attached" "chat108saferxA\] preview attached" "chat108saferxB\] preview attached" "chat108saferxC\] preview attached" "chat109v3default\] attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done'
mkdir -p $O/cmp; cd $O/cmp
curl -s -D h.txt -o home.html http://localhost:8860/; curl -s -o home2.html http://localhost:8861/
chk "/ is the v3 home (X-Dispatch-Home v3) and is exactly navy.transform(step-3 home)" 'grep -q "id=\"v9-story\"" home.html && grep -qi "x-dispatch-home: v3" h.txt && [ "$(node $H/navy_equiv.js $DEP/server_block_chat110navy.js home.html home2.html)" = TRANSFORMED ]'
chk "/ navy: styles link once, no inline c93 css, no Inter link, data-theme=system, tape once, credits + r6p still there" '[ "$(grep -o "/styles.css?v=chat110navy" home.html | wc -l)" = 1 ] && ! grep -q "<style>:root{--paper:#fbfaf7;--ink:#1b1b1b;" home.html && ! grep -q "family=Inter" home.html && grep -q "data-theme=\"system\" data-c110navy=\"1\"" home.html && grep -q "nv-v3 nvb" home.html && grep -q "/__navy/site.css?v=chat110navy" home.html && grep -q "class=\"nv-bbar\"" home.html && [ "$(grep -o "class=\"public-market-tape\"" home.html | wc -l)" = 1 ] && [ "$(grep -o "class=\"c107-fred\"" home.html | wc -l)" = 1 ] && grep -q "id=\"c102r6o-fred\"" home.html'
j(){ curl -s "http://localhost:$1$2"; }
chk "auth untouched: /__auth/login, /__auth/register, /api/me, /signin byte-identical to step 3; no scripts on the sign-in page" 'for u in /__auth/login /__auth/register /api/me "/api/me?x=1"; do [ "$(j 8860 "$u" | md5sum)" = "$(j 8861 "$u" | md5sum)" ] || exit 1; done && [ "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8860/signin)" = "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8861/signin)" ] && [ "$(j 8860 /__auth/login | grep -c "<script")" = 0 ]'
chk "r6p unchanged: real-yield blank-day fix; JSON byte-identical" '[ "$(j 8860 "/api/real-yield?case=blank" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "None None" ] && [ "$(j 8860 /api/c100/macro | md5sum)" = "$(j 8861 /api/c100/macro | md5sum)" ] && [ "$(j 8860 /api/market-reference-quotes | md5sum)" = "$(j 8861 /api/market-reference-quotes | md5sum)" ]'
for p in "/?preview=off" "/?settings=1" "/?checkout=1"; do n=$(echo "$p" | tr '/?=.' '____'); curl -s -o r$n "http://localhost:8860$p"; curl -s -o o$n "http://localhost:8861$p"; curl -s -D fh$n -o f$n "http://localhost:8890$p"; done
chk "/?preview=off, /?settings=1, /?checkout=1 on the stub (which answers every /?... with the captured home) = navy.transform(step 3)" 'for n in __preview_off __settings_1 __checkout_1; do [ "$(node $H/navy_equiv.js $DEP/server_block_chat110navy.js r$n o$n)" = TRANSFORMED ] || exit 1; done'
cat > spa_null.js <<'JS'
const fs=require("fs"),http=require("http");const SP=http.Server.prototype,e0=SP.emit;const f=function(){return e0.apply(this,arguments)};f.__chat109v3default=1;SP.emit=f;
const log=console.log;console.log=()=>{};eval(fs.readFileSync(process.argv[2],"utf8"));console.log=log;let bad=0;
for(const p of process.argv.slice(3)){const t=fs.readFileSync(p,"utf8");if(globalThis.__c110navy.transform(t)!==null){log("TOUCHED "+p);bad=1}}log(bad?"BAD":"UNTOUCHED");
JS
chk "real live SPA shells (/?settings=1 capture + 11 SPA routes) and the sign-in page are left untouched by the navy block" '[ "$(node spa_null.js $DEP/server_block_chat110navy.js $(grep -l "/app.js?v=chat102r6n" /workspace/c111/live2/*.body) /workspace/c111/live2/___auth_login.body | tail -1)" = UNTOUCHED ]'
curl -s -D fhp -o fp "http://localhost:8890/playbook/"; curl -s -D fhs -o fs "http://localhost:8890/screener/"
chk "SPA shell with the new index.html (/playbook/, /screener/ via the test front): all 7 edits land, v=chat110navy, dispatch-shell, no chat1/chat93/chat102r6n" 'for x in p s; do grep -qi "x-test-index-edits: applied" fh$x && grep -q "/app.js?v=chat110navy" f$x && grep -q "/styles.css?v=chat110navy" f$x && grep -q "classList.add(.dispatch-shell.)" f$x && ! grep -Eq "v=chat1\"|c93.css\?v=chat93|chat102r6n" f$x || exit 1; done'
cd $O/cmp; python3 - > links.txt <<'PY'
import re;t=open("/workspace/c109/live_home.html").read();i=t.index('<details class="menu">');j=t.index("</details>",i)
print("\n".join(sorted(set(h for h in re.findall(r'href="([^"]+)"',t[i:j]) if h.startswith("/") and h!="/"))))
PY
bad=0; nt=0; ns=0; : > routes.txt; while read l; do a=$(curl -s -o /tmp/r4a -w '%{http_code}' "http://localhost:8860$l"); b=$(curl -s -o /tmp/r4b -w '%{http_code}' "http://localhost:8861$l"); [ "$a" = "$b" ] || { echo "  code differs: $l"; bad=1; }
  r=$(node $H/navy_equiv.js $DEP/server_block_chat110navy.js /tmp/r4a /tmp/r4b "${l%%\?*}") || { echo "  differs beyond navy: $l"; bad=1; }; echo "$l $a $r" >> routes.txt; [ "$r" = TRANSFORMED ] && nt=$((nt+1)); [ "$r" = SAME ] && ns=$((ns+1)); done < links.txt
chk "all $(wc -l < links.txt) menu-link routes: same status; each page is exactly navy.transform(step 3) or byte-identical ($nt navy, $ns unchanged SPA/other)" '[ $bad = 0 ]'
chk "every 200 menu-link route ends in </html>; redirects unchanged ($(grep -vc " 200 " routes.txt) redirect)" 'while read l c r; do [ "$c" = 200 ] || continue; curl -s "http://localhost:8860$l" | tail -c 200 | grep -q "</html>" || exit 1; done < routes.txt'
chk "/__navy/site.css served by the block (text/css, 200)" '[ "$(curl -s -o /dev/null -w "%{http_code} %{content_type}" localhost:8860/__navy/site.css?v=chat110navy)" = "200 text/css; charset=utf-8" ]'
chk "static via the test front: new app.js/styles.css/c93.css served" '[ "$(curl -s localhost:8890/app.js?v=chat110navy | md5sum | cut -c1-32)" = f7678ca9b0284afea8bf74581fdf44eb ] && [ "$(curl -s localhost:8890/styles.css?v=chat110navy | md5sum | cut -c1-32)" = 290a380259ad5a4f1bdbcc787df8e196 ]'
cd $F; echo "servers left running for the browser probe (8860 rel, 8861 old, 8890 rel+front, 8891 old+front)"
rm -rf /tmp/r4new; mkdir -p /tmp/r4new; cp server.js app.js index.html styles.css c93.css /tmp/r4new/
python3 $S/restore_release.py $S > $O/rs.out 2>&1; chk "restore puts all 5 files back exactly (every file md5)" 'grep -q "\[restore\] DONE" $O/rs.out && snapall | cmp -s - /tmp/r4_pre.md5'
D --dry-run > $O/d2.out 2>&1; chk "after restore the installer accepts the tree again" 'grep -q "DRY RUN complete" $O/d2.out'
echo "RESULT pass=$PASS fail=$FAIL"; [ $FAIL = 0 ]
