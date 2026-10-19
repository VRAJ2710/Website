#!/usr/bin/env node
"use strict";
/* status, note, nextOpen and delayMin survive a later quote and a chart close.
   One formatter paints them. The venue calendar runs only when status is missing.
   Visible copy has no cached·yh, raw minute age, or proxy. */
const fs = require("fs");
const vm = require("vm");
const appPath = process.argv[2] || "/tmp/rt55/out/app.js";
const src = fs.readFileSync(appPath, "utf8");

function grab(name) {
  const at = src.indexOf("function " + name);
  if (at < 0) throw new Error("missing " + name);
  let i = src.indexOf("{", at), n = 0, q = "";
  for (; i < src.length; i++) {
    const c = src[i];
    if (q) { if (c === "\\") { i++; continue; } if (c === q) q = ""; continue; }
    if (c === "'" || c === '"' || c === "`") { q = c; continue; }
    if (c === "{") n++;
    else if (c === "}" && --n === 0) return src.slice(at, i + 1);
  }
  throw new Error("unclosed " + name);
}
function between(a, b) {
  const i = src.indexOf(a), j = src.indexOf(b);
  if (i < 0 || j < 0) throw new Error("missing markers " + a);
  return src.slice(i + a.length, j);
}
const openAt = Date.parse("2026-10-19T05:00:00Z"); // 06:00 UK (BST)
const calAt = Date.parse("2026-10-19T07:00:00Z"); // 08:00 UK, must not replace a server bag
const ctx = {
  OPEN: { MU: true, AAPL: false, COFFEE: false, "0700.HK": false, XAU: true },
  NEXT: { COFFEE: calAt, AAPL: calAt, "0700.HK": openAt, XAU: calAt },
  resolveInternalTicker: t => t,
  _rt18MarketOpen: tk => ctx.OPEN[tk] !== false,
  _rt51Next: tk => ctx.NEXT[tk] || 0,
  _fmtAsOf: () => "Fri 21:00"
};
vm.createContext(ctx);
ctx._rt18MarketOpen = tk => ctx.OPEN[tk] !== false;
ctx._rt51Next = tk => ctx.NEXT[tk] || 0;
const names = ["fe64_yqKey", "fe64_keepYq", "fe64_yqBag", "fe64_plainNote", "fe64_ukHm", "fe64_closedWords", "fe64_delayWords", "fe64_freshUndo", "fe64_quoteApply"];
vm.runInContext(names.map(grab).join("\n") + "\n" + between("// fe65-quote-begin", "// fe65-quote-end"), ctx);

let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("ok", msg);
  else { failed++; console.error("FAIL", msg); }
}
function bag(tk) { return ctx.fe64_yqBag(tk); }
function show(tk, meta) { return ctx.fe65_finishQuote(tk, Object.assign({ src: "yahoo", asOf: 1 }, meta)); }
function noBad(s, msg) {
  const t = String(s || "");
  ok(!/cached\s*[·.\-]?\s*yh|\bproxy\b|\b\d+\s*m\b/i.test(t), msg + " :: " + t);
}

ctx.fe64_keepYq("MU", { status: "closed", note: "opens 14:30 UK", nextOpen: openAt, delayMin: 15 });
ctx.fe64_keepYq("MU", { p: 10 });
ok(bag("MU") && bag("MU").status === "closed" && bag("MU").note === "opens 14:30 UK" && bag("MU").delayMin === 15, "later quote keeps the bag");
const mu = show("MU", { status: "stale", label: "STALE · 16m", detail: "STALE · 16m" });
ok(mu.status === "closed" && mu.label === "CLOSED" && /opens 14:30 UK/.test(mu.fe64Note), "closed bag uses the server note");
ok(!/08:00/.test(mu.fe64Note || ""), "closed bag does not use the venue calendar");
noBad(mu.label + " " + mu.detail + " " + mu.fe64Note, "MU visible");

ctx.fe64_keepYq.map = Object.create(null);
const soft = show("COFFEE", { status: "stale", label: "STALE · 3947m", detail: "Feed tick 3947m old" });
ok(soft.status === "closed" && soft.label === "CLOSED" && /opens 08:00 UK/.test(soft.fe64Note + " " + soft.detail), "missing status uses the venue calendar");
noBad(soft.label + " " + soft.detail + " " + soft.fe64Note, "softs visible");

const liveStale = show("NVDA", { status: "stale", label: "STALE · 21m", detail: "Last good copy 21m" });
ok(liveStale.status === "stale" && liveStale.label === "STALE", "open venue stale has no minute count");
noBad(liveStale.label + " " + liveStale.detail, "NVDA visible");

const cached = show("SPY", { status: "cached", label: "CACHED·YH", detail: "CACHED·YH" });
ok(cached.label === "CACHED" && !/yh/i.test(cached.label + cached.detail), "cached yh is gone");

ctx.OPEN.XAU = true;
const gold = show("XAU", { status: "proxy", label: "SPOT PROXY", detail: "Spot Gold (proxy)", src: "gold-api-spot-proxy-browser" });
ok(/Gold/.test(gold.detail) && !/proxy/i.test(gold.label + " " + gold.detail + " " + (gold.fe64Note || "")), "gold has no proxy wording");

ctx.fe64_keepYq("AAPL", { status: "closed", note: "", nextOpen: openAt, delayMin: 0 });
const aapl = show("AAPL", { status: "closed", label: "CLOSED", detail: "Market closed — last close Fri 21:00" });
ok(/opens 06:00 UK/.test(aapl.fe64Note + " " + aapl.detail) && !/last close/.test(aapl.detail), "twelve-data style close includes the opening time");

ctx.fe64_keepYq("0700.HK", { status: "closed", note: "opens 06:00 UK", nextOpen: openAt });
const hk = show("0700.HK", { status: "stale", label: "STALE · 16m" });
ok(hk.status === "closed" && /opens 06:00 UK/.test(hk.fe64Note), "HK uses the server bag");
ok(ctx.fe65_tapeWords(hk).indexOf("STALE") < 0 && ctx.fe65_tapeWords(hk).indexOf("16m") < 0, "tape words follow the bag");
ok(ctx.fe65_tapeName("XAU") === "Gold", "tape name is Gold");
const hkHead = ctx.fe65_feedLbl({ status: "closed", label: "CLOSED", fe64Note: "opens 06:00 UK" }, "0700.HK");
ok(hkHead === "CLOSED · opens 06:00 UK", "closed header keeps the opening note without a last close");
ok(hkHead.indexOf("DELAYED") < 0, "closed header is not DELAYED");
ok(ctx.fe65_feedLbl({ status: "closed", label: "CLOSED", fe64Note: "opens 14:30 UK" }, "MU") === "CLOSED · opens 14:30 UK", "MU header includes the opening time");
ok(src.indexOf("const feedLbl = fe65_feedLbl(d, a.tk);") >= 0, "analysis header uses the formatter");
ok(src.indexOf("const feedLbl=fe65_feedLbl(d, a.tk);") >= 0, "live header uses the formatter");
ok(src.indexOf("const lbl = fe65_feedLbl(d, t);") >= 0, "feed pill uses the formatter");
ok(src.indexOf('d.label||"PROXY"') < 0 && src.indexOf('d.label||"free feed"') >= 0, "proxy pill says free feed");

ok(src.indexOf("else delete fe64_keepYq.map[key]") < 0, "keepYq no longer deletes a bag");
["status:d.status,note:d.note,nextOpen:d.nextOpen,delayMin:d.delayMin", "status:q.status, note:q.note, nextOpen:q.nextOpen, delayMin:q.delayMin", "if (m && m.status) fe65q.status = m.status", "fe64_keepYq(tk, o)", "if (bag && bag.status) fe65o.status = bag.status"].forEach(bit => {
  ok(src.indexOf(bit) >= 0, "route keeps status: " + bit.slice(0, 42));
});
ok(src.indexOf("Prices come from free market feeds; some are delayed.") >= 0, "one markets line");
ok(src.indexOf("Dispatch live/free fallback remains") < 0, "dispatch fallback sentence is gone");
ok(src.indexOf('app.js?v=chat65') >= 0 || fs.readFileSync(appPath.replace(/app\.js$/, "index.html"), "utf8").indexOf("chat65") >= 0, "cache bust chat65");

if (failed) { console.error(failed + " failed"); process.exit(1); }
console.log("quote fixture passed");
