// chat100b harness test: gold change vs previous close, About founder card + photo. PORT default 8832.
const P = process.env.PORT || "8832", B = "http://127.0.0.1:" + P;
let pass = 0, fail = 0; const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 300))); };
const get = (p, u) => fetch(B + p, { headers: u ? { cookie: "dispatch_session=" + u } : {} });
const RAW = /GC=F|GBPUSD=X|\^DXY|DX-Y\.NYB|EURUSD=X|CL=F|BZ=F/;
(async () => {
  let r = await get("/__h/c100b?mode=real"); 
  let j = await (await get("/api/c100b/gold-change")).json();
  ok(j.available === true && j.usd && j.gbp, "gold-change available (live)", JSON.stringify(j));
  ok(j.usd && /previous close, gold futures \(COMEX, front month\)/.test(j.usd.basis) && /UK$/.test(j.usd.asOfUk), "usd basis plain words + UK time", j.usd && j.usd.basis);
  ok(j.gbp && /in pounds/.test(j.gbp.basis), "gbp basis says pounds", j.gbp && j.gbp.basis);
  ok(!RAW.test(JSON.stringify(j)), "no raw codes in gold-change JSON");
  let d = await (await get("/api/c97/gold-dash")).json();
  for (const k of ["gold_usd", "gold_gbp", "gold_eur"]) { const x = d.rows[k]; ok(x && /^[+\u2212]?[$£€][\d,.]+ \([+\u2212]?[\d.]+%\)$/.test(x.change) && /change vs previous close/.test(x.source), "gold-dash " + k + " has change + basis", x && x.change + " | " + x.source); }
  ok(d.rows.gold_usd.change.startsWith(j.usd.chg >= 0 ? "+$" : "\u2212$"), "gold-dash usd sign matches API");
  let m = await (await get("/api/c100/macro", "hmember")).text();
  const mm = JSON.parse(m); const tiles = JSON.stringify(mm); ok(/"gold_usd"[^}]*"change":"[+\u2212]\$/.test(tiles) && /"gold_gbp"[^}]*"change":"[+\u2212]£/.test(tiles), "macro tiles carry gold change", tiles.slice(0, 200));
  ok(!RAW.test(tiles), "no raw codes in macro JSON");
  for (const pg of ["/", "/gold/", "/gold/dashboard/", "/brief/", "/about"]) { const h = await (await get(pg)).text(); ok(!RAW.test(h.replace(/<script[\s\S]*?<\/script>/g, "")), "no raw codes in visible HTML " + pg); ok(/Not investment advice\. Capital at risk\./.test(h), "disclaimer on " + pg); }
  const gd = await (await get("/gold/dashboard/")).text(); ok(/c100b-(up|dn)/.test(gd) && /vs previous close/.test(gd), "gold dashboard table coloured change cell");
  // fallback + none
  await get("/__h/c100b?mode=none"); j = await (await get("/api/c100b/gold-change")).json(); ok(j.available === false, "no previous close -> available false");
  d = await (await get("/api/c97/gold-dash")).json(); ok(d.rows.gold_usd.change === "Change not available yet" && d.rows.gold_gbp.change === "Change not available yet", "gold-dash says 'Change not available yet'");
  m = await (await get("/api/c100/macro", "hmember")).text(); ok(/"gold_usd"[^}]*"change":"Change not available yet"/.test(m), "macro tile says 'Change not available yet'");
  await get("/__h/c100b?mode=snap"); j = await (await get("/api/c100b/gold-change")).json(); ok(j.available && /previous UK day/.test(j.usd.basis), "snapshot fallback labelled honestly", j.usd && j.usd.basis);
  await get("/__h/c100b?mode=real");
  // About
  const ab = await (await get("/about")).text();
  ok(/class="c100b-ed"/.test(ab) && /<h2[^>]*>Vraj Patel<\/h2>/.test(ab) && /Edited by Vraj Patel, London/.test(ab), "guest About founder card + byline");
  ok(/<img[^>]+src="\/assets\/founder\.webp\?v=[0-9a-f]+"[^>]+alt="Vraj Patel"/.test(ab), "guest About photo img alt Vraj Patel");
  ok(/href="https:\/\/www\.linkedin\.com\/company\/thedispatchmarket"[^>]*target="_blank"[^>]*rel="noopener noreferrer"/.test(ab) && /The Dispatch Market on LinkedIn/.test(ab), "LinkedIn link new tab noopener");
  ok(!/>V<\/(span|div)>/.test(ab), "no V placeholder");
  const sh = await (await get("/dashboard/", "hmember")).text(); ok(/window\.C100B_FOUNDER=\{"photo":"\/assets\/founder\.webp\?v=[0-9a-f]+"/.test(sh), "app shell gets C100B_FOUNDER photo");
  ok(/app\.js\?v=chat100b"/.test(sh), "index token chat100b");
  const app = await (await get("/app.js?v=chat100b")).text(); ok(/Edited by Vraj Patel, London/.test(app) && /c100b-about/.test(app), "app.js About sheet byline");
  r = await get("/assets/founder.webp"); const buf = Buffer.from(await r.arrayBuffer());
  ok(r.status === 200 && /image\/webp/.test(r.headers.get("content-type")) && buf.slice(8, 12).toString() === "WEBP", "photo route serves webp", r.status + " " + r.headers.get("content-type"));
  r = await fetch(B + "/assets/founder.webp", { method: "HEAD" }); ok(r.status === 200, "photo HEAD 200");
  r = await get("/assets/..%2fserver.js"); ok(r.status !== 200 || !/BB10I_MAINTENANCE_ON/.test(await r.text()), "no traversal via assets");
  console.log(`\nchat100b: ${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
