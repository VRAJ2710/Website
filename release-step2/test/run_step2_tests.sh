#!/usr/bin/env bash
# LOCAL tests for release-step2 (box only). Release-1 stand-in = stub + REAL r6n scrub + five v3 blocks; GETs other than / come
# from the live site through a caching proxy (same bytes for both servers). Seeded /api/real-yield cases test the blank-day fix.
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); F=/tmp/r2fix; PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ P=$(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); [ -n "$P" ] && kill $P; true; }
read SM SS RM < <(bash "$H/make_fixture.sh" $F | tail -1); O=/tmp/r2out; rm -rf $O; mkdir -p $O; cd $F
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
snapall > /tmp/r2_pre.md5
export R2_LOCAL_PAYLOAD="$DEP" R2_LOCAL_TEST=1 R2_TEST_SERVER_MD5="$SM" R2_TEST_SERVER_SIZE="$SS" R2_TEST_R6N_MD5="$RM"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
D --measure > $O/m.out 2>&1; chk "measure ok, nothing written, prints expected md5" 'grep -q "MEASURE only" $O/m.out && grep -q "r6n scrub ok" $O/m.out && snapall | cmp -s - /tmp/r2_pre.md5'
D --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - /tmp/r2_pre.md5'
R2_TEST_SERVER_MD5=0000 D --dry-run > $O/g1.out 2>&1; chk "refuses a server.js that is not the live step-1 pin" 'grep -q "is not the live step-1 server" $O/g1.out'
cp app.js /tmp/r2app; echo x >> app.js; D --dry-run > $O/g2.out 2>&1; cp /tmp/r2app app.js; chk "refuses a changed app.js" 'grep -q "app.js md5" $O/g2.out && grep -q "Nothing in the project was changed" $O/g2.out'
cp server.js /tmp/r2srv; python3 -c "
b=open('server.js','rb').read(); i=b.index(b'chat108saferxB'); open('server.js','wb').write(b[:i]+b'chat108saferxb'+b[i+14:])"
R2_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) D --dry-run > $O/g3.out 2>&1; cp /tmp/r2srv server.js; chk "refuses when a v3 block byte differs (same size)" 'grep -q "not exactly r6n backup" $O/g3.out'
cp server.js.20261111-070219.bak-chat102r6o /tmp/r2bak; cp server.js.20261111-070219.bak-chat102r6o server.js.20261112-000000.bak-chat102r6o; D --dry-run > $O/g4.out 2>&1; rm server.js.20261112-000000.bak-chat102r6o; chk "refuses two r6n backups" 'grep -q "expected exactly one" $O/g4.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_c102r6p.js
R2_LOCAL_PAYLOAD=$F/bad D --dry-run > $O/g5.out 2>&1; rm -rf bad; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" $O/g5.out'
snapall > /tmp/r2_pre.md5
D > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
S=$(ls -d $F/.release-snapshots/step2-* | head -1)
chk "snapshot has server.js + manifest + restore script" '[ -f $S/manifest.json ] && [ -f $S/restore_release.py ] && cmp -s $S/files/server.js /tmp/r2srv'
chk "only server.js changed" '[ "$(snapall | diff - /tmp/r2_pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - /tmp/r2_pre.md5 | grep -q "server.js$"'
chk "new server.js = prefix + r6p + same v3 blocks, node --check" 'python3 -c "
import sys
n=open(\"server.js\",\"rb\").read(); o=open(\"/tmp/r2srv\",\"rb\").read(); m=b\"// chat102r6c last-write scrub.\"
i=o.index(m); j=o.index(b\"chat105v3home2\")
k=o.rfind(b\"\n\",0,j)
tail=o[o.index(b\"\n// \", o.index(b\"[c102r6n] scrub attached\"))+1:] if False else None
sys.exit(0 if n[:i]==o[:i] and n.count(b\"[c102r6p] scrub attached\")==1 and b\"[c102r6n] scrub attached\" not in n else 1)" && node --check server.js && [ "$(tail -c 124771 server.js | md5sum)" = "$(tail -c 124771 /tmp/r2srv | md5sum)" ]'
# servers
CD=/tmp/r2cache; mkdir -p $CD
python3 - $CD <<'PY'
import hashlib, json, sys, os
d = sys.argv[1]
cases = {"/api/real-yield?case=blank": {"fetchedAt":"2026-11-16T19:35:55.434Z","available":True,"value":2.86,"prev":0,"change":2.86,"date":"2026-11-12","source":"US Treasury via FRED","series":"DFII10"},
         "/api/real-yield?case=equal": {"fetchedAt":"2026-11-27T20:00:00.537Z","available":True,"value":2.79,"prev":2.79,"change":0,"date":"2026-11-24","source":"US Treasury via FRED","series":"DFII10"},
         "/api/real-yield?case=normal": {"fetchedAt":"2026-11-13T02:31:02.151Z","available":True,"value":2.78,"prev":2.66,"change":0.12,"date":"2026-11-10","source":"US Treasury via FRED","series":"DFII10"},
         "/api/real-yield?case=negative": {"available":True,"value":-0.2,"prev":-0.25,"change":0.05,"date":"2021-06-01","source":"US Treasury via FRED","series":"DFII10"},
         "/api/c97/dgs10?case=zero": {"available":True,"value":4.9,"prev":0,"change":4.9,"date":"2026-11-12","source":"US Treasury via FRED","series":"DGS10"}}
for u, body in cases.items():
    k = os.path.join(d, hashlib.md5(u.encode()).hexdigest())
    open(k, "w").write(json.dumps(body, separators=(",", ":"))); open(k + ".h", "w").write(json.dumps({"s": 200, "h": {"content-type": "application/json; charset=utf-8"}}))
PY
kp 8871; kp 8860; kp 8861; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > /tmp/r2proxy.log 2>&1 &); sleep 0.7
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8860 node server.js > $O/rel.log 2>&1 &)
(UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html PORT=8861 node /tmp/r2srv > $O/old.log 2>&1 &); sleep 2.5
chk "release log: r6p scrub + 5 v3 attach lines, once each, no r6n" 'for t in "c102r6p\] scrub attached" "chat105v3home2\] preview attached" "chat108saferxA\] preview attached" "chat108saferxB\] preview attached" "chat108saferxC\] preview attached" "chat109v3default\] attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done; ! grep -q "c102r6n\] scrub attached" $O/rel.log && grep -q "c102r6n\] scrub attached" $O/old.log'
mkdir -p $O/cmp; cd $O/cmp
curl -s -D h.txt -o home.html http://localhost:8860/
chk "/ is still the v3 home with the step-1 headers" 'for i in v3home v8-hero v9-story v9-strip v9-charts v9-how v8-band; do grep -q "id=\"$i\"" home.html || exit 1; done; grep -qi "x-dispatch-home: v3" h.txt && ! grep -q "<meta name=\"robots\" content=\"noindex, nofollow\">" home.html'
chk "/ carries the r6p page fixes (r6o install-bar/UK-time + FRED label script) instead of r6n ids" 'grep -q "id=\"c102r6o-inst\"" home.html && grep -q "id=\"c102r6o-fred\"" home.html'
chk "/ keeps the full menu (same links as live) and one signup form" '[ "$(python3 -c "import re;t=open(\"home.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(sorted(re.findall(r\"href=\\\"([^\\\"]+)\\\"\",t[i:j])))")" = "$(python3 -c "import re;t=open(\"/workspace/c109/live_home.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(sorted(re.findall(r\"href=\\\"([^\\\"]+)\\\"\",t[i:j])))")" ] && [ "$(grep -o "action=\"/free-brief\"" home.html | wc -l)" = 1 ]'
j(){ curl -s "http://localhost:$1$2"; }
chk "/api/real-yield blank-day case: prev 0 -> null, change -> null (r6n kept prev 0)" '[ "$(j 8860 "/api/real-yield?case=blank" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"],d[\"value\"],d[\"date\"])")" = "None None 2.86 2026-11-12" ] && [ "$(j 8861 "/api/real-yield?case=blank" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"])")" = "0" ]'
chk "/api/real-yield genuine equal days (23-24 Nov 2.79) unchanged" '[ "$(j 8860 "/api/real-yield?case=equal" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "2.79 0" ]'
chk "/api/real-yield normal and negative real yields unchanged" '[ "$(j 8860 "/api/real-yield?case=normal" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "2.66 0.12" ] && [ "$(j 8860 "/api/real-yield?case=negative" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"],d[\"change\"])")" = "-0.25 0.05" ]'
chk "fix is scoped to /api/real-yield (dgs10 untouched)" '[ "$(j 8860 "/api/c97/dgs10?case=zero" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d[\"prev\"])")" = "0" ]'
for p in "/?preview=off" "/?settings=1" "/?checkout=1" /brief/ /gold/ /pricing /__auth/login /terminal/ /markets/ /calendar/ /methodology /lab/ /api/me /api/c100/macro /styles.css /app.js; do n=$(echo "$p" | tr '/?=.' '____'); curl -s -o r$n -w "%{http_code}\n" "http://localhost:8860$p" >> codes.r; curl -s -o o$n -w "%{http_code}\n" "http://localhost:8861$p" >> codes.o; done
chk "16 other routes: same status codes, HTML complete" 'cmp -s codes.r codes.o && for f in r__preview_off r__settings_1 r_brief_ r_gold_ r_pricing r___auth_login r_terminal_ r_calendar_; do tail -c 300 $f | tr -d "\n " | grep -q "</html>$" || exit 1; done'
chk "auth page: r6p strips every script (CSP script-src none), r6n left four in" '[ "$(grep -c "<script" r___auth_login)" = 0 ] && [ "$(grep -o "<script" o___auth_login | wc -l)" -ge 1 ]'
chk "static assets and JSON without quotes byte-identical (styles.css, app.js, /api/me)" 'cmp -s r_styles_css o_styles_css && cmp -s r_app_js o_app_js && cmp -s r_api_me o_api_me'
python3 - > links.txt <<'PY'
import re;t=open("/workspace/c109/live_home.html").read();i=t.index('<details class="menu">');j=t.index("</details>",i)
print("\n".join(sorted(set(h for h in re.findall(r'href="([^"]+)"',t[i:j]) if h.startswith("/") and h!="/"))))
PY
bad=0; while read l; do a=$(curl -s -o /tmp/r2a -w '%{http_code}' "http://localhost:8860$l"); b=$(curl -s -o /tmp/r2b -w '%{http_code}' "http://localhost:8861$l"); [ "$a" = "$b" ] || { echo "  code differs: $l $a $b"; bad=1; }; ct=$(file -b --mime-type /tmp/r2a); if [ "$ct" = text/html ]; then tail -c 300 /tmp/r2a | tr -d '\n ' | grep -q '</html>$' || { echo "  incomplete: $l"; bad=1; }; fi; done < links.txt
chk "all $(wc -l < links.txt) menu-link routes: same status as before, complete HTML" '[ $bad = 0 ]'
cd $F; kp 8860; kp 8861
python3 $S/restore_release.py $S > $O/rs.out 2>&1; chk "restore puts server.js back exactly (every file md5)" 'grep -q "\[restore\] DONE" $O/rs.out && snapall | cmp -s - /tmp/r2_pre.md5'
D --dry-run > $O/d2.out 2>&1; chk "after restore the installer accepts the tree again" 'grep -q "DRY RUN complete" $O/d2.out'
echo "RESULT pass=$PASS fail=$FAIL"; [ $FAIL = 0 ]
