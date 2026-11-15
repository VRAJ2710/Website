#!/usr/bin/env python3
"""Replace the r6j scrub. Header, footer, breadcrumb and the scenario script stay in the last-write block."""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
TAG = "chat102r6j"


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6k.py server.js app.js index.html old_block.js new_block.js")
    server, app, index, old_path, new_path = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    old = old_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if not old.endswith("\n"):
        old += "\n"
    if not new.endswith("\n"):
        new += "\n"
    if MARKER not in old or MARKER not in new or "chat102r6k:" not in new:
        sys.exit("scrub block marker missing")
    if new.count("[c102r6k] scrub attached") != 1 or "[c102r6j] scrub attached" in new:
        sys.exit("attach log is not the single r6k line")
    if text.count(old) != 1:
        sys.exit("staged scrub block matched %d times" % text.count(old))
    tags = re.findall(r"app\.js\?v=([A-Za-z0-9._-]+)", it)
    if tags != [TAG]:
        sys.exit("index.html app.js cache tag matched %r, expected %s" % (tags, TAG))
    prefix, suffix = text.split(old, 1)
    suffix_out = suffix + "\n" if suffix and not suffix.endswith("\n") else suffix
    result = prefix + suffix_out + new
    if not result.endswith(new) or result[: len(prefix)] != prefix:
        sys.exit("bytes before the scrub block changed")
    server.write_text(result, encoding="utf-8")
    app.write_text(at, encoding="utf-8")
    index.write_text(it, encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())
    print("app.js and index.html unchanged")
    print("index cache tag stays app.js?v=" + TAG)


if __name__ == "__main__":
    main()
