#!/usr/bin/env python3
"""patch_rt52s.py: server.js. 13F v2 + admin Console wording + styled admin-only page.
- /api/institutional-data?type=13f now uses institutional13fV2(): US-dollar values (per-filing unit check: filers that still send
  thousands are scaled), positions summed by CUSIP, change vs the previous quarter's 13F-HR (amendments and 13F-NT notices skipped),
  new and sold-out positions, % of the reported portfolio, quarter labels, tickers from OpenFIGI (free, keyless, 10 per request)
  with an SEC company_tickers name match as backup. Managers fetched in parallel; the result is kept 6h in memory and in the temp
  dir (stale copy served while a rebuild runs). The old institutional13f()/parse13f() stay in place, unused.
- /__admin: Console copy says "access code"/"private settings" instead of "key"/"Replit Secrets"; content names read as words
  ("SPX 2026", or the record's title); visitors who are not administrators get a styled page (still HTTP 403).
No DB, no new tables, no Stripe, no secrets. Does not touch the rt52ops anchors (non-public files, og-card, SRI).
Usage: python3 patch_rt52s.py [--check] server.js"""
import sys, subprocess, tempfile, os
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
def die(m): print('ABORT (nothing written):', m); sys.exit(1)
if '// ── rt52s' in s: die('rt52s already applied')
A1 = 'async function institutional13f() {'
A2 = 'return json(res, 200, await institutional13f());'
A3 = 'if (!isAdminUser(user)) return text(res, 403, "Administrator access required.");'
A4 = 'return text(res, 200, RT50_CONSOLE_HTML, "text/html; charset=utf-8"); // rt50console'
for a in (A1, A2, A3):
    if s.count(a) != 1: die('server.js anchor matched %d times: %s' % (s.count(a), a))
for need in ('const SEC_13F_MANAGERS', 'function sec13fInformationTableUrl(', 'async function secText(', 'async function readTextCapped(', 'const secRateLimiter', 'function institutionalResponse('):
    if need not in s: die('server.js missing ' + need)
BLOCK = r'''// ── rt52s: 13F v2 ── values in US dollars (unit checked per filing), positions summed by CUSIP, change vs the previous
// quarter's 13F-HR (amendments and 13F-NT notices skipped), new and sold-out positions, % of the reported portfolio, tickers from
// OpenFIGI (free, keyless) with an SEC company_tickers name match as fallback. Result kept 6h in memory and in the temp dir.
const RT52_13F_FILE = require("path").join(require("os").tmpdir(), "dispatch-13f-v2.json");
const RT52_13F = { at: 0, data: null, inflight: null };
const RT52_FIGI = new Map();
const RT52_SECTK = { at: 0, byName: null };
function rt52Load13f() { try { const o = JSON.parse(require("fs").readFileSync(RT52_13F_FILE, "utf8")); if (o && o.v === 2 && o.data && Array.isArray(o.data.items) && Date.now() - o.at < 6 * 3600_000) { RT52_13F.at = o.at; RT52_13F.data = o.data; } } catch (e) {} }
function rt52Save13f() { try { require("fs").writeFileSync(RT52_13F_FILE, JSON.stringify({ v: 2, at: RT52_13F.at, data: RT52_13F.data })); } catch (e) {} }
async function rt52SecBig(url) {
  if (!secRateLimiter.allow("sec")) throw new Error("SEC rate limit reached.");
  const response = await fetch(url, { headers: { "User-Agent": SEC_USER_AGENT, Accept: "application/xml, text/xml, application/json;q=0.9" }, redirect: "error", signal: AbortSignal.timeout(15_000) });
  if (!response.ok) throw new Error(`SEC ${response.status}`);
  return readTextCapped(response, 6 * 1024 * 1024);
}
function rt52Quarter(period) { const m = /^(\d{4})-(\d{2})-\d{2}$/.exec(String(period || "")); if (!m) return null; return `Q${Math.ceil(Number(m[2]) / 3)} ${m[1]}`; }
function rt52Parse13f(xml) {
  const tables = String(xml).match(/<(?:[\w.-]+:)?infoTable(?:\s[^>]*)?>[\s\S]*?<\/(?:[\w.-]+:)?infoTable>/gi) || [];
  const rows = tables.map(t => ({
    cusip: (xmlValue(t, "cusip") || "").toUpperCase(), name: xmlValue(t, "nameOfIssuer") || "", cls: xmlValue(t, "titleOfClass") || "",
    raw: secNumber(xmlValue(t, "value")), shares: secNumber(xmlValue(t, "sshPrnamt")), type: (xmlValue(t, "sshPrnamtType") || "SH").toUpperCase(),
    putCall: (xmlValue(t, "putCall") || "").toUpperCase(),
  })).filter(r => r.raw != null);
  // Since 2023 the value column is in dollars; some filers still send thousands. A median price per share under $1 means thousands.
  const px = rows.filter(r => r.type === "SH" && !r.putCall && r.shares > 0 && r.raw > 0).map(r => r.raw / r.shares).sort((a, b) => a - b);
  const median = px.length ? px[Math.floor(px.length / 2)] : 1;
  const mult = median < 1 ? 1000 : 1;
  const pos = new Map(); let total = 0;
  for (const r of rows) {
    const value = r.raw * mult; total += value;
    if (r.putCall || r.type !== "SH") continue;
    const key = r.cusip || r.name.toUpperCase();
    const p = pos.get(key) || { cusip: r.cusip, name: r.name, cls: r.cls, shares: 0, value: 0 };
    p.shares += r.shares || 0; p.value += value; pos.set(key, p);
  }
  return { pos, total, unit: mult === 1000 ? "thousands" : "dollars", count: pos.size, options: rows.filter(r => r.putCall).length };
}
async function rt52Figi(cusips) {
  const need = [...new Set(cusips.filter(c => /^[0-9A-Z]{9}$/.test(c) && !(RT52_FIGI.has(c) && Date.now() - RT52_FIGI.get(c).at < 7 * 864e5)))];
  for (let i = 0; i < need.length && i < 200; i += 10) {
    const batch = need.slice(i, i + 10);
    try {
      const r = await fetch("https://api.openfigi.com/v3/mapping", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(batch.map(c => ({ idType: "ID_CUSIP", idValue: c, exchCode: "US" }))), signal: AbortSignal.timeout(8000) });
      if (!r.ok) break;
      const out = await r.json();
      batch.forEach((c, k) => { const d = (out[k] && out[k].data) || []; const hit = d.find(x => x.marketSector === "Equity" && x.ticker) || d[0]; RT52_FIGI.set(c, { at: Date.now(), t: hit && hit.ticker ? String(hit.ticker).toUpperCase().replace("/", ".") : null }); });
    } catch (e) { break; }
  }
}
function rt52NormName(s) {
  return " " + String(s || "").toUpperCase().replace(/&/g, " AND ").replace(/[.,'()\/-]/g, " ")
    .replace(/\b(INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|LLC|LP|NV|SA|AG|SE|HLDGS|HOLDINGS|HLDG|HOLDING|GROUP|GRP|THE|CL [A-Z]|CLASS [A-Z]|COM|NEW|DEL|ORD|SHS|ADR|SPONSORED|SPON)\b/g, " ")
    .replace(/\bFINL\b/g, "FINANCIAL").replace(/\bINTL\b/g, "INTERNATIONAL").replace(/\bTECHNOLOGIES\b|\bTECHNOLOGY\b/g, "TECH").replace(/\bSVCS\b/g, "SERVICES").replace(/\bMTRS\b/g, "MOTORS").replace(/\bPHARMACEUTICALS\b/g, "PHARMA")
    .replace(/\s+/g, " ").trim() + " ";
}
async function rt52SecTickers() {
  if (RT52_SECTK.byName && Date.now() - RT52_SECTK.at < 864e5) return RT52_SECTK.byName;
  try {
    const rows = JSON.parse(await rt52SecBig("https://www.sec.gov/files/company_tickers.json"));
    const m = new Map(); Object.values(rows || {}).forEach(r => { const k = rt52NormName(r && r.title).trim(); if (k && !m.has(k)) m.set(k, String(r.ticker || "").toUpperCase()); });
    RT52_SECTK.byName = m; RT52_SECTK.at = Date.now();
  } catch (e) {}
  return RT52_SECTK.byName;
}
async function rt52Build13f() {
  let failures = 0;
  const one = async ({ cik, manager }) => {
    try {
      const sub = JSON.parse(await secText(`https://data.sec.gov/submissions/CIK${cik}.json`));
      const r = sub?.filings?.recent || {}; const hr = [];
      let notice = null;
      for (let i = 0; i < Math.min(r.form?.length || 0, 120); i += 1) {
        if (r.form[i] === "13F-HR" && !hr.some(j => r.reportDate[j] === r.reportDate[i])) hr.push(i);
        if (r.form[i] === "13F-NT" && !notice && !hr.length) notice = { period: r.reportDate[i], filed: r.filingDate[i] };
        if (hr.length >= 2) break;
      }
      if (!hr.length) { failures += 1; return null; }
      const cur = hr[0], prv = hr[1];
      const curUrl = await sec13fInformationTableUrl(cik, r.accessionNumber[cur], r.primaryDocument[cur]);
      const now = rt52Parse13f(await rt52SecBig(curUrl));
      let before = null, priorPeriod = null;
      if (prv !== undefined) { try { before = rt52Parse13f(await rt52SecBig(await sec13fInformationTableUrl(cik, r.accessionNumber[prv], r.primaryDocument[prv]))); priorPeriod = r.reportDate[prv]; } catch (e) { before = null; } }
      const rows = [];
      const keys = new Set([...now.pos.keys(), ...(before ? before.pos.keys() : [])]);
      for (const k of keys) {
        const a = now.pos.get(k), b = before ? before.pos.get(k) : undefined;
        const shares = a ? a.shares : 0, prior = before ? (b ? b.shares : 0) : null;
        const price = a && a.shares > 0 ? a.value / a.shares : b && b.shares > 0 ? b.value / b.shares : 0;
        let action = "REPORTED";
        if (before) action = !b ? "NEW" : !a ? "SOLD OUT" : shares > prior ? "ADDED" : shares < prior ? "TRIMMED" : "UNCHANGED";
        const flow = prior == null ? (a ? a.value : 0) : Math.abs(shares - prior) * price;
        rows.push({ k, a, b, shares, prior, action, flow });
      }
      const moved = rows.filter(x => x.action !== "UNCHANGED").sort((x, y) => y.flow - x.flow).slice(0, 12);
      return ({ manager, cik, period: r.reportDate[cur], priorPeriod, filingDate: r.filingDate[cur], url: curUrl, total: now.total, count: now.count, unit: now.unit, notice: notice && notice.period > r.reportDate[cur] ? notice : null, moved, changed: before ? rows.filter(x => x.action !== "UNCHANGED").length : null });
    } catch (e) { failures += 1; return null; }
  };
  const managers = (await Promise.all(SEC_13F_MANAGERS.map(one))).filter(Boolean);
  const cusips = []; managers.forEach(m => m.moved.forEach(x => { const c = (x.a || x.b).cusip; if (c) cusips.push(c); }));
  await rt52Figi(cusips);
  const byName = await rt52SecTickers();
  const items = [];
  for (let i = 0; i < 12; i += 1) managers.forEach(m => {
    const x = m.moved[i]; if (!x) return; const s = x.a || x.b;
    const figi = s.cusip && RT52_FIGI.get(s.cusip); let ticker = figi && figi.t || null;
    if (!ticker && byName) ticker = byName.get(rt52NormName(s.name).trim()) || null;
    const value = x.a ? Math.round(x.a.value) : 0, priorValue = x.b ? Math.round(x.b.value) : null;
    items.push({
      manager: m.manager, ticker, security: s.name || null, cusip: s.cusip || null, titleOfClass: s.cls || null, action: x.action,
      shares: x.shares, priorShares: x.prior, sharesChange: x.prior == null ? null : x.shares - x.prior,
      sharesChangePct: x.prior > 0 ? Math.round(((x.shares - x.prior) / x.prior) * 1000) / 10 : null,
      value, priorValue, valueUnit: "USD", pctOfPortfolio: m.total > 0 && value ? Math.round((value / m.total) * 1000) / 10 : x.a ? 0 : null,
      portfolioValue: Math.round(m.total), positions: m.count, positionsChanged: m.changed,
      period: m.period, quarter: rt52Quarter(m.period), priorPeriod: m.priorPeriod, priorQuarter: rt52Quarter(m.priorPeriod),
      filingDate: m.filingDate, filedUnit: m.unit, laterNotice: m.notice, tickerSource: figi && figi.t ? "OpenFIGI" : ticker ? "SEC name match" : null, sourceUrl: m.url,
    });
  });
  const status = items.length ? (failures ? "partial" : "available") : "unavailable";
  const note = !items.length ? "No parseable curated-manager 13F filing was available." : failures ? `${failures} curated manager filing${failures === 1 ? "" : "s"} could not be refreshed.` : "";
  const out = institutionalResponse("13f", status, "SEC EDGAR", items.length ? new Date().toISOString() : null, items, note);
  out.version = 2; out.managers = managers.map(m => ({ manager: m.manager, quarter: rt52Quarter(m.period), period: m.period, priorQuarter: rt52Quarter(m.priorPeriod), filingDate: m.filingDate, portfolioValue: Math.round(m.total), positions: m.count, positionsChanged: m.changed, laterNotice: m.notice, sourceUrl: m.url }));
  return out;
}
async function institutional13fV2() {
  if (!RT52_13F.data) rt52Load13f();
  const fresh = RT52_13F.data && Date.now() - RT52_13F.at < 6 * 3600_000;
  if (fresh) return RT52_13F.data;
  if (!RT52_13F.inflight) RT52_13F.inflight = rt52Build13f().then(d => { if (d.items.length) { RT52_13F.data = d; RT52_13F.at = Date.now(); rt52Save13f(); } return d; }).catch(() => institutionalResponse("13f", "unavailable", "SEC EDGAR", null, [], "SEC EDGAR data is temporarily unavailable.")).finally(() => { RT52_13F.inflight = null; });
  if (RT52_13F.data) return RT52_13F.data; // stale: serve the last good result while the rebuild runs
  try { const d = await RT52_13F.inflight; return d.items.length || !RT52_13F.data ? d : RT52_13F.data; } catch (e) { if (RT52_13F.data) return RT52_13F.data; throw e; }
}
// rt52s: admin Console copy in plain words; a styled page for visitors who are not administrators
let rt52ConsoleMemo = null;
function rt52ConsoleHtml(html) {
  if (rt52ConsoleMemo && rt52ConsoleMemo.src === html) return rt52ConsoleMemo.out;
  const pairs = [
    ["To add it later, put its key in Replit Secrets.", "To add it later, create an access code on the provider's website and save it in your Replit project's private settings."],
    ["Fix: create a new key at \"+b+\" and update it in Replit Secrets.", "Fix: create a new access code at \"+b+\" and save it in your Replit project's private settings in place of the old one."],
    ["or the key isn't allowed to use it.", "or its access code isn't allowed to use it."],
    ["\"Key not accepted\"", "\"Access code not accepted\""],
    ["The saved key was rejected", "The saved access code was rejected"],
    ["No Twelve Data key is saved", "No Twelve Data access code is saved"],
    ["function niceKey(k){k=String(k||\"\").replace(/-/g,\" \");return k.charAt(0).toUpperCase()+k.slice(1)}",
     "function niceKey(k){k=String(k||\"\").replace(/[-_]+/g,\" \").replace(/([a-z])([0-9])/gi,\"$1 $2\").replace(/([a-z])([A-Z])/g,\"$1 $2\");return k.split(\" \").map(function(w){return /^[a-z]{2,4}$/i.test(w)&&/^(spx|ndx|dxy|vix|wti|xau|btc|eth|fed|ecb|boe|cpi|gdp|faq|ai)$/i.test(w)?w.toUpperCase():w.charAt(0).toUpperCase()+w.slice(1)}).join(\" \")}"],
    ["<b>'+esc(niceKey(x.key))+'</b>", "<b>'+esc((x.payload&&typeof x.payload===\"object\"&&(x.payload.title||x.payload.headline))||niceKey(x.key))+'</b>"],
  ];
  let out = String(html || "");
  for (const [a, b] of pairs) out = out.split(a).join(b);
  rt52ConsoleMemo = { src: html, out };
  return out;
}
const RT52_ADMIN_ONLY = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Administrators only | The Dispatch Markets</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:#0b0f17;color:#e6e9ef;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.c{width:100%;max-width:440px;background:#121826;border:1px solid #2a3346;border-radius:16px;padding:28px 24px;box-shadow:0 10px 40px rgba(0,0,0,.45)}.k{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.16em;color:#d4a64a}
h1{font:600 28px/1.2 Georgia,"Times New Roman",serif;margin:10px 0 8px}p{margin:0 0 18px;color:#c3c9d5}a.b{display:inline-block;background:#d4a64a;color:#0b0f17;text-decoration:none;font-weight:700;padding:11px 18px;border-radius:10px}a.b:focus-visible{outline:2px solid #fff;outline-offset:3px}.s{margin-top:16px;font-size:13px;color:#97a0b3}</style></head>
<body><main class="c"><div class="k">THE DISPATCH · MARKETS</div><h1>Administrators only</h1><p>This page is for The Dispatch team. If that's you, sign in on the main site with your administrator account, then come back here.</p><a class="b" href="/">Go to The Dispatch</a><div class="s">Looking for your account? Open the menu on the main site and choose Settings.</div></main></body></html>`;
'''
s = s.replace(A1, BLOCK.rstrip('\n') + '\n' + A1, 1)
s = s.replace(A2, 'return json(res, 200, await institutional13fV2());', 1)
s = s.replace(A3, 'if (!isAdminUser(user)) return text(res, 403, RT52_ADMIN_ONLY, "text/html; charset=utf-8");', 1)
c4 = s.count(A4)
if c4 == 1: s = s.replace(A4, 'return text(res, 200, rt52ConsoleHtml(RT50_CONSOLE_HTML), "text/html; charset=utf-8"); // rt50console rt52s', 1)
print('console wording:', 'applied' if c4 == 1 else 'skipped (rt50console route not found; 13F and admin page still applied)')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: die('node --check failed: ' + r.stderr[:400])
print('OK rt52s: 13F v2 + admin page' + (' + console wording' if c4 == 1 else '') + '; node --check passed' + (' (dry run)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
