#!/usr/bin/env python3
"""patch_bb5c.py — /api/me tier matches hasPremiumAccess.

Chat63 plus bb5b. Server.js only. Does not rewrite app.js or index.html
and does not bump the client cache token.

bb5PublicUser copied user.tier into /api/me. An admin whose database tier
is free therefore came back as tier "free", while hasPremiumAccess(user)
is true and the pricing page already says "Admin · Premium included."
The serialised tier is now "premium" when hasPremiumAccess(user) is true.
Otherwise the database tier is copied through. The guest body and the five
signed-in keys stay the same. billingPortal is still the boolean on the
user row. Stripe, webhooks, checkout, prefs, and the database tier are
not edited.

Usage: python3 patch_bb5c.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "4b094d30cc5070c2ca44d7979452d648",
    "index.html": "0e595097e68bcf2f8c0c90395add2880",
    "server.js": "e3610e4f0c66a4b81209ec213aaf81c2",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def show(phase, name, raw):
    digest = hashlib.md5(raw).hexdigest()
    print("bb5c %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def read_bytes(path):
    if not os.path.isfile(path):
        return None
    return open(path, "rb").read()

raw = read_bytes(SRV)
if raw is None:
    die("server.js missing in %s" % D)
v = raw.decode("utf-8").replace("\r\n", "\n")
vcrlf = b"\r\n" in raw
app_before = read_bytes(APP)
idx_before = read_bytes(IDX)

digest = show("before", "server.js", raw)
if digest != EXPECTED_MD5["server.js"]:
    print("WARN md5 server.js: have %s expected %s (anchors still decide)" % (digest, EXPECTED_MD5["server.js"]))
for label, blob in (("app.js", app_before), ("index.html", idx_before)):
    if blob is None:
        print("bb5c before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5c %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5c \u2500\u2500" in v:
    print("REFUSE: bb5c already applied")
    sys.exit(0)

OLD = """function bb5PublicUser(user) {
  if (!user || !user.id) return { guest: true, tier: "free", billingPortal: false, isAdmin: false };
  var admin = typeof isAdminUser === "function" ? isAdminUser(user) === true : false;
  var out = {
    id: String(user.id),
    email: typeof user.email === "string" ? user.email : "",
    tier: typeof user.tier === "string" ? user.tier : "free",
    billingPortal: user.billingPortal === true,
    isAdmin: admin
  };
  return out;
}"""
NEW = """function bb5PublicUser(user) {
  return bb5cPublicUser(user);
}"""

miss = []
if "// \u2500\u2500 bb5b \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5b ──")
if v.count(OLD) != 1:
    miss.append("server.js anchor bb5PublicUser matched %d times" % v.count(OLD))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(OLD, NEW, 1)

BLOCK = r'''
// ── bb5c ── /api/me tier follows hasPremiumAccess. Database tier is unchanged.
// BB5C_JS
function bb5cPublicUser(user) {
  if (!user || !user.id) return { guest: true, tier: "free", billingPortal: false, isAdmin: false };
  var admin = false;
  try { admin = typeof isAdminUser === "function" && isAdminUser(user) === true; } catch (e) { admin = false; }
  var tier = typeof user.tier === "string" ? user.tier : "free";
  try {
    if (typeof hasPremiumAccess === "function" && hasPremiumAccess(user) === true) tier = "premium";
  } catch (e2) {}
  return {
    id: String(user.id),
    email: typeof user.email === "string" ? user.email : "",
    tier: tier,
    billingPortal: user.billingPortal === true,
    isAdmin: admin
  };
}
// BB5C_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5c")]
if bad:
    die("bb5c block declares a non-bb5c function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5c block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or 'tier === "premium"' in BLOCK or "tier === 'premium'" in BLOCK:
    die("bb5c block has a forbidden declaration")

v = v.rstrip("\n") + "\n" + BLOCK
print("server-only: app.js and index.html are not modified")

def nodecheck(src, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(src)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, r.stderr[:500]))

nodecheck(v, "server.js")
print("node --check passed" + (" (dry run)" if CHECK else ""))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
    print("bb5c app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5c index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5cbak"
try:
    open(bak, "wb").write(raw)
    open(SRV, "wb").write(after_srv)
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("node --check failed after write: " + r.stderr[:400])
    if read_bytes(APP) != app_before or read_bytes(IDX) != idx_before:
        raise RuntimeError("app.js or index.html changed")
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("APPLY bb5c /api/me tier follows hasPremiumAccess")
