// chat100c unit test: spot snapshot recording across UK days, with a fake clock and fake KV store (no network, no DB).
const fs = require("fs"), vm = require("vm"), path = require("path");
const blk = fs.readFileSync(process.env.BLK || [path.join(__dirname, "server_block_c100b.js"), path.join(__dirname, "../bundle/server_block_c100b.js")].find(f => fs.existsSync(f)), "utf8");
const gold = blk.slice(0, blk.indexOf("// ── About: founder card ──"));
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) pass++; else { fail++; console.log("FAIL " + m, x || ""); } };
let NOW = Date.parse("2026-11-02T09:00:00Z"), spot = { usd: 3900, gbp: 2900, eur: 3480 };
const kv = new Map(); let puts = 0;
const RD = class extends Date { constructor(...a) { a.length ? super(...a) : super(NOW); } static now() { return NOW; } };
const fmt = (ms, o) => new Intl.DateTimeFormat("en-GB", Object.assign({ timeZone: "Europe/London" }, o)).format(new Date(ms));
const ctx = { Date: RD, Intl, Math, Number, String, Object, JSON, Promise, isFinite, console,
  setInterval: () => ({ unref() {} }),
  c97UkIso: (ms) => new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London" }).format(new Date(ms)),
  c97UkHm: (ms) => fmt(ms, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }),
  c97UkWhen: (ms) => fmt(ms, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }) + " UK",
  c97Sg: (v, dp, u) => (v > 0 ? "+" : v < 0 ? "\u2212" : "") + Math.abs(v).toFixed(dp) + u,
  c96StoreOk: () => true, c96Get: async (k) => kv.has(k) ? JSON.parse(kv.get(k)) : null, c96Put: async (k, v) => { puts++; kv.set(k, JSON.stringify(v)); },
  c97GoldDash: async () => ({ rows: { gold_usd: { value: "$" + spot.usd.toLocaleString("en-GB", { minimumFractionDigits: 2 }), source: "gold-api.com spot" }, gold_gbp: { value: "£" + spot.gbp.toFixed(2), source: "gold-api.com spot ÷ pound in dollars" }, gold_eur: { value: "€" + spot.eur.toFixed(2), source: "gold-api.com spot ÷ euro in dollars" } } }) };
const load = () => vm.runInContext(gold + "\n;({ dash: () => c97GoldDash(), chg: () => c100bGoldChange(), st: () => ({ day: c100bDay, prev: c100bPrevDay }) })", vm.createContext(Object.assign({}, ctx)));
(async () => {
  ok(!/yahooQuote|GC=F|futures/i.test(gold.replace(/No futures prices are used\./, "")), "gold section has no Yahoo futures path");
  let A = load(), d = await A.dash();
  ok(d.rows.gold_usd.change === "Change not available yet" && d.rows.gold_gbp.change === "Change not available yet" && d.rows.gold_eur.change === "Change not available yet", "day 1: not available yet");
  ok(kv.size === 1, "day 1: snapshot stored in KV (existing cache table key)", [...kv.keys()]);
  // later the same day: still no change (no previous UK day), reading updated but save throttled
  NOW += 5 * 60e3; spot = { usd: 3910, gbp: 2905, eur: 3485 }; d = await A.dash(); ok(d.rows.gold_usd.change === "Change not available yet", "same day: still not available");
  // last half hour before UK midnight (GMT): every reading saved (>=1 min apart)
  NOW = Date.parse("2026-11-02T23:40:00Z"); spot = { usd: 3920, gbp: 2915, eur: 3495 }; const p0 = puts; await A.dash();
  NOW = Date.parse("2026-11-02T23:58:00Z"); spot = { usd: 3925.5, gbp: 2920.25, eur: 3500.75 }; await A.dash();
  ok(puts - p0 === 2, "late readings all saved", puts - p0);
  ok(JSON.parse(kv.get("c100c:gold-spot-day")).cur.usd === 3925.5, "KV holds last spot before UK midnight");
  // restart after midnight: new process loads snapshot from KV
  NOW = Date.parse("2026-11-03T08:00:00Z"); spot = { usd: 3950, gbp: 2930, eur: 3520 };
  A = load(); d = await A.dash();
  ok(d.rows.gold_usd.change === "+$24.50 (+0.62%)", "day 2 USD: spot now vs last pre-midnight spot", d.rows.gold_usd.change);
  ok(d.rows.gold_gbp.change === "+£9.75 (+0.33%)", "day 2 GBP: pound spot vs pound snapshot", d.rows.gold_gbp.change);
  ok(d.rows.gold_eur.change === "+€19.25 (+0.55%)", "day 2 EUR: euro spot vs euro snapshot", d.rows.gold_eur.change);
  ok(/our spot snapshot \(gold-api\), Mon 2 Nov, 23:58 UK/.test(d.rows.gold_usd.source), "basis names snapshot time", d.rows.gold_usd.source);
  ok(/our pound spot snapshot/.test(d.rows.gold_gbp.source) && /our euro spot snapshot/.test(d.rows.gold_eur.source), "pound/euro bases");
  let c = await A.chg(); ok(c.available && c.usd.prev === 3925.5 && c.gbp.prev === 2920.25, "API prev = snapshot", JSON.stringify(c.usd));
  // during day 2 the comparison stays fixed to day 1's snapshot
  NOW += 3 * 3600e3; spot = { usd: 3940, gbp: 2925, eur: 3510 }; d = await A.dash();
  ok(d.rows.gold_usd.change === "+$14.50 (+0.37%)", "later day 2: still vs day-1 snapshot", d.rows.gold_usd.change);
  // in-process rollover to day 3 (no restart)
  NOW = Date.parse("2026-11-03T23:50:00Z"); spot = { usd: 3930, gbp: 2918, eur: 3505 }; await A.dash();
  NOW = Date.parse("2026-11-04T00:10:00Z"); spot = { usd: 3935, gbp: 2920, eur: 3507 }; d = await A.dash();
  ok(d.rows.gold_usd.change === "+$5.00 (+0.13%)", "day 3: vs day-2 last pre-midnight spot (in process)", d.rows.gold_usd.change);
  // stale snapshot (>4 days): not available
  NOW = Date.parse("2026-11-09T09:00:00Z"); A = load(); kv.clear(); d = await A.dash(); ok(d.rows.gold_usd.change === "Change not available yet", "no KV snapshot after restart -> not available");
  console.log(`\nchat100c unit: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.log("ERR", e); process.exit(1); });
