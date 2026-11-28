#!/usr/bin/env python3
# Release step 10: chat115vizapp. Shows the approved chat114viz layer (same viz.css, viz.js, markup and data) to SIGNED-IN readers in
# the member app on /brief/, /gold/, /markets/ and /research/. Appends one trailing block after the step-9b chat114viz block. The block
# adds the chat114viz stylesheet and one mount script to the app shell HTML of requests with a dispatch_session cookie and serves
# that script at /__chat115vizapp/vizapp.js. app.js, index.html and every other file are untouched. Guest requests pass straight through.
# Refuses unless server.js is the STAGED step 9b (md5 9a875821..., 2,588,699 B) ending in the exact chat112verifymail + chat113cookie
# + step-9b chat114viz blocks, app.js/index.html/styles.css/c93.css are the live files and the block anchors match. Snapshots first.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
sys.dont_write_bytecode = True
T = os.environ.get("R9_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
SRV_MD5 = tv("R9_TEST_SERVER_MD5", "9a8758213ee7a63eb5d24757c3aa78f3"); SRV_SIZE = int(tv("R9_TEST_SERVER_SIZE", "2588699"))
PIN = {"app.js": "f7678ca9b0284afea8bf74581fdf44eb", "index.html": "11652c2aaeb8a06a5d83c308d3a472e7",
       "styles.css": "290a380259ad5a4f1bdbcc787df8e196", "c93.css": "7858e81781d304e1d1ef19a4562a4fc6"}
A = [(b"emit.__chat110navy = 1;", 1), (b"globalThis.__c110navy = { transform: transform };", 1), (b"SP.emit.__chat113cookie = 1;", 1),
     (b'var TAG = "chat112verifymail";', 1), (b'var TAG = "chat113cookie";', 1), (b"function sessionCookieHeader(", 1),
     (b'var TAG = "chat114viz";', 1), (b"emit.__chat114viz = 1;", 1), (b'"] injected " + path', 1)]
def say(m): print("[release-step10] " + m, flush=True)
def die(m): print("[release-step10] ABORT: " + m, file=sys.stderr); print("[release-step10] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
md5b = lambda b: hashlib.md5(b).hexdigest()
rd = lambda p: open(os.path.join(ROOT, p), "rb").read()
payload = lambda p: open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SRV_SIZE: die("server.js is %d B, not the staged step-9b %d B" % (len(srv), SRV_SIZE))
if md5b(srv) != SRV_MD5: die("server.js md5 %s is not the staged step-9b %s" % (md5b(srv), SRV_MD5))
for f, m in PIN.items():
    if not os.path.isfile(os.path.join(ROOT, f)): die(f + " missing")
    if md5b(rd(f)) != m: die("%s md5 %s is not the live file (%s)" % (f, md5b(rd(f)), m))
s7 = payload("server_block_chat112verifymail.js").rstrip(b"\n") + b"\n"
s8 = payload("server_block_chat113cookie.js").rstrip(b"\n") + b"\n"
s9 = payload("server_block_chat114viz.js").rstrip(b"\n") + b"\n"
blk = payload("server_block_chat115vizapp.js").rstrip(b"\n") + b"\n"
mjs = payload("vizapp.js").decode("utf-8")
if not srv.endswith(s7 + s8 + s9) or srv.count(s8) != 1 or srv.count(s7) != 1 or srv.count(s9) != 1:
    die("server.js does not end with the exact chat112verifymail + chat113cookie + step-9b chat114viz blocks")
if srv.count(b"chat115vizapp") != 0: die("server.js already contains chat115vizapp")
for a, n in A:
    if srv.count(a) != n: die("anchor %r occurs %d times, expected %d" % (a[:80], srv.count(a), n))
if json.dumps(mjs, ensure_ascii=True).encode() not in blk: die("block does not embed the exact vizapp.js payload")
if blk.count(b'var TAG = "chat115vizapp";') != 1 or blk.count(b"[\" + TAG + \"] attached") != 1 or blk.count(b"\"] injected \" + path") != 1: die("block shape unexpected")
newsrv = srv + blk
if not newsrv.startswith(srv) or newsrv[len(srv):] != blk or newsrv.count(blk) != 1: die("unexpected rewrite shape")
say("server.js = staged step 9b (ends with the exact chat112verifymail + chat113cookie + step-9b chat114viz blocks, %d anchors ok); delta = append chat115vizapp %+d B (vizapp.js %d B embedded)" % (len(A), len(blk), len(mjs.encode())))
sd = "/tmp/release-step10"; os.makedirs(sd, exist_ok=True); open(os.path.join(sd, "server.js"), "wb").write(newsrv)
if subprocess.run(["node", "--check", os.path.join(sd, "server.js")]).returncode != 0: die("node --check failed on the scratch server.js")
say("scratch ok: server.js %d B md5 %s (app.js, index.html, styles.css, c93.css unchanged)" % (len(newsrv), md5b(newsrv)))
if MODE == "measure": say("MEASURE only: nothing written. Expected server.js md5 %s, %d B" % (md5b(newsrv), len(newsrv))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sd); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step10-" + ts); k = 1
while os.path.exists(snap): k += 1; snap = os.path.join(ROOT, ".release-snapshots", "step10-%s-%d" % (ts, k))
os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed: server.js")
json.dump({"step": "release-step10 (chat115vizapp: visuals layer for signed-in readers in the member app)", "created": ts, "dev_head": head,
           "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(newsrv)}, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step10-tmp"; open(tmp, "wb").write(newsrv); os.replace(tmp, dst)
except Exception as e:
    print("[release-step10] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s --force" % (e, snap, snap), file=sys.stderr); sys.exit(1)
if md5b(rd("server.js")) != md5b(newsrv) or subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0:
    print("[release-step10] VERIFY FAILED. Restore with: python3 %s/restore_release.py %s --force" % (snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Other files untouched." % (md5b(newsrv), len(newsrv), md5b(srv)))
say("Restart ONLY 'Start application'; expect '[chat115vizapp] attached' after '[chat114viz] attached', then '[chat115vizapp] injected <path>' on the first signed-in app page. Do not publish until Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
