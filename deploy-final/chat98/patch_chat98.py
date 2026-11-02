#!/usr/bin/env python3
# chat98 (on chat97): in-app price, level and macro-release alerts (email path built but OFF: needs DISPATCH_MAIL_API_KEY);
# Portfolio X-ray (information only). Tables come from dev_create.sql, run by hand; the code never runs DDL and hides
# both features until to_regclass finds the tables. usage: patch_chat98.py server.js app.js index.html
import sys, os
SRV, APP, IDX = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat98: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
rd = lambda f: open(os.path.join(HERE, f), encoding="utf-8").read()
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat98" in srv or "chat98" in app or "v=chat98" in idx: sys.exit("patch_chat98: already applied")
if "// ── chat97 ──" not in srv or "v=chat97" not in idx: sys.exit("patch_chat98: needs the chat97 files")
blk = rd("server_block98.js")
for bad in ("create table", "alter table", "drop table", "create index", "truncate "):
    if bad in blk.lower(): sys.exit("patch_chat98: server block contains DDL: " + bad)
CSS = rd("app_c98.css").replace("\n", "")
if "</style" in CSS.lower(): sys.exit("patch_chat98: css contains </style")
app = "// chat98\n" + app + rd("app_block98.js")
idx = edit(idx, '<style id="c97-app">', '<style id="c98-app">' + CSS + '</style><style id="c97-app">', tag="idx-css")
idx = edit(idx, '<script defer src="/app.js?v=chat97"></script>', '<script defer src="/app.js?v=chat98"></script>', tag="idx-token")
srv = srv + "\n// ── chat98 ──\n" + blk
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat98: ok")
