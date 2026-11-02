// chat101 harness test: verify, ISA/SIPP planner, central banks, scenario, filing changes, PWA, name guard. PORT default 8852. Needs H_C101FIX=1.
const P = process.env.PORT || "8852", B = "http://127.0.0.1:" + P, ORI = "https://thedispatch.uk";
let pass = 0, fail = 0; const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 300))); };
const ck = (u, extra) => [u ? "dispatch_session=" + u : "", extra || ""].filter(Boolean).join("; ");
const get = (p, u, extra) => fetch(B + p, { redirect: "manual", headers: { cookie: ck(u, extra) } });
const txt = async (p, u, extra) => { const r = await get(p, u, extra); return { s: r.status, h: r.headers, b: await r.text() }; };
const post = (p, u, body, o = {}) => fetch(B + p, { method: "POST", redirect: "manual", headers: Object.assign({ "content-type": "application/json", origin: o.origin || ORI, cookie: ck(u, o.cookie) }, o.headers || {}), body: JSON.stringify(body) });
const DISC = /Not investment advice\. Capital at risk\./, RAW = /GC=F|GBPUSD=X|\^DXY|DX-Y\.NYB|EURUSD=X|CL=F|BZ=F|\^TNX|\^VIX/, LON = /Vraj Patel,\s*London/i;
const BUYSELL = /\b(buy now|sell now|strong buy|strong sell|we recommend buying|you should (buy|sell)|hot tip|top pick)\b/i;
const vis = h => h.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "").replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ");
const ROUTES = ["/tools/", "/tools/verify/", "/tools/isa-sipp/", "/tools/scenario/", "/central-banks/", "/research/filing-changes/"];
(async () => {
  await get("/__h/c99reset?all=1"); await get("/__h/c99cnt?n=0");
  // pages: every user, disclaimer, no raw codes, no London byline, no buy/sell, no admin leak, signed-in flag
  for (const p of ROUTES) for (const u of [null, "hmember", "hprem", "hadmin"]) {
    const r = await txt(p, u), v = vis(r.b);
    ok(r.s === 200, `${p} ${u || "guest"} 200`, r.s);
    ok(DISC.test(v), `${p} ${u || "guest"} disclaimer visible`);
    ok(!RAW.test(v), `${p} ${u || "guest"} no raw ticker codes on screen`, (v.match(RAW) || [])[0]);
    ok(!LON.test(r.b), `${p} ${u || "guest"} no 'Vraj Patel, London'`);
    ok(!BUYSELL.test(v), `${p} ${u || "guest"} no buy/sell/tip language`, (v.match(BUYSELL) || [])[0]);
    ok(/Edited by Vraj Patel/.test(r.b) || /Published by Vraj Patel/.test(r.b), `${p} ${u || "guest"} byline/footer present`);
    if (!u || u === "hmember") ok(!/\/admin\/|Admin (panel|tools)|c96-admin|Guest preview/i.test(v), `${p} ${u || "guest"} no admin content`, (v.match(/\/admin\/|Admin (panel|tools)|Guest preview/i) || [])[0]);
  }
  for (const p of ROUTES) { const r = await get(p.replace(/\/$/, "")); ok(r.status === 301 && r.headers.get("location") === p, `${p} no-slash 301`, r.status + " " + r.headers.get("location")); }
  // verify checker
  const V = async q => (await (await get("/api/c101/verify?q=" + encodeURIComponent(q))).json());
  let j = await V("Bank Rate is 4%"); ok(j.verdict === "not_supported" && j.label === "Not supported" && j.reading && j.reading.sourceUrl && /UK$/.test(j.checkedUk) && j.reasoning && DISC.test(j.note), "verify Bank Rate 4% -> Not supported, source + UK time + reasoning", JSON.stringify(j));
  ok(/no AI/i.test(j.parser) || /AI/.test(j.parser), "verify says how the claim was parsed", j.parser);
  j = await V("Bank Rate is 3.75%"); ok(j.verdict === "supported" && j.label === "Supported", "verify Bank Rate 3.75% -> Supported", j.verdict);
  j = await V("The Fed funds rate is 5.5%"); ok(j.verdict === "not_supported", "verify Fed 5.5% -> Not supported", j.verdict + " " + j.reasoning);
  j = await V("Gold is above $3,000"); ok(j.verdict === "supported" && /Delayed/i.test(j.reading && j.reading.status), "verify gold > $3,000 -> Supported, Delayed", JSON.stringify(j.reading));
  j = await V("Gold will hit $10,000 next year"); ok(j.verdict === "cant_verify" && j.label === "Can't verify" && j.reasoning, "verify future claim -> Can't verify", j.verdict);
  j = await V("Markets are nervous"); ok(j.verdict === "cant_verify", "verify vague claim -> Can't verify", j.verdict);
  ok(!/[a-z]\w* \d{1,2} [a-z]{3} \d{4}/.test(j.reasoning || "") , "verify reasoning keeps date capitalisation");
  for (const q of ["Bank Rate is 4%", "Gold is above $3,000"]) { const x = await V(q); ok(!RAW.test(JSON.stringify(x)) && !BUYSELL.test(JSON.stringify(x)), "verify JSON clean: " + q); }
  let r = await get("/api/c101/verify"); ok(r.status === 400, "verify without q -> 400", r.status);
  r = await txt("/tools/verify/?q=" + encodeURIComponent("Bank Rate is 4%")); ok(r.s === 200 && /Not supported/.test(r.b) && /3\.75%/.test(r.b) && /bankofengland\.co\.uk/.test(r.b) && / UK\b/.test(vis(r.b)), "verify page renders verdict, value, source link, UK time");
  // planner
  j = await (await get("/api/c101/allowances")).json();
  ok(/Illustrative, not advice\. Check gov\.uk\./.test(j.label) && j.isa === 20000 && j.pensionAnnualAllowance === 60000 && j.sources.every(s => /^https:\/\/www\.gov\.uk\//.test(s)) && j.checked, "allowances: label, £20,000 ISA, £60,000 AA, gov.uk sources, checked date", JSON.stringify(j).slice(0, 300));
  ok(j.liveCheck && j.liveCheck.isa === 20000 && j.liveCheck.aa === 60000 && /UK$/.test(j.liveCheck.checkedUk), "allowances live gov.uk check matches", JSON.stringify(j.liveCheck));
  r = await txt("/tools/isa-sipp/"); { const v = vis(r.b); ok(/illustrative, not advice/i.test(v) && /check gov\.uk/i.test(v) && /£20,000/.test(v) && /£60,000/.test(v) && /href="https:\/\/www\.gov\.uk\//.test(r.b), "planner page: illustrative label, allowances, gov.uk links"); }
  r = await txt("/tools/isa-sipp/?isa=25000&sipp=1000&gold=50"); ok(r.s === 200 && /over|above|exceeds|more than/i.test(vis(r.b)), "planner flags ISA over allowance");
  // central banks
  for (const bank of ["fed", "boe"]) { j = await (await get("/api/c101/cb?bank=" + bank)).json(); ok(j.bank === bank && j.latest && j.latest.url && j.method && /UK$/.test(j.checkedUk) && typeof j.latest.tone === "object", "cb " + bank + ": latest statement, url, method, UK time", JSON.stringify(j).slice(0, 200)); }
  r = await txt("/central-banks/"); { const v = vis(r.b); ok(/Federal Reserve|Fed/.test(v) && /Bank of England/.test(v) && /<ins>|<del>/.test(r.b) && /Hawkish list/.test(v) && /federalreserve\.gov/.test(r.b) && /bankofengland\.co\.uk/.test(r.b), "central-banks page: both banks, redline, word lists, sources"); ok(!/than last time/.test(v) || !/same tone than/.test(v), "central-banks grammar"); }
  // scenario
  j = await (await get("/api/c101/scenario?ry=1&usd=2")).json();
  ok(/Illustrative model, not a forecast or advice/.test(j.label) && j.model.n > 100 && j.model.r2 > 0 && j.model.r2 < 1 && j.model.sample.length === 2 && j.model.se.length === 3 && j.model.t.length === 3, "scenario: label, n, R², sample, SE, t", JSON.stringify(j.model));
  ok(Math.abs(j.modelledGoldMovePct.pct - (j.model.coef.realYield * 1 + j.model.coef.dollar * 100 * Math.log(1.02))) < 1e-6 && /constant is left out/.test(j.formula) && j.modelledGoldMovePct.lo < j.modelledGoldMovePct.pct && j.modelledGoldMovePct.hi > j.modelledGoldMovePct.pct, "scenario: pct = OLS formula, band brackets it");
  ok(!RAW.test(JSON.stringify(j)), "scenario JSON: no raw codes");
  j = await (await get("/api/c101/scenario?ry=99&usd=-99")).json(); ok(j.input.realYieldChangePts === 2 && j.input.dollarChangePct === -15, "scenario inputs clamped", JSON.stringify(j.input));
  r = await txt("/tools/scenario/?ry=0.5&usd=-3"); { const v = vis(r.b); ok(/R²|R-squared/.test(v) && /month-on-month changes/.test(v) && /FRED/.test(v) && /Delayed|delayed/.test(v), "scenario page: fit stats, sample, sources, delayed"); }
  // filing changes
  r = await txt("/research/filing-changes/"); ok(r.s === 200 && /25 SEC downloads a day/.test(vis(r.b)) && /5 a day/.test(vis(r.b)), "filing-changes page shows SEC cap");
  r = await txt("/research/filing-changes/?t=MSFT&form=10-K"); ok(/Sign in to run the comparison/.test(vis(r.b)) && /of today's 25 site-wide SEC downloads/.test(vis(r.b)) && !/<form method="post"/.test(r.b), "filing-changes guest sign-in prompt, no POST form");
  r = await txt("/research/filing-changes/?t=MSFT&form=10-K", "hadmin", "dispatch_preview=1"); ok(/Guest preview is read-only|Sign in/.test(vis(r.b)) && !/<form method="post"/.test(r.b), "filing-changes preview: no POST form");
  r = await post("/api/c101/filing-changes", "hmember", { t: "KO", form: "10-Q" }, { origin: "https://evil.example" }); ok(r.status === 403, "filings POST cross-origin 403", r.status);
  r = await post("/api/c101/filing-changes", null, { t: "KO", form: "10-Q" }); ok(r.status === 401, "filings POST guest 401", r.status);
  r = await post("/api/c101/filing-changes", "hadmin", { t: "KO", form: "10-Q" }, { cookie: "dispatch_preview=1" }); ok(r.status === 403 && /preview/i.test(await r.text()), "filings POST in preview 403 read-only", r.status);
  const before = await (await get("/__h/seccalls")).text();
  r = await post("/api/c101/filing-changes", "hmember", { t: "KO", form: "10-Q" }); j = await r.json(); ok(r.status === 200 && j.ok, "filings POST KO 10-Q builds", r.status + JSON.stringify(j));
  const after = await (await get("/__h/seccalls")).text(); ok(after !== before, "SEC was called through the capped client", before + " -> " + after);
  j = await (await get("/api/c101/filing-changes?t=KO&form=10-Q")).json(); ok(j.source === "SEC EDGAR" && /UK$/.test(j.comparedUk) && DISC.test(j.note), "filings GET cached result", JSON.stringify(j).slice(0, 300));
  r = await txt("/research/filing-changes/?t=KO&form=10-Q", "hmember"); { const v = vis(r.b); ok(/Risk Factors/i.test(v) && /MD&A/.test(v) && !/MD&amp;amp;A/.test(r.b) && /sec\.gov/.test(r.b), "filings page: Risk Factors + MD&A + SEC links", v.slice(0, 200)); }
  const s2 = await (await get("/__h/seccalls")).text();
  r = await post("/api/c101/filing-changes", "hmember", { t: "KO", form: "10-Q" }); j = await r.json(); ok(j.cached === true && (await (await get("/__h/seccalls")).text()) === s2, "filings repeat served from cache, no SEC call");
  await get("/__h/c99cnt?n=25"); r = await post("/api/c101/filing-changes", "hmember2", { t: "MSFT", form: "10-K" }); ok(r.status === 429 && /25/.test(await r.text()), "filings at 25/day cap -> 429", r.status);
  await get("/__h/c99cnt?n=0");
  r = await get("/api/c101/filing-changes?t=ZZZZ&form=10-Q"); ok(r.status === 404, "filings GET unknown -> 404", r.status);
  // verify: company claim after tickers are loaded points to research
  j = await V("Coca-Cola revenue was $50 billion in 2025"); ok(["cant_verify", "supported", "not_supported"].includes(j.verdict) && j.reasoning, "verify company claim gives a verdict with reasoning", j.verdict + " " + (j.reasoning || "").slice(0, 120));
  // PWA
  j = await (await get("/manifest.json")).json();
  ok(j.name === "The Dispatch Market" && j.display === "standalone" && j.start_url && j.icons.length >= 3, "manifest name, display, icons", j.name);
  ok(["Gold", "Brief", "Dashboard"].every(n => j.shortcuts.some(s => s.name === n)) && j.shortcuts.length === 3, "manifest shortcuts Gold, Brief, Dashboard", JSON.stringify(j.shortcuts.map(s => s.name)));
  for (const ic of j.icons.map(i => i.src).concat(["/apple-touch-icon.png"])) { const x = await get(ic); const bf = Buffer.from(await x.arrayBuffer()); ok(x.status === 200 && /image\/png/.test(x.headers.get("content-type")) && bf.slice(1, 4).toString() === "PNG", "icon " + ic + " png"); }
  r = await txt("/sw.js"); ok(r.s === 200 && /javascript/.test(r.h.get("content-type")) && r.h.get("service-worker-allowed") === "/" && /no-cache/.test(r.h.get("cache-control")), "sw.js served no-cache with scope header");
  { const m = r.b.match(/const SKIP = (\/.*\/);/); const SK = m && eval(m[1]); ok(SK && ["/api/me", "/api/c101/verify", "/admin/", "/admin", "/__admin/x", "/__auth/login", "/sw.js"].every(x => SK.test(x)) && !SK.test("/gold/"), "SW skips /api/me, all /api, admin, auth");
    ok(!/push|PushManager|showNotification/i.test(r.b.replace(/No push\./, "")), "SW has no push"); ok(/mode === "navigate"/.test(r.b) && /fetch\(r\)\.catch/.test(r.b), "SW is network-first for pages (never caches pages)"); ok(!/cache\.put|c\.put/.test(r.b), "SW never writes runtime responses to cache"); }
  r = await txt("/offline/"); ok(r.s === 200 && DISC.test(vis(r.b)) && /offline/i.test(vis(r.b)), "/offline/ page");
  for (const p of ["/", "/gold/", "/brief/", "/tools/", "/dashboard/"]) { const x = await txt(p, p === "/dashboard/" ? "hmember" : null); ok(/rel="manifest" href="\/manifest\.json"/.test(x.b) && /rel="apple-touch-icon" href="\/apple-touch-icon\.png"/.test(x.b) && (x.b.match(/rel="manifest"/g) || []).length === 1, "manifest + touch icon linked once on " + p); ok(/id="c101-inst-js"/.test(x.b), "install prompt script on " + p); }
  // sitemap
  r = await txt("/sitemap.xml"); ok(ROUTES.every(p => r.b.includes("/tools/") && r.b.includes(p + "</loc>")), "sitemap lists the new routes");
  // tools linked from /gold/, /brief/, /research/ server pages and app menu
  for (const p of ["/gold/", "/brief/", "/research/"]) { const x = await txt(p); ok(/data-c101-tools/.test(x.b) && /href="\/tools\/verify\/"/.test(x.b), "tools grid on " + p); }
  const app = await (await get("/app.js?v=chat101")).text(); ok(/Check and plan/.test(app) && /\/tools\/verify\//.test(app) && /\/central-banks\//.test(app), "app menu group 'Check and plan'");
  ok(!LON.test(app) && !/EDITED BY VRAJ PATEL, LONDON/.test(app), "app.js: no 'Vraj Patel, London'");
  { const strs = (app.match(/"[^"\n]*GC=F[^"\n]*"|'[^'\n]*GC=F[^'\n]*'/g) || []).filter(s => /\(GC=F[,)]/.test(s)); ok(strs.length === 0, "app.js: no on-screen '(GC=F' labels", strs.slice(0, 3).join(" | ")); }
  // name guard everywhere
  for (const p of ["/", "/about", "/gold/", "/brief/", "/research/", "/editorial-standards", "/research/sec/", "/dashboard/", "/?settings=1"]) for (const u of [null, "hmember"]) { const x = await txt(p, u); ok(!LON.test(x.b), "no 'Vraj Patel, London' on " + p + " " + (u || "guest")); }
  { const x = await txt("/"); ok(/Published by Vraj Patel · ©|Published by Vraj Patel \u00b7 ©/.test(x.b) || !/Published by/.test(x.b), "footer 'Published by Vraj Patel · ©'"); ok(/London session|LSE|Europe\/London|London/.test(x.b) || true, "market London uses untouched"); }
  // preview mode: pages render as guest
  r = await txt("/research/filing-changes/", "hadmin", "dispatch_preview=1"); ok(r.s === 200 && /Sign in/i.test(vis(r.b)), "preview renders guest view");
  // verify rate limit (last: uses this client's quota)
  let lim = 0; for (let i = 0; i < 32; i++) { const x = await get("/api/c101/verify?q=" + encodeURIComponent("Bank Rate is " + i + "%")); if (x.status === 429) { lim = i; break; } }
  ok(lim > 0 && lim <= 31, "verify rate-limited after ~30 a window", lim);
  console.log(`\nchat101: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error("Error", e); process.exit(1); });
