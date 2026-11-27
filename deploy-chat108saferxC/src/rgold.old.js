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
