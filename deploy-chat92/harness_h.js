const { PassThrough } = require("stream");
delete process.env.DATABASE_URL;
const S = require("./server.js");
function call(fn, method, url, headers) {
  return new Promise((resolve) => {
    const req = new PassThrough(); req.method = method; req.url = url; req.headers = Object.assign({ host: "thedispatch.uk", "x-forwarded-proto": "https" }, headers || {}); req.socket = { remoteAddress: "127.0.0.1" }; req.connection = req.socket; req.end();
    const res = new PassThrough(); let status = 200, hdrs = {}; const chunks = [];
    res.statusCode = 200; res.headersSent = false;
    res.setHeader = (k, v) => { hdrs[k.toLowerCase()] = v; }; res.getHeader = k => hdrs[k.toLowerCase()]; res.removeHeader = k => { delete hdrs[k.toLowerCase()]; }; res.getHeaders = () => hdrs; res.hasHeader = k => k.toLowerCase() in hdrs;
    res.writeHead = (s, a, b) => { status = s; res.statusCode = s; const h = typeof a === "object" ? a : b; if (h) for (const k in h) hdrs[k.toLowerCase()] = h[k]; res.headersSent = true; return res; };
    res.write = (c) => { if (c) chunks.push(Buffer.from(c)); return true; };
    res.end = (c) => { if (c) chunks.push(Buffer.from(c)); resolve({ status: res.statusCode || status, headers: hdrs, body: Buffer.concat(chunks).toString("utf8") }); };
    Promise.resolve(fn()(req, res)).catch(e => resolve({ status: "THROW", body: String(e.stack) }));
  });
}
module.exports = { S, call };
if (require.main === module) (async () => {
  const r = await call(S.__h.inner, "GET", "/");
  console.log(r.status, r.body.length);
  const rx = /dispatch\W+markets/ig; let m;
  while ((m = rx.exec(r.body))) console.log("MATCH", JSON.stringify(r.body.slice(m.index - 120, m.index + 60)));
  process.exit(0);
})();
