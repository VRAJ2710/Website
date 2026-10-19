// ── rt61b ──
// FE77_PURE_START
var fe77_xauRaw = null;
var fe77_xauHold = false;
var fe77_dxyIce = false;
var fe77_dxyIceQ = null;
var fe77_streamState = { early: null, done: null };

function fe77_esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function fe77_deskLine(tk, sc) {
  return "Top desk score: " + tk + " " + sc + "/100 (Dispatch desk score).";
}
function fe77_scrubDesk(s) {
  return String(s == null ? "" : s).replace(/Highest conviction on desk:\s*([A-Z0-9.^]+)\s*\(\s*(\d+)\s*\/\s*100[^)]*\)\.?/gi, function (_m, tk, n) {
    return fe77_deskLine(tk, n);
  });
}
function fe77_applyDesk(b) {
  if (!b || typeof b !== "object") return b;
  if (typeof b.summary === "string") b.summary = fe77_scrubDesk(b.summary);
  var raw = b.topDeskScore || b.highestConviction || b.topScore;
  var extra = "";
  if (raw && typeof raw === "object") extra = fe77_deskLine(raw.tk || raw.ticker || raw.symbol || "", raw.score != null ? raw.score : raw.sc);
  else if (typeof raw === "string") extra = fe77_scrubDesk(raw);
  if (extra && String(b.summary || "").indexOf("Top desk score:") < 0) b.summary = (extra + " " + (b.summary || "")).trim();
  return b;
}
function fe77_pct(n) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  if (typeof _rt53Pct === "function") {
    try { var shared = _rt53Pct(v); if (shared) return shared; } catch (e) {}
  }
  var sign = v > 0 ? "+" : v < 0 ? "\u2212" : "";
  return sign + Math.abs(v).toFixed(2) + "%";
}
function fe77_money(n) {
  var v = Number(n);
  if (!isFinite(v)) return "";
  if (typeof fe76_group === "function") {
    try { return fe76_group(v, Math.abs(v) >= 1 ? 2 : 4); } catch (e) {}
  }
  var dp = Math.abs(v) >= 1 ? 2 : 4;
  return v.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp });
}
function fe77_hhmm(asOfUk, asOf) {
  var s = String(asOfUk || "");
  var m = s.match(/(\d{1,2}):(\d{2})/);
  if (m) return (m[1].length === 1 ? "0" + m[1] : m[1]) + ":" + m[2];
  var ms = Date.parse(asOf || "");
  if (!isFinite(ms)) return "";
  try {
    var t = new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: "Europe/London" });
    var hm = String(t).match(/(\d{2}:\d{2})/);
    return hm ? hm[1] : "";
  } catch (e) { return ""; }
}
function fe77_asOfLabel(row) {
  var hm = fe77_hhmm(row && row.asOfUk, row && row.asOf);
  return hm ? ("as of " + hm + " UK") : "";
}
function fe77_themeChange(row) {
  if (!row) return null;
  if (row.changePct != null && row.changePct !== "") return Number(row.changePct);
  if (row.change != null && row.change !== "") return Number(row.change);
  return null;
}
function fe77_spyChange(row) {
  if (!row) return null;
  if (row.spyChange != null && row.spyChange !== "") return Number(row.spyChange);
  if (row.benchmark && row.benchmark.changePct != null) return Number(row.benchmark.changePct);
  return null;
}
function fe77_themeSource(row) {
  var s = row && row.source;
  if (!s) return "";
  if (typeof s === "object") return String(s.name || "");
  return String(s);
}
function fe77_excludedNote(list) {
  if (!Array.isArray(list) || !list.length) return "";
  return list.map(function (x) {
    if (x == null) return "";
    if (typeof x === "string") return x;
    return String(x.theme || x.name || "");
  }).filter(Boolean).join(", ");
}
function fe77_themesView(b, kind) {
  var leading = kind !== "lagging";
  var empty = { label: leading ? "Leading themes" : "Lagging themes", items: [], excluded: "" };
  if (!b || typeof b !== "object") return empty;
  var rows = leading ? (b.leadingThemes || b.leading_themes) : (b.laggingThemes || b.lagging_themes);
  var label = leading
    ? (b.leadingThemesLabel || b.overweightLabel || "Leading themes")
    : (b.laggingThemesLabel || b.underweightLabel || "Lagging themes");
  var items = [];
  if (Array.isArray(rows) && rows.length) {
    rows.forEach(function (row) {
      if (!row || typeof row !== "object") return;
      var theme = String(row.theme || row.name || "");
      var proxy = String(row.proxy || "");
      var ch = fe77_themeChange(row);
      var spy = fe77_spyChange(row);
      var src = fe77_themeSource(row);
      var asOf = fe77_asOfLabel(row);
      var name = theme + (proxy ? " (" + proxy + ")" : "");
      var changeText = ch == null || !isFinite(ch) ? "" : fe77_pct(ch);
      var spyText = spy == null || !isFinite(spy) ? "" : ("SPY " + fe77_pct(spy));
      var meta = [src, asOf].filter(Boolean).join(" · ");
      items.push({
        name: name, changeText: changeText, spyText: spyText, meta: meta, source: src, asOf: asOf,
        line: [name, changeText, spyText, meta].filter(Boolean).join(" · ")
      });
    });
  } else {
    var names = leading ? b.overweight : b.underweight;
    if (Array.isArray(names)) names.forEach(function (x) {
      items.push({ name: String(x), changeText: "", spyText: "", meta: "", source: "", asOf: "", line: String(x) });
    });
  }
  return { label: label, items: items, excluded: leading ? fe77_excludedNote(b.themesExcluded) : "" };
}
function fe77_themesPlain(b) {
  var view = fe77_themesView(b, "leading");
  if (!view.items.length) return "";
  var out = view.label + ": " + view.items.map(function (it) { return it.line; }).join("; ");
  if (view.excluded) out += ". Excluded: " + view.excluded;
  return out;
}
function fe77_briefThemes(b) {
  var lead = fe77_themesView(b, "leading");
  var lag = fe77_themesView(b, "lagging");
  if (!lead.items.length && !lag.items.length && !lead.excluded) return "";
  function col(view) {
    if (!view || !view.items.length) return "";
    var rows = view.items.map(function (it) {
      return '<div class="fe77-theme"><span class="fe77-theme-name">' + fe77_esc(it.name) + "</span>"
        + (it.changeText ? '<span class="fe77-theme-chg">' + fe77_esc(it.changeText) + "</span>" : "")
        + (it.spyText ? '<span class="fe77-theme-spy">' + fe77_esc(it.spyText) + "</span>" : "")
        + (it.meta ? '<span class="fe77-theme-meta">' + fe77_esc(it.meta) + "</span>" : "")
        + "</div>";
    }).join("");
    return '<div class="fe77-theme-col"><div class="fe77-theme-k">' + fe77_esc(view.label) + "</div>" + rows + "</div>";
  }
  var note = lead.excluded ? '<div class="fe77-excluded">Excluded: ' + fe77_esc(lead.excluded) + "</div>" : "";
  return '<div class="fe77-themes-wrap">' + col(lead) + col(lag) + note + "</div>";
}
function fe77_points(raw) {
  if (raw == null || raw === "") return [];
  if (typeof raw === "string") return [raw];
  if (!Array.isArray(raw)) return [];
  return raw.map(function (x) {
    if (typeof x === "string") return x;
    return String((x && (x.point || x.action || x.what || x.text)) || "");
  }).filter(Boolean);
}
function fe77_takeText(r) {
  if (!r || typeof r !== "object") return "";
  var raw = r.takeaway || r.whatToWatch || r.whatTheDataShows || r.recommendation || r.tradingImplication || r.tradeConsiderations || r.rebalance;
  var pts = fe77_points(raw);
  return pts.join(" ");
}
function fe77_portWatch(r) {
  var pts = fe77_points(r && (r.takeaway || r.whatToWatch || r.whatTheDataShows || r.rebalance));
  if (!pts.length) return "";
  return '<div style="background:var(--b1);border:1px solid var(--gb);border-radius:9px;padding:11px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.12em;margin-bottom:6px">TAKEAWAY</div>'
    + pts.map(function (x) { return '<div style="font-size:10.5px;color:var(--t2);padding:3px 0;line-height:1.4">' + fe77_esc(x) + "</div>"; }).join("")
    + "</div>";
}
function fe77_earnTake(r) {
  return fe77_takeText(r);
}
function fe77_intelTake(r) {
  var text = fe77_takeText(r);
  if (!text) return "";
  return '<div class="gc" style="padding:14px;border-left:3px solid var(--t3);margin-bottom:10px"><div style="font-family:var(--mn);font-size:8px;color:var(--t3);letter-spacing:0.18em;margin-bottom:6px">TAKEAWAY</div><div style="font-family:var(--sn);font-size:13px;color:var(--tx);line-height:1.65;font-weight:500">' + fe77_esc(text) + "</div></div>";
}
function fe77_takeStreamMeta(ev, state) {
  var box = state || fe77_streamState;
  if (!ev || typeof ev !== "object") return box;
  if (ev.meta && typeof ev.meta === "object") {
    if (ev.done) box.done = ev.meta;
    else box.early = ev.meta;
  }
  return box;
}
function fe77_streamMeta(final, state) {
  var box = state || fe77_streamState;
  if (final && final.meta && typeof final.meta === "object") box.done = final.meta;
  var meta = box.done || box.early || null;
  if (!state) fe77_streamState = { early: null, done: null };
  return meta;
}
function fe77_freshWord(delayMin, status) {
  var st = String(status || "");
  if (st === "closed" || st === "lunch") return "";
  var n = Number(delayMin);
  if (n > 0) return "delayed " + Math.round(n) + " min";
  if (n === 0) return "LIVE";
  return "";
}
function fe77_fxKey(raw) {
  var s = String(raw || "").toUpperCase().replace(/^\$/, "").trim();
  if (!s) return "";
  var pairs = { EURUSD: 1, GBPUSD: 1, USDJPY: 1, EURJPY: 1, GBPJPY: 1 };
  if (pairs[s]) return s;
  var yahoo = { "JPY=X": "USDJPY", "EURUSD=X": "EURUSD", "GBPUSD=X": "GBPUSD", "EURJPY=X": "EURJPY", "GBPJPY=X": "GBPJPY" };
  if (yahoo[s]) return yahoo[s];
  var bare = s.replace(/=X$/, "");
  if (pairs[bare]) return bare;
  if (s === "USDJPY=X") return "USDJPY";
  return "";
}
function fe77_dayPart(hour) {
  var h = Number(hour);
  if (!isFinite(h)) h = 12;
  if (h < 12) return "Morning";
  if (h < 17) return "Afternoon";
  return "Evening";
}
function fe77_briefTitle(edition, hour) {
  var label = "";
  if (edition && typeof edition === "object") label = edition.label || (edition.lead && edition.lead.label) || "";
  if (label) return String(label);
  return fe77_dayPart(hour) + " brief";
}
function fe77_futText(raw) {
  raw = raw || {};
  var fc = raw.futuresChange;
  if (fc && typeof fc === "object") {
    if (fc.text) return String(fc.text);
    var label = fc.label || "Gold futures (GC=F, delayed 10 min)";
    var c = fc.changePct != null ? fc.changePct : (fc.c != null ? fc.c : fc.change);
    if (c == null && Number(fc.price) > 0 && Number(fc.prevClose) > 0) c = ((Number(fc.price) - Number(fc.prevClose)) / Number(fc.prevClose)) * 100;
    if (c == null || !isFinite(Number(c))) return String(label);
    return String(label) + " " + fe77_pct(Number(c));
  }
  var f = raw.futures;
  if (!f || typeof f !== "object") return "";
  var pct = f.changePct != null ? f.changePct : (f.c != null ? f.c : f.change);
  if (pct == null && Number(f.price) > 0 && Number(f.prevClose) > 0) pct = ((Number(f.price) - Number(f.prevClose)) / Number(f.prevClose)) * 100;
  var name = f.label || "Gold futures (GC=F, delayed 10 min)";
  if (pct == null || !isFinite(Number(pct))) return String(name);
  return String(name) + " " + fe77_pct(Number(pct));
}
function fe77_dxyTitle(ice, fallback, label) {
  if (fallback) return "Dispatch FX basket";
  if (ice) return label || "US Dollar Index (ICE, Yahoo DX-Y.NYB)";
  return "Dispatch FX basket";
}
function fe77_quotePreview(meta) {
  if (typeof fe76_quoteBlock === "function") {
    try { var html = fe76_quoteBlock(meta); if (html) return html; } catch (e) {}
  }
  var q = meta && meta.quote;
  if (!q) return "";
  var n = Number(q.price != null ? q.price : (q.px != null ? q.px : q.last));
  if (!isFinite(n)) return "";
  var blob = [q.symbol, q.feed, q.source, q.name].join(" ");
  var label = /GC=F|futures/i.test(blob) && !/gold-api/i.test(blob) ? "Gold futures (GC=F, delayed 10 min)" : "Gold spot";
  var asOf = q.asOfUk ? String(q.asOfUk) : fe77_asOfLabel(q).replace(/^as of /, "");
  return label + " " + fe77_money(n) + (asOf ? " · " + asOf : "");
}
// FE77_PURE_END

var fe77_dxyFallback = false;
var fe77_dxyLabel = "";
function fe77_dxyName() {
  return fe77_dxyTitle(fe77_dxyIce, fe77_dxyFallback, fe77_dxyLabel);
}
function fe77_quietQ(q) {
  return !!(q && (q.changeAvailable === false || q.noPrevClose === true));
}
function fe77_liveQ(q) {
  return !!(q && q.changeAvailable === true && q.noPrevClose !== true);
}
function fe77_iceBlob(q) {
  if (!q || typeof q !== "object") return false;
  var bits = [q.symbol, q.feedSymbol, q.yahooSymbol, q.source, q.feed, q.name, q.provider, q.id];
  if (q.feed && typeof q.feed === "object") bits.push(q.feed.symbol, q.feed.source, q.feed.name);
  return /DX-Y\.NYB/i.test(bits.filter(Boolean).join(" "));
}
function fe77_copy(q) {
  var out = {};
  if (!q || typeof q !== "object") return out;
  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];
  return out;
}
function fe77_takeRef(data) {
  if (!data || typeof data !== "object") return;
  if (data.XAU) fe77_xauRaw = data.XAU;
  if (fe77_quietQ(data.XAU)) fe77_xauHold = true;
  else if (fe77_liveQ(data.XAU)) fe77_xauHold = false;
  var d = data.DXY || null;
  fe77_dxyFallback = !!(d && d.fallback === true);
  fe77_dxyLabel = "";
  if (fe77_dxyFallback) {
    fe77_dxyIce = false;
    fe77_dxyIceQ = null;
    return;
  }
  var ice = data["DX-Y.NYB"] || null;
  if (!ice && fe77_iceBlob(d)) ice = d;
  if (!ice && d && fe77_iceBlob(d.yahoo)) ice = d.yahoo;
  if (!ice && d && fe77_iceBlob(d.ice)) ice = d.ice;
  if (!ice && d && /DX-Y\.NYB/i.test(String(d.label || d.name || d.symbol || ""))) ice = d;
  var px = ice ? Number(ice.p != null ? ice.p : ice.price) : 0;
  fe77_dxyIce = px > 0;
  fe77_dxyIceQ = fe77_dxyIce ? ice : null;
  if (fe77_dxyIce) {
    var named = String((ice && (ice.label || ice.name)) || (d && (d.label || d.name)) || "");
    fe77_dxyLabel = /DX-Y\.NYB|Yahoo/i.test(named) ? named : "US Dollar Index (ICE, Yahoo DX-Y.NYB)";
  }
}
function fe77_prepXau(q) {
  if (!q || typeof q !== "object") return q;
  fe77_xauRaw = q;
  if (fe77_quietQ(q)) fe77_xauHold = true;
  else if (fe77_liveQ(q)) fe77_xauHold = false;
  var copy = fe77_copy(q);
  delete copy.futures;
  if (fe77_xauHold) {
    delete copy.c; delete copy.prev; delete copy.change; delete copy.changePct;
    copy.basis = "none";
    copy.noBasePrev = true;
    try { fe76_spotPrev = null; } catch (e) {}
  }
  if (fe77_xauHold || copy.dayRangeAvailable === false) {
    delete copy.dayHigh; delete copy.dayLow; delete copy.regularMarketDayHigh; delete copy.regularMarketDayLow; delete copy.high; delete copy.low;
  }
  return copy;
}
function fe77_prepDxy(data) {
  fe77_takeRef(data);
  if (fe77_dxyIceQ) {
    var q = fe77_copy(fe77_dxyIceQ);
    if (!(Number(q.p) > 0) && Number(q.price) > 0) q.p = Number(q.price);
    q.name = fe77_dxyName();
    q.source = "yahoo";
    q.proxy = false;
    return q;
  }
  var d = data && data.DXY;
  if (!d) return d;
  var out = fe77_copy(d);
  out.name = "Dispatch FX basket";
  return out;
}
function fe77_futObj() {
  var f = fe77_xauRaw && fe77_xauRaw.futures;
  return f && typeof f === "object" ? f : null;
}
function fe77_futPct(f) {
  if (!f) return null;
  var c = f.changePct != null ? f.changePct : (f.c != null ? f.c : (f.change != null ? f.change : null));
  if (c == null && Number(f.price) > 0 && Number(f.prevClose) > 0) c = ((Number(f.price) - Number(f.prevClose)) / Number(f.prevClose)) * 100;
  var n = Number(c);
  return isFinite(n) ? n : null;
}
function fe77_futLine() {
  return fe77_futText(fe77_xauRaw);
}
function fe77_futHlText() {
  var f = fe77_futObj();
  if (!f) return "";
  var h = Number(f.dayHigh), l = Number(f.dayLow);
  if (!(h > 0) || !(l > 0)) return "";
  return "Futures high " + fe77_money(h) + " · Futures low " + fe77_money(l);
}
function fe77_showFut() {
  if (fe77_xauHold) return true;
  var fc = fe77_xauRaw && fe77_xauRaw.futuresChange;
  return !!(fc && typeof fc === "object" && (fc.text || fc.changePct != null || fc.change != null || fc.price != null));
}
function fe77_goldTile(html) {
  if (typeof html !== "string") return html;
  if (fe77_xauHold) html = html.replace(/ <span class="bb1-c [\s\S]*?<\/span>/, "");
  if (!fe77_showFut()) return html;
  var bits = "";
  var line = fe77_futLine();
  var hl = fe77_futHlText();
  if (line) bits += '<div class="fe77-fut">' + fe77_esc(line) + "</div>";
  if (hl) bits += '<div class="fe77-fut fe77-fut-hl">' + fe77_esc(hl) + "</div>";
  if (!bits) return html;
  return html.replace('</div><p class="bb1-why">', "</div>" + bits + '<p class="bb1-why">');
}
function fe77_dxyTile(html) {
  if (typeof html !== "string") return html;
  return html.replace('class="bb1-k">Dollar', 'class="bb1-k">' + fe77_esc(fe77_dxyName()));
}
function fe77_css() {
  try {
    if (document.getElementById("fe77-css")) return;
    var st = document.createElement("style");
    st.id = "fe77-css";
    st.textContent = ".ai-retry-state{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start}.ai-retry-copy{display:flex;flex-direction:column;gap:4px;min-width:0}.openbb-customer-symbols{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.openbb-symbol-btn{padding:4px 10px;border:1px solid var(--gb);border-radius:999px;background:var(--b2);color:var(--t2)}.fe77-themes-wrap{padding:10px 16px;border-top:1px solid var(--gb)}.fe77-themes-wrap{display:flex;flex-direction:column;gap:8px}.fe77-theme-k{font-family:var(--mn);font-size:10px;letter-spacing:0.12em;color:var(--t2);margin-bottom:6px}.fe77-theme{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;padding:3px 0;font-size:12px;color:var(--t2)}.fe77-theme-chg,.fe77-theme-spy{font-family:var(--mn);font-weight:700;color:var(--tx)}.fe77-theme-meta{font-size:10px;color:var(--t3)}.fe77-excluded{font-size:10px;color:var(--t3);line-height:1.4}.fe77-fut{display:block;font-family:var(--mn);font-size:11px;line-height:1.35;color:var(--t2);margin-top:3px;white-space:normal;font-weight:500}.bb1-tile .fe77-fut{margin-top:4px}";
    document.head.appendChild(st);
  } catch (e) {}
}
try { fe77_css(); } catch (e) {}
try {
  var fe77_clean0 = _rt18BriefClean;
  _rt18BriefClean = function (b) {
    var out = fe77_clean0.apply(this, arguments);
    try { fe77_applyDesk(out); } catch (e) {}
    return out;
  };
} catch (e) {}
try {
  var fe77_one0 = _rt53One;
  _rt53One = function (spec) {
    var html = fe77_one0.apply(this, arguments);
    try {
      if (spec && spec[0] === "gold") html = fe77_goldTile(html);
      if (spec && spec[0] === "dollar") html = fe77_dxyTile(html);
    } catch (e) {}
    return html;
  };
} catch (e) {}
try {
  var fe77_src0 = _rt53Src;
  _rt53Src = function (tk) {
    if (tk === "DXY") return fe77_dxyName();
    if (tk === "XAU") return "Spot gold";
    return fe77_src0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_st0 = _rt53Status;
  _rt53Status = function (tk) {
    if (tk === "DXY") return fe77_dxyName();
    if (tk === "XAU") return "Spot";
    return fe77_st0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_tn0 = fe65_tapeName;
  fe65_tapeName = function (tk) {
    if (tk === "DXY") return fe77_dxyName();
    return fe77_tn0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_sl0 = _quoteSourceLabel;
  _quoteSourceLabel = function (src) {
    var out = "";
    try { out = fe77_sl0.apply(this, arguments); } catch (e) { out = String(src || ""); }
    var blob = String(src || "") + " " + out;
    if (fe77_dxyIce && /DX-Y\.NYB|dollar index|dxy/i.test(blob)) return fe77_dxyName();
    if (!fe77_dxyIce && /dxy-fx-computed|dxy-computed|fx-computed|computed from live fx|FX-computed|FX-COMPUTED/i.test(blob)) return "Dispatch FX basket";
    return out;
  };
} catch (e) {}
try {
  var fe77_fd0 = _frontDoorQuote;
  _frontDoorQuote = function (tk, name, description) {
    if (tk === "DXY") {
      name = fe77_dxyName();
      description = fe77_dxyName();
    }
    return fe77_fd0.call(this, tk, name, description);
  };
} catch (e) {}
try {
  var fe77_rt0 = _rtApply;
  _rtApply = function (tk, p, o) {
    if (tk === "XAU" && fe77_xauHold) {
      try { if (typeof _rt !== "undefined" && _rt) _rt.gcPct = null; } catch (e0) {}
      var opt = {};
      var src = o || {};
      for (var k in src) if (Object.prototype.hasOwnProperty.call(src, k)) opt[k] = src[k];
      delete opt.prev;
      opt.noBasePrev = true;
      var r = fe77_rt0.call(this, tk, p, opt);
      try {
        fe76_spotPrev = null;
        if (P.XAU) P.XAU.c = 0;
        liveQuoteChangeAvailable.XAU = false;
      } catch (e1) {}
      return r;
    }
    if (tk === "DXY") {
      var opt2 = {};
      var src2 = o || {};
      for (var k2 in src2) if (Object.prototype.hasOwnProperty.call(src2, k2)) opt2[k2] = src2[k2];
      opt2.name = fe77_dxyName();
      return fe77_rt0.call(this, tk, p, opt2);
    }
    return fe77_rt0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_gc0 = _rt34Gc;
  _rt34Gc = function () {
    if (fe77_xauHold) return;
    return fe77_gc0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_guard0 = _rtGuard;
  _rtGuard = function (tk, q, source) {
    if (tk === "XAU" && fe77_xauHold && q) {
      delete q.c; delete q.prev; delete q.change; delete q.changePct;
      q.basis = "none";
    }
    var r = fe77_guard0.apply(this, arguments);
    if (tk === "XAU" && fe77_xauHold) {
      try { if (typeof _rt !== "undefined" && _rt) _rt.gcPct = null; } catch (e2) {}
    }
    return r;
  };
} catch (e) {}
try {
  var fe77_ref0 = _rt37Ref;
  _rt37Ref = function (tk, q) {
    if (tk === "XAU") return fe77_prepXau(q);
    return fe77_ref0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_hl0 = fe69_hlHtml;
  fe69_hlHtml = function (tk) {
    if (tk === "XAU") {
      var text = fe77_futHlText();
      if (!text) return "";
      var parts = text.split(" · ");
      return '<div class="fe68-hl fe77-fut-hl"><span>' + fe77_esc(parts[0] || "") + "</span><span>" + fe77_esc(parts[1] || "") + "</span></div>";
    }
    return fe77_hl0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_fill0 = fe69_fillHl;
  fe69_fillHl = function (tk) {
    if (tk === "XAU") return;
    return fe77_fill0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_gs0 = _renderGoldSurface;
  _renderGoldSurface = function () {
    var h = fe77_gs0.apply(this, arguments);
    if (typeof h !== "string") return h;
    if (fe77_xauHold) h = h.replace(/<span class="gd-chg[^"]*">[\s\S]*?<\/span>/g, "");
    if (fe77_showFut()) {
      var line = fe77_futLine();
      var hl = fe77_futHlText();
      var extra = "";
      if (line) extra += '<div class="fe77-fut">' + fe77_esc(line) + "</div>";
      if (hl) extra += '<div class="fe77-fut">' + fe77_esc(hl) + "</div>";
      if (extra) h = h.replace(/(<div class="gd-px">[\s\S]*?<\/div>)/, "$1" + extra);
    }
    h = h.replace(/<span>DXY<\/span>/g, "<span>" + fe77_esc(fe77_dxyName()) + "</span>");
    h = h.replace(/Computed from 6 live FX pairs · ICE weights/g, fe77_dxyName());
    return h;
  };
} catch (e) {}
try {
  var fe77_tape0 = renderTape;
  renderTape = function () {
    var r = fe77_tape0.apply(this, arguments);
    try {
      if (!fe77_showFut()) return r;
      var line = fe77_futLine();
      if (!line) return r;
      document.querySelectorAll('#tape .ti[data-tk="XAU"]').forEach(function (el) {
        var ch = el.children && el.children[2];
        if (ch && fe77_xauHold) ch.textContent = "";
        if (el.querySelector(".fe77-fut")) return;
        var n = document.createElement("span");
        n.className = "fe77-fut";
        n.textContent = line;
        el.appendChild(n);
      });
    } catch (e2) {}
    return r;
  };
} catch (e) {}
try {
  var fe77_sub0 = _rt43SubText;
  _rt43SubText = function (tk) {
    if (tk === "XAU" && fe77_xauHold) return fe77_futLine();
    if (tk === "DXY") return fe77_dxyName();
    var t = fe77_sub0.apply(this, arguments);
    if (tk === "XAU" && typeof t === "string" && /Futures /.test(t) && !fe77_showFut()) return "";
    return t;
  };
} catch (e) {}

function fe77_emptyBrief() {
  var part = "Afternoon";
  try {
    part = fe77_dayPart(Number(new Date().toLocaleString("en-GB", { hour: "numeric", hourCycle: "h23", timeZone: "Europe/London" })));
  } catch (e) {}
  return part + " brief not published yet today.";
}
function fe77_ukStamp(ms) {
  try {
    return new Date(ms || Date.now()).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "Europe/London" });
  } catch (e) { return ""; }
}
function fe77_ukHour(ms) {
  try {
    return Number(new Date(ms || Date.now()).toLocaleString("en-GB", { hour: "numeric", hourCycle: "h23", timeZone: "Europe/London" }));
  } catch (e) { return 12; }
}
function fe77_delayOf(tk, meta) {
  var d = null;
  function take(v) { if (typeof v === "number" && isFinite(v)) d = v; }
  try { if (meta) take(meta.delayMin); } catch (e) {}
  try { var b = typeof fe70_bag === "function" ? fe70_bag(tk) : null; if (b) take(b.delayMin); } catch (e2) {}
  try { var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null; if (y) take(y.delayMin); } catch (e3) {}
  try { var f = typeof fe76_feedOf === "function" ? fe76_feedOf(tk) : null; if (f) take(f.delayMin); } catch (e4) {}
  try { if (typeof _rt23Ch !== "undefined" && _rt23Ch[tk]) take(_rt23Ch[tk].delayMin); } catch (e5) {}
  return d;
}
function fe77_applyFresh(tk, o) {
  if (!o || typeof o !== "object") return o;
  if (o.status === "closed" || o.status === "lunch") return o;
  var word = fe77_freshWord(fe77_delayOf(tk, o), o.status);
  if (!word) return o;
  if (word === "LIVE") {
    o.status = "live";
    o.label = "LIVE";
    o.fe64Note = "LIVE";
  } else {
    o.status = "delayed";
    o.label = word;
    o.fe64Note = word;
  }
  if (!o.detail || /delayed|live|synth/i.test(String(o.detail))) o.detail = word;
  return o;
}
function fe77_qaCss() {
  try {
    if (document.getElementById("fe77-qa")) return;
    var st = document.createElement("style");
    st.id = "fe77-qa";
    st.textContent = [
      ".fe71 .more-nav-panel{scroll-padding-top:0!important}",
      ".fe71-grp h3{scroll-margin-top:0!important}",
      ".fe76-dot{white-space:pre}",
      "@media (max-width:767px){.fe68-ins .institutional-row,.fe68-ins .fe76-ins{display:block!important;grid-template-columns:none!important;padding:10px 0}.fe68-ins .fe76-ins strong,.fe68-ins .institutional-row strong{display:inline}.fe68-ins .fe76-role{display:inline;margin-left:6px}.fe68-ins .fe76-ins strong~.fe76-role~span,.fe68-ins .fe76-ins small,.fe68-ins .institutional-row small{display:block;margin-top:2px}}",
      "#term-ins-root,#anlz-ins-root,.fe68-ins{height:auto!important;min-height:0!important;padding-bottom:0!important;flex:0 0 auto!important}",
      "@media (min-width:768px){.panel.p-expanded{bottom:auto!important;height:auto!important}.panel.p-expanded .panel-body{flex:0 0 auto!important;height:auto!important}html body.fe68-lenses .panel.p-expanded{bottom:0!important}}",
      "html body.fe68-lenses #p2body{padding-bottom:12px!important}",
      "html body.fe68-lenses .panel.p-expanded{z-index:96!important}",
      "#fe76-lens-bd{z-index:90!important}",
      "@media (min-width:768px){.cmd-bar{display:flex!important;flex-wrap:nowrap!important;align-items:center!important;min-width:0}.cmd-bar .cmd-ac-wrap,.cmd-bar [data-fe70-ask],.cmd-bar #cmdAuthBtn{position:static!important;top:auto!important;right:auto!important;left:auto!important;bottom:auto!important}}",
      "html.fe77-dash,html.fe77-dash body{overflow:hidden!important}",
      "html.fe77-dash .sidebar{position:fixed!important;top:0!important;left:0!important;height:100vh!important;max-height:100vh!important;z-index:80!important}",
      "html.fe77-dash #dashOv.term-overlay{padding-top:0!important}",
      ".fe77-sk{display:inline-block;min-width:4.6em;height:0.9em;border-radius:4px;vertical-align:middle;background:linear-gradient(90deg,var(--b3,#1c1e24),var(--b2,#2a2d36),var(--b3,#1c1e24));background-size:200% 100%;animation:fe77sk 1.1s linear infinite}",
      "@keyframes fe77sk{0%{background-position:100% 0}100%{background-position:-100% 0}}"
    ].join("");
    document.head.appendChild(st);
  } catch (e) {}
}
try { fe77_qaCss(); } catch (e) {}

var fe77_lensY = 0;
var fe77_lensPrev = "ov";
function fe77_closeLens() {
  var y = fe77_lensY || 0;
  var prev = fe77_lensPrev || "ov";
  try { document.body.classList.remove("fe68-lenses"); } catch (e) {}
  try {
    document.body.style.overflow = "";
    document.documentElement.style.overflow = "";
    document.body.style.position = "";
    document.documentElement.style.position = "";
  } catch (e2) {}
  try { var bd = document.getElementById("fe76-lens-bd"); if (bd) bd.remove(); } catch (e3) {}
  try { if (window.fe76_lensIv) { clearInterval(window.fe76_lensIv); window.fe76_lensIv = 0; } } catch (e4) {}
  try { if (typeof aTab !== "undefined") aTab = prev; } catch (e5) {}
  try { window.scrollTo(0, y); } catch (e6) {}
  try { if (typeof renderP2 === "function") renderP2(); } catch (e7) {}
}
function fe77_lensPlace() {
  var wide = false, on = false;
  try { wide = window.innerWidth >= 768; } catch (e) {}
  try { on = document.body.classList.contains("fe68-lenses"); } catch (e2) {}
  var bd = null;
  try { bd = document.getElementById("fe76-lens-bd"); } catch (e3) {}
  if (!wide || !on) {
    if (bd) bd.remove();
    try { if (!on) document.body.style.overflow = ""; } catch (e4) {}
    return;
  }
  if (!bd) {
    bd = document.createElement("div");
    bd.id = "fe76-lens-bd";
    document.body.appendChild(bd);
  }
}
try { fe76_closeLens = fe77_closeLens; } catch (e) {}
try { fe76_lensPlace = fe77_lensPlace; } catch (e) {}
try {
  var fe77_tab1 = _setATab;
  _setATab = function (t) {
    if (t === "cm") {
      try { fe77_lensY = window.scrollY || window.pageYOffset || 0; } catch (e) { fe77_lensY = 0; }
      try {
        if (typeof aTab !== "undefined" && aTab && aTab !== "cm") fe77_lensPrev = aTab;
      } catch (e2) {}
    }
    return fe77_tab1.apply(this, arguments);
  };
} catch (e) {}

function fe77_dashLock() {
  var on = false;
  try { var dash = document.getElementById("dashOv"); on = !!(dash && dash.isConnected); } catch (e) {}
  try { document.documentElement.classList.toggle("fe77-dash", on); } catch (e2) {}
  if (!on) return;
  try { var el = document.getElementById("dashOv"); if (el) el.style.paddingTop = "0px"; } catch (e3) {}
  try { window.scrollTo(0, 0); } catch (e4) {}
}
try {
  var fe77_ov0 = _showOverlay;
  _showOverlay = function () {
    var r = fe77_ov0.apply(this, arguments);
    try { fe77_dashLock(); if (typeof fe76_fitAsk === "function") fe76_fitAsk(); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe77_nav1 = nav;
  nav = function () {
    var r = fe77_nav1.apply(this, arguments);
    try { fe77_dashLock(); if (typeof fe76_fitAsk === "function") fe76_fitAsk(); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  if (typeof ResizeObserver === "function") {
    var fe77_ro = new ResizeObserver(function () { try { if (typeof fe76_fitAsk === "function") fe76_fitAsk(); fe77_dashLock(); } catch (e) {} });
    var fe77_watch = function () {
      var bar = document.querySelector(".cmd-bar");
      var auth = document.getElementById("cmdAuthBtn");
      if (bar) fe77_ro.observe(bar);
      if (auth) fe77_ro.observe(auth);
    };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fe77_watch);
    else fe77_watch();
    setTimeout(fe77_watch, 800);
    setTimeout(fe77_watch, 2500);
  }
} catch (e) {}

try {
  var fe77_hasNext0 = fe69_hasNext;
  fe69_hasNext = function (win) {
    if (win && win.next != null && String(win.next).trim() !== "" && String(win.next) !== "[object Object]") return true;
    try { return !!fe77_hasNext0.apply(this, arguments); } catch (e) { return false; }
  };
} catch (e) {}

try {
  var fe77_lbl0 = fe65_feedLbl;
  fe65_feedLbl = function (d, tk) {
    var word = fe77_freshWord(fe77_delayOf(tk, d), d && d.status);
    if (word) return word === "LIVE" ? "LIVE" : word;
    return fe77_lbl0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_qm1 = _quoteMeta;
  _quoteMeta = function (tk) {
    var o = fe77_qm1.apply(this, arguments);
    try { o = fe77_applyFresh(tk, o); } catch (e) {}
    try {
      if (tk === "DXY" && o) {
        if (fe77_dxyFallback || o.label === "SYNTH·DXY") {
          if (fe77_dxyFallback) {
            o.status = "proxy";
            o.label = "FX BASKET";
            o.detail = "Dispatch FX basket";
          } else if (o.label === "SYNTH·DXY") {
            o.label = "DELAYED";
            o.detail = fe77_dxyName();
            if (o.status === "proxy") o.status = "delayed";
          }
        }
      }
    } catch (e2) {}
    return o;
  };
} catch (e) {}
try {
  var fe77_bit0 = fe66_chartBit;
  fe66_chartBit = function (tk, range, meta) {
    try { if (meta) fe77_applyFresh(tk, meta); } catch (e) {}
    var bit = fe77_bit0.apply(this, arguments);
    try {
      var word = fe77_freshWord(fe77_delayOf(tk, meta), meta && meta.status);
      if (word && tk) {
        bit = String(bit).replace(/●\s*LIVE|LIVE·YS|delayed(?:\s+\d+\s*min)?|DELAYED(?:\s+\d+m)?/gi, word === "LIVE" ? "LIVE" : word);
      }
    } catch (e2) {}
    return bit;
  };
} catch (e) {}

try {
  var fe77_res0 = resolveInternalTicker;
  resolveInternalTicker = function (raw) {
    var fx = fe77_fxKey(raw);
    if (fx) return fx;
    return fe77_res0.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_aq1 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q) {
    var fx = fe77_fxKey(tk);
    if (fx && fx !== tk) {
      try { if (typeof liveSymbols !== "undefined" && liveSymbols.delete) liveSymbols.delete(tk); } catch (e) {}
      tk = fx;
    }
    var px = NaN;
    try { px = Number(q && (q.p != null ? q.p : q.price)); } catch (e2) { px = NaN; }
    if (!(px > 0)) return false;
    var prev = NaN, avail = null;
    try { prev = Number(q && (q.prev != null ? q.prev : q.prevClose)); } catch (e3) {}
    try { if (q && q.changeAvailable != null) avail = q.changeAvailable; } catch (e4) {}
    if (!(prev > 0) && avail !== true) {
      var copy = {};
      try { copy = fe77_copy(q); } catch (e5) { copy = q; }
      try { delete copy.c; delete copy.change; delete copy.changePct; copy.noBasePrev = true; } catch (e6) {}
      return fe77_aq1.call(this, tk, copy, arguments[2]);
    }
    return fe77_aq1.call(this, tk, q, arguments[2]);
  };
} catch (e) {}
try {
  var fe77_fp1 = fp;
  fp = function (tk) {
    var d = fe77_fp1.apply(this, arguments);
    if (!d) return d;
    var px = NaN, prev = NaN;
    try { px = Number(P[tk] && P[tk].p); } catch (e) {}
    try { prev = Number(BASE[tk] && BASE[tk].p); } catch (e2) {}
    var avail = null;
    try { avail = liveQuoteChangeAvailable[tk]; } catch (e3) {}
    if (!(px > 0) || (px === 0)) {
      d.p = "—";
      d.c = "";
      d.chg = "";
      d.fe77sk = 1;
      return d;
    }
    if (!(prev > 0) && avail === false) {
      d.c = "";
      d.chg = "";
    }
    return d;
  };
} catch (e) {}

try {
  var fe77_chg1 = fe73_chgLine;
  fe73_chgLine = function () {
    var out = fe77_chg1.apply(this, arguments);
    out = String(out == null ? "" : out);
    if (/opens\b|\bUK\b|\d{1,2}:\d{2}/.test(out)) out = out.replace(/\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$/i, "");
    return out;
  };
  fe66_chgLine = fe73_chgLine;
} catch (e) {}
try {
  var fe77_html1 = fe71_sheetHtml;
  fe71_sheetHtml = function () {
    var html = fe77_html1.apply(this, arguments);
    return String(html).replace(/<span class="fe76-dot">[\s\S]*?<\/span>/g, '<span class="fe76-dot">\u00a0·\u00a0</span>');
  };
} catch (e) {}
try {
  var fe77_stance0 = _rt20Stance;
  _rt20Stance = function (b) {
    var raw = "";
    try { raw = String(fe77_stance0.apply(this, arguments) || ""); } catch (e) { raw = ""; }
    var when = Date.now();
    try { when = Date.parse((b && (b.date || b.generatedAt || b.asOf || b.createdAt)) || "") || Date.now(); } catch (e2) { when = Date.now(); }
    var hour = fe77_ukHour(Date.now());
    var edition = null;
    try { edition = (b && (b.edition || null)) || (typeof fe76_edition !== "undefined" ? fe76_edition : null); } catch (e3) {}
    var title = fe77_briefTitle(edition || b, hour);
    var date = fe77_ukStamp(when);
    if (edition && (edition.label || (edition.lead && edition.lead.label))) return title + (date ? " · " + date : "");
    raw = raw.replace(/\bMorning\b/g, fe77_dayPart(hour));
    if (date && raw.indexOf(date) < 0) raw = raw + " · " + date;
    return raw;
  };
} catch (e) {}

var fe77_chatDead = 0;
function fe77_chatScrubStores() {
  try {
    var lk = Object.keys(localStorage);
    var i;
    for (i = 0; i < lk.length; i++) if (/^td_chat/.test(lk[i]) && lk[i] !== "td_chat_v") localStorage.removeItem(lk[i]);
  } catch (e) {}
  try {
    var sk = Object.keys(sessionStorage);
    var j;
    for (j = 0; j < sk.length; j++) if (/^td_chat/.test(sk[j])) sessionStorage.removeItem(sk[j]);
  } catch (e2) {}
  try { localStorage.removeItem("td_chat"); } catch (e3) {}
  try { sessionStorage.removeItem("td_chat"); } catch (e4) {}
}
function fe77_chatInstallEmpty() {
  var bucket = [];
  _chatMsgs = new Proxy(bucket, {
    get: function (t, p) {
      if (p === "push" || p === "unshift" || p === "splice" || p === "pop" || p === "shift") {
        return function () {
          if (fe77_chatDead) return p === "splice" ? [] : t.length;
          return Array.prototype[p].apply(t, arguments);
        };
      }
      var v = t[p];
      return typeof v === "function" ? v.bind(t) : v;
    },
    set: function (t, p, v) {
      if (fe77_chatDead) {
        if (p === "length" && !(Number(v) > 0)) t.length = 0;
        return true;
      }
      t[p] = v;
      return true;
    }
  });
}
function fe77_chatWipeAll() {
  fe77_chatDead = 1;
  try { fe76_chatGen = (typeof fe76_chatGen === "number" ? fe76_chatGen : 0) + 1; fe76_chatSeal = fe76_chatGen; } catch (e) {}
  try { _chatLoad = false; } catch (e2) {}
  try { clearInterval(_chatStatusIv); _chatStatusIv = null; _chatStatus = ""; } catch (e3) {}
  try { clearTimeout(fe76_saveT); } catch (e4) {}
  try { fe76_skipRender = 0; } catch (e5) {}
  fe77_chatScrubStores();
  fe77_chatInstallEmpty();
  fe77_chatScrubStores();
  try { var inp = document.getElementById("chatInp"); if (inp) inp.value = ""; } catch (e6) {}
  try { var el = document.getElementById("chatMsgs"); if (el) el.innerHTML = ""; } catch (e7) {}
  try { if (typeof _renderChatMsgs === "function") _renderChatMsgs(); } catch (e8) {}
}
function fe77_chatGuard() {
  if (!fe77_chatDead) return;
  var dirty = false;
  try { dirty = !_chatMsgs || _chatMsgs.length > 0; } catch (e) { dirty = true; }
  if (dirty) fe77_chatInstallEmpty();
  fe77_chatScrubStores();
  try {
    var inp = document.getElementById("chatInp");
    if (inp && inp.value === "What matters most in markets right now?") inp.value = "";
  } catch (e2) {}
  try {
    var el = document.getElementById("chatMsgs");
    if (el && el.querySelector(".chat-msg.user, .chat-msg.bot")) {
      if (typeof _renderChatMsgs === "function") _renderChatMsgs();
    }
  } catch (e3) {}
}
try { clearChat = function () { fe77_chatWipeAll(); }; } catch (e) {}
try {
  var fe77_read1 = fe73_chatRead;
  fe73_chatRead = function () {
    if (fe77_chatDead) { fe77_chatGuard(); return; }
    var r = fe77_read1.apply(this, arguments);
    try { if (fe77_chatDead) fe77_chatGuard(); } catch (e) {}
    return r;
  };
} catch (e) {}
try {
  var fe77_tg1 = toggleChat;
  toggleChat = function () {
    if (fe77_chatDead) fe77_chatGuard();
    var r = fe77_tg1.apply(this, arguments);
    if (fe77_chatDead) fe77_chatGuard();
    return r;
  };
} catch (e) {}
try {
  var fe77_os1 = openSettings;
  openSettings = function () {
    if (fe77_chatDead) fe77_chatGuard();
    var r = fe77_os1.apply(this, arguments);
    if (fe77_chatDead) fe77_chatGuard();
    return r;
  };
} catch (e) {}
try {
  var fe77_ask1 = (typeof fe69_openAsk === "function") ? fe69_openAsk : _openResearchAssistant;
  fe69_openAsk = function (question) {
    if (question === "What matters most in markets right now?") question = "";
    var r = fe77_ask1.call(this, question);
    if (fe77_chatDead) fe77_chatGuard();
    return r;
  };
  _openResearchAssistant = fe69_openAsk;
} catch (e) {}
try {
  document.addEventListener("focusin", function (ev) {
    var t = ev && ev.target;
    if (!t || t.id !== "chatInp") return;
    if (fe77_chatDead) fe77_chatGuard();
  }, true);
  document.addEventListener("focusout", function (ev) {
    var t = ev && ev.target;
    if (!t || t.id !== "chatInp") return;
    if (fe77_chatDead) fe77_chatGuard();
  }, true);
} catch (e) {}
try {
  var fe77_get1 = Storage.prototype.getItem;
  Storage.prototype.getItem = function (key) {
    if (fe77_chatDead && String(key) === "td_chat" && (this === window.localStorage || this === window.sessionStorage)) return null;
    return fe77_get1.apply(this, arguments);
  };
} catch (e) {}
try {
  var fe77_send1 = sendChatMessage;
  sendChatMessage = function (retryText) {
    if (retryText == null) {
      var text = "";
      try { text = String((document.getElementById("chatInp") || {}).value || "").trim(); } catch (e) {}
      if (!text) return;
      fe77_chatDead = 0;
    } else fe77_chatDead = 0;
    return fe77_send1.apply(this, arguments);
  };
} catch (e) {}
