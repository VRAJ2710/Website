"use strict";
// Writes a static preview of the terminal (fixture figures, real chart drawing) for layout checks.
const fs = require("fs");
const path = require("path");
const outDir = process.argv[2] || "/tmp/c102-preview";
fs.mkdirSync(outDir, { recursive: true });
const client = fs.readFileSync(path.join(__dirname, "client_c102.js"), "utf8");
const css = require("./lib_c102.js").C102_CSS;
const bars = [];
for (let i = 0; i < 80; i++) {
  const d = new Date(Date.UTC(2026, 6, 1 + i));
  const base = 3900 + Math.sin(i / 6) * 40 + i;
  bars.push({ sessionDate: d.toISOString().slice(0, 10), timeUtc: d.toISOString(), o: base - 4, h: base + 8, l: base - 10, c: base + 2, volume: i % 9 === 0 ? null : 12000 + i * 30 });
}
const ma = (n) => ({ status: "ok", sessions: n, points: bars.map((b, i) => i >= n - 1 ? { sessionDate: b.sessionDate, timeUtc: b.timeUtc, value: b.c - 5 } : null).filter(Boolean) });
const chart = {
  status: "ok",
  label: "Gold Dec 26 future · delayed",
  historyKind: "continuous-rolling-proxy",
  historyNote: "Daily bars are Yahoo Finance's continuous rolling front-month series. Not spot gold. Volume is futures volume when the feed returns it.",
  incompleteNote: "The current session is incomplete, so its candle is left out. Last completed session: " + bars[bars.length - 1].sessionDate + ".",
  exchangeTimezone: "America/New_York",
  lastCompleted: { sessionDate: bars[bars.length - 1].sessionDate, timeUtc: bars[bars.length - 1].timeUtc, close: bars[bars.length - 1].c, volume: bars[bars.length - 1].volume },
  bars: bars,
  ma20: ma(20),
  ma50: ma(50)
};
const model = {
  title: "Terminal",
  generatedAtUtc: "2026-11-06T15:30:00.000Z",
  generatedAtUk: "Fri, 6 November 2026, 15:30",
  note: "Gold is priced in dollars and pays no interest, so the dollar, US yields, volatility and futures positioning are the readings usually set beside it. Nothing here is a forecast or a recommendation.",
  spot: { status: "ok", price: 4053.5, unit: "US dollars per troy ounce", asOfUtc: "2026-11-06T15:23:00.000Z", asOfUk: "Fri, 6 November 2026, 15:23", source: "gold-api.com", frequency: "spot quote", lagSeconds: 420 },
  spotChange: { status: "unavailable", message: "The spot feed did not include a daily change. The futures percentage was not used." },
  silver: { status: "ok", price: 52.2, asOfUtc: "2026-11-06T15:23:00.000Z", source: "gold-api.com" },
  ratio: { status: "ok", value: 77.653, formula: "Gold spot (USD per troy ounce) ÷ silver spot (USD per troy ounce)", numerator: { price: 4053.5, asOfUtc: "2026-11-06T15:23:00.000Z" }, denominator: { price: 52.2, asOfUtc: "2026-11-06T15:23:00.000Z" }, source: "gold-api.com" },
  dollar: { status: "ok", price: 102.13, change: 0.58, asOfUtc: "2026-11-06T15:18:00.000Z", asOfUk: "Fri, 6 November 2026, 15:18", source: "ICE US Dollar Index via Yahoo Finance, delayed", frequency: "delayed quote", delayedByMin: 10, lagSeconds: 720 },
  nominal: { status: "ok", price: 4.87, unit: "percent", change: 0.03, asOfUtc: "2026-11-06T15:13:00.000Z", asOfUk: "Fri, 6 November 2026, 15:13", source: "Cboe 10-year Treasury yield index via Yahoo Finance, delayed", frequency: "delayed quote", lagSeconds: 1020 },
  realMarket: { status: "ok", value: 2.63, unit: "percent", change: 0.02, asOfUtc: "2026-11-06T15:22:00.000Z", asOfUk: "Fri, 6 November 2026, 15:22", source: "CNBC market quote, delayed", frequency: "delayed quote" },
  nominalOfficial: { status: "ok", value: 4.9, unit: "percent", change: -0.05, date: "2026-11-04", source: "US Treasury via FRED (DGS10), 10-year constant-maturity yield", frequency: "daily", message: "Official daily print for 2026-11-04. That is the observation date, not the time of the delayed market quote." },
  realOfficial: { status: "ok", value: 2.64, unit: "percent", change: 0, date: "2026-11-04", source: "US Treasury via FRED (DFII10), 10-year inflation-protected yield", frequency: "daily", message: "Official daily print for 2026-11-04." },
  vix: { status: "ok", price: 24.53, change: 0, asOfUtc: "2026-11-06T15:20:00.000Z", asOfUk: "Fri, 6 November 2026, 15:20", source: "Cboe Volatility Index via Yahoo Finance, delayed", frequency: "delayed quote", delayedByMin: 15 },
  positioning: { status: "ok", net: 105562, long: 122508, short: 16946, openInterest: 396810, weekChange: 1356, reportDate: "2026-10-27", lagDays: 10, market: "GOLD - COMMODITY EXCHANGE INC.", source: "CFTC Commitments of Traders, disaggregated futures only, COMEX gold", frequency: "weekly" },
  events: { status: "ok", message: "Scheduled releases only. Consensus forecasts are not shown.", items: [{ name: "US jobs report", when: "Fri 6 Nov, 13:30 UK", agency: "BLS", source: "US Bureau of Labor Statistics" }, { name: "UK consumer prices", when: "Wed 18 Nov, 07:00 UK", agency: "ONS", source: "Office for National Statistics" }] }
};
const theme = ":root{--paper:#fbfaf7;--ink:#1b1b1b;--muted:#5f6368;--rule:#dedad2;--accent:#1f3a5f;--down:#a23b2a;--up:#2f6b47;--amber:#8a6a12;--serif:Georgia,serif;--sans:Inter,system-ui,sans-serif}html.c97-dark{--paper:#151b23;--ink:#e7eaee;--muted:#aab3bf;--rule:#334050;--accent:#9cc0ea;--down:#f2998a;--up:#86d1a1;--amber:#e6c372}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 var(--sans)}header{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--rule)}header a{color:var(--ink)}main{max-width:1120px;margin:0 auto;padding:16px}h1{font:600 40px/1.15 var(--serif);margin:8px 0}";
function page(dark) {
  return "<!doctype html><html lang=\"en-GB\" class=\"" + (dark ? "c97-dark" : "") + "\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Terminal | The Dispatch Market</title><style>" + theme + "</style>" + css + "</head><body><header><a href=\"/\">The Dispatch Market</a><a href=\"/gold/\">Gold</a><a href=\"/terminal/\" aria-current=\"page\">Terminal</a><a href=\"/dashboard/\">Dashboard</a></header><main><h1>Terminal</h1><div id=\"mount\"></div></main><script>" + client + "</script><script>c102ui.mount(document.getElementById(\"mount\"),{model:" + JSON.stringify(model) + ",chart:" + JSON.stringify(chart) + "});window.addEventListener(\"load\",function(){var d=document.documentElement;var c=document.getElementById(\"c102\");document.body.dataset.overflow=String(d.scrollWidth>d.clientWidth+1);document.body.dataset.sw=String(d.scrollWidth);document.body.dataset.cw=String(d.clientWidth);if(c){document.body.dataset.c102=String(c.scrollWidth>c.clientWidth+1);document.body.dataset.csw=String(c.scrollWidth);document.body.dataset.ccw=String(c.clientWidth);}});</script></body></html>";
}
fs.writeFileSync(path.join(outDir, "light.html"), page(false));
fs.writeFileSync(path.join(outDir, "dark.html"), page(true));
console.log(outDir);
