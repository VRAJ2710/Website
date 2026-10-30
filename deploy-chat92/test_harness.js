const assert = require("assert"); const { S, call } = require("./h.js");
function head(b) {
  const g = (re) => { const m = b.match(re); return m ? m[1] : null; };
  return { title: g(/<title>([^<]*)<\/title>/), desc: g(/<meta name="description" content="([^"]*)"/), canon: g(/<link rel="canonical" href="([^"]*)"/),
    ogt: g(/property="og:title" content="([^"]*)"/), ogd: g(/property="og:description" content="([^"]*)"/), ogu: g(/property="og:url" content="([^"]*)"/), ogi: g(/property="og:image" content="([^"]*)"/), ogs: g(/property="og:site_name" content="([^"]*)"/),
    twc: g(/name="twitter:card" content="([^"]*)"/), twt: g(/name="twitter:title" content="([^"]*)"/), twd: g(/name="twitter:description" content="([^"]*)"/), twi: g(/name="twitter:image" content="([^"]*)"/), n_title: (b.match(/<title>/g) || []).length };
}
const B = "/research/capital-sustainability", O = "https://thedispatch.uk";
const radar = ["Capital Sustainability Monitor | The Dispatch Market", O + B];
const cases = [[B, ...radar], [B + "/", ...radar], [B + "/method", "How to read the Capital Sustainability Monitor | The Dispatch Market", O + B + "/method"], [B + "/METHOD/", "How to read the Capital Sustainability Monitor | The Dispatch Market", O + B + "/method"],
  [B + "/MSFT", "Microsoft (MSFT) · Capital Sustainability Monitor | The Dispatch Market", O + B + "/MSFT"], [B + "/msft", "Microsoft (MSFT) · Capital Sustainability Monitor | The Dispatch Market", O + B + "/MSFT"],
  [B + "/NVDA", null, O + B + "/NVDA"], [B + "/ZZZZ", ...radar], [B + "/a.b-c", ...radar]];
(async () => {
  for (const [u, t, c] of cases) {
    const r = await call(S.__h.inner, "GET", u); assert.strictEqual(r.status, 200, u); const h = head(r.body);
    if (t) assert.strictEqual(h.title, t.replace(/&/g, "&amp;"), u); assert.strictEqual(h.canon, c, u);
    assert.strictEqual(h.n_title, 1); assert.strictEqual(h.ogt, h.title); assert.strictEqual(h.twt, h.title); assert.strictEqual(h.ogu, c); assert.strictEqual(h.ogd, h.desc); assert.strictEqual(h.twd, h.desc);
    assert.ok(/Not a recommendation\. Capital at risk\./.test(h.desc)); assert.ok(!/\b(buy|sell)\b/i.test(h.title + h.desc));
    console.log("GET", u, "->", r.status, "|", h.title, "|", h.canon, "|", h.desc.slice(0, 50) + "…");
  }
  const hd = await call(S.__h.inner, "HEAD", B + "/MSFT"); console.log("HEAD", B + "/MSFT ->", hd.status);
  const pr = await call(S.__h.inner, "GET", "/pricing"); const ph = head(pr.body);
  assert.strictEqual(pr.status, 200); assert.strictEqual(ph.ogt, "Pricing · The Dispatch Market"); assert.strictEqual(ph.twt, ph.ogt); assert.strictEqual(ph.ogu, O + "/pricing"); assert.strictEqual(ph.ogi, O + "/og-card.png"); assert.strictEqual(ph.twi, ph.ogi); assert.strictEqual(ph.ogs, "The Dispatch Market"); assert.strictEqual(ph.twc, "summary_large_image"); assert.strictEqual(ph.ogd, ph.desc); assert.strictEqual(ph.twd, ph.desc);
  console.log("GET /pricing ->", pr.status, JSON.stringify(ph));
  // maintenance gate (outer handler, line 1 = true)
  const mt = [["GET", "/manifest.json", 200], ["HEAD", "/manifest.json", 200], ["POST", "/manifest.json", 503], ["GET", "/manifest.json/", 503], ["GET", "/manifest.json/x", 503], ["GET", "/manifest.jsonx", 503], ["GET", "/app.js", 503], ["GET", "/", 200], ["GET", B, 503], ["GET", "/pricing", 503], ["GET", "/api/monitor", 503], ["GET", "/health", 200]];
  for (const [m, u, exp] of mt) { const r = await call(S.__h.outer, m, u); console.log("maintenance", m, u, "->", r.status, r.headers["content-type"] || ""); assert.strictEqual(r.status, exp, m + " " + u); if (u !== "/manifest.json" && u !== "/health" && exp !== 0 && !/^\/api/.test(u) && m !== "HEAD") assert.ok(/Under maintenance/.test(r.body), "maint page " + u); if (u === "/manifest.json" && m === "GET") { JSON.parse(r.body); assert.ok(!/https?:\/\/(?!thedispatch\.uk|www\.w3\.org\/2000\/svg)/.test(r.body)); console.log("  manifest body:", r.body.replace(/\s+/g, " ").slice(0, 160) + "…"); } }
  // /api/monitor
  const am = await call(S.__h.inner, "GET", "/api/monitor"); console.log("GET /api/monitor ->", am.status);
  if (am.status === 200) { const j = JSON.parse(am.body); const s = JSON.stringify(j).match(/"sec":\{[^}]*\}/); console.log("  sec:", s ? s[0] : "(not found)"); }
  const home = await call(S.__h.inner, "GET", "/"); console.log("GET / (code render, no DB) ->", home.status, "matches /dispatch\\W+markets/i:", (home.body.match(/dispatch\W+markets/ig) || []).length);
  console.log("ALL OK"); process.exit(0);
})().catch(e => { console.error("FAIL", e.message); process.exit(1); });
