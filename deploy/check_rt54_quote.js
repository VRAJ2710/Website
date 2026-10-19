#!/usr/bin/env node
/* Mocked badge check for the chat64 quote wrappers.
   7a: delayed, stale, fresh, absent, closed, closed without a note, quiet FX.
   7b: CoinGecko stale headers, and a reply with no headers.
   Reads the helpers out of deploy/patch_rt54.py. Does not start the server. */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const py = fs.readFileSync(path.join(__dirname, "patch_rt54.py"), "utf8");
const a = py.indexOf("// fe64-quote-begin");
const b = py.indexOf("// fe64-quote-end");
if (a < 0 || b < a) {
  console.error("FAIL: quote helpers are not marked in patch_rt54.py");
  process.exit(1);
}
const ctx = { console, Date, Intl, Object, String, Number, Math, isFinite, JSON, Promise };
vm.createContext(ctx);
vm.runInContext(py.slice(a, b), ctx);

let n = 0;
function ok(cond, msg) {
  if (!cond) {
    console.error("FAIL:", msg);
    process.exit(1);
  }
  n += 1;
}
const aged = { status: "stale", label: "STALE", detail: "Feed tick 5h old", asOf: Date.now() - 5 * 3600e3, src: "yahoo", ageMs: 5 * 3600e3 };

ctx.fe64_keepYq("BP", { status: "delayed", delayMin: 15, note: "delayed 15m by exchange" });
let out = ctx.fe64_quoteApply("BP", aged);
ok(out.status === "delayed" && out.label === "delayed 15m by exchange" && !/stale/i.test(out.status + out.label), "delayed note, not stale");
ok(ctx.fe64_allowAgeStale("BP") === false, "delayed is not aged");

ctx.fe64_keepYq("SHEL", { status: "delayed", delayMin: 15 });
out = ctx.fe64_quoteApply("SHEL", aged);
ok(out.status === "delayed" && out.label === "delayed 15m by exchange", "delayed without a note uses the minutes");

ctx.fe64_keepYq("GLEN", { status: "stale", note: "last copy" });
out = ctx.fe64_quoteApply("GLEN", { status: "delayed", label: "DELAYED 1m", detail: "Yahoo Finance · delayed data", src: "yahoo", asOf: Date.now() });
ok(out.status === "stale" && out.label === "STALE" && out.detail === "This price is not current.", "stale shows STALE");

ctx.fe64_keepYq("NVDA", { status: "fresh" });
const live = { status: "live", label: "LIVE·YS", detail: "Yahoo Finance public stream", src: "yahoo-stream", asOf: Date.now() };
ok(ctx.fe64_quoteApply("NVDA", live) === live, "fresh live label is unchanged");
out = ctx.fe64_quoteApply("NVDA", aged);
ok(out.status === "live" && out.label === "LIVE" && out.status !== "stale", "fresh aged quote shows a live label");

ctx.fe64_keepYq("MU", { p: 88 });
ok(ctx.fe64_quoteApply("MU", aged) === aged, "absent status keeps today's result");
ok(ctx.fe64_allowAgeStale("MU") === true && ctx.fe64_allowAgeStale("NONE") === true, "absent still ages the way it does today");

ctx.fe64_keepYq("AAPL", { status: "closed", note: "US market closed · opens 14:30 UK", nextOpen: "2026-01-16T14:30:00.000Z" });
out = ctx.fe64_quoteApply("AAPL", aged);
ok(out.status === "closed" && out.label === "CLOSED" && out.fe64Note === "US market closed · opens 14:30 UK", "closed shows CLOSED plus the note");
ok(!/stale/i.test(out.status + out.label + out.detail), "closed is never stale");
ok(ctx.fe64_allowAgeStale("AAPL") === false, "closed is not aged");

ctx.fe64_keepYq("MSFT", { status: "closed", nextOpen: "2026-07-01T13:30:00.000Z" });
out = ctx.fe64_quoteApply("MSFT", aged);
ok(out.status === "closed" && out.label === "CLOSED" && out.fe64Note === "opens 14:30 UK", "closed without a note builds opens HH:MM UK");

ctx.fe64_keepYq("USDSEK", { status: "fresh", note: "quiet · local market opens 08:00 UK" });
out = ctx.fe64_quoteApply("USDSEK", aged);
ok(out.status !== "stale" && out.label === "quiet · local market opens 08:00 UK" && out.detail === out.label, "quiet FX shows the note");
ok(ctx.fe64_allowAgeStale("USDSEK") === false, "quiet FX is not aged");

ctx.fe64_keepYq("EURUSD", { status: "closed", note: "quiet · local market opens 07:00 UK" });
out = ctx.fe64_quoteApply("EURUSD", aged);
ok(out.status === "closed" && out.label === "CLOSED" && out.fe64Note === "quiet · local market opens 07:00 UK", "closed beats a quiet note");

ok(ctx.fe64_quoteApply("AAPL", aged).status === "closed", "AAPL stays closed");
ok(ctx.fe64_quoteApply("USDSEK", aged).label.indexOf("quiet") === 0, "USDSEK stays on its own note");
ok(ctx.fe64_quoteApply("MU", aged) === aged, "MU is untouched by the other names");

function headers(map, body) {
  return {
    headers: { get: function (name) { return Object.prototype.hasOwnProperty.call(map, name) ? map[name] : null; } },
    json: function () { return Promise.resolve(body); }
  };
}
const body = { bitcoin: { usd: 1 } };
const stale = headers({ "X-Dispatch-Data-Status": "stale", "X-Dispatch-As-Of": "2026-07-01T13:30:00.000Z" }, body);
ctx.fe64_cgRead(stale, "markets");
ok(ctx.fe64_cgAsOf("markets") === "as of 14:30 UK", "stale CoinGecko uses X-Dispatch-As-Of");
const oldHdr = headers({ "X-Dispatch-Data-Status": "stale", "X-Dispatch-Data-As-Of": "2026-01-15T14:30:00.000Z" }, body);
ctx.fe64_cgRead(oldHdr, "global");
ok(ctx.fe64_cgAsOf("global") === "as of 14:30 UK", "older as-of header still labels the block");
const both = headers({
  "X-Dispatch-Data-Status": "stale",
  "X-Dispatch-As-Of": "2026-07-01T13:30:00.000Z",
  "X-Dispatch-Data-As-Of": "2026-07-01T12:00:00.000Z"
}, body);
ctx.fe64_cgRead(both, "simple");
ok(ctx.fe64_cgAsOf("simple") === "as of 14:30 UK", "X-Dispatch-As-Of wins when both timestamps are present");
const fresh = headers({ "X-Dispatch-Data-Status": "fresh", "X-Dispatch-As-Of": "2026-07-01T13:30:00.000Z" }, body);
ctx.fe64_cgRead(fresh, "fresh");
ok(ctx.fe64_cgAsOf("fresh") === "", "fresh CoinGecko gets no as-of label");
const bare = headers({}, body);
ctx.fe64_cgRead(bare, "bare");
ok(ctx.fe64_cgAsOf("bare") === "", "no headers leaves the label off");

Promise.all([stale.json(), bare.json()]).then(function (parts) {
  ok(parts[0] === body && parts[1] === body, "header read leaves the JSON body alone");
  console.log("OK", n, "quote and CoinGecko checks");
}).catch(function (e) {
  console.error("FAIL", e);
  process.exit(1);
});
