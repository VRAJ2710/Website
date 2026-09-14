const assert = require("node:assert/strict");
const test = require("node:test");
const {
  BoundedTtlCache,
  FixedWindowRateLimiter,
  FixedWindowCreditLimiter,
  normalizeCoinGeckoPath,
  TWELVE_DATA_ALLOWED_SYMBOLS,
  TWELVE_DATA_DAILY_CREDIT_LIMIT,
  canonicalTwelveDataSymbols,
  normalizeTwelveDataSymbols,
  normalizeTwelveDataQuotes,
  twelveDataQuoteCoverage,
  normalizeGoldApiQuote,
  synthesizeDxyFromUsdRates,
  canReplaceLiveQuote,
  providerTimestampMs,
} = require("../marketProxy");
const { approvedRssFeedUrl } = require("../rssFeeds");

test("normalizes only the CoinGecko request shapes used by the terminal", () => {
  assert.equal(
    normalizeCoinGeckoPath("/simple/price?vs_currencies=usd&include_24hr_change=true&ids=bitcoin,ethereum"),
    "/simple/price?ids=bitcoin%2Cethereum&vs_currencies=usd&include_24hr_change=true",
  );
  assert.equal(
    normalizeCoinGeckoPath("/coins/bitcoin/market_chart?vs_currency=usd&days=7"),
    "/coins/bitcoin/market_chart?vs_currency=usd&days=7",
  );
  assert.equal(normalizeCoinGeckoPath("/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=1h,24h,7d").startsWith("/coins/markets?"), true);
  assert.equal(normalizeCoinGeckoPath("/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&nonce=1"), null);
  assert.equal(normalizeCoinGeckoPath("/simple/price?ids=bitcoin&vs_currencies=eur&include_24hr_change=true"), null);
  assert.equal(normalizeCoinGeckoPath("https://untrusted.example/path"), null);
});

test("cache expires entries and remains bounded by LRU entry and byte limits", () => {
  const cache = new BoundedTtlCache({ maxEntries: 2, maxBytes: 40 });
  cache.set("expired", { value: "a" }, 5, 0);
  assert.equal(cache.get("expired", 6), undefined);
  cache.set("first", { value: "a" }, 60, 10);
  cache.set("second", { value: "b" }, 60, 10);
  assert.deepEqual(cache.get("first", 10), { value: "a" });
  cache.set("third", { value: "c" }, 60, 10);
  assert.equal(cache.get("second", 10), undefined);
  assert.deepEqual(cache.get("first", 10), { value: "a" });
  assert.deepEqual(cache.get("third", 10), { value: "c" });
  assert.equal(cache.set("too-large", { value: "x".repeat(100) }, 60, 10), false);
  assert.ok(cache.entries.size <= 2);
  assert.ok(cache.bytes <= 40);
});

test("rate limiter caps request volume and bounds tracked clients", () => {
  const limiter = new FixedWindowRateLimiter({ limit: 2, windowMs: 50, maxKeys: 2 });
  assert.equal(limiter.allow("one", 0), true);
  assert.equal(limiter.allow("one", 0), true);
  assert.equal(limiter.allow("one", 0), false);
  assert.equal(limiter.allow("two", 0), true);
  assert.equal(limiter.allow("three", 0), true);
  assert.ok(limiter.windows.size <= 2);
  assert.equal(limiter.allow("one", 51), true);
});

test("credit limiter reserves each canonical quote request atomically", () => {
  const limiter = new FixedWindowCreditLimiter({ limit: 10, windowMs: 50, maxKeys: 1 });
  assert.equal(limiter.allow("core-tape", 8, 0), true);
  assert.equal(limiter.allow("core-tape", 3, 0), false);
  assert.equal(limiter.windows.get("core-tape").credits, 8);
  assert.equal(limiter.allow("core-tape", 2, 0), true);
  assert.equal(limiter.allow("core-tape", 1, 0), false);
  assert.equal(limiter.allow("core-tape", 10, 51), true);
});

test("the shared daily allowance stays bounded to the provider plan", () => {
  assert.equal(TWELVE_DATA_DAILY_CREDIT_LIMIT, 800);
  assert.equal(TWELVE_DATA_ALLOWED_SYMBOLS.length, 8);
  assert.equal(canonicalTwelveDataSymbols().length * 96, 768);
});

test("RSS routes resolve only the fixed approved HTTPS feeds", () => {
  assert.equal(approvedRssFeedUrl("f0"), "https://feeds.bbci.co.uk/news/business/rss.xml");
  assert.equal(approvedRssFeedUrl("f25"), "https://feeds.npr.org/1004/rss.xml");
  assert.equal(approvedRssFeedUrl("f26"), null);
  assert.equal(approvedRssFeedUrl("http://169.254.169.254/latest/meta-data"), null);
  assert.equal(approvedRssFeedUrl(undefined), null);
});

test("Twelve Data access is limited to the approved cross-asset tape", () => {
  assert.deepEqual(
    normalizeTwelveDataSymbols([
      "ETH/USD", "BTC/USD", "EUR/USD", "XAU/USD", "QQQ", "SPY",
      "NVDA", "AAPL", "AAPL", "GC=F", "MSFT", "https://example.com",
    ]),
    ["AAPL", "NVDA", "SPY", "QQQ", "XAU/USD", "EUR/USD", "BTC/USD", "ETH/USD"],
  );
  assert.deepEqual(normalizeTwelveDataSymbols("AAPL"), []);
  assert.deepEqual(canonicalTwelveDataSymbols(), [
    "AAPL", "NVDA", "SPY", "QQQ", "XAU/USD", "EUR/USD", "BTC/USD", "ETH/USD",
  ]);
});

test("Twelve Data payloads are normalized without trusting arbitrary symbols", () => {
  const quotes = normalizeTwelveDataQuotes({
    AAPL: {
      close: "311.78", previous_close: "309.35", percent_change: "0.7855", change: "2.43",
      name: "Apple Inc.", exchange: "NASDAQ", currency: "USD", last_quote_at: 1787578980,
    },
    "GC=F": { close: "4727.8", percent_change: "1.2", timestamp: 1787578980 },
    NVDA: { close: "not-a-number" },
    SPY: { close: "650.25", percent_change: "0.25" },
  });
  assert.deepEqual(quotes, {
    AAPL: {
      p: 311.78, c: 0.7855, prev: 309.35, change: 2.43,
      name: "Apple Inc.", exchange: "NASDAQ", currency: "USD", ts: 1787578980,
    },
  });
});

test("Twelve Data normalizes timestamped quotes across every approved asset class", () => {
  const timestamp = 1787578980;
  const payload = Object.fromEntries([
    ["AAPL", "200.10"],
    ["SPY", "650.25"],
    ["XAU/USD", "3650.40"],
    ["EUR/USD", "1.1825"],
    ["BTC/USD", "112500.00"],
    ["ETH/USD", "4100.00"],
    ["QQQ", "500.00"],
  ].map(([symbol, close]) => [symbol, {
    close, previous_close: close, percent_change: "0", change: "0", timestamp,
    name: symbol, exchange: "Twelve Data", currency: "USD",
  }]));
  const quotes = normalizeTwelveDataQuotes(payload);
  assert.deepEqual(Object.keys(quotes), ["AAPL", "SPY", "XAU/USD", "EUR/USD", "BTC/USD", "ETH/USD", "QQQ"]);
  for (const quote of Object.values(quotes)) assert.equal(quote.ts, timestamp);
});

test("Twelve Data normalization rejects missing and future provider timestamps", () => {
  const now = Date.now();
  const quotes = normalizeTwelveDataQuotes({
    AAPL: { close: "200" },
    NVDA: { close: "180", timestamp: Math.floor((now + 61_000) / 1000) },
    SPY: { close: "650", timestamp: Math.floor((now + 59_000) / 1000) },
  }, undefined, now);
  assert.deepEqual(Object.keys(quotes), ["SPY"]);
});

test("Twelve Data marks closed cash sessions without dropping the last print", () => {
  const timestamp = Math.floor(Date.now() / 1000);
  const quotes = normalizeTwelveDataQuotes({
    AAPL: {
      close: "200", previous_close: "199", timestamp, is_market_open: false,
      name: "Apple Inc.", exchange: "NASDAQ", currency: "USD",
    },
  });
  assert.equal(quotes.AAPL.marketClosed, true);
  assert.equal(quotes.AAPL.p, 200);
});

test("Twelve Data coverage records partial fresh batches without treating a closed market as a gap", () => {
  const timestamp = Math.floor(Date.now() / 1000);
  const coverage = twelveDataQuoteCoverage({
    AAPL: { close: "200", previous_close: "199", timestamp, is_market_open: true },
    NVDA: { close: "180", previous_close: "179", timestamp, is_market_open: false },
    SPY: { status: "closed" },
  }, ["AAPL", "NVDA", "SPY", "QQQ"], Date.now());
  assert.deepEqual(coverage.requestedSymbols, ["AAPL", "NVDA", "SPY", "QQQ"]);
  assert.deepEqual(coverage.returnedSymbols, ["AAPL", "NVDA"]);
  assert.deepEqual(coverage.missingSymbols, ["SPY", "QQQ"]);
  assert.deepEqual(coverage.marketClosedSymbols, ["SPY"]);
  assert.deepEqual(coverage.alertableMissingSymbols, ["QQQ"]);
});

test("provider timestamps convert seconds to milliseconds and reject the future", () => {
  assert.equal(providerTimestampMs(1787578980), 1787578980 * 1000);
  assert.equal(providerTimestampMs(1787578980000), 1787578980000);
  assert.equal(providerTimestampMs(Math.floor((Date.now() + 120_000) / 1000)), null);
  assert.equal(providerTimestampMs("not-a-time"), null);
});

test("gold-api payloads are labeled as spot proxies", () => {
  const quote = normalizeGoldApiQuote({
    price: 4331.799805,
    currency: "USD",
    updatedAt: "2026-09-14T03:02:06Z",
    name: "Gold",
    symbol: "XAU",
  });
  assert.equal(quote.p, 4331.799805);
  assert.equal(quote.source, "gold-api-spot-proxy");
  assert.equal(quote.proxy, true);
  assert.equal(quote.ts, Date.parse("2026-09-14T03:02:06Z") / 1000);
  assert.equal(normalizeGoldApiQuote({ price: 0 }), null);
});

test("fresh Twelve Data quotes are not overwritten by Yahoo or CoinGecko inside the cache window", () => {
  const now = 1_789_353_976_700;
  const windowMs = 16 * 60 * 1000;
  assert.equal(canReplaceLiveQuote({
    ticker: "XAU", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "yahoo", now, windowMs,
  }), false);
  assert.equal(canReplaceLiveQuote({
    ticker: "BTC", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "coingecko", now, windowMs,
  }), false);
  assert.equal(canReplaceLiveQuote({
    ticker: "XAU", currentSrc: "gold-api-spot-proxy", currentTs: now,
    incomingSrc: "yahoo", now, windowMs,
  }), false); // spot proxy beats delayed GC=F futures
  assert.equal(canReplaceLiveQuote({
    ticker: "XAU", currentSrc: "twelve-data", currentTs: now - windowMs - 1,
    incomingSrc: "yahoo", now, windowMs,
  }), true);
  assert.equal(canReplaceLiveQuote({
    ticker: "XAU", currentSrc: "gold-api-spot-proxy", currentTs: now,
    incomingSrc: "twelve-data", now, windowMs,
  }), true);
  assert.equal(canReplaceLiveQuote({
    ticker: "DXY", currentSrc: "yahoo", currentTs: now,
    incomingSrc: "frankfurter-ecb", now, windowMs,
  }), false);
});

test("Frankfurter USD rates synthesize an ICE-style DXY proxy", () => {
  const quote = synthesizeDxyFromUsdRates({
    CAD: 1.3858, CHF: 0.8153, EUR: 0.86266, GBP: 0.7403, JPY: 154.04, SEK: 9.694,
  }, "2026-09-11");
  assert.ok(quote);
  assert.equal(quote.source, "frankfurter-ecb");
  assert.equal(quote.proxy, true);
  assert.ok(Math.abs(quote.p - 99.1679) < 0.001);
  assert.equal(quote.ts, Date.parse("2026-09-11T00:00:00Z") / 1000);
  assert.equal(synthesizeDxyFromUsdRates({ EUR: 0 }, "2026-09-11"), null);
});
