#!/usr/bin/env python3
# usage: check_real.py shell|errors OUTDIR
import sys, re, json
mode, O = sys.argv[1], sys.argv[2]
if mode == "shell":
    N = lambda t: re.sub(r'\{"[A-Z0-9]+":"[^"]*"(,"[A-Z0-9]+":"[^"]*")*\}', "{DATES}", t)   # credits date map = live feed state
    a = open(O + "/shell_10.html").read(); b = open(O + "/shell_9b.html").read()
    c = a.replace('<link rel="stylesheet" href="/__chat114viz/viz.css?v=chat114viz">', "", 1).replace('<script src="/__chat115vizapp/vizapp.js?v=chat115vizapp" defer></script>', "", 1)
    assert N(c) == N(b) and a != b and a.count("/__chat115vizapp/vizapp.js") == 1 and a.count("/__chat114viz/viz.css") == 1
else:
    a = json.load(open(O + "/render10/app_render.json"))["errors"]; b = json.load(open(O + "/render9b/app_render.json"))["errors"]
    ok = {"HTTP 404 api/c102/terminal", "HTTP 404 api/c102/chart", "Failed to load resource: the server responded with a status of 404 (Not Found)"}
    for k in a:
        extra = set(a[k]) - set(b[k]) - ok
        assert not extra and not any("chat11" in e or "PAGEERROR" in e for e in a[k]), (k, extra)
        print(k, "new HTTP errors vs 9b:", sorted(set(e for e in a[k] if e.startswith("HTTP")) - set(e for e in b[k] if e.startswith("HTTP"))))
print("OK")
