#!/usr/bin/env python3
# Release step 1: live r6n + v3 home page as the default. Run by deploy.sh from the Replit project folder.
# It (1) proves which git commit is the live r6n tree (r6n .bak files on dev + pinned live fingerprints), (2) snapshots every
# dev file it will touch into .release-snapshots/step1-<TS>/ (with a manifest and restore script), (3) writes the r6n version of
# every file that changed since r6n, moves dev-only files aside, and (4) appends the five v3 blocks to the r6n server.js.
# Modes: measure | dry-run | apply. No git writes, no DB, no network, no server start, no publish.
import hashlib, json, os, shutil, subprocess, sys, time
MODE, ROOT, PAY = sys.argv[1], os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
T = os.environ.get("R1_LOCAL_TEST") == "1"
PIN = {
    "server.js": os.environ.get("R1_TEST_SERVER_MD5") if T and os.environ.get("R1_TEST_SERVER_MD5") else "4bfbb35e6854158b8e6e09309aa7aa61",
    "app.js": "bd13a193f2a16ef7d7a4508c25231bb9",      # = live https://thedispatch.uk/app.js (27 Nov 2026)
    "styles.css": "8023e711df4aaadbab1e1b4264bfd8c5",  # = live /styles.css
    "c93.css": "9d6a86a64135b1cc58e6af7b12973550",     # = live /c93.css
}
INFO = {"logo-mark.svg": "ff0e681027bc672d6fd12abe04ab7274", "manifest.json": "311101dac6bd8e909fa5e381f56be550",
        "llms.txt": "9a73ee75f3d6a92df10b5923d8879046", "og-card.svg": "443c9475edf3e30e7b801492ebaa0317"}
BLOCKS = ["server_block_chat105v3home2.js", "server_block_chat108saferxA.js", "server_block_chat108saferxB.js",
          "server_block_chat108saferxC.js", "server_block_chat109v3default.js"]
SKIP_DIRS = (".git/", "node_modules/", ".backups/", ".release-snapshots/", "data-cache/", ".cache/", ".ruff_cache/",
             ".dispatch-patch-scratch/", ".local/", ".upm/", ".config/", ".pythonlibs/")
def say(m): print("[release-step1] " + m, flush=True)
def die(m): print("[release-step1] ABORT: " + m, file=sys.stderr); print("[release-step1] Nothing in the project was changed.", file=sys.stderr); sys.exit(1)
def md5b(b): return hashlib.md5(b).hexdigest()
def rd(p): return open(os.path.join(ROOT, p), "rb").read()
def git(*a, binary=False):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", ROOT] + list(a), capture_output=True)
    if r.returncode != 0: raise RuntimeError("git " + " ".join(a) + ": " + r.stderr.decode(errors="replace").strip())
    return r.stdout if binary else r.stdout.decode()
def skipped(p): return p.startswith(SKIP_DIRS) or ".bak-" in p or p.endswith((".bak",)) or "/.bak" in p
# 0. project and git
if not os.path.isfile(os.path.join(ROOT, "server.js")): die("no server.js in " + ROOT)
try: head = git("rev-parse", "HEAD").strip()
except Exception as e: die("git is not usable here (" + str(e) + "); the r6n tree is taken from git history")
say("project " + ROOT + " | HEAD " + head)
for f in ("server.js", "app.js", "index.html"): say("dev %s md5 %s (%d B)" % (f, md5b(rd(f)), len(rd(f))))
# 1. the r6n files saved on dev when r6o was installed (11 Nov 07:02 UK) = the state published as e73d611a (r6n)
def one(pref):
    c = sorted(x for x in os.listdir(ROOT) if x.startswith(pref) and x.endswith(".bak-chat102r6o"))
    if len(c) != 1: die("expected exactly one %s*.bak-chat102r6o, found %d" % (pref, len(c)))
    return c[0]
bak = {f: one(f + ".") for f in ("server.js", "app.js", "index.html")}
bb = {f: rd(bak[f]) for f in bak}
for f in ("server.js", "app.js"):
    if md5b(bb[f]) != PIN[f]: die("%s md5 %s is not the r6n pin %s" % (bak[f], md5b(bb[f]), PIN[f]))
if bb["index.html"].count(b"/app.js?v=chat102r6n") != 1: die(bak["index.html"] + " does not load /app.js?v=chat102r6n once")
say("r6n backups ok: %s %s | %s %s (= live app.js) | %s %s" % (bak["server.js"], md5b(bb["server.js"]), bak["app.js"], md5b(bb["app.js"]), bak["index.html"], md5b(bb["index.html"])))
# 2. the git commit that holds exactly those three files and the live stylesheets
def blob(b): return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
want = {f: blob(bb[f]) for f in bb}
r6n = None
for c in git("log", "--format=%H", "-n", "600").split():
    try:
        if all(git("rev-parse", c + ":" + f).strip() == want[f] for f in want): r6n = c; break
    except Exception: continue
if not r6n: die("no commit in the last 600 has the r6n server.js, app.js and index.html; cannot rebuild the full r6n tree")
for f in ("styles.css", "c93.css"):
    try: m = md5b(git("show", r6n + ":" + f, binary=True))
    except Exception: die(f + " missing in " + r6n)
    if m != PIN[f]: die("%s in %s has md5 %s, not the live %s" % (f, r6n[:10], m, PIN[f]))
for f, w in INFO.items():
    try: m = md5b(git("show", r6n + ":" + f, binary=True)); say("info: %s in r6n %s (live %s)%s" % (f, m, w, "" if m == w else "  <-- differs, may be served dynamically"))
    except Exception: say("info: %s not in r6n tree" % f)
say("r6n commit: %s (%s)" % (r6n, git("log", "-1", "--format=%cd %s", "--date=iso", r6n).strip()))
# 3. deltas: tracked changes since r6n (working tree vs r6n) and untracked dev-only files
r6n_files = set(git("ls-tree", "-r", "--name-only", r6n).split("\n")) - {""}
modified, restored, aside = [], [], []
for line in git("diff", "--name-status", "--no-renames", r6n).splitlines():
    st, p = line.split("\t", 1)
    if skipped(p): continue
    if st == "D": restored.append(p)
    elif p in r6n_files: modified.append(p)
    else: aside.append(p)
for p in git("ls-files", "--others", "--exclude-standard").splitlines():
    if p and not skipped(p) and p not in r6n_files: aside.append(p)
for p in ("server.js", "app.js", "index.html"):
    if p not in modified: modified.append(p)
modified, restored, aside = sorted(set(modified)), sorted(set(restored)), sorted(set(aside))
say("files to put back to r6n: %d | deleted since r6n, to restore: %d | dev-only, to move aside: %d" % (len(modified), len(restored), len(aside)))
for p in modified: say("  r6n  " + p)
for p in restored: say("  back " + p)
for p in aside: say("  aside " + p)
if MODE == "measure": say("MEASURE only: nothing written."); sys.exit(0)
# 4. payload blocks and the new server.js (scratch)
blks = []
for b in BLOCKS:
    d = open(os.path.join(PAY, b), "rb").read()
    for bad in (b"process.env", b"child_process", b"ALTER TABLE", b"CREATE TABLE", b"DROP TABLE", b"require(\"fs\")"):
        if bad in d: die(b + " mentions " + bad.decode())
    blks.append(d.rstrip(b"\n") + b"\n")
base = bb["server.js"]
if b"chat105v3home" in base or b"chat108saferx" in base or b"chat109v3default" in base: die("r6n server.js already has a v3 block")
new = base + (b"" if base.endswith(b"\n") else b"\n") + b"".join(blks)
os.makedirs("/tmp/release-step1", exist_ok=True); sp = "/tmp/release-step1/server.js"; open(sp, "wb").write(new)
if subprocess.run(["node", "--check", sp]).returncode != 0: die("node --check failed on the scratch server.js")
if new[:len(base)] != base: die("r6n bytes changed in scratch")
say("scratch server.js ok: r6n %d B + v3 blocks %d B = %d B, md5 %s" % (len(base), len(new) - len(base), len(new), md5b(new)))
if MODE == "dry-run": say("DRY RUN complete: nothing in the project written. Scratch: " + sp); sys.exit(0)
# 5. snapshot the exact dev files (every path this step touches) BEFORE any write
ts = time.strftime("%Y%m%d-%H%M%S"); snap = os.path.join(ROOT, ".release-snapshots", "step1-" + ts); os.makedirs(snap)
man = {"step": "release-step1 (r6n + v3 default)", "created": ts, "dev_head": head, "r6n_commit": r6n, "files": {}}
for p in sorted(set(modified + restored + aside)):
    src = os.path.join(ROOT, p)
    if os.path.isfile(src):
        dst = os.path.join(snap, "files", p); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        if md5b(open(dst, "rb").read()) != md5b(open(src, "rb").read()): die("snapshot copy failed for " + p)
        man["files"][p] = md5b(open(src, "rb").read())
    else: man["files"][p] = None   # did not exist on dev: restore deletes it
man["release_server_md5"] = md5b(new)
json.dump(man, open(os.path.join(snap, "manifest.json"), "w"), indent=1)
shutil.copy2(os.path.join(PAY, "restore_release.py"), os.path.join(snap, "restore_release.py"))
say("snapshot: %s (%d files, manifest.json, restore_release.py)" % (snap, len(man["files"])))
# 6. write the release tree
try:
    for p in modified + restored:
        data = new if p == "server.js" else bb[p] if p in ("app.js", "index.html") else git("show", r6n + ":" + p, binary=True)
        dst = os.path.join(ROOT, p); os.makedirs(os.path.dirname(dst) or ROOT, exist_ok=True)
        tmp = dst + ".release-step1-tmp"; open(tmp, "wb").write(data); os.replace(tmp, dst)
    for p in aside:
        if os.path.isfile(os.path.join(ROOT, p)): os.remove(os.path.join(ROOT, p))
except Exception as e:
    print("[release-step1] ERROR while writing: %s. Restore with: python3 %s/restore_release.py %s" % (e, snap, snap), file=sys.stderr); sys.exit(1)
# 7. verify
bad = []
if md5b(rd("server.js")) != md5b(new): bad.append("server.js")
for f in ("app.js", "styles.css", "c93.css"):
    if md5b(rd(f)) != PIN[f]: bad.append(f)
if subprocess.run(["node", "--check", os.path.join(ROOT, "server.js")]).returncode != 0: bad.append("node --check")
tree = {}
for l in git("ls-tree", "-r", r6n).splitlines():
    meta, path = l.split("\t", 1)
    if meta.split()[1] == "blob": tree[path] = meta.split()[2]
left = []
for path, bl in tree.items():
    if skipped(path) or path == "server.js": continue
    fp = os.path.join(ROOT, path)
    if not os.path.isfile(fp) or blob(open(fp, "rb").read()) != bl: left.append(path)
extra = [p for p in git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
         if p and not skipped(p) and p not in tree and os.path.isfile(os.path.join(ROOT, p))]
if left: bad.append("still differs from r6n: " + ", ".join(left[:10]))
if extra: bad.append("dev-only files left: " + ", ".join(extra[:10]))
if bad:
    print("[release-step1] VERIFY FAILED: %s. Restore with: python3 %s/restore_release.py %s" % ("; ".join(bad), snap, snap), file=sys.stderr); sys.exit(1)
say("DONE: the tree now equals r6n %s except server.js (r6n + v3 blocks, md5 %s, %d B)." % (r6n[:10], md5b(new), len(new)))
say("app.js, styles.css, c93.css = live. Restart ONLY 'Start application' and check, then publish only if Vraj approves.")
say("Restore dev exactly: python3 %s/restore_release.py %s" % (snap, snap))
