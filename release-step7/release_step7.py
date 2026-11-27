#!/usr/bin/env python3
# Release step 7: verification emails, ENFORCEMENT OFF (chat112verifymail). Changes ONLY server.js: the last block (step 6,
# chat111verify) is replaced by chat112verifymail. Nothing before it changes. No schema, migration, env var or secret.
# Refuses unless server.js is the LIVE step-6 build (md5 343f7f30..., 2,521,438 B) ending in the exact chat110navyb +
# chat111verify blocks, app.js/index.html/styles.css/c93.css are the live files, and every prefix anchor the block relies on
# is present exactly as expected (sql, tokenHash, sessions, both sign-up routes, currentUser, sameOriginMutation, page, and the
# existing Resend connector wiring) with no verification code already in the prefix. Snapshots server.js first.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, os, shutil, subprocess, sys, time, json
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
sys.dont_write_bytecode = True; sys.path.insert(0, PAY); from anchors import A
T = os.environ.get("R7_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
SRV_MD5 = tv("R7_TEST_SERVER_MD5", "343f7f30ecebc6526a60ff90e1f49a48"); SRV_SIZE = int(tv("R7_TEST_SERVER_SIZE", "2521438"))
PIN = {"app.js": "f7678ca9b0284afea8bf74581fdf44eb", "index.html": "11652c2aaeb8a06a5d83c308d3a472e7",
       "styles.css": "290a380259ad5a4f1bdbcc787df8e196", "c93.css": "7858e81781d304e1d1ef19a4562a4fc6"}
def say(m): print("[release-step7] " + m, flush=True)
def die(m): print("[release-step7] ABORT: " + m, file=sys.stderr); print("[release-step7] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
md5b = lambda b: hashlib.md5(b).hexdigest()
rd = lambda p: open(os.path.join(ROOT, p), "rb").read()
payload = lambda p: open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SRV_SIZE: die("server.js is %d B, not the live step-6 %d B" % (len(srv), SRV_SIZE))
if md5b(srv) != SRV_MD5: die("server.js md5 %s is not the live step-6 %s" % (md5b(srv), SRV_MD5))
for f, m in PIN.items():
    if not os.path.isfile(os.path.join(ROOT, f)): die(f + " missing")
    if md5b(rd(f)) != m: die("%s md5 %s is not the live file (%s)" % (f, md5b(rd(f)), m))
navy = payload("server_block_chat110navyb.js").rstrip(b"\n") + b"\n"
s6 = payload("server_block_chat111verify.js").rstrip(b"\n") + b"\n"
blk = payload("server_block_chat112verifymail.js").rstrip(b"\n") + b"\n"
if not srv.endswith(navy + s6) or srv.count(s6) != 1 or srv.count(navy) != 1: die("server.js does not end with the exact live chat110navyb + chat111verify blocks")
for m, n in ((b'var TAG = "chat110navy";', 1), (b"site.css?v=chat110navyb", 1), (b'var TAG = "chat107credits";', 1), (b"[c102r6p] scrub attached", 1)):
    if srv.count(m) != n: die("%r occurs %d times in server.js, expected %d" % (m, srv.count(m), n))
prefix = srv[:-len(navy + s6)]
for a, n in A:
    if prefix.count(a) != n: die("prefix anchor %r occurs %d times, expected %d" % (a[:70], prefix.count(a), n))
if blk.count(b"var VERIFY_ENFORCE = false;") != 1 or b"VERIFY_ENFORCE = true" in blk: die("payload block must keep VERIFY_ENFORCE = false")
for m, n in ((b'var TAG = "chat111verify";', 1), (b"chat112verifymail", 0)):
    if srv.count(m) != n: die("%r occurs %d times in server.js, expected %d" % (m, srv.count(m), n))
newsrv = srv[:-len(s6)] + blk
say("server.js = live step 6 (ends with the exact chat110navyb + chat111verify blocks, %d prefix anchors ok); delta = chat111verify replaced by chat112verifymail, %+d B" % (len(A), len(newsrv) - len(srv)))
sd = "/tmp/release-step7"; os.makedirs(sd, exist_ok=True); open(os.path.join(sd, "server.js"), "wb").write(newsrv)
if subprocess.run(["node", "--check", os.path.join(sd, "server.js")]).returncode != 0: die("node --check failed on the scratch server.js")
say("scratch ok: server.js %d B md5 %s (app.js, index.html, styles.css, c93.css unchanged)" % (len(newsrv), md5b(newsrv)))
if MODE == "measure": say("MEASURE only: nothing written. Expected server.js md5 %s, %d B" % (md5b(newsrv), len(newsrv))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sd); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step7-" + ts); k = 1
while os.path.exists(snap): k += 1; snap = os.path.join(ROOT, ".release-snapshots", "step7-%s-%d" % (ts, k))
os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed: server.js")
json.dump({"step": "release-step7 (chat112verifymail: verification emails, enforcement off)", "created": ts, "dev_head": head,
           "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(newsrv)}, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step7-tmp"; open(tmp, "wb").write(newsrv); os.replace(tmp, dst)
except Exception as e:
    print("[release-step7] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s --force" % (e, snap, snap), file=sys.stderr); sys.exit(1)
if md5b(rd("server.js")) != md5b(newsrv) or subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0:
    print("[release-step7] VERIFY FAILED. Restore with: python3 %s/restore_release.py %s --force" % (snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Other files untouched." % (md5b(newsrv), len(newsrv), md5b(srv)))
say("Restart ONLY 'Start application'; expect one '[chat112verifymail] attached (enforcement off; verification emails on)' (dev says 'off: delivery not configured') plus the usual navy/credits/r6p lines. Publish only if Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
