#!/usr/bin/env python3
# Release step 4b: delta on top of the STAGED step 4. Changes ONLY server.js, and only inside the appended chat110navy block:
#   (1) embedded site.css, phone-width block: + html.nvb body:has(#c101-inst){padding-bottom:184px!important}
#       (the install bar sits above the 64px bottom bar, so the old 94px body padding left the footer's last line under it)
#   (2) site.css link cache tag v=chat110navy -> v=chat110navyb so phones fetch the new CSS.
# Refuses unless server.js is the staged step-4 build (md5 ec413c6b..., 2,517,162 B) ending in the exact step-4 block, and
# app.js/index.html/styles.css/c93.css are the step-4 files. Snapshots server.js first (manifest + restore script).
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, os, shutil, subprocess, sys, time, json
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
T = os.environ.get("R4B_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
SRV_MD5 = tv("R4B_TEST_SERVER_MD5", "ec413c6bd2562aa0cd14fc6d69e16210"); SRV_SIZE = int(tv("R4B_TEST_SERVER_SIZE", "2517162"))
PIN = {"app.js": "f7678ca9b0284afea8bf74581fdf44eb", "index.html": "11652c2aaeb8a06a5d83c308d3a472e7",
       "styles.css": "290a380259ad5a4f1bdbcc787df8e196", "c93.css": "7858e81781d304e1d1ef19a4562a4fc6"}
FIX_OLD = b"html.nvb #c101-inst{bottom:64px!important}\\n"
FIX_NEW = b"html.nvb #c101-inst{bottom:64px!important}\\n html.nvb body:has(#c101-inst){padding-bottom:184px!important}\\n"
LINK_OLD = b"var SITE_LINK = '<link rel=\"stylesheet\" href=\"/__navy/site.css?v=chat110navy\">';"
LINK_NEW = b"var SITE_LINK = '<link rel=\"stylesheet\" href=\"/__navy/site.css?v=chat110navyb\">'; // chat110navyb: footer padding fix + cache bust"
def say(m): print("[release-step4b] " + m, flush=True)
def die(m): print("[release-step4b] ABORT: " + m, file=sys.stderr); print("[release-step4b] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
md5b = lambda b: hashlib.md5(b).hexdigest()
rd = lambda p: open(os.path.join(ROOT, p), "rb").read()
payload = lambda p: open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SRV_SIZE: die("server.js is %d B, not the staged step-4 %d B" % (len(srv), SRV_SIZE))
if md5b(srv) != SRV_MD5: die("server.js md5 %s is not the staged step-4 %s" % (md5b(srv), SRV_MD5))
for f, m in PIN.items():
    if not os.path.isfile(os.path.join(ROOT, f)): die(f + " missing")
    if md5b(rd(f)) != m: die("%s md5 %s is not the step-4 file (%s)" % (f, md5b(rd(f)), m))
old = payload("server_block_chat110navy.js").rstrip(b"\n") + b"\n"
new = payload("server_block_chat110navyb.js").rstrip(b"\n") + b"\n"
if not srv.endswith(old) or srv.count(old) != 1: die("server.js does not end with the exact step-4 chat110navy block")
if old.count(FIX_OLD) != 1 or old.count(LINK_OLD) != 1: die("step-4 block anchors not found exactly once")
if old.replace(FIX_OLD, FIX_NEW).replace(LINK_OLD, LINK_NEW) != new: die("the 4b block is not exactly the step-4 block + the two edits")
for m, n in ((b'var TAG = "chat110navy";', 1), (b"chat110navyb", 0), (b"[chat107credits]", 0), (b'var TAG = "chat107credits";', 1), (b"[c102r6p] scrub attached", 1)):
    if srv.count(m) != n: die("%r occurs %d times in server.js, expected %d" % (m, srv.count(m), n))
newsrv = srv[:-len(old)] + new
say("server.js = staged step 4 (ends with the exact chat110navy block); delta = 2 edits inside that block, +%d B" % (len(newsrv) - len(srv)))
sd = "/tmp/release-step4b"; os.makedirs(sd, exist_ok=True); open(os.path.join(sd, "server.js"), "wb").write(newsrv)
if subprocess.run(["node", "--check", os.path.join(sd, "server.js")]).returncode != 0: die("node --check failed on the scratch server.js")
say("scratch ok: server.js %d B md5 %s (app.js, index.html, styles.css, c93.css unchanged)" % (len(newsrv), md5b(newsrv)))
if MODE == "measure": say("MEASURE only: nothing written. Expected server.js md5 %s, %d B" % (md5b(newsrv), len(newsrv))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sd); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step4b-" + ts); k = 1
while os.path.exists(snap): k += 1; snap = os.path.join(ROOT, ".release-snapshots", "step4b-%s-%d" % (ts, k))
os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed: server.js")
json.dump({"step": "release-step4b (step 4 + footer padding fix chat110navyb)", "created": ts, "dev_head": head,
           "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(newsrv)}, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step4b-tmp"; open(tmp, "wb").write(newsrv); os.replace(tmp, dst)
except Exception as e:
    print("[release-step4b] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s --force" % (e, snap, snap), file=sys.stderr); sys.exit(1)
if md5b(rd("server.js")) != md5b(newsrv) or subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0:
    print("[release-step4b] VERIFY FAILED. Restore with: python3 %s/restore_release.py %s --force" % (snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Other files untouched." % (md5b(newsrv), len(newsrv), md5b(srv)))
say("Restart ONLY 'Start application'; expect one '[chat110navy] attached', one '[chat107credits] attached', one '[c102r6p] scrub attached'. Publish only if Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
