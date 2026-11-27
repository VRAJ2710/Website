/* chat105v3home2: v3 home preview renderer. Reads existing same-origin free feeds only. */
(function(){
"use strict";
if(window.__v3p)return;window.__v3p=1;
var D=document,root=D.getElementById("v3home");if(!root)return;
var NAMES={"GC=F":"Gold futures (COMEX, front month)","DX-Y.NYB":"US dollar index (ICE)","^TNX":"US 10-year Treasury yield","BZ=F":"Brent crude futures (front month)","BTC-USD":"Bitcoin in US dollars","^GSPC":"S&P 500 index","^VIX":"VIX (US stock-market fear gauge)"};
function $(id){return D.getElementById(id)}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function safeUrl(u){u=String(u||"");return /^https?:\/\//i.test(u)||/^\/(?!\/)/.test(u)?u:"#"}
function get(u){return new Promise(function(ok){var c=window.AbortController?new AbortController():null,t=setTimeout(function(){try{c&&c.abort()}catch(e){}},12000);fetch(u,{credentials:"same-origin",signal:c?c.signal:undefined,headers:{"Accept":"application/json"}}).then(function(r){return r.ok?r.json():null}).then(function(j){clearTimeout(t);ok(j)}).catch(function(){clearTimeout(t);ok(null)})})}
function uk(ms,withDay){if(!isFinite(ms))return"";try{var o={timeZone:"Europe/London",hour:"2-digit",minute:"2-digit",hourCycle:"h23"};if(withDay!==false){o.weekday="short";o.day="numeric";o.month="short"}return new Intl.DateTimeFormat("en-GB",o).format(new Date(ms)).replace(/,(?=[^,]*$)/,",")+" UK"}catch(e){return""}}
function ukDate(ms){try{return new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/London",day:"numeric",month:"short"}).format(new Date(ms))}catch(e){return""}}
function ago(ms){var m=Math.round((Date.now()-ms)/60000);if(!isFinite(m))return"";if(m<1)return"updated just now";if(m<60)return"updated "+m+" min ago";var h=Math.floor(m/60);if(h<48)return"updated "+h+" h "+(m%60)+" min ago";return"updated "+Math.floor(h/24)+" days ago"}
function nf(x,dp){return Number(x).toLocaleString("en-GB",{minimumFractionDigits:dp,maximumFractionDigits:dp})}
function sg(x,dp,u){x=Number(x);var s=x>0?"+":x<0?"\u2212":"";return s+Math.abs(x).toFixed(dp)+(u||"")}
function cls(x){x=Number(x);return x>0.004?"v3-up":x<-0.004?"v3-down":"v3-flat"}
function noUK(s){return String(s||"").replace(/\bUK UK\b/g,"UK")}
/* reader text: never show raw ticker or series codes */
function plain(s){var t=String(s==null?"":s);
 t=t.replace(/;?\s*FRED series [A-Z0-9]+/g,"").replace(/\s*\((?:FRED )?[A-Z]{3,}[A-Z0-9]*(?:,\s*[A-Z]{3,}[A-Z0-9]*)*\)/g,function(m){return /[a-z]/.test(m)?m:""});
 t=t.replace(/\bGC=F\b/g,"gold futures (COMEX, front month)").replace(/\bSI=F\b/g,"silver futures").replace(/\bBZ=F\b/g,"Brent futures").replace(/\bCL=F\b/g,"WTI futures").replace(/\bDX-Y\.NYB\b/g,"ICE dollar index").replace(/\^TNX\b/g,"US 10-year yield").replace(/\^VIX\b/g,"VIX").replace(/\^GSPC\b/g,"S&P 500").replace(/\bBTC-USD\b/g,"Bitcoin").replace(/\bgold-api-spot-proxy(?:-browser)?\b/g,"gold-api.com spot price");
 return noUK(t.replace(/\s{2,}/g," ").trim())}
function lagCls(s){s=String(s||"").toLowerCase();return /stale|stored|old|unavailable/.test(s)?"st":/live|delayed|ok|computed/.test(s)?"ok":""}
function lag(s){return s?'<span class="v3-lag '+lagCls(s)+'">'+esc(s)+'</span>':""}
function empty(msg){return '<div class="v3-empty">'+esc(msg||"This feed didn't answer just now. We'll try again in two minutes.")+'</div>'}
function pctOf(s){var m=/\(?([+\u2212\-]?\d+(?:\.\d+)?)%\)?/.exec(String(s||""));if(!m)return null;return Number(m[1].replace("\u2212","-"))}
function asOfParts(a){a=String(a||"");var m=/^(\w[\w ]*?)\s*\u00b7\s*as of\s*(.*)$/.exec(a);return m?{lag:m[1],time:noUK(m[2])}:{lag:"",time:noUK(a)}}
/* sparkline / area chart */
function spark(vals,w,h,area,col){var v=vals.filter(function(x){return x!=null&&isFinite(x)});if(v.length<2)return"";var mn=Math.min.apply(null,v),mx=Math.max.apply(null,v),r=mx-mn||1,p=3;var pts=v.map(function(x,i){return[(i/(v.length-1))*(w-2*p)+p,h-p-((x-mn)/r)*(h-2*p)]});var d=pts.map(function(q,i){return(i?"L":"M")+q[0].toFixed(1)+" "+q[1].toFixed(1)}).join("");var up=v[v.length-1]>=v[0];var c=col||(up?"var(--v-up)":"var(--v-down)");var id="g"+Math.random().toString(36).slice(2,8);var s='<svg viewBox="0 0 '+w+' '+h+'" preserveAspectRatio="none" aria-hidden="true">';if(area)s+='<defs><linearGradient id="'+id+'" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="'+c+'" stop-opacity=".32"/><stop offset="1" stop-color="'+c+'" stop-opacity="0"/></linearGradient></defs><path d="'+d+"L"+pts[pts.length-1][0].toFixed(1)+" "+h+"L"+pts[0][0].toFixed(1)+" "+h+'Z" fill="url(#'+id+')"/>';s+='<path d="'+d+'" fill="none" stroke="'+c+'" stroke-width="'+(area?2:1.8)+'" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"/></svg>';return s}
function closes(y){try{var r=y.chart.result[0],ts=r.timestamp||[],c=r.indicators.quote[0].close||[],out=[];for(var i=0;i<c.length;i++)if(c[i]!=null&&isFinite(c[i]))out.push({t:ts[i]*1000,c:c[i]});return{meta:r.meta||{},pts:out}}catch(e){return null}}
var ICON={mail:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',doc:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 3h9l4 4v14H6z"/><path d="M9 11h7M9 15h7M9 7h3"/></svg>',gauge:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 16a8 8 0 1 1 16 0"/><path d="m12 16 4-5"/></svg>',chart:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 20h18"/><path d="m4 15 5-5 4 3 7-7"/></svg>',cal:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',list:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/></svg>',coin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="7" rx="7" ry="3"/><path d="M5 7v5c0 1.7 3.1 3 7 3s7-1.3 7-3V7M5 12v5c0 1.7 3.1 3 7 3s7-1.3 7-3v-5"/></svg>'};
function k(icon,label,go){return '<div class="v3-k">'+(ICON[icon]||"")+'<span>'+esc(label)+'</span>'+(go?'<a class="v3-go" href="'+esc(go[0])+'">'+esc(go[1])+' \u2192</a>':"")+'</div>'}
var S={};
/* 1. Market snapshot */
function rSnap(){var el=$("v3-snap");if(!el)return;var e=S.ed,mac=S.mac,rg=S.rg,h=k("doc","Market snapshot \u00b7 today's main theme",["/brief/","Read the brief"]);
 if(!e||!e.lead||!e.lead.headline){el.innerHTML=h+empty("Today's brief theme isn't available just now. We'll try again in two minutes.");return}
 var upMs=Date.parse(e.updatedAt||e.checkedAt||""),L=e.lead;
 h+='<h2 class="v3-h">'+esc(plain(L.headline))+'</h2>';
 h+='<div class="v3-chips">'+(e.label?'<span class="v3-chip"><b>'+esc(e.label)+'</b></span>':"")+'<span class="v3-chip">Lead story: <b>'+esc(plain(L.source||""))+'</b>'+(L.publishedAtUk?", "+esc(noUK(L.publishedAtUk)):"")+'</span>'+((L.coverage>1)?'<span class="v3-chip">Carried by '+esc(L.coverage)+' outlets</span>':"")+'</div>';
 var bits=[];
 if(rg&&rg.available&&isFinite(rg.score))bits.push("Our market regime score reads "+rg.score+" out of 100 ("+esc(rg.label||rg.regime||"")+")");
 var rows=(mac&&mac.rows)||[],g=null,dx=null,ty=null;rows.forEach(function(r){if(r.key==="gold_usd")g=r;if(r.key==="dxy")dx=r;if(r.key==="tnx")ty=r});
 function cs(r){var c=String(r.change||""),m=/\(([^()]+)\)\s*$/.exec(c);return c?" ("+esc(m?m[1]:c)+" since the previous close)":""}
 if(g)bits.push(esc(g.name)+" is "+esc(g.value)+cs(g));
 if(dx)bits.push("the "+esc(dx.name)+" is "+esc(dx.value)+cs(dx));
 if(ty)bits.push("the "+esc(ty.name)+" is "+esc(ty.value));
 if(bits.length)h+='<p class="v3-p">'+bits.join("; ").replace(/^./,function(c){return c.toUpperCase()})+'. Sources and times are on each figure below.</p>';
 h+='<div class="v3-upd"><span class="v3-dot'+((Date.now()-upMs)>6*36e5?" st":"")+'"></span><span data-v3ago="'+upMs+'">'+esc(ago(upMs))+'</span></div>';
 var al=(e.also||[]).slice(0,3);if(al.length)h+='<div class="v3-k" style="margin:16px 0 8px">'+ICON.list+'<span>Also in today\'s brief</span></div><ol class="v3-tl">'+al.map(function(s){return '<li><div class="w">'+esc(noUK(s.publishedAtUk||""))+' \u00b7 '+esc(plain(s.source||""))+'</div><div class="x"><a href="'+esc(safeUrl(s.link))+'" rel="noopener nofollow" target="_blank" style="color:inherit">'+esc(plain(s.headline))+'</a></div></li>'}).join("")+'</ol>';
 h+='<p class="v3-src">Source: The Dispatch brief, lead-story rule (headlines from the outlets named). Edition '+esc(noUK(e.updatedAtUk||""))+(e.checkedAtUk?", checked "+esc(noUK(e.checkedAtUk)):"")+'. '+lag("Edition")+'</p>';
 el.innerHTML=h}
/* 2. Gauges */
function semi(score){var cx=110,cy=104,r=84;function pt(a,rr){var t=Math.PI*(1-a/100);return[cx+(rr||r)*Math.cos(t),cy-(rr||r)*Math.sin(t)]}function arc(a0,a1,col){var p0=pt(a0),p1=pt(a1);return '<path d="M'+p0[0].toFixed(1)+' '+p0[1].toFixed(1)+' A'+r+' '+r+' 0 0 1 '+p1[0].toFixed(1)+' '+p1[1].toFixed(1)+'" stroke="'+col+'" stroke-width="16" fill="none" stroke-linecap="butt"/>'}
 var s=Math.max(0,Math.min(100,Number(score))),n=pt(s,70);
 return '<svg class="v3-gauge" viewBox="0 0 220 120" role="img" aria-label="Regime score '+esc(s)+' out of 100">'+arc(0,44.5,"#e5534b")+arc(45.5,59.5,"#e2b04a")+arc(60.5,100,"#3fae7a")+'<line x1="110" y1="104" x2="'+n[0].toFixed(1)+'" y2="'+n[1].toFixed(1)+'" stroke="var(--v-ink)" stroke-width="4" stroke-linecap="round"/><circle cx="110" cy="104" r="8" fill="var(--v-ink)"/></svg>'}
function rangeBar(label,val,dp,unit,lo,hi,lowL,highL,src,neutral){var p=hi>lo?Math.max(0,Math.min(100,(val-lo)/(hi-lo)*100)):50;return '<div class="v3-bar"><div class="t"><span>'+esc(label)+'</span><b>'+esc(nf(val,dp)+(unit||""))+'</b></div><div class="v3-trk'+(neutral?" n":"")+'"><i style="left:'+p.toFixed(1)+'%"></i></div><div class="e"><span>'+esc(lowL)+'</span><span>'+esc(highL)+'</span></div><p class="v3-src" style="margin-top:2px">'+src+'</p></div>'}
function yrange(y){var c=closes(y);if(!c||c.pts.length<20)return null;var v=c.pts.map(function(p){return p.c}),m=c.meta,last=isFinite(m.regularMarketPrice)?m.regularMarketPrice:v[v.length-1];return{lo:Math.min.apply(null,v.concat([last])),hi:Math.max.apply(null,v.concat([last])),last:last,t:(m.regularMarketTime||0)*1000,first:c.pts[0].t,lastBar:c.pts[c.pts.length-1].t,pts:c.pts}}
function rGauges(){var el=$("v3-gauges");if(!el)return;var rg=S.rg,h=k("gauge","Market mood \u00b7 risk appetite",["/methodology","How it's built"]);
 if(rg&&rg.available&&isFinite(rg.score)){h+=semi(rg.score)+'<div class="v3-gnum">'+esc(rg.score)+'</div><div class="v3-glab">'+esc(rg.label||rg.regime||"")+'</div><div class="v3-gends"><span>Risk-off</span><span>Risk-on</span></div>';
  var inp=rg.inputs||{};h+='<p class="v3-src">Dispatch regime model (our calculation, '+esc(inp.used!=null?inp.used:"?")+' of '+esc(inp.of!=null?inp.of:"?")+' inputs: VIX, S&amp;P 500 move, dollar index, oil and Bitcoin, from Yahoo Finance and Coinbase Exchange) \u00b7 computed '+esc(noUK(rg.computedAtUk||rg.asOfUk||""))+' '+lag(rg.stale?"Stored":"Computed")+'</p>'}
 else h+=empty("Our regime score isn't available just now, because too few of its inputs answered. We don't show a score built from too few inputs.");
 var b="",yv=S.y["^VIX"],yg=S.y["GC=F"],yd=S.y["DX-Y.NYB"],yt=S.y["^TNX"];
 function src(r,extra){return 'Yahoo Finance, '+esc(extra)+' \u00b7 as of '+esc(uk(r.t))+' '+lag("Delayed")}
 var rv=yrange(yv);if(rv)b+=rangeBar("Fear gauge (VIX)",rv.last,2,"",Math.min(10,rv.lo),Math.max(40,rv.hi),"Calm (10)","Stressed ("+nf(Math.max(40,rv.hi),0)+")",src(rv,"Cboe VIX index, delayed"));
 var r1=yrange(yg);if(r1)b+=rangeBar("Gold futures in their 1-year range",r1.last,1,"",r1.lo,r1.hi,"Low $"+nf(r1.lo,0),"High $"+nf(r1.hi,0),src(r1,"COMEX front month, daily closes since "+ukDate(r1.first)),true);
 var r2=yrange(yd);if(r2)b+=rangeBar("Dollar index in its 1-year range",r2.last,2,"",r2.lo,r2.hi,"Low "+nf(r2.lo,2),"High "+nf(r2.hi,2),src(r2,"ICE index, daily closes since "+ukDate(r2.first)),true);
 var r3=yrange(yt);if(r3)b+=rangeBar("US 10-year yield in its 1-year range",r3.last,2,"%",r3.lo,r3.hi,"Low "+nf(r3.lo,2)+"%","High "+nf(r3.hi,2)+"%",src(r3,"market yield, daily closes since "+ukDate(r3.first)),true);
 h+=b?'<div class="v3-bars">'+b+'</div>':empty("The range bars need Yahoo Finance daily history, which didn't answer just now.");
 el.innerHTML=h}
/* 3. Key prices */
var KEYS=["gold_usd","gold_gbp","silver","dxy","tnx","ry","brent","gbpusd","spx","btc"];
function official(series){var m=/Official daily:\s*([^()]+?)\s*\(([^)]*)\)/.exec(String(series||""));return m?plain(m[1]+" \u00b7 "+m[2]):""}
function rPrices(){var el=$("v3-prices");if(!el)return;var mac=S.mac,h=k("coin","Key prices",["/markets/","All markets"]);
 var rows=(mac&&mac.available!==false&&mac.rows)||[];if(!rows.length){el.innerHTML=h+empty("Prices aren't available just now. Our free feeds didn't answer; we'll try again in two minutes.");return}
 var by={};rows.forEach(function(r){by[r.key]=r});var list=KEYS.filter(function(x){return by[x]}).map(function(x){return by[x]});rows.forEach(function(r){if(list.indexOf(r)<0&&list.length<10)list.push(r)});
 h+='<div class="v3-prices">'+list.map(function(r){var p=pctOf(r.change),a=asOfParts(r.asOf),o=official(r.series),src=plain(String(r.source||"").split(";")[0]);var chg=r.change?'<span class="c '+(p==null?(/^\+/.test(r.change)?"v3-up":/^[\u2212-]/.test(r.change)?"v3-down":"v3-flat"):cls(p))+'">'+esc(r.change)+'</span>':'<span class="c v3-flat">No change figure</span>';
  return '<div class="v3-pt"><div class="n">'+esc(plain(r.name))+'</div><div class="v">'+esc(r.value)+'</div>'+chg+(o?'<div class="o">Official daily: '+esc(o)+'</div>':"")+'<p class="v3-src">'+esc(src)+' \u00b7 '+esc(a.time||"time not given")+' '+lag(r.status||a.lag)+'</p></div>'}).join("")+'</div>';
 el.innerHTML=h}
/* 4. Gold chart (big) */
function rGold(){var el=$("v3-gold");if(!el)return;var c=S.gch,h=k("chart","Gold futures (COMEX, front month) \u00b7 last 3 months",["/gold/","Gold desk"]);
 var bars=(c&&c.status==="ok"&&c.bars)||[];if(bars.length<10){el.innerHTML=h+empty("The gold futures chart isn't available just now. We'll try again in two minutes.");return}
 function sd(d){var m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(d||"");return m?Number(m[3])+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m[2]-1]+" "+m[1]:d}
 var b=bars.slice(-63),v=b.map(function(x){return x.c}),last=b[b.length-1],first=b[0],ch=(last.c/first.c-1)*100,mn=Math.min.apply(null,v),mx=Math.max.apply(null,v);
 var yq=S.y["GC=F"],m=yq&&yq.chart&&yq.chart.result&&yq.chart.result[0]&&yq.chart.result[0].meta;
 h+='<div class="v3-bign"><b>$'+esc(nf(last.c,1))+'</b><span class="'+cls(ch)+'" style="font-weight:700">'+esc(sg(ch,2,"%"))+' over 3 months</span></div>';
 h+='<p class="v3-src" style="margin:0 0 8px">Last completed session close, '+esc(sd(last.sessionDate))+' (New York session). Futures, not the spot price.'+(m&&isFinite(m.regularMarketPrice)?' Latest delayed futures quote: $'+esc(nf(m.regularMarketPrice,1))+', as of '+esc(uk(m.regularMarketTime*1000))+'.':"")+'</p>';
 h+='<div style="position:relative">'+spark(v,640,290,true,"var(--v-gold)").replace('<svg ','<svg class="v3-big" ')+'</div>';
 h+='<div class="v3-gends" style="max-width:none"><span>'+esc(sd(first.sessionDate))+' \u00b7 low $'+esc(nf(mn,0))+'</span><span>high $'+esc(nf(mx,0))+' \u00b7 '+esc(sd(last.sessionDate))+'</span></div>';
 var note=c.cacheState&&c.cacheState!=="fresh"&&c.cacheNote?" "+plain(c.cacheNote):"";
 h+='<p class="v3-src">'+esc(plain(c.source||"Yahoo Finance, delayed"))+', daily closes of the continuous front-month series.'+esc(note)+' '+lag(c.cacheState==="stale"?"Stored reading":"Daily bars")+'</p>';
 el.innerHTML=h}
/* 5. Chart tiles */
var TILES=["GC=F","DX-Y.NYB","^TNX","BZ=F","BTC-USD","^GSPC"];
function rTiles(){var el=$("v3-tiles");if(!el)return;var h=k("chart","Chart tiles \u00b7 one month",["/terminal/","Terminal"]),t="";
 TILES.forEach(function(sym){var c=closes(S.y[sym]);if(!c||c.pts.length<10)return;var p=c.pts.slice(-22),v=p.map(function(x){return x.c}),m=c.meta,last=isFinite(m.regularMarketPrice)?m.regularMarketPrice:v[v.length-1],ch=(last/v[0]-1)*100;var dp=sym==="^TNX"?3:sym==="DX-Y.NYB"?2:sym==="BTC-USD"?0:1,pre=sym==="^TNX"||sym==="DX-Y.NYB"||sym==="^GSPC"?"":"$",suf=sym==="^TNX"?"%":"";
  t+='<div class="v3-tile"><span class="n">'+esc(NAMES[sym])+'</span><span class="v">'+esc(pre+nf(last,dp)+suf)+'</span><span class="'+cls(ch)+'" style="font-size:12px;font-weight:700">'+esc(sg(ch,2,"%"))+' in a month</span>'+spark(v,160,46,true)+'<p class="v3-src" style="margin:0">Yahoo Finance \u00b7 '+esc(uk(m.regularMarketTime*1000))+' '+lag("Delayed")+'</p></div>'});
 el.innerHTML=h+(t?'<div class="v3-tiles">'+t+'</div><p class="v3-src">Lines are daily closes from Yahoo Finance over about one month; the big number is the latest delayed quote. The gold and Brent tiles are futures contract prices (front month).</p>':empty("The chart tiles need Yahoo Finance daily history, which didn't answer just now."))}
/* 6. Five-bullet summary */
function rMoves(){var el=$("v3-moves");if(!el)return;var h=k("list","Five things that moved",["/what-changed/","What changed today"]),rows=((S.mac&&S.mac.rows)||[]).filter(function(r){return r.change&&pctOf(r.change)!=null||/pt$/.test(String(r.change||""))});
 rows=rows.map(function(r){var p=pctOf(r.change);if(p==null){var m=/([+\u2212\-]?\d+(?:\.\d+)?)\s*pt/.exec(r.change);var lv=parseFloat(String(r.value).replace(/[^0-9.\-]/g,""));p=m&&lv?Number(m[1].replace("\u2212","-"))/lv*100:0}return{r:r,p:p}}).sort(function(a,b){return Math.abs(b.p)-Math.abs(a.p)});
 var top=rows.slice(0,5);if(!top.length&&!(S.today&&S.today.items&&S.today.items.length)){el.innerHTML=h+empty("No moves to show yet: the price feeds didn't answer. We'll try again in two minutes.");return}
 var heat=top.map(function(x){var p=x.p;var col=p==null?"var(--v-chip)":p>0?"color-mix(in srgb,var(--v-up) "+Math.min(55,12+Math.abs(p)*30).toFixed(0)+"%,transparent)":p<0?"color-mix(in srgb,var(--v-down) "+Math.min(55,12+Math.abs(p)*30).toFixed(0)+"%,transparent)":"var(--v-chip)";return '<div style="background:'+col+'"><small>'+esc(plain(x.r.name).replace(/ \(context\)$/,""))+'</small>'+esc(x.r.change.replace(/^.*\(([^)]+)\)$/,"$1"))+'</div>'}).join("");
 h+='<div class="v3-heat">'+heat+'</div><ul class="v3-ul">';
 var n=0;top.forEach(function(x){var r=x.r,a=asOfParts(r.asOf);n++;h+='<li><i class="'+cls(x.p)+'"></i><div><b>'+esc(plain(r.name))+'</b> '+esc(r.value)+', '+esc(r.change)+'. <span class="v3-src" style="display:inline">'+esc(plain(String(r.source||"").split(";")[0]))+' \u00b7 '+esc(a.time)+'</span> '+lag(r.status||a.lag)+'</div></li>'});
 ((S.today&&S.today.items)||[]).forEach(function(it){if(n>=5)return;n++;var a=asOfParts(it.time);h+='<li><i></i><div><b>'+esc(plain(it.title))+'</b>. '+esc(plain(it.detail||""))+' <span class="v3-src" style="display:inline">'+esc(plain(it.source||""))+' \u00b7 '+esc(a.time)+'</span> '+lag(a.lag)+'</div></li>'});
 h+='</ul><p class="v3-src">Ranked by the size of each move since its previous close. Facts only, not advice.</p>';el.innerHTML=h}
/* 7. Upcoming events */
function rCal(){var el=$("v3-cal");if(!el)return;var c=S.cal,h=k("cal","Upcoming events",["/calendar/","Full calendar"]);var now=Date.now();
 var rows=((c&&c.available!==false&&c.rows)||[]).filter(function(r){return !r.past&&isFinite(r.ms)&&r.ms>now-36e5}).sort(function(a,b){return a.ms-b.ms});
 if(!rows.length){el.innerHTML=h+empty("No upcoming releases are listed just now. The official calendars didn't answer, or nothing is scheduled in the window we check.");return}
 var f=rows[0],d=Math.max(0,f.ms-now),dd=Math.floor(d/864e5),hh=Math.floor(d%864e5/36e5),mm=Math.floor(d%36e5/6e4);
 h+='<div style="font:600 18px/1.3 Source Serif 4,Georgia,serif">'+esc(plain(f.name||f.title))+'</div><div class="v3-src" style="margin:2px 0 0">'+esc(noUK(f.when))+' \u00b7 '+esc(plain(f.source||f.agency||""))+(f.previous?' \u00b7 previous: '+esc(plain(f.previous)):"")+'</div>';
 h+='<div class="v3-cd" aria-label="Countdown"><div><b>'+dd+'</b><small>days</small></div><div><b>'+hh+'</b><small>hrs</small></div><div><b>'+mm+'</b><small>min</small></div></div><ol class="v3-tl">';
 var ag={};rows.slice(0,5).forEach(function(r){ag[plain(r.source||r.agency||"")]=1});
 rows.slice(1,5).forEach(function(r){h+='<li><div class="w">'+esc(noUK(r.when))+'</div><div class="x">'+esc(plain(r.name||r.title))+'</div>'+(r.previous?'<div class="y">Previous: '+esc(plain(r.previous))+'</div>':"")+'</li>'});
 h+='</ol><p class="v3-src">Official release calendars ('+esc(Object.keys(ag).filter(Boolean).join(", "))+') \u00b7 checked '+esc(noUK(c.fetchedUk||""))+' '+lag("Schedule")+'</p>';el.innerHTML=h}
/* 8. Also in today's brief */
function rAlso(){var el=$("v3-also");if(!el)return;var e=S.ed,h=k("doc","Also in today's brief",["/brief/","Read the brief"]);var a=(e&&e.also)||[];
 if(!a.length){el.innerHTML=h+empty("No other ranked stories in this edition yet.");return}
 h+='<ol class="v3-tl">'+a.slice(0,4).map(function(s){return '<li><div class="w">'+esc(noUK(s.publishedAtUk||""))+' \u00b7 '+esc(plain(s.source||""))+'</div><div class="x"><a href="'+esc(safeUrl(s.link))+'" rel="noopener nofollow" target="_blank" style="color:inherit">'+esc(plain(s.headline))+'</a></div></li>'}).join("")+'</ol><p class="v3-src">The Dispatch brief, other ranked stories \u00b7 '+esc(noUK(e.updatedAtUk||""))+' '+lag("Edition")+'</p>';el.innerHTML=h}
function safe(f){try{f()}catch(e){}}
function renderAll(){[rSnap,rGauges,rPrices,rGold,rTiles,rMoves,rCal].forEach(safe)}
function ych(sym,range){return get("/api/yahoo-chart?symbol="+encodeURIComponent(sym)+"&range="+range+"&interval=1d")}
function load(){S.y=S.y||{};var ys=["GC=F","DX-Y.NYB","^TNX","BZ=F","BTC-USD","^GSPC","^VIX"];
 return Promise.all([get("/api/brief/edition"),get("/api/c100/macro"),get("/api/regime"),get("/api/c97/calendar"),get("/api/c97/today"),get("/api/c102/chart?range=3m")].concat(ys.map(function(s){return ych(s,"1y")}))).then(function(r){
  if(r[0])S.ed=r[0];if(r[1])S.mac=r[1];if(r[2])S.rg=r[2];if(r[3])S.cal=r[3];if(r[4])S.today=r[4];if(r[5])S.gch=r[5];
  ys.forEach(function(s,i){if(r[6+i])S.y[s]=r[6+i]});renderAll();root.setAttribute("data-v3-ready","1")})}
/* Market tape (preview only): plain-English labels. The tape outside the preview is untouched. */
(function(){var FR={"STALE":"stale","CACHED":"cached","LAST CLOSE":"last close","LIVE":"live","DELAYED":"delayed","REFERENCE":"reference price","NO LIVE SYNC":"not updating"};
 function src(s){s=String(s||"");if(/gold-api/i.test(s))return"gold-api.com";if(/basket|dxy-fx/i.test(s))return"our FX basket (Yahoo Finance FX rates)";if(/SOURCE UNAVAILABLE/.test(s))return"source not given";return plain(s).replace(/^Yahoo Finance, ICE US Dollar Index$/,"Yahoo Finance (ICE)")}
 function stamp(s){s=String(s||"");if(/TIME UNAVAILABLE/.test(s)||!s)return"time not given";var m=/(\d{1,2}:\d{2})\s*UK/.exec(s);var d=/(\d{1,2} \w{3}|\w{3} \d{1,2} \w{3})/.exec(s);return"updated "+(d?d[1].replace(/^\w{3} /,"")+", ":"")+(m?m[1]+" UK":noUK(s))}
 function fix(){var t=D.querySelector(".public-market-tape");if(!t)return;
  var lab=t.querySelector(".public-market-tape-label");if(lab&&!lab.getAttribute("data-v3p")){lab.setAttribute("data-v3p","1");lab.innerHTML="Market tape <span>reference prices</span>"}
  var its=t.querySelectorAll(".public-market-tape-item");for(var i=0;i<its.length;i++){var it=its[i];if(it.getAttribute("data-v3p"))continue;var st=it.querySelector("strong"),sm=it.querySelector("small"),em=it.querySelector(".public-market-tape-empty");var name=st?st.textContent:"";
   var base=name==="GOLD"?"Gold spot price":name==="DOLLAR"?"US dollar index":name.charAt(0)+name.slice(1).toLowerCase();
   if(sm){var p=sm.textContent.split(" \u00b7 ");var fr=FR[p[0]]||String(p[0]||"").toLowerCase(),so=src(p[1]);if(name==="DOLLAR"&&/basket/.test(so))base="Dollar, our FX basket";sm.textContent=so+" \u00b7 "+fr+", "+stamp(p.slice(2).join(" \u00b7 "))}
   if(st)st.textContent=base;if(em)em.textContent="Not updating right now";it.setAttribute("data-v3p","1")}
  var e2=t.querySelectorAll(".public-market-tape-track>.public-market-tape-empty");for(var j=0;j<e2.length;j++)if(/NO LIVE SYNC|awaiting/.test(e2[j].textContent))e2[j].textContent="Waiting for prices"}
 fix();var tr=D.querySelector(".public-market-tape");if(tr&&window.MutationObserver)new MutationObserver(function(){fix()}).observe(tr,{childList:true,subtree:true});})();
load();setInterval(load,120000);
setInterval(function(){var n=D.querySelectorAll("[data-v3ago]");for(var i=0;i<n.length;i++)n[i].textContent=ago(Number(n[i].getAttribute("data-v3ago")))},30000);
})();
