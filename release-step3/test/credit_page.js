// node credit_page.js <block.js> <in.html> <url> <out.html> : run the credits block's credit() on a saved page (as the server would).
const fs = require("fs"), vm = require("vm");
const [block, inp, url, out] = process.argv.slice(2);
const ctx = { console: { log() {} }, setTimeout, clearTimeout, setInterval: () => ({ unref() {} }), Buffer, Intl, Promise, Date, JSON, Math, Object, String, Array, RegExp, Error, decodeURIComponent,
  require: (m) => m === "http" ? { ServerResponse: { prototype: { write() {}, end() {} } } } : require(m) };
ctx.globalThis = ctx; ctx.fetch = async () => ({ ok: true }); vm.createContext(ctx);
vm.runInContext("var c97Transform = function (h) { return h; }; const c97Mem = new Map([['fred:PAYEMS',{v:1,at:Date.parse('2026-11-27T20:00:00Z')}],['fred:UNRATE',{v:1,at:Date.parse('2026-11-27T20:00:00Z')}]]); const RT53_RY = { at: 0, v: null }; const RT44_EIA = { at: 0, v: null, src: '' };\n" + fs.readFileSync(block, "utf8"), ctx);
fs.writeFileSync(out, ctx.__c107credits.credit(fs.readFileSync(inp, "utf8"), url));
