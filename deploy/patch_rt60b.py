#!/usr/bin/env python3
"""rt60b client patch: chat74 -> chat75. Anchors decide; md5 only warns."""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "aed8eb85a623f1ad9e3383f17aeab06f"
EXPECT_INDEX_MD5 = "bde40289098e5cf3fe64e4e27e542f1d"
NEED_MARKER = "// ── rt60 ──"
REFUSE_MARKER = "// ── rt60b ──"

BLOCK = r'''
// ── rt60b ──
function fe74_admin() {
  try { return typeof fe71_who === "function" && fe71_who().admin === true; } catch (e) { return false; }
}
function fe74_groups() {
  var groups = [];
  try { groups = fe74_groups0(); } catch (e) { groups = []; }
  var book = null, i, kept = [], settings = ["settings", "Settings"];
  for (i = 0; i < groups.length; i++) if (groups[i] && groups[i].g === "Book") book = groups[i];
  if (book && book.items) {
    book.items.forEach(function (it) {
      if (it && it[0] === "settings") settings = it;
      else if (it && it[0] !== "console") kept.push(it);
    });
    book.items = kept;
  }
  var items = [settings];
  if (fe74_admin()) items.push(["console", "Console"]);
  groups.push({ g: "Account", items: items });
  return groups;
}
try { FE71_BLURB.console = "Console: site health, users and settings (admin only)"; } catch (e) {}
try {
  NAV_ICONS.console = '<rect x="3.5" y="4.5" width="17" height="15" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M7 9l3 2.2L7 13.4M12 14.5h5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>';
} catch (e) {}
try {
  var fe74_tile0 = fe71_tile;
  fe71_tile = function (id, label, group) {
    if (id === "console" && !fe74_admin()) return "";
    var html = fe74_tile0.apply(this, arguments);
    if (id !== "console") return html;
    return html.replace("<button ", '<a href="/__admin" ').replace("</button>", "</a>");
  };
} catch (e) {}
try {
  var fe74_go0 = fe71_go;
  fe71_go = function (id) {
    if (id === "console") return;
    return fe74_go0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe74_groups0 = fe71_groups;
  fe71_groups = fe74_groups;
} catch (e) {}
function fe74_css() {
  if (document.getElementById("fe74-css")) return;
  var st = document.createElement("style");
  st.id = "fe74-css";
  st.textContent = [
    ".fe71 a.fe71-tile{text-decoration:none;color:inherit}",
    ".fe71 [data-fe71-group='Account'] .fe71-grid{grid-template-columns:1fr!important}",
    ".fe71 [data-fe71-group='Account'] .fe71-tile{grid-column:1 / -1!important;height:auto!important;min-height:72px!important;overflow:hidden!important}",
    ".fe71 [data-fe71-group='Account'] .fe71-d{-webkit-line-clamp:3!important}"
  ].join("");
  document.head.appendChild(st);
}
try { fe74_css(); } catch (e) {}
'''


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def md5(raw):
    return hashlib.md5(raw).hexdigest()


def read_text(path):
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    return raw, raw.replace(b"\r\n", b"\n").decode("utf-8"), crlf


def write_text(path, text, crlf):
    data = text.encode("utf-8")
    if crlf:
        data = data.replace(b"\n", b"\r\n")
    path.write_bytes(data)


def paths():
    if len(sys.argv) >= 3:
        return pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if len(sys.argv) == 2:
        d = pathlib.Path(sys.argv[1])
        if d.is_dir():
            return d / "app.js", d / "index.html"
        return d, d.with_name("index.html")
    cwd = pathlib.Path.cwd()
    return cwd / "app.js", cwd / "index.html"


def main():
    app_path, index_path = paths()
    if not app_path.is_file() or not index_path.is_file():
        die("missing app.js or index.html")
    app_raw, app, app_crlf = read_text(app_path)
    index_raw, index, index_crlf = read_text(index_path)
    app_sum = md5(app_raw)
    index_sum = md5(index_raw)
    if app_sum != EXPECT_APP_MD5:
        print("WARN app.js md5 %s expected %s" % (app_sum, EXPECT_APP_MD5))
    if index_sum != EXPECT_INDEX_MD5:
        print("WARN index.html md5 %s expected %s" % (index_sum, EXPECT_INDEX_MD5))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    anchors = [
        "function fe71_who(",
        "function fe71_tile(",
        "function fe71_groups(",
        "function fe71_go(",
    ]
    for a in anchors:
        n = app.count(a)
        if n != 1:
            die("anchor %s count %s" % (a, n))
    if index.count('app.js?v=chat74"') != 1:
        die("cache bust anchor missing")
    app = app + BLOCK
    if app.count("function fe74_admin(") != 1:
        die("fe74_admin count")
    if app.count("function fe74_groups(") != 1:
        die("fe74_groups count")
    index = index.replace('app.js?v=chat74"', 'app.js?v=chat75"', 1)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
