import json, os
d = os.path.dirname(os.path.abspath(__file__))
t = open(d + "/src/block.tpl.js").read()
css = open(d + "/src/a8.css").read(); js = open(d + "/src/a8.js").read()
def lit(s): return json.dumps(s, ensure_ascii=True).replace("</", "<\\/")
out = t.replace("__CSS__", lit(css), 1).replace("__JS__", lit(js), 1)
assert "__CSS__" not in out and "__JS__" not in out
open(d + "/server_block_chat108saferxA.js", "w").write(out)
print(len(out.encode()))
