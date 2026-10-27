# deploy-chat89 — server bb12d + client rt63b (+ cache token chat89)

Applies on top of live chat88: server.js 5d4cb84f987f2e189d0a298e6f44025c, app.js dfd17c656fe880907efb073be5e03a3c, index.html 66b40f0face11c13288c3e83f6ee86ec (v=chat88).
Order: bb12d (server.js; line 1 BB10I_MAINTENANCE_ON stays true) → rt63b (app.js; also bumps index token app.js?v=chat88 → chat89, one line, idempotent). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat89-fixes/deploy-chat89/deploy.sh -o /tmp/deploy89.sh && echo "35d2c61ea4806a37bdafccd5cc4e464822f96814b3a20115d0b4f76a04edbf7c  /tmp/deploy89.sh" | sha256sum -c - && bash /tmp/deploy89.sh --dry-run
    bash /tmp/deploy89.sh

--dry-run also prints one informational Coinbase reachability line. Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any base md5 / patch sha256 / result mismatch aborts before touching live files; a partially applied state also aborts.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 03fd66ca2c1ddac8417fcb0ed8e37414 | 6a263dd862b0fd46571845ffe825aaef83cf473d06385f94a9919175af6d34ab |
| app.js | d45e0c8d6cb77fceb437ca9db6dfa73c | a3417ca669cfe39f9ed83c6875b908f04f7e761dfce6e0d6ed8d4ea8a2dc3135 |
| index.html | 8987d0ba0999841844da72d9381ad2f0 | 9047572eb7f0b2557f75066083e98c4d3668ba0f1ef8d4bf9b937f6a7cd1ea56 |

index.html differs from live by exactly one line: app.js?v=chat88 → app.js?v=chat89.
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat89. Rollback = copy the three backups back, then Republish.

## sha256
35d2c61ea4806a37bdafccd5cc4e464822f96814b3a20115d0b4f76a04edbf7c  deploy.sh
13aa9f6a51f775f77d10345f1ef6e8ff6898056d08f54458c9d4c90d63e56779  patch_bb12d.py  (original kept as patch_bb12d.orig.py, sha256 84f81a4d14e39a2691eeeabfc0bb84df97638e1f3d935557671cbdb903ea8028, md5 c5a942d68ef5fa9eeafbb7bfe95f9899; + 3-line Python<3.12 f-string portability fix; same output on 3.10–3.13)
52b1340b2278a70843b51c84556e6c9065fc5a9ea5079f29bb1be39964873a58  patch_rt63b.py (byte-identical to /workspace/rt63b; already runs on 3.10)
bb12d.diff / rt63b.diff are for review only.

## Fallback if raw GitHub is unreachable (bundle-b64-part-00..00)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat89/deploy.sh --dry-run && bash /tmp/deploy-chat89/deploy.sh
bundle.tgz sha256: 4e0a34db487f4320ed2480b78dff087ebe2b3d255ce529dc7c52093593f1c301
