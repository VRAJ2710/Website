// ── chat101f: market quotes first ── the US 10-year and real yields come from a free, delayed market quote (Tradeweb via
// CNBC, trades almost 24 hours on weekdays); the official daily FRED figure is kept as a secondary line, or used, labelled,
// when the quote is missing. Gold's change reads "since yesterday's close (23:57 UK, 4 Nov)". GET /api/c101f/rates.
const C101F_CNBC = "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=US10Y%7CUS10YTIP&requestMethod=itv&noform=0&partnerId=2&fund=1&exthrs=1&output=json";
const C101F_UA = "Mozilla/5.0 (compatible; TheDispatchMarket/1.0; +https://thedispatch.uk)";   // the quote host refuses agents without a Mozilla prefix
const C101F_URL = { US10Y: "https://www.cnbc.com/quotes/US10Y", US10YTIP: "https://www.cnbc.com/quotes/US10YTIP" };
function c101fNum(s) { const t = String(s == null ? "" : s).replace(/[%+,\s]/g, ""); const n = Number(t); return t !== "" && isFinite(n) ? n : null; }
async function c101fRates() {
  return (await c97Cached("c101f:rates", 2 * 60e3, async () => {
    const r = await fetch(C101F_CNBC, { headers: { "User-Agent": C101F_UA, Accept: "application/json" }, signal: AbortSignal.timeout(8000), redirect: "follow" });
    if (!r.ok) throw new Error("http " + r.status);
    const j = await r.json();
    const L = (j && j.FormattedQuoteResult && j.FormattedQuoteResult.FormattedQuote) || [], now = Date.now();
    const one = sym => {
      const q = L.find(x => x && x.symbol === sym); if (!q) return null;
      const v = c101fNum(q.last), pv = c101fNum(q.previous_day_closing);
      const ms = Date.parse(String(q.last_time || "").replace(/([+-]\d{2})(\d{2})$/, "$1:$2"));
      if (v == null || !(v > -5 && v < 25) || !isFinite(ms) || now - ms > 4 * 864e5 || ms - now > 6e5) return null;   // sane and at most 4 days old (weekends)
      return { value: v, prev: pv, change: pv != null ? Math.round((v - pv) * 1000) / 1000 : null, asOfMs: ms, asOfUk: c97UkWhen(ms),
        src: /tradeweb/i.test(String(q.exchange || "")) ? "Tradeweb via CNBC" : "CNBC market quote", url: C101F_URL[sym], changeBasis: "previous close" };
    };
    const out = { ten: one("US10Y"), tips: one("US10YTIP") };
    if (!out.ten && !out.tips) throw new Error("no quotes");
    return out;
  }, 5000)).v;
}
// Gold change wording: "since yesterday's close (23:57 UK, 4 Nov)"; after a weekend, "since the last close (23:57 UK, Fri 30 Oct)".
function c101fSince(snapAt, ms) {
  const y = c97UkIso(snapAt) === c97UkIso((ms || Date.now()) - 864e5), d = c97UkDate(snapAt);
  return "since " + (y ? "yesterday's close (" + c97UkHm(snapAt) + " UK, " + d.replace(/^\S+\s+/, "") + ")" : "the last close (" + c97UkHm(snapAt) + " UK, " + d + ")");
}
c100bMk = function (nowV, prev, basis, ms, snapAt) {
  const chg = nowV - prev, label = c101fSince(snapAt, ms), how = String(basis || "").replace(/^vs previous UK close,\s*/, "");
  return { price: nowV, prev, chg, pct: (nowV / prev - 1) * 100, basis: label + (how ? ", " + how : ""), label, asOfUk: c97UkWhen(ms), asOfMs: ms, snapUk: c97UkWhen(snapAt) };
};
{
  const c101fGd0 = c97GoldDash;
  c97GoldDash = async function () {
    const d = await c101fGd0.apply(this, arguments);
    if (!d || !d.rows) return d;
    let lv = null; try { lv = await c101fRates(); } catch (e) {}
    const rows = Object.assign({}, d.rows);
    const live = (k, q, label, plain) => {
      const off = rows[k] || null;
      if (q && isFinite(Number(q.value))) {
        rows[k] = { label, value: c97N(q.value, 2) + "%", change: q.change != null ? c97Sg(q.change, 2, " pt") : "", changeNote: "vs previous close",
          source: (/market quote/i.test(q.src) ? q.src : q.src + ", market quote") + ", delayed", asOf: "Delayed \u00b7 as of " + q.asOfUk, plain, delayed: true, live: true, num: q.value, prev: q.prev, url: q.url,
          official: off ? "Official daily: " + off.value + " (US Treasury via FRED, " + c97DayLong(off.date).replace(/ \d{4}$/, "") + ")" + (k === "ry" ? "; published with a 1\u20132 day lag" : "") : "",
          offRow: off };
      } else if (off) {
        rows[k] = Object.assign({}, off, { source: "Live quote unavailable, so this is the official daily figure: " + off.source + (k === "ry" ? "; published with a 1\u20132 day lag" : "") });
      }
    };
    live("tnx", lv && lv.ten, "US 10-year Treasury yield", "What the US government pays to borrow for ten years.");
    live("ry", lv && lv.tips, "US 10-year real yield", "The 10-year Treasury yield after expected inflation (inflation-protected Treasuries, TIPS). Gold, which pays no interest, often struggles when this rises.");
    const c = d.c100bChange;
    [["gold_usd", "usd"], ["gold_gbp", "gbp"], ["gold_eur", "eur"]].forEach(z => { const x = c && c[z[1]]; if (x && x.label && rows[z[0]]) rows[z[0]] = Object.assign({}, rows[z[0]], { changeBasis: "Change " + x.label, changeNote: x.label }); });
    return Object.assign({}, d, { rows });
  };
}
c97Tbl = function (rows) {
  return `<table class="c97t c97r"><thead><tr><th scope="col">Measure</th><th scope="col">Reading</th><th scope="col">Change</th><th scope="col">Source and time</th></tr></thead><tbody>` +
    rows.filter(Boolean).map(r => { const ch = String(r.change || ""), cl = /^\+\S/.test(ch) ? ' class="c100b-up"' : /^[\u2212-]\S/.test(ch) ? ' class="c100b-dn"' : "";
      return `<tr><td><strong>${c93Esc(r.label)}</strong><span class="c97p">${c93Esc(r.plain || "")}</span></td><td class="v">${c93Esc(r.value)}</td><td${cl}>${c93Esc(ch)}${r.changeNote ? `<span class="c97s">${c93Esc(r.changeNote)}</span>` : ""}</td><td><span class="c97s">${c93Esc(r.source)}</span><span class="c97s">${c93Esc(r.asOf || "")}</span>${r.official ? `<span class="c97s c101f-off">${c93Esc(r.official)}</span>` : ""}</td></tr>`; }).join("") + `</tbody></table>`;
};
{
  const c101fI0 = bb10iHandle0;
  bb10iHandle0 = async function c101fInner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (p === "/api/c101f/rates" && req.method === "GET") {
      let v = null; try { v = await c101fRates(); } catch (e) {}
      if (!v) return json(res, 200, { available: false }, { "Cache-Control": "no-store" });
      return json(res, 200, { available: true, ten: v.ten, tips: v.tips, note: "Free market quotes, delayed. Change is against the previous close." }, { "Cache-Control": "public, max-age=60" });
    }
    return c101fI0.apply(this, arguments);
  };
}
setTimeout(() => { try { c101fRates().catch(() => {}); } catch (e) {} }, 5000).unref();
