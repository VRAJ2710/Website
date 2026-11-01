#!/usr/bin/env python3
"""chat93: credibility redesign (groups A-F). Exact-count edits; any miss aborts with no files written.
usage: patch_chat93.py SERVER APP INDEX PATCHDIR"""
import sys, os, re
srv_p, app_p, idx_p, pdir = sys.argv[1:5]
def rd(p): return open(p, encoding="utf-8").read()
S, A, I = rd(srv_p), rd(app_p), rd(idx_p)
PRE, POST = rd(os.path.join(pdir, "c93_pre.js")), rd(os.path.join(pdir, "c93_post.js"))
PAGES, FE88 = rd(os.path.join(pdir, "c93_server_pages.js")), rd(os.path.join(pdir, "c93_fe88_company.js"))
import json
PAGES = PAGES.replace('/*C93_LIVE_JS*/""', json.dumps(rd(os.path.join(pdir, "c93_live.js")).strip()).replace("</", "<\\/"), 1)
assert "/*C93_LIVE_JS*/" not in PAGES
fails = []
def edit(src, label, old, new, count=1):
    n = src.count(old)
    if n != count:
        fails.append("%s: expected %d, found %d" % (label, count, n)); return src
    return src.replace(old, new)
def between(src, label, start, end, new):
    i = src.find(start)
    if i < 0 or src.find(start, i + 1) >= 0: fails.append(label + ": start not unique"); return src
    j = src.find(end, i)
    if j < 0: fails.append(label + ": end missing"); return src
    return src[:i] + new + src[j:]

# ───────────────────────── server.js ─────────────────────────
S = edit(S, "s.rootfiles", 'const RT52OPS_ROOT_FILES = new Set(["/app.js","/styles.css",', 'const RT52OPS_ROOT_FILES = new Set(["/app.js","/styles.css","/c93.css",')
S = edit(S, "s.rt20pre", 'const RT20S_PRE = new Set(["/app.js", "/styles.css"]);', 'const RT20S_PRE = new Set(["/app.js", "/styles.css", "/c93.css"]);')
S = edit(S, "s.routes", '  { // rt43s: pricing page, /upgrade, shared energy spot\n',
  '  { // chat93: trust pages and a brand-correct web manifest\n'
  '    let c93p = ""; try { c93p = new URL(req.url, "http://localhost").pathname; } catch {}\n'
  '    if (req.method === "GET" || req.method === "HEAD") {\n'
  '      if (c93p === "/manifest.json") return c93Manifest(req, res);\n'
  '      const c93k = c93p.length > 1 ? c93p.replace(/\\/+$/, "") : c93p;\n'
  '      if (Object.prototype.hasOwnProperty.call(C93_PAGES, c93k)) return c93Send(req, res, c93k);\n'
  '    }\n'
  '  }\n'
  '  { // rt43s: pricing page, /upgrade, shared energy spot\n')
S = edit(S, "s.pagesblock", "// rt43s: pricing, shared energy spot, honest reference/last-good marking, synthetic DXY from live FX\n",
  PAGES + "\n// rt43s: pricing, shared energy spot, honest reference/last-good marking, synthetic DXY from live FX\n")
# pricing on the paper template
S = between(S, "s.pricing", '  return res.end(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pricing · The Dispatch Market</title>',
  '</main></body></html>`);\n}',
  '  return res.end(c93Page("Pricing", "/pricing", "The Dispatch Market: Free and Premium (£15/month) plans.", `<h1>Pricing</h1><p class="lede">One upgrade, no token mark-up. Prices in GBP, billed monthly through Stripe.</p>'
  '<div class="c93g"><section class="c93c"><h2>Free</h2><p class="c93pr">£0</p><ul>${li(RT43S_FREE)}</ul></section>'
  '<section class="c93c c93cp"><h2>Premium</h2><p class="c93pr">£15/month</p><ul>${li(RT43S_PREM)}</ul></section></div>'
  '<p>${cta}</p><p class="muted">Research and data for information only. Not investment advice. Capital at risk. See the <a href="/terms">Terms</a> and <a href="/privacy">Privacy notice</a>.</p>`));\n  //')
S = edit(S, "s.pricing.tail", '  //</main></body></html>`);\n}', '}')
# legal pages
S = edit(S, "s.legal.mail", 'mailto:support@thedispatch.uk\\">support@thedispatch.uk</a>', 'mailto:dispatchmarket@mail.grokbot.com\\">dispatchmarket@mail.grokbot.com</a>', 2)
S = between(S, "s.legal.html", '  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} | The Dispatch Market</title>',
  '\n  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600" });\n  res.end(html);',
  '  const html = c93Page(title, terms ? "/terms" : "/privacy", terms ? "Terms of use for The Dispatch Market." : "How The Dispatch Market handles your data.", `<h1>${title}</h1>${body}`);')
# 404 pages
OLD404 = '<style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px system-ui;display:grid;place-items:center;min-height:100vh}main{width:min(620px,calc(100% - 40px));background:#111a26;border:1px solid #293849;border-radius:14px;padding:28px;box-sizing:border-box}h1{font-size:28px;margin:0 0 8px;color:#f5a623}p,li{color:#9baabb;line-height:1.6}a{color:#f5a623}ul{padding-left:22px}</style>'
NEW404 = '<meta name="theme-color" content="#fbfaf7"><style>body{margin:0;background:#fbfaf7;color:#1b1b1b;font:17px/1.6 Inter,system-ui,-apple-system,Segoe UI,Arial,sans-serif}main{max-width:680px;margin:0 auto;padding:48px 20px;box-sizing:border-box}.k{font-size:14px;color:#66655f;margin:0 0 6px}h1{font:600 32px/1.2 "Source Serif 4",Georgia,serif;margin:0 0 10px}p,li{color:#2b2a26}a{color:#1f3a5f}ul{padding-left:22px}li{margin:4px 0}.d{margin-top:28px;padding-top:14px;border-top:1px solid rgba(27,27,27,.2);font-size:14px;color:#45443f}</style>'
S = edit(S, "s.404.style", OLD404, NEW404, 2)
S = edit(S, "s.404.k", '<p>THE DISPATCH MARKET · 404</p>', '<p class="k">The Dispatch Market · Page not found</p>', 2)
S = edit(S, "s.404.disc", '</ul></main></body></html>', '</ul><p class="d"><strong>Not investment advice. Capital at risk.</strong> <a href="/about">About</a> · <a href="/methodology">Methodology</a> · <a href="/contact">Contact</a></p></main></body></html>', 2)
# auth/subscribe pages: paper instead of dark (same structure and fields)
S = edit(S, "s.page.style",
  '  <style>body{margin:0;background:#0b1018;color:#e8edf3;font:16px system-ui;display:grid;place-items:center;min-height:100vh}\n'
  '  main{width:min(420px,calc(100% - 40px));background:#111a26;border:1px solid #293849;border-radius:14px;padding:28px;box-sizing:border-box}\n'
  '  h1{font-size:22px;margin:0 0 8px;color:#f5a623}p{color:#9baabb;line-height:1.5}label{display:block;color:#b8c4d2;font-size:13px;margin:16px 0 6px}\n'
  '  input{width:100%;box-sizing:border-box;padding:11px;background:#0b1018;color:#fff;border:1px solid #3a4a5d;border-radius:7px}\n'
  '  button,a{display:inline-block;margin-top:20px;padding:11px 16px;border:0;border-radius:7px;background:#f5a623;color:#111;font-weight:700;text-decoration:none;cursor:pointer}\n'
  '  .muted{font-size:12px;color:#718096}</style>',
  '  <meta name="theme-color" content="#fbfaf7"><style>body{margin:0;background:#fbfaf7;color:#1b1b1b;font:16px/1.55 Inter,system-ui,-apple-system,"Segoe UI",Arial,sans-serif;display:grid;place-items:center;min-height:100vh}\n'
  '  main{width:min(420px,calc(100% - 40px));background:#fff;border:1px solid rgba(27,27,27,.16);border-radius:6px;padding:28px;box-sizing:border-box}\n'
  '  h1{font:600 22px/1.25 "Source Serif 4",Georgia,serif;margin:0 0 8px;color:#1b1b1b;letter-spacing:0}p{color:#45443f;line-height:1.5}label{display:block;color:#2b2a26;font-size:13px;font-weight:600;margin:16px 0 6px}\n'
  '  input{width:100%;box-sizing:border-box;padding:11px;background:#fff;color:#1b1b1b;border:1px solid rgba(27,27,27,.3);border-radius:4px;font:inherit}\n'
  '  button,a{display:inline-block;margin-top:20px;padding:11px 16px;border:0;border-radius:4px;background:#1f3a5f;color:#fff;font-weight:600;text-decoration:none;cursor:pointer;font-family:inherit}\n'
  '  .muted{font-size:12px;color:#66655f}.muted a{display:inline;margin:0;padding:0;background:none;color:#1f3a5f;font-weight:400;text-decoration:underline}</style>')
S = edit(S, "s.page.legal", 'style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Terms</a> · <a href="/privacy" style="display:inline;margin:0;padding:0;background:none;color:#9baabb;font-weight:400;text-decoration:underline">Privacy</a></p>',
  'style="display:inline;margin:0;padding:0;background:none;color:#45443f;font-weight:400;text-decoration:underline">Terms</a> · <a href="/privacy" style="display:inline;margin:0;padding:0;background:none;color:#45443f;font-weight:400;text-decoration:underline">Privacy</a><br>Not investment advice. Capital at risk.</p>')
S = edit(S, "s.login.brand", '<h1>THE DISPATCH</h1><p>Sign in to your market intelligence workspace.</p>', '<h1>The Dispatch Market</h1><p>Sign in to your account.</p>')
# sitemap
S = edit(S, "s.sitemap", '  const publishedCandidates = databaseReady\n',
  '  for (const c93u of ["/about", "/methodology", "/editorial-standards", "/corrections", "/contact"]) staticUrls.push(`  <url><loc>${PUBLIC_ORIGIN}${c93u}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>`); // chat93\n'
  '  for (const c93u of ["/research/capital-sustainability", "/research/capital-sustainability/method"].concat(typeof BB11_TICKERS !== "undefined" ? BB11_TICKERS.map(t => "/research/capital-sustainability/" + t) : [])) staticUrls.push(`  <url><loc>${PUBLIC_ORIGIN}${c93u}</loc><changefreq>daily</changefreq><priority>0.6</priority></url>`); // chat93 monitor\n'
  '  const publishedCandidates = databaseReady\n')
# signals wording (no "conviction")
S = edit(S, "s.sig.title", 'title: "Market Signals | Conviction-Weighted Macro Signals | The Dispatch Market",', 'title: "Market Signals | Macro Signals Explained | The Dispatch Market",')
S = edit(S, "s.sig.desc", 'description: "Review conviction-weighted market signals across macro, equities, gold, and risk appetite', 'description: "Review evidence-weighted market signals across macro, equities, gold, and risk appetite')
S = edit(S, "s.sig.h1", 'h1: "Market Signals: conviction-weighted macro context",', 'h1: "Market Signals: evidence-weighted macro context",')
S = edit(S, "s.research.deck", 'and conviction-weighted outlooks."', 'and evidence-weighted outlooks."')
# maintenance page brand
S = edit(S, "s.maint.title", "'<title>The Dispatch \\u2014 Under maintenance</title>'", "'<title>The Dispatch Market \\u2014 Under maintenance</title>'")
S = edit(S, "s.maint.k", '<p class="k">The Dispatch</p><h1>Under maintenance</h1>', '<p class="k">The Dispatch Market</p><h1>Under maintenance</h1>')
# SEC daily download counter survives restarts: existing table, no DDL
S = edit(S, "s.bb11.persist",
  '    await fsp.writeFile(tmp, JSON.stringify(snap)); await fsp.rename(tmp, BB11_FILE);\n    st.persist = { ok: true, error: null, saved_at: snap.saved_at };\n',
  '    await fsp.writeFile(tmp, JSON.stringify(snap)); await fsp.rename(tmp, BB11_FILE);\n    st.persist = { ok: true, error: null, saved_at: snap.saved_at };\n'
  '    if (databaseReady && sql) { try { await withTimeout(sql`INSERT INTO dispatch_openbb_research_cache (cache_key, value, expires_at, updated_at) VALUES (\'bb11:sec_downloads\', ${JSON.stringify({ day: st.sec.day, facts_today: st.sec.facts_today })}::jsonb, NOW() + interval \'3 days\', NOW()) ON CONFLICT (cache_key) DO UPDATE SET value = EXCLUDED.value, expires_at = EXCLUDED.expires_at, updated_at = NOW()`, 3000, "bb11 sec counter save timed out"); } catch (e) { /* chat93: best effort; the file copy above still holds */ } }\n')
S = edit(S, "s.bb11.ensure",
  '    } catch (e) { /* no file: seed */ }\n    bb11St = st; return st;\n',
  '    } catch (e) { /* no file: seed */ }\n'
  '    if (databaseReady && sql) { try {                                     // chat93: the SEC download count survives a redeploy that loses the file\n'
  '      var c93r = await withTimeout(sql`SELECT value FROM dispatch_openbb_research_cache WHERE cache_key = \'bb11:sec_downloads\' LIMIT 1`, 3000, "bb11 sec counter read timed out");\n'
  '      var c93v = c93r && c93r[0] && c93r[0].value; if (typeof c93v === "string") c93v = JSON.parse(c93v);\n'
  '      if (c93v && c93v.day === bb11UkDay(bb11Now()) && Number(c93v.facts_today) > Number(st.sec.facts_today || 0)) { st.sec.day = c93v.day; st.sec.facts_today = Number(c93v.facts_today); }\n'
  '    } catch (e) { /* no row or no DB: keep the file value */ } }\n'
  '    bb11St = st; return st;\n')

S = edit(S, "s.c93route", "// BB11_JS_END", "// BB11_JS_END\n// chat93: guest Home and the Capital Sustainability Monitor pages, server-rendered (inside the maintenance wrapper)\nvar c93Prev = bb10iHandle0;\nbb10iHandle0 = async function c93Handle(req, res) {\n  try { if (await c93Route(req, res)) return; } catch (e) { if (res.headersSent || res.writableEnded) return; }\n  return c93Prev.apply(this, arguments);\n};\n// C93_JS_END")
# ───────────────────────── app.js ─────────────────────────
A = edit(A, "a.kicker", '<div class="pg-hdr-kicker">THE DISPATCH · RESEARCH TERMINAL</div>', '<div class="pg-hdr-kicker">THE DISPATCH MARKET</div>')
A = edit(A, "a.nls.geo", '<span style="color:var(--t3)">NO LIVE SYNC${context.status', '<span style="color:var(--t3)">Delayed${context.status')
A = edit(A, "a.nls.tbl", "'<span style=\"color:var(--t3);opacity:0.55\">NO LIVE SYNC</span>'", "''")
A = edit(A, "a.tape", "function fe73_keepTape() {\n  var t = document.querySelector(\".tape\");", "function fe73_keepTape() {\n  if (document.documentElement.classList.contains(\"c93\")) return; // chat93: calm desk, no ticker tape\n  var t = document.querySelector(\".tape\");")
A = edit(A, "a.mkt.skip", "    const na = !hasSyncedQuote(a.tk);\n    const ch = liveChg(a.tk);\n    const col = na || ch == null ?", "    const na = !hasSyncedQuote(a.tk);\n    if (na && a.cat !== 'Crypto') return; // chat93: no placeholder rows\n    const ch = liveChg(a.tk);\n    const col = na || ch == null ?")
A = edit(A, "a.nls.status", '(d.status || "NO LIVE SYNC").toUpperCase()', 'String(d.status || "No current price")')
A = edit(A, "a.nls.dyn", ":'NO LIVE SYNC'}", ":'Price delayed'}")
A = edit(A, "a.nls.tk", "`${tk} NO LIVE SYNC`", "`${tk}: no current price`")
A = edit(A, "a.sess.1", "`${c.priced} prices · markets closed`", "`${c.priced} prices · US stocks closed`")
A = edit(A, "a.sess.2", "`${priced} prices · markets closed`", "`${priced} prices · US stocks closed`")
A = edit(A, "a.sess.3", "return `Markets closed${lc ?", "return `US stocks closed${lc ?")
A = edit(A, "a.rt53.omit", "  return '<article class=\"bb1-tile\" data-bb1-tile=\"' + id", "  if (value === \"\\u2014\") return \"\"; // chat93: no figure, no tile\n  return '<article class=\"bb1-tile\" data-bb1-tile=\"' + id")
A = edit(A, "a.rt53.inner", "function _rt53Inner() { return '<div class=\"bb1-h\">Macro</div><div class=\"bb1-grid\">' + _rt53TileList().map(_rt53One).join(\"\") + '</div>'; }",
  "function _rt53Inner() { var l = _rt53TileList(), t = l.map(_rt53One).filter(Boolean); if (!t.length) return \"\"; return '<div class=\"bb1-h\">Macro</div><div class=\"bb1-grid\">' + t.join(\"\") + '</div>' + (t.length < l.length ? '<p class=\"c93-note\">Some prices are delayed; we show the last official figure with its date.</p>' : ''); }")
A = edit(A, "a.onaccent", "color:#14151A", "color:var(--on-accent,#14151A)", 10)
A = edit(A, "a.chart.lazy", "    if (candles.length < 3) throw new Error('insufficient data');\n",
  '    if (typeof LightweightCharts === "undefined" && typeof c93_loadCharts === "function") { await c93_loadCharts(); if (_chartLoad.tk !== tk || _chartLoad.cid !== containerId) return; }\n'
  "    if (candles.length < 3) throw new Error('insufficient data');\n")
A = edit(A, "a.chart.col", "const upCol = '#00C896', dnCol = '#FF4757';", "const upCol = '#2f6b47', dnCol = '#a23b2a';")
# Dispatch Brief card
A = edit(A, "a.brief.tier", 'DISPATCH BRIEF · ${b.date || "TODAY"} · ${tierLbl}${(b._local || b._free || b._fallback) ? " · MODEL (NOT LLM)" : " · AI"}',
  'DISPATCH BRIEF · ${b.date || "TODAY"}${(b._local || b._free || b._fallback) ? " · Built from today\'s data" : " · AI-assisted draft"}')
A = edit(A, "a.brief.conf", '        ${b.confidence > 0 ? `<span style="font-family:var(--mn);font-size:10px;color:var(--t3)">Confidence ${b.confidence}</span>` : ""}\n', '')
A = edit(A, "a.brief.focus", 'letter-spacing:0.15em;margin-bottom:6px">FOCUS TICKERS</div>', 'letter-spacing:0.15em;margin-bottom:6px">COMPANIES MENTIONED</div>')
A = edit(A, "a.brief.clip", 'cursor:pointer">${_rt16Clip(t, 28)}</button>', 'cursor:pointer">${tk}</button>')
A = edit(A, "a.brief.cats", '${b.catalysts.map(c => `<div style="font-size:10px;color:var(--t2);padding:2px 0">⚡ ${c}</div>`).join("")}',
  '${b.catalysts.map(c => `<div style="font-size:10px;color:var(--t2);padding:2px 0">${String(c).replace(/\\s*\\(\\d{1,3}%\\)/g, "").replace(/\\s*\\d{1,3}\\/100/g, "")}</div>`).join("")}')
A = edit(A, "a.brief.risks", '${b.risks?.length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px">RISKS</div>${b.risks.map(r => `<div style="font-size:10px;color:var(--t2);padding:2px 0">⚠ ${r}</div>`).join("")}',
  '${b.risks?.filter(r => r && String(r).trim()).length ? `<div><div style="font-family:var(--mn);font-size:7px;color:var(--rd);letter-spacing:0.12em;margin-bottom:4px">RISKS</div>${b.risks.filter(r => r && String(r).trim()).map(r => `<div style="font-size:10px;color:var(--t2);padding:2px 0">${r}</div>`).join("")}')
A = edit(A, "a.brief.actions", '<span style="color:var(--pu)">→</span>${a}</div>`).join("")}',
  '<span style="color:var(--pu)">→</span>${String(a).replace(/\\s*\\(\\d{1,3}%\\)/g, "").replace(/\\s*\\d{1,3}\\/100/g, "")}</div>`).join("")}')
A = edit(A, "a.brief.foot", 'padding:8px;border-top:1px dotted var(--gb)">House view · Research only · Not investment advice</div>', 'padding:8px;border-top:1px dotted var(--gb)">House view · Not investment advice. Capital at risk.</div>')
# Brief page: drop the terminal clutter
A = edit(A, "a.rb.strip", '  h += _renderNeuralSessionStrip();\n  h += _renderSiteIntelCard("brief");\n  h += _renderOpenBbCustomerCard("brief", "Historical context for the house view");\n  const editorialBrief', '  const editorialBrief')
A = edit(A, "a.rb.routine", '  h += `<div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">${_renderMorningRoutineBtn(true)}</div>`;\n\n  h += _renderRegimeEngine();', '  h += _renderRegimeEngine();')
A = between(A, "a.rb.journal", '  h += `<div class="sec-label">Research Journal</div>`;\n  h += _renderLensJournal(8);\n', '  return h;\n}\n\n// ═══', '')
# desk-score lines
A = edit(A, "a.fe77.line", '  return "Top desk score: " + tk + " " + sc + "/100 (Dispatch desk score).";', '  return ""; // chat93: no desk-score line in reader copy')
A = edit(A, "a.fe77.scrub", "  return String(s == null ? \"\" : s).replace(/Highest conviction on desk:\\s*([A-Z0-9.^]+)\\s*\\(\\s*(\\d+)\\s*\\/\\s*100[^)]*\\)\\.?/gi, function (_m, tk, n) {\n    return fe77_deskLine(tk, n);\n  });",
  "  return String(s == null ? \"\" : s).replace(/Highest conviction on desk:\\s*([A-Z0-9.^]+)\\s*\\(\\s*(\\d+)\\s*\\/\\s*100[^)]*\\)\\.?\\s*/gi, \"\").replace(/Top desk score: [A-Z0-9.^-]+ \\d+\\/100 \\(Dispatch desk score\\)\\.\\s*/g, \"\");")
A = edit(A, "a.fe77.apply", '  if (extra && String(b.summary || "").indexOf("Top desk score:") < 0) b.summary = (extra + " " + (b.summary || "")).trim();\n', '')
A = edit(A, "a.fe82.loading", '    return "Regime inputs were still loading when this brief was built";', '    return "";')
A = edit(A, "a.fe82.off", 'return "Risk-off at brief time (" + re.score + "/100) — size down high-beta first";', 'return "Risk appetite was weak when this brief was built (regime reading " + re.score + " of 100)";')
A = edit(A, "a.fe82.on", 'return "Risk-on can reverse fast if VIX spikes";', 'return "Risk appetite can turn quickly if volatility (the VIX) jumps";')
# footer
A = between(A, "a.footer", 'function _siteFooter(){\n', '(function _uiCss14() {',
  'function _siteFooter(){\n'
  '  // chat93: one trust footer on every app page. The time is the last successful price refresh, UK time.\n'
  '  const _lf = _rt16LastFeed();\n'
  '  const upd = _lf ? `Prices last refreshed <span class="stf-time">${_rt16Hms(_lf)}</span> UK time` : "";\n'
  '  return `<footer class="site-trust-footer c93-foot">\n'
  '    <p class="c93-foot-disc"><strong>Not investment advice. Capital at risk.</strong> Prices come from free market feeds and may be delayed; every time is UK time.</p>\n'
  '    <p class="c93-foot-links"><a href="/about">About</a><a href="/editorial-standards">Editorial standards</a><a href="/methodology">Methodology</a><a href="/corrections">Corrections</a><a href="/contact">Contact</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></p>\n'
  '    <p class="c93-foot-brand">The Dispatch Market · Edited by Vraj Patel, London${upd ? " · " + upd : ""}</p>\n'
  '  </footer>`;\n'
  '}\n')
# monitor (fe88)
A = edit(A, "a.fe88.miss", "return '<span class=\"fe88-miss\" aria-label=\"' + fe88_esc(label) + '\">\\u2014</span>';", "return '<span class=\"fe88-miss\" title=\"' + fe88_esc(label) + '\"></span>';")
A = edit(A, "a.fe88.mark", '  if (s === "red") return "R";\n  if (s === "amber") return "A";\n  if (s === "green") return "G";\n  if (s === "n/a" || s === "n-a" || s === "na") return "n/a";',
  '  if (s === "red") return "Red";\n  if (s === "amber") return "Amber";\n  if (s === "green") return "Green";\n  if (s === "n/a" || s === "n-a" || s === "na") return "Not disclosed";')
A = edit(A, "a.fe88.flagbadge", '  var mark = fe88_flagMark(overall) || "n/a";\n  var flags = (flag && flag.flags) || {};', '  var mark = fe88_flagMark(overall) || "Not in filing";\n  var flags = (flag && flag.flags) || {};')
A = edit(A, "a.fe88.label", '  if (!obj.label) return "";\n  return obj.label;\n',
  '  if (!obj.label) return "";\n  return obj.label.replace(/(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}) UTC/g, function (m0, t0) { return fe88_uk(t0 + " UTC") || m0; });\n')
A = edit(A, "a.fe88.legend", "'<p class=\"fe88-legend\">R red, A amber, G green, n/a not disclosed. The five flags",
  "'<p class=\"fe88-legend\">Flags read Green, Amber or Red; \\u2018Not disclosed\\u2019 means the filing does not give the figure. The five flags")
A = edit(A, "a.fe88.rowco", "  var company = row.company ? '<span class=\"fe88-co\">' + fe88_esc(row.company) + \"</span>\" : \"\";", "  var company = row.company ? '<span class=\"fe88-co\">' + fe88_esc(fe88_tc(row.company)) + \"</span>\" : \"\";")
A = between(A, "a.fe88.company", "function fe88_companyHtml(payload, neighbors) {\n", "function fe88_methodHtml(payload) {\n", FE88)
# wrap: prepend runtime guards, append the shell
A = PRE.rstrip("\n") + "\n" + A.rstrip("\n") + "\n" + POST.rstrip("\n") + "\n"

# ───────────────────────── index.html ─────────────────────────
I = edit(I, "i.theme", "  document.documentElement.classList.add('fe64-js');\n", "  document.documentElement.classList.add('fe64-js');\n  document.documentElement.classList.add('c93');\n")
I = edit(I, "i.apple", '<meta name="apple-mobile-web-app-title" content="The Dispatch">', '<meta name="apple-mobile-web-app-title" content="The Dispatch Market">')
I = edit(I, "i.themecolor", '<meta name="theme-color" content="#14151A">', '<meta name="theme-color" content="#fbfaf7">')
I = edit(I, "i.statusbar", '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', '<meta name="apple-mobile-web-app-status-bar-style" content="default">')
I = edit(I, "i.fonts", "family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=optional", "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap")
I = edit(I, "i.css", '<link rel="stylesheet" href="/styles.css?v=chat1">', '<link rel="stylesheet" href="/styles.css?v=chat1"><link rel="stylesheet" href="/c93.css?v=chat93">')
I = edit(I, "i.charts", '<script defer src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>\n', '')
I = edit(I, "i.appjs", '<script defer src="/app.js?v=chat91"></script>', '<script defer src="/app.js?v=chat93"></script>')
# boot veil text stays 'Loading Dispatch': fe72_isBoot matches /loading dispatch/i
NAV = ('<nav class="c93-nav" id="c93Nav" aria-label="Main"><a href="/brief/" data-c93-nav="brief">Brief</a><a href="/gold/" data-c93-nav="gold">Gold</a>'
       '<a href="/markets/" data-c93-nav="mkt">Markets</a><a href="/research/" data-c93-nav="research">Research</a><a href="/methodology">Methodology</a><a href="/about">About</a>'
       '<button type="button" class="c93-more" aria-controls="c93Menu" aria-expanded="false">Tools</button></nav>')
STRIP = '<p class="c93-strip"><strong>Not investment advice. Capital at risk.</strong> Figures carry their source and UK time; free feeds may be delayed.</p>'
I = between(I, "i.cmdlogo", '  <div class="cmd-logo" aria-label="The Dispatch Market" role="button"', '  <div class="cmd-ac-wrap">',
  '  <a class="cmd-logo" href="/" aria-label="The Dispatch Market home"><span class="cmd-logo-text">The Dispatch Market</span></a>\n  ' + NAV + '\n')
I = edit(I, "i.cmdstrip", '  <div class="cmd-clk" id="cmdClk"></div>\n</div>\n', '  <div class="cmd-clk" id="cmdClk"></div>\n  ' + STRIP + '\n</div>\n')
I = edit(I, "i.p3a", '<span class="panel-sub">CONVICTION-WEIGHTED</span>', '<span class="panel-sub">EVIDENCE-WEIGHTED</span>')
I = edit(I, "i.p3b", 'Conviction-weighted macro context, not trading instructions.', 'Evidence-weighted macro context, not trading instructions.')
I = between(I, "i.hdrlogo", '    <div class="logo" onclick="openAbout()" aria-label="The Dispatch Market"', '    <div class="srch" onclick="openSearch()"',
  '    <a class="logo" href="/" aria-label="The Dispatch Market home"><span class="logo-text"><span class="logo-the">The</span><span class="logo-disp">Dispatch</span><span class="logo-markets">Market</span></span></a>\n'
  '    <button type="button" class="c93-menu-btn" aria-controls="c93Menu" aria-expanded="false">Menu</button>\n')
I = edit(I, "i.hdrstrip", '    <div><div class="clk" id="clk"></div><div class="clk-d" id="clkD"></div></div>\n  </header>', '    <div><div class="clk" id="clk"></div><div class="clk-d" id="clkD"></div></div>\n    ' + STRIP + '\n  </header>')
I = edit(I, "i.seo.eyebrow", '<p class="seo-public-eyebrow">THE DISPATCH MARKET · PUBLIC MARKET DESK</p>', '<p class="seo-public-eyebrow">THE DISPATCH MARKET · EDITED BY VRAJ PATEL, LONDON</p>')
I = edit(I, "i.seo.h1", '<h1 id="seo-public-title">Market intelligence for the moves that matter</h1>', '<h1 id="seo-public-title">Verified gold and macro research for independent investors</h1>')
I = edit(I, "i.seo.intro", 'Follow the evidence, understand the regime, and act on your own judgment.</p>', 'Every figure carries its source and the time it was checked, in UK time.</p>')
I = edit(I, "i.seo.conv", 'The Dispatch combines price context, sector rotation, conviction-weighted signals, and relevant news', 'The Dispatch Market combines price context, sector rotation, evidence-weighted signals, and relevant news')
I = edit(I, "i.seo.note", 'nothing on this site is financial advice or a recommendation to buy or sell an instrument.</p></aside>', 'nothing on this site is financial advice or a recommendation to buy or sell an instrument. Not investment advice. Capital at risk.</p><p><a href="/about">About</a> · <a href="/methodology">Methodology</a> · <a href="/editorial-standards">Editorial standards</a> · <a href="/contact">Contact</a></p></aside>')
I = edit(I, "i.about.tag", '<div class="about-tag">A gold and macro research house</div>', '<div class="about-tag">Verified gold and macro research for independent investors, with sources on every figure.</div>')
I = edit(I, "i.about.job", 'The Dispatch turns delayed, disclosed market data', 'The Dispatch Market turns delayed, disclosed market data')
I = edit(I, "i.about.h", '<h3 class="about-h">Founder &amp; analyst</h3>', '<h3 class="about-h">Editor</h3>')
I = edit(I, "i.about.avatar", '        <div class="about-avatar">V</div>\n', '')
I = edit(I, "i.about.role", '<div class="about-role">Founder · Analyst</div>', '<div class="about-role">Edited by Vraj Patel, London</div>')
I = edit(I, "i.about.copy", 'Independent market researcher and platform builder.</div>', 'Independent market researcher. <a href="/about">About The Dispatch Market</a> · <a href="/methodology">Methodology</a></div>')
I = edit(I, "i.about.disc", 'Nothing here is financial advice or a recommendation to buy or sell.</div>', 'Nothing here is financial advice or a recommendation to buy or sell. Not investment advice. Capital at risk.</div>')

if fails:
    sys.stderr.write("chat93 patch FAILED, nothing written:\n  " + "\n  ".join(fails) + "\n"); sys.exit(2)
for p, s in ((srv_p, S), (app_p, A), (idx_p, I)):
    tmp = p + ".c93tmp"; open(tmp, "w", encoding="utf-8").write(s); os.replace(tmp, p)
print("chat93 patch applied: server, app, index")
