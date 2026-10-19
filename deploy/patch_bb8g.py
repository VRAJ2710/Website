#!/usr/bin/env python3
"""patch_bb8g.py — source labels from publisher/host; cited, fact-based card answers with a server "In short:";
valuation answers without restated peer figures. Server.js only.
Stacked on bb8g (server md5 b9f30e995bc43d97738b839abf9cf3e3). Does not rewrite app.js or index.html.
(a) Every Ask source is labelled from its publisher field when present, otherwise from the link's host
    (friendly name, e.g. stocktwits.com -> Stocktwits, reuters.com -> Reuters; unknown hosts show the bare host).
    A generic or Yahoo label is never kept on a link that is not on Yahoo. /api/ticker-news items whose link is not
    on Yahoo carry the host's publisher as source/publisher (via: "Yahoo Finance RSS").
(b) Card/move answers: the card-score line and a new server beta line (from the card's own inputs) are cited with
    a "The Dispatch" source. A model sentence with no valid [n] and no figure from the fact lines is dropped whole
    (bb8d splitter), streamed and final. The prompt asks the model to cite every claim. A deterministic
    "In short:" line (move, gap to the benchmark, market mood, "no confirmed cause") is appended after the filters.
(c) Valuation answers: model sentences that restate a peer line (same ticker + same multiple, a listed
    comparison with a peer, or a listed "not reported") are dropped; the prompt says not to restate.
Citations stay consistent: the Sources list matches the cited [n], renumbered 1..n.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8g.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "b9f30e995bc43d97738b839abf9cf3e3",
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
    print("bb8g %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8g before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8g %s untouched" % label)

if "// \u2500\u2500 bb8g \u2500\u2500" in v:
    print("REFUSE: bb8g already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8f end", "// BB8F_JS_END"),
    ("bb8e marker", "// \u2500\u2500 bb8e \u2500\u2500"),
    ("bb8eLead", "function bb8eLead(pack, card, n0) {"),
    ("bb8eVerb", "function bb8eVerb(c, closed) {"),
    ("bb8eFull", "function bb8eFull(st) {"),
    ("bb8dDrop", "function bb8dDrop(sent, ok, facts) {"),
    ("bb8dStore", "function bb8dStore() {"),
    ("bb2System", "function bb2System(body, built, sources) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
    ("generateAi", "async function generateAi("),
    ("bb3bCompose", "function bb3bCompose(reply, built, cite) {"),
    ("bb2Footer", "function bb2Footer(sources) {"),
    ("bb2ClientSources", "function bb2ClientSources(body) {"),
    ("json", "function json(res, status, body, extraHeaders = {}) {"),
    ("rt37s source", 'summary: g("description").slice(0, 400), source: "Yahoo Finance" });'),
    ("bb3 sensitivity", 'inputs.push(bb3In("sensitivity",'),
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
print("bb8g anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8g ── Source labels from publisher or host; cited, fact-based card answers with a server "In short:";
// valuation answers without restated peer figures.
// BB8G_JS
var BB8G_HOSTS = [
  ["stocktwits.com", "Stocktwits"], ["reuters.com", "Reuters"], ["bloomberg.com", "Bloomberg"], ["finance.yahoo.com", "Yahoo Finance"],
  ["yahoo.com", "Yahoo Finance"], ["wsj.com", "The Wall Street Journal"], ["ft.com", "Financial Times"], ["cnbc.com", "CNBC"],
  ["marketwatch.com", "MarketWatch"], ["barrons.com", "Barron's"], ["bbc.co.uk", "BBC"], ["bbc.com", "BBC"], ["theguardian.com", "The Guardian"],
  ["apnews.com", "AP News"], ["investors.com", "Investor's Business Daily"], ["fool.com", "The Motley Fool"], ["fool.co.uk", "The Motley Fool"],
  ["seekingalpha.com", "Seeking Alpha"], ["zacks.com", "Zacks"], ["benzinga.com", "Benzinga"], ["investopedia.com", "Investopedia"],
  ["businesswire.com", "Business Wire"], ["prnewswire.com", "PR Newswire"], ["globenewswire.com", "GlobeNewswire"], ["accesswire.com", "ACCESSWIRE"],
  ["coindesk.com", "CoinDesk"], ["cointelegraph.com", "Cointelegraph"], ["forbes.com", "Forbes"], ["fortune.com", "Fortune"],
  ["insidermonkey.com", "Insider Monkey"], ["gurufocus.com", "GuruFocus"], ["simplywall.st", "Simply Wall St"], ["investing.com", "Investing.com"],
  ["thestreet.com", "TheStreet"], ["sec.gov", "SEC EDGAR"], ["nasdaq.com", "Nasdaq"], ["techcrunch.com", "TechCrunch"], ["axios.com", "Axios"],
  ["nytimes.com", "The New York Times"], ["economist.com", "The Economist"], ["247wallst.com", "24/7 Wall St."], ["investorplace.com", "InvestorPlace"],
  ["barchart.com", "Barchart"], ["finviz.com", "Finviz"], ["tipranks.com", "TipRanks"], ["morningstar.com", "Morningstar"], ["kiplinger.com", "Kiplinger"],
  ["proactiveinvestors.com", "Proactive Investors"], ["proactiveinvestors.co.uk", "Proactive Investors"], ["thedispatch.uk", "The Dispatch"],
  ["house.gov", "US House Clerk"], ["sky.com", "Sky News"], ["telegraph.co.uk", "The Telegraph"], ["cityam.com", "City A.M."]
];
var BB8G_GENERIC = /^(?:yahoo finance(?: news| rss)?|news|price feed|rss|feed)$/i;
var BB8G_BENCH_NAME = { SPY: "SPY", "^FTSE": "the FTSE 100", "^N225": "the Nikkei 225", "^HSI": "the Hang Seng", "^GDAXI": "the DAX", "^FCHI": "the CAC 40" };
var BB8G_CITE_RULE = "Cite every claim with the [n] of the fact line or source it comes from. Leave out any claim you cannot cite: no guesses about investor positioning, sector rotation or sentiment.";
var BB8G_VAL_RULE = "Do not restate the peer comparison lines or their figures; they are already shown. Add only interpretation, or nothing.";
function bb8gHost(link) {
  try { return new URL(String(link || "")).hostname.toLowerCase().replace(/^www\./, ""); } catch (e) { return ""; }
}
function bb8gHostLabel(link) {
  var h = bb8gHost(link);
  if (!h) return "";
  for (var i = 0; i < BB8G_HOSTS.length; i++) {
    var d = BB8G_HOSTS[i][0];
    if (h === d || h.slice(-(d.length + 1)) === "." + d) return BB8G_HOSTS[i][1];
  }
  return h;
}
// Label: the publisher field when present, else the link's host (friendly name, or the bare host).
function bb8gLabel(src) {
  if (!src || typeof src !== "object") return "";
  var name = String(src.name || "").trim();
  var pub = String(src.publisher || "").trim();
  if (pub) return name && name.toLowerCase().indexOf(pub.toLowerCase()) === 0 ? name : pub;
  if (!src.link) return name;
  var lab = bb8gHostLabel(src.link);
  if (!lab) return name;
  if (name && name.toLowerCase().indexOf(lab.toLowerCase()) === 0) return name;
  if (!name || BB8G_GENERIC.test(name)) return lab;
  if (/yahoo/i.test(name) && !/(^|\.)yahoo\.com$/.test(bb8gHost(src.link))) return lab;
  return name;
}
function bb8gRelabel(list) {
  (list || []).forEach(function (s) { if (s && typeof s === "object") { var l = bb8gLabel(s); if (l) s.name = l.slice(0, 80); } });
  return list;
}
function bb8gNums(text) {
  var out = {};
  String(text || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ").replace(/(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?/g, function (m, a, b) {
    var n = Number(String(a).replace(/,/g, "") + (b ? "." + b : ""));
    if (isFinite(n)) { out[n.toFixed(2)] = 1; out[n.toFixed(1)] = 1; }
    return m;
  });
  return out;
}
function bb8gHasFigure(sent, nums) {
  var mine = bb8gNums(sent), k;
  for (k in mine) if (nums[k]) return true;
  return false;
}
function bb8gCited(sent, max) {
  var hit = false;
  String(sent || "").replace(/\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]/g, function (m, g) { g.split(/\s*,\s*/).forEach(function (x) { var k = Number(x); if (k >= 1 && k <= max) hit = true; }); return m; });
  return hit;
}
// Card / move answers: a model sentence must carry a valid [n] or a figure from the server's fact lines.
function bb8gCardDrop(sent, st) {
  var mv = st && st.bb8eMove;
  if (!mv) return false;
  if (!mv.bb8gNums) mv.bb8gNums = bb8gNums(mv.text);
  var max = typeof bb8eFull === "function" ? bb8eFull(st).length : 0;
  if (bb8gCited(sent, max)) return false;
  return !bb8gHasFigure(sent, mv.bb8gNums);
}
function bb8gEsc(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function bb8gPairs(facts) {
  var pairs = {}, peers = {}, missing = {};
  (facts || []).forEach(function (f) {
    var s = String(f && f.sentence || "");
    if (f && f.b) peers[String(f.b).toUpperCase()] = 1;
    s.replace(/\b([A-Z][A-Z0-9.\-]{0,9})\s+(trailing|forward)\s+P\/E\b[^\d]*?(\d+(?:\.\d+)?)x/g, function (m, t, basis, n) { pairs[t + "|" + Number(n).toFixed(1)] = 1; return m; });
    var nr = /\b([A-Z][A-Z0-9.\-]{0,9})\s+(?:trailing|forward)\s+P\/E\b[^.]*?was not reported/.exec(s);
    if (nr) missing[nr[1]] = 1;
  });
  return { pairs: pairs, peers: peers, missing: missing };
}
// Valuation answers: drop sentences that restate a peer line (same ticker + same multiple, a listed comparison, or a listed gap).
function bb8gRestates(sent, facts) {
  var s = String(sent || "").replace(/\[\d{1,2}(?:\s*,\s*\d{1,2})*\]/g, " ");
  var P = bb8gPairs(facts), k;
  var tick = {};
  s.replace(/\b([A-Z][A-Z0-9.\-]{0,9}?)(?:'s|’s)?(?=[\s,.;:)!?]|$)/g, function (m, t) { tick[t] = 1; return m; });
  var nums = s.match(/\d+(?:\.\d+)?/g) || [];
  for (k in tick) for (var i = 0; i < nums.length; i++) if (P.pairs[k + "|" + Number(nums[i]).toFixed(1)]) return true;
  if (/^\s*(?:it|its|this|that)\b/i.test(s) && nums.some(function (n) { for (var key in P.pairs) if (key.split("|")[1] === Number(n).toFixed(1)) return true; return false; })) return true;
  if (/\b(?:lower|higher|cheaper|richer|more expensive|less expensive|below|above|in line with|discount to|premium to)\b/i.test(s)) {
    for (k in P.peers) if (new RegExp("\\b" + bb8gEsc(k) + "(?:'s|’s)?\\b").test(s)) return true;
  }
  for (k in P.missing) if (new RegExp("\\b" + bb8gEsc(k) + "\\b").test(s) && /not (?:been )?reported|isn't reported|unavailable|not available/i.test(s)) return true;
  return false;
}
function bb8gBeta(fit) {
  var rows = fit && Array.isArray(fit.inputs) ? fit.inputs : [];
  for (var i = 0; i < rows.length; i++) if (rows[i] && rows[i].key === "sensitivity" && rows[i].value != null && isFinite(Number(rows[i].value))) return Number(rows[i].value);
  return null;
}
function bb8gShort(pack) {
  var q = pack.q, c = Number(q.c), base = pack.base;
  var closed = String(q.status || "") === "closed" || /closed/i.test(String(q.note || ""));
  var move = typeof bb8eVerb === "function" ? bb8eVerb(c, closed) : (c < 0 ? "fell " : "rose ") + Math.abs(c).toFixed(2) + "%";
  if (Math.abs(c) < 0.005) move = closed ? "was unchanged" : "is flat";
  var bits = [base + " " + move];
  if (pack.bench && isFinite(Number(pack.bench.q.c))) {
    var d = c - Number(pack.bench.q.c), name = BB8G_BENCH_NAME[pack.bench.sym] || String(pack.bench.sym).replace(/^\^/, "");
    var pts = Math.abs(d).toFixed(2);
    bits.push(pts === "0.00" ? "in line with " + name : pts + " pts " + (d < 0 ? "behind " : "ahead of ") + name);
  } else bits.push("with no market comparison available");
  if (pack.fit && pack.fit.regime) bits.push("in a " + pack.fit.regime + " session");
  return "In short: " + bits.join(", ") + "; no confirmed cause.";
}
function bb8gShortCite(st) {
  var mv = st && st.bb8eMove;
  if (!mv || !mv.bb8gShort) return "";
  var n = mv.bb8gQ, c = st.bb8eCites;
  if (c && c.keep && c.full) {
    var idx = -1;
    for (var i = 0; i < c.full.length; i++) if (c.full[i] === mv.sources[0]) { idx = i; break; }
    var at = idx >= 0 ? c.keep.indexOf(idx) : -1;
    n = at >= 0 ? at + 1 : 0;
  }
  return mv.bb8gShort + (n ? " [" + n + "]" : "");
}
try {
  if (typeof bb8eLead === "function") {
    var bb8gLead0 = bb8eLead;
    bb8eLead = function (pack, card, n0) {
      var out = bb8gLead0.apply(this, arguments);
      try {
        out.sources.forEach(function (src) { if (src && src.name === "Yahoo Finance news" && src.link) { var hl = bb8gHostLabel(src.link); if (hl) src.name = hl; } });
        bb8gRelabel(out.sources);
        var lines = out.text.split("\n"), extra = [];
        if (pack.fit) {
          var m = n0 + out.sources.length + 1, beta = bb8gBeta(pack.fit), asOf = pack.fit.asOf || "";
          out.sources.push({ name: "The Dispatch", link: "https://thedispatch.uk/", asOf: asOf, detail: "Pulse card score (regime fit)" + (beta != null ? " and desk beta" : "") });
          for (var i = 0; i < lines.length; i++) {
            if (/^Card score \(Dispatch regime fit\):/.test(lines[i])) {
              lines[i] = lines[i] + " [" + m + "]";
              if (beta != null) lines.splice(i + 1, 0, "Beta (Dispatch desk reference): " + beta.toFixed(2) + ", so " + pack.base + " tends to move about " + beta.toFixed(2) + " times as much as the market. [" + m + "]");
              break;
            }
          }
        }
        var text = lines.join("\n");
        var factLines = lines.slice(1).join("\n");
        out.prompt = out.prompt.replace(out.text.split("\n").slice(1).join("\n"), factLines) + " " + BB8G_CITE_RULE;
        out.text = text;
        out.paint = text.replace(/\s*\[\d+\]/g, "");
        out.bb8gQ = n0 + 1;
        out.bb8gShort = bb8gShort(pack);
        out.bb8gNums = bb8gNums(text);
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb8dDrop === "function") {
    var bb8gDrop0 = bb8dDrop;
    bb8dDrop = function (sent, ok, facts) {
      if (bb8gDrop0.apply(this, arguments)) return true;
      try {
        if (facts && facts.length) return bb8gRestates(sent, facts);
        var st = bb8dStore();
        if (st && st.bb8eMode === "move" && st.bb8eMove) return bb8gCardDrop(sent, st);
      } catch (e) {}
      return false;
    };
  }
  if (typeof bb2System === "function") {
    var bb8gSystem0 = bb2System;
    bb2System = function (body, built) {
      var s = bb8gSystem0.apply(this, arguments);
      try { if (built && Array.isArray(built.facts) && built.facts.length) s += "\n\n" + BB8G_VAL_RULE; } catch (e) {}
      return s;
    };
  }
  if (typeof generateAi === "function") {
    var bb8gGen0 = generateAi;
    generateAi = async function (options) {
      var args = Array.prototype.slice.call(arguments);
      try {
        var st = bb8dStore();
        if (st && st.chat && options && typeof options.system === "string" && st.bb8eMode === "valuation") args[0] = Object.assign({}, options, { system: BB8G_VAL_RULE + "\n\n" + options.system });
      } catch (e) {}
      return bb8gGen0.apply(this, args);
    };
  }
  if (typeof bb2Complete === "function") {
    var bb8gComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var st = bb8dStore();
      var p = bb8gComplete0.apply(this, arguments);
      if (!st || st.bb8eMode !== "move" || typeof onDelta !== "function") return p;
      return Promise.resolve(p).then(function (r) {
        try {
          var mv = st.bb8eMove;
          if (mv && mv.bb8gShort) { st.bb8eNextSep = "\n\n"; try { onDelta(mv.bb8gShort + "\n"); } finally { st.bb8eNextSep = null; } }
        } catch (e) {}
        return r;
      });
    };
  }
  if (typeof bb3bCompose === "function") {
    var bb8gCompose0 = bb3bCompose;
    bb3bCompose = function (reply, built, cite) {
      var out = bb8gCompose0.apply(this, arguments);
      try {
        var st = bb8dStore(), facts = built && Array.isArray(built.facts) ? built.facts : [];
        if (!facts.length && st && st.bb8eMode === "move" && st.bb8eMove && st.bb8eMove.bb8gShort && String(out).indexOf(st.bb8eMove.bb8gShort) < 0) {
          out = String(out).replace(/\s+$/, "") + "\n\n" + bb8gShortCite(st);
        }
      } catch (e) {}
      return out;
    };
  }
  if (typeof bb2Footer === "function") {
    var bb8gFooter0 = bb2Footer;
    bb2Footer = function (sources) {
      try { bb8gRelabel(sources); } catch (e) {}
      var out = bb8gFooter0.apply(this, arguments);
      try { bb8gRelabel(sources); } catch (e) {}
      return out;
    };
  }
  if (typeof bb2ClientSources === "function") {
    var bb8gClient0 = bb2ClientSources;
    bb2ClientSources = function (body) {
      var out = bb8gClient0.apply(this, arguments);
      try {
        var arr = Array.isArray(body && body.sources) ? body.sources.filter(function (s) { return s && typeof s === "object" && String(s.name || s.src || "").trim(); }) : [];
        out.forEach(function (o, i) { var p = arr[i] && arr[i].publisher; if (typeof p === "string" && p.trim()) o.publisher = p.trim().slice(0, 80); });
      } catch (e) {}
      return out;
    };
  }
  // /api/ticker-news: items carried a fixed "Yahoo Finance" source even when the link is another publisher.
  if (typeof json === "function") {
    var bb8gJson0 = json;
    json = function (res, status, body) {
      try {
        if (body && typeof body === "object" && typeof body.symbol === "string" && Array.isArray(body.items)) {
          body.items.forEach(function (it) {
            if (!it || typeof it !== "object" || !it.link || it.source !== "Yahoo Finance") return;
            var lab = bb8gHostLabel(it.link);
            if (lab && lab !== "Yahoo Finance") { it.publisher = lab; it.source = lab; it.via = "Yahoo Finance RSS"; }
          });
        }
      } catch (e) {}
      return bb8gJson0.apply(this, arguments);
    };
  }
} catch (e) { console.warn("bb8g hooks skipped", e && e.message); }
// BB8G_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8g")]
if bad:
    die("bb8g block declares a non-bb8g function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8g block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8g function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8g block has a forbidden declaration")

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
print("bb8g setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8gbak"
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
print("APPLY bb8g source labels + cited card answers with In short + valuation restatement filter")
