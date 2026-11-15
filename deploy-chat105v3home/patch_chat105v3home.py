#!/usr/bin/env python3
"""Insert the chat105v3home preview block immediately before the single last-write scrub marker.
Every byte before the marker and every byte from the marker to EOF stays identical."""
import pathlib, sys
server, block_path = sys.argv[1], sys.argv[2]
MARKER = "// chat102r6c last-write scrub."
ATTACH = "[chat105v3home] preview attached"
text = pathlib.Path(server).read_text(encoding="utf-8")
block = pathlib.Path(block_path).read_text(encoding="utf-8")
if ATTACH in text:
    sys.exit("chat105v3home already present")
if text.count(MARKER) != 1:
    sys.exit("expected exactly one last-write scrub marker, found %d" % text.count(MARKER))
if block.count(ATTACH) != 1:
    sys.exit("payload block must contain exactly one attach log line")
i = text.index(MARKER)
if i > 0 and text[i - 1] != "\n":
    sys.exit("marker is not at the start of a line")
new = text[:i] + block.rstrip("\n") + "\n" + text[i:]
pathlib.Path(server).write_text(new, encoding="utf-8")
print("inserted", len(block.encode("utf-8")), "bytes before the scrub marker at byte", len(text[:i].encode("utf-8")))
