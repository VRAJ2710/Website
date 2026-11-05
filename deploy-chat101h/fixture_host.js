// Local stand-in for the live server hooks chat101h wraps. Not deployed.
const http = require("http");
const BB10I_MAINTENANCE_ON = false;
const PUBLIC_ORIGIN = "https://thedispatch.uk";
const C93_EDITOR = "Edited by Vraj Patel";
const C93_DISC = "Not investment advice. Capital at risk.";
const C93_CONTACT = "vraj2710@hotmail.com";
function c93Esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function c93Head(title, path, desc, extra) {
  return `<!doctype html><html lang="en-GB" class="c97-system"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${c93Esc(title)}</title><meta name="description" content="${c93Esc(desc)}"><link rel="canonical" href="https://thedispatch.uk${path}"><style>
:root{--paper:#fbfaf7;--ink:#1b1b1b;--muted:#5f6368;--rule:#dedad2;--accent:#1f3a5f;--serif:Georgia,serif;--sans:system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 var(--sans)}
a{color:var(--accent)}h1{font:600 2rem/1.15 var(--serif);margin:8px 0 12px}h2{font:600 1.4rem/1.25 var(--serif)}
.wrap{max-width:1120px;margin:0 auto;padding:0 32px}header.site{border-bottom:1px solid var(--rule)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;min-height:56px;gap:12px}
.nav a{margin-left:16px;color:var(--ink);min-height:44px;display:inline-flex;align-items:center}
.menu{display:none}.menu summary{cursor:pointer;min-height:44px;display:inline-flex;align-items:center}.menu nav{display:flex;flex-direction:column}.menu nav a{display:block;padding:12px 0;min-height:44px}.strip{border-bottom:1px solid var(--rule);font-size:13px}.disc{font-weight:700}
main>section{padding:28px 0;border-bottom:1px solid var(--rule)}.kicker{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);font-weight:700}
.dek{font:1.15rem/1.5 var(--serif);max-width:68ch}.byline,.note{color:var(--muted);font-size:14px}
.strip .wrap{display:flex;justify-content:space-between;gap:16px;align-items:center}
footer.site{padding:28px 0 48px;color:var(--muted);font-size:14px}
@media (max-width:760px){.wrap{padding:0 16px}.nav{display:none}.menu{display:block}h1{font-size:1.7rem}.strip .wrap{flex-direction:column;align-items:flex-start;gap:4px}}
html.c97-dark,html.c97-dark body{background:#151b23;color:#e7eaee}
html.c97-dark{--paper:#151b23;--ink:#e7eaee;--muted:#aab3bf;--rule:#334050;--accent:#9cc0ea}
@media (prefers-color-scheme:dark){html.c97-system{background:#151b23;color:#e7eaee;--paper:#151b23;--ink:#e7eaee;--muted:#aab3bf;--rule:#334050;--accent:#9cc0ea}}
</style><script>(function(){var q=/[?&]theme=(light|dark)/.exec(location.search||"");var m=/(?:^|;\\s*)dispatch_theme=(light|dark|system)/.exec(document.cookie||"");var s=q?q[1]:(m?m[1]:"system");document.documentElement.classList.remove("c97-light","c97-dark","c97-system");document.documentElement.classList.add("c97-"+s);})();</script>${extra || ""}</head>`;
}
function c93Header(path, user) {
  const acct = user ? '<a class="cta" href="/dashboard/">Your desk</a>' : '<a class="cta" href="/__auth/login">Sign in</a>';
  const links = [["/brief/", "Brief"], ["/gold/", "Gold"], ["/markets/", "Markets"], ["/research/", "Research"], ["/methodology", "Methodology"], ["/about", "About"]].map(([h, t]) => `<a href="${h}">${t}</a>`).join("");
  return `<header class="site"><div class="wrap"><a class="mark" href="/">The Dispatch Market</a><nav class="nav" aria-label="Main">${links}${acct}</nav><details class="menu"><summary>Menu</summary><nav aria-label="Main">${links}${acct}</nav></details></div></header>`;
}
function c93Footer() {
  return `<footer class="site"><div class="wrap"><div class="links"><a href="/about">About</a><a href="/editorial-standards">Editorial standards</a><a href="/methodology">Methodology</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></div><p><span class="disc">${C93_DISC}</span> The Dispatch Market publishes research and education, not personal recommendations.</p><p>Published by Vraj Patel · © 2026 The Dispatch Market</p></div></footer>`;
}
function c93Shell(o) {
  const left = o.strip != null ? o.strip : "Thursday 5 November 2026";
  return c93Head(o.title, o.path, o.desc, o.extraHead) + `<body>${c93Header(o.path, o.user)}<div class="strip"><div class="wrap"><span>${left}</span><span class="disc">${C93_DISC}</span></div></div><main class="wrap">${o.body}</main>${c93Footer()}${o.tail || ""}</body></html>`;
}
function c93Html(req, res, html, cache) {
  if (typeof c97Transform === "function") html = c97Transform(html, req);
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": cache || "public, max-age=300" });
  res.end(req.method === "HEAD" ? undefined : html);
}
function c97Transform(html) { return html; }
async function renderPublicSitemap() {
  const urls = ["/", "/research/", "/research/capital-sustainability", "/research/sec/", "/research/filing-changes/", "/gold/", "/brief/", "/tools/", "/central-banks/"];
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` + urls.map((u) => `  <url><loc>${PUBLIC_ORIGIN}${u}</loc></url>\n`).join("") + `</urlset>`;
}
async function c96UserOf(req) {
  const m = /dispatch_session=([^;]+)/.exec(String(req.headers.cookie || ""));
  if (!m) return null;
  if (m[1] === "hadmin") return { id: "hadmin", tier: "premium", isAdmin: true };
  if (m[1] === "hprem") return { id: "hprem", tier: "premium" };
  if (m[1] === "hmember") return { id: "hmember", tier: "free" };
  return null;
}
function isAdminUser(u) { return !!(u && u.isAdmin); }
const HUB = `<section><div class="kicker">Research</div><h1>Research</h1><p class="dek">Long-form research built from official filings and public data, with the method published alongside.</p><p class="byline">Edited by Vraj Patel</p></section><section><div class="kicker">Monitor · updated daily</div><h2><a href="/research/capital-sustainability">Capital Sustainability Monitor</a></h2><p>Is AI spending outrunning the cash that pays for it?</p></section><section data-c101-tools><h2>Check and plan</h2><a href="/tools/verify/">Verify this claim</a></section><section><h2>Also from the desk</h2><a href="/brief/">Today's brief</a><a href="/gold/">Gold</a><a href="/methodology">Methodology</a></section>`;
async function handle(req, res) {
  const u = new URL(req.url || "/", "http://localhost");
  const p = u.pathname;
  if (p === "/sitemap.xml") {
    const x = await renderPublicSitemap();
    res.writeHead(200, { "Content-Type": "application/xml; charset=utf-8" });
    return res.end(x);
  }
  if (p === "/research" || p === "/research/") {
    return c93Html(req, res, c93Shell({ title: "Research | The Dispatch Market", path: "/research/", desc: "Research from The Dispatch Market, including the Capital Sustainability Monitor. Not investment advice.", body: HUB }), "private, max-age=120");
  }
  const known = {
    "/": "HOME",
    "/gold/": "GOLD",
    "/brief/": "BRIEF",
    "/markets/": "MARKETS",
    "/research/capital-sustainability": "CSM",
    "/research/capital-sustainability/method": "CSM-METHOD",
    "/research/capital-sustainability/ORCL": "CSM-ORCL",
    "/research/sec/": "SEC",
    "/research/filing-changes/": "FILING",
    "/research/research-desk/": "DESK",
    "/central-banks/": "CB",
    "/tools/": "TOOLS",
    "/editorial-standards": "STANDARDS",
    "/methodology": "METHOD",
    "/about": "ABOUT",
    "/pricing": "PRICING"
  };
  if (Object.prototype.hasOwnProperty.call(known, p)) {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    return res.end(`<html><body><main>${known[p]}</main></body></html>`);
  }
  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("missing");
}
// chat101f: market quotes first
// BLOCK
const port = Number(process.env.PORT || 8877);
http.createServer((req, res) => handle(req, res)).listen(port, "127.0.0.1");
