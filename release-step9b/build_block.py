#!/usr/bin/env python3
# Dev-only generator: block_template.js + viz.css + viz.js -> server_block_chat114viz.js (ASCII only, strings as JSON literals).
import json, os
d = os.path.dirname(os.path.abspath(__file__)); r = lambda f: open(os.path.join(d, f), encoding="utf-8").read()
t = r("block_template.js"); assert t.count("/*@@CSS@@*/") == 1 and t.count("/*@@JS@@*/") == 1
out = t.replace("/*@@CSS@@*/", json.dumps(r("viz.css"), ensure_ascii=True)).replace("/*@@JS@@*/", json.dumps(r("viz.js"), ensure_ascii=True))
open(os.path.join(d, "server_block_chat114viz.js"), "w", encoding="ascii", newline="\n").write(out); print("built", len(out))
