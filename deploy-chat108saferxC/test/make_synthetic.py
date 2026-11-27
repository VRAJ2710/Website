# Builds a synthetic post-credits server.js for LOCAL tests only: a tiny runnable server (serves a captured dev "/" page,
# proxies other GETs read-only to the Replit dev preview) + the real chain tail: chat105v3home2, c102r6p scrub, chat107credits.
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); dep = "/workspace/c108/deploy-chat108saferxA"  # chain files (v3home2, credits) live with A
raw = sys.argv[1]; out = sys.argv[2]
r6p = "/workspace/c107/deploy-chat107credits/server_block_c102r6p.js"
prefix = r'''// SYNTHETIC TEST SERVER (box only). Markers for guards: [chat106softgate] attached
const VERIFY_ENFORCE = false;
const fs = require("fs"), http = require("http"), https = require("https");
const RAW = fs.readFileSync(process.env.RAW_HTML);
const DEV = "41c83e31-7da9-45c5-a194-58f8bc4f6608-00-3prevco89pef3.archer.replit.dev";
const cache = new Map();
setImmediate(function () {
  http.createServer(function (req, res) {
    const path = req.url.split("?")[0];
    if (path === "/" && req.method === "GET") { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); return res.end(RAW); }
    if (req.method !== "GET" && req.method !== "HEAD") { res.statusCode = 405; return res.end("read-only test server"); }
    if (process.env.OFFLINE) { res.statusCode = 404; return res.end("offline"); }
    if (cache.has(req.url)) { const c = cache.get(req.url); res.writeHead(c.s, c.h); return res.end(c.b); }
    const up = process.env.UPSTREAM_HTTP ? process.env.UPSTREAM_HTTP.split(":") : null;
    (up ? http : https).get({ host: up ? up[0] : DEV, port: up ? +up[1] : 443, path: req.url, headers: { "user-agent": "qa-synthetic", "accept-encoding": "identity", cookie: "dispatch_theme=system" } }, function (r) {
      const bufs = []; r.on("data", function (d) { bufs.push(d); }); r.on("end", function () {
        const b = Buffer.concat(bufs), h = { "content-type": r.headers["content-type"] || "application/octet-stream" };
        if (r.statusCode === 200) cache.set(req.url, { s: 200, h: h, b: b }); res.writeHead(r.statusCode, h); res.end(b); });
    }).on("error", function (e) { res.statusCode = 502; res.end(String(e)); });
  }).listen(+process.env.PORT || 8820, function () { console.log("synthetic server on " + (process.env.PORT || 8820)); });
});
'''
v = open(dep + "/server_block_chat105v3home2.js", "rb").read().rstrip(b"\n") + b"\n"
d = prefix.encode() + v + open(r6p, "rb").read()
c = open(dep + "/server_block_chat107credits.js", "rb").read()
d = d + (b"" if d.endswith(b"\n") else b"\n") + c
open(out, "wb").write(d)
print(len(d))
