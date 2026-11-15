// chat102r6 market-reference cache. Append-only. The GET returns the last good body and does not wait on feeds.
(function () {
  if (typeof marketReferenceQuotesSWR !== "function") return;
  var c102r6Orig = marketReferenceQuotesSWR;
  var c102r6Last = null;
  var c102r6At = 0;
  var c102r6Flight = null;
  var FEEDS = ["XAU", "DXY", "DXY_FX", "US10Y", "regime", "sessionSummary"];
  var TEXT = { label: 1, name: 1, text: 1, note: 1, source: 1, feedLabel: 1, narrative: 1, method: 1, changeNote: 1, displayChangeLabel: 1, basis: 1 };
  var SKIP = { symbol: 1, symbols: 1, id: 1, wire: 1 };

  function scrubText(s) {
    if (typeof c95Plain === "function") {
      try { return c95Plain(s); } catch (e) {}
    }
    return String(s)
      .replace(/\bGC=F\b/g, "gold futures")
      .replace(/\bDX-Y\.NYB\b/g, "the ICE dollar index")
      .replace(/\^TNX\b/g, "the US 10-year yield")
      .replace(/\b[A-Z]{1,5}=[FX]\b/g, "")
      .replace(/\b[A-Z]{3,6}-USD\b/g, "")
      .replace(/\(\s*\)/g, "")
      .replace(/ {2,}/g, " ")
      .replace(/\s+([,.;:])/g, "$1")
      .trim();
  }
  function scrubObj(value) {
    if (Array.isArray(value)) return value.map(function (item) { return item && typeof item === "object" ? scrubObj(item) : item; });
    var out = {};
    Object.keys(value).forEach(function (k) {
      var v = value[k];
      if (SKIP[k]) { out[k] = v; return; }
      if (typeof v === "string" && TEXT[k]) out[k] = scrubText(v);
      else if (v && typeof v === "object") out[k] = scrubObj(v);
      else out[k] = v;
    });
    return out;
  }
  function ukFrom(iso) {
    var ms = Date.parse(iso);
    if (!isFinite(ms)) return "";
    try {
      return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ms)) + " UK";
    } catch (e) { return ""; }
  }
  function whenOf(row) {
    if (!row || typeof row !== "object") return "";
    if (row.asOfUk) return row.asOfUk;
    if (row.checkedAtUk) return row.checkedAtUk;
    if (row.computedAtUk) return row.computedAtUk;
    if (row.asOf) return ukFrom(row.asOf);
    return "";
  }
  function storedNote(row) {
    var when = whenOf(row);
    return "Stored reading from " + (when || "the last good response") + ". It is not a new print.";
  }
  function good(key, row) {
    if (!row || typeof row !== "object") return false;
    if (key === "XAU" || key === "DXY" || key === "DXY_FX") return typeof row.p === "number" && isFinite(row.p);
    if (key === "US10Y") return typeof row.value === "number" && isFinite(row.value);
    if (key === "regime") return row.available === true || (typeof row.score === "number" && !!row.regime);
    if (key === "sessionSummary") return typeof row.text === "string" && row.text.length > 0;
    return false;
  }
  function carry(row) {
    var copy = Object.assign({}, row);
    copy.note = storedNote(row);
    copy.stale = true;
    copy.kept = true;
    return copy;
  }
  function anyGood(body) {
    return !!body && FEEDS.some(function (k) { return good(k, body[k]); });
  }
  function merge(prev, next) {
    var out = next && typeof next === "object" ? Object.assign({}, next) : {};
    if (prev) {
      FEEDS.forEach(function (k) {
        if (!good(k, out[k]) && good(k, prev[k])) out[k] = carry(prev[k]);
      });
      if (good("XAU", out.XAU) && prev.XAU && !(out.XAU.futures && typeof out.XAU.futures.price === "number") && prev.XAU.futures && typeof prev.XAU.futures.price === "number") {
        out.XAU = Object.assign({}, out.XAU, { futures: carry(prev.XAU.futures) });
        if (prev.XAU.futuresChange && typeof prev.XAU.futuresChange.price === "number" && !(out.XAU.futuresChange && typeof out.XAU.futuresChange.price === "number")) {
          out.XAU.futuresChange = carry(prev.XAU.futuresChange);
        }
      }
    }
    out.fetchedAt = Date.now();
    return scrubObj(out);
  }
  function empty() {
    var note = "No stored reading yet. No number was filled in.";
    return {
      XAU: { p: null, c: null, label: "Gold spot", name: "Gold spot", source: "gold-api.com", status: "unavailable", note: note, changeAvailable: false },
      DXY: { p: null, label: "US dollar index", name: "US dollar index", status: "unavailable", note: note, changeAvailable: false },
      DXY_FX: { p: null, label: "Dispatch FX basket", name: "Dispatch FX basket", status: "unavailable", note: note },
      US10Y: { label: "US 10-year yield", value: null, unit: "percent", status: "unavailable", note: note },
      regime: { available: false, regime: null, score: null, label: null, note: note },
      sessionSummary: { text: "", tradingNow: null, note: note },
      fetchedAt: Date.now()
    };
  }
  function limitedFetch(prev, url, opts) {
    var href = typeof url === "string" ? url : (url && url.url) || "";
    var ms = /gold-api\.com/i.test(href) ? 3000 : 2000;
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    var timer = setTimeout(function () { try { if (ctrl) ctrl.abort(); } catch (e) {} }, ms);
    var next = Object.assign({}, opts || {});
    if (ctrl) next.signal = ctrl.signal;
    return Promise.resolve(prev(url, next)).finally(function () { clearTimeout(timer); });
  }
  var c102r6PrevFetch = null;
  function refreshBound() {
    if (c102r6Flight) return c102r6Flight;
    c102r6Flight = Promise.resolve().then(function () {
      c102r6PrevFetch = globalThis.fetch;
      if (typeof c102r6PrevFetch === "function") {
        globalThis.fetch = function (url, opts) { return limitedFetch(c102r6PrevFetch, url, opts); };
      }
      return Promise.resolve(c102r6Orig()).then(function (body) {
        var merged = merge(c102r6Last, body);
        if (anyGood(merged)) {
          c102r6Last = merged;
          c102r6At = Date.now();
        }
      });
    }).catch(function () {}).finally(function () {
      if (typeof c102r6PrevFetch === "function") globalThis.fetch = c102r6PrevFetch;
      c102r6Flight = null;
    });
    return c102r6Flight;
  };
  function snapshot(body) {
    var out = Object.assign({}, body);
    FEEDS.forEach(function (k) {
      if (out[k] && typeof out[k] === "object" && !Array.isArray(out[k])) out[k] = Object.assign({}, out[k]);
    });
    return out;
  }
  function freshFor() {
    return typeof C102R6_TTL === "number" ? C102R6_TTL : 60000;
  }
  function fast() {
    if (!c102r6Last || Date.now() - c102r6At >= freshFor()) refreshBound();
    if (c102r6Last) return Promise.resolve(snapshot(c102r6Last));
    return Promise.resolve(empty());
  }
  try { marketReferenceQuotesSWR = fast; } catch (e) {}
  try { globalThis.marketReferenceQuotesSWR = fast; } catch (e2) {}
  if (typeof bb5gPublish === "function" && !bb5gPublish.__c102r6) {
    var prevPub = bb5gPublish;
    var wrapped = function (data) {
      var out = prevPub.apply(this, arguments);
      if (!data || !out || typeof out !== "object" || Array.isArray(out)) return out;
      FEEDS.forEach(function (k) {
        if (data[k] && data[k].kept && out[k] && typeof out[k] === "object") {
          out[k].note = data[k].note;
          out[k].stale = true;
          out[k].kept = true;
        }
      });
      return out;
    };
    wrapped.__c102r6 = 1;
    try { bb5gPublish = wrapped; } catch (e3) {}
  }
  if (typeof C102R6_NO_WARM === "undefined") {
    try {
      var warm = setTimeout(function () { refreshBound(); }, 50);
      if (warm && typeof warm.unref === "function") warm.unref();
    } catch (e4) {}
  }
})();
