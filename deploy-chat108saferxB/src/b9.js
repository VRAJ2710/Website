/* chat108saferxB: market colours and icons on the existing v3 cards, bitcoin and WTI from the existing market-context table
   into the key-price strip, and the sticky offset for the split story. No network, no storage; reads only the page. */
(function(){
"use strict";
if(window.__v9b)return;window.__v9b=1;
var D=document;
var IC={gold:'<path d="M3 19h18l-2.5-6h-13z"/><path d="M7.5 13 9.5 7h5l2 6"/>',
dollar:'<circle cx="12" cy="12" r="9"/><path d="M14.6 9.2c-.5-1-1.5-1.5-2.8-1.5-1.5 0-2.6.8-2.6 2s1.1 1.7 2.7 2c1.7.3 2.8.9 2.8 2.2s-1.2 2.1-2.8 2.1c-1.3 0-2.4-.6-2.9-1.6M12 6v1.7M12 16.3V18"/>',
yields:'<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.3"/><circle cx="17" cy="17" r="2.3"/>',
oil:'<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
crypto:'<path d="M12 2.8 20 7.4v9.2L12 21.2 4 16.6V7.4z"/><path d="M10 8.5h3a1.75 1.75 0 0 1 0 3.5h-3zm0 3.5h3.5a1.75 1.75 0 0 1 0 3.5H10zM10 8.5v7"/>',
equities:'<path d="M7 4v16M17 4v16"/><rect x="5" y="8" width="4" height="7" rx="1"/><rect x="15" y="6" width="4" height="9" rx="1"/>'};
function mk(t){t=String(t||"").toLowerCase();
 if(/gold|silver|platinum/.test(t))return"gold";
 if(/bitcoin|ether|crypto|solana/.test(t))return"crypto";
 if(/crude|brent|wti|oil|natural gas/.test(t))return"oil";
 if(/yield|treasury|gilt|bank rate/.test(t))return"yields";
 if(/dollar|pound|euro|yen|sterling/.test(t))return"dollar";
 if(/s&p|s&amp;p|nasdaq|dow|ftse|stock|equit|index \(context\)|vix/.test(t))return"equities";
 return"";}
function icon(m){var s=D.createElement("span");s.className="v9-mi";s.setAttribute("aria-hidden","true");s.innerHTML='<svg viewBox="0 0 24 24">'+IC[m]+"</svg>";return s}
function tagEl(el,nameEl){if(!el||!nameEl)return;var m=mk(nameEl.textContent);if(!m)return;if(el.getAttribute("data-mk")!==m)el.setAttribute("data-mk",m);if(!nameEl.querySelector(".v9-mi"))nameEl.insertBefore(icon(m),nameEl.firstChild)}
function tagAll(){
 Array.prototype.forEach.call(D.querySelectorAll("#v3-prices .v3-pt,#v3-tiles .v3-tile"),function(t){tagEl(t,t.querySelector(".n"))});
 Array.prototype.forEach.call(D.querySelectorAll("#v3-moves .v3-ul li"),function(li){var b=li.querySelector("b");if(b)tagEl(li,b)});
 var g=D.getElementById("v3-gold");if(g&&!g.getAttribute("data-mk"))g.setAttribute("data-mk","gold");}
/* bitcoin and WTI: copied (text only) from the existing market-context table rows, with their own source, time and lag */
function lagOf(s){s=String(s||"");return /stale|stored/i.test(s)?["Stale","st"]:/official daily|EIA/i.test(s)?["Official daily","ok"]:/last close|closed/i.test(s)?["Last close",""]:/delayed/i.test(s)?["Delayed","ok"]:/live/i.test(s)?["Live","ok"]:["Delay not stated",""]}
function extraRows(){var out=[],tb=D.querySelector("#c93top table.ctx tbody");if(!tb)return out;
 Array.prototype.forEach.call(tb.querySelectorAll("tr"),function(tr){var td=tr.children;if(td.length<4)return;
  var c0=td[0].cloneNode(true);Array.prototype.forEach.call(c0.querySelectorAll(".msrc"),function(x){x.remove()});var name=c0.textContent.replace(/\s+/g," ").trim();
  var key=/^bitcoin/i.test(name)?"btc":/^wti/i.test(name)?"wti":"";if(!key)return;
  var lvl=td[1].textContent.trim();if(!lvl)return;
  var src="";for(var i=0;i<td[3].childNodes.length;i++){var n=td[3].childNodes[i];if(n.nodeType===3)src+=n.nodeValue}src=src.replace(/\s+/g," ").trim()||td[3].textContent.trim();
  out.push({key:key,name:name,lvl:lvl,chg:td[2].textContent.trim(),dir:/\bup\b/.test(td[2].className)?"v3-up":/\bdown\b/.test(td[2].className)?"v3-down":"v3-flat",src:src})});
 return out}
function el(tag,cls,txt){var e=D.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e}
function addExtras(){var grid=D.querySelector("#v3-prices .v3-prices");if(!grid)return;
 Array.prototype.forEach.call(grid.querySelectorAll("[data-v9x]"),function(x){x.remove()});
 var have=Array.prototype.map.call(grid.querySelectorAll(".v3-pt .n"),function(n){return n.textContent.toLowerCase()}).join("|");
 extraRows().forEach(function(r){if(r.key==="btc"&&/bitcoin/.test(have))return;if(r.key==="wti"&&/wti/.test(have))return;
  var t=el("div","v3-pt");t.setAttribute("data-v9x",r.key);t.appendChild(el("div","n",r.name));t.appendChild(el("div","v",r.lvl));
  t.appendChild(el("span","c "+(r.chg?r.dir:"v3-flat"),r.chg||"No change figure"));
  var p=el("p","v3-src",r.src+" ");var lg=lagOf(r.src);p.appendChild(el("span","v3-lag "+lg[1],lg[0]));t.appendChild(p);grid.appendChild(t)});}
var busy=false,mo=null,WATCH=["v3-prices","v3-tiles","v3-moves","v3-gold"];
function run(){if(busy)return;busy=true;if(mo)mo.disconnect();try{addExtras();tagAll()}catch(e){}observe();busy=false}
function observe(){if(!mo)return;WATCH.forEach(function(id){var x=D.getElementById(id);if(x)mo.observe(x,{childList:true})});var tb=D.querySelector("#c93top table.ctx tbody");if(tb)mo.observe(tb,{childList:true})}
if("MutationObserver" in window){mo=new MutationObserver(function(){window.requestAnimationFrame(run)})}
run();
/* sticky offset: under the sticky tape, header and desk tabs */
var story=D.getElementById("v9-story"),tabs=D.querySelector(".v8-tabs"),hdr=D.querySelector("header.site");
function top(){if(!story)return;var t=12;if(hdr){var c=window.getComputedStyle(hdr);if(c.position==="sticky"||c.position==="fixed")t+=(parseFloat(c.top)||0)+hdr.offsetHeight}if(tabs&&window.getComputedStyle(tabs).position==="sticky")t+=tabs.offsetHeight;story.style.setProperty("--v9-top",Math.round(t)+"px")}
top();window.addEventListener("resize",top,{passive:true});
})();
