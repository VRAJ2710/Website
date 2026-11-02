const { rq, ok, done } = require("./t.js");
const OFF = 8832, ON = 8831, ORI = { origin: "https://thedispatch.uk" };
const NOMASTER = process.env.H_NO_MASTER === "1";
const SOON = /Use your own AI key: coming soon/;
const PROMISE = /add your own AI key in Settings|Any signed-in reader can add|Signed-in readers can add|or yours, if you prefer/;
(async () => {
  let r, j;
  // F2
  for (const [pg, u] of [["/pricing/", null], ["/pricing/", "hmember"], ["/methodology/", null], ["/methodology/", "hmember"]]) {
    r = await rq(OFF, "GET", pg, u ? { user: u } : {});
    if (NOMASTER) ok(`F2 no key: ${pg} ${u || "guest"} says coming soon, no promise`, r.s === 200 && SOON.test(r.b) && !PROMISE.test(r.b), r.s + " " + (r.b.match(PROMISE) || [""])[0]);
    else ok(`F2 key set: ${pg} ${u || "guest"} keeps BYOK copy`, r.s === 200 && PROMISE.test(r.b) && !SOON.test(r.b), r.s);
  }
  r = await rq(OFF, "GET", "/?settings=1", { user: "hmember" });
  ok("F2 app shell r2-nobyok class iff no key", NOMASTER === /<html[^>]*class="[^"]*r2-nobyok/.test(r.b), (r.b.match(/<html[^>]*>/) || [])[0]);
  r = await rq(OFF, "GET", "/app.js?v=chat99r2"); ok("F2 app.js has coming-soon wrappers", /Use your own AI key: coming soon/.test(r.b) && /r2NoByok/.test(r.b), r.s);
  // F4
  for (const pg of ["/brief/", "/pricing/", "/", "/about/", "/markets/yields/", "/research/"]) {
    r = await rq(OFF, "GET", pg); const n = r.b.split('action="/free-brief"').length - 1;
    ok(`F4 guest ${pg}: exactly one free-brief form`, r.s === 200 && n === 1, r.s + " forms=" + n);
  }
  r = await rq(OFF, "GET", "/brief/"); ok("F4 /brief/ keeps the mid-page form, drops footer", !/data-c96-footsu><form/.test(r.b) && /action="\/free-brief"/.test(r.b), "");
  // F1
  r = await rq(OFF, "GET", "/pricing/?view=guest", { user: "hadmin" });
  ok("F1 admin ?view=guest: guest page on same request, no-store, cookie", r.s === 200 && /view=exit/.test(r.b) && /no-store/.test(r.h["cache-control"] || "") && /dispatch_preview=1/.test(String(r.h["set-cookie"])), r.s + " " + r.h["cache-control"]);
  r = await rq(OFF, "GET", "/?view=guest", { user: "hadmin" });
  ok("F1 admin /?view=guest: guest home", r.s === 200 && /view=exit/.test(r.b) && !/Your daily read|Good to see you/.test(r.b), r.s);
  r = await rq(OFF, "GET", "/?view=exit", { user: "hadmin", cookie: "dispatch_preview=1" });
  ok("F1 ?view=exit: signed-in page on same request + cookie cleared", r.s === 200 && !/view=exit/.test(r.b) && /Max-Age=0/.test(String(r.h["set-cookie"])), r.s + String(r.h["set-cookie"]));
  r = await rq(OFF, "GET", "/pricing/?view=guest", { user: "hadmin", cookie: "dispatch_preview=1" }); // exit then guest again: still guest
  ok("F1 guest after exit honours guest", /view=exit/.test(r.b), "");
  r = await rq(OFF, "GET", "/pricing/", { user: "hmember" }); ok("F1 signed-in pages never public cache", !/public/.test(r.h["cache-control"] || ""), r.h["cache-control"]);
  r = await rq(OFF, "GET", "/pricing/"); ok("F1 guest pricing still cacheable", /public/.test(r.h["cache-control"] || ""), r.h["cache-control"]);
  r = await rq(OFF, "GET", "/pricing/?view=guest", { user: "hmember" }); ok("F1 member ?view=guest: no preview", !/dispatch_preview=1/.test(String(r.h["set-cookie"] || "")) && !/view=exit/.test(r.b), "");
  // F3
  r = await rq(OFF, "GET", "/", { user: "hmember" });
  const top = (r.b.match(/<section id="c93top">[\s\S]*?<\/section>/) || [""])[0];
  ok("F3 signed-in home: Market context first in the grid", top.indexOf("Market context") > 0 && top.indexOf("Market context") < top.indexOf("Today's brief") || top.indexOf("Market context") < top.indexOf("Today&#39;s brief"), top.slice(0, 200));
  // xAI
  r = await rq(OFF, "GET", "/api/admin/ai-readiness", { user: "hadmin" }); ok("admin ai-readiness: no xAI", r.s === 200 && !/xai|grok/i.test(r.b) && JSON.parse(r.b), r.s + r.b.slice(0, 200));
  r = await rq(OFF, "GET", "/api/ai-status", { user: "hadmin" }); ok("ai-status: no xAI, valid JSON", r.s === 200 && !/"xai"|xAI \/ Grok/.test(r.b) && JSON.parse(r.b), r.s + r.b.slice(0, 200));
  // CSV
  r = await rq(OFF, "POST", "/api/c98/portfolio", { user: "hmember2", json: { csv: 'Name,Value\n"Vanguard FTSE Global All Cap","£12,500"\nPhysical gold ETC,"2,000.50"\nCash ISA;1000\n"Fund, ""A""",300' }, headers: ORI });
  try { j = JSON.parse(r.b); } catch (e) { j = {}; }
  ok("CSV quoted thousands", r.s === 200 && j.holdings && j.holdings.length === 4 && j.holdings[0].amount === 12500 && j.holdings[1].amount === 2000.5 && j.holdings[2].amount === 1000 && j.holdings[3].amount === 300 && j.holdings[1].cls === "gold", r.s + r.b.slice(0, 300));
  // F5 text
  r = await rq(OFF, "GET", "/app.js?v=chat99r2");
  ok("F5 app.js: no Syncing / awaiting-feed display / 0 priced", !/Syncing…|Syncing\\u2026/.test(r.b) && !/\|\| "awaiting feed"|: "awaiting feed"}<\/span>/.test(r.b) && /liveN\?` · \$\{liveN\} priced`/.test(r.b) && /id = "r2-app"/.test(r.b), "");
  // line 1 / maintenance
  r = await rq(OFF, "GET", "/brief/"); ok("maintenance off: /brief/ 200", r.s === 200, r.s);
  r = await rq(ON, "GET", "/brief/"); ok("harness ON copy still gates (regression)", r.s === 503, r.s);
  // security with maintenance off
  r = await rq(OFF, "GET", "/console"); ok("SEC guest /console refused", r.s === 401 || r.s === 403 || r.s === 404 || (r.s === 302 && /login/.test(r.h.location || "")), r.s + " " + r.h.location);
  for (const a of ["/api/admin/ai-readiness", "/api/admin/content", "/api/admin/market-data", "/api/admin/recovery-alert"]) { r = await rq(OFF, "GET", a); ok("SEC guest " + a + " refused", [401, 403, 404].includes(r.s), r.s + r.b.slice(0, 100)); }
  r = await rq(OFF, "GET", "/api/admin/ai-readiness", { user: "hmember" }); ok("SEC member admin API refused", [401, 403, 404].includes(r.s), r.s);
  r = await rq(OFF, "POST", "/api/stripe/webhook", { body: '{"type":"checkout.session.completed"}', headers: { "content-type": "application/json" } }); ok("SEC unsigned Stripe webhook 400", r.s === 400, r.s + r.b.slice(0, 100));
  for (const pg of ["/", "/dashboard/", "/brief/", "/pricing/", "/about/", "/markets/yields/", "/gold/positioning/", "/data-status/"]) {
    r = await rq(OFF, "GET", pg); ok("SEC guest " + pg + ": no admin links/data", r.s === 200 && !/href="\/console|\/api\/admin\/|Admin tools|isAdmin":true/.test(r.b), r.s + " " + (r.b.match(/href="\/console[^"]*"|\/api\/admin\/[a-z-]+|Admin tools/) || [""])[0]);
  }
  done();
})();
