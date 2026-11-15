#!/usr/bin/env python3
"""Swap the chat105v3home block for the chat105v3home2 block. Nothing else changes.
Checks: the old block is present exactly once and ends exactly at the single last-write scrub marker;
the bytes before it are the fef1da0 prefix; the bytes from the marker to EOF are the r6o scrub block."""
import hashlib, pathlib, sys
server, old_p, new_p, pre_sha, pre_len, suf_sha, suf_len = sys.argv[1:8]
MARKER = b"// chat102r6c last-write scrub."
data = pathlib.Path(server).read_bytes()
old = pathlib.Path(old_p).read_bytes().rstrip(b"\n") + b"\n"
new = pathlib.Path(new_p).read_bytes().rstrip(b"\n") + b"\n"
if b"[chat105v3home2] preview attached" in data: sys.exit("chat105v3home2 already present")
if data.count(MARKER) != 1: sys.exit("expected exactly one scrub marker")
if data.count(old) != 1: sys.exit("the chat105v3home block is not present exactly once (byte-exact)")
if data.count(b"[chat105v3home] preview attached") != 1: sys.exit("expected exactly one chat105v3home attach line")
s = data.index(old); m = data.index(MARKER)
if s + len(old) != m: sys.exit("the chat105v3home block does not end at the scrub marker")
pre, suf = data[:s], data[m:]
ps, ss = hashlib.sha256(pre).hexdigest(), hashlib.sha256(suf).hexdigest()
if ps != pre_sha or str(len(pre)) != pre_len: sys.exit("prefix %s/%d is not the fef1da0 prefix %s/%s" % (ps, len(pre), pre_sha, pre_len))
if ss != suf_sha or str(len(suf)) != suf_len: sys.exit("scrub block %s/%d is not %s/%s" % (ss, len(suf), suf_sha, suf_len))
if new.count(b"[chat105v3home2] preview attached") != 1 or b"[chat105v3home] preview attached" in new: sys.exit("new block attach line check failed")
pathlib.Path(server).write_bytes(pre + new + suf)
print("prefix sha256", ps, "bytes", len(pre))
print("scrub block sha256", ss, "bytes", len(suf))
print("old block sha256", hashlib.sha256(old).hexdigest(), "bytes", len(old))
print("new block sha256", hashlib.sha256(new).hexdigest(), "bytes", len(new))
