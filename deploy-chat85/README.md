# deploy-chat85 — bb10f (server) + rt62h (app/index) for thedispatch.uk

Applies on top of live chat84 / bb10e (verified md5): server.js 6b4612281efc32ada0cabf38fa808ccb (bb10e), app.js 293c103a4efdd0fddaffc114bc3870ee (chat84; also confirmed from https://thedispatch.uk/app.js), index.html abd27d2e409eeef2dc8cf866927bc584 (chat84, v=chat84).
Order: bb10f (server.js), then rt62h (app.js, index v=chat85). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat85-bb10f-rt62h/deploy-chat85/deploy.sh -o /tmp/deploy85.sh && echo "522de77d68ed52193f7eb3c1902428ae2f2e4c085f21652403529a1d696a21c7  /tmp/deploy85.sh" | sha256sum -c - && bash /tmp/deploy85.sh --dry-run
    bash /tmp/deploy85.sh

--dry-run also prints one informational line on Coinbase reachability (never aborts). Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or result) aborts before touching live files.
rt62h prints "WARN index.html md5 abd27d2e… expected prefix 76207426" — harmless: it was authored against a different on-disk index; deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 3cd6dbab111d7c298d5a1d54292a034c | e77e3bdae4505cde97d3d7411c965e585d0581ab257ead561834b4920c49a505 |
| app.js | a88ca4b4e780faaddd756700375445b9 | 2b46b1484298341a545c53c88612d7e402a3efe94cf7f9e901e47537a645e777 |
| index.html | f27a947bb4efc28f3fb6dc24d96aa50a | e6a988986a9af2d6ce93fa55519c78dfeb0670283ff6f3f59846f0b25005c06a |

index.html differs from the live chat84 file by exactly one line: app.js?v=chat84 -> app.js?v=chat85. (Frontend quoted 696df415…, from a different copy; the value above is the real result on the verified chat84 index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat85. Rollback = copy the three backups back, then Republish.
After Republish: `curl -s https://thedispatch.uk/app.js | md5sum` -> a88ca4b4e780faaddd756700375445b9 ; `curl -s https://thedispatch.uk/ | grep -o 'app.js?v=[a-z0-9]*'` -> app.js?v=chat85.

## sha256
522de77d68ed52193f7eb3c1902428ae2f2e4c085f21652403529a1d696a21c7  deploy.sh
cd172dc523c6658b96363de74e94a2b611d3eab07a3dda42828dec0bddb69de8  patch_bb10f.py
66d0041646f9336de7c688b83ddcfb05c0c65b9573f66ecac985e0a55a265890  patch_rt62h.py (PR #82 commit 12cd39e6f16bed775145879a888ca783f1e4e011, byte-identical)

patch_bb10f.py = /workspace/bb10f/patch_bb10f.py (md5 a5692217e6f8cc70cfefdf819f43ce7e, sha256 a6d2694f4dbcbfd616790c23da79671c5ec8741aa86ae537808220cc8a88c123; kept as patch_bb10f.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12). Identical output on Python 3.10-3.13. bb10f.diff is for review only.

## Fallback if raw GitHub is unreachable (parts bundle-b64-part-00..01)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat85/deploy.sh --dry-run && bash /tmp/deploy-chat85/deploy.sh
bundle.tgz sha256: 28d6b772f7be18a5cf725b27c0ba71c96202f4d95675fc9308a748d2adb63b89
