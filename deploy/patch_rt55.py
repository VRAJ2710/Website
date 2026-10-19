#!/usr/bin/env python3
"""patch_rt55.py: client patch. Reads app.js?v=chatNN and writes chatNN+1.

The known live base is chat64 (patch_rt54.py at 91a166f applied to chat63):
  app.js md5 b45b28623e1c8368140406558df95b90
  index.html md5 b2271ff3debbf8790a4cdeb5a42b8297
A different checksum prints WARN and continues. Anchors still decide: a missing
or ambiguous anchor aborts with a non-zero status. A second run prints
REFUSE (already applied) and exits 0. Finishes with node --check.

1) Ask. bb5g sends one newline after the lead, so fe64_joinChunk and
fe64_flattenName must not add, drop, or rewrite newlines or spaces.
Entity spans wrap the same characters. deploy/check_rt55_ask.js feeds a
bb5g-shaped SSE sequence and a legacy newline-before-each-chunk stream.

2) News tags. The feed category is the default. Gold and other commodity
subjects run before equity. Stocks needs a real ticker, an exchange:ticker,
or a company-stock pattern. A headline with no market words is Other.
n.tg is the same word the chip and the filter use.

3) Quote badges. status, note, nextOpen and delayMin survive every merge
and the chart-close path. The fe64 formatter is what the tape, the markets
page, Twelve Data rows and the watchlist show. The venue calendar is used
only when the server did not send a status. Visible copy never says
cached·yh, yh, a raw minute age, or proxy.

4) The gold tape says Gold with a plain source note. The markets view has
one line: "Prices come from free market feeds; some are delayed."

5) At 1280 the markets table header no longer sits on the news filter chips.
Guests get the same header as a signed-in desk, with Sign in and Create
free account, and that pair is not repeated.

No server file is changed. Live server c689b794 is untouched.

Usage: python3 patch_rt55.py [--check] <dir containing app.js and index.html>"""
import sys, os, re, hashlib, subprocess, tempfile
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
D = args[0] if args else '.'
APP, IDX = os.path.join(D, 'app.js'), os.path.join(D, 'index.html')

EXPECT_APP_MD5 = "b45b28623e1c8368140406558df95b90"
EXPECT_INDEX_MD5 = "b2271ff3debbf8790a4cdeb5a42b8297"
NEED_MARKER = "// ── rt54 ──"

def load(p):
    b = open(p, 'rb').read(); return b.decode('utf-8').replace('\r\n', '\n'), b'\r\n' in b
def die(m): print('ABORT:', m); sys.exit(1)
def already(m): print('REFUSE:', m); sys.exit(0)
raw = open(APP, 'rb').read()
raw_idx = open(IDX, 'rb').read()
s, crlf = load(APP); h, hcrlf = load(IDX)
if '// ── rt55 ──' in s: already('rt55 already applied')
if NEED_MARKER not in s: die('base lacks ' + NEED_MARKER)
md5 = hashlib.md5(raw).hexdigest()
imd5 = hashlib.md5(raw_idx).hexdigest()
if md5 != EXPECT_APP_MD5:
    print('WARN md5 app.js: have %s expected %s (anchors still decide)' % (md5, EXPECT_APP_MD5))
if imd5 != EXPECT_INDEX_MD5:
    print('WARN md5 index.html: have %s expected %s (anchors still decide)' % (imd5, EXPECT_INDEX_MD5))
v = re.findall(r'app\.js\?v=chat(\d+)"', h)
if len(v) != 1: die('index app.js?v=chatN bust matched %d times' % len(v))
n = int(v[0]); base, nxt = 'chat%d' % n, 'chat%d' % (n + 1)
print('base:', base, 'app.md5', md5, 'index.md5', imd5, '->', nxt)

def sub1(src, old, new, label):
    c = src.count(old)
    if c != 1: die('%s matched %d times' % (label, c))
    return src.replace(old, new, 1)

# 1) Ask. Keep the chat64 call, but the helpers must be identity on
# newlines and spaces. The entity span copies the matched characters.
s = sub1(s,
'''function fe64_joinChunk(acc, chunk) {
  chunk = String(chunk == null ? "" : chunk);
  acc = String(acc == null ? "" : acc);
  if (!chunk) return acc;
  if (!acc) return chunk;
  var a = acc.replace(/[\\n\\r]+$/g, "");
  var c = chunk.replace(/^[\\n\\r]+/g, "");
  var broke = a.length !== acc.length || c.length !== chunk.length;
  var end = a.slice(-1), start = c.charAt(0);
  if (!broke) return acc + chunk;
  if (end === "(" && /[A-Za-z0-9]/.test(start)) return a + c;
  if (/[A-Za-z0-9]$/.test(end) && /^[a-z0-9)]/.test(start)) return a + c;
  if (/[A-Za-z0-9)]$/.test(end) && /^[A-Z(]/.test(start)) return a + " " + c;
  return a + c;
}''',
'''function fe64_joinChunk(acc, chunk) {
  return String(acc == null ? "" : acc) + String(chunk == null ? "" : chunk);
}''',
'join chunks without rewriting boundaries')
s = sub1(s,
'''function fe64_flattenName(text) {
  return String(text == null ? "" : text)
    .replace(/([A-Za-z])\\s*[\\n\\r]+\\s*([a-z])/g, "$1$2")
    .replace(/([A-Za-z0-9])\\s*[\\n\\r]+\\s*([A-Z])/g, "$1 $2")
    .replace(/([A-Za-z])\\s*[\\n\\r]+\\s*\\(/g, "$1 (")
    .replace(/\\(\\s*[\\n\\r]+\\s*([A-Za-z])/g, "($1");
}''',
'''function fe64_flattenName(text) {
  return String(text == null ? "" : text);
}''',
'flatten must not rewrite newlines or spaces')
s = sub1(s,
'''function fe64_entHtml(html) {
  return String(html || "").replace(/([A-Z][A-Za-z0-9&;.\'-]{1,40}(?:\\s+[A-Z][A-Za-z0-9&;.\'-]{1,40}){0,4})\\s*\\(\\s*([A-Z][A-Z0-9.]{1,8})\\s*\\)/g, \'<span class="fe64-ent">$1 ($2)</span>\');
}''',
'''function fe64_entHtml(html) {
  return String(html || "").replace(/([A-Z][A-Za-z0-9&;.\'-]{1,40}(?:\\s+[A-Z][A-Za-z0-9&;.\'-]{1,40}){0,4}\\s*\\(\\s*[A-Z][A-Z0-9.]{1,8}\\s*\\))/g, \'<span class="fe64-ent">$1</span>\');
}''',
'entity span keeps the token text')

# 2) Tags. Feed category is an argument again. Commodity subject, then
# strict equity, then the feed default. n.tg is written by _rt52Retag.
s = sub1(s, 'function _rt53bTag(text) {', 'function _rt53bTag(text, feedCat, src) {', 'tagger takes the feed')
s = sub1(s,
'''  if (fe64_cryptoStory(low, hit)) return "Crypto";
  if (fe64_equityStory(low, hit)) return "Stocks";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};
  Object.keys(rules).forEach(function (tag) {
    if (tag === "Crypto") return;
    var cfg = rules[tag] || {}, keys = cfg.k || [], s = 0;
    for (var i = 0; i < keys.length; i++) if (hit([keys[i]])) s += cfg.w || 1;
    if (s > bestScore) { bestScore = s; best = tag; }
  });
  return bestScore > 0 ? best : "Other";
}''',
'''  return fe65_storyTag(text, low, hit, feedCat, src);
}''',
'tag order is feed, commodity, then strict equity')
s = sub1(s,
'const tag=detectTag(title+" "+desc,feedMeta.cat);',
'const tag=detectTag(title+" "+desc,feedMeta.cat,feedMeta.src);',
'rss parse passes the feed')
s = sub1(s,
'''const t = detectTag(n.x + ' ' + (n.desc || ''), cat[n.src] || (n.company ? 'Stocks' : undefined)); if (t && t !== n.tg) n.tg = t;''',
'''const t = detectTag(n.x + ' ' + (n.desc || ''), cat[n.src] || (n.company ? 'Stocks' : undefined), n.src); if (t && t !== n.tg) n.tg = t;''',
'retag stores the chip tag')
s = sub1(s,
'''detectTag = function (text, feedCat) {
  var key = (text == null ? "" : String(text)) + "\\n" + (feedCat == null ? "" : String(feedCat));''',
'''detectTag = function (text, feedCat, src) {
  var key = (text == null ? "" : String(text)) + "\\n" + (feedCat == null ? "" : String(feedCat)) + "\\n" + (src == null ? "" : String(src));''',
'tag cache includes the feed source')

# 3) Quotes. Do not drop a status bag. Do not stamp a raw minute age.
# Chart close keeps status, note, nextOpen and delayMin when the meta has them.
s = sub1(s,
'''    label = proxy ? "CACHED·PROXY" : src === "session-cache" ? "CACHED" : src === "coingecko" ? "CACHED·CG" : src === "twelve-data" ? "CACHED·TD" : "CACHED·YH";''',
'''    label = proxy ? "CACHED" : src === "session-cache" ? "CACHED" : src === "coingecko" ? "CACHED" : src === "twelve-data" ? "CACHED" : "CACHED";''',
'cached label has no yh')
s = sub1(s,
'''        return { ...m, status: "stale", label: `STALE · ${age != null ? _fmtAge(tsMs) : "—"}`, detail: "Last good copy (the feed was busy or rate-limited). Not current market data." };''',
'''        return { ...m, status: "stale", label: "STALE", detail: "This price is not current." };''',
'stale label has no minute count')
s = sub1(s,
'''    const feedLbl = (d.status !== 'unavailable' && _rt20LastClose(a.tk)) ? 'CLOSED' : d.status === 'unavailable' ? 'NO SYNC' : (d.status === 'live' ? 'LIVE' : d.status === 'stale' ? 'STALE' : d.status === 'cached' ? 'CACHED' : d.status === 'proxy' ? 'PROXY' : 'DELAYED');''',
'''    const feedLbl = fe65_feedLbl(d, a.tk);''',
'analysis header uses the status formatter')
s = sub1(s,
'''  const feedLbl=(d.status!=="unavailable"&&_rt20LastClose(a.tk))?"CLOSED":d.status==="unavailable"?"NO SYNC":(d.status==="live"?"LIVE":d.status==="stale"?"STALE":d.status==="cached"?"CACHED":d.status==="proxy"?"PROXY":"DELAYED");''',
'''  const feedLbl=fe65_feedLbl(d, a.tk);''',
'live header uses the status formatter')
s = sub1(s,
'''  document.querySelectorAll(".rt43-feed").forEach(e => { const t = e.dataset.tk, d = fp(t); const lbl = (d.status !== "unavailable" && _rt20LastClose(t)) ? "CLOSED" : d.status === "unavailable" ? "NO SYNC" : d.status === "live" ? "LIVE" : d.status === "stale" ? "STALE" : d.status === "cached" ? "CACHED" : d.status === "proxy" ? "PROXY" : "DELAYED";''',
'''  document.querySelectorAll(".rt43-feed").forEach(e => { const t = e.dataset.tk, d = fp(t); const lbl = fe65_feedLbl(d, t);''',
'feed pill uses the status formatter')
s = sub1(s,
'''  if(s==="proxy")return `<span class="bd trust-stat trust-stat-delayed" title="${title}" style="background:var(--gdG);color:var(--gd);font-size:7.5px">${_escHtml(d.label||"PROXY")}</span>`;''',
'''  if(s==="proxy")return `<span class="bd trust-stat trust-stat-delayed" title="${title}" style="background:var(--gdG);color:var(--gd);font-size:7.5px">${_escHtml(d.label||"free feed")}</span>`;''',
'proxy pill does not say PROXY')
s = sub1(s,
'''    return _applyLiveQuote(tk, { p, ts: ts || undefined, marketClosed: true, source: "yahoo-chart-close", name: (m && (m.shortName || m.longName)) || "" }, "yahoo-chart-close");''',
'''    var fe65q = { p: p, ts: ts || undefined, marketClosed: true, source: "yahoo-chart-close", name: (m && (m.shortName || m.longName)) || "" };
    if (m && m.status) fe65q.status = m.status;
    if (m && m.note) fe65q.note = m.note;
    if (m && (m.nextOpen || m.nextOpen === 0)) fe65q.nextOpen = m.nextOpen;
    if (m && typeof m.delayMin === "number") fe65q.delayMin = m.delayMin;
    return _applyLiveQuote(tk, fe65q, "yahoo-chart-close");''',
'chart close keeps the status bag')
s = sub1(s,
'''    return {p:d.c,c:d.dp||0,prev:d.pc||d.c,change:d.d||0};''',
'''    return {p:d.c,c:d.dp||0,prev:d.pc||d.c,change:d.d||0,status:d.status,note:d.note,nextOpen:d.nextOpen,delayMin:d.delayMin};''',
'finnhub quote keeps status')
s = sub1(s,
'''  return {p:q.p, c:q.c, prev:q.prev, source:"finnhub"};''',
'''  return {p:q.p, c:q.c, prev:q.prev, source:"finnhub", status:q.status, note:q.note, nextOpen:q.nextOpen, delayMin:q.delayMin};''',
'finnhub ticker keeps status')
s = sub1(s,
'''  if (known) fe64_keepYq.map[key] = { status: st, delayMin: delayMin, note: note, nextOpen: nextOpen };
  else delete fe64_keepYq.map[key];''',
'''  if (!known && !note && nextOpen === "" && delayMin == null) return;
  var prev = fe64_keepYq.map[key] || {};
  var bag = { status: known ? st : (prev.status || ""), delayMin: delayMin != null ? delayMin : (prev.delayMin != null ? prev.delayMin : null), note: note || prev.note || "", nextOpen: nextOpen || prev.nextOpen || "" };
  if (bag.status) fe64_keepYq.map[key] = bag;''',
'a later quote without a status does not drop the bag')
s = sub1(s,
'''  else if (o.repaint) { _rt.dirty.add(tk); _rt.dir[tk] = 0; } // same value, new as-of: repaint without a flash
  return true;''',
'''  else if (o.repaint) { _rt.dirty.add(tk); _rt.dir[tk] = 0; } // same value, new as-of: repaint without a flash
  try { if (typeof fe64_keepYq === "function") fe64_keepYq(tk, o); } catch (e) {}
  return true;''',
'spot and stream applies keep a status when one was sent')
s = sub1(s,
'''function _rt43ApplySpot(tk, p, ts, src, name, pctHint) {''',
'''function _rt43ApplySpot(tk, p, ts, src, name, pctHint, bag) {''',
'spot apply accepts the server bag')
s = sub1(s,
'''  _rtApply(tk, p, { src, ts: _rt43Ms(ts), proxy: true, name, prev: pct != null ? p / (1 + pct / 100) : null, repaint: true });''',
'''  var fe65o = { src: src, ts: _rt43Ms(ts), proxy: true, name: name, prev: pct != null ? p / (1 + pct / 100) : null, repaint: true };
  if (bag && bag.status) fe65o.status = bag.status;
  if (bag && bag.note) fe65o.note = bag.note;
  if (bag && bag.nextOpen) fe65o.nextOpen = bag.nextOpen;
  if (bag && typeof bag.delayMin === "number") fe65o.delayMin = bag.delayMin;
  _rtApply(tk, p, fe65o);''',
'spot-energy forwards status, note, nextOpen and delayMin')
s = sub1(s,
'''["WTI", "BRENT"].forEach(tk => { const q = j[tk]; if (q && q.p > 0 && !q.stale) _rt43ApplySpot(tk, q.p, q.ts, "twelve-spot", q.name || `${tk} spot`, q.prev > 0 ? (q.p - q.prev) / q.prev * 100 : null); });''',
'''["WTI", "BRENT"].forEach(tk => { const q = j[tk]; if (q && q.p > 0 && !q.stale) _rt43ApplySpot(tk, q.p, q.ts, "twelve-spot", "spot", q.prev > 0 ? (q.p - q.prev) / q.prev * 100 : null, q); });''',
'spot-energy passes the quote object')

# 4) Jargon on the tape and the markets page.
s = sub1(s,
'''    detail = `${liveQuoteName[tk] || (src.startsWith("gold-api-spot-proxy") ? "Spot Gold (proxy)" : "Synthetic Dollar Index (proxy)")} · free reference API, not a live exchange instrument`;''',
'''    detail = `${liveQuoteName[tk] || (src.startsWith("gold-api-spot-proxy") ? "Gold" : "US dollar index")} · free market feed`;''',
'gold detail is a plain source note')
s = sub1(s,
'''        _rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Spot Gold (proxy)", repaint: true, ...((_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) ? { prev: p / (1 + _rt.gcPct.c / 100) } : { noBasePrev: true }) });''',
'''        _rtApply("XAU", p, { src: "gold-api-spot-proxy-browser", ts, proxy: true, name: "Gold", repaint: true, ...((_rt.gcPct && Date.now() - _rt.gcPct.at < 6 * 3600_000) ? { prev: p / (1 + _rt.gcPct.c / 100) } : { noBasePrev: true }) });''',
'gold tape name is Gold')
s = sub1(s,
'''    ? (liveQuoteName.XAU || "Spot Gold (proxy)")''',
'''    ? (liveQuoteName.XAU || "Gold")''',
'front door gold name')
s = sub1(s,
'''      ? (liveQuoteName.DXY || "Synthetic Dollar Index (proxy)")''',
'''      ? (liveQuoteName.DXY || "US dollar index")''',
'front door dollar name')
s = sub1(s,
'''  return _frontDoorQuote("XAU", "GOLD", "spot proxy") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index");''',
'''  return _frontDoorQuote("XAU", "GOLD", "free feed") + _frontDoorQuote("DXY", "DOLLAR", "US dollar index");''',
'front door gold description')
s = sub1(s,
'''  const title=_escAttr(`${d.label||s}${d.asOf?` · as of ${_fmtAsOf(d.asOf)} (${d.age})`:""}${d.detail?` · ${d.detail}`:""}`);''',
'''  const title=_escAttr(`${d.label||s}${d.asOf?` · as of ${_fmtAsOf(d.asOf)}`:""}${d.detail?` · ${d.detail}`:""}`);''',
'status title has no raw minute age')
s = sub1(s,
'''  if(d.status==="closed")return d.fe64Note?`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · ${_escHtml(d.fe64Note)}</span>`:`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · last close ${_rt18CloseLbl(_rt20LastClose(tk) || d.asOf)}</span>`;
  return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · as of ${_fmtAsOf(d.asOf)} · ${d.age}</span>`;''',
'''  if(d.status==="closed")return d.fe64Note?`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · ${_escHtml(d.fe64Note)}</span>`:`<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · CLOSED · last close ${_rt18CloseLbl(_rt20LastClose(tk) || d.asOf)}</span>`;
  return `<span class="asof-tag" title="${_escAttr(d.detail||"")}">${_escHtml(_quoteSourceLabel(d.src))} · as of ${_fmtAsOf(d.asOf)}</span>`;''',
'as-of line has no raw minute age')
s = sub1(s,
'''      <span class="trust-asof">Feed as of <strong>${asOf}</strong> (${age})</span>''',
'''      <span class="trust-asof">Feed as of <strong>${asOf}</strong></span>''',
'trust bar has no raw minute age')
s = sub1(s,
'''  return `<div class="front-door-quote-paxg" title="PAX Gold (PAXG) trading on ${_escAttr(x.venue)} — a tokenised-gold proxy that can sit at a premium or discount to spot. Not the XAU spot price.">PAXG ≈ $${_escHtml(px)} · ${_escHtml(x.venue)} stream · tokenised-gold proxy · last trade ${_escHtml(age)} ago</div>`;''',
'''  return `<div class="front-door-quote-paxg" title="PAX Gold (PAXG) trading on ${_escAttr(x.venue)}. Not the XAU spot price.">PAXG ≈ $${_escHtml(px)} · ${_escHtml(x.venue)} stream · tokenised gold · last trade ${_escHtml(age)} ago</div>`;''',
'paxg line does not say proxy')
s = sub1(s,
'''        if (wood && wood.p > 0 && _applyLiveQuote("LUMBER", { ...wood, name: wood.name || "Lumber ETF proxy (WOOD)" }, "yahoo")) {''',
'''        if (wood && wood.p > 0 && _applyLiveQuote("LUMBER", { ...wood, name: wood.name || "Lumber ETF (WOOD)" }, "yahoo")) {''',
'lumber name does not say proxy')
s = sub1(s,
'''<span class="openbb-meta">Dispatch live/free fallback remains in the surrounding view.</span>''',
'',
'remove the dispatch fallback sentence')
s = sub1(s,
'''  h += `<div class="surface-note" role="note"><strong>How to read this view</strong><span>Primary prices appear only when a qualifying fresh quote is available. Delayed, cached, proxy, and historical values stay labelled as context.</span></div>`;''',
'''  h += `<div class="surface-note" role="note"><span>Prices come from free market feeds; some are delayed.</span></div>`;''',
'one plain markets line')

# 5) Tape uses the formatted words, and Gold is the gold name.
s = sub1(s,
'''    return `<span class="ti" data-tk="${k}" title="${title}"><span style="color:${catCol};font-weight:700">${k}${badge}</span><span style="color:var(--tx);font-weight:700">${d.p}</span><span style="color:${chCol};font-weight:600">${ch==null?"—":chSign+d.c+"%"}</span></span>`;''',
'''    return `<span class="ti" data-tk="${k}" title="${_escAttr(fe65_tapeName(k) + " · " + (d.fe64Note || d.label || ""))}"><span style="color:${catCol};font-weight:700">${fe65_tapeName(k)}${_rtTapeBadge(d)}</span><span style="color:var(--tx);font-weight:700">${d.p}</span><span style="color:${chCol};font-weight:600">${ch==null?"—":chSign+d.c+"%"}</span></span>`;''',
'tape first paint uses the formatter')
s = sub1(s,
'''      if (el.dataset.rtSt !== d.status) { el.dataset.rtSt = d.status; k[0].innerHTML = `${_escHtml(tk)}${_rtTapeBadge(d)}`; }
      el.title = `${tk} · ${d.label || "NO SYNC"}${d.asOf ? ` · as of ${_fmtAsOf(d.asOf)}` : ""}`;''',
'''      var fe65sig = (d.status || "") + "|" + (d.fe64Note || "") + "|" + (d.label || "");
      if (el.dataset.rtSt !== fe65sig) { el.dataset.rtSt = fe65sig; k[0].innerHTML = `${_escHtml(fe65_tapeName(tk))}${_rtTapeBadge(d)}`; }
      el.title = `${fe65_tapeName(tk)} · ${d.fe64Note || d.label || "NO SYNC"}`;''',
'tape repaint uses the formatter')

BLOCK = r'''
// ── rt55 ──
// fe65-tag-begin
function fe65_feedCrypto(feedCat, src) {
  var s = (String(feedCat || "") + " " + String(src || "")).toLowerCase();
  if (s.indexOf("crypto") >= 0) return true;
  return /\b(coindesk|cointelegraph|decrypt)\b/.test(s) || /\bthe block\b/.test(s);
}
function fe65_commoditySubject(text) {
  var head = String(text || "").replace(/\s+/g, " ").trim().slice(0, 240);
  if (/\b(gold|silver|copper|oil|crude|brent|wti)\s+(miner|miners|shares|stock|stocks|equity|equities)\b/i.test(head)) return false;
  if (/^(?:the\s+|spot\s+)?(gold|silver|copper|oil|crude|brent|wti|wheat|corn|coffee|cocoa|lumber|platinum|palladium|nickel|natural gas)\b/i.test(head)) return true;
  return /\b(gold|silver|copper|oil|crude|brent|wti)\s+(?:price|prices|futures?)?\s*(?:rises|rise|falls|fall|climbs|climb|drops|drop|jumps|jump|slides|slide|gains|gain|surges|surge|tumbles|tumble|holds|hold)\b/i.test(head);
}
function fe65_exchTicker(text) {
  var raw = String(text || "");
  if (/\(\s*(?:nyse|nasdaq|lse|amex|tsx|asx|hkex|xetra|euronext|krx)\s*:\s*[a-z0-9][a-z0-9.\-]{0,12}\s*\)/i.test(raw)) return true;
  return /(?:^|[^a-z0-9])(?:nyse|nasdaq|lse|amex|tsx|asx|hkex)\s*:\s*[a-z0-9][a-z0-9.\-]{0,12}(?:$|[^a-z0-9])/i.test(raw);
}
function fe65_strictEquity(low, hit, raw) {
  if (fe65_exchTicker(raw)) return true;
  var names = ["bp", "shell", "exxon", "exxonmobil", "chevron", "conocophillips", "totalenergies", "equinor", "micron", "apple", "microsoft", "nvidia", "tesla", "amazon", "meta", "alphabet", "jpmorgan", "broadcom", "intel"];
  var stockWord = hit(["stock", "stocks", "share", "shares", "equity", "equities"]);
  if (hit(names) && stockWord) return true;
  var stop = { the: 1, and: 1, for: 1, are: 1, but: 1, not: 1, you: 1, all: 1, can: 1, had: 1, her: 1, was: 1, one: 1, our: 1, out: 1, day: 1, get: 1, has: 1, him: 1, his: 1, how: 1, man: 1, new: 1, now: 1, old: 1, see: 1, two: 1, way: 1, who: 1, oil: 1, gold: 1, sec: 1, ai: 1, fed: 1, etf: 1, ceo: 1, usd: 1, eur: 1, gbp: 1, top: 1, low: 1, big: 1, run: 1, key: 1, per: 1, via: 1 };
  var found = false;
  try {
    if (typeof A !== "undefined" && A && A.forEach) A.forEach(function (a) {
      if (found || !a || a.cat !== "Stock") return;
      var tk = String(a.tk || "").toLowerCase();
      if (tk.length < 3 || tk.length > 6 || stop[tk]) return;
      if (hit([tk])) found = true;
    });
  } catch (e) {}
  return found;
}
function fe65_hasMarket(low, hit, raw) {
  if (fe65_commoditySubject(raw) || fe65_strictEquity(low, hit, raw)) return true;
  if (hit(["stock", "stocks", "share", "shares", "equity", "equities", "bitcoin", "crypto", "ethereum", "btc", "eth", "blockchain", "gold", "silver", "copper", "oil", "crude", "brent", "wti"])) return true;
  var rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};
  var keys = Object.keys(rules);
  for (var i = 0; i < keys.length; i++) {
    var list = (rules[keys[i]] || {}).k || [];
    if (hit(list)) return true;
  }
  return false;
}
function fe65_storyTag(text, low, hit, feedCat, src) {
  var raw = String(text || "");
  if (!fe65_hasMarket(low, hit, raw)) return "Other";
  if (fe65_commoditySubject(raw)) return "Commodities";
  if (fe65_strictEquity(low, hit, raw)) return "Stocks";
  if (fe65_feedCrypto(feedCat, src)) return "Crypto";
  if (typeof fe64_cryptoStory === "function" && fe64_cryptoStory(low, hit)) return "Crypto";
  var best = "", bestScore = 0, rules = (typeof TAG_RULES === "object" && TAG_RULES) || {};
  Object.keys(rules).forEach(function (tag) {
    if (tag === "Crypto" || tag === "Stocks" || tag === "Earnings") return;
    var cfg = rules[tag] || {}, keys = cfg.k || [], sc = 0;
    for (var i = 0; i < keys.length; i++) if (hit([keys[i]])) sc += cfg.w || 1;
    if (sc > bestScore) { bestScore = sc; best = tag; }
  });
  if (bestScore > 0 && typeof fe64_chip === "function") return fe64_chip(best);
  if (bestScore > 0) return best;
  if (feedCat && typeof fe64_chip === "function") return fe64_chip(feedCat);
  return "Other";
}
// fe65-tag-end
// fe65-quote-begin
function fe65_scrub(s) {
  var t = String(s == null ? "" : s);
  var keepMin = /by the exchange|by exchange/i.test(t);
  t = t.replace(/cached\s*[·.\-]?\s*yh/ig, "CACHED");
  t = t.replace(/\bxau\s+spot\s+proxy\b/ig, "Gold");
  t = t.replace(/\bspot\s+proxy\b/ig, "");
  t = t.replace(/gold-api\.com/ig, "");
  t = t.replace(/\bproxy\b/ig, "");
  if (!keepMin) {
    t = t.replace(/\bdelayed\s+\d+\s*m\b/ig, "delayed");
    t = t.replace(/\s*·\s*\d+\s*m\b/ig, "");
    t = t.replace(/\b\d+\s*m\b/ig, "");
    t = t.replace(/\bas of\s+ago\b/ig, "");
  }
  return t.replace(/\s{2,}/g, " ").replace(/\s+([,.;)])/g, "$1").replace(/^[\s·\-]+|[\s·\-]+$/g, "").trim();
}
function fe65_opensFrom(ms) {
  var hm = "";
  try { hm = fe64_ukHm(ms); } catch (e) { hm = ""; }
  return hm ? "opens " + hm + " UK" : "";
}
function fe65_closedNote(tk, bag) {
  var note = "";
  try { note = fe64_plainNote(bag && bag.note); } catch (e) { note = ""; }
  if (note && /opens\s+\d/.test(note)) return note;
  var hm = "";
  try { hm = fe64_ukHm(bag && bag.nextOpen); } catch (e) { hm = ""; }
  if (hm) return "opens " + hm + " UK";
  if (!(bag && bag.status)) {
    var ms = 0;
    try { ms = _rt51Next(tk); } catch (e2) { ms = 0; }
    var cal = fe65_opensFrom(ms);
    if (cal) return cal;
  }
  return fe65_scrub(note);
}
function fe65_finishQuote(tk, m) {
  if (!m || m.status === "unavailable") return m;
  var key = tk;
  try { if (typeof resolveInternalTicker === "function") key = resolveInternalTicker(tk) || tk; } catch (e) {}
  var bag = null;
  try { bag = fe64_yqBag(key); } catch (e) {}
  var open = true;
  try { open = !!_rt18MarketOpen(key); } catch (e) {}
  var o = Object.assign({}, m);
  if (bag && bag.status) {
    try { o = fe64_quoteApply(key, o) || o; } catch (e) {}
    if (bag.status === "closed") {
      var words = fe65_closedNote(key, bag);
      o.status = "closed";
      o.label = "CLOSED";
      o.fe64Note = words;
      o.detail = words || "Market closed";
    }
  } else if (!open && o.status !== "live") {
    var calWords = fe65_closedNote(key, null);
    o.status = "closed";
    o.label = "CLOSED";
    o.fe64Note = calWords;
    o.detail = calWords || "Market closed";
  } else if (o.status === "stale" || /STALE/i.test(String(o.label || ""))) {
    o.status = "stale";
    o.label = "STALE";
    o.detail = "This price is not current.";
    o.fe64Note = "";
  }
  var src = String(o.src || "");
  if (key === "XAU" || /gold-api/i.test(src)) {
    o.detail = "Gold · free market feed";
    if (o.status === "proxy" || /proxy/i.test(String(o.label || ""))) {
      if (!open) {
        o.status = "closed";
        o.label = "CLOSED";
        o.fe64Note = o.fe64Note && /opens\s+\d/.test(o.fe64Note) ? o.fe64Note : fe65_closedNote(key, bag);
      } else {
        o.status = "delayed";
        o.label = "free feed";
        o.fe64Note = "free feed";
      }
    }
  }
  o.label = fe65_scrub(o.label);
  o.detail = fe65_scrub(o.detail);
  o.fe64Note = fe65_scrub(o.fe64Note);
  if (!o.label) o.label = o.status === "closed" ? "CLOSED" : o.status === "stale" ? "STALE" : o.status === "live" ? "LIVE" : "free feed";
  if (o.status === "closed" && o.fe64Note && !/opens\s+\d|free feed/i.test(o.label)) o.detail = o.fe64Note;
  return o;
}
function fe65_feedLbl(d, tk) {
  if (!d || d.status === "unavailable") return "NO SYNC";
  if (d.status === "closed") return "CLOSED" + (d.fe64Note ? " · " + d.fe64Note : "");
  if (d.status === "live") return "LIVE";
  if (d.status === "stale") return "STALE";
  if (d.status === "quiet") return d.fe64Note || "Quiet";
  if (d.status === "delayed") return fe65_scrub(d.fe64Note || d.label || "delayed");
  if (d.status === "cached") return "CACHED";
  if (d.status === "proxy") return fe65_scrub(d.label || "") || "free feed";
  try { if (tk && _rt20LastClose(tk)) return "CLOSED" + (d.fe64Note ? " · " + d.fe64Note : ""); } catch (e) {}
  return fe65_scrub(d.label || d.status || "delayed");
}
function fe65_tapeName(tk) {
  var key = tk;
  try { if (typeof resolveInternalTicker === "function") key = resolveInternalTicker(tk) || tk; } catch (e) {}
  return key === "XAU" ? "Gold" : String(tk || "");
}
function fe65_tapeWords(d) {
  if (!d) return "";
  if (d.status === "live") return "";
  if (d.status === "closed") return "CLOSED" + (d.fe64Note ? " · " + d.fe64Note : "");
  if (d.status === "stale") return "STALE";
  if (d.status === "quiet") return d.fe64Note || "Quiet";
  if (d.fe64Note) return d.fe64Note;
  return fe65_scrub(d.label || "");
}
// fe65-quote-end
try {
  (typeof NEWS !== "undefined" ? NEWS : []).forEach(function (n) { if (n) delete n._rt52; });
  if (typeof _rt52Retag === "function") _rt52Retag();
} catch (e) {}
try {
  var fe65_qm = _quoteMeta;
  _quoteMeta = function (tk) {
    var m = fe65_qm.apply(this, arguments);
    try { m = fe65_finishQuote(tk, m); } catch (e) {}
    return m;
  };
} catch (e) {}
try {
  var fe65_tb = _rtTapeBadge;
  _rtTapeBadge = function (d) {
    try {
      var words = fe65_tapeWords(d);
      if (d && words && d.status !== "live" && d.status !== "unavailable") {
        var cls = d.status === "delayed" ? "tape-del" : d.status === "stale" ? "tape-stale" : "tape-cache";
        return '<span class="tape-badge ' + cls + '" title="' + _escAttr(fe65_scrub(d.detail || words)) + '">' + _escHtml(words) + '</span>';
      }
    } catch (e) {}
    return fe65_tb.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe65_sl = _quoteSourceLabel;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe65_sl.apply(this, arguments); } catch (e) { out = String(src || ""); }
    if (/gold-api|spot proxy|proxy/i.test(String(src || "") + " " + out)) {
      if (/gold/i.test(String(src || "") + " " + out)) return "free gold feed";
      return "free market feed";
    }
    return fe65_scrub(out) || out;
  };
} catch (e) {}
function fe65_guestChrome() {
  var guest = false;
  try { guest = typeof _isVisitor === "function" && _isVisitor(); } catch (e) {}
  try { document.body.classList.toggle("fe65-guest", !!guest); } catch (e) {}
  if (!guest) return;
  try { if (typeof renderSidebarNav === "function") renderSidebarNav(); } catch (e) {}
  try { if (typeof renderNav === "function") renderNav(); } catch (e) {}
}
try {
  var fe65_ra = renderAuthButtons;
  renderAuthButtons = function () {
    var r = fe65_ra.apply(this, arguments);
    try { fe65_guestChrome(); } catch (e) {}
    return r;
  };
} catch (e) {}
try { fe65_guestChrome(); } catch (e) {}
try {
  var st65 = document.createElement("style");
  st65.setAttribute("data-fe65", "chat");
  st65.textContent = ".fe64-ent,.fe65-ent{display:inline;white-space:nowrap}.panel,.panel-body{min-width:0}.panel{overflow:hidden}.panel-body{overflow:auto}.tt th{z-index:0}.nf-wrap{display:flex;flex-wrap:wrap;gap:8px;padding:6px 0 10px;position:relative;z-index:2}.news-toolbar{position:relative;z-index:2}@media (min-width:768px) and (max-width:1320px){.panel-grid{grid-template-columns:minmax(0,1fr)!important;grid-template-rows:auto!important}.panel{min-height:240px}}@media (min-width:768px){body.fe65-guest .terminal-wrap{display:flex!important;visibility:visible!important}body.fe65-guest .cmd-bar,body.fe65-guest .sidebar{display:flex!important;visibility:visible!important;position:relative;z-index:80}body.fe65-guest #cmdAuthBtn{display:flex!important;flex:0 0 auto;visibility:visible!important}body.fe65-guest .cmd-bar{background:var(--paper,#14151a)}body.fe65-guest .term-overlay.front-door-overlay{top:var(--desk-chrome,92px);left:var(--sidebar-w,172px);z-index:40}}@media (max-width:767px){body.fe65-guest .hdr{display:flex!important;visibility:visible!important;position:sticky;top:0;z-index:80;background:var(--paper,#14151a)}body.fe65-guest .bnav{display:flex!important;visibility:visible!important}body.fe65-guest #hdrAuthBtn{display:flex!important;visibility:visible!important}body.fe65-guest .term-overlay.front-door-overlay{top:52px;left:0;z-index:40}}body.fe65-guest .term-overlay-account{display:none!important}";
  document.head.appendChild(st65);
} catch (e) {}
'''
if '// ── rt55 ──' in s: die('rt55 marker landed twice')
s = s.rstrip('\n') + '\n' + BLOCK
h = sub1(h, 'app.js?v=' + base + '"', 'app.js?v=' + nxt + '"', 'cache bust')

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
    t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
if r.returncode: die('node --check failed: ' + (r.stderr or '')[:800])
print('OK rt55: %s -> %s; node --check passed%s' % (base, nxt, ' (dry run)' if CHECK else ''))
if not CHECK:
    open(APP, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    open(IDX, 'wb').write((h.replace('\n', '\r\n') if hcrlf else h).encode('utf-8'))
    print('written', APP, IDX)
