#!/usr/bin/env python3
# chat108saferxB patch: append the batch-B preview block after the chat108saferxA block. Every existing byte is kept.
# Args: server.js block.js a_block.js expected_bytes
import hashlib, sys
server, block, ablk, want = sys.argv[1:5]
d = open(server, "rb").read()
b = open(block, "rb").read()
a = open(ablk, "rb").read()
def die(m):
    print("[patch-chat108saferxB] REFUSE: " + m); sys.exit(1)
if len(d) != int(want): die("server.js is %d bytes, expected %s (post-chat108saferxA)" % (len(d), want))
if not d.endswith(a): die("server.js does not end with the chat108saferxA block byte-exact")
if d.count(a) != 1: die("the chat108saferxA block is not present exactly once")
for m, n in ((b"[chat106softgate] attached", 1), (b"const VERIFY_ENFORCE = false;", 1), (b"[c102r6p] scrub attached", 1),
             (b"[c102r6o] scrub attached", 0), (b'var TAG = "chat107credits";', 1), (b"[chat105v3home2] preview attached", 1),
             (b'var TAG = "chat108saferxA";', 1), (b"chat108saferxB", 0)):
    if d.count(m) != n: die("%r occurs %d times, expected %d" % (m, d.count(m), n))
if b.count(b'var TAG = "chat108saferxB";') != 1: die("block TAG line missing")
if b.count(b"[chat108saferxB] preview attached") != 0: die("attach text must be built at runtime")
for bad in (b"process.env", b"require(\"fs\")", b"require('fs')", b"child_process", b"stripe", b"Stripe", b"ALTER TABLE", b"alter table", b"CREATE TABLE", b"fetch(", b"localStorage", b"XMLHttpRequest"):
    if bad in b: die("block mentions %r" % bad)
sep = b"" if d.endswith(b"\n") else b"\n"
out = d + sep + b
if out[: len(d)] != d: die("prefix changed")
open(server, "wb").write(out)
print("[patch-chat108saferxB] appended %d bytes; prefix %d bytes unchanged; sha256 of old file %s" % (len(out) - len(d), len(d), hashlib.sha256(d).hexdigest()))
