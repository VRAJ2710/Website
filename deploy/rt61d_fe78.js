// ── rt61d ──
// FE78_PURE_START
var fe78_meta = fe78_meta || Object.create(null);
function fe78_bag(tk) {
  if (!fe78_meta) fe78_meta = Object.create(null);
  return fe78_meta[tk] || null;
}
function fe78_esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function fe78_opinion(s) {
  return /\b(justified|catalyst|bullish|bearish|upside|downside|accelerat|headwind|overweight|underweight|valuation|narrative|intact|weighing|beneficiary|dominant|buy|sell|avoid|moat)\b/i.test(String(s || ""));
}
function fe78_about(a) {
  if (!a || typeof a !== "object") return "";
  var th = String(a.th == null ? "" : a.th).trim();
  if (!th || th === "undefined" || th === "None" || th === "null") return "";
  if (fe78_opinion(th)) return "";
  return th;
}
function fe78_isCrypto(tk) {
  var b = fe78_bag(tk);
  if (b && b.baseline === "24h") return true;
  var s = String(tk || "").toUpperCase().replace(/=X$/, "").replace(/-USD$/, "");
  if (/^(BTC|ETH|SOL|XRP|DOGE|ADA|AVAX|LINK|DOT|LTC|UNI|POL|NEAR|ALGO|HBAR|TON|BCH|XLM|FIL|APT|SUI|SHIB|PEPE|ATOM|INJ|BNB|TRX|MATIC)$/.test(s)) return true;
  try { if (typeof TICKER_CATS !== "undefined" && TICKER_CATS[s] === "cry") return true; } catch (e) {}
  try { if (typeof _rtIsCrypto === "function" && _rtIsCrypto(s)) return true; } catch (e2) {}
  return false;
}
function fe78_cryptoBasis(q, roll, now) {
  var fin = function (v) { return typeof v === "number" && isFinite(v); };
  var fresh = !!(roll && (now - roll.at) < 30 * 60 * 1000);
  var raw = q && (q.changePct != null ? q.changePct : q.c);
  var c = Number(raw);
  var hasC = raw != null && raw !== "" && isFinite(c);
  if (q && q.baseline === "24h") {
    return { mode: "srv", kind: "srv24", c: hasC ? c : null, prev: fin(q.prev) && q.prev > 0 ? q.prev : null };
  }
  if (fresh && roll.kind === "srv24") {
    return {
      mode: "keep",
      c: roll.c != null && isFinite(Number(roll.c)) ? Number(roll.c) : null,
      prev: fin(roll.prev) && roll.prev > 0 ? roll.prev : null
    };
  }
  return { mode: "client" };
}
function fe78_take(tk, q) {
  if (!tk || !q || typeof q !== "object") return null;
  var b = fe78_meta[tk] || (fe78_meta[tk] = {});
  if (Object.prototype.hasOwnProperty.call(q, "baseline")) b.baseline = q.baseline ? String(q.baseline) : "";
  var feed = q.feed && typeof q.feed === "object" ? q.feed : null;
  if (q.changeDay || (feed && feed.changeDay)) b.changeDay = String(q.changeDay || feed.changeDay);
  if (q.changeDayLabel || (feed && feed.changeDayLabel)) b.changeDayLabel = String(q.changeDayLabel || feed.changeDayLabel);
  if (Object.prototype.hasOwnProperty.call(q, "prevNote")) b.prevNote = q.prevNote ? String(q.prevNote) : "";
  var fl = q.feedLabel || (feed && (feed.feedLabel || feed.label)) || "";
  if (q.feedLabel || (feed && (feed.feedLabel || feed.label))) b.feedLabel = String(fl);
  if (q.baseline === "24h") {
    var raw = q.changePct != null ? q.changePct : q.c;
    var c = Number(raw);
    b.srvC = raw != null && isFinite(c) ? c : null;
  }
  if (q.nextOpen != null && q.nextOpen !== "") b.nextOpen = q.nextOpen;
  else if (q.feed && q.feed.nextOpen) b.nextOpen = q.feed.nextOpen;
  if (q.status) b.status = String(q.status);
  if (q.marketOpen === false || q.marketOpen === true) b.marketOpen = q.marketOpen;
  if (q.note) b.note = String(q.note);
  return b;
}
function fe78_dayTag(tk) {
  var b = fe78_bag(tk);
  if (!b) return "";
  if (b.changeDay) return String(b.changeDay).trim();
  var d = String(b.changeDayLabel || "").trim();
  var m = d.match(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/i);
  return m ? m[1] : "";
}
function fe78_isZero(s) {
  var t = String(s || "");
  if (!/%/.test(t)) return false;
  var parts = t.split("%");
  var i;
  for (i = 0; i < parts.length - 1; i++) {
    var bit = parts[i].replace(/[()↑↓▲▼•\s]/g, "");
    var m = bit.match(/[+\-]?(\d+(?:\.\d+)?)$/);
    if (m && Number(m[1]) === 0) return true;
  }
  return false;
}
function fe78_chgText(tk, s) {
  s = String(s == null ? "" : s);
  if (!s || s === "—" || s === "-" || /undefined|null/.test(s)) return "—";
  if (fe78_isZero(s)) return "—";
  s = s.replace(/\s*[·•]\s*[^·•]*\bmarket closed\b[^·•]*/ig, " ");
  s = s.replace(/\s{2,}/g, " ").trim();
  var tail = "";
  if (fe78_isCrypto(tk)) {
    if (!/\b24h\b/.test(s)) tail += " 24h";
  } else {
    var day = fe78_dayTag(tk);
    s = s.replace(/\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s+\d{1,2}\s+[A-Za-z]{3})?(?:\s+\d{4})?(?=\s*(?:[·•]|$))/gi, "");
    s = s.replace(/\s*[·•]\s*$/g, "").trim();
    if (day && s.indexOf(day) < 0) tail += " " + day;
  }
  var note = fe78_bag(tk) && fe78_bag(tk).prevNote;
  if (note && s.indexOf(String(note)) < 0) tail += " · " + note;
  return s + tail;
}
function fe78_chgHtml(tk, s) {
  var plain = fe78_chgText(tk, s);
  if (plain === "—") return "—";
  var note = fe78_bag(tk) && fe78_bag(tk).prevNote;
  if (!note) return fe78_esc(plain);
  var i = plain.lastIndexOf(String(note));
  if (i < 0) return fe78_esc(plain);
  return fe78_esc(plain.slice(0, i)) + '<span class="fe78-note">' + fe78_esc(note) + "</span>" + fe78_esc(plain.slice(i + String(note).length));
}
function fe78_quoteLabel(q, displayName) {
  q = q || {};
  var sym = String(q.symbol || q.ticker || q.tk || "").toUpperCase().replace(/=X$/, "").replace(/-USD$/, "");
  var gold = sym === "XAU" || sym === "GC=F" || sym === "GOLD";
  var label = q.label != null ? String(q.label).trim() : "";
  if (label && !(/^gold spot$/i.test(label) && !gold)) return label;
  var name = String(displayName || "").trim();
  if (!name && q.name && !(/^gold spot$/i.test(String(q.name)) && !gold)) name = String(q.name).trim();
  if (name && !(/^gold spot$/i.test(name) && !gold)) return name;
  if (gold) return label || "Gold spot";
  return sym || "";
}
function fe78_quotePx(q, n) {
  var label = String((q && q.label) || "");
  var sym = String((q && (q.symbol || q.ticker)) || "").toUpperCase().replace(/=X$/, "");
  var fx = label.indexOf("/") >= 0 || /^(EUR|GBP|USD|JPY|AUD|CAD|CHF|NZD|CNH|CNY)[A-Z]{3}$/.test(sym);
  var px = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return fx ? px : "$" + px;
}
function fe78_quoteLine(meta, displayName) {
  var q = null;
  if (meta && typeof meta === "object" && meta.quote && typeof meta.quote === "object") q = meta.quote;
  else if (meta && typeof meta === "object" && (meta.quoteLine || meta.price != null || meta.label || meta.symbol)) q = meta;
  if (!q) return "";
  var verbatim = q.quoteLine != null ? String(q.quoteLine).trim() : "";
  if (verbatim) return verbatim;
  var label = fe78_quoteLabel(q, displayName);
  if (!label) return "";
  var n = Number(q.price != null ? q.price : (q.px != null ? q.px : q.last));
  var px = isFinite(n) ? fe78_quotePx(q, n) : "";
  var tail = "";
  var cash = q.change != null && q.change !== "" ? Number(q.change) : NaN;
  var raw = q.changePct != null ? q.changePct : q.c;
  var pct = raw != null && raw !== "" && isFinite(Number(raw)) ? Number(raw) : NaN;
  var crypto = q.baseline === "24h" || fe78_isCrypto(q.symbol || q.ticker || "");
  if (isFinite(cash) && cash !== 0) {
    tail += " " + (cash > 0 ? "+" : "") + cash.toFixed(2);
    if (isFinite(pct) && pct !== 0) tail += " (" + (pct > 0 ? "+" : "") + pct.toFixed(2) + "%)";
    if (crypto) tail += " 24h";
  } else if (isFinite(pct) && pct !== 0) {
    tail += " " + (pct > 0 ? "+" : "") + pct.toFixed(2) + "%";
    if (crypto) tail += " 24h";
    else if (q.changeDay) tail += " " + q.changeDay;
  }
  if (!(isFinite(cash) && cash !== 0) && q.prevNote) tail += " · " + q.prevNote;
  var asOf = q.asOfUk ? (" · " + q.asOfUk) : "";
  if (!px && !tail && !asOf) return "";
  return label + (px ? " " + px : "") + tail + asOf;
}
function fe78_academyKeep(j) {
  return !!(j && typeof j === "object" && Array.isArray(j.items));
}
function fe78_academyNote(j, today) {
  if (!j || typeof j !== "object") return null;
  var edition = j.edition != null ? String(j.edition).trim().toLowerCase() : "";
  var label = j.label != null ? String(j.label).trim() : "";
  var dateLabel = j.dateLabel != null ? String(j.dateLabel).trim() : "";
  var nextRaw = j.nextRunUk != null ? String(j.nextRunUk).trim() : "";
  var has = !!(edition || label || dateLabel || j.stale != null || nextRaw);
  if (has) {
    var nextLine = "";
    if (nextRaw) {
      var m = nextRaw.match(/\d{1,2}:\d{2}/);
      var hm = m ? m[0] : nextRaw.replace(/\s*UK\s*$/i, "").trim();
      if (/^\d:\d{2}$/.test(hm)) hm = "0" + hm;
      nextLine = "Next set due " + hm + (/\bUK\b/.test(hm) ? "" : " UK");
    }
    var parts = [];
    if (label) parts.push(label);
    if (dateLabel && parts.join(" ").indexOf(dateLabel) < 0) parts.push(dateLabel);
    if (nextLine) parts.push(nextLine);
    if (!parts.length) {
      parts.push(edition === "yesterday" ? "Yesterday's set" : edition === "older" ? "An earlier set" : "Today's set");
    }
    return { text: parts.join(" · "), amber: j.stale === true };
  }
  var date = j.date != null ? String(j.date).trim() : "";
  if (!date || (today && date === String(today))) return null;
  return { text: "From " + date, amber: false };
}
function fe78_academyStore(box, j, today) {
  var out = box && typeof box === "object" ? box : {};
  var note = fe78_academyNote(j, today);
  if (note) out.note = note;
  else delete out.note;
  return out;
}
function fe78_regimeCol(score) {
  var n = Number(score);
  if (!(n >= 72)) {
    if (n >= 55) return "var(--gd)";
    if (n >= 40) return "var(--bl)";
    if (isFinite(n)) return "var(--rd)";
    return "var(--gd)";
  }
  return "var(--gn)";
}
function fe78_regimeFrom(raw, local) {
  var srv = null;
  if (raw && typeof raw === "object" && raw.localEstimate !== true) {
    var label = String(raw.regime || raw.label || "").trim();
    var score = raw.score != null && raw.score !== "" ? Number(raw.score) : NaN;
    if (label || isFinite(score)) {
      var asOfUk = raw.asOfUk ? String(raw.asOfUk).trim() : "";
      if (!asOfUk && raw.asOf) asOfUk = fe78_ukStamp(raw.asOf);
      if (!label) {
        if (score >= 72) label = "Risk-On (Strong)";
        else if (score >= 55) label = "Risk-On (Fragile)";
        else if (score >= 40) label = "Transition";
        else label = "Risk-Off";
      }
      srv = { label: label, score: isFinite(score) ? score : (local && local.score), asOf: raw.asOf || "", asOfUk: asOfUk };
    }
  }
  if (srv) {
    var out = {};
    var base = local && typeof local === "object" ? local : {};
    for (var k in base) out[k] = base[k];
    out.label = srv.label;
    out.score = srv.score;
    out.asOf = srv.asOf;
    out.asOfUk = srv.asOfUk;
    out.localEstimate = false;
    out.loading = false;
    out._hide = false;
    out.col = fe78_regimeCol(srv.score);
    return out;
  }
  if (!local || typeof local !== "object") return local || null;
  if (local.loading) return local;
  var copy = {};
  for (var k2 in local) copy[k2] = local[k2];
  var lab = String(copy.label || "");
  if (lab && lab.indexOf("Dispatch local estimate") < 0) copy.label = lab + " · Dispatch local estimate";
  copy.localEstimate = true;
  return copy;
}
function fe78_regimeTitle(re) {
  re = re || {};
  var bits = [];
  if (re.label) bits.push(String(re.label));
  if (re.score != null && re.score !== "" && !re.loading) bits.push(re.score + "/100");
  var title = bits.join(" · ") || "Market regime";
  if (re.localEstimate && title.indexOf("Dispatch local estimate") < 0) title += " · Dispatch local estimate";
  if (!re.localEstimate && re.asOfUk) title += " · " + re.asOfUk;
  return title;
}
function fe78_regimeSub(re) {
  re = re || {};
  if (re.loading) return re._hide ? "" : "Regime: loading…";
  var core = (re.label || "regime") + (re.score != null && !re.loading ? " " + re.score + "/100" : "");
  if (re.localEstimate) return core;
  if (re.asOfUk) return "current regime " + core + " · " + re.asOfUk;
  return "current regime " + core;
}
function fe78_briefBits(b) {
  var empty = { label: "", dayLabel: "", name: "", text: "" };
  if (!b || typeof b !== "object") return empty;
  var ed = b.edition && typeof b.edition === "object" ? b.edition : null;
  var label = String((ed && ed.label) || b.label || b.editionLabel || "").trim();
  var day = String((ed && ed.dayLabel) || b.dayLabel || b.dateLabel || "").trim();
  var name = String((ed && ed.name) || b.name || "").trim();
  var text = label || (day && name ? (day + " · " + name) : (name || day || ""));
  return { label: label, dayLabel: day, name: name, text: text };
}
function fe78_sourceTitle(s) {
  if (s == null || s === "") return "";
  if (typeof s === "string") return s;
  if (typeof s === "object") return String(s.title || s.label || s.name || "");
  return "";
}
function fe78_badgeText(feedLabel, feed) {
  if (feedLabel != null && String(feedLabel).trim()) {
    var s = String(feedLabel).trim();
    try {
      if (typeof fe65_scrub === "function") {
        var cleaned = fe65_scrub(s);
        if (cleaned) s = String(cleaned);
      }
    } catch (e) {}
    return s;
  }
  if (feed && typeof feed === "object") {
    if (feed.label) return String(feed.label);
    try {
      if (typeof fe76_feedLabel === "function") {
        var t = fe76_feedLabel(feed);
        if (t) return String(t);
      }
    } catch (e2) {}
  }
  return "";
}
function fe78_venueName(tk) {
  var t = String(tk || "").toUpperCase();
  if (/\.HK$/.test(t) || t === "HSI" || t === "^HSI" || t === "9988.HK") return "Hong Kong";
  if (/\.T$/.test(t) || t === "N225" || t === "^N225") return "Tokyo";
  if (/\.(SS|SZ)$/.test(t) || t === "SSEC" || t === "000001.SS") return "Shanghai";
  if (/\.KS$/.test(t) || t === "KOSPI" || t === "^KS11") return "Seoul";
  if (/\.NS$/.test(t) || t === "NSEI" || t === "^NSEI") return "India";
  if (/\.L$/.test(t) || t === "FTSE" || t === "^FTSE") return "London";
  if (/\.AX$/.test(t) || t === "ASX200") return "Sydney";
  if (/\.DE$/.test(t) || t === "DAX") return "Frankfurt";
  if (/\.PA$/.test(t) || t === "CAC") return "Paris";
  if (/\.TO$/.test(t)) return "Toronto";
  if (/\.TW$/.test(t)) return "Taipei";
  return "";
}
function fe78_ukStamp(v) {
  var ms = typeof v === "number" ? v : Date.parse(v || "");
  if (typeof v === "string" && /^\d{11,}$/.test(v)) ms = Number(v);
  if (!isFinite(ms) || ms <= 0) return "";
  if (ms < 1e11) ms *= 1000;
  try {
    var d = new Date(ms);
    var wd = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(d);
    var day = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", day: "numeric", month: "short" }).format(d);
    var parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d);
    var h = "", mi = "";
    parts.forEach(function (p) { if (p.type === "hour") h = p.value; if (p.type === "minute") mi = p.value; });
    if (h.length === 1) h = "0" + h;
    if (!wd || !day || !h || !mi) return "";
    return wd + " " + day + ", " + h + ":" + mi + " UK";
  } catch (e) { return ""; }
}
function fe78_closedLine(tk, nextOpen) {
  var venue = fe78_venueName(tk);
  if (!venue) return "";
  var stamp = fe78_ukStamp(nextOpen);
  return venue + " market closed" + (stamp ? " · opens " + stamp : "");
}
function fe78_tidyStatus(s, tk, nextOpen) {
  var closed = tk ? fe78_closedLine(tk, nextOpen) : "";
  if (closed) return closed;
  var text = String(s || "");
  return text.replace(/(\d{1,2}:\d{2}\s*UK)\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s+\d{1,2}\s+[A-Za-z]{3})?(?:\s+\d{4})?/gi, "$1");
}
function fe78_cryptoLine(tk, px) {
  var b = fe78_bag(tk);
  if (!b || b.baseline !== "24h" || b.srvC == null || !isFinite(Number(b.srvC)) || Number(b.srvC) === 0) return "";
  var c = Number(b.srvC);
  var pct = (c > 0 ? "+" : "") + c.toFixed(2) + "%";
  var n = Number(px);
  if (!(n > 0)) return (c > 0 ? "\u2191 " : "\u2193 ") + pct + " 24h";
  var diff = n - n / (1 + c / 100);
  var abs = Math.abs(diff);
  var num = abs >= 1000 ? Math.round(abs).toLocaleString("en-US") : abs.toFixed(2);
  var sign = diff < 0 ? "-" : "+";
  var arrow = diff < 0 ? "\u2193 " : "\u2191 ";
  return arrow + sign + "$" + num + " (" + pct + ") 24h";
}
function fe78_askPrefill(subject) {
  var raw = String(subject == null ? "" : subject).replace(/\s+/g, " ").trim();
  raw = raw.replace(/\s+[—–-]\s+.*$/, "");
  raw = raw.replace(/\b(neutral(?:[-\s]?bull|-bear|\s+fit)?|bullish|bearish|headwind|regime-aligned|cautious)\b/ig, "");
  raw = raw.replace(/\s+/g, " ").replace(/^[\s—–\-]+|[\s—–\-]+$/g, "").trim();
  if (!raw || /^markets?(?:\s+right\s+now)?$/i.test(raw)) return "What matters most in markets right now?";
  return "What matters most for " + raw + " right now?";
}
function fe78_dxyLabel(serverLabel, ice, fallback) {
  if (fallback || !ice) return "Dispatch FX basket";
  var s = String(serverLabel || "").trim();
  if (s === "US Dollar Index (ICE)") return s;
  return "US Dollar Index (ICE)";
}
function fe78_deskScore(n) {
  if (n == null || n === "" || !isFinite(Number(n))) return "";
  return "Desk score " + Number(n) + "/100";
}
function fe78_zeroish(s) {
  var t = String(s || "");
  if (/\$0\.00\b/.test(t)) return true;
  if (/(?:^|[^\d.])\+?0\.00%/.test(t)) return true;
  if (/\+0\.00\b/.test(t)) return true;
  if (/\(\s*\+?0\.00\s*%?\s*\)/.test(t)) return true;
  return false;
}
function fe78_skel() {
  return '<span class="fe78-skel" aria-hidden="true"></span>';
}
// FE78_PURE_END

function fe78_displayName(sym, q) {
  var tk = String(sym || "").toUpperCase().replace(/=X$/, "").replace(/-USD$/, "");
  try {
    if (typeof A !== "undefined" && A && A.find) {
      var row = A.find(function (x) { return x && (x.tk === tk || x.tk === String(sym || "")); });
      if (row && row.nm) return row.nm;
    }
  } catch (e) {}
  try { if (typeof liveQuoteName !== "undefined" && liveQuoteName[tk]) return liveQuoteName[tk]; } catch (e2) {}
  if (q && q.name && !/^gold spot$/i.test(String(q.name))) return String(q.name);
  return tk;
}
function fe78_profileHtml(a, mode) {
  var tx = "";
  try { tx = typeof _rt24Th === "function" ? _rt24Th(a) : fe78_about(a); } catch (e) { tx = fe78_about(a); }
  tx = String(tx || "").trim();
  if (!tx || tx === "undefined" || tx === "None") return "";
  if (mode !== "full" && mode !== "th" && typeof _rt26Sent === "function") {
    try { tx = _rt26Sent(tx, mode === "ov" ? 200 : 140); } catch (e2) {}
  }
  tx = String(tx || "").trim();
  if (!tx || tx === "undefined") return "";
  var body = fe78_esc(tx);
  if (mode === "ov" || mode === "th") return '<div class="ap-thesis">' + body + "</div>";
  if (mode === "full") {
    return '<div class="gc" style="border-left:3px solid var(--bl)"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">PROFILE</div><div style="font-size:11.5px;color:var(--t2);line-height:1.6;margin-top:6px">' + body + "</div></div>";
  }
  return '<div class="gc"><div style="font-size:8px;color:var(--t3);font-family:var(--mn);letter-spacing:0.1em">PROFILE</div><div style="font-size:10.5px;color:var(--t2);line-height:1.55;margin-top:4px">' + body + "</div></div>";
}
function fe78_css() {
  try {
    if (typeof document === "undefined" || document.getElementById("fe78-css")) return;
    var st = document.createElement("style");
    st.id = "fe78-css";
    st.textContent = ".fe78-note{font-size:10px;color:var(--t3,#8b909a);font-weight:500;margin-left:4px}.fe78-acad{display:block;margin:8px 0 10px;padding:8px 10px;border-radius:8px;font-size:13px;line-height:1.45;color:var(--t2,#c8cdd6);background:rgba(255,255,255,.04);border:1px solid var(--b4,rgba(255,255,255,.08));white-space:normal;overflow-wrap:anywhere;max-width:100%;box-sizing:border-box}.fe78-acad-stale{color:#e0b15a;border-color:rgba(224,177,90,.45);background:rgba(224,177,90,.1)}.fe78-skel{display:inline-block;height:0.85em;min-width:4.8em;border-radius:4px;background:linear-gradient(90deg,rgba(255,255,255,.05),rgba(255,255,255,.16),rgba(255,255,255,.05));background-size:200% 100%;animation:fe78sh 1.1s ease-in-out infinite;vertical-align:-0.1em}@keyframes fe78sh{0%{background-position:100% 0}100%{background-position:-100% 0}}";
    document.head.appendChild(st);
  } catch (e) {}
}
try { fe78_css(); } catch (eCss) {}

try {
  var fe78_th0 = _rt24Th;
  _rt24Th = function (a) {
    var t = fe78_about(a);
    return t || "";
  };
  void fe78_th0;
} catch (eTh) {}
try {
  var fe78_live0 = _applyLiveQuote;
  _applyLiveQuote = function (tk, q, source) {
    try { fe78_take(tk, q); } catch (eT) {}
    var ok = fe78_live0.apply(this, arguments);
    try {
      if (typeof P !== "undefined" && P[tk]) {
        if (!(P[tk].p > 0)) { P[tk].p = null; P[tk].c = null; }
        else if (Number(P[tk].c) === 0) {
          P[tk].c = null;
          if (typeof liveQuoteChangeAvailable !== "undefined") liveQuoteChangeAvailable[tk] = false;
        }
      }
    } catch (eZ) {}
    return ok;
  };
} catch (eLive) {}
function fe78_priceReady(tk) {
  try {
    var p = (typeof P !== "undefined" && P[tk]) ? P[tk].p : null;
    if (!(typeof p === "number" && isFinite(p) && p > 0)) return false;
    if (typeof fe76_looksZero === "function" && fe76_looksZero(tk, p)) return false;
    return true;
  } catch (e) { return false; }
}
function fe78_changeReady(tk) {
  try {
    if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return false;
    var c = null;
    try { c = typeof liveChg === "function" ? liveChg(tk) : null; } catch (e1) { c = null; }
    if (c == null && typeof P !== "undefined" && P[tk] && typeof P[tk].c === "number") c = P[tk].c;
    return typeof c === "number" && isFinite(c) && c !== 0;
  } catch (e) { return false; }
}
function fe78_nextOpen(tk) {
  var b = fe78_bag(tk);
  if (b && b.nextOpen) return b.nextOpen;
  try {
    if (typeof fe70_bag === "function") {
      var bag = fe70_bag(tk);
      if (bag && bag.nextOpen) return bag.nextOpen;
    }
  } catch (e) {}
  try {
    if (typeof fe70_isHk === "function" && fe70_isHk(tk) && typeof fe70_hkBag === "function") {
      var hk = fe70_hkBag();
      if (hk && hk.nextOpen) return hk.nextOpen;
    }
  } catch (e2) {}
  try {
    var y = typeof fe64_yqBag === "function" ? fe64_yqBag(tk) : null;
    if (y && y.nextOpen) return y.nextOpen;
  } catch (e3) {}
  return "";
}
function fe78_isClosed(tk) {
  var b = fe78_bag(tk);
  if (b && (b.status === "closed" || b.marketOpen === false || /market closed/i.test(String(b.note || "")))) return true;
  try { if (typeof fe66_closedQuote === "function" && fe66_closedQuote(tk)) return true; } catch (e) {}
  try {
    var bag = typeof fe70_bag === "function" ? fe70_bag(tk) : null;
    if (bag && (bag.status === "closed" || bag.marketOpen === false || /market closed/i.test(String(bag.note || "")))) return true;
  } catch (e2) {}
  return false;
}
function fe78_status(tk, s) {
  if (!fe78_venueName(tk) || !fe78_isClosed(tk)) return fe78_tidyStatus(s, "", "");
  return fe78_tidyStatus(s || "", tk, fe78_nextOpen(tk));
}
try {
  var fe78_chg0 = fe66_chgLine;
  fe66_chgLine = function (tk) {
    try {
      var px = (typeof P !== "undefined" && P[tk]) ? P[tk].p : null;
      var forced = fe78_cryptoLine(tk, px);
      if (forced) return forced;
    } catch (eF) {}
    var out = "";
    try { out = fe78_chg0.apply(this, arguments); } catch (e) { out = ""; }
    var s = String(out == null ? "" : out);
    if (fe78_zeroish(s) || ((!s || s === "—" || /awaiting|no sync|syncing/i.test(s)) && !fe78_changeReady(tk))) return fe78_skel();
    s = fe78_chgText(tk, s);
    if (fe78_zeroish(s)) return fe78_skel();
    return s;
  };
  if (typeof fe73_chgLine === "function") fe73_chgLine = fe66_chgLine;
} catch (eChg) {}
try {
  var fe78_px0 = fe66_priceLine;
  fe66_priceLine = function (tk) {
    if (!fe78_priceReady(tk)) return fe78_skel();
    var out = "";
    try { out = fe78_px0.apply(this, arguments); } catch (e) { out = ""; }
    if (!out || out === "—" || fe78_zeroish(out) || /sync|NO LIVE/i.test(String(out))) return fe78_skel();
    return out;
  };
} catch (ePx) {}
try {
  fe76_quoteBlock = function (meta) {
    var q = meta && meta.quote;
    if (!q || typeof q !== "object" || Array.isArray(q)) return "";
    var sym = String(q.symbol || q.ticker || q.tk || "");
    var line = fe78_quoteLine({ quote: q }, fe78_displayName(sym, q));
    if (!line || /undefined/.test(line)) return "";
    if (q.quoteLine && String(q.quoteLine).trim()) return '<div class="fe76-qlines"><div class="fe76-qline">' + fe78_esc(line) + "</div></div>";
    var note = q.prevNote ? String(q.prevNote) : "";
    var html = fe78_esc(line);
    if (note && line.indexOf(note) >= 0) {
      var i = line.lastIndexOf(note);
      html = fe78_esc(line.slice(0, i)) + '<span class="fe78-note">' + fe78_esc(note) + "</span>" + fe78_esc(line.slice(i + note.length));
    }
    return '<div class="fe76-qlines"><div class="fe76-qline">' + html + "</div></div>";
  };
} catch (eQb) {}
try {
  fe77_quotePreview = function (meta) {
    var q = meta && meta.quote;
    if (!q) return "";
    return fe78_quoteLine(meta, fe78_displayName(q.symbol || q.ticker || "", q));
  };
} catch (eQp) {}
try {
  var fe78_title0 = fe77_briefTitle;
  fe77_briefTitle = function (edition, hour) {
    var bits = fe78_briefBits(edition);
    if (bits && bits.text) return bits.text;
    return fe78_title0.apply(this, arguments);
  };
} catch (eBt) {}
try {
  var fe78_st0 = _rt20Stance;
  _rt20Stance = function (b) {
    var bits = fe78_briefBits(b);
    if (bits && bits.text) return typeof fe77_kicker === "function" ? fe77_kicker(bits.text) : bits.text;
    return fe78_st0.apply(this, arguments);
  };
} catch (eSt) {}
try {
  var fe78_src0 = fe77_themeSource;
  fe77_themeSource = function (row) {
    var t = fe78_sourceTitle(row && row.source);
    if (t) return t;
    return fe78_src0.apply(this, arguments);
  };
} catch (eSrc) {}
try {
  var fe78_lbl0 = fe65_feedLbl;
  fe65_feedLbl = function (d, tk) {
    var b = fe78_bag(tk);
    var custom = b && b.feedLabel ? fe78_badgeText(b.feedLabel, null) : "";
    if (custom) return custom;
    return fe78_lbl0.apply(this, arguments);
  };
} catch (eLbl) {}
try {
  var fe78_fr0 = fe77_applyFresh;
  fe77_applyFresh = function (tk, o) {
    var out = fe78_fr0.apply(this, arguments);
    var b = fe78_bag(tk);
    var custom = b && b.feedLabel ? fe78_badgeText(b.feedLabel, null) : "";
    if (out && custom) { out.label = custom; out.fe64Note = custom; }
    return out;
  };
} catch (eFr) {}
try {
  var fe78_feed0 = fe66_feedLbl;
  fe66_feedLbl = function (d, tk) {
    var out = "";
    try { out = fe78_feed0.apply(this, arguments); } catch (e) { out = ""; }
    var line = fe78_status(tk, out);
    return line || out;
  };
} catch (eFeed) {}
try {
  var fe78_line0 = fe70_line;
  fe70_line = function (tk) {
    var out = "";
    try { out = fe78_line0.apply(this, arguments); } catch (e) { out = ""; }
    var line = fe78_status(tk, out);
    return line || out;
  };
} catch (eLine) {}
try {
  var fe78_sess0 = fe70_sess;
  fe70_sess = function (tk) {
    var row = { st: "", c: "" };
    try { row = fe78_sess0.apply(this, arguments) || row; } catch (e) {}
    if (row && fe78_isClosed(tk) && fe78_venueName(tk)) row.st = fe78_status(tk, row.st);
    return row;
  };
} catch (eSess) {}
try {
  var fe78_head0 = fe76_head;
  fe76_head = function (tk) {
    var out = "";
    try { out = fe78_head0.apply(this, arguments); } catch (e) { out = ""; }
    if (fe78_isClosed(tk) && fe78_venueName(tk)) return fe78_status(tk, out);
    return fe78_tidyStatus(out, "", "");
  };
} catch (eHead) {}
try {
  var fe78_sub0 = _patchP2LiveHeader;
  _patchP2LiveHeader = function () {
    var r = fe78_sub0.apply(this, arguments);
    try {
      var priceEl = document.querySelector("#p2body .ap-price");
      var chgEl = document.querySelector("#p2body .ap-chg");
      if (priceEl && priceEl.querySelector && !priceEl.querySelector(".fe78-skel") && fe78_zeroish(priceEl.textContent)) priceEl.innerHTML = fe78_skel();
      if (chgEl && chgEl.querySelector && !chgEl.querySelector(".fe78-skel") && fe78_zeroish(chgEl.textContent)) chgEl.innerHTML = fe78_skel();
      var sub = document.getElementById("p2sub");
      var tk = typeof termSelTk !== "undefined" ? termSelTk : "";
      if (sub && tk) sub.textContent = fe78_status(tk, sub.textContent);
    } catch (e) {}
    return r;
  };
} catch (eSub) {}
try {
  var fe78_ask0 = fe69_askCard;
  function fe78_fillAsk(btn) {
    var inp = document.getElementById("chatInp");
    if (!inp) return;
    var tk = "";
    try { tk = fe69_intelTk(); } catch (e1) { tk = ""; }
    var who = tk;
    try {
      if (typeof A !== "undefined" && A && A.find) {
        var row = A.find(function (x) { return x && x.tk === tk; });
        if (row && row.nm) who = row.nm;
      }
    } catch (e2) {}
    if (!who) {
      try { who = fe69_askHead(btn); } catch (e3) { who = ""; }
    }
    var cur = String(inp.value || "");
    var next = fe78_askPrefill(who || cur.replace(/^What matters most about\s+/i, "").replace(/\?$/, ""));
    if (!cur || /what matters most about/i.test(cur) || cur === next) inp.value = next;
  }
  fe69_askCard = function (btn) {
    var r = fe78_ask0.apply(this, arguments);
    try { fe78_fillAsk(btn); } catch (e) {}
    [40, 180, 400].forEach(function (ms) {
      setTimeout(function () { try { fe78_fillAsk(btn); } catch (e2) {} }, ms);
    });
    return r;
  };
} catch (eAsk) {}
try {
  var fe78_openAsk0 = _openResearchAssistant;
  _openResearchAssistant = function (question) {
    var q = String(question || "");
    if (/what matters most about/i.test(q)) q = fe78_askPrefill(q.replace(/^what matters most about\s+/i, "").replace(/\?$/, ""));
    return fe78_openAsk0.call(this, q);
  };
} catch (eOpen) {}
try {
  fe77_dxyTitle = function (ice, fallback, label) {
    return fe78_dxyLabel(label, ice, fallback);
  };
} catch (eDxy) {}
try {
  var fe78_pct0 = fe73_pctText;
  fe73_pctText = function (n) {
    if (!isFinite(Number(n)) || Number(n) === 0) return "";
    return fe78_pct0.apply(this, arguments);
  };
} catch (ePct) {}
try {
  var fe78_fpct0 = fe66_pct;
  fe66_pct = function (ch) {
    if (!isFinite(Number(ch)) || Number(ch) === 0) return "";
    return fe78_fpct0.apply(this, arguments);
  };
} catch (eFpct) {}
try {
  var fe78_abs0 = fe73_absText;
  fe73_absText = function (ccy, n) {
    if (!isFinite(Number(n)) || Math.abs(Number(n)) < 0.005) return "";
    var out = fe78_abs0.apply(this, arguments);
    return fe78_zeroish(out) ? "" : out;
  };
} catch (eAbs) {}
function fe78_scrubZeros(root) {
  if (!root || !root.querySelectorAll) return;
  root.querySelectorAll(".ap-price,.ap-chg,.asset-price,.asset-chg,.change,.idx-card-px,.idx-card-chg,.conv-px,.conv-chg,.value").forEach(function (el) {
    if (el.querySelector && el.querySelector(".fe78-skel")) return;
    if (fe78_zeroish(el.textContent || "")) el.innerHTML = fe78_skel();
  });
}
try {
  var fe78_rm0 = renderMain;
  renderMain = function () {
    var r = fe78_rm0.apply(this, arguments);
    try { fe78_scrubZeros(document.getElementById("main")); } catch (e) {}
    return r;
  };
} catch (eRm) {}
try {
  var fe78_rp0 = renderP2;
  renderP2 = function () {
    var r = fe78_rp0.apply(this, arguments);
    try { fe78_scrubZeros(document.getElementById("p2body")); } catch (e) {}
    return r;
  };
} catch (eRp) {}
try {
  setInterval(function () {
    try { fe78_scrubZeros(document.body); } catch (e) {}
  }, 80);
} catch (eIv) {}

var fe78_srvRegime = null;
function fe78_stampRegime(raw) {
  var view = fe78_regimeFrom(raw, null);
  if (!view || view.localEstimate) return;
  if (fe78_srvRegime && fe78_srvRegime.asOf && view.asOf) {
    var a = Date.parse(fe78_srvRegime.asOf);
    var b = Date.parse(view.asOf);
    if (isFinite(a) && isFinite(b) && b + 1000 < a) return;
  }
  fe78_srvRegime = view;
}
function fe78_academyHtml(note) {
  if (!note || !note.text) return "";
  var cls = note.amber ? "fe78-acad fe78-acad-stale" : "fe78-acad";
  return '<p class="' + cls + '">' + fe78_esc(note.text) + "</p>";
}
try {
  var fe78_eng0 = _computeRegimeEngine;
  _computeRegimeEngine = function () {
    var local = null;
    try { local = fe78_eng0.apply(this, arguments); } catch (e) { local = null; }
    return fe78_regimeFrom(fe78_srvRegime, local);
  };
} catch (eReg) {}
try {
  var fe78_ref0 = fe77_takeRef;
  fe77_takeRef = function (data) {
    var r = fe78_ref0.apply(this, arguments);
    try { if (data && data.regime) fe78_stampRegime(data.regime); } catch (e) {}
    return r;
  };
} catch (eRef) {}
try {
  var fe78_sm0 = fe77_streamMeta;
  fe77_streamMeta = function () {
    var meta = fe78_sm0.apply(this, arguments);
    try { if (meta && meta.regime) fe78_stampRegime(meta.regime); } catch (e) {}
    return meta;
  };
} catch (eSm) {}
try {
  var fe78_json0 = _bb2CommitJson;
  _bb2CommitJson = function (data) {
    try { if (data && data.meta && data.meta.regime) fe78_stampRegime(data.meta.regime); } catch (e) {}
    return fe78_json0.apply(this, arguments);
  };
} catch (eJs) {}
try {
  if (typeof _chatMsgs !== "undefined" && _chatMsgs && _chatMsgs.forEach) {
    _chatMsgs.forEach(function (m) { if (m && m.meta && m.meta.regime) fe78_stampRegime(m.meta.regime); });
  }
} catch (eBoot) {}
try {
  var fe78_step0 = _rt47StepHtml;
  _rt47StepHtml = function (s) {
    var html = fe78_step0.apply(this, arguments);
    try {
      var note = (typeof _rt48Ai !== "undefined" && _rt48Ai && _rt48Ai.note) ? _rt48Ai.note : null;
      var banner = fe78_academyHtml(note);
      if (banner && s && (s.ai || (s.t === "info" && typeof _rt47L !== "undefined" && _rt47L.id === "news"))) {
        if (String(html).indexOf("fe78-acad") < 0) html = banner + html;
      }
    } catch (e) {}
    return html;
  };
} catch (eStep) {}
try {
  var rawAc = JSON.parse(localStorage.getItem("td_academy_auto_v1") || "{}");
  if (rawAc && rawAc.ai && rawAc.ai.note && typeof _rt48Ai === "object" && _rt48Ai) _rt48Ai.note = rawAc.ai.note;
} catch (eAc) {}
