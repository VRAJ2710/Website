// chat101c harness test: menu is a full-screen sheet (Menu and All sections) with an X, one column of dropdown groups,
// only the current page's group open, Admin Console admin-only (incl. cached pages, never in preview), market cards CSS/JS. PORT default 8852.
const P = process.env.PORT || "8852", B = "http://127.0.0.1:" + P;
let pass = 0, fail = 0; const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 300))); };
const get = (p, u, extra) => fetch(B + p, { redirect: "manual", headers: { cookie: [u ? "dispatch_session=" + u : "", extra || ""].filter(Boolean).join("; ") } });
const txt = async (p, u, extra) => { const r = await get(p, u, extra); return { s: r.status, b: await r.text() }; };
const GROUPS = ["Start", "Desk", "Markets", "Research", "Book", "Gold and macro", "Tools and filings", "About", "Account"];
const REQ = ["Home", "Brief", "Playbook", "Gold", "Dashboard", "Market Lab", "Signals", "Markets", "Screener", "Sectors", "Heatmap", "Crypto", "Newsroom", "Paper", "Research", "Documents", "Geo Ops", "Watchlist", "Portfolio", "Learn", "Settings", "Calendar", "What changed today", "Yields", "Gold positioning", "Alerts", "Portfolio X-ray", "Data status", "Tools", "Verify this claim", "ISA/SIPP planner", "Central banks", "Scenario simulator", "Filing change detector", "About", "Pricing"];
const hdr = b => (/<header class="site">[\s\S]*?<\/header>/.exec(b) || [""])[0];
const sheets = h => [...h.matchAll(/<nav class="c101c-sheet"[\s\S]*?<\/nav>/g)].map(m => m[0]);
const DISC = /Not investment advice\. Capital at risk\./;
(async () => {
  await get("/__h/c99reset?all=1"); await get("/__h/c99cnt?n=0");
  const WANT = { "/": -1, "/gold/": 0, "/tools/verify/": 6, "/about": 7, "/what-changed/": 5, "/central-banks/": 5, "/brief/": 0, "/tools/": 6 };
  for (const [pg, want] of Object.entries(WANT)) for (const u of [null, "hmember", "hadmin"]) {
    const r = await txt(pg, u), h = hdr(r.b), who = u || "guest";
    if (!h) { ok(r.s === 200 && /app\.js\?v=chat101c"/.test(r.b), `${pg} ${who} opens in the app with v=chat101c`, r.s); continue; }
    const S = sheets(h);
    ok(S.length === 2, `${pg} ${who} two sheets (All sections + Menu)`, S.length);
    ok(/<details class="c101b-all"><summary>All sections<\/summary><nav class="c101c-sheet"/.test(h) && /<details class="menu"><summary aria-label="Menu: all sections">Menu<\/summary><nav class="c101c-sheet"/.test(h), `${pg} ${who} both buttons open a sheet`);
    const ids = [...h.matchAll(/ id="([^"]+)"/g)].map(m => m[1]); ok(new Set(ids).size === ids.length, `${pg} ${who} unique ids`, ids.filter((x, i) => ids.indexOf(x) !== i).join(","));
    for (const [i, s] of S.entries()) {
      const nm = `${pg} ${who} sheet${i}`;
      ok(/<button type="button" class="c101c-x" aria-label="Close menu">/.test(s), `${nm} X with aria-label`);
      const heads = [...s.matchAll(/<button type="button" class="c101c-btn" id="([^"]+)" aria-expanded="(true|false)" aria-controls="([^"]+)"><span class="c101c-t">([^<]+)<\/span>/g)];
      ok(heads.map(m => m[4].replace("&amp;", "&")).join("|") === GROUPS.join("|"), `${nm} nine dropdown headings in order`, heads.map(m => m[4]).join("|"));
      ok(heads.every(m => new RegExp(`<ul id="${m[3]}" aria-labelledby="${m[1]}"${m[2] === "true" ? ">" : " hidden>"}`).test(s)), `${nm} aria-controls/labelledby/hidden in step`);
      const open = heads.map((m, j) => m[2] === "true" ? j : -1).filter(j => j >= 0);
      ok(want < 0 ? open.length === 0 : open.length === 1 && open[0] === want, `${nm} default open = ${want < 0 ? "none" : GROUPS[want]}`, open.join(","));
      const L = [...s.matchAll(/<a [^>]*>([^<]+)<\/a>/g)].map(m => m[1].replace("&amp;", "&")), miss = REQ.filter(l => !L.includes(l));
      ok(!miss.length, `${nm} all ${REQ.length} sections`, miss.join(","));
      ok(s.indexOf('class="c101c-top"') < s.indexOf('class="c101c-acc"') && /<p class="c101c-note">Some pages are for signed-in readers or members/.test(s) && s.indexOf("c101c-note") > s.lastIndexOf("</ul>"), `${nm} primary action at top, note at bottom`);
      ok(new RegExp(u ? ">Your desk<" : ">Sign in<").test(s.slice(0, s.indexOf("c101c-acc"))), `${nm} ${u ? "Your desk" : "Sign in"} at top`);
      const adm = /href="\/__admin"/.test(s), acct = (/data-c101c-acct=""><span class="c101c-vh">, <\/span>(\d)</.exec(s) || [])[1];
      ok(u === "hadmin" ? adm && acct === "2" : !adm && acct === "1", `${nm} Admin Console ${u === "hadmin" ? "shown (count 2)" : "hidden (count 1)"}`, adm + " " + acct);
      for (const m of heads) { const ul = (new RegExp(`<ul id="${m[3]}"[^>]*>([\\s\\S]*?)</ul>`).exec(s) || [, ""])[1]; const n = (ul.match(/<li>/g) || []).length; const c = +(new RegExp(`id="${m[1]}"[\\s\\S]*?c101c-n[^>]*><span class="c101c-vh">, </span>(\\d+)`).exec(s) || [])[1]; if (n !== c) ok(false, `${nm} ${m[4]} count ${c} vs ${n}`); }
    }
    ok(DISC.test(r.b), `${pg} ${who} disclaimer`);
    ok(!/<details[^>]*>(?:(?!<\/details>)[\s\S])*<details/.test(h), `${pg} ${who} no nested details`);
  }
  // cached pages: guest first, then admin, then member again; admin in preview never sees the console
  for (const pg of ["/gold/", "/about", "/"]) {
    const seq = [[null, ""], ["hadmin", ""], ["hmember", ""], ["hadmin", "dispatch_preview=1"], [null, ""]];
    for (const [u, ex] of seq) { const h = hdr((await txt(pg, u, ex)).b); if (!h) continue; const adm = (h.match(/href="\/__admin"/g) || []).length, want = u === "hadmin" && !ex ? 2 : 0;
      ok(adm === want, `cache ${pg} ${u || "guest"}${ex ? "+preview" : ""} admin links ${want}`, adm); }
  }
  // CSS/JS present: full-screen sheet, lock, X, market cards, group headings
  const h = (await txt("/about")).b;
  ok(/nav\.c101c-sheet\{position:fixed;inset:0/.test(h) || /nav\.c101c-sheet\{[^}]*position:fixed/.test(h), "sheet CSS position:fixed full screen");
  ok(/c101c-lock/.test(h) && /overflow:hidden!important/.test(h), "scroll-lock CSS");
  ok(/@media \(max-width:599px\)\{table\.ctx/.test(h) && /tabular-nums/.test(h), "market-card CSS below 600px, tabular figures");
  ok(/window\.__c101c/.test(h) && /c101c-gh/.test(h), "market group-heading script");
  const home = (await txt("/")).b; ok(/<table class="ctx/.test(home) || /table\.ctx/.test(home), "home has the market-context table");
  // app
  const app = (await txt("/app.js?v=chat101c")).b;
  ok(/chat101c: calmer menu/.test(app) && /aria-label="Close menu"/.test(app) && /c101c-sheet/.test(app), "app.js: sheet with X");
  ok(/_userAdmin === true && !window\._tdMePreview/.test(app), "app.js: Admin Console admin-only, never in preview");
  const ih = (await txt("/dashboard/", "hmember")).b; ok(/\/app\.js\?v=chat101c"/.test(ih), "index.html loads app.js?v=chat101c", (ih.match(/app\.js\?v=\w+/) || [])[0]);
  await txt("/about"); // warm the shared guest cache, then a member must get "Your desk" in every account button
  for (const pg of ["/about", "/", "/tools/verify/"]) { const h = hdr((await txt(pg, "hmember")).b), c = [...h.matchAll(/class="cta" href="([^"]+)"/g)].map(m => m[1]);
    ok(c.length >= 3 && c.every(x => x === "/dashboard/"), `member ${pg}: every account button is "Your desk"`, c.join(",")); }
  for (const pg of ["/about", "/tools/verify/"]) { const h = hdr((await txt(pg, "hadmin", "dispatch_preview=1")).b), c = [...h.matchAll(/class="cta" href="([^"]+)"/g)].map(m => m[1]);
    ok(c.length >= 3 && c.every(x => x === "/__auth/login"), `admin preview ${pg}: account buttons stay "Sign in"`, c.join(",")); }
  console.log(`\nchat101c: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.log("FAIL crash " + (e && e.stack)); process.exit(1); });
