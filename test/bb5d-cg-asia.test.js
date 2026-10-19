const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5d.py");
const SIGNED = ["basis", "c", "change", "currency", "delayMin", "exchange", "name", "p", "prev", "stale", "status", "ts"];

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB5D_JS\n([\s\S]*?)\n\/\/ BB5D_JS_END/);
  assert.ok(m, "BB5D_JS block missing");
  const js = m[1];
  assert.equal(/CREATE TABLE|setInterval\(|stripe\.webhooks/.test(js), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.ok(names.length > 0);
  assert.ok(names.every(name => name.startsWith("bb5d")));
  assert.equal(new Set(names).size, names.length);
  return js;
}

function load() {
  const context = {
    console, Map, JSON, URL, encodeURIComponent, decodeURIComponent, Date, Math, Number, String, isFinite,
    bb5dClock: () => 1_700_000_000_000
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(extractJs() + "\nbb5dStore.clear(); bb5dCarry.until = 0; bb5dCarry.boot = false;", context, { filename: "bb5d.js" });
  return context;
}

test("cold CoinGecko cache stays unavailable, a warm array is served stale without wrapping", () => {
  const s = load();
  const markets = "/coins/markets?ids=bitcoin&vs_currency=usd";
  const cold = s.bb5dAnswer(s.bb5dKey(markets), true);
  assert.equal(JSON.stringify(cold.body), JSON.stringify({ error: "CoinGecko cooling down", unavailable: true }));
  assert.equal(cold.headers["X-Dispatch-Data-Status"], "unavailable");
  assert.equal(cold.headers["X-Dispatch-As-Of"], undefined);

  const body = [{ id: "bitcoin", current_price: 100 }];
  s.bb5dPut(s.bb5dKey(markets), body, "2026-01-01T00:00:00.000Z");
  const warm = s.bb5dAnswer(s.bb5dKey("/coins/markets?vs_currency=usd&ids=bitcoin"), true);
  assert.equal(Array.isArray(warm.body), true);
  assert.equal(JSON.stringify(warm.body), JSON.stringify(body));
  assert.equal(warm.headers["X-Dispatch-Data-Status"], "stale");
  assert.equal(warm.headers["X-Dispatch-As-Of"], "2026-01-01T00:00:00.000Z");
  assert.equal(warm.headers["X-Dispatch-Data-As-Of"], "2026-01-01T00:00:00.000Z");
});

test("a markets sibling is used only when every requested id is already cached", () => {
  const s = load();
  s.bb5dPut(s.bb5dKey("/coins/markets?ids=bitcoin,ethereum&vs_currency=usd"), [
    { id: "bitcoin", current_price: 1 },
    { id: "ethereum", current_price: 2 }
  ], "2026-01-02T00:00:00.000Z");
  const one = s.bb5dAnswer(s.bb5dKey("/coins/markets?ids=ethereum&vs_currency=usd"), true);
  assert.equal(JSON.stringify(one.body), JSON.stringify([{ id: "ethereum", current_price: 2 }]));
  const missing = s.bb5dAnswer(s.bb5dKey("/coins/markets?ids=bitcoin,dogecoin&vs_currency=usd"), true);
  assert.equal(missing.body.unavailable, true);
  const otherVs = s.bb5dAnswer(s.bb5dKey("/coins/markets?ids=bitcoin&vs_currency=eur"), true);
  assert.equal(otherVs.body.unavailable, true);
});

test("a carried cooldown lets the first request through", () => {
  const s = load();
  s.bb5dCarry.until = s.bb5dNow() + 60000;
  s.bb5dCarry.boot = true;
  assert.equal(s.bb5dGate(), false);
  assert.equal(s.bb5dGate(), true);
});

test("delayed Asia and FX prints are not stale, and a US print follows the same allowance", () => {
  const s = load();
  const minute = 60000;
  const ks = s.bb5dClass(16 * minute, 15);
  const tse = s.bb5dClass(16 * minute, 15);
  const axjo = s.bb5dClass(20 * minute, 20);
  const brlDelayed = s.bb5dClass(16 * minute, 15);
  const brlOld = s.bb5dClass(20 * minute, 0);
  const us = s.bb5dClass(20 * 1000, 0);
  const ksOld = s.bb5dClass(24 * minute, 15);
  for (const row of [ks, tse, axjo, brlDelayed]) {
    assert.equal(row.status, "delayed");
    assert.equal(row.stale, false);
    assert.equal(row.note, "delayed " + row.delayMin + "m by exchange");
  }
  assert.equal(us.status, "fresh");
  assert.equal(us.stale, false);
  assert.equal(brlOld.status, "stale");
  assert.equal(ksOld.status, "stale");

  const quote = s.bb5dFromRow({
    symbol: "005930.KS",
    regularMarketPrice: 70000,
    regularMarketPreviousClose: 69000,
    currency: "KRW",
    fullExchangeName: "KRX",
    shortName: "Samsung",
    regularMarketTime: Math.floor((s.bb5dNow() - 16 * minute) / 1000),
    exchangeDataDelayedBy: 15
  });
  assert.equal(quote.p, 70000);
  assert.equal(quote.status, "delayed");
  assert.equal(quote.stale, false);
  assert.equal(quote.delayMin, 15);
  assert.equal(quote.note, "delayed 15m by exchange");
  for (const key of SIGNED) assert.equal(Object.prototype.hasOwnProperty.call(quote, key), true);
  assert.equal(s.bb5dFromRow({ regularMarketPrice: 0, exchangeDataDelayedBy: 15 }), null);

  s.BB3_ALIAS = { ASX200: "^AXJO", KOSPI: "^KS11", USDBRL: "BRL=X", USDINR: "INR=X" };
  assert.equal(s.bb5dWire("ASX200").wire, "^AXJO");
  assert.equal(s.bb5dWire("KOSPI").wire, "^KS11");
  assert.equal(s.bb5dWire("USDBRL").wire, "BRL=X");
  assert.equal(s.bb5dWire("USDINR").wire, "INR=X");
  assert.equal(s.bb5dWire("005930.KS").wire, "005930.KS");
  assert.equal(s.bb5dWire("6758.T").wire, "6758.T");
  assert.equal(s.bb5dWire("7203.T").wire, "7203.T");
  assert.equal(s.bb5dWire("AAPL").wire, "AAPL");
});

test("the chart fallback pool still visits the tail", async () => {
  const s = load();
  const seen = [];
  await s.bb5dPool(["AAPL", "MSFT", "005930.KS", "6758.T", "^AXJO", "BRL=X", "INR=X"], 6, async (symbol) => {
    seen.push(symbol);
    return symbol;
  });
  assert.deepEqual(seen.sort(), ["005930.KS", "6758.T", "AAPL", "BRL=X", "INR=X", "MSFT", "^AXJO"]);
});
