#!/usr/bin/env python3
"""Replace the r6n scrub and apply the four reader-facing fixes. Bump the cache tag."""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
OLD_TAG = "chat102r6n"
NEW_TAG = "chat102r6o"
HELPER = r'''function c102r6oAfter() {
  if (typeof document === "undefined" || !document.querySelectorAll) return;
  var info = { fut: false, src: "", sym: "" };
  var line = "Gold";
  try { info = c102r6nGoldRow(); line = c102r6nLine(info); } catch (e0) {}
  if (info.fut) line = String(line).replace(/\bspot\b/ig, "").replace(/\s{2,}/g, " ").replace(/\s+·\s*/g, " · ").trim();
  var chips = document.querySelectorAll(".wl-glance-chip");
  var i;
  for (i = 0; i < chips.length; i++) {
    var el = chips[i];
    var oc = el.getAttribute("onclick") || "";
    var tk = el.querySelector(".wl-g-tk");
    var id = tk ? String(tk.textContent || "").trim() : "";
    if (oc.indexOf("'XAU'") < 0 && oc.indexOf("GC=F") < 0 && id !== "XAU" && id !== "GC=F" && id !== "Gold" && el.getAttribute("data-c102r6o") !== "1") continue;
    el.setAttribute("data-c102r6o", "1");
    if (tk && tk.textContent !== "Gold") tk.textContent = "Gold";
    var host = null;
    var kids = el.children || [];
    var j;
    for (j = 0; j < kids.length; j++) {
      if (/wl-g-/.test(String(kids[j].className || ""))) continue;
      if (kids[j].children && kids[j].children.length) continue;
      host = kids[j];
      break;
    }
    if (!host && document.createElement) {
      host = document.createElement("span");
      host.className = "c102r6o-lag";
      if (el.appendChild) el.appendChild(host);
    }
    if (host && host.textContent !== line) host.textContent = line;
  }
  var rows = document.querySelectorAll(".cap-nums, .cap-lbl, .news-px, .news-act");
  for (i = 0; i < rows.length; i++) {
    var row = rows[i];
    if (row.children && row.children.length) continue;
    var v = String(row.textContent || "");
    var next = v.replace(/\bGC=F\b/g, "Gold").replace(/\bXAU\b/g, "Gold");
    if (next !== v) row.textContent = next;
  }
  if (document.createTreeWalker && document.body) {
    var tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var n, list = [];
    while ((n = tw.nextNode())) list.push(n);
    for (i = 0; i < list.length; i++) {
      var node = list[i];
      var p = node.parentNode;
      if (!p || /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(p.tagName || "")) continue;
      var u = String(node.nodeValue || "").replace(/\bUK UK\b/g, "UK");
      if (u !== node.nodeValue) node.nodeValue = u;
    }
  }
}
'''
REPLACEMENTS = (
    (
        'const upd = _lf ? `Prices last refreshed <span class="stf-time">${_rt16Hms(_lf)}</span> UK time` : "";',
        'const upd = _lf ? `Prices last refreshed <span class="stf-time">${String(_rt16Hms(_lf) || "").replace(/\\s*UK\\s*$/i, "")}</span> UK time` : "";',
        "footer UK time",
    ),
    (
        "${p.a} — · ${p.b} —",
        '${p.a==="XAU"||p.a==="GC=F"?"Gold":p.a} — · ${p.b==="XAU"||p.b==="GC=F"?"Gold":p.b} —',
        "cap row empty",
    ),
    (
        '${p.a} ${ca >= 0 ? "+" : ""}${ca.toFixed(1)}% · ${p.b} ${cb >= 0 ? "+" : ""}${cb.toFixed(1)}%',
        '${p.a==="XAU"||p.a==="GC=F"?"Gold":p.a} ${ca >= 0 ? "+" : ""}${ca.toFixed(1)}% · ${p.b==="XAU"||p.b==="GC=F"?"Gold":p.b} ${cb >= 0 ? "+" : ""}${cb.toFixed(1)}%',
        "cap row numbers",
    ),
    (
        "${topTk} ${d.p}",
        '${topTk==="XAU"||topTk==="GC=F"?"Gold":topTk} ${d.p}',
        "news price label",
    ),
    (
        ">Open ${topTk}</button>",
        '>${topTk==="XAU"||topTk==="GC=F"?"Open Gold":"Open "+topTk}</button>',
        "news open label",
    ),
    (
        "function fe83f_afterPaint() {",
        HELPER + "function fe83f_afterPaint() {",
        "reader label helper",
    ),
    (
        "    try { c102r6nDashGold(); } catch (eN) {}",
        "    try { c102r6nDashGold(); } catch (eN) {}\n    try { c102r6oAfter(); } catch (eO) {}",
        "reader label paint",
    ),
)


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6o.py server.js app.js index.html old_block.js new_block.js")
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
    if MARKER not in old or MARKER not in new or "chat102r6o:" not in new:
        sys.exit("scrub block marker missing")
    if new.count("[c102r6o] scrub attached") != 1 or "[c102r6n] scrub attached" in new:
        sys.exit("attach log is not the single r6o line")
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
    server.write_text(result, encoding="utf-8")
    app.write_text(at, encoding="utf-8")
    index.write_text(it.replace("app.js?v=" + OLD_TAG, "app.js?v=" + NEW_TAG, 1), encoding="utf-8")
    print("replaced the last-write scrub block; bytes before it unchanged; block is last")
    print("prefix sha256 " + hashlib.sha256(prefix.encode("utf-8")).hexdigest())
    print("index cache tag is app.js?v=" + NEW_TAG)


if __name__ == "__main__":
    main()
