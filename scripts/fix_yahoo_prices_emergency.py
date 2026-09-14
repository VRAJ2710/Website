#!/usr/bin/env python3
"""Emergency: restore working yahooQuote + front-door price display."""
from __future__ import annotations
import re, shutil, subprocess, sys
from pathlib import Path

APP, SRV, INDEX = Path("app.js"), Path("server.js"), Path("index.html")

NEW_YAHOO = '''async function yahooQuote(symbols) {
  const out = {};
  await Promise.all((symbols || []).slice(0, 60).map(async symbol => {
    if (!symbol) return;
    const encoded = encodeURIComponent(symbol);
    const urls = [
      `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?range=1d&interval=1m&includePrePost=true`,
      `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?range=5d&interval=1d&includePrePost=true`,
    ];
    for (const u of urls) {
      try {
        const d = await (await upstream(u, { signal: AbortSignal.timeout(8_000) })).json();
        const result = d.chart?.result?.[0];
        const meta = result?.meta;
        if (!meta) continue;
        let price = null;
        let session = "regular";
        const post = Number(meta.postMarketPrice);
        const pre = Number(meta.preMarketPrice);
        const regular = Number(meta.regularMarketPrice);
        const fullday = Number(meta.fulldayPrice);
        if (Number.isFinite(post) && post > 0) { price = post; session = "post"; }
        else if (Number.isFinite(pre) && pre > 0) { price = pre; session = "pre"; }
        else if (Number.isFinite(regular) && regular > 0) { price = regular; session = "regular"; }
        else if (Number.isFinite(fullday) && fullday > 0) { price = fullday; session = "fullday"; }
        if (!(price > 0)) continue;
        const prev = Number(meta.previousClose || meta.chartPreviousClose || price);
        const change = price - (prev || price);
        const c = prev ? (change / prev) * 100 : 0;
        const ts = Number(meta.regularMarketTime) || null;
        out[symbol] = {
          p: price,
          c,
          prev: prev > 0 ? prev : price,
          change,
          currency: meta.currency || null,
          exchange: meta.exchangeName || meta.fullExchangeName || null,
          name: meta.longName || meta.shortName || symbol,
          ts,
          session,
          marketClosed: session === "regular" && meta.marketState && String(meta.marketState).toUpperCase().includes("CLOSE"),
        };
        return;
      } catch {}
    }
  }));
  return out;
}'''

def main():
  if not SRV.exists() or not APP.exists():
    print("ERROR: run from Repl root"); return 1
  shutil.copy2(SRV, SRV.with_suffix(".js.bak-yhfix"))
  srv = SRV.read_text(encoding="utf-8")
  m = re.search(r"async function yahooQuote\(symbols\) \{[\s\S]*?\n\}", srv)
  if not m:
    print("ERROR: yahooQuote not found"); return 1
  srv = srv[:m.start()] + NEW_YAHOO + srv[m.end():]
  SRV.write_text(srv, encoding="utf-8")
  print("replaced yahooQuote with resilient parser")

  shutil.copy2(APP, APP.with_suffix(".js.bak-yhfix"))
  app = APP.read_text(encoding="utf-8")
  # Fix referencePx to allow live + proxy + extended + delayed
  old = '''function referencePx(tk) {
  const meta = _quoteMeta(tk);
  const p = P[tk]?.p;
  const retained = liveSymbols.has(tk)
    && typeof p === "number"
    && isFinite(p)
    && p > 0;
  if (!retained || meta.status === "live" || meta.status === "unavailable") return null;
  return typeof p === "number" && isFinite(p) && p > 0 ? p : null;
}'''
  new = '''function referencePx(tk) {
  const meta = _quoteMeta(tk);
  const p = P[tk]?.p;
  const retained = liveSymbols.has(tk)
    && typeof p === "number"
    && isFinite(p)
    && p > 0;
  // Front door must show any synced print (live, proxy, delayed, EXT).
  if (!retained || meta.status === "unavailable") return null;
  return p;
}'''
  if old in app:
    app = app.replace(old, new, 1)
    print("fixed referencePx")
  else:
    # looser replace
    m = re.search(r"function referencePx\(tk\) \{[\s\S]*?\n\}", app)
    if m and "meta.status === \"live\"" in m.group(0):
      app = app[:m.start()] + new + app[m.end():]
      print("fixed referencePx (regex)")
    else:
      print("WARN: referencePx pattern not found")

  # Re-render home after prices
  if 'pg==="home"' not in app[app.find("async function _fetchLivePrices"):app.find("async function _fetchLivePrices")+5000]:
    anchor = "if(pg===\"mkt\"&&_mktView===\"curated\")_patchCuratedPrices();"
    if anchor in app:
      app = app.replace(
        anchor,
        'if(pg==="home"||pg==="brief"){ try{ renderMain(); }catch(e){} }\n  '+anchor,
        1,
      )
      print("re-render home after price fetch")
    else:
      print("WARN: could not add home re-render")

  APP.write_text(app, encoding="utf-8")
  if INDEX.exists():
    html = INDEX.read_text(encoding="utf-8")
    html2, n = re.subn(r'(app\.js\?v=)([^\"]+)', r'\1pricefix1', html, count=1)
    if n:
      INDEX.write_text(html2, encoding="utf-8")
      print("bumped app.js?v=pricefix1")

  for f in (SRV, APP):
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    if r.returncode != 0:
      print(f.name, "CHECK FAIL", r.stderr); return 1
    print(f.name, "node --check OK")
  print("OK — republish Autoscale now")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
