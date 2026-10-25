"""bb10h: QA fix (chat86) for the stale crypto Ask, the doubled BTC paragraph, the /markets INTEL gold price and the /brief crypto figures, on top of bb10h live.
(a) Stale crypto Ask: root cause was bb8qPackMem (the last move pack per name, replayed for 24 h with its ORIGINAL price and as-of time when the new pack
    missed its 3 s wait). Its keys now carry a build id (BB10H_BUILD = sha256 of the server file); a pack for an open market older than 90 s is never replayed
    (closed-market packs keep their 24 h); Coinbase stale-max 15 min -> 2 min; any crypto sentence whose own "as of" is older than 10 min is dropped (with one
    honest line) and the same sentence never reaches the sources list. There is no Ask answer cache to key.
(b) Doubled coin paragraph: one price per coin (the freshest Coinbase snapshot): a second price for the same coin is dropped, the Yahoo period line keeps its
    period figure but loses its competing "to $N now" price (its source detail is kept in step), "We don't have the crypto figures / In short: no crypto figures"
    is dropped when coin lines are present, and the proxy label is dropped from a named coin's own Coinbase line.
(c) /brief, /lenses, /intelligence prose: every coin % carries its period ("24h on Coinbase" / "month-to-date, Yahoo") from the same helpers as the Ask
    (Coinbase 24h rolling, Yahoo daily-chart month-to-date); a mismatching figure is rewritten to the canonical one or neutralised. An unlabelled gold price is
    labelled gold spot (gold-api.com, as of its own UK time) or gold futures GC=F; the data is read once per request with withTimeout (2.5 s).
(d) Routes: /api/chat (both stream and JSON paths) and /api/brief, /api/intelligence, /api/lenses prose change; every other route is unchanged.
Server-only. No new secrets, paid feeds, tables or background timers.
Usage: python3 patch_bb10h.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
BASE_MD5 = "9777ab9b8bebaa77f475b738995aa3d8"
MARK = "// ── bb10h:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
// ── bb10h: QA fix (chat86) for the stale crypto Ask, the doubled BTC paragraph, the /markets INTEL gold price and the /brief crypto figures.
// Server-only. No secrets, tables, feeds or background timers; the only timer is withTimeout around data the page already reads. ──
// Root cause of the stale answer: bb8q kept the last "move pack" per name (bb8qPackMem) for 24 h and served it, with its original as-of
// time, whenever the new pack missed its 3 s wait. A 08:11 pack was therefore replayed at 14:44. There is no Ask answer cache.
var BB10H_VER = "bb10h";
var BB10H_BUILD = (function () {
  try { return BB10H_VER + "-" + crypto.createHash("sha256").update(fs.readFileSync(__filename)).digest("hex").slice(0, 12); } catch (e) { return BB10H_VER; }
})();
var BB10H_LIVE_TTL_MS = 90 * 1000;
var BB10H_ASOF_MAX_MS = 10 * 60 * 1000;
var BB10H_CTX_WAIT_MS = 2500;
var BB10H_STALE_NOTE = "We do not quote a live crypto price here because the latest data we hold for it is more than 10 minutes old.";
try { BB10_CB_STALE_MS = 2 * 60 * 1000; } catch (e) {}
// every cache key carries the build id
function bb10hKey(kind, id) { return BB10H_BUILD + "|" + kind + "|" + String(id); }

// ── (1a) the move-pack memo: keyed by build, and a pack for an open market is never replayed after the live TTL ──
try {
  var bb10hMemGet = bb8qPackMem.get, bb10hMemSet = bb8qPackMem.set;
  bb8qPackMem.get = function (k) { return bb10hMemGet.call(this, bb10hKey("pack", k)); };
  bb8qPackMem.set = function (k, v) { return bb10hMemSet.call(this, bb10hKey("pack", k), v); };
} catch (e) { console.warn("bb10h pack memo key skipped", e && e.message); }
function bb10hPackStale(r) {
  var q = r && r.q;
  if (!q) return false;
  if (/closed/i.test(String(q.status || "") + " " + String(q.note || ""))) return false;   // a closed market's last session is still the latest
  var at = Number(r.bb8qCachedAt);
  return isFinite(at) && at > 0 && Date.now() - at > BB10H_LIVE_TTL_MS;
}
var bb10hWait0 = bb8eWait;
bb8eWait = async function (st) {
  var r = await bb10hWait0.apply(this, arguments);
  try {
    if (r && r.bb8qCached && bb10hPackStale(r)) {
      st.bb10hDroppedPack = { base: r.base, builtAt: r.bb8qCachedAt };
      st.bb8eMoveR = null; st.bb8qPackCached = false;
      return null;
    }
  } catch (e) {}
  return r;
};

// ── clock helpers (UK wall time in an answer back to epoch ms) ──
var BB10H_MON = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
function bb10hUkParts(ms) {
  var p = {};
  new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = Number(x.value); });
  return p;
}
function bb10hUkToMs(y, mo, d, h, mi) {
  var wall = Date.UTC(y, mo, d, h, mi), g = wall;
  for (var i = 0; i < 2; i++) { var p = bb10hUkParts(g); g = wall - (Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - Math.floor(g / 60000) * 60000); }
  return g;
}
// "Sun 25 Oct, 14:55 UK" or "14:55 UK" -> ms (null when it does not parse)
function bb10hAsOfMs(txt, now) {
  var m = /(?:[A-Z][a-z]{2} (\d{1,2}) ([A-Z][a-z]{2,4}),? )?(\d{2}):(\d{2}) UK/.exec(String(txt || ""));
  if (!m) return null;
  var n = bb10hUkParts(now), ms;
  if (m[1]) {
    var mo = BB10H_MON[String(m[2]).slice(0, 3).toLowerCase()];
    if (mo == null) return null;
    ms = bb10hUkToMs(n.year, mo, Number(m[1]), Number(m[3]), Number(m[4]));
    if (ms > now + 86400000) ms = bb10hUkToMs(n.year - 1, mo, Number(m[1]), Number(m[3]), Number(m[4]));
  } else {
    ms = bb10hUkToMs(n.year, n.month - 1, n.day, Number(m[3]), Number(m[4]));
    if (ms > now + 5 * 60000) ms -= 86400000;
  }
  return ms;
}
var BB10H_ASOF_RE = /\bas of ((?:[A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4},? )?\d{2}:\d{2} UK)/g;
var BB10H_CRYPTO_WORD_RE = /\b(?:crypto(?:currenc\w+)?|bitcoin|ether(?:eum)?)\b/i;
var BB10H_CONTRA = [
  /^\s*We don't have the [^.]*?figures this question asks about in our data feed right now[^.]*\.(?:\s*\[\d+\])*\s*$/,
  /^\s*In short: no [^.]*?figures this question asks about in our feed[^.]*\.(?:\s*\[\d+\])*\s*$/
];
var BB10H_PRICE_RE = /\b(?:at|to|is|now|priced at|trading at)\s+\$([\d,]+(?:\.\d+)?)(?!\s*(?:bn|tn|m\b|k\b)|\d)/gi;
var BB10H_TF_RE = /Yahoo Finance daily closes/;
var BB10H_SNAP_RE = /Coinbase 24h rolling/;
function bb10hNum(s) { return Number(String(s).replace(/,/g, "")); }
function bb10hCites(s) { var o = []; (String(s).match(/\[(\d+)\]/g) || []).forEach(function (m) { o.push(m.slice(1, -1)); }); return o; }
// prices a sentence states for a coin: only "at / to / is / now $X" figures near the coin's snapshot price (a base close "of $X" is history, not a price)
function bb10hPrices(sent, ref) {
  var out = [], m, re = new RegExp(BB10H_PRICE_RE.source, "gi");
  while ((m = re.exec(String(sent).replace(/\[\d+\]/g, "")))) { var v = bb10hNum(m[1]); if (ref > 0 && v >= ref * 0.6 && v <= ref * 1.6) out.push(v); }
  return out;
}
function bb10hPer(sent) { var m = /\b(This month|This week|Today|Year to date)\b/.exec(sent); return m ? m[1] : ""; }
// the "to $N now" of a Yahoo period sentence is a second live price for the coin: keep the period figure, drop that price
function bb10hRebase(sent, price) {
  var m = /\bto \$([\d,]+(?:\.\d+)?) now(?=,)/.exec(sent);
  if (!m) return sent;
  return sent.replace(/\s+to \$[\d,]+(?:\.\d+)? now(?=,)/, "").replace(/(\b(?:down|up) \d+(?:\.\d+)?%)(?= \()/, function (x, a) {
    var per = bb10hPer(sent);
    return a + (/month/i.test(per) ? " month-to-date" : /week/i.test(per) ? " week-to-date" : /year/i.test(per) ? " year-to-date" : "");
  });
}
// the final answer: stale as-of out, one price per coin, no "no figures" contradiction, no proxy label on the coin's own line
function bb10hApply(r, st) {
  if (!r || typeof r !== "object" || typeof r.reply !== "string" || !st) return r;
  var sp = bb10fSplit(r.reply), body = sp.body, tail = sp.tail, sources = r.sources, now = Date.now();
  var rows = st.bb10cRows || {}, named = st.bb10fNamed || [], lost = {}, info = { stale: [], dup: [], rebased: [], contra: [], proxy: [] }, changed = false;
  var lines = body.split("\n");
  // pass 1: sentences list per line
  var units = [];
  lines.forEach(function (line, li) {
    if (!line.trim() || /^\s*(?:Basis|Sources):/.test(line)) return;
    bb10fSents(line).forEach(function (sent, si) {
      var cs = []; try { cs = bb10cCoinsIn(sent); } catch (e) { cs = []; }
      units.push({ li: li, si: si, t: sent, coin: cs.length === 1 ? cs[0] : "", multi: cs.length > 1, drop: false, why: "" });
    });
  });
  // (a) a crypto sentence whose own as-of is older than the limit is never served
  units.forEach(function (u) {
    if (!(u.coin || u.multi || BB10H_CRYPTO_WORD_RE.test(u.t))) return;
    var m, re = new RegExp(BB10H_ASOF_RE.source, "g"), old = false;
    while ((m = re.exec(u.t))) { var ms = bb10hAsOfMs(m[1], now); if (ms != null && now - ms > BB10H_ASOF_MAX_MS) old = true; }
    if (old) { u.drop = true; u.why = "stale"; info.stale.push(u.t.slice(0, 80)); }
  });
  // a coin the question names is not a "proxy": drop that label from its own Coinbase line (also inside a "; "-joined line)
  var namedAll = named.slice(); try { bb10cCoinsIn(String(st.bb10fQ || "")).forEach(function (c) { if (namedAll.indexOf(c) < 0) namedAll.push(c); }); } catch (e) {}
  units.forEach(function (u) {
    if (u.drop || !BB10H_SNAP_RE.test(u.t) || !/As a proxy,/i.test(u.t)) return;
    var t2 = u.t.replace(/(^\s*|;\s+)As a proxy,\s*([^,;]{1,40}?)(?=\s+(?:is|was|are|were|fell|rose)\b)/gi, function (m, a, nm) {
      var cs = []; try { cs = bb10cCoinsIn(nm); } catch (e) { cs = []; }
      return cs.length === 1 && namedAll.indexOf(cs[0]) >= 0 ? a + nm : m;
    });
    if (t2 !== u.t) { u.t = t2; u.edit = true; info.proxy.push(u.t.slice(0, 60)); }
  });
  // (b) one price per coin (the freshest Coinbase snapshot), one period figure per coin
  var seenTf = {}, seenSnap = {};
  units.forEach(function (u) {
    if (u.drop || !u.coin || !rows[u.coin] || !(Number(rows[u.coin].price) > 0)) return;
    var S = Number(rows[u.coin].price), ps = bb10hPrices(u.t, S), isTf = BB10H_TF_RE.test(u.t), isSnap = BB10H_SNAP_RE.test(u.t);
    var diff = ps.filter(function (p) { return Math.abs(p / S - 1) > 0.0005; });
    if (isTf) {
      var k = u.coin + "|" + bb10hPer(u.t);
      if (seenTf[k]) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); return; }
      seenTf[k] = 1;
      if (diff.length) { var nt = bb10hRebase(u.t, diff[0]); if (nt !== u.t) { info.rebased.push({ from: u.t, to: nt }); u.t = nt; u.edit = true; } }
      return;
    }
    if (isSnap) {
      var k2 = u.coin + "|" + u.t.replace(/\s*\[\d+\]/g, "").replace(/^\s*As a proxy,\s*/i, "");
      if (seenSnap[k2]) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); return; }
      seenSnap[k2] = 1;
      return;
    }
    if (diff.length) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); }
  });
  // (c) "we have no crypto figures" next to the crypto figures themselves
  var haveCoin = units.some(function (u) { return !u.drop && u.coin && rows[u.coin] && (BB10H_TF_RE.test(u.t) || BB10H_SNAP_RE.test(u.t)); });
  if (haveCoin) units.forEach(function (u) { if (!u.drop && BB10H_CONTRA.some(function (re) { return re.test(u.t); })) { u.drop = true; u.why = "contra"; info.contra.push(u.t.slice(0, 80)); } });
  if (!units.some(function (u) { return u.drop || u.edit; })) return r;
  // rebuild only the lines that changed
  var byLine = {};
  units.forEach(function (u) { (byLine[u.li] = byLine[u.li] || []).push(u); });
  var out = [];
  lines.forEach(function (line, li) {
    var us = byLine[li];
    if (!us || !us.some(function (u) { return u.drop || u.edit; })) { out.push(line); return; }
    us.forEach(function (u) { if (u.drop) bb10hCites(u.t).forEach(function (n) { lost[n] = "bb10h"; }); });
    var keep = us.filter(function (u) { return !u.drop; }).map(function (u) { return u.t; });
    out.push(keep.join(" "));
  });
  body = out.join("\n").replace(/(?:^|\n)[ \t]+(?=\n)/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/^\n+/, "").replace(/\s+$/, "");
  if (info.stale.length && !/more than 10 minutes old/.test(body)) body = body.replace(/\s+$/, "") + "\n\n" + BB10H_STALE_NOTE;
  var rn = bb10fRenumber(body, tail, lost, sources);
  body = rn.body; tail = rn.tail; sources = rn.sources;
  // a period sentence's source detail must say what the sentence says
  info.rebased.forEach(function (x) {
    var a = x.from.replace(/\s*\[\d+\]/g, "").replace(/\.$/, ""), b = x.to.replace(/\s*\[\d+\]/g, "").replace(/\.$/, "");
    if (tail.indexOf(a) >= 0) tail = tail.split(a).join(b);
    if (Array.isArray(sources)) sources = sources.map(function (s) { return s && typeof s.detail === "string" && s.detail.indexOf(a) >= 0 ? Object.assign({}, s, { detail: s.detail.split(a).join(b) }) : s; });
  });
  // the Yahoo period source for a coin with a Coinbase price: its other periods ("to $N now") drop the second price too
  function bb10hSrcRebase(t) {
    var m = /finance\.yahoo\.com\/quote\/([A-Z0-9]+)-USD\//.exec(String(t)), S = m && rows[m[1]] ? Number(rows[m[1]].price) : 0;
    if (!(S > 0) || !BB10H_TF_RE.test(t)) return t;
    return t.replace(/\s+to \$([\d,]+(?:\.\d+)?) now(?=[,)])/g, function (x, n) { return Math.abs(bb10hNum(n) / S - 1) > 0.0005 ? "" : x; });
  }
  if (haveCoin) {
    tail = tail.split("\n").map(function (l) { return /^\[\d+\]\s/.test(l) ? bb10hSrcRebase(l) : l; }).join("\n");
    if (Array.isArray(sources)) sources = sources.map(function (x) {
      if (!x) return x;
      var d = typeof x.detail === "string" ? x.detail : null, d2 = d == null ? null : bb10hSrcRebase((x.link || "") + " " + d).slice(String(x.link || "").length + 1);
      return d != null && d2 !== d ? Object.assign({}, x, { detail: d2 }) : x;
    });
  }
  var o = Object.assign({}, r);
  o.reply = body + tail;
  if (sources !== r.sources) o.sources = sources;
  st.bb10hApplied = info;
  return o;
}
var bb10hFin0 = bb8qFinish;
bb8qFinish = function (out, st) {
  var r = bb10hFin0.apply(this, arguments);
  try { return bb10hApply(r, st); } catch (e) { console.warn("bb10h finish", e && e.message); return r; }
};

// ── (2) /brief, /lenses and /intelligence prose: coin % carry their period; one gold price, labelled ──
var BB10H_ALT = "Bitcoin|BTC|Ethereum|Ether|ETH|Solana|SOL|XRP|Ripple|Dogecoin|DOGE|Cardano|ADA|Avalanche|AVAX|Chainlink|LINK|Litecoin|LTC|Polkadot|DOT|Stellar|XLM|Shiba Inu|SHIB";
var BB10H_MOVE_SRC = "\\b(" + BB10H_ALT + ")\\b([^.;:%\\n]{0,40}?)\\b(down|up|fell|rose|gained|lost|slipped|dropped|declined|rallied|climbed|slid|sank|jumped|surged)\\s+(?:by\\s+|about\\s+|roughly\\s+|around\\s+)?(\\d+(?:\\.\\d+)?)\\s?%";
var BB10H_NEG_RE = /^(?:down|fell|lost|slipped|dropped|declined|slid|sank)$/i;
var BB10H_LABEL_24 = "24h on Coinbase", BB10H_LABEL_MTD = "month-to-date, Yahoo";
var bb10hMem = { mtd: {}, gold: null };
function bb10hCoinRow(coin) {
  var h = null; try { h = bb10CbRow(coin); } catch (e) { h = null; }
  if (!h || !(Date.now() - h.at <= BB10H_LIVE_TTL_MS)) return null;
  return { price: h.last, pct: (h.last / h.open - 1) * 100, at: h.at };
}
function bb10hMtd(coin) {
  var m = bb10hMem.mtd[coin];
  return m && Date.now() - m.at <= BB10H_LIVE_TTL_MS ? m : null;
}
async function bb10hLoadMtd(coin) {
  var tf = BB8Q_TF.filter(function (t) { return t.id === "month"; })[0];
  var j = await fetchYahooChart(coin + "-USD", "1y", "1d"), b = bb8qBars(j), c = b && tf ? bb8qTfChange(b, tf, null) : null;
  if (c && isFinite(c.pct)) bb10hMem.mtd[coin] = { pct: c.pct, base: c.from, baseDate: c.fromDate, now: c.to, asOf: b.nowMs, at: Date.now() };
}
async function bb10hLoadGold() {
  var q = await fetchGoldProxy();
  if (q && Number(q.p) > 0 && !q.stale && !q.cached) bb10hMem.gold = { q: q, at: Date.now() };
}
var BB10H_AI_RE = /market brief|site-intelligence|multi-lens/i;
async function bb10hPrefetch(options, r) {
  var sys = String((options && options.system) || "");
  if (!BB10H_AI_RE.test(sys)) return;
  var txt = ""; try { txt = typeof r === "string" ? r : JSON.stringify((r && (r.validated || r.text)) || ""); } catch (e) { txt = ""; }
  var coins = []; try { coins = bb10cCoinsIn(txt).slice(0, 6); } catch (e) { coins = []; }
  var jobs = [];
  if (coins.length) { jobs.push(bb10CryptoLoad(coins).catch(function () {})); coins.forEach(function (c) { jobs.push(bb10hLoadMtd(c).catch(function () {})); }); }
  if (/\bgold\b|\bXAU\b/i.test(txt)) jobs.push(bb10hLoadGold().catch(function () {}));
  if (!jobs.length) return;
  await withTimeout(Promise.all(jobs), BB10H_CTX_WAIT_MS, "bb10h context").catch(function () {});
}
var bb10hAi0 = generateAi;
generateAi = async function (options) {
  var r = await bb10hAi0.apply(this, arguments);
  try { await bb10hPrefetch(options, r); } catch (e) {}
  return r;
};
function bb10hFmtPct(x) { return Math.abs(x).toFixed(2); }
var BB10H_TAIL_PER = /^\s*(?:(?:over|in|during)\s+(?:the\s+)?(?:last\s+|past\s+)?(?:24[- ]?h(?:ours?|rs?)?|day)\b|(?:today|overnight|month[- ]to[- ]date|this month|MTD)\b)/i;
var BB10H_TAIL_PAREN = /^\s*\((?:[^)]*(?:Coinbase|Yahoo|24h|rolling|month)[^)]*)\)/i;
function bb10hCoinText(s) {
  var re = new RegExp(BB10H_MOVE_SRC, "gi"), out = "", last = 0, m, any = false;
  while ((m = re.exec(s))) {
    var cs = []; try { cs = bb10cCoinsIn(m[1]); } catch (e) { cs = []; }
    if (cs.length !== 1) continue;
    var coin = cs[0], rest = s.slice(re.lastIndex, re.lastIndex + 70), whole = m[0] + rest;
    var per = /month[- ]to[- ]date|\bMTD\b|this month/i.test(m[2] + " " + rest.slice(0, 40)) ? "month" : /24[- ]?h(?:ours?|rs?)?|\btoday\b|overnight|past day|last day|over the day/i.test(m[2] + " " + rest.slice(0, 40)) ? "day" : /\b(?:week|year|ytd|quarter|since)\b/i.test(m[2] + " " + rest.slice(0, 40)) ? "other" : "";
    if (per === "other") continue;
    var neg = BB10H_NEG_RE.test(m[3]), shown = (neg ? -1 : 1) * Number(m[4]);
    var cb = bb10hCoinRow(coin), my = bb10hMtd(coin), target = null, label = "";
    if (per === "month") { target = my ? my.pct : null; label = BB10H_LABEL_MTD; }
    else if (per === "day") { target = cb ? cb.pct : null; label = BB10H_LABEL_24; }
    else if (cb && Math.abs(shown - cb.pct) <= 0.05) { target = cb.pct; label = BB10H_LABEL_24; }
    else if (my && Math.abs(shown - my.pct) <= 0.05) { target = my.pct; label = BB10H_LABEL_MTD; }
    else if (cb) { target = cb.pct; label = BB10H_LABEL_24; }
    var rep, consumed = 0;
    if (target == null) { rep = m[1] + m[2] + m[3] + " (no verified figure available right now)"; }
    else {
      var verb = (target < 0) === neg ? m[3] : (target < 0 ? "down" : "up");
      rep = m[1] + m[2] + verb + " " + bb10hFmtPct(target) + "% (" + label + ")";
      var after = s.slice(re.lastIndex), t1 = BB10H_TAIL_PAREN.exec(after) || BB10H_TAIL_PER.exec(after);
      if (t1) consumed = t1[0].length;
    }
    out += s.slice(last, m.index) + rep; last = re.lastIndex + consumed; re.lastIndex = last; any = true;
  }
  return any ? out + s.slice(last) : s;
}
function bb10hGoldText(s) {
  if (!/\bgold\b|\bXAU\b/i.test(s) || /gold-api\.com|GC=F/i.test(s)) return s;
  return s.replace(/\$([\d,]{4,}(?:\.\d+)?)/g, function (m, n) {
    var v = bb10hNum(n);
    if (!(v >= 1000 && v <= 100000)) return m;
    var g = bb10hMem.gold, sn = null;
    try { sn = typeof lastChatLiveSnapshot !== "undefined" ? lastChatLiveSnapshot : null; } catch (e) { sn = null; }
    if (sn && isFinite(Number(sn.goldLast)) && Math.abs(v / Number(sn.goldLast) - 1) <= 0.0015 && Date.now() - Number(sn.goldTs) * 1000 <= BB10H_ASOF_MAX_MS) {
      return m + " (gold futures GC=F, Yahoo Finance, delayed 10 min, as of " + bb10Uk(Number(sn.goldTs) * 1000) + ")";
    }
    if (g && g.q && Date.now() - g.at <= BB10H_LIVE_TTL_MS) {
      var ms = bb8qMs(g.q) || g.at;
      return "$" + bb8qNum(g.q.p, 2) + " (gold spot, gold-api.com, as of " + bb10Uk(ms) + ")";
    }
    return "\u27e6bb10h-price\u27e7";
  }).replace(/\s*(?:,\s*)?(?:with |at |around )?(?:a |an )?(?:spot )?(?:price|level) (?:of|at) \u27e6bb10h-price\u27e7/gi, "").replace(/\s+(?:at|around)\s+\u27e6bb10h-price\u27e7/gi, "").replace(/\u27e6bb10h-price\u27e7/g, "a price we cannot verify right now");
}
function bb10hText(s) {
  if (typeof s !== "string" || s.length < 12) return s;
  var t = s;
  try { if (/%/.test(t)) t = bb10hCoinText(t); } catch (e) { t = s; }
  try { t = bb10hGoldText(t); } catch (e) {}
  return t;
}
var BB10H_SKIP = { date: 1, tk: 1, type: 1, value: 1, verdict: 1, priority: 1, focusTickers: 1, fit: 1, name: 1, role: 1, confidence: 1, id: 1 };
function bb10hWalk(v, key, depth) {
  if (depth > 6) return v;
  if (typeof v === "string") return BB10H_SKIP[key] ? v : bb10hText(v);
  if (Array.isArray(v)) { var a = v.map(function (x) { return bb10hWalk(x, key, depth + 1); }); return a.some(function (x, i) { return x !== v[i]; }) ? a : v; }
  if (v && typeof v === "object") {
    var o = null;
    Object.keys(v).forEach(function (k) { var n = bb10hWalk(v[k], k, depth + 1); if (n !== v[k]) { o = o || Object.assign({}, v); o[k] = n; } });
    return o || v;
  }
  return v;
}
var BB10H_TEXT_ROUTES = { "/api/brief": ["brief"], "/api/intelligence": ["intel"], "/api/lenses": ["lenses", "intelligence"] };
var bb10hShape0 = bb8oShape;
bb8oShape = function (res, status, body) {
  var out = bb10hShape0.apply(this, arguments);
  try {
    var p = res && res.bb8oPath, keys = BB10H_TEXT_ROUTES[p];
    if (!keys || status !== 200 || !out || typeof out !== "object" || out.error) return out;
    var o = null;
    keys.forEach(function (k) { if (out[k] != null) { var n = bb10hWalk(out[k], k, 0); if (n !== out[k]) { o = o || Object.assign({}, out); o[k] = n; } } });
    return o || out;
  } catch (e) { return out; }
};
'''

ANCHOR = "// BB10G_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10H_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10h.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10h: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10g live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10h already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10h.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10h: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
