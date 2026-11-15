#!/usr/bin/env python3
"""chat106softgate: turn the email-verification checkout/sign-up gate into a reminder.

Applies AFTER deploy-chat102r6p. Expected root layout (exact bytes):
  PREFIX (fef1da0 prefix, sha256 PRE_SHA, PRE_LEN bytes)
  + chat105v3home2 block (exact bytes)
  + r6p scrub block (exact bytes, starts at the single last-write scrub marker, runs to EOF)
Consistency: PREFIX + v3home2 block + r6o scrub block must have md5 PRE_R6P_MD5 (the pre-r6p dev server).
Only PREFIX is edited. Every edit must match exactly once; otherwise nothing is written.
Usage: patch_chat106softgate.py server.js block.js v3home2.js r6o.js r6p.js PRE_SHA PRE_LEN PRE_R6P_MD5
"""
import hashlib, pathlib, re, sys

MARKER = b"// chat102r6c last-write scrub."
ATTACH = "[chat106softgate] attached"


def fail(msg):
    sys.exit("chat106softgate patch refused: " + msg)


def norm(b):
    return b.rstrip(b"\n") + b"\n"


def sub_once(text, pattern, repl, label, flags=0):
    rx = re.compile(pattern, flags)
    hits = rx.findall(text)
    if len(hits) != 1:
        fail("%s: anchor matched %d times (need exactly 1)" % (label, len(hits)))
    out, n = rx.subn(repl, text, count=1)
    if n != 1 or out == text:
        fail("%s: substitution did not apply" % label)
    print("edit ok:", label)
    return out


def main():
    if len(sys.argv) != 9:
        fail("usage: server.js block.js v3home2.js r6o.js r6p.js PRE_SHA PRE_LEN PRE_R6P_MD5")
    server = pathlib.Path(sys.argv[1])
    block = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
    v3h2 = norm(pathlib.Path(sys.argv[3]).read_bytes())
    r6o = pathlib.Path(sys.argv[4]).read_bytes()
    r6p = pathlib.Path(sys.argv[5]).read_bytes()
    pre_sha, pre_len, pre_r6p_md5 = sys.argv[6], int(sys.argv[7]), sys.argv[8]
    data = server.read_bytes()

    if ATTACH.encode() in data:
        fail("chat106softgate is already applied")
    if block.count(ATTACH) != 1:
        fail("block does not carry exactly one attach line")
    if data.count(MARKER) != 1:
        fail("expected exactly one last-write scrub marker")
    m = data.index(MARKER)
    tail = data[m:]
    if tail == r6o:
        fail("the r6o scrub is still in place: apply deploy-chat102r6p first, then this installer")
    if tail != r6p:
        fail("bytes from the scrub marker to EOF are not the r6p block (sha256 %s, %d bytes)" % (hashlib.sha256(tail).hexdigest(), len(tail)))
    if data.count(v3h2) != 1:
        fail("the chat105v3home2 block is not present exactly once (byte-exact)")
    s = data.index(v3h2)
    if s + len(v3h2) != m:
        fail("the chat105v3home2 block does not end at the scrub marker")
    pre = data[:s]
    ps = hashlib.sha256(pre).hexdigest()
    if ps != pre_sha or len(pre) != pre_len:
        fail("prefix %s/%d is not the guarded dev prefix %s/%d" % (ps, len(pre), pre_sha, pre_len))
    recon = hashlib.md5(pre + v3h2 + r6o).hexdigest()
    if recon != pre_r6p_md5:
        fail("prefix + v3home2 + r6o md5 %s is not the pre-r6p dev server %s" % (recon, pre_r6p_md5))
    print("root is post-r6p: md5", hashlib.md5(data).hexdigest(), "bytes", len(data))
    print("prefix sha256", ps, "bytes", len(pre))

    t = pre.decode("utf-8")
    for name in ("VERIFY_ENFORCE", "c106sg"):
        if name in t:
            fail("%s already present in the prefix" % name)
    # Preconditions that the edits rely on.
    if len(re.findall(r"^function withAssetVersion\(html\) \{", t, re.M)) != 1:
        fail("function withAssetVersion(html) is not declared exactly once at top level")
    if len(re.findall(r"^async function issueEmailVerification\(user\) \{", t, re.M)) != 1:
        fail("issueEmailVerification is not declared exactly once")
    if len(re.findall(r"if \(!user\.emailVerified\) \{", t)) != 2:
        fail("expected exactly two `if (!user.emailVerified) {` gates (sign-in and checkout)")

    # E0: the soft-gate block, right after the verification TTL constants.
    t = sub_once(t, r"(const EMAIL_VERIFICATION_TTL_SECONDS = EMAIL_VERIFICATION_TTL_HOURS \* 60 \* 60;[^\n]*\n)",
                 lambda mm: mm.group(1) + block.rstrip("\n") + "\n", "E0 insert soft-gate block")
    # E1: session lookup accepts unverified accounts unless VERIFY_ENFORCE.
    t = sub_once(t, r"AND u\.email_verified\s*=\s*TRUE(\s+LIMIT 1\))",
                 lambda mm: "AND (u.email_verified=TRUE OR ${VERIFY_ENFORCE ? 0 : 1}=1)" + mm.group(1),
                 "E1 session lookup")
    # E2: register, existing unverified account with the right password: sign in and resend (soft mode).
    t = sub_once(t, r"(\n([ \t]*))(if \(!existing\.emailVerified && validPassword\(password, existing\.passwordHash\)\) \{)",
                 lambda mm: mm.group(1) + "if (!VERIFY_ENFORCE && !existing.emailVerified && validPassword(password, existing.passwordHash)) { // chat106softgate"
                 + mm.group(1) + "  await c106sgSend(existing, \"register-again\");"
                 + mm.group(1) + "  await setSession(req, res, existing, cookieValue(req, \"dispatch_session\"));"
                 + mm.group(1) + "  res.writeHead(302, { Location: \"/\" });"
                 + mm.group(1) + "  return res.end();"
                 + mm.group(1) + "}" + mm.group(1) + mm.group(3),
                 "E2 register existing unverified")
    # E3: register, new account: the verify-first page only when enforcing; otherwise send and continue.
    t = sub_once(t, r"(\n([ \t]*))if \(verificationRequired\) \{(\s*const delivered = await issueEmailVerification\(user\);\s*return page\([\s\S]*?\);\s*\}[ \t]*\n)",
                 lambda mm: mm.group(1) + "if (verificationRequired && VERIFY_ENFORCE) {" + mm.group(3)
                 + mm.group(2) + "if (verificationRequired && !VERIFY_ENFORCE && !user.emailVerified) await c106sgSend(user, \"register\"); // chat106softgate\n",
                 "E3 register new account")
    # E4: sign-in gate only when enforcing.
    t = sub_once(t, r"if \(!user\.emailVerified\) \{(\s*const delivered = await issueEmailVerification\(user\);\s*return page\(res, \"[^\"]*\", delivered\s*\?\s*\"[^\"]*Your account is not active yet)",
                 lambda mm: "if (!user.emailVerified && VERIFY_ENFORCE) { // chat106softgate" + mm.group(1),
                 "E4 sign-in gate")
    # E5: checkout gate only when enforcing; a new unverified account still gets its email and goes on to checkout.
    t = sub_once(t, r"(\n([ \t]*))if \(!user\.emailVerified\) \{(\s*const delivered = await issueEmailVerification\(user\);\s*return page\(res, \"[^\"]*\", delivered\s*\?\s*\"[^\"]*Verify your email before checkout)",
                 lambda mm: mm.group(1) + "if (!VERIFY_ENFORCE && accountCreated && !user.emailVerified) await c106sgSend(user, \"checkout\"); // chat106softgate"
                 + mm.group(1) + "if (!user.emailVerified && VERIFY_ENFORCE) {" + mm.group(3),
                 "E5 checkout gate")
    # E6: reminder on the signed-in checkout page.
    t = sub_once(t, r"(if \(user\) return page\(res, \"Premium[^\"]*\", )(`<h1>PREMIUM ACCESS</h1><p>Continue to Stripe Checkout)",
                 lambda mm: mm.group(1) + "c106sgReminderHtml(user) + " + mm.group(2),
                 "E6 checkout page reminder")
    # E7: resend / status / reminder.js routes just before the existing /__auth/verify GET route.
    t = sub_once(t, r"(\n([ \t]*))(if \(p === \"/__auth/verify\" && req\.method === \"GET\"\) \{)",
                 lambda mm: mm.group(1) + "if (p.startsWith(\"/__auth/verify/\") && await c106sgRoute(p, req, res)) return; // chat106softgate"
                 + mm.group(1) + mm.group(3),
                 "E7 routes")

    if t.count(ATTACH) != 1:
        fail("patched prefix does not carry exactly one attach line")
    if len(re.findall(r"if \(!user\.emailVerified\) \{", t)) != 0:
        fail("an unconditional emailVerified gate is still present")
    for needle in ("ALTER" + " TABLE", "DROP" + " TABLE", "TRUNC" + "ATE"):
        if t.count(needle) != pre.decode("utf-8").count(needle):
            fail("DDL count changed for " + needle)
    for needle in ("stripe", "Stripe", "STRIPE", "c97AiRank", "aiProviderStatus", "deliverVerificationEmail", "email_verified BOOLEAN"):
        a = pre.decode("utf-8").count(needle)
        b = t.count(needle) - block.count(needle)
        if a != b:
            fail("unexpected change in occurrences of %r (%d -> %d)" % (needle, a, b))
    new_pre = t.encode("utf-8")
    out = new_pre + v3h2 + r6p
    if out[len(new_pre):] != v3h2 + r6p:
        fail("v3home2 + r6p tail changed")
    server.write_bytes(out)
    print("new prefix sha256", hashlib.sha256(new_pre).hexdigest(), "bytes", len(new_pre))
    print("new server md5", hashlib.md5(out).hexdigest(), "bytes", len(out))


if __name__ == "__main__":
    main()
