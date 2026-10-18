#!/usr/bin/env python3
"""patch_rt45s.py (server only): /learn/ SEO title, meta description and H1 describe the new beginner guides + glossary.
Exact-string replace inside PUBLIC_APP_ROUTE_DEFINITIONS (learn). Refuses twice; safe-skip (no change) if anchors moved.
Usage: python3 patch_rt45s.py [--check] server.js"""
import sys, subprocess, tempfile, os
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
NEW_T = 'title: "Learn | Beginner Guides, Glossary & Frameworks | The Dispatch Markets",'
if NEW_T in s: sys.exit("REFUSE: rt45s already applied")
R = [
 ('title: "Learn | Market Analysis Frameworks | The Dispatch Markets",', NEW_T),
 ('description: "Free market education from The Dispatch Markets covering macro, fundamentals, technical analysis, portfolio risk, signals, economics, and calculators.",',
  'description: "Free plain-English market lessons: live vs delayed prices, gold and macro, oil, FX, crypto, stocks, charts and risk, plus a searchable glossary and pro frameworks.",'),
 ('h1: "Learn: practical market analysis frameworks",', 'h1: "Learn: plain-English market guides, glossary and frameworks",'),
]
for old, new in R:
    if s.count(old) != 1: print("SKIPPED: anchor matched %d times (%s); nothing changed" % (s.count(old), old[:50])); sys.exit(0)
for old, new in R: s = s.replace(old, new)
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: sys.exit("ABORT: node --check failed: " + r.stderr[:400])
print("OK rt45s: learn title/description/h1 updated; node --check passed" + (" (dry run)" if check else ""))
if not check:
    open(p, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8")); print("written", p)
