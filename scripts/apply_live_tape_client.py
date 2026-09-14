#!/usr/bin/env python3
"""Surgical live-tape client map for Replit the-dispatch workspace.
Updates TWELVE_DATA_SYMBOLS + fetchTwelveDataPrices guards in app.js.
Does NOT touch billing/session/www code.
"""
from __future__ import annotations
import re, shutil, sys
from pathlib import Path

ROOT = Path(".").resolve()
APP = ROOT / "app.js"
MP = ROOT / "marketProxy.js"
INDEX = ROOT / "index.html"

NEW_SYMBOLS = '''const TWELVE_DATA_SYMBOLS = Object.freeze({
  AAPL: "AAPL", NVDA: "NVDA",
  SPY: "SPY", QQQ: "QQQ",
  XAU: "XAU/USD", EURUSD: "EUR/USD",
  BTC: "BTC/USD", ETH: "ETH/USD",
});'''

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
    let hits = 0;
    Object.entries(TWELVE_DATA_SYMBOLS).forEach(([ticker, symbol]) => {
      const row = quotes[symbol];
      if (!row) return;
      const quote = {
        ...row,
        fetchedAt: row.ts ?? data.fetchedAt,
        marketClosed: !!row.marketClosed || closedSymbols.has(symbol),
      };
      if (_applyLiveQuote(ticker, quote, "twelve-data")) hits++;
    });
    return hits;
  } catch (e) {
    return 0;
  }
}'''

NEW_ALLOWED = '''const TWELVE_DATA_ALLOWED_SYMBOLS = Object.freeze([
  "AAPL", "NVDA", "SPY", "QQQ",
  "XAU/USD", "EUR/USD",
  "BTC/USD", "ETH/USD",
]);'''

def main():
  if not APP.exists():
    print("ERROR: app.js not found in", ROOT); return 1
  shutil.copy2(APP, APP.with_suffix(".js.bak-livetape"))
  text = APP.read_text(encoding="utf-8")
  m = re.search(r"const TWELVE_DATA_SYMBOLS = Object\.freeze\(\{[\s\S]*?\}\);", text)
  if not m:
    print("ERROR: TWELVE_DATA_SYMBOLS block not found"); return 1
  text = text[:m.start()] + NEW_SYMBOLS + text[m.end():]
  print("updated TWELVE_DATA_SYMBOLS")

  m2 = re.search(r"async function fetchTwelveDataPrices\(\) \{[\s\S]*?\n\}", text)
  if m2:
    text = text[:m2.start()] + NEW_FETCH + text[m2.end():]
    print("updated fetchTwelveDataPrices")
  else:
    print("WARN: fetchTwelveDataPrices not replaced")

  # Ensure Yahoo overwrite guard mentions twelve-data (already present usually)
  if 'liveQuoteSrc[tk] !== "twelve-data"' not in text:
    print("WARN: twelve-data overwrite guard missing — review manually")

  APP.write_text(text, encoding="utf-8")

  if MP.exists():
    shutil.copy2(MP, MP.with_suffix(".js.bak-livetape"))
    mp = MP.read_text(encoding="utf-8")
    m3 = re.search(r"const TWELVE_DATA_ALLOWED_SYMBOLS = Object\.freeze\(\[[\s\S]*?\]\);", mp)
    if m3:
      mp = mp[:m3.start()] + NEW_ALLOWED + mp[m3.end():]
      MP.write_text(mp, encoding="utf-8")
      print("updated TWELVE_DATA_ALLOWED_SYMBOLS in marketProxy.js")
    else:
      print("WARN: allowlist not found in marketProxy.js (may be inlined in server.js)")

  if INDEX.exists():
    idx = INDEX.read_text(encoding="utf-8")
    # bump app.js?v= cache buster if present
    idx2, n = re.subn(r"(app\.js\?v=)(\d+)", lambda m: m.group(1) + str(int(m.group(2)) + 1 if m.group(2).isdigit() else 1789356001), idx, count=1)
    if n:
      INDEX.write_text(idx2, encoding="utf-8")
      print("bumped app.js cache buster")
    else:
      # try TD- asset version style
      print("no app.js?v= buster found — hard refresh after deploy")

  print("OK — restart / republish Autoscale, then hard-refresh thedispatch.uk")
  return 0

if __name__ == "__main__":
  sys.exit(main())
