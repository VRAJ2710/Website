#!/usr/bin/env python3
"""Fix Twelve Data timestamp units in app.js fetchTwelveDataPrices + _applyLiveQuote."""
from __future__ import annotations
import re, shutil, sys
from pathlib import Path

APP = Path("app.js")
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
    const providerFetchedAt = Number(data.fetchedAt);
    let hits = 0;
    Object.entries(TWELVE_DATA_SYMBOLS).forEach(([ticker, symbol]) => {
      const row = quotes[symbol];
      if (!row) return;
      // Prefer server fetchedAt (ms). Provider row.ts is often unix seconds — never pass seconds as ms.
      let fetchedAt = Number.isFinite(providerFetchedAt) && providerFetchedAt > 0 ? providerFetchedAt : Date.now();
      const rawTs = Number(row.ts);
      if (Number.isFinite(rawTs) && rawTs > 0) {
        const tsMs = rawTs < 10_000_000_000 ? rawTs * 1000 : rawTs;
        if (tsMs <= Date.now() + 60_000) fetchedAt = tsMs;
      }
      const quote = {
        ...row,
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

APPLY_GUARD = '''function _applyLiveQuote(tk, q, source) {
  if (!tk || !q || typeof q.p !== "number" || !isFinite(q.p) || q.p <= 0) return false;
  const c = typeof q.c === "number" && isFinite(q.c) ? q.c : 0;
  const prev = typeof q.prev === "number" && q.prev > 0 ? q.prev : q.p / (1 + c / 100);
  P[tk] = { p: q.p, c: +c.toFixed(2) };
  BASE[tk] = { p: prev, c: 0 };
  if (!HIST[tk]) HIST[tk] = [];
  HIST[tk].push(q.p);
  if (HIST[tk].length > 120) HIST[tk].shift();
  liveSymbols.add(tk);
  let sourceFetchedAt = Number(q.fetchedAt);
  // Provider timestamps may arrive in seconds; normalize to ms before age checks.
  if (Number.isFinite(sourceFetchedAt) && sourceFetchedAt > 0 && sourceFetchedAt < 10_000_000_000) {
    sourceFetchedAt = sourceFetchedAt * 1000;
  }
  liveQuoteTs[tk] = Number.isFinite(sourceFetchedAt) && sourceFetchedAt > 0 && sourceFetchedAt <= Date.now() + 60_000
    ? sourceFetchedAt
    : Date.now();
  liveQuoteSrc[tk] = source || "yahoo";
  return true;
}'''

def main():
  if not APP.exists():
    print("ERROR: app.js missing"); return 1
  shutil.copy2(APP, APP.with_suffix(".js.bak-tsfix"))
  text = APP.read_text(encoding="utf-8")
  m = re.search(r"async function fetchTwelveDataPrices\(\) \{[\s\S]*?\n\}", text)
  if not m:
    print("ERROR: fetchTwelveDataPrices not found"); return 1
  text = text[:m.start()] + NEW_FETCH + text[m.end():]
  print("patched fetchTwelveDataPrices")
  m2 = re.search(r"function _applyLiveQuote\([\s\S]*?\n\}", text)
  if not m2:
    print("ERROR: _applyLiveQuote not found"); return 1
  text = text[:m2.start()] + APPLY_GUARD + text[m2.end():]
  print("patched _applyLiveQuote")
  # bump cache buster if present
  idx = Path("index.html")
  if idx.exists():
    html = idx.read_text(encoding="utf-8")
    html2, n = re.subn(r'(app\.js\?v=)([^\"]+)', r'\1tsfix1', html, count=1)
    if n:
      idx.write_text(html2, encoding="utf-8")
      print("bumped app.js?v= to tsfix1")
  APP.write_text(text, encoding="utf-8")
  print("OK")
  return 0

if __name__ == "__main__":
  sys.exit(main())
