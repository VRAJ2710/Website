"use strict";

/**
 * Shared feed-status rules for the desk bootstrap.
 * A quote that arrived this session is counted. "AWAITING FEED" is only the
 * pre-completion placeholder. After the fetch settles with nothing counted,
 * the shell must say FEED DEGRADED.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.FeedStatus = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const COUNTED_STATUSES = Object.freeze([
    "live", "closed", "rth-close", "extended", "cached", "delayed", "stale", "proxy",
  ]);

  function emptyCounts() {
    return {
      live: 0, closed: 0, "rth-close": 0, extended: 0,
      cached: 0, delayed: 0, stale: 0, proxy: 0, unavailable: 0,
    };
  }

  function quoteStatusCounts(statuses) {
    const counts = emptyCounts();
    (statuses || []).forEach(status => {
      const key = Object.prototype.hasOwnProperty.call(counts, status) ? status : "unavailable";
      counts[key] += 1;
    });
    return counts;
  }

  function quoteStatusSummary(statuses, options) {
    const counts = quoteStatusCounts(statuses);
    const includeUnavailable = options && options.includeUnavailable === true;
    const keys = includeUnavailable ? COUNTED_STATUSES.concat(["unavailable"]) : COUNTED_STATUSES;
    const parts = keys.filter(key => counts[key] > 0).map(key => counts[key] + " " + key.toUpperCase());
    if (parts.length) return parts.join(" · ");
    if (options && options.fetchSettled) return "FEED DEGRADED";
    return "AWAITING FEED";
  }

  function providerTimestampMs(ts) {
    const n = Number(ts);
    if (!Number.isFinite(n) || n <= 0) return null;
    return n < 10_000_000_000 ? n * 1000 : n;
  }

  /** Accept Yahoo `{p,c,prev}` and Finnhub `{c,dp,pc}` quote objects. */
  function coerceQuote(q) {
    if (!q || typeof q !== "object") return null;
    if (typeof q.p === "number" && Number.isFinite(q.p) && q.p > 0) return q;
    if (typeof q.c === "number" && Number.isFinite(q.c) && q.c > 0 && ("dp" in q || "pc" in q)) {
      return {
        p: q.c,
        c: typeof q.dp === "number" && Number.isFinite(q.dp) ? q.dp : 0,
        prev: typeof q.pc === "number" && q.pc > 0 ? q.pc : q.c,
        ts: q.t,
      };
    }
    return null;
  }

  function referencePrintAllowed(meta, price) {
    if (!(typeof price === "number" && Number.isFinite(price) && price > 0)) return false;
    if (!meta || meta.status === "unavailable") return false;
    return true;
  }

  /**
   * Stale means this client stopped receiving, not that the exchange print
   * is the previous cash close. Provider time is display-only (`asOf`).
   */
  function classifySyncedQuote(input) {
    const src = input.src || "yahoo";
    const nowMs = input.now || Date.now();
    const receiptMs = input.receiptMs || nowMs;
    const providerMs = input.providerMs || receiptMs;
    const proxy = !!input.proxy
      || src.indexOf("gold-api") === 0
      || src === "frankfurter-ecb"
      || src === "open-exchange-rate-api";
    let status = "delayed";
    let label = "DELAYED";
    if (proxy) {
      status = "proxy";
      label = src.indexOf("gold-api") === 0 ? "SPOT PROXY" : "PROXY";
    } else if (input.session === "post" || input.session === "pre" || input.session === "otc" || input.session === "fullday") {
      status = "extended";
      label = input.session === "post" ? "AH" : input.session === "pre" ? "PRE" : "EXT";
    } else if (!input.continuous && input.marketClosed) {
      status = "rth-close";
      label = "RTH CLOSE";
    } else if (src === "coingecko") {
      status = "live";
      label = "LIVE·CG";
    } else if (src === "twelve-data") {
      status = "live";
      label = "LIVE·TD";
    } else if (src === "session-cache") {
      status = "cached";
      label = "CACHED";
    } else if (src === "finnhub") {
      status = "delayed";
      label = "DELAYED·FH";
    }
    const staleAfter = src === "twelve-data" ? 16 * 60 * 1000
      : src === "coingecko" ? 10 * 60 * 1000
      : 30 * 60 * 1000;
    const ageMs = nowMs - receiptMs;
    if (ageMs > staleAfter && status !== "cached") {
      status = "stale";
      label = proxy ? "STALE·PROXY" : "STALE";
    }
    return { status, label, asOf: providerMs, ageMs };
  }

  function yahooRequestSymbols(tickers, map) {
    return [...new Set((tickers || []).map(tk => (map && map[tk]) || tk).filter(Boolean))];
  }

  function quoteForTicker(payload, ticker, map) {
    if (!payload || typeof payload !== "object") return null;
    const wire = (map && map[ticker]) || ticker;
    return coerceQuote(payload[wire] || payload[ticker]);
  }

  function shellLabel(kind, state) {
    if (kind === "markets") {
      if (state.paused) return "Paused";
      if (state.fetching && !state.synced) return "Fetching";
      if (state.synced) return state.summary || (state.synced + " synced");
      if (state.settled) return "FEED DEGRADED";
      return "Fetching";
    }
    if (state.fetching && !state.headlines) return "AWAITING FEED";
    if (state.headlines) return "UPDATED";
    if (state.settled) return "NEWS DEGRADED";
    return "AWAITING FEED";
  }

  return {
    COUNTED_STATUSES,
    quoteStatusCounts,
    quoteStatusSummary,
    providerTimestampMs,
    coerceQuote,
    referencePrintAllowed,
    classifySyncedQuote,
    yahooRequestSymbols,
    quoteForTicker,
    shellLabel,
  };
});
