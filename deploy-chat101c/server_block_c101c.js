// ── chat101c ── menu sheet. "All sections" (desktop) and "Menu" (below 1280px) open the same full-screen sheet with a solid
// background and a close button: one column, each group a tap-to-expand heading (aria-expanded / aria-controls) in the
// old All sections style; only the group with the current page starts open (on the front page all start closed). Body
// scroll is locked while it is open. "Your desk" / "Sign in" is the primary action at the top; the sign-in note is small
// at the bottom. Market-context rows become cards below 600px, grouped under headings. Every chat101b link is kept;
// Admin Console stays admin-only. Nav and layout only: no routes, data or DDL.
function c101cGroupOf(path) {
  const p = String(path || "/");
  if (p === "/") return -1;                      // the front page starts with every group closed
  let best = -1, bl = 0;
  C101B_GROUPS.forEach(([g, items], gi) => items.forEach(([h]) => {
    if (h === p && bl < 1e6) { best = gi; bl = 1e6; }
    else if (h.length > 1 && h.endsWith("/") && p.indexOf(h) === 0 && h.length > bl) { best = gi; bl = h.length; }
  }));
  return best;
}
const C101C_NOTE = "Some pages are for signed-in readers or members; signed out, they show a sign-in or plans page.";
function c101cLinks(its, path) {
  return its.map(([h, t]) => `<li><a href="${c93Esc(h)}"${h === path ? ' aria-current="page"' : ""}${h === C101B_ADMIN[0] ? ' data-c101b-admin=""' : ""}>${c93Esc(t)}</a></li>`).join("");
}
function c101cItems(g, admin) { const its = C101B_GROUPS.find(x => x[0] === g)[1]; return g === "Account" && admin ? its.concat([C101B_ADMIN]) : its; }
function c101cAcc(user, path, acct, px) {
  const admin = c96IsAdmin(user), cur = c101cGroupOf(path);
  return `<div class="c101c-top">${acct}</div><div class="c101c-acc">` + C101B_GROUPS.map(([g], gi) => {
    const its = c101cItems(g, admin), on = gi === cur, b = `c101c-${px}b${gi}`, l = `c101c-${px}l${gi}`;
    return `<div class="c101c-sec"><h2 class="c101c-hd"><button type="button" class="c101c-btn" id="${b}" aria-expanded="${on}" aria-controls="${l}">` +
      `<span class="c101c-t">${c93Esc(g)}</span><span class="c101c-n"${g === "Account" ? ' data-c101c-acct=""' : ""}><span class="c101c-vh">, </span>${its.length}<span class="c101c-vh"> links</span></span><span class="c101c-ch" aria-hidden="true"></span></button></h2>` +
      `<ul id="${l}" aria-labelledby="${b}"${on ? "" : " hidden"}>${c101cLinks(its, path)}</ul></div>`;
  }).join("") + `</div><p class="c101c-note">${C101C_NOTE}</p>`;
}
function c101cSheet(user, path, acct, px) {
  return `<nav class="c101c-sheet" aria-label="All sections"><div class="c101c-bar"><span class="c101c-title">All sections</span>` +
    `<button type="button" class="c101c-x" aria-label="Close menu"><svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button></div>` +
    `<div class="c101c-in">${c101cAcc(user, path, acct, px)}</div></nav>`;
}
const C101C_CSS =
  // the sheet: full screen, solid, scrolls on its own
  "header.site details>nav.c101c-sheet{position:fixed;top:0;right:0;bottom:0;left:0;width:auto;height:100vh;height:100dvh;max-height:none;margin:0;padding:0;z-index:1000;" +
  "background:var(--paper)!important;color:var(--ink);border:0;border-radius:0;box-shadow:none;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;box-sizing:border-box;-webkit-overflow-scrolling:touch}" +
  "html.c101c-lock,html.c101c-lock body{overflow:hidden!important}" +
  "header.site .c101c-bar{position:sticky;top:0;z-index:1;display:flex;align-items:center;justify-content:space-between;gap:12px;height:60px;padding:0 20px;background:var(--paper);border-bottom:1px solid var(--rule);box-sizing:border-box}" +
  "header.site .c101c-title{font:600 15px/1.2 var(--sans);color:var(--ink)}" +
  "header.site .c101c-x{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;margin:0 -6px 0 0;padding:0;background:transparent;color:var(--ink);border:1px solid var(--rule);border-radius:4px;cursor:pointer}" +
  "header.site .c101c-x:hover{border-color:var(--ink)}header.site .c101c-x:focus-visible{outline:2px solid var(--accent);outline-offset:2px}" +
  "header.site .c101c-in{max-width:640px;margin:0 auto;padding:16px 20px 40px;box-sizing:border-box}" +
  "header.site .c101c-top{margin:0 0 18px}" +
  "header.site .c101c-top a.cta{display:block;box-sizing:border-box;min-height:46px;margin:0;padding:13px 16px;text-align:center;font:600 15px/1.25 var(--sans);border:1px solid var(--ink);border-radius:4px;background:var(--ink);color:var(--paper)}" +
  "header.site .c101c-sec{border-bottom:1px solid var(--rule)}header.site .c101c-sec:first-child{border-top:1px solid var(--rule)}" +
  "header.site .c101c-hd{margin:0;padding:0;font:inherit}" +
  // group labels in the old All sections style: small capitals, muted, spaced
  "header.site .c101c-btn{display:flex;align-items:center;width:100%;min-height:52px;box-sizing:border-box;margin:0;padding:0 2px;background:transparent;border:0;border-radius:0;" +
  "color:var(--muted);font:600 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;text-align:left;cursor:pointer;-webkit-tap-highlight-color:transparent}" +
  "header.site .c101c-btn:hover,header.site .c101c-btn[aria-expanded=true]{color:var(--ink)}" +
  "header.site .c101c-btn:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}" +
  "header.site .c101c-t{flex:1 1 auto}" +
  "header.site .c101c-n{flex:0 0 auto;font:500 12px/1 var(--sans);letter-spacing:0;color:var(--muted);min-width:22px;text-align:right;font-variant-numeric:tabular-nums}" +
  "header.site .c101c-ch{flex:0 0 auto;width:7px;height:7px;margin:-4px 6px 0 14px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);transition:transform .15s ease}" +
  "header.site .c101c-btn[aria-expanded=true] .c101c-ch{transform:rotate(-135deg);margin-top:4px}" +
  "header.site .c101c-acc ul{list-style:none;margin:0 0 10px;padding:0}header.site .c101c-acc ul[hidden]{display:none!important}" +
  "header.site .c101c-acc li{margin:0}" +
  "header.site .c101c-acc a{display:flex;align-items:center;min-height:44px;box-sizing:border-box;margin:0;padding:10px 4px;border:0;border-top:1px solid var(--rule);font:500 15px/1.3 var(--sans);color:var(--ink);white-space:normal}" +
  "header.site .c101c-acc a:hover{color:var(--accent)}" +
  "header.site .c101c-acc a[aria-current=page]{font-weight:600;color:var(--accent);box-shadow:inset 2px 0 0 var(--accent);padding-left:12px}" +
  "header.site .c101c-acc a:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}" +
  "header.site p.c101c-note{margin:18px 0 0;font:400 12px/1.45 var(--sans);color:var(--muted)}" +
  ".c101c-vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}" +
  "@media (prefers-reduced-motion:reduce){header.site .c101c-ch{transition:none}}" +
  // market context: cards below 600px, grouped under headings; desktop table unchanged
  "table.ctx tr.c101c-gh{display:none}" +
  "@media (max-width:359px){header.site .wrap{padding-left:10px;padding-right:10px;gap:6px}header.site .mark{font-size:15px}header.site form.c97tg{margin-left:0}header.site details.menu>summary{padding-left:8px}}" +
  "@media (max-width:599px){table.ctx,table.ctx tbody{display:block;width:100%}" +
  "table.ctx thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}" +
  "table.ctx tr.c101c-gh{display:block;border:0;padding:0}table.ctx tr.c101c-gh th{display:block;padding:16px 2px 6px;border:0;text-align:left;font:600 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}" +
  "table.ctx tbody tr.c101c-gh:first-child th{padding-top:4px}" +
  "table.ctx tbody tr:not(.c101c-gh){display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:'name val' 'name chg' 'src src';column-gap:14px;row-gap:2px;align-items:start;" +
  "margin:0 0 8px;padding:12px 14px;border:1px solid var(--rule);border-radius:6px;background:var(--paper);box-sizing:border-box}" +
  "table.ctx tbody tr:not(.c101c-gh)>td{display:block;padding:0;border:0;min-width:0}" +
  "table.ctx tbody tr>td:nth-child(1){grid-area:name;font:600 15px/1.3 var(--sans);color:var(--ink);overflow-wrap:anywhere}" +
  "table.ctx tbody tr>td:nth-child(1) .msrc{display:none!important}" +
  "table.ctx tbody tr>td:nth-child(2){grid-area:val;text-align:right;font:600 16px/1.3 var(--sans);font-variant-numeric:tabular-nums;white-space:nowrap}" +
  "table.ctx tbody tr>td:nth-child(3){grid-area:chg;text-align:right;font:500 13px/1.3 var(--sans);font-variant-numeric:tabular-nums;white-space:normal}" +
  "table.ctx tbody tr>td:nth-child(3):not(.up):not(.down){color:var(--muted)}" +
  "table.ctx tbody tr>td.src{display:block!important;grid-area:src;margin-top:6px;font:400 12px/1.4 var(--sans);color:var(--muted);overflow-wrap:anywhere}" +
  "table.ctx tbody td .c100-fig{text-align:right;font:inherit}}";
// group headings for the market-context rows (shown below 600px only)
const C101C_JS = "(function(){if(window.__c101c)return;window.__c101c=1;var D=document,H=D.documentElement;" +
  "function sheets(){return Array.prototype.slice.call(D.querySelectorAll('header.site details[open]>nav.c101c-sheet'));}" +
  "function sync(){H.classList.toggle('c101c-lock',sheets().length>0);}" +
  "D.addEventListener('toggle',function(e){var d=e.target;if(!d||!d.matches||!d.matches('header.site details'))return;sync();var n=d.querySelector(':scope>nav.c101c-sheet');if(d.open&&n){var x=n.querySelector('.c101c-x');if(x)try{x.focus({preventScroll:true});}catch(_){}}},true);" +
  "D.addEventListener('click',function(e){var t=e.target&&e.target.closest?e.target:null;if(!t)return;" +
  "var x=t.closest('header.site .c101c-x');if(x){e.preventDefault();var d=x.closest('details');if(d){d.removeAttribute('open');var s=d.querySelector('summary');if(s)s.focus();}sync();return;}" +
  "var b=t.closest('header.site .c101c-btn');if(!b)return;e.preventDefault();" +
  "var l=D.getElementById(b.getAttribute('aria-controls'));var on=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',on?'true':'false');if(l){if(on)l.removeAttribute('hidden');else l.setAttribute('hidden','');}});" +
  "D.addEventListener('keydown',function(e){if(e.key==='Escape'){setTimeout(sync,0);return;}if(e.key!=='Tab')return;var n=sheets()[0];if(!n)return;" +
  "var f=Array.prototype.filter.call(n.querySelectorAll('a[href],button'),function(z){return z.offsetParent!==null;});if(!f.length)return;" +
  "var a=D.activeElement;if(e.shiftKey&&a===f[0]){e.preventDefault();f[f.length-1].focus();}else if(!e.shiftKey&&a===f[f.length-1]){e.preventDefault();f[0].focus();}});" +
  "function grp(t){t=String(t||'');return /^(gold|silver|platinum)/i.test(t)?'M':/crude|wti|brent|natural gas|oil/i.test(t)?'Energy':/bitcoin|ether|crypto|solana/i.test(t)?'Crypto':/yield|treasury|gilt|bank rate|interest/i.test(t)?'Rates':/dollar|pound|euro|yen|sterling/i.test(t)?'Currencies':/s&p|nasdaq|ftse|dow|stocks|equit|vix/i.test(t)?'Stocks':'Other';}" +
  "function head(b){var rows=Array.prototype.filter.call(b.children,function(r){return !r.classList.contains('c101c-gh');});" +
  "Array.prototype.forEach.call(b.querySelectorAll('tr.c101c-gh'),function(r){r.remove();});" +
  "var silver=rows.some(function(r){return /^silver/i.test(r.cells[0]?r.cells[0].firstChild&&r.cells[0].firstChild.textContent:'');});var last=null;" +
  "rows.forEach(function(r){var c=r.cells[0];if(!c)return;var g=grp(c.firstChild?c.firstChild.textContent:c.textContent);if(g==='M')g=silver?'Gold and silver':'Gold';if(g===last)return;last=g;" +
  "var h=D.createElement('tr');h.className='c101c-gh';var th=D.createElement('th');th.colSpan=4;th.scope='colgroup';th.textContent=g;h.appendChild(th);b.insertBefore(h,r);});}" +
  "function watch(b){var mo=new MutationObserver(function(){mo.disconnect();try{head(b);}catch(_){}mo.observe(b,{childList:true});});mo.observe(b,{childList:true});if(b.children.length){try{head(b);}catch(_){}}}" +
  "function init(){Array.prototype.forEach.call(D.querySelectorAll('table.ctx tbody[data-rows]'),watch);}" +
  "if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',init);else init();" +
  "})();";
c93Header = function (path, user) {
  const cur = h => (h === path || (h.length > 1 && h.endsWith("/") && path.indexOf(h) === 0)) ? ' aria-current="page"' : "";
  const links = C93_NAV.map(([h, t]) => `<a href="${h}"${cur(h)}>${t}</a>`).join("");
  const acct = user ? '<a class="cta" href="/dashboard/">Your desk</a>' : '<a class="cta" href="/__auth/login">Sign in</a>';
  return `<header class="site"><style>${C101B_CSS}${C101C_CSS}</style><div class="wrap"><a class="mark" href="/">The Dispatch Market</a>` +
    `<nav class="nav" aria-label="Main">${links}<details class="c101b-all"><summary>All sections</summary>${c101cSheet(user, path, acct, "d")}</details>${acct}</nav>` +
    `<details class="menu"><summary aria-label="Menu: all sections">Menu</summary>${c101cSheet(user, path, acct, "m")}</details></div><script>${C101B_JS}${C101C_JS}</script></header>`;
};
{
  // cached static pages: add Admin Console for the admin here (before the chat101b wrapper, which then leaves the page alone)
  const H1 = c93Html;
  c93Html = function (req, res, html, cache) {
    if (req && req.c101bAdmin && !req.c94Preview && typeof html === "string" && html.indexOf("data-c101b-admin") < 0) {
      html = html.split('<li><a href="/settings/">Settings</a></li></ul>').join('<li><a href="/settings/">Settings</a></li><li><a href="/__admin" data-c101b-admin="">Admin Console</a></li></ul>')
        .split('data-c101c-acct=""><span class="c101c-vh">, </span>1<').join('data-c101c-acct=""><span class="c101c-vh">, </span>2<');
    }
    return H1.apply(this, arguments.length > 3 ? [req, res, html, cache] : [req, res, html]);
  };
}
