// chat101b browser audit: menu open at 390 and 1280, guest / member / admin, server page and app page.
const pp = require("/workspace/c97/shot/node_modules/puppeteer-core");
const fs = require("fs");
const B = "http://127.0.0.1:8852", OUT = "/workspace/c101b/shots";
const REQ = ["Home","Brief","Playbook","Gold","Dashboard","Market Lab","Signals","Markets","Screener","Sectors","Heatmap","Crypto","Newsroom","Paper","Research","Documents","Geo Ops","Watchlist","Portfolio","Learn","Settings","Calendar","What changed today","Yields","Gold positioning","Alerts","Portfolio X-ray","Data status","Tools","Verify this claim","ISA/SIPP planner","Central banks","Scenario simulator","Filing change detector","About","Pricing"];
const res = []; let pass = 0, fail = 0;
const ok = (c, n, d) => { c ? pass++ : fail++; res.push((c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : " :: " + String(d).slice(0, 300))); };
(async () => {
  const b = await pp.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  const checked = new Map();
  for (const u of [null, "hmember", "hadmin"]) for (const w of [390, 1280]) for (const [kind, pg] of [["server", "/tools/"], ["app", "/dashboard/"], ["server2", "/about"]]) {
    const who = u || "guest", tag = `${who} ${w} ${kind}(${pg})`;
    const ctx = await b.createBrowserContext(); const p = await ctx.newPage();
    await p.setViewport({ width: w, height: w < 500 ? 844 : 900 });
    const errs = []; p.on("pageerror", e => errs.push(e.message));
    if (u) await p.setCookie({ name: "dispatch_session", value: u, domain: "127.0.0.1", path: "/" });
    await p.goto(B + pg, { waitUntil: "networkidle2" }); await new Promise(r => setTimeout(r, 800));
    // hide the install prompt for clean shots
    await p.evaluate(() => { document.querySelectorAll("[class*=install],[id*=install],[data-c101-pwa]").forEach(e => { if (/Install/.test(e.textContent || "") && e.getBoundingClientRect().height < 200) e.style.display = "none"; }); });
    const isApp = await p.evaluate(() => !document.querySelector("header.site"));
    const trig = await p.evaluateHandle(() => [...document.querySelectorAll("header.site details.c101b-all>summary, header.site details.menu>summary, [aria-controls='c93Menu']")].find(e => e.offsetParent !== null && e.getBoundingClientRect().width > 0));
    const tname = await p.evaluate(e => e ? e.textContent.trim() : null, trig);
    ok(!!tname, `${tag} visible menu button`, tname);
    if (!tname) { await ctx.close(); continue; }
    ok(w < 500 ? tname === "Menu" : tname === "All sections", `${tag} button says ${w < 500 ? "Menu" : "All sections"}`, tname);
    // keyboard: focus, Enter opens, focus reaches a menu link, Escape closes and returns focus
    await trig.focus(); await p.keyboard.press("Enter"); await new Promise(r => setTimeout(r, 300));
    const sel = isApp ? "#c93Menu" : (w < 500 ? "header.site details.menu" : "header.site details.c101b-all");
    let open = await p.evaluate(s => { const m = document.querySelector(s); return !!m && (m.tagName === "DETAILS" ? m.open : !m.hidden); }, sel);
    ok(open, `${tag} Enter opens the menu`);
    if (!isApp) await p.keyboard.press("Tab");
    const inMenu = await p.evaluate(s => { const m = document.querySelector(s); const a = document.activeElement; return !!(m && a && m.contains(a) && a.tagName === "A") ? a.textContent.trim() : false; }, sel);
    ok(!!inMenu, `${tag} keyboard focus moves into the menu`, inMenu);
    // contents
    const info = await p.evaluate(s => { const m = document.querySelector(s); const r = m.querySelector(".c101b-panel,nav,.c101b-cols") ? (m.querySelector(".c101b-panel") || m.querySelector("nav") || m).getBoundingClientRect() : m.getBoundingClientRect();
      const L = [...m.querySelectorAll("a")].map(a => [a.childNodes[0] ? a.childNodes[0].textContent.trim() : a.textContent.trim(), a.getAttribute("href"), a.getAttribute("data-c93-nav") || "", a.getBoundingClientRect().width > 0]);
      return { L, left: r.left, right: r.right, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, fs: getComputedStyle(m.querySelector("a")).fontSize }; }, sel);
    const labels = info.L.map(x => x[0]);
    const miss = REQ.filter(l => !labels.includes(l)); ok(!miss.length, `${tag} all ${REQ.length} core sections listed`, miss.join(", "));
    const hidden = info.L.filter(x => !x[3]).map(x => x[0]); ok(!hidden.length, `${tag} every listed link is rendered`, hidden.join(", "));
    const adm = info.L.some(x => x[1] === "/__admin");
    ok(u === "hadmin" ? adm : !adm, `${tag} Admin Console ${u === "hadmin" ? "shown" : "hidden"}`);
    ok(info.sw <= info.cw, `${tag} no horizontal overflow with menu open`, info.sw + "/" + info.cw);
    ok(info.left >= -1 && info.right <= info.cw + 1, `${tag} menu inside the screen`, info.left + ".." + info.right);
    const fn = `${OUT}/${who}_${w}_${isApp ? "app" : "site"}${kind === "server2" ? "_about" : ""}.png`;
    await p.screenshot({ path: fn }); res.push("SHOT " + fn);
    // Escape closes and returns focus to the button
    await p.keyboard.press("Escape"); await new Promise(r => setTimeout(r, 200));
    open = await p.evaluate(s => { const m = document.querySelector(s); return !!m && (m.tagName === "DETAILS" ? m.open : !m.hidden); }, sel);
    const back = await p.evaluate(e => document.activeElement === e, trig);
    ok(!open && back, `${tag} Escape closes and focus returns to the button`, open + " " + back);
    // every link resolves (fetch as this user, following redirects)
    for (const [l, h] of info.L) {
      const key = who + " " + h; if (checked.has(key) || !h || h.startsWith("/__auth")) continue;
      const r = await p.evaluate(async h => { try { const x = await fetch(h, { credentials: "include" }); const t = await x.text(); return [x.status, t.length, x.url.replace(location.origin, ""), /<title>[^<]*(Not found|404)/i.test(t)]; } catch (e) { return [0, 0, String(e), true]; } }, h);
      checked.set(key, r); ok(r[0] === 200 && r[1] > 800 && !r[3], `${who} link ${l} ${h} -> ${r[2]} works`, r.join(" "));
    }
    // app pages: click every in-app link from the menu and check a page renders with no script error
    if (isApp && u && w === 1280) {
      const ids = info.L.filter(x => x[2]).map(x => [x[0], x[2]]);
      for (const [l, id] of ids) {
        await p.evaluate(() => { const b = [...document.querySelectorAll("[aria-controls='c93Menu']")].find(e => e.offsetParent); const m = document.getElementById("c93Menu"); if (!m || m.hidden) b.click(); });
        await new Promise(r => setTimeout(r, 150));
        const e0 = errs.length;
        await p.evaluate(id => { const a = document.querySelector(`#c93Menu a[data-c93-nav="${id}"]`); a.click(); }, id);
        await new Promise(r => setTimeout(r, 900));
        const st = await p.evaluate(() => ({ len: (document.querySelector("main,#app,#content,body") || document.body).innerText.length, nf: /Page not found/.test(document.body.innerText), menu: !!(document.getElementById("c93Menu") && !document.getElementById("c93Menu").hidden) }));
        const pgNow = await p.evaluate(() => typeof pg !== "undefined" ? pg : "?"); ok(errs.length === e0 && st.len > 300 && !st.nf && (pgNow === id || id === "settings" || id === "home"), `${who} app: menu ${l} (${id}) opens a page [pg=${pgNow}]`, JSON.stringify(st) + " " + errs.slice(e0).join(";"));
      }
    }
    ok(!errs.length, `${tag} no script errors`, errs.join(" | "));
    await ctx.close();
  }
  // ?open= hand-off for members
  for (const [p0, id] of [["/documents/", "intel"], ["/portfolio/holdings/", "port"]]) {
    const ctx = await b.createBrowserContext(); const p = await ctx.newPage(); await p.setViewport({ width: 1280, height: 900 });
    await p.setCookie({ name: "dispatch_session", value: "hmember", domain: "127.0.0.1", path: "/" });
    await p.goto(B + p0, { waitUntil: "networkidle2" }); await new Promise(r => setTimeout(r, 1500));
    const st = await p.evaluate(() => ({ url: location.pathname + location.search, cur: typeof pg !== "undefined" ? pg : "?", txt: document.body.innerText.slice(0, 4000) }));
    ok(st.cur === id, `member ${p0} opens ${id} in the app`, st.url + " pg=" + st.cur);
    fs.writeFileSync(`${OUT}/open_${id}.txt`, st.txt); await p.screenshot({ path: `${OUT}/member_open_${id}.png` }); res.push(`SHOT ${OUT}/member_open_${id}.png (page: ${st.cur})`);
    await ctx.close();
  }
  await b.close();
  fs.writeFileSync(`${OUT}/audit.txt`, res.join("\n") + `\n${pass} passed, ${fail} failed\n`);
  console.log(res.filter(x => !x.startsWith("PASS")).join("\n")); console.log(`${pass} passed, ${fail} failed`);
})().catch(e => { console.log("CRASH", e.stack); process.exit(1); });
