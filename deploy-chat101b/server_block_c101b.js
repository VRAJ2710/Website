// ── chat101b ── every core section back in the header: a few top links plus an "All sections" menu on every
// server page (desktop panel, and the mobile Menu), /what-changed/, and sign-in gates for Documents and Portfolio.
// Admin Console is listed only for the admin. No new tables, no DDL.
const C101B_GROUPS = [
  ["Start", [["/", "Home"], ["/brief/", "Brief"], ["/playbook/", "Playbook"], ["/gold/", "Gold"]]],
  ["Desk", [["/dashboard/", "Dashboard"], ["/lab/", "Market Lab"], ["/signals/", "Signals"]]],
  ["Markets", [["/markets/", "Markets"], ["/screener/", "Screener"], ["/sectors/", "Sectors"], ["/heatmap/", "Heatmap"], ["/crypto/", "Crypto"]]],
  ["Research", [["/news/", "Newsroom"], ["/paper/", "Paper"], ["/research/", "Research"], ["/documents/", "Documents"], ["/geo/", "Geo Ops"]]],
  ["Book", [["/watchlist/", "Watchlist"], ["/portfolio/holdings/", "Portfolio"], ["/learn/", "Learn"]]],
  ["Gold and macro", [["/gold/dashboard/", "Gold dashboard"], ["/calendar/", "Calendar"], ["/what-changed/", "What changed today"], ["/markets/yields/", "Yields"], ["/gold/positioning/", "Gold positioning"], ["/central-banks/", "Central banks"], ["/data-status/", "Data status"]]],
  ["Tools and filings", [["/tools/", "Tools"], ["/tools/verify/", "Verify this claim"], ["/tools/isa-sipp/", "ISA/SIPP planner"], ["/tools/scenario/", "Scenario simulator"], ["/alerts/", "Alerts"], ["/portfolio/", "Portfolio X-ray"], ["/research/filing-changes/", "Filing change detector"], ["/research/sec/", "Company filings"], ["/research/sec/screener/", "Filings screener"], ["/research/capital-sustainability", "Capital Sustainability Monitor"]]],
  ["About", [["/about", "About"], ["/pricing", "Pricing"], ["/free-brief/", "Free brief"], ["/methodology", "Methodology"], ["/editorial-standards", "Editorial standards"], ["/corrections", "Corrections"], ["/contact", "Contact"]]],
  ["Account", [["/settings/", "Settings"]]]
];
const C101B_ADMIN = ["/__admin", "Admin Console"];
const C101B_CSS = "header.site .c101b-all{position:static;display:inline-block;margin-left:24px}" +
  "header.site .c101b-all>summary{list-style:none;cursor:pointer;font-size:14px;color:var(--ink);white-space:nowrap;padding:6px 10px;border:1px solid var(--rule);border-radius:2px}" +
  "header.site .c101b-all>summary::-webkit-details-marker{display:none}" +
  "header.site .c101b-all>summary::after{content:\"\";display:inline-block;margin-left:6px;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid currentColor;vertical-align:2px}" +
  "header.site .c101b-all[open]>summary::after{border-top:0;border-bottom:5px solid currentColor}" +
  "header.site .c101b-all>summary:focus-visible,header.site .menu>summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}" +
  "header.site .c101b-panel{position:absolute;right:24px;top:calc(100% + 1px);width:min(920px,calc(100vw - 48px));max-height:calc(100vh - 96px);overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--rule);border-radius:4px;box-shadow:0 12px 32px rgba(0,0,0,.14);padding:16px 20px;z-index:60;box-sizing:border-box}" +
  ".c101b-cols{columns:3 220px;column-gap:28px}.c101b-g{break-inside:avoid;margin:0 0 14px}" +
  ".c101b-g h2{font:600 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 4px}" +
  ".c101b-g ul{list-style:none;margin:0;padding:0}.c101b-g li{margin:0}" +
  "header.site .c101b-g a{display:block;margin:0;padding:6px 0;font-size:14px;color:var(--ink);border-bottom:1px solid var(--rule);white-space:normal}" +
  "header.site .c101b-g a:hover{color:var(--accent)}header.site .c101b-g a[aria-current=page]{font-weight:600}" +
  ".c101b-note{font-size:12px;color:var(--muted);margin:4px 0 0}" +
  "header.site .menu nav{max-height:calc(100vh - 64px);overflow:auto;box-sizing:border-box}" +
  "header.site .menu nav>a.cta{display:inline-block;border:1px solid var(--ink);padding:6px 12px;margin:6px 0 10px}" +
  "header.site .menu .c101b-cols{columns:2 150px;column-gap:18px}" +
  "header.site .menu .c101b-g a{padding:9px 0;font-size:15px;border-bottom:1px solid var(--rule)}" +
  "header.site .nav{display:flex;align-items:center;flex-wrap:nowrap}" +
  "header.site .nav>a{margin-left:14px}header.site .c101b-all{margin-left:14px}header.site .nav .c101b-g a{margin:0}" +
  "@media (min-width:1280px){header.site .wrap{max-width:1300px}}" +
  "@media (max-width:420px){header.site .wrap{gap:10px}header.site .menu summary{padding-right:0}}" +
  "@media (max-width:380px){header.site .wrap{padding:0 14px;gap:8px}header.site .mark{font-size:17px}}" +
  "@media (max-width:1279px){header.site .nav{display:none}header.site .menu{display:block}header.site .menu nav{position:absolute;left:0;right:0;top:100%}}" +
  "@media (min-width:761px) and (max-width:1279px){header.site .menu .c101b-cols{columns:3 180px}}";
const C101B_JS = "(function(){if(window.__c101b)return;window.__c101b=1;" +
  "function open(){return Array.prototype.slice.call(document.querySelectorAll('header.site details[open]'));}" +
  "document.addEventListener('keydown',function(e){if(e.key!=='Escape')return;var o=open();if(!o.length)return;o.forEach(function(d){d.removeAttribute('open');});var s=o[0].querySelector('summary');if(s)s.focus();});" +
  "document.addEventListener('click',function(e){var d=e.target&&e.target.closest?e.target.closest('header.site details'):null;open().forEach(function(x){if(x!==d)x.removeAttribute('open');});});" +
  "document.addEventListener('focusin',function(e){open().forEach(function(x){if(!x.contains(e.target))x.removeAttribute('open');});});" +
  "})();";
function c101bAllHtml(user, path) {
  const admin = c96IsAdmin(user);
  return `<div class="c101b-cols">` + C101B_GROUPS.map(([g, items]) => {
    const its = g === "Account" && admin ? items.concat([C101B_ADMIN]) : items;
    return `<div class="c101b-g"><h2>${c93Esc(g)}</h2><ul>` + its.map(([h, t]) => `<li><a href="${c93Esc(h)}"${h === path ? ' aria-current="page"' : ""}${h === C101B_ADMIN[0] ? ' data-c101b-admin=""' : ""}>${c93Esc(t)}</a></li>`).join("") + `</ul></div>`;
  }).join("") + `</div><p class="c101b-note">Some pages are for signed-in readers or members; they show a sign-in or plans page when you are signed out.</p>`;
}
c93Header = function (path, user) {
  const cur = h => (h === path || (h.length > 1 && h.endsWith("/") && path.indexOf(h) === 0)) ? ' aria-current="page"' : "";
  const links = C93_NAV.map(([h, t]) => `<a href="${h}"${cur(h)}>${t}</a>`).join("");
  const acct = user ? '<a class="cta" href="/dashboard/">Your desk</a>' : '<a class="cta" href="/__auth/login">Sign in</a>';
  const all = c101bAllHtml(user, path);
  return `<header class="site"><style>${C101B_CSS}</style><div class="wrap"><a class="mark" href="/">The Dispatch Market</a>` +
    `<nav class="nav" aria-label="Main">${links}<details class="c101b-all"><summary>All sections</summary><div class="c101b-panel" role="region" aria-label="All sections">${all}</div></details>${acct}</nav>` +
    `<details class="menu"><summary aria-label="Menu: all sections">Menu</summary><nav aria-label="All sections">${acct}${all}</nav></details></div><script>${C101B_JS}</script></header>`;
};
// /what-changed/ (public), /documents/ and /portfolio/holdings/ (signed-in: open the desk page; signed out: a sign-in page)
async function c101bWhatChanged(req, res, user) {
  const t = await c97Today().catch(() => null);
  const body = `<style>${C97_CSS}</style><section><div class="kicker">Today</div><h1>What changed today</h1><p class="dek">Sourced releases and price moves since the UK morning, newest first, each with its source and UK time.</p><p class="byline">${C93_EDITOR}</p></section>` +
    `<section>${c97TodayHtml(t)}</section><section><p class="c97note">See also the <a href="/calendar/">macro calendar</a>, the <a href="/gold/dashboard/">gold dashboard</a> and <a href="/brief/">today's brief</a>.</p></section>`;
  return c93Html(req, res, c93Shell({ title: "What changed today | The Dispatch Market", path: "/what-changed/", desc: "Sourced releases and price moves today, in UK time. Not investment advice.", user, body }), "private, max-age=60");
}
const C101B_GATES = {
  "/documents/": ["Documents", "intel", "Your document library: company filings, reports and notes you have saved.", "Documents is for signed-in readers, so your saved files stay in your account."],
  "/portfolio/holdings/": ["Portfolio", "port", "Track your holdings and see how they move.", "Portfolio is for signed-in readers, so your holdings stay in your account."]
};
{
  const R0 = c93Route;
  c93Route = async function (req, res) {
    if (req.method === "GET" || req.method === "HEAD") {
      let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { u0 = null; }
      const p = u0 ? u0.pathname : "", k = p.replace(/\/+$/, "") + "/";
      if (k === "/what-changed/" || Object.prototype.hasOwnProperty.call(C101B_GATES, k)) {
        if (!p.endsWith("/")) { res.writeHead(301, { Location: k + (u0.search || "") }); res.end(); return true; }
        let user = await c96UserOf(req); if (user && req.c96PreviewOn) { req.c94Preview = p; user = null; } if (user) req.c94Signed = true;
        if (k === "/what-changed/") { await c101bWhatChanged(req, res, user); return true; }
        const G = C101B_GATES[k];
        if (user) { res.writeHead(302, { Location: "/?open=" + G[1], "Cache-Control": "no-store" }); res.end(); return true; }
        c98Send(req, res, c98Gate(G[0], k, G[2], null, `${c93Esc(G[3])} <a href="/__auth/login">Sign in</a> to open it, or <a href="/pricing">see plans</a>.`));
        return true;
      }
    }
    // cached static pages (About, Methodology, ...) are built without an account; mark the admin so c93Html can add Admin Console
    try {
      if ((req.method === "GET" || req.method === "HEAD") && typeof C93_PAGES === "object") {
        const p2 = String(req.url || "").split("?")[0];
        if (Object.prototype.hasOwnProperty.call(C93_PAGES, p2) && !req.c96PreviewOn && !/(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String(req.headers.cookie || ""))) {
          const u2 = await c96UserOf(req); if (c96IsAdmin(u2)) req.c101bAdmin = true;
        }
      }
    } catch (e) {}
    return R0.apply(this, arguments);
  };
}
{
  const H0 = c93Html;
  c93Html = function (req, res, html, cache) {
    if (req && req.c101bAdmin && !req.c94Preview && typeof html === "string" && html.indexOf("data-c101b-admin") < 0)
      html = html.split('<li><a href="/settings/">Settings</a></li></ul>').join('<li><a href="/settings/">Settings</a></li><li><a href="/__admin" data-c101b-admin="">Admin Console</a></li></ul>');
    return H0.apply(this, arguments.length > 3 ? [req, res, html, cache] : [req, res, html]);
  };
}
