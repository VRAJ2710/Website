#!/usr/bin/env python3
"""patch_bb8r.py — Jack's deploy patch, stacked on bb8o (server.js md5 77aa597819385227f1407cd5d6c69f53).

P0: quote footer label is the Ask subject (Gold spot only for XAU) on the stream meta event and the JSON body;
GC=F YTD base is the last prior-year exchange-local daily close (Wed 31 Dec 2025 close 4341.10, not a 3341 misread);
after drops, [n] is rebound to the source whose symbol/title actually carries the figure; one in-memory regime
figure with an as-of for both Ask paths and the reference feed; BP.L market cap converts GBp to GBP once and
does not divide Yahoo's already-GBP marketCap again.
P1: gold-this-week opens with the gold-api spot line; a keyless FOMC/BEA/ONS week calendar (BLS noted if it
fails); prose prices snap to the cited figure; filler such as "it's essential to monitor" is dropped; each
label's as-of is that source's own time; proxy lines use the exact words "As a proxy, ".
P2: DXY display label is "US Dollar Index (ICE)" while the source entry keeps "Yahoo DX-Y.NYB"; 0700.HK
changeDay is the session weekday ("Fri") on every session tag the server sends.
Server.js only. Appended after // BB8O_JS_END. No tables, intervals, timers, secrets, Stripe or Replit.
Usage: python3 patch_bb8r.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "77aa597819385227f1407cd5d6c69f53",
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
    sha = hashlib.sha256(raw).hexdigest()
    print("bb8r %s %s md5=%s sha256=%s lines=%d" % (phase, name, digest, sha, len(raw.splitlines())))
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
        print("bb8r before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8r %s untouched" % label)

if "// BB8R_JS" in v:
    print("REFUSE: bb8r already applied")
    sys.exit(0)

REPLACE = []

REQUIRED = [
    ("bb8o end marker (bb8r is appended after it)", "// BB8O_JS_END"),
    ("bb8q2 end marker", "// BB8Q2_JS_END"),
    ("bb8q2 DXY label", 'var BB8Q2_DXY = "US Dollar Index (ICE, Yahoo DX-Y.NYB)";'),
    ("bb8oQuoteLabel", "function bb8oQuoteLabel(q) {"),
    ("bb8oPost", "function bb8oPost(doc, st) {"),
    ("bb8oProfileFrom", "function bb8oProfileFrom(sym, r) {"),
    ("bb8pQuoteMeta", "function bb8pQuoteMeta(st) {"),
    ("bb3Mood", "function bb3Mood(m) {"),
    ("bb8qBuild", "async function bb8qBuild(st, body) {"),
    ("bb8qFinish", "function bb8qFinish(out, st) {"),
    ("bb8qNoData", "function bb8qNoData(doc, st, ctx) {"),
    ("bb8qParse", "function bb8qParse(out) {"),
    ("bb8qRender", "function bb8qRender(doc) {"),
]
for a, _b in REPLACE:
    REQUIRED.append(("replace: " + a.strip()[:60], a))
miss = []
for name, anchor in REQUIRED:
    n = v.count(anchor)
    if n != 1:
        miss.append("anchor %s matched %d times (want 1)" % (name, n))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)
print("bb8r anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8r ── Ask quote label, GC=F YTD bar, citation rebind, one cached regime, GBp market cap,
// gold-week spot opener, free week calendar, cited-figure snap, per-source as-of, "As a proxy, ".
// See docs/bb8r.md. Stacked on bb8o. In-memory only. No tables, timers or new feeds that need a key.
// BB8R_JS
var BB8R_REGIME_MS = 10 * 60 * 1000;
var BB8R_CAL_MS = 6 * 3600 * 1000;
var BB8R_NAMES = { MU: "Micron Technology", NVDA: "NVIDIA", AAPL: "Apple", XAU: "Gold spot", GOLD: "Gold spot" };
var BB8R_MON = { January: 1, February: 2, March: 3, April: 4, May: 5, June: 6, July: 7, August: 8, September: 9, October: 10, November: 11, December: 12 };
var BB8R_FILLER = /it'?s essential to monitor|it is essential to monitor|essential to monitor|monitor related economic indicators|while we don'?t have specific figures/i;
var BB8R_DXY_LONG = "US Dollar Index (ICE, Yahoo DX-Y.NYB)";
var BB8R_DXY_SHORT = "US Dollar Index (ICE)";
var bb8rReg = { at: 0, row: null };
var bb8rCalMem = { at: 0, data: null };
var bb8rYahooMem = {};

function bb8rPx(n) {
  var v = Number(n);
  if (!(v > 0) || !isFinite(v)) return "";
  var p = v.toFixed(2).split(".");
  p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return p.join(".");
}
function bb8rSigned(n, d) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  return (v > 0 ? "+" : v < 0 ? "-" : "") + Math.abs(v).toFixed(d == null ? 2 : d);
}
function bb8rCoName(sym, yahooName) {
  var s = String(sym || "").toUpperCase();
  if (/^(?:XAU|GOLD)$/.test(s)) return "Gold spot";
  if (s === "GC=F") return "Gold futures (GC=F)";
  if (yahooName && !/gold spot/i.test(String(yahooName))) {
    var n = String(yahooName).replace(/,?\s+(?:Inc\.?|Incorporated|Corporation|Corp\.?|plc|p\.l\.c\.|Limited|Ltd\.?|Company|Co\.?)$/i, "").trim();
    if (n && n.length > 1) return n;
  }
  return BB8R_NAMES[s] || s || "Quote";
}
function bb8rSubjectSym(st) {
  var b = "";
  try { b = String((st && (st.bb8eBase || (st.bb8eMoveR && st.bb8eMoveR.base))) || ""); } catch (e) { b = ""; }
  b = b.trim().toUpperCase();
  if (b) return b;
  try { if (st && st.bb8qCtx && st.bb8qCtx.gold) return "XAU"; } catch (e) {}
  return "";
}
function bb8rGoldSym(sym) { return /^(?:XAU|GOLD|GC=F|XAUUSD=X)$/i.test(String(sym || "")); }
function bb8rQuoteLine(q) {
  if (!q || !(Number(q.price) > 0) || !q.label) return "";
  var line = q.label + " $" + bb8rPx(q.price);
  if (q.change != null && isFinite(Number(q.change)) && q.changePct != null && isFinite(Number(q.changePct))) {
    line += " " + bb8rSigned(q.change, 2) + " (" + bb8rSigned(q.changePct, 2) + "%)";
  }
  if (q.asOfUk) line += " \u00b7 " + q.asOfUk;
  return line;
}
function bb8rPackQuote(st, sym) {
  var pack = st && st.bb8eMoveR;
  var q = pack && pack.q;
  if (!q || !(Number(q.p) > 0)) return null;
  var p = Number(q.p), prev = Number(q.prev);
  var pct = isFinite(Number(q.c)) ? Number(q.c) : (prev > 0 ? (p / prev - 1) * 100 : null);
  var ch = null;
  if (isFinite(Number(q.change)) && prev > 0 && Math.abs(Number(q.change) - (p - prev)) < Math.abs(p - prev) + 0.05) ch = Number(q.change);
  else if (prev > 0) ch = p - prev;
  var ms = pack.ms || (typeof bb8qMs === "function" ? bb8qMs(q) : 0) || Date.now();
  var label = bb8rCoName(sym || pack.base, q.name);
  var o = {
    symbol: String(sym || pack.base || ""),
    feedSymbol: pack.ysym || sym || null,
    label: label,
    name: label,
    price: p,
    change: ch != null ? Number(ch.toFixed(2)) : null,
    changePct: pct != null ? Number(pct.toFixed(4)) : null,
    prevClose: prev > 0 ? prev : null,
    currency: q.currency || "USD",
    asOf: typeof bb8qIso === "function" ? bb8qIso(ms) : new Date(ms).toISOString(),
    asOfUk: typeof bb8qUk === "function" ? bb8qUk(ms) : (typeof bb8dUk === "function" ? bb8dUk(ms) : null),
    source: "Yahoo Finance",
    session: q.session || q.status || null
  };
  o.quoteLine = bb8rQuoteLine(o);
  return o;
}
function bb8rSpotQuote(st) {
  var c = st && st.bb8qCtx, s = c && c.spot && c.spot.q;
  if (!s || !(Number(s.p) > 0)) return null;
  var ms = c.spot.ms || Date.now();
  var o = {
    symbol: "XAU", feedSymbol: "XAU", label: "Gold spot", name: "Gold spot",
    price: Number(s.p),
    change: s.changeAvailable && s.change != null ? Number(Number(s.change).toFixed(2)) : null,
    changePct: s.changeAvailable && s.c != null ? Number(Number(s.c).toFixed(4)) : null,
    prevClose: s.changeAvailable && Number(s.prev) > 0 ? Number(s.prev) : null,
    changeAvailable: !!s.changeAvailable,
    currency: "USD",
    asOf: typeof bb8qIso === "function" ? bb8qIso(ms) : new Date(ms).toISOString(),
    asOfUk: typeof bb8qUk === "function" ? bb8qUk(ms) : null,
    source: "gold-api.com",
    feed: "gold-api.com spot (api.gold-api.com/price/XAU)"
  };
  o.quoteLine = bb8rQuoteLine(o);
  return o;
}
// One quote object for the stream meta event and the JSON body. Label is the Ask subject.
function bb8rQuoteMeta(st, prior) {
  var sym = bb8rSubjectSym(st);
  var gold = bb8rGoldSym(sym);
  var o = gold ? (bb8rSpotQuote(st) || prior) : (bb8rPackQuote(st, sym) || prior);
  if (!o || typeof o !== "object") return prior || null;
  if (gold) {
    o = Object.assign({}, o);
    o.symbol = "XAU"; o.label = "Gold spot"; o.name = "Gold spot";
    o.quoteLine = bb8rQuoteLine(o);
    return o;
  }
  o = Object.assign({}, o);
  if (/gold spot/i.test(String(o.label || "")) || /gold spot/i.test(String(o.name || "")) || !o.label) {
    o.label = bb8rCoName(sym, o.name);
    o.name = o.label;
  }
  bb8rFixChange(o);
  o.quoteLine = bb8rQuoteLine(o);
  return o;
}
// bb8p stores the percent in `change`. The footer wants the cash move in `change` and the percent in `changePct`.
function bb8rFixChange(o) {
  var p = Number(o && o.price), prev = Number(o && (o.prevClose != null ? o.prevClose : o.prev));
  var ch = Number(o && o.change);
  if (!(p > 0) || !(prev > 0) || !isFinite(ch)) return o;
  var dollar = p - prev, pct = (p / prev - 1) * 100;
  if (Math.abs(ch - dollar) > 0.2 && Math.abs(ch - pct) < 0.08) {
    o.changePct = Number(pct.toFixed(4));
    o.change = Number(dollar.toFixed(2));
  } else if (o.changePct == null && Math.abs(ch - dollar) <= 0.2) {
    o.changePct = Number(pct.toFixed(4));
  }
  return o;
}

// GBp price is pence. £ = price/100. Yahoo's LSE marketCap is already GBP: keep it when it
// matches shares*(price/100), divide it only when it is ~100x that, and never add the two.
function bb8rCap(raw) {
  raw = raw || {};
  var cur = String(raw.currency || raw.priceCurrency || "");
  var div = (cur === "GBp" || cur === "GBX" || cur === "ZAc" || cur === "ILA") ? 100 : 1;
  var px = Number(raw.price != null ? raw.price : raw.regularMarketPrice);
  var sh = Number(raw.sharesOutstanding || raw.impliedSharesOutstanding);
  var mc = Number(raw.marketCap);
  var pxMajor = px > 0 ? px / div : null;
  var implied = sh > 0 && pxMajor > 0 ? sh * pxMajor : null;
  var impliedRaw = sh > 0 && px > 0 ? sh * px : null;
  var status = "missing", out = null, ratio = null;
  if (mc > 0 && implied > 0) {
    ratio = mc / implied;
    if (ratio >= 0.8 && ratio <= 1.25) { out = mc; status = "ok"; }
    else if (ratio >= 1.6 && ratio <= 2.4) { out = implied; status = "deduped"; }
    else if (ratio >= 50 && ratio <= 200) { out = mc / 100; status = "corrected-minor-units"; }
    else if (impliedRaw > 0 && mc / impliedRaw >= 0.5 && mc / impliedRaw <= 2) { out = implied; status = "computed-from-pence"; }
    else { out = implied; status = "computed"; }
  } else if (implied > 0) { out = implied; status = "computed"; }
  else if (mc > 0) { out = mc; status = "unverified"; }
  var major = div === 100 && (cur === "GBp" || cur === "GBX") ? "GBP" : (cur === "ZAc" ? "ZAR" : (cur === "ILA" ? "ILS" : (cur || null)));
  return {
    price: isFinite(px) ? px : null,
    priceCurrency: cur || null,
    priceMajor: pxMajor != null ? Math.round(pxMajor * 10000) / 10000 : null,
    sharesOutstanding: sh > 0 ? sh : null,
    yahooMarketCap: mc > 0 ? mc : null,
    marketCap: out != null ? Math.round(out) : null,
    marketCapCurrency: major,
    impliedMarketCap: implied != null ? Math.round(implied) : null,
    ratio: ratio != null ? Math.round(ratio * 1000) / 1000 : null,
    status: status
  };
}
function bb8rCapText(mc, ccy) {
  var n = Number(mc);
  if (!(n > 0)) return "";
  var sym = ccy === "GBP" ? "\u00a3" : ccy === "USD" ? "$" : ccy === "EUR" ? "\u20ac" : (ccy ? ccy + " " : "");
  var u = n >= 1e12 ? [1e12, "tn"] : n >= 1e9 ? [1e9, "bn"] : n >= 1e6 ? [1e6, "m"] : [1, ""];
  return sym + (n / u[0]).toFixed(1) + u[1];
}
function bb8rNumRaw(v) {
  if (v && typeof v === "object" && "raw" in v) v = v.raw;
  var n = Number(v);
  return v == null || v === "" || !isFinite(n) ? null : n;
}
function bb8rProfile(sym, yahoo, prior) {
  var pr = (yahoo && yahoo.price) || {}, sd = (yahoo && yahoo.summaryDetail) || {}, ks = (yahoo && yahoo.defaultKeyStatistics) || {};
  var cap = bb8rCap({
    currency: pr.currency || sd.currency || (prior && prior.priceCurrency) || "",
    price: bb8rNumRaw(pr.regularMarketPrice) || (prior && prior.price) || null,
    sharesOutstanding: bb8rNumRaw(ks.sharesOutstanding) || bb8rNumRaw(ks.impliedSharesOutstanding) || (prior && prior.marketCapCheck && prior.marketCapCheck.sharesOutstanding) || null,
    marketCap: bb8rNumRaw(sd.marketCap) || bb8rNumRaw(pr.marketCap) || null
  });
  var o = prior && typeof prior === "object" ? Object.assign({}, prior) : { symbol: sym };
  o.priceCurrency = cap.priceCurrency;
  o.currency = cap.marketCapCurrency || o.currency || null;
  o.price = cap.price != null ? cap.price : o.price;
  o.priceMajor = cap.priceMajor;
  o.marketCap = cap.marketCap;
  o.marketCapCurrency = cap.marketCapCurrency;
  o.marketCapText = bb8rCapText(cap.marketCap, cap.marketCapCurrency);
  o.marketCapCheck = {
    status: cap.status, sharesOutstanding: cap.sharesOutstanding, yahooMarketCap: cap.yahooMarketCap,
    impliedMarketCap: cap.impliedMarketCap, ratio: cap.ratio, price: cap.price, priceCurrency: cap.priceCurrency, priceMajor: cap.priceMajor
  };
  if (cap.priceCurrency === "GBp" || cap.priceCurrency === "GBX") o.unitNote = "Quoted in pence (" + cap.priceCurrency + "); 100p = \u00a31. Market cap is in pounds (Yahoo marketCap is already GBP; it is not divided again).";
  if (o.asset && typeof o.asset === "object") o.asset = Object.assign({}, o.asset, { mc: o.marketCapText || o.asset.mc });
  return o;
}

// Last prior-year daily bar in the exchange's own dates. Unadjusted close, not adjclose.
function bb8rBarDate(ts, tz) {
  var n = Number(ts);
  if (!(n > 0)) return "";
  var ms = n < 1e12 ? n * 1000 : n;
  try {
    return new Intl.DateTimeFormat("en-CA", { timeZone: tz || "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms));
  } catch (e) { return ""; }
}
function bb8rYtdPick(bars, today) {
  var y = Number(String(today || "").slice(0, 4));
  if (!y || !Array.isArray(bars)) return null;
  var boundary = y + "-01-01", prior = [];
  bars.forEach(function (b) {
    if (!b || !(Number(b.close) > 0) || !b.date) return;
    if (String(b.date) < boundary) prior.push(b);
  });
  if (!prior.length) return null;
  var bar = prior[prior.length - 1];
  var close = Number(bar.close);
  return { bar: bar, close: close, display: Math.round(close * 100) / 100, date: bar.date };
}
function bb8rYtdDir(from, to) {
  var a = Number(from), b = Number(to);
  if (!(a > 0) || !(b > 0)) return null;
  var pct = (b / a - 1) * 100;
  var word = Math.abs(pct) < 0.005 ? "unchanged" : (pct < 0 ? "down" : "up");
  return { from: a, to: b, pct: pct, word: word, instrument: "GC=F" };
}
function bb8rYtdLabel(text) {
  return String(text || "").split("\n").map(function (l) {
    if (!/year to date|\bYTD\b/i.test(l)) return l;
    if (!/GC=F|gold futures/i.test(l)) return l;
    if (!/gold spot/i.test(l)) return l;
    return l.replace(/gold spot/ig, "gold futures (GC=F)").replace(/(gold futures \(GC=F\))(?:\s*\(GC=F\))+/gi, "$1");
  }).join("\n");
}

function bb8rRegimeRemember(mood, inputs) {
  var now = Date.now();
  if (bb8rReg.row && now - bb8rReg.at < BB8R_REGIME_MS) return bb8rReg.row;
  if (!mood || !isFinite(Number(mood.score))) return bb8rReg.row;
  var uk = typeof bb8qUk === "function" ? bb8qUk(now) : (typeof bb8dUk === "function" ? bb8dUk(now) : "");
  bb8rReg = { at: now, row: { mood: { regime: mood.regime, score: Number(mood.score) }, inputs: inputs || null, asOf: now, asOfIso: new Date(now).toISOString(), asOfUk: uk } };
  return bb8rReg.row;
}
function bb8rRegimeRow() {
  if (!bb8rReg.row) return null;
  if (Date.now() - bb8rReg.at >= BB8R_REGIME_MS) return null;
  return bb8rReg.row;
}
function bb8rStampRegime(ctx) {
  var row = bb8rRegimeRow();
  if (!ctx || !row) return;
  var mood = row.mood;
  var t = "Dispatch regime model (ours): market mood " + mood.regime + ", score " + mood.score + "/100, as of " + row.asOfUk + ".";
  ctx.regime = { regime: mood.regime, score: mood.score, asOf: row.asOfIso, asOfUk: row.asOfUk };
  (ctx.facts || []).forEach(function (f) {
    if (!f || f.id !== "regime") return;
    f.text = t;
    if (f.src) {
      f.src.detail = "Our regime model (The Dispatch): " + mood.regime + ", score " + mood.score + "/100, as of " + row.asOfUk;
      f.src.asOf = row.asOfIso;
      try { if (typeof bb8qSrcText !== "undefined" && bb8qSrcText && bb8qSrcText.set) bb8qSrcText.set(f.src, f.src.detail); } catch (e) {}
    }
  });
}
function bb8rRegimePublic(row) {
  if (!row) return null;
  return { regime: row.mood.regime, score: row.mood.score, asOf: row.asOfIso, asOfUk: row.asOfUk, memory: "process", ttlSec: Math.round(BB8R_REGIME_MS / 1000) };
}

function bb8rInHay(v, hay) {
  return (String(hay || "").replace(/,/g, "").match(/\d+(?:\.\d+)?/g) || []).some(function (x) { return Math.abs(Number(x) - v) <= 0.02; });
}
function bb8rClaim(sentence) {
  var b = String(sentence || "").replace(/\u27e6\d+\u27e7/g, " ").replace(/\[\d{1,2}\]/g, " ");
  if (/\b(?:DXY|US Dollar Index|dollar index)\b/i.test(b)) return "DX-Y.NYB";
  if (/\b(?:10-year|10y|Treasury yield|\^TNX)\b/i.test(b)) return "^TNX";
  if (/\bVIX\b|volatility index/i.test(b)) return "^VIX";
  if (/S&P\s*500|\^GSPC/i.test(b)) return "^GSPC";
  if (/\bSPY\b/.test(b)) return "SPY";
  if (/5-session|futures range|session high|session low|high is \$|low is \$/i.test(b)) return "futures-range";
  if (/regime|Risk-On|Risk-Off|Transition|\/100/i.test(b)) return "regime";
  return null;
}
function bb8rSrcBlob(src) {
  var extra = "";
  try { if (typeof bb8qSrcText !== "undefined" && bb8qSrcText && bb8qSrcText.get) extra = bb8qSrcText.get(src) || ""; } catch (e) {}
  return ((src && (src.bb8qKey || "")) + " " + (src && src.name || "") + " " + (src && src.title || "") + " " + (src && src.label || "") + " " + (src && src.detail || "") + " " + extra);
}
function bb8rSrcMatch(src, claim) {
  if (!src || !claim) return false;
  var k = String(src.bb8qKey || "");
  var blob = bb8rSrcBlob(src);
  if (claim === "DX-Y.NYB") return k === "DX-Y.NYB" || (/DX-Y\.NYB|US Dollar Index/.test(blob) && !/\^GSPC|S&P 500/.test(k));
  if (claim === "^TNX") return k === "^TNX" || (/\^TNX|10-year|Treasury yield/.test(blob) && k !== "^VIX");
  if (claim === "^VIX") return k === "^VIX" || (/\^VIX|\bVIX\b/.test(blob) && k !== "^TNX");
  if (claim === "^GSPC") return k === "^GSPC" || /\^GSPC|S&P 500/.test(blob);
  if (claim === "SPY") return k === "SPY" || /\bSPY\b/.test(blob);
  if (claim === "regime") return k === "regime" || /regime model|Dispatch regime/.test(blob);
  if (claim === "futures-range") {
    if (/news|Fortitude/i.test(String(src.name || "") + " " + String(src.detail || "").slice(0, 80))) return false;
    return /futures|bb8o:levels|GC=F|chart/.test(k + " " + blob);
  }
  return false;
}
function bb8rFigs(sentence) {
  return (String(sentence || "").replace(/\u27e6\d+\u27e7/g, " ").replace(/\[\d{1,2}\]/g, " ").replace(/\b(?:19|20)\d{2}\b/g, " ").replace(/\b\d{1,2}:\d{2}\b/g, " ").replace(/,/g, "").match(/\d+(?:\.\d+)?/g) || []).map(Number).filter(function (n) { return n >= 1; });
}
function bb8rBest(doc, claim, sentence) {
  var figs = bb8rFigs(sentence).filter(function (n) { return n >= 10 || /%/.test(sentence); });
  var hits = [];
  (doc.srcs || []).forEach(function (src, i) {
    if (!bb8rSrcMatch(src, claim)) return;
    var hay = bb8rSrcBlob(src);
    if (figs.length && !figs.every(function (n) { return bb8rInHay(n, hay) || n < 10; })) return;
    hits.push(i);
  });
  if (!hits.length) {
    (doc.srcs || []).forEach(function (src, i) { if (bb8rSrcMatch(src, claim)) hits.push(i); });
  }
  return hits.length ? hits[0] : null;
}
function bb8rSplitSent(line) {
  var s = String(line), out = [], cur = "";
  for (var i = 0; i < s.length; i++) {
    var ch = s.charAt(i);
    cur += ch;
    if (!/[.!?]/.test(ch)) continue;
    var nx = s.charAt(i + 1);
    if (nx && !/\s/.test(nx)) continue;
    while (i + 1 < s.length && /\s/.test(s.charAt(i + 1))) { cur += s.charAt(++i); }
    var rest = s.slice(i + 1), tm = /^((?:\u27e6\d+\u27e7\s*)+)/.exec(rest);
    if (tm) { cur += tm[1]; i += tm[1].length; }
    out.push(cur); cur = "";
  }
  if (cur) out.push(cur);
  return out.length ? out : [s];
}
function bb8rCites(doc) {
  if (!doc || typeof doc.body !== "string") return doc;
  doc.body = doc.body.split("\n").map(function (line) {
    if (!line.trim() || /^\s*Sources:/.test(line)) return line;
    return bb8rSplitSent(line).map(function (sentence) {
      var claim = bb8rClaim(sentence);
      if (!claim) return sentence;
      var best = bb8rBest(doc, claim, sentence);
      if (best == null) return sentence;
      var s = sentence.replace(/\s*\u27e6\d+\u27e7/g, "");
      return s.replace(/\s+$/, "") + " \u27e6" + best + "\u27e7";
    }).join("");
  }).join("\n");
  return doc;
}
function bb8rSnapDoc(doc) {
  if (!doc) return doc;
  doc.body = String(doc.body).split("\n").map(function (line) {
    var keys = [];
    line.replace(/\u27e6(\d+)\u27e7/g, function (m, k) { keys.push(Number(k)); return m; });
    if (!keys.length) return line;
    var hay = keys.map(function (k) { return bb8rSrcBlob(doc.srcs[k]); }).join(" ");
    return line.replace(/\$(\d{1,3}(?:,\d{3})*\.\d{2})/g, function (m, num) {
      var v = Number(num.replace(/,/g, ""));
      var best = null, bd = 1e9;
      (hay.replace(/,/g, "").match(/\d{3,5}\.\d{2,}/g) || []).forEach(function (x) {
        var n = Number(x), d = Math.abs(n - v);
        if (d < bd) { bd = d; best = n; }
      });
      if (best == null || bd < 0.001 || bd > 1) return m;
      return "$" + bb8rPx(best);
    });
  }).join("\n");
  return doc;
}
function bb8rFiller(doc) {
  if (!doc) return doc;
  doc.body = String(doc.body).split("\n").map(function (line) {
    if (!BB8R_FILLER.test(line)) return line;
    return bb8rSplitSent(line).filter(function (s) { return s.trim() && !BB8R_FILLER.test(s); }).join(" ");
  }).join("\n");
  return doc;
}
function bb8rAsOfPhrase(src) {
  if (!src) return "";
  var uk = String(src.asOfUk || "");
  if (!uk) return "";
  if (src.bb8rClose || src.closed) {
    var day = uk.split(",")[0];
    return day ? day + " close" : uk;
  }
  return uk;
}
function bb8rProxyAsOf(doc) {
  if (!doc) return doc;
  doc.body = String(doc.body).split("\n").map(function (line) {
    if (!/\u27e6\d+\u27e7/.test(line)) return line;
    if (!/proxy|What we do have|GBP\/USD|FTSE|Hang Seng|USDCNH|as market proxies/i.test(line)) return line;
    var bits = line.split(/;\s*/);
    var out = bits.map(function (bit) {
      var km = /\u27e6(\d+)\u27e7/.exec(bit);
      if (!km) return bit;
      var src = doc.srcs[Number(km[1])];
      if (!src) return bit;
      var phrase = bb8rAsOfPhrase(src);
      var body = bit.replace(/^What we do have[\s\S]*?:\s*/i, "").replace(/,\s*as market proxies\s*\([^)]*\)\s*:\s*/i, "");
      body = body.replace(/,?\s*as of [^.\u27e6]+/i, "");
      if (phrase && body.indexOf(phrase) < 0) {
        body = body.replace(/\s*(\u27e6\d+\u27e7)/, ", as of " + phrase + " $1");
      }
      body = body.replace(/^\s+/, "");
      if (/^as a proxy,/i.test(body)) return "As a proxy" + body.slice(body.indexOf(","));
      if (src.bb8qProxy || /proxy|What we do have|as market proxies/i.test(line)) return "As a proxy, " + body;
      return body;
    });
    return out.join("; ");
  }).join("\n");
  return doc;
}
function bb8rDxy(doc) {
  if (!doc) return doc;
  doc.body = String(doc.body).split(BB8R_DXY_LONG).join(BB8R_DXY_SHORT);
  (doc.srcs || []).forEach(function (s) {
    if (!s) return;
    var blob = bb8rSrcBlob(s);
    if (!/DX-Y\.NYB/.test(blob)) return;
    s.bb8rDisplay = BB8R_DXY_SHORT;
    if (s.detail && s.detail.indexOf("Yahoo DX-Y.NYB") < 0) s.detail = s.detail + " Yahoo DX-Y.NYB";
    if (!s.detail) s.detail = "Yahoo DX-Y.NYB";
  });
  return doc;
}
function bb8rGoldWeek(doc, st) {
  var ctx = st && st.bb8qCtx;
  var q = String((ctx && ctx.q) || "");
  if (!ctx || !ctx.gold || !/\bweek\b/i.test(q) || !ctx.spot || !ctx.spot.q || !(Number(ctx.spot.q.p) > 0)) return doc;
  var uk = "";
  var m = /as of ([^)]+)\)/.exec(String(ctx.spot.text || ""));
  if (m) uk = m[1].replace(/^\s+|\s+$/g, "").replace(/;.*$/, "");
  if (!uk && typeof bb8qUk === "function") uk = bb8qUk(ctx.spot.ms || Date.now());
  var line = "Gold spot $" + bb8rPx(ctx.spot.q.p) + " (gold-api.com, as of " + uk + ").";
  if (ctx.spot.src && typeof bb8qTok === "function") line += " " + bb8qTok(doc, ctx.spot.src);
  var lines = String(doc.body).split("\n").map(function (l) { return l.replace(/^\s*Live:\s*/, ""); }).filter(function (l) {
    return !/^\s*Gold spot is at \$/.test(l) && !/^\s*Gold spot \$/.test(l);
  });
  doc.body = line + "\n\n" + lines.join("\n").replace(/^\n+/, "");
  return doc;
}
function bb8rQuoteBody(doc, st) {
  var sym = bb8rSubjectSym(st);
  if (!sym || bb8rGoldSym(sym)) return doc;
  var q = bb8rQuoteMeta(st, null);
  if (!q || !q.quoteLine) return doc;
  doc.body = String(doc.body).replace(/Gold spot \$[\d,]+(?:\.\d+)?(?:\s+[+\-][\d,]+(?:\.\d+)?(?:\s*\([+\-][\d.]+%\))?)?(?:\s*\u00b7[^\n]*)?/gi, q.quoteLine);
  return doc;
}
function bb8rUkYmd(ms) {
  try {
    return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms || Date.now()));
  } catch (e) { return new Date(ms || Date.now()).toISOString().slice(0, 10); }
}
function bb8rWeekBounds(ymd) {
  var d = new Date(String(ymd) + "T12:00:00Z");
  if (!isFinite(d.getTime())) return null;
  var dow = d.getUTCDay(), back = dow === 0 ? 6 : dow - 1;
  var mon = new Date(d.getTime() - back * 86400000);
  var sun = new Date(mon.getTime() + 6 * 86400000);
  var iso = function (x) { return x.toISOString().slice(0, 10); };
  return { start: iso(mon), end: iso(sun) };
}
function bb8rIso(y, mon, day) {
  if (!y || !mon || !day) return "";
  return String(y) + "-" + ("0" + mon).slice(-2) + "-" + ("0" + day).slice(-2);
}
function bb8rCalParseFomc(html, now) {
  var h = String(html || "");
  var y = Number(bb8rUkYmd(now).slice(0, 4));
  var start = h.indexOf(y + " FOMC Meetings");
  if (start < 0) return [];
  var end = h.indexOf("FOMC Meetings", start + 12);
  var slice = h.slice(start, end > start ? end : start + 30000);
  var re = /<strong>([A-Za-z]+)<\/strong>[\s\S]{0,500}?fomc-meeting__date[^>]*>([^<]+)</g;
  var out = [], m;
  while ((m = re.exec(slice))) {
    var mi = BB8R_MON[m[1]];
    if (!mi) continue;
    var dates = String(m[2] || "").replace(/\*/g, "").trim();
    var parts = dates.split(/[^\d]+/).filter(Boolean);
    var day = Number(parts[parts.length - 1]);
    var iso = bb8rIso(y, mi, day);
    if (!iso) continue;
    out.push({ date: iso, kind: "FOMC", source: "FOMC", link: "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", text: "FOMC meeting " + m[1] + " " + dates + " " + y + " (federalreserve.gov)" });
  }
  return out;
}
function bb8rCalParseBea(html, now) {
  var h = String(html || "");
  var y = Number(bb8rUkYmd(now).slice(0, 4));
  var re = /<div class="release-date">([A-Za-z]+)\s+(\d{1,2})<\/div>[\s\S]{0,800}?release-title[^>]*>([^<]+)</g;
  var out = [], m;
  while ((m = re.exec(h))) {
    var mi = BB8R_MON[m[1]];
    if (!mi) continue;
    var title = String(m[3] || "").replace(/\s+/g, " ").trim();
    if (!/\b(?:GDP|Personal Income|international trade)\b/i.test(title)) continue;
    out.push({ date: bb8rIso(y, mi, Number(m[2])), kind: "BEA", source: "BEA", link: "https://www.bea.gov/news/schedule", text: title + " on " + m[1] + " " + m[2] + " (bea.gov)" });
  }
  return out.filter(function (e) { return e.date; });
}
function bb8rCalParseOns(html, now) {
  var h = String(html || "");
  var re = /data-gtm-release-title\s*=\s*"([^"]+)"[\s\S]{0,800}?data-gtm-release-date\s*=\s*"(\d{8})"/g;
  var out = [], m;
  while ((m = re.exec(h))) {
    var title = m[1].replace(/\s+/g, " ").trim();
    if (!/\b(?:CPI|CPIH|GDP|inflation|labour market|labor market|retail sales|producer price|earnings)\b/i.test(title)) continue;
    var d = m[2];
    out.push({ date: d.slice(0, 4) + "-" + d.slice(4, 6) + "-" + d.slice(6, 8), kind: "ONS", source: "ONS", link: "https://www.ons.gov.uk/releasecalendar", text: title + " (ons.gov.uk)" });
  }
  return out;
}
function bb8rMacroTitle(t) { return /\b(?:CPI|CPIH|GDP|inflation|labour market|labor market|retail sales|PPI|employment|nonfarm|personal income|FOMC|earnings)\b/i.test(String(t || "")); }
async function bb8rGetText(url) {
  if (typeof fetch !== "function") return "";
  var r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (compatible; DispatchResearch/1.0)" } });
  if (!r || !r.ok) return "";
  return await r.text();
}
async function bb8rCalLoad(now) {
  var t = now || Date.now();
  if (bb8rCalMem.data && t - bb8rCalMem.at < BB8R_CAL_MS) return bb8rCalMem.data;
  var data = { events: [], checked: [], failed: [], at: t };
  var jobs = [
    ["FOMC", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", bb8rCalParseFomc],
    ["BEA", "https://www.bea.gov/news/schedule", bb8rCalParseBea],
    ["ONS", "https://www.ons.gov.uk/releasecalendar", bb8rCalParseOns],
    ["BLS", "https://www.bls.gov/schedule/news_release/bls.jr.htm", function () { return []; }]
  ];
  for (var i = 0; i < jobs.length; i++) {
    var html = "";
    try { html = await bb8rGetText(jobs[i][1]); } catch (e) { html = ""; }
    if (!html || html.length < 80) { data.failed.push(jobs[i][0]); continue; }
    var ev = [];
    try { ev = jobs[i][2](html, t) || []; } catch (e2) { ev = []; }
    if (jobs[i][0] === "BLS") { data.failed.push("BLS"); continue; }
    data.checked.push(jobs[i][0]);
    ev.forEach(function (e) { data.events.push(e); });
  }
  bb8rCalMem = { at: t, data: data };
  return data;
}
function bb8rSrc(name, link, ms, detail, key) {
  if (typeof bb8qSrc === "function") return bb8qSrc(name, link, ms, detail, key);
  return { name: name, link: link, asOf: new Date(ms || Date.now()).toISOString(), detail: detail, bb8qKey: key, bb8q: true };
}
async function bb8rCalAttach(ctx) {
  if (!ctx || !/\bweek\b/i.test(String(ctx.q || ""))) return;
  var data = null;
  try { data = await bb8rCalLoad(Date.now()); } catch (e) { data = null; }
  if (!data) return;
  var w = bb8rWeekBounds(bb8rUkYmd(Date.now()));
  var ev = (data.events || []).filter(function (e) { return w && e.date >= w.start && e.date <= w.end && bb8rMacroTitle(e.text); });
  ev.forEach(function (e) {
    if (e.src) return;
    e.src = bb8rSrc(e.source || "Calendar", e.link || "", Date.now(), e.text, "bb8r:cal");
    ctx.facts = ctx.facts || []; ctx.sources = ctx.sources || [];
    ctx.facts.push({ id: "bb8r:cal", text: e.text, src: e.src });
    ctx.sources.push(e.src);
  });
  ctx.bb8rCal = { events: ev, checked: data.checked || [], failed: data.failed || [], week: w };
}
function bb8rCalLine(doc, st) {
  var cal = st && st.bb8qCtx && st.bb8qCtx.bb8rCal;
  if (!cal || !doc) return doc;
  var repl;
  if (cal.events && cal.events.length && typeof bb8qTok === "function") {
    repl = cal.events.map(function (e) { return e.text + (e.src ? " " + bb8qTok(doc, e.src) : ""); }).join("; ");
  } else if ((cal.checked || []).length) {
    repl = "No FOMC, BEA or ONS release falls this week (calendars checked" + ((cal.failed || []).length ? "; " + cal.failed.join("/") + " did not load" : "") + ")";
  } else return doc;
  doc.body = String(doc.body).replace(/No scheduled Fed, economic-data or earnings dates for this week are in our feed/, repl);
  return doc;
}
function bb8rDayName(ms, tz) {
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: tz || "Europe/London", weekday: "short", day: "numeric", month: "short" }).formatToParts(new Date(ms)).forEach(function (p) { parts[p.type] = p.value; });
    return { wd: parts.weekday, full: parts.weekday + " " + parts.day + " " + parts.month };
  } catch (e) { return null; }
}
function bb8rTz(sym) {
  var s = String(sym || "").toUpperCase();
  if (/\.HK$/.test(s)) return "Asia/Hong_Kong";
  if (/\.T$/.test(s)) return "Asia/Tokyo";
  if (/\.TW$|\.TWO$/.test(s)) return "Asia/Taipei";
  if (/\.L$/.test(s)) return "Europe/London";
  if (/\.AX$/.test(s)) return "Australia/Sydney";
  return "America/New_York";
}
function bb8rSessionTag(row, sym) {
  if (!row || typeof row !== "object") return row;
  var ts = Number(row.ts);
  if (!(ts > 0)) return row;
  var ms = ts < 1e12 ? ts * 1000 : ts;
  var d = bb8rDayName(ms, bb8rTz(sym));
  if (!d) return row;
  row.changeDay = d.wd;
  row.changeDayLabel = d.full;
  if (row.feed && typeof row.feed === "object" && !Array.isArray(row.feed)) {
    row.feed.changeDay = d.wd;
    row.feed.changeDayLabel = d.full;
    if (!row.feed.sessionDayUk) row.feed.sessionDayUk = d.full;
  }
  if (row.session && typeof row.session === "object") {
    row.session.changeDay = d.wd;
    if (!row.session.dayUk) row.session.dayUk = d.full;
  }
  return row;
}
function bb8rCapNote(cap) {
  if (!cap) return "";
  if (cap.status === "corrected-minor-units") return "Yahoo market cap was about 100 times shares times the pound price, so it was divided by 100; ";
  if (cap.status === "deduped") return "Yahoo market cap matched the sum of the pound cap and itself, so the two were not added; ";
  if (cap.status === "computed" || cap.status === "computed-from-pence") return "from shares times the pence price divided by 100; ";
  if (cap.priceCurrency === "GBp" || cap.priceCurrency === "GBX") return "price is in pence; Yahoo market cap is already in pounds and was not divided again; ";
  return "";
}
function bb8rMetricCap(ctx) {
  if (!ctx || !Array.isArray(ctx.facts)) return;
  ctx.facts.forEach(function (f) {
    if (!f || f.id !== "bb8o:metric" || !/market capitalisation|market cap/i.test(String(f.text || ""))) return;
    var cap = ctx.bb8rCap;
    if (!cap || !(cap.marketCap > 0)) return;
    var base = bb8rSubjectSym({ bb8eBase: ctx.bb8rSym }) || "The listing";
    f.text = base + "'s market capitalisation is " + bb8rCapText(cap.marketCap, cap.marketCapCurrency) + " (" + bb8rCapNote(cap) + "Yahoo Finance).";
    if (f.src) {
      f.src.marketCapCheck = cap;
      f.src.detail = f.text.replace(/\.$/, "") + "; price " + cap.price + " " + (cap.priceCurrency || "") + "; sharesOutstanding " + cap.sharesOutstanding + "; yahooMarketCap " + cap.yahooMarketCap;
      try { bb8qSrcText.set(f.src, f.src.detail); } catch (e) {}
    }
  });
}
function bb8rAfter(out, st) {
  if (!out || typeof out.reply !== "string" || typeof bb8qParse !== "function" || typeof bb8qRender !== "function") return out;
  var doc = bb8qParse(out);
  try { bb8rGoldWeek(doc, st); } catch (e) {}
  try { bb8rQuoteBody(doc, st); } catch (e) {}
  try { bb8rSnapDoc(doc); } catch (e) {}
  try { bb8rFiller(doc); } catch (e) {}
  try { bb8rProxyAsOf(doc); } catch (e) {}
  try { bb8rCalLine(doc, st); } catch (e) {}
  try { bb8rCites(doc); } catch (e) {}
  try { bb8rDxy(doc); } catch (e) {}
  try { doc.body = bb8rYtdLabel(doc.body); } catch (e) {}
  var r = bb8qRender(doc);
  return Object.assign({}, out, { reply: r.reply, sources: r.sources });
}
try {
  if (typeof bb3Mood === "function") {
    var bb8rMood0 = bb3Mood;
    bb3Mood = function (m) {
      var live = bb8rRegimeRow();
      if (live) return live.mood;
      var mood = bb8rMood0.apply(this, arguments);
      try { var row = bb8rRegimeRemember(mood, m); if (row) return row.mood; } catch (e) {}
      return mood;
    };
  }
  if (typeof bb8pQuoteMeta === "function") {
    var bb8rQm0 = bb8pQuoteMeta;
    bb8pQuoteMeta = function (st) {
      var q = null;
      try { q = bb8rQm0.apply(this, arguments); } catch (e) { q = null; }
      try { return bb8rQuoteMeta(st, q); } catch (e2) { return q; }
    };
  }
  if (typeof bb8pMetaFix === "function") {
    var bb8rMeta0 = bb8pMetaFix;
    bb8pMetaFix = function (meta, admin, st) {
      var m = bb8rMeta0.apply(this, arguments);
      try {
        if (st && m && typeof m === "object") {
          m.quote = bb8rQuoteMeta(st, m.quote || null);
          var row = bb8rRegimeRow();
          if (row) m.regime = bb8rRegimePublic(row);
        }
      } catch (e) {}
      return m;
    };
  }
  if (typeof bb8oProfileFrom === "function") {
    var bb8rProf0 = bb8oProfileFrom;
    bb8oProfileFrom = function (sym, yahoo) {
      var p = bb8rProf0.apply(this, arguments);
      try { return bb8rProfile(sym, yahoo, p); } catch (e) { return p; }
    };
  }
  if (typeof bb8qBuild === "function") {
    var bb8rBuild0 = bb8qBuild;
    bb8qBuild = async function (st, body) {
      var ctx = await bb8rBuild0.apply(this, arguments);
      try { bb8rStampRegime(ctx); } catch (e) {}
      try { await bb8rCalAttach(ctx); } catch (e) {}
      try {
        if (ctx && ctx.tf && ctx.tf.id === "ytd") ctx.tf.text = bb8rYtdLabel(ctx.tf.text);
        var base = st && st.bb8eBase;
        var ysym = typeof bb8bYahooSym === "function" && base ? bb8bYahooSym(base) : base;
        var y = (ysym && bb8rYahooMem[String(ysym).toUpperCase()]) || (base && bb8rYahooMem[String(base).toUpperCase()]) || null;
        if (ctx && y) {
          var ks = y.defaultKeyStatistics || {}, pr = y.price || {}, sd = y.summaryDetail || {};
          ctx.bb8rSym = base;
          ctx.bb8rCap = bb8rCap({
            currency: pr.currency || sd.currency || "",
            price: bb8rNumRaw(pr.regularMarketPrice),
            sharesOutstanding: bb8rNumRaw(ks.sharesOutstanding) || bb8rNumRaw(ks.impliedSharesOutstanding),
            marketCap: bb8rNumRaw(sd.marketCap) || bb8rNumRaw(pr.marketCap)
          });
        }
        bb8rMetricCap(ctx);
      } catch (e) {}
      return ctx;
    };
  }
  if (typeof bb8qFinish === "function") {
    var bb8rFin0 = bb8qFinish;
    bb8qFinish = function (out, st) {
      var r = bb8rFin0.apply(this, arguments);
      try { r = bb8rAfter(r, st); } catch (e) { console.warn("bb8r", e && e.message); }
      return r;
    };
  }
  if (typeof bb8lYahooShared === "function") {
    var bb8rYsh0 = bb8lYahooShared;
    bb8lYahooShared = async function (sym) {
      var y = await bb8rYsh0.apply(this, arguments);
      try { if (sym && y && typeof y === "object") bb8rYahooMem[String(sym).toUpperCase()] = y; } catch (e) {}
      return y;
    };
  }
  if (typeof yahooQuote === "function") {
    var bb8rYq0 = yahooQuote;
    yahooQuote = async function () {
      var out = await bb8rYq0.apply(this, arguments);
      try {
        if (out && typeof out === "object") {
          Object.keys(out).forEach(function (k) { if (out[k] && typeof out[k] === "object") bb8rSessionTag(out[k], k); });
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof marketReferenceQuotes === "function") {
    var bb8rRef0 = marketReferenceQuotes;
    marketReferenceQuotes = async function () {
      var out = await bb8rRef0.apply(this, arguments);
      try {
        var row = bb8rRegimeRow();
        if (out && typeof out === "object" && row) out.regime = bb8rRegimePublic(row);
      } catch (e) {}
      return out;
    };
  }
} catch (e) { console.warn("bb8r hooks skipped", e && e.message); }
// BB8R_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8r")]
if bad:
    die("bb8r block declares a non-bb8r function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8r block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8r function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "setTimeout(" in BLOCK or "stripe" in BLOCK.lower() or ".tier" in BLOCK or "process.env" in BLOCK:
    die("bb8r block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8r replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8r setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8rbak"
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
print("APPLY bb8r quote labels, GC=F YTD bar, citation rebind, regime cache, GBp cap, week calendar")
