// chat100 harness test: macro API, screener auto-build, inspector, defaults, fear gauge, security re-checks. PORT default 8832 (maintenance off)
const pp = require("/workspace/c97/shot/node_modules/puppeteer-core");
const PORT = +(process.env.PORT || 8832), B = "http://127.0.0.1:" + PORT;
let pass = 0, fail = 0; const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL", m); } };
const RAW = /\b(GC=F|SI=F|BZ=F|CL=F|\^GSPC|\^TNX|DX-Y\.NYB|GBPUSD=X|DX=F)\b/;
const get = (p, h) => fetch(B + p, { headers: h || {}, redirect: "manual" });
(async () => {
  let r = await get("/api/c100/macro"), j = await r.json();
  ok(r.status === 200 && j.available, "macro available");
  const keys = (j.rows || []).map(x => x.key);
  for (const k of ["gold_usd", "silver", "gold_gbp", "dxy", "tnx", "ry", "brent", "gbpusd", "spx"]) ok(keys.includes(k), "macro row " + k);
  for (const x of j.rows || []) { ok(x.name && x.value && x.source && x.sourceUrl && x.series && /UK/.test(x.asOf) && x.status && x.plain, "row complete " + x.key); ok(!RAW.test(x.name + x.value + x.source + x.asOf), "no raw code " + x.key); }
  ok(/÷/.test((j.rows.find(x => x.key === "gold_gbp") || {}).formula || ""), "gold in GBP formula");
  ok(/max-age=60/.test(r.headers.get("cache-control") || ""), "macro cache header");
  // screener: page shows a calm building state or the table, and status respects the cap
  r = await get("/research/sec/screener/"); let h = await r.text();
  ok(r.status === 200 && (/Building the screener, check back shortly\./.test(h) || /<table class="c97t c99t">/.test(h)), "screener page state");
  ok(!/has not been built yet/.test(h), "old empty text gone");
  let st = {}; for (let i = 0; i < 20; i++) { st = await (await get("/api/c99/status")).json(); if (st.screener) break; await new Promise(r => setTimeout(r, 1000)); }
  ok(st.screener === true, "screener built without an admin click");
  ok(st.used <= st.cap && st.cap === 25, "SEC cap respected " + st.used + "/" + st.cap);
  h = await (await get("/research/sec/screener/")).text(); ok(/<table class="c97t c99t">/.test(h), "screener table after build");
  // inspector injected once on server pages and the app shell
  for (const p of ["/", "/dashboard/", "/brief/", "/gold/", "/gold/dashboard/", "/markets/yields/", "/gold/positioning/", "/research/sec/screener/", "/pricing/"]) {
    h = await (await get(p)).text();
    ok((h.match(/id="c100-insp-js"/g) || []).length === 1 && (h.match(/id="c100-insp"/g) || []).length === 1, "inspector once on " + p);
    ok(!/V1 · GOLD FIRST/.test(h), "no V1 label " + p);
  }
  h = await (await get("/dashboard/")).text(); ok(/app\.js\?v=chat100d"/.test(h), "index token chat100d");
  // security re-checks
  ok([302, 303, 401, 403, 404].includes((await get("/console")).status), "guest /console refused");
  r = await fetch(B + "/api/c99/screener/build", { method: "POST", redirect: "manual" }); ok(r.status >= 400, "guest admin build refused " + r.status);
  r = await fetch(B + "/api/stripe/webhook", { method: "POST", body: "{}", headers: { "content-type": "application/json" } }); ok(r.status === 400, "stripe webhook unsigned 400 " + r.status);
  // browser: defaults, migration, fear gauge, inspector click + keyboard
  const b = await pp.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  for (const [w, th] of [[390, "light"], [1280, "dark"]]) {
    const ctx = await b.createBrowserContext(), p = await ctx.newPage(); await p.setViewport({ width: w, height: 900 });
    await p.setCookie({ name: "dispatch_theme", value: th, domain: "127.0.0.1", path: "/" }, { name: "dispatch_session", value: "hmember", domain: "127.0.0.1", path: "/" });
    await p.evaluateOnNewDocument(() => { if (!sessionStorage.getItem("x")) { sessionStorage.setItem("x", 1); localStorage.setItem("td_wls", JSON.stringify([{ id: "wl1", name: "My Watchlist", tickers: ["SPY", "NVDA", "BTC", "XAU", "AAPL"] }])); } });
    await p.goto(B + "/dashboard/", { waitUntil: "domcontentloaded" }); await new Promise(r => setTimeout(r, 4500));
    const s = await p.evaluate(() => ({ wl: watchlists[0].tickers.join(","), tiles: document.querySelectorAll("#c100-macro [data-c100]").length, chips: document.querySelectorAll(".book-px-tk").length, txt: (document.getElementById("c100-macro") || {}).innerText || "" }));
    ok(s.wl === "XAU,SLV,GBPUSD,DXY,TNX,BRENT,SPX", w + " old default migrated: " + s.wl);
    ok(s.tiles >= 9, w + " macro tiles " + s.tiles); ok(s.chips === 0, w + " no raw ticker chips for the default book");
    ok(!RAW.test(s.txt) && !/\b(AAPL|NVDA|SPY)\b/.test(s.txt), w + " macro panel plain names");
    await p.focus("#c100-macro [data-c100]"); await p.keyboard.press("Enter"); await new Promise(r => setTimeout(r, 300));
    let d = await p.evaluate(() => { const e = document.getElementById("c100-pane"); return e && !e.hidden && getComputedStyle(e).display !== "none" ? { t: e.innerText, f: document.activeElement && document.activeElement.className, role: e.getAttribute("role"), rect: e.getBoundingClientRect().width } : null; });
    ok(d && d.role === "dialog" && /gold-api/i.test(d.t) && /UK/.test(d.t) && /Delayed|Last known/.test(d.t), w + " dashboard tile opens inspector by keyboard " + JSON.stringify(d && d.t.slice(0, 80)));
    ok(d && d.rect <= w, w + " pane fits");
    await p.keyboard.press("Escape"); await new Promise(r => setTimeout(r, 200));
    d = await p.evaluate(() => ({ open: !!(document.getElementById("c100-pane") && !document.getElementById("c100-pane").hidden), foc: document.activeElement && document.activeElement.hasAttribute("data-c100") }));
    ok(!d.open && d.foc, w + " Esc closes and focus returns");
    for (const [pg, sel, want] of [["/gold/dashboard/", "table.c97t .c100-fig", /gold-api|FRED|Yahoo|ICE/], ["/gold/", "table.ctx .c100-fig", /UK/], ["/markets/yields/", "table.c97t .c100-fig", /FRED|Treasury/], ["/gold/positioning/", "table.c97t .c100-fig", /CFTC/], ["/", "table.ctx .c100-fig", /UK/], ["/brief/", "table.ctx .c100-fig", /UK/]]) {
      if (/ctx/.test(sel)) await p.deleteCookie({ name: "dispatch_session", domain: "127.0.0.1", path: "/" }); // signed-in users get the app view on these pages
      await p.goto(B + pg, { waitUntil: "domcontentloaded" }); await p.waitForSelector(sel, { timeout: 15000 }).catch(() => {});
      const n = await p.$$eval(sel, e => e.length);
      ok(n > 0, w + " figures decorated on " + pg + " (" + n + ")");
      if (!n) continue;
      await p.click(sel); await new Promise(r => setTimeout(r, 250));
      d = await p.evaluate(() => { const e = document.getElementById("c100-pane"); return e && !e.hidden ? e.innerText : ""; });
      ok(want.test(d) && /UK|Time not stated/.test(d), w + " inspector on " + pg + ": " + d.replace(/\s+/g, " ").slice(0, 140));
      await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); await p.keyboard.press("Tab");
      const inPane = await p.evaluate(() => !!document.activeElement.closest("#c100-pane")); ok(inPane, w + " focus trapped in pane " + pg);
      await p.keyboard.press("Escape");
    }
    await ctx.close();
  }
  await b.close();
  console.log(`t_c100: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.log("ERR", e); process.exit(1); });
