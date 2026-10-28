#!/usr/bin/env python3
"""chat91 patch: (1) boot-time idempotent data fix for stored editorial payloads, (2) short title suffix
"| The Dispatch" / "· The Dispatch" -> "The Dispatch Market", (3) index.html asset token chat90 -> chat91.
Usage: patch_brand2.py server.js app.js index.html   (files edited in place ONLY if every assertion passes)
python3.8+ safe. Touches nothing but the three named files."""
import re, sys

BOOT_ANCHOR = "  await seedEditorialContent();\n  await sql`DELETE FROM dispatch_sessions WHERE expires_at <= NOW()`;\n"
BOOT_FIX = '''  await seedEditorialContent();
  // chat91: one-off, idempotent, bounded copy fix for payloads stored by earlier seeds (seed uses ON CONFLICT DO NOTHING,
  // so old brand text would otherwise stay). Only payload is touched; ids, versions, status, published_at, updated_at are not.
  // Never blocks boot: any error is logged and ignored. No DDL.
  try {
    const bb91Brand = await sql`UPDATE dispatch_editorial_content SET payload = replace(payload::text, 'Dispatch Markets', 'Dispatch Market')::jsonb WHERE payload::text LIKE '%Dispatch Markets%' RETURNING id`;
    const bb91Title = await sql`UPDATE dispatch_editorial_content SET payload = jsonb_set(payload, '{title}', to_jsonb(left(payload->>'title', char_length(payload->>'title') - 15) || ' | The Dispatch Market')) WHERE content_type = 'page' AND jsonb_typeof(payload->'title') = 'string' AND payload->>'title' LIKE '% | The Dispatch' RETURNING id`;
    console.log(`[chat91] editorial brand fix: ${bb91Brand.length} row(s) 'Dispatch Markets' -> 'Dispatch Market'; ${bb91Title.length} page title suffix row(s) '| The Dispatch' -> '| The Dispatch Market'`);
  } catch (bb91Err) {
    console.warn("[chat91] editorial brand fix skipped:", bb91Err && bb91Err.message ? bb91Err.message : bb91Err);
  }
  await sql`DELETE FROM dispatch_sessions WHERE expires_at <= NOW()`;
'''

# (name, compiled regex, replacement, expected count)
SERVER_RULES = [
 ("route-def titles ('| The Dispatch\",' before description)", re.compile(r'(\| The Dispatch)(",\n    description:)'), r'\1 Market\2', 5),
 ("admin dashboard <title>", re.compile(r'(Admin dashboard \\u00b7 The Dispatch)(</title>)'), r'\1 Market\2', 1),
 ("page(res, \"... · The Dispatch\") titles", re.compile(r'(page\(res, "[^"\n]+ · The Dispatch)(")'), r'\1 Market\2', 5),
 ("Pricing <title>", re.compile(r'(<title>Pricing · The Dispatch)(</title>)'), r'\1 Market\2', 1),
]
APP_RULES = [
 ("fe88 monitor docTitle suffix", re.compile(r'(Monitor \| The Dispatch)(";)'), r'\1 Market\2', 4),
]

def run_rules(name, text, rules, report):
    for label, rx, rep, n in rules:
        text, got = rx.subn(rep, text)
        if got != n:
            raise SystemExit("ABORT %s: rule '%s' replaced %d, expected %d" % (name, label, got, n))
        report.append("%s: %s: %d" % (name, label, got))
    return text

def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: patch_brand2.py server.js app.js index.html")
    sp, ap, ip = argv[1:4]
    s = open(sp, encoding="utf-8").read(); a = open(ap, encoding="utf-8").read(); i = open(ip, encoding="utf-8").read()
    report = []
    if s.count(BOOT_ANCHOR) != 1: raise SystemExit("ABORT server.js: boot anchor found %d times" % s.count(BOOT_ANCHOR))
    if "chat91" in s or "chat91" in a: raise SystemExit("ABORT: already contains chat91")
    s = s.replace(BOOT_ANCHOR, BOOT_FIX); report.append("server.js: boot data fix inserted: 1")
    s = run_rules("server.js", s, SERVER_RULES, report)
    a = run_rules("app.js", a, APP_RULES, report)
    tok_old, tok_new = 'app.js?v=chat90"', 'app.js?v=chat91"'
    if i.count(tok_old) != 1: raise SystemExit("ABORT index.html: token %s found %d times" % (tok_old, i.count(tok_old)))
    i = i.replace(tok_old, tok_new); report.append("index.html: asset token chat90 -> chat91: 1")
    # LEFT checks: no short-suffix title remains in the targeted shapes; line 1 unchanged
    left_rx = re.compile(r'(\| The Dispatch|· The Dispatch)(?! Market)(?:",\n    description:|</title>|";|")')
    for nm, t in (("server.js", s), ("app.js", a)):
        m = [x for x in left_rx.finditer(t) if "Under maintenance" not in t[x.start()-40:x.end()+40]]
        if m: raise SystemExit("ABORT %s: short suffix title still present near %r" % (nm, t[m[0].start()-60:m[0].end()+10]))
    if not s.startswith("const BB10I_MAINTENANCE_ON = true;"): raise SystemExit("ABORT: server line 1 changed")
    for p, t in ((sp, s), (ap, a), (ip, i)):
        open(p, "w", encoding="utf-8", newline="").write(t)
    print("\n".join(report)); print("patch_brand2: ok")

if __name__ == "__main__":
    main(sys.argv)
