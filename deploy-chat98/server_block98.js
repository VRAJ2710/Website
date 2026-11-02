// In-app alerts and Portfolio X-ray. Tables come from deploy-chat98/dev_create.sql (run by hand);
// this code never runs DDL. Each feature stays hidden until to_regclass finds its tables.
const C98_TABLES = { alerts: ["dispatch_alerts", "dispatch_alert_events"], portfolio: ["dispatch_portfolio"] };
let C98_REG = { at: 0, v: null };
function c98Db() { try { const d = c96Db(); if (d) return d; } catch (e) {} return (typeof sql === "function" && sql) ? sql : null; }
async function c98Status() {
  if (C98_REG.v && Date.now() - C98_REG.at < 5 * 60e3) return C98_REG.v;
  const db = c98Db(), v = { alerts: false, portfolio: false };
  if (db) {
    try {
      const has = async n => { const r = await db`SELECT to_regclass(${"public." + n}) AS t`; return !!(r && r[0] && r[0].t); };
      for (const k of Object.keys(C98_TABLES)) { let all = true; for (const n of C98_TABLES[k]) if (!(await has(n))) { all = false; break; } v[k] = all; }
    } catch (e) { v.alerts = false; v.portfolio = false; }
  }
  C98_REG = { at: Date.now(), v }; return v;
}
// Email delivery is built behind a flag and stays off: it needs a mail provider key that is not set.
function c98EmailOn() { return process.env.DISPATCH_ALERTS_EMAIL === "1" && !!process.env.DISPATCH_MAIL_API_KEY; }
const C98_EMAIL_NOTE = "Email alerts are switched off. They need a mail provider key (DISPATCH_MAIL_API_KEY) before they can be turned on. Alerts show here and in the app.";
// Subjects readers can watch. Values come from the gold dashboard feeds (each keeps its own source and time).
const C98_SUBJ = {
  gold_usd: { kind: "price", label: "Gold spot, US$ per ounce", unit: "$", dp: 2 },
  gold_gbp: { kind: "price", label: "Gold spot, \u00a3 per ounce", unit: "\u00a3", dp: 2 },
  gold_eur: { kind: "price", label: "Gold spot, \u20ac per ounce", unit: "\u20ac", dp: 2 },
  silver: { kind: "price", label: "Silver spot, US$ per ounce", unit: "$", dp: 2 },
  dxy: { kind: "price", label: "US dollar index", unit: "", dp: 2 },
  ratio: { kind: "level", label: "Gold/silver ratio", unit: "", dp: 1 },
  tnx: { kind: "level", label: "US 10-year Treasury yield (%)", unit: "", dp: 2 },
  ry: { kind: "level", label: "US 10-year real yield (%)", unit: "", dp: 2 }
};
function c98Num(s) { const n = Number(String(s == null ? "" : s).replace(/[^0-9.\-]/g, "")); return Number.isFinite(n) ? n : null; }
function c98Fmt(sub, v) { const d = C98_SUBJ[sub]; return d ? d.unit + c97N(v, d.dp) : String(v); }
function c98SameOrigin(req) {
  const o = String(req.headers.origin || ""), host = String(req.headers.host || "");
  if (!o) return String(req.headers["sec-fetch-site"] || "") === "same-origin";
  try { return new URL(o).host === host; } catch (e) { return false; }
}
function c98Preview(req, user) { return !!(user && c96IsAdmin(user) && /(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String(req.headers.cookie || ""))); }
async function c98Body(req) {
  let raw = ""; for await (const ch of req) { raw += ch; if (raw.length > 64 * 1024) { const e = new Error("too large"); e.code = "C98_BIG"; throw e; } }
  const ct = String(req.headers["content-type"] || "");
  if (/json/i.test(ct)) { try { return { json: true, v: JSON.parse(raw || "{}") }; } catch (e) { return { json: true, v: {} }; } }
  const f = new URLSearchParams(raw), v = {}; for (const [k, x] of f) v[k] = x; return { json: false, v };
}
function c98Reply(req, res, b, status, body, back) {
  if (b && b.json === false) { const q = body && body.error ? "?e=" + encodeURIComponent(String(body.error).slice(0, 160)) : "?ok=1"; res.writeHead(303, { Location: back + q, "Cache-Control": "no-store" }); return res.end(); }
  return json(res, status, body, { "Cache-Control": "no-store" });
}
function c98Limit(user) { try { return hasPremiumAccess(user) ? 50 : 10; } catch (e) { return 10; } }
async function c98Alerts(uid) {
  const db = c98Db();
  const a = await db`SELECT id, kind, subject, op, threshold, note, active, armed, created_at, last_fired_at, last_value FROM dispatch_alerts WHERE user_id=${uid} ORDER BY created_at DESC LIMIT 100`;
  const e = await db`SELECT id, alert_id, fired_at, value, message, seen FROM dispatch_alert_events WHERE user_id=${uid} ORDER BY fired_at DESC LIMIT 30`;
  return { alerts: a || [], events: e || [] };
}
function c98MacroNames(cal) { const s = new Set(); ((cal && cal.rows) || []).forEach(r => { if (r && r.name) s.add(r.name); }); return Array.from(s).sort(); }
async function c98AlertCreate(user, v) {
  const sub = String(v.subject || "").slice(0, 80), kind = C98_SUBJ[sub] ? C98_SUBJ[sub].kind : "macro";
  let op = String(v.op || ""), thr = null;
  if (kind === "macro") {
    const cal = await c97Calendar().catch(() => null);
    if (c98MacroNames(cal).indexOf(sub) < 0) return { status: 400, body: { error: "Pick a release from the list." } };
    op = "release";
  } else {
    if (op !== "above" && op !== "below") return { status: 400, body: { error: "Pick above or below." } };
    thr = c98Num(v.threshold); if (thr == null || thr <= -100 || thr > 1e7) return { status: 400, body: { error: "Enter a number for the level." } };
  }
  const note = String(v.note || "").replace(/[\u0000-\u001f<>]/g, "").trim().slice(0, 140) || null;
  const uid = String(user.id), db = c98Db();
  const cur = await db`SELECT id FROM dispatch_alerts WHERE user_id=${uid} LIMIT 60`;
  if ((cur || []).length >= c98Limit(user)) return { status: 409, body: { error: "You have reached your alert limit (" + c98Limit(user) + "). Delete one first." } };
  const r = await db`INSERT INTO dispatch_alerts (user_id, kind, subject, op, threshold, note) VALUES (${uid}, ${kind}, ${sub}, ${op}, ${thr}, ${note}) RETURNING id`;
  C98_EVAL.at = 0;
  return { status: 200, body: { ok: true, id: r && r[0] ? r[0].id : null } };
}
// Evaluator: crossing alerts fire once, then re-arm when the reading goes back the other side.
const C98_EVAL = { at: 0, busy: false, last: null };
async function c98Evaluate() {
  if (C98_EVAL.busy) return; C98_EVAL.busy = true;
  try {
    const st = await c98Status(); if (!st.alerts) return;
    const db = c98Db();
    const gd = await c97GoldDash().catch(() => null), R = (gd && gd.rows) || {};
    const cal = await c97Calendar().catch(() => null);
    const list = await db`SELECT id, user_id, kind, subject, op, threshold, armed, created_at, last_fired_at FROM dispatch_alerts WHERE active=TRUE ORDER BY id LIMIT 5000`;
    let fired = 0;
    for (const a of list || []) {
      if (a.kind === "macro") {
        const since = Math.max(Date.parse(a.created_at) || 0, Date.parse(a.last_fired_at || "") || 0);
        const row = ((cal && cal.rows) || []).filter(r => r.name === a.subject && r.actual && r.ms > since && r.ms <= Date.now()).sort((x, y) => y.ms - x.ms)[0];
        if (row) {
          const msg = row.name + " is out: " + row.actual + (row.previous ? " (previous " + row.previous + ")" : "") + ". Source: " + row.source + ", released " + row.when + ".";
          await db`UPDATE dispatch_alerts SET last_fired_at=now() WHERE id=${a.id}`;
          await db`INSERT INTO dispatch_alert_events (alert_id, user_id, value, message) VALUES (${a.id}, ${a.user_id}, ${null}, ${msg.slice(0, 400)})`;
          fired++;
        }
        continue;
      }
      const r = R[a.subject]; const v = r ? c98Num(r.value) : null; if (v == null) continue;
      const thr = Number(a.threshold), hit = a.op === "above" ? v > thr : v < thr;
      if (hit && a.armed) {
        const lab = C98_SUBJ[a.subject] ? C98_SUBJ[a.subject].label : a.subject;
        const msg = lab + " is " + r.value + ", " + (a.op === "above" ? "above" : "below") + " your level of " + c98Fmt(a.subject, thr) + ". Source: " + r.source + ". " + (r.asOf || "") + ".";
        await db`UPDATE dispatch_alerts SET armed=FALSE, last_fired_at=now(), last_value=${v} WHERE id=${a.id}`;
        await db`INSERT INTO dispatch_alert_events (alert_id, user_id, value, message) VALUES (${a.id}, ${a.user_id}, ${v}, ${msg.slice(0, 400)})`;
        fired++;
      } else if (!hit && !a.armed) {
        await db`UPDATE dispatch_alerts SET armed=TRUE, last_value=${v} WHERE id=${a.id}`;
      }
    }
    C98_EVAL.last = { at: Date.now(), checked: (list || []).length, fired };
  } catch (e) { C98_EVAL.last = { at: Date.now(), error: String(e && e.message || e).slice(0, 120) }; }
  finally { C98_EVAL.busy = false; C98_EVAL.at = Date.now(); }
}
setInterval(() => { c98Evaluate().catch(() => {}); }, 5 * 60e3).unref();
setTimeout(() => { c98Evaluate().catch(() => {}); }, 20e3).unref();

// ── Portfolio X-ray: information only ──
const C98_CLASSES = {
  uk_eq: { label: "UK shares", macro: 1, usd: 0.3, gold: 0, rates: -4 },
  us_eq: { label: "US shares", macro: 1, usd: 1, gold: 0, rates: -6 },
  gl_eq: { label: "Global shares", macro: 1, usd: 0.6, gold: 0, rates: -5 },
  em_eq: { label: "Emerging-market shares", macro: 1.2, usd: 0.4, gold: 0, rates: -5 },
  gilts: { label: "UK government bonds (gilts)", macro: -0.2, usd: 0, gold: 0, rates: -8 },
  linkers: { label: "Index-linked bonds", macro: -0.1, usd: 0, gold: 0, rates: -12 },
  ust: { label: "US Treasuries", macro: -0.2, usd: 1, gold: 0, rates: -7 },
  credit: { label: "Corporate bonds", macro: 0.3, usd: 0.2, gold: 0, rates: -6 },
  gold: { label: "Gold", macro: -0.1, usd: 1, gold: 1, rates: -3 },
  silver: { label: "Silver and other metals", macro: 0.5, usd: 1, gold: 0.8, rates: -3 },
  property: { label: "Property", macro: 0.7, usd: 0, gold: 0, rates: -7 },
  crypto: { label: "Crypto", macro: 1.5, usd: 1, gold: 0, rates: -6 },
  cash_gbp: { label: "Cash in pounds", macro: 0, usd: 0, gold: 0, rates: 0 },
  cash_usd: { label: "Cash in US dollars", macro: 0, usd: 1, gold: 0, rates: 0 },
  other: { label: "Not classified", macro: 0, usd: 0, gold: 0, rates: 0 }
};
const C98_RULES = [
  [/premium bonds?/i, "cash_gbp"], [/gold|bullion|sovereign|britannia|krugerrand/i, "gold"], [/silver|platinum|palladium|metals?\b/i, "silver"],
  [/bitcoin|ethereum|crypto|\bbtc\b|\beth\b/i, "crypto"], [/index[- ]?linked|linker|\btips\b|inflation[- ]linked/i, "linkers"],
  [/gilt|uk gov/i, "gilts"], [/treasur|us gov/i, "ust"], [/corporate|credit|\bbond/i, "credit"],
  [/reit|property|real estate/i, "property"], [/emerging|\bem\b|china|india|brazil/i, "em_eq"],
  [/world|global|msci|acwi|all[- ]world|developed/i, "gl_eq"],
  [/s&p|nasdaq|dow jones|\bus\b|america|u\.s\./i, "us_eq"], [/ftse|\buk\b|britain|british/i, "uk_eq"],
  [/(usd|dollar).*cash|cash.*(usd|dollar)/i, "cash_usd"], [/cash|savings|money market|premium bonds/i, "cash_gbp"]
];
function c98Classify(name, cls) { if (cls && C98_CLASSES[cls]) return cls; for (const [re, c] of C98_RULES) if (re.test(name)) return c; return "other"; }
function c98Parse(text) {
  const out = []; const lines = String(text || "").split(/\r?\n/).slice(0, 60);
  for (let ln of lines) {
    ln = ln.trim(); if (!ln || /^name\s*,/i.test(ln)) continue;
    const parts = ln.split(/\s*[,;\t]\s*/); if (parts.length < 2) continue;
    const name = parts[0].replace(/["<>]/g, "").slice(0, 60), amt = c98Num(parts[1]); if (!name || amt == null || amt <= 0) continue;
    out.push({ name, amount: amt, cls: c98Classify(name, (parts[2] || "").trim()) });
  }
  return out.slice(0, 50);
}
function c98Xray(h) {
  const tot = h.reduce((s, x) => s + x.amount, 0); if (!tot) return null;
  const by = {}; h.forEach(x => { by[x.cls] = (by[x.cls] || 0) + x.amount / tot; });
  const sum = k => Object.keys(by).reduce((s, c) => s + by[c] * C98_CLASSES[c][k], 0);
  return { total: tot, by, macro: sum("macro"), usd: sum("usd"), gold: sum("gold"), rates: sum("rates") };
}
function c98Arr(h) { if (typeof h === "string") { try { h = JSON.parse(h); } catch (e) { h = null; } } return Array.isArray(h) ? h.filter(x => x && x.name && x.amount > 0 && C98_CLASSES[x.cls]) : []; }
async function c98Portfolio(uid) { const r = await c98Db()`SELECT holdings, updated_at FROM dispatch_portfolio WHERE user_id=${uid} LIMIT 1`; return r && r[0] ? { holdings: c98Arr(r[0].holdings), at: Date.parse(r[0].updated_at) || Date.now() } : { holdings: [], at: 0 }; }
function c98Pct(x) { return (Math.round(x * 1000) / 10).toFixed(1) + "%"; }
const C98_ASOF = "Mon 2 Nov 2026";
function c98XrayHtml(h, at, R) {
  const x = c98Xray(h); if (!x) return `<p class="c97note">Add holdings below to see the X-ray.</p>`;
  const src = `<span class="c97s">Source: your holdings, saved ${c93Esc(c97UkWhen(at))}</span>`;
  const rows = Object.keys(x.by).sort((a, b) => x.by[b] - x.by[a]).map(c => `<tr><td><strong>${c93Esc(C98_CLASSES[c].label)}</strong></td><td class="v">${c98Pct(x.by[c])}</td><td>${src}</td></tr>`).join("");
  const line = (k, title, plain, v) => `<tr><td><strong>${title}</strong><span class="c97p">${plain}</span></td><td class="v">${v}</td><td>${src}<span class="c97s">Method: rule-of-thumb weights below, set ${C98_ASOF}</span></td></tr>`;
  const ratesTxt = (x.rates >= 0 ? "+" : "") + (Math.round(x.rates * 10) / 10).toFixed(1) + "%";
  const live = [R.ry, R.dxy, R.gold_gbp].filter(Boolean);
  return `<div class="c98wrap"><table class="c97t"><thead><tr><th>What you hold</th><th>Share</th><th>Source and time</th></tr></thead><tbody>${rows}</tbody></table></div>` +
    `<h2>Sensitivity</h2><div class="c98wrap"><table class="c97t"><thead><tr><th>Exposure</th><th>Reading</th><th>Source and method</th></tr></thead><tbody>` +
    line("macro", "Growth (macro) exposure", "How much of the mix tends to rise and fall with the economy. 100% is roughly an all-shares mix.", c98Pct(x.macro)) +
    line("usd", "US dollar exposure", "The share priced in dollars. For a pound-based reader, a stronger dollar lifts this part in pounds and a weaker one lowers it.", c98Pct(x.usd)) +
    line("gold", "Gold exposure", "How much moves with the gold price.", c98Pct(x.gold)) +
    line("rates", "Rates sensitivity", "A rough guide to the move in the whole mix if long-term interest rates rose by one percentage point. Bonds fall when yields rise.", ratesTxt) +
    `</tbody></table></div>` + (live.length ? `<h2>Today's readings for these drivers</h2>${c97Tbl(live)}` : "");
}
function c98HoldingsText(h) { return h.map(x => `${x.name}, ${x.amount}${x.cls && x.cls !== c98Classify(x.name) ? ", " + x.cls : ""}`).join("\n"); }
const C98_CSS = ".c98f{display:grid;gap:10px;max-width:640px;margin:10px 0}.c98f label{font:600 13px/1.4 var(--sans)}.c98f input,.c98f select,.c98f textarea{font:15px/1.4 var(--sans);padding:8px;border:1px solid var(--rule);border-radius:6px;background:var(--paper);color:var(--ink);width:100%}.c98f textarea{min-height:160px;font-family:ui-monospace,Menlo,monospace}.c98f button{font:600 14px/1 var(--sans);padding:10px 14px;border-radius:6px;border:0;background:var(--accent);color:#fff;cursor:pointer;justify-self:start}.c98wrap{overflow-x:auto;max-width:100%}html.c97-dark .c98f button{color:#0f1720}@media (prefers-color-scheme:dark){html.c97-system .c98f button{color:#0f1720}}.c98row{display:flex;gap:8px;flex-wrap:wrap;align-items:end}.c98row>*{flex:1 1 140px}.c98msg{padding:10px 12px;border-radius:6px;border:1px solid var(--rule);margin:10px 0}.c98ev{list-style:none;padding:0}.c98ev li{border-top:1px solid var(--rule);padding:10px 0}.c98ev .new{font:700 11px/1 var(--sans);text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin-right:6px}.c98del{display:inline}.c98del button{background:none;color:var(--accent);border:1px solid var(--rule);padding:6px 10px}";
function c98Msg(u0) { const e = u0.searchParams.get("e"), ok = u0.searchParams.get("ok"); return e ? `<p class="c98msg" role="alert">${c93Esc(e.slice(0, 160))}</p>` : ok ? `<p class="c98msg" role="status">Saved.</p>` : ""; }
function c98Gate(title, path, desc, user, msg) {
  return c93Shell({ title: title + " | The Dispatch Market", path, desc, user, body: `<style>${C97_CSS}${C98_CSS}</style><section><h1>${c93Esc(title)}</h1><p class="dek">${msg}</p><p class="byline">${C93_EDITOR}</p></section>` });
}
function c98Send(req, res, html, status) {
  const wh = res.writeHead;
  res.writeHead = function (st, h) { res.writeHead = wh; return wh.call(this, status || st, Object.assign({}, h || {}, { "Cache-Control": "private, no-store" })); };
  return c93Html(req, res, html, "no-store");
}
async function c98AlertsPage(req, res, user, u0) {
  const st = await c98Status();
  const desc = "Price, level and macro-release alerts shown in the app. Information only.";
  if (!st.alerts) return c98Send(req, res, c98Gate("Alerts", "/alerts/", desc, user, "Alerts are not switched on yet. Check back soon."), 404);
  if (!user) return c98Send(req, res, c98Gate("Alerts", "/alerts/", desc, user, `Alerts are for signed-in readers. <a href="/__auth/login">Sign in</a> to set one.`));
  const { alerts, events } = await c98Alerts(String(user.id));
  const gd = await c97GoldDash().catch(() => null), R = (gd && gd.rows) || {};
  const cal = await c97Calendar().catch(() => null), names = c98MacroNames(cal);
  const opt = Object.keys(C98_SUBJ).map(k => `<option value="${k}">${c93Esc(C98_SUBJ[k].label)}${R[k] ? " (now " + c93Esc(R[k].value) + ")" : ""}</option>`).join("");
  const ev = events.length ? `<ul class="c98ev">${events.map(e => `<li>${e.seen ? "" : `<span class="new">New</span>`}${c93Esc(e.message)}<br><span class="c97s">Alert time: ${c93Esc(c97UkWhen(Date.parse(e.fired_at) || Date.now()))}</span></li>`).join("")}</ul><form method="post" action="/api/c98/alerts/seen" class="c98del"><button type="submit">Mark all as read</button></form>` : `<p class="c97note">Nothing has triggered yet.</p>`;
  const list = alerts.length ? `<div class="c98wrap"><table class="c97t"><thead><tr><th>Alert</th><th>Status</th><th></th></tr></thead><tbody>${alerts.map(a => {
    const what = a.kind === "macro" ? "When " + a.subject + " is released" : (C98_SUBJ[a.subject] ? C98_SUBJ[a.subject].label : a.subject) + " " + a.op + " " + c98Fmt(a.subject, Number(a.threshold));
    const stx = a.kind === "macro" ? (a.last_fired_at ? "Last sent " + c97UkWhen(Date.parse(a.last_fired_at)) : "Waiting for the release") : (a.armed ? "Watching" : "Triggered " + c97UkWhen(Date.parse(a.last_fired_at) || Date.now()) + "; resets when it crosses back");
    return `<tr><td><strong>${c93Esc(what)}</strong>${a.note ? `<span class="c97p">${c93Esc(a.note)}</span>` : ""}</td><td>${c93Esc(stx)}</td><td><form method="post" action="/api/c98/alerts/delete" class="c98del"><input type="hidden" name="id" value="${c93Esc(String(a.id))}"><button type="submit" aria-label="Delete alert: ${c93Esc(what)}">Delete</button></form></td></tr>`;
  }).join("")}</tbody></table></div>` : `<p class="c97note">You have no alerts yet.</p>`;
  const body = `<style>${C97_CSS}${C98_CSS}</style><section><div class="kicker">Your tools</div><h1>Alerts</h1><p class="dek">Get a note in the app when a price or level crosses a line you set, or when an official release comes out. Prices come from free delayed feeds and are checked about every five minutes, so an alert can arrive a few minutes after the move. Information only: an alert is not a recommendation.</p><p class="byline">${C93_EDITOR}</p></section>${c98Msg(u0)}` +
    `<section><h2>Triggered</h2>${ev}</section><section><h2>Your alerts (${alerts.length} of ${c98Limit(user)})</h2>${list}</section>` +
    `<section><h2>New price or level alert</h2><form method="post" action="/api/c98/alerts" class="c98f"><div class="c98row"><div><label for="c98s">Reading</label><select id="c98s" name="subject">${opt}</select></div><div><label for="c98o">When it goes</label><select id="c98o" name="op"><option value="above">above</option><option value="below">below</option></select></div><div><label for="c98t">Level</label><input id="c98t" name="threshold" inputmode="decimal" required placeholder="for example 4000"></div></div><div><label for="c98n">Note to yourself (optional)</label><input id="c98n" name="note" maxlength="140"></div><button type="submit">Add alert</button></form></section>` +
    (names.length ? `<section><h2>New release alert</h2><form method="post" action="/api/c98/alerts" class="c98f"><div><label for="c98m">Release</label><select id="c98m" name="subject">${names.map(n => `<option>${c93Esc(n)}</option>`).join("")}</select></div><input type="hidden" name="op" value="release"><button type="submit">Tell me when it is out</button><p class="c97note">Release alerts carry the official figure and the previous one, from the <a href="/calendar/">macro calendar</a> sources. There are no forecasts.</p></form></section>` : "") +
    `<section><p class="c97note">${C98_EMAIL_NOTE}</p></section>`;
  return c98Send(req, res, c93Shell({ title: "Alerts | The Dispatch Market", path: "/alerts/", desc, user, body }));
}
async function c98PortfolioPage(req, res, user, u0) {
  const st = await c98Status();
  const desc = "See how a mix of holdings leans on growth, gold, the US dollar and interest rates. Information only, not advice.";
  if (!st.portfolio) return c98Send(req, res, c98Gate("Portfolio X-ray", "/portfolio/", desc, user, "Portfolio X-ray is not switched on yet. Check back soon."), 404);
  if (!user) return c98Send(req, res, c98Gate("Portfolio X-ray", "/portfolio/", desc, user, `Portfolio X-ray is for signed-in readers, so your holdings stay in your account. <a href="/__auth/login">Sign in</a> to use it.`));
  const p = await c98Portfolio(String(user.id));
  const gd = await c97GoldDash().catch(() => null), R = (gd && gd.rows) || {};
  const assume = `<div class="c98wrap"><table class="c97t"><thead><tr><th>Holding type</th><th>Growth</th><th>US dollar</th><th>Gold</th><th>If rates rise 1 point</th></tr></thead><tbody>${Object.keys(C98_CLASSES).filter(k => k !== "other").map(k => { const c = C98_CLASSES[k]; return `<tr><td>${c93Esc(c.label)}</td><td>${c98Pct(c.macro)}</td><td>${c98Pct(c.usd)}</td><td>${c98Pct(c.gold)}</td><td>${c.rates > 0 ? "+" : ""}${c.rates}%</td></tr>`; }).join("")}</tbody></table></div><p class="c97note">Source: The Dispatch Market rule-of-thumb weights, set ${C98_ASOF}. They are rough round numbers for broad index-type holdings, not measured from your funds. Real funds differ: check each fund's factsheet for its actual currency mix and bond duration.</p>`;
  const body = `<style>${C97_CSS}${C98_CSS}</style><section><div class="kicker">Your tools</div><h1>Portfolio X-ray</h1><p class="dek">Paste or type what you hold and see how the mix leans on economic growth, gold, the US dollar and interest rates. Information only: this is not advice and makes no recommendation.</p><p class="byline">${C93_EDITOR}</p></section>${c98Msg(u0)}` +
    `<section><h2>Your mix</h2>${c98XrayHtml(p.holdings, p.at, R)}</section>` +
    `<section><h2>Holdings</h2><form method="post" action="/api/c98/portfolio" class="c98f"><label for="c98h">One holding per line: name, amount (any currency, or a percentage), and optionally a type. A CSV export works if the first two columns are name and value.</label><textarea id="c98h" name="csv" spellcheck="false" placeholder="FTSE 100 tracker, 4000&#10;Global shares fund, 6000&#10;Gilts fund, 2500&#10;Physical gold, 1000&#10;Cash savings, 1500">${c93Esc(c98HoldingsText(p.holdings))}</textarea><p class="c97note">Types we recognise from the name: UK, US, global and emerging-market shares; gilts, index-linked and corporate bonds; US Treasuries; gold, silver, property, crypto and cash. To set a type yourself, add one of: ${Object.keys(C98_CLASSES).join(", ")}.</p><button type="submit">Save and X-ray</button></form>${p.holdings.length ? `<form method="post" action="/api/c98/portfolio/delete" class="c98del"><button type="submit">Delete my holdings</button></form>` : ""}</section>` +
    `<section><h2>How the X-ray works</h2>${assume}</section>`;
  return c98Send(req, res, c93Shell({ title: "Portfolio X-ray | The Dispatch Market", path: "/portfolio/", desc, user, body }));
}
{
  const c98Route0 = c93Route;
  c93Route = async function (req, res) {
    if (req.method === "GET" || req.method === "HEAD") {
      let u0; try { u0 = new URL(req.url, "http://localhost"); } catch (e) { u0 = null; }
      const p = u0 ? u0.pathname : "";
      if (p === "/alerts" || p === "/portfolio" || p === "/alerts/" || p === "/portfolio/") {
        if (!p.endsWith("/")) { res.writeHead(301, { Location: p + "/" + (u0.search || "") }); res.end(); return true; }
        let user = await c96UserOf(req);
        if (user && req.c96PreviewOn) { req.c94Preview = p; user = null; }
        if (user) req.c94Signed = true;
        if (p === "/alerts/") await c98AlertsPage(req, res, user, u0); else await c98PortfolioPage(req, res, user, u0);
        return true;
      }
    }
    return c98Route0.apply(this, arguments);
  };
}
{
  const c98I0 = bb10iHandle0;
  bb10iHandle0 = async function c98Inner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (p.indexOf("/api/c98/") !== 0) return c98I0.apply(this, arguments);
    const m = req.method;
    try {
      if (p === "/api/c98/status" && (m === "GET" || m === "HEAD")) { const s = await c98Status(); return json(res, 200, { alerts: s.alerts, portfolio: s.portfolio, email: c98EmailOn(), emailNote: C98_EMAIL_NOTE }, { "Cache-Control": "no-store" }); }
      const st = await c98Status();
      const isA = p.indexOf("/api/c98/alerts") === 0, isP = p.indexOf("/api/c98/portfolio") === 0;
      if (!isA && !isP) return json(res, 404, { error: "Not found" }, { "Cache-Control": "no-store" });
      if ((isA && !st.alerts) || (isP && !st.portfolio)) return json(res, 404, { error: "Not switched on yet.", available: false }, { "Cache-Control": "no-store" });
      const user = await c96UserOf(req), back = isA ? "/alerts/" : "/portfolio/";
      if (!user) return json(res, 401, { error: "Sign in required." }, { "Cache-Control": "no-store" });
      if (c98Preview(req, user)) return json(res, m === "GET" ? 401 : 403, { error: m === "GET" ? "Sign in required." : "Guest preview is read-only.", preview: true }, { "Cache-Control": "no-store" });
      const uid = String(user.id);
      if (m === "GET" || m === "HEAD") {
        if (p === "/api/c98/alerts") { const a = await c98Alerts(uid); return json(res, 200, { available: true, alerts: a.alerts, events: a.events, unseen: a.events.filter(e => !e.seen).length, limit: c98Limit(user), email: c98EmailOn(), emailNote: C98_EMAIL_NOTE, subjects: Object.keys(C98_SUBJ).map(k => ({ id: k, label: C98_SUBJ[k].label, kind: C98_SUBJ[k].kind })) }, { "Cache-Control": "no-store" }); }
        if (p === "/api/c98/portfolio") { const pf = await c98Portfolio(uid); const x = c98Xray(pf.holdings); return json(res, 200, { available: true, holdings: pf.holdings, xray: x, savedUk: pf.at ? c97UkWhen(pf.at) : null, note: "Information only. Not investment advice." }, { "Cache-Control": "no-store" }); }
        return json(res, 405, { error: "Use POST." }, { "Cache-Control": "no-store" });
      }
      if (m !== "POST") return json(res, 405, { error: "Use GET or POST." }, { "Cache-Control": "no-store" });
      if (!c98SameOrigin(req)) return json(res, 403, { error: "Changes must come from this site." }, { "Cache-Control": "no-store" });
      const b = await c98Body(req);
      if (p === "/api/c98/alerts") { const r = await c98AlertCreate(user, b.v); return c98Reply(req, res, b, r.status, r.body, back); }
      if (p === "/api/c98/alerts/delete") { const id = Math.trunc(Number(b.v.id)); if (!(id > 0)) return c98Reply(req, res, b, 400, { error: "Missing alert." }, back); await c98Db()`DELETE FROM dispatch_alerts WHERE id=${id} AND user_id=${uid}`; return c98Reply(req, res, b, 200, { ok: true }, back); }
      if (p === "/api/c98/alerts/seen") { await c98Db()`UPDATE dispatch_alert_events SET seen=TRUE WHERE user_id=${uid} AND seen=FALSE`; return c98Reply(req, res, b, 200, { ok: true }, back); }
      if (p === "/api/c98/portfolio") {
        const h = Array.isArray(b.v.holdings) ? b.v.holdings.slice(0, 50).map(x => ({ name: String(x && x.name || "").replace(/["<>]/g, "").slice(0, 60), amount: c98Num(x && x.amount), c0: x && x.cls })).filter(x => x.name && x.amount > 0).map(x => ({ name: x.name, amount: x.amount, cls: c98Classify(x.name, x.c0) })) : c98Parse(b.v.csv);
        if (!h.length) return c98Reply(req, res, b, 400, { error: "Add at least one line with a name and an amount, for example: Global shares fund, 6000" }, back);
        await c98Db()`INSERT INTO dispatch_portfolio (user_id, holdings, updated_at) VALUES (${uid}, ${JSON.stringify(h)}::jsonb, now()) ON CONFLICT (user_id) DO UPDATE SET holdings=EXCLUDED.holdings, updated_at=now()`;
        return c98Reply(req, res, b, 200, { ok: true, holdings: h, xray: c98Xray(h) }, back);
      }
      if (p === "/api/c98/portfolio/delete") { await c98Db()`DELETE FROM dispatch_portfolio WHERE user_id=${uid}`; return c98Reply(req, res, b, 200, { ok: true }, back); }
      return json(res, 404, { error: "Not found" }, { "Cache-Control": "no-store" });
    } catch (e) {
      console.error("[c98]", p, e && e.message);
      if (e && e.code === "C98_BIG") return json(res, 413, { error: "Too much text." }, { "Cache-Control": "no-store" });
      return json(res, 503, { error: "Could not reach your saved data. Try again shortly." }, { "Cache-Control": "no-store" });
    }
  };
}
