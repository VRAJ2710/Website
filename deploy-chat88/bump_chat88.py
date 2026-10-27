#!/usr/bin/env python3
"""chat88 cache-token bump: index.html app.js?v=chat87 -> app.js?v=chat88. Bytes-exact (CRLF/LF preserved).
Usage: bump_chat88.py <index.html>   Second run prints REFUSE and exits 0."""
import sys
OLD = b'app.js?v=chat87"'
NEW = b'app.js?v=chat88"'
def main():
    if len(sys.argv) != 2: print("usage: bump_chat88.py index.html"); return 2
    p = sys.argv[1]
    raw = open(p, "rb").read()
    if raw.count(NEW) == 1 and raw.count(OLD) == 0 and b"app.js?v=chat87" not in raw:
        print("REFUSE: chat88 token already set"); return 0
    if raw.count(OLD) != 1 or raw.count(b"app.js?v=chat88") != 0:
        print("ABORT: expected exactly one app.js?v=chat87 token and no chat88 token"); return 1
    out = raw.replace(OLD, NEW, 1)
    tmp = p + ".tmp88"; open(tmp, "wb").write(out)
    import os; os.replace(tmp, p)
    print("bump_chat88: index token chat87 -> chat88"); return 0
sys.exit(main())
