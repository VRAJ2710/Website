// chat101h harness: article routes on a fixture host, plus the app.js append against the downloaded live app when present.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const crypto = require("crypto");
const DIR = __dirname;
const PORT = process.env.PORT || "8877";
const B = "http://127.0.0.1:" + PORT;
const LIVE_APP = process.env.LIVE_APP || "/tmp/livechk/https___thedispatch_uk_app_js";
let pass = 0, fail = 0;
const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 240))); };
const ck = (u, extra) => [u ? "dispatch_session=" + u : "", extra || ""].filter(Boolean).join("; ");
const get = (p, u, extra) => fetch(B + p, { redirect: "manual", headers: { cookie: ck(u, extra) } });
const txt = async (p, u, extra) => { const r = await get(p, u, extra); return { s: r.status, h: r.headers, b: await r.text() }; };
const vis = (h) => h.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ");
const DISC = /Not investment advice\. Capital at risk\./;
const RAW = /GC=F|GBPUSD=X|\^DXY|DX-Y\.NYB|EURUSD=X|CL=F|BZ=F|\^TNX|\^VIX/;
const LON = new RegExp("Vraj Patel," + "\\s*" + "London", "i");
const BUY = /\b(buy now|sell now|strong buy|strong sell|we recommend buying|you should (buy|sell)|price target)\b/i;
const SLUGS = ["bank-rate-energy-shock-sterling-gold", "gold-real-yields-breakeven-inflation", "central-bank-gold-reserves-value-volume"];
const USERS = [null, "hmember", "hprem", "hadmin"];

function buildServer(dest) {
  const host = fs.readFileSync(path.join(DIR, "fixture_host.js"), "utf8");
  const block = fs.readFileSync(path.join(DIR, "server_block_c101h.js"), "utf8");
  if (!host.includes("// BLOCK")) throw new Error("fixture marker missing");
  fs.writeFileSync(dest, host.replace("// BLOCK", block));
}

(async () => {
  const dest = path.join(fs.mkdtempSync("/tmp/c101h-fix-"), "server.js");
  buildServer(dest);
  const child = spawn(process.execPath, ["--check", dest], { stdio: "inherit" });
  const checked = await new Promise((r) => child.on("exit", r));
  ok(checked === 0, "node --check fixture server");
  const srv = spawn(process.execPath, [dest], { env: Object.assign({}, process.env, { PORT }), stdio: ["ignore", "pipe", "pipe"] });
  let err = "";
  srv.stderr.on("data", (d) => { err += d; });
  await new Promise((r) => setTimeout(r, 250));
  try {
    const hub = await txt("/research/");
    const hv = vis(hub.b);
    ok(hub.s === 200 && /Capital Sustainability Monitor/.test(hv) && /Check and plan/.test(hv) && /Also from the desk/.test(hv), "research hub keeps monitor, tools and desk links");
    ok(/data-c101h-articles/.test(hub.b) && SLUGS.every((s) => hub.b.includes("/research/" + s + "/")), "research hub lists three articles");
    ok(DISC.test(hv) && /Edited by Vraj Patel/.test(hub.b) && !LON.test(hub.b), "hub disclaimer, byline, no London");
    ok(/Evergreen explainer/.test(hv) && /Timely analysis/.test(hv), "hub labels evergreen and timely");
    for (const slug of SLUGS) for (const u of USERS) {
      const r = await txt("/research/" + slug + "/", u);
      const v = vis(r.b);
      ok(r.s === 200, `${slug} ${u || "guest"} 200`, r.s);
      ok(DISC.test(v), `${slug} ${u || "guest"} disclaimer visible`);
      ok(/Edited by Vraj Patel/.test(r.b) && !/Reviewed by Vraj|personally reviewed/i.test(v), `${slug} byline is Edited by, not a review claim`);
      ok(!LON.test(r.b) && !RAW.test(v) && !BUY.test(v), `${slug} ${u || "guest"} no London, raw codes or tips`, (v.match(RAW) || v.match(BUY) || [])[0]);
      ok(/rel="canonical" href="https:\/\/thedispatch\.uk\/research\/${slug}\/"/.test(r.b) || r.b.includes('rel="canonical" href="https://thedispatch.uk/research/' + slug + '/"'), `${slug} canonical`);
      ok(/application\/ld\+json/.test(r.b) && /"editor"/.test(r.b) && !/"author"\s*:/.test(r.b), `${slug} JSON-LD editor, no author`);
      ok(r.b.includes("<h1>") && /<h2>/.test(r.b) && /href="https:\/\//.test(r.b), `${slug} headings and external source link`);
      if (u) ok(/Your desk/.test(r.b), `${slug} ${u} signed-in header`);
      else ok(/Sign in/.test(r.b), `${slug} guest sign-in link`);
    }
    const bankRaw = await txt("/research/bank-rate-energy-shock-sterling-gold/");
    const bank = vis(bankRaw.b);
    ok(/4%/.test(bank) && /0\.25 percentage points/.test(bank) && /8–1/.test(bank) && /4 November 2026/.test(bank), "Bank article keeps the checked decision figures");
    ok(/20:01 UK \(GMT\)/.test(bank) && /bankofengland\.co\.uk\/monetary-policy-summary-and-minutes\/2026\/november-2026/.test(bankRaw.b) && /monetary-policy-report\/2026\/november-2026/.test(bankRaw.b), "Bank article as-of and both BoE links");
    ok(!/3\.5%|\$108|4\.25%/.test(bank), "Bank article does not add CPI, oil or the dissent size as a quote");
    const realRaw = await txt("/research/gold-real-yields-breakeven-inflation/");
    const real = vis(realRaw.b);
    ok(/Evergreen explainer/.test(real) && /federalreserve\.gov/.test(realRaw.b) && /21 May 2019/.test(real) && /no claim about the latest yield/i.test(real), "real-yield article is evergreen and sourced");
    const imfRaw = await txt("/research/central-bank-gold-reserves-value-volume/");
    const imf = vis(imfRaw.b);
    ok(/Evergreen explainer/.test(imf) && /imf\.org\/external\/np\/sta\/ir\/IRProcessWeb\/pdf\/guide\.pdf/.test(imfRaw.b) && /19:50 UK/.test(imf) && /No current reserve total/.test(imf), "reserves article is evergreen, IMF link, 19:50 check");
    for (const slug of SLUGS) {
      const r = await get("/research/" + slug);
      ok(r.status === 301 && r.headers.get("location") === "/research/" + slug + "/", slug + " slash redirect", r.status + " " + r.headers.get("location"));
    }
    for (const p of ["/research/capital-sustainability", "/research/capital-sustainability/ORCL", "/research/sec/", "/research/filing-changes/", "/research/research-desk/", "/gold/", "/brief/", "/central-banks/", "/tools/"]) {
      const r = await txt(p);
      ok(r.s === 200 && !/data-c101h-articles/.test(r.b) && !/c101h-article/.test(r.b), "existing route untouched " + p, r.s);
    }
    const sm = await txt("/sitemap.xml");
    ok(SLUGS.every((s) => sm.b.includes("https://thedispatch.uk/research/" + s + "/")) && sm.b.includes("/research/capital-sustainability") && sm.b.includes("/research/filing-changes/"), "sitemap adds articles and keeps existing locs");
    const preview = await txt("/research/bank-rate-energy-shock-sterling-gold/", "hadmin", "dispatch_preview=1");
    ok(preview.s === 200 && /Sign in/.test(preview.b) && DISC.test(vis(preview.b)), "admin guest preview still shows the article as a guest");
    const missing = await txt("/research/not-a-real-article/");
    ok(missing.s === 404, "unknown research slug still 404", missing.s);
  } finally {
    srv.kill("SIGTERM");
  }
  if (err.trim()) ok(false, "server stderr empty", err.slice(0, 300));

  // app.js append against the downloaded live file, when that file is the chat101g build
  if (fs.existsSync(LIVE_APP)) {
    const md5 = crypto.createHash("md5").update(fs.readFileSync(LIVE_APP)).digest("hex");
    ok(md5 === "0b4c442a055584920d9539fb50c9a7f1", "downloaded app.js is the live chat101g build", md5);
    const scratch = fs.mkdtempSync("/tmp/c101h-app-");
    const app = path.join(scratch, "app.js");
    const server = path.join(scratch, "server.js");
    const index = path.join(scratch, "index.html");
    fs.copyFileSync(LIVE_APP, app);
    fs.writeFileSync(server, "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\n// chat101f: market quotes first\nc97Transform\nrenderPublicSitemap\nc93Html\n");
    fs.writeFileSync(index, '<script defer src="/app.js?v=chat101g"></script>\n');
    const py = spawn("python3", [path.join(DIR, "patch_c101h.py"), server, app, index, path.join(DIR, "server_block_c101h.js"), path.join(DIR, "app_block_c101h.js")], { stdio: "inherit" });
    ok(await new Promise((r) => py.on("exit", r)) === 0, "patch applies to live app.js shape");
    const chk = spawn(process.execPath, ["--check", app], { stdio: "inherit" });
    ok(await new Promise((r) => chk.on("exit", r)) === 0, "node --check patched live app.js");
    const body = fs.readFileSync(app, "utf8");
    ok(body.includes("data-c101h-app") && body.includes("chat101g: phone Account drawer") && body.includes("/research/bank-rate-energy-shock-sterling-gold/") && !/GC=F/.test(body.slice(body.lastIndexOf("chat101h:"))), "patched app keeps chat101g and adds article links");
    const again = spawn("python3", [path.join(DIR, "patch_c101h.py"), server, app, index, path.join(DIR, "server_block_c101h.js"), path.join(DIR, "app_block_c101h.js")]);
    ok(await new Promise((r) => again.on("exit", r)) !== 0, "second patch is refused");
    const hash = crypto.createHash("sha256").update(fs.readFileSync(app)).digest("hex");
    const md = crypto.createHash("md5").update(fs.readFileSync(app)).digest("hex");
    console.log("NEW_APP_MD5 " + md);
    console.log("NEW_APP_SHA256 " + hash);
  } else ok(false, "live app.js available for the append test", LIVE_APP);

  console.log((fail ? "FAILED " : "OK ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
