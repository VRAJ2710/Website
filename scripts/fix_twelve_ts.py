#!/usr/bin/env python3
"""Fix live-tape: Twelve Data timestamp units + stale window on free-plan cache."""
from __future__ import annotations
import re, shutil, sys
from pathlib import Path

APP = Path("app.js")
INDEX = Path("index.html")

NEW_FETCH = '''async function fetchTwelveDataPrices() {
  try {
    const symbols = Object.values(TWELVE_DATA_SYMBOLS);
    const res = await fetch(`/api/twelve-data-quote?symbols=${encodeURIComponent(symbols.join(","))}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) return 0;
    const data = await res.json();
    if (data?.configured === false || data?.unavailable) return 0;
    const quotes = data?.quotes || {};
    const closedSymbols = new Set(data?.marketClosedSymbols || []);
    // Prefer server fetchedAt (ms). row.ts is often unix seconds.
    let batchFetchedAt = Number(data.fetchedAt);
    if (!Number.isFinite(batchFetchedAt) || batchFetchedAt <= 0) batchFetchedAt = Date.now();
    else if (batchFetchedAt < 10_000_000_000) batchFetchedAt *= 1000;
    let hits = 0;
    Object.entries(TWELVE_DATA_SYMBOLS).forEach(([ticker, symbol]) => {
      const row = quotes[symbol];
      if (!row) return;
      let fetchedAt = batchFetchedAt;
      const rawTs = Number(row.ts);
      if (Number.isFinite(rawTs) && rawTs > 0) {
        const tsMs = rawTs < 10_000_000_000 ? rawTs * 1000 : rawTs;
        // Keep the newer of provider tick vs batch fetch, never seconds-as-ms.
        if (tsMs <= Date.now() + 60_000) fetchedAt = Math.max(fetchedAt, tsMs);
      }
      // For shared-cache hits, floor age to "just received" so LIVE·TD survives the 15m server TTL.
      if (data.cached) fetchedAt = Date.now();
      const quote = {
        ...row,
        ts: fetchedAt,
        fetchedAt,
        marketClosed: !!row.marketClosed || closedSymbols.has(symbol),
      };
      if (_applyLiveQuote(ticker, quote, "twelve-data")) hits++;
    });
    return hits;
  } catch (e) {
    return 0;
  }
}'''

def main():
  if not APP.exists():
    print("ERROR: app.js missing"); return 1
  shutil.copy2(APP, APP.with_suffix(".js.bak-livets"))
  text = APP.read_text(encoding="utf-8")

  m = re.search(r"async function fetchTwelveDataPrices\(\) \{[\s\S]*?\n\}", text)
  if not m:
    print("ERROR: fetchTwelveDataPrices not found"); return 1
  text = text[:m.start()] + NEW_FETCH + text[m.end():]
  print("patched fetchTwelveDataPrices")

  # Fix: twelve-data stale window must match shared cache (16m), not 3m
  old = 'const staleAfterMs = src === "twelve-data" ? PRICE_STALE_MS'
  new = 'const staleAfterMs = src === "twelve-data" ? TWELVE_DATA_CACHE_WINDOW_MS'
  if old in text:
    text = text.replace(old, new, 1)
    print("patched twelve-data staleAfterMs → TWELVE_DATA_CACHE_WINDOW_MS")
  elif new in text:
    print("staleAfterMs already uses TWELVE_DATA_CACHE_WINDOW_MS")
  else:
    print("WARN: staleAfterMs pattern not found")

  # Ensure symbol map includes gold/crypto/etfs
  m2 = re.search(r"const TWELVE_DATA_SYMBOLS = Object\.freeze\(\{[\s\S]*?\}\);", text)
  if m2 and "XAU/USD" not in m2.group(0):
    text = text[:m2.start()] + '''const TWELVE_DATA_SYMBOLS = Object.freeze({
  AAPL: "AAPL", NVDA: "NVDA",
  SPY: "SPY", QQQ: "QQQ",
  XAU: "XAU/USD", EURUSD: "EUR/USD",
  BTC: "BTC/USD", ETH: "ETH/USD",
});''' + text[m2.end():]
    print("patched TWELVE_DATA_SYMBOLS")
  else:
    print("TWELVE_DATA_SYMBOLS ok")

  APP.write_text(text, encoding="utf-8")

  if INDEX.exists():
    html = INDEX.read_text(encoding="utf-8")
    html2, n = re.subn(r'(app\.js\?v=)([^\"]+)', r'\1livefix2', html, count=1)
    if n:
      INDEX.write_text(html2, encoding="utf-8")
      print("bumped app.js cache buster")
  print("OK — republish Autoscale, then hard-refresh")
  return 0

if __name__ == "__main__":
  sys.exit(main())
