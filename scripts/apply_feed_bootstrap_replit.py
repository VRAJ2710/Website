#!/usr/bin/env python3
"""Surgical feed-bootstrap patch for the live Repl app.js.

Maps desk tickers through YAHOO_SYMBOLS before /api/yahoo-quote, reads the
quote back with data[wire] || data[ticker], isolates price chunks with
Promise.allSettled, and stamps RSS_FEEDS ids f0..f25 from rssFeeds.js.

Idempotent. Does not replace the rest of app.js.
"""
from __future__ import annotations

import os
import re
import sys

CACHE_TOKEN = "pricefix7"

YAHOO_CHUNK = """async function _fetchYahooPriceChunk(chunk) {
  const list = (chunk || []).filter(Boolean);
  const wire = tk => (typeof YAHOO_SYMBOLS !== "undefined" && YAHOO_SYMBOLS[tk]) || tk;
  const yhSyms = [...new Set(list.map(wire).filter(Boolean))];
  if (!yhSyms.length) return 0;
  let hits = 0;
  const missing = [];
  try {
    const res = await fetch(`/api/yahoo-quote?symbols=${encodeURIComponent(yhSyms.join(","))}`, { signal: AbortSignal.timeout(12000) });
    if (!res.ok) return typeof _fetchFinnhubPriceFallback === "function" ? await _fetchFinnhubPriceFallback(list) : 0;
    const data = await res.json();
    for (const tk of list) {
      const yhSym = YAHOO_SYMBOLS[tk] || tk;
      const q = data && (data[yhSym] || data[tk]);
      if (q && _applyLiveQuote(tk, q, "yahoo")) hits++;
      else missing.push(tk);
    }
  } catch (e) {
    return typeof _fetchFinnhubPriceFallback === "function" ? await _fetchFinnhubPriceFallback(list) : 0;
  }
  if (missing.length && typeof _fetchFinnhubPriceFallback === "function") {
    hits += await _fetchFinnhubPriceFallback(missing);
  }
  return hits;
}"""

ALL_SETTLED = """const results=await Promise.allSettled(pair.map(c=>_fetchYahooPriceChunk(c)));
    results.forEach(r=>{
      if(r.status==="fulfilled")successCount+=r.value||0;
      else console.error("yahoo price chunk failed:",r.reason&&r.reason.message||r.reason);
    });"""


def fail(message: str) -> None:
    print(f"apply_feed_bootstrap_replit: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_allowlist(root: str) -> dict[str, str]:
    candidates = [
        os.path.join(root, "rssFeeds.js"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rssFeeds.js"),
    ]
    path = next((p for p in candidates if os.path.isfile(p)), None)
    if not path:
        fail("rssFeeds.js not found")
    text = open(path, encoding="utf-8").read()
    pairs = re.findall(r'(f\d{1,2}):\s*"([^"]+)"', text)
    if len(pairs) < 26:
        fail(f"rssFeeds.js has {len(pairs)} feeds, expected f0..f25")
    return {url: fid for fid, url in pairs}


def function_span(src: str, name: str) -> tuple[int, int, str]:
    marker = f"async function {name}("
    start = src.find(marker)
    if start < 0:
        fail(f"missing {name}")
    nxt = re.search(r"\nasync function ", src[start + len(marker):])
    if not nxt:
        fail(f"{name} is not followed by another async function")
    end = start + len(marker) + nxt.start()
    return start, end, src[start:end]


def patch_yahoo(src: str) -> tuple[str, bool]:
    start, end, body = function_span(src, "_fetchYahooPriceChunk")
    if "chunk.join" in body:
        return src[:start] + YAHOO_CHUNK + src[end:], True
    mapped = (
        "YAHOO_SYMBOLS" in body
        and ("data[yhSym] || data[tk]" in body or "yahooData[yhSym] || yahooData[tk]" in body)
    )
    if mapped:
        return src, False
    fail("_fetchYahooPriceChunk is neither the desk-ticker bug nor the wire-symbol fix")


def patch_allsettled(src: str) -> tuple[str, bool]:
    old = "const results=await Promise.all(pair.map(c=>_fetchYahooPriceChunk(c)));\n    successCount+=results.reduce((a,b)=>a+b,0);"
    if old in src:
        return src.replace(old, ALL_SETTLED, 1), True
    if "Promise.allSettled(pair.map(c=>_fetchYahooPriceChunk(c)))" in src:
        return src, False
    fail("price chunk pair is neither Promise.all nor Promise.allSettled")


def patch_rss(src: str, url_to_id: dict[str, str]) -> tuple[str, bool]:
    start = src.find("const RSS_FEEDS = [")
    tag = src.find("const TAG_RULES", start if start >= 0 else 0)
    if start < 0 or tag < 0:
        fail("RSS_FEEDS block not found")
    block = src[start:tag]
    changed = False
    seen: list[str] = []

    def stamp(match: re.Match[str]) -> str:
        nonlocal changed
        existing = match.group(1)
        url = match.group(2)
        fid = url_to_id.get(url)
        if not fid:
            fail(f"RSS url is not on the f0..f25 allowlist: {url}")
        if existing and existing != fid:
            fail(f"{url} is {existing}; allowlist id is {fid}")
        seen.append(fid)
        if existing:
            return match.group(0)
        changed = True
        return '{id:"%s",url:"%s"' % (fid, url)

    block2 = re.sub(r'\{(?:id:"(f\d+)",)?url:"([^"]+)"', stamp, block)
    if len(seen) != len(set(seen)):
        fail("duplicate RSS feed ids after stamp")
    preserve = ".map((feed,id)=>({...feed,id:feed.id||`f${id}`}))"
    overwrite = ".map((feed,id)=>({...feed,id:`f${id}`}))"
    if overwrite in block2:
        block2 = block2.replace(overwrite, preserve, 1)
        changed = True
    elif ".map(" in block2 and "feed.id||`f${id}`" not in block2:
        fail("RSS_FEEDS map does not preserve explicit ids")
    return src[:start] + block2 + src[tag:], changed


def patch_index(root: str) -> bool:
    path = os.path.join(root, "index.html")
    if not os.path.isfile(path):
        return False
    html = open(path, encoding="utf-8").read()
    original = html
    html2, n = re.subn(
        r'(<script\b[^>]*\bsrc=["\']/app\.js)\?v=[^"\']+',
        r"\1?v=" + CACHE_TOKEN,
        html,
    )
    if n == 0 and "app.js" not in html:
        fail("index.html has no app.js script")
    html = html2
    html = re.sub(r"var V='[^']*'", "var V='TD-" + CACHE_TOKEN + "'", html, count=1)
    feed_js = os.path.join(root, "feedStatus.js")
    if os.path.isfile(feed_js) and "feedStatus.js" not in html:
        html = re.sub(
            r'(<script\b[^>]*\bsrc=["\']/app\.js\?v=' + CACHE_TOKEN + r')',
            '<script src="/feedStatus.js?v=' + CACHE_TOKEN + r'"></script>\n\1',
            html,
            count=1,
        )
    if html == original:
        return False
    open(path, "w", encoding="utf-8").write(html)
    return True


def main() -> None:
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    app_path = os.path.join(root, "app.js")
    if not os.path.isfile(app_path):
        fail(f"no app.js in {root}")
    src = open(app_path, encoding="utf-8").read()
    notes: list[str] = []
    src, yahoo_changed = patch_yahoo(src)
    notes.append("yahoo wire symbols" if yahoo_changed else "yahoo already mapped")
    src, settled_changed = patch_allsettled(src)
    notes.append("chunk allSettled" if settled_changed else "chunks already allSettled")
    src, rss_changed = patch_rss(src, load_allowlist(root))
    notes.append("rss ids stamped" if rss_changed else "rss ids already explicit")
    if yahoo_changed or settled_changed or rss_changed:
        open(app_path, "w", encoding="utf-8").write(src)
    index_changed = patch_index(root)
    notes.append("cache-bust " + CACHE_TOKEN if index_changed else "index cache token unchanged")
    # Fail closed if the desk-ticker request survived.
    chunk_at = src.find("async function _fetchYahooPriceChunk(")
    nxt = src.find("async function ", chunk_at + 10)
    chunk = src[chunk_at:nxt if nxt > 0 else chunk_at + 2500]
    if "chunk.join" in chunk:
        fail("chunk.join still present in _fetchYahooPriceChunk")
    if "data[yhSym] || data[tk]" not in chunk and "yahooData[yhSym] || yahooData[tk]" not in chunk:
        fail("quote lookup data[wire] || data[ticker] missing")
    print("apply_feed_bootstrap_replit: " + "; ".join(notes))


if __name__ == "__main__":
    main()
