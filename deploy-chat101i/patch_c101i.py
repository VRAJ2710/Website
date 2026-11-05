#!/usr/bin/env python3
# chat101i: replace only the Bank Rate article, its paragraph helper, and the
# existing c101h style block. Usage:
#   patch_c101i.py SERVER OLD_BANK NEW_BANK CSS_OLD CSS_NEW
#   patch_c101i.py --check BASE GOT OLD_BANK NEW_BANK CSS_OLD CSS_NEW
import pathlib, sys

LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
OLD_PARAS = '  function paras(list) { return list.map((p) => `<p>${p}</p>`).join(""); }\n'
NEW_PARAS = '  function paras(list) { return list.map((p) => (p.indexOf(\'<div class="c101h-watch"\') === 0 ? p : `<p>${p}</p>`)).join(""); } // chat101i: bank-rate article\n'
DISC = "Not investment advice. Capital at risk."
BYLINE = "Edited by Vraj Patel"

def die(m):
    sys.exit("patch_c101i: " + m)

def rd(p):
    return pathlib.Path(p).read_text(encoding="utf-8")

def apply_edits(text, frag_old, frag_new, css_old, css_new):
    if text.count(OLD_PARAS) != 1:
        die("paragraph helper count is %d" % text.count(OLD_PARAS))
    if text.count(frag_old) != 1:
        die("bank article count is %d" % text.count(frag_old))
    if text.count(css_old) != 1:
        die("style-block anchor count is %d" % text.count(css_old))
    return text.replace(css_old, css_new, 1).replace(OLD_PARAS, NEW_PARAS, 1).replace(frag_old, frag_new, 1)

def assert_result(old, got, frag_old, frag_new, css_old, css_new):
    if old.count(frag_old) != 1 or old.count(OLD_PARAS) != 1 or old.count(css_old) != 1:
        die("base is not the single chat101h article")
    expect = apply_edits(old, frag_old, frag_new, css_old, css_new)
    # apply_edits dies on bad counts; re-read expect from a copy by doing the replaces directly
    # The call above already transformed. Rebuild expect without the count dies by using the known-good path.
    if got != expect:
        die("server.js changed outside the Bank Rate article, the paragraph helper and the style block")
    if got.count(frag_new) != 1 or frag_old in got:
        die("new article is not the single replacement")
    if OLD_PARAS in got or got.count(NEW_PARAS) != 1:
        die("paragraph helper was not replaced once")
    if css_old in got or got.count(css_new) != 1:
        die("style block was not replaced once")
    if "<style" in frag_new:
        die("article fragment contains a style tag")
    if got.count(DISC) < old.count(DISC) or got.count(BYLINE) < old.count(BYLINE):
        die("byline or disclaimer was removed")
    if "21 May 2019" not in got or "19:50 UK (GMT), 5 November 2026" not in got:
        die("the other articles were altered")
    if got.split("\n", 1)[0] != LINE1:
        die("line 1 lost")

def main(argv):
    if argv[1] == "--check":
        base, got, oldf, newf, css_o, css_n = argv[2:8]
        assert_result(rd(base), rd(got), rd(oldf), rd(newf), rd(css_o), rd(css_n))
        print("patch_c101i: check ok")
        return
    server, oldf, newf, css_o, css_n = argv[1:6]
    text = rd(server)
    frag_old, frag_new = rd(oldf), rd(newf)
    css_old, css_new = rd(css_o), rd(css_n)
    if text.split("\n", 1)[0] != LINE1:
        die("line 1 changed")
    if "chat101h: three sourced research articles" not in text:
        die("chat101h article block is not in this server.js")
    if "chat101i: bank-rate article" in text:
        die("already applied")
    if "slug: \"gold-real-yields-breakeven-inflation\"" not in text or "slug: \"central-bank-gold-reserves-value-volume\"" not in text:
        die("the other research articles are missing")
    _london = "Vraj Patel," + " London"
    for bad in ("GC=F", "CL=F", "^TNX", "buy now", "sell now", "stripe.", _london, "<style"):
        if bad in frag_new:
            die("new article contains a forbidden token")
    got = apply_edits(text, frag_old, frag_new, css_old, css_new)
    assert_result(text, got, frag_old, frag_new, css_old, css_new)
    if "$108 per barrel" not in got or "216 pence per therm" not in got or "one-for-now" not in got:
        die("new bank facts missing")
    pathlib.Path(server).write_text(got, encoding="utf-8")
    print("patch_c101i: ok")

if __name__ == "__main__":
    main(sys.argv)
