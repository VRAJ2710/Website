#!/usr/bin/env python3
"""rt63b client patch on live chat88 (app.js md5 dfd17c65...). Anchors decide; md5 only warns.

P1  Cold direct loads of /research/capital-sustainability[/{ticker}|/method]
    were redirected by the boot nav at the end of app.js:
        nav(_publicPageFromPath(location.pathname) || "home", {history:"replace"})
    That line runs at script execution; the fe88 wrapper of _publicPageFromPath
    is only installed later in fe88_boot. So "/research/capital-sustainability"
    resolved to "research" and _syncPublicPageUrl() rewrote the URL to /research/,
    and the ticker/method paths resolved to null -> "home" -> "/".
    Fix: a hoisted, dependency-free fe89_isMonitorPath() and a boot nav that,
    for a monitor path, opens "research" with history:"none" (URL untouched).
P2  Radar table caption was a table-caption inside a display:block table at
    narrow widths (one-word-wide column). Caption is now display:block, the card
    layout runs up to 1439px, and the desktop table gets explicit column widths.
P3x /dashboard/ (admin, any zoom): html.fe77-dash pinned .sidebar at top:0 over the
    tape/status/intel bars (fe77 qaCss, same in chat86). fe89_sbPlace() (called from
    fe77_dashLock + resize) sets --fe89-sbtop = .terminal-wrap top; fe89 CSS starts
    the fixed rail there. Short viewports (<=860px high) get a tighter rail so it
    fits without its own scrollbar (also fixes / at 150% zoom).
P4x Desktop back/forward inside the monitor lost the overlay (URL right, page wrong):
    fe88_paint called _showOverlay on an existing researchOv, which closes it.
    fe89_ovPaint() swaps the body in place instead.
P2x Radar table: <1440px it becomes a grid of label/value cells per row (no
    squeezed columns); >=1440px fixed layout with wider column shares.
Optional 2nd arg index.html: bumps app.js?v=chat88 -> chat89 (idempotent).
Usage: patch_rt63b.py <app.js> [index.html]   Second apply prints REFUSE, exit 0.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "dfd17c656fe880907efb073be5e03a3c"
REFUSE_MARKER = "// ── rt63b ──"

A1_OLD = "function _publicPageFromPath(pathname) {\n"
A1_NEW = r"""// ── rt63b ──
// fe89: the boot nav runs before fe88_boot wraps _publicPageFromPath, so the
// monitor paths must be recognised here, with no dependency on fe88 vars.
function fe89_isMonitorPath(pathname) {
  return /^\/research\/capital-sustainability(?:\/|$)/.test(String(pathname || ""));
}
function fe89_bootNav() {
  const mon = fe89_isMonitorPath(location.pathname);
  nav(mon ? "research" : (_publicPageFromPath(location.pathname) || "home"), { history: mon ? "none" : "replace" });
}
// _showOverlay() CLOSES an overlay that already exists, so every second desktop
// fe88_paint (skeleton -> result, or popstate -> repaint) toggled the monitor off.
function fe89_ovPaint(html) {
  const ex = document.getElementById("researchOv");
  const body = ex && ex.querySelector(".term-overlay-body");
  if (!body) { _showOverlay("researchOv", "Capital Sustainability Monitor", html); return; }
  body.innerHTML = html;
  ex.scrollTop = 0;
  const card = ex.querySelector(".term-overlay-card");
  if (card) card.scrollTop = 0;
  body.scrollTop = 0;
}
""" + A1_OLD

A2_OLD = '  else nav(_publicPageFromPath(location.pathname) || "home", { history: "replace" });\n'
A2_NEW = '  else fe89_bootNav();\n'

C1_OLD = "@media(max-width:759px){.fe88-table,"
C1_NEW = "@media(max-width:1439px){.fe88-table caption{display:block;width:100%;padding:0 0 10px;text-align:left}.fe88-table,"

C2_OLD = "@media(prefers-reduced-motion:reduce){.fe88,.fe88 *{animation:none !important;transition:none !important}}"
CSS_ADD = (
    ".fe88-table th,.fe88-table td{white-space:normal;min-width:0;overflow-wrap:break-word}"
    ".fe88-pick label{flex:1 0 100%}"
    ".fe88-radar{max-width:100%;min-width:0}"
    "@media(min-width:760px) and (max-width:1439px){"
    ".fe88-table tr{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:2px 18px;padding:12px}"
    '.fe88-table td[data-label="Why it is on the radar"],.fe88-table td[data-label="As of"]{grid-column:1/-1}}'
    "@media(min-width:1440px){.fe88-table{table-layout:fixed}"
    ".fe88-table thead th:nth-child(1){width:5%}.fe88-table thead th:nth-child(2){width:15%}"
    ".fe88-table thead th:nth-child(3){width:7%}.fe88-table thead th:nth-child(4){width:18%}"
    ".fe88-table thead th:nth-child(5){width:7%}.fe88-table thead th:nth-child(6){width:10%}"
    ".fe88-table thead th:nth-child(7){width:9%}.fe88-table thead th:nth-child(8){width:8%}"
    ".fe88-table thead th:nth-child(9){width:8%}.fe88-table thead th:nth-child(10){width:13%}}"
)
C2_NEW = CSS_ADD + C2_OLD

D1_OLD = "  try { window.scrollTo(0, 0); } catch (e4) {}\n}\ntry {\n  var fe77_ov0 = _showOverlay;"
D1_NEW = ("  try { window.scrollTo(0, 0); } catch (e4) {}\n  try { fe89_sbPlace(); } catch (e5) {}\n}\n"
          "function fe89_sbPlace() {\n"
          "  const on = document.documentElement.classList.contains(\"fe77-dash\");\n"
          "  const wrap = document.querySelector(\".terminal-wrap\");\n"
          "  if (!on || !wrap || window.innerWidth < 768) return;\n"
          "  const y = Math.max(0, Math.round(wrap.getBoundingClientRect().top + (window.scrollY || 0)));\n"
          "  document.documentElement.style.setProperty(\"--fe89-sbtop\", y + \"px\");\n"
          "}\n"
          "function fe89_css() {\n"
          "  if (document.getElementById(\"fe89-css\")) return;\n"
          "  const st = document.createElement(\"style\");\n"
          "  st.id = \"fe89-css\";\n"
          "  st.textContent = \"@media (min-width:768px){html.fe77-dash body .sidebar{top:var(--fe89-sbtop,0px)!important;min-height:0!important;height:calc(100vh - var(--fe89-sbtop,0px))!important;max-height:calc(100vh - var(--fe89-sbtop,0px))!important}}\" +\n"
          "    \"@media (min-width:768px) and (max-height:860px){body .sidebar{padding-top:12px;padding-bottom:10px}.sidebar .sb-item.sb-primary{min-height:31px;padding-top:5px;padding-bottom:5px}.sidebar .sb-spacer{height:8px}}\";\n"
          "  document.head.appendChild(st);\n"
          "  window.addEventListener(\"resize\", function () { try { fe89_sbPlace(); } catch (e) {} });\n"
          "}\n"
          "try {\n  var fe77_ov0 = _showOverlay;")

D2_OLD = "try { fe77_qaCss(); } catch (e) {}\n"
D2_NEW = D2_OLD + "try { fe89_css(); } catch (e) {}\n"

E1_OLD = 'try { _showOverlay("researchOv", "Capital Sustainability Monitor", html); painted = true; }'
E1_NEW = 'try { fe89_ovPaint(html); painted = true; }'

EDITS = [("boot nav fn", A1_OLD, A1_NEW), ("boot nav call", A2_OLD, A2_NEW),
         ("css breakpoint", C1_OLD, C1_NEW), ("css add", C2_OLD, C2_NEW),
         ("dash sidebar fn", D1_OLD, D1_NEW), ("dash css call", D2_OLD, D2_NEW),
         ("monitor overlay repaint", E1_OLD, E1_NEW)]

IDX_OLD = 'app.js?v=chat88"'
IDX_NEW = 'app.js?v=chat89"'


def die(msg):
    print("FAIL", msg)
    sys.exit(1)


def read_text(path):
    raw = path.read_bytes()
    return raw, raw.replace(b"\r\n", b"\n").decode("utf-8"), b"\r\n" in raw


def write_text(path, text, crlf):
    data = text.encode("utf-8")
    if crlf:
        data = data.replace(b"\n", b"\r\n")
    path.write_bytes(data)


def check_js(text, label):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(text)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die(label + "\n" + chk.stdout + chk.stderr)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2:
        print("usage: patch_rt63b.py <app.js> [index.html]")
        return 2
    app_path = pathlib.Path(sys.argv[1])
    index_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not app_path.is_file():
        die("missing app.js")
    app_raw, app, crlf = read_text(app_path)
    sm = hashlib.md5(app_raw).hexdigest()
    if sm != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (sm, EXPECT_APP_MD5))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    for name, old, _new in EDITS:
        if app.count(old) != 1:
            die("anchor count %d for %s" % (app.count(old), name))
    for _name, old, new in EDITS:
        app = app.replace(old, new, 1)
    if app.count(REFUSE_MARKER) != 1 or app.count("fe89_bootNav()") != 2:
        die("post-edit markers")
    check_js(app, "node --check failed")
    print("node --check ok")
    back = app.replace("\n", "\r\n").replace("\r\n", "\n")
    if back != app:
        die("crlf roundtrip")
    idx = None
    if index_path is not None:
        if not index_path.is_file():
            die("missing index.html")
        _iraw, itext, icrlf = read_text(index_path)
        if itext.count(IDX_OLD) == 1:
            idx = (index_path, itext.replace(IDX_OLD, IDX_NEW, 1), icrlf)
        elif itext.count(IDX_NEW) == 1 and IDX_OLD not in itext:
            print("index already chat89")
        else:
            die("index cache token anchor missing")
    write_text(app_path, app, crlf)
    if idx:
        write_text(*idx)
        print("index token chat88 -> chat89")
    print("patched", app_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
