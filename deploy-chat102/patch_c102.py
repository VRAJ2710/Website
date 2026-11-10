#!/usr/bin/env python3
"""Apply chat102 onto a chat101h server.js, app.js and index.html. Exact append plus one boot guard."""
import pathlib
import sys

BOOT_OLD = """function fe89_bootNav() {
  const mon = fe89_isMonitorPath(location.pathname);
  nav(mon ? "research" : (_publicPageFromPath(location.pathname) || "home"), { history: mon ? "none" : "replace" });
}"""
BOOT_NEW = """function fe89_bootNav() {
  // chat102: /terminal/ is a public page. Do not send that address to Home.
  try {
    var c102Path = String(location.pathname || "");
    if (c102Path === "/terminal" || c102Path === "/terminal/") return;
  } catch (eC102) {}
  const mon = fe89_isMonitorPath(location.pathname);
  nav(mon ? "research" : (_publicPageFromPath(location.pathname) || "home"), { history: mon ? "none" : "replace" });
}"""
INDEX_OLD = '/app.js?v=chat101h"'
INDEX_NEW = '/app.js?v=chat102"'


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102.py server.js app.js index.html server_block app_block")
    server, app, index, sblock, ablock = [pathlib.Path(p) for p in sys.argv[1:6]]
    sb = sblock.read_text(encoding="utf-8")
    ab = ablock.read_text(encoding="utf-8")
    if "chat102 terminal" not in sb and "chat102 terminal." not in sb:
        sys.exit("server block is missing its marker")
    st = server.read_text(encoding="utf-8")
    at = app.read_text(encoding="utf-8")
    it = index.read_text(encoding="utf-8")
    if "chat102 terminal" in st or "api/c102/terminal" in st:
        sys.exit("server.js already contains chat102")
    if BOOT_OLD not in at:
        sys.exit("app.js is missing the fe89_bootNav guard site")
    if at.count(BOOT_OLD) != 1:
        sys.exit("fe89_bootNav guard site is not unique")
    if "chat102: keep /terminal/" in at:
        sys.exit("app.js already contains the chat102 block")
    if it.count(INDEX_OLD) != 1:
        sys.exit("index.html does not contain exactly one chat101h app cache token")
    server.write_text(st.rstrip("\n") + "\n" + sb.strip("\n") + "\n", encoding="utf-8")
    app.write_text(at.replace(BOOT_OLD, BOOT_NEW, 1).rstrip("\n") + "\n" + ab.strip("\n") + "\n", encoding="utf-8")
    index.write_text(it.replace(INDEX_OLD, INDEX_NEW, 1), encoding="utf-8")
    print("patched")


if __name__ == "__main__":
    main()
