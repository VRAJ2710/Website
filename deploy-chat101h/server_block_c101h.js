// ── chat101h: three sourced research articles on the existing Research section ──
// Appended to the live server. No new tables, no Stripe, no change to existing routes.
// Article pages are public for guests, free members, premium and admin. The Research
// listing keeps the Capital Sustainability Monitor, Check and plan, and Also from the desk.
(function c101hInstall() {
  const ORIGIN = (typeof PUBLIC_ORIGIN === "string" && PUBLIC_ORIGIN) || "https://thedispatch.uk";
  const CHECKED_BOE = "5 November 2026, 20:01 UK (GMT)";
  const CHECKED_FED = "5 November 2026, 20:01 UK (GMT)";
  const CHECKED_IMF = "5 November 2026, 19:50 UK (GMT)";
  const AS_OF_BOE = "As of 5 November 2026, 19:50 UK (GMT). Rechecked against the Bank of England pages at 20:01 UK (GMT) the same day; the decision figures below were unchanged.";
  const AS_OF_FED = "As of 5 November 2026, 20:01 UK (GMT). This explainer uses the Federal Reserve's methodological pages only. It quotes no current yield and no gold price.";
  const AS_OF_IMF = "As of 5 November 2026, 19:50 UK (GMT). This explainer uses the IMF's reporting guidelines. It quotes no current reserve total and no gold price.";
  const esc = (s) => (typeof c93Esc === "function" ? c93Esc(s) : String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])));
  const editor = (typeof C93_EDITOR === "string" && C93_EDITOR) || "Edited by Vraj Patel";
  const disc = (typeof C93_DISC === "string" && C93_DISC) || "Not investment advice. Capital at risk.";

  const CSS = `<style id="c101h-css">
.c101h-list{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:12px}
.c101h-list a{display:block;min-height:48px;padding:14px 16px;border:1px solid var(--rule,#dedad2);border-radius:8px;color:inherit;text-decoration:none;background:transparent}
.c101h-list a:hover{border-color:var(--accent,#1f3a5f)}
.c101h-list a:focus-visible,.c101h-article a:focus-visible,.c101h-back:focus-visible{outline:2px solid var(--accent,#1f3a5f);outline-offset:3px}
.c101h-kind{display:inline-block;width:fit-content;font:600 12px/1.3 var(--sans,Inter,system-ui,sans-serif);letter-spacing:.04em;text-transform:uppercase;color:var(--accent,#1f3a5f);border:1px solid var(--rule,#dedad2);border-radius:999px;padding:3px 8px;margin:0 0 6px}
.c101h-list strong{display:block;margin:8px 0 4px;font:600 1.35rem/1.25 var(--serif,Georgia,serif);letter-spacing:-.01em}
.c101h-list .c101h-dek,.c101h-checked{display:block;color:var(--muted,#5f6368);font-size:15px;line-height:1.45}
.c101h-article{max-width:68ch}
.c101h-article p,.c101h-article li{font-size:1.125rem;line-height:1.7;overflow-wrap:anywhere}
.c101h-article h2{margin-top:1.75rem;overflow-wrap:anywhere}
.c101h-article a{text-decoration:underline;text-underline-offset:.14em}
.c101h-article ul{padding-left:1.2rem}
.c101h-flag{margin:0 0 8px}
.c101h-end{font-weight:600;color:var(--ink,#1b1b1b)}
.c101h-back{display:inline-flex;align-items:center;min-height:44px;margin:0 0 8px}
@media (max-width:390px){.c101h-article p,.c101h-article li{font-size:1.0625rem}.c101h-list strong{font-size:1.2rem}.wrap{padding-left:16px;padding-right:16px}}
</style>`;

  function paras(list) { return list.map((p) => `<p>${p}</p>`).join(""); }
  function srcList(items) {
    return `<ul>${items.map((s) => `<li><a href="${esc(s.url)}">${esc(s.name)}</a> — ${s.note}</li>`).join("")}</ul>`;
  }

  const ARTICLES = [
    {
      slug: "bank-rate-energy-shock-sterling-gold",
      kind: "Timely analysis",
      evergreen: false,
      title: "The Bank raised rates. That is not a simple signal for sterling gold.",
      dek: "The November decision is about preventing an energy shock from becoming persistent inflation. Gold investors must separate that policy problem from currency translation.",
      description: "Why the Bank of England's November 2026 Bank Rate decision is about inflation persistence, not a standalone signal for sterling gold. Not investment advice.",
      checked: CHECKED_BOE,
      asOf: AS_OF_BOE,
      sources: [
        { name: "November 2026 Monetary Policy Summary and Minutes", url: "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/november-2026", note: "Summary; minutes paragraphs 2–7 and 16–22. Checked 5 November 2026, 20:01 UK (GMT). The 19:50 figures were unchanged." },
        { name: "November 2026 Monetary Policy Report", url: "https://www.bankofengland.co.uk/monetary-policy-report/2026/november-2026", note: "Overview; section 1.3; Box A. Checked 5 November 2026, 20:01 UK (GMT)." }
      ],
      blocks: [
        { h: null, ps: [
          `The Bank of England has raised Bank Rate to <strong>4%</strong>, an increase of <strong>0.25 percentage points</strong>, following an <strong>8–1</strong> vote at the meeting ending <strong>4 November 2026</strong>. The dissenter wanted a larger increase, not a hold. Those are the facts in the <a href="https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/november-2026">Bank’s decision published on 5 November</a>, checked at <strong>20:01 UK (GMT), 5 November 2026</strong>.`,
          "For a reader following gold in pounds, the temptation is to turn that announcement into a directional rule: higher rates support sterling and hurt gold. That shortcut bundles together different markets, different inflation measures and an exchange-rate assumption that the decision itself cannot establish.",
          "The more useful question is what the Bank is trying to prevent, and which part of that story could matter for gold."
        ] },
        { h: "An energy bill is not yet an inflation spiral", ps: [
          `The <a href="https://www.bankofengland.co.uk/monetary-policy-report/2026/november-2026">Monetary Policy Report</a> distinguishes the immediate increase in energy bills from indirect cost increases along supply chains, and from second-round changes in wage and price-setting. These mechanisms should not be treated as interchangeable.`,
          "Direct effects arrive when households pay more for fuel or utilities. Indirect effects follow when an energy-intensive supplier passes costs to another business, which eventually raises its own prices. Second-round effects are the more persistent behavioural response: workers and firms begin setting pay and prices around continuing inflation rather than a temporary change in relative costs.",
          "The Bank says evidence of those knock-on wage and price effects remains limited. Its decision is therefore not proof that an inflation spiral has already arrived. It reflects a judgement that pressure still in the pipeline, alongside more resilient activity, warrants tighter policy before the evidence becomes conclusive.",
          "That distinction matters. Policymakers act with a lag. Waiting for complete confirmation can mean reacting too late; acting early can also compound a slowdown that would have contained inflation anyway."
        ] },
        { h: "Higher nominal rates do not settle the real-return question", ps: [
          "Gold does not pay contractual interest. An interest-bearing alternative can become more attractive when its expected purchasing-power return improves. But Bank Rate is a nominal policy setting, not a complete measure of that expected real return.",
          "If inflation expectations rise alongside nominal rates, the purchasing-power comparison need not improve by the full policy increase. Equally, a credible response that restrains expectations could tighten real financial conditions more than the headline change suggests. This is an analytical framework, not an estimate of what happened in markets today.",
          "The Bank’s own discussion of financial conditions adds another caution: its market interest-rate curve includes risk premia as well as expectations for future policy. A higher curve is not a promise that the Committee will deliver every increase apparently embedded in it."
        ] },
        { h: "Sterling adds a separate channel", ps: [
          "For matching units and observation times, a dollar gold reference price translates into pounds by dividing it by the dollar value of a pound. This is currency arithmetic, not a prediction or a claim about today’s exchange rate.",
          "If dollar gold were unchanged, a stronger pound would reduce that sterling reference price; a weaker pound would increase it. If dollar gold also moved, the combined outcome would depend on both changes. Dealer spreads, product charges and any currency hedge would make an actual holding’s outcome different again.",
          "A UK policy decision therefore cannot be read in isolation. Sterling responds to the relative outlook for economies and policy, and to information already reflected in prices. Global gold has its own dollar, real-rate and demand influences. Nothing in the decision establishes the size or sign of those market reactions."
        ] },
        { h: "What would change this reading?", ps: [
          `The central uncertainty is whether limited pass-through means subdued eventual inflation pressure or merely delayed pressure. In its <a href="https://www.bankofengland.co.uk/monetary-policy-report/2026/november-2026">Box A evidence review</a>, the Bank explains why hedging, fixed-price contracts and compressed margins can initially cushion firms against energy costs.`,
          "A durable fall in energy costs, weaker demand and subdued pay settlements would weaken the case that the shock must become persistent. Broader price increases, stronger wage-setting responses and restored pricing power would strengthen it. Neither path mechanically determines gold’s return.",
          "Our interpretation would need revision if the evidence showed that the policy response was addressing a materially different inflation mechanism, or that the apparent absence of second-round effects was already contradicted by broad, consistent data. For now, the useful conclusion is narrower: this is a decision about inflation persistence, not a standalone signal for sterling gold.",
          "No gold, currency or bond market quote is used here. The article analyses the official decision; it does not measure an announcement-day market reaction."
        ] }
      ]
    },
    {
      slug: "gold-real-yields-breakeven-inflation",
      kind: "Evergreen explainer",
      evergreen: true,
      title: "A rising real yield is not always the gold signal it appears to be",
      dek: "Breakeven inflation contains expectations, risk compensation and liquidity effects. Understanding the difference makes a gold dashboard more useful.",
      description: "An evergreen explainer of why a TIPS real yield and breakeven inflation are not a clean, single gold signal. Not investment advice.",
      checked: CHECKED_FED,
      asOf: AS_OF_FED,
      sources: [
        { name: "Tips from TIPS: Update and Discussions", url: "https://www.federalreserve.gov/econres/notes/feds-notes/tips-from-tips-update-and-discussions-20190521.html", note: "Sections 1–2 and 4; decomposition and model limitations. Staff research note by Don Kim, Cait Walsh and Min Wei, 21 May 2019. Checked 5 November 2026, 20:01 UK (GMT)." },
        { name: "TIPS Yield Curve and Inflation Compensation", url: "https://www.federalreserve.gov/data/tips-yield-curve-and-inflation-compensation.htm", note: "Explanation and Q&amp;A, including risk premiums, hypothetical smoothed yields, and delay and revision. Checked 5 November 2026, 20:01 UK (GMT)." }
      ],
      blocks: [
        { h: null, ps: [
          "Gold commentary often gives real yields a leading role: when inflation-adjusted bond returns rise, an asset paying no interest faces stronger competition. It is a useful mechanism. It is not a complete explanation of every move in gold, and the familiar real-yield series is not a perfectly clean reading of that mechanism.",
          "The distinction begins with the instrument behind the number. US Treasury Inflation-Protected Securities, or TIPS, adjust payments for consumer-price inflation. Their market yields are commonly described as real yields. A comparison with nominal Treasury yields of matching maturity produces the breakeven inflation rate, also called inflation compensation.",
          `The <a href="https://www.federalreserve.gov/data/tips-yield-curve-and-inflation-compensation.htm">Federal Reserve’s explanation of its TIPS yield curve</a> makes clear that inflation compensation can be driven by risk premiums as well as expectations. This article uses that methodological explanation, checked at <strong>20:01 UK (GMT), 5 November 2026</strong>. It makes no claim about the latest yield level or today’s gold market.`
        ] },
        { h: "The spread contains more than a forecast", ps: [
          "A breakeven is often described as what the market expects inflation to average over the life of the bonds. That wording is too strong.",
          `In their <a href="https://www.federalreserve.gov/econres/notes/feds-notes/tips-from-tips-update-and-discussions-20190521.html">Federal Reserve staff research note, published 21 May 2019</a>, Don Kim, Cait Walsh and Min Wei set out a decomposition: inflation compensation contains expected inflation, plus an inflation risk premium, minus a TIPS liquidity premium.`,
          "Expected inflation is the component most readers intend to discuss. The inflation risk premium is compensation for bearing uncertainty about inflation when holding nominal bonds. Its sign and size need not be fixed. The liquidity component reflects the wedge between TIPS yields and the model’s underlying real yield, associated with the relative trading characteristics and demand for the securities.",
          "The important point is not that every daily move can be neatly allocated. It is that the observed spread alone cannot identify the allocation."
        ] },
        { h: "Why that changes a gold interpretation", ps: [
          "Consider a conditional example without attaching numbers to it. Suppose nominal Treasury yields are unchanged while quoted TIPS yields rise. Breakeven inflation falls as a matter of subtraction.",
          "A quick account might say investors now expect less inflation and demand a higher real return. That could be part of the explanation. But if TIPS have become less liquid relative to nominal Treasuries, the liquidity wedge could produce some of the same pattern without the equivalent change in underlying inflation expectations.",
          "That matters for gold because a liquidity disturbance and an improvement in expected real income are different economic stories. They may arrive with different changes in dollar funding conditions, investor risk appetite and demand for liquid assets. The yield chart cannot, by itself, tell the reader which mechanism dominates.",
          "The staff note also separates the underlying real yield into expected future real short rates and a real term premium: compensation for bearing real interest-rate risk over time. Even after allowing for liquidity, a longer-dated yield is not simply a forecast of the central bank’s next decision."
        ] },
        { h: "A cleaner way to read the dashboard", ps: [
          "Start with the exact series. A fitted yield curve is an estimate assembled from securities, not necessarily the yield on a particular bond that a reader could transact at. The Federal Reserve’s curve page explicitly describes smoothed yields on hypothetical TIPS and warns that methodology and data vintages can change.",
          "Then match the horizon. An inflation release covering recent prices, a long-horizon breakeven and a policy rate answer different questions. Placing them together can be informative; treating them as interchangeable is not.",
          "Finally, compare interpretations rather than hunting for automatic confirmation. If inflation compensation falls, do surveys and other evidence also suggest weaker inflation expectations? Are there signs of impaired market liquidity? Is the movement concentrated in a particular maturity? These checks help separate a plausible explanation from a convenient story."
        ] },
        { h: "The limits of a better explanation", ps: [
          "Model decompositions do not reveal expectations with certainty. The staff note shows that different models can generate different estimates, and stresses that expectations and attitudes to risk are more complex than the models representing them. The curve itself is a staff research product, not an official statistical release, and is subject to delay and revision.",
          "A liquidity-based interpretation would be weakened if independent evidence showed normal trading conditions and a broad, consistent shift in expectations instead. An expectations-led explanation would be weakened if it depended on a single unstable model or disappeared after correcting a series mismatch.",
          "The conclusion is not to discard real yields. It is to describe them precisely: a valuable part of the opportunity-cost picture, with measurement and interpretation risks. Gold’s relationship with that picture must be tested, not assumed. No current quote or mechanical price forecast is implied."
        ] }
      ]
    },
    {
      slug: "central-bank-gold-reserves-value-volume",
      kind: "Evergreen explainer",
      evergreen: true,
      title: "More valuable reserves do not necessarily mean more central-bank gold buying",
      dek: "A reserve stock, a valuation gain and a purchase are different things. The IMF’s reporting framework explains how to tell them apart.",
      description: "An evergreen explainer of why a higher reported value of monetary gold is not, by itself, evidence of central-bank buying. Not investment advice.",
      checked: CHECKED_IMF,
      asOf: AS_OF_IMF,
      sources: [
        { name: "International Reserves and Foreign Currency Liquidity: Guidelines for a Data Template", url: "https://www.imf.org/external/np/sta/ir/IRProcessWeb/pdf/guide.pdf", note: "Paragraphs 32, 98–101 and 128–135; Appendix II item I.A.(4) and footnote 5. Checked 5 November 2026, 19:50 UK (GMT). Standing methodology, not a current-event source." }
      ],
      blocks: [
        { h: null, ps: [
          "A central bank reports that its gold reserves are worth more. The headline becomes another claim about official-sector buying. That conclusion may be right, but a larger money value is not enough to establish it.",
          "A reserve statement measures a stock at a reference date. A purchase is a transaction over a period. The stock’s reported value can change even when the quantity of gold does not. For readers using central-bank demand to understand gold, separating those ideas is essential.",
          `This is a reporting-method explainer, not a claim about recent buying by any country. Its primary source is the <a href="https://www.imf.org/external/np/sta/ir/IRProcessWeb/pdf/guide.pdf">IMF’s International Reserves and Foreign Currency Liquidity guidelines</a>, checked at <strong>19:50 UK (GMT), 5 November 2026</strong>. No current reserve total or gold-price quote is used.`
        ] },
        { h: "Start with quantity, price and date", ps: [
          "The IMF guidance says monetary gold should be valued at the current market price of commodity gold and that the valuation basis should be disclosed. Its template separately requests the volume in fine troy ounces. See the guide’s monetary-gold valuation section and the reserve-assets template in its appendix.",
          "In the simplest unchanged reporting framework, the money value is the quantity of gold multiplied by the price used to value it. A higher valuation price therefore increases the reported value of an unchanged quantity. A move in the reporting currency can add another translation effect where the gold reference price is expressed in a different currency.",
          "This is why a statement that gold reserves reached a record value is not equivalent to a statement that the central bank made record purchases. It could reflect a change in price, quantity, currency translation or a combination of them.",
          "Even the reporting date needs care. A statement released today can describe holdings at an earlier month-end. Comparing its reserve value with today’s gold quote mixes observation dates and may manufacture an apparent discrepancy that the accounts never contained."
        ] },
        { h: "The portfolio-share trap", ps: [
          "A similar problem affects gold’s share of total reserves. That share has a numerator and a denominator: the value assigned to gold and the total value of the reserve portfolio.",
          "Gold’s share can rise because its valuation increases. It can also rise because other reserve assets fall in value or are drawn down. Neither mechanism necessarily involves an additional purchase of gold.",
          "The distinction does not make the portfolio change irrelevant. A larger gold share may alter the institution’s exposure to market movements. But it does change the causal story. An accounting result should not be promoted into evidence of a new strategic allocation decision without supporting disclosure.",
          "For gold-market analysis, the practical question is therefore not merely whether the share increased. It is whether the evidence identifies an intentional addition to holdings, rather than a valuation or denominator effect."
        ] },
        { h: "What counts as monetary gold?", ps: [
          `The <a href="https://www.imf.org/external/np/sta/ir/IRProcessWeb/pdf/guide.pdf">IMF guide</a> defines the reserve-template gold item to include bullion and unallocated gold accounts with nonresidents. It distinguishes an allocated account’s ownership of specific gold from an unallocated account’s claim to delivery.`,
          "It also discusses gold deposits and swaps. Under its recommended treatment, swaps are handled like repurchase arrangements rather than automatically interpreted as outright sales. The economic exposure and the legal movement of gold need not tell the same story.",
          "These details are not grounds to dismiss official statistics. They are reasons to read the notes. A headline balance-sheet item is not a bar-by-bar inventory, a transaction ledger or a complete statement of immediate market demand."
        ] },
        { h: "A defensible reading process", ps: [
          "Begin with the reporting institution’s own release and record the reference period, units, valuation basis and any revisions. Prefer a disclosed quantity series to an inference drawn from a money value. Check that adjacent observations use consistent definitions before calling their difference a change in holdings.",
          "Next, look for a reconciliation explaining transactions, valuation changes and other adjustments. A rise in a consistently measured volume is stronger evidence of increased reported holdings than a rise in value alone. It still does not, without transaction information, identify the precise execution date, price, counterparty or motive.",
          "Finally, distinguish the individual country from the aggregate. Evidence that an institution added gold does not establish the balance of buying and selling across the official sector. Missing reports and different reference dates can prevent an apparently comprehensive total from answering that question."
        ] },
        { h: "What would overturn the cautious conclusion?", ps: [
          "An official transaction disclosure or a clear stock-flow reconciliation could establish that purchases drove a particular increase. Consistent quantity data, supported by notes excluding reclassification or other adjustments, would substantially strengthen that interpretation.",
          "Conversely, unchanged volume alongside higher reported value would undermine the claim that the increase itself proves buying. A revision to the reporting basis could invalidate a simple comparison altogether.",
          "Central-bank demand matters, but the discipline comes before the narrative: identify the stock, isolate the valuation and establish the transaction. A larger number on a reserve statement is the beginning of the analysis, not its conclusion."
        ] }
      ]
    }
  ];

  const BY_SLUG = {};
  ARTICLES.forEach((a) => { a.path = "/research/" + a.slug + "/"; BY_SLUG[a.slug] = a; });

  function listHtml() {
    const items = ARTICLES.map((a) => `<li><a href="${a.path}"><span class="c101h-kind">${esc(a.kind)}</span><strong>${esc(a.title)}</strong><span class="c101h-dek">${esc(a.dek)}</span></a></li>`).join("");
    return CSS + `<section data-c101h-articles><div class="kicker">Articles</div><h2>Sourced notes</h2><p style="max-width:720px">Longer notes from public sources. Timely pieces show the UK time they were checked. Evergreen explainers are labelled and do not use a current market level. ${esc(disc)}</p><ul class="c101h-list">${items}</ul></section>`;
  }

  function articleHtml(a) {
    const body = a.blocks.map((b) => (b.h ? `<h2>${esc(b.h)}</h2>` : "") + paras(b.ps)).join("");
    return `${CSS}<section class="prose c101h-article"><p class="c101h-flag"><span class="c101h-kind">${esc(a.kind)}</span></p><div class="kicker"><a href="/research/">Research</a></div><h1>${esc(a.title)}</h1><p class="dek">${esc(a.dek)}</p><p class="byline">${esc(editor)}</p><p class="c101h-checked">${esc(a.asOf)}</p></section><section class="prose c101h-article">${body}<h2>Sources and verification</h2>${srcList(a.sources)}<p class="c101h-end">${esc(disc)}</p><p><a class="c101h-back" href="/research/">Back to Research</a></p></section>`;
  }

  function jsonLd(a) {
    const data = {
      "@context": "https://schema.org",
      "@type": "Article",
      headline: a.title,
      description: a.dek,
      inLanguage: "en-GB",
      datePublished: "2026-11-05",
      dateModified: "2026-11-05",
      isAccessibleForFree: true,
      mainEntityOfPage: ORIGIN + a.path,
      url: ORIGIN + a.path,
      publisher: { "@type": "Organization", name: "The Dispatch Market", url: ORIGIN + "/" },
      editor: { "@type": "Person", name: "Vraj Patel" },
      citation: a.sources.map((s) => ({ "@type": "CreativeWork", name: s.name, url: s.url }))
    };
    return `<script type="application/ld+json">${JSON.stringify(data).replace(/</g, "\\u003c")}</script>`;
  }

  function adminOf(u) {
    try { if (typeof c96IsAdmin === "function" && c96IsAdmin(u)) return true; } catch (e) {}
    try { if (typeof isAdminUser === "function" && isAdminUser(u)) return true; } catch (e) {}
    return !!(u && (u.isAdmin || u.admin));
  }

  async function userOf(req, path) {
    let user = null;
    try { user = typeof c96UserOf === "function" ? await c96UserOf(req) : null; } catch (e) { user = null; }
    const preview = /(?:^|;\s*)dispatch_preview=1(?:;|$)/.test(String((req && req.headers && req.headers.cookie) || ""));
    if (user && (req.c96PreviewOn || (preview && adminOf(user)))) { req.c94Preview = path; user = null; }
    if (user) req.c94Signed = true;
    return user;
  }

  function sendArticle(req, res, user, a) {
    const shell = {
      title: a.title + " | The Dispatch Market",
      path: a.path,
      desc: a.description,
      user,
      strip: `<a href="/research/">Research</a> \u203a ${esc(a.title)}`,
      extraHead: jsonLd(a),
      body: articleHtml(a) + jsonLd(a)
    };
    const html = c93Shell(shell);
    const cache = "public, max-age=300";
    if (typeof c93Html === "function") return c93Html(req, res, html, cache);
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": cache });
    res.end(req.method === "HEAD" ? undefined : html);
  }

  function match(pathname) {
    const raw = String(pathname || "");
    const m = /^\/research\/([a-z0-9-]{8,80})\/?$/.exec(raw);
    if (!m || !BY_SLUG[m[1]]) return null;
    const a = BY_SLUG[m[1]];
    if (raw !== a.path) return { redirect: a.path };
    return { article: a };
  }

  if (typeof handle === "function" && !handle.__c101h) {
    const prev = handle;
    const wrapped = async function (req, res) {
      try {
        if (typeof BB10I_MAINTENANCE_ON !== "undefined" && BB10I_MAINTENANCE_ON) return prev.apply(this, arguments);
        if (req && (req.method === "GET" || req.method === "HEAD")) {
          let u = null;
          try { u = new URL(req.url || "/", "http://localhost"); } catch (e) { u = null; }
          const hit = u && match(u.pathname);
          if (hit) {
            if (hit.redirect) { res.writeHead(301, { Location: hit.redirect + (u.search || "") }); return res.end(); }
            const user = await userOf(req, hit.article.path);
            return sendArticle(req, res, user, hit.article);
          }
        }
      } catch (e) { console.error("[c101h] article", e && e.message); }
      return prev.apply(this, arguments);
    };
    wrapped.__c101h = 1;
    handle = wrapped;
  }

  const ANCHOR = '<p class="byline">Edited by Vraj Patel</p></section>';
  function inject(html) {
    if (typeof html !== "string" || html.indexOf("data-c101h-articles") >= 0) return html;
    if (html.indexOf("<h1>Research</h1>") < 0 || html.indexOf(ANCHOR) < 0) return html;
    return html.replace(ANCHOR, ANCHOR + listHtml());
  }
  if (typeof c93Html === "function" && !c93Html.__c101h) {
    const prevHtml = c93Html;
    const wrappedHtml = function (req, res, html, cache) {
      try {
        let p = "";
        try { p = new URL((req && req.url) || "/", "http://localhost").pathname; } catch (e) { p = ""; }
        if (p === "/research" || p === "/research/") html = inject(html);
      } catch (e) {}
      return prevHtml.call(this, req, res, html, cache);
    };
    wrappedHtml.__c101h = 1;
    c93Html = wrappedHtml;
  }
  if (typeof c97Transform === "function" && !c97Transform.__c101h) {
    const prevTr = c97Transform;
    const wrappedTr = function (html, req) {
      let out = prevTr.apply(this, arguments);
      try {
        let p = "";
        try { p = new URL((req && req.url) || "/", "http://localhost").pathname; } catch (e) { p = ""; }
        if (p === "/research" || p === "/research/") out = inject(out);
      } catch (e) {}
      return out;
    };
    wrappedTr.__c101h = 1;
    c97Transform = wrappedTr;
  }
  if (typeof renderPublicSitemap === "function" && !renderPublicSitemap.__c101h) {
    const prevMap = renderPublicSitemap;
    const wrappedMap = async function () {
      let x = await prevMap.apply(this, arguments);
      if (typeof x !== "string" || x.indexOf("</urlset>") < 0) return x;
      const add = ARTICLES.map((a) => a.path).filter((u) => x.indexOf("<loc>" + ORIGIN + u + "</loc>") < 0);
      if (!add.length) return x;
      return x.replace("</urlset>", add.map((u) => `  <url><loc>${ORIGIN}${u}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n`).join("") + "</urlset>");
    };
    wrappedMap.__c101h = 1;
    renderPublicSitemap = wrappedMap;
  }
})();
