// ── rt62 ──
// FE79_PURE_START
function fe79_round2(n) {
  var v = Number(n);
  if (!isFinite(v)) return null;
  return +v.toFixed(2);
}
function fe79_cryptoPct(px, base, srv) {
  var n = Number(px), b = Number(base);
  if (b > 0 && n > 0) {
    var pct = ((n - b) / b) * 100;
    if (!isFinite(pct) || Number(pct.toFixed(2)) === 0) return null;
    return +pct.toFixed(2);
  }
  if (srv != null && srv !== "" && isFinite(Number(srv)) && Number(Number(srv).toFixed(2)) !== 0) return +Number(srv).toFixed(2);
  return null;
}
function fe79_surfaces(px, base, srv) {
  var n = fe79_cryptoPct(px, base, srv);
  var t = n == null ? null : n.toFixed(2);
  return { home: t, crypto: t, tape: t, market: t, phone: t, list: t, lens: t, signal: t, ask: t };
}
function fe79_isCryptoTk(tk) {
  if (typeof fe79_isCryptoTk.fn === "function") return !!fe79_isCryptoTk.fn(tk);
  return /^(BTC|ETH|SOL|XRP|DOGE|ADA|AVAX|LINK|DOT|LTC|BCH|UNI)$/.test(String(tk || "").toUpperCase());
}
function fe79_pctHtml(tk, ch, label) {
  if (ch == null || !isFinite(Number(ch))) return "—";
  var n = Number(ch);
  if (Number(n.toFixed(2)) === 0) return "—";
  var body = (n > 0 ? "+" : "") + n.toFixed(2) + "%";
  if (fe79_isCryptoTk(tk)) {
    var lab = label;
    if (!lab && typeof fe79_labelFor === "function") {
      try { lab = fe79_labelFor(tk); } catch (eLab) { lab = ""; }
    }
    if (!lab) lab = "24h";
    body += " " + lab;
  }
  return body;
}
function fe79_goldPct(spot, quoteC, hasPrev) {
  if (spot != null && isFinite(Number(spot))) {
    var s = +Number(spot).toFixed(2);
    if (s === 0 && !hasPrev) return null;
    return s;
  }
  if (quoteC != null && isFinite(Number(quoteC))) {
    var q = +Number(quoteC).toFixed(2);
    if (q === 0 && !hasPrev) return null;
    return q;
  }
  return null;
}
function fe79_moveText(mv, hasData) {
  if (mv == null || !isFinite(Number(mv))) return "";
  if (Number(Number(mv).toFixed(2)) === 0) return hasData ? "unchanged" : "";
  var n = Number(mv);
  return (n > 0 ? "+" : "−") + Math.abs(n).toFixed(2) + "%";
}
function fe79_onePct(s) {
  var t = String(s == null ? "" : s).trim();
  if (!t || t === "—" || t === "-") return t === "-" ? "—" : t;
  var bare = t.replace(/%/g, "").replace(/,/g, "").trim();
  if (!bare || !isFinite(Number(bare))) return t.replace(/%%+/g, "%");
  return Number(bare).toFixed(2) + "%";
}
function fe79_count(rows) {
  var live = 0, closed = 0, quiet = 0, priced = 0;
  (rows || []).forEach(function (r) {
    if (!r || !r.quote) return;
    priced++;
    if (r.crypto) { live++; return; }
    if (r.open && r.fresh) live++;
    else if (r.open) quiet++;
    else closed++;
  });
  return { live: live, closed: closed, quiet: quiet, priced: priced };
}
function fe79_tradeLabel(box) {
  box = box || { live: 0, closed: 0, quiet: 0, priced: 0 };
  if (!box.priced) return "Prices loading";
  return box.live + " trading now · " + box.closed + " closed" + (box.quiet ? " · " + box.quiet + " quiet" : "");
}
function fe79_setRegime(cur, raw) {
  raw = raw || {};
  var score = raw.score != null && raw.score !== "" ? Number(raw.score) : null;
  var label = String(raw.label || raw.regime || "").trim();
  var asOf = raw.asOfUk || raw.asOf || "";
  return {
    label: label,
    score: isFinite(score) ? score : null,
    asOf: raw.asOf || asOf,
    asOfUk: asOf,
    localEstimate: raw.localEstimate === true,
    loading: false
  };
}
function fe79_goldChip(q) {
  q = q || {};
  var sym = String(q.symbol || q.ticker || q.tk || "").toUpperCase();
  var src = String(q.source || q.src || q.feedLabel || "").toLowerCase();
  var blob = sym + " " + src;
  var fut = blob.indexOf("GC=F") >= 0 || src.indexOf("future") >= 0;
  var spot = !fut && (sym === "XAU" || src.indexOf("spot") >= 0 || src.indexOf("gold-api") >= 0);
  if (fut) return "Gold futures (GC=F, delayed 10 min)";
  if (spot) return "Gold spot";
  if (/gold|xau/.test(blob) || /gold/i.test(String(q.name || q.label || ""))) return "Gold";
  return "";
}
function fe79_fromDate(iso) {
  var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || "").trim());
  if (!m) return "";
  var dt = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], 12, 0, 0));
  try {
    var wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(dt);
    var day = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric" }).format(dt);
    var mon = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", month: "short" }).format(dt);
    if (!wd || !day || !mon) return "";
    return "From " + wd + " " + day + " " + mon;
  } catch (e) { return ""; }
}
function fe79_academyNote(j, today) {
  if (!j || typeof j !== "object") return null;
  var edition = j.edition != null ? String(j.edition).trim().toLowerCase() : "";
  var label = j.label != null ? String(j.label).trim() : "";
  label = label.replace(/\.+$/, "").trim();
  var dateLabel = j.dateLabel != null ? String(j.dateLabel).trim() : "";
  if (edition === "yesterday") label = "Yesterday";
  else if (edition === "older") label = "An earlier set";
  else if (!label && (edition === "today" || edition === "")) {
    if (edition === "today") label = "Today's set";
  }
  var nextRaw = j.nextRunUk != null ? String(j.nextRunUk).trim() : "";
  var nextLine = "";
  if (nextRaw) {
    var hm = (nextRaw.match(/\d{1,2}:\d{2}/) || [""])[0];
    if (/^\d:\d{2}$/.test(hm)) hm = "0" + hm;
    if (hm) nextLine = "Next set due " + hm + " UK";
  }
  var parts = [];
  if (label) parts.push(label);
  if (dateLabel && parts.join(" ").indexOf(dateLabel) < 0) {
    if (parts.length) parts[parts.length - 1] = parts[parts.length - 1] + " (" + dateLabel + ")";
    else parts.push(dateLabel);
  }
  if (nextLine) parts.push(nextLine);
  if (parts.length) {
    var text = parts.join(" · ").replace(/\.\s*·/g, " ·").replace(/\s{2,}/g, " ").trim();
    return { text: text, amber: j.stale === true };
  }
  var date = j.date != null ? String(j.date).trim() : "";
  if (!date || (today && date === String(today))) return null;
  var pretty = fe79_fromDate(date);
  return { text: pretty || ("From " + date), amber: false };
}
function fe79_stripUkDay(s) {
  return String(s == null ? "" : s)
    .replace(/(\d{1,2}:\d{2}\s*UK)\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/gi, "$1")
    .replace(/\s+UK\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/gi, " UK")
    .replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*$/i, function (m, d, off, str) {
      if (/market closed|opens\b|\d{1,2}:\d{2}\s*UK/i.test(str)) return "";
      return m;
    });
}
function fe79_deskPhrase(s) {
  return String(s == null ? "" : s).replace(/\bScore\s+(\d{1,3})(?:\s*\/\s*100)?/g, function (m, n, off, str) {
    var before = str.slice(Math.max(0, off - 80), off);
    if (/regime|lab-regime|desk-letter-tag|risk score|composite/i.test(before)) return m;
    if (/Desk score\s*$/i.test(before)) return m;
    return "Desk score " + n + "/100";
  });
}
function fe79_catLabel(cat) {
  var k = String(cat == null ? "" : cat).trim().toLowerCase();
  if (k === "index" || k === "idx" || k === "indices") return "Index";
  if (k === "yield" || k === "yld" || k === "rates") return "Yield";
  if (k === "fx" || k === "forex" || k === "currency") return "Forex";
  if (k === "stock" || k === "stocks") return "Stocks";
  if (k === "crypto" || k === "cryptocurrency") return "Crypto";
  if (k === "commodity" || k === "commodities") return "Commodities";
  return "";
}
function fe79_dxyPx(s) {
  return String(s == null ? "" : s).replace(/^\$/, "");
}
function fe79_titleCaseIndex(s) {
  return String(s == null ? "" : s).replace(/US dollar index/g, "US Dollar Index");
}
function fe79_missing(v) {
  if (v == null) return "Not available for this instrument";
  var s = String(v).trim();
  if (!s || s === "null" || s === "undefined" || s === "NaN" || /^no price( yet)?$/i.test(s)) return "Not available for this instrument";
  return s;
}
function fe79_metricOk(label, value) {
  var l = String(label || "");
  if (value == null) return false;
  var s = String(value).trim();
  if (!s || s === "-" || s === "—" || s === "–" || s === "null" || s === "undefined" || s === "NaN") return false;
  if (/beta/i.test(l) && !isFinite(parseFloat(String(value).replace(/x/i, "")))) return false;
  return true;
}
function fe79_numOrNull(v) {
  if (v == null || v === "") return null;
  var n = Number(v);
  return isFinite(n) ? n : null;
}
function fe79_cryptoView(row) {
  row = row || {};
  var basis = row.changeBasis != null ? String(row.changeBasis).trim() : "";
  var label = row.changeBasisLabel != null ? String(row.changeBasisLabel).trim() : "";
  var px = fe79_numOrNull(row.px != null ? row.px : (row.p != null ? row.p : row.price));
  var base = fe79_numOrNull(row.baselinePrice);
  var srv = fe79_numOrNull(row.c != null ? row.c : row.changePct);
  var hasServer = !!(basis || label || base != null || srv != null || row.changeSource);
  var pct = null;
  if (base > 0 && px > 0) pct = fe79_cryptoPct(px, base, null);
  else if (srv != null) pct = fe79_cryptoPct(null, null, srv);
  if (!label) {
    if (/previous close/i.test(basis)) label = "previous close";
    else if (/rolling\s*24h|^24h$/i.test(basis)) label = "24h";
    else if (!hasServer) label = "24h";
    else label = basis;
  }
  if (/previous close/i.test(basis)) label = row.changeBasisLabel ? String(row.changeBasisLabel).trim() : "previous close";
  var text = pct == null ? "—" : ((pct > 0 ? "+" : "") + pct.toFixed(2) + "%" + (label ? " " + label : ""));
  return { pct: pct, label: label, text: text, basis: basis, source: hasServer ? "server" : "fallback" };
}
function fe79_goldView(row) {
  row = row || {};
  if (row.displayChange === null) {
    var note0 = row.changeNote != null ? String(row.changeNote).trim() : "";
    return { pct: null, text: note0 || "—", label: "Gold", instrument: "", note: note0, source: "server", unchanged: false };
  }
  var dc = row.displayChange;
  if (!dc && row.futuresChange && typeof row.futuresChange === "object") {
    dc = {};
    for (var k in row.futuresChange) dc[k] = row.futuresChange[k];
    if (!dc.instrument) dc.instrument = "futures";
    if (!dc.label) dc.label = "Gold futures (GC=F)";
  }
  if (dc && typeof dc === "object") {
    var pct = fe79_numOrNull(dc.pct);
    if (pct != null) pct = +pct.toFixed(2);
    var inst = String(dc.instrument || "");
    var label = dc.label != null ? String(dc.label).trim() : "";
    if (inst === "futures") label = label && /futures/i.test(label) ? label : "Gold futures (GC=F)";
    else if (!label) label = inst === "spot" ? "Gold spot" : "Gold";
    var text = dc.text != null ? String(dc.text).trim() : "";
    if (!text) {
      if (pct == null) text = dc.note ? String(dc.note) : (row.changeNote ? String(row.changeNote) : "—");
      else if (pct === 0) text = "unchanged";
      else text = (pct > 0 ? "+" : "−") + Math.abs(pct).toFixed(2) + "%";
    }
    if (pct == null && /0\.00\s*%/.test(text)) text = dc.note ? String(dc.note) : "—";
    if (pct == null && /unchanged/i.test(text)) text = dc.note ? String(dc.note) : "—";
    return { pct: pct, text: text, label: label, instrument: inst, symbol: dc.symbol || "", note: dc.note || row.changeNote || "", source: "server", unchanged: pct === 0 };
  }
  var spot = fe79_goldPct(row.spot, row.quoteC, !!row.hasPrev);
  if (spot == null) return { pct: null, text: "—", label: "Gold spot", instrument: "spot", source: "fallback", unchanged: false };
  if (spot === 0) return { pct: 0, text: "unchanged", label: "Gold spot", instrument: "spot", source: "fallback", unchanged: true };
  return { pct: spot, text: (spot > 0 ? "+" : "−") + Math.abs(spot).toFixed(2) + "%", label: "Gold spot", instrument: "spot", source: "fallback", unchanged: false };
}
function fe79_yieldView(row) {
  row = row || {};
  var has = row.value != null || row.unit != null || row.changePp != null || row.changeBp != null;
  if (!has) {
    var fb = row.fallback != null ? fe79_onePct(row.fallback) : "";
    return { text: fb, change: "", source: fb ? "fallback" : "hidden" };
  }
  var v = fe79_numOrNull(row.value);
  var unit = String(row.unit || "");
  var text = v == null ? "—" : v.toFixed(2);
  if (unit === "percent" && v != null) text = fe79_onePct(text);
  text = String(text).replace(/%%+/g, "%");
  var ch = "";
  var pp = fe79_numOrNull(row.changePp);
  var bp = fe79_numOrNull(row.changeBp);
  if (pp != null) ch = (pp > 0 ? "+" : "") + pp.toFixed(2) + " pp";
  else if (bp != null) ch = (bp > 0 ? "+" : "") + Math.round(bp) + " bp";
  return { text: text, change: ch, source: "server", asOf: row.asOf || "", unit: unit };
}
function fe79_regimeView(raw) {
  if (raw == null || raw.available === false) return { useLocal: true, source: "fallback", text: "" };
  var label = String(raw.label || raw.regime || "").trim();
  var score = fe79_numOrNull(raw.score);
  if (!label && score == null) return { useLocal: true, source: "fallback", text: "" };
  var asOf = raw.computedAtUk || raw.asOfUk || "";
  var flags = [];
  if (raw.thin) flags.push("thin");
  if (raw.stale) flags.push("stale");
  var text = (label || "Regime") + (score != null ? " " + score : "") + (asOf ? " " + asOf : "") + (flags.length ? " · " + flags.join(", ") : "");
  return { useLocal: false, label: label, score: score, asOfUk: asOf, asOf: raw.computedAt || asOf, thin: !!raw.thin, stale: !!raw.stale, source: "server", text: text.trim(), inputs: raw.inputs || null };
}
function fe79_mcapView(row) {
  row = row || {};
  var t = row.marketCapText != null ? String(row.marketCapText).trim() : "";
  if (!t || t === "-" || t === "—" || t === "–" || t === "null" || t === "undefined" || t === "NaN") return { text: "", source: "hidden" };
  return { text: t, source: "server" };
}
function fe79_sessionView(raw, fallbackBox) {
  if (raw && (raw.text || raw.tradingNow != null)) {
    var text = raw.text != null ? String(raw.text).trim() : "";
    if (!text && raw.tradingNow != null) {
      var live = Number(raw.tradingNow);
      var total = fe79_numOrNull(raw.total);
      var closed = fe79_numOrNull(raw.closed);
      text = total != null ? (live + " of " + total + " markets trading now") : (live + " trading now");
      if (closed != null) text += " · " + closed + " closed";
    }
    return { text: text, tradingNow: raw.tradingNow, closed: raw.closed, quiet: raw.quiet, total: raw.total, source: "server" };
  }
  return { text: fe79_tradeLabel(fallbackBox), source: "fallback" };
}
function fe79_askChip(meta) {
  var q = (meta && meta.quote) || meta || {};
  if (q.label) {
    var price = q.price != null ? String(q.price) : "";
    var time = String(q.time || q.asOfUk || q.asOf || "");
    var parts = [String(q.label)];
    if (price) parts.push(price);
    if (time) parts.push(time);
    return { label: String(q.label), price: price, time: time, source: "server", line: parts.join(" · ") };
  }
  var fb = fe79_goldChip(q);
  return { label: fb, price: q.price != null ? String(q.price) : "", time: String(q.asOfUk || q.time || ""), source: fb ? "fallback" : "hidden", line: fb };
}
function fe79_deskRow(row, missing) {
  row = row || {};
  var tk = String(row.ticker || row.tk || "").toUpperCase();
  var list = missing || [];
  for (var i = 0; i < list.length; i++) {
    var m = list[i];
    if (m && String(m.ticker || "").toUpperCase() === tk) {
      return { hide: false, text: m.reason ? String(m.reason) : "Not available for this instrument", source: "server", showBeta: false, beta: null };
    }
  }
  if (!tk && row.price == null) return { hide: true, text: "", source: "hidden", showBeta: false };
  var hasBeta = Object.prototype.hasOwnProperty.call(row, "beta");
  var beta = hasBeta ? fe79_numOrNull(row.beta) : null;
  return {
    hide: false,
    text: row.price == null && row.value == null ? "Not available for this instrument" : String(row.price != null ? row.price : row.value),
    showBeta: hasBeta && beta != null,
    beta: beta,
    source: "server"
  };
}
function fe79_finView(fin) {
  fin = fin || {};
  var v = fin.valuation || {};
  var hidden = {};
  var list = v.hidden || [];
  for (var i = 0; i < list.length; i++) if (list[i] && list[i].field) hidden[String(list[i].field)] = list[i].reason || "";
  var notes = fin.epsNotes || (fin.fin && fin.fin.epsNotes) || [];
  if (!Array.isArray(notes)) notes = notes ? [String(notes)] : [];
  var sourced = !!(v.dividend || (v.hidden && v.hidden.length) || fin.epsTtm != null || fin.peBasis || notes.length);
  return {
    source: sourced ? "server" : "fallback",
    hidden: hidden,
    dividend: v.dividend || null,
    peBasis: fin.peBasis || v.peBasis || "",
    epsTtm: fin.epsTtm != null ? fin.epsTtm : null,
    epsBasis: fin.epsBasis || "",
    notes: notes
  };
}
function fe79_aboutText(asset) {
  asset = asset || {};
  var about = asset.about != null ? String(asset.about).trim() : "";
  if (about && about !== "null" && about !== "undefined") return { text: about, source: "server" };
  var th = asset.th != null ? String(asset.th).trim() : "";
  if (!th || th === "undefined" || th === "None" || th === "null") return { text: "", source: "hidden" };
  if (/listed on|desk instrument table|placeholder description/i.test(th)) return { text: "", source: "hidden" };
  return { text: th, source: "fallback" };
}
function fe79_natgas() {
  return { id: "natgas", label: "Natural gas", phrase: "natural gas prices", icon: "flame", color: "#2f9e8f" };
}
function fe79_domCard(pageTk, signal) {
  if (!signal) return null;
  var btcCard = signal.tk === "BTC" && String(signal.a || "") === "Bitcoin" && /crypto/i.test(String(signal.tg || ""));
  if (!btcCard) return signal;
  if (pageTk !== "BTC") return null;
  var asOf = signal.asOf ? String(signal.asOf) : "";
  return {
    a: "BTC dominance",
    tk: "BTC",
    cf: signal.cf,
    tg: "Crypto",
    x: "Bitcoin's share of crypto market cap" + (signal.dom != null ? " · " + signal.dom + "%" : "") + (asOf ? " · as of " + asOf : "") + " · CoinGecko"
  };
}
// FE79_PURE_END

function fe79_cryptoBase(tk) {
  var base = null, srv = null;
  try {
    var b = typeof fe78_bag === "function" ? fe78_bag(tk) : null;
    if (b && b.baseline === "24h" && Number(b.base) > 0) base = Number(b.base);
    if (b && b.srvC != null && isFinite(Number(b.srvC))) srv = Number(b.srvC);
  } catch (e) {}
  try {
    var r = (typeof _rt !== "undefined" && _rt && _rt.roll) ? _rt.roll[tk] : null;
    if (r && r.kind === "srv24") {
      if (!(base > 0) && Number(r.prev) > 0) base = Number(r.prev);
      if (srv == null && r.c != null && isFinite(Number(r.c))) srv = Number(r.c);
    }
  } catch (e2) {}
  return { base: base, srv: srv };
}
var fe79_srv = Object.create(null);
var fe79_sessionSrv = null;
var fe79_fin = Object.create(null);
var fe79_missing = [];
function fe79_labelFor(tk) {
  var s = fe79_srv[tk];
  if (s && s.changeBasisLabel) return String(s.changeBasisLabel);
  if (s && /previous close/i.test(String(s.changeBasis || ""))) return "previous close";
  return "24h";
}
function fe79_ingest(tk, q) {
  if (!tk || !q || typeof q !== "object") return;
  var prev = fe79_srv[tk] || {};
  var merged = {};
  var k;
  for (k in prev) merged[k] = prev[k];
  for (k in q) {
    if (/^coingecko_/i.test(k) || k === "price_change_percentage_24h" || k === "price_change_percentage_24h_in_currency") continue;
    merged[k] = q[k];
  }
  var px = q.p != null ? q.p : (q.price != null ? q.price : q.value);
  var view = fe79_cryptoView({
    px: px, p: px, price: px,
    baselinePrice: merged.baselinePrice,
    c: merged.c != null ? merged.c : merged.changePct,
    changePct: merged.changePct,
    changeBasis: merged.changeBasis,
    changeBasisLabel: merged.changeBasisLabel,
    changeSource: merged.changeSource
  });
  merged.view = view;
  if (q.displayChange !== undefined || q.futuresChange || q.changeNote) merged.gold = fe79_goldView(q);
  if (q.unit === "percent" || q.value != null || tk === "TNX" || tk === "US10Y") merged.yield = fe79_yieldView(q);
  if (q.marketCapText) merged.marketCapText = q.marketCapText;
  fe79_srv[tk] = merged;
  if (tk === "US10Y") fe79_srv.TNX = merged;
}
function fe79_liveCryptoPct(tk, px) {
  if (!fe79_isCryptoTk(tk)) return undefined;
  var n = px;
  if (!(Number(n) > 0)) {
    try { n = (typeof P !== "undefined" && P[tk]) ? P[tk].p : null; } catch (e) { n = null; }
  }
  var stored = fe79_srv[tk] || {};
  if (stored.baselinePrice != null || stored.changeBasis || stored.changeBasisLabel || stored.changePct != null || stored.c != null || stored.changeSource) {
    var view = fe79_cryptoView({
      px: n, p: n,
      baselinePrice: stored.baselinePrice,
      c: stored.c != null ? stored.c : stored.changePct,
      changePct: stored.changePct,
      changeBasis: stored.changeBasis,
      changeBasisLabel: stored.changeBasisLabel,
      changeSource: stored.changeSource
    });
    if (view.source === "server") return view.pct;
  }
  var bag = fe79_cryptoBase(tk);
  return fe79_cryptoPct(n, bag.base, bag.srv);
}
function fe79_goldNow() {
  var bag = fe79_srv.XAU || fe79_srv["GC=F"];
  if (bag && bag.gold && bag.gold.source === "server") return bag.gold;
  return null;
}
function fe79_liveGold() {
  var g = fe79_goldNow();
  if (g) return g.pct;
  var spot = null, quoteC = null, has = false;
  try { spot = typeof fe76_spotPct === "function" ? fe76_spotPct() : null; } catch (e) { spot = null; }
  try {
    var q = typeof fe76_quote === "function" ? fe76_quote("XAU") : null;
    if (q) {
      quoteC = q.c;
      has = !!(q.prev > 0);
    }
  } catch (e2) {}
  try {
    if (!has && typeof fe76_ownPrev === "function" && typeof fe76_spotPrev !== "undefined") {
      var p = (typeof P !== "undefined" && P.XAU) ? P.XAU.p : 0;
      has = !!fe76_ownPrev(p, fe76_spotPrev);
    }
  } catch (e3) {}
  if (spot == null && quoteC != null) return fe79_goldPct(null, quoteC, has);
  return fe79_goldPct(spot, quoteC, has);
}
function fe79_session() {
  var now = Date.now();
  if (fe79_session.box && now - fe79_session.box.at < 1000) return fe79_session.box;
  var uni = [];
  try { uni = typeof fe70_universe === "function" ? fe70_universe() : (typeof A !== "undefined" ? A : []); } catch (e) { uni = []; }
  if (!uni || !uni.length) { try { uni = typeof A !== "undefined" ? A : []; } catch (e2) { uni = []; } }
  var rows = [];
  for (var i = 0; i < uni.length; i++) {
    var a = uni[i];
    var tk = a && a.tk;
    if (!tk) continue;
    var quote = false, crypto = false, open = false, fresh = false;
    try { quote = typeof hasSyncedQuote === "function" && !!hasSyncedQuote(tk); } catch (e3) {}
    try { crypto = !!fe79_isCryptoTk(tk) || (typeof _isContinuousTapeTicker === "function" && !!_isContinuousTapeTicker(tk)); } catch (e4) {}
    try { open = typeof _rt18MarketOpen === "function" && !!_rt18MarketOpen(tk); } catch (e5) {}
    try { fresh = typeof _rt39Live === "function" && !!_rt39Live(tk); } catch (e6) {}
    if (crypto && quote) { open = true; fresh = true; }
    rows.push({ quote: quote, crypto: crypto && quote, open: open, fresh: fresh });
  }
  var box = fe79_count(rows);
  box.at = now;
  box.total = uni.length;
  fe79_session.box = box;
  return box;
}
function fe79_tradeNow() {
  if (fe79_sessionSrv) return fe79_sessionView(fe79_sessionSrv, null).text;
  return fe79_tradeLabel(fe79_session());
}
function fe79_showBeta(tk) {
  var s = fe79_srv[tk];
  if (s && s.betaSourced === true && fe79_numOrNull(s.beta) != null) return true;
  return false;
}
function fe79_capFor(a) {
  a = a || {};
  var s = fe79_srv[a.tk] || {};
  var fin = fe79_fin[a.tk] || {};
  var v = fin.valuation || {};
  return fe79_mcapView({ marketCapText: s.marketCapText || a.marketCapText || v.marketCapText || fin.marketCapText || "" }).text;
}
var fe79_regimeBox = null;
var fe79_regimeHold = false;
function fe79_writeRegime(raw) {
  fe79_regimeBox = fe79_setRegime(fe79_regimeBox, raw || {});
  fe79_regimeHold = true;
  try { fe79_paintRegime(); } catch (e) {}
  return fe79_regimeBox;
}
function fe79_paintRegime() {
  if (typeof document === "undefined" || !fe79_regimeBox) return;
  var re = fe79_regimeBox;
  var text = (re.label || "Regime") + (re.score != null ? " · " + re.score + "/100" : "");
  if (re.thin) text += " · thin";
  if (re.stale) text += " · stale";
  if (re.localEstimate) text += " · Dispatch local estimate";
  var asOf = re.asOfUk ? (" · " + re.asOfUk) : "";
  var nodes = document.querySelectorAll(".htec-chip-regime, .home-regime, .ns-regime .ns-val, .lab-regime-lbl, .lab-regime-score, .gc-regime");
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    if (el.classList && el.classList.contains("lab-regime-score")) el.textContent = text;
    else if (el.classList && el.classList.contains("gc-regime")) {
      var lab = el.querySelector("div div div:nth-child(3)");
      if (lab) lab.textContent = re.label || "";
    } else el.textContent = text + asOf;
  }
}
function fe79_readSurfaces(tk) {
  var n = fe79_liveCryptoPct(tk);
  var t = n == null ? null : n.toFixed(2);
  var fpC = null;
  try { fpC = typeof fp === "function" ? String((fp(tk) || {}).c || "") : t; } catch (e) { fpC = t; }
  if (fpC === "") fpC = null;
  return { home: t, crypto: t, tape: t, market: t, phone: t, list: t, lens: t, signal: t, ask: t, fp: fpC === "—" ? null : fpC };
}
try { fe79_isCryptoTk.fn = function (tk) { try { if (typeof _rtIsCrypto === "function" && _rtIsCrypto(tk)) return true; } catch (e) {} return /^(BTC|ETH|SOL|XRP|DOGE|ADA|AVAX|LINK|DOT|LTC|BCH|UNI)$/.test(String(tk || "").toUpperCase()); }; } catch (eFn) {}

try {
  var fe79_lc0 = liveChg;
  liveChg = function (tk) {
    tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
    if (fe79_isCryptoTk(tk)) return fe79_liveCryptoPct(tk);
    if (tk === "XAU") return fe79_liveGold();
    var r = null;
    try { r = fe79_lc0.apply(this, arguments); } catch (e) { r = null; }
    if (r === 0) return null;
    return r;
  };
} catch (eLc) {}
try {
  var fe79_rc0 = referenceChg;
  referenceChg = function (tk) {
    tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
    if (fe79_isCryptoTk(tk)) return fe79_liveCryptoPct(tk);
    if (tk === "XAU") return fe79_liveGold();
    return fe79_rc0.apply(this, arguments);
  };
} catch (eRc) {}
try {
  var fe79_fp0 = fp;
  fp = function (tk) {
    var d = fe79_fp0.apply(this, arguments);
    if (!d) return d;
    try {
      tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
      if (fe79_isCryptoTk(tk)) {
        var pct = fe79_liveCryptoPct(tk);
        if (pct == null) { d.c = ""; d.chg = ""; }
        else {
          d.c = pct.toFixed(2);
          var bag = fe79_cryptoBase(tk);
          var px = (typeof P !== "undefined" && P[tk]) ? Number(P[tk].p) : 0;
          if (bag.base > 0 && px > 0) {
            var diff = px - bag.base;
            d.chg = Math.abs(diff) >= 1000 ? Math.round(diff).toLocaleString() : diff.toFixed(2);
          }
        }
      }
      if (tk === "XAU") {
        var g = fe79_liveGold();
        if (g == null) { d.c = ""; d.chg = ""; }
        else d.c = g.toFixed(2);
      }
      if (tk === "DXY" && d.p) d.p = fe79_dxyPx(d.p);
      if (tk === "TNX" || tk === "US10Y") {
        var yld = fe79_srv.TNX && fe79_srv.TNX.yield;
        if (yld && yld.source === "server" && yld.text) d.p = String(yld.text).replace(/%%+/g, "%");
        else if (d.p && d.p !== "—") d.p = fe79_onePct(d.p);
      } else if (typeof fe77_isYield === "function" && fe77_isYield(tk) && d.p && d.p !== "—") d.p = fe79_onePct(d.p);
    } catch (e) {}
    return d;
  };
} catch (eFp) {}
try {
  var fe79_cv0 = _rtCoinView;
  _rtCoinView = function (coin) {
    var out = fe79_cv0.apply(this, arguments);
    try {
      if (out) out.c24 = fe79_liveCryptoPct(out.tk, out.p);
    } catch (e) {}
    return out;
  };
} catch (eCv) {}
try {
  var fe79_ctx0 = _siteIntelContext;
  _siteIntelContext = function (surface) {
    var t = fe79_ctx0.apply(this, arguments);
    try {
      if (surface === "crypto" && typeof _cryptoMktData !== "undefined" && _cryptoMktData) {
        var line = _cryptoMktData.slice(0, 8).map(function (c) {
          var sym = String(c.symbol || "").toUpperCase();
          var pct = fe79_liveCryptoPct(sym, c.current_price);
          return sym + " " + (pct == null ? "—" : pct.toFixed(2) + "% 24h");
        }).join(", ");
        t = String(t).replace(/Crypto top:[^\n]*/, "Crypto top: " + line);
      }
    } catch (e) {}
    return t;
  };
} catch (eCtx) {}
try {
  var fe79_q0 = _rt47Q;
  _rt47Q = function (tk) {
    var q = fe79_q0.apply(this, arguments);
    if (!q) return q;
    try {
      if (tk === "XAU") {
        var goldQ = fe79_goldNow();
        q.c = goldQ ? goldQ.pct : fe79_liveGold();
        if (goldQ && goldQ.instrument === "futures") q.lb = "Gold futures (GC=F)";
      }
      else if (fe79_isCryptoTk(tk)) q.c = fe79_liveCryptoPct(tk);
      else if (q.c === 0 && (q.p === "—" || q.p === "" || q.c === 0) && !(typeof P !== "undefined" && P[tk] && isFinite(P[tk].c) && P[tk].c !== 0)) {
        if (String(q.c) === "0" && !(typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === true)) q.c = null;
      }
      if (tk === "TNX" || tk === "US10Y") {
        var yldQ = fe79_srv.TNX && fe79_srv.TNX.yield;
        if (yldQ && yldQ.source === "server" && yldQ.text) q.p = String(yldQ.text).replace(/%%+/g, "%");
        else q.p = fe79_onePct(q.p);
      } else if (typeof fe77_isYield === "function" && fe77_isYield(tk)) q.p = fe79_onePct(q.p);
      if (q.c != null && !isFinite(Number(q.c))) q.c = null;
      if (q.c != null && Number(Number(q.c).toFixed(2)) === 0 && tk === "XAU" && fe79_liveGold() == null) q.c = null;
    } catch (e) {}
    return q;
  };
} catch (eQ) {}
try {
  var fe79_ev0 = _signalEvidence;
  _signalEvidence = function (signal) {
    var ev = fe79_ev0.apply(this, arguments);
    if (!ev) return ev;
    try {
      if (signal && signal.tk === "XAU") {
        var goldNow = fe79_goldNow();
        ev.move = goldNow ? goldNow.pct : fe79_liveGold();
        if (goldNow && goldNow.pct == null) ev.reason = goldNow.note || goldNow.text || "";
      } else if (signal && fe79_isCryptoTk(signal.tk)) {
        var cp = fe79_liveCryptoPct(signal.tk);
        ev.move = cp;
        var too = cp != null && Math.abs(cp) > 1.5;
        var unavailable = ev.price === "UNAVAILABLE" || ev.status === "UNAVAILABLE";
        ev.stale = unavailable || too || !!(ev.meta && ev.meta.status === "stale");
        ev.conviction = unavailable ? null : too ? Math.min(signal.cf, 50) : signal.cf;
        ev.reason = too ? ("Comparable move " + cp.toFixed(2) + "% exceeds 1.5%") : (unavailable ? "Comparable price unavailable" : "");
      }
      if (signal && (signal.tk === "TNX" || signal.tk === "DXY")) {
        var px = ev.price;
        if (px == null || px === "UNAVAILABLE" || /^no price/i.test(String(px)) || String(px) === "null") ev.price = "Not available for this instrument";
      }
      if (ev.price == null || String(ev.price) === "null" || String(ev.price) === "undefined" || String(ev.price) === "NaN") ev.price = "Not available for this instrument";
    } catch (e) {}
    return ev;
  };
} catch (eEv) {}
var fe79_sigHold = {};
try {
  var fe79_sig0 = _rt52Sig;
  _rt52Sig = function (s) {
    var g = fe79_sig0.apply(this, arguments);
    if (!g || !s) return g;
    try {
      if (s.tk === "XAU") {
        var goldCard = fe79_goldNow();
        if (goldCard && goldCard.source === "server") {
          g.mvT = goldCard.pct == null ? "" : fe79_moveText(goldCard.pct, true);
          if (goldCard.pct == null) {
            fe79_sigHold.XAU = "";
            g.why = goldCard.note || goldCard.text || "—";
            g.line = goldCard.label ? (goldCard.label + " · " + (goldCard.text || "—")) : (goldCard.text || "—");
          } else if (goldCard.unchanged) {
            g.why = String(g.why || "").replace(/\+0\.00%[^·,]*/g, "unchanged");
            if (g.why.indexOf("unchanged") < 0) g.why = (g.why ? g.why + " · " : "") + "unchanged";
            g.line = goldCard.label + " · unchanged";
          } else {
            g.mvT = goldCard.text || g.mvT;
            var heldGold = Math.abs(goldCard.pct) > 1.5;
            g.why = heldGold
              ? ("Desk score " + s.cf + "/100, held at " + Math.min(s.cf, 50) + ": XAU moved " + g.mvT + ", past the 1.5% review line")
              : ("Desk score " + s.cf + "/100 · XAU " + g.mvT + ", within the 1.5% review line");
            g.line = (goldCard.label || "Gold") + " · " + g.mvT;
          }
          return g;
        }
        var mv = fe79_liveGold();
        var has = false;
        try {
          var qq = typeof fe76_quote === "function" ? fe76_quote("XAU") : null;
          has = !!(qq && qq.prev > 0);
          if (!has && typeof fe76_ownPrev === "function") has = !!fe76_ownPrev(P.XAU && P.XAU.p, fe76_spotPrev);
        } catch (e1) {}
        var mvT = fe79_moveText(mv, has);
        if (!mvT && fe79_sigHold.XAU) mvT = fe79_sigHold.XAU;
        if (mvT) fe79_sigHold.XAU = mvT;
        g.mvT = mvT;
        g.why = String(g.why || "").replace(/\+0\.00%[^·,]*/g, mvT || "").replace(/\s{2,}/g, " ").trim();
        if (mv == null && !mvT) g.why = g.why.replace(/\bunchanged\b/g, "").replace(/change not available/g, "").trim();
        if (mv != null && Number(mv.toFixed(2)) === 0 && has) {
          g.why = g.why.replace(/\+0\.00%[^·,]*/, "unchanged");
          if (g.why.indexOf("unchanged") < 0) g.why = (g.why ? g.why + " · " : "") + "unchanged";
        }
        g.line = String(g.line || "").replace(/\+0\.00%[^·]*/g, mvT || "").replace(/\s{2,}/g, " ").trim();
      }
      if ((s.tk === "TNX" || s.tk === "DXY") && g.st && /no price/i.test(String(g.st.txt || "") + String(g.line || ""))) {
        g.st.txt = "Not available for this instrument";
        g.line = String(g.line || "").replace(/no price yet|no price/ig, "Not available for this instrument");
        g.why = String(g.why || "").replace(/no price yet|no price/ig, "Not available for this instrument");
      }
    } catch (e) {}
    return g;
  };
} catch (eSig) {}
try {
  _rt51Label = function () { return fe79_tradeNow(); };
  _rt37Sum = function () { return fe79_tradeNow(); };
  quoteStatusSummary = function () { return fe79_tradeNow(); };
  _rt37Count = function () {
    if (fe79_sessionSrv && fe79_sessionSrv.tradingNow != null) {
      return { priced: fe79_sessionSrv.total, live: fe79_sessionSrv.tradingNow, total: fe79_sessionSrv.total, closed: fe79_sessionSrv.closed, quiet: fe79_sessionSrv.quiet || 0, open: true };
    }
    var b = fe79_session();
    return { priced: b.priced, live: b.live, total: b.total, closed: b.closed, quiet: b.quiet, open: true };
  };
  var fe79_hero0 = _rt37Hero;
  _rt37Hero = function () {
    if (fe79_sessionSrv) return fe79_tradeNow();
    var b = fe79_session();
    var out = [b.live + " trading now"];
    try {
      var prev = String(fe79_hero0.apply(this, arguments) || "");
      prev.split(" · ").slice(1).forEach(function (bit) { if (bit && !/trading now/.test(bit)) out.push(bit); });
    } catch (e) {}
    return out.join(" · ");
  };
  void fe79_hero0;
} catch (eTr) {}
try {
  var fe79_eng0 = _computeRegimeEngine;
  _computeRegimeEngine = function () {
    if (fe79_regimeHold && fe79_regimeBox) return fe79_regimeBox;
    var local = null;
    try { local = fe79_eng0.apply(this, arguments); } catch (e) { local = null; }
    try {
      if (typeof fe78_srvRegime !== "undefined" && fe78_srvRegime && !fe78_srvRegime.localEstimate) {
        fe79_regimeBox = fe78_srvRegime;
        return fe79_regimeBox;
      }
    } catch (e2) {}
    if (!fe79_regimeBox) fe79_regimeBox = local;
    else if (local && !fe79_regimeHold) {
      var same = fe79_regimeBox.label === local.label && fe79_regimeBox.score === local.score && fe79_regimeBox.asOfUk === local.asOfUk;
      if (!same) fe79_regimeBox = local;
    }
    return fe79_regimeBox;
  };
} catch (eReg) {}
try {
  var fe79_stamp0 = fe78_stampRegime;
  fe78_stampRegime = function (raw) {
    try { fe79_stamp0.apply(this, arguments); } catch (e) {}
    try {
      if (typeof fe78_srvRegime !== "undefined" && fe78_srvRegime) {
        fe79_regimeHold = false;
        fe79_regimeBox = fe78_srvRegime;
        fe79_paintRegime();
      }
    } catch (e2) {}
  };
} catch (eSt) {}
try {
  fe78_quoteLabel = function (q, displayName) {
    q = q || {};
    if (q.label) return String(q.label);
    var chip = fe79_goldChip({
      symbol: q.symbol || q.ticker || q.tk,
      source: q.source || q.src,
      name: displayName || q.name || q.label
    });
    if (chip) {
      if (chip === "Gold" && q.asOfUk) return "Gold";
      return chip;
    }
    var label = q.label != null ? String(q.label).trim() : "";
    if (label && !/^gold spot$/i.test(label)) return label;
    var name = String(displayName || "").trim();
    if (name && !/^gold spot$/i.test(name)) return name;
    return String(q.symbol || q.ticker || "");
  };
} catch (eLab) {}
try {
  var fe79_line0 = fe78_quoteLine;
  fe78_quoteLine = function (meta, displayName) {
    var quoted = meta && meta.quote;
    if (quoted && quoted.label) return fe79_askChip(meta).line;
    var line = "";
    try { line = fe79_line0.apply(this, arguments); } catch (e) { line = ""; }
    if (!line) return line;
    if (/Gold spot/.test(line) && /GC=F|futures/i.test(line + " " + displayName)) {
      line = line.replace(/^Gold spot/, "Gold futures (GC=F, delayed 10 min)");
    }
    return line;
  };
} catch (eLine) {}
try {
  fe78_academyNote = function (j, today) { return fe79_academyNote(j, today); };
  var fe79_store0 = fe78_academyStore;
  fe78_academyStore = function (box, j, today) {
    var out = fe79_store0.apply(this, arguments);
    try {
      var note = fe79_academyNote(j, today);
      if (out && note) out.note = note;
      if (out && j && j.edition) out.edition = j.edition;
    } catch (e) {}
    return out;
  };
} catch (eAc) {}
try {
  var fe79_step0 = _rt47StepHtml;
  _rt47StepHtml = function (s) {
    var html = fe79_step0.apply(this, arguments);
    try {
      var note = (typeof _rt48Ai !== "undefined" && _rt48Ai) ? _rt48Ai.note : null;
      if (typeof _rt48Ai !== "undefined" && _rt48Ai && _rt48Ai.edition) {
        note = fe79_academyNote(_rt48Ai, typeof _rt46Day === "function" ? _rt46Day() : "");
      } else if (note && note.text) {
        note = { text: fe79_stripUkDay(String(note.text).replace(/\.\s*·/g, " ·")), amber: !!note.amber };
        note.text = String(note.text).replace(/^From (\d{4}-\d{2}-\d{2})$/, function (_, iso) { return fe79_fromDate(iso) || ("From " + iso); });
      }
      var banner = typeof fe78_academyHtml === "function" ? fe78_academyHtml(note) : "";
      var news = typeof _rt47L !== "undefined" && _rt47L && _rt47L.id === "news";
      if (banner && news && String(html).indexOf("fe78-acad") < 0) html = banner + html;
    } catch (e) {}
    return html;
  };
} catch (eStep) {}
try {
  var fe79_chgText0 = fe78_chgText;
  fe78_chgText = function (tk, s) {
    var out = "";
    try { out = fe79_chgText0.apply(this, arguments); } catch (e) { out = String(s || ""); }
    out = fe79_stripUkDay(out);
    if (/market closed|opens\b|\d{1,2}:\d{2}\s*UK/i.test(out)) out = out.replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*$/i, "");
    return out;
  };
} catch (eCh) {}
try {
  var fe79_money0 = fe66_money;
  fe66_money = function (tk, n) {
    if (String(tk || "").toUpperCase() === "DXY") {
      var v = Number(n);
      if (!isFinite(v)) return "—";
      return fe79_dxyPx(Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(2));
    }
    var s = fe79_money0.apply(this, arguments);
    if (String(tk || "").toUpperCase() === "DXY") return fe79_dxyPx(s);
    return s;
  };
} catch (eMo) {}
try {
  var fe79_chip0 = fe64_chip;
  fe64_chip = function (tag) {
    var hit = fe79_catLabel(tag);
    if (hit) return hit;
    return fe79_chip0.apply(this, arguments);
  };
} catch (eChip) {}
try {
  var fe79_match0 = _matchTickerSignals;
  _matchTickerSignals = function (tk) {
    var rows = fe79_match0.apply(this, arguments) || [];
    var asOf = "";
    var dom = null;
    try { if (typeof _cryptoDominance !== "undefined" && _cryptoDominance) dom = _cryptoDominance.btc; } catch (e) {}
    try { if (typeof fe64_cgAsOf === "function") asOf = fe64_cgAsOf("global") || ""; } catch (e2) {}
    var out = [];
    for (var i = 0; i < rows.length; i++) {
      var s = rows[i];
      var card = fe79_domCard(tk, { a: s.a, tk: s.tk, cf: s.cf, tg: s.tg, dom: dom, asOf: asOf });
      if (!card) continue;
      if (card.a === "BTC dominance") {
        s = Object.assign({}, s, { a: "BTC dominance", x: card.x });
      }
      out.push(s);
    }
    return out;
  };
} catch (eMatch) {}
try {
  var fe79_brief0 = _renderDispatchBrief;
  _renderDispatchBrief = function () {
    var h = fe79_brief0.apply(this, arguments);
    return fe79_deskPhrase(h);
  };
} catch (eBr) {}
try {
  var fe79_dash0 = renderDash;
  renderDash = function () {
    var h = fe79_dash0.apply(this, arguments);
    return fe79_deskPhrase(h);
  };
} catch (eDa) {}
function fe79_scrub(root) {
  if (!root || !root.querySelectorAll) return;
  var nodes = root.querySelectorAll(".asset-price,.asset-chg,.ap-price,.ap-chg,.idx-card-px,.idx-card-chg,.conv-px,.conv-chg,.rt47-qp,.rt52-sig-e,.rt52-sig-w,.tt td,.home-tape,.home-brief,.home-brief-s");
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    if (el.querySelector && el.querySelector(".fe78-skel")) continue;
    var t = el.textContent || "";
    if (/^\s*(null|undefined|NaN)\s*$/.test(t)) {
      el.textContent = "Not available for this instrument";
      continue;
    }
    if (t.indexOf("%%") >= 0) el.textContent = t.replace(/%%+/g, "%");
    if (/US dollar index/.test(el.textContent || "")) el.textContent = fe79_titleCaseIndex(el.textContent);
    if (/\bUK\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/.test(el.textContent || "")) el.textContent = fe79_stripUkDay(el.textContent);
    if (/^\s*-\s*$/.test(t) && el.closest && el.closest("[data-price-card], .tt, .rt-cg-table")) {
      try { el.innerHTML = typeof fe78_skel === "function" ? fe78_skel() : "—"; } catch (e) {}
    }
  }
}
try {
  setInterval(function () {
    try { fe79_scrub(document.body); } catch (e) {}
    try { if (fe79_regimeBox) fe79_paintRegime(); } catch (e2) {}
  }, 400);
} catch (eIv) {}
try {
  if (typeof _rt48Ai !== "undefined" && _rt48Ai && _rt48Ai.note && _rt48Ai.note.text) {
    _rt48Ai.note.text = String(_rt48Ai.note.text).replace(/\.\s*·/g, " ·").replace(/^From (\d{4}-\d{2}-\d{2})$/, function (_, iso) { return fe79_fromDate(iso) || _; });
    if (_rt48Ai.edition === "yesterday") _rt48Ai.note = fe79_academyNote(_rt48Ai, typeof _rt46Day === "function" ? _rt46Day() : "");
  }
} catch (eBoot) {}
function fe79_takeRegime(raw) {
  var v = fe79_regimeView(raw);
  if (!v || v.useLocal) {
    fe79_regimeHold = false;
    return null;
  }
  fe79_regimeBox = fe79_setRegime(null, { label: v.label, score: v.score, asOfUk: v.asOfUk, asOf: v.asOf, localEstimate: false });
  fe79_regimeBox.thin = v.thin;
  fe79_regimeBox.stale = v.stale;
  fe79_regimeBox.source = "server";
  fe79_regimeHold = true;
  try { fe79_paintRegime(); } catch (e) {}
  return fe79_regimeBox;
}
function fe79_takeDesk(data) {
  if (!data || typeof data !== "object") return;
  var quotes = data.quotes && typeof data.quotes === "object" ? data.quotes : data;
  fe79_missing = Array.isArray(data.missing) ? data.missing : [];
  Object.keys(quotes).forEach(function (tk) {
    if (tk === "missing" || tk === "quotes" || tk === "sessionSummary" || tk === "regime") return;
    var row = quotes[tk];
    if (!row || typeof row !== "object") return;
    if (row.price == null && row.value == null && row.p == null && row.displayChange === undefined) return;
    if (Object.prototype.hasOwnProperty.call(row, "beta")) row = Object.assign({}, row, { betaSourced: true });
    fe79_ingest(tk, row);
  });
  fe79_missing.forEach(function (m) {
    if (!m || !m.ticker) return;
    fe79_srv[m.ticker] = Object.assign({}, fe79_srv[m.ticker], { missingReason: m.reason || "Not available for this instrument" });
  });
}
function fe79_noteJson(url, data) {
  if (!data || typeof data !== "object") return;
  url = String(url || "");
  try {
    if (/\/api\/regime(\?|$)/.test(url)) fe79_takeRegime(data);
    if (/session-summary/.test(url) && (data.text || data.tradingNow != null)) fe79_sessionSrv = data;
    if (/market-reference-quotes/.test(url)) {
      if (data.sessionSummary) fe79_sessionSrv = data.sessionSummary;
      if (data.regime) fe79_takeRegime(data.regime);
      if (data.US10Y) fe79_ingest("TNX", data.US10Y);
      ["XAU", "DXY", "BTC", "ETH", "SOL", "TNX"].forEach(function (tk) { if (data[tk] && typeof data[tk] === "object") fe79_ingest(tk, data[tk]); });
    }
    if (/desk-quotes/.test(url)) fe79_takeDesk(data);
    if (/\/api\/brief/.test(url)) {
      var reg = data.regime || (data.brief && data.brief.regime);
      if (reg && typeof reg === "object") fe79_takeRegime(reg);
    }
    if (/financials|listing-profile/.test(url)) {
      var sym = "";
      try { sym = decodeURIComponent((url.match(/symbol=([^&]+)/) || [])[1] || ""); } catch (eSym) { sym = ""; }
      if (sym) fe79_fin[sym] = data.valuation ? data : (data.data || data);
    }
  } catch (e) {}
}
function fe79_blockStaleCache() {
  function wipe(store, pred) {
    try {
      var keys = [];
      for (var i = 0; i < store.length; i++) keys.push(store.key(i));
      keys.forEach(function (k) { if (k && pred(k)) store.removeItem(k); });
    } catch (e) {}
  }
  try { wipe(localStorage, function (k) { return k.indexOf("td_brief_") === 0 || k === "td_brief_hist"; }); } catch (e1) {}
  try { wipe(sessionStorage, function (k) { return k.indexOf("td_si2_") === 0; }); } catch (e2) {}
  try {
    var set = Storage.prototype.setItem;
    if (!fe79_blockStaleCache.done) {
      Storage.prototype.setItem = function (k, v) {
        var key = String(k || "");
        if (this === localStorage && (key.indexOf("td_brief_") === 0 || key === "td_brief_hist")) return;
        if (this === sessionStorage && key.indexOf("td_si2_") === 0) return;
        return set.apply(this, arguments);
      };
      fe79_blockStaleCache.done = true;
    }
  } catch (e3) {}
}
function fe79_finHtml(tk, data, html) {
  var view = fe79_finView(data || fe79_fin[tk] || {});
  if (view.source !== "server") return html;
  var h = String(html || "");
  if (view.peBasis) h = h.replace(/EPS \(TTM\)/g, "EPS (TTM, " + view.peBasis + ")").replace(/>P\/E</g, ">P/E (" + view.peBasis + ")<");
  if (view.dividend && view.dividend.basis) h = h.replace(/Dividend Yield/g, "Dividend yield (" + view.dividend.basis + ")");
  Object.keys(view.hidden).forEach(function (field) {
    var label = field === "pe" ? "P/E" : field === "pb" ? "P/B" : field === "ps" ? "P/S" : field === "divYield" || field === "dividend" ? "Dividend" : field;
    h = h.replace(new RegExp("<div[^>]*>\\s*" + label + "[\\s\\S]*?</div>\\s*</div>", "i"), "");
  });
  if (view.notes && view.notes.length) h += '<p class="fe79-eps-note">' + view.notes.map(function (n) { return String(n); }).join(" ") + "</p>";
  return h;
}
try { fe79_blockStaleCache(); } catch (eCache) {}
try {
  var fe79_about0 = fe78_about;
  fe78_about = function (a) {
    var v = fe79_aboutText(a);
    if (v.source === "hidden") return "";
    if (v.source === "server" || v.source === "fallback") return v.text;
    try { return fe79_about0.apply(this, arguments) || ""; } catch (e) { return ""; }
  };
} catch (eAbout) {}
try {
  var fe79_live2 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q) {
    try { fe79_ingest(tk, q); } catch (e) {}
    return fe79_live2.apply(this, arguments);
  };
} catch (eIn) {}
try {
  var fe79_qrow0 = _rt47QRow;
  _rt47QRow = function (tk) {
    var html = fe79_qrow0.apply(this, arguments);
    if (tk === "XAU") {
      var g = fe79_goldNow();
      if (g && g.instrument === "futures") html = String(html).replace("Gold (spot)", "Gold futures (GC=F)");
      else if (g && g.label && g.instrument === "spot") html = String(html).replace("Gold (spot)", g.label);
    }
    return html;
  };
} catch (eRow) {}
try {
  var fe79_rf0 = renderFinancials;
  renderFinancials = function (tk, data) {
    var h = fe79_rf0.apply(this, arguments);
    try { if (data) fe79_fin[tk] = data; } catch (e) {}
    try { h = fe79_finHtml(tk, data, h); } catch (e2) {}
    return h;
  };
} catch (eFin) {}
try {
  var fe79_fetch0 = fetch;
  fetch = function (input, init) {
    var url = typeof input === "string" ? input : (input && input.url) || "";
    var p = fe79_fetch0.apply(this, arguments);
    if (!p || typeof p.then !== "function") return p;
    if (!/\/api\/(regime|session-summary|market-reference-quotes|desk-quotes|brief|financials|listing-profile)|yahoo-quote|ext-hours|coingecko/.test(String(url))) return p;
    return p.then(function (res) {
      try {
        if (res && res.ok && res.clone) res.clone().json().then(function (j) { fe79_noteJson(url, j); }).catch(function () {});
      } catch (e) {}
      return res;
    });
  };
} catch (eFetch) {}
function fe79_bootConsume() {
  function pull(url) {
    try {
      fetch(url, { credentials: "same-origin", cache: "no-store" }).then(function (r) { return r && r.ok ? r.json() : null; }).then(function (j) { if (j) fe79_noteJson(url, j); }).catch(function () {});
    } catch (e) {}
  }
  pull("/api/regime");
  pull("/api/session-summary");
  pull("/api/market-reference-quotes");
  pull("/api/desk-quotes?symbols=TNX,DXY,XAU,BTC&beta=1");
}
try { setTimeout(fe79_bootConsume, 30); } catch (eBoot2) {}
try {
  var fe79_step1 = _rt47StepHtml;
  _rt47StepHtml = function (s) {
    var html = fe79_step1.apply(this, arguments);
    try {
      if (s && s.ai && s.t === "q" && typeof _rt48Ai !== "undefined" && _rt48Ai && Array.isArray(_rt48Ai.items)) {
        var it = _rt48Ai.items[s.n % 10 - 5];
        var look = (typeof RT48B_LOOK !== "undefined" && it && RT48B_LOOK[it.asset]) || (it && it.asset === "natgas" ? fe79_natgas() : null);
        if (look && String(html).indexOf("fe79-asset") < 0) {
          var chip = '<p class="fe79-asset" style="color:' + (look.color || look.col || "inherit") + '">' + (typeof _rt47Ic === "function" && look.icon ? _rt47Ic(look.icon || look.ic) : (typeof _rt47Ic === "function" && look.ic ? _rt47Ic(look.ic) : "")) + (look.label || "") + "</p>";
          html = chip + html;
        }
      }
    } catch (e) {}
    return html;
  };
} catch (eNat) {}
