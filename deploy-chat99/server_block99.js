// chat99: SEC EDGAR deep-dives for any US filer, a filings screener, and charts under Ask answers.
// SEC calls only when DISPATCH_SEC_UA is set, through the existing bb11SecGet (shared SEC limiter, UA read at call time).
// Every SEC download (tickers list, company facts, screener frames) counts against ONE daily cap of 25, kept in the
// existing bb11:sec_downloads counter (same UK day, same row, shared with the Capital Sustainability Monitor).
// Results are kept in the existing dispatch_openbb_research_cache table (no new tables, no DDL).
// Information only: figures as filed with the SEC. Not investment advice. Capital at risk.
const C99_CAP = 25, C99_USER_DAY = 5;
const C99_DD_TTL = 7 * 86400, C99_SCR_TTL = 40 * 86400, C99_TK_TTL = 7 * 86400;
const C99_SRC = "SEC EDGAR XBRL company facts (data.sec.gov)";
const C99_MEM = { tk: null, dd: new Map(), scr: null, user: new Map(), fl: new Map() };
function c99Db() { try { return c98Db(); } catch (e) { return null; } }
function c99Uk(ms) { try { return c97UkWhen(ms); } catch (e) { return new Date(ms).toISOString().slice(0, 16).replace("T", " ") + " UTC"; } }
async function c99CacheGet(k) {
  const db = c99Db(); if (!db) return null;
  try {
    const r = await withTimeout(db`SELECT value FROM dispatch_openbb_research_cache WHERE cache_key = ${k} AND expires_at > NOW() LIMIT 1`, 3000, "c99 cache read timed out");
    let v = r && r[0] && r[0].value; if (typeof v === "string") v = JSON.parse(v); return v || null;
  } catch (e) { return null; }
}
async function c99CachePut(k, v, ttlSec) {
  const db = c99Db(); if (!db) return;
  try { await withTimeout(db`INSERT INTO dispatch_openbb_research_cache (cache_key, value, expires_at, updated_at) VALUES (${k}, ${JSON.stringify(v)}::jsonb, NOW() + make_interval(secs => ${ttlSec}), NOW()) ON CONFLICT (cache_key) DO UPDATE SET value = EXCLUDED.value, expires_at = EXCLUDED.expires_at, updated_at = NOW()`, 5000, "c99 cache save timed out"); } catch (e) { /* best effort */ }
}
async function c99Used() { try { await bb11Ensure(); const st = bb11St, d = bb11UkDay(bb11Now()); return st.sec.day === d ? Number(st.sec.facts_today || 0) : 0; } catch (e) { return 0; } }
async function c99Take() {                                     // one slot of the shared daily SEC download cap
  await bb11Ensure(); const st = bb11St, day = bb11UkDay(bb11Now());
  if (st.sec.day !== day) { st.sec.day = day; st.sec.facts_today = 0; }
  if (Number(st.sec.facts_today || 0) >= C99_CAP) return false;
  st.sec.facts_today = Number(st.sec.facts_today || 0) + 1; bb11Touch(st);
  bb11Persist(st).catch(function () {});
  return true;
}
function c99Err(code, msg) { const e = new Error(msg); e.code = code; return e; }
async function c99Sec(url, maxBytes) {
  const ua = bb11Ua(); if (!ua) throw c99Err("NO_UA", "SEC downloads are switched off on this site for now.");
  if (!(await c99Take())) throw c99Err("CAP", "Today's SEC download limit (" + C99_CAP + " a day) is used up. It resets at midnight UK time.");
  const r = await bb11SecGet(url, ua, null, 60000, maxBytes || 30 * 1024 * 1024);
  return JSON.parse(r.text);
}
async function c99Tickers(allowDownload) {
  if (C99_MEM.tk && Date.now() - C99_MEM.tk.at < C99_TK_TTL * 1000) return C99_MEM.tk;
  const c = await c99CacheGet("c99:tickers"); if (c && Array.isArray(c.rows)) { C99_MEM.tk = c; return c; }
  if (!allowDownload) return null;
  const j = await c99Sec("https://www.sec.gov/files/company_tickers.json", 4 * 1024 * 1024);
  const rows = Object.keys(j).map(k => j[k]).filter(x => x && x.ticker && x.cik_str).map(x => [String(x.ticker).toUpperCase(), Number(x.cik_str), String(x.title || "").slice(0, 90)]);
  const v = { at: Date.now(), rows }; C99_MEM.tk = v; await c99CachePut("c99:tickers", v, C99_TK_TTL); return v;
}
function c99Find(tk, t) { t = String(t || "").toUpperCase(); return tk && tk.rows.find(r => r[0] === t) || null; }
const C99_M = [
  ["rev", "Revenue", "Money the company took in from customers over the year.", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"], "USD", false],
  ["op", "Operating profit", "Profit from the main business, before interest and tax.", ["OperatingIncomeLoss"], "USD", false],
  ["ni", "Net profit", "What was left for shareholders after all costs, interest and tax.", ["NetIncomeLoss", "ProfitLoss"], "USD", false],
  ["ocf", "Cash from operations", "Cash the business actually generated in the year.", ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"], "USD", false],
  ["capex", "Spending on property and equipment", "Cash spent on buildings, data centres, machines and similar.", ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"], "USD", false],
  ["cash", "Cash at year end", "Cash and near-cash on the balance sheet at the year end.", ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"], "USD", true],
  ["debt", "Long-term debt", "Borrowing due after more than a year, at the year end.", ["LongTermDebt", "LongTermDebtNoncurrent"], "USD", true],
  ["eq", "Shareholders' equity", "Assets minus liabilities: the book value owned by shareholders.", ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], "USD", true],
  ["eps", "Earnings per share (diluted)", "Net profit divided by the number of shares, counting options.", ["EarningsPerShareDiluted"], "USD/shares", true]
];
function c99Annual(G, names, unit, instant) {
  let best = null;
  for (const n of names) {
    const u = G[n] && G[n].units && G[n].units[unit]; if (!Array.isArray(u)) continue;
    const by = new Map();
    for (const x of u) {
      if (!/^10-K/.test(String(x.form || "")) || typeof x.val !== "number" || !x.end) continue;
      if (instant) { if (x.fp !== "FY") continue; }
      else { if (!x.start) continue; const d = (Date.parse(x.end) - Date.parse(x.start)) / 864e5; if (!(d > 350 && d < 380)) continue; }
      const p = by.get(x.end); if (!p || String(x.filed) > String(p.filed)) by.set(x.end, x);
    }
    if (!by.size) continue;
    const rows = Array.from(by.values()).sort((a, b) => a.end < b.end ? -1 : 1).slice(-5).map(x => ({ end: x.end, val: x.val, form: x.form, filed: x.filed, accn: x.accn }));
    if (!best || rows[rows.length - 1].end > best.rows[best.rows.length - 1].end) best = { concept: n, rows };
  }
  return best;
}
function c99FromFacts(t, cik, j) {
  const G = (j && j.facts && j.facts["us-gaap"]) || {}, m = {};
  C99_M.forEach(([k, label, plain, names, unit, inst]) => { const a = c99Annual(G, names, unit, inst); if (a) m[k] = { label, plain, concept: a.concept, rows: a.rows }; });
  if (m.ocf && m.capex) { const cx = new Map(m.capex.rows.map(r => [r.end, r.val])); const rows = m.ocf.rows.filter(r => cx.has(r.end)).map(r => ({ end: r.end, val: r.val - cx.get(r.end), form: r.form, filed: r.filed, accn: r.accn })); if (rows.length) m.fcf = { label: "Free cash flow", plain: "Cash from operations minus spending on property and equipment.", concept: "computed", rows }; }
  return { v: 1, ticker: t, cik, name: String((j && j.entityName) || t).slice(0, 90), at: Date.now(), metrics: m, ok: !!(m.rev || m.ni) };
}
async function c99Deep(t, allowDownload) {
  t = String(t || "").toUpperCase(); if (!/^[A-Z][A-Z0-9.\-]{0,9}$/.test(t)) throw c99Err("BAD", "That does not look like a US ticker.");
  const mem = C99_MEM.dd.get(t); if (mem && Date.now() - mem.at < C99_DD_TTL * 1000) return mem;
  const c = await c99CacheGet("c99:dd:" + t); if (c && c.metrics) { C99_MEM.dd.set(t, c); return c; }
  if (!allowDownload) return null;
  if (C99_MEM.fl.has(t)) return C99_MEM.fl.get(t);
  const p = (async () => {
    const tk = await c99Tickers(true), row = c99Find(tk, t);
    if (!row) throw c99Err("UNKNOWN", "The SEC's list of company tickers does not include " + t + ".");
    const j = await c99Sec("https://data.sec.gov/api/xbrl/companyfacts/CIK" + ("0000000000" + row[1]).slice(-10) + ".json", 30 * 1024 * 1024);
    const dd = c99FromFacts(t, row[1], j); if (!dd.name || dd.name === t) dd.name = row[2] || t;
    C99_MEM.dd.set(t, dd); if (C99_MEM.dd.size > 200) C99_MEM.dd.delete(C99_MEM.dd.keys().next().value);
    await c99CachePut("c99:dd:" + t, dd, C99_DD_TTL);
    try { const idx = (await c99CacheGet("c99:dd-index")) || { list: [] }; idx.list = [[t, dd.name, dd.at]].concat((idx.list || []).filter(x => x[0] !== t)).slice(0, 300); await c99CachePut("c99:dd-index", idx, 365 * 86400); } catch (e) {}
    return dd;
  })();
  C99_MEM.fl.set(t, p); try { return await p; } finally { C99_MEM.fl.delete(t); }
}
function c99Money(v) { if (typeof v !== "number") return "n/a"; const a = Math.abs(v), s = v < 0 ? "−" : ""; return a >= 1e9 ? s + "$" + (a / 1e9).toFixed(a >= 1e11 ? 0 : 1) + "bn" : a >= 1e6 ? s + "$" + (a / 1e6).toFixed(0) + "m" : s + "$" + Math.round(a).toLocaleString("en-GB"); }
function c99Val(k, v) { return k === "eps" ? (v < 0 ? "−$" : "$") + Math.abs(v).toFixed(2) : c99Money(v); }
function c99Year(end) { return "Year to " + new Date(end + "T00:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }); }
function c99Bars(title, rows, k) {                             // small server-side SVG bar chart, no script
  if (!rows || rows.length < 2) return "";
  const W = 560, H = 180, pad = 28, n = rows.length, bw = (W - pad * 2) / n * 0.6, max = Math.max(...rows.map(r => Math.abs(r.val))) || 1, hasNeg = rows.some(r => r.val < 0);
  const zero = hasNeg ? H / 2 : H - pad, scale = (hasNeg ? H / 2 - pad : H - pad * 2) / max;
  const bars = rows.map((r, i) => { const x = pad + (W - pad * 2) / n * (i + 0.2), h = Math.abs(r.val) * scale, y = r.val >= 0 ? zero - h : zero; return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(1, h).toFixed(1)}" class="${r.val < 0 ? "neg" : "pos"}"><title>${c93Esc(c99Year(r.end) + ": " + c99Val(k, r.val))}</title></rect><text x="${(x + bw / 2).toFixed(1)}" y="${H - 6}" text-anchor="middle">${r.end.slice(0, 4)}</text><text x="${(x + bw / 2).toFixed(1)}" y="${(r.val >= 0 ? y - 4 : y + h + 12).toFixed(1)}" text-anchor="middle" class="v">${c93Esc(c99Val(k, r.val))}</text>`; }).join("");
  return `<figure class="c99fig"><figcaption>${c93Esc(title)}</figcaption><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${c93Esc(title)}"><line x1="${pad}" x2="${W - pad}" y1="${zero}" y2="${zero}" class="ax"/>${bars}</svg></figure>`;
}
const C99_CSS = ".c99fig{margin:14px 0;max-width:600px}.c99fig figcaption{font-weight:600;margin-bottom:4px}.c99fig svg{width:100%;height:auto;display:block}.c99fig rect.pos{fill:#1f6f5c}.c99fig rect.neg{fill:#b4483c}.c99fig text{font:11px system-ui,sans-serif;fill:currentColor}.c99fig .ax{stroke:currentColor;opacity:.35}.c99wrap{overflow-x:auto}.c99f{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;margin:10px 0}.c99f input,.c99f select{font:inherit;padding:8px;border:1px solid #8a94a3;border-radius:6px;background:transparent;color:inherit;min-height:40px}.c99f button{font:inherit;padding:8px 14px;border-radius:6px;border:0;background:#1f6f5c;color:#fff;min-height:40px;cursor:pointer}.c99f label{display:block;font-size:13px}.c99t td.v,.c99t th.v{text-align:right;white-space:nowrap}html.c97-dark .c99fig rect.pos{fill:#4fb59a}html.c97-dark .c99fig rect.neg{fill:#e07b6f}@media (prefers-color-scheme:dark){html.c97-system .c99fig rect.pos{fill:#4fb59a}html.c97-system .c99fig rect.neg{fill:#e07b6f}}";
function c99DeepHtml(dd) {
  const m = dd.metrics, keys = ["rev", "op", "ni", "ocf", "capex", "fcf", "cash", "debt", "eq", "eps"].filter(k => m[k]);
  const ends = Array.from(new Set([].concat(...keys.map(k => m[k].rows.map(r => r.end))))).sort().slice(-5);
  if (!keys.length || !ends.length) return `<p class="c97note">${c93Esc(dd.name)} does not report these items in US-GAAP annual (10-K) data, for example because it files under international rules (IFRS, form 20-F). Nothing is shown rather than guessing.</p>`;
  const filed = ends.map(e => { for (const k of keys) { const r = m[k].rows.find(x => x.end === e); if (r) return r.form + " filed " + r.filed; } return ""; });
  const head = `<tr><th>Item</th>${ends.map(e => `<th class="v">${c93Esc(c99Year(e))}</th>`).join("")}</tr>`;
  const body = keys.map(k => `<tr><td><strong>${c93Esc(m[k].label)}</strong><span class="c97p">${c93Esc(m[k].plain)}</span></td>${ends.map(e => { const r = m[k].rows.find(x => x.end === e); return `<td class="v">${r ? c93Esc(c99Val(k, r.val)) : "–"}</td>`; }).join("")}</tr>`).join("") + `<tr><td><span class="c97s">Filing</span></td>${filed.map(f => `<td class="v"><span class="c97s">${c93Esc(f)}</span></td>`).join("")}</tr>`;
  const r = m.rev && m.rev.rows, rl = r && r[r.length - 1], rp = r && r[r.length - 2];
  const op = m.op && m.op.rows.find(x => rl && x.end === rl.end);
  const lines = [];
  if (rl && rp && rp.val > 0) lines.push(`Revenue ${rl.val >= rp.val ? "grew" : "fell"} ${Math.abs((rl.val / rp.val - 1) * 100).toFixed(1)}% in the ${c93Esc(c99Year(rl.end).replace("Year", "year"))}.`);
  if (rl && op && rl.val > 0) lines.push(`The operating margin was ${(op.val / rl.val * 100).toFixed(1)}%: ${c93Esc(c99Money(op.val))} of operating profit on ${c93Esc(c99Money(rl.val))} of revenue.`);
  const f = m.fcf && m.fcf.rows[m.fcf.rows.length - 1]; if (f) lines.push(`Free cash flow was ${c93Esc(c99Money(f.val))} in the ${c93Esc(c99Year(f.end).replace("Year", "year"))}.`);
  const src = `<p class="c97s">Source: ${C99_SRC}, annual figures as filed in each 10-K (filing dates in the last row). Downloaded ${c93Esc(c99Uk(dd.at))}. Free cash flow is our arithmetic: cash from operations minus spending on property and equipment.</p>`;
  return (lines.length ? `<ul class="c99sum">${lines.map(l => `<li>${l}</li>`).join("")}</ul>` : "") +
    c99Bars("Revenue", m.rev && m.rev.rows, "rev") + c99Bars("Net profit", m.ni && m.ni.rows, "ni") + c99Bars("Free cash flow", m.fcf && m.fcf.rows, "fcf") +
    `<div class="c99wrap"><table class="c97t c99t"><thead>${head}</thead><tbody>${body}</tbody></table></div>` + src;
}
function c99UserOk(uid) { const d = bb11UkDay(bb11Now()), k = d + ":" + uid, n = C99_MEM.user.get(k) || 0; if (n >= C99_USER_DAY) return false; C99_MEM.user.set(k, n + 1); if (C99_MEM.user.size > 5000) C99_MEM.user.clear(); return true; }
function c99Preview(req, user) { try { return c98Preview(req, user); } catch (e) { return false; } }
async function c99HubPage(req, res, user, u0) {
  const used = await c99Used(), on = !!bb11Ua(), idx = (await c99CacheGet("c99:dd-index")) || { list: [] }, msg = u0.searchParams.get("e");
  const mon = (typeof BB11_TICKERS !== "undefined" ? BB11_TICKERS : []).map(t => `<a href="/research/sec/${t}/">${t}</a>`).join(" · ");
  const recent = (idx.list || []).slice(0, 40).map(x => `<li><a href="/research/sec/${c93Esc(x[0])}/">${c93Esc(x[1])} (${c93Esc(x[0])})</a> <span class="c97s">downloaded ${c93Esc(c99Uk(x[2]))}</span></li>`).join("");
  const body = `<style>${C97_CSS}${C99_CSS}</style><section><div class="kicker">Research</div><h1>Company filings</h1><p class="dek">Five years of annual figures for any US-listed company, straight from its 10-K filings with the US Securities and Exchange Commission (SEC), with charts and plain-English notes. Information only.</p><p class="byline">${C93_EDITOR}</p></section>` +
    (msg ? `<p class="c97note" role="alert">${c93Esc(msg.slice(0, 200))}</p>` : "") +
    `<section><h2>Look up a company</h2><form method="get" action="/research/sec/go" class="c99f"><div><label for="c99t">US ticker</label><input id="c99t" name="t" maxlength="10" autocomplete="off" required placeholder="for example KO"></div><button type="submit">Open</button></form>` +
    `<p class="c97s">${on ? `SEC downloads used today: ${used} of ${C99_CAP} (shared across the site; resets at midnight UK time). Companies already downloaded open without using one.` : "SEC downloads are switched off on this site for now, so only companies already downloaded can be shown."}</p></section>` +
    `<section><h2>Screener</h2><p><a href="/research/sec/screener/">Screen every US filer</a> by revenue, growth and margins from their latest annual filings.</p></section>` +
    (recent ? `<section><h2>Recently downloaded</h2><ul>${recent}</ul></section>` : "") +
    (mon ? `<section><h2>In the Capital Sustainability Monitor</h2><p>${mon}</p></section>` : "");
  return c98Send(req, res, c93Shell({ title: "Company filings | The Dispatch Market", path: "/research/sec/", desc: "Five years of SEC-filed annual figures for any US-listed company, with charts and plain English.", user, body }));
}
async function c99DeepPage(req, res, user, t, u0) {
  let dd = null, err = u0.searchParams.get("e");
  try { dd = await c99Deep(t, false); } catch (e) { err = err || e.message; }
  const title = dd ? dd.name + " (" + t + ")" : t;
  let main;
  if (dd) main = c99DeepHtml(dd);
  else if (!bb11Ua()) main = `<p class="c97note">We have not downloaded ${c93Esc(t)} yet, and SEC downloads are switched off on this site for now.</p>`;
  else if (!user) main = `<p class="c97note">We have not downloaded ${c93Esc(t)} yet. <a href="/__auth/login">Sign in</a> to fetch its filings from the SEC (free; uses one of today's ${C99_CAP} site-wide downloads).</p>`;
  else if (c99Preview(req, user)) main = `<p class="c97note">Guest preview is read-only.</p>`;
  else main = `<p class="c97note">We have not downloaded ${c93Esc(t)} yet. Fetching uses one of today's ${C99_CAP} site-wide SEC downloads (${await c99Used()} used so far).</p><form method="post" action="/api/c99/sec/fetch" class="c99f"><input type="hidden" name="t" value="${c93Esc(t)}"><button type="submit">Fetch ${c93Esc(t)} filings from the SEC</button></form>`;
  const body = `<style>${C97_CSS}${C99_CSS}</style><section><div class="kicker"><a href="/research/sec/">Company filings</a></div><h1>${c93Esc(title)}</h1>${dd ? `<p class="dek">Annual figures as filed with the SEC${dd.cik ? ", CIK " + c93Esc(String(dd.cik)) : ""}. Information only, not a recommendation.</p>` : ""}<p class="byline">${C93_EDITOR}</p></section>` +
    (err ? `<p class="c97note" role="alert">${c93Esc(String(err).slice(0, 200))}</p>` : "") + `<section>${main}</section>`;
  return c98Send(req, res, c93Shell({ title: title + " filings | The Dispatch Market", path: "/research/sec/" + t + "/", desc: "SEC-filed annual figures for " + title + ", with charts and plain English.", user, body }));
}
// ── screener: SEC XBRL frames, one calendar year across every filer ──
function c99ScrYear(now) { const d = new Date(now); return d.getUTCMonth() >= 4 ? d.getUTCFullYear() - 1 : d.getUTCFullYear() - 2; }
async function c99Frame(tag, y) { const j = await c99Sec("https://data.sec.gov/api/xbrl/frames/us-gaap/" + tag + "/USD/CY" + y + ".json", 20 * 1024 * 1024); const m = new Map(); (j.data || []).forEach(x => { if (x && typeof x.val === "number") m.set(Number(x.cik), { v: x.val, n: x.entityName, a: x.accn, e: x.end }); }); return m; }
async function c99ScrBuild() {
  const y = c99ScrYear(bb11Now());
  const need = 7 + (await c99Tickers(false) ? 0 : 1);
  if (C99_CAP - (await c99Used()) < need) throw c99Err("CAP", "Building the screener needs " + need + " SEC downloads and fewer than that are left today. Try after midnight UK time.");
  const tk = await c99Tickers(true), byCik = new Map(); tk.rows.forEach(r => { if (!byCik.has(r[1])) byCik.set(r[1], r[0]); });
  const r1 = await c99Frame("Revenues", y), r2 = await c99Frame("RevenueFromContractWithCustomerExcludingAssessedTax", y);
  const p1 = await c99Frame("Revenues", y - 1), p2 = await c99Frame("RevenueFromContractWithCustomerExcludingAssessedTax", y - 1);
  const op = await c99Frame("OperatingIncomeLoss", y), ni = await c99Frame("NetIncomeLoss", y), ocf = await c99Frame("NetCashProvidedByUsedInOperatingActivities", y);
  const ciks = new Set([...r1.keys(), ...r2.keys()]), rows = [];
  ciks.forEach(c => {
    const rv = r1.get(c) || r2.get(c); if (!rv || rv.v < 1e7) return;
    const pv = r1.get(c) ? p1.get(c) : p2.get(c); const o = op.get(c), n = ni.get(c), cf = ocf.get(c);
    rows.push({ c, t: byCik.get(c) || null, n: String(rv.n || "").slice(0, 80), r: rv.v, g: pv && pv.v > 0 ? +((rv.v / pv.v - 1) * 100).toFixed(1) : null, om: o ? +(o.v / rv.v * 100).toFixed(1) : null, nm: n ? +(n.v / rv.v * 100).toFixed(1) : null, cf: cf ? cf.v : null, e: rv.e });
  });
  rows.sort((a, b) => b.r - a.r);
  const v = { v: 1, year: y, at: Date.now(), rows }; C99_MEM.scr = v; await c99CachePut("c99:screener", v, C99_SCR_TTL); return v;
}
async function c99Scr() { if (C99_MEM.scr) return C99_MEM.scr; const c = await c99CacheGet("c99:screener"); if (c && Array.isArray(c.rows)) C99_MEM.scr = c; return C99_MEM.scr; }
function c99Filter(s, q) {
  const num = (k, d) => { const n = Number(q.get(k)); return q.get(k) != null && q.get(k) !== "" && Number.isFinite(n) ? n : d; };
  const minR = num("min_rev", 0) * 1e6, minG = num("min_growth", null), minM = num("min_margin", null), txt = String(q.get("q") || "").trim().toLowerCase().slice(0, 40);
  const sort = ["r", "g", "om", "nm"].indexOf(q.get("sort")) >= 0 ? q.get("sort") : "r";
  let rows = s.rows.filter(r => r.r >= minR && (minG == null || (r.g != null && r.g >= minG)) && (minM == null || (r.om != null && r.om >= minM)) && (!txt || r.n.toLowerCase().indexOf(txt) >= 0 || (r.t && r.t.toLowerCase() === txt)));
  rows = rows.slice().sort((a, b) => (b[sort] == null ? -1e18 : b[sort]) - (a[sort] == null ? -1e18 : a[sort]));
  return { total: rows.length, rows: rows.slice(0, 100), sort, minR: minR / 1e6, minG, minM, txt };
}
async function c99ScrPage(req, res, user, u0) {
  const s = await c99Scr(), q = u0.searchParams, msg = q.get("e"), admin = user && c96IsAdmin(user) && !c99Preview(req, user);
  let main;
  if (!s) main = `<p class="c97note">The screener has not been built yet.${admin ? "" : " Check back soon."}</p>`;
  else {
    const f = c99Filter(s, q), pct = v => v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1) + "%", pm = v => v == null ? "–" : (v < 0 ? "−" : "") + Math.abs(v).toFixed(1) + "%";
    const opt = (v, l) => `<option value="${v}"${f.sort === v ? " selected" : ""}>${l}</option>`;
    main = `<form method="get" action="/research/sec/screener/" class="c99f"><div><label for="c99q">Name or ticker</label><input id="c99q" name="q" value="${c93Esc(f.txt)}" maxlength="40"></div><div><label for="c99r">Revenue at least ($m)</label><input id="c99r" name="min_rev" inputmode="decimal" value="${f.minR || ""}" size="7"></div><div><label for="c99g">Growth at least (%)</label><input id="c99g" name="min_growth" inputmode="decimal" value="${f.minG == null ? "" : f.minG}" size="5"></div><div><label for="c99m">Operating margin at least (%)</label><input id="c99m" name="min_margin" inputmode="decimal" value="${f.minM == null ? "" : f.minM}" size="5"></div><div><label for="c99s">Sort by</label><select id="c99s" name="sort">${opt("r", "Revenue")}${opt("g", "Revenue growth")}${opt("om", "Operating margin")}${opt("nm", "Net margin")}</select></div><button type="submit">Screen</button></form>` +
      `<p class="c97s">${f.total.toLocaleString("en-GB")} companies match${f.total > 100 ? "; showing the first 100" : ""}.</p>` +
      `<div class="c99wrap"><table class="c97t c99t"><thead><tr><th>Company</th><th class="v">Revenue</th><th class="v">Growth</th><th class="v">Operating margin</th><th class="v">Net margin</th></tr></thead><tbody>${f.rows.map(r => `<tr><td>${r.t ? `<a href="/research/sec/${c93Esc(r.t)}/">${c93Esc(r.n)}</a> <span class="c97s">${c93Esc(r.t)}</span>` : c93Esc(r.n)}</td><td class="v">${c93Esc(c99Money(r.r))}</td><td class="v">${pct(r.g)}</td><td class="v">${pm(r.om)}</td><td class="v">${pm(r.nm)}</td></tr>`).join("")}</tbody></table></div>` +
      `<p class="c97s">Source: SEC EDGAR XBRL frames (data.sec.gov), calendar year ${s.year} as reported in 10-K filings; the SEC lines up each company's fiscal year with the nearest calendar year. Built ${c93Esc(c99Uk(s.at))}. Growth compares with ${s.year - 1}. Margins are our arithmetic on the filed figures. Companies that report under international rules, or use other revenue labels, are missing.</p>` +
      `<p class="c97s">Revenue: money taken in from customers. Operating margin: operating profit as a share of revenue. Net margin: net profit as a share of revenue. A screen is a starting point for reading filings, not a recommendation.</p>`;
  }
  const adminBox = admin ? `<section><h2>Admin</h2><form method="post" action="/api/c99/screener/build" class="c99f"><button type="submit">${s ? "Rebuild" : "Build"} the screener (uses 7 or 8 of today's ${C99_CAP} SEC downloads; ${await c99Used()} used)</button></form></section>` : "";
  const body = `<style>${C97_CSS}${C99_CSS}</style><section><div class="kicker"><a href="/research/sec/">Company filings</a></div><h1>Filings screener</h1><p class="dek">Every US filer's revenue, growth and margins from its latest full-year SEC filings. Information only.</p><p class="byline">${C93_EDITOR}</p></section>` + (msg ? `<p class="c97note" role="alert">${c93Esc(msg.slice(0, 200))}</p>` : "") + `<section>${main}</section>` + adminBox;
  return c98Send(req, res, c93Shell({ title: "Filings screener | The Dispatch Market", path: "/research/sec/screener/", desc: "Screen every US filer by revenue, growth and margins from SEC filings.", user, body }));
}
// ── chart data for Ask answers ──
async function c99Chart(k) {
  const isGold = k === "gold";
  if (!isGold && !/^[A-Z][A-Z0-9.\-]{0,9}$/.test(k)) return null;
  const r = await fetchYahooChart(isGold ? "GC=F" : k, "6mo", "1d");
  const res0 = r && !r.unavailable && r.data && r.data.chart && r.data.chart.result && r.data.chart.result[0]; if (!res0) return null;
  const ts = res0.timestamp || [], cl = (res0.indicators && res0.indicators.quote && res0.indicators.quote[0] && res0.indicators.quote[0].close) || [];
  const pts = []; ts.forEach((t, i) => { if (typeof cl[i] === "number") pts.push([t * 1000, +cl[i].toFixed(2)]); });
  if (pts.length < 10) return null;
  const meta = res0.meta || {}, cur = meta.currency || "USD";
  const name = isGold ? "Gold futures price, US$ per troy ounce (COMEX, nearest contract)" : String(meta.longName || meta.shortName || k).slice(0, 80) + " share price (" + cur + ")";
  const first = pts[0][1], last = pts[pts.length - 1][1], ch = (last / first - 1) * 100;
  let dd = null; try { if (!isGold) dd = await c99Deep(k, false); } catch (e) {}
  return { key: k, title: name, points: pts, source: "Yahoo Finance chart data, daily closes, delayed", asOf: "as of " + c99Uk(pts[pts.length - 1][0]), plain: "Daily closing prices over the last six months: " + (ch >= 0 ? "up " : "down ") + Math.abs(ch).toFixed(1) + "% from " + first.toLocaleString("en-GB") + " to " + last.toLocaleString("en-GB") + ".", filings: dd ? "/research/sec/" + k + "/" : null };
}
{
  const c99R0 = c93Route;
  c93Route = async function (req, res) {
    let u0 = null; try { u0 = new URL(req.url || "/", "http://localhost"); } catch (e) {}
    const p = u0 ? u0.pathname : "";
    if (u0 && (req.method === "GET" || req.method === "HEAD") && p.indexOf("/research/sec") === 0) {
      if (p === "/research/sec") { res.writeHead(301, { Location: "/research/sec/" }); return res.end(); }
      let user = null; try { user = await c96UserOf(req); if (user && req.c96PreviewOn) user = null; } catch (e) {}
      try {
        if (p === "/research/sec/") return await c99HubPage(req, res, user, u0);
        if (p === "/research/sec/go") { const t = String(u0.searchParams.get("t") || "").trim().toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 10); res.writeHead(302, { Location: t ? "/research/sec/" + t + "/" : "/research/sec/" }); return res.end(); }
        if (p === "/research/sec/screener/") return await c99ScrPage(req, res, user, u0);
        const m = /^\/research\/sec\/([A-Za-z][A-Za-z0-9.\-]{0,9})\/?$/.exec(p);
        if (m) { const t = m[1].toUpperCase(); if (p !== "/research/sec/" + t + "/") { res.writeHead(301, { Location: "/research/sec/" + t + "/" }); return res.end(); } return await c99DeepPage(req, res, user, t, u0); }
      } catch (e) { console.error("[c99]", p, e && e.message); }
    }
    return c99R0.apply(this, arguments);
  };
}
{
  const c99I0 = bb10iHandle0;
  bb10iHandle0 = async function c99Inner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (p.indexOf("/api/c99/") !== 0) return c99I0.apply(this, arguments);
    const m = req.method, H = { "Cache-Control": "no-store" };
    try {
      if (p === "/api/c99/status" && m === "GET") return json(res, 200, { sec: !!bb11Ua(), used: await c99Used(), cap: C99_CAP, screener: !!(await c99Scr()) }, H);
      if (p === "/api/c99/chart" && m === "GET") {
        const k0 = String(new URL(req.url, "http://localhost").searchParams.get("k") || "").trim();
        const k = k0.toLowerCase() === "gold" ? "gold" : k0.toUpperCase();
        const c = await c99Chart(k); return c ? json(res, 200, c, { "Cache-Control": "public, max-age=600" }) : json(res, 404, { error: "No chart for that." }, H);
      }
      if (p.indexOf("/api/c99/sec/") === 0 && m === "GET") {
        const t = decodeURIComponent(p.slice("/api/c99/sec/".length)).toUpperCase();
        const dd = await c99Deep(t, false); return dd ? json(res, 200, Object.assign({ source: C99_SRC, downloadedUk: c99Uk(dd.at), note: "Information only. Not investment advice. Capital at risk." }, dd), H) : json(res, 404, { error: "Not downloaded yet.", ticker: t }, H);
      }
      if (m !== "POST") return json(res, 404, { error: "Not found" }, H);
      if (!c98SameOrigin(req)) return json(res, 403, { error: "Changes must come from this site." }, H);
      const user = await c96UserOf(req), b = await c98Body(req);
      if (!user) return json(res, 401, { error: "Sign in required." }, H);
      if (c99Preview(req, user)) return json(res, 403, { error: "Guest preview is read-only.", preview: true }, H);
      if (p === "/api/c99/sec/fetch") {
        const t = String(b.v.t || b.v.ticker || "").trim().toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 10), back = t ? "/research/sec/" + t + "/" : "/research/sec/";
        if (!t) return c98Reply(req, res, b, 400, { error: "Enter a ticker." }, "/research/sec/");
        if (await c99Deep(t, false)) return c98Reply(req, res, b, 200, { ok: true, cached: true }, back);
        if (!c96IsAdmin(user) && !c99UserOk(String(user.id))) return c98Reply(req, res, b, 429, { error: "You have fetched " + C99_USER_DAY + " companies today. Try again tomorrow." }, back);
        try { const dd = await c99Deep(t, true); return c98Reply(req, res, b, 200, { ok: true, ticker: t, name: dd.name }, back); }
        catch (e) { return c98Reply(req, res, b, e.code === "CAP" ? 429 : e.code === "NO_UA" ? 503 : e.code === "UNKNOWN" || e.code === "BAD" ? 404 : 502, { error: e.code ? e.message : "The SEC did not answer. Try again later." }, back); }
      }
      if (p === "/api/c99/screener/build") {
        if (!c96IsAdmin(user)) return json(res, 403, { error: "Admins only." }, H);
        try { const s = await c99ScrBuild(); return c98Reply(req, res, b, 200, { ok: true, year: s.year, rows: s.rows.length }, "/research/sec/screener/"); }
        catch (e) { return c98Reply(req, res, b, e.code === "CAP" ? 429 : e.code === "NO_UA" ? 503 : 502, { error: e.code ? e.message : "The SEC did not answer. Try again later." }, "/research/sec/screener/"); }
      }
      return json(res, 404, { error: "Not found" }, H);
    } catch (e) {
      console.error("[c99]", p, e && e.message);
      if (e && e.code === "C98_BIG") return json(res, 413, { error: "Too much text." }, H);
      return json(res, 503, { error: "Try again shortly." }, H);
    }
  };
}
