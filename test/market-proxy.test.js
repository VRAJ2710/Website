const assert = require("node:assert/strict");
const test = require("node:test");
const {
  BoundedTtlCache,
  FixedWindowRateLimiter,
  normalizeCoinGeckoPath,
  normalizeTwelveDataSymbols,
  normalizeTwelveDataQuotes,
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

test("RSS routes resolve only the fixed approved HTTPS feeds", () => {
  assert.equal(approvedRssFeedUrl("f0"), "https://feeds.bbci.co.uk/news/business/rss.xml");
  assert.equal(approvedRssFeedUrl("f25"), "https://feeds.npr.org/1004/rss.xml");
  assert.equal(approvedRssFeedUrl("f26"), null);
  assert.equal(approvedRssFeedUrl("http://169.254.169.254/latest/meta-data"), null);
  assert.equal(approvedRssFeedUrl(undefined), null);
});

test("Twelve Data access is limited to the core stock and FX tape", () => {
  assert.deepEqual(
    normalizeTwelveDataSymbols(["EUR/USD", "AAPL", "AAPL", "GC=F", "https://example.com"]),
    ["AAPL", "EUR/USD"],
  );
  assert.deepEqual(normalizeTwelveDataSymbols("AAPL"), []);
});

test("Twelve Data payloads are normalized without trusting arbitrary symbols", () => {
  const quotes = normalizeTwelveDataQuotes({
    AAPL: {
      close: "311.78", previous_close: "309.35", percent_change: "0.7855", change: "2.43",
      name: "Apple Inc.", exchange: "NASDAQ", currency: "USD", last_quote_at: 1787578980,
    },
    "GC=F": { close: "4727.8", percent_change: "1.2" },
    NVDA: { close: "not-a-number" },
  });
  assert.deepEqual(quotes, {
    AAPL: {
      p: 311.78, c: 0.7855, prev: 309.35, change: 2.43,
      name: "Apple Inc.", exchange: "NASDAQ", currency: "USD", ts: 1787578980,
    },
  });
});