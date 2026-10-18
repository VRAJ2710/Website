#!/usr/bin/env python3
"""patch_bb3_fit.py — one regime-fit score, and a signed Hormuz oil adjustment.

Stacks on bb2 (marker // ── bb2 ──). The live base is chat58: server.js md5
2e04b3c16f8400dc5ea211e676831b23 after patch_bb2.py plus the hotfix that
replaces user.tier !== "premium" with !hasPremiumAccess(user). A different
md5 warns and does not abort, so the patch still applies after rt53.

Does not modify /api/chat or the Ask client. A separate patch_bb3_ask.py may
change those. The two patches apply in either order: this one only appends a
/api/regime-fit route and rewrites the Hormuz oil lines. A second run prints
"REFUSE: bb3fit already applied" and exits 0, before any md5 warning.

Regime fit
  GET /api/regime-fit?ticker=MU
  also accepts ?t=MU (the markets page parameter). If both are set, ticker wins.
  Body: { "regimeFit": { ... } }
  Cache-Control: public, max-age=60
  No login check and no new table. Guests and admins share one in-memory
  snapshot, so the same prices always produce the same JSON. Only symbols in
  the desk table are scored. Any other symbol returns a null score and does
  not call upstream. The shared market pack (VIX, the S&P 500, oil, Bitcoin,
  SPY, and the dollar) is fetched at most once per 60 seconds, whatever the
  ticker. Each ticker result sits in an LRU of 64. A cache hit does not touch
  the limiter and is the same for every caller. A cache miss uses the existing
  yahooRateLimiter when that helper is loaded, otherwise a 30-per-minute
  per-address window. A limited miss returns the last stored score for that
  symbol, or a null score, and does not fetch. Missing prices on a known
  symbol are marked with a null value and add nothing.

  regimeFit fields, in order:
    ticker, score, reason, label, regime, asOf, method, version,
    inputs[{key, label, value, unit, source, asOf, weight, contribution}],
    benchmark{symbol, value, asOf}
  score is an integer 0-100, or null.
  label is Tailwind (68 and above), Neutral (45 to 67), or Headwind (below 45),
  or null when score is null.
  regime is Risk-On (mood 55 and above), Transition (40 to 54), or Risk-Off
  (below 40), or null when score is null.
  version is "bb3".
  Every asOf is an ISO 8601 UTC string.
  method, reason, and each input label are plain sentences for the reader.
  contribution is signed points. The score starts at 50 (stated in method) and
  50 plus the contributions equals the score. weight is the most that row can move.
  benchmark.symbol is SPY. benchmark.value is that fund's percent change this
  session, or null.

Hormuz
  The supply-risk score used the absolute WTI move, so a fall of 0.60% added
  1.2 points. A supply-disruption score should rise when oil rises (the market
  is pricing tighter supply) and fall when oil falls. The adjustment is now
  twice the signed move, capped at 12 points either way. The basis sentence
  says the same thing.

The Hormuz lines live in the client, so app.js?v=chatNN is bumped one step
when those lines change. rt53 may already have bumped it; the current number
is detected. No bump when the client is unchanged.

Usage: python3 patch_bb3_fit.py [--check] <dir with app.js, index.html, server.js>
CRLF-safe. node --check runs before anything is written; a later failure restores backups.
Prints md5 and line count of each file before and after. Prints no secrets.
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "server.js": "2e04b3c16f8400dc5ea211e676831b23",
    "app.js": "86153acc103ab9bd246fbdf96055ffab",
    "index.html": "4a680ac27bde0eb044944767ac6838c6",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP = os.path.join(D, "app.js")
IDX = os.path.join(D, "index.html")
SRV = os.path.join(D, "server.js")

def load(p):
    b = open(p, "rb").read()
    return b.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in b

def die(m):
    print("ABORT (nothing written):", m)
    sys.exit(1)

def show(phase, path, data=None):
    raw = open(path, "rb").read() if data is None else data
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    name = os.path.basename(path)
    digest = hashlib.md5(raw).hexdigest()
    print("bb3fit %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

def nodecheck(src, label):
    fd, tmp = tempfile.mkstemp(suffix=".js")
    os.close(fd)
    r = None
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    if r is None or r.returncode:
        err = "" if r is None else (r.stderr or "")[:500]
        die("node --check failed for %s: %s" % (label, err))

APOS, MINUS = "\u2019", "\u2212"
OLD_SCORE = "    if (wtiC != null) adj += Math.min(12, Math.abs(wtiC) * 2);"
NEW_SCORE = "    if (wtiC != null) adj += Math.round(Math.max(-12, Math.min(12, wtiC * 2)) * 10) / 10; // bb3fit: a rise in oil raises this supply-risk score; a fall lowers it"
OLD_BASIS = (
    "`Oil adjustment: twice today" + APOS + "s WTI move (${oilC >= 0 ? '+' : '" + MINUS
    + "'}${Math.abs(oilC).toFixed(2)}%), up to 12: +${Math.round(Math.min(12, Math.abs(oilC) * 2) * 10) / 10}`"
)
NEW_BASIS = (
    "`Oil adjustment: twice today" + APOS + "s WTI move (${oilC >= 0 ? '+' : '" + MINUS
    + "'}${Math.abs(oilC).toFixed(2)}%), capped at 12 points either way: ${(_bb3p => (_bb3p > 0 ? '+' : _bb3p < 0 ? '"
    + MINUS + "' : '') + Math.abs(_bb3p))(Math.round(Math.max(-12, Math.min(12, oilC * 2)) * 10) / 10)}. A rise in oil raises this supply-risk score; a fall lowers it.`"
)

SERVER_BLOCK = r'''
// ── bb3fit ── One regime-fit score for every visitor, from one cached market snapshot.
// GET /api/regime-fit?ticker=MU returns { regimeFit }. Public cache, 60 seconds. No login check.
// Only desk symbols are scored. The market pack is one fetch per 60 seconds. Ticker results are an LRU of 64.
// A cache hit skips the limiter. A miss uses yahooRateLimiter when it is loaded. A limited miss does not fetch.
// BB3_FIT_JS
const BB3_VERSION = "bb3";
const BB3_BASELINE = 50;
const BB3_TTL = 60 * 1000;
const BB3_STALE = 15 * 60 * 1000;
const BB3_ROWS = JSON.parse('[["AAPL","none","other",1.18],["ABBV","positive","other",0.62],["ABNB","positive","other",1.42],["ABT","positive","other",0.75],["ACN","positive","other",1.02],["ADA","none","crypto",2.2],["ADBE","none","other",1.22],["ADSK","none","other",1.12],["ALGO","none","crypto",1.8],["AMAT","positive","other",1.45],["AMD","positive","other",1.68],["AMGN","none","other",0.55],["AMT","none","other",0.88],["AMZN","positive","other",1.22],["APT","none","crypto",2.4],["ARKK","none","other",1.8],["ARM","positive","other",1.85],["ASML","positive","other",1.18],["ASX200","none","other",0.85],["ATOM","none","crypto",1.9],["AUDUSD","none","other",0.18],["AVAX","positive","crypto",2.45],["AVGO","positive","other",1.28],["BA","cautious","other",1.42],["BABA","none","other",0.92],["BAC","positive","other",1.38],["BCH","none","crypto",1.85],["BLK","positive","other",1.28],["BMY","none","other",0.45],["BP","none","other",0.68],["BRENT","none","commodity",0.5],["BRKB","positive","other",0.88],["BTC","positive","crypto",1.85],["C","none","other",1.45],["CAC","none","other",1.12],["CAT","positive","other",1.08],["COCOA","positive","commodity",0.25],["COFFEE","positive","commodity",0.28],["COIN","positive","other",3.2],["COP","positive","other",0.98],["COPPER","positive","commodity",0.42],["CORN","none","commodity",0.3],["COST","positive","other",0.72],["CRM","positive","other",1.18],["CRWD","positive","other",1.42],["CSCO","none","other",0.82],["CVX","positive","other",0.92],["DASH","positive","other",1.52],["DDOG","positive","other",1.35],["DE","none","other",0.95],["DEO","none","other",0.58],["DIS","none","other",1.05],["DOGE","none","crypto",3.2],["DOT","none","crypto",2.1],["DUK","none","other",0.42],["EEM","none","other",1.1],["ENPH","cautious","other",2.0],["EOG","positive","other",1.1],["EQIX","positive","other",0.95],["ETH","none","crypto",1.65],["EURGBP","none","other",0.1],["EURJPY","none","other",0.2],["EURUSD","none","other",0.15],["F","none","other",1.38],["FIL","none","crypto",2.15],["FSLR","positive","other",1.4],["GBPJPY","none","other",0.25],["GBPUSD","none","other",0.18],["GILD","none","other",0.42],["GM","none","other",1.22],["GME","none","other",2.8],["GOOGL","positive","other",1.08],["GS","positive","other",1.38],["HBAR","none","crypto",1.95],["HD","positive","other",1.02],["HON","none","other",0.95],["HOOD","positive","other",2.4],["INFY","none","other",0.82],["INJ","positive","crypto",2.3],["INTC","cautious","other",1.28],["INTU","positive","other",1.18],["ISRG","positive","other",0.92],["IWM","none","other",1.25],["JNJ","none","other",0.62],["JPM","positive","other",1.12],["KO","positive","other",0.58],["KOSPI","none","other",1.05],["LINK","positive","crypto",1.95],["LLY","positive","other",0.48],["LMT","positive","other",0.65],["LOW","none","other",1.12],["LRCX","positive","other",1.55],["LTC","none","crypto",1.65],["LUMBER","none","commodity",0.45],["MA","positive","other",0.95],["MCD","positive","other",0.72],["META","positive","other",1.35],["MRK","positive","other",0.55],["MRVL","positive","other",1.65],["MS","positive","other",1.42],["MSFT","none","other",0.92],["MSTR","none","other",3.5],["MU","positive","other",1.62],["NEAR","positive","crypto",2.15],["NEE","none","other",0.52],["NET","positive","other",1.42],["NFLX","positive","other",1.2],["NG","cautious","commodity",0.55],["NKE","none","other",0.92],["NOW","positive","other",1.08],["NVDA","positive","other",1.72],["NVO","positive","other",0.45],["NVS","positive","other",0.48],["NZDUSD","cautious","other",0.22],["O","none","other",0.75],["OJ","positive","commodity",0.22],["ORCL","positive","other",0.88],["PALLADIUM","cautious","commodity",0.55],["PANW","positive","other",1.18],["PEP","positive","other",0.52],["PEPE","none","crypto",4.0],["PFE","cautious","other",0.58],["PG","positive","other",0.48],["PLAT","none","commodity",0.32],["PLD","none","other",1.0],["PLTR","positive","other",2.12],["PM","positive","other",0.62],["POL","none","crypto",2.4],["PYPL","none","other",1.38],["QCOM","positive","other",1.32],["QQQ","positive","other",1.15],["REGN","positive","other",0.52],["RIO","none","other",0.78],["RIVN","cautious","other",2.85],["RKLB","positive","other",2.1],["RTX","positive","other",0.92],["RUT","none","other",1.25],["SAP","positive","other",0.82],["SBUX","none","other",0.88],["SCHW","none","other",1.28],["SHEL","none","other",0.72],["SHIB","none","crypto",3.5],["SHOP","positive","other",1.65],["SLB","positive","other",1.2],["SLV","positive","commodity",0.35],["SMCI","positive","other",2.2],["SNOW","none","other",1.42],["SO","none","other",0.42],["SOL","positive","crypto",2.1],["SONY","positive","other",0.92],["SOXX","positive","other",1.6],["SPG","none","other",1.2],["SPOT","positive","other",1.5],["SPY","none","other",1.0],["SUI","positive","crypto",2.6],["T","none","other",0.62],["TLT","cautious","other",-0.2],["TM","none","other",0.72],["TMO","positive","other",0.72],["TNX","none","other",0.1],["TON","positive","crypto",2.3],["TSLA","none","other",2.05],["TSM","positive","other",1.22],["TXN","positive","other",1.08],["UBER","positive","other",1.35],["UL","none","other",0.52],["UNH","positive","other",0.68],["UNI","positive","crypto",2.25],["UPS","none","other",1.02],["URA","positive","other",1.3],["USDBRL","cautious","other",0.35],["USDCAD","none","other",0.15],["USDCHF","none","other",0.12],["USDINR","none","other",0.12],["USDJPY","none","other",0.22],["USDMXN","none","other",0.28],["V","positive","other",0.92],["VALE","none","other",1.02],["VRTX","positive","other",0.55],["VZ","none","other",0.42],["WFC","none","other",1.18],["WHEAT","none","commodity",0.35],["WMT","positive","other",0.52],["WTI","none","commodity",0.45],["XAU","positive","commodity",-0.15],["XLB","none","other",1.0],["XLC","positive","other",1.1],["XLE","positive","other",0.9],["XLF","positive","other",1.1],["XLI","none","other",1.05],["XLK","positive","other",1.2],["XLM","none","crypto",1.62],["XLP","none","other",0.55],["XLRE","none","other",0.85],["XLU","none","other",0.45],["XLV","none","other",0.7],["XLY","none","other",1.15],["XOM","positive","other",0.82],["XRP","none","crypto",1.42],["ZS","positive","other",1.38]]');
const BB3_ALIAS_ROWS = JSON.parse('[["SPX","^GSPC"],["DJIA","^DJI"],["IXIC","^IXIC"],["FTSE","^FTSE"],["DAX","^GDAXI"],["N225","^N225"],["NSEI","^NSEI"],["HSI","^HSI"],["XAU","GC=F"],["WTI","CL=F"],["SLV","SI=F"],["NG","NG=F"],["EURUSD","EURUSD=X"],["GBPUSD","GBPUSD=X"],["USDJPY","JPY=X"],["DXY","DX-Y.NYB"],["VIX","^VIX"],["BRKB","BRK-B"],["AUDUSD","AUDUSD=X"],["USDCAD","CAD=X"],["USDCHF","CHF=X"],["NZDUSD","NZDUSD=X"],["EURGBP","EURGBP=X"],["COPPER","HG=F"],["WHEAT","ZW=F"],["CORN","ZC=F"],["COFFEE","KC=F"],["PLAT","PL=F"],["COCOA","CC=F"],["OJ","OJ=F"],["LUMBER","LBR=F"],["PALLADIUM","PA=F"],["CAC","^FCHI"],["ASX200","^AXJO"],["KOSPI","^KS11"],["USDMXN","MXN=X"],["USDBRL","BRL=X"],["USDINR","INR=X"],["RUT","^RUT"],["TNX","^TNX"],["BRENT","BZ=F"],["EURJPY","EURJPY=X"],["GBPJPY","GBPJPY=X"],["BTC","BTC-USD"],["ETH","ETH-USD"],["SOL","SOL-USD"],["XRP","XRP-USD"],["DOGE","DOGE-USD"],["ADA","ADA-USD"],["AVAX","AVAX-USD"],["LINK","LINK-USD"],["DOT","DOT-USD"],["LTC","LTC-USD"],["UNI","UNI7083-USD"],["POL","POL28321-USD"],["NEAR","NEAR-USD"],["ALGO","ALGO-USD"],["HBAR","HBAR-USD"],["BCH","BCH-USD"],["XLM","XLM-USD"],["FIL","FIL-USD"],["APT","APT21794-USD"],["SUI","SUI20947-USD"],["ATOM","ATOM-USD"],["INJ","INJ-USD"],["SHIB","SHIB-USD"],["PEPE","PEPE24478-USD"],["TON","TON11419-USD"]]');
const BB3_MAP = {};
BB3_ROWS.forEach(function (row) { BB3_MAP[row[0]] = { stance: row[1], cat: row[2], beta: row[3] }; });
const BB3_ALIAS = {};
BB3_ALIAS_ROWS.forEach(function (row) { BB3_ALIAS[row[0]] = row[1]; });
const BB3_METHOD = "The score starts at 50. Each row adds or subtracts its contribution, in points. Weight is the most that row can move the score. If a figure is missing, that row adds nothing, and every visitor looking at the same prices sees the same total. The total is kept between 0 and 100; that correction is the last row, and it is zero when the total was already in range. 68 and above is Tailwind, 45 to 67 is Neutral, and below 45 is Headwind. The market mood is a separate reading that also starts at 50. It uses five figures, rounded to two decimals before the points are chosen: how much traders are paying to insure US shares, the S&P 500's move today, the dollar's level, whether oil is above 95 dollars a barrel, and Bitcoin's move today. If the S&P 500 index print is missing, the S&P 500 fund's move is used instead, for every visitor. The dollar's level is the desk's published dollar index when that is available, and otherwise the exchange dollar index. 55 and above is Risk-On, 40 to 54 is Transition, and below 40 is Risk-Off. A positive desk view adds 18 when the mood is 55 or above. A cautious desk view adds 12 when the mood is below 45. A commodity adds 15 when the mood favours energy or gold, which it does unless the mood is 60 or above and oil is not above 90 dollars. Crypto adds 12 when the mood is 58 or above, and loses 15 when the mood is below 42. A gain of more than 1.5 percent adds 8 when the mood is 55 or above. A fall of more than 2 percent takes off 10. A name that usually moves more than 1.5 times as sharply as the market loses 12 when the mood is below 60. The benchmark value is the S&P 500 fund's own percent change this session.";
const BB3_FIT_MAX = 64;
const BB3_MISS_LIMIT = 30;
const BB3_MISS_WINDOW = 60 * 1000;
const BB3_MISS_KEYS = 1024;
const BB3_BOX = { at: 0, pack: null, pending: null, fits: new Map(), fitPending: new Map(), lastGood: new Map() };
const BB3_LOCAL = { hits: new Map() };

function bb3Reset() {
  BB3_BOX.at = 0;
  BB3_BOX.pack = null;
  BB3_BOX.pending = null;
  BB3_BOX.fits = new Map();
  BB3_BOX.fitPending = new Map();
  BB3_BOX.lastGood = new Map();
  BB3_LOCAL.hits = new Map();
}
function bb3FitMax() { return BB3_FIT_MAX; }
function bb3CacheSize() { return BB3_BOX.fits.size; }
function bb3Hot(ticker) { return BB3_BOX.fits.has(ticker); }
function bb3Tickers() { return Object.keys(BB3_MAP); }
function bb3DropHot() { BB3_BOX.fits = new Map(); }
function bb3Known(ticker) { return Object.prototype.hasOwnProperty.call(BB3_MAP, ticker); }
function bb3LruSet(map, key, value) {
  if (map.has(key)) map.delete(key);
  map.set(key, value);
  while (map.size > BB3_FIT_MAX) map.delete(map.keys().next().value);
}
function bb3Client(req) {
  const headers = (req && req.headers) || {};
  const fwd = headers["x-forwarded-for"] || headers["X-Forwarded-For"] || "";
  const ip = String(fwd).split(",")[0].trim();
  if (ip) return ip.slice(0, 80);
  const sock = req && req.socket && req.socket.remoteAddress;
  return sock ? String(sock).slice(0, 80) : "unknown";
}
function bb3LocalAllow(ip, now) {
  const key = ip || "unknown";
  let row = BB3_LOCAL.hits.get(key);
  if (!row || now - row.at >= BB3_MISS_WINDOW) row = { at: now, n: 0 };
  BB3_LOCAL.hits.delete(key);
  BB3_LOCAL.hits.set(key, row);
  while (BB3_LOCAL.hits.size > BB3_MISS_KEYS) BB3_LOCAL.hits.delete(BB3_LOCAL.hits.keys().next().value);
  if (row.n >= BB3_MISS_LIMIT) return false;
  row.n += 1;
  return true;
}
function bb3AllowMiss(req, now) {
  const ip = bb3Client(req);
  if (typeof yahooRateLimiter !== "undefined" && yahooRateLimiter && typeof yahooRateLimiter.allow === "function") {
    return !!yahooRateLimiter.allow(ip);
  }
  return bb3LocalAllow(ip, now);
}
function bb3Remember(ticker, fit, now) {
  bb3LruSet(BB3_BOX.fits, ticker, { fit: fit, at: now, packAt: BB3_BOX.at });
  bb3LruSet(BB3_BOX.lastGood, ticker, fit);
}
function bb3Hit(ticker, now) {
  const hit = BB3_BOX.fits.get(ticker);
  if (!hit || !BB3_BOX.pack || hit.packAt !== BB3_BOX.at || now - hit.at >= BB3_TTL) return null;
  bb3LruSet(BB3_BOX.fits, ticker, hit);
  return hit.fit;
}
function bb3Limited(ticker, now) {
  if (BB3_BOX.lastGood.has(ticker)) return BB3_BOX.lastGood.get(ticker);
  const stamp = BB3_BOX.at ? BB3_BOX.at : Math.floor(now / BB3_TTL) * BB3_TTL;
  return bb3Blank(ticker, "This score is temporarily unavailable. Nothing is shown rather than a different number.", stamp);
}
function bb3Round(n, dp) {
  const f = Math.pow(10, dp == null ? 2 : dp);
  return Math.round(Number(n) * f) / f;
}
function bb3Num(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  return isFinite(n) ? bb3Round(n, 2) : null;
}
function bb3Iso(ms) {
  const d = new Date(ms);
  return isFinite(d.getTime()) ? d.toISOString() : new Date(0).toISOString();
}
function bb3OilPoints(pct) {
  if (pct == null || !isFinite(Number(pct))) return null;
  return bb3Round(Math.max(-12, Math.min(12, Number(pct) * 2)), 1);
}
function bb3ChokeScore(base, wtiPct, vix) {
  let adj = Number(base);
  if (!isFinite(adj)) adj = 0;
  const oil = bb3OilPoints(wtiPct);
  if (oil != null) adj += oil;
  if (vix != null && isFinite(Number(vix)) && Number(vix) > 20) adj += 4;
  return Math.min(99, Math.round(adj));
}
function bb3Profile(ticker) {
  const row = BB3_MAP[ticker];
  if (!row) return { stance: "none", cat: "other", beta: null, known: false };
  return { stance: row.stance, cat: row.cat, beta: row.beta, known: true };
}
function bb3Mood(m) {
  m = m || {};
  const vix = bb3Num(m.vix), spx = bb3Num(m.spx), dxy = bb3Num(m.dxy), oil = bb3Num(m.oil), btc = bb3Num(m.btc);
  let score = BB3_BASELINE;
  if (vix != null) {
    if (vix < 16) score += 18;
    else if (vix < 20) score += 8;
    else if (vix > 28) score -= 22;
    else if (vix > 22) score -= 12;
  }
  if (spx != null) {
    if (spx > 0.5) score += 8;
    else if (spx < -0.5) score -= 10;
  }
  if (dxy != null) {
    if (dxy < 99) score += 6;
    else if (dxy > 101) score -= 6;
  }
  if (oil != null && oil > 95) score -= 5;
  if (btc != null && btc > 2) score += 4;
  if (score > 100) score = 100;
  if (score < 0) score = 0;
  let regime = "Risk-Off";
  if (score >= 55) regime = "Risk-On";
  else if (score >= 40) regime = "Transition";
  const favoursCommodity = score < 60 || (oil != null && oil > 90);
  return { score: score, regime: regime, vix: vix, spx: spx, dxy: dxy, oil: oil, btc: btc, favoursCommodity: favoursCommodity, wary: score < 60 };
}
function bb3Finish(raw) {
  let score = raw;
  if (score > 100) score = 100;
  if (score < 0) score = 0;
  score = Math.round(score);
  return { score: score, bounds: score - raw };
}
function bb3In(key, label, value, unit, source, ms, weight, contribution) {
  return { key: key, label: label, value: value, unit: unit, source: source, asOf: bb3Iso(ms), weight: weight, contribution: contribution };
}
function bb3Blank(ticker, reason, nowMs) {
  const asOf = bb3Iso(nowMs);
  return {
    ticker: ticker || "",
    score: null,
    reason: reason,
    label: null,
    regime: null,
    asOf: asOf,
    method: BB3_METHOD,
    version: BB3_VERSION,
    inputs: [],
    benchmark: { symbol: "SPY", value: null, asOf: asOf }
  };
}
function bb3Assemble(ticker, profile, mood, session, spy, nowMs, sessionAsOfMs, spyAsOfMs) {
  profile = profile || { stance: "none", cat: "other", beta: null, known: false };
  const inputs = [];
  const deskVal = profile.stance === "positive" ? "Positive" : profile.stance === "cautious" ? "Cautious" : "None";
  let deskC = 0;
  if (profile.stance === "positive" && mood.score >= 55) deskC = 18;
  if (profile.stance === "cautious" && mood.score < 45) deskC = 12;
  inputs.push(bb3In("desk", "Desk view in this market mood", deskVal, "", "Dispatch desk reference", nowMs, 18, deskC));
  const comVal = profile.cat === "commodity" ? "Commodity" : "Not a commodity";
  const comC = profile.cat === "commodity" && mood.favoursCommodity ? 15 : 0;
  inputs.push(bb3In("commodity", "Commodity link to this market mood", comVal, "", "Dispatch desk reference", nowMs, 15, comC));
  const cryVal = profile.cat === "crypto" ? "Crypto" : "Not crypto";
  let cryC = 0;
  if (profile.cat === "crypto" && mood.score >= 58) cryC = 12;
  if (profile.cat === "crypto" && mood.score < 42) cryC = -15;
  inputs.push(bb3In("crypto", "Crypto link to this market mood", cryVal, "", "Dispatch desk reference", nowMs, 15, cryC));
  const sess = bb3Num(session);
  let sessC = 0;
  if (sess != null && sess > 1.5 && mood.score >= 55) sessC = 8;
  if (sess != null && sess < -2) sessC = -10;
  inputs.push(bb3In("session", "Today's price move", sess, "percent", "Yahoo Finance", sess == null ? nowMs : (sessionAsOfMs || nowMs), 10, sessC));
  const beta = profile.beta == null ? null : bb3Num(profile.beta);
  const sensC = beta != null && mood.wary && beta > 1.5 ? -12 : 0;
  inputs.push(bb3In("sensitivity", "How sharply this name moves when the market falls", beta, "times the market", "Dispatch desk reference", nowMs, 12, sensC));
  const raw = BB3_BASELINE + inputs.reduce(function (sum, row) { return sum + row.contribution; }, 0);
  const done = bb3Finish(raw);
  inputs.push(bb3In("bounds", "Kept between 0 and 100", raw, "points", "Dispatch desk reference", nowMs, 0, done.bounds));
  const label = done.score >= 68 ? "Tailwind" : done.score >= 45 ? "Neutral" : "Headwind";
  const bits = [label + ", " + done.score + " out of 100, while the market mood is " + mood.regime + ". The score starts at 50."];
  if (deskC === 18) bits.push("The desk's positive view fits this mood, which adds 18.");
  if (deskC === 12) bits.push("The desk's cautious view fits this mood, which adds 12.");
  if (comC) bits.push("This is a commodity and the mood favours energy or gold, which adds 15.");
  if (cryC === 12) bits.push("This is crypto and the mood supports it, which adds 12.");
  if (cryC === -15) bits.push("This is crypto and the mood works against it, which takes off 15.");
  if (sessC === 8) bits.push("Today's rise is above 1.5 percent in a supportive mood, which adds 8.");
  if (sessC === -10) bits.push("Today's fall is past 2 percent, which takes off 10.");
  if (sess == null) bits.push("Today's price was not available, so that row added nothing.");
  if (sensC === -12) bits.push("This name moves more sharply than the market, and the mood is wary of that, which takes off 12.");
  if (beta == null) bits.push("How sharply it moves with the market was not on the desk list, so that row added nothing.");
  if (done.bounds) bits.push("The total was kept between 0 and 100.");
  if (bits.length === 1) bits.push("None of the rows moved the score.");
  const spyVal = spy == null || !isFinite(Number(spy)) ? null : bb3Num(spy);
  return {
    ticker: ticker,
    score: done.score,
    reason: bits.join(" "),
    label: label,
    regime: mood.regime,
    asOf: bb3Iso(nowMs),
    method: BB3_METHOD,
    version: BB3_VERSION,
    inputs: inputs,
    benchmark: { symbol: "SPY", value: spyVal, asOf: bb3Iso(spyAsOfMs || nowMs) }
  };
}
function bb3QuotePct(q) {
  if (!q || !isFinite(Number(q.p)) || Number(q.p) <= 0) return null;
  if (q.basis === "none") return null;
  if (!isFinite(Number(q.c))) return null;
  return Number(q.c);
}
function bb3QuotePx(q) {
  if (!q || !isFinite(Number(q.p)) || Number(q.p) <= 0) return null;
  return Number(q.p);
}
function bb3QuoteMs(q, fallback) {
  if (!q || q.ts == null || !isFinite(Number(q.ts)) || Number(q.ts) <= 0) return fallback;
  const n = Number(q.ts);
  return n < 1e12 ? n * 1000 : n;
}
function bb3Yahoo(ticker) { return BB3_ALIAS[ticker] || ticker; }
async function bb3Quotes(symbols) {
  if (typeof yahooQuote !== "function") return {};
  try {
    const got = await yahooQuote(symbols);
    return got && typeof got === "object" ? got : {};
  } catch (e) {
    return {};
  }
}
async function bb3Pack(now) {
  if (BB3_BOX.pack && now - BB3_BOX.at < BB3_TTL) return BB3_BOX.pack;
  if (BB3_BOX.pending) return BB3_BOX.pending;
  const stamp = now;
  BB3_BOX.pending = (async function () {
    const quotes = await bb3Quotes(["^VIX", "^GSPC", "CL=F", "BTC-USD", "SPY", "DX-Y.NYB"]);
    let dxy = null;
    try { if (typeof fetchSyntheticDxy === "function") dxy = await fetchSyntheticDxy(); } catch (e) { dxy = null; }
    const thin = !quotes["^VIX"] && !quotes["^GSPC"] && !quotes["SPY"];
    if (thin && BB3_BOX.pack && stamp - BB3_BOX.at < BB3_STALE) return BB3_BOX.pack;
    const pack = { quotes: quotes, dxy: dxy, extra: {}, at: stamp };
    BB3_BOX.pack = pack;
    BB3_BOX.at = stamp;
    BB3_BOX.fits = new Map();
    return pack;
  })();
  try { return await BB3_BOX.pending; }
  finally { BB3_BOX.pending = null; }
}
async function bb3OneQuote(pack, yahooSym) {
  if (pack.quotes && pack.quotes[yahooSym]) return pack.quotes[yahooSym];
  if (Object.prototype.hasOwnProperty.call(pack.extra, yahooSym)) return pack.extra[yahooSym];
  if (!pack.extraPending) pack.extraPending = new Map();
  if (!pack.extraPending.has(yahooSym)) {
    pack.extraPending.set(yahooSym, bb3Quotes([yahooSym]).then(function (got) {
      const row = got[yahooSym] || null;
      pack.extra[yahooSym] = row;
      return row;
    }));
  }
  return pack.extraPending.get(yahooSym);
}
async function bb3Compute(ticker, now) {
  const pack = await bb3Pack(now);
  const q = await bb3OneQuote(pack, bb3Yahoo(ticker));
  const spyQ = pack.quotes ? pack.quotes["SPY"] : null;
  const indexPct = bb3QuotePct(pack.quotes && pack.quotes["^GSPC"]);
  const spyPct = bb3QuotePct(spyQ);
  const dxyQ = pack.dxy && isFinite(Number(pack.dxy.p)) && Number(pack.dxy.p) > 0 ? pack.dxy : (pack.quotes && pack.quotes["DX-Y.NYB"]);
  const mood = bb3Mood({
    vix: bb3QuotePx(pack.quotes && pack.quotes["^VIX"]),
    spx: indexPct != null ? indexPct : spyPct,
    dxy: bb3QuotePx(dxyQ),
    oil: bb3QuotePx(pack.quotes && pack.quotes["CL=F"]),
    btc: bb3QuotePct(pack.quotes && pack.quotes["BTC-USD"])
  });
  return bb3Assemble(ticker, bb3Profile(ticker), mood, bb3QuotePct(q), spyPct, pack.at, q ? bb3QuoteMs(q, pack.at) : pack.at, spyQ ? bb3QuoteMs(spyQ, pack.at) : pack.at);
}
function bb3CachedFit(ticker, req, now) {
  const hit = bb3Hit(ticker, now);
  if (hit) return Promise.resolve(hit);
  if (BB3_BOX.fitPending.has(ticker)) return BB3_BOX.fitPending.get(ticker);
  if (!bb3AllowMiss(req, now)) return Promise.resolve(bb3Limited(ticker, now));
  const job = bb3Compute(ticker, now).then(function (fit) {
    bb3Remember(ticker, fit, Date.now());
    return fit;
  }).finally(function () {
    if (BB3_BOX.fitPending.get(ticker) === job) BB3_BOX.fitPending.delete(ticker);
  });
  BB3_BOX.fitPending.set(ticker, job);
  return job;
}
async function bb3RegimeFit(req, res) {
  const now = Date.now();
  let ticker = "";
  try {
    const host = (req.headers && (req.headers.host || req.headers.Host)) || "localhost";
    const url = new URL(req.url || "/", "http://" + host);
    const raw = url.searchParams.has("ticker") ? url.searchParams.get("ticker") : (url.searchParams.get("t") || "");
    const text = String(raw == null ? "" : raw);
    ticker = text.length > 32 ? "" : text.trim().toUpperCase();
  } catch (e) { ticker = ""; }
  if (!/^[A-Z0-9.^=-]{1,14}$/.test(ticker) || !bb3Known(ticker)) {
    const fit = bb3Blank(String(ticker || "").slice(0, 14), "Enter a market symbol such as MU. No score is shown rather than a guessed one.", now);
    return json(res, 200, { regimeFit: fit }, { "Cache-Control": "public, max-age=60" });
  }
  const fit = await bb3CachedFit(ticker, req, now);
  const caching = fit && fit.score == null ? "no-store" : "public, max-age=60";
  return json(res, 200, { regimeFit: fit }, { "Cache-Control": caching });
}
try {
  const bb3Handle0 = handle;
  handle = async function (req, res) {
    try {
      const host = (req.headers && (req.headers.host || req.headers.Host)) || "localhost";
      const url = new URL(req.url || "/", "http://" + host);
      if (url.pathname === "/api/regime-fit") {
        if (req.method !== "GET" && req.method !== "HEAD") {
          if (res && typeof res.setHeader === "function") res.setHeader("Allow", "GET, HEAD");
          return json(res, 405, { error: "Method not allowed." });
        }
        return await bb3RegimeFit(req, res);
      }
    } catch (e) {}
    return bb3Handle0.apply(this, arguments);
  };
} catch (e) { console.warn("bb3fit route skipped"); }
// BB3_FIT_JS_END
'''

def main():
    for p in (APP, IDX, SRV):
        if not os.path.isfile(p):
            die("missing " + p)
    s, crlf = load(APP)
    h, hcrlf = load(IDX)
    v, vcrlf = load(SRV)
    if "// \u2500\u2500 bb3fit \u2500\u2500" in v or "// bb3fit:" in s:
        print("REFUSE: bb3fit already applied")
        return 0
    for path in (APP, IDX, SRV):
        digest = show("before", path)
        expect = EXPECTED_MD5.get(os.path.basename(path)) or ""
        if expect and digest != expect:
            print("WARN md5 %s: have %s expected %s (anchors still decide)" % (os.path.basename(path), digest, expect))
    miss = []
    def need(hay, needle, label, n=None):
        c = hay.count(needle)
        if n is None:
            if c < 1:
                miss.append("%s missing" % label)
        elif c != n:
            miss.append("%s matched %d times" % (label, c))
    need(v, "// \u2500\u2500 bb2 \u2500\u2500", "server.js bb2 marker")
    need(v, "async function yahooQuote(", "server.js yahooQuote")
    need(v, "async function fetchSyntheticDxy(", "server.js fetchSyntheticDxy")
    need(v, "function json(", "server.js json")
    need(s, "// \u2500\u2500 bb2 \u2500\u2500", "app.js bb2 marker")
    need(s, OLD_SCORE, "app.js Hormuz score line", 1)
    need(s, OLD_BASIS, "app.js Hormuz basis line", 1)
    chat_hits = re.findall(r'app\.js\?v=chat(\d+)"', h)
    chat_n = None
    if len(chat_hits) != 1:
        miss.append('index.html app.js?v=chatNN" matched %d times' % len(chat_hits))
    else:
        chat_n = int(chat_hits[0])
        if chat_n < 58:
            miss.append("index.html is chat%d; need chat58 or later (bb2)" % chat_n)
    if miss:
        print("ABORT (nothing written):")
        for item in miss:
            print("ABORT:", item)
        sys.exit(1)
    new_s = s.replace(OLD_SCORE, NEW_SCORE, 1).replace(OLD_BASIS, NEW_BASIS, 1)
    if new_s.count("// bb3fit:") != 1 or "Math.abs(wtiC)" in new_s or "Math.abs(oilC) * 2" in new_s:
        die("Hormuz sign was not fully replaced")
    if new_s.count("sendChatMessage") != s.count("sendChatMessage"):
        die("refusing to change Ask chat code")
    new_h = h
    if new_s != s:
        base, nxt = "chat%d" % chat_n, "chat%d" % (chat_n + 1)
        token = 'app.js?v=%s"' % base
        if new_h.count(token) != 1:
            die("index cache token matched %d times" % new_h.count(token))
        new_h = new_h.replace(token, 'app.js?v=%s"' % nxt, 1)
        print("bb3fit index %s -> %s" % (base, nxt))
    block = SERVER_BLOCK.strip("\n")
    if block.count("// \u2500\u2500 bb3fit \u2500\u2500") != 1 or "/api/regime-fit" not in block:
        die("server block is incomplete")
    if "/api/chat" in block or "sendChatMessage" in block or "user.tier" in block:
        die("server block touches Ask or chat")
    new_v = v.rstrip("\n") + "\n" + block + "\n"
    if new_v.count('"/api/chat"') != v.count('"/api/chat"'):
        die("refusing to change /api/chat")
    if new_v.count("// \u2500\u2500 bb2 \u2500\u2500") < 1 or new_v.count("// \u2500\u2500 bb3fit \u2500\u2500") != 1:
        die("server markers after build are wrong")
    nodecheck(new_s, "app.js")
    nodecheck(new_v, "server.js")
    print("node --check passed" + (" (dry run)" if CHECK else ""))
    after = {APP: encode(new_s, crlf), IDX: encode(new_h, hcrlf), SRV: encode(new_v, vcrlf)}
    for path in (APP, IDX, SRV):
        show("after", path, after[path])
    if CHECK:
        print("dry run, nothing written")
        return 0
    def restore(baks):
        for path, bak in baks:
            if os.path.exists(bak):
                open(path, "wb").write(open(bak, "rb").read())
                os.unlink(bak)
    baks = []
    try:
        for path in (APP, IDX, SRV):
            bak = path + ".bb3fitbak"
            open(bak, "wb").write(open(path, "rb").read())
            baks.append((path, bak))
            open(path, "wb").write(after[path])
        for path in (APP, SRV):
            r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
            if r.returncode:
                restore(baks)
                print("ABORT: node --check failed after write; backups restored:", (r.stderr or "")[:400])
                return 1
        for path, bak in baks:
            os.unlink(bak)
    except Exception as e:
        restore(baks)
        print("ABORT: write failed; backups restored:", e)
        return 1
    print("written", APP, IDX, SRV)
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
