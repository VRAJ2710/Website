(function(){
"use strict";
if(window.__c107)return;window.__c107=1;
var CFG=window.__c107cfg||{d:{},eia:false,hide:{}};
var CAT={
DGS10:["Board of Governors of the Federal Reserve System (US)","Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis"],
DFII10:["Board of Governors of the Federal Reserve System (US)","Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis, Inflation-Indexed"],
DTWEXBGS:["Board of Governors of the Federal Reserve System (US)","Nominal Broad U.S. Dollar Index"],
DCOILWTICO:["U.S. Energy Information Administration","Crude Oil Prices: West Texas Intermediate (WTI) - Cushing, Oklahoma"],
DCOILBRENTEU:["U.S. Energy Information Administration","Crude Oil Prices: Brent - Europe"],
PAYEMS:["U.S. Bureau of Labor Statistics","All Employees, Total Nonfarm"],
UNRATE:["U.S. Bureau of Labor Statistics","Unemployment Rate"],
CPIAUCSL:["U.S. Bureau of Labor Statistics","Consumer Price Index for All Urban Consumers: All Items in U.S. City Average"],
PCEPI:["U.S. Bureau of Economic Analysis","Personal Consumption Expenditures: Chain-type Price Index"],
A191RL1Q225SBEA:["U.S. Bureau of Economic Analysis","Real Gross Domestic Product"],
DFEDTARU:["Board of Governors of the Federal Reserve System (US)","Federal Funds Target Range - Upper Limit"],
DFEDTARL:["Board of Governors of the Federal Reserve System (US)","Federal Funds Target Range - Lower Limit"]
};
var D=document;
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function cite(id){var c=CAT[id];if(!c)return"";var u="https://fred.stlouisfed.org/series/"+id,d=CFG.d&&CFG.d[id];
return esc(c[0])+", "+esc(c[1])+" ["+id+"], retrieved from FRED, Federal Reserve Bank of St. Louis; <a href=\""+u+"\" rel=\"noopener\">"+u+"</a>"+(d?", "+esc(d):"")}
function rowText(el){var r=el.closest&&el.closest("tr,.v3-pt,li");return r?(r.textContent||""):(el.textContent||"")}
function idsFor(el,t){
var out=[],m,re;
if(/\(FRED ([A-Z0-9]+(?:, [A-Z0-9]+)*)\)/.test(t)){re=/\(FRED ([A-Z0-9]+(?:, [A-Z0-9]+)*)\)/g;while((m=re.exec(t)))m[1].split(", ").forEach(function(x){if(CAT[x])out.push(x)});}
if(/^Official daily:/.test(t.trim())&&/US Treasury via FRED/.test(t))out.push(/real yield|TIPS|inflation-protected/i.test(rowText(el))?"DFII10":"DGS10");
if(/FRED, US 10-year Treasury yield/.test(t))out.push("DGS10");
if(/FRED, US 10-year real yield \(TIPS\)|10-year real yield \(TIPS\), FRED/.test(t))out.push("DFII10");
if(/broad trade-weighted US dollar index, FRED/i.test(t))out.push("DTWEXBGS");
if(CFG.eia&&/US EIA (spot|daily print)/.test(t))out.push(/Brent/i.test(rowText(el))?"DCOILBRENTEU":"DCOILWTICO");
return out}
function box(el){
var c=el.closest("article,.v3-card,table,section,.c101card")||el.parentNode;
if(c&&c.tagName==="TABLE"){var w=c.parentNode&&c.parentNode.classList&&c.parentNode.classList.contains("c101d-tw")?c.parentNode:c;return{key:w,after:true}}
return{key:c,after:false}}
function holder(b){
if(b.key.__c107h&&b.key.__c107h.isConnected)return b.key.__c107h;
var h=D.createElement("div");h.className="c107-cites";h.setAttribute("data-c107","1");
if(b.after)b.key.parentNode.insertBefore(h,b.key.nextSibling);else b.key.appendChild(h);
b.key.__c107h=h;return h}
function hideFig(el){var r=el.closest("tr,.v3-pt,li,p");if(!r||r.getAttribute("data-c107-hidden"))return;r.setAttribute("data-c107-hidden","1");var N="<span class=\"c107-hold\">Not shown: awaiting publisher permission</span>";if(r.tagName==="TR"&&r.cells&&r.cells.length>1){for(var i=1;i<r.cells.length;i++)r.cells[i].innerHTML=i===1?N:""}else r.innerHTML=N}
function add(el,id){if(CFG.hide&&CFG.hide[id]){hideFig(el);return}
var b=box(el);if(!b.key||!b.key.parentNode)return;var h=holder(b);if(h.querySelector("[data-id=\""+id+"\"]"))return;
var p=D.createElement("p");p.className="c107-cite";p.setAttribute("data-id",id);p.innerHTML=cite(id);h.appendChild(p)}
function fiscal(){var as=D.querySelectorAll("a[href*=\"fiscaldata.treasury.gov\"]"),i;for(i=0;i<as.length;i++){var a=as[i];if(a.closest(".c107-cites,.c107-meth,footer"))continue;var b=box(a);if(!b.key||!b.key.parentNode)continue;var h=holder(b);if(h.querySelector("[data-id=\"fiscal\"]"))continue;var p=D.createElement("p");p.className="c107-cite";p.setAttribute("data-id","fiscal");p.innerHTML="Source: <a href=\"https://fiscaldata.treasury.gov\" rel=\"noopener\">U.S. Treasury, Fiscal Data</a>";h.appendChild(p)}}
function scan(){
if(!D.body)return;
var tw=D.createTreeWalker(D.body,NodeFilter.SHOW_TEXT),n,list=[];
while((n=tw.nextNode())){var v=n.nodeValue;if(v&&/FRED|US EIA/.test(v))list.push(n)}
list.forEach(function(n){var p=n.parentElement;if(!p||/^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(p.tagName)||p.closest(".c107-cites,footer,.c107-meth"))return;
var t=p.textContent||"";if(t.length>400)return;idsFor(p,t).forEach(function(id){add(p,id)});
var v=n.nodeValue,nv=v.replace(/\(FRED ([A-Z0-9]+(?:, [A-Z0-9]+)*)\)/g,function(all,ids){var l=ids.split(", ");for(var i=0;i<l.length;i++)if(!CAT[l[i]])return all;return"(FRED)"});if(nv!==v)n.nodeValue=nv});
var as=D.querySelectorAll("a[href*=\"fred.stlouisfed.org/series/\"]"),i;for(i=0;i<as.length;i++){var a=as[i];if(a.closest(".c107-cites,footer,.c107-meth"))continue;var m=/series\/([A-Z0-9]+)/.exec(a.getAttribute("href")||"");if(m&&CAT[m[1]])add(a,m[1])}
var mk=D.querySelectorAll("[data-c107-ids]"),k;for(k=0;k<mk.length;k++){var e=mk[k];if(e.closest(".c107-cites,footer,.c107-meth"))continue;var host=e.parentElement||e;(e.getAttribute("data-c107-ids")||"").split(",").forEach(function(x){if(CAT[x])add(host,x)})}
fiscal()}
var tm=0;function soon(){if(tm)return;tm=setTimeout(function(){tm=0;try{scan()}catch(e){}},250)}
function boot(){try{scan()}catch(e){}try{new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var t=ms[i].target;if(t&&t.closest&&t.closest(".c107-cites"))continue;soon();return}}).observe(D.body,{childList:true,subtree:true,characterData:true})}catch(e){}}
if(D.readyState==="loading")D.addEventListener("DOMContentLoaded",boot);else boot();
})();
