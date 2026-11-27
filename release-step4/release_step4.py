#!/usr/bin/env python3
# Release step 4: live step 3 (r6n + r6p + v3 default + FRED credits) + the navy redesign VISUALS (chat110navy).
# Changes exactly four files: styles.css (navy, DM Sans), c93.css (compat import), index.html (7 exact edits: navy shell class,
# device-default theme, cache tags v=chat110navy), app.js (46 presentation hunks hand-split from the navy commits, applied to the
# live bd13a193) and appends one presentation-only response-transform block to server.js. No auth, verification, Resend,
# checkout, Ask provider-order, Stripe or email_verified code. Snapshots all five files first (manifest + restore script).
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, re, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
T = os.environ.get("R4_LOCAL_TEST") == "1"
def tv(k, d): return os.environ.get(k) if T and os.environ.get(k) else d
PIN = {"app.js": "bd13a193f2a16ef7d7a4508c25231bb9", "index.html": tv("R4_TEST_INDEX_MD5", "932c42324a218a02a1bd69f64a6f5757"),
       "styles.css": "8023e711df4aaadbab1e1b4264bfd8c5", "c93.css": "9d6a86a64135b1cc58e6af7b12973550"}
NEW = {"app.js": "f7678ca9b0284afea8bf74581fdf44eb", "styles.css": "290a380259ad5a4f1bdbcc787df8e196",
       "c93.css": "7858e81781d304e1d1ef19a4562a4fc6", "index.html": tv("R4_TEST_NEW_INDEX_MD5", "11652c2aaeb8a06a5d83c308d3a472e7")}
SIZE = int(tv("R4_TEST_SERVER_SIZE", "2493329"))
R6N_PIN = tv("R4_TEST_R6N_MD5", "4bfbb35e6854158b8e6e09309aa7aa61")
OPT_MD5 = os.environ.get("STEP3_SERVER_MD5", "")
BLOCKS = ["server_block_chat105v3home2.js", "server_block_chat108saferxA.js", "server_block_chat108saferxB.js",
          "server_block_chat108saferxC.js", "server_block_chat109v3default.js", "server_block_chat107credits.js"]
MARKER = b"// chat102r6c last-write scrub."
def say(m): print("[release-step4] " + m, flush=True)
def die(m): print("[release-step4] ABORT: " + m, file=sys.stderr); print("[release-step4] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
def md5b(b): return hashlib.md5(b).hexdigest()
def rd(p): return open(os.path.join(ROOT, p), "rb").read()
def payload(p): return open(os.path.join(PAY, p), "rb").read()
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip() or "none"
except Exception: head = "none"
srv = rd("server.js")
say("project %s | HEAD %s | server.js md5 %s (%d B)" % (ROOT, head, md5b(srv), len(srv)))
if len(srv) != SIZE: die("server.js is %d B, not the post-step-3 %d B" % (len(srv), SIZE))
if OPT_MD5 and md5b(srv) != OPT_MD5: die("server.js md5 %s is not STEP3_SERVER_MD5 %s" % (md5b(srv), OPT_MD5))
cur = {}
for f in ("app.js", "index.html", "styles.css", "c93.css"):
    cur[f] = rd(f) if os.path.isfile(os.path.join(ROOT, f)) else None
    m = md5b(cur[f]) if cur[f] is not None else "missing"
    if m != PIN[f]: die("%s md5 %s is not the live file (%s)" % (f, m, PIN[f]))
# 1. exact post-step-3 structure: r6n prefix + r6p scrub + 5 v3 blocks + credits
c = sorted(x for x in os.listdir(ROOT) if x.startswith("server.js.") and x.endswith(".bak-chat102r6o"))
if len(c) != 1: die("expected exactly one server.js*.bak-chat102r6o (the r6n server), found %d" % len(c))
r6n = rd(c[0])
if md5b(r6n) != R6N_PIN: die("%s md5 %s is not the r6n pin %s" % (c[0], md5b(r6n), R6N_PIN))
if r6n.count(MARKER) != 1: die("scrub marker found %d times in the r6n server" % r6n.count(MARKER))
i = r6n.index(MARKER); prefix = r6n[:i]
if r6n[i:].rstrip(b"\n") != payload("server_block_c102r6n.js").rstrip(b"\n"): die("the r6n backup does not end with the published r6n scrub")
step3 = prefix + payload("server_block_c102r6p.js").rstrip(b"\n") + b"\n" + b"".join(payload(b).rstrip(b"\n") + b"\n" for b in BLOCKS)
if srv != step3: die("server.js is not exactly the step-3 build (r6n prefix + r6p + v3 blocks + credits); expected md5 %s, %d B" % (md5b(step3), len(step3)))
for m, n in ((b"[c102r6p] scrub attached", 1), (b"[c102r6n] scrub attached", 0), (b'var TAG = "chat107credits";', 1), (b"[chat106softgate]", 0),
             (b'var TAG = "chat109v3default";', 1), (b'var TAG = "chat110navy";', 0)):
    if srv.count(m) != n: die("%r occurs %d times in server.js, expected %d" % (m, srv.count(m), n))
say("server.js = post-step-3 build, byte-exact (r6n prefix %d B + r6p + v3 blocks + credits)" % len(prefix))
# 2. the r6n server must not depend on any index.html string this step edits (else its shell injection would silently miss)
edits = json.loads(payload("index_edits.json").decode("utf-8"))
def ctx(p):
    k = prefix.index(p); return prefix[max(0, k - 120):k + len(p) + 120].decode("utf-8", "replace").replace("\n", " ")
for probe in (b"styles.css?v=chat1", b"c93.css?v=chat93", b"app.js?v=chat102r6n", b"classList.add('c93')", b".seo-public{max-width:980px",
              b"family=Inter:wght@400;500;600&display=swap", b"/api/market-reference-quotes\" as=\"fetch\""):
    if prefix.count(probe): die("server.js references %r (%d x), so the index/cache-tag edit may not be self-contained. First context: %s" % (probe, prefix.count(probe), ctx(probe)))
say("server.js prefix does not reference any index.html string this step edits")
# 3. build the four new files
lines = cur["app.js"].decode("utf-8").split("\n")
pj = json.loads(payload("app_navy_patch.json").decode("utf-8"))
if pj["base_md5"] != PIN["app.js"]: die("app patch is for another base")
for h in sorted(pj["hunks"], key=lambda h: -h["a1"]):
    if h["op"] == "a": lines[h["a1"]:h["a1"]] = h["new"]
    else:
        if lines[h["a1"] - 1:h["a2"]] != h["old"]: die("app.js hunk %s does not match the live file" % h["id"])
        lines[h["a1"] - 1:h["a2"]] = h["new"]
newf = {"app.js": "\n".join(lines).encode("utf-8")}
ix = cur["index.html"].decode("utf-8")
for o, n in edits:
    if ix.count(o) != 1: die("index.html edit anchor found %d times: %r" % (ix.count(o), o[:60]))
    ix = ix.replace(o, n)
newf["index.html"] = ix.encode("utf-8")
newf["styles.css"] = payload("styles.navy.css"); newf["c93.css"] = payload("c93.css")
for f, m in NEW.items():
    if md5b(newf[f]) != m: die("built %s md5 %s is not the expected %s" % (f, md5b(newf[f]), m))
appd = newf["app.js"].decode("utf-8")
for bad in ("isPrimaryLiveQuote(a.tk);const retained", '"NO LIVE SYNC"}', "CHAT_AI_UNAVAILABLE, retryable: true", 'return "dark";'):
    if bad in appd and bad not in cur["app.js"].decode("utf-8"): die("excluded app.js code present: " + bad)
nb = payload("server_block_chat110navy.js").rstrip(b"\n") + b"\n"
if nb.count(b'var TAG = "chat110navy";') != 1 or nb.count(b'console.log("[" + TAG + "] " + "attached")') != 1: die("navy block attach line missing")
for bad in (b"process.env", b"child_process", b"ALTER TABLE", b"CREATE TABLE", b"DROP TABLE", b"require(\"fs\")", b"VERIFY_ENFORCE", b"resend", b"Resend", b"stripe.", b"setCookie", b"Set-Cookie", b"email_verified", b"fallbackOrder"):
    if bad in nb: die("navy block mentions " + bad.decode())
newsrv = srv + nb
sd = "/tmp/release-step4"; os.makedirs(sd, exist_ok=True)
for f, b in list(newf.items()) + [("server.js", newsrv)]: open(os.path.join(sd, f), "wb").write(b)
for f in ("server.js", "app.js"):
    if subprocess.run(["node", "--check", os.path.join(sd, f)]).returncode != 0: die("node --check failed on the scratch " + f)
say("scratch ok: server.js %d B md5 %s | app.js %d B md5 %s | index.html %d B md5 %s | styles.css %d B md5 %s | c93.css %d B md5 %s" % (
    len(newsrv), md5b(newsrv), len(newf["app.js"]), md5b(newf["app.js"]), len(newf["index.html"]), md5b(newf["index.html"]),
    len(newf["styles.css"]), md5b(newf["styles.css"]), len(newf["c93.css"]), md5b(newf["c93.css"])))
if MODE == "measure": say("MEASURE only: nothing written. Expected release server.js md5 %s, %d B" % (md5b(newsrv), len(newsrv))); sys.exit(0)
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sd); sys.exit(0)
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step4-" + ts); os.makedirs(os.path.join(snap, "files"))
files = {"server.js": srv, "app.js": cur["app.js"], "index.html": cur["index.html"], "styles.css": cur["styles.css"], "c93.css": cur["c93.css"]}
for f, b in files.items():
    shutil.copy2(os.path.join(ROOT, f), os.path.join(snap, "files", f))
    if md5b(open(os.path.join(snap, "files", f), "rb").read()) != md5b(b): die("snapshot copy failed: " + f)
man = {"step": "release-step4 (step 3 + navy visuals chat110navy)", "created": ts, "dev_head": head,
       "files": {f: md5b(b) for f, b in files.items()}, "release_server_md5": md5b(newsrv)}
json.dump(man, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (server.js app.js index.html styles.css c93.css, manifest.json, restore_release.py)" % snap)
try:
    for f, b in list(newf.items()) + [("server.js", newsrv)]:
        dst = os.path.join(ROOT, f); tmp = dst + ".release-step4-tmp"; open(tmp, "wb").write(b); os.replace(tmp, dst)
except Exception as e:
    print("[release-step4] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s --force" % (e, snap, snap), file=sys.stderr); sys.exit(1)
bad = [f for f, b in list(newf.items()) + [("server.js", newsrv)] if md5b(rd(f)) != md5b(b)]
for f in ("server.js", "app.js"):
    if subprocess.run(["node", "--check", os.path.join(ROOT, f)]).returncode != 0: bad.append("node --check " + f)
if bad:
    print("[release-step4] VERIFY FAILED: %s. Restore with: python3 %s/restore_release.py %s --force" % ("; ".join(bad), snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: server.js md5 %s, %d B (was %s). app.js %s, index.html %s, styles.css %s, c93.css %s." % (
    md5b(newsrv), len(newsrv), md5b(srv), NEW["app.js"], NEW["index.html"], NEW["styles.css"], NEW["c93.css"]))
say("Restart ONLY 'Start application'; expect one '[chat110navy] attached', one '[chat107credits] attached', one '[c102r6p] scrub attached'. Publish only if Vraj approves.")
say("Restore: python3 %s/restore_release.py %s" % (snap, snap))
