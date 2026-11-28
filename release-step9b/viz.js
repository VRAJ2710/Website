/* chat114viz: Market Snapshot, gauge bars, key-price row, sparklines, events timeline and tiles for
   /brief/, /gold/, /markets/, /research/. Reads only this site's own free /api endpoints. Never invents a number:
   a missing reading renders as "Not available". Plain names only (no tickers or series codes). Not investment advice. */
(function () {
  if (window.__chat114viz) return; window.__chat114viz = 1;
  var root = document.getElementById('chat114viz'); if (!root) return;
  var PAGE = root.getAttribute('data-cz-page') || 'brief';
  try { document.documentElement.classList.add('cz-on', 'cz-' + PAGE); } catch (e) {}
  var NA = 'Not available';
  var MINUS = '\u2212';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function num(v) { return typeof v === 'number' && isFinite(v); }
  function fmt(v, dp) { return num(v) ? v.toLocaleString('en-GB', { minimumFractionDigits: dp, maximumFractionDigits: dp }) : NA; }
  function signed(v, dp, unit) { if (!num(v)) return null; var r = Math.abs(v).toFixed(dp); if (+r === 0) return '0' + (dp ? '.' + '0'.repeat(dp) : '') + unit; return (v > 0 ? '+' : MINUS) + Number(r).toLocaleString('en-GB', { minimumFractionDigits: dp, maximumFractionDigits: dp }) + unit; }
  function dir(v) { return !num(v) ? 'na' : (Math.abs(v) < 1e-9 ? 'flat' : (v > 0 ? 'up' : 'down')); }
  var UKF = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/London', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false });
  var UKD = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/London', weekday: 'short', day: 'numeric', month: 'short' });
  function ukTime(t) { if (t == null || t === '') return null; var d = new Date(typeof t === 'number' && t < 1e12 ? t * 1000 : t); if (isNaN(d)) return null; var p = {}; UKF.formatToParts(d).forEach(function (x) { p[x.type] = x.value; }); return p.weekday + ' ' + p.day + ' ' + p.month + ', ' + p.hour + ':' + p.minute + ' UK'; }
  function ukDay(iso) { if (!iso) return null; var d = new Date(String(iso).length === 10 ? iso + 'T12:00:00Z' : iso); return isNaN(d) ? null : UKD.format(d).replace(',', ''); }
  function cleanSrc(s) { s = String(s || ''); return s.replace(/\s*\((?:[A-Z0-9^=.\-]{1,12})\)\s*/g, ' ').replace(/\s+/g, ' ').trim(); }
  function get1(u, ms) { return new Promise(function (ok) { var c = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (c) c.abort(); ok(null); }, ms); fetch(u, { credentials: 'same-origin', cache: 'no-store', signal: c ? c.signal : undefined }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { clearTimeout(t); ok(j); }).catch(function () { clearTimeout(t); ok(null); }); }); }
  // one retry after a short pause: a feed that still does not answer is shown as Not available, never filled in
  function get(u) { return get1(u, 15000).then(function (j) { return j || new Promise(function (r) { setTimeout(r, 1500); }).then(function () { return get1(u, 15000); }); }); }
  function lagOf(o) {
    // the lag label: how old / how delayed the number is
    var bits = [];
    if (o.daily) bits.push('daily figure for ' + (ukDay(o.daily) || o.daily));
    else if (num(o.delayMin) && o.delayMin > 0) bits.push('delayed ' + o.delayMin + ' min');
    else if (o.live && o.status !== 'closed') bits.push('live');
    else bits.push('latest quote');
    if (o.status === 'closed') bits.push('market closed, last price');
    if (o.stale) bits.push('stored reading, not refreshed');
    return bits.join(' \u00b7 ');
  }
  function meta(o) { return [o.src || 'Source not given', o.time || 'time not given', lagOf(o)].join(' \u00b7 '); }

  // ---------- normalise the feeds into display items ----------
  var DQN = { SLV: ['Silver futures (COMEX, front month)', '$', 2], WTI: ['WTI crude oil futures (NYMEX, front month)', '$', 2], NG: ['US natural gas futures (NYMEX, front month)', '$', 3],
    DXY: ['US Dollar Index (ICE)', '', 2], EURUSD: ['Euro in US dollars', '$', 4], GBPUSD: ['Pound in US dollars', '$', 4], USDJPY: ['US dollar in yen', '\u00a5', 2],
    TNX: ['US 10-year Treasury yield (Cboe index)', '', 2, '%'], SPX: ['S&P 500', '', 2], DJIA: ['Dow Jones Industrial Average', '', 2], IXIC: ['Nasdaq Composite', '', 2], VIX: ['Cboe volatility index (VIX)', '', 2] };
  var CRN = { BTC: ['Bitcoin', 0], ETH: ['Ether', 2], SOL: ['Solana', 2] };
  function naItem(name, why) { return { name: name, na: true, why: why }; }
  function fromDesk(dq, k) {
    var q = dq && dq.quotes && dq.quotes[k], n = DQN[k]; if (!q || !num(q.price)) return naItem(n[0]);
    var it = { name: n[0], value: (n[1] || '') + fmt(q.price, n[2]) + (n[3] || ''), pct: q.changePct, basis: 'vs previous close',
      src: cleanSrc(q.sourceLabel || q.source), time: q.asOfUk || ukTime(q.asOf), delayMin: q.delayMin, status: q.status };
    if (k === 'TNX' && num(q.changePp)) { it.chgText = signed(q.changePp * 100, 1, ' bp'); it.chgDir = dir(q.changePp); }
    return it;
  }
  function fromCrypto(cs, coin) {
    var r = cs && cs.rows && cs.rows.filter(function (x) { return x.coin === coin; })[0], n = CRN[coin];
    if (!r || !r.available || !num(r.price)) return naItem(n[0]);
    return { name: n[0], value: '$' + fmt(r.price, n[1]), pct: r.changePct, basis: 'over 24 hours', src: 'Coinbase Exchange', time: r.asOfUk || ukTime(r.asOf), live: true, status: 'open',
      range: (num(r.low24h) && num(r.high24h) && r.high24h > r.low24h) ? { lo: r.low24h, hi: r.high24h, v: r.price, dp: n[1], label: '24-hour range' } : null };
  }
  function goldSpot(mrq) {
    var x = mrq && mrq.XAU; if (!x || !num(x.p)) return naItem('Gold spot (US$ per troy ounce)');
    var f = x.feed || {}, fut = x.futuresChange || x.futures;
    var it = { name: 'Gold spot (US$ per troy ounce)', value: '$' + fmt(x.p, 2), pct: null, chgText: 'Spot change not available', chgDir: 'na',
      src: f.sourceLabel || x.sourceLabel || 'gold-api.com spot price', time: f.asOfUk || ukTime(x.ts), live: num(f.ageSec) && f.ageSec < 600, status: x.status === 'closed' ? 'closed' : null, stale: !!x.stale };
    if (fut && num(fut.price)) {
      it.second = 'Gold futures (COMEX, front month): $' + fmt(fut.price, 2) + (num(fut.changePct) ? ' ' + signed(fut.changePct, 2, '%') + ' vs previous close' : '') +
        ' \u00b7 ' + cleanSrc(fut.source) + ' \u00b7 ' + (fut.asOfUk || ukTime(fut.asOf)) + ' \u00b7 delayed ' + (fut.delayMin || 10) + ' min. This is the futures change, not spot\u2019s.';
      it.futPct = fut.changePct;
    }
    return it;
  }
  function tenYear(dq, dgs) {
    var it = fromDesk(dq, 'TNX'); it.name = 'US 10-year Treasury yield';
    if (dgs && dgs.available && num(dgs.value)) it.second = 'Official daily close (US Treasury via FRED): ' + fmt(dgs.value, 2) + '% for ' + (ukDay(dgs.date) || dgs.date) + (num(dgs.change) ? ', ' + signed(dgs.change * 100, 0, ' bp') + ' on the day before' : '') + '.';
    return it;
  }
  function realYield(rates, ry) {
    var t = rates && rates.tips, it;
    if (t && num(t.value)) it = { name: 'US 10-year real yield (inflation-protected)', value: fmt(t.value, 2) + '%', chgText: num(t.change) ? signed(t.change * 100, 1, ' bp') : null, chgDir: dir(t.change), basis: 'vs previous close',
      src: cleanSrc(t.src), time: t.asOfUk || ukTime(t.asOfMs), delayMin: null, status: null };
    else it = naItem('US 10-year real yield (inflation-protected)');
    if (ry && ry.available && num(ry.value)) it.second = 'Official daily close (US Treasury via FRED): ' + fmt(ry.value, 2) + '% for ' + (ukDay(ry.date) || ry.date) + '.';
    return it;
  }
  function wti(dq, eia) {
    var it = fromDesk(dq, 'WTI');
    if (eia && eia.available && eia.WTI && num(eia.WTI.p)) it.second = 'Official daily price (EIA via FRED): $' + fmt(eia.WTI.p, 2) + ' a barrel for ' + (ukDay(eia.WTI.date) || eia.WTI.date) + '.';
    return it;
  }
  function goldSpark(ch, n) {
    if (!ch || ch.status !== 'ok' || !ch.bars || ch.bars.length < 5) return null;
    var bars = ch.bars.filter(function (b) { return num(b.c); }), last = bars.slice(-n);
    return { pts: last.map(function (b) { return b.c; }), from: last[0].sessionDate, to: last[last.length - 1].sessionDate, all: bars, stale: ch.cacheState === 'stale', label: 'Gold futures (COMEX, front month), daily closes, ' + cleanSrc(ch.source) };
  }

  // ---------- render helpers ----------
  function chg(it) {
    if (it.na) return '<span class="cz-chg cz-na">' + NA + '</span>';
    if (it.chgText) return '<span class="cz-chg cz-' + (it.chgDir || 'na') + '">' + esc(it.chgText) + '</span>';
    var s = signed(it.pct, 2, '%'); return s ? '<span class="cz-chg cz-' + dir(it.pct) + '" title="' + esc(it.basis || '') + '">' + esc(s) + '</span>' : '<span class="cz-chg cz-na">Change not available</span>';
  }
  function spark(sp, w, h, cls) {
    if (!sp || !sp.pts || sp.pts.length < 2) return '';
    var p = sp.pts, lo = Math.min.apply(null, p), hi = Math.max.apply(null, p), rg = hi - lo || 1, pad = 2;
    var d = p.map(function (v, i) { return (i ? 'L' : 'M') + (pad + i * (w - 2 * pad) / (p.length - 1)).toFixed(1) + ' ' + (pad + (h - 2 * pad) * (1 - (v - lo) / rg)).toFixed(1); }).join(' ');
    var up = p[p.length - 1] >= p[0];
    return '<svg class="cz-spark ' + (cls || '') + ' cz-' + (up ? 'up' : 'down') + '" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" role="img" aria-label="' + esc(sp.label + ', ' + p.length + ' closes from ' + ukDay(sp.from) + ' to ' + ukDay(sp.to)) + '"><path d="' + d + ' L' + (w - pad) + ' ' + h + ' L' + pad + ' ' + h + ' Z" class="cz-area"/><path d="' + d + '" class="cz-line"/></svg>';
  }
  function rangeBar(r) {
    if (!r) return '';
    var pos = Math.max(0, Math.min(100, (r.v - r.lo) / (r.hi - r.lo) * 100));
    return '<div class="cz-range" aria-label="' + esc(r.label) + '"><span class="cz-rtrack"><i style="left:' + pos.toFixed(1) + '%"></i></span><span class="cz-rlab"><b>' + esc(fmt(r.lo, r.dp)) + '</b><em>' + esc(r.label) + '</em><b>' + esc(fmt(r.hi, r.dp)) + '</b></span></div>';
  }
  function bigPrice(it) {
    if (it.na) return '<div class="cz-p3"><div class="cz-pn">' + esc(it.name) + '</div><div class="cz-pv cz-nav">' + NA + '</div><div class="cz-src">No reading from this site\u2019s free feed right now. Nothing was filled in.</div></div>';
    return '<div class="cz-p3"><div class="cz-pn">' + esc(it.name) + '</div><div class="cz-pv">' + esc(it.value) + '</div>' + chg(it) +
      (it.spark ? spark(it.spark, 160, 34, 'cz-sp3') : '') + '<div class="cz-src">' + esc(meta(it)) + '</div>' + (it.second ? '<div class="cz-sec">' + esc(it.second) + '</div>' : '') + '</div>';
  }
  function chip(it) {
    if (it.na) return '<li class="cz-chip cz-chipna"><span class="cz-cn">' + esc(it.name) + '</span><span class="cz-cv cz-nav">' + NA + '</span><span class="cz-src">No reading right now. Nothing was filled in.</span></li>';
    return '<li class="cz-chip"><span class="cz-cn">' + esc(it.name) + '</span><span class="cz-crow"><span class="cz-cv">' + esc(it.value) + '</span>' + chg(it) + '</span>' +
      (it.spark ? spark(it.spark, 120, 26, 'cz-spc') + '<span class="cz-spl">' + esc(it.spark.pts.length + ' daily closes to ' + ukDay(it.spark.to)) + '</span>' : '') + rangeBar(it.range) +
      '<span class="cz-src">' + esc(meta(it)) + '</span>' + (it.second ? '<span class="cz-sec">' + esc(it.second) + '</span>' : '') + '</li>';
  }
  function gauge(g) {
    if (!g || g.na) return '<div class="cz-g cz-gna"><div class="cz-gh"><span>' + esc(g.name) + '</span><b class="cz-nav">' + NA + '</b></div><div class="cz-gt"><i style="width:0"></i></div><p class="cz-why">' + esc(g.why || '') + '</p></div>';
    var pct = Math.max(0, Math.min(100, g.pct));
    return '<div class="cz-g"><div class="cz-gh"><span>' + esc(g.name) + '</span><b>' + esc(g.valueText) + '</b></div>' +
      '<div class="cz-gt cz-g-' + (g.tone || 'neutral') + '" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + Math.round(pct) + '" aria-label="' + esc(g.name) + '"><i style="width:' + pct.toFixed(1) + '%"></i>' + (g.marks || []).map(function (m) { return '<s style="left:' + m + '%"></s>'; }).join('') + '</div>' +
      '<div class="cz-gs"><span>' + esc(g.lo) + '</span><span>' + esc(g.hi) + '</span></div><p class="cz-why">' + esc(g.why) + '</p><div class="cz-src">' + esc(g.meta) + '</div></div>';
  }
  function card(id, kicker, title, why, body, extra) {
    return '<div class="cz-card ' + (extra || '') + '" id="' + id + '"><div class="cz-ch"><span class="cz-k">' + esc(kicker) + '</span><h2 class="cz-h">' + esc(title) + '</h2><p class="cz-what">' + esc(why) + '</p></div>' + body + '</div>';
  }

  // ---------- gauges ----------
  function gRisk(rg) {
    if (!rg || !rg.available || !num(rg.score)) return { na: true, name: 'Risk appetite gauge', why: 'Our five-input regime score did not arrive. Nothing was filled in.' };
    return { name: 'Risk appetite gauge (ours)', valueText: rg.score + ' of 100 \u00b7 ' + (rg.label || rg.regime || ''), pct: rg.score, tone: rg.score >= 60 ? 'up' : (rg.score < 45 ? 'down' : 'mid'), marks: [45, 60],
      lo: '0 \u00b7 risk-off', hi: 'risk-on \u00b7 100',
      why: 'Summarises five market inputs (volatility, the S&P 500 move, the dollar, oil and the Bitcoin move) into one score. Below 45 reads as risk-off, 45 to 59 mixed, 60 and above risk-on. It describes conditions; it is not a forecast.',
      meta: 'Dispatch regime model (ours), inputs from Yahoo Finance and Coinbase Exchange \u00b7 ' + (rg.computedAtUk || rg.asOfUk || ukTime(rg.asOf) || 'time not given') + ' \u00b7 recomputed every 10 min' + (rg.stale ? ' \u00b7 stored reading' : '') };
  }
  function gVix(dq) {
    var q = dq && dq.quotes && dq.quotes.VIX; if (!q || !num(q.price)) return { na: true, name: 'Volatility (VIX)', why: 'The volatility index did not arrive. Nothing was filled in.' };
    return { name: 'Expected volatility (Cboe VIX)', valueText: fmt(q.price, 2) + (num(q.changePct) ? ' (' + signed(q.changePct, 1, '%') + ')' : ''), pct: (q.price - 10) / 30 * 100, tone: q.price >= 25 ? 'down' : (q.price < 16 ? 'up' : 'mid'),
      lo: '10 \u00b7 calm', hi: 'stressed \u00b7 40', why: 'What options prices imply about S&P 500 swings over the next 30 days. Higher means traders are paying more for protection. The 10 to 40 bar is a display scale only.',
      meta: [cleanSrc(q.sourceLabel || q.source), q.asOfUk || ukTime(q.asOf), lagOf({ delayMin: q.delayMin, status: q.status })].join(' \u00b7 ') };
  }
  function gSessions(ss) {
    if (!ss || !num(ss.total) || !ss.total) return { na: true, name: 'Markets trading now', why: 'The session calendar did not arrive.' };
    return { name: 'Markets trading now', valueText: ss.tradingNow + ' of ' + ss.total, pct: ss.tradingNow / ss.total * 100, tone: 'neutral', lo: 'none open', hi: 'all ' + ss.total + ' open',
      why: 'How many of the 13 markets we track are in session. When most are shut, prices shown are last trades and can jump at the next open.',
      meta: 'Dispatch session calendar (ours, published exchange hours and holidays) \u00b7 ' + (ss.asOfUk || ukTime(ss.asOf)) + ' \u00b7 refreshed every minute' };
  }
  function gPositioning(t) {
    var p = t && t.positioning; if (!p || !num(p.net) || !num(p.openInterest) || !p.openInterest) return { na: true, name: 'Gold futures positioning (CFTC)', why: 'The weekly CFTC report did not arrive. Nothing was filled in.' };
    var sh = p.net / p.openInterest * 100;
    return { name: 'Gold futures positioning: net long share of open interest', valueText: signed(sh, 1, '%') + (num(p.weekChange) ? ' \u00b7 net ' + signed(p.weekChange, 0, '') + ' contracts on the week' : ''), pct: 50 + sh / 2, tone: 'neutral', marks: [50],
      lo: '\u2212100% net short', hi: 'net long +100%', why: 'Long minus short contracts in the CFTC disaggregated futures-only report, as a share of all open contracts. Weekly, so it lags prices. Our calculation from the CFTC figures.',
      meta: 'CFTC Commitments of Traders, COMEX gold \u00b7 report for ' + (ukDay(p.reportDate) || p.reportDate) + ' \u00b7 weekly' + (num(p.lagDays) ? ', ' + p.lagDays + ' days old' : '') + (p.status === 'stale' ? ' \u00b7 stored reading, not refreshed' : '') };
  }
  function gRange(sp) {
    if (!sp || !sp.all || sp.all.length < 50) return { na: true, name: 'Gold futures: place in its one-year range', why: 'Daily history did not arrive.' };
    var cs = sp.all.map(function (b) { return b.c; }), lo = Math.min.apply(null, cs), hi = Math.max.apply(null, cs), c = cs[cs.length - 1];
    return { name: 'Gold futures: latest daily close within its last ' + cs.length + ' sessions', valueText: '$' + fmt(c, 2) + ' \u00b7 ' + Math.round((c - lo) / (hi - lo) * 100) + '% of the way up', pct: (c - lo) / (hi - lo) * 100, tone: 'neutral',
      lo: 'low $' + fmt(lo, 0), hi: 'high $' + fmt(hi, 0), why: 'Shows whether the latest completed close sits near the bottom or top of the past year\u2019s closes. Our calculation from the daily bars; history only, not a signal.',
      meta: 'Yahoo Finance daily bars (continuous front month), delayed \u00b7 last completed session ' + ukDay(sp.to) + (sp.stale ? ' \u00b7 stored reading' : '') };
  }
  function gBtcRange(cs) {
    var it = fromCrypto(cs, 'BTC'); if (it.na || !it.range) return { na: true, name: 'Bitcoin within its 24-hour range', why: 'Coinbase stats did not arrive.' };
    var r = it.range, p = (r.v - r.lo) / (r.hi - r.lo) * 100;
    return { name: 'Bitcoin within its 24-hour range', valueText: Math.round(p) + '% of the way up', pct: p, tone: 'neutral', lo: 'low $' + fmt(r.lo, 0), hi: 'high $' + fmt(r.hi, 0),
      why: 'Crypto trades every day, so it is often the only market moving at weekends. This places the latest trade between the 24-hour low and high.', meta: 'Coinbase Exchange public stats \u00b7 ' + it.time + ' \u00b7 live, trades 24/7' };
  }

  // ---------- sections ----------
  function events(t, max) {
    var ev = t && t.events, now = Date.now();
    var items = ev && ev.items ? ev.items.filter(function (e) { return Date.parse(e.timeUtc) > now; }).slice(0, max) : [];
    var body = items.length ? '<ol class="cz-tl">' + items.map(function (e) {
      var d = new Date(e.timeUtc), days = Math.ceil((d - now) / 864e5), p = {};
      UKF.formatToParts(d).forEach(function (x) { p[x.type] = x.value; });
      return '<li><span class="cz-tld"><b>' + esc(p.day) + '</b>' + esc(p.month) + '</span><span class="cz-tlb"><strong>' + esc(e.name) + '</strong><span class="cz-src">' + esc(e.when || ukTime(e.timeUtc)) + ' \u00b7 in ' + days + (days === 1 ? ' day' : ' days') + ' \u00b7 ' + '<a href="' + esc(e.sourceUrl) + '" rel="noopener" target="_blank">' + esc(e.source) + '</a></span></span></li>';
    }).join('') + '</ol>' : '<p class="cz-nav">' + NA + ': the release schedule did not arrive. Nothing was filled in.</p>';
    return card('cz-events', 'Upcoming events', 'Scheduled data releases', 'Official release dates that often move gold, yields and the dollar. Times are UK. Release schedules from the agencies; consensus forecasts are not shown.', body +
      '<p class="cz-src cz-foot">Source: agency release calendars, via this site\u2019s terminal feed \u00b7 ' + esc(t && (t.generatedAtUk ? t.generatedAtUk + ' UK' : '') || 'time not given') + ' \u00b7 schedule, not live data. <a href="/calendar/">Full calendar</a></p>', 'cz-ev');
  }
  function bullets(list) { var l = list.filter(Boolean).slice(0, 5); while (l.length < 5) l.push(null); return '<ul class="cz-b5">' + l.map(function (b) { return b ? '<li>' + b + '</li>' : '<li class="cz-nav">' + NA + ': a reading for this line did not arrive.</li>'; }).join('') + '</ul>'; }
  function line(it, extra) { if (!it || it.na) return null; var c = it.chgText || signed(it.pct, 2, '%'); return '<b>' + esc(it.name) + '</b> ' + esc(it.value) + (c ? ' (' + esc(c) + (it.chgText ? '' : ' ' + (it.basis || '')) + ')' : '') + (extra ? ' ' + esc(extra) : '') + ' <span class="cz-src">' + esc(it.src + ' \u00b7 ' + it.time) + '</span>'; }

  function snapshot(D, cfg) {
    var rg = D.rg, ss = D.mrq && D.mrq.sessionSummary;
    var head = cfg.headline(D);
    var body = '<p class="cz-hl">' + esc(head) + '</p>' +
      '<div class="cz-gg">' + cfg.gauges.map(function (g) { return gauge(g); }).join('') + '</div>' +
      '<div class="cz-p3row">' + cfg.three.map(bigPrice).join('') + '</div>' +
      '<div class="cz-sum"><h3 class="cz-h3">In five lines</h3>' + bullets(cfg.lines) + '</div>' +
      '<p class="cz-src cz-foot">Facts from free public feeds as this site already shows them; each line carries its own source and UK time. ' + (ss && ss.text ? esc(ss.text) + '. ' : '') + 'Not investment advice.</p>';
    return card('cz-snap', 'Market snapshot', cfg.title, cfg.why, body, 'cz-hero');
  }
  function priceRow(items, title, why) {
    return card('cz-keys', 'Key prices', title, why, '<ul class="cz-chips">' + items.map(chip).join('') + '</ul><p class="cz-src cz-foot">Green is up and red is down against the stated basis (previous close, or 24 hours for crypto). Sparklines appear only where this site has a daily history (gold futures); crypto shows its 24-hour range instead. No history is drawn for the rest.</p>', 'cz-kp');
  }
  function sessionTiles(ss) {
    if (!ss || !ss.markets) return card('cz-sess', 'Sessions', 'Which markets are open', '', '<p class="cz-nav">' + NA + '</p>');
    return card('cz-sess', 'Sessions', 'Which markets are open now', 'A closed market shows its last trade; prices can gap at the next open. From our session calendar of published exchange hours and holidays.',
      '<ul class="cz-tiles">' + ss.markets.map(function (m) { return '<li class="cz-tile cz-' + (m.open ? 'open' : 'shut') + '"><span class="cz-dot"></span><b>' + esc(m.label) + '</b><span>' + (m.open ? 'Open now' : 'Closed') + (m.open ? (m.calendar === '24/7' ? ' \u00b7 trades 24/7' : '') : (m.nextOpenUk ? ' \u00b7 opens ' + esc(m.nextOpenUk) : '')) + '</span></li>'; }).join('') + '</ul>' +
      '<p class="cz-src cz-foot">Dispatch session calendar (ours) \u00b7 ' + esc(ss.asOfUk || '') + ' \u00b7 refreshed every minute. Frankfurt and Paris use hours only (no holiday calendar).</p>');
  }
  function goldChart(sp) {
    if (!sp) return card('cz-gchart', 'Trend', 'Gold futures, recent daily closes', '', '<p class="cz-nav">' + NA + ': daily history did not arrive. Nothing was drawn.</p>');
    var p = sp.pts, a = p[0], b = p[p.length - 1], ch = (b - a) / a * 100;
    return card('cz-gchart', 'Trend', 'Gold futures: last ' + p.length + ' daily closes', 'Shows the path behind today\u2019s price. Daily closes are the secondary line: the main gold number is the live spot quote above.',
      '<div class="cz-bigspark">' + spark(sp, 600, 120, 'cz-spbig') + '</div><div class="cz-gs"><span>' + esc(ukDay(sp.from)) + ': $' + esc(fmt(a, 2)) + '</span><span>' + esc(ukDay(sp.to)) + ': $' + esc(fmt(b, 2)) + ' <em class="cz-chg cz-' + dir(ch) + '">' + esc(signed(ch, 1, '%')) + '</em></span></div>' +
      '<p class="cz-src cz-foot">' + esc(sp.label) + ' \u00b7 daily bars, last completed session ' + esc(ukDay(sp.to)) + ' (the current session is left out until it completes)' + (sp.stale ? ' \u00b7 stored reading, not refreshed' : '') + '.</p>');
  }

  function build(D) {
    var dq = D.dq, mrq = D.mrq, cs = D.cs, t = D.term, sp = goldSpark(D.chart, 30), sp60 = goldSpark(D.chart, 60);
    var gold = goldSpot(mrq), spx = fromDesk(dq, 'SPX'), dxy = fromDesk(dq, 'DXY'), ten = tenYear(dq, D.dgs), ry = realYield(D.rates, D.ry), oil = wti(dq, D.eia),
      silver = fromDesk(dq, 'SLV'), btc = fromCrypto(cs, 'BTC'), gbp = fromDesk(dq, 'GBPUSD'), vix = fromDesk(dq, 'VIX'), ndq = fromDesk(dq, 'IXIC');
    var gfut = (function () { var f = mrq && mrq.XAU && (mrq.XAU.futuresChange || mrq.XAU.futures); if (!f || !num(f.price)) return naItem('Gold futures (COMEX, front month)');
      return { name: 'Gold futures (COMEX, front month)', value: '$' + fmt(f.price, 2), pct: f.changePct, basis: 'vs previous close', src: cleanSrc(f.source), time: f.asOfUk || ukTime(f.asOf), delayMin: f.delayMin || 10, status: mrq.sessionSummary && mrq.sessionSummary.byClass && mrq.sessionSummary.byClass.commodities && mrq.sessionSummary.byClass.commodities.open === 0 ? 'closed' : null, spark: sp }; })();
    var rg = D.rg, ss = mrq && mrq.sessionSummary, regimeHead = rg && rg.available ? (rg.label || rg.regime) + ': risk appetite gauge ' + rg.score + ' of 100' : 'Risk appetite gauge not available';
    var sessHead = ss && num(ss.total) ? ss.tradingNow + ' of ' + ss.total + ' markets trading now' : '';
    var lineRisk = rg && rg.available ? '<b>Risk appetite gauge (ours)</b> ' + esc(rg.score + ' of 100, ' + (rg.label || '')) + ' <span class="cz-src">' + esc('Dispatch regime model \u00b7 ' + (rg.computedAtUk || '')) + '</span>' : null;
    var html = '';
    if (PAGE === 'brief') {
      html += snapshot(D, { title: 'Where markets stand', why: 'The brief\u2019s key readings in one card: our risk gauge, volatility, how many markets are open, and the three prices the brief leads on.',
        headline: function () { return regimeHead + (sessHead ? ' \u00b7 ' + sessHead : ''); }, gauges: [gRisk(rg), gVix(dq), gSessions(ss)], three: [gold, spx, dxy],
        lines: [line(gold, gold.futPct != null ? '; futures ' + signed(gold.futPct, 2, '%') : ''), line(spx), line(ten), line(oil), line(btc)] });
      html += priceRow([gfut, silver, oil, ndq, vix, ten, gbp, btc], 'More of today\u2019s figures', 'A compact read of the other prices the brief draws on. Each shows its own source, UK time and delay.');
      html += events(t, 5);
    } else if (PAGE === 'gold') {
      html += snapshot(D, { title: 'Gold at a glance', why: 'The live spot price first, then the readings usually set beside gold: positioning, the one-year range, real yields and the dollar.',
        headline: function () { return (gold.na ? 'Gold spot not available' : 'Gold spot ' + gold.value + ' an ounce') + (gold.futPct != null ? ' \u00b7 gold futures (COMEX, front month) ' + signed(gold.futPct, 2, '%') + ' vs previous close' : ''); },
        gauges: [gRisk(rg), gPositioning(t), gRange(D.chart && D.chart.bars ? goldSpark(D.chart, 250) : null)], three: [gold, silver, ry],
        lines: [line(gold), line(gfut), line(ry), line(dxy), line(ten)] });
      html += goldChart(sp60);
      html += priceRow([gfut, silver, dxy, ten, gbp, oil], 'Prices that move with gold', 'Gold is priced in dollars and pays no interest, so the dollar and yields are the usual companions. Silver moves with it more often than not.');
      html += events(t, 4);
    } else if (PAGE === 'markets') {
      html += snapshot(D, { title: 'Markets right now', why: 'Who is open, how calm or stressed markets are, and the three headline prices, before the full tables below.',
        headline: function () { return (sessHead || 'Session calendar not available') + ' \u00b7 ' + regimeHead; }, gauges: [gSessions(ss), gVix(dq), gRisk(rg), gBtcRange(cs)], three: [spx, ten, dxy],
        lines: [line(spx), line(ndq), line(vix), line(oil), line(btc)] });
      html += priceRow([fromDesk(dq, 'DJIA'), ndq, vix, gfut, silver, oil, fromDesk(dq, 'NG'), fromDesk(dq, 'EURUSD'), gbp, fromDesk(dq, 'USDJPY'), ry, btc, fromCrypto(cs, 'ETH'), fromCrypto(cs, 'SOL')], 'Across asset classes', 'Stocks, commodities, currencies, rates and crypto in one row of tiles. The full tables follow below.');
      html += sessionTiles(ss);
      html += events(t, 4);
    } else {
      html += snapshot(D, { title: 'Market context for the research', why: 'The readings our notes refer to most, so you can see today\u2019s levels before reading a note. Notes below carry their own checked times.',
        headline: function () { return regimeHead + (sessHead ? ' \u00b7 ' + sessHead : ''); }, gauges: [gRisk(rg), gVix(dq)], three: [gold, spx, ten],
        lines: [line(gold), line(ry), line(dxy), line(spx), lineRisk] });
      html += events(t, 4);
    }
    html += '<p class="cz-disc">Every figure above comes from this site\u2019s own free feeds and shows its source, UK time and delay. Where a feed is missing the card says Not available. Nothing here is a forecast or a recommendation.</p>';
    root.innerHTML = html; root.setAttribute('data-cz-ready', '1');
  }
  Promise.all([
    get('/api/market-reference-quotes'), get('/api/desk-quotes?symbols=SLV,WTI,NG,DXY,EURUSD,GBPUSD,USDJPY,TNX,SPX,DJIA,IXIC,VIX'), get('/api/crypto-snapshot?coins=BTC,ETH,SOL&limit=3'),
    get('/api/regime'), get('/api/c102/terminal'), get('/api/c102/chart'), get('/api/c101f/rates'), get('/api/real-yield'), get('/api/c97/dgs10'), get('/api/eia-spot')
  ]).then(function (a) {
    try { build({ mrq: a[0], dq: a[1], cs: a[2], rg: a[3], term: a[4], chart: a[5], rates: a[6], ry: a[7], dgs: a[8], eia: a[9] }); }
    catch (e) { root.innerHTML = '<p class="cz-nav">The market snapshot could not be drawn. No number was filled in.</p>'; if (window.console) console.warn('chat114viz', e); }
  });
})();
