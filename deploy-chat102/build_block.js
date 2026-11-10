"use strict";
// Rebuilds server_block_c102.js from lib_c102.js and client_c102.js.
const fs = require("fs");
const path = require("path");
const dir = __dirname;
const lib = fs.readFileSync(path.join(dir, "lib_c102.js"), "utf8");
const client = fs.readFileSync(path.join(dir, "client_c102.js"), "utf8");
if (client.indexOf("</" + "script") >= 0) throw new Error("client contains a script close tag");
const out = "// chat102 terminal. Built from lib_c102.js and client_c102.js. Edit those, then run node build_block.js.\n" +
  "(function () {\n" +
  "  var module = { exports: {} };\n" +
  lib + "\n" +
  "  var c102api = module.exports;\n" +
  "  c102api.c102Install.clientJs = " + JSON.stringify(client) + ";\n" +
  "  if (typeof globalThis !== \"undefined\") globalThis.c102 = c102api;\n" +
  "  if (!globalThis.C102_NO_INSTALL) c102api.c102Install();\n" +
  "})();\n";
fs.writeFileSync(path.join(dir, "server_block_c102.js"), out);
console.log("server_block_c102.js", out.length);
