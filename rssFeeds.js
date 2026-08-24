"use strict";

const RSS_FEED_URLS = Object.freeze({
  f0: "https://feeds.bbci.co.uk/news/business/rss.xml",
  f1: "https://www.cnbc.com/id/100003114/device/rss/rss.html",
  f2: "https://www.cnbc.com/id/20910258/device/rss/rss.html",
  f3: "https://www.cnbc.com/id/19854910/device/rss/rss.html",
  f4: "https://feeds.marketwatch.com/marketwatch/topstories",
  f5: "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC,SPY,QQQ,IWM&region=US&lang=en-US",
  f6: "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
  f7: "https://www.theguardian.com/business/rss",
  f8: "https://www.investing.com/rss/news_14.rss",
  f9: "https://www.investing.com/rss/news_1.rss",
  f10: "https://www.investing.com/rss/news_25.rss",
  f11: "https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL=F,GC=F,SI=F,NG=F&region=US&lang=en-US",
  f12: "https://www.coindesk.com/arc/outboundfeeds/rss/",
  f13: "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EFTSE,%5EGDAXI,%5EN225,%5EHSI&region=US&lang=en-US",
  f14: "https://feeds.bbci.co.uk/news/world/rss.xml",
  f15: "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
  f16: "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
  f17: "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
  f18: "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
  f19: "https://www.theguardian.com/world/rss",
  f20: "https://www.theguardian.com/uk-news/rss",
  f21: "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
  f22: "https://rss.nytimes.com/services/xml/rss/nyt/Europe.xml",
  f23: "https://rss.nytimes.com/services/xml/rss/nyt/AsiaPacific.xml",
  f24: "https://www.aljazeera.com/xml/rss/all.xml",
  f25: "https://feeds.npr.org/1004/rss.xml",
});

function approvedRssFeedUrl(feedId) {
  return typeof feedId === "string" && /^f\d{1,2}$/.test(feedId)
    ? RSS_FEED_URLS[feedId] || null
    : null;
}

module.exports = { RSS_FEED_URLS, approvedRssFeedUrl };