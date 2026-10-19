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
  // non-finite change on a valid price: basis none, c 0
  const t2 = c.bb8oShape({ bb8oPath: "/api/market-reference-quotes" }, 200, { DXY: { p: 101.9, prev: null, c: null, change: null, ts: 1 } });
  assert.equal(t2.DXY.c, 0); assert.equal(t2.DXY.basis, "none"); assert.equal(t2.DXY.changeAvailable, false);
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
  assert.deepEqual(Object.keys(a).sort(), ["ageSec", "asOf", "asOfUk", "delayMin", "fallback", "market", "reason", "sessionDate", "sessionDayUk", "sessionLabel", "source", "status", "symbol", "v"]);
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

const BANNED = /^(target(High|Low|Mean|Median)(Price)?|priceTargets?|targetPrice|recommendation(Key|Mean|Trend|s)?|upgradeDowngradeHistory|upgrades|downgrades|numberOfAnalystOpinions|(average|consensus)?(analyst)?ratings?|analystRatings?|ra)$/i;
function keyScan(o, path, hits) { if (!o || typeof o !== "object") return hits; for (const k of Object.keys(o)) { if (BANNED.test(k)) hits.push(path + "." + k); keyScan(o[k], path + "." + k, hits); } return hits; }
test("ratings: one sanitizer strips analyst ratings and price targets at the source, the cache, responses and AI bodies", async () => {
  const c = load();
  const y = await c.rt32Yahoo("NVDA");
  assert.deepEqual(keyScan(y, "y", []), []);
  assert.equal(y.financialData.profitMargins.raw, 0.5, "other fields kept");
  c.RT32.cache.set("NVDA", { at: 1, data: { valuation: { price: 100, pe: 30, targetMean: 250, recommendation: "buy" }, metrics: { peRatio: 30 } } });
  assert.deepEqual(keyScan(c.RT32.cache.get("NVDA"), "cache", []), []);
  assert.equal(c.RT32.cache.get("NVDA").data.valuation.pe, 30);
  const body = { symbol: "BP.L", valuation: { price: 619.5, targetMean: 638.06, recommendation: "buy" }, priceTarget: { targetHigh: 1 }, recommendations: [{ buy: 3 }], upgrades: [], nested: [{ deep: { rating: "Buy", averageAnalystRating: "1.8 - Buy", ok: 1 } }] };
  const out = c.bb8oShape({ bb8oPath: "/api/financials" }, 200, body);
  assert.deepEqual(keyScan(out, "body", []), []);
  assert.equal(out.valuation.price, 619.5); assert.equal(out.nested[0].deep.ok, 1);
  const ask = { messages: [{ role: "user", content: "Why is NVDA moving?" }], context: "Ticker: NVDA (NVIDIA)\nAI score: 76/100 | Sentiment: Bullish | Rating: Strong Buy\nActive ticker: NVDA NVIDIA · Score 76/100 · Bullish · Strong Buy · $182.10 · Beta 1.72 · 52.8x\nAnalysts' mean price target is $250.00 (40 analysts), consensus rating Buy. Revenue grew 50%. The street recommendation is Outperform.", tickers: [{ tk: "NVDA", ra: "Strong Buy", targetMean: 250, sc: 76 }] };
  const b1 = await c.readBody({ __body: ask }), b2 = await c.bb2Read0({ __body: ask });
  for (const b of [b1, b2]) {
    assert.deepEqual(keyScan(b, "ask", []), []);
    assert.equal(/Strong Buy|Rating:|rating Buy|Outperform|price target|\$250/i.test(JSON.stringify(b)), false, JSON.stringify(b));
    assert.match(b.context, /Sentiment: Bullish/); assert.match(b.context, /Score 76\/100 · Bullish · \$182\.10/); assert.match(b.context, /Revenue grew 50%/);
    assert.equal(b.messages[0].content, "Why is NVDA moving?"); assert.equal(b.tickers[0].sc, 76);
  }
  // cycles and non-objects are safe
  const cyc = { a: 1 }; cyc.self = cyc; c.bb8oStripRatings(cyc); assert.equal(cyc.a, 1);
  assert.equal(c.bb8oStripRatings(null), null);
});

test("protocol: names, no timers, anchors, refuse marker, dry run", () => {
  const fns = [...B8O.matchAll(/(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(m => m[1]);
  assert.ok(fns.length > 40);
  assert.deepEqual(fns.filter(n => !n.startsWith("bb8o")), []);
  const vars = [...B8O.matchAll(/(?:^|\n)var\s+([A-Za-z0-9_$]+)/g)].map(m => m[1]);
  assert.deepEqual(vars.filter(n => !/^(bb8o|BB8O_)/.test(n)), []);
  assert.equal(/setInterval\(|setTimeout\(|CREATE TABLE|\.tier\b|stripe/i.test(B8O), false);
  assert.match(PATCH, /REFUSE: bb8o already applied/);
  assert.match(PATCH, /"--check" in sys\.argv/);
  assert.match(PATCH, /"server\.js": "9b48a917c654891a50e7c7c6bd8c9a49"/);
  assert.equal(/bb8p/i.test(PATCH), false, "no anchor on bb8p code");
  assert.equal(/sec\.gov|edgar/i.test(B8O), false, "no new SEC requests");
});
