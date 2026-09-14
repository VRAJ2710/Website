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
  looksLikeUsListedEquity,
  yahooChartUrl,
  normalizeYahooChartResult,
  quoteProvenance,
  isContinuousDeskTicker,
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

test("Twelve Data never marks gold, FX, or crypto market-closed from equity flags", () => {
  const timestamp = Math.floor(Date.now() / 1000);
  const quotes = normalizeTwelveDataQuotes({
    "XAU/USD": { close: "4300", previous_close: "4290", timestamp, is_market_open: false },
    "BTC/USD": { close: "77000", previous_close: "76000", timestamp, status: "closed" },
    "ETH/USD": { close: "4100", previous_close: "4000", timestamp, market_open: false },
    "EUR/USD": { close: "1.16", previous_close: "1.15", timestamp, is_market_open: "false" },
    AAPL: { close: "200", previous_close: "199", timestamp, is_market_open: false },
  });
  assert.equal(quotes["XAU/USD"].marketClosed, undefined);
  assert.equal(quotes["BTC/USD"].marketClosed, undefined);
  assert.equal(quotes["ETH/USD"].marketClosed, undefined);
  assert.equal(quotes["EUR/USD"].marketClosed, undefined);
  assert.equal(quotes.AAPL.marketClosed, true);
});

test("Yahoo chart URLs request pre/post and only use 1m bars for listed US names", () => {
  assert.equal(looksLikeUsListedEquity("AAPL"), true);
  assert.equal(looksLikeUsListedEquity("SPY"), true);
  assert.equal(looksLikeUsListedEquity("BRK.B"), true);
  assert.equal(looksLikeUsListedEquity("GC=F"), false);
  assert.equal(looksLikeUsListedEquity("BTC-USD"), false);
  assert.equal(looksLikeUsListedEquity("EURUSD=X"), false);
  assert.equal(looksLikeUsListedEquity("^GSPC"), false);
  assert.match(yahooChartUrl("AAPL"), /includePrePost=true/);
  assert.match(yahooChartUrl("AAPL"), /interval=1m/);
  assert.match(yahooChartUrl("GC=F"), /includePrePost=true/);
  assert.match(yahooChartUrl("GC=F"), /interval=1d/);
});

test("Yahoo quote prefers post then pre then validated fullday then regular outside RTH", () => {
  const now = 1_789_176_000_000; // after Friday post close
  const periods = {
    pre: { start: 1789113600, end: 1789133400 },
    regular: { start: 1789133400, end: 1789156800 },
    post: { start: 1789156800, end: 1789171200 },
  };
  const post = normalizeYahooChartResult({
    meta: {
      symbol: "AAPL",
      regularMarketPrice: 332.27,
      regularMarketTime: 1789156801,
      regularMarketChangePercent: 1.74,
      previousClose: 326.57,
      chartPreviousClose: 326.57,
      postMarketPrice: 332.55,
      postMarketChange: 0.28,
      postMarketChangePercent: 0.08,
      postMarketTime: 1789171199,
      hasPrePostMarketData: true,
      currentTradingPeriod: periods,
      currency: "USD",
      exchangeName: "NMS",
      longName: "Apple Inc.",
    },
  }, now);
  assert.equal(post.session, "post");
  assert.equal(post.p, 332.55);
  assert.equal(post.marketClosed, undefined);

  const pre = normalizeYahooChartResult({
    meta: {
      symbol: "AAPL",
      regularMarketPrice: 332.27,
      regularMarketTime: 1789156801,
      previousClose: 326.57,
      preMarketPrice: 333.10,
      preMarketChange: 0.83,
      preMarketChangePercent: 0.25,
      preMarketTime: 1789130000,
      hasPrePostMarketData: true,
      currentTradingPeriod: periods,
      currency: "USD",
      exchangeName: "NMS",
    },
  }, now);
  assert.equal(pre.session, "pre");
  assert.equal(pre.p, 333.10);

  const lastBar = normalizeYahooChartResult({
    meta: {
      symbol: "SPY",
      regularMarketPrice: 764.29,
      regularMarketTime: 1789156800,
      previousClose: 757.83,
      fulldayPrice: 760.82,
      fulldayChange: 6.46,
      fulldayChangePercent: 0.852,
      hasPrePostMarketData: true,
      currentTradingPeriod: periods,
      currency: "USD",
      exchangeName: "PCX",
    },
    timestamp: [1789156800, 1789171140],
    indicators: { quote: [{ close: [764.29, 764.41] }] },
  }, now);
  assert.equal(lastBar.session, "post");
  assert.equal(lastBar.p, 764.41);

  const weekendFulldayQuirk = normalizeYahooChartResult({
    meta: {
      symbol: "AAPL",
      regularMarketPrice: 332.27,
      regularMarketTime: 1789156801,
      previousClose: 326.57,
      chartPreviousClose: 326.57,
      fulldayPrice: 328.59,
      fulldayChange: 5.7,
      fulldayChangePercent: 1.745,
      hasPrePostMarketData: true,
      currentTradingPeriod: periods,
      currency: "USD",
      exchangeName: "NMS",
    },
  }, now);
  assert.equal(weekendFulldayQuirk.session, "regular");
  assert.equal(weekendFulldayQuirk.p, 332.27);
  assert.equal(weekendFulldayQuirk.marketClosed, true);

  const otc = normalizeYahooChartResult({
    meta: {
      symbol: "ABCD",
      regularMarketPrice: 2.5,
      regularMarketTime: 1789156800,
      previousClose: 2.4,
      postMarketPrice: 2.55,
      postMarketTime: 1789160000,
      hasPrePostMarketData: true,
      currentTradingPeriod: periods,
      currency: "USD",
      exchangeName: "PNK",
      fullExchangeName: "Other OTC",
    },
  }, now);
  assert.equal(otc.session, "otc");
  assert.equal(otc.p, 2.55);

  const gold = normalizeYahooChartResult({
    meta: {
      symbol: "GC=F",
      regularMarketPrice: 4376.9,
      regularMarketTime: 1789356138,
      previousClose: 4393.9,
      fulldayPrice: 4376.9,
      hasPrePostMarketData: false,
      currency: "USD",
      exchangeName: "CMX",
    },
  }, now);
  assert.equal(gold.session, "regular");
  assert.equal(gold.marketClosed, undefined);
  assert.equal(gold.p, 4376.9);
});

test("Yahoo extended prints can replace a closed Twelve Data RTH quote, but not gold/crypto", () => {
  const now = 1_789_353_976_700;
  const windowMs = 16 * 60 * 1000;
  assert.equal(canReplaceLiveQuote({
    ticker: "AAPL", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "yahoo", currentMarketClosed: true, incomingSession: "post",
    now, windowMs,
  }), true);
  assert.equal(canReplaceLiveQuote({
    ticker: "SPY", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "yahoo", currentMarketClosed: true, incomingSession: "regular",
    now, windowMs,
  }), false);
  assert.equal(canReplaceLiveQuote({
    ticker: "AAPL", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "yahoo", currentMarketClosed: true, incomingSession: null,
    now, windowMs,
  }), true);
  assert.equal(canReplaceLiveQuote({
    ticker: "XAU", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "yahoo", currentMarketClosed: true, incomingSession: "post",
    now, windowMs,
  }), false);
  assert.equal(canReplaceLiveQuote({
    ticker: "BTC", currentSrc: "twelve-data", currentTs: now - 60_000,
    incomingSrc: "coingecko", currentMarketClosed: true, incomingSession: "post",
    now, windowMs,
  }), false);
  assert.equal(isContinuousDeskTicker("ETH"), true);
  assert.equal(isContinuousDeskTicker("AAPL"), false);
});

test("quote provenance keeps a number on the tape with EXT·HRS or RTH CLOSE, never MARKET CLOSED", () => {
  assert.deepEqual(quoteProvenance({
    ticker: "AAPL", src: "yahoo", session: "post",
  }), {
    status: "extended",
    label: "AH",
    detail: "Yahoo after-hours / post-RTH print — delayed retail feed, not a live NASDAQ/NYSE tape",
    trusted: true,
  });
  assert.equal(quoteProvenance({ ticker: "SPY", src: "yahoo", session: "fullday" }).label, "EXT·HRS");
  assert.deepEqual(quoteProvenance({
    ticker: "AAPL", src: "twelve-data", marketClosed: true, ageMs: 48 * 3600 * 1000, staleAfterMs: 16 * 60 * 1000,
  }), {
    status: "rth-close",
    label: "RTH CLOSE",
    detail: "Regular US cash session closed — last RTH print retained. No extended/OTC print applied.",
    trusted: true,
  });
  const gold = quoteProvenance({
    ticker: "XAU", src: "twelve-data", marketClosed: true, session: "post",
  });
  assert.equal(gold.status, "live");
  assert.equal(gold.label, "LIVE·TD");
  assert.notEqual(gold.label, "MARKET CLOSED");
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
