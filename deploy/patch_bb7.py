#!/usr/bin/env python3
"""patch_bb7.py — SEC Form 4 and House PTR disclosures. Server.js only.

Stacked on bb6 (server md5 3d7e492fb982dda566939f52f792b74b). Does not rewrite
app.js or index.html and does not bump the client cache token.

GET /api/insiders reads EDGAR Form 4 filings and the House Clerk's yearly
PTR index. Guests and free members see five open-market P/S rows. Premium,
including admins via hasPremiumAccess, can ask for every code and the House
list. There is no PDF text library in package.json, so House filings are
listed with links and marked See filing.

Usage: python3 patch_bb7.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "b45b28623e1c8368140406558df95b90",
    "index.html": "b2271ff3debbf8790a4cdeb5a42b8297",
    "server.js": "3d7e492fb982dda566939f52f792b74b",
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
    print("bb7 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb7 before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb7 %s untouched" % label)

chat_n = None
if idx_before is not None:
    hits = re.findall(r'app\.js\?v=chat(\d+)"', idx_before.decode("utf-8", "replace"))
    if len(hits) == 1:
        chat_n = int(hits[0])
        print("index chat%d unchanged" % chat_n)
    else:
        print("WARN index.html cache token count=%d (not modified)" % len(hits))

if "// \u2500\u2500 bb7 \u2500\u2500" in v:
    print("REFUSE: bb7 already applied")
    sys.exit(0)

ROUTE_OLD = "  if (p === \"/api/institutional-data\" && req.method === \"GET\") {"
ROUTE_NEW = "  if (p === \"/api/insiders\") return bb7Route(req, res, url);\n" + ROUTE_OLD

miss = []
if "// \u2500\u2500 bb6 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb6 ──")
if v.count(ROUTE_OLD) != 1:
    miss.append("server.js anchor insiders route matched %d times" % v.count(ROUTE_OLD))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)

v = v.replace(ROUTE_OLD, ROUTE_NEW, 1)

BLOCK = r"""
// ── bb7 ── Insider Form 4 and House PTR disclosures. In-request only.
// BB7_JS
// EDGAR: https://www.sec.gov/files/company_tickers.json and https://data.sec.gov/submissions/CIK##########.json
// House index verified 2026-10-19: https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.zip
// PTR pdf verified: https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{YEAR}/{DocID}.pdf
var bb7Mem = new Map();
var bb7EdgarHits = [];
var bb7Inflight = new Map();
var bb7DiskReady = false;
var bb7FormTtl = 6 * 60 * 60 * 1000;
var bb7HouseTtl = 24 * 60 * 60 * 1000;
var bb7PdfTtl = 24 * 60 * 60 * 1000;
function bb7Now() {
  try {
    if (typeof globalThis.bb7Clock === "function") {
      var n = Number(globalThis.bb7Clock());
      if (isFinite(n)) return n;
    }
  } catch (e) {}
  return Date.now();
}
function bb7Premium(user) {
  try { return typeof hasPremiumAccess === "function" && hasPremiumAccess(user) === true; }
  catch (e) { return false; }
}
function bb7Headers() {
  return {
    "User-Agent": "TheDispatchMarkets admin@thedispatch.uk",
    "Accept-Encoding": "gzip, deflate",
    Accept: "application/json, application/xml, text/xml, application/zip, application/pdf;q=0.8, */*;q=0.5"
  };
}
function bb7TakeToken(now) {
  var windowMs = 1000;
  var limit = 10;
  var t = Number(now);
  var keep = [];
  for (var i = 0; i < bb7EdgarHits.length; i++) {
    if (t - bb7EdgarHits[i] < windowMs) keep.push(bb7EdgarHits[i]);
  }
  bb7EdgarHits = keep;
  if (bb7EdgarHits.length >= limit) return { ok: false, wait: Math.max(1, windowMs - (t - bb7EdgarHits[0])) };
  bb7EdgarHits.push(t);
  return { ok: true, wait: 0 };
}
function bb7Sleep(ms) {
  try {
    if (typeof globalThis.bb7SleepHook === "function") return Promise.resolve(globalThis.bb7SleepHook(ms));
  } catch (e) {}
  return new Promise(function (resolve) {
    var timer = setTimeout(resolve, ms);
    if (timer && timer.unref) timer.unref();
  });
}
async function bb7Pace() {
  for (var n = 0; n < 6; n++) {
    var slot = bb7TakeToken(bb7Now());
    if (slot.ok) return;
    await bb7Sleep(Math.min(slot.wait, 1100));
  }
  var last = bb7TakeToken(bb7Now());
  if (!last.ok) throw new Error("EDGAR pace");
}
function bb7CacheFile() {
  try {
    if (typeof __dirname !== "string" || !__dirname) return "";
    return require("path").join(__dirname, "data-cache", "bb7-insiders.json");
  } catch (e) { return ""; }
}
function bb7DiskLoad() {
  var file = bb7CacheFile();
  if (!file) return;
  try {
    var saved = JSON.parse(require("fs").readFileSync(file, "utf8"));
    var entries = saved && saved.entries || [];
    for (var i = 0; i < entries.length; i++) {
      var row = entries[i];
      if (!row || !row.k || row.body == null) continue;
      bb7Mem.set(row.k, { at: Number(row.at) || 0, ttl: Number(row.ttl) || bb7FormTtl, body: row.body });
    }
  } catch (e) {}
}
function bb7DiskSave() {
  var file = bb7CacheFile();
  if (!file) return;
  try {
    var fs = require("fs");
    var path = require("path");
    var entries = [];
    bb7Mem.forEach(function (row, key) {
      if (!row || String(key).indexOf("pdf:") === 0) return;
      entries.push({ k: key, at: row.at, ttl: row.ttl, body: row.body });
    });
    var out = JSON.stringify({ v: 1, savedAt: new Date(bb7Now()).toISOString(), entries: entries });
    while (out.length > 1800000 && entries.length > 1) { entries.pop(); out = JSON.stringify({ v: 1, savedAt: new Date(bb7Now()).toISOString(), entries: entries }); }
    fs.mkdirSync(path.dirname(file), { recursive: true });
    var tmp = file + ".tmp-" + process.pid;
    fs.writeFileSync(tmp, out);
    fs.renameSync(tmp, file);
  } catch (e) {}
}
function bb7EnsureDisk() {
  if (bb7DiskReady) return;
  bb7DiskReady = true;
  bb7DiskLoad();
}
function bb7Remember(key, body, ttl, now) {
  bb7EnsureDisk();
  bb7Mem.delete(key);
  bb7Mem.set(key, { at: now == null ? bb7Now() : now, ttl: ttl, body: body });
  var form4 = [];
  bb7Mem.forEach(function (_row, k) { if (String(k).indexOf("f4:") === 0) form4.push(k); });
  while (form4.length > 32) bb7Mem.delete(form4.shift());
  bb7DiskSave();
}
function bb7Recall(key) {
  bb7EnsureDisk();
  return bb7Mem.get(key) || null;
}
function bb7Reset() {
  bb7Mem = new Map();
  bb7EdgarHits = [];
  bb7Inflight = new Map();
  bb7DiskReady = true;
}
function bb7Decode(text) {
  return String(text || "")
    .replace(/<!\[CDATA\[|\]\]>/g, "")
    .replace(/&#(\d+);/g, function (_m, n) { return String.fromCharCode(Number(n)); })
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, "\"").replace(/&apos;/g, "'").replace(/&amp;/g, "&");
}
function bb7Tag(xml, tag) {
  var re = new RegExp("<(?:[\\w.-]+:)?" + tag + "(?:\\s[^>]*)?>([\\s\\S]*?)</(?:[\\w.-]+:)?" + tag + ">", "i");
  var m = re.exec(String(xml || ""));
  if (!m) return "";
  var inner = m[1];
  var v = /<(?:[\w.-]+:)?value(?:\s[^>]*)?>([\s\S]*?)<\/(?:[\w.-]+:)?value>/i.exec(inner);
  return bb7Decode(v ? v[1] : inner).replace(/<[^>]+>/g, "").trim();
}
function bb7Blocks(xml, tag) {
  var re = new RegExp("<(?:[\\w.-]+:)?" + tag + "(?:\\s[^>]*)?>[\\s\\S]*?</(?:[\\w.-]+:)?" + tag + ">", "gi");
  return String(xml || "").match(re) || [];
}
function bb7Num(value) {
  var n = Number(String(value || "").replace(/,/g, ""));
  return isFinite(n) ? n : null;
}
function bb7IsoDate(value) {
  var s = String(value || "").trim();
  var iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
  if (iso) return iso[1] + "-" + iso[2] + "-" + iso[3];
  var us = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);
  if (!us) return s;
  var month = ("0" + us[1]).slice(-2);
  var day = ("0" + us[2]).slice(-2);
  return us[3] + "-" + month + "-" + day;
}
function bb7CodeLabel(code) {
  var labels = {
    P: "Open-market purchase", S: "Open-market sale", A: "Grant or award", M: "Exercise or conversion",
    F: "Tax withholding", G: "Gift", D: "Disposition to the issuer", C: "Conversion",
    X: "Exercise of a derivative", I: "Discretionary transaction", J: "Other",
    L: "Small acquisition", W: "Will or inheritance", K: "Equity swap", U: "Tender",
    Z: "Voting trust deposit or withdrawal"
  };
  var key = String(code || "").toUpperCase();
  return labels[key] || key;
}
function bb7Flag(xml, tag) {
  var v = bb7Tag(xml, tag).toLowerCase();
  return v === "1" || v === "true";
}
function bb7Role(xml) {
  var rel = bb7Blocks(xml, "reportingOwnerRelationship")[0] || xml;
  var parts = [];
  if (bb7Flag(rel, "isDirector")) parts.push("director");
  if (bb7Flag(rel, "isOfficer")) parts.push(bb7Tag(rel, "officerTitle") || "officer");
  if (bb7Flag(rel, "isTenPercentOwner")) parts.push("10% owner");
  var other = bb7Flag(rel, "isOther") ? bb7Tag(rel, "otherText") : "";
  if (other) parts.push(other);
  return parts.join(", ");
}
function bb7ParseForm4(xml, meta) {
  meta = meta || {};
  var owner = bb7Tag(xml, "rptOwnerName");
  var role = bb7Role(xml);
  var rows = [];
  var add = function (block, deriv) {
    var shares = bb7Num(bb7Tag(block, "transactionShares"));
    var price = bb7Num(bb7Tag(block, "transactionPricePerShare"));
    var code = bb7Tag(block, "transactionCode").toUpperCase();
    rows.push({
      insiderName: owner,
      insiderRole: role,
      transactionCode: code,
      codeLabel: bb7CodeLabel(code),
      shares: shares,
      price: price,
      value: shares != null && price != null ? Math.round(shares * price * 100) / 100 : null,
      sharesOwnedAfter: bb7Num(bb7Tag(block, "sharesOwnedFollowingTransaction")),
      transactionDate: bb7IsoDate(bb7Tag(block, "transactionDate")),
      filingDate: bb7IsoDate(meta.filingDate || ""),
      acquiredDisposed: bb7Tag(block, "transactionAcquiredDisposedCode").toUpperCase(),
      isDerivative: !!deriv,
      accession: meta.accession || "",
      filingUrl: meta.filingUrl || ""
    });
  };
  bb7Blocks(xml, "nonDerivativeTransaction").forEach(function (block) { add(block, false); });
  bb7Blocks(xml, "derivativeTransaction").forEach(function (block) { add(block, true); });
  return rows;
}
function bb7IsOpenMarket(row) {
  if (!row || row.isDerivative) return false;
  var code = String(row.transactionCode || "").toUpperCase();
  return code === "P" || code === "S";
}
function bb7Pick(rows, opts) {
  var premium = !!(opts && opts.premium);
  var all = premium && opts && opts.codes === "all";
  var list = [];
  var source = rows || [];
  for (var i = 0; i < source.length; i++) {
    if (!all && !bb7IsOpenMarket(source[i])) continue;
    list.push(source[i]);
    if (!premium && list.length >= 5) break;
  }
  return list;
}
function bb7Explainer() {
  return {
    what: "Form 4 is the filing a company insider (director, officer or 10% owner) must make within two business days of trading the company's shares.",
    where: "From SEC EDGAR, the US regulator's public filing system.",
    why: "Open-market purchases (code P) and sales (code S) show what insiders did with their own money. Sales are often routine (tax, diversification, pre-set 10b5-1 plans), and this is a disclosure, not a signal to trade.",
    house: "Members of the US House must report securities trades over $1,000 within 45 days in a Periodic Transaction Report; amounts are disclosed as ranges."
  };
}
function bb7ZipEntries(buf) {
  var b = Buffer.isBuffer(buf) ? buf : Buffer.from(buf);
  var eocd = -1;
  var min = Math.max(0, b.length - 22 - 65536);
  for (var i = b.length - 22; i >= min; i--) {
    if (b.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) return [];
  var p = b.readUInt32LE(eocd + 16);
  var entries = [];
  var zlib = require("zlib");
  while (p + 46 <= b.length && b.readUInt32LE(p) === 0x02014b50) {
    var method = b.readUInt16LE(p + 10);
    var compSize = b.readUInt32LE(p + 20);
    var nameLen = b.readUInt16LE(p + 28);
    var extraLen = b.readUInt16LE(p + 30);
    var commentLen = b.readUInt16LE(p + 32);
    var localOff = b.readUInt32LE(p + 42);
    var name = b.slice(p + 46, p + 46 + nameLen).toString("utf8");
    if (localOff + 30 <= b.length) {
      var localNameLen = b.readUInt16LE(localOff + 26);
      var localExtraLen = b.readUInt16LE(localOff + 28);
      var dataOff = localOff + 30 + localNameLen + localExtraLen;
      var comp = b.slice(dataOff, dataOff + compSize);
      var data = comp;
      if (method === 8) data = zlib.inflateRawSync(comp);
      if (method === 0 || method === 8) entries.push({ name: name, data: data });
    }
    p += 46 + nameLen + extraLen + commentLen;
  }
  return entries;
}
function bb7ParseHouseXml(xml) {
  var blocks = bb7Blocks(String(xml || "").replace(/^\uFEFF/, ""), "Member");
  var out = [];
  for (var i = 0; i < blocks.length; i++) {
    var block = blocks[i];
    if (bb7Tag(block, "FilingType").toUpperCase() !== "P") continue;
    var docId = bb7Tag(block, "DocID");
    var year = bb7Tag(block, "Year");
    var stateDst = bb7Tag(block, "StateDst").toUpperCase();
    var prefix = bb7Tag(block, "Prefix");
    var first = bb7Tag(block, "First");
    var last = bb7Tag(block, "Last");
    var suffix = bb7Tag(block, "Suffix");
    var member = [prefix, first, last, suffix].filter(Boolean).join(" ");
    out.push({
      member: member,
      state: stateDst.slice(0, 2),
      district: stateDst.slice(2),
      filingDate: bb7IsoDate(bb7Tag(block, "FilingDate")),
      docId: docId,
      pdfUrl: "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/" + year + "/" + docId + ".pdf",
      parsed: false,
      note: "See filing"
    });
  }
  out.sort(function (a, b) { return String(b.filingDate).localeCompare(String(a.filingDate)); });
  return out;
}
function bb7PdfString(token) {
  var s = String(token || "");
  s = s.replace(/^\(/, "").replace(/\)\s*Tj$/i, "").replace(/\)$/, "");
  return s.replace(/\\n/g, "\n").replace(/\\r/g, "\r").replace(/\\t/g, "\t").replace(/\\\(/g, "(").replace(/\\\)/g, ")").replace(/\\\\/g, "\\");
}
function bb7PdfOperators(text) {
  var parts = [];
  var tj = /\(((?:\\.|[^\\)])*)\)\s*Tj/g;
  var m;
  while ((m = tj.exec(text))) parts.push(bb7PdfString("(" + m[1] + ")"));
  var array = /\[([\s\S]*?)\]\s*TJ/g;
  while ((m = array.exec(text))) {
    var inner = /\(((?:\\.|[^\\)])*)\)/g;
    var p;
    while ((p = inner.exec(m[1]))) parts.push(bb7PdfString("(" + p[1] + ")"));
  }
  return parts.join("");
}
function bb7PdfText(buf) {
  if (buf == null) return "";
  if (typeof buf === "string") return bb7PdfOperators(buf);
  var b = Buffer.isBuffer(buf) ? buf : Buffer.from(buf);
  var latin = b.toString("latin1");
  var zlib = null;
  try { zlib = require("zlib"); } catch (e) { zlib = null; }
  var out = [];
  var re = /stream\r?\n/g;
  var m;
  while ((m = re.exec(latin))) {
    var end = latin.indexOf("endstream", m.index);
    if (end < 0) break;
    var dict = latin.slice(Math.max(0, m.index - 400), m.index);
    var chunk = b.slice(m.index + m[0].length, end);
    if (chunk.length && chunk[chunk.length - 1] === 0x0a) chunk = chunk.slice(0, chunk.length - 1);
    if (chunk.length && chunk[chunk.length - 1] === 0x0d) chunk = chunk.slice(0, chunk.length - 1);
    var text = "";
    if (/FlateDecode/.test(dict) && zlib) {
      try { text = zlib.inflateSync(chunk).toString("latin1"); } catch (e2) { text = ""; }
    } else text = chunk.toString("latin1");
    var pulled = bb7PdfOperators(text);
    if (pulled) out.push(pulled);
    re.lastIndex = end + 9;
  }
  return out.join("\n").replace(/[ \t]+\n/g, "\n").trim();
}
function bb7PtrLines(text, ticker) {
  var want = String(ticker || "").toUpperCase();
  if (!want) return [];
  var lines = String(text || "").split(/\r?\n/);
  var out = [];
  var word = new RegExp("(^|[^A-Z0-9])" + want.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "([^A-Z0-9]|$)", "i");
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    if (!word.test(line)) continue;
    var amount = line.match(/\$[0-9][0-9,]*(?:\s*[-–]\s*\$[0-9][0-9,]*)?|Over\s+\$[0-9][0-9,]*/i);
    var date = line.match(/\b(\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2})\b/);
    var type = line.match(/(?:^|\s)([PSEX])(?:\s|$)/);
    var owner = line.match(/\b(SP|JT|DC|Self)\b/i);
    var asset = line.split(new RegExp(want, "i"))[0].replace(/[-–|]+/g, " ").trim();
    out.push({
      asset: asset,
      ticker: want,
      type: type ? type[1].toUpperCase() : "",
      date: date ? bb7IsoDate(date[1]) : "",
      amountRange: amount ? amount[0].replace(/\s+/g, " ") : "",
      owner: owner ? owner[1].toUpperCase() : ""
    });
  }
  return out;
}
function bb7PdfTrades(buf, ticker) {
  var text = "";
  try { text = bb7PdfText(buf); } catch (e) { text = ""; }
    if (!/[A-Za-z]{3,}/.test(text || "")) return { parsed: false, note: "See filing", trades: [] };
  return { parsed: true, note: "", trades: bb7PtrLines(text, ticker) };
}
function bb7PdfLibrary() {
  var names = ["pdf-parse", "pdfjs-dist"];
  for (var i = 0; i < names.length; i++) {
    try { require.resolve(names[i]); return names[i]; } catch (e) {}
  }
  return "";
}
function bb7FetchImpl() {
  try {
    if (typeof globalThis.bb7Fetch === "function") return globalThis.bb7Fetch;
  } catch (e) {}
  return typeof fetch === "function" ? fetch : null;
}
async function bb7FetchBuf(url, pace) {
  if (pace !== false && /sec\.gov/i.test(url)) await bb7Pace();
  var fetchImpl = bb7FetchImpl();
  if (!fetchImpl) throw new Error("no fetch");
  var res = await fetchImpl(url, { headers: bb7Headers(), redirect: "follow", signal: AbortSignal.timeout(15000) });
  if (!res || res.ok === false) {
    var err = new Error("HTTP " + (res && res.status));
    err.status = res && res.status;
    throw err;
  }
  var buf;
  if (typeof res.arrayBuffer === "function") buf = Buffer.from(await res.arrayBuffer());
  else buf = Buffer.from(String(await res.text()));
  if (buf.length > 2 && buf[0] === 0x1f && buf[1] === 0x8b) buf = require("zlib").gunzipSync(buf);
  return buf;
}
function bb7Archive(cik, accession, doc) {
  var acc = String(accession || "").replace(/-/g, "");
  var parts = String(doc || "").split("/").filter(Boolean).map(encodeURIComponent);
  return "https://www.sec.gov/Archives/edgar/data/" + Number(cik) + "/" + acc + "/" + parts.join("/");
}
function bb7IndexUrl(cik, accession) {
  var acc = String(accession || "").replace(/-/g, "");
  return "https://www.sec.gov/Archives/edgar/data/" + Number(cik) + "/" + acc + "/" + accession + "-index.html";
}
function bb7TickerKeys(symbol) {
  var s = String(symbol || "").trim().toUpperCase().replace(/^\$/, "");
  var keys = [s];
  if (s.indexOf(".") >= 0) keys.push(s.replace(/\./g, "-"));
  if (s.indexOf("-") >= 0) keys.push(s.replace(/-/g, "."));
  return keys;
}
async function bb7TickerMap(now) {
  var row = bb7Recall("map:tickers");
  if (row && now - row.at <= bb7HouseTtl) return row.body;
  var buf = await bb7FetchBuf("https://www.sec.gov/files/company_tickers.json");
  var json = JSON.parse(buf.toString("utf8"));
  var byTicker = {};
  Object.keys(json || {}).forEach(function (key) {
    var item = json[key];
    var symbol = String(item && item.ticker || "").toUpperCase();
    if (!symbol || !Number.isFinite(Number(item.cik_str))) return;
    var rec = { cik: String(item.cik_str).padStart(10, "0"), company: String(item.title || "") };
    byTicker[symbol] = rec;
    if (symbol.indexOf("-") >= 0) byTicker[symbol.replace(/-/g, ".")] = rec;
  });
  bb7Remember("map:tickers", byTicker, bb7HouseTtl, now);
  return byTicker;
}
function bb7Lookup(map, ticker) {
  if (!map) return null;
  var keys = bb7TickerKeys(ticker);
  for (var i = 0; i < keys.length; i++) if (map[keys[i]]) return map[keys[i]];
  return null;
}
function bb7FormList(submission) {
  var recent = submission && submission.filings && submission.filings.recent || {};
  var forms = recent.form || [];
  var out = [];
  for (var i = 0; i < forms.length; i++) {
    var form = String(forms[i] || "");
    if (form !== "4" && form !== "4/A") continue;
    out.push({
      form: form,
      filingDate: recent.filingDate ? recent.filingDate[i] : "",
      accession: recent.accessionNumber ? recent.accessionNumber[i] : "",
      primary: recent.primaryDocument ? recent.primaryDocument[i] : ""
    });
  }
  return out;
}
async function bb7FormXml(cik, filing) {
  var url = bb7Archive(cik, filing.accession, filing.primary);
  var buf = await bb7FetchBuf(url);
  var text = buf.toString("utf8");
  if (text.indexOf("ownershipDocument") >= 0) return text;
  var indexUrl = bb7Archive(cik, filing.accession, "index.json");
  var index = JSON.parse((await bb7FetchBuf(indexUrl)).toString("utf8"));
  var items = index && index.directory && index.directory.item || [];
  var name = "";
  for (var i = 0; i < items.length; i++) {
    var itemName = String(items[i] && items[i].name || "");
    if (/\.xml$/i.test(itemName) && !/primary_doc/i.test(itemName)) { name = itemName; break; }
  }
  if (!name) return text;
  return (await bb7FetchBuf(bb7Archive(cik, filing.accession, name))).toString("utf8");
}
async function bb7FetchForm4(ticker, mode, now) {
  var map = await bb7TickerMap(now);
  var hit = bb7Lookup(map, ticker);
  if (!hit) return { unknown: true };
  var subUrl = "https://data.sec.gov/submissions/CIK" + hit.cik + ".json";
  var submission = JSON.parse((await bb7FetchBuf(subUrl)).toString("utf8"));
  var filings = bb7FormList(submission);
  var rows = [];
  var open = 0;
  var used = 0;
  var company = hit.company || submission.name || "";
  for (var i = 0; i < filings.length && used < 40; i++) {
    used++;
    var filing = filings[i];
    var meta = { filingDate: filing.filingDate, accession: filing.accession, filingUrl: bb7IndexUrl(hit.cik, filing.accession) };
    var parsed = [];
    try { parsed = bb7ParseForm4(await bb7FormXml(hit.cik, filing), meta); } catch (e) { parsed = []; }
    for (var j = 0; j < parsed.length; j++) {
      rows.push(parsed[j]);
      if (bb7IsOpenMarket(parsed[j])) open++;
    }
    if (mode !== "full" && open >= 5) break;
  }
  if (!company && submission && submission.name) company = submission.name;
  var complete = used >= filings.length || used >= 40;
  return {
    unknown: false,
    ticker: bb7TickerKeys(ticker)[0],
    cik: hit.cik,
    company: company,
    rows: rows,
    complete: complete,
    filings: filings.length
  };
}
async function bb7Form4(ticker, mode, now) {
  var key = "f4:" + bb7TickerKeys(ticker)[0];
  var cached = bb7Recall(key);
  var fresh = cached && now - cached.at <= cached.ttl;
  if (fresh && cached.body && (mode !== "full" || cached.body.complete)) return Object.assign({ stale: false, asOf: new Date(cached.at).toISOString() }, cached.body);
  var flight = "f4-flight:" + key + ":" + mode;
  if (bb7Inflight.has(flight)) return bb7Inflight.get(flight);
  var job = (async function () {
    var pack = await bb7FetchForm4(ticker, mode, now);
    if (!pack.unknown) bb7Remember(key, pack, bb7FormTtl, now);
    return Object.assign({ stale: false, asOf: new Date(now).toISOString() }, pack);
  })();
  bb7Inflight.set(flight, job);
  try { return await job; }
  finally { bb7Inflight.delete(flight); }
}
async function bb7HouseIndex(now) {
  var cached = bb7Recall("house:index");
  if (cached && now - cached.at <= cached.ttl) return { stale: false, asOf: new Date(cached.at).toISOString(), items: cached.body };
  var year = new Date(now).getUTCFullYear();
  var years = [year, year - 1];
  var items = [];
  var failed = 0;
  for (var i = 0; i < years.length; i++) {
    try {
      var buf = await bb7FetchBuf("https://disclosures-clerk.house.gov/public_disc/financial-pdfs/" + years[i] + "FD.zip", false);
      var entries = bb7ZipEntries(buf);
      var xml = "";
      for (var j = 0; j < entries.length; j++) if (/\.xml$/i.test(entries[j].name)) xml = entries[j].data.toString("utf8");
      items = items.concat(bb7ParseHouseXml(xml));
    } catch (e) { failed++; }
  }
  if (!items.length && cached) return { stale: true, asOf: new Date(cached.at).toISOString(), items: cached.body };
  if (!items.length) {
    var err = new Error("House index unavailable");
    err.house = true;
    if (failed) throw err;
  }
  var seen = {};
  var unique = [];
  for (var u = 0; u < items.length; u++) {
    var id = items[u].pdfUrl || items[u].docId;
    if (seen[id]) continue;
    seen[id] = 1;
    unique.push(items[u]);
  }
  items = unique;
  items.sort(function (a, b) { return String(b.filingDate).localeCompare(String(a.filingDate)); });
  bb7Remember("house:index", items, bb7HouseTtl, now);
  return { stale: false, asOf: new Date(now).toISOString(), items: items };
}
function bb7HouseView(index) {
  var items = (index && index.items || []).slice(0, 40).map(function (item) {
    return {
      member: item.member, state: item.state, district: item.district, filingDate: item.filingDate,
      docId: item.docId, pdfUrl: item.pdfUrl, parsed: false, note: "See filing"
    };
  });
  var lib = "";
  try { lib = bb7PdfLibrary(); } catch (e) { lib = ""; }
  var note = lib
    ? "Periodic Transaction Reports that mention this ticker are parsed from the PDF text layer. Unreadable filings stay marked See filing."
    : "No PDF text library is installed, so each Periodic Transaction Report is listed with its link and marked See filing.";
  return { items: items, asOf: index ? index.asOf : "", note: note };
}
function bb7Shape(pack, opts) {
  var premium = !!(opts && opts.premium);
  var codes = premium && opts && opts.codes === "all" ? "all" : "PS";
  var insider = pack && pack.rows ? bb7Pick(pack.rows, { premium: premium, codes: codes }) : [];
  var meta = { limited: !premium, count: insider.length, codes: codes };
  if (!premium) meta.upgrade = "premium";
  var body = {
    ticker: pack.ticker,
    cik: pack.cik || "",
    company: pack.company || "",
    asOf: pack.asOf || "",
    stale: !!pack.stale,
    source: { name: "SEC EDGAR", url: "https://www.sec.gov/edgar" },
    explainer: bb7Explainer(),
    insider: insider,
    house: opts && opts.house && premium ? (opts.houseBody || null) : null,
    meta: meta
  };
  if (!insider.length) body.note = pack && pack.filings === 0 ? "No Form 4 filings for this ticker." : (pack && pack.note || "");
  if (body.note === "") delete body.note;
  return body;
}
function bb7Unavailable() {
  return {
    status: 200,
    body: { unavailable: true, message: "Insider filings unavailable right now" },
    headers: { "X-Dispatch-Data-Status": "unavailable" }
  };
}
function bb7StaleResult(pack, opts) {
  var body = bb7Shape(Object.assign({}, pack, { stale: true }), opts);
  var headers = { "X-Dispatch-Data-Status": "stale" };
  if (body.asOf) headers["X-Dispatch-As-Of"] = String(body.asOf);
  return { status: 200, body: body, headers: headers };
}
async function bb7Load(ticker, opts) {
  var now = bb7Now();
  var mode = opts && opts.premium ? "full" : "free";
  var key = "f4:" + bb7TickerKeys(ticker)[0];
  try {
    var pack = await bb7Form4(ticker, mode, now);
    if (pack.unknown) return { status: 404, body: { error: "Unknown ticker." }, headers: {} };
    var houseBody = null;
    if (opts && opts.house && opts.premium) {
      try { houseBody = bb7HouseView(await bb7HouseIndex(now)); }
      catch (e) {
        var old = bb7Recall("house:index");
        if (old) houseBody = bb7HouseView({ items: old.body, asOf: new Date(old.at).toISOString() });
        else houseBody = { items: [], asOf: "", note: "House disclosures are temporarily unavailable." };
      }
    }
    var fresh = bb7Shape(pack, { premium: !!opts.premium, codes: opts && opts.codes, house: !!(opts && opts.house), houseBody: houseBody });
    var headers = { "X-Dispatch-Data-Status": pack.stale ? "stale" : "fresh" };
    if (pack.stale && fresh.asOf) headers["X-Dispatch-As-Of"] = String(fresh.asOf);
    return { status: 200, body: fresh, headers: headers };
  } catch (e) {
    var cached = bb7Recall(key);
    if (cached && cached.body) return bb7StaleResult(Object.assign({ asOf: new Date(cached.at).toISOString() }, cached.body), opts || {});
    return bb7Unavailable();
  }
}
async function bb7Route(req, res, url) {
  if (!req || req.method !== "GET") return json(res, 405, { error: "Method not allowed." });
  var ticker = bb7TickerKeys(url.searchParams.get("t") || "")[0];
  if (!ticker || !/^[A-Z][A-Z0-9.-]{0,9}$/.test(ticker)) return json(res, 400, { error: "Ticker required." });
  var user = null;
  try { user = await currentUser(req); } catch (e) { user = null; }
  var premium = bb7Premium(user);
  var out = await bb7Load(ticker, {
    premium: premium,
    codes: premium && url.searchParams.get("codes") === "all" ? "all" : "PS",
    house: premium && url.searchParams.get("house") === "1"
  });
  return json(res, out.status, out.body, out.headers || {});
}
// BB7_JS_END

"""

declared = re.findall(r"(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb7")]
if bad:
    die("bb7 block declares a non-bb7 function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb7 block repeats a function: %s" % ", ".join(dupes))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK:
    die("bb7 block has a forbidden declaration")

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
    print("bb7 app.js untouched")
if idx_before is not None:
    show("after", "index.html", idx_before)
    print("bb7 index.html untouched")
if chat_n is not None:
    print("index chat%d unchanged" % chat_n)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb7bak"
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
print("APPLY bb7 insiders")
