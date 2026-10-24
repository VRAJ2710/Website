#!/usr/bin/env python3
"""rt62g client patch: chat83b -> chat84. Anchors decide; md5 only warns.

Admin Home pegged the main thread. _quoteMeta asked fe83f_pickDay for the
session day, fe83f_marketClosed asked fe78_isClosed, that asked
fe66_closedQuote, that asked hasSyncedQuote, and hasSyncedQuote called
_quoteMeta again. A saved price (an admin session has one) makes the
predicate call _quoteMeta, so the cycle never returns. The load event, the
header clock and the panel fill never get a turn.

The closed check now reads the quote bag and the session clock only.
_quoteMeta refuses to re-enter its day rewrite. The rss-feed dedupe settles
within 15s and drops a failed entry so a retry can run. The post-paint
pass is a timer, so one section cannot starve the load event.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

EXPECT_APP_MD5 = "f63c681c5f366e2185e36dd7d4ccd23c"
EXPECT_INDEX_PREFIX = "e88590c7"
NEED_MARKER = "// ── rt62f ──"
REFUSE_MARKER = "// ── rt62g ──"

BLOCK = r"""
// ── rt62g ──
// fe84: closed-session day lookup must not re-enter _quoteMeta.
// The rss-feed cache settles (15s) and a failed entry is dropped.
"""


def die(msg):
    print("FAIL", msg)
    sys.exit(1)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("%s count %s" % (label, n))
    return text.replace(old, new, 1)


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


def anchors(app):
    app = once(
        app,
        """function fe83f_fixSigns(s) {
  var t = String(s == null ? "" : s);
  var prev;
  do {
    prev = t;
    t = t.replace(/\\+\\s*\\(\\s*\\+\\s*-(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "-$1");
    t = t.replace(/\\+\\s*\\(\\s*-(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "-$1");
    t = t.replace(/\\+\\s*\\(\\s*\\+(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "+$1");
    t = t.replace(/\\(\\s*\\+\\s*-(\\d)/g, "(-$1");
    t = t.replace(/\\+\\s*-(\\d)/g, "-$1");
    t = t.replace(/--(\\d)/g, "-$1");
  } while (t !== prev);
  return t;
}""",
        """function fe83f_fixSigns(s) {
  var t = String(s == null ? "" : s);
  var prev, n = 0;
  do {
    prev = t;
    t = t.replace(/\\+\\s*\\(\\s*\\+\\s*-(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "-$1");
    t = t.replace(/\\+\\s*\\(\\s*-(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "-$1");
    t = t.replace(/\\+\\s*\\(\\s*\\+(\\d[\\d,]*(?:\\.\\d+)?%?)\\)/g, "+$1");
    t = t.replace(/\\(\\s*\\+\\s*-(\\d)/g, "(-$1");
    t = t.replace(/\\+\\s*-(\\d)/g, "-$1");
    t = t.replace(/--(\\d)/g, "-$1");
    if (++n > 8) break;
  } while (t !== prev);
  return t;
}""",
        "fixSigns cap",
    )
    app = once(
        app,
        """function fe83f_marketClosed(tk) {
  try { if (typeof fe78_isClosed === "function" && fe78_isClosed(tk)) return true; } catch (e) {}
  try { if (typeof _rt18MarketOpen === "function") return !_rt18MarketOpen(tk); } catch (e2) {}
  return false;
}""",
        """function fe83f_marketClosed(tk) {
  // fe78_isClosed calls fe66_closedQuote, which calls hasSyncedQuote, which calls _quoteMeta.
  // _quoteMeta calls fe83f_pickDay, which calls this. Read the bag and the session clock only.
  try {
    var b = typeof fe78_bag === "function" ? fe78_bag(tk) : null;
    if (b && (b.status === "closed" || b.marketOpen === false)) return true;
  } catch (e) {}
  try {
    var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null;
    if (y && (y.status === "closed" || y.marketOpen === false)) return true;
  } catch (e2) {}
  try { if (typeof _rt18MarketOpen === "function") return !_rt18MarketOpen(tk); } catch (e3) {}
  return false;
}""",
        "market closed",
    )
    app = once(
        app,
        """  var fe83f_qm0 = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe83f_qm0.apply(this, arguments);
    try {
      var day = fe83f_pickDay(tk);
      if (day && m && m.detail) m.detail = String(m.detail).replace(/\\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\b/, day);
    } catch (e) {}
    return m;
  };""",
        """  var fe83f_qm0 = _quoteMeta;
  var fe83f_qmBusy = false;
  _quoteMeta = function (tk) {
    if (fe83f_qmBusy) return fe83f_qm0.apply(this, arguments);
    fe83f_qmBusy = true;
    try {
      var m = fe83f_qm0.apply(this, arguments);
      try {
        var day = fe83f_pickDay(tk);
        if (day && m && m.detail) m.detail = String(m.detail).replace(/\\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\\b/, day);
      } catch (eDay) {}
      return m;
    } finally {
      fe83f_qmBusy = false;
    }
  };""",
        "quote meta guard",
    )
    app = once(
        app,
        """  try {
    if (typeof queueMicrotask === "function") queueMicrotask(run);
    else setTimeout(run, 0);
  } catch (e) { fe83f_paintQueued = false; }""",
        """  try {
    // A microtask storm here starves the load event and the header clock. A timer yields.
    setTimeout(run, 0);
  } catch (e) { fe83f_paintQueued = false; }""",
        "paint timer",
    )
    app = once(
        app,
        """function fe83f_rssFetch(input, init) {
  var url = "";
  try { url = typeof input === "string" ? input : (input && input.url) || ""; } catch (e0) { url = ""; }
  var key = fe83f_rssKey(url);
  if (!key) {
    var plain = fe83f_rssFetch.orig || window.fetch.bind(window);
    return plain(input, init);
  }
  if (!fe83f_rssFetch.map) fe83f_rssFetch.map = Object.create(null);
  var hit = fe83f_rssFetch.map[key];
  if (hit) return hit.then(fe83f_rssResponse);
  if (!fe83f_rssFetch.orig) fe83f_rssFetch.orig = window.fetch.bind(window);
  var net = fe83f_rssFetch.orig(input, init);
  var savedP = Promise.resolve(net).then(function (r) {
    return r.text().then(function (t) {
      return { status: r.status, body: t, type: (r.headers && r.headers.get && r.headers.get("content-type")) || "application/xml" };
    });
  }, function (err) {
    delete fe83f_rssFetch.map[key];
    throw err;
  });
  fe83f_rssFetch.map[key] = savedP;
  return savedP.then(fe83f_rssResponse, function (err) {
    delete fe83f_rssFetch.map[key];
    throw err;
  });
}""",
        """function fe84_rssSettle(key, net) {
  var timer = 0;
  var timed = new Promise(function (_ok, reject) {
    timer = setTimeout(function () { reject(new Error("rss-feed timeout")); }, 15000);
  });
  return Promise.race([
    Promise.resolve(net).then(function (r) {
      return r.text().then(function (t) {
        return { status: r.status, body: t, type: (r.headers && r.headers.get && r.headers.get("content-type")) || "application/xml" };
      });
    }),
    timed
  ]).then(function (saved) {
    if (timer) clearTimeout(timer);
    if (!saved || !(saved.status >= 200 && saved.status < 400)) delete fe83f_rssFetch.map[key];
    return saved;
  }, function (err) {
    if (timer) clearTimeout(timer);
    delete fe83f_rssFetch.map[key];
    throw err;
  });
}
function fe83f_rssFetch(input, init) {
  var url = "";
  try { url = typeof input === "string" ? input : (input && input.url) || ""; } catch (e0) { url = ""; }
  var key = fe83f_rssKey(url);
  if (!key) {
    var plain = fe83f_rssFetch.orig || window.fetch.bind(window);
    return plain(input, init);
  }
  if (!fe83f_rssFetch.map) fe83f_rssFetch.map = Object.create(null);
  var hit = fe83f_rssFetch.map[key];
  if (hit) return hit.then(fe83f_rssResponse);
  if (!fe83f_rssFetch.orig) fe83f_rssFetch.orig = window.fetch.bind(window);
  var savedP = fe84_rssSettle(key, fe83f_rssFetch.orig(input, init));
  fe83f_rssFetch.map[key] = savedP;
  return savedP.then(fe83f_rssResponse, function (err) {
    delete fe83f_rssFetch.map[key];
    throw err;
  });
}""",
        "rss settle",
    )
    return app


def run_unit(app_text):
    if app_text.count("var fe83f_qmBusy = false;") != 1:
        die("guard missing")
    if app_text.count("rss-feed timeout") != 1 or app_text.count("}, 15000);") < 1:
        die("rss timeout missing")
    if "fe78_isClosed(tk)" in app_text.split("function fe83f_marketClosed")[1].split("function fe83f_pickDay")[0]:
        die("closed cycle still wired")
    if "queueMicrotask(run)" in app_text:
        die("paint still microtask")
    src = r"""
function assert(cond, msg) { if (!cond) { console.error("FAIL", msg); process.exit(1); } }
function fe83f_fixSigns(s) {
  var t = String(s == null ? "" : s);
  var prev, n = 0;
  do {
    prev = t;
    t = t.replace(/\+\s*\(\s*\+\s*-(\d[\d,]*(?:\.\d+)?%?)\)/g, "-$1");
    t = t.replace(/\+\s*\(\s*-(\d[\d,]*(?:\.\d+)?%?)\)/g, "-$1");
    t = t.replace(/\+\s*\(\s*\+(\d[\d,]*(?:\.\d+)?%?)\)/g, "+$1");
    t = t.replace(/\(\s*\+\s*-(\d)/g, "(-$1");
    t = t.replace(/\+\s*-(\d)/g, "-$1");
    t = t.replace(/--(\d)/g, "-$1");
    if (++n > 8) break;
  } while (t !== prev);
  return t;
}
assert(fe83f_fixSigns("+-1.29% Sat") === "-1.29% Sat", "fix concat");
assert(fe83f_fixSigns("--1.29%") === "-1.29%", "fix minus");
assert(fe83f_fixSigns("+ (+-1.29%)") .indexOf("+-") < 0, "fix pair");
assert(fe83f_fixSigns("+1.29%") === "+1.29%", "keep pos");
var blows = 0;
var fe83f_qmBusy = false;
function base(tk) { return { status: "closed", detail: "Sat close " + tk }; }
function quote(tk) {
  blows++;
  if (blows > 12) throw new Error("loop");
  if (fe83f_qmBusy) return base(tk);
  fe83f_qmBusy = true;
  try {
    var m = base(tk);
    var closed = quote(tk).status === "closed";
    if (closed) m.detail = m.detail.replace(/\bSat\b/, "Fri");
    return m;
  } finally { fe83f_qmBusy = false; }
}
var got = quote("SPY");
assert(got.detail.indexOf("Fri") >= 0, "rewrote day");
assert(blows === 2, "one reentry");
console.log("fe84 unit ok");
"""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(src)
        tmp.close()
        test = subprocess.run(["node", tmp.name], capture_output=True, text=True)
        if test.returncode != 0:
            die("fe84 tests failed\n" + test.stdout + test.stderr)
        print(test.stdout.strip())
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)


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
    if not index_sum.startswith(EXPECT_INDEX_PREFIX):
        print("WARN index.html md5 %s expected prefix %s" % (index_sum, EXPECT_INDEX_PREFIX))
    if REFUSE_MARKER in app:
        print("REFUSE")
        return 0
    if NEED_MARKER not in app:
        die("missing anchor %s" % NEED_MARKER)
    if index.count('app.js?v=chat83b"') != 1:
        die("cache bust anchor missing")
    app = anchors(app)
    app = app + "\n" + BLOCK.strip() + "\n"
    if app.count("function fe84_rssSettle(") != 1:
        die("settle def")
    if app.count("function fe83f_rssFetch(") != 1 or app.count("function fe83f_marketClosed(") != 1:
        die("replaced def")
    index = index.replace('app.js?v=chat83b"', 'app.js?v=chat84"', 1)
    if index.count('app.js?v=chat84"') != 1 or "chat83b" in index:
        die("cache bust")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    try:
        tmp.write(app)
        tmp.close()
        chk = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        if chk.returncode != 0:
            die("node --check failed\n" + chk.stdout + chk.stderr)
        print("node --check ok")
        run_unit(app)
    finally:
        pathlib.Path(tmp.name).unlink(missing_ok=True)
    write_text(app_path, app, app_crlf)
    write_text(index_path, index, index_crlf)
    print("patched", app_path, index_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
