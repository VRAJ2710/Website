#!/usr/bin/env python3
"""Append the chat102r6c last-write scrub and plain the staged app.js gold labels.

Does not invent bytes. Refuses unless the app anchors and the chat103b cache tag are each present once, as required.
"""
import pathlib
import sys

MARKER = "// chat102r6c last-write scrub."
OLD_LABEL = 'var label = held.label && /GC=F|futures/i.test(String(held.label)) ? String(held.label) : "GC=F";'
NEW_LABEL = 'var label = held.label && !/GC=F|DX-Y|\\^TNX|=X\\b|\\^VIX|\\^GSPC|CL=F|BTC-USD/.test(String(held.label)) ? String(held.label) : "Gold futures";'
OLD_TXT = 'var txt = "GC=F " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";'
NEW_TXT = 'var txt = "Gold futures " + (g.pct > 0 ? "+" : "") + Number(g.pct).toFixed(2) + "%";'
OLD_TAG = "app.js?v=chat103b"
NEW_TAG = "app.js?v=chat103c"


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: patch_c102r6c.py server.js app.js index.html server_block_c102r6c.js")
    server, app, index, block = [pathlib.Path(p) for p in sys.argv[1:]]
    text = server.read_text(encoding="utf-8")
    extra = block.read_text(encoding="utf-8").strip("\n") + "\n"
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if MARKER not in extra:
        sys.exit("server block is missing its marker")
    if text.count(MARKER) > 0:
        sys.exit("already chat102r6c")
    if "chat102r6b reader-facing scrub" not in text:
        sys.exit("server.js is not the staged chat102r6b build")
    if at.count(OLD_LABEL) != 1:
        sys.exit("app.js gold label fallback matched %d times" % at.count(OLD_LABEL))
    if at.count(OLD_TXT) != 2:
        sys.exit("app.js GC=F percent text matched %d times" % at.count(OLD_TXT))
    if it.count(OLD_TAG) != 1:
        sys.exit("index.html app.js?v=chat103b matched %d times" % it.count(OLD_TAG))
    banned = ("create " + "table", "drop " + "table", "alter " + "table")
    if any(piece in extra.lower() for piece in banned):
        sys.exit("server block mentions DDL")
    server.write_text(text.rstrip("\n") + "\n" + extra, encoding="utf-8")
    app.write_text(at.replace(OLD_LABEL, NEW_LABEL, 1).replace(OLD_TXT, NEW_TXT), encoding="utf-8")
    index.write_text(it.replace(OLD_TAG, NEW_TAG, 1), encoding="utf-8")
    print("appended chat102r6c and plained the gold labels")


if __name__ == "__main__":
    main()
