// ── chat97 ── Light / Dark / System theme, gold dashboard, macro calendar, "What changed today", leftovers.
// Theme: a first-party cookie (dispatch_theme) picks the class on <html> for every server-rendered page,
// the app reads the same cookie (and localStorage) before first paint, and signed-in readers keep it in
// their saved preferences (display.scheme). System follows prefers-color-scheme through CSS alone, so no flash.
const C97_SCHEMES = ["light", "dark", "system"];
function c97SchemeOf(req) {
  const m = /(?:^|;\s*)dispatch_theme=(light|dark|system)(?:;|$)/.exec(String((req && req.headers && req.headers.cookie) || ""));
  return m ? m[1] : "system";
}
{
  const c97San0 = rt17SanitizePrefs;
  rt17SanitizePrefs = function (input) {
    const out = c97San0(input);
    try {
      const di = input && typeof input === "object" && input.display && typeof input.display === "object" ? input.display : null;
      if (out && out.display && di && C97_SCHEMES.indexOf(di.scheme) >= 0) out.display.scheme = di.scheme;
    } catch (e) {}
    return out;
  };
}
// Calm dark slate. Every pair below was checked for WCAG AA (4.5:1 body text, 3:1 large text and chart lines).
const C97_DARK = { paper: "#151b23", paper2: "#1b222c", paper3: "#222b37", ink: "#e7eaee", ink2: "#cdd3db", muted: "#aab3bf", rule: "#334050", accent: "#9cc0ea", down: "#f2998a", up: "#86d1a1", amber: "#e6c372", field: "#0f141a", fieldRule: "#66727f" };
function c97Css(rules) {
  // rules: [[selector-list, declarations]]; "" selector = the <html> element itself.
  const pre = (p, sel) => sel.split(",").map(s => { s = s.trim(); return s === "" ? p : s.indexOf("&") === 0 ? p + s.slice(1) : p + " " + s; }).join(",");
  const block = p => rules.map(r => pre(p, r[0]) + "{" + r[1] + "}").join("");
  return block("html.c97-dark") + "@media (prefers-color-scheme:dark){" + block("html.c97-system") + "}";
}
const C97D = C97_DARK;
const C97_SITE_CSS = c97Css([
  ["", `color-scheme:dark;--paper:${C97D.paper};--ink:${C97D.ink};--muted:${C97D.muted};--rule:${C97D.rule};--accent:${C97D.accent};--down:${C97D.down};--up:${C97D.up};--amber:${C97D.amber}`],
  ["body", `background:${C97D.paper};color:${C97D.ink}`],
  ["a", `color:${C97D.accent}`],
  ["header.site,.menu nav", `background:${C97D.paper2}!important`],
  [".dek,.lede", `color:${C97D.ink2}!important`],
  [".prose p,.prose li", `color:${C97D.ink2}!important`],
  ["footer.site", `background:${C97D.paper}`],
  [".c96su input[type=email],input,select,textarea", `background:${C97D.field}!important;color:${C97D.ink}!important;border-color:${C97D.fieldRule}!important`],
  [".c96su button,button.c96b,.cta", `background:${C97D.accent}!important;color:${C97D.field}!important;border-color:${C97D.accent}!important`],
  ["[style*=\"color:#5f6368\"],[style*=\"color:#66655f\"],[style*=\"color:#45443f\"],[style*=\"color:#555\"],[style*=\"color:#666\"]", `color:${C97D.muted}!important`],
  ["[style*=\"color:#1b1b1b\"],[style*=\"color:#2b2a26\"],[style*=\"color:#333\"]", `color:${C97D.ink}!important`],
  ["[style*=\"background:#fff\"],[style*=\"background:#ffffff\"],[style*=\"background:#fbfaf7\"],[style*=\"background:#f4f2ec\"],[style*=\"background: #fff\"]", `background:${C97D.paper2}!important`],
  ["[style*=\"color:#a23b2a\"]", `color:${C97D.down}!important`], ["[style*=\"color:#2f6b47\"]", `color:${C97D.up}!important`], ["[style*=\"color:#1f3a5f\"]", `color:${C97D.accent}!important`],
  ["img[src*=\"logo\"],svg.logo", "filter:invert(1) hue-rotate(180deg)"],
  [".c96ok", `background:#17301f!important;color:${C97D.ink}!important`], [".c96warn", `background:#3a2a12!important;color:${C97D.ink}!important`],
  ["[data-c94-preview]", "background:#0b2240!important;color:#fff!important"]
]);
const C97_AUTH_CSS = c97Css([
  ["", "color-scheme:dark"],
  ["body", `background:${C97D.paper}!important;color:${C97D.ink}!important`],
  ["main", `background:${C97D.paper2}!important;border-color:${C97D.rule}!important`],
  ["h1,h2,h3,strong", `color:${C97D.ink}!important`],
  ["p,li", `color:${C97D.ink2}!important`],
  ["label", `color:${C97D.ink}!important`],
  ["input,select,textarea", `background:${C97D.field}!important;color:${C97D.ink}!important;border-color:${C97D.fieldRule}!important`],
  ["main button", `background:${C97D.accent}!important;color:${C97D.field}!important`],
  ["main a", `color:${C97D.accent}!important`],
  [".muted,.muted a,a[style*=\"background:none\"]", `background:none!important;color:${C97D.muted}!important`],
  ["[style*=\"color:#a23b2a\"],.err,.error", `color:${C97D.down}!important`]
]) + "a.rt35s-login-link{color:#8a5300!important}"; // light: the amber link was 2:1 on white
const C97_GENERIC_CSS = c97Css([
  ["", "color-scheme:dark"],
  ["body", `background:${C97D.paper}!important;color:${C97D.ink}!important`],
  ["main,.card,.box", `background-color:transparent`],
  ["h1,h2,h3,strong,th,td", `color:${C97D.ink}!important`],
  ["p,li,.d,.src,.o a,.k", `color:${C97D.ink2}!important`],
  ["a", `color:${C97D.accent}!important`],
  ["input,select,textarea", `background:${C97D.field}!important;color:${C97D.ink}!important;border-color:${C97D.fieldRule}!important`],
  [".c96su button,button", `background:${C97D.accent}!important;color:${C97D.field}!important;border-color:${C97D.accent}!important`],
  [".c96ok", `background:#17301f!important;color:${C97D.ink}!important`], [".c96warn", `background:#3a2a12!important;color:${C97D.ink}!important`],
  ["[style*=\"color:#\"]", `color:${C97D.ink2}!important`],
  ["[style*=\"background:#\"]", `background:${C97D.paper2}!important`]
]);
// The toggle itself: a tiny POST form (works with scripts off, on auth and maintenance pages too).
const C97_TG_CSS = ".c97tg{display:inline-flex;align-items:center;gap:0;margin:0 0 0 8px;font:500 12px/1 Inter,system-ui,-apple-system,'Segoe UI',Arial,sans-serif}" +
  ".c97tg button{font:inherit;padding:6px 8px;min-height:30px;border:1px solid #8c877d;background:transparent;color:inherit;cursor:pointer;margin:0 0 0 -1px}" +
  ".c97tg button:first-of-type{border-radius:3px 0 0 3px;margin:0}.c97tg button:last-of-type{border-radius:0 3px 3px 0}" +
  ".c97tg button[aria-pressed=true]{background:#1b1b1b;color:#fff;border-color:#1b1b1b}.c97tg .c97tg-one{display:none}" +
  "@media (max-width:1439px){.c97tg button.c97tg-all{display:none}.c97tg .c97tg-one{display:inline-block;border-radius:3px;margin:0;white-space:nowrap}}header.site .nav a{white-space:nowrap}" +
  ".c97tg-float{position:absolute;top:10px;right:12px;z-index:9}" +
  "html.c97-dark .c97tg button{border-color:#66727f}html.c97-dark .c97tg button[aria-pressed=true]{background:#9cc0ea;color:#0f141a;border-color:#9cc0ea}" +
  "@media (prefers-color-scheme:dark){html.c97-system .c97tg button{border-color:#66727f}html.c97-system .c97tg button[aria-pressed=true]{background:#9cc0ea;color:#0f141a;border-color:#9cc0ea}}" +
  ".c97vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}";
const C97_LABEL = { light: "Light", dark: "Dark", system: "System" };
function c97ToggleHtml(scheme, back, float) {
  const next = scheme === "light" ? "dark" : scheme === "dark" ? "system" : "light";
  const b = c93Esc(String(back || "/").slice(0, 300));
  return `<form class="c97tg${float ? " c97tg-float" : ""}" method="post" action="/__theme" aria-label="Colour theme"><input type="hidden" name="back" value="${b}">` +
    C97_SCHEMES.map(s => `<button class="c97tg-all" type="submit" name="t" value="${s}" aria-pressed="${s === scheme}">${C97_LABEL[s]}</button>`).join("") +
    `<button class="c97tg-one" type="submit" name="t" value="${next}" aria-label="Theme: ${C97_LABEL[scheme]}. Switch to ${C97_LABEL[next]}">Theme: ${C97_LABEL[scheme]}</button></form>`;
}
function c97Transform(html, req) {
  if (typeof html !== "string" || html.length < 40 || html.indexOf('id="c97-theme"') >= 0 || html.indexOf("<!--c97-theme-->") >= 0) return html;
  if (!/^\s*<!doctype html/i.test(html)) return html;
  const scheme = c97SchemeOf(req);
  let path = "/"; try { path = new URL(req.url || "/", "http://localhost").pathname + (new URL(req.url || "/", "http://localhost").search || ""); } catch (e) {}
  if (html.indexOf('id="cmdBar"') >= 0 || /\/app\.js\?v=/.test(html)) {          // the app shell themes itself before paint; just set the class
    return html.replace(/<html([^>]*)>/i, (m, a) => /\sclass="/i.test(a) ? "<html" + a.replace(/\sclass="/i, ' class="c97-' + scheme + " ") + ">" : "<html" + a + ' class="c97-' + scheme + '">').replace("<head>", '<head><!--c97-theme-->');
  }
  const kind = html.indexOf('<header class="site"') >= 0 ? "site" : html.indexOf("rt34s-legal") >= 0 ? "auth" : "generic";
  const css = (kind === "site" ? C97_SITE_CSS : kind === "auth" ? C97_AUTH_CSS : C97_GENERIC_CSS) + C97_TG_CSS;
  html = html.replace(/<html([^>]*)>/i, (m, a) => /\sclass="/i.test(a) ? "<html" + a.replace(/\sclass="/i, ' class="c97-' + scheme + " ") + ">" : "<html" + a + ' class="c97-' + scheme + '">');
  const meta = scheme === "dark" ? `<meta name="theme-color" content="${C97D.paper}">` : scheme === "light" ? "" : `<meta name="theme-color" media="(prefers-color-scheme: dark)" content="${C97D.paper}">`;
  if (scheme === "dark") html = html.replace(/<meta name="theme-color" content="[^"]*">/i, "");
  html = html.replace(/<\/head>/i, `${meta}<style id="c97-theme">${css}</style></head>`);
  if (req && req.__c97NoForm) return html;
  if (kind === "site") html = html.replace('<details class="menu">', c97ToggleHtml(scheme, path, false) + '<details class="menu">');
  else html = html.replace(/<body([^>]*)>/i, (m) => m + c97ToggleHtml(scheme, path, true));
  return html;
}
// Response hook: holds an HTML writeHead until end() so the body can be themed and Content-Length recomputed.
// Installed twice: outermost (pages answered before the inner handler) and just after the compression shim
// (so it themes the page before gzip/brotli). Anything streamed with res.write passes through untouched.
function c97Hook(req, res) {
  if (!res || res.__c97h === 2) return;
  res.__c97h = (res.__c97h || 0) + 1;
  const oWH = res.writeHead, oW = res.write, oE = res.end;
  let held = null;
  const hget = (h, k) => { if (h) { const hk = Object.keys(h).find(x => x.toLowerCase() === k); if (hk) return h[hk]; } try { return res.getHeader(k); } catch (e) { return undefined; } };
  res.writeHead = function (status, a, b) {
    try {
      if (!held && !res.headersSent) {
        const reason = typeof a === "string" ? a : undefined;
        const h = (a && typeof a === "object" && !Array.isArray(a)) ? a : (b && typeof b === "object" && !Array.isArray(b)) ? b : null;
        if (!(Array.isArray(a) || Array.isArray(b))) {
          const ct = String(hget(h, "content-type") || ""), ce = hget(h, "content-encoding");
          if (/^text\/html/i.test(ct) && !ce && Number(status) !== 204 && Number(status) !== 304) { held = { status, reason, h: h || {} }; return res; }
        }
      }
    } catch (e) {}
    return oWH.apply(this, arguments);
  };
  const flush = () => { if (held) { const x = held; held = null; if (x.reason) oWH.call(res, x.status, x.reason, x.h); else oWH.call(res, x.status, x.h); } };
  res.write = function () { try { flush(); } catch (e) {} return oW.apply(res, arguments); };
  res.end = function (chunk, enc, cb) {
    try {
      const done = typeof chunk === "function" ? chunk : typeof enc === "function" ? enc : cb;
      const body = typeof chunk === "function" ? null : chunk;
      const implicit = !held && !res.headersSent && /^text\/html/i.test(String(res.getHeader("content-type") || "")) && !res.getHeader("content-encoding");
      if ((held || implicit) && body != null && (typeof body === "string" || Buffer.isBuffer(body))) {
        const s = typeof body === "string" ? body : body.toString("utf8");
        try { const csp = String((held && hget(held.h, "content-security-policy")) || res.getHeader("content-security-policy") || ""); req.__c97NoForm = /form-action 'none'/.test(csp); } catch (e) {}
        const out = c97Transform(s, req);
        if (out !== s) {
          const len = Buffer.byteLength(out);
          if (held) { Object.keys(held.h).forEach(k => { if (k.toLowerCase() === "content-length") delete held.h[k]; }); held.h["Content-Length"] = len; }
          else if (res.getHeader("content-length") != null) res.setHeader("Content-Length", len);
          flush();
          return oE.call(res, out, done);
        }
      }
      if (held && body == null && req.method === "HEAD") {
        // HEAD: Node drops the body; keep the declared length honest by leaving it as the page code set it.
      }
      flush();
    } catch (e) { try { flush(); } catch (e2) {} }
    return oE.apply(res, arguments);
  };
}
{
  const c97Rt20 = rt20sWrapResponse;
  rt20sWrapResponse = function (req, res) { const r = c97Rt20.apply(this, arguments); try { c97Hook(req, res); } catch (e) {} return r; };
}
// POST /__theme: saves the choice in the cookie, and in the account for a signed-in reader (not in guest preview).
async function c97ThemePost(req, res) {
  let raw = "";
  try { for await (const ch of req) { raw += ch; if (raw.length > 2048) break; } } catch (e) {}
  let t = "", back = "/";
  const ct = String(req.headers["content-type"] || "");
  try {
    if (/json/i.test(ct)) { const j = JSON.parse(raw || "{}"); t = j.theme || j.t || ""; back = j.back || "/"; }
    else { const f = new URLSearchParams(raw); t = f.get("t") || ""; back = f.get("back") || "/"; }
  } catch (e) {}
  if (C97_SCHEMES.indexOf(t) < 0) { res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" }); return res.end("Pick light, dark or system."); }
  if (!/^\/(?![\/\\])[^\s<>"]*$/.test(back)) back = "/";
  const origin = String(req.headers.origin || ""), host = String(req.headers.host || "");
  const sameOrigin = !origin || origin === "null" ? !origin : (() => { try { return new URL(origin).host === host; } catch (e) { return false; } })();
  const secure = String(req.headers["x-forwarded-proto"] || "").indexOf("https") === 0 || !!(req.socket && req.socket.encrypted) || /thedispatch\.uk$/i.test(host);
  const ck = `dispatch_theme=${t}; Path=/; Max-Age=31536000; SameSite=Lax${secure ? "; Secure" : ""}`;
  if (!sameOrigin) { res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" }); return res.end("Theme changes must come from this site."); }
  let saved = "device";
  if (sameOrigin) {
    try {
      const user = await c96UserOf(req);
      const preview = user && c96IsAdmin(user) && /(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String(req.headers.cookie || ""));
      if (user && !preview && sql) {
        const rows = await sql`SELECT prefs FROM dispatch_user_prefs WHERE user_id=${user.id} LIMIT 1`;
        const cur = rt17SanitizePrefs(bb4aObj(rows && rows[0] && rows[0].prefs));
        cur.display = Object.assign({}, cur.display || {}, { scheme: t });
        await bb4aPutPrefs(user, { prefs: cur });
        saved = "account";
      }
    } catch (e) { saved = "device"; }
  }
  if (/json/i.test(ct)) { res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "Set-Cookie": ck }); return res.end(JSON.stringify({ ok: true, theme: t, saved })); }
  res.writeHead(303, { Location: back, "Cache-Control": "no-store", "Set-Cookie": ck });
  return res.end();
}
// ── chat97 data: small stale-while-revalidate cache over free official sources ──
const C97_UA = "The Dispatch Market research (dispatchmarket@mail.grokbot.com)";
async function c97Get(url, accept) {
  const r = await fetch(url, { headers: { "User-Agent": C97_UA, Accept: accept || "*/*" }, signal: AbortSignal.timeout(12000), redirect: "follow" });
  if (!r.ok) throw new Error("http " + r.status);
  return r;
}
const c97Mem = new Map();
async function c97Cached(key, ttl, fn, waitMs) {
  let e = c97Mem.get(key); const now = Date.now();
  if (!e) { e = { v: null, at: 0, err: "", p: null, tryAt: 0 }; c97Mem.set(key, e); }
  const fresh = e.v != null && now - e.at < ttl;
  if (!fresh && !e.p && now - e.tryAt > (e.v != null ? 60e3 : 20e3)) {
    e.tryAt = now;
    e.p = Promise.resolve().then(fn).then(v => { if (v != null) { e.v = v; e.at = Date.now(); e.err = ""; } }).catch(err => { e.err = String(err && err.message || err).replace(/[^\w .:-]/g, "").slice(0, 80); }).finally(() => { e.p = null; });
  }
  if (e.v == null && e.p) await Promise.race([e.p, new Promise(r => setTimeout(r, waitMs || 9000))]);
  return { v: e.v, at: e.at, err: e.err, stale: !!(e.v != null && Date.now() - e.at >= ttl) };
}
function c97UkFmt(ms, o) { try { return new Intl.DateTimeFormat("en-GB", Object.assign({ timeZone: "Europe/London" }, o)).format(new Date(ms)); } catch (e) { return ""; } }
function c97UkHm(ms) { return c97UkFmt(ms, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }); }
function c97UkDate(ms) { return c97UkFmt(ms, { weekday: "short", day: "numeric", month: "short" }); }
function c97UkIso(ms) { return c97UkFmt(ms, { year: "numeric", month: "2-digit", day: "2-digit" }).split("/").reverse().join("-"); }
function c97UkWhen(ms) { return c97UkDate(ms) + ", " + c97UkHm(ms) + " UK"; }
function c97DayLong(iso) { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || "")); if (!m) return String(iso || ""); return Number(m[3]) + " " + ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][Number(m[2]) - 1] + " " + m[1]; }
function c97TzOff(ms, tz) {
  const p = {}; new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }).formatToParts(new Date(ms)).forEach(x => { p[x.type] = x.value; });
  return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute, +p.second) - ms;
}
function c97Zoned(y, mo, d, h, mi, tz) { let g = Date.UTC(y, mo - 1, d, h, mi); let t = g - c97TzOff(g, tz); t = g - c97TzOff(t, tz); return t; }
function c97N(v, dp) { const n = Number(v); return isFinite(n) ? n.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }) : "n/a"; }
function c97Sg(v, dp, unit) { const n = Number(v); if (!isFinite(n)) return ""; return (n > 0 ? "+" : n < 0 ? "\u2212" : "") + Math.abs(n).toFixed(dp) + (unit || ""); }
const C97_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function c97Period(ym) { const m = /^(\d{4})-(\d{2})/.exec(ym || ""); return m ? C97_MON[Number(m[2]) - 1] + " " + m[1] : String(ym || ""); }
function c97Quarter(ym) { const m = /^(\d{4})-(\d{2})/.exec(ym || ""); return m ? "Q" + (Math.floor((Number(m[2]) - 1) / 3) + 1) + " " + m[1] : String(ym || ""); }

// FRED (St. Louis Fed) keyless CSV. Rows: [isoDate, number], oldest first.
async function c97Fred(id, years) {
  const from = new Date(Date.now() - (years || 2) * 366 * 864e5).toISOString().slice(0, 10);
  const r = await c97Cached("fred:" + id, 3 * 3600e3, async () => {
    const t = await (await c97Get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + encodeURIComponent(id) + "&cosd=" + from, "text/csv,*/*")).text();
    const rows = t.trim().split(/\r?\n/).slice(1).map(l => l.split(",")).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x[0]) && x[1] !== "." && x[1] !== "" && isFinite(Number(x[1]))).map(x => [x[0], Number(x[1])]);
    if (!rows.length) throw new Error("empty");
    return rows;
  });
  return r;
}
// ONS time series JSON: months/quarters with releaseDate and nextRelease.
async function c97Ons(path) {
  return c97Cached("ons:" + path, 3 * 3600e3, async () => {
    const j = await (await c97Get("https://www.ons.gov.uk/" + path + "/data", "application/json")).json();
    const months = (j.months || []).map(m => { const mm = /^(\d{4}) ([A-Z]{3})$/.exec(String(m.date || "")); if (!mm || !isFinite(Number(m.value))) return null; return [mm[1] + "-" + ("0" + (C97_MON.map(x => x.toUpperCase()).indexOf(mm[2]) + 1)).slice(-2), Number(m.value)]; }).filter(Boolean);
    const d = j.description || {};
    return { rows: months, releaseDate: d.releaseDate || "", nextRelease: d.nextRelease || "", title: d.title || "" };
  });
}
async function c97Boe() {
  return c97Cached("boe:bank-rate", 6 * 3600e3, async () => {
    const t = await (await c97Get("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2024&Dateto=now&SeriesCodes=IUDBEDR&CSVF=TN&UsingCodes=Y", "text/csv,*/*")).text();
    const rows = [];
    t.split(/\r?\n/).forEach(l => { const m = /^(\d{1,2}) (\w{3}) (\d{4}),\s*([\d.]+)/.exec(l.trim()); if (m) rows.push([m[3] + "-" + ("0" + (C97_MON.indexOf(m[2]) + 1)).slice(-2) + "-" + ("0" + m[1]).slice(-2), Number(m[4])]); });
    if (!rows.length) throw new Error("empty");
    rows.sort((a, b) => a[0] < b[0] ? -1 : 1);
    return rows;
  });
}
// Schedules. FOMC and MPC dates were read from federalreserve.gov and bankofengland.co.uk on 2 Nov 2026.
const C97_FOMC = ["2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08"];
const C97_MPC = ["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30", "2026-09-17", "2026-11-05", "2026-12-17", "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-17", "2027-07-29", "2027-09-16", "2027-11-04", "2027-12-16"];
async function c97Bls() {
  return c97Cached("bls:ics", 12 * 3600e3, async () => {
    const t = await (await c97Get("https://www.bls.gov/schedule/news_release/bls.ics", "text/calendar,*/*")).text();
    const out = [];
    t.replace(/\r?\n[ \t]/g, "").split("BEGIN:VEVENT").slice(1).forEach(ev => {
      const s = /SUMMARY[^:]*:(.+)/.exec(ev), d = /DTSTART[^:]*:(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/.exec(ev);
      if (!s || !d) return;
      const title = s[1].trim();
      const kind = /^Employment Situation\b/i.test(title) ? "us_jobs" : /^Consumer Price Index\b/i.test(title) ? "us_cpi" : null;
      if (!kind) return;
      out.push({ ms: c97Zoned(+d[1], +d[2], +d[3], +d[4], +d[5], "America/New_York"), kind, title });
    });
    if (!out.length) throw new Error("no events");
    return out;
  });
}
async function c97Bea() {
  return c97Cached("bea:schedule", 12 * 3600e3, async () => {
    const t = await (await c97Get("https://www.bea.gov/news/schedule/full", "text/html")).text();
    const out = [], re = /release-date">([^<]+)<\/div>\s*<small[^>]*>([^<]+)<\/small>[\s\S]*?release-title[^>]*>([^<]+)</g;
    const yr = new Date().getUTCFullYear(); let m, last = 0, y = yr;
    while ((m = re.exec(t))) {
      const title = m[3].replace(/&amp;/g, "&").trim();
      const kind = /^GDP \(|Gross Domestic Product, \d/i.test(title) ? "us_gdp" : /Personal Income and Outlays/i.test(title) ? "us_pce" : null;
      const dm = /(\w+)\s+(\d{1,2})/.exec(m[1]), tm = /(\d{1,2}):(\d{2})\s*([AP]M)/i.exec(m[2]);
      if (!dm) continue;
      const mi = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].indexOf(dm[1].slice(0, 3).toLowerCase());
      if (mi < 0) continue;
      if (mi < last - 6) y = yr + 1; last = mi;
      if (!kind) continue;
      let h = tm ? Number(tm[1]) % 12 + (/pm/i.test(tm[3]) ? 12 : 0) : 8, mn = tm ? Number(tm[2]) : 30;
      out.push({ ms: c97Zoned(y, mi + 1, Number(dm[2]), h, mn, "America/New_York"), kind, title });
    }
    if (!out.length) throw new Error("no events");
    return out;
  });
}
async function c97OnsUpcoming() {
  return c97Cached("ons:upcoming", 12 * 3600e3, async () => {
    const out = [];
    for (const [q, re, kind] of [["consumer price inflation", /^Consumer price inflation, UK: \w+ \d{4}$/i, "uk_cpi"], ["gdp monthly estimate", /^GDP monthly estimate, UK: \w+ \d{4}$/i, "uk_gdp"], ["labour market", /^UK Labour Market: \w+ \d{4}$/i, "uk_lab"]]) {
      try {
        const j = await (await c97Get("https://api.beta.ons.gov.uk/v1/search/releases?limit=30&release-type=type-upcoming&query=" + encodeURIComponent(q), "application/json")).json();
        (j.releases || []).forEach(r => { const d = r.description || {}; const ms = Date.parse(d.release_date || ""); if (re.test(String(d.title || "")) && isFinite(ms)) out.push({ ms, kind, title: d.title }); });
      } catch (e) {}
    }
    if (!out.length) throw new Error("no events");
    return out;
  });
}
const C97_KIND = {
  us_jobs: { venue: "US", agency: "BLS", name: "US jobs report (payrolls and unemployment)", src: "US Bureau of Labor Statistics", url: "https://www.bls.gov/schedule/news_release/empsit.htm", plain: "How many jobs US employers added last month. A strong number tends to lift the dollar and yields." },
  us_cpi: { venue: "US", agency: "BLS", name: "US consumer prices (CPI)", src: "US Bureau of Labor Statistics", url: "https://www.bls.gov/schedule/news_release/cpi.htm", plain: "How fast US prices rose over the past year. Hotter inflation usually means higher-for-longer rates." },
  us_gdp: { venue: "US", agency: "BEA", name: "US GDP", src: "US Bureau of Economic Analysis", url: "https://www.bea.gov/news/schedule", plain: "How fast the US economy grew, at an annual rate, after inflation." },
  us_pce: { venue: "US", agency: "BEA", name: "US personal income and spending (PCE prices)", src: "US Bureau of Economic Analysis", url: "https://www.bea.gov/news/schedule", plain: "The Fed's preferred inflation gauge, shown as the yearly change." },
  fomc: { venue: "US", agency: "Fed", name: "Federal Reserve rate decision (FOMC)", src: "Federal Reserve", url: "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", plain: "The Fed sets the US policy rate range. Statement at 14:00 New York time." },
  uk_cpi: { venue: "UK", agency: "ONS", name: "UK consumer prices (CPI)", src: "Office for National Statistics", url: "https://www.ons.gov.uk/economy/inflationandpriceindices", plain: "How fast UK prices rose over the past year. The Bank of England targets 2%." },
  uk_gdp: { venue: "UK", agency: "ONS", name: "UK GDP, monthly estimate", src: "Office for National Statistics", url: "https://www.ons.gov.uk/economy/grossdomesticproductgdp", plain: "Whether UK output grew or shrank in the month." },
  uk_lab: { venue: "UK", agency: "ONS", name: "UK labour market (unemployment)", src: "Office for National Statistics", url: "https://www.ons.gov.uk/employmentandlabourmarket", plain: "The UK unemployment rate over three months." },
  mpc: { venue: "UK", agency: "BoE", name: "Bank of England rate decision (MPC)", src: "Bank of England", url: "https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates", plain: "The Bank of England sets Bank Rate. Announcement at 12:00 UK." }
};
// Latest two readings per kind, with the period they describe. Values are computed exactly as stated in "how".
async function c97Readings() {
  const out = {};
  const yoy = (rows, i) => i >= 12 ? (rows[i][1] / rows[i - 12][1] - 1) * 100 : null;
  const fr = async (id) => { const r = await c97Fred(id, 3); return r.v || []; };
  const jobs = await fr("PAYEMS"), un = await fr("UNRATE");
  if (jobs.length > 2) {
    const i = jobs.length - 1, d0 = jobs[i][1] - jobs[i - 1][1], d1 = jobs[i - 1][1] - jobs[i - 2][1];
    const u0 = un.find(x => x[0] === jobs[i][0]), u1 = un.find(x => x[0] === jobs[i - 1][0]);
    out.us_jobs = { period: jobs[i][0].slice(0, 7), actual: c97Sg(d0, 0, "k jobs") + (u0 ? ", unemployment " + c97N(u0[1], 1) + "%" : ""), prevPeriod: jobs[i - 1][0].slice(0, 7), previous: c97Sg(d1, 0, "k jobs") + (u1 ? ", unemployment " + c97N(u1[1], 1) + "%" : ""), how: "Change in nonfarm payrolls (FRED PAYEMS), unemployment rate (FRED UNRATE)" };
  }
  for (const [k, id] of [["us_cpi", "CPIAUCSL"], ["us_pce", "PCEPI"]]) {
    const r = await fr(id); const i = r.length - 1;
    if (i > 13) out[k] = { period: r[i][0].slice(0, 7), actual: c97N(yoy(r, i), 1) + "% a year", prevPeriod: r[i - 1][0].slice(0, 7), previous: c97N(yoy(r, i - 1), 1) + "% a year", how: "Year-on-year change in the index (FRED " + id + ")" };
  }
  const g = await fr("A191RL1Q225SBEA");
  if (g.length > 1) { const i = g.length - 1; out.us_gdp = { period: g[i][0].slice(0, 7), quarter: true, actual: c97N(g[i][1], 1) + "% annualised", prevPeriod: g[i - 1][0].slice(0, 7), previous: c97N(g[i - 1][1], 1) + "% annualised", how: "Real GDP growth, seasonally adjusted annual rate (FRED A191RL1Q225SBEA)" }; }
  const fu = await fr("DFEDTARU"), fl = await fr("DFEDTARL");
  if (fu.length && fl.length) {
    const lu = fu[fu.length - 1], ll = fl[fl.length - 1];
    let pu = null, pl = null; for (let i = fu.length - 1; i >= 0; i--) if (fu[i][1] !== lu[1]) { pu = fu[i]; pl = fl.find(x => x[0] === fu[i][0]) || null; break; }
    out.fomc = { period: lu[0], actual: c97N(ll[1], 2) + "\u2013" + c97N(lu[1], 2) + "%", previous: pu ? c97N(pl ? pl[1] : pu[1] - 0.25, 2) + "\u2013" + c97N(pu[1], 2) + "%" : "", prevPeriod: pu ? pu[0] : "", series: fu, how: "Federal funds target range (FRED DFEDTARL, DFEDTARU)" };
  }
  const oc = await c97Ons("economy/inflationandpriceindices/timeseries/d7g7/mm23");
  if (oc.v && oc.v.rows.length > 1) { const r = oc.v.rows, i = r.length - 1; out.uk_cpi = { period: r[i][0], actual: c97N(r[i][1], 1) + "% a year", prevPeriod: r[i - 1][0], previous: c97N(r[i - 1][1], 1) + "% a year", released: oc.v.releaseDate, next: oc.v.nextRelease, how: "CPI annual rate (ONS series D7G7)" }; }
  const og = await c97Ons("economy/grossdomesticproductgdp/timeseries/ecy2/mgdp");
  if (og.v && og.v.rows.length > 2) { const r = og.v.rows, i = r.length - 1; out.uk_gdp = { period: r[i][0], actual: c97Sg((r[i][1] / r[i - 1][1] - 1) * 100, 1, "% on the month"), prevPeriod: r[i - 1][0], previous: c97Sg((r[i - 1][1] / r[i - 2][1] - 1) * 100, 1, "% on the month"), released: og.v.releaseDate, next: og.v.nextRelease, how: "Monthly change in the GDP index (ONS series ECY2)" }; }
  const ol = await c97Ons("employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/mgsx/lms");
  if (ol.v && ol.v.rows.length > 1) { const r = ol.v.rows, i = r.length - 1; out.uk_lab = { period: r[i][0], three: true, actual: c97N(r[i][1], 1) + "% unemployed", prevPeriod: r[i - 1][0], previous: c97N(r[i - 1][1], 1) + "% unemployed", released: ol.v.releaseDate, next: ol.v.nextRelease, how: "Unemployment rate, three months ending in the month shown (ONS series MGSX)" }; }
  const b = await c97Boe();
  if (b.v && b.v.length) { const r = b.v, l = r[r.length - 1]; let p = null; for (let i = r.length - 1; i >= 0; i--) if (r[i][1] !== l[1]) { p = r[i]; break; } out.mpc = { period: l[0], actual: c97N(l[1], 2) + "%", previous: p ? c97N(p[1], 2) + "%" : "", prevPeriod: p ? p[0] : "", series: r, how: "Bank Rate (Bank of England series IUDBEDR)" }; }
  return out;
}
function c97PeriodLabel(k, ym, rd) {
  if (!ym) return "";
  if (k === "fomc" || k === "mpc") return "from " + c97DayLong(ym);
  if (rd && rd.quarter) return c97Quarter(ym);
  if (rd && rd.three) { const m = /^(\d{4})-(\d{2})/.exec(ym); if (m) { const e = Number(m[2]) - 1, s = (e + 10) % 12; return "3 months to " + C97_MON[e] + " " + m[1] + " (" + C97_MON[s] + "\u2013" + C97_MON[e] + ")"; } }
  return c97Period(ym);
}
// Which period a release on this date should describe, so an un-updated source is never shown as the new figure.
function c97Expect(k, ms) {
  const y = Number(c97UkFmt(ms, { year: "numeric" })), m = Number(c97UkFmt(ms, { month: "numeric" }));
  const back = n => { let yy = y, mm = m - n; while (mm < 1) { mm += 12; yy--; } return yy + "-" + ("0" + mm).slice(-2); };
  if (k === "us_jobs" || k === "us_cpi" || k === "us_pce" || k === "uk_cpi") return back(1);
  if (k === "uk_gdp" || k === "uk_lab") return back(2);
  if (k === "us_gdp") { const q = Math.floor((m - 1) / 3); let yy = y, qq = q; if (qq === 0) { qq = 4; yy--; } return yy + "-" + ("0" + (qq * 3 - 2)).slice(-2); }
  return null;
}
async function c97Calendar() {
  return (await c97Cached("c97:calendar", 30 * 60e3, async () => {
    const now = Date.now(), ev = [];
    const [bls, bea, ons] = await Promise.all([c97Bls(), c97Bea(), c97OnsUpcoming()]);
    const notes = [];
    (bls.v || []).forEach(e => ev.push(e)); if (!bls.v) notes.push("BLS schedule unavailable right now");
    (bea.v || []).forEach(e => ev.push(e)); if (!bea.v) notes.push("BEA schedule unavailable right now");
    (ons.v || []).forEach(e => ev.push(e)); if (!ons.v) notes.push("ONS upcoming releases unavailable right now");
    C97_FOMC.forEach(d => { const [y, mo, da] = d.split("-").map(Number); ev.push({ ms: c97Zoned(y, mo, da, 14, 0, "America/New_York"), kind: "fomc", title: "FOMC statement" }); });
    C97_MPC.forEach(d => { const [y, mo, da] = d.split("-").map(Number); ev.push({ ms: c97Zoned(y, mo, da, 12, 0, "Europe/London"), kind: "mpc", title: "MPC announcement" }); });
    const R = await c97Readings();
    // Recent UK releases come from each ONS series' own release date.
    for (const k of ["uk_cpi", "uk_gdp", "uk_lab"]) { const rd = R[k]; const ms = rd && Date.parse(rd.released || ""); if (isFinite(ms) && !ev.some(e => e.kind === k && Math.abs(e.ms - ms) < 864e5)) ev.push({ ms: ms, kind: k, title: C97_KIND[k].name }); }
    // ONS publishes at 07:00 UK; its feeds carry the date only, so pin UK rows to 07:00 UK on that day.
    ev.forEach(e => { if (/^uk_/.test(e.kind)) { const [y, mo, da] = c97UkIso(e.ms).split("-").map(Number); e.ms = c97Zoned(y, mo, da, 7, 0, "Europe/London"); } });
    const seen = {};
    const rows = ev.filter(e => e.ms > now - 21 * 864e5 && e.ms < now + 75 * 864e5).sort((a, b) => a.ms - b.ms).filter(e => { const key = e.kind + ":" + c97UkIso(e.ms); if (seen[key]) return false; seen[key] = 1; return true; }).map(e => {
      const K = C97_KIND[e.kind], rd = R[e.kind], past = e.ms <= now;
      const row = { ms: e.ms, when: c97UkWhen(e.ms), dayIso: c97UkIso(e.ms), venue: K.venue, agency: K.agency, name: K.name, title: e.title, source: K.src, sourceUrl: K.url, plain: K.plain, past, previous: "", actual: "", how: rd ? rd.how : "" };
      if (!rd) { row.previous = "Not available right now"; row.actual = past ? "Not available right now" : "Due " + row.when; return row; }
      if (e.kind === "fomc" || e.kind === "mpc") {
        const day = new Date(e.ms).toISOString().slice(0, 10);
        if (past) {
          const s = rd.series || []; const after = s.filter(x => x[0] >= day)[0], before = s.filter(x => x[0] < day).slice(-1)[0];
          const fmt = x => e.kind === "fomc" ? (c97N(x[1] - 0.25, 2) + "\u2013" + c97N(x[1], 2) + "%") : c97N(x[1], 2) + "%";
          row.actual = after ? fmt(after) + (before && after[1] === before[1] ? " (unchanged)" : "") : "Awaiting the source update";
          row.previous = before ? fmt(before) : "";
        } else { row.previous = rd.actual + " (current)"; row.actual = "Due " + row.when; }
        return row;
      }
      const exp = c97Expect(e.kind, e.ms), lab = p => c97PeriodLabel(e.kind, p, rd);
      if (past) {
        if (exp && rd.period === exp) { row.actual = lab(rd.period) + ": " + rd.actual; row.previous = lab(rd.prevPeriod) + ": " + rd.previous; }
        else { row.actual = "Awaiting the source update"; row.previous = lab(rd.period) + ": " + rd.actual; }
      } else { row.previous = lab(rd.period) + ": " + rd.actual; row.actual = "Due " + row.when; }
      return row;
    });
    return { rows, notes, fetchedAt: now };
  }, 15000)).v;
}

// Gold dashboard readings (2-minute cache, last good kept if a feed fails).
async function c97GoldDash() {
  return (await c97Cached("c97:gold", 2 * 60e3, async () => {
    const at = Date.now(), rows = {};
    const [xau, xag, yq, fx, ry, ty] = await Promise.all([
      (async () => { try { return await fetchGoldProxy(); } catch (e) { return null; } })(),
      (async () => { try { const j = await (await c97Get("https://api.gold-api.com/price/XAG", "application/json")).json(); return Number(j.price) > 0 ? { p: Number(j.price), ts: Date.parse(j.updatedAt || "") || at } : null; } catch (e) { return null; } })(),
      (async () => { try { return await yahooQuote(["DX-Y.NYB", "GBPUSD=X", "EURUSD=X"]); } catch (e) { return null; } })(),
      (async () => { try { const j = await (await c97Get("https://api.frankfurter.dev/v1/latest?base=USD&symbols=GBP,EUR", "application/json")).json(); return j && j.rates ? j : null; } catch (e) { return null; } })(),
      c97Fred("DFII10", 1), c97Fred("DGS10", 1)
    ]);
    const tsMs = t => { const n = Number(t); return n > 1e12 ? n : n > 1e9 ? n * 1000 : at; };
    const ok = q => q && Number(q.p) > 0;
    const Q = yq || {};
    const gbp = ok(Q["GBPUSD=X"]) ? { usd: Number(Q["GBPUSD=X"].p), src: "Yahoo Finance FX, delayed", ms: tsMs(Q["GBPUSD=X"].ts) } : fx && fx.rates.GBP ? { usd: 1 / Number(fx.rates.GBP), src: "ECB reference rate via Frankfurter, " + c97DayLong(fx.date), ms: Date.parse(fx.date + "T15:00:00Z") } : null;
    const eur = ok(Q["EURUSD=X"]) ? { usd: Number(Q["EURUSD=X"].p), src: "Yahoo Finance FX, delayed", ms: tsMs(Q["EURUSD=X"].ts) } : fx && fx.rates.EUR ? { usd: 1 / Number(fx.rates.EUR), src: "ECB reference rate via Frankfurter, " + c97DayLong(fx.date), ms: Date.parse(fx.date + "T15:00:00Z") } : null;
    if (ok(xau)) {
      const p = Number(xau.p), ms = tsMs(xau.ts);
      rows.gold_usd = { label: "Gold spot, US$ per troy ounce", value: "$" + c97N(p, 2), source: "gold-api.com spot", asOf: c97UkWhen(ms), plain: "The dollar price of one troy ounce (31.1 g) of gold." };
      if (gbp) rows.gold_gbp = { label: "Gold spot, \u00a3 per troy ounce", value: "\u00a3" + c97N(p / gbp.usd, 2), source: "gold-api.com spot \u00f7 pound in dollars (" + c97N(gbp.usd, 4) + ", " + gbp.src + ")", asOf: c97UkWhen(Math.min(ms, gbp.ms)), plain: "The same ounce priced in pounds. A weaker pound lifts this even if the dollar price is flat." };
      if (eur) rows.gold_eur = { label: "Gold spot, \u20ac per troy ounce", value: "\u20ac" + c97N(p / eur.usd, 2), source: "gold-api.com spot \u00f7 euro in dollars (" + c97N(eur.usd, 4) + ", " + eur.src + ")", asOf: c97UkWhen(Math.min(ms, eur.ms)), plain: "The same ounce priced in euros." };
      if (ok(xag)) rows.ratio = { label: "Gold/silver ratio", value: c97N(p / xag.p, 1), source: "gold-api.com spot gold \u00f7 spot silver ($" + c97N(xag.p, 2) + ")", asOf: c97UkWhen(Math.min(ms, xag.ts)), plain: "How many ounces of silver buy one ounce of gold. A higher ratio means silver is cheap relative to gold." };
    }
    if (ok(xag)) rows.silver = { label: "Silver spot, US$ per troy ounce", value: "$" + c97N(xag.p, 2), source: "gold-api.com spot", asOf: c97UkWhen(xag.ts), plain: "The dollar price of one troy ounce of silver." };
    const dq = Q["DX-Y.NYB"];
    if (ok(dq)) rows.dxy = { label: "US dollar index", value: c97N(dq.p, 2), change: dq.prev > 0 ? c97Sg((dq.p / dq.prev - 1) * 100, 2, "%") : "", source: "ICE US Dollar Index via Yahoo Finance, delayed", asOf: c97UkWhen(tsMs(dq.ts)), plain: "The dollar against six major currencies. A stronger dollar is usually a headwind for gold." };
    const fred = (r, label, plain, series) => { const v = r && r.v; if (!v || !v.length) return null; const a = v[v.length - 1], b = v[v.length - 2]; return { label, value: c97N(a[1], 2) + "%", change: b ? c97Sg(a[1] - b[1], 2, " pt") : "", source: "US Treasury daily print via FRED (" + series + "), dated " + c97DayLong(a[0]), asOf: "Fetched " + c97UkWhen(r.at), plain, date: a[0], num: a[1], prev: b ? b[1] : null }; };
    const r1 = fred(ry, "US 10-year real yield", "The 10-year Treasury yield after expected inflation. Gold, which pays no interest, often struggles when this rises.", "DFII10"); if (r1) rows.ry = r1;
    const r2 = fred(ty, "US 10-year Treasury yield", "What the US government pays to borrow for ten years.", "DGS10"); if (r2) rows.tnx = r2;
    if (!Object.keys(rows).length) throw new Error("no feeds");
    // Free market feeds are delayed: say so next to the time. Official FRED rows show their print date instead.
    ["gold_usd", "gold_gbp", "gold_eur", "silver", "ratio", "dxy"].forEach(k => { if (rows[k]) { rows[k].delayed = true; if (rows[k].asOf && !/^Delayed/.test(rows[k].asOf)) rows[k].asOf = "Delayed \u00b7 as of " + rows[k].asOf; } });
    return { rows, at };
  }, 9000)).v;
}
// 10-year yield for the live tables: FRED DGS10 first (the official Treasury print); the live script falls back to Yahoo, labelled.
async function c97Dgs10(req, res) {
  const r = await c97Fred("DGS10", 1);
  const v = r.v;
  if (!v || !v.length) return json(res, 200, { available: false, reason: r.err || "pending" }, { "Cache-Control": "no-store" });
  const a = v[v.length - 1], b = v[v.length - 2];
  return json(res, 200, { available: true, value: a[1], prev: b ? b[1] : null, change: b ? Math.round((a[1] - b[1]) * 100) / 100 : null, date: a[0], source: "US Treasury via FRED", series: "DGS10", fetchedAt: new Date(r.at).toISOString() }, { "Cache-Control": "public, max-age=900" });
}
// ── chat97 pages: /gold/dashboard/, /calendar/, and "What changed today" ──
const C97_CSS = ".c97t{width:100%;border-collapse:collapse;margin:8px 0 6px}.c97t th{font:600 12px/1.4 var(--sans);text-align:left;color:var(--muted);border-bottom:1px solid var(--ink);padding:8px 8px 6px}" +
  ".c97t td{vertical-align:top;border-bottom:1px solid var(--rule);padding:10px 8px;font-size:15px}.c97t td.v{font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}" +
  ".c97s{display:block;font-size:12.5px;color:var(--muted);margin-top:3px}.c97p{display:block;font-size:13.5px;margin-top:3px}.c97note{font-size:13.5px;color:var(--muted);max-width:760px}" +
  ".c97tl{list-style:none;margin:8px 0;padding:0;border-left:2px solid var(--rule)}.c97tl li{margin:0 0 12px;padding:0 0 0 14px}.c97tl time{font:600 13px var(--sans);display:block}" +
  ".c97tag{display:inline-block;font:600 11px/1.6 var(--sans);border:1px solid var(--rule);border-radius:3px;padding:0 6px;margin-right:6px;color:var(--ink)}" +
  "@media (max-width:719px){.c97t.c97r thead{display:none}.c97t.c97r tr{display:block;border-bottom:1px solid var(--rule);padding:8px 0}.c97t.c97r td{display:block;border:0;padding:3px 0}}";
function c97Tbl(rows) {
  return `<table class="c97t c97r"><thead><tr><th scope="col">Measure</th><th scope="col">Reading</th><th scope="col">Change</th><th scope="col">Source and time</th></tr></thead><tbody>` +
    rows.filter(Boolean).map(r => `<tr><td><strong>${c93Esc(r.label)}</strong><span class="c97p">${c93Esc(r.plain || "")}</span></td><td class="v">${c93Esc(r.value)}</td><td>${c93Esc(r.change || "")}</td><td><span class="c97s">${c93Esc(r.source)}</span><span class="c97s">${c93Esc(r.asOf || "")}</span></td></tr>`).join("") + `</tbody></table>`;
}
async function c97Today() {
  return (await c97Cached("c97:today", 5 * 60e3, async () => {
    const now = Date.now(), today = c97UkIso(now), items = [];
    const [cal, gd] = await Promise.all([c97Calendar().catch(() => null), c97GoldDash().catch(() => null)]);
    (cal && cal.rows || []).filter(r => r.dayIso === today).forEach(r => items.push({ ms: r.ms, time: c97UkHm(r.ms) + " UK", title: r.name + (r.past ? "" : " (due)"), detail: r.past ? "Actual " + r.actual + ". Previous " + r.previous + "." : "Previous " + r.previous + ".", source: r.source, url: r.sourceUrl }));
    const R = gd && gd.rows || {};
    if (R.dxy && R.dxy.change) items.push({ ms: now, time: R.dxy.asOf, title: "US dollar index " + R.dxy.value, detail: R.dxy.change + " since the previous close.", source: R.dxy.source });
    if (R.gold_usd) items.push({ ms: now - 1, time: R.gold_usd.asOf, title: "Gold spot " + R.gold_usd.value + (R.gold_gbp ? " (" + R.gold_gbp.value + ")" : ""), detail: "Latest spot reading.", source: R.gold_usd.source });
    if (R.silver) items.push({ ms: now - 2, time: R.silver.asOf, title: "Silver spot " + R.silver.value, detail: R.ratio ? "Gold/silver ratio " + R.ratio.value + "." : "Latest spot reading.", source: R.silver.source });
    const yd = new Date(now - 864e5 * (new Date(now).getUTCDay() === 1 ? 3 : 1)).toISOString().slice(0, 10);
    for (const k of ["tnx", "ry"]) { const r = R[k]; if (r && r.date >= yd) items.push({ ms: now - 3, time: "Print dated " + c97DayLong(r.date), title: r.label + " " + r.value, detail: (r.change ? r.change + " on the previous print." : "") , source: r.source }); }
    try {
      if (typeof bb7HouseIndex === "function") {
        const idx = await Promise.race([bb7HouseIndex(now), new Promise(r => setTimeout(() => r(null), 4000))]);
        const hs = (idx && idx.items || []).filter(i => bb7IsoDate(i.filingDate) === today);
        if (hs.length) items.push({ ms: now - 4, time: "Filed " + c97DayLong(today), title: hs.length + " House periodic transaction report" + (hs.length > 1 ? "s" : ""), detail: hs.slice(0, 4).map(h => h.member).filter(Boolean).join(", ") + (hs.length > 4 ? " and others" : "") + ".", source: "US House Clerk financial disclosures", url: "https://disclosures-clerk.house.gov/FinancialDisclosure" });
      }
    } catch (e) {}
    items.sort((a, b) => b.ms - a.ms);
    return { day: today, items, fetchedAt: now, fetchedUk: c97UkWhen(now) };
  }, 15000)).v || { day: c97UkIso(Date.now()), items: [], fetchedUk: c97UkWhen(Date.now()) };
}
function c97TodayHtml(t) {
  if (!t || !t.items.length) return `<p class="c97note">Nothing sourced has changed yet today (${c93Esc(c97DayLong(c97UkIso(Date.now())))}). Releases and price moves appear here as they land.</p>`;
  return `<ol class="c97tl">` + t.items.map(i => `<li><time>${c93Esc(i.time)}</time><strong>${c93Esc(i.title)}</strong> ${c93Esc(i.detail || "")}<span class="c97s">Source: ${i.url ? `<a href="${c93Esc(i.url)}" rel="noopener">${c93Esc(i.source)}</a>` : c93Esc(i.source)}</span></li>`).join("") + `</ol><p class="c97s">Checked ${c93Esc(t.fetchedUk || "")}.</p>`;
}
async function c97GoldPage(req, res, user) {
  const gd = await c97GoldDash().catch(() => null), R = gd && gd.rows || {};
  const t = await c97Today().catch(() => null);
  const body = `<style>${C97_CSS}</style><section><div class="kicker">Gold</div><h1>Gold dashboard</h1><p class="dek">Gold in dollars, pounds and euros, the gold/silver ratio, real yields and the dollar, each with its source and the UK time of the reading.</p><p class="byline">${C93_EDITOR}</p></section>` +
    `<section><h2>Price</h2>${c97Tbl([R.gold_usd, R.gold_gbp, R.gold_eur, R.silver, R.ratio])}${R.gold_usd ? "" : `<p class="c97note">The spot feed is not answering right now. Try again in a minute.</p>`}</section>` +
    `<section><h2>What moves it</h2>${c97Tbl([R.ry, R.tnx, R.dxy])}<p class="c97note">Treasury yields are official end-of-day prints, published the next US morning. The dollar index is a delayed market price.</p></section>` +
    `<section><h2>Central-bank buying and ETF flows</h2><p class="c97note">The World Gold Council publishes these figures on Goldhub. Its terms do not allow us to copy or republish its data without written permission, so we link to it instead of showing the numbers here.</p><ul><li><a href="https://www.gold.org/goldhub/data/gold-reserves-by-country" rel="noopener">Central-bank gold reserves (World Gold Council, Goldhub)</a></li><li><a href="https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows" rel="noopener">Gold ETF holdings and flows (World Gold Council, Goldhub)</a></li></ul></section>` +
    `<section><h2>What changed today</h2>${c97TodayHtml(t)}</section>` +
    `<section><p class="c97note">See also the <a href="/calendar/">macro calendar</a> and <a href="/gold/">how to read gold</a>. Readings refresh about every two minutes; a feed that fails keeps its last reading with its original time.</p></section>`;
  const html = c93Shell({ title: "Gold dashboard | The Dispatch Market", path: "/gold/dashboard/", desc: "Gold in US dollars, pounds and euros, the gold/silver ratio, real yields and the dollar, with sources and UK times. Not investment advice.", user, body });
  return c93Html(req, res, html, "private, max-age=60");
}
async function c97CalendarPage(req, res, user) {
  const cal = await c97Calendar().catch(() => null), rows = cal && cal.rows || [];
  const tr = r => `<tr><td><strong>${c93Esc(r.when)}</strong></td><td><span class="c97tag">${c93Esc(r.venue)}</span>${c93Esc(r.agency)}</td><td><strong>${c93Esc(r.name)}</strong><span class="c97p">${c93Esc(r.plain)}</span></td><td>${c93Esc(r.previous)}</td><td>${c93Esc(r.actual)}</td><td><span class="c97s"><a href="${c93Esc(r.sourceUrl)}" rel="noopener">${c93Esc(r.source)}</a></span><span class="c97s">${c93Esc(r.how)}</span></td></tr>`;
  const head = `<thead><tr><th scope="col">UK date and time</th><th scope="col">Country</th><th scope="col">Release</th><th scope="col">Previous</th><th scope="col">Actual</th><th scope="col">Source</th></tr></thead>`;
  const up = rows.filter(r => !r.past), past = rows.filter(r => r.past).reverse();
  const body = `<style>${C97_CSS}</style><section><div class="kicker">Calendar</div><h1>Macro calendar</h1><p class="dek">The US and UK releases that move gold, the dollar and rates, in UK time, with the previous figure and, once published, the actual figure.</p><p class="byline">${C93_EDITOR}</p></section>` +
    `<section><h2>Coming up</h2>${up.length ? `<table class="c97t c97r">${head}<tbody>${up.map(tr).join("")}</tbody></table>` : `<p class="c97note">The schedules are not answering right now. Try again shortly.</p>`}</section>` +
    `<section><h2>Recently released</h2>${past.length ? `<table class="c97t c97r">${head}<tbody>${past.map(tr).join("")}</tbody></table>` : `<p class="c97note">No releases in the last three weeks.</p>`}</section>` +
    `<section><p class="c97note">Not shown, because each needs a paid source: consensus forecasts, market-implied rate-cut odds and earnings-call transcripts. We only show numbers we can source for free and cite. "Awaiting the source update" means the release time has passed but the free official series has not yet been updated. Dates come from the BLS and BEA release schedules, the ONS release calendar, and the Federal Reserve and Bank of England meeting calendars. US times are converted from New York time.${cal && cal.notes && cal.notes.length ? " " + c93Esc(cal.notes.join(". ")) + "." : ""}</p></section>`;
  const html = c93Shell({ title: "Macro calendar | The Dispatch Market", path: "/calendar/", desc: "US and UK macro releases in UK time with previous and actual figures from BLS, BEA, ONS, the Fed and the Bank of England. Not investment advice.", user, body });
  return c93Html(req, res, html, "private, max-age=120");
}
C93_NAV.splice(2, 0, ["/calendar/", "Calendar"]);
{
  const c97Route0 = c93Route;
  c93Route = async function (req, res) {
    if (req.method === "GET" || req.method === "HEAD") {
      let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { u0 = null; }
      const p = u0 ? u0.pathname : "";
      if (p === "/gold/dashboard" || p === "/calendar" || p === "/gold/dashboard/" || p === "/calendar/") {
        if (!p.endsWith("/")) { res.writeHead(301, { Location: p + "/" + (u0.search || "") }); res.end(); return true; }
        let user = await c96UserOf(req);
        if (user && req.c96PreviewOn) { req.c94Preview = p; user = null; }
        if (user) req.c94Signed = true;
        if (p === "/gold/dashboard/") await c97GoldPage(req, res, user); else await c97CalendarPage(req, res, user);
        return true;
      }
    }
    return c97Route0.apply(this, arguments);
  };
}
// House filings: newest first by real filing date (the source dates are M/D/YYYY, so a text sort is wrong).
if (typeof bb7HouseIndex === "function") {
  const c97HI0 = bb7HouseIndex;
  bb7HouseIndex = async function () {
    const r = await c97HI0.apply(this, arguments);
    try { if (r && Array.isArray(r.items)) r.items = r.items.slice().sort((a, b) => String(bb7IsoDate(b.filingDate)).localeCompare(String(bb7IsoDate(a.filingDate)))); } catch (e) {}
    return r;
  };
}
if (typeof bb7HouseView === "function") {
  const c97House0 = bb7HouseView;
  bb7HouseView = function () {
    const out = c97House0.apply(this, arguments);
    try {
      if (out && Array.isArray(out.items)) {
        out.items = out.items.slice().sort((a, b) => String(bb7IsoDate(b.filingDate)).localeCompare(String(bb7IsoDate(a.filingDate))));
        out.items.forEach(i => { const iso = bb7IsoDate(i.filingDate); if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) i.filingDateUk = c97DayLong(iso); });
        out.order = "newest filing first";
      }
    } catch (e) {}
    return out;
  };
}
// Light touch on existing pages: a link to the dashboard from /gold/, and the timeline on /brief/.
{
  const c97Tx0 = c97Transform;
  c97Transform = function (html, req) {
    let p = "/"; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (typeof html === "string" && html.indexOf('<header class="site"') >= 0 && html.indexOf('id="c97-theme"') < 0) {
      if (p === "/gold/") html = html.replace("</section>", `</section><p class="c97note" style="margin:6px 0 0"><a href="/gold/dashboard/"><strong>Open the gold dashboard</strong></a>: gold in \u00a3, $ and \u20ac, the gold/silver ratio, real yields and the dollar, with sources.</p>`);
      if (p === "/brief/" && C97_TODAY_SNAP) html = html.replace("</main>", `<section><style>${C97_CSS}</style><h2>What changed today</h2>${c97TodayHtml(C97_TODAY_SNAP)}</section></main>`);
    }
    return c97Tx0(html, req);
  };
}
var C97_TODAY_SNAP = null;
function c97TodayWarm() { c97Today().then(t => { if (t) C97_TODAY_SNAP = t; }).catch(() => {}); }
// Outermost wrapper: theme form, theme hook, the new JSON endpoints, and guest preview on /api/prefs.
{
  const c97H0 = handle;
  handle = async function (req, res) {
    try { c97Hook(req, res); } catch (e) {}
    let u; try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { return c97H0.apply(this, arguments); }
    const p = u.pathname, m = req.method;
    if (p === "/__theme" || p === "/__theme/") {
      if (m === "POST") return c97ThemePost(req, res);
      res.writeHead(303, { Location: "/", "Cache-Control": "no-store" }); return res.end();
    }
    if (p === "/brief/" && (m === "GET" || m === "HEAD")) { if (!C97_TODAY_SNAP || Date.now() - C97_TODAY_SNAP.fetchedAt > 5 * 60e3) { const w = c97Today().then(t => { if (t) C97_TODAY_SNAP = t; }).catch(() => {}); if (!C97_TODAY_SNAP) await Promise.race([w, new Promise(r => setTimeout(r, 3000))]); } }
    if (p === "/api/prefs") {
      const admin = /(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String(req.headers.cookie || "")) && c96IsAdmin(await c96UserOf(req));
      if (admin) {
        if (m === "GET" || m === "HEAD") return json(res, 401, { error: "Sign in required.", preview: true }, { "Cache-Control": "no-store" });
        return json(res, 403, { error: "Guest preview is read-only.", preview: true }, { "Cache-Control": "no-store" });
      }
    }
    return c97H0.apply(this, arguments);
  };
}
// JSON endpoints sit inside the maintenance wrapper, like the other public read-only APIs.
{
  const c97I0 = bb10iHandle0;
  bb10iHandle0 = async function c97Inner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if ((req.method === "GET" || req.method === "HEAD") && p.indexOf("/api/c97/") === 0) {
      const H = { "Cache-Control": "public, max-age=60" };
      try {
        if (p === "/api/c97/dgs10") return await c97Dgs10(req, res);
        if (p === "/api/c97/gold-dash") { const g = await c97GoldDash(); return json(res, 200, g ? { available: true, rows: g.rows, fetchedAt: new Date(g.at).toISOString(), fetchedUk: c97UkWhen(g.at) } : { available: false }, H); }
        if (p === "/api/c97/calendar") { const c = await c97Calendar(); return json(res, 200, c ? { available: true, rows: c.rows, notes: c.notes, consensus: "Not shown: consensus forecasts, rate-cut odds and transcripts need a paid source.", fetchedUk: c97UkWhen(c.fetchedAt) } : { available: false }, H); }
        if (p === "/api/c97/today") { const t = await c97Today(); return json(res, 200, t, H); }
      } catch (e) { return json(res, 200, { available: false }, { "Cache-Control": "no-store" }); }
      return json(res, 404, { error: "Not found" }, { "Cache-Control": "no-store" });
    }
    return c97I0.apply(this, arguments);
  };
}
setTimeout(() => { try { c97GoldDash().catch(() => {}); c97Calendar().catch(() => {}); c97TodayWarm(); } catch (e) {} }, 4000).unref();
// ── chat97: the site's own Ask no longer uses xAI Grok. Order: Google Gemini first, then OpenAI, then any other
// configured provider. Readers can still bring their own xAI key (BYOK), which is untouched.
function c97AiRank(id) { return id === "google" ? 0 : id === "openai" ? 1 : 2; }
{
  const c97Aps0 = aiProviderStatus;
  aiProviderStatus = function () {
    const s = c97Aps0.apply(this, arguments);
    try {
      const order = (s.fallbackOrder || []).filter(id => id !== "xai");
      s.fallbackOrder = order.map((id, i) => [id, i]).sort((a, b) => c97AiRank(a[0]) - c97AiRank(b[0]) || a[1] - b[1]).map(x => x[0]);
      s.strategy = "gemini-first-openai-fallback";
      (s.providers || []).forEach(p => { if (p.id === "xai") { p.enabled = false; p.mode = "readers-own-key-only"; } });
    } catch (e) {}
    return s;
  };
}
if (typeof bb3bAttempts === "function") {
  const c97Att0 = bb3bAttempts;
  bb3bAttempts = function () {
    const list = c97Att0.apply(this, arguments) || [];
    if (list.length === 1 && list[0] && list[0].id === "byok") return list; // a reader's own key: leave as chosen
    const rank = a => a.kind === "provider" && a.id === "google" ? 0 : (a.kind === "openai-slot" || a.id === "openai") ? 1 : 2;
    return list.filter(a => a && a.kind !== "xai-key" && a.id !== "xai").map((a, i) => [a, i]).sort((x, y) => rank(x[0]) - rank(y[0]) || x[1] - y[1]).map(x => x[0]);
  };
}
