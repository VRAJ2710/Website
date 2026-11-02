// chat100d harness test: gold change spot vs our previous-UK-day spot snapshot, About founder card + photo. PORT default 8832.
const P = process.env.PORT || "8832", B = "http://127.0.0.1:" + P;
let pass = 0, fail = 0; const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 300))); };
const get = (p, u) => fetch(B + p, { headers: u ? { cookie: "dispatch_session=" + u } : {} });
const RAW = /GC=F|GBPUSD=X|\^DXY|DX-Y\.NYB|EURUSD=X|CL=F|BZ=F/;
(async () => {
  const FUT = /futures|COMEX|Yahoo Finance, delayed[^;]*previous close|previous close, gold/i;
  const SPOT_BASIS = /^vs previous UK close, our (pound |euro )?spot snapshot \(gold-api( spot \u00f7 (pound|euro) in dollars)?\), .+ UK$/;
  const CHG = /^[+\u2212][$£€][\d,.]+ \([+\u2212][\d.]+%\)$/;
  const rowsOf = async () => (await (await get("/api/c97/gold-dash")).json()).rows;
  const tiles = async () => { const r = (await (await get("/api/c100/macro", "hmember")).json()).rows || []; return JSON.stringify(r.filter(x => /^gold_/.test(x.key))); };
  const goldTr = (h) => (h.match(/<tr><td><strong>Gold spot, [^<]*<\/strong>[\s\S]*?<\/tr>/g) || []).join("\n");
  // A) no previous-UK-day spot snapshot (the state right after publish)
  await get("/__h/c100b?mode=none");
  let j = await (await get("/api/c100b/gold-change")).json();
  ok(j.available === false && !j.usd && !j.gbp && !j.eur, "no snapshot -> available false", JSON.stringify(j));
  ok(!FUT.test(JSON.stringify(j)), "no futures wording in gold-change JSON (none)");
  let d = await rowsOf();
  for (const k of ["gold_usd", "gold_gbp", "gold_eur"]) ok(d[k] && d[k].change === "Change not available yet" && !FUT.test(d[k].source + " " + d[k].changeBasis), "gold-dash " + k + " 'Change not available yet', no futures", d[k] && d[k].change + " | " + d[k].source);
  let m = await tiles(); ok(/"gold_usd"[^}]*"change":"Change not available yet"/.test(m) && /"gold_gbp"[^}]*"change":"Change not available yet"/.test(m), "macro tiles 'Change not available yet'");
  ok(!FUT.test(m) && !RAW.test(m), "macro JSON: no futures source, no raw codes");
  let h = goldTr(await (await get("/gold/dashboard/")).text()); ok((h.match(/<td>Change not available yet<\/td>/g) || []).length === 3 && !FUT.test(h), "gold dashboard page: 3 gold spot rows (US$, £, €) not available yet, no futures", h.slice(0, 300));
  // B) simulated previous-UK-day spot snapshot, up
  const sp = await (await get("/__h/c100b?mode=snap")).json();
  j = await (await get("/api/c100b/gold-change")).json();
  ok(j.available === true && j.usd && j.gbp && j.eur, "snapshot -> available (usd, gbp, eur)", JSON.stringify(j).slice(0, 300));
  for (const k of ["usd", "gbp", "eur"]) {
    const x = j[k]; ok(x && SPOT_BASIS.test(x.basis) && /UK$/.test(x.asOfUk), k + " basis is spot-on-spot plain words + UK time", x && x.basis);
    ok(x && Math.abs(x.prev - sp.prev[k]) < 1e-9 && Math.abs(x.chg - (x.price - x.prev)) < 1e-6 && Math.abs(x.pct - (x.price / x.prev - 1) * 100) < 1e-6, k + " change = spot now - our spot snapshot", x && JSON.stringify(x));
  }
  ok(/pound spot snapshot/.test(j.gbp.basis) && /euro spot snapshot/.test(j.eur.basis), "pound/euro compare their own spot snapshots");
  ok(!FUT.test(JSON.stringify(j)) && !RAW.test(JSON.stringify(j)), "no futures source / raw codes in gold-change JSON (snap)");
  d = await rowsOf();
  const cur = { gold_usd: "$", gold_gbp: "£", gold_eur: "€" };
  for (const k of Object.keys(cur)) { const x = d[k]; ok(x && CHG.test(x.change) && x.change.indexOf(cur[k]) === 1 && /our (pound |euro )?spot snapshot \(gold-api/.test(x.source) && !FUT.test(x.source + " " + x.changeBasis + " " + x.changeNote), "gold-dash " + k + " spot change + spot basis, no futures", x && x.change + " | " + x.source); }
  ok(d.gold_usd.change.startsWith(j.usd.chg >= 0 ? "+$" : "\u2212$") && d.gold_usd.change.indexOf(Math.abs(j.usd.chg).toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })) > 0, "gold-dash usd equals API change", d.gold_usd.change);
  m = await tiles(); ok(/"gold_usd"[^}]*"change":"[+\u2212]\$/.test(m) && /"gold_gbp"[^}]*"change":"[+\u2212]£/.test(m), "macro tiles carry spot change", m.slice(0, 200));
  ok(!FUT.test(m) && !RAW.test(m), "macro JSON (snap): no futures source, no raw codes");
  h = goldTr(await (await get("/gold/dashboard/")).text()); ok((h.match(/c100b-up/g) || []).length === 3 && /vs previous UK close/.test(h) && /spot snapshot \(gold-api/.test(h) && !FUT.test(h), "gold dashboard: 3 gold spot rows green, 'vs previous UK close, our spot snapshot', no futures", h.slice(0, 400));
  await get("/__h/c100b?mode=snap&dir=down"); h = goldTr(await (await get("/gold/dashboard/")).text()); ok((h.match(/c100b-dn/g) || []).length === 3, "gold dashboard: 3 gold spot rows red when spot is below the snapshot");
  j = await (await get("/api/c100b/gold-change")).json(); ok(j.usd.chg < 0 && j.gbp.chg < 0, "down snapshot -> negative change");
  // Market context script: no futures text shipped; uses prev from the API with the displayed spot
  for (const pg of ["/", "/gold/", "/gold/dashboard/", "/brief/", "/about"]) { const hh = await (await get(pg)).text(); ok(!RAW.test(hh.replace(/<script[\s\S]*?<\/script>/g, "")), "no raw codes in visible HTML " + pg); ok(/Not investment advice\. Capital at risk\./.test(hh), "disclaimer on " + pg); ok(!/GC=F|gold futures \(COMEX|previous close, gold futures/i.test(hh), "no gold-futures source on " + pg); }
  const home = await (await get("/")).text(); ok(/api\/c100b\/gold-change/.test(home) && /Number\(c\.prev\)/.test(home), "Market context computes spot now vs snapshot prev");
  await get("/__h/c100b?mode=none");
  // About
  const ab = await (await get("/about")).text();
  ok(/class="c100b-ed"/.test(ab) && /<h2[^>]*>Vraj Patel<\/h2>/.test(ab) && /Edited by Vraj Patel, London/.test(ab), "guest About founder card + byline");
  ok(/<img[^>]+src="\/assets\/founder\.webp\?v=[0-9a-f]+"[^>]+alt="Vraj Patel"/.test(ab), "guest About photo img alt Vraj Patel");
  ok(/href="https:\/\/www\.linkedin\.com\/in\/vraj2710"[^>]*target="_blank"[^>]*rel="noopener noreferrer"/.test(ab) && /Vraj Patel on LinkedIn/.test(ab), "LinkedIn link new tab noopener");
  ok(!/>V<\/(span|div)>/.test(ab), "no V placeholder");
  const sh = await (await get("/dashboard/", "hmember")).text(); ok(/window\.C100B_FOUNDER=\{"photo":"\/assets\/founder\.webp\?v=[0-9a-f]+"/.test(sh), "app shell gets C100B_FOUNDER photo");
  ok(/app\.js\?v=chat100d"/.test(sh), "index token chat100d");
  const app = await (await get("/app.js?v=chat100d")).text(); ok(/Edited by Vraj Patel, London/.test(app) && /c100b-about/.test(app), "app.js About sheet byline");
  r = await get("/assets/founder.webp"); const buf = Buffer.from(await r.arrayBuffer());
  ok(r.status === 200 && /image\/webp/.test(r.headers.get("content-type")) && buf.slice(8, 12).toString() === "WEBP", "photo route serves webp", r.status + " " + r.headers.get("content-type"));
  r = await fetch(B + "/assets/founder.webp", { method: "HEAD" }); ok(r.status === 200, "photo HEAD 200");
  r = await get("/assets/..%2fserver.js"); ok(r.status !== 200 || !/BB10I_MAINTENANCE_ON/.test(await r.text()), "no traversal via assets");
  // chat100d: final About bio everywhere, old draft wording nowhere
  const BIO = "Vraj Patel founded The Dispatch Market to give independent investors a careful, sourced read on gold and macro. He edits every piece from London.";
  const OLD = /writes the research|builds the site|builds the platform|writes the desk/;
  { const ga = await (await get("/about")).text(); ok(ga.includes('<p class="c100b-bio">' + BIO + "</p>"), "guest /about bio exact"); ok(!OLD.test(ga), "guest /about: no old wording");
    const ap = await (await get("/app.js?v=chat100d")).text(); ok(ap.includes('<p class="rt49-bio">' + BIO + "</p>"), "app About bio exact"); ok(!OLD.test(ap), "app.js: no old wording");
    for (const pg of ["/", "/gold/", "/brief/", "/dashboard/", "/?settings=1"]) { const t = await (await get(pg, "hmember")).text(); ok(!OLD.test(t), "no old wording on " + pg + " (member)"); const g = await (await get(pg)).text(); ok(!OLD.test(g), "no old wording on " + pg + " (guest)"); }
    ok(/<a class="c100b-li" href="https:\/\/www\.linkedin\.com\/in\/vraj2710" target="_blank" rel="noopener noreferrer">[\s\S]*?Vraj Patel on LinkedIn/.test(ga), "guest founder link = /in/vraj2710, 'Vraj Patel on LinkedIn', new tab, noopener noreferrer");
    const sh = await (await get("/dashboard/", "hmember")).text(); ok(/window\.C100B_FOUNDER=\{[^}]*"li":"https:\/\/www\.linkedin\.com\/in\/vraj2710","liLabel":"Vraj Patel on LinkedIn"/.test(sh), "app founder config = /in/vraj2710 + label");
    ok(/rel="noopener noreferrer">' \+ svg \+ _rt49Esc\(F\.liLabel\)/.test(ap) && !/linkedin\.com\/company\//.test(ap), "app link noopener noreferrer, no company URL in app.js");
    for (const [nm, t] of [["guest /about", ga], ["app shell", sh]]) ok(!/linkedin\.com\/company\//.test(t) && !/The Dispatch Market on LinkedIn/.test(t), "company-page URL not used for founder link: " + nm);
    const idx2 = await (await get("/?settings=1", "hmember")).text(); ok(!/linkedin\.com\/company\//.test(idx2), "index About: no company URL"); }
  console.log(`\nchat100d: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
