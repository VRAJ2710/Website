"use strict";
// chat103 CPI day. Pure logic plus c103Install, which is appended onto the live chat102r4 server.
// Request handlers do not wait on BLS or Yahoo. Figures come from a stored release or say "not loaded yet".

const C103_UA = "The Dispatch Market research (https://thedispatch.uk)";
const C103_BLS = "https://api.bls.gov/publicAPI/v2/timeseries/data/";
const C103_ICS = "https://www.bls.gov/schedule/news_release/bls.ics";
const C103_HTML = "https://www.bls.gov/schedule/news_release/cpi.htm";
const C103_RI = "https://www.bls.gov/news.release/cpi.t01.htm";
const C103_RI_HOME = "https://www.bls.gov/cpi/tables/relative-importance/";
const C103_GOLD_LABEL = "Gold futures (COMEX, front month), Yahoo Finance delayed";
const C103_CONTRIB_LABEL = "approx. contribution, our calculation from BLS data";
const C103_SOURCE = "Source: U.S. Bureau of Labor Statistics";
const C103_RECORD_FROM = "2026-12-10";
const C103_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const C103_MON = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

// Item codes checked against download.bls.gov cu.item. Ids except SAR returned M09 2026 on 10 Nov 2026.
const C103_CATALOG = [
  ["headline", "All items", "CUSR0000SA0", "CUUR0000SA0", "All items", "The broad US city CPI for all urban consumers. The month move takes out the usual seasonal swing. The year move does not.", true],
  ["core", "All items less food and energy", "CUSR0000SA0L1E", "CUUR0000SA0L1E", "All items less food and energy", "Food and energy jump around. Leaving them out shows the slower part of the basket.", true],
  ["food", "Food", "CUSR0000SAF1", "CUUR0000SAF1", "Food", "Groceries and meals out. A large food move can shift the headline without saying much about other prices.", false],
  ["foodHome", "Food at home", "CUSR0000SAF11", "CUUR0000SAF11", "Food at home", "Groceries. This is the part of food households buy in shops.", false],
  ["foodAway", "Food away from home", "CUSR0000SEFV", "CUUR0000SEFV", "Food away from home", "Meals out. BLS often does not seasonally adjust this line.", false],
  ["energy", "Energy", "CUSR0000SA0E", "CUUR0000SA0E", "Energy", "Petrol, heating and electricity. Energy is a small weight that can still dominate a single month.", false],
  ["energyComm", "Energy commodities", "CUSR0000SACE", "CUUR0000SACE", "Energy commodities", "Fuels bought as goods, including motor fuel.", false],
  ["energySvc", "Energy services", "CUSR0000SEHF", "CUUR0000SEHF", "Energy services", "Electricity and piped gas.", false],
  ["gasoline", "Gasoline (all types)", "CUSR0000SETB01", "CUUR0000SETB01", "Gasoline (all types)", "Pump prices. In the September 2026 release this was more than half of the monthly headline move.", false],
  ["shelter", "Shelter", "CUSR0000SAH1", "CUUR0000SAH1", "Shelter", "The largest weight in the basket, so a small shelter move can decide the headline.", false],
  ["rent", "Rent of primary residence", "CUSR0000SEHA", "CUUR0000SEHA", "Rent of primary residence", "Rent that tenants actually pay. It moves more slowly than house prices.", false],
  ["oer", "Owners' equivalent rent of residences", "CUSR0000SEHC", "CUUR0000SEHC", "Owners' equivalent rent of residences", "What BLS uses instead of house prices: the rent an owner would pay to live in their own home.", false],
  ["apparel", "Apparel", "CUSR0000SAA", "CUUR0000SAA", "Apparel", "Clothing. It is seasonal, which is why the month figure uses the adjusted series.", false],
  ["newVehicles", "New vehicles", "CUSR0000SETA01", "CUUR0000SETA01", "New vehicles", "New cars and trucks. A guide to goods prices outside food and energy.", false],
  ["usedVehicles", "Used cars and trucks", "CUSR0000SETA02", "CUUR0000SETA02", "Used cars and trucks", "Used vehicles swing more than most goods lines.", false],
  ["medical", "Medical care", "CUSR0000SAM", "CUUR0000SAM", "", "Doctors, hospitals and medicines together. Table 1 often has no single weight for this total, so the contribution stays unloaded.", false],
  ["medicalComm", "Medical care commodities", "CUSR0000SAM1", "CUUR0000SAM1", "Medical care commodities", "Medicines and medical goods.", false],
  ["medicalSvc", "Medical care services", "CUSR0000SAM2", "CUUR0000SAM2", "Medical care services", "Doctors and hospitals.", false],
  ["transportSvc", "Transportation services", "CUSR0000SAS4", "CUUR0000SAS4", "Transportation services", "Insurance, repairs and fares. Not the price of the vehicle itself.", false],
  ["coreGoods", "Commodities less food and energy commodities", "CUSR0000SACL1E", "CUUR0000SACL1E", "Commodities less food and energy commodities", "Goods with food and energy taken out.", false],
  ["coreSvc", "Services less energy services", "CUSR0000SASLE", "CUUR0000SASLE", "Services less energy services", "Services with energy bills taken out. Shelter sits inside this line.", false],
  ["recreation", "Recreation", "CUSR0000SAR", "CUUR0000SAR", "", "Tickets, kit and other leisure. Included because the news release treats it as a major index.", false]
];

const C103_FALLBACK = [
  { y: 2026, m: 12, d: 10, h: 8, min: 30, source: "labelled-fallback", fallbackLabel: "Labelled fallback. This date was not in the cached BLS schedule." },
  { y: 2027, m: 1, d: 13, h: 8, min: 30, source: "labelled-fallback", fallbackLabel: "Labelled fallback. This date was not in the cached BLS schedule." }
];

const C103_TABLES = ["cpi_releases", "cpi_series_values", "cpi_gold_reactions", "cpi_gold_snapshots", "cpi_notice_dismissals"];

const C103_DDL = [
  `CREATE TABLE IF NOT EXISTS cpi_releases (
    period TEXT PRIMARY KEY,
    release_at TIMESTAMPTZ,
    release_source TEXT NOT NULL,
    reference_label TEXT,
    headline_mom DOUBLE PRECISION,
    headline_yoy DOUBLE PRECISION,
    core_mom DOUBLE PRECISION,
    core_yoy DOUBLE PRECISION,
    bls_fetched_at TIMESTAMPTZ,
    payload JSONB,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`,
  `CREATE TABLE IF NOT EXISTS cpi_series_values (
    series_id TEXT NOT NULL,
    period TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (series_id, period)
  )`,
  `CREATE TABLE IF NOT EXISTS cpi_gold_reactions (
    release_at TIMESTAMPTZ PRIMARY KEY,
    reference_period TEXT,
    anchor_at TIMESTAMPTZ,
    anchor_price DOUBLE PRECISION,
    plus_1h_at TIMESTAMPTZ,
    plus_1h_price DOUBLE PRECISION,
    plus_1h_pct DOUBLE PRECISION,
    plus_1d_session TEXT,
    plus_1d_price DOUBLE PRECISION,
    plus_1d_pct DOUBLE PRECISION,
    plus_5d_session TEXT,
    plus_5d_price DOUBLE PRECISION,
    plus_5d_pct DOUBLE PRECISION,
    hourly_available BOOLEAN NOT NULL DEFAULT FALSE,
    recorded BOOLEAN NOT NULL DEFAULT FALSE,
    hour_label TEXT,
    source_label TEXT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  )`,
  `CREATE TABLE IF NOT EXISTS cpi_gold_snapshots (
    id BIGSERIAL PRIMARY KEY,
    release_at TIMESTAMPTZ NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    window_kind TEXT NOT NULL,
    source_label TEXT NOT NULL,
    UNIQUE (release_at, window_kind, observed_at)
  )`,
  `CREATE TABLE IF NOT EXISTS cpi_notice_dismissals (
    user_id TEXT NOT NULL,
    release_key TEXT NOT NULL,
    dismissed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, release_key)
  )`
];

function c103Esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]));
}

function c103Pad(n) { return String(n).padStart(2, "0"); }

function c103Period(y, m) { return y + "-" + c103Pad(m); }

function c103PeriodLabel(period) {
  const m = /^(\d{4})-(\d{2})$/.exec(String(period || ""));
  if (!m) return "";
  return C103_MONTHS[Number(m[2]) - 1] + " " + m[1];
}

function c103Parts(ms, timeZone) {
  const fmt = new Intl.DateTimeFormat("en-GB", {
    timeZone: timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short"
  });
  const bag = {};
  fmt.formatToParts(new Date(ms)).forEach((p) => { if (p.type !== "literal") bag[p.type] = p.value; });
  return {
    year: Number(bag.year),
    month: Number(bag.month),
    day: Number(bag.day),
    hour: Number(bag.hour),
    minute: Number(bag.minute),
    second: Number(bag.second),
    tzName: bag.timeZoneName || ""
  };
}

function c103OffsetMs(utcMs, timeZone) {
  const p = c103Parts(utcMs, timeZone);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return asUtc - utcMs;
}

function c103ZonedToUtc(y, m, d, h, min, timeZone) {
  let utc = Date.UTC(y, m - 1, d, h, min, 0);
  let off = c103OffsetMs(utc, timeZone);
  utc = Date.UTC(y, m - 1, d, h, min, 0) - off;
  off = c103OffsetMs(utc, timeZone);
  return new Date(Date.UTC(y, m - 1, d, h, min, 0) - off);
}

function c103FormatUk(ms) {
  if (typeof ms !== "number" || !isFinite(ms)) return "";
  const p = c103Parts(ms, "Europe/London");
  const weekday = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date(ms));
  return weekday + ", " + p.day + " " + C103_MONTHS[p.month - 1] + " " + p.year + " at " + c103Pad(p.hour) + ":" + c103Pad(p.minute) + " " + p.tzName;
}

function c103EtDate(ms) {
  const p = c103Parts(ms, "America/New_York");
  return c103Period(p.year, p.month).slice(0, 8) && (p.year + "-" + c103Pad(p.month) + "-" + c103Pad(p.day));
}

function c103Ymd(ms, timeZone) {
  const p = c103Parts(ms, timeZone || "America/New_York");
  return p.year + "-" + c103Pad(p.month) + "-" + c103Pad(p.day);
}

function c103Round1(n) {
  if (typeof n !== "number" || !isFinite(n)) return null;
  const sign = n < 0 ? -1 : 1;
  return sign * Math.round((Math.abs(n) + 1e-10) * 10) / 10;
}

function c103Pct(newer, older) {
  if (typeof newer !== "number" || typeof older !== "number" || !isFinite(newer) || !isFinite(older) || older === 0) return null;
  return (newer / older - 1) * 100;
}

function c103FredMonth(iso) {
  const m = /^(\d{4})-(\d{2})/.exec(String(iso || ""));
  return m ? m[1] + "-" + m[2] : "";
}

function c103ShiftYm(ym, delta) {
  const m = /^(\d{4})-(\d{2})$/.exec(ym || "");
  if (!m) return "";
  let y = Number(m[1]);
  let mo = Number(m[2]) + delta;
  while (mo < 1) { mo += 12; y -= 1; }
  while (mo > 12) { mo -= 12; y += 1; }
  return y + "-" + c103Pad(mo);
}

function c103FredAt(rows, ym) {
  if (!ym) return null;
  const hit = (rows || []).find((row) => row && c103FredMonth(row[0]) === ym && typeof row[1] === "number" && isFinite(row[1]));
  return hit || null;
}

function c103CalendarChange(rows, index, monthsBack) {
  const cur = rows && rows[index];
  if (!cur || typeof cur[1] !== "number" || !isFinite(cur[1])) return null;
  const base = c103FredAt(rows, c103ShiftYm(c103FredMonth(cur[0]), -monthsBack));
  if (!base) return null;
  return c103Pct(cur[1], base[1]);
}

function c103SignedPct(n) {
  const rounded = c103Round1(n);
  if (typeof rounded !== "number") return "";
  if (rounded === 0) return "0.0%";
  return (rounded > 0 ? "+" : "\u2212") + Math.abs(rounded).toFixed(1) + "%";
}

function c103SeriesChange(rows, period, monthsBack) {
  const cur = c103FredAt(rows, period);
  if (!cur) return null;
  const index = (rows || []).indexOf(cur);
  return c103CalendarChange(rows, index, monthsBack);
}

function c103CalendarCpiText(headline, core, nsa, index) {
  const period = c103FredMonth(headline[index][0]);
  const mom = c103Round1(c103CalendarChange(headline, index, 1));
  const coreMom = c103Round1(c103SeriesChange(core, period, 1));
  const yoy = c103Round1(c103SeriesChange(nsa, period, 12));
  if (typeof yoy === "number") return (yoy < 0 ? "\u2212" : "") + Math.abs(yoy).toFixed(1) + "% a year";
  const base = c103ShiftYm(period, -12);
  const gap = base === "2025-10"
    ? "year-on-year not published by BLS (no October 2025 data)"
    : "year-on-year not published by BLS (no " + c103PeriodLabel(base) + " data)";
  const momText = typeof mom === "number" ? c103SignedPct(mom) + " on the month" : "month change not published";
  const coreText = typeof coreMom === "number" ? " (core " + c103SignedPct(coreMom) + ")" : "";
  return momText + coreText + "; " + gap;
}

function c103CalendarCpi(headline, core, nsa) {
  const rows = headline || [];
  const i = rows.length - 1;
  if (i < 0) return null;
  const period = c103FredMonth(rows[i][0]);
  if (!period) return null;
  const prevYm = c103ShiftYm(period, -1);
  const prev = c103FredAt(rows, prevYm);
  const prevIndex = prev ? rows.indexOf(prev) : -1;
  return {
    period: period,
    prevPeriod: prev ? prevYm : "",
    actual: c103CalendarCpiText(rows, core, nsa, i),
    previous: prevIndex >= 0 ? c103CalendarCpiText(rows, core, nsa, prevIndex) : "Not published: no " + c103PeriodLabel(prevYm) + " index",
    how: C103_SOURCE + ". Month change, seasonally adjusted. The year change uses the same month a year earlier and is left unpublished when that index is missing."
  };
}

function c103Contribution(weight, change) {
  if (typeof weight !== "number" || typeof change !== "number" || !isFinite(weight) || !isFinite(change)) return null;
  return (weight / 100) * change;
}

function c103MonNum(name) {
  const key = String(name || "").slice(0, 3).toLowerCase();
  return C103_MON[key] || 0;
}

function c103PrevMonth(y, m) {
  return m === 1 ? { y: y - 1, m: 12 } : { y: y, m: m - 1 };
}

function c103ReleaseInstant(y, m, d, h, min) {
  const when = c103ZonedToUtc(y, m, d, h == null ? 8 : h, min == null ? 30 : min, "America/New_York");
  const et = c103Ymd(when.getTime(), "America/New_York");
  const ref = c103PrevMonth(y, m);
  return {
    y: y, m: m, d: d, h: h == null ? 8 : h, min: min == null ? 30 : min,
    startMs: when.getTime(),
    etDate: et,
    referencePeriod: c103Period(ref.y, ref.m),
    releaseAtUtc: when.toISOString(),
    releaseUk: c103FormatUk(when.getTime())
  };
}

function c103Unfold(text) {
  return String(text || "").replace(/\r\n/g, "\n").replace(/\n[ \t]/g, "");
}

function c103ParseIcs(text) {
  const src = c103Unfold(text);
  const out = [];
  const chunks = src.split("BEGIN:VEVENT");
  for (let i = 1; i < chunks.length; i++) {
    const chunk = chunks[i];
    const summary = (chunk.match(/^SUMMARY:(.*)$/m) || [])[1];
    if (String(summary || "").trim() !== "Consumer Price Index") continue;
    const stamp = chunk.match(/^DTSTART(?:;([^:]+))?:(\d{8}T\d{6})(Z?)/m);
    if (!stamp) continue;
    const params = stamp[1] || "";
    const raw = stamp[2];
    const zulu = stamp[3] === "Z";
    const y = Number(raw.slice(0, 4));
    const m = Number(raw.slice(4, 6));
    const d = Number(raw.slice(6, 8));
    const h = Number(raw.slice(9, 11));
    const min = Number(raw.slice(11, 13));
    let startMs;
    if (zulu) startMs = Date.UTC(y, m - 1, d, h, min, 0);
    else {
      const zone = /TZID=([^;:]+)/.exec(params);
      const tz = zone && /new_york|us-eastern|eastern/i.test(zone[1]) ? "America/New_York" : "America/New_York";
      startMs = c103ZonedToUtc(y, m, d, h, min, tz).getTime();
    }
    const row = c103ReleaseInstant(y, m, d, h, min);
    row.startMs = startMs;
    row.releaseAtUtc = new Date(startMs).toISOString();
    row.releaseUk = c103FormatUk(startMs);
    row.etDate = c103Ymd(startMs, "America/New_York");
    row.source = "bls-ics";
    row.scheduleUrl = C103_ICS;
    out.push(row);
  }
  return out;
}

function c103ParseHtmlSchedule(html) {
  const out = [];
  const rows = String(html || "").match(/<tr[\s\S]*?<\/tr>/gi) || [];
  rows.forEach((row) => {
    const cells = [];
    const re = /<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi;
    let cell;
    while ((cell = re.exec(row))) {
      const text = cell[1].replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
      if (text) cells.push(text);
    }
    if (cells.length < 2) return;
    const ref = /^([A-Za-z]+)\s+(\d{4})$/.exec(cells[0]);
    const rel = /^([A-Za-z]+)\.?\s+(\d{1,2}),\s+(\d{4})$/.exec(cells[1]);
    if (!ref || !rel) return;
    const rm = c103MonNum(ref[1]);
    const relMonth = c103MonNum(rel[1]);
    if (!rm || !relMonth) return;
    let h = 8;
    let min = 30;
    const tm = /(\d{1,2}):(\d{2})\s*(AM|PM)/i.exec(cells[2] || "");
    if (tm) {
      h = Number(tm[1]) % 12;
      if (/pm/i.test(tm[3])) h += 12;
      min = Number(tm[2]);
    } else return;
    const rowOut = c103ReleaseInstant(Number(rel[3]), relMonth, Number(rel[2]), h, min);
    rowOut.referencePeriod = c103Period(Number(ref[2]), rm);
    rowOut.source = "bls-html";
    rowOut.scheduleUrl = C103_HTML;
    out.push(rowOut);
  });
  return out;
}

function c103MergeSchedule(icsEvents, htmlEvents) {
  const byDay = new Map();
  (icsEvents || []).forEach((ev) => { if (ev && ev.etDate) byDay.set(ev.etDate, Object.assign({}, ev)); });
  (htmlEvents || []).forEach((ev) => {
    if (!ev || !ev.etDate) return;
    const cur = byDay.get(ev.etDate);
    if (!cur) byDay.set(ev.etDate, Object.assign({}, ev));
    else if (ev.referencePeriod) cur.referencePeriod = ev.referencePeriod;
  });
  C103_FALLBACK.forEach((fb) => {
    const row = c103ReleaseInstant(fb.y, fb.m, fb.d, fb.h, fb.min);
    row.source = "labelled-fallback";
    row.fallbackLabel = fb.fallbackLabel;
    row.scheduleUrl = C103_HTML;
    if (!byDay.has(row.etDate)) byDay.set(row.etDate, row);
  });
  return Array.from(byDay.values()).sort((a, b) => a.startMs - b.startMs);
}

function c103Countdown(nowMs, events) {
  const next = (events || []).find((ev) => ev.startMs > nowMs);
  if (!next) return null;
  let left = Math.max(0, next.startMs - nowMs);
  const days = Math.floor(left / 86400000);
  left -= days * 86400000;
  const hours = Math.floor(left / 3600000);
  left -= hours * 3600000;
  const minutes = Math.floor(left / 60000);
  const seconds = Math.floor((left - minutes * 60000) / 1000);
  return {
    releaseAtUtc: next.releaseAtUtc,
    releaseUk: next.releaseUk,
    zoneName: c103Parts(next.startMs, "Europe/London").tzName,
    etDate: next.etDate,
    referencePeriod: next.referencePeriod,
    referenceLabel: c103PeriodLabel(next.referencePeriod),
    source: next.source,
    fallbackLabel: next.fallbackLabel || "",
    scheduleUrl: next.scheduleUrl || C103_ICS,
    days: days,
    hours: hours,
    minutes: minutes,
    seconds: seconds,
    what: "Time left until the next US CPI news release.",
    why: "The Bureau of Labor Statistics puts the index out at 08:30 US Eastern. This clock shows that moment in UK time, including GMT or BST."
  };
}

function c103IndexMap(points) {
  const map = new Map();
  (points || []).forEach((p) => {
    if (!p || typeof p.value !== "number" || !isFinite(p.value)) return;
    map.set(p.year + "-" + p.month, p.value);
  });
  return map;
}

function c103ParseBls(payload) {
  const root = payload && typeof payload === "object" ? payload : null;
  if (!root || root.status !== "REQUEST_SUCCEEDED" || !root.Results || !Array.isArray(root.Results.series)) {
    return { ok: false, series: {} };
  }
  const series = {};
  root.Results.series.forEach((s) => {
    const id = s && s.seriesID;
    if (!id || !C103_CATALOG.some((row) => row[2] === id || row[3] === id)) return;
    const points = [];
    (s.data || []).forEach((r) => {
      const per = String(r && r.period || "");
      if (!/^M(0[1-9]|1[0-2])$/.test(per)) return;
      if (r.value == null || r.value === "" || r.value === "-") return;
      const value = Number(r.value);
      if (!isFinite(value)) return;
      points.push({ year: Number(r.year), month: Number(per.slice(1)), value: value });
    });
    series[id] = points;
  });
  return { ok: Object.keys(series).length > 0, series: series };
}

function c103CellText(html) {
  return String(html || "")
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<span[^>]*footnoteRefs[\s\S]*?<\/span>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/g, " ")
    .replace(/\(\d+\)/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function c103ParseRi(html) {
  const rows = [];
  const tr = String(html || "").match(/<tr[\s\S]*?<\/tr>/gi) || [];
  let weightCol = -1;
  let weightId = "";
  let asOf = "";
  const parsed = tr.map((row) => {
    const cells = [];
    const re = /<t[dh]([^>]*)>([\s\S]*?)<\/t[dh]>/gi;
    let m;
    while ((m = re.exec(row))) {
      cells.push({ attrs: m[1] || "", text: c103CellText(m[2]) });
    }
    return cells;
  });
  parsed.forEach((cells) => {
    cells.forEach((cell, i) => {
      if (!/relative/i.test(cell.text) || !/importance/i.test(cell.text)) return;
      weightCol = i;
      const id = /id="([^"]+)"/i.exec(cell.attrs);
      if (id) weightId = id[1];
      const month = cell.text.match(/((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})/i);
      if (month) asOf = month[1].replace(/\s+/g, " ");
    });
  });
  parsed.forEach((cells) => {
    if (!cells.length) return;
    const name = cells[0].text;
    if (!name || /expenditure category|relative importance/i.test(name)) return;
    let weightText = "";
    if (weightId) {
      const hit = cells.find((cell) => new RegExp("headers=\"[^\"]*" + weightId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).test(cell.attrs));
      if (hit) weightText = hit.text.replace(/,/g, "");
    }
    if (!weightText && weightCol >= 0 && cells[weightCol]) weightText = cells[weightCol].text.replace(/,/g, "");
    if (!/^\d+\.\d+$/.test(weightText) || Number(weightText) > 100) return;
    rows.push({ name: name, weight: Number(weightText) });
  });
  const byName = {};
  rows.forEach((r) => { if (byName[r.name] == null) byName[r.name] = r.weight; });
  return {
    ok: rows.length > 0 && weightCol >= 0,
    asOf: asOf,
    weightMonth: asOf,
    byName: byName,
    sourceUrl: C103_RI,
    homeUrl: C103_RI_HOME,
    citation: "Relative importance: U.S. Bureau of Labor Statistics, CPI news release Table 1. " + C103_RI + " Annual tables: " + C103_RI_HOME
  };
}

function c103MonthNameToNum(text) {
  return c103MonNum(String(text || ""));
}

function c103WeightsMatch(weightMonth, latestPeriod) {
  const per = /^(\d{4})-(\d{2})$/.exec(String(latestPeriod || ""));
  const label = String(weightMonth || "").match(/([A-Za-z]+)\.?\s+(\d{4})/);
  if (!per || !label) return false;
  const prev = c103PrevMonth(Number(per[1]), Number(per[2]));
  return c103MonthNameToNum(label[1]) === prev.m && Number(label[2]) === prev.y;
}

function c103IndexGapNote(kind, y, m) {
  const label = C103_MONTHS[m - 1] + " " + y;
  if (y === 2025 && m === 10 && kind === "mom") return "Month-on-month not published: no October 2025 index";
  if (y === 2025 && m === 10 && kind === "yoy") return "Year-on-year not published: BLS has no October 2025 index because of the 2025 US government shutdown.";
  const lead = kind === "yoy" ? "Year-on-year not published: " : "Month change not published: ";
  return lead + "BLS has no " + label + " index.";
}

function c103YoyLabel(y, m) {
  if (y === 2025 && m === 10) return "Not published by BLS (no October 2025 data)";
  return "";
}

const C103_SHUTDOWN_NOTE = "Not collected by BLS (2025 US government shutdown)";

function c103ChangePair(saMap, nsaMap, y, m) {
  const sa = saMap.get(y + "-" + m);
  const nsa = nsaMap.get(y + "-" + m);
  const prev = c103PrevMonth(y, m);
  const saPrev = saMap.get(prev.y + "-" + prev.m);
  const nsaPrevYear = nsaMap.get((y - 1) + "-" + m);
  const mom = c103Pct(sa, saPrev);
  const yoy = c103Pct(nsa, nsaPrevYear);
  return {
    saIndex: typeof sa === "number" ? sa : null,
    nsaIndex: typeof nsa === "number" ? nsa : null,
    mom: mom,
    momRounded: c103Round1(mom),
    momNote: typeof sa === "number" && typeof saPrev !== "number" ? c103IndexGapNote("mom", prev.y, prev.m) : "",
    yoy: yoy,
    yoyRounded: c103Round1(yoy),
    yoyNote: typeof nsa === "number" && typeof nsaPrevYear !== "number" ? c103IndexGapNote("yoy", y - 1, m) : "",
    yoyLabel: typeof nsa === "number" && typeof nsaPrevYear !== "number" ? c103YoyLabel(y - 1, m) : ""
  };
}

function c103BuildMonths(series, ri) {
  const maps = {};
  Object.keys(series || {}).forEach((id) => { maps[id] = c103IndexMap(series[id]); });
  const keys = new Set();
  C103_CATALOG.forEach((row) => {
    const sa = maps[row[2]];
    const nsa = maps[row[3]];
    if (sa) sa.forEach((_, k) => keys.add(k));
    if (nsa) nsa.forEach((_, k) => keys.add(k));
  });
  const months = Array.from(keys).map((k) => {
    const [ys, ms] = k.split("-");
    return { y: Number(ys), m: Number(ms) };
  }).sort((a, b) => a.y === b.y ? a.m - b.m : a.y - b.y);
  return months.map((slot) => {
    const period = c103Period(slot.y, slot.m);
    const cats = C103_CATALOG.map((row) => {
      const pair = c103ChangePair(maps[row[2]] || new Map(), maps[row[3]] || new Map(), slot.y, slot.m);
      const weight = row[4] && ri && ri.byName ? ri.byName[row[4]] : null;
      const weightNum = typeof weight === "number" ? weight : null;
      const weightsOk = !!(ri && c103WeightsMatch(ri.weightMonth || ri.asOf, period));
      return {
        key: row[0],
        name: row[1],
        momSeries: row[2],
        yoySeries: row[3],
        riName: row[4] || "",
        why: row[5],
        free: row[6],
        period: period,
        periodLabel: c103PeriodLabel(period),
        saIndex: pair.saIndex,
        nsaIndex: pair.nsaIndex,
        mom: pair.mom,
        momRounded: pair.momRounded,
        momNote: pair.momNote,
        yoy: pair.yoy,
        yoyRounded: pair.yoyRounded,
        yoyNote: pair.yoyNote,
        yoyLabel: pair.yoyLabel,
        weight: weightNum,
        weightMonth: ri && (ri.weightMonth || ri.asOf) || "",
        weightsMatch: weightsOk,
        contribution: weightsOk && typeof pair.mom === "number" ? c103Contribution(weightNum, pair.mom) : null,
        contributionUnit: "pp",
        contributionLabel: C103_CONTRIB_LABEL,
        contributionNote: !weightsOk ? "The weight month is not the month before this figure. Contributions are not shown." : (typeof pair.mom === "number" ? "" : (pair.momNote || "Month change is not available, so no contribution is calculated.")),
        source: C103_SOURCE
      };
    });
    const headline = cats[0];
    const core = cats[1];
    return { period: period, periodLabel: c103PeriodLabel(period), year: slot.y, month: slot.m, headline: headline, core: core, categories: cats };
  });
}

function c103GoldUrl(interval, range) {
  const id = ["GC", "=F"].join("");
  return "https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(id) + "?range=" + range + "&interval=" + interval;
}

function c103GoldSymbol() { return ["GC", "=F"].join(""); }

function c103ParseYahoo(payload, intervalMs) {
  const result = payload && payload.chart && Array.isArray(payload.chart.result) ? payload.chart.result[0] : null;
  const meta = result && result.meta;
  if (!meta || meta.symbol !== c103GoldSymbol()) return { ok: false, bars: [], message: "The futures feed did not return the front-month contract. No number was filled in." };
  if (meta.instrumentType && meta.instrumentType !== "FUTURE") return { ok: false, bars: [], message: "The feed was not a futures contract. No number was filled in." };
  const name = String(meta.shortName || meta.longName || "");
  if (!/gold/i.test(name)) return { ok: false, bars: [], message: "The futures name was not gold. No number was filled in." };
  const quote = (result.indicators && result.indicators.quote && result.indicators.quote[0]) || {};
  const ts = Array.isArray(result.timestamp) ? result.timestamp : [];
  const tz = meta.exchangeTimezoneName || "America/New_York";
  const bars = [];
  for (let i = 0; i < ts.length; i++) {
    const close = quote.close && quote.close[i];
    const open = quote.open && quote.open[i];
    if (typeof ts[i] !== "number" || typeof close !== "number" || !isFinite(close)) continue;
    const startMs = ts[i] * 1000;
    bars.push({
      startMs: startMs,
      endMs: startMs + intervalMs,
      close: close,
      open: typeof open === "number" && isFinite(open) ? open : null,
      timeUtc: new Date(startMs).toISOString(),
      sessionDate: c103Ymd(startMs, tz)
    });
  }
  bars.sort((a, b) => a.startMs - b.startMs);
  return { ok: bars.length > 0, bars: bars, timezone: tz, message: bars.length ? "" : "The futures feed returned no completed bars. No number was filled in." };
}

function c103EtClock(ms) {
  const p = c103Parts(ms, "America/New_York");
  return c103Pad(p.hour) + ":" + c103Pad(p.minute);
}

function c103CompletedBars(bars, nowMs, daily) {
  const today = c103Ymd(nowMs, "America/New_York");
  return (bars || []).filter((b) => {
    if (!b || typeof b.close !== "number" || typeof b.endMs !== "number") return false;
    if (b.endMs > nowMs) return false;
    if (daily && b.sessionDate && b.sessionDate >= today) return false;
    return true;
  });
}

function c103GoldReaction(release, hourlyBars, dailyBars, nowMs) {
  const row = {
    releaseAtUtc: release.releaseAtUtc,
    releaseUk: release.releaseUk,
    referencePeriod: release.referencePeriod,
    referenceLabel: c103PeriodLabel(release.referencePeriod),
    hourlyAvailable: false,
    hourLabel: "",
    anchorUk: "",
    dayAnchorLabel: "",
    plus1hPct: null,
    plus1dSession: null,
    plus1dPrice: null,
    plus1dPct: null,
    plus5dSession: null,
    plus5dPrice: null,
    plus5dPct: null,
    recorded: false,
    rollNote: "",
    sourceLabel: C103_GOLD_LABEL,
    what: "How the front-month gold future moved after this release.",
    why: "Past releases only. This is the move that already happened. It is not a view on the next release."
  };
  const hourly = release && release.dailyOnly ? [] : c103CompletedBars(hourlyBars, nowMs || release.startMs, false);
  const before = hourly.filter((b) => b.endMs <= release.startMs && release.startMs - b.endMs <= 3 * 3600000);
  const anchor = before.length ? before[before.length - 1] : null;
  const after = anchor ? hourly.filter((b) => b.endMs >= release.startMs + 3600000 && b.startMs >= release.startMs && b.endMs - (release.startMs + 3600000) <= 2.5 * 3600000) : [];
  const plus = after.length ? after[0] : null;
  if (anchor && plus) {
    row.hourlyAvailable = true;
    row.hourAnchorPrice = anchor.close;
    row.anchorPrice = anchor.close;
    row.plus1hPrice = plus.close;
    row.plus1hPct = c103Pct(plus.close, anchor.close);
    row.hourLabel = c103EtClock(anchor.endMs) + "\u2192" + c103EtClock(plus.endMs) + " ET (hourly bars)";
    row.anchorUk = c103FormatUk(anchor.endMs);
  }
  const daily = c103CompletedBars(dailyBars, nowMs || release.startMs, true);
  const prior = daily.filter((b) => b.sessionDate < release.etDate);
  const dayAnchor = prior.length ? prior[prior.length - 1] : null;
  if (dayAnchor) {
    row.dayAnchorLabel = "prior session close";
    row.dayAnchorUk = dayAnchor.sessionDate;
    row.dayAnchorPrice = dayAnchor.close;
    const later = daily.filter((b) => b.sessionDate > dayAnchor.sessionDate);
    const d1 = later[0];
    const d5 = later[4];
    if (d1) {
      row.plus1dSession = d1.sessionDate;
      row.plus1dPrice = d1.close;
      row.plus1dPct = c103Pct(d1.close, dayAnchor.close);
      if (c103RollJump(dayAnchor, d1)) row.rollNote = "This window crosses a jump between sessions. It may be a contract roll on the continuous series.";
    }
    if (d5) {
      row.plus5dSession = d5.sessionDate;
      row.plus5dPrice = d5.close;
      row.plus5dPct = c103Pct(d5.close, dayAnchor.close);
    }
  }
  return row;
}

function c103RollJump(prev, next) {
  if (!prev || !next || typeof prev.close !== "number" || typeof next.open !== "number" || prev.close === 0) return false;
  const gap = Math.abs(next.open / prev.close - 1);
  return gap > 0.015;
}

function c103MergeGold(computed, stored) {
  const by = new Map();
  (stored || []).forEach((row) => { if (row && row.releaseAtUtc) by.set(row.releaseAtUtc, Object.assign({}, row)); });
  (computed || []).forEach((row) => {
    if (!row || !row.releaseAtUtc) return;
    const old = by.get(row.releaseAtUtc);
    const next = Object.assign({}, row);
    if (old) {
      if (next.plus1hPct == null && old.plus1hPct != null) next.plus1hPct = old.plus1hPct;
      if (!next.hourlyAvailable && old.hourlyAvailable) {
        next.hourlyAvailable = true;
        if (/Daily windows only/.test(next.hourMessage || "")) next.hourMessage = old.hourMessage || "";
      }
      if (!next.hourLabel && old.hourLabel) next.hourLabel = old.hourLabel;
    }
    by.set(row.releaseAtUtc, next);
  });
  return Array.from(by.values()).sort((a, b) => String(a.releaseAtUtc) < String(b.releaseAtUtc) ? 1 : -1);
}

function c103ApplySnapshots(row, snaps) {
  const mine = (snaps || []).filter((s) => s && s.releaseAtUtc === row.releaseAtUtc);
  const pick = (kind) => mine.filter((s) => s.windowKind === kind).sort((a, b) => String(a.observedAtUtc) < String(b.observedAtUtc) ? 1 : -1)[0];
  const pre = pick("pre");
  const target = Date.parse(row.releaseAtUtc) + 60 * 60 * 1000;
  const post = mine.filter((s) => s.windowKind === "plus_1h" || s.windowKind === "post").sort((a, b) => Math.abs(Date.parse(a.observedAtUtc) - target) - Math.abs(Date.parse(b.observedAtUtc) - target))[0];
  if (pre && typeof pre.price === "number") {
    row.recordedPreUk = c103FormatUk(Date.parse(pre.observedAtUtc));
    row.recordedPrePrice = pre.price;
  }
  if (post && typeof post.price === "number") {
    row.recordedPostUk = c103FormatUk(Date.parse(post.observedAtUtc));
    row.recordedPostPrice = post.price;
  }
  if (pre && post && typeof pre.price === "number" && typeof post.price === "number") {
    row.plus1hPct = c103Pct(post.price, pre.price);
    row.hourlyAvailable = true;
    row.hourLabel = (row.recordedPreUk || "pre-release") + " \u2192 " + (row.recordedPostUk || "after the release");
    row.anchorUk = row.recordedPreUk || row.anchorUk;
    row.recorded = true;
    row.recordedNote = "Recorded by The Dispatch from that delayed feed at the times shown.";
  }
  return row;
}

function c103SnapshotDecision(nowMs, events) {
  if (c103Ymd(nowMs, "America/New_York") < C103_RECORD_FROM) return null;
  const et = c103Parts(nowMs, "America/New_York");
  for (const ev of events || []) {
    if (!ev || ev.etDate < C103_RECORD_FROM) continue;
    if (nowMs >= ev.startMs - 20 * 60000 && nowMs < ev.startMs - 60000) return { releaseAtUtc: ev.releaseAtUtc, windowKind: "pre" };
    if (nowMs >= ev.startMs + 60 * 60000 && nowMs < ev.startMs + 75 * 60000) return { releaseAtUtc: ev.releaseAtUtc, windowKind: "plus_1h" };
    const day = et.year + "-" + c103Pad(et.month) + "-" + c103Pad(et.day);
    const mins = et.hour * 60 + et.minute;
    if (day >= ev.etDate && mins >= 16 * 60 + 45 && mins <= 17 * 60 + 15) {
      const end = ev.startMs + 8 * 86400000;
      if (nowMs <= end && et.hour !== 0) return { releaseAtUtc: ev.releaseAtUtc, windowKind: "session" };
    }
  }
  return null;
}

function c103LatestFigure(month, key) {
  if (!month) return null;
  const row = key === "core" ? month.core : month.headline;
  if (!row || (row.saIndex == null && row.nsaIndex == null)) return null;
  return {
    period: month.period,
    periodLabel: month.periodLabel,
    name: row.name,
    what: key === "core" ? "US CPI-U, all items less food and energy." : "US CPI-U, all items.",
    why: row.why,
    momSeries: row.momSeries,
    yoySeries: row.yoySeries,
    saIndex: row.saIndex,
    nsaIndex: row.nsaIndex,
    mom: row.mom,
    momRounded: row.momRounded,
    yoy: row.yoy,
    yoyRounded: row.yoyRounded,
    yoyNote: row.yoyNote || "",
    yoyLabel: row.yoyLabel || "",
    momNote: row.momNote || "",
    source: C103_SOURCE
  };
}

function c103SeriesGood(points) {
  return Array.isArray(points) && points.some((p) => p && typeof p.value === "number" && isFinite(p.value));
}

function c103SqlNum(value) {
  if (typeof value === "number") return isFinite(value) ? value : null;
  if (value == null) return null;
  const text = String(value).trim();
  if (!text) return null;
  const n = Number(text);
  return isFinite(n) ? n : null;
}

function c103NoteWhen(value) {
  const ms = typeof value === "number" ? value : Date.parse(value);
  if (!isFinite(ms)) return "";
  const p = c103Parts(ms, "Europe/London");
  const weekday = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", weekday: "short" }).format(new Date(ms));
  const mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][p.month - 1];
  return weekday + " " + p.day + " " + mon + ", " + c103Pad(p.hour) + ":" + c103Pad(p.minute) + " UK";
}

function c103CarryNote(when) {
  const shown = c103NoteWhen(when);
  return "Stored reading from " + (shown || "the last good response") + ". It was not refreshed. It is not a new print.";
}

function c103NewestPeriod(points) {
  let best = "";
  (points || []).forEach((p) => {
    if (!p || typeof p.value !== "number" || !isFinite(p.value)) return;
    const key = c103Period(p.year, p.month);
    if (key > best) best = key;
  });
  return best;
}

function c103UnionPoints(prev, next) {
  const map = new Map();
  (prev || []).forEach((p) => {
    if (p && typeof p.value === "number" && isFinite(p.value)) map.set(c103Period(p.year, p.month), p);
  });
  const prevNewest = c103NewestPeriod(prev);
  const nextNewest = c103NewestPeriod(next);
  const older = !!(prevNewest && nextNewest && nextNewest < prevNewest);
  (next || []).forEach((p) => {
    if (!p || typeof p.value !== "number" || !isFinite(p.value)) return;
    map.set(c103Period(p.year, p.month), p);
  });
  return { points: Array.from(map.values()), older: older };
}

function c103PickSeries(nextMap, prevMap) {
  const out = {};
  const carried = {};
  const ids = new Set(Object.keys(prevMap || {}).concat(Object.keys(nextMap || {})));
  ids.forEach((id) => {
    const next = nextMap && nextMap[id];
    const prev = prevMap && prevMap[id];
    if (c103SeriesGood(next)) {
      const union = c103UnionPoints(prev, next);
      out[id] = union.points;
      if (union.older) carried[id] = true;
    } else if (c103SeriesGood(prev)) {
      out[id] = prev;
      carried[id] = true;
    }
  });
  return { series: out, carried: carried };
}

function c103ShutdownRow() {
  return {
    period: "2025-10",
    periodLabel: "October 2025",
    headlineYoy: null,
    coreYoy: null,
    headlineMom: null,
    coreMom: null,
    note: C103_SHUTDOWN_NOTE,
    headlineYoyNote: C103_SHUTDOWN_NOTE,
    coreYoyNote: C103_SHUTDOWN_NOTE,
    headlineYoyDetail: C103_SHUTDOWN_NOTE,
    coreYoyDetail: C103_SHUTDOWN_NOTE,
    headlineMomNote: C103_SHUTDOWN_NOTE,
    coreMomNote: C103_SHUTDOWN_NOTE,
    gap: true
  };
}

function c103WithShutdownGap(rows) {
  const list = rows || [];
  if (!list.some((row) => row && row.period < "2025-10") || !list.some((row) => row && row.period > "2025-10")) return list;
  if (list.some((row) => row && row.period === "2025-10")) return list;
  return list.concat([c103ShutdownRow()]).sort((a, b) => a.period < b.period ? -1 : a.period > b.period ? 1 : 0).slice(-24);
}

function c103WithShutdownArchive(rows) {
  const list = rows || [];
  if (!list.some((row) => row && row.period < "2025-10") || !list.some((row) => row && row.period > "2025-10")) return list;
  if (list.some((row) => row && row.period === "2025-10")) return list;
  const blank = {
    momRounded: null,
    yoyRounded: null,
    momNote: C103_SHUTDOWN_NOTE,
    yoyNote: C103_SHUTDOWN_NOTE,
    yoyLabel: "Not published by BLS (no October 2025 data)"
  };
  return list.concat([{
    period: "2025-10",
    periodLabel: "October 2025",
    headline: Object.assign({}, blank),
    core: Object.assign({}, blank)
  }]).sort((a, b) => a.period < b.period ? 1 : a.period > b.period ? -1 : 0);
}

function c103Compose(parts, nowMs) {
  const prevMap = (parts && parts.previousSeries) || {};
  const nextMap = parts && parts.series && parts.series.ok ? parts.series.series : {};
  const picked = c103PickSeries(nextMap, prevMap);
  const series = Object.keys(picked.series).length ? picked.series : null;
  const carried = picked.carried;
  const riFresh = parts && parts.ri && parts.ri.ok;
  const ri = riFresh ? parts.ri : (parts && parts.previousRi && parts.previousRi.byName ? parts.previousRi : null);
  const riCarried = !riFresh && !!(ri && ri.byName);
  const kept = parts && parts.previousEvents || [];
  const icsFresh = parts && parts.icsOk && Array.isArray(parts.ics) && parts.ics.length > 0;
  const htmlFresh = parts && parts.htmlOk && Array.isArray(parts.html) && parts.html.length > 0;
  const archiveFresh = parts && parts.archiveOk && Array.isArray(parts.archive) && parts.archive.length > 0;
  const icsIn = icsFresh ? parts.ics : kept.filter((ev) => ev && ev.source === "bls-ics");
  const htmlIn = htmlFresh ? parts.html : kept.filter((ev) => ev && ev.source === "bls-html");
  const archiveIn = archiveFresh ? parts.archive : kept.filter((ev) => ev && ev.source === "bls-archive");
  const icsCarried = !icsFresh && icsIn.length > 0;
  const htmlCarried = !htmlFresh && htmlIn.length > 0;
  const primary = c103MergeSchedule(icsIn, htmlIn);
  const haveDay = new Set(primary.map((ev) => ev.etDate));
  const events = primary.concat(archiveIn.filter((ev) => ev && ev.etDate && !haveDay.has(ev.etDate))).sort((a, b) => a.startMs - b.startMs);
  const usedEvents = events;
  const scheduleFromFetch = (parts && parts.icsOk) || (parts && parts.htmlOk);
  const prevBars = (parts && parts.feedBars) || {};
  const hourlyFresh = parts && Array.isArray(parts.hourly) && parts.hourly.length > 0;
  const dailyFresh = parts && Array.isArray(parts.daily) && parts.daily.length > 0;
  const hourly = hourlyFresh ? parts.hourly : (prevBars.hourly || []);
  const daily = dailyFresh ? parts.daily : (prevBars.daily || []);
  const hourlyCarried = !hourlyFresh && hourly.length > 0;
  const dailyCarried = !dailyFresh && daily.length > 0;
  const months = series ? c103BuildMonths(series, ri) : [];
  const latest = months.length ? months[months.length - 1] : null;
  const trendMonths = months.filter((row) => row.headline && (row.headline.nsaIndex != null || row.headline.saIndex != null));
  const trend = c103WithShutdownGap(trendMonths.slice(-24).map((row) => ({
    period: row.period,
    periodLabel: row.periodLabel,
    headlineYoy: row.headline.yoyRounded,
    coreYoy: row.core && typeof row.core.yoyRounded === "number" ? row.core.yoyRounded : null,
    headlineYoyNote: row.headline.yoyLabel || row.headline.yoyNote || "",
    headlineYoyDetail: row.headline.yoyNote || "",
    coreYoyNote: row.core && (row.core.yoyLabel || row.core.yoyNote) || "",
    coreYoyDetail: row.core && row.core.yoyNote || "",
    headlineMom: row.headline.momRounded,
    coreMom: row.core ? row.core.momRounded : null,
    headlineMomNote: row.headline.momNote || "",
    coreMomNote: row.core && row.core.momNote || ""
  })));
  const archive = c103WithShutdownArchive(months.slice().reverse().map((row) => ({
    period: row.period,
    periodLabel: row.periodLabel,
    headline: c103LatestFigure(row, "headline"),
    core: c103LatestFigure(row, "core")
  })).filter((row) => row.headline || row.core));
  const past = usedEvents.filter((ev) => ev.startMs <= nowMs);
  const goldComputed = (hourly.length || daily.length)
    ? past.slice().reverse().map((ev) => {
      const useHourly = ev && ev.dailyOnly ? [] : hourly;
      const row = c103ApplySnapshots(c103GoldReaction(ev, useHourly, daily, nowMs), parts && parts.snapshots);
      if (ev && ev.dailyOnly) row.hourMessage = "Daily windows only for this older release.";
      else if (!useHourly.length) row.hourMessage = "No number was filled in.";
      else if (hourlyCarried && row.hourlyAvailable) row.hourMessage = c103CarryNote(prevBars.hourlyAt || "");
      else if (!row.hourlyAvailable) row.hourMessage = "Hourly bars do not cover this release.";
      if (!daily.length) row.dayMessage = "No number was filled in.";
      else if (dailyCarried && (row.plus1dPct != null || row.plus5dPct != null)) row.dayMessage = c103CarryNote(prevBars.dailyAt || "");
      return row;
    })
    : [];
  const gold = c103MergeGold(goldComputed, parts && parts.storedGold);
  const countdown = c103Countdown(nowMs, usedEvents);
  const blsWhen = (parts && parts.feedTimes && parts.feedTimes.bls) || (parts && parts.storedFetchedAt) || "";
  const headlineCarried = !!(carried.CUSR0000SA0 || carried.CUUR0000SA0);
  const coreCarried = !!(carried.CUSR0000SA0L1E || carried.CUUR0000SA0L1E);
  let statusNote = "";
  if (!latest) statusNote = "not loaded yet";
  else if (headlineCarried) statusNote = c103CarryNote(blsWhen);
  const candidate = latest && past.some((ev) => ev.referencePeriod === latest.period && ev.startMs <= nowMs);
  const match = candidate ? past.filter((ev) => ev.referencePeriod === latest.period).slice(-1)[0] : null;
  return {
    ok: !!latest || !!countdown,
    generatedAtUtc: new Date(nowMs).toISOString(),
    generatedAtUk: c103FormatUk(nowMs),
    source: C103_SOURCE,
    statusNote: statusNote,
    scheduleSource: scheduleFromFetch ? "bls" : (usedEvents.length ? "stored" : ""),
    countdown: countdown,
    latest: latest ? {
      period: latest.period,
      periodLabel: latest.periodLabel,
      releaseUk: match ? match.releaseUk : "",
      releaseAtUtc: match ? match.releaseAtUtc : "",
      headline: Object.assign(c103LatestFigure(latest, "headline") || {}, headlineCarried ? { message: c103CarryNote(blsWhen), carried: true } : {}),
      core: Object.assign(c103LatestFigure(latest, "core") || {}, coreCarried ? { message: c103CarryNote(blsWhen), carried: true } : {}),
      fetchedAt: (headlineCarried || coreCarried) && blsWhen ? blsWhen : (parts && parts.fetchedAt || new Date(nowMs).toISOString()),
      releaseSource: match ? match.source : ""
    } : null,
    trend: trend,
    archive: archive,
    categories: latest ? latest.categories.filter((row) => !row.free) : [],
    contributions: latest ? latest.categories.filter((row) => !row.free).map((row) => ({
      key: row.key,
      name: row.name,
      weight: row.weight,
      momRounded: row.momRounded,
      contribution: row.contribution,
      label: C103_CONTRIB_LABEL
    })) : [],
    gold: gold,
    relativeImportance: ri && ri.ok ? { asOf: ri.asOf, citation: ri.citation, sourceUrl: ri.sourceUrl, homeUrl: ri.homeUrl } : (ri ? { asOf: ri.asOf || "", citation: ri.citation || "", sourceUrl: C103_RI, homeUrl: C103_RI_HOME, missing: !ri.ok } : null),
    contributionLabel: C103_CONTRIB_LABEL,
    goldLabel: C103_GOLD_LABEL,
    seriesFresh: !!(parts && parts.series && parts.series.ok) && !headlineCarried && !coreCarried,
    noticeCandidate: match && latest ? { releaseKey: match.releaseAtUtc, periodLabel: latest.periodLabel, referencePeriod: latest.period } : null,
    previousSeries: series,
    previousRi: ri,
    previousEvents: usedEvents,
    previousMonths: months,
    previousGold: gold,
    feedBars: {
      hourly: hourly,
      daily: daily,
      hourlyAt: hourlyFresh ? (parts.fetchedAt || new Date(nowMs).toISOString()) : (prevBars.hourlyAt || ""),
      dailyAt: dailyFresh ? (parts.fetchedAt || new Date(nowMs).toISOString()) : (prevBars.dailyAt || "")
    },
    feedTimes: {
      bls: (parts && parts.series && parts.series.ok && !headlineCarried) ? (parts.fetchedAt || new Date(nowMs).toISOString()) : blsWhen,
      riCarried: riCarried,
      icsCarried: icsCarried,
      htmlCarried: htmlCarried,
      hourlyCarried: hourlyCarried,
      dailyCarried: dailyCarried
    }
  };
}

function c103Cold(nowMs) {
  const now = nowMs || Date.now();
  return {
    ok: false,
    cacheState: "cold",
    generatedAtUtc: new Date(now).toISOString(),
    generatedAtUk: c103FormatUk(now),
    source: C103_SOURCE,
    statusNote: "not loaded yet",
    cacheNote: "No stored release yet. The feeds are being asked in the background. No number was filled in.",
    countdown: null,
    latest: null,
    trend: [],
    archive: [],
    scheduleSource: ""
  };
}

function c103WorthStoring(body) {
  if (!body || body.cacheState === "cold") return false;
  if (body.latest && body.latest.headline && typeof body.latest.headline.saIndex === "number") return true;
  if (body.countdown && body.countdown.releaseAtUtc) return true;
  return false;
}

function c103WithCache(body, at, state) {
  const copy = Object.assign({}, body);
  copy.cacheState = state;
  copy.cachedAt = new Date(at).toISOString();
  if (state === "stale") {
    const age = Math.max(0, Math.round((Date.now() - at) / 1000));
    copy.cacheNote = "Stored release from " + (c103NoteWhen(copy.cachedAt) || "the last response") + ", " + age + " seconds ago. It was not refreshed for this response. It is not a new print.";
  } else delete copy.cacheNote;
  return copy;
}

const c103Flights = new Map();

function c103Kick(store, key, producer) {
  if (c103Flights.has(key)) return c103Flights.get(key);
  const run = Promise.resolve().then(() => producer()).then((body) => {
    const next = body;
    if (c103WorthStoring(next)) {
      const saved = Object.assign({}, next);
      delete saved.cacheState;
      delete saved.cacheNote;
      delete saved.cachedAt;
      store.set(key, { ok: true, at: Date.now(), body: saved });
    }
    return next;
  }).catch(() => null).finally(() => { c103Flights.delete(key); });
  c103Flights.set(key, run);
  return run;
}

function c103Memo(store, key, ttl, producer, cold) {
  const now = Date.now();
  const hit = store.get(key);
  const limit = typeof ttl === "function" ? ttl(hit && hit.body) : ttl;
  const fresh = !!(hit && hit.ok && now - hit.at < limit);
  if (!fresh) c103Kick(store, key, producer);
  if (fresh) return Promise.resolve(c103WithCache(hit.body, hit.at, "fresh"));
  if (hit && hit.ok) return Promise.resolve(c103WithCache(hit.body, hit.at, "stale"));
  return Promise.resolve(typeof cold === "function" ? cold() : c103Cold(now));
}

function c103IsPremium(user) {
  try {
    if (!user) return false;
    if (user.tier === "premium") return true;
    if (typeof isAdminUser === "function" && isAdminUser(user)) return true;
  } catch (e) {}
  return false;
}

function c103Notice(candidate, reader, dismissals) {
  if (!reader || !reader.signedIn || !candidate || !candidate.releaseKey) return { show: false };
  const gone = (dismissals || []).some((k) => k === candidate.releaseKey);
  if (gone) return { show: false, releaseKey: candidate.releaseKey };
  return {
    show: true,
    releaseKey: candidate.releaseKey,
    text: "CPI is out. The " + candidate.periodLabel + " figures are on this page."
  };
}

function c103Respond(model, reader, dismissals) {
  const src = model || c103Cold();
  const premium = !!(reader && reader.premium);
  const base = {
    ok: !!src.ok,
    access: premium ? "premium" : "free",
    cacheState: src.cacheState || "cold",
    generatedAtUtc: src.generatedAtUtc,
    generatedAtUk: src.generatedAtUk,
    source: C103_SOURCE,
    statusNote: src.statusNote || (src.latest ? "" : "not loaded yet"),
    countdown: src.countdown || null,
    latest: src.latest || null,
    trend: Array.isArray(src.trend) ? src.trend : [],
    archive: Array.isArray(src.archive) ? src.archive.map((row) => ({
      period: row.period,
      periodLabel: row.periodLabel,
      headline: row.headline || null,
      core: row.core || null
    })) : [],
    notice: c103Notice(src.noticeCandidate, reader, dismissals)
  };
  if (src.cacheNote) base.cacheNote = src.cacheNote;
  if (src.cachedAt) base.cachedAt = src.cachedAt;
  if (premium) {
    base.categories = Array.isArray(src.categories) ? src.categories : [];
    base.contributions = Array.isArray(src.contributions) ? src.contributions : [];
    base.gold = Array.isArray(src.gold) ? src.gold : [];
    base.contributionLabel = C103_CONTRIB_LABEL;
    base.goldLabel = C103_GOLD_LABEL;
    base.relativeImportance = src.relativeImportance || null;
  }
  return c103Guest(base);
}

function c103Guest(value) {
  if (Array.isArray(value)) return value.map(c103Guest);
  if (!value || typeof value !== "object") return value;
  const out = {};
  Object.keys(value).forEach((key) => {
    if (key === "momSeries" || key === "yoySeries" || key === "seriesId" || key === "series_id") return;
    out[key] = c103Guest(value[key]);
  });
  return out;
}

function c103DdlAudit(text) {
  const alterW = ["alt", "er"].join("");
  const dropW = ["dr", "op"].join("");
  const tableW = ["tab", "le"].join("");
  const indexW = ["ind", "ex"].join("");
  const truncW = ["tru", "ncate"].join("");
  const createW = ["cre", "ate"].join("");
  const banned = new RegExp("\\b(?:" + alterW + "|" + dropW + ")\\s+(?:" + tableW + "|" + indexW + ")\\b|\\b" + truncW + "\\b|\\b" + createW + "\\s+" + indexW + "\\b", "i");
  const createRe = new RegExp("create\\s+table(?:\\s+if\\s+not\\s+exists)?\\s+([a-z0-9_]+)", "gi");
  const found = [];
  let m;
  const src = String(text || "");
  if (banned.test(src)) return { ok: false, reason: "banned", tables: [] };
  while ((m = createRe.exec(src))) {
    const stmt = m[0];
    const name = m[1].toLowerCase();
    if (!/if\s+not\s+exists/i.test(stmt) || C103_TABLES.indexOf(name) < 0) return { ok: false, reason: stmt, tables: found };
    found.push(name);
  }
  const uniq = Array.from(new Set(found));
  const missing = C103_TABLES.filter((name) => uniq.indexOf(name) < 0);
  if (missing.length) return { ok: false, reason: "missing " + missing.join(","), tables: uniq };
  return { ok: true, tables: uniq };
}

function c103ItemPath(it) {
  if (!it || !it.length) return "";
  if (it.length >= 4 && typeof it[1] === "string" && it[1].charAt(0) === "/") return it[1];
  if (typeof it[0] === "string" && it[0].charAt(0) === "/") return it[0];
  return "";
}

function c103InsertInto(list) {
  if (!Array.isArray(list) || list.some((it) => c103ItemPath(it) === "/cpi/")) return;
  const sample = list.find((it) => Array.isArray(it));
  const row = sample && sample.length >= 4
    ? ["", "/cpi/", "CPI Day", "US inflation release, in UK time"]
    : sample && sample.length === 3
      ? ["/cpi/", "CPI Day", "US inflation release, in UK time"]
      : ["/cpi/", "CPI Day"];
  const at = list.findIndex((it) => c103ItemPath(it) === "/terminal/");
  if (at >= 0) list.splice(at + 1, 0, row);
  else list.push(row);
}

function c103InsertNav(nav, groups) {
  if (Array.isArray(nav) && !nav.some((x) => x && x[0] === "/cpi/")) {
    const markets = nav.findIndex((x) => x && x[0] === "/markets/");
    const research = nav.findIndex((x) => x && x[0] === "/research/");
    const item = ["/cpi/", "CPI Day"];
    if (markets >= 0) nav.splice(markets + 1, 0, item);
    else if (research >= 0) nav.splice(research, 0, item);
    else nav.push(item);
  }
  if (Array.isArray(groups)) {
    groups.forEach((g) => {
      if (!g || g[0] !== "Gold and macro" || !Array.isArray(g[1])) return;
      c103InsertInto(g[1]);
    });
  }
  return { nav: nav, groups: groups };
}

function c103Paths(nav, groups) {
  const out = [];
  (nav || []).forEach((x) => { if (x && x[0]) out.push(x[0]); });
  (groups || []).forEach((g) => (g[1] || []).forEach((it) => { const p = c103ItemPath(it); if (p) out.push(p); }));
  return out;
}

function c103Deadline(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(Object.assign(new Error("timeout"), { name: "TimeoutError" })), ms);
    Promise.resolve(promise).then((v) => { clearTimeout(t); resolve(v); }, (e) => { clearTimeout(t); reject(e); });
  });
}

function c103RawGet(deps, url, ms, body) {
  const limit = Math.min(2500, ms || 2500);
  const headers = Object.assign({
    "User-Agent": (deps && deps.ua) || C103_UA,
    Accept: "application/json, text/calendar, text/html, */*"
  }, (deps && deps.headers) || {});
  if (body) headers["Content-Type"] = "application/json";
  if (deps && typeof deps.fetch === "function" && !(deps && deps.request)) {
    const Ctrl = deps.AbortController || (typeof AbortController === "function" ? AbortController : null);
    const ctrl = Ctrl ? new Ctrl() : null;
    const timer = setTimeout(() => { try { if (ctrl) ctrl.abort(); } catch (e) {} }, limit);
    return c103Deadline(deps.fetch(url, {
      method: body ? "POST" : "GET",
      headers: headers,
      body: body || undefined,
      redirect: "follow",
      signal: ctrl ? ctrl.signal : undefined
    }).then(async (res) => {
      const text = typeof res.text === "function" ? await res.text() : String(res.body || "");
      if (!res || res.ok === false || (res.status && res.status >= 400)) throw new Error("http");
      return text;
    }), limit).finally(() => clearTimeout(timer));
  }
  const request = deps && deps.request;
  if (typeof request !== "function") return Promise.reject(new Error("no-transport"));
  return new Promise((resolve, reject) => {
    let done = false;
    const req = request(url, { method: body ? "POST" : "GET", headers: headers });
    const finish = (err, val) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      if (err) reject(err); else resolve(val);
    };
    const kill = () => {
      try { if (req && typeof req.destroy === "function") req.destroy(); } catch (e) {}
      finish(Object.assign(new Error("timeout"), { name: "TimeoutError" }));
    };
    const timer = setTimeout(kill, limit);
    if (req && typeof req.setTimeout === "function") req.setTimeout(limit, kill);
    if (req && typeof req.on === "function") {
      req.on("error", (e) => finish(e.name === "AbortError" ? Object.assign(new Error("timeout"), { name: "TimeoutError" }) : e));
      req.on("response", (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(String(c))));
        res.on("end", () => {
          const code = res.statusCode || 0;
          const text = Buffer.concat(chunks).toString("utf8");
          if (code >= 400) finish(new Error("http"));
          else finish(null, text);
        });
      });
    }
    try { if (body && req && req.write) req.write(body); if (req && req.end) req.end(); } catch (e) { finish(e); }
  });
}

async function c103Job(fn) {
  try { return { ok: true, value: await fn() }; }
  catch (e) { return { ok: false, error: e && e.name === "TimeoutError" ? "timeout" : "failed" }; }
}

function c103ParseArchive(html, nowMs) {
  const out = [];
  const seen = new Set();
  const re = /cpi_(\d{2})(\d{2})(\d{4})\.htm/g;
  const cutoff = nowMs - 5 * 365.25 * 86400000;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const month = Number(m[1]);
    const day = Number(m[2]);
    const year = Number(m[3]);
    if (month < 1 || month > 12 || day < 1 || day > 31) continue;
    const row = c103ReleaseInstant(year, month, day, 8, 30);
    if (row.startMs < cutoff || seen.has(row.etDate)) continue;
    seen.add(row.etDate);
    row.source = "bls-archive";
    row.dailyOnly = true;
    row.scheduleUrl = "https://www.bls.gov/bls/news-release/cpi.htm";
    out.push(row);
  }
  return out;
}

async function c103FetchAll(deps, nowMs) {
  const ms = Math.min(2500, (deps && deps.timeoutMs) || 2500);
  const year = c103Parts(nowMs, "America/New_York").year;
  const endYear = String(year);
  const startYear = String(deps && deps.apiKey ? year - 19 : year - 9);
  const ids = [];
  C103_CATALOG.forEach((row) => { ids.push(row[2], row[3]); });
  const info = {
    apiKey: deps && deps.apiKey,
    hasStored: !!(deps && deps.hasStored),
    inReleaseWindow: !!(deps && deps.inReleaseWindow),
    hasNewMonth: !!(deps && deps.hasNewMonth),
    missingReleaseMonth: !!(deps && deps.missingReleaseMonth),
    needsSecondBatch: !!(deps && deps.needsSecondBatch)
  };
  const plan = c103BlsPlan(deps && deps.blsBudget, nowMs, info);
  const chunks = [];
  if (plan.call) {
    const size = plan.batch;
    const startAt = plan.offset || 0;
    for (let i = startAt; i < ids.length && chunks.length < plan.batches; i += size) chunks.push(ids.slice(i, i + size));
  }
  const blsBody = (list) => {
    const payload = { seriesid: list, startyear: startYear, endyear: endYear };
    if (deps && deps.apiKey) payload.registrationkey = deps.apiKey;
    return JSON.stringify(payload);
  };
  const scheduleDue = !(deps && deps.scheduleFresh);
  const yahooDue = !(deps && deps.yahooFresh);
  const riDue = scheduleDue || !!(deps && deps.riDue);
  const [ics, html, ri, archive, hourly, daily, blsParts] = await Promise.all([
    scheduleDue ? c103Job(() => c103RawGet(deps, C103_ICS, ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    scheduleDue ? c103Job(() => c103RawGet(deps, C103_HTML, ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    riDue ? c103Job(() => c103RawGet(deps, C103_RI, ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    scheduleDue ? c103Job(() => c103RawGet(deps, "https://www.bls.gov/bls/news-release/cpi.htm", ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    yahooDue ? c103Job(() => c103RawGet(deps, c103GoldUrl("1h", "2y"), ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    yahooDue ? c103Job(() => c103RawGet(deps, c103GoldUrl("1d", "5y"), ms)) : Promise.resolve({ ok: false, error: "skipped" }),
    Promise.all(chunks.map((list) => c103Job(() => c103RawGet(Object.assign({}, deps, { headers: { "Content-Type": "application/json" } }), C103_BLS, ms, blsBody(list)))))
  ]);
  const series = {};
  let seriesOk = false;
  let blsMade = 0;
  blsParts.forEach((part, i) => {
    const offset = (plan.offset || 0) + i * (plan.batch || 0);
    const where = "reason=" + (plan.reason || "call") + " offset=" + offset;
    if (!part.ok) {
      console.log("[c103] BLS fail " + where + " " + (part.error || "failed"));
      return;
    }
    let json = null;
    try { json = JSON.parse(part.value); } catch (e) { json = null; }
    const parsed = c103ParseBls(json);
    if (!parsed.ok) {
      console.log("[c103] BLS fail " + where + " status");
      return;
    }
    blsMade += 1;
    seriesOk = true;
    let newest = "";
    Object.keys(parsed.series).forEach((id) => {
      series[id] = parsed.series[id];
      const top = c103NewestPeriod(parsed.series[id]);
      if (top > newest) newest = top;
    });
    console.log("[c103] BLS ok " + where + " series=" + Object.keys(parsed.series).length + " newest=" + (newest || "none"));
  });
  if (riDue) console.log("[c103] weights " + (ri.ok ? "ok month=" + ((ri.value && c103ParseRi(ri.value).weightMonth) || "none") : "fail " + (ri.error || "failed")));
  const blsBudget = c103BlsCharge(plan, blsMade, nowMs);
  let hourlyBars = [];
  let dailyBars = [];
  if (hourly.ok) {
    try { hourlyBars = c103CompletedBars(c103ParseYahoo(JSON.parse(hourly.value), 3600000).bars || [], nowMs, false); } catch (e) { hourlyBars = []; }
  }
  if (daily.ok) {
    try { dailyBars = c103CompletedBars(c103ParseYahoo(JSON.parse(daily.value), 86400000).bars || [], nowMs, true); } catch (e) { dailyBars = []; }
  }
  const archiveRows = archive.ok ? c103ParseArchive(archive.value, nowMs) : [];
  return {
    icsOk: ics.ok && c103ParseIcs(ics.value).length > 0,
    htmlOk: html.ok && c103ParseHtmlSchedule(html.value).length > 0,
    archiveOk: archive.ok && archiveRows.length > 0,
    ics: ics.ok ? c103ParseIcs(ics.value) : [],
    html: html.ok ? c103ParseHtmlSchedule(html.value) : [],
    archive: archiveRows,
    blsBudget: blsBudget,
    blsCalls: blsMade,
    ri: ri.ok ? c103ParseRi(ri.value) : { ok: false },
    series: { ok: seriesOk, series: series },
    hourly: hourlyBars,
    daily: dailyBars,
    fetchedAt: new Date(nowMs).toISOString(),
    errors: {
      ics: ics.ok ? "" : ics.error,
      html: html.ok ? "" : html.error,
      ri: ri.ok ? "" : ri.error,
      bls: seriesOk ? "" : "failed",
      hourly: hourly.ok ? "" : hourly.error,
      daily: daily.ok ? "" : daily.error
    }
  };
}

function c103Carry(previous) {
  if (!previous) return {};
  return {
    previousSeries: previous.previousSeries || null,
    previousRi: previous.previousRi || null,
    previousEvents: previous.previousEvents || null,
    previousMonths: previous.previousMonths || null,
    previousGold: previous.previousGold || previous.gold || null,
    feedBars: previous.feedBars || null,
    feedTimes: previous.feedTimes || null,
    storedGold: previous.storedGold || previous.gold || [],
    blsBudget: previous.blsBudget || null,
    storedFetchedAt: previous.latest && previous.latest.fetchedAt || previous.cachedAt || "",
    snapshots: previous.snapshots || []
  };
}

function c103BlsSeriesCap(apiKey) { return apiKey ? 50 : 25; }

function c103BlsPlan(budget, nowMs, info) {
  const keyed = !!(info && info.apiKey);
  const cap = keyed ? 500 : 20;
  const batch = c103BlsSeriesCap(info && info.apiKey);
  const day = c103Ymd(nowMs, "America/New_York");
  const calls = budget && budget.dayKey === day ? (budget.calls || 0) : 0;
  const last = budget && budget.lastBlsAt ? budget.lastBlsAt : 0;
  const base = { cap: cap, batch: batch, calls: calls, day: day, lastBlsAt: last };
  const room = cap - calls;
  if (room <= 0) return Object.assign(base, { call: false, reason: "budget", batches: 0 });
  if (!(info && info.hasStored)) return Object.assign(base, { call: true, reason: "empty", batches: room });
  if (info.missingReleaseMonth) {
    if (last && nowMs - last < 5 * 60 * 1000) return Object.assign(base, { call: false, reason: "poll-wait", batches: 0, offset: 0 });
    return Object.assign(base, { call: true, reason: "missing-month", batches: 1, offset: 0 });
  }
  if (info.inReleaseWindow && !info.hasNewMonth) {
    if (last && nowMs - last < 5 * 60 * 1000) return Object.assign(base, { call: false, reason: "poll-wait", batches: 0, offset: 0 });
    return Object.assign(base, { call: true, reason: "release-window", batches: 1, offset: 0 });
  }
  if (info.needsSecondBatch && room > 0) {
    if (last && nowMs - last < 5 * 60 * 1000) return Object.assign(base, { call: false, reason: "poll-wait", batches: 0, offset: 0 });
    return Object.assign(base, { call: true, reason: "second-batch", batches: 1, offset: batch });
  }
  if (last && nowMs - last < 24 * 3600 * 1000) return Object.assign(base, { call: false, reason: "daily", batches: 0 });
  return Object.assign(base, { call: true, reason: "daily", batches: room });
}

function c103BlsCharge(plan, made, nowMs) {
  return { dayKey: plan.day, calls: plan.calls + made, lastBlsAt: made ? nowMs : plan.lastBlsAt };
}

function c103InReleaseWindow(events, nowMs) {
  return (events || []).some((ev) => ev && nowMs >= ev.startMs && nowMs - ev.startMs <= 90 * 60 * 1000);
}

function c103NeedsSecondBatch(model) {
  if (!model || !model.latest || !model.latest.period) return false;
  const bits = /^(\d{4})-(\d{2})$/.exec(model.latest.period);
  if (!bits) return false;
  const y = Number(bits[1]);
  const m = Number(bits[2]);
  const series = model.previousSeries || {};
  return C103_CATALOG.some((row) => [row[2], row[3]].some((id) => !(series[id] || []).some((p) => p.year === y && p.month === m)));
}

function c103DueReference(events, nowMs) {
  const past = (events || []).filter((ev) => ev && ev.startMs <= nowMs && ev.referencePeriod && !ev.dailyOnly);
  past.sort((a, b) => b.startMs - a.startMs);
  return past[0] || null;
}

function c103ReleaseMonthMissing(model, nowMs) {
  const due = c103DueReference(model && model.previousEvents, nowMs);
  if (!due) return false;
  if (nowMs - due.startMs > 36 * 3600 * 1000) return false;
  const bits = /^(\d{4})-(\d{2})$/.exec(due.referencePeriod);
  if (!bits) return false;
  const points = model && model.previousSeries && model.previousSeries.CUSR0000SA0;
  return !(points || []).some((p) => p && p.year === Number(bits[1]) && p.month === Number(bits[2]) && typeof p.value === "number");
}

function c103HasNewMonth(model, nowMs) {
  const events = model && model.previousEvents || [];
  const open = events.filter((ev) => ev && nowMs >= ev.startMs && nowMs - ev.startMs <= 90 * 60 * 1000);
  if (!open.length) return true;
  return open.every((ev) => model.latest && model.latest.period === ev.referencePeriod);
}

function c103CacheMs(model, nowMs) {
  const events = model && model.previousEvents || [];
  const next = events.filter((ev) => ev && ev.startMs > nowMs).sort((a, b) => a.startMs - b.startMs)[0];
  const inWindow = c103InReleaseWindow(events, nowMs);
  if (c103ReleaseMonthMissing(model, nowMs)) return 60 * 1000;
  if (inWindow && !c103HasNewMonth(model, nowMs)) return 60 * 1000;
  const follow = inWindow || events.some((ev) => ev && nowMs >= ev.startMs && nowMs - ev.startMs < 6 * 3600 * 1000);
  const weightsOk = !!(model && model.latest && model.previousRi && c103WeightsMatch(model.previousRi.weightMonth || model.previousRi.asOf, model.latest.period));
  if (follow && c103NeedsSecondBatch(model)) return 60 * 1000;
  if (inWindow && model && model.latest && !weightsOk) return 60 * 1000;
  if (next) return Math.max(1000, Math.min(15 * 60 * 1000, next.startMs - nowMs));
  return 15 * 60 * 1000;
}

function c103ForNow(model, nowMs) {
  const copy = Object.assign({}, model || {});
  copy.countdown = c103Countdown(nowMs, copy.previousEvents || []);
  return copy;
}

async function c103Refresh(deps, nowMs, previous) {
  const events = previous && previous.previousEvents || [];
  const yahooAt = previous && previous.feedBars && Date.parse(previous.feedBars.hourlyAt || previous.feedBars.dailyAt || "");
  deps.hasStored = !!(previous && previous.latest);
  deps.inReleaseWindow = c103InReleaseWindow(events, nowMs);
  deps.hasNewMonth = c103HasNewMonth(previous, nowMs);
  deps.missingReleaseMonth = c103ReleaseMonthMissing(previous, nowMs);
  deps.blsBudget = (previous && previous.blsBudget) || (deps && deps.blsBudget) || { calls: 0, dayKey: "", lastBlsAt: 0 };
  const dueNow = c103DueReference(events, nowMs);
  deps.needsSecondBatch = c103NeedsSecondBatch(previous) && !!(dueNow && previous && previous.latest && previous.latest.period === dueNow.referencePeriod);
  deps.scheduleFresh = !!(previous && previous.previousEvents && previous.previousEvents.some((ev) => ev && ev.source === "bls-ics") && previous.feedTimes && nowMs - Date.parse(previous.feedTimes.schedule || 0) < 24 * 3600 * 1000);
  const weightsOk = previous && previous.latest && previous.previousRi && c103WeightsMatch(previous.previousRi.weightMonth || previous.previousRi.asOf, previous.latest.period);
  const lastRi = previous && previous.feedTimes && Date.parse(previous.feedTimes.ri || 0);
  deps.riDue = !!(deps.inReleaseWindow && previous && previous.latest && !weightsOk && (!lastRi || nowMs - lastRi >= 5 * 60 * 1000));
  deps.yahooFresh = !!(yahooAt && nowMs - yahooAt < 15 * 60 * 1000);
  const fetched = await c103FetchAll(deps, nowMs);
  const model = c103Compose(Object.assign({}, fetched, c103Carry(previous), { snapshots: (deps && deps.snapshots) || (previous && previous.snapshots) || [] }), nowMs);
  model.blsBudget = fetched.blsBudget;
  if (model.feedTimes) {
    model.feedTimes.schedule = deps.scheduleFresh ? (previous.feedTimes && previous.feedTimes.schedule) : new Date(nowMs).toISOString();
    model.feedTimes.ri = fetched.ri && fetched.ri.ok ? new Date(nowMs).toISOString() : (previous && previous.feedTimes && previous.feedTimes.ri);
  }
  if (!model.latest) model.statusNote = "not loaded yet";
  if (c103ReleaseMonthMissing(model, nowMs)) {
    const due = c103DueReference(model.previousEvents, nowMs);
    model.statusNote = "The " + c103PeriodLabel(due.referencePeriod) + " figures are not in the stored release yet.";
  }
  model.countdown = c103Countdown(nowMs, model.previousEvents || []);
  return model;
}

function c103CacheControl(body) {
  if (!body || body.cacheState === "cold") return "no-store";
  if (body.cacheState === "stale") return "private, max-age=0, stale-while-revalidate=120";
  return "private, max-age=15, stale-while-revalidate=120";
}

const C103_CSS = "<style id=\"c103-css\">.c103{box-sizing:border-box;max-width:100%;overflow-x:clip;font:15px/1.45 var(--sans,Inter,system-ui,sans-serif);color:var(--ink);background:var(--paper);min-width:0}.c103 *,.c103 *::before,.c103 *::after{box-sizing:border-box}.c103 h2,.c103 h3{font-family:var(--serif,Georgia,serif);line-height:1.2;margin:0 0 8px;color:var(--ink)}.c103 h2{font-size:1.45rem}.c103 p,.c103 caption,.c103 caption a{overflow-wrap:anywhere}.c103 a{color:var(--ink);text-decoration-thickness:1px;text-underline-offset:3px}.c103 a:focus-visible,.c103 button:focus-visible,#c103-canvas:focus-visible{outline:3px solid var(--ink);outline-offset:3px}.c103-k{color:var(--ink);font-size:14px}.c103-v{font:600 1.6rem/1.2 var(--serif,Georgia,serif);margin:4px 0;font-variant-numeric:tabular-nums;color:var(--ink)}.c103-miss{border-left:3px solid var(--amber);padding:4px 0 4px 10px;margin:8px 0;color:var(--ink)}.c103-banner{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;justify-content:space-between;border:1px solid var(--rule);padding:10px 12px;margin:0 0 14px;background:var(--paper);color:var(--ink)}.c103-banner button,.c103-tools button{min-height:44px;min-width:44px;padding:8px 12px;background:var(--paper);color:var(--ink);border:1px solid var(--rule);border-radius:4px;cursor:pointer}.c103-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0}.c103-card{min-width:0;border-top:2px solid var(--ink);padding:10px 2px}.c103-card h3{font:600 14px/1.3 var(--sans,Inter,sans-serif);margin:0 0 6px;color:var(--ink)}.c103-count{border-top:2px solid var(--ink);padding:12px 0;margin:8px 0 4px}.c103-count strong{font:600 1.8rem/1.1 var(--serif,Georgia,serif);font-variant-numeric:tabular-nums}.c103-chart{min-width:0;margin:8px 0 16px}#c103-canvas{display:block;width:100%;height:420px;max-width:100%;touch-action:pan-y;background:var(--paper)}.c103-legend{display:flex;flex-wrap:wrap;gap:12px 18px;list-style:none;margin:8px 0;padding:0;color:var(--ink)}.c103-swatch{display:inline-block;width:28px;height:0;border-top:3px solid var(--ink);margin-right:6px;vertical-align:middle}.c103-swatch-core{border-top-style:dashed;border-top-color:var(--up)}.c103-scroll{display:block;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch}.c103 table{border-collapse:collapse;width:max-content;min-width:100%;font-size:15px;color:var(--ink)}.c103 caption{caption-side:top;text-align:left;padding:0 0 8px;font-size:15px;white-space:normal;color:var(--ink)}.c103 th,.c103 td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule);white-space:nowrap;font-weight:400;vertical-align:top;color:var(--ink);background:var(--paper)}.c103 thead th{font-weight:600}.c103 td.c103-why{white-space:normal;min-width:14rem}.c103-live{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}.c103-gap{color:var(--muted);margin:0 0 8px}.c103-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:22px;min-width:0}.c103-lock{border:1px solid var(--rule);padding:12px;margin:12px 0;color:var(--ink);background:var(--paper)}@media (max-width:899px){.c103-stats{grid-template-columns:1fr 1fr}.c103-grid{grid-template-columns:1fr}#c103-canvas{height:300px}}@media (max-width:479px){.c103-stats{grid-template-columns:1fr}#c103-canvas{height:240px}.c103{font-size:15px}}@media (prefers-reduced-motion:reduce){.c103 *{transition:none!important;animation:none!important}}@media (min-width:1280px){header.site .wrap{height:auto;min-height:64px;flex-wrap:wrap;align-items:center;row-gap:8px;padding-top:8px;padding-bottom:8px;box-sizing:border-box;max-width:min(1300px,100%)}header.site .nav{flex:1 1 0;flex-wrap:wrap;justify-content:flex-end;align-items:center;row-gap:4px;min-width:0}header.site .nav>a{margin-left:12px}header.site form.c97tg{flex:0 0 auto}}</style>";

function c103DismissGate(req, key, known, limiter, nowMs, userId) {
  const headers = (req && req.headers) || {};
  const type = String(headers["content-type"] || "");
  if (!/^application\/json\b/i.test(type)) return { ok: false, status: 415, error: "JSON required" };
  const origin = String(headers.origin || "");
  const site = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
  if (origin !== site && origin !== "https://thedispatch.uk" && origin !== "https://www.thedispatch.uk") {
    return { ok: false, status: 403, error: "Origin refused" };
  }
  if (!known || known.indexOf(key) < 0) return { ok: false, status: 400, error: "Unknown release" };
  if (limiter && typeof limiter.allow === "function" && !limiter.allow(userId || "reader", nowMs || Date.now())) {
    return { ok: false, status: 429, error: "Too many dismissals" };
  }
  return { ok: true, key: key };
}

async function c103Peek(req) {
  return await new Promise((resolve) => {
    const chunks = [];
    let size = 0;
    req.on("data", (c) => { size += c.length; if (size < 4000) chunks.push(c); });
    req.on("end", () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}")); }
      catch (e) { resolve({}); }
    });
    req.on("error", () => resolve({}));
  });
}

async function c103RecordTick(deps, nowMs) {
  if (c103Ymd(nowMs, "America/New_York") < C103_RECORD_FROM) return null;
  const hit = (deps.events || []).find((ev) => ev && nowMs >= ev.startMs - 20 * 60000 && nowMs <= ev.startMs + 90 * 60000);
  if (!hit) return null;
  const text = await c103RawGet(deps, c103GoldUrl("5m", "1d"), Math.min(2500, (deps && deps.timeoutMs) || 2500));
  const parsed = c103ParseYahoo(JSON.parse(text), 5 * 60000);
  const fresh = c103CompletedBars(parsed.bars || [], nowMs, false).filter((b) => nowMs - b.endMs <= 10 * 60000);
  const target = hit.startMs + 60 * 60 * 1000;
  let bar = null;
  let kind = "pre";
  if (nowMs < hit.startMs) {
    const pres = fresh.filter((b) => b.endMs <= hit.startMs);
    bar = pres.length ? pres[pres.length - 1] : null;
    kind = "pre";
  } else {
    bar = fresh.slice().sort((a, b) => Math.abs(a.endMs - target) - Math.abs(b.endMs - target))[0] || null;
    if (!bar || Math.abs(bar.endMs - target) > 10 * 60 * 1000) return null;
    kind = "post";
  }
  if (!bar) return null;
  return {
    releaseAtUtc: hit.releaseAtUtc,
    observedAtUtc: new Date(bar.endMs).toISOString(),
    price: bar.close,
    windowKind: kind,
    sourceLabel: C103_GOLD_LABEL
  };
}

async function c103SaveSnapshot(deps, snap) {
  if (!deps || typeof deps.sql !== "function" || !snap) return;
  if (typeof deps.sql.query === "function") {
    await deps.sql.query(
      "INSERT INTO cpi_gold_snapshots (release_at, observed_at, price, window_kind, source_label) VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING",
      [snap.releaseAtUtc, snap.observedAtUtc, snap.price, snap.windowKind, C103_GOLD_LABEL]
    );
  }
}

async function c103LoadStored(deps) {
  if (!deps || typeof deps.sql !== "function" || typeof deps.sql.query !== "function") return null;
  const one = async (text) => {
    const result = await deps.sql.query(text);
    return result && result[0] && Array.isArray(result[0].data) ? result[0].data : [];
  };
  const seriesRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT series_id, period, value FROM cpi_series_values) t");
  const goldRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT release_at, reference_period, plus_1h_pct, plus_1d_pct, plus_5d_pct, hourly_available, recorded, hour_label, source_label FROM cpi_gold_reactions) t");
  const budgetRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT payload FROM cpi_releases WHERE period = '__bls_budget') t");
  const scheduleRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT payload, bls_fetched_at FROM cpi_releases WHERE period = '__schedule') t");
  const figureRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT period, bls_fetched_at FROM cpi_releases WHERE period ~ '^[0-9]{4}-[0-9]{2}$') t");
  const seriesAtRows = await one("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT period, series_id, MAX(fetched_at) AS fetched_at FROM cpi_series_values GROUP BY period, series_id) t");
  const series = {};
  seriesRows.forEach((row) => {
    const m = /^(\d{4})-(\d{2})$/.exec(row.period || "");
    if (!m || typeof Number(row.value) !== "number") return;
    if (!series[row.series_id]) series[row.series_id] = [];
    series[row.series_id].push({ year: Number(m[1]), month: Number(m[2]), value: Number(row.value) });
  });
  const storedGold = goldRows.map((row) => ({
    releaseAtUtc: new Date(row.release_at).toISOString(),
    referencePeriod: row.reference_period,
    plus1hPct: row.plus_1h_pct,
    plus1dPct: row.plus_1d_pct,
    plus5dPct: row.plus_5d_pct,
    hourlyAvailable: !!row.hourly_available,
    hourLabel: row.hour_label || "",
    recorded: !!row.recorded,
    sourceLabel: C103_GOLD_LABEL,
    releaseUk: c103FormatUk(new Date(row.release_at).getTime())
  }));
  let budget = budgetRows[0] && budgetRows[0].payload ? budgetRows[0].payload : null;
  if (typeof budget === "string") { try { budget = JSON.parse(budget); } catch (e) { budget = null; } }
  const schedule = scheduleRows[0] && scheduleRows[0].payload ? scheduleRows[0].payload : null;
  const savedEvents = schedule && Array.isArray(schedule.events) ? schedule.events : [];
  const figureAt = (figureRows || []).reduce((best, row) => {
    if (!row || !row.period || row.period <= best.period) return best;
    return { period: row.period, at: row.bls_fetched_at || "" };
  }, { period: "", at: "" });
  let newestSeries = "";
  Object.keys(series).forEach((id) => {
    const top = c103NewestPeriod(series[id]);
    if (top > newestSeries) newestSeries = top;
  });
  const shownAt = (seriesAtRows || []).filter((row) => row && row.period === newestSeries);
  const headlineAt = shownAt.find((row) => row.series_id === "CUSR0000SA0");
  const seriesAt = (headlineAt && headlineAt.fetched_at) || (shownAt[0] && shownAt[0].fetched_at) || "";
  const scheduleAt = (schedule && schedule.fetchedAt) || (scheduleRows[0] && scheduleRows[0].bls_fetched_at) || "";
  const savedAt = seriesAt || figureAt.at || "";
  if (!Object.keys(series).length && !storedGold.length && !savedEvents.length) return null;
  const model = c103Compose({
    series: { ok: Object.keys(series).length > 0, series: series },
    ri: { ok: false },
    icsOk: false,
    htmlOk: false,
    previousEvents: savedEvents,
    hourly: [],
    daily: [],
    storedGold: storedGold,
    fetchedAt: savedAt,
    storedFetchedAt: savedAt,
    feedTimes: { bls: savedAt, schedule: scheduleAt }
  }, savedAt ? Date.parse(savedAt) : Date.now());
  model.storedGold = storedGold;
  model.blsBudget = budget;
  model.releaseRowPending = !!(newestSeries && !(figureRows || []).some((row) => row && row.period === newestSeries));
  if (savedAt && model.latest) model.latest.fetchedAt = savedAt;
  model.statusNote = model.latest ? "Stored release loaded from the database." : "not loaded yet";
  return model;
}

function c103Install() {
  c103Install.limiter = typeof FixedWindowRateLimiter === "function"
    ? new FixedWindowRateLimiter({ limit: 8, windowMs: 10 * 60 * 1000, maxKeys: 2000 })
    : { allow: function () { return true; } };
  if (c103Install.done) return;
  try { c103InsertNav(typeof C93_NAV !== "undefined" ? C93_NAV : null, typeof C101B_GROUPS !== "undefined" ? C101B_GROUPS : null); } catch (e) {}
  const store = new Map();
  const depsOf = () => ({
    request: typeof c103Install.request === "function" ? c103Install.request : defaultRequest,
    fetch: null,
    ua: C103_UA,
    apiKey: typeof process !== "undefined" && process.env ? process.env.BLS_API_KEY : "",
    timeoutMs: 2500,
    sql: typeof sql === "function" ? sql : null
  });
  function defaultRequest(url, options) {
    const lib = /^https:/.test(url) ? require("https") : require("http");
    return lib.request(url, options);
  }
  async function produce() {
    let prev = store.get("model");
    const deps = depsOf();
    if (!prev) {
      const loaded = await c103LoadStored(deps).catch(() => null);
      if (loaded && loaded.latest) {
        store.set("model", { ok: true, at: 0, body: loaded });
        prev = store.get("model");
      }
    }
    deps.snapshots = await c103LoadSnapshots(deps).catch(() => []);
    deps.knownSeries = prev && prev.body && prev.body.previousSeries || {};
    deps.knownGold = prev && prev.body && prev.body.storedGold || [];
    const body = await c103Refresh(deps, Date.now(), prev && prev.body);
    await c103Persist(deps, body);
    return body;
  }
  function read() {
    return c103Memo(store, "model", (body) => c103CacheMs(body, Date.now()), produce, () => c103Cold(Date.now()));
  }
  function send(res, code, body, cache) {
    const payload = JSON.stringify(body);
    res.writeHead(code, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": cache || c103CacheControl(body),
      "Vary": "Cookie",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin"
    });
    res.end(payload);
  }
  async function readerOf(req) {
    let user = null;
    try { user = typeof c96UserOf === "function" ? await c96UserOf(req) : null; } catch (e) { user = null; }
    return { user: user, premium: c103IsPremium(user), signedIn: !!(user && user.id), userId: user && user.id };
  }
  async function page(req, res) {
    try { if (typeof c97Hook === "function") c97Hook(req, res); } catch (e) {}
    const reader = await readerOf(req);
    const origin = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
    const client = c103Install.clientJs || "";
    const css = C103_CSS;
    const body = css + "<section><div class=\"kicker\">Markets</div><h1>CPI day</h1><p class=\"dek\">The US consumer price index, shown in UK time. Headline and core are free. Members also get the category breakdown and how gold futures moved after past releases. No forecast.</p><p class=\"byline\">Edited by Vraj Patel</p></section><section id=\"c103-mount\" aria-busy=\"true\"><p>Loading the stored release…</p></section><script>" + client + "</script><script>document.getElementById(\"c103-mount\").setAttribute(\"aria-busy\",\"false\");if(window.c103ui){window.c103ui.mount(document.getElementById(\"c103-mount\"));}else{document.getElementById(\"c103-mount\").innerHTML=\"<p>The CPI script did not start. No number was filled in. <a href=\\\"/calendar/\\\">Calendar</a></p>\";}</script><noscript><p>Figures load in the browser from the stored release. Nothing is estimated while that is off. <a href=\"https://www.bls.gov/cpi/\">U.S. Bureau of Labor Statistics CPI</a>.</p></noscript>";
    const shell = {
      title: "CPI day | The Dispatch Market",
      path: "/cpi/",
      desc: "US CPI in UK time: the next release, headline and core, and a 24-month trend. Category weights and gold futures after past releases are for members.",
      user: reader.user,
      extraHead: "<link rel=\"canonical\" href=\"" + origin + "/cpi/\"><meta property=\"og:title\" content=\"CPI day | The Dispatch Market\"><meta property=\"og:description\" content=\"US CPI in UK time, with the source and the release date on every figure.\">",
      body: body
    };
    const html = typeof c93Shell === "function" ? c93Shell(shell) : "<!doctype html><title>CPI day | The Dispatch Market</title>" + body;
    if (typeof c93Html === "function") return c93Html(req, res, html, "private, max-age=60");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "private, max-age=60", "X-Content-Type-Options": "nosniff" });
    res.end(req.method === "HEAD" ? undefined : html);
  }
  async function api(req, res) {
    const reader = await readerOf(req);
    const model = c103ForNow(await read(), Date.now());
    let dismissals = [];
    if (reader.signedIn) {
      try { dismissals = await c103Deadline(c103LoadDismissals(depsOf(), reader.userId), 400); }
      catch (e) { dismissals = []; }
    }
    return send(res, 200, c103Respond(model, reader, dismissals));
  }
  async function dismiss(req, res) {
    const reader = await readerOf(req);
    if (!reader.signedIn) return send(res, 401, { error: "Sign in required" }, "no-store");
    const stored = store.get("model");
    const known = ((stored && stored.body && stored.body.previousEvents) || []).map((ev) => ev.releaseAtUtc).filter(Boolean);
    const gate = c103DismissGate(req, String((await c103Peek(req)).releaseKey || ""), known, c103Install.limiter, Date.now(), reader.userId);
    if (!gate.ok) return send(res, gate.status, { ok: false, error: gate.error }, "no-store");
    try { await c103SaveDismissal(depsOf(), reader.userId, gate.key); }
    catch (e) { return send(res, 200, { ok: false, statusNote: "not loaded yet" }, "no-store"); }
    return send(res, 200, { ok: true, releaseKey: gate.key }, "no-store");
  }
  if (typeof handle === "function" && !handle.__c103) {
    const prev = handle;
    const wrapped = async function (req, res) {
      try {
        if (typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON) return prev.apply(this, arguments);
        let u = null;
        try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { u = null; }
        const p = u ? u.pathname : "";
        if (req.method === "GET" || req.method === "HEAD") {
          if (p === "/cpi") { res.writeHead(301, { Location: "/cpi/" }); return res.end(); }
          if (p === "/cpi/") return page(req, res);
          if (p === "/api/c103/cpi") return api(req, res);
        }
        if (req.method === "POST" && p === "/api/c103/notice/dismiss") return dismiss(req, res);
      } catch (e) { console.error("[c103]", e && e.message); }
      return prev.apply(this, arguments);
    };
    wrapped.__c103 = 1;
    handle = wrapped;
  }
  if (typeof renderPublicSitemap === "function" && !renderPublicSitemap.__c103) {
    const prevMap = renderPublicSitemap;
    const wrappedMap = async function () {
      let x = await prevMap.apply(this, arguments);
      const origin = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
      if (typeof x !== "string" || x.indexOf("</urlset>") < 0 || x.indexOf(origin + "/cpi/") >= 0) return x;
      return x.replace("</urlset>", "  <url><loc>" + origin + "/cpi/</loc><changefreq>daily</changefreq><priority>0.7</priority></url>\n</urlset>");
    };
    wrappedMap.__c103 = 1;
    renderPublicSitemap = wrappedMap;
  }
  try {
    const warm = setTimeout(() => {
      const deps = depsOf();
      c103EnsureSchema(deps).then(() => c103LoadStored(deps)).then((loaded) => {
        if (loaded && (loaded.latest || (loaded.previousEvents && loaded.previousEvents.length))) store.set("model", { ok: true, at: 0, body: loaded });
      }).catch(() => {}).finally(() => { read().catch(() => {}); });
    }, 50);
    if (warm && typeof warm.unref === "function") warm.unref();
    const recorder = setInterval(() => {
      const deps = depsOf();
      const prev = store.get("model");
      deps.events = prev && prev.body && prev.body.previousEvents;
      c103RecordTick(deps, Date.now()).then((snap) => {
        if (!snap) return;
        deps.snapshots = [snap];
        return c103SaveSnapshot(deps, snap);
      }).catch(() => {});
    }, 60 * 1000);
    if (recorder && typeof recorder.unref === "function") recorder.unref();
  } catch (e) {}
  c103Install.done = 1;
  c103Install._store = store;
}

async function c103EnsureSchema(deps) {
  if (!deps || typeof deps.sql !== "function") return;
  const audit = c103DdlAudit(C103_DDL.join("\n"));
  if (!audit.ok) return;
  for (const stmt of C103_DDL) {
    const one = stmt.match(/create\s+table\s+if\s+not\s+exists\s+([a-z0-9_]+)/i);
    if (!one || C103_TABLES.indexOf(one[1].toLowerCase()) < 0) return;
    if (typeof deps.sql.query === "function") await deps.sql.query(stmt);
    else await deps.sql([stmt]);
  }
}

async function c103LoadDismissals(deps, userId) {
  if (!deps || typeof deps.sql !== "function" || !userId) return [];
  const result = await deps.sql`SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (
    SELECT release_key FROM cpi_notice_dismissals WHERE user_id = ${userId}
  ) t`;
  const rows = result && result[0] && Array.isArray(result[0].data) ? result[0].data : [];
  return rows.map((r) => r.release_key).filter(Boolean);
}

async function c103SaveDismissal(deps, userId, key) {
  if (!deps || typeof deps.sql !== "function") throw new Error("no-db");
  await deps.sql`INSERT INTO cpi_notice_dismissals (user_id, release_key) VALUES (${userId}, ${key}) ON CONFLICT DO NOTHING`;
}

async function c103LoadSnapshots(deps) {
  if (!deps || typeof deps.sql !== "function") return [];
  const result = await deps.sql`SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (
    SELECT release_at, observed_at, price, window_kind, source_label FROM cpi_gold_snapshots
    WHERE release_at >= ${C103_RECORD_FROM} ORDER BY observed_at DESC LIMIT 400
  ) t`;
  const rows = result && result[0] && Array.isArray(result[0].data) ? result[0].data : [];
  return rows.map((r) => ({
    releaseAtUtc: new Date(r.release_at).toISOString(),
    observedAtUtc: new Date(r.observed_at).toISOString(),
    price: Number(r.price),
    windowKind: r.window_kind,
    sourceLabel: C103_GOLD_LABEL
  })).filter((r) => isFinite(r.price));
}

async function c103Persist(deps, model) {
  if (!deps || typeof deps.sql !== "function" || !model) return;
  if (model.snapshotToSave && model.snapshotToSave.price != null) {
    const s = model.snapshotToSave;
    await deps.sql`INSERT INTO cpi_gold_snapshots (release_at, observed_at, price, window_kind, source_label)
      VALUES (${s.releaseAtUtc}, ${s.observedAtUtc}, ${s.price}, ${s.windowKind}, ${C103_GOLD_LABEL})
      ON CONFLICT DO NOTHING`;
  }
  const changed = c103ChangedSeries(deps.knownSeries || {}, model.previousSeries || {});
  const newestStored = c103NewestPeriod([].concat(...Object.keys(deps.knownSeries || {}).map((id) => deps.knownSeries[id] || [])));
  const latest = model.latest;
  const month = latest && latest.period || "none";
  let missingInDb = "";
  if (typeof deps.sql.query === "function") {
    try {
      const found = await deps.sql.query("SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) AS data FROM (SELECT s.period FROM cpi_series_values s WHERE s.series_id = 'CUSR0000SA0' AND s.period = (SELECT MAX(period) FROM cpi_series_values WHERE series_id = 'CUSR0000SA0') AND NOT EXISTS (SELECT 1 FROM cpi_releases r WHERE r.period = s.period) LIMIT 1) t");
      const data = found && found[0] && found[0].data;
      missingInDb = data && data[0] && data[0].period || "";
    } catch (e) { missingInDb = ""; }
  }
  const pending = !!(missingInDb && latest && latest.period === missingInDb);
  model.releaseRowPending = pending;
  const wantRelease = !!(latest && latest.headline && typeof latest.headline.saIndex === "number" && (model.seriesFresh || pending) && (!newestStored || latest.period >= newestStored));
  try {
    if (changed.length && typeof deps.sql.query === "function") {
      await deps.sql.query(
        "INSERT INTO cpi_series_values (series_id, period, value) SELECT series_id, period, value FROM jsonb_to_recordset($1::jsonb) AS x(series_id text, period text, value double precision) ON CONFLICT (series_id, period) DO UPDATE SET value = EXCLUDED.value, fetched_at = NOW() WHERE cpi_series_values.value IS DISTINCT FROM EXCLUDED.value",
        [JSON.stringify(changed.map((row) => ({ series_id: row.series_id, period: row.period, value: c103SqlNum(row.value) })).filter((row) => row.value != null))]
      );
    }
    if (wantRelease && typeof deps.sql.query === "function") {
      await deps.sql.query(
        "INSERT INTO cpi_releases (period, release_at, release_source, reference_label, headline_mom, headline_yoy, core_mom, core_yoy, bls_fetched_at, payload) VALUES ($1, $2, $3, $4, NULLIF($5::text, '')::double precision, NULLIF($6::text, '')::double precision, NULLIF($7::text, '')::double precision, NULLIF($8::text, '')::double precision, $9, $10::jsonb) ON CONFLICT (period) DO UPDATE SET headline_mom = EXCLUDED.headline_mom, headline_yoy = EXCLUDED.headline_yoy, core_mom = EXCLUDED.core_mom, core_yoy = EXCLUDED.core_yoy, bls_fetched_at = EXCLUDED.bls_fetched_at, fetched_at = NOW()",
        [latest.period, latest.releaseAtUtc || null, latest.releaseSource || "stored", latest.periodLabel || null, c103SqlNum(latest.headline.momRounded), c103SqlNum(latest.headline.yoyRounded), c103SqlNum(latest.core && latest.core.momRounded), c103SqlNum(latest.core && latest.core.yoyRounded), latest.fetchedAt && isFinite(Date.parse(latest.fetchedAt)) ? latest.fetchedAt : null, JSON.stringify({ period: latest.period })]
      );
      model.releaseRowPending = false;
      console.log("[c103] persist ok " + month);
    }
  } catch (err) {
    if (wantRelease) model.releaseRowPending = true;
    console.log("[c103] persist fail " + month + " " + (err && err.message || err));
  }
  const goldRows = c103ChangedGold(deps.knownGold || [], model.gold || []);
  if (goldRows.length && typeof deps.sql.query === "function") {
    await deps.sql.query(
      "INSERT INTO cpi_gold_reactions (release_at, reference_period, plus_1h_pct, plus_1d_pct, plus_5d_pct, hourly_available, recorded, hour_label, source_label) SELECT release_at, reference_period, plus_1h_pct, plus_1d_pct, plus_5d_pct, hourly_available, recorded, hour_label, source_label FROM jsonb_to_recordset($1::jsonb) AS x(release_at timestamptz, reference_period text, plus_1h_pct double precision, plus_1d_pct double precision, plus_5d_pct double precision, hourly_available boolean, recorded boolean, hour_label text, source_label text) ON CONFLICT (release_at) DO UPDATE SET plus_1h_pct = COALESCE(EXCLUDED.plus_1h_pct, cpi_gold_reactions.plus_1h_pct), plus_1d_pct = COALESCE(EXCLUDED.plus_1d_pct, cpi_gold_reactions.plus_1d_pct), plus_5d_pct = COALESCE(EXCLUDED.plus_5d_pct, cpi_gold_reactions.plus_5d_pct), hourly_available = cpi_gold_reactions.hourly_available OR EXCLUDED.hourly_available, recorded = EXCLUDED.recorded, hour_label = COALESCE(EXCLUDED.hour_label, cpi_gold_reactions.hour_label), computed_at = NOW()",
      [JSON.stringify(goldRows.map((g) => ({
        release_at: g.releaseAtUtc,
        reference_period: g.referencePeriod || null,
        plus_1h_pct: c103SqlNum(g.plus1hPct),
        plus_1d_pct: c103SqlNum(g.plus1dPct),
        plus_5d_pct: c103SqlNum(g.plus5dPct),
        hourly_available: !!g.hourlyAvailable,
        recorded: !!g.recorded,
        hour_label: g.hourLabel || null,
        source_label: C103_GOLD_LABEL
      })))]
    );
  }
  if (model.previousEvents && model.previousEvents.length && typeof deps.sql.query === "function") {
    const slim = model.previousEvents.map((ev) => ({
      etDate: ev.etDate, startMs: ev.startMs, releaseAtUtc: ev.releaseAtUtc, releaseUk: ev.releaseUk,
      source: ev.source, referencePeriod: ev.referencePeriod, dailyOnly: !!ev.dailyOnly, y: ev.y, m: ev.m, d: ev.d
    }));
    const when = (model.feedTimes && model.feedTimes.schedule) || (model.latest && model.latest.fetchedAt) || null;
    await deps.sql.query(
      "INSERT INTO cpi_releases (period, release_source, bls_fetched_at, payload) VALUES ('__schedule', 'schedule', $2, $1::jsonb) ON CONFLICT (period) DO UPDATE SET payload = EXCLUDED.payload, bls_fetched_at = EXCLUDED.bls_fetched_at",
      [JSON.stringify({ events: slim, fetchedAt: when }), when]
    );
  }
  if (model.blsBudget && typeof deps.sql.query === "function") {
    await deps.sql.query(
      "INSERT INTO cpi_releases (period, release_source, payload) VALUES ('__bls_budget', 'budget', $1::jsonb) ON CONFLICT (period) DO UPDATE SET payload = EXCLUDED.payload, fetched_at = NOW()",
      [JSON.stringify(model.blsBudget)]
    );
  }
}

function c103ChangedSeries(prev, next) {
  const rows = [];
  Object.keys(next || {}).forEach((id) => {
    const have = new Map((prev[id] || []).map((p) => [p.year + "-" + p.month, p.value]));
    (next[id] || []).forEach((p) => {
      if (typeof p.value !== "number") return;
      const key = p.year + "-" + p.month;
      if (have.get(key) === p.value) return;
      rows.push({ series_id: id, period: c103Period(p.year, p.month), value: p.value });
    });
  });
  return rows;
}

function c103ChangedGold(prev, next) {
  const have = new Map((prev || []).map((row) => [row.releaseAtUtc, row]));
  return (next || []).filter((row) => {
    if (!row || !row.releaseAtUtc) return false;
    const old = have.get(row.releaseAtUtc);
    if (!old) return true;
    return old.plus1hPct !== row.plus1hPct || old.plus1dPct !== row.plus1dPct || old.plus5dPct !== row.plus5dPct;
  });
}

const api = {
  C103_GOLD_LABEL, C103_CONTRIB_LABEL, C103_SOURCE, C103_CATALOG, C103_DDL, C103_TABLES, C103_FALLBACK, C103_RECORD_FROM,
  c103Esc, c103ZonedToUtc, c103FormatUk, c103Parts, c103Ymd, c103Round1, c103Pct, c103Contribution,
  c103ParseIcs, c103ParseHtmlSchedule, c103MergeSchedule, c103Countdown, c103ReleaseInstant,
  c103ParseBls, c103ParseRi, c103BuildMonths, c103ParseYahoo, c103GoldReaction, c103ApplySnapshots,
  c103SnapshotDecision, c103Compose, c103Cold, c103Memo, c103Respond, c103IsPremium, c103DdlAudit,
  c103InsertNav, c103Paths, c103RawGet, c103Refresh, c103FetchAll, c103CacheControl, c103Install,
  c103CarryNote, c103NoteWhen, c103SqlNum, c103Persist, c103SeriesGood, c103PickSeries, c103BlsPlan, c103BlsCharge, c103BlsSeriesCap,
  c103CacheMs, c103ForNow, c103DismissGate, c103RecordTick, c103ChangedSeries, c103ParseArchive,
  c103WeightsMatch, c103MergeGold, c103LoadStored,
  c103WorthStoring, c103GoldUrl,
  c103CalendarChange, c103CalendarCpi
};

if (typeof module !== "undefined" && module.exports) module.exports = api;
