/* chat102 terminal client. No polling. Two requests, then stop. */
(function (root) {
  "use strict";
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c];
    });
  }
  function num(n, d) {
    if (typeof n !== "number" || !isFinite(n)) return "";
    return n.toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function chg(n, d, suffix) {
    if (typeof n !== "number" || !isFinite(n)) return "";
    if (n === 0) return (d ? "0." + "0".repeat(d) : "0") + (suffix || "");
    return (n > 0 ? "+" : "\u2212") + Math.abs(n).toFixed(d) + (suffix || "");
  }
  function uk(iso) {
    var ms = Date.parse(iso);
    if (!isFinite(ms)) return "";
    try {
      return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms));
    } catch (e) { return ""; }
  }
  function miss(row) {
    if (!row) return "This reading is unavailable. No number was filled in.";
    if (row.message) return row.message;
    if (row.status === "timeout") return "This source did not answer in time. No number was filled in.";
    if (row.status === "malformed") return "This source returned something we could not use. No number was filled in.";
    return "This reading is unavailable. No number was filled in.";
  }
  function shown(row) { return row && (row.status === "ok" || row.status === "partial" || row.status === "stale"); }
  function tile(title, body, href, label) {
    return "<article class=\"c102-tile\"><h3>" + esc(title) + "</h3>" + body + (href ? "<p><a href=\"" + href + "\">" + esc(label) + "</a></p>" : "") + "</article>";
  }
  function when(row) {
    var t = row.asOfUk || uk(row.asOfUtc) || row.date || "";
    var lag = row.lagSeconds != null ? " \u00b7 " + (row.lagSeconds < 90 ? row.lagSeconds + " seconds" : row.lagSeconds < 5400 ? Math.round(row.lagSeconds / 60) + " minutes" : Math.round(row.lagSeconds / 3600) + " hours") + " ago" : "";
    return t ? "<p class=\"c102-k\">" + esc(t + lag) + (row.frequency ? " \u00b7 " + esc(row.frequency) : "") + (row.delayedByMin != null ? " \u00b7 exchange delay " + esc(String(row.delayedByMin)) + " min" : "") + "</p>" : "";
  }
  function priceTile(row, digits) {
    if (!shown(row) || typeof row.price !== "number") return "<p class=\"c102-miss\">" + esc(miss(row)) + "</p>";
    var change = row.change == null ? "<p class=\"c102-miss\">Change unavailable. No figure was filled in.</p>" : "<p>Change " + esc(chg(row.change, digits, "")) + (row.change === 0 ? " (the feed returned zero)" : "") + "</p>";
    var stale = row.status !== "ok" && row.message ? "<p class=\"c102-miss\">" + esc(row.message) + "</p>" : "";
    return "<p class=\"c102-v\">" + esc(num(row.price, digits)) + "</p>" + change + when(row) + "<p class=\"c102-k\">" + esc(row.source || "") + "</p>" + stale;
  }
  function yieldTile(row) {
    var v = row && (typeof row.value === "number" ? row.value : row.price);
    if (!shown(row) || typeof v !== "number") return "<p class=\"c102-miss\">" + esc(miss(row)) + "</p>";
    var change = row.change == null ? "<p class=\"c102-miss\">Change unavailable.</p>" : "<p>Change " + esc(chg(row.change, 2, row.unit === "percent" || row.value != null ? " pt" : "")) + (row.change === 0 ? " (the feed returned zero)" : "") + "</p>";
    var extra = row.status !== "ok" && row.message ? "<p class=\"c102-miss\">" + esc(row.message) + "</p>" : "";
    return "<p class=\"c102-v\">" + esc(num(v, 2)) + "%</p>" + change + when(row) + "<p class=\"c102-k\">" + esc(row.source || "") + "</p>" + extra;
  }
  function render(model, chart) {
    model = model || {};
    var spot = model.spot || {};
    var ch = model.spotChange || {};
    var fut = chart && chart.lastCompleted ? chart : null;
    var spotBody;
    if (shown(spot) && typeof spot.price === "number") {
      spotBody = "<p class=\"c102-v\">$" + esc(num(spot.price, 2)) + "</p><p class=\"c102-k\">" + esc(spot.unit || "US dollars per troy ounce") + "</p>" + when(spot) + "<p class=\"c102-k\">" + esc(spot.source || "") + " \u00b7 spot quote</p>";
      if (ch.status === "ok" && typeof ch.changePct === "number") spotBody += "<p>Daily change " + esc(chg(ch.changePct, 2, "%")) + (ch.changePct === 0 ? " (the snapshot returned zero)" : "") + "</p><p class=\"c102-k\">" + esc(ch.basis || "") + "</p><p class=\"c102-k\">" + esc(ch.source || "") + "</p>";
      else spotBody += "<p class=\"c102-miss\">" + esc(miss(ch)) + "</p>";
      if (spot.status === "stale" && spot.message) spotBody += "<p class=\"c102-miss\">" + esc(spot.message) + "</p>";
    } else spotBody = "<p class=\"c102-miss\">" + esc(miss(spot)) + "</p>";
    var futBody = "<p class=\"c102-miss\">" + esc(fut ? "" : miss(chart)) + "</p>";
    if (fut) {
      var lc = fut.lastCompleted;
      futBody = "<p class=\"c102-v\">$" + esc(num(lc.close, 2)) + "</p><p>" + esc(fut.label || "COMEX front-month gold future \u00b7 delayed") + "</p><p class=\"c102-k\">Last completed session " + esc(lc.sessionDate) + " \u00b7 " + esc(fut.exchangeTimezone || "") + "</p><p class=\"c102-k\">" + esc(fut.incompleteNote || "") + "</p><p class=\"c102-k\">" + (lc.volume == null ? "No futures volume on that session." : "Futures volume " + esc(num(lc.volume, 0)) + ", not spot volume.") + "</p>";
    }
    var real = model.realMarket && shown(model.realMarket) && (typeof model.realMarket.value === "number" || typeof model.realMarket.price === "number") ? model.realMarket : model.realOfficial;
    var tiles = [
      tile("Gold spot", spotBody, "/gold/dashboard/", "Gold dashboard"),
      tile("Front-month future", futBody, "#c102-chart", "Chart"),
      tile("US dollar index", priceTile(model.dollar, 2), "/gold/dashboard/", "Dollar on the gold dashboard"),
      tile("US 10-year yield", yieldTile(model.nominal), "/markets/yields/", "Yields"),
      tile("US 10-year real yield", yieldTile(real), "/markets/yields/", "Yields"),
      tile("Volatility index", priceTile(model.vix, 2), "/data-status/", "Data status")
    ].join("");
    var ratio = model.ratio || {};
    var macro = "<p>" + esc(model.note || "") + "</p><h3>Official daily yields</h3><p class=\"c102-k\">These prints keep their own dates. They are not the same moment as the delayed quotes.</p>" + yieldTile(model.nominalOfficial) + yieldTile(model.realOfficial) + "<h3>Gold and silver</h3>";
    if (shown(ratio) && typeof ratio.value === "number") {
      macro += "<p class=\"c102-v\">" + esc(num(ratio.value, 1)) + "</p><p>" + esc(ratio.formula || "Gold spot \u00f7 silver spot") + "</p>";
      macro += "<p class=\"c102-k\">Gold " + esc(num(ratio.numerator.price, 2)) + " USD per troy ounce, " + esc(uk(ratio.numerator.asOfUtc)) + ". Silver " + esc(num(ratio.denominator.price, 2)) + " USD per troy ounce, " + esc(uk(ratio.denominator.asOfUtc)) + ".</p>";
      if (ratio.message) macro += "<p class=\"c102-miss\">" + esc(ratio.message) + "</p>";
    } else macro += "<p class=\"c102-miss\">" + esc(miss(ratio)) + "</p>";
    var pos = model.positioning || {};
    var posHtml;
    if (pos.status === "ok" || pos.status === "stale") {
      posHtml = "<p class=\"c102-v\">" + esc(num(pos.net, 0)) + "</p><p>Net gold futures, money managers. Contracts that gain if the price rises, minus contracts that gain if it falls.</p>";
      posHtml += "<p class=\"c102-k\">Weekly \u00b7 report date " + esc(pos.reportDate) + (pos.lagDays != null ? " \u00b7 " + esc(String(pos.lagDays)) + " days before today" : "") + "</p>";
      posHtml += "<p class=\"c102-k\">" + esc(pos.market || "") + " \u00b7 " + esc(pos.source || "") + "</p>";
      posHtml += "<p>Long " + esc(num(pos.long, 0)) + " \u00b7 short " + esc(num(pos.short, 0)) + (pos.openInterest != null ? " \u00b7 open interest " + esc(num(pos.openInterest, 0)) : "") + "</p>";
      posHtml += pos.weekChange == null ? "<p class=\"c102-miss\">Change from the prior week is unavailable.</p>" : "<p>Change from the prior week " + esc(chg(pos.weekChange, 0, " contracts")) + (pos.weekChange === 0 ? " (the two reports matched)" : "") + "</p>";
      if (pos.status === "stale") posHtml += "<p class=\"c102-miss\">" + esc(pos.message || "") + "</p>";
      posHtml += "<p><a href=\"/gold/positioning/\">Gold positioning, including the ten-year range</a></p>";
    } else posHtml = "<p class=\"c102-miss\">" + esc(miss(pos)) + "</p>";
    var ev = model.events || {};
    var evHtml;
    if (ev.items && ev.items.length) {
      evHtml = "<p class=\"c102-k\">" + esc(ev.message || "Scheduled releases only. Consensus forecasts are not shown.") + "</p><ol class=\"c102-ev\">" + ev.items.map(function (it) {
        return "<li><strong>" + esc(it.name || "Release") + "</strong> <span class=\"c102-k\">" + esc(it.when || it.day || "") + " \u00b7 " + esc(it.agency || "") + " \u00b7 " + esc(it.source || "") + "</span></li>";
      }).join("") + "</ol><p><a href=\"/calendar/\">Full calendar</a></p>";
    } else evHtml = "<p class=\"c102-miss\">" + esc(miss(ev)) + "</p><p><a href=\"/calendar/\">Full calendar</a></p>";
    var risk = "<ul class=\"c102-src\"><li>Gold and silver spot from gold-api.com, in US dollars per troy ounce, each with its own time. A futures percentage is not used as the spot change.</li><li>The chart is the COMEX front-month future on a continuous rolling series. It is not spot gold and the volume is not spot volume.</li><li>The dollar index is the ICE index via Yahoo Finance when the feed names ICE. A computed currency basket is not shown as that index.</li><li>The US 10-year yield is a delayed quote. The official daily Treasury print is a second figure with its own date.</li><li>The real yield keeps the delayed quote and the official daily print apart.</li><li>Volatility is the Cboe Volatility Index. A volatility note is not a substitute.</li><li>Positioning is the weekly CFTC report for COMEX gold only.</li><li>The calendar lists scheduled releases. It does not include a consensus forecast.</li></ul><p>Not investment advice. Capital at risk.</p><p><a href=\"/data-status/\">Data status</a> \u00b7 <a href=\"/methodology\">Methodology</a> \u00b7 <a href=\"/dashboard/\">Dashboard</a> \u00b7 <a href=\"/gold/\">Gold</a></p>";
    var label = (fut && fut.label) || "COMEX front-month gold future \u00b7 delayed";
    var note = (fut && fut.historyNote) || "Completed sessions only. The current session is left out when the feed includes it.";
    var extra = [fut && fut.barTimeNote, fut && fut.volumeRepeatNote, fut && fut.incompleteNote].filter(Boolean).join(" ");
    var chartHtml = "<div id=\"c102-chart\" class=\"c102-chart\"><div class=\"c102-chart-h\"><h2 id=\"c102-chart-title\">" + esc(label) + "</h2><p id=\"c102-chart-note\" class=\"c102-k\">" + esc(note) + "</p><p class=\"c102-k\">" + esc(extra) + "</p></div><div class=\"c102-tools\" role=\"group\" aria-label=\"Chart range\"><button type=\"button\" data-c102-months=\"3\" aria-pressed=\"false\">3 months</button><button type=\"button\" data-c102-months=\"6\" aria-pressed=\"true\">6 months</button><button type=\"button\" data-c102-months=\"12\" aria-pressed=\"false\">1 year</button><button type=\"button\" data-c102-ma=\"20\" aria-pressed=\"true\">20-session average</button><button type=\"button\" data-c102-ma=\"50\" aria-pressed=\"true\">50-session average</button><button type=\"button\" id=\"c102-table-btn\" aria-expanded=\"false\" aria-controls=\"c102-table\">Table of sessions</button></div><p id=\"c102-span\" class=\"c102-k\"></p><p id=\"c102-readout\" class=\"c102-read\">Use the arrow keys on the chart to read a session.</p><div id=\"c102-live\" class=\"c102-live\" aria-live=\"polite\"></div><canvas id=\"c102-canvas\" width=\"800\" height=\"460\" tabindex=\"0\" role=\"img\" aria-label=\"" + esc(label) + "\" aria-describedby=\"c102-readout c102-chart-note\"></canvas><div id=\"c102-table\" hidden></div></div>";
    return "<div class=\"c102\" id=\"c102\"><p class=\"c102-k\">Assembled " + esc(model.generatedAtUk || uk(model.generatedAtUtc) || "") + "</p><div class=\"c102-tiles\">" + tiles + "</div>" + chartHtml + "<div class=\"c102-grid\"><section aria-labelledby=\"c102-macro\"><h2 id=\"c102-macro\">Macro</h2>" + macro + "</section><section aria-labelledby=\"c102-pos\"><h2 id=\"c102-pos\">Positioning</h2>" + posHtml + "</section></div><section aria-labelledby=\"c102-ev\"><h2 id=\"c102-ev\">Events</h2>" + evHtml + "</section><section aria-labelledby=\"c102-risk\"><h2 id=\"c102-risk\">Risk and sources</h2>" + risk + "</section></div>";
  }

  function cssColor(name, fallback) {
    try {
      var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return v || fallback;
    } catch (e) { return fallback; }
  }
  function shiftMonth(iso, delta) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ""));
    if (!m) return "";
    var d = new Date(Date.UTC(+m[1], +m[2] - 1 + delta, +m[3]));
    return d.toISOString().slice(0, 10);
  }
  function windowBars(bars, months) {
    var list = bars || [];
    if (!list.length) return [];
    var n = Number(months);
    if (!isFinite(n) || n <= 0) n = 6;
    var cut = shiftMonth(list[list.length - 1].sessionDate, -n);
    var out = list.filter(function (b) { return b && b.sessionDate && b.sessionDate >= cut; });
    return out.length ? out : list.slice(-1);
  }
  function draw(canvas, chart, state) {
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");
    var bars = windowBars(chart && chart.bars, state.months);
    var dpr = (root.devicePixelRatio || 1);
    var w = canvas.clientWidth || 320;
    var h = canvas.clientHeight || 300;
    canvas.width = Math.max(1, Math.floor(w * dpr));
    canvas.height = Math.max(1, Math.floor(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var ink = cssColor("--ink", "#1b1b1b");
    var muted = cssColor("--muted", "#5f6368");
    var rule = cssColor("--rule", "#dedad2");
    var up = cssColor("--up", "#2f6b47");
    var down = cssColor("--down", "#a23b2a");
    var paper = cssColor("--paper", "#fbfaf7");
    ctx.fillStyle = paper;
    ctx.fillRect(0, 0, w, h);
    if (!bars.length) {
      ctx.fillStyle = ink;
      ctx.font = "15px sans-serif";
      ctx.fillText("No completed session to draw.", 12, 28);
      return;
    }
    var padL = 58, padR = 12, padT = 12, padB = 28;
    var volH = Math.max(36, Math.round(h * 0.18));
    var plotB = h - padB - volH - 8;
    var highs = bars.map(function (b) { return b.h; });
    var lows = bars.map(function (b) { return b.l; });
    var max = Math.max.apply(null, highs);
    var min = Math.min.apply(null, lows);
    if (!(max > min)) { max += 1; min -= 1; }
    var y = function (v) { return padT + (max - v) / (max - min) * (plotB - padT); };
    var slot = (w - padL - padR) / bars.length;
    ctx.strokeStyle = rule;
    ctx.lineWidth = 1;
    ctx.fillStyle = muted;
    ctx.font = "14px sans-serif";
    for (var g = 0; g < 4; g++) {
      var val = min + (max - min) * g / 3;
      var yy = y(val);
      ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke();
      ctx.fillText(num(val, 0), 4, yy + 4);
    }
    var vols = bars.map(function (b) { return b.volume || 0; });
    var vmax = Math.max.apply(null, vols.concat([1]));
    bars.forEach(function (b, i) {
      var x = padL + slot * i + slot / 2;
      var rising = b.c >= b.o;
      ctx.strokeStyle = rising ? up : down;
      ctx.fillStyle = rising ? up : down;
      ctx.beginPath();
      ctx.moveTo(x, y(b.h));
      ctx.lineTo(x, y(b.l));
      ctx.stroke();
      var top = y(Math.max(b.o, b.c));
      var bot = y(Math.min(b.o, b.c));
      ctx.fillRect(x - Math.max(1, slot * 0.28), top, Math.max(2, slot * 0.56), Math.max(1, bot - top));
      if (b.volume) {
        var vh = (b.volume / vmax) * volH;
        ctx.globalAlpha = 0.45;
        ctx.fillRect(x - Math.max(1, slot * 0.28), h - padB - vh, Math.max(2, slot * 0.56), vh);
        ctx.globalAlpha = 1;
      }
    });
    function line(series, color) {
      if (!state["ma" + series] || !chart["ma" + series] || chart["ma" + series].status !== "ok") return;
      var map = {};
      chart["ma" + series].points.forEach(function (p) { map[p.sessionDate] = p.value; });
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      var started = false;
      bars.forEach(function (b, i) {
        if (map[b.sessionDate] == null) return;
        var x = padL + slot * i + slot / 2;
        var yy = y(map[b.sessionDate]);
        if (!started) { ctx.moveTo(x, yy); started = true; } else ctx.lineTo(x, yy);
      });
      ctx.stroke();
    }
    line(20, cssColor("--amber", "#8a6a12"));
    line(50, cssColor("--accent", "#1f3a5f"));
    if (state.index >= 0 && state.index < bars.length) {
      var b = bars[state.index];
      var x = padL + slot * state.index + slot / 2;
      ctx.strokeStyle = ink;
      ctx.setLineDash([3, 3]);
      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, h - padB); ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.fillStyle = muted;
    ctx.font = "14px sans-serif";
    var left = bars[0].sessionDate;
    var right = bars[bars.length - 1].sessionDate;
    ctx.fillText(left, padL, h - 8);
    var rightW = ctx.measureText ? ctx.measureText(right).width : 88;
    ctx.fillText(right, Math.max(padL + 96, w - padR - rightW), h - 8);
    state._bars = bars;
    state._geom = { padL: padL, slot: slot };
  }
  function readout(chart, bar) {
    if (!bar) return "No session selected.";
    var vol = bar.volume == null ? "Volume not returned for this session." : "Futures volume " + num(bar.volume, 0) + ".";
    var tz = (chart && chart.exchangeTimezone) || "America/New_York";
    var clock = String(bar.timeUtc || "").slice(11, 16);
    return "Session date " + bar.sessionDate + " (" + tz + "). Open " + num(bar.o, 2) + ", high " + num(bar.h, 2) + ", low " + num(bar.l, 2) + ", close " + num(bar.c, 2) + ". " + vol + " Bar timestamp " + clock + " UTC, midnight at the start of that session date in New York. Not a settlement time.";
  }
  function tableHtml(bars) {
    var view = (bars || []).slice(-12);
    return "<div class=\"c102-sessions\">" + view.map(function (b) {
      return "<article class=\"c102-session\"><h3>" + esc(b.sessionDate) + "</h3><p>Open " + esc(num(b.o, 2)) + "</p><p>High " + esc(num(b.h, 2)) + "</p><p>Low " + esc(num(b.l, 2)) + "</p><p>Close " + esc(num(b.c, 2)) + "</p><p>" + (b.volume == null ? "Volume not returned" : "Futures volume " + esc(num(b.volume, 0))) + "</p><p class=\"c102-k\">" + esc(uk(b.timeUtc)) + "</p></article>";
    }).join("") + "<p class=\"c102-k\">Latest 12 completed sessions in this list. The chart uses the selected range.</p></div>";
  }
  function bind(rootEl, chart) {
    var canvas = rootEl.querySelector("#c102-canvas");
    var live = rootEl.querySelector("#c102-live");
    var readoutEl = rootEl.querySelector("#c102-readout");
    var table = rootEl.querySelector("#c102-table");
    var state = { months: 6, ma20: true, ma50: true, index: -1, user: false };
    var ro, mq;
    function spanText() {
      var bars = windowBars(chart && chart.bars, state.months);
      if (!bars.length) return "No completed sessions in this range.";
      var name = state.months === 12 ? "1 year" : state.months + " months";
      return name + " \u00b7 " + bars[0].sessionDate + " to " + bars[bars.length - 1].sessionDate + " \u00b7 " + bars.length + " completed sessions";
    }
    function paint() {
      draw(canvas, chart, state);
      var span = rootEl.querySelector("#c102-span");
      if (span) span.textContent = spanText();
      if (canvas && state._bars && state._bars.length) {
        canvas.setAttribute("data-c102-from", state._bars[0].sessionDate);
        canvas.setAttribute("data-c102-to", state._bars[state._bars.length - 1].sessionDate);
      }
    }
    function select(i, fromUser) {
      var bars = state._bars || [];
      if (!bars.length) return;
      if (i < 0) i = 0;
      if (i >= bars.length) i = bars.length - 1;
      state.index = i;
      paint();
      var text = readout(chart, bars[i]);
      if (readoutEl) readoutEl.textContent = text;
      if (fromUser && live) live.textContent = text;
    }
    rootEl.querySelectorAll("[data-c102-months]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.months = Number(btn.getAttribute("data-c102-months")) || 6;
        rootEl.querySelectorAll("[data-c102-months]").forEach(function (b) { b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
        paint();
        var bars = state._bars || [];
        if (bars.length) select(bars.length - 1, false);
      });
    });
    rootEl.querySelectorAll("[data-c102-ma]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var k = btn.getAttribute("data-c102-ma") === "50" ? "ma50" : "ma20";
        state[k] = !state[k];
        btn.setAttribute("aria-pressed", state[k] ? "true" : "false");
        paint();
      });
    });
    var tableBtn = rootEl.querySelector("#c102-table-btn");
    if (tableBtn && table) {
      tableBtn.addEventListener("click", function () {
        var open = table.hasAttribute("hidden");
        if (open) { table.innerHTML = tableHtml(windowBars(chart && chart.bars, state.months)); table.removeAttribute("hidden"); }
        else table.setAttribute("hidden", "");
        tableBtn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
    if (canvas) {
      canvas.addEventListener("keydown", function (e) {
        var bars = state._bars || [];
        if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" && e.key !== "Home" && e.key !== "End") return;
        e.preventDefault();
        var i = state.index < 0 ? bars.length - 1 : state.index;
        if (e.key === "ArrowLeft") i -= 1;
        if (e.key === "ArrowRight") i += 1;
        if (e.key === "Home") i = 0;
        if (e.key === "End") i = bars.length - 1;
        select(i, true);
      });
      canvas.addEventListener("pointerdown", function (e) {
        var rect = canvas.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var g = state._geom;
        if (!g || !state._bars) return;
        var i = Math.floor((x - g.padL) / g.slot);
        select(i, true);
      });
    }
    if (typeof ResizeObserver === "function" && canvas) {
      ro = new ResizeObserver(function () { paint(); });
      ro.observe(canvas);
    }
    var mo;
    if (typeof MutationObserver === "function") {
      mo = new MutationObserver(function () { paint(); });
      mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-theme"] });
    }
    if (window.matchMedia) {
      try {
        mq = window.matchMedia("(prefers-color-scheme: dark)");
        var onMq = function () { paint(); };
        if (mq.addEventListener) mq.addEventListener("change", onMq);
        else if (mq.addListener) mq.addListener(onMq);
      } catch (e) {}
    }
    paint();
    if (state._bars && state._bars.length) select(state._bars.length - 1, false);
    rootEl._c102Cleanup = function () {
      try { if (ro) ro.disconnect(); } catch (e) {}
      try { if (mo) mo.disconnect(); } catch (e) {}
    };
    window.addEventListener("pagehide", function () { if (rootEl._c102Cleanup) rootEl._c102Cleanup(); }, { once: true });
  }
  function mount(el, opts) {
    opts = opts || {};
    if (!el) return;
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    window.addEventListener("pagehide", function () { if (ctrl) ctrl.abort(); }, { once: true });
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden" && ctrl) ctrl.abort();
    });
    function fail(message) {
      el.innerHTML = render({ title: "Terminal", generatedAtUtc: new Date().toISOString(), note: "Gold is priced in dollars and pays no interest, so the dollar, US yields, volatility and futures positioning are the readings usually set beside it. Nothing here is a forecast or a recommendation.", spot: { status: "unavailable", message: message }, spotChange: { status: "unavailable", message: message }, dollar: { status: "unavailable", message: message }, nominal: { status: "unavailable", message: message }, realMarket: { status: "unavailable", message: message }, realOfficial: { status: "unavailable", message: message }, nominalOfficial: { status: "unavailable", message: message }, vix: { status: "unavailable", message: message }, ratio: { status: "unavailable", message: message }, positioning: { status: "unavailable", message: message }, events: { status: "unavailable", message: message } }, { status: "unavailable", message: message });
      el.setAttribute("aria-busy", "false");
    }
    if (opts.model || opts.chart) {
      el.innerHTML = render(opts.model || {}, opts.chart || null);
      el.setAttribute("aria-busy", "false");
      bind(el, opts.chart || {});
      return;
    }
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); fail("The readings did not arrive in time. No number was filled in."); }, 12000);
    Promise.all([
      fetch("/api/c102/terminal", { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: "application/json" } }).then(function (r) { if (!r.ok) throw new Error("http"); return r.json(); }),
      fetch("/api/c102/chart", { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: "application/json" } }).then(function (r) { if (!r.ok) throw new Error("http"); return r.json(); })
    ]).then(function (pair) {
      clearTimeout(timer);
      el.innerHTML = render(pair[0], pair[1]);
      el.setAttribute("aria-busy", "false");
      bind(el, pair[1]);
    }).catch(function () {
      clearTimeout(timer);
      if (el.getAttribute("aria-busy") === "false" && el.querySelector(".c102")) return;
      fail("The readings did not load. No number was filled in.");
    });
  }
  root.c102ui = { render: render, mount: mount, draw: draw, readout: readout, windowBars: windowBars };
})(typeof globalThis !== "undefined" ? globalThis : this);
