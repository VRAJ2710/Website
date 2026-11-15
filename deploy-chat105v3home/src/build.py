import json,pathlib
B=pathlib.Path(__file__).parent
t=(B/'block.tpl.js').read_text()
css=(B/'home.css').read_text(); js=(B/'home.js').read_text(); snip=(B/'snippet.html').read_text().strip()
def lit(s): return json.dumps(s, ensure_ascii=True).replace('</','<\\/')
out=t.replace('__CSS__',lit(css)).replace('__JS__',lit(js)).replace('__SNIP__',lit(snip))
(B/'server_block_chat105v3home.js').write_text(out)
print(len(out.encode()))
