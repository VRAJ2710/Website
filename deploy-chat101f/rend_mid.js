var LV=a[8]&&a[8].available?a[8]:{},T10=LV.ten,TIP=LV.tips,tg=a[6];
function d8s(s){return d8(s).replace(/ \d{4}$/,"")}
function offT(v,src,date){return"Official daily: "+v+" ("+src+", "+d8s(date)+")"}
function nyP(){try{var o={};new Intl.DateTimeFormat("en-US",{timeZone:"America/New_York",weekday:"short",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date()).forEach(function(x){o[x.type]=x.value});return{d:o.weekday||"",m:Number(o.hour||0)%24*60+Number(o.minute||0)}}catch(e){return null}}
function sesT(kind){var t=nyP();if(!t)return"";var d=t.d,m=t.m,wk=d==="Sat"||(d==="Sun"&&m<1080)||(d==="Fri"&&m>=1020);
if(kind==="ust")return wk?"US Treasury market: closed for the weekend, showing the last quote":"US Treasury market: trading (almost 24 hours on weekdays), quote delayed";
if(kind==="cboe")return!(d==="Sat"||d==="Sun")&&m>=570&&m<960?"Cboe yield index: US session open, quote delayed":"Cboe yield index: US session closed, showing the last close";
if(kind==="nymex")return wk?"NYMEX crude futures: closed for the weekend, showing the last trade":m>=1020&&m<1080?"NYMEX crude futures: daily one-hour break, showing the last trade":"NYMEX crude futures: trading, quote delayed";
return""}
function nxt(){var x=Date.now(),i=0,s;do{x+=DAY;i++;s=new Date(x).toLocaleDateString("en-GB",{timeZone:"Europe/London",weekday:"short",day:"numeric",month:"short"})}while(/^(Sat|Sun)/.test(s)&&i<5);return s}
var ryOk=ry&&ry.available&&isFinite(Number(ry.value)),tgOk=tg&&tg.available&&isFinite(Number(tg.value));
// 10-year: the market quote first (Tradeweb via CNBC, trades almost 24 hours on weekdays), then the Cboe index, then the official daily figure
var tOff=tgOk?offT(n(tg.value,2)+"%","US Treasury via FRED",tg.date):"";
if(T10&&isFinite(Number(T10.value)))rows.tnx=["US 10-year Treasury yield (market quote, delayed)",n(T10.value,2)+"%",T10.change!=null?sg(T10.change,2," pt"):"",cut(["Delayed",T10.src||"CNBC market quote",T10.asOfUk,"change vs previous close"]),T10.change,0,tOff,sesT("ust")];
else if(rows.tnx){rows.tnx[3]=rows.tnx[3]+" \u00b7 change vs previous close";rows.tnx[6]=tOff;rows.tnx[7]=sesT("cboe")}
else if(tgOk)rows.tnx=["US 10-year Treasury yield, official daily figure",n(tg.value,2)+"%",tg.change!=null?sg(tg.change,2," pt"):"","Live quote unavailable, so this is the official daily figure \u00b7 US Treasury via FRED \u00b7 "+d8(tg.date),tg.change,0,"",""];
// Real yield: the 10-year inflation-protected (TIPS) market quote when CNBC has one; the official FRED figure lags 1 to 2 days
var rOff=ryOk?offT(n(ry.value,2)+"%","US Treasury via FRED",ry.date)+"; published with a 1\u20132 day lag":"";
if(TIP&&isFinite(Number(TIP.value)))rows.ry=["US 10-year real yield (TIPS market quote, delayed)",n(TIP.value,2)+"%",TIP.change!=null?sg(TIP.change,2," pt"):"",cut(["Delayed",TIP.src||"CNBC market quote",TIP.asOfUk,"change vs previous close"]),TIP.change,0,rOff,sesT("ust")];
else if(ryOk)rows.ry=["US 10-year real yield (official daily figure)",n(ry.value,2)+"%",ry.change!=null?sg(ry.change,2," pt"):"","Official daily figure, published with a 1\u20132 day lag \u00b7 US Treasury via FRED \u00b7 "+d8(ry.date)+" \u00b7 next update "+nxt(),ry.change,0,"",""];
// WTI: NYMEX front-month futures first (trade almost 24 hours on weekdays); the EIA official spot underneath, or instead if the futures quote is missing
var w=eia&&eia.available&&eia.WTI,wOk=w&&Number(w.p)>0;
if(rows.wtif){rows.wtif[3]=rows.wtif[3]+" \u00b7 change vs previous close";rows.wtif[6]=wOk?offT("$"+n(w.p,2),"US EIA spot",w.date):"";rows.wtif[7]=sesT("nymex");rows.wti=rows.wtif}
else if(wOk)rows.wti=["WTI crude, official daily spot (live quote unavailable)","$"+n(w.p,2),Number(w.prev)>0?sg((w.p/w.prev-1)*100,2,"%"):"","Live quote unavailable, so this is the official daily figure \u00b7 US EIA daily print \u00b7 "+d8(w.date),Number(w.prev)>0?(w.p/w.prev-1)*100:null,0,"",""];
