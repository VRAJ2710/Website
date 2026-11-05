#!/usr/bin/env python3
# chat101i: replace only the Bank Rate research article inside the chat101h server block.
# Usage: patch_c101i.py SERVER OLD_BANK NEW_BANK
import pathlib, sys
S, OLD, NEW = sys.argv[1:4]
def die(m):
    sys.exit("patch_c101i: " + m)
srv = pathlib.Path(S).read_text(encoding="utf-8")
old = pathlib.Path(OLD).read_text(encoding="utf-8")
new = pathlib.Path(NEW).read_text(encoding="utf-8")
LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != LINE1:
    die("line 1 changed")
if "chat101h: three sourced research articles" not in srv:
    die("chat101h article block is not in this server.js")
if "chat101i: bank-rate article" in srv:
    die("already applied")
OLD_PARAS = '  function paras(list) { return list.map((p) => `<p>${p}</p>`).join(""); }\n'
NEW_PARAS = '  function paras(list) { return list.map((p) => (p.indexOf(\'<div class="c101h-watch"\') === 0 ? p : `<p>${p}</p>`)).join(""); } // chat101i: bank-rate article\n'
if srv.count(OLD_PARAS) != 1:
    die("paragraph helper count is %d" % srv.count(OLD_PARAS))
if srv.count(old) != 1:
    die("bank article count is %d" % srv.count(old))
if "slug: \"gold-real-yields-breakeven-inflation\"" not in srv or "slug: \"central-bank-gold-reserves-value-volume\"" not in srv:
    die("the other research articles are missing")
_london = "Vraj Patel," + " London"
for bad in ("GC=F", "CL=F", "^TNX", "buy now", "sell now", "stripe.", _london):
    if bad in new:
        die("new article contains a forbidden token")
srv = srv.replace(OLD_PARAS, NEW_PARAS, 1).replace(old, new, 1)
if srv.split("\n", 1)[0] != LINE1:
    die("line 1 lost")
if srv.count("slug: \"bank-rate-energy-shock-sterling-gold\"") != 1:
    die("bank slug count")
if "21 May 2019" not in srv or "19:50 UK (GMT), 5 November 2026" not in srv:
    die("the other articles were altered")
if "$108 per barrel" not in srv or "216 pence per therm" not in srv or "one-for-now" not in srv:
    die("new bank facts missing")
pathlib.Path(S).write_text(srv, encoding="utf-8")
print("patch_c101i: ok")
