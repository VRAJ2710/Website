#!/usr/bin/env python3
"""patch_bb6.py — exchange holidays close the shared classifier. Server.js only.

Stacked on bb5h (server md5 71b1739d8dcba7a6ca21b86cf35c0c43). Does not rewrite
app.js or index.html and does not bump the client cache token.

A holiday was falling through bb5eOpenAt, so Yahoo's period still looked open
and the print came back stale. bb6Shut fails that open check, drops Yahoo's
next timestamp, and turns a thin-FX quiet into closed. The note names the
holiday and, when the next session is an early close, says so.

Usage: python3 patch_bb6.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "b45b28623e1c8368140406558df95b90",
    "index.html": "b2271ff3debbf8790a4cdeb5a42b8297",
    "server.js": "71b1739d8dcba7a6ca21b86cf35c0c43",
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
    print("bb6 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb6 before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb6 %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb6 \u2500\u2500" in v:
    print("REFUSE: bb6 already applied")
    sys.exit(0)

OPEN_OLD = """function bb5eOpenAt(spec, d) {
  try {
    if (!spec || spec.mode === "always") return true;"""
OPEN_NEW = """function bb5eOpenAt(spec, d) {
  try {
    if (spec && spec.mode !== "always" && typeof bb6Shut === "function" && bb6Shut(spec, d)) return false;
    if (!spec || spec.mode === "always") return true;"""

SPEC_OLD = """  var spec = typeof bb5gSpec === "function" ? bb5gSpec(symbol) : bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);
  var tableOpen = bb5eOpenAt(spec, new Date(t));
  var open = typeof bb5fOpen === "function" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);"""
SPEC_NEW = """  var spec = typeof bb5gSpec === "function" ? bb5gSpec(symbol) : bb5eSpec(symbol);
  if (spec && symbol) spec.bb6Sym = symbol;
  var yahoo = bb5eYahoo(hints, t);
  var tableOpen = bb5eOpenAt(spec, new Date(t));
  var open = typeof bb5fOpen === "function" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);
  if (typeof bb6Shut === "function" && bb6Shut(spec, new Date(t))) open = false;"""

NOTE_OLD = """  var next = bb5eNext(spec, t, yahoo.next, yahoo.known && !yahoo.open && tableOpen);
  var status = typeof bb5fStatus === "function" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed");
  out.status = status;
  out.stale = false;
  if (next) out.nextOpen = new Date(next).toISOString();
  else delete out.nextOpen;
  out.note = bb5eNote(spec, status, next, t);"""
NOTE_NEW = """  var bb6Off = typeof bb6Shut === "function" && bb6Shut(spec, new Date(t));
  var next = bb5eNext(spec, t, bb6Off ? 0 : yahoo.next, yahoo.known && !yahoo.open && tableOpen && !bb6Off);
  var status = typeof bb5fStatus === "function" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed");
  if (bb6Off) status = "closed";
  out.status = status;
  out.stale = false;
  if (next) out.nextOpen = new Date(next).toISOString();
  else delete out.nextOpen;
  out.note = typeof bb6Note === "function" ? bb6Note(spec, status, next, t) : bb5eNote(spec, status, next, t);"""

miss = []
if "// \u2500\u2500 bb5h \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb5h ──")
for name, old in (
    ("bb5eOpenAt", OPEN_OLD),
    ("bb5eApply spec", SPEC_OLD),
    ("bb5eApply note", NOTE_OLD),
):
    n = v.count(old)
    if n != 1:
        miss.append("server.js anchor %s matched %d times" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(OPEN_OLD, OPEN_NEW, 1)
v = v.replace(SPEC_OLD, SPEC_NEW, 1)
v = v.replace(NOTE_OLD, NOTE_NEW, 1)

BLOCK = r'''
// ── bb6 ── A listed holiday is closed, including a refill. Early closes name the next session.
// BB6_JS
// NYSE and Nasdaq, 2026 and 2027. 13:00 ET is minute 780.
// https://www.nyse.com/markets/hours-calendars
// https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx
var bb6UsFull = {
  "2026-01-01": "New Year's Day", "2026-01-19": "Martin Luther King Jr. Day", "2026-02-16": "Washington's Birthday",
  "2026-04-03": "Good Friday", "2026-05-25": "Memorial Day", "2026-06-19": "Juneteenth",
  "2026-07-03": "Independence Day", "2026-09-07": "Labor Day", "2026-11-26": "Thanksgiving", "2026-12-25": "Christmas Day",
  "2027-01-01": "New Year's Day", "2027-01-18": "Martin Luther King Jr. Day", "2027-02-15": "Washington's Birthday",
  "2027-03-26": "Good Friday", "2027-05-31": "Memorial Day", "2027-06-18": "Juneteenth",
  "2027-07-05": "Independence Day", "2027-09-06": "Labor Day", "2027-11-25": "Thanksgiving", "2027-12-24": "Christmas Day"
};
var bb6UsEarly = { "2026-11-27": ["Day after Thanksgiving", 780], "2026-12-24": ["Christmas Eve", 780], "2027-11-26": ["Day after Thanksgiving", 780] };
// LSE cash. The official table began at 31 Aug 2026 when it was read, so earlier 2026 dates are omitted. Half-day close 12:30 London is minute 750.
// https://www.londonstockexchange.com/equities-trading/business-days
var bb6LseFull = {
  "2026-08-31": "Summer Bank Holiday", "2026-12-25": "Christmas Day", "2026-12-28": "Boxing Day",
  "2027-01-01": "New Year's Day", "2027-03-26": "Good Friday", "2027-03-29": "Easter Monday",
  "2027-05-03": "Early May Bank Holiday", "2027-05-31": "Spring Bank Holiday", "2027-08-30": "Summer Bank Holiday",
  "2027-12-27": "Christmas Day", "2027-12-28": "Boxing Day"
};
var bb6LseEarly = {
  "2026-12-24": ["Christmas Eve", 750], "2026-12-31": ["New Year's Eve", 750],
  "2027-12-24": ["Christmas Eve", 750], "2027-12-31": ["New Year's Eve", 750]
};
// JPX cash equities. Closed Sat/Sun, national holidays, 1-3 Jan and 31 Dec. Not the derivatives holiday-trading calendar.
// https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html
// https://www.jpx.co.jp/corporate/about-jpx/calendar/
// https://www.jpx.co.jp/english/equities/trading/domestic/01.html
var bb6JpxFull = {
  "2026-01-01": "New Year's Day", "2026-01-02": "market holiday", "2026-01-12": "Coming of Age Day",
  "2026-02-11": "National Foundation Day", "2026-02-23": "Emperor's Birthday", "2026-03-20": "Vernal Equinox",
  "2026-04-29": "Showa Day", "2026-05-04": "Greenery Day", "2026-05-05": "Children's Day", "2026-05-06": "substitute holiday",
  "2026-07-20": "Marine Day", "2026-08-11": "Mountain Day", "2026-09-21": "Respect for the Aged Day",
  "2026-09-22": "Citizen's Holiday", "2026-09-23": "Autumnal Equinox", "2026-10-12": "Sports Day",
  "2026-11-03": "Culture Day", "2026-11-23": "Labor Thanksgiving Day", "2026-12-31": "market holiday",
  "2027-01-01": "New Year's Day", "2027-01-11": "Coming of Age Day", "2027-02-11": "National Foundation Day",
  "2027-02-23": "Emperor's Birthday", "2027-03-22": "substitute holiday", "2027-04-29": "Showa Day",
  "2027-05-03": "Constitution Memorial Day", "2027-05-04": "Greenery Day", "2027-05-05": "Children's Day",
  "2027-07-19": "Marine Day", "2027-08-11": "Mountain Day", "2027-09-20": "Respect for the Aged Day",
  "2027-09-23": "Autumnal Equinox", "2027-10-11": "Sports Day", "2027-11-03": "Culture Day",
  "2027-11-23": "Labor Thanksgiving Day", "2027-12-31": "market holiday"
};
// HKEX securities. Half-day means no afternoon session, close 12:00 HKT, minute 720. Lunar dates are from the circulars.
// https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/ce_SEHK_CT_075_2025.pdf
// https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2026/ce_SEHK_CT_077_2026.pdf
var bb6HkFull = {
  "2026-01-01": "New Year's Day", "2026-02-17": "Lunar New Year", "2026-02-18": "Lunar New Year", "2026-02-19": "Lunar New Year",
  "2026-04-03": "Good Friday", "2026-04-06": "day after Ching Ming", "2026-04-07": "day after Easter Monday",
  "2026-05-01": "Labour Day", "2026-05-25": "day after Buddha's Birthday", "2026-06-19": "Tuen Ng",
  "2026-07-01": "HKSAR Establishment Day", "2026-10-01": "National Day", "2026-10-19": "day after Chung Yeung", "2026-12-25": "Christmas Day",
  "2027-01-01": "New Year's Day", "2027-02-08": "Lunar New Year", "2027-02-09": "Lunar New Year",
  "2027-03-26": "Good Friday", "2027-03-29": "Easter Monday", "2027-04-05": "Ching Ming",
  "2027-05-13": "Buddha's Birthday", "2027-06-09": "Tuen Ng", "2027-07-01": "HKSAR Establishment Day",
  "2027-09-16": "day after Mid-Autumn", "2027-10-01": "National Day", "2027-10-08": "Chung Yeung", "2027-12-27": "Christmas"
};
var bb6HkEarly = {
  "2026-02-16": ["Lunar New Year's Eve", 720], "2026-12-24": ["Christmas Eve", 720], "2026-12-31": ["New Year's Eve", 720],
  "2027-02-05": ["Lunar New Year's Eve", 720], "2027-12-24": ["Christmas Eve", 720], "2027-12-31": ["New Year's Eve", 720]
};
// ASX cash. Early close 14:10 Sydney is minute 850. 26 Apr 2027 is a normal day (Sunday ANZAC is not observed as a close).
// https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours/trading-calendar
var bb6AsxFull = {
  "2026-01-01": "New Year's Day", "2026-01-26": "Australia Day", "2026-04-03": "Good Friday", "2026-04-06": "Easter Monday",
  "2026-06-08": "King's Birthday", "2026-12-25": "Christmas Day", "2026-12-28": "Boxing Day",
  "2027-01-01": "New Year's Day", "2027-01-26": "Australia Day", "2027-03-26": "Good Friday", "2027-03-29": "Easter Monday",
  "2027-06-14": "King's Birthday", "2027-12-27": "Christmas Day", "2027-12-28": "Boxing Day"
};
var bb6AsxEarly = {
  "2026-12-24": ["Christmas Eve", 850], "2026-12-31": ["New Year's Eve", 850],
  "2027-12-24": ["Christmas Eve", 850], "2027-12-31": ["New Year's Eve", 850]
};
// NSE equity cash, 2026 only. 2027 was not published. 8 Nov 2026 Muhurat is a Sunday and is not a full close.
// https://nsearchives.nseindia.com/content/circulars/CMTR71775.pdf
// https://www.nseindia.com/resources/exchange-communication-holidays
var bb6NseFull = {
  "2026-01-15": "Municipal Elections", "2026-01-26": "Republic Day", "2026-03-03": "Holi",
  "2026-03-26": "Ram Navami", "2026-03-31": "Mahavir Jayanti", "2026-04-03": "Good Friday",
  "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti", "2026-05-01": "Maharashtra Day", "2026-05-28": "Bakri Id",
  "2026-06-26": "Muharram", "2026-09-14": "Ganesh Chaturthi", "2026-10-02": "Gandhi Jayanti",
  "2026-10-20": "Dussehra", "2026-11-10": "Diwali-Balipratipada", "2026-11-24": "Guru Nanak Jayanti", "2026-12-25": "Christmas Day"
};
// NSE currency segment. Equity dates plus the currency circular's extra days. 2027 omitted.
// https://nsearchives.nseindia.com/content/circulars/CD71962.pdf
// https://nsearchives.nseindia.com/content/circulars/CD72233.pdf
var bb6InrFull = {
  "2026-01-15": "Municipal Elections", "2026-01-26": "Republic Day", "2026-02-19": "Chhatrapati Shivaji Maharaj Jayanti",
  "2026-03-03": "Holi", "2026-03-19": "Gudi Padwa", "2026-03-26": "Ram Navami", "2026-03-31": "Mahavir Jayanti",
  "2026-04-01": "Annual Bank Closing", "2026-04-03": "Good Friday", "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
  "2026-05-01": "Maharashtra Day", "2026-05-28": "Bakri Id", "2026-06-26": "Muharram", "2026-08-26": "Id-E-Milad",
  "2026-09-14": "Ganesh Chaturthi", "2026-10-02": "Gandhi Jayanti", "2026-10-20": "Dussehra",
  "2026-11-10": "Diwali-Balipratipada", "2026-11-24": "Guru Nanak Jayanti", "2026-12-25": "Christmas Day"
};
// B3, 2026 only. 18 Feb is a late open, not a full close, so it is omitted. 2027 was not published.
// https://www.b3.com.br/data/files/05/23/DB/C9/7992F91005A262F9AC094EA8/CL%20041-2026-VNC%20ERRATA%20-%20CALENDARIO%20DE%20FERIADOS%20EM%202026_EN.pdf
// https://www.b3.com.br/pt_br/noticias/calendario-de-negociacao-da-b3-confira-o-funcionamento-da-bolsa-em-2026.htm
var bb6B3Full = {
  "2026-01-01": "New Year's Day", "2026-02-16": "Carnival", "2026-02-17": "Carnival", "2026-04-03": "Good Friday",
  "2026-04-21": "Tiradentes", "2026-05-01": "Labor Day", "2026-06-04": "Corpus Christi", "2026-09-07": "Independence Day",
  "2026-10-12": "Our Lady of Aparecida", "2026-11-02": "All Souls' Day", "2026-11-20": "Black Awareness Day",
  "2026-12-24": "Christmas Eve", "2026-12-25": "Christmas Day", "2026-12-31": "New Year's Eve"
};
// KRX cash, only dates named by a KRX notice. 2027 is unpublished except 1 Jan from the 2026 year-end window.
// 1 Jan 2026 and 5 May 2026 were not in those notices, so they are omitted.
// https://kind.krx.co.kr/external/dst/notice/11637/[%ED%95%9C%EA%B5%AD%EA%B1%B0%EB%9E%98%EC%86%8C]%202026%EB%85%84%20%EC%98%AC%EB%B9%BC%EB%AF%B8%EA%B3%B5%EC%8B%9C%20%EC%95%88%EB%82%B4.pdf
// https://strn.krx.co.kr/corebbs5/BHPSTRN0401/list
var bb6KrxFull = {
  "2026-02-16": "Seollal", "2026-02-17": "Seollal", "2026-02-18": "Seollal", "2026-03-02": "Independence Movement Day",
  "2026-05-01": "Labor Day", "2026-05-25": "Buddha's Birthday", "2026-06-03": "local election",
  "2026-07-17": "Constitution Day", "2026-08-17": "Liberation Day", "2026-09-24": "Chuseok", "2026-09-25": "Chuseok",
  "2026-10-05": "National Foundation Day", "2026-10-09": "Hangeul Day", "2026-12-25": "Christmas Day",
  "2026-12-31": "year-end holiday", "2027-01-01": "New Year's Day"
};
// ICE Futures US softs (cocoa, coffee, cotton, FCOJ, sugar). Canadian-only closes are not included.
// https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_Exchange_Notice_2026_Holiday_Calendar_20260609.pdf
// https://www.ice.com/publicdocs/futures_us/exchange_notices/ICE_Futures_US_Exchange_Notice-2027_Holiday_Calendar_20260604.pdf
var bb6SoftFull = {
  "2026-01-01": "New Year's Day", "2026-01-19": "Martin Luther King Jr. Day", "2026-02-16": "Washington's Birthday",
  "2026-04-03": "Good Friday", "2026-05-25": "Memorial Day", "2026-06-19": "Juneteenth", "2026-07-03": "Independence Day",
  "2026-09-07": "Labor Day", "2026-11-26": "Thanksgiving", "2026-12-25": "Christmas Day",
  "2027-01-01": "New Year's Day", "2027-01-18": "Martin Luther King Jr. Day", "2027-02-15": "Washington's Birthday",
  "2027-03-26": "Good Friday", "2027-05-31": "Memorial Day", "2027-06-18": "Juneteenth", "2027-07-05": "Independence Day",
  "2027-09-06": "Labor Day", "2027-11-25": "Thanksgiving", "2027-12-24": "Christmas Day"
};
// ICE energy, only cells the notice marks closed. Other US holidays are "open" with hours announced later.
var bb6NrgFull = {
  "2026-01-01": "New Year's Day", "2026-04-03": "Good Friday", "2026-12-25": "Christmas Day",
  "2027-01-01": "New Year's Day", "2027-03-26": "Good Friday", "2027-12-24": "Christmas Day"
};
// ICE daily gold and silver, closed cells only. Applied to XAU, GC=F and XAU/USD.
var bb6GoldFull = {
  "2026-01-01": "New Year's Day", "2026-04-03": "Good Friday", "2026-05-25": "Memorial Day",
  "2026-12-25": "Christmas Day", "2026-12-28": "Boxing Day",
  "2027-01-01": "New Year's Day", "2027-03-26": "Good Friday", "2027-05-31": "Memorial Day",
  "2027-12-24": "Christmas Day", "2027-12-27": "Boxing Day"
};
// CME Globex. Holiday hours are a "Holiday Schedule" finalized about two weeks ahead, so this is not the NYSE list.
// The only outright "no trading" date on the hours page is Good Friday 2027. Floor closes are not Globex closes.
// https://www.cmegroup.com/trading-hours.html
var bb6CmeFull = { "2027-03-26": "Good Friday" };
var bb6Full = {
  us: bb6UsFull, lse: bb6LseFull, jpx: bb6JpxFull, hk: bb6HkFull, asx: bb6AsxFull,
  nse: bb6NseFull, inrc: bb6InrFull, b3: bb6B3Full, krx: bb6KrxFull,
  soft: bb6SoftFull, nrg: bb6NrgFull, gold: bb6GoldFull, cme: bb6CmeFull
};
var bb6Early = { us: bb6UsEarly, lse: bb6LseEarly, hk: bb6HkEarly, asx: bb6AsxEarly };
function bb6Day(tz, d) {
  try {
    return new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
  } catch (e) { return ""; }
}
function bb6Tz(spec) {
  if (!spec) return "America/New_York";
  if (spec.mode === "fut" || spec.mode === "soft") return "America/New_York";
  if (spec.mode === "lumber" || spec.mode === "cbot") return "America/Chicago";
  return spec.tz || "America/New_York";
}
function bb6Book(spec) {
  if (!spec || spec.mode === "always" || spec.mode === "fx") return null;
  var sym = String(spec.bb6Sym || "").toUpperCase();
  if (spec.mode === "soft") return "soft";
  if (spec.mode === "fut") {
    if (sym === "WTI" || sym === "BRENT" || sym === "CL=F" || sym === "BZ=F") return "nrg";
    if (sym === "XAU" || sym === "GC=F" || sym === "XAU/USD") return "gold";
    return "cme";
  }
  if (spec.mode === "cbot" || spec.mode === "lumber") return "cme";
  if (spec.mode === "thin") {
    if (spec.tz === "Asia/Kolkata") return "inrc";
    if (spec.tz === "America/Sao_Paulo") return "b3";
    return null;
  }
  if (spec.mode !== "cash") return null;
  if (spec.tz === "America/New_York" && spec.label === "US") return "us";
  if (spec.tz === "Europe/London") return "lse";
  if (spec.tz === "Asia/Tokyo") return "jpx";
  if (spec.tz === "Asia/Hong_Kong") return "hk";
  if (spec.tz === "Asia/Seoul") return "krx";
  if (spec.tz === "Australia/Sydney") return "asx";
  if (spec.tz === "Asia/Kolkata") return "nse";
  return null;
}
function bb6Hit(spec, d) {
  var book = bb6Book(spec);
  if (!book || !bb6Full[book]) return null;
  var day = bb6Day(bb6Tz(spec), d);
  if (!day) return null;
  if (bb6Full[book][day]) return { name: bb6Full[book][day], early: 0 };
  var early = bb6Early[book];
  if (early && early[day]) return { name: early[day][0], early: early[day][1] };
  return null;
}
function bb6Shut(spec, d) {
  try {
    var hit = bb6Hit(spec, d);
    if (!hit) return false;
    if (!hit.early) return true;
    var p = bb5eParts(bb6Tz(spec), d);
    return p.m >= hit.early;
  } catch (e) { return false; }
}
function bb6CloseAt(spec, next) {
  if (!next) return 0;
  try {
    var hit = bb6Hit(spec, new Date(next));
    if (!hit || !hit.early) return 0;
    var p = bb5eParts(bb6Tz(spec), new Date(next));
    return next + (hit.early - p.m) * 60000;
  } catch (e) { return 0; }
}
function bb6Note(spec, status, next, now) {
  if (status === "quiet" || typeof bb5eNote !== "function") return typeof bb5eNote === "function" ? bb5eNote(spec, status, next, now) : "";
  var hit = null;
  try { hit = bb6Hit(spec, new Date(now)); } catch (e) { hit = null; }
  if (!hit) return bb5eNote(spec, status, next, now);
  var label = (spec && spec.label) || "Market";
  var when = next && typeof bb5eLondon === "function" ? bb5eLondon(next, now) : "";
  var note = label + " market closed (" + hit.name + ")";
  if (when) note += " · opens " + when + " UK";
  var closeAt = bb6CloseAt(spec, next);
  if (closeAt && typeof bb5eLondon === "function") note += " · early close " + bb5eLondon(closeAt, now) + " UK";
  return note;
}
// BB6_JS_END
'''

declared = re.findall(r'(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', BLOCK)
bad = [name for name in declared if not name.startswith("bb6")]
if bad:
    die("bb6 block declares a non-bb6 function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb6 block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb6 block has a forbidden declaration")

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
    print("bb6 app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb6 index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb6bak"
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
print("APPLY bb6 holidays")
