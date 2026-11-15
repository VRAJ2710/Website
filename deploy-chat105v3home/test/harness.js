// Local harness: serves the captured live "/" HTML like the app does, proxies /api/* to the live site,
// then loads the chat105v3home block exactly as server.js would (after the server exists).
const http=require('http'),https=require('https'),fs=require('fs'),path=require('path'),zlib=require('zlib');
const HOME=fs.readFileSync(process.env.HOME_HTML||path.join(__dirname,'../raw/live.html'));
const MODE=process.env.MODE||'send';
const cache={};
const srv=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://x');
  if(u.pathname==='/'){
    const theme=(req.headers.cookie||'').match(/th=(\w+)/);let body=HOME.toString();
    if(theme)body=body.replace('class="c97-system"','class="c97-'+theme[1]+'"');
    if(MODE==='chunked'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':Buffer.byteLength(body)});const b=Buffer.from(body);res.write(b.slice(0,5000));res.write(b.slice(5000,40000));res.end(b.slice(40000));return}
    if(MODE==='gzip'&&/gzip/.test(req.headers['accept-encoding']||'')){const z=zlib.gzipSync(body);res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Encoding':'gzip','Content-Length':z.length});return res.end(z)}
    res.setHeader('Content-Type','text/html; charset=utf-8');res.setHeader('Cache-Control','private, max-age=60');res.setHeader('ETag','"abc"');res.setHeader('Content-Length',Buffer.byteLength(body));return res.end(body)}
  if(u.pathname.startsWith('/api/')){
    const k=req.url;
    if(cache[k])return send(cache[k]);
    https.get('https://thedispatch.uk'+req.url,{headers:{'accept':'application/json'}},r=>{const b=[];r.on('data',d=>b.push(d));r.on('end',()=>{const o={s:r.statusCode,b:Buffer.concat(b)};if(o.s===200)cache[k]=o;send(o)})}).on('error',()=>send({s:502,b:Buffer.from('{}')}));
    function send(o){res.writeHead(o.s,{'Content-Type':'application/json'});res.end(o.b)}
    return}
  res.statusCode=404;res.end('nf');
});
srv.listen(+process.env.PORT||8787,()=>{
  if(process.env.BLOCK!=='0'){require(process.env.BLOCK_FILE||path.join(__dirname,'../build/server_block_chat105v3home.js'))}
  console.log('harness up',MODE);
});
