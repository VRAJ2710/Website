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

The same patch memoizes Intl.DateTimeFormat (bounded, first statement),
hoists the London hour-minute formatter inside fe64_ukHm, and Map-memoizes
the pure string helpers that dominated the home profile.
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

SHIM = r"""(function fe84_dtfShim(){
  try {
    if (!Intl || typeof Intl.DateTimeFormat !== "function" || Intl.DateTimeFormat.fe84) return;
    var fe84_dtfOrig = Intl.DateTimeFormat;
    var fe84_dtfCache = Object.create(null);
    var fe84_dtfN = 0;
    function fe84_dtf(locales, options) {
      var key;
      try {
        var loc = locales == null ? "" : (Array.isArray(locales) ? ("a:" + locales.join(",")) : ("s:" + String(locales)));
        key = loc + "|" + (options == null ? "" : JSON.stringify(options));
      } catch (eKey) {
        return new fe84_dtfOrig(locales, options);
      }
      var hit = fe84_dtfCache[key];
      if (hit) return hit;
      if (fe84_dtfN >= 200) { fe84_dtfCache = Object.create(null); fe84_dtfN = 0; }
      var made = new fe84_dtfOrig(locales, options);
      fe84_dtfCache[key] = made;
      fe84_dtfN++;
      return made;
    }
    fe84_dtf.prototype = fe84_dtfOrig.prototype;
    if (typeof fe84_dtfOrig.supportedLocalesOf === "function") fe84_dtf.supportedLocalesOf = fe84_dtfOrig.supportedLocalesOf.bind(fe84_dtfOrig);
    fe84_dtf.fe84 = 1;
    Intl.DateTimeFormat = fe84_dtf;
  } catch (e) {}
})();"""

BLOCK = r"""
// ── rt62g ──
// fe84: closed-session day lookup must not re-enter _quoteMeta.
// The rss-feed cache settles (15s) and a failed entry is dropped.
// Intl.DateTimeFormat is memoized at the top of this file (200, then clear).
// fe64_ukHm keeps one London hour-minute formatter.
// Pure string helpers use a Map of 500 and clear it when it fills.
// resolveInternalTicker is keyed on A.length, the last desk ticker, and a
// YAHOO_SYMBOLS recount that runs only when A.length changes. A yahoo-only
// edit that leaves A.length the same can stay stale until the next length
// change. P does not change the result, so it is not part of the key.
// The repeated A.find inside resolveInternalTicker is covered by that memo.
// _rt18CloseLbl is keyed on the caller's timezone plus the timestamp.
// fe84-memo-begin
function fe84_key(raw) {
  return typeof raw + ":" + (raw == null ? "" : String(raw));
}
function fe84_memo(fn, cap) {
  var map = new Map();
  var lim = cap || 500;
  return function (raw) {
    var key = fe84_key(raw);
    if (map.has(key)) return map.get(key);
    var out = fn.call(this, raw);
    if (map.size >= lim) map.clear();
    map.set(key, out);
    return out;
  };
}
var fe84_univLen = -1;
var fe84_yahooN = 0;
function fe84_univVer() {
  var n = 0;
  var tail = "";
  try {
    n = (typeof A !== "undefined" && A && A.length) || 0;
    tail = n ? String((A[n - 1] && A[n - 1].tk) || "") : "";
  } catch (e) { n = 0; tail = ""; }
  if (n !== fe84_univLen) {
    fe84_univLen = n;
    fe84_yahooN = 0;
    try {
      if (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS) {
        for (var k in YAHOO_SYMBOLS) {
          if (Object.prototype.hasOwnProperty.call(YAHOO_SYMBOLS, k)) fe84_yahooN++;
        }
      }
    } catch (e2) { fe84_yahooN = 0; }
  }
  return n + ":" + fe84_yahooN + ":" + tail;
}
function fe84_memo2(fn, cap) {
  var map = new Map();
  var lim = cap || 500;
  return function (a, b) {
    var key = fe84_key(a) + "\\n" + fe84_key(b);
    if (map.has(key)) return map.get(key);
    var out = fn.call(this, a, b);
    if (map.size >= lim) map.clear();
    map.set(key, out);
    return out;
  };
}
function fe84_memoResolve(fn) {
  var map = new Map();
  return function (raw) {
    var key = fe84_univVer() + "\n" + fe84_key(raw);
    if (map.has(key)) return map.get(key);
    var out = fn.call(this, raw);
    if (map.size >= 500) map.clear();
    map.set(key, out);
    return out;
  };
}
// fe84-memo-end
try { if (typeof sanitizeTicker === "function") sanitizeTicker = fe84_memo(sanitizeTicker, 500); } catch (eSan) {}
try { if (typeof fe77_fxKey === "function") fe77_fxKey = fe84_memo(fe77_fxKey, 500); } catch (eFx) {}
try { if (typeof fe65_scrub === "function") fe65_scrub = fe84_memo(fe65_scrub, 500); } catch (eScr) {}
try { if (typeof fe68_words === "function") fe68_words = fe84_memo(fe68_words, 500); } catch (eWrd) {}
try { if (typeof fe76_group === "function") fe76_group = fe84_memo2(fe76_group, 500); } catch (eGrp) {}
try { if (typeof fe64_plainNote === "function") fe64_plainNote = fe84_memo(fe64_plainNote, 500); } catch (eNote) {}
try {
  if (typeof fe82_scrubLoad === "function") {
    var fe84_scrubLoad0 = fe82_scrubLoad;
    var fe84_loadAt = 0;
    fe82_scrubLoad = function () {
      var now = Date.now();
      if (now - fe84_loadAt < 1000) return;
      fe84_loadAt = now;
      return fe84_scrubLoad0.apply(this, arguments);
    };
  }
} catch (eLoad) {}
try { if (typeof resolveInternalTicker === "function") resolveInternalTicker = fe84_memoResolve(resolveInternalTicker); } catch (eRes) {}
try {
  if (typeof _rt18CloseLbl === "function") {
    var fe84_close0 = _rt18CloseLbl;
    var fe84_closeMap = new Map();
    _rt18CloseLbl = function (ts) {
      var tz = "Europe/London";
      try { if (typeof _rt17Tz === "function") tz = _rt17Tz() || tz; } catch (eTz) {}
      var key = String(tz || "Europe/London") + "|" + fe84_key(ts);
      if (fe84_closeMap.has(key)) return fe84_closeMap.get(key);
      var out = fe84_close0.call(this, ts);
      if (fe84_closeMap.size >= 500) fe84_closeMap.clear();
      fe84_closeMap.set(key, out);
      return out;
    };
  }
} catch (eLbl) {}
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
    app = once(
        app,
        "// ── rt59 ──\n(function fe70_storage(){",
        SHIM + "\n// ── rt59 ──\n(function fe70_storage(){",
        "intl shim",
    )
    app = once(
        app,
        r"""function fe64_ukHm(iso) {
  var ms = typeof iso === "number" ? iso : Date.parse(iso || "");
  if (typeof iso === "string" && /^\d{11,}$/.test(iso)) ms = Number(iso);
  if (!isFinite(ms)) return "";
  try {
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    return h && mi ? h + ":" + mi : "";
  } catch (e) { return ""; }
}""",
        r"""var fe84_ukHmFmt = null;
var fe84_ukHmMap = new Map();
function fe64_ukHm(iso) {
  var ms = typeof iso === "number" ? iso : Date.parse(iso || "");
  if (typeof iso === "string" && /^\d{11,}$/.test(iso)) ms = Number(iso);
  if (!isFinite(ms)) return "";
  try {
    var bucket = Math.floor(ms / 60000);
    var cached = fe84_ukHmMap.get(bucket);
    if (cached != null) return cached;
    if (!fe84_ukHmFmt) fe84_ukHmFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
    var parts = fe84_ukHmFmt.formatToParts(new Date(ms));
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    var out = h && mi ? h + ":" + mi : "";
    if (fe84_ukHmMap.size >= 500) fe84_ukHmMap.clear();
    fe84_ukHmMap.set(bucket, out);
    return out;
  } catch (e) { return ""; }
}""",
        "ukHm hoist",
    )
    app = once(
        app,
        """function fe83f_pickDayPure(changeDay, label, feedDay, closed, todayWd) {
  var a = fe83f_wd(changeDay) || fe83f_wd(label) || fe83f_wd(feedDay);
  if (a) return a;
  if (closed && (todayWd === "Sat" || todayWd === "Sun")) return "Fri";
  return "";
}""",
        """function fe83f_pickDayPure(changeDay, label, feedDay, closed, todayWd) {
  var a = fe83f_wd(changeDay) || fe83f_wd(label) || fe83f_wd(feedDay);
  if (closed && (todayWd === "Sat" || todayWd === "Sun") && (!a || a === "Sat" || a === "Sun")) return "Fri";
  if (a) return a;
  return "";
}""",
        "weekend session day",
    )
    app = once(
        app,
        """    if (crypto) tail += " 24h";
    else if (q.changeDay) tail += " " + q.changeDay;""",
        """    if (crypto) tail += " 24h";
    else if (q.changeDay) {
      var fe84_day = q.changeDay;
      try {
        if (typeof fe83f_pickDay === "function") {
          var fe84_picked = fe83f_pickDay(q.symbol || q.ticker || "");
          if (fe84_picked) fe84_day = fe84_picked;
        }
      } catch (eDay) {}
      tail += " " + fe84_day;
    }""",
        "quote line session day",
    )
    app = once(
        app,
        """const IS_DESKTOP = () => window.innerWidth >= 768;
const MOBILE = () => !IS_DESKTOP() || (typeof window !== 'undefined' && window.innerWidth < 768);""",
        """var fe84_dw = -1, fe84_desk = false;
function fe84_deskSync() {
  var w = 0;
  try { w = window.innerWidth || 0; } catch (e) { w = 0; }
  fe84_dw = w;
  fe84_desk = w >= 768;
  return fe84_desk;
}
try { window.addEventListener("resize", fe84_deskSync); } catch (eDesk) {}
const IS_DESKTOP = () => (fe84_dw <= 0 ? fe84_deskSync() : fe84_desk);
const MOBILE = () => !(fe84_dw <= 0 ? fe84_deskSync() : fe84_desk);""",
        "desktop width cache",
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
    if not app_text.startswith("(function fe84_dtfShim(){"):
        die("shim not first")
    if app_text.find("function fe84_dtfShim") > app_text.find("function fe70_storage"):
        die("shim after storage")
    uk = app_text.split("function fe64_ukHm", 1)[1].split("function fe64_closedWords", 1)[0]
    if uk.count("new Intl.DateTimeFormat") != 1 or "fe84_ukHmFmt.formatToParts" not in uk:
        die("ukHm still constructs")
    if '(!a || a === "Sat" || a === "Sun")) return "Fri"' not in app_text:
        die("weekend day")
    if "sanitizeTicker = fe84_memo(sanitizeTicker, 500)" not in app_text:
        die("sanitize memo")
    if "resolveInternalTicker = fe84_memoResolve(resolveInternalTicker)" not in app_text:
        die("resolve memo")
    if "_rt18CloseLbl = function (ts)" not in app_text:
        die("close lbl memo")
    shim = app_text.split("// ── rt59 ──", 1)[0]
    memo = app_text.split("// fe84-memo-begin", 1)[1].split("// fe84-memo-end", 1)[0]
    src = shim + "\n" + memo + "\n" + r"""
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
function fe83f_wd(s) {
  var m = String(s || "").trim().match(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/i);
  if (!m) return "";
  var x = m[1].toLowerCase();
  return x.charAt(0).toUpperCase() + x.slice(1, 3);
}
function fe83f_pickDayPure(changeDay, label, feedDay, closed, todayWd) {
  var a = fe83f_wd(changeDay) || fe83f_wd(label) || fe83f_wd(feedDay);
  if (closed && (todayWd === "Sat" || todayWd === "Sun") && (!a || a === "Sat" || a === "Sun")) return "Fri";
  if (a) return a;
  return "";
}
assert(fe83f_pickDayPure("Sat", "", "", true, "Sat") === "Fri", "gold sat");
assert(fe83f_pickDayPure("Fri", "", "", true, "Sat") === "Fri", "wti fri");
assert(fe83f_pickDayPure("Thu", "", "", true, "Thu") === "Thu", "weekday");
assert(fe83f_pickDayPure("", "", "", true, "Sun") === "Fri", "empty weekend");
assert(fe83f_pickDayPure("Sat", "", "", false, "Sat") === "Sat", "open sat stays");
var calls = 0;
function rawSan(s) { calls++; return String(s == null ? "" : s).toUpperCase(); }
var san = fe84_memo(rawSan, 3);
assert(san("nvda") === "NVDA" && san("nvda") === "NVDA" && calls === 1, "memo hit");
san("a");
san("b");
var before = calls;
san("c");
assert(calls === before + 1, "memo fill");
assert(san("nvda") === "NVDA" && calls === before + 2, "cleared");
var badN = 0;
function boom() { badN++; if (badN < 2) throw new Error("x"); return "ok"; }
var bm = fe84_memo(boom, 10);
try { bm("a"); } catch (e) {}
assert(bm("a") === "ok" && badN === 2, "no cache throw");
var A = [{ tk: "SPY" }];
var YAHOO_SYMBOLS = { SPY: "SPY", BTC: "BTC-USD" };
var rc = 0;
function resolve(raw) { rc++; return String(raw) === "BTC-USD" ? "BTC" : String(raw); }
var rr = fe84_memoResolve(resolve);
assert(rr("BTC-USD") === "BTC" && rr("BTC-USD") === "BTC" && rc === 1, "resolve hit");
A.push({ tk: "NVDA" });
assert(rr("BTC-USD") === "BTC" && rc === 2, "resolve ver");
var list = Intl.DateTimeFormat(["en-GB", "en"], { timeZone: "UTC" });
assert(list === Intl.DateTimeFormat(["en-GB", "en"], { timeZone: "UTC" }), "dtf cache");
assert(list instanceof Intl.DateTimeFormat, "instanceof");
assert(typeof list.resolvedOptions === "function" && list.resolvedOptions().timeZone, "resolved");
var parts = list.formatToParts(new Date(0));
assert(Array.isArray(parts) && parts.length > 0, "parts");
if (typeof list.formatRange === "function") assert(typeof list.formatRange(new Date(0), new Date(60000)) === "string", "range");
var bare = Intl.DateTimeFormat("en-GB", { timeZone: "UTC" });
assert(bare instanceof Intl.DateTimeFormat && typeof bare.format === "function", "no new");
var made = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
assert(made.formatToParts(new Date(0)).some(function (p) { return p.type === "hour"; }), "with new");
assert(Intl.DateTimeFormat(["en-GB", "fr"]) !== Intl.DateTimeFormat("fr"), "array key");
assert(Array.isArray(Intl.DateTimeFormat.supportedLocalesOf(["en-GB"])), "supported");
var zones = Intl.supportedValuesOf("timeZone");
var keep = Intl.DateTimeFormat("en-GB", { timeZone: zones[0] });
for (var i = 1; i <= 200; i++) Intl.DateTimeFormat("en-GB", { timeZone: zones[i] });
assert(Intl.DateTimeFormat("en-GB", { timeZone: zones[0] }) !== keep, "bound");
assert(Intl.DateTimeFormat("en-GB", { timeZone: zones[0] }) === Intl.DateTimeFormat("en-GB", { timeZone: zones[0] }), "refilled");
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
    if app.count("function fe84_dtf(") != 1 or app.count("var fe84_ukHmFmt = null;") != 1:
        die("intl hooks")
    if app.count("function fe84_memo(") != 1:
        die("memo def")
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
