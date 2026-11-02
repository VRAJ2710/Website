// chat101c browser audit: full-screen menu sheet (Menu and All sections), one column of dropdown groups, X close, body lock. 320/390/1280, light/dark, guest/member/admin.
const pp = require("/workspace/c97/shot/node_modules/puppeteer-core");
const fs = require("fs");
const B = "http://127.0.0.1:8852", OUT = process.env.OUT || "/workspace/c101c/shots";
const REQ = ["Home","Brief","Playbook","Gold","Dashboard","Market Lab","Signals","Markets","Screener","Sectors","Heatmap","Crypto","Newsroom","Paper","Research","Documents","Geo Ops","Watchlist","Portfolio","Learn","Settings","Calendar","What changed today","Yields","Gold positioning","Alerts","Portfolio X-ray","Data status","Tools","Verify this claim","ISA/SIPP planner","Central banks","Scenario simulator","Filing change detector","About","Pricing"];
const GROUPS = ["Start","Desk","Markets","Research","Book","Gold and macro","Tools and filings","About","Account"];
const res = []; let pass = 0, fail = 0;
const ok = (c, n, d) => { c ? pass++ : fail++; const L = (c ? "PASS " : "FAIL ") + n + (c || d === undefined ? "" : " :: " + String(d).slice(0, 300)); res.push(L); console.log(L); };
const sleep = t => new Promise(r => setTimeout(r, t));
const SEL = "#c93Menu, header.site details.menu, header.site details.c101b-all";
(async () => {
  const b = await pp.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  const checked = new Map();
  async function page(u, w, dark, pth, extra) {
    const ctx = await b.createBrowserContext(); const p = await ctx.newPage();
    await p.setViewport({ width: w, height: w < 1000 ? 844 : 900 });
    const errs = []; p.on("pageerror", e => errs.push(e.message)); p.__nav = []; p.on("framenavigated", f => { if (f === p.mainFrame()) p.__nav.push(f.url().replace(B, "")); });
    const ck = [];
    if (u) ck.push({ name: "dispatch_session", value: u, domain: "127.0.0.1", path: "/" });
    if (dark) ck.push({ name: "dispatch_theme", value: "dark", domain: "127.0.0.1", path: "/" });
    if (extra) ck.push(...extra);
    if (ck.length) await p.setCookie(...ck);
    await p.goto(B + pth, { waitUntil: "networkidle2" }); await sleep(700);
    await p.evaluate(() => { document.querySelectorAll("[class*=install],[id*=install],[data-c101-pwa]").forEach(e => { if (/Install/.test(e.textContent || "") && e.getBoundingClientRect().height < 200) e.style.display = "none"; }); });
    const isApp = await p.evaluate(() => !document.querySelector("header.site"));
    return { ctx, p, errs, isApp };
  }
  const trigger = p => p.evaluateHandle(() => [...document.querySelectorAll("header.site details.c101b-all>summary, header.site details.menu>summary, [aria-controls='c93Menu']")].find(e => e.offsetParent !== null && e.getBoundingClientRect().width > 0));
  const menuSel = (isApp, w) => isApp ? "#c93Menu" : (w < 1280 ? "header.site details.menu" : "header.site details.c101b-all");
  const isOpen = (p, s) => p.evaluate(s => { const m = document.querySelector(s); return !!m && (m.tagName === "DETAILS" ? m.open : !m.hidden); }, s);
  const state = (p, s) => p.evaluate(s => {
    const m = document.querySelector(s), sh = m.querySelector("nav.c101c-sheet") || m, box = sh.getBoundingClientRect(), x = sh.querySelector(".c101c-x"), xr = x && x.getBoundingClientRect();
    const pts = [[5, 5], [innerWidth / 2, innerHeight / 2], [innerWidth - 5, innerHeight - 5], [5, innerHeight - 5], [innerWidth - 5, 70]].map(([a, b]) => { const e = document.elementFromPoint(a, b); return !!e && sh.contains(e); });
    const btns = [...m.querySelectorAll(".c101c-btn")].map(x => { const l = document.getElementById(x.getAttribute("aria-controls")); const r = x.getBoundingClientRect();
      return { t: x.querySelector(".c101c-t").textContent, tag: x.tagName, type: x.type, exp: x.getAttribute("aria-expanded"), ctl: !!l, hid: l ? l.hidden : null, lab: l ? l.getAttribute("aria-labelledby") === x.id : false,
        n: +x.querySelector(".c101c-n").textContent.replace(/\D/g, ""), li: l ? l.querySelectorAll("a").length : -1, h: r.height }; });
    const L = [...m.querySelectorAll("a")].map(a => { const r = a.getBoundingClientRect(); return { l: a.textContent.trim(), h: a.getAttribute("href"), id: a.getAttribute("data-c93-nav") || "", vis: r.width > 0 && r.height > 0, ht: r.height, cta: /c101c-cta|cta/.test(a.className) && !!a.closest(".c101c-top") }; });
    const cta = m.querySelector(".c101c-top a"), note = m.querySelector(".c101c-note"), last = [...m.querySelectorAll("*")].filter(e => e.offsetParent !== null || e.getClientRects().length).pop();
    const nr = note && note.getBoundingClientRect(), fb = m.querySelector(".c101c-btn");
    const cs = e => e ? getComputedStyle(e) : {};
    return { btns, L, acc: !!m.querySelector(".c101c-acc"), grid: !!m.querySelector(".c101c-grid"), sheet: sh.classList.contains("c101c-sheet"), pts, lock: document.documentElement.classList.contains("c101c-lock"), bodyOv: cs(document.body).overflow, z: +cs(sh).zIndex, pos: cs(sh).position,
      x: x ? { lab: x.getAttribute("aria-label"), w: xr.width, h: xr.height, right: xr.right, top: xr.top } : null, cols: new Set([...sh.querySelectorAll(".c101c-btn")].map(b => Math.round(b.getBoundingClientRect().left))).size,
      cta: cta ? { t: cta.textContent.trim(), top: cta.getBoundingClientRect().top, h: cta.getBoundingClientRect().height, bg: cs(cta).backgroundColor, fg: cs(cta).color } : null,
      firstBtnTop: fb ? fb.getBoundingClientRect().top : null,
      note: note ? { fs: parseFloat(cs(note).fontSize), col: cs(note).color, last: !note.nextElementSibling || note.nextElementSibling.tagName === "NOSCRIPT", text: note.textContent } : null,
      ink: cs(document.body).color, bodyBg: cs(document.body).backgroundColor, panelBg: cs(sh).backgroundColor,
      left: box.left, right: box.right, top: box.top, bottom: box.bottom, sh: sh.scrollHeight, ch: sh.clientHeight,
      sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, vh: innerHeight, dark: document.documentElement.className };
  }, s);
  const lum = c => { const m = (c || "").match(/[\d.]+/g); if (!m) return -1; return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255; };
  const want = (pth, pgId) => { // expected open group index
    if (pth === "/") return -1;
    const map = { "/gold/": 0, "/tools/verify/": 6, "/about": 7, "/what-changed/": 5, "/dashboard/": 1, "/research/sec/": 6, "/central-banks/": 5, "/research/": 3, "/markets/": 2, "/tools/": 6, "/pricing/": 7 };
    return pth in map ? map[pth] : null;
  };
  const cfgs = [];
  for (const u of [null, "hmember", "hadmin"]) for (const w of [320, 390, 1280]) for (const dark of [false, true]) for (const pth of ["/", "/tools/verify/", "/dashboard/"]) cfgs.push([u, w, dark, pth]);
  for (const pth of ["/gold/", "/about", "/what-changed/", "/research/", "/markets/", "/central-banks/"]) for (const u of [null, "hmember"]) cfgs.push([u, 390, false, pth]);
  cfgs.push(["hadmin", 390, false, "/tools/verify/", [{ name: "dispatch_preview", value: "1", domain: "127.0.0.1", path: "/" }]]);
  cfgs.push(["hadmin", 390, false, "/dashboard/", [{ name: "dispatch_preview", value: "1", domain: "127.0.0.1", path: "/" }]]);
  for (const [u, w, dark, pth, extra] of cfgs) {
    if (process.env.ONLY && !new RegExp(process.env.ONLY).test(`${u || "guest"} ${w} ${dark ? "dark" : "light"} ${pth}${extra ? " preview" : ""}`)) continue;
    const who = (u || "guest") + (extra ? "+preview" : ""), adminView = u === "hadmin" && !extra;
    const { ctx, p, errs, isApp } = await page(u, w, dark, pth, extra);
    try {
    const tag = `${who} ${w} ${dark ? "dark" : "light"} ${isApp ? "app" : "site"}${pth}`;
    // no admin leak anywhere on the page (closed state too)
    const admDom = await p.evaluate(() => document.querySelectorAll('a[href="/__admin"]').length);
    if (!adminView) ok(admDom === 0, `${tag} no Admin Console link in the page`, admDom);
    let trig = await trigger(p); const tname = await p.evaluate(e => e ? e.textContent.trim() : null, trig);
    ok(tname === (w < 1280 ? "Menu" : "All sections"), `${tag} button says ${w < 1280 ? "Menu" : "All sections"}`, tname);
    if (!tname) { await ctx.close(); continue; }
    const sel = menuSel(isApp, w);
    const ov0 = await p.evaluate(() => getComputedStyle(document.body).overflow);
    await trig.focus(); await p.keyboard.press("Enter"); await sleep(300);
    ok(await isOpen(p, sel), `${tag} Enter opens the menu`);
    const f1 = await p.evaluate(s => { const a = document.activeElement, m = document.querySelector(s); return m && m.contains(a) ? (a.getAttribute("aria-label") || a.textContent.trim()) : null; }, sel);
    ok(f1 === "Close menu", `${tag} focus moves to the close X`, f1);
    let s = await state(p, sel);
    const pgId = isApp ? await p.evaluate(() => typeof pg !== "undefined" ? pg : "") : "";
    ok(s.sheet && s.pos === "fixed" && s.left <= 0.5 && s.top <= 0.5 && s.right >= s.cw - 0.5 && s.bottom >= s.vh - 0.5, `${tag} sheet covers the whole screen`, [s.pos, s.left, s.top, s.right, s.bottom, s.cw, s.vh].join(","));
    ok(s.pts.every(Boolean), `${tag} nothing from the page shows through (hit-test corners/centre)`, s.pts.join(","));
    const alpha = (s.panelBg.match(/rgba\([^)]*,\s*([\d.]+)\)/) || [0, "1"])[1];
    ok(+alpha === 1, `${tag} solid sheet background`, s.panelBg);
    if (dark) ok(lum(s.panelBg) < 0.2 && lum(s.panelBg) >= 0, `${tag} dark sheet background`, s.panelBg); else ok(lum(s.panelBg) > 0.85, `${tag} light sheet background`, s.panelBg);
    ok(s.lock && s.bodyOv === "hidden", `${tag} body scroll locked while open`, s.lock + " " + s.bodyOv);
    const y0 = await p.evaluate(() => scrollY); await p.mouse.move(s.cw / 2, s.vh - 20); await p.mouse.wheel({ deltaY: 900 }); await sleep(250);
    const y1 = await p.evaluate(() => scrollY); ok(y0 === y1, `${tag} page behind does not scroll`, y0 + "->" + y1);
    await p.evaluate(s => { const sh = document.querySelector(s).querySelector("nav.c101c-sheet") || document.querySelector(s); sh.scrollTop = 0; }, sel);
    ok(s.x && s.x.lab === "Close menu" && s.x.w >= 44 && s.x.h >= 44 && s.x.right > s.cw - 30 && s.x.top < 20, `${tag} X top right, labelled, 44px`, JSON.stringify(s.x));
    ok(s.sw <= s.cw, `${tag} no horizontal overflow`, s.sw + "/" + s.cw);
    ok(s.acc && !s.grid && s.cols === 1, `${tag} one column of dropdown groups`, s.cols);
    ok(s.btns.length === 9 && s.btns.map(x => x.t).join("|") === GROUPS.join("|"), `${tag} nine group headings in order`, s.btns.map(x => x.t).join("|"));
    ok(s.btns.every(x => x.tag === "BUTTON" && x.type === "button" && x.ctl && x.lab && (x.exp === "true") === (x.hid === false)), `${tag} headings are buttons with aria-expanded/aria-controls in step`, JSON.stringify(s.btns.filter(x => !(x.tag === "BUTTON" && x.ctl && x.lab && (x.exp === "true") === (x.hid === false)))));
    ok(s.btns.every(x => x.h >= 44), `${tag} heading targets ≥44px`, s.btns.map(x => x.h).join(","));
    ok(s.btns.every(x => x.n === x.li), `${tag} counts match the links`, s.btns.map(x => x.n + "/" + x.li).join(","));
    const hst = await p.evaluate(s => { const t = document.querySelector(s).querySelector(".c101c-btn .c101c-t"), c = getComputedStyle(t.closest(".c101c-btn")); return [c.textTransform, c.fontSize, c.letterSpacing, c.fontWeight]; }, sel);
    ok(hst[0] === "uppercase" && hst[1] === "12px" && Math.abs(parseFloat(hst[2]) - 0.72) < 0.05 && +hst[3] >= 600, `${tag} old 'All sections' label style (600 12px uppercase .06em)`, hst.join(","));
    const open = s.btns.map((x, i) => x.exp === "true" ? i : -1).filter(i => i >= 0), wg = want(pth, pgId);
    ok(open.length <= 1, `${tag} at most one group open by default`, open.join(","));
    if (wg !== null) ok(wg === -1 ? open.length === 0 : open.length === 1 && open[0] === wg, `${tag} default open group = ${wg < 0 ? "none" : GROUPS[wg]}`, open.map(i => GROUPS[i]).join(",") || "none");
    const vis = s.L.filter(x => x.vis && !x.cta).length, inOpen = open.reduce((a, i) => a + s.btns[i].li, 0);
    ok(vis === inOpen, `${tag} only the open group's links show`, vis + " vs " + inOpen);
    ok(s.cta && s.cta.t === (u && !extra ? "Your desk" : "Sign in") && s.cta.top < s.firstBtnTop && s.cta.h >= 44, `${tag} primary "${u && !extra ? "Your desk" : "Sign in"}" at the top`, JSON.stringify(s.cta));
    ok(s.cta && Math.abs(lum(s.cta.bg) - lum(s.cta.fg)) > 0.4, `${tag} primary action has strong contrast`, s.cta && s.cta.bg + " / " + s.cta.fg);
    ok(s.note && s.note.last && s.note.fs <= 13 && /signed-in readers or members/.test(s.note.text), `${tag} sign-in note small, at the bottom`, JSON.stringify(s.note));
    // Tab stays inside the sheet: Shift+Tab from the X lands on the last control in the sheet
    await p.evaluate(s => document.querySelector(s).querySelector(".c101c-x").focus(), sel); await p.keyboard.down("Shift"); await p.keyboard.press("Tab"); await p.keyboard.up("Shift");
    ok(await p.evaluate(s => document.querySelector(s).contains(document.activeElement), sel), `${tag} Tab focus trapped in the sheet`, await p.evaluate(() => (document.activeElement.outerHTML || "").slice(0, 80) + " menu " + !!document.getElementById("c93Menu")) + " nav " + JSON.stringify(p.__nav));
    // keyboard: Enter toggles, Space toggles back
    const r = await p.evaluate(s => { const m = document.querySelector(s); const b0 = m.querySelector(".c101c-btn"); b0.focus(); return [document.activeElement === b0, b0.getAttribute("aria-expanded")]; }, sel);
    await p.keyboard.press("Enter"); await sleep(80);
    const e1 = await p.evaluate(s => { const b0 = document.querySelector(s).querySelector(".c101c-btn"); return [b0.getAttribute("aria-expanded"), document.getElementById(b0.getAttribute("aria-controls")).hidden]; }, sel);
    await p.keyboard.press("Space"); await sleep(80);
    const e2 = await p.evaluate(s => { const b0 = document.querySelector(s).querySelector(".c101c-btn"); return [b0.getAttribute("aria-expanded"), document.getElementById(b0.getAttribute("aria-controls")).hidden]; }, sel);
    const flip = v => v === "true" ? "false" : "true";
    ok(r[0] && e1[0] === flip(r[1]) && e1[1] === (e1[0] !== "true") && e2[0] === r[1] && e2[1] === (e2[0] !== "true"), `${tag} Enter and Space toggle a heading`, JSON.stringify([r, e1, e2]));
    ok(await isOpen(p, sel), `${tag} menu stays open while toggling`);
    const nm = `${who}_${w}_${dark ? "dark" : "light"}_${isApp ? "app" : "site"}${pth.replace(/\//g, "_")}`;
    if (["/", "/tools/verify/", "/dashboard/"].includes(pth) && !extra) { await p.screenshot({ path: `${OUT}/${nm}_menu_open.png` }); res.push(`SHOT ${OUT}/${nm}_menu_open.png`); }
    // open every group: every link becomes visible and reachable by scrolling the sheet
    await p.evaluate(s => document.querySelector(s).querySelectorAll('.c101c-btn[aria-expanded="false"]').forEach(b => b.click()), sel); await sleep(150);
    s = await state(p, sel);
    ok(s.btns.every(x => x.exp === "true" && !x.hid), `${tag} every group opens`);
    ok(s.L.every(x => x.vis), `${tag} every link shows once its group is open`, s.L.filter(x => !x.vis).map(x => x.l).join(","));
    ok(s.L.filter(x => !x.cta).every(x => x.ht >= 44), `${tag} link targets ≥44px`, s.L.filter(x => x.ht < 44).map(x => x.l + ":" + x.ht).join(","));
    const lastIn = await p.evaluate(s => { const m = document.querySelector(s), sc = m.querySelector("nav.c101c-sheet") || m; sc.scrollTop = 1e6; const as = m.querySelectorAll("a"), a = as[as.length - 1], r = a.getBoundingClientRect(), x = sc.querySelector(".c101c-x").getBoundingClientRect(); return r.bottom <= innerHeight + 1 && r.top >= 0 && x.top >= 0 && x.top < 20; }, sel);
    ok(lastIn, `${tag} last link reachable by scrolling the sheet; X stays visible`);
    ok(s.sw <= s.cw, `${tag} no horizontal overflow with all groups open`, s.sw + "/" + s.cw);
    ok(s.lock, `${tag} still locked with all groups open`);
    const labels = s.L.map(x => x.l), miss = REQ.filter(l => !labels.includes(l));
    ok(!miss.length, `${tag} all ${REQ.length} core sections listed`, miss.join(", "));
    const adm = s.L.some(x => x.h === "/__admin"); ok(adminView ? adm : !adm, `${tag} Admin Console ${adminView ? "shown" : "hidden"}`);
    // X closes, unlocks, focus back on the button
    await p.evaluate(s => document.querySelector(s).querySelector(".c101c-x").click(), sel); await sleep(250);
    const xs = await p.evaluate(e => [document.activeElement === e || (!e.isConnected && document.activeElement.matches("[aria-controls='c93Menu'],details>summary")), document.documentElement.classList.contains("c101c-lock"), getComputedStyle(document.body).overflow], trig);
    ok(!(await isOpen(p, sel)) && xs[0] && !xs[1] && xs[2] === ov0, `${tag} X closes, unlocks scroll, returns focus`, JSON.stringify(xs));
    // Escape closes, unlocks, focus back on the button
    if (!(await p.evaluate(e => e.isConnected && e.offsetParent !== null, trig))) trig = await trigger(p);   // the app may re-render its header
    await trig.click(); await sleep(250);
    await p.evaluate(s => { const m = document.querySelector(s); const a = m.querySelector("a"); a && a.focus(); }, sel);
    await p.keyboard.press("Escape"); await sleep(250);
    const back = await p.evaluate(e => [document.activeElement === e || (!e.isConnected && document.activeElement.matches("[aria-controls='c93Menu'],details>summary")), document.documentElement.classList.contains("c101c-lock")], trig);
    ok(!(await isOpen(p, sel)) && back[0] && !back[1], `${tag} Escape closes, unlocks, returns focus`, JSON.stringify(back));
    if (w === 390 && pth === "/" && !extra && !u) { await p.screenshot({ path: `${OUT}/${nm}_menu_closed.png` }); res.push(`SHOT ${OUT}/${nm}_menu_closed.png`); }
    const yb = await p.evaluate(() => { scrollTo(0, 0); return scrollY; }); await p.mouse.wheel({ deltaY: 400 }); await sleep(250);
    if (ov0 !== "hidden") ok(await p.evaluate(() => scrollY > 0 || document.documentElement.scrollHeight <= innerHeight), `${tag} page scrolls again after close`);
    // every link answers 200 for this user
    for (const x of s.L) {
      const key = who + " " + x.h; if (checked.has(key) || !x.h || x.h.startsWith("/__auth")) continue;
      const r = await p.evaluate(async h => { try { const q = await fetch(h, { credentials: "include" }); const t = await q.text(); return [q.status, t.length, q.url.replace(location.origin, ""), /<title>[^<]*(Not found|404)/i.test(t)]; } catch (e) { return [0, 0, String(e), true]; } }, x.h);
      checked.set(key, r); ok(r[0] === 200 && r[1] > 800 && !r[3], `${who} link ${x.l} ${x.h} -> ${r[2]} 200`, r.join(" "));
    }
    // app at 390, signed in: open each link's group, click it, and check the right view opens
    if (isApp && u && w === 390 && !dark && !extra && pth === "/dashboard/") {
      for (const x of s.L.filter(x => x.id && !x.cta)) {
        await p.evaluate(() => { const b = [...document.querySelectorAll("[aria-controls='c93Menu']")].find(e => e.offsetParent); const m = document.getElementById("c93Menu"); if (!m || m.hidden) b.click(); }); await sleep(150);
        const e0 = errs.length;
        const vis = await p.evaluate(id => { const a = document.querySelector(`#c93Menu a[data-c93-nav="${id}"]`); const ul = a.closest("ul"); const bt = ul && document.querySelector(`[aria-controls="${ul.id}"]`); if (bt && bt.getAttribute("aria-expanded") !== "true") bt.click(); a.scrollIntoView({ block: "nearest" }); const r = a.getBoundingClientRect(); const v = r.height > 0 && r.top >= 0 && r.bottom <= innerHeight; a.click(); return v; }, x.id);
        await sleep(900);
        const st = await p.evaluate(() => ({ len: document.body.innerText.length, nf: /Page not found/.test(document.body.innerText), cur: typeof pg !== "undefined" ? pg : "?" }));
        ok(vis && errs.length === e0 && st.len > 300 && !st.nf && (st.cur === x.id || x.id === "settings" || x.id === "home"), `${who} app 390: ${x.l} (${x.id}) group opens, view opens [pg=${st.cur}]`, JSON.stringify(st) + " vis=" + vis + " " + errs.slice(e0).join(";"));
      }
    }
    ok(!errs.length, `${tag} no script errors`, errs.join(" | "));
    } catch (e) { ok(false, `${who} ${w} ${dark ? "dark" : "light"} ${pth} audit step crashed`, e.message + " nav " + JSON.stringify(p.__nav) + " errs " + JSON.stringify(errs)); }
    await ctx.close();
  }
  // screenshots: page with the menu closed, sheet with one group open, 1280 All sections
  for (const [u, w, dark, pth, nm, act] of [
    [null, 390, false, "/", "phone_390_light_menu_closed_page", "none"], [null, 390, true, "/", "phone_390_dark_menu_closed_page", "none"],
    [null, 390, false, "/", "phone_390_light_menu_open_all_collapsed", "open"], [null, 390, true, "/", "phone_390_dark_menu_open_all_collapsed_no_bleed", "open"],
    [null, 390, false, "/gold/", "phone_390_light_one_group_open_gold_start", "open"], [null, 390, true, "/gold/", "phone_390_dark_one_group_open_gold_start", "open"],
    ["hmember", 390, true, "/dashboard/", "phone_390_dark_app_member_desk_open", "open"],
    [null, 320, false, "/", "phone_320_light_menu_open_all_collapsed", "open"], [null, 320, false, "/", "phone_320_light_menu_closed_page", "none"],
    [null, 1280, false, "/tools/verify/", "desktop_1280_light_all_sections", "open"], ["hadmin", 1280, true, "/tools/verify/", "desktop_1280_dark_admin_all_sections", "open"]]) {
    const { ctx, p } = await page(u, w, dark, pth); if (act === "open") { const trig = await trigger(p); await trig.click(); await sleep(350); }
    await p.screenshot({ path: `${OUT}/${nm}.png` }); res.push(`SHOT ${OUT}/${nm}.png`); await ctx.close();
  }
  // market cards: every field still there and visible; compare with the chat101b base counts
  const cards = require("./cards.js"); const base = JSON.parse(fs.readFileSync(__dirname + "/cards_base.json", "utf8"));
  if (process.env.ONLY) { console.log(`${pass} passed, ${fail} failed`); await b.close(); return; }
  const K = ["rows", "values", "changes", "sources", "dates"]; // Delayed labels follow live feed state (they flip between runs), so they are checked against the same page load
  for (const pth of ["/", "/gold/"]) for (const w of [320, 390, 1280]) for (const dark of [false, true]) {
    const nm = `cards_${pth === "/" ? "home" : "gold"}_${w}_${dark ? "dark" : "light"}`;
    const shot = (w < 1280 && (w === 390 || !dark)) ? `${OUT}/${nm}.png` : null;
    const c = await cards(b, w, dark, pth, shot); if (shot) res.push(`SHOT ${shot}`);
    const bs = base[pth + " " + w], tag = `cards ${pth} ${w} ${dark ? "dark" : "light"}`;
    ok(K.every(k => c[k] === bs[k]), `${tag} same data points/changes/sources/dates/Delayed as chat101b`, K.map(k => `${k} ${bs[k]}->${c[k]}`).join(" "));
    ok(c.delayed >= 1 && c.vDelayed === c.delayed, `${tag} every Delayed label in the feed data is shown`, c.vDelayed + " of " + c.delayed);
    ok(c.vValues === c.values && c.vChanges === c.changes && c.vSources === c.sources && c.vDates === c.dates && c.vDelayed === c.delayed, `${tag} every field visible`, JSON.stringify(c));
    ok(!c.overflow.length && c.sw <= c.cw, `${tag} no overflow; card shape name|value, change under value, source below`, c.overflow.join(";") + " sw " + c.sw + "/" + c.cw);
    ok(!c.codes.length, `${tag} no raw ticker codes`, c.codes.join(";"));
    ok(c.signs.every(([d, sg, col]) => (d === "up" ? sg === "+" : sg === "−" || sg === "-")) && new Set(c.signs.map(x => x[0] + x[2])).size <= 2, `${tag} change keeps sign and red/green`, JSON.stringify(c.signs));
    if (w < 600) ok(c.heads.length >= 3 && c.heads.every(h => /^(Gold|Gold and silver|Rates|Energy|Crypto|Currencies|Stocks|Other)$/.test(h)), `${tag} group headings`, c.heads.join("|"));
    else ok(c.heads.length === 0, `${tag} desktop table unchanged (no headings shown)`, c.heads.join("|"));
  }
  await b.close();
  fs.writeFileSync(`${OUT}/audit.txt`, res.join("\n") + `\n${pass} passed, ${fail} failed\n`);
  console.log(`${pass} passed, ${fail} failed`);
})().catch(e => { console.log("CRASH", e.stack); process.exit(1); });
