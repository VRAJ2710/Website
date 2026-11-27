#!/usr/bin/env python3
# Release step 2: live step 1 (r6n + v3 default) + the r6p data fixes. Run by deploy.sh from the Replit project folder.
# server.js only. It proves server.js is exactly <r6n server backup> + <the five step-1 v3 blocks>, proves the r6n backup ends
# with the published r6n last-write scrub, and swaps that scrub for the r6p scrub (Terminal previous close = last completed
# daily session; r6o install-bar / UK-time / Gold-label fixes it was built on; the 15 Nov auth-page script strip; and the
# /api/real-yield blank-day fix). Every byte before the scrub and every v3 block byte after it stay the same.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
T = os.environ.get("R2_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
PIN = {"server.js": tv("R2_TEST_SERVER_MD5", "dc4ceaf91ea6992cee8c788bf61a52cf"),
       "app.js": "bd13a193f2a16ef7d7a4508c25231bb9", "index.html": tv("R2_TEST_INDEX_MD5", "932c42324a218a02a1bd69f64a6f5757"),
       "styles.css": "8023e711df4aaadbab1e1b4264bfd8c5", "c93.css": "9d6a86a64135b1cc58e6af7b12973550"}
SIZE = int(tv("R2_TEST_SERVER_SIZE", "2465272"))
R6N_PIN = tv("R2_TEST_R6N_MD5", "4bfbb35e6854158b8e6e09309aa7aa61")
BLOCKS = ["server_block_chat105v3home2.js", "server_block_chat108saferxA.js", "server_block_chat108saferxB.js",
          "server_block_chat108saferxC.js", "server_block_chat109v3default.js"]
MARKER = b"// chat102r6c last-write scrub."
def say(m): print("[release-step2] " + m, flush=True)
def die(m): print("[release-step2] ABORT: " + m, file=sys.stderr); print("[release-step2] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
def md5b(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()
def rd(p): return open(os.path.join(ROOT, p), "rb").read()
def payload(p): return open(os.path.join(PAY, p), "rb").read()
# 0. the live step-1 tree
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if md5b(srv) != PIN["server.js"] or len(srv) != SIZE:
    die("server.js md5 %s / %d B is not the live step-1 server (%s / %d B)" % (md5b(srv), len(srv), PIN["server.js"], SIZE))
for f in ("app.js", "index.html", "styles.css", "c93.css"):
    m = md5b(rd(f)) if os.path.isfile(os.path.join(ROOT, f)) else "missing"
    if m != PIN[f]: die("%s md5 %s is not the live step-1 file (%s)" % (f, m, PIN[f]))
say("live step-1 files ok: server.js, app.js, index.html, styles.css, c93.css")
# 1. server.js = r6n backup + v3 blocks, exactly
c = sorted(x for x in os.listdir(ROOT) if x.startswith("server.js.") and x.endswith(".bak-chat102r6o"))
if len(c) != 1: die("expected exactly one server.js*.bak-chat102r6o (the r6n server), found %d" % len(c))
r6n = rd(c[0])
if md5b(r6n) != R6N_PIN: die("%s md5 %s is not the r6n pin %s" % (c[0], md5b(r6n), R6N_PIN))
blks = []
for b in BLOCKS: blks.append(payload(b).rstrip(b"\n") + b"\n")
tail = b"".join(blks)
expect = r6n + (b"" if r6n.endswith(b"\n") else b"\n") + tail
if srv != expect: die("server.js is not exactly r6n backup + the five step-1 v3 blocks (someone changed it after step 1)")
say("server.js = %s (%d B) + v3 blocks (%d B), byte-exact" % (c[0], len(r6n), len(tail)))
# 2. the r6n backup ends with the published r6n scrub
if r6n.count(MARKER) != 1: die("scrub marker found %d times in the r6n server" % r6n.count(MARKER))
i = r6n.index(MARKER); prefix, scrub_n = r6n[:i], r6n[i:]
want_n = payload("server_block_c102r6n.js")
if scrub_n.rstrip(b"\n") != want_n.rstrip(b"\n"): die("the r6n scrub in server.js (%d B, sha256 %s) is not the published r6n block (%d B, sha256 %s)" % (len(scrub_n), sha(scrub_n), len(want_n), sha(want_n)))
if srv.count(b"[c102r6n] scrub attached") != 1 or b"[c102r6o] scrub attached" in srv or b"[c102r6p] scrub attached" in srv:
    die("expected exactly one r6n attach log and no r6o/r6p")
say("r6n scrub ok: %d B at byte %d, sha256 %s; prefix sha256 %s" % (len(scrub_n), i, sha(scrub_n), sha(prefix)))
# 3. the r6p block
p6 = payload("server_block_c102r6p.js").rstrip(b"\n") + b"\n"
for need in (b"chat102r6p:", b"c102r6pSessionPrev", b"c102r6pInstallQuote", b"realYieldPrev", b"/^\\/__auth(?:\\/|$)/"):
    if need not in p6: die("r6p block is missing " + need.decode())
if p6.count(b"[c102r6p] scrub attached") != 1 or b"[c102r6o] scrub attached" in p6 or b"[c102r6n] scrub attached" in p6: die("r6p block attach log is not the single r6p line")
if not p6.startswith(MARKER) or p6.count(MARKER) != 1: die("r6p block does not start with the scrub marker")
sp_ = p6.split(b"function c102r6pSessionPrev", 1)[-1].split(b"function c102r6pYahooQuote", 1)[0]
if b"chartPreviousClose" in sp_: die("c102r6pSessionPrev must not read chartPreviousClose")
for bad in (b"process.env", b"child_process", b"ALTER TABLE", b"CREATE TABLE", b"DROP TABLE", b"require(\"fs\")", b"xai", b"anthropic"):
    if bad in p6: die("r6p block mentions " + bad.decode())
# 4. scratch build
new = prefix + p6 + tail
if not new.startswith(prefix) or not new.endswith(tail): die("prefix or v3 tail changed in scratch")
if new.count(b"[c102r6p] scrub attached") != 1 or b"[c102r6n] scrub attached" in new: die("scratch attach logs wrong")
os.makedirs("/tmp/release-step2", exist_ok=True); spath = "/tmp/release-step2/server.js"; open(spath, "wb").write(new)
if subprocess.run(["node", "--check", spath]).returncode != 0: die("node --check failed on the scratch server.js")
say("scratch server.js ok: prefix %d B + r6p %d B + v3 blocks %d B = %d B, md5 %s" % (len(prefix), len(p6), len(tail), len(new), md5b(new)))
if MODE == "measure": say("MEASURE only: nothing written. Expected release server.js md5 %s, %d B" % (md5b(new), len(new))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + spath); sys.exit(0)
# 5. snapshot, then write
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step2-" + ts); os.makedirs(os.path.join(snap, "files"))
shutil.copy2(os.path.join(ROOT, "server.js"), os.path.join(snap, "files", "server.js"))
if md5b(open(os.path.join(snap, "files", "server.js"), "rb").read()) != md5b(srv): die("snapshot copy failed")
man = {"step": "release-step2 (step 1 + r6p data fixes)", "created": ts, "dev_head": head, "files": {"server.js": md5b(srv)}, "release_server_md5": md5b(new)}
json.dump(man, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js, manifest.json, restore_release.py)" % snap)
try:
    dst = os.path.join(ROOT, "server.js"); tmp = dst + ".release-step2-tmp"; open(tmp, "wb").write(new); os.replace(tmp, dst)
except Exception as e:
    print("[release-step2] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s" % (e, snap, snap), file=sys.stderr); sys.exit(1)
bad = []
if md5b(rd("server.js")) != md5b(new): bad.append("server.js md5")
if subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0: bad.append("node --check")
for f in ("app.js", "index.html", "styles.css", "c93.css"):
    if md5b(rd(f)) != PIN[f]: bad.append(f)
if bad:
    print("[release-step2] VERIFY FAILED: %s. Restore with: python3 %s/restore_release.py %s" % ("; ".join(bad), snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). Nothing else changed." % (md5b(new), len(new), md5b(srv)))
say("Restart ONLY 'Start application'; expect one '[c102r6p] scrub attached' line and no r6n attach. Publish only if Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
