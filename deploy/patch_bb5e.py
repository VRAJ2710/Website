#!/usr/bin/env python3
"""patch_bb5e.py — a closed venue is not a stale print.

Chat63 plus bb5b plus bb5c plus bb5d. Server.js only. Does not rewrite
app.js or index.html and does not bump the client cache token.

bb5d labelled a quote stale from print age alone. Outside the venue's own
session that last print is closed, not stale. Thin onshore FX (INR, BRL,
and KRW/TWD/IDR/PHP if asked) is quiet on a weekday while the local desk
is shut, and closed on the weekend. Majors stay on the 24/5 FX rule.

The CLOSED-badge calendar is not in server.js. It is ported from app.js:
_RT18_IDX, the original NY cash / FX / futures rule, the rt38 VEN table,
the rt43 lunch windows for .T and .HK listings, and the rt51 commodity
windows. No holiday list exists there, so none is added. A marketState or
currentTradingPeriod already on the v7 row or chart meta wins, with the
table as the fallback. No extra request is made.

BRL, TWD, IDR and PHP have no window in that client table. BRL uses the
B3 cash session (America/Sao_Paulo 10:00-17:00). TWD uses TWSE
(Asia/Taipei 09:00-13:30), IDR uses IDX (Asia/Jakarta 09:00-15:00) and
PHP uses PSE (Asia/Manila 09:30-15:00). INR uses the existing NSE window
and KRW uses the existing KRX window.

Usage: python3 patch_bb5e.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "4b094d30cc5070c2ca44d7979452d648",
    "index.html": "0e595097e68bcf2f8c0c90395add2880",
    "server.js": "2e0bb821abcd3030a8e0fa717de373be",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def show(phase, name, raw):
    digest = hashlib.md5(raw).hexdigest()
    print("bb5e %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def read_bytes(path):
    if not os.path.isfile(path):
        return None
    return open(path, "rb").read()

raw = read_bytes(SRV)
if raw is None:
    die("server.js missing in %s" % D)
v = raw.decode("utf-8").replace("\r\n", "\n")
vcrlf = b"\r\n" in raw
app_before = read_bytes(APP)
idx_before = read_bytes(IDX)

digest = show("before", "server.js", raw)
if digest != EXPECTED_MD5["server.js"]:
    print("WARN md5 server.js: have %s expected %s (anchors still decide)" % (digest, EXPECTED_MD5["server.js"]))
for label, blob in (("app.js", app_before), ("index.html", idx_before)):
    if blob is None:
        print("bb5e before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb5e %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb5e \u2500\u2500" in v:
    print("REFUSE: bb5e already applied")
    sys.exit(0)

ROW_OLD = """  return bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: row.currency,
    basis: isFinite(prevRaw) && prevRaw > 0 ? "previous_close" : "none",
    exchange: row.fullExchangeName || row.exchange || "",
    name: row.longName || row.shortName || row.symbol || "",
    ts: row.regularMarketTime,
    delayMin: Number(row.exchangeDataDelayedBy) > 0 ? Number(row.exchangeDataDelayedBy) : 0
  }, Number(row.exchangeDataDelayedBy));"""
ROW_NEW = """  return bb5eApply(bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: row.currency,
    basis: isFinite(prevRaw) && prevRaw > 0 ? "previous_close" : "none",
    exchange: row.fullExchangeName || row.exchange || "",
    name: row.longName || row.shortName || row.symbol || "",
    ts: row.regularMarketTime,
    delayMin: Number(row.exchangeDataDelayedBy) > 0 ? Number(row.exchangeDataDelayedBy) : 0
  }, Number(row.exchangeDataDelayedBy)), row && row.symbol, row);"""

CHART_OLD = """  return bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: meta.currency,
    basis: basis ? basis.basis : "none",
    exchange: meta.exchangeName,
    name: meta.longName || meta.shortName || symbol,
    ts: meta.regularMarketTime,
    delayMin: isFinite(delay) && delay > 0 ? delay : 0
  }, delay);"""
CHART_NEW = """  return bb5eApply(bb5dAnnotate({
    p: price,
    c: prev ? ((price - prev) / prev) * 100 : 0,
    prev: prev,
    change: price - prev,
    currency: meta.currency,
    basis: basis ? basis.basis : "none",
    exchange: meta.exchangeName,
    name: meta.longName || meta.shortName || symbol,
    ts: meta.regularMarketTime,
    delayMin: isFinite(delay) && delay > 0 ? delay : 0
  }, delay), symbol, meta);"""

miss = []
if "// \u2500\u2500 bb5d \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5d ──")
if v.count(ROW_OLD) != 1:
    miss.append("server.js anchor bb5dFromRow matched %d times" % v.count(ROW_OLD))
if v.count(CHART_OLD) != 1:
    miss.append("server.js anchor bb5dChartOne matched %d times" % v.count(CHART_OLD))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(ROW_OLD, ROW_NEW, 1).replace(CHART_OLD, CHART_NEW, 1)

BLOCK = r'''
// ── bb5e ── A closed venue is not a stale print. Calendar ported from app.js; no holiday list.
// BB5E_JS
var bb5eFmt = {};
var bb5eIdx = {
  FTSE: ["Europe/London", 480, 990, "London"], "^FTSE": ["Europe/London", 480, 990, "London"],
  DAX: ["Europe/Berlin", 540, 1050, "Frankfurt"], "^GDAXI": ["Europe/Berlin", 540, 1050, "Frankfurt"],
  CAC: ["Europe/Paris", 540, 1050, "Paris"], "^FCHI": ["Europe/Paris", 540, 1050, "Paris"],
  STOXX50: ["Europe/Berlin", 540, 1050, "Frankfurt"],
  N225: ["Asia/Tokyo", 540, 930, "Tokyo"], "^N225": ["Asia/Tokyo", 540, 930, "Tokyo"],
  HSI: ["Asia/Hong_Kong", 570, 960, "Hong Kong"], "^HSI": ["Asia/Hong_Kong", 570, 960, "Hong Kong"],
  NSEI: ["Asia/Kolkata", 555, 930, "India"], "^NSEI": ["Asia/Kolkata", 555, 930, "India"],
  ASX200: ["Australia/Sydney", 600, 960, "Sydney"], "^AXJO": ["Australia/Sydney", 600, 960, "Sydney"],
  KOSPI: ["Asia/Seoul", 540, 930, "Korea"], "^KS11": ["Asia/Seoul", 540, 930, "Korea"]
};
var bb5eThin = {
  USDINR: ["Asia/Kolkata", 555, 930, "India"], "INR=X": ["Asia/Kolkata", 555, 930, "India"],
  USDBRL: ["America/Sao_Paulo", 600, 1020, "Brazil"], "BRL=X": ["America/Sao_Paulo", 600, 1020, "Brazil"],
  USDKRW: ["Asia/Seoul", 540, 930, "Korea"], "KRW=X": ["Asia/Seoul", 540, 930, "Korea"],
  USDTWD: ["Asia/Taipei", 540, 810, "Taipei"], "TWD=X": ["Asia/Taipei", 540, 810, "Taipei"],
  USDIDR: ["Asia/Jakarta", 540, 900, "Jakarta"], "IDR=X": ["Asia/Jakarta", 540, 900, "Jakarta"],
  USDPHP: ["Asia/Manila", 570, 900, "Manila"], "PHP=X": ["Asia/Manila", 570, 900, "Manila"]
};
var bb5eFx = { EURUSD: 1, GBPUSD: 1, USDJPY: 1, AUDUSD: 1, USDCAD: 1, USDCHF: 1, NZDUSD: 1, EURGBP: 1, EURJPY: 1, GBPJPY: 1, USDMXN: 1, USDSEK: 1, DXY: 1, "DX-Y.NYB": 1, "EURUSD=X": 1, "GBPUSD=X": 1, "JPY=X": 1, "AUDUSD=X": 1, "CAD=X": 1, "CHF=X": 1, "NZDUSD=X": 1, "EURGBP=X": 1, "EURJPY=X": 1, "GBPJPY=X": 1, "MXN=X": 1, "SEK=X": 1 };
var bb5eCoin = { BTC: 1, ETH: 1, SOL: 1, XRP: 1, DOGE: 1, ADA: 1, AVAX: 1, LINK: 1, DOT: 1, LTC: 1, UNI: 1, POL: 1, NEAR: 1, ALGO: 1, HBAR: 1, BCH: 1, XLM: 1, FIL: 1, APT: 1, SUI: 1, ATOM: 1, INJ: 1, SHIB: 1, PEPE: 1, TON: 1 };
var bb5eSoft = { COFFEE: [255, 810], "KC=F": [255, 810], COCOA: [285, 810], "CC=F": [285, 810], OJ: [480, 840], "OJ=F": [480, 840], SUGAR: [210, 780] };
var bb5eCbot = { WHEAT: 1, CORN: 1, SOYBEAN: 1, SOYBEANS: 1, SOY: 1, OATS: 1, "ZW=F": 1, "ZC=F": 1, "ZS=F": 1, "ZO=F": 1 };
var bb5eLumber = { LUMBER: 1, "LBR=F": 1 };
function bb5eNow() {
  try {
    if (typeof globalThis.bb5eClock === "function") {
      var n = Number(globalThis.bb5eClock());
      if (isFinite(n)) return n;
    }
  } catch (e) {}
  return Date.now();
}
function bb5eCanon(symbol) {
  return String(symbol || "").trim().toUpperCase();
}
function bb5eParts(tz, d) {
  var fmt = bb5eFmt[tz];
  if (!fmt) {
    fmt = new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false });
    bb5eFmt[tz] = fmt;
  }
  var o = {};
  fmt.formatToParts(d).forEach(function (part) { o[part.type] = part.value; });
  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };
}
function bb5eWeekday(wd) {
  return wd === "Mon" || wd === "Tue" || wd === "Wed" || wd === "Thu" || wd === "Fri";
}
function bb5eCash(tz, o, c, label, lo, lc) {
  var spec = { mode: "cash", tz: tz, o: o, c: c, label: label };
  if (lo != null) { spec.lo = lo; spec.lc = lc; }
  return spec;
}
function bb5eSpec(symbol) {
  var s = bb5eCanon(symbol);
  var thin = bb5eThin[s];
  if (thin) return { mode: "thin", quiet: true, tz: thin[0], o: thin[1], c: thin[2], label: thin[3] };
  var idx = bb5eIdx[s];
  if (idx) return bb5eCash(idx[0], idx[1], idx[2], idx[3]);
  if (/\.T$/.test(s)) return bb5eCash("Asia/Tokyo", 540, 930, "Tokyo", 690, 750);
  if (/\.KS$/.test(s)) return bb5eCash("Asia/Seoul", 540, 930, "Korea");
  if (/\.HK$/.test(s)) return bb5eCash("Asia/Hong_Kong", 570, 960, "Hong Kong", 720, 780);
  if (/\.L$/.test(s)) return bb5eCash("Europe/London", 480, 990, "London");
  if (/\.DE$/.test(s)) return bb5eCash("Europe/Berlin", 540, 1050, "Frankfurt");
  if (/\.PA$/.test(s)) return bb5eCash("Europe/Paris", 540, 1050, "Paris");
  if (/\.AX$/.test(s)) return bb5eCash("Australia/Sydney", 600, 960, "Sydney");
  if (/\.NS$/.test(s)) return bb5eCash("Asia/Kolkata", 555, 930, "India");
  if (bb5eCoin[s] || /-USD$/.test(s)) return { mode: "always", label: "Crypto" };
  if (bb5eSoft[s]) return { mode: "soft", o: bb5eSoft[s][0], c: bb5eSoft[s][1], label: "US" };
  if (bb5eCbot[s]) return { mode: "cbot", label: "US" };
  if (bb5eLumber[s]) return { mode: "lumber", label: "US" };
  if (/=F$/.test(s)) return { mode: "fut", label: "US" };
  if (bb5eFx[s] || /=X$/.test(s)) return { mode: "fx", label: "FX" };
  return bb5eCash("America/New_York", 570, 960, "US");
}
function bb5eWindow(spec, d) {
  var p = bb5eParts(spec.tz, d);
  if (p.wd === "Sat" || p.wd === "Sun") return false;
  if (spec.lo != null && p.m >= spec.lo && p.m < spec.lc) return false;
  return p.m >= spec.o && p.m < spec.c;
}
function bb5eFxOpen(d) {
  var p = bb5eParts("America/New_York", d);
  if (p.wd === "Sat") return false;
  if (p.wd === "Fri" && p.m >= 1020) return false;
  if (p.wd === "Sun" && p.m < 1020) return false;
  return true;
}
function bb5eFutOpen(d) {
  var p = bb5eParts("America/New_York", d);
  if (p.wd === "Sat") return false;
  if (p.wd === "Fri" && p.m >= 1020) return false;
  if (p.wd === "Sun" && p.m < 1080) return false;
  if (p.m >= 1020 && p.m < 1080) return false;
  return true;
}
function bb5eCbotOpen(d) {
  var p = bb5eParts("America/Chicago", d);
  var evening = (p.wd === "Sun" || p.wd === "Mon" || p.wd === "Tue" || p.wd === "Wed" || p.wd === "Thu") && p.m >= 1140;
  var day = bb5eWeekday(p.wd) && (p.m < 465 || (p.m >= 510 && p.m < 800));
  return evening || day;
}
function bb5eSoftOpen(spec, d) {
  var p = bb5eParts("America/New_York", d);
  return bb5eWeekday(p.wd) && p.m >= spec.o && p.m < spec.c;
}
function bb5eLumberOpen(d) {
  var p = bb5eParts("America/Chicago", d);
  return bb5eWeekday(p.wd) && p.m >= 540 && p.m < 905;
}
function bb5eOpenAt(spec, d) {
  try {
    if (!spec || spec.mode === "always") return true;
    if (spec.mode === "fx") return bb5eFxOpen(d);
    if (spec.mode === "fut") return bb5eFutOpen(d);
    if (spec.mode === "cbot") return bb5eCbotOpen(d);
    if (spec.mode === "soft") return bb5eSoftOpen(spec, d);
    if (spec.mode === "lumber") return bb5eLumberOpen(d);
    return bb5eWindow(spec, d);
  } catch (e) { return true; }
}
function bb5eOffday(spec, d) {
  try {
    var tz = spec && (spec.mode === "fx" || spec.mode === "fut") ? "America/New_York" : (spec && spec.tz) || "America/New_York";
    var p = bb5eParts(tz, d);
    return p.wd === "Sat" || p.wd === "Sun";
  } catch (e) { return false; }
}
function bb5eMs(v) {
  var n = Number(v);
  if (!isFinite(n) || n <= 0) return 0;
  return n < 1e12 ? n * 1000 : n;
}
function bb5eYahoo(hints, now) {
  if (!hints || typeof hints !== "object") return { known: false, open: false, next: 0 };
  var state = String(hints.marketState || "").toUpperCase();
  var reg = hints.currentTradingPeriod && hints.currentTradingPeriod.regular;
  var start = reg ? bb5eMs(reg.start) : 0;
  var end = reg ? bb5eMs(reg.end) : 0;
  var shut = state === "CLOSED" || state === "PRE" || state === "PREPRE" || state === "POST" || state === "POSTPOST";
  if (state === "REGULAR") return { known: true, open: true, next: 0 };
  if (shut) return { known: true, open: false, next: start > now ? start : 0 };
  if (start && end && now >= start && now < end) return { known: true, open: true, next: 0 };
  if (start && end) return { known: true, open: false, next: start > now ? start : 0 };
  return { known: false, open: false, next: 0 };
}
function bb5eNext(spec, now, yahooNext, force) {
  if (yahooNext && yahooNext > now) return yahooNext;
  var start = now;
  if (force) {
    var walk = now;
    var guard = now + 18 * 3600000;
    while (walk < guard && bb5eOpenAt(spec, new Date(walk))) walk += 300000;
    start = walk;
  }
  var slot = Math.ceil((start + 1) / 900000) * 900000;
  for (var k = 0; k < 8 * 96; k++, slot += 900000) {
    if (bb5eOpenAt(spec, new Date(slot))) return slot;
  }
  return 0;
}
function bb5eLondon(ms, now) {
  var tz = "Europe/London";
  var d = new Date(ms);
  var day = function (x) { return new Intl.DateTimeFormat("en-CA", { timeZone: tz }).format(x); };
  var hm = new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(d);
  var wd = day(d) === day(new Date(now)) ? "" : new Intl.DateTimeFormat("en-GB", { timeZone: tz, weekday: "short" }).format(d) + " ";
  return wd + hm;
}
function bb5eLive(q, now) {
  var delay = Number(q && q.delayMin);
  if (!isFinite(delay) || delay < 0) delay = 0;
  delay = Math.round(delay);
  var ts = Number(q && q.ts);
  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;
  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;
  if (typeof bb5dClass === "function") return bb5dClass(age, delay);
  var note = delay > 0 ? "delayed " + delay + "m by exchange" : "";
  var cadence = typeof bb5dCadenceMs === "number" ? bb5dCadenceMs : 60000;
  var margin = typeof bb5dMarginMs === "number" ? bb5dMarginMs : 120000;
  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? "delayed" : "fresh", stale: false, note: note };
  if (Number(age) > cadence + delay * 60000 + margin) return { delayMin: delay, status: "stale", stale: true, note: "" };
  if (delay > 0) return { delayMin: delay, status: "delayed", stale: false, note: note };
  return { delayMin: 0, status: "fresh", stale: false, note: "" };
}
function bb5eNote(spec, status, next, now) {
  var when = next ? bb5eLondon(next, now) : "";
  if (status === "quiet") return when ? "quiet · local market opens " + when + " UK" : "quiet";
  var label = (spec && spec.label) || "Market";
  if (!when) return label + " market closed";
  return label + " market closed · opens " + when + " UK";
}
function bb5eApply(q, symbol, hints, now) {
  if (!q || typeof q !== "object") return q;
  var out = {};
  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];
  var t = now == null ? bb5eNow() : Number(now);
  if (!isFinite(t)) t = bb5eNow();
  var spec = bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);
  var tableOpen = bb5eOpenAt(spec, new Date(t));
  var open = yahoo.known ? yahoo.open : tableOpen;
  if (open) {
    var cls = bb5eLive(out, t);
    out.delayMin = cls.delayMin;
    out.status = cls.status;
    out.stale = cls.stale;
    if (cls.note) out.note = cls.note;
    else delete out.note;
    delete out.nextOpen;
    return out;
  }
  var next = bb5eNext(spec, t, yahoo.next, yahoo.known && !yahoo.open && tableOpen);
  var status = spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed";
  out.status = status;
  out.stale = false;
  if (next) out.nextOpen = new Date(next).toISOString();
  else delete out.nextOpen;
  out.note = bb5eNote(spec, status, next, t);
  return out;
}
// BB5E_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb5e")]
if bad:
    die("bb5e block declares a non-bb5e function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb5e block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb5e block has a forbidden declaration")
if v.count("return bb5eApply(bb5dAnnotate(") != 2:
    die("bb5e wiring count is %d" % v.count("return bb5eApply(bb5dAnnotate("))

v = v.rstrip("\n") + "\n" + BLOCK
print("server-only: app.js and index.html are not modified")

def nodecheck(src, label):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(src)
        tmp = t.name
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        die("node --check failed for %s: %s" % (label, r.stderr[:500]))

nodecheck(v, "server.js")
print("node --check passed" + (" (dry run)" if CHECK else ""))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
    print("bb5e app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb5e index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb5ebak"
try:
    open(bak, "wb").write(raw)
    open(SRV, "wb").write(after_srv)
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("node --check failed after write: " + r.stderr[:400])
    if read_bytes(APP) != app_before or read_bytes(IDX) != idx_before:
        raise RuntimeError("app.js or index.html changed")
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("APPLY bb5e venue closed")
