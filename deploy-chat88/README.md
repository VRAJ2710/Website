# deploy-chat88 — consolidated: server bb12b + client rt62j + rt63 (Capital Sustainability Monitor) + cache token chat88

Applies on top of live: server.js 92a2ce51dfc1bf3e16466d7451d9ae1a (maint2/bb10j), app.js 21f3cee5da20d9fc2f2f03d21623dcb4 (chat86), index.html 35084b102b38f99b582838aa19dadfad (v=chat86).
Order: bb12b (server.js, keeps BB10I_MAINTENANCE_ON = true on line 1) → rt62j (app.js, index token chat87) → rt63 (app.js; token already chat87 so unchanged) → bump_chat88.py (index token chat87 → chat88, bytes-exact, idempotent). Never starts the server, never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat88-monitor/deploy-chat88/deploy.sh -o /tmp/deploy88.sh && echo "ea8c1fcf0fae32a3e58caca8e34564b52161d2dd4ec032d094bff13ac33f6f30  /tmp/deploy88.sh" | sha256sum -c - && bash /tmp/deploy88.sh --dry-run
    bash /tmp/deploy88.sh

--dry-run also prints one informational Coinbase reachability line. Option: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any base md5 / patch sha256 / result mismatch aborts before touching live files. rt62j / rt63 print harmless WARNs about index/app md5 prefixes (authored against other copies); deploy.sh verifies the real final md5/sha256.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 5d4cb84f987f2e189d0a298e6f44025c | ebdca89cd2a3b5f5328526a1308125499d80ba0ab74b62de3d06f5d642638662 |
| app.js | dfd17c656fe880907efb073be5e03a3c | 522bcbb18f5bd3faa9126a4a252cb903d24d52e0bce86fa36f7af17c81458e71 |
| index.html | 66b40f0face11c13288c3e83f6ee86ec | fd4309b9dfbdc1a7ce58b9aeee022beb5d2f6880406735d7b5b5e9daa5919fab |

index.html differs from live by exactly one line: app.js?v=chat86 → app.js?v=chat88. (Note: stacking rt62j+rt63 gives a different app.js md5 from the chat87 bundle's 9205119… because rt63 is added.)
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat88. Rollback = copy the three backups back, then Republish.

## sha256
ea8c1fcf0fae32a3e58caca8e34564b52161d2dd4ec032d094bff13ac33f6f30  deploy.sh
b92d237c261e6faa7ad5c8f87d76192a3dd15adf9c4c442128c47cbcf030c300  patch_bb12b.py  (original kept as patch_bb12b.orig.py, sha256 0b4d88e3ec1b0dea19c47805679d30a60dbb10d5e583728c914646b98c362af3, md5 98964d78761eeba12d4d7c101dc45b0b; + 3-line Python<3.12 f-string portability fix; same output on 3.10–3.13)
940abbd7281e8117673e9dbc6385e39771bbadb7c3b37afe53d7375f817b0b30  patch_rt62j.py (PR #84, byte-identical)
99c78d25d161701cb9336def2a77b41b2b10f2336ed2f53af07624d2391e5603  patch_rt63.py (PR #85 commit bb79977196f80a499f2f89671904a31e9c42cecd, byte-identical)
0de1163d41448fdfca0716f008e211319c827c862d20da80d4fe0a556b079d39  bump_chat88.py
bb12b.diff / rt63.diff are for review only.

## Fallback if raw GitHub is unreachable (bundle-b64-part-00..06)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat88/deploy.sh --dry-run && bash /tmp/deploy-chat88/deploy.sh
bundle.tgz sha256: 172454a36a29ba74b3abc10788f9f9ef4271b4d66e8f0618e210da2d6c428a14
