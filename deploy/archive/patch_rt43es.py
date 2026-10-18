#!/usr/bin/env python3
"""patch_rt43es.py (server only): /pricing Premium list says "Cancel any time (Settings → Manage billing)".
Admin note unchanged. Safe-skip if the anchor is absent. Usage: python3 patch_rt43es.py [--check] server.js"""
import sys, os, subprocess, shutil
args = [a for a in sys.argv[1:] if a != "--check"]; check = "--check" in sys.argv
p = args[0] if args else "server.js"
raw = open(p, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; s = raw.replace("\r\n", "\n")
NEW = '"Cancel any time (Settings \u2192 Manage billing)"]'
OLD = '"Cancel any time from Manage billing"]'
if NEW in s: sys.exit("REFUSE: rt43es already applied")
if s.count(OLD) != 1: print("SKIPPED: pricing anchor matched %d times; nothing changed" % s.count(OLD)); sys.exit(0)
out = s.replace(OLD, NEW)
if crlf: out = out.replace("\n", "\r\n")
tmp = p + ".rt43e.tmp.js"; open(tmp, "wb").write(out.encode("utf-8"))
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode: os.remove(tmp); sys.exit("node --check FAILED:\n" + r.stderr)
if check: os.remove(tmp); print("CHECK OK: rt43es would apply"); sys.exit(0)
shutil.copy(p, p + ".bak-rt43e"); os.replace(tmp, p); print("APPLIED rt43es; backup at", p + ".bak-rt43e")
