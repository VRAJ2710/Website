#!/usr/bin/env python3
"""patch_bb8q2.py — P0 follow-up to bb8q (Jack's calls): Yahoo DX-Y.NYB, labelled "US Dollar Index (ICE, Yahoo
DX-Y.NYB)", is the dollar index on every server output (reference route DXY with price/change/changePct/prevClose/
asOf/asOfUk/label/source, gold desk, regime input, Ask context, JSON live block); the FX-computed index is labelled
"Dispatch FX basket" wherever it stays (DXY_FX, fallback); UK no-data line names UK CPI / UK gilt yields; after a
cold start (no spot previous close; no free keyless spot history exists) every gold answer and the XAU quote carry
gold futures' own day change, labelled and cited (futuresChange), never borrowed into spot's fields.
Server.js only. Stacked on bb8q (live server md5 b4f66c896a13a73fb03656386c4ae802). Does not rewrite app.js or index.html.
No tables, intervals, timers, dependencies, secrets or billing changes. See docs/bb8q2.md.
Usage: python3 patch_bb8q2.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "b4f66c896a13a73fb03656386c4ae802",
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
    print("bb8q2 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8q2 before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8q2 %s untouched" % label)

if "// \u2500\u2500 bb8q2 \u2500\u2500" in v:
    print("REFUSE: bb8q2 already applied")
    sys.exit(0)

REPLACE = [
]
REQUIRED = [
    ("bb8q end", "// BB8Q_JS_END"),
    ("bb8qBuild", "async function bb8qBuild(st, body) {"),
    ("bb8qNoData", "function bb8qNoData(doc, st, ctx) {"),
    ("bb8qRender", "function bb8qRender(doc) {"),
    ("bb8qTok", "function bb8qTok(doc, src) {"),
    ("bb8qSt", "function bb8qSt() {"),
    ("bb8qVerb", "function bb8qVerb(pct, closed, dp) {"),
    ("bb8qTfSym", "function bb8qTfSym(st, topic, gold) {"),
    ("bb8qSrc", "function bb8qSrc(name, link, ms, detail, key) {"),
    ("bb8qSrcText", "var bb8qSrcText = new WeakMap();"),
    ("BB8Q_MACRO", "var BB8Q_MACRO = ["),
    ("bb8q DXY label", '{ sym: "DX-Y.NYB", label: "US Dollar Index (DXY)"'),
    ("bb8pQuoteMeta", "function bb8pQuoteMeta(st) {"),
    ("bb8pTopicLabel", "function bb8pTopicLabel(topic) {"),
    ("BB8P_TOPICS", "var BB8P_TOPICS = ["),
    ("marketReferenceQuotes", "async function marketReferenceQuotes() {"),
    ("fetchSyntheticDxy", "async function fetchSyntheticDxy() {"),
    ("yahooQuote", "async function yahooQuote(symbols) {"),
    ("bb3Pack", "async function bb3Pack(now) {"),
    ("bb3OneQuote", "async function bb3OneQuote(pack, yahooSym) {"),
    ("buildChatLiveMarketBlock", "async function buildChatLiveMarketBlock() {"),
    ("live block DXY line", "lines.push(`US Dollar Index DXY ${f(dx.p)}"),
    ("bb8Late", "function bb8Late(ms) {"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
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
print("bb8q2 anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8q2 ── DXY is Yahoo DX-Y.NYB everywhere (the FX-computed index is labelled "Dispatch FX basket"), UK gilt
// wording in the no-data line, and a cited gold move after a cold start.
// Jack's calls (Mon 19 Oct 2026, after bb8q):
// * DXY: Yahoo DX-Y.NYB, labelled "US Dollar Index (ICE, Yahoo DX-Y.NYB)", is the dollar index on every server
//   output: /api/market-reference-quotes DXY (with price, change, changePct, prevClose, asOf, asOfUk, label,
//   source), the gold desk snapshot, the regime model's dollar input, Ask's shared context and the JSON route's live
//   block. The FX-computed index stays only as DXY_FX on the reference route and as a fallback, labelled
//   "Dispatch FX basket".
// * UK: proxies only; the no-data line says "We don't carry UK CPI or UK gilt yields in our data feed right now"
//   (gilt wording whenever the question touches gilts, yields or UK rates).
// * Gold spot change after a restart: gold-api.com's /history and /ohlc need an x-api-key (401 without one, free
//   tier 10 requests/hour), Yahoo has no spot symbol (XAUUSD=X and XAU=X are delisted), freegoldapi.com's daily file
//   ends 2026-02-20 and is futures-based, Swissquote's public feed has bid/ask only and LBMA blocks the request.
//   No free keyless spot previous close was found, so spot keeps its own previous close only after a UK day roll (bb8q),
//   and until then every answer and the XAU quote carry gold futures' own day change, labelled
//   ("gold futures (GC=F) +0.08% today"), cited to the futures source. Never borrowed into spot's fields.
// BB8Q2_JS
var BB8Q2_DXY = "US Dollar Index (ICE, Yahoo DX-Y.NYB)";
var BB8Q2_FX = "Dispatch FX basket";
var BB8Q2_MS = 2500;
var BB8Q2_RATES = /\b(?:gilts?|yields?|interest rates?|rates? (?:cuts?|hikes?|rises?|decisions?|path|outlook)|(?:bank|base|policy) rate|BoE|bank of england|MPC|bonds?)\b/i;
var BB8Q2_FUT = "Gold futures (GC=F, delayed 10 min)";

function bb8q2Race(p) {
  var dl = typeof bb8Late === "function" ? bb8Late(BB8Q2_MS) : null;
  var safe = Promise.resolve(p).catch(function () { return null; });
  return dl ? Promise.race([safe, dl.then(function () { return null; })]) : safe;
}
function bb8q2Ice(x) {
  if (!x || !(Number(x.p) > 0)) return null;
  var p = Number(x.p), prev = Number(x.prev) > 0 ? Number(x.prev) : null, ms = bb8qMs(x) || Date.now();
  var o = Object.assign({}, x, {
    symbol: "DX-Y.NYB", name: BB8Q2_DXY, label: BB8Q2_DXY, exchange: "ICE", source: "Yahoo Finance (DX-Y.NYB)", proxy: false,
    price: p, prevClose: prev, prev: prev, change: prev ? p - prev : null, changePct: prev ? (p / prev - 1) * 100 : null,
    asOf: bb8qIso(ms), asOfUk: bb8qUk(ms), changeAvailable: prev != null
  });
  o.c = o.changePct;
  return o;
}
function bb8q2Fx(x) {
  if (!x || !(Number(x.p) > 0)) return x;
  var ms = bb8qMs(x) || Date.now(), prev = Number(x.prev) > 0 ? Number(x.prev) : null;
  return Object.assign({}, x, {
    symbol: "DISPATCH-FX", name: BB8Q2_FX, label: BB8Q2_FX, price: Number(x.p), prevClose: prev,
    change: x.change != null ? x.change : null, changePct: x.c != null ? x.c : null, asOf: bb8qIso(ms), asOfUk: bb8qUk(ms),
    note: "our own index computed from six FX rates; not the ICE US Dollar Index"
  });
}
function bb8q2Pct(p, prev) { return Number(p) > 0 && Number(prev) > 0 ? (Number(p) / Number(prev) - 1) * 100 : null; }
function bb8q2Signed(pct) { return (pct < 0 ? "-" : "+") + Math.abs(pct).toFixed(2) + "%"; }
function bb8q2FutChange(price, prev, ms) {
  var pct = bb8q2Pct(price, prev);
  if (pct == null) return null;
  return {
    symbol: "GC=F", label: BB8Q2_FUT, price: Number(price), prevClose: Number(prev), change: Number((Number(price) - Number(prev)).toFixed(2)),
    changePct: Number(pct.toFixed(4)), asOf: bb8qIso(ms || Date.now()), asOfUk: bb8qUk(ms || Date.now()), source: "Yahoo Finance", delayMin: 10,
    text: "gold futures (GC=F) " + bb8q2Signed(pct) + " today"
  };
}
// XAU on the reference route: spot fields stay spot; futuresChange is the labelled fallback move.
function bb8q2GoldFill(x, gq) {
  if (!x || typeof x !== "object") return x;
  var o = Object.assign({}, x);
  var gp = gq && Number(gq.p) > 0 ? Number(gq.p) : null, gprev = gq && Number(gq.prev) > 0 ? Number(gq.prev) : null, gms = gq ? bb8qMs(gq) : 0;
  if (gp && !o.futures) o.futures = { symbol: "GC=F", label: BB8Q2_FUT, price: gp, dayHigh: null, dayLow: null, asOf: bb8qIso(gms), source: "Yahoo Finance" };
  if (o.futures && gprev) { o.futures = Object.assign({}, o.futures, { prevClose: gprev, changePct: Number(bb8q2Pct(o.futures.price, gprev).toFixed(4)), asOfUk: bb8qUk(Date.parse(o.futures.asOf) || gms), delayMin: 10 }); }
  if (!o.changeAvailable) {
    var fc = o.futures && gprev ? bb8q2FutChange(o.futures.price, gprev, Date.parse(o.futures.asOf) || gms) : null;
    o.futuresChange = fc;
    o.changeNote = fc ? "No spot previous close yet: show futuresChange with its label, never as spot's change." : "No spot or futures previous close available.";
  } else o.futuresChange = null;
  return o;
}
// UK no-data wording
function bb8q2UkParts(topic) {
  if (!topic || topic.mode !== "topic" || !topic.entities || !topic.entities.some(function (e) { return e.id === "uk"; })) return null;
  var ids = (topic.series || []).map(function (s) { return s.id; }), out = [];
  if (ids.indexOf("inflation") >= 0) out.push(["UK CPI", "CPI"]);
  if (ids.indexOf("gdp") >= 0) out.push(["UK GDP figures", "GDP"]);
  if (ids.indexOf("jobs") >= 0) out.push(["UK jobs data", "jobs"]);
  if (ids.indexOf("gilts") >= 0 || ids.indexOf("rates") >= 0 || BB8Q2_RATES.test(String(topic.q || ""))) out.push(["UK gilt yields", "gilt"]);
  return out.length ? out : null;
}
function bb8q2Join(a) { return a.length === 1 ? a[0] : a.slice(0, -1).join(", ") + " or " + a[a.length - 1]; }
// The gold spot line once spot has no previous close: the reader still gets today's move, from futures, labelled.
async function bb8q2GoldCtx(ctx, st) {
  if (!ctx || !ctx.spot || !ctx.spot.q) return;
  if (ctx.spot.q.changeAvailable) {
    // one bracket: "(previous close $x; gold-api.com, as of ...)"
    var tidy = function (x) { return String(x).replace(/\) \(gold-api\.com, as of /, "; gold-api.com, as of "); };
    ctx.spot.text = tidy(ctx.spot.text);
    ctx.facts.forEach(function (f) { if (f.id === "spot") f.text = tidy(f.text); });
    if (ctx.spot.src) { ctx.spot.src.detail = tidy(ctx.spot.src.detail); try { bb8qSrcText.set(ctx.spot.src, ctx.spot.src.detail); } catch (e) {} }
    return;
  }
  var pack = typeof bb3Pack === "function" ? await bb8q2Race(bb3Pack(Date.now())) : null;
  var gq = pack && typeof bb3OneQuote === "function" ? await bb8q2Race(bb3OneQuote(pack, "GC=F")) : null;
  var sp = Number(ctx.spot.q.p), uk = bb8qUk(ctx.spot.ms), head = "Gold spot is at $" + bb8qNum(sp, 2) + " (gold-api.com, as of " + uk + ")";
  var price = ctx.fut && ctx.fut.sn && Number(ctx.fut.sn.goldLast) > 0 ? Number(ctx.fut.sn.goldLast) : gq && Number(gq.p) > 0 ? Number(gq.p) : null;
  var prev = gq && Number(gq.prev) > 0 ? Number(gq.prev) : null, pct = bb8q2Pct(price, prev);
  if (pct != null && !ctx.fut) {
    var fms = bb8qMs(gq) || Date.now();
    var ftx = BB8Q2_FUT + " " + bb8qVerb(pct, false).replace(/^is /, "are ") + " at $" + bb8qNum(price, 2) + " (previous close $" + bb8qNum(prev, 2) + "), as of " + bb8qUk(fms) + ".";
    var fsrc = bb8qSrc("Yahoo Finance quote", bb8qLink("GC=F"), fms, ftx.replace(/\.$/, ""), "futures");
    ctx.fut = { sn: { goldLast: price, goldTs: Math.floor(fms / 1000) }, text: ftx, windows: "", src: fsrc };
    ctx.facts.push({ id: "futures", text: ftx, src: fsrc }); ctx.sources.push(fsrc);
  }
  var fact;
  ctx.spot.head = head;
  if (pct != null) {
    bb8q2SpotMove(ctx, price, prev);
    ctx.spot.liveText = head + "; spot has no previous close in our feed yet, so the day's move shown is gold futures'";
    fact = head + "; spot has no previous close in our feed yet, so today's move is the gold futures (GC=F) change.";
  } else {
    ctx.spot.text = head + "; neither our spot feed nor our futures feed has a previous close right now, so today's move is not available.";
    fact = ctx.spot.text;
  }
  ctx.facts.forEach(function (f) { if (f.id === "spot") f.text = fact; });
  if (ctx.spot.src) { ctx.spot.src.detail = fact.replace(/\.$/, ""); try { bb8qSrcText.set(ctx.spot.src, ctx.spot.src.detail); } catch (e) {} }
}
function bb8q2SpotMove(ctx, price, prev) {
  var pct = bb8q2Pct(price, prev);
  if (pct == null || !ctx.spot || !ctx.spot.head) return;
  ctx.spot.futMove = { pct: pct, prev: prev, price: price, text: "gold futures (GC=F) " + bb8q2Signed(pct) + " today" };
  ctx.spot.text = ctx.spot.head + "; spot has no previous close in our feed yet, so today's move comes from gold futures (GC=F, delayed 10 min), " + (Math.abs(pct) < 0.005 ? "unchanged" : (pct < 0 ? "down " : "up ") + Math.abs(pct).toFixed(2) + "%") + " today.";
}
function bb8q2Esc(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
try {
  // (1) DXY labels in the shared context and the JSON route's live block
  if (typeof BB8Q_MACRO !== "undefined") BB8Q_MACRO.forEach(function (m) { if (m.sym === "DX-Y.NYB") m.label = BB8Q2_DXY; });
  if (typeof fetchSyntheticDxy === "function") {
    var bb8q2Fx0 = fetchSyntheticDxy;
    fetchSyntheticDxy = async function () { var q = await bb8q2Fx0.apply(this, arguments); try { return q && typeof q === "object" ? Object.assign({}, q, { name: BB8Q2_FX, label: BB8Q2_FX }) : q; } catch (e) { return q; } };
  }
  // the regime model's dollar input: DX-Y.NYB when Yahoo has it, else the labelled FX basket
  if (typeof bb3Pack === "function") {
    var bb8q2Pack0 = bb3Pack;
    bb3Pack = async function () {
      var p = await bb8q2Pack0.apply(this, arguments);
      try {
        if (p && typeof p === "object" && !p.bb8q2) {
          var ice = bb8q2Ice(p.quotes && p.quotes["DX-Y.NYB"]);
          p.dxyFx = p.dxy ? bb8q2Fx(p.dxy) : null;
          if (ice) { p.dxy = ice; p.dxySrc = "ice"; } else if (p.dxy) { p.dxy = bb8q2Fx(p.dxy); p.dxySrc = "fx"; }
          p.bb8q2 = true;
        }
      } catch (e) {}
      return p;
    };
  }
  if (typeof marketReferenceQuotes === "function") {
    var bb8q2Ref0 = marketReferenceQuotes;
    marketReferenceQuotes = async function () {
      var out = await bb8q2Ref0.apply(this, arguments);
      try {
        if (!out || typeof out !== "object") return out;
        var yq = typeof yahooQuote === "function" ? await bb8q2Race(yahooQuote(["DX-Y.NYB", "GC=F"])) : null;
        var ice = bb8q2Ice(yq && yq["DX-Y.NYB"]);
        var fx = out.DXY && out.DXY.symbol !== "DX-Y.NYB" ? bb8q2Fx(out.DXY) : null;
        if (fx) out.DXY_FX = fx;
        if (ice) out.DXY = ice;
        else if (fx) out.DXY = Object.assign({}, fx, { fallback: true, fallbackReason: "Yahoo DX-Y.NYB unavailable; this is the Dispatch FX basket" });
        if (out.XAU) out.XAU = bb8q2GoldFill(out.XAU, yq && yq["GC=F"]);
      } catch (e) {}
      return out;
    };
  }
  if (typeof buildChatLiveMarketBlock === "function") {
    var bb8q2Blk0 = buildChatLiveMarketBlock;
    buildChatLiveMarketBlock = async function () {
      var s = await bb8q2Blk0.apply(this, arguments);
      return typeof s === "string" ? s.replace(/US Dollar Index DXY(?=[ :])/g, BB8Q2_DXY) : s;
    };
  }
  // (2) UK: gilts are a series we do not carry
  if (typeof BB8P_TOPICS !== "undefined" && !BB8P_TOPICS.some(function (t) { return t.id === "gilts"; })) {
    BB8P_TOPICS.push({ id: "gilts", kind: "series", label: "UK gilt yield", re: /\b(?:gilts?|gilt yields?|UK (?:2|5|10|30)[- ]?(?:y|yr|year)s?|UK (?:bond |government bond )?yields?)\b/i });
  }
  if (typeof bb8pTopicLabel === "function") {
    var bb8q2Lab0 = bb8pTopicLabel;
    bb8pTopicLabel = function (topic) {
      try { var u = bb8q2UkParts(topic); if (u) return bb8q2Join(u.map(function (x) { return x[0]; })); } catch (e) {}
      return bb8q2Lab0.apply(this, arguments);
    };
  }
  if (typeof bb8qNoData === "function") {
    var bb8q2Nd0 = bb8qNoData;
    bb8qNoData = function (doc, st, ctx) {
      // a second pass sees the original wording, so bb8q's own de-duplication still applies
      try {
        doc.body = String(doc.body).replace(/(^|\n)We don't carry /g, "$1We don't have ")
          .replace(/(^|\n)(What we do have, from Yahoo Finance as of [^\n]*? UK), as market proxies \(not [^)]*\):/g, "$1$2:")
          .replace(/(^|\n)A related yield, not a gilt yield: [^\n]*/g, "");
      } catch (e) {}
      var r = bb8q2Nd0.apply(this, arguments);
      try {
        var u = bb8q2UkParts(ctx && ctx.topic);
        if (u) {
          var not = bb8q2Join(u.map(function (x) { return x[1]; })) + " data";
          doc.body = doc.body.replace(/(^|\n)(What we do have, from Yahoo Finance as of [^\n]*? UK):/, "$1$2, as market proxies (not " + not + "):");
          if (u.some(function (x) { return x[1] === "gilt"; })) {
            var tn = (ctx.facts || []).filter(function (f) { return f.id === "^TNX"; })[0];
            var y = tn ? /\bis (\d+(?:\.\d+)?)%/.exec(tn.text) : null;
            if (tn && y) {
              // inside the proxy line, so the brief trim keeps it
              var bit = "the US 10-year Treasury yield (^TNX), a related yield but not a gilt yield, is " + y[1] + "% " + bb8qTok(doc, tn.src);
              var lines = doc.body.split("\n"), done = false;
              for (var i = 0; i < lines.length; i++) if (/^What we do have, from Yahoo Finance/.test(lines[i])) { lines[i] = lines[i].replace(/\.\s*$/, "") + "; " + bit + "."; done = true; }
              if (!done) lines.splice(1, 0, "", "What we do have, from Yahoo Finance: " + bit + ".");
              doc.body = lines.join("\n");
            }
          }
        }
      } catch (e) {}
      return r;
    };
  }
  // a dollar question's timeframe change is the dollar index's own
  if (typeof bb8qTfSym === "function") {
    var bb8q2TfSym0 = bb8qTfSym;
    bb8qTfSym = function (st, topic, gold) {
      try { if (!gold && !(st && st.bb8eBase) && topic && topic.entities && topic.entities.some(function (e) { return e.id === "dollar"; })) return "DX-Y.NYB"; } catch (e) {}
      return bb8q2TfSym0.apply(this, arguments);
    };
  }
  // the stream paints the UK opener with the same wording as the final reply
  if (typeof bb2Complete === "function") {
    var bb8q2Complete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      try {
        var st = bb8qSt(), u = st && st.bb8qCtx ? bb8q2UkParts(st.bb8qCtx.topic) : null;
        if (u && typeof onDelta === "function") {
          var od = onDelta;
          arguments[2] = function (d) { if (typeof d === "string") d = d.replace(/^We don't have (UK )/, "We don't carry $1"); return od.call(this, d); };
        }
      } catch (e) {}
      return bb8q2Complete0.apply(this, arguments);
    };
  }
  // (3) gold move after a cold start, and the regime's dollar input named
  if (typeof bb8qBuild === "function") {
    var bb8q2Build0 = bb8qBuild;
    bb8qBuild = async function (st, body) {
      var ctx = await bb8q2Build0.apply(this, arguments);
      try {
        var pk = typeof bb3Pack === "function" ? await bb8q2Race(bb3Pack(Date.now())) : null;
        var dn = pk && pk.dxySrc === "fx" ? "the dollar (" + BB8Q2_FX + ")" : "the " + BB8Q2_DXY;
        (ctx && ctx.facts || []).forEach(function (f) {
          if (f.id !== "regime") return;
          f.text = f.text.replace("the dollar index", dn);
          if (f.src) { f.src.detail = String(f.src.detail).replace("dollar index", dn.replace(/^the /, "")); try { bb8qSrcText.set(f.src, f.src.detail); } catch (e) {} }
        });
        if (ctx && ctx.tf) {
          var dx = ctx.tf.sym === "DX-Y.NYB";
          var fixTf = function (x) { return String(x).replace(dx ? /\$(?=\d)/g : /(?!)/g, "").replace(/, DX-Y\.NYB (is|are) /g, ", the " + BB8Q2_DXY + " $1 ").replace(/\b(is|are) (?:down|up) 0\.00%/g, "$1 unchanged"); };
          ctx.tf.text = fixTf(ctx.tf.text);
          if (ctx.tfMore) ctx.tfMore = ctx.tfMore.map(fixTf);
          ctx.facts.forEach(function (f) { if (f.src === ctx.tf.src) f.text = ctx.tf.text; });
          if (ctx.tf.src) { ctx.tf.src.detail = fixTf(ctx.tf.src.detail); try { bb8qSrcText.set(ctx.tf.src, ctx.tf.src.detail); } catch (e) {} }
        }
        await bb8q2GoldCtx(ctx, st);
      } catch (e) {}
      return ctx;
    };
  }
  // every gold spot line that carries the futures move also cites the futures source
  if (typeof bb8qRender === "function") {
    var bb8q2Render0 = bb8qRender;
    bb8qRender = function (doc) {
      try {
        var st0 = bb8qSt(), u0 = st0 && st0.bb8qCtx ? bb8q2UkParts(st0.bb8qCtx.topic) : null;
        if (doc && u0) doc.body = String(doc.body).replace(/(^|\n)We don't have (UK )/, "$1We don't carry $2");
      } catch (e) {}
      try {
        var st = bb8qSt(), ctx = st && st.bb8qCtx;
        if (doc && ctx && ctx.spot && ctx.spot.futMove && ctx.fut && ctx.fut.src) {
          var t = ctx.spot.text.replace(/\.$/, ""), ft = bb8qTok(doc, ctx.fut.src);
          var re = new RegExp(bb8q2Esc(t) + "(\\.?[ \\t]*)((?:\\u27e6\\d+\\u27e7[ \\t]*)*)", "g");
          doc.body = String(doc.body).split("\n").map(function (l) {
            if (/^\s*Live: /.test(l) && ctx.spot.liveText) return l.replace(t, ctx.spot.liveText);
            return l.replace(re, function (m, gap, toks) {
              if (toks.indexOf(ft) >= 0) return m;
              var tail = (toks.match(/[ \t]*$/) || [""])[0];
              return t + (gap || " ") + toks.replace(/[ \t]*$/, "") + ft + tail;
            });
          }).join("\n");
        }
      } catch (e) {}
      return bb8q2Render0.apply(this, arguments);
    };
  }
  if (typeof bb8eLead === "function") {
    var bb8q2Lead0 = bb8eLead;
    bb8eLead = function (pack, card, n0) {
      try {
        var st = bb8qSt(), c = st && st.bb8qCtx, q = pack && pack.q;
        if (c && c.spot && c.spot.futMove && pack.ysym === "GC=F" && q && Number(q.p) > 0 && Number(q.prev) > 0) bb8q2SpotMove(c, Number(q.p), Number(q.prev));
      } catch (e) {}
      return bb8q2Lead0.apply(this, arguments);
    };
  }
  // Ask meta.quote: the same futuresChange fallback field
  if (typeof bb8pQuoteMeta === "function") {
    var bb8q2Qm0 = bb8pQuoteMeta;
    bb8pQuoteMeta = function (st) {
      var q = bb8q2Qm0.apply(this, arguments);
      try {
        var c = st && st.bb8qCtx;
        if (q && q.symbol === "XAU" && c && c.spot) {
          var fm = c.spot.futMove;
          if (q.futures && fm && q.futures.prevClose == null) { q.futures.prevClose = fm.prev; q.futures.changePct = Number(fm.pct.toFixed(4)); }
          if (!q.changeAvailable) {
            q.futuresChange = fm ? bb8q2FutChange(fm.price, fm.prev, c.fut && c.fut.sn ? Number(c.fut.sn.goldTs) * 1000 : Date.now()) : null;
            q.changeNote = q.futuresChange ? "No spot previous close yet: show futuresChange with its label, never as spot's change." : "No spot or futures previous close available.";
          } else q.futuresChange = null;
        }
      } catch (e) {}
      return q;
    };
  }
} catch (e) { console.warn("bb8q2 hooks skipped", e && e.message); }
// BB8Q2_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8q2")]
if bad:
    die("bb8q2 block declares a non-bb8q2 function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8q2 block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8q2 function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "setTimeout(" in BLOCK or "stripe" in BLOCK.lower() or ".tier" in BLOCK or "process.env" in BLOCK:
    die("bb8q2 block has a forbidden declaration")

for a, b in REPLACE:
    v = v.replace(a, b, 1)
    print("bb8q2 replaced in place: %s" % a.strip().splitlines()[0][:70])
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
print("bb8q2 setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8q2bak"
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
print("APPLY bb8q2 DXY = Yahoo DX-Y.NYB everywhere (FX basket labelled), UK CPI/gilt no-data wording, cited gold futures move after a cold start")
