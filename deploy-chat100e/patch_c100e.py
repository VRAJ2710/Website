#!/usr/bin/env python3
# chat100e: byline "Edited by Vraj Patel" (no ", London") everywhere it appears, and the one-sentence bio.
# Applies on top of the LIVE chat100d build (server 15ecc241, app 0e4bb0e3, index b0961c77). Exact-count edits only.
import sys
S, A, I = sys.argv[1:4]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx = rd(S), rd(A), rd(I)
if "/app.js?v=chat100e\"" in idx: sys.exit("patch_c100e: already applied")
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit("patch_c100e: %s expected %d match(es), found %d" % (tag, n, c))
    return s.replace(old, new)
OLD_BIO = "Vraj Patel founded The Dispatch Market to give independent investors a careful, sourced read on gold and macro. He edits every piece from London."
NEW_BIO = "Vraj Patel founded The Dispatch Market to give independent investors a careful, sourced read on gold and macro."
# server.js: the shared byline constant (guest About card, /about and /standards bylines, article/brief bylines via
# c96Byline, home meta description), the contact block, the block comment, the guest About bio
srv = edit(srv, 'const C93_EDITOR = "Edited by Vraj Patel, London";', 'const C93_EDITOR = "Edited by Vraj Patel";', tag="srv-editor")
srv = edit(srv, "<br>Edited by Vraj Patel, London. Not investment advice.", "<br>Edited by Vraj Patel. Not investment advice.", tag="srv-contact")
srv = edit(srv, '// 2) About: founder card with photo, "Edited by Vraj Patel, London" and', '// 2) About: founder card with photo, "Edited by Vraj Patel" and', tag="srv-comment")
srv = edit(srv, '<p class="c100b-bio">' + OLD_BIO + '</p>', '<p class="c100b-bio">' + NEW_BIO + '</p>', tag="srv-bio")
# app.js: footer brand byline, app About bio, block comment, app About byline
app = edit(app, "The Dispatch Market · Edited by Vraj Patel, London${upd", "The Dispatch Market · Edited by Vraj Patel${upd", tag="app-foot")
app = edit(app, '<p class="rt49-bio">' + OLD_BIO + '</p>', '<p class="rt49-bio">' + NEW_BIO + '</p>', tag="app-bio")
app = edit(app, '// constant in server.js), "Edited by Vraj Patel, London" and', '// constant in server.js), "Edited by Vraj Patel" and', tag="app-comment")
app = edit(app, '<div class="rt49-by">Edited by Vraj Patel, London</div>', '<div class="rt49-by">Edited by Vraj Patel</div>', tag="app-by")
# index.html: legacy About byline and the cache tag
idx = edit(idx, '<div class="about-role">Edited by Vraj Patel, London</div>', '<div class="about-role">Edited by Vraj Patel</div>', tag="idx-by")
idx = edit(idx, '<script defer src="/app.js?v=chat100d"></script>', '<script defer src="/app.js?v=chat100e"></script>', tag="idx-token")
# guards: none of the removed wording may remain anywhere
for nm, t in ((S, srv), (A, app), (I, idx)):
    for bad in ("Edited by Vraj Patel, London", "edits every piece from London", "He edits every piece", "writes the research", "builds the site", "builds the platform", "linkedin.com/company/"):
        if bad in t: sys.exit("patch_c100e: forbidden wording %r left in %s" % (bad, nm))
for nm, t in ((S, srv), (A, app)):
    if NEW_BIO not in t: sys.exit("patch_c100e: new bio missing in " + nm)
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c100e: ok")
