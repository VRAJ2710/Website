#!/usr/bin/env python3
"""Append chat103 onto a chat102r4 server.js, app.js and index.html. The chat102 tail stays byte-for-byte."""
import pathlib
import sys

GUARD_OLD = 'if (c102Path === "/terminal" || c102Path === "/terminal/") return;'
GUARD_NEW = 'if (c102Path === "/terminal" || c102Path === "/terminal/" || c102Path === "/cpi" || c102Path === "/cpi/") return;'
INDEX_OLD = '/app.js?v=chat102"'
INDEX_NEW = '/app.js?v=chat103"'


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c103.py server.js app.js index.html server_block app_block")
    server, app, index, sblock, ablock = [pathlib.Path(p) for p in sys.argv[1:6]]
    sb = sblock.read_text(encoding="utf-8")
    ab = ablock.read_text(encoding="utf-8")
    if "chat103 cpi day" not in sb:
        sys.exit("server block is missing its marker")
    st = server.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if "chat103 cpi day" in st or "/api/c103/cpi" in st:
        sys.exit("server.js already contains chat103")
    if GUARD_OLD not in at:
        sys.exit("app.js is missing the chat102 terminal path guard")
    if at.count(GUARD_OLD) != 1:
        sys.exit("chat102 terminal path guard is not unique")
    if 'c102Path === "/cpi"' in at:
        sys.exit("app.js already contains the chat103 path guard")
    if it.count(INDEX_OLD) != 1:
        sys.exit("index.html does not contain exactly one chat102 app cache token")
    server.write_text(st.rstrip("\n") + "\n" + sb.strip("\n") + "\n", encoding="utf-8")
    app.write_text(at.replace(GUARD_OLD, GUARD_NEW, 1).rstrip("\n") + "\n" + ab.strip("\n") + "\n", encoding="utf-8")
    index.write_text(it.replace(INDEX_OLD, INDEX_NEW, 1), encoding="utf-8")
    print("patched")


if __name__ == "__main__":
    main()
