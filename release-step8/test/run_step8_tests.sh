#!/usr/bin/env bash
# LOCAL tests for release-step8 (box only). Fixture = live step-7 stand-in: step-3 fixture + the real
# step-4, 4b, 6 and 7 installers, with a TEST-ONLY auth harness in the prefix (verbatim lineage auth
# over PGlite / Postgres 17) and a mocked @replit/connectors-sdk (no network).
set -u
H=$(cd "$(dirname "$0")" && pwd); DEP=$(dirname "$H")
C112=/workspace/c112; S4=$C112/release-step4; S4B=$C112/release-step4b
S6=/workspace/c113/release-step6; S7=/workspace/c113/release-step7
F=/tmp/r8fix; O=${OUT:-/workspace/qa-dispatch/release-step8/tests}; PASS=0; FAIL=0
chk(){ if (eval "$2"); then echo "PASS $1"; PASS=$((PASS+1)); else echo "FAIL $1"; FAIL=$((FAIL+1)); fi; }
kp(){ for P in $(ss -ltnp | grep ":$1 " | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill $P; done; true; }
rm -rf $O; mkdir -p $O; A=$O/auth; mkdir -p $A

echo "---- standalone header proof ----"
node $H/cookie_headers.js > $O/cookie_headers.out 2>&1
chk "Node raw headers: register flat, Premium bug comma-joins, flatten fix is 4 separate cookies" 'grep -q "ALLOK cookie_headers.js" $O/cookie_headers.out'
cat $O/cookie_headers.out

echo "---- Chrome jar under production flags ----"
openssl req -x509 -newkey rsa:2048 -keyout $O/k.pem -out $O/c.pem -days 2 -nodes -subj "/CN=thedispatch.uk" >/dev/null 2>&1
for p in 18444; do kp $p; done
CK_KEY=$O/k.pem CK_CERT=$O/c.pem CK_PORT=18444 node $H/prod_flags_server.js > $O/prod_flags.log 2>&1 &
sleep 0.3
CK_PORT=18444 python3 $H/chrome_cookies.py > $O/chrome.out 2>&1
chk "Chrome: free register signed in; Premium bug stores an empty session; flatten fix stores the token + account_created" 'grep -q "ALLOK chrome_cookies.py" $O/chrome.out'
cat $O/chrome.out
kp 18444

echo "---- fixture: real steps 4, 4b, 6, 7 + auth harness ----"
mkdir -p /tmp/node_modules/@replit/connectors-sdk
cp $H/mock/connectors-sdk.js /tmp/node_modules/@replit/connectors-sdk/index.js
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
X=$(md5sum < server.js | cut -c1-32); Y=$(wc -c < server.js)
R7_LOCAL_PAYLOAD="$S7" R7_LOCAL_TEST=1 R7_TEST_SERVER_MD5=$X R7_TEST_SERVER_SIZE=$Y bash "$S7/deploy.sh" --dir $F > $O/s7.out 2>&1
chk "fixture: real step-4, 4b, 6 and 7 installers applied (on the harness prefix)" 'grep -q "DONE: server.js md5" $O/s4.out && grep -q "DONE: server.js md5" $O/s4b.out && grep -q "DONE: server.js md5" $O/s6.out && grep -q "DONE: server.js md5" $O/s7.out'
node --check server.js && rm -rf .release-snapshots && git add -A >/dev/null 2>&1 && git commit -qm "live step 7 stand-in" >/dev/null 2>&1
snapall(){ find . \( -path ./.git -o -path ./.release-snapshots \) -prune -o -type f -print | sort | xargs md5sum; }
rm -rf /tmp/r8old; mkdir -p /tmp/r8old; cp server.js app.js index.html styles.css c93.css /tmp/r8old/
B7MD5=$(md5sum < server.js | cut -c1-32); B7SZ=$(wc -c < server.js)
export R8_LOCAL_PAYLOAD="$DEP"
D(){ bash "$DEP/deploy.sh" --dir $F "$@"; }
T(){ R8_LOCAL_TEST=1 R8_TEST_SERVER_MD5=$B7MD5 R8_TEST_SERVER_SIZE=$B7SZ D "$@"; }
TO(){ R8_LOCAL_TEST=1 R8_TEST_SERVER_MD5=$(md5sum < server.js | cut -c1-32) R8_TEST_SERVER_SIZE=$(wc -c < server.js) D "$@"; }
snapall > $O/pre.md5

echo "---- installer guards ----"
D --measure > $O/g0.out 2>&1; chk "refuses without the live step-7 server.js (real pins 589ede82, 2,538,324 B)" 'grep -q "not the live step-7" $O/g0.out'
T --measure > $O/m.out 2>&1; chk "measure ok, nothing written" 'grep -q "MEASURE only" $O/m.out && snapall | cmp -s - $O/pre.md5'
# record expected fixture md5/size from measure
EXP_MD5=$(sed -n 's/.*Expected server.js md5 \([0-9a-f]*\), \([0-9]*\) B.*/\1/p' $O/m.out)
EXP_SZ=$(sed -n 's/.*Expected server.js md5 [0-9a-f]*, \([0-9]*\) B.*/\1/p' $O/m.out)
echo "fixture expected md5 $EXP_MD5 size $EXP_SZ" | tee $O/expected.txt
T --dry-run > $O/d.out 2>&1; chk "dry-run ok, nothing written" 'grep -q "DRY RUN complete" $O/d.out && snapall | cmp -s - $O/pre.md5'
R8_LOCAL_TEST=1 R8_TEST_SERVER_MD5=0000 R8_TEST_SERVER_SIZE=$B7SZ D --dry-run > $O/g1.out 2>&1
chk "refuses a wrong server.js md5" 'grep -q "is not the live step-7" $O/g1.out'
for f in app.js index.html styles.css c93.css; do cp $f $O/keep; echo "/*x*/" >> $f; T --dry-run > $O/g_$f.out 2>&1; cp $O/keep $f; done
chk "refuses a changed app.js / index.html / styles.css / c93.css" 'for f in app.js index.html styles.css c93.css; do grep -q "$f md5" $O/g_$f.out || exit 1; done'
# break the trailing step-7 block
sed -i 's/var TAG = "chat112verifymail";/var TAG = "chat112verifymailX";/' server.js
TO --dry-run > $O/g2.out 2>&1; cp /tmp/r8old/server.js server.js
chk "refuses when the step-7 chat112verifymail block differs" 'grep -q "does not end with the exact live chat112verifymail" $O/g2.out'
# already-fixed line
python3 - <<'PY'
old = '      res.setHeader("Set-Cookie", [sessionCookie, "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120"].filter(Boolean));'
new = '      res.setHeader("Set-Cookie", [].concat(sessionCookie || [], "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120").filter(Boolean));'
s = open("server.js").read(); assert s.count(old)==1; open("server.js","w").write(s.replace(old,new,1))
PY
TO --dry-run > $O/g3.out 2>&1; cp /tmp/r8old/server.js server.js
chk "refuses when the Set-Cookie call is already flattened" 'grep -q "already present\|occurs 0 times, expected 1\|flattened Set-Cookie" $O/g3.out'
sed -i '2i // chat113cookie already here' server.js
TO --dry-run > $O/g4.out 2>&1; cp /tmp/r8old/server.js server.js
chk "refuses when chat113cookie already exists" 'grep -q "already contains chat113cookie" $O/g4.out'
mkdir -p bad; cp "$DEP"/*.py "$DEP"/server_block_*.js bad/; echo '//x' >> bad/server_block_chat113cookie.js
R8_LOCAL_PAYLOAD=$F/bad T --dry-run > $O/g5.out 2>&1; rm -rf bad
chk "tampered payload refused by sha256" 'grep -q "sha256 mismatch" $O/g5.out'
chk "all refusals left the project untouched" 'snapall | cmp -s - $O/pre.md5'

echo "---- apply / snapshot / restore ----"
T > $O/a.out 2>&1; chk "apply ok" 'grep -q "DONE: server.js md5" $O/a.out'
SN=$(ls -d $F/.release-snapshots/step8-* | head -1)
chk "snapshot step8-<TS>: server.js (= step 7) + manifest + restore script" 'cmp -s $SN/files/server.js /tmp/r8old/server.js && [ -f $SN/manifest.json ] && [ -f $SN/restore_release.py ] && basename $SN | grep -qE "^step8-[0-9]{8}-[0-9]{6}$"'
chk "exactly 1 file changed (server.js); app/index/styles/c93 byte-identical; node --check; expected md5/size" '[ "$(snapall | diff - $O/pre.md5 | grep -c "^<")" = 1 ] && snapall | diff - $O/pre.md5 | grep "^<" | grep -q " ./server.js$" && for f in app.js index.html styles.css c93.css; do cmp -s $f /tmp/r8old/$f || exit 1; done && node --check server.js && [ "$(md5sum < server.js | cut -c1-32)" = "$EXP_MD5" ] && [ "$(wc -c < server.js | tr -d " ")" = "$EXP_SZ" ]'
python3 -c "
import pathlib
dep=pathlib.Path('$DEP'); old=pathlib.Path('/tmp/r8old/server.js').read_bytes(); new=pathlib.Path('server.js').read_bytes()
blk=(dep/'server_block_chat113cookie.js').read_bytes().rstrip(b'\n')+b'\n'
s7=(dep/'server_block_chat112verifymail.js').read_bytes().rstrip(b'\n')+b'\n'
OL=b'      res.setHeader(\"Set-Cookie\", [sessionCookie, \"dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120\"].filter(Boolean));\n'
NW=b'      res.setHeader(\"Set-Cookie\", [].concat(sessionCookie || [], \"dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120\").filter(Boolean));\n'
assert old.endswith(s7) and new.endswith(s7+blk)
assert old.replace(OL,NW,1)+blk == new
" && echo SHAPE_OK > $O/shape.out || echo SHAPE_BAD > $O/shape.out
chk "server.js shape: only the one Set-Cookie flatten plus chat113cookie" 'grep -q SHAPE_OK $O/shape.out'

python3 $SN/restore_release.py $SN > $O/r.out 2>&1
chk "restore puts step 7 back byte-exact" 'cmp -s server.js /tmp/r8old/server.js'
echo x >> server.js; python3 $SN/restore_release.py $SN > $O/r2.out 2>&1
chk "restore refuses without --force if server.js changed after release" 'grep -q "Re-run with --force" $O/r2.out'
cp /tmp/r8old/server.js server.js; sleep 1; T > $O/a2.out 2>&1
chk "re-apply ok (new snapshot)" 'grep -q "DONE" $O/a2.out && [ $(ls -d $F/.release-snapshots/step8-* | wc -l) = 2 ]'

echo "---- auth servers: new (step 8) and old (step 7) ----"
CD=/tmp/r8cache; for p in 8871 8864 8865; do kp $p; done
(CACHE_DIR=$CD PORT=8871 node /workspace/c109/release-step1/test/cacheproxy.js > $O/proxy.log 2>&1 &)
sleep 0.7
ENVP="DISPATCH_RECOVERY_DELIVERY_PROVIDER=resend DISPATCH_PUBLIC_ORIGIN=https://thedispatch.uk DISPATCH_RECOVERY_DELIVERY_TIMEOUT_MS=1500 UPSTREAM_HTTP=localhost:8871 RAW_HTML=/workspace/c109/live_home.html"
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.new MOCK_RESEND_LOG=$O/mail.new NETLOG=$O/net.new NODE_OPTIONS="--require $H/netlog.js" PORT=8864 node server.js > $O/rel.log 2>&1 &)
(env $ENVP DISPATCH_RECOVERY_EMAIL_FROM="The Dispatch <accounts@thedispatch.uk>" MOCK_RESEND_MODE_FILE=$O/mode.old MOCK_RESEND_LOG=$O/mail.old NETLOG=$O/net.old NODE_OPTIONS="--require $H/netlog.js" PORT=8865 node /tmp/r8old/server.js > $O/old.log 2>&1 &)
sleep 5
chk "log: chat113cookie attaches once; verifymail/navy/credits/r6p once" '[ "$(grep -c "\[chat113cookie\] attached" $O/rel.log)" = 1 ] && for t in "chat112verifymail\] attached" "chat110navy\] attached" "chat107credits\] attached" "c102r6p\] scrub attached"; do [ "$(grep -c "$t" $O/rel.log)" = 1 ] || exit 1; done && ! grep -q "chat113cookie" $O/old.log'

hdr(){ curl -sS -D - -o /dev/null "$@"; }
post(){ # $1 key $2 port $3 data $4 path
  curl -sS -o $A/$1.body -D $A/$1.hdr -c $A/$1.jar -b $A/$1.jar -X POST --data "$3" "http://localhost:$2$4" >/dev/null
}
me(){ curl -sS -b $A/$1.jar "http://localhost:$2/api/me"; }
# capture raw Set-Cookie without following
rawpost(){ curl -sS -o $A/$1.body -D $A/$1.hdr -X POST --data "$3" "http://localhost:$2$4" >/dev/null; }

for side in new:8864 old:8865; do n=${side%%:*}; p=${side##*:}
  rawpost reg_$n $p 'name=&email=new1@example.com&password=newpassword1' /__auth/register
  # fill jar via a second request that also signs in
  post regj_$n $p 'name=&email=new1b@example.com&password=newpassword1' /__auth/register
  me regj_$n $p > $A/me_reg_$n.json
  post login_$n $p 'email=old@example.com&password=oldpassword1' /__auth/login
  rawpost loginraw_$n $p 'email=old@example.com&password=oldpassword1' /__auth/login
  me login_$n $p > $A/me_login_$n.json
  rawpost sub_$n $p 'email=new2@example.com&password=newpassword2' /__auth/subscribe
  post subj_$n $p 'email=new2b@example.com&password=newpassword2' /__auth/subscribe
  me subj_$n $p > $A/me_sub_$n.json
  rawpost subold_$n $p 'email=old@example.com&password=oldpassword1' /__auth/subscribe
  # logout uses the signed-in jar from login
  curl -sS -o $A/logout_$n.body -D $A/logout_$n.hdr -c $A/logout_$n.jar -b $A/login_$n.jar -X POST --data '' "http://localhost:$p/__auth/logout" >/dev/null
  me logout_$n $p > $A/me_logout_$n.json
  # guest me and a couple of pages for route-sameness
  curl -sS -o $A/me_guest_$n.body -D $A/me_guest_$n.hdr "http://localhost:$p/api/me" >/dev/null
  curl -sS -o $A/page_login_$n.body -D $A/page_login_$n.hdr "http://localhost:$p/__auth/login" >/dev/null
  curl -sS -o $A/page_reg_$n.body -D $A/page_reg_$n.hdr "http://localhost:$p/__auth/register" >/dev/null
  curl -sS -o $A/page_sub_$n.body -D $A/page_sub_$n.hdr "http://localhost:$p/__auth/subscribe" >/dev/null
done

python3 - $A > $A/summary.txt <<'PY'
import json, sys, re, pathlib
A = pathlib.Path(sys.argv[1])

def cookies(key):
    hdr = (A / (key + ".hdr")).read_bytes().replace(b"\r\n", b"\n").decode("utf-8", "replace")
    lines = []
    for l in hdr.splitlines():
        if l.lower().startswith("set-cookie:"):
            v = l.split(":", 1)[1].strip()
            v = re.sub(r"dispatch_session=[0-9a-f]{64}", "dispatch_session=<token>", v)
            lines.append(v)
    status = hdr.splitlines()[0].split(" ")[1] if hdr.splitlines() else "?"
    loc = [l.split(":",1)[1].strip() for l in hdr.splitlines() if l.lower().startswith("location:")]
    return status, loc, lines

def joined(vals):
    return any("dispatch_session=" in v and ",dispatch_session=" in v for v in vals)

def session_token_headers(vals):
    # raw values before normalisation
    return [v for v in vals if v.startswith("dispatch_session=")]

ok = True
def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + ((" " + detail) if detail else ""))
    ok = ok and cond

# --- new (step 8) raw headers ---
st, loc, ck = cookies("reg_new")
check("free sign-up: 302 to /", st == "302" and loc == ["/"])
check("free sign-up: 3 flat session Set-Cookie, no account_created, no comma-join",
      len(ck) == 3 and all(v.startswith("dispatch_session=") for v in ck) and not joined(ck) and not any("dispatch_account_created" in v for v in ck),
      str(ck))
check("free sign-up raw includes the session token placeholder", any(v.startswith("dispatch_session=<token>") for v in ck))

st, loc, ck = cookies("sub_new")
check("Premium new-account: 302 to /?checkout=1", st == "302" and loc == ["/?checkout=1"])
check("Premium new-account: 4 flat Set-Cookie (3 session + account_created), no comma-join",
      len(ck) == 4 and not joined(ck) and ck[-1].startswith("dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120") and sum(v.startswith("dispatch_session=") for v in ck) == 3,
      str(ck))
check("Premium new-account raw includes the session token placeholder", any(v.startswith("dispatch_session=<token>") for v in ck))

st, loc, ck = cookies("loginraw_new")
check("login: 3 flat session Set-Cookie, no account_created",
      st == "302" and loc == ["/"] and len(ck) == 3 and not joined(ck) and all(v.startswith("dispatch_session=") for v in ck), str(ck))

st, loc, ck = cookies("subold_new")
check("Premium existing-account: setSession only (no account_created, not comma-joined)",
      st == "302" and loc == ["/?checkout=1"] and not joined(ck) and not any("dispatch_account_created" in v for v in ck), str(ck))

st, loc, ck = cookies("logout_new")
check("logout: 302 and clear-session cookies, no established token",
      st == "302" and loc == ["/"] and all("<token>" not in v for v in ck) and any(v.startswith("dispatch_session=") for v in ck), str(ck))

# --- /api/me ---
def me(key):
    return json.loads((A / key).read_text())

for label, key in (("free sign-up", "me_reg_new.json"), ("login", "me_login_new.json"), ("Premium new-account", "me_sub_new.json")):
    m = me(key)
    check("/api/me signed in after " + label, m.get("guest") is False and m.get("email") and m.get("tier") == "free", json.dumps(m))

m = me("me_logout_new.json")
check("/api/me is guest after logout", m.get("guest") is True, json.dumps(m))

# --- old (step 7) still has the bug; other auth paths match new ---
st, loc, ck = cookies("sub_old")
check("step-7 Premium new-account still comma-joins session cookies (control)",
      joined(ck) and any(v.startswith("dispatch_account_created=1") for v in ck), str(ck))

for k in ("reg", "loginraw", "subold", "logout"):
    n, o = cookies(k + "_new"), cookies(k + "_old")
    check(k + " status/location/cookies identical on step 7 vs step 8", n == o, "new=%s old=%s" % (n, o))

# bodies of guest routes unchanged
for k in ("me_guest", "page_login", "page_reg", "page_sub"):
    bn, bo = (A / (k + "_new.body")).read_bytes(), (A / (k + "_old.body")).read_bytes()
    hn = [l.lower() for l in (A / (k + "_new.hdr")).read_text(errors="replace").splitlines() if l]
    ho = [l.lower() for l in (A / (k + "_old.hdr")).read_text(errors="replace").splitlines() if l]
    stn = hn[0].split(" ")[1] if hn else "?"; sto = ho[0].split(" ")[1] if ho else "?"
    check(k + " status+body identical on step 7 vs step 8", bn == bo and stn == sto, "status %s vs %s len %d vs %d" % (stn, sto, len(bn), len(bo)))

# subscribe-new cookies MUST differ (this is the fix)
n, o = cookies("sub_new"), cookies("sub_old")
check("Premium new-account cookies differ from step 7 (the fix)", n != o)

print("ALLOK" if ok else "NOTOK")
PY
cat $A/summary.txt
chk "auth + cookie integration (raw headers, /api/me, login/logout, other routes unchanged)" 'grep -q ALLOK $A/summary.txt'

# curl jar: after Premium sign-up on step 8, the follow-up /api/me was signed in (already checked).
# Also confirm curl jar has one session token + account_created for Premium, and only a session for free.
python3 - $A <<'PY'
import pathlib, re, sys
A = pathlib.Path(sys.argv[1])
def jar(key):
    rows = []
    for line in (A/(key+".jar")).read_text().splitlines():
        if not line or line.startswith("#"): continue
        p = line.split("\t")
        if len(p) >= 7: rows.append((p[5], p[6]))
    return rows
# curl's jar may omit HttpOnly depending on version; /api/me already proved the session was sent.
print("regj jar", jar("regj_new"))
print("subj jar", jar("subj_new"))
print("logout jar", jar("logout_new"))
PY

# shutdown
for p in 8864 8865 8871; do kp $p; done

echo
echo "RESULTS: $PASS passed, $FAIL failed"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
