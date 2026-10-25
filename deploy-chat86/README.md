# deploy-chat86 — bb10g (server) + rt62i (app/index) for thedispatch.uk

Applies on top of live chat85 / bb10f (verified md5): server.js 3cd6dbab111d7c298d5a1d54292a034c (bb10f), app.js a88ca4b4e780faaddd756700375445b9 (chat85; also confirmed from https://thedispatch.uk/app.js), index.html f27a947bb4efc28f3fb6dc24d96aa50a (chat85, v=chat85).
Order: bb10g (server.js), then rt62i (app.js, index v=chat86). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat86-bb10g-rt62i/deploy-chat86/deploy.sh -o /tmp/deploy86.sh && echo "51e29f3a80d78d1713a12677532a54899abec6405cef0a9d39d488a4914ffba9  /tmp/deploy86.sh" | sha256sum -c - && bash /tmp/deploy86.sh --dry-run
    bash /tmp/deploy86.sh

--dry-run also prints one informational line on Coinbase reachability (never aborts). Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or result) aborts before touching live files.
rt62i prints "WARN index.html md5 f27a947b… expected prefix 696df415" — harmless: it was authored against a different on-disk index; deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 9777ab9b8bebaa77f475b738995aa3d8 | feb4f4d497795049cd91d0141cadaeb56843da60e3f0e3ca46c4f205e0bb8b24 |
| app.js | 21f3cee5da20d9fc2f2f03d21623dcb4 | aca0bf0b4f7447d92b6a3fbc592805de06cf5b381cafc1972a8eb748c2e9f12a |
| index.html | 35084b102b38f99b582838aa19dadfad | 5405b9a63e0cafd8c3468031b40a642808f62bed1b9ea672fd67904ac4002a53 |

index.html differs from the live chat85 file by exactly one line: app.js?v=chat85 -> app.js?v=chat86. (Frontend quoted cb90c315…, from a different copy; the value above is the real result on the verified chat85 index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat86. Rollback = copy the three backups back, then Republish.
After Republish: `curl -s https://thedispatch.uk/app.js | md5sum` -> 21f3cee5da20d9fc2f2f03d21623dcb4 ; `curl -s https://thedispatch.uk/ | grep -o 'app.js?v=[a-z0-9]*'` -> app.js?v=chat86.

## sha256
51e29f3a80d78d1713a12677532a54899abec6405cef0a9d39d488a4914ffba9  deploy.sh
821b7638b2fa2d66e098cc4ace48b52fd507a95bf8abd17c35ba5a53e1a9f6cd  patch_bb10g.py
930ab297c3dd79585cd546bb370e18dd5b618633282668cbd7b9af08ea8c51c5  patch_rt62i.py (PR #83 commit 69d0d6e6c944aaf467a0c068a4c5ec88e56e87f1, byte-identical)

patch_bb10g.py = /workspace/bb10g/patch_bb10g.py (md5 c530ba53422429bfc35c997a68105886, sha256 5e0da673035aeeaa1ec3a6682dace53070e14b293460196fa9a254d4e055026d; kept as patch_bb10g.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12; the original fails on 3.10). Identical output on Python 3.10-3.13. bb10g.diff is for review only.

## Fallback if raw GitHub is unreachable (parts bundle-b64-part-00..01)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat86/deploy.sh --dry-run && bash /tmp/deploy-chat86/deploy.sh
bundle.tgz sha256: c103b063bb145af43638f2a7235a00b3a1aa47c042a7159bb4c3877571603e44
