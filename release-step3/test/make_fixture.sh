#!/bin/bash
# Fixture = the live step-2 tree: step-2 fixture (stub prefix + REAL r6n scrub as the r6n backup; v3 blocks) with the pinned
# release-step2 installer applied (r6n scrub -> r6p), committed. Prints: server md5, size, r6n backup md5.
set -e
F=${1:-/tmp/r3fix}; S2=/workspace/c111/release-step2
read SM SS RM < <(bash $S2/test/make_fixture.sh "$F" | tail -1)
cd "$F"
R2_LOCAL_PAYLOAD=$S2 R2_LOCAL_TEST=1 R2_TEST_SERVER_MD5=$SM R2_TEST_SERVER_SIZE=$SS R2_TEST_R6N_MD5=$RM bash $S2/deploy.sh --dir "$F" > /tmp/r3fix_step2.out 2>&1
grep -q "DONE: server.js md5" /tmp/r3fix_step2.out
rm -rf .release-snapshots; git add -A; git commit -qm "live step 2"
echo "$(md5sum < server.js | cut -c1-32) $(wc -c < server.js) $RM"
