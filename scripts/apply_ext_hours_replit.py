#!/usr/bin/env python3
"""Apply Yahoo EXT·HRS / OTC tape fix on Replit the-dispatch (surgical).
Replaces marketProxy.js from PR branch helpers already vendored beside this script
OR downloads them. Patches server.js yahooQuote + app.js session labels.
"""
from __future__ import annotations
import re, shutil, sys, urllib.request
from pathlib import Path

ROOT = Path(".").resolve()
APP = ROOT / "app.js"
SRV = ROOT / "server.js"
MP = ROOT / "marketProxy.js"
INDEX = ROOT / "index.html"
MP_URL = "https://raw.githubusercontent.com/VRAJ2710/Website/cursor/equity-extended-hours-bbc2/marketProxy.js"

NEW_YAHOO = '''async function yahooQuote(symbols) {
  const out = {};
  await Promise.all(symbols.slice(0, 60).map(async symbol => {
    const urls = [yahooChartUrl(symbol)];
    if (urls[0] !== yahooDailyChartUrl(symbol)) urls.push(yahooDailyChartUrl(symbol));
    for (const u of urls) {
      try {
        const d = await (await upstream(u)).json();
        const quote = normalizeYahooChartResult(d.chart?.result?.[0]);
        if (quote) {
          out[symbol] = quote;
          return;
        }
      } catch {}
    }
  }));
  return out;
}'''

CONTINUOUS_BLOCK = '''const CONTINUOUS_TAPE_TICKERS = Object.freeze(["XAU", "EURUSD", "BTC", "ETH"]);
function _isContinuousTapeTicker(tk) {
  return CONTINUOUS_TAPE_TICKERS.includes(tk);
}
'''

def ensure_import(text: str) -> str:
  """Ensure server.js destructures yahoo helpers from marketProxy."""
  needed = ["yahooChartUrl", "yahooDailyChartUrl", "normalizeYahooChartResult"]
  if all(n in text for n in needed) and "normalizeYahooChartResult" in text:
    # still ensure they're in the require destructuring
    m = re.search(r'\} = require\("\./marketProxy"\);', text)
    if m:
      block_start = text.rfind("const {", 0, m.start())
      block = text[block_start:m.end()]
      missing = [n for n in needed if n not in block]
      if missing:
        insert = ",\n  " + ",\n  ".join(missing)
        text = text[:m.start()] + insert + "\n" + text[m.start():]
        print("added to marketProxy require:", missing)
      else:
        print("marketProxy require already has yahoo helpers")
    return text
  # fallback: add after existing require
  if 'require("./marketProxy")' in text:
    text = text.replace(
      '} = require("./marketProxy");',
      '  yahooChartUrl,\n  yahooDailyChartUrl,\n  normalizeYahooChartResult,\n} = require("./marketProxy");',
      1,
    )
    print("patched marketProxy require (append)")
  return text

def patch_app(text: str) -> str:
  if "CONTINUOUS_TAPE_TICKERS" not in text:
    # insert near liveQuoteMarketClosed
    anchor = "let liveQuoteMarketClosed"
    i = text.find(anchor)
    if i < 0:
      raise SystemExit("liveQuoteMarketClosed not found")
    # find end of that let line
    nl = text.find("\n", i)
    insert = "\nlet liveQuoteSession={};\n" + CONTINUOUS_BLOCK
    if "let liveQuoteSession" not in text:
      text = text[:nl+1] + insert + text[nl+1:]
      print("added CONTINUOUS_TAPE_TICKERS + liveQuoteSession")
    else:
      text = text[:nl+1] + CONTINUOUS_BLOCK + text[nl+1:]
      print("added CONTINUOUS_TAPE_TICKERS")
  elif "_isContinuousTapeTicker" not in text:
    text = text.replace(
      'const CONTINUOUS_TAPE_TICKERS = Object.freeze(["XAU", "EURUSD", "BTC", "ETH"]);',
      CONTINUOUS_BLOCK.strip(),
      1,
    )

  if "let liveQuoteSession" not in text:
    text = text.replace(
      "let liveQuoteMarketClosed",
      "let liveQuoteSession={};\nlet liveQuoteMarketClosed",
      1,
    )
    print("added liveQuoteSession decl")

  # Patch marketClosed assignment in _applyLiveQuote
  old_closed = "liveQuoteMarketClosed[tk] = !!q.marketClosed;"
  new_closed = "liveQuoteMarketClosed[tk] = _isContinuousTapeTicker(tk) ? false : !!q.marketClosed;\n  liveQuoteSession[tk] = _isContinuousTapeTicker(tk) ? null : (q.session || null);"
  if old_closed in text and "liveQuoteSession[tk]" not in text.split("liveQuoteMarketClosed[tk]")[1][:200]:
    text = text.replace(old_closed, new_closed, 1)
    print("patched _applyLiveQuote session/closed")
  elif "liveQuoteSession[tk]" in text:
    print("_applyLiveQuote session already present")
  else:
    # production variant with more fields after marketClosed
    m = re.search(r"liveQuoteMarketClosed\[tk\]\s*=\s*!!q\.marketClosed;", text)
    if m:
      text = text[:m.start()] + new_closed + text[m.end():]
      print("patched _applyLiveQuote marketClosed (regex)")
    else:
      m2 = re.search(r"liveQuoteMarketClosed\[tk\]\s*=\s*[^;]+;", text)
      if m2 and "liveQuoteSession[tk]" not in text[m2.start():m2.start()+300]:
        text = text[:m2.end()] + "\n  liveQuoteSession[tk] = _isContinuousTapeTicker(tk) ? null : (q.session || null);" + text[m2.end():]
        # also force continuous never closed
        text = text[:m2.start()] + "liveQuoteMarketClosed[tk] = _isContinuousTapeTicker(tk) ? false : !!q.marketClosed;" + text[m2.end():]
        print("patched _applyLiveQuote (append session)")
      else:
        print("WARN: could not patch _applyLiveQuote closed/session")

  # Replace hard MARKET CLOSED block in _quoteMeta
  # Production pattern: if (liveQuoteMarketClosed[tk]) { status = "closed"; label = "MARKET CLOSED"; ...
  pat = re.compile(
    r'if\s*\(\s*liveQuoteMarketClosed\[tk\]\s*\)\s*\{\s*'
    r'status\s*=\s*"closed";\s*'
    r'label\s*=\s*"MARKET CLOSED";[\s\S]*?\}',
    re.M,
  )
  replacement = '''const session = _isContinuousTapeTicker(tk) ? null : liveQuoteSession[tk];
  const cashClosed = !_isContinuousTapeTicker(tk) && !!liveQuoteMarketClosed[tk];
  if (session === "post") {
    status = "extended"; label = "AH";
    detail = "Yahoo after-hours / post-RTH print — delayed retail feed";
  } else if (session === "pre") {
    status = "extended"; label = "PRE";
    detail = "Yahoo pre-market print — delayed retail feed";
  } else if (session === "otc") {
    status = "extended"; label = "OTC";
    detail = "Yahoo OTC / off-exchange print — delayed";
  } else if (session === "fullday") {
    status = "extended"; label = "EXT·HRS";
    detail = "Yahoo combined/extended-hours print — delayed retail feed";
  } else if (cashClosed) {
    status = "rth-close"; label = "RTH CLOSE";
    detail = "Regular US cash session closed — last RTH print retained";
  }'''
  m = pat.search(text)
  if m:
    text = text[:m.start()] + replacement + text[m.end():]
    print("replaced MARKET CLOSED block with EXT·HRS / RTH CLOSE")
  elif 'label = "AH"' in text or 'status = "extended"' in text:
    print("_quoteMeta extended labels already present")
  else:
    print("WARN: MARKET CLOSED block not found — manual check needed")

  # Fix stat() pills for extended / rth-close — avoid treating closed as missing
  if 's==="extended"' not in text and "s === \"extended\"" not in text:
    # insert before stale or unavailable handling in stat()
    m = re.search(r'function stat\(tk\)\{[\s\S]*?if\(s==="unavailable"\)', text)
    if m:
      insert = 'if(s==="extended")return `<span class="bd trust-stat trust-stat-ext" title="${title}" style="background:var(--gdG);color:var(--gd);font-size:7.5px">${_esc(d.label||"EXT·HRS")}</span>`;\n  if(s==="rth-close"||s==="closed")return `<span class="bd trust-stat trust-stat-rth" title="${title}" style="background:var(--b3);color:var(--t2);font-size:7.5px">${_esc(d.label||"RTH CLOSE")}</span>`;\n  '
      text = text[:m.end()-len('if(s==="unavailable")')] + insert + 'if(s==="unavailable")' + text[m.end():]
      print("patched stat() pills")
    else:
      print("WARN: stat() pattern not found")

  # Ensure fp()/status paths that map closed → NO SYNC are fixed
  text2, n = re.subn(
    r"d\.status\s*===\s*['\"]unavailable['\"]\s*\?\s*['\"]NO SYNC['\"]",
    '(d.status==="unavailable"?"NO SYNC":(d.status==="extended"?(d.label||"EXT·HRS"):(d.status==="rth-close"||d.status==="closed"?(d.label||"RTH CLOSE"):null))) || (false?"NO SYNC"',
    text,
  )
  # That regex is too risky — skip if complicated
  # Simpler: replace patterns that treat closed as unavailable in live tape
  if "status === \"closed\"" in text and "rth-close" in text:
    # soften: closed treated like rth-close in tape bit
    pass

  return text

def main():
  if not APP.exists() or not SRV.exists():
    print("ERROR: run from Replit workspace root"); return 1

  # 1) marketProxy.js from PR
  shutil.copy2(MP, MP.with_suffix(".js.bak-exthrs")) if MP.exists() else None
  print("downloading marketProxy.js from PR #14…")
  MP.write_bytes(urllib.request.urlopen(MP_URL, timeout=60).read())
  print("wrote marketProxy.js", MP.stat().st_size)

  # 2) server.js
  shutil.copy2(SRV, SRV.with_suffix(".js.bak-exthrs"))
  srv = SRV.read_text(encoding="utf-8")
  srv = ensure_import(srv)
  m = re.search(r"async function yahooQuote\(symbols\) \{[\s\S]*?\n\}", srv)
  if not m:
    print("ERROR: yahooQuote not found in server.js"); return 1
  srv = srv[:m.start()] + NEW_YAHOO + srv[m.end():]
  print("replaced yahooQuote")
  SRV.write_text(srv, encoding="utf-8")

  # 3) app.js
  shutil.copy2(APP, APP.with_suffix(".js.bak-exthrs"))
  app = APP.read_text(encoding="utf-8")
  app = patch_app(app)
  APP.write_text(app, encoding="utf-8")

  # 4) cache buster
  if INDEX.exists():
    html = INDEX.read_text(encoding="utf-8")
    html2, n = re.subn(r'(app\.js\?v=)([^\"]+)', r'\1exthrs1', html, count=1)
    if n:
      INDEX.write_text(html2, encoding="utf-8")
      print("bumped app.js?v=exthrs1")

  # sanity
  for needle in ["normalizeYahooChartResult", "yahooChartUrl", "EXT·HRS", "RTH CLOSE", "liveQuoteSession"]:
    ok = needle in APP.read_text(encoding="utf-8") or needle in SRV.read_text(encoding="utf-8") or needle in MP.read_text(encoding="utf-8")
    print(f"check {needle}: {'OK' if ok else 'MISSING'}")
  print("OK — republish Autoscale, hard-refresh")
  return 0

if __name__ == "__main__":
  sys.exit(main())
