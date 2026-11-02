// ── chat100b ──
// 1) Gold change vs the previous close on every gold row (Market context on /, /gold/ and /brief/, the dashboard
//    macro tiles and the gold dashboard). Free sources only: Yahoo Finance's delayed chart for COMEX gold futures (front
//    month) and the pound in dollars give the previous close. Fallback when Yahoo has no previous close: the last
//    gold-api.com spot reading we saved on the previous UK day, kept in the existing dispatch_openbb_research_cache
//    table (key c100b:gold-day, no new tables, no DDL). With neither, the row says "Change not available yet".
// 2) About: founder card with photo, "Edited by Vraj Patel, London" and a LinkedIn link, on the guest page and in the app.
//    Photo drop-in: put the image at the file below (next to server.js) and restart. LinkedIn: change the one line below.
const C100B_FOUNDER_PHOTO_FILE = "assets/founder.webp";                                  // photo file, relative to server.js
const C100B_FOUNDER_LINKEDIN = "https://www.linkedin.com/company/thedispatchmarket";     // swap for a personal profile URL
const C100B_FOUNDER_LINKEDIN_LABEL = /linkedin\.com\/in\//.test(C100B_FOUNDER_LINKEDIN) ? "Vraj Patel on LinkedIn" : "The Dispatch Market on LinkedIn";
const C100B_PHOTO_URL = "/" + C100B_FOUNDER_PHOTO_FILE.replace(/^\/+/, "");
let c100bYqImpl = null;                                                                     // test hook only
const C100B_OZ_G = 31.1034768;
const C100B_FUT = "vs previous close, gold futures (COMEX, front month), Yahoo Finance, delayed";
const C100B_FUT_GBP = "vs previous close, gold futures (COMEX, front month) in pounds at the pound's own previous close, Yahoo Finance, delayed";
const C100B_SNAP = "vs our last saved gold-api.com spot price on the previous UK day";
let c100bDay = null;                                                                        // { day, usd, gbp, at } today's latest spot reading
let c100bPrevDay = null;                                                                    // the previous UK day's last reading
let c100bSaveAt = 0, c100bLoaded = false;
function c100bTsMs(t) { const n = Number(t); return !isFinite(n) || n <= 0 ? Date.now() : (n < 1e12 ? n * 1000 : n); }
async function c100bLoadSnap() {
  if (c100bLoaded) return; c100bLoaded = true;
  try { if (!c96StoreOk()) return; const v = await c96Get("c100b:gold-day"); if (v && typeof v === "object") { if (v.prev) c100bPrevDay = v.prev; if (v.cur) c100bDay = c100bDay || v.cur; } } catch (e) {}
}
async function c100bNoteSpot(usd, gbp) {                                                     // called on each good spot read
  if (!(usd > 0)) return;
  await c100bLoadSnap();
  const now = Date.now(), day = c97UkIso(now);
  if (c100bDay && c100bDay.day !== day) { c100bPrevDay = c100bDay; c100bSaveAt = 0; }
  c100bDay = { day, usd, gbp: gbp > 0 ? gbp : null, at: now };
  if (now - c100bSaveAt < 15 * 60e3) return;
  c100bSaveAt = now;
  try { if (c96StoreOk()) await c96Put("c100b:gold-day", { cur: c100bDay, prev: c100bPrevDay }); } catch (e) {}
}
function c100bMk(now, prev, basis, ms) { const chg = now - prev; return { price: now, prev, chg, pct: (now / prev - 1) * 100, basis, asOfUk: c97UkWhen(ms), asOfMs: ms }; }
async function c100bGoldChange() {
  const c = await c97Cached("c100b:goldchg", 2 * 60e3, async () => {
    let Q = {};
    try { Q = (await withTimeout((c100bYqImpl || yahooQuote)(["GC=F", "GBPUSD=X"]), 7000, "timeout")) || {}; } catch (e) { Q = {}; }
    const g = Q["GC=F"], f = Q["GBPUSD=X"], ok = x => x && Number(x.p) > 0 && Number(x.prev) > 0;
    const out = { available: false, usd: null, gbp: null };
    if (ok(g)) {
      const gms = c100bTsMs(g.ts);
      out.usd = c100bMk(Number(g.p), Number(g.prev), C100B_FUT, gms);
      if (ok(f)) out.gbp = c100bMk(Number(g.p) / Number(f.p), Number(g.prev) / Number(f.prev), C100B_FUT_GBP, Math.min(gms, c100bTsMs(f.ts)));
    }
    await c100bLoadSnap();
    const pd = c100bPrevDay, cd = c100bDay;
    if (pd && cd && pd.day !== cd.day && Date.now() - pd.at < 4 * 864e5) {                    // fallback: our own saved spot readings
      const ms = cd.at;
      if (!out.usd && pd.usd > 0 && cd.usd > 0) out.usd = c100bMk(cd.usd, pd.usd, C100B_SNAP + " (" + c97UkWhen(pd.at) + ")", ms);
      if (!out.gbp && pd.gbp > 0 && cd.gbp > 0) out.gbp = c100bMk(cd.gbp, pd.gbp, C100B_SNAP + " (" + c97UkWhen(pd.at) + ")", ms);
    }
    out.available = !!(out.usd || out.gbp);
    return out;
  }, 8000);
  return c.v || { available: false, usd: null, gbp: null };
}
function c100bMoney(v, cur, dp) { const n = Number(v); if (!isFinite(n)) return ""; return (n > 0 ? "+" : n < 0 ? "\u2212" : "") + cur + Math.abs(n).toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }); }
function c100bChgText(x, cur, div) { return x ? c100bMoney(x.chg / (div || 1), cur, 2) + " (" + c97Sg(x.pct, 2, "%") + ")" : "Change not available yet"; }
function c100bNum(s) { const n = Number(String(s || "").replace(/[^0-9.]/g, "")); return n > 0 ? n : null; }
// Gold dashboard rows (also feeds the dashboard macro tiles): add the change to gold in $, £ and €.
{
  const c100bGd0 = c97GoldDash;
  c97GoldDash = async function () {
    const d = await c100bGd0.apply(this, arguments);
    if (!d || !d.rows || !d.rows.gold_usd) return d;
    let c = null; try { c = await c100bGoldChange(); } catch (e) {}
    try { await c100bNoteSpot(c100bNum(d.rows.gold_usd.value), d.rows.gold_gbp ? c100bNum(d.rows.gold_gbp.value) : null); } catch (e) {}
    const rows = Object.assign({}, d.rows);
    const eurUsd = (() => { const m = /euro in dollars \(([\d.]+)/.exec((rows.gold_eur && rows.gold_eur.source) || ""); return m ? Number(m[1]) : null; })();
    const add = (k, x, cur) => {
      if (!rows[k]) return; const r = Object.assign({}, rows[k]);
      if (x) { r.change = c100bChgText(x, cur); r.changePct = x.pct; r.changeBasis = "Change " + x.basis + ", " + x.asOfUk; r.changeNote = (/previous UK day/.test(x.basis) ? "vs previous UK day" : "vs previous close") + ", " + x.asOfUk; r.source = r.source + "; change " + x.basis; }
      else { r.change = "Change not available yet"; r.changePct = null; r.changeBasis = "No previous close yet"; r.changeNote = ""; }
      rows[k] = r;
    };
    add("gold_usd", c && c.usd, "$");
    add("gold_gbp", c && c.gbp, "\u00a3");
    if (rows.gold_eur) {                                                                   // the US$ change converted at today's euro rate; % is the dollar move
      const x = c && c.usd && eurUsd > 0 ? Object.assign({}, c.usd, { chg: c.usd.chg / eurUsd, basis: c.usd.basis + ", converted to euros at today's rate" }) : null;
      add("gold_eur", x, "\u20ac");
    }
    return Object.assign({}, d, { rows });
  };
}
// ── About: founder card ──
const c100bFs = require("fs"), c100bPath = require("path");
let c100bPhoto = { at: 0, buf: null, tag: "" };
function c100bPhotoGet() {
  const now = Date.now(); if (now - c100bPhoto.at < 5 * 60e3) return c100bPhoto;
  c100bPhoto.at = now;
  try { const f = c100bPath.join(__dirname, C100B_FOUNDER_PHOTO_FILE); const b = c100bFs.statSync(f).isFile() ? c100bFs.readFileSync(f) : null;
    if (b && b.length > 100 && b.length < 3e6) { c100bPhoto.buf = b; c100bPhoto.tag = require("crypto").createHash("sha256").update(b).digest("hex").slice(0, 12); } else { c100bPhoto.buf = null; c100bPhoto.tag = ""; }
  } catch (e) { c100bPhoto.buf = null; c100bPhoto.tag = ""; }
  return c100bPhoto;
}
function c100bPhotoSrc() { const p = c100bPhotoGet(); return p.buf ? C100B_PHOTO_URL + "?v=" + p.tag : ""; }
const C100B_LI_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" width="15" height="15"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13zm1.78 13.02H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>';
const C100B_ED_CSS = `.c100b-ed{display:flex;gap:20px;align-items:center;margin:22px 0 26px;padding:20px 22px;border:1px solid #d8d2c4;border-radius:10px;background:linear-gradient(180deg,#fffdf8,#f6f2e8)}
.c100b-ph{flex:0 0 112px;width:112px;height:112px;border-radius:50%;padding:3px;background:linear-gradient(140deg,#b08a3e,#e6d3a3)}
.c100b-ph img{display:block;width:106px;height:106px;border-radius:50%;object-fit:cover;background:#fff}
.c100b-fd{min-width:0}.c100b-k{font:600 11px/1.2 Inter,system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#8a6a2c;margin:0 0 6px}
.c100b-nm{font:600 28px/1.15 "Source Serif 4",Georgia,serif;margin:0;color:#1b1b1b}
.c100b-by{font:600 15px/1.4 Inter,system-ui,sans-serif;margin:6px 0 8px;color:#3b3b3b}
.c100b-bio{margin:0 0 12px;font-size:15px;line-height:1.5;color:#4a4a4a;max-width:560px}
.c100b-li{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 14px;border:1px solid #0a66c2;border-radius:6px;color:#0a66c2;font:600 14px/1 Inter,system-ui,sans-serif;text-decoration:none}
.c100b-li:hover{background:#0a66c2;color:#fff}.c100b-li:focus-visible{outline:2px solid #2563eb;outline-offset:2px}
.c100b-vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (max-width:560px){.c100b-ed{flex-direction:column;align-items:flex-start;gap:14px;padding:18px}.c100b-nm{font-size:25px}}
html.c97-dark .c100b-ed{border-color:#3a4552;background:linear-gradient(180deg,#18202a,#141a22)}html.c97-dark .c100b-nm{color:#eef2f6}html.c97-dark .c100b-by{color:#d3dae2}html.c97-dark .c100b-bio{color:#b9c3ce}html.c97-dark .c100b-k{color:#d9b46a}html.c97-dark .c100b-li{border-color:#70b5f9;color:#9ccdfc}html.c97-dark .c100b-li:hover{background:#70b5f9;color:#0f141a}
@media (prefers-color-scheme:dark){html.c97-system .c100b-ed{border-color:#3a4552;background:linear-gradient(180deg,#18202a,#141a22)}html.c97-system .c100b-nm{color:#eef2f6}html.c97-system .c100b-by{color:#d3dae2}html.c97-system .c100b-bio{color:#b9c3ce}html.c97-system .c100b-k{color:#d9b46a}html.c97-system .c100b-li{border-color:#70b5f9;color:#9ccdfc}}`;
const C100B_UPDN_CSS = `.c100b-up{color:#15803d}.c100b-dn{color:#b91c1c}html.c97-dark .c100b-up{color:#4ade80}html.c97-dark .c100b-dn{color:#f87171}@media (prefers-color-scheme:dark){html.c97-system .c100b-up{color:#4ade80}html.c97-system .c100b-dn{color:#f87171}}`;
function c100bEditorCard() {
  const ph = c100bPhotoSrc();
  return `<style>${C100B_ED_CSS}\n${C100B_UPDN_CSS}</style><section class="c100b-ed" aria-labelledby="c100b-nm">` +
    (ph ? `<div class="c100b-ph"><img src="${c93Esc(ph)}" alt="Vraj Patel" width="106" height="106" decoding="async"></div>` : "") +
    `<div class="c100b-fd"><p class="c100b-k">Founder and editor</p><h2 class="c100b-nm" id="c100b-nm">Vraj Patel</h2><p class="c100b-by">${c93Esc(C93_EDITOR)}</p>` +
    `<p class="c100b-bio">Vraj founded The Dispatch Market to give independent investors a careful, sourced read on gold and macro. He writes the research and builds the site himself.</p>` +
    `<a class="c100b-li" href="${c93Esc(C100B_FOUNDER_LINKEDIN)}" target="_blank" rel="noopener noreferrer">${C100B_LI_SVG}${c93Esc(C100B_FOUNDER_LINKEDIN_LABEL)}<span class="c100b-vh"> (opens in a new tab)</span></a></div></section>`;
}
try {
  const ab = C93_PAGES["/about"], f0 = ab && ab[2];
  if (typeof f0 === "function") ab[2] = function () {
    let h = String(f0.apply(this, arguments));
    h = h.replace(/^<figure[\s\S]*?<\/figure>/, "");                                     // the old optional photo slot
    return h.replace(`<p class="byline">${C93_EDITOR}</p>`, () => c100bEditorCard());
  };
} catch (e) {}
// Gold dashboard table: change cells green/red by sign, with a short note on what the change is measured against.
{
  c97Tbl = function (rows) {
    return `<table class="c97t c97r"><thead><tr><th scope="col">Measure</th><th scope="col">Reading</th><th scope="col">Change</th><th scope="col">Source and time</th></tr></thead><tbody>` +
      rows.filter(Boolean).map(r => { const ch = String(r.change || ""), cl = /^\+\S/.test(ch) ? ' class="c100b-up"' : /^[\u2212-]\S/.test(ch) ? ' class="c100b-dn"' : "";
        return `<tr><td><strong>${c93Esc(r.label)}</strong><span class="c97p">${c93Esc(r.plain || "")}</span></td><td class="v">${c93Esc(r.value)}</td><td${cl}>${c93Esc(ch)}${r.changeNote ? `<span class="c97s">${c93Esc(r.changeNote)}</span>` : ""}</td><td><span class="c97s">${c93Esc(r.source)}</span><span class="c97s">${c93Esc(r.asOf || "")}</span></td></tr>`; }).join("") + `</tbody></table>`;
  };
}
{
  const c100bTr0 = c97Transform;
  c97Transform = function (html, req) {
    let out = c100bTr0(html, req);
    if (typeof out !== "string" || out.indexOf('id="c100b-js"') >= 0 || !/<\/body>/i.test(out)) return out;
    const app = out.indexOf('id="aboutOv"') >= 0;
    const cfg = `window.C100B_FOUNDER=${JSON.stringify({ photo: c100bPhotoSrc(), li: C100B_FOUNDER_LINKEDIN, liLabel: C100B_FOUNDER_LINKEDIN_LABEL }).replace(/</g, "\\u003c")};`;
    if (!app && out.indexOf('class="c100b-ed"') < 0) out = out.replace(/<\/head>/i, `<style id="c100b-css">${C100B_UPDN_CSS}</style></head>`);
    return out.replace(/<\/body>(?![\s\S]*<\/body>)/i, `<script id="c100b-js">${cfg}</script></body>`);
  };
}
{
  const c100bI0 = bb10iHandle0;
  bb10iHandle0 = async function c100bInner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (p === "/api/c100b/gold-change" && req.method === "GET") {
      try { const c = await c100bGoldChange(); return json(res, 200, c, { "Cache-Control": "public, max-age=60" }); }
      catch (e) { return json(res, 200, { available: false, usd: null, gbp: null }, { "Cache-Control": "no-store" }); }
    }
    if (p === C100B_PHOTO_URL && (req.method === "GET" || req.method === "HEAD")) {
      const ph = c100bPhotoGet();
      if (!ph.buf) { res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" }); return res.end("Not found"); }
      res.writeHead(200, { "Content-Type": /\.png$/i.test(p) ? "image/png" : /\.jpe?g$/i.test(p) ? "image/jpeg" : "image/webp", "Content-Length": ph.buf.length, "Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff" });
      return res.end(req.method === "HEAD" ? undefined : ph.buf);
    }
    return c100bI0.apply(this, arguments);
  };
}
