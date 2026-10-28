#!/usr/bin/env python3
"""chat90 brand rename: "The Dispatch Markets" -> "The Dispatch Market" (singular). Python 3.8+.
Usage: patch_brand.py <server.js> <app.js> <index.html> [--static <dir>] [--report <file>]
Only brand strings change. Generic "markets", domains, URLs, UA strings (DispatchMarkets/1.0), ids, keys, paths stay.
Also bumps index.html app.js?v=chat89 -> chat90 (exactly one line).
Anchors/counts are asserted; any surprise -> exit 1 before writing anything."""
import json, re, sys, pathlib

def die(m):
    print("PATCH-ABORT: " + m, file=sys.stderr); sys.exit(1)

# (regex, replacement) applied in order
RULES = [
    (re.compile(r"Dispatch Markets\b"), "Dispatch Market"),        # The Dispatch Markets / Dispatch Markets
    (re.compile(r"DISPATCH MARKETS\b"), "DISPATCH MARKET"),
    (re.compile(r"THE DISPATCH · MARKETS"), "THE DISPATCH · MARKET"),
    (re.compile(r"THE DISPATCH <b>·</b> MARKETS"), "THE DISPATCH <b>·</b> MARKET"),
    (re.compile(r"The Dispatch · Markets"), "The Dispatch · Market"),
    (re.compile(r"The <em>Dispatch</em> Markets"), "The <em>Dispatch</em> Market"),
    (re.compile(r'<span class="cmd-logo-market">MARKETS</span>'), '<span class="cmd-logo-market">MARKET</span>'),
    (re.compile(r'<span class="logo-markets">Markets</span>'), '<span class="logo-markets">Market</span>'),
]
# anything still brand-like after patching?
LEFT = re.compile(r"dispatch(?:\s|·|&middot;|&nbsp;|<[^>]*>)+markets\b", re.I)

EXPECT = {  # file -> expected number of replacements (all rules together)
    "server.js": 45, "app.js": 16, "index.html": 14,
}

def apply(text):
    n = 0
    for rx, rep in RULES:
        text, k = rx.subn(rep, text); n += k
    return text, n

def main(argv):
    args = argv[1:]
    static = None; report = None
    for flag in ("--static", "--report"):
        if flag in args:
            i = args.index(flag); v = args[i + 1]; del args[i:i + 2]
            if flag == "--static": static = v
            else: report = v
    if len(args) != 3: die("usage: patch_brand.py server.js app.js index.html [--static dir] [--report file]")
    out = {}; lines = []
    for p in args:
        path = pathlib.Path(p); name = path.name
        if name not in EXPECT: die("unexpected file " + name)
        src = path.read_bytes().decode("utf-8")
        new, n = apply(src)
        if n != EXPECT[name]: die("%s: %d replacements, expected %d (base differs?)" % (name, n, EXPECT[name]))
        if LEFT.search(new): die("%s: brand-like text remains after patch" % name)
        if name == "server.js":
            if not new.startswith("const BB10I_MAINTENANCE_ON = true;"): die("server.js line 1 maintenance flag changed")
        if name == "index.html":
            old, k = "app.js?v=chat89", new.count("app.js?v=chat89")
            if k != 1: die("index.html: expected exactly one app.js?v=chat89, got %d" % k)
            new = new.replace(old, "app.js?v=chat90"); n += 0
        # line-level report
        sl = src.split("\n"); nl = new.split("\n")
        if len(sl) != len(nl): die("line count changed in " + name)
        for i, (a, b) in enumerate(zip(sl, nl), 1):
            if a != b: lines.append((name, i, a, b))
        out[path] = (new, n)
    # static files (optional, in-place literal replacement)
    stat = {}
    if static:
        for sn in ("manifest.json", "llms.txt"):
            sp = pathlib.Path(static) / sn
            if not sp.is_file(): print("static: %s not present, skipped" % sn); continue
            s = sp.read_bytes().decode("utf-8")
            if not LEFT.search(s): print("static: %s has no brand text, skipped" % sn); continue
            t, k = apply(s)
            if LEFT.search(t): die("%s: brand-like text remains" % sn)
            if sn.endswith(".json"):
                json.loads(t)
            stat[sp] = (t, k); print("static: %s -> %d replacement(s)" % (sn, k))
    # write only after everything checked
    for path, (new, n) in out.items():
        path.write_bytes(new.encode("utf-8")); print("%s: %d brand replacements" % (path.name, n))
    for sp, (t, k) in stat.items():
        sp.write_bytes(t.encode("utf-8"))
    if report:
        with open(report, "w", encoding="utf-8") as f:
            for name, i, a, b in lines:
                f.write("%s:%d\n  - %s\n  + %s\n" % (name, i, a[:400], b[:400]))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
