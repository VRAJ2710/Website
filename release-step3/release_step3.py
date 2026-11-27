#!/usr/bin/env python3
# Release step 3: live step 2 (r6n + r6p + v3 default) + the FRED source credits (chat107credits, commit 12e9f76f) with the
# /calendar/ raw-ID fix. server.js only: app.js, index.html and the stylesheets are not touched (credits needs no app.js change).
# It proves server.js is exactly <r6n prefix> + <step-2 r6p scrub> + <the five v3 blocks> (rebuilt from the r6n backup and the
# pinned payload, so the unknown post-step-2 md5 is not needed), then appends the credits block at the end.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
T = os.environ.get("R3_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
PIN = {"app.js": "bd13a193f2a16ef7d7a4508c25231bb9", "index.html": tv("R3_TEST_INDEX_MD5", "932c42324a218a02a1bd69f64a6f5757"),
       "styles.css": "8023e711df4aaadbab1e1b4264bfd8c5", "c93.css": "9d6a86a64135b1cc58e6af7b12973550"}
SIZE = int(tv("R3_TEST_SERVER_SIZE", "2472342"))
R6N_PIN = tv("R3_TEST_R6N_MD5", "4bfbb35e6854158b8e6e09309aa7aa61")
OPT_MD5 = os.environ.get("STEP2_SERVER_MD5", "")   # optional: the md5 Replit printed after step 2; checked when given
BLOCKS = ["server_block_chat105v3home2.js", "server_block_chat108saferxA.js", "server_block_chat108saferxB.js",
          "server_block_chat108saferxC.js", "server_block_chat109v3default.js"]
MARKER = b"// chat102r6c last-write scrub."
def say(m): print("[release-step3] " + m, flush=True)
def die(m): print("[release-step3] ABORT: " + m, file=sys.stderr); print("[release-step3] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
def md5b(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()
def rd(p): return open(os.path.join(ROOT, p), "rb").read()
def payload(p): return open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SIZE: die("server.js is %d B, not the post-step-2 %d B" % (len(srv), SIZE))
if OPT_MD5 and md5b(srv) != OPT_MD5: die("server.js md5 %s is not STEP2_SERVER_MD5 %s" % (md5b(srv), OPT_MD5))
for f in ("app.js", "index.html", "styles.css", "c93.css"):
    m = md5b(rd(f)) if os.path.isfile(os.path.join(ROOT, f)) else "missing"
    if m != PIN[f]: die("%s md5 %s is not the live file (%s)" % (f, m, PIN[f]))
# 1. exact post-step-2 structure
c = sorted(x for x in os.listdir(ROOT) if x.startswith("server.js.") and x.endswith(".bak-chat102r6o"))
if len(c) != 1: die("expected exactly one server.js*.bak-chat102r6o (the r6n server), found %d" % len(c))
r6n = rd(c[0])
if md5b(r6n) != R6N_PIN: die("%s md5 %s is not the r6n pin %s" % (c[0], md5b(r6n), R6N_PIN))
if r6n.count(MARKER) != 1: die("scrub marker found %d times in the r6n server" % r6n.count(MARKER))
i = r6n.index(MARKER); prefix = r6n[:i]
if r6n[i:].rstrip(b"\n") != payload("server_block_c102r6n.js").rstrip(b"\n"): die("the r6n backup does not end with the published r6n scrub")
p6 = payload("server_block_c102r6p.js").rstrip(b"\n") + b"\n"
tail = b"".join(payload(b).rstrip(b"\n") + b"\n" for b in BLOCKS)
step2 = prefix + p6 + tail
if srv != step2: die("server.js is not exactly the step-2 build (r6n prefix + r6p scrub + v3 blocks); expected md5 %s, %d B" % (md5b(step2), len(step2)))
for m, n in ((b"[c102r6p] scrub attached", 1), (b"[c102r6n] scrub attached", 0), (b"[c102r6o] scrub attached", 0), (b"[chat107credits]", 0), (b"[chat106softgate]", 0), (b'var TAG = "chat109v3default";', 1)):
    if srv.count(m) != n: die("%r occurs %d times in server.js, expected %d" % (m, srv.count(m), n))
say("server.js = post-step-2 build, byte-exact (r6n prefix %d B + r6p %d B + v3 blocks %d B)" % (len(prefix), len(p6), len(tail)))
# 2. credits block
cb = payload("server_block_chat107credits.js").rstrip(b"\n") + b"\n"
if cb.count(b'var TAG = "chat107credits";') != 1 or cb.count(b'console.log("[" + TAG + "] attached")') != 1: die("credits block attach line missing")
for need in (b"function fredIds", b"data-c107-ids", b"This product uses FRED\\u00ae data but is not endorsed or certified by the Federal Reserve Bank of St. Louis."):
    if need not in cb: die("credits block is missing " + need.decode(errors="replace"))
for bad in (b"process.env", b"child_process", b"ALTER TABLE", b"CREATE TABLE", b"DROP TABLE", b"require(\"fs\")", b"VERIFY_ENFORCE", b"resend"):
    if bad in cb: die("credits block mentions " + bad.decode())
new = srv + cb
open_dir = "/tmp/release-step3"; os.makedirs(open_dir, exist_ok=True); spath = open_dir + "/server.js"; open(spath, "wb").write(new)
if subprocess.run(["node", "--check", spath]).returncode != 0: die("node --check failed on the scratch server.js")
if not new.startswith(srv) or new.count(b'var TAG = "chat107credits";') != 1: die("scratch build wrong")
say("scratch server.js ok: step 2 %d B + credits %d B = %d B, md5 %s" % (len(srv), len(cb), len(new), md5b(new)))
if MODE == "measure": say("MEASURE only: nothing written. Expected release server.js md5 %s, %d B" % (md5b(new), len(new))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + spath); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step3-" + ts); os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed")
man = {"step": "release-step3 (step 2 + FRED source credits)", "created": ts, "dev_head": head, "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(new)}
json.dump(man, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step3-tmp"; open(tmp, "wb").write(new); os.replace(tmp, dst)
except Exception as e:
    print("[release-step3] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s" % (e, snap, snap), file=sys.stderr); sys.exit(1)
bad = []
if md5b(rd("server.js")) != md5b(new): bad.append("server.js md5")
if subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0: bad.append("node --check")
for f in ("app.js", "index.html", "styles.css", "c93.css"):
    if md5b(rd(f)) != PIN[f]: bad.append(f)
if bad:
    print("[release-step3] VERIFY FAILED: %s. Restore with: python3 %s/restore_release.py %s" % ("; ".join(bad), snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Nothing else changed." % (md5b(new), len(new), md5b(srv)))
say("Restart ONLY 'Start application'; expect one '[chat107credits] attached' and one '[c102r6p] scrub attached'. Publish only if Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
