#!/usr/bin/env python3
# Dev-only generator: block_template.js + vizapp.js -> server_block_chat115vizapp.js (ASCII only, the script as a JSON literal).
import json, os
d = os.path.dirname(os.path.abspath(__file__)); r = lambda f: open(os.path.join(d, f), encoding="utf-8").read()
t = r("block_template.js"); assert t.count("/*@@JS@@*/") == 1
out = t.replace("/*@@JS@@*/", json.dumps(r("vizapp.js"), ensure_ascii=True))
open(os.path.join(d, "server_block_chat115vizapp.js"), "w", encoding="ascii", newline="\n").write(out); print("built", len(out))
