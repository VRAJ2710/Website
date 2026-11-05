#!/usr/bin/env python3
# chat101d: public support/contact email -> vraj2710@hotmail.com (Vraj's request, 5 Nov 2026), cache tag app.js?v=chat101d.
# Plus live-bug fixes (Vraj, 5 Nov 2026): tables at phone widths scroll inside their own box instead of widening the page
# (c93 pages: a wrapper div; app views: page-level horizontal-overflow guard at <=600px); /watchlist "Daily check" button gets
# solid AA colours (white on navy, 11.6:1) in light and dark; JSON-LD publisher URL lower-cased to /in/vraj2710 (name stays Vraj Patel).
# Leaves alone: outbound data-feed User-Agent strings (SEC/official sources) and the recovery-email From (env var). Refuses a second run.
import sys
import json
S, A, I = sys.argv[1:4]
rd = lambda p: open(p, encoding="utf-8").read()
srv, app, idx = rd(S), rd(A), rd(I)
OLD, NEW = "dispatchmarket@mail.grokbot.com", "vraj2710@hotmail.com"
if '/app.js?v=chat101d"' in idx or 'const C93_CONTACT = "%s";' % NEW in srv: sys.exit("patch_c101d: already applied")
if '/app.js?v=chat101c"' not in idx or "// \u2500\u2500 chat101c \u2500\u2500" not in srv: sys.exit("patch_c101d: chat101c is not applied")
L1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)"
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101d: server.js line 1 is not the maintenance=false line")
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit("patch_c101d: %s expected %d match(es), found %d" % (tag, n, c))
    return s.replace(old, new)
# 1. the one constant behind every footer/About/Contact/Editorial standards/Corrections/Pricing mailto
srv = edit(srv, 'const C93_CONTACT = "%s";' % OLD, 'const C93_CONTACT = "%s";' % NEW, tag="C93_CONTACT")
# 2. Terms ("Questions:") and Privacy ("Contact:") copy, hard-coded mailto + visible text
srv = edit(srv, '<p>Questions: <a href=\\"mailto:%s\\">%s</a></p>' % (OLD, OLD), '<p>Questions: <a href=\\"mailto:%s\\">%s</a></p>' % (NEW, NEW), tag="terms")
srv = edit(srv, '<p>Contact: <a href=\\"mailto:%s\\">%s</a></p>' % (OLD, OLD), '<p>Contact: <a href=\\"mailto:%s\\">%s</a></p>' % (NEW, NEW), tag="privacy")
# 3. the only remaining old address is the outbound C97 data-feed User-Agent (not shown to readers)
if srv.count(OLD) != 1 or 'const C97_UA = "The Dispatch Market research (%s)";' % OLD not in srv: sys.exit("patch_c101d: unexpected leftover old address")
idx = edit(idx, '<script defer src="/app.js?v=chat101c"></script>', '<script defer src="/app.js?v=chat101d"></script>', tag="idx-token")
# 4. JSON-LD publisher URL: lower-case LinkedIn handle (display name already "Vraj Patel")
srv = edit(srv, 'name: "Vraj Patel", url: "https://www.linkedin.com/in/VRAJ2710"', 'name: "Vraj Patel", url: "https://www.linkedin.com/in/vraj2710"', n=3, tag="ld-srv")
idx = edit(idx, '"name":"Vraj Patel","url":"https://www.linkedin.com/in/VRAJ2710"', '"name":"Vraj Patel","url":"https://www.linkedin.com/in/vraj2710"', tag="ld-idx")
# 5. c93 pages: tables (other than the market-context cards) scroll inside a wrapper on phones; no page-wide sideways scroll
CSS = ("@media (max-width:599px){html{overflow-x:hidden}.c101d-tw{display:block;width:100%;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}"
       ".c101d-tw>table{margin-bottom:0}}")
JS = ("(function(){if(window.__c101d)return;window.__c101d=1;function w(){try{Array.prototype.forEach.call(document.querySelectorAll('table:not(.ctx)'),function(t){"
      "var p=t.parentNode;if(!p||(p.classList&&p.classList.contains('c101d-tw'))||t.closest('header.site'))return;var d=document.createElement('div');d.className='c101d-tw';"
      "p.insertBefore(d,t);d.appendChild(t);});}catch(e){}}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',w);else w();})();")
srv = edit(srv, "\nconst C101C_JS = ", "\n// \u2500\u2500 chat101d \u2500\u2500 phone tables scroll in their own box\nconst C101D_CSS = %s;\nconst C101D_JS = %s;\nconst C101C_JS = " % (json.dumps(CSS), json.dumps(JS)), tag="c101d-consts")
srv = edit(srv, "<style>${C101B_CSS}${C101C_CSS}</style>", "<style>${C101B_CSS}${C101C_CSS}${C101D_CSS}</style>", tag="hdr-css")
srv = edit(srv, "<script>${C101B_JS}${C101C_JS}</script></header>", "<script>${C101B_JS}${C101C_JS}${C101D_JS}</script></header>", tag="hdr-js")
# 6. app views: page-level sideways-scroll guard on phones, and AA colours for the Daily check button
if "chat101d" in app: sys.exit("patch_c101d: app already has chat101d")
ABLK = ('// \u2500\u2500 chat101d: app views never scroll sideways on phones; "Daily check" button in solid AA colours (light and dark) \u2500\u2500\n'
  '(function () {\n  try {\n    var st = document.createElement("style");\n    st.textContent =\n'
  '      "@media (max-width:600px){html.c93,html.c93 body{overflow-x:hidden!important;max-width:100%}}" +\n'
  '      "button[onclick=\\"runMorningDeskRun()\\"][style*=\\"gradient\\"]{background:#1F3A5F!important;color:#FFFFFF!important}";\n'
  '    (document.head || document.documentElement).appendChild(st);\n  } catch (e) {}\n})();\n')
app = app.rstrip("\n") + "\n" + ABLK
if srv.split("\n", 1)[0] != L1: sys.exit("patch_c101d: line 1 changed")
if "Edited by Vraj Patel" not in srv or "Not investment advice. Capital at risk." not in srv: sys.exit("patch_c101d: byline or disclaimer missing")
for p, t in ((S, srv), (A, app), (I, idx)): open(p, "w", encoding="utf-8").write(t)
print("patch_c101d: ok")
