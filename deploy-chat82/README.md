# deploy-chat82 — bb10c (server) + rt62d (app/index) for thedispatch.uk

Applies on top of the live chat81 files (verified md5): server.js e7f75c9bccd6668a8b075d682444af49 (bb10b), app.js 78e28a26d768f8cbd0458f1609717ffb (chat81; also confirmed from https://thedispatch.uk/app.js?v=chat81), index.html 1d1a37cfa43dde4d1281363414452954 (chat81).
Apply order: bb10c (server.js), then rt62d (app.js chat81->chat82, index v=chat82).
Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat82-bb10c-rt62d/deploy-chat82/deploy.sh -o /tmp/deploy82.sh && echo "0664a686589e901227ed615bbba2b9330481eb327ae5a4898dff7d039bcdc59b  /tmp/deploy82.sh" | sha256sum -c - && bash /tmp/deploy82.sh --dry-run
    bash /tmp/deploy82.sh

--dry-run also prints one informational line: whether Coinbase https://api.exchange.coinbase.com/products/BTC-USD/stats is REACHABLE from Replit (10 s timeout; never aborts).
Options: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or final) aborts before touching live files.
The rt62d script prints "WARN index.html md5 ... expected prefix 83bb6a28" — harmless: it was authored against a different on-disk index; anchors decide, and deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | e5391dbbb4a41e4ddfed1140560973e2 | 602b3ef3318072afb7ad9acecbfd6c4a90379aeee0ea6b6b4c25adb390c4136a (22406 lines) |
| app.js | e45d14a361587253a328c0de1ff4c791 | e6b3b6ba2311841c3b966b3fc2f1748660d139f9eb53aec4507d9f98d407bea0 |
| index.html | 16c4bade1ff3baf1e7d1f335402d74fa | eb7dad16a30653695392d61396a44de96aa916dfaf3403a93829925d56a60622 |

index.html differs from the live chat81 file by exactly one line: app.js?v=chat81 -> app.js?v=chat82. (Frontend quoted index md5 30af5ae4…, from a different base copy; the value above is the real result on the verified live chat81 index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat82 next to each file. Rollback = copy the three backups back, then Republish.

## Patch file sha256
0664a686589e901227ed615bbba2b9330481eb327ae5a4898dff7d039bcdc59b  deploy.sh
1e66449950523be9088ea04cc2a201c7efa9bbb74234fa5af35c8b03a20ba043  patch_bb10c.py
62eae1ed2f1402d3967d22b64d1ee309fce6a73630c2d6f663edcafb7abc689a  patch_rt62d.py

patch_rt62d.py = PR #78 commit 264e9bb2ec05c08b68970ab9470ddbc0428c5dc9 (deploy/), byte-identical.
patch_bb10c.py = /workspace/bb10c/patch_bb10c.py (sha256 08e63697f5d5a0a85509f12a48d3ae7fc8e181e3a0176fcb6fdb81e8a63baa02, kept as patch_bb10c.orig.py) plus the same 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12). Identical output on Python 3.10/3.11/3.12/3.13. bb10c.diff is for review only.

## Fallback if raw GitHub is unreachable from Replit (local files only: bundle-b64-part-00..01, 16 KB each)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files' contents back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat82/deploy.sh --dry-run && bash /tmp/deploy-chat82/deploy.sh
bundle.tgz sha256: 77895e540756f69f24f8e71486a67bdbc65289a439ca4c97168144add60535f2
