// TEST ONLY (box): stands in for the real r6n server's static + index.html handling after step 4.
// Serves /app.js, /styles.css, /c93.css from STATIC_DIR, and applies index_edits.json to SPA-shell HTML coming from UPSTREAM
// (the live SPA shell is index.html rendered by the r6n server; the edits are literal and each anchor occurs once there).
const http=require("http"),fs=require("fs"),path=require("path");
const UP=+process.env.UPSTREAM_PORT, DIR=process.env.STATIC_DIR, EDITS=process.env.EDITS?JSON.parse(fs.readFileSync(process.env.EDITS,"utf8")):null;
http.createServer((req,res)=>{
  const p=req.url.split("?")[0];
  if(/^\/(app\.js|styles\.css|c93\.css)$/.test(p)){const b=fs.readFileSync(path.join(DIR,p.slice(1)));res.writeHead(200,{"content-type":p.endsWith(".js")?"application/javascript":"text/css","cache-control":"no-store"});return res.end(b);}
  const r2=http.request({host:"127.0.0.1",port:UP,path:req.url,method:req.method,headers:req.headers},r=>{
    const bufs=[];r.on("data",d=>bufs.push(d));r.on("end",()=>{let b=Buffer.concat(bufs);const h=Object.assign({},r.headers);
      if(EDITS&&/text\/html/.test(h["content-type"]||"")){let t=b.toString("utf8");if(t.indexOf("/app.js?v=chat102r6n")>=0){let ok=true;for(const [o,n] of EDITS){if(t.split(o).length!==2){ok=false;break}t=t.replace(o,()=>n)}if(ok){b=Buffer.from(t);h["x-test-index-edits"]="applied"}else h["x-test-index-edits"]="ANCHOR-MISS"}}
      delete h["content-length"];delete h["transfer-encoding"];res.writeHead(r.statusCode,h);res.end(b)})});
  r2.on("error",e=>{res.statusCode=502;res.end(String(e))});req.pipe(r2);
}).listen(+process.env.PORT,()=>console.log("navyfront on "+process.env.PORT));
