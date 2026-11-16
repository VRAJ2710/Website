#!/usr/bin/env python3
"""Replace the r6o last-write scrub with r6p. Bytes before the scrub are unchanged."""
import hashlib
import pathlib
import sys

MARKER = "// chat102r6c last-write scrub."


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: patch_c102r6p.py server.js old_block.js new_block.js")
    server, old_path, new_path = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    old = old_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")
    if not old.endswith("\n"):
        old += "\n"
    if not new.endswith("\n"):
        new += "\n"
    if MARKER not in old or MARKER not in new:
        sys.exit("scrub block marker missing")
    if "chat102r6p:" not in new:
        sys.exit("r6p comment missing from the new block")
    if new.count("[c102r6p] scrub attached") != 1 or "[c102r6o] scrub attached" in new:
        sys.exit("attach log is not the single r6p line")
    if "c102r6pSessionPrev" not in new or "c102r6pInstallQuote" not in new:
        sys.exit("r6p previous-close helpers missing")
    if "chartPreviousClose" in new.split("function c102r6pSessionPrev", 1)[-1].split("function c102r6pYahooQuote", 1)[0]:
        sys.exit("c102r6pSessionPrev must not read chartPreviousClose")
    if text.count(old) != 1:
        sys.exit("staged scrub block matched %d times" % text.count(old))
    prefix, suffix = text.split(old, 1)
    suffix_out = suffix + "\n" if suffix and not suffix.endswith("\n") else suffix
    result = prefix + suffix_out + new
    if not result.endswith(new) or result[: len(prefix)] != prefix:
        sys.exit("bytes before the scrub block changed")
    if result.count("[c102r6p] scrub attached") != 1:
        sys.exit("stacked server does not have exactly one r6p attach log")
    if "[c102r6o] scrub attached" in result:
        sys.exit("r6o attach log is still present")
    server.write_text(result, encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
