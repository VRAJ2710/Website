// chat101b harness test: every core section is back in the site header ("All sections") and the mobile Menu,
// every link resolves to a working page, gates for guests, Admin Console only for the admin. PORT default 8852.
const fs = require("fs");
const P = process.env.PORT || "8852", B = "http://127.0.0.1:" + P;
let pass = 0, fail = 0; const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 300))); };
const ck = (u, extra) => [u ? "dispatch_session=" + u : "", extra || ""].filter(Boolean).join("; ");
const get = (p, u, extra) => fetch(B + p, { redirect: "manual", headers: { cookie: ck(u, extra) } });
const txt = async (p, u, extra) => { const r = await get(p, u, extra); return { s: r.status, h: r.headers, b: await r.text() }; };
const DISC = /Not investment advice\. Capital at risk\./, LON = /Vraj Patel,\s*London/i, RAW = /GC=F/;
const vis = h => h.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "").replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ");
// the required list (label -> path)
const REQ = [["Home", "/"], ["Brief", "/brief/"], ["Playbook", "/playbook/"], ["Gold", "/gold/"], ["Dashboard", "/dashboard/"], ["Market Lab", "/lab/"], ["Signals", "/signals/"],
  ["Markets", "/markets/"], ["Screener", "/screener/"], ["Sectors", "/sectors/"], ["Heatmap", "/heatmap/"], ["Crypto", "/crypto/"], ["Newsroom", "/news/"], ["Paper", "/paper/"],
  ["Research", "/research/"], ["Documents", "/documents/"], ["Geo Ops", "/geo/"], ["Watchlist", "/watchlist/"], ["Portfolio", "/portfolio/holdings/"], ["Learn", "/learn/"], ["Settings", "/settings/"],
  ["Calendar", "/calendar/"], ["What changed today", "/what-changed/"], ["Yields", "/markets/yields/"], ["Gold positioning", "/gold/positioning/"], ["Alerts", "/alerts/"], ["Portfolio X-ray", "/portfolio/"],
  ["Data status", "/data-status/"], ["Tools", "/tools/"], ["Verify this claim", "/tools/verify/"], ["ISA/SIPP planner", "/tools/isa-sipp/"], ["Central banks", "/central-banks/"],
  ["Scenario simulator", "/tools/scenario/"], ["Filing change detector", "/research/filing-changes/"], ["About", "/about"], ["Pricing", "/pricing"]];
const USERS = [null, "hmember", "hprem", "hadmin"];
const hdr = b => { const m = /<header class="site">[\s\S]*?<\/header>/.exec(b); return m ? m[0] : ""; };
const hrefs = h => [...h.matchAll(/<a [^>]*href="([^"#]+)"[^>]*>([^<]*)/g)].map(m => [m[2].trim(), m[1]]);
async function resolve(p, u) { // follow up to 4 redirects; return final status + body
  let cur = p, s, b = "", loc;
  for (let i = 0; i < 5; i++) { const r = await get(cur, u); s = r.status; b = await r.text(); loc = r.headers.get("location");
    if (s >= 300 && s < 400 && loc) { cur = loc.startsWith("http") ? loc.replace(/^https?:\/\/[^/]+/, "") : loc; continue; } break; }
  return { s, b, final: cur };
}
(async () => {
  await get("/__h/c99reset?all=1"); await get("/__h/c99cnt?n=0");
  // 1. server header on several server pages: every required item in the panel and in the mobile Menu, per user
  const PAGES = ["/brief/", "/gold/", "/markets/", "/tools/", "/what-changed/", "/about"];
  for (const pg of PAGES) for (const u of USERS) {
    const r = await txt(pg, u), h = hdr(r.b), who = u || "guest";
    if (r.s === 200 && !h && u && /\/app\.js\?v=chat101[bc]"/.test(r.b)) { ok(true, `${pg} ${who} opens in the app (menu checked in app.js)`); continue; }
    ok(r.s === 200 && h, `${pg} ${who} 200 with site header`, r.s);
    const panel = (/<details class="c101b-all">[\s\S]*?<\/details>/.exec(h) || [""])[0], menu = (/<details class="menu">[\s\S]*?<\/details>/.exec(h) || [""])[0];
    ok(/<summary[^>]*>All sections<\/summary>/.test(panel), `${pg} ${who} desktop 'All sections' button`);
    ok(/<summary[^>]*>Menu<\/summary>/.test(menu), `${pg} ${who} mobile Menu`);
    for (const [part, nm] of [[panel, "desktop"], [menu, "mobile"]]) {
      const L = hrefs(part), miss = REQ.filter(([l, p]) => !L.some(([l2, p2]) => l2 === l && p2 === p));
      ok(!miss.length, `${pg} ${who} ${nm}: all ${REQ.length} core sections present`, miss.map(x => x.join(" ")).join(", "));
    }
    for (const t of ["Brief", "Gold", "Calendar", "Markets", "Research"]) ok(new RegExp('<nav class="nav"[^]*?>' + t + "</a>").test(h), `${pg} ${who} top link ${t} kept`);
    const adm = /\/__admin|data-c101b-admin|Admin Console/.test(h);
    ok(u === "hadmin" ? adm : !adm, `${pg} ${who} Admin Console ${u === "hadmin" ? "shown" : "not shown"}`);
    ok(DISC.test(vis(r.b)), `${pg} ${who} disclaimer visible`);
    ok(!LON.test(r.b) && !RAW.test(vis(r.b)), `${pg} ${who} no London byline, no raw codes`);
  }
  // admin in preview mode sees what a guest sees
  { const h = hdr((await txt("/brief/", "hadmin", "dispatch_preview=1")).b); ok(h && !/\/__admin|data-c101b-admin/.test(h), "admin in guest preview: no Admin Console"); }
  // 2. every header link resolves to a working page, for every user
  const all = new Map(); for (const u of USERS) for (const [l, p] of hrefs(hdr((await txt("/tools/", u)).b))) all.set(p, l);
  ok(all.size >= REQ.length && all.has("/__admin"), "link list collected (incl. admin)", all.size);
  for (const u of USERS) for (const [p, l] of all) {
    if (p === "/__admin" && u !== "hadmin") continue;
    if (p.startsWith("/__auth/")) continue;
    const r = await resolve(p, u), who = u || "guest";
    ok(r.s === 200 && r.b.length > 800 && !/<title>[^<]*(Not found|404)/i.test(r.b), `${who} ${l} ${p} -> ${r.final} works`, r.s + " " + r.b.length);
  }
  // 3. gates and redirects
  for (const [p, open, word] of [["/documents/", "intel", "Documents"], ["/portfolio/holdings/", "port", "Portfolio"]]) {
    let r = await txt(p); ok(r.s === 200 && /Sign in/i.test(vis(r.b)) && /\/pricing|plans/i.test(r.b) && new RegExp(word).test(vis(r.b)) && DISC.test(vis(r.b)), `${p} guest gets a sign-in gate`, r.s);
    ok(/no-store/.test(r.h.get("cache-control") || ""), `${p} gate no-store`, r.h.get("cache-control"));
    r = await txt(p, "hadmin", "dispatch_preview=1"); ok(r.s === 200 && /Sign in/i.test(vis(r.b)), `${p} admin preview gets the gate`, r.s);
    for (const u of ["hmember", "hprem", "hadmin"]) { const g = await get(p, u); ok(g.status === 302 && g.headers.get("location") === "/?open=" + open, `${p} ${u} -> /?open=${open}`, g.status + " " + g.headers.get("location")); }
    const n = await get(p.replace(/\/$/, "")); ok(n.status === 301 && n.headers.get("location") === p, `${p} no-slash 301`, n.status);
  }
  { const g = await get("/settings/"); ok(g.status === 302 && /^\/\?settings=1/.test(g.headers.get("location") || ""), "/settings/ -> /?settings=1", g.status + " " + g.headers.get("location")); }
  { const r = await txt("/what-changed/"); ok(r.s === 200 && /What changed today/.test(vis(r.b)) && DISC.test(vis(r.b)) && /Edited by Vraj Patel/.test(r.b), "/what-changed/ renders"); }
  // 4. the app (signed-in pages) carries the same list and the renamed button
  const app = (await txt("/app.js?v=chat101b")).b, idx = (await txt("/", "hmember", "")).b;
  ok(/chat101b: all sections/.test(app), "app.js has the chat101b menu");
  const miss = REQ.filter(([l, p]) => !app.includes('"' + p + '", "' + l + '"')); ok(!miss.length, "app.js menu has all core sections", miss.map(x => x.join(" ")).join(", "));
  ok(/_userAdmin === true && !window._tdMePreview/.test(app), "app.js: Admin Console only for admin, never in preview");
  ok(/if \(C100_NM && C100_NM\[tk\]\)/.test(app), "app.js: start-up guard for C100_NM");
  const ih = fs.existsSync(process.env.H_INDEX || "") ? fs.readFileSync(process.env.H_INDEX, "utf8") : (await txt("/?x=1", "hmember")).b;
  ok(/\/app\.js\?v=chat101[bc]"/.test(ih), "index.html loads app.js?v=chat101b", (ih.match(/app\.js\?v=[\w]+/) || [])[0]);
  ok(/aria-haspopup="true">All sections<\/button>/.test(ih) && /<a href="\/pricing">Pricing<\/a>/.test(ih) && /aria-label="Menu: all sections">Menu</.test(ih), "index.html: All sections button, Pricing link, Menu label");
  // 5. chat101 routes still clean
  for (const p of ["/tools/", "/tools/verify/", "/tools/isa-sipp/", "/tools/scenario/", "/central-banks/", "/research/filing-changes/"]) for (const u of [null, "hmember"]) {
    const r = await txt(p, u), v = vis(r.b); ok(r.s === 200 && DISC.test(v) && !RAW.test(v) && !LON.test(r.b) && !/\/__admin/.test(r.b), `chat101 ${p} ${u || "guest"} clean`, r.s);
  }
  const sw = (await txt("/sw.js")).b; ok(!/cache\.put|addEventListener\(["']push/.test(sw), "service worker: no cache.put, no push");
  console.log(`${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.log("FAIL crash " + (e && e.stack)); process.exit(1); });
