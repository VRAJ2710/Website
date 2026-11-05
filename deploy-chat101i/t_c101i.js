// chat101i: the Bank Rate article is replaced; the other two notes stay.
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const DIR = path.join(__dirname, "..", "deploy-chat101h");
const HERE = __dirname;
const LINE1 = "const BB10I_MAINTENANCE_ON = false; // set false to turn maintenance off (restart to apply)\n";
const PORT = process.env.PORT || "8878";
const B = "http://127.0.0.1:" + PORT;
let pass = 0, fail = 0;
const ok = (c, n, d) => { if (c) pass++; else fail++; console.log((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : "  :: " + String(d).slice(0, 280))); };
const LON = new RegExp("Vraj Patel," + "\\s*" + "London", "i");
const RAW = /GC=F|GBPUSD=X|\^DXY|CL=F|\^TNX|\^VIX/;
const BUY = /\b(buy now|sell now|strong buy|strong sell|most likely|price target)\b/i;
const vis = (h) => h.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ");

(async () => {
  const dir = fs.mkdtempSync("/tmp/c101i-");
  const server = path.join(dir, "server.js");
  const block = fs.readFileSync(path.join(DIR, "server_block_c101h.js"), "utf8");
  const beforeYields = block.slice(block.indexOf('slug: "gold-real-yields-breakeven-inflation"'));
  fs.writeFileSync(server, LINE1 + block);
  const args = [path.join(HERE, "patch_c101i.py"), server, path.join(HERE, "old_bank.frag"), path.join(HERE, "new_bank.frag"), path.join(HERE, "css_old.frag"), path.join(HERE, "css_new.frag")];
  const py = spawn("python3", args, { stdio: "inherit" });
  ok(await new Promise((r) => py.on("exit", r)) === 0, "patch applies once");
  const again = spawn("python3", args, { stdio: "ignore" });
  ok(await new Promise((r) => again.on("exit", r)) !== 0, "second patch is refused");
  const patched = fs.readFileSync(server, "utf8");
  ok(patched.startsWith(LINE1.trim()), "line 1 unchanged");
  ok(patched.includes("chat101i: bank-rate article"), "marker present");
  ok(patched.includes(beforeYields), "evergreen articles are byte-for-byte unchanged");
  ok(!LON.test(patched.slice(patched.indexOf("chat101i:"))), "new helper and article have no London byline");
  const chk = spawn(process.execPath, ["--check", server], { stdio: "inherit" });
  ok(await new Promise((r) => chk.on("exit", r)) === 0, "node --check patched server text");

  const host = fs.readFileSync(path.join(DIR, "fixture_host.js"), "utf8");
  const iife = patched.slice(LINE1.length);
  const live = path.join(dir, "live.js");
  if (!host.includes("// BLOCK")) throw new Error("fixture marker missing");
  fs.writeFileSync(live, host.replace("// BLOCK", iife));
  const chk2 = spawn(process.execPath, ["--check", live], { stdio: "inherit" });
  ok(await new Promise((r) => chk2.on("exit", r)) === 0, "node --check fixture plus patch");
  const srv = spawn(process.execPath, [live], { env: Object.assign({}, process.env, { PORT }), stdio: ["ignore", "ignore", "pipe"] });
  let err = "";
  srv.stderr.on("data", (d) => { err += d; });
  await new Promise((r) => setTimeout(r, 250));
  const get = (p) => fetch(B + p).then(async (r) => ({ s: r.status, b: await r.text() }));
  try {
    const bank = await get("/research/bank-rate-energy-shock-sterling-gold/");
    const v = vis(bank.b);
    ok(bank.s === 200, "bank article 200", bank.s);
    ok(/\$108 per barrel/.test(v) && /216 pence per therm/.test(v) && /15 UK working days ending 27 October/.test(v), "futures average, contract and window");
    ok(/38% and 81%/.test(v) && /front-month/.test(v) && /not a spot price/i.test(v), "scale is labelled as futures, not a decision-day spot");
    ok(/3\.5% in September/.test(v) && /4\.9% in 2027 Q2/.test(v) && /is an outcome/.test(v), "CPI outturn and projection are distinguished");
    ok(/not the start of a hiking cycle/.test(v) && /one-for-now/.test(v) && /up, down, or sideways/.test(v), "Taylor's minutes wording");
    ok(/4\.25%/.test(v) && /unlikely to be sufficient/.test(v) && /range of views/.test(v), "Mann, Pill and the paragraph 19 range");
    ok(/lower margins continue to be the most commonly cited/i.test(v) && /fixed-price contracts and hedging arrangements/.test(v) && !/Box A does not/.test(v), "Box A keeps the margins point; hedging stays with Chart 1.3");
    ok(/Correction, 5 November 2026/.test(v) && (v.match(/Correction, 5 November 2026/g) || []).length === 1, "one dated correction, not a body lecture");
    ok(/additional hikes will likely be required/.test(v) && /further increase in the near term/.test(v) && /argument for a further increase/.test(v), "Greene, Lombardelli and Bailey on a further step");
    ok(/for now/.test(v) && /additional insurance/.test(v) && /up, down, or sideways/.test(v), "Breeden, Dhingra and Taylor are not folded into the others");
    ok(/suggests that risk premia continue to contribute to the upward slope/.test(v) && !/because of risk premia/.test(v), "risk premia wording follows the Report");
    ok(/around 4\.9% at the end of 2027/.test(v) && /around 4\.7% by late 2029/.test(v) && /17 December 2026/.test(v), "curve levels are dated, and the next decision is named");
    ok(/2\.50%/.test(v) && /3\.75%/.test(v) && /Box E/.test(v) && /2021/.test(v), "September foreign policy rates and Box E");
    ok(/Neither sets the sterling price of gold/.test(v) && /slope downward/.test(v) && /late-October averages/.test(v), "table cells match the futures path, not a spot rule");
    ok(/not on a pre-set path/.test(v) && /minutes entries disagree about the next move/.test(v), "deck is the Committee line plus the split");
    const prose = bank.b.split("<h2>The scale is a futures average")[1] || "";
    ok(!/<style/i.test(prose) && /id="c101h-css"/.test(bank.b) && /\.c101h-watch td\{display:block/.test(bank.b), "table CSS lives in the existing style block, not in the prose");
    const ld = JSON.parse((bank.b.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/) || [])[1] || "null");
    ok(ld && ld.description === "The Bank says policy is not on a pre-set path, and members\u2019 minutes entries disagree about the next move." && !String(ld.description).includes("<"), "JSON-LD description is the deck, not the table markup");
    ok(/<table>/.test(bank.b) && /Not a forecast/.test(v) && /not a ranking/.test(v), "monitoring table is a framework");
    ok(/Not investment advice\. Capital at risk\./.test(v) && /Edited by Vraj Patel/.test(bank.b), "byline and disclaimer");
    ok(!LON.test(bank.b) && !RAW.test(v) && !BUY.test(v), "no London, raw codes, tips or most-likely call", (v.match(BUY) || v.match(RAW) || [])[0]);
    ok(/21:57 UK/.test(v) && /not a live price feed/i.test(v), "as-of time is a document check, not a quote");
    ok(bank.b.includes("https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/november-2026") && bank.b.includes("https://www.bankofengland.co.uk/monetary-policy-report/2026/november-2026"), "both Bank links");
    const yields = vis((await get("/research/gold-real-yields-breakeven-inflation/")).b);
    const reserves = vis((await get("/research/central-bank-gold-reserves-value-volume/")).b);
    ok(/21 May 2019/.test(yields) && /Evergreen explainer/.test(yields), "real-yield article unchanged in substance");
    ok(/19:50 UK/.test(reserves) && /imf\.org/.test((await get("/research/central-bank-gold-reserves-value-volume/")).b), "reserves article unchanged in substance");
    const hub = vis((await get("/research/")).b);
    ok(/Capital Sustainability Monitor/.test(hub) && /Check and plan/.test(hub) && /Also from the desk/.test(hub) && /bank-rate-energy-shock-sterling-gold/.test((await get("/research/")).b), "hub keeps the monitor, tools, desk links and the same slug");
    try {
      const puppeteer = require("/tmp/qa-deps/node_modules/puppeteer-core");
      const browser = await puppeteer.launch({ executablePath: "/usr/local/bin/google-chrome", headless: "new", args: ["--no-sandbox", "--disable-dev-shm-usage"] });
      const page = await browser.newPage();
      await page.setViewport({ width: 320, height: 800 });
      await page.goto(B + "/research/bank-rate-energy-shock-sterling-gold/?theme=light", { waitUntil: "networkidle0" });
      const lay = await page.evaluate(() => {
        const td = document.querySelector(".c101h-watch td");
        const st = td ? getComputedStyle(td) : null;
        return {
          display: st && st.display,
          sw: document.documentElement.scrollWidth,
          cw: document.documentElement.clientWidth,
          styleInWatch: !!document.querySelector(".c101h-watch style"),
          text: (document.body.innerText || "").includes("Neither sets the sterling price of gold")
        };
      });
      ok(lay.display === "block" && lay.sw <= lay.cw + 1 && !lay.styleInWatch && lay.text, "phone table stacks, does not overflow, and has no nested style", JSON.stringify(lay));
      await page.screenshot({ path: "/opt/cursor/artifacts/c101i-bank-light-320.png" });
      await browser.close();
    } catch (e) {
      ok(false, "phone table check", e.message);
    }
  } finally {
    srv.kill("SIGTERM");
  }
  if (err.trim()) ok(false, "server stderr empty", err.slice(0, 300));
  console.log((fail ? "FAILED " : "OK ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
