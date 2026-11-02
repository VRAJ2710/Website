#!/usr/bin/env python3
# chat97 (on top of chat96): Light/Dark/System theme across app, site, auth and maintenance pages; gold dashboard; macro calendar;
# "What changed today"; 10-year yield from FRED DGS10; House filings newest first; guest preview covers /api/prefs. No new tables.
# Exact-count edits; any miss aborts, nothing written. usage: patch_chat97.py server.js app.js index.html
import sys, os, json
SRV, APP, IDX = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat97: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
rd = lambda f: open(os.path.join(HERE, f), encoding="utf-8").read()
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat97" in srv or "chat97" in app or "v=chat97" in idx: sys.exit("patch_chat97: already applied")
if "chat96" not in srv or "v=chat96" not in idx: sys.exit("patch_chat97: needs the chat96 files")

# ── app ──
app = edit(app, 'display: { theme: "dark", fontSize: pick(Di.fontSize, ["s", "m", "l"], "m"), reduceMotion: Di.reduceMotion === true },',
  'display: { theme: "dark", fontSize: pick(Di.fontSize, ["s", "m", "l"], "m"), reduceMotion: Di.reduceMotion === true, ...(["light", "dark", "system"].includes(Di.scheme) ? { scheme: Di.scheme } : {}) },', tag="clean-scheme")
app = edit(app, '''  const display = `${_rt17Soon("Theme: Light", "Terminal dark is the only theme for now.")}''',
  '''  const display = `<div class="rt17-h">Theme</div>${_rt17Seg("Theme", (typeof _c97Scheme === "function" ? _c97Scheme() : "system"), [["light", "Light"], ["dark", "Dark"], ["system", "System"]], "_c97SetScheme")}<div class="rt17-note">System follows your device setting. Saved on this device${signed ? " and in your account" : ""}.</div>''', tag="settings-theme")
app = edit(app, '<div class="rt17-foot">Research only · Not investment advice · <span id="rt17-save"',
  '<div class="rt17-foot"><span class="c97-disc">Research and education only. Not investment advice. Capital at risk.</span><span id="rt17-save"', tag="settings-disc")
app = edit(app, 'fe68_esc(item.filingDate || "")', 'fe68_esc(item.filingDateUk || item.filingDate || "")', n=2, tag="house-date")
app = edit(app, 'window._tdMeEmail=typeof d.email==="string"?d.email:"";', 'window._tdMeEmail=typeof d.email==="string"?d.email:"";window._tdMePreview=d.preview===true;', tag="me-preview")
app = "// chat97\n" + app + rd("app_block97.js")

# ── index: theme class before first paint, dark tokens, Calendar link, cache token ──
idx = edit(idx, "  document.documentElement.classList.add('c93');\n})();",
  "  document.documentElement.classList.add('c93');\n"
  "  try { var m = /(?:^|;\\s*)dispatch_theme=(light|dark|system)(?:;|$)/.exec(document.cookie || ''), s = m ? m[1] : localStorage.getItem('dispatch_theme'); if (!/^(light|dark|system)$/.test(s || '')) s = 'system'; var de = document.documentElement; de.classList.remove('c97-light', 'c97-dark', 'c97-system'); de.classList.add('c97-' + s); } catch (e) { document.documentElement.classList.add('c97-system'); } // chat97 theme, before paint\n"
  "})();", tag="idx-head")
CSS = rd("app_dark.css") + rd("app_c97.css").replace("\n", "")
if "</style" in CSS.lower(): sys.exit("patch_chat97: css contains </style")
idx = edit(idx, '<link rel="stylesheet" href="/c93.css?v=chat93">', '<link rel="stylesheet" href="/c93.css?v=chat93"><style id="c97-app">' + CSS + '</style>', tag="idx-css")
idx = edit(idx, '<a href="/gold/" data-c93-nav="gold">Gold</a>', '<a href="/gold/" data-c93-nav="gold">Gold</a><a href="/calendar/">Calendar</a>', tag="idx-nav")
idx = edit(idx, '<script defer src="/app.js?v=chat96"></script>', '<script defer src="/app.js?v=chat97"></script>', tag="idx-token")

# ── server: live tables take the 10-year from FRED DGS10; appended chat97 block ──
LIVE96 = rd("live96.js"); LIVE97 = rd("live97.js")
if "</script" in LIVE97.lower(): sys.exit("patch_chat97: live97.js contains </script")
srv = edit(srv, "const C96_LIVE_JS = " + json.dumps(LIVE96) + ";", "const C96_LIVE_JS = " + json.dumps(LIVE97) + "; // chat97: DGS10 first", tag="live")
srv = srv + "\n// ── chat97 ──\n" + rd("server_block97.js")
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat97: ok")
