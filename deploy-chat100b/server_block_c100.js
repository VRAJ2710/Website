// ── chat100 ──
// 1 /api/c100/macro: gold and macro readings for the dashboard (plain names, source, UK time, delayed/last-known, formula).
// 3 The filings screener builds itself the first time it is needed, inside the shared 25-a-day SEC cap (bb11:sec_downloads).
// 4 Source inspector: tap or click a figure to see its source, series, retrieval time, status and formula.
// No DDL. No new tables. Information only. Not investment advice. Capital at risk.
const C100_URL = {
  gold: "https://gold-api.com/", fred: s => "https://fred.stlouisfed.org/series/" + s, yahoo: "https://finance.yahoo.com/markets/",
  ice: "https://www.ice.com/futures-us/indices"
};
async function c100Macro() {
  return (await c97Cached("c100:macro", 2 * 60e3, async () => {
    const at = Date.now();
    const [gd, yq] = await Promise.all([c97GoldDash().catch(() => null), (async () => { try { return await yahooQuote(["BZ=F", "GBPUSD=X", "^GSPC"]); } catch (e) { return null; } })()]);
    const R = (gd && gd.rows) || {}, Q = yq || {}, out = [];
    const tsMs = t => { const n = Number(t); return n > 1e12 ? n : n > 1e9 ? n * 1000 : at; };
    const ok = q => q && Number(q.p) > 0;
    const fromGd = (k, name, series, url, formula) => { const r = R[k]; if (!r) return; out.push({ key: k, name, value: r.value, change: r.change || "", source: r.source, sourceUrl: url, series, asOf: r.asOf || "", status: r.delayed ? "Delayed" : "Official daily print", formula: formula || "", plain: r.plain || "" }); };
    const fromYq = (k, sym, name, series, dp, pre, plain, formula) => { const q = Q[sym]; if (!ok(q)) return; out.push({ key: k, name, value: (pre || "") + c97N(q.p, dp), change: q.prev > 0 ? c97Sg((q.p / q.prev - 1) * 100, 2, "%") : "", source: "Yahoo Finance, delayed", sourceUrl: C100_URL.yahoo, series, asOf: "Delayed \u00b7 as of " + c97UkWhen(tsMs(q.ts)), status: "Delayed", formula: formula || "", plain }); };
    fromGd("gold_usd", "Gold spot", "Spot gold price, US dollars per troy ounce", C100_URL.gold);
    fromGd("silver", "Silver spot", "Spot silver price, US dollars per troy ounce", C100_URL.gold);
    fromGd("gold_gbp", "Gold in pounds", "Spot gold price converted to pounds per troy ounce", C100_URL.gold, "Gold in pounds = gold spot in US$ \u00f7 pound in US$ (GBP/USD)");
    fromGd("dxy", "US dollar index", "ICE US Dollar Index: the dollar against six major currencies", C100_URL.ice);
    fromGd("tnx", "US 10-year yield", "10-year US Treasury yield, constant maturity, daily (FRED series DGS10)", C100_URL.fred("DGS10"));
    fromGd("ry", "US real yield (10-year)", "10-year US Treasury inflation-protected yield, daily (FRED series DFII10)", C100_URL.fred("DFII10"));
    fromYq("brent", "BZ=F", "Brent crude oil", "Brent crude oil futures, nearest contract, US$ a barrel", 2, "$", "The global benchmark oil price.");
    fromYq("gbpusd", "GBPUSD=X", "Pound in dollars", "Pound sterling priced in US dollars", 4, "$", "How many dollars one pound buys.");
    fromYq("spx", "^GSPC", "S&P 500 (context)", "S&P 500 index of large US companies", 2, "", "Shown for context on risk appetite, not as a gold measure.");
    if (!out.length) throw new Error("no feeds");
    return { rows: out, at };
  }, 9000)).v;
}
// ── screener: first build without an admin click ──
const C100_SCR = { p: null, nextTry: 0, last: "" };
function c100ScrKick(why) {
  try {
    if (C100_SCR.p || Date.now() < C100_SCR.nextTry || !bb11Ua()) return;
    C100_SCR.p = (async () => {
      if (await c99Scr()) return;
      const need = 7 + ((await c99Tickers(false)) ? 0 : 1);
      if (C99_CAP - (await c99Used()) < need) { C100_SCR.last = "cap"; C100_SCR.nextTry = Date.now() + 30 * 60e3; return; }
      await c99ScrBuild(); C100_SCR.last = "built"; console.log("[c100] screener built (" + why + ")");
    })().catch(e => { C100_SCR.last = String(e && e.code || "err"); C100_SCR.nextTry = Date.now() + 6 * 3600e3; console.error("[c100] screener build", e && e.message); })
      .finally(() => { C100_SCR.p = null; if (!C100_SCR.nextTry || C100_SCR.last === "built") C100_SCR.nextTry = Date.now() + 10 * 60e3; });
  } catch (e) {}
}
setTimeout(() => { try { c100ScrKick("startup"); } catch (e) {} }, 120e3).unref();
{
  const c100ScrPage0 = c99ScrPage;
  c99ScrPage = async function (req, res, user, u0) { try { if (!(await c99Scr())) c100ScrKick("page"); } catch (e) {} return c100ScrPage0.apply(this, arguments); };
}
// ── /api/c100/macro and /api/c100/status ──
{
  const c100I0 = bb10iHandle0;
  bb10iHandle0 = async function c100Inner(req, res) {
    let p = ""; try { p = new URL(req.url || "/", "http://localhost").pathname; } catch (e) {}
    if (p === "/api/c100/macro" && req.method === "GET") {
      try { const m = await c100Macro(); return json(res, 200, m ? { available: true, rows: m.rows, fetchedAt: new Date(m.at).toISOString(), fetchedUk: c97UkWhen(m.at) } : { available: false }, { "Cache-Control": "public, max-age=60" }); }
      catch (e) { return json(res, 200, { available: false }, { "Cache-Control": "no-store" }); }
    }
    return c100I0.apply(this, arguments);
  };
}
// ── source inspector (every page, including the app) ──
const C100_INSP_CSS = `.c100-fig{all:unset;cursor:pointer;border-bottom:1px dotted currentColor;font:inherit;color:inherit}.c100-fig:focus-visible,[data-c100]:focus-visible{outline:2px solid #2563eb;outline-offset:2px;border-radius:2px}
#c100-pane{position:fixed;z-index:2147483000;right:16px;bottom:16px;width:min(380px,calc(100vw - 24px));max-height:min(70vh,520px);overflow:auto;background:#fff;color:#151b23;border:1px solid #c9c4b8;border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,.25);padding:14px 16px;font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
#c100-pane[hidden]{display:none}#c100-pane h2{font-size:16px;margin:0 30px 2px 0;line-height:1.3}#c100-pane .v{font-size:20px;font-weight:700;margin:2px 0 8px}#c100-pane dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:4px 10px}#c100-pane dt{font-weight:600;color:#4a4f57}#c100-pane dd{margin:0;overflow-wrap:anywhere}
#c100-pane a{color:#1f3a8a;text-decoration:underline}#c100-pane .x{position:absolute;top:8px;right:8px;min-width:32px;min-height:32px;border:1px solid #c9c4b8;border-radius:6px;background:transparent;color:inherit;font-size:16px;cursor:pointer}#c100-pane .ft{margin:10px 0 0;font-size:12px;color:#4a4f57}
html.c97-dark #c100-pane{background:#151b23;color:#ece9e2;border-color:#3a4452}html.c97-dark #c100-pane dt,html.c97-dark #c100-pane .ft{color:#b8bec8}html.c97-dark #c100-pane a{color:#9cc0ea}html.c97-dark #c100-pane .x{border-color:#3a4452}
@media (prefers-color-scheme:dark){html.c97-system #c100-pane{background:#151b23;color:#ece9e2;border-color:#3a4452}html.c97-system #c100-pane dt,html.c97-system #c100-pane .ft{color:#b8bec8}html.c97-system #c100-pane a{color:#9cc0ea}}
@media (max-width:600px){#c100-pane{left:12px;right:12px;bottom:12px;width:auto}}`;
const C100_INSP_JS = String.raw`(function(){if(window.__c100)return;window.__c100=1;
var SRC=[[/FRED \((\w+)\)|FRED series (\w+)/,function(m){var s=m[1]||m[2];return["FRED, Federal Reserve Bank of St. Louis (US Treasury data)","https://fred.stlouisfed.org/series/"+s,s==="DFII10"?"10-year US Treasury inflation-protected (real) yield, daily (FRED series DFII10)":s==="DGS10"?"10-year US Treasury yield, constant maturity, daily (FRED series DGS10)":"FRED series "+s]}],
[/real yield/i,function(){return["FRED, Federal Reserve Bank of St. Louis (US Treasury data)","https://fred.stlouisfed.org/series/DFII10","10-year US Treasury inflation-protected (real) yield, daily (FRED series DFII10)"]},1],
[/10-year Treasury yield|US 10-year yield/i,function(){return["FRED, Federal Reserve Bank of St. Louis (US Treasury data)","https://fred.stlouisfed.org/series/DGS10","10-year US Treasury yield, constant maturity, daily (FRED series DGS10)"]},1],
[/US Treasury daily par yield/i,function(){return["US Treasury","https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve","Daily Treasury par yield curve rates"]}],
[/Bank of England/i,function(){return["Bank of England","https://www.bankofengland.co.uk/statistics/yield-curves","Nominal par gilt yields, end of day"]}],
[/CFTC/i,function(){return["CFTC Commitments of Traders","https://publicreporting.cftc.gov/","Disaggregated futures-only report, gold on COMEX, weekly"]}],
[/EIA/,function(){return["US Energy Information Administration","https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm","Crude oil spot price, daily"]}],
[/Frankfurter|ECB/,function(){return["European Central Bank reference rates, via Frankfurter","https://www.frankfurter.app/","Euro foreign exchange reference rates"]}],
[/Coinbase/i,function(){return["Coinbase","https://www.coinbase.com/price","Spot price in US dollars"]}],
[/CoinGecko/i,function(){return["CoinGecko","https://www.coingecko.com/","Spot price in US dollars"]}],
[/ICE US Dollar|US Dollar Index|dollar index/i,function(){return["ICE US Dollar Index, via Yahoo Finance","https://finance.yahoo.com/markets/","ICE US Dollar Index: the dollar against six major currencies"]},1],
[/gold-api/i,function(m,t){return["gold-api.com","https://gold-api.com/",/silver/i.test(t)&&!/gold/i.test(t.split("|")[0])?"Spot silver price, US dollars per troy ounce":"Spot gold price, US dollars per troy ounce"]}],
[/SEC EDGAR|SEC filing|data\.sec\.gov/i,function(){return["US SEC EDGAR","https://www.sec.gov/edgar/search/","Company financial data as filed (XBRL)"]}],
[/Yahoo/i,function(m,t){return["Yahoo Finance, delayed","https://finance.yahoo.com/markets/",""]}],
[/risk-appetite|The Dispatch/i,function(){return["The Dispatch Market model","/methodology/","In-house gauge built from the figures shown"]}]];
var FORM=[[/£ per gram/i,"Gold in pounds per gram = gold spot in US$ ÷ pound in US$ (GBP/USD) ÷ 31.1035 grams per troy ounce"],[/£ per troy ounce|gold in pounds|£/i,"Gold in pounds = gold spot in US$ ÷ pound in US$ (GBP/USD)"],[/€ per troy ounce/i,"Gold in euros = gold spot in US$ ÷ euro in US$ (EUR/USD)"],[/gold\/silver ratio/i,"Gold/silver ratio = gold spot ÷ silver spot"],
[/net position as a share/i,"Net position ÷ all open gold futures contracts"],[/^net position/i,"Contracts that gain if gold rises − contracts that gain if gold falls"],[/percentile/i,"Share of the last ten years of weekly reports with a net position at or below this week's"],[/change over a week/i,"Latest yield − yield about one week earlier"],[/change over a month/i,"Latest yield − yield about one month earlier"]];
function T(e){return e?String(e.textContent||"").replace(/\s+/g," ").trim():""}
function when(t){var m=/((?:[A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2},? )?\d{1,2}:\d{2} UK)/.exec(t);return m?m[1]:""}
function status(t){if(/last known|saved/i.test(t))return"Last known: the feed did not answer, so this is the last reading saved (time shown)";if(/delayed/i.test(t))return"Delayed: free feeds lag the market, usually by 15 to 20 minutes";if(/last close|closed/i.test(t))return"Last close: that market is shut";if(/FRED|Treasury|Bank of England|CFTC|EIA|ECB|dated|End of day|Positions as of/i.test(t))return"Official print: published once a day or week, dated as shown";return"Latest reading"}
function src(t,label){for(var i=0;i<SRC.length;i++){var r=SRC[i],m=r[0].exec(r[2]?label+" "+t:t);if(m&&!(r[2]&&/gold-api/i.test(t)))return r[1](m,label+"|"+t)}return[t||"See the note under the table","",""]}
function form(label,t){for(var i=0;i<FORM.length;i++)if(FORM[i][0].test(label))return FORM[i][1];if(/÷/.test(t)&&/gold|silver/i.test(label))return t;return""}
function info(el){var d=el.closest("[data-c100]");if(d){return{name:d.getAttribute("data-c100-name"),value:d.getAttribute("data-c100-value"),src:d.getAttribute("data-c100-src"),url:d.getAttribute("data-c100-url"),series:d.getAttribute("data-c100-series"),at:d.getAttribute("data-c100-at"),status:d.getAttribute("data-c100-status"),formula:d.getAttribute("data-c100-formula")}}
var tr=el.closest("tr");if(!tr)return null;var tds=tr.querySelectorAll("td");if(!tds.length)return null;var table=tr.closest("table");
var c0=tds[0].cloneNode(true);[].forEach.call(c0.querySelectorAll(".src,.c97p,.c97s"),function(x){x.remove()});var label=T(c0);
var col=el.closest("td"),ci=[].indexOf.call(tds,col);var th=table.querySelectorAll("thead th");var head=th[ci]?T(th[ci]):"";
var srcT="";var sc=tr.querySelector("td.src")||tr.querySelectorAll(".c97s");if(sc&&sc.length!==undefined){srcT=[].map.call(sc,T).join(" · ")}else if(sc)srcT=T(sc);
if(!srcT){var w=table.closest(".c99wrap")||table;var n=w.nextElementSibling;while(n&&!(n.classList&&n.classList.contains("c97s"))&&!/^H2$/.test(n.tagName))n=n.nextElementSibling;if(n&&n.classList&&n.classList.contains("c97s"))srcT=T(n)}
var sec=table.closest("section"),h2=sec&&sec.querySelector("h2"),ctxName=h2?T(h2):"";
var S=src(srcT,label),name=label+(head&&ci>1&&!/reading|level|yield$/i.test(head)?" · "+head:"")+(/Treasuries|gilts/i.test(ctxName)?" ("+ctxName+")":"");
var st=srcT.replace(/^Source:\s*/i,"");
return{name:name,value:T(col||tds[1]),src:S[0],url:S[1],series:S[2]||label,at:when(srcT)||when(T(document.querySelector("main"))),status:status(srcT),formula:form(head&&ci>1?head:label,st)}}
var pane,last;function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function open(el){var d=info(el);if(!d)return;if(!pane){pane=document.createElement("div");pane.id="c100-pane";pane.setAttribute("role","dialog");pane.setAttribute("aria-labelledby","c100-h");pane.hidden=true;document.body.appendChild(pane);pane.addEventListener("keydown",function(e){if(e.key==="Escape"){e.preventDefault();close()}if(e.key==="Tab"){var f=pane.querySelectorAll("a,button");if(!f.length)return;var a=f[0],b=f[f.length-1];if(e.shiftKey&&document.activeElement===a){e.preventDefault();b.focus()}else if(!e.shiftKey&&document.activeElement===b){e.preventDefault();a.focus()}}})}
last=el;var u=d.url?(/^\//.test(d.url)?d.url:d.url):"";
pane.innerHTML='<button type="button" class="x" aria-label="Close source details">×</button><h2 id="c100-h">'+esc(d.name||"Figure")+'</h2>'+(d.value?'<div class="v">'+esc(d.value)+'</div>':"")+'<dl><dt>Source</dt><dd>'+(u?'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+esc(d.src)+'</a>':esc(d.src))+'</dd>'+(d.series?'<dt>Series</dt><dd>'+esc(d.series)+'</dd>':"")+'<dt>Retrieved</dt><dd>'+esc(d.at||"Time shown on the page")+'</dd><dt>Status</dt><dd>'+esc(d.status||"Latest reading")+'</dd>'+(d.formula?'<dt>Formula</dt><dd>'+esc(d.formula)+'</dd>':"")+'</dl><p class="ft">Information only. Not investment advice. Capital at risk.</p>';
pane.hidden=false;pane.querySelector(".x").onclick=close;pane.querySelector(".x").focus()}
function close(){if(!pane||pane.hidden)return;pane.hidden=true;if(last&&last.focus){try{last.focus()}catch(e){}}}
function deco(){[].forEach.call(document.querySelectorAll("table.ctx tbody tr td.n:nth-child(2),table.c97t tbody td.v"),function(td){if(td.querySelector(".c100-fig")||!T(td)||td.closest("form"))return;var b=document.createElement("button");b.type="button";b.className="c100-fig";b.setAttribute("aria-haspopup","dialog");b.title="Show the source of this figure";while(td.firstChild)b.appendChild(td.firstChild);td.appendChild(b)})}
document.addEventListener("click",function(e){var t=e.target;if(!t||!t.closest)return;if(pane&&!pane.hidden&&!pane.contains(t)&&!t.closest(".c100-fig,[data-c100]"))close();var b=t.closest(".c100-fig,[data-c100]");if(b){e.preventDefault();e.stopPropagation();open(b)}},true);
document.addEventListener("keydown",function(e){if(e.key==="Escape")close()});
var tm;function sch(){clearTimeout(tm);tm=setTimeout(deco,150)}
if(document.readyState!=="loading")deco();else document.addEventListener("DOMContentLoaded",deco);
try{new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var n=ms[i].target;if(n&&n.closest&&n.closest("table"))return sch()}}).observe(document.documentElement,{childList:true,subtree:true})}catch(e){}
})();`;
{
  const c100TransformPrev = c97Transform;
  c97Transform = function (html, req) {
    const out = c100TransformPrev(html, req);
    if (typeof out !== "string" || out.indexOf('id="c100-insp"') >= 0 || !/<\/body>/i.test(out)) return out;
    return out.replace(/<\/head>/i, `<style id="c100-insp">${C100_INSP_CSS}</style></head>`).replace(/<\/body>(?![\s\S]*<\/body>)/i, `<script id="c100-insp-js">${C100_INSP_JS}</script></body>`);
  };
}
