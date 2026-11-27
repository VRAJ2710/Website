#!/bin/bash
# Builds a git fixture that mimics the Replit workspace: commit "r6n" (live files) then dev commits, r6n .bak files, untracked files.
set -e
F=${1:-/tmp/r1fix}; rm -rf "$F"; mkdir -p "$F"; cd "$F"
LIVE=/workspace/c109/live
python3 - "$F/server.js" <<'PY'
import sys
pre = open("/workspace/c108/deploy-chat108saferxC/test/make_synthetic.py").read()
a = pre.index("prefix = r'''") + len("prefix = r'''"); b = pre.index("'''", a)
p = pre[a:b].replace("// SYNTHETIC TEST SERVER (box only). Markers for guards: [chat106softgate] attached\nconst VERIFY_ENFORCE = false;\n", "// SYNTHETIC r6n STAND-IN (box only): serves the captured LIVE r6n home, proxies other GETs to the live site.\n")
p = p.replace('const DEV = "41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev";', 'const DEV = "thedispatch.uk";')
assert 'thedispatch.uk' in p and 'softgate' not in p
r6 = open("/workspace/c107/deploy-chat107credits/server_block_c102r6p.js").read()
open(sys.argv[1], "w").write(p + r6)
PY
cp $LIVE/app.js app.js; cp /workspace/c109/index.r6n.candidate.html index.html; cp $LIVE/styles.css $LIVE/c93.css $LIVE/logo-mark.svg $LIVE/manifest.json $LIVE/llms.txt $LIVE/og-card.svg .
mkdir -p attached_assets data-cache; echo "pdf" > attached_assets/brief.pdf; echo '{"t":1}' > data-cache/x.json
printf 'run = "node server.js"\n' > .replit; printf '{"name":"dispatch"}\n' > package.json; printf 'node_modules/\n.release-snapshots/\n' > .gitignore
git init -q; git config user.email t@t; git config user.name t; git add -A; git commit -qm "r6n publish"
R6N_SERVER=$(md5sum server.js | cut -c1-32)
cp server.js server.js.20261111-070219.bak-chat102r6o; cp app.js app.js.20261111-070219.bak-chat102r6o; cp index.html index.html.20261111-070219.bak-chat102r6o
git add -A; git commit -qm "r6o backups"
# dev changes (navy base, email verification, etc. stand-ins)
printf '\n// dev fef1da0 stand-in: email_verified, paid-first Ask\n' >> server.js; printf '\n// navy\n' >> app.js; sed -i 's/chat102r6n/chat102r6o/' index.html
printf '\n/* navy */\n' >> styles.css; echo '@import url(styles.css);' > c93.css; printf '[env]\nRESEND=1\n' >> .replit
mkdir -p migrations; echo "ALTER TABLE x;" > migrations/0001.sql; echo "// new" > recoverySenderCheck.js; git rm -q attached_assets/brief.pdf
echo '{"t":2}' > data-cache/x.json; git add -A; git commit -qm "dev fef1da0"
cp server.js server.js.20261127-092541.bak-chat108saferxC
mkdir -p scripts; echo "print(1)" > scripts/compare-redesign-tests.py; echo "uncommitted" >> llms.txt
mkdir -p node_modules/x; echo x > node_modules/x/i.js
echo "$R6N_SERVER"
