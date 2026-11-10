#!/usr/bin/env python3
"""Replace the staged chat103 block. Bytes before that block, including the chat102r5 terminal, stay byte-for-byte."""
import pathlib
import sys

SERVER_MARK = "// chat103 cpi day"
APP_MARK = "// chat103: keep /cpi/"
INDEX_OLD = '/app.js?v=chat103"'
INDEX_NEW = '/app.js?v=chat103b"'


def replace_from(text, mark, block):
    at = text.find(mark)
    if at < 0:
        sys.exit("missing marker " + mark)
    if text.find(mark, at + len(mark)) >= 0:
        sys.exit("marker is not unique: " + mark)
    line = text.rfind("\n", 0, at)
    if line < 0:
        sys.exit("marker is not on its own line: " + mark)
    return text[: line + 1] + block.strip("\n") + "\n", text[: line + 1]


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c103.py server.js app.js index.html server_block app_block")
    server, app, index, sblock, ablock = [pathlib.Path(p) for p in sys.argv[1:6]]
    sb = sblock.read_text(encoding="utf-8")
    ab = ablock.read_text(encoding="utf-8")
    if SERVER_MARK not in sb:
        sys.exit("server block is missing its marker")
    if APP_MARK not in ab:
        sys.exit("app block is missing its marker")
    st = server.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if SERVER_MARK not in st:
        sys.exit("server.js does not already contain chat103")
    if APP_MARK not in at:
        sys.exit("app.js does not already contain the chat103 menu block")
    if 'c102Path === "/terminal"' not in at or 'c102Path === "/cpi"' not in at:
        sys.exit("app.js lost the terminal or /cpi/ path guard")
    if it.count(INDEX_OLD) != 1:
        sys.exit("index.html does not contain exactly one chat103 app cache token")
    new_server, server_prefix = replace_from(st, SERVER_MARK, sb)
    new_app, app_prefix = replace_from(at, APP_MARK, ab)
    if not new_server.startswith(server_prefix) or not new_app.startswith(app_prefix):
        sys.exit("prefix was not kept")
    server.write_text(new_server, encoding="utf-8")
    app.write_text(new_app, encoding="utf-8")
    index.write_text(it.replace(INDEX_OLD, INDEX_NEW, 1), encoding="utf-8")
    print("patched")


if __name__ == "__main__":
    main()
