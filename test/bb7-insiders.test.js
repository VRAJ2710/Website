const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb7.py"), "utf8");
const blockStart = patch.indexOf("// BB7_JS\n");
const blockEnd = patch.indexOf("// BB7_JS_END");
assert.ok(blockStart > 0 && blockEnd > blockStart);
const block = patch.slice(blockStart, blockEnd + "// BB7_JS_END".length);
assert.equal(block.includes("CREATE TABLE"), false);
assert.equal(block.includes("setInterval("), false);
assert.equal(block.includes("stripe.webhooks"), false);
assert.equal(block.includes(".tier"), false);
assert.match(patch, /3d7e492fb982dda566939f52f792b74b/);
assert.match(patch, /bb6/);

const context = {
  console, Date, Intl, Number, String, isFinite, Object, Array, Math, RegExp, JSON, Error,
  process, Buffer, require, AbortSignal, URL, encodeURIComponent, setTimeout, clearTimeout, Promise, Map
};
context.globalThis = context;
function hasPremiumAccess(user) {
  if (!user) return false;
  if (user.admin === true) return true;
  return user.tier === "premium";
}
context.hasPremiumAccess = hasPremiumAccess;
vm.createContext(context);
vm.runInContext(block, context, { filename: "bb7.js" });

let clock = Date.parse("2026-10-19T12:00:00Z");
context.bb7Clock = function () { return clock; };
context.bb7SleepHook = function (ms) { clock += ms; };

function reset() {
  clock = Date.parse("2026-10-19T12:00:00Z");
  context.bb7Reset();
}

const FORM = `<?xml version="1.0"?>
<ownershipDocument>
  <issuer><issuerName>Apple Inc.</issuerName><issuerTradingSymbol>AAPL</issuerTradingSymbol></issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>COOK TIMOTHY D</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>1</isDirector><isOfficer>1</isOfficer><isTenPercentOwner>0</isTenPercentOwner>
      <officerTitle>Chief Executive Officer</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-02</value></transactionDate>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>100</value></transactionShares>
        <transactionPricePerShare><value>10.5</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>500</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-03</value></transactionDate>
      <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>40</value></transactionShares>
        <transactionPricePerShare><value>11</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>460</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-04</value></transactionDate>
      <transactionCoding><transactionCode>A</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>15</value></transactionShares>
        <transactionPricePerShare><value>0</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>475</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-05</value></transactionDate>
      <transactionCoding><transactionCode>F</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>3</value></transactionShares>
        <transactionPricePerShare><value>12</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>472</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
  <derivativeTable>
    <derivativeTransaction>
      <transactionDate><value>2026-03-06</value></transactionDate>
      <transactionCoding><transactionCode>M</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>20</value></transactionShares>
        <transactionPricePerShare><value>5</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts><sharesOwnedFollowingTransaction><value>20</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
    </derivativeTransaction>
  </derivativeTable>
</ownershipDocument>`;

test("Form 4 XML keeps P, S, A, F and a derivative M", () => {
  const rows = context.bb7ParseForm4(FORM, {
    filingDate: "2026-03-07",
    accession: "0000320193-26-000010",
    filingUrl: "https://www.sec.gov/Archives/edgar/data/320193/000032019326000010/0000320193-26-000010-index.html"
  });
  assert.deepEqual(rows.map(row => row.transactionCode), ["P", "S", "A", "F", "M"]);
  assert.equal(rows[0].insiderName, "COOK TIMOTHY D");
  assert.equal(rows[0].insiderRole, "director, Chief Executive Officer");
  assert.equal(rows[0].codeLabel, "Open-market purchase");
  assert.equal(rows[1].codeLabel, "Open-market sale");
  assert.equal(rows[2].codeLabel, "Grant or award");
  assert.equal(rows[3].codeLabel, "Tax withholding");
  assert.equal(rows[4].codeLabel, "Exercise or conversion");
  assert.equal(rows[0].shares, 100);
  assert.equal(rows[0].price, 10.5);
  assert.equal(rows[0].value, 1050);
  assert.equal(rows[0].sharesOwnedAfter, 500);
  assert.equal(rows[0].transactionDate, "2026-03-02");
  assert.equal(rows[0].filingDate, "2026-03-07");
  assert.equal(rows[0].acquiredDisposed, "A");
  assert.equal(rows[1].acquiredDisposed, "D");
  assert.equal(rows[0].isDerivative, false);
  assert.equal(rows[4].isDerivative, true);
  assert.equal(rows[4].transactionCode, "M");
  assert.match(rows[0].filingUrl, /index\.html$/);
});

test("free sees five P/S rows, premium and admin see every code", () => {
  const rows = context.bb7ParseForm4(FORM, { filingDate: "2026-03-07", accession: "0000320193-26-000010", filingUrl: "https://example/index.html" });
  const extra = [];
  "PSPSPS".split("").forEach((code, i) => {
    extra.push(Object.assign({}, rows[0], { transactionCode: code, transactionDate: "2026-04-0" + (i + 1) }));
  });
  const all = rows.concat(extra);
  const free = context.bb7Pick(all, { premium: context.hasPremiumAccess(null) });
  assert.equal(free.length, 5);
  assert.ok(free.every(row => row.transactionCode === "P" || row.transactionCode === "S"));
  assert.ok(free.every(row => row.isDerivative === false));
  const premium = context.bb7Pick(all, { premium: context.hasPremiumAccess({ tier: "premium" }), codes: "all" });
  assert.equal(premium.length, all.length);
  assert.ok(premium.some(row => row.transactionCode === "A"));
  assert.ok(premium.some(row => row.transactionCode === "F"));
  assert.ok(premium.some(row => row.isDerivative && row.transactionCode === "M"));
  const admin = context.bb7Pick(all, { premium: context.hasPremiumAccess({ tier: "free", admin: true }), codes: "all" });
  assert.equal(admin.length, all.length);
  const guest = context.bb7Shape({ ticker: "AAPL", cik: "0000320193", company: "Apple Inc.", asOf: "2026-10-19T12:00:00.000Z", rows: all, filings: 3 }, { premium: false });
  assert.equal(guest.meta.limited, true);
  assert.equal(guest.meta.upgrade, "premium");
  assert.equal(guest.meta.count, 5);
  assert.equal(guest.meta.codes, "PS");
  assert.equal(guest.house, null);
  const full = context.bb7Shape({ ticker: "AAPL", cik: "0000320193", company: "Apple Inc.", asOf: "2026-10-19T12:00:00.000Z", rows: all, filings: 3 }, { premium: true, codes: "all" });
  assert.equal(full.meta.limited, false);
  assert.equal(full.meta.upgrade, undefined);
  assert.equal(full.meta.codes, "all");
  assert.equal(full.insider.length, all.length);
});

test("the EDGAR token bucket allows 10 requests in a second", () => {
  reset();
  const now = 1_700_000_000_000;
  for (let i = 0; i < 10; i++) assert.equal(context.bb7TakeToken(now).ok, true, "slot " + i);
  const blocked = context.bb7TakeToken(now);
  assert.equal(blocked.ok, false);
  assert.equal(blocked.wait, 1000);
  assert.equal(context.bb7TakeToken(now + 1000).ok, true);
});

test("EDGAR down serves a warm cache as stale and a cold cache as unavailable", async () => {
  reset();
  const row = context.bb7ParseForm4(FORM, { filingDate: "2026-03-07", accession: "0000320193-26-000010", filingUrl: "https://example/index.html" })[0];
  context.bb7Remember("f4:AAPL", {
    ticker: "AAPL", cik: "0000320193", company: "Apple Inc.", rows: [row], complete: true, filings: 1
  }, context.bb7FormTtl, clock - context.bb7FormTtl - 5000);
  context.bb7Fetch = async function () {
    return { ok: false, status: 429, headers: { get: function () { return ""; } }, arrayBuffer: async function () { return new ArrayBuffer(0); } };
  };
  const warm = await context.bb7Load("AAPL", { premium: false });
  assert.equal(warm.status, 200);
  assert.equal(warm.body.stale, true);
  assert.equal(warm.body.unavailable, undefined);
  assert.ok(warm.body.asOf);
  assert.equal(warm.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(warm.headers["X-Dispatch-As-Of"], warm.body.asOf);
  assert.equal(warm.body.insider.length, 1);

  reset();
  context.bb7Fetch = async function () { throw new Error("EDGAR down"); };
  const cold = await context.bb7Load("AAPL", { premium: true, codes: "all" });
  assert.equal(cold.status, 200);
  assert.deepEqual(cold.body, { unavailable: true, message: "Insider filings unavailable right now" });
  assert.equal(cold.headers["X-Dispatch-Data-Status"], "unavailable");
});

function pdfText(source) {
  const payload = Buffer.from(source);
  const comp = zlib.deflateSync(payload);
  return Buffer.concat([
    Buffer.from("%PDF-1.4\n1 0 obj << /Filter /FlateDecode /Length " + comp.length + " >>\nstream\n"),
    comp,
    Buffer.from("\nendstream\nendobj\n")
  ]);
}

test("a text-layer House PDF yields a trade and a scanned PDF says See filing", () => {
  const parsed = context.bb7PdfTrades(pdfText("BT (Apple Inc. AAPL P 01/15/2026 $1,001 - $15,000 SP) Tj ET"), "AAPL");
  assert.equal(parsed.parsed, true);
  assert.equal(parsed.note, "");
  assert.equal(parsed.trades.length, 1);
  assert.equal(parsed.trades[0].ticker, "AAPL");
  assert.equal(parsed.trades[0].asset, "Apple Inc.");
  assert.equal(parsed.trades[0].type, "P");
  assert.equal(parsed.trades[0].date, "2026-01-15");
  assert.equal(parsed.trades[0].amountRange, "$1,001 - $15,000");
  assert.equal(parsed.trades[0].owner, "SP");
  const scanned = context.bb7PdfTrades(Buffer.from("%PDF-1.4\n1 0 obj << /Type /XObject /Subtype /Image /Width 1 /Height 1 /Length 1 >>\nstream\nX\nendstream\nendobj\n"), "AAPL");
  assert.equal(scanned.parsed, false);
  assert.equal(scanned.note, "See filing");
  assert.deepEqual(scanned.trades, []);
  assert.equal(context.bb7PdfLibrary(), "");
});

function zipDeflate(name, data) {
  const comp = zlib.deflateRawSync(data);
  const nameB = Buffer.from(name);
  const crc = zlib.crc32(data);
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0);
  local.writeUInt16LE(8, 8);
  local.writeUInt32LE(crc, 14);
  local.writeUInt32LE(comp.length, 18);
  local.writeUInt32LE(data.length, 22);
  local.writeUInt16LE(nameB.length, 26);
  const cd = Buffer.alloc(46);
  cd.writeUInt32LE(0x02014b50, 0);
  cd.writeUInt16LE(8, 10);
  cd.writeUInt32LE(crc, 16);
  cd.writeUInt32LE(comp.length, 20);
  cd.writeUInt32LE(data.length, 24);
  cd.writeUInt16LE(nameB.length, 28);
  const body = Buffer.concat([local, nameB, comp]);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(1, 8);
  eocd.writeUInt16LE(1, 10);
  eocd.writeUInt32LE(46 + nameB.length, 12);
  eocd.writeUInt32LE(body.length, 16);
  return Buffer.concat([body, cd, nameB, eocd]);
}

test("the House index lists FilingType P with a Clerk PDF link", () => {
  const xml = `<?xml version="1.0"?><FinancialDisclosure>
    <Member><Last>Aaron</Last><First>Richard</First><FilingType>W</FilingType><StateDst>MI04</StateDst><Year>2026</Year><FilingDate>4/15/2026</FilingDate><DocID>8068</DocID></Member>
    <Member><Prefix>Hon.</Prefix><Last>Alford</Last><First>Mark</First><FilingType>P</FilingType><StateDst>MO04</StateDst><Year>2026</Year><FilingDate>3/31/2026</FilingDate><DocID>20034201</DocID></Member>
  </FinancialDisclosure>`;
  const entries = context.bb7ZipEntries(zipDeflate("2026FD.xml", Buffer.from(xml)));
  assert.equal(entries.length, 1);
  const items = context.bb7ParseHouseXml(entries[0].data.toString("utf8"));
  assert.equal(items.length, 1);
  assert.equal(items[0].member, "Hon. Mark Alford");
  assert.equal(items[0].state, "MO");
  assert.equal(items[0].district, "04");
  assert.equal(items[0].filingDate, "2026-03-31");
  assert.equal(items[0].docId, "20034201");
  assert.equal(items[0].pdfUrl, "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20034201.pdf");
  assert.equal(items[0].parsed, false);
  assert.equal(items[0].note, "See filing");
});

function oneForm(code) {
  return `<?xml version="1.0"?><ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>COOK TIMOTHY D</rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isOfficer>1</isOfficer><officerTitle>Chief Executive Officer</officerTitle></reportingOwnerRelationship></reportingOwner><nonDerivativeTransaction><transactionDate><value>2026-02-02</value></transactionDate><transactionCoding><transactionCode>${code}</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>8</value></transactionShares><transactionPricePerShare><value>4</value></transactionPricePerShare><transactionAcquiredDisposedCode><value>${code === "S" || code === "F" ? "D" : "A"}</value></transactionAcquiredDisposedCode></transactionAmounts><postTransactionAmounts><sharesOwnedFollowingTransaction><value>80</value></sharesOwnedFollowingTransaction></postTransactionAmounts></nonDerivativeTransaction></ownershipDocument>`;
}

function mockEdgar(codes) {
  const seen = [];
  const xmlHits = [];
  context.bb7Fetch = async function (url, init) {
    seen.push({ url: String(url), headers: init && init.headers });
    const headers = { get: function () { return ""; } };
    const send = function (text) {
      return { ok: true, status: 200, headers: headers, arrayBuffer: async function () { return Buffer.from(text); } };
    };
    if (String(url).includes("company_tickers.json")) {
      return send(JSON.stringify({
        0: { cik_str: 320193, ticker: "AAPL", title: "Apple Inc." },
        1: { cik_str: 884394, ticker: "SPY", title: "SPDR S&P 500 ETF Trust" }
      }));
    }
    if (String(url).includes("CIK0000320193")) {
      return send(JSON.stringify({
        name: "Apple Inc.",
        filings: { recent: {
          form: codes.map(function () { return "4"; }),
          filingDate: codes.map(function () { return "2026-02-02"; }),
          accessionNumber: codes.map(function (_c, i) { return "0000320193-26-00000" + i; }),
          primaryDocument: codes.map(function (_c, i) { return "f" + i + ".xml"; })
        } }
      }));
    }
    if (String(url).includes("CIK0000884394")) {
      return send(JSON.stringify({ name: "SPDR S&P 500 ETF Trust", filings: { recent: { form: ["10-K"], filingDate: ["2026-01-01"], accessionNumber: ["0000884394-26-000001"], primaryDocument: ["spy.htm"] } } }));
    }
    const file = String(url).match(/f(\d+)\.xml/);
    if (file) {
      xmlHits.push(url);
      return send(oneForm(codes[Number(file[1])]));
    }
    if (String(url).includes("FD.zip")) {
      const xml = Buffer.from("<FinancialDisclosure><Member><Prefix>Hon.</Prefix><Last>Alford</Last><First>Mark</First><FilingType>P</FilingType><StateDst>MO04</StateDst><Year>2026</Year><FilingDate>3/31/2026</FilingDate><DocID>20034201</DocID></Member></FinancialDisclosure>");
      return { ok: true, status: 200, headers: headers, arrayBuffer: async function () { return zipDeflate("2026FD.xml", xml); } };
    }
    throw new Error("unexpected " + url);
  };
  return { seen: seen, xmlHits: xmlHits };
}

test("requests send the EDGAR user agent and stop early for a free member", async () => {
  reset();
  const codes = ["P", "S", "A", "P", "S", "P", "S", "M"];
  const hit = mockEdgar(codes);
  const headers = context.bb7Headers();
  assert.equal(headers["User-Agent"], "TheDispatchMarkets admin@thedispatch.uk");
  assert.ok(headers["Accept-Encoding"]);
  const free = await context.bb7Load("AAPL", { premium: false });
  assert.equal(free.status, 200);
  assert.equal(free.body.meta.limited, true);
  assert.equal(free.body.meta.count, 5);
  assert.equal(free.body.insider.length, 5);
  assert.ok(hit.seen.some(call => call.headers && call.headers["User-Agent"] === "TheDispatchMarkets admin@thedispatch.uk"));
  const freeXml = hit.xmlHits.length;
  assert.ok(freeXml < codes.length);
  assert.ok(freeXml >= 5);

  reset();
  const premiumHit = mockEdgar(codes);
  const premium = await context.bb7Load("AAPL", { premium: true, codes: "all" });
  assert.equal(premium.body.meta.limited, false);
  assert.equal(premium.body.meta.codes, "all");
  assert.equal(premiumHit.xmlHits.length, codes.length);
  assert.ok(premium.body.insider.some(row => row.transactionCode === "A"));
  assert.ok(premium.body.insider.some(row => row.transactionCode === "M"));
});

test("an unknown ticker is 404 and an ETF with no Form 4 is an empty list", async () => {
  reset();
  mockEdgar(["P"]);
  const missing = await context.bb7Load("ZZZZ", { premium: true, codes: "all" });
  assert.equal(missing.status, 404);
  assert.deepEqual(missing.body, { error: "Unknown ticker." });
  reset();
  mockEdgar(["P"]);
  const etf = await context.bb7Load("SPY", { premium: true, codes: "all" });
  assert.equal(etf.status, 200);
  assert.deepEqual(etf.body.insider, []);
  assert.equal(etf.body.note, "No Form 4 filings for this ticker.");
  assert.equal(etf.body.company, "SPDR S&P 500 ETF Trust");
});

test("premium house=1 lists Clerk PTRs as See filing", async () => {
  reset();
  mockEdgar(["P", "S"]);
  const out = await context.bb7Load("AAPL", { premium: true, codes: "PS", house: true });
  assert.equal(out.status, 200);
  assert.ok(out.body.house);
  assert.equal(out.body.house.items.length, 1);
  assert.equal(out.body.house.items[0].note, "See filing");
  assert.equal(out.body.house.items[0].parsed, false);
  assert.match(out.body.house.items[0].pdfUrl, /ptr-pdfs\/2026\/20034201\.pdf$/);
  assert.match(out.body.house.note, /No PDF text library/);
  const guest = await context.bb7Load("AAPL", { premium: false, house: true });
  assert.equal(guest.body.house, null);
});

test("the explainer is factual and does not recommend a trade", () => {
  const explainer = context.bb7Explainer();
  assert.match(explainer.what, /Form 4/);
  assert.match(explainer.where, /SEC EDGAR/);
  assert.match(explainer.why, /code P/);
  assert.match(explainer.why, /code S/);
  assert.match(explainer.house, /Periodic Transaction Report/);
  const text = JSON.stringify(explainer);
  assert.equal(/\bbuy\b/i.test(text), false);
  assert.equal(/\bsell\b/i.test(text), false);
  assert.equal(/\bbullish\b/i.test(text), false);
  assert.equal(/\bbearish\b/i.test(text), false);
  assert.equal(/\brecommend/i.test(text), false);
});
