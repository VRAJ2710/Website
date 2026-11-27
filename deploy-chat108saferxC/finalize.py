# Rebuild the block and refresh the sha256 manifest in deploy.sh (PAYLOAD_COMMIT is pinned separately after the payload push).
import hashlib, re, subprocess, os
d = os.path.dirname(os.path.abspath(__file__)); os.chdir(d)
subprocess.check_call(["python3", "build_block.py"]); subprocess.check_call(["node", "--check", "server_block_chat108saferxC.js"])
s = open("deploy.sh").read(); sh = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for f in ("patch_chat108saferxC.py", "server_block_chat108saferxC.js", "server_block_chat108saferxB.js"):
    s = re.sub(re.escape(f) + r' [0-9a-zA-Z_]+"', f + " " + sh(f) + '"', s)
open("deploy.sh", "w").write(s); print("manifest refreshed")
