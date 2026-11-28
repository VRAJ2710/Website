// DEV-SHAPED read-only caching proxy: like cacheproxy.js, but drops Replit's published-hosting analytics tag from HTML (Replit adds it
// after the server responds, so the dev server never sends it). Pages then end </nav></body></html> exactly as on dev.
// read-only caching proxy to the LIVE site for deterministic comparisons (GET only; first answer per URL is reused)
const http=require("http"),https=require("https"),fs=require("fs"),path=require("path"),crypto=require("crypto");
const DIR=process.env.CACHE_DIR||"/tmp/r1cache";fs.mkdirSync(DIR,{recursive:true});
http.createServer((req,res)=>{if(req.method!=="GET"){res.statusCode=405;return res.end("GET only")}
 const k=path.join(DIR,crypto.createHash("md5").update(req.url).digest("hex"));
 if(fs.existsSync(k)){const c=JSON.parse(fs.readFileSync(k+".h"));res.writeHead(c.s,c.h);return res.end(fs.readFileSync(k))}
 https.get({host:"thedispatch.uk",path:req.url,headers:{"user-agent":"Mozilla/5.0 qa-step1","accept-encoding":"identity",cookie:req.headers.cookie||""}},r=>{const b=[];r.on("data",d=>b.push(d));r.on("end",()=>{let body=Buffer.concat(b);if(/text\/html/i.test(r.headers["content-type"]||""))body=Buffer.from(body.toString("utf8").replace(/<script src="https:\/\/i\.replit\.com\/script\.js"[^>]*><\/script>(?=<\/body>)/,""),"utf8");const h={"content-type":r.headers["content-type"]||"application/octet-stream"};if(r.headers.location)h.location=r.headers.location;fs.writeFileSync(k,body);fs.writeFileSync(k+".h",JSON.stringify({s:r.statusCode,h}));res.writeHead(r.statusCode,h);res.end(body)})}).on("error",e=>{res.statusCode=502;res.end(String(e))})
}).listen(+process.env.PORT||8870,()=>console.log("cacheproxy on "+(process.env.PORT||8870)));
