// ── chat93: trust pages on a plain paper template (About, Contact, Methodology, Corrections, Editorial standards) ──
const C93_MISSION = "Verified gold and macro research for independent investors, with sources on every figure.";
const C93_EDITOR = "Edited by Vraj Patel, London";
const C93_CONTACT = "dispatchmarket@mail.grokbot.com";
const C93_PHOTO = ""; // optional editor photo URL; when empty the photo slot is not rendered at all
const C93_FOOT_HTML = '<footer class="c93f"><p class="c93f-d"><strong>Not investment advice. Capital at risk.</strong> Figures come from free public feeds and official filings. Each one shows its source and when it was checked, in UK time.</p><p class="c93f-l"><a href="/about">About</a><a href="/editorial-standards">Editorial standards</a><a href="/methodology">Methodology</a><a href="/corrections">Corrections</a><a href="/contact">Contact</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></p><p class="c93f-b">The Dispatch Market \u00b7 ' + C93_EDITOR + '</p></footer>';
const C93_PAGE_CSS = 'html{background:#fbfaf7}body{margin:0;background:#fbfaf7;color:#1b1b1b;font:17px/1.65 "Public Sans",system-ui,-apple-system,"Segoe UI",Arial,sans-serif;font-variant-numeric:tabular-nums}' +
  '.c93h{border-bottom:1px solid rgba(27,27,27,.14)}.c93h>div{max-width:820px;margin:0 auto;padding:14px 20px;display:flex;gap:8px 16px;align-items:center;flex-wrap:wrap}' +
  '.c93h .w{font:600 21px/1.2 Fraunces,Georgia,serif;color:#1b1b1b;text-decoration:none;margin-right:auto}.c93h nav{display:flex;flex-wrap:wrap;gap:4px 14px}.c93h nav a{font-size:14px;color:#45443f;text-decoration:none}.c93h nav a:hover,.c93h nav a[aria-current]{color:#1b1b1b;text-decoration:underline}' +
  '.c93s{background:#f4f2ec;font-size:13px;color:#45443f;border-bottom:1px solid rgba(27,27,27,.07)}.c93s>div{max-width:820px;margin:0 auto;padding:6px 20px}' +
  'main{max-width:820px;margin:0 auto;padding:34px 20px 8px;box-sizing:border-box}h1{font:600 38px/1.15 Fraunces,Georgia,serif;margin:0 0 12px}h2{font:600 22px/1.3 Fraunces,Georgia,serif;margin:32px 0 8px}' +
  'p,li{color:#2b2a26}a{color:#1f3a5f}.lede{font-size:19px;color:#45443f}.by{font-size:14px;color:#66655f;margin-top:-4px}' +
  'table{border-collapse:collapse;width:100%;font-size:15px;margin:8px 0}th,td{text-align:left;padding:8px 10px 8px 0;border-bottom:1px solid rgba(27,27,27,.1);vertical-align:top}thead th{font-size:13px;color:#66655f;border-bottom:1px solid rgba(27,27,27,.28)}' +
  '.photo{margin:0 0 16px}.photo img{width:120px;height:120px;object-fit:cover;border-radius:4px}' +
  '.c93f{max-width:820px;margin:44px auto 0;padding:20px 20px 36px;border-top:1px solid rgba(27,27,27,.28);font-size:14px;color:#45443f;box-sizing:border-box}.c93f p{margin:0 0 8px;color:#45443f}.c93f-d{color:#1b1b1b!important}.c93f-l{display:flex;flex-wrap:wrap;gap:4px 14px}.c93f-l a{color:#45443f}.c93f-b{color:#66655f!important;font-size:13px}' +
  '.c93g{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:18px 0}.c93c{border:1px solid rgba(27,27,27,.16);border-radius:6px;padding:18px 20px;background:#fff}.c93c h2{margin:0 0 4px}.c93cp{border-color:#1f3a5f}.c93pr{font:600 28px/1.2 Fraunces,Georgia,serif;margin:0 0 8px;color:#1b1b1b}.c93c ul{padding-left:20px;margin:0}.c93c li{margin:4px 0;font-size:15px}.muted{font-size:14px;color:#66655f}' +
  '@media (max-width:600px){h1{font-size:30px}body{font-size:16px}}';
function c93Esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function c93Page(title, path, desc, body) {
  const nav = [["/brief/", "Brief"], ["/gold/", "Gold"], ["/markets/", "Markets"], ["/research/", "Research"], ["/methodology", "Methodology"], ["/about", "About"]]
    .map(([h, t]) => `<a href="${h}"${h === path ? ' aria-current="page"' : ""}>${t}</a>`).join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${c93Esc(title)} | The Dispatch Market</title><meta name="description" content="${c93Esc(desc)}"><link rel="canonical" href="https://thedispatch.uk${path}"><meta name="theme-color" content="#fbfaf7"><meta property="og:site_name" content="The Dispatch Market"><meta property="og:title" content="${c93Esc(title)} | The Dispatch Market"><meta property="og:description" content="${c93Esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://thedispatch.uk${path}"><meta property="og:image" content="https://thedispatch.uk/og-card.png"><meta name="twitter:card" content="summary_large_image"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Public+Sans:wght@400;600&display=swap" rel="stylesheet"><style>${C93_PAGE_CSS}</style></head><body><header class="c93h"><div><a class="w" href="/">The Dispatch Market</a><nav aria-label="Main">${nav}</nav></div></header><div class="c93s"><div><strong>Not investment advice. Capital at risk.</strong> Every figure shows its source and the time it was checked, in UK time.</div></div><main>${body}</main>${C93_FOOT_HTML}</body></html>`;
}
const C93_PAGES = {
  "/about": ["About The Dispatch Market", "Who edits The Dispatch Market, what it publishes and how it works. " + C93_MISSION, () =>
    (C93_PHOTO ? `<figure class="photo"><img src="${c93Esc(C93_PHOTO)}" alt="Vraj Patel" width="120" height="120"></figure>` : "") +
    `<h1>About The Dispatch Market</h1><p class="lede">${C93_MISSION}</p><p class="by">${C93_EDITOR}</p>` +
    `<h2>What we publish</h2><ul><li><a href="/brief/">The Brief</a>: a short daily read of what moved in gold, rates, the dollar, oil and shares, and why it may matter.</li><li><a href="/playbook/">The Playbook</a>: a weekly set of gold and macro scenarios, with what would change the view.</li><li><a href="/gold/">Gold</a> and <a href="/markets/">Markets</a>: prices across asset classes, each with its source and time.</li><li><a href="/research/capital-sustainability">The Capital Sustainability Monitor</a>: what company filings at the SEC show about how big spenders fund their capital spending.</li></ul>` +
    `<h2>How we work</h2><p>Every figure on the site carries its source and the time it was checked, in UK time. Most prices come from free public feeds, so some are delayed. Company figures come from official SEC filings. When a feed fails we show the last official figure with its date, or say plainly that the figure is not available. We do not fill gaps with guesses.</p><p>The full list of sources is on the <a href="/methodology">methodology page</a>. How we write and check is on the <a href="/editorial-standards">editorial standards page</a>, and anything we get wrong is logged on the <a href="/corrections">corrections page</a>.</p>` +
    `<h2>What we are not</h2><p>The Dispatch Market is a research publication. It is not a broker and it does not give personal financial advice. Nothing here is a recommendation to buy or sell anything. Not investment advice. Capital at risk: the value of investments can fall as well as rise.</p>` +
    `<h2>Get in touch</h2><p>Email <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a>. More on the <a href="/contact">contact page</a>.</p>`],
  "/contact": ["Contact", "How to contact The Dispatch Market, report an error or ask about your account.", () =>
    `<h1>Contact</h1><p class="lede">The quickest way to reach us is by email.</p><p><a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a></p>` +
    `<h2>Reporting an error</h2><p>Tell us the page, the figure and what you think is wrong. We check every report and log confirmed fixes on the <a href="/corrections">corrections page</a>.</p>` +
    `<h2>Accounts and billing</h2><p>Premium is billed monthly through Stripe. You can manage or cancel it from Settings when signed in, or email us and we will help.</p>` +
    `<h2>What we cannot do</h2><p>We cannot give personal financial advice or tell you whether to buy or sell anything. Not investment advice. Capital at risk.</p>`],
  "/methodology": ["Methodology", "Where every figure on The Dispatch Market comes from, how often it updates and what we do when a feed fails.", () =>
    `<h1>Methodology</h1><p class="lede">Where our figures come from, how fresh they are, and what we show when a source fails.</p>` +
    `<h2>Sources</h2><table><thead><tr><th>What</th><th>Source</th><th>Freshness</th></tr></thead><tbody>` +
    `<tr><td>Gold spot price</td><td>gold-api.com (free feed)</td><td>Checked about every 30 seconds while the page is open</td></tr>` +
    `<tr><td>Shares, indices, oil and currency prices</td><td>Yahoo Finance (free, unofficial), with Finnhub and Twelve Data as backups</td><td>Often delayed by around 15 minutes; outside trading hours we show the last close and its date</td></tr>` +
    `<tr><td>US Treasury yields and the real yield</td><td>US Treasury daily rates</td><td>Once a day, the official print with its date</td></tr>` +
    `<tr><td>Oil and gas spot prices</td><td>US Energy Information Administration (EIA)</td><td>The official daily series, usually a day or more behind</td></tr>` +
    `<tr><td>Crypto prices</td><td>Coinbase and CoinGecko public feeds</td><td>Near real time; crypto trades every day</td></tr>` +
    `<tr><td>Company figures (Capital Sustainability Monitor)</td><td>SEC EDGAR company filings (XBRL company facts)</td><td>Checked once a UK day; each page shows the filing, its period and the date it was filed</td></tr>` +
    `<tr><td>News</td><td>Publishers' public RSS feeds, linked to the original</td><td>Every few minutes</td></tr></tbody></table>` +
    `<h2>Times and trading sessions</h2><p>All times are UK time (GMT, or BST in summer). We label sessions by asset class rather than saying "markets closed": US shares trade 9:30am to 4pm New York time on weekdays, gold and major currencies trade almost around the clock from Sunday evening to Friday evening, and crypto trades every day.</p>` +
    `<h2>When a feed fails</h2><p>We show the last official figure with its date, or a plain sentence saying the figure is not available. We never show a blank dash in place of a number.</p>` +
    `<h2>Scores, flags and scenarios</h2><p>Some pages use simple rules-based models, such as the regime reading and the five filing flags in the Capital Sustainability Monitor. The thresholds behind them are editorial judgements, not facts, and they are published with each model. They describe conditions; they are not recommendations. The <a href="/research/capital-sustainability/method">monitor's method</a> is published in full.</p>` +
    `<h2>Use of AI</h2><p>The Ask assistant and some drafts of the daily Brief use an AI model working from the figures above. These are labelled. Rules-based briefs are labelled as built from today's data.</p>` +
    `<p>Not investment advice. Capital at risk.</p>`],
  "/editorial-standards": ["Editorial standards", "How The Dispatch Market writes, sources and checks its research.", () =>
    `<h1>Editorial standards</h1><p class="lede">${C93_MISSION}</p><p class="by">${C93_EDITOR}</p>` +
    `<h2>Sources on every figure</h2><p>Every number we publish carries its source and the time it was checked, in UK time. If we cannot source a figure, we do not publish it.</p>` +
    `<h2>Facts and views kept apart</h2><p>We separate what the data shows from what we think it may mean, and we say what would change our view.</p>` +
    `<h2>No buy or sell calls</h2><p>We do not tell readers to buy, sell or hold anything, and we do not publish price targets. Nothing here is personal financial advice. Not investment advice. Capital at risk.</p>` +
    `<h2>Plain English</h2><p>We write numbers the way people say them ($115.9bn rather than 115,948,000,000) and explain terms the first time we use them.</p>` +
    `<h2>Independence</h2><p>We are funded by reader subscriptions. We do not take payment to cover companies or assets.</p>` +
    `<h2>Corrections</h2><p>When we get something wrong we fix it, say what changed and log it on the <a href="/corrections">corrections page</a>. Report an error to <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a>.</p>`],
  "/corrections": ["Corrections", "Errors we have found and fixed on The Dispatch Market.", () =>
    `<h1>Corrections</h1><p class="lede">When we get something wrong, we fix it and record it here.</p>` +
    `<h2>Log</h2><table><thead><tr><th>Date</th><th>Page</th><th>What was wrong and what we changed</th></tr></thead><tbody>` +
    `<tr><td>October 2026</td><td>Capital Sustainability Monitor, company pages</td><td>Company pages showed the number of companies covered in place of each company's rank (Microsoft showed "Rank 19" when it was 14th of 19). Each page now shows "Rank N of 19".</td></tr></tbody></table>` +
    `<h2>Report an error</h2><p>Email <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a> with the page and the figure.</p>`],
};
const c93PageCache = new Map();
function c93Send(req, res, key) {
  let html = c93PageCache.get(key);
  if (!html) { const d = C93_PAGES[key]; html = c93Page(d[0], key, d[1], d[2]()); c93PageCache.set(key, html); }
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=600" });
  return res.end(req.method === "HEAD" ? undefined : html);
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
