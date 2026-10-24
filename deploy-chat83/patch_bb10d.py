#!/usr/bin/env python3
"""bb10d: QA chat82 server fixes on top of bb10c live.
(1) Crypto Ask figure + citation integrity: every % / price a sentence attaches to a coin must be that coin's Coinbase 24h snapshot
    figure or a figure in a cited source that names that coin and that period; cross-coin comparisons on different bases are rewritten
    to the two snapshot figures (or dropped); every [n] must point at a source that holds the sentence's figure and subject.
    Prompt rule added for crypto Asks. Works on the stream and JSON paths (hooks bb8qFinish after bb10c's post-check).
(2) Transient HTTP 500s: every bb10* request-path wrapper falls back to the original response on any error; the academy-daily
    res.end interception is idempotent, never throws and always ends the response.
Server-only, anchor-based, no timers/tables/secrets.
Usage: python3 patch_bb10d.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
BASE_MD5 = "e5391dbbb4a41e4ddfed1140560973e2"
MARK = "// ── bb10d:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
// ── bb10d: QA chat82 on bb10c live ──
// ── bb10d (1): crypto Ask figure + citation integrity. A % or price a sentence attaches to a coin is that coin's Coinbase snapshot
// figure, or a figure a cited source states for that same coin and that same period. Anything else is removed, never re-attributed. ──
var BB10D_RULE_KEY = "CRYPTO FIGURES (coin-specific):";
var BB10D_RULE = BB10D_RULE_KEY + " a percentage or price written for a named coin may only be that coin's own Coinbase snapshot figure supplied above. Never attach one coin's figure, or a figure from a source about an index, another coin or a headline, to a different coin. A month-to-date, weekly, yearly or other-period figure may be written only if a cited source states it for that same coin and that same period, and the sentence must name both the coin and the period. Do not compare one coin with another coin or an index using figures on different bases; give each coin's own snapshot figure with its own [n]. Cite a [n] only when that source's text holds the figure and the coin named in that sentence.";
var BB10D_PER = [
  ["month", /\b(?:month|monthly|month[- ]to[- ]date|mtd|30-?day|30d)\b/i],
  ["week", /\b(?:week|weekly|7-?day|7d)\b/i],
  ["year", /\b(?:year|yearly|ytd|year[- ]to[- ]date|12-?month|annual\w*)\b/i],
  ["quarter", /\b(?:quarter|quarterly|qtd)\b/i],
  ["since", /\bsince\b/i],
  ["close", /\b(?:previous|prior|last|yesterday'?s?)\s+(?:session'?s?\s+|trading\s+)?close\b|\bfrom (?:the )?\w+ close\b|\bcalendar[- ]day\b/i],
  ["day", /\b(?:24[- ]?h(?:ours?|rs?)?|rolling 24|past day|last day|today|over the day|overnight|past 24|last 24)\b/i]
];
var BB10D_OTHER_RE = /\b(?:S&P(?: 500)?|Nasdaq(?:[- ]100| Composite)?|Dow(?: Jones)?|Russell(?: 2000)?|FTSE(?: 100)?|DAX|Nikkei|Stoxx|VIX|gold|silver|crude|Brent|WTI|oil|dollar index|DXY|US dollar|U\.S\. dollar|Treasur(?:y|ies)|yields?|equities|stocks)\b/gi;
var BB10D_CMP_RE = /\b(?:lagg(?:ed|ing)|trail(?:ed|ing|s)|outperform\w*|underperform\w*|outpac\w+|outdid|beat(?:ing|s)?|versus|vs\.?|compared (?:with|to)|relative to|in contrast to|ahead of|behind|better than|worse than|more than|less than|stronger than|weaker than|than)\b/i;
var BB10D_SKIP_LINE = /^\s*(?:Basis:|In short:|Live:|What we do have|Sources:)/i;

function bb10dPeriods(text) {
  var s = String(text || ""), out = [];
  BB10D_PER.forEach(function (p) { if (p[1].test(s)) out.push(p[0]); });
  return out;
}
function bb10dNonDay(arr) { return arr.filter(function (p) { return p !== "day"; }); }
function bb10dFigs(text) {
  var s = String(text || ""), out = [], m, re = /(\d+(?:\.\d+)?)\s?(?:%|per ?cent\b|percent\b)/gi, rp = /\$\s?(\d[\d,]*(?:\.\d+)?)(?:\s?([kKmMbB])\b)?/g;
  while ((m = re.exec(s))) out.push({ i: m.index, len: m[0].length, kind: "pct", val: parseFloat(m[1]) });
  while ((m = rp.exec(s))) {
    var v = Number(m[1].replace(/,/g, "")), mult = { k: 1e3, m: 1e6, b: 1e9 }[String(m[2] || "").toLowerCase()] || 1;
    if (isFinite(v)) out.push({ i: m.index, len: m[0].length, kind: "usd", val: v * mult });
  }
  return out.sort(function (a, b) { return a.i - b.i; });
}
function bb10dFigEq(a, b) {
  if (!a || !b || a.kind !== b.kind) return false;
  return a.kind === "pct" ? Math.abs(a.val - b.val) <= BB10C_TOL + 1e-9 : Math.abs(a.val - b.val) <= Math.max(0.005, Math.abs(b.val) * 0.001);
}
function bb10dEnts(text) {
  var s = String(text || ""), ents = [], m;
  BB10C_COIN_RE.forEach(function (r) {
    if (!BB10_CB_COINS[r[0]]) return;
    var re = new RegExp(r[1].source, String(r[1].flags || "").replace("g", "") + "g");
    while ((m = re.exec(s))) { ents.push({ i: m.index, end: m.index + m[0].length, key: r[0] }); if (!m[0].length) re.lastIndex++; }
  });
  var ro = new RegExp(BB10D_OTHER_RE.source, "gi");
  while ((m = ro.exec(s))) ents.push({ i: m.index, end: m.index + m[0].length, key: "@" + m[0].toLowerCase().replace(/\s+/g, " ") });
  ents.sort(function (a, b) { return a.i - b.i; });
  var out = [];
  ents.forEach(function (e) { var p = out[out.length - 1]; if (p && p.key === e.key && e.i - p.end < 40) return; out.push(e); });
  return out;
}
// each figure gets .owner (a coin ticker, "@name" for an index/commodity, or null) and .cs/.ce, the bounds of its clause
function bb10dOwners(text) {
  var s = String(text || ""), figs = bb10dFigs(s), ents = bb10dEnts(s), cuts = [0], m, re = /;\s|,\s+(?:while|whereas|and|but|with)\b|\s+(?:while|whereas)\b/gi;
  while ((m = re.exec(s))) cuts.push(m.index);
  cuts.push(s.length + 1);
  figs.forEach(function (f) { var k = 0; while (cuts[k + 1] <= f.i) k++; f.cs = cuts[k]; f.ce = cuts[k + 1]; });
  figs.forEach(function (f) {
    var inCl = ents.filter(function (e) { return e.i >= f.cs && e.i < f.ce; });
    var sameKind = figs.filter(function (g) { return g.kind === f.kind && g.cs === f.cs; });
    if (inCl.length >= 2 && inCl.length === sameKind.length) { f.owner = inCl[sameKind.indexOf(f)].key; return; }
    var before = inCl.filter(function (e) { return e.i < f.i; }), after = inCl.filter(function (e) { return e.i >= f.i; });
    if (before.length) { f.owner = before[before.length - 1].key; return; }
    if (after.length) { f.owner = after[0].key; return; }
    var prev = ents.filter(function (e) { return e.i < f.i; });
    f.owner = prev.length ? prev[prev.length - 1].key : null;
  });
  return figs;
}
function bb10dCoinKeys(text) {
  var out = [];
  bb10dEnts(text).forEach(function (e) { if (e.key.charAt(0) !== "@" && out.indexOf(e.key) < 0) out.push(e.key); });
  return out;
}
// the sentence's own words, source by source: "[n] name | link | as of ... | detail"
function bb10dParseSources(tail) {
  var out = {};
  String(tail || "").split("\n").forEach(function (l) {
    var m = /^\[(\d+)\]\s+(.*)$/.exec(l);
    if (!m) return;
    var p = m[2].split(" | ");
    out[m[1]] = { n: m[1], name: p[0] || "", link: p[1] || "", det: p.length >= 4 ? p.slice(3).join(" | ") : m[2], line: m[2] };
  });
  return out;
}
// the part of a source that states this figure for this coin (coin = null: for anything), or "" when it does not
function bb10dSrcSegs(src, fig, coin) {
  var res = [];
  if (!src) return res;
  var det = src.det, sf = bb10dOwners(det), coins = bb10dCoinKeys(det + " " + src.name + " " + src.link);
  sf.forEach(function (g) {
    if (!bb10dFigEq(fig, g)) return;
    if (coin && !(g.owner === coin || (g.owner == null && coins.length === 1 && coins[0] === coin))) return;
    var a = 0, b = det.length, re = /[.;]\s+(?=[A-Z])/g, m;
    while ((m = re.exec(det))) { var e = m.index + m[0].length; if (e <= g.i) a = e; else { b = m.index + 1; break; } }
    res.push(det.slice(a, b));
  });
  return res;
}
function bb10dSrcSeg(src, fig, coin) { var r = bb10dSrcSegs(src, fig, coin); return r.length ? r[0] : ""; }
function bb10dSrcHas(src, fig, coin) { return !!bb10dSrcSeg(src, fig, coin); }
function bb10dPerOverlap(per, sper) {
  var main = per.filter(function (p) { return p !== "close"; }), need = main.length ? main : per;
  return need.some(function (p) { return sper.indexOf(p) >= 0; });
}
function bb10dNeg(clauseBefore) {
  return BB10C_NEG_RE.test(clauseBefore) ? true : (BB10C_POS_RE.test(clauseBefore) ? false : null);
}
function bb10dSnapMatch(f, row, text) {
  if (!row) return false;
  if (f.kind === "usd") return [row.price, row.open24h, row.high24h, row.low24h].some(function (v) { return v != null && isFinite(v) && Math.abs(f.val - v) <= Math.max(0.005, Math.abs(v) * 0.001); });
  if (Math.abs(f.val - Math.abs(row.changePct)) > BB10C_TOL + 1e-9) return false;
  var before = String(text).slice(Math.max(f.cs, f.i - 60), f.i + f.len + 20), neg = bb10dNeg(before);
  return neg == null || Math.abs(row.changePct) < 0.005 || neg === (row.changePct < 0);
}
// verdict for one coin-owned figure: "ok", "fix" (an unlabelled % the bb10c post-check can rewrite to the snapshot) or "bad:<why>"
function bb10dJudge(f, sent, o) {
  var coin = f.owner, row = o.rows[coin], clause = sent.slice(f.cs, f.ce), per = bb10dNonDay(bb10dPeriods(clause));
  if (!per.length) {
    var sp = bb10dNonDay(bb10dPeriods(sent)), single = bb10dCoinKeys(sent).length === 1 && bb10dFigs(sent).filter(function (g) { return g.kind === f.kind; }).length === 1;
    if (single && sp.length && !/\b(?:24[- ]?h|today|rolling)\b/i.test(sent)) per = sp;
  }
  if (row && bb10dSnapMatch(f, row, sent) && !per.length) return "ok";
  var cited = o.cited.length ? o.cited : Object.keys(o.srcs);
  var srcOk = cited.some(function (n) {
    var src = o.srcs[n];
    var segs = src ? bb10dSrcSegs(src, f, coin) : [];
    if (!segs.length) return false;
    if (per.length) return segs.some(function (seg) { return bb10dPerOverlap(per, bb10dPeriods(seg)); });
    return f.kind === "usd" || !row;
  });
  if (srcOk) return "ok";
  if (row && f.kind === "pct" && !per.length && !o.quoted && !o.otherCoin && o.rowCoins === 1) return "fix";
  return per.length ? "bad:" + coin + " " + f.val + (f.kind === "pct" ? "%" : " usd") + " is not that coin's snapshot figure and no cited source states it for that coin and period (" + per.join("/") + ")"
    : "bad:" + coin + " " + f.val + (f.kind === "pct" ? "%" : " usd") + " is neither that coin's snapshot figure nor in a cited source about that coin";
}
function bb10dCiteOf(tail, coin) {
  try { var mm = new RegExp("(?:^|\\n)\\[(\\d+)\\][^\\n]*products/" + coin + "-USD/stats").exec(tail || ""); return mm ? "[" + mm[1] + "]" : ""; } catch (e) { return ""; }
}
function bb10dSnapSentence(coins, rows, tail) {
  var rs = coins.filter(function (c) { return rows[c]; });
  if (!rs.length) return "";
  var bits = rs.map(function (c) { return bb10cName(c) + " " + bb10cMoveText(rows[c]); });
  var text = bits.length > 1 ? bits.slice(0, -1).join(", ") + " and " + bits[bits.length - 1] : bits[0];
  var cites = rs.map(function (c) { return bb10dCiteOf(tail, c); }).filter(Boolean);
  return text + " (" + bb10cBasis(rows[rs[0]]) + ")" + (cites.length ? " " + cites.join(" ") : "") + ".";
}
// phase 1 (before bb10c post-check): coin attribution + cross-coin comparisons. Returns the sentence, a replacement, or "" to drop it.
function bb10dSentence(sent, o) {
  var figs = bb10dOwners(sent), cf = figs.filter(function (f) { return f.owner && f.owner.charAt(0) !== "@"; });
  if (!cf.length) return sent;
  var coins = bb10dCoinKeys(sent), rowCoins = coins.filter(function (c) { return o.rows[c]; });
  o.quoted = /["\u201c\u201d]/.test(sent) || /\b(?:reported|reports|according to|quoted|quotes|said|says|headline|reuters|bloomberg|cnbc|coindesk|marketwatch|bbc)\b/i.test(sent);
  o.otherCoin = rowCoins.length !== coins.length; o.rowCoins = rowCoins.length;
  if (coins.length >= 2 && BB10D_CMP_RE.test(sent)) {
    var pers = bb10dNonDay(bb10dPeriods(sent));
    var snapAll = !pers.length && cf.every(function (f) { return o.rows[f.owner] && bb10dSnapMatch(f, o.rows[f.owner], sent); }) &&
      coins.every(function (c) { return cf.some(function (f) { return f.owner === c; }); });
    if (snapAll) return sent;
    if (pers.length) {
      // same-period comparison: each figure must be stated by a cited source for its own coin and that period
      var sameOk = cf.every(function (f) { return bb10dJudge(f, sent, o) === "ok"; });
      if (sameOk) return sent;
    }
    var have = coins.every(function (c) { return o.rows[c] && o.body.indexOf(bb10cPct2(o.rows[c].changePct) + "%") >= 0; });
    o.why.push("cross-coin comparison on different bases: " + sent.slice(0, 100));
    if (!have && coins.length <= 3 && coins.every(function (c) { return o.rows[c]; })) { o.rewrote++; return bb10dSnapSentence(coins, o.rows, o.tail); }
    return "";
  }
  for (var k = 0; k < cf.length; k++) {
    var v = bb10dJudge(cf[k], sent, o);
    if (v.indexOf("bad:") === 0) { o.why.push(v.slice(4)); return ""; }
  }
  return sent;
}
// phase 2 (after bb10c post-check): every [n] must point at a source holding a figure of that sentence for its subject
function bb10dCitations(sent, o) {
  var marks = [], m, re = /\[(\d+)\]/g;
  while ((m = re.exec(sent))) if (marks.indexOf(m[1]) < 0) marks.push(m[1]);
  var figs = bb10dOwners(sent);
  if (!marks.length || !figs.length) return sent;
  var valid = [], out = sent;
  marks.forEach(function (n) {
    var src = o.srcs[n];
    var good = !!src && figs.some(function (f) { return bb10dSrcHas(src, f, f.owner && f.owner.charAt(0) !== "@" ? f.owner : null); });
    if (good) valid.push(n);
    else { out = out.replace(new RegExp("\\s?\\[" + n + "\\]", "g"), ""); o.markers++; o.why.push("[" + n + "] does not hold the figure for: " + sent.slice(0, 80)); }
  });
  if (valid.length) return out;
  // no valid marker left: a snapshot figure gets its Coinbase source; anything else is removed
  var need = [], bad = false;
  figs.forEach(function (f) {
    var c = f.owner && f.owner.charAt(0) !== "@" ? f.owner : null, row = c && o.rows[c];
    if (row && bb10dSnapMatch(f, row, sent)) { if (need.indexOf(c) < 0) need.push(c); } else bad = true;
  });
  if (bad) { o.why.push("figure left without a valid source: " + sent.slice(0, 100)); return ""; }
  var cites = need.map(function (c) { return bb10dCiteOf(o.tail, c); }).filter(Boolean);
  if (!cites.length) { o.why.push("snapshot figure without a Coinbase source in the list: " + sent.slice(0, 100)); return ""; }
  return out.replace(/\s*([.!?])?\s*$/, function (x, p) { return " " + cites.join(" ") + (p || "."); });
}
var BB10D_SPLIT = /(?<=[.!?\u27e7]|[.!?]\s*(?:\[\d+\]\s*)*\[\d+\])\s+(?=[A-Z"(\u27e6\[])/;
function bb10dMapSentences(text, fn) {
  var prot = String(text).replace(/\b(U\.S|U\.K|e\.g|i\.e|vs|approx)\./g, function (m) { return m.slice(0, -1) + "\ue010"; });
  var lines = prot.split("\n").map(function (line) {
    if (!line.trim() || BB10D_SKIP_LINE.test(line)) return line;
    // a marker-only piece ("... UK). [1]") belongs to the sentence before it: merge it so it is judged and kept or dropped with that sentence
    var pieces = [];
    line.split(BB10D_SPLIT).forEach(function (s) {
      if (/^\s*(?:\[\d+\]\s*)+[.]?\s*$/.test(s)) { if (pieces.length) pieces[pieces.length - 1] += " " + s.trim(); return; }
      pieces.push(s);
    });
    var kept = pieces.map(function (s) { return fn(s); }).filter(function (s) { return s && s.trim(); });
    return kept.join(" ");
  });
  // a line whose sentences were all dropped is removed, with no run of blank lines left behind
  var out = [];
  lines.forEach(function (l, i) { if (!l.trim() && i > 0 && (!lines[i - 1].trim() || !out.length)) return; out.push(l); });
  return out.join("\n").replace(/\ue010/g, ".").replace(/^\n+/, "");
}
function bb10dRun(r, st, phase) {
  var rows = st && st.bb10cRows;
  if (!r || typeof r !== "object" || typeof r.reply !== "string" || !rows) return r;
  var idx = r.reply.search(/\n\nSources:/), body = idx >= 0 ? r.reply.slice(0, idx) : r.reply, tail = idx >= 0 ? r.reply.slice(idx) : "";
  var o = { rows: rows, tail: tail, srcs: bb10dParseSources(tail), body: body, why: [], rewrote: 0, markers: 0, cited: [] };
  var text = bb10dMapSentences(body, function (sent) {
    o.cited = []; String(sent).replace(/\[(\d+)\]/g, function (x, n) { if (o.cited.indexOf(n) < 0) o.cited.push(n); return x; });
    return phase === 1 ? bb10dSentence(sent, o) : bb10dCitations(sent, o);
  });
  if (text === body) return r;
  if (!text.replace(/\s+/g, "") || !/[A-Za-z]/.test(text.replace(/Basis:[^\n]*/g, ""))) {
    var coinsHit = bb10dCoinKeys(body).filter(function (c) { return rows[c]; });
    if (!coinsHit.length && st.bb10cSubject && rows[st.bb10cSubject]) coinsHit = [st.bb10cSubject];
    if (!coinsHit.length) coinsHit = Object.keys(rows);
    var fb = bb10dSnapSentence(coinsHit.slice(0, 3), rows, tail);
    text = fb || "That figure is not in our feed for that coin, so none is shown.";
    o.why.push("every sentence removed; snapshot sentence shown");
  }
  var res = Object.assign({}, r); res.reply = text + tail;
  if (st) {
    st.bb10dGuard = st.bb10dGuard || { dropped: 0, markers: 0, rewrote: 0, why: [] };
    var g = st.bb10dGuard; g.markers += o.markers; g.rewrote += o.rewrote; g.dropped += o.why.length;
    o.why.forEach(function (w) { if (g.why.length < 8) g.why.push(w); });
    try { st.bb8pDrops = st.bb8pDrops || []; o.why.slice(0, 4).forEach(function (w) { st.bb8pDrops.push({ s: w.slice(0, 120), why: "bb10d crypto figure/citation guard" }); }); } catch (e) {}
  }
  return res;
}

// the whole crypto-Ask check, in order: attribution and comparison guard, bb10c post-check, citation integrity
function bb10dApply(r, st) {
  if (!r || !st || !st.bb10cRows) return r;
  try { r = bb10dRun(r, st, 1); } catch (e1) { try { console.warn("bb10d guard", e1 && e1.message); } catch (e) {} }
  try { r = bb10cPostCheck(r, st); } catch (e2) {}
  try { r = bb10dRun(r, st, 2); } catch (e3) { try { console.warn("bb10d cites", e3 && e3.message); } catch (e) {} }
  return r;
}

// ── bb10d (2): transient 500s. Hardening only, in-request, no timers. Every wrapper falls back to the previous function. ──
// (a) the academy res.end interception is idempotent, never throws, keeps Content-Length true and handles Buffer chunks
function bb10dBodyText(chunk) {
  if (typeof chunk === "string") return chunk;
  if (chunk && typeof chunk === "object" && typeof chunk.length === "number" && typeof chunk.toString === "function" && Buffer.isBuffer(chunk)) return chunk.toString("utf8");
  return null;
}
function bb10dWrapEnd(res) {
  if (!res || res.bb10cEnd || res.bb10dEnd || typeof res.end !== "function") return;
  res.bb10cEnd = true; res.bb10dEnd = true;
  var end0 = res.end;
  res.end = function (chunk) {
    var args = Array.prototype.slice.call(arguments), self = this, changed = false;
    try {
      if (!self.writableEnded && !self.writableFinished && !(typeof self.getHeader === "function" && self.getHeader("content-encoding"))) {
        var txt = bb10dBodyText(chunk);
        if (txt && txt.length < 2000000 && /^\s*\{/.test(txt)) {
          var j = JSON.parse(txt);
          if (j && Array.isArray(j.items)) {
            var nt = JSON.stringify(bb10cAcademyAll(j));
            if (nt && nt !== txt) {
              args[0] = typeof chunk === "string" ? nt : Buffer.from(nt, "utf8");
              if (self.headersSent && typeof self._header === "string" && /\r\ncontent-length:/i.test(self._header)) throw new Error("length already sent");
              changed = true;
              if (!self.headersSent && typeof self.getHeader === "function" && self.getHeader("content-length") != null) self.setHeader("Content-Length", Buffer.byteLength(nt));
            }
          }
        }
      }
    } catch (e) { args = Array.prototype.slice.call(arguments); changed = false; }
    try { return end0.apply(self, args); } catch (e) {
      if (changed) { try { return end0.apply(self, Array.prototype.slice.call(arguments)); } catch (e2) {} }
      try { if (!self.writableEnded) end0.call(self); } catch (e3) {}
      return self;
    }
  };
}
// (b) a route that has already started its response and then throws is not re-run by the fall-through in the earlier wrappers
function bb10dSafeRoute(fn) {
  return async function (req, res) {
    try { return await fn.apply(this, arguments); } catch (e) {
      if (res && (res.headersSent || res.writableEnded)) { console.warn("bb10d route threw after the response started", e && e.message); return; }
      throw e;
    }
  };
}
// (c) rows that are null or not objects are removed before the EPS and valuation maths (the only two throw sites reproduced)
function bb10dCleanFin(body) {
  if (!body || typeof body !== "object") return body;
  var bad = function (a) { return Array.isArray(a) && a.some(function (r) { return !r || typeof r !== "object"; }); };
  var keep = function (a) { return a.filter(function (r) { return r && typeof r === "object"; }); };
  var f = body.financials, e = body.earnings;
  var fq = f && typeof f === "object" && bad(f.quarterly), fa = f && typeof f === "object" && bad(f.annual);
  var eh = e && typeof e === "object" && bad(e.history);
  if (!fq && !fa && !eh) return body;
  var o = Object.assign({}, body);
  if (fq || fa) { o.financials = Object.assign({}, f); if (fq) o.financials.quarterly = keep(f.quarterly); if (fa) o.financials.annual = keep(f.annual); }
  if (eh) o.earnings = Object.assign({}, e, { history: keep(e.history) });
  return o;
}
// (d) a static file whose stream fails after the headers are out would raise an unhandled 'error' event; close the response instead
function bb10dStaticStream(res) {
  var cr0 = fs.createReadStream;
  return function () {
    var s = cr0.apply(fs, arguments);
    try { s.on("error", function (e) { console.warn("bb10d static stream", e && e.message); try { if (!res.writableEnded) res.destroy(); } catch (e2) {} }); } catch (e) {}
    return s;
  };
}
try {
  if (typeof bb10cWrapEnd === "function" && typeof bb10cAcademyAll === "function") bb10cWrapEnd = bb10dWrapEnd;
  if (typeof bb10RegimeRoute === "function") bb10RegimeRoute = bb10dSafeRoute(bb10RegimeRoute);
  if (typeof bb10SessionRoute === "function") bb10SessionRoute = bb10dSafeRoute(bb10SessionRoute);
  if (typeof bb10DeskRoute === "function") bb10DeskRoute = bb10dSafeRoute(bb10DeskRoute);
  if (typeof bb10bCryptoRoute === "function") bb10bCryptoRoute = bb10dSafeRoute(bb10bCryptoRoute);
  var bb10dFinX0 = bb10Financials;
  bb10Financials = function (body) {
    try { return bb10dFinX0.call(this, bb10dCleanFin(body)); } catch (e) { return body; }
  };
  var bb10dServe0 = serveStatic;
  serveStatic = function (req, res) {
    var cr0 = fs.createReadStream, swapped = false;
    try { fs.createReadStream = bb10dStaticStream(res); swapped = true; } catch (e) {}
    try { return bb10dServe0.apply(this, arguments); } finally { if (swapped) { try { fs.createReadStream = cr0; } catch (e) {} } }
  };
  var bb10dHandle0 = handle;
  handle = async function (req, res) {
    try { return await bb10dHandle0.apply(this, arguments); } catch (e) {
      if (res && (res.headersSent || res.writableEnded)) {
        console.warn("bb10d: error after the response started", e && e.message);
        try { if (!res.writableEnded) res.end(); } catch (e2) {}
        return;
      }
      throw e;
    }
  };
} catch (e) { console.warn("bb10d hardening skipped", e && e.message); }

// ── bb10d hooks: rebinding wrappers. Each falls back to the previous function on any error. ──
try {
  // (1) crypto Ask: coin attribution + comparison guard BEFORE the bb10c post-check, citation check AFTER it
  var bb10dFin0 = bb10cFin0;
  bb8qFinish = function (out, st) {
    var r = bb10dFin0.apply(this, arguments);
    try { if (r && st && st.bb10cRows) return bb10dApply(r, st); } catch (e) {}
    try { return bb10cPostCheck(r, st); } catch (e2) { return r; }
  };
  // the model is told which coin figures it may write
  if (typeof bb8pRecord === "function") {
    var bb10dRec0 = bb8pRecord;
    bb8pRecord = function (system, messages) {
      var s = bb10dRec0.apply(this, arguments);
      try {
        var st = bb8pSt();
        if (st && st.bb10cRows && typeof s === "string" && s.indexOf(BB10D_RULE_KEY) < 0) {
          s = s.indexOf(BB8P_GROUND) === 0 ? BB8P_GROUND + "\n\n" + BB10D_RULE + s.slice(BB8P_GROUND.length) : s + "\n\n" + BB10D_RULE;
          st.bb8pSys = s;
        }
      } catch (e) {}
      return s;
    };
  }
} catch (e) { console.warn("bb10d hooks skipped", e && e.message); }
'''

ANCHOR = "// BB10C_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10D_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10d.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10d: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10c live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10d already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10d.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10d: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
