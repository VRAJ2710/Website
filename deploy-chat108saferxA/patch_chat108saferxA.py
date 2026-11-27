#!/usr/bin/env python3
# chat108saferxA patch: append the batch-A preview block after the chat107credits block. Every existing byte is kept.
# Args: server.js block.js credits_block.js v3h2_block.js expected_bytes
import hashlib, sys
server, block, cred, v3h2, want = sys.argv[1:6]
d = open(server, "rb").read()
b = open(block, "rb").read()
c = open(cred, "rb").read()
v = open(v3h2, "rb").read().rstrip(b"\n") + b"\n"
def die(m):
    print("[patch-chat108saferxA] REFUSE: " + m); sys.exit(1)
if len(d) != int(want): die("server.js is %d bytes, expected %s (post-chat107credits)" % (len(d), want))
if not d.endswith(c): die("server.js does not end with the chat107credits block byte-exact")
if d.count(v) != 1: die("the chat105v3home2 block is not present exactly once")
for m, n in ((b"[chat106softgate] attached", 1), (b"const VERIFY_ENFORCE = false;", 1), (b"[c102r6p] scrub attached", 1),
             (b"[c102r6o] scrub attached", 0), (b'var TAG = "chat107credits";', 1), (b"[chat105v3home2] preview attached", 1), (b"chat108saferxA", 0)):
    if d.count(m) != n: die("%r occurs %d times, expected %d" % (m, d.count(m), n))
if b.count(b'var TAG = "chat108saferxA";') != 1: die("block TAG line missing")
if b.count(b"[chat108saferxA] preview attached") != 0: die("attach text must be built at runtime")
for bad in (b"process.env", b"require(\"fs\")", b"require('fs')", b"child_process", b"stripe", b"Stripe", b"ALTER TABLE", b"alter table", b"CREATE TABLE", b"fetch("):
    if bad in b: die("block mentions %r" % bad)
sep = b"" if d.endswith(b"\n") else b"\n"
out = d + sep + b
if out[: len(d)] != d: die("prefix changed")
open(server, "wb").write(out)
print("[patch-chat108saferxA] appended %d bytes; prefix %d bytes unchanged; sha256 of old file %s" % (len(out) - len(d), len(d), hashlib.sha256(d).hexdigest()))
