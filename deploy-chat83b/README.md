# deploy-chat83b — client-only hotfix rt62f for thedispatch.uk

Live now (chat83, required — script aborts otherwise, nothing changed): server.js 6a359cecb836848284c2264d13122482 (bb10d), app.js ef0ce14cde79cd45a9eae72e2031ece7, index.html 1d6725049d4a819e7a5d268713037bcc (v=chat83).
What it does: replaces app.js with the bundled **chat82** app.js (base-chat82-app.js.gz, md5 e45d14a361587253a328c0de1ff4c791; index base 16c4bade1ff3baf1e7d1f335402d74fa), applies patch_rt62f.py (PR #80 commit 6cbbe25b4c73988f06e3ac3fd364a030cbaca18d) in scratch, then installs app.js + index.html (v=chat83b).
**server.js is never modified or backed up** — only its md5 is verified before and after (must stay 6a359cec…). Never starts the server; never touches git/DB/.replit/package.json/env/Stripe/npm. Click Republish yourself afterwards.

## Run in the Replit Shell (from the project folder)
    curl -fsSL https://raw.githubusercontent.com/VRAJ2710/Website/deploy/jack-chat83b-rt62f/deploy-chat83b/deploy.sh -o /tmp/deploy83b.sh && echo "2c9ac7312567088bb9f422f8ac2888a0786c7d17c2f2f2be6a111eb222d86312  /tmp/deploy83b.sh" | sha256sum -c - && bash /tmp/deploy83b.sh --dry-run
    bash /tmp/deploy83b.sh

Options: --dir /path/to/project. Second run: "REFUSE: already applied", exit 0. Any md5/sha256 mismatch aborts before touching live files. Needs node, python3 (3.8+), gzip, curl.
The rt62f script prints "WARN index.html md5 16c4bade… expected prefix 30af5ae4" — harmless (anchors decide); deploy.sh verifies the real final md5.

## Expected results
| file | md5 | sha256 |
|---|---|---|
| server.js (UNCHANGED) | 6a359cecb836848284c2264d13122482 | 067ab1e873bd906670f190244db8a59dea573706e9da639f2b5a01285fabe916 |
| app.js | f63c681c5f366e2185e36dd7d4ccd23c | 9bc65b0ab48fc35ade2c96639747d83af880e5ad896f281b53b55f625206dbd3 |
| index.html | 4ef366778c09fe776757f39d083f9ae2 | a95eecc5b5356ebf061d11e1b240da762e75e455a47a35198da9fddee9e1ab10 |

index.html differs from the live chat83 index by exactly one line: app.js?v=chat83 -> app.js?v=chat83b (the patch itself sets 'chat83b').
Backups: app.js and index.html as <file>.<YYYYmmdd-HHMMSS>.bak-chat83b. Rollback = copy those two back, then Republish.

## sha256
2c9ac7312567088bb9f422f8ac2888a0786c7d17c2f2f2be6a111eb222d86312  deploy.sh
393823a97af5a33b005dc18611ee1c2f106f12b445f056e61886a6a68ca25a96  patch_rt62f.py (byte-identical to PR #80 commit 6cbbe25b)
e6cd7470dd417155c877e26e09ff58905bf57b3ad09b59e0562170b3a4ef68f0  base-chat82-app.js.gz
eb7dad16a30653695392d61396a44de96aa916dfaf3403a93829925d56a60622  base-chat82-index.html

## Fallback if raw GitHub is unreachable (parts bundle-b64-part-00..56, concatenated in order)
    cat > /tmp/b.b64 <<'EOB'      # paste the part files back to back, then EOB
    base64 -d /tmp/b.b64 | tar xz -C /tmp && bash /tmp/deploy-chat83b/deploy.sh --dry-run && bash /tmp/deploy-chat83b/deploy.sh
bundle.tgz sha256: 4ebff370dee874ec2bccf2420bfa980bd3ad925fec7cc8bf09636d6de556c3a6
