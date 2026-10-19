#!/usr/bin/env python3
"""patch_bb8h.py — Yahoo's published beta on card answers; every model [n] must match its line. Server.js only.
Stacked on bb8g (server md5 7d10de541da933783afa032a90a4e57c). Does not rewrite app.js or index.html.
1) Beta: the bb8g line "Beta (Dispatch desk reference): ..." is removed. When Yahoo publishes a beta
   (quoteSummary summaryDetail.beta, already loaded for the card by bb5, else defaultKeyStatistics.beta from the
   same free quoteSummary call), the lead shows "MU's published beta is 2.23 (Yahoo Finance, 5-year monthly) ... [n]"
   cited "Yahoo Finance" with the key-statistics URL and its as-of; otherwise no beta line. "The Dispatch" source
   now covers only the card score. A model sentence that calls any number other than Yahoo's a beta is dropped.
2) Citation matching: each [n] on a model sentence must point at a fact or source line that shares one of the
   sentence's figures (number with a unit or %, currency, multiple, the number a beta names), or, when the
   sentence has no figure, one of its tickers. Otherwise it is re-pointed to the matching server fact line's
   source, else stripped; a sentence left with no [n] and a figure found in no fact line is dropped. Sources are
   then pruned and renumbered as before (bb8e).
3) Card answers: a model sentence is kept only when it carries a matched [n] and restates none of the card bullet
   figures; otherwise it is dropped (uncited interpretation too). With nothing left the answer is the bullets plus
   'In short'.
4) Insiders: filings load 4 at a time through the shared 10/s SEC limiter and /api/insiders answers within about
   6.5 s; what is ready comes back with meta.partial true, meta.more "loading", note "More filings loading -
   refresh shortly", X-Dispatch-Data-Status: partial, while the same scan keeps filling the cache.
5) Insiders window: free (5 open-market trades) and premium (40 filings) scans no longer share the cache key, so a
   free scan can never stand in for a premium window; a filing that fails twice ends the scan as partial; partial
   scans are never cached, and a complete entry is only replaced by another complete scan. The window covers the
   unbroken run of filings actually loaded.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8h.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "7d10de541da933783afa032a90a4e57c",
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
    print("bb8h %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8h before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8h %s untouched" % label)

if "// \u2500\u2500 bb8h \u2500\u2500" in v:
    print("REFUSE: bb8h already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8g end", "// BB8G_JS_END"),
    ("bb8g beta line", '"Beta (Dispatch desk reference): "'),
    ("bb8eMovePack", "async function bb8eMovePack(base) {"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb8dCleanLine", "function bb8dCleanLine(line, ok, facts) {"),
    ("bb8dSplit", "function bb8dSplit(line) {"),
    ("bb8dStore", "function bb8dStore() {"),
    ("bb8gNums", "function bb8gNums(text) {"),
    ("bb5BetaMem", "var bb5BetaMem = {};"),
    ("rt32Yahoo", "async function rt32Yahoo(sym) {"),
    ("bb8bYahooSym", "function bb8bYahooSym(sym) {"),
    ("bb7FetchForm4", "async function bb7FetchForm4(ticker, mode, now) {"),
    ("bb7Form4", "async function bb7Form4(ticker, mode, now) {"),
    ("bb7FormXml", "async function bb7FormXml(cik, filing) {"),
    ("bb7Shape", "function bb7Shape(pack, opts) {"),
    ("bb8Older", "async function bb8Older(ticker, before, opts) {"),
    ("bb8Load0", "var bb8Load0 = bb7Load;"),
    ("bb8Partial", "function bb8Partial(ticker, mode, opts) {"),
    ("bb8Late", "function bb8Late(ms) {"),
    ("bb8Track", "function bb8Track(ticker, mode, info) {"),
]
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
print("bb8h anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8h ── Yahoo's published beta (cited Yahoo Finance) replaces the card beta line; every model [n] must point
// at a fact or source line that shares the sentence's figure (or, with no figure, its ticker); card prose that
// restates the bullets is dropped; insiders answer within 6.5 s and never cache or label a short scan as complete.
// BB8H_JS
var BB8H_YAHOO_MS = 2500;
var BB8H_NOT_TICKERS = { US: 1, UK: 1, EU: 1, AI: 1, ETF: 1, TTM: 1, CEO: 1, CFO: 1, DRAM: 1, NAND: 1, GDP: 1, FX: 1, IPO: 1, EPS: 1, NTM: 1, PE: 1, II: 1, III: 1, NYSE: 1, NASDAQ: 1, FTSE: 1, DAX: 1, CAC: 1, VIX: 1, DXY: 1, BBC: 1, AP: 1, SEC: 1, OK: 1, PM: 1, AM: 1, GMT: 1, BST: 1, UTC: 1, ET: 1, YOY: 1, QOQ: 1, Q: 1, A: 1, I: 1 };
function bb8hRound(n) { return Math.round(Number(n) * 100) / 100; }
function bb8hBetaOf(v) {
  if (v && typeof v === "object") return bb8hBetaOf(v.raw != null ? v.raw : v.fmt);
  var n = Number(v);
  return v != null && v !== "" && isFinite(n) ? bb8hRound(n) : null;
}
// Yahoo's published beta: summaryDetail.beta (what bb5 already loads for the card), else defaultKeyStatistics.beta.
async function bb8hYahooBeta(base) {
  var key = String(base || "").toUpperCase();
  try {
    var hit = typeof bb5BetaMem !== "undefined" && bb5BetaMem ? bb5BetaMem[key] : null;
    if (hit && hit.beta != null && isFinite(Number(hit.beta)) && Date.now() - Number(hit.at || 0) < 3600000) return { beta: bb8hRound(hit.beta), asOf: hit.asOf || new Date(Number(hit.at) || Date.now()).toISOString(), via: "summaryDetail.beta" };
  } catch (e) {}
  if (typeof rt32Yahoo !== "function") return null;
  try {
    var sym = typeof bb8bYahooSym === "function" ? bb8bYahooSym(key) : key;
    var q = await Promise.race([rt32Yahoo(sym), new Promise(function (r) { setTimeout(function () { r(null); }, BB8H_YAHOO_MS); })]);
    var sd = q && q.summaryDetail, ks = q && q.defaultKeyStatistics;
    var b = bb8hBetaOf(sd && sd.beta), via = "summaryDetail.beta";
    if (b == null) { b = bb8hBetaOf(ks && ks.beta); via = "defaultKeyStatistics.beta"; }
    return b == null ? null : { beta: b, asOf: new Date().toISOString(), via: via };
  } catch (e) { return null; }
}
// Figures: numbers with a unit or %, currency amounts, "N out of 100" / "N/100", multiples, and the number a beta names.
function bb8hFigs(text) {
  var s = String(text || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " "), out = {};
  var add = function (x) { var n = Number(String(x).replace(/,/g, "")); if (isFinite(n)) out[n.toFixed(2)] = 1; };
  s.replace(/[$£€]\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)/g, function (m, a) { add(a); return m; });
  s.replace(/(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:%|percent\b|per cent\b|percentage points?\b|pts?\b|points?\b|[x×](?![a-z])|times\b|out of 100\b|\/100\b|bp\b|basis points\b)/gi, function (m, a) { add(a); return m; });
  s.replace(/\bbeta\b[^.\d]{0,24}?(\d+(?:\.\d+)?)/gi, function (m, a) { add(a); return m; });
  s.replace(/(\d+(?:\.\d+)?)\s*(?:-|\s)?beta\b/gi, function (m, a) { add(a); return m; });
  return out;
}
function bb8hTicks(text, known) {
  var out = {};
  String(text || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/\^?\b[A-Z][A-Z0-9]{0,5}(?:\.[A-Z]{1,2})?\b/g, function (m) {
    var t = m.replace(/^\^/, "");
    if (!BB8H_NOT_TICKERS[t] && known[t]) out[t] = 1;
    return m;
  });
  return out;
}
function bb8hAny(a, b) { for (var k in a) if (b[k]) return true; return false; }
function bb8hWords(text) {
  var out = {};
  String(text || "").toLowerCase().replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/[a-z]{4,}/g, function (w) { out[w] = 1; return w; });
  return out;
}
function bb8hOverlap(words, text) { var n = 0, o = bb8hWords(text); for (var k in words) if (o[k]) n++; return n; }
// For the current answer: per source number, the text of every fact line that cites it plus the source record itself.
function bb8hIndex(st, facts) {
  var full = typeof bb8eFull === "function" ? bb8eFull(st) : [];
  var idx = { n: full.length, text: {}, fact: {}, factFigs: {}, known: {}, yBeta: null, yN: 0 };
  var addText = function (n, t, isFact) {
    if (!(n >= 1 && n <= full.length)) return;
    idx.text[n] = (idx.text[n] || "") + "\n" + t;
    if (isFact) { idx.fact[n] = (idx.fact[n] || "") + "\n" + t; var f = bb8hFigs(t); for (var k in f) idx.factFigs[k] = 1; }
  };
  var known = idx.known;
  var mv = st && st.bb8eMove;
  if (mv && mv.bb8hPack) {
    var p = mv.bb8hPack;
    [p.base, p.bench && p.bench.sym, p.sector && p.sector.sym].forEach(function (t) { if (t) known[String(t).replace(/^\^/, "")] = 1; });
  }
  (facts || []).forEach(function (f) { if (f && f.a) known[String(f.a).toUpperCase()] = 1; if (f && f.b) known[String(f.b).toUpperCase()] = 1; });
  try { (st && st.bb8eBody && Array.isArray(st.bb8eBody.tickers) ? st.bb8eBody.tickers : []).forEach(function (t) { known[String(t).toUpperCase()] = 1; }); } catch (e) {}
  if (st && st.bb8eBase) known[String(st.bb8eBase).toUpperCase()] = 1;
  full.forEach(function (s, i) { if (s) addText(i + 1, String(s.name || "") + " " + String(s.detail || ""), false); });
  if (mv && mv.text) {
    mv.text.split("\n").slice(1).forEach(function (line) {
      var ns = []; line.replace(/\[(\d{1,2})\]/g, function (m, g) { ns.push(Number(g)); return m; });
      ns.forEach(function (n) { addText(n, line, true); });
    });
    if (mv.bb8hBeta) { idx.yBeta = mv.bb8hBeta.beta; idx.yN = full.indexOf(mv.bb8hBeta.src) + 1; }
  }
  if (facts && facts.length && st && st.peerSource) {
    var pn = full.indexOf(st.peerSource) + 1;
    facts.forEach(function (f) { if (f && f.sentence) addText(pn, f.sentence, true); });
  }
  return idx;
}
function bb8hMatch(idx, n, figs, ticks, hasFig) {
  var t = idx.text[n];
  if (!t) return false;
  return hasFig ? bb8hAny(figs, bb8hFigs(t)) : bb8hAny(ticks, bb8hTicks(t, idx.known));
}
// Re-point or strip each [n]; returns "" when the sentence must go.
function bb8hFixSentence(sent, idx) {
  var s = String(sent || "");
  var figs = bb8hFigs(s), ticks = bb8hTicks(s, idx.known);
  var hasFig = Object.keys(figs).length > 0;
  if (/\bbeta\b/i.test(s)) {
    var nums = s.replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").match(/\d+(?:\.\d+)?/g) || [];
    if (nums.length) {
      // Only Yahoo's published beta may be called a beta.
      if (idx.yBeta == null || !nums.some(function (x) { return Number(x).toFixed(2) === Number(idx.yBeta).toFixed(2); })) return "";
    }
  }
  var cites = [];
  s.replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) { g.split(/\s*,\s*/).forEach(function (x) { cites.push(Number(x)); }); return m; });
  if (!cites.length) return s;
  var keep = [];
  cites.forEach(function (n) {
    var ok = n >= 1 && n <= idx.n && bb8hMatch(idx, n, figs, ticks, hasFig);
    var to = ok ? n : 0;
    if (!to) {
      // Re-point: prefer a server fact line that shares the figure/ticker, then any source record.
      // Among several matching lines, the one sharing the most words with the sentence wins.
      var best = 0, top = -1, words = bb8hWords(s);
      for (var a = 1; a <= idx.n; a++) if (idx.fact[a] && (hasFig ? bb8hAny(figs, bb8hFigs(idx.fact[a])) : bb8hAny(ticks, bb8hTicks(idx.fact[a], idx.known)))) {
        var sc = bb8hOverlap(words, idx.fact[a]);
        if (sc > top) { top = sc; best = a; }
      }
      for (var b = 1; b <= idx.n && !best; b++) if (bb8hMatch(idx, b, figs, ticks, hasFig)) best = b;
      to = best;
    }
    if (to && keep.indexOf(to) < 0) keep.push(to);
  });
  var first = true;
  var out = s.replace(/[ \t]*\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m) {
    if (!first) return "";
    first = false;
    if (!keep.length) return "";
    return (/^[ \t]/.test(m) ? " " : "") + keep.map(function (k) { return "[" + k + "]"; }).join("");
  }).replace(/\s+([.!?])/g, "$1");
  if (!keep.length && hasFig) {
    for (var k in figs) if (!idx.factFigs[k]) return "";
  }
  return out;
}
// Card answers: the bullets already state every card figure. A model sentence is kept only when it carries a
// matched [n] and restates none of the bullet figures (same rule as the valuation restatement filter).
function bb8hLeadFigs(mv) {
  if (!mv.bb8hFigs) mv.bb8hFigs = bb8hFigs(mv.text);
  return mv.bb8hFigs;
}
function bb8hCardKeep(sent, lead) {
  if (!/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/.test(sent)) return false;
  return !bb8hAny(bb8hFigs(sent), lead || {});
}
function bb8hRewriteLine(line, st, facts) {
  if (!line) return line;
  var idx = bb8hIndex(st, facts);
  if (!idx.n) return line;
  var pre = (/^\s*(?:[-*•]|\d+[.)])\s+/.exec(line) || [""])[0];
  var card = !!(st && st.bb8eMode === "move" && st.bb8eMove && !(facts && facts.length));
  var lead = card ? bb8hLeadFigs(st.bb8eMove) : null;
  var parts = bb8dSplit(String(line).slice(pre.length)).map(function (x) { return bb8hFixSentence(x, idx); }).filter(function (x) { return x && x.trim() && (!card || bb8hCardKeep(x, lead)); });
  if (!parts.length) return "";
  return pre.trim() ? pre.trim() + " " + parts.join(" ") : parts.join(" ");
}
try {
  if (typeof bb8eMovePack === "function") {
    var bb8hPack0 = bb8eMovePack;
    bb8eMovePack = async function (base) {
      var pack = await bb8hPack0.apply(this, arguments);
      if (pack) { try { pack.bb8hBeta = await bb8hYahooBeta(pack.base); } catch (e) { pack.bb8hBeta = null; } }
      return pack;
    };
  }
  if (typeof bb8eLead === "function") {
    var bb8hLead0 = bb8eLead;
    bb8eLead = function (pack, card, n0) {
      var out = bb8hLead0.apply(this, arguments);
      try {
        var lines = out.text.split("\n");
        var oldFacts = lines.slice(1).join("\n");
        // The bb8g line called the card input "Dispatch desk reference"; it is replaced by Yahoo's own figure, or dropped.
        lines = lines.filter(function (l) { return !/^Beta \(Dispatch desk reference\):/.test(l); });
        out.sources.forEach(function (s) { if (s && s.name === "The Dispatch") s.detail = "Pulse card score (regime fit)"; });
        var yb = pack && pack.bb8hBeta;
        if (yb && yb.beta != null) {
          var k = n0 + out.sources.length + 1;
          var src = { name: "Yahoo Finance", link: "https://finance.yahoo.com/quote/" + encodeURIComponent(pack.ysym || pack.base) + "/key-statistics/", asOf: yb.asOf, detail: pack.base + " beta (5Y monthly), published by Yahoo Finance" };
          out.sources.push(src);
          var at = -1;
          for (var i = 1; i < lines.length; i++) if (/^Card score \(Dispatch regime fit\):/.test(lines[i])) at = i;
          if (at < 0) for (var j = 1; j < lines.length; j++) if (!/^In the news/.test(lines[j])) at = j;
          var bl = pack.base + "'s published beta is " + Number(yb.beta).toFixed(2) + " (Yahoo Finance, 5-year monthly), so it has tended to move about " + Number(yb.beta).toFixed(2) + " times as much as the market. [" + k + "]";
          lines.splice(at >= 0 ? at + 1 : lines.length, 0, bl);
          out.bb8hBeta = { beta: Number(yb.beta), src: src };
        }
        var text = lines.join("\n");
        out.prompt = out.prompt.replace(oldFacts, lines.slice(1).join("\n")) + " Only the Yahoo Finance line may be called beta; never call the card score or its inputs a beta. Cite each figure with the [n] of the line that shows it. Do not restate any figure from the lines above; add at most two cited sentences of context they do not already give, or nothing.";
        out.text = text;
        out.paint = text.replace(/\s*\[\d+\]/g, "");
        out.bb8gNums = typeof bb8gNums === "function" ? bb8gNums(text) : out.bb8gNums;
        out.bb8hPack = pack;
        out.bb8hFigs = null;
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb8dCleanLine === "function") {
    var bb8hClean0 = bb8dCleanLine;
    bb8dCleanLine = function (line, ok, facts) {
      var out = bb8hClean0.apply(this, arguments);
      try {
        var st = bb8dStore();
        if (out && st && st.chat && ((st.bb8eMode === "move" && st.bb8eMove) || (facts && facts.length))) out = bb8hRewriteLine(out, st, facts);
      } catch (e) {}
      return out;
    };
  }
} catch (e) { console.warn("bb8h hooks skipped", e && e.message); }
// Insiders (items 4 and 5). Root cause of "Last 7 months" -> "Last 3 weeks": the free scan (stops after 5
// open-market trades, about 6 NVDA filings) and the premium scan (40 filings) shared one cache key "f4:T", so a
// free visitor overwrote the complete premium entry; the next cold premium request ran past the 8 s budget and
// was answered from that free entry as "stale" with a window built from its 6 filings. Separately, a filing whose
// fetch failed (limiter wait or SEC error) was counted as scanned, so a short scan could be cached as complete.
// Now: premium "f4:T" only ever holds complete 40-filing scans, free scans live in "f4:T:free", a scan with a
// failed filing is partial and never cached, the window covers only the filings actually loaded (the unbroken run
// from the newest), filings load 4 at a time through the shared 10/s SEC limiter, and the route answers within
// about 6.5 s with what is ready (meta.partial, X-Dispatch-Data-Status: partial) while the same scan finishes
// and fills the cache.
var BB8H_CAP_MS = 6500;
var BB8H_PAR = 4;
var BB8H_SCAN = 40;
var BB8H_MORE_NOTE = "More filings loading \u2014 refresh shortly";
var BB8H_RETRY_NOTE = "Some filings could not be loaded \u2014 refresh shortly";
function bb8hCap() {
  try { var n = Number(globalThis.bb8InsidersBudgetMs); if (isFinite(n) && n > 0) return n; } catch (e) {}
  return BB8H_CAP_MS;
}
function bb8hKey(ticker, mode) { var k = "f4:" + bb7TickerKeys(ticker)[0]; return mode === "full" ? k : k + ":free"; }
// A cached pack answers a request only when its scan finished; a complete premium scan also answers free requests.
function bb8hServes(body, mode) {
  if (!body || body.complete !== true) return false;
  if (mode === "full") return !body.scope || body.scope === "full";
  return true;
}
function bb8hCached(ticker, mode, now, freshOnly) {
  var keys = mode === "full" ? [bb8hKey(ticker, "full")] : [bb8hKey(ticker, "full"), bb8hKey(ticker, "free")];
  for (var i = 0; i < keys.length; i++) {
    var row = bb7Recall(keys[i]);
    if (!row || !bb8hServes(row.body, mode)) continue;
    if (keys[i].slice(-5) === ":free" && row.body.scope !== "free") continue;
    if (freshOnly && !(now - row.at <= row.ttl)) continue;
    return row;
  }
  return null;
}
// Old entries from before bb8h may hold a free (incomplete) scan under the premium key: drop them so they are
// never served as a premium window.
function bb8hPurge(ticker) {
  try {
    var key = bb8hKey(ticker, "full"), row = bb7Recall(key);
    if (row && row.body && !bb8hServes(row.body, "full")) bb7Mem.delete(key);
  } catch (e) {}
}
function bb8hKeep(ticker, pack, now) {
  if (!pack || pack.unknown || pack.complete !== true) return false;
  bb7Remember(bb8hKey(ticker, pack.scope === "full" ? "full" : "free"), pack, bb7FormTtl, now);
  return true;
}
// One retry. SEC answering 404/410 for a filing is a real answer (nothing to parse), not a failed load.
async function bb8hFiling(cik, filing) {
  for (var n = 0; ; n++) {
    try { return await bb7FormXml(cik, filing); }
    catch (e) {
      if (e && (e.status === 404 || e.status === 410)) return "";
      if (n >= 1) throw e;
    }
  }
}
// Load up to 40 filings, BB8H_PAR at a time. Rows are taken in filing order from the unbroken run of loaded
// filings, so the window and rows always describe the same filings. A filing that fails twice ends the run.
function bb8hScan(cik, filings, mode, onInfo) {
  var limit = Math.min(filings.length, BB8H_SCAN);
  var got = new Array(limit), next = 0, run = 0, open = 0, stop = false, failed = 0, rows = [];
  var info = { rows: rows, scanned: function () { return run; } };
  if (onInfo) onInfo(info);
  function advance() {
    while (!stop && run < limit && got[run] !== undefined) {
      if (got[run] === null) { failed++; stop = true; break; }
      for (var j = 0; j < got[run].length; j++) { rows.push(got[run][j]); if (bb7IsOpenMarket(got[run][j])) open++; }
      run++;
      if (mode !== "full" && open >= 5) stop = true;
    }
  }
  async function worker() {
    while (!stop && next < limit) {
      var i = next++, f = filings[i], xml = null;
      try { xml = await bb8hFiling(cik, f); } catch (e) { xml = null; }
      if (xml == null) got[i] = null;
      else {
        var meta = { filingDate: f.filingDate, accession: f.accession, filingUrl: bb7IndexUrl(cik, f.accession) };
        try { got[i] = bb7ParseForm4(xml, meta) || []; } catch (e2) { got[i] = []; }
      }
      advance();
    }
  }
  var ws = [];
  for (var w = 0; w < Math.min(BB8H_PAR, Math.max(1, limit)); w++) ws.push(worker());
  return Promise.all(ws).then(function () {
    advance();
    var done = failed === 0 && (run >= limit || (mode !== "full" && open >= 5));
    return { rows: rows, scanned: run, failed: failed, complete: done };
  });
}
async function bb8hFetchForm4(ticker, mode, now) {
  var map = await bb7TickerMap(now);
  var hit = bb7Lookup(map, ticker);
  if (!hit) return { unknown: true };
  var submission = JSON.parse((await bb7FetchBuf("https://data.sec.gov/submissions/CIK" + hit.cik + ".json")).toString("utf8"));
  var filings = bb7FormList(submission);
  var company = hit.company || submission.name || "";
  var r = await bb8hScan(hit.cik, filings, mode, function (info) {
    bb8Track(ticker, mode, { rows: info.rows, cik: hit.cik, company: company, list: filings, scanned: info.scanned });
  });
  return {
    unknown: false, ticker: bb7TickerKeys(ticker)[0], cik: hit.cik, company: company, rows: r.rows,
    complete: r.complete, scope: mode === "full" ? "full" : "free", failed: r.failed,
    filings: filings.length, scanned: r.scanned,
    newestFiling: r.scanned ? filings[0].filingDate : "",
    oldestFiling: r.scanned ? filings[r.scanned - 1].filingDate : ""
  };
}
async function bb8hForm4(ticker, mode, now) {
  var row = bb8hCached(ticker, mode, now, true);
  if (row) return Object.assign({ stale: false, asOf: new Date(row.at).toISOString() }, row.body);
  var flight = "f4-flight:" + bb8hKey(ticker, "full") + ":" + mode;
  if (bb7Inflight.has(flight)) return bb7Inflight.get(flight);
  var job = (async function () {
    var pack = await bb8hFetchForm4(ticker, mode, now);
    bb8hKeep(ticker, pack, now);
    return Object.assign({ stale: false, asOf: new Date(now).toISOString() }, pack);
  })();
  bb7Inflight.set(flight, job);
  try { return await job; }
  finally { bb7Inflight.delete(flight); }
}
function bb8hFlag(out, loading) {
  if (!out || !out.body || !out.body.meta || !out.body.meta.partial) return out;
  out.body.meta.more = loading ? "loading" : "retry";
  out.body.note = loading ? BB8H_MORE_NOTE : BB8H_RETRY_NOTE;
  out.headers = Object.assign({}, out.headers || {}, { "X-Dispatch-Data-Status": "partial", "Cache-Control": "no-store" });
  delete out.headers["X-Dispatch-As-Of"];
  return out;
}
// What is ready when the cap hits: the unbroken run of loaded filings (possibly none yet), flagged partial.
function bb8hPartial(ticker, mode, opts) {
  var out = bb8Partial(ticker, mode, opts);
  if (!out) {
    var key = bb7TickerKeys(ticker)[0];
    var prog = bb8Progress.get(key + ":" + mode);
    var list = prog && prog.list || null;
    var pack = { ticker: key, cik: prog && prog.cik || "", company: prog && prog.company || "", rows: [], complete: false, filings: list ? list.length : null, scanned: 0, newestFiling: "", oldestFiling: "", stale: false, asOf: new Date(bb7Now()).toISOString(), note: BB8H_MORE_NOTE };
    var houseBody = null;
    if (opts && opts.house && opts.premium) {
      var old = bb7Recall("house:index");
      houseBody = old ? bb7HouseView({ items: old.body, asOf: new Date(old.at).toISOString() }) : { items: [], asOf: "", note: "House filings are still loading. Try again in a moment." };
    }
    var body = bb7Shape(pack, { premium: !!(opts && opts.premium), codes: opts && opts.codes, house: !!(opts && opts.house), houseBody: houseBody });
    body.meta.partial = true;
    out = { status: 200, body: body, headers: {} };
  }
  return bb8hFlag(out, true);
}
async function bb8hOlder(ticker, before, opts) {
  var now = bb7Now();
  var key = "f4:" + bb7TickerKeys(ticker)[0] + "<" + before + ":" + (opts.codes === "all" ? "all" : "PS");
  var cached = bb7Recall(key);
  var pack = cached && now - cached.at <= cached.ttl && cached.body && cached.body.complete === true ? cached.body : null;
  if (!pack) {
    cached = null;
    var map = await bb7TickerMap(now);
    var hit = bb7Lookup(map, ticker);
    if (!hit) return { status: 404, body: { error: "Unknown ticker." }, headers: {} };
    var submission = JSON.parse((await bb7FetchBuf("https://data.sec.gov/submissions/CIK" + hit.cik + ".json")).toString("utf8"));
    var filings = bb7FormList(submission).filter(function (f) { return String(f.filingDate || "") < before; });
    var r = await bb8hScan(hit.cik, filings, "full", null);
    pack = {
      unknown: false, ticker: bb7TickerKeys(ticker)[0], cik: hit.cik, company: hit.company || submission.name || "", rows: r.rows,
      complete: r.complete, scope: "full", failed: r.failed, filings: filings.length, scanned: r.scanned,
      newestFiling: r.scanned ? filings[0].filingDate : "", oldestFiling: r.scanned ? filings[r.scanned - 1].filingDate : ""
    };
    if (pack.complete) bb7Remember(key, pack, bb7FormTtl, now);
  }
  var body = bb7Shape(Object.assign({ stale: false, asOf: new Date(cached ? cached.at : now).toISOString() }, pack), { premium: true, codes: opts.codes, house: false });
  body.meta.before = before;
  return bb8hFlag({ status: 200, body: body, headers: { "X-Dispatch-Data-Status": "fresh" } }, false);
}
try {
  if (typeof bb7FetchForm4 === "function") bb7FetchForm4 = bb8hFetchForm4;
  if (typeof bb7Form4 === "function") bb7Form4 = bb8hForm4;
  if (typeof bb8Older === "function") bb8Older = bb8hOlder;
  if (typeof bb7Shape === "function") {
    var bb8hShape0 = bb7Shape;
    bb7Shape = function (pack, opts) {
      var body = bb8hShape0.apply(this, arguments);
      try {
        // A scan that did not finish is partial, and its window says so.
        if (pack && pack.complete !== true && body && body.meta) {
          body.meta.partial = true;
          if (body.meta.window && typeof body.meta.window === "object") {
            body.meta.window.partial = true;
            if (!pack.scanned) body.meta.window.label = "Loading filings";
          }
        }
      } catch (e) {}
      return body;
    };
  }
  if (typeof bb7Load === "function" && typeof bb8Load0 === "function") {
    // Replaces the bb8 8 s wrapper (same retry-once rule) with the 6.5 s cap and complete-only fallbacks.
    bb7Load = async function (ticker, opts) {
      var t0 = Date.now(), cap = bb8hCap(), self = this;
      var mode = opts && opts.premium ? "full" : "free";
      bb8hPurge(ticker);
      var job = bb8Load0.call(self, ticker, opts);
      var out = await Promise.race([job, bb8Late(cap)]);
      if (out !== "bb8-late" && out && out.body && out.body.unavailable && cap - (Date.now() - t0) > 1500) {
        job = bb8Load0.call(self, ticker, opts);
        out = await Promise.race([job, bb8Late(cap - (Date.now() - t0))]);
      }
      if (out !== "bb8-late") return bb8hFlag(out, false);
      job.catch(function () {});
      var row = bb8hCached(ticker, mode, bb7Now(), false);
      if (row) return bb7StaleResult(Object.assign({ asOf: new Date(row.at).toISOString() }, row.body), opts || {});
      return bb8hPartial(ticker, mode, opts);
    };
  }
} catch (e) { console.warn("bb8h insiders hooks skipped", e && e.message); }
// BB8H_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8h")]
if bad:
    die("bb8h block declares a non-bb8h function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8h block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8h function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8h block has a forbidden declaration")

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
print("bb8h setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8hbak"
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
print("APPLY bb8h Yahoo beta, citation matching, card restatement filter, insiders 6.5 s cap + complete-only cache")
