#!/usr/bin/env python3
"""Replace the r6l scrub, name the gold card from its real source, and bump the cache tag."""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
OLD_TAG = "chat102r6j"
NEW_TAG = "chat102r6m"
HELPER = r'''function c102r6mVendor(src) {
  var s = String(src || "");
  var l = s.toLowerCase();
  if (l.indexOf("twelve") >= 0) return "Twelve Data";
  if (l.indexOf("yahoo") >= 0 || s.indexOf("GC=F") >= 0) return "Yahoo Finance";
  if (l.indexOf("gold-api") >= 0 || l.indexOf("goldapi") >= 0) return "gold-api";
  return "";
}
function c102r6mGoldInfo() {
  var src = "", inst = "";
  try {
    var g = typeof fe81_goldHeld === "function" ? fe81_goldHeld() : null;
    if (g) { src = g.source || g.src || g.feed || ""; inst = g.instrument || ""; }
  } catch (e0) {}
  if (!src) {
    try {
      var f = typeof fe77_futObj === "function" ? fe77_futObj() : null;
      if (f) { src = f.source || f.src || f.feed || ""; if (!inst) inst = f.instrument || ""; }
    } catch (e1) {}
  }
  if (!src && typeof liveQuoteSrc !== "undefined" && liveQuoteSrc) {
    try { src = liveQuoteSrc["GC=F"] || liveQuoteSrc.XAU || ""; } catch (e2) { src = ""; }
  }
  return { src: String(src || ""), inst: String(inst || "") };
}
function c102r6mIsFut(kind, src, inst) {
  var l = String(src || "").toLowerCase();
  if (l.indexOf("gold-api") >= 0 || l.indexOf("goldapi") >= 0) return false;
  if (inst === "spot") return false;
  if (inst === "futures") return true;
  if (l.indexOf("twelve") >= 0 && l.indexOf("fut") < 0 && l.indexOf("gc=f") < 0) return false;
  return kind === "futures" || kind === "fut";
}
function c102r6mGoldLabel(kind) {
  var info = c102r6mGoldInfo();
  var vendor = c102r6mVendor(info.src);
  var fut = c102r6mIsFut(kind, info.src, info.inst);
  if (!vendor && fut && !info.src) vendor = "Yahoo Finance";
  var head = fut ? "Gold futures (COMEX, front month)" : "Gold";
  if (vendor === "gold-api") return head + " · gold-api";
  if (vendor === "Twelve Data" || vendor === "Yahoo Finance") return head + " · " + vendor + ", delayed";
  return head;
}
'''
REPLACEMENTS = (
    (
        "function fe85_asofBits() {",
        HELPER + "function fe85_asofBits() {",
        "gold label helper",
    ),
    (
        'return hm ? ("Gold futures (COMEX, front month) · Yahoo Finance, delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · Yahoo Finance, delayed";',
        'var label = c102r6mGoldLabel("futures");\n  return hm ? (label + " · as of " + hm + " UK") : label;',
        "gold futures as-of line",
    ),
    (
        'if (b && b.kind === "futures") return "Gold futures (COMEX, front month) · Yahoo Finance, delayed";',
        'if (b && b.kind === "futures") return c102r6mGoldLabel(b.kind);',
        "gold source label",
    ),
    (
        'if (futK) return "Gold futures (COMEX, front month) · Yahoo Finance, delayed";',
        'if (futK) return c102r6mGoldLabel("futures");',
        "gold kicker",
    ),
)


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6m.py server.js app.js index.html old_block.js new_block.js")
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
    if MARKER not in old or MARKER not in new or "chat102r6m:" not in new:
        sys.exit("scrub block marker missing")
    if new.count("[c102r6m] scrub attached") != 1 or "[c102r6l] scrub attached" in new:
        sys.exit("attach log is not the single r6m line")
    if text.count(old) != 1:
        sys.exit("staged scrub block matched %d times" % text.count(old))
    for old_s, _new_s, name in REPLACEMENTS:
        n = at.count(old_s)
        if n != 1:
            sys.exit("app.js anchor %s matched %d times" % (name, n))
    tags = re.findall(r"app\.js\?v=([A-Za-z0-9._-]+)", it)
    if tags != [OLD_TAG]:
        sys.exit("index.html app.js cache tag matched %r, expected %s" % (tags, OLD_TAG))
    prefix, suffix = text.split(old, 1)
    suffix_out = suffix + "\n" if suffix and not suffix.endswith("\n") else suffix
    result = prefix + suffix_out + new
    if not result.endswith(new) or result[: len(prefix)] != prefix:
        sys.exit("bytes before the scrub block changed")
    for old_s, new_s, _name in REPLACEMENTS:
        at = at.replace(old_s, new_s, 1)
    if at.count("Gold futures (COMEX, front month) · Yahoo Finance, delayed") != 0:
        sys.exit("a gold label still hardcodes Yahoo Finance")
    server.write_text(result, encoding="utf-8")
    app.write_text(at, encoding="utf-8")
    index.write_text(it.replace("app.js?v=" + OLD_TAG, "app.js?v=" + NEW_TAG, 1), encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())
    print("gold card vendor follows the displayed source")
    print("index cache tag is app.js?v=" + NEW_TAG)


if __name__ == "__main__":
    main()
