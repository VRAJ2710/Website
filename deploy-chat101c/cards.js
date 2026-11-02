// market-context rows: counts of data points, sources, dates and Delayed labels, and how many are visible, at a width.
const pp = require("/workspace/c97/shot/node_modules/puppeteer-core");
const B = "http://127.0.0.1:8852";
module.exports = async function cards(b, w, dark, pth, shot) {
  const ctx = await b.createBrowserContext(); const p = await ctx.newPage();
  await p.setViewport({ width: w, height: 844 });
  if (dark) await p.setCookie({ name: "dispatch_theme", value: "dark", domain: "127.0.0.1", path: "/" });
  await p.goto(B + pth, { waitUntil: "networkidle2" }); await new Promise(r => setTimeout(r, 1500));
  const r = await p.evaluate(() => {
    const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
    const T = e => (e ? e.textContent : "").replace(/\s+/g, " ").trim();
    const out = { rows: 0, values: 0, changes: 0, sources: 0, dates: 0, delayed: 0, vValues: 0, vChanges: 0, vSources: 0, vDates: 0, vDelayed: 0, heads: [], overflow: [], codes: [], names: [] };
    const dateRe = /\b(\d{1,2} [A-Z][a-z]{2}( \d{4})?|\d{1,2}:\d{2})\b/;
    document.querySelectorAll("table.ctx").forEach(t => {
      const tr = t.getBoundingClientRect();
      t.querySelectorAll("tbody tr").forEach(row => {
        if (row.classList.contains("c101c-gh")) { if (vis(row)) out.heads.push(T(row)); return; }
        const c = row.cells; out.rows++; out.names.push(c[0].firstChild ? c[0].firstChild.textContent : T(c[0]));
        const srcEls = [c[0].querySelector(".msrc"), row.querySelector("td.src")];
        const st = T(c[3] || c[0].querySelector(".msrc"));
        if (T(c[1])) { out.values++; if (vis(c[1])) out.vValues++; }
        if (T(c[2])) { out.changes++; if (vis(c[2])) out.vChanges++; }
        if (st) { out.sources++; if (srcEls.some(vis)) out.vSources++; }
        if (dateRe.test(st)) { out.dates++; if (srcEls.some(e => vis(e) && dateRe.test(T(e)))) out.vDates++; }
        if (/Delayed/.test(st)) { out.delayed++; if (srcEls.some(e => vis(e) && /Delayed/.test(T(e)))) out.vDelayed++; }
        [...c].forEach(td => { if (!vis(td)) return; const r = td.getBoundingClientRect(); if (r.right > document.documentElement.clientWidth + 1 || td.scrollWidth > td.clientWidth + 1) out.overflow.push(T(td).slice(0, 40)); });
        if (/\b[A-Z]{1,5}=F\b|\^[A-Z]{2,}|\b[A-Z]{3,6}-USD\b/.test(T(row))) out.codes.push(T(row).slice(0, 60));
        // card shape below 600px: value right of name on line 1, change below value, source below both
        if (innerWidth < 600 && vis(c[1])) {
          const n = c[0].getBoundingClientRect(), v = c[1].getBoundingClientRect(), ch = c[2].getBoundingClientRect(), s = (row.querySelector("td.src") || c[0]).getBoundingClientRect();
          const okShape = Math.abs(n.top - v.top) < 4 && v.left > n.left && (!T(c[2]) || (ch.top >= v.bottom - 1 && Math.abs(ch.right - v.right) < 2)) && s.top >= Math.max(n.bottom, v.bottom, T(c[2]) ? ch.bottom : 0) - 1;
          if (!okShape) out.overflow.push("shape:" + T(c[0]).slice(0, 30));
          const cs = getComputedStyle(c[1]); if (cs.textAlign !== "right" || !/tabular-nums/.test(cs.fontVariantNumeric)) out.overflow.push("align:" + T(c[0]).slice(0, 30));
        }
      });
    });
    out.sw = document.documentElement.scrollWidth; out.cw = document.documentElement.clientWidth;
    out.signs = [...document.querySelectorAll("table.ctx td.n.up, table.ctx td.n.down")].map(td => [td.className.includes("up") ? "up" : "down", T(td).charAt(0), getComputedStyle(td).color]);
    return out;
  });
  if (shot) { const el = await p.$("table.ctx"); if (el) await el.screenshot({ path: shot }); }
  await ctx.close(); return r;
};
if (require.main === module) (async () => {
  const b = await pp.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  const o = {}; for (const pth of ["/", "/gold/"]) for (const w of [320, 390, 1280]) o[pth + " " + w] = await module.exports(b, w, false, pth);
  console.log(JSON.stringify(o)); await b.close();
})();
