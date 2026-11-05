// ── chat101h: sourced research articles on the signed-in Research desk ──
// The public /research/ page is server-rendered. Signed-in readers open the Research desk in this app.
// These cards link to the same public articles. Nothing already on the desk is removed.
(() => { try {
  if (typeof renderResearch !== "function" || renderResearch.__c101h) return;
  const CARDS = `<section data-c101h-app aria-label="Sourced research articles" style="margin:0 0 16px">
<style>
.c101h-app{display:grid;gap:10px}
.c101h-app a{display:block;min-height:48px;padding:12px 14px;border:1px solid var(--gb,var(--rule,#d6d1c4));border-radius:8px;color:inherit;text-decoration:none;background:var(--b1,transparent)}
.c101h-app a:hover{border-color:var(--gd,var(--accent,#1f3a5f))}
.c101h-app a:focus-visible{outline:2px solid var(--gd,var(--accent,#1f3a5f));outline-offset:3px}
.c101h-app .k{display:inline-block;font:600 11px/1.3 var(--mn,var(--sans,system-ui));letter-spacing:.06em;text-transform:uppercase;color:var(--gd,var(--accent,#1f3a5f))}
.c101h-app strong{display:block;margin:6px 0 4px;font:600 1.15rem/1.3 var(--sf,Georgia,serif)}
.c101h-app span{display:block;color:var(--t2,var(--muted,#5f6368));font-size:14px;line-height:1.45}
</style>
<div class="kicker" style="letter-spacing:.08em;font-size:11px;font-weight:700;text-transform:uppercase;color:var(--gd,var(--accent,#1f3a5f))">Sourced notes</div>
<h2 style="margin:6px 0 8px;font:600 1.35rem/1.25 var(--sf,Georgia,serif)">From public sources</h2>
<p style="margin:0 0 8px;color:var(--t2,var(--muted,#5f6368));max-width:68ch">Timely notes show the UK time they were checked. Evergreen explainers are labelled and do not use a current market level. Not investment advice. Capital at risk.</p>
<div class="c101h-app">
<a href="/research/bank-rate-energy-shock-sterling-gold/"><span class="k">Timely analysis</span><strong>The Bank raised rates. That is not a simple signal for sterling gold.</strong><span>The November decision is about inflation persistence, not a standalone sterling-gold signal.</span></a>
<a href="/research/gold-real-yields-breakeven-inflation/"><span class="k">Evergreen explainer</span><strong>A rising real yield is not always the gold signal it appears to be</strong><span>Breakeven inflation mixes expectations, risk compensation and liquidity.</span></a>
<a href="/research/central-bank-gold-reserves-value-volume/"><span class="k">Evergreen explainer</span><strong>More valuable reserves do not necessarily mean more central-bank gold buying</strong><span>A reserve stock, a valuation gain and a purchase are different things.</span></a>
</div></section>`;
  const prev = renderResearch;
  const wrapped = function () {
    const h = prev.apply(this, arguments);
    if (typeof selReport !== "undefined" && selReport) return h;
    if (typeof h === "string" && h.indexOf("data-c101h-app") >= 0) return h;
    return CARDS + h;
  };
  wrapped.__c101h = 1;
  renderResearch = wrapped;
} catch (e) {} })();
