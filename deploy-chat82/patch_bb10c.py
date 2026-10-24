#!/usr/bin/env python3
"""bb10c: QA chat81 server fixes on top of bb10b live.
(1) Admin crypto Ask: price, % and basis for a coin come from ONE Coinbase 24h snapshot (same as /api/crypto-snapshot) across the
    context, search-context, grounding blocks, move lead and meta.quote; news-quoted % for a snapshot coin is stripped; answer post-check.
(2) Academy tagger: an asset tag needs a market/asset keyword (or a market-section feed); deny list for careers/lifestyle/sport/etc.
(3) Academy lesson: one set-level generatedAt (+ generatedAtUk, date), items carry only that time plus sourcePublishedAt;
    also applied to the real /api/academy-daily response (res.end), which bypassed the bb10b shaping.
Server-only, anchor-based, no timers/tables/secrets.
Usage: python3 patch_bb10c.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs."""
import sys, os, hashlib, subprocess
NL = b"\n"  # py<3.12 portability: no backslash inside f-string braces
BASE_MD5 = "e7f75c9bccd6668a8b075d682444af49"
MARK = "// ── bb10c:"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BLOCK = r'''
// ── bb10c: (1) admin crypto Ask: ONE basis. Price and percent come from the same Coinbase 24h snapshot as /api/crypto-snapshot,
// the basis is named in the answer, a news-quoted percentage never stands in for it, and an answer percentage that differs from the
// snapshot by more than 0.05 pp is rewritten (clear cases) or followed by a basis note. (2) Academy: market-keyword gate.
// (3) Academy lesson: one generatedAt for the header and every item. No new secrets, feeds, tables or timers. ──
var BB10C_TOL = 0.05;
var BB10C_WAIT_MS = 2500;
var BB10C_COIN_RE = [
  ["BTC", /\bbitcoin\b(?!\s+cash)|\bbtc\b/i, "Bitcoin"],
  ["ETH", /\bethereum\b|\bether\b|\beth\b/i, "Ether"],
  ["SOL", /\b[Ss]olana\b|\bSOL\b/, "Solana"],
  ["XRP", /\bxrp\b|\bripple\b/i, "XRP"],
  ["DOGE", /\bdoge(?:coin)?\b/i, "Dogecoin"],
  ["ADA", /\b[Cc]ardano\b|\bADA\b/, "Cardano"],
  ["AVAX", /\b[Aa]valanche\b|\bAVAX\b/, "Avalanche"],
  ["LINK", /\b[Cc]hainlink\b|\bLINK\b/, "Chainlink"],
  ["LTC", /\b[Ll]itecoin\b|\bLTC\b/, "Litecoin"],
  ["DOT", /\b[Pp]olkadot\b|\bDOT\b/, "Polkadot"],
  ["BCH", /\bbitcoin cash\b|\bBCH\b/i, "Bitcoin Cash"],
  ["SHIB", /\b[Ss]hiba(?: [Ii]nu)?\b|\bSHIB\b/, "Shiba Inu"],
  ["TRX", /\b[Tt]ron\b|\bTRX\b/, "TRON"],
  ["XLM", /\b[Ss]tellar\b|\bXLM\b/, "Stellar"]
];
var BB10C_NAME = {};
BB10C_COIN_RE.forEach(function (r) { BB10C_NAME[r[0]] = r[2]; });
function bb10cName(coin) { return BB10C_NAME[coin] || coin; }
function bb10cCoinsIn(text) {
  var s = String(text || ""), out = [];
  try { bb10CoinsIn(s).forEach(function (c) { if (out.indexOf(c) < 0) out.push(c); }); } catch (e) {}
  BB10C_COIN_RE.forEach(function (r) { if (BB10_CB_COINS[r[0]] && r[1].test(s) && out.indexOf(r[0]) < 0) out.push(r[0]); });
  return out;
}
function bb10cCoinFromSym(sym) {
  var s = String(sym || "").trim().toUpperCase();
  if (!s) return "";
  var c = "";
  try { c = bb10CoinOf(s); } catch (e) { c = ""; }
  if (c) return c;
  try { if (/^[A-Z0-9]{2,6}$/.test(s) && BB10_CB_COINS[s] && bb3Yahoo(s) === s + "-USD") return s; } catch (e) {}
  return "";
}
function bb10cRow(coin) {
  try { var h = bb10CbRow(coin); return h ? bb10bSnapRow(h) : null; } catch (e) { return null; }
}
function bb10cHm(ms) { try { return bb10bHm(ms); } catch (e) { return ""; } }
function bb10cBasis(s) { return "Coinbase 24h rolling, as of " + bb10cHm(s.at) + " UK"; }
function bb10cStatsLink(coin) { return "https://api.exchange.coinbase.com/products/" + coin + "-USD/stats"; }
function bb10cPct2(p) { return Math.abs(Number(p)).toFixed(2); }
function bb10cMoveText(s) {
  // "is down 3.87%" / "is up 1.20%" / "is unchanged", straight from the snapshot's own percentage
  return bb8qVerb(s.changePct, false);
}
function bb10cFactText(coin, s) {
  return bb10cName(coin) + " (" + coin + "-USD) " + bb10cMoveText(s) + " at " + bb10bFmtUsd(s.price) + " (" + bb10cBasis(s) + ").";
}
function bb10cWithTimeout(p, ms) {
  return Promise.race([Promise.resolve(p).catch(function () { return null; }), new Promise(function (r) { setTimeout(function () { r(null); }, ms); })]);
}
function bb10cApplySrc(src, coin, s, text) {
  if (!src || typeof src !== "object") return;
  src.name = BB10B_CB_SRC; src.link = bb10cStatsLink(coin); src.asOf = bb10Iso(s.at);
  src.detail = String(text).replace(/\.$/, "").slice(0, 400);
  src.bb10c = true;
  try { bb8qSrcText.set(src, String(text).replace(/\.$/, "")); } catch (e) {}
}
// A news headline that quotes its own percentage (or price) for a coin that has a Coinbase snapshot: the figure is removed from what
// the model sees, so the answer cannot carry a second percentage for the same coin.
var BB10C_PCT_RE = /[+\-\u2212\u2013]?\d{1,3}(?:\.\d+)?\s?(?:%|per ?cent\b|percent\b)/gi;
function bb10cStripNews(s, rows) {
  if (!s || typeof s !== "object") return false;
  var det = String(s.detail || ""), name = String(s.name || "");
  if (s.bb8q || s.bb10c || /coinbase exchange public stats/i.test(name)) return false;
  var hit = bb10cCoinsIn(det + " " + String(s.title || "")).filter(function (c) { return rows[c]; });
  if (!hit.length) return false;
  BB10C_PCT_RE.lastIndex = 0;
  if (!BB10C_PCT_RE.test(det)) return false;
  BB10C_PCT_RE.lastIndex = 0;
  s.detail = det.replace(BB10C_PCT_RE, "a news-quoted move").replace(/\$\d[\d,]*(?:\.\d+)?/g, "a news-quoted price");
  s.bb10cStripped = true;
  return true;
}
async function bb10cApplyCtx(ctx, st, body) {
  if (!ctx || !Array.isArray(ctx.facts)) return ctx;
  var q = String(ctx.q || ""), coins = [], add = function (c) { if (c && coins.indexOf(c) < 0) coins.push(c); };
  ctx.facts.forEach(function (f) { if (f && /^proxy:/.test(f.id)) add(bb10cCoinFromSym(String(f.id).slice(6))); });
  if (ctx.tf && ctx.tf.sym) add(bb10cCoinFromSym(ctx.tf.sym));
  if (st && st.bb8eBase) add(bb10cCoinFromSym(st.bb8eBase));
  var named = bb10cCoinsIn(q);
  named.forEach(add);
  var list = body && Array.isArray(body.sources) ? body.sources : [];
  list.forEach(function (s) { if (s && typeof s === "object") bb10cCoinsIn(String(s.detail || "") + " " + String(s.title || "")).forEach(add); });
  coins = coins.filter(function (c) { return BB10_CB_COINS[c]; });
  if (!coins.length) return ctx;
  await bb10cWithTimeout(bb10CryptoLoad(coins), BB10C_WAIT_MS);
  var rows = {}, fallback = [];
  coins.forEach(function (c) { var r = bb10cRow(c); if (r) rows[c] = r; });
  ctx.bb10c = { rows: rows, coins: coins, named: named, fallback: fallback };
  if (st) { st.bb10cRows = rows; st.bb10cSubject = named.length === 1 ? named[0] : null; }
  var have = {};
  ctx.facts.forEach(function (f) {
    var m = f && /^proxy:(.+)$/.exec(String(f.id || ""));
    if (!m) return;
    var coin = bb10cCoinFromSym(m[1]);
    if (!coin) return;
    var s = rows[coin];
    if (!s) {
      // Coinbase unreachable: keep the Yahoo fact but name its basis, never present it as the page's 24h figure
      if (f.text.indexOf("Yahoo Finance quote basis") < 0) {
        var note = " (Yahoo Finance quote basis, not the Coinbase 24h figure shown on the market pages, which is unavailable right now)";
        f.text = /, as of /.test(f.text) ? f.text.replace(/, as of /, note + ", as of ") : f.text.replace(/\.$/, "") + note + ".";
        if (f.src) { f.src.detail = f.text.replace(/\.$/, "").slice(0, 400); try { bb8qSrcText.set(f.src, f.text.replace(/\.$/, "")); } catch (e) {} }
        fallback.push(coin);
      }
      return;
    }
    have[coin] = 1;
    var t = bb10cFactText(coin, s);
    f.text = t;
    bb10cApplySrc(f.src, coin, s, t);
    if (f.src && f.src.bb8qProxy) f.src.bb8qProxy.bit = bb10cName(coin) + " " + bb10cMoveText(s) + " at " + bb10bFmtUsd(s.price) + " (" + bb10cBasis(s) + ")";
  });
  // a coin the question names that no Yahoo proxy covered: add its snapshot as a cited fact
  named.forEach(function (c) {
    var s = rows[c];
    if (!s || have[c]) return;
    var t = bb10cFactText(c, s), src = bb8qSrc(BB10B_CB_SRC, bb10cStatsLink(c), s.at, t.replace(/\.$/, ""), "cb:" + c);
    src.bb10c = true;
    ctx.facts.push({ id: "cb:" + c, text: t, src: src }); ctx.sources.push(src);
    have[c] = 1;
  });
  // "today" on a crypto symbol: Yahoo's calendar-day close is another basis. The Coinbase rolling 24h figure replaces it.
  if (ctx.tf && ctx.tfReq === "today") {
    var tc = bb10cCoinFromSym(ctx.tf.sym), ts = tc && rows[tc];
    if (ts) {
      var tt = "Over the Coinbase rolling 24 hours (not a calendar-day change), " + bb10cName(tc) + " " + bb10cMoveText(ts) + ", from " + bb10bFmtUsd(ts.open24h) + " to " + bb10bFmtUsd(ts.price) + " (" + bb10cBasis(ts) + ").";
      ctx.tf.text = tt;
      bb10cApplySrc(ctx.tf.src, tc, ts, tt);
      if (ctx.tfMore && ctx.tfMore.length) { ctx.tf.src.detail = (ctx.tf.src.detail + "; " + ctx.tfMore.join(" ")).slice(0, 400); try { bb8qSrcText.set(ctx.tf.src, ctx.tf.src.detail); } catch (e) {} }
      ctx.facts.forEach(function (f) { if (f && f.src === ctx.tf.src) f.text = tt; });
    }
  }
  // news-quoted percentages for a coin that has a snapshot are removed from the supplied sources
  var stripped = 0;
  list.forEach(function (s) { if (bb10cStripNews(s, rows)) stripped++; });
  ctx.bb10c.stripped = stripped;
  return ctx;
}

// ── bb10c (1b): move pack / lead / quote chip on the Coinbase basis ──
async function bb10cMovePack(base, pack) {
  var coin = bb10cCoinFromSym(base);
  if (!coin) return pack;
  await bb10cWithTimeout(bb10CryptoLoad([coin]), BB10C_WAIT_MS);
  var s = bb10cRow(coin);
  if (!s) return pack;
  var q = Object.assign({}, pack && pack.q ? pack.q : {}, { p: s.price, prev: s.open24h, c: s.changePct, change: s.change, ts: Math.floor(s.at / 1000), currency: "USD", status: "open", note: "", basis: "rolling24h", name: bb10cName(coin) });
  var out = pack ? Object.assign({}, pack) : { base: base, ysym: coin + "-USD", fit: null };
  out.q = q; out.ms = s.at; out.bench = null; out.sector = null; out.bb10cCb = s;
  // headlines that carry their own percentage for this coin are not shown beside the Coinbase figure
  out.news = (Array.isArray(pack && pack.news) ? pack.news : []).filter(function (it) {
    var t = String(it && it.title || "");
    BB10C_PCT_RE.lastIndex = 0;
    var has = BB10C_PCT_RE.test(t); BB10C_PCT_RE.lastIndex = 0;
    return !(has && bb10cCoinsIn(t).indexOf(coin) >= 0);
  });
  return out;
}
function bb10cLeadFix(r, pack) {
  var s = pack.bb10cCb, coin = s.coin, label = bb10cBasis(s), prev = bb10bFmtUsd(s.open24h);
  var head = /'s latest move, as of [A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4}, \d{2}:\d{2} UK:/;
  var fix = function (t) {
    if (typeof t !== "string") return t;
    return t.replace(head, "'s latest move (" + label + "):").replace(/\(previous close \$[\d,]+(?:\.\d+)?\)/, "(24 hours earlier " + prev + ")");
  };
  var o = Object.assign({}, r);
  o.text = fix(r.text); o.paint = fix(r.paint); o.prompt = fix(r.prompt);
  if (Array.isArray(r.sources) && r.sources.length) {
    var s0 = Object.assign({}, r.sources[0]), t = bb10cFactText(coin, s);
    bb10cApplySrc(s0, coin, s, t);
    o.sources = [s0].concat(r.sources.slice(1));
  }
  return o;
}
function bb10cQuoteFix(st, o) {
  var coin = bb10cCoinFromSym(bb8rSubjectSym(st)) || (st && st.bb10cSubject) || "";
  if (!coin) return null;
  var s = (st && st.bb10cRows && st.bb10cRows[coin]) || bb10cRow(coin);
  if (!s) return null;
  var q = Object.assign({}, o || {}), label = bb10cName(coin);
  q.symbol = coin + "-USD"; q.feedSymbol = coin + "-USD"; q.label = label; q.name = label;
  q.price = s.price; q.change = bb10R(s.change, s.price >= 1 ? 2 : 6); q.changePct = s.changePct; q.prevClose = s.open24h;
  q.currency = "USD"; q.asOf = s.asOf; q.asOfUk = s.asOfUk; q.session = null;
  q.source = "Coinbase Exchange"; q.priceSource = BB10B_CB_SRC; q.feed = BB10B_CB_SRC + " (" + coin + "-USD)";
  q.changeBasis = "rolling 24h"; q.basisLabel = bb10cBasis(s); q.changeBasisLabel = bb10cBasis(s);
  q.quoteLine = label + " $" + bb8rPx(s.price) + " " + bb8rSigned(q.change, s.price >= 1 ? 2 : 6) + " (" + bb8rSigned(s.changePct, 2) + "%) \u00b7 " + bb10cBasis(s);
  return q;
}

// ── bb10c (1c): post-check. A percentage beside a coin name that differs from the snapshot by more than 0.05 pp. ──
var BB10C_WINDOW_RE = /\b(?:week|weekly|month|monthly|year|yearly|ytd|since|quarter|all[- ]time|record|highs?|lows?|peak|cap|volume|dominance|inflows?|outflows?|etfs?|7-?day|30-?day|7d|30d|from (?:the )?\w+ close|volatility|share of|allocation|yield|apy|fees?)\b/i;
var BB10C_MOVE_RE = /\b(?:down|up|fall(?:s|en|ing)?|fell|drop(?:s|ped|ping)?|dip(?:s|ped|ping)?|slid(?:e|es|ing)?|slip(?:s|ped|ping)?|lower|higher|gain(?:s|ed|ing)?|ris(?:e|es|en|ing)|rose|climb(?:s|ed|ing)?|jump(?:s|ed|ing)?|surg(?:e|es|ed|ing)|rall(?:y|ies|ied|ying)|lost|lose[sd]?|declin(?:e|es|ed|ing)|slump(?:s|ed|ing)?|sank|sink(?:s|ing)?|tumbl(?:e|es|ed|ing)|retreat(?:s|ed|ing)?|weaker|stronger|change[sd]?|moved?|moves)\b/i;
var BB10C_NEG_RE = /\b(?:down|fall(?:s|en|ing)?|fell|drop(?:s|ped|ping)?|dip(?:s|ped|ping)?|slid(?:e|es|ing)?|slip(?:s|ped|ping)?|lower|lost|lose[sd]?|declin(?:e|es|ed|ing)|slump(?:s|ed|ing)?|sank|sink(?:s|ing)?|tumbl(?:e|es|ed|ing)|retreat(?:s|ed|ing)?|weaker)\b/i;
var BB10C_POS_RE = /\b(?:up|gain(?:s|ed|ing)?|ris(?:e|es|en|ing)|rose|climb(?:s|ed|ing)?|jump(?:s|ed|ing)?|surg(?:e|es|ed|ing)|rall(?:y|ies|ied|ying)|higher|stronger|advanc\w+)\b/i;
function bb10cSplitClauses(sentence) {
  return sentence.split(/(?=;\s)|(?=,\s+(?:while|whereas|and|but|with)\b)|(?=\s+(?:while|whereas)\b)/i);
}
function bb10cFixClause(clause, sentCoins, rows, rep) {
  if (BB10C_WINDOW_RE.test(clause)) return clause;
  var coins = bb10cCoinsIn(clause).filter(function (c) { return rows[c]; });
  var other = bb10cCoinsIn(clause).filter(function (c) { return !rows[c]; });
  if (!coins.length && sentCoins.length === 1) coins = sentCoins;
  if (!coins.length || other.length) return clause;
  var re = /([+\-\u2212\u2013]?)(\d{1,3}(?:\.\d+)?)(\s?(?:%|per ?cent\b|percent\b))/gi, m, out = clause, shifts = 0;
  var figs = [];
  while ((m = re.exec(clause))) figs.push({ i: m.index, len: m[0].length, sign: m[1], val: parseFloat(m[2]), unit: m[3] });
  if (!figs.length) return clause;
  for (var k = figs.length - 1; k >= 0; k--) {
    var f = figs[k], before = clause.slice(Math.max(0, f.i - 60), f.i + f.len + 20);
    if (!(f.sign || BB10C_MOVE_RE.test(before))) continue;
    var neg = f.sign && f.sign !== "+" ? true : (BB10C_NEG_RE.test(before) ? true : (BB10C_POS_RE.test(before) ? false : null));
    var ok = coins.some(function (c) {
      var p = rows[c].changePct;
      if (Math.abs(f.val - Math.abs(p)) > BB10C_TOL + 1e-9) return false;
      return neg == null || Math.abs(p) < 0.005 || (neg === (p < 0));
    });
    if (ok) continue;
    var single = coins.length === 1 ? rows[coins[0]] : null;
    var dirOk = single && (neg == null || Math.abs(single.changePct) < 0.005 || neg === (single.changePct < 0));
    if (single && dirOk && !rep.quoted) {
      var rep2 = bb10cPct2(single.changePct) + "%" + (rep.seen[single.coin] ? "" : " (" + bb10cBasis(single) + ")");
      rep.seen[single.coin] = 1;
      out = out.slice(0, f.i) + (f.sign ? (single.changePct < 0 ? "\u2212" : "+") : "") + rep2 + out.slice(f.i + f.len);
      rep.fixed++;
      rep.coins[single.coin] = 1;
    } else {
      coins.forEach(function (c) { rep.noted[c] = 1; });
    }
  }
  // price of the same coin in that clause: from the same snapshot (only a figure within 3% is treated as the same quote)
  if (coins.length === 1 && rep.coins[coins[0]]) {
    var s = rows[coins[0]];
    out = out.replace(/\$(\d[\d,]*(?:\.\d+)?)/g, function (m0, n) {
      var v = Number(n.replace(/,/g, ""));
      if (!(v > 0) || Math.abs(v / s.price - 1) > 0.03 || Math.abs(v - s.price) < 0.005) return m0;
      return bb10bFmtUsd(s.price);
    });
  }
  return out;
}
function bb10cPostCheck(r, st) {
  var rows = st && st.bb10cRows;
  if (!r || typeof r !== "object" || typeof r.reply !== "string" || !rows) return r;
  var all = Object.keys(rows);
  if (!all.length) return r;
  var idx = r.reply.search(/\n\nSources:/), body = idx >= 0 ? r.reply.slice(0, idx) : r.reply, tail = idx >= 0 ? r.reply.slice(idx) : "";
  var rep = { fixed: 0, noted: {}, seen: {}, coins: {} };
  var lines = body.split("\n").map(function (line) {
    if (!line.trim() || /^\s*Basis:/.test(line)) return line;
    var sents = line.split(/(?<=[.!?\]\u27e7])\s+(?=[A-Z"(\u27e6\[])/);
    return sents.map(function (sent) {
      var sc = bb10cCoinsIn(sent).filter(function (c) { return rows[c]; });
      if (!sc.length || !/\d\s?(?:%|per ?cent|percent)/i.test(sent)) return sent;
      rep.quoted = /["\u201c\u201d]/.test(sent) || /\b(?:reported|reports|according to|quoted|quotes|said|says|headline|reuters|bloomberg|cnbc|coindesk|marketwatch|bbc)\b/i.test(sent);
      return bb10cSplitClauses(sent).map(function (cl) { return bb10cFixClause(cl, sc, rows, rep); }).join("");
    }).join(" ");
  });
  var text = lines.join("\n");
  // coins that still carry a different figure get one basis note, from the snapshot only
  var notes = Object.keys(rep.noted).filter(function (c) { return rows[c] && !rep.coins[c]; });
  if (notes.length) {
    var citeOf = function (c) {
      try { var mm = new RegExp("(?:^|\\n)\\[(\\d+)\\][^\\n]*products/" + c + "-USD/stats").exec(tail || ""); return mm ? " [" + mm[1] + "]" : ""; } catch (e) { return ""; }
    };
    text += "\n\nBasis: " + notes.map(function (c) { var s = rows[c]; return bb10cName(c) + " " + bb10cMoveText(s) + " at " + bb10bFmtUsd(s.price) + " (" + bb10cBasis(s) + ")" + citeOf(c); }).join("; ") + ". Any other percentage quoted for the same coin comes from a different source or time window.";
  }
  if (text === body) return r;
  var o = Object.assign({}, r);
  o.reply = text + tail;
  if (st) st.bb10cPost = { fixed: rep.fixed, noted: notes.length };
  return o;
}

// ── bb10c (2): Academy tagger gate. An asset tag needs an explicit market/asset keyword in the headline (or a market-section feed). ──
var BB10C_MKT_RE = /\b(?:stocks?|shares|equit(?:y|ies)|markets?|wall street|s&p|nasdaq|dow|ftse|dax|nikkei|hang seng|treasur(?:y|ies)|bonds?|yields?|gilts?|inflation|cpi|ppi|interest rates?|rates? (?:cuts?|hikes?|decisions?)|fed|federal reserve|fomc|ecb|bank of england|boe|central banks?|dollar|greenback|sterling|pound|euro|yen|currency|currencies|forex|gold|bullion|silver|oil|crude|brent|wti|opec\+?|natural gas|bitcoin|btc|ether|ethereum|crypto\w*|etfs?|commodit(?:y|ies)|investors?|traders?|earnings|gdp|tariffs?|recession|rall(?:y|ies)|sell-?off|payrolls?|jobs report|unemployment rate|ipo|dividends?|hedge funds?|banks?|mortgage rates?|national debt)\b/i;
var BB10C_STRONG_RE = /\b(?:stocks?|shares|wall street|s&p|nasdaq|dow|ftse|treasur(?:y|ies)|yields?|gold|bullion|oil|crude|brent|bitcoin|btc|ether|ethereum|crypto\w*|dollar|sterling|forex|fed|federal reserve|etfs?|bonds?)\b/i;
var BB10C_DENY_RE = /\b(?:job (?:search|hunt|seekers?|interviews?)|careers?|cvs?|r\u00e9sum\u00e9s?|resumes?|interview tips|graduates?|apprentic\w+|work-life|workplace|lifestyle|recipes?|holidays?|travel tips?|wellbeing|dating|relationships?|horoscopes?|football|soccer|premier league|champions league|cricket|rugby|tennis|golf|formula (?:1|one)|olympics?|world cup|nba|nfl|mlb|nhl|boxing|ufc|wimbledon|oscars?|baftas?|grammys?|emmys?|films?|movies?|celebrit(?:y|ies)|royal family|k-pop|albums?|concerts?|tv (?:show|series)|reality tv|fashion|love island|taylor swift)\b|\b(?:ai|artificial intelligence)\b[^.]{0,40}\b(?:jobs?|workers?|careers?|graduates?)\b|\b(?:jobs?|careers?)\b[^.]{0,40}\b(?:ai|artificial intelligence)\b/i;
var BB10C_SECTION_RE = /^(?:MarketWatch|CoinDesk|Investing\.com)$/i;
function bb10cMarketOk(h, src) {
  h = String(h || "");
  if (!h) return false;
  if (BB10C_DENY_RE.test(h) && !BB10C_STRONG_RE.test(h)) return false;
  if (BB10C_SECTION_RE.test(String(src || ""))) return true;
  return BB10C_MKT_RE.test(h);
}
var bb10cWhyPrev = null;
function bb10cWhyV(x) {
  try {
    if (x && typeof x === "object" && x.h) {
      if (!bb10cMarketOk(x.h, x.src)) return "non-market-headline";
      var A = RT48B_ASSETS[x.asset];
      if (A && !A[1].test(String(x.h)) && !BB10C_MKT_RE.test(String(x.h)) && !BB10C_SECTION_RE.test(String(x.src || ""))) return "no-market-keyword";
    }
  } catch (e) {}
  return bb10cWhyPrev.apply(this, arguments);
}

// ── bb10c (3): Academy lesson: ONE generatedAt for the header and every item. A source's own publish time is kept apart. ──
var BB10C_ITEM_TIME_KEYS = ["updated", "updatedAt", "updatedUk", "updatedLabel", "asOf", "asOfUk", "at", "ts", "time", "timeUk", "publishedAt", "pubDate", "generatedAt", "generatedAtUk"];
function bb10cUkDate(ms) {
  try {
    var p = {};
    new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short" }).formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = x.value; });
    return p.weekday + " " + p.day + " " + p.month;
  } catch (e) { return ""; }
}
function bb10cAcademySet(body) {
  if (!body || typeof body !== "object" || !Array.isArray(body.items)) return body;
  var out = Object.assign({}, body), t = Date.parse(String(body.generatedAt || body.asOf || ""));
  if (!isFinite(t)) t = Date.now();
  var iso = new Date(t).toISOString(), hm = bb10bHm(t), day = bb10cUkDate(t), today = bb10cUkDate(Date.now());
  out.generatedAt = iso; out.asOf = iso;
  out.generatedAtUk = hm; out.generatedDateUk = day;
  out.generatedAtUkLabel = day + ", " + hm + " UK";
  out.updatedLabel = "Updated " + (day === today ? "today" : day) + " \u00b7 " + hm + " UK";
  out.items = body.items.map(function (it) {
    if (!it || typeof it !== "object") return it;
    var n = Object.assign({}, it), pub = null;
    var pv = it.sourcePublishedAt || it.publishedAt || it.pubDate || "", pt = typeof pv === "number" ? pv : Date.parse(String(pv));
    if (isFinite(pt) && pt > 0) pub = pt;
    BB10C_ITEM_TIME_KEYS.forEach(function (k) { delete n[k]; });
    n.generatedAt = iso; n.generatedAtUk = hm;
    n.sourcePublishedAt = pub ? new Date(pub).toISOString() : null;
    n.sourcePublishedAtUk = pub ? bb10cUkDate(pub) + ", " + bb10bHm(pub) + " UK" : null;
    return n;
  });
  return out;
}
function bb10cAcademyAll(j) {
  var o = j;
  try { o = bb10bAcademyShape(o); } catch (e) { o = j; }
  return bb10cAcademySet(o);
}
function bb10cWrapEnd(res) {
  if (!res || res.bb10cEnd || typeof res.end !== "function") return;
  res.bb10cEnd = true;
  var end0 = res.end;
  res.end = function (chunk) {
    var args = Array.prototype.slice.call(arguments);
    try {
      if (typeof chunk === "string" && chunk.charAt(0) === "{") {
        var j = JSON.parse(chunk);
        if (j && Array.isArray(j.items)) args[0] = JSON.stringify(bb10cAcademyAll(j));
      }
    } catch (e) {}
    return end0.apply(this, args);
  };
}

// ── bb10c hooks: rebinding wrappers. Each falls back to the previous function on any error. ──
try {
  // (1) crypto Ask on the Coinbase basis
  var bb10cBuild0 = bb8qBuild;
  bb8qBuild = async function (st, body) {
    var ctx = await bb10cBuild0.apply(this, arguments);
    try { await bb10cApplyCtx(ctx, st, body); } catch (e) { console.warn("bb10c ask", e && e.message); }
    return ctx;
  };
  var bb10cMove0 = bb8eMovePack;
  bb8eMovePack = async function (base) {
    var pack = await bb10cMove0.apply(this, arguments);
    try { return await bb10cMovePack(base, pack); } catch (e) { return pack; }
  };
  var bb10cLead0 = bb8eLead;
  bb8eLead = function (pack, card, n0) {
    var r = bb10cLead0.apply(this, arguments);
    try { if (pack && pack.bb10cCb && r) return bb10cLeadFix(r, pack); } catch (e) {}
    return r;
  };
  var bb10cQM0 = bb8rQuoteMeta;
  bb8rQuoteMeta = function (st, prior) {
    var o = bb10cQM0.apply(this, arguments);
    try { var q = bb10cQuoteFix(st, o); if (q) return q; } catch (e) {}
    return o;
  };
  var bb10cFin0 = bb8qFinish;
  bb8qFinish = function (out, st) {
    var r = bb10cFin0.apply(this, arguments);
    try { return bb10cPostCheck(r, st); } catch (e) { return r; }
  };
  // the no-data proxy line: bb8rProxyAsOf cut the header at the colon inside "18:35 UK" and left "35 UK:" in the sentence
  var bb10cPA0 = bb8rProxyAsOf;
  bb8rProxyAsOf = function (doc) {
    var held = [];
    try {
      if (doc && typeof doc.body === "string") {
        doc.body = doc.body.replace(/(What we do have[^\n:]*? as of [A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4}, \d{2}):(\d{2} UK):/g, "$1\u2236$2:")
          .replace(/\(Coinbase 24h rolling, as of \d{2}:\d{2} UK\)/g, function (m) { held.push(m); return "\ue000" + (held.length - 1) + "\ue001"; });
      }
    } catch (e) {}
    var r = bb10cPA0.apply(this, arguments);
    try {
      if (held.length && doc && typeof doc.body === "string") {
        doc.body = doc.body.replace(/\ue000(\d+)\ue001/g, function (m, i) { return held[Number(i)] || ""; })
          .replace(/(\(Coinbase 24h rolling, as of \d{2}:\d{2} UK\)), as of [A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4}, \d{2}:\d{2} UK/g, "$1");
      }
    } catch (e) {}
    return r;
  };
  // (2) Academy tagger gate
  bb10cWhyPrev = _rt48bWhy;
  _rt48bWhy = bb10cWhyV;
  var bb10cHeads0 = _rt48sHeads;
  _rt48sHeads = async function () {
    var r = await bb10cHeads0.apply(this, arguments);
    try { return Array.isArray(r) ? r.filter(function (h) { return bb10cMarketOk(h && h.h, h && h.src); }) : r; } catch (e) { return r; }
  };
  // (3) Academy lesson: one generatedAt; the source's own publish time kept apart
  var bb10cItem0 = _rt48bItem;
  _rt48bItem = function (H, asset, dir, e, kind) {
    var it = bb10cItem0.apply(this, arguments);
    try { var t = Number(H && H.t); if (it && isFinite(t) && t > 0) it.sourcePublishedAt = new Date(t).toISOString(); } catch (e2) {}
    return it;
  };
  var bb10cShape0 = bb8oShape;
  bb8oShape = function (res, status, body) {
    var out = bb10cShape0.apply(this, arguments);
    try { if (res && res.bb8oPath === "/api/academy-daily") return bb10cAcademyAll(out); } catch (e) {}
    return out;
  };
  var bb10cHandle0 = handle;
  handle = async function (req, res) {
    try {
      var p = String((req && req.url) || "").split("?")[0];
      if (p === "/api/academy-daily") bb10cWrapEnd(res);
    } catch (e) {}
    return bb10cHandle0.apply(this, arguments);
  };
} catch (e) { console.warn("bb10c hooks skipped", e && e.message); }
'''

ANCHOR = "// BB10B_JS_END"
EDITS = [(ANCHOR, ANCHOR + "\n" + BLOCK.rstrip("\n") + "\n// BB10C_JS_END")]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb10c.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb10c: {f} md5 {m0} lines {raw.count(NL)}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10b live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in s: print("REFUSE: bb10c already applied"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb10c.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
    os.replace(tmp, f); print(f"bb10c: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(NL)}"); return 0
sys.exit(main())
