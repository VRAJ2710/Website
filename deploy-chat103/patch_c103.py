#!/usr/bin/env python3
"""Replace the chat103 block in place. Everything from chat102r6 onward, including the r6c last-write scrub, stays byte for byte."""
import pathlib
import sys

START = "// chat103 cpi day"
R6 = "// chat102r6 market-reference cache."
R6B = "// chat102r6b reader-facing scrub."
R6C = "// chat102r6c last-write scrub."
TAG = "app.js?v=chat103c"


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: patch_c103.py server.js app.js index.html server_block")
    server, app, index, sblock = [pathlib.Path(p) for p in sys.argv[1:5]]
    block = sblock.read_text(encoding="utf-8").strip("\n")
    text = server.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if START not in block:
        sys.exit("server block is missing its marker")
    if "proto.end" in block:
        sys.exit("server block wraps res.end; that would sit after the r6c scrub")
    if text.count("\n" + START) != 1:
        sys.exit("chat103 block is missing or not unique")
    for mark in (R6, R6B, R6C):
        if text.count("\n" + mark) != 1:
            sys.exit("missing or repeated anchor " + mark)
    start = text.find("\n" + START)
    end = text.find("\n" + R6)
    if end < start:
        sys.exit("chat102r6 is not after the chat103 block")
    if R6C in text[start:end]:
        sys.exit("r6c sits inside the chat103 block")
    suffix = text[end:]
    if it.count(TAG) != 1:
        sys.exit("index.html does not contain exactly one chat103c cache tag")
    if "app.js?v=chat103d" in it or "app.js?v=chat103b" in it:
        sys.exit("index.html cache tag is not chat103c")
    new = text[: start + 1] + block + suffix
    if new[new.find("\n" + R6):] != suffix:
        sys.exit("bytes from chat102r6 onward changed")
    old_c = text[text.find("\n" + R6C):]
    new_c = new[new.find("\n" + R6C):]
    if old_c != new_c:
        sys.exit("chat102r6c last-write block changed")
    if new.count("proto.end = end") != text.count("proto.end = end"):
        sys.exit("a response-end wrapper was added")
    if new.count("[c102r6c] scrub attached") != 1:
        sys.exit("r6c attach log is not intact")
    if "Year-on-year not published:" not in new[start:new.find("\n" + R6)]:
        sys.exit("replacement chat103 block has no year-on-year note")
    server.write_text(new, encoding="utf-8")
    # app.js is unchanged, so the chat103c cache tag stays.
    if at != app.read_text(encoding="utf-8") or it != index.read_text(encoding="utf-8"):
        sys.exit("app.js or index.html was touched")
    print("replaced the chat103 block; chat102r6c stayed last")


if __name__ == "__main__":
    main()
