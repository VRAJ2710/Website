#!/usr/bin/env python3
"""Replace the r6h scrub, name the gold-futures vendor, and bump the app cache tag.

Anchors are content, not line numbers. Bytes before the scrub marker stay identical.
"""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
NEW_TAG = "chat102r6i"
REPLACEMENTS = (
    (
        'return hm ? ("Gold futures (COMEX, front month) · delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · delayed";',
        'return hm ? ("Gold futures (COMEX, front month) · Yahoo Finance, delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · Yahoo Finance, delayed";',
        "gold futures as-of line",
    ),
    (
        'if (b && b.kind === "futures") return "Gold futures (COMEX, front month)";',
        'if (b && b.kind === "futures") return "Gold futures (COMEX, front month) · Yahoo Finance, delayed";',
        "gold source label",
    ),
    (
        """function _rtGoldKicker() {
  // rt14: plain words up front; the provider / status / checked detail moves to the tooltip (_rtGoldKickerTitle).
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {""",
        """function _rtGoldKicker() {
  // rt14: plain words up front; the provider / status / checked detail moves to the tooltip (_rtGoldKickerTitle).
  var futK = false;
  try { var gbK = typeof fe83f_goldBits === "function" ? fe83f_goldBits() : null; futK = !!(gbK && gbK.kind === "futures"); } catch (eFutK) { futK = false; }
  if (futK) return "Gold futures (COMEX, front month) · Yahoo Finance, delayed";
  if (typeof livePx === "function" && livePx("XAU") != null && liveQuoteSrc.XAU) {""",
        "gold kicker",
    ),
    (
        'if (fut) html = html.replace(/(\\s*[·|•]\\s*)spot\\b/ig, "");',
        'if (fut) html = html.replace(/\\bSPOT\\b/g, "DELAYED").replace(/(\\s*[·|•]\\s*)spot\\b/ig, "").replace(/\\bGold spot\\b/g, "Gold futures (COMEX, front month)");',
        "futures status spot word",
    ),
)


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6i.py server.js app.js index.html old_block.js new_block.js")
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
    if MARKER not in old or MARKER not in new:
        sys.exit("scrub block is missing its marker")
    if "chat102r6i:" not in new:
        sys.exit("new scrub block is not chat102r6i")
    if text.count(old) != 1:
        sys.exit("staged scrub block matched %d times" % text.count(old))
    for old_s, _new_s, name in REPLACEMENTS:
        n = at.count(old_s)
        if n != 1:
            sys.exit("app.js anchor %s matched %d times" % (name, n))
    tags = re.findall(r"app\.js\?v=([A-Za-z0-9._-]+)", it)
    if len(tags) != 1:
        sys.exit("index.html app.js cache tag matched %d times" % len(tags))
    if tags[0] == NEW_TAG:
        sys.exit("index already " + NEW_TAG)
    prefix, suffix = text.split(old, 1)
    suffix_out = suffix + "\n" if suffix and not suffix.endswith("\n") else suffix
    result = prefix + suffix_out + new
    if not result.endswith(new) or result[: len(prefix)] != prefix:
        sys.exit("bytes before the scrub block changed")
    for old_s, new_s, _name in REPLACEMENTS:
        at = at.replace(old_s, new_s, 1)
    server.write_text(result, encoding="utf-8")
    app.write_text(at, encoding="utf-8")
    index.write_text(it.replace("app.js?v=" + tags[0], "app.js?v=" + NEW_TAG, 1), encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())
    print("app.js gold futures source line names Yahoo Finance")
    print("index cache tag is app.js?v=" + NEW_TAG)


if __name__ == "__main__":
    main()
