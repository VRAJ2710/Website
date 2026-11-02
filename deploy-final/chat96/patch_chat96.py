#!/usr/bin/env python3
# chat96 (includes chat95, which never ships alone): all eight macro tiles from the first paint, plain names instead of market codes, guest-preview links on trust pages,
# desk and crypto quotes served from a short cache instead of tripping the limiter. Exact-count edits; any miss aborts, nothing written.
# usage: patch_chat96.py server.js app.js index.html
import sys, os, json
SRV, APP, IDX = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat96: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat96" in srv or "chat96" in app or "v=chat96" in idx or "chat95" in srv: sys.exit("patch_chat96: already applied")
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
  if (c && c.h && Date.now() - c.t < 864e5 && c.h.indexOf("<article") === 0) {
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
  'return hm ? ("Gold futures (COMEX, front month) · delayed · as of " + hm + " UK") : "Gold futures (COMEX, front month) · delayed";', tag="fe85-asof")
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
# ── app 4 (chat96): titles fix the plural brand too; "Regime: loading…" never shows; UNAVAILABLE reads as a word; onboarding roadmap is current ──
app = edit(app, 'document.title.replace(/\\bThe Dispatch\\b(?! Market)/g', 'document.title.replace(/\\bDispatch Markets\\b/g, "Dispatch Market").replace(/\\bThe Dispatch\\b(?! Market)/g', tag="title-rx")
app = edit(app, '(re._hide ? "" : " · Regime: loading…")', '""', tag="reg-home")
app = edit(app, 're.loading ? (re._hide ? "" : "Regime: loading…") :', 're.loading ? (re._hide ? "" : "Regime updating") :', tag="reg-rt18")
app = edit(app, 'out = out.replace(/Regime: loading…\\s*·\\s*\\d{1,3}\\/100/g, "Regime: loading…");', 'out = out.replace(/Regime (?:updating|: loading…)\\s*·\\s*\\d{1,3}\\/100/g, "Regime updating");', tag="reg-rt18b")
app = edit(app, 'return { ...r, loading: true, label: "Regime: loading…", narrative: "Regime: loading…" };', 'return { ...r, loading: true, label: "Regime updating", narrative: "" };', tag="reg-skel")
app = edit(app, 'if (re.loading) return re._hide ? "" : "Regime: loading…";', 'if (re.loading) return "";', tag="reg-sub")
app = edit(app, '<li><strong>Your own AI key</strong> — connect your AI provider and control the cost (coming soon)</li>\n      <li><strong>Journal</strong> — your decision history becomes the moat (next)</li>',
  '<li><strong>Your own AI key</strong> — add a key from OpenAI, Anthropic, xAI Grok, Google Gemini or Perplexity in Settings; your provider bills you</li>', tag="roadmap")
app = edit(app, 'Gold desk · conditional weekly playbook · AI research assistant on Premium.', 'Gold desk · conditional weekly playbook · Ask, our AI research assistant, on Premium or with your own AI key.', tag="onboard-dek")
app = edit(app, ' · Energy super-cycle · BTC halving cycle</div>', ' · Energy super-cycle</div>', tag="halving")
# chat answers from the reader's key: a 424 carries a plain reason (and, for Premium, an offer of the site's AI)
app = edit(app, '''    if (!res.ok) {
      _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
      return;
    }''', '''    if (!res.ok) {
      try { const c96d = await res.clone().json(); if (c96d && c96d.byok) { c96ByokFailMsg(c96d); return; } } catch (c96e) {} // chat96: your-key failures say why
      _chatMsgs.push({ role: "assistant", kind: "ai-unavailable", content: CHAT_AI_UNAVAILABLE, retryable: true });
      return;
    }''', tag="chat-424")
app = edit(app, '''      const data = await res2.json().catch(() => ({}));
      if (!res2.ok) {''', '''      const data = await res2.json().catch(() => ({}));
      if (!res2.ok && data && data.byok) { c96ByokFailMsg(data); return; } // chat96
      if (!res2.ok) {''', tag="chat-424b")
blk = open(os.path.join(HERE, "app_block.js"), encoding="utf-8").read().replace("@@PLAIN@@", PLAIN)
app = "// chat95 chat96\n" + app + blk

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
# ── server 4 (chat96): register name, login/reset CSRF, account delete/export cover AI keys, desk last-good capped at 10 min ──
srv = edit(srv, '<label for="register-email">Email address</label>', '<label for="register-name">Name <span class="muted">(optional)</span></label><input id="register-name" name="name" type="text" maxlength="60" autocomplete="name"><label for="register-email">Email address</label>', tag="reg-name")
srv = edit(srv, '''        VALUES (${user.id}, ${user.email}, ${user.passwordHash}, 'free')`;
    } catch {''', '''        VALUES (${user.id}, ${user.email}, ${user.passwordHash}, 'free')`;
      try { await c96SaveName(user.id, form.get("name")); } catch (c96e) {} // chat96: optional name, stored with the account
    } catch {''', tag="reg-save")
srv = edit(srv, '''  if (p === "/__auth/reset" && req.method === "POST") {
    if (!allowAuthRequest(req, res)) return;''', '''  if (p === "/__auth/reset" && req.method === "POST") {
    if (!sameOriginMutation(req)) return text(res, 403, "Cross-site password reset is not allowed."); // chat96
    if (!allowAuthRequest(req, res)) return;''', tag="reset-csrf")
srv = edit(srv, '''  if (p === "/__auth/login" && req.method === "POST") {
    if (!allowAuthRequest(req, res)) return;''', '''  if (p === "/__auth/login" && req.method === "POST") {
    if (!sameOriginMutation(req)) return text(res, 403, "Cross-site sign-in is not allowed."); // chat96: login CSRF
    if (!allowAuthRequest(req, res)) return;''', tag="login-csrf")
srv = edit(srv, '''        prefsUpdatedAt: rows[0] ? rows[0].updated_at : null,
      };''', '''        prefsUpdatedAt: rows[0] ? rows[0].updated_at : null,
        name: await c96GetName(user.id) || null,
        aiKeys: await c96ByokList(user.id), // chat96: provider, last 4 and dates only; never the key
      };''', tag="export")
srv = edit(srv, '<title>${title}</title>', '<title>${String(title).replace(/ \u00b7 The Dispatch Market$/, " | The Dispatch Market")}</title>', tag="auth-title")
srv = edit(srv, '''      await sql`DELETE FROM dispatch_users WHERE id=${user.id}`;
      await sql`DELETE FROM dispatch_sessions WHERE user_id=${user.id}`;''', '''      await sql`DELETE FROM dispatch_users WHERE id=${user.id}`;
      try { await c96AccountPurge(user.id); } catch (c96e) { console.warn("c96 purge:", (c96e && c96e.code) || "error"); } // chat96: AI keys and name go too
      await sql`DELETE FROM dispatch_sessions WHERE user_id=${user.id}`;''', tag="delete")
srv = edit(srv, 'BB10E_CACHE_AGE_MS = 24 * 3600 * 1000;', 'BB10E_CACHE_AGE_MS = 10 * 60 * 1000; // chat96: last-good at most 10 minutes', tag="bb10e-age")
LIVE = open(os.path.join(HERE, "live96.js"), encoding="utf-8").read()
if "</script" in LIVE.lower(): sys.exit("patch_chat96: live96.js contains </script")
srv = srv + "\n// ── chat96 ──\nconst C96_LIVE_JS = " + json.dumps(LIVE) + ";\n" + open(os.path.join(HERE, "server_block.js"), encoding="utf-8").read()


# ── index: new cache token for app.js ──
idx = edit(idx, '<script defer src="/app.js?v=chat94"></script>', '<script defer src="/app.js?v=chat96"></script>', tag="idx-token")
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat96: ok")
