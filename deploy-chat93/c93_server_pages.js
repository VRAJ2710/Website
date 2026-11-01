// ── chat93: server-rendered reader pages on one paper template (Home for guests, the Capital Sustainability Monitor, trust pages) ──
const C93_MISSION = "Verified gold and macro research for independent investors, with sources on every figure.";
const C93_EDITOR = "Edited by Vraj Patel, London";
const C93_CONTACT = "dispatchmarket@mail.grokbot.com";
const C93_PHOTO = ""; // optional editor photo URL; when empty the photo slot is not rendered at all
const C93_DISC = "Not investment advice. Capital at risk.";
const C93_CSS = ":root{--paper:#fbfaf7;--ink:#1b1b1b;--muted:#5f6368;--rule:#dedad2;--accent:#1f3a5f;--down:#a23b2a;--up:#2f6b47;--amber:#8a6a12;--serif:'Source Serif 4',Georgia,serif;--sans:Inter,system-ui,-apple-system,'Segoe UI',Arial,sans-serif}" +
  "*{box-sizing:border-box}html{background:var(--paper)}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 var(--sans);font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}" +
  ".wrap{max-width:1120px;margin:0 auto;padding:0 32px}header.site{border-bottom:1px solid var(--rule);background:#fff;position:relative}header.site .wrap{display:flex;align-items:center;justify-content:space-between;height:64px;gap:16px}" +
  ".mark{font:600 22px/1 var(--serif);letter-spacing:-.01em;color:var(--ink);white-space:nowrap}.mark:hover{text-decoration:none}.nav a{color:var(--ink);margin-left:24px;font-size:14px}.nav a[aria-current]{text-decoration:underline;text-underline-offset:4px}.nav a.cta{border:1px solid var(--ink);padding:6px 12px;border-radius:2px}" +
  ".menu{display:none;font-size:14px}.menu summary{list-style:none;cursor:pointer;padding:8px 0 8px 12px;color:var(--ink)}.menu summary::-webkit-details-marker{display:none}.menu nav{position:absolute;left:0;right:0;top:56px;background:#fff;border-bottom:1px solid var(--rule);padding:6px 18px 12px;z-index:5}.menu nav a{display:block;padding:10px 0;color:var(--ink);font-size:15px;border-bottom:1px solid var(--rule)}.menu nav a:last-child{border-bottom:0}" +
  ".strip{font-size:12.5px;color:var(--muted);border-bottom:1px solid var(--rule)}.strip .wrap{display:flex;justify-content:space-between;gap:16px;min-height:34px;align-items:center}.disc{font-weight:600;color:var(--ink)}" +
  ".kicker{font:600 12px/1.3 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}h1{font:600 46px/1.12 var(--serif);letter-spacing:-.015em;margin:12px 0 14px;max-width:780px}h2{font:600 24px/1.2 var(--serif);margin:0 0 6px}h3{font:600 18px/1.3 var(--serif);margin:0 0 6px}" +
  ".dek{font:400 19px/1.5 var(--serif);color:#333;max-width:700px;margin:0}.byline{font-size:13px;color:var(--muted);margin:14px 0 0}.grid{display:grid;grid-template-columns:2fr 1fr;gap:48px}main>section{padding:36px 0;border-bottom:1px solid var(--rule)}main>section:last-of-type{border-bottom:0}" +
  "table{width:100%;border-collapse:collapse;font-size:14px}th{font:600 11.5px/1.3 var(--sans);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);text-align:left;border-bottom:1px solid var(--ink);padding:8px 8px 8px 0}td{border-bottom:1px solid var(--rule);padding:10px 8px 10px 0;vertical-align:top}td.n,th.n{text-align:right}td.n{white-space:nowrap}" +
  ".src{font-size:12px;color:var(--muted)}.down{color:var(--down)}.up{color:var(--up)}.note{font-size:13px;color:var(--muted);margin:10px 0 0}.card{border-top:3px solid var(--ink);padding-top:12px}.f-red{color:var(--down);font-weight:600}.f-amber{color:var(--amber);font-weight:600}.f-green{color:var(--up);font-weight:600}.f-na{color:var(--muted)}" +
  ".facts{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin:22px 0 6px}.facts div{border-top:1px solid var(--ink);padding-top:8px}.facts b{display:block;font:600 26px/1.2 var(--serif)}.facts span{font-size:13px;color:var(--muted)}.big{font:600 26px/1.2 var(--serif);margin:6px 0 4px}" +
  ".prose{max-width:720px}.prose p,.prose li{font-size:16px;line-height:1.65;color:#2b2a26}.prose h2{margin:30px 0 8px}.prose table{margin:8px 0 4px}.lede{font:400 19px/1.5 var(--serif);color:#333;margin:0}.pager{display:flex;justify-content:space-between;gap:16px;font-size:14px;padding:18px 0}" +
  ".c93g{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin:18px 0}.c93c{border-top:3px solid var(--ink);padding-top:12px}.c93cp{border-top-color:var(--accent)}.c93pr{font:600 28px/1.2 var(--serif);margin:0 0 8px}.c93c ul{padding-left:20px;margin:0}.c93c li{margin:4px 0;font-size:15px}.muted{font-size:14px;color:var(--muted)}" +
  "footer.site{padding:36px 0 48px;font-size:13px;color:var(--muted);border-top:1px solid var(--rule)}footer.site .links a{color:var(--ink);margin-right:20px}footer.site p{margin:10px 0 0}" +
  ".msrc{display:none}@media (max-width:760px){table.ctx .msrc{display:block;margin-top:2px}table.ctx td.src,table.ctx th.src{display:none}.wrap{padding:0 18px}header.site .wrap{height:56px}.nav{display:none}.menu{display:block}.mark{font-size:19px}h1{font-size:31px}.dek,.lede{font-size:17px}.grid{grid-template-columns:1fr;gap:28px}.strip .wrap{padding-top:8px;padding-bottom:8px;flex-direction:column;align-items:flex-start;gap:2px}.facts{grid-template-columns:1fr 1fr;gap:16px}.facts b{font-size:22px}footer.site .links a{display:inline-block;margin:0 16px 8px 0}.hide-m{display:none}td,th{padding-right:6px}}";
function c93Esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
const C93_NAV = [["/brief/", "Brief"], ["/gold/", "Gold"], ["/markets/", "Markets"], ["/research/", "Research"], ["/methodology", "Methodology"], ["/about", "About"]];
function c93UkParts(ms, tz) {
  const o = {}; try { for (const p of new Intl.DateTimeFormat("en-GB", { timeZone: tz || "Europe/London", weekday: "long", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(ms))) o[p.type] = p.value; } catch (e) {}
  return o;
}
function c93UkDay(ms) { const o = c93UkParts(ms); return (o.weekday || "") + " " + (o.day || "") + " " + (o.month || "") + " " + (o.year || ""); }
function c93Date(iso) {                                                    // "2026-06-30" -> "30 June 2026"
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || "")); if (!m) return "";
  return Number(m[3]) + " " + ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][Number(m[2]) - 1] + " " + m[1];
}
function c93Sessions(ms) {                                                 // per asset class, from New York trading hours
  const ny = c93UkParts(ms, "America/New_York"), d = ny.weekday || "", t = Number(ny.hour || 0) * 60 + Number(ny.minute || 0);
  const wk = /Monday|Tuesday|Wednesday|Thursday|Friday/.test(d);
  const us = wk && t >= 570 && t < 960;
  const fx = (d === "Sunday" && t >= 1080) || (/Monday|Tuesday|Wednesday|Thursday/.test(d) && (t < 1020 || t >= 1080)) || (d === "Friday" && t < 1020);
  if (d === "Saturday" || (d === "Sunday" && t < 1080) || (d === "Friday" && t >= 1020)) return { text: "US stocks, gold and currencies closed for the weekend \u00b7 Crypto trades every day", weekend: true };
  return { text: "US stocks " + (us ? "open" : "closed") + " · Gold and currencies " + (fx ? "trading" : "closed") + " · Crypto trades every day", weekend: false };
}
function c93Head(title, path, desc, extra) {
  return `<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${c93Esc(title)}</title><meta name="description" content="${c93Esc(desc)}"><link rel="canonical" href="https://thedispatch.uk${path}"><meta name="theme-color" content="#fbfaf7"><link rel="icon" type="image/svg+xml" href="/logo-mark.svg"><link rel="manifest" href="/manifest.json"><meta property="og:site_name" content="The Dispatch Market"><meta property="og:title" content="${c93Esc(title)}"><meta property="og:description" content="${c93Esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://thedispatch.uk${path}"><meta property="og:image" content="https://thedispatch.uk/og-card.png"><meta name="twitter:card" content="summary_large_image"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;600&display=swap" rel="stylesheet"><style>${C93_CSS}</style>${extra || ""}</head>`;
}
function c93Header(path, user) {
  const cur = h => (h === path || (h.length > 1 && h.endsWith("/") && path.indexOf(h) === 0)) ? ' aria-current="page"' : "";
  const links = C93_NAV.map(([h, t]) => `<a href="${h}"${cur(h)}>${t}</a>`).join("");
  const acct = user ? '<a class="cta" href="/dashboard/">Your desk</a>' : '<a class="cta" href="/__auth/login">Sign in</a>';
  return `<header class="site"><div class="wrap"><a class="mark" href="/">The Dispatch Market</a><nav class="nav" aria-label="Main">${links}${acct}</nav><details class="menu"><summary aria-label="Open the menu">Menu</summary><nav aria-label="Main">${links}${acct}</nav></details></div></header>`;
}
function c93Footer() {
  return `<footer class="site"><div class="wrap"><div class="links"><a href="/about">About</a><a href="/editorial-standards">Editorial standards</a><a href="/methodology">Methodology</a><a href="/corrections">Corrections</a><a href="mailto:${C93_CONTACT}">Contact: ${C93_CONTACT}</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></div>` +
    `<p><span class="disc">${C93_DISC}</span> The Dispatch Market publishes research and education, not personal recommendations. Prices come from free public feeds and some are delayed; each figure shows its source and time.</p>` +
    `<p>\u00a9 ${new Date().getUTCFullYear()} The Dispatch Market \u00b7 thedispatch.uk \u00b7 ${C93_EDITOR}</p></div></footer>`;
}
function c93Shell(o) {                                                     // o: title, path, desc, body, strip (left side), user, extraHead, tail
  const left = o.strip != null ? o.strip : `${c93Esc(c93UkDay(Date.now()))} \u00b7 ${c93Esc(c93Sessions(Date.now()).text)}`;
  return c93Head(o.title, o.path, o.desc, o.extraHead) + `<body>${c93Header(o.path, o.user)}<div class="strip"><div class="wrap"><span>${left}</span><span class="disc">${C93_DISC}</span></div></div><main class="wrap">${o.body}</main>${c93Footer()}${o.tail || ""}</body></html>`;
}
function c93Page(title, path, desc, body) {                                // trust, pricing and legal pages
  return c93Shell({ title: title + " | The Dispatch Market", path, desc, body: `<section class="prose">${body}</section>` });
}
function c93Html(req, res, html, cache) {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": cache || "public, max-age=600", "X-Content-Type-Options": "nosniff" });
  return res.end(req.method === "HEAD" ? undefined : html);
}
const C93_PAGES = {
  "/about": ["About The Dispatch Market", "Who edits The Dispatch Market, what it publishes and how it works. " + C93_MISSION, () =>
    (C93_PHOTO ? `<figure style="margin:0 0 16px"><img src="${c93Esc(C93_PHOTO)}" alt="Vraj Patel" width="120" height="120" style="object-fit:cover;border-radius:4px"></figure>` : "") +
    `<div class="kicker">About</div><h1>About The Dispatch Market</h1><p class="lede">${C93_MISSION}</p><p class="byline">${C93_EDITOR}</p>` +
    `<h2>What we publish</h2><ul><li><a href="/brief/">The Brief</a>: a short daily read of what moved in gold, rates, the dollar, oil and shares, and why it may matter.</li><li><a href="/playbook/">The Playbook</a>: a weekly set of gold and macro scenarios, with what would change the view.</li><li><a href="/gold/">Gold</a> and <a href="/markets/">Markets</a>: prices across asset classes, each with its source and time.</li><li><a href="/research/capital-sustainability">The Capital Sustainability Monitor</a>: what company filings at the SEC show about how big spenders fund their capital spending.</li></ul>` +
    `<h2>How we work</h2><p>Every figure on the site carries its source and the time it was checked, in UK time. Most prices come from free public feeds, so some are delayed. Company figures come from official SEC filings. When a feed fails we show the last official figure with its date, or leave the figure out. We do not fill gaps with guesses.</p><p>The full list of sources is on the <a href="/methodology">methodology page</a>. How we write and check is on the <a href="/editorial-standards">editorial standards page</a>, and anything we get wrong is logged on the <a href="/corrections">corrections page</a>.</p>` +
    `<h2>What we are not</h2><p>The Dispatch Market is a research publication. It is not a broker and it does not give personal financial advice. Nothing here is a recommendation to buy or sell anything. Not investment advice. Capital at risk: the value of investments can fall as well as rise.</p>` +
    `<h2>Get in touch</h2><p>Email <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a>. More on the <a href="/contact">contact page</a>.</p>`],
  "/contact": ["Contact", "How to contact The Dispatch Market, report an error or ask about your account.", () =>
    `<div class="kicker">Contact</div><h1>Contact</h1><p class="lede">The quickest way to reach us is by email.</p><p><a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a></p>` +
    `<h2>Reporting an error</h2><p>Tell us the page, the figure and what you think is wrong. We check every report and log confirmed fixes on the <a href="/corrections">corrections page</a>.</p>` +
    `<h2>Accounts and billing</h2><p>Premium is billed monthly through Stripe. You can manage or cancel it from Settings when signed in, or email us and we will help.</p>` +
    `<h2>What we cannot do</h2><p>We cannot give personal financial advice or tell you whether to buy or sell anything. Not investment advice. Capital at risk.</p>`],
  "/methodology": ["Methodology", "Where every figure on The Dispatch Market comes from, how often it updates and what we do when a feed fails.", () =>
    `<div class="kicker">How we work</div><h1>Methodology</h1><p class="lede">Where our figures come from, how fresh they are, and what we show when a source fails.</p>` +
    `<h2>Sources</h2><table><thead><tr><th>What</th><th>Source</th><th>Freshness</th></tr></thead><tbody>` +
    `<tr><td>Gold spot price</td><td>gold-api.com (free feed)</td><td>Checked about every 30 seconds while the page is open</td></tr>` +
    `<tr><td>Shares, indices, oil and currency prices</td><td>Yahoo Finance (free, unofficial), with Finnhub and Twelve Data as backups</td><td>Often delayed by around 15 minutes; outside trading hours we show the last close and its date</td></tr>` +
    `<tr><td>US Treasury yields and the real yield</td><td>US Treasury daily rates, via FRED</td><td>Once a day, the official print with its date</td></tr>` +
    `<tr><td>Oil and gas spot prices</td><td>US Energy Information Administration (EIA), via FRED</td><td>The official daily series, usually a day or more behind</td></tr>` +
    `<tr><td>Crypto prices</td><td>Coinbase and CoinGecko public feeds</td><td>Near real time; crypto trades every day</td></tr>` +
    `<tr><td>Company figures (Capital Sustainability Monitor)</td><td>SEC EDGAR company filings (XBRL company facts)</td><td>Checked once a UK day; each page shows the filing, its period and the date it was filed</td></tr>` +
    `<tr><td>News</td><td>Publishers' public RSS feeds, linked to the original</td><td>Every few minutes</td></tr></tbody></table>` +
    `<h2>Times and trading sessions</h2><p>All times are UK time (GMT, or BST in summer). We label sessions by asset class rather than saying "markets closed": US shares trade 9:30am to 4pm New York time on weekdays, gold and major currencies trade almost around the clock from Sunday evening to Friday evening, and crypto trades every day.</p>` +
    `<h2>When a feed fails</h2><p>We show the last official figure with its date. If we have no figure we can stand behind, we leave the line out and say that some prices are delayed. We never show a dash or a placeholder in place of a number.</p>` +
    `<h2>Scores, flags and scenarios</h2><p>Some pages use simple rules-based models, such as the risk-appetite gauge and the five filing checks in the Capital Sustainability Monitor. The thresholds behind them are editorial judgements, not facts, and they are published with each model. They describe conditions; they are not recommendations. The <a href="/research/capital-sustainability/method">monitor's method</a> is published in full.</p>` +
    `<h2>Use of AI</h2><p>The Ask assistant and some drafts of the daily Brief use an AI model working from the figures above. These are labelled. Rules-based briefs are labelled as built from today's data.</p>`],
  "/editorial-standards": ["Editorial standards", "How The Dispatch Market writes, sources and checks its research.", () =>
    `<div class="kicker">How we work</div><h1>Editorial standards</h1><p class="lede">${C93_MISSION}</p><p class="byline">${C93_EDITOR}</p>` +
    `<h2>Sources on every figure</h2><p>Every number we publish carries its source and the time it was checked, in UK time. If we cannot source a figure, we do not publish it.</p>` +
    `<h2>Facts and views kept apart</h2><p>We separate what the data shows from what we think it may mean, and we say what would change our view.</p>` +
    `<h2>No buy or sell calls</h2><p>We do not tell readers to buy, sell or hold anything, and we do not publish price targets. Nothing here is personal financial advice. Not investment advice. Capital at risk.</p>` +
    `<h2>Plain English</h2><p>We write numbers the way people say them ($115.9bn rather than 115,948,000,000) and explain terms the first time we use them.</p>` +
    `<h2>Independence</h2><p>We are funded by reader subscriptions. We do not take payment to cover companies or assets.</p>` +
    `<h2>Corrections</h2><p>When we get something wrong we fix it, say what changed and log it on the <a href="/corrections">corrections page</a>. Report an error to <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a>.</p>`],
  "/corrections": ["Corrections", "Errors we have found and fixed on The Dispatch Market.", () =>
    `<div class="kicker">How we work</div><h1>Corrections</h1><p class="lede">When we get something wrong, we fix it and record it here.</p>` +
    `<h2>Log</h2><table><thead><tr><th>Date</th><th>Page</th><th>What was wrong and what we changed</th></tr></thead><tbody>` +
    `<tr><td>October 2026</td><td>Capital Sustainability Monitor, company pages</td><td>Company pages showed the total number of companies ("Rank 19") instead of each company's own rank. Fixed; each page now shows "Ranked N of 19".</td></tr></tbody></table>` +
    `<h2>Report an error</h2><p>Email <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a> with the page and the figure.</p>`],
};
const c93PageCache = new Map();
function c93Send(req, res, key) {
  let html = c93PageCache.get(key);
  if (!html) { const d = C93_PAGES[key]; html = c93Page(d[0], key, d[1], d[2]()); c93PageCache.set(key, html); }
  return c93Html(req, res, html);
}
let c93ManifestBody = null;
function c93Manifest(req, res) {
  if (!c93ManifestBody) {
    let m = {};
    try { m = JSON.parse(require("fs").readFileSync(require("path").join(__dirname, "manifest.json"), "utf8")) || {}; } catch (e) { m = {}; }
    m.name = "The Dispatch Market"; m.short_name = "Dispatch Market"; m.description = C93_MISSION;
    m.background_color = "#fbfaf7"; m.theme_color = "#fbfaf7";
    if (!m.start_url) m.start_url = "/";
    if (!m.display) m.display = "standalone";
    c93ManifestBody = JSON.stringify(m);
  }
  res.writeHead(200, { "Content-Type": "application/manifest+json; charset=utf-8", "Cache-Control": "public, max-age=3600" });
  return res.end(req.method === "HEAD" ? undefined : c93ManifestBody);
}
// ── Capital Sustainability Monitor, server-rendered from the bb11 payload ──
const C93_CSM = "/research/capital-sustainability";
const C93_CHECKS = [["sustainability_gap", "Sustainability gap"], ["fcf_coverage", "Free-cash-flow coverage"], ["debt_reliance", "Debt reliance"], ["interest_burden", "Interest burden"], ["margin_trend", "Margin trend"]];
const C93_GROUPS = { "hyperscaler": "Hyperscaler", "ai-infrastructure borrower": "AI infrastructure borrower" };
function c93Grp(g) { const s = String(g || ""); return C93_GROUPS[s] || (s ? s.charAt(0).toUpperCase() + s.slice(1) : ""); }
function c93Num(n, dp) { const x = Number(n); return isFinite(x) ? x.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }) : ""; }
function c93Sg(n, dp, unit) { const x = Number(n); if (n == null || !isFinite(x)) return ""; return (x > 0 ? "+" : x < 0 ? "\u2212" : "") + Math.abs(x).toFixed(dp) + (unit || ""); }
function c93Bn(v) { const n = Number(v); if (v == null || !isFinite(n)) return ""; const a = Math.abs(n), s = n < 0 ? "\u2212" : ""; return a >= 1e12 ? s + "$" + (a / 1e12).toFixed(2) + "tn" : a >= 1e9 ? s + "$" + (a / 1e9).toFixed(1) + "bn" : a >= 1e6 ? s + "$" + (a / 1e6).toFixed(1) + "m" : s + "$" + c93Num(a, 0); }
function c93Pct(g) { return g == null ? "" : c93Sg(Number(g) * 100, 0, "%"); }
function c93Flag(v) { const s = String(v || "").toLowerCase(); const w = s === "red" ? "Red" : s === "amber" ? "Amber" : s === "green" ? "Green" : "Not in filing"; return `<span class="f-${s === "red" || s === "amber" || s === "green" ? s : "na"}">${w}</span>`; }
function c93Reason(r) {
  return String(r || "").replace(/^./, c => c.toUpperCase()).replace(/(^|\s)-(\d)/g, "$1\u2212$2").replace(/\bOCF\b/g, "operating cash flow")
    .replace(/^turned worse since last quarter: (.*)$/, (m, k) => k.split(/,\s*/).map(x => (C93_CHECKS.find(c => c[0] === x) || [0, x.replace(/_/g, " ")])[1]).join(", ") + " check turned worse since last quarter");
}
async function c93Monitor(kind, tkr, limit) {
  if (typeof bb11Body !== "function") return null;
  const st = bb11St || await bb11Ensure();
  try { const rp = bb11Refresh(st); if (rp) rp.catch(function () { }); } catch (e) { }
  const hit = bb11Body(st, kind, bb11Now(), limit || BB11_LIMIT_MAX, tkr || null);
  return hit && hit.body ? JSON.parse(hit.body) : null;
}
function c93CsmSource(d) {
  const f = d && d.as_of && d.as_of.filings || {}, m = d && d.as_of && d.as_of.market || {};
  const bits = ["Source: SEC EDGAR XBRL company facts" + (f.latest_period_end_max ? ", periods to " + c93Date(f.latest_period_end_max) : "")];
  if (m.last_bar_date_max) bits.push("prices Yahoo Finance daily bars, delayed, last close " + c93Date(m.last_bar_date_max));
  return bits.join("; ") + ".";
}
const C93_NAMES = { GOOGL: "Alphabet", VRT: "Vertiv", AMZN: "Amazon", CRWV: "CoreWeave", ORCL: "Oracle", AVGO: "Broadcom", DLR: "Digital Realty", EQIX: "Equinix", META: "Meta", AMD: "AMD", CEG: "Constellation Energy", MSFT: "Microsoft", CRM: "Salesforce", VST: "Vistra", T: "AT&T", NVDA: "Nvidia", MU: "Micron", NEE: "NextEra Energy", XOM: "ExxonMobil" };
function c93Nm(r, tkr) { const t = (r && r.ticker) || tkr || ""; return C93_NAMES[t] || (r && r.company) || t; }
function c93MonitorRows(rows, full) {
  return rows.map(r => `<tr>${full ? `<td class="n" style="text-align:left">${r.rank}</td>` : ""}<td><a href="${C93_CSM}/${encodeURIComponent(r.ticker)}">${c93Esc(c93Nm(r))}</a>${full ? ` <span class="src">${c93Esc(r.ticker)}</span>` : ""}</td><td>${c93Esc((r.reasons || []).map(c93Reason).filter(Boolean).join("; "))}</td>${full ? `<td class="hide-m">${c93Esc(r.attention ? r.attention.charAt(0).toUpperCase() + r.attention.slice(1) : "")}</td>` : ""}<td class="n">${c93Flag(r.filing_flag && r.filing_flag.overall)}</td></tr>`).join("");
}
async function c93CsmIndex(req, res, user) {
  const d = await c93Monitor("radar", null, BB11_LIMIT_MAX); if (!d || !Array.isArray(d.ranking) || !d.ranking.length) return false;
  const body = `<section><div class="kicker">Research</div><h1>Capital Sustainability Monitor</h1><p class="dek">Is AI spending outrunning the cash that pays for it? We rank ${d.total || d.ranking.length} US-listed companies on capital spending against operating cash flow, debt and margins, using their SEC filings.</p><p class="byline">${C93_EDITOR} \u00b7 <a href="${C93_CSM}/method">How the ranking works</a></p></section>` +
    `<section><h2>The ranking</h2><p class="note" style="margin:0 0 12px">Ranked by attention and the gap between spending and cash. A ranking of conditions, not a recommendation.</p><table><thead><tr><th>Rank</th><th>Company</th><th>What stands out</th><th class="hide-m">Market attention</th><th class="n">Filing flag</th></tr></thead><tbody>${c93MonitorRows(d.ranking, true)}</tbody></table><p class="src" style="margin-top:12px">${c93Esc(c93CsmSource(d))} <a href="${C93_CSM}/method">Method</a></p></section>`;
  return c93Html(req, res, c93Shell({ title: "Capital Sustainability Monitor | The Dispatch Market", path: C93_CSM, desc: "How 19 big US spenders fund their capital spending, from their SEC filings: five checks, ranked. Not investment advice.", user, strip: `<a href="/research/">Research</a> \u203a Capital Sustainability Monitor`, body }), "public, max-age=300");
}
async function c93CsmMethod(req, res, user) {
  const d = await c93Monitor("radar", null, 1); if (!d) return false;
  const t = d.thresholds || {}, g = t.gap_pp || {}, f = t.fcf_cov || {}, dc = t.debt_capex || {}, ic = t.int_opinc || {}, mp = t.margin_pp || {};
  const pc = v => v == null ? "" : Math.round(Number(v) * 100) + "%";
  const rows = [["Sustainability gap", "Capital spending growth over 12 months minus the average growth of operating cash flow, revenue and operating income", `Amber above ${g.amber} pt, red above ${g.red} pt`],
    ["Free-cash-flow coverage", "Free cash flow as a share of capital spending", `Green at ${pc(f.green)} or more, amber from ${pc(f.amber)}, red below`],
    ["Debt reliance", "New long-term borrowing as a share of capital spending, last 12 months", `Amber from ${pc(dc.amber)}, red from ${pc(dc.red)}`],
    ["Interest burden", "Interest expense as a share of operating income", `Amber from ${pc(ic.amber)}, red from ${pc(ic.red)}`],
    ["Margin trend", "Change in operating margin against the prior 12 months", `Amber below ${mp.amber} pt, red below ${mp.red} pt`]];
  const body = `<section class="prose"><div class="kicker">Capital Sustainability Monitor</div><h1>How the ranking works</h1><p class="lede">Five checks on each company's latest SEC filings, plus how much attention its shares are getting. The thresholds are editorial judgements, published here in full.</p><p class="byline">${C93_EDITOR}</p>` +
    `<h2>The five checks</h2><table><thead><tr><th>Check</th><th>What it measures</th><th>Thresholds</th></tr></thead><tbody>${rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${c93Esc(r[2])}</td></tr>`).join("")}</tbody></table>` +
    `<h2>The filing flag</h2><p>Each check reads green, amber or red. A company's overall filing flag summarises the five; a check reads "not in filing" when the filing does not give the figure, and it then adds nothing to the score.</p>` +
    `<h2>The ranking</h2><p>Half of the score comes from the filings: the flags, the size of the sustainability gap, whether capital spending is speeding up, and whether any check turned worse since the last quarter. The other half comes from the shares: trading volume against its 20-day average and the size of the five-day price move. Companies without recent price data are ranked on their filings alone, after the others.</p><p>Market attention reads high when the market half of the score is 40 or more out of 100, and low below 15.</p>` +
    `<h2>Sources</h2><p>SEC EDGAR XBRL company facts (data.sec.gov), checked once a UK day; prices from Yahoo Finance daily bars, which are delayed and are not live quotes. Each company page names the filing, its period and the date it was filed.</p><p>This is a ranking of conditions in public filings. It is not a recommendation to buy or sell any share. Not investment advice. Capital at risk.</p><p><a href="${C93_CSM}">Back to the ranking</a></p></section>`;
  return c93Html(req, res, c93Shell({ title: "How the Capital Sustainability Monitor works | The Dispatch Market", path: C93_CSM + "/method", desc: "The five filing checks, their thresholds and how the Capital Sustainability Monitor ranks companies.", user, strip: `<a href="/research/">Research</a> \u203a <a href="${C93_CSM}">Capital Sustainability Monitor</a> \u203a Method`, body }));
}
function c93Dek(i) {
  const m = i.metrics || {}, f = i.filing || {}, out = [];
  const pe = /^(\d{4})-(\d{2})/.exec(String(f.latest_period_end || "")), to = pe ? " in the 12 months to " + ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][Number(pe[2]) - 1] + " " + pe[1] : " over the last 12 months";
  const cg = Number(m.capex_growth_ttm), og = Number(m.ocf_growth_ttm);
  if (isFinite(cg) && isFinite(og) && m.capex_growth_ttm != null && m.ocf_growth_ttm != null) {
    const verb = cg >= 0 ? "grew " + Math.round(cg * 100) + "%" : "fell " + Math.round(-cg * 100) + "%";
    const cmp = og > 0 && cg > 2 * og ? "more than twice as fast as" : cg > og ? "faster than" : "more slowly than";
    out.push("Capital spending " + verb + to + ", " + cmp + " operating cash flow (" + c93Pct(og) + ").");
  }
  const cov = Number(m.fcf_coverage_of_capex), bits = [];
  if (m.fcf_coverage_of_capex != null && isFinite(cov)) bits.push(cov > 0 ? "Free cash flow still covers " + Math.round(cov * 100) + "% of capital spending" : "Free cash flow is negative");
  if (m.debt_issuance_pct_capex != null) bits.push(Number(m.debt_issuance_pct_capex) === 0 ? "the company issued no new long-term debt" : "new long-term borrowing equalled " + Math.round(Number(m.debt_issuance_pct_capex)) + "% of capital spending");
  if (bits.length) { const s = bits.join(" and "); out.push(s.charAt(0).toUpperCase() + s.slice(1) + "."); }
  return out.join(" ");
}
function c93CheckReading(k, i) {
  const m = i.metrics || {};
  if (k === "sustainability_gap" && m.sustainability_gap_pp != null) { const g = Number(m.sustainability_gap_pp); return "Capital spending growth " + (g >= 0 ? "exceeds" : "trails") + " the average of cash-flow, revenue and operating-income growth by " + Math.abs(g).toFixed(0) + " pt"; }
  if (k === "fcf_coverage" && m.fcf_coverage_of_capex != null) { const c = Number(m.fcf_coverage_of_capex); return c >= 0 ? "Free cash flow equals " + Math.round(c * 100) + "% of capital spending" : "Free cash flow is negative, \u2212" + Math.round(-c * 100) + "% of capital spending"; }
  if (k === "debt_reliance" && m.debt_issuance_pct_capex != null) { const v = Number(m.debt_issuance_pct_capex); return v === 0 ? "No new long-term debt in the last 12 months" : "New long-term debt equals " + v.toFixed(0) + "% of capital spending"; }
  if (k === "interest_burden" && m.interest_pct_opinc != null) return m.operating_loss_ttm ? "Operating loss over the last 12 months, so interest is not covered by operating income" : "Interest is " + Number(m.interest_pct_opinc).toFixed(1) + "% of operating income";
  if (k === "margin_trend" && m.opmargin_change_pp != null) { const v = Number(m.opmargin_change_pp); return "Operating margin " + (v >= 0 ? "up " : "down ") + Math.abs(v).toFixed(1) + " pt year on year"; }
  return "The filing does not give this figure";
}
async function c93CsmCompany(req, res, user, tkr) {
  const d = await c93Monitor("detail", tkr, 1); const i = d && d.instrument; if (!i) return false;
  const r = await c93Monitor("radar", null, BB11_LIMIT_MAX); const list = r && Array.isArray(r.ranking) ? r.ranking : [];
  const f = i.filing || {}, m = i.metrics || {}, t = i.ttm || {}, fl = i.filing_flag || {}, mk = i.market || {}, ch = i.changes_since_last_quarter || {}, disc = i.disclosures || {};
  const name = c93Nm(i, tkr), of = d.rank_of != null ? d.rank_of : list.length || null;
  const by = [];
  if (i.rank != null) by.push("Ranked " + i.rank + (of ? " of " + of : ""));
  if (fl.overall) by.push("Filing flag: " + c93Flag(fl.overall) + (fl.previous_overall && fl.previous_overall !== fl.overall ? " (was " + c93Esc(fl.previous_overall) + " last quarter)" : ""));
  if (f.form) by.push("Based on Form " + c93Esc(f.form) + (f.latest_period_end ? " for the period to " + c93Date(f.latest_period_end) : "") + (f.latest_filed ? ", filed " + c93Date(f.latest_filed) : ""));
  const facts = [[c93Bn(t.capex), "Capex, trailing 12 months" + (m.capex_growth_ttm != null ? " (" + c93Pct(m.capex_growth_ttm) + ")" : "")], [c93Bn(t.ocf), "Operating cash flow, TTM" + (m.ocf_growth_ttm != null ? " (" + c93Pct(m.ocf_growth_ttm) + ")" : "")],
    [c93Bn(t.fcf != null ? t.fcf : m.fcf_ttm), "Free cash flow, TTM"], [m.opmargin_ttm_pct != null ? Number(m.opmargin_ttm_pct).toFixed(1) + "%" : "", "Operating margin, TTM" + (m.opmargin_change_pp != null ? " (" + c93Sg(m.opmargin_change_pp, 1, " pt") + ")" : "")]].filter(x => x[0]);
  const fileUrl = disc.filing && /^https:\/\/www\.sec\.gov\//.test(disc.filing.url || "") ? disc.filing.url : "";
  const src = `Source: SEC EDGAR XBRL company facts, ${c93Esc(name)} Form ${c93Esc(f.form || "filing")}${f.latest_accession ? ", accession " + c93Esc(f.latest_accession) : ""}. TTM = trailing twelve months; growth vs the prior TTM.${fileUrl ? ` <a href="${c93Esc(fileUrl)}" rel="noopener noreferrer">Read the filing</a>` : ""}`;
  const flags = fl.flags || {}, prevF = i.previous_quarter_flags || {};
  const checks = C93_CHECKS.map(([k, label]) => `<tr><td>${label}</td><td>${c93Esc(c93CheckReading(k, i))}</td><td class="n">${c93Flag(flags[k])}</td></tr>`).join("");
  const changed = [];
  const worse = Array.isArray(ch.flags_worse) ? ch.flags_worse : (fl.turned_worse || []), better = Array.isArray(ch.flags_better) ? ch.flags_better : (fl.turned_better || []);
  const lbl = k => ((C93_CHECKS.find(c => c[0] === k) || [0, k.replace(/_/g, " ")])[1]).toLowerCase();
  const pf = k => { const v = prevF && (prevF[k] && typeof prevF[k] === "object" ? prevF[k].flag || prevF[k].overall : prevF[k]); return typeof v === "string" ? v : ""; };
  worse.forEach(k => changed.push("the " + lbl(k) + " check moved " + (pf(k) ? "from " + pf(k) + " " : "") + "to " + (flags[k] || "a worse reading")));
  better.forEach(k => changed.push("the " + lbl(k) + " check improved " + (pf(k) ? "from " + pf(k) + " " : "") + "to " + (flags[k] || "a better reading")));
  if (ch.capex_growth_ttm_prev != null && ch.capex_growth_ttm_now != null) changed.push("capital spending growth went from " + c93Pct(ch.capex_growth_ttm_prev) + " to " + c93Pct(ch.capex_growth_ttm_now));
  const changedTxt = changed.length ? " What changed since last quarter: " + changed.join("; ") + "." : "";
  let side = "";
  if (mk && mk.last_close != null && isFinite(Number(mk.last_close))) {
    const mv = [];
    if (mk.ret_1d_pct != null) mv.push(c93Sg(mk.ret_1d_pct, 1, "%") + " on the day");
    if (mk.ret_5d_pct != null) mv.push(c93Sg(mk.ret_5d_pct, 1, "%") + " over five sessions");
    if (mk.volume_ratio != null) mv.push("volume " + Number(mk.volume_ratio).toFixed(2) + "\u00d7 its 20-day average");
    side = `<div class="card"><div class="kicker">Market context</div><p class="big">$${c93Num(mk.last_close, 2)}</p><p class="src" style="margin:0 0 10px">Last close, ${c93Esc(c93Date(mk.as_of))} \u00b7 Yahoo Finance daily bars, delayed; not a live quote</p>` +
      (mv.length ? `<p style="margin:0 0 10px">${c93Esc(mv.join(", ").replace(/^./, c => c.toUpperCase()))}.${i.attention ? " Market attention: " + c93Esc(i.attention) + "." : ""}</p>` : "") +
      (disc.customer_concentration && disc.customer_concentration.summary ? `<p class="src">Customer concentration: ${c93Esc(disc.customer_concentration.summary)}${disc.customer_concentration.section ? " (" + c93Esc(disc.customer_concentration.section) + ")" : ""}</p>` : "") + `</div>`;
  }
  const commits = Array.isArray(disc.power_and_data_centre_commitments) ? disc.power_and_data_centre_commitments.filter(c => c && c.item && c.usd_bn != null && isFinite(Number(c.usd_bn))) : [];
  const commitHtml = commits.length ? `<section><h2>Commitments the filing discloses</h2><table><thead><tr><th>Commitment</th><th class="n">Amount</th><th class="hide-m">Where in the filing</th></tr></thead><tbody>${commits.map(c => `<tr><td>${c93Esc(c.item)}</td><td class="n">${c93Esc(c93Bn(Number(c.usd_bn) * 1e9))}</td><td class="src hide-m">${c93Esc(c.section || "")}</td></tr>`).join("")}</tbody></table></section>` : "";
  const idx = list.findIndex(x => x.ticker === tkr), prev = idx > 0 ? list[idx - 1] : null, next = idx >= 0 && idx < list.length - 1 ? list[idx + 1] : null;
  const pager = (prev || next) ? `<nav class="pager" aria-label="Adjacent companies"><span>${prev ? `<a href="${C93_CSM}/${prev.ticker}">\u2190 ${c93Esc(c93Nm(prev))} (ranked ${prev.rank})</a>` : ""}</span><a href="${C93_CSM}">All ${of || list.length} companies</a><span>${next ? `<a href="${C93_CSM}/${next.ticker}">${c93Esc(c93Nm(next))} (ranked ${next.rank}) \u2192</a>` : ""}</span></nav>` : "";
  const body = `<section><div class="kicker">Capital Sustainability Monitor${i.group ? " \u00b7 " + c93Esc(c93Grp(i.group)) : ""}</div><h1>${c93Esc(name)} (${c93Esc(tkr)})</h1>${c93Dek(i) ? `<p class="dek">${c93Esc(c93Dek(i))}</p>` : ""}<p class="byline">${by.join(" \u00b7 ")}</p>` +
    (facts.length ? `<div class="facts">${facts.map(x => `<div><b>${c93Esc(x[0])}</b><span>${c93Esc(x[1])}</span></div>`).join("")}</div>` : "") + `<p class="src">${src}</p></section>` +
    `<section><div class="grid"><div><h2>The five checks</h2><table style="margin-top:12px"><thead><tr><th>Check</th><th>Reading</th><th class="n">Flag</th></tr></thead><tbody>${checks}</tbody></table><p class="note">Thresholds are editorial judgments, published in full on the <a href="${C93_CSM}/method">method page</a>.${c93Esc(changedTxt)}</p></div><div>${side}</div></div></section>` +
    commitHtml + pager;
  return c93Html(req, res, c93Shell({ title: `${name} (${tkr}) | Capital Sustainability Monitor | The Dispatch Market`, path: C93_CSM + "/" + tkr, desc: (c93Dek(i) || `${name} in the Capital Sustainability Monitor.`) + " Not investment advice.", user, strip: `<a href="/research/">Research</a> \u203a <a href="${C93_CSM}">Capital Sustainability Monitor</a> \u203a ${c93Esc(name)}`, body }), "public, max-age=300");
}
// ── Home for guests: the approved layout. Prices fill from the site's own feeds; rows without a figure are left out ──
const C93_LIVE_JS = /*C93_LIVE_JS*/"";
async function c93Home(req, res) {
  const now = Date.now(), ses = c93Sessions(now);
  let mon = null; try { mon = await c93Monitor("radar", null, 3); } catch (e) { mon = null; }
  const top = mon && Array.isArray(mon.ranking) ? mon.ranking.slice(0, 3) : [];
  const monHtml = top.length ? `<section><div class="kicker">Research</div><h2 style="margin-top:8px">Capital Sustainability Monitor</h2><p style="max-width:720px;margin:0 0 14px">Is AI spending outrunning the cash that pays for it? We rank ${mon.total || 19} US-listed companies on capital spending against operating cash flow, debt and margins, using their SEC filings.</p><table><thead><tr><th>Company</th><th>What stands out</th><th class="n">Filing flag</th></tr></thead><tbody>${c93MonitorRows(top, false)}</tbody></table><p class="src" style="margin-top:12px">${c93Esc(c93CsmSource(mon))} <a href="${C93_CSM}/method">Method</a> \u00b7 <a href="${C93_CSM}">All ${mon.total || 19} companies</a></p></section>` : "";
  const body = `<section><div class="kicker">Independent gold and macro research</div><h1>Know what matters before gold moves.</h1><p class="dek">${C93_MISSION} A daily read on the dollar, real yields, oil and risk appetite, and what they mean for gold.</p><p class="byline">${C93_EDITOR} \u00b7 <a href="/about">About the desk</a> \u00b7 <a href="/methodology">How we work</a></p></section>` +
    `<section id="c93top"><div class="grid" data-auto><div data-need hidden><h2>Market context</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds. Where a market is shut we show its last close.</p>${c93CtxTable("gold,dxy,tnx,ry,btc,wti")}</div>` +
    `<div class="card" id="c93brief" hidden><div class="kicker" id="c93bk">Today's brief</div><h3 style="margin-top:8px" id="c93bh"></h3><p style="margin:0 0 8px" id="c93bp"></p><p class="src"><span id="c93bt"></span> \u00b7 <a href="/brief/">Read the brief</a></p></div></div></section>` + monHtml;
  const html = c93Shell({ title: "The Dispatch Market | Independent gold and macro research", path: "/", desc: C93_MISSION + " " + C93_EDITOR + ".", body, tail: `<script>${C93_LIVE_JS}</script>` }).replace("<body>", `<body data-wk="${ses.weekend ? 1 : 0}">`);
  return c93Html(req, res, html, "private, max-age=60");
}
function c93CtxTable(keys) {
  return `<table class="ctx"><thead><tr><th>Measure</th><th class="n">Level</th><th class="n">Change</th><th class="src">Source, as of (UK)</th></tr></thead><tbody data-rows="${keys}"></tbody></table><p class="note c93miss" hidden>Some prices are delayed; we show the last official figure with its date.</p>`;
}
function c93SesClass(ms) {                                                 // session label per asset class, New York hours
  const ny = c93UkParts(ms, "America/New_York"), d = ny.weekday || "", t = Number(ny.hour || 0) * 60 + Number(ny.minute || 0);
  const us = /Monday|Tuesday|Wednesday|Thursday|Friday/.test(d) && t >= 570 && t < 960;
  const fut = (d === "Sunday" && t >= 1080) || (/Monday|Tuesday|Wednesday|Thursday/.test(d) && (t < 1020 || t >= 1080)) || (d === "Friday" && t < 1020);
  const wk = d === "Saturday" || (d === "Sunday" && t < 1080) || (d === "Friday" && t >= 1020);
  const shut = wk ? "closed for the weekend; prices are Friday's close" : "between sessions; prices are the last close";
  return { us: "US shares: " + (us ? "open, prices delayed" : wk ? "closed for the weekend; prices are Friday's close" : "closed; prices are the last close"),
    metals: "Gold and silver futures: " + (fut ? "trading, prices delayed" : shut), energy: "Energy futures: " + (fut ? "trading, prices delayed" : shut),
    fx: "Currencies: " + (fut ? "trading" : shut) + ". Treasury yields: the latest daily figure", crypto: "Crypto: trades every day" };
}
function c93Card(title, body) { return `<div class="card"><h3 style="margin:0 0 6px">${title}</h3>${body}</div>`; }
const C93_MEMBERS = `<p style="margin:0">Signed-in members also get watchlists, the full desk brief and the Gold Dashboard. <a href="/__auth/login">Sign in</a> or <a href="/pricing">see plans</a>.</p>`;
function c93RegimeCard() {
  return `<div class="card" id="c93rg" hidden><div class="kicker">Risk-appetite gauge</div><p class="big" id="c93rgv" style="margin:8px 0 6px"></p><p style="margin:0 0 8px" id="c93rgp"></p><p class="src" id="c93rgs"></p></div>`;
}
function c93Guest(req, res, o) {
  const ses = c93Sessions(Date.now());
  const html = c93Shell({ title: o.title + " | The Dispatch Market", path: o.path, desc: o.desc, body: o.body, tail: `<script>${C93_LIVE_JS}</script>` }).replace("<body>", `<body data-wk="${ses.weekend ? 1 : 0}">`);
  return c93Html(req, res, html, "private, max-age=60");
}
function c93Group(title, ses, keys) {
  return `<section data-need hidden><h2>${title}</h2><p class="note" style="margin:0 0 12px">${c93Esc(ses)}.</p>${c93CtxTable(keys)}</section>`;
}
function c93Markets(req, res) {
  const s = c93SesClass(Date.now());
  const body = `<section><div class="kicker">Markets</div><h1>Markets</h1><p class="dek">Prices across asset classes from free public feeds. Each line shows its source and the time it was checked, in UK time. Some feeds are delayed.</p></section>` +
    c93Group("Gold and silver", s.metals, "gold,silver") + c93Group("Energy", s.energy, "wti,ng") + c93Group("The dollar, currencies and rates", s.fx, "dxy,eurusd,gbpusd,usdjpy,tnx,ry") +
    c93Group("US shares", s.us, "spx,djia,ixic,vix") + c93Group("Crypto", s.crypto, "btc,eth,sol") +
    `<section><p class="note" style="margin:0">Where each figure comes from is set out in our <a href="/methodology">methodology</a>.</p>${C93_MEMBERS}</section>`;
  return c93Guest(req, res, { title: "Markets", path: "/markets/", desc: "Gold, oil, the dollar, yields, US shares and crypto, each with its source and UK time. Not investment advice.", body });
}
function c93Gold(req, res) {
  const s = c93SesClass(Date.now());
  const body = `<section><div class="kicker">Gold</div><h1>Gold and what moves it</h1><p class="dek">Gold has no yield, so it tends to compete with what cash and bonds pay after inflation, and it is priced in dollars. These are the measures we watch, with their sources.</p><p class="byline">${C93_EDITOR}</p></section>` +
    `<section><div class="grid" data-auto><div data-need hidden><h2>The gold dashboard, in brief</h2><p class="note" style="margin:0 0 12px">${c93Esc(s.metals)}.</p>${c93CtxTable("gold,silver,dxy,ry,tnx")}</div>${c93RegimeCard()}</div></section>` +
    `<section class="prose"><h2>How to read these figures</h2><p><strong>Real yield.</strong> The 10-year US Treasury yield after expected inflation. When it rises, holding gold costs more in income given up, and gold has often struggled; when it falls, the reverse.</p><p><strong>The dollar.</strong> Gold is priced in US dollars, so a stronger dollar makes it dearer for buyers using other currencies.</p><p><strong>Risk appetite.</strong> In stressed markets some investors move towards gold; our gauge summarises five market inputs.</p><p class="note">These are long-run tendencies, not rules, and they break down for long stretches. Not investment advice.</p></section>` +
    `<section>${c93Card("The full Gold Dashboard", `<p style="margin:0 0 8px">Levels, sessions and volatility, updated through the day, are part of membership.</p>${C93_MEMBERS}`)}</section>`;
  return c93Guest(req, res, { title: "Gold", path: "/gold/", desc: "Gold futures, the dollar and real yields, with sources and UK times, and how to read them. Not investment advice.", body });
}
function c93Brief(req, res) {
  const day = c93UkDay(Date.now());
  const body = `<section><div class="kicker">Today's brief \u00b7 ${c93Esc(day)}</div><h1 id="c93bh">Today's brief</h1><p class="dek" id="c93bp"></p><p class="byline"><span id="c93bt"></span> \u00b7 ${C93_EDITOR}</p></section>` +
    `<section><div class="grid" data-auto><div data-need hidden><h2>The figures behind it</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds; where a market is shut we show its last close.</p>${c93CtxTable("gold,dxy,tnx,ry,wti,spx,vix,btc")}</div>${c93RegimeCard()}</div></section>` +
    `<section>${c93Card("The full desk brief", `<p style="margin:0 0 8px">Members get the full brief with themes, catalysts and the companies in the news, plus an audio version.</p>${C93_MEMBERS}`)}<p class="note" style="margin-top:12px">This brief is built by rules from the figures shown, not written by AI. It describes conditions; it is not a recommendation.</p></section>`;
  return c93Guest(req, res, { title: "Today's brief", path: "/brief/", desc: "A short daily read on gold, the dollar, real yields, oil and risk appetite, with sources. Not investment advice.", body });
}
function c93Signals(req, res) {
  const body = `<section><div class="kicker">Signals</div><h1>What moved past our review line</h1><p class="dek">We flag any market that moved more than 1.5% since its previous close, and we publish our risk-appetite gauge. These describe what happened. They are not trade signals or recommendations.</p></section>` +
    `<section><div class="grid" data-auto><div><div data-need hidden><h2>Moves of more than 1.5%</h2><table class="ctx"><thead><tr><th>Market</th><th class="n">Level</th><th class="n">Move</th><th class="src">Source, as of (UK)</th></tr></thead><tbody id="c93sigb"></tbody></table></div><p id="c93sign" hidden>No market we follow moved more than 1.5% since its previous close.</p></div>${c93RegimeCard()}</div></section>` +
    `<section><p class="note" style="margin:0 0 8px">The 1.5% line is an editorial threshold, explained in our <a href="/methodology">methodology</a>.</p>${C93_MEMBERS}</section>`;
  return c93Guest(req, res, { title: "Signals", path: "/signals/", desc: "Markets that moved more than 1.5%, and our risk-appetite gauge, with sources. Not investment advice.", body });
}
let c93NewsCache = { t: 0, items: [] };
async function c93News(req, res) {
  const now = Date.now();
  if (now - c93NewsCache.t > 600000 || !c93NewsCache.items.length) {
    let items = []; try { if (typeof _rt48sHeads === "function") items = await _rt48sHeads(2500); } catch (e) { items = []; }
    if (items.length || now - c93NewsCache.t > 3600000) c93NewsCache = { t: now, items: items || [] };
  }
  const items = c93NewsCache.items.filter(x => x.link).slice(0, 15);
  const tm = t => { if (!t) return ""; const o = c93UkParts(t); return `${o.weekday ? o.weekday.slice(0, 3) : ""} ${o.day || ""} ${o.month ? o.month.slice(0, 3) : ""}, ${o.hour}:${o.minute} UK`; };
  const list = items.length ? `<section><h2>Headlines that matter for gold and macro</h2><p class="note" style="margin:0 0 12px">From publishers' public feeds, linked to the original. We pick headlines that mention gold, rates, the dollar, oil, shares or crypto.</p><table><thead><tr><th>Headline</th><th class="src">Source, published (UK)</th></tr></thead><tbody>${items.map(x => `<tr><td><a href="${c93Esc(x.link)}" rel="noopener nofollow">${c93Esc(x.h)}</a><span class="src msrc">${c93Esc(x.src)} \u00b7 ${c93Esc(tm(x.t))}</span></td><td class="src">${c93Esc(x.src)} \u00b7 ${c93Esc(tm(x.t))}</td></tr>`).join("")}</tbody></table></section>` : "";
  let fil = ""; try { const d = await c93Monitor("radar", null, BB11_LIMIT_MAX); const rows = d && Array.isArray(d.ranking) ? d.ranking.filter(r => r.filing && r.filing.latest_filed).sort((a, b) => String(b.filing.latest_filed).localeCompare(String(a.filing.latest_filed))).slice(0, 6) : [];
    if (rows.length) fil = `<section><h2>Latest company filings we track</h2><p class="note" style="margin:0 0 12px">From SEC EDGAR, for the 19 companies in the <a href="${C93_CSM}">Capital Sustainability Monitor</a>.</p><table><thead><tr><th>Company</th><th>Filing</th><th class="n">Filed</th></tr></thead><tbody>${rows.map(r => `<tr><td><a href="${C93_CSM}/${encodeURIComponent(r.ticker)}">${c93Esc(c93Nm(r))}</a></td><td>Form ${c93Esc(r.filing.form || "")} for the period to ${c93Esc(c93Date(r.filing.latest_period_end))}</td><td class="n">${c93Esc(c93Date(r.filing.latest_filed))}</td></tr>`).join("")}</tbody></table></section>`;
  } catch (e) { fil = ""; }
  const body = `<section><div class="kicker">News</div><h1>News</h1><p class="dek">Headlines from public news feeds and the latest company filings we track, each with its source and time.</p></section>` + list + fil +
    `<section>${C93_MEMBERS}</section>`;
  return c93Html(req, res, c93Shell({ title: "News | The Dispatch Market", path: "/news/", desc: "Gold and macro headlines from public feeds, and the latest SEC filings we track. Not investment advice.", body }), "private, max-age=120");
}
async function c93ResearchHub(req, res) {
  let mon = null; try { mon = await c93Monitor("radar", null, 3); } catch (e) { mon = null; }
  const top = mon && Array.isArray(mon.ranking) ? mon.ranking.slice(0, 3) : [];
  const body = `<section><div class="kicker">Research</div><h1>Research</h1><p class="dek">Long-form research built from official filings and public data, with the method published alongside.</p><p class="byline">${C93_EDITOR}</p></section>` +
    (top.length ? `<section><div class="kicker">Monitor \u00b7 updated daily</div><h2 style="margin-top:8px"><a href="${C93_CSM}">Capital Sustainability Monitor</a></h2><p style="max-width:720px;margin:0 0 14px">Is AI spending outrunning the cash that pays for it? Five checks on ${mon.total || 19} US-listed companies, from their SEC filings.</p><table><thead><tr><th>Company</th><th>What stands out</th><th class="n">Filing flag</th></tr></thead><tbody>${c93MonitorRows(top, false)}</tbody></table><p class="src" style="margin-top:12px">${c93Esc(c93CsmSource(mon))} <a href="${C93_CSM}/method">Method</a> \u00b7 <a href="${C93_CSM}">All ${mon.total || 19} companies</a></p></section>` : "") +
    `<section><h2>Also from the desk</h2><table><tbody><tr><td><a href="/brief/">Today's brief</a></td><td>A short daily read on gold, the dollar, real yields, oil and risk appetite.</td></tr><tr><td><a href="/gold/">Gold</a></td><td>The measures that move gold, with sources, and how to read them.</td></tr><tr><td><a href="/methodology">Methodology</a></td><td>Where every figure comes from and what we do when a feed fails.</td></tr></tbody></table><div style="margin-top:14px">${C93_MEMBERS}</div></section>`;
  return c93Html(req, res, c93Shell({ title: "Research | The Dispatch Market", path: "/research/", desc: "Research from The Dispatch Market, including the Capital Sustainability Monitor. Not investment advice.", body }), "private, max-age=120");
}
const C93_GUEST = { "/markets": c93Markets, "/gold": c93Gold, "/brief": c93Brief, "/signals": c93Signals, "/news": c93News, "/research": c93ResearchHub };
async function c93Route(req, res) {                                        // guest Home and the monitor pages; everything else falls through to the app
  if (req.method !== "GET" && req.method !== "HEAD") return false;
  let p = ""; try { p = new URL(req.url, "http://localhost").pathname; } catch (e) { return false; }
  const gk = p.replace(/\/+$/, "") || "/";
  const guest = p === "/" || p === "/index.html" || Object.prototype.hasOwnProperty.call(C93_GUEST, gk);
  if (!guest && p.indexOf(C93_CSM) !== 0) return false;
  let user = null; try { user = await currentUser(req); } catch (e) { user = null; }
  if (guest) {
    if (user) return false;                                                // signed-in readers keep the app views
    if (p === "/" || p === "/index.html") { await c93Home(req, res); return true; }
    if (!p.endsWith("/")) { res.writeHead(301, { Location: gk + "/" }); res.end(); return true; }
    await C93_GUEST[gk](req, res); return true;
  }
  const rest = p.slice(C93_CSM.length).replace(/\/+$/, "");
  if (rest === "") return (await c93CsmIndex(req, res, user)) !== false;
  if (rest === "/method") return (await c93CsmMethod(req, res, user)) !== false;
  const m = /^\/([A-Za-z0-9.\-]{1,10})$/.exec(rest);
  if (m && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(m[1].toUpperCase()) >= 0) {
    if (m[1] !== m[1].toUpperCase()) { res.writeHead(301, { Location: C93_CSM + "/" + m[1].toUpperCase() }); res.end(); return true; }
    return (await c93CsmCompany(req, res, user, m[1])) !== false;
  }
  return false;
}
