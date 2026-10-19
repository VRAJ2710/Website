const assert = require("node:assert");
const test = require("node:test");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const VENDOR = "var TWELVE_DATA_CACHE_MS = 15 * 60 * 1000;\nvar TWELVE_DATA_REFRESH_LEASE_MS = 30 * 1000;\nvar REFERENCE_QUOTE_CACHE_MS = 5 * 60 * 1000;\nvar bb5dCadenceMs = 60000;\nvar bb5dMarginMs = 120000;\nfunction bb5dClass(ageMs, delayMin) {\n  var delay = Number(delayMin);\n  if (!isFinite(delay) || delay < 0) delay = 0;\n  delay = Math.round(delay);\n  var note = delay > 0 ? \"delayed \" + delay + \"m by exchange\" : \"\";\n  if (ageMs == null || !isFinite(Number(ageMs))) return { delayMin: delay, status: delay > 0 ? \"delayed\" : \"fresh\", stale: false, note: note };\n  var allowance = bb5dCadenceMs + delay * 60000 + bb5dMarginMs;\n  if (Number(ageMs) > allowance) return { delayMin: delay, status: \"stale\", stale: true, note: \"\" };\n  if (delay > 0) return { delayMin: delay, status: \"delayed\", stale: false, note: note };\n  return { delayMin: 0, status: \"fresh\", stale: false, note: \"\" };\n}\nvar bb5eFmt = {};\nvar bb5eIdx = {\n  FTSE: [\"Europe/London\", 480, 990, \"London\"], \"^FTSE\": [\"Europe/London\", 480, 990, \"London\"],\n  DAX: [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"], \"^GDAXI\": [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"],\n  CAC: [\"Europe/Paris\", 540, 1050, \"Paris\"], \"^FCHI\": [\"Europe/Paris\", 540, 1050, \"Paris\"],\n  STOXX50: [\"Europe/Berlin\", 540, 1050, \"Frankfurt\"],\n  N225: [\"Asia/Tokyo\", 540, 930, \"Tokyo\"], \"^N225\": [\"Asia/Tokyo\", 540, 930, \"Tokyo\"],\n  HSI: [\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\"], \"^HSI\": [\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\"],\n  NSEI: [\"Asia/Kolkata\", 555, 930, \"India\"], \"^NSEI\": [\"Asia/Kolkata\", 555, 930, \"India\"],\n  ASX200: [\"Australia/Sydney\", 600, 960, \"Sydney\"], \"^AXJO\": [\"Australia/Sydney\", 600, 960, \"Sydney\"],\n  KOSPI: [\"Asia/Seoul\", 540, 930, \"Korea\"], \"^KS11\": [\"Asia/Seoul\", 540, 930, \"Korea\"]\n};\nvar bb5eThin = {\n  USDINR: [\"Asia/Kolkata\", 555, 930, \"India\"], \"INR=X\": [\"Asia/Kolkata\", 555, 930, \"India\"],\n  USDBRL: [\"America/Sao_Paulo\", 600, 1020, \"Brazil\"], \"BRL=X\": [\"America/Sao_Paulo\", 600, 1020, \"Brazil\"],\n  USDKRW: [\"Asia/Seoul\", 540, 930, \"Korea\"], \"KRW=X\": [\"Asia/Seoul\", 540, 930, \"Korea\"],\n  USDTWD: [\"Asia/Taipei\", 540, 810, \"Taipei\"], \"TWD=X\": [\"Asia/Taipei\", 540, 810, \"Taipei\"],\n  USDIDR: [\"Asia/Jakarta\", 540, 900, \"Jakarta\"], \"IDR=X\": [\"Asia/Jakarta\", 540, 900, \"Jakarta\"],\n  USDPHP: [\"Asia/Manila\", 570, 900, \"Manila\"], \"PHP=X\": [\"Asia/Manila\", 570, 900, \"Manila\"]\n};\nvar bb5eFx = { EURUSD: 1, GBPUSD: 1, USDJPY: 1, AUDUSD: 1, USDCAD: 1, USDCHF: 1, NZDUSD: 1, EURGBP: 1, EURJPY: 1, GBPJPY: 1, USDMXN: 1, USDSEK: 1, DXY: 1, \"DX-Y.NYB\": 1, \"EURUSD=X\": 1, \"GBPUSD=X\": 1, \"JPY=X\": 1, \"AUDUSD=X\": 1, \"CAD=X\": 1, \"CHF=X\": 1, \"NZDUSD=X\": 1, \"EURGBP=X\": 1, \"EURJPY=X\": 1, \"GBPJPY=X\": 1, \"MXN=X\": 1, \"SEK=X\": 1 };\nvar bb5eCoin = { BTC: 1, ETH: 1, SOL: 1, XRP: 1, DOGE: 1, ADA: 1, AVAX: 1, LINK: 1, DOT: 1, LTC: 1, UNI: 1, POL: 1, NEAR: 1, ALGO: 1, HBAR: 1, BCH: 1, XLM: 1, FIL: 1, APT: 1, SUI: 1, ATOM: 1, INJ: 1, SHIB: 1, PEPE: 1, TON: 1 };\nvar bb5eSoft = { COFFEE: [255, 810], \"KC=F\": [255, 810], COCOA: [285, 810], \"CC=F\": [285, 810], OJ: [480, 840], \"OJ=F\": [480, 840], SUGAR: [210, 780] };\nvar bb5eCbot = { WHEAT: 1, CORN: 1, SOYBEAN: 1, SOYBEANS: 1, SOY: 1, OATS: 1, \"ZW=F\": 1, \"ZC=F\": 1, \"ZS=F\": 1, \"ZO=F\": 1 };\nvar bb5eLumber = { LUMBER: 1, \"LBR=F\": 1 };\nfunction bb5eNow() {\n  try {\n    if (typeof globalThis.bb5eClock === \"function\") {\n      var n = Number(globalThis.bb5eClock());\n      if (isFinite(n)) return n;\n    }\n  } catch (e) {}\n  return Date.now();\n}\nfunction bb5eCanon(symbol) {\n  return String(symbol || \"\").trim().toUpperCase();\n}\nfunction bb5eParts(tz, d) {\n  var fmt = bb5eFmt[tz];\n  if (!fmt) {\n    fmt = new Intl.DateTimeFormat(\"en-US\", { timeZone: tz, weekday: \"short\", hour: \"2-digit\", minute: \"2-digit\", hour12: false });\n    bb5eFmt[tz] = fmt;\n  }\n  var o = {};\n  fmt.formatToParts(d).forEach(function (part) { o[part.type] = part.value; });\n  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };\n}\nfunction bb5eWeekday(wd) {\n  return wd === \"Mon\" || wd === \"Tue\" || wd === \"Wed\" || wd === \"Thu\" || wd === \"Fri\";\n}\nfunction bb5eCash(tz, o, c, label, lo, lc) {\n  var spec = { mode: \"cash\", tz: tz, o: o, c: c, label: label };\n  if (lo != null) { spec.lo = lo; spec.lc = lc; }\n  return spec;\n}\nfunction bb5eSpec(symbol) {\n  var s = bb5eCanon(symbol);\n  var thin = bb5eThin[s];\n  if (thin) return { mode: \"thin\", quiet: true, tz: thin[0], o: thin[1], c: thin[2], label: thin[3] };\n  var idx = bb5eIdx[s];\n  if (idx) return bb5eCash(idx[0], idx[1], idx[2], idx[3]);\n  if (/\\.T$/.test(s)) return bb5eCash(\"Asia/Tokyo\", 540, 930, \"Tokyo\", 690, 750);\n  if (/\\.KS$/.test(s)) return bb5eCash(\"Asia/Seoul\", 540, 930, \"Korea\");\n  if (/\\.HK$/.test(s)) return bb5eCash(\"Asia/Hong_Kong\", 570, 960, \"Hong Kong\", 720, 780);\n  if (/\\.L$/.test(s)) return bb5eCash(\"Europe/London\", 480, 990, \"London\");\n  if (/\\.DE$/.test(s)) return bb5eCash(\"Europe/Berlin\", 540, 1050, \"Frankfurt\");\n  if (/\\.PA$/.test(s)) return bb5eCash(\"Europe/Paris\", 540, 1050, \"Paris\");\n  if (/\\.AX$/.test(s)) return bb5eCash(\"Australia/Sydney\", 600, 960, \"Sydney\");\n  if (/\\.NS$/.test(s)) return bb5eCash(\"Asia/Kolkata\", 555, 930, \"India\");\n  if (bb5eCoin[s] || /-USD$/.test(s)) return { mode: \"always\", label: \"Crypto\" };\n  if (bb5eSoft[s]) return { mode: \"soft\", o: bb5eSoft[s][0], c: bb5eSoft[s][1], label: \"US\" };\n  if (bb5eCbot[s]) return { mode: \"cbot\", label: \"US\" };\n  if (bb5eLumber[s]) return { mode: \"lumber\", label: \"US\" };\n  if (/=F$/.test(s)) return { mode: \"fut\", label: \"US\" };\n  if (bb5eFx[s] || /=X$/.test(s)) return { mode: \"fx\", label: \"FX\" };\n  return bb5eCash(\"America/New_York\", 570, 960, \"US\");\n}\nfunction bb5eWindow(spec, d) {\n  var p = bb5eParts(spec.tz, d);\n  if (p.wd === \"Sat\" || p.wd === \"Sun\") return false;\n  if (spec.lo != null && p.m >= spec.lo && p.m < spec.lc) return false;\n  return p.m >= spec.o && p.m < spec.c;\n}\nfunction bb5eFxOpen(d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  if (p.wd === \"Sat\") return false;\n  if (p.wd === \"Fri\" && p.m >= 1020) return false;\n  if (p.wd === \"Sun\" && p.m < 1020) return false;\n  return true;\n}\nfunction bb5eFutOpen(d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  if (p.wd === \"Sat\") return false;\n  if (p.wd === \"Fri\" && p.m >= 1020) return false;\n  if (p.wd === \"Sun\" && p.m < 1080) return false;\n  if (p.m >= 1020 && p.m < 1080) return false;\n  return true;\n}\nfunction bb5eCbotOpen(d) {\n  var p = bb5eParts(\"America/Chicago\", d);\n  var evening = (p.wd === \"Sun\" || p.wd === \"Mon\" || p.wd === \"Tue\" || p.wd === \"Wed\" || p.wd === \"Thu\") && p.m >= 1140;\n  var day = bb5eWeekday(p.wd) && (p.m < 465 || (p.m >= 510 && p.m < 800));\n  return evening || day;\n}\nfunction bb5eSoftOpen(spec, d) {\n  var p = bb5eParts(\"America/New_York\", d);\n  return bb5eWeekday(p.wd) && p.m >= spec.o && p.m < spec.c;\n}\nfunction bb5eLumberOpen(d) {\n  var p = bb5eParts(\"America/Chicago\", d);\n  return bb5eWeekday(p.wd) && p.m >= 540 && p.m < 905;\n}\nfunction bb5eOpenAt(spec, d) {\n  try {\n    if (!spec || spec.mode === \"always\") return true;\n    if (spec.mode === \"fx\") return bb5eFxOpen(d);\n    if (spec.mode === \"fut\") return bb5eFutOpen(d);\n    if (spec.mode === \"cbot\") return bb5eCbotOpen(d);\n    if (spec.mode === \"soft\") return bb5eSoftOpen(spec, d);\n    if (spec.mode === \"lumber\") return bb5eLumberOpen(d);\n    return bb5eWindow(spec, d);\n  } catch (e) { return true; }\n}\nfunction bb5eOffday(spec, d) {\n  try {\n    var tz = spec && (spec.mode === \"fx\" || spec.mode === \"fut\") ? \"America/New_York\" : (spec && spec.tz) || \"America/New_York\";\n    var p = bb5eParts(tz, d);\n    return p.wd === \"Sat\" || p.wd === \"Sun\";\n  } catch (e) { return false; }\n}\nfunction bb5eMs(v) {\n  var n = Number(v);\n  if (!isFinite(n) || n <= 0) return 0;\n  return n < 1e12 ? n * 1000 : n;\n}\nfunction bb5eYahoo(hints, now) {\n  if (!hints || typeof hints !== \"object\") return { known: false, open: false, next: 0 };\n  var state = String(hints.marketState || \"\").toUpperCase();\n  var reg = hints.currentTradingPeriod && hints.currentTradingPeriod.regular;\n  var start = reg ? bb5eMs(reg.start) : 0;\n  var end = reg ? bb5eMs(reg.end) : 0;\n  var shut = state === \"CLOSED\" || state === \"PRE\" || state === \"PREPRE\" || state === \"POST\" || state === \"POSTPOST\";\n  if (state === \"REGULAR\") return { known: true, open: true, next: 0 };\n  if (shut) return { known: true, open: false, next: start > now ? start : 0 };\n  if (start && end && now >= start && now < end) return { known: true, open: true, next: 0 };\n  if (start && end) return { known: true, open: false, next: start > now ? start : 0 };\n  return { known: false, open: false, next: 0 };\n}\nfunction bb5eNext(spec, now, yahooNext, force) {\n  if (yahooNext && yahooNext > now) return yahooNext;\n  var start = now;\n  if (force) {\n    var walk = now;\n    var guard = now + 18 * 3600000;\n    while (walk < guard && bb5eOpenAt(spec, new Date(walk))) walk += 300000;\n    start = walk;\n  }\n  var slot = Math.ceil((start + 1) / 900000) * 900000;\n  for (var k = 0; k < 8 * 96; k++, slot += 900000) {\n    if (bb5eOpenAt(spec, new Date(slot))) return slot;\n  }\n  return 0;\n}\nfunction bb5eLondon(ms, now) {\n  var tz = \"Europe/London\";\n  var d = new Date(ms);\n  var day = function (x) { return new Intl.DateTimeFormat(\"en-CA\", { timeZone: tz }).format(x); };\n  var hm = new Intl.DateTimeFormat(\"en-GB\", { timeZone: tz, hour: \"2-digit\", minute: \"2-digit\", hourCycle: \"h23\" }).format(d);\n  var wd = day(d) === day(new Date(now)) ? \"\" : new Intl.DateTimeFormat(\"en-GB\", { timeZone: tz, weekday: \"short\" }).format(d) + \" \";\n  return wd + hm;\n}\nfunction bb5eLive(q, now) {\n  var delay = Number(q && q.delayMin);\n  if (!isFinite(delay) || delay < 0) delay = 0;\n  delay = Math.round(delay);\n  var ts = Number(q && q.ts);\n  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;\n  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;\n  if (typeof bb5dClass === \"function\") return bb5dClass(age, delay);\n  var note = delay > 0 ? \"delayed \" + delay + \"m by exchange\" : \"\";\n  var cadence = typeof bb5dCadenceMs === \"number\" ? bb5dCadenceMs : 60000;\n  var margin = typeof bb5dMarginMs === \"number\" ? bb5dMarginMs : 120000;\n  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? \"delayed\" : \"fresh\", stale: false, note: note };\n  if (Number(age) > cadence + delay * 60000 + margin) return { delayMin: delay, status: \"stale\", stale: true, note: \"\" };\n  if (delay > 0) return { delayMin: delay, status: \"delayed\", stale: false, note: note };\n  return { delayMin: 0, status: \"fresh\", stale: false, note: \"\" };\n}\nfunction bb5eNote(spec, status, next, now) {\n  var when = next ? bb5eLondon(next, now) : \"\";\n  if (status === \"quiet\") return when ? \"quiet \u00b7 local market opens \" + when + \" UK\" : \"quiet\";\n  var label = (spec && spec.label) || \"Market\";\n  if (!when) return label + \" market closed\";\n  return label + \" market closed \u00b7 opens \" + when + \" UK\";\n}\nfunction bb5eApply(q, symbol, hints, now) {\n  if (!q || typeof q !== \"object\") return q;\n  var out = {};\n  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];\n  var t = now == null ? bb5eNow() : Number(now);\n  if (!isFinite(t)) t = bb5eNow();\n  var spec = typeof bb5gSpec === \"function\" ? bb5gSpec(symbol) : bb5eSpec(symbol);\n  var yahoo = bb5eYahoo(hints, t);\n  var tableOpen = bb5eOpenAt(spec, new Date(t));\n  var open = typeof bb5fOpen === \"function\" ? bb5fOpen(spec, yahoo, tableOpen) : (yahoo.known ? yahoo.open : tableOpen);\n  if (open) {\n    var cls = bb5eLive(out, t);\n    out.delayMin = cls.delayMin;\n    out.status = cls.status;\n    out.stale = cls.stale;\n    if (cls.note) out.note = cls.note;\n    else delete out.note;\n    delete out.nextOpen;\n    return out;\n  }\n  var next = bb5eNext(spec, t, yahoo.next, yahoo.known && !yahoo.open && tableOpen);\n  var status = typeof bb5fStatus === \"function\" ? bb5fStatus(spec, new Date(t)) : (spec.quiet && !bb5eOffday(spec, new Date(t)) ? \"quiet\" : \"closed\");\n  out.status = status;\n  out.stale = false;\n  if (next) out.nextOpen = new Date(next).toISOString();\n  else delete out.nextOpen;\n  out.note = bb5eNote(spec, status, next, t);\n  return out;\n}\n// BB5E_JS_END\n\n// \u2500\u2500 bb5f \u2500\u2500 Thin FX follows the onshore desk. Refills are classified too.\n// BB5F_JS\nvar bb5fAlias = { USDINR: \"INR=X\", USDBRL: \"BRL=X\" };\nfunction bb5fWire(symbol) {\n  var raw = String(symbol || \"\").trim();\n  if (!raw) return null;\n  var key = raw.toUpperCase();\n  var wire = raw;\n  try {\n    if (typeof BB3_ALIAS === \"object\" && BB3_ALIAS && BB3_ALIAS[key]) wire = String(BB3_ALIAS[key]);\n  } catch (e) {}\n  if (wire === raw && bb5fAlias[key]) wire = bb5fAlias[key];\n  var upper = wire.toUpperCase();\n  if (upper === \"USDINR=X\") wire = \"INR=X\";\n  if (upper === \"USDBRL=X\") wire = \"BRL=X\";\n  return { req: raw, wire: wire };\n}\nfunction bb5fOpen(spec, yahoo, tableOpen) {\n  return typeof bb5gOpen === \"function\" ? bb5gOpen(spec, yahoo, tableOpen) : (!!(spec && spec.quiet) ? !!tableOpen : (yahoo && yahoo.known ? !!yahoo.open : !!tableOpen));\n}\nfunction bb5fStatus(spec, d) {\n  if (!spec || !spec.quiet) return \"closed\";\n  try {\n    if (typeof bb5eFxOpen === \"function\" && !bb5eFxOpen(d)) return \"closed\";\n  } catch (e) {\n    try { if (typeof bb5eOffday === \"function\" && bb5eOffday(spec, d)) return \"closed\"; } catch (e2) {}\n  }\n  return \"quiet\";\n}\nfunction bb5fNeedsChart(symbol, q) {\n  var spec = typeof bb5eSpec === \"function\" ? bb5eSpec(symbol) : null;\n  if (!spec || !spec.quiet) return false;\n  var ts = Number(q && q.ts);\n  return !(isFinite(ts) && ts > 0);\n}\nfunction bb5fRefill(q, symbol) {\n  if (!q || typeof q !== \"object\") return q;\n  var out = {};\n  for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k)) out[k] = q[k];\n  out.cached = true;\n  return out;\n}\nfunction bb5fPublish(data, now) {\n  if (!data || typeof data !== \"object\" || Array.isArray(data)) return data;\n  var t = now == null ? Date.now() : Number(now);\n  if (!isFinite(t)) t = Date.now();\n  var out = {};\n  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {\n    var q = data[k];\n    if (!q || typeof q !== \"object\" || typeof bb5eApply !== \"function\" || typeof bb5eSpec !== \"function\") { out[k] = q; continue; }\n    var spec = typeof bb5gSpec === \"function\" ? bb5gSpec(k) : bb5eSpec(k);\n    if (!q.status || q.cached || (spec && spec.quiet)) out[k] = bb5eApply(q, k, null, t);\n    else out[k] = q;\n  }\n  return out;\n}\n// BB5F_JS_END\n\n// \u2500\u2500 bb5g \u2500\u2500 Every quote route is classified. HK lunch and the softs use the desk clock.\n// BB5G_JS\nfunction bb5gSpec(symbol) {\n  var s = typeof bb5eCanon === \"function\" ? bb5eCanon(symbol) : String(symbol || \"\").trim().toUpperCase();\n  if (s === \"HSI\" || s === \"^HSI\") return { mode: \"cash\", tz: \"Asia/Hong_Kong\", o: 570, c: 960, lo: 720, lc: 780, label: \"Hong Kong\" };\n  if (s === \"WTI\" || s === \"BRENT\" || s === \"CL=F\" || s === \"BZ=F\" || s === \"XAU\" || s === \"GC=F\" || s === \"XAU/USD\") return { mode: \"fut\", label: \"US\" };\n  if (s === \"DXY\" || s === \"DX-Y.NYB\") return { mode: \"fx\", label: \"FX\" };\n  if (s === \"BTC/USD\" || s === \"ETH/USD\") return { mode: \"always\", label: \"Crypto\" };\n  var slash = s.indexOf(\"/\") >= 0 ? s.replace(/\\//g, \"\") : \"\";\n  if (slash && typeof bb5eSpec === \"function\") {\n    if (typeof bb5eFx === \"object\" && bb5eFx && bb5eFx[slash]) return bb5eSpec(slash);\n    if (typeof bb5eThin === \"object\" && bb5eThin && bb5eThin[slash]) return bb5eSpec(slash);\n    return { mode: \"fx\", label: \"FX\" };\n  }\n  return typeof bb5eSpec === \"function\" ? bb5eSpec(s) : null;\n}\nfunction bb5gOpen(spec, yahoo, tableOpen) {\n  var scheduled = spec && (spec.quiet || spec.mode === \"cash\" || spec.mode === \"soft\" || spec.mode === \"lumber\" || spec.mode === \"cbot\" || spec.mode === \"thin\");\n  if (scheduled) {\n    if (!tableOpen) return false;\n    if (yahoo && yahoo.known && !yahoo.open) return false;\n    return true;\n  }\n  if (yahoo && yahoo.known) return !!yahoo.open;\n  return !!tableOpen;\n}\nfunction bb5gIsQuote(q) {\n  if (!q || typeof q !== \"object\" || Array.isArray(q)) return false;\n  var p = Number(q.p);\n  return isFinite(p) && p > 0;\n}\nfunction bb5gApply(q, symbol, now, cadence) {\n  if (!bb5gIsQuote(q) || typeof bb5eApply !== \"function\") return q;\n  var wasStale = q.stale === true;\n  var next = bb5eApply(q, symbol, null, now);\n  if (!next || typeof next !== \"object\") return q;\n  if (cadence > 0 && typeof bb5hRetouch === \"function\") return bb5hRetouch(next, now, cadence);\n  if (wasStale && next.status !== \"closed\" && next.status !== \"quiet\") next.stale = true;\n  return next;\n}\nfunction bb5gMap(map, now, cadence) {\n  if (!map || typeof map !== \"object\" || Array.isArray(map)) return map;\n  var out = {};\n  for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k)) out[k] = bb5gApply(map[k], k, now, cadence);\n  return out;\n}\nfunction bb5gPublish(data, now, symbol, route) {\n  if (!data || typeof data !== \"object\") return data;\n  if (Array.isArray(data)) return data;\n  var t = now == null ? Date.now() : Number(now);\n  if (!isFinite(t)) t = Date.now();\n  var cadence = typeof bb5hRouteMs === \"function\" ? bb5hRouteMs(route, data, t) : 0;\n  if (bb5gIsQuote(data)) return bb5gApply(data, symbol || data.symbol || data.name || \"\", t, cadence);\n  var out = {};\n  for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) {\n    if (k === \"quotes\" || k === \"directIndices\") out[k] = bb5gMap(data[k], t, cadence);\n    else out[k] = bb5gApply(data[k], k, t, cadence);\n  }\n  return out;\n}\nfunction bb5gJoinStream(acc, piece, firstModel) {\n  var s = String(piece || \"\");\n  acc = String(acc || \"\");\n  if (firstModel && acc && !/\\n$/.test(acc) && !/^\\n/.test(s)) s = \"\\n\" + s;\n  return { acc: acc + s, piece: s };\n}\n// BB5G_JS_END\n\n// \u2500\u2500 bb5h \u2500\u2500 Stale follows the route cache, not the Yahoo 60s window.\n// BB5H_JS\nfunction bb5hEnergyMs(now) {\n  var t = now == null ? Date.now() : Number(now);\n  if (!isFinite(t)) t = Date.now();\n  var day = new Date(t).toISOString().slice(0, 10);\n  var budget = 300;\n  try {\n    if (typeof process !== \"undefined\" && process.env && process.env.RT43_TD_ENERGY_DAILY != null) budget = Math.max(0, Number(process.env.RT43_TD_ENERGY_DAILY || 300));\n  } catch (e) {}\n  var used = 0;\n  try {\n    if (typeof RT43S_EN === \"object\" && RT43S_EN && RT43S_EN.day === day) used = Number(RT43S_EN.used) || 0;\n  } catch (e2) {}\n  var left = budget - used;\n  var msLeft = Date.parse(day + \"T24:00:00Z\") - t;\n  if (!(left >= 2) || !(msLeft > 0)) return 60000;\n  return Math.max(60000, Math.floor(msLeft / (left / 2)));\n}\nfunction bb5hRouteMs(route, data, now) {\n  // twelve: TWELVE_DATA_CACHE_MS server.js:431, cache_expires_at server.js:4961.\n  // The 30s TWELVE_DATA_REFRESH_LEASE_MS at server.js:449 is the in-flight claim.\n  if (route === \"twelve\") return typeof TWELVE_DATA_CACHE_MS === \"number\" ? TWELVE_DATA_CACHE_MS : 15 * 60 * 1000;\n  // reference: REFERENCE_QUOTE_CACHE_MS server.js:575.\n  if (route === \"reference\") return typeof REFERENCE_QUOTE_CACHE_MS === \"number\" ? REFERENCE_QUOTE_CACHE_MS : 5 * 60 * 1000;\n  // energy: refreshSec is the interval at server.js:7934, echoed at server.js:7947.\n  if (route === \"energy\") {\n    var sec = data && Number(data.refreshSec);\n    if (isFinite(sec) && sec > 0) return Math.round(sec * 1000);\n    return bb5hEnergyMs(now);\n  }\n  // finnhub: no cache TTL. Live fetch at server.js:4339. Window is bb5dCadenceMs server.js:10535.\n  if (route === \"finnhub\") return typeof bb5dCadenceMs === \"number\" ? bb5dCadenceMs : 60000;\n  return 0;\n}\nfunction bb5hHm(ms) {\n  try {\n    return new Intl.DateTimeFormat(\"en-GB\", { timeZone: \"Europe/London\", hour: \"2-digit\", minute: \"2-digit\", hourCycle: \"h23\" }).format(new Date(ms));\n  } catch (e) { return \"\"; }\n}\nfunction bb5hClass(q, now, cadence) {\n  var delay = Number(q && q.delayMin);\n  if (!isFinite(delay) || delay < 0) delay = 0;\n  delay = Math.round(delay);\n  var ts = Number(q && q.ts);\n  var tsMs = ts > 0 && ts < 1e12 ? ts * 1000 : ts;\n  var age = isFinite(tsMs) && tsMs > 0 ? Math.max(0, now - tsMs) : null;\n  var margin = typeof bb5dMarginMs === \"number\" ? bb5dMarginMs : 120000;\n  var fresh = typeof bb5dCadenceMs === \"number\" ? bb5dCadenceMs : 60000;\n  var windowMs = Number(cadence) + delay * 60000 + margin;\n  if (age == null || !isFinite(Number(age))) return { delayMin: delay, status: delay > 0 ? \"delayed\" : \"fresh\", stale: false, note: delay > 0 ? \"delayed \" + delay + \"m by exchange\" : \"\" };\n  if (Number(age) > windowMs) return { delayMin: delay, status: \"stale\", stale: true, note: \"\" };\n  if (Number(age) > fresh) {\n    var hm = bb5hHm(tsMs);\n    return { delayMin: delay, status: \"delayed\", stale: false, note: hm ? \"updated \" + hm + \" UK\" : \"updated UK\" };\n  }\n  if (delay > 0) return { delayMin: delay, status: \"delayed\", stale: false, note: \"delayed \" + delay + \"m by exchange\" };\n  return { delayMin: 0, status: \"fresh\", stale: false, note: \"\" };\n}\nfunction bb5hRetouch(q, now, cadence) {\n  if (!q || typeof q !== \"object\") return q;\n  if (q.status === \"closed\" || q.status === \"quiet\") return q;\n  var cls = bb5hClass(q, now, cadence);\n  q.delayMin = cls.delayMin;\n  q.status = cls.status;\n  q.stale = cls.stale;\n  if (cls.note) q.note = cls.note;\n  else delete q.note;\n  delete q.nextOpen;\n  return q;\n}\n// BB5H_JS_END\n";

const patch = fs.readFileSync(path.join(__dirname, "../deploy/patch_bb5h.py"), "utf8");
const blockStart = patch.indexOf("// BB5H_JS\n");
const blockEnd = patch.indexOf("// BB5H_JS_END");
assert.ok(blockStart > 0 && blockEnd > blockStart);
const block = patch.slice(blockStart, blockEnd);
assert.ok(VENDOR.includes(block), "vendor drifted from patch_bb5h.py");
assert.equal(block.includes("CREATE TABLE"), false);
assert.equal(block.includes("setInterval("), false);
assert.equal(block.includes("stripe.webhooks"), false);

const context = {
  console, Date, Intl, Number, String, isFinite, Object, Array, Math, RegExp, JSON, Error, process
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(VENDOR, context, { filename: "bb5h-vendor.js" });

const TUE = Date.parse("2026-10-20T15:00:00Z"); // 16:00 UK, 11:00 ET
const SAT = Date.parse("2026-10-17T16:00:00Z");
const MARGIN = 120000;

function row(now, ageSec, extra) {
  return Object.assign({ p: 100, c: 0.1, prev: 99, ts: Math.floor(now / 1000) - ageSec }, extra || {});
}
function twelve(symbol, now, ageSec) {
  return context.bb5gPublish({ quotes: { [symbol]: row(now, ageSec) } }, now, null, "twelve").quotes[symbol];
}
function past(route, now, data) {
  const cadence = context.bb5hRouteMs(route, data || null, now);
  return Math.floor((cadence + MARGIN) / 1000) + 2;
}

test("BTC/USD 200s is delayed, not stale", () => {
  const q = twelve("BTC/USD", TUE, 200);
  assert.equal(q.status, "delayed");
  assert.equal(q.stale, false);
  assert.equal(q.note, "updated 15:56 UK");
});

test("ETH/USD 200s is not stale", () => {
  const q = twelve("ETH/USD", TUE, 200);
  assert.equal(q.status, "delayed");
  assert.equal(q.stale, false);
});

test("a Twelve Data tick older than the cache plus 2m is stale", () => {
  const age = past("twelve", TUE);
  assert.ok(age > 200);
  const q = twelve("BTC/USD", TUE, age);
  assert.equal(q.status, "stale");
  assert.equal(q.stale, true);
  assert.equal(context.bb5hRouteMs("twelve"), 15 * 60 * 1000);
});

test("EUR/USD on a weekday with 200s is not stale", () => {
  const q = twelve("EUR/USD", TUE, 200);
  assert.equal(q.status, "delayed");
  assert.equal(q.stale, false);
  assert.match(q.note, /^updated \d{2}:\d{2} UK$/);
});

test("XAU/USD with 200s is not stale", () => {
  const q = twelve("XAU/USD", TUE, 200);
  assert.equal(q.status, "delayed");
  assert.equal(q.stale, false);
});

test("a print younger than 60s stays fresh", () => {
  const q = twelve("BTC/USD", TUE, 30);
  assert.equal(q.status, "fresh");
  assert.equal(q.stale, false);
});

test("crypto on Twelve Data is not closed on a weekend", () => {
  for (const symbol of ["BTC/USD", "ETH/USD"]) {
    const q = twelve(symbol, SAT, 200);
    assert.notEqual(q.status, "closed");
    assert.equal(q.stale, false);
    assert.equal(q.status, "delayed");
  }
});

test("a weekend FX session stays closed", () => {
  const q = twelve("EUR/USD", SAT, 30);
  assert.equal(q.status, "closed");
  assert.equal(q.stale, false);
});

test("thin FX quiet is left alone", () => {
  const q = twelve("USDINR", TUE, 200);
  assert.equal(q.status, "quiet");
  assert.equal(q.stale, false);
});

test("Yahoo's 60s cadence is unchanged", () => {
  const q = context.bb5eApply(row(TUE, 200), "AAPL", null, TUE);
  assert.equal(q.status, "stale");
  assert.equal(q.stale, true);
  const fresh = context.bb5eApply(row(TUE, 30), "AAPL", null, TUE);
  assert.equal(fresh.status, "fresh");
  assert.equal(fresh.stale, false);
});

test("reference quotes use the 5 minute cache", () => {
  assert.equal(context.bb5hRouteMs("reference"), 5 * 60 * 1000);
  const inside = context.bb5gPublish({ XAU: row(TUE, 200) }, TUE, null, "reference");
  assert.equal(inside.XAU.status, "delayed");
  assert.equal(inside.XAU.stale, false);
  const outside = context.bb5gPublish({ XAU: row(TUE, past("reference", TUE)) }, TUE, null, "reference");
  assert.equal(outside.XAU.status, "stale");
  assert.equal(outside.XAU.stale, true);
});

test("spot energy uses its refresh interval", () => {
  const cadence = context.bb5hEnergyMs(TUE);
  assert.ok(cadence > 200000);
  const refreshSec = Math.round(cadence / 1000);
  const inside = context.bb5gPublish({ WTI: row(TUE, 200, { stale: true, source: "twelve-spot" }), refreshSec }, TUE, null, "energy");
  assert.equal(inside.WTI.status, "delayed");
  assert.equal(inside.WTI.stale, false);
  assert.match(inside.WTI.note, /^updated \d{2}:\d{2} UK$/);
  const age = Math.floor((refreshSec * 1000 + MARGIN) / 1000) + 2;
  const outside = context.bb5gPublish({ WTI: row(TUE, age, { source: "twelve-spot" }), refreshSec }, TUE, null, "energy");
  assert.equal(outside.WTI.status, "stale");
  assert.equal(outside.WTI.stale, true);
});

test("finnhub uses the live 60s window", () => {
  assert.equal(context.bb5hRouteMs("finnhub"), 60000);
  const inside = context.bb5gPublish(row(TUE, 90), TUE, "AAPL", "finnhub");
  assert.equal(inside.status, "delayed");
  assert.equal(inside.stale, false);
  assert.equal(inside.note, "updated 15:58 UK");
  const outside = context.bb5gPublish(row(TUE, 200), TUE, "AAPL", "finnhub");
  assert.equal(outside.status, "stale");
  assert.equal(outside.stale, true);
});
