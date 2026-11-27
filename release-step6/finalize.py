import hashlib, re, os
d = os.path.dirname(os.path.abspath(__file__)); os.chdir(d)
s = open("deploy.sh").read(); sh = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for f in re.findall(r'^  "([A-Za-z0-9_.]+) [0-9a-zA-Z_]+"$', s, re.M):
    s = re.sub(re.escape(f) + r' [0-9a-zA-Z_]+"', f + " " + sh(f) + '"', s)
open("deploy.sh", "w").write(s); print("manifest refreshed")
