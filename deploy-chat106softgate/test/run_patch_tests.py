#!/usr/bin/env python3
"""Local tests for patch_chat106softgate.py on the reconstructed fixture. Usage: python3 run_patch_tests.py"""
import difflib, hashlib, os, pathlib, re, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
PATCH = PKG / "patch_chat106softgate.py"
BLOCK = PKG / "server_block_chat106softgate.js"
V3H2 = PKG / "server_block_chat105v3home2.js"
R6O = PKG / "server_block_c102r6o.js"
R6P = PKG / "server_block_c102r6p.js"
v3 = V3H2.read_bytes().rstrip(b"\n") + b"\n"
r6o, r6p = R6O.read_bytes(), R6P.read_bytes()
results = []
def ok(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("ok   - " if cond else "FAIL - ") + name + (("  " + extra) if extra else ""))
def build(pre, tail):
    return pre + v3 + tail
def run_patch(path, pre, md5_override=None):
    ps = hashlib.sha256(pre).hexdigest()
    md5 = md5_override or hashlib.md5(pre + v3 + r6o).hexdigest()
    return subprocess.run([sys.executable, str(PATCH), str(path), str(BLOCK), str(V3H2), str(R6O), str(R6P), ps, str(len(pre)), md5], capture_output=True, text=True)
def patched_prefix(path):
    data = path.read_bytes(); return data[: data.index(v3)]
def main():
    W = pathlib.Path(tempfile.mkdtemp(prefix="c106sg-test-"))
    pre = (HERE / "fixture_prefix.js").read_bytes()
    # 1. Happy path on a post-r6p layout.
    f = W / "server.js"; f.write_bytes(build(pre, r6p))
    r = run_patch(f, pre); print(r.stdout.strip()); print(r.stderr.strip())
    ok("patch applies on post-r6p fixture", r.returncode == 0)
    out = f.read_bytes()
    ok("v3home2 + r6p tail byte-identical", out.endswith(v3 + r6p))
    newpre = patched_prefix(f)
    ok("exactly one attach line", out.count(b"[chat106softgate] attached") == 1)
    ok("node --check on full patched fixture", subprocess.run(["node", "--check", str(f)]).returncode == 0)
    # 2. Diff: every changed hunk is a chat106softgate change.
    a = pre.decode().splitlines(); b = newpre.decode().splitlines()
    bad = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal": continue
        if op in ("delete",):
            bad.append(("deleted", a[i1:i2])); continue
        old = a[i1:i2]; new = b[j1:j2]
        text = "\n".join(new)
        if not re.search(r"VERIFY_ENFORCE|c106sg|chat106softgate", text) and not (op == "insert"):
            bad.append((op, old, new))
    ok("only chat106softgate hunks changed; nothing deleted", not bad, str(bad)[:400])
    removed = [l for l in difflib.ndiff(a, b) if l.startswith("- ")]
    ok("only 5 original lines rewritten (session filter + 3 gates + checkout page)", len(removed) == 5, str(len(removed)))
    for l in removed: print("   rewritten:", l[2:].strip()[:110])
    ok("ALTER count unchanged (0 added)", newpre.count(b"ALTER TABLE") == pre.count(b"ALTER TABLE"))
    ok("Stripe mentions unchanged", newpre.count(b"Stripe") == pre.count(b"Stripe") and newpre.count(b"stripe") == pre.count(b"stripe"))
    ok("issueEmailVerification body unchanged", re.search(rb"async function issueEmailVerification[\s\S]*?\n}\n", pre).group(0) in newpre)
    pp = W / "patched_prefix.js"; pp.write_bytes(newpre)
    ok("node --check on patched prefix", subprocess.run(["node", "--check", str(pp)]).returncode == 0)
    # 3. Behaviour, flag off (as shipped) and flag on.
    for mode in ("off", "on"):
        target = pp
        if mode == "on":
            target = W / "patched_prefix_on.js"
            s = newpre.decode().replace("const VERIFY_ENFORCE = false;", "const VERIFY_ENFORCE = true;", 1)
            target.write_text(s)
        r = subprocess.run(["node", str(HERE / "behaviour.test.js"), str(target), mode], capture_output=True, text=True)
        print(r.stdout.strip()); print(r.stderr.strip()[-2000:])
        ok("behaviour tests, VERIFY_ENFORCE=%s" % ("false" if mode == "off" else "true"), r.returncode == 0 and "passed" in r.stdout)
        ok("attach line logged once (%s)" % mode, r.stdout.count("[chat106softgate] attached") == 1)
    # 4. Unpatched fixture behaves as the hard gate (baseline sanity).
    base = W / "base_prefix.js"; base.write_bytes(pre)
    r = subprocess.run(["node", "-e", """
process.env.NODE_ENV='test';process.env.DISPATCH_TEST_REQUIRE_EMAIL_VERIFICATION='1';
const m=require(process.argv[1]);const mk=(method,url,body,cookie)=>({method,url,headers:{host:'dev.test',cookie:cookie||''},body:body||'',socket:{}});
const rs=()=>{const r={headers:{},body:''};r.setHeader=(k,v)=>r.headers[k.toLowerCase()]=v;r.getHeader=k=>r.headers[k.toLowerCase()];r.writeHead=(s,h={})=>{r.status=s;Object.assign(r.headers,Object.fromEntries(Object.entries(h).map(([k,v])=>[k.toLowerCase(),v])))};r.end=b=>{if(b)r.body+=b};return r};
(async()=>{const r=rs();await m.handle(mk('POST','/__auth/subscribe','email=z%40x.test&password=password1'),r);console.log(r.status, /before checkout/.test(r.body)?'BLOCKED':'OPEN');})();
""", str(base)], capture_output=True, text=True)
    ok("baseline (unpatched) guest checkout is blocked, as on dev today", r.stdout.strip() == "200 BLOCKED", r.stdout.strip())
    # 5. Refusals.
    f2 = W / "pre_r6p.js"; f2.write_bytes(build(pre, r6o))
    r = run_patch(f2, pre); ok("refuses before r6p (r6o tail)", r.returncode != 0 and "apply deploy-chat102r6p first" in r.stderr, r.stderr.strip())
    ok("refusal leaves file untouched", f2.read_bytes() == build(pre, r6o))
    r = run_patch(f, pre); ok("refuses a second run", r.returncode != 0 and "already applied" in r.stderr, r.stderr.strip())
    f3 = W / "wrongpre.js"; f3.write_bytes(build(pre, r6p))
    r = subprocess.run([sys.executable, str(PATCH), str(f3), str(BLOCK), str(V3H2), str(R6O), str(R6P), "0" * 64, str(len(pre)), hashlib.md5(pre + v3 + r6o).hexdigest()], capture_output=True, text=True)
    ok("refuses a different prefix sha", r.returncode != 0 and "not the guarded dev prefix" in r.stderr)
    r = run_patch(f3, pre, md5_override="0" * 32); ok("refuses when prefix+v3home2+r6o md5 is not the pre-r6p server", r.returncode != 0 and "pre-r6p" in r.stderr)
    dup = pre.replace(b"AND u.email_verified=TRUE LIMIT 1) uq`;", b"AND u.email_verified=TRUE LIMIT 1) uq`;\n// AND u.email_verified=TRUE LIMIT 1)", 1)
    f4 = W / "dup.js"; f4.write_bytes(build(dup, r6p))
    r = run_patch(f4, dup); ok("refuses an ambiguous anchor", r.returncode != 0 and "matched 2 times" in r.stderr, r.stderr.strip())
    miss = pre.replace(b"Verify your email before checkout", b"Confirm your email before checkout")
    f5 = W / "miss.js"; f5.write_bytes(build(miss, r6p))
    r = run_patch(f5, miss); ok("refuses a missing anchor", r.returncode != 0, r.stderr.strip())
    ok("refusals leave files untouched", f4.read_bytes() == build(dup, r6p) and f5.read_bytes() == build(miss, r6p))
    # 6. Indentation tolerance (real dev indentation is not known exactly).
    re4 = re.sub(rb"(?m)^( +)", lambda m: b"\t" * (len(m.group(1)) // 2), pre)
    f6 = W / "tabs.js"; f6.write_bytes(build(re4, r6p))
    r = run_patch(f6, re4); ok("applies with tab indentation", r.returncode == 0, r.stderr.strip())
    if r.returncode == 0:
        p6 = W / "tabs_prefix.js"; p6.write_bytes(patched_prefix(f6))
        r = subprocess.run(["node", str(HERE / "behaviour.test.js"), str(p6), "off"], capture_output=True, text=True)
        ok("behaviour (flag off) with tab indentation", r.returncode == 0, r.stderr.strip()[-500:])
    fails = [n for n, c in results if not c]
    print("\n%d/%d checks passed" % (len(results) - len(fails), len(results)))
    shutil.rmtree(W)
    sys.exit(1 if fails else 0)
main()
