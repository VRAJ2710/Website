// Offline tests for deploy/patch_bb8o.py: zero-price fallback and the canonical feed object, Form 4 trade-date
// fallbacks, the LSE listing profile, the brief edition rule and the Taiwan session. Loads the bb8o block with
// stubs; no network, no live files, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8o.py"), "utf8");
const B8O = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8o \u2500\u2500"), PATCH.indexOf("// BB8O_JS_END") + 14);
assert.match(B8O, /function bb8oFix\(/);

// Copies of the server helpers the block calls (bb7Tag/bb7Blocks/bb7IsoDate are verbatim from server.js).
const STUBS = `
var NOW = Date.parse("2026-10-19T10:52:15Z");
function bb7Decode(s) { return String(s || "").replace(/&amp;/g, "&"); }
function bb7Tag(xml, tag) {
  var re = new RegExp("<(?:[\\\\w.-]+:)?" + tag + "(?:\\\\s[^>]*)?>([\\\\s\\\\S]*?)</(?:[\\\\w.-]+:)?" + tag + ">", "i");
  var m = re.exec(String(xml || ""));
  if (!m) return "";
  var inner = m[1];
  var v = /<(?:[\\w.-]+:)?value(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:[\\w.-]+:)?value>/i.exec(inner);
  return bb7Decode(v ? v[1] : inner).replace(/<[^>]+>/g, "").trim();
}
function bb7Blocks(xml, tag) {
  var re = new RegExp("<(?:[\\\\w.-]+:)?" + tag + "(?:\\\\s[^>]*)?>[\\\\s\\\\S]*?</(?:[\\\\w.-]+:)?" + tag + ">", "gi");
  return String(xml || "").match(re) || [];
}
function bb7IsoDate(value) {
  var s = String(value || "").trim();
  var iso = /^(\\d{4})-(\\d{2})-(\\d{2})/.exec(s);
  if (iso) return iso[1] + "-" + iso[2] + "-" + iso[3];
  var us = /^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{4})$/.exec(s);
  if (!us) return s;
  return us[3] + "-" + ("0" + us[1]).slice(-2) + "-" + ("0" + us[2]).slice(-2);
}
function bb7ParseForm4(xml, meta) {
  var rows = [];
  bb7Blocks(xml, "nonDerivativeTransaction").forEach(function (b) { rows.push({ transactionCode: bb7Tag(b, "transactionCode"), transactionDate: bb7IsoDate(bb7Tag(b, "transactionDate")), filingDate: (meta || {}).filingDate || "" }); });
  bb7Blocks(xml, "derivativeTransaction").forEach(function (b) { rows.push({ transactionCode: bb7Tag(b, "transactionCode"), transactionDate: bb7IsoDate(bb7Tag(b, "transactionDate")), filingDate: (meta || {}).filingDate || "", isDerivative: true }); });
  return rows;
}
function parseForm4(xml, ticker, sourceUrl) {
  var blocks = String(xml).match(/<(nonDerivativeTransaction|derivativeTransaction)>[\\s\\S]*?<\\/\\1>/gi) || [];
  return blocks.slice(0, 20).map(function (b) { return { ticker: ticker, date: null, sourceUrl: sourceUrl }; });
}
var BB8L_MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
function bb8lDay(s) { var m = /^(\\d{4})-(\\d{2})-(\\d{2})/.exec(String(s || "")); return m ? Number(m[3]) + " " + BB8L_MON[Number(m[2]) - 1] + " " + m[1] : ""; }
function bb8lRowDates(body) { return body; }
function bb8cUnit(c) { return c === "GBp" ? { major: "GBP", div: 100 } : { major: String(c || "").toUpperCase(), div: 1 }; }
function bb8dUk(ms) {
  var p = {}; new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms)).forEach(function (x) { p[x.type] = x.value; });
  return p.weekday + " " + p.day + " " + p.month + ", " + p.hour + ":" + p.minute + " UK";
}
function bb5eCanon(s) { return String(s || "").trim().toUpperCase(); }
function bb5eCash(tz, o, c, label, lo, lc) { var s = { mode: "cash", tz: tz, o: o, c: c, label: label }; if (lo != null) { s.lo = lo; s.lc = lc; } return s; }
function bb5eSpec(symbol) {
  var s = bb5eCanon(symbol);
  if (/\\.HK$/.test(s)) return bb5eCash("Asia/Hong_Kong", 570, 960, "Hong Kong", 720, 780);
  if (/\\.L$/.test(s)) return bb5eCash("Europe/London", 480, 990, "London");
  if (/=X$/.test(s)) return { mode: "fx", label: "FX" };
  return bb5eCash("America/New_York", 570, 960, "US");
}
function bb5gSpec(symbol) { return bb5eSpec(symbol); }
var OPEN = {};
function bb5eOpenAt(spec, d) { return !!OPEN[spec.label]; }
function bb5eApply(q, sym) { var o = Object.assign({}, q); if (!OPEN[(bb5eSpec(sym) || {}).label]) { o.status = "closed"; o.nextOpen = "2026-10-20T01:30:00.000Z"; } return o; }
var CHART = null, UPCALLS = [];
async function upstream(u) { UPCALLS.push(u); return { json: async function () { return /2330/.test(u) ? CHART : { chart: { result: [] } }; } }; }
var YQ = {};
async function yahooQuote(symbols) { return JSON.parse(JSON.stringify(YQ)); }
async function fetchYahooQuote(s) { return YQ[s] ? JSON.parse(JSON.stringify(YQ[s])) : null; }
var HEADS = [];
async function _rt48sHeads() { return HEADS.map(function (h) { return Object.assign({}, h); }); }
var SENT = [];
function json(res, status, body, extra) { SENT.push({ status: status, body: body }); return body; }
async function handle(req, res) { return "base"; }
var RT32 = { cache: new Map() };
async function rt32Yahoo(sym) { return { financialData: { currentPrice: { raw: 100 }, targetMeanPrice: { raw: 250 }, targetHighPrice: { raw: 300 }, targetLowPrice: { raw: 150 }, targetMedianPrice: { raw: 240 }, recommendationKey: "buy", recommendationMean: { raw: 1.8 }, numberOfAnalystOpinions: { raw: 40 }, profitMargins: { raw: 0.5 } }, recommendationTrend: { trend: [{ strongBuy: 10 }] }, upgradeDowngradeHistory: { history: [{ firm: "X", toGrade: "Buy" }] }, price: { regularMarketPrice: { raw: 100 } } }; }
async function readBody(req) { return JSON.parse(JSON.stringify(req.__body)); }
var bb2Read0 = typeof readBody === "function" ? readBody : async function () { return {}; };
var GEN = [];
var NEXTV = null;
async function generateAi(options) { GEN.push(options); var r = { text: "{}", provider: "stub", model: "stub" }; if (NEXTV) r.validated = NEXTV; return r; }
function validateCommitteeResponse(t) { return t; }
function validateLensesResponse(t) { return t; }
function validateIntelligenceResponse(t) { return t; }
function validateBriefResponse(t) { return t; }
function normaliseChatAnswer(t) { return t; }
var YCH = {}, YCALLS = [];
function bb8oTestSeries(closes) { var t0 = 1792180800 - (closes.length - 1) * 86400; return { chart: { result: [{ meta: { regularMarketTime: t0 + (closes.length - 1) * 86400 }, timestamp: closes.map(function (_c, i) { return t0 + i * 86400; }), indicators: { quote: [{ close: closes }] } }] } }; }
async function fetchYahooChart(sym, range, interval) { YCALLS.push(sym + "|" + range + "|" + interval); return YCH[sym] ? { data: YCH[sym] } : { unavailable: true }; }
`;
function load() {
  const ctx = { console: { warn() {} }, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, Map, Intl, isFinite, crypto };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext(B8O, ctx, { filename: "bb8o.js" });
  return ctx;
}
const FRI = 1792138094; // Fri 16 Oct 2026 08:08:14 UTC = 16:08 HKT

test("item 1: a zero price falls back to the last valid close with its real timestamp and session", async () => {
  const c = load();
  c.YQ = { "0700.HK": { p: 417.8, prev: 417.8, c: 0, change: 0, currency: "HKD", ts: FRI, status: "closed" } };
  await c.yahooQuote(["0700.HK"]);
  c.YQ = { "0700.HK": { p: 0, prev: 0, c: NaN, change: NaN, currency: "HKD", ts: 0, status: "closed" } };
  const out = await c.yahooQuote(["0700.HK"]);
  const q = out["0700.HK"];
  assert.equal(q.p, 417.8);
  assert.equal(q.ts, FRI);
  assert.equal(q.fallback, true);
  assert.equal(q.fallbackReason, "zero-price");
  assert.equal(q.session.label, "regular close, Fri 16 Oct, 16:08 HKT (09:08 UK)");
  assert.equal(q.session.date, "2026-10-16");
  assert.ok(Number.isFinite(q.c) && Number.isFinite(q.change));
  assert.match(q.note, /^Last valid close · regular close, Fri 16 Oct/);
});

test("item 1: null / NaN / Infinity prices never pass; no memory uses one Yahoo daily chart read; else the row is dropped", async () => {
  const c = load();
  c.CHART = { chart: { result: [{ meta: { currency: "TWD", regularMarketTime: 1792387806, exchangeTimezoneName: "Asia/Taipei" }, timestamp: [1792198800, 1792285200, 1792371600, 1792387806], indicators: { quote: [{ close: [2440, 2425, 2420, 2420] }] } }] } };
  c.YQ = { "2330.TW": { p: null, ts: 1792387806 }, "BAD": { p: Infinity } };
  let out = await c.yahooQuote(["2330.TW", "BAD"]);
  assert.equal(out["2330.TW"].p, 2420);
  assert.equal(out["2330.TW"].fallbackReason, "missing-price");
  assert.equal(out["2330.TW"].ts, 1792387806);
  assert.equal(out["2330.TW"].prev, 2425, "previous close is the prior trading day, not a duplicate bar of the same day");
  assert.match(out["2330.TW"].session.label, /13:30 Taipei time \(06:30 UK\)/);
  c.CHART = { chart: { result: [] } };
  assert.equal("BAD" in out, false);
  assert.ok(c.UPCALLS.every(u => /^https:\/\/query1\.finance\.yahoo\.com\/v8\/finance\/chart\//.test(u)));
  // Route edge: finnhub single object with p 0 and nothing remembered -> {}
  assert.deepEqual(JSON.parse(JSON.stringify(c.bb8oShape({ bb8oPath: "/api/finnhub", bb8oQuery: new URLSearchParams("symbol=ZZZ") }, 200, { p: 0, c: 0 }))), {});
  // Twelve map: NaN dropped, valid kept with feed
  const tb = c.bb8oShape({ bb8oPath: "/api/twelve-data-quote" }, 200, { quotes: { "EUR/USD": { p: 1.12, prev: 1.124, c: -0.3, change: -0.004, ts: Math.floor(c.NOW / 1000) }, "X/Y": { p: NaN } } });
  assert.deepEqual(Object.keys(tb.quotes), ["EUR/USD"]);
  assert.equal(tb.quotes["EUR/USD"].feed.symbol, "EURUSD=X");
  // no previous close and an explicit null change (fix A): stays null, flagged; a non-finite change becomes 0, basis none
  const t2 = c.bb8oShape({ bb8oPath: "/api/market-reference-quotes" }, 200, { DXY: { p: 101.9, prev: null, c: null, change: null, ts: 1 }, VIX: { p: 18, prev: null, c: NaN, change: "x", ts: 1 } });
  assert.equal(t2.DXY.c, null); assert.equal(t2.DXY.change, null); assert.equal(t2.DXY.changeAvailable, false);
  assert.equal(t2.VIX.c, 0); assert.equal(t2.VIX.basis, "none"); assert.equal(t2.VIX.changeAvailable, false);
});

test("item 1: fetchYahooQuote (DXY inputs) and valuation price are guarded too", async () => {
  const c = load();
  c.YQ = { "EURUSD=X": { p: 1.121, prev: 1.124, ts: 1792405850 } };
  assert.equal((await c.fetchYahooQuote("EURUSD=X")).p, 1.121);
  c.YQ = { "EURUSD=X": { p: 0, prev: 1.124, ts: 1792405850 } };
  const q = await c.fetchYahooQuote("EURUSD=X");
  assert.equal(q.p, 1.121); assert.equal(q.fallback, true);
  const v = c.bb8oShape({ bb8oPath: "/api/financials" }, 200, { symbol: "EURUSD=X", valuation: { price: 0 } });
  assert.equal(v.valuation.price, 1.121); assert.equal(v.valuation.priceFallback, true);
  const w = c.bb8oShape({ bb8oPath: "/api/financials" }, 200, { symbol: "NOPE", valuation: { price: NaN } });
  assert.equal(w.valuation.price, null); assert.equal(w.valuation.priceMissing, true);
});

test("item 4: one feed status per row, same classifier on every route", () => {
  const c = load();
  const now = c.NOW, s = Math.floor(now / 1000);
  c.OPEN = { FX: true, London: true };
  const f = (q, sym) => c.bb8oFeed(q, sym, "yahoo", now);
  assert.equal(f({ p: 1.12, ts: s - 20, delayMin: 0 }, "EURUSD=X").status, "live");
  assert.equal(f({ p: 1.12, ts: s - 400, delayMin: 0 }, "EURUSD=X").status, "delayed");
  assert.equal(f({ p: 1.12, ts: s - 400, delayMin: 0 }, "EURUSD=X").reason, "age");
  assert.equal(f({ p: 1.12, ts: s - 1300, delayMin: 0 }, "EURUSD=X").status, "stale");
  assert.equal(f({ p: 619, ts: s - 904, delayMin: 15 }, "BP.L").status, "delayed");
  assert.equal(f({ p: 619, ts: s - 904, delayMin: 15 }, "BP.L").reason, "exchange-delay");
  assert.equal(f({ p: 417.8, ts: FRI, status: "closed" }, "0700.HK").status, "closed");
  assert.equal(f({ p: 417.8, ts: FRI, status: "closed" }, "0700.HK").sessionLabel, "regular close, Fri 16 Oct, 16:08 HKT (09:08 UK)");
  assert.equal(f({ p: 1.1, ts: s - 5, fallback: true }, "EURUSD=X").status, "stale");
  const a = c.bb8oShape({ bb8oPath: "/api/yahoo-quote" }, 200, { "EURUSD=X": { p: 1.12, ts: s - 30, delayMin: 0, status: "fresh" } })["EURUSD=X"].feed;
  const b = c.bb8oShape({ bb8oPath: "/api/twelve-data-quote" }, 200, { quotes: { "EUR/USD": { p: 1.12, ts: s - 30, delayMin: 0, status: "delayed" } } }).quotes["EUR/USD"].feed;
  for (const k of ["v", "symbol", "status", "ageSec", "asOf", "asOfUk", "delayMin", "market"]) assert.deepEqual(a[k], b[k], k);
  assert.deepEqual(Object.keys(a).sort(), ["ageSec", "asOf", "asOfUk", "changeDay", "changeDayLabel", "delayMin", "fallback", "market", "reason", "sessionDate", "sessionDayUk", "sessionLabel", "source", "status", "symbol", "v"]);
});

const X = (tx, de, por) => `<ownershipDocument>${por ? `<periodOfReport>${por}</periodOfReport>` : ""}<nonDerivativeTable><nonDerivativeTransaction><transactionCoding><transactionCode>S</transactionCode></transactionCoding>${tx ? `<transactionDate><value>${tx}</value></transactionDate>` : ""}${de ? `<deemedExecutionDate><value>${de}</value></deemedExecutionDate>` : ""}</nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>`;
test("item 2: transactionDate, then deemedExecutionDate, then periodOfReport; never the filing date", () => {
  const c = load();
  const meta = { filingDate: "2026-09-23" };
  assert.deepEqual([c.bb7ParseForm4(X("2026-09-21", "", "2026-09-20"), meta)[0]].map(r => [r.transactionDate, r.transactionDateSource])[0], ["2026-09-21", "transactionDate"]);
  assert.deepEqual([c.bb7ParseForm4(X("", "2026-09-19", "2026-09-18"), meta)[0]].map(r => [r.transactionDate, r.transactionDateSource])[0], ["2026-09-19", "deemedExecutionDate"]);
  assert.deepEqual([c.bb7ParseForm4(X("", "", "2026-09-18"), meta)[0]].map(r => [r.transactionDate, r.transactionDateSource])[0], ["2026-09-18", "periodOfReport"]);
  const none = c.bb7ParseForm4(X("", "", ""), meta)[0];
  assert.equal(none.transactionDate, null);
  const body = c.bb8lRowDates({ insider: [none, Object.assign({}, none, { transactionDate: "2026-09-02", filingDate: "2026-09-02" }), Object.assign({}, none, { transactionDate: "2026-09-21" })] });
  const miss = body.insider.find(r => r.transactionDateMissing);
  assert.equal(miss.transactionDate, null); assert.equal(miss.tradeDate, null); assert.equal(miss.transactionDateUk, null);
  assert.equal(miss.whenUk, "Trade date not reported · filed 23 Sep 2026");
  assert.equal(body.insider[0].tradeDate, "2026-09-21");
  assert.equal(body.insider[0].whenUk, "21 Sep 2026 · filed 23 Sep 2026");
  const same = body.insider.find(r => r.sameDayFiling);
  assert.equal(same.whenUk, "2 Sep 2026 · filed same day");
  assert.equal(body.insider[2], miss, "missing trade dates sort last");
  const legacy = c.parseForm4(X("", "2026-09-19", ""), "NVDA", "u")[0];
  assert.equal(legacy.date, "2026-09-19"); assert.equal(legacy.dateSource, "deemedExecutionDate");
  assert.equal(c.parseForm4(X("", "", ""), "NVDA", "u")[0].dateMissing, true);
});

test("item 3: LSE profile handles GBp and checks market cap against price x shares", () => {
  const c = load();
  const r = { price: { longName: "BP p.l.c.", currency: "GBp", regularMarketPrice: { raw: 619.5 }, exchangeName: "LSE", quoteType: "EQUITY", marketCap: { raw: 95734734848 } }, summaryDetail: { marketCap: { raw: 95734734848 }, trailingPE: { raw: 24.78 } }, defaultKeyStatistics: { sharesOutstanding: { raw: 15453548807 } }, assetProfile: { sector: "Energy", industry: "Oil & Gas Integrated", country: "United Kingdom" } };
  const p = c.bb8oProfileFrom("BP.L", r);
  assert.equal(p.marketCapText, "£95.7bn"); assert.equal(p.marketCapCurrency, "GBP"); assert.equal(p.priceCurrency, "GBp");
  assert.equal(p.priceMajor, 6.195); assert.equal(p.marketCapCheck.status, "ok");
  assert.equal(p.asset.nm, "BP p.l.c. (LSE)"); assert.equal(p.asset.rg, "UK"); assert.equal(p.asset.mc, "£95.7bn");
  assert.equal(JSON.stringify(p).match(/\b(buy|sell|hold|target|undervalued|opportunity)\b/i), null);
  const r2 = JSON.parse(JSON.stringify(r)); r2.summaryDetail.marketCap.raw = 9573473484800; r2.price.marketCap.raw = 9573473484800;
  const p2 = c.bb8oProfileFrom("BP.L", r2);
  assert.equal(p2.marketCapCheck.status, "corrected-minor-units"); assert.equal(p2.marketCapText, "£95.7bn");
  const s = c.bb8oSearchBody({ quotes: [{ symbol: "BP.L", longname: "BP p.l.c.", exchDisp: "London", exchange: "LSE", typeDisp: "Equity", quoteType: "EQUITY", sector: "Energy" }], news: [], status: "available" }, p);
  assert.equal(s.result[0].symbol, "BP.L"); assert.equal(s.result[0].name, "BP p.l.c."); assert.equal(s.result[0].exchange, "London");
  assert.equal(s.result[0].profile, p); assert.equal(s.profile, p); assert.equal(s.quotes.length, 1);
});

const H = (h, src, t, as) => ({ h, src, link: "https://example.org/" + encodeURIComponent(h), t: Date.parse(t), as: as || ["USD"] });
test("item 5: the edition lead holds; a new edition needs broader coverage, a new day or an aged lead", async () => {
  const c = load();
  const base = [H("Dollar holds steady as French unrest weighs on Euro", "Investing.com", "2026-10-19T09:00:00Z"), H("Gold edges higher in quiet trade", "CNBC", "2026-10-19T08:00:00Z", ["XAU"])];
  c.HEADS = base;
  const t0 = Date.parse("2026-10-19T09:10:00Z");
  const e1 = await c.bb8oEdition(t0);
  assert.equal(e1.reason, "cold-start"); assert.match(e1.editionId, /^2026-10-19\.1-[0-9a-f]{6}$/);
  assert.equal(e1.updatedAtUk, "Updated 10:10 UK");
  // fresher single-source stories do not move the lead
  c.HEADS = base.concat([H("Oil slips as stockpiles build in US", "MarketWatch", "2026-10-19T09:30:00Z", ["WTI"])]);
  c.bb8oEd.headsAt = 0;
  const e2 = await c.bb8oEdition(t0 + 40 * 60000);
  assert.equal(e2.editionId, e1.editionId); assert.equal(e2.lead.headline, e1.lead.headline); assert.equal(e2.updatedAt, e1.updatedAt);
  // a newer story carried by two more outlets -> new edition (after the 30-minute dwell)
  c.HEADS = c.HEADS.concat([H("Bank of England signals pause as inflation cools", "BBC Business", "2026-10-19T10:00:00Z", ["GBP"]), H("Bank of England pause signalled as inflation cools", "CNBC", "2026-10-19T10:02:00Z", ["GBP"]), H("Inflation cools, Bank of England signals pause", "MarketWatch", "2026-10-19T10:03:00Z", ["GBP"])]);
  c.bb8oEd.headsAt = 0;
  const early = await c.bb8oEdition(t0 + 10 * 60000);
  assert.equal(early.editionId, e1.editionId, "dwell holds the lead for 30 minutes");
  c.bb8oEd.headsAt = 0;
  const e3 = await c.bb8oEdition(t0 + 60 * 60000);
  assert.equal(e3.reason, "broader-coverage"); assert.equal(e3.seq, 2); assert.match(e3.lead.headline, /Bank of England/); assert.equal(e3.lead.coverage, 3);
  const e4 = await c.bb8oEdition(t0 + 61 * 60000);
  assert.equal(e4.editionId, e3.editionId);
  // new UK day
  c.bb8oEd.headsAt = 0;
  const e5 = await c.bb8oEdition(Date.parse("2026-10-20T00:30:00Z"));
  assert.equal(e5.reason, "new-day"); assert.equal(e5.day, "2026-10-20"); assert.equal(e5.seq, 1);
  // restart: a fresh process with the same feeds elects the same lead and id
  const c2 = load(); c2.HEADS = base;
  const r1 = await c2.bb8oEdition(t0);
  assert.equal(r1.editionId, e1.editionId);
  // feeds down: no edition, no crash
  const c3 = load(); c3.HEADS = [];
  const z = await c3.bb8oEdition(t0);
  assert.equal(z.editionId, null); assert.equal(z.status, "unavailable");
});

test("item 5: brief response carries the edition; the GET route is public and request-driven", async () => {
  const c = load();
  c.HEADS = [H("Dollar holds steady as French unrest weighs on Euro", "Investing.com", "2026-10-19T09:00:00Z")];
  const res = {};
  await c.handle({ method: "POST", url: "/api/brief", headers: {} }, res);
  assert.ok(res.bb8oEdition && res.bb8oEdition.editionId);
  const b = c.bb8oShape(res, 200, { brief: { text: "x" }, cached: false });
  assert.equal(b.edition.editionId, res.bb8oEdition.editionId);
  await c.handle({ method: "GET", url: "/api/brief/edition", headers: {} }, {});
  assert.equal(c.SENT.at(-1).status, 200); assert.equal(c.SENT.at(-1).body.editionId, res.bb8oEdition.editionId);
});

test("Taiwan listings use the Taipei session", () => {
  const c = load();
  const s = c.bb5eSpec("2330.TW");
  assert.equal(s.tz, "Asia/Taipei"); assert.equal(s.o, 540); assert.equal(s.c, 810); assert.equal(s.label, "Taiwan");
  assert.equal(c.bb5eSpec("6488.TWO").label, "Taiwan");
  assert.equal(c.bb5eSpec("AAPL").label, "US");
});

const TARGET = /^(target(High|Low|Mean|Median)(Price)?|priceTargets?|targetPrice|analystTargets?|consensusTarget|recommendation(Key|Mean|Trend)|upgradeDowngradeHistory|numberOfAnalystOpinions|analystRatings?|averageAnalystRating|consensusRating)$/i;
const GENERIC = /^(ratings?|ra|recommendations?|upgrades|downgrades)$/i;
function keyScan(o, path, hits, re) { re = re || TARGET; if (!o || typeof o !== "object") return hits; for (const k of Object.keys(o)) { if (re.test(k)) hits.push(path + "." + k); keyScan(o[k], path + "." + k, hits, re); } return hits; }
const both = (o, p) => keyScan(o, p, [], TARGET).concat(keyScan(o, p, [], GENERIC));
test("ratings: target / analyst keys go everywhere; generic keys only from the market allowlist and the fundamentals source and cache", async () => {
  const c = load();
  const y = await c.rt32Yahoo("NVDA");
  assert.deepEqual(both(y, "y"), []);
  assert.equal(y.financialData.profitMargins.raw, 0.5, "other fields kept");
  c.RT32.cache.set("NVDA", { at: 1, data: { valuation: { price: 100, pe: 30, targetMean: 250, recommendation: "buy" }, metrics: { peRatio: 30 } } });
  assert.deepEqual(both(c.RT32.cache.get("NVDA"), "cache"), []);
  assert.equal(c.RT32.cache.get("NVDA").data.valuation.pe, 30);
  const mk = () => ({ symbol: "BP.L", valuation: { price: 619.5, targetMean: 638.06, recommendation: "buy" }, priceTarget: { targetHigh: 1 }, recommendations: [{ buy: 3 }], upgrades: [], nested: [{ deep: { rating: "Buy", ra: "Hold", ratings: [1], averageAnalystRating: "1.8 - Buy", ok: 1 } }] });
  for (const route of ["/api/financials", "/api/finnhub", "/api/yahoo-quote", "/api/search", "/api/listing-profile", "/api/brief", "/api/openbb/fundamentals", "/api/screener"]) {
    const out = c.bb8oShape({ bb8oPath: route }, 200, mk());
    assert.deepEqual(both(out, route), [], route);
    assert.equal(out.nested[0].deep.ok, 1);
  }
  for (const route of ["/api/public/content", "/api/admin/content", "/api/prefs", "/api/me", "/api/academy-daily", "/api/committee", "/api/lenses", "/api/chat", "/api/ai-status", undefined]) {
    const out = c.bb8oShape({ bb8oPath: route }, 200, mk());
    assert.deepEqual(keyScan(out, "x", [], TARGET), [], String(route));
    assert.equal(out.valuation.recommendation, "buy", String(route));
    assert.equal(out.nested[0].deep.rating, "Buy"); assert.equal(out.nested[0].deep.ra, "Hold"); assert.deepEqual(out.nested[0].deep.ratings, [1]);
    assert.deepEqual(out.recommendations, [{ buy: 3 }]); assert.deepEqual(out.upgrades, []);
  }
  assert.equal(c.bb8oMarketRoute("/api/financials/x"), false, "exact paths only");
  const cyc = { a: 1 }; cyc.self = cyc; c.bb8oStripRatings(cyc, true); assert.equal(cyc.a, 1);
  assert.equal(c.bb8oStripRatings(null, true), null);
});
test("ratings: AI bodies sanitize only the client context / fact fields; the question and messages pass through byte-identical", async () => {
  const c = load();
  const q = "Should I buy MU? Its price target is $150 and the rating: Strong Buy · Hold";
  const ask = { messages: [{ role: "system", content: "Rating: Buy" }, { role: "user", content: "Why is NVDA moving?" }, { role: "assistant", content: "x" }, { role: "user", content: q }], question: q, userThesis: "I think the consensus rating Buy is wrong",
    context: "Ticker: NVDA (NVIDIA)\nAI score: 76/100 | Sentiment: Bullish | Rating: Strong Buy\nActive ticker: NVDA NVIDIA · Score 76/100 · Bullish · Strong Buy · $182.10 · Beta 1.72 · 52.8x\nAnalysts' mean price target is $250.00 (40 analysts), consensus rating Buy. Revenue grew 50%. The street recommendation is Outperform.",
    terminalContext: "Financial metrics: P/E 30, ROE 40 | Analyst: 40 buy / 5 hold / 1 sell | PT mean $250.5\nRegime: risk-on",
    tickers: [{ tk: "NVDA", ra: "Strong Buy", targetMean: 250, sc: 76 }], facts: [{ label: "P/E", value: 30, rating: "Buy", note: "consensus rating Buy" }], extra: { targetPrice: 1, rating: 5 } };
  const raw = JSON.stringify(ask.messages);
  const b1 = await c.readBody({ __body: ask }), b2 = await c.bb2Read0({ __body: ask });
  for (const b of [b1, b2]) {
    assert.equal(JSON.stringify(b.messages), raw, "messages byte-identical");
    assert.equal(b.messages[3].content, q); assert.equal(b.question, q); assert.equal(b.userThesis, "I think the consensus rating Buy is wrong");
    assert.equal(/Strong Buy|Rating:|rating Buy|Outperform|price target|\$250|Analyst:|PT mean/i.test(b.context + b.terminalContext + JSON.stringify(b.tickers) + JSON.stringify(b.facts)), false);
    assert.match(b.context, /Sentiment: Bullish/); assert.match(b.context, /Score 76\/100 · \$182\.10/); assert.match(b.context, /Revenue grew 50%/);
    assert.match(b.terminalContext, /P\/E 30, ROE 40\nRegime: risk-on/);
    assert.deepEqual(both(b.tickers, "t").concat(both(b.facts, "f")), []); assert.equal(b.tickers[0].sc, 76); assert.equal(b.facts[0].value, 30);
    assert.deepEqual(b.extra, { rating: 5 }, "outside context fields only target keys go");
  }
});
test("ratings: a stub model receives the user's question byte-identical and the no-advice rule", async () => {
  const c = load();
  vm.runInContext(`
    var MODEL = [];
    var SYS = "You are Dispatch Expert, a market-research assistant. No buy or sell recommendation and no price target.";
    async function stubModel(body) { MODEL.push(JSON.stringify(body)); return "You should buy MU now."; }
    async function stubAsk(req) {
      var b = await readBody(req);
      var reply = await stubModel({ system: SYS + "\\nTERMINAL CONTEXT:\\n" + b.context, messages: b.messages });
      return reply.replace(/\\b(?:you should|i recommend(?: that)? you)\\s+(?:buy|sell)\\b/gi, "no trade recommendation (research only)");
    }`, c);
  const input = { messages: [{ role: "user", content: "Should I buy MU?" }], context: "Active ticker: MU · $120.40 · Strong Buy · price target $150.00" };
  const sent = JSON.stringify(input.messages[0].content);
  const reply = await c.stubAsk({ __body: JSON.parse(JSON.stringify(input)) });
  const prompt = JSON.parse(c.MODEL[0]);
  assert.equal(JSON.stringify(prompt.messages[prompt.messages.length - 1].content), sent);
  assert.equal(Buffer.compare(Buffer.from(prompt.messages[0].content), Buffer.from("Should I buy MU?")), 0);
  assert.match(prompt.system, /No buy or sell recommendation/);
  assert.equal(/Strong Buy|price target \$150/.test(prompt.system), false);
  assert.match(prompt.system, /Active ticker: MU · \$120\.40/);
  assert.equal(/you should buy/i.test(reply), false);
});

const ADVICE = ["Buy MU on dips.", "We recommend accumulating NVDA.", "Investors should trim positions after the rally.", "Our rating is Strong Buy.", "MU is a buy here.", "Price target of $150.", "We see a fair value of $210 per share.", "Upside to $1,000 is likely.", "Go long NVDA into earnings.", "Go short the memory names.", "Add to positions below $800.", "Consider taking profits.", "Overweight semis.", "Move to overweight on memory.", "The stock offers 25% upside.", "Set a stop-loss at $820.", "Keep position size small given volatility.", "Allocate 5% of the portfolio to MU.", "Rebalance: Trim largest position to <20%.", "Hold.", "Analysts upgraded MU to Outperform.", "Entry point near $850 looks attractive.", "Our 12-month target of $1,050 implies upside.", "This is a good time to buy.", "Add defensive or low-correlation asset.", "Rotate into bonds.", "**Verdict:** Buy.", "Underweight Europe.", "Accumulate below $878.84."];
const FACTS = ["Insiders sold 120,000 shares in October.", "Buybacks totalled $1.2bn last quarter.", "The sell-off deepened on Friday.", "Selling pressure eased after the CPI print.", "MU fell 5.63% to $878.84 in its last session.", "Gold held steady near $4,180.", "Holders of the notes were repaid in full.", "Funds bought Treasuries as yields fell.", "Short interest rose to 3% of float.", "MU underperformed the SOXX by 1.48 points.", "Technology is overweight at 45% of the portfolio.", "Management added capacity in Idaho.", "The company will hold its earnings call on 18 December.", "Revenue grew 50% year on year to $9.3bn.", "Downside risks include a memory price slump.", "MU has a weighting of 7% in the SOXX.", "Consensus EPS for next quarter is $2.28.", "NVDA added 3% on Friday.", "The Fed will hold rates at 4.5%.", "Investors sold tech and bought bonds.", "Exit polls point to a hung parliament.", "Hedge funds sold 2m shares.", "Add to that the strong dollar.", "Investors rotated into bonds."];
test("advice: buy/sell/hold calls, ratings, targets and sizing are matched; factual buying and selling is not", () => {
  const c = load();
  assert.deepEqual(ADVICE.filter(s => !c.bb8oIsAdvice(s)), [], "advice missed");
  assert.deepEqual(FACTS.filter(s => c.bb8oIsAdvice(s)), [], "fact matched");
  assert.equal(c.bb8oAdviceText("MU fell 5.63% to $878.84. Buy on weakness. Insiders sold shares.\n- Price target $150.\n- Revenue grew 50%."), "MU fell 5.63% to $878.84. Insiders sold shares.\n- Revenue grew 50%.");
  assert.equal(c.bb8oAdviceCommittee("## Recommendation\nMU fell 5.63%. Buy MU; price target $1,050.\n\n## Verdict\nStrong Buy.\n\n## Risks\nA memory slump would hit margins."),
    "## Takeaway\nMU fell 5.63%.\n\n## Takeaway\nNo takeaway beyond the facts above.\n\n## Risks\nA memory slump would hit margins.");
});
test("advice: every prose field of committee, lenses, intelligence and brief output; takeaway added, labels neutral", () => {
  const c = load();
  const lenses = { lenses: [{ name: "Value", role: "Valuation lens", analysis: "MU trades at 30x. We see a fair value of $1,050. Buy on weakness.", verdict: "BUY" }, { name: "Macro", role: "Macro", analysis: "Strong Buy. Go long into earnings.", verdict: "HOLD" }],
    intelligence: { verdict: "Strong Buy with a target of $1,050.", confidence: 70, bullCase: "AI demand lifts pricing. Upside to $1,050 is likely.", actionPlan: "Accumulate below $878.84. Set a stop-loss at $820.", catalysts: ["Earnings on 18 December", "Buy before earnings."], positionSizing: "Allocate 5% of the portfolio to MU." }, meta: { provider: "stub" } };
  const L = c.bb8oShape({ bb8oPath: "/api/lenses" }, 200, lenses);
  assert.deepEqual(L.lenses.map(l => [l.analysis, l.verdict, l.takeaway]), [["MU trades at 30x.", "MONITOR", "MONITOR"], ["No takeaway beyond the facts above.", "MONITOR", "MONITOR"]]);
  assert.deepEqual([L.intelligence.verdict, L.intelligence.takeaway, L.intelligence.bullCase, L.intelligence.actionPlan, L.intelligence.positionSizing, L.intelligence.confidence], ["No takeaway beyond the facts above.", "No takeaway beyond the facts above.", "AI demand lifts pricing.", "No takeaway beyond the facts above.", "No takeaway beyond the facts above.", 70]);
  assert.deepEqual(L.intelligence.catalysts, ["Earnings on 18 December"]);
  const I = c.bb8oShape({ bb8oPath: "/api/intelligence" }, 200, { intel: { headline: "MU is a buy after the dip", insight: "MU fell 5.63%. Insiders sold shares. We recommend accumulating MU.", actions: [{ label: "Buy MU now", type: "chat", value: "Should I buy MU?" }, { label: "Explain MU's move", type: "chat", value: "Why did MU fall?" }], fit: [{ tk: "MU", score: 60 }] } });
  assert.equal(I.intel.headline, "No takeaway beyond the facts above."); assert.equal(I.intel.insight, "MU fell 5.63%. Insiders sold shares.");
  assert.deepEqual(I.intel.actions, [{ label: "Explain MU's move", type: "chat", value: "Why did MU fall?" }]); assert.deepEqual(I.intel.fit, [{ tk: "MU", score: 60 }]);
  const doc = { ticker: "MU", sentiment: "Bullish", keyTakeaways: ["Revenue grew 50%", "Investors should buy before the print."], tradingImplication: "Accumulate on weakness; fair value of $1,050.", summary: "MU reported revenue up 50%. Buybacks continued. We rate it a buy.", recommendation: "BUY", rebalance: [{ action: "Trim largest position to <20%", priority: "high" }] };
  const C = c.bb8oShape({ bb8oPath: "/api/committee" }, 200, { content: [{ type: "text", text: JSON.stringify(doc) }] });
  const cj = JSON.parse(C.content[0].text);
  assert.deepEqual([cj.ticker, cj.sentiment, cj.keyTakeaways, cj.tradingImplication, cj.summary, cj.recommendation, cj.takeaway], ["MU", "Bullish", ["Revenue grew 50%"], "No takeaway beyond the facts above.", "MU reported revenue up 50%. Buybacks continued.", "MONITOR", "MONITOR"]);
  assert.deepEqual(cj.rebalance, [{ action: "No takeaway beyond the facts above.", priority: "high" }]);
  const B = c.bb8oShape({ bb8oPath: "/api/brief" }, 200, { brief: { headline: "Stocks slip as chips lead the sell-off", houseView: "BUY", summary: "Chip stocks led a sell-off. Investors should buy the dip. Treasuries rallied.", overweight: ["Gold"], risks: ["Hormuz", "Go long gold as a hedge."] } });
  assert.deepEqual([B.brief.headline, B.brief.houseView, B.brief.summary, B.brief.risks, B.brief.overweight], ["Stocks slip as chips lead the sell-off", "MONITOR", "Chip stocks led a sell-off. Treasuries rallied.", ["Hormuz"], []]);
  assert.equal(B.brief.leadingThemesLabel, "Leading themes"); assert.deepEqual(B.brief.themesExcluded, [{ list: "leading", theme: "Gold", reason: "no measured figure" }]);
  // Errors, other statuses and other routes are untouched.
  const err = { error: "Buy now" }; assert.deepEqual(c.bb8oShape({ bb8oPath: "/api/committee" }, 502, err), { error: "Buy now" });
  for (const route of ["/api/chat", "/api/me", "/api/admin/content", "/api/academy-daily"]) assert.deepEqual(c.bb8oShape({ bb8oPath: route }, 200, { reply: "Buy MU.", verdict: "BUY" }), { reply: "Buy MU.", verdict: "BUY" }, route);
});
test("advice: committee, lenses, intelligence and brief prompts carry the no-advice rule; other prompts do not", async () => {
  const c = load();
  for (const v of ["validateCommitteeResponse", "validateLensesResponse", "validateIntelligenceResponse", "validateBriefResponse"]) await vm.runInContext(`generateAi({ system: "SYS", messages: [], validate: ${v} })`, c);
  await vm.runInContext(`generateAi({ system: "CHAT", messages: [], validate: normaliseChatAnswer })`, c);
  await vm.runInContext(`generateAi({ system: "SYS\\n" + BB8O_NO_ADVICE, messages: [], validate: validateLensesResponse })`, c);
  const sys = c.GEN.map(o => o.system);
  assert.deepEqual(sys.slice(0, 4).map(s => s.endsWith("\n" + c.BB8O_NO_ADVICE) && s.startsWith("SYS")), [true, true, true, true]);
  assert.equal(sys[4], "CHAT"); assert.equal(sys[5].split(c.BB8O_NO_ADVICE).length, 2, "added once");
  assert.match(c.BB8O_NO_ADVICE, /never give a buy, sell, hold/); assert.match(c.BB8O_NO_ADVICE, /price target/);
});

const DESK = [
  ["Highest conviction on desk: XOM (84/100, Bullish).", "Top desk score: XOM 84/100 (Dispatch desk score)."],
  ["Highest conviction on desk: XOM (84/100, Bearish)", "Top desk score: XOM 84/100 (Dispatch desk score)"],
  ["Top pick: NVDA (91/100, Bullish).", "Top desk score: NVDA 91/100 (Dispatch desk score)."],
  ["Highest-conviction name: MU (77/100)", "Top desk score: MU 77/100 (Dispatch desk score)"],
  ["Our top conviction is **TSM** (88/100, Bullish).", "Our Top desk score: TSM 88/100 (Dispatch desk score)."],
  ["XOM highest conviction (84/100) · CVX lowest (40/100)", "Top desk score: XOM 84/100 (Dispatch desk score) · CVX lowest (40/100)"],
  ["Best idea on the desk: AAPL (80/100, n/a)", "Top desk score: AAPL 80/100 (Dispatch desk score)"]
];
test("desk score: 'highest conviction' / 'top pick' become the plain Dispatch desk score; no bullish or bearish call", () => {
  const c = load();
  for (const [inp, out] of DESK) { assert.equal(c.bb8oDeskScore(inp), out, inp); assert.equal(c.bb8oIsAdvice(c.bb8oDeskScore(inp)), false, out); }
  // Without a score there is nothing to restate, so the advice filter drops the sentence instead.
  for (const s of ["Highest conviction: XOM.", "XOM is our top pick.", "High-conviction long in NVDA.", "Best idea this week is gold."]) assert.equal(c.bb8oIsAdvice(s), true, s);
  assert.equal(c.bb8oAdviceText("Gold rose 1.2%. Highest conviction on desk: XOM (84/100, Bullish). XOM is our top pick."), "Gold rose 1.2%. Top desk score: XOM 84/100 (Dispatch desk score).");
  const B = c.bb8oShape({ bb8oPath: "/api/brief" }, 200, { brief: { houseView: "Highest conviction on desk: XOM (84/100, Bullish)", summary: "Fear/Greed: Fear (31/100). Highest conviction on desk: XOM (84/100, Bullish). Research only — not investment advice." } });
  assert.equal(B.brief.houseView, "Top desk score: XOM 84/100 (Dispatch desk score)");
  assert.equal(B.brief.summary, "Fear/Greed: Fear (31/100). Top desk score: XOM 84/100 (Dispatch desk score). Research only — not investment advice.");
  // AI context reaching the model is restated the same way; the question is untouched.
  const b = c.bb8oScrubBody({ question: "Is XOM the highest conviction (84/100) name?", context: "Highest conviction on desk: XOM (84/100, Bullish)." });
  assert.equal(b.question, "Is XOM the highest conviction (84/100) name?"); assert.equal(b.context, "Top desk score: XOM 84/100 (Dispatch desk score).");
});
const OWUW = ["Overweight: Gold, Cash", "Underweight: High-beta tech", "OVERWEIGHT: energy", "**Underweight:** small caps", "Regime: Risk-off | Overweight: Gold, Treasuries | Underweight: High-beta tech"];
function themeCharts(c) {
  c.YCH.SPY = c.bb8oTestSeries([598, 596, 596, 594, 592, 593.42]);   // 5 sessions: 598 -> 593.42 = -0.77%
  c.YCH.GLD = c.bb8oTestSeries([384, 388, 388, 390, 393, 396.33]);   // 384 -> 396.33 = +3.21%
  c.YCH.BIL = c.bb8oTestSeries([91.52, 91.53, 91.53, 91.54, 91.56, 91.59]); // +0.08%
  c.YCH.IEF = c.bb8oTestSeries([95.2, 95.4, 95.4, 95.5, 95.6, 95.93]); // +0.77%
  c.YCH.XLK = c.bb8oTestSeries([281, 276, 276, 272, 270, 268.75]);   // 281 -> 268.75 = -4.36%
  c.YCH.XLE = c.bb8oTestSeries([90, 89, 89, 88, 87, 86]);             // -4.44%: did not lead
}
test("themes: 'Overweight: Gold, Cash' becomes measured, cited Leading themes; unmeasurable themes are left out", async () => {
  const c = load(); themeCharts(c);
  for (const s of OWUW) assert.equal(c.bb8oIsAdvice(s), true, s);
  const L = await c.bb8oThemes(["Gold", "Cash", "Crypto winter", "Energy"], true);
  assert.equal(L.label, "Leading themes");
  assert.deepEqual(L.items.map(x => [x.theme, x.proxy, x.changePct, x.benchmark.changePct, x.relativePct, x.window, x.source.url]),
    [["Gold", "GLD", 3.21, -0.77, 3.98, "5 sessions", "https://finance.yahoo.com/quote/GLD/history/"], ["Cash", "BIL", 0.08, -0.77, 0.85, "5 sessions", "https://finance.yahoo.com/quote/BIL/history/"]]);
  assert.match(L.items[0].text, /^Gold \(GLD\) \+3\.21% vs S&P 500 \(SPY\) −0\.77% over the 5 sessions to Fri 16 Oct \(Yahoo Finance, as of .+ UK\)$/);
  assert.deepEqual(L.excluded.map(x => [x.theme, x.reason]).sort(), [["Crypto winter", "no measured figure"], ["Energy", "did not lead the S&P 500 (SPY) over the window"]]);
  // Cash with no BIL figure is left out rather than listed.
  delete c.YCH.BIL; c.bb8oThemeCache.clear();
  const L2 = await c.bb8oThemes(["Gold", "Cash"], true);
  assert.deepEqual(L2.items.map(x => x.theme), ["Gold"]); assert.deepEqual(L2.excluded, [{ theme: "Cash", reason: "no measured figure" }]);
});
test("themes: brief keeps overweight / underweight keys with the neutral text and adds leadingThemes, laggingThemes and labels", async () => {
  const c = load(); themeCharts(c);
  const br = await c.bb8oBriefThemes({ houseView: "x", overweight: ["Gold", "Cash"], underweight: ["High-beta tech", "Gold"] });
  assert.deepEqual([br.leadingThemesLabel, br.overweightLabel, br.laggingThemesLabel, br.underweightLabel], ["Leading themes", "Leading themes", "Lagging themes", "Lagging themes"]);
  assert.deepEqual(br.overweight, br.leadingThemes.map(x => x.text)); assert.deepEqual(br.underweight, br.laggingThemes.map(x => x.text));
  assert.deepEqual(br.laggingThemes.map(x => [x.theme, x.proxy, x.changePct]), [["High-beta tech", "XLK", -4.36]]);
  assert.deepEqual(br.themesExcluded.map(x => [x.list, x.theme]), [["lagging", "Gold"]]);
  // The response layer leaves a measured brief alone.
  const out = c.bb8oShape({ bb8oPath: "/api/brief" }, 200, { brief: JSON.parse(JSON.stringify(br)) });
  assert.deepEqual(out.brief.overweight, br.overweight);
  // generateAi measures the brief right after the model; other routes are not measured.
  c.NEXTV = { overweight: ["Gold", "Cash"] };
  const r = await vm.runInContext(`generateAi({ system: "S", messages: [], validate: validateBriefResponse })`, c);
  assert.deepEqual(r.validated.leadingThemes.map(x => x.proxy), ["GLD", "BIL"]); assert.equal(r.validated.overweight[0], r.validated.leadingThemes[0].text);
  c.NEXTV = { overweight: ["Gold"] };
  const r2 = await vm.runInContext(`generateAi({ system: "S", messages: [], validate: validateLensesResponse })`, c);
  assert.deepEqual(r2.validated, { overweight: ["Gold"] });
});
test("themes: AI context 'Overweight: …' / 'Underweight: …' segments become measured themes; the question stays byte-identical", async () => {
  const c = load(); themeCharts(c);
  const out = await Promise.all(OWUW.map(s => c.bb8oThemeLine(s)));
  assert.match(out[0], /^Leading themes \(measured, 5 sessions to Fri 16 Oct, vs S&P 500 \(SPY\) −0\.77%; Yahoo Finance, as of .+ UK\): Gold \(GLD\) \+3\.21%, Cash \(BIL\) \+0\.08%$/);
  assert.match(out[1], /^Lagging themes \(measured, .+\): High-beta tech \(XLK\) −4\.36%$/);
  assert.equal(out[2], "", "energy did not lead, so the segment is removed");
  assert.equal(out[3], "", "small caps have no figure in the stub: removed");
  assert.match(out[4], /^Regime: Risk-off \| Leading themes \(.+\): Gold \(GLD\) \+3\.21%, Treasuries \(IEF\) \+0\.77% \| Lagging themes \(.+\): High-beta tech \(XLK\) −4\.36%$/);
  const req = { __body: { question: "Should I go overweight gold? Overweight: Gold, Cash", context: "Regime: Risk-off | Overweight: Gold, Treasuries | Underweight: High-beta tech", messages: [{ role: "user", content: "Overweight: Gold" }] } };
  const b = await c.readBody(req);
  assert.equal(b.question, req.__body.question); assert.deepEqual(b.messages, req.__body.messages);
  assert.match(b.context, /^Regime: Risk-off \| Leading themes/);
  // A body without such a segment makes no Yahoo request at all.
  c.YCALLS.length = 0; await c.readBody({ __body: { question: "Why did MU fall?", context: "MU fell 5.63%." } }); assert.equal(c.YCALLS.length, 0);
});

test("fix A: upstream null change / changePct / prevClose stay null (bb8q / bb8q2 gold spot); junk values still become 0", () => {
  const c = load();
  const spot = { p: 4166.6, c: null, change: null, changePct: null, prev: null, prevClose: null, changeAvailable: false, label: "Gold spot", futuresChange: { symbol: "GC=F", changePct: 0.2, prevClose: 4181.1 }, changeNote: "No spot previous close yet; futures change shown separately." };
  const out = c.bb8oTidy(spot);
  assert.deepEqual([out.c, out.change, out.changePct, out.prev, out.prevClose, out.changeAvailable], [null, null, null, null, null, false]);
  assert.deepEqual(out.futuresChange, spot.futuresChange); assert.equal(out.changeNote, spot.changeNote); assert.equal(out, spot, "nothing to change: same object");
  // changeAvailable:false alone is enough; NaN with no flag is junk and becomes 0 as before
  assert.deepEqual([c.bb8oTidy({ p: 10, c: 0.5, change: 0.05, changeAvailable: false }).c, c.bb8oTidy({ p: 10, c: 0.5, change: 0.05, changeAvailable: false }).change], [null, null]);
  assert.deepEqual([c.bb8oTidy({ p: 10, c: NaN, change: Infinity, prev: 0 }).c, c.bb8oTidy({ p: 10, c: NaN, change: Infinity, prev: 0 }).change], [0, 0]);
  // a null change is never a zero-price failure: the row is valid and passes through the response layer untouched
  assert.equal(c.bb8oValid(spot), true);
  // the zero-price fallback keeps nulls too when the upstream row said "no change"
  const fb = c.bb8oFromLast({ p: 0, c: null, change: null, changeAvailable: false, changeNote: "n", futuresChange: { x: 1 } }, "XAU", { p: 4160, prev: null, ts: 1792400000, tsMs: 1792400000000, src: "gold-api.com" }, "zero-price");
  assert.deepEqual([fb.p, fb.c, fb.change, fb.prev, fb.changeAvailable, fb.changeNote, fb.futuresChange.x, fb.fallback], [4160, null, null, null, false, "n", 1, true]);
  // through the response layer: bb8q's spot row keeps its nulls, futuresChange, changeNote and its feed string (as feedLabel / feed.label)
  const R = c.bb8oShape({ bb8oPath: "/api/market-reference-quotes" }, 200, { XAU: Object.assign({ ts: Math.floor(c.NOW / 1000), feed: "gold-api.com spot (api.gold-api.com/price/XAU)", source: "gold-api-spot-proxy" }, spot) });
  assert.deepEqual([R.XAU.c, R.XAU.change, R.XAU.prev, R.XAU.changeAvailable, R.XAU.changeNote, R.XAU.futuresChange.changePct], [null, null, null, false, spot.changeNote, 0.2]);
  assert.equal(typeof R.XAU.feed, "object"); assert.equal(R.XAU.feed.symbol, "XAU"); assert.equal(R.XAU.feedLabel, "gold-api.com spot (api.gold-api.com/price/XAU)"); assert.equal(R.XAU.feed.label, R.XAU.feedLabel);
  // with a previous close the change is still computed
  const ok = c.bb8oTidy({ p: 110, prev: 100, c: null, change: null });
  assert.deepEqual([Math.round(ok.c * 100) / 100, Math.round(ok.change * 100) / 100], [10, 10]);
});
test("fix B: Leading / Lagging themes are a numbered, citable source in bb8q's shared context when the Ask is about them", async () => {
  const c = load(); themeCharts(c);
  vm.runInContext(`var bb8qSrcText = new WeakMap(); function bb8qSrc(name, link, ms, detail, key) { var s = { name: name, link: link, asOf: new Date(ms).toISOString(), detail: String(detail).slice(0, 400), bb8q: true, bb8qKey: key }; bb8qSrcText.set(s, String(detail)); return s; }
    function bb8pQuestion(b) { return b.question; }`, c);
  const body = { question: "Which themes are leading this week?", context: "Regime: Risk-off | Overweight: Gold, Cash | Underweight: High-beta tech" };
  const ctx = { facts: [{ id: "regime", text: "r", src: { name: "x" } }], sources: [{ name: "x" }], q: body.question };
  await c.bb8oThemeFacts(ctx, body);
  assert.deepEqual(ctx.facts.map(f => f.id), ["regime", "themes"]);
  const th = ctx.facts[1];
  assert.match(th.text, /^Leading and lagging themes \(Dispatch measurement from Yahoo Finance daily closes over the 5 sessions to Fri 16 Oct, against the S&P 500 \(SPY\), which is down 0\.77% over the same window\)\. Leading themes: Gold \(GLD, SPDR Gold Shares\) up 3\.21%; Cash \(BIL, SPDR 1-3 Month T-Bill ETF\) up 0\.08%\. Lagging themes: High-beta tech \(XLK, Technology Select Sector SPDR\) down 4\.36%\. As of Fri 16 Oct, 21:00 UK\.$/);
  assert.equal(th.text.split("0.77%").length, 2, "the SPY figure appears once, in one source");
  assert.equal(ctx.sources[1], th.src); assert.equal(th.src.link, "https://finance.yahoo.com/quote/GLD/history/"); assert.equal(th.src.bb8qKey, "themes");
  assert.deepEqual(th.src.bb8oThemes.map(x => [x.list, x.proxy, x.changePct, x.spyChangePct]), [["leading", "GLD", 3.21, -0.77], ["leading", "BIL", 0.08, -0.77], ["lagging", "XLK", -4.36, -0.77]]);
  assert.equal(c.bb8qSrcText.get(th.src), th.text.replace(/\.$/, ""));
  // idempotent; an unrelated Ask adds nothing and makes no Yahoo request
  await c.bb8oThemeFacts(ctx, body); assert.equal(ctx.facts.length, 2);
  c.YCALLS.length = 0; c.bb8oThemeCache.clear();
  const ctx2 = { facts: [], sources: [], q: "Why did MU fall?" };
  await c.bb8oThemeFacts(ctx2, { question: "Why did MU fall?", context: body.context }); assert.equal(ctx2.facts.length, 0); assert.equal(c.YCALLS.length, 0);
  // naming a theme counts as asking about it
  const ctx3 = { facts: [], sources: [], q: "How has gold done?" };
  await c.bb8oThemeFacts(ctx3, { question: "How has gold done?", context: body.context }); assert.deepEqual(ctx3.facts.map(f => f.id), ["themes"]);
});

// ── QA items folded into the bb8q2 restack ──
test("QA P0: 'Gold spot' only ever carries XAU data; an MU / NVDA / AAPL Pulse Ask never shows gold spot with a non-XAU price", () => {
  const c = load();
  const xau = { bb8qCtx: { spot: { q: { p: 4166.6 } } } };
  for (const [sym, name, p, prev] of [["MU", "Micron Technology, Inc.", 878.84, 931.24], ["NVDA", "NVIDIA Corporation", 181.42, 186.1], ["AAPL", "Apple Inc.", 247.1, 249.0]]) {
    const st = Object.assign({ bb8eMoveR: { base: sym, ysym: sym, q: { p, prev, name } } }, xau);
    const chg = (p - prev).toFixed(2), pct = ((p / prev - 1) * 100).toFixed(2);
    const reply = `${sym} fell ${Math.abs(pct)}% in its last session. [1]\n\nGold spot $${p.toLocaleString("en-US", { minimumFractionDigits: 2 })} ${chg} (${pct}%)`;
    const out = c.bb8oGoldSpotGuard(reply, st);
    assert.equal(/Gold spot[^\n]*\$\s?(?!4,1)/.test(out), false, sym + ": " + out);
    assert.match(out, new RegExp("^" + sym + " \\(" + name.replace(/[.()]/g, "\\$&") + "\\) \\$", "m"), "relabelled with the subject's own symbol and name");
    // a gold spot clause with a price that is neither XAU nor the subject is dropped
    const out2 = c.bb8oGoldSpotGuard(`${sym} fell [1]. Gold spot is at $512.30 today.`, st);
    assert.equal(out2, `${sym} fell [1].`);
  }
  // a gold Ask keeps XAU spot
  const g = "Live: Gold spot is at $4,166.60; no spot previous close is available yet [1]; gold futures (GC=F, delayed 10 min) are up 0.20% at $4,189.50 [2].";
  assert.equal(c.bb8oGoldSpotGuard(g, xau), g);
  assert.equal(c.bb8oGoldSpotGuard("Gold spot (reference) at $4,170.10.", {}), "Gold spot (reference) at $4,170.10.");
  // meta.quote: subject's own label; XAU untouched
  assert.deepEqual(c.bb8oQuoteLabel({ symbol: "MU", name: "Gold spot", label: "Gold spot", price: 878.84 }).label, "MU");
  assert.equal(c.bb8oQuoteLabel({ symbol: "MU", name: "Micron Technology, Inc.", price: 878.84 }).label, "Micron Technology, Inc.");
  assert.equal(c.bb8oQuoteLabel({ symbol: "XAU", name: "Gold spot", label: "Gold spot" }).label, "Gold spot");
});
function hkBars(dup) {
  // Wed 14, Thu 15, Fri 16 Oct 2026 daily bars for 0700.HK (Yahoo stamps 09:30 HKT = 01:30 UTC)
  const ts = [1791941400, 1792027800, 1792114200, 1792200600].map(x => x - 86400);
  const close = dup ? [405.0, 410.2, 417.8, 417.8] : [405.0, 410.2, 412.4, 417.8];
  const high = dup ? [407.0, 412.0, 412.6, 428.8] : [407.0, 412.0, 414.0, 428.8];
  const low = dup ? [401.0, 404.2, 408.0, 415.8] : [401.0, 404.2, 409.0, 415.8];
  return { chart: { result: [{ meta: { currency: "HKD", exchangeTimezoneName: "Asia/Hong_Kong", regularMarketTime: 1792138094, chartPreviousClose: 399.0 }, timestamp: ts, indicators: { quote: [{ close, high, low }] } }] } };
}
test("QA P0: 0700.HK duplicate daily bar: previous distinct session close, Fri change tag; normal series unchanged", async () => {
  const c = load();
  const D = hkBars(true).chart.result[0], N = hkBars(false).chart.result[0];
  assert.deepEqual(c.bb8oDistinctPrev(D, "Asia/Hong_Kong"), { prev: 410.2, fix: "duplicate-bar", prevDay: "2026-10-14", lastDay: "2026-10-16" });
  assert.deepEqual(c.bb8oDistinctPrev(N, "Asia/Hong_Kong"), { prev: 412.4, fix: null, prevDay: "2026-10-15", lastDay: "2026-10-16" });
  // the live 19 Oct shape: Thu and Fri both close 417.80 with ranges that contain it: still the previous distinct close
  const L = JSON.parse(JSON.stringify(D)); L.indicators.quote[0].high = [407.0, 412.0, 422.6, 428.8]; L.indicators.quote[0].low = [401.0, 404.2, 414.0, 415.8];
  assert.deepEqual(c.bb8oDistinctPrev(L, "Asia/Hong_Kong"), { prev: 410.2, fix: "duplicate-bar", prevDay: "2026-10-14", lastDay: "2026-10-16" });
  // the same session date twice (duplicate timestamps) collapses to one bar
  const S = JSON.parse(JSON.stringify(N)); S.timestamp[3] = S.timestamp[2] + 3600; assert.equal(c.bb8oDistinctPrev(S, "Asia/Hong_Kong").prev, 410.2);
  // nothing distinct left: chart meta previous close
  const M = { meta: { previousClose: 411.0 }, timestamp: [1792027800, 1792114200], indicators: { quote: [{ close: [417.8, 417.8], high: [412.6, 428.8], low: [408.0, 415.8] }] } };
  assert.deepEqual(c.bb8oDistinctPrev(M, "Asia/Hong_Kong").prev, 411.0);
  // through yahooQuote: a zero-change row is checked once against the daily bars and fixed
  vm.runInContext(`upstream = async function (u) { UPCALLS.push(u); return { json: async function () { return /0700/.test(u) ? HKC : { chart: { result: [] } }; } }; };`, Object.assign(c, { HKC: hkBars(true) }));
  c.YQ = { "0700.HK": { p: 417.8, prev: 417.8, c: 0, change: 0, ts: 1792138094, currency: "HKD" }, "MU": { p: 878.84, prev: 931.24, c: -5.6269, change: -52.4, ts: 1792180800 } };
  const out = await c.yahooQuote(["0700.HK", "MU"]);
  assert.deepEqual([out["0700.HK"].prev, Math.round(out["0700.HK"].c * 100) / 100, out["0700.HK"].prevFix], [410.2, 1.85, "duplicate-bar"]);
  assert.equal(out["0700.HK"].prevNote, "Previous close is the Wed 14 Oct close (the prior daily bar repeated the last close).");
  assert.deepEqual(out.MU, c.YQ.MU, "normal rows unchanged, no chart read");
  assert.equal(c.UPCALLS.filter(u => /0700/.test(u)).length, 1); assert.equal(c.UPCALLS.filter(u => /MU/.test(u)).length, 0);
  await c.yahooQuote(["0700.HK"]); assert.equal(c.UPCALLS.filter(u => /0700/.test(u)).length, 1, "10-minute memory, no second read");
  // the change tag names the last session's day in Hong Kong time
  const R = c.bb8oShape({ bb8oPath: "/api/yahoo-quote" }, 200, { "0700.HK": out["0700.HK"] });
  assert.deepEqual([R["0700.HK"].changeDay, R["0700.HK"].changeDayLabel, R["0700.HK"].feed.changeDay], ["Fri", "Fri 16 Oct", "Fri"]);
});
test("QA P2: BTC has one canonical rolling-24h baseline (CoinGecko 24h when fresh, else Yahoo rolling 24h), labelled 24h", () => {
  const c = load();
  const now = Date.now();
  vm.runInContext(`var coinGeckoLastGood = new Map(); var coinGeckoLastGoodAt = new Map();`, c);
  const row = { p: 104200, prev: 103784, c: 0.4008, change: 416, ts: Math.floor(now / 1000), basis: "rolling_24h" };
  let R = c.bb8oShape({ bb8oPath: "/api/yahoo-quote" }, 200, { "BTC-USD": Object.assign({}, row) });
  assert.deepEqual([R["BTC-USD"].baseline, R["BTC-USD"].baselineSource, Math.round(R["BTC-USD"].change)], ["24h", "Yahoo 15-minute bars, rolling 24h", 416]);
  c.coinGeckoLastGood.set("/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true", { bitcoin: { usd: 104150, usd_24h_change: 0.5363, last_updated_at: Math.floor(now / 1000) - 60 } });
  for (const route of ["/api/yahoo-quote", "/api/market-reference-quotes", "/api/twelve-data-quote"]) {
    const td = route === "/api/twelve-data-quote";
    R = c.bb8oShape({ bb8oPath: route }, 200, td ? { quotes: { "BTC-USD": Object.assign({}, row) } } : { "BTC-USD": Object.assign({}, row) });
    const b = td ? R.quotes["BTC-USD"] : R["BTC-USD"];
    assert.deepEqual([b.baseline, b.baselineSource, b.changePct, b.c, Math.round(b.change)], ["24h", "CoinGecko 24h change", 0.5363, 0.5363, 556], route);
    assert.match(b.asOfUk, / UK$/);
  }
  // stale CoinGecko (over 10 minutes): back to the Yahoo rolling 24h basis
  c.coinGeckoLastGood.set("/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true", { bitcoin: { usd: 104150, usd_24h_change: 0.5363, last_updated_at: Math.floor(now / 1000) - 3600 } });
  R = c.bb8oShape({ bb8oPath: "/api/yahoo-quote" }, 200, { "BTC-USD": Object.assign({}, row) });
  assert.equal(R["BTC-USD"].baselineSource, "Yahoo 15-minute bars, rolling 24h");
  // stocks are untouched
  R = c.bb8oShape({ bb8oPath: "/api/yahoo-quote" }, 200, { MU: { p: 878.84, prev: 931.24, c: -5.6269, change: -52.4, ts: 1792180800 } });
  assert.equal(R.MU.baseline, undefined);
});
test("QA P2: brief edition carries a dated label and a UK-time edition name; the edition id stays stable", () => {
  const c = load();
  const ed = { id: "2026-10-19.1-abc123", day: "2026-10-19", seq: 1, reason: "cold-start", startedAt: Date.parse("2026-10-19T07:40:00Z"), lead: { h: "x", src: "s", link: "l", t: 0, as: [], coverage: 1, sources: ["s"] }, also: [] };
  const at = (iso) => c.bb8oEditionOut(ed, Date.parse(iso));
  assert.deepEqual([at("2026-10-19T10:59:00Z").label, at("2026-10-19T11:00:00Z").label, at("2026-10-19T15:59:00Z").label, at("2026-10-19T16:00:00Z").label],
    ["Mon 19 Oct · Morning edition", "Mon 19 Oct · Afternoon edition", "Mon 19 Oct · Afternoon edition", "Mon 19 Oct · Evening edition"]);
  assert.equal(at("2026-10-19T12:10:00Z").dayLabel, "Mon 19 Oct");
  assert.deepEqual([...new Set(["10:59", "11:00", "16:00"].map(h => at("2026-10-19T" + h + ":00Z").editionId))], ["2026-10-19.1-abc123"]);
  const B = c.bb8oShape({ bb8oPath: "/api/brief", bb8oEdition: at("2026-10-19T12:10:00Z") }, 200, { brief: { date: "2026-10-19", headline: "h" } });
  assert.deepEqual([B.brief.date, B.brief.dateLabel, B.brief.editionLabel], ["2026-10-19", "Mon 19 Oct", "Mon 19 Oct · Afternoon edition"]);
});
test("QA P2: static desk thesis and rating / sentiment words in page context never reach the model; the question is untouched", () => {
  const c = load();
  const ctx = "Page: Ticker\nActive ticker: NVDA NVIDIA · Score 76/100 · Bullish · Strong Buy · $181.42 (-2.51%) · Beta 1.72 · 52.8x\nPlatform thesis: AI infrastructure spend accelerating. Data center revenue dominant. TSMC Q1 confirms demand strength. Elevated valuation justified by 90%+ growth.\nLive price: $181.42 (-2.51%) [feed]";
  const b = c.bb8oScrubBody({ question: "Is NVDA's valuation justified by growth? Platform thesis: TSMC Q1 confirms demand.", context: ctx });
  assert.equal(b.question, "Is NVDA's valuation justified by growth? Platform thesis: TSMC Q1 confirms demand.");
  assert.equal(b.context, "Page: Ticker\nActive ticker: NVDA NVIDIA · Score 76/100 · $181.42 (-2.51%) · Beta 1.72 · 52.8x\nLive price: $181.42 (-2.51%) [feed]");
  assert.equal(/TSMC Q1 confirms|Elevated valuation justified|Strong Buy|Bullish/.test(b.context), false);
});

const ET = (iso) => Date.parse(iso); // ET offsets in Oct 2026: UTC-4
test("protocol: names, no timers, anchors, refuse marker, dry run", () => {
  const fns = [...B8O.matchAll(/(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(m => m[1]);
  assert.ok(fns.length > 40);
  assert.deepEqual(fns.filter(n => !n.startsWith("bb8o")), []);
  const vars = [...B8O.matchAll(/(?:^|\n)var\s+([A-Za-z0-9_$]+)/g)].map(m => m[1]);
  assert.deepEqual(vars.filter(n => !/^(bb8o|BB8O_)/.test(n)), []);
  assert.equal(/setInterval\(|setTimeout\(|CREATE TABLE|\.tier\b|stripe/i.test(B8O), false);
  assert.match(PATCH, /REFUSE: bb8o already applied/);
  assert.match(PATCH, /"--check" in sys\.argv/);
  assert.match(PATCH, /"server\.js": "af877dde4d73f4c19eeff011a0e98f89"/);
  assert.match(PATCH, /\/\/ BB8Q2_JS_END/, "stacked after the bb8q2 block"); assert.match(PATCH, /stacked directly on bb8q2/);
  assert.equal(/BB8P_JS"\)|bb8pFigs\(|bb8pHayOf\(/.test(B8O), false, "bb8p's guard is not modified");
  assert.equal(/sec\.gov|edgar/i.test(B8O), false, "no new SEC requests");
});

// ── QA 1:44 (P0 a, P1 c–i): the answer post-pass, with bb8q's own document helpers (parse / token / render) ──
const PQ = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8q.py"), "utf8");
const fnSrc = (src, name) => { const a = src.indexOf("\nfunction " + name + "("); assert.ok(a >= 0, name); return src.slice(a + 1, src.indexOf("\n}\n", a) + 3); };
function loadQ() {
  const c = load();
  vm.runInContext(["bb8qParse", "bb8qTok", "bb8qRender", "bb8qNum", "bb8qDayName", "bb8qIso", "bb8qSrc"].map(n => fnSrc(PQ, n)).join("\n") +
    "\nfunction bb8qUk(ms) { return bb8dUk(ms); }\nvar bb8qSrcText = new WeakMap();\nfunction bb2Footer(s) { return s && s.length ? \"\\n\\nSources:\\n\" + s.map(function (x, i) { return \"[\" + (i + 1) + \"] \" + x.name; }).join(\"\\n\") : \"\"; }\n", c);
  return c;
}
// the bb8qFinish wrapper's own steps (the same function both /api/chat paths call through bb8jAssemble)
function finish(c, reply, sources, st) {
  const doc = c.bb8qParse({ reply, sources });
  doc.body = c.bb8oGoldSpotGuard(doc.body, st);
  const stat = c.bb8oPost(doc, st);
  const r = c.bb8qRender(doc); r.sources.forEach(c.bb8oSrcLabel);
  return { reply: r.reply.split("\n\nSources:")[0], sources: r.sources, stat };
}
const SRC = (c, name, detail, key, ms) => c.bb8qSrc(name, "https://finance.yahoo.com/", ms || Date.parse("2026-10-19T12:39:00Z"), detail, key);

test("QA P0 (a): gold YTD direction and % come from the two cited numbers; the exact QA case is corrected on both paths", () => {
  const c = loadQ();
  // the exact QA case: start 3,341.10, now ~4,185.90 (+25%); the answer said "down"
  const dirs = [{ from: 3341.10, to: 4185.90, pct: (4185.90 / 3341.10 - 1) * 100 }];
  const qa = "Year to date (from the Wed 31 Dec close of $3,341.10), gold futures (GC=F) are down 3.52%.";
  const r = c.bb8oDirFix(qa, dirs);
  assert.equal(r.fixed, true);
  assert.equal(r.s, "Year to date (from the Wed 31 Dec close of $3,341.10), gold futures (GC=F) are up 25.29%.");
  // explicit start and end in the sentence; a right claim is untouched; verbs flip too
  assert.equal(c.bb8oDirFix("Gold fell 25.29% from $3,341.10 to $4,185.90 this year.", []).s, "Gold rose 25.29% from $3,341.10 to $4,185.90 this year.");
  const ok = "MU fell 5.63% to $878.84 in its last session (previous close $931.24).";
  assert.equal(c.bb8oDirFix(ok, []).fixed, false);
  assert.equal(c.bb8oDirFix("MU rose 5.63% to $878.84 in its last session (previous close $931.24).", []).s, ok);
  // the context line is computed in code: both numbers, direction and % (never from model text)
  const ctx = { tf: { id: "ytd", sym: "GC=F", text: "Year to date, from last year's final close of $3,341.10 (Wed 31 Dec) to $4,185.90 now, gold futures (GC=F) are down 3.52% (Yahoo Finance daily closes, as of Mon 19 Oct, 13:29 UK)." },
    tfMore: ["This month (from the Wed 30 Sept close of $4,186.70), gold futures (GC=F) are up 0.02%."], facts: [] };
  ctx.tf.src = SRC(c, "Yahoo Finance chart", ctx.tf.text, "tf"); ctx.facts.push({ id: "tf:ytd", text: ctx.tf.text, src: ctx.tf.src });
  c.bb8oDirCtx(ctx);
  assert.match(ctx.tf.text, /to \$4,185\.90 now, gold futures \(GC=F\) are up 25\.29%/);
  assert.equal(ctx.tfMore[0], "This month (from the Wed 30 Sept close of $4,186.70 to $4,185.90 now), gold futures (GC=F) are down 0.02%.");
  assert.equal(ctx.facts[0].text, ctx.tf.text);
  assert.match(ctx.tf.src.detail, /up 25\.29%/);
  // the post-pass on the final document (stream and JSON call the same function): corrected, cited, counted
  const st = { bb8qCtx: Object.assign(ctx, { q: "How has gold done this year?" }) };
  const out = finish(c, "Gold spot is at $4,163.60. [1]\n\n" + qa + " [2]\n\nIn short: gold is higher this year. [2]", [SRC(c, "gold-api.com", "Gold spot is at $4,163.60", "spot"), ctx.tf.src], st);
  assert.match(out.reply, /\(from the Wed 31 Dec close of \$3,341\.10\), gold futures \(GC=F\) are up 25\.29%\. \[2\]/);
  assert.doesNotMatch(out.reply, /down 3\.52/);
  assert.equal(out.stat.dir, 1);
  // a direction claim on a start figure no source carries is dropped, not "corrected"
  const out2 = finish(c, "Gold spot is at $4,163.60. [1] Gold is up 9.00% from $4,600.00 to $4,185.90. [1]", [SRC(c, "gold-api.com", "Gold spot is at $4,163.60, futures $4,185.90", "spot")], { bb8qCtx: { q: "gold?" } });
  assert.doesNotMatch(out2.reply, /4,600|9\.00/);
  assert.match(out2.reply, /^Gold spot is at \$4,163\.60\. \[1\]$/);
});

test("QA P1 (c): intent beats template: MU beta / P/E / dividend answer first with the cited value and source", () => {
  const c = loadQ();
  const move = SRC(c, "Yahoo Finance quote", "MU, SPY, SOXX last price and session change", "move");
  const beta = SRC(c, "Yahoo Finance key statistics", "MU beta (5Y monthly) 2.23", "beta");
  const tmpl = "MU's latest move, as of Fri 16 Oct, 21:00 UK:\nMU fell 5.63% to $878.84 in its last session (previous close $931.24). [1]\nMU's published beta is 2.23 (Yahoo Finance, 5-year monthly), so it has tended to move about 2.23 times as much as the market. [2]\n\nIn short: MU fell 5.63%; no confirmed cause. [1]";
  const b = finish(c, tmpl, [move, beta], { bb8qCtx: { q: "What is Micron's beta?" } });
  assert.match(b.reply, /^MU's published beta is 2\.23 \(Yahoo Finance, 5-year monthly\)[^\n]*\[1\]\n\nMU's latest move/);
  assert.equal(b.stat.moved, "beta");
  // P/E: the header plus its first P/E line already lead, so nothing moves
  const pe = SRC(c, "Yahoo Finance", "trailing P/E (TTM) and forward P/E, refreshed on request", "val");
  const p = finish(c, "Peer comparisons as of Fri 16 Oct, 21:00 UK:\nMU trailing P/E (TTM) 11.8x is lower than NVDA trailing P/E (TTM) 27.1x by 15.3x (56.5%).\n\nMU forward P/E (next 12 months) 4.9x is lower than NVDA forward P/E (next 12 months) 15.3x by 10.4x (68.0%). [1]", [pe], { bb8qCtx: { q: "What is Micron's P/E ratio?" } });
  assert.match(p.reply, /^Peer comparisons as of Fri 16 Oct, 21:00 UK:\nMU trailing P\/E \(TTM\) 11\.8x [^\n]*\(56\.5%\)\. \[1\]/);   // every P/E sentence carries its own [n]
  // dividend: no sentence answers it, so the server's cited dividend fact leads
  const dv = SRC(c, "Yahoo Finance key statistics", "MU pays a dividend of $0.60 a share a year, a yield of 0.07% (Yahoo Finance, summary detail)", "bb8o:metric");
  const d = finish(c, tmpl, [move, beta], { bb8qCtx: { q: "Does Micron pay a dividend?", bb8oMetric: { id: "dividend", text: "MU pays a dividend of $0.60 a share a year, a yield of 0.07% (Yahoo Finance, summary detail).", src: dv } } });
  assert.match(d.reply, /^MU pays a dividend of \$0\.60 a share a year, a yield of 0\.07% \(Yahoo Finance, summary detail\)\. \[1\]\n\nMU's latest move/);
  assert.equal(d.sources[0], dv);
  // a non-factual question keeps the template order
  assert.match(finish(c, tmpl, [move, beta], { bb8qCtx: { q: "Why did MU fall?" } }).reply, /^MU's latest move/);
});

test("QA P1 (d): 'this week' gets an outlook from cited levels and scheduled dates only; one line when nothing is citable", () => {
  const c = loadQ();
  const fut = SRC(c, "Yahoo Finance quote", "Gold futures (GC=F) 5 completed sessions high $4,242.30, low $4,095.00", "futures");
  const lv = { n: 5, label: "gold futures (GC=F)", low: 4095, high: 4242.3, span: "sessions Mon 12 Oct to Fri 16 Oct", src: fut, fmt: v => "$" + c.bb8qNum(v, 2) };
  const r = finish(c, "Gold futures are up 0.05%. [1]\n\nGold will probably test $4,300 this week.\n\nIn short: gold is flat. [1]", [fut], { bb8qCtx: { q: "What's the outlook for gold this week?", bb8oLevels: lv } });
  assert.match(r.reply, /Outlook for this week \(from our data, not a forecast\): the 5-session range for gold futures \(GC=F\) is \$4,095\.00 \(low\) to \$4,242\.30 \(high\), sessions Mon 12 Oct to Fri 16 Oct \[1\]\. No scheduled Fed, economic-data or earnings dates for this week are in our feed\.\n\nIn short:/);
  assert.doesNotMatch(r.reply, /4,300/);                       // the invented forecast is gone (uncited)
  const ev = SRC(c, "Yahoo Finance", "MU next earnings date (Yahoo Finance calendarEvents, estimated)", "earn");
  const r2 = finish(c, "MU fell 5.63%. [1]", [SRC(c, "Yahoo Finance quote", "MU fell 5.63%", "move")], { bb8qCtx: { q: "What's the outlook for MU this week?", bb8oEvents: [{ text: "MU next earnings: Wed 21 Oct 2026 (estimated)", src: ev }] } });
  assert.match(r2.reply, /Outlook for this week \(from our data, not a forecast\): MU next earnings: Wed 21 Oct 2026 \(estimated\) \[2\]\.$/);
  const r3 = finish(c, "Gold futures are up 0.05%. [1]", [fut], { bb8qCtx: { q: "What happens to gold this week?" } });
  assert.match(r3.reply, /\n\nOutlook for this week: nothing in our feed is citable for the week ahead \(no scheduled Fed, data or earnings dates and no measured range\), so we give no outlook\.$/);
  assert.doesNotMatch(finish(c, "Gold futures are up 0.05%. [1]", [fut], { bb8qCtx: { q: "How is gold today?" } }).reply, /Outlook/);
});

test("QA P1 (e/f/g/h/i): citation hygiene, proxy labels, headline as-of, one S&P figure, source title/label (QA China JSON case)", () => {
  const c = loadQ();
  const cnh = SRC(c, "Yahoo Finance quote", "USD/CNH (offshore yuan) (USDCNH=X) is down 0.07% at 6.6808, as of Mon 19 Oct, 13:31 UK", "USDCNH=X", Date.parse("2026-10-19T12:31:00Z")); cnh.bb8qProxy = { sym: "USDCNH=X", label: "USD/CNH (offshore yuan)" };
  const hsi = SRC(c, "Yahoo Finance quote", "The Hang Seng (^HSI) rose 0.52% in its last session, to 24,186.83", "^HSI", Date.parse("2026-10-16T08:08:00Z")); hsi.bb8qProxy = { sym: "^HSI", label: "the Hang Seng" };
  const vix = SRC(c, "Yahoo Finance quote", "VIX (CBOE volatility index) (^VIX) fell 7.05% in its last session, to 18.58", "^VIX");
  const reg = SRC(c, "Dispatch regime model", "Our regime model (The Dispatch): Risk-Off, score 37/100", "regime");
  const spx = SRC(c, "Yahoo Finance quote", "S&P 500 (^GSPC) fell 1.09% in its last session, to 7,659.44", "^GSPC");
  const spy = SRC(c, "Yahoo Finance quote", "MU, SPY, SOXX last price and session change: SPY down 1.11%", "move");
  const reply = [
    "We don't have China GDP figures in our data feed right now, so this answer does not quote any.",
    "",
    "What we do have, from Yahoo Finance as of Mon 19 Oct, 13:30 UK: USD/CNH (offshore yuan) is down 0.07% at 6.6808 [1]; the Hang Seng rose 0.52% in its last session, to 24,186.83 [2].",
    "The VIX, which measures market volatility, fell by 7.05% to 18.58, suggesting a slight easing in market fears [3]. The offshore yuan (USD/CNH) is down 0.07% at 6.6808, which may reflect ongoing pressures in the Chinese economy [1]. Additionally, the Hang Seng index rose by 0.52% in its last session, which could indicate some resilience [2]. This shift aligns with a broader trend of seeking safety amid uncertainty, which may be influenced by geopolitical developments and inflation expectations [4]. The market is in a Risk-Off regime with a score of 37/100. [4] As the market continues to navigate these conditions, it will be important to monitor any forthcoming economic data from China. The focus will likely remain on defensive sectors.",
    "SPY (S&P 500 ETF) fell 1.11% in the same session, so gold outperformed. [6] The S&P 500 (^GSPC) fell 1.09% in its last session, to 7,659.44. [5]",
    "",
    "In short: no China GDP figures in our feed; related live markets are above."
  ].join("\n");
  const out = finish(c, reply, [cnh, hsi, vix, reg, spx, spy], { bb8qCtx: { q: "What did the latest China GDP data show?" } });
  const R = out.reply;
  for (const gone of [/geopolitic/, /seeking safety/, /important to monitor/, /defensive sectors/, /which may reflect/, /resilience/, /suggesting a slight easing/, /7,659\.44/]) assert.doesNotMatch(R, gone, String(gone));
  assert.equal((R.match(/6\.6808/g) || []).length, 1, "USD/CNH once");
  assert.equal((R.match(/24,186\.83|0\.52%/g) || []).length, 2, "HSI once (figure and level in one clause)");
  assert.match(R, /What we do have, as proxies, from Yahoo Finance as of Mon 19 Oct, 13:31 UK:/);      // (f) + (g): source time 13:31 ≥ 13:30
  assert.match(R, /The market is in a Risk-Off regime with a score of 37\/100\. \[\d\]/);               // regime cited only for its score
  assert.match(R, /The VIX, which measures market volatility, fell by 7\.05% to 18\.58 \[\d\]\./);
  assert.match(R, /SPY \(S&P 500 ETF\) fell 1\.11%/);                                                  // (h) one S&P figure
  R.split("\n").forEach(l => { if (!l.trim() || /^In short:|^We don't have/.test(l)) return; c.bb8oSplit(l.replace(/\[(\d+)\]/g, "\u27e6$1\u27e7")).forEach(s => assert.match(s, /\u27e6\d+\u27e7/, "every claim sentence has its own [n]: " + s)); });
  // every source the answer lists has a title and a label, and keeps its name
  out.sources.forEach(s => { assert.ok(s.name && s.title && s.label, JSON.stringify(s)); });
  assert.equal(out.sources.find(s => s === cnh).label, "USD/CNH (offshore yuan) (USDCNH=X) (proxy)");
  assert.equal(out.sources.find(s => s === reg).title, "Dispatch regime model · Regime model (The Dispatch)");
  // GBP/USD proxy sentence gets the in-text label
  const gbp = SRC(c, "Yahoo Finance quote", "GBP/USD (GBPUSD=X) is down 0.06% at 1.3322", "GBPUSD=X"); gbp.bb8qProxy = { sym: "GBPUSD=X", label: "GBP/USD" };
  assert.match(finish(c, "We don't have UK inflation figures in our data feed right now.\n\nGBP/USD is down 0.06% at 1.3322. [1]", [gbp], { bb8qCtx: { q: "UK inflation?" } }).reply, /\nAs a proxy, GBP\/USD is down 0\.06% at 1\.3322\. \[1\]/);
});

test("QA P1 (e): stream == JSON drops: the same model text gives byte-identical documents and sources on both paths", () => {
  const c = loadQ();
  const mk = () => { const s = SRC(c, "Yahoo Finance quote", "S&P 500 (^GSPC) fell 1.09% in its last session, to 7,659.44", "^GSPC"); const r = SRC(c, "Dispatch regime model", "Our regime model: Risk-Off, score 37/100", "regime"); return [s, r]; };
  const text = "The S&P 500 (^GSPC) fell 1.09% in its last session, to 7,659.44. [1] This reflects geopolitical developments. [2] Investors should watch central bank statements.\n\nIn short: stocks fell. [1]";
  const a = finish(c, text, mk(), { stream: true, bb8qCtx: { q: "How did stocks do?" } }), j = finish(c, text, mk(), { stream: false, bb8qCtx: { q: "How did stocks do?" } });
  assert.equal(a.reply, j.reply);
  assert.deepEqual(a.sources.map(s => [s.name, s.title, s.label, s.detail]), j.sources.map(s => [s.name, s.title, s.label, s.detail]));
  assert.deepEqual(a.stat.dropped, j.stat.dropped);
  assert.equal(a.reply, "The S&P 500 (^GSPC) fell 1.09% in its last session, to 7,659.44. [1]\n\nIn short: stocks fell. [1]");
});
