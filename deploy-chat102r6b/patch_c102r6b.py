#!/usr/bin/env python3
"""Append the chat102r6b reader-facing scrub onto a chat102r6 server.js. Does not write app.js or index.html."""
import pathlib
import sys

MARKER = "// chat102r6b reader-facing scrub."


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: patch_c102r6b.py server.js server_block_c102r6b.js")
    server, block = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    extra = block.read_text(encoding="utf-8").strip("\n") + "\n"
    if MARKER not in extra:
        sys.exit("server block is missing its marker")
    if text.count(MARKER) > 0:
        sys.exit("already chat102r6b")
    if "chat102r6 market-reference cache" not in text:
        sys.exit("server.js is not the chat102r6 build")
    banned = ("create " + "table", "drop " + "table", "alter " + "table")
    low = extra.lower()
    if any(piece in low for piece in banned):
        sys.exit("server block mentions DDL")
    server.write_text(text.rstrip("\n") + "\n" + extra, encoding="utf-8")
    print("appended chat102r6b")


if __name__ == "__main__":
    main()
