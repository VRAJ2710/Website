#!/usr/bin/env python3
# chat107credits patch: append the credits block after the r6p last-write scrub. Every existing byte is kept.
# Args: server.js block.js r6p_block.js v3h2_block.js expected_bytes
import hashlib, sys
server, block, r6p, v3h2, want = sys.argv[1:6]
d = open(server, "rb").read()
b = open(block, "rb").read()
r = open(r6p, "rb").read()
v = open(v3h2, "rb").read().rstrip(b"\n") + b"\n"
def die(m):
    print("[patch-chat107credits] REFUSE: " + m); sys.exit(1)
if len(d) != int(want): die("server.js is %d bytes, expected %s (post-softgate)" % (len(d), want))
if not d.endswith(r): die("server.js does not end with the r6p scrub block byte-exact")
if d.count(v) != 1: die("the chat105v3home2 block is not present exactly once")
if not d.endswith(v + r): die("chat105v3home2 block is not immediately before the r6p scrub")
for m, n in ((b"[chat106softgate] attached", 1), (b"const VERIFY_ENFORCE = false;", 1), (b"[c102r6p] scrub attached", 1), (b"[c102r6o] scrub attached", 0), (b"[chat107credits]", 0)):
    if d.count(m) != n: die("%r occurs %d times, expected %d" % (m, d.count(m), n))
if b.count(b'console.log("[" + TAG + "] attached")') != 1 or b.count(b'var TAG = "chat107credits";') != 1: die("block attach line missing")
sep = b"" if d.endswith(b"\n") else b"\n"
out = d + sep + b
if out[: len(d)] != d: die("prefix changed")
open(server, "wb").write(out)
print("[patch-chat107credits] appended %d bytes; prefix %d bytes unchanged; sha256 of old file %s" % (len(out) - len(d), len(d), hashlib.sha256(d).hexdigest()))
