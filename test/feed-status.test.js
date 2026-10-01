"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
  quoteStatusCounts,
  quoteStatusSummary,
  coerceQuote,
  referencePrintAllowed,
  classifySyncedQuote,
  yahooRequestSymbols,
  quoteForTicker,
  providerTimestampMs,
  shellLabel,
} = require("../feedStatus");
const { normalizeGoldApiQuote, synthesizeDxyFromUsdRates } = require("../marketProxy");

test("closed-session and proxy quotes count instead of collapsing to AWAITING FEED", () => {
  const counts = quoteStatusCounts(["rth-close", "extended", "proxy", "delayed"]);
  assert.equal(counts["rth-close"], 1);
  assert.equal(counts.extended, 1);
  assert.equal(counts.proxy, 1);
  assert.equal(counts.unavailable, 0);
  assert.equal(quoteStatusSummary(["rth-close", "proxy"]), "1 RTH-CLOSE · 1 PROXY");
});

test("a settled fetch with no counted quotes is FEED DEGRADED, not AWAITING FEED", () => {
  assert.equal(quoteStatusSummary(["unavailable", "unavailable"]), "AWAITING FEED");
  assert.equal(
    quoteStatusSummary(["unavailable"], { fetchSettled: true }),
    "FEED DEGRADED",
  );
  assert.equal(shellLabel("markets", { fetching: true, synced: 0 }), "Fetching");
  assert.equal(shellLabel("markets", { settled: true, synced: 0, fetching: false }), "FEED DEGRADED");
  assert.equal(shellLabel("news", { fetching: false, headlines: 0, settled: true }), "NEWS DEGRADED");
  assert.equal(shellLabel("news", { fetching: false, headlines: 4, settled: true }), "UPDATED");
});

test("Yahoo wire symbols are requested and mapped back onto desk tickers", () => {
  const map = { SPX: "^GSPC", GBPUSD: "GBPUSD=X", COPPER: "HG=F", AAPL: "AAPL" };
  assert.deepEqual(yahooRequestSymbols(["SPX", "AAPL", "COPPER"], map), ["^GSPC", "AAPL", "HG=F"]);
  const payload = {
    "^GSPC": { p: 5200, c: -0.4, prev: 5220, ts: 1_700_000_000 },
    "HG=F": { p: 4.2, c: 0.1, prev: 4.1 },
  };
  assert.equal(quoteForTicker(payload, "SPX", map).p, 5200);
  assert.equal(quoteForTicker(payload, "COPPER", map).p, 4.2);
  assert.equal(quoteForTicker(payload, "GBPUSD", map), null);
  assert.equal(quoteForTicker({ GBPUSD: {} }, "GBPUSD", map), null);
});

test("Finnhub quote shape and proxy prints stay usable", () => {
  const finnhub = coerceQuote({ c: 201.5, d: 1.2, dp: 0.6, pc: 200.3 });
  assert.equal(finnhub.p, 201.5);
  assert.equal(finnhub.c, 0.6);
  const classified = classifySyncedQuote({
    src: "yahoo",
    marketClosed: true,
    providerMs: Date.now() - 11 * 60 * 60 * 1000,
    receiptMs: Date.now(),
    now: Date.now(),
  });
  assert.equal(classified.status, "rth-close");
  const proxy = classifySyncedQuote({
    src: "open-exchange-rate-api",
    proxy: true,
    receiptMs: Date.now(),
    providerMs: Date.now() - 7 * 60 * 60 * 1000,
    now: Date.now(),
  });
  assert.equal(proxy.status, "proxy");
  assert.equal(referencePrintAllowed(proxy, 101.38), true);
  assert.equal(referencePrintAllowed({ status: "unavailable" }, 101.38), false);
});

test("provider timestamps in seconds are not treated as milliseconds", () => {
  assert.equal(providerTimestampMs(1_790_798_401), 1_790_798_401_000);
  assert.equal(providerTimestampMs(1_790_840_195_466), 1_790_840_195_466);
});

test("one rejected quote batch does not drop an already coerced sibling", async () => {
  const batches = await Promise.allSettled([
    Promise.resolve(quoteForTicker({ AAPL: { p: 100, c: 1, prev: 99 } }, "AAPL", { AAPL: "AAPL" })),
    Promise.reject(new Error("upstream timeout")),
  ]);
  const hits = batches.filter(result => result.status === "fulfilled" && result.value).map(result => result.value.p);
  assert.deepEqual(hits, [100]);
});

test("reference proxies expose the quote shape the desk applies", () => {
  const gold = normalizeGoldApiQuote({ price: 4164.6, currency: "USD", updatedAt: "2026-10-01T07:30:00.000Z" });
  assert.equal(gold.proxy, true);
  assert.equal(gold.source, "gold-api-spot-proxy");
  assert.ok(gold.p > 4000);
  const dxy = synthesizeDxyFromUsdRates({
    EUR: 0.88, GBP: 0.75, JPY: 149, CAD: 1.36, SEK: 10.4, CHF: 0.85,
  }, "2026-10-01");
  assert.equal(dxy.proxy, true);
  assert.equal(dxy.name, "Synthetic Dollar Index (proxy)");
  assert.ok(dxy.p > 50 && dxy.p < 200);
  assert.equal(referencePrintAllowed({ status: "proxy" }, dxy.p), true);
});
