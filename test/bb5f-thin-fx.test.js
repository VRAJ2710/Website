const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const PATCH = path.join(__dirname, "..", "deploy", "patch_bb5f.py");
const BB5E = `var bb5eFmt = {};
var bb5eIdx = {
  FTSE: ["Europe/London", 480, 990, "London"], "^FTSE": ["Europe/London", 480, 990, "London"],
  DAX: ["Europe/Berlin", 540, 1050, "Frankfurt"], "^GDAXI": ["Europe/Berlin", 540, 1050, "Frankfurt"],
  CAC: ["Europe/Paris", 540, 1050, "Paris"], "^FCHI": ["Europe/Paris", 540, 1050, "Paris"],
  STOXX50: ["Europe/Berlin", 540, 1050, "Frankfurt"],
  N225: ["Asia/Tokyo", 540, 930, "Tokyo"], "^N225": ["Asia/Tokyo", 540, 930, "Tokyo"],
  HSI: ["Asia/Hong_Kong", 570, 960, "Hong Kong"], "^HSI": ["Asia/Hong_Kong", 570, 960, "Hong Kong"],
  NSEI: ["Asia/Kolkata", 555, 930, "India"], "^NSEI": ["Asia/Kolkata", 555, 930, "India"],
  ASX200: ["Australia/Sydney", 600, 960, "Sydney"], "^AXJO": ["Australia/Sydney", 600, 960, "Sydney"],
  KOSPI: ["Asia/Seoul", 540, 930, "Korea"], "^KS11": ["Asia/Seoul", 540, 930, "Korea"]
};
var bb5eThin = {
  USDINR: ["Asia/Kolkata", 555, 930, "India"], "INR=X": ["Asia/Kolkata", 555, 930, "India"],
  USDBRL: ["America/Sao_Paulo", 600, 1020, "Brazil"], "BRL=X": ["America/Sao_Paulo", 600, 1020, "Brazil"],
  USDKRW: ["Asia/Seoul", 540, 930, "Korea"], "KRW=X": ["Asia/Seoul", 540, 930, "Korea"],
  USDTWD: ["Asia/Taipei", 540, 810, "Taipei"], "TWD=X": ["Asia/Taipei", 540, 810, "Taipei"],
  USDIDR: ["Asia/Jakarta", 540, 900, "Jakarta"], "IDR=X": ["Asia/Jakarta", 540, 900, "Jakarta"],
  USDPHP: ["Asia/Manila", 570, 900, "Manila"], "PHP=X": ["Asia/Manila", 570, 900, "Manila"]
};
var bb5eFx = { EURUSD: 1, GBPUSD: 1, USDJPY: 1, AUDUSD: 1, USDCAD: 1, USDCHF: 1, NZDUSD: 1, EURGBP: 1, EURJPY: 1, GBPJPY: 1, USDMXN: 1, USDSEK: 1, DXY: 1, "DX-Y.NYB": 1, "EURUSD=X": 1, "GBPUSD=X": 1, "JPY=X": 1, "AUDUSD=X": 1, "CAD=X": 1, "CHF=X": 1, "NZDUSD=X": 1, "EURGBP=X": 1, "EURJPY=X": 1, "GBPJPY=X": 1, "MXN=X": 1, "SEK=X": 1 };
var bb5eCoin = { BTC: 1, ETH: 1, SOL: 1, XRP: 1, DOGE: 1, ADA: 1, AVAX: 1, LINK: 1, DOT: 1, LTC: 1, UNI: 1, POL: 1, NEAR: 1, ALGO: 1, HBAR: 1, BCH: 1, XLM: 1, FIL: 1, APT: 1, SUI: 1, ATOM: 1, INJ: 1, SHIB: 1, PEPE: 1, TON: 1 };
var bb5eSoft = { COFFEE: [255, 810], "KC=F": [255, 810], COCOA: [285, 810], "CC=F": [285, 810], OJ: [480, 840], "OJ=F": [480, 840], SUGAR: [210, 780] };
var bb5eCbot = { WHEAT: 1, CORN: 1, SOYBEAN: 1, SOYBEANS: 1, SOY: 1, OATS: 1, "ZW=F": 1, "ZC=F": 1, "ZS=F": 1, "ZO=F": 1 };
var bb5eLumber = { LUMBER: 1, "LBR=F": 1 };
function bb5eNow() {
  try {
    if (typeof globalThis.bb5eClock === "function") {
      var n = Number(globalThis.bb5eClock());
      if (isFinite(n)) return n;
    }
  } catch (e) {}
  return Date.now();
}
function bb5eCanon(symbol) {
  return String(symbol || "").trim().toUpperCase();
}
function bb5eParts(tz, d) {
  var fmt = bb5eFmt[tz];
  if (!fmt) {
    fmt = new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false });
    bb5eFmt[tz] = fmt;
  }
  var o = {};
  fmt.formatToParts(d).forEach(function (part) { o[part.type] = part.value; });
  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };
}
function bb5eWeekday(wd) {
  return wd === "Mon" || wd === "Tue" || wd === "Wed" || wd === "Thu" || wd === "Fri";
}
function bb5eCash(tz, o, c, label, lo, lc) {
  var spec = { mode: "cash", tz: tz, o: o, c: c, label: label };
  if (lo != null) { spec.lo = lo; spec.lc = lc; }
  return spec;
}
function bb5eSpec(symbol) {
  var s = bb5eCanon(symbol);
  var thin = bb5eThin[s];
  if (thin) return { mode: "thin", quiet: true, tz: thin[0], o: thin[1], c: thin[2], label: thin[3] };
  var idx = bb5eIdx[s];
  if (idx) return bb5eCash(idx[0], idx[1], idx[2], idx[3]);
  if (/\\.T$/.test(s)) return bb5eCash("Asia/Tokyo", 540, 930, "Tokyo", 690, 750);
  if (/\\.KS$/.test(s)) return bb5eCash("Asia/Seoul", 540, 930, "Korea");
  if (/\\.HK$/.test(s)) return bb5eCash("Asia/Hong_Kong", 570, 960, "Hong Kong", 720, 780);
  if (/\\.L$/.test(s)) return bb5eCash("Europe/London", 480, 990, "London");
  if (/\\.DE$/.test(s)) return bb5eCash("Europe/Berlin", 540, 1050, "Frankfurt");
  if (/\\.PA$/.test(s)) return bb5eCash("Europe/Paris", 540, 1050, "Paris");
  if (/\\.AX$/.test(s)) return bb5eCash("Australia/Sydney", 600, 960, "Sydney");
  if (/\\.NS$/.test(s)) return bb5eCash("Asia/Kolkata", 555, 930, "India");
  if (bb5eCoin[s] || /-USD$/.test(s)) return { mode: "always", label: "Crypto" };
  if (bb5eSoft[s]) return { mode: "soft", o: bb5eSoft[s][0], c: bb5eSoft[s][1], label: "US" };
  if (bb5eCbot[s]) return { mode: "cbot", label: "US" };
  if (bb5eLumber[s]) return { mode: "lumber", label: "US" };
  if (/=F$/.test(s)) return { mode: "fut", label: "US" };
  if (bb5eFx[s] || /=X$/.test(s)) return { mode: "fx", label: "FX" };
  return bb5eCash("America/New_York", 570, 960, "US");
}
function bb5eWindow(spec, d) {
  var p = bb5eParts(spec.tz, d);
  if (p.wd === "Sat" || p.wd === "Sun") return false;
  if (spec.lo != null && p.m >= spec.lo && p.m < spec.lc) return false;
  return p.m >= spec.o && p.m < spec.c;
}
function bb5eFxOpen(d) {
  var p = bb5eParts("America/New_York", d);
  if (p.wd === "Sat") return false;
  if (p.wd === "Fri" && p.m >= 1020) return false;
  if (p.wd === "Sun" && p.m < 1020) return false;
  return true;
}
function bb5eFutOpen(d) {
  var p = bb5eParts("America/New_York", d);
  if (p.wd === "Sat") return false;
  if (p.wd === "Fri" && p.m >= 1020) return false;
  if (p.wd === "Sun" && p.m < 1080) return false;
  if (p.m >= 1020 && p.m < 1080) return false;
  return true;
}
function bb5eCbotOpen(d) {
  var p = bb5eParts("America/Chicago", d);
  var evening = (p.wd === "Sun" || p.wd === "Mon" || p.wd === "Tue" || p.wd === "Wed" || p.wd === "Thu") && p.m >= 1140;
  var day = bb5eWeekday(p.wd) && (p.m < 465 || (p.m >= 510 && p.m < 800));
  return evening || day;
}
function bb5eSoftOpen(spec, d) {
  var p = bb5eParts("America/New_York", d);
  return bb5eWeekday(p.wd) && p.m >= spec.o && p.m < spec.c;
}
function bb5eLumberOpen(d) {
  var p = bb5eParts("America/Chicago", d);
  return bb5eWeekday(p.wd) && p.m >= 540 && p.m < 905;
}
function bb5eOpenAt(spec, d) {
  try {
    if (!spec || spec.mode === "always") return true;
    if (spec.mode === "fx") return bb5eFxOpen(d);
    if (spec.mode === "fut") return bb5eFutOpen(d);
    if (spec.mode === "cbot") return bb5eCbotOpen(d);
    if (spec.mode === "soft") return bb5eSoftOpen(spec, d);
    if (spec.mode === "lumber") return bb5eLumberOpen(d);
    return bb5eWindow(spec, d);
  } catch (e) { return true; }
}
function bb5eOffday(spec, d) {
  try {
    var tz = spec && (spec.mode === "fx" || spec.mode === "fut") ? "America/New_York" : (spec && spec.tz) || "America/New_York";
    var p = bb5eParts(tz, d);
    return p.wd === "Sat" || p.wd === "Sun";
  } catch (e) { return false; }
}
function bb5eMs(v) {
  var n = Number(v);
  if (!isFinite(n) || n <= 0) return 0;
  return n < 1e12 ? n * 1000 : n;
}
function bb5eYahoo(hints, now) {
  if (!hints || typeof hints !== "object") return { known: false, open: false, next: 0 };
  var state = String(hints.marketState || "").toUpperCase();
  var reg = hints.currentTradingPeriod && hints.currentTradingPeriod.regular;
  var start = reg ? bb5eMs(reg.start) : 0;
  var end = reg ? bb5eMs(reg.end) : 0;
  var shut = state === "CLOSED" || state === "PRE" || state === "PREPRE" || state === "POST" || state === "POSTPOST";
  if (state === "REGULAR") return { known: true, open: true, next: 0 };
  if (shut) return { known: true, open: false, next: start > now ? start : 0 };
  if (start && end && now >= start && now < end) return { known: true, open: true, next: 0 };
  if (start && end) return { known: true, open: false, next: start > now ? start : 0 };
  return { known: false, open: false, next: 0 };
}
function bb5eNext(spec, now, yahooNext, force) {
  if (yahooNext && yahooNext > now) return yahooNext;
  var start = now;
  if (force) {
    var walk = now;
    var guard = now + 18 * 3600000;
    while (walk < guard && bb5eOpenAt(spec, new Date(walk))) walk += 300000;
    start = walk;
  }
  var slot = Math.ceil((start + 1) / 900000) * 900000;
  for (var k = 0; k < 8 * 96; k++, slot += 900000) {
    if (bb5eOpenAt(spec, new Date(slot))) return slot;
  }
  return 0;
}
function bb5eLondon(ms, now) {
  var tz = "Europe/London";
  var d = new Date(ms);
  var day = function (x) { return new Intl.DateTimeFormat("en-CA", { timeZone: tz }).format(x); };
  var hm = new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(d);
  var wd = day(d) === day(new Date(now)) ? "" : new Intl.DateTimeFormat("en-GB", { timeZone: tz, weekday: "short" }).format(d) + " ";
  return wd + hm;
}
function bb5eLive(q, now) {
  var delay = Number(q && q.delayMin);
  if (!isFinite(delay) || delay < 0) delay = 0;
  delay = Math.round(delay);
  var ts = Number(q && q.ts);
  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;
  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;
  if (typeof bb5dClass === "function") return bb5dClass(age, delay);
  var note = delay > 0 ? "delayed " + delay + "m by exchange" : "";
  var cadence = typeof bb5dCadenceMs === "number" ? bb5dCadenceMs : 60000;
  var margin = typeof bb5dMarginMs === "number" ? bb5dMarginMs : 120000;
  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? "delayed" : "fresh", stale: false, note: note };
  if (Number(age) > cadence + delay * 60000 + margin) return { delayMin: delay, status: "stale", stale: true, note: "" };
  if (delay > 0) return { delayMin: delay, status: "delayed", stale: false, note: note };
  return { delayMin: 0, status: "fresh", stale: false, note: "" };
}
function bb5eNote(spec, status, next, now) {
  var when = next ? bb5eLondon(next, now) : "";
  if (status === "quiet") return when ? "quiet · local market opens " + when + " UK" : "quiet";
  var label = (spec && spec.label) || "Market";
  if (!when) return label + " market closed";
  return label + " market closed · opens " + when + " UK";
}
function bb5eApply(q, symbol, hints, now) {
  if (!q || typeof q !== "object") return q;
  var out = {};
  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];
  var t = now == null ? bb5eNow() : Number(now);
  if (!isFinite(t)) t = bb5eNow();
  var spec = bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);
  var tableOpen = bb5eOpenAt(spec, new Date(t));
  var open = yahoo.known ? yahoo.open : tableOpen;
  if (open) {
    var cls = bb5eLive(out, t);
    out.delayMin = cls.delayMin;
    out.status = cls.status;
    out.stale = cls.stale;
    if (cls.note) out.note = cls.note;
    else delete out.note;
    delete out.nextOpen;
    return out;
  }
  var next = bb5eNext(spec, t, yahoo.next, yahoo.known && !yahoo.open && tableOpen);
  var status = spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed";
  out.status = status;
  out.stale = false;
  if (next) out.nextOpen = new Date(next).toISOString();
  else delete out.nextOpen;
  out.note = bb5eNote(spec, status, next, t);
  return out;
}`;

function extract(src, name) {
  const m = src.match(new RegExp("// " + name + "\\n([\\s\\S]*?)\\n// " + name + "_END"));
  assert.ok(m, name + " block missing");
  return m[1];
}

function load() {
  const src = fs.readFileSync(PATCH, "utf8");
  const js = extract(src, "BB5F_JS");
  assert.equal(/CREATE TABLE|setInterval\(|stripe\.webhooks/.test(js), false);
  const names = [...js.matchAll(/(?:^|\n)\s*(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(/g)].map(x => x[1]);
  assert.ok(names.length > 0);
  assert.ok(names.every(name => name.startsWith("bb5f")), names.join(","));
  assert.equal(new Set(names).size, names.length);
  assert.equal(src.includes("app.js?v=chat"), false);
  assert.equal(src.includes("return bb5fWire(symbol);"), true);
  let bb5e = BB5E;
  const openOld = "var open = yahoo.known ? yahoo.open : tableOpen;";
  const openNew = 'var open = typeof bb5fOpen === "function" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);';
  const statusOld = 'var status = spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed";';
  const statusNew = 'var status = typeof bb5fStatus === "function" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? "quiet" : "closed");';
  assert.equal(bb5e.includes(openOld), true);
  assert.equal(bb5e.includes(statusOld), true);
  bb5e = bb5e.replace(openOld, openNew).replace(statusOld, statusNew);
  const context = { console, Intl, Date, Math, Number, String, isFinite, Object };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(bb5e + "\n" + js, context, { filename: "bb5f.js" });
  context.BB3_ALIAS = { USDINR: "INR=X", USDBRL: "BRL=X", EURUSD: "EURUSD=X" };
  context.bb5dWire = function (symbol) { return context.bb5fWire(symbol); };
  return context;
}

function at(iso) { return Date.parse(iso); }

const LONDON_NIGHT = at("2026-10-19T01:17:00Z"); // 02:17 UK, 06:47 IST
const MUMBAI = at("2026-10-19T05:00:00Z"); // 10:30 IST
const PERIOD = { regular: { start: 1792364400, end: 1792450740 } };

function row(now, ageMin, extra) {
  const ts = extra && extra.ts != null ? extra.ts : Math.floor((now - ageMin * 60000) / 1000);
  return Object.assign({
    p: 94.95, c: 0, prev: 94.95, change: 0, currency: "INR", basis: "previous_close",
    exchange: "CCY", name: "USD/INR", ts, delayMin: 0
  }, extra, { ts });
}

test("USDINR at 02:17 UK is quiet until 04:45 UK from a fresh row and a refill", () => {
  const s = load();
  const hints = { marketState: "REGULAR", currentTradingPeriod: PERIOD };
  const fresh = s.bb5eApply(row(LONDON_NIGHT, 60, { ts: 1792369028, delayMin: 15 }), "INR=X", hints, LONDON_NIGHT);
  assert.equal(fresh.status, "quiet");
  assert.equal(fresh.stale, false);
  assert.equal(fresh.ts, 1792369028);
  assert.equal(fresh.basis, "previous_close");
  assert.equal(fresh.delayMin, 15);
  assert.equal(fresh.nextOpen, "2026-10-19T03:45:00.000Z");
  assert.equal(fresh.note, "quiet · local market opens 04:45 UK");
  const named = s.bb5eApply(row(LONDON_NIGHT, 60, { ts: 1792369028 }), "USDINR", hints, LONDON_NIGHT);
  assert.equal(named.status, "quiet");
  assert.equal(named.nextOpen, fresh.nextOpen);

  const stored = { INR: { p: 94.9, c: 0, prev: 94.7, change: 0.2, currency: "INR", basis: "previous_close", exchange: "CCY", name: "USD/INR", ts: 1792369028, delayMin: 15, status: "stale", stale: true } };
  const refilled = s.bb5fPublish({ "INR=X": s.bb5fRefill(stored.INR, "INR=X") }, LONDON_NIGHT);
  assert.equal(refilled["INR=X"].status, "quiet");
  assert.equal(refilled["INR=X"].stale, false);
  assert.equal(refilled["INR=X"].cached, true);
  assert.equal(refilled["INR=X"].basis, "previous_close");
  assert.equal(refilled["INR=X"].ts, 1792369028);
  assert.equal(refilled["INR=X"].nextOpen, "2026-10-19T03:45:00.000Z");
  assert.equal(refilled["INR=X"].note, "quiet · local market opens 04:45 UK");
});

test("USDBRL at 02:17 UK is quiet until the B3 open in UK time", () => {
  const s = load();
  const hints = { marketState: "REGULAR", currentTradingPeriod: PERIOD };
  const out = s.bb5eApply(row(LONDON_NIGHT, 60, { ts: 1792369028, currency: "BRL", p: 5.06, name: "USD/BRL" }), "BRL=X", hints, LONDON_NIGHT);
  assert.equal(out.status, "quiet");
  assert.equal(out.stale, false);
  assert.equal(out.nextOpen, "2026-10-19T13:00:00.000Z");
  assert.equal(out.note, "quiet · local market opens 14:00 UK");
  const named = s.bb5eApply(row(LONDON_NIGHT, 60, { currency: "BRL" }), "USDBRL", hints, LONDON_NIGHT);
  assert.equal(named.status, "quiet");
  assert.equal(named.nextOpen, out.nextOpen);
});

test("USDINR during the NSE session with a 24 minute tick is stale", () => {
  const s = load();
  const q = row(MUMBAI, 24, { delayMin: 15 });
  const out = s.bb5eApply(q, "USDINR", { marketState: "REGULAR", currentTradingPeriod: PERIOD }, MUMBAI);
  assert.equal(out.status, "stale");
  assert.equal(out.stale, true);
  assert.equal(out.delayMin, 15);
  assert.equal(out.nextOpen, undefined);
  assert.equal(out.note, undefined);
  assert.equal(out.ts, q.ts);
});

test("the fetch wire is INR=X and BRL=X, never a six-letter =X symbol", () => {
  const s = load();
  assert.equal(s.bb5fWire("USDINR").wire, "INR=X");
  assert.equal(s.bb5fWire("USDBRL").wire, "BRL=X");
  assert.equal(s.bb5fWire("INR=X").wire, "INR=X");
  assert.equal(s.bb5fWire("BRL=X").wire, "BRL=X");
  assert.equal(s.bb5fWire("USDINR=X").wire, "INR=X");
  assert.equal(s.bb5fWire("USDBRL=X").wire, "BRL=X");
  assert.equal(s.bb5dWire("USDINR").wire, "INR=X");
  assert.equal(s.bb5dWire("USDBRL").wire, "BRL=X");
  s.BB3_ALIAS = null;
  assert.equal(s.bb5fWire("USDINR").wire, "INR=X");
  assert.equal(s.bb5fWire("EURUSD").wire, "EURUSD");
});

test("two refilled pairs keep their own print times", () => {
  const s = load();
  const a = s.bb5fRefill({ p: 94.9, prev: 94.7, c: 0, change: 0, currency: "INR", basis: "previous_close", ts: 1792369028, delayMin: 0, status: "stale", stale: true }, "INR=X");
  const b = s.bb5fRefill({ p: 5.06, prev: 5.07, c: 0, change: 0, currency: "BRL", basis: "previous_close", ts: 1792361000, delayMin: 0, status: "stale", stale: true }, "BRL=X");
  const out = s.bb5fPublish({ "INR=X": a, "BRL=X": b }, LONDON_NIGHT);
  assert.equal(out["INR=X"].ts, 1792369028);
  assert.equal(out["BRL=X"].ts, 1792361000);
  assert.notEqual(out["INR=X"].ts, out["BRL=X"].ts);
  assert.equal(out["INR=X"].cached, true);
  assert.equal(out["BRL=X"].cached, true);
  assert.equal(out["INR=X"].status, "quiet");
  assert.equal(out["BRL=X"].status, "quiet");
  assert.equal(out["INR=X"].stale, false);
  assert.equal(out["BRL=X"].basis, "previous_close");
});

test("EURUSD at the same clock stays on the 24/5 rule", () => {
  const s = load();
  const hints = { marketState: "REGULAR", currentTradingPeriod: PERIOD };
  const fresh = s.bb5eApply(row(LONDON_NIGHT, 0.5, { delayMin: 0, currency: "USD", p: 1.12, name: "EUR/USD" }), "EURUSD=X", hints, LONDON_NIGHT);
  assert.equal(fresh.status, "fresh");
  assert.equal(fresh.stale, false);
  assert.equal(fresh.nextOpen, undefined);
  const old = s.bb5eApply(row(LONDON_NIGHT, 45, { delayMin: 0, currency: "USD", p: 1.12 }), "EURUSD", hints, LONDON_NIGHT);
  assert.equal(old.status, "stale");
  assert.equal(old.stale, true);
  const saturday = at("2026-10-17T12:00:00Z");
  const closed = s.bb5eApply(row(saturday, 30, { delayMin: 0 }), "EURUSD=X", null, saturday);
  assert.equal(closed.status, "closed");
  assert.equal(closed.stale, false);
});
