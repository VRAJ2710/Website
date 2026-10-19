#!/usr/bin/env python3
"""patch_bb8.py — Ask conclusion, NTM forward P/E, delay wording, insiders window,
cold-cache wait and House label. Server.js only.
Stacked on bb7 (server md5 e10bf8fdeb7f9c7f3265ab2a0e0ec549). Does not rewrite
app.js or index.html and does not bump the client cache token.
1) Ask peer answers: a "cannot compare" dead end after comparisons is replaced by a
   conclusion built from the precomputed FACT lines; peers with no figure are named.
2) Forward P/E: Yahoo forwardPE = price / epsForward, and epsForward is the NEXT fiscal
   year consensus (+1y), so NVDA used FY Jan-2028 EPS and MU FY Aug-2028 EPS. Replaced by
   price / next-12-month consensus EPS (0y and +1y weighted by days left in the year).
3) Quote notes read "delayed N min by exchange".
4) /api/insiders meta.window labels the scanned span ("Last 6 months"); premium can page
   older filings with before=YYYY-MM-DD. Form 4 XML is read in one EDGAR request per
   filing (was three), so a default load costs fewer EDGAR calls than bb7.
5) /api/insiders waits up to 8s for EDGAR on a cold cache, then returns the rows loaded
   so far (meta.partial) before falling back to unavailable. 10/s token bucket kept.
6) House list is labelled "Latest House trade filings (all members)".
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "e10bf8fdeb7f9c7f3265ab2a0e0ec549",
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
    print("bb8 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8 before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8 %s untouched" % label)

if "// \u2500\u2500 bb8 \u2500\u2500" in v:
    print("REFUSE: bb8 already applied")
    sys.exit(0)

# (old, new, expected count)
EDITS = [
    ("delay note", '"delayed " + delay + "m by exchange"', '"delayed " + delay + " min by exchange"', 4),
    ("rt32 modules", 'majorHoldersBreakdown,price";', 'majorHoldersBreakdown,price,earningsTrend";', 1),
    ("rt32 forwardPe", 'forwardPe: rt32R(sd.forwardPE) || rt32R(ks.forwardPE),',
     'forwardPe: bb8Rt32Forward(y, rt32R(fd.currentPrice) || rt32R(pr.regularMarketPrice), sym), forwardBasis: "next 12 months (consensus EPS)",', 1),
    ("rt41s label", '\u00b7 forward P/E ${f(v.forwardPe)}', '\u00b7 forward P/E (next 12 months) ${f(v.forwardPe)}', 1),
    ("bb2One label", 'const label = basis === "trailing" ? "trailing P/E (TTM)" : "forward P/E";',
     'const label = basis === "trailing" ? "trailing P/E (TTM)" : "forward P/E (next 12 months)";', 1),
    ("bb2 facts row", '" | forward P/E " + f + px + asOf;',
     '" | forward P/E (next 12 months) " + f + (typeof bb8EpsNote === "function" ? bb8EpsNote(v) : "") + px + asOf;', 1),
    ("bb2Summary modules", '?modules=price,summaryDetail,defaultKeyStatistics&crumb=', '?modules=price,summaryDetail,defaultKeyStatistics,earningsTrend&crumb=', 1),
    ("bb2Summary forward",
     'forward: bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.forwardPE) != null ? bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.forwardPE) : bb2Num(r.summaryDetail && r.summaryDetail.forwardPE),',
     'forward: bb8SummaryForward(r, sym), epsTtm: bb2Num(r.defaultKeyStatistics && r.defaultKeyStatistics.trailingEps), epsNtm: (bb8NtmGet(sym) || {}).epsNtm || null,', 1),
    ("bb7FormXml raw primary",
     '  var url = bb7Archive(cik, filing.accession, filing.primary);\n  var buf = await bb7FetchBuf(url);\n',
     '  var url = bb7Archive(cik, filing.accession, bb8RawPrimary(filing.primary));\n  var buf;\n  try { buf = await bb7FetchBuf(url); }\n  catch (bb8e) { if (bb8RawPrimary(filing.primary) === String(filing.primary || "")) throw bb8e; url = bb7Archive(cik, filing.accession, filing.primary); buf = await bb7FetchBuf(url); }\n', 1),
    ("bb7FetchForm4 progress",
     '  var company = hit.company || submission.name || "";\n  for (var i = 0; i < filings.length && used < 40; i++) {\n',
     '  var company = hit.company || submission.name || "";\n  bb8Track(ticker, mode, { rows: rows, cik: hit.cik, company: company, list: filings, scanned: function () { return used; } });\n  for (var i = 0; i < filings.length && used < 40; i++) {\n', 1),
    ("bb7FetchForm4 window",
     '    complete: complete,\n    filings: filings.length\n  };\n',
     '    complete: complete,\n    filings: filings.length,\n    scanned: used,\n    newestFiling: filings.length ? filings[0].filingDate : "",\n    oldestFiling: used ? filings[used - 1].filingDate : ""\n  };\n', 1),
]

miss = []
if "// \u2500\u2500 bb7 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // \u2500\u2500 bb7 \u2500\u2500")
for name, old, new, want in EDITS:
    n = v.count(old)
    if n != want:
        miss.append("anchor %s matched %d times (want %d)" % (name, n, want))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)
for name, old, new, want in EDITS:
    v = v.replace(old, new)
    print("bb8 edit %s x%d" % (name, want))

BLOCK = r"""
// ── bb8 ── Ask conclusion, NTM forward P/E, delay wording, insiders window + cold-cache wait, House label.
// BB8_JS
// Forward P/E: Yahoo forwardPE = price / epsForward, and epsForward is the consensus for the NEXT
// fiscal year (earningsTrend "+1y"), not the next twelve months. bb8 uses a time-weighted NTM EPS
// (current-year "0y" and "+1y" consensus, weighted by days left in the current fiscal year).
var bb8Ntm = new Map();
var bb8NtmTtl = 12 * 60 * 60 * 1000;
var bb8NtmInflight = new Map();
var bb8Made = [];
var bb8Progress = new Map();
var bb8MapFlight = null;
var BB8_FWD_LABEL = "forward P/E (next 12 months)";
var BB8_HOUSE_LABEL = "Latest House trade filings (all members)";
function bb8Raw(v) {
  if (v && typeof v === "object") v = v.raw != null ? v.raw : null;
  var n = Number(v);
  return v != null && v !== "" && isFinite(n) ? n : null;
}
function bb8Key(sym) { return String(sym || "").toUpperCase().replace(/-/g, "."); }
function bb8NtmFromTrend(trend, now) {
  var list = Array.isArray(trend) ? trend : [];
  var y0 = null, y1 = null;
  for (var i = 0; i < list.length; i++) {
    var t = list[i];
    if (!t) continue;
    if (t.period === "0y") y0 = t;
    if (t.period === "+1y") y1 = t;
  }
  if (!y0 || !y1) return null;
  var e0 = bb8Raw(y0.earningsEstimate && y0.earningsEstimate.avg);
  var e1 = bb8Raw(y1.earningsEstimate && y1.earningsEstimate.avg);
  var end0 = Date.parse(String(y0.endDate || "") + "T23:59:59Z");
  if (e0 == null || e1 == null || !isFinite(end0)) return null;
  var t0 = now == null ? Date.now() : now;
  var left = (end0 - t0) / (365.25 * 86400000);
  var w = left <= 0 ? 0 : (left >= 1 ? 1 : left);
  var ntm = w * e0 + (1 - w) * e1;
  return { eps0: e0, eps1: e1, end0: String(y0.endDate || ""), end1: String(y1.endDate || ""), weight: Math.round(w * 1000) / 1000, epsNtm: Math.round(ntm * 10000) / 10000, at: t0 };
}
function bb8NtmRemember(sym, info) {
  if (!info) return null;
  bb8Ntm.set(bb8Key(sym), info);
  if (bb8Ntm.size > 400) bb8Ntm.delete(bb8Ntm.keys().next().value);
  return info;
}
function bb8NtmGet(sym, now) {
  var hit = bb8Ntm.get(bb8Key(sym));
  if (!hit) return null;
  var t = now == null ? Date.now() : now;
  return t - hit.at <= bb8NtmTtl ? hit : null;
}
function bb8ForwardFrom(price, info) {
  var px = Number(price);
  if (!info || !(info.epsNtm > 0) || !(px > 0)) return null;
  var pe = px / info.epsNtm;
  return pe > 0 && pe < 1000 ? Math.round(pe * 100) / 100 : null;
}
function bb8ApplyNtm(sym, v) {
  if (!v || typeof v !== "object") return v;
  var info = bb8NtmGet(sym);
  v.forward = bb8ForwardFrom(v.price, info);
  v.forwardBasis = v.forward != null ? "NTM consensus" : "";
  v.epsNtm = v.forward != null ? info.epsNtm : null;
  return v;
}
async function bb8NtmFetch(sym) {
  var key = bb8Key(sym);
  if (bb8NtmInflight.has(key)) return bb8NtmInflight.get(key);
  var job = (async function () {
    if (typeof bb2Crumb !== "function" || typeof bb2Fetch !== "function") return null;
    var gate = await bb2Crumb();
    var url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/" + encodeURIComponent(key.replace(/\./g, "-")) + "?modules=earningsTrend&crumb=" + encodeURIComponent(gate.crumb);
    var res = await bb2Fetch(url, { headers: bb2Hdr(gate.cookie), signal: AbortSignal.timeout(2500) });
    if (!res || !res.ok) return null;
    var j = await res.json();
    var r = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
    return bb8NtmRemember(key, bb8NtmFromTrend(r && r.earningsTrend && r.earningsTrend.trend));
  })();
  bb8NtmInflight.set(key, job);
  try { return await job; } catch (e) { return null; } finally { bb8NtmInflight.delete(key); }
}
async function bb8NtmEnsure(list) {
  var want = (list || []).filter(function (s) { return s && !bb8NtmGet(s); });
  if (!want.length) return;
  await Promise.all(want.map(function (s) { return bb8NtmFetch(s).catch(function () { return null; }); }));
}
function bb8SummaryForward(r, sym) {
  var info = bb8NtmRemember(sym, bb8NtmFromTrend(r && r.earningsTrend && r.earningsTrend.trend));
  return bb8ForwardFrom(bb8Raw(r && r.price && r.price.regularMarketPrice), info);
}
function bb8Rt32Forward(y, price, sym) {
  var info = bb8NtmFromTrend(y && y.earningsTrend && y.earningsTrend.trend);
  if (info && sym) bb8NtmRemember(sym, info);
  return bb8ForwardFrom(price, info);
}
function bb8EpsNote(v) {
  if (!v || !(v.epsTtm > 0) || !(v.epsNtm > 0)) return "";
  return " | EPS TTM $" + Number(v.epsTtm).toFixed(2) + ", next-12-month consensus EPS $" + Number(v.epsNtm).toFixed(2);
}
// Ask conclusion: replace "cannot compare" dead ends with a conclusion built from the FACT lines.
function bb8DeadEndRe() {
  return /[^.!?\n]*?(?:\b(?:cannot|can ?not|can't|could not|couldn't|unable to|not (?:possible|able|feasible) to|impossible to|difficult to|hard to|no way to)\b[^.!?\n]{0,60}?\bcompar\w*|\b(?:no|a) (?:direct |meaningful |like-for-like )?comparison (?:is|was|can be) (?:not )?(?:possible|available|feasible|made)\b|\binsufficient (?:data|information) to compar\w*)[^.!?\n]*[.!?]?/i;
}
function bb8IsDeadEnd(text) { return bb8DeadEndRe().test(String(text || "")); }
function bb8Join(list) {
  if (list.length <= 1) return list.join("");
  return list.slice(0, -1).join(", ") + " and " + list[list.length - 1];
}
function bb8Conclusion(facts) {
  var list = Array.isArray(facts) ? facts.filter(Boolean) : [];
  var base = "";
  var parts = [];
  var missing = [];
  ["trailing", "forward"].forEach(function (basis) {
    var lower = [], higher = [], level = [], label = "";
    list.forEach(function (f) {
      if (f.basis !== basis) return;
      if (!base && f.a) base = f.a;
      if (f.dir === "missing") {
        var who = String(f.sentence || "").split(" ")[0];
        var lab = basis === "trailing" ? "trailing P/E (TTM)" : BB8_FWD_LABEL;
        if (who) missing.push(who + " " + lab);
        return;
      }
      label = f.label || label;
      if (f.dir === "lower") lower.push(f.b);
      else if (f.dir === "higher") higher.push(f.b);
      else if (f.dir === "in line") level.push(f.b);
    });
    var bits = [];
    if (lower.length) bits.push("lower than " + bb8Join(lower));
    if (higher.length) bits.push("higher than " + bb8Join(higher));
    if (level.length) bits.push("in line with " + bb8Join(level));
    if (bits.length) parts.push("its " + (label || (basis === "trailing" ? "trailing P/E (TTM)" : BB8_FWD_LABEL)) + " is " + bb8Join(bits));
  });
  if (!parts.length || !base) return "";
  var out = "In short, on the figures shown, " + base + "'s " + parts.join(", and ").replace(/^its /, "") + ".";
  var uniq = [];
  missing.forEach(function (m) { if (uniq.indexOf(m) < 0) uniq.push(m); });
  if (uniq.length) out += " " + bb8Join(uniq) + (uniq.length === 1 ? " was" : " were") + " not reported, so the conclusion on that basis rests on the other peers.";
  return out;
}
function bb8Remember(line) {
  if (!line) return;
  if (bb8Made.indexOf(line) < 0) bb8Made.push(line);
  while (bb8Made.length > 200) bb8Made.shift();
}
function bb8FixConclusion(text, facts) {
  var s = String(text == null ? "" : text);
  var list = Array.isArray(facts) ? facts : [];
  if (!list.some(function (f) { return f && f.dir && f.dir !== "missing"; })) return s;
  if (!bb8IsDeadEnd(s)) return s;
  var done = false;
  var re = new RegExp(bb8DeadEndRe().source, "gi");
  var out = s.replace(re, function (m) {
    var lead = (m.match(/^\s*/) || [""])[0];
    if (done) return "";
    done = true;
    var c = bb8Conclusion(list);
    if (!c) return m;
    bb8Remember(c);
    return (lead ? "\n\n" : "") + c;
  });
  return out.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n");
}
function bb8Protected(line) { return bb8Made.indexOf(String(line || "").trim()) >= 0; }
function bb8HoldExtra(text) {
  return /\b(conclu\w*|overall|in (?:short|summary|sum)|to sum\w*|while|whilst|although|though|however|cannot|can ?not|can't|unable|impossible|difficult|compar\w*|directly|insufficient)\b/i.test(String(text || ""));
}
function bb8AskRule() {
  return "Finish with one short concluding sentence that agrees with the peer comparison lines already shown, saying on each basis which peers the company is above or below. Never say the company cannot be compared with its peers when comparison lines exist. If a peer's figure is not reported, name that peer and conclude from the others. Forward P/E here uses next-12-month consensus EPS. No buy or sell call and no price target.";
}
// Insiders: window label, cold-cache wait, older-page cursor, House label.
function bb8RawPrimary(primary) { return String(primary || "").replace(/^xsl[^/]*\//i, ""); }
function bb8Budget() {
  try {
    var n = Number(globalThis.bb8InsidersBudgetMs);
    if (isFinite(n) && n > 0) return n;
  } catch (e) {}
  return 8000;
}
function bb8Track(ticker, mode, info) {
  var key = bb7TickerKeys(ticker)[0] + ":" + mode;
  bb8Progress.set(key, info);
  if (bb8Progress.size > 64) bb8Progress.delete(bb8Progress.keys().next().value);
}
function bb8Day(s) { var t = Date.parse(String(s || "").slice(0, 10) + "T00:00:00Z"); return isFinite(t) ? t : null; }
function bb8WindowLabel(from, to) {
  var a = bb8Day(from), b = bb8Day(to);
  if (a == null || b == null || b < a) return "";
  var days = Math.round((b - a) / 86400000);
  if (days < 45) { var w = Math.max(1, Math.round(days / 7)); return "Last " + w + (w === 1 ? " week" : " weeks"); }
  var m = Math.max(2, Math.round(days / 30.44));
  if (m >= 12 && m % 12 === 0) return "Last " + (m / 12) + (m === 12 ? " year" : " years");
  return "Last " + m + " months";
}
function bb8Window(pack, premium) {
  if (!premium) return { label: "Latest 5 open-market trades", premiumOnly: false };
  var rows = (pack && pack.rows) || [];
  var dates = rows.map(function (r) { return r && r.filingDate; }).filter(Boolean).sort();
  var from = (pack && pack.oldestFiling) || dates[0] || "";
  var to = (pack && pack.newestFiling) || dates[dates.length - 1] || "";
  var scanned = pack && pack.scanned != null ? pack.scanned : null;
  var more = !!(pack && pack.filings != null && scanned != null && scanned < pack.filings);
  var win = { label: bb8WindowLabel(from, to) || "Latest filings", from: from, to: to, filings: scanned, more: more };
  if (more && from) win.next = "before=" + from;
  return win;
}
function bb8Partial(ticker, mode, opts) {
  var key = bb7TickerKeys(ticker)[0];
  var prog = bb8Progress.get(key + ":" + mode);
  if (!prog || !prog.rows || !prog.rows.length) return null;
  var scanned = typeof prog.scanned === "function" ? prog.scanned() : 0;
  var list = prog.list || [];
  var pack = {
    ticker: key, cik: prog.cik || "", company: prog.company || "", rows: prog.rows.slice(), complete: false,
    filings: list.length, scanned: scanned, newestFiling: list.length ? list[0].filingDate : "",
    oldestFiling: scanned && list[scanned - 1] ? list[scanned - 1].filingDate : "", stale: false, asOf: new Date(bb7Now()).toISOString()
  };
  var houseBody = null;
  if (opts && opts.house && opts.premium) {
    var old = bb7Recall("house:index");
    houseBody = old ? bb7HouseView({ items: old.body, asOf: new Date(old.at).toISOString() }) : { items: [], asOf: "", note: "House filings are still loading. Try again in a moment." };
  }
  var body = bb7Shape(pack, { premium: !!(opts && opts.premium), codes: opts && opts.codes, house: !!(opts && opts.house), houseBody: houseBody });
  body.meta.partial = true;
  body.note = "Showing the filings loaded so far. Refresh in a few seconds for the full list.";
  return { status: 200, body: body, headers: { "X-Dispatch-Data-Status": "partial" } };
}
function bb8Late(ms) {
  return new Promise(function (resolve) {
    var t = setTimeout(function () { resolve("bb8-late"); }, ms);
    if (t && t.unref) t.unref();
  });
}
async function bb8Older(ticker, before, opts) {
  var now = bb7Now();
  var key = "f4:" + bb7TickerKeys(ticker)[0] + "<" + before + ":" + (opts.codes === "all" ? "all" : "PS");
  var cached = bb7Recall(key);
  var pack = cached && now - cached.at <= cached.ttl ? cached.body : null;
  if (!pack) {
    var map = await bb7TickerMap(now);
    var hit = bb7Lookup(map, ticker);
    if (!hit) return { status: 404, body: { error: "Unknown ticker." }, headers: {} };
    var submission = JSON.parse((await bb7FetchBuf("https://data.sec.gov/submissions/CIK" + hit.cik + ".json")).toString("utf8"));
    var all = bb7FormList(submission);
    var filings = all.filter(function (f) { return String(f.filingDate || "") < before; });
    var rows = [], used = 0;
    for (var i = 0; i < filings.length && used < 40; i++) {
      used++;
      var meta = { filingDate: filings[i].filingDate, accession: filings[i].accession, filingUrl: bb7IndexUrl(hit.cik, filings[i].accession) };
      try { rows = rows.concat(bb7ParseForm4(await bb7FormXml(hit.cik, filings[i]), meta)); } catch (e) {}
    }
    pack = {
      unknown: false, ticker: bb7TickerKeys(ticker)[0], cik: hit.cik, company: hit.company || submission.name || "", rows: rows,
      complete: true, filings: filings.length, scanned: used,
      newestFiling: filings.length ? filings[0].filingDate : "", oldestFiling: used ? filings[used - 1].filingDate : ""
    };
    bb7Remember(key, pack, bb7FormTtl, now);
  }
  var body = bb7Shape(Object.assign({ stale: false, asOf: new Date(cached ? cached.at : now).toISOString() }, pack), { premium: true, codes: opts.codes, house: false });
  body.meta.before = before;
  return { status: 200, body: body, headers: { "X-Dispatch-Data-Status": "fresh" } };
}
try {
  if (typeof bb3bRewrite === "function") {
    var bb8Rewrite0 = bb3bRewrite;
    bb3bRewrite = function (text, facts, drop) {
      var src = String(text == null ? "" : text);
      var self = this;
      var out;
      if (bb8Made.length && src.split("\n").some(bb8Protected)) {
        var lines = src.split("\n"), acc = [], chunk = [];
        var flush = function () { if (chunk.length) { acc.push(bb8Rewrite0.call(self, chunk.join("\n"), facts, drop)); chunk = []; } };
        lines.forEach(function (line) { if (bb8Protected(line)) { flush(); acc.push(line); } else chunk.push(line); });
        flush();
        out = acc.join("\n");
      } else out = bb8Rewrite0.call(self, src, facts, drop);
      return bb8FixConclusion(out, facts);
    };
  }
  if (typeof bb3bHold === "function") {
    var bb8Hold0 = bb3bHold;
    bb3bHold = function (text, facts) { return bb8Hold0.call(this, text, facts) || bb8HoldExtra(text); };
  }
  if (typeof bb2System === "function") {
    var bb8System0 = bb2System;
    bb2System = function (body, built, sources) {
      var sys = bb8System0.call(this, body, built, sources);
      return built && Array.isArray(built.facts) && built.facts.length ? sys + "\n\n" + bb8AskRule() : sys;
    };
  }
  if (typeof bb2StoreQuote === "function") {
    var bb8Store0 = bb2StoreQuote;
    bb2StoreQuote = function (row, at) {
      bb8Store0.call(this, row, at);
      try {
        var hit = row && row.symbol && bb2Mem.vals.get(String(row.symbol).toUpperCase());
        if (hit && hit.v) { hit.v.epsTtm = bb2Num(row.epsTrailingTwelveMonths); bb8ApplyNtm(row.symbol, hit.v); }
      } catch (e) {}
    };
  }
  if (typeof bb2Refresh === "function") {
    var bb8Refresh0 = bb2Refresh;
    bb2Refresh = async function (syms) {
      var list = [...new Set((syms || []).map(function (s) { return String(s || "").toUpperCase(); }).filter(Boolean))];
      await Promise.all([bb8Refresh0.call(this, syms), bb8NtmEnsure(list).catch(function () {})]);
      list.forEach(function (s) { var hit = bb2Mem.vals.get(s); if (hit && hit.v) bb8ApplyNtm(s, hit.v); });
    };
  }
  if (typeof bb7TickerMap === "function") {
    var bb8Map0 = bb7TickerMap;
    bb7TickerMap = function (now) {
      var row = bb7Recall("map:tickers");
      if (row && now - row.at <= bb7HouseTtl) return Promise.resolve(row.body);
      if (!bb8MapFlight) bb8MapFlight = bb8Map0.call(this, now).finally(function () { bb8MapFlight = null; });
      return bb8MapFlight;
    };
  }
  if (typeof bb7Shape === "function") {
    var bb8Shape0 = bb7Shape;
    bb7Shape = function (pack, opts) {
      var body = bb8Shape0.call(this, pack, opts);
      try { body.meta.window = bb8Window(pack, !!(opts && opts.premium)); } catch (e) {}
      if (body.house && typeof body.house === "object") { body.house.label = BB8_HOUSE_LABEL; body.house.scope = "all-members"; body.house.tickerFiltered = false; }
      return body;
    };
  }
  if (typeof bb7HouseView === "function") {
    var bb8House0 = bb7HouseView;
    bb7HouseView = function (index) {
      var out = bb8House0.call(this, index);
      out.label = BB8_HOUSE_LABEL;
      out.scope = "all-members";
      out.tickerFiltered = false;
      return out;
    };
  }
  if (typeof bb7Load === "function") {
    var bb8Load0 = bb7Load;
    bb7Load = async function (ticker, opts) {
      var t0 = Date.now();
      var budget = bb8Budget();
      var mode = opts && opts.premium ? "full" : "free";
      var self = this;
      var job = bb8Load0.call(self, ticker, opts);
      var out = await Promise.race([job, bb8Late(budget)]);
      if (out !== "bb8-late" && out && out.body && out.body.unavailable && budget - (Date.now() - t0) > 1500) {
        job = bb8Load0.call(self, ticker, opts);
        out = await Promise.race([job, bb8Late(budget - (Date.now() - t0))]);
      }
      if (out !== "bb8-late") return out;
      job.catch(function () {});
      var cached = bb7Recall("f4:" + bb7TickerKeys(ticker)[0]);
      if (cached && cached.body) return bb7StaleResult(Object.assign({ asOf: new Date(cached.at).toISOString() }, cached.body), opts || {});
      return bb8Partial(ticker, mode, opts) || bb7Unavailable();
    };
  }
  if (typeof bb7Route === "function") {
    var bb8Route0 = bb7Route;
    bb7Route = async function (req, res, url) {
      var before = url && url.searchParams ? String(url.searchParams.get("before") || "") : "";
      if (!before || !req || req.method !== "GET") return bb8Route0.apply(this, arguments);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(before)) return json(res, 400, { error: "before must be YYYY-MM-DD." });
      var ticker = bb7TickerKeys(url.searchParams.get("t") || "")[0];
      if (!ticker || !/^[A-Z][A-Z0-9.-]{0,9}$/.test(ticker)) return json(res, 400, { error: "Ticker required." });
      var user = null;
      try { user = await currentUser(req); } catch (e) { user = null; }
      if (!bb7Premium(user)) return bb8Route0.apply(this, arguments);
      var codes = url.searchParams.get("codes") === "all" ? "all" : "PS";
      var out;
      try { out = await Promise.race([bb8Older(ticker, before, { codes: codes }), bb8Late(bb8Budget() + 4000)]); }
      catch (e) { out = null; }
      if (!out || out === "bb8-late") out = bb7Unavailable();
      return json(res, out.status, out.body, out.headers || {});
    };
  }
} catch (e) { console.warn("bb8 hooks skipped", e && e.message); }
// BB8_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8")]
if bad:
    die("bb8 block declares a non-bb8 function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8 block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8 function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8 block has a forbidden declaration")

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
print("bb8 setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8bak"
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
print("APPLY bb8 ask + insiders")
