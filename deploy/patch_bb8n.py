#!/usr/bin/env python3
"""patch_bb8n.py — No beta line or card score for non-equities (gold/metals, FX, crypto, indices, rates and
commodity futures); Sources list only what the answer cites, renumbered 1..n by first appearance (both paths).
Server.js only. Stacked on bb8m (server md5 464c5b95c3079b067a840b5b0a8fde25). Does not rewrite app.js or index.html.
Equity check: symbol patterns (=X, =F, ^, -USD, DX-Y.NYB, XAU/XAG/XPT/XPD, currency pairs, BB3 crypto/commodity
rows), else Yahoo price.quoteType (EQUITY/ETF are equities). Beta lines need a finite, non-zero Yahoo beta.
Pruning runs at the shared assembler after every filter and the bb8n trim; the JSON top-level sources array and the
stream done event carry the same pruned list. See docs/bb8n.md.
No tables, intervals, timers, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8n.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "464c5b95c3079b067a840b5b0a8fde25",
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
    print("bb8n %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8n before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8n %s untouched" % label)

if "// \u2500\u2500 bb8n \u2500\u2500" in v:
    print("REFUSE: bb8n already applied")
    sys.exit(0)

REPLACE = [
]
REQUIRED = [
    ("bb8m end", "// BB8M_JS_END"),
    ("bb8mTrim", "function bb8mTrim(reply, max) {"),
    ("bb8mUnits", "function bb8mUnits(text) {"),
    ("bb8mWords", "function bb8mWords(text) {"),
    ("bb8eMovePack", "async function bb8eMovePack(base) {"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb8dDrop", "function bb8dDrop(sent, ok, facts) {"),
    ("bb8kApplyHints", "function bb8kApplyHints(body) {"),
    ("bb8jAssemble", "function bb8jAssemble(reply, store) {"),
    ("bb8kSources", "function bb8kSources(st) {"),
    ("bb2Footer", "function bb2Footer(sources) {"),
    ("bb8hYahooBeta", "async function bb8hYahooBeta(base) {"),
    ("rt32Yahoo", "async function rt32Yahoo(sym) {"),
    ("rt32Yahoo price module", "  const mods = \"summaryDetail,defaultKeyStatistics,financialData,earnings,earningsHistory,calendarEvents,institutionOwnership,majorHoldersBreakdown,price,earningsTrend\";\n  for (let i = 0; i < 2; i++) {\n    const crumb = await rt32Crumb(i > 0);"),
    ("bb8Late", "function bb8Late(ms) {"),
    ("bb8bYahooSym", "function bb8bYahooSym(sym) {"),
    ("bb3Yahoo", "function bb3Yahoo(ticker) {"),
    ("BB3_MAP", "const BB3_MAP = {};"),
    ("bb8dStore", "function bb8dStore() {"),
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
print("bb8n anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8n ── No beta or card score for non-equities; Sources list only what the answer cites (both paths).
// BB8N_JS
// (a) Equity check. Before bb8n the server had no equity test: the card used BB3 rows (cat "crypto" / "commodity" /
// "other") and bb8h's Yahoo beta for any base, so the XAU card printed "beta 0.00" and a card score. bb8nKind:
// symbol patterns first (Yahoo symbol via bb3Yahoo: "=X" FX, "=F" futures, "^" indices and rate indices, "-USD"
// crypto, DX-Y.NYB, XAU/XAG/XPT/XPD metals, 6-letter currency pairs, BB3 crypto/commodity rows); otherwise Yahoo
// price.quoteType from the quoteSummary the card already loads (shared with bb8l's in-flight call): EQUITY and ETF
// are equities, CURRENCY / CRYPTOCURRENCY / INDEX / FUTURE / MUTUALFUND / anything else are not. No quoteType in
// time and no pattern: treated as an equity (the pre-bb8n behaviour), and the beta must still be finite and non-zero.
// For a non-equity the move pack has no card fit and no beta, so the lead has no "Card score" or beta line, no
// Dispatch score source, and neither reaches the prompt; the client context's "Score N/100" and "Beta x" for a
// non-equity active ticker are removed from the prompt; model sentences naming a beta or card score are dropped.
// (b) Sources. After every filter and the bb8m trim, the shared assembler (bb8jAssemble: stream done event and JSON
// reply) keeps only the sources the text cites, renumbers them 1..n in order of first appearance, rewrites every
// [n] (In short line included) and drops markers that point at nothing. The returned sources and st.bb8jSources
// (the JSON top-level sources array) are the same pruned list. The stream's done.reply replaces the painted text on
// the client (app.js uses final.reply), so painted numbering never survives. No cited source: unchanged.
var BB8N_YAHOO_MS = 2500;
var BB8N_INDEX = { SPX: 1, DJIA: 1, IXIC: 1, FTSE: 1, DAX: 1, CAC: 1, N225: 1, NSEI: 1, HSI: 1, ASX200: 1, KOSPI: 1, VIX: 1, DXY: 1, TNX: 1, TYX: 1, FVX: 1, IRX: 1, US10Y: 1, US2Y: 1, US30Y: 1 };
var BB8N_METAL = /^(?:XAU|XAG|XPT|XPD|GOLD|SILVER)(?:USD)?$/;
var BB8N_CCY = "(?:USD|EUR|GBP|JPY|CHF|AUD|NZD|CAD|CNY|CNH|HKD|SEK|NOK|DKK|SGD|INR|MXN|ZAR|TRY|KRW|BRL)";
var BB8N_PAIR = new RegExp("^" + BB8N_CCY + BB8N_CCY + "$");
var BB8N_QT = { EQUITY: "equity", ETF: "equity", CURRENCY: "fx", CRYPTOCURRENCY: "crypto", INDEX: "index", FUTURE: "future", MUTUALFUND: "fund", OPTION: "option", MONEYMARKET: "fund" };
// Symbol-pattern kind, or null when the patterns cannot tell.
function bb8nKindBySymbol(base) {
  var b = String(base || "").toUpperCase(), y = "";
  try { y = String(typeof bb3Yahoo === "function" ? bb3Yahoo(b) : b).toUpperCase(); } catch (e) { y = b; }
  if (BB8N_METAL.test(b)) return "metal";
  if (/=X$/.test(y) || BB8N_PAIR.test(b)) return "fx";
  if (/=F$/.test(y)) return /^(?:GC|SI|PL|PA|HG)=F$/.test(y) ? "metal" : (/^(?:ZN|ZB|ZF|ZT|GE|SR3)=F$/.test(y) ? "rates" : "future");
  if (/^\^/.test(y) || /^\^/.test(b) || y === "DX-Y.NYB" || BB8N_INDEX[b]) return /^\^(?:TNX|TYX|FVX|IRX)$/.test(y) || /^(?:TNX|TYX|FVX|IRX|US\d+Y)$/.test(b) ? "rates" : "index";
  if (/-(?:USD|USDT|GBP|EUR)$/.test(y) || /-(?:USD|USDT)$/.test(b)) return "crypto";
  try {
    var row = typeof BB3_MAP !== "undefined" && BB3_MAP ? BB3_MAP[b] : null;
    if (row && row.cat === "crypto") return "crypto";
    if (row && row.cat === "commodity") return "commodity";
  } catch (e) {}
  return null;
}
function bb8nKindByQuoteType(qt) {
  var k = String(qt || "").toUpperCase();
  return k ? (BB8N_QT[k] || "other") : null;
}
// { equity, kind, via } for a card/move base. Never throws; waits at most BB8N_YAHOO_MS through bb8Late.
async function bb8nKind(base) {
  var k = bb8nKindBySymbol(base);
  if (k) return { equity: false, kind: k, via: "symbol" };
  if (typeof rt32Yahoo === "function") {
    try {
      var sym = typeof bb8bYahooSym === "function" ? bb8bYahooSym(base) : String(base || "");
      var p = rt32Yahoo(sym);
      if (p && typeof p.catch === "function") p.catch(function () {});
      var late = typeof bb8Late === "function" ? bb8Late(BB8N_YAHOO_MS) : null;
      var res = late ? await Promise.race([p, late]) : await p;
      var qt = res && res !== "bb8-late" && res.price ? res.price.quoteType : null;
      var kq = bb8nKindByQuoteType(qt);
      if (kq) return { equity: kq === "equity", kind: kq, via: "yahoo quoteType " + String(qt).toUpperCase() };
    } catch (e) {}
  }
  return { equity: true, kind: "equity", via: "assumed (no pattern, no quoteType)" };
}
function bb8nBetaOk(b) {
  var n = b && typeof b === "object" ? Number(b.beta) : Number(b);
  return b != null && isFinite(n) && n !== 0;
}
// Client context: drop "Score N/100" and "Beta x" from the Active ticker line for a non-equity, and an unusable beta.
function bb8nContext(ctx) {
  if (typeof ctx !== "string" || ctx.indexOf("Active ticker:") < 0) return ctx;
  return ctx.replace(/^(Active ticker:\s*\$?(\^?[A-Z][A-Z0-9.\-=^]{0,11})[^\n]*)$/m, function (line, all, tk) {
    var nonEq = !!bb8nKindBySymbol(tk);
    var out = line;
    if (nonEq) out = out.replace(/\s*\u00b7\s*Score\s+-?\d+(?:\.\d+)?\/100/g, "");
    out = out.replace(/\s*\u00b7\s*Beta\s+([^\u00b7\n]*?)(?=\s*\u00b7|\s*$)/g, function (m, v) { var n = Number(String(v).trim()); return nonEq || !isFinite(n) || n === 0 || !String(v).trim() ? "" : m; });
    return out;
  });
}
// A model sentence that restates a beta or the card score (non-equity card/move answers only).
function bb8nRestates(sent) {
  // Beta (not "high-beta"/"low-beta" sector labels), the card score or regime fit. A bare N/100 counts only when
  // it is not the market regime or Fear/Greed reading, which stay valid for every asset.
  var t = String(sent || "");
  if (/(?<![-\w])beta\b|card score|regime[- ]fit|\bpulse (?:card )?score\b/i.test(t)) return true;
  return /\bscored? (?:is |of |at )?\d{1,3}\s*(?:\/\s*100|out of 100)\b/i.test(t) && !/fear|greed|risk-o(?:n|ff)|regime (?:reading|score)|market (?:mood|regime)/i.test(t);
}
// Prune and renumber. Returns { reply, sources, map } or null when nothing is changed.
function bb8nPrune(reply, sources) {
  var text = String(reply || "");
  var at = text.lastIndexOf("\nSources:\n");
  if (at < 0) return null;
  var bodyEnd = at; while (bodyEnd > 0 && text[bodyEnd - 1] === "\n") bodyEnd--;
  var body = text.slice(0, bodyEnd), sep = text.slice(bodyEnd, at + 1), foot = text.slice(at + 1);
  var footLines = foot.split("\n").slice(1);
  var items = [], rest = [];
  for (var i = 0; i < footLines.length; i++) {
    var m = footLines[i].match(/^\[(\d+)\]\s?(.*)$/);
    if (m && Number(m[1]) === items.length + 1 && !rest.length) items.push(m[2]); else rest.push(footLines[i]);
  }
  if (!items.length) return null;
  if (!Array.isArray(sources) || sources.length !== items.length) return null;   // footer and list must agree
  var src = sources;
  var n = items.length, order = [], map = {};
  var re = /\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g;
  body.replace(re, function (mm, g) { g.split(/\s*,\s*/).forEach(function (x) { var k = Number(x); if (k >= 1 && k <= n && !map[k]) { map[k] = order.length + 1; order.push(k); } }); return mm; });
  if (!order.length) {
    // Nothing resolvable is cited: the list stays as the earlier patches left it, but markers that point at
    // nothing are removed so every remaining [n] resolves.
    var bare = body.replace(/ ?\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (mm, g) { return g.split(/\s*,\s*/).some(function (x) { var k = Number(x); return k >= 1 && k <= n; }) ? mm : ""; });
    return bare === body ? null : { reply: bare + sep + foot, sources: src.slice(), map: {} };
  }
  var same = order.length === n && order.every(function (k, j) { return k === j + 1; });
  var newBody = body.replace(/ ?\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (mm, g) {
    var got = [];
    g.split(/\s*,\s*/).forEach(function (x) { var k = map[Number(x)]; if (k && got.indexOf(k) < 0) got.push(k); });
    return got.length ? (mm.charAt(0) === " " ? " " : "") + "[" + got.join(", ") + "]" : "";
  });
  if (same && newBody === body) return null;
  var lines = order.map(function (k, j) { return "[" + (j + 1) + "] " + items[k - 1]; });
  return {
    reply: newBody + sep + "Sources:\n" + lines.concat(rest).join("\n"),
    sources: order.map(function (k) { return src[k - 1]; }),
    map: map
  };
}
// bb8m's brief trim can cut every cited sentence (answer opens with uncited context). Keep the first cited
// sentence instead: the longest prefix that fits with it, then that sentence, so the answer still cites a source.
var BB8N_CITE = /\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/;
function bb8nBodyOf(text) {
  var t = String(text || ""), at = t.search(/\n+Sources:\n/);
  var b = at >= 0 ? t.slice(0, at) : t;
  return b.replace(/(?:^|\n)In short:[^\n]*/g, "");
}
function bb8nKeepCited(orig, r, max) {
  if (!r || !r.cut || typeof bb8mUnits !== "function" || typeof bb8mWords !== "function") return r;
  if (BB8N_CITE.test(bb8nBodyOf(r.text)) || !BB8N_CITE.test(bb8nBodyOf(orig))) return r;
  var text = String(orig || ""), at = text.search(/\n+Sources:\n/);
  var body = at >= 0 ? text.slice(0, at) : text, tail = at >= 0 ? text.slice(at) : "";
  var sm = body.match(/(?:^|\n)(In short:[^\n]*)\s*$/) || body.match(/(?:^|\n)(In short:[^\n]*)/);
  var inShort = sm ? sm[1] : "";
  var rest = (sm ? body.slice(0, sm.index) + body.slice(sm.index + sm[0].length) : body).replace(/\s+$/, "");
  var ends = bb8mUnits(rest), c = -1;
  for (var i = 0; i < ends.length; i++) { var u = rest.slice(i ? ends[i - 1] : 0, ends[i]); if (BB8N_CITE.test(u) && !/:\s*$/.test(u.trim())) { c = i; break; } }
  if (c < 0) return r;
  var unit = rest.slice(c ? ends[c - 1] : 0, ends[c]).trim();
  var budget = max - bb8mWords(inShort) - bb8mWords(unit), keep = 0;
  for (var j = 0; j < c; j++) { if (bb8mWords(rest.slice(0, ends[j])) > budget) break; keep = ends[j]; }
  var pre = rest.slice(0, keep).replace(/\s+$/, "");
  var joiner = !pre ? "" : (/\n/.test(rest.slice(keep, (c ? ends[c - 1] : 0) + 1)) ? "\n" : " ");
  var cut = (pre + joiner + unit).replace(/\s+$/, "");
  return { text: cut + (inShort ? "\n\n" + inShort : "") + tail, cut: true, words: bb8mWords(cut) + bb8mWords(inShort) };
}
try {
  if (typeof bb8mTrim === "function") {
    var bb8nTrim0 = bb8mTrim;
    bb8mTrim = function (reply, max) { return bb8nKeepCited(reply, bb8nTrim0.apply(this, arguments), max); };
  }
  if (typeof bb8eMovePack === "function") {
    var bb8nPack0 = bb8eMovePack;
    bb8eMovePack = async function (base) {
      var kp = bb8nKind(base);
      var pack = await bb8nPack0.apply(this, arguments);
      if (!pack) return pack;
      try {
        var k = await kp;
        pack.bb8nKind = k;
        if (!k.equity) { pack.fit = null; pack.bb8hBeta = null; }
        else if (pack.bb8hBeta && !bb8nBetaOk(pack.bb8hBeta)) pack.bb8hBeta = null;
        var st = bb8dStore();
        if (st && st.chat) st.bb8nNonEq = !k.equity;
      } catch (e) {}
      return pack;
    };
  }
  if (typeof bb8eLead === "function") {
    var bb8nLead0 = bb8eLead;
    bb8eLead = function (pack) {
      var out = bb8nLead0.apply(this, arguments);
      try {
        if (out && pack && pack.bb8nKind && !pack.bb8nKind.equity && typeof out.prompt === "string") {
          out.prompt = out.prompt.replace(" Only the Yahoo Finance line may be called beta; never call the card score or its inputs a beta.", "") +
            " This is not an equity (" + pack.bb8nKind.kind + "): do not mention a beta, a card score or a regime-fit score for it.";
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb8dDrop === "function") {
    var bb8nDrop0 = bb8dDrop;
    bb8dDrop = function (sent) {
      try { var st = bb8dStore(); if (st && ((st.chat && st.bb8nNonEq) || st.bb8nNonEqSym) && bb8nRestates(sent)) return true; } catch (e) {}
      return bb8nDrop0.apply(this, arguments);
    };
  }
  if (typeof bb8kApplyHints === "function") {
    var bb8nApply0 = bb8kApplyHints;
    bb8kApplyHints = function (body) {
      try { if (body && typeof body.context === "string") body.context = bb8nContext(body.context); } catch (e) {}
      try {
        // Symbol-only (no network) flag, set before any data fetch, so the restatement filter also holds when the
        // move pack is late or missing and the answer is the model text alone.
        var tk = body && Array.isArray(body.tickers) && body.tickers.length === 1 ? body.tickers[0] : "";
        if (!tk && body && typeof body.context === "string") { var mt = body.context.match(/Active ticker:\s*([A-Za-z0-9.^=\-]{1,15})/); if (mt) tk = mt[1]; }
        var ks = tk ? bb8nKindBySymbol(String(tk)) : null;
        var st2 = bb8dStore();
        if (st2 && ks) st2.bb8nNonEqSym = true;
      } catch (e) {}
      return bb8nApply0.apply(this, arguments);
    };
  }
  if (typeof bb8jAssemble === "function") {
    var bb8nAssemble0 = bb8jAssemble;
    bb8jAssemble = function (reply, store) {
      var out = bb8nAssemble0.apply(this, arguments);
      try {
        if (out && typeof out.reply === "string") {
          var st = store || null;
          var list = Array.isArray(out.sources) ? out.sources : (st && Array.isArray(st.bb8jSources) ? st.bb8jSources : null);
          var p = bb8nPrune(out.reply, list);
          if (p) {
            out.reply = p.reply;
            if (p.sources) { out.sources = p.sources; if (st) st.bb8jSources = p.sources.slice(); }
          }
        }
      } catch (e) {}
      return out;
    };
  }
} catch (e) { console.warn("bb8n hooks skipped", e && e.message); }
// BB8N_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8n")]
if bad:
    die("bb8n block declares a non-bb8n function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8n block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8n function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8n block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8n replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8n setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8nbak"
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
print("APPLY bb8n no beta/card score for non-equities; Sources list only what is cited, renumbered")
