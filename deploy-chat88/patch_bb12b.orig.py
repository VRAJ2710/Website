"""bb12b = bb12 + DevOps review fixes, as ONE patch on the live server bb10j (md5 92a2ce51dfc1bf3e16466d7451d9ae1a, 23580 lines). Output is bb12 (below) plus, inside the bb11 block only:
 (a) /api/monitor rate-limit key never trusts a client-set first X-Forwarded-For entry: cf-connecting-ip (if it looks like an IP) > XFF entry before the last (2+ entries) > only XFF entry > socket address; IPv6/port forms normalised, key capped.
     Per-client limit 120/min (was 240) plus a global backstop of 2000/min for all monitor routes (same FixedWindowRateLimiter, no timers). 429 body/headers unchanged.
 (b) BB11_FACTS_MAX_BYTES = 25 MB (26214400). Still 4 companyfacts/day, concurrency 4.
 (c) Radar list and per-ticker detail: Cache-Control "public, max-age=300, stale-while-revalidate=600" (weak ETag / 304 unchanged).
 (d) Cold start: the seed counts as a market pull of its own UK day (refresh.last_market_pull = {uk_day, at, ok:true, fetched, failed:0, seed:true}); same-day cold start does not pull, later UK days pull once. Persisted-file restore unchanged.
--- bb12 description follows ---
bb12: ONE combined patch on the live server bb10j (md5 92a2ce51dfc1bf3e16466d7451d9ae1a, 23580 lines). Applies, in this order:
 1. bb11 + bb11b: Capital Sustainability Monitor data side (GET|HEAD /api/monitor, /api/monitor/{TICKER}), ONE market adapter (bb11bMarketAdapter) and the delayed-data `label`.
    Block inserted after // BB10J_JS_END (inside bb10i's maintenance wrapper, via bb10iHandle0). Content identical to /workspace/dispatch-live-bb11b.
 2. bb10h: stale crypto Ask fix (build-id keys + TTLs), doubled BTC paragraph, brief/intelligence/lenses period labels, gold spot label.
    Block inserted after // BB10G_JS_END, i.e. exactly where it sat on bb10g and BEFORE the bb10i/bb10j maintenance block. bb10h never rebinds `handle`
    (it overrides bb8eWait, bb8qFinish, generateAi, bb8oShape and the bb8qPackMem accessors), so the maintenance handler stays the outermost layer.
 3. SPA shell for the monitor pages (Frontend rt63): GET/HEAD /research/capital-sustainability, /research/capital-sustainability/method and
    /research/capital-sustainability/{TICKER} (^[A-Za-z0-9.\\-]{1,10}$, any case, optional trailing slash) answer 200 text/html with the plain index.html shell
    (default head, no per-route meta), through the same text() helper the other SPA routes use. One 4-line insertion in handle(), before the
    /research/:slug editorial route so these paths win. Everything else under /research, /brief, /report is unchanged. Maintenance behaviour is unchanged
    (the route sits inside the maintenance wrapper: guests 503 except "/", admin gets the shell).
Server-only. No new packages, tables, timers/cron/polling, env values (DISPATCH_SEC_UA from bb11 stays optional) or LLM calls. New names are bb12-prefixed (bb10h/bb11 names unchanged).
Usage: python3 patch_bb12b.py <folder containing server.js> [--check]
--check is a dry run (nothing written). A second run prints REFUSE and exits 0. A base md5 mismatch only WARNs. CRLF files stay CRLF."""
import sys, os, hashlib, subprocess
BASE_MD5 = "92a2ce51dfc1bf3e16466d7451d9ae1a"
def md5(b): return hashlib.md5(b).hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()

BB11 = r'''// ── bb11: Capital Sustainability Monitor, data side (GET /api/monitor, GET /api/monitor/{TICKER}) ─────────────────────────────────
// Port of the research prototype (monitor.py + METHODOLOGY.md) to JS, formulas/weights/thresholds/tags/flags/ordering unchanged. Pure arithmetic: no AI/LLM calls.
// Served from an in-memory cache seeded with the prototype's 2026-10-27 snapshot (embedded below) plus a best-effort JSON file in os.tmpdir(), read at the first request only.
// No timers, no DB tables, no startup work. Everything below runs only inside a request:
//  - market data: at most ONE batched pull per UK day (<= 25 instruments, Yahoo chart via the existing fetchYahooChart, each fetch under withTimeout), single-flight, stale-while-revalidate (the request that finds the cache a day old is answered from cache immediately)
//  - SEC: only if env DISPATCH_SEC_UA is set (read at call time). Per filer at most one submissions check per UK day (If-Modified-Since); company facts are re-read and the figures recomputed ONLY when a new 10-Q/10-K accession appears
//  - pull fails or nothing cached: the seeded snapshot is served with explicit stale/as-of flags. Nothing is estimated; every figure carries its source and as-of.
// The routes sit INSIDE bb10i's maintenance wrapper (they hook bb10iHandle0): guests get the 503 while maintenance is on, the admin cookie sees them. Public read-only otherwise.
// An attention and fundamentals-gap ranking, not a recommendation. Not investment advice. Capital at risk.
var BB11_VERSION = "bb11-1";
var BB11_CAP = 25;                 // hard cap on instruments per pull / per request (plan: 25)
var BB11_LIMIT_DEFAULT = 10, BB11_LIMIT_MAX = 25;
var BB11_FETCH_MS = 8000, BB11_SEC_MS = 12000, BB11_FACTS_MS = 60000, BB11_FACTS_MAX_BYTES = 25 * 1024 * 1024;
var BB11_MAX_FACTS_PER_DAY = 4;    // company-facts downloads per UK day (each is 1-15 MB)
var BB11_CONCURRENCY = 4;
var BB11_FILE = require("path").join(require("os").tmpdir(), "dispatch-monitor-v1.json");
var BB11_DISCLAIMER = "Not investment advice. Capital at risk.";
var BB11_NOTE = "Attention and fundamentals-gap ranking, not a recommendation. Thresholds and weights are analytical judgments, not facts. Not investment advice. Capital at risk.";
var BB11_MARKET_SOURCE = "Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote";
var BB11_SEC_SOURCE = "SEC EDGAR XBRL company facts (data.sec.gov)";
var BB11_TH = { winsor: 1.0, gap_pp: { amber: 10.0, red: 40.0 }, fcf_cov: { green: 0.5, amber: 0.0 }, debt_capex: { amber: 0.10, red: 0.25 }, int_opinc: { amber: 0.05, red: 0.15 }, margin_pp: { amber: -1.0, red: -4.0 } };
var BB11_FLAGS = ["sustainability_gap", "fcf_coverage", "debt_reliance", "interest_burden", "margin_trend"];
var BB11_RANK = { green: 0, amber: 1, red: 2 };
var BB11_W_FILING = 0.5, BB11_W_MARKET = 0.5;
var BB11_FORMULA = "Radar = 0.5 x Filing + 0.5 x Market (0-100). If market data is unavailable the row shows the Filing score only and is ranked after rows with both. " +
  "Filing (0-100) = 50 x flag_points/10 [red=2, amber=1, n/a=0 over the 5 flags] + 20 x min(max(Sustainability Gap,0),150)/150 " +
  "+ 15 x min(max(latest-quarter capex growth - TTM capex growth, 0),100)/100 [capex acceleration, pp] " +
  "+ min(15, 5 x number of flags that turned worse vs the previous quarter + 5 if debt issued in the latest quarter >= 10% of that quarter's capex). " +
  "Market (0-100) = 50 x clip((volume / mean volume of prior 20 sessions - 1)/2, 0, 1) + 50 x clip(|5-session price change| / 15%, 0, 1). " +
  "Attention: high if Market >= 40, low if < 15, else medium. Weights and cut-offs are editorial judgments, not facts.";
// universe = PRESETS["radar"] in prototype order (that order is the stable tie-break)
var BB11_TICKERS = ["MSFT", "GOOGL", "AMZN", "META", "ORCL", "CRWV", "NVDA", "AVGO", "AMD", "MU", "VRT", "CEG", "VST", "NEE", "EQIX", "DLR", "XOM", "T", "CRM"];
// hand-checked tag maps of the six original names (UNIVERSE in monitor.py); every other filer uses the ordered fallback lists
var BB11_EXPL = {
  MSFT: { name: "Microsoft", group: "hyperscaler", capex: ["PaymentsToAcquirePropertyPlantAndEquipment"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromDebtMaturingInMoreThanThreeMonths"], interest: ["InterestExpenseNonoperating"] },
  GOOGL: { name: "Alphabet", group: "hyperscaler", capex: ["PaymentsToAcquirePropertyPlantAndEquipment"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromDebtNetOfIssuanceCosts"], interest: ["InterestExpenseNonoperating"] },
  AMZN: { name: "Amazon", group: "hyperscaler", capex: ["PaymentsToAcquireProductiveAssets"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromIssuanceOfLongTermDebt"], interest: ["InterestExpenseNonoperating"] },
  META: { name: "Meta", group: "hyperscaler", capex: ["PaymentsToAcquirePropertyPlantAndEquipment"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromIssuanceOfLongTermDebt"], interest: ["InterestExpenseDebt"] },
  ORCL: { name: "Oracle", group: "hyperscaler", capex: ["PaymentsToAcquirePropertyPlantAndEquipment"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromIssuanceOfSeniorLongTermDebt", "ProceedsFromIssuanceOfLongTermDebt"], interest: ["InterestExpense"] },
  CRWV: { name: "CoreWeave", group: "ai-infrastructure borrower", capex: ["PaymentsToAcquirePropertyPlantAndEquipment"], ocf: ["NetCashProvidedByUsedInOperatingActivities"], rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], opinc: ["OperatingIncomeLoss"], debt: ["ProceedsFromIssuanceOfLongTermDebt"], interest: ["InterestExpenseDebt"] }
};
var BB11_FALLBACK = {
  ocf: ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
  capex: ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets", "PaymentsForCapitalImprovements", "PaymentsToDevelopRealEstateAssets", "PaymentsToAcquireOtherPropertyPlantAndEquipment", "PaymentsToAcquireRealEstate", "PaymentsToAcquireOilAndGasPropertyAndEquipment"],
  rev: ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "RevenuesNetOfInterestExpense"],
  opinc: ["OperatingIncomeLoss"],
  debt: ["ProceedsFromIssuanceOfLongTermDebt", "ProceedsFromDebtMaturingInMoreThanThreeMonths", "ProceedsFromDebtNetOfIssuanceCosts", "ProceedsFromIssuanceOfSeniorLongTermDebt", "ProceedsFromIssuanceOfDebt", "ProceedsFromIssuanceOfUnsecuredDebt", "ProceedsFromNotesPayable"],
  interest: ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt", "InterestAndDebtExpense", "InterestExpenseLongTermDebt"]
};
var BB11_GROUPS = { MSFT: "hyperscaler", GOOGL: "hyperscaler", AMZN: "hyperscaler", META: "hyperscaler", ORCL: "hyperscaler", CRWV: "ai-infrastructure borrower", NVDA: "AI supplier", AVGO: "AI supplier", AMD: "AI supplier", MU: "AI supplier", VRT: "AI supplier (power and cooling)", CEG: "power utility", VST: "power utility", NEE: "power utility", EQIX: "digital infrastructure REIT", DLR: "digital infrastructure REIT", XOM: "heavy-capex industrial", T: "telecom", CRM: "low-capex software" };
var BB11_COMMIT_TAGS = ["UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount", "PurchaseObligation", "LessorOperatingLeaseNotYetCommencedAmount", "LesseeOperatingLeaseLeaseNotYetCommencedPaymentsDue"];
var BB11_METRICS = ["capex", "ocf", "rev", "opinc", "debt", "interest"];

// ── Python-compatible number helpers (so the port matches monitor.py to the last digit) ─────────────────────────────────────────────
function bb11PySum(a) {                      // CPython 3.12+ sum(): Neumaier-compensated float sum (exact for ints below 2^53)
  var f = 0, c = 0;
  for (var i = 0; i < a.length; i++) {
    var x = a[i], t = f + x;
    if (Math.abs(f) >= Math.abs(x)) c += (f - t) + x; else c += (x - t) + f;
    f = t;
  }
  return (c && isFinite(c)) ? f + c : f;
}
function bb11PyFixed(x, d) {                 // like Python '%.<d>f' of |x|: round-half-even on the exact binary value (JS toFixed rounds an exact tie up)
  var s = Math.abs(x), r = s.toFixed(d), e = s.toFixed(Math.min(100, d + 40));
  var m = /^(\d+)(?:\.(\d*))?$/.exec(e);
  if (m) {
    var fr = m[2] || "", head = fr.slice(0, d), rest = fr.slice(d);
    if (/^50*$/.test(rest)) {                // exact tie
      var lo = m[1] + (d ? "." + head : ""), last = (m[1] + head).slice(-1);
      r = (Number(last) % 2 === 0) ? lo : r;
    }
  }
  return r;
}
function bb11PyFmt(x, d, plus) { var neg = x < 0 || Object.is(x, -0); return (neg ? "-" : (plus ? "+" : "")) + bb11PyFixed(x, d); }
function bb11PyRound1(x) { return Number((x < 0 || Object.is(x, -0) ? "-" : "") + bb11PyFixed(x, 1)); }
function bb11Clip(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }
function bb11Day(s) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s)); if (!m) throw new Error("bad date"); return Date.UTC(+m[1], +m[2] - 1, +m[3]) / 86400000; }
function bb11YrBack(dn) {
  var d = new Date(dn * 86400000), y = d.getUTCFullYear() - 1, mo = d.getUTCMonth(), da = d.getUTCDate(), t = Date.UTC(y, mo, da);
  if (new Date(t).getUTCMonth() !== mo) t = Date.UTC(y, mo, 28);
  return t / 86400000;
}
function bb11Growth(a, b) { return (a === null || a === undefined || b === null || b === undefined || b <= 0) ? null : a / b - 1.0; }
function bb11Has(v) { return v !== null && v !== undefined; }

// ── XBRL period arithmetic (monitor.py build_series / cum / period / quarter / ttm) ──────────────────────────────────────────────────
function bb11BuildSeries(facts, tags) {      // Map "start|end" -> {s,e,val,accn,form,filed,tag}; first tag in priority wins; latest filing wins per tag
  var out = new Map(), gaap = (facts.facts && facts.facts["us-gaap"]) || {};
  tags.forEach(function (tag) {
    if (!Object.prototype.hasOwnProperty.call(gaap, tag)) return;
    var best = new Map(), us = (gaap[tag].units && gaap[tag].units.USD) || [];
    us.forEach(function (x) {
      if (!("start" in x)) return;
      var k = x.start + "|" + x.end, b = best.get(k);
      if (!b || x.filed > b.filed) best.set(k, { s: x.start, e: x.end, val: x.val, accn: x.accn, form: x.form, filed: x.filed, tag: tag });
    });
    best.forEach(function (v, k) { if (!out.has(k)) out.set(k, v); });
  });
  return out;
}
function bb11Cum(series, end, maxDays, tol) {
  maxDays = maxDays || 380; tol = tol === undefined ? 6 : tol;
  var cands = [];
  series.forEach(function (v) {
    if (Math.abs(bb11Day(v.e) - end) <= tol) { var n = bb11Day(v.e) - bb11Day(v.s) + 1; if (n <= maxDays) cands.push({ n: n, v: v }); }
  });
  if (!cands.length) return null;
  var b = cands[0]; for (var i = 1; i < cands.length; i++) if (cands[i].n > b.n) b = cands[i];
  return { start: b.v.s, end: b.v.e, days: b.n, val: b.v.val, accn: b.v.accn, form: b.v.form, filed: b.v.filed, tag: b.v.tag };
}
function bb11Period(series, startNear, endNear, tol) {
  tol = tol === undefined ? 8 : tol;
  var hit = null;
  series.forEach(function (v) {
    if (hit) return;
    if (Math.abs(bb11Day(v.s) - startNear) <= tol && Math.abs(bb11Day(v.e) - endNear) <= tol) hit = { start: v.s, end: v.e, days: bb11Day(v.e) - bb11Day(v.s) + 1, val: v.val, accn: v.accn, form: v.form, filed: v.filed, tag: v.tag };
  });
  return hit;
}
function bb11Quarter(series, end) {
  var vals = Array.from(series.values()), direct = null;
  for (var i = 0; i < vals.length && !direct; i++) {
    var v = vals[i];
    if (Math.abs(bb11Day(v.e) - end) <= 6) { var n = bb11Day(v.e) - bb11Day(v.s) + 1; if (n >= 80 && n <= 100) direct = v; }
  }
  if (direct) return { val: direct.val, accns: [direct.accn] };
  var cands = [];
  vals.forEach(function (v) { var n = bb11Day(v.e) - bb11Day(v.s) + 1; if (Math.abs(bb11Day(v.e) - end) <= 6 && n >= 150 && n <= 380) cands.push({ n: n, v: v }); });
  cands.sort(function (a, b) { return a.n - b.n || (a.v.s < b.v.s ? -1 : a.v.s > b.v.s ? 1 : 0) || (a.v.e < b.v.e ? -1 : a.v.e > b.v.e ? 1 : 0); });
  for (var j = 0; j < cands.length; j++) {
    var c = cands[j].v;
    for (var k = 0; k < vals.length; k++) {
      var w = vals[k], dd = bb11Day(c.e) - bb11Day(w.e);
      if (w.s === c.s && dd >= 80 && dd <= 100) return { val: c.val - w.val, accns: [c.accn, w.accn] };
    }
  }
  return null;
}
function bb11Ttm(series, end) {
  var c = bb11Cum(series, end);
  if (!c) return null;
  if (c.days >= 350) return { val: c.val, accns: [c.accn], end: c.end, basis: "12m reported" };
  var cs = bb11Day(c.start), ce = bb11Day(c.end);
  var fy = bb11Period(series, cs - 365, cs - 1, 10), prior = bb11Period(series, bb11YrBack(cs), bb11YrBack(ce), 10);
  if (!fy || !prior || fy.days < 350) return null;
  return { val: fy.val + c.val - prior.val, accns: [fy.accn, c.accn, prior.accn], end: c.end, basis: "FY + YTD - prior YTD" };
}
function bb11ComputeCompany(tkr, cfg, facts) {   // -> rows (newest first, up to 8)
  var S = {}; BB11_METRICS.forEach(function (m) { S[m] = bb11BuildSeries(facts, cfg[m]); });
  if (!S.ocf.size) { var err = new Error("operating cash flow is not disclosed under the tags tried"); err.notComputable = true; throw err; }
  var ends = Array.from(new Set(Array.from(S.ocf.values()).map(function (v) { return v.e; }))).sort().reverse();
  var floor = bb11Day(ends[0]) - 740;
  ends = ends.filter(function (e) { return bb11Day(e) >= floor; });
  var qends = [];
  ends.forEach(function (e) { if (!qends.length || Math.abs(bb11Day(qends[qends.length - 1]) - bb11Day(e)) > 20) qends.push(e); });
  qends = qends.slice(0, 8);
  var rows = [];
  qends.forEach(function (e) {
    var end = bb11Day(e), r = { ticker: tkr, company: cfg.name, period_end: e };
    BB11_METRICS.forEach(function (m) {
      var q = bb11Quarter(S[m], end), t = bb11Ttm(S[m], end), tp = bb11Ttm(S[m], bb11YrBack(end)), qp = bb11Quarter(S[m], bb11YrBack(end));
      r[m + "_q"] = q ? q.val : null; r[m + "_ttm"] = t ? t.val : null; r[m + "_ttm_prior"] = tp ? tp.val : null; r[m + "_q_prior"] = qp ? qp.val : null;
      r[m + "_src_accn"] = t ? t.accns : (q ? q.accns : null);
    });
    r.fcf_q = (bb11Has(r.capex_q) && bb11Has(r.ocf_q)) ? r.ocf_q - r.capex_q : null;
    ["ttm", "ttm_prior"].forEach(function (k) { r["fcf_" + k] = (bb11Has(r["ocf_" + k]) && bb11Has(r["capex_" + k])) ? r["ocf_" + k] - r["capex_" + k] : null; });
    r.fcf_q_prior = (bb11Has(r.ocf_q_prior) && bb11Has(r.capex_q_prior)) ? r.ocf_q_prior - r.capex_q_prior : null;
    ["capex", "ocf", "rev", "opinc", "interest"].forEach(function (m) { r[m + "_g_ttm"] = bb11Growth(r[m + "_ttm"], r[m + "_ttm_prior"]); r[m + "_g_q"] = bb11Growth(r[m + "_q"], r[m + "_q_prior"]); });
    r.opmargin_ttm = (bb11Has(r.opinc_ttm) && r.rev_ttm) ? r.opinc_ttm / r.rev_ttm : null;
    r.opmargin_ttm_prior = (bb11Has(r.opinc_ttm_prior) && r.rev_ttm_prior) ? r.opinc_ttm_prior / r.rev_ttm_prior : null;
    r.opmargin_q = (bb11Has(r.opinc_q) && r.rev_q) ? r.opinc_q / r.rev_q : null;
    rows.push(r);
  });
  ["capex", "ocf", "rev", "opinc"].forEach(function (m) {
    var qs = qends.slice(0, 4).map(function (e) { return bb11Quarter(S[m], bb11Day(e)); }), t = rows[0][m + "_ttm"];
    if (bb11Has(t) && qs.every(function (q) { return q; })) rows[0][m + "_recon_diff"] = bb11PySum(qs.map(function (q) { return q.val; })) - t;
  });
  return rows;
}
function bb11GenericCfg(cik, name, facts) {
  var gaap = (facts.facts && facts.facts["us-gaap"]) || {};
  function durations(tag) { var us = (gaap[tag] && gaap[tag].units && gaap[tag].units.USD) || []; return us.filter(function (x) { return "start" in x; }).map(function (x) { return [x.start, x.end]; }); }
  function maxEnd(ds) { return ds.reduce(function (a, d) { return d[1] > a ? d[1] : a; }, ""); }
  var have = [];
  BB11_FALLBACK.ocf.forEach(function (t, i) { var ds = durations(t); if (ds.length) have.push({ e: maxEnd(ds), i: -i, t: t }); });
  if (!have.length) { var err = new Error("no operating-cash-flow fact under us-gaap"); err.notComputable = true; throw err; }
  have.sort(function (a, b) { return a.e < b.e ? 1 : a.e > b.e ? -1 : (b.i - a.i) || (a.t < b.t ? 1 : a.t > b.t ? -1 : 0); });
  var latest = have[0].e, cfg = { name: name, cik: cik, group: "", missing: [], ocf: have.map(function (h) { return h.t; }) };
  var cutoff = new Date((bb11Day(latest) - 20) * 86400000).toISOString().slice(0, 10);
  Object.keys(BB11_FALLBACK).forEach(function (m) {
    if (m === "ocf") return;
    var pick = null;
    for (var i = 0; i < BB11_FALLBACK[m].length && !pick; i++) { var t = BB11_FALLBACK[m][i], ds = durations(t); if (ds.length && maxEnd(ds) >= cutoff) pick = t; }
    cfg[m] = pick ? [pick] : []; if (!pick) cfg.missing.push(m);
  });
  return cfg;
}
function bb11Classify(facts) {                // [supported, reason]
  var ns = (facts && facts.facts) || {}, tax = Object.keys(ns), forms = new Set();
  tax.forEach(function (k) { Object.keys(ns[k]).slice(0, 60).forEach(function (tg) { var us = ns[k][tg].units || {}; Object.keys(us).forEach(function (u) { us[u].slice(0, 50).forEach(function (x) { forms.add(x.form); }); }); }); });
  var fpi = ["20-F", "40-F", "6-K"].filter(function (f) { return forms.has(f); });
  if (tax.indexOf("us-gaap") < 0) {
    var why = "its XBRL uses " + (tax.slice().sort().join(", ") || "no taxonomy") + " rather than us-gaap";
    if (fpi.length) why += "; it files " + fpi.join("/") + " (foreign private issuer), not 10-Q/10-K, and typically reports in a non-USD currency and half-yearly";
    return [false, "Not supported yet: " + why + ". The checks need quarterly us-gaap duration facts in USD."];
  }
  if (forms.size && !(forms.has("10-K") || forms.has("10-Q")) && (forms.has("20-F") || forms.has("40-F"))) return [false, "Not supported yet: foreign private issuer (20-F/40-F) with no 10-Q/10-K quarterly data; the TTM and growth checks need quarterly USD facts."];
  return [true, ""];
}

// ── scoring (monitor.py evaluate / filing_score / market_score / reasons / tag_for / add_radar) ──────────────────────────────────────
function bb11Evaluate(r) {
  var m = {}, W = BB11_TH.winsor, cg = r.capex_g_ttm, og = r.ocf_g_ttm, rg = r.rev_g_ttm, ig = r.opinc_g_ttm;
  var parts = { ocf: og, rev: rg, opinc: ig }, used = [], avail = [];
  Object.keys(parts).forEach(function (k) { var v = parts[k]; if (bb11Has(v)) { v = Math.max(-W, Math.min(W, v)); avail.push(v); used.push(k); } });
  m.capex_growth_ttm = cg; m.ocf_growth_ttm = og; m.rev_growth_ttm = rg; m.opinc_growth_ttm = ig;
  m.gap_vs_ocf_pp = (!bb11Has(cg) || !bb11Has(og)) ? null : (cg - og) * 100;
  m.gap_vs_rev_pp = (!bb11Has(cg) || !bb11Has(rg)) ? null : (cg - rg) * 100;
  m.gap_vs_opinc_pp = (!bb11Has(cg) || !bb11Has(ig)) ? null : (cg - ig) * 100;
  m.sustainability_gap_pp = (!bb11Has(cg) || !avail.length) ? null : (cg - bb11PySum(avail) / avail.length) * 100;
  m.gap_components_used = used;
  var cap = r.capex_ttm, ocf = r.ocf_ttm, fcf = r.fcf_ttm;
  m.fcf_ttm = fcf;
  m.fcf_coverage_of_capex = (!bb11Has(fcf) || !cap) ? null : fcf / cap;
  m.capex_pct_ocf = (!ocf || ocf <= 0 || !bb11Has(cap)) ? null : cap / ocf * 100;
  m.debt_issuance_ttm = r.debt_ttm;
  m.debt_issuance_pct_capex = (!bb11Has(r.debt_ttm) || !cap) ? null : r.debt_ttm / cap * 100;
  m.interest_ttm = r.interest_ttm; m.interest_growth_ttm = r.interest_g_ttm;
  m.interest_pct_opinc = (!bb11Has(r.interest_ttm) || !bb11Has(r.opinc_ttm) || r.opinc_ttm <= 0) ? null : r.interest_ttm / r.opinc_ttm * 100;
  m.operating_loss_ttm = bb11Has(r.opinc_ttm) && r.opinc_ttm <= 0;
  m.opmargin_ttm_pct = !bb11Has(r.opmargin_ttm) ? null : r.opmargin_ttm * 100;
  m.opmargin_change_pp = (!bb11Has(r.opmargin_ttm) || !bb11Has(r.opmargin_ttm_prior)) ? null : (r.opmargin_ttm - r.opmargin_ttm_prior) * 100;
  var F = {}, g = m.sustainability_gap_pp, T = BB11_TH;
  F.sustainability_gap = g === null ? "n/a" : (g <= T.gap_pp.amber ? "green" : g <= T.gap_pp.red ? "amber" : "red");
  var c = m.fcf_coverage_of_capex;
  F.fcf_coverage = c === null ? "n/a" : (c >= T.fcf_cov.green ? "green" : c >= T.fcf_cov.amber ? "amber" : "red");
  var d = m.debt_issuance_pct_capex;
  F.debt_reliance = d === null ? "n/a" : (d / 100 < T.debt_capex.amber ? "green" : d / 100 <= T.debt_capex.red ? "amber" : "red");
  var i = m.interest_pct_opinc;
  F.interest_burden = (m.operating_loss_ttm && r.interest_ttm) ? "red" : i === null ? "n/a" : (i / 100 < T.int_opinc.amber ? "green" : i / 100 <= T.int_opinc.red ? "amber" : "red");
  var mp = m.opmargin_change_pp;
  F.margin_trend = mp === null ? "n/a" : (mp >= T.margin_pp.amber ? "green" : mp >= T.margin_pp.red ? "amber" : "red");
  var vals = BB11_FLAGS.map(function (k) { return F[k]; });
  var reds = vals.filter(function (v) { return v === "red"; }).length, ambers = vals.filter(function (v) { return v === "amber"; }).length, scored = vals.filter(function (v) { return v !== "n/a"; }).length;
  F.overall = scored < 3 ? "insufficient data" : reds >= 3 ? "red" : (reds >= 1 || ambers >= 2) ? "amber" : "green";
  var gaps = [m.gap_vs_ocf_pp, m.gap_vs_rev_pp, m.gap_vs_opinc_pp].filter(bb11Has);
  m.capex_outpacing_all_returns = gaps.length > 0 && gaps.every(function (x) { return x > 0; });
  return { m: m, F: F };
}
function bb11FilingScore(r, F, Fprev, gapPp) {
  var pts = { red: 2, amber: 1 }, flagPts = 0;
  BB11_FLAGS.forEach(function (k) { flagPts += pts[F[k]] || 0; });
  var gap = gapPp || 0;
  var s1 = 50 * flagPts / 10, s2 = 20 * Math.min(Math.max(gap, 0), 150) / 150;
  var accel = (bb11Has(r.capex_g_q) && bb11Has(r.capex_g_ttm)) ? (r.capex_g_q - r.capex_g_ttm) * 100 : 0;
  var s3 = 15 * Math.min(Math.max(accel, 0), 100) / 100;
  var worse = BB11_FLAGS.filter(function (k) { return Fprev && F[k] in BB11_RANK && Fprev[k] in BB11_RANK && BB11_RANK[F[k]] > BB11_RANK[Fprev[k]]; });
  var better = BB11_FLAGS.filter(function (k) { return Fprev && F[k] in BB11_RANK && Fprev[k] in BB11_RANK && BB11_RANK[F[k]] < BB11_RANK[Fprev[k]]; });
  var debtNew = bb11Has(r.debt_q) && !!r.capex_q && r.debt_q >= 0.10 * r.capex_q;
  var s4 = Math.min(15, 5 * worse.length + (debtNew ? 5 : 0));
  return { score: s1 + s2 + s3 + s4, parts: { flags: s1, gap: s2, capex_accel: s3, change: s4 }, flag_points: flagPts, capex_accel_pp: accel, worse: worse, better: better, debt_issued_latest_q: !!debtNew };
}
function bb11MarketScore(md) {
  if (!md || "error" in md) return null;
  var v = 50 * Math.min(Math.max((md.volume_ratio - 1) / 2, 0), 1), p = 50 * Math.min(Math.abs(md.ret_5d_pct) / 15, 1), m = v + p;
  return { score: m, volume_pts: v, price_pts: p, attention: m >= 40 ? "high" : m < 15 ? "low" : "medium" };
}
function bb11Reasons(res, fs, ms, md) {
  var m = res.metrics, F = res.flags, c = [], pf = function (x) { return bb11PyFmt(x, 0, true) + "%"; };
  if ((F.sustainability_gap === "red" || F.sustainability_gap === "amber") && bb11Has(m.capex_growth_ttm))
    c.push([F.sustainability_gap === "red" ? 30 : 15, "capex " + pf(m.capex_growth_ttm * 100) + " vs OCF " + (m.ocf_growth_ttm === null ? "n/a" : pf(m.ocf_growth_ttm * 100)) + " (TTM)"]);
  if (F.fcf_coverage === "red") c.push([28, "capex exceeds operating cash flow (FCF negative)"]);
  if (F.debt_reliance === "red" || F.debt_reliance === "amber") c.push([F.debt_reliance === "red" ? 26 : 12, "debt issued = " + bb11PyFmt(m.debt_issuance_pct_capex, 0, false) + "% of capex"]);
  if (F.interest_burden === "red" || F.interest_burden === "amber")
    c.push([F.interest_burden === "red" ? 24 : 10, m.operating_loss_ttm ? "interest expense on an operating loss" : "interest = " + bb11PyFmt(m.interest_pct_opinc, 0, false) + "% of operating income"]);
  if (F.margin_trend === "red" || F.margin_trend === "amber") c.push([F.margin_trend === "red" ? 22 : 9, "operating margin " + bb11PyFmt(m.opmargin_change_pp, 1, true) + " pp y/y"]);
  if (fs.worse.length) c.push([27, "turned worse since last quarter: " + fs.worse.join(", ")]);
  if (ms) {
    if (md.volume_ratio >= 1.5) c.push([ms.volume_pts, "volume " + bb11PyFmt(md.volume_ratio, 1, false) + "x its 20-day average"]);
    if (Math.abs(md.ret_5d_pct) >= 3) c.push([ms.price_pts, "price " + bb11PyFmt(md.ret_5d_pct, 1, true) + "% over 5 sessions"]);
  }
  c.sort(function (a, b) { return -a[0] - -b[0]; });   // stable, descending by weight
  var out = c.slice(0, 2).map(function (x) { return x[1]; });
  return out.length ? out : ["no flag or market trigger above the display thresholds"];
}
function bb11TagFor(att, overall) {
  var fl = { "red": "flagged red", "amber": "flagged amber", "green": "green", "insufficient data": "not scoreable (too few disclosed inputs)" }[overall];
  return "attention " + att + ", fundamentals " + fl;
}
function bb11AddRadar(res, md) {              // mutates res like add_radar()
  var ms = bb11MarketScore(md), fs = res.filing_score;
  res.market = (md && !("error" in md)) ? md : { status: "market data unavailable", detail: (md && md.error) || "not fetched" };
  res.market_score = ms;
  res.radar_score = ms ? bb11PyRound1(BB11_W_FILING * fs.score + BB11_W_MARKET * ms.score) : null;
  res.filing_only_score = bb11PyRound1(fs.score);
  if (res.flags.overall === "insufficient data") res.radar_score = null;
  res.scoreable = res.flags.overall !== "insufficient data";
  res.attention = ms ? ms.attention : "unavailable";
  res.hype_vs_fundamentals_tag = ms ? bb11TagFor(ms.attention, res.flags.overall) : "market data unavailable; filings " + res.flags.overall;
  res.reasons = bb11Reasons(res, fs, ms, md);
  return res;
}
// Ranking per METHODOLOGY.md: rows with a Radar score first (descending); then rows with a Filing score only (market unavailable), descending; rows with
// insufficient filing data last, unscored. Ties keep the prototype's universe order (stable sort). NOTE: monitor.py sorts the last two groups together on
// filing_only_score, so an "insufficient data" row can sit above a filing-only row there; the written methodology is followed here (see report).
function bb11Rank(results) {
  var tier = function (r) { return r.radar_score !== null ? 0 : (r.scoreable === false ? 2 : 1); };
  var key = function (r) { return -(r.radar_score !== null ? r.radar_score : r.filing_only_score); };
  var out = results.map(function (r, i) { return { r: r, i: i }; });
  out.sort(function (a, b) { return (tier(a.r) - tier(b.r)) || (key(a.r) - key(b.r)) || (a.i - b.i); });
  return out.map(function (x, i) { x.r.rank = i + 1; return x.r; });
}
// analyse() after the rows exist. base = {ticker, company, group, cik, tags, rows:[latest, previous?], filed, commits}; today = "YYYY-MM-DD" (UTC)
function bb11Assemble(base, curated, today) {
  var rows = base.rows, latest = rows[0], ev = bb11Evaluate(latest), m = ev.m, F = ev.F;
  var Fprev = (rows.length > 1 && bb11Has(rows[1].ocf_ttm)) ? bb11Evaluate(rows[1]).F : null;
  var fs = bb11FilingScore(latest, F, Fprev, m.sustainability_gap_pp);
  var age = bb11Day(today) - bb11Day(latest.period_end), cik = base.cik, tags = base.tags;
  var accns = Array.from(new Set([].concat.apply([], Object.keys(latest).filter(function (k) { return /_src_accn$/.test(k) && latest[k]; }).map(function (k) { return latest[k]; })))).sort();
  var srcFilings = {}; accns.forEach(function (a) { srcFilings[a] = "https://www.sec.gov/Archives/edgar/data/" + cik + "/" + a.replace(/-/g, "") + "/"; });
  var cik10 = ("0000000000" + cik).slice(-10);
  var nd = BB11_METRICS.filter(function (k) { return !tags[k] || !tags[k].length; }).concat(Object.keys(F).filter(function (k) { return F[k] === "n/a"; }));
  var d = {
    status: age > 200 ? "stale" : "ok", ticker: base.ticker, company: base.company, group: base.group, cik: cik,
    latest_period_end: latest.period_end, latest_filed: base.filed, filing_age_days: age, tags: tags, not_disclosed_or_na: nd, metrics: m, flags: F,
    previous_quarter_flags: Fprev,
    changes_since_last_quarter: { flags_worse: fs.worse, flags_better: fs.better, previous_period_end: rows.length > 1 ? rows[1].period_end : null, capex_growth_ttm_now: latest.capex_g_ttm, capex_growth_ttm_prev: rows.length > 1 ? rows[1].capex_g_ttm : null, overall_prev: Fprev ? Fprev.overall : null, overall_now: F.overall },
    filing_score: fs, xbrl_commitments: base.commits || {},
    ttm: { capex: latest.capex_ttm, ocf: latest.ocf_ttm, fcf: latest.fcf_ttm, revenue: latest.rev_ttm, operating_income: latest.opinc_ttm, debt_issuance: latest.debt_ttm, interest_expense: latest.interest_ttm },
    ttm_prior: { capex: latest.capex_ttm_prior, ocf: latest.ocf_ttm_prior, revenue: latest.rev_ttm_prior, operating_income: latest.opinc_ttm_prior, interest_expense: latest.interest_ttm_prior },
    latest_quarter: { capex: latest.capex_q, ocf: latest.ocf_q, fcf: latest.fcf_q, revenue: latest.rev_q, operating_income: latest.opinc_q, debt_issuance: latest.debt_q, interest_expense: latest.interest_q },
    source_filings: srcFilings, source_api: "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik10 + ".json",
    disclosures: (curated && Object.prototype.hasOwnProperty.call(curated, base.ticker)) ? curated[base.ticker] : "not disclosed / not reviewed (text review runs only on request)"
  };
  if (age > 200) d.message = "Stale: the latest period in the SEC XBRL API ended " + latest.period_end + " (" + age + " days ago). A newer 10-Q/10-K may exist that the API has not yet absorbed; check the filing index.";
  return d;
}
// facts -> base (analyse() up to the point where rows exist). Returns {ok:true, base, accn, form} or {ok:false, status, message}
function bb11FromFacts(item, facts) {
  var cl = bb11Classify(facts);
  if (!cl[0]) return { ok: false, status: "unsupported", message: cl[1] };
  var cfg;
  try { cfg = BB11_EXPL[item.ticker] ? JSON.parse(JSON.stringify(BB11_EXPL[item.ticker])) : bb11GenericCfg(item.cik, item.company, facts); } catch (e) { if (e.notComputable) return { ok: false, status: "not_computable", message: "Not disclosed or n/a: " + e.message }; throw e; }
  cfg.group = BB11_GROUPS[item.ticker] || cfg.group || "user-selected";
  var rows;
  try { rows = bb11ComputeCompany(item.ticker, cfg, facts); } catch (e) { if (e.notComputable) return { ok: false, status: "not_computable", message: "Not disclosed or n/a: " + e.message }; throw e; }
  var latest = rows[0], gaap = facts.facts["us-gaap"], filed = null, best = null;
  cfg.ocf.forEach(function (t) { ((gaap[t] && gaap[t].units && gaap[t].units.USD) || []).forEach(function (y) {
    if (y.end === latest.period_end) { if (filed === null || y.filed > filed) filed = y.filed; if (["10-Q", "10-K"].indexOf(y.form) >= 0 && (!best || y.filed > best.filed)) best = y; }
  }); });
  var commits = {};
  BB11_COMMIT_TAGS.forEach(function (t) {
    var us = ((gaap[t] && gaap[t].units && gaap[t].units.USD) || []).slice().sort(function (a, b) { return a.end < b.end ? -1 : a.end > b.end ? 1 : 0; }), x = us[us.length - 1];
    if (x) commits[t] = { value: x.val, as_of: x.end, accn: x.accn, form: x.form };
  });
  var tags = {}; ["capex", "ocf", "rev", "opinc", "debt", "interest"].forEach(function (k) { tags[k] = cfg[k]; });
  return { ok: true, base: { ticker: item.ticker, company: cfg.name, group: cfg.group, cik: item.cik, tags: tags, rows: rows.slice(0, 2), filed: filed, commits: commits, accn: best ? best.accn : null, form: best ? best.form : null, accn_filed: best ? best.filed : null }, rows: rows };
}
// bb11b: MARKET ADAPTER (part 1/2): the source's response shape. Swap the market source here and in bb11bMarketAdapter.
// Yahoo chart JSON -> market entry (monitor.py parse_yahoo). nowSec = unix seconds. Throws on fewer than 22 usable bars.
function bb11ParseYahoo(js, nowSec) {
  var res = js.chart.result[0], meta = res.meta, q = res.indicators.quote[0], bars = [];
  for (var i = 0; i < res.timestamp.length; i++) { var c = q.close[i], v = q.volume[i]; if (c !== null && c !== undefined && v !== null && v !== undefined) bars.push([res.timestamp[i], c, v]); }
  var reg = (meta.currentTradingPeriod && meta.currentTradingPeriod.regular) || {}, hasReg = Object.keys(reg).length > 0;
  if (bars.length && hasReg && (reg.start || 0) <= bars[bars.length - 1][0] && bars[bars.length - 1][0] <= (reg.end || 0) && nowSec < reg.end) bars = bars.slice(0, -1);
  if (bars.length < 22) throw new Error("fewer than 22 daily bars");
  var c2 = bars.map(function (b) { return b[1]; }), v2 = bars.map(function (b) { return b[2]; }), n = c2.length, off = meta.gmtoffset || 0;
  var avg = bb11PySum(v2.slice(n - 21, n - 1)) / 20;
  return { last_bar_date: new Date((bars[n - 1][0] + off) * 1000).toISOString().slice(0, 10), last_close: c2[n - 1], currency: meta.currency === undefined ? null : meta.currency,
    ret_1d_pct: (c2[n - 1] / c2[n - 2] - 1) * 100, ret_5d_pct: (c2[n - 1] / c2[n - 6] - 1) * 100, volume_last: v2[n - 1], volume_avg_20d: avg, volume_ratio: v2[n - 1] / avg,
    spark: c2.slice(-20).map(function (x) { return Number(bb11PyFixed(x, 2)) * (x < 0 ? -1 : 1); }) };
}
// bb11b: END MARKET ADAPTER (part 1/2)
var BB11_SEED = {"v":1,"generated_utc":"2026-10-27 09:54 UTC","sec_retrieved":"2026-10-27","market_source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","source_note":"Seed snapshot of the prototype Radar (radar.json / results.json of 2026-10-27). SEC data: XBRL company facts, retrieved 2026-10-27. Market data: Yahoo Finance chart API, end-of-day bars, fetched 2026-10-27 09:52 UTC.","companies":{"MSFT":{"ticker":"MSFT","company":"Microsoft","group":"hyperscaler","cik":789019,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromDebtMaturingInMoreThanThreeMonths"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"MSFT","company":"Microsoft","period_end":"2026-06-30","capex_q":35802000000,"capex_ttm":115948000000,"capex_ttm_prior":64551000000,"capex_q_prior":17079000000,"capex_src_accn":["0001193125-26-323660"],"ocf_q":55441000000,"ocf_ttm":182935000000,"ocf_ttm_prior":136162000000,"ocf_q_prior":42647000000,"ocf_src_accn":["0001193125-26-323660"],"rev_q":90007000000,"rev_ttm":331839000000,"rev_ttm_prior":281724000000,"rev_q_prior":76441000000,"rev_src_accn":["0001193125-26-323660"],"opinc_q":40603000000,"opinc_ttm":155237000000,"opinc_ttm_prior":128528000000,"opinc_q_prior":34323000000,"opinc_src_accn":["0001193125-26-323660"],"debt_q":null,"debt_ttm":0,"debt_ttm_prior":0,"debt_q_prior":0,"debt_src_accn":["0001193125-26-323660"],"interest_q":839000000,"interest_ttm":3051000000,"interest_ttm_prior":2385000000,"interest_q_prior":615000000,"interest_src_accn":["0001193125-26-323660"],"fcf_q":19639000000,"fcf_ttm":66987000000,"fcf_ttm_prior":71611000000,"fcf_q_prior":25568000000,"capex_g_ttm":0.7962231413920775,"capex_g_q":1.096258563147725,"ocf_g_ttm":0.34350993669305674,"ocf_g_q":0.29999765516917964,"rev_g_ttm":0.17788686799846665,"rev_g_q":0.17747020577962092,"opinc_g_ttm":0.20780685920577624,"opinc_g_q":0.182967689304548,"interest_g_ttm":0.27924528301886786,"interest_g_q":0.3642276422764228,"opmargin_ttm":0.4678081840892722,"opmargin_ttm_prior":0.4562195624085985,"opmargin_q":0.4511093581610319,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"MSFT","company":"Microsoft","period_end":"2026-03-31","capex_q":30876000000,"capex_ttm":97225000000,"capex_ttm_prior":61345000000,"capex_q_prior":16745000000,"capex_src_accn":["0001193125-26-323660","0001193125-26-191507","0001193125-26-191507"],"ocf_q":46679000000,"ocf_ttm":170141000000,"ocf_ttm_prior":130710000000,"ocf_q_prior":37044000000,"ocf_src_accn":["0001193125-26-323660","0001193125-26-191507","0001193125-26-191507"],"rev_q":82886000000,"rev_ttm":318273000000,"rev_ttm_prior":270010000000,"rev_q_prior":70066000000,"rev_src_accn":["0001193125-26-323660","0001193125-26-191507","0001193125-26-191507"],"opinc_q":38398000000,"opinc_ttm":148957000000,"opinc_ttm_prior":122130000000,"opinc_q_prior":32000000000,"opinc_src_accn":["0001193125-26-323660","0001193125-26-191507","0001193125-26-191507"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":197000000,"debt_q_prior":0,"debt_src_accn":null,"interest_q":778000000,"interest_ttm":2827000000,"interest_ttm_prior":2471000000,"interest_q_prior":594000000,"interest_src_accn":["0001193125-26-323660","0001193125-26-191507","0001193125-26-191507"],"fcf_q":15803000000,"fcf_ttm":72916000000,"fcf_ttm_prior":69365000000,"fcf_q_prior":20299000000,"capex_g_ttm":0.5848887439889152,"capex_g_q":0.8438936996118245,"ocf_g_ttm":0.3016678142452758,"ocf_g_q":0.2600961019328367,"rev_g_ttm":0.17874523165808665,"rev_g_q":0.18297034224873698,"opinc_g_ttm":0.21965937934987312,"opinc_g_q":0.1999375000000001,"interest_g_ttm":0.14407122622420077,"interest_g_q":0.3097643097643097,"opmargin_ttm":0.4680164512855316,"opmargin_ttm_prior":0.4523165808673753,"opmargin_q":0.46326279468185216}],"filed":"2026-07-29","commits":{},"accn":"0001193125-26-323660","form":"10-K","accn_filed":"2026-07-29"},"GOOGL":{"ticker":"GOOGL","company":"Alphabet","group":"hyperscaler","cik":1652044,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromDebtNetOfIssuanceCosts"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"GOOGL","company":"Alphabet","period_end":"2026-06-30","capex_q":44924000000,"capex_ttm":132402000000,"capex_ttm_prior":66980000000,"capex_q_prior":22446000000,"capex_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"ocf_q":39069000000,"ocf_ttm":185675000000,"ocf_ttm_prior":133708000000,"ocf_q_prior":27747000000,"ocf_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"rev_q":119796000000,"rev_ttm":445866000000,"rev_ttm_prior":371399000000,"rev_q_prior":96428000000,"rev_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"opinc_q":40770000000,"opinc_ttm":147628000000,"opinc_ttm_prior":121370000000,"opinc_q_prior":31271000000,"opinc_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"debt_q":24847000000,"debt_ttm":89412000000,"debt_ttm_prior":40092000000,"debt_q_prior":26846000000,"debt_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"interest_q":1278000000,"interest_ttm":2252000000,"interest_ttm_prior":402000000,"interest_q_prior":261000000,"interest_src_accn":["0001652044-26-000018","0001652044-26-000071","0001652044-26-000071"],"fcf_q":-5855000000,"fcf_ttm":53273000000,"fcf_ttm_prior":66728000000,"fcf_q_prior":5301000000,"capex_g_ttm":0.9767393251716932,"capex_g_q":1.0014256437672637,"ocf_g_ttm":0.3886603643761031,"ocf_g_q":0.40804411287706777,"rev_g_ttm":0.20050404012934875,"rev_g_q":0.2423362508814868,"opinc_g_ttm":0.21634670841229298,"opinc_g_q":0.30376387067890387,"interest_g_ttm":4.601990049751244,"interest_g_q":3.8965517241379306,"opmargin_ttm":0.331103963971238,"opmargin_ttm_prior":0.32679140223856284,"opmargin_q":0.3403285585495342,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":1000000,"opinc_recon_diff":0},{"ticker":"GOOGL","company":"Alphabet","period_end":"2026-03-31","capex_q":35674000000,"capex_ttm":109924000000,"capex_ttm_prior":57720000000,"capex_q_prior":17197000000,"capex_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"ocf_q":45790000000,"ocf_ttm":174353000000,"ocf_ttm_prior":132601000000,"ocf_q_prior":36150000000,"ocf_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"rev_q":109896000000,"rev_ttm":422498000000,"rev_ttm_prior":359713000000,"rev_q_prior":90234000000,"rev_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"opinc_q":39696000000,"opinc_ttm":138129000000,"opinc_ttm_prior":117524000000,"opinc_q_prior":30606000000,"opinc_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"debt_q":31379000000,"debt_ttm":91411000000,"debt_ttm_prior":16139000000,"debt_q_prior":4532000000,"debt_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"interest_q":533000000,"interest_ttm":1235000000,"interest_ttm_prior":208000000,"interest_q_prior":34000000,"interest_src_accn":["0001652044-26-000018","0001652044-26-000048","0001652044-26-000048"],"fcf_q":10116000000,"fcf_ttm":64429000000,"fcf_ttm_prior":74881000000,"fcf_q_prior":18953000000,"capex_g_ttm":0.9044352044352044,"capex_g_q":1.0744315869046925,"ocf_g_ttm":0.3148694202909481,"ocf_g_q":0.2666666666666666,"rev_g_ttm":0.17454192648027744,"rev_g_q":0.21790012633818745,"opinc_g_ttm":0.17532589088186246,"opinc_g_q":0.2970005881199764,"interest_g_ttm":4.9375,"interest_g_q":14.676470588235293,"opmargin_ttm":0.3269340919957018,"opmargin_ttm_prior":0.32671602082771545,"opmargin_q":0.36121423891679405}],"filed":"2026-07-23","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":75600000000,"as_of":"2026-03-31","accn":"0001652044-26-000048","form":"10-Q"},"PurchaseObligation":{"value":7700000000,"as_of":"2025-12-31","accn":"0001652044-26-000018","form":"10-K"}},"accn":"0001652044-26-000071","form":"10-Q","accn_filed":"2026-07-23"},"AMZN":{"ticker":"AMZN","company":"Amazon","group":"hyperscaler","cik":1018724,"tags":{"capex":["PaymentsToAcquireProductiveAssets"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"AMZN","company":"Amazon","period_end":"2026-06-30","capex_q":54208000000,"capex_ttm":173028000000,"capex_ttm_prior":107656000000,"capex_q_prior":32183000000,"capex_src_accn":["0001018724-26-000026"],"ocf_q":45387000000,"ocf_ttm":161403000000,"ocf_ttm_prior":121137000000,"ocf_q_prior":32515000000,"ocf_src_accn":["0001018724-26-000026"],"rev_q":200606000000,"rev_ttm":775680000000,"rev_ttm_prior":670038000000,"rev_q_prior":167702000000,"rev_src_accn":["0001018724-26-000004","0001018724-26-000026","0001018724-26-000026"],"opinc_q":27461000000,"opinc_ttm":93712000000,"opinc_ttm_prior":76190000000,"opinc_q_prior":19171000000,"opinc_src_accn":["0001018724-26-000004","0001018724-26-000026","0001018724-26-000026"],"debt_q":13557000000,"debt_ttm":81925000000,"debt_ttm_prior":746000000,"debt_q_prior":0,"debt_src_accn":["0001018724-26-000026"],"interest_q":1314000000,"interest_ttm":3331000000,"interest_ttm_prior":2230000000,"interest_q_prior":516000000,"interest_src_accn":["0001018724-26-000004","0001018724-26-000026","0001018724-26-000026"],"fcf_q":-8821000000,"fcf_ttm":-11625000000,"fcf_ttm_prior":13481000000,"fcf_q_prior":332000000,"capex_g_ttm":0.6072304376904214,"capex_g_q":0.6843675232265483,"ocf_g_ttm":0.3324005052131058,"ocf_g_q":0.3958788251576195,"rev_g_ttm":0.15766568463281194,"rev_g_q":0.19620517346245125,"opinc_g_ttm":0.2299776873605459,"opinc_g_q":0.4324239737102915,"interest_g_ttm":0.49372197309417043,"interest_g_q":1.5465116279069768,"opmargin_ttm":0.12081270627062707,"opmargin_ttm_prior":0.11370996868834304,"opmargin_q":0.1368902226254449,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"AMZN","company":"Amazon","period_end":"2026-03-31","capex_q":44203000000,"capex_ttm":151003000000,"capex_ttm_prior":93093000000,"capex_q_prior":25019000000,"capex_src_accn":["0001018724-26-000014"],"ocf_q":26032000000,"ocf_ttm":148531000000,"ocf_ttm_prior":113903000000,"ocf_q_prior":17015000000,"ocf_src_accn":["0001018724-26-000014"],"rev_q":181519000000,"rev_ttm":742776000000,"rev_ttm_prior":650313000000,"rev_q_prior":155667000000,"rev_src_accn":["0001018724-26-000004","0001018724-26-000014","0001018724-26-000014"],"opinc_q":23852000000,"opinc_ttm":85422000000,"opinc_ttm_prior":71691000000,"opinc_q_prior":18405000000,"opinc_src_accn":["0001018724-26-000004","0001018724-26-000014","0001018724-26-000014"],"debt_q":53441000000,"debt_ttm":68368000000,"debt_ttm_prior":746000000,"debt_q_prior":746000000,"debt_src_accn":["0001018724-26-000014"],"interest_q":800000000,"interest_ttm":2533000000,"interest_ttm_prior":2303000000,"interest_q_prior":541000000,"interest_src_accn":["0001018724-26-000004","0001018724-26-000014","0001018724-26-000014"],"fcf_q":-18171000000,"fcf_ttm":-2472000000,"fcf_ttm_prior":20810000000,"fcf_q_prior":-8004000000,"capex_g_ttm":0.6220661059370738,"capex_g_q":0.7667772492905391,"ocf_g_ttm":0.3040130637472236,"ocf_g_q":0.5299441669115486,"rev_g_ttm":0.14218230298333268,"rev_g_q":0.16607244952366274,"opinc_g_ttm":0.19153031761308958,"opinc_g_q":0.2959521869057322,"interest_g_ttm":0.09986973512809372,"interest_g_q":0.478743068391867,"opmargin_ttm":0.11500371579049404,"opmargin_ttm_prior":0.11024076098740145,"opmargin_q":0.13140222235688825}],"filed":"2026-07-31","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":32408000000,"as_of":"2024-06-30","accn":"0001018724-24-000130","form":"10-Q"}},"accn":"0001018724-26-000026","form":"10-Q","accn_filed":"2026-07-31"},"META":{"ticker":"META","company":"Meta","group":"hyperscaler","cik":1326801,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseDebt"]},"rows":[{"ticker":"META","company":"Meta","period_end":"2026-09-30","capex_q":33942000000,"capex_ttm":104438000000,"capex_ttm_prior":62733000000,"capex_q_prior":18829000000,"capex_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"ocf_q":32785000000,"ocf_ttm":133087000000,"ocf_ttm_prior":107574000000,"ocf_q_prior":29999000000,"ocf_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"rev_q":64601000000,"rev_ttm":241605000000,"rev_ttm_prior":189458000000,"rev_q_prior":51242000000,"rev_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"opinc_q":12988000000,"opinc_ttm":79380000000,"opinc_ttm_prior":81895000000,"opinc_q_prior":20535000000,"opinc_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"debt_q":0,"debt_ttm":54816000000,"debt_ttm_prior":0,"debt_q_prior":0,"debt_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"interest_q":882000000,"interest_ttm":2592000000,"interest_ttm_prior":911000000,"interest_q_prior":205000000,"interest_src_accn":["0001628280-26-003942","0001628280-26-066773","0001628280-26-066773"],"fcf_q":-1157000000,"fcf_ttm":28649000000,"fcf_ttm_prior":44841000000,"fcf_q_prior":11170000000,"capex_g_ttm":0.6648016195622719,"capex_g_q":0.8026448563386266,"ocf_g_ttm":0.2371669734322419,"ocf_g_q":0.09286976232541089,"rev_g_ttm":0.27524306178678115,"rev_g_q":0.2607041099098395,"opinc_g_ttm":-0.030710055558947458,"opinc_g_q":-0.3675188702215729,"interest_g_ttm":1.8452250274423712,"interest_g_q":3.302439024390244,"opmargin_ttm":0.3285528031290743,"opmargin_ttm_prior":0.4322593925830527,"opmargin_q":0.2010495193572855,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":1000000,"opinc_recon_diff":0},{"ticker":"META","company":"Meta","period_end":"2026-06-30","capex_q":30116000000,"capex_ttm":89325000000,"capex_ttm_prior":52162000000,"capex_q_prior":16538000000,"capex_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"ocf_q":31862000000,"ocf_ttm":130301000000,"ocf_ttm_prior":102299000000,"ocf_q_prior":25561000000,"ocf_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"rev_q":60801000000,"rev_ttm":228247000000,"rev_ttm_prior":178804000000,"rev_q_prior":47516000000,"rev_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"opinc_q":18775000000,"opinc_ttm":86926000000,"opinc_ttm_prior":78712000000,"opinc_q_prior":20441000000,"opinc_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"debt_q":null,"debt_ttm":54816000000,"debt_ttm_prior":10432000000,"debt_q_prior":null,"debt_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"interest_q":754000000,"interest_ttm":1917000000,"interest_ttm_prior":null,"interest_q_prior":232000000,"interest_src_accn":["0001628280-26-003942","0001628280-26-050705","0001628280-26-050705"],"fcf_q":1746000000,"fcf_ttm":40976000000,"fcf_ttm_prior":50137000000,"fcf_q_prior":9023000000,"capex_g_ttm":0.7124535102181664,"capex_g_q":0.821018260974725,"ocf_g_ttm":0.2737270159043588,"ocf_g_q":0.24650835256836579,"rev_g_ttm":0.27652065949307625,"rev_g_q":0.27959003283104633,"opinc_g_ttm":0.1043551173899786,"opinc_g_q":-0.08150286189521061,"interest_g_ttm":null,"interest_g_q":2.25,"opmargin_ttm":0.3808418073402936,"opmargin_ttm_prior":0.4402138654616228,"opmargin_q":0.3087942632522491}],"filed":"2026-10-22","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":355730000000,"as_of":"2026-09-30","accn":"0001628280-26-066773","form":"10-Q"}},"accn":"0001628280-26-066773","form":"10-Q","accn_filed":"2026-10-22"},"ORCL":{"ticker":"ORCL","company":"Oracle","group":"hyperscaler","cik":1341439,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfSeniorLongTermDebt","ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"ORCL","company":"Oracle","period_end":"2026-08-31","capex_q":28499000000,"capex_ttm":75660000000,"capex_ttm_prior":27414000000,"capex_q_prior":8502000000,"capex_src_accn":["0001193125-26-277521","0001193125-26-389274","0001193125-26-389274"],"ocf_q":23103000000,"ocf_ttm":46940000000,"ocf_ttm_prior":21534000000,"ocf_q_prior":8140000000,"ocf_src_accn":["0001193125-26-277521","0001193125-26-389274","0001193125-26-389274"],"rev_q":19345000000,"rev_ttm":71776000000,"rev_ttm_prior":59018000000,"rev_q_prior":14926000000,"rev_src_accn":["0001193125-26-277521","0001193125-26-389274","0001193125-26-389274"],"opinc_q":6728000000,"opinc_ttm":23057000000,"opinc_ttm_prior":17964000000,"opinc_q_prior":4277000000,"opinc_src_accn":["0001193125-26-277521","0001193125-26-389274","0001193125-26-389274"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":13921000000,"debt_q_prior":0,"debt_src_accn":null,"interest_q":1428000000,"interest_ttm":5104000000,"interest_ttm_prior":3659000000,"interest_q_prior":923000000,"interest_src_accn":["0001193125-26-277521","0001193125-26-389274","0001193125-26-389274"],"fcf_q":-5396000000,"fcf_ttm":-28720000000,"fcf_ttm_prior":-5880000000,"fcf_q_prior":-362000000,"capex_g_ttm":1.759903698840009,"capex_g_q":2.3520348153375674,"ocf_g_ttm":1.1798086746540353,"ocf_g_q":1.8382063882063884,"rev_g_ttm":0.2161713375580332,"rev_g_q":0.2960605654562509,"opinc_g_ttm":0.28351146737920274,"opinc_g_q":0.5730652326397008,"interest_g_ttm":0.3949166438917737,"interest_g_q":0.5471289274106175,"opmargin_ttm":0.3212355104770397,"opmargin_ttm_prior":0.30438171405333964,"opmargin_q":0.3477901266477126,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":1000000,"opinc_recon_diff":-1000000},{"ticker":"ORCL","company":"Oracle","period_end":"2026-05-31","capex_q":16493000000,"capex_ttm":55663000000,"capex_ttm_prior":21215000000,"capex_q_prior":9080000000,"capex_src_accn":["0001193125-26-277521"],"ocf_q":14620000000,"ocf_ttm":31977000000,"ocf_ttm_prior":20821000000,"ocf_q_prior":6157000000,"ocf_src_accn":["0001193125-26-277521"],"rev_q":19184000000,"rev_ttm":67357000000,"rev_ttm_prior":57399000000,"rev_q_prior":15903000000,"rev_src_accn":["0001193125-26-277521"],"opinc_q":6133000000,"opinc_ttm":20606000000,"opinc_ttm_prior":17678000000,"opinc_q_prior":5109000000,"opinc_src_accn":["0001193125-26-277521"],"debt_q":1549000000,"debt_ttm":46093000000,"debt_ttm_prior":19548000000,"debt_q_prior":0,"debt_src_accn":["0001193125-26-277521"],"interest_q":1439000000,"interest_ttm":4599000000,"interest_ttm_prior":3578000000,"interest_q_prior":978000000,"interest_src_accn":["0001193125-26-277521"],"fcf_q":-1873000000,"fcf_ttm":-23686000000,"fcf_ttm_prior":-394000000,"fcf_q_prior":-2923000000,"capex_g_ttm":1.6237567758661324,"capex_g_q":0.8164096916299559,"ocf_g_ttm":0.5358051966764323,"ocf_g_q":1.374533051810947,"rev_g_ttm":0.1734873429850694,"rev_g_q":0.2063132742249889,"opinc_g_ttm":0.16562959610815708,"opinc_g_q":0.20043061264435313,"interest_g_ttm":0.28535494689770813,"interest_g_q":0.47137014314928427,"opmargin_ttm":0.30592217586887777,"opmargin_ttm_prior":0.30798445965957594,"opmargin_q":0.3196934945788157}],"filed":"2026-09-11","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":34150000000,"as_of":"2026-08-31","accn":"0001193125-26-389274","form":"10-Q"}},"accn":"0001193125-26-389274","form":"10-Q","accn_filed":"2026-09-11"},"CRWV":{"ticker":"CRWV","company":"CoreWeave","group":"ai-infrastructure borrower","cik":1769628,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseDebt"]},"rows":[{"ticker":"CRWV","company":"CoreWeave","period_end":"2026-06-30","capex_q":6422000000,"capex_ttm":20566000000,"capex_ttm_prior":8572904000,"capex_q_prior":2453000000,"capex_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"ocf_q":679000000,"ocf_ttm":6911000000,"ocf_ttm_prior":637786000,"ocf_q_prior":-251000000,"ocf_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"rev_q":2575000000,"rev_ttm":7590000000,"rev_ttm_prior":3524945000,"rev_q_prior":1212000000,"rev_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"opinc_q":-49000000,"opinc_ttm":-231000000,"opinc_ttm_prior":221432000,"opinc_q_prior":19000000,"opinc_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"debt_q":13457000000,"debt_ttm":24180000000,"debt_ttm_prior":9592459000,"debt_q_prior":3611000000,"debt_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"interest_q":558000000,"interest_ttm":1619000000,"interest_ttm_prior":755400000,"interest_q_prior":256000000,"interest_src_accn":["0001769628-26-000104","0001769628-26-000366","0001769628-26-000366"],"fcf_q":-5743000000,"fcf_ttm":-13655000000,"fcf_ttm_prior":-7935118000,"fcf_q_prior":-2704000000,"capex_g_ttm":1.398953726765166,"capex_g_q":1.6180187525479006,"ocf_g_ttm":9.835923021201468,"ocf_g_q":null,"rev_g_ttm":1.15322508578148,"rev_g_q":1.1245874587458746,"opinc_g_ttm":-2.0432096535279456,"opinc_g_q":-3.5789473684210527,"interest_g_ttm":1.1432353719883506,"interest_g_q":1.1796875,"opmargin_ttm":-0.030434782608695653,"opmargin_ttm_prior":0.06281856880036427,"opmargin_q":-0.019029126213592235,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":-420000,"opinc_recon_diff":261000},{"ticker":"CRWV","company":"CoreWeave","period_end":"2026-03-31","capex_q":7695000000,"capex_ttm":16597000000,"capex_ttm_prior":8367065000,"capex_q_prior":1407000000,"capex_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"ocf_q":2984000000,"ocf_ttm":5981000000,"ocf_ttm_prior":770962000,"ocf_q_prior":61000000,"ocf_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"rev_q":2078000000,"rev_ttm":6227000000,"rev_ttm_prior":2708316000,"rev_q_prior":982000000,"rev_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"opinc_q":-144000000,"opinc_ttm":-163000000,"opinc_ttm_prior":280153000,"opinc_q_prior":-27000000,"opinc_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"debt_q":3290000000,"debt_ttm":14334000000,"debt_ttm_prior":6871353000,"debt_q_prior":785000000,"debt_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"interest_q":427000000,"interest_ttm":1318000000,"interest_ttm_prior":565497000,"interest_q_prior":257000000,"interest_src_accn":["0001769628-26-000104","0001769628-26-000222","0001769628-26-000222"],"fcf_q":-4711000000,"fcf_ttm":-10616000000,"fcf_ttm_prior":-7596103000,"fcf_q_prior":-1346000000,"capex_g_ttm":0.9836107404448273,"capex_g_q":4.46908315565032,"ocf_g_ttm":6.757840204834999,"ocf_g_q":47.91803278688525,"rev_g_ttm":1.299214714974176,"rev_g_q":1.1160896130346232,"opinc_g_ttm":-1.5818249313767834,"opinc_g_q":null,"interest_g_ttm":1.3306931778594757,"interest_g_q":0.66147859922179,"opmargin_ttm":-0.026176328890316364,"opmargin_ttm_prior":0.1034417697196339,"opmargin_q":-0.06929740134744947}],"filed":"2026-08-12","commits":{},"accn":"0001769628-26-000366","form":"10-Q","accn_filed":"2026-08-12"},"NVDA":{"ticker":"NVDA","company":"NVIDIA CORP","group":"AI supplier","cik":1045810,"tags":{"capex":["PaymentsToAcquireProductiveAssets"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromDebtNetOfIssuanceCosts"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"NVDA","company":"NVIDIA CORP","period_end":"2026-07-26","capex_q":2677000000,"capex_ttm":7354000000,"capex_ttm_prior":5012000000,"capex_q_prior":1895000000,"capex_src_accn":["0001045810-26-000021","0001045810-26-000075","0001045810-26-000075"],"ocf_q":24077000000,"ocf_ttm":134360000000,"ocf_ttm_prior":77035000000,"ocf_q_prior":15365000000,"ocf_src_accn":["0001045810-26-000021","0001045810-26-000075","0001045810-26-000075"],"rev_q":96221000000,"rev_ttm":302970000000,"rev_ttm_prior":165218000000,"rev_q_prior":46743000000,"rev_src_accn":["0001045810-26-000021","0001045810-26-000075","0001045810-26-000075"],"opinc_q":63734000000,"opinc_ttm":197579000000,"opinc_ttm_prior":95980000000,"opinc_q_prior":28440000000,"opinc_src_accn":["0001045810-26-000021","0001045810-26-000075","0001045810-26-000075"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":227000000,"interest_ttm":464000000,"interest_ttm_prior":246000000,"interest_q_prior":62000000,"interest_src_accn":["0001045810-26-000021","0001045810-26-000075","0001045810-26-000075"],"fcf_q":21400000000,"fcf_ttm":127006000000,"fcf_ttm_prior":72023000000,"fcf_q_prior":13470000000,"capex_g_ttm":0.4672785315243415,"capex_g_q":0.41266490765171504,"ocf_g_ttm":0.7441422729927956,"ocf_g_q":0.567002928734136,"rev_g_ttm":0.8337590335193501,"rev_g_q":1.0585114348672526,"opinc_g_ttm":1.058543446551365,"opinc_g_q":1.240998593530239,"interest_g_ttm":0.8861788617886179,"interest_g_q":2.661290322580645,"opmargin_ttm":0.652140475954715,"opmargin_ttm_prior":0.5809294386810154,"opmargin_q":0.6623710000935347,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":-1000000,"opinc_recon_diff":0},{"ticker":"NVDA","company":"NVIDIA CORP","period_end":"2026-04-26","capex_q":1757000000,"capex_ttm":6572000000,"capex_ttm_prior":4094000000,"capex_q_prior":1227000000,"capex_src_accn":["0001045810-26-000021","0001045810-26-000052","0001045810-26-000052"],"ocf_q":50344000000,"ocf_ttm":125648000000,"ocf_ttm_prior":76158000000,"ocf_q_prior":27414000000,"ocf_src_accn":["0001045810-26-000021","0001045810-26-000052","0001045810-26-000052"],"rev_q":81615000000,"rev_ttm":253491000000,"rev_ttm_prior":148515000000,"rev_q_prior":44062000000,"rev_src_accn":["0001045810-26-000021","0001045810-26-000052","0001045810-26-000052"],"opinc_q":53536000000,"opinc_ttm":162285000000,"opinc_ttm_prior":86182000000,"opinc_q_prior":21638000000,"opinc_src_accn":["0001045810-26-000021","0001045810-26-000052","0001045810-26-000052"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":102000000,"interest_ttm":298000000,"interest_ttm_prior":246000000,"interest_q_prior":63000000,"interest_src_accn":["0001045810-26-000021","0001045810-26-000052","0001045810-26-000052"],"fcf_q":48587000000,"fcf_ttm":119076000000,"fcf_ttm_prior":72064000000,"fcf_q_prior":26187000000,"capex_g_ttm":0.605276013678554,"capex_g_q":0.4319478402607988,"ocf_g_ttm":0.649833241419155,"ocf_g_q":0.8364339388633546,"rev_g_ttm":0.7068376931623068,"rev_g_q":0.8522763378875222,"opinc_g_ttm":0.8830498247893992,"opinc_g_q":1.4741658193918106,"interest_g_ttm":0.21138211382113825,"interest_g_q":0.6190476190476191,"opmargin_ttm":0.6402002437956377,"opmargin_ttm_prior":0.5802915530417803,"opmargin_q":0.6559578508852539}],"filed":"2026-08-26","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":22700000000,"as_of":"2026-01-25","accn":"0001045810-26-000021","form":"10-K"},"PurchaseObligation":{"value":45774000000,"as_of":"2025-07-27","accn":"0001045810-25-000209","form":"10-Q"}},"accn":"0001045810-26-000075","form":"10-Q","accn_filed":"2026-08-26"},"AVGO":{"ticker":"AVGO","company":"Broadcom Inc.","group":"AI supplier","cik":1730168,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"AVGO","company":"Broadcom Inc.","period_end":"2026-08-02","capex_q":532000000,"capex_ttm":1250000000,"capex_ttm_prior":508000000,"capex_q_prior":142000000,"capex_src_accn":["0001730168-25-000121","0001730168-26-000080","0001730168-26-000080"],"ocf_q":14197000000,"ocf_ttm":40653000000,"ocf_ttm_prior":25438000000,"ocf_q_prior":7166000000,"ocf_src_accn":["0001730168-25-000121","0001730168-26-000080","0001730168-26-000080"],"rev_q":29591000000,"rev_ttm":89104000000,"rev_ttm_prior":59926000000,"rev_q_prior":15952000000,"rev_src_accn":["0001730168-25-000121","0001730168-26-000080","0001730168-26-000080"],"opinc_q":15955000000,"opinc_ttm":42814000000,"opinc_ttm_prior":22603000000,"opinc_q_prior":5887000000,"opinc_src_accn":["0001730168-25-000121","0001730168-26-000080","0001730168-26-000080"],"debt_q":0,"debt_ttm":9445000000,"debt_ttm_prior":15664000000,"debt_q_prior":6960000000,"debt_src_accn":["0001730168-25-000121","0001730168-26-000080","0001730168-26-000080"],"interest_q":778000000,"interest_ttm":null,"interest_ttm_prior":3365000000,"interest_q_prior":807000000,"interest_src_accn":["0001730168-26-000080"],"fcf_q":13665000000,"fcf_ttm":39403000000,"fcf_ttm_prior":24930000000,"fcf_q_prior":7024000000,"capex_g_ttm":1.4606299212598426,"capex_g_q":2.7464788732394365,"ocf_g_ttm":0.5981209214560894,"ocf_g_q":0.9811610382361149,"rev_g_ttm":0.4869005106297768,"rev_g_q":0.8550025075225678,"opinc_g_ttm":0.8941733398221474,"opinc_g_q":1.7102089349413965,"interest_g_ttm":null,"interest_g_q":-0.035935563816604676,"opmargin_ttm":0.4804947028191776,"opmargin_ttm_prior":0.3771818576244034,"opmargin_q":0.5391842114156331,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"AVGO","company":"Broadcom Inc.","period_end":"2026-05-03","capex_q":231000000,"capex_ttm":860000000,"capex_ttm_prior":538000000,"capex_q_prior":144000000,"capex_src_accn":["0001730168-25-000121","0001730168-26-000054","0001730168-26-000054"],"ocf_q":10493000000,"ocf_ttm":33622000000,"ocf_ttm_prior":23235000000,"ocf_q_prior":6555000000,"ocf_src_accn":["0001730168-25-000121","0001730168-26-000054","0001730168-26-000054"],"rev_q":22187000000,"rev_ttm":75465000000,"rev_ttm_prior":57046000000,"rev_q_prior":15004000000,"rev_src_accn":["0001730168-25-000121","0001730168-26-000054","0001730168-26-000054"],"opinc_q":10788000000,"opinc_ttm":32746000000,"opinc_ttm_prior":20504000000,"opinc_q_prior":5829000000,"opinc_src_accn":["0001730168-25-000121","0001730168-26-000054","0001730168-26-000054"],"debt_q":0,"debt_ttm":16405000000,"debt_ttm_prior":13679000000,"debt_q_prior":749000000,"debt_src_accn":["0001730168-25-000121","0001730168-26-000054","0001730168-26-000054"],"interest_q":776000000,"interest_ttm":null,"interest_ttm_prior":3622000000,"interest_q_prior":769000000,"interest_src_accn":["0001730168-26-000054"],"fcf_q":10262000000,"fcf_ttm":32762000000,"fcf_ttm_prior":22697000000,"fcf_q_prior":6411000000,"capex_g_ttm":0.5985130111524164,"capex_g_q":0.6041666666666667,"ocf_g_ttm":0.44704110178609846,"ocf_g_q":0.6007627765064836,"rev_g_ttm":0.3228797812291835,"rev_g_q":0.47873900293255134,"opinc_g_ttm":0.5970542333203277,"opinc_g_q":0.8507462686567164,"interest_g_ttm":null,"interest_g_q":0.00910273081924573,"opmargin_ttm":0.43392301066719674,"opmargin_ttm_prior":0.35942923254917086,"opmargin_q":0.4862306756208591}],"filed":"2026-09-10","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":126821000000,"as_of":"2026-08-02","accn":"0001730168-26-000080","form":"10-Q"}},"accn":"0001730168-26-000080","form":"10-Q","accn_filed":"2026-09-10"},"AMD":{"ticker":"AMD","company":"ADVANCED MICRO DEVICES INC","group":"AI supplier","cik":2488,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"AMD","company":"ADVANCED MICRO DEVICES INC","period_end":"2026-06-27","capex_q":808000000,"capex_ttm":1677000000,"capex_ttm_prior":834000000,"capex_q_prior":282000000,"capex_src_accn":["0000002488-26-000018","0000002488-26-000123","0000002488-26-000123"],"ocf_q":2366000000,"ocf_ttm":10080000000,"ocf_ttm_prior":4877000000,"ocf_q_prior":2011000000,"ocf_src_accn":["0000002488-26-000018","0000002488-26-000123","0000002488-26-000123"],"rev_q":11536000000,"rev_ttm":41305000000,"rev_ttm_prior":29600000000,"rev_q_prior":7685000000,"rev_src_accn":["0000002488-26-000018","0000002488-26-000123","0000002488-26-000123"],"opinc_q":1990000000,"opinc_ttm":6488000000,"opinc_ttm_prior":2267000000,"opinc_q_prior":-134000000,"opinc_src_accn":["0000002488-26-000018","0000002488-26-000123","0000002488-26-000123"],"debt_q":0,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":0,"debt_src_accn":["0000002488-26-000123","0000002488-26-000076"],"interest_q":37000000,"interest_ttm":147000000,"interest_ttm_prior":100000000,"interest_q_prior":38000000,"interest_src_accn":["0000002488-26-000018","0000002488-26-000123","0000002488-26-000123"],"fcf_q":1558000000,"fcf_ttm":8403000000,"fcf_ttm_prior":4043000000,"fcf_q_prior":1729000000,"capex_g_ttm":1.0107913669064748,"capex_g_q":1.8652482269503547,"ocf_g_ttm":1.0668443715398812,"ocf_g_q":0.17652909000497274,"rev_g_ttm":0.3954391891891893,"rev_g_q":0.5011060507482108,"opinc_g_ttm":1.86193206881341,"opinc_g_q":null,"interest_g_ttm":0.47,"interest_g_q":-0.02631578947368418,"opmargin_ttm":0.15707541459871685,"opmargin_ttm_prior":0.07658783783783783,"opmargin_q":0.17250346740638003,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"AMD","company":"ADVANCED MICRO DEVICES INC","period_end":"2026-03-28","capex_q":389000000,"capex_ttm":1151000000,"capex_ttm_prior":706000000,"capex_q_prior":212000000,"capex_src_accn":["0000002488-26-000018","0000002488-26-000076","0000002488-26-000076"],"ocf_q":2955000000,"ocf_ttm":9725000000,"ocf_ttm_prior":3459000000,"ocf_q_prior":939000000,"ocf_src_accn":["0000002488-26-000018","0000002488-26-000076","0000002488-26-000076"],"rev_q":10253000000,"rev_ttm":37454000000,"rev_ttm_prior":27750000000,"rev_q_prior":7438000000,"rev_src_accn":["0000002488-26-000018","0000002488-26-000076","0000002488-26-000076"],"opinc_q":1476000000,"opinc_ttm":4364000000,"opinc_ttm_prior":2670000000,"opinc_q_prior":806000000,"opinc_src_accn":["0000002488-26-000018","0000002488-26-000076","0000002488-26-000076"],"debt_q":0,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":2441000000,"debt_src_accn":["0000002488-26-000076"],"interest_q":37000000,"interest_ttm":148000000,"interest_ttm_prior":87000000,"interest_q_prior":20000000,"interest_src_accn":["0000002488-26-000018","0000002488-26-000076","0000002488-26-000076"],"fcf_q":2566000000,"fcf_ttm":8574000000,"fcf_ttm_prior":2753000000,"fcf_q_prior":727000000,"capex_g_ttm":0.6303116147308783,"capex_g_q":0.8349056603773586,"ocf_g_ttm":1.8115062156692687,"ocf_g_q":2.146964856230032,"rev_g_ttm":0.34969369369369363,"rev_g_q":0.3784619521376713,"opinc_g_ttm":0.6344569288389512,"opinc_g_q":0.8312655086848635,"interest_g_ttm":0.7011494252873562,"interest_g_q":0.8500000000000001,"opmargin_ttm":0.11651625994553319,"opmargin_ttm_prior":0.09621621621621622,"opmargin_q":0.14395786599044183}],"filed":"2026-08-05","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":30276000000,"as_of":"2026-06-27","accn":"0000002488-26-000123","form":"10-Q"},"PurchaseObligation":{"value":12166000000,"as_of":"2025-12-27","accn":"0000002488-26-000018","form":"10-K"}},"accn":"0000002488-26-000123","form":"10-Q","accn_filed":"2026-08-05"},"MU":{"ticker":"MU","company":"MICRON TECHNOLOGY INC","group":"AI supplier","cik":723125,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"MU","company":"MICRON TECHNOLOGY INC","period_end":"2026-09-03","capex_q":11110000000,"capex_ttm":30712000000,"capex_ttm_prior":15857000000,"capex_q_prior":5658000000,"capex_src_accn":["0000723125-26-000023"],"ocf_q":43973000000,"ocf_ttm":89675000000,"ocf_ttm_prior":17525000000,"ocf_q_prior":5730000000,"ocf_src_accn":["0000723125-26-000023"],"rev_q":54229000000,"rev_ttm":133188000000,"rev_ttm_prior":37378000000,"rev_q_prior":11315000000,"rev_src_accn":["0000723125-26-000023"],"opinc_q":43751000000,"opinc_ttm":99340000000,"opinc_ttm_prior":9770000000,"opinc_q_prior":3654000000,"opinc_src_accn":["0000723125-26-000023"],"debt_q":0,"debt_ttm":0,"debt_ttm_prior":4430000000,"debt_q_prior":0,"debt_src_accn":["0000723125-26-000023"],"interest_q":0,"interest_ttm":106000000,"interest_ttm_prior":477000000,"interest_q_prior":124000000,"interest_src_accn":["0000723125-26-000023"],"fcf_q":32863000000,"fcf_ttm":58963000000,"fcf_ttm_prior":1668000000,"fcf_q_prior":72000000,"capex_g_ttm":0.9368102415337076,"capex_g_q":0.9635913750441851,"ocf_g_ttm":4.1169757489301,"ocf_g_q":6.674171029668412,"rev_g_ttm":2.563272513243084,"rev_g_q":3.7926646045072916,"opinc_g_ttm":9.167860798362334,"opinc_g_q":10.973453749315818,"interest_g_ttm":-0.7777777777777778,"interest_g_q":-1.0,"opmargin_ttm":0.7458629906598192,"opmargin_ttm_prior":0.2613837016426775,"opmargin_q":0.8067823489276955,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"MU","company":"MICRON TECHNOLOGY INC","period_end":"2026-05-28","capex_q":7826000000,"capex_ttm":25260000000,"capex_ttm_prior":13319000000,"capex_q_prior":2938000000,"capex_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"ocf_q":25388000000,"ocf_ttm":51432000000,"ocf_ttm_prior":15200000000,"ocf_q_prior":4609000000,"ocf_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"rev_q":41456000000,"rev_ttm":90274000000,"rev_ttm_prior":33813000000,"rev_q_prior":9301000000,"rev_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"opinc_q":33318000000,"opinc_ttm":59243000000,"opinc_ttm_prior":7638000000,"opinc_q_prior":2169000000,"opinc_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"debt_q":0,"debt_ttm":0,"debt_ttm_prior":4430000000,"debt_q_prior":1748000000,"debt_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"interest_q":0,"interest_ttm":230000000,"interest_ttm_prior":489000000,"interest_q_prior":123000000,"interest_src_accn":["0000723125-26-000023","0000723125-26-000015","0000723125-26-000015"],"fcf_q":17562000000,"fcf_ttm":26172000000,"fcf_ttm_prior":1881000000,"fcf_q_prior":1671000000,"capex_g_ttm":0.8965387791876267,"capex_g_q":1.663716814159292,"ocf_g_ttm":2.3836842105263156,"ocf_g_q":4.508353221957041,"rev_g_ttm":1.6698015556147046,"rev_g_q":3.457155144608107,"opinc_g_ttm":6.756349829798377,"opinc_g_q":14.360995850622407,"interest_g_ttm":-0.5296523517382413,"interest_g_q":-1.0,"opmargin_ttm":0.6562576157033033,"opmargin_ttm_prior":0.22588945080294562,"opmargin_q":0.8036954843689695}],"filed":"2026-10-09","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":10800000000,"as_of":"2026-09-03","accn":"0000723125-26-000023","form":"10-K"}},"accn":"0000723125-26-000023","form":"10-K","accn_filed":"2026-10-09"},"VRT":{"ticker":"VRT","company":"Vertiv Holdings Co","group":"AI supplier (power and cooling)","cik":1674101,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"VRT","company":"Vertiv Holdings Co","period_end":"2026-06-30","capex_q":173300000,"capex_ttm":424400000,"capex_ttm_prior":178600000,"capex_q_prior":45000000,"capex_src_accn":["0001674101-26-000008","0001628280-26-050609","0001628280-26-050609"],"ocf_q":1099800000,"ocf_ttm":3354200000,"ocf_ttm_prior":1426500000,"ocf_q_prior":322900000,"ocf_src_accn":["0001674101-26-000008","0001628280-26-050609","0001628280-26-050609"],"rev_q":3274300000,"rev_ttm":11479600000,"rev_ttm_prior":9094000000,"rev_q_prior":2638100000,"rev_src_accn":["0001674101-26-000008","0001628280-26-050609","0001628280-26-050609"],"opinc_q":637900000,"opinc_ttm":2174600000,"opinc_ttm_prior":1561900000,"opinc_q_prior":442400000,"opinc_src_accn":["0001674101-26-000008","0001628280-26-050609","0001628280-26-050609"],"debt_q":0,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":0,"debt_src_accn":["0001628280-26-050609","0001628280-26-026556"],"interest_q":17400000,"interest_ttm":52500000,"interest_ttm_prior":113200000,"interest_q_prior":21300000,"interest_src_accn":["0001674101-26-000008","0001628280-26-050609","0001628280-26-050609"],"fcf_q":926500000,"fcf_ttm":2929800000,"fcf_ttm_prior":1247900000,"fcf_q_prior":277900000,"capex_g_ttm":1.3762597984322507,"capex_g_q":2.851111111111111,"ocf_g_ttm":1.3513494567122328,"ocf_g_q":2.4060080520284917,"rev_g_ttm":0.26232680888497906,"rev_g_q":0.2411584094613548,"opinc_g_ttm":0.3922786349958385,"opinc_g_q":0.44190777576853524,"interest_g_ttm":-0.5362190812720848,"interest_g_q":-0.18309859154929575,"opmargin_ttm":0.18943168751524445,"opmargin_ttm_prior":0.1717506047943699,"opmargin_q":0.19482026692728216,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"VRT","company":"Vertiv Holdings Co","period_end":"2026-03-31","capex_q":112600000,"capex_ttm":296100000,"capex_ttm_prior":167700000,"capex_q_prior":36500000,"capex_src_accn":["0001674101-26-000008","0001628280-26-026556","0001628280-26-026556"],"ocf_q":766800000,"ocf_ttm":2577300000,"ocf_ttm_prior":1485100000,"ocf_q_prior":303300000,"ocf_src_accn":["0001674101-26-000008","0001628280-26-026556","0001628280-26-026556"],"rev_q":2649500000,"rev_ttm":10843400000,"rev_ttm_prior":8408700000,"rev_q_prior":2036000000,"rev_src_accn":["0001674101-26-000008","0001628280-26-026556","0001628280-26-026556"],"opinc_q":440100000,"opinc_ttm":1979100000,"opinc_ttm_prior":1455500000,"opinc_q_prior":290700000,"opinc_src_accn":["0001674101-26-000008","0001628280-26-026556","0001628280-26-026556"],"debt_q":2100000000,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":0,"debt_src_accn":["0001628280-26-026556"],"interest_q":-4400000,"interest_ttm":56400000,"interest_ttm_prior":136700000,"interest_q_prior":25300000,"interest_src_accn":["0001674101-26-000008","0001628280-26-026556","0001628280-26-026556"],"fcf_q":654200000,"fcf_ttm":2281200000,"fcf_ttm_prior":1317400000,"fcf_q_prior":266800000,"capex_g_ttm":0.7656529516994632,"capex_g_q":2.084931506849315,"ocf_g_ttm":0.7354386909972392,"ocf_g_q":1.5281899109792283,"rev_g_ttm":0.28954535183797736,"rev_g_q":0.3013261296660117,"opinc_g_ttm":0.3597389213328752,"opinc_g_q":0.5139318885448916,"interest_g_ttm":-0.5874177029992684,"interest_g_q":-1.1739130434782608,"opmargin_ttm":0.1825165538484239,"opmargin_ttm_prior":0.1730945330431577,"opmargin_q":0.1661068126061521}],"filed":"2026-07-29","commits":{},"accn":"0001628280-26-050609","form":"10-Q","accn_filed":"2026-07-29"},"CEG":{"ticker":"CEG","company":"Constellation Energy Corp","group":"power utility","cik":1868275,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"CEG","company":"Constellation Energy Corp","period_end":"2026-06-30","capex_q":1246000000,"capex_ttm":3897000000,"capex_ttm_prior":2854000000,"capex_q_prior":767000000,"capex_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"ocf_q":1128000000,"ocf_ttm":4206000000,"ocf_ttm_prior":456000000,"ocf_q_prior":1477000000,"ocf_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"rev_q":5843000000,"rev_ttm":24780000000,"rev_ttm_prior":20568000000,"rev_q_prior":5161000000,"rev_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"opinc_q":580000000,"opinc_ttm":4596000000,"opinc_ttm_prior":3841000000,"opinc_q_prior":951000000,"opinc_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"debt_q":2231000000,"debt_ttm":5001000000,"debt_ttm_prior":20000000,"debt_q_prior":0,"debt_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"interest_q":283000000,"interest_ttm":783000000,"interest_ttm_prior":501000000,"interest_q_prior":118000000,"interest_src_accn":["0001868275-26-000032","0001868275-26-000104","0001868275-26-000104"],"fcf_q":-118000000,"fcf_ttm":309000000,"fcf_ttm_prior":-2398000000,"fcf_q_prior":710000000,"capex_g_ttm":0.36545199719691657,"capex_g_q":0.6245110821382007,"ocf_g_ttm":8.223684210526315,"ocf_g_q":-0.23628977657413675,"rev_g_ttm":0.20478413068844814,"rev_g_q":0.13214493315248976,"opinc_g_ttm":0.19656339494923203,"opinc_g_q":-0.3901156677181914,"interest_g_ttm":0.562874251497006,"interest_g_q":1.3983050847457625,"opmargin_ttm":0.18547215496368039,"opmargin_ttm_prior":0.1867464021781408,"opmargin_q":0.09926407667294199,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":1000000,"opinc_recon_diff":0},{"ticker":"CEG","company":"Constellation Energy Corp","period_end":"2026-03-31","capex_q":1275000000,"capex_ttm":3418000000,"capex_ttm_prior":2633000000,"capex_q_prior":806000000,"capex_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"ocf_q":425000000,"ocf_ttm":4555000000,"ocf_ttm_prior":-1634000000,"ocf_q_prior":107000000,"ocf_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"rev_q":7541000000,"rev_ttm":24098000000,"rev_ttm_prior":19810000000,"rev_q_prior":6106000000,"rev_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"opinc_q":2332000000,"opinc_ttm":4967000000,"opinc_ttm_prior":3990000000,"opinc_q_prior":451000000,"opinc_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"debt_q":2770000000,"debt_ttm":2770000000,"debt_ttm_prior":20000000,"debt_q_prior":0,"debt_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"interest_q":253000000,"interest_ttm":618000000,"interest_ttm_prior":525000000,"interest_q_prior":146000000,"interest_src_accn":["0001868275-26-000032","0001868275-26-000067","0001868275-26-000067"],"fcf_q":-850000000,"fcf_ttm":1137000000,"fcf_ttm_prior":-4267000000,"fcf_q_prior":-699000000,"capex_g_ttm":0.2981390049373338,"capex_g_q":0.5818858560794045,"ocf_g_ttm":null,"ocf_g_q":2.97196261682243,"rev_g_ttm":0.21645633518425034,"rev_g_q":0.23501473960039299,"opinc_g_ttm":0.24486215538847111,"opinc_g_q":4.170731707317073,"interest_g_ttm":0.17714285714285705,"interest_g_q":0.7328767123287672,"opmargin_ttm":0.20611669018175782,"opmargin_ttm_prior":0.20141342756183744,"opmargin_q":0.3092428059939}],"filed":"2026-08-06","commits":{},"accn":"0001868275-26-000104","form":"10-Q","accn_filed":"2026-08-06"},"VST":{"ticker":"VST","company":"Vistra Corp.","group":"power utility","cik":1692819,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"VST","company":"Vistra Corp.","period_end":"2026-06-30","capex_q":689000000,"capex_ttm":2866000000,"capex_ttm_prior":2573000000,"capex_q_prior":690000000,"capex_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"ocf_q":1023000000,"ocf_ttm":5121000000,"ocf_ttm_prior":4226000000,"ocf_q_prior":572000000,"ocf_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"rev_q":4401000000,"rev_ttm":18985000000,"rev_ttm_prior":16006000000,"rev_q_prior":3753000000,"rev_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"opinc_q":553000000,"opinc_ttm":3563000000,"opinc_ttm_prior":3582000000,"opinc_q_prior":515000000,"opinc_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"debt_q":4172000000,"debt_ttm":8719000000,"debt_ttm_prior":1826000000,"debt_q_prior":209000000,"debt_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"interest_q":312000000,"interest_ttm":1132000000,"interest_ttm_prior":1111000000,"interest_q_prior":303000000,"interest_src_accn":["0001692819-26-000006","0001692819-26-000019","0001692819-26-000019"],"fcf_q":334000000,"fcf_ttm":2255000000,"fcf_ttm_prior":1653000000,"fcf_q_prior":-118000000,"capex_g_ttm":0.11387485425573263,"capex_g_q":-0.0014492753623188692,"ocf_g_ttm":0.21178419309039276,"ocf_g_q":0.7884615384615385,"rev_g_ttm":0.1861177058603023,"rev_g_q":0.17266187050359716,"opinc_g_ttm":-0.0053042992741485495,"opinc_g_q":0.0737864077669903,"interest_g_ttm":0.018901890189019,"interest_g_q":0.02970297029702973,"opmargin_ttm":0.18767447985251515,"opmargin_ttm_prior":0.2237910783456204,"opmargin_q":0.12565326062258578,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"VST","company":"Vistra Corp.","period_end":"2026-03-31","capex_q":883000000,"capex_ttm":2867000000,"capex_ttm_prior":2381000000,"capex_q_prior":768000000,"capex_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"ocf_q":1199000000,"ocf_ttm":4670000000,"ocf_ttm_prior":4850000000,"ocf_q_prior":599000000,"ocf_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"rev_q":5001000000,"rev_ttm":18337000000,"rev_ttm_prior":15852000000,"rev_q_prior":4250000000,"rev_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"opinc_q":1499000000,"opinc_ttm":3525000000,"opinc_ttm_prior":3875000000,"opinc_q_prior":-120000000,"opinc_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"debt_q":2250000000,"debt_ttm":4756000000,"debt_ttm_prior":3117000000,"debt_q_prior":0,"debt_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"interest_q":263000000,"interest_ttm":1123000000,"interest_ttm_prior":1049000000,"interest_q_prior":319000000,"interest_src_accn":["0001692819-26-000006","0001692819-26-000014","0001692819-26-000014"],"fcf_q":316000000,"fcf_ttm":1803000000,"fcf_ttm_prior":2469000000,"fcf_q_prior":-169000000,"capex_g_ttm":0.20411591768164628,"capex_g_q":0.14973958333333326,"ocf_g_ttm":-0.03711340206185565,"ocf_g_q":1.001669449081803,"rev_g_ttm":0.15676255362099423,"rev_g_q":0.17670588235294127,"opinc_g_ttm":-0.0903225806451613,"opinc_g_q":null,"interest_g_ttm":0.07054337464251659,"interest_g_q":-0.17554858934169282,"opmargin_ttm":0.19223428041664395,"opmargin_ttm_prior":0.2444486500126167,"opmargin_q":0.2997400519896021}],"filed":"2026-08-10","commits":{},"accn":"0001692819-26-000019","form":"10-Q","accn_filed":"2026-08-10"},"NEE":{"ticker":"NEE","company":"NEXTERA ENERGY INC","group":"power utility","cik":753308,"tags":{"capex":[],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerIncludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":[]},"rows":[{"ticker":"NEE","company":"NEXTERA ENERGY INC","period_end":"2026-03-31","capex_q":null,"capex_ttm":null,"capex_ttm_prior":null,"capex_q_prior":null,"capex_src_accn":null,"ocf_q":2614000000,"ocf_ttm":12330000000,"ocf_ttm_prior":12952000000,"ocf_q_prior":2769000000,"ocf_src_accn":["0000753308-26-000015","0000753308-26-000031","0000753308-26-000031"],"rev_q":6100000000,"rev_ttm":25900000000,"rev_ttm_prior":24100000000,"rev_q_prior":6000000000,"rev_src_accn":["0000753308-26-000015","0000753308-26-000031","0000753308-26-000031"],"opinc_q":2208000000,"opinc_ttm":8232000000,"opinc_ttm_prior":7722000000,"opinc_q_prior":2256000000,"opinc_src_accn":["0000753308-26-000015","0000753308-26-000031","0000753308-26-000031"],"debt_q":8307000000,"debt_ttm":21861000000,"debt_ttm_prior":26798000000,"debt_q_prior":9840000000,"debt_src_accn":["0000753308-26-000015","0000753308-26-000031","0000753308-26-000031"],"interest_q":null,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":null,"interest_src_accn":null,"fcf_q":null,"fcf_ttm":null,"fcf_ttm_prior":null,"fcf_q_prior":null,"capex_g_ttm":null,"capex_g_q":null,"ocf_g_ttm":-0.04802347127856699,"ocf_g_q":-0.05597688696280245,"rev_g_ttm":0.07468879668049788,"rev_g_q":0.016666666666666607,"opinc_g_ttm":0.06604506604506599,"opinc_g_q":-0.021276595744680882,"interest_g_ttm":null,"interest_g_q":null,"opmargin_ttm":0.3178378378378378,"opmargin_ttm_prior":0.3204149377593361,"opmargin_q":0.3619672131147541,"ocf_recon_diff":0,"rev_recon_diff":100000000,"opinc_recon_diff":0},{"ticker":"NEE","company":"NEXTERA ENERGY INC","period_end":"2025-12-31","capex_q":null,"capex_ttm":null,"capex_ttm_prior":null,"capex_q_prior":null,"capex_src_accn":null,"ocf_q":2499000000,"ocf_ttm":12485000000,"ocf_ttm_prior":13260000000,"ocf_q_prior":1981000000,"ocf_src_accn":["0000753308-26-000015"],"rev_q":6100000000,"rev_ttm":25800000000,"rev_ttm_prior":23500000000,"rev_q_prior":5300000000,"rev_src_accn":["0000753308-26-000015"],"opinc_q":1586000000,"opinc_ttm":8280000000,"opinc_ttm_prior":7479000000,"opinc_q_prior":941000000,"opinc_src_accn":["0000753308-26-000015"],"debt_q":8148000000,"debt_ttm":23394000000,"debt_ttm_prior":24769000000,"debt_q_prior":8594000000,"debt_src_accn":["0000753308-26-000015"],"interest_q":null,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":null,"interest_src_accn":null,"fcf_q":null,"fcf_ttm":null,"fcf_ttm_prior":null,"fcf_q_prior":null,"capex_g_ttm":null,"capex_g_q":null,"ocf_g_ttm":-0.05844645550527905,"ocf_g_q":0.2614840989399294,"rev_g_ttm":0.09787234042553195,"rev_g_q":0.15094339622641506,"opinc_g_ttm":0.10709987966305645,"opinc_g_q":0.6854410201912859,"interest_g_ttm":null,"interest_g_q":null,"opmargin_ttm":0.3209302325581395,"opmargin_ttm_prior":0.3182553191489362,"opmargin_q":0.26}],"filed":"2026-04-23","commits":{},"accn":"0000753308-26-000031","form":"10-Q","accn_filed":"2026-04-23"},"EQIX":{"ticker":"EQIX","company":"EQUINIX INC","group":"digital infrastructure REIT","cik":1101239,"tags":{"capex":["PaymentsToAcquireOtherPropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfSeniorLongTermDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"EQIX","company":"EQUINIX INC","period_end":"2026-06-30","capex_q":1578000000,"capex_ttm":5406000000,"capex_ttm_prior":3450000000,"capex_q_prior":989000000,"capex_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"ocf_q":1067000000,"ocf_ttm":3942000000,"ocf_ttm_prior":3492000000,"ocf_q_prior":944000000,"ocf_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"rev_q":2625000000,"rev_ttm":9805000000,"rev_ttm_prior":8943000000,"rev_q_prior":2256000000,"rev_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"opinc_q":665000000,"opinc_ttm":2138000000,"opinc_ttm_prior":1480000000,"opinc_q_prior":494000000,"opinc_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"debt_q":927000000,"debt_ttm":4664000000,"debt_ttm_prior":4090000000,"debt_q_prior":1696000000,"debt_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"interest_q":151000000,"interest_ttm":569000000,"interest_ttm_prior":500000000,"interest_q_prior":135000000,"interest_src_accn":["0001101239-26-000032","0001101239-26-000147","0001101239-26-000147"],"fcf_q":-511000000,"fcf_ttm":-1464000000,"fcf_ttm_prior":42000000,"fcf_q_prior":-45000000,"capex_g_ttm":0.5669565217391304,"capex_g_q":0.5955510616784632,"ocf_g_ttm":0.12886597938144329,"ocf_g_q":0.13029661016949157,"rev_g_ttm":0.09638823660963891,"rev_g_q":0.16356382978723394,"opinc_g_ttm":0.4445945945945946,"opinc_g_q":0.34615384615384626,"interest_g_ttm":0.1379999999999999,"interest_g_q":0.11851851851851847,"opmargin_ttm":0.21805201427842938,"opmargin_ttm_prior":0.16549256401654924,"opmargin_q":0.25333333333333335,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"EQIX","company":"EQUINIX INC","period_end":"2026-03-31","capex_q":1256000000,"capex_ttm":4817000000,"capex_ttm_prior":3109000000,"capex_q_prior":750000000,"capex_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"ocf_q":717000000,"ocf_ttm":3819000000,"ocf_ttm_prior":3460000000,"ocf_q_prior":809000000,"ocf_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"rev_q":2444000000,"rev_ttm":9436000000,"rev_ttm_prior":8846000000,"rev_q_prior":2225000000,"rev_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"opinc_q":577000000,"opinc_ttm":1967000000,"opinc_ttm_prior":1422000000,"opinc_q_prior":458000000,"opinc_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"debt_q":1492000000,"debt_ttm":5433000000,"debt_ttm_prior":3138000000,"debt_q_prior":370000000,"debt_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"interest_q":148000000,"interest_ttm":553000000,"interest_ttm_prior":475000000,"interest_q_prior":122000000,"interest_src_accn":["0001101239-26-000032","0001101239-26-000091","0001101239-26-000091"],"fcf_q":-539000000,"fcf_ttm":-998000000,"fcf_ttm_prior":351000000,"fcf_q_prior":59000000,"capex_g_ttm":0.5493727886780315,"capex_g_q":0.6746666666666667,"ocf_g_ttm":0.10375722543352595,"ocf_g_q":-0.11372064276885041,"rev_g_ttm":0.06669681211847167,"rev_g_q":0.09842696629213488,"opinc_g_ttm":0.38326300984528827,"opinc_g_q":0.259825327510917,"interest_g_ttm":0.16421052631578958,"interest_g_q":0.21311475409836067,"opmargin_ttm":0.20845697329376855,"opmargin_ttm_prior":0.16075062174994348,"opmargin_q":0.23608837970540097}],"filed":"2026-07-29","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":708000000,"as_of":"2026-06-30","accn":"0001101239-26-000147","form":"10-Q"},"PurchaseObligation":{"value":8239000000,"as_of":"2026-06-30","accn":"0001101239-26-000147","form":"10-Q"}},"accn":"0001101239-26-000147","form":"10-Q","accn_filed":"2026-07-29"},"DLR":{"ticker":"DLR","company":"DIGITAL REALTY TRUST, INC.","group":"digital infrastructure REIT","cik":1297996,"tags":{"capex":["PaymentsToDevelopRealEstateAssets"],"ocf":["NetCashProvidedByUsedInOperatingActivities","NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],"rev":["Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"DLR","company":"DIGITAL REALTY TRUST, INC.","period_end":"2026-03-31","capex_q":870038000,"capex_ttm":3263914000,"capex_ttm_prior":2959728000,"capex_q_prior":787303000,"capex_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"ocf_q":532421000,"ocf_ttm":2545472000,"ocf_ttm_prior":2308287000,"ocf_q_prior":399085000,"ocf_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"rev_q":1635173000,"rev_ttm":6340228000,"rev_ttm_prior":5631462000,"rev_q_prior":1407637000,"rev_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"opinc_q":267806000,"opinc_ttm":729437000,"opinc_ttm_prior":519358000,"opinc_q_prior":196861000,"opinc_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"debt_q":39008000,"debt_ttm":2656630000,"debt_ttm_prior":3100717000,"debt_q_prior":871286000,"debt_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"interest_q":116384000,"interest_ttm":455867000,"interest_ttm_prior":441765000,"interest_q_prior":98464000,"interest_src_accn":["0001104659-26-015365","0001104659-26-054255","0001104659-26-054255"],"fcf_q":-337617000,"fcf_ttm":-718442000,"fcf_ttm_prior":-651441000,"fcf_q_prior":-388218000,"capex_g_ttm":0.10277498472832636,"capex_g_q":0.1050866057921791,"ocf_g_ttm":0.102753687041516,"ocf_g_q":0.3341042635027627,"rev_g_ttm":0.12585825847710597,"rev_g_q":0.16164394655724457,"opinc_g_ttm":0.4044974757296509,"opinc_g_q":0.36038118266187813,"interest_g_ttm":0.03192194945276339,"interest_g_q":0.18199545011374707,"opmargin_ttm":0.11504901716468241,"opmargin_ttm_prior":0.0922243637620213,"opmargin_q":0.16377838919796253,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":1111000},{"ticker":"DLR","company":"DIGITAL REALTY TRUST, INC.","period_end":"2025-12-31","capex_q":1002161000,"capex_ttm":3181179000,"capex_ttm_prior":2831740000,"capex_q_prior":735410000,"capex_src_accn":["0001104659-26-015365"],"ocf_q":718953000,"ocf_ttm":2412136000,"ocf_ttm_prior":2261477000,"ocf_q_prior":769475000,"ocf_src_accn":["0001104659-26-015365"],"rev_q":1634671000,"rev_ttm":6112692000,"rev_ttm_prior":5554968000,"rev_q_prior":1435862000,"rev_src_accn":["0001104659-26-015365"],"opinc_q":112624000,"opinc_ttm":658492000,"opinc_ttm_prior":471864000,"opinc_q_prior":144322000,"opinc_src_accn":["0001104659-26-015365"],"debt_q":1612577000,"debt_ttm":3488908000,"debt_ttm_prior":2234999000,"debt_q_prior":1207492000,"debt_src_accn":["0001104659-26-015365"],"interest_q":116516000,"interest_ttm":437947000,"interest_ttm_prior":452836000,"interest_q_prior":104742000,"interest_src_accn":["0001104659-26-015365"],"fcf_q":-283208000,"fcf_ttm":-769043000,"fcf_ttm_prior":-570263000,"fcf_q_prior":34065000,"capex_g_ttm":0.12340080657122465,"capex_g_q":0.3627241946669204,"ocf_g_ttm":0.06661973568601409,"ocf_g_q":-0.06565775366321192,"rev_g_ttm":0.1004009384032456,"rev_g_q":0.13845968484436533,"opinc_g_ttm":0.3955122662462065,"opinc_g_q":-0.21963387425340553,"interest_g_ttm":-0.032879453047019225,"interest_g_q":0.11240953963071165,"opmargin_ttm":0.10772536879005191,"opmargin_ttm_prior":0.08494450373071456,"opmargin_q":0.06889704411468729}],"filed":"2026-05-01","commits":{},"accn":"0001104659-26-054255","form":"10-Q","accn_filed":"2026-05-01"},"XOM":{"ticker":"XOM","company":"ExxonMobil Holdings Corp","group":"heavy-capex industrial","cik":2115436,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["Revenues"],"opinc":[],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpense"]},"rows":[{"ticker":"XOM","company":"ExxonMobil Holdings Corp","period_end":"2026-06-30","capex_q":null,"capex_ttm":null,"capex_ttm_prior":null,"capex_q_prior":null,"capex_src_accn":null,"ocf_q":null,"ocf_ttm":null,"ocf_ttm_prior":null,"ocf_q_prior":null,"ocf_src_accn":null,"rev_q":116017000000,"rev_ttm":null,"rev_ttm_prior":null,"rev_q_prior":81506000000,"rev_src_accn":["0000034088-26-000093"],"opinc_q":null,"opinc_ttm":null,"opinc_ttm_prior":null,"opinc_q_prior":null,"opinc_src_accn":null,"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":227000000,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":145000000,"interest_src_accn":["0000034088-26-000093"],"fcf_q":null,"fcf_ttm":null,"fcf_ttm_prior":null,"fcf_q_prior":null,"capex_g_ttm":null,"capex_g_q":null,"ocf_g_ttm":null,"ocf_g_q":null,"rev_g_ttm":null,"rev_g_q":0.4234166809805413,"opinc_g_ttm":null,"opinc_g_q":null,"interest_g_ttm":null,"interest_g_q":0.5655172413793104,"opmargin_ttm":null,"opmargin_ttm_prior":null,"opmargin_q":null},{"ticker":"XOM","company":"ExxonMobil Holdings Corp","period_end":"2025-06-30","capex_q":null,"capex_ttm":null,"capex_ttm_prior":null,"capex_q_prior":null,"capex_src_accn":null,"ocf_q":null,"ocf_ttm":null,"ocf_ttm_prior":null,"ocf_q_prior":null,"ocf_src_accn":null,"rev_q":81506000000,"rev_ttm":null,"rev_ttm_prior":null,"rev_q_prior":null,"rev_src_accn":["0000034088-26-000093"],"opinc_q":null,"opinc_ttm":null,"opinc_ttm_prior":null,"opinc_q_prior":null,"opinc_src_accn":null,"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":145000000,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":null,"interest_src_accn":["0000034088-26-000093"],"fcf_q":null,"fcf_ttm":null,"fcf_ttm_prior":null,"fcf_q_prior":null,"capex_g_ttm":null,"capex_g_q":null,"ocf_g_ttm":null,"ocf_g_q":null,"rev_g_ttm":null,"rev_g_q":null,"opinc_g_ttm":null,"opinc_g_q":null,"interest_g_ttm":null,"interest_g_q":null,"opmargin_ttm":null,"opmargin_ttm_prior":null,"opmargin_q":null}],"filed":"2026-08-03","commits":{},"accn":"0000034088-26-000093","form":"10-Q","accn_filed":"2026-08-03"},"T":{"ticker":"T","company":"AT&T INC.","group":"telecom","cik":732717,"tags":{"capex":["PaymentsToAcquireProductiveAssets"],"ocf":["NetCashProvidedByUsedInOperatingActivitiesContinuingOperations","NetCashProvidedByUsedInOperatingActivities"],"rev":["Revenues"],"opinc":["OperatingIncomeLoss"],"debt":["ProceedsFromIssuanceOfLongTermDebt"],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"T","company":"AT&T INC.","period_end":"2026-09-30","capex_q":5061000000,"capex_ttm":22419000000,"capex_ttm_prior":20904000000,"capex_q_prior":4887000000,"capex_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"ocf_q":10519000000,"ocf_ttm":40235000000,"ocf_ttm_prior":40860000000,"ocf_q_prior":10152000000,"ocf_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"rev_q":32322000000,"rev_ttm":128852000000,"rev_ttm_prior":124480000000,"rev_q_prior":30709000000,"rev_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"opinc_q":4095000000,"opinc_ttm":23579000000,"opinc_ttm_prior":23700000000,"opinc_q_prior":6119000000,"opinc_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"debt_q":21833000000,"debt_ttm":35870000000,"debt_ttm_prior":14042000000,"debt_q_prior":7598000000,"debt_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"interest_q":1979000000,"interest_ttm":7466000000,"interest_ttm_prior":6674000000,"interest_q_prior":1700000000,"interest_src_accn":["0000732717-26-000120","0000732717-26-000372","0000732717-26-000372"],"fcf_q":5458000000,"fcf_ttm":17816000000,"fcf_ttm_prior":19956000000,"fcf_q_prior":5265000000,"capex_g_ttm":0.07247416762342129,"capex_g_q":0.03560466543891949,"ocf_g_ttm":-0.015296133137542856,"ocf_g_q":0.03615051221434196,"rev_g_ttm":0.03512210796915172,"rev_g_q":0.05252531831059293,"opinc_g_ttm":-0.0051054852320675526,"opinc_g_q":-0.3307730021245302,"interest_g_ttm":0.11866946359005093,"interest_g_q":0.16411764705882348,"opmargin_ttm":0.18299289106882313,"opmargin_ttm_prior":0.19039203084832904,"opmargin_q":0.12669389270465936,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"T","company":"AT&T INC.","period_end":"2026-06-30","capex_q":5700000000,"capex_ttm":22245000000,"capex_ttm_prior":21319000000,"capex_q_prior":4897000000,"capex_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"ocf_q":10801000000,"ocf_ttm":39868000000,"ocf_ttm_prior":40943000000,"ocf_q_prior":9763000000,"ocf_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"rev_q":31558000000,"rev_ttm":127239000000,"rev_ttm_prior":123984000000,"rev_q_prior":30847000000,"rev_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"opinc_q":7038000000,"opinc_ttm":25603000000,"opinc_ttm_prior":19697000000,"opinc_q_prior":6501000000,"opinc_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"debt_q":5939000000,"debt_ttm":21635000000,"debt_ttm_prior":6446000000,"debt_q_prior":3473000000,"debt_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"interest_q":1883000000,"interest_ttm":7187000000,"interest_ttm_prior":6649000000,"interest_q_prior":1655000000,"interest_src_accn":["0000732717-26-000120","0000732717-26-000297","0000732717-26-000297"],"fcf_q":5101000000,"fcf_ttm":17623000000,"fcf_ttm_prior":19624000000,"fcf_q_prior":4866000000,"capex_g_ttm":0.04343543318166887,"capex_g_q":0.1639779456810293,"ocf_g_ttm":-0.026256014459126065,"ocf_g_q":0.10631977875652976,"rev_g_ttm":0.026253387533875294,"rev_g_q":0.02304924303822098,"opinc_g_ttm":0.2998426156267451,"opinc_g_q":0.08260267651130593,"interest_g_ttm":0.08091442322153708,"interest_g_q":0.13776435045317226,"opmargin_ttm":0.20121975180565707,"opmargin_ttm_prior":0.15886727319654148,"opmargin_q":0.22301793523036947}],"filed":"2026-10-21","commits":{},"accn":"0000732717-26-000372","form":"10-Q","accn_filed":"2026-10-21"},"CRM":{"ticker":"CRM","company":"Salesforce, Inc.","group":"low-capex software","cik":1108524,"tags":{"capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"ocf":["NetCashProvidedByUsedInOperatingActivities"],"rev":["RevenueFromContractWithCustomerExcludingAssessedTax"],"opinc":["OperatingIncomeLoss"],"debt":[],"interest":["InterestExpenseNonoperating"]},"rows":[{"ticker":"CRM","company":"Salesforce, Inc.","period_end":"2026-07-31","capex_q":171000000,"capex_ttm":596000000,"capex_ttm_prior":672000000,"capex_q_prior":135000000,"capex_src_accn":["0001108524-26-000060","0001108524-26-000190","0001108524-26-000190"],"ocf_q":1269000000,"ocf_ttm":15750000000,"ocf_ttm_prior":13169000000,"ocf_q_prior":740000000,"ocf_src_accn":["0001108524-26-000060","0001108524-26-000190","0001108524-26-000190"],"rev_q":11345000000,"rev_ttm":43938000000,"rev_ttm_prior":39502000000,"rev_q_prior":10236000000,"rev_src_accn":["0001108524-26-000060","0001108524-26-000190","0001108524-26-000190"],"opinc_q":2331000000,"opinc_ttm":8735000000,"opinc_ttm_prior":7987000000,"opinc_q_prior":2332000000,"opinc_src_accn":["0001108524-26-000060","0001108524-26-000190","0001108524-26-000190"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":473000000,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":67000000,"interest_src_accn":["0001108524-26-000190"],"fcf_q":1098000000,"fcf_ttm":15154000000,"fcf_ttm_prior":12497000000,"fcf_q_prior":605000000,"capex_g_ttm":-0.11309523809523814,"capex_g_q":0.2666666666666666,"ocf_g_ttm":0.19599058394714852,"ocf_g_q":0.7148648648648648,"rev_g_ttm":0.11229811148802593,"rev_g_q":0.1083431027745212,"opinc_g_ttm":0.09365218480030046,"opinc_g_q":-0.00042881646655235084,"interest_g_ttm":null,"interest_g_q":6.059701492537314,"opmargin_ttm":0.1988028585734444,"opmargin_ttm_prior":0.2021922940610602,"opmargin_q":0.20546496253856325,"capex_recon_diff":0,"ocf_recon_diff":0,"rev_recon_diff":0,"opinc_recon_diff":0},{"ticker":"CRM","company":"Salesforce, Inc.","period_end":"2026-04-30","capex_q":145000000,"capex_ttm":560000000,"capex_ttm_prior":674000000,"capex_q_prior":179000000,"capex_src_accn":["0001108524-26-000060","0001108524-26-000127","0001108524-26-000127"],"ocf_q":6701000000,"ocf_ttm":15221000000,"ocf_ttm_prior":13321000000,"ocf_q_prior":6476000000,"ocf_src_accn":["0001108524-26-000060","0001108524-26-000127","0001108524-26-000127"],"rev_q":11133000000,"rev_ttm":42829000000,"rev_ttm_prior":38591000000,"rev_q_prior":9829000000,"rev_src_accn":["0001108524-26-000060","0001108524-26-000127","0001108524-26-000127"],"opinc_q":2347000000,"opinc_ttm":8736000000,"opinc_ttm_prior":7438000000,"opinc_q_prior":1942000000,"opinc_src_accn":["0001108524-26-000060","0001108524-26-000127","0001108524-26-000127"],"debt_q":null,"debt_ttm":null,"debt_ttm_prior":null,"debt_q_prior":null,"debt_src_accn":null,"interest_q":317000000,"interest_ttm":null,"interest_ttm_prior":null,"interest_q_prior":68000000,"interest_src_accn":["0001108524-26-000127"],"fcf_q":6556000000,"fcf_ttm":14661000000,"fcf_ttm_prior":12647000000,"fcf_q_prior":6297000000,"capex_g_ttm":-0.16913946587537088,"capex_g_q":-0.1899441340782123,"ocf_g_ttm":0.1426319345394489,"ocf_g_q":0.0347436689314391,"rev_g_ttm":0.10981835142908958,"rev_g_q":0.13266863363516124,"opinc_g_ttm":0.17450927668728156,"opinc_g_q":0.2085478887744594,"interest_g_ttm":null,"interest_g_q":3.6617647058823533,"opmargin_ttm":0.20397394288916387,"opmargin_ttm_prior":0.1927392397191055,"opmargin_q":0.21081469505075}],"filed":"2026-08-27","commits":{"UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount":{"value":4200000000,"as_of":"2026-07-31","accn":"0001108524-26-000190","form":"10-Q"},"PurchaseObligation":{"value":2000000000,"as_of":"2019-01-31","accn":"0001108524-19-000009","form":"10-K"}},"accn":"0001108524-26-000190","form":"10-Q","accn_filed":"2026-08-27"}},"market":{"MSFT":{"last_bar_date":"2026-10-26","last_close":532.5999755859375,"currency":"USD","ret_1d_pct":1.5423854015536254,"ret_5d_pct":-0.17244787667403116,"volume_last":18814100,"volume_avg_20d":20195760.0,"volume_ratio":0.9315866300649245,"spark":[508.96,512.9,512.8,517.53,525.18,529.3,529.76,522.61,535.07,541.15,543.45,533.69,539.44,529.05,533.52,531.87,532.95,521.08,524.51,532.6],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094745.5722172,"fetched_utc":"2026-10-27 09:52 UTC"},"GOOGL":{"last_bar_date":"2026-10-26","last_close":316.79998779296875,"currency":"USD","ret_1d_pct":-1.064927314295805,"ret_5d_pct":-7.955141340422001,"volume_last":23918300,"volume_avg_20d":23686590.0,"volume_ratio":1.0097823283131933,"spark":[340.92,344.08,338.24,343.5,346.47,347.68,350.5,348.29,351.66,352.72,353.78,347.64,349.22,340.59,344.18,340.28,334.76,324.22,320.21,316.8],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094745.966977,"fetched_utc":"2026-10-27 09:52 UTC"},"AMZN":{"last_bar_date":"2026-10-26","last_close":249.08999633789062,"currency":"USD","ret_1d_pct":0.4395146523752613,"ret_5d_pct":-5.090499237089652,"volume_last":32613300,"volume_avg_20d":35818075.0,"volume_ratio":0.9105263194630085,"spark":[246.67,249.15,248.23,251.52,251.4,256.29,259.92,254.06,262.43,259.53,258.58,254.08,254.76,250.0,262.45,262.63,262.37,250.38,248.0,249.09],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094746.3512955,"fetched_utc":"2026-10-27 09:52 UTC"},"META":{"last_bar_date":"2026-10-26","last_close":630.5599975585938,"currency":"USD","ret_1d_pct":-1.8766919252791836,"ret_5d_pct":-10.614652503921763,"volume_last":30862600,"volume_avg_20d":19255370.0,"volume_ratio":1.6028048279518907,"spark":[738.79,725.18,725.93,728.08,741.9,738.88,721.31,720.89,718.67,742.96,762.5,737.54,736.72,709.33,705.44,694.25,697.52,648.85,642.62,630.56],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094746.7360225,"fetched_utc":"2026-10-27 09:52 UTC"},"ORCL":{"last_bar_date":"2026-10-26","last_close":126.05999755859375,"currency":"USD","ret_1d_pct":-0.07926926174119941,"ret_5d_pct":-2.7239747504065215,"volume_last":22937700,"volume_avg_20d":29364510.0,"volume_ratio":0.7811368212852862,"spark":[137.79,137.3,138.07,142.3,142.48,144.77,143.56,135.69,141.4,137.39,143.2,130.55,134.47,128.23,129.59,131.14,129.13,125.54,126.16,126.06],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094747.1394086,"fetched_utc":"2026-10-27 09:52 UTC"},"CRWV":{"last_bar_date":"2026-10-26","last_close":55.189998626708984,"currency":"USD","ret_1d_pct":1.7608518587812982,"ret_5d_pct":-9.70222579974923,"volume_last":68580500,"volume_avg_20d":51813535.0,"volume_ratio":1.3236020279257148,"spark":[85.93,87.12,88.57,89.62,87.39,91.72,88.45,81.58,82.08,80.26,77.81,65.78,69.69,61.39,61.12,62.13,61.82,55.6,54.24,55.19],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094747.534538,"fetched_utc":"2026-10-27 09:52 UTC"},"NVDA":{"last_bar_date":"2026-10-26","last_close":216.0,"currency":"USD","ret_1d_pct":2.3890752397295545,"ret_5d_pct":-0.5020942264857275,"volume_last":90493500,"volume_avg_20d":105304700.0,"volume_ratio":0.8593491078745773,"spark":[227.21,228.38,230.86,233.95,238.9,239.24,237.47,230.48,229.28,226.32,228.52,221.3,217.23,214.13,217.09,216.47,221.97,212.21,210.96,216.0],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094747.9408422,"fetched_utc":"2026-10-27 09:52 UTC"},"AVGO":{"last_bar_date":"2026-10-26","last_close":329.1700134277344,"currency":"USD","ret_1d_pct":2.3284073994313426,"ret_5d_pct":-1.6198879134099342,"volume_last":18558000,"volume_avg_20d":21682805.0,"volume_ratio":0.8558855738452659,"spark":[355.1,351.19,343.64,355.14,362.51,375.81,376.51,360.14,361.54,354.73,357.31,346.25,344.33,328.75,334.59,334.37,337.8,323.24,321.68,329.17],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094748.3312652,"fetched_utc":"2026-10-27 09:52 UTC"},"AMD":{"last_bar_date":"2026-10-26","last_close":531.280029296875,"currency":"USD","ret_1d_pct":2.8038568636415295,"ret_5d_pct":-1.2582396895618353,"volume_last":16718300,"volume_avg_20d":19487285.0,"volume_ratio":0.8579081180369662,"spark":[607.57,611.76,615.73,633.91,631.75,649.42,645.86,620.68,608.1,594.24,605.53,570.82,562.23,528.75,538.05,534.74,552.72,507.93,516.79,531.28],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094748.7135935,"fetched_utc":"2026-10-27 09:52 UTC"},"MU":{"last_bar_date":"2026-10-26","last_close":903.7000122070312,"currency":"USD","ret_1d_pct":2.9798900094374803,"ret_5d_pct":-0.1326126836838415,"volume_last":22705400,"volume_avg_20d":26901420.0,"volume_ratio":0.8440223601579396,"spark":[1065.08,1065.11,1097.39,1074.89,1063.96,1045.56,1088.0,1035.84,1029.0,989.04,953.19,914.13,931.24,878.84,904.9,896.07,913.67,856.49,877.55,903.7],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094749.1118808,"fetched_utc":"2026-10-27 09:52 UTC"},"VRT":{"last_bar_date":"2026-10-26","last_close":199.77999877929688,"currency":"USD","ret_1d_pct":2.809793767642388,"ret_5d_pct":-3.0570666710895034,"volume_last":5515000,"volume_avg_20d":5546990.0,"volume_ratio":0.9942329082980139,"spark":[248.34,241.31,246.12,252.18,253.62,253.14,246.49,243.73,242.78,239.36,237.29,222.83,214.75,206.42,206.08,203.56,212.15,195.59,194.32,199.78],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094749.4952378,"fetched_utc":"2026-10-27 09:52 UTC"},"CEG":{"last_bar_date":"2026-10-26","last_close":252.47999572753906,"currency":"USD","ret_1d_pct":-0.3827189711512302,"ret_5d_pct":-4.069306058178079,"volume_last":2877900,"volume_avg_20d":4242650.0,"volume_ratio":0.6783260462211118,"spark":[264.58,254.02,258.92,257.49,267.62,300.4,299.59,285.07,298.07,293.89,295.79,279.54,275.0,271.37,263.19,258.84,270.74,255.21,253.45,252.48],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094749.900719,"fetched_utc":"2026-10-27 09:52 UTC"},"VST":{"last_bar_date":"2026-10-26","last_close":141.72999572753906,"currency":"USD","ret_1d_pct":1.1201427114789109,"ret_5d_pct":-5.3239822198918985,"volume_last":4299400,"volume_avg_20d":7884470.0,"volume_ratio":0.5452998108940741,"spark":[140.83,138.35,139.75,140.02,144.89,160.5,166.72,156.14,161.48,158.13,162.36,151.79,154.17,152.02,149.7,150.32,156.14,140.83,140.16,141.73],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094750.2981353,"fetched_utc":"2026-10-27 09:52 UTC"},"NEE":{"last_bar_date":"2026-10-26","last_close":82.04000091552734,"currency":"USD","ret_1d_pct":-0.0730786354553481,"ret_5d_pct":4.950751998507119,"volume_last":8947700,"volume_avg_20d":12711025.0,"volume_ratio":0.7039322163240179,"spark":[75.89,75.74,76.35,76.83,76.28,77.88,77.06,77.37,77.38,78.51,78.22,78.37,78.96,79.8,78.17,78.86,78.28,81.9,82.1,82.04],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094750.7209458,"fetched_utc":"2026-10-27 09:52 UTC"},"EQIX":{"last_bar_date":"2026-10-26","last_close":967.6500244140625,"currency":"USD","ret_1d_pct":1.3214239060607147,"ret_5d_pct":-0.8260648529876069,"volume_last":715700,"volume_avg_20d":499280.0,"volume_ratio":1.433464188431341,"spark":[1015.27,1011.58,1012.33,1025.72,1023.44,1047.36,1031.77,1011.16,1026.06,1032.6,1019.4,995.9,996.26,985.98,975.71,987.44,995.0,952.62,955.03,967.65],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094751.112467,"fetched_utc":"2026-10-27 09:52 UTC"},"DLR":{"last_bar_date":"2026-10-26","last_close":174.52999877929688,"currency":"USD","ret_1d_pct":1.2531204521070372,"ret_5d_pct":0.8843923579750612,"volume_last":2820000,"volume_avg_20d":1825010.0,"volume_ratio":1.545197012619109,"spark":[176.56,175.53,176.49,178.55,179.87,184.65,180.47,176.07,178.76,180.16,178.14,172.09,174.47,175.97,173.0,175.31,176.31,170.94,172.37,174.53],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094751.5197778,"fetched_utc":"2026-10-27 09:52 UTC"},"XOM":{"last_bar_date":"2026-10-26","last_close":184.5399932861328,"currency":"USD","ret_1d_pct":0.7259355512948318,"ret_5d_pct":3.51132743420397,"volume_last":10893300,"volume_avg_20d":11399010.0,"volume_ratio":0.9556356209881385,"spark":[161.35,162.75,163.82,164.01,164.0,164.48,164.05,168.5,168.94,172.15,174.08,177.01,174.68,178.98,178.28,177.86,178.09,178.23,183.21,184.54],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094751.9513054,"fetched_utc":"2026-10-27 09:52 UTC"},"T":{"last_bar_date":"2026-10-26","last_close":20.850000381469727,"currency":"USD","ret_1d_pct":-0.38222609909026595,"ret_5d_pct":-10.129311655987983,"volume_last":59360800,"volume_avg_20d":51644040.0,"volume_ratio":1.1494220823932442,"spark":[24.48,24.4,24.3,24.3,24.24,24.43,24.47,24.87,22.18,22.49,22.85,23.05,23.5,23.44,23.2,23.42,21.91,22.74,20.93,20.85],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094752.359853,"fetched_utc":"2026-10-27 09:52 UTC"},"CRM":{"last_bar_date":"2026-10-26","last_close":247.61000061035156,"currency":"USD","ret_1d_pct":-0.38621180576102754,"ret_5d_pct":2.1282754081497934,"volume_last":5690100,"volume_avg_20d":7980540.0,"volume_ratio":0.7129968648738055,"spark":[225.31,229.57,236.69,234.69,229.79,224.99,224.56,227.8,229.13,233.92,238.01,235.95,246.74,240.7,242.45,242.43,241.78,250.29,248.57,247.61],"source":"Yahoo Finance chart API (free, unofficial), daily bars, delayed; not a live quote","fetched_epoch":1793094752.7486122,"fetched_utc":"2026-10-27 09:52 UTC"}},"disclosures":{"MSFT":{"filing":{"form":"10-K","accession":"0001193125-26-323660","filed":"2026-07-29","period":"2026-06-30","url":"https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm"},"customer_concentration":{"status":"disclosed","summary":"No sales to an individual customer accounted for more than 10% of revenue in FY2026, FY2025 or FY2024.","section":"Item 8, Note 18 - Segment Information and Geographic Data"},"power_and_data_centre_commitments":[{"item":"Purchase commitments (primarily datacenters; open purchase orders and take-or-pay contracts)","usd_bn":194.06,"section":"Item 7 MD&A, Material Cash Requirements (contractual obligations table, note d)"},{"item":"Construction commitments","usd_bn":34.566,"section":"Item 7 MD&A, Material Cash Requirements"},{"item":"Leases not yet commenced (primarily datacenters); commence FY2027-FY2033","usd_bn":329.1,"section":"Item 8, Note 13 - Leases","as_of":"2026-06-30","comparability":"discounting not stated in the sentence reviewed"}],"other":[{"item":"Commercial remaining performance obligation (increase of 84% to $678bn is stated for fiscal 2026 in the MD&A highlights)","usd_bn":678,"section":"Item 7 MD&A, fiscal year 2026 highlights"}],"not_disclosed":["Separate power-purchase or energy commitment figure"]},"GOOGL":{"filing":{"form":"10-Q","accession":"0001652044-26-000071","filed":"2026-07-23","period":"2026-06-30","url":"https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm"},"customer_concentration":{"status":"not disclosed in the 10-Q reviewed","summary":"No customer-concentration statement found in the Q2 2026 10-Q text. Revenue backlog (RPO) of $519.5bn is disclosed, of which $513.9bn Google Cloud.","section":"Note 2 - Revenues (Revenue Backlog)"},"power_and_data_centre_commitments":[{"item":"Fixed or guaranteed contractual commitments >1 year (significant majority long-term supply agreements; also includes energy service agreements with take-or-pay terms, obligations through 2054). Energy portion not separated.","usd_bn":707.0,"section":"Note 10 - Commitments and Contingencies"},{"item":"Data-centre leases not yet commenced (2026-2031)","usd_bn":85.2,"section":"Note 4 - Leases","as_of":"2026-06-30","comparability":"undiscounted"},{"item":"Short-term lease commitment commencing Q3 2026","usd_bn":5.8,"section":"Note 4 - Leases"},{"item":"Financial guarantees (backstops for counterparties' long-lead equipment for power purchase and energy agreements), maximum","usd_bn":7.6,"section":"Note 10 - Commitments and Contingencies"}],"other":[{"item":"Revenue backlog (remaining performance obligations)","usd_bn":519.5,"section":"Note 2 - Revenues"}],"not_disclosed":["Customer concentration (not stated in this 10-Q)","Separate energy-commitment figure"]},"AMZN":{"filing":{"form":"10-Q","accession":"0001018724-26-000026","filed":"2026-07-31","period":"2026-06-30","url":"https://www.sec.gov/Archives/edgar/data/1018724/000101872426000026/amzn-20260630.htm"},"customer_concentration":{"status":"not disclosed in the 10-Q reviewed","summary":"No customer-concentration statement found. Unrecognised customer-contract commitments (contracts >1 year) were approximately $496bn, weighted-average remaining life 6.4 years. The filing also names expanded multi-year commitments: OpenAI +$100.0bn over 8.0 years (on top of an existing $38.0bn) and Anthropic more than $100.0bn over 10.0 years.","section":"Item 1, Note 1 - Accounting Policies and Supplemental Disclosures (unearned revenue / performance obligations)"},"power_and_data_centre_commitments":[{"item":"Unconditional purchase obligations (long-term agreements for energy, digital media content, property and equipment, software). Energy portion not separated.","usd_bn":130.065,"section":"Item 1, Note 4 - Commitments and Contingencies"},{"item":"Leases not yet commenced","usd_bn":137.214,"section":"Item 1, Note 4 - Commitments and Contingencies","as_of":"2026-06-30","comparability":"undiscounted"},{"item":"Financing obligations incl. interest (fulfilment network and data-centre facilities)","usd_bn":11.07,"section":"Item 1, Note 4 - Commitments and Contingencies"}],"other":[{"item":"Unrecognised customer-contract commitments (>1 year terms)","usd_bn":496,"section":"Item 1, Note 1"}],"not_disclosed":["Customer concentration (not stated in this 10-Q)","Separate energy-commitment figure"]},"META":{"filing":{"form":"10-Q","accession":"0001628280-26-066773","filed":"2026-10-22","period":"2026-09-30","url":"https://www.sec.gov/Archives/edgar/data/1326801/000162828026066773/meta-20260930.htm"},"customer_concentration":{"status":"not disclosed in the 10-Q reviewed","summary":"No customer-concentration statement found in the Q3 2026 10-Q text.","section":"n/a"},"power_and_data_centre_commitments":[{"item":"Non-cancellable contractual commitments (mostly third-party cloud capacity, servers and network, energy service agreements for data centres, Reality Labs hardware); about $45.85bn due 2026 and $121.41bn due 2027. Energy portion not separated.","usd_bn":454.52,"section":"Note 10 - Commitments and Contingencies"},{"item":"Leases not yet commenced (data centres, energy-related infrastructure, colocations, network); 2026-2036","usd_bn":355.73,"section":"Note 10 - Commitments and Contingencies","as_of":"2026-09-30","comparability":"discounting not stated in the sentence reviewed"},{"item":"Contingent obligation to purchase cloud capacity over five years (may be reduced)","usd_bn":14.72,"section":"Note 10 - Commitments and Contingencies"}],"other":[{"item":"Q3 2026 (three months to 30 Sep 2026) costs and expenses were $51.61bn including a $9.89bn charge related to the August 2026 multistate attorneys general agreement ($11.89bn in the nine months). The charge is not the full payout: the filing states about $12.7bn is payable to states over 10 years, plus $5.3bn of contingent amounts for which no liability is recognised. The charge is the stated driver of the Q3 operating-income drop, so the margin_trend result is charge-affected.","usd_bn":9.89,"section":"Item 2 MD&A, Q3 2026 results","as_of":"2026-09-30"}],"not_disclosed":["Customer concentration (not stated in this 10-Q)","Separate energy-commitment figure"]},"ORCL":{"filing":{"form":"10-Q","accession":"0001193125-26-389274","filed":"2026-09-11","period":"2026-08-31","url":"https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm"},"customer_concentration":{"status":"not disclosed in the 10-Q reviewed","summary":"No customer-concentration statement found. Remaining performance obligations were $664bn at 31 Aug 2026 versus $455bn a year earlier, 'primarily attributable to certain significant cloud contracts'. Counterparties not named.","section":"Item 2 MD&A, Remaining Performance Obligations from Contracts with Customers"},"power_and_data_centre_commitments":[{"item":"Unconditional purchase and other obligations >=1 year (primarily long-term supply arrangements for cloud-infrastructure components and power supply arrangements for data centres)","usd_bn":34.15,"section":"Item 1, Note 6 - Leases and Other Commitments (Unconditional Obligations)"},{"item":"Additional lease commitments not yet on balance sheet (Oracle's wording; same economic item as 'leases not yet commenced' elsewhere); substantially all data-centre; commence Q2 FY2027 to FY2029, terms 15-19 years","usd_bn":288,"section":"Item 1, Note 6 - Leases and Other Commitments","as_of":"2026-08-31","comparability":"discounting not stated in the sentence reviewed"}],"other":[{"item":"Remaining performance obligations","usd_bn":664,"section":"Item 2 MD&A"}],"not_disclosed":["Customer concentration (not stated in this 10-Q)","Debt issuance for Q1 FY2027: none reported in the cash-flow statement (no debt-proceeds line; $4.2bn of borrowing repayments and $19.9bn of ATM equity raised). Earlier Oracle quarters in the trailing twelve months were not checked, so TTM debt reliance stays n/a"]},"CRWV":{"filing":{"form":"10-Q","accession":"0001769628-26-000366","filed":"2026-08-12","period":"2026-06-30","url":"https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm"},"customer_concentration":{"status":"disclosed","summary":"Q2 2026 revenue: Customer A 36%, Customer B 26%, Customer C 10% (top three = 72%); six months: A 40%, B 23%. Q2 2025 top customer 71%. Customers A and B each 32% of accounts receivable at 30 Jun 2026. Customers are anonymised in the filing. Risk factors name OpenAI (order form up to approximately $6.5bn through May 2031) and Meta (committed up to approximately $21.0bn, capacity through Dec 2032).","section":"Item 1, Note 2 - Revenue (Significant Customers); Item 1A Risk Factors"},"power_and_data_centre_commitments":[{"item":"Leases not yet commenced (primarily data centres, equipment and office buildings); commence 2026-2029, terms 7-16 years. A floor, not a total: excludes arrangements with significant uncertainty in the payment amounts","usd_bn":35.5,"section":"Item 1, Note 8 - Leases (Leases Not Yet Commenced)","as_of":"2026-06-30","note":"floor: excludes uncertain-amount arrangements","comparability":"undiscounted"}],"other":[{"item":"Remaining performance obligations; 41% expected within 24 months","usd_bn":103.7,"section":"Item 1, Note 2 - Revenue (RPO)"}],"not_disclosed":["Separate power-purchase commitment figure (power swaps and power purchase agreements appear only as fair-valued derivatives, not as a commitment total)"]}}};
// ── state, cache, refresh (request-triggered, single-flight) ─────────────────────────────────────────────────────────────────────────
var bb11Now = function () { return Date.now(); };                       // injectable clock (tests)
// bb11b: MARKET ADAPTER (part 2/2). Swap the market source HERE (and the parser in part 1/2 above): nothing else in the monitor knows the URL,
// host, headers or response shape of the source. In: one symbol + now (ms). Out: a normalized market entry
// {last_bar_date,last_close,currency,ret_1d_pct,ret_5d_pct,volume_last,volume_avg_20d,volume_ratio,spark}; throws on any failure.
// The caller (bb11PullMarket) owns the cap (<= BB11_CAP), concurrency, withTimeout and the source/fetched stamps.
var bb11Chart = function (sym) { return fetchYahooChart(sym.replace(/\./g, "-"), "3mo", "1d"); };   // existing Yahoo helper (30 s cache, 512 KB cap, degraded flag)
var BB11B_MARKET_NAME = "Yahoo Finance";
async function bb11bMarketAdapter(sym, nowMs) {
  var r = await bb11Chart(sym);
  if (!r || r.unavailable || !r.data) throw new Error("chart unavailable");
  return bb11ParseYahoo(r.data, nowMs / 1000);
}
function bb11bLabel(fetchedUtc) { return fetchedUtc ? "Market data delayed, source " + BB11B_MARKET_NAME + ", as of " + fetchedUtc : "Market data unavailable, source " + BB11B_MARKET_NAME + " (no reading yet)"; }
// bb11b: END MARKET ADAPTER
var bb11SecGet = async function (url, ua, ims, timeoutMs, maxBytes) {  // the ONLY new network call: SEC, on demand, UA from DISPATCH_SEC_UA, shared SEC limiter
  if (!secRateLimiter.allow("sec")) throw new Error("SEC rate limit reached");
  var h = { "User-Agent": ua, Accept: "application/json" };
  if (ims) h["If-Modified-Since"] = ims;
  var resp = await withTimeout(fetch(url, { headers: h, redirect: "error", signal: AbortSignal.timeout(timeoutMs) }), timeoutMs, "SEC request timed out");
  if (resp.status === 304) return { status: 304 };
  if (!resp.ok) throw new Error("SEC HTTP " + resp.status);
  var text = await withTimeout(readTextCapped(resp, maxBytes), timeoutMs, "SEC read timed out");
  return { status: 200, text: text, lastModified: resp.headers.get("last-modified") || null };
};
var bb11Rl = new FixedWindowRateLimiter({ limit: 120, windowMs: 60000, maxKeys: 1024 });   // bb12b: per client 120/min (was 240)
var bb12bGlobalRl = new FixedWindowRateLimiter({ limit: 2000, windowMs: 60000, maxKeys: 4 });   // bb12b: backstop for all monitor routes together, 2000/min; same fixed-window mechanism, no timers
function bb12bOctets(s) { var o = s.split("."); return o.length === 4 && o.every(function (x) { return /^\d{1,3}$/.test(x) && +x <= 255; }) ? o.map(Number) : null; }
function bb12bIp(raw) {                                                   // bb12b: one address -> normalised key text (no port/brackets/zone, v4-mapped v6 -> v4, v6 -> 8 lowercase groups), or null if it does not look like an IP
  var s = String(raw == null ? "" : raw).trim().toLowerCase(), m, o;
  if (!s || s.length > 64) return null;
  if ((m = /^\[([^\]]+)\](?::\d{1,5})?$/.exec(s))) s = m[1];
  else if (/^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$/.test(s)) s = s.slice(0, s.lastIndexOf(":"));
  if (s.indexOf("%") > 0) s = s.slice(0, s.indexOf("%"));
  if ((m = /^::ffff:(\d{1,3}(?:\.\d{1,3}){3})$/.exec(s))) s = m[1];
  if (s.indexOf(":") < 0) { o = bb12bOctets(s); return o ? o.join(".") : null; }
  if (!/^[0-9a-f:.]+$/.test(s) || s.indexOf(":::") >= 0 || s.split("::").length > 2) return null;
  if ((m = /(\d{1,3}(?:\.\d{1,3}){3})$/.exec(s))) { o = bb12bOctets(m[1]); if (!o) return null; s = s.slice(0, s.length - m[1].length) + ((o[0] << 8) | o[1]).toString(16) + ":" + ((o[2] << 8) | o[3]).toString(16); }
  var parts = s.split("::"), a = parts[0] ? parts[0].split(":") : [], b = parts.length > 1 && parts[1] ? parts[1].split(":") : [], all = a.concat(b);
  if (!all.every(function (h) { return /^[0-9a-f]{1,4}$/.test(h); })) return null;
  if (parts.length === 1 ? all.length !== 8 : all.length > 7) return null;
  while (a.length + b.length < 8) a.push("0");
  return a.concat(b).map(function (h) { return h.replace(/^0+(?=.)/, ""); }).join(":");
}
function bb12bClientKey(req) {                                            // bb12b: rate-limit key for the monitor routes. Never the client-set first X-Forwarded-For entry.
  var h = (req && req.headers) || {}, k = bb12bIp(h["cf-connecting-ip"]);  // 1) cf-connecting-ip, when it looks like an IP
  if (k) return k;
  var xf = String(h["x-forwarded-for"] || "").slice(-2048).split(",").map(function (x) { return x.trim(); }).filter(Boolean);
  if (xf.length) { k = bb12bIp(xf.length >= 2 ? xf[xf.length - 2] : xf[0]); if (k) return k; }   // 2) entry before the last (Google frontend appends client, then its own hop); 3) the only entry
  return bb12bIp(req && req.socket && req.socket.remoteAddress) || "unknown";   // 4) socket address
}
function bb12bSeedPull(seed) {                                            // bb12b: the embedded seed already is a market pull of its own UK day (fetched 2026-10-27 09:52 UTC), so a cold start on that UK day does not pull again; later UK days pull once as designed
  var eps = BB11_TICKERS.map(function (t) { var m = seed.market[t]; return m && !("error" in m) && bb11Num(m.fetched_epoch) ? m.fetched_epoch : null; }).filter(function (x) { return x !== null; });
  if (!eps.length) return { uk_day: null, at: null, ok: null, fetched: 0, failed: 0 };
  var at = Math.max.apply(null, eps) * 1000;
  return { uk_day: bb11UkDay(at), at: new Date(at).toISOString(), ok: true, fetched: eps.length, failed: BB11_TICKERS.length - eps.length, seed: true };
}
var bb11DayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" });
function bb11UkDay(ms) { var o = {}; bb11DayFmt.formatToParts(new Date(ms)).forEach(function (p) { o[p.type] = p.value; }); return o.year + "-" + o.month + "-" + o.day; }
function bb11Utc(ms) { return new Date(ms).toISOString().slice(0, 16).replace("T", " ") + " UTC"; }
var bb11St = null, bb11LoadP = null, bb11Inflight = null;
function bb11Init() {
  var seed = BB11_SEED, st = { v: 1, rev: 1, live: false, companies: {}, market: {}, pull: bb12bSeedPull(seed), sec: { day: null, facts_today: 0, checked: {}, new_filings: [], errors: [] }, persist: { ok: null, error: null, saved_at: null }, view: null, viewKey: null, bodies: new Map(), perr: null };
  BB11_TICKERS.forEach(function (t) { st.companies[t] = seed.companies[t]; st.market[t] = seed.market[t]; });
  return st;
}
function bb11Num(x) { return typeof x === "number" && isFinite(x); }
function bb11GoodMarket(m) {
  if (!m || typeof m !== "object") return false;
  if ("error" in m) return typeof m.error === "string" && bb11Num(m.fetched_epoch);
  return bb11Num(m.last_close) && bb11Num(m.ret_5d_pct) && bb11Num(m.ret_1d_pct) && bb11Num(m.volume_ratio) && bb11Num(m.fetched_epoch) && typeof m.last_bar_date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(m.last_bar_date) && Array.isArray(m.spark) && m.spark.every(bb11Num);
}
function bb11GoodBase(c, seedC) {
  try {
    return c && c.ticker === seedC.ticker && c.cik === seedC.cik && Array.isArray(c.rows) && c.rows.length >= 1 && c.rows.length <= 2 && /^\d{4}-\d{2}-\d{2}$/.test(c.rows[0].period_end) && c.rows[0].period_end >= seedC.rows[0].period_end && c.tags && typeof c.tags === "object" && typeof c.company === "string" && typeof c.group === "string" && (c.commits === undefined || typeof c.commits === "object");
  } catch (e) { return false; }
}
function bb11Merge(st, j) {                                              // adopt only well-formed, not-older data from the disk file; anything odd is ignored
  if (!j || j.v !== 1) return;
  BB11_TICKERS.forEach(function (t) {
    var c = j.companies && j.companies[t]; if (bb11GoodBase(c, BB11_SEED.companies[t])) st.companies[t] = c;
    var m = j.market && j.market[t]; if (bb11GoodMarket(m) && m.fetched_epoch >= (st.market[t].fetched_epoch || 0)) st.market[t] = m;
  });
  if (j.pull && typeof j.pull === "object" && (j.pull.uk_day === null || /^\d{4}-\d{2}-\d{2}$/.test(String(j.pull.uk_day)))) st.pull = { uk_day: j.pull.uk_day || null, at: typeof j.pull.at === "string" ? j.pull.at : null, ok: j.pull.ok === true ? true : (j.pull.ok === false ? false : null), fetched: bb11Num(j.pull.fetched) ? j.pull.fetched : 0, failed: bb11Num(j.pull.failed) ? j.pull.failed : 0 };
  if (j.pull && st.pull && j.pull.seed === true && st.pull.uk_day === j.pull.uk_day && st.pull.ok === true && j.pull.at === bb12bSeedPull(BB11_SEED).at) st.pull.seed = true;   // bb12b: a persisted seed marker survives a restore
  var s = j.sec;
  if (s && typeof s === "object") {
    st.sec.day = typeof s.day === "string" ? s.day : null; st.sec.facts_today = bb11Num(s.facts_today) ? s.facts_today : 0;
    if (s.checked && typeof s.checked === "object") BB11_TICKERS.forEach(function (t) { var c = s.checked[t]; if (c && typeof c === "object") st.sec.checked[t] = { day: String(c.day || ""), last_modified: typeof c.last_modified === "string" ? c.last_modified : null, latest_accn: typeof c.latest_accn === "string" ? c.latest_accn : null, form: typeof c.form === "string" ? c.form : null, filed: typeof c.filed === "string" ? c.filed : null, status: String(c.status || "").slice(0, 40) }; });
    if (Array.isArray(s.new_filings)) st.sec.new_filings = s.new_filings.slice(-20).filter(function (x) { return x && typeof x.ticker === "string" && typeof x.accn === "string"; }).map(function (x) { return { ticker: x.ticker, accn: x.accn, form: String(x.form || ""), detected_utc: String(x.detected_utc || ""), applied: x.applied === true }; });
  }
  st.live = j.live === true;
}
function bb11Ensure() {                                                  // first request only; a missing / unreadable / corrupt file just means "seed"
  if (!bb11LoadP) bb11LoadP = (async function () {
    var st = bb11Init();
    try {
      var fsp = require("fs").promises, stt = await fsp.stat(BB11_FILE);
      if (stt.size > 0 && stt.size <= 8 * 1024 * 1024) bb11Merge(st, JSON.parse(await fsp.readFile(BB11_FILE, "utf8")));
    } catch (e) { /* no file: seed */ }
    bb11St = st; return st;
  })();
  return bb11LoadP;
}
async function bb11Persist(st) {                                         // best effort, never throws
  try {
    var fsp = require("fs").promises, tmp = BB11_FILE + "." + process.pid + ".tmp";
    var snap = { v: 1, saved_at: new Date(bb11Now()).toISOString(), live: st.live, companies: st.companies, market: st.market, pull: st.pull, sec: { day: st.sec.day, facts_today: st.sec.facts_today, checked: st.sec.checked, new_filings: st.sec.new_filings } };
    await fsp.writeFile(tmp, JSON.stringify(snap)); await fsp.rename(tmp, BB11_FILE);
    st.persist = { ok: true, error: null, saved_at: snap.saved_at };
  } catch (e) { st.persist = { ok: false, error: String((e && e.code) || "write failed"), saved_at: st.persist.saved_at }; }
}
function bb11Touch(st) { st.rev++; st.view = null; st.bodies = new Map(); }
function bb11Ua() { var u = process.env.DISPATCH_SEC_UA; return (typeof u === "string" && u.trim().length >= 5) ? u.trim() : null; }   // read at call time, never hardcoded
function bb11SecEnabled() { var ua = bb11Ua(); return ua ? { enabled: true } : { enabled: false, reason: "DISPATCH_SEC_UA not set" }; }
function bb11MarketDue(st, now) { return st.pull.uk_day !== bb11UkDay(now); }
function bb11SecDue(st, now) {
  if (!bb11Ua()) return false;
  var day = bb11UkDay(now);
  return BB11_TICKERS.some(function (t) { var c = st.sec.checked[t]; return !c || c.day !== day; });
}
async function bb11PullMarket(st, now) {                                 // ONE batched pull per UK day, <= BB11_CAP instruments, each fetch under withTimeout
  var day = bb11UkDay(now), syms = BB11_TICKERS.slice(0, BB11_CAP), fetched = 0, failed = 0;
  st.pull = { uk_day: day, at: new Date(now).toISOString(), ok: null, fetched: 0, failed: 0 };   // the attempt counts for the day even if it fails
  async function one(sym) {
    try {
      var e = await withTimeout(bb11bMarketAdapter(sym, bb11Now()), BB11_FETCH_MS, "market fetch timed out");
      if (!bb11Num(e.last_close) || !bb11Num(e.ret_5d_pct) || !bb11Num(e.volume_ratio) || !bb11Num(e.ret_1d_pct)) throw new Error("non-finite market figure");
      e.source = BB11_MARKET_SOURCE; e.fetched_epoch = bb11Now() / 1000; e.fetched_utc = bb11Utc(bb11Now());
      st.market[sym] = e; fetched++;
    } catch (err) {
      failed++;
      var prev = st.market[sym], msg = String((err && err.message) || err).slice(0, 120);
      if (prev && !("error" in prev)) st.market[sym] = Object.assign({}, prev, { pull_error: msg, pull_error_uk_day: day });   // keep the last good reading, flagged
      else st.market[sym] = { error: msg, source: BB11_MARKET_SOURCE, fetched_epoch: bb11Now() / 1000, fetched_utc: bb11Utc(bb11Now()) };
    }
  }
  for (var i = 0; i < syms.length; i += BB11_CONCURRENCY) await Promise.all(syms.slice(i, i + BB11_CONCURRENCY).map(one));
  st.pull = { uk_day: day, at: st.pull.at, ok: fetched > 0, fetched: fetched, failed: failed };
  if (fetched > 0) st.live = true;
}
function bb11PickLatest(text) {                                          // newest 10-Q/10-K in a submissions document
  var j = JSON.parse(text), rec = j.filings.recent, i;
  for (i = 0; i < rec.form.length; i++) if (rec.form[i] === "10-Q" || rec.form[i] === "10-K") return { accn: rec.accessionNumber[i], form: rec.form[i], filed: rec.filingDate[i] };
  return null;
}
async function bb11SecCheck(st, now) {                                   // only when DISPATCH_SEC_UA is set; per filer <= 1 submissions check per UK day; facts only on a NEW accession
  var ua = bb11Ua(); if (!ua) return;
  var day = bb11UkDay(now), sec = st.sec;
  if (sec.day !== day) { sec.day = day; sec.facts_today = 0; }
  var cik10 = function (c) { return ("0000000000" + c).slice(-10); };
  for (var k = 0; k < BB11_TICKERS.length; k++) {
    var t = BB11_TICKERS[k], base = st.companies[t], chk = sec.checked[t];
    try {
      if (!chk || chk.day !== day) {
        var r = await bb11SecGet("https://data.sec.gov/submissions/CIK" + cik10(base.cik) + ".json", ua, chk && chk.last_modified, BB11_SEC_MS, 8 * 1024 * 1024);
        if (r.status === 304) chk = Object.assign({}, chk, { day: day, status: "not_modified" });
        else { var lt = bb11PickLatest(r.text); chk = { day: day, last_modified: r.lastModified, latest_accn: lt ? lt.accn : null, form: lt ? lt.form : null, filed: lt ? lt.filed : null, status: "checked" }; }
        sec.checked[t] = chk;
      }
      var isNew = chk.latest_accn && chk.latest_accn !== base.accn;
      if (isNew && sec.facts_today < BB11_MAX_FACTS_PER_DAY && chk.facts_day !== day) {
        sec.facts_today++; chk.facts_day = day;
        if (!sec.new_filings.some(function (x) { return x.accn === chk.latest_accn; })) sec.new_filings.push({ ticker: t, accn: chk.latest_accn, form: chk.form || "", detected_utc: bb11Utc(bb11Now()), applied: false });
        var f = await bb11SecGet("https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik10(base.cik) + ".json", ua, null, BB11_FACTS_MS, BB11_FACTS_MAX_BYTES);
        var res = bb11FromFacts({ ticker: t, cik: base.cik, company: base.company }, JSON.parse(f.text));
        if (res.ok && res.base.accn && res.base.accn !== base.accn && res.base.rows[0].period_end >= base.rows[0].period_end) {
          st.companies[t] = res.base; st.live = true; chk.status = "refreshed";
          sec.new_filings.forEach(function (x) { if (x.accn === chk.latest_accn || x.accn === res.base.accn) x.applied = true; });
        } else chk.status = res.ok ? "facts_not_yet_updated" : String(res.status);
      }
    } catch (e) {
      sec.errors.push({ ticker: t, at: bb11Utc(bb11Now()), error: String((e && e.message) || e).slice(0, 100) }); if (sec.errors.length > 10) sec.errors.shift();
      if (!sec.checked[t]) sec.checked[t] = { day: day, last_modified: null, latest_accn: null, form: null, filed: null, status: "error" }; else sec.checked[t].day = day;
    }
    bb11Touch(st);
  }
}
function bb11Refresh(st) {                                               // single-flight: concurrent requests share one run; started by a request, never by a timer
  if (bb11Inflight) return bb11Inflight;
  var now = bb11Now(), doMarket = bb11MarketDue(st, now), doSec = bb11SecDue(st, now);
  if (!doMarket && !doSec) return null;
  st.rev++; st.view = null; st.bodies = new Map();
  var p = (async function () {
    try { if (doMarket) await bb11PullMarket(st, now); } catch (e) { st.perr = String((e && e.message) || e).slice(0, 100); }
    try { if (doSec) await bb11SecCheck(st, now); } catch (e) { st.perr = String((e && e.message) || e).slice(0, 100); }
    await bb11Persist(st);
  })().then(function () { }, function () { }).then(function () { bb11Inflight = null; bb11Touch(st); });
  bb11Inflight = p; return p;
}
// ── views ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
function bb11MarketView(md, now) {
  if (!md || "error" in md) return { status: "unavailable", detail: (md && md.error) || "not fetched", source: BB11_MARKET_SOURCE, label: bb11bLabel(null), as_of: null, stale: true };
  var stale = bb11UkDay(md.fetched_epoch * 1000) !== bb11UkDay(now);
  return { status: "ok", source: md.source || BB11_MARKET_SOURCE, label: bb11bLabel(md.fetched_utc), as_of: md.last_bar_date, fetched_utc: md.fetched_utc, stale: stale, pull_error: md.pull_error || null, currency: md.currency, last_close: md.last_close, ret_1d_pct: md.ret_1d_pct, ret_5d_pct: md.ret_5d_pct, volume_last: md.volume_last, volume_avg_20d: md.volume_avg_20d, volume_ratio: md.volume_ratio, spark: md.spark };
}
function bb11Row(d, now) {
  var f = d.flags, base = bb11St.companies[d.ticker], prev = d.previous_quarter_flags;
  var mv = bb11MarketView(d.market && d.market.status === "market data unavailable" ? { error: d.market.detail } : d.market, now);
  return {
    rank: d.rank, ticker: d.ticker, company: d.company, group: d.group,
    radar_score: d.radar_score, filing_only_score: d.filing_only_score, scoreable: d.scoreable,
    attention: d.attention, tag: d.hype_vs_fundamentals_tag, reasons: d.reasons,
    filing_flag: { overall: f.overall, flags: { sustainability_gap: f.sustainability_gap, fcf_coverage: f.fcf_coverage, debt_reliance: f.debt_reliance, interest_burden: f.interest_burden, margin_trend: f.margin_trend }, previous_overall: prev ? prev.overall : null, turned_worse: d.filing_score.worse, turned_better: d.filing_score.better },
    filing: { status: d.status, message: d.message || null, latest_period_end: d.latest_period_end, latest_filed: d.latest_filed, filing_age_days: d.filing_age_days, latest_accession: base.accn || null, form: base.form || null, source: BB11_SEC_SOURCE, source_api: d.source_api, as_of: d.latest_period_end },
    market: mv,
    market_score: d.market_score ? { score: d.market_score.score, volume_pts: d.market_score.volume_pts, price_pts: d.market_score.price_pts } : null,
    filing_score: { score: d.filing_score.score, parts: d.filing_score.parts, flag_points: d.filing_score.flag_points, capex_accel_pp: d.filing_score.capex_accel_pp, debt_issued_latest_q: d.filing_score.debt_issued_latest_q }
  };
}
function bb11Detail(d, row) {
  return Object.assign({}, row, { cik: d.cik, metrics: d.metrics, tags: d.tags, not_disclosed_or_na: d.not_disclosed_or_na, changes_since_last_quarter: d.changes_since_last_quarter, previous_quarter_flags: d.previous_quarter_flags, ttm: d.ttm, ttm_prior: d.ttm_prior, latest_quarter: d.latest_quarter, xbrl_commitments: d.xbrl_commitments, source_filings: d.source_filings, disclosures: d.disclosures });
}
function bb11Meta(st, now) {
  var ms = BB11_TICKERS.map(function (t) { return st.market[t]; }).filter(function (m) { return m && !("error" in m); });
  var eps = ms.map(function (m) { return m.fetched_epoch; }), bars = ms.map(function (m) { return m.last_bar_date; }).sort();
  var today = bb11UkDay(now), stale = !ms.length || ms.some(function (m) { return bb11UkDay(m.fetched_epoch * 1000) !== today; });
  var flings = BB11_TICKERS.map(function (t) { return st.companies[t].rows[0].period_end; }).sort();
  var sec = bb11SecEnabled(); if (sec.enabled) { sec.checked_today = BB11_TICKERS.filter(function (t) { var c = st.sec.checked[t]; return c && c.day === today; }).length; sec.new_filings = st.sec.new_filings.slice(-5); sec.last_errors = st.sec.errors.slice(-3); }
  return {
    served_from: st.live ? "live-cache" : "seed", stale: stale,
    as_of: {
      market: { source: BB11_MARKET_SOURCE, label: bb11bLabel(eps.length ? bb11Utc(Math.max.apply(null, eps) * 1000) : null), last_bar_date_min: bars[0] || null, last_bar_date_max: bars[bars.length - 1] || null, fetched_utc_oldest: eps.length ? bb11Utc(Math.min.apply(null, eps) * 1000) : null, fetched_utc_newest: eps.length ? bb11Utc(Math.max.apply(null, eps) * 1000) : null, stale: stale },
      filings: { source: BB11_SEC_SOURCE, latest_period_end_min: flings[0], latest_period_end_max: flings[flings.length - 1], seed_retrieved: BB11_SEED.sec_retrieved }
    },
    refresh: { in_progress: !!bb11Inflight, market_pulls_per_uk_day: 1, market_pull_due: bb11MarketDue(st, now), last_market_pull: { uk_day: st.pull.uk_day, at: st.pull.at, ok: st.pull.ok, fetched: st.pull.fetched, failed: st.pull.failed, seed: st.pull.seed === true }, instrument_cap: BB11_CAP },
    sec: sec, persistence: { ok: st.persist.ok, saved_at: st.persist.saved_at }
  };
}
function bb11Build(st, now) {
  var key = st.rev + "|" + bb11UkDay(now) + "|" + new Date(now).toISOString().slice(0, 10) + "|" + (bb11Inflight ? 1 : 0);
  if (st.view && st.viewKey === key) return st.view;
  var today = new Date(now).toISOString().slice(0, 10), detailBy = {};
  var results = BB11_TICKERS.map(function (t) { var d = bb11Assemble(st.companies[t], BB11_SEED.disclosures, today); bb11AddRadar(d, st.market[t]); return d; });
  var ranked = bb11Rank(results);
  var rows = ranked.map(function (d) { var r = bb11Row(d, now); detailBy[d.ticker] = { d: d, row: r }; return r; });
  st.view = { rows: rows, detailBy: detailBy, meta: bb11Meta(st, now) }; st.viewKey = key; st.bodies = new Map();
  return st.view;
}
function bb11Body(st, kind, now, limit, tkr) {
  var v = bb11Build(st, now), ck = kind + "|" + (tkr || limit), hit = st.bodies.get(ck);
  if (hit) return hit;
  var obj;
  if (kind === "radar") {
    var top = v.rows.slice(0, limit);
    obj = Object.assign({ ok: true, version: BB11_VERSION, title: "Capital Sustainability Monitor", disclaimer: BB11_DISCLAIMER, note: BB11_NOTE, formula: BB11_FORMULA, thresholds: BB11_TH, total: v.rows.length, limit: limit, shown: top.length, ranking: top, not_analysed: [] }, v.meta);
  } else {
    var e = v.detailBy[tkr];
    obj = Object.assign({ ok: true, version: BB11_VERSION, title: "Capital Sustainability Monitor", disclaimer: BB11_DISCLAIMER, note: BB11_NOTE, thresholds: BB11_TH, rank_of: v.rows.length, ticker: tkr, instrument: bb11Detail(e.d, e.row) }, v.meta);
  }
  var body = JSON.stringify(obj), etag = 'W/"bb11-' + require("crypto").createHash("sha1").update(body).digest("hex").slice(0, 20) + '"';
  hit = { body: body, etag: etag, len: Buffer.byteLength(body) }; st.bodies.set(ck, hit);
  return hit;
}
// ── routes ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
function bb11Send(req, res, status, body, extra) {
  var h = Object.assign({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }, SECURITY_HEADERS, extra || {});
  h["Content-Length"] = Buffer.byteLength(body);
  res.writeHead(status, h); res.end(req.method === "HEAD" ? undefined : body);
}
function bb11Err(req, res, status, code, extra) { bb11Send(req, res, status, JSON.stringify(Object.assign({ ok: false, error: code }, extra && extra.body)), extra && extra.headers); }
async function bb11Route(req, res) {
  var raw = String(req.url || "").split(/[?#]/)[0];
  if (raw !== "/api/monitor" && raw.indexOf("/api/monitor/") !== 0) return false;
  var p = raw.length > 1 && raw.charAt(raw.length - 1) === "/" ? raw.slice(0, -1) : raw;
  if (req.method !== "GET" && req.method !== "HEAD") { bb11Err(req, res, 405, "method_not_allowed", { headers: { Allow: "GET, HEAD" } }); return true; }
  if (!bb11Rl.allow(bb12bClientKey(req), bb11Now()) || !bb12bGlobalRl.allow("monitor", bb11Now())) { bb11Err(req, res, 429, "rate_limited", { headers: { "Retry-After": "60" } }); return true; }
  var tkr = null;
  if (p !== "/api/monitor") {
    var seg = p.slice("/api/monitor/".length);
    try { seg = decodeURIComponent(seg); } catch (e) { bb11Err(req, res, 400, "invalid_ticker"); return true; }
    if (seg.indexOf("/") >= 0) { bb11Err(req, res, 404, "not_found"); return true; }
    if (!/^[A-Z0-9.\-]{1,10}$/.test(seg)) { bb11Err(req, res, 400, "invalid_ticker"); return true; }
    tkr = seg;
  }
  var st = bb11St || await bb11Ensure();
  if (tkr !== null && BB11_TICKERS.indexOf(tkr) < 0) { bb11Err(req, res, 404, "unknown_ticker", { body: { ticker: tkr } }); return true; }
  var now = bb11Now(), limit = BB11_LIMIT_DEFAULT;
  if (tkr === null) {
    var q = String(req.url).split("?")[1], lv = q ? new URLSearchParams(q.split("#")[0]).get("limit") : null;
    if (lv !== null && /^\d{1,3}$/.test(lv)) limit = Math.min(BB11_LIMIT_MAX, Math.max(1, parseInt(lv, 10)));
  }
  var rp = bb11Refresh(st);                                              // starts (or joins) a refresh when something is due; never awaited by the request
  var hit = bb11Body(st, tkr === null ? "radar" : "detail", now, limit, tkr);
  if (rp) rp.catch(function () { });
  var h = Object.assign({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "public, max-age=300, stale-while-revalidate=600", ETag: hit.etag, "X-Robots-Tag": "noindex" }, SECURITY_HEADERS);
  if (req.headers["if-none-match"] && String(req.headers["if-none-match"]).split(",").some(function (x) { return x.trim() === hit.etag; })) { delete h["Content-Type"]; res.writeHead(304, h); res.end(); return true; }
  h["Content-Length"] = hit.len;
  res.writeHead(200, h); res.end(req.method === "HEAD" ? undefined : hit.body);
  return true;
}
var bb11Prev = bb10iHandle0;
bb10iHandle0 = async function bb11Handle(req, res) {                     // inside the maintenance wrapper: guests get bb10i's 503 first, the admin cookie passes
  try { if (await bb11Route(req, res)) return; }
  catch (e) { try { if (!res.headersSent) bb11Send(req, res, 503, JSON.stringify({ ok: false, error: "monitor_unavailable" }), { "Retry-After": "30" }); else res.end(); } catch (e2) { } return; }
  return bb11Prev.apply(this, arguments);
};
'''

BB10H = r'''
// ── bb10h: QA fix (chat86) for the stale crypto Ask, the doubled BTC paragraph, the /markets INTEL gold price and the /brief crypto figures.
// Server-only. No secrets, tables, feeds or background timers; the only timer is withTimeout around data the page already reads. ──
// Root cause of the stale answer: bb8q kept the last "move pack" per name (bb8qPackMem) for 24 h and served it, with its original as-of
// time, whenever the new pack missed its 3 s wait. A 08:11 pack was therefore replayed at 14:44. There is no Ask answer cache.
var BB10H_VER = "bb10h";
var BB10H_BUILD = (function () {
  try { return BB10H_VER + "-" + crypto.createHash("sha256").update(fs.readFileSync(__filename)).digest("hex").slice(0, 12); } catch (e) { return BB10H_VER; }
})();
var BB10H_LIVE_TTL_MS = 90 * 1000;
var BB10H_ASOF_MAX_MS = 10 * 60 * 1000;
var BB10H_CTX_WAIT_MS = 2500;
var BB10H_STALE_NOTE = "We do not quote a live crypto price here because the latest data we hold for it is more than 10 minutes old.";
try { BB10_CB_STALE_MS = 2 * 60 * 1000; } catch (e) {}
// every cache key carries the build id
function bb10hKey(kind, id) { return BB10H_BUILD + "|" + kind + "|" + String(id); }

// ── (1a) the move-pack memo: keyed by build, and a pack for an open market is never replayed after the live TTL ──
try {
  var bb10hMemGet = bb8qPackMem.get, bb10hMemSet = bb8qPackMem.set;
  bb8qPackMem.get = function (k) { return bb10hMemGet.call(this, bb10hKey("pack", k)); };
  bb8qPackMem.set = function (k, v) { return bb10hMemSet.call(this, bb10hKey("pack", k), v); };
} catch (e) { console.warn("bb10h pack memo key skipped", e && e.message); }
function bb10hPackStale(r) {
  var q = r && r.q;
  if (!q) return false;
  if (/closed/i.test(String(q.status || "") + " " + String(q.note || ""))) return false;   // a closed market's last session is still the latest
  var at = Number(r.bb8qCachedAt);
  return isFinite(at) && at > 0 && Date.now() - at > BB10H_LIVE_TTL_MS;
}
var bb10hWait0 = bb8eWait;
bb8eWait = async function (st) {
  var r = await bb10hWait0.apply(this, arguments);
  try {
    if (r && r.bb8qCached && bb10hPackStale(r)) {
      st.bb10hDroppedPack = { base: r.base, builtAt: r.bb8qCachedAt };
      st.bb8eMoveR = null; st.bb8qPackCached = false;
      return null;
    }
  } catch (e) {}
  return r;
};

// ── clock helpers (UK wall time in an answer back to epoch ms) ──
var BB10H_MON = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
function bb10hUkParts(ms) {
  var p = {};
  new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = Number(x.value); });
  return p;
}
function bb10hUkToMs(y, mo, d, h, mi) {
  var wall = Date.UTC(y, mo, d, h, mi), g = wall;
  for (var i = 0; i < 2; i++) { var p = bb10hUkParts(g); g = wall - (Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - Math.floor(g / 60000) * 60000); }
  return g;
}
// "Sun 25 Oct, 14:55 UK" or "14:55 UK" -> ms (null when it does not parse)
function bb10hAsOfMs(txt, now) {
  var m = /(?:[A-Z][a-z]{2} (\d{1,2}) ([A-Z][a-z]{2,4}),? )?(\d{2}):(\d{2}) UK/.exec(String(txt || ""));
  if (!m) return null;
  var n = bb10hUkParts(now), ms;
  if (m[1]) {
    var mo = BB10H_MON[String(m[2]).slice(0, 3).toLowerCase()];
    if (mo == null) return null;
    ms = bb10hUkToMs(n.year, mo, Number(m[1]), Number(m[3]), Number(m[4]));
    if (ms > now + 86400000) ms = bb10hUkToMs(n.year - 1, mo, Number(m[1]), Number(m[3]), Number(m[4]));
  } else {
    ms = bb10hUkToMs(n.year, n.month - 1, n.day, Number(m[3]), Number(m[4]));
    if (ms > now + 5 * 60000) ms -= 86400000;
  }
  return ms;
}
var BB10H_ASOF_RE = /\bas of ((?:[A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2,4},? )?\d{2}:\d{2} UK)/g;
var BB10H_CRYPTO_WORD_RE = /\b(?:crypto(?:currenc\w+)?|bitcoin|ether(?:eum)?)\b/i;
var BB10H_CONTRA = [
  /^\s*We don't have the [^.]*?figures this question asks about in our data feed right now[^.]*\.(?:\s*\[\d+\])*\s*$/,
  /^\s*In short: no [^.]*?figures this question asks about in our feed[^.]*\.(?:\s*\[\d+\])*\s*$/
];
var BB10H_PRICE_RE = /\b(?:at|to|is|now|priced at|trading at)\s+\$([\d,]+(?:\.\d+)?)(?!\s*(?:bn|tn|m\b|k\b)|\d)/gi;
var BB10H_TF_RE = /Yahoo Finance daily closes/;
var BB10H_SNAP_RE = /Coinbase 24h rolling/;
function bb10hNum(s) { return Number(String(s).replace(/,/g, "")); }
function bb10hCites(s) { var o = []; (String(s).match(/\[(\d+)\]/g) || []).forEach(function (m) { o.push(m.slice(1, -1)); }); return o; }
// prices a sentence states for a coin: only "at / to / is / now $X" figures near the coin's snapshot price (a base close "of $X" is history, not a price)
function bb10hPrices(sent, ref) {
  var out = [], m, re = new RegExp(BB10H_PRICE_RE.source, "gi");
  while ((m = re.exec(String(sent).replace(/\[\d+\]/g, "")))) { var v = bb10hNum(m[1]); if (ref > 0 && v >= ref * 0.6 && v <= ref * 1.6) out.push(v); }
  return out;
}
function bb10hPer(sent) { var m = /\b(This month|This week|Today|Year to date)\b/.exec(sent); return m ? m[1] : ""; }
// the "to $N now" of a Yahoo period sentence is a second live price for the coin: keep the period figure, drop that price
function bb10hRebase(sent, price) {
  var m = /\bto \$([\d,]+(?:\.\d+)?) now(?=,)/.exec(sent);
  if (!m) return sent;
  return sent.replace(/\s+to \$[\d,]+(?:\.\d+)? now(?=,)/, "").replace(/(\b(?:down|up) \d+(?:\.\d+)?%)(?= \()/, function (x, a) {
    var per = bb10hPer(sent);
    return a + (/month/i.test(per) ? " month-to-date" : /week/i.test(per) ? " week-to-date" : /year/i.test(per) ? " year-to-date" : "");
  });
}
// the final answer: stale as-of out, one price per coin, no "no figures" contradiction, no proxy label on the coin's own line
function bb10hApply(r, st) {
  if (!r || typeof r !== "object" || typeof r.reply !== "string" || !st) return r;
  var sp = bb10fSplit(r.reply), body = sp.body, tail = sp.tail, sources = r.sources, now = Date.now();
  var rows = st.bb10cRows || {}, named = st.bb10fNamed || [], lost = {}, info = { stale: [], dup: [], rebased: [], contra: [], proxy: [] }, changed = false;
  var lines = body.split("\n");
  // pass 1: sentences list per line
  var units = [];
  lines.forEach(function (line, li) {
    if (!line.trim() || /^\s*(?:Basis|Sources):/.test(line)) return;
    bb10fSents(line).forEach(function (sent, si) {
      var cs = []; try { cs = bb10cCoinsIn(sent); } catch (e) { cs = []; }
      units.push({ li: li, si: si, t: sent, coin: cs.length === 1 ? cs[0] : "", multi: cs.length > 1, drop: false, why: "" });
    });
  });
  // (a) a crypto sentence whose own as-of is older than the limit is never served
  units.forEach(function (u) {
    if (!(u.coin || u.multi || BB10H_CRYPTO_WORD_RE.test(u.t))) return;
    var m, re = new RegExp(BB10H_ASOF_RE.source, "g"), old = false;
    while ((m = re.exec(u.t))) { var ms = bb10hAsOfMs(m[1], now); if (ms != null && now - ms > BB10H_ASOF_MAX_MS) old = true; }
    if (old) { u.drop = true; u.why = "stale"; info.stale.push(u.t.slice(0, 80)); }
  });
  // a coin the question names is not a "proxy": drop that label from its own Coinbase line (also inside a "; "-joined line)
  var namedAll = named.slice(); try { bb10cCoinsIn(String(st.bb10fQ || "")).forEach(function (c) { if (namedAll.indexOf(c) < 0) namedAll.push(c); }); } catch (e) {}
  units.forEach(function (u) {
    if (u.drop || !BB10H_SNAP_RE.test(u.t) || !/As a proxy,/i.test(u.t)) return;
    var t2 = u.t.replace(/(^\s*|;\s+)As a proxy,\s*([^,;]{1,40}?)(?=\s+(?:is|was|are|were|fell|rose)\b)/gi, function (m, a, nm) {
      var cs = []; try { cs = bb10cCoinsIn(nm); } catch (e) { cs = []; }
      return cs.length === 1 && namedAll.indexOf(cs[0]) >= 0 ? a + nm : m;
    });
    if (t2 !== u.t) { u.t = t2; u.edit = true; info.proxy.push(u.t.slice(0, 60)); }
  });
  // (b) one price per coin (the freshest Coinbase snapshot), one period figure per coin
  var seenTf = {}, seenSnap = {};
  units.forEach(function (u) {
    if (u.drop || !u.coin || !rows[u.coin] || !(Number(rows[u.coin].price) > 0)) return;
    var S = Number(rows[u.coin].price), ps = bb10hPrices(u.t, S), isTf = BB10H_TF_RE.test(u.t), isSnap = BB10H_SNAP_RE.test(u.t);
    var diff = ps.filter(function (p) { return Math.abs(p / S - 1) > 0.0005; });
    if (isTf) {
      var k = u.coin + "|" + bb10hPer(u.t);
      if (seenTf[k]) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); return; }
      seenTf[k] = 1;
      if (diff.length) { var nt = bb10hRebase(u.t, diff[0]); if (nt !== u.t) { info.rebased.push({ from: u.t, to: nt }); u.t = nt; u.edit = true; } }
      return;
    }
    if (isSnap) {
      var k2 = u.coin + "|" + u.t.replace(/\s*\[\d+\]/g, "").replace(/^\s*As a proxy,\s*/i, "");
      if (seenSnap[k2]) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); return; }
      seenSnap[k2] = 1;
      return;
    }
    if (diff.length) { u.drop = true; u.why = "dup"; info.dup.push(u.t.slice(0, 80)); }
  });
  // (c) "we have no crypto figures" next to the crypto figures themselves
  var haveCoin = units.some(function (u) { return !u.drop && u.coin && rows[u.coin] && (BB10H_TF_RE.test(u.t) || BB10H_SNAP_RE.test(u.t)); });
  if (haveCoin) units.forEach(function (u) { if (!u.drop && BB10H_CONTRA.some(function (re) { return re.test(u.t); })) { u.drop = true; u.why = "contra"; info.contra.push(u.t.slice(0, 80)); } });
  if (!units.some(function (u) { return u.drop || u.edit; })) return r;
  // rebuild only the lines that changed
  var byLine = {};
  units.forEach(function (u) { (byLine[u.li] = byLine[u.li] || []).push(u); });
  var out = [];
  lines.forEach(function (line, li) {
    var us = byLine[li];
    if (!us || !us.some(function (u) { return u.drop || u.edit; })) { out.push(line); return; }
    us.forEach(function (u) { if (u.drop) bb10hCites(u.t).forEach(function (n) { lost[n] = "bb10h"; }); });
    var keep = us.filter(function (u) { return !u.drop; }).map(function (u) { return u.t; });
    out.push(keep.join(" "));
  });
  body = out.join("\n").replace(/(?:^|\n)[ \t]+(?=\n)/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/^\n+/, "").replace(/\s+$/, "");
  if (info.stale.length && !/more than 10 minutes old/.test(body)) body = body.replace(/\s+$/, "") + "\n\n" + BB10H_STALE_NOTE;
  var rn = bb10fRenumber(body, tail, lost, sources);
  body = rn.body; tail = rn.tail; sources = rn.sources;
  // a period sentence's source detail must say what the sentence says
  info.rebased.forEach(function (x) {
    var a = x.from.replace(/\s*\[\d+\]/g, "").replace(/\.$/, ""), b = x.to.replace(/\s*\[\d+\]/g, "").replace(/\.$/, "");
    if (tail.indexOf(a) >= 0) tail = tail.split(a).join(b);
    if (Array.isArray(sources)) sources = sources.map(function (s) { return s && typeof s.detail === "string" && s.detail.indexOf(a) >= 0 ? Object.assign({}, s, { detail: s.detail.split(a).join(b) }) : s; });
  });
  // the Yahoo period source for a coin with a Coinbase price: its other periods ("to $N now") drop the second price too
  function bb10hSrcRebase(t) {
    var m = /finance\.yahoo\.com\/quote\/([A-Z0-9]+)-USD\//.exec(String(t)), S = m && rows[m[1]] ? Number(rows[m[1]].price) : 0;
    if (!(S > 0) || !BB10H_TF_RE.test(t)) return t;
    return t.replace(/\s+to \$([\d,]+(?:\.\d+)?) now(?=[,)])/g, function (x, n) { return Math.abs(bb10hNum(n) / S - 1) > 0.0005 ? "" : x; });
  }
  if (haveCoin) {
    tail = tail.split("\n").map(function (l) { return /^\[\d+\]\s/.test(l) ? bb10hSrcRebase(l) : l; }).join("\n");
    if (Array.isArray(sources)) sources = sources.map(function (x) {
      if (!x) return x;
      var d = typeof x.detail === "string" ? x.detail : null, d2 = d == null ? null : bb10hSrcRebase((x.link || "") + " " + d).slice(String(x.link || "").length + 1);
      return d != null && d2 !== d ? Object.assign({}, x, { detail: d2 }) : x;
    });
  }
  var o = Object.assign({}, r);
  o.reply = body + tail;
  if (sources !== r.sources) o.sources = sources;
  st.bb10hApplied = info;
  return o;
}
var bb10hFin0 = bb8qFinish;
bb8qFinish = function (out, st) {
  var r = bb10hFin0.apply(this, arguments);
  try { return bb10hApply(r, st); } catch (e) { console.warn("bb10h finish", e && e.message); return r; }
};

// ── (2) /brief, /lenses and /intelligence prose: coin % carry their period; one gold price, labelled ──
var BB10H_ALT = "Bitcoin|BTC|Ethereum|Ether|ETH|Solana|SOL|XRP|Ripple|Dogecoin|DOGE|Cardano|ADA|Avalanche|AVAX|Chainlink|LINK|Litecoin|LTC|Polkadot|DOT|Stellar|XLM|Shiba Inu|SHIB";
var BB10H_MOVE_SRC = "\\b(" + BB10H_ALT + ")\\b([^.;:%\\n]{0,40}?)\\b(down|up|fell|rose|gained|lost|slipped|dropped|declined|rallied|climbed|slid|sank|jumped|surged)\\s+(?:by\\s+|about\\s+|roughly\\s+|around\\s+)?(\\d+(?:\\.\\d+)?)\\s?%";
var BB10H_NEG_RE = /^(?:down|fell|lost|slipped|dropped|declined|slid|sank)$/i;
var BB10H_LABEL_24 = "24h on Coinbase", BB10H_LABEL_MTD = "month-to-date, Yahoo";
var bb10hMem = { mtd: {}, gold: null };
function bb10hCoinRow(coin) {
  var h = null; try { h = bb10CbRow(coin); } catch (e) { h = null; }
  if (!h || !(Date.now() - h.at <= BB10H_LIVE_TTL_MS)) return null;
  return { price: h.last, pct: (h.last / h.open - 1) * 100, at: h.at };
}
function bb10hMtd(coin) {
  var m = bb10hMem.mtd[coin];
  return m && Date.now() - m.at <= BB10H_LIVE_TTL_MS ? m : null;
}
async function bb10hLoadMtd(coin) {
  var tf = BB8Q_TF.filter(function (t) { return t.id === "month"; })[0];
  var j = await fetchYahooChart(coin + "-USD", "1y", "1d"), b = bb8qBars(j), c = b && tf ? bb8qTfChange(b, tf, null) : null;
  if (c && isFinite(c.pct)) bb10hMem.mtd[coin] = { pct: c.pct, base: c.from, baseDate: c.fromDate, now: c.to, asOf: b.nowMs, at: Date.now() };
}
async function bb10hLoadGold() {
  var q = await fetchGoldProxy();
  if (q && Number(q.p) > 0 && !q.stale && !q.cached) bb10hMem.gold = { q: q, at: Date.now() };
}
var BB10H_AI_RE = /market brief|site-intelligence|multi-lens/i;
async function bb10hPrefetch(options, r) {
  var sys = String((options && options.system) || "");
  if (!BB10H_AI_RE.test(sys)) return;
  var txt = ""; try { txt = typeof r === "string" ? r : JSON.stringify((r && (r.validated || r.text)) || ""); } catch (e) { txt = ""; }
  var coins = []; try { coins = bb10cCoinsIn(txt).slice(0, 6); } catch (e) { coins = []; }
  var jobs = [];
  if (coins.length) { jobs.push(bb10CryptoLoad(coins).catch(function () {})); coins.forEach(function (c) { jobs.push(bb10hLoadMtd(c).catch(function () {})); }); }
  if (/\bgold\b|\bXAU\b/i.test(txt)) jobs.push(bb10hLoadGold().catch(function () {}));
  if (!jobs.length) return;
  await withTimeout(Promise.all(jobs), BB10H_CTX_WAIT_MS, "bb10h context").catch(function () {});
}
var bb10hAi0 = generateAi;
generateAi = async function (options) {
  var r = await bb10hAi0.apply(this, arguments);
  try { await bb10hPrefetch(options, r); } catch (e) {}
  return r;
};
function bb10hFmtPct(x) { return Math.abs(x).toFixed(2); }
var BB10H_TAIL_PER = /^\s*(?:(?:over|in|during)\s+(?:the\s+)?(?:last\s+|past\s+)?(?:24[- ]?h(?:ours?|rs?)?|day)\b|(?:today|overnight|month[- ]to[- ]date|this month|MTD)\b)/i;
var BB10H_TAIL_PAREN = /^\s*\((?:[^)]*(?:Coinbase|Yahoo|24h|rolling|month)[^)]*)\)/i;
function bb10hCoinText(s) {
  var re = new RegExp(BB10H_MOVE_SRC, "gi"), out = "", last = 0, m, any = false;
  while ((m = re.exec(s))) {
    var cs = []; try { cs = bb10cCoinsIn(m[1]); } catch (e) { cs = []; }
    if (cs.length !== 1) continue;
    var coin = cs[0], rest = s.slice(re.lastIndex, re.lastIndex + 70), whole = m[0] + rest;
    var per = /month[- ]to[- ]date|\bMTD\b|this month/i.test(m[2] + " " + rest.slice(0, 40)) ? "month" : /24[- ]?h(?:ours?|rs?)?|\btoday\b|overnight|past day|last day|over the day/i.test(m[2] + " " + rest.slice(0, 40)) ? "day" : /\b(?:week|year|ytd|quarter|since)\b/i.test(m[2] + " " + rest.slice(0, 40)) ? "other" : "";
    if (per === "other") continue;
    var neg = BB10H_NEG_RE.test(m[3]), shown = (neg ? -1 : 1) * Number(m[4]);
    var cb = bb10hCoinRow(coin), my = bb10hMtd(coin), target = null, label = "";
    if (per === "month") { target = my ? my.pct : null; label = BB10H_LABEL_MTD; }
    else if (per === "day") { target = cb ? cb.pct : null; label = BB10H_LABEL_24; }
    else if (cb && Math.abs(shown - cb.pct) <= 0.05) { target = cb.pct; label = BB10H_LABEL_24; }
    else if (my && Math.abs(shown - my.pct) <= 0.05) { target = my.pct; label = BB10H_LABEL_MTD; }
    else if (cb) { target = cb.pct; label = BB10H_LABEL_24; }
    var rep, consumed = 0;
    if (target == null) { rep = m[1] + m[2] + m[3] + " (no verified figure available right now)"; }
    else {
      var verb = (target < 0) === neg ? m[3] : (target < 0 ? "down" : "up");
      rep = m[1] + m[2] + verb + " " + bb10hFmtPct(target) + "% (" + label + ")";
      var after = s.slice(re.lastIndex), t1 = BB10H_TAIL_PAREN.exec(after) || BB10H_TAIL_PER.exec(after);
      if (t1) consumed = t1[0].length;
    }
    out += s.slice(last, m.index) + rep; last = re.lastIndex + consumed; re.lastIndex = last; any = true;
  }
  return any ? out + s.slice(last) : s;
}
function bb10hGoldText(s) {
  if (!/\bgold\b|\bXAU\b/i.test(s) || /gold-api\.com|GC=F/i.test(s)) return s;
  return s.replace(/\$([\d,]{4,}(?:\.\d+)?)/g, function (m, n) {
    var v = bb10hNum(n);
    if (!(v >= 1000 && v <= 100000)) return m;
    var g = bb10hMem.gold, sn = null;
    try { sn = typeof lastChatLiveSnapshot !== "undefined" ? lastChatLiveSnapshot : null; } catch (e) { sn = null; }
    if (sn && isFinite(Number(sn.goldLast)) && Math.abs(v / Number(sn.goldLast) - 1) <= 0.0015 && Date.now() - Number(sn.goldTs) * 1000 <= BB10H_ASOF_MAX_MS) {
      return m + " (gold futures GC=F, Yahoo Finance, delayed 10 min, as of " + bb10Uk(Number(sn.goldTs) * 1000) + ")";
    }
    if (g && g.q && Date.now() - g.at <= BB10H_LIVE_TTL_MS) {
      var ms = bb8qMs(g.q) || g.at;
      return "$" + bb8qNum(g.q.p, 2) + " (gold spot, gold-api.com, as of " + bb10Uk(ms) + ")";
    }
    return "\u27e6bb10h-price\u27e7";
  }).replace(/\s*(?:,\s*)?(?:with |at |around )?(?:a |an )?(?:spot )?(?:price|level) (?:of|at) \u27e6bb10h-price\u27e7/gi, "").replace(/\s+(?:at|around)\s+\u27e6bb10h-price\u27e7/gi, "").replace(/\u27e6bb10h-price\u27e7/g, "a price we cannot verify right now");
}
function bb10hText(s) {
  if (typeof s !== "string" || s.length < 12) return s;
  var t = s;
  try { if (/%/.test(t)) t = bb10hCoinText(t); } catch (e) { t = s; }
  try { t = bb10hGoldText(t); } catch (e) {}
  return t;
}
var BB10H_SKIP = { date: 1, tk: 1, type: 1, value: 1, verdict: 1, priority: 1, focusTickers: 1, fit: 1, name: 1, role: 1, confidence: 1, id: 1 };
function bb10hWalk(v, key, depth) {
  if (depth > 6) return v;
  if (typeof v === "string") return BB10H_SKIP[key] ? v : bb10hText(v);
  if (Array.isArray(v)) { var a = v.map(function (x) { return bb10hWalk(x, key, depth + 1); }); return a.some(function (x, i) { return x !== v[i]; }) ? a : v; }
  if (v && typeof v === "object") {
    var o = null;
    Object.keys(v).forEach(function (k) { var n = bb10hWalk(v[k], k, depth + 1); if (n !== v[k]) { o = o || Object.assign({}, v); o[k] = n; } });
    return o || v;
  }
  return v;
}
var BB10H_TEXT_ROUTES = { "/api/brief": ["brief"], "/api/intelligence": ["intel"], "/api/lenses": ["lenses", "intelligence"] };
var bb10hShape0 = bb8oShape;
bb8oShape = function (res, status, body) {
  var out = bb10hShape0.apply(this, arguments);
  try {
    var p = res && res.bb8oPath, keys = BB10H_TEXT_ROUTES[p];
    if (!keys || status !== 200 || !out || typeof out !== "object" || out.error) return out;
    var o = null;
    keys.forEach(function (k) { if (out[k] != null) { var n = bb10hWalk(out[k], k, 0); if (n !== out[k]) { o = o || Object.assign({}, out); o[k] = n; } } });
    return o || out;
  } catch (e) { return out; }
};
'''

SPA_ANCHOR = '  const editorialRoute = p.match(/^\\/(brief|report|research)\\/([a-z0-9][a-z0-9-]{0,63})\\/?$/);\n'
SPA = '''  // bb12: SPA shell for the Capital Sustainability Monitor pages. Must sit before the /research/:slug editorial route so these paths win.
  // Same helper and headers as the other SPA routes (text(): 200, text/html, no-store, HEAD without body). Plain shell: index.html with its default head.
  if ((req.method === "GET" || req.method === "HEAD") && /^\\/research\\/capital-sustainability(?:\\/(?:method|[A-Za-z0-9.\\-]{1,10}))?\\/?$/.test(p)) {
    return text(res, 200, withAssetVersion(INDEX_TEMPLATE), "text/html; charset=utf-8");
  }
'''

EDITS = [
 ("// BB10J_JS_END", "// BB10J_JS_END\n" + BB11.rstrip("\n") + "\n// BB11_JS_END"),
 ("// BB10G_JS_END", "// BB10G_JS_END\n" + BB10H.rstrip("\n") + "\n// BB10H_JS_END"),
 (SPA_ANCHOR, SPA + SPA_ANCHOR),
]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; check = "--check" in sys.argv
    if not args: print("usage: patch_bb12b.py <folder> [--check]"); return 0
    f = os.path.join(args[0], "server.js")
    if not os.path.isfile(f): print("REFUSE: no server.js in " + args[0]); return 0
    raw = open(f, "rb").read(); m0 = md5(raw)
    print(f"bb12b: {f} md5 {m0} lines {raw.count(b'\n')}")
    if m0 != BASE_MD5: print(f"WARN: md5 {m0} != expected base {BASE_MD5} (bb10j live); continuing on anchors")
    crlf = b"\r\n" in raw; s = raw.decode("utf-8").replace("\r\n", "\n")
    if "// ── bb11:" in s or "BB11_JS_END" in s or "// ── bb10h:" in s or "BB10H_JS_END" in s or "// bb12:" in s: print("REFUSE: bb12b (or bb12 / bb10h / bb11) already applied"); return 0
    if "BB10I_MAINTENANCE_ON" not in s or "var bb10iHandle0" not in s or "bb10jSend" not in s: print("REFUSE: bb10i/bb10j is not applied (BB10I_MAINTENANCE_ON / bb10iHandle0 / bb10jSend missing)"); return 0
    for a, b in EDITS:
        n = s.count(a)
        if n != 1: print(f"REFUSE: anchor found {n}x: {a[:90]!r}"); return 0
        s = s.replace(a, b, 1)
    out = s.replace("\n", "\r\n") if crlf else s
    data = out.encode("utf-8"); tmp = f + ".bb12b.tmp.js"; open(tmp, "wb").write(data)
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        os.remove(tmp); print("REFUSE: node --check failed\n" + r.stderr); return 0
    print("node --check: ok")
    if check:
        os.remove(tmp); print(f"--check: dry run ok, would write md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
    os.replace(tmp, f); print(f"bb12b: wrote {f} md5 {md5(data)} sha256 {sha(data)} lines {data.count(b'\n')}"); return 0
if __name__ == "__main__": sys.exit(main())
