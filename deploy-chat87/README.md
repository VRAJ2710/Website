# deploy-chat87 — bb10h (server) + rt62j (app/index) for thedispatch.uk

Applies on top of live chat86 / bb10g (verified md5): server.js 9777ab9b8bebaa77f475b738995aa3d8 (bb10g), app.js 21f3cee5da20d9fc2f2f03d21623dcb4 (chat86; also confirmed from https://thedispatch.uk/app.js), index.html 35084b102b38f99b582838aa19dadfad (chat86, v=chat86).
Order: bb10h (server.js), then rt62j (app.js, index v=chat87). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat87-bb10h-rt62j/deploy-chat87/deploy.sh -o /tmp/deploy87.sh && echo "02d17f22ebea5ee9374866ea10b533643523606ccb0e22d655003ceaa43bd56b  /tmp/deploy87.sh" | sha256sum -c - && bash /tmp/deploy87.sh --dry-run
    bash /tmp/deploy87.sh

--dry-run also prints one informational line on Coinbase reachability (never aborts). Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or result) aborts before touching live files.
rt62j prints "WARN index.html md5 35084b10… expected prefix cb90c315" — harmless: it was authored against a different on-disk index; deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 9be7817db01cd10fa000c36aa57e4136 | 2a35209af13b9a7571fcfae2050cd9266267f4ceb89d8936f58b2ef1327c1d0f |
| app.js | 9205119495bff3682f86510f36a0fc7b | c98990c92fd513e80043b4a5472e17c3eef7320554ec62f3dbc8baea765500cb |
| index.html | da1fe152d351bc9d47b48b61e88f2f4e | e8a34fb7c17563d173247f512debf30be12c85a37322790340cf38a04d45ccd1 |

index.html differs from the live chat86 file by exactly one line: app.js?v=chat86 -> app.js?v=chat87. (The patch's own expected index prefix cb90c315… is from a different copy; the value above is the real result on the verified chat86 index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat87. Rollback = copy the three backups back, then Republish.
After Republish: `curl -s https://thedispatch.uk/app.js | md5sum` -> 9205119495bff3682f86510f36a0fc7b ; `curl -s https://thedispatch.uk/ | grep -o 'app.js?v=[a-z0-9]*'` -> app.js?v=chat87.

## sha256
02d17f22ebea5ee9374866ea10b533643523606ccb0e22d655003ceaa43bd56b  deploy.sh
837532477b6c035348490570a4f18faa309d0bb5505a6474671fdb9624b687b0  patch_bb10h.py
940abbd7281e8117673e9dbc6385e39771bbadb7c3b37afe53d7375f817b0b30  patch_rt62j.py (PR #84 commit 74b7d2d4154af5ff1e8003a989f9e5d837ad3e8f, byte-identical)

patch_bb10h.py = /workspace/bb10h/patch_bb10h.py (md5 45b6b41d4151a03a29521b4128e9a85e, sha256 afc1ed7212bd07b6495c32001baba0f3da9345e4e87b288ff82c3df8a7643560; kept as patch_bb10h.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12; the original fails on 3.10). Identical output on Python 3.10-3.13. bb10h.diff is for review only.

## Fallback if raw GitHub is unreachable (parts bundle-b64-part-00..01)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat87/deploy.sh --dry-run && bash /tmp/deploy-chat87/deploy.sh
bundle.tgz sha256: 6496650bd04b0b405a33b5b34110387329d1362e00274a92d678e41e248a0c67
