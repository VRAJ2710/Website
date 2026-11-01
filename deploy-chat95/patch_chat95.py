#!/usr/bin/env python3
# chat95: all eight macro tiles from the first paint, plain names instead of market codes, guest-preview links on trust pages,
# desk and crypto quotes served from a short cache instead of tripping the limiter. Exact-count edits; any miss aborts, nothing written.
# usage: patch_chat95.py server.js app.js index.html
import sys, os
SRV, APP, IDX = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat95: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat95" in srv or "chat95" in app or "v=chat95" in idx: sys.exit("patch_chat95: already applied")
PLAIN = open(os.path.join(HERE, "plain.js"), encoding="utf-8").read().strip()

# ── app 1: the macro grid always has eight cells: live tile, else last known (with its saved time), else a labelled placeholder ──
app = edit(app, '''function _rt53Inner() { var l = _rt53TileList(), t = l.map(_rt53One).filter(Boolean); if (!t.length) return ""; return '<div class="bb1-h">Macro</div><div class="bb1-grid">' + t.join("") + '</div>' + (t.length < l.length ? '<p class="c93-note">Some prices are delayed; we show the last official figure with its date.</p>' : ''); }''',
'''function _rt53Inner() { // chat95: eight cells in a fixed order from the first paint
  var l = _rt53TileList(), live = 0, held = 0;
  var t = l.map(function (spec) { var r = c95Tile(spec); if (r.k === "live") live++; else if (r.k === "last") held++; return r.h; });
  if (live) c95TileSave();
  return '<div class="bb1-h">Macro</div><div class="bb1-grid">' + t.join("") + '</div>' + (live + held < l.length ? '<p class="c93-note">Figures still loading show their name until the price arrives. Free feeds may be delayed.</p>' : held ? '<p class="c93-note">Tiles marked Last known show the latest figure we hold and when we saved it; the live price replaces it as soon as it loads.</p>' : '');
}
function c95TileStore() {
  if (window.__c95tiles) return window.__c95tiles;
  var c = {}; try { c = JSON.parse(localStorage.getItem("c95bb1") || "{}") || {}; } catch (e) { c = {}; }
  window.__c95tiles = c; return c;
}
function c95TileSave() {
  var now = Date.now(), ks = Object.keys(c95TileStore()).sort().join(","); // save at once when a new tile arrives, else at most every 30 s
  if (ks === window.__c95keys && window.__c95saved && now - window.__c95saved < 30000) return; window.__c95saved = now; window.__c95keys = ks;
  try { localStorage.setItem("c95bb1", JSON.stringify(c95TileStore())); } catch (e) {}
}
function c95UkStamp(ms) {
  try { return new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(ms)).replace(/,/g, "") + " UK"; } catch (e) { return ""; }
}
function c95Tile(spec) {
  var id = spec[0], h = "", C = c95TileStore();
  try { h = _rt53One(spec) || ""; } catch (e) { h = ""; }
  if (h) {
    if (/^(dollar|us10|vix|brent|wti)$/.test(id)) h = h.replace(/<div class="bb1-meta">([^<]*)<\\/div><\\/article>$/, function (m, x) { return '<div class="bb1-meta">' + _rt53Esc(c95Src(x.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'"))) + '</div></article>'; });
    C[id] = { h: h, t: Date.now() };
    return { k: "live", h: h };
  }
  var c = C[id];
  if (c && c.h && Date.now() - c.t < 7 * 864e5 && c.h.indexOf("<article") === 0) {
    return { k: "last", h: c.h.replace('<article class="bb1-tile"', '<article class="bb1-tile bb1-last"').replace('<div class="bb1-meta">', '<div class="bb1-meta">Last known, saved ' + _rt53Esc(c95UkStamp(c.t)) + ' \\u00b7 ') };
  }
  return { k: "wait", h: '<article class="bb1-tile bb1-wait" data-c95-wait="' + id + '" aria-busy="true"><div class="bb1-k">' + _rt53Esc(spec[2]) + '</div><div class="bb1-pv" aria-hidden="true">\\u2026</div><p class="bb1-why">' + _rt53Esc(spec[3]) + '</p><div class="bb1-wmeta">Loading latest\\u2026</div></article>' };
}''', tag="rt53Inner")

# ── app 2: the real yield starts at once (no idle wait), restores its last official print with its date, and retries once ──
app = edit(app, '''function _rt53RyStart() {
  var go = function () {''', '''function _rt53RyStart() { // chat95: immediate, cached with its print date, one retry
  try { var sv = JSON.parse(localStorage.getItem("c95ry") || "null"); if (!_rt53Ry && sv && isFinite(Number(sv.value)) && sv.date && Date.now() - Number(sv.saved || 0) < 10 * 864e5) _rt53Ry = { value: Number(sv.value), prev: sv.prev, change: sv.change, date: String(sv.date) }; } catch (e) {}
  var tries = 0;
  var go = function () {
    tries++;''', tag="ry-start")
app = edit(app, '''      if (!j || j.available === false || !isFinite(Number(j.value)) || !j.date) return;
      _rt53Ry = { value: Number(j.value), prev: j.prev == null || !isFinite(Number(j.prev)) ? null : Number(j.prev), change: j.change == null || !isFinite(Number(j.change)) ? null : Number(j.change), date: String(j.date) };''',
'''      if (!j || j.available === false || !isFinite(Number(j.value)) || !j.date) { if (tries < 2) setTimeout(go, 20000); return; }
      _rt53Ry = { value: Number(j.value), prev: j.prev == null || !isFinite(Number(j.prev)) ? null : Number(j.prev), change: j.change == null || !isFinite(Number(j.change)) ? null : Number(j.change), date: String(j.date) };
      try { localStorage.setItem("c95ry", JSON.stringify(Object.assign({ saved: Date.now() }, _rt53Ry))); } catch (e) {}''', tag="ry-save")
app = edit(app, '''    }).catch(function () {});
  };
  if (typeof requestIdleCallback === "function") requestIdleCallback(go, { timeout: 2500 });
  else setTimeout(go, 1200);
}''', '''    }).catch(function () { if (tries < 2) setTimeout(go, 20000); });
  };
  if (_rt53Ry) { try { if (typeof pg === "undefined" || pg === "home") _paintFrontDoorQuotes(); } catch (e) {} }
  go();
}''', tag="ry-go")

# ── app 3: plain futures labels at the source, so painters and the page agree and nothing repaints every second ──
app = edit(app, 'return hm ? ("Gold futures (GC=F) · as of " + hm + " UK") : "Gold futures (GC=F)";',
  'return hm ? ("Gold futures (COMEX, front month) · Yahoo Finance, delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · Yahoo Finance, delayed";', tag="fe85-asof")
app = edit(app, '"Gold futures (GC=F, delayed 10 min)"', '"Gold futures (COMEX, front month, delayed 10 min)"', 10, tag="gold-lbl-d")
app = edit(app, '"Gold futures (GC=F)', '"Gold futures (COMEX, front month)', 20, tag="gold-lbl")
app = edit(app, 'Gold futures \\(GC=F\\)', 'Gold futures \\((?:GC=F|COMEX, front month)\\)', 12, tag="gold-rx")
app = edit(app, '  return { name: row[0], sym: row[1], label: row[0] + " (" + row[1] + ")" };',
  '  var ven = { "HG=F": "COMEX", "SI=F": "COMEX", "PL=F": "NYMEX", "PA=F": "NYMEX", "NG=F": "NYMEX", "CL=F": "NYMEX", "BZ=F": "ICE" }[row[1]] || "";\n  return { name: row[0], sym: row[1], label: row[0] + " (" + (ven ? ven + ", " : "") + "front month)" }; // chat95: no raw codes', tag="fe86-cmd")
app = edit(app, '''    var line = fe87_macroMeta(fe87_stamp(fe87_sessionMs("XAU")), closed ? fe87_reopenPhrase("XAU") : "", closed, nowHm);
    if (line && meta.textContent !== line) meta.textContent = line;''', '''    var line = c95Src(fe87_macroMeta(fe87_stamp(fe87_sessionMs("XAU")), closed ? fe87_reopenPhrase("XAU") : "", closed, nowHm));
    if (line && meta.textContent !== line) meta.textContent = line;''', tag="fe87-gold-meta")
app = edit(app, '''  var line = fe87_macroMeta(fe87_stamp(fe87_sessionMs(tk)), fe87_reopenPhrase(tk), true, nowHm);
  if (line && meta.textContent !== line) meta.textContent = line;''', '''  var line = c95Src(fe87_macroMeta(fe87_stamp(fe87_sessionMs(tk)), fe87_reopenPhrase(tk), true, nowHm));
  if (line && meta.textContent !== line) meta.textContent = line;''', tag="fe87-other-meta")
blk = open(os.path.join(HERE, "app_block.js"), encoding="utf-8").read().replace("@@PLAIN@@", PLAIN)
app = "// chat95\n" + app + blk

# ── server 1: guest home and markets labels without codes ──
srv = edit(srv, '\\"Gold futures (COMEX, GC=F)\\"', '\\"Gold futures (COMEX, front month)\\"', tag="dq-gold")
srv = edit(srv, '\\"Silver futures (COMEX, SI=F)\\"', '\\"Silver futures (COMEX, front month)\\"', tag="dq-silver")
srv = edit(srv, '\\"WTI crude futures (CL=F)\\"', '\\"WTI crude futures (NYMEX, front month)\\"', tag="dq-wti")
srv = edit(srv, '\\"US natural gas futures (NG=F)\\"', '\\"US natural gas futures (NYMEX, front month)\\"', tag="dq-ng")
srv = edit(srv, 'var BB10_DESK_LABEL = { "^TNX": "US 10-year yield (^TNX)", "DX-Y.NYB": "US Dollar Index (ICE, Yahoo DX-Y.NYB)", "GC=F": "Gold futures (GC=F, delayed 10 min)", "^VIX": "VIX (CBOE)" };',
  'var BB10_DESK_LABEL = { "^TNX": "US 10-year Treasury yield (Cboe)", "DX-Y.NYB": "US Dollar Index (ICE)", "GC=F": "Gold futures (COMEX, front month, delayed 10 min)", "^VIX": "VIX (Cboe)" }; // chat95: plain names', tag="desk-label")

# ── server 2: trust pages (About, Methodology, ...) honour the admin ?view=guest preview, and preview links keep it ──
srv = edit(srv, '''  const keep = (h) => { const k = h.replace(/\\/+$/, "") || "/"; return k === "/" || Object.prototype.hasOwnProperty.call(C93_GUEST, k) || h.indexOf(C93_CSM) === 0 || c94Short(k); };''',
  '''  const keep = (h) => { const k = h.replace(/\\/+$/, "") || "/"; return k === "/" || Object.prototype.hasOwnProperty.call(C93_GUEST, k) || Object.prototype.hasOwnProperty.call(C93_PAGES, k) || h.indexOf(C93_CSM) === 0 || c94Short(k); }; // chat95: trust pages too''', tag="keep")
srv = edit(srv, '''  if (!html) { const d = C93_PAGES[key]; html = c93Page(d[0], key, d[1], d[2]()); c93PageCache.set(key, html); }
  return c93Html(req, res, html);''', '''  if (!html) { const d = C93_PAGES[key]; html = c93Page(d[0], key, d[1], d[2]()); c93PageCache.set(key, html); }
  if (/[?&]view=guest(?:&|$)/.test(String(req.url || ""))) return (async () => { // chat95: admin-only guest preview on trust pages
    let u = null; try { u = await currentUser(req); } catch (e) { u = null; }
    if (u && typeof isAdminUser === "function" && isAdminUser(u)) req.c94Preview = key;
    return c93Html(req, res, html);
  })();
  return c93Html(req, res, html);''', tag="c93Send")

# ── server 3: real yield: retry a failed cold fetch after 2 minutes, not 15 ──
srv = edit(srv, '  if ((!RT53_RY.v || now - RT53_RY.at > 6 * 3600e3) && now - RT53_RY.tryAt > 15 * 60e3) {',
  '  if ((!RT53_RY.v || now - RT53_RY.at > 6 * 3600e3) && now - RT53_RY.tryAt > (RT53_RY.v ? 15 : 2) * 60e3) { // chat95: cold failures retry sooner', tag="ry-retry")

# ── server 4: appended block: real-yield warm at boot; desk/crypto micro-cache in front of the (unchanged) limiter ──
srv = srv + open(os.path.join(HERE, "server_block.js"), encoding="utf-8").read()

# ── index: new cache token for app.js ──
idx = edit(idx, '<script defer src="/app.js?v=chat94"></script>', '<script defer src="/app.js?v=chat95"></script>', tag="idx-token")
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat95: ok")
