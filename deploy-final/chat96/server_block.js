
// ── chat96 ── one bundle on live chat94 (includes the chat95 work). Built and tested, not published.
// Real-yield warm at boot (from chat95).
(function c95Boot() {
  try {
    const t = setTimeout(() => {
      try {
        if (typeof RT53_RY === "object" && RT53_RY && !RT53_RY.v && !RT53_RY.p && typeof rt53RyFetch === "function") {
          RT53_RY.tryAt = Date.now();
          RT53_RY.p = rt53RyFetch().catch(e => { RT53_RY.reason = String((e && e.message) || "error").replace(/[^\w .-]/g, "").slice(0, 80); }).finally(() => { RT53_RY.p = null; });
        }
      } catch (e) { console.warn("c95Boot:", e && e.message); }
    }, 3000);
    if (t && t.unref) t.unref();
  } catch (e) { console.warn("c95Boot:", e && e.message); }
})();
function c96UkParts(ms) { return c93UkParts(ms == null ? Date.now() : ms); }
function c96Hm(ms) { const o = c96UkParts(ms); return (o.hour || "") + ":" + (o.minute || ""); }
function c96UkStamp(ms) { const o = c96UkParts(ms); return (o.weekday ? o.weekday.slice(0, 3) + " " : "") + (o.day || "") + " " + (o.month ? o.month.slice(0, 3) : "") + ", " + (o.hour || "") + ":" + (o.minute || "") + " UK"; }
function c96UkOffset(ms) { const o = c96UkParts(ms), mi = ["January","February","March","April","May","June","July","August","September","October","November","December"].indexOf(o.month); return Date.UTC(Number(o.year), mi, Number(o.day), Number(o.hour), Number(o.minute)) - Math.floor(ms / 60000) * 60000; }
// C1/C2: a 15-second cache in front of the PUBLIC desk and crypto quote routes only (no cookies in the key, nothing cached
// that sets a cookie). The limiter config is unchanged. If the limiter refuses, the last good answer from the past 10 minutes
// is sent, marked served:"last-good" with servedAt and its UK time, so the page can say "as of HH:MM UK, delayed".
// No global json() override: the route's own response is captured from writeHead/end.
const C96_MC = new Map();
const C96_FRESH_MS = 15e3, C96_LASTGOOD_MS = 10 * 60e3, C96_MC_MAX = 200;
function c96Micro(orig, tag) {
  return async function c96MicroRoute(req, res, url) {
    let k = "";
    try {
      const u = url && url.searchParams ? url : new URL(req.url, "http://localhost");
      k = tag + "?" + Array.from(u.searchParams.entries()).sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0).map(p => p[0] + "=" + p[1]).join("&");
    } catch (e) { k = ""; }
    if (!k || (req.method !== "GET" && req.method !== "HEAD")) return orig.apply(this, arguments);
    const hit = C96_MC.get(k), now = Date.now();
    if (hit && now - hit.at < C96_FRESH_MS) {
      res.writeHead(200, Object.assign({}, hit.headers, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Dispatch-Cache": "fresh" }));
      return res.end(req.method === "HEAD" ? undefined : hit.body);
    }
    const wh0 = res.writeHead, e0 = res.end;
    let code = 0, hdrs = null, held = false;
    res.writeHead = function (c, a, b) { code = c; hdrs = Object.assign({}, (typeof a === "string" ? b : a) || {}); if (c === 429 || c === 200) { held = true; return res; } return wh0.apply(res, arguments); };
    res.end = function (chunk, enc, cb) {
      res.writeHead = wh0; res.end = e0;
      if (!held) return e0.apply(res, arguments);
      try {
        const text = chunk != null && typeof chunk !== "function" ? (Buffer.isBuffer(chunk) ? chunk.toString("utf8") : String(chunk)) : "";
        const setsCookie = Object.keys(hdrs || {}).some(h => /^set-cookie$/i.test(h)) || !!(res.getHeader && res.getHeader("Set-Cookie"));
        if (code === 200 && text && text.charCodeAt(0) === 123 && !setsCookie) {
          let j = null; try { j = JSON.parse(text); } catch (e) { j = null; }
          if (j && !j.error && !j.served) {
            if (C96_MC.size >= C96_MC_MAX && !C96_MC.has(k)) C96_MC.delete(C96_MC.keys().next().value);
            const keep = {}; for (const h of Object.keys(hdrs || {})) if (!/^(content-length|set-cookie|date)$/i.test(h)) keep[h] = hdrs[h];
            C96_MC.set(k, { at: Date.now(), body: text, headers: keep });
          }
        } else if (code === 429) {
          const lg = C96_MC.get(k);
          if (lg && Date.now() - lg.at < C96_LASTGOOD_MS) {
            let b = null; try { b = JSON.parse(lg.body); } catch (e) { b = null; }
            if (b && typeof b === "object" && !Array.isArray(b)) {
              b.served = "last-good"; b.servedReason = "rate limit"; b.servedAt = new Date(lg.at).toISOString(); b.servedAtUk = c96Hm(lg.at) + " UK";
              const s = JSON.stringify(b);
              wh0.call(res, 200, Object.assign({}, lg.headers, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Dispatch-Cache": "last-good", "Content-Length": Buffer.byteLength(s) }));
              return e0.call(res, req.method === "HEAD" ? undefined : s);
            }
          }
        }
      } catch (e) { console.warn("c96Micro:", e && e.message); }
      wh0.call(res, code, hdrs || {});
      return e0.call(res, chunk, enc, cb);
    };
    return orig.apply(this, arguments);
  };
}
if (typeof bb10DeskRoute === "function") bb10DeskRoute = c96Micro(bb10DeskRoute, "desk");
if (typeof bb10bCryptoRoute === "function") bb10bCryptoRoute = c96Micro(bb10bCryptoRoute, "crypto");
// Crypto: INJ through Coinbase as well (SHIB, PEPE and ATOM already are); one PEPE id.
try { if (typeof BB10_CB_COINS === "object") { BB10_CB_COINS.INJ = 1; } if (typeof BB10_CG_ID === "object") { BB10_CG_ID["injective-protocol"] = "INJ"; } } catch (e) { console.warn("c96 coins:", e && e.message); }
// Listicle headlines ("5 stocks to buy", "Top 10 ...") are not news for this desk.
const C96_LISTICLE = /^\s*(?:the\s+)?(?:top\s+)?\d{1,2}\s+(?:best\s+|top\s+|cheap\s+|hot\s+|must[- ]own\s+|growth\s+|dividend\s+|ai\s+|penny\s+)*(?:stocks?|shares|etfs?|funds?|cryptos?|coins?|ways|things|reasons|picks|tips|signs|moves)\b|\b(?:stocks?|shares|etfs?)\s+to\s+(?:buy|sell|watch|own)\b|^\s*(?:top|best)\s+\d{1,2}\b/i;
function c96IsListicle(h) { return C96_LISTICLE.test(String(h || "")); }
if (typeof _rt48sHeads === "function") { const c96Heads0 = _rt48sHeads; _rt48sHeads = async function () { const r = await c96Heads0.apply(this, arguments); return Array.isArray(r) ? r.filter(x => !(x && c96IsListicle(x.h))) : r; }; }
// Outlier guard (the INTC case): a one-day share move of 60% or more is treated as a bad print and left out
// (the page then shows no figure rather than a wrong one); 15% or more is flagged largeMove.
if (typeof yahooQuote === "function") {
  const c96Yq0 = yahooQuote;
  yahooQuote = async function () {
    const out = await c96Yq0.apply(this, arguments);
    try {
      for (const k of Object.keys(out || {})) {
        const q = out[k]; if (!q || typeof q !== "object" || /-USD$|=X$|^\^/.test(k)) continue;
        const c = Number(q.c);
        if (isFinite(c) && Math.abs(c) >= 60) { delete out[k]; console.warn("c96 outlier withheld:", k, c.toFixed(1)); }
        else if (isFinite(c) && Math.abs(c) >= 15) out[k] = Object.assign({}, q, { largeMove: true });
      }
    } catch (e) { console.warn("c96 outlier:", e && e.message); }
    return out;
  };
}
// Alphabet and the other company rows: "over five sessions" names the date the five sessions run to.
function c93MonitorRows(rows, full) {
  return rows.map(r => `<tr>${full ? `<td class="n" style="text-align:left">${r.rank}</td>` : ""}<td><a href="${C93_CSM}/${encodeURIComponent(r.ticker)}">${c93Esc(c93Nm(r))}</a>${full ? ` <span class="src">${c93Esc(r.ticker)}</span>` : ""}</td><td>${c93Esc((r.reasons || []).map(c93Reason).filter(Boolean).join("; ").replace(/\b(?:over|in) (?:the last )?(?:5|five) (?:trading )?sessions\b/gi, m => { const d = (r.market && r.market.as_of) || c96LastBar; return d ? "over the five sessions to " + c93Date(d) : m; }))}</td>${full ? `<td class="hide-m">${c93Esc(r.attention ? r.attention.charAt(0).toUpperCase() + r.attention.slice(1) : "")}</td>` : ""}<td class="n">${c93Flag(r.filing_flag && r.filing_flag.overall)}</td></tr>`).join("");
}
let c96LastBar = "";
{ const c96Mon0 = c93Monitor; c93Monitor = async function () { const d = await c96Mon0.apply(this, arguments); try { const m = d && d.as_of && d.as_of.market; if (m && m.last_bar_date_max) c96LastBar = m.last_bar_date_max; } catch (e) {} return d; }; }
// ── chat96 storage: the existing table dispatch_openbb_research_cache (no new tables, no DDL). Keys are namespaced
// (c96:..., byok:...) and stored with expires_at NULL. With no database the features that need storage say so.
let c96SqlImpl = null;                                                    // test hook only
const C96_MEM = new Map();
function c96MemOk() { return process.env.DISPATCH_BYOK_MEMORY_STORE === "1" && !process.env.DATABASE_URL; } // tests only; never with a database
function c96Db() { if (c96SqlImpl) return c96SqlImpl; return (typeof sql === "function" && sql && databaseReady) ? sql : null; }
function c96StoreOk() { return !!c96Db() || c96MemOk(); }
function c96NoStore() { return Object.assign(new Error("storage unavailable"), { code: "C96_NO_STORE" }); }
async function c96Get(k) {
  const db = c96Db();
  if (db) { const r = await db`SELECT value FROM dispatch_openbb_research_cache WHERE cache_key = ${k} LIMIT 1`; return r && r[0] ? r[0].value : null; }
  if (c96MemOk()) return C96_MEM.has(k) ? JSON.parse(C96_MEM.get(k)) : null;
  throw c96NoStore();
}
async function c96Put(k, v, onlyNew) {                                    // onlyNew: returns false when the key already exists
  const db = c96Db(), s = JSON.stringify(v);
  if (db) {
    if (onlyNew) { const r = await db`INSERT INTO dispatch_openbb_research_cache (cache_key, value, expires_at, updated_at) VALUES (${k}, ${s}::jsonb, NULL, NOW()) ON CONFLICT (cache_key) DO NOTHING RETURNING cache_key`; return !!(r && r.length); }
    await db`INSERT INTO dispatch_openbb_research_cache (cache_key, value, expires_at, updated_at) VALUES (${k}, ${s}::jsonb, NULL, NOW()) ON CONFLICT (cache_key) DO UPDATE SET value = EXCLUDED.value, expires_at = NULL, updated_at = NOW()`;
    return true;
  }
  if (c96MemOk()) { if (onlyNew && C96_MEM.has(k)) return false; C96_MEM.set(k, s); return true; }
  throw c96NoStore();
}
async function c96Del(k) {
  const db = c96Db();
  if (db) { await db`DELETE FROM dispatch_openbb_research_cache WHERE cache_key = ${k}`; return; }
  if (c96MemOk()) { C96_MEM.delete(k); return; }
  throw c96NoStore();
}
async function c96DelPrefix(prefix) {
  const db = c96Db(), like = prefix.replace(/[\\%_]/g, m => "\\" + m) + "%";
  if (db) { await db`DELETE FROM dispatch_openbb_research_cache WHERE cache_key LIKE ${like}`; return; }
  if (c96MemOk()) { for (const k of Array.from(C96_MEM.keys())) if (k.indexOf(prefix) === 0) C96_MEM.delete(k); return; }
  throw c96NoStore();
}
// Optional display name from the register form (stored beside the account, not in the users table, so no DDL).
function c96CleanName(v) { const s = String(v || "").replace(/[\u0000-\u001f\u007f<>]/g, "").replace(/\s+/g, " ").trim(); return s.slice(0, 60); }
async function c96SaveName(userId, name) { const n = c96CleanName(name); if (!userId || !n || !c96StoreOk()) return; try { await c96Put("c96:name:" + userId, { name: n, at: new Date().toISOString() }); } catch (e) { console.warn("c96 name save:", (e && e.code) || "error"); } }
async function c96GetName(userId) { if (!userId || !c96StoreOk()) return ""; try { const v = await c96Get("c96:name:" + userId); return v && v.name ? String(v.name) : ""; } catch (e) { return ""; } }
async function c96AccountPurge(userId) {                                  // account deletion: the reader's AI keys and name go too
  if (!userId || !c96StoreOk()) return;
  await c96DelPrefix("byok:" + userId + ":");
  await c96Del("c96:name:" + userId);
}

// ── Free daily-brief sign-up. Stored only (nothing is sent yet): key c96:brief-signup:<sha256 of the address>. ──
const C96_SU_LIMIT = new FixedWindowRateLimiter({ limit: 5, windowMs: 10 * 60e3, maxKeys: 10000 });
const C96_EMAIL_RE = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~\-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?)+$/;
const C96_SU_PRIVACY = `We use your email only to send the free brief, and we will not share it. Every email will have a one-click unsubscribe. See the <a href="/privacy">privacy notice</a>.`;
const C96_SU_FROM = ["home", "brief", "footer", "research", "404", "maintenance", "page", "pricing"];
function c96SignupForm(where, compact) {
  const from = C96_SU_FROM.indexOf(where) >= 0 ? where : "page";
  return `<form class="c96su${compact ? " c96su-c" : ""}" method="post" action="/free-brief" aria-label="Get the free daily brief by email">` +
    (compact ? "" : `<div class="kicker">Free daily brief</div><h2 style="margin:8px 0 6px">Get the brief by email, free</h2><p style="margin:0 0 10px;max-width:620px">A short read on gold, the dollar, real yields, oil and risk appetite, with the source of every figure. Sending starts soon; sign up now and you'll get the first one.</p>`) +
    `<div class="c96su-row"><label for="c96su-${from}" class="c96vh">Email address</label><input id="c96su-${from}" type="email" name="email" required maxlength="254" autocomplete="email" placeholder="you@example.com"><input type="hidden" name="from" value="${from}"><span class="c96hp" aria-hidden="true"><label>Leave this empty <input type="text" name="website" tabindex="-1" autocomplete="off"></label></span><button type="submit">Get the free brief</button></div>` +
    `<p class="src" style="margin:8px 0 0">${C96_SU_PRIVACY}</p></form>`;
}
const C96_CSS = ".c96su{margin:0}.c96su-row{display:flex;gap:8px;flex-wrap:wrap;max-width:560px}.c96su input[type=email]{flex:1 1 240px;min-width:0;font:15px var(--sans);padding:9px 10px;border:1px solid #8c877d;border-radius:2px;background:#fff;color:var(--ink)}.c96su button{font:600 14px var(--sans);padding:9px 14px;border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:2px;cursor:pointer}.c96hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}.c96vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}" +
  "footer.site .c96su{margin:0 0 18px;padding-bottom:18px;border-bottom:1px solid var(--rule)}.c96ok{border-left:3px solid var(--up);padding:8px 12px;background:#fff}.c96warn{border-left:3px solid var(--amber);padding:8px 12px;background:#fff}.c96wall{border:1px solid var(--rule);background:#fff;padding:16px;margin-top:14px}.c96pv li{margin:6px 0}.c96sample{border:1px dashed #8c877d;background:#fff;padding:14px 16px;margin:14px 0}.c96sample .kicker{color:var(--amber)}";
function c96Ip(req) { const f = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim(); return f || (req.socket && req.socket.remoteAddress) || "?"; }
async function c96ReadForm(req, max) {
  let size = 0; const chunks = [];
  for await (const c of req) { size += c.length; if (size > max) { const e = new Error("too large"); e.code = "C96_TOO_LARGE"; throw e; } chunks.push(c); }
  return new URLSearchParams(Buffer.concat(chunks).toString("utf8"));
}
function c96Redirect(res, loc, code) { res.writeHead(code || 303, { Location: loc, "Cache-Control": "no-store" }); return res.end(); }
async function c96SignupPost(req, res) {
  if (!sameOriginMutation(req)) return c96Redirect(res, "/free-brief/?s=invalid");
  const ct = String(req.headers["content-type"] || "").toLowerCase();
  let f;
  try { f = ct.indexOf("application/x-www-form-urlencoded") === 0 ? await c96ReadForm(req, 4096) : new URLSearchParams(); } catch (e) { return c96Redirect(res, "/free-brief/?s=invalid"); }
  if (f.get("website")) return c96Redirect(res, "/free-brief/?s=ok");    // honeypot: look successful, store nothing
  if (!C96_SU_LIMIT.allow("su:" + c96Ip(req))) return c96Redirect(res, "/free-brief/?s=busy");
  const email = String(f.get("email") || "").trim().toLowerCase();
  if (email.length > 254 || !C96_EMAIL_RE.test(email)) return c96Redirect(res, "/free-brief/?s=invalid");
  const from = C96_SU_FROM.indexOf(String(f.get("from") || "")) >= 0 ? String(f.get("from")) : "page";
  if (!c96StoreOk()) return c96Redirect(res, "/free-brief/?s=later");
  try {
    const h = crypto.createHash("sha256").update(email).digest("hex");
    const fresh = await c96Put("c96:brief-signup:" + h, { email, from, at: new Date().toISOString(), status: "pending", list: "free-daily-brief" }, true);
    return c96Redirect(res, "/free-brief/?s=" + (fresh ? "ok" : "dup"));
  } catch (e) { console.warn("c96 signup:", (e && e.code) || "error"); return c96Redirect(res, "/free-brief/?s=later"); }
}
const C96_SU_MSG = {
  ok: ["c96ok", "You're on the list. We'll email the free daily brief to that address once sending starts. Nothing else is sent."],
  dup: ["c96ok", "That address is already on the list. You don't need to do anything else."],
  invalid: ["c96warn", "That email address doesn't look right. Please check it and try again."],
  busy: ["c96warn", "Too many sign-ups from this connection in the last few minutes. Please try again shortly."],
  later: ["c96warn", "We couldn't save your sign-up just now. Nothing was stored. Please try again later."]
};
async function c96FreeBriefPage(req, res, user) {
  let s = ""; try { s = new URL(req.url, "http://x").searchParams.get("s") || ""; } catch (e) { s = ""; }
  const m = C96_SU_MSG[s];
  const note = m ? `<p class="${m[0]}" role="status">${c93Esc(m[1])}</p>` : "";
  const maint = typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON && !req.c96Admin;
  if (maint) { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "Content-Security-Policy": C96_MAINT_CSP, "X-Robots-Tag": "noindex" }); return res.end(req.method === "HEAD" ? undefined : c96MaintHtml(m)); }
  const body = `<section class="prose"><div class="kicker">Free daily brief</div><h1>The free daily brief</h1><p class="lede">A short read on gold, the dollar, real yields, oil and risk appetite, each figure with its source and UK time. Free, by email.</p>${note}</section>` +
    `<section>${c96SignupForm("page", true)}<p class="note">What you get: the headline of the day's <a href="/brief/">Brief</a>, the five figures behind it and a link to read more. Built by rules from public data, not written by AI. Not investment advice. Capital at risk.</p></section>`;
  return c93Html(req, res, c93Shell({ title: "Free daily brief | The Dispatch Market", path: "/free-brief/", desc: "Get The Dispatch Market's free daily brief on gold and macro by email. Not investment advice.", user, body }), "private, no-store");
}

// ── Shell, nav and footer ──
C93_NAV.splice(C93_NAV.findIndex(x => x[0] === "/methodology"), 0, ["/pricing", "Plans"]);
C93_NAV.push(["/free-brief/", "Free brief"]);
function c93Shell(o) {
  const left = o.strip != null ? o.strip : `${c93Esc(c93UkDay(Date.now()))} \u00b7 ${c93Esc(c93Sessions(Date.now()).text)}`;
  return c93Head(o.title, o.path, o.desc, `<style>${C96_CSS}</style>` + (o.extraHead || "")) + `<body>${c93Header(o.path, o.user)}<div class="strip"><div class="wrap"><span>${left}</span><span class="disc">${C93_DISC}</span></div></div><main class="wrap">${o.body}</main>${c93Footer(o.user)}${o.tail || ""}</body></html>`;
}
function c93Footer(user) {
  return `<footer class="site"><div class="wrap">${user ? "" : `<div data-c96-footsu>${c96SignupForm("footer", false)}</div>`}<div class="links"><a href="/about">About</a><a href="/pricing">Plans</a><a href="/editorial-standards">Editorial standards</a><a href="/methodology">Methodology</a><a href="/corrections">Corrections</a><a href="mailto:${C93_CONTACT}">Contact: ${C93_CONTACT}</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></div>` +
    `<p><span class="disc">${C93_DISC}</span> The Dispatch Market publishes research and education, not personal recommendations. Prices come from free public feeds and are delayed; each figure shows its source and time.</p>` +
    `<p>Published by Vraj Patel, London \u00b7 \u00a9 ${new Date().getUTCFullYear()} The Dispatch Market \u00b7 thedispatch.uk \u00b7 <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a></p></div></footer>`;
}
// Guest preview (admins): a 30-minute HttpOnly cookie, so links need no ?view=guest. Exit clears it.
function c94PreviewHtml(html, exit) {
  const maint = typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON;
  const bar = `<div role="note" data-c94-preview style="background:#1d3557;color:#fff;font:600 13px/1.45 Inter,system-ui,sans-serif;padding:9px 16px;text-align:center"><strong>Guest preview</strong> \u00b7 only administrators can see this. It shows the site as a signed-out reader sees it${maint ? " once maintenance is switched off. While maintenance is on, guests get the maintenance page" : ""}. It ends after 30 minutes. <a href="?view=exit" style="color:#fff;text-decoration:underline">Exit preview</a></div>`;
  return html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">').replace(/<body([^>]*)>/, (m) => m + bar);
}
function c93Html(req, res, html, cache) {
  const pv = req && req.c94Preview;
  if (pv) html = c94PreviewHtml(html, pv);
  if (req && req.c94Signed && !pv) {                                      // signed-in: account header, no guest sign-up
    html = html.replace('<a class="cta" href="/__auth/login">Sign in</a>', '<a class="cta" href="/dashboard/">Your desk</a>').replace(/<div data-c96-footsu>[\s\S]*?<\/form><\/div>/, "");
  }
  res.writeHead(200, Object.assign({ "Content-Type": "text/html; charset=utf-8", "Cache-Control": pv ? "private, no-store" : (req && req.c94Signed ? "private, max-age=60" : (cache || "public, max-age=600")), "X-Content-Type-Options": "nosniff" }, pv ? { "X-Robots-Tag": "noindex" } : {}));
  return res.end(req.method === "HEAD" ? undefined : html);
}
C93_PAGES["/about"][0] = "About";

// ── Brief, Gold, Research and the two homes ──
function c96Byline(pub, upd) { return `Published ${c96Hm(pub)} UK, ${c93Esc(c93UkDay(pub))}${upd ? ` \u00b7 Updated <span id="c96upd">${c93Esc(c96Hm(upd))} UK</span>` : ""} \u00b7 ${C93_EDITOR}`; }
function c96BriefPub(now) {
  const o = c93UkParts(now), mi = ["January","February","March","April","May","June","July","August","September","October","November","December"].indexOf(o.month);
  const six = Date.UTC(Number(o.year), mi, Number(o.day), 6, 0) - c96UkOffset(now);
  return Number(o.hour) >= 6 ? six : six - 864e5;
}
const C96_SCHEDULE = "A new Brief is published at 06:00 UK every day, and its figures refresh whenever you open the page. It is built by fixed rules from the figures shown; it is not written by AI.";
function c96BriefLabel(now) { const h = Number(c93UkParts(now).hour); return h >= 5 && h < 12 ? "Morning brief" : h >= 12 && h < 17 ? "Afternoon brief" : "Evening brief"; }
function c93Brief(req, res, user) {
  const now = Date.now(), pub = c96BriefPub(now);
  const body = `<section><div class="kicker">${c96BriefLabel(now)} \u00b7 ${c93Esc(c93UkDay(now))}</div><h1 id="c93bh">Today's brief</h1><p class="dek" id="c93bp"></p><p class="note" id="c96wc" hidden></p><p class="byline">${c96Byline(pub, now)} \u00b7 <span id="c93bt"></span></p></section>` +
    `<section id="c96pv" hidden><h2>In today's brief</h2><ul class="c96pv" id="c96pvl"></ul><div class="c96wall"><p style="margin:0 0 8px"><strong>The rest of today's brief is for members.</strong> Members get the full brief with themes, catalysts and the companies in the news, plus an audio version.</p>${C93_MEMBERS}</div></section>` +
    `<section><div class="grid" data-auto><div data-need hidden><h2>The figures behind it</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds; where a market is shut we show its last close.</p>${c93CtxTable("gold,gold_gbp_oz,dxy,tnx,ry,wti,spx,vix,btc")}</div>${c93RegimeCard()}</div></section>` +
    `<section>${user ? "" : c96SignupForm("brief", false)}<p class="note" style="margin-top:12px">${C96_SCHEDULE} It describes conditions; it is not a recommendation.</p></section>`;
  return c93Guest(req, res, { title: "Today's brief", path: "/brief/", desc: "A short daily read on gold, the dollar, real yields, oil and risk appetite, with sources. Not investment advice.", body, user });
}
function c93Gold(req, res, user) {
  const s = c93SesClass(Date.now());
  const body = `<section><div class="kicker">Gold</div><h1>Gold and what moves it</h1><p class="dek">Gold has no yield, so it tends to compete with what cash and bonds pay after inflation, and it is priced in dollars. These are the measures we watch, with their sources.</p><p class="byline">${C93_EDITOR}</p></section>` +
    `<section><div class="grid" data-auto><div data-need hidden><h2>The gold dashboard, in brief</h2><p class="note" style="margin:0 0 12px">Gold is shown on one basis: the spot price per troy ounce from gold-api.com, a free reference feed, in US dollars and in pounds. ${c93Esc(s.metals.replace(/^Gold and silver futures: /, "Silver futures: "))}.</p>${c93CtxTable("gold,gold_gbp_oz,gold_gbp_g,silver,dxy,ry,tnx")}</div>${c93RegimeCard()}</div></section>` +
    `<section class="prose"><h2>How to read these figures</h2><p><strong>Gold in pounds.</strong> The dollar spot price divided by the pound's dollar rate at the time shown. A gram is 1/31.1035 of a troy ounce. It is a reference price, not a dealer's buying or selling price.</p><p><strong>Real yield.</strong> The 10-year US Treasury yield after expected inflation. When it rises, holding gold costs more in income given up, and gold has often struggled; when it falls, the reverse.</p><p><strong>The dollar.</strong> Gold is priced in US dollars, so a stronger dollar makes it dearer for buyers using other currencies.</p><p><strong>Risk appetite.</strong> In stressed markets some investors move towards gold; our gauge summarises five market inputs (<a href="/methodology#regime">how it works</a>).</p><p class="note">These are long-run tendencies, not rules, and they break down for long stretches. Not investment advice.</p></section>` +
    `<section>${c93Card("The full Gold Dashboard", `<p style="margin:0 0 8px">Levels, sessions and volatility, updated through the day, are part of membership.</p>${C93_MEMBERS}`)}</section>`;
  return c93Guest(req, res, { title: "Gold", path: "/gold/", desc: "Gold spot in dollars and pounds per ounce and per gram, the dollar and real yields, with sources and UK times. Not investment advice.", body, user });
}
function c93Guest(req, res, o) {
  const ses = c93Sessions(Date.now());
  const html = c93Shell({ title: o.title + " | The Dispatch Market", path: o.path, desc: o.desc, body: o.body, user: o.user, tail: `<script>${C96_LIVE_JS}</script>` }).replace("<body>", `<body data-wk="${ses.weekend ? 1 : 0}">`);
  return c93Html(req, res, html, "private, max-age=60");
}
async function c93ResearchHub(req, res, user) {
  let mon = null; try { mon = await c93Monitor("radar", null, 3); } catch (e) { mon = null; }
  const top = mon && Array.isArray(mon.ranking) ? mon.ranking.slice(0, 3) : [];
  const body = `<section><div class="kicker">Research</div><h1>Research</h1><p class="dek">Long-form research built from official filings and public data, with the method published alongside.</p><p class="byline">${C93_EDITOR}</p></section>` +
    (top.length ? `<section><div class="kicker">Monitor \u00b7 updated daily</div><h2 style="margin-top:8px"><a href="${C93_CSM}">Capital Sustainability Monitor</a></h2><p style="max-width:720px;margin:0 0 14px">Is AI spending outrunning the cash that pays for it? Five checks on ${mon.total || 19} US-listed companies, from their SEC filings.</p><table><thead><tr><th>Company</th><th>What stands out</th><th class="n">Filing flag</th></tr></thead><tbody>${c93MonitorRows(top, false)}</tbody></table><p class="src" style="margin-top:12px">${c93Esc(c93CsmSource(mon))} <a href="${C93_CSM}/method">Method</a> \u00b7 <a href="${C93_CSM}">All ${mon.total || 19} companies</a></p></section>` : "") +
    `<section><h2>Also from the desk</h2><table><tbody><tr><td><a href="/brief/">Today's brief</a></td><td>A short daily read on gold, the dollar, real yields, oil and risk appetite.</td></tr><tr><td><a href="/gold/">Gold</a></td><td>The measures that move gold, with sources, and how to read them.</td></tr><tr><td><a href="/methodology">Methodology</a></td><td>Where every figure comes from and what we do when a feed fails.</td></tr></tbody></table><div style="margin-top:14px">${C93_MEMBERS}</div></section>` +
    (user ? "" : `<section>${c96SignupForm("research", false)}</section>`);
  return c93Html(req, res, c93Shell({ title: "Research | The Dispatch Market", path: "/research/", desc: "Research from The Dispatch Market, including the Capital Sustainability Monitor. Not investment advice.", user, body }), "private, max-age=120");
}
async function c96MonHtml() {
  let mon = null; try { mon = await c93Monitor("radar", null, 3); } catch (e) { mon = null; }
  const top = mon && Array.isArray(mon.ranking) ? mon.ranking.slice(0, 3) : [];
  return top.length ? `<section><div class="kicker">Research</div><h2 style="margin-top:8px">Capital Sustainability Monitor</h2><p style="max-width:720px;margin:0 0 14px">Is AI spending outrunning the cash that pays for it? We rank ${mon.total || 19} US-listed companies on capital spending against operating cash flow, debt and margins, using their SEC filings.</p><table><thead><tr><th>Company</th><th>What stands out</th><th class="n">Filing flag</th></tr></thead><tbody>${c93MonitorRows(top, false)}</tbody></table><p class="src" style="margin-top:12px">${c93Esc(c93CsmSource(mon))} <a href="${C93_CSM}/method">Method</a> \u00b7 <a href="${C93_CSM}">All ${mon.total || 19} companies</a></p></section>` : "";
}
function c96BriefCard(kick) { return `<div class="card" id="c93brief" hidden><div class="kicker" id="c93bk">${kick}</div><h3 style="margin-top:8px" id="c93bh"></h3><p style="margin:0 0 8px" id="c93bp"></p><p class="note" id="c96rx" hidden></p><p class="src"><span id="c93bt"></span> \u00b7 <a href="/brief/">Read the brief</a></p></div>`; }
async function c93Home(req, res) {
  const now = Date.now(), ses = c93Sessions(now), monHtml = await c96MonHtml();
  const body = `<section><div class="kicker">Independent gold and macro research</div><h1>Know what matters before gold moves.</h1><p class="dek">${C93_MISSION} A daily read on the dollar, real yields, oil and risk appetite, and what they mean for gold. Prices are delayed.</p><p class="byline">${C93_EDITOR} \u00b7 <a href="/about">About the desk</a> \u00b7 <a href="/methodology">How we work</a></p></section>` +
    `<section>${c96SignupForm("home", false)}</section>` +
    `<section id="c93top"><div class="grid" data-auto><div data-need hidden><h2>Market context</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds, delayed. Where a market is shut we show its last close.</p>${c93CtxTable("gold,gold_gbp_oz,dxy,tnx,ry,btc,wti")}</div>` +
    c96BriefCard("Today's brief") + `</div></section>` + monHtml;
  const html = c93Shell({ title: "The Dispatch Market | Independent gold and macro research", path: "/", desc: C93_MISSION + " " + C93_EDITOR + ".", body, tail: `<script>${C96_LIVE_JS}</script>` }).replace("<body>", `<body data-wk="${ses.weekend ? 1 : 0}">`);
  return c93Html(req, res, html, "private, max-age=60");
}
// Signed-in home: the brief and market context first, the rankings lower, and the desk one click away.
async function c96Home(req, res, user) {
  const now = Date.now(), ses = c93Sessions(now), monHtml = await c96MonHtml();
  let name = ""; try { name = await c96GetName(user && user.id); } catch (e) { name = ""; }
  const body = `<section><div class="kicker">${c96BriefLabel(now)} \u00b7 ${c93Esc(c93UkDay(now))}</div><h1 style="font-size:36px">${name ? "Good to see you, " + c93Esc(name.split(" ")[0]) + "." : "Your daily read"}</h1><p class="dek">Today's brief and the figures behind it. Your watchlists, alerts and the full desk are on <a href="/dashboard/">your desk</a>.</p></section>` +
    `<section id="c93top"><div class="grid" data-auto>` + c96BriefCard("Today's brief") + `<div data-need hidden><h2>Market context</h2><p class="note" style="margin:0 0 12px">Latest levels from free public feeds, delayed.</p>${c93CtxTable("gold,gold_gbp_oz,dxy,tnx,ry,wti,btc")}</div></div></section>` +
    `<section><div class="grid" data-auto><div>${c93RegimeCard()}</div><div class="card"><div class="kicker">Your desk</div><p style="margin:8px 0">Watchlists, alerts, the Gold Dashboard and Ask live on the desk.</p><p style="margin:0"><a href="/dashboard/">Open your desk</a> \u00b7 <a href="/settings/">Settings</a></p></div></div></section>` + monHtml;
  const html = c93Shell({ title: "Your daily read | The Dispatch Market", path: "/", desc: C93_MISSION, user, body, tail: `<script>${C96_LIVE_JS}</script>` }).replace("<body>", `<body data-wk="${ses.weekend ? 1 : 0}">`);
  return c93Html(req, res, html, "private, no-store");
}
C93_GUEST["/gold"] = c93Gold; C93_GUEST["/brief"] = c93Brief; C93_GUEST["/research"] = c93ResearchHub;
// Public gold spot (gold-api.com) for the pages above, through the same 15-second cache.
async function c96GoldSpotRoute(req, res) {
  let q = null; try { q = typeof fetchGoldProxy === "function" ? await fetchGoldProxy() : null; } catch (e) { console.warn("c96 gold spot:", e && e.message); q = null; }
  let sq = q; try { if (q && typeof bb8qSpotQuote === "function") sq = bb8qSpotQuote(q); } catch (e) { sq = q; }
  if (!sq || !(Number(sq.p) > 0)) return json(res, 200, { available: false, source: "gold-api.com spot" });
  const ms = Number(sq.ts) > 0 ? Number(sq.ts) * 1000 : Date.now();
  return json(res, 200, { available: true, price: Number(sq.p), changePct: sq.changeAvailable ? Number(sq.c) : null, unit: "US$ per troy ounce", source: "gold-api.com spot", stale: !!sq.stale, asOf: new Date(ms).toISOString(), asOfUk: c96UkStamp(ms) });
}
const c96GoldMicro = c96Micro(c96GoldSpotRoute, "gold");
// ── chat96 BYOK: readers' own AI keys ─────────────────────────────────────────────────────────────────────────────
// Storage: existing table dispatch_openbb_research_cache, key byok:<userId>:<provider>, encrypted payload only (no DDL).
// Encryption: AES-256-GCM, random 12-byte IV per record, auth tag stored, AAD = the cache key. Master key: env
// DISPATCH_BYOK_MASTER_KEY (32 bytes, base64). Missing or invalid -> every key endpoint refuses (503 BYOK_UNAVAILABLE);
// there is no weaker fallback key. Keys are never returned to the browser, logged, or put in errors; provider error
// bodies are never echoed. Provider URLs are constants below; nothing user-supplied reaches a URL or a model name.
const C96_BYOK = {
  openai: { label: "OpenAI", re: /^sk-[A-Za-z0-9_\-]{20,200}$/, model: "gpt-4o-mini", envModel: "DISPATCH_BYOK_OPENAI_MODEL" },
  anthropic: { label: "Anthropic", re: /^sk-ant-[A-Za-z0-9_\-]{20,200}$/, model: "claude-haiku-4-5", envModel: "DISPATCH_BYOK_ANTHROPIC_MODEL" },
  xai: { label: "xAI Grok", re: /^xai-[A-Za-z0-9]{20,200}$/, model: "grok-3-mini", envModel: "DISPATCH_BYOK_XAI_MODEL" },
  gemini: { label: "Google Gemini", re: /^AIza[0-9A-Za-z_\-]{30,60}$/, model: "gemini-2.5-flash", envModel: "DISPATCH_BYOK_GEMINI_MODEL" },
  perplexity: { label: "Perplexity", re: /^pplx-[A-Za-z0-9]{20,200}$/, model: "sonar", envModel: "DISPATCH_BYOK_PERPLEXITY_MODEL" }
};
const C96_BYOK_ORDER = ["openai", "anthropic", "xai", "gemini", "perplexity"];
const C96_BYOK_MAXLEN = 300;
const C96_ALS = new (require("async_hooks").AsyncLocalStorage)();
let c96MkCache = { src: null, key: null };
function c96MasterKey() {
  const s = String(process.env.DISPATCH_BYOK_MASTER_KEY || "").trim();
  if (c96MkCache.src === s) return c96MkCache.key;
  let k = null;
  if (s && /^[A-Za-z0-9+/_\-]+={0,2}$/.test(s)) { try { const b = Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64"); if (b.length === 32) k = b; } catch (e) { k = null; } }
  c96MkCache = { src: s, key: k };
  return k;
}
function c96ByokAvailable() { return !!c96MasterKey() && c96StoreOk(); }
function c96ByokKey(userId, provider) { return "byok:" + userId + ":" + provider; }
function c96Encrypt(plain, aad) {
  const mk = c96MasterKey(); if (!mk) throw Object.assign(new Error("BYOK unavailable"), { code: "BYOK_UNAVAILABLE" });
  const iv = crypto.randomBytes(12), c = crypto.createCipheriv("aes-256-gcm", mk, iv);
  c.setAAD(Buffer.from(aad, "utf8"));
  const ct = Buffer.concat([c.update(Buffer.from(plain, "utf8")), c.final()]);
  return { v: 1, alg: "aes-256-gcm", iv: iv.toString("base64"), tag: c.getAuthTag().toString("base64"), ct: ct.toString("base64") };
}
function c96Decrypt(rec, aad) {
  const mk = c96MasterKey(); if (!mk) throw Object.assign(new Error("BYOK unavailable"), { code: "BYOK_UNAVAILABLE" });
  if (!rec || rec.v !== 1 || rec.alg !== "aes-256-gcm") throw Object.assign(new Error("bad record"), { code: "BYOK_RECORD" });
  const iv = Buffer.from(String(rec.iv || ""), "base64"), tag = Buffer.from(String(rec.tag || ""), "base64");
  if (iv.length !== 12 || tag.length !== 16) throw Object.assign(new Error("bad record"), { code: "BYOK_RECORD" });
  const d = crypto.createDecipheriv("aes-256-gcm", mk, iv); d.setAAD(Buffer.from(aad, "utf8")); d.setAuthTag(tag);
  return Buffer.concat([d.update(Buffer.from(String(rec.ct || ""), "base64")), d.final()]).toString("utf8");
}
function c96Meta(provider, rec) { return { provider, label: C96_BYOK[provider].label, last4: String(rec.last4 || "").slice(-4), addedAt: rec.addedAt || null, status: rec.status || "untested", checkedAt: rec.checkedAt || null }; }
async function c96ByokList(userId) {                                      // metadata only: provider, label, last 4, dates, last test result
  if (!userId || !c96StoreOk()) return [];
  const out = [];
  for (const p of C96_BYOK_ORDER) { let rec = null; try { rec = await c96Get(c96ByokKey(userId, p)); } catch (e) { rec = null; } if (rec && rec.ct) out.push(c96Meta(p, rec)); }
  return out;
}
async function c96ByokSave(userId, provider, key) {
  const k = c96ByokKey(userId, provider), now = new Date().toISOString();
  const rec = Object.assign(c96Encrypt(key, k), { provider, last4: key.slice(-4), addedAt: now, status: "untested", checkedAt: null });
  await c96Put(k, rec);
  return c96Meta(provider, rec);
}
async function c96ByokLoad(userId, provider) { const k = c96ByokKey(userId, provider); const rec = await c96Get(k); if (!rec || !rec.ct) return null; return { rec, key: c96Decrypt(rec, k) }; }
async function c96ByokMark(userId, provider, status) { const k = c96ByokKey(userId, provider); const rec = await c96Get(k); if (!rec || !rec.ct) return; rec.status = status; rec.checkedAt = new Date().toISOString(); await c96Put(k, rec); }
async function c96ByokDelete(userId, provider) { await c96Del(c96ByokKey(userId, provider)); }
function c96Redact(s) { return String(s == null ? "" : s).replace(/(sk-ant-|sk-|xai-|pplx-|AIza)[A-Za-z0-9_\-]{6,}/g, "$1[redacted]").slice(0, 300); }
// One cheap, fixed call per provider: list models (no tokens), or a 1-token request where there is no list endpoint.
function c96TestReq(provider, key) {
  switch (provider) {
    case "openai": return ["https://api.openai.com/v1/models", { method: "GET", headers: { Authorization: "Bearer " + key } }];
    case "anthropic": return ["https://api.anthropic.com/v1/models?limit=1", { method: "GET", headers: { "x-api-key": key, "anthropic-version": "2023-06-01" } }];
    case "xai": return ["https://api.x.ai/v1/models", { method: "GET", headers: { Authorization: "Bearer " + key } }];
    case "gemini": return ["https://generativelanguage.googleapis.com/v1beta/models?pageSize=1", { method: "GET", headers: { "x-goog-api-key": key } }];
    case "perplexity": return ["https://api.perplexity.ai/chat/completions", { method: "POST", headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" }, body: JSON.stringify({ model: "sonar", max_tokens: 1, messages: [{ role: "user", content: "Hi" }] }) }];
  }
  return null;
}
async function c96Fetch(url, opts, ms) {
  const c = new AbortController(), t = setTimeout(() => { try { c.abort(); } catch (e) {} }, ms || 15000);
  try { return await fetch(url, Object.assign({}, opts, { signal: c.signal, redirect: "error" })); } finally { clearTimeout(t); }
}
async function c96Peek(r) { try { return (await r.text()).slice(0, 4000); } catch (e) { return ""; } }
// Map a provider response to ok / invalid / nocredit / error. The body is read only to tell "no credit" from "bad key"; it is never returned or logged.
async function c96Classify(provider, r) {
  if (r.ok) return "ok";
  const s = r.status, b = (await c96Peek(r)).toLowerCase();
  if (s === 401) return "invalid";
  if (provider === "gemini" && s === 400 && /api_key_invalid|api key not valid|invalid api key/.test(b)) return "invalid";
  if (s === 400 && /invalid[_ ]api[_ ]key|incorrect api key|invalid x-api-key|authentication/.test(b)) return "invalid";
  if (s === 402 || s === 403 || s === 429 || /credit|quota|billing|insufficient|balance|exhausted|payment/.test(b)) return "nocredit";
  return "error";
}
const C96_STATUS_TEXT = { ok: "OK", invalid: "Invalid key", nocredit: "No credit/permission", error: "Provider error" };
async function c96ByokTest(provider, key) {
  const rq = c96TestReq(provider, key); if (!rq) return "error";
  try { const r = await c96Fetch(rq[0], rq[1], 15000); const st = await c96Classify(provider, r); if (st !== "ok") console.warn("BYOK test:", provider, r.status); return st; }
  catch (e) { console.warn("BYOK test:", provider, "network"); return "error"; }
}
function c96Model(provider) { const m = String(process.env[C96_BYOK[provider].envModel] || "").trim(); return /^[a-z0-9.\-]{1,60}$/.test(m) ? m : C96_BYOK[provider].model; }
async function c96ByokComplete(provider, key, options) {
  const model = c96Model(provider);
  const raw = typeof asAiMessages === "function" ? asAiMessages(options && options.messages) : (Array.isArray(options && options.messages) ? options.messages : []);
  const messages = raw.map(m => ({ role: m.role === "assistant" ? "assistant" : "user", content: String(m.content || "") }));
  const system = typeof clipped === "function" ? clipped(options && options.system, 14000) : String((options && options.system) || "").slice(0, 14000);
  const tokens = Math.max(300, Math.min(Number(options && options.maxTokens) || 1000, 2400));
  const temperature = typeof (options && options.temperature) === "number" ? options.temperature : 0.2;
  let url, req;
  if (provider === "anthropic") {
    url = "https://api.anthropic.com/v1/messages";
    req = { method: "POST", headers: { "x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json" }, body: JSON.stringify({ model, system, max_tokens: tokens, temperature, messages }) };
  } else if (provider === "gemini") {
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + encodeURIComponent(model) + ":generateContent";
    req = { method: "POST", headers: { "x-goog-api-key": key, "Content-Type": "application/json" }, body: JSON.stringify({ systemInstruction: { parts: [{ text: system }] }, contents: messages.map(m => ({ role: m.role === "assistant" ? "model" : "user", parts: [{ text: m.content }] })), generationConfig: { maxOutputTokens: tokens, temperature } }) };
  } else {
    url = provider === "openai" ? "https://api.openai.com/v1/chat/completions" : provider === "xai" ? "https://api.x.ai/v1/chat/completions" : "https://api.perplexity.ai/chat/completions";
    const b = { model, messages: [{ role: "system", content: system }].concat(messages), temperature };
    if (provider === "openai") b.max_completion_tokens = tokens; else b.max_tokens = tokens;
    req = { method: "POST", headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" }, body: JSON.stringify(b) };
  }
  let r;
  try { r = await c96Fetch(url, req, typeof AI_TIMEOUT_MS === "number" ? AI_TIMEOUT_MS : 25000); }
  catch (e) { console.warn("BYOK chat:", provider, "network"); throw c96ByokErr(provider, "error", 0); }
  if (!r.ok) { const st = await c96Classify(provider, r); console.warn("BYOK chat:", provider, r.status); throw c96ByokErr(provider, st, r.status); }
  let d; try { d = await r.json(); } catch (e) { throw c96ByokErr(provider, "error", 502); }
  let text = "";
  if (provider === "anthropic") text = (Array.isArray(d && d.content) ? d.content : []).filter(x => x && x.type === "text").map(x => x.text).join("");
  else if (provider === "gemini") { const c0 = d && Array.isArray(d.candidates) && d.candidates[0]; text = c0 && c0.content && Array.isArray(c0.content.parts) ? c0.content.parts.map(x => (x && x.text) || "").join("") : ""; }
  else text = (d && d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content) || "";
  if (typeof text !== "string" || !text.trim()) throw c96ByokErr(provider, "empty", 502);
  return { text: String(text), model, provider: C96_BYOK[provider].label + " (your key)" };
}
function c96ByokMsg(provider, st) {
  const L = C96_BYOK[provider] ? C96_BYOK[provider].label : "AI";
  if (st === "invalid") return "Your " + L + " key was rejected (invalid key). Update it in Settings.";
  if (st === "nocredit") return "Your " + L + " key was rejected (no credit or no permission). Check your " + L + " account, or update the key in Settings.";
  if (st === "empty") return "Your " + L + " key worked but the answer came back empty. Please try again.";
  if (st === "rate") return "You've asked a lot of questions with your own key in the last ten minutes. Please wait a few minutes.";
  return "Your " + L + " key couldn't be used just now (the provider didn't answer). Please try again, or check the key in Settings.";
}
function c96ByokErr(provider, st, status) {
  const code = { invalid: "BYOK_INVALID", nocredit: "BYOK_NO_CREDIT", empty: "BYOK_EMPTY", error: "BYOK_ERROR" }[st] || "BYOK_ERROR";
  const msg = c96ByokMsg(provider, st);
  const e = typeof AiRequestError === "function" ? new AiRequestError(424, msg, code) : Object.assign(new Error(msg), { status: 424, code });
  const store = C96_ALS.getStore(); if (store && !store.err) store.err = { provider, st, code, message: msg };
  return e;
}
function c96Guard() { const s = C96_ALS.getStore(); return s && s.byok ? s : null; }
function c96GuardErr() { return typeof AiRequestError === "function" ? new AiRequestError(503, "Site AI is not used for this request.", "BYOK_GUARD") : new Error("BYOK guard"); }
// Wraps (by assignment): with a reader's key in context, the attempt list is that key only, so nothing falls back to the site's keys.
if (typeof hasPremiumAccess === "function") { const c96Prem0 = hasPremiumAccess; hasPremiumAccess = function (user) { const g = c96Guard(); if (g && user && String(user.id) === String(g.userId)) return true; return c96Prem0.apply(this, arguments); }; }
if (typeof bb3bAttempts === "function") { const c96Att0 = bb3bAttempts; bb3bAttempts = function () { if (c96Guard()) return [{ kind: "openai-slot", id: "byok" }]; return c96Att0.apply(this, arguments); }; }
if (typeof bb3bRunOpenAiSlot === "function") {
  const c96Slot0 = bb3bRunOpenAiSlot;
  bb3bRunOpenAiSlot = async function (attempt, options) {
    const g = c96Guard();
    if (!g) return c96Slot0.apply(this, arguments);
    if (!attempt || attempt.id !== "byok") throw c96GuardErr();
    const result = await c96ByokComplete(g.byok.provider, g.byok.key, options || {});
    g.used = true;
    if (options && typeof options.validate === "function") return Object.assign({}, result, { validated: options.validate(result.text) });
    return result;
  };
}
if (typeof bb3bRunXaiKey === "function") { const c96Xai0 = bb3bRunXaiKey; bb3bRunXaiKey = async function () { if (c96Guard()) throw c96GuardErr(); return c96Xai0.apply(this, arguments); }; }
if (typeof aiProviderFetch === "function") { const c96Apf0 = aiProviderFetch; aiProviderFetch = async function () { if (c96Guard()) throw c96GuardErr(); return c96Apf0.apply(this, arguments); }; }
if (typeof generateWithAiProvider === "function") { const c96Gwp0 = generateWithAiProvider; generateWithAiProvider = async function () { if (c96Guard()) throw c96GuardErr(); return c96Gwp0.apply(this, arguments); }; }
if (typeof bb2OpenAi === "function") { const c96B2o = bb2OpenAi; bb2OpenAi = async function () { if (c96Guard()) throw c96GuardErr(); return c96B2o.apply(this, arguments); }; }
if (typeof bb2Gemini === "function") { const c96B2g = bb2Gemini; bb2Gemini = async function () { if (c96Guard()) throw c96GuardErr(); return c96B2g.apply(this, arguments); }; }
if (typeof _bb4dOne === "function") { const c96B4 = _bb4dOne; _bb4dOne = async function () { if (c96Guard()) throw c96GuardErr(); return c96B4.apply(this, arguments); }; }

// Endpoints. All need a signed-in user. Mutations: same-origin (Sec-Fetch-Site and Origin host), JSON content type and an
// X-Dispatch-CSRF token = HMAC(master-key-derived key, session cookie), compared in constant time. Per-user limits.
const C96_LIM_TEST = new FixedWindowRateLimiter({ limit: 5, windowMs: 10 * 60e3, maxKeys: 5000 });
const C96_LIM_EDIT = new FixedWindowRateLimiter({ limit: 20, windowMs: 10 * 60e3, maxKeys: 5000 });
const C96_LIM_ASK = new FixedWindowRateLimiter({ limit: 20, windowMs: 10 * 60e3, maxKeys: 5000 });
function c96Csrf(req) {
  const mk = c96MasterKey(), sess = cookieValue(req, "dispatch_session") || "";
  if (!mk || !sess) return "";
  const k = crypto.createHmac("sha256", mk).update("dispatch-byok-csrf-v1").digest();
  return crypto.createHmac("sha256", k).update("csrf:" + sess).digest("base64url");
}
function c96CsrfOk(req) {
  const want = c96Csrf(req), got = String(req.headers["x-dispatch-csrf"] || "");
  if (!want || !got || got.length !== want.length) return false;
  try { return crypto.timingSafeEqual(Buffer.from(got), Buffer.from(want)); } catch (e) { return false; }
}
function c96J(res, status, body) { return json(res, status, body, { "Cache-Control": "no-store", "Pragma": "no-cache" }); }
async function c96ByokRoute(req, res, p, user) {
  if (!user) return c96J(res, 401, { error: "Sign in to manage your AI keys.", code: "AUTH" });
  const providers = C96_BYOK_ORDER.map(id => ({ id, label: C96_BYOK[id].label }));
  if (!c96ByokAvailable()) return c96J(res, 503, { available: false, providers, keys: [], error: "Your AI keys are not available yet.", code: "BYOK_UNAVAILABLE" });
  const uid = String(user.id);
  if (p === "/api/byok/keys" && req.method === "GET") return c96J(res, 200, { available: true, providers, keys: await c96ByokList(uid), csrf: c96Csrf(req) });
  const mutation = (req.method === "POST" && (p === "/api/byok/keys" || p === "/api/byok/test" || p === "/api/byok/delete")) || (req.method === "DELETE" && (p === "/api/byok/keys" || p === "/api/byok/delete"));
  if (!mutation) { res.setHeader("Allow", p === "/api/byok/keys" ? "GET, POST, DELETE" : "POST"); return c96J(res, 405, { error: "Method not allowed." }); }
  if (!sameOriginMutation(req) || !rt17SameOriginJson(req) || !c96CsrfOk(req)) return c96J(res, 403, { error: "This request was blocked as a possible cross-site request. Reload Settings and try again.", code: "CSRF" });
  let body = {};
  try { body = await rt17ReadJson(req, 2048); } catch (e) { return c96J(res, 400, { error: "Bad request.", code: "BAD_JSON" }); }
  const provider = String((body && body.provider) || "");
  if (!Object.prototype.hasOwnProperty.call(C96_BYOK, provider)) return c96J(res, 400, { error: "Choose a provider.", code: "PROVIDER" });
  if (p === "/api/byok/test") {
    if (!C96_LIM_TEST.allow("t:" + uid)) return c96J(res, 429, { error: "You can test keys 5 times in 10 minutes. Please wait a few minutes.", code: "RATE" });
    let got = null; try { got = await c96ByokLoad(uid, provider); } catch (e) { console.warn("BYOK load:", provider, (e && e.code) || "error"); return c96J(res, 500, { error: "We couldn't read that key. Delete it and add it again.", code: "BYOK_RECORD" }); }
    if (!got) return c96J(res, 404, { error: "No " + C96_BYOK[provider].label + " key saved.", code: "NONE" });
    const st = await c96ByokTest(provider, got.key);
    got = null;
    try { await c96ByokMark(uid, provider, st); } catch (e) { console.warn("BYOK mark:", provider, (e && e.code) || "error"); }
    return c96J(res, 200, { provider, result: st, resultText: C96_STATUS_TEXT[st], keys: await c96ByokList(uid) });
  }
  if (!C96_LIM_EDIT.allow("e:" + uid)) return c96J(res, 429, { error: "Too many key changes in 10 minutes. Please wait a few minutes.", code: "RATE" });
  if (p === "/api/byok/delete" || req.method === "DELETE") {
    try { await c96ByokDelete(uid, provider); } catch (e) { console.warn("BYOK delete:", provider, (e && e.code) || "error"); return c96J(res, 500, { error: "We couldn't delete that key just now. Please try again.", code: "STORE" }); }
    return c96J(res, 200, { ok: true, deleted: provider, keys: await c96ByokList(uid) });
  }
  const key = typeof (body && body.key) === "string" ? body.key.trim() : "";
  if (!key || key.length > C96_BYOK_MAXLEN || !C96_BYOK[provider].re.test(key)) return c96J(res, 400, { error: "That doesn't look like " + (provider === "openai" ? "an " : "a ") + C96_BYOK[provider].label + " key. Check you copied all of it.", code: "FORMAT" });
  try { const meta = await c96ByokSave(uid, provider, key); return c96J(res, 200, { ok: true, saved: meta, keys: await c96ByokList(uid) }); }
  catch (e) { console.warn("BYOK save:", provider, (e && e.code) || "error"); return c96J(res, 500, { error: "We couldn't save that key just now. Nothing was stored.", code: "STORE" }); }
}
// Which key a reader's Ask uses: one that last tested OK, else an untested one, else any (so the reader sees why it fails).
async function c96ByokPick(uid) {
  if (!c96ByokAvailable()) return null;
  const list = await c96ByokList(uid); if (!list.length) return null;
  const rank = s => s === "ok" ? 0 : s === "untested" ? 1 : 2;
  list.sort((a, b) => rank(a.status) - rank(b.status) || C96_BYOK_ORDER.indexOf(a.provider) - C96_BYOK_ORDER.indexOf(b.provider));
  const got = await c96ByokLoad(uid, list[0].provider); if (!got) return null;
  return { provider: list[0].provider, key: got.key };
}
async function c96HasByok(uid) { try { return c96ByokAvailable() && (await c96ByokList(uid)).length > 0; } catch (e) { return false; } }
// POST /api/chat from a signed-in reader with a saved key. Premium readers can send X-Dispatch-AI-Keys: site to use the site's AI instead.
async function c96ByokAsk(req, res, user, next) {
  const prem = (function () { try { return !!(user && (user.tier === "premium" || isAdminUser(user))); } catch (e) { return false; } })();
  const wantSite = String(req.headers["x-dispatch-ai-keys"] || "").toLowerCase() === "site";
  if (prem && wantSite) return next();
  let pick = null; try { pick = await c96ByokPick(String(user.id)); } catch (e) { console.warn("BYOK pick:", (e && e.code) || "error"); pick = null; }
  if (!pick) return next();
  const L = C96_BYOK[pick.provider].label, label = { provider: pick.provider, label: "Using your " + L + " key" };
  if (!C96_LIM_ASK.allow("a:" + user.id)) return c96J(res, 429, Object.assign({ error: c96ByokMsg(pick.provider, "rate"), code: "BYOK_RATE", byok: label }, prem ? { siteKeysOffer: true } : {}));
  delete req.headers["x-dispatch-stream"];                                // the JSON path runs through bb3bGenerateAi, where the key is applied
  req.headers.accept = "application/json";
  const store = { byok: { provider: pick.provider, key: pick.key }, userId: String(user.id), prem };
  pick = null;
  const e0 = res.end, wh0 = res.writeHead, w0 = res.write;
  let code = 0, hdrs = null, flushed = false;
  const flush = () => { if (flushed || !code) return; flushed = true; wh0.call(res, code, hdrs || {}); };
  res.writeHead = function (c, a, b) { code = c; hdrs = Object.assign({}, (typeof a === "string" ? b : a) || {}); return res; };
  res.write = function () { flush(); return w0.apply(res, arguments); };
  res.end = function (chunk, enc, cb) {
    res.end = e0; res.writeHead = wh0; res.write = w0;
    if (typeof chunk === "function") { cb = chunk; chunk = undefined; enc = undefined; }
    if (typeof enc === "function") { cb = enc; enc = undefined; }
    const st = code || res.statusCode || 200;
    if (!flushed) {
      try {
        const text = chunk != null ? (Buffer.isBuffer(chunk) ? chunk.toString("utf8") : String(chunk)) : "";
        let out = null, outCode = st;
        if (store.err && st !== 200) {
          out = Object.assign({ error: store.err.message, code: store.err.code, byok: label }, store.prem ? { siteKeysOffer: true } : {});
          outCode = 424;
        } else if (text && text.charCodeAt(0) === 123) {
          const j = JSON.parse(text);
          if (j && typeof j === "object" && !Array.isArray(j)) { j.byok = label; if (typeof j.error === "string") j.error = c96Redact(j.error); out = j; }
        }
        if (out) {
          const s = JSON.stringify(out), h = {};
          for (const k of Object.keys(hdrs || {})) if (!/^content-length$/i.test(k)) h[k] = hdrs[k];
          try { res.removeHeader("Content-Length"); } catch (e) {}
          h["Content-Type"] = "application/json; charset=utf-8"; h["Cache-Control"] = "no-store"; h["Content-Length"] = Buffer.byteLength(s);
          flushed = true; wh0.call(res, outCode, h);
          return e0.call(res, s, "utf8", cb);
        }
      } catch (e) { console.warn("BYOK ask wrap:", e && e.message); }
      flush();
    }
    return chunk === undefined ? e0.call(res, cb) : e0.call(res, chunk, enc, cb);
  };
  return C96_ALS.run(store, () => next());
}

// ── chat96: routing, preview, maintenance, headers, sitemap, 404, pricing, methodology ──
// currentUser once per request (several layers ask; the session lookup is the same).
if (typeof currentUser === "function") {
  const c96Cu0 = currentUser, c96CuW = new WeakMap();
  currentUser = function (req) {
    if (!req || typeof req !== "object" || arguments.length > 1) return c96Cu0.apply(this, arguments);
    if (c96CuW.has(req)) return c96CuW.get(req);
    const pr = Promise.resolve(c96Cu0.apply(this, arguments));
    c96CuW.set(req, pr); pr.catch(() => c96CuW.delete(req));
    return pr;
  };
}
async function c96UserOf(req) { try { return await currentUser(req); } catch (e) { return null; } }
function c96IsAdmin(u) { try { return !!(u && typeof isAdminUser === "function" && isAdminUser(u)); } catch (e) { return false; } }

// c93Route: preview comes from the admin's preview cookie (set in c96Inner); a signed-in reader on bare "/" gets the calm home.
async function c93Route(req, res) {
  if (req.method !== "GET" && req.method !== "HEAD") return false;
  let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { return false; }
  const p = u0.pathname, q = u0.search || "";
  const gk = p.replace(/\/+$/, "") || "/";
  if (p === "/" && u0.searchParams.has("settings")) return false; // chat96: /settings/ opens the app's Settings page for everyone
  const guest = p === "/" || p === "/index.html" || Object.prototype.hasOwnProperty.call(C93_GUEST, gk);
  const short = !guest && c94Short(gk);
  if (!guest && !short && p.indexOf(C93_CSM) !== 0) return false;
  let user = await c96UserOf(req);
  if (user && req.c96PreviewOn) { req.c94Preview = p; user = null; }
  if (user) req.c94Signed = true;
  if (short) {
    const T = gk.slice(1).toUpperCase();
    if (p !== "/" + T) { res.writeHead(301, { Location: "/" + T + q }); res.end(); return true; }
    return (await c93CsmCompany(req, res, user, T)) !== false;
  }
  if (guest) {
    if (user) { if (p === "/" && !q) { await c96Home(req, res, user); return true; } return false; } // /?settings=1 etc. stay with the app
    if (p === "/" || p === "/index.html") { await c93Home(req, res); return true; }
    if (!p.endsWith("/")) { res.writeHead(301, { Location: gk + "/" + q }); res.end(); return true; }
    await C93_GUEST[gk](req, res); return true;
  }
  const rest = p.slice(C93_CSM.length).replace(/\/+$/, "");
  if (rest === "") return (await c93CsmIndex(req, res, user)) !== false;
  if (rest === "/method") return (await c93CsmMethod(req, res, user)) !== false;
  const m = /^\/([A-Za-z0-9.\-]{1,10})$/.exec(rest);
  if (m && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(m[1].toUpperCase()) >= 0) {
    if (m[1] !== m[1].toUpperCase()) { res.writeHead(301, { Location: C93_CSM + "/" + m[1].toUpperCase() + q }); res.end(); return true; }
    return (await c93CsmCompany(req, res, user, m[1])) !== false;
  }
  return false;
}

// ── Maintenance page: white, favicon, contact, disclaimer, free-brief sign-up. "/" stays 200 for the Promote health check. ──
const C96_FAV = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231f3a5f'/%3E%3Cpath d='M9 8h7a8 8 0 010 16H9z' fill='none' stroke='%23fff' stroke-width='3'/%3E%3C/svg%3E";
const C96_MAINT_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'";
function c96MaintHtml(m) {
  const note = m && m[1] ? `<p class="${m[0] === "c96warn" ? "c96warn" : "c96ok"}" role="status">${c93Esc(m[1])}</p>` : "";
  return `<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="theme-color" content="#ffffff"><title>Under maintenance | The Dispatch Market</title><link rel="icon" href="${C96_FAV}">` +
    `<style>:root{--ink:#1b1b1b;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}html,body{margin:0}body{background:#fff;color:#1b1b1b;font:16px/1.6 var(--sans);padding:40px 20px}main{max-width:34rem;margin:0 auto}.k{color:#1f3a5f;letter-spacing:.2em;font-size:.78rem;font-weight:700;text-transform:uppercase;margin:0 0 1rem}h1{font:400 2.2rem/1.2 Georgia,"Times New Roman",serif;margin:0 0 .8rem}h2{font:600 1.1rem/1.3 Georgia,serif;margin:2rem 0 .6rem}p{margin:0 0 .8rem;color:#45443f}a{color:#1f3a5f}.src{font-size:.8rem;color:#66655f}.d{margin-top:2rem;font-size:.85rem;color:#45443f}.o{margin-top:2.4rem;font-size:.75rem}.o a{color:#66655f}.c96ok{background:#eef5ee;border-left:3px solid #2e6b3a;padding:8px 12px;color:#1b1b1b}.c96warn{background:#fbf1e6;border-left:3px solid #9a5a12;padding:8px 12px;color:#1b1b1b}${C96_CSS}</style></head>` +
    `<body><main><p class="k">The Dispatch Market</p><h1>Under maintenance</h1><p>We are making improvements and will be back shortly.</p>${note}` +
    `<h2>Get the free daily brief</h2><p>A short read on gold, the dollar, real yields, oil and risk appetite, with the source of every figure.</p>${c96SignupForm("maintenance", true)}` +
    `<p class="d">Contact: <a href="mailto:${C93_CONTACT}">${C93_CONTACT}</a><br>Edited by Vraj Patel, London. Not investment advice. Capital at risk.</p>` +
    `<p class="o"><a href="/__auth/login" rel="nofollow">Owner sign in</a></p></main></body></html>`;
}
var c96MaintSend0 = bb10iSend;
bb10iSend = function c96MaintSend(req, res, p) {
  var api = p !== null && (p === "/api" || p.indexOf("/api/") === 0);
  if (api) return c96MaintSend0(req, res, p);                              // API JSON body and 503 unchanged
  var raw = String(req.url || "").split(/[?#]/)[0];
  var root = p === "/" && (req.method === "GET" || req.method === "HEAD") && (raw === "/" || /^https?:\/\/[^\/]*\/?$/i.test(raw));
  var body = c96MaintHtml();
  var hd = { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex", "Content-Length": Buffer.byteLength(body), "X-Content-Type-Options": "nosniff", "Content-Security-Policy": C96_MAINT_CSP };
  if (!root) hd["Retry-After"] = BB10I_RETRY_AFTER;
  res.writeHead(root ? 200 : 503, hd);
  res.end(req.method === "HEAD" ? undefined : body);
};

// ── 404 and sitemap ──
var c96NotFound0 = renderPublicNotFound;
renderPublicNotFound = function (pathname) {
  const h = c96NotFound0.apply(this, arguments);
  const css = `<style>:root{--ink:#1b1b1b;--sans:system-ui,-apple-system,"Segoe UI",Arial,sans-serif}.c96nf{max-width:620px;margin:28px auto;padding:0 20px}.src{font-size:12px;color:#66655f}${C96_CSS}</style>`;
  return h.replace("</head>", css + "</head>").replace("</body>", `<section class="c96nf">${c96SignupForm("404", false)}</section></body>`);
};
var c96Sitemap0 = renderPublicSitemap;
renderPublicSitemap = async function () {
  let x = await c96Sitemap0.apply(this, arguments);
  const drop = new Set((typeof PUBLIC_APP_ROUTE_DEFINITIONS !== "undefined" ? PUBLIC_APP_ROUTE_DEFINITIONS : []).map(r => r.path));
  x = x.replace(/[ \t]*<url><loc>([^<]*)<\/loc>[\s\S]*?<\/url>\r?\n?/g, (m, loc) => drop.has(String(loc).slice(PUBLIC_ORIGIN.length)) ? "" : m);
  const add = ["/markets/", "/signals/", "/news/", "/research/", "/pricing", "/free-brief/", "/privacy", "/terms"].filter(u => x.indexOf(`<loc>${PUBLIC_ORIGIN}${u}</loc>`) < 0);
  return x.replace("</urlset>", add.map(u => `  <url><loc>${PUBLIC_ORIGIN}${u}</loc><changefreq>${/news|markets|signals/.test(u) ? "daily" : "monthly"}</changefreq><priority>0.6</priority></url>\n`).join("") + "</urlset>");
};

// ── Auth page titles carry the brand; reset with no token says so and offers a new link ──
var c96Page0 = page;
page = function (res, title, content) {
  const t = String(title == null ? "" : title);
  return c96Page0.call(this, res, /Dispatch Market/.test(t) ? t : (t ? t + " | The Dispatch Market" : "The Dispatch Market"), content);
};
const C96_RESET_NOTOKEN = `<h1>Reset link expired or invalid</h1><p>This password reset link has expired, has been used, or is incomplete. Enter your email and we will send a new one.</p><form method="post" action="/__auth/recover"><label for="c96r-email">Email address</label><input id="c96r-email" name="email" type="email" autocomplete="email" required><button>Send a new link</button></form><p class="muted"><a href="/__auth/login">Back to sign in</a></p>`;

// ── Pricing: plain English, two plans, a labelled premium sample, BYOK. No Stripe change: the same /__auth/subscribe checkout. ──
const C96_FREE = ["The daily Brief and the Market context table, with the source and UK time of every figure", "Gold in dollars and pounds, Markets, Signals and News", "The Capital Sustainability Monitor and Research", "Watchlists and price alerts", "Ask, if you add your own AI key in Settings (your provider bills you)"];
const C96_PREM = ["Everything in Free", "The weekly Gold Playbook: scenarios and what would change the view", "The full daily Brief, not just the preview", "Company statements and institutional holders", "Ask, using our AI keys (or yours, if you prefer)", "Cancel any time from Settings, Manage billing"];
const C96_SAMPLE = `<section class="c93c" id="c96sample" style="margin-top:22px"><div class="kicker">Premium sample \u00b7 an excerpt from a past Gold Playbook, for illustration</div><h3 style="margin:8px 0">Scenario: real yields fall while the dollar holds</h3><p>What we watch: the US 10-year real yield (US Treasury via FRED) and the US Dollar Index. In past episodes when the real yield fell by a quarter of a point or more in a month with the dollar flat, gold in US dollars has tended to firm, but not every time. What would change the view: a rebound in the real yield above its level at the start of the month.</p><p class="note" style="margin:0">Sample text only, not a current view. Not investment advice. Capital at risk.</p></section>`;
async function rt43sPricing(req, res) {
  let user = await c96UserOf(req);
  if (user && req.c96PreviewOn) { req.c94Preview = "/pricing"; user = null; }
  if (user) req.c94Signed = true;
  const admin = c96IsAdmin(user);
  const prem = !!user && (user.tier === "premium" || admin);
  const li = a => a.map(x => `<li>${c93Esc(x)}</li>`).join("");
  const cta = prem
    ? `<p class="note">${admin ? "Admin account: Premium is included and there is no Stripe subscription." : `Premium is active. Manage billing from <a href="/settings/">Settings</a>.`}</p>`
    : `<p>${user ? "" : `<a class="cta" href="/__auth/register">Create a free account</a> \u00b7 `}<a href="/__auth/subscribe">Get Premium, \u00a315 a month</a></p>`;
  const body = `<section class="prose"><div class="kicker">Plans</div><h1>Plans and pricing</h1><p class="lede">Two plans. Prices in pounds, billed monthly through Stripe. Cancel any time.</p></section>` +
    `<section><div class="c93g"><section class="c93c"><h2>Free</h2><p class="c93pr">\u00a30</p><ul>${li(C96_FREE)}</ul></section><section class="c93c c93cp"><h2>Premium</h2><p class="c93pr">\u00a315 a month</p><ul>${li(C96_PREM)}</ul></section></div>${cta}` +
    `<h2 style="margin-top:26px">Using your own AI key</h2><p>Any signed-in reader can add their own key from OpenAI, Anthropic, xAI (Grok), Google (Gemini) or Perplexity in <a href="/settings/">Settings</a>. Your questions to Ask then go to that provider with your key, and your provider bills you directly. We store the key encrypted, never show it back to you in full, and delete it when you delete it or close your account. Ask always says which key it used.</p>` +
    C96_SAMPLE + (user ? "" : `<section style="margin-top:26px">${c96SignupForm("pricing", false)}</section>`) +
    `<p class="note" style="margin-top:20px">Research and education, not personal recommendations. Not investment advice. Capital at risk.</p></section>`;
  const html = c93Shell({ title: "Plans and pricing | The Dispatch Market", path: "/pricing", desc: "The Dispatch Market: Free (\u00a30) and Premium (\u00a315 a month). Not investment advice.", user, body });
  return c93Html(req, res, html, "public, max-age=600");
}

// ── Methodology matches the site: real feed names, one gold basis, the gauge's bands, the Brief's schedule, AI and BYOK ──
(function c96Method() {
  const d = C93_PAGES["/methodology"]; if (!d || typeof d[2] !== "function") return;
  const f0 = d[2];
  d[2] = function () {
    let h = f0.apply(this, arguments);
    const rep = (a, b) => { if (h.indexOf(a) >= 0) h = h.replace(a, b); else console.warn("c96 methodology: text not found:", a.slice(0, 40)); };
    rep(`<tr><td>Gold spot price</td><td>gold-api.com (free feed)</td><td>Checked about every 30 seconds while the page is open</td></tr>`,
      `<tr><td>Gold spot price (US$ per troy ounce)</td><td>gold-api.com (free feed). This is the one gold price on our public pages.</td><td>Checked about every 30 seconds while the page is open</td></tr>` +
      `<tr><td>Gold in pounds (per troy ounce and per gram)</td><td>Derived: the gold-api.com spot price divided by the pound-dollar rate; per gram is per ounce divided by 31.1035</td><td>As fresh as the older of the two inputs; both are shown with their times</td></tr>`);
    rep(`<td>Yahoo Finance (free, unofficial), with Finnhub and Twelve Data as backups</td>`,
      `<td>Delayed exchange data through Yahoo Finance (free, unofficial), with Finnhub and Twelve Data as backups. Each row names the feed it came from. Futures (gold on the desk, silver, oil, gas) are front-month contracts on COMEX, NYMEX or ICE.</td>`);
    rep(`<h2>Scores, flags and scenarios</h2>`,
      `<h2 id="regime">The risk-appetite gauge</h2><p>The gauge is a score from 0 to 100 built by fixed rules from five free inputs: the VIX volatility index, the day's S&amp;P 500 move, the US Dollar Index, the oil price and the day's Bitcoin move. A score below 45 reads as risk-off, 45 to 59 as mixed, and 60 and above as risk-on. So "risk-off (37 of 100)" means the inputs together look cautious today. It describes conditions; it is not a forecast or a recommendation.</p>` +
      `<h2 id="brief">The daily Brief</h2><p>${C96_SCHEDULE} Each Brief shows when it was published and when its figures were last updated, in UK time, and a line on what changed since the previous close.</p>` +
      `<h2>Scores, flags and scenarios</h2>`);
    rep(`<h2>Use of AI</h2><p>The Ask assistant and some drafts of the daily Brief use an AI model working from the figures above. These are labelled. Rules-based briefs are labelled as built from today's data.</p>`,
      `<h2 id="ai">Use of AI</h2><p>The public Brief, the gauge and the market tables are built by fixed rules from the figures above, not written by AI. Ask, our research assistant for signed-in readers, uses an AI model, and its answers are labelled as AI and must cite the figures and sources they use; if it cannot source a figure, it says so rather than guessing.</p>` +
      `<h2 id="byok">Your own AI key</h2><p>Signed-in readers can add their own key from OpenAI, Anthropic, xAI (Grok), Google (Gemini) or Perplexity in Settings. Ask then uses that key for that reader's questions only and says so ("Using your OpenAI key"). Keys are encrypted on our server (AES-256-GCM), never sent back to the browser, never written to logs, and deleted with the account. A key test makes one small request to the provider's official address. If your key fails, Ask tells you why; free accounts never fall back to our keys, and Premium accounts are asked before we use ours.</p>`);
    return h;
  };
  try { c93PageCache.delete("/methodology"); } catch (e) {}
})();

// ── Outermost wrapper: headers, canonical redirects, auth HEAD/CSP, manifest, the free-brief sign-up (works in maintenance) ──
const C96_SEC = { "Referrer-Policy": "strict-origin-when-cross-origin", "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(self \"https://checkout.stripe.com\")", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "SAMEORIGIN" };
const C96_AUTH_CSP = "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; form-action 'self' https://checkout.stripe.com https://billing.stripe.com; frame-ancestors 'none'; base-uri 'none'; object-src 'none'";
var c96FrontPrev = handle;
async function c96Front(req, res) {
  try { for (const k in C96_SEC) if (!res.getHeader(k)) res.setHeader(k, C96_SEC[k]); } catch (e) {}
  let u; try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { return c96FrontPrev.apply(this, arguments); }
  const p = u.pathname, m = req.method, gh = m === "GET" || m === "HEAD";
  const host = String(req.headers.host || "").toLowerCase();
  if (gh && /^www\./.test(host) && !/^\/api\/stripe\//.test(p)) return c96Redirect(res, "https://" + host.slice(4) + (req.url && req.url.charAt(0) === "/" ? req.url : "/"), 301);
  if (gh && (p === "/signup" || p === "/signup/" || p === "/register" || p === "/register/")) return c96Redirect(res, "/__auth/register" + u.search, 301);
  if (gh && (p === "/login" || p === "/login/" || p === "/signin" || p === "/signin/")) return c96Redirect(res, "/__auth/login" + u.search, 301);
  const rm = gh && /^\/research\/([A-Za-z0-9.\-]{1,10})\/?$/.exec(p);
  if (rm && rm[1] !== "capital-sustainability" && typeof BB11_TICKERS !== "undefined" && BB11_TICKERS.indexOf(rm[1].toUpperCase()) >= 0) return c96Redirect(res, C93_CSM + "/" + rm[1].toUpperCase() + u.search, 301);
  if (gh && p === "/manifest.json" && typeof c93Manifest === "function") return c93Manifest(req, res);
  if (p === "/free-brief" || p === "/free-brief/") {
    if (m === "POST") return c96SignupPost(req, res);
    if (!gh) { res.setHeader("Allow", "GET, HEAD, POST"); return c96Redirect(res, "/free-brief/", 303); }
    if (p === "/free-brief") return c96Redirect(res, "/free-brief/" + u.search, 301);
    const user = await c96UserOf(req);
    if (c96IsAdmin(user)) req.c96Admin = true;
    if (user && !(req.c96Admin && /(?:^|;\s*)dispatch_preview=1/.test(String(req.headers.cookie || "")))) req.c94Signed = true;
    return c96FreeBriefPage(req, res, req.c94Signed ? user : null);
  }
  if (p.indexOf("/__auth/") === 0) {
    if (m === "HEAD") req.method = "GET";                                  // HEAD answers exactly as GET (Node drops the body for HEAD)
    if (req.method === "GET") { try { res.setHeader("Content-Security-Policy", C96_AUTH_CSP); } catch (e) {} }
    if (p === "/__auth/reset" && req.method === "GET" && !u.searchParams.get("token") && !cookieValue(req, "dispatch_reset")) return page(res, "Reset link expired", C96_RESET_NOTOKEN);
  }
  return c96FrontPrev.apply(this, arguments);
}
handle = c96Front;

// ── Inner wrapper (behind the maintenance gate): guest preview cookie, BYOK endpoints, Ask with the reader's key, gold spot ──
const C96_PV_COOKIE = "dispatch_preview";
function c96PvSet(res, on) {
  const c = on ? `${C96_PV_COOKIE}=1; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=1800` : `${C96_PV_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=0`;
  const prev = res.getHeader("Set-Cookie"); res.setHeader("Set-Cookie", prev ? [].concat(prev, c) : c);
}
var c96InnerPrev = bb10iHandle0;
async function c96Inner(req, res) {
  let u; try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { return c96InnerPrev.apply(this, arguments); }
  const p = u.pathname, m = req.method, gh = m === "GET" || m === "HEAD";
  const hasSess = !!(req.headers.cookie && typeof dispatchSessionTokens === "function" && dispatchSessionTokens(req.headers.cookie).length);
  const user = hasSess ? await c96UserOf(req) : null;
  const admin = c96IsAdmin(user);
  const view = gh && !p.startsWith("/api/") ? u.searchParams.get("view") : null;
  if (view === "guest" || view === "exit") {
    if (admin) {
      c96PvSet(res, view === "guest");
      u.searchParams.delete("view");
      return c96Redirect(res, p + (u.searchParams.toString() ? "?" + u.searchParams.toString() : ""), 302);
    }
    if (view === "exit") { c96PvSet(res, false); }
  }
  const pvOn = admin && /(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String(req.headers.cookie || ""));
  if (pvOn) {
    req.c96PreviewOn = true;
    if (gh && !p.startsWith("/api/")) req.c94Preview = p;
    if (p === "/api/me" && m === "GET") return json(res, 200, { guest: true, tier: "free", billingPortal: false, isAdmin: false, preview: true }, { "Cache-Control": "no-store" });
  } else if (user) req.c94Signed = true;
  if (p === "/api/c96/gold-spot" && gh) return c96GoldMicro(req, res, u);
  if (p.indexOf("/api/byok/") === 0) return c96ByokRoute(req, res, p, pvOn ? null : user);
  if (p === "/api/chat" && m === "POST" && user && !pvOn) { const self = this, args = arguments; return c96ByokAsk(req, res, user, () => c96InnerPrev.apply(self, args)); }
  return c96InnerPrev.apply(this, arguments);
}
bb10iHandle0 = c96Inner;
