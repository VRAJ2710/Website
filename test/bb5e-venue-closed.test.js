const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5e.py");
const KEPT = ["p", "c", "prev", "change", "currency", "basis", "exchange", "name", "ts", "delayMin"];

function extractJs() {
  const src = fs.readFileSync(PATCH, "utf8");
  const m = src.match(/\/\/ BB5E_JS\n([\s\S]*?)\n\/\/ BB5E_JS_END/);
  assert.ok(m, "BB5E_JS block missing");
  const js = m[1];
  assert.equal(/CREATE TABLE|setInterval\(|stripe\.webhooks/.test(js), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.ok(names.length > 0);
  assert.ok(names.every(name => name.startsWith("bb5e")), names.join(","));
  assert.equal(new Set(names).size, names.length);
  assert.equal(src.includes("row && row.symbol, row);"), true);
  assert.equal(src.includes("}, delay), symbol, meta);"), true);
  assert.equal(src.includes("app.js?v=chat"), false);
  return js;
}

function load() {
  const context = {
    console, Map, JSON, URL, Intl, Date, Math, Number, String, isFinite, Object
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(extractJs(), context, { filename: "bb5e.js" });
  return context;
}

function at(iso) {
  return Date.parse(iso);
}

function quote(now, ageMin, extra) {
  const ts = Math.floor((now - ageMin * 60000) / 1000);
  return Object.assign({
    p: 100, c: 1, prev: 99, change: 1, currency: "USD", basis: "previous_close",
    exchange: "Test", name: "Name", ts, delayMin: 15, source: "yahoo"
  }, extra);
}

function kept(out, src) {
  for (const key of KEPT) assert.equal(out[key], src[key], key);
  assert.equal(out.source, "yahoo");
}

test("AAPL at 02:00 UK is closed until 14:30 UK, including both DST-gap weeks", () => {
  const s = load();
  const winter = at("2026-01-14T02:00:00Z");
  const q = quote(winter, 40);
  const out = s.bb5eApply(q, "AAPL", null, winter);
  assert.equal(out.status, "closed");
  assert.equal(out.stale, false);
  assert.equal(out.delayMin, 15);
  assert.equal(out.nextOpen, "2026-01-14T14:30:00.000Z");
  assert.equal(out.note, "US market closed · opens 14:30 UK");
  kept(out, q);

  const spring = at("2026-03-18T02:00:00Z");
  const gap = s.bb5eApply(quote(spring, 40), "AAPL", null, spring);
  assert.equal(gap.status, "closed");
  assert.equal(gap.stale, false);
  assert.equal(gap.nextOpen, "2026-03-18T13:30:00.000Z");
  assert.equal(gap.note, "US market closed · opens 13:30 UK");

  const autumn = at("2026-10-28T02:00:00Z");
  const back = s.bb5eApply(quote(autumn, 40), "AAPL", null, autumn);
  assert.equal(back.nextOpen, "2026-10-28T13:30:00.000Z");
  assert.equal(back.note, "US market closed · opens 13:30 UK");

  const summer = at("2026-07-15T02:00:00Z");
  const both = s.bb5eApply(quote(summer, 40), "AAPL", null, summer);
  assert.equal(both.nextOpen, "2026-07-15T13:30:00.000Z");
  assert.equal(both.note, "US market closed · opens 14:30 UK");
});

test("7203.T is delayed during the Tokyo session and closed outside it, including lunch", () => {
  const s = load();
  const open = at("2026-01-14T01:00:00Z");
  const live = quote(open, 16);
  const during = s.bb5eApply(live, "7203.T", null, open);
  assert.equal(during.status, "delayed");
  assert.equal(during.stale, false);
  assert.equal(during.delayMin, 15);
  assert.equal(during.note, "delayed 15m by exchange");
  assert.equal(during.nextOpen, undefined);
  kept(during, live);

  const shut = at("2026-01-14T12:00:00Z");
  const after = s.bb5eApply(quote(shut, 40), "7203.T", null, shut);
  assert.equal(after.status, "closed");
  assert.equal(after.stale, false);
  assert.equal(after.nextOpen, "2026-01-15T00:00:00.000Z");
  assert.equal(after.note, "Tokyo market closed · opens Thu 00:00 UK");

  const lunch = at("2026-01-14T02:45:00Z");
  const mid = s.bb5eApply(quote(lunch, 10), "7203.T", null, lunch);
  assert.equal(mid.status, "closed");
  assert.equal(mid.nextOpen, "2026-01-14T03:30:00.000Z");
  assert.equal(mid.note, "Tokyo market closed · opens 03:30 UK");
  assert.equal(s.bb5eOpenAt(s.bb5eSpec("^N225"), new Date(lunch)), true);
});

test("USDINR is quiet before Mumbai and stale during it when the tick is old", () => {
  const s = load();
  const early = at("2026-01-14T02:00:00Z");
  const q = quote(early, 45, { currency: "INR" });
  const quiet = s.bb5eApply(q, "USDINR", null, early);
  assert.equal(quiet.status, "quiet");
  assert.equal(quiet.stale, false);
  assert.equal(quiet.nextOpen, "2026-01-14T03:45:00.000Z");
  assert.equal(quiet.note, "quiet · local market opens 03:45 UK");
  kept(quiet, q);
  const wire = s.bb5eApply(q, "INR=X", null, early);
  assert.equal(wire.status, "quiet");
  assert.equal(wire.nextOpen, quiet.nextOpen);

  const session = at("2026-01-14T05:00:00Z");
  const old = quote(session, 24, { currency: "INR" });
  const stale = s.bb5eApply(old, "USDINR", null, session);
  assert.equal(stale.status, "stale");
  assert.equal(stale.stale, true);
  assert.equal(stale.delayMin, 15);
  assert.equal(stale.nextOpen, undefined);
  assert.equal(stale.note, undefined);

  const saturday = at("2026-01-17T02:00:00Z");
  const weekend = s.bb5eApply(quote(saturday, 45, { currency: "INR" }), "USDINR", null, saturday);
  assert.equal(weekend.status, "closed");
  assert.equal(weekend.stale, false);
  assert.equal(weekend.nextOpen, "2026-01-19T03:45:00.000Z");
  assert.equal(weekend.note, "India market closed · opens Mon 03:45 UK");
});

test("USDBRL is quiet while B3 is shut, and KRW uses the Seoul window", () => {
  const s = load();
  const early = at("2026-01-14T02:00:00Z");
  const brl = s.bb5eApply(quote(early, 45, { currency: "BRL" }), "USDBRL", null, early);
  assert.equal(brl.status, "quiet");
  assert.equal(brl.stale, false);
  assert.equal(brl.nextOpen, "2026-01-14T13:00:00.000Z");
  assert.equal(brl.note, "quiet · local market opens 13:00 UK");
  assert.equal(s.bb5eApply(quote(early, 45), "BRL=X", null, early).status, "quiet");

  const desk = at("2026-01-14T15:00:00Z");
  const old = s.bb5eApply(quote(desk, 24, { currency: "BRL" }), "USDBRL", null, desk);
  assert.equal(old.status, "stale");
  assert.equal(old.stale, true);

  const seoul = at("2026-01-14T12:00:00Z");
  const krw = s.bb5eApply(quote(seoul, 45), "KRW=X", null, seoul);
  assert.equal(krw.status, "quiet");
  assert.equal(krw.nextOpen, "2026-01-15T00:00:00.000Z");
  assert.equal(krw.note, "quiet · local market opens Thu 00:00 UK");
});

test("EURUSD is closed on Saturday and stays on the age rule during the week", () => {
  const s = load();
  const saturday = at("2026-01-17T12:00:00Z");
  const closed = s.bb5eApply(quote(saturday, 45), "EURUSD", null, saturday);
  assert.equal(closed.status, "closed");
  assert.equal(closed.stale, false);
  assert.equal(closed.nextOpen, "2026-01-18T22:00:00.000Z");
  assert.equal(closed.note, "FX market closed · opens Sun 22:00 UK");
  assert.equal(s.bb5eApply(quote(saturday, 45), "EURUSD=X", null, saturday).nextOpen, closed.nextOpen);

  const week = at("2026-01-14T02:00:00Z");
  const fresh = s.bb5eApply(quote(week, 0.5, { delayMin: 0 }), "EURUSD", null, week);
  assert.equal(fresh.status, "fresh");
  assert.equal(fresh.stale, false);
  assert.equal(fresh.nextOpen, undefined);
  const aged = s.bb5eApply(quote(week, 45, { delayMin: 0 }), "EURUSD", null, week);
  assert.equal(aged.status, "stale");
  assert.equal(aged.stale, true);
});

test("an open US venue with a 24 minute tick is stale", () => {
  const s = load();
  const now = at("2026-01-14T15:00:00Z");
  const q = quote(now, 24);
  const out = s.bb5eApply(q, "AAPL", null, now);
  assert.equal(out.status, "stale");
  assert.equal(out.stale, true);
  assert.equal(out.delayMin, 15);
  assert.equal(out.nextOpen, undefined);
  assert.equal(out.note, undefined);
  kept(out, q);
  const fresh = s.bb5eApply(quote(now, 0.25, { delayMin: 0 }), "^GSPC", null, now);
  assert.equal(fresh.status, "fresh");
  assert.equal(fresh.stale, false);
});

test("indices and Korea listings follow their own sessions", () => {
  const s = load();
  const now = at("2026-01-14T12:00:00Z");
  const ax = s.bb5eApply(quote(now, 40), "^AXJO", null, now);
  assert.equal(ax.status, "closed");
  assert.equal(ax.stale, false);
  assert.equal(ax.nextOpen, "2026-01-14T23:00:00.000Z");
  assert.equal(ax.note, "Sydney market closed · opens 23:00 UK");
  const named = s.bb5eApply(quote(now, 40), "ASX200", null, now);
  assert.equal(named.nextOpen, ax.nextOpen);

  const ks = s.bb5eApply(quote(now, 40), "005930.KS", null, now);
  assert.equal(ks.status, "closed");
  assert.equal(ks.nextOpen, "2026-01-15T00:00:00.000Z");
  assert.equal(ks.note, "Korea market closed · opens Thu 00:00 UK");
  assert.equal(s.bb5eApply(quote(now, 40), "^KS11", null, now).nextOpen, ks.nextOpen);
});

test("Yahoo marketState wins when the quote already carries it", () => {
  const s = load();
  const night = at("2026-01-14T02:00:00Z");
  const forced = s.bb5eApply(quote(night, 16), "AAPL", { marketState: "REGULAR" }, night);
  assert.equal(forced.status, "delayed");
  assert.equal(forced.stale, false);
  assert.equal(forced.nextOpen, undefined);
  assert.equal(forced.note, "delayed 15m by exchange");

  const session = at("2026-01-14T15:00:00Z");
  const holiday = s.bb5eApply(quote(session, 5, { delayMin: 0 }), "AAPL", { marketState: "CLOSED" }, session);
  assert.equal(holiday.status, "closed");
  assert.equal(holiday.stale, false);
  assert.equal(holiday.nextOpen, "2026-01-15T14:30:00.000Z");
  assert.equal(holiday.note, "US market closed · opens Thu 14:30 UK");

  const posted = s.bb5eApply(quote(night, 10), "AAPL", {
    marketState: "CLOSED",
    currentTradingPeriod: { regular: { start: at("2026-01-14T14:30:00Z") / 1000, end: at("2026-01-14T21:00:00Z") / 1000 } }
  }, night);
  assert.equal(posted.nextOpen, "2026-01-14T14:30:00.000Z");

  const chart = s.bb5eApply(quote(session, 16), "AAPL", {
    currentTradingPeriod: { regular: { start: at("2026-01-14T14:30:00Z") / 1000, end: at("2026-01-14T21:00:00Z") / 1000 } }
  }, session);
  assert.equal(chart.status, "delayed");
  assert.equal(chart.nextOpen, undefined);
});

test("an open path reuses bb5dClass and a second pass does not stack notes", () => {
  const s = load();
  let seen = 0;
  s.bb5dClass = function () {
    seen += 1;
    return { delayMin: 15, status: "delayed", stale: false, note: "delayed 15m by exchange" };
  };
  const now = at("2026-01-14T15:00:00Z");
  const once = s.bb5eApply(quote(now, 16), "AAPL", null, now);
  const twice = s.bb5eApply(once, "AAPL", null, now);
  assert.equal(seen, 2);
  assert.equal(twice.status, "delayed");
  assert.equal(twice.note, "delayed 15m by exchange");
  assert.equal(twice.nextOpen, undefined);
  assert.equal(s.bb5eApply(null, "AAPL", null, now), null);
});
