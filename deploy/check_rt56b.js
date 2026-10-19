#!/usr/bin/env node
"use strict";
/* Lunch break. The resume clock is Europe/London, computed from the venue window.
   A server closed, stale, delayed or quiet status wins over the calendar.
   A lunch flag or a note that says lunch is the server's own signal. */
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt56b/in/app.js";
const src = fs.readFileSync(appPath, "utf8");
const at = src.indexOf("// fe66b-pure-begin");
const end = src.indexOf("// fe66b-pure-end");
if (at < 0 || end < 0) throw new Error("missing fe66b helpers");

function parts(tz, d) {
  const o = {};
  new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d).forEach(x => { o[x.type] = x.value; });
  return { wd: o.weekday, m: (Number(o.hour) % 24) * 60 + Number(o.minute) };
}
function uk(ms) {
  const p = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms));
  let h = "", mi = "";
  p.forEach(x => { if (x.type === "hour") h = x.value; if (x.type === "minute") mi = x.value; });
  return h + ":" + mi;
}

const ctx = {
  A: [
    { tk: "7203.T", ex: "TSE", cat: "Stock", _rt43: true },
    { tk: "0700.HK", ex: "HKEX", cat: "Stock", _rt43: true },
    { tk: "600519.SS", ex: "SSE", cat: "Stock" },
    { tk: "000001.SZ", ex: "SZSE", cat: "Stock" }
  ],
  fe66b_cal: {
    TSE: ["Asia/Tokyo", 540, 930, 690, 750],
    HKEX: ["Asia/Hong_Kong", 570, 960, 720, 780],
    SSE: ["Asia/Shanghai", 570, 900, 690, 780],
    SZSE: ["Asia/Shanghai", 570, 900, 690, 780],
    LSE: ["Europe/London", 480, 990],
    KRX: ["Asia/Seoul", 540, 930]
  },
  _rt18Parts: parts,
  fe64_ukHm: uk
};
vm.createContext(ctx);
vm.runInContext(src.slice(at, end), ctx);

const TSE_LUNCH = Date.parse("2026-10-19T03:00:00Z");
const TSE_BEFORE = Date.parse("2026-10-19T02:29:00Z");
const TSE_START = Date.parse("2026-10-19T02:30:00Z");
const TSE_END = Date.parse("2026-10-19T03:30:00Z");
const TSE_WINTER = Date.parse("2026-01-15T02:45:00Z");
const HK_LUNCH = Date.parse("2026-10-19T04:30:00Z");
const HK_BEFORE = Date.parse("2026-10-19T03:59:00Z");
const HK_START = Date.parse("2026-10-19T04:00:00Z");
const HK_END = Date.parse("2026-10-19T05:00:00Z");
const HK_NOTE = "Hong Kong market closed (day after Chung Yeung) · opens Tue 02:30 UK";
const PHRASE = "Lunch break · resumes ";

let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("ok", msg);
  else { failed++; console.error("FAIL", msg); }
}

ok(ctx.fe66b_text("7203.T", { status: "fresh" }, TSE_LUNCH) === PHRASE + "04:30 UK", "TSE lunch in BST resumes 04:30 UK");
ok(ctx.fe66b_text("7203.T", { status: "live" }, TSE_START) === PHRASE + "04:30 UK", "TSE lunch starts at 11:30 JST");
ok(ctx.fe66b_text("7203.T", { status: "fresh" }, TSE_BEFORE) === "", "TSE just before lunch stays open");
ok(ctx.fe66b_text("7203.T", { status: "fresh" }, TSE_END) === "", "TSE at 12:30 JST is the afternoon session");
ok(ctx.fe66b_text("7203.T", { status: "fresh" }, TSE_WINTER) === PHRASE + "03:30 UK", "TSE lunch in winter resumes 03:30 UK");
ok(ctx.fe66b_text("7203.T", null, TSE_LUNCH) === PHRASE + "04:30 UK", "missing status uses the calendar");
ok(ctx.fe66b_text("7203.T", {}, TSE_LUNCH) === PHRASE + "04:30 UK", "empty bag uses the calendar");

ok(ctx.fe66b_text("0700.HK", { status: "fresh" }, HK_LUNCH) === PHRASE + "06:00 UK", "HKEX lunch resumes 06:00 UK");
ok(ctx.fe66b_text("0700.HK", { status: "open" }, HK_START) === PHRASE + "06:00 UK", "HKEX lunch starts at 12:00 HKT");
ok(ctx.fe66b_text("0700.HK", { status: "fresh" }, HK_BEFORE) === "", "HKEX just before lunch");
ok(ctx.fe66b_text("0700.HK", { status: "fresh" }, HK_END) === "", "HKEX at 13:00 HKT is the afternoon session");

ok(ctx.fe66b_text("0700.HK", { status: "closed", note: HK_NOTE }, HK_LUNCH) === "", "closed holiday wins during HKEX lunch");
ok(ctx.fe66b_text("7203.T", { status: "closed", note: "Tokyo market closed · opens 04:30 UK" }, TSE_LUNCH) === "", "closed wins during TSE lunch");
ok(ctx.fe66b_text("7203.T", { status: "stale", note: "This price is not current." }, TSE_LUNCH) === "", "stale wins");
ok(ctx.fe66b_text("7203.T", { status: "delayed", delayMin: 15 }, TSE_LUNCH) === "", "delayed wins");
ok(ctx.fe66b_text("7203.T", { status: "quiet", note: "Quiet" }, TSE_LUNCH) === "", "quiet wins");
ok(ctx.fe66b_text("7203.T", { status: "fresh" }, Date.parse("2026-10-17T03:00:00Z")) === "", "weekend is not a lunch break");

ok(ctx.fe66b_text("7203.T", { status: "closed", lunch: true, nextOpen: "2026-10-19T03:30:00.000Z" }, Date.parse("2026-10-19T08:00:00Z")) === PHRASE + "04:30 UK", "server lunch flag uses nextOpen");
ok(ctx.fe66b_text("0700.HK", { status: "closed", note: "Lunch break on HKEX", nextOpen: "2026-10-19T05:00:00.000Z" }, Date.parse("2026-10-19T12:00:00Z")) === PHRASE + "06:00 UK", "server lunch note uses nextOpen");
ok(ctx.fe66b_text("7203.T", { status: "fresh", session: "lunch" }, TSE_WINTER) === PHRASE + "03:30 UK", "session lunch still computes the winter clock");

ok(ctx.fe66b_text("600519.SS", { status: "fresh" }, Date.parse("2026-10-19T04:00:00Z")) === PHRASE + "06:00 UK", "SSE lunch window from the calendar");
ok(ctx.fe66b_text("000001.SZ", { status: "fresh" }, Date.parse("2026-10-19T03:29:00Z")) === "", "SZSE before its lunch");
ok(ctx.fe66b_text("000001.SZ", { status: "fresh" }, Date.parse("2026-10-19T04:00:00Z")) === PHRASE + "06:00 UK", "SZSE lunch");
ok(ctx.fe66b_text("HSBA.L", { status: "fresh" }, TSE_LUNCH) === "", "a venue without a lunch window stays quiet");

ok(src.indexOf("var fe66b_cal = H;") >= 0, "lunch windows come from the venue calendar");
ok(src.indexOf("fe64_quoteApply = function") >= 0 && src.indexOf("fe66b_applyMeta") >= 0, "the fe64 formatter applies the lunch line");
ok(src.indexOf('s==="lunch"') >= 0, "status pill reads the lunch line");
ok(src.indexOf("lunchBadge") >= 0, "glance badge reads the lunch line");
ok(/app\.js\?v=chat68/.test(fs.readFileSync(appPath.replace(/app\.js$/, "index.html"), "utf8")), "cache bust chat68");

if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("rt56b fixture passed");
