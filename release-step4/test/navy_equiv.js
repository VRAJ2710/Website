// TEST ONLY: proves a release page is exactly chat110navy.transform(step-3 page) (or byte-identical when the block leaves it alone).
// usage: node navy_equiv.js <block.js> <rel.html> <old.html>   -> prints SAME | TRANSFORMED | DIFF
const fs=require("fs"),http=require("http");
const SP=http.Server.prototype, e0=SP.emit; const f=function(){return e0.apply(this,arguments)}; f.__chat109v3default=1; SP.emit=f;
const log=console.log; console.log=()=>{}; eval(fs.readFileSync(process.argv[2],"utf8")); console.log=log;
const rel=fs.readFileSync(process.argv[3],"utf8"), old=fs.readFileSync(process.argv[4],"utf8");
if(rel===old){log("SAME");process.exit(0)}
const t=globalThis.__c110navy.transform(old, process.argv[5] || "/");
// late inserts from blocks that patch ServerResponse (r6p styles before </head>, credits before </body>) land after ours,
// so the two order-dependent inserts (site link, bottom bar) are compared position-free: each must occur exactly once.
const L='<link rel="stylesheet" href="/__navy/site.css?v=chat110navy">', B=/<nav class="nv-bbar"[\s\S]*?<\/nav>/;
function norm(x){return x.split(L).join("").replace(B,"")}
function once(x){return x.split(L).length===2&&(x.match(/<nav class="nv-bbar"/g)||[]).length===1}
if(t!=null&&(t===rel||(once(rel)&&once(t)&&norm(t)===norm(rel)&&(t.match(B)||[""])[0]===(rel.match(B)||[""])[0]))){log("TRANSFORMED");process.exit(0)}
log("DIFF");process.exit(1);
