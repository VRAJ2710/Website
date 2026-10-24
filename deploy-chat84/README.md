# deploy-chat84 — bb10e (server) + rt62g (app/index) for thedispatch.uk

Applies on top of live chat83b / bb10d (verified md5): server.js 6a359cecb836848284c2264d13122482 (bb10d), app.js f63c681c5f366e2185e36dd7d4ccd23c (chat83b; also confirmed from https://thedispatch.uk/app.js), index.html 4ef366778c09fe776757f39d083f9ae2 (chat83b, v=chat83b).
Order: bb10e (server.js), then rt62g (app.js, index v=chat84). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat84-bb10e-rt62g/deploy-chat84/deploy.sh -o /tmp/deploy84.sh && echo "40b3e4a23615a3fa09be2e3cb4dcdbde9f91c97975edfa1683fa0060e3572800  /tmp/deploy84.sh" | sha256sum -c - && bash /tmp/deploy84.sh --dry-run
    bash /tmp/deploy84.sh

--dry-run also prints one informational line on Coinbase reachability (never aborts). Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch (live base, patch file or result) aborts before touching live files.
rt62g prints "WARN index.html md5 4ef36677… expected prefix e88590c7" — harmless: it was authored against a different on-disk index; deploy.sh verifies the real final index md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 6b4612281efc32ada0cabf38fa808ccb | 1a42d427019469a853d4704c2bcec22d3b760f433a5767d4e3200944ecca2530 |
| app.js | 293c103a4efdd0fddaffc114bc3870ee | 24c1a308d448935a061f9a2f7378532f78d31f6bc0edadfdc57572b6ccc27433 |
| index.html | abd27d2e409eeef2dc8cf866927bc584 | c8ff211628c83de21668a593623a50a068c3cb8b59458530cb5726c0bee3eb38 |

index.html differs from the live chat83b file by exactly one line: app.js?v=chat83b -> app.js?v=chat84. (The requested index md5 76207426… came from a different on-disk copy; the value above is the real result on the verified chat83b index.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat84. Rollback = copy the three backups back, then Republish.
After Republish: `curl -s https://thedispatch.uk/app.js | md5sum` -> 293c103a4efdd0fddaffc114bc3870ee ; `curl -s https://thedispatch.uk/ | grep -o 'app.js?v=[a-z0-9]*'` -> app.js?v=chat84.

## sha256
40b3e4a23615a3fa09be2e3cb4dcdbde9f91c97975edfa1683fa0060e3572800  deploy.sh
957e4b26e8d209df4f1268011eb4c5572a5c02e818b7a58bc185b7dc12fd9d03  patch_bb10e.py
34b15d60f6906d9e3aff2c8f972dbb103502357c7450898ea160aae087c7aaa8  patch_rt62g.py (PR #81 commit 40cd95db7f989788cd2d491638ea900681112034, byte-identical)

patch_bb10e.py = /workspace/bb10e/patch_bb10e.py (md5 7148816d04dd79adb8abafb4215e4d6f, sha256 9e692244e54bf051691693d5d7bd1503440c42231f3866fad84c918f35cc9097; kept as patch_bb10e.orig.py) plus a 3-line Python<3.12 portability fix (b'\n' inside f-string braces is a SyntaxError before 3.12; original fails on 3.10). Identical output on Python 3.10-3.13. bb10e.diff is for review only.

## Fallback if raw GitHub is unreachable (parts bundle-b64-part-00..01)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat84/deploy.sh --dry-run && bash /tmp/deploy-chat84/deploy.sh
bundle.tgz sha256: 096e7ac637fabe83de9bab57b1301642e77a0eb5578f3ec5dc6a9786e3c4b840
