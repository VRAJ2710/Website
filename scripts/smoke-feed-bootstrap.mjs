#!/usr/bin/env node
/**
 * Fails when the desk cannot leave its initial markets/news shell.
 *
 * Local (default): serves this repo and a mock quote/RSS API, then drives
 * Chrome. A yahoo request that still asks for desk tickers (WTI, SPX, …)
 * fails. RSS feed=undefined fails. Shell text left on Fetching / AWAITING FEED
 * fails.
 *
 * Remote: BASE_URL=https://thedispatch.uk node scripts/smoke-feed-bootstrap.mjs
 * checks the published shell after a Replit republish. It does not mock Yahoo.
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BASE = process.env.BASE_URL ? process.env.BASE_URL.replace(/\/$/, "") : "";
const DESK_ALIASES = new Set([
  "WTI", "SPX", "NG", "BTC", "COPPER", "DXY", "XAU", "DJIA", "IXIC",
  "EURUSD", "USDJPY", "SLV", "BRENT", "VIX", "GBPUSD",
]);
const WIRE = {
  "CL=F": 78.42,
  "NG=F": 3.12,
  "^GSPC": 5721.5,
  "GC=F": 4162.5,
  "BTC-USD": 64250,
  "^DJI": 42110,
  "^IXIC": 17880,
  "HG=F": 4.55,
  "DX-Y.NYB": 101.38,
  "AAPL": 226.4,
  "SI=F": 32.1,
  "BZ=F": 81.2,
};
const ALIAS_TRAP = { WTI: 3.57, NG: 6.5, BTC: 36.95, SPX: 1, XAU: 1, COPPER: 1, DXY: 1 };

function quoteFor(symbol) {
  const p = Object.prototype.hasOwnProperty.call(WIRE, symbol)
    ? WIRE[symbol]
    : Object.prototype.hasOwnProperty.call(ALIAS_TRAP, symbol)
      ? ALIAS_TRAP[symbol]
      : 50 + (symbol.length % 17);
  return { p, c: 0.4, prev: p / 1.004, currency: "USD", name: symbol, ts: Math.floor(Date.now() / 1000) };
}

function rssXml(feed) {
  return `<?xml version="1.0"?><rss version="2.0"><channel><title>${feed}</title><item><title>Smoke headline ${feed}</title><link>https://example.test/${feed}</link><pubDate>Wed, 01 Oct 2026 07:00:00 GMT</pubDate><description>Desk smoke item ${feed}</description></item></channel></rss>`;
}

function contentType(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (file.endsWith(".css")) return "text/css; charset=utf-8";
  if (file.endsWith(".svg")) return "image/svg+xml";
  if (file.endsWith(".json")) return "application/json";
  return "application/octet-stream";
}

function startMock() {
  const seen = { yahoo: [], rss: [], badYahoo: [], badRss: [] };
  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", "http://127.0.0.1");
    const send = (code, body, type = "application/json") => {
      res.writeHead(code, { "content-type": type, "cache-control": "no-store" });
      res.end(body);
    };
    if (url.pathname === "/api/yahoo-quote") {
      const symbols = (url.searchParams.get("symbols") || "").split(",").map(s => s.trim()).filter(Boolean);
      seen.yahoo.push(symbols);
      const bad = symbols.filter(s => DESK_ALIASES.has(s));
      if (bad.length) seen.badYahoo.push(bad);
      const out = {};
      symbols.forEach(s => { out[s] = quoteFor(s); });
      return send(200, JSON.stringify(out));
    }
    if (url.pathname === "/api/rss-feed") {
      const feed = url.searchParams.get("feed") || "";
      seen.rss.push(feed);
      if (!/^f\d{1,2}$/.test(feed)) {
        seen.badRss.push(feed);
        return send(400, JSON.stringify({ error: "Unknown RSS feed." }));
      }
      return send(200, rssXml(feed), "application/xml");
    }
    if (url.pathname === "/api/finnhub") {
      res.setHeader("X-Dispatch-Data-Status", "degraded");
      const endpoint = url.searchParams.get("endpoint");
      if (endpoint === "news" || endpoint === "company-news") return send(200, "[]");
      return send(200, "{}");
    }
    if (url.pathname === "/api/twelve-data-quote") {
      return send(200, JSON.stringify({ configured: false, unavailable: true, reason: "missing_api_key", quotes: {} }));
    }
    if (url.pathname === "/api/market-reference-quotes") {
      return send(200, JSON.stringify({
        XAU: { p: 4162.5, c: 0.2, prev: 4154, ts: Date.now(), source: "gold-api-spot-proxy", proxy: true },
        DXY: { p: 101.38, c: -0.1, prev: 101.5, ts: Date.now(), source: "open-exchange-rate-api", proxy: true },
        fetchedAt: Date.now(),
      }));
    }
    if (url.pathname === "/api/coingecko") return send(200, "{}");
    if (url.pathname === "/api/yahoo-chart") {
      return send(200, JSON.stringify({ chart: { result: [{ indicators: { quote: [{ close: [] }] } }] } }));
    }
    if (url.pathname === "/api/me") return send(200, JSON.stringify({ tier: "free" }));
    if (url.pathname === "/api/stripe-status") return send(200, JSON.stringify({ configured: false }));
    if (url.pathname.startsWith("/api/")) return send(200, "{}");

    const rel = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname).replace(/^\/+/, "");
    const file = path.join(ROOT, rel);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      return send(404, "not found", "text/plain");
    }
    return send(200, fs.readFileSync(file), contentType(file));
  });
  return new Promise(resolve => {
    server.listen(0, "127.0.0.1", () => resolve({ server, seen, port: server.address().port }));
  });
}

function loadPuppeteer() {
  try { return require("puppeteer-core"); } catch { /* workspace may not depend on it */ }
  return require("/tmp/pp/node_modules/puppeteer-core");
}

async function main() {
  const failures = [];
  let browser;
  let mock;
  const target = BASE || null;
  try {
    if (!target) mock = await startMock();
    const puppeteer = loadPuppeteer();
    const chrome = process.env.CHROME_PATH || "/usr/local/bin/google-chrome";
    browser = await puppeteer.launch({
      executablePath: chrome,
      headless: true,
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    const page = await browser.newPage();
    page.setDefaultTimeout(20000);
    await page.setViewport({ width: 1440, height: 900 });
    const pageErrors = [];
    page.on("pageerror", err => pageErrors.push(String(err && err.message || err)));
    const url = target ? `${target}/` : `http://127.0.0.1:${mock.port}/`;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForFunction(
      () => typeof priceFetching !== "undefined" && priceFetching === false
        && typeof newsFetching !== "undefined" && newsFetching === false
        && typeof _priceFetchAttempted !== "undefined" && _priceFetchAttempted === true,
      { timeout: 45000 },
    );
    const snap = await page.evaluate(() => ({
      cmd: document.getElementById("cmdLive")?.textContent || "",
      p1: document.getElementById("p1sub")?.textContent || "",
      p2: document.getElementById("p2sub")?.textContent || "",
      news: typeof NEWS !== "undefined" ? NEWS.length : 0,
      priceFetching,
      newsFetching,
      live: typeof liveSymbols !== "undefined" ? [...liveSymbols] : [],
      px: {
        WTI: typeof P !== "undefined" ? P.WTI?.p : null,
        SPX: typeof P !== "undefined" ? P.SPX?.p : null,
        BTC: typeof P !== "undefined" ? P.BTC?.p : null,
        COPPER: typeof P !== "undefined" ? P.COPPER?.p : null,
        DXY: typeof P !== "undefined" ? P.DXY?.p : null,
        AAPL: typeof P !== "undefined" ? P.AAPL?.p : null,
        XAU: typeof P !== "undefined" ? P.XAU?.p : null,
      },
      rss0: typeof RSS_FEEDS !== "undefined" ? RSS_FEEDS[0]?.id : null,
      rssN: typeof RSS_FEEDS !== "undefined" ? RSS_FEEDS.length : 0,
    }));
    const stuck = [];
    if (snap.cmd === "Fetching" || snap.cmd === "") stuck.push(`cmdLive=${JSON.stringify(snap.cmd)}`);
    if (snap.p1 === "— AWAITING FEED" || snap.p1 === "AWAITING FEED") stuck.push(`p1sub=${JSON.stringify(snap.p1)}`);
    if (snap.p2 === "AWAITING FEED") stuck.push(`p2sub=${JSON.stringify(snap.p2)}`);
    if (snap.news < 1) stuck.push("NEWS.length=0");
    for (const tk of ["WTI", "SPX", "AAPL"]) {
      if (!snap.live.includes(tk)) stuck.push(`liveSymbols missing ${tk}`);
    }
    if (stuck.length) failures.push("shell still loading: " + stuck.join("; "));
    if (!target) {
      if (snap.px.WTI !== 78.42) failures.push(`WTI price ${snap.px.WTI} (wire CL=F is 78.42)`);
      if (snap.px.SPX !== 5721.5) failures.push(`SPX price ${snap.px.SPX} (wire ^GSPC is 5721.5)`);
      if (snap.px.BTC !== 64250) failures.push(`BTC price ${snap.px.BTC} (wire BTC-USD is 64250)`);
      if (snap.px.COPPER !== 4.55) failures.push(`COPPER price ${snap.px.COPPER} (wire HG=F is 4.55)`);
      if (snap.px.AAPL !== 226.4) failures.push(`AAPL price ${snap.px.AAPL}`);
      if (snap.rss0 !== "f0") failures.push(`RSS_FEEDS[0].id=${snap.rss0}`);
      const flat = mock.seen.yahoo.flat();
      for (const need of ["^GSPC", "CL=F", "BTC-USD", "GC=F", "HG=F", "DX-Y.NYB"]) {
        if (!flat.includes(need)) failures.push(`yahoo request missing ${need}`);
      }
      if (mock.seen.badYahoo.length) failures.push("yahoo requested desk tickers " + JSON.stringify(mock.seen.badYahoo.slice(0, 4)));
      if (mock.seen.badRss.length) failures.push("rss feed ids " + JSON.stringify(mock.seen.badRss.slice(0, 8)));
      if (!mock.seen.rss.includes("f0")) failures.push("rss never requested f0");
    }
    const artifactDir = "/opt/cursor/artifacts";
    try { fs.mkdirSync(artifactDir, { recursive: true }); } catch { /* optional */ }
    const report = { url, snap, yahooRequests: mock ? mock.seen.yahoo.length : null, rss: mock ? mock.seen.rss : null, pageErrors: pageErrors.slice(0, 8), failures };
    try { fs.writeFileSync(path.join(artifactDir, "feed-bootstrap-smoke.json"), JSON.stringify(report, null, 2)); } catch { /* optional */ }
    try { await page.screenshot({ path: path.join(artifactDir, "feed-bootstrap-shell.png"), fullPage: false }); } catch { /* optional */ }
    if (failures.length) {
      console.error(JSON.stringify(report, null, 2));
      process.exitCode = 1;
      return;
    }
    console.log(JSON.stringify({
      ok: true,
      cmd: snap.cmd,
      p1: snap.p1,
      p2: snap.p2,
      news: snap.news,
      live: snap.live.length,
      px: snap.px,
    }));
  } finally {
    if (browser) await browser.close().catch(() => {});
    if (mock) await new Promise(resolve => mock.server.close(resolve));
  }
}

main().catch(err => {
  console.error(err && err.stack || err);
  process.exit(1);
});
