#!/usr/bin/env python3
"""
patch_rt16.py — The Dispatch Markets: rt16 (chat14 -> chat15). CLIENT ONLY (server.js untouched).

Usage (Replit workspace root, next to app.js and index.html):
    python3 patch_rt16.py --check     # dry run, writes nothing
    python3 patch_rt16.py             # apply
    python3 patch_rt16.py --dir PATH

Dispatch QA chat14 findings:
  1. Guests get the same 5-tab bar as members: Home / Brief / Playbook (lock) / Gold / More; Markets + News move to More.
     More-sheet group labels readable (12px, higher contrast).
  2. Footer "Updated HH:MM:SS" is 24h and ticks once a second from the real last feed update (stream tick or poll);
     guest front-door footer replaced by the same plain-English footer.
  3. Gold: unknown/empty macro events dropped; card + "AI scenario analysis" note hidden when nothing is left.
  4. Home brief: HTML entities from the server decoded before escaping (no "S&amp;P"); brief card states when it was
     written and the live regime now, so 52 vs 62 is explained.
  5. "FEED DEGRADED" no longer raised by CoinGecko back-off alone while fresh (<15 min) data is on screen.
  7. Phone header: badges/Console collapsed (they stay in Settings/More), 44px tap targets, search gets the width.
  8. Desktop "AWAITING FEED" panel placeholders removed.
  9. OpenBB card jargon replaced; headlines clamped at word boundaries with an ellipsis (CSS line clamp).
 10. Markets table category column shows the full word, 11px; status badges equal min-width; source text >= 11px.
Exact anchors with counts; refuses to run twice; CRLF safe; node --check; tmp-then-rename.
No new endpoint, no server work, the realtime layer (rt9..rt14) logic is untouched apart from the module header.
"""
import argparse, os, shutil, subprocess, sys, tempfile

MARKER = "REALTIME PRICE LAYER (rt16)"
PREV_MARKER = "REALTIME PRICE LAYER (rt14)"
APP_EDITS = [
    ('module header rt14 -> rt16',
     r'''// REALTIME PRICE LAYER (rt14) — browser-direct, free, keyless.''',
     r'''// REALTIME PRICE LAYER (rt16) — browser-direct, free, keyless.'''),
    ('renderNav: guests get the 5-tab bar',
     r'''    ? [["home","Home"],["brief","Brief"],["gold","Gold"],["mkt","Markets"],["news","News"]]
    : NAV_PRIMARY;
  let h = visiblePrimary.map(([id,lb]) =>
    `<button class="${pg===id?"on":""}" onclick="${publicOnly ? `location.href='${PUBLIC_NAV_PATHS[id] || "/"}'` : `nav('${id}')`}" aria-label="${lb}" aria-current="${pg===id?'page':'false'}">${_navIco(id)}<span>${lb}</span></button>`''',
     r'''    ? [["home","Home"],["brief","Brief"],["playbook","Playbook"],["gold","Gold"]]
    : NAV_PRIMARY;
  let h = visiblePrimary.map(([id,lb]) =>
    `<button class="${pg===id?"on":""}" onclick="${publicOnly ? `location.href='${PUBLIC_NAV_PATHS[id] || "/"}'` : `nav('${id}')`}" aria-label="${lb}${publicOnly&&id==="playbook"?" (Premium)":""}" aria-current="${pg===id?'page':'false'}">${_navIco(id)}<span>${lb}${publicOnly&&id==="playbook"?'<span class="nav-lock" aria-hidden="true">🔒</span>':""}</span></button>`'''),
    ('_navInMore: guest primary matches the bar',
     r'''    const primary = [["home","Home"],["brief","Brief"],["gold","Gold"],["mkt","Markets"],["news","News"]].map(i => i[0]);''',
     r'''    const primary = ["home", "brief", "playbook", "gold"];'''),
    ('More sheet: guest primary matches the bar',
     r'''  const publicPrimary = new Set([ "home", "brief", "gold", "mkt", "news" ]);''',
     r'''  const publicPrimary = new Set([ "home", "brief", "playbook", "gold" ]);'''),
    ('More sheet: guest group label',
     r'''? `<div class="more-nav-grp">Free desk</div>''',
     r'''? `<div class="more-nav-grp">All sections</div>'''),
    ('_siteFooter: 24h, live-ticking time',
     r'''  const upd = priceLastFetch ? `Updated ${_fmtAsOf(priceLastFetch.getTime())}` : "";''',
     r'''  const _lf = _rt16LastFeed();
  const upd = _lf ? `Updated <span class="stf-time">${_rt16Hms(_lf)}</span>` : "";'''),
    ('front-door footer unified',
     r'''    <footer class="front-door-footer">Research only · Market data may be delayed · Not financial advice · <button type="button" onclick="openAbout()">About the house</button></footer>''',
     r'''    ${_siteFooter()}'''),
    ('gold events: drop unknown, hide empty',
     r'''    if ((d.events || []).length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Upcoming macro events</div>`;
      d.events.forEach(e => {''',
     r'''    const _unk = v => { const t = String(v == null ? "" : v).trim().toLowerCase(); return !t || t === "unknown" || t === "n/a" || t === "—" || t === "tbd"; };
    const _evs = (d.events || []).filter(e => e && !_unk(e.event) && !_unk(e.date));
    if (_evs.length) {
      h += `<div class="gd-card gc"><div class="gd-sec-h">Upcoming macro events</div>`;
      _evs.forEach(e => {'''),
    ('gold events: no "unknown" badges',
     r'''        <div class="gd-event-d">${_escHtml(e.date)} · ${bd(e.impact || "medium", e.impact === "high" ? "var(--rd)" : "var(--gd)")} ${bd(e.cat || "Macro", "var(--bl)")}</div>''',
     r'''        <div class="gd-event-d">${_escHtml(e.date)}${_unk(e.impact) ? "" : ` · ${bd(e.impact, e.impact === "high" ? "var(--rd)" : "var(--gd)")}`} ${bd(_unk(e.cat) ? "Macro" : e.cat, "var(--bl)")}</div>'''),
    ('gold events: note only with an AI-written note',
     r'''        <div class="gd-sm">${_escHtml(e.goldNote || "")}</div>
      </div>`;
      });
      h += `<div class="gd-note">AI scenario analysis</div></div>`;''',
     r'''        ${_unk(e.goldNote) ? "" : `<div class="gd-sm">${_escHtml(e.goldNote)}</div>`}
      </div>`;
      });
      h += `${_evs.some(e => !_unk(e.goldNote)) ? `<div class="gd-note">AI scenario analysis</div>` : ""}</div>`;'''),
    ('home brief: decode entities + time/regime line',
     r'''      <div class="home-brief-stance">${_escHtml(_brief.houseView || "House view")}</div>
      <div class="home-brief-h">${_escHtml(_brief.headline)}</div>
      ${_brief.summary ? `<div class="home-brief-s">${_escHtml(String(_brief.summary).slice(0, 220))}${String(_brief.summary).length > 220 ? "…" : ""}</div>` : ""}''',
     r'''      <div class="home-brief-stance">${_escHtml(_rt16Dec(_brief.houseView || "House view"))}</div>
      <div class="home-brief-h">${_escHtml(_rt16Dec(_brief.headline))}</div>
      ${_brief.summary ? `<div class="home-brief-s">${_escHtml(_rt16Clip(_rt16Dec(_brief.summary), 220))}</div>` : ""}
      <div class="home-brief-t">${_escHtml(_rt16BriefWhen(_brief))}${re && re.label ? ` · live regime now ${_escHtml(re.label)} ${re.score}/100` : ""}</div>'''),
    ('status bar: CG back-off alone is not DEGRADED',
     r'''  const degraded=priceErrorCount>=2||(_priceFetchAttempted&&!hasFeed&&!priceFetching)||cgThrottle;''',
     r'''  const degraded=priceErrorCount>=2||(_priceFetchAttempted&&!hasFeed&&!priceFetching)||(cgThrottle&&!_rt16FreshOk());'''),
    ('feed banner: CG back-off alone with fresh data is quiet',
     r'''  const cgWait = typeof _cgBackoffUntil === "number" && _cgBackoffUntil > Date.now();
  if (!degraded && !cgWait) {''',
     r'''  const cgWait = typeof _cgBackoffUntil === "number" && _cgBackoffUntil > Date.now() && !_rt16FreshOk();
  if (!degraded && !cgWait) {'''),
    ('OpenBB card copy',
     r'''<div class="openbb-customer-kicker">OPTIONAL RESEARCH CONNECTOR</div><h2>${_escHtml(title)}</h2><div class="openbb-meta">OpenBB historical/fundamental context only · never a primary live-price source</div>''',
     r'''<div class="openbb-customer-kicker">Background</div><h2>${_escHtml(title)}</h2><div class="openbb-meta">History and company fundamentals · not used for live prices</div>'''),
    ('markets table: full category word',
     r'''      <td style="font-family:var(--sn);font-size:9px;color:var(--t3)">${a.cat.slice(0,4)}</td>''',
     r'''      <td class="tt-cat" style="font-family:var(--sn);font-size:11px;color:var(--t3);white-space:nowrap">${_escHtml(a.cat)}</td>'''),
    ('watchlist glance: % from the basis when the stream has no abs change',
     r"""     const chgLbl = hasChange ? `${arrow} ${sign}${d.c}% · ${abs}` : "—";""",
     r"""     const chgLbl = hasChange ? `${arrow} ${sign}${d.c}% · ${abs}` : (retained && ch != null && Number.isFinite(Number(ch)) ? `${ch > 0 ? "▲" : ch < 0 ? "▼" : "•"} ${sign}${Number(ch).toFixed(2)}%` : "—");"""),
    ('front door deck: final text first (no swap when the brief arrives)',
     r"""      <p class="front-door-deck">${brief
        ? `The current house line is ${_escHtml(brief.houseView || "under review")}. Read the free Dispatch Brief for the evidence, risks, and questions behind the stance.`
        : "A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions."}</p>""",
     r"""      <p class="front-door-deck">A weekly research letter for independent traders. Scenarios, invalidation, and provenance—not predictions.</p>"""),
    ('anomalies: word clip',
     r'''highNews.forEach(n => anomalies.push({ t: "news", m: n.x.slice(0, 72) }));''',
     r'''highNews.forEach(n => anomalies.push({ t: "news", m: _rt16Clip(n.x, 72) }));'''),
    ('signals insight: word clip',
     r'''${s.a} (${s.cf}%): ${s.x.slice(0, 80)}''',
     r'''${s.a} (${s.cf}%): ${_rt16Clip(s.x, 80)}'''),
    ('news insight: word clip',
     r'''${latest ? latest.x.slice(0, 100) : "Fetching feeds…"}''',
     r'''${latest ? _rt16Clip(latest.x, 100) : "Fetching feeds…"}'''),
    ('news ingest: word clip',
     r'''x:it.headline.length>120?it.headline.slice(0,117)+"...":it.headline,''',
     r'''x:_rt16Clip(it.headline,120),'''),
    ('OpenBB: no OPTIONAL badge',
     r'''      : historical?.available || fundamentals?.available ? "SUPPLEMENTAL" : "OPTIONAL";''',
     r'''      : historical?.available || fundamentals?.available ? "SUPPLEMENTAL" : "";'''),
    ('OpenBB: plain empty text',
     r'''<div class="openbb-empty">Optional OpenBB historical context. Select one symbol and load a bounded snapshot; it never replaces a primary live price.</div>''',
     r'''<div class="openbb-empty">Pick a symbol to load its price history and fundamentals. Background only: live prices come from the feeds above.</div>'''),
    ('rt16 helpers + CSS + footer ticker (after ui14 css)',
     r'''.wl-glance-mini{min-width:44px}
}`;
    document.head.appendChild(s);
  } catch (e) {}
})();
''',
     r'''.wl-glance-mini{min-width:44px}
}`;
    document.head.appendChild(s);
  } catch (e) {}
})();

// ── rt16 (UI only) ─────────────────────────────────────────
function _rt16Hms(ts) {
  const d = new Date(ts); if (isNaN(d)) return "—";
  const p = n => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}
/** Newest real feed update: a stream tick or a successful poll. */
function _rt16LastFeed() {
  let t = typeof priceLastFetch !== "undefined" && priceLastFetch ? priceLastFetch.getTime() : 0;
  try { for (const k in _rt.lastRecv) { const v = _rt.lastRecv[k]; if (v > t) t = v; } } catch (e) {}
  return t > Date.now() + 5000 ? 0 : t;
}
/** Fresh enough to call healthy: something live, or a poll in the last 15 minutes with quotes on screen. */
function _rt16FreshOk() {
  try {
    const c = quoteStatusCounts();
    if (c.live > 0) return true;
    const t = _rt16LastFeed();
    return !!t && Date.now() - t < 15 * 60 * 1000 && (c.cached + c.delayed + c.closed) > 0;
  } catch (e) { return false; }
}
function _rt16Dec(s) {
  let t = String(s == null ? "" : s);
  for (let i = 0; i < 2 && /&(amp|lt|gt|quot|#39|#x27|apos|nbsp);/.test(t); i++) {
    t = t.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&(#39|#x27|apos);/g, "'").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
  }
  return t;
}
function _rt16Clip(s, n) {
  s = String(s || ""); if (s.length <= n) return s;
  const cut = s.slice(0, n), sp = cut.lastIndexOf(" ");
  return (sp > n * 0.6 ? cut.slice(0, sp) : cut).replace(/[\s,;:·–—-]+$/, "") + "…";
}
function _rt16BriefWhen(b) {
  const ts = Date.parse(b && (b.generatedAt || b.asOf || b.createdAt || "")) || 0;
  return ts ? `Brief written ${_rt16Hms(ts)}` : (b && b.date ? `Brief for ${b.date}` : "Today's brief");
}
(function _rt16Css() {
  try {
    if (document.getElementById("ui16-css")) return;
    const s = document.createElement("style");
    s.id = "ui16-css";
    s.textContent = `.more-nav-grp{font-size:12px!important;letter-spacing:.08em;color:var(--t2,#B8B8B0)!important;opacity:1!important;font-weight:700;padding-top:14px}
.nav-lock{font-size:9px;margin-left:2px;vertical-align:top}
.home-brief-t{font-family:var(--mn);font-size:11px;color:var(--t3);margin-top:6px}
.tt td.tt-cat{min-width:72px}
.price-row-meta,.price-row-meta .asof-tag{font-size:11px!important}
.price-row-meta .bd.trust-stat{display:inline-block;min-width:84px;text-align:center;box-sizing:border-box}
.news-hl{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:normal;word-break:normal}
.site-trust-footer .stf-time{font-variant-numeric:tabular-nums}
.acct-menu-btn{display:none}
.acct-menu{position:fixed;z-index:9999;min-width:220px;background:var(--bg2,#111);border:1px solid var(--gb,#333);border-radius:10px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.5)}
.acct-menu .acct-lbl{font-family:var(--mn);font-size:11px;color:var(--gd);padding:10px 12px 6px;letter-spacing:.08em}
.acct-menu a,.acct-menu button{display:flex;align-items:center;width:100%;min-height:44px;padding:0 12px;background:none;border:0;color:var(--tx,#EDEDE8);font:600 14px var(--sn);text-decoration:none;text-align:left;border-radius:6px;cursor:pointer;box-sizing:border-box}
.acct-menu a:hover,.acct-menu button:hover{background:rgba(212,160,23,.12)}
.term-overlay>.site-trust-footer{margin:28px 16px 0}
@media (max-width:767px){
 .hdr .hdr-auth.has-acct>.auth-group{display:none!important}
 .hdr .hdr-auth.has-acct .acct-menu-btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;min-width:44px;padding:0 10px;background:none;border:1px solid var(--gb,#333);border-radius:8px;color:var(--gd);font:700 12px var(--mn);cursor:pointer}
 .hdr .hdr-auth .auth-btn{min-height:44px;display:inline-flex;align-items:center}
 .hdr .srch{flex:1 1 auto;min-width:120px;min-height:44px}
 .hdr .srch .srch-ph{display:inline}
 #bnav button{min-height:44px}
 .neural-strip{display:grid!important;grid-template-columns:1fr 1fr;gap:8px}
 .neural-strip .ns-cell{min-width:0}
 .neural-strip .ns-val{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .si-act,.si-ask,.openbb-symbol-btn,.ai-retry-btn,.brief-play-btn{min-height:44px;display:inline-flex;align-items:center}
 .brief-play-btn{font-size:11px!important}
 .gd-if-k{white-space:nowrap}
}
.openbb-customer-badge:empty{display:none}`;
    document.head.appendChild(s);
  } catch (e) {}
})();
// Phone account menu: one button in the header opens Admin/Console/Plan/Settings/Sign out.
function _rt16AcctDecorate() {
  const hdr = document.getElementById("hdrAuthBtn");
  if (!hdr) return;
  const signed = typeof _userSignedIn !== "undefined" && _userSignedIn && (_userAdmin === true || (typeof _isPremium === "function" && _isPremium()));
  hdr.classList.toggle("has-acct", !!signed);
  if (signed && !hdr.querySelector(".acct-menu-btn")) {
    hdr.insertAdjacentHTML("beforeend", `<button type="button" class="acct-menu-btn" aria-haspopup="menu" aria-expanded="false" onclick="_rt16AcctToggle(this)">Account ▾</button>`);
  }
}
function _rt16AcctClose() {
  document.getElementById("acctMenu")?.remove();
  document.querySelectorAll(".acct-menu-btn").forEach(b => b.setAttribute("aria-expanded", "false"));
  document.removeEventListener("click", _rt16AcctOutside, true);
}
function _rt16AcctOutside(e) { if (!e.target.closest("#acctMenu,.acct-menu-btn")) _rt16AcctClose(); }
function _rt16AcctToggle(btn) {
  if (document.getElementById("acctMenu")) { _rt16AcctClose(); return; }
  const admin = _userAdmin === true, prem = typeof _isPremium === "function" && _isPremium();
  const m = document.createElement("div");
  m.id = "acctMenu"; m.className = "acct-menu"; m.setAttribute("role", "menu");
  m.innerHTML = `<div class="acct-lbl">${admin ? "ADMIN · FULL ACCESS" : prem ? "PREMIUM" : "FREE"}</div>`
    + (admin ? `<a role="menuitem" href="/__admin">Admin console</a>` : "")
    + (prem && !admin ? `<button type="button" role="menuitem" onclick="_rt16AcctClose();_openBillingPortal()">Plan &amp; billing</button>` : "")
    + `<button type="button" role="menuitem" onclick="_rt16AcctClose();openSettings()">Settings</button>`
    + `<a role="menuitem" href="/__auth/logout">Sign out</a>`;
  document.body.appendChild(m);
  const r = btn.getBoundingClientRect();
  m.style.top = `${Math.round(r.bottom + 6)}px`;
  m.style.right = `${Math.max(8, Math.round(window.innerWidth - r.right))}px`;
  btn.setAttribute("aria-expanded", "true");
  setTimeout(() => document.addEventListener("click", _rt16AcctOutside, true), 0);
}
// Desktop overlays (Brief, Gold, …) get the same footer; checked by the 1s clock below.
function _rt16OverlayFooters() {
  if (typeof IS_DESKTOP === "function" && !IS_DESKTOP()) return;
  document.querySelectorAll(".term-overlay").forEach(ov => {
    if (!ov.offsetParent && getComputedStyle(ov).position !== "fixed") return;
    if (ov.querySelector(".site-trust-footer")) return;
    ov.insertAdjacentHTML("beforeend", _siteFooter());
  });
}
// Footer clock: once a second, text only, paused while the tab is hidden.
(function _rt16FooterClock() {
  try {
    setInterval(() => {
      if (document.hidden) return;
      try { _rt16AcctDecorate(); _rt16OverlayFooters(); } catch (e) {}
      const els = document.querySelectorAll(".site-trust-footer .stf-time");
      if (!els.length) return;
      const t = _rt16LastFeed(); if (!t) return;
      const txt = _rt16Hms(t);
      els.forEach(el => { if (el.textContent !== txt) el.textContent = txt; });
    }, 1000);
  } catch (e) {}
})();
'''),
]

INDEX_EDITS = [
    ("p1sub placeholder", '<span class="panel-sub" id="p1sub">— AWAITING FEED</span>', '<span class="panel-sub" id="p1sub"></span>'),
    ("p2sub placeholder", '<span class="panel-sub" id="p2sub">AWAITING FEED</span>', '<span class="panel-sub" id="p2sub"></span>'),
    ("cache-bust app.js chat14 -> chat15", '/app.js?v=chat14"', '/app.js?v=chat15"'),
]

def load(path):
    with open(path, "rb") as f:
        raw = f.read().decode("utf-8")
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def apply(text, edits, label, errors):
    for e in edits:
        name, old, new = e[0], e[1], e[2]
        want = e[3] if len(e) > 3 else 1
        n = text.count(old)
        if n != want:
            errors.append(f"{label}: '{name}' anchor matched {n} times (need exactly {want})")
            continue
        text = text.replace(old, new)
    return text


def node_check(js_text, label, errors, required):
    node = shutil.which("node")
    if not node:
        if required:
            errors.append(f"{label}: node not found on PATH for `node --check` (use --skip-node-check to override)")
        else:
            print(f"WARN: node not found; {label} not syntax-checked")
        return
    fd, tmp = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(js_text.encode("utf-8"))
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            errors.append(f"{label}: node --check failed: {(r.stderr or r.stdout).strip()[:400]}")
    finally:
        try: os.remove(tmp)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()
    app_p, idx_p = (os.path.join(a.dir, n) for n in ("app.js", "index.html"))
    for p in (app_p, idx_p):
        if not os.path.isfile(p):
            sys.exit(f"ABORT: {p} not found — nothing written")
    app, app_crlf = load(app_p)
    idx, idx_crlf = load(idx_p)
    if MARKER in app or 'app.js?v=chat15"' in idx:
        sys.exit("ABORT: rt16 already applied (marker / chat15 found) — refusing to run twice; nothing written")
    if PREV_MARKER not in app or 'app.js?v=chat14"' not in idx:
        sys.exit("ABORT: these are not the chat14 (rt14) files — nothing written")
    errors = []
    new_app = apply(app, APP_EDITS, "app.js", errors)
    new_idx = apply(idx, INDEX_EDITS, "index.html", errors)
    if not errors:
        if (new_app.count(MARKER) != 1 or PREV_MARKER in new_app or new_app.count("function _rt16LastFeed(") != 1
                or "OPTIONAL RESEARCH CONNECTOR" in new_app or "About the house</button></footer>" in new_app
                or new_idx.count('app.js?v=chat15"') != 1 or "AWAITING FEED</span>" in new_idx):
            errors.append("post-edit sanity check failed")
        node_check(new_app, "app.js", errors, required=False)
    if errors:
        print("ABORT — no files written:")
        for e in errors: print("  -", e)
        sys.exit(1)
    print(f"OK: {len(APP_EDITS)} app.js edits, {len(INDEX_EDITS)} index.html edits verified (app.js {len(new_app)-len(app):+d} chars); server.js not touched")
    if a.check:
        print("--check: dry run, nothing written"); return
    tmps = []
    try:
        for p, text, crlf in ((app_p, new_app, app_crlf), (idx_p, new_idx, idx_crlf)):
            if crlf: text = text.replace("\n", "\r\n")
            tmp = p + ".rt16.tmp"
            with open(tmp, "wb") as f: f.write(text.encode("utf-8"))
            tmps.append((tmp, p))
    except Exception as e:
        for tmp, _ in tmps:
            try: os.remove(tmp)
            except OSError: pass
        sys.exit(f"ABORT: could not stage output ({e}) — no files written")
    for tmp, p in tmps: os.replace(tmp, p)
    print("Written: app.js, index.html (app.js?v=chat15)")


if __name__ == "__main__":
    main()
