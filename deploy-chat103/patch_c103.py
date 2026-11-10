#!/usr/bin/env python3
"""Replace the chat103 block in place.

The end of the CPI block is the next line that starts a different // chat
block, so a later chat104 rename outside the CPI region is left alone.
The last-write scrub stays byte for byte. app.js and index.html are not written.
"""
import pathlib
import re
import sys

START = "// chat103 cpi day"
R6C = "// chat102r6c last-write scrub."
NEXT = re.compile(r"\n// chat(?!103\b)")


def next_chat(text, start):
    match = NEXT.search(text, start + 1)
    return -1 if match is None else match.start()


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
    if text.count("\n" + R6C) != 1:
        sys.exit("missing or repeated anchor " + R6C)
    start = text.find("\n" + START)
    end = next_chat(text, start)
    if end < 0 or end < start:
        sys.exit("no later // chat block after chat103")
    if R6C in text[start:end]:
        sys.exit("r6c sits inside the chat103 block")
    suffix = text[end:]
    new = text[: start + 1] + block + suffix
    if not new.startswith(text[: start + 1]):
        sys.exit("bytes in front of chat103 changed")
    if new[len(new) - len(suffix):] != suffix:
        sys.exit("bytes after the chat103 block changed")
    old_c = text[text.find("\n" + R6C):]
    new_c = new[new.find("\n" + R6C):]
    if old_c != new_c:
        sys.exit("chat102r6c last-write block changed")
    if new.count("proto.end = end") != text.count("proto.end = end"):
        sys.exit("a response-end wrapper was added")
    if new.count("[c102r6c] scrub attached") != 1:
        sys.exit("r6c attach log is not intact")
    region = new[start:len(new) - len(suffix)]
    if "proto.end" in region:
        sys.exit("replacement chat103 block wraps res.end")
    if "Year-on-year not published:" not in region:
        sys.exit("replacement chat103 block has no year-on-year note")
    if "Not published by BLS (no October 2025 data)" not in region:
        sys.exit("replacement chat103 block has no October 2025 label")
    server.write_text(new, encoding="utf-8")
    if at != app.read_text(encoding="utf-8") or it != index.read_text(encoding="utf-8"):
        sys.exit("app.js or index.html was touched")
    print("replaced the chat103 block; bytes outside it stayed")


if __name__ == "__main__":
    main()
