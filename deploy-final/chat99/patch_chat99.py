#!/usr/bin/env python3
# chat99 (on chat98): SEC EDGAR deep-dives for any US filer (/research/sec/<TICKER>/), a filings screener built from
# XBRL frames (/research/sec/screener/), and a small sourced chart under Ask answers (BYOK and site AI). The SEC daily
# cap rises from 4 to 25 and stays in the one shared bb11:sec_downloads counter; needs DISPATCH_SEC_UA. No DDL. usage: patch_chat99.py server.js app.js index.html
import sys, os
SRV, APP, IDX = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat99: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
rd = lambda f: open(os.path.join(HERE, f), encoding="utf-8").read()
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat99" in srv or "chat99" in app or "v=chat99" in idx: sys.exit("patch_chat99: already applied")
if "// ── chat98 ──" not in srv or "v=chat98" not in idx: sys.exit("patch_chat99: needs the chat98 files")
blk = rd("server_block99.js")
for bad in ("create table", "alter table", "drop table", "create index", "truncate "):
    if bad in blk.lower(): sys.exit("patch_chat99: server block contains DDL: " + bad)
CSS = rd("app_c99.css").replace("\n", "")
if "</style" in CSS.lower(): sys.exit("patch_chat99: css contains </style")
app = "// chat99\n" + app + rd("app_block99.js")
idx = edit(idx, '<style id="c98-app">', '<style id="c99-app">' + CSS + '</style><style id="c98-app">', tag="idx-css")
idx = edit(idx, '<script defer src="/app.js?v=chat98"></script>', '<script defer src="/app.js?v=chat99"></script>', tag="idx-token")
srv = edit(srv, "var BB11_MAX_FACTS_PER_DAY = 4;", "var BB11_MAX_FACTS_PER_DAY = 25;", tag="sec-cap")
srv = srv + "\n// ── chat99 ──\n" + blk
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat99: ok")
