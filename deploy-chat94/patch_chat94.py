#!/usr/bin/env python3
# chat94: fixes from the chat93 admin QA pass. Exact-count edits; any miss aborts and nothing is written.
# usage: patch_chat94.py server.js app.js index.html
import sys
SRV, APP, IDX = sys.argv[1:4]
def edit(s, old, new, n=1, tag=""):
    c = s.count(old)
    if c != n: sys.exit(f"patch_chat94: {tag}: expected {n} match(es), found {c}")
    return s.replace(old, new)
srv = open(SRV, encoding="utf-8").read(); app = open(APP, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read()
if "chat94" in srv or "chat94" in app or "v=chat94" in idx: sys.exit("patch_chat94: already applied")

# ── server 1: About carries the full funding sentence (Editorial standards already has it in full) ──
srv = edit(srv, "Capital at risk: the value of investments can fall as well as rise.</p>` +\n    `<h2>Get in touch</h2>",
  "Capital at risk: the value of investments can fall as well as rise.</p>` +\n    `<h2>How we are funded</h2><p>We are funded by reader subscriptions. We do not take payment to cover companies or assets.</p>` + // chat94\n    `<h2>Get in touch</h2>", tag="about-funding")

# ── server 2: c93Html learns the admin-only guest preview (banner, no-store, noindex, links keep ?view=guest) ──
srv = edit(srv, '''function c93Html(req, res, html, cache) {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": cache || "public, max-age=600", "X-Content-Type-Options": "nosniff" });''',
'''function c94Short(k) {                                                    // chat94: /MSFT style short company paths
  const m = /^\\/([A-Za-z0-9.\\-]{1,10})$/.exec(k);
  return !!(m && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(m[1].toUpperCase()) >= 0);
}
function c94PreviewHtml(html, exit) {                                      // chat94: admin-only "what guests see" preview
  const keep = (h) => { const k = h.replace(/\\/+$/, "") || "/"; return k === "/" || Object.prototype.hasOwnProperty.call(C93_GUEST, k) || h.indexOf(C93_CSM) === 0 || c94Short(k); };
  html = html.replace(/href="(\\/[^"?#]*)"/g, (m, h) => keep(h) ? `href="${h}?view=guest"` : m);
  const maint = typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON;
  const bar = `<div role="note" data-c94-preview style="background:#1d3557;color:#fff;font:600 13px/1.45 Inter,system-ui,sans-serif;padding:9px 16px;text-align:center"><strong>Guest preview</strong> · only administrators can see this. It shows the page as a signed-out reader sees it${maint ? " once maintenance is switched off. While maintenance is on, guests get the maintenance page" : ""}. <a href="${c93Esc(exit)}" style="color:#fff;text-decoration:underline">Exit preview</a></div>`;
  return html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">').replace(/<body([^>]*)>/, (m) => m + bar);
}
function c93Html(req, res, html, cache) {
  const pv = req && req.c94Preview;
  if (pv) html = c94PreviewHtml(html, pv);
  res.writeHead(200, Object.assign({ "Content-Type": "text/html; charset=utf-8", "Cache-Control": pv ? "private, no-store" : (req && req.c94Signed ? "private, max-age=60" : (cache || "public, max-age=600")), "X-Content-Type-Options": "nosniff" }, pv ? { "X-Robots-Tag": "noindex" } : {}));''', tag="c93Html")

# ── server 3: c93Route: admin ?view=guest preview, /TICKER short routes, redirects keep the query ──
a = srv.index("async function c93Route(req, res) {"); b = srv.index("\n// rt43s: pricing, shared energy spot", a)
if srv.count("async function c93Route(req, res) {") != 1: sys.exit("patch_chat94: c93Route count")
srv = srv[:a] + '''async function c93Route(req, res) {                                        // guest Home and the monitor pages; everything else falls through to the app
  if (req.method !== "GET" && req.method !== "HEAD") return false;
  let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { return false; }
  const p = u0.pathname, q = u0.search || "";
  const gk = p.replace(/\\/+$/, "") || "/";
  const guest = p === "/" || p === "/index.html" || Object.prototype.hasOwnProperty.call(C93_GUEST, gk);
  const short = !guest && c94Short(gk);                                    // chat94: /MSFT renders the company page, /msft and /MSFT/ 301 to /MSFT
  if (!guest && !short && p.indexOf(C93_CSM) !== 0) return false;
  let user = null; try { user = await currentUser(req); } catch (e) { user = null; }
  if (user && u0.searchParams.get("view") === "guest" && typeof isAdminUser === "function" && isAdminUser(user)) { req.c94Preview = p; user = null; } // chat94: admin-only guest preview
  if (user) req.c94Signed = true;                                          // chat94: a page that shows "Your desk" is never sent as public cache
  if (short) {
    const T = gk.slice(1).toUpperCase();
    if (p !== "/" + T) { res.writeHead(301, { Location: "/" + T + q }); res.end(); return true; }
    return (await c93CsmCompany(req, res, user, T)) !== false;
  }
  if (guest) {
    if (user) return false;                                                // signed-in readers keep the app views (by design); admins can add ?view=guest
    if (p === "/" || p === "/index.html") { await c93Home(req, res); return true; }
    if (!p.endsWith("/")) { res.writeHead(301, { Location: gk + "/" + q }); res.end(); return true; }
    await C93_GUEST[gk](req, res); return true;
  }
  const rest = p.slice(C93_CSM.length).replace(/\\/+$/, "");
  if (rest === "") return (await c93CsmIndex(req, res, user)) !== false;
  if (rest === "/method") return (await c93CsmMethod(req, res, user)) !== false;
  const m = /^\\/([A-Za-z0-9.\\-]{1,10})$/.exec(rest);
  if (m && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(m[1].toUpperCase()) >= 0) {
    if (m[1] !== m[1].toUpperCase()) { res.writeHead(301, { Location: C93_CSM + "/" + m[1].toUpperCase() + q }); res.end(); return true; }
    return (await c93CsmCompany(req, res, user, m[1])) !== false;
  }
  return false;
}
''' + srv[b:]

# ── server 4: the admin Console links to the guest preview ──
srv = edit(srv, '<a class=\\"btn sm back\\" href=\\"/\\">&#8592; Back to site</a>',
  '<span><a class=\\"btn sm back\\" href=\\"/?view=guest\\" title=\\"See the site as a signed-out reader (admin only)\\">Guest preview</a> <a class=\\"btn sm back\\" href=\\"/\\">&#8592; Back to site</a></span>', tag="console-link")

# ── server 5: the maintenance page carries the disclaimer too (string only; the gate logic is untouched) ──
srv = edit(srv, "<p>We are making improvements and will be back shortly.</p>' +",
  "<p>We are making improvements and will be back shortly.</p><p style=\"margin-top:1.6rem;font-size:.8rem;color:#8a877f\">Not investment advice. Capital at risk.</p>' + // chat94", tag="maint-disc")

# ── app 1: no "V" avatar placeholders (Research hub author block, SPX 2026 author block) ──
app = edit(app, '<div class="about-avatar" style="width:40px;height:40px;font-size:20px">V</div>', '', tag="avatar40")
app = edit(app, '        <div class="about-avatar" style="width:36px;height:36px;font-size:18px">V</div>\n', '', tag="avatar36")
# ── app 2: the About overlay hides the photo slot instead of a "VP" monogram until /founder.jpg exists ──
app = edit(app, '<span class="rt49-mono" aria-hidden="true">VP</span>', '<span class="rt49-mono" aria-hidden="true"></span>', tag="vp-mono")
app = edit(app, '#aboutOv .rt49-ph.rt49-nophoto .rt49-mono{display:flex}', '#aboutOv .rt49-ph.rt49-nophoto{display:none} /* chat94: no monogram placeholder */', tag="vp-css")
# ── app 3: admin menus link the guest preview ──
app = edit(app, '+ (admin ? `<a role="menuitem" href="/__admin">Admin console</a>` : "")',
  '+ (admin ? `<a role="menuitem" href="/__admin">Admin console</a><a role="menuitem" href="/?view=guest">Guest preview</a>` : "")', tag="menu")
app = edit(app, '${admin ? `<a class="rt17-btn" href="/__admin">Admin console</a>` : ""}',
  '${admin ? `<a class="rt17-btn" href="/__admin">Admin console</a> <a class="rt17-btn" href="/?view=guest">Guest preview</a>` : ""}', tag="rt17")
app = edit(app, '<a class="rt49-btn rt49-btn-gh" href="/__admin">Console</a>',
  '<a class="rt49-btn rt49-btn-gh" href="/__admin">Console</a><a class="rt49-btn rt49-btn-gh" href="/?view=guest">Guest preview</a>', tag="rt49-acct")
app = "// chat94\n" + app if not app.startswith("#!") else app
# ── index: new cache token for app.js ──
idx = edit(idx, '<script defer src="/app.js?v=chat93"></script>', '<script defer src="/app.js?v=chat94"></script>', tag="idx-token")
open(SRV, "w", encoding="utf-8").write(srv); open(APP, "w", encoding="utf-8").write(app); open(IDX, "w", encoding="utf-8").write(idx)
print("patch_chat94: ok")
