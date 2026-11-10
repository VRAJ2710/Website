/* chat103 CPI day client. One request, then one retry only when the server has no stored release yet. */
(function (root) {
  "use strict";
  var GOLD = "Gold futures (COMEX, front month), Yahoo Finance delayed";
  var CONTRIB = "approx. contribution, our calculation from BLS data";
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c];
    });
  }
  function num(n, d) {
    if (typeof n !== "number" || !isFinite(n)) return "";
    return n.toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function pct(n) {
    if (typeof n !== "number" || !isFinite(n)) return "";
    if (n === 0) return "0.0%";
    return (n > 0 ? "+" : "\u2212") + Math.abs(n).toFixed(1) + "%";
  }
  function pct2(n) {
    if (typeof n !== "number" || !isFinite(n)) return "";
    if (n === 0) return "0.00%";
    return (n > 0 ? "+" : "\u2212") + Math.abs(n).toFixed(2) + "%";
  }
  function miss(text) {
    return "<p class=\"c103-miss\">" + esc(text || "not loaded yet") + "</p>";
  }
  function figure(row, kind) {
    if (!row) return miss("not loaded yet");
    var value = kind === "yoy" ? row.yoyRounded : row.momRounded;
    var index = kind === "yoy" ? row.nsaIndex : row.saIndex;
    var series = kind === "yoy" ? row.yoySeries : row.momSeries;
    var label = kind === "yoy" ? "Year change, not seasonally adjusted" : "Month change, seasonally adjusted";
    if (typeof value !== "number") return miss("not loaded yet");
    var carried = row.message ? miss(row.message) : "";
    return "<p class=\"c103-v\">" + esc(pct(value)) + "</p><p>" + esc(label) + ".</p><p class=\"c103-k\">Index " + esc(num(index, 3)) + " \u00b7 " + esc(series || "") + "</p><p class=\"c103-k\">" + esc(row.source || "Source: U.S. Bureau of Labor Statistics") + " \u00b7 " + esc(row.periodLabel || "") + "</p><p>" + esc(row.why || "") + "</p>" + carried;
  }
  function card(title, body) {
    return "<article class=\"c103-card\"><h3>" + esc(title) + "</h3>" + body + "</article>";
  }
  function countdown(c) {
    if (!c || !c.releaseAtUtc) return "<section class=\"c103-count\" aria-labelledby=\"c103-count\"><h2 id=\"c103-count\">Next release</h2>" + miss("not loaded yet") + "</section>";
    var clock = c.days + "d " + c.hours + "h " + c.minutes + "m";
    var src = c.source === "labelled-fallback"
      ? (c.fallbackLabel || "Labelled fallback. This date was not in the cached BLS schedule.")
      : "Schedule: U.S. Bureau of Labor Statistics.";
    return "<section class=\"c103-count\" aria-labelledby=\"c103-count\"><h2 id=\"c103-count\">Next release</h2><p><strong data-c103-left=\"" + esc(c.releaseAtUtc) + "\">" + esc(clock) + "</strong></p><p>" + esc(c.what || "") + "</p><p>Release " + esc(c.releaseUk || "") + (c.zoneName ? " (" + esc(c.zoneName) + ")" : "") + ".</p><p class=\"c103-k\">Reference month " + esc(c.referenceLabel || "") + ".</p><p>" + esc(c.why || "") + "</p><p class=\"c103-k\">" + esc(src) + " <a href=\"" + esc(c.scheduleUrl || "https://www.bls.gov/schedule/news_release/cpi.htm") + "\">BLS schedule</a></p></section>";
  }
  function banner(notice) {
    if (!notice || !notice.show) return "";
    return "<div class=\"c103-banner\" role=\"status\"><p><strong>" + esc(notice.text || "CPI is out.") + "</strong> This notice stays on the site. It is not an email.</p><button type=\"button\" data-c103-dismiss=\"" + esc(notice.releaseKey || "") + "\">Dismiss</button></div>";
  }
  function trendTable(rows) {
    var body = (rows || []).map(function (r) {
      return "<tr><th scope=\"row\">" + esc(r.periodLabel || r.period || "") + "</th><td>" + esc(pct(r.headlineYoy)) + "</td><td>" + esc(pct(r.coreYoy)) + "</td></tr>";
    }).join("");
    if (!body) return miss("not loaded yet");
    return "<div class=\"c103-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"24-month trend. This box scrolls sideways on a narrow screen. The rest of the page does not.\"><table><caption>Headline and core, change from a year earlier, last 24 stored months. Source: U.S. Bureau of Labor Statistics.</caption><thead><tr><th scope=\"col\">Month</th><th scope=\"col\">Headline year change</th><th scope=\"col\">Core year change</th></tr></thead><tbody>" + body + "</tbody></table></div>";
  }
  function archiveTable(rows) {
    var body = (rows || []).map(function (r) {
      var h = r.headline || {};
      var c = r.core || {};
      return "<tr><th scope=\"row\">" + esc(r.periodLabel || r.period || "") + "</th><td>" + esc(typeof h.momRounded === "number" ? pct(h.momRounded) : "not loaded yet") + "</td><td>" + esc(typeof h.yoyRounded === "number" ? pct(h.yoyRounded) : "not loaded yet") + "</td><td>" + esc(typeof c.momRounded === "number" ? pct(c.momRounded) : "not loaded yet") + "</td><td>" + esc(typeof c.yoyRounded === "number" ? pct(c.yoyRounded) : "not loaded yet") + "</td></tr>";
    }).join("");
    if (!body) return miss("not loaded yet");
    return "<div class=\"c103-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Archive of stored CPI months. This box scrolls sideways. The rest of the page does not.\"><table><caption>Every stored month. Headline and core only. Source: U.S. Bureau of Labor Statistics. A blank cell was not in the stored release.</caption><thead><tr><th scope=\"col\">Month</th><th scope=\"col\">Headline month</th><th scope=\"col\">Headline year</th><th scope=\"col\">Core month</th><th scope=\"col\">Core year</th></tr></thead><tbody>" + body + "</tbody></table></div>";
  }
  function catTable(rows, ri) {
    var body = (rows || []).map(function (r) {
      var contrib = typeof r.contribution === "number" ? num(r.contribution, 3) : "not loaded yet";
      var weight = typeof r.weight === "number" ? num(r.weight, 3) : "not loaded yet";
      return "<tr><th scope=\"row\">" + esc(r.name) + "</th><td>" + esc(typeof r.momRounded === "number" ? pct(r.momRounded) : "not loaded yet") + "</td><td>" + esc(typeof r.yoyRounded === "number" ? pct(r.yoyRounded) : "not loaded yet") + "</td><td>" + esc(weight) + "</td><td>" + esc(contrib) + "</td><td>" + esc(r.momSeries || "") + "</td></tr>";
    }).join("");
    if (!body) return miss("not loaded yet");
    var cite = ri && ri.citation ? ri.citation : "Relative importance source: U.S. Bureau of Labor Statistics.";
    return "<div class=\"c103-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Category breakdown. This box scrolls sideways. The rest of the page does not.\"><table><caption>Category breakdown for the latest stored month. " + esc(CONTRIB) + ". " + esc(cite) + "</caption><thead><tr><th scope=\"col\">Category</th><th scope=\"col\">Month</th><th scope=\"col\">Year</th><th scope=\"col\">Weight</th><th scope=\"col\">Approx. contribution</th><th scope=\"col\">Month series</th></tr></thead><tbody>" + body + "</tbody></table></div>";
  }
  function goldTable(rows) {
    var body = (rows || []).map(function (r) {
      var hour = r.hourlyAvailable && typeof r.plus1hPct === "number" ? pct2(r.plus1hPct) : "Hourly bars do not cover this release";
      return "<tr><th scope=\"row\">" + esc(r.releaseUk || r.releaseAtUtc || "") + "</th><td>" + esc(r.referenceLabel || "") + "</td><td>" + esc(hour) + "</td><td>" + esc(typeof r.plus1dPct === "number" ? pct2(r.plus1dPct) : "not loaded yet") + "</td><td>" + esc(typeof r.plus5dPct === "number" ? pct2(r.plus5dPct) : "not loaded yet") + "</td><td>" + esc(r.anchorAtUtc || "") + "</td><td>" + esc(r.plus1hAtUtc || "") + "</td></tr>";
    }).join("");
    if (!body) return miss("not loaded yet");
    return "<div class=\"c103-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Gold futures after past CPI releases. This box scrolls sideways. The rest of the page does not.\"><table><caption>" + esc(GOLD) + ". Move from the last bar before 08:30 US Eastern. History only.</caption><thead><tr><th scope=\"col\">Release, UK time</th><th scope=\"col\">Reference month</th><th scope=\"col\">To +1 hour</th><th scope=\"col\">To +1 trading day</th><th scope=\"col\">To +5 trading days</th><th scope=\"col\">Anchor time</th><th scope=\"col\">+1 hour bar end</th></tr></thead><tbody>" + body + "</tbody></table></div>";
  }
  function render(model) {
    model = model || {};
    var latest = model.latest || {};
    var h = latest.headline;
    var c = latest.core;
    var note = model.statusNote ? "<p class=\"c103-miss\">" + esc(model.statusNote) + "</p>" : "";
    var cache = model.cacheNote ? "<p class=\"c103-miss\">" + esc(model.cacheNote) + "</p>" : "";
    var when = latest.periodLabel ? "<p class=\"c103-k\">Latest stored month " + esc(latest.periodLabel) + (latest.releaseUk ? " \u00b7 release " + esc(latest.releaseUk) : "") + ". " + esc(model.source || "Source: U.S. Bureau of Labor Statistics") + ".</p>" : "<p class=\"c103-k\">" + esc(model.source || "Source: U.S. Bureau of Labor Statistics") + ".</p>";
    var stats = "<div class=\"c103-stats\">" + [
      card("Headline, month", figure(h, "mom")),
      card("Headline, year", figure(h, "yoy")),
      card("Core, month", figure(c, "mom")),
      card("Core, year", figure(c, "yoy"))
    ].join("") + "</div>";
    var chart = "<section class=\"c103-chart\" aria-labelledby=\"c103-trend\"><h2 id=\"c103-trend\">24-month trend</h2><p>Year change in headline and core. Each point is a stored BLS month, not a forecast.</p><p id=\"c103-read\" class=\"c103-k\">The table under the chart lists the same numbers.</p><div id=\"c103-live\" class=\"c103-live\" aria-live=\"polite\"></div><canvas id=\"c103-canvas\" tabindex=\"0\" role=\"img\" aria-label=\"Headline and core year change over the last 24 stored months\" aria-describedby=\"c103-read\"></canvas>" + trendTable(model.trend) + "</section>";
    var archive = "<section aria-labelledby=\"c103-arch\"><h2 id=\"c103-arch\">Archive</h2><p>Every month in the stored BLS response, newest first. Built from the index levels, not typed in.</p>" + archiveTable(model.archive) + "</section>";
    var premium = "";
    if (model.access === "premium") {
      premium = "<div class=\"c103-grid\"><section aria-labelledby=\"c103-cat\"><h2 id=\"c103-cat\">Categories</h2><p>What moved inside the basket. " + esc(CONTRIB) + ".</p>" + catTable(model.categories, model.relativeImportance) + "</section><section aria-labelledby=\"c103-gold\"><h2 id=\"c103-gold\">Gold after past releases</h2><p>" + esc(GOLD) + ". The hour column is only filled when hourly bars exist. No view on the next release.</p>" + goldTable(model.gold) + "</section></div>";
    } else {
      premium = "<section class=\"c103-lock\" aria-labelledby=\"c103-lock\"><h2 id=\"c103-lock\">Members</h2><p>The category breakdown, the approximate contributions and the gold-futures history are part of membership. Headline, core, the countdown and the trend above stay available.</p><p><a href=\"/pricing\">See plans</a></p></section>";
    }
    return "<div class=\"c103\" id=\"c103\">" + banner(model.notice) + note + cache + when + countdown(model.countdown) + stats + chart + archive + premium + "<p class=\"c103-k\">" + esc(model.source || "Source: U.S. Bureau of Labor Statistics") + ". Not investment advice. Capital at risk.</p><p><a href=\"/terminal/\">Terminal</a> \u00b7 <a href=\"/calendar/\">Calendar</a> \u00b7 <a href=\"/methodology\">Methodology</a></p></div>";
  }
  function cssColor(name, fallback) {
    try {
      var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return v || fallback;
    } catch (e) { return fallback; }
  }
  function draw(canvas, trend) {
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");
    var rows = trend || [];
    var dpr = root.devicePixelRatio || 1;
    var w = canvas.clientWidth || 320;
    var h = canvas.clientHeight || 240;
    canvas.width = Math.max(1, Math.floor(w * dpr));
    canvas.height = Math.max(1, Math.floor(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var ink = cssColor("--ink", "#1b1b1b");
    var paper = cssColor("--paper", "#fbfaf7");
    var muted = cssColor("--ink-3", "#5c6570");
    var rule = cssColor("--rule", "rgba(0,0,0,.14)");
    var a = cssColor("--gold", "#1f3a5f");
    var b = cssColor("--pos", "#2f6b47");
    ctx.fillStyle = paper;
    ctx.fillRect(0, 0, w, h);
    if (!rows.length) {
      ctx.fillStyle = ink;
      ctx.font = "15px sans-serif";
      ctx.fillText("not loaded yet", 12, 28);
      return;
    }
    var vals = [];
    rows.forEach(function (r) {
      if (typeof r.headlineYoy === "number") vals.push(r.headlineYoy);
      if (typeof r.coreYoy === "number") vals.push(r.coreYoy);
    });
    var min = Math.min.apply(null, vals.concat([0]));
    var max = Math.max.apply(null, vals.concat([1]));
    if (!(max > min)) { max += 1; min -= 1; }
    var padL = 36, padR = 8, padT = 12, padB = 24;
    function y(v) { return padT + (max - v) / (max - min) * (h - padT - padB); }
    function x(i) { return padL + (rows.length === 1 ? 0 : i * (w - padL - padR) / (rows.length - 1)); }
    ctx.strokeStyle = rule;
    ctx.fillStyle = muted;
    ctx.font = "14px sans-serif";
    ctx.beginPath();
    ctx.moveTo(padL, y(0));
    ctx.lineTo(w - padR, y(0));
    ctx.stroke();
    ctx.fillText(num(max, 1), 2, y(max) + 4);
    ctx.fillText(num(min, 1), 2, y(min));
    function line(key, color) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      var started = false;
      rows.forEach(function (r, i) {
        if (typeof r[key] !== "number") return;
        var xx = x(i), yy = y(r[key]);
        if (!started) { ctx.moveTo(xx, yy); started = true; } else ctx.lineTo(xx, yy);
      });
      ctx.stroke();
    }
    line("headlineYoy", a);
    line("coreYoy", b);
    ctx.fillStyle = muted;
    ctx.fillText(rows[0].period || "", padL, h - 6);
    var right = rows[rows.length - 1].period || "";
    ctx.fillText(right, Math.max(padL, w - padR - 72), h - 6);
  }
  function bind(rootEl, model) {
    var canvas = rootEl.querySelector("#c103-canvas");
    var live = rootEl.querySelector("#c103-live");
    var read = rootEl.querySelector("#c103-read");
    var trend = model.trend || [];
    var index = trend.length - 1;
    function paint() { draw(canvas, trend); }
    function speak(fromUser) {
      var row = trend[index];
      if (!row) return;
      var text = (row.periodLabel || row.period || "Month") + ". Headline year change " + (typeof row.headlineYoy === "number" ? pct(row.headlineYoy) : "not loaded") + ". Core year change " + (typeof row.coreYoy === "number" ? pct(row.coreYoy) : "not loaded") + ".";
      if (read) read.textContent = text;
      if (fromUser && live) live.textContent = text;
    }
    if (canvas) {
      canvas.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" && e.key !== "Home" && e.key !== "End") return;
        e.preventDefault();
        if (e.key === "ArrowLeft") index -= 1;
        if (e.key === "ArrowRight") index += 1;
        if (e.key === "Home") index = 0;
        if (e.key === "End") index = trend.length - 1;
        if (index < 0) index = 0;
        if (index >= trend.length) index = trend.length - 1;
        speak(true);
      });
    }
    var btn = rootEl.querySelector("[data-c103-dismiss]");
    if (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-c103-dismiss");
        fetch("/api/c103/notice/dismiss", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ releaseKey: key })
        }).then(function () {
          var box = btn.closest(".c103-banner");
          if (box) box.remove();
        }).catch(function () {});
      });
    }
    var left = rootEl.querySelector("[data-c103-left]");
    if (left) {
      var target = Date.parse(left.getAttribute("data-c103-left"));
      var timer = setInterval(function () {
        if (!isFinite(target)) return;
        var ms = Math.max(0, target - Date.now());
        var days = Math.floor(ms / 86400000);
        ms -= days * 86400000;
        var hours = Math.floor(ms / 3600000);
        ms -= hours * 3600000;
        var minutes = Math.floor(ms / 60000);
        left.textContent = days + "d " + hours + "h " + minutes + "m";
      }, 30000);
      root.addEventListener("pagehide", function () { clearInterval(timer); }, { once: true });
    }
    paint();
    speak(false);
    if (typeof ResizeObserver === "function" && canvas) {
      var ro = new ResizeObserver(function () { paint(); });
      ro.observe(canvas);
    }
    if (typeof MutationObserver === "function") {
      var mo = new MutationObserver(function () { paint(); });
      mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-theme"] });
    }
    try {
      var mq = root.matchMedia && root.matchMedia("(prefers-color-scheme: dark)");
      if (mq && mq.addEventListener) mq.addEventListener("change", paint);
    } catch (e) {}
  }
  function mount(el) {
    if (!el) return;
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    function show(model) {
      el.innerHTML = render(model);
      el.setAttribute("aria-busy", "false");
      bind(el, model || {});
    }
    function fail() {
      show({ statusNote: "not loaded yet", source: "Source: U.S. Bureau of Labor Statistics", access: "free" });
    }
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); fail(); }, 12000);
    function pull(attempt) {
      fetch("/api/c103/cpi", { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: "application/json" } }).then(function (r) {
        if (!r.ok) throw new Error("http");
        return r.json();
      }).then(function (model) {
        clearTimeout(timer);
        show(model);
        if (attempt === 0 && model && model.cacheState === "cold") {
          setTimeout(function () { if (ctrl && ctrl.signal && ctrl.signal.aborted) return; pull(1); }, 1500);
        }
      }).catch(function () {
        clearTimeout(timer);
        if (el.getAttribute("aria-busy") === "false" && el.querySelector(".c103")) return;
        fail();
      });
    }
    pull(0);
  }
  root.c103ui = { render: render, mount: mount, draw: draw };
})(typeof globalThis !== "undefined" ? globalThis : this);
