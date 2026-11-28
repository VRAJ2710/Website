#!/usr/bin/env python3
# Release step 9: chat114viz, the visuals pass (Market Snapshot, gauges, key-price row, sparklines, tiles, events timeline) on
# /brief/, /gold/, /markets/ and /research/. Changes ONLY server.js: appends one trailing block (chat114viz) after the step-8
# chat113cookie block. The block serves viz.css/viz.js itself (embedded strings) and injects them into those four pages' finished HTML.
# Nothing else changes: no prefix edit, no new file in the project, no endpoint, secret, config, schema, route, Stripe or page edit.
# Refuses unless server.js is the LIVE step 8 (md5 a633becf..., 2,539,589 B) ending in the exact chat112verifymail + chat113cookie blocks,
# app.js/index.html/styles.css/c93.css are the live files and the block-derived anchors match. Snapshots server.js first.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
sys.dont_write_bytecode = True
T = os.environ.get("R9_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
SRV_MD5 = tv("R9_TEST_SERVER_MD5", "a633becfed6eb4e12c88415cdccf6fd7"); SRV_SIZE = int(tv("R9_TEST_SERVER_SIZE", "2539589"))
PIN = {"app.js": "f7678ca9b0284afea8bf74581fdf44eb", "index.html": "11652c2aaeb8a06a5d83c308d3a472e7",
       "styles.css": "290a380259ad5a4f1bdbcc787df8e196", "c93.css": "7858e81781d304e1d1ef19a4562a4fc6"}
# anchors that come from the step 4/7/8 blocks themselves (identical in the stand-in fixture and on the real file)
A = [(b"emit.__chat110navy = 1;", 1), (b"globalThis.__c110navy = { transform: transform };", 1), (b"SP.emit.__chat113cookie = 1;", 1),
     (b'var TAG = "chat112verifymail";', 1), (b'var TAG = "chat113cookie";', 1), (b"function sessionCookieHeader(", 1)]
def say(m): print("[release-step9] " + m, flush=True)
def die(m): print("[release-step9] ABORT: " + m, file=sys.stderr); print("[release-step9] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
md5b = lambda b: hashlib.md5(b).hexdigest()
rd = lambda p: open(os.path.join(ROOT, p), "rb").read()
payload = lambda p: open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SRV_SIZE: die("server.js is %d B, not the live step-8 %d B" % (len(srv), SRV_SIZE))
if md5b(srv) != SRV_MD5: die("server.js md5 %s is not the live step-8 %s" % (md5b(srv), SRV_MD5))
for f, m in PIN.items():
    if not os.path.isfile(os.path.join(ROOT, f)): die(f + " missing")
    if md5b(rd(f)) != m: die("%s md5 %s is not the live file (%s)" % (f, md5b(rd(f)), m))
s7 = payload("server_block_chat112verifymail.js").rstrip(b"\n") + b"\n"
s8 = payload("server_block_chat113cookie.js").rstrip(b"\n") + b"\n"
blk = payload("server_block_chat114viz.js").rstrip(b"\n") + b"\n"
css = payload("viz.css").decode("utf-8"); js = payload("viz.js").decode("utf-8")
if not srv.endswith(s7 + s8) or srv.count(s8) != 1 or srv.count(s7) != 1: die("server.js does not end with the exact live chat112verifymail + chat113cookie blocks")
if srv.count(b"chat114viz") != 0: die("server.js already contains chat114viz")
for a, n in A:
    if srv.count(a) != n: die("anchor %r occurs %d times, expected %d" % (a[:80], srv.count(a), n))
# the block must embed exactly the two payload assets (the files the preview was approved with)
if json.dumps(css, ensure_ascii=True).encode() not in blk or json.dumps(js, ensure_ascii=True).encode() not in blk: die("block does not embed the exact viz.css / viz.js payload")
if blk.count(b'var TAG = "chat114viz";') != 1 or blk.count(b"[\" + TAG + \"] attached") != 1: die("block shape unexpected")
newsrv = srv + blk
if not newsrv.startswith(srv) or newsrv[len(srv):] != blk or newsrv.count(blk) != 1: die("unexpected rewrite shape")
say("server.js = live step 8 (ends with the exact chat112verifymail + chat113cookie blocks, %d anchors ok); delta = append chat114viz %+d B (viz.css %d B + viz.js %d B embedded)" % (len(A), len(blk), len(css.encode()), len(js.encode())))
sd = "/tmp/release-step9"; os.makedirs(sd, exist_ok=True); open(os.path.join(sd, "server.js"), "wb").write(newsrv)
if subprocess.run(["node", "--check", os.path.join(sd, "server.js")]).returncode != 0: die("node --check failed on the scratch server.js")
say("scratch ok: server.js %d B md5 %s (app.js, index.html, styles.css, c93.css unchanged)" % (len(newsrv), md5b(newsrv)))
if MODE == "measure": say("MEASURE only: nothing written. Expected server.js md5 %s, %d B" % (md5b(newsrv), len(newsrv))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sd); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step9-" + ts); k = 1
while os.path.exists(snap): k += 1; snap = os.path.join(ROOT, ".release-snapshots", "step9-%s-%d" % (ts, k))
os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed: server.js")
json.dump({"step": "release-step9 (chat114viz: visuals pass on brief, gold, markets, research)", "created": ts, "dev_head": head,
           "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(newsrv)}, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step9-tmp"; open(tmp, "wb").write(newsrv); os.replace(tmp, dst)
except Exception as e:
    print("[release-step9] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s --force" % (e, snap, snap), file=sys.stderr); sys.exit(1)
if md5b(rd("server.js")) != md5b(newsrv) or subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0:
    print("[release-step9] VERIFY FAILED. Restore with: python3 %s/restore_release.py %s --force" % (snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Other files untouched." % (md5b(newsrv), len(newsrv), md5b(srv)))
say("Restart ONLY 'Start application'; expect one '[chat114viz] attached' line after '[chat113cookie] attached'. Do not publish until Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
