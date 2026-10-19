// Offline tests for deploy/patch_bb8r.py. Loads the bb8r block in a vm with stubs.
// No network, no live server.js, no server start.
const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { spawnSync } = require("node:child_process");

const PATCH = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8r.py"), "utf8");
const B8R = PATCH.slice(PATCH.indexOf("// \u2500\u2500 bb8r \u2500\u2500"), PATCH.indexOf("// BB8R_JS_END") + 14);
assert.match(B8R, /function bb8rQuoteMeta\(/);
const PQ = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb8q.py"), "utf8");
const fnSrc = (src, name) => {
  const a = src.indexOf("\nfunction " + name + "(");
  assert.ok(a >= 0, name);
  return src.slice(a + 1, src.indexOf("\n}\n", a) + 3);
};

const FRI = 1792138094; // Fri 16 Oct 2026 08:08:14 UTC = 16:08 HKT
const SH = 15453548807;
const PX = 622;
const MC = 96121077760; // Yahoo price.marketCap and summaryDetail.marketCap, already GBP

const STUBS = `
var MOOD = { regime: "Risk-On (Fragile)", score: 55 };
var YSUM = null;
var YQ = {};
var FETCHES = [];
var PAGES = {};
function bb3Mood() { return { regime: MOOD.regime, score: MOOD.score }; }
function bb8qUk() { return "Mon 19 Oct, 14:40 UK"; }
function bb8dUk() { return bb8qUk(); }
function bb8pQuoteMeta(st) {
  var pack = st && st.bb8eMoveR;
  if (!pack || !pack.q) return { label: "Gold spot", name: "Gold spot", price: 909.09, change: 3.44, prevClose: 878.84, currency: "USD", asOfUk: "Mon 19 Oct, 14:40 UK" };
  return { symbol: pack.base, name: "Gold spot", label: "Gold spot", price: Number(pack.q.p), change: Number(pack.q.c), prevClose: Number(pack.q.prev), currency: pack.q.currency || "USD", asOfUk: "Mon 19 Oct, 14:40 UK", source: "Yahoo Finance" };
}
function bb8pMetaFix(meta, admin, st) {
  var m = Object.assign({}, meta || {});
  m.quote = bb8pQuoteMeta(st);
  return m;
}
function bb8oProfileFrom(sym) {
  return { symbol: sym, marketCap: ${MC} * 2, marketCapCurrency: "GBp", marketCapText: "GBp 192.2bn", price: ${PX}, asset: { mc: "GBp 192.2bn" } };
}
async function bb8lYahooShared() { return YSUM; }
async function bb8qBuild(st) {
  if (st && st.bb8eBase && YSUM) await bb8lYahooShared(st.bb8eBase);
  return st.bb8qCtx;
}
function bb8qFinish(out) { return out; }
async function yahooQuote() { return JSON.parse(JSON.stringify(YQ)); }
async function marketReferenceQuotes() { return { XAU: { p: 1 } }; }
async function fetch(url) {
  FETCHES.push(String(url));
  var html = PAGES[String(url)] || "";
  if (!html) return { ok: false, text: async function () { return ""; } };
  return { ok: true, text: async function () { return html; } };
}
function bb2Footer(s) { return s && s.length ? "\\n\\nSources:\\n" + s.map(function (x, i) { return "[" + (i + 1) + "] " + x.name; }).join("\\n") : ""; }
`;

function load() {
  const ctx = { console, Date, JSON, Math, Object, String, Number, Array, RegExp, Promise, URL, Map, WeakMap, Intl, isFinite, encodeURIComponent };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(STUBS, ctx);
  vm.runInContext("var bb8qSrcText = new WeakMap();\n" + ["bb8qIso", "bb8qSrc", "bb8qParse", "bb8qTok", "bb8qRender"].map(n => fnSrc(PQ, n)).join("\n"), ctx);
  vm.runInContext(B8R, ctx, { filename: "bb8r.js" });
  return ctx;
}
function finish(c, reply, sources, st) {
  const r = c.bb8qFinish({ reply, sources }, st || { bb8qCtx: { q: "" } });
  return { reply: String(r.reply).split("\n\nSources:")[0], sources: r.sources, raw: r.reply };
}
const pack = (base, name, extra) => ({
  base, ysym: base, ms: 1,
  q: Object.assign({ p: 909.09, prev: 878.84, c: 3.44, change: 30.25, name, currency: "USD" }, extra || {})
});

test("P0 footer: MU, NVDA and AAPL labels are the subject on the stream meta event and the JSON body", () => {
  const c = load();
  const cases = [
    ["MU", "Micron Technology, Inc.", "Micron Technology", 909.09, 878.84, 30.25, 3.44],
    ["NVDA", "NVIDIA Corporation", "NVIDIA", 181.42, 186.1, -4.68, -2.51],
    ["AAPL", "Apple Inc.", "Apple", 226.5, 224.1, 2.4, 1.07]
  ];
  for (const [sym, yahoo, label, p, prev, ch, pct] of cases) {
    const st = { bb8eBase: sym, bb8eMoveR: pack(sym, yahoo, { p, prev, change: ch, c: pct, name: yahoo }) };
    const stream = c.bb8pQuoteMeta(st);
    const json = c.bb8pMetaFix({ provider: "x" }, false, st);
    for (const q of [stream, json.quote]) {
      assert.equal(q.label, label, sym);
      assert.equal(q.name, label, sym);
      assert.equal(q.quoteLine, label + " $" + c.bb8rPx(p) + " " + c.bb8rSigned(ch, 2) + " (" + c.bb8rSigned(pct, 2) + "%) · Mon 19 Oct, 14:40 UK");
      assert.equal(/gold spot/i.test(q.label + " " + q.quoteLine), false, sym);
    }
  }
  const mu = { bb8eBase: "MU" };
  const prior = c.bb8pQuoteMeta(mu);
  assert.equal(prior.label, "Micron Technology");
  const fixed = c.bb8rQuoteMeta(mu, { label: "Gold spot", name: "Gold spot", price: 909.09, change: 3.44, prevClose: 878.84, currency: "USD", asOfUk: "Mon 19 Oct, 14:40 UK" });
  assert.equal(fixed.label, "Micron Technology");
  assert.match(fixed.quoteLine, /^Micron Technology \$909\.09 \+30\.25 \(\+3\.44%\)/);
  const body = finish(c, "Gold spot $909.09 +30.25 (+3.44%) · Mon 19 Oct, 14:40 UK\n\nMU rose on the session.", [], { bb8eBase: "MU", bb8eMoveR: pack("MU", "Micron Technology, Inc."), bb8qCtx: { q: "How is MU?" } });
  assert.match(body.reply, /^Micron Technology \$909\.09 \+30\.25 \(\+3\.44%\)/);
  assert.doesNotMatch(body.reply, /Gold spot/);
});

test("P0 footer: XAU stays Gold spot on both paths", () => {
  const c = load();
  const st = {
    bb8eBase: "XAU",
    bb8eMoveR: pack("GC=F", "Gold", { p: 4181.2, prev: 4180, change: 1.2, c: 0.03 }),
    bb8qCtx: { gold: true, spot: { q: { p: 4156.3, change: 12.4, c: 0.3, prev: 4143.9, changeAvailable: true }, ms: 1, text: "Gold spot is at $4,156.30 (gold-api.com, as of Mon 19 Oct, 14:42 UK)." } }
  };
  const stream = c.bb8pQuoteMeta(st);
  const json = c.bb8pMetaFix({}, false, st).quote;
  for (const q of [stream, json]) {
    assert.equal(q.label, "Gold spot");
    assert.equal(q.name, "Gold spot");
    assert.equal(q.symbol, "XAU");
    assert.equal(q.price, 4156.3);
    assert.match(q.quoteLine, /^Gold spot \$4,156\.30 /);
    assert.equal(q.source, "gold-api.com");
  }
});

test("P0 YTD: last prior-year GC=F bar is Wed 31 Dec 2025 close 4341.10, and the direction is computed", () => {
  const c = load();
  assert.equal(c.bb8rBarDate(1767157200, "America/New_York"), "2025-12-31");
  const bars = [
    { date: "2025-12-29", close: 4343.60009765625 },
    { date: "2025-12-30", close: 4386.2998046875 },
    { date: "2025-12-31", close: 4341.10009765625 },
    { date: "2026-01-02", close: 4329.60009765625 }
  ];
  const pick = c.bb8rYtdPick(bars, "2026-10-19");
  assert.equal(pick.date, "2025-12-31");
  assert.equal(pick.close, 4341.10009765625);
  assert.equal(pick.display.toFixed(2), "4341.10");
  const dir = c.bb8rYtdDir(pick.display, 4181.2);
  assert.equal(dir.word, "down");
  assert.equal(dir.instrument, "GC=F");
  assert.ok(dir.pct < -3 && dir.pct > -4);
  const mixed = c.bb8rYtdLabel("Year to date, gold spot (GC=F) from the Wed 31 Dec close of $4,341.10 are down 3.68%.");
  assert.match(mixed, /gold futures \(GC=F\)/);
  assert.doesNotMatch(mixed, /gold spot/i);
});

test("P0 citations: DXY, 10-year and the futures range each point at the source that contains the figure", () => {
  const c = load();
  const spx = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/%5EGSPC/", 1, "S&P 500 (^GSPC) fell 1.09% to 7,659.44", "^GSPC");
  const vix = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/%5EVIX/", 1, "VIX (^VIX) fell 7.05% to 18.58", "^VIX");
  const fort = c.bb8qSrc("Fortitude Gold article", "https://example.test/fortitude", 1, "Fortitude Gold expands the mine", "news");
  const dxy = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/DX-Y.NYB/", 1, "US Dollar Index (ICE, Yahoo DX-Y.NYB) last 98.42", "DX-Y.NYB");
  const tnx = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/%5ETNX/", 1, "US 10-year Treasury yield (^TNX) 4.15%", "^TNX");
  const fut = c.bb8qSrc("Yahoo Finance chart", "https://finance.yahoo.com/quote/GC=F/history/", 1, "gold futures (GC=F) 5-session high 4242.30 low 4095.00", "GC=F");
  const reply = [
    "The US Dollar Index is at 98.42. [1]",
    "The 10-year Treasury yield is 4.15%. [2]",
    "The 5-session futures range high is $4,242.30 and the low is $4,095.00. [3]"
  ].join("\n");
  const out = finish(c, reply, [spx, vix, fort, dxy, tnx, fut], { bb8qCtx: { q: "Give me the detailed market picture" } });
  assert.equal(out.sources.length, 3);
  assert.equal(out.sources[0].bb8qKey, "DX-Y.NYB");
  assert.equal(out.sources[1].bb8qKey, "^TNX");
  assert.equal(out.sources[2].bb8qKey, "GC=F");
  assert.match(out.reply, /US Dollar Index is at 98\.42\. \[1\]/);
  assert.match(out.reply, /10-year Treasury yield is 4\.15%\. \[2\]/);
  assert.match(out.reply, /5-session futures range high is \$4,242\.30 and the low is \$4,095\.00\. \[3\]/);
  assert.equal(out.sources.some(s => /Fortitude|\^GSPC|\^VIX/.test(s.bb8qKey + " " + s.name)), false);
});

test("P0 regime: one cached figure and as-of for mood, JSON meta and the reference feed", () => {
  const c = load();
  const first = c.bb3Mood({ vix: 16 });
  assert.equal(first.score, 55);
  assert.equal(first.regime, "Risk-On (Fragile)");
  c.MOOD = { regime: "Transition", score: 47 };
  const second = c.bb3Mood({ vix: 28 });
  assert.equal(second.score, 55);
  assert.equal(second.regime, "Risk-On (Fragile)");
  const st = { bb8eBase: "MU", bb8eMoveR: pack("MU", "Micron Technology, Inc.") };
  const meta = c.bb8pMetaFix({}, false, st);
  const ref = c.marketReferenceQuotes();
  return ref.then(body => {
    assert.equal(meta.regime.score, 55);
    assert.equal(body.regime.score, 55);
    assert.equal(meta.regime.regime, body.regime.regime);
    assert.equal(meta.regime.asOf, body.regime.asOf);
    assert.ok(meta.regime.asOfUk);
    c.bb8rReg.at = Date.now() - c.BB8R_REGIME_MS - 5;
    const third = c.bb3Mood({});
    assert.equal(third.score, 47);
    assert.equal(third.regime, "Transition");
  });
});

test("P0 BP.L: GBp price is divided once, Yahoo's GBP marketCap is not divided and not added", () => {
  const c = load();
  const implied = SH * PX / 100;
  const live = c.bb8rCap({ currency: "GBp", price: PX, regularMarketPrice: PX, sharesOutstanding: SH, marketCap: MC });
  assert.equal(live.price, PX);
  assert.equal(live.priceCurrency, "GBp");
  assert.equal(live.priceMajor, 6.22);
  assert.equal(live.sharesOutstanding, SH);
  assert.equal(live.yahooMarketCap, MC);
  assert.equal(live.status, "ok");
  assert.equal(live.marketCapCurrency, "GBP");
  assert.equal(live.marketCap, MC);
  assert.ok(Math.abs(live.ratio - 1) < 0.001);
  assert.notEqual(live.marketCap, Math.round(MC / 100));
  assert.notEqual(live.marketCap, Math.round(MC + implied));
  assert.equal(c.bb8rCapText(live.marketCap, "GBP"), "\u00a396.1bn");
  const penceTimesShares = c.bb8rCap({ currency: "GBp", price: PX, sharesOutstanding: SH, marketCap: SH * PX });
  assert.equal(penceTimesShares.status, "corrected-minor-units");
  assert.ok(Math.abs(penceTimesShares.marketCap - implied) < 2);
  const summed = c.bb8rCap({ currency: "GBp", price: PX, sharesOutstanding: SH, marketCap: implied * 2 });
  assert.equal(summed.status, "deduped");
  assert.ok(Math.abs(summed.marketCap - implied) < 2);
  const bare = c.bb8rCap({ currency: "GBp", price: PX, sharesOutstanding: SH });
  assert.equal(bare.status, "computed");
  assert.ok(Math.abs(bare.marketCap - implied) < 2);
  const noShares = c.bb8rCap({ currency: "GBp", price: PX, marketCap: MC });
  assert.equal(noShares.status, "unverified");
  assert.equal(noShares.marketCap, MC);
  const y = {
    price: { currency: "GBp", regularMarketPrice: { raw: PX }, marketCap: { raw: MC }, quoteType: "EQUITY", exchange: "LSE", longName: "BP p.l.c." },
    summaryDetail: { currency: "GBp", marketCap: { raw: MC } },
    defaultKeyStatistics: { sharesOutstanding: { raw: SH }, impliedSharesOutstanding: { raw: SH } }
  };
  const profile = c.bb8oProfileFrom("BP.L", y);
  assert.equal(profile.marketCapCheck.status, "ok");
  assert.equal(profile.marketCapCheck.price, PX);
  assert.equal(profile.marketCapCheck.priceCurrency, "GBp");
  assert.equal(profile.marketCapCheck.sharesOutstanding, SH);
  assert.equal(profile.marketCapCheck.yahooMarketCap, MC);
  assert.equal(profile.marketCap, MC);
  assert.equal(profile.marketCapCurrency, "GBP");
  assert.equal(profile.marketCapText, "\u00a396.1bn");
  assert.match(profile.unitNote, /already GBP/);
  const src = { name: "Yahoo Finance key statistics", detail: "GBp 96.1 billion", bb8qKey: "bb8o:metric" };
  const ctx = { q: "What is BP's market cap?", facts: [{ id: "bb8o:metric", text: "BP.L's market capitalisation is GBp 96.1 billion (Yahoo Finance, summary detail).", src }], sources: [src] };
  c.YSUM = y;
  return c.bb8qBuild({ bb8eBase: "BP.L", bb8qCtx: ctx }, {}).then(() => {
    assert.match(ctx.facts[0].text, /£96\.1bn/);
    assert.match(ctx.facts[0].text, /already in pounds and was not divided again/);
    assert.doesNotMatch(ctx.facts[0].text, /GBp 96/);
    assert.equal(src.marketCapCheck.yahooMarketCap, MC);
    assert.match(src.detail, /price 622 GBp/);
    assert.match(src.detail, /sharesOutstanding 15453548807/);
    assert.match(src.detail, /yahooMarketCap 96121077760/);
  });
});

test("P1 gold this week opens with the gold-api spot line", () => {
  const c = load();
  const st = {
    bb8eBase: "XAU",
    bb8qCtx: {
      gold: true,
      q: "What's the outlook for gold this week?",
      spot: { q: { p: 4156.3 }, ms: 1, text: "Gold spot is at $4,156.30 (gold-api.com, as of Mon 19 Oct, 14:42 UK)." }
    }
  };
  const out = finish(c, "Live: Gold futures (GC=F) rose 1.20% this week.\n\nGold spot is at $4,100.00.\n\nIn short: higher.", [], st);
  assert.match(out.reply, /^Gold spot \$4,156\.30 \(gold-api\.com, as of Mon 19 Oct, 14:42 UK\)\./);
  assert.match(out.reply, /Gold futures \(GC=F\) rose 1\.20% this week/);
  assert.doesNotMatch(out.reply, /Live:|Gold spot is at \$4,100/);
});

test("P1 calendar: FOMC, BEA and ONS parse; this week is honest when empty, and a real release is cited", async () => {
  const c = load();
  const fomc = `<div>2026 FOMC Meetings</div><strong>October</strong><div class="fomc-meeting__date col-xs-4">27-28</div><div>2025 FOMC Meetings</div><strong>October</strong><div class="fomc-meeting__date">28-29</div>`;
  const bea = `<div class="release-date">October 29</div><td class="release-title views-field">GDP (Advance Estimate), 3rd Quarter 2026</td>`;
  const ons = `data-gtm-release-title = "Quarterly suicide death registrations in England"\n data-gtm-release-date="20261019"`;
  c.PAGES["https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"] = fomc;
  c.PAGES["https://www.bea.gov/news/schedule"] = bea;
  c.PAGES["https://www.ons.gov.uk/releasecalendar"] = ons;
  c.PAGES["https://www.bls.gov/schedule/news_release/bls.jr.htm"] = "";
  assert.equal(c.bb8rCalParseFomc(fomc, Date.parse("2026-10-19T12:00:00Z"))[0].date, "2026-10-28");
  assert.equal(c.bb8rCalParseBea(bea, Date.parse("2026-10-19T12:00:00Z"))[0].date, "2026-10-29");
  assert.equal(c.bb8rCalParseOns(ons, Date.parse("2026-10-19T12:00:00Z")).length, 0);
  const ctx = { q: "What happens to gold this week?", facts: [], sources: [], gold: true };
  await c.bb8qBuild({ bb8qCtx: ctx }, {});
  assert.deepEqual(ctx.bb8rCal.events, []);
  assert.ok(ctx.bb8rCal.checked.indexOf("FOMC") >= 0 && ctx.bb8rCal.checked.indexOf("BLS") < 0);
  assert.ok(ctx.bb8rCal.failed.indexOf("BLS") >= 0);
  const empty = finish(c, "Outlook for this week: nothing else.\n\nNo scheduled Fed, economic-data or earnings dates for this week are in our feed.", [], { bb8qCtx: ctx });
  assert.match(empty.reply, /No FOMC, BEA or ONS release falls this week \(calendars checked; BLS did not load\)/);
  assert.doesNotMatch(empty.reply, /No scheduled Fed/);
  const onsCpi = ons + `\ndata-gtm-release-title = "Consumer price inflation, UK: September 2026"\n data-gtm-release-date="20261021"`;
  const beaWeek = bea + `<div class="release-date">October 22</div><td class="release-title">Personal Income and Outlays, September 2026</td>`;
  const c2 = load();
  c2.PAGES["https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"] = fomc;
  c2.PAGES["https://www.bea.gov/news/schedule"] = beaWeek;
  c2.PAGES["https://www.ons.gov.uk/releasecalendar"] = onsCpi;
  c2.PAGES["https://www.bls.gov/schedule/news_release/bls.jr.htm"] = "x".repeat(300);
  const ctx2 = { q: "gold this week", facts: [], sources: [], gold: true };
  await c2.bb8qBuild({ bb8qCtx: ctx2 }, {});
  const dates = ctx2.bb8rCal.events.map(e => e.date).sort();
  assert.deepEqual(dates, ["2026-10-21", "2026-10-22"]);
  const hit = finish(c2, "No scheduled Fed, economic-data or earnings dates for this week are in our feed.", [], { bb8qCtx: ctx2 });
  assert.match(hit.reply, /Personal Income and Outlays/);
  assert.match(hit.reply, /Consumer price inflation/);
  assert.match(hit.reply, /\[\d\]/);
  assert.doesNotMatch(hit.reply, /suicide|No scheduled Fed|No FOMC, BEA or ONS/);
  const c3 = load();
  const ctx3 = { q: "gold this week", facts: [], sources: [] };
  await c3.bb8qBuild({ bb8qCtx: ctx3 }, {});
  const kept = finish(c3, "No scheduled Fed, economic-data or earnings dates for this week are in our feed.", [], { bb8qCtx: ctx3 });
  assert.match(kept.reply, /No scheduled Fed, economic-data or earnings dates for this week are in our feed/);
});

test("P1 prose uses the cited figure, drops the filler, and gives each proxy its own as-of with the exact words", () => {
  const c = load();
  const gc = c.bb8qSrc("Yahoo Finance chart", "https://finance.yahoo.com/quote/GC=F/", 1, "GC=F last price $4,181.20", "GC=F");
  const snapped = finish(c, "GC=F unchanged at $4,181.00. [1]", [gc], { bb8qCtx: { q: "gold today" } });
  assert.match(snapped.reply, /\$4,181\.20/);
  assert.doesNotMatch(snapped.reply, /4,181\.00/);
  const far = finish(c, "From $4,341.10 to $4,386.30. [1]", [c.bb8qSrc("Yahoo Finance chart", "https://finance.yahoo.com/quote/GC=F/", 1, "closes 4341.10 and 4386.30", "GC=F")], { bb8qCtx: { q: "gold" } });
  assert.match(far.reply, /\$4,341\.10/);
  assert.match(far.reply, /\$4,386\.30/);
  const filler = finish(c, "Gold futures (GC=F) are at $4,181.20. [1] It's essential to monitor related economic indicators before the next print.", [gc], { bb8qCtx: { q: "gold" } });
  assert.match(filler.reply, /Gold futures \(GC=F\) are at \$4,181\.20\. \[1\]/);
  assert.doesNotMatch(filler.reply, /essential to monitor/);
  const ftse = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/%5EFTSE/", 1, "FTSE 100 up 0.20% at 9,412.00", "^FTSE");
  ftse.asOfUk = "Mon 19 Oct, 14:28 UK";
  ftse.bb8qProxy = { sym: "^FTSE", label: "the FTSE 100" };
  const hsi = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/%5EHSI/", 1, "Hang Seng rose 0.52% to 24,186.83", "^HSI");
  hsi.asOfUk = "Fri 16 Oct, 09:08 UK";
  hsi.bb8rClose = true;
  hsi.bb8qProxy = { sym: "^HSI", label: "the Hang Seng" };
  const line = "What we do have, as market proxies (not CPI data): the FTSE 100 is up 0.20% at 9,412.00 [1]; the Hang Seng rose 0.52% to 24,186.83 [2].";
  const prox = finish(c, line, [ftse, hsi], { bb8qCtx: { q: "UK inflation and China GDP" } });
  assert.match(prox.reply, /As a proxy, the FTSE 100 is up 0\.20% at 9,412\.00, as of Mon 19 Oct, 14:28 UK \[1\]/);
  assert.match(prox.reply, /As a proxy, the Hang Seng rose 0\.52% to 24,186\.83, as of Fri 16 Oct close \[2\]/);
  assert.doesNotMatch(prox.reply, /14:42|as market proxies/);
});

test("P2: DXY display label is short and 0700.HK changeDay is Fri", async () => {
  const c = load();
  const dxy = c.bb8qSrc("Yahoo Finance quote", "https://finance.yahoo.com/quote/DX-Y.NYB/", 1, "US Dollar Index (ICE, Yahoo DX-Y.NYB) last 98.42", "DX-Y.NYB");
  const out = finish(c, "The US Dollar Index (ICE, Yahoo DX-Y.NYB) is at 98.42. [1]", [dxy], { bb8qCtx: { q: "dollar" } });
  assert.match(out.reply, /US Dollar Index \(ICE\) is at 98\.42/);
  assert.doesNotMatch(out.reply, /Yahoo DX-Y\.NYB/);
  assert.match(out.sources[0].detail, /Yahoo DX-Y\.NYB/);
  assert.equal(out.sources[0].bb8rDisplay, "US Dollar Index (ICE)");
  c.YQ = { "0700.HK": { p: 417.8, ts: FRI, feed: { symbol: "0700.HK" }, session: { label: "regular close" } } };
  const row = (await c.yahooQuote(["0700.HK"]))["0700.HK"];
  assert.equal(row.changeDay, "Fri");
  assert.equal(row.feed.changeDay, "Fri");
  assert.equal(row.session.changeDay, "Fri");
  assert.match(row.changeDayLabel, /^Fri 16 Oct/);
  const str = c.bb8rSessionTag({ p: 1, ts: FRI, feed: "yahoo" }, "0700.HK");
  assert.equal(str.changeDay, "Fri");
  assert.equal(str.feed, "yahoo");
});

test("protocol: bb8r names, no timers, refuse, dry run, CRLF, md5 warn, missing anchor aborts", () => {
  const fns = [...B8R.matchAll(/(?:^|\n)(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(m => m[1]);
  assert.ok(fns.length > 20);
  assert.deepEqual(fns.filter(n => !n.startsWith("bb8r")), []);
  const dupes = fns.filter((n, i) => fns.indexOf(n) !== i);
  assert.deepEqual(dupes, []);
  const vars = [...B8R.matchAll(/(?:^|\n)var\s+([A-Za-z0-9_$]+)/g)].map(m => m[1]);
  assert.deepEqual(vars.filter(n => !/^(bb8r|BB8R_)/.test(n)), []);
  assert.equal(/setInterval\(|setTimeout\(|CREATE TABLE|\.tier\b|stripe|process\.env/i.test(B8R), false);
  assert.match(PATCH, /REFUSE: bb8r already applied/);
  assert.match(PATCH, /"--check" in sys\.argv/);
  assert.match(PATCH, /77aa597819385227f1407cd5d6c69f53/);
  const anchors = [
    "// BB8Q2_JS_END",
    'var BB8Q2_DXY = "US Dollar Index (ICE, Yahoo DX-Y.NYB)";',
    "function bb8oQuoteLabel(q) { return q; }",
    "function bb8oPost(doc, st) { return doc; }",
    "function bb8oProfileFrom(sym, r) { return { symbol: sym }; }",
    "function bb8pQuoteMeta(st) { return null; }",
    "function bb3Mood(m) { return { regime: 'Transition', score: 40 }; }",
    "async function bb8qBuild(st, body) { return null; }",
    "function bb8qFinish(out, st) { return out; }",
    "function bb8qNoData(doc, st, ctx) { return doc; }",
    "function bb8qParse(out) { return { body: '', srcs: [] }; }",
    "function bb8qRender(doc) { return { reply: doc.body, sources: [] }; }",
    "// BB8O_JS_END"
  ];
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bb8r-"));
  const srv = path.join(dir, "server.js");
  const body = anchors.join("\n") + "\n";
  fs.writeFileSync(srv, body);
  const py = path.join(__dirname, "../deploy/patch_bb8r.py");
  const run = (args, file) => spawnSync("python3", [py, ...args, dir], { encoding: "utf8" });
  const dry = run(["--check"]);
  assert.equal(dry.status, 0, dry.stderr + dry.stdout);
  assert.match(dry.stdout, /WARN md5 server\.js/);
  assert.match(dry.stdout, /dry run, nothing written/);
  assert.match(dry.stdout, /node --check passed/);
  assert.equal(fs.readFileSync(srv, "utf8"), body);
  fs.writeFileSync(srv, body.replace(/\n/g, "\r\n"));
  const apply = run([]);
  assert.equal(apply.status, 0, apply.stderr + apply.stdout);
  assert.match(apply.stdout, /APPLY bb8r/);
  const written = fs.readFileSync(srv);
  assert.ok(written.includes(Buffer.from("\r\n")));
  assert.ok(!written.includes(Buffer.from("\r\r\n")));
  assert.equal(spawnSync("node", ["--check", srv], { encoding: "utf8" }).status, 0);
  const again = run([]);
  assert.equal(again.status, 0, again.stderr + again.stdout);
  assert.match(again.stdout, /REFUSE: bb8r already applied/);
  const broken = body.replace("function bb8qRender(doc) { return { reply: doc.body, sources: [] }; }\n", "");
  fs.writeFileSync(srv, broken);
  const abort = run([]);
  assert.equal(abort.status, 1);
  assert.match(abort.stdout, /ABORT/);
  assert.equal(fs.readFileSync(srv, "utf8"), broken);
  fs.rmSync(dir, { recursive: true, force: true });
});
