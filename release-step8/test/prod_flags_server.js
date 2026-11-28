// Tiny HTTPS server: production cookie flags, bug vs fix subscribe construction. Test only.
const https = require("https"), fs = require("fs");
const key = process.env.CK_KEY, cert = process.env.CK_CERT, port = Number(process.env.CK_PORT || 18444);
const flags = (clear, domain) => ["Path=/", "HttpOnly", "SameSite=Lax", clear ? "Max-Age=0" : "Max-Age=2592000", "Secure", ...(domain ? ["Domain=thedispatch.uk"] : [])];
function sessionCookieHeader(token) {
  const established = [`dispatch_session=${token}`, ...flags(false, true)].join("; ");
  return [["dispatch_session=", ...flags(true, false)].join("; "), ["dispatch_session=", ...flags(true, true)].join("; "), established];
}
const tok = "ab".repeat(32);
https.createServer({ key: fs.readFileSync(key), cert: fs.readFileSync(cert) }, (req, res) => {
  if (req.url === "/register" || req.url === "/login") {
    res.setHeader("Set-Cookie", sessionCookieHeader(tok));
    res.writeHead(302, { Location: "/me" }); return res.end();
  }
  if (req.url === "/subscribe-bug") {
    res.setHeader("Set-Cookie", sessionCookieHeader(tok));
    const sessionCookie = res.getHeader("Set-Cookie");
    res.setHeader("Set-Cookie", [sessionCookie, "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120"].filter(Boolean));
    res.writeHead(302, { Location: "/me" }); return res.end();
  }
  if (req.url === "/subscribe-fix") {
    res.setHeader("Set-Cookie", sessionCookieHeader(tok));
    const sessionCookie = res.getHeader("Set-Cookie");
    res.setHeader("Set-Cookie", [].concat(sessionCookie || [], "dispatch_account_created=1; Path=/; SameSite=Lax; Max-Age=120").filter(Boolean));
    res.writeHead(302, { Location: "/me" }); return res.end();
  }
  if (req.url === "/me") { res.writeHead(200, { "content-type": "text/plain" }); return res.end("cookie: " + (req.headers.cookie || "")); }
  res.writeHead(404); res.end();
}).listen(port, "127.0.0.1", () => console.log("https " + port));
