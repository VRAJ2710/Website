"use strict";

const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const EM = "\u2014";
const ROOT = path.join(__dirname, "..");
const APPLY = path.join(ROOT, "scripts", "apply_synced_quote_layer_replit.py");

const APP_FIXTURE = String.raw`
function resolveInternalTicker(raw) {
  const s = String(raw || "").toUpperCase();
  if (s === "GC=F") return "XAU";
  if (s === "CL=F") return "WTI";
  return s;
}
function _quoteMeta(tk) {
  tk = resolveInternalTicker(tk) || tk;
  if (!liveSymbols.has(tk)) return { status: "unavailable", label: "NO SYNC", asOf: null, src: null };
  const src = liveQuoteSrc[tk] || "";
  if (String(src).startsWith("gold-api-spot-proxy")) return { status: "proxy", label: "SPOT PROXY", asOf: 1, src };
  if (src === "frankfurter-ecb") return { status: "proxy", label: "SYNTH·DXY", asOf: 1, src };
  if (src === "yahoo") return { status: "delayed", label: "DELAYED", asOf: 1, src };
  if (src === "session-cache") return { status: "cached", label: "CACHED", asOf: 1, src };
  if (src === "twelve-data") return { status: "live", label: "LIVE·TD", asOf: 1, src };
  return { status: "unavailable", label: "NO SYNC", asOf: null, src };
}
function isPrimaryLiveQuote(tk) { return _quoteMeta(tk).status === "live"; }
function hasSyncedQuote(tk) {
  tk = (typeof resolveInternalTicker === "function" && resolveInternalTicker(tk)) || tk;
  const p = P[tk] && P[tk].p;
  return typeof p === "number" && isFinite(p) && p > 0 && _quoteMeta(tk).status !== "unavailable";
}
function fp(tk) {
  tk = resolveInternalTicker(tk) || tk;
  const meta = _quoteMeta(tk);
  const row = P[tk];
  if (!row || typeof row.p !== "number") return { p: "${EM}", c: "${EM}", status: "unavailable", label: meta.label || "NO SYNC", asOf: null, d: 0 };
  return { p: row.p.toFixed(2), c: Number(row.c || 0).toFixed(2), status: meta.status, label: meta.label, asOf: meta.asOf, d: row.c > 0 ? 1 : row.c < 0 ? -1 : 0 };
}
function _escHtml(s) { return String(s == null ? "" : s); }
function _fmtAsOf() { return "14:39"; }
let liveQuoteName = {};

function _getRegimeState() {
  const nosync = { p: "${EM}", c: "${EM}", d: 0, status: "unavailable" };
  const vix = isPrimaryLiveQuote("VIX") ? fp("VIX") : nosync;
  // Prefer live index; SPY is the ETF proxy when ^GSPC not synced this session
  let spx = nosync, spxProxy = null;
  if (isPrimaryLiveQuote("SPX")) {
    spx = fp("SPX");
  } else if (isPrimaryLiveQuote("SPY")) {
    spx = fp("SPY");
    spxProxy = "SPY";
  }
  let id = "risk-on-fragile", label = "Risk-On (Fragile)";
  const q = (tk) => isPrimaryLiveQuote(tk) ? fp(tk) : nosync;
  const dxy = q("DXY"), oil = q("WTI"), gold = q("XAU"), btc = q("BTC");
  return { id, label, spx: spx.p, spxChg: spx.c, spxProxy, vix: vix.p, dxy: dxy.p, oil: oil.p, gold: gold.p, btc: btc.p };
}
function _liveTapeBit(label, ...tks) {
  for (const tk of tks) {
    if (!isPrimaryLiveQuote(tk)) continue;
    const d = fp(tk);
    if (d.status === "unavailable") continue;
    const c = liveChg(tk);
    const chg = c != null ? " (" + (c >= 0 ? "+" : "") + Number(c).toFixed(2) + "%)" : "";
    return label + " " + d.p + chg;
  }
  return null;
}
/** Raw numeric price only when a qualifying live feed confirms it — never seed, delayed, cached, stale, or proxy. */
function livePx(tk) {
  if (!isPrimaryLiveQuote(tk)) return null;
  const p = P[tk]?.p;
  return typeof p === "number" && isFinite(p) && p > 0 ? p : null;
}
function liveChg(tk) {
  if (!isPrimaryLiveQuote(tk)) return null;
  if (typeof liveQuoteChangeAvailable !== "undefined" && liveQuoteChangeAvailable[tk] === false) return null;
  const c = P[tk]?.c;
  return typeof c === "number" && isFinite(c) ? c : null;
}
function _frontDoorQuote(tk, name, description) {
  const px = referencePx(tk);
  const ch = referenceChg(tk);
  const meta = _quoteMeta(tk);
  const price = px != null ? fp(tk).p : "no print";
  const change = ch != null ? \`\${ch >= 0 ? "+" : ""}\${Number(ch).toFixed(2)}%\` : "";
  const referenceName = tk === "XAU"
    ? (liveQuoteName.XAU || "Spot Gold (proxy)")
    : tk === "DXY"
      ? (liveQuoteName.DXY || "Synthetic Dollar Index (proxy)")
      : meta.label;
  const provenance = meta.status === "unavailable"
    ? \`NO SYNC · \${referenceName}\`
    : \`\${meta.label} · \${referenceName}\`;
  return '<div class="front-door-quote"><div class="front-door-quote-value">' + price + (change ? " " + change : "") + '</div><div class="front-door-quote-meta">' + provenance + '</div></div>';
}
function referencePx() { return null; }
function referenceChg() { return null; }
async function _fetchLivePrices(){
  if(pg==="home"){ try{ _refreshHomeAfterPrices(); }catch(e){} }
  else if(pg==="brief"){ try{ renderMain(); }catch(e){} }
}
function _goldHeroChangeAnchor() {
  const px = livePxN != null ? livePxN : g.price;
  const chg = g.changePct;
}
const _hero = '<span>DXY <b>\${d.macro?.dxy?.px != null ? d.macro.dxy.px : "${EM}"}</b></span>';
const _kv = '<div class="gd-kv"><span>DXY</span><b>\${d.macro?.dxy?.px != null ? d.macro.dxy.px : "${EM}"} <span class="\${(d.macro?.dxy?.chg||0)>=0?"px-up":"px-dn"}">\${d.macro?.dxy?.chg != null ? _gdChg(d.macro.dxy.chg) : ""}</span></b></div>';
`;

function applyTo(dir) {
  const run = spawnSync("python3", [APPLY, dir], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  return run.stdout;
}

test("synced quote layer uses hasSyncedQuote for proxy, delayed, and futures aliases", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "synced-quote-"));
  fs.writeFileSync(path.join(dir, "app.js"), APP_FIXTURE.replace(/\\\$/g, "$").replace(/\\`/g, "`"));
  fs.writeFileSync(path.join(dir, "index.html"), "var V='TD-pricefix10';\n<script defer src=\"/app.js?v=pricefix10\"></script>\n");
  applyTo(dir);
  const app = fs.readFileSync(path.join(dir, "app.js"), "utf8");
  const index = fs.readFileSync(path.join(dir, "index.html"), "utf8");
  assert.match(app, /function livePx\(tk\) \{\s*const key = \(typeof resolveInternalTicker/);
  assert.match(app, /if \(!hasSyncedQuote\(key\)\) return null;/);
  assert.doesNotMatch(app, /function livePx\(tk\) \{\s*if \(!isPrimaryLiveQuote/);
  assert.match(app, /hasSyncedQuote\("VIX"\)/);
  assert.match(app, /hasSyncedQuote\(tk\) \? fp\(tk\)/);
  assert.match(app, /if \(!hasSyncedQuote\(tk\)\) continue;/);
  assert.match(app, /const synced = hasSyncedQuote\(tk\);/);
  assert.doesNotMatch(app, /const px = referencePx\(tk\);/);
  assert.match(app, /_refreshBriefSurfaces\(\)/);
  assert.match(app, /livePx\("DXY"\)/);
  assert.match(app, /liveChg\("XAU"\)/);
  assert.match(index, /TD-pricefix11/);
  assert.match(index, /app\.js\?v=pricefix11/);
  applyTo(dir);

  const context = {
    P: {
      XAU: { p: 4178.8, c: 0.33 },
      DXY: { p: 101.73, c: 0.01 },
      VIX: { p: 18.2, c: -1.1 },
    },
    liveSymbols: new Set(["XAU", "DXY", "VIX"]),
    liveQuoteSrc: {
      XAU: "gold-api-spot-proxy",
      DXY: "frankfurter-ecb",
      VIX: "yahoo",
    },
    liveQuoteChangeAvailable: { XAU: true, DXY: true, VIX: true },
    liveQuoteName: { XAU: "Spot Gold (proxy)", DXY: "Synthetic Dollar Index (proxy)" },
  };
  vm.createContext(context);
  vm.runInContext(app, context);
  assert.equal(context.isPrimaryLiveQuote("XAU"), false);
  assert.equal(context.isPrimaryLiveQuote("DXY"), false);
  assert.equal(context.livePx("XAU"), 4178.8);
  assert.equal(context.livePx("GC=F"), 4178.8);
  assert.equal(context.P["GC=F"], undefined);
  assert.equal(context.livePx("DXY"), 101.73);
  assert.equal(context.liveChg("XAU"), 0.33);
  assert.equal(context.liveChg("DXY"), 0.01);
  assert.equal(context.livePx("VIX"), 18.2);
  assert.equal(context.livePx("MU"), null);
  const regime = context._getRegimeState();
  assert.equal(regime.gold, "4178.80");
  assert.equal(regime.dxy, "101.73");
  assert.equal(regime.vix, "18.20");
  assert.match(context._liveTapeBit("Gold", "XAU"), /4178\.80/);
  assert.match(context._liveTapeBit("DXY", "DXY"), /101\.73/);
  assert.match(context._liveTapeBit("VIX", "VIX"), /18\.20/);
  const goldDoor = context._frontDoorQuote("XAU", "GOLD", "spot proxy");
  assert.match(goldDoor, /4178\.80/);
  assert.match(goldDoor, /SPOT PROXY/);
  assert.doesNotMatch(goldDoor, /no print/);
  const dollarDoor = context._frontDoorQuote("DXY", "DOLLAR", "ICE index");
  assert.match(dollarDoor, /101\.73/);
  assert.match(dollarDoor, /SYNTH·DXY/);
  assert.equal(context.livePx("NONE"), null);
  const empty = context._frontDoorQuote("NONE", "NONE", "none");
  assert.match(empty, /no print/);
  assert.match(empty, /NO SYNC/);
});
