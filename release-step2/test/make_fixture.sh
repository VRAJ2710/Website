#!/bin/bash
# Builds a fixture that mimics the live step-1 Replit tree: server.js = r6n stand-in (stub prefix + the REAL published r6n
# scrub block) + the five v3 blocks; server.js.*.bak-chat102r6o = the r6n stand-in; live app.js/styles/c93; r6n index.
set -e
F=${1:-/tmp/r2fix}; DEP=$(cd "$(dirname "$0")/.." && pwd); rm -rf "$F"; mkdir -p "$F"; cd "$F"
LIVE=/workspace/c109/live
python3 - "$DEP" <<'PY'
import sys
dep = sys.argv[1]
pre = open("/workspace/c108/deploy-chat108saferxC/test/make_synthetic.py").read()
a = pre.index("prefix = r'''") + len("prefix = r'''"); b = pre.index("'''", a)
p = pre[a:b].replace("// SYNTHETIC TEST SERVER (box only). Markers for guards: [chat106softgate] attached\nconst VERIFY_ENFORCE = false;\n", "// SYNTHETIC r6n STAND-IN (box only): stub prefix + the real r6n scrub.\n")
p = p.replace('const DEV = "41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev";', 'const DEV = "thedispatch.uk";')
r6n = (p + open(dep + "/server_block_c102r6n.js").read()).encode()
open("server.js.20261111-070219.bak-chat102r6o", "wb").write(r6n)
blocks = ["server_block_chat105v3home2.js", "server_block_chat108saferxA.js", "server_block_chat108saferxB.js", "server_block_chat108saferxC.js", "server_block_chat109v3default.js"]
tail = b"".join(open(dep + "/" + x, "rb").read().rstrip(b"\n") + b"\n" for x in blocks)
open("server.js", "wb").write(r6n + (b"" if r6n.endswith(b"\n") else b"\n") + tail)
PY
cp $LIVE/app.js app.js; cp /workspace/c109/index.r6n.candidate.html index.html; cp $LIVE/styles.css $LIVE/c93.css $LIVE/logo-mark.svg $LIVE/manifest.json .
cp app.js app.js.20261111-070219.bak-chat102r6o; cp index.html index.html.20261111-070219.bak-chat102r6o
mkdir -p data-cache; echo '{"t":1}' > data-cache/x.json; printf 'run = "node server.js"\n' > .replit
git init -q; git config user.email t@t; git config user.name t; git add -A; git commit -qm "live step 1"
echo "$(md5sum < server.js | cut -c1-32) $(wc -c < server.js) $(md5sum < server.js.20261111-070219.bak-chat102r6o | cut -c1-32)"
