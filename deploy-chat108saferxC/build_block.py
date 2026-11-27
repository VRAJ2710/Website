import json, os, sys
d = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, d + "/src")
from patches import PATCHES
home = open(d + "/src/home.v3home2.js").read()
P = list(PATCHES) + [(open(d + "/src/rgold.old.js").read(), open(d + "/src/rgold.new.js").read(), 1)]
out = home
for o, n, c in P:
    assert home.count(o) == c, ("count", o[:80], home.count(o), c)
    out = out.replace(o, n)
open(d + "/src/home.c10.preview.js", "w").write(out)  # reference copy of what the preview serves
t = open(d + "/src/block.tpl.js").read()
def lit(s): return json.dumps(s, ensure_ascii=True).replace("</", "<\\/")
pj = "[" + ",".join("[" + lit(o) + "," + lit(n) + "," + str(c) + "]" for o, n, c in P) + "]"
b = t.replace("__CSS__", lit(open(d + "/src/c10.css").read()), 1).replace("__PATCHES__", pj, 1)
assert "__CSS__" not in b and "__PATCHES__" not in b
open(d + "/server_block_chat108saferxC.js", "w").write(b); print(len(b.encode()))
