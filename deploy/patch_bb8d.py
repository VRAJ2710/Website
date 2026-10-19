#!/usr/bin/env python3
"""patch_bb8d.py — Ask: server-built "In short" conclusion; whole-sentence cleanup; UK time in Ask text and quote notes. Server.js only.
Stacked on bb8c (server md5 2d807112acf22009af0fa09da742f94c). Does not rewrite app.js or index.html.
1) /api/chat with peer comparison lines, both the SSE stream (done.reply, the text the client keeps) and the JSON
   handler: the reply is rebuilt as lead block + cleaned model body + a deterministic, neutral conclusion built from
   the comparison facts ("In short: on next-12-month earnings MU is the cheapest of its peers at 4.9x, against
   13.6-45.2x; ..."). The conclusion is appended after every filter and never passes through one. The model body is
   taken from the raw model text (not the stream-rewritten text), split into sentences with bracket awareness, and
   only whole sentences are dropped: model conclusions, "different bases" and dead-end lines, buy/sell, undervalued or
   opportunity wording, filler, unbalanced brackets, fragments, and P/E figures absent from the comparison lines.
   The stream rewrite no longer inserts the "different bases" sentence into a partial sentence.
2) Timestamps in Ask text (lead block, Sources footer, prompt citations, live market block) and quote notes
   ("updated ...", "opens ...") use UK time, Europe/London: "Fri 16 Oct, 21:00 UK". JSON ts/asOf values unchanged.
No tables, intervals, dependencies, secrets or Stripe changes.
Usage: python3 patch_bb8d.py [--check] <dir with server.js>
"""
import hashlib, os, re, sys, subprocess, tempfile

EXPECTED_MD5 = {
    "app.js": "843c42b73f671d80c6e563d2edddb829",
    "index.html": "07137d3795c694d726cb9a295719849e",
    "server.js": "2d807112acf22009af0fa09da742f94c",
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
    print("bb8d %s %s md5=%s lines=%d" % (phase, name, digest, len(raw.splitlines())))
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
        print("bb8d before %s missing (not required, not written)" % label)
        continue
    got = show("before", label, blob)
    exp = EXPECTED_MD5.get(label) or ""
    if exp and got != exp:
        print("WARN md5 %s: have %s expected %s (file is not modified)" % (label, got, exp))
    else:
        print("bb8d %s untouched" % label)

if "// \u2500\u2500 bb8d \u2500\u2500" in v:
    print("REFUSE: bb8d already applied")
    sys.exit(0)

REQUIRED = [
    ("bb8c marker", "// \u2500\u2500 bb8c \u2500\u2500"),
    ("bb3LeadText", "function bb3LeadText(built, cite) {"),
    ("bb3bCompose", "function bb3bCompose(reply, built, cite) {"),
    ("bb2Complete", "async function bb2Complete(system, messages, onDelta) {"),
    ("bb2Footer", "function bb2Footer(sources) {"),
    ("bb2FixSentence", "function bb2FixSentence(sentence, facts) {"),
    ("bb5eLondon", "function bb5eLondon(ms, now) {"),
    ("bb5hHm", "function bb5hHm(ms) {"),
    ("buildChatLiveMarketBlock", "async function buildChatLiveMarketBlock("),
    ("bb8cAllowed", "function bb8cAllowed(facts) {"),
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
print("bb8d anchors ok x%d" % len(REQUIRED))

BLOCK = r"""
// ── bb8d ── Ask: server-built "In short" conclusion appended after every filter; whole-sentence, bracket-aware cleanup;
// UK-time ("Fri 16 Oct, 21:00 UK") for every timestamp in Ask text and quote notes. Machine JSON fields unchanged.
// BB8D_JS
var BB8D_TZ = "Europe/London";
function bb8dUkMs(ms) {
  var d = new Date(Number(ms));
  if (!isFinite(d.getTime())) return "";
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: BB8D_TZ, weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
      .formatToParts(d).forEach(function (p) { parts[p.type] = p.value; });
    return parts.weekday + " " + parts.day + " " + parts.month + ", " + parts.hour + ":" + parts.minute;
  } catch (e) { return ""; }
}
function bb8dUk(ms) { var s = bb8dUkMs(ms); return s ? s + " UK" : ""; }
function bb8dParse(s) {
  var m = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::(\d{2})(?:\.\d{1,3})?)?\s?(Z|UTC|GMT|[+-]\d{2}:?\d{2})$/.exec(String(s || "").trim());
  if (!m) return NaN;
  var zone = m[4] === "UTC" || m[4] === "GMT" ? "Z" : (/^[+-]\d{4}$/.test(m[4]) ? m[4].slice(0, 3) + ":" + m[4].slice(3) : m[4]);
  return Date.parse(m[1] + "T" + m[2] + ":" + (m[3] || "00") + zone);
}
function bb8dUkText(text) {
  return String(text == null ? "" : text).replace(/\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?\s?(?:Z|UTC|GMT|[+-]\d{2}:?\d{2})(?!\w)/g, function (m) {
    var ms = bb8dParse(m);
    var s = isFinite(ms) ? bb8dUk(ms) : "";
    return s || m;
  });
}
// Bracket-aware sentence split: never splits inside (), [], or at a decimal point; splits run-on joins like "forward).Trailing".
function bb8dSplit(line) {
  var s = String(line || ""), out = [], cur = "", depth = 0;
  for (var i = 0; i < s.length; i++) {
    var ch = s.charAt(i);
    cur += ch;
    if (ch === "(" || ch === "[") depth++;
    else if ((ch === ")" || ch === "]") && depth > 0) depth--;
    else if ((ch === "." || ch === "!" || ch === "?") && depth === 0) {
      var nx = s.charAt(i + 1), pv = s.charAt(i - 1);
      if (ch === "." && /\d/.test(pv) && /\d/.test(nx)) continue;
      if (ch === "." && /[A-Z]/.test(pv) && !/[A-Za-z]/.test(s.charAt(i - 2) || "")) continue;
      if (nx === "" || /\s/.test(nx) || /[A-Z"'(\[*]/.test(nx)) {
        while (i + 1 < s.length && /[.!?"')\]*]/.test(s.charAt(i + 1)) && depth === 0) { if (/[)\]]/.test(s.charAt(i + 1))) break; cur += s.charAt(++i); }
        out.push(cur); cur = "";
      }
    }
  }
  if (cur) out.push(cur);
  return out.map(function (x) { return x.trim(); }).filter(Boolean);
}
function bb8dBalanced(s) {
  var p = 0, b = 0;
  for (var i = 0; i < s.length; i++) {
    var c = s.charAt(i);
    if (c === "(") p++; else if (c === ")") { if (--p < 0) return false; }
    else if (c === "[") b++; else if (c === "]") { if (--b < 0) return false; }
  }
  if (p || b) return false;
  if (((s.match(/\*\*/g) || []).length % 2) !== 0) return false;
  if (((s.match(/"/g) || []).length % 2) !== 0) return false;
  return true;
}
function bb8dIsFact(line) {
  return /^\s*[A-Z][A-Z0-9.\-]{0,9}\s+(?:trailing|forward)\s+P\/E\b[\s\S]*\b(?:is (?:lower|higher) than|is in line with)\b/.test(line) ||
    /^\s*[A-Z][A-Z0-9.\-]{0,9}\s+(?:trailing|forward)\s+P\/E\b[\s\S]*\bwas not reported, so\b/.test(line);
}
function bb8dDrop(sent, ok, facts) {
  var s = String(sent || "").replace(/^\s*(?:[-*•]|\d+[.)])\s+/, "").trim();
  if (!s) return true;
  if (/^(?:\*\*)?\s*(?:in\s+)+(?:short|conclusion|summary|sum)\b/i.test(s)) return true;
  if (/^(?:\*\*)?\s*(?:in short|in conclusion|in summary|in sum|to sum(?:marise|marize| up)?|summing up|overall|to conclude|conclusion|bottom line|summary|net[- ]net)\b/i.test(s)) return true;
  if (/different bases|not (?:be )?compared|\bcannot\b|\bcan ?not\b|\bcan't\b|\bunable to\b|not possible|insufficient|no (?:direct |meaningful )?comparison|apples[- ]to[- ]apples/i.test(s)) return true;
  if (/\b(?:undervalued|overvalued|under-valued|over-valued|opportunit\w*|bargain|buy(?:ing)?|sell(?:ing)?|price targets?|upside|downside|should (?:consider|look)|worth (?:buying|owning))\b/i.test(s)) return true;
  if (typeof bb8bFillerRe === "function") { try { var fr = bb8bFillerRe(); fr.lastIndex = 0; var fm = s.match(new RegExp(fr.source, "i")); if (fm && fm[0].trim().length > 12) return true; } catch (e) {} }
  if (!bb8dBalanced(s)) return true;
  if (/\btrailing\b|\bTTM\b/i.test(s) && /\bforward\b/i.test(s) && /\d(?:\.\d+)?\s*[x×]/.test(s)) return true;
  // A sentence the comparison checker would rewrite (wrong direction, or trailing compared with forward) is dropped whole.
  if (facts && facts.length && typeof bb8dFix0 === "function") { try { if (bb8dFix0(s, facts) !== s) return true; } catch (e) {} }
  var words = s.split(/\s+/).filter(Boolean).length;
  if (words < 4) return true;
  // An unterminated piece is kept only if it reads as a full sentence (long enough, not ending mid-phrase).
  if (!/[.!?:)"'*]$/.test(s) && (words < 8 || /(?:'s|’s|\b(?:the|a|an|and|or|of|to|is|are|was|at|in|on|for|with|than|its|their|but))$/i.test(s))) return true;
  if (/\bP\/E\b|\bmultiple\b|\bearnings\b|\bvaluation\b/i.test(s)) {
    var nums = s.match(/\d+(?:\.\d+)?(?=\s*[x×])/g) || [];
    for (var k = 0; k < nums.length; k++) if (!ok[Number(nums[k]).toFixed(1)]) return true;
  }
  return false;
}
function bb8dCleanLine(line, ok, facts) {
  var t = String(line || "").trim();
  if (!t || /^Peer comparisons\b/i.test(t) || bb8dIsFact(t) || /^(?:\*\*)?Sources?:/i.test(t)) return "";
  var pre = (/^\s*(?:[-*•]|\d+[.)])\s+/.exec(line) || [""])[0];
  var sents = bb8dSplit(String(line).slice(pre.length)).filter(function (x) { return !bb8dDrop(x, ok, facts); }).map(function (x) {
    x = x.trim();
    return /[.!?:)"'*]$/.test(x) ? x : x + ".";
  });
  if (!sents.length) return "";
  return pre.trim() ? pre.trim() + " " + sents.join(" ") : sents.join(" ");
}
function bb8dBody(raw, facts) {
  var ok = typeof bb8cAllowed === "function" ? bb8cAllowed(facts) : {};
  var s = String(raw == null ? "" : raw);
  s = s.replace(/(?:^|\n)\s*(?:\*\*)?Sources?:?(?:\*\*)?:?[\s\S]*$/i, "").replace(/\s*\bSources:\s*\[\d+\][\s\S]*$/i, "");
  s = s.replace(/Fetching latest valuations\.\s*/g, "");
  var lines = s.split("\n"), keep = [];
  lines.forEach(function (line) {
    if (!line.trim()) { keep.push(""); return; }
    var c = bb8dCleanLine(line, ok, facts);
    if (c) keep.push(c);
  });
  return keep.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}
function bb8dRange(vals) {
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
  return lo === hi ? lo.toFixed(1) + "x" : lo.toFixed(1) + "–" + hi.toFixed(1) + "x";
}
function bb8dList(a) { return a.length <= 1 ? (a[0] || "") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1]; }
// Deterministic, neutral conclusion from the peer comparison facts.
function bb8dConclusion(built) {
  var facts = (built && Array.isArray(built.facts) ? built.facts : []).filter(Boolean);
  if (!facts.length) return "";
  var base = (built && built.base) || facts[0].a;
  var clauses = [], notes = [];
  ["forward", "trailing"].forEach(function (basis) {
    var label = basis === "forward" ? "on next-12-month earnings" : "on trailing earnings (TTM)";
    var pe = basis === "forward" ? "forward P/E" : "trailing P/E (TTM)";
    var va = null, lower = [], higher = [], level = [], miss = [], baseMissing = false;
    facts.forEach(function (f) {
      if (f.basis !== basis) return;
      if (f.dir === "missing") {
        var who = String(f.sentence || "").split(" ")[0];
        if (who === base) baseMissing = true; else if (who && miss.indexOf(who) < 0) miss.push(who);
        return;
      }
      va = f.va;
      if (f.dir === "lower") lower.push(f); else if (f.dir === "higher") higher.push(f); else level.push(f);
    });
    if (baseMissing && va == null) { notes.push(base + "'s " + pe + " isn't reported"); return; }
    var n = lower.length + higher.length + level.length;
    if (va == null || !n) { if (miss.length) notes.push(pe + " isn't reported for " + bb8dList(miss)); return; }
    var v = Number(va).toFixed(1) + "x";
    var syms = function (arr) { return arr.map(function (f) { return f.b; }); };
    var vals = function (arr) { return arr.map(function (f) { return Number(f.vb); }); };
    var c;
    if (lower.length === n) c = label + " " + base + " is the cheapest of its peers at " + v + ", against " + bb8dRange(vals(lower));
    else if (higher.length === n) c = label + " " + base + " is the most expensive of its peers at " + v + ", against " + bb8dRange(vals(higher));
    else if (level.length === n) c = label + " " + base + " is in line with its peers at " + v;
    else {
      var bits = [];
      if (lower.length) bits.push("below " + bb8dList(syms(lower)) + " (" + bb8dRange(vals(lower)) + ")");
      if (higher.length) bits.push("above " + bb8dList(syms(higher)) + " (" + bb8dRange(vals(higher)) + ")");
      if (level.length) bits.push("in line with " + bb8dList(syms(level)));
      c = label + " " + base + " sits in the middle of its peers at " + v + ": " + bits.join(", ");
    }
    clauses.push(c);
    if (miss.length) notes.push(bb8dList(miss) + (miss.length > 1 ? "' " : "'s ") + pe + (miss.length > 1 ? " aren't" : " isn't") + " reported");
  });
  var all = clauses.concat(notes);
  if (!all.length) return "";
  return "In short: " + all.join("; ") + ".";
}
function bb8dStore() { try { return typeof bb2Als !== "undefined" && bb2Als && bb2Als.getStore ? bb2Als.getStore() : null; } catch (e) { return null; } }
function bb8dAsOf(built) {
  if (built && built.asOf) return built.asOf;
  var best = 0;
  try {
    (built && built.facts || []).forEach(function (f) {
      [f && f.a, f && f.b].forEach(function (s) { var h = s && bb2Mem && bb2Mem.vals && bb2Mem.vals.get(s); if (h && h.v && h.v.marketMs > best) best = h.v.marketMs; });
    });
  } catch (e) {}
  return best ? bb8dUk(best) : "";
}
try {
  if (typeof bb2Complete === "function") {
    var bb8dComplete0 = bb2Complete;
    bb2Complete = function (system, messages, onDelta) {
      var st = bb8dStore();
      if (st) st.bb8dRaw = "";
      // Paint only whole, cleaned sentences while streaming; the raw text is kept for the final reply.
      var pend = "", stop = false;
      var paint = function (force) {
        var facts = st && Array.isArray(st.facts) ? st.facts : [];
        if (!facts.length) { if (pend) { var all = pend; pend = ""; onDelta(all); } return; }
        if (stop) { pend = ""; return; }
        var ok = typeof bb8cAllowed === "function" ? bb8cAllowed(facts) : {};
        var out = "";
        var nl = pend.lastIndexOf("\n");
        if (nl >= 0) {
          pend.slice(0, nl).split("\n").forEach(function (line) {
            if (stop) return;
            if (/^\s*(?:\*\*)?Sources?:/i.test(line)) { stop = true; return; }
            var c = line.trim() ? bb8dCleanLine(line, ok, facts) : "";
            out += c ? c + "\n" : (line.trim() ? "" : "\n");
          });
          pend = pend.slice(nl + 1);
        }
        if (!stop && pend) {
          if (/^\s*(?:\*\*)?Sources?:/i.test(pend)) { if (force) stop = true; }
          else {
            var parts = bb8dSplit(pend);
            var done = force ? parts : parts.slice(0, -1);
            if (done.length) {
              var c2 = bb8dCleanLine(done.join(" "), ok, facts);
              if (c2) out += c2 + " ";
              if (force) pend = "";
              else { var last = parts[parts.length - 1] || "", at = last ? pend.lastIndexOf(last) : -1; pend = at >= 0 ? pend.slice(at) : last; }
            }
            if (force) pend = "";
          }
        }
        if (out) onDelta(out);
      };
      var p = bb8dComplete0.call(this, system, messages, function (d) {
        try { if (st && typeof d === "string") { st.bb8dRaw += d; pend += d; paint(false); return; } } catch (e) {}
        return onDelta.apply(this, arguments);
      });
      return Promise.resolve(p).then(function (r) { try { paint(true); } catch (e) {} return r; });
    };
  }
  if (typeof bb3bCompose === "function") {
    var bb8dCompose0 = bb3bCompose;
    bb3bCompose = function (reply, built, cite) {
      var facts = built && Array.isArray(built.facts) ? built.facts : [];
      if (!facts.length) return bb8dUkText(bb8dCompose0.call(this, reply, built, cite));
      var st = bb8dStore();
      var raw = st && typeof st.bb8dRaw === "string" ? st.bb8dRaw : String(reply == null ? "" : reply);
      var b2 = Object.assign({}, built, { asOf: bb8dAsOf(built) });
      var lead = typeof bb3LeadText === "function" ? bb8dUkText(bb3LeadText(b2, cite)).trim() : "";
      if (b2.asOf && !built.asOf) lead = lead.replace(/^Peer comparisons:/, "Peer comparisons as of " + b2.asOf + ":");
      var body = bb8dUkText(bb8dBody(raw, facts));
      var verdict = bb8dConclusion(b2);
      // The verdict is appended last and never passes through a filter.
      return [lead, body, verdict].filter(function (x) { return x && x.trim(); }).join("\n\n");
    };
  }
  if (typeof bb3LeadText === "function") {
    var bb8dLead0 = bb3LeadText;
    bb3LeadText = function () { return bb8dUkText(bb8dLead0.apply(this, arguments)); };
  }
  if (typeof bb2Footer === "function") {
    var bb8dFooter0 = bb2Footer;
    bb2Footer = function (sources) { return bb8dUkText(bb8dFooter0.apply(this, arguments)); };
  }
  if (typeof bb2System === "function") {
    var bb8dSystem0 = bb2System;
    bb2System = function () {
      return bb8dUkText(bb8dSystem0.apply(this, arguments)) + "\n\nDo not write a concluding or summary sentence; the server adds it. Write times as UK time.";
    };
  }
  if (typeof buildChatLiveMarketBlock === "function") {
    var bb8dLive0 = buildChatLiveMarketBlock;
    buildChatLiveMarketBlock = async function () { return bb8dUkText(await bb8dLive0.apply(this, arguments)); };
  }
  if (typeof bb2FixSentence === "function") {
    var bb8dFix0 = bb2FixSentence;
    bb2FixSentence = function (sentence, facts) {
      var out = bb8dFix0.apply(this, arguments);
      return out !== sentence && /different bases and are not compared/.test(out) ? "" : out;
    };
  }
  if (typeof bb5eLondon === "function") bb5eLondon = function (ms) { return bb8dUkMs(ms); };
  if (typeof bb5hHm === "function") bb5hHm = function (ms) { return bb8dUkMs(ms); };
} catch (e) { console.warn("bb8d hooks skipped", e && e.message); }
// BB8D_JS_END
"""

declared = re.findall(r"(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(", BLOCK)
bad = [name for name in declared if not name.startswith("bb8d")]
if bad:
    die("bb8d block declares a non-bb8d function: %s" % ", ".join(bad))
counts = {}
for name in declared:
    counts[name] = counts.get(name, 0) + 1
dupes = [name for name, n in counts.items() if n > 1]
if dupes:
    die("bb8d block repeats a function: %s" % ", ".join(dupes))
clash = [name for name in declared if re.search(r"(?m)^(?:async\s+)?function\s+" + re.escape(name) + r"\s*\(", v)]
if clash:
    die("bb8d function already declared in server.js: %s" % ", ".join(clash))
if "CREATE TABLE" in BLOCK or "setInterval(" in BLOCK or "stripe.webhooks" in BLOCK or ".tier" in BLOCK:
    die("bb8d block has a forbidden declaration")

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
print("bb8d setInterval( count=%d CREATE TABLE count=%d" % (v.count("setInterval("), v.count("CREATE TABLE")))
after_srv = encode(v, vcrlf)
show("after", "server.js", after_srv)
if app_before is not None:
    show("after", "app.js", app_before)
if idx_before is not None:
    show("after", "index.html", idx_before)
if CHECK:
    print("dry run, nothing written")
    sys.exit(0)

bak = SRV + ".bb8dbak"
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
print("APPLY bb8d server-built conclusion + UK time")
