(function(){
var $=function(i){return document.getElementById(i)},KEY="c93ctx2",saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||"{}")||{}}catch(e){}
function get(u){return new Promise(function(ok){var c=new AbortController(),t=setTimeout(function(){c.abort()},9000);fetch(u,{credentials:"same-origin",signal:c.signal}).then(function(r){return r.ok?r.json():null}).then(function(j){clearTimeout(t);ok(j)}).catch(function(){clearTimeout(t);ok(null)})})}
function n(x,dp){return Number(x).toLocaleString("en-GB",{minimumFractionDigits:dp,maximumFractionDigits:dp})}
function sg(x,dp,u){x=Number(x);return(x>0?"+":x<0?"\u2212":"")+Math.abs(x).toFixed(dp)+(u||"")}
function d8(s){var m=/^(\d{4})-(\d{2})-(\d{2})/.exec(s||"");return m?Number(m[3])+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m[2]-1]+" "+m[1]:""}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function q(o){return o&&isFinite(Number(o.price))&&Number(o.price)>0?o:null}
// key: [desk-quotes ticker, label, prefix, decimals, unit]
var DQ={gold:["XAU","Gold futures (COMEX, GC=F)","$",2],silver:["SLV","Silver futures (COMEX, SI=F)","$",2],wtif:["WTI","WTI crude futures (CL=F)","$",2],ng:["NG","US natural gas futures (NG=F)","$",3],
dxy:["DXY","US Dollar Index (ICE)","",2],eurusd:["EURUSD","Euro in US dollars","",4],gbpusd:["GBPUSD","Pound in US dollars","",4],usdjpy:["USDJPY","US dollar in yen","",2],
tnx:["TNX","US 10-year Treasury yield","",2,"%"],spx:["SPX","S&P 500","",2],djia:["DJIA","Dow Jones Industrial Average","",2],ixic:["IXIC","Nasdaq Composite","",2],vix:["VIX","Cboe volatility index (VIX)","",2]};
var CR={btc:["BTC","Bitcoin",0],eth:["ETH","Ether",2],sol:["SOL","Solana",2]};
function srcName(o){var s=String(o.source||"");var m=/^([^(]+)/.exec(s);return(m?m[1]:s).trim()||"Yahoo Finance"}
var bodies=[].slice.call(document.querySelectorAll("tbody[data-rows]")),want={};
bodies.forEach(function(b){b.getAttribute("data-rows").split(",").forEach(function(k){want[k]=1})});
var briefEl=$("c93bh"),sigEl=$("c93sigb");if(briefEl){want.gold=want.dxy=want.ry=want.wti=1}
if(sigEl)for(var k0 in DQ)want[k0]=1;
var syms=[];for(var k in want){if(DQ[k])syms.push(DQ[k][0]);if(k==="wti")syms.push("WTI")}
var coins=[];for(var c in CR)if(want[c])coins.push(CR[c][0]);
var needRg=briefEl||$("c93rg")||sigEl;
Promise.all([syms.length?get("/api/desk-quotes?symbols="+syms.join(",")+"&beta=1"):null,want.ry?get("/api/real-yield"):null,want.wti?get("/api/eia-spot"):null,coins.length?get("/api/crypto-snapshot?coins="+coins.join(",")+"&limit="+coins.length):null,needRg?get("/api/regime"):null]).then(function(a){
var dq=a[0]&&a[0].quotes||{},ry=a[1],eia=a[2],cs=a[3],rg=a[4],rows={},now=Date.now();
Object.keys(DQ).forEach(function(k){var d=DQ[k],o=q(dq[d[0]]);if(!o)return;var pp=d[4]==="%";
rows[k]=[d[1],d[2]+n(o.price,d[3])+(d[4]||""),pp?(o.changePp!=null?sg(o.changePp,2," pt"):""):(o.changePct!=null?sg(o.changePct,2,"%"):""),(o.status==="closed"?"Last close":"Delayed")+", "+srcName(o)+" \u00b7 "+(o.asOfUk||""),pp?o.changePp:o.changePct]});
if(ry&&ry.available&&isFinite(Number(ry.value)))rows.ry=["US 10-year real yield",n(ry.value,2)+"%",ry.change!=null?sg(ry.change,2," pt"):"","US Treasury daily print \u00b7 "+d8(ry.date),ry.change];
var w=eia&&eia.available&&eia.WTI;if(w&&Number(w.p)>0)rows.wti=["WTI crude, official spot","$"+n(w.p,2),Number(w.prev)>0?sg((w.p/w.prev-1)*100,2,"%"):"","US EIA daily print \u00b7 "+d8(w.date),Number(w.prev)>0?(w.p/w.prev-1)*100:null];
else if(rows.wtif)rows.wti=rows.wtif;
(cs&&cs.rows||[]).forEach(function(r){for(var c in CR)if(CR[c][0]===r.coin&&r.available&&Number(r.price)>0)rows[c]=[CR[c][1],"$"+n(r.price,CR[c][2]),r.changePct!=null?sg(r.changePct,2,"% 24h"):"","Coinbase \u00b7 "+(r.asOfUk||""),r.changePct]});
for(var k in rows)saved[k]={r:rows[k],t:now};try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){}
function pick(k){if(rows[k])return{r:rows[k],stale:0};if(saved[k]&&now-saved[k].t<12096e5)return{r:saved[k].r,stale:1};return null}
bodies.forEach(function(b){var keys=b.getAttribute("data-rows").split(","),used=0,miss=0,h="";
keys.forEach(function(k){var p=pick(k);if(!p){miss++;return}if(p.stale)miss++;used++;var r=p.r,cl=r[4]==null||!r[2]?"":Number(r[4])<0?" down":Number(r[4])>0?" up":"";
h+='<tr><td>'+esc(r[0])+'<span class="src msrc">'+esc(r[3])+'</span></td><td class="n">'+esc(r[1])+'</td><td class="n'+cl+'">'+esc(r[2])+'</td><td class="src">'+esc(r[3])+'</td></tr>'});
var box=b.closest("[data-need]")||b.closest("section");b.innerHTML=h;if(box)box.hidden=!used;var note=box&&box.querySelector(".c93miss");if(note)note.hidden=!(used&&miss)});
var regime=rg&&rg.available&&rg.score!=null?rg:null,wk=document.body.getAttribute("data-wk")==="1";
if(briefEl){var gp=pick("gold"),dp=pick("dxy"),gr=gp&&gp.r,dr=dp&&dp.r;
if(regime||gr){var mood=regime?(/off/i.test(regime.label)?"Cautious":/on/i.test(regime.label)?"Risk appetite firm":"Mixed signals"):"Markets",bits=[];
if(dr&&dr[4]!=null){var dv=Number(dr[4]);bits.push(Math.abs(dv)<0.15?"dollar steady":"dollar "+(dv>0?"up ":"down ")+Math.abs(dv).toFixed(1)+"%")}
if(gr&&gr[4]!=null){var gv=Number(gr[4]);bits.push(Math.abs(gv)<0.15?"gold little changed":"gold "+(gv<0?"off ":"up ")+Math.abs(gv).toFixed(1)+"%"+(wk?" on Friday":""))}
var p=[];if(regime)p.push("Our risk-appetite gauge reads "+String(regime.label).toLowerCase()+" ("+regime.score+" of 100).");
if(rows.ry)p.push("The US 10-year real yield was "+n(ry.value,2)+"% at the "+d8(ry.date)+" Treasury print"+(ry.change!=null&&Number(ry.change)!==0?", "+(ry.change<0?"down ":"up ")+Math.abs(ry.change).toFixed(2)+" points":"")+".");
if(w&&rows.wti&&rows.wti!==rows.wtif)p.push("The last official WTI crude price was $"+n(w.p,2)+" a barrel ("+d8(w.date)+").");
else if(rows.wtif&&dq.WTI)p.push("WTI crude futures last settled at $"+n(dq.WTI.price,2)+" a barrel"+(dq.WTI.changePct!=null?", "+sg(dq.WTI.changePct,1,"%")+" on the day":"")+".");
briefEl.textContent=mood+(wk?" into the weekend":"")+(bits.length?": "+bits.join(", "):"");$("c93bp").textContent=p.join(" ");
$("c93bt").textContent="Built from today's data at "+new Date().toLocaleTimeString("en-GB",{timeZone:"Europe/London",hour:"2-digit",minute:"2-digit"})+" UK";var bx=$("c93brief");if(bx)bx.hidden=false}}
var rgEl=$("c93rg");if(rgEl&&regime){var ins=regime.inputs||{},band=regime.score>=60?"60 and above":regime.score>=45?"45 to 59":"below 45";
$("c93rgv").textContent=regime.score+" of 100 \u00b7 "+regime.label;
$("c93rgp").textContent="The gauge combines five free inputs: the VIX"+(ins.vix!=null?" ("+n(ins.vix,2)+")":"")+", the S&P 500 move"+(ins.spx!=null?" ("+sg(ins.spx,2,"%")+")":"")+", the US Dollar Index"+(ins.dxy!=null?" ("+n(ins.dxy,2)+")":"")+", oil"+(ins.oil!=null?" ($"+n(ins.oil,2)+")":"")+" and the Bitcoin move"+(ins.btc!=null?" ("+sg(ins.btc,2,"%")+")":"")+". A score "+band+" reads as "+String(regime.label).toLowerCase()+". It describes conditions; it is not a forecast or a recommendation.";
$("c93rgs").textContent="Dispatch model, inputs from Yahoo Finance and Coinbase \u00b7 computed "+(regime.computedAtUk||regime.asOfUk||"");rgEl.hidden=false}
if(sigEl){var LINE=1.5,h2="",cnt=0;Object.keys(DQ).concat(Object.keys(CR)).forEach(function(k){var p=pick(k);if(!p||p.r[4]==null||DQ[k]&&DQ[k][4]==="%")return;var v=Number(p.r[4]);if(Math.abs(v)<LINE)return;cnt++;
h2+='<tr><td>'+esc(p.r[0])+'<span class="src msrc">'+esc(p.r[3])+'</span></td><td class="n">'+esc(p.r[1])+'</td><td class="n'+(v<0?" down":" up")+'">'+esc(p.r[2])+'</td><td class="src">'+esc(p.r[3])+'</td></tr>'});
sigEl.innerHTML=h2;var sb=sigEl.closest("[data-need]");if(sb)sb.hidden=!cnt;var sn=$("c93sign");if(sn)sn.hidden=!!cnt}
document.querySelectorAll(".grid[data-auto]").forEach(function(g){var vis=[].filter.call(g.children,function(x){return!x.hidden}).length;if(!vis)g.closest("section").hidden=true;else if(vis<2)g.style.gridTemplateColumns="1fr"})})})();
