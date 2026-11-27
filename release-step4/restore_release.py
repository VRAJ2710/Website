#!/usr/bin/env python3
# Restore the dev workspace exactly as it was before a release step: copies back every file in the snapshot manifest and
# deletes files that did not exist on dev. Usage: python3 restore_release.py <snapshot-dir> [--force]
import hashlib, json, os, shutil, sys
snap = os.path.abspath(sys.argv[1]); force = "--force" in sys.argv
root = os.path.dirname(os.path.dirname(snap))  # <root>/.release-snapshots/<name>
man = json.load(open(os.path.join(snap, "manifest.json")))
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
def die(m): print("[restore] ABORT: " + m, file=sys.stderr); sys.exit(1)
cur = md5(os.path.join(root, "server.js"))
if cur != man.get("release_server_md5") and not force:
    die("server.js (%s) is not the release server.js (%s); something changed after the release. Re-run with --force to restore anyway." % (cur, man.get("release_server_md5")))
for p, m in sorted(man["files"].items()):
    dst = os.path.join(root, p)
    if m is None:
        if os.path.isfile(dst):
            os.remove(dst); print("[restore] removed " + p)
            d = os.path.dirname(dst)
            while d != root and os.path.isdir(d) and not os.listdir(d): os.rmdir(d); d = os.path.dirname(d)
        continue
    src = os.path.join(snap, "files", p)
    if md5(src) != m: die("snapshot copy of %s is damaged" % p)
    os.makedirs(os.path.dirname(dst) or root, exist_ok=True); tmp = dst + ".restore-tmp"; shutil.copy2(src, tmp); os.replace(tmp, dst)
bad = [p for p, m in man["files"].items() if (m is None and os.path.exists(os.path.join(root, p))) or (m is not None and md5(os.path.join(root, p)) != m)]
if bad: die("verify failed for: " + ", ".join(bad))
print("[restore] DONE: %d files back to the dev state of %s (dev HEAD %s). Restart ONLY 'Start application'." % (len(man["files"]), man["created"], man["dev_head"][:10]))
