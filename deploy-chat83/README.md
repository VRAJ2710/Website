# deploy-chat83 — bb10d (server) + rt62e (app/index) for thedispatch.uk

Applies on top of the live chat82 files (verified md5): server.js e5391dbbb4a41e4ddfed1140560973e2 (bb10c), app.js e45d14a361587253a328c0de1ff4c791 (chat82; also confirmed from https://thedispatch.uk/app.js?v=chat82), index.html 16c4bade1ff3baf1e7d1f335402d74fa (chat82).
Apply order: bb10d (server.js), then rt62e (app.js chat82->chat83, index v=chat83).
Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat83-bb10d-rt62e/deploy-chat83/deploy.sh -o /tmp/deploy83.sh && echo "6d141cd6d2ca6fcf930bf38b1ba65cd85a0872432e41dae578b0ddf666a2da0b  /tmp/deploy83.sh" | sha256sum -c - && bash /tmp/deploy83.sh --dry-run
    bash /tmp/deploy83.sh

--dry-run also prints one informational line: whether Coinbase https://api.exchange.coinbase.com/products/BTC-USD/stats is REACHABLE from Replit (10 s timeout; never aborts).
Options: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or final) aborts before touching live files.
The rt62e script prints "WARN index.html md5 ... expected prefix 30af5ae4" — harmless: it was authored against a different on-disk index; anchors decide, and deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 6a359cecb836848284c2264d13122482 | 067ab1e873bd906670f190244db8a59dea573706e9da639f2b5a01285fabe916 |
| app.js | ef0ce14cde79cd45a9eae72e2031ece7 | 1dfb8ef48e0a5a4450f423bc00903c5ba5794b7bd1a545d246024f62bcd4ac0e |
| index.html | 1d6725049d4a819e7a5d268713037bcc | 95aaa61102c2c0d83236b951716c51f92770e64c3dcd73468cb74263fce5fe35 |

index.html differs from the live chat82 file by exactly one line: app.js?v=chat82 -> app.js?v=chat83. (Frontend quoted index md5 f3c5613f…, from a different base copy; the value above is the real result on the verified live chat82 index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat83 next to each file. Rollback = copy the three backups back, then Republish.

## Patch file sha256
6d141cd6d2ca6fcf930bf38b1ba65cd85a0872432e41dae578b0ddf666a2da0b  deploy.sh
ae39146e8ecaa4b2c87fa4e48d63b7d5bdb04a0ee01d3bcd85fa4ab7d36024eb  patch_bb10d.py
8baf9969da1697149bd835fcdf9483e68fb7e7c7f67119fd42ce41e94e4495f2  patch_rt62e.py

patch_rt62e.py = PR #79 commit 78a5e324897b0f64ee8a7a464cd67ecd3d05609e (deploy/), byte-identical.
patch_bb10d.py = /workspace/bb10d/patch_bb10d.py (md5 dbef741e948c636310f1ec9658d8cdda, sha256 cb2ccdbd33211c8b8b0691cc5e294974428b117dc2cf9b47339f95469ee38a8a, kept as patch_bb10d.orig.py) plus the same 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12). Identical output on Python 3.10/3.11/3.12/3.13. bb10d.diff is for review only.

## Fallback if raw GitHub is unreachable from Replit (local files only: bundle-b64-part-00..01)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files' contents back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat83/deploy.sh --dry-run && bash /tmp/deploy-chat83/deploy.sh
bundle.tgz sha256: b83af3bbb986cd7c8d7c6841b64f7d66f34af13f93e0e57eef5190c03f9e83d5
