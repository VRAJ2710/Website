#!/usr/bin/env python3
"""patch_bb3_ask.py — follow-up to live bb2 (chat58, server 2e04b3c1).

Root of the 9.3s first paint: bb2StreamInner awaits Yahoo (up to 900ms) before
writeHead. On a cold in-memory cache that wait returns nothing, so the lead is
empty and the first visible text is the model. This patch opens the SSE
response before any quote fetch. A cached snapshot, stale included, is the
first event and names its as-of. A cold fetch runs in the background of this
request (no cron). The status line "Fetching latest valuations." is not the
answer. The model starts at once, in parallel with that fetch.

generateAi does not stream. It POSTs without stream:true, reads response.json(),
and returns choices[0].message.content. Google there is :generateContent, not
the SSE endpoint. The Ask stream does not call generateAi. It calls bb2OpenAi
(gpt-4o-mini, stream:true, one delta per SSE line) and, on failure, bb2Gemini
(streamGenerateContent?alt=sse, one part per event). Timeouts stay 20s, in that
order. Those calls already deliver tokens as they arrive. Two things still hid
them: the cold path waited up to 800ms for Yahoo before bb2Complete, and the
pump held every partial until a sentence ended. Non-comparison tokens are now
written as they arrive. A partial that names a ticker and a number, or a P/E,
stays held until the sentence boundary, then the same validator runs.

Peer and valuation questions drop context lines that do not name the ticker or
a peer (generic headlines, the regime essay, the brief, the portfolio). The
authoritative comparison block stays. Other questions keep their context.

The held-sentence matcher treated the newline before a replaced sentence as
part of that sentence, so the replacement was glued on: "(90.2%).Trailing…".
A decimal point at the end of a chunk was also a false boundary. Separators
stay outside the replacement, and a "." between digits is not a sentence end.

Comparisons are one block, one line per peer, including INTC when trailing P/E
was not reported. Later restatements, including a model bullet list, are dropped.
Peer and valuation questions cite only sources that name the ticker or its
peers, then renumber. Other questions keep the supplied sources.

Does not edit regime-fit or chokepoint code, and does not change app.js or
index.html, so the cache buster stays wherever rt53 left it. Requires chatNN
with NN >= 58 and the bb2 markers. Already-applied exits 0.

Usage: python3 patch_bb3_ask.py [--check] <dir with app.js, index.html, server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

# Live bb2 base (pre-bb2 files with patch_bb2.py applied). A blank value skips
# the warning. Mismatch warns and does not abort, so an rt53 bust still applies.
EXPECTED_MD5 = {
    "app.js": "86153acc103ab9bd246fbdf96055ffab",
    "index.html": "4a680ac27bde0eb044944767ac6838c6",
    "server.js": "2e04b3c16f8400dc5ea211e676831b23",
}

CHECK = "--check" in sys.argv
args = [a for a in sys.argv[1:] if a != "--check"]
D = args[0] if args else "."
APP, IDX, SRV = os.path.join(D, "app.js"), os.path.join(D, "index.html"), os.path.join(D, "server.js")

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
    print("bb3 %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
    return digest

def encode(text, use_crlf):
    return (text.replace("\n", "\r\n") if use_crlf else text).encode("utf-8")

s, crlf = load(APP)
h, hcrlf = load(IDX)
v, vcrlf = load(SRV)

for path in (APP, IDX, SRV):
    digest = show("before", path)
    expect = EXPECTED_MD5.get(os.path.basename(path)) or ""
    if expect and digest != expect:
        print("WARN md5 %s: have %s expected %s (anchors still decide)" % (os.path.basename(path), digest, expect))

if "// \u2500\u2500 bb3 \u2500\u2500" in v:
    print("REFUSE: bb3 already applied")
    sys.exit(0)

miss = []
if "// \u2500\u2500 bb2 \u2500\u2500" not in s:
    miss.append("app.js marker missing: // ── bb2 ──")
if "// \u2500\u2500 bb2 \u2500\u2500" not in v:
    miss.append("server.js marker missing: // ── bb2 ──")
chat_hits = re.findall(r'app\.js\?v=chat(\d+)"', h)
chat_n = None
if len(chat_hits) != 1:
    miss.append('index.html marker missing: app.js?v=chatNN" (found %d)' % len(chat_hits))
else:
    chat_n = int(chat_hits[0])
    if chat_n < 58:
        miss.append("index.html is chat%d; need chat58 or later" % chat_n)
anchors = [
    "async function bb2StreamInner(",
    "function bb2Finish(",
    "function bb2Rewrite(",
    "function bb2ClientSources(",
    "function bb2Lead(",
    "if (!user || !hasPremiumAccess(user))",
]
for anchor in anchors:
    if v.count(anchor) != 1:
        miss.append("server.js anchor %r matched %d times" % (anchor, v.count(anchor)))
if miss:
    print("ABORT (nothing written):")
    for item in miss:
        print("ABORT:", item)
    sys.exit(1)
print("index chat%d unchanged" % chat_n)

BLOCK = r'''
// ── bb3 ── First SSE byte before Yahoo. One comparison block. Relevant citations only.
// BB3_JS
function bb3Next(buf, force) {
  var lead = 0;
  while (lead < buf.length && /\s/.test(buf.charAt(lead))) lead++;
  var i = lead;
  while (i < buf.length) {
    var c = buf.charAt(i);
    if (c === "." || c === "!" || c === "?") {
      var prev = i > 0 ? buf.charAt(i - 1) : "";
      var next = i + 1 < buf.length ? buf.charAt(i + 1) : "";
      var decimal = c === "." && /\d/.test(prev) && (/\d/.test(next) || (next === "" && !force));
      if (!decimal) {
        if (next === "" && !force) return null;
        if (next !== "" && !/\s/.test(next)) { i++; continue; }
        var j = i + 1;
        while (j < buf.length && /\s/.test(buf.charAt(j))) j++;
        return { prefix: buf.slice(0, lead), sentence: buf.slice(lead, i + 1), sep: buf.slice(i + 1, j), rest: buf.slice(j) };
      }
    }
    i++;
  }
  if (force && buf.length) return { prefix: "", sentence: buf, sep: "", rest: "" };
  return null;
}
function bb3Fix(sentence, facts) {
  var s = String(sentence || "");
  var nl = s.lastIndexOf("\n");
  if (nl >= 0) return s.slice(0, nl + 1) + bb3Fix(s.slice(nl + 1), facts);
  var fixed = typeof bb2FixSentence === "function" ? bb2FixSentence(s, facts) : s;
  return typeof bb2Scrub === "function" ? bb2Scrub(fixed) : fixed;
}
function bb3Restates(sentence, facts) {
  var s = String(sentence || "");
  if (!facts || !facts.length) return false;
  for (var n = 0; n < facts.length; n++) {
    var f = facts[n];
    if (!f || !f.a || !f.b) continue;
    var hasA = new RegExp("\\b" + f.a + "\\b").test(s);
    var hasB = new RegExp("\\b" + f.b + "\\b").test(s);
    if (hasA && hasB && (/\b(higher|lower|above|below|cheaper|richer|premium|discount)\b/i.test(s) || /p\/e|multiple/i.test(s))) return true;
    if (f.dir === "missing" && (hasA || hasB) && /not reported/i.test(s)) return true;
  }
  return false;
}
function bb3Rewrite(text, facts, drop) {
  var buf = String(text || ""), out = "";
  function take(force) {
    var part = bb3Next(buf, force);
    if (!part) return false;
    if (part.rest === buf) return false;
    if (drop && bb3Restates(part.sentence, facts)) out += part.prefix + part.sep;
    else out += part.prefix + bb3Fix(part.sentence, facts) + part.sep;
    buf = part.rest;
    return true;
  }
  var guard = 0;
  while (buf && take(false)) { if (++guard > 10000) break; }
  if (buf) take(true);
  return out;
}
function bb3LeadText(built, cite) {
  var facts = (built && built.facts) || [];
  var lines = [];
  facts.forEach(function (f) { if (f && f.sentence) lines.push(f.sentence); });
  if (!lines.length) return "";
  var head = built.asOf ? "Peer comparisons as of " + built.asOf + ":" : "Peer comparisons:";
  if (cite) head += " [" + cite + "]";
  return head + "\n" + lines.join("\n") + "\n\n";
}
function bb3Tickers(body) {
  var q = typeof bb2Question === "function" ? bb2Question(body) : "";
  var peer = typeof bb2PeerAsk === "function" ? bb2PeerAsk(q) : false;
  var list = [];
  function add(t) {
    t = String(t || "").toUpperCase();
    if (!t || !/^[A-Z][A-Z0-9.\-]{0,9}$/.test(t) || list.indexOf(t) >= 0) return;
    list.push(t);
  }
  var base = typeof bb2Base === "function" ? bb2Base(q) : null;
  if (base) {
    add(base);
    var peers = (typeof BB2_PEERS !== "undefined" && BB2_PEERS && BB2_PEERS[base]) || [];
    peers.forEach(add);
  }
  if (body && Array.isArray(body.tickers)) body.tickers.forEach(add);
  return { q: q, peer: peer, tickers: list };
}
function bb3Mentions(source, tickers) {
  var blob = ((source && source.name) || "") + " " + ((source && source.detail) || "") + " " + ((source && source.link) || "");
  blob = blob.toUpperCase();
  for (var i = 0; i < tickers.length; i++) {
    if (new RegExp("\\b" + tickers[i].replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(blob)) return true;
  }
  return false;
}
function bb3FilterSources(sources, body) {
  var info = bb3Tickers(body);
  var out = [];
  (sources || []).forEach(function (src) {
    if (!src) return;
    if (bb3Mentions(src, info.tickers)) out.push(src);
    else if (!info.peer) out.push(src);
  });
  return out;
}
function bb3Compose(reply, built, cite) {
  var facts = (built && built.facts) || [];
  var text = bb3Rewrite(String(reply || "").replace(/\n+Sources:[\s\S]*$/i, ""), facts, true);
  text = text.replace(/Peer comparisons as of [^\n]*\n/g, "").replace(/^Peer comparisons:\n/gm, "");
  text = text.replace(/Fetching latest valuations\.\n*/g, "");
  text = text.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
  if (facts.length) {
    var lead = bb3LeadText(built, cite).trim();
    return (lead + (text ? "\n\n" + text : "")).trim();
  }
  if (text) return text.trim();
  return /Fetching latest valuations\./.test(String(reply || "")) ? "Fetching latest valuations." : "";
}
function bb3ReadCache(syms) {
  var out = {}, any = false;
  (syms || []).forEach(function (sym) {
    var hit = bb2Mem && bb2Mem.vals && bb2Mem.vals.get(sym);
    if (hit && hit.v) { out[sym] = hit.v; any = true; }
  });
  return any ? out : null;
}
function bb3Hold(text, facts) {
  var s = String(text || "");
  if (!s) return false;
  if (/p\/e|multiple|trailing|forward|\bttm\b|not reported/i.test(s)) return true;
  if (/\b(higher|lower|above|below|cheaper|richer|premium|discount)\b/i.test(s)) return true;
  if (/\b[A-Z]{2,5}\b/.test(s) && /\d/.test(s)) return true;
  if (/\d\.$/.test(s)) return true;
  if (facts && facts.length) {
    for (var n = 0; n < facts.length; n++) {
      var f = facts[n];
      if (!f) continue;
      if ((f.a && new RegExp("\\b" + f.a + "\\b").test(s)) || (f.b && new RegExp("\\b" + f.b + "\\b").test(s))) return true;
    }
  }
  return false;
}
function bb3TrimBody(body) {
  var info = bb3Tickers(body);
  if (!info.peer || !body || typeof body.context !== "string" || !body.context) return body;
  var tickers = info.tickers;
  var lines = body.context.split("\n");
  var kept = [], inHeads = false, keepFollow = false;
  lines.forEach(function (line) {
    var t = line.trim();
    if (/^Latest headlines:/i.test(t)) { inHeads = true; keepFollow = false; return; }
    if (inHeads) {
      if (!t) { inHeads = false; return; }
      if (/^[•\-] /.test(t) || /^\[[^\]]+\]/.test(t)) {
        if (bb3Mentions({ name: t, detail: t, link: "" }, tickers)) kept.push(t);
        return;
      }
      inHeads = false;
    }
    if (!t) { keepFollow = false; return; }
    var mention = bb3Mentions({ name: t, detail: "", link: "" }, tickers);
    var peerHead = /peer valuation/i.test(t);
    var follow = keepFollow && /^(Financials:|Earnings:|Live price:)/i.test(t);
    if (mention || peerHead || follow) {
      kept.push(line);
      keepFollow = /^(Active ticker:|Peer valuations)/i.test(t);
    } else keepFollow = false;
  });
  var ctx = kept.join("\n").replace(/\n{3,}/g, "\n\n").trim().slice(0, 1600);
  var next = {};
  Object.keys(body).forEach(function (k) { next[k] = body[k]; });
  next.context = ctx;
  return next;
}
async function bb3StreamInner(req, res) {
  var t0 = Date.now();
  var user = await currentUser(req);
  if (!user || !hasPremiumAccess(user)) return json(res, 401, { error: "Premium membership required" });
  var body = await bb2Read0(req);
  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no"
  });
  if (typeof res.flushHeaders === "function") { try { res.flushHeaders(); } catch (e) {} }
  if (res.socket && typeof res.socket.setNoDelay === "function") { try { res.socket.setNoDelay(true); } catch (e2) {} }
  var firstAt = 0, modelAt = 0;
  function send(obj, kind) {
    res.write("data: " + JSON.stringify(obj) + "\n\n");
    if (typeof res.flush === "function") { try { res.flush(); } catch (e) {} }
    if (!firstAt && obj && obj.t) firstAt = Date.now();
    if (kind === "model" && obj && obj.t && !modelAt) modelAt = Date.now();
  }
  var info = bb3Tickers(body);
  var base = info.peer ? (typeof bb2Base === "function" ? bb2Base(info.q) : null) : null;
  var syms = base ? [base].concat((typeof BB2_PEERS !== "undefined" && BB2_PEERS && BB2_PEERS[base]) || []).slice(0, 6) : [];
  var built = null;
  var vals = syms.length ? bb3ReadCache(syms) : null;
  if (vals && typeof bb2BuildFacts === "function") built = bb2BuildFacts(base, vals);
  var sources = bb2ClientSources(body);
  function addYahoo() {
    if (!(built && built.facts && built.facts.length) || typeof bb2PeerSource !== "function") return 0;
    if (!sources.some(function (src) { return src && src.name === "Yahoo Finance"; })) sources.push(bb2PeerSource(base, built));
    return sources.length;
  }
  var cite = addYahoo();
  var facts = built && built.facts ? built.facts : [];
  var lead = bb3LeadText(built, cite);
  var acc = "";
  if (lead) { acc += lead; send({ t: lead }, "lead"); }
  else if (base) { var note = "Fetching latest valuations.\n\n"; acc += note; send({ t: note }, "status"); }
  var pendingLead = null;
  if (syms.length && typeof bb2Refresh === "function") {
    var job = null;
    try { job = bb2Refresh(syms); } catch (e) { job = null; }
    if (job && typeof job.then === "function") {
      if (!built) {
        pendingLead = Promise.race([
          job.then(function () { return "up"; }).catch(function () { return "up"; }),
          new Promise(function (r) { setTimeout(function () { r("slow"); }, 800); })
        ]).then(function (up) {
          if (up !== "up") { if (typeof job.catch === "function") job.catch(function () {}); return; }
          vals = bb3ReadCache(syms);
          if (!(vals && typeof bb2BuildFacts === "function")) return;
          built = bb2BuildFacts(base, vals);
          facts = built.facts || [];
          cite = addYahoo();
          lead = bb3LeadText(built, cite);
          if (lead) { acc += lead; send({ t: lead }, "lead"); }
        });
      } else if (typeof job.catch === "function") job.catch(function () {});
    }
  }
  var store = (typeof bb2Als !== "undefined" && bb2Als && bb2Als.getStore) ? bb2Als.getStore() : null;
  if (store) {
    store.facts = facts;
    store.bb3Built = built || { facts: facts, asOf: built && built.asOf || "" };
    store.clientSources = sources.filter(function (src) { return !(src && src.name === "Yahoo Finance"); });
    store.peerSource = (sources.length && sources[sources.length - 1] && sources[sources.length - 1].name === "Yahoo Finance") ? sources[sources.length - 1] : null;
    store.body = body;
  }
  var buf = "";
  function pump(force) {
    while (buf) {
      var part = bb3Next(buf, false);
      if (!part) break;
      buf = part.rest;
      if (bb3Restates(part.sentence, facts)) continue;
      var piece = part.prefix + bb3Fix(part.sentence, facts) + part.sep;
      acc += piece;
      send({ t: piece }, "model");
    }
    if (force && buf) {
      var last = bb3Next(buf, true);
      buf = "";
      if (last && !bb3Restates(last.sentence, facts)) {
        var tail = last.prefix + bb3Fix(last.sentence, facts) + last.sep;
        acc += tail;
        send({ t: tail }, "model");
      }
    } else if (buf && !bb3Hold(buf, facts)) {
      var open = buf;
      buf = "";
      acc += open;
      send({ t: open }, "model");
    }
  }
  var meta = { provider: "Dispatch", model: "comparison" };
  try {
    var askBody = bb3TrimBody(body);
    var system = typeof bb2System === "function" ? bb2System(askBody, built, sources) : "";
    meta = await bb2Complete(system, askBody && askBody.messages, function (d) { buf += d; pump(false); });
  } catch (e) {
    if (!acc.trim()) { send({ error: "unavailable" }); res.end(); console.warn("bb3 chat provider miss", Date.now() - t0); return; }
  }
  if (pendingLead) { try { await pendingLead; } catch (e2) {} }
  pump(true);
  if (store) store.facts = facts;
  var citeN = store && store.peerSource ? (store.clientSources.length + 1) : 0;
  var reply = bb3Compose(acc, store && store.bb3Built, citeN);
  var footSources = [];
  if (store && Array.isArray(store.clientSources)) footSources.push.apply(footSources, store.clientSources);
  if (store && store.peerSource) footSources.push(store.peerSource);
  reply += typeof bb2Footer === "function" ? bb2Footer(footSources) : "";
  var srcAt = reply.indexOf("\n\nSources:");
  if (srcAt < 0) srcAt = reply.indexOf("\nSources:");
  if (srcAt >= 0 && acc.indexOf("Sources:") < 0) send({ t: reply.slice(srcAt) });
  send({ done: true, reply: reply, meta: { provider: meta.provider, model: meta.model, streamed: true }, sources: footSources });
  res.end();
  console.warn("bb3 chat ttft_ms", (firstAt || Date.now()) - t0, "model_ttft_ms", modelAt ? modelAt - t0 : -1, "total_ms", Date.now() - t0);
}
try {
  var bb3Client0 = bb2ClientSources;
  bb2ClientSources = function (body) { return bb3FilterSources(bb3Client0(body), body); };
  bb2Rewrite = function (text, facts) { return bb3Rewrite(text, facts, false); };
  bb2Lead = function (built, cite) { return bb3LeadText(built, cite); };
  bb2Finish = function (reply, store) {
    var facts = (store && store.facts) || [];
    var built = (store && store.bb3Built) || { facts: facts, asOf: "" };
    var cite = store && store.peerSource ? ((store.clientSources || []).length + 1) : 0;
    var text = bb3Compose(reply, built.facts ? built : { facts: facts, asOf: built.asOf || "" }, cite);
    var sources = [];
    if (store && Array.isArray(store.clientSources)) sources.push.apply(sources, store.clientSources);
    if (store && store.peerSource) sources.push(store.peerSource);
    return text + (typeof bb2Footer === "function" ? bb2Footer(sources) : "");
  };
  if (typeof bb2System === "function") {
    var bb3System0 = bb2System;
    bb2System = function (body, built, sources) {
      return bb3System0.call(this, bb3TrimBody(body), built, sources) + "\n\nThe peer comparison lines are already on screen. Do not repeat them as a paragraph or as bullets. Do not restate a peer P/E. Add only other context.";
    };
  }
  bb2StreamInner = bb3StreamInner;
} catch (e) { console.warn("bb3 hooks skipped", e && e.message); }
// BB3_JS_END
'''

v = v.rstrip("\n") + "\n" + BLOCK
print("APPLY ask first byte, one comparison block, relevant sources")

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
after = encode(v, vcrlf)
show("after", APP)
show("after", IDX)
show("after", SRV, after)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb3bak"
try:
    open(bak, "wb").write(open(SRV, "rb").read())
    open(SRV, "wb").write(after)
    r = subprocess.run(["node", "--check", SRV], capture_output=True, text=True)
    if r.returncode:
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
        print("ABORT: node --check failed after write; backup restored:", r.stderr[:400])
        sys.exit(1)
    os.unlink(bak)
except Exception as e:
    if os.path.exists(bak):
        open(SRV, "wb").write(open(bak, "rb").read())
        os.unlink(bak)
    print("ABORT: write failed; backup restored:", e)
    sys.exit(1)
print("written", SRV)
