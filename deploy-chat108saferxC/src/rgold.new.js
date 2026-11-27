/* 4. Gold chart (big). chat108saferxC: the latest free delayed futures quote is the main figure (lag label, UK time); the last
   completed close is on a secondary line. The 3-month change is measured from the first close in the window to the main figure;
   both come from the same continuous front-month series. With no fresh quote, the close is the main figure, labelled so. */
function rGold(){var el=$("v3-gold");if(!el)return;var c=S.gch,h=k("chart","Gold futures (COMEX, front month) \u00b7 last 3 months",["/gold/","Gold desk"]);
 var bars=(c&&c.status==="ok"&&c.bars)||[];if(bars.length<10){el.innerHTML=h+empty("The gold futures chart isn't available just now. We'll try again in two minutes.");return}
 function sd(d){var m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(d||"");return m?Number(m[3])+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m[2]-1]+" "+m[1]:d}
 var b=bars.slice(-63),v=b.map(function(x){return x.c}),last=b[b.length-1],first=b[0],mn=Math.min.apply(null,v),mx=Math.max.apply(null,v);
 var yq=S.y["GC=F"],m=yq&&yq.chart&&yq.chart.result&&yq.chart.result[0]&&yq.chart.result[0].meta;
 var qp=m&&isFinite(m.regularMarketPrice)&&m.regularMarketPrice>0?Number(m.regularMarketPrice):null,qt=m&&isFinite(m.regularMarketTime)?m.regularMarketTime*1000:NaN;
 var lastT=Date.parse(last.timeUtc||"")||Date.parse((last.sessionDate||"")+"T05:00:00Z");
 var fresh=qp!=null&&isFinite(qt)&&qt>lastT+18*36e5&&(isTodayUK(qt)||Date.now()-qt<12*36e5);
 var chC=(last.c/first.c-1)*100;
 if(fresh){var chQ=(qp/first.c-1)*100;
  h+='<div class="v3-bign"><b>$'+esc(nf(qp,1))+'</b><span class="'+cls(chQ)+'" style="font-weight:700">'+esc(sg(chQ,2,"%"))+' over 3 months</span></div>';
  h+='<p class="v3-src v10-main">Latest delayed futures quote, as of '+esc(uk(qt))+'. Futures, not the spot price. The 3-month change runs from the '+esc(sd(first.sessionDate))+' close to this quote, on the same continuous front-month series. '+lag("Delayed")+'</p>';
  h+='<div class="v10-sec"><span>Last completed close</span><b>$'+esc(nf(last.c,1))+'</b><span>'+esc(sd(last.sessionDate))+' (New York session)</span><span class="'+cls(chC)+'">'+esc(sg(chC,2,"%"))+' close to close over 3 months</span>'+lag("Daily close")+'</div>'}
 else{
  h+='<div class="v3-bign"><b>$'+esc(nf(last.c,1))+'</b><span class="'+cls(chC)+'" style="font-weight:700">'+esc(sg(chC,2,"%"))+' over 3 months, close to close</span></div>';
  h+='<p class="v3-src v10-main">Last completed session close, '+esc(sd(last.sessionDate))+' (New York session). Futures, not the spot price. No fresh delayed quote is available just now'+(qp!=null&&isFinite(qt)?' (the newest one we have is $'+esc(nf(qp,1))+', as of '+esc(uk(qt))+')':"")+'. '+lag("Last close")+'</p>'}
 h+='<div style="position:relative">'+spark(v,640,290,true,"var(--v-gold)").replace('<svg ','<svg class="v3-big" ')+'</div>';
 h+='<div class="v3-gends" style="max-width:none"><span>'+esc(sd(first.sessionDate))+' \u00b7 low $'+esc(nf(mn,0))+'</span><span>high $'+esc(nf(mx,0))+' \u00b7 '+esc(sd(last.sessionDate))+'</span></div>';
 var note=c.cacheState&&c.cacheState!=="fresh"&&c.cacheNote?" "+plain(c.cacheNote):"";
 h+='<p class="v3-src">'+esc(plain(c.source||"Yahoo Finance, delayed"))+', daily closes of the continuous front-month series'+(fresh?'; main figure: Yahoo Finance delayed quote for the same series':"")+'.'+esc(note)+' '+lag(c.cacheState==="stale"?"Stored reading":"Daily bars")+'</p>';
 el.innerHTML=h}

