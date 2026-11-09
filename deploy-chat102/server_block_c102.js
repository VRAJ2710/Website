// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.
(function () {
  var module = { exports: {} };
"use strict";
// chat102 pure terminal logic. No I/O except c102Collect, which receives fetch.
// Appended onto the live chat101h server by deploy.sh. Do not fetch a client-supplied symbol.

const C102_GOLD_URL = "https://api.gold-api.com/price/XAU";
const C102_SILVER_URL = "https://api.gold-api.com/price/XAG";
const C102_YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/";
const C102_FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=";
const C102_COT = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json";
const C102_FUTURE = "GC=F";
const C102_UA = "The Dispatch Market research (https://thedispatch.uk)";

function c102Esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]));
}

function c102Uk(iso) {
  const ms = Date.parse(iso);
  if (!isFinite(ms)) return null;
  try {
    return new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/London",
      weekday: "short",
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23"
    }).format(new Date(ms));
  } catch (e) {
    return null;
  }
}

function c102Ymd(ms, tz) {
  try {
    return new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms));
  } catch (e) {
    return "";
  }
}

function c102Lag(iso, now) {
  const ms = Date.parse(iso);
  if (!isFinite(ms)) return null;
  return Math.max(0, Math.round((now - ms) / 1000));
}

function c102LagText(sec) {
  if (sec == null) return "";
  if (sec < 90) return sec + " seconds";
  const m = Math.round(sec / 60);
  if (m < 90) return m + " minutes";
  const h = Math.round(m / 60);
  if (h < 48) return h + " hours";
  return Math.round(h / 24) + " days";
}

function c102Num(n, d) {
  if (typeof n !== "number" || !isFinite(n)) return null;
  return n.toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
}

function c102Chg(n, d, suffix) {
  if (typeof n !== "number" || !isFinite(n)) return null;
  if (n === 0) return "0" + (d ? "." + "0".repeat(d) : "") + (suffix || "");
  const sign = n > 0 ? "+" : "\u2212";
  return sign + Math.abs(n).toFixed(d) + (suffix || "");
}

function c102Fail(kind, message) {
  return { status: kind || "unavailable", message: message || "This reading is unavailable. No number was filled in." };
}

function c102Stamp(row, now, staleAfter) {
  if (!row || !row.asOfUtc) return row;
  row.asOfUk = c102Uk(row.asOfUtc);
  row.lagSeconds = c102Lag(row.asOfUtc, now);
  if (row.status === "ok" && row.lagSeconds != null && staleAfter != null && row.lagSeconds > staleAfter) {
    row.status = "stale";
    row.message = "Last reading " + (row.asOfUk || row.asOfUtc) + ", " + c102LagText(row.lagSeconds) + " ago. It is not a live price.";
  }
  return row;
}

function c102ParseMetal(body, expectSymbol) {
  let j = body;
  if (typeof body === "string") {
    try { j = JSON.parse(body); } catch (e) { return c102Fail("malformed", "The spot feed returned text that was not a price."); }
  }
  if (!j || typeof j !== "object") return c102Fail("malformed", "The spot feed returned no price.");
  if (j.symbol !== expectSymbol || j.currency !== "USD" || typeof j.price !== "number" || !isFinite(j.price) || !(j.price > 0)) {
    return c102Fail("malformed", "The spot feed did not return a US dollar price for this metal.");
  }
  const ms = Date.parse(j.updatedAt);
  if (!isFinite(ms)) return c102Fail("malformed", "The spot feed returned a price without a time.");
  return {
    status: "ok",
    name: expectSymbol === "XAU" ? "Gold spot" : "Silver spot",
    price: j.price,
    currency: "USD",
    unit: "US dollars per troy ounce",
    asOfUtc: new Date(ms).toISOString(),
    source: "gold-api.com",
    sourceUrl: "https://api.gold-api.com/price/" + expectSymbol,
    frequency: "spot quote"
  };
}

function c102Ratio(gold, silver) {
  if (!gold || gold.status !== "ok" || !silver || silver.status !== "ok") {
    return c102Fail("unavailable", "The gold/silver ratio needs both spot prices from gold-api.com. It was not estimated.");
  }
  const gap = Math.abs(Date.parse(gold.asOfUtc) - Date.parse(silver.asOfUtc));
  if (!isFinite(gap)) return c102Fail("malformed", "The spot times could not be compared, so the ratio is not shown.");
  const base = {
    numerator: { name: "Gold spot", price: gold.price, unit: "USD per troy ounce", asOfUtc: gold.asOfUtc },
    denominator: { name: "Silver spot", price: silver.price, unit: "USD per troy ounce", asOfUtc: silver.asOfUtc },
    formula: "Gold spot (USD per troy ounce) \u00f7 silver spot (USD per troy ounce)",
    source: "gold-api.com",
    value: Math.round((gold.price / silver.price) * 1000) / 1000,
    asOfUtc: gold.asOfUtc
  };
  if (gap === 0) return Object.assign({ status: "ok" }, base);
  if (gap <= 180000) {
    return Object.assign({ status: "partial", message: "The gold and silver prints are " + Math.round(gap / 1000) + " seconds apart, so this is not one timestamp." }, base);
  }
  return {
    status: "unavailable",
    message: "Gold and silver timestamps differ by " + c102LagText(Math.round(gap / 1000)) + ", so the ratio is not shown.",
    goldAsOfUtc: gold.asOfUtc,
    silverAsOfUtc: silver.asOfUtc,
    source: "gold-api.com"
  };
}

function c102YahooQuote(payload, expect) {
  const result = payload && payload.chart && Array.isArray(payload.chart.result) ? payload.chart.result[0] : null;
  const meta = result && result.meta;
  if (!meta || meta.symbol !== expect.symbol) return c102Fail("malformed", "The quote feed did not return the series that was requested.");
  const name = String(meta.longName || meta.shortName || "");
  if (expect.rejectName && expect.rejectName.test(name + " " + meta.symbol)) return c102Fail("malformed", "The series was not the index this panel shows.");
  if (expect.nameTest && !expect.nameTest.test(name)) return c102Fail("malformed", "The series name was not the one this panel shows.");
  if (expect.instrument && meta.instrumentType && meta.instrumentType !== expect.instrument) return c102Fail("malformed", "The instrument type was not the one this panel shows.");
  const price = meta.regularMarketPrice;
  if (typeof price !== "number" || !isFinite(price)) return c102Fail("unavailable", "The quote feed returned no price.");
  if (expect.range && (price < expect.range[0] || price > expect.range[1])) return c102Fail("malformed", "The price was outside the range this panel can describe.");
  const prevRaw = typeof meta.previousClose === "number" ? meta.previousClose : (typeof meta.chartPreviousClose === "number" ? meta.chartPreviousClose : null);
  const prev = prevRaw != null && isFinite(prevRaw) ? prevRaw : null;
  const change = prev == null ? null : Math.round((price - prev) * 1e6) / 1e6;
  const sec = meta.regularMarketTime;
  if (typeof sec !== "number" || !isFinite(sec)) return c102Fail("malformed", "The quote had no exchange time, so it is not shown.");
  const exchange = String(meta.fullExchangeName || "");
  const ice = expect.wantIce ? (/ICE/i.test(exchange) || meta.exchangeName === "NYB") : false;
  if (expect.wantIce && !ice) return c102Fail("malformed", "The dollar quote was not identified as the ICE index, so it is not labelled as ICE.");
  return {
    status: change == null ? "partial" : "ok",
    message: change == null ? "The quote included a price and a time, and no previous close. No change was filled in." : "",
    name: expect.label,
    vendorName: name,
    price: price,
    previousClose: prev,
    change: change,
    asOfUtc: new Date(sec * 1000).toISOString(),
    exchange: exchange || meta.exchangeName || "",
    timezone: meta.exchangeTimezoneName || "",
    currency: meta.currency || "",
    instrumentType: meta.instrumentType || "",
    delayedByMin: typeof meta.exchangeDataDelayedBy === "number" ? meta.exchangeDataDelayedBy : null,
    source: expect.source,
    sourceUrl: expect.sourceUrl,
    frequency: "delayed quote",
    unit: expect.unit || null,
    ice: ice
  };
}

function c102FredCsv(csv, series) {
  const lines = String(csv || "").trim().split(/\r?\n/).slice(1);
  const rows = [];
  for (const line of lines) {
    const bits = line.split(",");
    const d = bits[0];
    const v = bits[1];
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d || "")) continue;
    if (v == null || v === "." || v === "" || !isFinite(Number(v))) continue;
    rows.push({ date: d, value: Number(v) });
  }
  if (!rows.length) return c102Fail("unavailable", "The official daily series did not include a number.");
  const last = rows[rows.length - 1];
  const prev = rows.length > 1 ? rows[rows.length - 2] : null;
  const change = prev ? Math.round((last.value - prev.value) * 1000) / 1000 : null;
  const which = series === "DFII10" ? "10-year inflation-protected yield" : "10-year constant-maturity yield";
  return {
    status: "ok",
    series: series,
    name: series === "DFII10" ? "US 10-year real yield, official daily" : "US 10-year yield, official daily",
    value: last.value,
    unit: "percent",
    date: last.date,
    previousDate: prev ? prev.date : null,
    previousValue: prev ? prev.value : null,
    change: change,
    frequency: "daily",
    source: "US Treasury via FRED (" + series + "), " + which,
    sourceUrl: "https://fred.stlouisfed.org/series/" + series,
    message: "Official daily print for " + last.date + ". That is the observation date, not the time of the delayed market quote."
  };
}

function c102FredRows(rows, series) {
  if (!Array.isArray(rows) || !rows.length) return c102Fail("unavailable", "The official daily series did not include a number.");
  const clean = rows.filter((r) => Array.isArray(r) && /^\d{4}-\d{2}-\d{2}$/.test(r[0]) && typeof r[1] === "number" && isFinite(r[1]));
  if (!clean.length) return c102Fail("malformed", "The official daily series could not be read.");
  const lines = "DATE,VALUE\n" + clean.map((r) => r[0] + "," + r[1]).join("\n");
  return c102FredCsv(lines, series);
}

function c102Cot(rows) {
  if (!Array.isArray(rows)) return c102Fail("malformed", "The positioning feed did not return a list.");
  const ok = rows.filter((r) => {
    if (!r || typeof r !== "object") return false;
    const name = String(r.commodity_name || "");
    const market = String(r.market_and_exchange_names || "");
    const code = String(r.cftc_contract_market_code || "");
    if (code !== "088691" || name !== "GOLD") return false;
    if (/MICRO/i.test(name) || /MICRO/i.test(market)) return false;
    if (market !== "GOLD - COMMODITY EXCHANGE INC.") return false;
    return /^\d{4}-\d{2}-\d{2}/.test(String(r.report_date_as_yyyy_mm_dd || ""));
  });
  if (!rows.length) return c102Fail("unavailable", "The weekly positioning report did not include a row.");
  if (!ok.length) return c102Fail("malformed", "The positioning rows were not COMEX gold. Micro gold was not used.");
  ok.sort((a, b) => String(a.report_date_as_yyyy_mm_dd) < String(b.report_date_as_yyyy_mm_dd) ? 1 : -1);
  const latest = ok[0];
  const long = Number(latest.m_money_positions_long_all);
  const short = Number(latest.m_money_positions_short_all);
  const oi = Number(latest.open_interest_all);
  if (!isFinite(long) || !isFinite(short)) return c102Fail("malformed", "The positioning row had no contract counts.");
  const net = long - short;
  let weekChange = null;
  if (ok[1]) {
    const pn = Number(ok[1].m_money_positions_long_all) - Number(ok[1].m_money_positions_short_all);
    if (isFinite(pn)) weekChange = net - pn;
  }
  const reportDate = String(latest.report_date_as_yyyy_mm_dd).slice(0, 10);
  return {
    status: "ok",
    frequency: "weekly",
    reportDate: reportDate,
    asOfUtc: reportDate + "T00:00:00.000Z",
    commodity: "GOLD",
    market: "GOLD - COMMODITY EXCHANGE INC.",
    long: long,
    short: short,
    net: net,
    openInterest: isFinite(oi) ? oi : null,
    weekChange: weekChange,
    source: "CFTC Commitments of Traders, disaggregated futures only, COMEX gold",
    sourceUrl: "https://publicreporting.cftc.gov/",
    message: "Money managers' gold futures on COMEX. Weekly, as of the report date. This is not a view on where the price will go."
  };
}

function c102Sma(bars, n) {
  if (!Array.isArray(bars) || bars.length < n) return null;
  const points = [];
  let sum = 0;
  for (let i = 0; i < bars.length; i++) {
    sum += bars[i].c;
    if (i >= n) sum -= bars[i - n].c;
    if (i >= n - 1) points.push({ sessionDate: bars[i].sessionDate, timeUtc: bars[i].timeUtc, value: Math.round((sum / n) * 100) / 100 });
  }
  return { status: "ok", sessions: n, points: points };
}

function c102Chart(payload, nowMs) {
  const result = payload && payload.chart && Array.isArray(payload.chart.result) ? payload.chart.result[0] : null;
  const meta = result && result.meta;
  if (!meta || meta.symbol !== C102_FUTURE) return c102Fail("unavailable", "The futures chart feed did not return COMEX gold.");
  if (meta.instrumentType && meta.instrumentType !== "FUTURE") return c102Fail("malformed", "The chart series was not a future.");
  const tz = meta.exchangeTimezoneName || "America/New_York";
  const quote = (result.indicators && result.indicators.quote && result.indicators.quote[0]) || {};
  const ts = Array.isArray(result.timestamp) ? result.timestamp : [];
  const raw = [];
  for (let i = 0; i < ts.length; i++) {
    const o = quote.open && quote.open[i];
    const h = quote.high && quote.high[i];
    const l = quote.low && quote.low[i];
    const c = quote.close && quote.close[i];
    const vol = quote.volume && quote.volume[i];
    if (![o, h, l, c].every((x) => typeof x === "number" && isFinite(x))) continue;
    if (typeof ts[i] !== "number" || !isFinite(ts[i])) continue;
    let volume = null;
    if (typeof vol === "number" && isFinite(vol) && vol > 0) volume = vol;
    raw.push({
      timeUtc: new Date(ts[i] * 1000).toISOString(),
      sessionDate: c102Ymd(ts[i] * 1000, tz),
      o: o, h: h, l: l, c: c, volume: volume
    });
  }
  const today = c102Ymd(nowMs, tz);
  const completed = [];
  let excluded = 0;
  for (const bar of raw) {
    if (!bar.sessionDate || bar.sessionDate >= today) { excluded++; continue; }
    completed.push(bar);
  }
  let volumeRepeatsCleared = 0;
  for (let i = 0; i < completed.length - 1; i++) {
    const a = completed[i];
    const b = completed[i + 1];
    if (a.volume != null && b.volume != null && a.volume === b.volume && (a.c !== b.c || a.o !== b.o || a.h !== b.h || a.l !== b.l)) {
      a.volume = null;
      volumeRepeatsCleared++;
    }
  }
  const vendorName = String(meta.shortName || meta.longName || "").trim();
  const label = vendorName ? vendorName + " future \u00b7 delayed" : "COMEX front-month gold future \u00b7 delayed";
  const last = completed.length ? completed[completed.length - 1] : null;
  const ma20 = c102Sma(completed, 20) || { status: "unavailable", message: "The 20-session average needs 20 completed sessions. This response has " + completed.length + "." };
  const ma50 = c102Sma(completed, 50) || { status: "unavailable", message: "The 50-session average needs 50 completed sessions. This response has " + completed.length + "." };
  if (!completed.length) {
    return c102Fail("unavailable", "No completed session was in the futures chart. The current session was left out.");
  }
  return {
    status: "ok",
    label: label,
    vendorName: vendorName || null,
    exchange: meta.fullExchangeName || "COMEX",
    exchangeTimezone: tz,
    currency: meta.currency || "USD",
    historyKind: "continuous-rolling-proxy",
    historyNote: "Daily bars are Yahoo Finance's continuous rolling front-month series. The vendor name is the name on this response. The bars are not that named month's own history, they are not back-adjusted here, and they are not spot gold. Volume, where the feed returned a figure that was not repeated on the next session, is futures volume, not spot volume.",
    barTimeNote: "Each daily bar is timestamped at midnight in America/New_York. In UTC that is 04:00 during US daylight time and 05:00 during US standard time. That clock is the bar timestamp, not a settlement time.",
    volumeRepeatsCleared: volumeRepeatsCleared,
    volumeRepeatNote: volumeRepeatsCleared ? "The feed repeated one futures volume on the next session. The earlier copy is left blank." : "",
    excludedIncompleteSessions: excluded,
    incompleteNote: excluded
      ? "The current session (" + today + ", " + tz + ") is incomplete, so its candle is left out of the chart and the averages. Last completed session: " + last.sessionDate + "."
      : "No current-session bar was in this response. Last completed session: " + last.sessionDate + " (" + tz + ").",
    lastCompleted: { sessionDate: last.sessionDate, timeUtc: last.timeUtc, open: last.o, high: last.h, low: last.l, close: last.c, volume: last.volume },
    sessionDates: completed.map((b) => b.sessionDate),
    bars: completed,
    ma20: ma20,
    ma50: ma50,
    delayedByMin: typeof meta.exchangeDataDelayedBy === "number" ? meta.exchangeDataDelayedBy : null,
    source: "Yahoo Finance, delayed",
    sourceUrl: "https://finance.yahoo.com/",
    frequency: "daily bars"
  };
}

function c102SnapshotChange(dash) {
  const row = dash && dash.rows && dash.rows.gold_usd;
  if (!row) return c102Fail("unavailable", "No spot previous close was published. The futures move was not used.");
  const src = String(row.source || "");
  if (/futures|GC=F|GC%3DF/i.test(src)) return c102Fail("unavailable", "A futures move was not used as the spot change.");
  if (!/gold-api/i.test(src)) return c102Fail("unavailable", "The spot change did not come from the gold spot snapshot.");
  if (row.changePct == null || !isFinite(Number(row.changePct))) {
    return c102Fail("unavailable", "The spot snapshot did not include a daily change. Nothing was filled in.");
  }
  return {
    status: "ok",
    changePct: Number(row.changePct),
    text: row.change || null,
    basis: row.changeBasis || row.changeNote || "since the desk's previous spot snapshot",
    source: src,
    asOfText: row.asOf || null,
    frequency: "change since the previous spot snapshot"
  };
}

function c102Events(cal) {
  const rows = cal && (Array.isArray(cal.rows) ? cal.rows : (cal.v && Array.isArray(cal.v.rows) ? cal.v.rows : null));
  if (!rows) return c102Fail("unavailable", "The release calendar did not answer. No dates were filled in.");
  const items = [];
  for (const r of rows) {
    if (!r || r.past) continue;
    const blob = [r.agency, r.name, r.title, r.source, r.venue].join(" ");
    if (!/ONS|Office for National Statistics|\bBLS\b|Bureau of Labor|\bBEA\b|Economic Analysis|FOMC|Federal Reserve|Bank of England|\bBoE\b|\bMPC\b/i.test(blob)) continue;
    items.push({
      when: r.when || null,
      day: r.dayIso || null,
      name: r.name || r.title || null,
      agency: r.agency || null,
      source: r.source || null,
      sourceUrl: r.sourceUrl || null,
      timeUtc: typeof r.ms === "number" ? new Date(r.ms).toISOString() : null
    });
    if (items.length >= 8) break;
  }
  return {
    status: items.length ? "ok" : "partial",
    items: items,
    frequency: "release schedule",
    message: items.length ? "Scheduled releases only. Consensus forecasts are not shown." : "No upcoming release from these agencies was in the calendar.",
    consensus: "not shown"
  };
}

function c102Cnbc(rates) {
  if (!rates || (!rates.ten && !rates.tips)) return { nominal: c102Fail("unavailable", "The delayed yield quote did not answer."), real: c102Fail("unavailable", "The delayed real-yield quote did not answer.") };
  const one = (q, name) => {
    if (!q || typeof q.value !== "number" || !isFinite(q.value)) return c102Fail("unavailable", name + " did not include a number.");
    const ms = typeof q.asOfMs === "number" ? q.asOfMs : Date.parse(q.asOfUtc || "");
    if (!isFinite(ms)) return c102Fail("malformed", name + " had no time, so it is not shown.");
    return {
      status: q.change == null ? "partial" : "ok",
      name: name,
      value: q.value,
      unit: "percent",
      change: typeof q.change === "number" && isFinite(q.change) ? q.change : null,
      asOfUtc: new Date(ms).toISOString(),
      source: q.src || "CNBC market quote",
      sourceUrl: q.url || null,
      frequency: "delayed quote",
      message: q.change == null ? "No previous close was attached. No change was filled in." : ""
    };
  };
  return { nominal: one(rates.ten, "US 10-year yield, delayed market quote"), real: one(rates.tips, "US 10-year real yield, delayed market quote") };
}

function c102Classify(err) {
  const msg = String(err && err.message || err || "");
  const name = err && err.name;
  if (name === "AbortError" || /timeout|aborted/i.test(msg)) return c102Fail("timeout", "This source did not answer in time. No number was filled in.");
  if (/malformed|json|unexpected/i.test(msg)) return c102Fail("malformed", "This source returned something we could not use. No number was filled in.");
  return c102Fail("unavailable", "This source did not answer. No number was filled in.");
}

function c102Assemble(parts, nowMs) {
  const now = nowMs || Date.now();
  const gold = parts.gold && parts.gold.status ? parts.gold : c102Fail("unavailable", "Gold spot did not answer.");
  const silver = parts.silver && parts.silver.status ? parts.silver : c102Fail("unavailable", "Silver spot did not answer.");
  if (gold.asOfUtc) c102Stamp(gold, now, 4 * 86400);
  if (silver.asOfUtc) c102Stamp(silver, now, 4 * 86400);
  const ratio = c102Ratio(gold.status === "ok" || gold.status === "stale" ? gold : null, silver.status === "ok" || silver.status === "stale" ? silver : null);
  if (ratio.asOfUtc && ratio.status === "ok") c102Stamp(ratio, now, 4 * 86400);
  const dollar = parts.dollar && parts.dollar.status ? parts.dollar : c102Fail("unavailable", "The dollar index did not answer.");
  if (dollar.asOfUtc) c102Stamp(dollar, now, 4 * 86400);
  const vix = parts.vix && parts.vix.status ? parts.vix : c102Fail("unavailable", "The volatility index did not answer.");
  if (vix.asOfUtc) c102Stamp(vix, now, 4 * 86400);
  const nominal = parts.nominal && parts.nominal.status ? parts.nominal : c102Fail("unavailable", "The delayed 10-year yield did not answer.");
  if (nominal.asOfUtc) c102Stamp(nominal, now, 4 * 86400);
  const realMarket = parts.realMarket && parts.realMarket.status ? parts.realMarket : c102Fail("unavailable", "The delayed real yield did not answer.");
  if (realMarket.asOfUtc && realMarket.status !== "unavailable" && realMarket.status !== "timeout" && realMarket.status !== "malformed") c102Stamp(realMarket, now, 4 * 86400);
  const dgs = parts.dgs10 && parts.dgs10.status ? parts.dgs10 : c102Fail("unavailable", "The official daily 10-year yield did not answer.");
  const dfii = parts.dfii10 && parts.dfii10.status ? parts.dfii10 : c102Fail("unavailable", "The official daily real yield did not answer.");
  const positioning = parts.positioning && parts.positioning.status ? parts.positioning : c102Fail("unavailable", "The weekly positioning report did not answer.");
  if (positioning.reportDate) {
    const ageDays = (Date.parse(c102Ymd(now, "America/New_York") + "T00:00:00Z") - Date.parse(positioning.reportDate + "T00:00:00Z")) / 86400000;
    positioning.lagDays = isFinite(ageDays) ? Math.round(ageDays) : null;
    if (positioning.status === "ok" && positioning.lagDays != null && positioning.lagDays > 21) {
      positioning.status = "stale";
      positioning.message = "Weekly report dated " + positioning.reportDate + " (" + positioning.lagDays + " days ago). It is not a newer report.";
    }
  }
  const events = parts.events && parts.events.status ? parts.events : c102Fail("unavailable", "The release calendar did not answer. No dates were filled in.");
  const spotChange = parts.spotChange && parts.spotChange.status ? parts.spotChange : c102Fail("unavailable", "The spot feed did not include a daily change. The futures percentage was not used.");
  return {
    ok: true,
    title: "Terminal",
    generatedAtUtc: new Date(now).toISOString(),
    generatedAtUk: c102Uk(new Date(now).toISOString()),
    spot: gold,
    silver: silver,
    ratio: ratio,
    dollar: dollar,
    vix: vix,
    nominal: nominal,
    realMarket: realMarket,
    nominalOfficial: dgs,
    realOfficial: dfii,
    spotChange: spotChange,
    positioning: positioning,
    events: events,
    note: "Gold is priced in dollars and pays no interest, so the dollar, US yields, volatility and futures positioning are the readings usually set beside it. They use different clocks. Nothing here is a forecast or a recommendation."
  };
}

function c102Deadline(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("timeout")), ms);
    Promise.resolve(promise).then((v) => { clearTimeout(t); resolve(v); }, (e) => { clearTimeout(t); reject(e); });
  });
}

async function c102Get(deps, url, accept, ms) {
  const fetch = deps.fetch;
  const limit = ms || 2000;
  const ctrl = typeof AbortController === "function" ? new AbortController() : null;
  const timer = setTimeout(() => { try { if (ctrl) ctrl.abort(); } catch (e) {} }, limit);
  try {
    const res = await c102Deadline(fetch(url, {
      headers: { "User-Agent": (deps && deps.ua) || C102_UA, Accept: accept || "application/json" },
      redirect: "follow",
      signal: ctrl ? ctrl.signal : undefined
    }), limit);
    if (!res || !res.ok) throw new Error("http " + (res && res.status));
    return res;
  } catch (e) {
    if (e && (e.name === "AbortError" || /aborted/i.test(String(e.message || "")))) throw new Error("timeout");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

async function c102Collect(deps, nowMs) {
  const ms = (deps && deps.timeoutMs) || 2000;
  const job = (fn) => fn().then((v) => ({ ok: true, v: v })).catch((e) => ({ ok: false, err: c102Classify(e) }));
  const limit = (p) => c102Deadline(Promise.resolve().then(() => p), ms);
  const yahoo = (symbol, range, interval) => c102Get(deps, C102_YAHOO + encodeURIComponent(symbol) + "?range=" + range + "&interval=" + interval, "application/json", ms).then((r) => r.json());
  const tasks = {
    gold: job(() => c102Get(deps, C102_GOLD_URL, "application/json", ms).then((r) => r.json()).then((j) => c102ParseMetal(j, "XAU"))),
    silver: job(() => c102Get(deps, C102_SILVER_URL, "application/json", ms).then((r) => r.json()).then((j) => c102ParseMetal(j, "XAG"))),
    dollar: job(() => yahoo("DX-Y.NYB", "5d", "1d").then((j) => c102YahooQuote(j, {
      symbol: "DX-Y.NYB", instrument: "INDEX", nameTest: /dollar index/i, rejectName: /synthetic|basket|VXX/i, wantIce: true, range: [40, 200],
      label: "US dollar index", source: "ICE US Dollar Index via Yahoo Finance, delayed", sourceUrl: "https://finance.yahoo.com/"
    }))),
    vix: job(() => yahoo("^VIX", "5d", "1d").then((j) => c102YahooQuote(j, {
      symbol: "^VIX", instrument: "INDEX", nameTest: /volatility index/i, rejectName: /VXX/i, range: [1, 150],
      label: "Cboe volatility index", source: "Cboe Volatility Index via Yahoo Finance, delayed", sourceUrl: "https://finance.yahoo.com/"
    }))),
    nominal: job(() => yahoo("^TNX", "5d", "1d").then((j) => c102YahooQuote(j, {
      symbol: "^TNX", instrument: "INDEX", nameTest: /treasury|yield|10[- ]year|tnx/i, rejectName: /VXX/i, range: [0, 25], unit: "percent",
      label: "US 10-year Treasury yield", source: "Cboe 10-year Treasury yield index via Yahoo Finance, delayed", sourceUrl: "https://finance.yahoo.com/"
    }))),
    dgs10: job(async () => {
      if (deps.fred) return limit(deps.fred("DGS10"));
      const res = await c102Get(deps, C102_FRED + "DGS10", "text/csv,*/*", ms);
      return c102FredCsv(await res.text(), "DGS10");
    }),
    dfii10: job(async () => {
      if (deps.fred) return limit(deps.fred("DFII10"));
      const res = await c102Get(deps, C102_FRED + "DFII10", "text/csv,*/*", ms);
      return c102FredCsv(await res.text(), "DFII10");
    }),
    positioning: job(async () => {
      const where = "cftc_contract_market_code='088691' AND commodity_name='GOLD' AND market_and_exchange_names='GOLD - COMMODITY EXCHANGE INC.'";
      const q = C102_COT + "?" + new URLSearchParams({
        "$select": "report_date_as_yyyy_mm_dd,commodity_name,cftc_contract_market_code,market_and_exchange_names,m_money_positions_long_all,m_money_positions_short_all,open_interest_all",
        "$where": where,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": "2"
      }).toString();
      const res = await c102Get(deps, q, "application/json", ms);
      return c102Cot(await res.json());
    }),
    events: job(async () => {
      if (!deps.calendar) return c102Fail("unavailable", "The release calendar is not configured on this server. No dates were filled in.");
      return c102Events(await limit(deps.calendar()));
    }),
    spotChange: job(async () => {
      if (!deps.goldDash) return c102Fail("unavailable", "The spot snapshot change is not configured. The futures percentage was not used.");
      return c102SnapshotChange(await limit(deps.goldDash()));
    }),
    cnbc: job(async () => {
      if (!deps.cnbc) return null;
      return c102Cnbc(await limit(deps.cnbc()));
    })
  };
  const keys = Object.keys(tasks);
  const settled = await Promise.all(keys.map((k) => tasks[k]));
  const got = {};
  keys.forEach((k, i) => {
    const row = settled[i];
    got[k] = row.ok ? row.v : row.err;
  });
  if (got.nominal && (got.nominal.status === "unavailable" || got.nominal.status === "timeout" || got.nominal.status === "malformed") && got.cnbc && got.cnbc.nominal && got.cnbc.nominal.status === "ok") {
    got.nominal = got.cnbc.nominal;
    got.nominal.usedFallback = "delayed market quote";
  }
  const realMarket = got.cnbc && got.cnbc.real ? got.cnbc.real : c102Fail("unavailable", "The delayed real-yield quote did not answer. The official daily print is shown separately when it is present.");
  const model = c102Assemble({
    gold: got.gold,
    silver: got.silver,
    dollar: got.dollar,
    vix: got.vix,
    nominal: got.nominal,
    realMarket: realMarket,
    dgs10: got.dgs10,
    dfii10: got.dfii10,
    positioning: got.positioning,
    events: got.events,
    spotChange: got.spotChange
  }, nowMs || Date.now());
  model.upstream = {
    gold: got.gold && got.gold.status,
    silver: got.silver && got.silver.status,
    dollar: got.dollar && got.dollar.status,
    vix: got.vix && got.vix.status,
    nominal: got.nominal && got.nominal.status,
    realMarket: realMarket && realMarket.status,
    dgs10: got.dgs10 && got.dgs10.status,
    dfii10: got.dfii10 && got.dfii10.status,
    positioning: got.positioning && got.positioning.status,
    events: got.events && got.events.status
  };
  return model;
}

async function c102ChartFetch(deps, nowMs) {
  const res = await c102Get(deps, C102_YAHOO + encodeURIComponent(C102_FUTURE) + "?range=1y&interval=1d", "application/json", (deps && deps.timeoutMs) || 2500);
  const json = await res.json();
  return c102Chart(json, nowMs || Date.now());
}

const c102Flights = new Map();

function c102WorthStoring(body) {
  if (!body || typeof body !== "object") return false;
  if (body.cacheState === "cold") return false;
  if (body.status === "timeout" || body.status === "unavailable" || body.status === "malformed") return false;
  if (Array.isArray(body.bars) && body.bars.length && body.status === "ok") return true;
  const keys = ["spot", "silver", "dollar", "vix", "nominal", "realMarket", "nominalOfficial", "realOfficial", "positioning", "events"];
  return keys.some((k) => {
    const row = body[k];
    if (!row || (row.status !== "ok" && row.status !== "stale" && row.status !== "partial")) return false;
    return typeof row.price === "number" || typeof row.value === "number" || typeof row.net === "number" || (Array.isArray(row.items) && row.items.length > 0);
  });
}

function c102WithCache(body, at, state) {
  const copy = Object.assign({}, body);
  copy.cacheState = state;
  copy.cachedAt = new Date(at).toISOString();
  if (state === "stale") {
    const age = Math.max(0, Math.round((Date.now() - at) / 1000));
    copy.cacheNote = "Stored reading from " + copy.cachedAt + ", " + c102LagText(age) + " ago. It was not refreshed for this response. It is not a new print.";
  } else {
    delete copy.cacheNote;
  }
  return copy;
}

function c102Kick(store, key, producer) {
  if (c102Flights.has(key)) return c102Flights.get(key);
  const run = Promise.resolve().then(() => producer()).then((body) => {
    if (c102WorthStoring(body)) store.set(key, { ok: true, at: Date.now(), body: body });
    return body;
  }).catch(() => null).finally(() => { c102Flights.delete(key); });
  c102Flights.set(key, run);
  return run;
}

function c102Memo(store, key, ttl, producer, cold) {
  const now = Date.now();
  const hit = store.get(key);
  const fresh = !!(hit && hit.ok && now - hit.at < ttl);
  if (!fresh) c102Kick(store, key, producer);
  if (fresh) return Promise.resolve({ body: c102WithCache(hit.body, hit.at, "fresh"), cached: true, stale: false, at: hit.at });
  if (hit && hit.ok) return Promise.resolve({ body: c102WithCache(hit.body, hit.at, "stale"), cached: true, stale: true, at: hit.at });
  return Promise.resolve({ body: typeof cold === "function" ? cold() : null, cached: false, stale: false, at: 0 });
}

function c102ColdSnap(nowMs) {
  const model = c102Assemble({}, nowMs || Date.now());
  model.ok = false;
  model.cacheState = "cold";
  model.cacheNote = "No stored reading yet. The feeds are being asked in the background. No number was filled in.";
  return model;
}

function c102ColdChart() {
  return {
    ok: false,
    status: "unavailable",
    cacheState: "cold",
    message: "No stored futures chart yet. The feed is being asked in the background. No candles were filled in.",
    cacheNote: "No stored futures chart yet. The feed is being asked in the background. No candles were filled in."
  };
}

function c102Line(label, value, extra) {
  if (value == null || value === "") return "";
  return "<p><span class=\"c102-k\">" + c102Esc(label) + "</span> " + c102Esc(value) + (extra ? " <span class=\"c102-k\">" + c102Esc(extra) + "</span>" : "") + "</p>";
}

function c102StatusText(row) {
  if (!row) return "This reading is unavailable. No number was filled in.";
  if (row.message) return row.message;
  if (row.status === "timeout") return "This source did not answer in time. No number was filled in.";
  if (row.status === "malformed") return "This source returned something we could not use. No number was filled in.";
  if (row.status === "unavailable") return "This reading is unavailable. No number was filled in.";
  return "";
}

function c102Render(model, chart) {
  const m = model || {};
  const spot = m.spot || c102Fail("unavailable");
  const chg = m.spotChange || c102Fail("unavailable");
  const dollar = m.dollar || c102Fail("unavailable");
  const nom = m.nominal || c102Fail("unavailable");
  const realM = m.realMarket || c102Fail("unavailable");
  const realO = m.realOfficial || c102Fail("unavailable");
  const nomO = m.nominalOfficial || c102Fail("unavailable");
  const vix = m.vix || c102Fail("unavailable");
  const ratio = m.ratio || c102Fail("unavailable");
  const pos = m.positioning || c102Fail("unavailable");
  const ev = m.events || c102Fail("unavailable");
  const fut = chart && chart.status === "ok" ? chart : (chart || c102Fail("unavailable", "The futures chart is not loaded yet."));
  const tile = (title, body, href, hrefLabel) => {
    return "<article class=\"c102-tile\"><h3>" + c102Esc(title) + "</h3>" + body + (href ? "<p><a href=\"" + href + "\">" + c102Esc(hrefLabel) + "</a></p>" : "") + "</article>";
  };
  const priceBit = (row, digits, suffix) => {
    if (!row || (row.status !== "ok" && row.status !== "partial" && row.status !== "stale") || typeof row.price !== "number") {
      return "<p class=\"c102-miss\">" + c102Esc(c102StatusText(row)) + "</p>";
    }
    const unit = suffix || "";
    let change = "";
    if (row.change == null) change = "<p class=\"c102-miss\">Change unavailable. No figure was filled in.</p>";
    else change = "<p>Change " + c102Esc(c102Chg(row.change, digits, unit)) + (row.change === 0 ? " (the feed returned zero)" : "") + "</p>";
    const when = row.asOfUk ? "<p class=\"c102-k\">" + c102Esc(row.asOfUk) + (row.lagSeconds != null ? " \u00b7 " + c102Esc(c102LagText(row.lagSeconds)) + " ago" : "") + "</p>" : "";
    const src = "<p class=\"c102-k\">" + c102Esc(row.source || "") + (row.frequency ? " \u00b7 " + c102Esc(row.frequency) : "") + (row.delayedByMin != null ? " \u00b7 exchange delay " + c102Esc(String(row.delayedByMin)) + " min" : "") + "</p>";
    const stale = row.status === "stale" ? "<p class=\"c102-miss\">" + c102Esc(row.message || "Older reading") + "</p>" : (row.status === "partial" && row.message ? "<p class=\"c102-miss\">" + c102Esc(row.message) + "</p>" : "");
    return "<p class=\"c102-v\">" + c102Esc(c102Num(row.price, digits)) + c102Esc(unit) + "</p>" + change + when + src + stale;
  };
  const yieldBit = (row) => {
    if (!row || (row.status !== "ok" && row.status !== "partial" && row.status !== "stale") || typeof row.value !== "number" && typeof row.price !== "number") {
      return "<p class=\"c102-miss\">" + c102Esc(c102StatusText(row)) + "</p>";
    }
    const v = typeof row.value === "number" ? row.value : row.price;
    const change = row.change == null ? "<p class=\"c102-miss\">Change unavailable.</p>" : "<p>Change " + c102Esc(c102Chg(row.change, 2, " pt")) + (row.change === 0 ? " (the feed returned zero)" : "") + "</p>";
    const when = row.asOfUk || (row.date ? row.date : "");
    return "<p class=\"c102-v\">" + c102Esc(c102Num(v, 2)) + "%</p>" + change + "<p class=\"c102-k\">" + c102Esc(when) + (row.frequency ? " \u00b7 " + c102Esc(row.frequency) : "") + "</p><p class=\"c102-k\">" + c102Esc(row.source || "") + "</p>" + (row.message && row.status !== "ok" ? "<p class=\"c102-miss\">" + c102Esc(row.message) + "</p>" : "");
  };
  let spotBody = priceBit(Object.assign({}, spot, { change: null }), 2, "");
  if (spot.status === "ok" || spot.status === "stale" || spot.status === "partial") {
    spotBody = "<p class=\"c102-v\">$" + c102Esc(c102Num(spot.price, 2)) + "</p><p class=\"c102-k\">" + c102Esc(spot.unit || "US dollars per troy ounce") + "</p>";
    spotBody += "<p class=\"c102-k\">" + c102Esc(spot.asOfUk || "") + (spot.lagSeconds != null ? " \u00b7 " + c102Esc(c102LagText(spot.lagSeconds)) + " ago" : "") + "</p>";
    spotBody += "<p class=\"c102-k\">" + c102Esc(spot.source || "") + " \u00b7 spot quote</p>";
    if (chg.status === "ok" && typeof chg.changePct === "number") {
      spotBody += "<p>Daily change " + c102Esc(c102Chg(chg.changePct, 2, "%")) + (chg.changePct === 0 ? " (the snapshot returned zero)" : "") + "</p>";
      spotBody += "<p class=\"c102-k\">" + c102Esc(chg.basis || "") + "</p><p class=\"c102-k\">" + c102Esc(chg.source || "") + "</p>";
    } else {
      spotBody += "<p class=\"c102-miss\">" + c102Esc(c102StatusText(chg)) + "</p>";
    }
    if (spot.status === "stale") spotBody += "<p class=\"c102-miss\">" + c102Esc(spot.message || "") + "</p>";
  }
  let futBody = "<p class=\"c102-miss\">" + c102Esc(c102StatusText(fut)) + "</p>";
  if (fut && fut.lastCompleted && typeof fut.lastCompleted.close === "number") {
    const lc = fut.lastCompleted;
    futBody = "<p class=\"c102-v\">$" + c102Esc(c102Num(lc.close, 2)) + "</p>";
    futBody += "<p>" + c102Esc(fut.label || "COMEX front-month gold future \u00b7 delayed") + "</p>";
    futBody += "<p class=\"c102-k\">Last completed session " + c102Esc(lc.sessionDate) + " \u00b7 " + c102Esc(fut.exchangeTimezone || "") + "</p>";
    futBody += "<p class=\"c102-k\">" + c102Esc(fut.incompleteNote || "") + "</p>";
    futBody += "<p class=\"c102-k\">Futures close, not spot. " + (lc.volume == null ? "No futures volume on that session." : "Futures volume " + c102Esc(c102Num(lc.volume, 0)) + ".") + "</p>";
  }
  const tiles = [
    tile("Gold spot", spotBody, "/gold/dashboard/", "Gold dashboard"),
    tile("Front-month future", futBody, "#c102-chart", "Chart"),
    tile("US dollar index", priceBit(dollar, 2, ""), "/gold/dashboard/", "Dollar on the gold dashboard"),
    tile("US 10-year yield", yieldBit(nom), "/markets/yields/", "Yields"),
    tile("US 10-year real yield", yieldBit(realM.status === "ok" || realM.status === "partial" || realM.status === "stale" ? realM : realO), "/markets/yields/", "Yields"),
    tile("Volatility index", priceBit(vix, 2, ""), "/data-status/", "Data status")
  ].join("");
  let macro = "<p>" + c102Esc(m.note || "") + "</p>";
  macro += "<h3>Official daily yields</h3>";
  macro += "<p class=\"c102-k\">These are separate from the delayed market quotes above. A different date is a different print, not the same moment.</p>";
  macro += yieldBit(nomO);
  macro += yieldBit(realO);
  macro += "<h3>Gold and silver</h3>";
  if (ratio.status === "ok" || ratio.status === "partial" || ratio.status === "stale") {
    macro += "<p class=\"c102-v\">" + c102Esc(c102Num(ratio.value, 1)) + "</p>";
    macro += "<p>Gold/silver ratio. " + c102Esc(ratio.formula || "") + "</p>";
    macro += "<p class=\"c102-k\">Gold " + c102Esc(c102Num(ratio.numerator.price, 2)) + " USD/oz at " + c102Esc(c102Uk(ratio.numerator.asOfUtc) || "") + ". Silver " + c102Esc(c102Num(ratio.denominator.price, 2)) + " USD/oz at " + c102Esc(c102Uk(ratio.denominator.asOfUtc) || "") + ".</p>";
    if (ratio.message) macro += "<p class=\"c102-miss\">" + c102Esc(ratio.message) + "</p>";
  } else macro += "<p class=\"c102-miss\">" + c102Esc(c102StatusText(ratio)) + "</p>";
  if (m.silver && typeof m.silver.price === "number" && (m.silver.status === "ok" || m.silver.status === "stale" || m.silver.status === "partial")) {
    macro += "<p class=\"c102-k\">Silver spot $" + c102Esc(c102Num(m.silver.price, 2)) + " per troy ounce \u00b7 " + c102Esc(m.silver.asOfUk || "") + " \u00b7 " + c102Esc(m.silver.source || "") + "</p>";
  }
  let posHtml = "<p class=\"c102-miss\">" + c102Esc(c102StatusText(pos)) + "</p>";
  if (pos.status === "ok" || pos.status === "stale") {
    posHtml = "<p class=\"c102-v\">" + c102Esc(c102Num(pos.net, 0)) + "</p>";
    posHtml += "<p>Net gold futures, money managers (contracts that gain if the price rises, minus contracts that gain if it falls).</p>";
    posHtml += "<p class=\"c102-k\">Weekly \u00b7 report date " + c102Esc(pos.reportDate) + (pos.lagDays != null ? " \u00b7 " + c102Esc(String(pos.lagDays)) + " days before today" : "") + "</p>";
    posHtml += "<p class=\"c102-k\">" + c102Esc(pos.market) + " \u00b7 " + c102Esc(pos.source) + "</p>";
    posHtml += "<p>Long " + c102Esc(c102Num(pos.long, 0)) + " \u00b7 short " + c102Esc(c102Num(pos.short, 0)) + (pos.openInterest != null ? " \u00b7 open interest " + c102Esc(c102Num(pos.openInterest, 0)) : "") + "</p>";
    if (pos.weekChange == null) posHtml += "<p class=\"c102-miss\">Change from the prior week is unavailable.</p>";
    else posHtml += "<p>Change from the prior week " + c102Esc(c102Chg(pos.weekChange, 0, " contracts")) + (pos.weekChange === 0 ? " (the two reports matched)" : "") + "</p>";
    if (pos.status === "stale") posHtml += "<p class=\"c102-miss\">" + c102Esc(pos.message || "") + "</p>";
    posHtml += "<p><a href=\"/gold/positioning/\">Gold positioning, including the ten-year range</a></p>";
  }
  let evHtml = "<p class=\"c102-miss\">" + c102Esc(c102StatusText(ev)) + "</p>";
  if (ev.items && ev.items.length) {
    evHtml = "<p class=\"c102-k\">" + c102Esc(ev.message || "") + "</p><ol class=\"c102-ev\">" + ev.items.map((it) => "<li><strong>" + c102Esc(it.name || "Release") + "</strong> <span class=\"c102-k\">" + c102Esc(it.when || it.day || "") + " \u00b7 " + c102Esc(it.agency || "") + " \u00b7 " + c102Esc(it.source || "") + "</span></li>").join("") + "</ol><p><a href=\"/calendar/\">Full calendar</a></p>";
  } else if (ev.status === "partial") evHtml = "<p class=\"c102-miss\">" + c102Esc(ev.message || "") + "</p><p><a href=\"/calendar/\">Full calendar</a></p>";
  const risk = "<ul class=\"c102-src\"><li>Gold and silver spot: gold-api.com, US dollars per troy ounce, each with its own time.</li><li>Front-month future: Yahoo Finance continuous rolling proxy, daily completed sessions only. Not spot, and not labelled with a ticker.</li><li>Dollar index: the ICE index via Yahoo Finance when the feed names ICE. A computed currency basket is not used.</li><li>US 10-year yield: delayed Cboe yield index via Yahoo Finance. Official daily Treasury print via FRED is a second line with its own date.</li><li>Real yield: delayed market quote when that quote answers, otherwise only the official daily FRED print. The dates are not merged.</li><li>Volatility: the Cboe Volatility Index via Yahoo Finance. A volatility product is not a substitute.</li><li>Positioning: CFTC weekly disaggregated futures for COMEX gold only.</li><li>Calendar: public schedules. No consensus forecast.</li></ul><p>Not investment advice. Capital at risk.</p><p><a href=\"/data-status/\">Data status</a> \u00b7 <a href=\"/methodology\">Methodology</a></p>";
  const chartBlock = "<div id=\"c102-chart\" class=\"c102-chart\"><div class=\"c102-chart-h\"><h2 id=\"c102-chart-title\">" + c102Esc(fut.label || "COMEX front-month gold future \u00b7 delayed") + "</h2><p id=\"c102-chart-note\" class=\"c102-k\">" + c102Esc((fut && fut.historyNote) || "The chart loads from the futures feed. An incomplete session is left out.") + "</p></div><div class=\"c102-tools\" role=\"group\" aria-label=\"Chart range\"><button type=\"button\" data-c102-range=\"63\" aria-pressed=\"false\">3 months</button><button type=\"button\" data-c102-range=\"126\" aria-pressed=\"true\">6 months</button><button type=\"button\" data-c102-range=\"252\" aria-pressed=\"false\">1 year</button><button type=\"button\" data-c102-ma=\"20\" aria-pressed=\"true\">20-session average</button><button type=\"button\" data-c102-ma=\"50\" aria-pressed=\"true\">50-session average</button><button type=\"button\" data-c102-table aria-expanded=\"false\" aria-controls=\"c102-table\">Table of sessions</button></div><p id=\"c102-readout\" class=\"c102-read\"></p><div id=\"c102-live\" class=\"c102-live\" aria-live=\"polite\"></div><canvas id=\"c102-canvas\" tabindex=\"0\" role=\"img\" aria-describedby=\"c102-readout c102-chart-note\"></canvas><div id=\"c102-table\" hidden></div></div>";
  return "<div class=\"c102\" data-c102><p class=\"c102-k\">" + c102Esc(m.generatedAtUk || "") + "</p><div class=\"c102-tiles\">" + tiles + "</div>" + chartBlock + "<div class=\"c102-grid\"><section aria-labelledby=\"c102-macro\"><h2 id=\"c102-macro\">Macro</h2>" + macro + "</section><section aria-labelledby=\"c102-pos\"><h2 id=\"c102-pos\">Positioning</h2>" + posHtml + "</section></div><section aria-labelledby=\"c102-ev\"><h2 id=\"c102-ev\">Events</h2>" + evHtml + "</section><section aria-labelledby=\"c102-risk\"><h2 id=\"c102-risk\">Risk and sources</h2>" + risk + "</section></div>";
}

const C102_CSS = "<style id=\"c102-css\">.c102{font:15px/1.5 var(--sans,Inter,system-ui,sans-serif);color:var(--ink,#1b1b1b);min-width:0;max-width:100%;overflow-x:clip;container-type:inline-size}.c102 h2,.c102 h3{font-family:var(--serif,Georgia,serif);line-height:1.2;margin:0 0 8px}.c102 h2{font-size:1.6rem}.c102-k{color:var(--muted,#5f6368);font-size:14px}.c102-v{font:600 1.7rem/1.2 var(--serif,Georgia,serif);margin:4px 0}.c102-miss{color:var(--ink,#1b1b1b);background:transparent;border-left:3px solid var(--amber,#8a6a12);padding:4px 0 4px 10px;margin:8px 0}.c102-tiles{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:12px 0 18px}.c102-tile{min-width:0;border-top:2px solid var(--ink,#1b1b1b);padding:10px 2px 4px}.c102-tile h3{font:600 14px/1.3 var(--sans,Inter,sans-serif);letter-spacing:.02em;margin:0 0 6px}.c102-tile p{margin:4px 0;overflow-wrap:anywhere}.c102 a{text-decoration-thickness:1px;text-underline-offset:3px}.c102 a:focus-visible,.c102 button:focus-visible,#c102-canvas:focus-visible{outline:2px solid var(--accent,#1f3a5f);outline-offset:3px}.c102-tools{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.c102-tools button{min-height:44px;min-width:44px;padding:8px 12px;font:600 15px/1.2 var(--sans,Inter,sans-serif);background:transparent;color:inherit;border:1px solid var(--rule,#dedad2);border-radius:4px;cursor:pointer}.c102-tools button[aria-pressed=true]{background:var(--ink,#1b1b1b);color:var(--paper,#fbfaf7);border-color:var(--ink,#1b1b1b)}.c102-chart{min-width:0;margin:8px 0 22px}#c102-canvas{display:block;width:100%;height:460px;touch-action:pan-y;background:transparent}.c102-read{min-height:1.4em;font-size:15px}.c102-live{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}.c102-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:28px;min-width:0}.c102 section{min-width:0;padding:8px 0 18px}.c102-ev,.c102-src{padding-left:1.2rem;margin:8px 0}.c102-ev li,.c102-src li{margin:6px 0}.c102-table-scroll{display:block;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}.c102-ohlc{border-collapse:collapse;width:max-content;min-width:100%;font-size:15px}.c102-ohlc caption{caption-side:top;text-align:left;font-size:15px;padding:0 0 8px}.c102-ohlc th,.c102-ohlc td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule,#dedad2);white-space:nowrap;font-weight:400}.c102-ohlc thead th{font-weight:600}@container (max-width:900px){.c102-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.c102-grid{grid-template-columns:1fr}#c102-canvas{height:360px}}@media (max-width:700px){.c102-tiles{grid-template-columns:1fr}.c102-grid{grid-template-columns:1fr}#c102-canvas{height:300px}.c102{font-size:15px}}@media (prefers-reduced-motion:reduce){.c102 *{transition:none!important;animation:none!important}}</style>";

function c102Install() {
  if (c102Install.done) return;
  try {
    if (typeof C93_NAV !== "undefined" && Array.isArray(C93_NAV) && !C93_NAV.some((x) => x && x[0] === "/terminal/")) {
      const at = C93_NAV.findIndex((x) => x && x[0] === "/gold/");
      const item = ["/terminal/", "Terminal"];
      if (at >= 0) C93_NAV.splice(at + 1, 0, item); else C93_NAV.push(item);
    }
  } catch (e) {}
  try {
    if (typeof C101B_GROUPS !== "undefined" && Array.isArray(C101B_GROUPS)) {
      const g = C101B_GROUPS.find((x) => x && x[0] === "Gold and macro");
      if (g && Array.isArray(g[1]) && !g[1].some((x) => x && x[0] === "/terminal/")) g[1].unshift(["/terminal/", "Terminal"]);
    }
  } catch (e) {}
  const store = new Map();
  const depsOf = () => ({
    fetch: typeof fetch === "function" ? fetch : null,
    ua: typeof C97_UA === "string" ? C97_UA : C102_UA,
    fred: typeof c97Fred === "function" ? async (id) => {
      const r = await c97Fred(id, 2);
      const rows = r && Array.isArray(r.v) ? r.v : (Array.isArray(r) ? r : null);
      return c102FredRows(rows, id);
    } : null,
    calendar: typeof c97Calendar === "function" ? () => c97Calendar() : null,
    goldDash: typeof c97GoldDash === "function" ? () => c97GoldDash() : null,
    cnbc: typeof c101fRates === "function" ? () => c101fRates() : null
  });
  async function snapshot() {
    const hit = await c102Memo(store, "snap", 60 * 1000, () => c102Collect(depsOf(), Date.now()), () => c102ColdSnap(Date.now()));
    return hit.body || c102ColdSnap(Date.now());
  }
  async function chart() {
    const hit = await c102Memo(store, "chart", 120 * 1000, () => c102ChartFetch(depsOf(), Date.now()), c102ColdChart);
    return hit.body || c102ColdChart();
  }
  function cacheControl(body) {
    if (!body || body.cacheState === "cold") return "no-store";
    if (body.cacheState === "stale") return "private, max-age=0, stale-while-revalidate=120";
    return "private, max-age=15, stale-while-revalidate=120";
  }
  function send(res, code, body) {
    const payload = JSON.stringify(body);
    res.writeHead(code, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": cacheControl(body),
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin"
    });
    res.end(payload);
  }
  async function page(req, res) {
    try { if (typeof c97Hook === "function") c97Hook(req, res); } catch (e) {}
    let user = null;
    try { user = typeof c96UserOf === "function" ? await c96UserOf(req) : null; } catch (e) { user = null; }
    const origin = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
    const client = c102Install.clientJs || "";
    const body = C102_CSS + "<section><div class=\"kicker\">Markets</div><h1>Terminal</h1><p class=\"dek\">A delayed look at COMEX gold futures beside gold spot, the dollar, US yields and volatility. Each figure keeps its own source and time.</p><p class=\"byline\">Edited by Vraj Patel</p></section><section id=\"c102-mount\" aria-busy=\"true\"><p>Loading readings\u2026</p></section><script>" + client + "</script><script>document.getElementById(\"c102-mount\").setAttribute(\"aria-busy\",\"false\");if(window.c102ui){window.c102ui.mount(document.getElementById(\"c102-mount\"));}else{document.getElementById(\"c102-mount\").innerHTML=\"<p>The terminal script did not start. The rest of the site is unchanged. <a href=\\\"/gold/dashboard/\\\">Gold dashboard</a></p>\";}</script><noscript><p>This page loads its figures in the browser. The <a href=\"/gold/dashboard/\">gold dashboard</a>, <a href=\"/calendar/\">calendar</a> and <a href=\"/gold/positioning/\">positioning</a> pages work without it.</p></noscript>";
    const shell = {
      title: "Terminal | The Dispatch Market",
      path: "/terminal/",
      desc: "Delayed COMEX gold futures, gold spot, the dollar, US yields and volatility, with the source and UK time on each figure. Not investment advice.",
      user: user,
      extraHead: "<link rel=\"canonical\" href=\"" + origin + "/terminal/\"><meta property=\"og:title\" content=\"Terminal | The Dispatch Market\"><meta property=\"og:description\" content=\"Delayed COMEX gold futures, gold spot, the dollar, US yields and volatility, with sources and UK times.\">",
      body: body
    };
    const html = typeof c93Shell === "function" ? c93Shell(shell) : "<!doctype html><title>Terminal | The Dispatch Market</title>" + body;
    if (typeof c93Html === "function") return c93Html(req, res, html, "private, max-age=60");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "private, max-age=60" });
    res.end(req.method === "HEAD" ? undefined : html);
  }
  if (typeof handle === "function" && !handle.__c102) {
    const prev = handle;
    const wrapped = async function (req, res) {
      try {
        if (typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON) return prev.apply(this, arguments);
        let u = null;
        try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { u = null; }
        const p = u ? u.pathname : "";
        if (req.method === "GET" || req.method === "HEAD") {
          if (p === "/terminal") { res.writeHead(301, { Location: "/terminal/" }); return res.end(); }
          if (p === "/terminal/") return page(req, res);
          if (p === "/api/c102/terminal") {
            try { return send(res, 200, await snapshot()); }
            catch (e) { return send(res, 200, c102Assemble({ gold: c102Classify(e) }, Date.now())); }
          }
          if (p === "/api/c102/chart") {
            try { return send(res, 200, await chart()); }
            catch (e) { return send(res, 200, c102Classify(e)); }
          }
        }
      } catch (e) { console.error("[c102]", e && e.message); }
      return prev.apply(this, arguments);
    };
    wrapped.__c102 = 1;
    handle = wrapped;
  }
  if (typeof renderPublicSitemap === "function" && !renderPublicSitemap.__c102) {
    const prevMap = renderPublicSitemap;
    const wrappedMap = async function () {
      let x = await prevMap.apply(this, arguments);
      const origin = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
      if (typeof x !== "string" || x.indexOf("</urlset>") < 0 || x.indexOf(origin + "/terminal/") >= 0) return x;
      return x.replace("</urlset>", "  <url><loc>" + origin + "/terminal/</loc><changefreq>hourly</changefreq><priority>0.7</priority></url>\n</urlset>");
    };
    wrappedMap.__c102 = 1;
    renderPublicSitemap = wrappedMap;
  }
  try {
    const warm = setTimeout(() => {
      snapshot().catch(() => {});
      chart().catch(() => {});
    }, 50);
    if (warm && typeof warm.unref === "function") warm.unref();
  } catch (e) {}
  c102Install.done = 1;
}

const api = {
  c102Esc, c102Uk, c102Ymd, c102ParseMetal, c102Ratio, c102YahooQuote, c102FredCsv, c102FredRows, c102Cot, c102Chart, c102Sma,
  c102SnapshotChange, c102Events, c102Cnbc, c102Assemble, c102Collect, c102ChartFetch, c102Render, c102Install, c102Classify,
  c102Memo, c102ColdSnap, c102ColdChart, c102WorthStoring,
  C102_CSS, C102_FUTURE
};
if (typeof module !== "undefined" && module.exports) module.exports = api;

  var c102api = module.exports;
  c102api.c102Install.clientJs = "/* chat102 terminal client. No polling. Two requests, then one retry only when the server has no stored reading yet. */\n(function (root) {\n  \"use strict\";\n  function esc(s) {\n    return String(s == null ? \"\" : s).replace(/[&<>\"]/g, function (c) {\n      return { \"&\": \"&amp;\", \"<\": \"&lt;\", \">\": \"&gt;\", \"\\\"\": \"&quot;\" }[c];\n    });\n  }\n  function num(n, d) {\n    if (typeof n !== \"number\" || !isFinite(n)) return \"\";\n    return n.toLocaleString(\"en-GB\", { minimumFractionDigits: d, maximumFractionDigits: d });\n  }\n  function chg(n, d, suffix) {\n    if (typeof n !== \"number\" || !isFinite(n)) return \"\";\n    if (n === 0) return (d ? \"0.\" + \"0\".repeat(d) : \"0\") + (suffix || \"\");\n    return (n > 0 ? \"+\" : \"\\u2212\") + Math.abs(n).toFixed(d) + (suffix || \"\");\n  }\n  function uk(iso) {\n    var ms = Date.parse(iso);\n    if (!isFinite(ms)) return \"\";\n    try {\n      return new Intl.DateTimeFormat(\"en-GB\", { timeZone: \"Europe/London\", weekday: \"short\", day: \"numeric\", month: \"long\", year: \"numeric\", hour: \"2-digit\", minute: \"2-digit\", hourCycle: \"h23\" }).format(new Date(ms));\n    } catch (e) { return \"\"; }\n  }\n  function miss(row) {\n    if (!row) return \"This reading is unavailable. No number was filled in.\";\n    if (row.message) return row.message;\n    if (row.status === \"timeout\") return \"This source did not answer in time. No number was filled in.\";\n    if (row.status === \"malformed\") return \"This source returned something we could not use. No number was filled in.\";\n    return \"This reading is unavailable. No number was filled in.\";\n  }\n  function shown(row) { return row && (row.status === \"ok\" || row.status === \"partial\" || row.status === \"stale\"); }\n  function tile(title, body, href, label) {\n    return \"<article class=\\\"c102-tile\\\"><h3>\" + esc(title) + \"</h3>\" + body + (href ? \"<p><a href=\\\"\" + href + \"\\\">\" + esc(label) + \"</a></p>\" : \"\") + \"</article>\";\n  }\n  function when(row) {\n    var t = row.asOfUk || uk(row.asOfUtc) || row.date || \"\";\n    var lag = row.lagSeconds != null ? \" \\u00b7 \" + (row.lagSeconds < 90 ? row.lagSeconds + \" seconds\" : row.lagSeconds < 5400 ? Math.round(row.lagSeconds / 60) + \" minutes\" : Math.round(row.lagSeconds / 3600) + \" hours\") + \" ago\" : \"\";\n    return t ? \"<p class=\\\"c102-k\\\">\" + esc(t + lag) + (row.frequency ? \" \\u00b7 \" + esc(row.frequency) : \"\") + (row.delayedByMin != null ? \" \\u00b7 exchange delay \" + esc(String(row.delayedByMin)) + \" min\" : \"\") + \"</p>\" : \"\";\n  }\n  function priceTile(row, digits) {\n    if (!shown(row) || typeof row.price !== \"number\") return \"<p class=\\\"c102-miss\\\">\" + esc(miss(row)) + \"</p>\";\n    var change = row.change == null ? \"<p class=\\\"c102-miss\\\">Change unavailable. No figure was filled in.</p>\" : \"<p>Change \" + esc(chg(row.change, digits, \"\")) + (row.change === 0 ? \" (the feed returned zero)\" : \"\") + \"</p>\";\n    var stale = row.status !== \"ok\" && row.message ? \"<p class=\\\"c102-miss\\\">\" + esc(row.message) + \"</p>\" : \"\";\n    return \"<p class=\\\"c102-v\\\">\" + esc(num(row.price, digits)) + \"</p>\" + change + when(row) + \"<p class=\\\"c102-k\\\">\" + esc(row.source || \"\") + \"</p>\" + stale;\n  }\n  function yieldTile(row) {\n    var v = row && (typeof row.value === \"number\" ? row.value : row.price);\n    if (!shown(row) || typeof v !== \"number\") return \"<p class=\\\"c102-miss\\\">\" + esc(miss(row)) + \"</p>\";\n    var change = row.change == null ? \"<p class=\\\"c102-miss\\\">Change unavailable.</p>\" : \"<p>Change \" + esc(chg(row.change, 2, row.unit === \"percent\" || row.value != null ? \" pt\" : \"\")) + (row.change === 0 ? \" (the feed returned zero)\" : \"\") + \"</p>\";\n    var extra = row.status !== \"ok\" && row.message ? \"<p class=\\\"c102-miss\\\">\" + esc(row.message) + \"</p>\" : \"\";\n    return \"<p class=\\\"c102-v\\\">\" + esc(num(v, 2)) + \"%</p>\" + change + when(row) + \"<p class=\\\"c102-k\\\">\" + esc(row.source || \"\") + \"</p>\" + extra;\n  }\n  function render(model, chart) {\n    model = model || {};\n    var spot = model.spot || {};\n    var ch = model.spotChange || {};\n    var fut = chart && chart.lastCompleted ? chart : null;\n    var spotBody;\n    if (shown(spot) && typeof spot.price === \"number\") {\n      spotBody = \"<p class=\\\"c102-v\\\">$\" + esc(num(spot.price, 2)) + \"</p><p class=\\\"c102-k\\\">\" + esc(spot.unit || \"US dollars per troy ounce\") + \"</p>\" + when(spot) + \"<p class=\\\"c102-k\\\">\" + esc(spot.source || \"\") + \" \\u00b7 spot quote</p>\";\n      if (ch.status === \"ok\" && typeof ch.changePct === \"number\") spotBody += \"<p>Daily change \" + esc(chg(ch.changePct, 2, \"%\")) + (ch.changePct === 0 ? \" (the snapshot returned zero)\" : \"\") + \"</p><p class=\\\"c102-k\\\">\" + esc(ch.basis || \"\") + \"</p><p class=\\\"c102-k\\\">\" + esc(ch.source || \"\") + \"</p>\";\n      else spotBody += \"<p class=\\\"c102-miss\\\">\" + esc(miss(ch)) + \"</p>\";\n      if (spot.status === \"stale\" && spot.message) spotBody += \"<p class=\\\"c102-miss\\\">\" + esc(spot.message) + \"</p>\";\n    } else spotBody = \"<p class=\\\"c102-miss\\\">\" + esc(miss(spot)) + \"</p>\";\n    var futBody = \"<p class=\\\"c102-miss\\\">\" + esc(fut ? \"\" : miss(chart)) + \"</p>\";\n    if (fut) {\n      var lc = fut.lastCompleted;\n      futBody = \"<p class=\\\"c102-v\\\">$\" + esc(num(lc.close, 2)) + \"</p><p>\" + esc(fut.label || \"COMEX front-month gold future \\u00b7 delayed\") + \"</p><p class=\\\"c102-k\\\">Last completed session \" + esc(lc.sessionDate) + \" \\u00b7 \" + esc(fut.exchangeTimezone || \"\") + \"</p><p class=\\\"c102-k\\\">\" + esc(fut.incompleteNote || \"\") + \"</p><p class=\\\"c102-k\\\">\" + (lc.volume == null ? \"No futures volume on that session.\" : \"Futures volume \" + esc(num(lc.volume, 0)) + \", not spot volume.\") + \"</p>\";\n    }\n    var real = model.realMarket && shown(model.realMarket) && (typeof model.realMarket.value === \"number\" || typeof model.realMarket.price === \"number\") ? model.realMarket : model.realOfficial;\n    var tiles = [\n      tile(\"Gold spot\", spotBody, \"/gold/dashboard/\", \"Gold dashboard\"),\n      tile(\"Front-month future\", futBody, \"#c102-chart\", \"Chart\"),\n      tile(\"US dollar index\", priceTile(model.dollar, 2), \"/gold/dashboard/\", \"Dollar on the gold dashboard\"),\n      tile(\"US 10-year yield\", yieldTile(model.nominal), \"/markets/yields/\", \"Yields\"),\n      tile(\"US 10-year real yield\", yieldTile(real), \"/markets/yields/\", \"Yields\"),\n      tile(\"Volatility index\", priceTile(model.vix, 2), \"/data-status/\", \"Data status\")\n    ].join(\"\");\n    var ratio = model.ratio || {};\n    var macro = \"<p>\" + esc(model.note || \"\") + \"</p><h3>Official daily yields</h3><p class=\\\"c102-k\\\">These prints keep their own dates. They are not the same moment as the delayed quotes.</p>\" + yieldTile(model.nominalOfficial) + yieldTile(model.realOfficial) + \"<h3>Gold and silver</h3>\";\n    if (shown(ratio) && typeof ratio.value === \"number\") {\n      macro += \"<p class=\\\"c102-v\\\">\" + esc(num(ratio.value, 1)) + \"</p><p>\" + esc(ratio.formula || \"Gold spot \\u00f7 silver spot\") + \"</p>\";\n      macro += \"<p class=\\\"c102-k\\\">Gold \" + esc(num(ratio.numerator.price, 2)) + \" USD per troy ounce, \" + esc(uk(ratio.numerator.asOfUtc)) + \". Silver \" + esc(num(ratio.denominator.price, 2)) + \" USD per troy ounce, \" + esc(uk(ratio.denominator.asOfUtc)) + \".</p>\";\n      if (ratio.message) macro += \"<p class=\\\"c102-miss\\\">\" + esc(ratio.message) + \"</p>\";\n    } else macro += \"<p class=\\\"c102-miss\\\">\" + esc(miss(ratio)) + \"</p>\";\n    var pos = model.positioning || {};\n    var posHtml;\n    if (pos.status === \"ok\" || pos.status === \"stale\") {\n      posHtml = \"<p class=\\\"c102-v\\\">\" + esc(num(pos.net, 0)) + \"</p><p>Net gold futures, money managers. Contracts that gain if the price rises, minus contracts that gain if it falls.</p>\";\n      posHtml += \"<p class=\\\"c102-k\\\">Weekly \\u00b7 report date \" + esc(pos.reportDate) + (pos.lagDays != null ? \" \\u00b7 \" + esc(String(pos.lagDays)) + \" days before today\" : \"\") + \"</p>\";\n      posHtml += \"<p class=\\\"c102-k\\\">\" + esc(pos.market || \"\") + \" \\u00b7 \" + esc(pos.source || \"\") + \"</p>\";\n      posHtml += \"<p>Long \" + esc(num(pos.long, 0)) + \" \\u00b7 short \" + esc(num(pos.short, 0)) + (pos.openInterest != null ? \" \\u00b7 open interest \" + esc(num(pos.openInterest, 0)) : \"\") + \"</p>\";\n      posHtml += pos.weekChange == null ? \"<p class=\\\"c102-miss\\\">Change from the prior week is unavailable.</p>\" : \"<p>Change from the prior week \" + esc(chg(pos.weekChange, 0, \" contracts\")) + (pos.weekChange === 0 ? \" (the two reports matched)\" : \"\") + \"</p>\";\n      if (pos.status === \"stale\") posHtml += \"<p class=\\\"c102-miss\\\">\" + esc(pos.message || \"\") + \"</p>\";\n      posHtml += \"<p><a href=\\\"/gold/positioning/\\\">Gold positioning, including the ten-year range</a></p>\";\n    } else posHtml = \"<p class=\\\"c102-miss\\\">\" + esc(miss(pos)) + \"</p>\";\n    var ev = model.events || {};\n    var evHtml;\n    if (ev.items && ev.items.length) {\n      evHtml = \"<p class=\\\"c102-k\\\">\" + esc(ev.message || \"Scheduled releases only. Consensus forecasts are not shown.\") + \"</p><ol class=\\\"c102-ev\\\">\" + ev.items.map(function (it) {\n        return \"<li><strong>\" + esc(it.name || \"Release\") + \"</strong> <span class=\\\"c102-k\\\">\" + esc(it.when || it.day || \"\") + \" \\u00b7 \" + esc(it.agency || \"\") + \" \\u00b7 \" + esc(it.source || \"\") + \"</span></li>\";\n      }).join(\"\") + \"</ol><p><a href=\\\"/calendar/\\\">Full calendar</a></p>\";\n    } else evHtml = \"<p class=\\\"c102-miss\\\">\" + esc(miss(ev)) + \"</p><p><a href=\\\"/calendar/\\\">Full calendar</a></p>\";\n    var risk = \"<ul class=\\\"c102-src\\\"><li>Gold and silver spot from gold-api.com, in US dollars per troy ounce, each with its own time. A futures percentage is not used as the spot change.</li><li>The chart is the COMEX front-month future on a continuous rolling series. It is not spot gold and the volume is not spot volume.</li><li>The dollar index is the ICE index via Yahoo Finance when the feed names ICE. A computed currency basket is not shown as that index.</li><li>The US 10-year yield is a delayed quote. The official daily Treasury print is a second figure with its own date.</li><li>The real yield keeps the delayed quote and the official daily print apart.</li><li>Volatility is the Cboe Volatility Index. A volatility note is not a substitute.</li><li>Positioning is the weekly CFTC report for COMEX gold only.</li><li>The calendar lists scheduled releases. It does not include a consensus forecast.</li></ul><p>Not investment advice. Capital at risk.</p><p><a href=\\\"/data-status/\\\">Data status</a> \\u00b7 <a href=\\\"/methodology\\\">Methodology</a> \\u00b7 <a href=\\\"/dashboard/\\\">Dashboard</a> \\u00b7 <a href=\\\"/gold/\\\">Gold</a></p>\";\n    var label = (fut && fut.label) || \"COMEX front-month gold future \\u00b7 delayed\";\n    var note = (fut && fut.historyNote) || \"Completed sessions only. The current session is left out when the feed includes it.\";\n    var extra = [fut && fut.barTimeNote, fut && fut.volumeRepeatNote, fut && fut.incompleteNote].filter(Boolean).join(\" \");\n    var chartHtml = \"<div id=\\\"c102-chart\\\" class=\\\"c102-chart\\\"><div class=\\\"c102-chart-h\\\"><h2 id=\\\"c102-chart-title\\\">\" + esc(label) + \"</h2><p id=\\\"c102-chart-note\\\" class=\\\"c102-k\\\">\" + esc(note) + \"</p><p class=\\\"c102-k\\\">\" + esc(extra) + \"</p></div><div class=\\\"c102-tools\\\" role=\\\"group\\\" aria-label=\\\"Chart range\\\"><button type=\\\"button\\\" data-c102-months=\\\"3\\\" aria-pressed=\\\"false\\\">3 months</button><button type=\\\"button\\\" data-c102-months=\\\"6\\\" aria-pressed=\\\"true\\\">6 months</button><button type=\\\"button\\\" data-c102-months=\\\"12\\\" aria-pressed=\\\"false\\\">1 year</button><button type=\\\"button\\\" data-c102-ma=\\\"20\\\" aria-pressed=\\\"true\\\">20-session average</button><button type=\\\"button\\\" data-c102-ma=\\\"50\\\" aria-pressed=\\\"true\\\">50-session average</button><button type=\\\"button\\\" id=\\\"c102-table-btn\\\" aria-expanded=\\\"false\\\" aria-controls=\\\"c102-table\\\">Table of sessions</button></div><p id=\\\"c102-span\\\" class=\\\"c102-k\\\"></p><p id=\\\"c102-readout\\\" class=\\\"c102-read\\\">Use the arrow keys on the chart to read a session.</p><div id=\\\"c102-live\\\" class=\\\"c102-live\\\" aria-live=\\\"polite\\\"></div><canvas id=\\\"c102-canvas\\\" width=\\\"800\\\" height=\\\"460\\\" tabindex=\\\"0\\\" role=\\\"img\\\" aria-label=\\\"\" + esc(label) + \"\\\" aria-describedby=\\\"c102-readout c102-chart-note\\\"></canvas><div id=\\\"c102-table\\\" hidden></div></div>\";\n    var cacheHtml = model.cacheNote ? \"<p class=\\\"c102-miss\\\" id=\\\"c102-cache\\\">\" + esc(model.cacheNote) + \"</p>\" : \"\";\n    var chartCache = chart && chart.cacheNote ? \"<p class=\\\"c102-miss\\\">\" + esc(chart.cacheNote) + \"</p>\" : \"\";\n    return \"<div class=\\\"c102\\\" id=\\\"c102\\\"><p class=\\\"c102-k\\\">Assembled \" + esc(model.generatedAtUk || uk(model.generatedAtUtc) || \"\") + \"</p>\" + cacheHtml + \"<div class=\\\"c102-tiles\\\">\" + tiles + \"</div>\" + chartCache + chartHtml + \"<div class=\\\"c102-grid\\\"><section aria-labelledby=\\\"c102-macro\\\"><h2 id=\\\"c102-macro\\\">Macro</h2>\" + macro + \"</section><section aria-labelledby=\\\"c102-pos\\\"><h2 id=\\\"c102-pos\\\">Positioning</h2>\" + posHtml + \"</section></div><section aria-labelledby=\\\"c102-ev\\\"><h2 id=\\\"c102-ev\\\">Events</h2>\" + evHtml + \"</section><section aria-labelledby=\\\"c102-risk\\\"><h2 id=\\\"c102-risk\\\">Risk and sources</h2>\" + risk + \"</section></div>\";\n  }\n\n  function cssColor(name, fallback) {\n    try {\n      var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();\n      return v || fallback;\n    } catch (e) { return fallback; }\n  }\n  function shiftMonth(iso, delta) {\n    var m = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(String(iso || \"\"));\n    if (!m) return \"\";\n    var d = new Date(Date.UTC(+m[1], +m[2] - 1 + delta, +m[3]));\n    return d.toISOString().slice(0, 10);\n  }\n  function windowBars(bars, months) {\n    var list = bars || [];\n    if (!list.length) return [];\n    var n = Number(months);\n    if (!isFinite(n) || n <= 0) n = 6;\n    var cut = shiftMonth(list[list.length - 1].sessionDate, -n);\n    var out = list.filter(function (b) { return b && b.sessionDate && b.sessionDate >= cut; });\n    return out.length ? out : list.slice(-1);\n  }\n  function draw(canvas, chart, state) {\n    if (!canvas || !canvas.getContext) return;\n    var ctx = canvas.getContext(\"2d\");\n    var bars = windowBars(chart && chart.bars, state.months);\n    var dpr = (root.devicePixelRatio || 1);\n    var w = canvas.clientWidth || 320;\n    var h = canvas.clientHeight || 300;\n    canvas.width = Math.max(1, Math.floor(w * dpr));\n    canvas.height = Math.max(1, Math.floor(h * dpr));\n    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);\n    ctx.clearRect(0, 0, w, h);\n    var ink = cssColor(\"--ink\", \"#1b1b1b\");\n    var muted = cssColor(\"--muted\", \"#5f6368\");\n    var rule = cssColor(\"--rule\", \"#dedad2\");\n    var up = cssColor(\"--up\", \"#2f6b47\");\n    var down = cssColor(\"--down\", \"#a23b2a\");\n    var paper = cssColor(\"--paper\", \"#fbfaf7\");\n    ctx.fillStyle = paper;\n    ctx.fillRect(0, 0, w, h);\n    if (!bars.length) {\n      ctx.fillStyle = ink;\n      ctx.font = \"15px sans-serif\";\n      ctx.fillText(\"No completed session to draw.\", 12, 28);\n      return;\n    }\n    var padL = 58, padR = 12, padT = 12, padB = 28;\n    var volH = Math.max(36, Math.round(h * 0.18));\n    var plotB = h - padB - volH - 8;\n    var highs = bars.map(function (b) { return b.h; });\n    var lows = bars.map(function (b) { return b.l; });\n    var max = Math.max.apply(null, highs);\n    var min = Math.min.apply(null, lows);\n    if (!(max > min)) { max += 1; min -= 1; }\n    var y = function (v) { return padT + (max - v) / (max - min) * (plotB - padT); };\n    var slot = (w - padL - padR) / bars.length;\n    ctx.strokeStyle = rule;\n    ctx.lineWidth = 1;\n    ctx.fillStyle = muted;\n    ctx.font = \"14px sans-serif\";\n    for (var g = 0; g < 4; g++) {\n      var val = min + (max - min) * g / 3;\n      var yy = y(val);\n      ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke();\n      ctx.fillText(num(val, 0), 4, yy + 4);\n    }\n    var vols = bars.map(function (b) { return b.volume || 0; });\n    var vmax = Math.max.apply(null, vols.concat([1]));\n    bars.forEach(function (b, i) {\n      var x = padL + slot * i + slot / 2;\n      var rising = b.c >= b.o;\n      ctx.strokeStyle = rising ? up : down;\n      ctx.fillStyle = rising ? up : down;\n      ctx.beginPath();\n      ctx.moveTo(x, y(b.h));\n      ctx.lineTo(x, y(b.l));\n      ctx.stroke();\n      var top = y(Math.max(b.o, b.c));\n      var bot = y(Math.min(b.o, b.c));\n      ctx.fillRect(x - Math.max(1, slot * 0.28), top, Math.max(2, slot * 0.56), Math.max(1, bot - top));\n      if (b.volume) {\n        var vh = (b.volume / vmax) * volH;\n        ctx.globalAlpha = 0.45;\n        ctx.fillRect(x - Math.max(1, slot * 0.28), h - padB - vh, Math.max(2, slot * 0.56), vh);\n        ctx.globalAlpha = 1;\n      }\n    });\n    function line(series, color) {\n      if (!state[\"ma\" + series] || !chart[\"ma\" + series] || chart[\"ma\" + series].status !== \"ok\") return;\n      var map = {};\n      chart[\"ma\" + series].points.forEach(function (p) { map[p.sessionDate] = p.value; });\n      ctx.strokeStyle = color;\n      ctx.lineWidth = 1.5;\n      ctx.beginPath();\n      var started = false;\n      bars.forEach(function (b, i) {\n        if (map[b.sessionDate] == null) return;\n        var x = padL + slot * i + slot / 2;\n        var yy = y(map[b.sessionDate]);\n        if (!started) { ctx.moveTo(x, yy); started = true; } else ctx.lineTo(x, yy);\n      });\n      ctx.stroke();\n    }\n    line(20, cssColor(\"--amber\", \"#8a6a12\"));\n    line(50, cssColor(\"--accent\", \"#1f3a5f\"));\n    if (state.index >= 0 && state.index < bars.length) {\n      var b = bars[state.index];\n      var x = padL + slot * state.index + slot / 2;\n      ctx.strokeStyle = ink;\n      ctx.setLineDash([3, 3]);\n      ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, h - padB); ctx.stroke();\n      ctx.setLineDash([]);\n    }\n    ctx.fillStyle = muted;\n    ctx.font = \"14px sans-serif\";\n    var left = bars[0].sessionDate;\n    var right = bars[bars.length - 1].sessionDate;\n    ctx.fillText(left, padL, h - 8);\n    var rightW = ctx.measureText ? ctx.measureText(right).width : 88;\n    ctx.fillText(right, Math.max(padL + 96, w - padR - rightW), h - 8);\n    state._bars = bars;\n    state._geom = { padL: padL, slot: slot };\n  }\n  function barClock(bar) { return String(bar && bar.timeUtc || \"\").slice(11, 16); }\n  function barStamp(bar, chart) {\n    var tz = (chart && chart.exchangeTimezone) || \"America/New_York\";\n    var clock = barClock(bar);\n    return \"Bar timestamp \" + clock + \" UTC. That is midnight at the start of session date \" + bar.sessionDate + \" in \" + tz + \" (04:00 UTC in US daylight time, 05:00 UTC in US standard time). Not a settlement time.\";\n  }\n  function readout(chart, bar) {\n    if (!bar) return \"No session selected.\";\n    var vol = bar.volume == null ? \"Volume not returned for this session.\" : \"Futures volume \" + num(bar.volume, 0) + \".\";\n    var tz = (chart && chart.exchangeTimezone) || \"America/New_York\";\n    return \"Session date \" + bar.sessionDate + \" (\" + tz + \"). Open \" + num(bar.o, 2) + \", high \" + num(bar.h, 2) + \", low \" + num(bar.l, 2) + \", close \" + num(bar.c, 2) + \". \" + vol + \" \" + barStamp(bar, chart);\n  }\n  function tableHtml(bars, chart) {\n    var view = (bars || []).slice(-12);\n    var rows = view.map(function (b) {\n      var vol = b.volume == null ? \"Not returned\" : num(b.volume, 0);\n      return \"<tr><th scope=\\\"row\\\">\" + esc(b.sessionDate) + \"</th><td>\" + esc(num(b.o, 2)) + \"</td><td>\" + esc(num(b.h, 2)) + \"</td><td>\" + esc(num(b.l, 2)) + \"</td><td>\" + esc(num(b.c, 2)) + \"</td><td>\" + esc(vol) + \"</td><td>\" + esc(barStamp(b, chart)) + \"</td></tr>\";\n    }).join(\"\");\n    return \"<div class=\\\"c102-table-scroll\\\" tabindex=\\\"0\\\" role=\\\"region\\\" aria-label=\\\"Latest 12 completed sessions. This box scrolls sideways on a narrow screen. The rest of the page does not.\\\"><table class=\\\"c102-ohlc\\\"><caption>Latest 12 completed sessions in the selected range. The bar timestamp is midnight in New York, written in UTC. It is not a settlement time.</caption><thead><tr><th scope=\\\"col\\\">Session date</th><th scope=\\\"col\\\">Open</th><th scope=\\\"col\\\">High</th><th scope=\\\"col\\\">Low</th><th scope=\\\"col\\\">Close</th><th scope=\\\"col\\\">Futures volume</th><th scope=\\\"col\\\">Bar timestamp</th></tr></thead><tbody>\" + rows + \"</tbody></table></div>\";\n  }\n  function bind(rootEl, chart) {\n    var canvas = rootEl.querySelector(\"#c102-canvas\");\n    var live = rootEl.querySelector(\"#c102-live\");\n    var readoutEl = rootEl.querySelector(\"#c102-readout\");\n    var table = rootEl.querySelector(\"#c102-table\");\n    var state = { months: 6, ma20: true, ma50: true, index: -1, user: false };\n    var ro, mq;\n    function spanText() {\n      var bars = windowBars(chart && chart.bars, state.months);\n      if (!bars.length) return \"No completed sessions in this range.\";\n      var name = state.months === 12 ? \"1 year\" : state.months + \" months\";\n      return name + \" \\u00b7 \" + bars[0].sessionDate + \" to \" + bars[bars.length - 1].sessionDate + \" \\u00b7 \" + bars.length + \" completed sessions\";\n    }\n    function paint() {\n      draw(canvas, chart, state);\n      var span = rootEl.querySelector(\"#c102-span\");\n      if (span) span.textContent = spanText();\n      if (canvas && state._bars && state._bars.length) {\n        canvas.setAttribute(\"data-c102-from\", state._bars[0].sessionDate);\n        canvas.setAttribute(\"data-c102-to\", state._bars[state._bars.length - 1].sessionDate);\n      }\n    }\n    function select(i, fromUser) {\n      var bars = state._bars || [];\n      if (!bars.length) return;\n      if (i < 0) i = 0;\n      if (i >= bars.length) i = bars.length - 1;\n      state.index = i;\n      paint();\n      var text = readout(chart, bars[i]);\n      if (readoutEl) readoutEl.textContent = text;\n      if (fromUser && live) live.textContent = text;\n    }\n    rootEl.querySelectorAll(\"[data-c102-months]\").forEach(function (btn) {\n      btn.addEventListener(\"click\", function () {\n        state.months = Number(btn.getAttribute(\"data-c102-months\")) || 6;\n        rootEl.querySelectorAll(\"[data-c102-months]\").forEach(function (b) { b.setAttribute(\"aria-pressed\", b === btn ? \"true\" : \"false\"); });\n        paint();\n        var bars = state._bars || [];\n        if (bars.length) select(bars.length - 1, false);\n      });\n    });\n    rootEl.querySelectorAll(\"[data-c102-ma]\").forEach(function (btn) {\n      btn.addEventListener(\"click\", function () {\n        var k = btn.getAttribute(\"data-c102-ma\") === \"50\" ? \"ma50\" : \"ma20\";\n        state[k] = !state[k];\n        btn.setAttribute(\"aria-pressed\", state[k] ? \"true\" : \"false\");\n        paint();\n      });\n    });\n    var tableBtn = rootEl.querySelector(\"#c102-table-btn\");\n    if (tableBtn && table) {\n      tableBtn.addEventListener(\"click\", function () {\n        var open = table.hasAttribute(\"hidden\");\n        if (open) { table.innerHTML = tableHtml(windowBars(chart && chart.bars, state.months), chart); table.removeAttribute(\"hidden\"); }\n        else table.setAttribute(\"hidden\", \"\");\n        tableBtn.setAttribute(\"aria-expanded\", open ? \"true\" : \"false\");\n      });\n    }\n    if (canvas) {\n      canvas.addEventListener(\"keydown\", function (e) {\n        var bars = state._bars || [];\n        if (e.key !== \"ArrowLeft\" && e.key !== \"ArrowRight\" && e.key !== \"Home\" && e.key !== \"End\") return;\n        e.preventDefault();\n        var i = state.index < 0 ? bars.length - 1 : state.index;\n        if (e.key === \"ArrowLeft\") i -= 1;\n        if (e.key === \"ArrowRight\") i += 1;\n        if (e.key === \"Home\") i = 0;\n        if (e.key === \"End\") i = bars.length - 1;\n        select(i, true);\n      });\n      canvas.addEventListener(\"pointerdown\", function (e) {\n        var rect = canvas.getBoundingClientRect();\n        var x = e.clientX - rect.left;\n        var g = state._geom;\n        if (!g || !state._bars) return;\n        var i = Math.floor((x - g.padL) / g.slot);\n        select(i, true);\n      });\n    }\n    if (typeof ResizeObserver === \"function\" && canvas) {\n      ro = new ResizeObserver(function () { paint(); });\n      ro.observe(canvas);\n    }\n    var mo;\n    if (typeof MutationObserver === \"function\") {\n      mo = new MutationObserver(function () { paint(); });\n      mo.observe(document.documentElement, { attributes: true, attributeFilter: [\"class\", \"data-theme\"] });\n    }\n    if (window.matchMedia) {\n      try {\n        mq = window.matchMedia(\"(prefers-color-scheme: dark)\");\n        var onMq = function () { paint(); };\n        if (mq.addEventListener) mq.addEventListener(\"change\", onMq);\n        else if (mq.addListener) mq.addListener(onMq);\n      } catch (e) {}\n    }\n    paint();\n    if (state._bars && state._bars.length) select(state._bars.length - 1, false);\n    rootEl._c102Cleanup = function () {\n      try { if (ro) ro.disconnect(); } catch (e) {}\n      try { if (mo) mo.disconnect(); } catch (e) {}\n    };\n    window.addEventListener(\"pagehide\", function () { if (rootEl._c102Cleanup) rootEl._c102Cleanup(); }, { once: true });\n  }\n  function mount(el, opts) {\n    opts = opts || {};\n    if (!el) return;\n    var ctrl = typeof AbortController === \"function\" ? new AbortController() : null;\n    window.addEventListener(\"pagehide\", function () { if (ctrl) ctrl.abort(); }, { once: true });\n    document.addEventListener(\"visibilitychange\", function () {\n      if (document.visibilityState === \"hidden\" && ctrl) ctrl.abort();\n    });\n    function fail(message) {\n      el.innerHTML = render({ title: \"Terminal\", generatedAtUtc: new Date().toISOString(), note: \"Gold is priced in dollars and pays no interest, so the dollar, US yields, volatility and futures positioning are the readings usually set beside it. Nothing here is a forecast or a recommendation.\", spot: { status: \"unavailable\", message: message }, spotChange: { status: \"unavailable\", message: message }, dollar: { status: \"unavailable\", message: message }, nominal: { status: \"unavailable\", message: message }, realMarket: { status: \"unavailable\", message: message }, realOfficial: { status: \"unavailable\", message: message }, nominalOfficial: { status: \"unavailable\", message: message }, vix: { status: \"unavailable\", message: message }, ratio: { status: \"unavailable\", message: message }, positioning: { status: \"unavailable\", message: message }, events: { status: \"unavailable\", message: message } }, { status: \"unavailable\", message: message });\n      el.setAttribute(\"aria-busy\", \"false\");\n    }\n    if (opts.model || opts.chart) {\n      el.innerHTML = render(opts.model || {}, opts.chart || null);\n      el.setAttribute(\"aria-busy\", \"false\");\n      bind(el, opts.chart || {});\n      return;\n    }\n    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); fail(\"The readings did not arrive in time. No number was filled in.\"); }, 12000);\n    function pull(attempt) {\n      Promise.all([\n        fetch(\"/api/c102/terminal\", { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: \"application/json\" } }).then(function (r) { if (!r.ok) throw new Error(\"http\"); return r.json(); }),\n        fetch(\"/api/c102/chart\", { signal: ctrl ? ctrl.signal : undefined, headers: { Accept: \"application/json\" } }).then(function (r) { if (!r.ok) throw new Error(\"http\"); return r.json(); })\n      ]).then(function (pair) {\n        clearTimeout(timer);\n        if (el._c102Cleanup) el._c102Cleanup();\n        el.innerHTML = render(pair[0], pair[1]);\n        el.setAttribute(\"aria-busy\", \"false\");\n        bind(el, pair[1]);\n        var cold = (pair[0] && pair[0].cacheState === \"cold\") || (pair[1] && pair[1].cacheState === \"cold\");\n        if (attempt === 0 && cold) setTimeout(function () { if (ctrl && ctrl.signal && ctrl.signal.aborted) return; pull(1); }, 1500);\n      }).catch(function () {\n        clearTimeout(timer);\n        if (el.getAttribute(\"aria-busy\") === \"false\" && el.querySelector(\".c102\")) return;\n        fail(\"The readings did not load. No number was filled in.\");\n      });\n    }\n    pull(0);\n  }\n  root.c102ui = { render: render, mount: mount, draw: draw, readout: readout, windowBars: windowBars, tableHtml: tableHtml, barStamp: barStamp };\n})(typeof globalThis !== \"undefined\" ? globalThis : this);\n";
  if (typeof globalThis !== "undefined") globalThis.c102 = c102api;
  if (!globalThis.C102_NO_INSTALL) c102api.c102Install();
})();
