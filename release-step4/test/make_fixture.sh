#!/bin/bash
# Fixture = the live step-3 tree: step-2 fixture with the pinned release-step3 installer applied, committed.
# Prints: server md5, size, r6n backup md5.
set -e
F=${1:-/tmp/r4fix}; S3=/workspace/c111/release-step3
read SM SS RM < <(bash $S3/test/make_fixture.sh "$F" | tail -1)
cd "$F"
R3_LOCAL_PAYLOAD=$S3 R3_LOCAL_TEST=1 R3_TEST_SERVER_SIZE=$SS R3_TEST_R6N_MD5=$RM bash $S3/deploy.sh --dir "$F" > /tmp/r4fix_step3.out 2>&1
grep -q "DONE: server.js md5" /tmp/r4fix_step3.out
rm -rf .release-snapshots; git add -A; git commit -qm "live step 3"
echo "$(md5sum < server.js | cut -c1-32) $(wc -c < server.js) $RM"
