# deploy-maint2 — SERVER-ONLY bb10j for thedispatch.uk

Applies bb10j to server.js only, on top of live bb10i / maint1 (md5 d01094a38f0fbf00800ccd1bbc5f733c). app.js (21f3cee5…) and index.html (35084b10…) are never modified; deploy.sh prints their md5s before and after and fails if they change. Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-maint2-bb10j/deploy-maint2/deploy.sh -o /tmp/deploy_maint2.sh && echo "cf0d44825fe3d4d75fe31579252ef4c36014c87529b79abedeac693980cf1717  /tmp/deploy_maint2.sh" | sha256sum -c - && bash /tmp/deploy_maint2.sh --dry-run
    bash /tmp/deploy_maint2.sh

--dry-run also prints one informational Coinbase reachability line. Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Base md5 mismatch (including the older bb10g), patch sha256 mismatch or result mismatch aborts before touching the live file.

## Expected result
| file | md5 | sha256 |
|---|---|---|
| server.js | 92a2ce51dfc1bf3e16466d7451d9ae1a | 2ac42ae446bfdeefe2c30cc72561f7b54d6b763bc2c051a40950addcba2765b5 |
| app.js | 21f3cee5da20d9fc2f2f03d21623dcb4 | unchanged |
| index.html | 35084b102b38f99b582838aa19dadfad | unchanged |

Backup: server.js.<YYYYmmdd-HHMMSS>.bak-maint2. Rollback = copy it back to server.js, then Republish.

## sha256
cf0d44825fe3d4d75fe31579252ef4c36014c87529b79abedeac693980cf1717  deploy.sh
a9e6a741d8f486b7ea00fe774f67427e60e2c56191689bfdf3afdcd11d64c32c  patch_bb10j.py

patch_bb10j.py = /workspace/bb10j/patch_bb10j.py (md5 56668a504d9ea59630a943d8f5396f7c, sha256 365bb5272c33891dbf7b965ec379a1861f0aae08b15fec557537e055a85d44a1; kept as patch_bb10j.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces fails before 3.12). Identical output on Python 3.10-3.13. bb10j.diff is for review only.

## Fallback if raw GitHub is unreachable (bundle-b64-part-00..00)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-maint2/deploy.sh --dry-run && bash /tmp/deploy-maint2/deploy.sh
bundle.tgz sha256: a0da224bf94f1ea3a2b04e8752f1c1a2ab74905b7db2213c710253512ecade8f
