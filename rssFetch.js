"use strict";

const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);
const MAX_RSS_REDIRECTS = 3;

function isPrivateHostname(hostname) {
  const host = String(hostname || "").toLowerCase().replace(/^\[|\]$/g, "");
  if (!host || host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local")) return true;
  if (host === "metadata.google.internal" || host === "0.0.0.0") return true;
  const match = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!match) return false;
  const parts = match.slice(1).map(Number);
  if (parts.some(part => part > 255)) return true;
  const [a, b] = parts;
  return a === 10 || a === 127 || a === 0
    || (a === 169 && b === 254)
    || (a === 172 && b >= 16 && b <= 31)
    || (a === 192 && b === 168)
    || (a === 100 && b >= 64 && b <= 127);
}

function assertPublicHttps(url) {
  const parsed = new URL(url);
  if (parsed.protocol !== "https:") throw new Error("RSS URL must stay on HTTPS");
  if (isPrivateHostname(parsed.hostname)) throw new Error("RSS URL must stay on a public host");
  return parsed.href;
}

/**
 * Follow a few public HTTPS redirects. Allowlisted feeds such as MarketWatch,
 * Guardian Business, and CoinDesk answer 301/302/308 before the XML. Treating
 * those as failures produced an empty 200 from the proxy.
 */
async function fetchRssDocument(feedUrl, options = {}) {
  const doFetch = options.fetch || globalThis.fetch;
  const readText = options.readText || (async response => response.text());
  let current = assertPublicHttps(feedUrl);
  for (let hop = 0; hop <= MAX_RSS_REDIRECTS; hop++) {
    const response = await doFetch(current, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; DispatchMarkets/1.0; +https://thedispatch.uk)",
        Accept: "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
      },
      redirect: "manual",
      signal: options.signal || AbortSignal.timeout(8_000),
    });
    if (REDIRECT_STATUSES.has(response.status)) {
      const location = response.headers.get("location");
      if (!location) throw new Error(`RSS ${response.status} missing location`);
      if (hop === MAX_RSS_REDIRECTS) throw new Error("RSS redirect limit");
      current = assertPublicHttps(new URL(location, current).href);
      continue;
    }
    if (!response.ok) throw new Error(`RSS ${response.status}`);
    const body = await readText(response, 512 * 1024);
    if (!body || !String(body).includes("<")) throw new Error("RSS empty body");
    return String(body);
  }
  throw new Error("RSS redirect limit");
}

module.exports = { fetchRssDocument, isPrivateHostname, assertPublicHttps, MAX_RSS_REDIRECTS };
