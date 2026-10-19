#!/usr/bin/env python3
"""patch_rt59c.py: client patch on chat72. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat72, the output of patch_rt59b.py:
  app.js md5 099a828e118b0f100eeb3b58c89eaf00
  index.html md5 274203635358dfe5a0e54fb274b38c34
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

The "Loading Dispatch" boot status is hidden, with aria-busy set false, once a
route has rendered. The same settle runs after client navigations and tab
switches. The node stays in the document so the attribute can be read. New
handlers use the fe72_ prefix.

Usage: python3 patch_rt59c.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "099a828e118b0f100eeb3b58c89eaf00"
EXPECT_INDEX_MD5 = "274203635358dfe5a0e54fb274b38c34"
NEED_MARKER = "// \u2500\u2500 rt59b \u2500\u2500"
LOADER = '<div class="dispatch-boot-loader" id="dispatchBootLoader" role="status" aria-live="polite">'
LOADER_BUSY = '<div class="dispatch-boot-loader" id="dispatchBootLoader" role="status" aria-live="polite" aria-busy="true">'

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// \u2500\u2500 rt59c \u2500\u2500' in s: already('rt59c already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
md5 = hashlib.md5(raw).hexdigest()
imd5 = hashlib.md5(raw_idx).hexdigest()
if md5 != EXPECT_APP_MD5:
    print('WARN md5 app.js: have %s expected %s (anchors still decide)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    print('WARN md5 index.html: have %s expected %s (anchors still decide)' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust matched %d times' % len(v))
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
print('base:', base, 'app.md5', md5, 'index.md5', imd5, '->', nxt)

def subn(src, old, new, label, n=1):
    c = src.count(old)
    if c != n: die('%s matched %d times' % (label, c))
    return src.replace(old, new)

for name in (
    'function _finishAppBoot()',
    'function nav(',
    'function _setATab(',
    'function _setInstitutionalTab(',
    'function _setNewsFilter(',
):
    if s.count(name) != 1: die('%s matched %d times' % (name, s.count(name)))
if h.count('id="dispatchBootLoader"') != 1: die('dispatchBootLoader matched %d times' % h.count('id="dispatchBootLoader"'))
if h.count(LOADER) != 1: die('boot loader markup matched %d times' % h.count(LOADER))

BLOCK = r"""// ── rt59c ──
// The boot veil is a status node ("Loading Dispatch"). Route render used to
// wait on _finishAppBoot, which only runs after /api/me. Settle as soon as a
// route or tab has painted, and keep the node so aria-busy can be read.
function fe72_isBoot(el) {
  if (!el || el.nodeType !== 1) return false;
  if (el.id === "dispatchInitError") return false;
  var t = String(el.textContent || "").replace(/\s+/g, " ").trim();
  if (!/loading dispatch/i.test(t) || t.length > 80) return false;
  if (el.id === "dispatchBootLoader") return true;
  if (el.classList && el.classList.contains("dispatch-boot-loader")) return true;
  var role = "", busy = "";
  try { role = el.getAttribute("role") || ""; } catch (e) {}
  try { busy = el.getAttribute("aria-busy") || ""; } catch (e2) {}
  return role === "status" || busy === "true";
}
function fe72_settle() {
  var nodes, i, j, el, seen, dup;
  try { document.body.classList.remove("app-booting"); } catch (e) {}
  try { document.body.setAttribute("aria-busy", "false"); } catch (e2) {}
  try {
    nodes = document.querySelectorAll("#dispatchBootLoader, .dispatch-boot-loader, [role='status'], [aria-busy='true']");
  } catch (e3) { nodes = []; }
  seen = [];
  for (i = 0; i < nodes.length; i++) {
    if (!fe72_isBoot(nodes[i])) continue;
    dup = false;
    for (j = 0; j < seen.length; j++) if (seen[j] === nodes[i]) dup = true;
    if (!dup) seen.push(nodes[i]);
  }
  for (i = 0; i < seen.length; i++) {
    el = seen[i];
    try {
      el.setAttribute("aria-busy", "false");
      el.setAttribute("aria-hidden", "true");
      el.setAttribute("aria-live", "off");
      el.hidden = true;
      el.style.setProperty("display", "none", "important");
    } catch (e4) {}
  }
}
function fe72_after() {
  try { fe72_settle(); } catch (e) {}
}
var fe72_finish0 = _finishAppBoot;
_finishAppBoot = function fe72_finish() {
  try { fe72_settle(); } catch (e) {}
};
var fe72_nav0 = nav;
nav = function fe72_nav() {
  var r;
  try { r = fe72_nav0.apply(this, arguments); }
  finally { fe72_after(); }
  return r;
};
var fe72_tab0 = _setATab;
_setATab = function fe72_setATab() {
  var r;
  try { r = fe72_tab0.apply(this, arguments); }
  finally { fe72_after(); }
  return r;
};
var fe72_inst0 = _setInstitutionalTab;
_setInstitutionalTab = function fe72_setInst() {
  var r;
  try { r = fe72_inst0.apply(this, arguments); }
  finally { fe72_after(); }
  return r;
};
var fe72_news0 = _setNewsFilter;
_setNewsFilter = function fe72_setNewsFilter() {
  var r;
  try { r = fe72_news0.apply(this, arguments); }
  finally { fe72_after(); }
  return r;
};
fe72_after();
try { requestAnimationFrame(fe72_after); } catch (e) {}
try { setTimeout(fe72_after, 0); } catch (e2) {}
"""
if not s.endswith('\n'): s += '\n'
s = s + '\n' + BLOCK
if s.count('function fe72_settle') != 1: die('fe72_settle missing after append')
if s.count('function fe72_isBoot') != 1: die('fe72_isBoot missing after append')
if s.count('function fe72_nav') != 1: die('fe72_nav missing after append')
h = subn(h, LOADER, LOADER_BUSY, 'boot loader aria-busy')
h = subn(h, 'app.js?v=%s"' % base, 'app.js?v=%s"' % nxt, 'cache bust')

def write(path, text, use_crlf):
    data = text.replace('\n', '\r\n').encode('utf-8') if use_crlf else text.encode('utf-8')
    open(path, 'wb').write(data)

if CHECK:
    print('CHECK ONLY')
    sys.exit(0)
write(APP, s, crlf)
write(IDX, h, hcrlf)
tmp = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False)
tmp.write(s); tmp.close()
r = subprocess.run(['node', '--check', tmp.name], capture_output=True, text=True)
os.unlink(tmp.name)
if r.returncode != 0:
    die('node --check failed\n' + (r.stderr or r.stdout or ''))
print('OK', nxt, 'app.md5', hashlib.md5(open(APP,'rb').read()).hexdigest(), 'index.md5', hashlib.md5(open(IDX,'rb').read()).hexdigest())
