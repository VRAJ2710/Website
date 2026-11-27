#!/usr/bin/env bash
# LOCAL tests for release-step1 (box only): git fixture of the workspace, r6n stand-in server = stub + r6p scrub serving the
# captured LIVE r6n home; other GETs come from the live site through a caching proxy (same bytes for both servers).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); F=/tmp/r1fix; PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ P=$(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); [ -n "$P" ] && kill $P; true; }
R6=$(bash "$H/make_fixture.sh" $F | tail -1); O=/tmp/r1out; rm -rf $O; mkdir -p $O; cd $F
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
snapall > /tmp/r1_pre.md5
export R1_LOCAL_PAYLOAD="$DEP" R1_LOCAL_TEST=1 R1_TEST_SERVER_MD5="$R6"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
D --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - /tmp/r1_pre.md5'
chk "measure finds the r6n commit and the deltas" 'grep -q "r6n commit:" $O/m.out && grep -q "aside migrations/0001.sql" $O/m.out && grep -q "back attached_assets/brief.pdf" $O/m.out && grep -q "r6n  styles.css" $O/m.out'
D --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - /tmp/r1_pre.md5'
R1_TEST_SERVER_MD5=0000 D --dry-run > $O/g1.out 2>&1; chk "refuses when the r6n server backup is not the pin" 'grep -q "is not the r6n pin" $O/g1.out'
cp app.js.20261111-070219.bak-chat102r6o /tmp/appbak; echo x >> app.js.20261111-070219.bak-chat102r6o; D --dry-run > $O/g2.out 2>&1; cp /tmp/appbak app.js.20261111-070219.bak-chat102r6o
chk "refuses when the app.js backup is not the live app.js" 'grep -q "app.js.20261111-070219.bak-chat102r6o md5" $O/g2.out && snapall | cmp -s - /tmp/r1_pre.md5'
mv .git /tmp/r1git; D --dry-run > $O/g3.out 2>&1; mv /tmp/r1git .git; chk "refuses without git history" 'grep -q "git is not usable" $O/g3.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo "//x" >> bad/server_block_chat109v3default.js
R1_LOCAL_PAYLOAD=$F/bad D --dry-run > $O/g4.out 2>&1; rm -rf bad; chk "tampered payload refused (sha256)" 'grep -q "sha256 mismatch" $O/g4.out'
snapall > /tmp/r1_pre.md5
D > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: the tree now equals r6n" $O/a.out'
S=$(ls -d $F/.release-snapshots/step1-* | head -1)
chk "snapshot has every touched file + manifest + restore script" '[ -f $S/manifest.json ] && [ -f $S/restore_release.py ] && [ -f $S/files/server.js ] && [ -f $S/files/migrations/0001.sql ] && [ -f $S/files/scripts/compare-redesign-tests.py ]'
chk "release app.js, styles.css, c93.css = live files" '[ "$(md5sum < app.js | cut -c1-32)" = bd13a193f2a16ef7d7a4508c25231bb9 ] && [ "$(md5sum < styles.css | cut -c1-32)" = 8023e711df4aaadbab1e1b4264bfd8c5 ] && [ "$(md5sum < c93.css | cut -c1-32)" = 9d6a86a64135b1cc58e6af7b12973550 ]'
chk "release server.js = r6n bytes + v3 blocks, node --check" 'cmp -n $(wc -c < server.js.20261111-070219.bak-chat102r6o) server.js server.js.20261111-070219.bak-chat102r6o && node --check server.js && [ "$(grep -c "var TAG = \"chat109v3default\";" server.js)" = 1 ]'
chk "dev-only files moved aside, deleted file restored" '[ ! -e migrations/0001.sql ] && [ ! -e recoverySenderCheck.js ] && [ ! -e scripts/compare-redesign-tests.py ] && [ -f attached_assets/brief.pdf ] && grep -q "run = \"node server.js\"" .replit && ! grep -q RESEND .replit'
# servers
kp 8870; kp 8860; kp 8861; (PORT=8870 node "$H/cacheproxy.js" > /tmp/r1proxy.log 2>&1 &); sleep 0.7
(UPSTREAM_HTTP=localhost:8870 RAW_HTML=/workspace/c109/live_home.html PORT=8860 node server.js > $O/rel.log 2>&1 &)
(UPSTREAM_HTTP=localhost:8870 RAW_HTML=/workspace/c109/live_home.html PORT=8861 node server.js.20261111-070219.bak-chat102r6o > $O/r6n.log 2>&1 &); sleep 2
chk "release log: r6n scrub + 5 v3 attach lines, once each" 'for t in "c102r6p\] scrub attached" "chat105v3home2\] preview attached" "chat108saferxA\] preview attached" "chat108saferxB\] preview attached" "chat108saferxC\] preview attached" "chat109v3default\] attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done'
mkdir -p $O/cmp; cd $O/cmp
curl -s -D h.txt -o home.html http://localhost:8860/; curl -s -o utm.html "http://localhost:8860/?utm_source=x"
chk "/ is the v3 home (hero, story, strip, charts, 1-2-3, band)" 'for i in v3home v8-hero v9-story v9-strip v9-charts v9-how v8-band; do grep -q "id=\"$i\"" home.html || exit 1; done'
chk "/ has no preview ribbon, no preview noindex, no preview headers" '! grep -qi "preview only" home.html && ! grep -q "v3-rib" home.html && ! grep -q "<meta name=\"robots\" content=\"noindex, nofollow\">" home.html && ! grep -qi "x-robots-tag" h.txt && grep -qi "x-dispatch-home: v3" h.txt && ! grep -qi "x-dispatch-preview" h.txt'
chk "/ keeps the full menu (same links as live) and one signup form" '[ "$(python3 -c "import re;t=open(\"home.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(sorted(re.findall(r\"href=\\\"([^\\\"]+)\\\"\",t[i:j])))")" = "$(python3 -c "import re;t=open(\"/workspace/c109/live_home.html\").read();i=t.index(\"<details class=\\\"menu\\\">\");j=t.index(\"</details>\",i);print(sorted(re.findall(r\"href=\\\"([^\\\"]+)\\\"\",t[i:j])))")" ] && [ "$(grep -o "action=\"/free-brief\"" home.html | wc -l)" = 1 ]'
chk "/?utm_source=x is also v3" 'grep -q "id=\"v9-story\"" utm.html'
for p in "/?preview=off" "/?settings=1" "/?checkout=1" /brief/ /gold/ /pricing /__auth/login /__auth/register /terminal/ /markets/ /methodology /lab/ /api/me /api/c100/macro /styles.css /app.js; do n=$(echo "$p" | tr '/?=.' '____'); curl -s -o r$n "http://localhost:8860$p"; curl -s -o o$n "http://localhost:8861$p"; done
chk "other routes byte-identical to r6n (incl. /?preview=off, /?settings=1, /?checkout=1)" 'for f in o*; do cmp -s "$f" "r${f#o}" || { echo "  differs: $f"; exit 1; }; done'
curl -s -o rck -H "Cookie: td_v3p=1" "http://localhost:8860/?settings=1"; chk "a leftover td_v3p cookie does not change /?settings=1" 'cmp -s rck o__settings_1'
python3 - > links.txt <<'PY'
import re;t=open("/workspace/c109/live_home.html").read();i=t.index('<details class="menu">');j=t.index("</details>",i)
print("\n".join(sorted(set(h for h in re.findall(r'href="([^"]+)"',t[i:j]) if h.startswith("/") and h!="/"))))
PY
bad=0; while read l; do a=$(curl -s -o /tmp/r1a -w '%{http_code}' "http://localhost:8860$l"); b=$(curl -s -o /tmp/r1b -w '%{http_code}' "http://localhost:8861$l"); cmp -s /tmp/r1a /tmp/r1b || { echo "  menu link differs: $l"; bad=1; }; [ "$a" = "$b" ] || bad=1; done < links.txt
chk "all $(wc -l < links.txt) menu-link routes byte-identical to r6n" '[ $bad = 0 ]'
curl -s -o post.r -X POST http://localhost:8860/; curl -s -o post.o -X POST http://localhost:8861/; chk "POST / unchanged" 'cmp -s post.r post.o'
cd $F; kp 8860; kp 8861
python3 $S/restore_release.py $S > $O/rs.out 2>&1; chk "restore puts dev back exactly (every file md5)" 'grep -q "\[restore\] DONE" $O/rs.out && snapall | cmp -s - /tmp/r1_pre.md5'
echo "RESULT pass=$PASS fail=$FAIL"; [ $FAIL = 0 ]
