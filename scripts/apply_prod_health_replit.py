#!/usr/bin/env python3
"""Apply PR#13 prod-health onto Replit without wiping EXT·HRS live tape."""
from __future__ import annotations
import re, shutil, sys, urllib.request
from pathlib import Path

ROOT = Path(".").resolve()
MP = ROOT / "marketProxy.js"
SRV = ROOT / "server.js"
APP = ROOT / "app.js"
INDEX = ROOT / "index.html"
MERGED_MP_URL = "https://raw.githubusercontent.com/VRAJ2710/Website/cursor/equity-extended-hours-bbc2/scripts/marketProxy.health-merged.js"
# fallback: we push merged file to that path

GEO_FN = '''
const geoCache = new BoundedTtlCache({ maxEntries: 16, maxBytes: 512 * 1024 });
const GEO_CACHE_MS = 60_000;
async function geoEarthquakes(searchParams) {
  const query = normalizeGeoQuery(searchParams);
  const cached = geoCache.get(query.cacheKey);
  if (cached) return { body: cached, cache: "hit" };
  const response = await upstream(query.feedUrl, { signal: AbortSignal.timeout(8_000) });
  const body = normalizeUsgsEarthquakes(await response.json(), query);
  geoCache.set(query.cacheKey, body, GEO_CACHE_MS);
  return { body, cache: "miss" };
}
'''

def ensure_requires(srv: str) -> str:
  needed = [
    "normalizeGeoQuery", "normalizeUsgsEarthquakes", "staticCacheControl",
    "attachSecurityHeaders", "GEO_CACHE_CONTROL", "USGS_SOURCE",
    "composeCoinGeckoPath", "SECURITY_HEADERS",
  ]
  m = re.search(r'const \{([\s\S]*?)\} = require\("\./marketProxy"\);', srv)
  if not m:
    print("WARN: marketProxy require not found")
    return srv
  block = m.group(1)
  missing = [n for n in needed if n not in block]
  if missing:
    insert = ",\n  " + ",\n  ".join(missing)
    srv = srv[:m.end(1)] + insert + srv[m.end(1):]
    print("added requires", missing)
  else:
    print("requires ok")
  return srv

def patch_json(srv: str) -> str:
  # Ensure json() merges SECURITY_HEADERS if a simple json helper exists
  m = re.search(r'function json\(res, status, body(?:, extraHeaders = \{\})?\) \{[\s\S]*?\n\}', srv)
  if not m:
    print("WARN: json() not found")
    return srv
  new = '''function json(res, status, body, extraHeaders = {}) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    ...SECURITY_HEADERS,
    ...extraHeaders,
  });
  res.end(payload);
}'''
  srv = srv[:m.start()] + new + srv[m.end():]
  print("patched json()")
  return srv

def patch_serve_static(srv: str) -> str:
  m = re.search(r'function serveStatic\(req, res, pathname(?:, searchParams)?\) \{[\s\S]*?\n\}', srv)
  if not m:
    print("WARN: serveStatic not found"); return srv
  new = '''function serveStatic(req, res, pathname, searchParams) {
  const requested = pathname === "/" ? "/index.html" : pathname;
  const file = path.normalize(path.join(root, requested));
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return false;
  const blocked = /(^|\\/)(server\\.js|stripeClient\\.js|marketProxy\\.js|rssFeeds\\.js|package\\.json|package-lock\\.json|.*\\.md)$/i;
  if (blocked.test(requested)) return false;
  const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json", ".txt": "text/plain", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2" };
  const ext = path.extname(file).toLowerCase();
  res.writeHead(200, {
    "Content-Type": types[ext] || "application/octet-stream",
    "Cache-Control": staticCacheControl(pathname, searchParams || new URL(req.url, "http://localhost").searchParams),
    ...SECURITY_HEADERS,
  });
  fs.createReadStream(file).pipe(res);
  return true;
}'''
  srv = srv[:m.start()] + new + srv[m.end():]
  print("patched serveStatic")
  return srv

def patch_geo_route(srv: str) -> str:
  if "async function geoEarthquakes" not in srv:
    # insert before handle or after caches
    anchor = "const twelveDataCache"
    i = srv.find(anchor)
    if i < 0:
      i = srv.find("async function handle")
    if i < 0:
      print("WARN: cannot insert geoEarthquakes"); 
    else:
      # insert after twelveDataCache line
      nl = srv.find("\n", i)
      srv = srv[:nl+1] + GEO_FN + srv[nl+1:]
      print("inserted geoEarthquakes + geoCache")
  else:
    # upgrade body if still using all_week
    if "all_week" in srv and "normalizeGeoQuery" not in srv[srv.find("geo"):srv.find("geo")+800]:
      print("WARN: old geo path may remain — check manually")
    print("geoEarthquakes already present")

  # Replace /api/geo handler
  pat = re.compile(r'if\s*\(\s*p\s*===\s*"/api/geo"\s*\)\s*\{[\s\S]*?\n  \}', re.M)
  replacement = '''if (p === "/api/geo") {
    try {
      const { body, cache } = await geoEarthquakes(url.searchParams);
      return json(res, 200, body, {
        "Cache-Control": GEO_CACHE_CONTROL,
        "X-Dispatch-Cache": cache,
      });
    } catch {
      return json(res, 200, {
        events: [],
        source: USGS_SOURCE,
        asOf: new Date().toISOString(),
        status: "unavailable",
      });
    }
  }'''
  m = pat.search(srv)
  if m:
    srv = srv[:m.start()] + replacement + srv[m.end():]
    print("patched /api/geo route")
  else:
    print("WARN: /api/geo route not found")

  # serveStatic call should pass searchParams
  srv2, n = re.subn(
    r'if\s*\(\s*serveStatic\(\s*req\s*,\s*res\s*,\s*p\s*\)\s*\)\s*return;',
    'if (serveStatic(req, res, p, url.searchParams)) return;',
    srv,
    count=1,
  )
  if n:
    srv = srv2
    print("serveStatic call passes searchParams")
  return srv

def patch_coingecko_route(srv: str) -> str:
  # Prefer composeCoinGeckoPath(raw, searchParams) if coinGecko uses only path
  if "composeCoinGeckoPath" in srv:
    print("composeCoinGeckoPath already referenced")
  # Update route to pass searchParams
  srv2, n = re.subn(
    r'if\s*\(\s*p\s*===\s*"/api/coingecko"\s*\)\s*return\s+coinGecko\([^;]+;',
    'if (p === "/api/coingecko") return coinGecko(req, res, url.searchParams.get("path"), url.searchParams);',
    srv,
    count=1,
  )
  if n:
    srv = srv2
    print("patched /api/coingecko route signature")
  # Inside coinGecko, ensure composeCoinGeckoPath is used
  if "function coinGecko" in srv or "async function coinGecko" in srv:
    if "composeCoinGeckoPath" not in srv[srv.find("coinGecko"):srv.find("coinGecko")+1200]:
      # try replace normalizeCoinGeckoPath(rawPath) with compose
      srv3, n3 = re.subn(
        r'normalizeCoinGeckoPath\(\s*rawPath\s*\)',
        'composeCoinGeckoPath(rawPath, searchParams)',
        srv,
        count=3,
      )
      if n3:
        srv = srv3
        print("coinGecko uses composeCoinGeckoPath")
  return srv

def patch_handle_security(srv: str) -> str:
  # At start of handle, attachSecurityHeaders(res)
  m = re.search(r'async function handle\(req, res\)\s*\{', srv)
  if not m:
    m = re.search(r'function handle\(req, res\)\s*\{', srv)
  if not m:
    print("WARN: handle() not found"); return srv
  insert_at = m.end()
  if "attachSecurityHeaders(res)" in srv[insert_at:insert_at+400]:
    print("attachSecurityHeaders already in handle")
    return srv
  srv = srv[:insert_at] + "\n  attachSecurityHeaders(res);" + srv[insert_at:]
  print("handle() attaches security headers")
  return srv

def patch_app_cg(app: str) -> str:
  # Back off when unavailable/rate_limited JSON
  if "rate_limited" in app and "X-Dispatch-Data-Status" in app:
    # strengthen: if body.unavailable
    needle = "if (res.status === 429 || res.headers.get(\"X-Dispatch-Data-Status\") === \"unavailable\")"
    if "unavailable" in app[app.find("cgFetch"):app.find("cgFetch")+800]:
      print("cgFetch already handles unavailable header")
    # Also parse JSON unavailable
  # Add after successful res in fetchCrypto
  if 'd.unavailable' not in app and 'data?.unavailable' not in app:
    old = "if(!res.ok)return null;\n    const d=await res.json();"
    new = "if(!res.ok)return null;\n    const d=await res.json();\n    if(d&&(d.unavailable||d.rate_limited)){_cgBackoffUntil=Date.now()+90000;return null;}"
    if old in app:
      app = app.replace(old, new, 1)
      print("patched fetchCrypto unavailable backoff")
    else:
      print("WARN: fetchCrypto pattern not found")
  return app

def main():
  if not MP.exists() or not SRV.exists():
    print("ERROR: run from Replit workspace root"); return 1

  # 1) merged marketProxy
  shutil.copy2(MP, MP.with_suffix(".js.bak-health"))
  local = Path("/tmp/marketProxy.health-merged.js")
  # try URL then local path next to script
  try:
    MP.write_bytes(urllib.request.urlopen(MERGED_MP_URL, timeout=60).read())
    print("downloaded merged marketProxy")
  except Exception as e:
    alt = Path(__file__).resolve().parent / "marketProxy.health-merged.js"
    if alt.exists():
      MP.write_bytes(alt.read_bytes())
      print("copied merged marketProxy from scripts/")
    else:
      print("ERROR: merged marketProxy missing", e); return 1

  # 2) server
  shutil.copy2(SRV, SRV.with_suffix(".js.bak-health"))
  srv = SRV.read_text(encoding="utf-8")
  srv = ensure_requires(srv)
  srv = patch_json(srv)
  srv = patch_serve_static(srv)
  srv = patch_geo_route(srv)
  srv = patch_coingecko_route(srv)
  srv = patch_handle_security(srv)
  SRV.write_text(srv, encoding="utf-8")

  # 3) app cg backoff
  if APP.exists():
    shutil.copy2(APP, APP.with_suffix(".js.bak-health"))
    app = patch_app_cg(APP.read_text(encoding="utf-8"))
    APP.write_text(app, encoding="utf-8")

  if INDEX.exists():
    html = INDEX.read_text(encoding="utf-8")
    html2, n = re.subn(r'(app\.js\?v=)([^\"]+)', r'\1health1', html, count=1)
    if n:
      INDEX.write_text(html2, encoding="utf-8")
      print("bumped app.js?v=health1")

  # checks
  mp = MP.read_text(encoding="utf-8")
  srv = SRV.read_text(encoding="utf-8")
  for needle, where in [
    ("SECURITY_HEADERS", mp), ("normalizeGeoQuery", mp), ("yahooChartUrl", mp),
    ("geoEarthquakes", srv), ("staticCacheControl", srv), ("attachSecurityHeaders", srv),
  ]:
    print(f"check {needle}: {'OK' if needle in where else 'MISSING'}")
  print("OK — republish Autoscale, then curl /api/geo and headers")
  return 0

if __name__ == "__main__":
  sys.exit(main())
