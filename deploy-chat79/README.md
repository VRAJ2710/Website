# deploy-chat79 — bb10 (server) + rt62 (app/index) for thedispatch.uk

Applies on top of the live files (verified md5): server.js d595fee7031ef3458b20fea7efbdb378 (bb9a), app.js cb0ca833c4f4dcc9daa579b603d92e85 (chat78; also confirmed from https://thedispatch.uk/app.js?v=chat78), index.html 8a73c6ac030361010ecd11c9430627c4 (chat78).
Never starts the server, never touches git/DB/.replit/package.json/env/Stripe. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat79-bb10-rt62/deploy-chat79/deploy.sh -o /tmp/deploy79.sh && echo "d3cf0f5d4baa76ba209b06a3d3c7a942ff2e22c8cc700b37a4fbecc96d38250a  /tmp/deploy79.sh" | sha256sum -c - && bash /tmp/deploy79.sh --dry-run
    bash /tmp/deploy79.sh

--dry-run also prints one informational line: whether Coinbase https://api.exchange.coinbase.com/products/BTC-USD/stats is REACHABLE from Replit (10 s timeout; never aborts; bb10 falls back to a labelled previous-close basis if unreachable).
Options: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch aborts before touching live files.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js | 56ebb9729fc8866d1be6488f244f550e | fce77985430956e5eaf7c090537c21d678e7fc79a6352a8d66f7df6f81671f92 (21564 lines) |
| app.js | d16d919877becccafd142f86bda132a2 | 64a8ec47d719ce91a032ab21a33685b51a17c7ed50ac1b4d2abbb75159f2a07a |
| index.html | c4cc3fe04d896fa0d6b1c05c5839b0e8 | fcafbd5422fc2772586cc3886947a9c622ad7be7bd114e31791e93133f649071 |

index.html differs from the chat78 file by exactly one line: app.js?v=chat78 -> app.js?v=chat79.
Backups: <file>.<YYYYmmdd-HHMMSS>.bak-chat79 next to each file. Rollback = copy the three backups back, then Republish.

## Patch file sha256
d3cf0f5d4baa76ba209b06a3d3c7a942ff2e22c8cc700b37a4fbecc96d38250a  deploy.sh
dde37896cb0c0712f2385f01555c3119c7497e094f0cd019a0e2b8226bbb226f  patch_bb10.py
bc46597b92b0c41b6444e61710916cad896332a31a11d888a2bc44808edced4c  patch_rt62.py
36d92624453cdc13a584b131ecf9a56f7757deebd413705d64425d449266f747  rt62_fe79.js
234ae43f850e9407e4b92e9fa0a7dee35a6e045bf044d2c6640d873545536b2b  rt62_fe79_test.js

patch_rt62.py, rt62_fe79.js, rt62_fe79_test.js are byte-identical to PR #75 head ac1cb8a1d6331d95eea6123903a505d4010dd1d7 (deploy/).
patch_bb10.py = /workspace/bb10/patch_bb10.py (sha256 553e51061f37d03f8f8b1a0e263aefa2f968a26c0edf294c5125f0c435a1a642) plus the same 3-line Python<3.12 portability fix as in chat78 (b'\n' inside f-string braces is a SyntaxError before 3.12); outputs identical on Python 3.10/3.11/3.13.
