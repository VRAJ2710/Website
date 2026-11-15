#!/usr/bin/env python3
"""Replace the r6m scrub without the learn breadcrumb, and label dashboard gold from the desk quote."""
import hashlib
import pathlib
import re
import sys

MARKER = "// chat102r6c last-write scrub."
OLD_TAG = "chat102r6m"
NEW_TAG = "chat102r6n"
HELPER = r'''function c102r6nGoldRow() {
  var row = null;
  try {
    if (typeof fe79_srv !== "undefined" && fe79_srv) row = fe79_srv.XAU || fe79_srv["GC=F"] || null;
  } catch (e0) { row = null; }
  row = row || {};
  var dc = row.displayChange && typeof row.displayChange === "object" ? row.displayChange : {};
  var gold = row.gold && typeof row.gold === "object" ? row.gold : {};
  var inst = String(row.instrument || dc.instrument || gold.instrument || "");
  var src = String(row.source || row.src || row.feed || "");
  var sym = String(row.symbol || row.feedSymbol || row.ticker || dc.symbol || "");
  if (!src && typeof liveQuoteSrc !== "undefined" && liveQuoteSrc) {
    try { src = String(liveQuoteSrc["GC=F"] || liveQuoteSrc.XAU || ""); } catch (e1) { src = ""; }
  }
  var blob = src + " " + sym;
  var fut = inst === "futures" || (/GC=F/i.test(blob) && !/gold-api/i.test(src));
  if (/gold-api/i.test(src) && inst !== "futures") fut = false;
  return { fut: fut, src: src, sym: sym };
}
function c102r6nVendor(src, sym) {
  var s = (String(src || "") + " " + String(sym || "")).toLowerCase();
  if (s.indexOf("twelve") >= 0) return "Twelve Data";
  if (s.indexOf("yahoo") >= 0 || s.indexOf("gc=f") >= 0) return "Yahoo Finance";
  if (s.indexOf("gold-api") >= 0 || s.indexOf("goldapi") >= 0) return "gold-api";
  return "";
}
function c102r6nLine(info) {
  var vendor = c102r6nVendor(info.src, info.sym);
  if (info.fut) return "Gold futures (COMEX, front month)" + (vendor ? " · " + vendor + ", delayed" : "");
  if (vendor === "gold-api") return "Gold spot · gold-api";
  return "Gold" + (vendor ? " · " + vendor : "");
}
function c102r6nClean(v, fut) {
  var next = String(v || "").replace(/\bGC=F\b/g, "Gold").replace(/\bXAU\b/g, "Gold");
  if (fut) next = next.replace(/\bGold spot\b/ig, "Gold futures").replace(/\bspot\b/ig, "futures");
  return next;
}
function c102r6nText(el, fut) {
  if (!el) return;
  if (el.children && el.children.length) {
    var n = el.firstChild;
    while (n) {
      if (n.nodeType === 3) {
        var t = c102r6nClean(n.nodeValue, fut);
        if (t !== n.nodeValue) n.nodeValue = t;
      }
      n = n.nextSibling;
    }
    return;
  }
  var v = String(el.textContent || "");
  var next = c102r6nClean(v, fut);
  if (next !== v) el.textContent = next;
}
function c102r6nGoldEl(el, tk) {
  var oc = el.getAttribute ? (el.getAttribute("onclick") || "") : "";
  var card = el.getAttribute ? (el.getAttribute("data-price-card") || el.getAttribute("data-c102r6n") || "") : "";
  var id = tk ? String(tk.textContent || "").trim() : "";
  return card === "gold" || card === "XAU" || card === "GC=F" || id === "XAU" || id === "GC=F" || id === "Gold" || oc.indexOf("'XAU'") >= 0 || oc.indexOf("GC=F") >= 0;
}
function c102r6nDashGold() {
  if (typeof document === "undefined" || !document.querySelectorAll) return;
  var info = c102r6nGoldRow();
  var line = c102r6nLine(info);
  var nodes = document.querySelectorAll(".spine-cell, .wl-glance-chip, .conv-card");
  var i;
  for (i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var tk = el.querySelector(".spine-tk") || el.querySelector(".wl-g-tk") || el.querySelector(".conv-tk");
    if (!c102r6nGoldEl(el, tk)) continue;
    if (el.setAttribute) el.setAttribute("data-c102r6n", "gold");
    if (tk && tk.textContent !== "Gold") tk.textContent = "Gold";
    c102r6nText(el.querySelector(".spine-lbl"), info.fut);
    c102r6nText(el.querySelector(".spine-chg") || el.querySelector(".wl-g-c") || el.querySelector(".conv-chg"), info.fut);
    var nm = el.querySelector(".conv-nm");
    if (nm && nm.textContent !== line) nm.textContent = line;
    var asof = el.querySelector(".spine-asof") || el.querySelector(".asof-tag");
    if (asof) {
      var prev = String(asof.textContent || "");
      var hm = prev.match(/as of [^·]+$/);
      var next = line + (hm ? " · " + hm[0].trim() : "");
      if (asof.textContent !== next) asof.textContent = next;
    }
    if (String(el.className || "").indexOf("wl-glance-chip") >= 0) {
      var kids = el.children || [];
      var j;
      for (j = 0; j < kids.length; j++) {
        if (/wl-g-/.test(String(kids[j].className || ""))) continue;
        if (kids[j].children && kids[j].children.length) continue;
        if (kids[j].textContent !== line) kids[j].textContent = line;
        break;
      }
    }
  }
}
'''
REPLACEMENTS = (
    (
        "function fe83f_afterPaint() {",
        HELPER + "function fe83f_afterPaint() {",
        "dashboard gold helper",
    ),
    (
        """    try { fe83f_paintGold(); } catch (e2) {}
    try { fe83f_paintDays(); } catch (e3) {}""",
        """    try { fe83f_paintGold(); } catch (e2) {}
    try { c102r6nDashGold(); } catch (eN) {}
    try { fe83f_paintDays(); } catch (e3) {}""",
        "dashboard gold paint",
    ),
)


def main():
    if len(sys.argv) != 6:
        sys.exit("usage: patch_c102r6n.py server.js app.js index.html old_block.js new_block.js")
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
    if MARKER not in old or MARKER not in new or "chat102r6n:" not in new:
        sys.exit("scrub block marker missing")
    if new.count("[c102r6n] scrub attached") != 1 or "[c102r6m] scrub attached" in new:
        sys.exit("attach log is not the single r6n line")
    if "c102r6m-crumb" in new or "c102r6l-crumb" in new:
        sys.exit("new scrub still injects a breadcrumb")
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
    print("learn breadcrumb removed; dashboard gold follows the desk quote")
    print("index cache tag is app.js?v=" + NEW_TAG)


if __name__ == "__main__":
    main()
