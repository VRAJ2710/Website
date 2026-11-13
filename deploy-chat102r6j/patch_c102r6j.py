#!/usr/bin/env python3
"""Replace the r6i scrub and the gold-card spot/XAU lines. Anchors are content."""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
NEW_TAG = "chat102r6j"
REPLACEMENTS = (
    (
        'if (fut) html = html.replace(/\\bSPOT\\b/g, "DELAYED").replace(/(\\s*[·|•]\\s*)spot\\b/ig, "").replace(/\\bGold spot\\b/g, "Gold futures (COMEX, front month)");',
        'if (fut) html = html.replace(/\\bSPOT\\b/g, "DELAYED").replace(/>(\\s*)spot(\\s*)</ig, ">$1Futures$2<").replace(/(\\s*[·|•]\\s*)spot\\b/ig, "").replace(/\\bGold spot\\b/g, "Gold futures (COMEX, front month)");',
        "futures status spot badge",
    ),
    (
        """    var tk = el.querySelector(".spine-tk");
    if (!tk || String(tk.textContent || "").trim() !== "XAU") return;""",
        """    var tk = el.querySelector(".spine-tk");
    var tkText = tk ? String(tk.textContent || "").trim() : "";
    if (!tk || (tkText !== "XAU" && tkText !== "Gold futures" && el.getAttribute("data-fe83f-gold") !== "1")) return;
    if (b.kind === "futures") {
      el.setAttribute("data-fe83f-gold", "1");
      if (tkText === "XAU") tk.textContent = "Gold futures";
      var badges = el.querySelectorAll(".trust-stat,.bd");
      for (var bi = 0; bi < badges.length; bi++) {
        if (/^spot$/i.test(String(badges[bi].textContent || "").trim())) badges[bi].textContent = "Futures";
      }
    }""",
        "desk spine gold ticker",
    ),
)


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6j.py server.js app.js index.html old_block.js new_block.js")
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
    if MARKER not in old or MARKER not in new or "chat102r6j:" not in new:
        sys.exit("scrub block marker missing")
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
    print("desk spine gold card no longer shows spot or XAU")
    print("index cache tag is app.js?v=" + NEW_TAG)


if __name__ == "__main__":
    main()
