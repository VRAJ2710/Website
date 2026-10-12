#!/usr/bin/env python3
"""patch_rt32s.py — real /api/financials, /api/earnings, /api/holders, /api/statements (free sources only).
  SEC EDGAR companyfacts (ticker->CIK via company_tickers.json, UA 'TheDispatch support@thedispatch.uk') for statements;
  Yahoo quoteSummary (own fc.yahoo.com cookie + crumb, cached 6h) for valuation, earnings and institutions; if Yahoo fails,
  valuation is computed from SEC + the Yahoo chart price. 12h per-symbol cache, in-flight dedupe, 8s timeouts on every fetch,
  stale cache served on error. No startup work: everything runs on the first request. One normalised payload is served on
  all four paths (financials/valuation/earnings/institutions sections, each with source + asOf, plus the old compat keys).
  The stub line is replaced by a call; the helper code is appended at end of file. SKIPs cleanly if the stub line is not
  found exactly once or rt32s is already present. Never start server.js in the Replit workspace.
Usage: python3 patch_rt32s.py [--check] path/to/server.js"""
import sys, os, re, subprocess, tempfile
CODE = r'''// rt32s: free fundamentals (SEC EDGAR companyfacts + Yahoo quoteSummary), 12h cache, inflight dedupe, 8s timeouts
const RT32 = { cache: new Map(), inflight: new Map(), cik: null, cikAt: 0, cikP: null, ck: "", crumb: "", crumbAt: 0, crumbP: null };
const RT32_UA = "TheDispatch support@thedispatch.uk";
const RT32_BUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
function rt32Get(u, headers) { return fetch(u, { headers: headers || {}, signal: AbortSignal.timeout(8000), redirect: "follow" }); }
async function rt32CikMap() {
  if (RT32.cik && Date.now() - RT32.cikAt < 7 * 864e5) return RT32.cik;
  if (!RT32.cikP) RT32.cikP = (async () => {
    const r = await rt32Get("https://www.sec.gov/files/company_tickers.json", { "User-Agent": RT32_UA, Accept: "application/json" });
    if (!r.ok) throw new Error("sec tickers " + r.status);
    const j = await r.json(), m = new Map();
    for (const v of Object.values(j)) if (v && v.ticker) m.set(String(v.ticker).toUpperCase(), { cik: String(v.cik_str).padStart(10, "0"), name: v.title });
    RT32.cik = m; RT32.cikAt = Date.now(); return m;
  })().finally(() => { RT32.cikP = null; });
  return RT32.cikP;
}
async function rt32Crumb(force) {
  if (!force && RT32.crumb && Date.now() - RT32.crumbAt < 6 * 3600e3) return RT32.crumb;
  if (!RT32.crumbP) RT32.crumbP = (async () => {
    const r = await rt32Get("https://fc.yahoo.com/", { "User-Agent": RT32_BUA });
    const sc = (typeof r.headers.getSetCookie === "function" ? r.headers.getSetCookie() : [r.headers.get("set-cookie") || ""]).map(c => String(c).split(";")[0]).filter(Boolean).join("; ");
    const c = await rt32Get("https://query2.finance.yahoo.com/v1/test/getcrumb", { "User-Agent": RT32_BUA, Cookie: sc });
    const t = (await c.text()).trim();
    if (!c.ok || !t || t.length > 40 || /[<{\s]/.test(t)) throw new Error("crumb " + c.status);
    RT32.ck = sc; RT32.crumb = t; RT32.crumbAt = Date.now(); return t;
  })().finally(() => { RT32.crumbP = null; });
  return RT32.crumbP;
}
async function rt32Yahoo(sym) {
  const mods = "summaryDetail,defaultKeyStatistics,financialData,earnings,earningsHistory,calendarEvents,institutionOwnership,majorHoldersBreakdown,price";
  for (let i = 0; i < 2; i++) {
    const crumb = await rt32Crumb(i > 0);
    const r = await rt32Get(`https://query2.finance.yahoo.com/v10/finance/quoteSummary/${encodeURIComponent(sym)}?modules=${mods}&crumb=${encodeURIComponent(crumb)}`, { "User-Agent": RT32_BUA, Cookie: RT32.ck });
    if (r.status === 401 || r.status === 403) continue;
    if (!r.ok) throw new Error("yahoo " + r.status);
    const j = await r.json();
    const res = j && j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
    if (!res) throw new Error("yahoo empty");
    return res;
  }
  throw new Error("yahoo auth");
}
async function rt32Price(sym) {
  try {
    const r = await rt32Get(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=1d&interval=1d`, { "User-Agent": RT32_BUA });
    if (!r.ok) return null;
    const m = (await r.json())?.chart?.result?.[0]?.meta;
    return m && m.regularMarketPrice > 0 ? m.regularMarketPrice : null;
  } catch { return null; }
}
const RT32_C = {
  revenue: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "SalesRevenueGoodsNet"],
  grossProfit: ["GrossProfit"], operatingIncome: ["OperatingIncomeLoss"], netIncome: ["NetIncomeLoss", "ProfitLoss"],
  eps: ["EarningsPerShareDiluted", "EarningsPerShareBasic"], cfo: ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
  capex: ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
  cash: ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
  debt: ["LongTermDebtNoncurrent", "LongTermDebt"], debtCur: ["LongTermDebtCurrent", "DebtCurrent"], equity: ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
};
function rt32Days(a, b) { return (Date.parse(b) - Date.parse(a)) / 864e5; }
function rt32Units(facts, names) {
  const g = facts && facts["us-gaap"] || {};
  let best = null;
  for (const n of names) {
    const u = g[n] && g[n].units; if (!u) continue;
    const arr = u.USD || u["USD/shares"] || Object.values(u)[0]; if (!arr || !arr.length) continue;
    const last = arr.reduce((m, x) => x.end > m ? x.end : m, "");
    if (!best || last > best.last) best = { arr, last };
  }
  return best ? best.arr : [];
}
function rt32Flow(arr) {
  const by = new Map();
  for (const x of arr) { if (!x.start || !x.end || x.val == null) continue; const k = x.start + "|" + x.end; const o = by.get(k); if (!o || x.filed > o.filed) by.set(k, x); }
  const L = [...by.values()], ann = new Map(), q = new Map();
  for (const x of L) {
    const d = rt32Days(x.start, x.end);
    if (d > 340 && d < 390) ann.set(x.end, x.val);
    if (d > 75 && d < 105) q.set(x.end, x.val);
  }
  for (const x of L) {
    const d = rt32Days(x.start, x.end); if (d < 105 || d > 390) continue;
    let prev = null;
    for (const y of L) if (y.start === x.start && y.end < x.end && (!prev || y.end > prev.end)) prev = y;
    if (prev) { const g = rt32Days(prev.end, x.end); if (g > 75 && g < 105 && !q.has(x.end)) q.set(x.end, x.val - prev.val); }
  }
  return { ann, q };
}
function rt32Inst(arr) { const m = new Map(); for (const x of arr) if (x.end && x.val != null && !x.start) { const o = m.get(x.end); if (!o || x.filed > o.filed) m.set(x.end, x); } return new Map([...m].map(([k, v]) => [k, v.val])); }
function rt32Sec(facts) {
  const F = {}, I = {};
  for (const k of ["revenue", "grossProfit", "operatingIncome", "netIncome", "eps", "cfo", "capex"]) F[k] = rt32Flow(rt32Units(facts, RT32_C[k]));
  for (const k of ["cash", "debt", "debtCur", "equity"]) I[k] = rt32Inst(rt32Units(facts, RT32_C[k]));
  const build = (key, n) => {
    const ends = new Set([...F.revenue[key].keys(), ...F.netIncome[key].keys()]);
    return [...ends].sort().reverse().slice(0, n).map(end => {
      const g = k => F[k][key].has(end) ? F[k][key].get(end) : null, ins = k => I[k].has(end) ? I[k].get(end) : null;
      const cfo = g("cfo"), cx = g("capex");
      const d = ins("debt"), dc = ins("debtCur");
      return { period: key === "ann" ? "FY" + end.slice(0, 4) : end.slice(0, 7), end, revenue: g("revenue"), grossProfit: g("grossProfit"), operatingIncome: g("operatingIncome"), netIncome: g("netIncome"), eps: g("eps"),
        fcf: cfo != null ? cfo - (cx || 0) : null, cash: ins("cash"), debt: d != null || dc != null ? (d || 0) + (dc || 0) : null, equity: ins("equity") };
    });
  };
  const sh = (facts && facts.dei && facts.dei.EntityCommonStockSharesOutstanding && facts.dei.EntityCommonStockSharesOutstanding.units.shares) || [];
  const shares = sh.length ? sh.reduce((m, x) => x.end > m.end ? x : m).val : null;
  return { annual: build("ann", 5), quarterly: build("q", 5), shares };
}
const rt32R = v => v && typeof v === "object" ? (v.raw != null ? v.raw : null) : (typeof v === "number" ? v : null);
async function rt32Build(sym) {
  const now = new Date().toISOString(), out = { symbol: sym, asOf: now, financials: null, valuation: null, earnings: null, institutions: null };
  const ySym = sym.replace(/\./g, "-");
  const [secR, yR] = await Promise.allSettled([
    (async () => {
      const m = await rt32CikMap(); const e = m.get(sym) || m.get(ySym); if (!e) return null;
      const r = await rt32Get(`https://data.sec.gov/api/xbrl/companyfacts/CIK${e.cik}.json`, { "User-Agent": RT32_UA, Accept: "application/json" });
      if (!r.ok) throw new Error("sec facts " + r.status);
      const j = await r.json(); const s = rt32Sec(j.facts); s.name = e.name; return s;
    })(),
    rt32Yahoo(ySym),
  ]);
  const sec = secR.status === "fulfilled" ? secR.value : null, y = yR.status === "fulfilled" ? yR.value : null;
  if (sec && (sec.annual.length || sec.quarterly.length)) out.financials = { source: "SEC EDGAR (XBRL company facts)", asOf: now, name: sec.name, annual: sec.annual, quarterly: sec.quarterly };
  if (y) {
    const sd = y.summaryDetail || {}, ks = y.defaultKeyStatistics || {}, fd = y.financialData || {}, pr = y.price || {};
    const v = { source: "Yahoo Finance", asOf: now, price: rt32R(fd.currentPrice) || rt32R(pr.regularMarketPrice), pe: rt32R(sd.trailingPE), forwardPe: rt32R(sd.forwardPE) || rt32R(ks.forwardPE), ps: rt32R(sd.priceToSalesTrailing12Months),
      pb: rt32R(ks.priceToBook), evEbitda: rt32R(ks.enterpriseToEbitda), marketCap: rt32R(sd.marketCap) || rt32R(pr.marketCap), divYield: rt32R(sd.dividendYield) != null ? rt32R(sd.dividendYield) : rt32R(sd.yield),
      beta: rt32R(sd.beta), profitMargin: rt32R(fd.profitMargins), revenueGrowth: rt32R(fd.revenueGrowth), targetMean: rt32R(fd.targetMeanPrice), recommendation: fd.recommendationKey || null };
    if (Object.entries(v).some(([k, x]) => !["source", "asOf"].includes(k) && x != null)) out.valuation = v;
    const hist = ((y.earningsHistory || {}).history || []).map(h => {
      const a = rt32R(h.epsActual), e = rt32R(h.epsEstimate), sp = rt32R(h.surprisePercent), qd = h.quarter && h.quarter.fmt;
      return { quarter: qd ? `${qd.slice(0, 7)}` : (h.period || ""), date: qd || null, actual: a, estimate: e, surprisePct: sp != null ? Math.round(sp * 1000) / 10 : null, beat: a != null && e != null ? a >= e : null };
    }).filter(h => h.actual != null).reverse();
    const ce = (y.calendarEvents || {}).earnings || {};
    const nd = (ce.earningsDate || [])[0];
    if (hist.length || nd) out.earnings = { source: "Yahoo Finance", asOf: now, history: hist, next: nd ? { date: nd.fmt, estimate: rt32R(ce.earningsAverage), isEstimate: !!ce.isEarningsDateEstimate } : null };
    const io = (y.institutionOwnership || {}).ownershipList || [], mh = y.majorHoldersBreakdown || {};
    const holders = io.map(h => ({ name: h.organization, pct: rt32R(h.pctHeld), shares: rt32R(h.position), value: rt32R(h.value), date: h.reportDate && h.reportDate.fmt, change: rt32R(h.pctChange) })).filter(h => h.name);
    if (holders.length || rt32R(mh.institutionsPercentHeld) != null) out.institutions = { source: "Yahoo Finance (13F filings)", asOf: now, pctHeld: rt32R(mh.institutionsPercentHeld), insidersPct: rt32R(mh.insidersPercentHeld), count: rt32R(mh.institutionsCount), holders };
  }
  if (!out.valuation && sec) {
    const px = await rt32Price(ySym);
    if (px) {
      const q = sec.quarterly, ttm = k => q.length >= 4 && q.slice(0, 4).every(x => x[k] != null) ? q.slice(0, 4).reduce((s, x) => s + x[k], 0) : (sec.annual[0] ? sec.annual[0][k] : null);
      const eps = ttm("eps"), rev = ttm("revenue"), mc = sec.shares ? px * sec.shares : null, eq = (q[0] || sec.annual[0] || {}).equity;
      out.valuation = { source: "Computed: SEC EDGAR + Yahoo price", asOf: now, price: px, pe: eps > 0 ? px / eps : null, forwardPe: null, ps: mc && rev > 0 ? mc / rev : null, pb: mc && eq > 0 ? mc / eq : null, evEbitda: null, marketCap: mc, divYield: null };
    }
  }
  if (!out.earnings && sec && sec.quarterly.some(x => x.eps != null)) out.earnings = { source: "SEC EDGAR (no estimates)", asOf: now, history: sec.quarterly.filter(x => x.eps != null).slice(0, 4).map(x => ({ quarter: x.end.slice(0, 7), date: x.end, actual: x.eps, estimate: null, surprisePct: null, beat: null })), next: null };
  const v = out.valuation || {}, H = out.earnings && out.earnings.history || [];
  // compat with the existing client loaders
  out.metrics = { peRatio: v.pe, forwardPE: v.forwardPe, psRatio: v.ps, pbRatio: v.pb, evEbitda: v.evEbitda, marketCap: v.marketCap, dividendYield: v.divYield };
  out.history = H; out.nextEarnings = out.earnings && out.earnings.next;
  const bt = H.filter(h => h.beat != null); out.beatRate = bt.length ? Math.round(bt.filter(h => h.beat).length / bt.length * 100) : null;
  const sp = H.filter(h => h.surprisePct != null); out.avgSurprise = sp.length ? Math.round(sp.reduce((s, h) => s + h.surprisePct, 0) / sp.length * 10) / 10 : null;
  out.holders = (out.institutions && out.institutions.holders) || [];
  out.sources = { sec: secR.status === "fulfilled" ? (sec ? "ok" : "no CIK") : String(secR.reason && secR.reason.message), yahoo: yR.status === "fulfilled" ? "ok" : String(yR.reason && yR.reason.message) };
  return out;
}
async function rt32Fundamentals(req, res, p, url) {
  const sym = String(url.searchParams.get("symbol") || "").trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9.\-]{0,9}$/.test(sym)) return json(res, 200, { symbol: sym, unavailable: true, reason: "bad symbol", data: [], earnings: [], holders: [], history: [] });
  const hit = RT32.cache.get(sym);
  if (hit && Date.now() - hit.at < 12 * 3600e3) return json(res, 200, hit.data, { "Cache-Control": "public, max-age=600" });
  try {
    if (!RT32.inflight.has(sym)) RT32.inflight.set(sym, rt32Build(sym).finally(() => RT32.inflight.delete(sym)));
    const data = await RT32.inflight.get(sym);
    const any = data.financials || data.valuation || data.earnings || data.institutions;
    if (any) { RT32.cache.set(sym, { at: Date.now(), data }); if (RT32.cache.size > 300) RT32.cache.delete(RT32.cache.keys().next().value); }
    else if (hit) return json(res, 200, hit.data);
    return json(res, 200, any ? data : { ...data, unavailable: true });
  } catch (e) {
    console.warn("[rt32s] fundamentals", sym, e && e.message);
    if (hit) return json(res, 200, hit.data);
    return json(res, 200, { symbol: sym, unavailable: true, reason: "source error", data: [], earnings: [], holders: [], history: [] });
  }
}
'''
CHECK = '--check' in sys.argv
args = [a for a in sys.argv[1:] if a != '--check']
P = args[0] if args else 'server.js'
b = open(P, 'rb').read(); crlf = b'\r\n' in b; s = b.decode('utf-8').replace('\r\n', '\n')
if 'rt32Fundamentals' in s: print('SKIP rt32s already applied; server.js left as is.'); sys.exit(0)
KEY = '["/api/financials", "/api/earnings", "/api/statements", "/api/holders"].includes(p)'
lines = [i for i, l in enumerate(s.split('\n')) if KEY in l and 'return json(res, 200' in l]
if len(lines) != 1:
    print(f'SKIP stub line matched {len(lines)} times; server.js left as is. Run: grep -n \'"/api/financials"\' server.js'); sys.exit(0)
L = s.split('\n'); i = lines[0]
if not re.search(r'url\.searchParams', L[i]): print('SKIP stub line does not use url.searchParams; server.js left as is.'); sys.exit(0)
ind = re.match(r'\s*', L[i]).group(0)
L[i] = ind + 'if (' + KEY + ') return rt32Fundamentals(req, res, p, url);'
s = '\n'.join(L).rstrip('\n') + '\n\n' + CODE + '\n'
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t: t.write(s); tmp = t.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True); os.unlink(tmp)
if r.returncode: print('ABORT: node --check failed, nothing written:', r.stderr[:300]); sys.exit(1)
print(f'APPLY stub line {i+1} -> rt32Fundamentals; helpers appended; node --check passed' + (' (dry run, nothing written)' if CHECK else ''))
if not CHECK:
    open(P, 'wb').write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8')); print('written', P)
