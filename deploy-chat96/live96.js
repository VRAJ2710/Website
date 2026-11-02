(function(){
var $=function(i){return document.getElementById(i)},KEY="c96ctx",saved={},DAY=864e5;try{saved=JSON.parse(localStorage.getItem(KEY)||"{}")||{}}catch(e){}
function get(u){return new Promise(function(ok){var c=new AbortController(),t=setTimeout(function(){c.abort()},9000);fetch(u,{credentials:"same-origin",signal:c.signal}).then(function(r){return r.ok?r.json():null}).then(function(j){clearTimeout(t);ok(j)}).catch(function(){clearTimeout(t);ok(null)})})}
function n(x,dp){return Number(x).toLocaleString("en-GB",{minimumFractionDigits:dp,maximumFractionDigits:dp})}
function sg(x,dp,u){x=Number(x);return(x>0?"+":x<0?"\u2212":"")+Math.abs(x).toFixed(dp)+(u||"")}
function d8(s){var m=/^(\d{4})-(\d{2})-(\d{2})/.exec(s||"");return m?Number(m[3])+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m[2]-1]+" "+m[1]:""}
function hm(t){try{return new Date(t).toLocaleTimeString("en-GB",{timeZone:"Europe/London",hour:"2-digit",minute:"2-digit"})}catch(e){return""}}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function q(o){return o&&isFinite(Number(o.price))&&Number(o.price)>0?o:null}
// key: [desk-quotes ticker, label, prefix, decimals, unit]. Gold is not here: it has one basis, gold-api.com spot.
var DQ={silver:["SLV","Silver futures (COMEX, front month)","$",2],wtif:["WTI","WTI crude futures (NYMEX, front month)","$",2],ng:["NG","US natural gas futures (NYMEX, front month)","$",3],
dxy:["DXY","US Dollar Index (ICE)","",2],eurusd:["EURUSD","Euro in US dollars","",4],gbpusd:["GBPUSD","Pound in US dollars","",4],usdjpy:["USDJPY","US dollar in yen","",2],
tnx:["TNX","US 10-year Treasury yield","",2,"%"],spx:["SPX","S&P 500","",2],djia:["DJIA","Dow Jones Industrial Average","",2],ixic:["IXIC","Nasdaq Composite","",2],vix:["VIX","Cboe volatility index (VIX)","",2]};
var CR={btc:["BTC","Bitcoin",0],eth:["ETH","Ether",2],sol:["SOL","Solana",2]};
function srcName(o){var s=String(o.source||o.feed||"");var m=/^([^(]+)/.exec(s);return(m?m[1]:s).trim()}
function cut(a){return a.filter(Boolean).join(" \u00b7 ")}
var bodies=[].slice.call(document.querySelectorAll("tbody[data-rows]")),want={};
bodies.forEach(function(b){b.getAttribute("data-rows").split(",").forEach(function(k){want[k]=1})});
var briefEl=$("c93bh"),sigEl=$("c93sigb");if(briefEl){want.gold=want.dxy=want.ry=want.wti=want.spx=want.btc=1}
if(sigEl){for(var k0 in DQ)want[k0]=1;want.gold=1}
if(want.gold_gbp_oz||want.gold_gbp_g){want.gold=1;want.gbpusd=1}
var syms=[];for(var k in want){if(DQ[k])syms.push(DQ[k][0]);if(k==="wti")syms.push("WTI")}syms=syms.filter(function(x,i){return syms.indexOf(x)===i});
var coins=[];for(var c in CR)if(want[c])coins.push(CR[c][0]);
var needRg=briefEl||$("c93rg")||sigEl;
Promise.all([syms.length?get("/api/desk-quotes?symbols="+syms.join(",")+"&beta=1"):null,want.ry?get("/api/real-yield"):null,want.wti?get("/api/eia-spot"):null,coins.length?get("/api/crypto-snapshot?coins="+coins.join(",")+"&limit="+coins.length):null,needRg?get("/api/regime"):null,want.gold?get("/api/c96/gold-spot"):null]).then(function(a){
var dqj=a[0]||{},dq=dqj.quotes||{},ry=a[1],eia=a[2],cs=a[3],rg=a[4],gs=a[5],rows={},now=Date.now();
var lg=dqj.served==="last-good"?(dqj.servedAtUk||""):"";
Object.keys(DQ).forEach(function(k){var d=DQ[k],o=q(dq[d[0]]);if(!o)return;var pp=d[4]==="%";
var st=lg?"Delayed, as of "+lg:(o.status==="closed"?"Last close":"Delayed");
rows[k]=[d[1],d[2]+n(o.price,d[3])+(d[4]||""),pp?(o.changePp!=null?sg(o.changePp,2," pt"):""):(o.changePct!=null?sg(o.changePct,2,"%"):""),cut([st,srcName(o),lg?"":(o.asOfUk||"")]),pp?o.changePp:o.changePct]});
if(gs&&gs.available&&Number(gs.price)>0){var gt=(gs.stale?"Last known, ":"")+"gold-api.com spot \u00b7 "+(gs.asOfUk||"");rows.gold=["Gold spot, US$ per troy ounce","$"+n(gs.price,2),gs.changePct!=null?sg(gs.changePct,2,"%"):"",gt,gs.changePct];
var gb=q(dq.GBPUSD);if(gb){var oz=gs.price/Number(gb.price),bs="Gold spot \u00f7 pound in dollars ("+n(gb.price,4)+"), gold-api.com and "+(srcName(gb)||"FX feed")+" \u00b7 "+(gs.asOfUk||"");
rows.gold_gbp_oz=["Gold spot, \u00a3 per troy ounce","\u00a3"+n(oz,2),"",bs,null];rows.gold_gbp_g=["Gold spot, \u00a3 per gram","\u00a3"+n(oz/31.1034768,2),"",bs,null]}}
if(ry&&ry.available&&isFinite(Number(ry.value)))rows.ry=["US 10-year real yield",n(ry.value,2)+"%",ry.change!=null?sg(ry.change,2," pt"):"","US Treasury daily print via FRED \u00b7 "+d8(ry.date),ry.change];
var w=eia&&eia.available&&eia.WTI;if(w&&Number(w.p)>0)rows.wti=["WTI crude, official spot","$"+n(w.p,2),Number(w.prev)>0?sg((w.p/w.prev-1)*100,2,"%"):"","US EIA daily print \u00b7 "+d8(w.date),Number(w.prev)>0?(w.p/w.prev-1)*100:null];
else if(rows.wtif)rows.wti=rows.wtif;
var clg=cs&&cs.served==="last-good"?(cs.servedAtUk||""):"";
(cs&&cs.rows||[]).forEach(function(r){for(var c in CR)if(CR[c][0]===r.coin){var sn=srcName(r)||"Coinbase";
if(r.available&&Number(r.price)>0)rows[c]=[CR[c][1],"$"+n(r.price,CR[c][2]),r.changePct!=null?sg(r.changePct,2,"% 24h"):"",cut([clg?"Delayed, as of "+clg:"",sn,clg?"":(r.asOfUk||"")]),r.changePct];
else rows[c]=[CR[c][1],"No current price","","No reading from Coinbase or CoinGecko right now",null,1]}});
for(var k in rows)if(!rows[k][5])saved[k]={r:rows[k],t:now};try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){}
// Last known: a saved row is shown for up to a day, labelled with the time it was saved; older than that, the line is left out.
function pick(k){if(rows[k]&&!rows[k][5])return{r:rows[k],stale:0};if(saved[k]&&now-saved[k].t<DAY){var r=saved[k].r.slice();r[3]="Last known, saved "+hm(saved[k].t)+" UK \u00b7 "+r[3];r[2]="";r[4]=null;return{r:r,stale:1}}if(rows[k])return{r:rows[k],stale:1};return null}
bodies.forEach(function(b){var keys=b.getAttribute("data-rows").split(","),used=0,miss=0,h="";
keys.forEach(function(k){var p=pick(k);if(!p){miss++;return}if(p.stale)miss++;used++;var r=p.r,cl=r[4]==null||!r[2]?"":Number(r[4])<0?" down":Number(r[4])>0?" up":"";
h+='<tr><td>'+esc(r[0])+'<span class="src msrc">'+esc(r[3])+'</span></td><td class="n">'+esc(r[1])+'</td><td class="n'+cl+'">'+esc(r[2])+'</td><td class="src">'+esc(r[3])+'</td></tr>'});
var box=b.closest("[data-need]")||b.closest("section");b.innerHTML=h;if(box)box.hidden=!used;var note=box&&box.querySelector(".c93miss");if(note)note.hidden=!(used&&miss)});
var regime=rg&&rg.available&&rg.score!=null?rg:null,wk=document.body.getAttribute("data-wk")==="1";
function band(s){return s>=60?"60 and above":s>=45?"45 to 59":"below 45"}
function moveTxt(name,r,flat){if(!r||r[4]==null)return"";var v=Number(r[4]);return Math.abs(v)<flat?name+" little changed":name+" "+(v>0?"up ":"down ")+Math.abs(v).toFixed(1)+"%"}
if(briefEl){var gp=pick("gold"),dp=pick("dxy"),gr=gp&&!gp.stale&&gp.r,dr=dp&&!dp.stale&&dp.r;
if(regime||gr){var mood=regime?(/off/i.test(regime.label)?"Cautious":/on/i.test(regime.label)?"Risk appetite firm":"Mixed signals"):"Markets",bits=[];
var dt=moveTxt("dollar",dr,0.15);if(dt)bits.push(dt);var gt2=moveTxt("gold",gr,0.15);if(gt2)bits.push(gt2+(wk?" on Friday":""));
var p=[];if(regime)p.push("Our risk-appetite gauge reads "+String(regime.label).toLowerCase()+" ("+regime.score+" of 100; a score "+band(regime.score)+" reads that way).");
if(rows.ry)p.push("The US 10-year real yield was "+n(ry.value,2)+"% at the "+d8(ry.date)+" Treasury print"+(ry.change!=null&&Number(ry.change)!==0?", "+(ry.change<0?"down ":"up ")+Math.abs(ry.change).toFixed(2)+" points":"")+".");
if(w&&rows.wti&&rows.wti!==rows.wtif)p.push("The last official WTI crude price was $"+n(w.p,2)+" a barrel ("+d8(w.date)+").");
else if(rows.wtif&&dq.WTI)p.push("WTI crude futures last settled at $"+n(dq.WTI.price,2)+" a barrel"+(dq.WTI.changePct!=null?", "+sg(dq.WTI.changePct,1,"%")+" on the day":"")+".");
briefEl.textContent=mood+(wk?" into the weekend":"")+(bits.length?": "+bits.join(", "):"");$("c93bp").textContent=p.join(" ");
var wc=$("c96wc");if(wc){var ch=[moveTxt("Gold",gr,0.15),moveTxt("the dollar",dr,0.15),moveTxt("the S&P 500",pick("spx")&&!pick("spx").stale&&pick("spx").r,0.2),moveTxt("Bitcoin",pick("btc")&&!pick("btc").stale&&pick("btc").r,0.5)].filter(Boolean);if(ch.length){wc.textContent="What changed since the previous close: "+ch.join("; ")+".";wc.hidden=false}}
var pl=$("c96pvl");if(pl){var li=[];if(briefEl.textContent)li.push(briefEl.textContent+".");if(p[1])li.push(p[1]);else if(p[0])li.push(p[0]);if(li.length){pl.innerHTML=li.slice(0,2).map(function(x){return"<li>"+esc(x)+"</li>"}).join("");$("c96pv").hidden=false}}
var rx=$("c96rx");if(rx&&regime){rx.innerHTML="Risk gauge: "+esc(String(regime.label).toLowerCase())+" ("+esc(regime.score)+" of 100). Below 45 reads risk-off, 45 to 59 mixed, 60 and above risk-on. <a href=\"/methodology#regime\">How it works</a>";rx.hidden=false}
var bd=0;[gr&&gs&&gs.asOf,dr&&dq[DQ.dxy[0]]&&dq[DQ.dxy[0]].asOf].forEach(function(s){var t=Date.parse(s||"");if(t&&t>bd)bd=t});var ukd=function(t,o){return new Date(t).toLocaleDateString("en-GB",Object.assign({timeZone:"Europe/London"},o))},DO={weekday:"long",day:"numeric",month:"long"};var old=!bd||ukd(bd,{year:"numeric",month:"2-digit",day:"2-digit"})!==ukd(now,{year:"numeric",month:"2-digit",day:"2-digit"});var bk=$("c93bk");if(bk&&old)bk.textContent=bd?"Latest brief \u00b7 "+ukd(bd,DO):"Latest brief";$("c93bt").textContent=old?(bd?"Built from the last market close, "+ukd(bd,DO)+", "+hm(bd)+" UK":"Built from the latest available data"):"Built from today's data at "+hm(now)+" UK";var up=$("c96upd");if(up)up.textContent=hm(now)+" UK";var bx=$("c93brief");if(bx)bx.hidden=false}}
var rgEl=$("c93rg");if(rgEl&&regime){var ins=regime.inputs||{};
$("c93rgv").textContent=regime.score+" of 100 \u00b7 "+regime.label;
$("c93rgp").innerHTML=esc("The gauge combines five free inputs: the VIX"+(ins.vix!=null?" ("+n(ins.vix,2)+")":"")+", the S&P 500 move"+(ins.spx!=null?" ("+sg(ins.spx,2,"%")+")":"")+", the US Dollar Index"+(ins.dxy!=null?" ("+n(ins.dxy,2)+")":"")+", oil"+(ins.oil!=null?" ($"+n(ins.oil,2)+")":"")+" and the Bitcoin move"+(ins.btc!=null?" ("+sg(ins.btc,2,"%")+")":"")+". A score "+band(regime.score)+" reads as "+String(regime.label).toLowerCase()+": below 45 is risk-off, 45 to 59 mixed, 60 and above risk-on. It describes conditions; it is not a forecast or a recommendation. ")+'<a href="/methodology#regime">How it works</a>';
$("c93rgs").textContent="Dispatch rules-based gauge; inputs: VIX, S&P 500, US Dollar Index and oil from delayed exchange feeds, Bitcoin from Coinbase \u00b7 computed "+(regime.computedAtUk||regime.asOfUk||"");rgEl.hidden=false}
if(sigEl){var LINE=1.5,h2="",cnt=0;["gold"].concat(Object.keys(DQ),Object.keys(CR)).forEach(function(k){var p=pick(k);if(!p||p.stale||p.r[4]==null||DQ[k]&&DQ[k][4]==="%")return;var v=Number(p.r[4]);if(Math.abs(v)<LINE)return;cnt++;
h2+='<tr><td>'+esc(p.r[0])+'<span class="src msrc">'+esc(p.r[3])+'</span></td><td class="n">'+esc(p.r[1])+'</td><td class="n'+(v<0?" down":" up")+'">'+esc(p.r[2])+'</td><td class="src">'+esc(p.r[3])+'</td></tr>'});
sigEl.innerHTML=h2;var sb=sigEl.closest("[data-need]");if(sb)sb.hidden=!cnt;var sn=$("c93sign");if(sn)sn.hidden=!!cnt}
document.querySelectorAll(".grid[data-auto]").forEach(function(g){var vis=[].filter.call(g.children,function(x){return!x.hidden}).length;if(!vis)g.closest("section").hidden=true;else if(vis<2)g.style.gridTemplateColumns="1fr"})})})();
