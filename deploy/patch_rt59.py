#!/usr/bin/env python3
"""patch_rt59.py: client patch on chat70. Reads app.js?v=chatNN and writes chatNN+1.

The known base is chat70, the output of patch_rt58.py:
  app.js md5 a2340d4aa1cf772a1f1b02f054a9c265
  index.html md5 dc83072412c2a0b0a3af2b64fc3f9908
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

Guest Home scrolls on the document, including when storage throws. News shows
Loading headlines until a fetch completes, and retries an empty first load.
Headlines use a weighted word-boundary tag. Tape, header and the session panel
share one status line: opening, venue hours, a Hong Kong holiday, and quiet
measured from lagMs when the quote carries it. The brief's Written marker uses
generatedAtUk or generatedAt and those fields stay on the saved daily copy.
House filing notes are left as the server sent them.

Usage: python3 patch_rt59.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "a2340d4aa1cf772a1f1b02f054a9c265"
EXPECT_INDEX_MD5 = "dc83072412c2a0b0a3af2b64fc3f9908"
NEED_MARKER = "// ── rt58 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt59 ──' in s: already('rt59 already applied')
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

SHIM = r"""// ── rt59 ──
(function fe70_storage(){
  function mem(){
    var box = Object.create(null);
    return {
      getItem: function(k){ return Object.prototype.hasOwnProperty.call(box, k) ? box[k] : null; },
      setItem: function(k, v){ box[String(k)] = String(v); },
      removeItem: function(k){ delete box[k]; },
      clear: function(){ box = Object.create(null); },
      key: function(i){ var keys = Object.keys(box); return keys[i] || null; },
      get length(){ return Object.keys(box).length; }
    };
  }
  function install(name){
    var store = null, bad = false;
    try { store = window[name]; } catch (e) { bad = true; }
    if (!bad) { try { if (!store || typeof store.getItem !== "function") bad = true; else store.getItem("__fe70"); } catch (e2) { bad = true; } }
    if (!bad) return;
    var bag = mem();
    try { Object.defineProperty(window, name, { configurable: true, get: function(){ return bag; } }); } catch (e3) {}
  }
  try { install("localStorage"); } catch (e) {}
  try { install("sessionStorage"); } catch (e) {}
})();"""
STORY = r"""function fe70_at(raw, term) {
  var k = String(term || "").toLowerCase();
  if (!k) return -1;
  var re = new RegExp("(^|[^a-z0-9])" + k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "s?($|[^a-z0-9])", "i");
  var m = re.exec(raw);
  return m ? m.index : -1;
}
function fe70_financeSrc(src) {
  return /reuters|bloomberg|financial times|\bft\.com\b|\bwsj\b|wall street journal|\bcnbc\b|marketwatch|barron|yahoo finance|seeking alpha|investing\.com|bbc business|sky business/i.test(String(src || ""));
}
function fe68_storyTag(text, low, hit, feedCat, src) {
  var raw = " " + String(text == null ? "" : text).toLowerCase().replace(/[\u2018\u2019\u201B]/g, "'").replace(/\s+/g, " ") + " ";
  var rules = {
    Stocks: [["skyworks", 3], ["coreweave", 3], ["fleetpartners", 3], ["fleet partners", 3], ["starboard", 3], ["hang seng", 2], ["kospi", 2], ["nikkei", 2], ["asx", 2], ["msci", 2], ["s&p 500", 2], ["s&p", 2], ["nasdaq", 2], ["dow jones", 2], ["asian stocks", 2], ["pharma", 2], ["biotech", 2], ["moderna", 2], ["merck", 2], ["stocktwits", 3], ["gift nifty", 3], ["nifty", 2], ["vwap", 2], ["profit", 2], ["earnings", 2], ["q1", 2], ["q2", 2], ["q3", 2], ["q4", 2], ["revenue", 2], ["guidance", 2], ["deal", 2], ["acquires", 2], ["acquire", 2], ["merger", 2], ["stake", 2], ["ipo", 2], ["listing", 1], ["results", 2], ["misses", 2], ["miss", 2], ["beats", 2], ["shares", 1], ["stocks", 1], ["stock", 1], ["equities", 1], ["equity", 1]],
    Crypto: [["xrp ledger", 4], ["bitcoin", 6], ["btc", 4], ["ethereum", 4], ["ether", 4], ["zcash", 4], ["solana", 4], ["xrp", 4], ["dogecoin", 3], ["blockchain", 3], ["defi", 3], ["stablecoin", 3], ["crypto", 3], ["cryptocurrency", 3], ["tokenized", 2], ["tokenization", 2], ["custody", 2], ["token", 2]],
    Commodities: [["newpeak", 3], ["ampol", 3], ["new hope", 3], ["natural gas", 3], ["minerals", 3], ["mineral", 2], ["mining", 2], ["pipeline", 2], ["lng", 3], ["brent", 2], ["wti", 2], ["crude", 2], ["copper", 2], ["gold", 2], ["silver", 2], ["wheat", 2], ["corn", 2], ["grain", 2], ["coal", 2], ["drilling", 2], ["oil", 2], ["gas", 2], ["metals", 2], ["metal", 1]],
    Macro: [["government spending", 4], ["central bank", 3], ["house prices", 3], ["home prices", 3], ["economic growth", 3], ["china's growth", 3], ["interest rate", 2], ["rate cut", 2], ["rate hike", 2], ["bond yield", 2], ["bond rout", 2], ["labour market", 2], ["labor market", 2], ["federal reserve", 3], ["inflation", 2], ["unemployment", 2], ["housing", 3], ["house price", 3], ["boe", 2], ["fed", 2], ["ecb", 2], ["boj", 2], ["gdp", 3], ["cpi", 2], ["pmi", 2], ["budget", 2], ["bonds", 1], ["bond", 1], ["yields", 1], ["jobs", 1], ["rates", 1]],
    Geopolitics: [["rejoin eu", 4], ["brexit", 3], ["ceasefire", 3], ["sanctions", 3], ["sanction", 2], ["ukraine", 3], ["putin", 3], ["trump", 2], ["starmer", 3], ["macron", 3], ["summit", 2], ["tariff", 2], ["trade war", 3], ["hormuz", 4], ["strait", 2], ["shipping lane", 2], ["war", 2], ["government", 1], ["govt", 2], ["president", 1], ["eu", 2]],
    Forex: [["currency pair", 3], ["eur/usd", 3], ["gbp/usd", 3], ["usd/jpy", 3], ["forex", 3], ["sterling", 2], ["dollar", 2], ["euro", 2], ["yen", 2], ["fx", 2]],
    Regulation: [["investigates", 5], ["investigate", 5], ["regulator", 4], ["gambling", 4], ["licence", 3], ["license", 3], ["probe", 5], ["fca", 4], ["sec", 5], ["cftc", 4], ["esma", 4], ["fine", 3], ["fined", 3], ["ban", 2]]
  };
  var found = [], names = Object.keys(rules), i, j, term, pos, score, at, tag;
  for (i = 0; i < names.length; i++) {
    tag = names[i];
    score = 0;
    at = -1;
    for (j = 0; j < rules[tag].length; j++) {
      term = rules[tag][j];
      pos = fe70_at(raw, term[0]);
      if (pos < 0) continue;
      if (term[0] === "fine" || term[0] === "fined" || term[0] === "ban") {
        if (fe70_at(raw, "bank") < 0 && fe70_at(raw, "shares") < 0 && fe70_at(raw, "trading") < 0 && fe70_at(raw, "regulator") < 0 && fe70_at(raw, "fca") < 0 && fe70_at(raw, "sec") < 0 && fe70_at(raw, "licence") < 0 && fe70_at(raw, "license") < 0 && fe70_at(raw, "company") < 0 && fe70_at(raw, "firm") < 0 && fe70_at(raw, "stock") < 0) continue;
      }
      score += term[1];
      if (at < 0 || pos < at) at = pos;
    }
    if (score > 0) found.push({ tag: tag, score: score, at: at });
  }
  var market = fe70_at(raw, "stock") >= 0 || fe70_at(raw, "stocks") >= 0 || fe70_at(raw, "market") >= 0 || fe70_at(raw, "markets") >= 0 || fe70_at(raw, "crypto") >= 0 || fe70_at(raw, "token") >= 0 || fe70_at(raw, "tokenized") >= 0 || fe70_at(raw, "trading") >= 0 || fe70_at(raw, "exchange") >= 0 || fe70_at(raw, "listing") >= 0 || fe70_at(raw, "bond") >= 0 || fe70_at(raw, "equity") >= 0 || fe70_at(raw, "fund") >= 0 || fe70_at(raw, "tariff") >= 0;
  if ((fe70_at(raw, "framework") >= 0 || fe70_at(raw, "rule") >= 0) && market) {
    var reg = null;
    for (i = 0; i < found.length; i++) if (found[i].tag === "Regulation") reg = found[i];
    pos = fe70_at(raw, "framework");
    if (pos < 0) pos = fe70_at(raw, "rule");
    if (!reg) found.push({ tag: "Regulation", score: 3, at: pos });
    else { reg.score += 3; if (pos >= 0 && pos < reg.at) reg.at = pos; }
  }
  if (!found.length) {
    if (/\bmarkets?\b/.test(raw) && feedCat) {
      var chip = fe68_chip(feedCat);
      if (chip && chip !== "Other") return chip;
    }
    if (fe70_financeSrc(src)) {
      var prior = fe68_chip(feedCat);
      return prior === "Macro" ? "Macro" : "Stocks";
    }
    return "Other";
  }
  var best = found[0];
  for (i = 1; i < found.length; i++) {
    if (found[i].score > best.score) best = found[i];
    else if (found[i].score === best.score && found[i].at < best.at) best = found[i];
    else if (found[i].score === best.score && found[i].at === best.at && feedCat && fe68_chip(feedCat) === found[i].tag) best = found[i];
  }
  var tied = found.filter(function (x) { return x.score === best.score && x.at === best.at; });
  if (tied.length > 1 && feedCat) {
    var want = fe68_chip(feedCat);
    for (i = 0; i < tied.length; i++) if (tied[i].tag === want) return want;
  }
  return best.tag;
}"""
BLOCK = r"""// fe70-pure-begin
function fe70_hm(v) {
  var ms = typeof v === "number" ? v : Date.parse(v || "");
  if (typeof v === "string" && /^\d{11,}$/.test(v)) ms = Number(v);
  if (!isFinite(ms) || ms <= 0) return "";
  if (ms < 1e11) ms *= 1000;
  try {
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    if (h.length === 1) h = "0" + h;
    return h && mi ? h + ":" + mi : "";
  } catch (e) { return ""; }
}
function fe70_opensWhen(v) {
  var ms = typeof v === "number" ? v : Date.parse(v || "");
  if (typeof v === "string" && /^\d{11,}$/.test(v)) ms = Number(v);
  if (!isFinite(ms) || ms <= 0) return "";
  if (ms < 1e11) ms *= 1000;
  try {
    var wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date(ms));
    var hm = fe70_hm(ms);
    return wd && hm ? wd + " " + hm + " UK" : "";
  } catch (e) { return ""; }
}
function fe70_openingLine(phase, firstPriceAt, note) {
  if (phase !== "opening") return "";
  var hm = fe70_hm(firstPriceAt);
  if (!hm && note) {
    var m = String(note).match(/(\d{1,2}:\d{2})\s*UK/i);
    if (m) hm = m[1].length === 4 ? "0" + m[1] : m[1];
  }
  if (!hm) {
    var t = String(note || "").replace(/\s+/g, " ").trim();
    if (/opening/i.test(t) && /due/i.test(t)) return t.charAt(0).toUpperCase() + t.slice(1);
    return "";
  }
  return "Opening · first prices due " + hm + " UK";
}
function fe70_isQuiet(opt) {
  opt = opt || {};
  if (opt.phase === "opening") return false;
  var clock = null;
  if (typeof opt.lagMs === "number" && isFinite(opt.lagMs)) clock = opt.lagMs;
  else if (typeof opt.ageMs === "number" && isFinite(opt.ageMs)) clock = opt.ageMs;
  if (clock == null) return false;
  return clock >= 20 * 60000;
}
function fe70_written(b) {
  if (!b || typeof b !== "object") return "";
  if (b.generatedAtUk) return "Written " + b.generatedAtUk;
  var ts = Date.parse(b.generatedAt || "");
  if (!ts) return "";
  try {
    var d = new Date(ts);
    var wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(d);
    var day = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short" }).format(d);
    var hm = fe70_hm(ts);
    if (!wd || !day || !hm) return "";
    return "Written " + wd + " " + day + ", " + hm + " UK";
  } catch (e) { return ""; }
}
function fe70_stamp(brief, data) {
  if (!brief || typeof brief !== "object") return brief;
  data = data || {};
  var inner = data.brief && typeof data.brief === "object" ? data.brief : {};
  var g = data.generatedAt || inner.generatedAt || brief.generatedAt || "";
  var u = data.generatedAtUk || inner.generatedAtUk || brief.generatedAtUk || "";
  if (g) brief.generatedAt = g;
  if (u) brief.generatedAtUk = u;
  return brief;
}
function fe70_spec(tk) {
  var t = String(tk || "").toUpperCase();
  var idx = {
    FTSE: ["Europe/London", 480, 990], "^FTSE": ["Europe/London", 480, 990],
    DAX: ["Europe/Berlin", 540, 1050], "^GDAXI": ["Europe/Berlin", 540, 1050],
    CAC: ["Europe/Paris", 540, 1050], "^FCHI": ["Europe/Paris", 540, 1050],
    N225: ["Asia/Tokyo", 540, 930], "^N225": ["Asia/Tokyo", 540, 930],
    HSI: ["Asia/Hong_Kong", 570, 960], "^HSI": ["Asia/Hong_Kong", 570, 960],
    NSEI: ["Asia/Kolkata", 555, 930], "^NSEI": ["Asia/Kolkata", 555, 930],
    ASX200: ["Australia/Sydney", 600, 960], "^AXJO": ["Australia/Sydney", 600, 960],
    KOSPI: ["Asia/Seoul", 540, 930], "^KS11": ["Asia/Seoul", 540, 930]
  };
  var suf = [
    [".L", "Europe/London", 480, 990],
    [".HK", "Asia/Hong_Kong", 570, 960],
    [".T", "Asia/Tokyo", 540, 930],
    [".AX", "Australia/Sydney", 600, 960],
    [".KS", "Asia/Seoul", 540, 930],
    [".NS", "Asia/Kolkata", 555, 930],
    [".SS", "Asia/Shanghai", 570, 900],
    [".SZ", "Asia/Shanghai", 570, 900],
    [".DE", "Europe/Berlin", 540, 1050],
    [".PA", "Europe/Paris", 540, 1050]
  ];
  var row = idx[t];
  if (!row) {
    var i;
    for (i = 0; i < suf.length; i++) if (t.slice(-suf[i][0].length) === suf[i][0]) row = suf[i].slice(1);
  }
  if (!row) return null;
  return { tz: row[0], open: row[1], close: row[2] };
}
var FE70_HK = ["0700.HK", "9988.HK", "HSI", "^HSI"];
function fe70_isHk(tk) {
  return FE70_HK.indexOf(String(tk || "").toUpperCase()) >= 0;
}
// fe70-pure-end
var fe70_q = Object.create(null);
var fe70_newsReady = false;
var fe70_newsTries = 0;
var fe70_newsTimer = 0;
function fe70_newsHold() {
  try { if (typeof NEWS !== "undefined" && NEWS && NEWS.length) return false; } catch (e) {}
  return fe70_newsReady !== true;
}
function fe70_repaintNews() {
  try {
    if (typeof pg !== "undefined" && pg === "news") {
      if (typeof _paintNewsListOnly === "function" && document.getElementById("news-list-body")) _paintNewsListOnly(true);
      else if (typeof renderMain === "function") renderMain();
    }
    if (typeof IS_DESKTOP === "function" && IS_DESKTOP() && typeof renderP2 === "function") renderP2();
  } catch (e) {}
}
function fe70_isCfx(tk) {
  var t = String(tk || "");
  try { if (typeof _rtIsCrypto === "function" && _rtIsCrypto(t)) return true; } catch (e) {}
  try { if (typeof _rt18Class === "function") { var c = _rt18Class(t); if (c === "crypto" || c === "fx") return true; } } catch (e2) {}
  var tc = (typeof TICKER_CATS !== "undefined" && TICKER_CATS[t]) || "";
  if (tc === "cry" || tc === "fx") return true;
  if (/^[A-Z]{6}$/.test(t) && /USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD/.test(t)) return true;
  return false;
}
function fe70_bag(tk) {
  var o = {}, q = fe70_q[tk], y = null, k;
  if (q) { for (k in q) if (Object.prototype.hasOwnProperty.call(q, k)) o[k] = q[k]; }
  try { y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null; } catch (e) { y = null; }
  if (y) {
    if (!o.status && y.status) o.status = y.status;
    if (o.delayMin == null && y.delayMin != null) o.delayMin = y.delayMin;
    if (!o.note && y.note) o.note = y.note;
    if ((o.nextOpen == null || o.nextOpen === "") && y.nextOpen) o.nextOpen = y.nextOpen;
    if (o.marketOpen == null && y.marketOpen != null) o.marketOpen = y.marketOpen;
    if (!o.phase && y.phase) o.phase = y.phase;
    if (o.lagMs == null && typeof y.lagMs === "number") o.lagMs = y.lagMs;
    if (!o.firstPriceAt && y.firstPriceAt) o.firstPriceAt = y.firstPriceAt;
  }
  return o;
}
function fe70_hkBag() {
  var keys = ["0700.HK", "9988.HK", "HSI"], i, b;
  for (i = 0; i < keys.length; i++) {
    b = fe70_bag(keys[i]);
    if (b && (b.status === "closed" || b.marketOpen === false || /holiday/i.test(String(b.note || "")))) return b;
  }
  return null;
}
function fe70_opening(tk) {
  return fe70_bag(tk).phase === "opening";
}
function fe70_line(tk, where) {
  var bag = fe70_bag(tk);
  var open = fe70_openingLine(bag.phase, bag.firstPriceAt, bag.note);
  if (open) return open;
  var hk = fe70_hkBag();
  if (hk && fe70_isHk(tk)) {
    var when = fe70_opensWhen(hk.nextOpen);
    if (where === "panel") return when ? "closed · holiday · opens " + when : "closed · holiday";
    return when ? "CLOSED · opens " + when : "CLOSED";
  }
  return "";
}
function fe70_scrub(s) {
  return String(s == null ? "" : s).replace(/cached/ig, "").replace(/\s{2,}/g, " ").replace(/\s+·\s+·/g, " · ").trim();
}
function fe70_finish(tk, m) {
  var o = {}, k;
  m = m || {};
  for (k in m) if (Object.prototype.hasOwnProperty.call(m, k)) o[k] = m[k];
  var line = fe70_line(tk, "tape");
  if (line && line.indexOf("Opening") === 0) {
    o.status = "opening"; o.label = line; o.detail = line; o.fe64Note = line;
  } else if (line && line.indexOf("CLOSED") === 0) {
    o.status = "closed"; o.label = "CLOSED"; o.detail = line;
    o.fe64Note = line.replace(/^CLOSED\s*·\s*/, "");
  } else if (o.status === "rth-close" || /RTH CLOSE/i.test(String(o.label || ""))) {
    if (fe70_isCfx(tk)) { o.status = "delayed"; o.label = fe70_scrub(o.label) || "delayed"; }
    else { o.status = "closed"; o.label = "CLOSED"; }
  }
  var bag = fe70_bag(tk);
  var delay = typeof bag.delayMin === "number" && bag.delayMin > 0 ? Math.round(bag.delayMin) : 0;
  if (!line && delay > 0 && o.status !== "live" && o.status !== "closed" && o.status !== "lunch" && o.status !== "opening") {
    var words = "delayed " + delay + " min by exchange";
    o.status = "delayed"; o.label = words; o.detail = words; o.fe64Note = words;
  }
  if (String(tk) === "XAU" && o.status === "live") { o.label = "LIVE Spot gold"; o.detail = "Spot gold"; }
  ["label", "detail", "fe64Note"].forEach(function (key) {
    if (typeof o[key] === "string") o[key] = fe70_scrub(o[key]);
  });
  if (o.status === "cached" || (o.label && /cached/i.test(m.label || ""))) {
    if (!o.label) { o.status = "delayed"; o.label = "delayed"; o.detail = o.detail || "delayed"; }
  }
  return o;
}
function fe70_sess(tk) {
  var line = fe70_line(tk, "panel");
  if (line) return { st: line, c: "" };
  var open = false, live = false, synced = false;
  try { synced = hasSyncedQuote(tk); } catch (e) { synced = false; }
  if (!synced) return { st: "no price yet", c: "" };
  try { open = _rt18MarketOpen(tk); } catch (e2) {}
  try { live = _rt39Live(tk); } catch (e3) {}
  if (live) return { st: "trading", c: "rt51-ok" };
  if (open) return { st: "quiet (open, no new price for 20 min)", c: "" };
  var nx = 0, when = "";
  try { nx = _rt51Next(tk); } catch (e4) {}
  try { when = nx ? _rt51When(nx) : ""; } catch (e5) {}
  return { st: "closed" + (when ? " · opens " + when : ""), c: "" };
}
function fe70_universe() {
  var extra = [
    { tk: "FTSE", nm: "FTSE 100", cat: "Index", ex: "LSE" },
    { tk: "DAX", nm: "DAX", cat: "Index", ex: "XETRA" },
    { tk: "NSEI", nm: "Nifty 50", cat: "Index", ex: "NSE" },
    { tk: "HSI", nm: "Hang Seng", cat: "Index", ex: "HKEX" }
  ];
  var have = {};
  try { A.forEach(function (a) { if (a && a.tk) have[a.tk] = 1; }); } catch (e) {}
  return A.concat(extra.filter(function (a) { return !have[a.tk]; }));
}
function fe70_rank(tk) {
  var d = {}, as = 0;
  try { d = fp(tk) || {}; } catch (e) {}
  var s = d.status || "";
  var rank = s === "live" ? 6 : s === "closed" ? 5 : s === "lunch" ? 4 : s === "delayed" ? 3 : s === "stale" ? 2 : (s === "cached" || s === "proxy" ? 1 : 0);
  try { as = d.asOf ? new Date(d.asOf).getTime() : 0; } catch (e2) { as = 0; }
  if (!as) { try { as = Number(liveQuoteTs[tk]) || 0; } catch (e3) {} }
  return { rank: rank, as: as || 0 };
}
function fe70_dedupe(list) {
  var best = Object.create(null), order = [], i, tk, key, cur, prev;
  for (i = 0; i < list.length; i++) {
    tk = list[i];
    key = String(tk || "").toUpperCase();
    cur = fe70_rank(tk);
    prev = best[key];
    if (!prev) { best[key] = { tk: tk, rank: cur.rank, as: cur.as }; order.push(key); continue; }
    if (cur.rank > prev.rank || (cur.rank === prev.rank && cur.as >= prev.as)) best[key] = { tk: tk, rank: cur.rank, as: cur.as };
  }
  return order.map(function (k) { return best[k].tk; });
}
function fe70_age(tk) {
  var ts = 0;
  try { ts = Number(liveQuoteTs[tk]) || 0; } catch (e) {}
  if (ts > 0 && ts < 1e11) ts *= 1000;
  if (!(ts > 0)) return null;
  return Date.now() - ts;
}
function fe70_unlockHome(dialog) {
  try {
    if (!dialog || dialog.id !== "homeOv") return;
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.width = "";
    document.body.classList.add("fe70-home");
    dialog.classList.add("fe70-doc");
  } catch (e) {}
}
function fe70_afterNews() {
  if (typeof fe70_newsTries !== "number" || !isFinite(fe70_newsTries)) fe70_newsTries = 0;
  try {
    if (typeof NEWS !== "undefined" && NEWS.length) { fe70_newsReady = true; fe70_newsTries = 0; return; }
  } catch (e) {}
  if (fe70_newsReady === true) return;
  try { if (typeof updatePaused !== "undefined" && updatePaused) return; } catch (e2) {}
  if (fe70_newsTries >= 3) { fe70_newsReady = true; fe70_repaintNews(); return; }
  var wait = [1000, 3000, 8000][fe70_newsTries] || 8000;
  fe70_newsTries++;
  clearTimeout(fe70_newsTimer);
  fe70_newsTimer = setTimeout(function () {
    if (fe70_newsReady !== true) { try { fetchLiveNews(); } catch (e) {} }
  }, wait);
}
try {
  var fe70_apply0 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q, source) {
    var ok = fe70_apply0.apply(this, arguments);
    try {
      if (tk && q) {
        var prev = fe70_q[tk] || {}, next = {}, k;
        for (k in prev) next[k] = prev[k];
        if (q.phase) next.phase = q.phase;
        if (q.firstPriceAt != null && q.firstPriceAt !== "") next.firstPriceAt = q.firstPriceAt;
        if (typeof q.lagMs === "number" && isFinite(q.lagMs)) next.lagMs = q.lagMs;
        if (typeof q.note === "string" && q.note) next.note = q.note;
        if (typeof q.delayMin === "number" && isFinite(q.delayMin)) next.delayMin = q.delayMin;
        if (q.status) next.status = q.status;
        if (q.nextOpen != null && q.nextOpen !== "") next.nextOpen = q.nextOpen;
        if (q.marketOpen === false) next.marketOpen = false;
        else if (q.marketOpen === true) next.marketOpen = true;
        fe70_q[tk] = next;
        if (fe70_isCfx(tk) && typeof liveQuoteMarketClosed !== "undefined") liveQuoteMarketClosed[tk] = false;
      }
    } catch (e) {}
    return ok;
  };
} catch (e) {}
try {
  var fe70_qm = _quoteMeta;
  var fe70_inMeta = false;
  _quoteMeta = function (tk) {
    var m = fe70_qm.apply(this, arguments);
    if (fe70_inMeta) return m;
    fe70_inMeta = true;
    try { m = fe70_finish(tk, m); } catch (e) {}
    fe70_inMeta = false;
    return m;
  };
} catch (e) {}
try {
  var fe70_live0 = _rt39Live;
  var fe70_inLive = false;
  _rt39Live = function (tk) {
    if (fe70_inLive) return false;
    fe70_inLive = true;
    try {
      if (fe70_opening(tk)) return false;
      if (!hasSyncedQuote(tk) || !_rt18MarketOpen(tk)) return false;
      var m = _quoteMeta(tk) || {};
      if (m.status === "live") return true;
      if (m.status === "closed" || m.status === "lunch" || m.status === "opening") return false;
      var bag = fe70_bag(tk);
      if (typeof bag.lagMs === "number" && isFinite(bag.lagMs)) return !fe70_isQuiet({ phase: bag.phase, lagMs: bag.lagMs });
      return fe70_live0.apply(this, arguments);
    } catch (e) {
      try { return fe70_live0.apply(this, arguments); } catch (e2) { return false; }
    } finally { fe70_inLive = false; }
  };
} catch (e) {}
try {
  var fe70_at0 = _rt18MarketOpenAt;
  _rt18MarketOpenAt = function (tk, d) {
    try {
      if (fe70_hkBag() && fe70_isHk(tk)) return false;
      var spec = fe70_spec(tk);
      if (spec && typeof _rt18Parts === "function") {
        var p = _rt18Parts(spec.tz, d instanceof Date ? d : new Date(d));
        if (!p || p.wd === "Sat" || p.wd === "Sun") return false;
        return p.m >= spec.open && p.m < spec.close;
      }
    } catch (e) {}
    return fe70_at0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe70_next0 = _rt51Next;
  _rt51Next = function (tk) {
    try {
      var hk = fe70_hkBag();
      if (hk && fe70_isHk(tk) && hk.nextOpen) {
        var ms = typeof hk.nextOpen === "number" ? hk.nextOpen : Date.parse(hk.nextOpen);
        if (ms > 0 && ms < 1e11) ms *= 1000;
        if (ms > Date.now()) return ms;
      }
    } catch (e) {}
    return fe70_next0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe70_tb = _rtTapeBadge;
  _rtTapeBadge = function (d) {
    var html = "";
    try { html = fe70_tb.apply(this, arguments) || ""; } catch (e) { html = ""; }
    return String(html).replace(/cached/ig, "");
  };
} catch (e) {}
try {
  _rt16BriefWhen = function (b) {
    try { return fe70_written(b) || ""; } catch (e) { return ""; }
  };
} catch (e) {}
try {
  var fe70_brief = _renderDispatchBrief;
  _renderDispatchBrief = function () {
    var h = fe70_brief.apply(this, arguments);
    try {
      var w = fe70_written(typeof _brief !== "undefined" ? _brief : null);
      if (w && String(h).indexOf(w) < 0) {
        h = String(h).replace(/(DISPATCH BRIEF[^<]*)/, "$1 · " + w);
      }
    } catch (e) {}
    return h;
  };
} catch (e) {}
try {
  var fe70_openDlg = _openA11yDialog;
  _openA11yDialog = function (dialog, closeFn, focusSelector) {
    var home = dialog && dialog.id === "homeOv";
    var r = fe70_openDlg.apply(this, arguments);
    if (home) fe70_unlockHome(dialog);
    return r;
  };
} catch (e) {}
try { if (typeof NEWS !== "undefined" && NEWS && NEWS.length) fe70_newsReady = true; } catch (e) {}
try {
  var st70 = document.createElement("style");
  st70.id = "fe70-css";
  st70.textContent = "body.fe70-home,body.fe70-home html{overflow:auto!important;position:static!important;height:auto!important;width:auto!important}body.fe70-home #homeOv,body.fe70-home #homeOv.term-overlay,body.fe70-home #homeOv.front-door-overlay{position:relative!important;inset:auto!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;width:auto!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;z-index:1!important}body.fe70-home #homeOv .term-overlay-card,body.fe70-home #homeOv .term-overlay-body{height:auto!important;max-height:none!important;overflow:visible!important}body.fe70-home:not(.app-booting) .tape{visibility:visible!important}body.fe68-lenses .panel.p-expanded{position:relative!important;inset:auto!important;height:auto!important;min-height:0!important}@media (max-width:767px){[data-fe70-ask=desk]{display:none!important}[data-fe70-ask=mob]{display:inline-flex!important;min-width:44px;min-height:44px;align-items:center;justify-content:center}.hdr{z-index:260}}@media (min-width:768px){[data-fe70-ask=mob]{display:none!important}[data-fe70-ask=desk]{display:inline-flex!important;min-width:44px;min-height:44px;align-items:center;justify-content:center;position:relative;z-index:261}.cmd-bar{position:relative;z-index:260}}";
  document.head.appendChild(st70);
} catch (e) {}"""
CRITICAL = r"""<style id="fe70-critical">
@media (max-width:767px){
  .terminal-wrap{display:none!important}
  .hdr{display:flex;flex-wrap:wrap;align-items:center;max-width:100%}
  #hdrAuthBtn,.hdr .hdr-auth{flex-wrap:wrap;max-width:100%}
  [data-fe70-ask="mob"]{display:inline-flex!important;align-items:center;justify-content:center;min-width:44px;min-height:44px}
  [data-fe70-ask="desk"]{display:none!important}
}
@media (min-width:768px){
  .hdr{display:none!important}
  .cmd-bar{position:relative;z-index:260}
  [data-fe70-ask="desk"]{display:inline-flex!important;align-items:center;justify-content:center;min-width:44px;min-height:44px;position:relative;z-index:261}
  [data-fe70-ask="mob"]{display:none!important}
}
</style>"""
ASK_DESK = """<button type="button" class="hdr-act-btn" data-fe70-ask="desk" onclick="_openResearchAssistant('What matters most in markets right now?')">Ask</button>"""
ASK_MOB = """<button type="button" class="hdr-act-btn" data-fe70-ask="mob" onclick="_openResearchAssistant('What matters most in markets right now?')">Ask</button>"""

if not s.startswith("const DISPATCH_ASSET_VERSION"):
    die('app.js does not start at the asset version')
s = SHIM + s

start = s.find("function fe68_storyTag(")
end = s.find("\nfunction fe68_ms(")
if start < 0 or end < start or s.count("function fe68_storyTag(") != 1:
    die('story tag anchor missing')
s = s[:start] + STORY + s[end+1:]

s = subn(s, '    status = "rth-close"; label = "RTH CLOSE";',
    '    status = "closed"; label = "CLOSED";', 'rth close')
s = subn(s, '            if(row?.usd>0&&_applyLiveQuote(sym,{p:row.usd,c:typeof row.usd_24h_change==="number"?row.usd_24h_change:0,prev:row.usd/(1+(row.usd_24h_change||0)/100)},"coingecko"))_refreshView();',
    '            if(row?.usd>0){const q={p:row.usd,prev:row.usd};if(typeof row.usd_24h_change==="number"){q.c=row.usd_24h_change;q.prev=row.usd/(1+(row.usd_24h_change/100));}if(_applyLiveQuote(sym,q,"coingecko"))_refreshView();}',
    'cg change')
s = subn(s, '              const c=typeof row.usd_24h_change==="number"?row.usd_24h_change:0;\n              priceInfo={p:row.usd,c,prev:row.usd/(1+c/100),_src:"coingecko"};',
    '              const c=typeof row.usd_24h_change==="number"?row.usd_24h_change:null;\n              priceInfo={p:row.usd,c:c,prev:c==null?row.usd:row.usd/(1+c/100),_src:"coingecko"};',
    'lookup change')
s = subn(s, '        c: typeof priceInfo.c === "number" ? priceInfo.c : 0,',
    '        c: typeof priceInfo.c === "number" ? priceInfo.c : undefined,',
    'apply change')
s = subn(s, '        if (res.ok && data.brief) {\n          _brief = _rt18BriefClean(data.brief);',
    '        if (res.ok && data.brief) {\n          _brief = _rt18BriefClean(data.brief);\n          try { fe70_stamp(_brief, data); } catch (e) {}',
    'brief stamp')
s = subn(s, """  const ordered=[
    ...TAPE_ORDER.filter(k=>liveSymbols.has(k)),
    ...live.filter(k=>!TAPE_ORDER.includes(k)).sort(),
  ];""",
"""  const ordered=(typeof fe70_dedupe==="function"?fe70_dedupe:function(x){return x;})([
    ...TAPE_ORDER.filter(k=>liveSymbols.has(k)),
    ...live.filter(k=>!TAPE_ORDER.includes(k)).sort(),
  ]);""", 'tape dedupe')
s = subn(s, 'return `<span class="ti" data-tk="${k}" title=',
    'return `<span class="ti" data-tk="${k}" data-st="${_escAttr(d.status||"")}" data-as="${Number(d.asOf)||0}" title=',
    'tape attrs')
s = subn(s, 'function _renderNewsBodyInner(opts){\n  const compact=!!opts?.compact;',
    'function _renderNewsBodyInner(opts){\n  if (typeof fe70_newsHold === "function" && fe70_newsHold()) return \'<div class="gc" style="padding:20px;text-align:center"><div style="font-size:12px;color:var(--t2)">Loading headlines\\u2026</div></div>\';\n  const compact=!!opts?.compact;',
    'news body')
s = subn(s, 'h+=`<div class="news-result-meta"><span id="news-result-count">${shown} shown</span> · ${NEWS.length} loaded · ${worldN} world · ${RSS_FEEDS.length} feeds${newsQ?` · filter “${_escHtml(newsQ)}”`:""}</div>`;',
    'h+=`<div class="news-result-meta">${(typeof fe70_newsHold==="function"&&fe70_newsHold())?\'<span id="news-result-count">Loading headlines\\u2026</span>\':(\'<span id="news-result-count">\'+shown+\' shown</span> · \'+NEWS.length+\' loaded · \'+worldN+\' world · \'+RSS_FEEDS.length+\' feeds\'+(newsQ?\' · filter “\'+_escHtml(newsQ)+\'”\':""))}</div>`;',
    'news count')
s = subn(s, '  newsFetching=false;renderStatus();_syncTapePulse();',
    '  newsFetching=false;renderStatus();_syncTapePulse();\n  try { if (typeof NEWS !== "undefined" && NEWS.length) fe70_newsReady = true; else if (typeof fe70_afterNews === "function") fe70_afterNews(); } catch (e) {}',
    'news retry')
s = subn(s, 'try { const keyNext = {}; A.forEach(a => { const k = _rt51Grp(a)',
    'try { const keyNext = {}; (typeof fe70_universe==="function"?fe70_universe():A).forEach(a => { const k = _rt51Grp(a)',
    'panel book')
s = subn(s, 'const open = _rt18MarketOpen(a.tk); if (_rt39Live(a.tk)) { G.live++; o.live++; } else if (open) { G.quiet.push(a.tk); o.quiet++; } else {',
    'const open = _rt18MarketOpen(a.tk); if (_rt39Live(a.tk)) { G.live++; o.live++; } else if (typeof fe70_opening==="function" && fe70_opening(a.tk)) { G.opening = (G.opening||[]).concat([a.tk]); } else if (open) { G.quiet.push(a.tk); o.quiet++; } else {',
    'opening quiet')
s = subn(s, 'A.filter(a => _rt51Grp(a) === G.k)',
    '(typeof fe70_universe==="function"?fe70_universe():A).filter(a => _rt51Grp(a) === G.k)',
    'panel list')
s = subn(s, "if (hasSyncedQuote(a.tk)) { if (_rt39Live(a.tk)) { st = 'trading'; c = 'rt51-ok'; } else if (_rt18MarketOpen(a.tk)) st = 'quiet'; else { const nx = _rt51Next(a.tk); st = `closed${nx ? ' · opens ' + _rt51When(nx) : ''}`; } }",
    "if (typeof fe70_sess === \"function\") { const ss = fe70_sess(a.tk); st = ss.st; c = ss.c; } else if (hasSyncedQuote(a.tk)) { if (_rt39Live(a.tk)) { st = 'trading'; c = 'rt51-ok'; } else if (_rt18MarketOpen(a.tk)) st = 'quiet'; else { const nx = _rt51Next(a.tk); st = `closed${nx ? ' · opens ' + _rt51When(nx) : ''}`; } }",
    'panel status')
s = subn(s, ' Exchange holidays are not shown.', '', 'holiday footnote', 2)
s = subn(s, """function fe69_beforeDate(win) {
  if (!win) return "";
  var raw = win.next != null && String(win.next).trim() !== "" ? String(win.next) : (win.from != null ? String(win.from) : "");
  var m = raw.match(/(\\d{4}-\\d{2}-\\d{2})/);
  return m ? m[1] : "";
}
function fe69_hasNext(win) {
  return !!(win && win.next != null && String(win.next).trim() !== "");
}""",
"""function fe69_beforeDate(win) {
  if (!win) return "";
  var raw = win.next;
  if (raw && typeof raw === "object") raw = raw.before != null ? raw.before : (raw.date != null ? raw.date : "");
  if (raw == null || String(raw).trim() === "" || String(raw) === "[object Object]") raw = win.from != null ? win.from : "";
  var m = String(raw == null ? "" : raw).match(/(\\d{4}-\\d{2}-\\d{2})/);
  return m ? m[1] : "";
}
function fe69_hasNext(win) {
  if (!win || win.next == null) return false;
  return !!fe69_beforeDate({ next: win.next });
}""", 'older cursor')
s = subn(s, """    var got = await fe69_fetchIns(q);
    var data = got.data || {};
    if (data.meta && data.meta.window) fe69_win[tk] = data.meta.window;
    else fe69_win[tk] = Object.assign({}, win, { next: "" });
    fe69_extra[tk] = fe69_mergeRows(fe69_extra[tk] || [], data.insider || []);
    var root = fe69_insRoot("");""",
"""    fe69_loadOlder.url = q;
    var prevN = (fe69_extra[tk] || []).length;
    var got = await fe69_fetchIns(q);
    var data = got.data || {};
    fe69_extra[tk] = fe69_mergeRows(fe69_extra[tk] || [], data.insider || []);
    var grew = (fe69_extra[tk] || []).length > prevN;
    if (data.meta && data.meta.window && grew && fe69_hasNext(data.meta.window)) fe69_win[tk] = data.meta.window;
    else fe69_win[tk] = Object.assign({}, (data.meta && data.meta.window) || win || {}, { next: "" });
    var root = fe69_insRoot(fe69_loadOlder.rootId || "");""",
    'load older')
s = subn(s, 'body.fe68-lenses .panel-body{min-height:0!important}',
    'body.fe68-lenses .panel-body{min-height:0!important}body.fe68-lenses .panel.p-expanded{position:relative!important;inset:auto!important;height:auto!important;min-height:0!important}',
    'lenses gap')

s = s + "\n" + BLOCK
if "function fe70_openingLine" not in s: die('opening helper missing')
if "No PDF text library" in s: die('house note was rewritten')
h = subn(h, '<link rel="stylesheet" href="/styles.css?v=chat1">', CRITICAL + '<link rel="stylesheet" href="/styles.css?v=chat1">', 'critical css')
h = subn(h, '<div id="cmdAuthBtn"', ASK_DESK + '\n  <div id="cmdAuthBtn"', 'desk ask')
h = subn(h, '<button class="info-btn"', ASK_MOB + '\n    <button class="info-btn"', 'mob ask')
h2 = re.sub(r'app\.js\?v=chat\d+"', 'app.js?v=%s"' % nxt, h, count=1)
out = s.replace('\n', '\r\n').encode('utf-8') if crlf else s.encode('utf-8')
tmp = tempfile.NamedTemporaryFile('wb', suffix='.js', delete=False)
tmp.write(out); tmp.close()
try:
    chk = subprocess.run(['node', '--check', tmp.name], capture_output=True, text=True)
finally:
    os.unlink(tmp.name)
if chk.returncode != 0:
    die('node --check failed\n' + (chk.stderr or chk.stdout or ''))
if not CHECK:
    open(APP, 'wb').write(out)
    open(IDX, 'wb').write(h2.replace('\n', '\r\n').encode('utf-8') if hcrlf else h2.encode('utf-8'))
print('OK', nxt, 'app.md5', hashlib.md5(out).hexdigest())
