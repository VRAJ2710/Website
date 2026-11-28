// TEST ONLY (--require): logs every outbound TCP connection (net.Socket.prototype.connect, used by http/https/tls/fetch-undici)
// and every fetch() URL to $NETLOG. Creates the file at start so "empty" means "nothing contacted".
const fs = require("fs"), net = require("net"), F = process.env.NETLOG;
try { fs.writeFileSync(F, ""); } catch (e) {}
function log(h, p) { try { fs.appendFileSync(F, String(h) + ":" + String(p) + "\n"); } catch (e) {} }
const sc = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...args) {
  try { let o = args[0]; if (Array.isArray(o)) o = o[0]; if (typeof o !== "object") o = { port: args[0], host: typeof args[1] === "string" ? args[1] : "localhost" };
    log(o.path ? "unix" : (o.host || "localhost"), o.path || o.port); } catch (e) {}
  return sc.apply(this, args);
};
if (globalThis.fetch) { const f0 = globalThis.fetch; globalThis.fetch = function (u) { try { const x = new URL(String(u && u.url || u)); log("fetch " + x.hostname, x.port || x.protocol); } catch (e) {} return f0.apply(this, arguments); }; }
