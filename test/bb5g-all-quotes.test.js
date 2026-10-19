const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");

const BB5E = "// BB5E_JS\nvar bb5eFmt = {};\nvar bb5eIdx = {\n  FTSE: [\"Europe/London\", 480, 990, \"London\"], \"^FTSE\": [\"Europe/London\", 480, 990, \"London\"],\n  DAX: [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"], \"^GDAXI\": [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"],\n  CAC: [\"Europe/Paris\", 540, 1050, \"Paris\"], \"^FCHI\": [\"Europe/Paris\", 540, 1050, \"Paris\"],\n  STOXX50: [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"],\n  N225: [\"Asia/Tokyo\", 540, 930, \"Tokyo\"], \"^N225\": [\"Asia/Tokyo\", 540, 930, \"Tokyo\"],\n  HSI: [\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\"], \"^HSI\": [\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\"],\n  NSEI: [\"Asia/Kolkata\", 555, 930, \"India\"], \"^NSEI\": [\"Asia/Kolkata\", 555, 930, \"India\"],\n  ASX200: [\"Australia/Sydney\", 600, 960, \"Sydney\"], \"^AXJO\": [\"Australia/Sydney\", 600, 960, \"Sydney\"],\n  KOSPI: [\"Asia/Seoul\", 540, 930, \"Korea\"], \"^KS11\": [\"Asia/Seoul\", 540, 930, \"Korea\"]\n};\nvar bb5eThin = {\n  USDINR: [\"Asia/Kolkata\", 555, 930, \"India\"], \"INR=X\": [\"Asia/Kolkata\", 555, 930, \"India\"],\n  USDBRL: [\"America/Sao_Paulo\", 600, 1020, \"Brazil\"], \"BRL=X\": [\"America/Sao_Paulo\", 600, 1020, \"Brazil\"],\n  USDKRW: [\"Asia/Seoul\", 540, 930, \"Korea\"], \"KRW=X\": [\"Asia/Seoul\", 540, 930, \"Korea\"],\n  USDTWD: [\"Asia/Taipei\", 540, 810, \"Taipei\"], \"TWD=X\": [\"Asia/Taipei\", 540, 810, \"Taipei\"],\n  USDIDR: [\"Asia/Jakarta\", 540, 900, \"Jakarta\"], \"IDR=X\": [\"Asia/Jakarta\", 540, 900, \"Jakarta\"],\n  USDPHP: [\"Asia/Manila\", 570, 900, \"Manila\"], \"PHP=X\": [\"Asia/Manila\", 570, 900, \"Manila\"]\n};\nvar bb5eFx = { EURUSD: 1, GBPUSD: 1, USDJPY: 1, AUDUSD: 1, USDCAD: 1, USDCHF: 1, NZDUSD: 1, EURGBP: 1, EURJPY: 1, GBPJPY: 1, USDMXN: 1, USDSEK: 1, DXY: 1, \"DX-Y.NYB\": 1, \"EURUSD=X\": 1, \"GBPUSD=X\": 1, \"JPY=X\": 1, \"AUDUSD=X\": 1, \"CAD=X\": 1, \"CHF=X\": 1, \"NZDUSD=X\": 1, \"EURGBP=X\": 1, \"EURJPY=X\": 1, \"GBPJPY=X\": 1, \"MXN=X\": 1, \"SEK=X\": 1 };\nvar bb5eCoin = { BTC: 1, ETH: 1, SOL: 1, XRP: 1, DOGE: 1, ADA: 1, AVAX: 1, LINK: 1, DOT: 1, LTC: 1, UNI: 1, POL: 1, NEAR: 1, ALGO: 1, HBAR: 1, BCH: 1, XLM: 1, FIL: 1, APT: 1, SUI: 1, ATOM: 1, INJ: 1, SHIB: 1, PEPE: 1, TON: 1 };\nvar bb5eSoft = { COFFEE: [255, 810], \"KC=F\": [255, 810], COCOA: [285, 810], \"CC=F\": [285, 810], OJ: [480, 840], \"OJ=F\": [480, 840], SUGAR: [210, 780] };\nvar bb5eCbot = { WHEAT: 1, CORN: 1, SOYBEAN: 1, SOYBEANS: 1, SOY: 1, OATS: 1, \"ZW=F\": 1, \"ZC=F\": 1, \"ZS=F\": 1, \"ZO=F\": 1 };\nvar bb5eLumber = { LUMBER: 1, \"LBR=F\": 1 };\nfunction bb5eNow() {\n  try {\n    if (typeof globalThis.bb5eClock === \"function\") {\n      var n = Number(globalThis.bb5eClock());\n      if (isFinite(n)) return n;\n    }\n  } catch (e) {}\n  return Date.now();\n}\nfunction bb5eCanon(symbol) {\n  return String(symbol || \"\").trim().toUpperCase();\n}\nfunction bb5eParts(tz, d) {\n  var fmt = bb5eFmt[tz];\n  if (!fmt) {\n    fmt = new Intl.DateTimeFormat(\"en-US\", { timeZone: tz, weekday: \"short\", hour: \"2-digit\", minute: \"2-digit\", hour12: false });\n    bb5eFmt[tz] = fmt;\n  }\n  var o = {};\n  fmt.formatToParts(d).forEach(function (part) { o[part.type] = part.value; });\n  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };\n}\nfunction bb5eWeekday(wd) {\n  return wd === \"Mon\" || wd === \"Tue\" || wd === \"Wed\" || wd === \"Thu\" || wd === \"Fri\";\n}\nfunction bb5eCash(tz, o, c, label, lo, lc) {\n  var spec = { mode: \"cash\", tz: tz, o: o, c: c, label: label };\n  if (lo != null) { spec.lo = lo; spec.lc = lc; }\n  return spec;\n}\nfunction bb5eSpec(symbol) {\n  var s = bb5eCanon(symbol);\n  var thin = bb5eThin[s];\n  if (thin) return { mode: \"thin\", quiet: true, tz: thin[0], o: thin[1], c: thin[2], label: thin[3] };\n  var idx = bb5eIdx[s];\n  if (idx) return bb5eCash(idx[0], idx[1], idx[2], idx[3]);\n  if (/\\.T$/.test(s)) return bb5eCash(\"Asia/Tokyo\", 540, 930, \"Tokyo\", 690, 750);\n  if (/\\.KS$/.test(s)) return bb5eCash(\"Asia/Seoul\", 540, 930, \"Korea\");\n  if (/\\.HK$/.test(s)) return bb5eCash(\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\", 720, 780);\n  if (/\\.L$/.test(s)) return bb5eCash(\"Europe/London\", 480, 990, \"London\");\n  if (/\\.DE$/.test(s)) return bb5eCash(\"Europe/Berlin\", 540, 1050, \"Frankfurt\");\n  if (/\\.PA$/.test(s)) return bb5eCash(\"Europe/Paris\", 540, 1050, \"Paris\");\n  if (/\\.AX$/.test(s)) return bb5eCash(\"Australia/Sydney\", 600, 960, \"Sydney\");\n  if (/\\.NS$/.test(s)) return bb5eCash(\"Asia/Kolkata\", 555, 930, \"India\");\n  if (bb5eCoin[s] || /-USD$/.test(s)) return { mode: \"always\", label: \"Crypto\" };\n  if (bb5eSoft[s]) return { mode: \"soft\", o: bb5eSoft[s][0], c: bb5eSoft[s][1], label: \"US\" };\n  if (bb5eCbot[s]) return { mode: \"cbot\", label: \"US\" };\n  if (bb5eLumber[s]) return { mode: \"lumber\", label: \"US\" };\n  if (/=F$/.test(s)) return { mode: \"fut\", label: \"US\" };\n  if (bb5eFx[s] || /=X$/.test(s)) return { mode: \"fx\", label: \"FX\" };\n  return bb5eCash(\"America/New_York\", 570, 960, \"US\");\n}\nfunction bb5eWindow(spec, d) {\n  var p = bb5eParts(spec.tz, d);\n  if (p.wd === \"Sat\" || p.wd === \"Sun\") return false;\n  if (spec.lo != null && p.m >= spec.lo && p.m < spec.lc) return false;\n  return p.m >= spec.o && p.m < spec.c;\n}\nfunction bb5eFxOpen(d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  if (p.wd === \"Sat\") return false;\n  if (p.wd === \"Fri\" && p.m >= 1020) return false;\n  if (p.wd === \"Sun\" && p.m < 1020) return false;\n  return true;\n}\nfunction bb5eFutOpen(d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  if (p.wd === \"Sat\") return false;\n  if (p.wd === \"Fri\" && p.m >= 1020) return false;\n  if (p.wd === \"Sun\" && p.m < 1080) return false;\n  if (p.m >= 1020 && p.m < 1080) return false;\n  return true;\n}\nfunction bb5eCbotOpen(d) {\n  var p = bb5eParts(\"America/Chicago\", d);\n  var evening = (p.wd === \"Sun\" || p.wd === \"Mon\" || p.wd === \"Tue\" || p.wd === \"Wed\" || p.wd === \"Thu\") && p.m >= 1140;\n  var day = bb5eWeekday(p.wd) && (p.m < 465 || (p.m >= 510 && p.m < 800));\n  return evening || day;\n}\nfunction bb5eSoftOpen(spec, d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  return bb5eWeekday(p.wd) && p.m >= spec.o && p.m < spec.c;\n}\nfunction bb5eLumberOpen(d) {\n  var p = bb5eParts(\"America/Chicago\", d);\n  return bb5eWeekday(p.wd) && p.m >= 540 && p.m < 905;\n}\nfunction bb5eOpenAt(spec, d) {\n  try {\n    if (!spec || spec.mode === \"always\") return true;\n    if (spec.mode === \"fx\") return bb5eFxOpen(d);\n    if (spec.mode === \"fut\") return bb5eFutOpen(d);\n    if (spec.mode === \"cbot\") return bb5eCbotOpen(d);\n    if (spec.mode === \"soft\") return bb5eSoftOpen(spec, d);\n    if (spec.mode === \"lumber\") return bb5eLumberOpen(d);\n    return bb5eWindow(spec, d);\n  } catch (e) { return true; }\n}\nfunction bb5eOffday(spec, d) {\n  try {\n    var tz = spec && (spec.mode === \"fx\" || spec.mode === \"fut\") ? \"America/New_York\" : (spec && spec.tz) || \"America/New_York\";\n    var p = bb5eParts(tz, d);\n    return p.wd === \"Sat\" || p.wd === \"Sun\";\n  } catch (e) { return false; }\n}\nfunction bb5eMs(v) {\n  var n = Number(v);\n  if (!isFinite(n) || n <= 0) return 0;\n  return n < 1e12 ? n * 1000 : n;\n}\nfunction bb5eYahoo(hints, now) {\n  if (!hints || typeof hints !== \"object\") return { known: false, open: false, next: 0 };\n  var state = String(hints.marketState || \"\").toUpperCase();\n  var reg = hints.currentTradingPeriod && hints.currentTradingPeriod.regular;\n  var start = reg ? bb5eMs(reg.start) : 0;\n  var end = reg ? bb5eMs(reg.end) : 0;\n  var shut = state === \"CLOSED\" || state === \"PRE\" || state === \"PREPRE\" || state === \"POST\" || state === \"POSTPOST\";\n  if (state === \"REGULAR\") return { known: true, open: true, next: 0 };\n  if (shut) return { known: true, open: false, next: start > now ? start : 0 };\n  if (start && end && now >= start && now < end) return { known: true, open: true, next: 0 };\n  if (start && end) return { known: true, open: false, next: start > now ? start : 0 };\n  return { known: false, open: false, next: 0 };\n}\nfunction bb5eNext(spec, now, yahooNext, force) {\n  if (yahooNext && yahooNext > now) return yahooNext;\n  var start = now;\n  if (force) {\n    var walk = now;\n    var guard = now + 18 * 3600000;\n    while (walk < guard && bb5eOpenAt(spec, new Date(walk))) walk += 300000;\n    start = walk;\n  }\n  var slot = Math.ceil((start + 1) / 900000) * 900000;\n  for (var k = 0; k < 8 * 96; k++, slot += 900000) {\n    if (bb5eOpenAt(spec, new Date(slot))) return slot;\n  }\n  return 0;\n}\nfunction bb5eLondon(ms, now) {\n  var tz = \"Europe/London\";\n  var d = new Date(ms);\n  var day = function (x) { return new Intl.DateTimeFormat(\"en-CA\", { timeZone: tz }).format(x); };\n  var hm = new Intl.DateTimeFormat(\"en-GB\", { timeZone: tz, hour: \"2-digit\", minute: \"2-digit\", hourCycle: \"h23\" }).format(d);\n  var wd = day(d) === day(new Date(now)) ? \"\" : new Intl.DateTimeFormat(\"en-GB\", { timeZone: tz, weekday: \"short\" }).format(d) + \" \";\n  return wd + hm;\n}\nfunction bb5eLive(q, now) {\n  var delay = Number(q && q.delayMin);\n  if (!isFinite(delay) || delay < 0) delay = 0;\n  delay = Math.round(delay);\n  var ts = Number(q && q.ts);\n  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;\n  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;\n  if (typeof bb5dClass === \"function\") return bb5dClass(age, delay);\n  var note = delay > 0 ? \"delayed \" + delay + \"m by exchange\" : \"\";\n  var cadence = typeof bb5dCadenceMs === \"number\" ? bb5dCadenceMs : 60000;\n  var margin = typeof bb5dMarginMs === \"number\" ? bb5dMarginMs : 120000;\n  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? \"delayed\" : \"fresh\", stale: false, note: note };\n  if (Number(age) > cadence + delay * 60000 + margin) return { delayMin: delay, status: \"stale\", stale: true, note: \"\" };\n  if (delay > 0) return { delayMin: delay, status: \"delayed\", stale: false, note: note };\n  return { delayMin: 0, status: \"fresh\", stale: false, note: \"\" };\n}\nfunction bb5eNote(spec, status, next, now) {\n  var when = next ? bb5eLondon(next, now) : \"\";\n  if (status === \"quiet\") return when ? \"quiet \u00b7 local market opens \" + when + \" UK\" : \"quiet\";\n  var label = (spec && spec.label) || \"Market\";\n  if (!when) return label + \" market closed\";\n  return label + \" market closed \u00b7 opens \" + when + \" UK\";\n}\nfunction bb5eApply(q, symbol, hints, now) {\n  if (!q || typeof q !== \"object\") return q;\n  var out = {};\n  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];\n  var t = now == null ? bb5eNow() : Number(now);\n  if (!isFinite(t)) t = bb5eNow();\n  var spec = bb5eSpec(symbol);\n  var yahoo = bb5eYahoo(hints, t);\n  var tableOpen = bb5eOpenAt(spec, new Date(t));\n  var open = typeof bb5fOpen === \"function\" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);\n  if (open) {\n    var cls = bb5eLive(out, t);\n    out.delayMin = cls.delayMin;\n    out.status = cls.status;\n    out.stale = cls.stale;\n    if (cls.note) out.note = cls.note;\n    else delete out.note;\n    delete out.nextOpen;\n    return out;\n  }\n  var next = bb5eNext(spec, t, yahoo.next, yahoo.known && !yahoo.open && tableOpen);\n  var status = typeof bb5fStatus === \"function\" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? \"quiet\" : \"closed\");\n  out.status = status;\n  out.stale = false;\n  if (next) out.nextOpen = new Date(next).toISOString();\n  else delete out.nextOpen;\n  out.note = bb5eNote(spec, status, next, t);\n  return out;\n}\n";
const BB5F = "// BB5F_JS\nvar bb5fAlias = { USDINR: \"INR=X\", USDBRL: \"BRL=X\" };\nfunction bb5fWire(symbol) {\n  var raw = String(symbol || \"\").trim();\n  if (!raw) return null;\n  var key = raw.toUpperCase();\n  var wire = raw;\n  try {\n    if (typeof BB3_ALIAS === \"object\" && BB3_ALIAS && BB3_ALIAS[key]) wire = String(BB3_ALIAS[key]);\n  } catch (e) {}\n  if (wire === raw && bb5fAlias[key]) wire = bb5fAlias[key];\n  var upper = wire.toUpperCase();\n  if (upper === \"USDINR=X\") wire = \"INR=X\";\n  if (upper === \"USDBRL=X\") wire = \"BRL=X\";\n  return { req: raw, wire: wire };\n}\nfunction bb5fOpen(spec, yahoo, tableOpen) {\n  if (spec && spec.quiet) return !!tableOpen;\n  if (yahoo && yahoo.known) return !!yahoo.open;\n  return !!tableOpen;\n}\nfunction bb5fStatus(spec, d) {\n  if (!spec || !spec.quiet) return \"closed\";\n  try {\n    if (typeof bb5eFxOpen === \"function\" && !bb5eFxOpen(d)) return \"closed\";\n  } catch (e) {\n    try { if (typeof bb5eOffday === \"function\" && bb5eOffday(spec, d)) return \"closed\"; } catch (e2) {}\n  }\n  return \"quiet\";\n}\nfunction bb5fNeedsChart(symbol, q) {\n  var spec = typeof bb5eSpec === \"function\" ? bb5eSpec(symbol) : null;\n  if (!spec || !spec.quiet) return false;\n  var ts = Number(q && q.ts);\n  return !(isFinite(ts) && ts > 0);\n}\nfunction bb5fRefill(q, symbol) {\n  if (!q || typeof q !== \"object\") return q;\n  var out = {};\n  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];\n  out.cached = true;\n  return out;\n}\nfunction bb5fPublish(data, now) {\n  if (!data || typeof data !== \"object\" || Array.isArray(data)) return data;\n  var t = now == null ? Date.now() : Number(now);\n  if (!isFinite(t)) t = Date.now();\n  var out = {};\n  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {\n    var q = data[k];\n    if (!q || typeof q !== \"object\" || typeof bb5eApply !== \"function\" || typeof bb5eSpec !== \"function\") { out[k] = q; continue; }\n    var spec = bb5eSpec(k);\n    if ((spec && spec.quiet) || q.cached) out[k] = bb5eApply(q, k, null, t);\n    else out[k] = q;\n  }\n  return out;\n}\n";
const BB5G = "// BB5G_JS\nfunction bb5gSpec(symbol) {\n  var s = typeof bb5eCanon === \"function\" ? bb5eCanon(symbol) : String(symbol || \"\").trim().toUpperCase();\n  if (s === \"HSI\" || s === \"^HSI\") return { mode: \"cash\", tz: \"Asia/Hong_Kong\", o: 570, c: 960, lo: 720, lc: 780, label: \"Hong Kong\" };\n  if (s === \"WTI\" || s === \"BRENT\" || s === \"CL=F\" || s === \"BZ=F\" || s === \"XAU\" || s === \"GC=F\" || s === \"XAU/USD\") return { mode: \"fut\", label: \"US\" };\n  if (s === \"DXY\" || s === \"DX-Y.NYB\") return { mode: \"fx\", label: \"FX\" };\n  if (s === \"BTC/USD\" || s === \"ETH/USD\") return { mode: \"always\", label: \"Crypto\" };\n  var slash = s.indexOf(\"/\") >= 0 ? s.replace(/\\//g, \"\") : \"\";\n  if (slash && typeof bb5eSpec === \"function\") {\n    if (typeof bb5eFx === \"object\" && bb5eFx && bb5eFx[slash]) return bb5eSpec(slash);\n    if (typeof bb5eThin === \"object\" && bb5eThin && bb5eThin[slash]) return bb5eSpec(slash);\n    return { mode: \"fx\", label: \"FX\" };\n  }\n  return typeof bb5eSpec === \"function\" ? bb5eSpec(s) : null;\n}\nfunction bb5gOpen(spec, yahoo, tableOpen) {\n  var scheduled = spec && (spec.quiet || spec.mode === \"cash\" || spec.mode === \"soft\" || spec.mode === \"lumber\" || spec.mode === \"cbot\" || spec.mode === \"thin\");\n  if (scheduled) {\n    if (!tableOpen) return false;\n    if (yahoo && yahoo.known && !yahoo.open) return false;\n    return true;\n  }\n  if (yahoo && yahoo.known) return !!yahoo.open;\n  return !!tableOpen;\n}\nfunction bb5gIsQuote(q) {\n  if (!q || typeof q !== \"object\" || Array.isArray(q)) return false;\n  var p = Number(q.p);\n  return isFinite(p) && p > 0;\n}\nfunction bb5gApply(q, symbol, now) {\n  if (!bb5gIsQuote(q) || typeof bb5eApply !== \"function\") return q;\n  var wasStale = q.stale === true;\n  var next = bb5eApply(q, symbol, null, now);\n  if (!next || typeof next !== \"object\") return q;\n  if (wasStale && next.status !== \"closed\" && next.status !== \"quiet\") next.stale = true;\n  return next;\n}\nfunction bb5gMap(map, now) {\n  if (!map || typeof map !== \"object\" || Array.isArray(map)) return map;\n  var out = {};\n  for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k)) out[k] = bb5gApply(map[k], k, now);\n  return out;\n}\nfunction bb5gPublish(data, now, symbol) {\n  if (!data || typeof data !== \"object\") return data;\n  if (Array.isArray(data)) return data;\n  var t = now == null ? Date.now() : Number(now);\n  if (!isFinite(t)) t = Date.now();\n  if (bb5gIsQuote(data)) return bb5gApply(data, symbol || data.symbol || data.name || \"\", t);\n  var out = {};\n  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {\n    if (k === \"quotes\" || k === \"directIndices\") out[k] = bb5gMap(data[k], t);\n    else out[k] = bb5gApply(data[k], k, t);\n  }\n  return out;\n}\nfunction bb5gJoinStream(acc, piece, firstModel) {\n  var s = String(piece || \"\");\n  acc = String(acc || \"\");\n  if (firstModel && acc && !/\\n$/.test(acc) && !/^\\n/.test(s)) s = \"\\n\" + s;\n  return { acc: acc + s, piece: s };\n}\n";

const openOld = `function bb5fOpen(spec, yahoo, tableOpen) {
  if (spec && spec.quiet) return !!tableOpen;
  if (yahoo && yahoo.known) return !!yahoo.open;
  return !!tableOpen;
}`;
const openNew = `function bb5fOpen(spec, yahoo, tableOpen) {
  return typeof bb5gOpen === "function" ? bb5gOpen(spec, yahoo, tableOpen) : (!!(spec && spec.quiet) ? !!tableOpen : (yahoo && yahoo.known ? !!yahoo.open : !!tableOpen));
}`;
const specOld = `  var spec = bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);`;
const specNew = `  var spec = typeof bb5gSpec === "function" ? bb5gSpec(symbol) : bb5eSpec(symbol);
  var yahoo = bb5eYahoo(hints, t);`;

let src = BB5E + "\n" + BB5F + "\n";
assert.equal(src.split(openOld).length, 2);
assert.equal(src.split(specOld).length, 2);
src = src.replace(openOld, openNew).replace(specOld, specNew) + "\n" + BB5G;

const context = {
  console, Date, Intl, Number, String, isFinite, Object, Array, Math, RegExp, JSON, Error
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(src, context, { filename: "bb5g-vendor.js" });

const REGULAR = { marketState: "REGULAR", currentTradingPeriod: { regular: { start: 1792364400, end: 1792450740 } } };
const MON = Date.parse("2026-10-19T02:07:00Z"); // 03:07 UK
const HK_OPEN = Date.parse("2026-10-19T03:30:00Z"); // 11:30 HKT
const HK_LUNCH = Date.parse("2026-10-19T04:30:00Z"); // 12:30 HKT
const SAT = Date.parse("2026-10-17T04:00:00Z");
const SUN = Date.parse("2026-10-18T16:00:00Z");
const COCOA_ON = Date.parse("2026-10-19T15:00:00Z"); // 11:00 ET

function row(ts, extra) {
  return Object.assign({ p: 10, c: 0, prev: 10, ts: ts, delayMin: 0, basis: "previous_close" }, extra || {});
}
function apply(symbol, ts, now, hints, extra) {
  return context.bb5eApply(row(ts, extra), symbol, hints || null, now);
}

test("AAPL on the Twelve Data path at 03:07 UK Monday is closed until 13:30Z", () => {
  const payload = context.bb5gPublish({
    quotes: { AAPL: row(Math.floor(Date.parse("2026-10-16T20:00:00Z") / 1000), { name: "Apple" }) },
    directIndices: {},
    fetchedAt: MON,
    provider: { id: "twelve-data" }
  }, MON);
  const q = payload.quotes.AAPL;
  assert.equal(q.status, "closed");
  assert.equal(q.stale, false);
  assert.equal(q.nextOpen, "2026-10-19T13:30:00.000Z");
  assert.match(q.note, /opens 14:30 UK/);
  assert.equal(typeof q.delayMin, "number");
  assert.equal(payload.fetchedAt, MON);
  assert.equal(payload.provider.id, "twelve-data");
});

test("0700.HK is delayed in the morning session, closed at lunch, and closed on Saturday", () => {
  const tick = Math.floor((HK_OPEN - 5 * 60 * 1000) / 1000);
  const open = apply("0700.HK", tick, HK_OPEN, REGULAR, { delayMin: 15 });
  assert.equal(open.status, "delayed");
  assert.equal(open.stale, false);
  assert.equal(open.nextOpen, undefined);
  assert.equal(open.delayMin, 15);
  const lunch = apply("0700.HK", tick, HK_LUNCH, REGULAR, { delayMin: 15 });
  assert.equal(lunch.status, "closed");
  assert.equal(lunch.stale, false);
  assert.equal(lunch.nextOpen, "2026-10-19T05:00:00.000Z");
  const sat = apply("0700.HK", tick, SAT, REGULAR, { delayMin: 15 });
  assert.equal(sat.status, "closed");
  assert.equal(sat.stale, false);
  assert.equal(sat.nextOpen, "2026-10-19T01:30:00.000Z");
  const hsi = apply("^HSI", tick, HK_LUNCH, REGULAR);
  assert.equal(hsi.status, "closed");
  assert.equal(hsi.nextOpen, "2026-10-19T05:00:00.000Z");
  assert.equal(context.bb5gSpec("HSI").lo, 720);
});

test("COFFEE is closed on Sunday and at 03:07 UK Monday, with today's open", () => {
  const fri = Math.floor(Date.parse("2026-10-16T17:00:00Z") / 1000);
  for (const now of [SUN, MON]) {
    const q = apply("COFFEE", fri, now, REGULAR);
    assert.equal(q.status, "closed");
    assert.equal(q.stale, false);
    assert.equal(q.nextOpen, "2026-10-19T08:15:00.000Z");
  }
  const kc = apply("KC=F", fri, MON, REGULAR);
  assert.equal(kc.status, "closed");
  assert.equal(kc.nextOpen, "2026-10-19T08:15:00.000Z");
});

test("COCOA during the session with a 24 minute tick is stale", () => {
  const ts = Math.floor((COCOA_ON - 24 * 60 * 1000) / 1000);
  const q = apply("COCOA", ts, COCOA_ON, REGULAR, { delayMin: 15 });
  assert.equal(q.status, "stale");
  assert.equal(q.stale, true);
  assert.equal(q.delayMin, 15);
  assert.equal(q.nextOpen, undefined);
  assert.equal(q.note, undefined);
});

test("every quote route item has a status", () => {
  const now = MON;
  const fri = Math.floor(Date.parse("2026-10-16T20:00:00Z") / 1000);
  const twelve = context.bb5gPublish({ quotes: { AAPL: row(fri), SPY: row(fri), "EUR/USD": row(Math.floor(now / 1000)) }, directIndices: { SPX: row(fri) } }, now);
  for (const q of [twelve.quotes.AAPL, twelve.quotes.SPY, twelve.quotes["EUR/USD"], twelve.directIndices.SPX]) {
    assert.ok(q.status);
    assert.equal(typeof q.stale, "boolean");
    assert.equal(typeof q.delayMin, "number");
  }
  assert.equal(twelve.quotes.AAPL.status, "closed");
  assert.equal(twelve.quotes["EUR/USD"].status, "fresh");
  const ref = context.bb5gPublish({ XAU: row(Math.floor(now / 1000)), DXY: row(Math.floor(now / 1000)), fetchedAt: now }, now);
  assert.ok(ref.XAU.status);
  assert.ok(ref.DXY.status);
  assert.equal(ref.fetchedAt, now);
  const fh = context.bb5gPublish(row(fri, { name: "AAPL" }), null, "AAPL");
  assert.equal(fh.status, "closed");
  assert.equal(fh.nextOpen, "2026-10-19T13:30:00.000Z");
  const yahoo = { "0700.HK": row(Math.floor(HK_LUNCH / 1000), { cached: true, status: "stale", stale: true }) };
  const published = context.bb5fPublish(yahoo, HK_LUNCH);
  assert.equal(published["0700.HK"].status, "closed");
  assert.equal(published["0700.HK"].cached, true);
});

test("Ask model chunks of NVIDIA (NVDA) has a reassemble exactly", () => {
  const text = "NVIDIA (NVDA) has a";
  const parts = ["NVID", "IA (", "NV", "DA) ha", "s a"];
  let acc = "";
  let out = "";
  parts.forEach((p, i) => {
    const j = context.bb5gJoinStream(acc, p, i === 0 && !acc);
    out += j.piece;
    acc = j.acc;
  });
  assert.equal(acc, text);
  assert.equal(out, text);
  const lead = context.bb5gJoinStream("Lead.", parts[0], true);
  assert.equal(lead.piece, "\n" + parts[0]);
  const next = context.bb5gJoinStream(lead.acc, parts[1], false);
  assert.equal(next.piece, parts[1]);
  assert.equal(next.acc, "Lead.\nNVIDIA (");
});

test("the patch is server-only and does not bump chat", () => {
  const patch = fs.readFileSync("deploy/patch_bb5g.py", "utf8");
  assert.match(patch, /bb5gPublish\(await twelveDataQuote/);
  assert.match(patch, /bb5gJoinStream\(acc, s, !modelAt\)/);
  assert.doesNotMatch(patch, /app\.js\?v=chat6[5-9]/);
  assert.match(patch, /b45b28623e1c8368140406558df95b90/);
  assert.match(patch, /b2271ff3debbf8790a4cdeb5a42b8297/);
});
