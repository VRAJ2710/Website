#!/usr/bin/env python3
"""Replace the chat102r6c scrub block in place. Bytes outside that block stay identical."""
import pathlib
import sys

MARKER = "// chat102r6c last-write scrub."


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: patch_c102r6d.py server.js old_block.js new_block.js")
    server, old_path, new_path = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    old = old_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")
    if not old.endswith("\n"):
        old += "\n"
    if not new.endswith("\n"):
        new += "\n"
    if MARKER not in old or MARKER not in new:
        sys.exit("scrub block is missing its marker")
    if text.count(old) != 1:
        sys.exit("staged r6c block matched %d times" % text.count(old))
    prefix, suffix = text.split(old, 1)
    if suffix and not suffix.endswith("\n"):
        suffix_out = suffix + "\n"
    else:
        suffix_out = suffix
    result = prefix + suffix_out + new
    outside = prefix + suffix
    outside_new = result[: len(result) - len(new)]
    if outside_new != prefix + suffix_out:
        sys.exit("bytes outside the r6c block changed")
    if not result.endswith(new):
        sys.exit("updated scrub block is not last")
    if prefix != text[: text.find(old)]:
        sys.exit("prefix before the scrub block changed")
    server.write_text(result, encoding="utf-8")
    print("replaced chat102r6c block in place; bytes before it unchanged; block is last")


if __name__ == "__main__":
    main()
