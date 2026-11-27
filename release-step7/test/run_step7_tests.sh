#!/usr/bin/env bash
# LOCAL tests for release-step7 (box only). Fixture = live step-6 stand-in: step-3 fixture + the real step-4, 4b and 6 installers,
# with a TEST-ONLY auth harness in the prefix (verbatim lineage auth + Resend-wiring code over PGlite / Postgres 17) and a mocked
# @replit/connectors-sdk (records calls; no network).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H"); C112=/workspace/c112; S4=$C112/release-step4; S4B=$C112/release-step4b; S6=/workspace/c113/release-step6
F=/tmp/r7fix; O=${OUT:-/workspace/qa-dispatch/release-step7/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O; mkdir -p $O; A=$O/auth; mkdir -p $A
mkdir -p /tmp/node_modules/@replit/connectors-sdk; cp $H/mock/connectors-sdk.js /tmp/node_modules/@replit/connectors-sdk/index.js
read SM SS RM < <(bash "$S4/test/make_fixture.sh" $F | tail -1); cd $F
R4_LOCAL_PAYLOAD="$S4" R4_LOCAL_TEST=1 R4_TEST_SERVER_SIZE="$SS" R4_TEST_R6N_MD5="$RM" bash "$S4/deploy.sh" --dir $F > $O/s4.out 2>&1
X=$(md5sum < server.js | cut -c1-32); Y=$(wc -c < server.js)
R4B_LOCAL_PAYLOAD="$S4B" R4B_LOCAL_TEST=1 R4B_TEST_SERVER_MD5=$X R4B_TEST_SERVER_SIZE=$Y bash "$S4B/deploy.sh" --dir $F > $O/s4b.out 2>&1
python3 $H/make_auth_prefix.py $O/auth_prefix.js
python3 - $O/auth_prefix.js <<'PY'
import sys
s = open("server.js").read(); a = open(sys.argv[1]).read()
i = s.index("\n") + 1; s = s[:i] + a + s[i:]
hook = '    const path = req.url.split("?")[0];\n'; assert s.count(hook) == 1
s = s.replace(hook, hook + '    if (authHarness(req, res)) return;\n'); open("server.js", "w").write(s)
PY
X=$(md5sum < server.js | cut -c1-32); Y=$(wc -c < server.js)
R6_LOCAL_PAYLOAD="$S6" R6_LOCAL_TEST=1 R6_TEST_SERVER_MD5=$X R6_TEST_SERVER_SIZE=$Y bash "$S6/deploy.sh" --dir $F > $O/s6.out 2>&1
chk "fixture: real step-4, 4b and step-6 installers applied (on the harness prefix)" 'grep -q "DONE: server.js md5" $O/s4.out && grep -q "DONE: server.js md5" $O/s4b.out && grep -q "DONE: server.js md5" $O/s6.out'
node --check server.js && rm -rf .release-snapshots && git add -A >/dev/null 2>&1 && git commit -qm "live step 6 stand-in" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r7old; mkdir -p /tmp/r7old; cp server.js app.js index.html styles.css c93.css /tmp/r7old/
B6MD5=$(md5sum < server.js | cut -c1-32); B6SZ=$(wc -c < server.js)
export R7_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R7_LOCAL_TEST=1 R7_TEST_SERVER_MD5=$B6MD5 R7_TEST_SERVER_SIZE=$B6SZ D "$@"; }
TO(){ R7_LOCAL_TEST=1 R7_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R7_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5
D --measure > $O/g0.out 2>&1; chk "refuses without the live step-6 server.js (real pins 343f7f30, 2,521,438 B)" 'grep -q "not the live step-6" $O/g0.out'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R7_LOCAL_TEST=1 R7_TEST_SERVER_MD5=0000 R7_TEST_SERVER_SIZE=$B6SZ D --dry-run > $O/g1.out 2>&1; chk "refuses a wrong server.js md5" 'grep -q "is not the live step-6" $O/g1.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done'
sed -i 's/INTERVAL .10 minutes.`;$/INTERVAL '"'"'11 minutes'"'"'`;/' server.js; cmp -s server.js /tmp/r7old/server.js && echo "WARN sed no-op"
TO --dry-run > $O/g2.out 2>&1; cp /tmp/r7old/server.js server.js
chk "refuses when the step-6 chat111verify block differs" 'grep -q "does not end with the exact live chat110navyb + chat111verify" $O/g2.out'
sed -i 's#const { ReplitConnectors } = require("@replit/connectors-sdk");#const { ReplitConnectors: RC } = require("@replit/connectors-sdk");#' server.js
TO --dry-run > $O/g3.out 2>&1; cp /tmp/r7old/server.js server.js
chk "refuses when the Resend connector wiring is not exactly as expected" 'grep -q "prefix anchor .*ReplitConnectors.* occurs 0 times" $O/g3.out'
sed -i 's#connectors.proxy("resend", "/emails", {#connectors.proxy("resend2", "/emails", {#' server.js
TO --dry-run > $O/g3b.out 2>&1; cp /tmp/r7old/server.js server.js
chk "refuses when there is no Resend /emails call to reuse" 'grep -q "prefix anchor .*resend.*/emails.* occurs 0 times" $O/g3b.out'
sed -i '2i // issueEmailVerification already here' server.js
TO --dry-run > $O/g4.out 2>&1; cp /tmp/r7old/server.js server.js
chk "refuses when verification code already exists in the prefix" "grep -q \"prefix anchor b'issueEmailVerification' occurs 1 times\" \$O/g4.out"
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; sed -i 's/var VERIFY_ENFORCE = false;/var VERIFY_ENFORCE = true; /' bad/server_block_chat112verifymail.js
R7_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5.out 2>&1; rm -rf bad; chk "tampered payload (VERIFY_ENFORCE=true) refused by sha256" 'grep -q "sha256 mismatch" $O/g5.out'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step7-* | head -1)
chk "snapshot step7-<TS>: server.js (= step 6) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r7old/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step7-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); app/index/styles/c93 byte-identical; node --check" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r7old/$f || exit 1; done && node --check server.js'
N6=$(( B6SZ - $(wc -c < $DEP/server_block_chat111verify.js) ))
chk "server.js = step-6 server.js with only its last block (chat111verify) replaced by chat112verifymail" 'cat <(head -c $N6 /tmp/r7old/server.js) $DEP/server_block_chat112verifymail.js | cmp -s - server.js && tail -c $(wc -c < $DEP/server_block_chat111verify.js) /tmp/r7old/server.js | cmp -s - $DEP/server_block_chat111verify.js'
python3 $SN/restore_release.py $SN > $O/r.out 2>&1; chk "restore puts step 6 back byte-exact" 'cmp -s server.js /tmp/r7old/server.js'
echo x >> server.js; python3 $SN/restore_release.py $SN > $O/r2.out 2>&1; chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r7old/server.js server.js; sleep 1; T > $O/a2.out 2>&1; chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step7-* | wc -l) = 2 ]'
# ---- servers: new (step 7) and old (step 6), each with its own PGlite DB, mocked Resend, outbound connection log ----
CD=/tmp/r2cache; for p in 8871 8862 8863 8864 8892 8893; do kp $p; done; (CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > $O/proxy.log 2>&1 &); sleep 0.7
ENVP="DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS=1500 UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html"
echo ok > $O/mode.new; echo ok > $O/mode.old; : > $O/mail.new; : > $O/mail.old
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.new NETLOG=$O/net.new NODE_OPTIONS="--require $H/netlog.js" PORT=8862 node server.js > $O/rel.log 2>&1 &)
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.old MOCK_RESEND_LOG=$O/mail.old NETLOG=$O/net.old NODE_OPTIONS="--require $H/netlog.js" PORT=8863 node /tmp/r7old/server.js > $O/old.log 2>&1 &); sleep 4
(UPSTREAM_PORT=8862 STATIC_DIR=/tmp/r7old EDITS=$S4/index_edits.json PORT=8892 node $S4/test/navyfront.js > $O/front.log 2>&1 &)
(UPSTREAM_PORT=8863 STATIC_DIR=/tmp/r7old EDITS=$S4/index_edits.json PORT=8893 node $S4/test/navyfront.js > $O/oldfront.log 2>&1 &); sleep 1
chk "log: chat112verifymail attaches once with emails on; navy/credits/r6p once; no chat111verify left" '[ "$(grep -c "\[chat112verifymail\] attached (enforcement off; verification emails on)" $O/rel.log)" = 1 ] && for t in "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done && ! grep -q chat111verify $O/rel.log'
post(){ curl -s -o $A/$1.body -D $A/$1.hdr -c $A/$1.jar -w "%{time_total}" -X POST --data "$3" "http://localhost:$2$4" > $A/$1.time; }
me(){ curl -s -b $A/$1.jar "http://localhost:$2/api/me"; }
db(){ curl -s "http://localhost:$1/__testdb/$2"; }
mails(){ grep -c . $O/mail.$1; }
for side in new:8862 old:8863; do n=${side%%:*}; p=${side##*:}
  post reg_$n $p 'name=&email=new1@example.com&password=newpassword1' /__auth/register; me reg_$n $p > $A/me_reg_$n.json
  post login_new_$n $p 'email=new1@example.com&password=newpassword1' /__auth/login; me login_new_$n $p > $A/me_login_new_$n.json
  post login_old_$n $p 'email=old@example.com&password=oldpassword1' /__auth/login; me login_old_$n $p > $A/me_login_old_$n.json
  post badpw_$n $p 'email=old@example.com&password=wrongpassword' /__auth/login
  post dup_$n $p 'email=new1@example.com&password=newpassword1' /__auth/register
  post sub_$n $p 'email=new2@example.com&password=newpassword2' /__auth/subscribe; me sub_$n $p > $A/me_sub_$n.json
  post subold_$n $p 'email=old@example.com&password=oldpassword1' /__auth/subscribe
done
sleep 1.5; db 8862 users > $A/db_new.json; db 8863 users > $A/db_old.json
python3 - $A > $A/summary.txt <<'PY'
import json, sys, re
A = sys.argv[1]
def st(k):
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
python3 - $O/mail.new > $A/mail_check.txt <<'PY'
import json, sys, re
L = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print("count", len(L)); ok = True
for x in L:
    b = x["opts"]["body"]; t = b["text"]
    m = re.search(r"https://thedispatch\.uk/__auth/verify\?token=([0-9a-f]{64})\n", t)
    bad = [w for w in ("invest", "buy ", "sell", "price", "gold", "return", "profit", "advice", "tip") if w in t.lower()]
    good = x["name"] == "resend" and x["path"] == "/emails" and x["opts"]["method"] == "POST" and b["from"] == "The Dispatch <accounts@thedispatch.uk>" and b["subject"] == "Confirm your email for The Dispatch" and len(b["to"]) == 1 and m and not bad and set(b) == {"from", "to", "subject", "text"}
    print(b["to"][0], "ok" if good else "BAD", "words=%s" % bad); ok = ok and bool(good)
print("ALLOK" if ok else "NOTOK")
print("TEXT-SAMPLE:\n" + (L[0]["opts"]["body"]["text"] if L else ""))
PY
cat $A/mail_check.txt
chk "sign-up responses identical to step 6 (register, sign-in new+existing, bad password, duplicate, Premium sign-up, existing-user subscribe)" '[ "$(grep -c "same_status_location_cookies=True same_body=True" $A/summary.txt)" = 7 ] && [ "$(grep -c "^me_.* same=True" $A/summary.txt)" = 4 ]'
chk "new user signed in right after sign-up and can sign in again (unverified is never blocked)" 'grep -q "^me_reg       same=True new={.guest.: False, .email.: .new1@example.com." $A/summary.txt && grep -q "^me_login_new same=True new={.guest.: False, .email.: .new1@example.com." $A/summary.txt'
chk "exactly ONE email per new sign-up (new1 register, new2 Premium) and none for sign-in, duplicate, existing-user subscribe; step 6 sends none" '[ "$(mails new)" = 2 ] && [ "$(mails old)" = 0 ] && grep -q "^new1@example.com ok" $A/mail_check.txt && grep -q "^new2@example.com ok" $A/mail_check.txt'
chk "email: Resend connector POST /emails, from The Dispatch <accounts@thedispatch.uk>, 1 recipient, plain text, link https://thedispatch.uk/__auth/verify?token=<64 hex>, no investment wording" 'grep -q "^ALLOK$" $A/mail_check.txt'
chk "DB: new sign-ups unverified, existing stays verified; dispatch_email_verifications has one row per new user" "grep -q \"^db_new {'old@example.com': True, 'new1@example.com': False, 'new2@example.com': False}\" \$A/summary.txt && [ \"\$(db 8862 verifications | python3 -c 'import json,sys; print(sorted(r[\"email\"] for r in json.load(sys.stdin)))')\" = \"['new1@example.com', 'new2@example.com']\" ]"
# ---- failure modes: provider rejection, transport error, timeout ----
for mode in fail throw hang; do echo $mode > $O/mode.new; post f_$mode 8862 "email=f_$mode@example.com&password=newpassword1" /__auth/register; me f_$mode 8862 > $A/me_f_$mode.json; done
sleep 2.5; echo ok > $O/mode.new
chk "Resend failure/transport error/timeout: sign-up still 302 + signed in, answered in < 0.5 s (timeout case too)" 'for m in fail throw hang; do grep -q "^HTTP/1.1 302" $A/f_$m.hdr && grep -q "\"email\":\"f_$m@example.com\"" $A/me_f_$m.json && python3 -c "import sys; sys.exit(0 if float(open(\"$A/f_$m.time\").read()) < 0.5 else 1)" || exit 1; done'
chk "one log line per failure: provider status 422, transport_error, timeout" '[ "$(grep -c "verification email not sent (sign-up): provider status 422" $O/rel.log)" = 1 ] && [ "$(grep -c "verification email not sent (sign-up): transport_error" $O/rel.log)" = 1 ] && [ "$(grep -c "verification email not sent (sign-up): timeout" $O/rel.log)" = 1 ] && ! grep -q "@example.com" $O/rel.log'
# ---- verify link ----
TOK1=$(python3 -c "import json,re; L=[json.loads(l) for l in open('$O/mail.new')]; print([re.search(r'token=([0-9a-f]{64})', x['opts']['body']['text']).group(1) for x in L if x['opts']['body']['to'][0]=='new1@example.com'][0])")
TOK2=$(python3 -c "import json,re; L=[json.loads(l) for l in open('$O/mail.new')]; print([re.search(r'token=([0-9a-f]{64})', x['opts']['body']['text']).group(1) for x in L if x['opts']['body']['to'][0]=='new2@example.com'][0])")
curl -s -I "localhost:8862/__auth/verify?token=$TOK1" > $A/v_head.txt
curl -s -D $A/v1.hdr -o $A/v1.html "localhost:8862/__auth/verify?token=$TOK1"; curl -s -o $A/v1b.html "localhost:8862/__auth/verify?token=$TOK1"
db 8862 "expire?email=new2@example.com" > /dev/null; curl -s -o $A/v2.html "localhost:8862/__auth/verify?token=$TOK2"; curl -s -o $A/v3.html "localhost:8862/__auth/verify?token=nothex"; curl -s -o $A/v4.html "localhost:8862/__auth/verify"
db 8862 users > $A/db_after_verify.json
chk "HEAD on the link (scanners) does not use it up" 'grep -q "^HTTP/1.1 200" $A/v_head.txt && grep -q "Email confirmed" $A/v1.html'
chk "verify link works once: 200 on-brand 'Email confirmed' page (no-store, no-referrer), new1 now verified" 'grep -q "^HTTP/1.1 200" $A/v1.hdr && grep -qi "^cache-control: no-store" $A/v1.hdr && grep -qi "^referrer-policy: no-referrer" $A/v1.hdr && grep -q "<h1>Email confirmed</h1>" $A/v1.html && grep -q "Not investment advice" $A/v1.html && python3 -c "import json,sys; d={r[\"email\"]:r[\"email_verified\"] for r in json.load(open(\"$A/db_after_verify.json\"))}; sys.exit(0 if d[\"new1@example.com\"] is True else 1)"'
chk "reused, expired, malformed and missing tokens get the friendly page; expired leaves new2 unverified" 'for f in v1b v2 v3 v4; do grep -q "This link has expired or was already used" $A/$f.html || exit 1; done && python3 -c "import json,sys; d={r[\"email\"]:r[\"email_verified\"] for r in json.load(open(\"$A/db_after_verify.json\"))}; sys.exit(0 if d[\"new2@example.com\"] is False else 1)"'
# ---- resend + rate limits ----
rs(){ curl -s -o $A/rs_$1.json -w "%{http_code}" -b $A/$2.jar -X POST ${3:-} localhost:8862/__auth/verify/resend; }
M0=$(mails new); c1=$(rs a f_fail); c2=$(curl -s -o $A/rs_guest.json -w "%{http_code}" -X POST localhost:8862/__auth/verify/resend); c3=$(rs v login_old_new); c4=$(rs x f_fail "-H Origin:https://evil.example")
codes=""; for i in 1 2 3 4 5; do db 8862 "age?email=f_fail@example.com&min=6" > /dev/null; codes="$codes $(rs r$i f_fail)"; done; c6=$(rs again f_fail)
echo "first=$c1 guest=$c2 verified=$c3 crosssite=$c4 aged:$codes again=$c6 mails_added=$(( $(mails new) - M0 ))" > $A/resend.txt; cat $A/resend.txt
chk "resend: right after sign-up 429 rate_limited; guest 401; verified user 'verified' (no send); cross-site 403" '[ "$c1" = 429 ] && grep -q "\"rate_limited\"" $A/rs_a.json && [ "$c2" = 401 ] && [ "$c3" = 200 ] && grep -q "\"verified\"" $A/rs_v.json && [ "$c4" = 403 ]'
chk "resend: 1 per 5 min and 5 per 24 h (incl. the sign-up attempt, which failed at the provider): after 6-min steps 4 sends go out, the 5th and an immediate retry are 429" '[ "$codes" = " 200 200 200 200 429" ] && [ "$c6" = 429 ] && [ $(( $(mails new) - M0 )) = 4 ] && grep -q "\"sent\"" $A/rs_r1.json'
# ---- status + banner markup ----
curl -s -b $A/f_fail.jar localhost:8862/__auth/verify/status > $A/st_unv.json; curl -s -b $A/login_old_new.jar localhost:8862/__auth/verify/status > $A/st_ver.json; curl -s localhost:8862/__auth/verify/status > $A/st_guest.json
chk "status: unverified {show:true}; verified and guest {show:false}" 'grep -q "{\"show\":true}" $A/st_unv.json && grep -q "{\"show\":false}" $A/st_ver.json && grep -q "{\"show\":false}" $A/st_guest.json'
curl -s -b $A/f_fail.jar -D $A/gold_unv.hdr -o $A/gold_unv.html localhost:8862/gold/; curl -s -o $A/gold_guest_new.html localhost:8862/gold/; curl -s -o $A/gold_guest_old.html localhost:8863/gold/
chk "signed-in page gets exactly one reminder script tag (private, no-store); guest page byte-identical to step 6 with no tag" '[ "$(grep -o "/__auth/verify/reminder.js?v=c112" $A/gold_unv.html | wc -l)" = 1 ] && grep -qi "^cache-control: private, no-store" $A/gold_unv.hdr && cmp -s $A/gold_guest_new.html $A/gold_guest_old.html && ! grep -q reminder.js $A/gold_guest_new.html'
chk "reminder.js served as JS" '[ "$(curl -s -o /dev/null -w "%{http_code} %{content_type}" localhost:8862/__auth/verify/reminder.js?v=c112)" = "200 application/javascript; charset=utf-8" ]'
# ---- missing table / column: still never breaks sign-up ----
kp 8864; (env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" TEST_NO_VTABLE=1 MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.nt PORT=8864 node $F/server.js > $O/novt.log 2>&1 &); sleep 4
post nt 8864 "email=nt@example.com&password=newpassword1" /__auth/register; me nt 8864 > $A/me_nt.json; sleep 1; kp 8864
chk "DB without dispatch_email_verifications: sign-up 302 + signed in, one log line, no email" 'grep -q "^HTTP/1.1 302" $A/nt.hdr && grep -q "nt@example.com" $A/me_nt.json && [ "$(grep -c "verification step skipped after sign-up" $O/novt.log)" = 1 ] && [ ! -s $O/mail.nt ]'
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.off PORT=8864 node $F/server.js > $O/off.log 2>&1 &); sleep 4
post off 8864 "email=off@example.com&password=newpassword1" /__auth/register; sleep 1; kp 8864
chk "delivery not configured (e.g. dev, no from-address): attaches with emails off, sign-up fine, nothing sent" 'grep -q "verification emails off: delivery not configured" $O/off.log && grep -q "^HTTP/1.1 302" $A/off.hdr && [ ! -s $O/mail.off ]'
# ---- network, guest views, routes ----
chk "outbound connections: none except the local test upstream (Resend is mocked in-process; no real network)" '[ -s $O/net.new ] && [ -z "$(grep -v "^localhost:8871$\|^127.0.0.1:8871$" $O/net.new)" ]'
j(){ curl -s "http://localhost:$1$2"; }
chk "guest /api/me byte-identical to step 6 and the live capture" '[ "$(j 8862 /api/me | md5sum)" = "$(j 8863 /api/me | md5sum)" ] && [ "$(j 8862 /api/me | md5sum)" = "$(curl -s localhost:8871/api/me | md5sum)" ]'
chk "/__auth/login and /__auth/register byte-identical; /signin same" 'for u in /__auth/login /__auth/register; do [ "$(j 8862 $u | md5sum)" = "$(j 8863 $u | md5sum)" ] || exit 1; done && [ "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8862/signin)" = "$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" localhost:8863/signin)" ]'
mkdir -p $O/cmp; cd $O/cmp; n=0; bad=""
while read r; do k=$(echo "$r" | tr '/?=.' '____'); curl -s -o n$k "http://localhost:8862$r"; curl -s -o o$k "http://localhost:8863$r"
  cmp -s n$k o$k || bad="$bad $r"; n=$((n+1)); done < /tmp/routes.txt
echo "$bad" > $O/route_diffs.txt; cd $F
chk "all 57 routes byte-identical to step 6 (guest)" '[ -z "$(tr -d " " < $O/route_diffs.txt)" ] && [ $n = 57 ]'
# ---- browser ----
post shots 8862 "email=shots@example.com&password=newpassword1" /__auth/register
post bn 8862 "email=banner@example.com&password=newpassword1" /__auth/register
post vo 8863 'email=old@example.com&password=oldpassword1' /__auth/login
tk(){ grep dispatch_session $A/$1.jar | awk '{print $7}' | tail -1; }
echo "{\"unverified_new\":\"$(tk bn)\",\"verified_new\":\"$(tk login_old_new)\",\"verified_old\":\"$(tk vo)\"}" > $O/cookies.json
python3 $H/shots7.py http://localhost:8892 http://localhost:8893 http://localhost:8862 $O/shots $O/cookies.json > $O/shots.txt 2>&1; tail -9 $O/shots.txt
chk "browser 320/390/1280 dark+light: /signin pixel-identical; verify pages render, no overflow; banner fully visible for the unverified user only; verified + guest /gold/ pixel-identical to step 6" 'grep -q "^RESULT worst_identical_diff=0.00000 issues=none" $O/shots.txt'
chk "banner: Resend click reports the limit right after sign-up; dismiss hides it and it stays hidden after reload" 'grep -q "resend_click_text: Link already sent" $O/shots.txt && grep -q "dismiss: {.gone_on_click.: True, .gone_after_reload.: True}" $O/shots.txt'
echo "RESULT pass=$PASS fail=$FAIL"; echo "servers left running: 8892 (step7+front) 8893 (step6+front)"; [ $FAIL = 0 ]
